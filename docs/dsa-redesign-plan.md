# DSA page redesign: plan and decisions

Status: adopted on 1 November 2026. Companion to [the audit](dsa-audit.md). The appendix records the completed
card outline from the content files.

**Implementation status:** All 376 curated practice problems have full in-page solution cards; 539 extra problems
remain in the Later lists with their original progress and external references. Lessons, labs and stage projects are
available. Some lesson examples require external dependencies or earlier setup and have not been independently run.
DSA lesson and verification sources are no longer Git-ignored; rebuilding also requires the existing
shared `_build` scripts. The committed compact problem catalog supports offline rebuilds without the ignored
metadata caches. Adding a new problem requires verified metadata caches; a successful build with all caches present
refreshes the catalog automatically.

## 1. Goal

Turn `dsa.html` from a problem list with external links into a self-contained field guide plus problem tracker that
feels like the same product as the AI page: open a card, read it, do the task, tick it, close it, and finish the day's
session knowing what you learned. External links stay, but only as optional "Go deeper" pointers to an exact section.

## 2. What is reused from the AI page (and what is not)

| Part | Decision |
|---|---|
| Build step | Same approach as the AI page, so no new tooling: Markdown sources in `_build/dsa/NN-key.md` (and `NN-key.cards.md` for problem cards) are rendered by the shared, escaping renderer `_build/mdlite.py` into data-only scripts `dsa-lessons/<module>.js`, loaded when a module is opened. `_build/build_dsa_guide.py` reuses `build_guide.py`'s parsers. As with the AI page, the generated page and lesson scripts are committed and the Markdown sources stay in `_build/`. |
| Styling | `guide.css` is loaded unchanged; `dsa.css` only adds what the DSA page needs (problem cards, hint ladder, stepper, milestones). Same fonts, colours, app bar, stage map, rail, controls and dark mode. |
| Progress and sync | Unchanged `progress.js` and the same tracker key `dsa-status`, so every saved status and the Google Drive sync keep working. Problem ids are unchanged, so no migration is needed; new card ids are namespaced (`l:module/slug`) and can never collide with LeetCode numbers. |
| Page script | `dsa.js` is a sibling of `guide.js` rather than an extraction from it: the DSA page needs problem cards, status triples, difficulty and pattern filters, milestones and a session planner that the AI page does not, and extracting shared code would have meant rewriting the AI page's script. Shared behaviour (one card open at a time, lazy loading, deep links, Done-next, Needs practice and Revisit) matches the AI page. |
| AI page | One deliberate change, requested in the brief: opening a lesson while a long lesson above it is open no longer throws the page upwards. The header you click now stays where it was and the lesson opens below it (`guide.js`, six lines). Measured in Chrome: the clicked header used to jump from 300 px to -3,057 px (desktop) and -4,994 px (phone); it now stays at 300 px. Nothing else on the AI page changes. |

## 3. Information architecture

Twelve stages; every stage depends only on earlier ones. Times are shown on every card, module and stage.

| # | Stage | Modules | Card style |
|---|---|---|---|
| 1 | Foundations and workflow | solving routine, complexity and cost models (amortised analysis, memory and caches, the Python cost sheet, measuring), recursion and induction, correctness and testing | compact primers |
| 2 | Core containers | arrays and dynamic arrays (list internals), hash tables (dict and set internals), linked lists, stacks and queues (deque internals) | recap cards |
| 3 | Scanning patterns | two pointers, sliding window, prefix sums, binary search (bisect), monotonic stacks and queues | recap cards |
| 4 | Order | sorting (Timsort and powersort internals) as recaps; heaps (heapq internals) and intervals as primers | recaps, then primers |
| 5 | Trees | binary trees and tree recursion, BSTs and ordered maps, tries | primers |
| 6 | Graphs | modelling and traversal (BFS, DFS, topological order), union-find and MSTs, weighted shortest paths | primers |
| 7 | Search, DP and greedy | backtracking, DP from recursion to tables, DP on grids, strings and knapsacks, greedy and exchange arguments, advanced DP (optional) | primers |
| 8 | Designing structures and specialist tools | data-structure design (LRU, LFU, iterators), string algorithms, bits and number theory, Fenwick and segment trees (optional) | primers; strings as recaps |
| 9 | DSA in production systems | storage engines (B+ trees, LSM trees, WAL), caches and rate limiters (LRU, LFU, TinyLFU, S3-FIFO, SIEVE), search engines (inverted indexes, BM25, tries and FSTs), consistent hashing and Merkle trees, filters and sketches (Bloom, cuckoo, XOR, HyperLogLog, Count-Min, MinHash and LSH), algorithms in developer tools (Myers diff, merge, regex as NFA/DFA, build order, text buffers) | primers |
| 10 | DSA behind AI systems | vector search (KD-tree, LSH, IVF-PQ, HNSW, DiskANN), LLM serving (paged KV cache, radix-tree prefix caching, beam search, top-k and top-p), BPE tokenisers, graphs for retrieval and agents (PageRank, k-hop expansion, DAG workflows), data dedup and contamination checks; cross-linked to the AI page rather than duplicating it | primers |
| 11 | Frontier (optional) | AlphaDev, the 2025 shortest-path "sorting barrier" result, funnel and elastic hashing, learned indexes, Swiss tables, pdqsort, driftsort, ipnsort and powersort, recent vector-index research | short primers |
| 12 | Mastery | interleaved mixed review sets, deriving unfamiliar solutions, three capstones | primers, sets, builds |

Ordering changes from the old page, and why: sorting and heaps move before trees (tree and graph cards use heaps and
sorted order); backtracking moves next to DP (DP is presented as backtracking that remembers); linked lists join stacks
and queues; strings, bits and range queries move after the core algorithms they rely on. The old topics are otherwise
kept: the 34 old topics map onto the technique modules, and each module's Later list holds that topic's remaining
problems.

