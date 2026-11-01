# DSA page redesign: plan and decisions

Status: adopted on 1 November 2026. Companion to [the audit](dsa-audit.md). The card outline in the appendix is
regenerated from the content files at build time, so it always matches the page.

**Implementation status:** The guide currently has lessons, labs, tracked problems, selected full solutions and
stage projects. Most full problem-solution cards are still missing. New lesson links and lesson examples have not
all been independently verified. The remaining sections describe the intended design, not completed or verified
features. DSA lesson and verification sources are no longer Git-ignored; rebuilding also requires the existing
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

The same pass compiled all 377 lesson Python blocks. Of those, 279 eligible examples ran in temporary,
resource-limited working directories; 88 were not executed because they use file I/O, external dependencies or
other restricted operations, and 10 require context from other cards or skipped setup blocks. These counts do not
establish that every lesson example has been fully tested.

## 8. Writing standard

Plain British English, no em dashes, intuition before formalism, a worked example in every card, no filler. Every
explanation, restatement and code sample is written from scratch (nothing copied from LeetCode, GeeksforGeeks, books or
videos). Python 3.12 throughout, with one-line C++ or Java notes where costs differ.

## 9. Verification

`_build/verify_dsa.py` checks every card for its required parts and their order, applies the link policy to every
link, compiles every Python block, and runs every author's test script: each problem card has a script that compares
the brute force with the optimal code on random small inputs, and primer templates are stress-tested the same way.
Browser tests (Playwright) cover navigation, expansion and scroll position, self-checks, steppers, status buttons,
milestones, progress persistence, review resurfacing, filters, mobile width and the AI page. `node --test` covers
progress, sync and page integrity.

## 10. Projects

| Stage | Project |
|---|---|
| 1 | dsakit: a benchmark and stress-testing kit (used by every later project) |
| 2 | An ordered hash map, built and measured |
| 3 | Log metrics on a stream: sliding windows, rolling maxima and range counts |
| 4 | Logs bigger than memory: external sort and time-range queries |
| 5 | Type-ahead: an autocomplete service |
| 6 | A mini build system and task runner; route planner on real roads |
| 7 | Diff and merge tool |
| 8 | Cache and throttle: LRU and LFU caches with TTL, and a rate limiter |
| 9 | Counting at scale: stream analytics with sketches |
| 10 | Vector search from scratch; a BPE tokeniser checked against a reference |
| Capstones | Redis-lite; a mini search engine; TinyLSM, a storage engine (with a B+ tree variant as a stretch) |

## 11. Process

Research by four parallel agents (learning design, real-world projects, problem-bank audit, verified resources), then
this plan, then schema and UI, then module authors in parallel (one or two modules each, never sharing a file), then
problem-card authors per module once its ladder is fixed (separate `.cards.md` files), project authors (separate files,
appended by the lead), integration, verification and browser QA, with commits per stage.

## Appendix: card outline

Generated at build time.