Depth follows the brief: the owner is solid on everything before trees in the old order, so stages 2 and 3, sorting and
string algorithms are **recap cards** (internals, template, worked example, pitfalls, one quick check). From heaps and
trees onwards every card is a **full primer**.

## 4. Card schemas

**Primer** (question-titled, 10-20 minutes): the question as asked; a short answer (key-idea box); Intuition; How it
works; Cost (derived, not asserted); When to use it (when not to, trade-offs against alternatives); Worked trace (an
interactive step-through); Template (tested Python); Pitfalls; Check yourself (2-4 questions, answers hidden); Lab (2-3
tracker problems with the expected result); Go deeper (exact sections); "You now know ...". The page appends "Problems
that practise this" from the problem tags, so every primer lists its problems and every problem links back.

**Recap** (5-10 minutes): the idea; Internals; Template; Worked example; Pitfalls; Quick check; "You now know ...".

**Problem card** (the heart of the page; depth scales with difficulty): title with a link to the free original;
difficulty, tier (core, "Derive it", "Stretch") and a pattern chip linking to its primer; The problem (restated in our
own words, with an example); Constraints and what they imply; a three-level hint ladder (what to notice, a nudge, the key
insight); then, hidden behind "Show the solution": Brute force (cost and exact bottleneck); The insight; Optimal
solution, traced; Code (tested); Complexity (justified); Mistakes and edge cases; 2-3 Variations; Go deeper (reference
solutions and the free editor page). Status buttons are unchanged: **Solved** (brute force and optimal), **Brute only**,
**Stuck**, and so are the Easy, Medium and Hard groups.

**Lab** (30-60 minutes, hands-on): Steps; What you should see.

**Project** (one per stage plus three capstones): The brief; Spec; Milestones (1-2 hours each; each one is a checkbox,
saved like any other item); Done when (acceptance tests and benchmarks); Testing and validation; Performance analysis
(predict, then measure); Stretch goals; Hints with deep links.

## 5. Problems: ladders, review sets and the Later list

- Each technique module has a curated ladder of 6-12 problems split by difficulty, each with a full card. The ladders
  come from an audit of all 899 tracked problems.
- Six mixed review sets (about 60 problems, topic hidden until the last hint) open along the route.
- **Scope cut, made explicitly (breadth, not depth):** the rest of the old tracker's problems keep their ids, statuses
  and difficulty split in a per-module **Later list**, with links to the original problem and to reference solutions
  but no in-page card yet. Cards for them are the obvious next increment.
- Nothing is lost: a test asserts that every one of the 899 old ids is still on the page exactly once.

## 6. UI changes

- Today's session: about 30 minutes of new cards (or one lab), one problem on an idea already learned, and one review
  item. It is kept for the day and ticked off as you go, says "Session complete" at the end, and suggests the next
  project milestone.
- Review queue: anything marked Brute only, Stuck, Needs practice or Revisit comes back after three days, oldest first.
- Filters: view (everything, cards, problems, projects, review), status, difficulty and pattern, plus search.
- Every card is deep-linkable (`#l-...` for cards, `#p-<id>` for problems), opens in place below its header, and is
  keyboard accessible (real buttons and summaries; Escape closes and returns focus to the header).
- Interactive step-through traces (Back, Next, Show all) and copy buttons on code.
- Stage map shows time left and progress per stage; modules show cards, problems and estimated time.
- Mobile: problem rows stack (title, then tags, then status buttons); controls wrap; tested at 390 px wide.
- Runnable Python cells: **not added.** They need a WebAssembly Python (Pyodide, about 10 MB) and loosening the site's
  strict Content Security Policy (`'wasm-unsafe-eval'` plus a CDN), which the security tests forbid. Copy buttons plus a
  local editor are the robust option. Recorded as a deliberate deviation.

## 7. Link policy (enforced by `lint_dsa.py`, `verify_dsa.py` and `check_links.py`)

Exact section, anchor or page only; no homepages, roadmaps, problem lists, repository roots, playlists or search pages;
whole long articles only with a `#section`; videos only when under about 20 minutes (length stated) or with a verified
timestamp; free resources only; every URL fetched and verified; anything unverifiable goes in the report, not on the
page. Problem links are: the original problem (all free), the doocs reference-solutions page for that problem, and the
NeetCode editor page. The old "Find a video" YouTube search links are removed (search pages are generic); a problem
video is shown only when its duration is present in the cached audit data and meets the length limit.

On 1 November 2026, 480 distinct lesson and project URLs were fetched. Their HTML anchors, generated AI-page anchors,
GitHub line ranges and PDF page numbers were checked; PDF checks confirm that the page exists, not that it is the
best section for the lesson. The 16 problem-solution references added after the original audit were also fetched and
checked for the expected title and a Python solution. This is a reachability and target check, not a complete editorial
review of every resource or a guarantee that a site will remain available.

The same pass compiled all 377 lesson Python blocks. Of those, 297 eligible examples ran in temporary,
resource-limited working directories; 72 were not executed because they use file I/O, external dependencies or
other restricted operations, and 8 require context from other cards or skipped setup blocks. These counts do not
establish that every lesson example has been fully tested.

## 8. Writing standard

Plain British English, no em dashes, intuition before formalism, a worked example in every card, no filler. Every
explanation, restatement and code sample is written from scratch (nothing copied from LeetCode, GeeksforGeeks, books or
videos). Python 3.12 throughout, with one-line C++ or Java notes where costs differ.

## 9. Verification

`_build/verify_dsa.py` checks every card for its required parts and their order, applies the link policy, compiles
Python blocks, and runs the problem-card test scripts. Browser checks cover loading and retry, hidden solutions,
expansion and scroll position, status buttons, milestones, progress persistence, review resurfacing, mobile width and
AI lesson loading. `node --test` covers progress, sync and page integrity. Some lesson examples still require the
manual setup or optional dependencies described above; they have not all been executed independently.

## 10. Projects

| Stage | Project |
|---|---|
| Foundations | Range-sum experiment bench |
| Containers | Cancellation-safe task queue |
| Scanning | Sliding telemetry report |
| Order | Meeting room allocator |
| Trees | Trie-backed name directory |
| Graphs | Weighted delivery routes |
| DP and greedy | 0/1 purchase planner |
| Design and tools | Fenwick-backed inventory totals |
| Production | Local document search |
| AI systems | Approximate vector retrieval lab |
| Frontier | Four-value sorting kernel study |
| Mastery | Parallel build planner; searchable field notes; recoverable key-value notebook |

## 11. Process

Research by four parallel agents (learning design, real-world projects, problem-bank audit, verified resources), then
this plan, then schema and UI, then module authors in parallel (one or two modules each, never sharing a file), then
problem-card authors per module once its ladder is fixed (separate `.cards.md` files), project authors (separate files,
appended by the lead), integration, verification and browser QA, with commits per stage.

## Appendix: card outline

This outline reflects the current content sources; times are the card estimates shown on the page.

### Foundations and workflow

#### [Solving problems you have not seen](../dsa.html#m-method)

- Primer: What does "solved" mean, and what loop gets you there? (16 min)
- Primer: How do you pin a problem down before solving it? (14 min)
- Primer: Why write the brute force first, and how do you write one quickly? (14 min)
- Primer: How do the constraints tell you what complexity to aim for? (13 min)
- Primer: How do you find the bottleneck in a brute force and remove it? (15 min)
- Primer: What do you do when you are stuck? (14 min)
- Primer: How should you use timeboxes, hints and solutions so practice sticks? (12 min)
- Lab: Maximum subarray: from O(n^3) to O(n) (50 min)
- Practice: 6 complete cards; 0 additional Later-list problems.

#### [Complexity, memory and cost models](../dsa.html#m-cost)

- Primer: How do you predict running time before you run the code? (15 min)
- Primer: What do Big-O, Big-Theta and Big-Omega actually promise? (15 min)
- Primer: How much memory does a program really use? (14 min)
- Primer: Why is list.append O(1) when a resize copies the whole list? (16 min)
- Primer: Why does scanning an array beat chasing pointers when both are O(n)? (14 min)
- Primer: What do Python's built-in operations really cost? (16 min)
- Primer: How do you measure running time and estimate the growth exponent? (15 min)
- Lab: Doubling experiments: predict, then measure (45 min)
- Practice: 9 complete cards; 0 additional Later-list problems.

#### [Recursion, induction and divide and conquer](../dsa.html#m-recur)

- Primer: How does a proof by induction work, and why does it prove recursive code correct? (14 min)
- Primer: What happens on the call stack when a function calls itself? (13 min)
- Primer: How do you write a recursive function without tracing every call? (15 min)
- Primer: How do you find the running time of a recursive function? (16 min)
- Primer: How does divide and conquer sort a list and count its inversions in O(n log n)? (16 min)
- Primer: How do you compute x^n with only O(log n) multiplications? (13 min)
- Primer: How do you run deep recursion safely in Python, or turn it into a loop? (15 min)
- Lab: See the recursion tree: count calls, memoise, then remove the recursion (45 min)
- Practice: 7 complete cards; 0 additional Later-list problems.

#### [Correctness: invariants, testing and debugging](../dsa.html#m-correct)

- Primer: How do you state exactly what a function must do? (13 min)
- Primer: How do you prove a loop is correct, and that it stops? (15 min)
- Primer: How do you rearrange an array in place without losing track? (14 min)
- Primer: How do you prove that a greedy choice is safe? (14 min)
- Primer: How do you find the input that breaks your code, and then the bug? (15 min)
- Primer: How do you stress-test a solution against a brute force? (16 min)
- Primer: What does property-based testing add, and how do you use Hypothesis? (14 min)
- Lab: Break it, then prove it (45 min)
- Practice: 6 complete cards; 0 additional Later-list problems.

#### [Build a cost and correctness workbench](../dsa.html#m-projectfound)

- Project: Range-sum experiment bench (6-8 h)

### Core containers

#### [Arrays, dynamic arrays, strings and grids](../dsa.html#m-arrays)

- Recap: Python lists: references, capacity and amortised append (12 min)
- Recap: In place: reverse, rotate and compact (10 min)
- Recap: The array as its own index (10 min)
- Recap: Strings as character arrays (10 min)
- Recap: Grids: row-major indexing, neighbours and traversal orders (12 min)
- Recap: Transforming matrices in place (10 min)
- Lab: Build a dynamic array and measure growth factors (45 min)
- Practice: 12 complete cards; 10 additional Later-list problems.

#### [Hash tables, sets and counting](../dsa.html#m-hashing)

- Recap: Hash tables: chaining, probing, tombstones and resizing (12 min)
- Recap: Inside CPython's dict and set (12 min)
- Recap: The complement pattern: look up before you insert (10 min)
- Recap: Counting and grouping with canonical keys (10 min)
- Recap: Sets: membership, de-duplication and set algebra (10 min)
- Recap: Hashing, sorting or an array? When hashing goes wrong (10 min)
- Lab: Probe lengths you can see (40 min)
- Practice: 12 complete cards; 10 additional Later-list problems.

#### [Linked lists, stacks and queues](../dsa.html#m-linear)

- Recap: Linked lists: rewiring, reversal and dummy heads (12 min)
- Recap: Fast and slow pointers: middle, cycle and cycle entry (12 min)
- Recap: Stacks for matching and nesting (10 min)
- Recap: Evaluating expressions with stacks (12 min)
- Recap: Queues, deques and ring buffers (12 min)
- Recap: A queue from two stacks, and why it is amortised O(1) (10 min)
- Lab: Deque three ways: list, linked list and ring buffer (45 min)
- Practice: 12 complete cards; 47 additional Later-list problems.

#### [Build a container-backed task queue](../dsa.html#m-projectcontain)

- Project: Cancellation-safe task queue (6-8 h)

### Scanning patterns

#### [Two pointers](../dsa.html#m-twoptr)

- Recap: Opposite ends: pair sum and the discard argument (12 min)
- Recap: Three-sum and k-sum: sort, fix one, skip duplicates (12 min)
- Lab: Stress-test three-sum and catch the duplicate bugs (40 min)
- Recap: Read and write pointers: compact and merge in place (12 min)
- Recap: Partitions: two-way and the Dutch national flag (12 min)
- Recap: Palindromes: converge, skip and allow one deletion (10 min)
- Recap: The limiting side: most water and trapped rain (14 min)
- Practice: 11 complete cards; 17 additional Later-list problems.

#### [Sliding window](../dsa.html#m-window)

- Recap: Fixed-size windows: one in, one out (10 min)
- Recap: Variable windows: grow, shrink, and why it works (14 min)
- Recap: Counting windows: at most K and exactly K (12 min)
- Recap: Minimum covering window: the formed counter (14 min)
- Recap: Window extremes, and when to leave the window behind (12 min)
- Lab: Rolling metrics over a log stream (50 min)
- Practice: 12 complete cards; 18 additional Later-list problems.

#### [Prefix sums and difference arrays](../dsa.html#m-prefix)

- Recap: Prefix sums and half-open ranges (10 min)
- Recap: Counting subarrays with a prefix map (12 min)
- Recap: Remainders, XOR and balance as prefix keys (10 min)
- Recap: 2D prefix sums and integral images (12 min)
- Recap: Difference arrays: many range updates, one rebuild (10 min)
- Recap: Left and right passes (10 min)
- Lab: Integral image: region sums and a box blur at any radius (45 min)
- Practice: 12 complete cards; 11 additional Later-list problems.

#### [Binary search and searching the answer](../dsa.html#m-bsearch)

- Recap: Binary search as an invariant (12 min)
- Recap: Rotated arrays and peaks (12 min)
- Recap: Binary search on the answer (14 min)
- Recap: Implicit search spaces: counting and cuts (14 min)
- Recap: Floats, overflow, exhaustive tests and production uses (12 min)
- Lab: Binary search torture test (45 min)
- Practice: 12 complete cards; 34 additional Later-list problems.

#### [Monotonic stacks and queues](../dsa.html#m-mono)

- Recap: Next greater element: the monotonic stack and its O(n) bound (12 min)
- Recap: Largest rectangle in a histogram (12 min)
- Recap: Contribution counting: sum of subarray minimums (12 min)
- Recap: Monotonic deque: the maximum of every window (12 min)
- Recap: Recognising monotonic structure, and when a heap is simpler (10 min)
- Lab: Count the pops: measuring the amortised bound (40 min)
- Practice: 12 complete cards; 12 additional Later-list problems.

#### [Build a telemetry window analyzer](../dsa.html#m-projectscan)

- Project: Sliding telemetry report (6-8 h)

### Order: sorting, heaps and intervals

#### [Sorting, partitioning and selection](../dsa.html#m-sorting)

- Recap: Merge sort: merging, stability and inversions (12 min)
- Recap: Partitioning and quicksort: Lomuto, Hoare and three-way (14 min)
- Recap: Quickselect: the k-th element without sorting (12 min)
- Recap: Counting, radix and bucket sort, and the n log n floor (14 min)
- Recap: How Python and C++ sort: Timsort, powersort and introsort (14 min)
- Recap: Custom orders: keys, comparators and consistency (12 min)
- Lab: Sorting showdown (50 min)
- Practice: 12 complete cards; 2 additional Later-list problems.

#### [Heaps and priority queues](../dsa.html#m-heap)

- Primer: What does a priority queue promise, and how does a heap fit a tree into a list? (15 min)
- Primer: How do push and pop keep a heap valid in O(log n)? (16 min)
- Primer: Why is building a heap O(n), not O(n log n)? (15 min)
- Primer: How do you use Python's heapq for max-heaps, records and ties? (14 min)
- Primer: How do you keep the k largest items of a stream? (14 min)
- Primer: How do you merge k sorted lists with a heap? (14 min)
- Lab: Top-k over a stream: your heap against heapq, sort and Counter (45 min)
- Primer: How do two heaps give you a running median? (13 min)
- Primer: How do you delete or reprioritise an item buried in a heap? (16 min)
- Primer: How do schedulers and timers use a heap, and when does a timing wheel win? (15 min)
- Practice: 12 complete cards; 16 additional Later-list problems.

#### [Intervals and sweep line](../dsa.html#m-intervals)

- Primer: When do two intervals overlap, and should the end be included? (13 min)
- Primer: How do you merge overlapping intervals, and why is sorting by start enough? (14 min)
- Primer: How do you insert or remove a range in a sorted list of disjoint intervals? (14 min)
- Primer: How many intervals overlap at the busiest moment? (15 min)
- Primer: How many rooms do you need, and which room gets each meeting? (14 min)
- Primer: Why does picking the earliest end give the most non-overlapping intervals? (15 min)
- Primer: How do you answer many point queries against many intervals at once? (15 min)
- Primer: Which sort order does an interval problem need, and where do sweeps run in production? (14 min)
- Lab: Calendar sweeps: peak load, rooms and free time for 50,000 bookings (45 min)
- Practice: 12 complete cards; 10 additional Later-list problems.

#### [Build a room allocation planner](../dsa.html#m-projectorder)

- Project: Meeting room allocator (6-8 h)

### Trees

#### [Binary trees and tree recursion](../dsa.html#m-trees)

- Primer: What do pre-order, in-order and post-order visit, and when do you need each? (15 min)
- Primer: How do you walk a tree level by level, and why does a queue do it? (14 min)
- Primer: What should each recursive call return? Solving tree problems bottom-up (16 min)
- Primer: When should information flow down a tree instead of up? (16 min)
- Primer: How do you find the best path when it does not have to pass through the root? (16 min)
- Primer: How do you find the lowest common ancestor of two nodes? (15 min)
- Primer: How do you rebuild a tree from its traversals, and turn it into a string and back? (15 min)
- Primer: How do you traverse a tree without recursion, and when do you have to? (15 min)
- Primer: Where do trees run in real software, and which traversal does each one use? (12 min)
- Lab: Tree toolkit: build, walk, serialise and property-test (50 min)
- Practice: 12 complete cards; 47 additional Later-list problems.

#### [Binary search trees and ordered maps](../dsa.html#m-bst)

- Primer: How does a binary search tree find and insert a key in O(h)? (15 min)
- Primer: How do you delete a key from a binary search tree without breaking the order? (15 min)
- Primer: How do you check that a binary tree really is a binary search tree? (15 min)
- Primer: Why does in-order traversal of a BST come out sorted, and how do you get the k-th smallest, a successor or an iterator? (16 min)
- Primer: Why does the shape of a BST decide its speed, and how bad can it get? (14 min)
- Primer: How do AVL trees, red-black trees, treaps and B-trees keep the height logarithmic? (18 min)
- Primer: Which ordered map should you use in Python, and why does SortedList beat a balanced tree there? (16 min)
- Primer: How do databases and Redis keep huge ordered data fast to search and scan? (14 min)
- Lab: Balanced or not: a plain BST against SortedList, bisect and set (45 min)
- Practice: 12 complete cards; 9 additional Later-list problems.

#### [Tries](../dsa.html#m-trie)

- Primer: How does a trie look up a word or a prefix in time proportional to its length? (15 min)
- Primer: How do you count, rank and list the completions of a prefix? (15 min)
- Primer: When should you use a trie rather than a hash set or a sorted list? (14 min)
- Lab: Autocomplete: trie or sorted list? (45 min)
- Primer: How do you find every dictionary word hidden in a letter grid without searching for each word separately? (16 min)
- Primer: How do you search a trie with wildcards, or find every dictionary word that starts at a given position? (14 min)
- Primer: How does a binary trie find the maximum XOR of two numbers? (14 min)
- Primer: How does a router find the longest matching prefix, and why are production tries compressed? (15 min)
- Practice: 12 complete cards; 7 additional Later-list problems.

#### [Build a prefix directory](../dsa.html#m-projecthier)

- Project: Trie-backed name directory (6-8 h)

### Graphs

#### [Graph modelling and traversal](../dsa.html#m-graphs)

- Primer: How do you turn a problem into a graph, and how should you store it? (15 min)
- Primer: How does BFS find the shortest path in an unweighted graph? (15 min)
- Primer: How does DFS find connected components, and when does recursion fail? (14 min)
- Primer: How do you run BFS on a grid, and why start from every source at once? (14 min)
- Lab: Maze lab: BFS, DFS and distance maps (45 min)
- Primer: How do you find the fewest moves through a puzzle's states? (15 min)
- Primer: How do you detect a cycle, and when can a graph be two-coloured? (15 min)
- Primer: How do you order tasks that depend on each other? (15 min)
- Primer: How do build tools run dependent tasks in parallel? (14 min)
- Practice: 12 complete cards; 35 additional Later-list problems.

#### [Union-find and minimum spanning trees](../dsa.html#m-dsu)

- Primer: When do you need union-find instead of a graph search? (12 min)
- Primer: How do path compression and union by size make union-find almost O(1)? (15 min)
- Primer: What problems become easy once you can merge groups? (15 min)
- Primer: How do you keep ratios or offsets along union-find edges? (13 min)
- Primer: How do you answer connectivity queries offline, or when edges are deleted? (14 min)
- Primer: How does Kruskal build a minimum spanning tree, and why is the greedy choice safe? (15 min)
- Primer: When is Prim's algorithm the better choice for a minimum spanning tree? (14 min)
- Primer: How does union-find label connected regions in an image? (13 min)
- Lab: Percolation: estimate a physical constant with union-find (45 min)
- Practice: 12 complete cards; 8 additional Later-list problems.

#### [Weighted shortest paths](../dsa.html#m-paths)

- Primer: How does Dijkstra's algorithm find shortest paths, and why is a popped distance final? (18 min)
- Primer: Why do negative edges break Dijkstra, and how does Bellman-Ford handle them and "at most k stops"? (16 min)
- Primer: How do you find shortest paths when every edge costs 0 or 1? (13 min)
- Primer: How do you adapt Dijkstra when a route's cost is not a plain sum, or the state is more than a vertex? (16 min)
- Primer: How does Floyd-Warshall find all-pairs shortest paths, and why must k be the outer loop? (14 min)
- Primer: How do you find shortest and longest paths in a DAG in linear time, even with negative edges? (14 min)
- Primer: Which shortest-path algorithm should you choose, and how does A* use a heuristic without losing optimality? (16 min)
- Lab: Route planner on a grid: BFS vs Dijkstra vs A* (50 min)
- Primer: What else can graph search reveal: Euler paths, bridges and strongly connected components? (optional) (15 min)
- Primer: How do routers and map services compute shortest paths at scale? (14 min)
- Practice: 12 complete cards; 16 additional Later-list problems.

#### [Build a route planner](../dsa.html#m-projectnetwork)

- Project: Weighted delivery routes (6-8 h)

### Search, dynamic programming and greedy

#### [Complete search and backtracking](../dsa.html#m-backtrack)

- Primer: How do you turn "try every possibility" into a search tree you can count? (15 min)
- Primer: How do you generate every subset, and why are there exactly 2^n? (14 min)
- Primer: How do choose, explore, unchoose generate permutations and combinations without duplicates? (15 min)
- Primer: How do you build partitions and well-formed strings piece by piece? (15 min)
- Primer: How does pruning make exponential search fast enough? (15 min)
- Primer: How do you solve N-queens and Sudoku with O(1) conflict checks? (16 min)
- Primer: Why must a grid word search undo its marks when flood fill never does? (14 min)
- Primer: Will exhaustive search finish in time, and what do you do when it will not? (16 min)
- Lab: Sudoku solver: from blind search to most-constrained-first (50 min)
- Practice: 12 complete cards; 23 additional Later-list problems.

#### [Dynamic programming: from recursion to tables](../dsa.html#m-dp)

- Primer: Why is plain recursion exponential on climbing stairs, and how does memoisation make it linear? (15 min)
- Primer: How do you write a correct recurrence before writing any code? (16 min)
- Primer: How do you turn a memoised recursion into a table, and then into two variables? (15 min)
- Primer: How do you solve take-or-skip problems such as decoding a digit string? (15 min)
- Primer: Why does the loop order change the answer in coin change? (16 min)
- Primer: How do you find the longest increasing subsequence in O(n log n)? (16 min)
- Primer: How do you add state when the index alone is not enough? (16 min)
- Practice: 0 complete cards; 41 additional Later-list problems.

#### [DP on grids, strings and knapsacks](../dsa.html#m-dpseq)

- Primer: How do you count or minimise paths through a grid with DP? (13 min)
- Primer: How does the LCS table find the longest common subsequence, and how do you read it back? (15 min)
- Primer: How does edit distance turn one word into another, and how do you recover the edits? (15 min)
- Lab: Spelling suggestions with edit distance (50 min)
- Primer: How do you match or count one sequence inside another (distinct subsequences, wildcards, interleaving)? (14 min)
- Primer: How do range tables solve palindrome problems? (13 min)
- Primer: How does 0/1 knapsack work, and why does the one-row loop run backwards? (15 min)
- Primer: What changes when items can be reused: unbounded knapsack, coin change and counting order? (13 min)
- Primer: How do you split a string into dictionary words (or palindromes) with DP? (12 min)
- Primer: Where do sequence DPs run in real software, and what changes at scale? (12 min)
- Practice: 12 complete cards; 43 additional Later-list problems.

#### [Greedy algorithms and exchange arguments](../dsa.html#m-greedy)

- Primer: What makes an algorithm greedy, and when can you trust it? (11 min)
- Primer: How do you prove a greedy choice is safe: exchange arguments and staying ahead? (15 min)
- Primer: How do you find a counterexample that breaks a greedy rule? (13 min)
- Lab: Greedy or not? Let a brute force decide (40 min)
- Primer: How do you solve reach and jump problems in one pass? (12 min)
- Primer: Why does gas station restart after a negative tank, and why is that correct? (13 min)
- Primer: How do you find the right sort key for a greedy, and prove it? (14 min)
- Primer: When does a greedy need a heap, and how do you use one? (13 min)
- Practice: 0 complete cards; 34 additional Later-list problems.

#### [Advanced dynamic programming](../dsa.html#m-dpadv)

- Primer: How does interval DP solve problems over every contiguous range [i, j]? (16 min)
- Primer: How do you run DP on a tree, and how does rerooting give every node's answer in O(n)? (16 min)
- Primer: How does bitmask DP turn n! orderings into 2^n subsets? (17 min)
- Lab: Travelling salesman for 15 cities: permutations vs bitmask DP (45 min)
- Primer: How do you count the numbers up to N that have a digit property? (15 min)
- Primer: How do you count ways modulo 10^9 + 7 without getting wrong answers? (13 min)
- Primer: How do you speed up a DP whose transitions scan a whole range? (15 min)
- Primer: Why is a DP a shortest or longest path in a DAG, and what does that view buy you? (14 min)
- Practice: 12 complete cards; 10 additional Later-list problems.

#### [Build a bounded budget planner](../dsa.html#m-projectstrategy)

- Project: 0/1 purchase planner (6-8 h)

### Designing structures and specialist tools

#### [Designing data structures](../dsa.html#m-design)

- Primer: How do you design a data structure from the operations it must support? (15 min)
- Primer: How do you design an LRU cache with O(1) get and put? (16 min)
- Primer: How do you build an LFU cache where every operation is O(1)? (16 min)
- Primer: How do you add get-min, get-max or get-random to a structure in O(1)? (15 min)
- Primer: How do you store values that change over time and query them by time or version? (15 min)
- Primer: How do you count recent events and limit request rates? (16 min)
- Primer: How do you design iterators that flatten, peek or produce values lazily? (14 min)
- Primer: How do you test a data structure you designed? (15 min)
- Lab: LRU cache, tested and measured (45 min)
- Practice: 12 complete cards; 8 additional Later-list problems.

#### [String algorithms](../dsa.html#m-strings)

- Recap: Python strings: real costs, counts and canonical shapes (10 min)
- Recap: Palindromes: expanding around 2n - 1 centres (10 min)
- Recap: Rolling hash and Rabin-Karp (12 min)
- Recap: KMP and the prefix function (12 min)
- Recap: The Z-function and its Z-box (10 min)
- Recap: Parsing, tokenising and length-prefixed encodings (10 min)
- Lab: Find the duplicates: repeated passages across documents (45 min)
- Practice: 12 complete cards; 21 additional Later-list problems.

#### [Bits and number theory](../dsa.html#m-bitmath)

- Primer: How does two's complement store negative numbers, and what changes in Python? (15 min)
- Primer: How do you set, clear and test bits, and why does x & -x isolate the lowest set bit? (15 min)
- Primer: Why does XOR find the number that appears once? (12 min)
- Primer: How do you enumerate every subset, and every submask of a mask, with bits? (15 min)
- Primer: Why does Euclid's algorithm find the greatest common divisor so fast? (12 min)
- Primer: How do you compute huge powers and divide under a modulus like 10^9 + 7? (15 min)
- Primer: How does the sieve of Eratosthenes find every prime up to n in O(n log log n)? (15 min)
- Lab: Bits for speed: sieves and subset loops, measured (45 min)
- Primer: How do you count combinations modulo a prime for many queries? (14 min)
- Primer: Why is 0.1 + 0.2 != 0.3, and how do you keep geometry and fractions exact? (15 min)
- Practice: 12 complete cards; 48 additional Later-list problems.

#### [Range queries: Fenwick and segment trees](../dsa.html#m-rangeq)

- Primer: Where do prefix sums stop working, and what replaces them? (12 min)
- Primer: How does a sparse table answer range minimum in O(1)? (14 min)
- Primer: How does a Fenwick tree keep prefix sums correct under updates in O(log n)? (18 min)
- Primer: How do you count inversions and "smaller after self" with a Fenwick tree? (15 min)
- Primer: When do you need coordinate compression, and how do you do it safely? (12 min)
- Primer: How does a segment tree answer any associative range query in O(log n)? (18 min)
- Lab: Range query benchmark: naive, prefix rebuild, Fenwick and segment tree (45 min)
- Primer: How does lazy propagation make range updates O(log n)? (18 min)
- Primer: Where do range-query structures run in real systems? (14 min)
- Practice: 12 complete cards; 2 additional Later-list problems.

#### [Build a mutable range-sum index](../dsa.html#m-projectengineer)

- Project: Fenwick-backed inventory totals (6-8 h)

### DSA in production systems

#### [Storage engines: B-trees, LSM trees and write-ahead logs](../dsa.html#m-storage)

- Primer: How do you choose a data structure from requirements? (15 min)
- Primer: Why do databases index with B+ trees instead of binary search trees? (17 min)
- Primer: How does a write-ahead log make writes survive a crash? (16 min)
- Primer: How does an LSM tree turn random writes into sequential ones? (17 min)
- Primer: What does compaction cost, and how do leveled and tiered compaction trade read, write and space amplification? (16 min)
- Primer: Why do LevelDB and Redis use skip lists? (15 min)
- Primer: When does a B+ tree beat an LSM tree, and when does it lose? (15 min)
- Primer: How do you find the real bottleneck before optimising? (15 min)
- Lab: Measure a real B-tree, then choose an engine (50 min)
- Practice: 1 complete cards; 0 additional Later-list problems.

#### [Caches and rate limiters in production](../dsa.html#m-caching)

- Primer: Why does plain LRU fail, and what do CLOCK and Redis's sampled LRU approximate? (18 min)
- Primer: How do LFU with ageing and TinyLFU admission keep the popular keys cached? (18 min)
- Primer: How does S3-FIFO beat LRU with three FIFO queues? (17 min)
- Primer: How does SIEVE evict with one queue and a moving hand? (15 min)
- Primer: How do you measure a cache with trace replay and miss-ratio curves? (17 min)

#### [Search engines: inverted indexes, ranking and type-ahead](../dsa.html#m-search)

- Primer: How does a search engine find every document that contains a word? (15 min)
- Primer: How do you intersect a short posting list with a huge one without reading all of it? (15 min)
- Primer: How does a search engine turn posting lists into a BM25 ranking? (15 min)
- Primer: How does a search engine return the top 10 without scoring every match? (16 min)
- Primer: How do search engines shrink posting lists to about a byte per document? (14 min)
- Primer: How does a search box suggest the best completions after two keystrokes? (15 min)
- Primer: How does search still find "receive" when you type "recieve"? (16 min)
- Lab: Race merge against galloping on a Zipf-shaped index (45 min)

#### [Filters and sketches: approximate answers in tiny memory](../dsa.html#m-sketch)

- Primer: How does a Bloom filter say "definitely not here" in about 10 bits per key? (16 min)
- Primer: How does a cuckoo filter support deletion, and when does it beat a Bloom filter? (15 min)
- Primer: How do XOR and binary fuse filters store a fixed set in about 9 bits per key? (14 min)
- Primer: How does HyperLogLog count billions of distinct items in 12 KB? (16 min)
- Primer: How does a count-min sketch estimate how often each item appears, with a guaranteed error? (15 min)
- Primer: How do you find the heavy hitters in a stream without counting everything? (14 min)
- Primer: How can a few hundred numbers estimate how similar two documents are? (15 min)
- Primer: How does LSH banding find similar pairs without comparing every pair? (15 min)
- Primer: How do you keep a uniform random sample of a stream whose length you do not know? (12 min)
- Lab: Measure your sketches: error against memory for a Bloom filter and a count-min sketch (45 min)

#### [Build an inverted search index](../dsa.html#m-projectprod)

- Project: Local document search (6-8 h)

### DSA behind AI systems

#### [Vector search: from brute force to HNSW and DiskANN](../dsa.html#m-vectors)

- Primer: What does exact k-nearest-neighbour search really cost, and why keep a heap of size k? (15 min)
- Primer: Why do KD-trees work in 2-D but collapse in 100 dimensions? (15 min)
- Primer: How can random hyperplanes hash similar vectors into the same bucket? (16 min)
- Primer: How does an IVF index use k-means to scan only a few clusters? (16 min)
- Primer: How does product quantisation shrink a vector to a few bytes and still rank it? (18 min)
- Primer: How does HNSW find near neighbours with a few hundred distance computations? (20 min)
- Primer: How does DiskANN search a billion vectors from an SSD? (18 min)
- Primer: How do you measure recall@k against latency and choose an index? (15 min)
- Lab: Brute force, LSH and IVF on 20,000 vectors (50 min)

#### [Inside LLM serving: KV caches, prefix trees and decoding](../dsa.html#m-llmserve)

- Primer: How does PagedAttention store a growing KV cache without wasting memory? (16 min)
- Primer: How does a radix tree let an LLM server reuse the KV cache of shared prompts? (17 min)
- Primer: How does beam search keep the k best hypotheses, and why normalise by length? (15 min)
- Primer: How do top-k and top-p sampling choose the next token efficiently? (15 min)
- Primer: How does continuous batching decide what runs at each step? (16 min)
- Lab: Measure prefix-cache reuse on simulated chat traffic (50 min)

#### [Tokenisers: byte-pair encoding and friends](../dsa.html#m-tokens)

- Primer: What does byte-pair encoding actually learn? (16 min)
- Primer: How do you train BPE fast enough for a real corpus? (17 min)
- Primer: How does a tokeniser apply merge ranks to new text? (15 min)
- Primer: How does byte-level BPE encode any string, and what does GPT-2's pre-tokeniser do? (16 min)
- Primer: How do WordPiece and Unigram differ from BPE, and which tokeniser quirks bite? (17 min)
- Lab: Train a byte-level BPE on Pride and Prejudice: naive versus heap (45 min)

#### [Graphs behind AI systems: retrieval and agents](../dsa.html#m-aigraph)

- Primer: How does PageRank turn links into scores, and why does power iteration converge? (15 min)
- Primer: How does personalised PageRank find passages for a multi-hop question, as HippoRAG does? (15 min)
- Primer: How do you expand a knowledge graph k hops from the question without flooding the context? (14 min)
- Primer: How does GraphRAG split an entity graph into communities, and what does Leiden fix in Louvain? (15 min)
- Primer: How do you run an agent workflow as a DAG: order, parallel branches, loops and crash recovery? (15 min)
- Lab: PageRank and personalised PageRank, checked against an exact solve (45 min)

#### [Build a vector retrieval evaluator](../dsa.html#m-projectaisys)

- Project: Approximate vector retrieval lab (6-8 h)

### Frontier (optional)

#### [Frontier: recent results (optional)](../dsa.html#m-frontier)

- Primer: What did AlphaDev change in the C++ standard library's sort, and why did it matter? (10 min)
- Primer: Has Dijkstra's algorithm been beaten? The sorting barrier for shortest paths (12 min)
- Primer: Can open addressing beat uniform probing without moving keys? Elastic and funnel hashing (12 min)
- Primer: Can a model replace a B-tree? Learned indexes and what stuck (10 min)
- Primer: What makes Swiss tables fast, and why did Go 1.24 switch its map to one? (12 min)
- Primer: Which sorting algorithms do standard libraries use now, and why? (12 min)
- Primer: How can one bit per dimension still give trustworthy vector distances? RaBitQ (12 min)

#### [Build a tiny-sort experiment](../dsa.html#m-projectfrontier)

- Project: Four-value sorting kernel study (6-8 h)

### Mastery: mixed practice and capstones

#### [Interleaved practice and review](../dsa.html#m-mixed)

- Primer: Why does mixing topics in practice beat doing them in blocks? (14 min)
- Primer: Which technique does a problem statement point to? (18 min)
- Primer: How do you tell look-alike techniques apart? (16 min)
- Primer: How does the same problem change at n = 20, 10^3, 10^5 and 10^9? (15 min)
- Primer: When should you re-solve a problem, and how does Today's session schedule it? (13 min)
- Primer: How do you keep an error log that actually reduces mistakes? (12 min)
- Primer: What belongs on a DSA flashcard, and what does not? (12 min)
- Primer: How do you find your weak spots from your tracker? (12 min)
- Lab: Classification sprint: twenty statements in thirty minutes (45 min)
- Practice: 60 complete cards; 0 additional Later-list problems.

#### [Deriving solutions to unfamiliar problems](../dsa.html#m-derive)

- Primer: How do small cases reveal a pattern you can then prove? (15 min)
- Primer: How do you climb from a brute force to an optimal solution one fix at a time? (16 min)
- Primer: How do you spot that a new problem is a known one in disguise? (15 min)
- Primer: When does changing the representation crack a problem? (15 min)
- Primer: How do you decide what state a scan or a DP must remember? (16 min)
- Primer: How do you know your solution cannot be improved? (13 min)
- Primer: How do you explain a solution in 60 seconds? (13 min)
- Primer: How do you run a timed session or a mock interview? (14 min)
- Primer: How do you learn the most from a failed attempt? (13 min)
- Lab: Timed mock: two unseen problems in sixty minutes (75 min)

#### [Capstone dependency planner](../dsa.html#m-projectmasteryplanner)

- Project: Capstone: parallel build planner (8-12 h)

#### [Capstone local search service](../dsa.html#m-projectmasterysearch)

- Project: Capstone: searchable field notes (8-12 h)

#### [Capstone versioned key-value store](../dsa.html#m-projectmasterystorage)

- Project: Capstone: recoverable key-value notebook (10-12 h)
