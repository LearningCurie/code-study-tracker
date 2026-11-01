---
key: mixed
name: Interleaved practice and review
stage: mastery
summary: Choose the right idea from an unlabelled statement, and keep every problem you have solved solvable, with mixed review sets, spaced re-solves, an error log and small cards.
why: Inside a module the technique is announced by the module's title, so practice there trains execution, not choice. Real problems, interviews and production incidents arrive without labels: the hard part is noticing that "longest stretch with at most k zeros" is a window while "exact sum with negative values" needs prefix sums, or that weighted edges rule out BFS. This module turns recognition into a trained skill with unlabelled review sets that open along the route and a pattern atlas of cues and counter-cues across the whole guide, and it gives you a review system (spaced re-solves, an error log, single-fact cards, weak-spot analysis) that keeps solved problems solvable months later. The same habits run good engineering teams: blameless post-mortems, runbooks that map symptoms to causes, and profiling before optimising.
outcomes:
- Explain why interleaved and spaced practice beat blocked practice, and use the review sets and Today's session as they are designed
- Classify an unfamiliar statement in about two minutes from its constraints, output shape and input structure, using cues and counter-cues from every module
- Decide between six pairs of look-alike techniques with one deciding question each, and settle doubts with a counterexample hunt
- Read the constraints first and change the algorithm as n moves from 20 to 10^9
- Run a spaced re-solve ladder from a blank file and grade each attempt honestly as Solved, Brute only or Stuck
- Keep an error log and single-fact cards, and use your tracker data to choose what to practise next
cues:
- You cannot name the technique within two minutes of reading the statement
- The problem looks like two techniques at once, or like a module you studied weeks ago
- A familiar problem with one constraint changed: negative values, weighted edges, a much larger n
- A problem you solved a month ago that you could not now rewrite from a blank file
traps:
- Reading the judge's topic tags before you have chosen, which removes exactly the decision this module trains
- Marking Solved after needing a nudge, so the problem never comes back for review
- Working through a whole review set in one sitting instead of one problem per session
- Re-solving by retyping remembered code instead of re-deriving it from a blank file
- Writing flashcards that hold whole solutions
systems:
- Anki, the open-source flashcard app, schedules reviews at expanding intervals; since version 23.10 it offers a scheduler based on SuperMemo's SM-2 algorithm or the newer FSRS, and the re-solve ladder applies the same idea to whole problems
- Blameless post-mortems in site reliability engineering record what failed and which check would have caught it, the same move as the error log
- On-call runbooks map symptoms to likely causes and first checks, a pattern atlas for production incidents
further:
- Article · 25 min | Dunlosky: Strengthening the student toolbox (practice testing, distributed and interleaved practice) | https://www.aft.org/ae/fall2013/dunlosky
- Article · 20 min | Rohrer, Dedrick and Stershic: Interleaved practice improves mathematics learning (free PDF) | https://files.eric.ed.gov/fulltext/ED557355.pdf
- Article · 40 min | Andy Matuschak: How to write good prompts (spaced-repetition cards that build understanding) | https://andymatuschak.org/prompts/#retrieval
- Article · 40 min | Michael Nielsen: Augmenting long-term memory (a working scientist's account of using Anki) | https://augmentingcognition.com/ltm.html
---

=== primer | Why does mixing topics in practice beat doing them in blocks? | 14 min
goal: Explain why interleaved and spaced practice train the choice of technique, and use this page's review sets and Today's session the way they are designed
link: Rohrer, Dedrick and Stershic, "Interleaved Practice Improves Mathematics Learning" (free PDF) | https://files.eric.ed.gov/fulltext/ED557355.pdf | 10 min: the abstract and the first three pages, which explain why blocked practice lets students skip choosing a strategy
link: Wikipedia: Desirable difficulty, "Spacing and interleaving" | https://en.wikipedia.org/wiki/Desirable_difficulty#Spacing_and_interleaving | 3 min: one short section on why the harder schedule wins later
practice: 219, 1679, 930

> [!key]
> Inside a block of problems from one module you know the technique before you read the statement, so you practise executing it but never practise **choosing** it. Mixing problems from different modules (**interleaving**) forces the choice, and spreading them over days (**spacing**) forces you to rebuild the idea from memory instead of copying it from the last problem. Both feel slower while you practise, and both win clearly on tests weeks later.

## Intuition

Picture learning to drive only in an empty car park, one manoeuvre at a time: twenty hill starts, then twenty reverse parks. Each one goes well because you know what is coming. On a real road nobody announces the manoeuvre; recognising which one the situation needs is half the skill. A problem list filed under "Sliding window" is the car park: the label answers the hardest question for you.

Algorithm problems are the same. "Longest substring with at most k distinct letters" and "count the subarrays whose sum is k" look alike, yet the first is a window and the second needs prefix sums. If you only ever meet them inside their own modules, you never practise telling them apart, and the first time you must, it is in an interview.

## How it works

### Three schedules

```text
blocked      W W W W   P P P P   T T T T     "which idea?" is answered by the module title
interleaved  W P T P   T W P W   P T W T     every problem starts with "which idea?"
spaced       day 1: W P T      day 4: P W T      day 11: T W P
             (W = window, P = prefix sums, T = two pointers)
```

### What the evidence says

- **Interleaving builds strategy choice.** Rohrer, Dedrick and Stershic gave 126 seventh-grade students the same maths problems over three months, arranged either in blocks or interleaved. Interleaving won on a surprise test a day later (effect size d = 0.42) and by more thirty days later (d = 0.79). Their explanation is the one above: with blocked practice, students know the strategy before they read the problem.
- **It holds in real classrooms.** In a preregistered trial with 54 classes over four months, the interleaved group scored 61% against 38% on an unannounced test a month later (Rohrer and colleagues, 2020).
- **Mix look-alikes, not everything.** A 2019 meta-analysis (Brunmair and Richter) found the benefit is largest when the categories are easy to confuse. That is why this guide pairs confusable techniques: window and prefix sums, BFS and Dijkstra, greedy and DP.
- **Spacing beats more of the same.** Spreading ten problems over two sessions virtually doubled scores four weeks later, while doing nine problems instead of three in one sitting made no difference at one or four weeks (Rohrer and Taylor, 2006).
- **It feels worse while it works better.** In a study summarised by Dunlosky, students who practised in blocks scored higher during practice, yet those who interleaved did three times better on the test a week later. Expect mixed practice to feel slow; that is the effect, not a sign of failure.

### How this page builds it in

- The **review sets** in this module have no topic labels. Each opens when you have marked every card of the module it follows as done: set 1 after Prefix sums, set 2 after Monotonic stacks, set 3 after Tries, set 4 after Weighted shortest paths, set 5 after Greedy, set 6 after Bits and number theory. A set only uses ideas you have met.
- **Today's session** has one review slot. It offers the oldest problem or card you marked **Brute only** or **Stuck** that has become due (three days after you marked it). When nothing is due and a set is open, it offers the next unsolved problem of the earliest open set. One mixed problem a day spreads the sets out on their own.
- The hints open one at a time: what to notice, then a nudge, then the key insight, which starts with the **Pattern** line. Name the technique yourself, in writing, before you open anything.

## Cost

Interleaving costs no extra problems; it changes the order. The real costs are two. Each problem takes longer, because the first two to five minutes go on choosing an idea. And your success rate during practice drops, which feels like going backwards. Budget one mixed problem per session: a Medium has a 30-minute timebox, so five sessions a week is about two and a half hours of mixed practice. Compare that with twenty window problems in one weekend: after the first three or four, the extra problems add almost nothing a month later (the overlearning result above).

## When to use it

- After you have met at least two techniques that can be confused. A brand-new technique is learnt best from a worked example and a few problems in a row (the cards and their Labs), and only then mixed.
- Keep short blocked bursts where they help: two or three problems right after a card get the mechanics into your hands. Then move on.

| Situation | Do this |
|---|---|
| You have just read a card | Its 2-3 Lab problems, in a row |
| A module is finished | Its review set opens: one mixed problem per session |
| Preparing for interviews | Mostly mixed problems, timed |
| A technique you keep failing | One short blocked burst, then back to mixed |

## Worked trace

Turning three topic pools into one interleaved week with the template below: always take the pool with the most problems left, unless it was the one just used.

```steps
Start: three pools; nothing chosen yet
    window: w1 w2 w3    prefix: p1 p2    twoptr: t1 t2
    order:  (empty)
---
window has the most left (3), so take {{w1}}
    window: w2 w3    prefix: p1 p2    twoptr: t1 t2
    order:  {{w1}}
---
All pools have 2 left; window was just used anyway and ties go by name, so {{p1}}
    window: w2 w3    prefix: p2    twoptr: t1 t2
    order:  w1 {{p1}}
---
window and twoptr have 2 left; take {{t1}} (window would also do; ties go by name)
    window: w2 w3    prefix: p2    twoptr: t2
    order:  w1 p1 {{t1}}
---
window has the most left (2): {{w2}}
    window: w3    prefix: p2    twoptr: t2
    order:  w1 p1 t1 {{w2}}
---
One each left: {{p2}}, {{t2}}, then {{w3}}; no two neighbours share a topic
    order:  w1 p1 t1 w2 {{p2}} {{t2}} {{w3}}
```

## Template

```python
import heapq


def interleave(pools):
    """pools: topic -> list of problems. Returns [(topic, problem)] with no two neighbours from the
    same topic whenever that is possible: take the largest remaining pool that is not the last topic."""
    queues = {t: list(v) for t, v in pools.items() if v}
    heap = [(-len(v), t) for t, v in queues.items()]
    heapq.heapify(heap)
    out, last = [], None
    while heap:
        left, topic = heapq.heappop(heap)
        if topic == last and heap:
            other = heapq.heappop(heap)
            heapq.heappush(heap, (left, topic))
            left, topic = other
        out.append((topic, queues[topic].pop(0)))
        last = topic
        if left + 1 < 0:
            heapq.heappush(heap, (left + 1, topic))
    return out


week = interleave({"window": ["w1", "w2", "w3"], "prefix": ["p1", "p2"], "twoptr": ["t1", "t2"]})
# [('window', 'w1'), ('prefix', 'p1'), ('twoptr', 't1'), ('window', 'w2'), ('prefix', 'p2'), ...]
```

Use it to build your own mixed sets from the problem banks of finished modules. It keeps each topic's order, and a clean result (no neighbours sharing a topic) exists exactly when no pool holds more than half of all problems, rounded up.

## Pitfalls

- **Peeking at the label.** The problem link opens the judge, which may show topic tags; do not scroll to them before you have chosen. The Solutions and Video links name the technique too.
- **Grading generously.** Needing the nudge means the choice was not yours. Mark Brute only or Stuck so the problem comes back.
- **Binge-solving a set.** Five mixed problems in one evening is blocked practice again, just with variety; the spacing is gone.
- **Struggling too long.** Difficulty helps only while it stays achievable. If after ten minutes you cannot name even two candidate ideas, open the first hint.
- **Mixing only unrelated topics.** The gain comes from look-alikes. A set of a heap problem, a trie problem and a bit trick trains less choice than a window problem next to a prefix-sum problem.

## Check yourself

Q: During a week of blocked practice your accuracy is 90%; in a week of mixed practice it is 60%. Which week taught you more, and why is the accuracy misleading?
A: Very likely the mixed week. Blocked accuracy is inflated because the block tells you the technique, so you never had to choose; the studies above show blocked groups doing better during practice and much worse weeks later. Mixed accuracy measures the skill you need, including the choice.

Q: Why does this guide interleave window problems with prefix-sum problems rather than with, say, trie problems?
A: Interleaving helps most when the categories are easy to confuse (Brunmair and Richter's meta-analysis). Window and prefix-sum problems share their surface ("subarray", "sum", "longest"), so mixing them forces you to find the deciding feature; a trie problem is rarely mistaken for either.

Q: Set 1 is open. You marked one problem Brute only on Monday evening and nothing else is marked. What does the review slot of Today's session offer on Tuesday, and what on Thursday evening?
A: On Tuesday nothing is due yet (an item becomes due three days after you marked it), so the slot offers the next unsolved problem of set 1. By Thursday evening the Monday item is due, so it is offered first, as a re-solve from a blank file.

Q: You have three free hours this weekend and the DP modules are fresh. Plan A: twelve DP problems on Saturday. Plan B: four problems on Saturday and four on Sunday, mixing DP with earlier modules. Which do you choose?
A: Plan B. Spreading practice over two sessions roughly doubled retention four weeks later in Rohrer and Taylor's study, while extra problems in one sitting added nothing; mixing in earlier modules also trains the choice between DP and its look-alikes (greedy, backtracking).

## Lab

Do the first three problems of review set 1, one per session if you can. Before writing any code, write down the idea you think applies and a one-line reason; compare it with the Pattern line only after solving.

- **219 Contains Duplicate II.** Expected: false for `nums = [4, 1, 2, 4], k = 2` (the two 4s are three apart) and true for `[4, 1, 4, 2]`; target O(n) time.
- **1679 Max Number of K-Sum Pairs.** Expected: 2 for `nums = [2, 2, 3, 3, 3], k = 5`, and 2 for `[1, 1, 1, 1], k = 2`.
- **930 Binary Subarrays With Sum.** Expected: 6 for `nums = [1, 0, 0, 1], goal = 1`, and 6 for `[0, 1, 0, 1], goal = 1`; target O(n).
- Expected for the whole Lab: you named an idea within about two minutes for each problem, and your written guess matched the Pattern line at least twice.

> [!know]
> You now know why mixed, spaced practice beats blocks, and how this page's review sets and Today's session schedule it for you.

=== primer | Which technique does a problem statement point to? | 18 min
goal: Map the cues and constraints of a statement to candidate techniques anywhere in this guide, and reject near-misses with counter-cues
link: USACO Guide: Time Complexity, "Common Complexities and Constraints" | https://usaco.guide/bronze/time-comp#common-complexities-and-constraints | 5 min: the table from input size to the complexity that fits; divide its operation counts by about 10 to 50 for Python
link: CodePath: UMPIRE interview strategy, "Match" | https://guides.codepath.org/compsci/UMPIRE-Interview-Strategy#match | 4 min: the Match step, which names the known problem category before any plan is made
practice: 438, 189, 1657

> [!key]
> Read a statement for three things, in this order: the **constraints** (which running times are even allowed), the **shape of the answer** (one number, a count, every solution, a structure) and the **structure of the input** (sorted, contiguous, pairs, grid, graph, stream). Together they usually leave two candidates; a **counter-cue** decides between them. The atlas below lists the cues and counter-cues for every technique in this guide.

## Intuition

A doctor does not test for every disease. Symptoms suggest a short list, and one deciding test rules out the look-alike. Statement cues are the symptoms ("longest contiguous", "fewest moves", "every way") and counter-cues are the deciding tests ("values can be negative", "moves cost different amounts").

## How it works

### The two-minute routine

1. **Constraints.** Turn n into a target complexity (the template below). n <= 20 invites exponential search; n = 10^5 demands O(n log n); n = 10^9 means you cannot even read n items.
2. **Answer shape.** Every solution listed points to search; a count or a best value over choices points to DP or greedy; a yes/no on a number that only flips once points to binary search on the answer.
3. **Input structure.** Sorted? Contiguous? Intervals? A grid or links? A stream?
4. **Atlas row, then its counter-cue.** If the counter-cue fires, move to the row it names.
5. **Nothing fits?** Write the brute force and climb from it (the module Deriving solutions to unfamiliar problems).

### The atlas

| Statement cue | Technique | Module | Counter-cue, then use |
|---|---|---|---|
| No idea at all, n tiny | Brute force with itertools | Solving problems you have not seen | Always a valid first step and your test oracle |
| "Seen this value or its complement before?" | Set or dict lookup | Hash tables, sets and counting | Need order, ranges or nearest values: sort or an ordered map |
| Count, group, anagram, duplicates | Counter or a canonical key | Hash tables, sets and counting | Only the top k counts: add a heap |
| Values in 1..n, O(1) extra space | Array as its own index | Arrays, dynamic arrays, strings and grids | Values unbounded: hashing |
| Rotate, transpose, spiral, simulate on a matrix | Index arithmetic and reversals | Arrays, dynamic arrays, strings and grids | Fewest moves across the grid: BFS |
| Brackets, nesting, undo, most recent first | Stack | Linked lists, stacks and queues | "Next greater": monotonic stack |
| Next pointers; cycle, middle, k-th from the end | Pointer rewiring, fast and slow pointers | Linked lists, stacks and queues | Random access needed: copy to a list |
| Sorted input, pair or triple with a target | Two pointers from both ends | Two pointers | Unsorted and indices wanted: hash map |
| Remove, compact or partition in place | Read and write pointers | Two pointers | Extra space allowed and order kept: build a new list |
| Longest or shortest contiguous stretch under a condition | Variable sliding window | Sliding window | Negative values or an exact target: prefix sums |
| Every window of length k | Fixed window | Sliding window | Window maximum: monotonic deque |
| Count subarrays with sum, remainder or balance exactly k | Prefix sums plus a count map | Prefix sums and difference arrays | Non-negative values and "at most": a window works too |
| Many range sums on unchanging data | 1D or 2D prefix sums | Prefix sums and difference arrays | Updates between queries: Fenwick tree |
| Many range additions, one read at the end | Difference array | Prefix sums and difference arrays | Reads between updates: Fenwick tree |
| Sorted or rotated array, find a position | Binary search on the index | Binary search and searching the answer | Unsorted, one query: just scan |
| Minimise the maximum, smallest x that works | Binary search on the answer | Binary search and searching the answer | Check not monotone in x: DP or search |
| Next greater or smaller, "until a taller one" | Monotonic stack | Monotonic stacks and queues | k-th greater rather than next: ordered structure |
| Maximum or minimum of every window | Monotonic deque | Monotonic stacks and queues | A single window: one scan |
| Sum of the minimum over all subarrays | Contribution counting with a monotonic stack | Monotonic stacks and queues | n <= 1000: running minimum over all subarrays |
| Order would make it easy: neighbours, groups | Sort first, then one pass | Sorting, partitioning and selection | Data arrives over time: heap or ordered map |
| k-th smallest of fixed data, asked once | Quickselect, heapq.nsmallest or sort | Sorting, partitioning and selection | Many queries or a stream: heap |
| Repeatedly take the best while items arrive | Heap | Heaps and priority queues | One query on fixed data: sort or select |
| Merge k sorted sources; running median | k-way merge; two heaps | Heaps and priority queues | Arbitrary deletions: ordered map |
| Start and end pairs: merge, overlap, free time | Sort by start and merge | Intervals and sweep line | Peak overlap: sweep events |
| Rooms needed, peak load | +1/-1 event sweep or a heap of end times | Intervals and sweep line | Weighted intervals: DP |
| Most non-overlapping intervals | Earliest end first | Intervals and sweep line | Intervals carry values: DP with bisect |
| Root and children; answer combines subtrees | Recursion returning values up | Binary trees and tree recursion | Answer depends on the path from the root: pass state down |
| Level by level, nearest to the root | Breadth-first traversal by levels | Binary trees and tree recursion | Path-shaped questions: DFS |
| Sorted data with inserts and deletes; floor, ceiling, rank | Ordered map: SortedList or bisect | Binary search trees and ordered maps | No updates: sorted list plus bisect |
| Many words sharing prefixes; words in a grid | Trie | Tries | Exact lookups only: a set |
| Grid cells or linked entities; reachability, components | BFS or DFS flood fill | Graph modelling and traversal | Links only added, queries online: union-find |
| Fewest moves, every move costs the same | BFS, multi-source if many starts | Graph modelling and traversal | Moves cost different amounts: Dijkstra |
| Prerequisites, dependency order | Topological sort | Graph modelling and traversal | Undirected: union-find or parent tracking |
| Two groups with "must differ" pairs | Two-colouring | Graph modelling and traversal | "Must be together" pairs: union-find |
| "Same group?" while links are added | Union-find | Union-find and minimum spanning trees | Need paths or distances: BFS |
| Connect everything at least total cost | Kruskal or Prim | Union-find and minimum spanning trees | One cheapest route: shortest paths |
| Weighted edges, cheapest route, weights >= 0 | Dijkstra | Weighted shortest paths | Negative edges: Bellman-Ford; costs 0 or 1: 0-1 BFS |
| At most k stops | k rounds of Bellman-Ford, or Dijkstra on (node, stops) | Weighted shortest paths | No hop limit: Dijkstra |
| List all, every, generate; n around 20 | Backtracking with pruning | Complete search and backtracking | Only a count or best: DP |
| Count ways or optimise over choices; states repeat | Memoised recursion, then a table | Dynamic programming: from recursion to tables | One choice provably safe: greedy |
| Modes: holding or not, cooldown | State-machine DP | Dynamic programming: from recursion to tables | No modes: take or skip |
| Two sequences: subsequence, edit, align | Two-sequence DP table | DP on grids, strings and knapsacks | Contiguous only: window or hashing |
| Right and down moves on a grid | Grid DP | DP on grids, strings and knapsacks | Moves in all directions: graph search |
| Items, weights, capacity or target sum | Knapsack DP | DP on grids, strings and knapsacks | Huge capacity, n <= 40: meet in the middle |
| A local choice looks safe; reach, fuel, balance | Greedy with an exchange argument | Greedy algorithms and exchange arguments | A small counterexample breaks it: DP |
| Burst or merge over a range; subsets of <= 20; digits of N | Interval, bitmask or digit DP | Advanced dynamic programming | Simple choices: ordinary DP |
| "Implement a class" with costs per operation | Hash map plus a list, heap or sorted list | Designing data structures | One operation only: one structure |
| Find a pattern in a long text; repeats | KMP or rolling hash | String algorithms | Short text: str.find |
| Once while others appear twice; subsets as masks | XOR and bitmasks | Bits and number theory | Other multiplicities: count bits per position |
| Modulo 10^9 + 7, gcd, primes, nCr | Modular arithmetic, sieve, combinations | Bits and number theory | Small values: compute directly |
| Range queries mixed with updates | Fenwick or segment tree | Range queries: Fenwick and segment trees | No updates: prefix sums or a sparse table |

## Cost

The routine takes about two minutes. A wrong technique typically costs 20 to 30 minutes before you notice, so even one avoided miss per week pays for the habit many times over. The template's estimate is O(1) per call: seven formulas.

## When to use it

On every unfamiliar statement, before writing code; and after every solve, to add or sharpen a row in your own copy. A row only suggests: the counter-cue and a hand-worked example decide. When two rows match, the problem is often both: sort then sweep, Dijkstra then DP over distances, BFS inside binary search.

## Worked trace

Classifying a statement nobody labelled: "n <= 10^5 positive integers; find the length of the shortest contiguous stretch whose sum is at least T."

```steps
Constraints first: n = 10^5, so the budget allows {{O(n log n)}}; all pairs (5 * 10^9) is out
    n = 10^5   ->   target O(n log n) or better
---
Answer shape: one length, a best value over many stretches
    shape: {{optimise over ranges}}
---
Input structure: one array, the stretch must be {{contiguous}}, values all {{positive}}
    structure: contiguous, positive
---
Atlas rows that match: "shortest contiguous stretch" (window) and "sum" (prefix sums)
    candidates: {{variable window}}  |  prefix sums
---
Counter-cue check: values are positive, so adding grows the sum and removing shrinks it
    window counter-cue ("negative values") does {{not}} fire
---
Decision: variable window, O(n). Change one word, "integers may be negative", and the counter-cue fires
    positive -> {{window}}
    may be negative -> {{prefix sums + monotonic deque}}
```

## Template

```python
import math

CLASSES = [
    ("O(n!)", lambda n: math.factorial(n) if n <= 20 else math.inf),
    ("O(2^n)", lambda n: 2.0 ** n if n <= 1000 else math.inf),
    ("O(n^3)", lambda n: float(n) ** 3),
    ("O(n^2)", lambda n: float(n) ** 2),
    ("O(n sqrt n)", lambda n: n * math.sqrt(n)),
    ("O(n log n)", lambda n: n * max(1.0, math.log2(n))),
    ("O(n)", lambda n: float(n)),
]


def target_complexity(n, budget=10**7):
    """Slowest complexity class whose operation count fits the budget (about one second of simple
    Python operations). Anything faster also fits; anything slower will not."""
    for name, ops in CLASSES:
        if ops(n) <= budget:
            return name
    return "O(log n) or O(1): you cannot even read n items"


# n = 8: O(n!)   20: O(2^n)   1000: O(n^2)   5000: O(n sqrt n)   10^5: O(n log n)
# 10^6: O(n)     10^9: O(log n) or O(1)
```

The budget of 10^7 simple operations per second is a rule of thumb for pure Python; work done inside C built-ins (`sorted`, `sum`, `set` operations) runs 10 to 100 times faster.

## Pitfalls

- **Matching surface words.** "Subarray" does not always mean a window, and a "tree" of dependencies may be a general graph.
- **Ignoring small constraints.** n <= 20 is an invitation: try every subset or permutation, or use bitmasks.
- **Stopping at the first row.** Always check the counter-cue; it exists because the look-alike is common.
- **Forgetting combinations.** Many Mediums are two rows at once: sort then two pointers, Dijkstra then DP.

## Check yourself

Q: What does `target_complexity(2000)` return, and is an O(n^2 log n) idea safe at n = 2000?
A: "O(n^2)": n^3 = 8·10^9 is far over the budget and n^2 = 4·10^6 fits. n^2 log n is about 4.4·10^7 simple operations, several seconds in pure Python, so it is risky; look for O(n^2) or move the inner work into C built-ins.

Q: A colleague classifies "fewest knight moves between two squares of a chessboard" as grid DP. Which cue did they miss?
A: Grid DP needs moves in a fixed direction (right and down), so the cells form an acyclic order. A knight moves in all directions, so the board is a graph with cycles and every move costs one: BFS.

Q: Why does "values may be negative" rule out the variable window for "shortest stretch with sum at least T"?
A: The window relies on monotone validity: removing an element from the left must never make an invalid window valid. With negatives, dropping a negative element raises the sum, so the window may stop shrinking too early (or never become valid) and miss shorter answers.

## Lab

For each problem write the atlas row you used and its counter-cue before coding, then compare with the Pattern line.

- **438 Find All Anagrams in a String.** Expected: `[0, 1, 3]` for `s = "cbacab", p = "abc"`; target O(n).
- **189 Rotate Array.** Expected: `[4, 5, 1, 2, 3]` for `[1, 2, 3, 4, 5], k = 2`, and `[3, 1, 2]` for `[1, 2, 3], k = 4` (k larger than n); O(1) extra space.
- **1657 Determine if Two Strings Are Close.** Expected: true for `("aab", "bba")`, false for `("aabbc", "abccc")` and false for `("ab", "aa")`.

> [!know]
> You now know how to classify a statement from its constraints, answer shape and input structure, and check the counter-cue before you commit.

=== primer | How do you tell look-alike techniques apart? | 16 min
goal: Ask the one deciding question for six confusable pairs of techniques, and settle any remaining doubt by letting a random tester hunt for a counterexample
link: USACO Guide: Greedy Algorithms with Sorting, "When Greedy Fails" | https://usaco.guide/silver/greedy-sorting#when-greedy-fails | 5 min: coin change and knapsack, where the natural greedy choice is wrong and DP is needed
practice: 1004, 523, 646

> [!key]
> Most wrong-technique mistakes come from six pairs that share their surface: sliding window or prefix sums, BFS or Dijkstra, greedy or DP, heap or sort or quickselect, backtracking or DP, union-find or BFS. Each pair has one **deciding question**, such as "does the condition stay true when I shrink the range?". When you are still unsure, write the simpler idea and let a random tester compare it with a brute force: a two-minute **counterexample hunt** beats twenty minutes of arguing.

## Intuition

Identical twins share a face; you tell them apart by one feature, a scar or a voice. You do not compare everything, you check the one thing that differs. Each pair below has such a feature, and it is always a property of the problem, never a word in the statement.

## How it works

### Six pairs and their deciding questions

| Pair | What they share | Deciding question | Yes | No |
|---|---|---|---|---|
| Sliding window or prefix sums | Contiguous subarrays, sums | Does shrinking a valid range keep it valid (and growing an invalid one keep it invalid)? | Window: O(n), O(1) space | Prefix sums plus a hash map: exact targets, negative values, counting |
| BFS or Dijkstra | Fewest or cheapest moves | Does every move cost the same? | BFS, O(V + E) | Dijkstra if costs >= 0; 0-1 BFS for costs 0 and 1; Bellman-Ford for negatives |
| Greedy or DP | Optimise over a sequence of choices | Can you prove one choice is always safe, and does a brute force fail to break it? | Greedy, usually sort plus one pass | DP over the choices |
| Heap, sort or quickselect | Smallest, largest, top k | Does data arrive or change between questions? | Heap: O(log n) per operation | Fixed data: sort for full order, heapq.nsmallest or quickselect for top k |
| Backtracking or DP | Choices, "ways" | Must every solution be listed, or only counted or optimised? | List them: backtracking (the output can be exponential) | Count or best, with repeating states: DP |
| Union-find or BFS | Connectivity | Are links only added and is the relation symmetric, with no paths or distances needed? | Union-find, near O(1) per operation | BFS or DFS: directed reach, distances, paths |

Two problems from this module's review sets show the first pair from both sides: 1004 (longest run of 1s with at most k flips) is a window, because a stretch with too many zeros stays bad as it grows; 523 (a stretch whose sum is a multiple of k) is prefix sums, because "multiple of k" is not monotone at all. And 2101 (bombs triggering bombs) looks like union-find but is not: a large bomb can reach a small one that cannot reach back, so the relation is not symmetric.

### Settle it with a counterexample hunt

When the deciding question is hard to answer by thought alone, test it. Write the candidate (fast, maybe wrong), an obviously correct brute force, and a generator of small random inputs; run thousands of cases and stop at the first disagreement. Sort the cases so the smallest failing input is found first: a three-element counterexample explains itself, a fifty-element one does not.

## Cost

A hunt costs about five minutes to write the brute force, two for the generator, and seconds to run 10,000 small cases. A wrong submission or a wrong interview answer costs far more. The techniques themselves:

| Option | Time | Extra space |
|---|---|---|
| Window / prefix sums with a map | O(n) / O(n) | O(1) or O(alphabet) / O(n) |
| BFS / Dijkstra with heapq | O(V + E) / O((V + E) log V) | O(V) / O(V + E) |
| Top k of n by sort / nsmallest / quickselect | O(n log n) / O(n log k) / O(n) average | O(n) / O(k) / O(1) in place |

## When to use it

Ask the deciding question whenever two atlas rows match. Run a counterexample hunt whenever your idea is greedy, or a window over values that might be negative, or any "this feels right" step you cannot prove in two sentences. Skip the hunt when a short proof exists: an exchange argument you can state is better evidence than any number of random tests.

## Worked trace

The window idea for "shortest stretch with sum at least k" on `[1, -1, 1, 3]` with k = 4. The correct answer is 2 (`[1, 3]`).

```steps
right = 0: add 1, sum = 1 < 4, nothing to record
    nums   {{1}}  -1   1   3      window [0, 0], sum 1
---
right = 1: add -1, sum = 0
    nums   1  {{-1}}   1   3      window [0, 1], sum 0
---
right = 2: add 1, sum = 1
    nums   1  -1  {{1}}   3       window [0, 2], sum 1
---
right = 3: add 3, sum = 4 >= 4: record length 4, then drop nums[0] = 1
    nums   1  -1   1  {{3}}       window [0, 3], sum 4, best = 4
---
sum is now 3 < 4, so the window stops shrinking and the loop ends
    nums   .  {{-1}}   1   3      window [1, 3], sum 3, best = 4
---
But dropping the -1 would have raised the sum back to 4 with length 2: the window answered {{4}}, the truth is {{2}}
    nums   .   .  {{1}}  {{3}}    [1, 3] sums to 4
```

The random hunt below finds an even smaller case on its own: `([-3, 3], 1)`, where the window never becomes valid and answers -1 although `[3]` alone works.

## Template

```python
import math
import random


def find_counterexample(candidate, oracle, gen, trials=10_000, seed=0):
    """Compare a fast idea with a slow, obviously correct oracle on random small inputs.
    Returns the smallest disagreeing input found, or None."""
    rnd = random.Random(seed)
    cases = sorted((gen(rnd) for _ in range(trials)), key=lambda c: len(repr(c)))
    for case in cases:
        if candidate(*case) != oracle(*case):
            return case
    return None


def shortest_at_least_window(nums, k):
    """Window idea: valid only when every value is non-negative."""
    best, s, left = math.inf, 0, 0
    for right, x in enumerate(nums):
        s += x
        while s >= k:
            best = min(best, right - left + 1)
            s -= nums[left]
            left += 1
    return best if best < math.inf else -1


def shortest_at_least_brute(nums, k):
    best = math.inf
    for i in range(len(nums)):
        s = 0
        for j in range(i, len(nums)):
            s += nums[j]
            if s >= k:
                best = min(best, j - i + 1)
                break
    return best if best < math.inf else -1


def gen_signed(rnd):
    return ([rnd.randint(-3, 4) for _ in range(rnd.randint(1, 6))], rnd.randint(1, 6))


print(find_counterexample(shortest_at_least_window, shortest_at_least_brute, gen_signed))
# ([-3, 3], 1); with values drawn from 0..4 instead it prints None
```

The same harness compares a greedy coin-change function with a DP one: on random coin systems that include 1 it reports `((1, 4, 5), 8)`, where greedy pays 5 + 1 + 1 + 1 (four coins) and DP pays 4 + 4 (two).

## Pitfalls

- **Trusting the examples.** Statement examples are chosen to explain, not to break; they rarely contain the negative value or the tie that kills a wrong idea.
- **Union-find on a directed relation.** It merges both ways, so it answers "same group" for pairs that only reach one way.
- **BFS with almost equal weights.** Costs of 1 and 2 are not equal costs; use Dijkstra, or split each cost-2 edge into two cost-1 edges.
- **A hunt with a buggy oracle.** Check the brute force on the statement's examples first, or the hunt will "find" correct code wrong.

## Check yourself

Q: "Longest stretch whose sum is at most k, all values non-negative": window or prefix sums? Give the reason in one sentence.
A: A window: with non-negative values, removing an element from a valid stretch keeps the sum at most k, and adding to an invalid stretch keeps it above k, so validity is monotone and each end only moves forward.

Q: Friendships are added one at a time. After each addition you must answer either (a) "are these two people connected?" or (b) "how many links separate them?". Which structure for each?
A: (a) union-find: links are only added, the relation is symmetric and only membership is asked, at near O(1) per operation. (b) BFS: union-find stores no paths or distances, so you need a traversal of the graph (from one endpoint, O(V + E) per question).

Q: Someone finds the median of a fixed list by pushing every element onto a heap and popping n/2 times. Is it correct, what does it cost, and what would you use instead?
A: It is correct and costs O(n log n), no better than sorting. For one median of fixed data, sort once (`sorted(a)[len(a) // 2]`) or use quickselect for O(n) on average; the two-heap method earns its keep only when values arrive over time.

## Lab

- **1004 Max Consecutive Ones III.** Before coding, answer the window-or-prefix-sums question in writing. Expected: 4 for `nums = [1, 0, 1, 1, 0, 1, 0], k = 1`, and 0 for `[0, 0, 0], k = 0`; target O(n), O(1) space.
- **523 Continuous Subarray Sum.** Same question first. Expected: true for `[2, 4, 1], k = 7`, false for `[3, 1], k = 5`, true for `[5, 0, 0], k = 3` (the two zeros form a valid stretch).
- **646 Maximum Length of Pair Chain.** Write a greedy version and an O(n^2) DP version, then run `find_counterexample` between them. Expected: 2 for `[[1, 3], [2, 4], [5, 6], [4, 5]]`, 3 for `[[1, 2], [3, 4], [5, 6]]`, and the hunt returns None.

> [!know]
> You now know the deciding question for six look-alike pairs and how to settle a doubtful idea with a counterexample hunt.

=== primer | How does the same problem change at n = 20, 10^3, 10^5 and 10^9? | 15 min
goal: Read the constraints first and pick a different algorithm for the same story as n grows, including the point where n is too large to read the input at all
link: Competitive Programmer's Handbook, section 2.3 "Estimating efficiency" | https://cses.fi/book/book.pdf#page=31 | 5 min: PDF page 31, the table from input size to the time complexity that fits; scale its numbers down for Python
practice: 1442, 1823, 2101

> [!key]
> The constraints are part of the problem: they tell you which algorithm the setter wants. The same story needs brute force at n = 20, a quadratic or simple DP at 10^3, an O(n log n) or O(n) idea at 10^5, and at 10^9 something that never touches every item, such as a formula, a binary search or fast exponentiation. Read n (and the value range, and the number of queries) before you design anything.

## Intuition

Delivering 5 parcels, you can try every route. Delivering 5,000, you need a rule such as "nearest next". Delivering to every house in a country, you no longer plan routes at all; you plan depots and use averages. The task did not change, its size did, and each size has its own tools.

## How it works

### One story at four sizes

A robot climbs n steps, moving 1, 2 or 3 steps at a time. How many different routes reach the top, modulo 1,000,000,007? Let f(n) be the answer: the last move was 1, 2 or 3 steps, so f(n) = f(n - 1) + f(n - 2) + f(n - 3), with f(0) = 1 and f(negative) = 0.

| n | Budget allows | What works | Why the previous version stops working |
|---|---|---|---|
| 20 | Exponential | List every route explicitly: 121,415 routes, about 0.2 s | (nothing yet) |
| 10^3 | O(n^2) | A loop over the recurrence | Listing is hopeless (about 10^264 routes), and memoised recursion is 1,000 calls deep: Python's default recursion limit is 1,000, so it raises RecursionError |
| 10^5 | O(n log n) | The same loop with three rolling variables, taking `% MOD` every step | Without the modulus the exact count has 26,465 digits and every addition gets slower |
| 10^9 | O(log n) | Raise the 3 x 3 step matrix to the n-th power by repeated squaring: about 30 squarings | The O(n) loop managed 10^7 steps in 2.7 s, so 10^9 would take about 4.5 minutes |

### Other stories, the same lesson

| Story | n = 20 | n = 10^3 | n = 10^5 | n = 10^9 |
|---|---|---|---|---|
| Count pairs i < j with a[i] + a[j] <= T | All pairs | All pairs (5·10^5) | Sort, then two pointers | The values are 1..n: count by arithmetic, O(1) |
| Can a subset reach the sum T? | Try all 2^20 subsets | Subset-sum DP if T <= 10^4 (O(nT)) | Only with special structure; in general it is NP-hard | Values 1..n: every T from 0 to n(n + 1)/2 is reachable |

The second table carries a warning: when a problem that is hard in general appears with a large n, the constraints are hiding structure (small values, a special sequence) that you are meant to find.

## Cost

Counting the work for the climbing story: listing routes costs one step per route, about 1.84^n; the loop costs n iterations of three additions; the matrix method costs one or two 3 x 3 multiplications (27 multiply-adds each) per bit of n, so about 2 · 30 · 27 = 1,620 operations at n = 10^9. Same answer, from minutes down to under a millisecond.

## When to use it

Always, as the first two minutes of a problem: n, the value range, the number of queries q, and the time limit. Check the product of the sizes, not each one alone: n = 10^5 with q = 10^5 queries rules out O(n) per query. When the constraints are tiny, enjoy it: a clean brute force is the intended solution, not a lack of ambition.

## Worked trace

`routes_matrix(10)` processes the bits of 10 = 0b1010 from the lowest, keeping `result` (the product so far) and `step` (the matrix squared once per bit).

```steps
Start: result = M^0 (the identity), step = M^1; bits of 10 from the right: 0, 1, 0, 1
    n = 1010 (binary)   result = M^0   step = M^1
---
Bit 0 is {{0}}: leave result, square step
    n = 101             result = M^0   step = {{M^2}}
---
Bit 1 is {{1}}: result = result * step, then square step
    n = 10              result = {{M^2}}   step = {{M^4}}
---
Bit 2 is {{0}}: square step only
    n = 1               result = M^2   step = {{M^8}}
---
Bit 3 is {{1}}: result = M^2 * M^8
    n = 0               result = {{M^10}}
---
f(10) is the top-left entry of M^10: {{274}}, matching 1, 1, 2, 4, 7, 13, 24, 44, 81, 149, 274
    f(0..10) = 1 1 2 4 7 13 24 44 81 149 {{274}}
```

## Template

```python
MOD = 1_000_000_007


def routes_loop(n):
    """n up to about 10^6: bottom-up with three rolling variables. O(n) time, O(1) space."""
    a, b, c = 0, 0, 1                     # f(i - 3), f(i - 2), f(i - 1), starting from f(0) = 1
    for _ in range(n):
        a, b, c = b, c, (a + b + c) % MOD
    return c


def mat_mult(X, Y):
    return [[sum(X[i][t] * Y[t][j] for t in range(3)) % MOD for j in range(3)] for i in range(3)]


def routes_matrix(n):
    """n up to 10^18: (f(i), f(i-1), f(i-2)) = M (f(i-1), f(i-2), f(i-3)), so apply M^n to
    (f(0), f(-1), f(-2)) = (1, 0, 0). O(log n) matrix products."""
    result = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    step = [[1, 1, 1], [1, 0, 0], [0, 1, 0]]
    while n:
        if n & 1:
            result = mat_mult(result, step)
        step = mat_mult(step, step)
        n >>= 1
    return result[0][0]


assert routes_loop(10) == routes_matrix(10) == 274
assert routes_loop(10**5) == routes_matrix(10**5)
```

## Pitfalls

- **The recursion limit.** Memoised recursion is an O(n) algorithm that still crashes at n = 1,000 in Python; go bottom-up, or raise the limit only with care.
- **Forgetting the modulus.** Python's integers never overflow, so nothing warns you; the numbers just grow until every operation is slow. In C++ or Java they overflow silently.
- **Reading "values up to 10^9" as "n up to 10^9".** A large value range forbids arrays indexed by value (use a dict or coordinate compression) but says nothing about n.
- **Ignoring the number of test cases.** "Up to 10^4 test cases, sum of n up to 2·10^5" is a different budget from "10^4 test cases of n = 2·10^5".

## Check yourself

Q: `routes_loop(10**7)` took 2.7 s. Roughly how long would `routes_loop(10**8)` take, and what does that tell you about n = 10^8 in Python?
A: About 27 s, ten times as long, because the loop is linear. Even an O(n) loop of simple Python operations is too slow around 10^8; you need either C-level built-ins (or NumPy) or an algorithm below O(n).

Q: Why does the memoised version fail at n = 1,000 but succeed at n = 600?
A: Each pending call f(i) waits on f(i - 1), so the call stack grows to about n frames before anything returns. Python's default recursion limit is 1,000 frames, so n = 600 fits and n = 1,000 raises RecursionError, although the algorithm itself is fine.

Q: A problem has n <= 300 and asks for something you can do in O(n^3) or, with a clever trick, in O(n). Which do you write first?
A: The O(n^3) version if it is simpler: 2.7·10^7 simple operations is a few seconds in Python, so check whether the inner loop can be cut to O(n^2) (9·10^4 operations, instant). With n this small the setter expects a cubic or quadratic idea; the O(n) trick is a bonus, not the target.

## Lab

Write down the target complexity from each problem's constraints before choosing an idea.

- **1442 Count Triplets That Can Form Two Arrays of Equal XOR** (n <= 300). Expected: 2 for `[2, 2, 2]` and 2 for `[1, 3, 2]`; an O(n^2) solution is comfortably within the budget.
- **1823 Find the Winner of the Circular Game** (n <= 500). Solve it once by simulation and once in O(n). Expected: 5 for `n = 6, k = 2`, and 4 for `n = 4, k = 1`.
- **2101 Detonate the Maximum Bombs** (n <= 100). Expected: 2 for `[[0, 0, 2], [3, 0, 1], [1, 0, 1]]`; the constraint permits O(n^3).

> [!know]
> You now know how to read the constraints first and match the algorithm to the size, including when n is too large to touch every item.

=== primer | When should you re-solve a problem, and how does Today's session schedule it? | 13 min
goal: Run a spaced re-solve ladder (a few days, one week, three weeks, two months) from a blank file, grade every attempt honestly, and let this page handle the first rung
link: Cepeda and colleagues, "Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention" (free PDF) | https://www.yorku.ca/ncepeda/publications/CVRWP2008.pdf | 4 min: the abstract on page 1: the best gap between reviews grows with how long you want to remember, from about 20-40% of a one-week horizon to 5-10% of a one-year horizon
link: Rohrer and Taylor, "The Effects of Overlearning and Distributed Practice" (free PDF) | https://files.eric.ed.gov/fulltext/ED505642.pdf | 3 min: the abstract on page 1: the same ten problems over two sessions instead of one doubled the score four weeks later
practice: 946, 240, 328

> [!key]
> Solving a problem once proves you could do it that day. Re-solving it **from a blank file** after a gap, then after longer gaps (a few days, a week, three weeks, two months), makes it something you can do months later under pressure. Grade every attempt honestly: **Solved** only if you wrote the brute force and the optimal solution yourself; **Brute only** if you reached a correct but slow solution or needed a nudge; **Stuck** if you needed the key insight or the solution. Brute only and Stuck come back in Today's session three days later; the longer rungs are yours to schedule.

## Intuition

Memory fades fastest just after learning. Pulling an idea back out when it has started to fade (but is not gone) strengthens it far more than rereading it while it is fresh: this is the testing effect combined with spacing. One successful re-solve after two months is worth more than three re-solves in the same week, and a failed re-solve tells you something a fresh solve cannot: which part you only understood while it was in front of you.

## How it works

### The ladder

| Rung | Gap after the last attempt | Who schedules it |
|---|---|---|
| 0 | 3 days, after Brute only or Stuck | This page: Today's session |
| 1 | 1 week, after a clean solve | You: your journal |
| 2 | 3 weeks | You |
| 3 | 2 months | You |
| Off | (none) | The problem retires to the bank pool |

The rule is one line: a clean solve climbs one rung; anything else drops back to rung 0. The gaps expand because, as Cepeda's data shows, the best gap is a sizeable fraction of how long you want to remember, so each successful retrieval earns a longer one.

### The blank-file rule

A re-solve starts from an empty file with the statement only: no old code, no notes. Keep the page's timebox (Easy 20, Medium 30, Hard 45 minutes). Write the brute force first, then the optimal version, then test both against each other on small random inputs. Retyping code you remember is not a re-solve; it tests your typing, not your reasoning.

### Grading honestly

| What happened | Mark |
|---|---|
| Brute force and optimal written alone, within about 1.5x the timebox; you can state the cost and why it is correct | Solved |
| Only a correct slow solution, or you needed "What to notice" or "A nudge", or you went far over the timebox | Brute only |
| You needed "Key insight" or read a solution | Stuck |

### How Today's session runs rung 0

- Marking **Brute only** or **Stuck** records the time; three days later the item becomes due.
- The review slot holds one item per session: the oldest due item; if nothing is due, the next problem of the earliest open review set.
- After the re-solve, mark the new result. **Solved** takes it out of the queue. If the result is the same status as before, clear it and set it again so the date updates (clicking a selected status clears it).
- The **Review** view lists everything currently marked Brute only or Stuck, for a longer catch-up session.
- The page does not schedule rungs 1 to 3; the template computes those dates for your journal.

## Cost

Derive the weekly load before you commit to it. If you add N new problems a week and each climbs r rungs, then once the pipeline is full you face about N x r re-solves a week. With N = 5 and all four rungs that is 20 re-solves a week; at 15 to 20 minutes each (re-solves are faster than first solves), five to seven hours, which is too much. So be selective: give every Brute only or Stuck problem the full ladder, give clean first solves only rungs 1 and 3, and cap reviews at about a third of your practice time. That brings N = 5 down to roughly 8 to 12 re-solves a week.

## When to use it

Use the full ladder for core problems of each module, for anything you marked Brute only or Stuck, and for interview staples. Skip it for bank problems that taught you nothing new, and for problems you can only "solve" by remembering code: rewrite their cards instead, then re-solve. If the queue grows beyond one or two re-solves per session, stop adding new problems for a few days; review debt only grows.

## Worked trace

One problem's history through the ladder (dates from the template below).

```steps
2 Nov: first attempt, needed the key insight: {{Stuck}}. Rung 0: due in 3 days
    history: Stuck                         next: {{5 Nov}}
---
5 Nov (Today's session offers it): reached only the slow version: {{Brute only}}. Back to rung 0
    history: Stuck, Brute                  next: {{8 Nov}}
---
8 Nov: clean solve from a blank file: {{Solved}}. Rung 1: one week
    history: Stuck, Brute, Solved          next: {{15 Nov}}
---
15 Nov: clean again. Rung 2: three weeks
    history: ..., Solved, Solved           next: {{6 Dec}}
---
6 Dec: clean again. Rung 3: two months
    history: ..., Solved x3                next: {{4 Feb}}
---
4 Feb: clean after two months: off the ladder
    history: ..., Solved x4                next: {{none}}
```

## Template

```python
from datetime import date, timedelta

LADDER = [3, 7, 21, 60]          # days until the next re-solve, by rung


def next_resolve(history):
    """history: [(date, result)] oldest first, result in {"solved", "brute", "stuck"}.
    A clean solve climbs one rung; anything else drops to rung 0 (a re-solve in 3 days).
    Returns the next re-solve date, or None once the problem has climbed off the ladder."""
    rung = 0
    for _, result in history:
        rung = rung + 1 if result == "solved" else 0
    if rung >= len(LADDER):
        return None
    return history[-1][0] + timedelta(days=LADDER[rung])


h = [(date(2026, 11, 2), "stuck"), (date(2026, 11, 5), "brute"), (date(2026, 11, 8), "solved")]
print(next_resolve(h))                                  # 2026-11-15
print(next_resolve([(date(2026, 11, 2), "solved")]))    # 2026-11-09: a clean first solve starts at rung 1
```

## Pitfalls

- **Retyping instead of re-deriving.** If you remember the code, write the brute force first anyway, and say the invariant aloud before the optimal version.
- **Re-solving the same day.** It feels productive and measures short-term memory only.
- **Generous grading.** A Solved mark removes the problem from review; if you hesitated at the key step, it was not Solved.
- **Letting the queue grow.** One or two re-solves per session is sustainable; ten is a backlog you will skip.
- **Re-solving favourites.** The problems you dislike are usually the ones that need it.

## Check yourself

Q: A history reads `[(1 Mar, solved), (8 Mar, stuck)]`. When is the next re-solve, and why not later?
A: 11 Mar. The Stuck result drops the problem back to rung 0, three days after the failed attempt; the earlier clean solve does not count any more, because the failure shows the idea had not stuck.

Q: Why do the gaps grow (3, 7, 21, 60 days) instead of staying at one week?
A: Each successful retrieval makes the memory more durable, and the best gap is a fraction of how long you want to remember (Cepeda and colleagues: roughly 20-40% of a one-week horizon, 5-10% of a one-year horizon). Fixed short gaps spend time re-proving what you already hold; growing gaps test you near the point of forgetting, which is where retrieval helps most.

Q: You re-solve 946 cleanly but it takes 50 minutes against a 30-minute timebox. What do you mark, and what happens next?
A: Brute only: past about 1.5x the timebox the solution is not yet fluent, even if it is correct. Today's session brings it back three days later; once a re-solve is clean and on time, mark Solved and put the one-week date in your journal.

## Lab

Solve each problem today, record the attempt as `(date, result)`, and compute its next date with `next_resolve`. Expected: three dates in your journal (three days out for Brute only or Stuck, one week out for a clean solve).

- **946 Validate Stack Sequences.** Expected: false for `pushed = [1, 2, 3], popped = [3, 1, 2]` and true for `popped = [2, 3, 1]`; O(n).
- **240 Search a 2D Matrix II.** Expected: true for target 6 and false for target 10 in `[[1, 4, 7], [2, 5, 8], [3, 6, 9]]`; O(m + n).
- **328 Odd Even Linked List.** Expected: 1 3 5 2 4 6 from the list 1 to 6, and a single node 7 unchanged; O(1) extra space.

> [!know]
> You now know how to run a spaced re-solve ladder from a blank file, grade attempts honestly, and combine it with Today's session.

=== primer | How do you keep an error log that actually reduces mistakes? | 12 min
goal: Record every failed or slow attempt in one line with a category, review the log by category each week, and turn the most frequent category into a specific drill
link: USACO Guide: Debugging Checklist, "Wrong Answer or Runtime Error" | https://usaco.guide/general/debugging-checklist#wrong-answer-or-runtime-error | 5 min: the checklist to run before you decide which category a mistake belongs to; the "Time Limit Exceeded" section after it covers the complexity category
practice: 1283, 1248, 2300

> [!key]
> A problem journal records what you learnt; an **error log** records how you fail. One line per mistake: date, problem, **category**, what happened. Categories (misread, wrong technique, broken invariant, off-by-one, complexity, missed edge case, Python cost trap) let you review by kind of mistake, so one drill fixes a whole class of future bugs instead of one problem.

## Intuition

Aviation checklists and blameless post-mortems exist because people repeat the same few failure modes. A post-mortem does not ask "who was careless?" but "which check would have caught this?". Your log asks the same question of your code, and after a month the answer is usually one or two categories that account for most of your losses.

## How it works

### The categories

| Category | Typical symptom | Drill that targets it |
|---|---|---|
| misread | Solved a different problem; missed a constraint | Restate the problem in one sentence and list the constraints before coding |
| technique | Right code for the wrong idea | Two classification sprints; add the missed cue to your atlas |
| invariant | Pointers or windows drift; wrong on some inputs | Write the invariant as a comment first, then assert it while testing |
| off-by-one | Fails at the boundaries; empty or size-one inputs | Half-open ranges; test sizes 0, 1, 2 on purpose |
| complexity | Correct but times out | Compute the target from n before designing; time a worst-case input |
| edge-case | Fails on duplicates, negatives, zeros, extremes | Run the edge-case catalogue before submitting |
| python-cost | Hidden O(n) inside a loop | Check the cost sheet: `list.pop(0)`, `x in list`, `s +=` in loops, slicing |

### The line and the weekly review

One line, written right after the attempt: `2026-11-04 | 930 | off-by-one | did not seed the counts with prefix 0`. Once a week, count by category, take the largest, and apply its drill to every problem for the next week. At the next review, check whether that category's count fell. Keep the categories few: seven is enough to separate the causes without agonising over the label.

## Cost

About 30 seconds per entry and ten minutes per weekly review. Over a month that is under an hour, and it typically removes the single most expensive habit you have (often off-by-one or skipping the constraints), which costs far more than an hour.

## When to use it

Log every Brute only or Stuck result and every wrong submission, including the ones you fixed in two minutes: the cheap mistakes recur most. Do not log typos that the interpreter flagged instantly unless the same typo keeps coming back. When a mistake fits two categories, choose the earliest step of the solving loop that went wrong (a misread that led to the wrong technique is a misread).

## Worked trace

Turning a failed attempt into one log line.

```steps
1283 fails a hidden test: the answer is too small by one
    symptom: {{wrong answer}}, off by one
---
Reproduce with the smallest input that fails, found with a brute force
    nums = [4, 4], threshold = 2   expected 4, got {{3}}
---
Find the line: the check summed x // d, which rounds down; the statement rounds each quotient up
    sum(x // d)  {{should be sum((x + d - 1) // d)}}
---
Which check would have caught it? Restating the statement in my own words: "each quotient rounded up"
    category: {{misread}}
---
Write the line
    2026-11-06 | 1283 | misread | rounded quotients down, not up
---
At the weekly review off-by-one has three entries, the most: next week's drill is {{test sizes 0, 1, 2 on purpose}}
    off-by-one 3   technique 2   edge-case 1   ...
```

## Template

```python
from collections import defaultdict

DRILLS = {
    "misread": "Restate the problem in one sentence and list the constraints before coding.",
    "technique": "Do two classification sprints; add the missed cue to your atlas.",
    "invariant": "Write the invariant as a comment first, then assert it while testing.",
    "off-by-one": "Use half-open ranges; test sizes 0, 1, 2 on purpose.",
    "complexity": "Compute the target from n before designing; time a worst-case input.",
    "edge-case": "Run the edge-case catalogue: empty, one, duplicates, negatives, extremes.",
    "python-cost": "Check the cost sheet: list.pop(0), x in list, s += in loops, slicing.",
}


def review(log_lines, top=3):
    """log_lines: 'date | problem | category | what happened'. Returns the commonest categories,
    each with its count, its drill and the problems that showed it."""
    by_cat = defaultdict(list)
    for line in log_lines:
        day, problem, category, note = [part.strip() for part in line.split("|", 3)]
        by_cat[category].append(problem)
    ranked = sorted(by_cat.items(), key=lambda kv: -len(kv[1]))[:top]
    return [(cat, len(probs), DRILLS.get(cat, "new category: define a drill"), probs)
            for cat, probs in ranked]


LOG = """2026-11-02 | 1004 | technique | tried prefix sums; the window was enough
2026-11-03 | 523 | edge-case | forgot that the stretch needs length >= 2
2026-11-04 | 930 | off-by-one | did not seed the counts with prefix 0
2026-11-06 | 1283 | misread | rounded the quotients down; the statement rounds up
2026-11-07 | 2300 | complexity | nested loop, 10^10 pairs
2026-11-09 | 1944 | technique | reached for a heap; a stack was the idea
2026-11-10 | 1209 | python-cost | rebuilt the string with += inside the loop
2026-11-12 | 1248 | off-by-one | atMost(k - 1) computed with the wrong window bound
2026-11-13 | 2125 | off-by-one | skipped the last non-empty row""".splitlines()
print(review(LOG)[0])
# ('off-by-one', 3, 'Use half-open ranges; test sizes 0, 1, 2 on purpose.', ['930', '1248', '2125'])
```

## Pitfalls

- **Vague categories.** "Bug" or "silly mistake" cannot be drilled. Name the check that would have caught it.
- **Logging only disasters.** The two-minute fixes are the most frequent and the cheapest to eliminate.
- **Never reviewing.** A log nobody reads is a diary. Put the weekly review in your calendar.
- **Too many categories.** Twenty categories split the counts so thin that nothing stands out.
- **Blame instead of process.** "I was careless" changes nothing; "I skip the size-one test" leads to a drill.

## Check yourself

Q: Your solution passed every example but timed out on n = 10^5 because you used `nums.pop(0)` inside a loop. Which category, and why not "complexity"?
A: python-cost. The algorithm was linear on paper; the hidden O(n) cost of `list.pop(0)` (every element shifts left) made it quadratic. The drill is the Python cost sheet (use `collections.deque.popleft`), not a new algorithm.

Q: Why review by category rather than re-reading each problem's notes?
A: Mistakes cluster by kind, not by problem. Ten off-by-one errors in ten different problems look unrelated problem by problem, but by category they become one habit with one drill (half-open ranges, size 0-2 tests) that prevents the next ten as well.

Q: A log line reads `1004 | bug | forgot something`. What is wrong with it, and how would you rewrite it?
A: Neither the category nor the note says which check failed, so it cannot be counted or drilled. Rewrite it with a real category and a precise note, for example `2026-11-02 | 1004 | invariant | moved left before decrementing the zero count`.

## Lab

Solve the three problems and log every slip, including ones your own tests caught. Then run `review` on your lines. Expected: either at least one category with two or more entries, or an empty log you can honestly defend.

- **1283 Find the Smallest Divisor Given a Threshold.** Expected: 6 for `nums = [2, 7, 11], threshold = 5`, and 4 for `[4, 4], threshold = 2`.
- **1248 Count Number of Nice Subarrays.** Expected: 4 for `[1, 2, 1, 2, 1], k = 2`, and 0 for `[2, 4], k = 1`.
- **2300 Successful Pairs of Spells and Potions.** Expected: `[1, 3]` for `spells = [2, 5], potions = [1, 2, 3, 4], success = 8`.

> [!know]
> You now know how to log mistakes by category and turn the most frequent one into a drill that prevents a whole class of bugs.

=== primer | What belongs on a DSA flashcard, and what does not? | 12 min
goal: Write small single-fact cards for cues, invariants, recurrences, costs and pitfalls, schedule them with expanding gaps, and never put a whole solution on a card
link: Andy Matuschak: How to write good prompts, "Properties of effective retrieval practice" | https://andymatuschak.org/prompts/#properties | 10 min: the five properties (focused, precise, consistent, tractable, effortful); then skim "Procedural knowledge"
link: Wikipedia: Leitner system, "Method" | https://en.wikipedia.org/wiki/Leitner_system#Method | 3 min: the box scheme behind expanding review gaps, if you prefer paper cards
practice: 1209, 1019, 16

> [!key]
> A good card asks for **one fact you need to rebuild a solution**: the cue that points to a technique, the invariant that makes it correct, the recurrence, the cost with its reason, or the bug to avoid. A card holding a whole solution trains you to recognise code you have seen, not to produce it. Write four or five cards per solved problem from your journal, review them for a few minutes a day, and let a scheduler space them out.

## Intuition

A card is an interview question you can answer in one breath: "why is the monotonic stack linear?", "what must the prefix-count map start with?". Problems test whether you can build a solution; cards keep the parts sharp between problems, the way scales keep a pianist's fingers ready for pieces.

## How it works

### Five kinds of card

| Kind | Front | Back |
|---|---|---|
| Cue to technique | Count subarrays with an exact sum, values may be negative: which idea? | Prefix sums with a count map |
| Invariant | Monotonic stack for next greater: what is true of the stack? | Values strictly decrease from bottom to top, and every element on it is still waiting for its answer |
| Recurrence | Fewest coins for amount a: recurrence and base case? | best[a] = 1 + min(best[a - c]) over coins c <= a; best[0] = 0 |
| Cost with reason | Why is the monotonic stack O(n) overall? | Each index is pushed once and popped at most once |
| Pitfall | Prefix-count map: what must it contain before the loop? | {0: 1}, so stretches that start at index 0 are counted |

### What makes a card bad

- **Whole solutions.** "Solve 1209" with twenty lines of code on the back: you will recognise the code and still fail to write it.
- **Vague fronts.** "What is dynamic programming?" has no checkable answer, so you cannot grade yourself honestly.
- **Two facts at once.** "Cost and invariant of a monotonic stack" gets graded as right when you knew one of them. Split it.
- **Facts you never understood.** A card cannot create understanding; work the problem first, then write the card.

### Scheduling

Use a spaced-repetition app such as Anki (its scheduler is based on SuperMemo's SM-2 algorithm, or the newer FSRS), or a Leitner box: cards move up a box each time you answer correctly and back to the first box when you miss, and higher boxes are reviewed less often. Anki imports plain text files with one card per line and fields separated by tabs, which the template below produces.

## Cost

Say you solve five problems a week and write four cards each: 20 new cards a week. With gaps that roughly double after each correct answer, a card costs about six to eight reviews in its first year, so each week's batch costs about 140 reviews spread over the year. In steady state that is about 20 reviews a day; at roughly ten seconds each, three to four minutes a day.

## When to use it

Write cards right after the journal entry for a solved problem, and from each module's "Spot it" cues. Review them as a warm-up at the start of a session. Do not let cards replace problems: cards keep the parts ready, but only re-solving from a blank file proves you can assemble them.

## Worked trace

Turning one journal entry (for 930, counting 0/1 subarrays with a given sum) into cards with the template.

```steps
The journal entry: problem, cue, technique, invariant, cost, pitfall
    cue: count subarrays with an exact sum, zeros allowed
    technique: prefix sums with a count map
---
Card 1, cue to technique: the front is the {{cue}}, the back names the idea
    count subarrays with an exact sum, zeros allowed: which idea?
    -> {{prefix sums with a count map}} (930 Binary Subarrays With Sum)
---
Card 2, invariant: one sentence that must hold at every step
    prefix sums with a count map: what stays true at every step?
    -> seen[s] = number of {{earlier}} prefixes equal to s
---
Card 3, cost with its reason
    -> {{O(n)}}: one pass, O(1) expected per dict operation
---
Card 4, the pitfall
    930: the bug to avoid?  -> {{seed the map}}: seen = {0: 1}
---
Export: one line per card, a tab between front and back, ready for Anki's text import
    front <TAB> back
```

## Template

```python
def cards_from_entry(entry):
    """entry: dict with problem, cue, technique, invariant, cost, pitfall.
    Returns (front, back) pairs, one fact each. Never the whole solution."""
    p = entry["problem"]
    return [
        (f"{entry['cue']}: which idea?", f"{entry['technique']} ({p})"),
        (f"{entry['technique']}: what stays true at every step?", entry["invariant"]),
        (f"{entry['technique']} on {p}: target cost and why?", entry["cost"]),
        (f"{p}: the bug to avoid?", entry["pitfall"]),
    ]


def to_tsv(cards):
    """Tab-separated front/back lines, which Anki's plain-text importer reads."""
    clean = lambda s: s.replace("\t", " ").replace("\n", " ")
    return "\n".join(f"{clean(f)}\t{clean(b)}" for f, b in cards)


entry = dict(problem="930 Binary Subarrays With Sum",
             cue="count subarrays with an exact sum, zeros allowed",
             technique="prefix sums with a count map",
             invariant="seen[s] = number of earlier prefixes equal to s, before adding the current prefix",
             cost="O(n): one pass, O(1) expected per dict operation",
             pitfall="start with seen = {0: 1} so subarrays that begin at index 0 count")
open("cards.tsv", "w").write(to_tsv(cards_from_entry(entry)) + "\n")
```

## Pitfalls

- **Cards that are too big.** If the answer takes more than one breath, split the card.
- **Ambiguous fronts.** If two different answers are both right, add context to the front ("for non-negative values").
- **Reviewing instead of solving.** Cards support practice; they do not replace re-solves.
- **Keeping bad cards.** A card you keep failing for the same reason is badly written: rewrite or delete it.

## Check yourself

Q: Rewrite the card "Explain the sliding window technique" as two good cards.
A: For example: "Longest stretch with at most k distinct letters: which idea, and what makes it valid?" with the back "Variable window; validity is monotone: shrinking a valid window keeps it valid". And: "Variable window: why is it O(n) although it has a loop inside a loop?" with the back "Each index enters once (right end) and leaves at most once (left end)". Each asks for one checkable fact.

Q: Why is putting the solution code for 1209 on a card a poor investment?
A: Reviewing it trains recognition: you see the code and think "yes, that one", which feels like knowing it. Producing a solution needs the cue, the idea (a stack of runs) and the invariant, each retrieved on its own; cards for those transfer to other problems, a code card transfers to nothing.

Q: In `to_tsv`, why are tabs inside a card replaced by spaces?
A: The importer splits each line on tabs: a tab inside the front or back would create an extra field and shift the text into the wrong place. Newlines are replaced for the same reason, since each line is one card.

## Lab

Solve each problem, then write four cards for it with the template. Expected: no card longer than two short lines, none containing more than one line of code, and at least one cue card and one invariant card per problem.

- **1209 Remove All Adjacent Duplicates in String II.** Expected: `"z"` for `s = "xyyyxxz", k = 3`, and `""` for `"aabbaa", k = 2`.
- **1019 Next Greater Node In Linked List.** Expected: `[4, 4, 5, 5, 0]` for the list 3, 1, 4, 2, 5.
- **16 3Sum Closest.** Expected: 2 for `[-2, 0, 1, 3]` with target 2, and 3 for `[1, 1, 1, 0]` with target 100.

> [!know]
> You now know how to write small single-fact cards and schedule them, so the parts of every solution stay ready between problems.

=== primer | How do you find your weak spots from your tracker? | 12 min
goal: Use your statuses, the Review view and an export of your progress to find the modules and mistake kinds that cost you most, and plan the next two weeks of practice from them
link: USACO Guide: Practicing, "Reading Solutions" | https://usaco.guide/general/practicing#reading-solutions | 5 min: how to read a solution one step at a time and then implement it yourself, which is what a Stuck problem needs before its re-solve
practice: 2966, 1944, 2125

> [!key]
> Your statuses are data. For each module, the share of tried problems you marked Brute only or Stuck shows where your understanding is thin, and the error log shows why. Pick the worst one or two modules, re-read their cards, redo their Stuck problems from a blank file, and add a few fresh bank problems from them to your practice. Measure again in two weeks.

## Intuition

You do not optimise a program by speeding up every line; you profile it and fix the hot spot. Practice time works the same way. Spreading effort evenly over thirty modules feels fair, but most of the gain is in the two or three where you keep getting stuck.

## How it works

### What the page already shows

- Module headers and the rail show solved counts per module; the stage map shows lessons and problems per stage.
- The status filter shows only problems with a chosen status, and the **Review** view lists everything marked Brute only or Stuck.
- The progress menu has **Export all progress as a JSON file**. Problem statuses sit under `trackers["dsa-status"]`, each `{"status": s, "updatedAt": ms}` with 1 Solved, 2 Brute only, 3 Stuck.

### Three numbers per module

For each module count the problems you have **tried** (any status), and from them the **help rate** (Brute only plus Stuck, divided by tried) and the **stuck rate** (Stuck divided by tried).

| Signal | Likely cause | Next two weeks |
|---|---|---|
| High stuck rate in one module | The core idea did not land | Re-read its cards, redo its Stuck problems from a blank file, then three bank problems |
| High help rate in mixed sets, low in module practice | Recognition, not mechanics | Classification sprints, the atlas, look-alike pairs |
| Mostly Brute only | You find a solution but not the optimal one | Target complexity first; the optimisation ladder in the Deriving solutions module |
| One error-log category dominates | A habit | That category's drill on every problem |

## Cost

The export and the analysis take about ten minutes, every two weeks. The script runs in time linear in the number of tracked items, instant even for the full bank of about 900 problems.

## When to use it

Every two weeks, after finishing a stage, and before choosing what to revise for an interview. Do not do it after every problem: with three or four attempts per module, one bad evening looks like a weakness. Require at least three tried problems before you trust a module's rate.

## Worked trace

`weak_spots` on a small export: seven tried problems in two modules.

```steps
Load: statuses from the export, and problem -> module from the page's data
    window: 3 1 , 76 2 , 424 1 , 1004 1     prefix: 560 1 , 930 2 , 523 3
---
Tally the window module: four tried, three Solved, one Brute only
    window  tried {{4}}  solved 3  brute 1  stuck 0
---
Tally the prefix module: three tried, one of each status
    prefix  tried {{3}}  solved 1  brute 1  stuck 1
---
Help rates: (brute + stuck) / tried
    window  1/4 = {{0.25}}      prefix  2/3 = {{0.67}}
---
Both modules reach the three-attempt minimum, so rank by help rate
    0.67 Prefix sums ...   0.25 Sliding window ...
---
Plan: prefix sums first: re-read the count-map card, redo {{523}} (Stuck) from a blank file, add three bank problems
```

## Template

```python
import json
from collections import Counter, defaultdict


def weak_spots(status, module_of, names, min_tried=3):
    """status: problem id -> 0..3 (1 Solved, 2 Brute only, 3 Stuck). module_of: id -> module key.
    Returns (help rate, module, tried, solved, brute only, stuck), worst first."""
    tally = defaultdict(Counter)
    for pid, s in status.items():
        if s and pid in module_of:
            tally[module_of[pid]][s] += 1
    rows = []
    for key, c in tally.items():
        tried = sum(c.values())
        if tried >= min_tried:
            rows.append((round((c[2] + c[3]) / tried, 2), names[key], tried, c[1], c[2], c[3]))
    return sorted(rows, reverse=True)


def load(progress_file_text, page_html_text):
    """progress: the exported JSON file; page: the saved dsa.html, whose data sits in a
    <script id="guide-data"> element."""
    entries = json.loads(progress_file_text)["trackers"]["dsa-status"]
    status = {pid: e["status"] for pid, e in entries.items()}
    start = page_html_text.index('id="guide-data">') + len('id="guide-data">')
    data = json.loads(page_html_text[start:page_html_text.index("</script>", start)])
    module_of, names = {}, {}
    for m in data["modules"]:
        names[m["key"]] = m["name"]
        for row in m.get("practice", []):
            module_of[row[0]] = m["key"]
        for pid in m.get("bank", []):
            module_of[pid] = m["key"]
    return status, module_of, names


# status, module_of, names = load(open("study-progress.json").read(), open("dsa.html").read())
# for row in weak_spots(status, module_of, names): print(row)
```

Card statuses (Done, Needs practice, Revisit) live in the same export under ids that are not problem numbers; `module_of` only maps problems, so cards are ignored here. Read their Needs practice marks separately.

## Pitfalls

- **Small samples.** Two attempts make a rate of 0, 0.5 or 1; wait for at least three.
- **No data is not strength.** A module you never practised has no rate; check the untried ones too.
- **Mixed problems.** All review-set problems belong to this module in the data, so a high rate here means "recognition"; use the Pattern line and your error log to see which techniques they were.
- **Gaming the metric.** Generous Solved marks make the numbers look good and hide exactly the weaknesses you are looking for.

## Check yourself

Q: A module has six tried problems: three Solved, two Brute only, one Stuck. What are its help rate and stuck rate, and is it a weak spot?
A: Help rate (2 + 1) / 6 = 0.5 and stuck rate 1/6, about 0.17. Half the attempts needed help, so it is a candidate; the low stuck rate suggests mostly Brute only results, so work on optimisation (target complexity, the ladder) rather than re-learning the idea.

Q: Your mixed review sets show a help rate of 0.6 while every module's own practice is below 0.2. What is the diagnosis?
A: You can execute each technique when the module tells you which one to use, but you struggle to choose it unlabelled: a recognition weakness. Spend the next two weeks on classification sprints, the atlas and the look-alike pairs rather than on re-reading technique cards.

Q: Your two weakest modules by rate are Advanced dynamic programming (optional) and Sliding window, and an interview is three weeks away. Which comes first, and why?
A: Sliding window: it is essential, appears in a large share of interview problems and is fast to fix with a few re-solves. Advanced DP is optional and rarely asked; plan it after the interview.

## Lab

Solve the three problems, then export your progress and run `weak_spots`. Expected: a list of rows `(help rate, module, tried, solved, brute only, stuck)`, worst first, and a written two-week plan for the top row.

- **2966 Divide Array Into Arrays With Max Difference.** Expected: `[[1, 2, 3], [7, 8, 9]]` for `[1, 2, 3, 7, 8, 9], k = 2`, and `[]` for the same array with `k = 1`.
- **1944 Number of Visible People in a Queue.** Expected: `[2, 1, 2, 1, 0]` for heights `[5, 3, 4, 1, 2]`; O(n).
- **2125 Number of Laser Beams in a Bank.** Expected: 6 for `["101", "000", "011", "010"]`.

> [!know]
> You now know how to turn your statuses and error log into a ranked list of weak spots and a two-week practice plan.

=== lab | Classification sprint: twenty statements in thirty minutes | 45 min
goal: Name the technique, the module and the deciding cue for twenty unlabelled statements under time pressure, then log every miss

Recognition is a skill you can drill without writing code. This sprint uses twenty short statements written for this guide: each is a disguised version of a common problem shape, and several come in look-alike pairs on purpose.

## Steps

1. Set a timer for 30 minutes. For each statement below write four things on paper, without opening any answer: the **technique**, the **module**, the **deciding cue** (the phrase or constraint that decided it) and the **target complexity**.
2. Do all twenty before checking anything. If you are stuck on one for more than two minutes, write your best guess and move on: guessing under time pressure is part of the drill.
3. When the timer ends, open the answers one by one. Score one point for the technique and one for the deciding cue (a different cue that also decides it counts).
4. For every miss, add a line to your error log with the category `technique` and the cue you missed, and add the cue to your atlas or as a card.
5. Repeat the sprint in two weeks with the order reversed, and compare scores and times.

## The twenty statements

Q: 1. A sensor log holds up to 10^5 readings, some of them negative. Count the stretches of consecutive readings that add up to exactly T.
A: Prefix sums with a hash map of counts (Prefix sums and difference arrays). Deciding cue: an exact target with negative values, so a window cannot decide when to shrink; count earlier running totals equal to total - T. O(n).

Q: 2. Given a string of up to 10^5 lowercase letters, find the length of the longest stretch that uses at most three distinct letters.
A: Variable sliding window with letter counts (Sliding window). Deciding cue: longest contiguous stretch under a condition that stays true when the stretch shrinks ("at most three distinct"). O(n).

Q: 3. A sorted list of prices and a budget B: find two different items whose prices add up to exactly B, using O(1) extra memory.
A: Two pointers from both ends (Two pointers). Deciding cue: sorted input, a pair with a target, and O(1) extra space, which rules out a hash set. O(n).

Q: 4. Parcels with weights must ship in the given order over d days; each day's load cannot exceed the truck's capacity. Find the smallest capacity that ships everything within d days (n up to 10^5).
A: Binary search on the answer with a greedy feasibility check (Binary search and searching the answer). Deciding cue: "smallest capacity that works", and a larger capacity never hurts, so feasibility is monotone. O(n log(sum of weights)).

Q: 5. For each day in a list of share prices, report how many days you would wait for a strictly higher price (0 if it never comes).
A: Monotonic stack (Monotonic stacks and queues). Deciding cue: "the next strictly higher value to the right" for every element. O(n).

Q: 6. Jobs arrive at a server over time, each with a priority. At every tick the server runs the waiting job with the highest priority. Simulate 10^5 arrivals.
A: Heap (Heaps and priority queues). Deciding cue: repeatedly take the best item while new items keep arriving. O(n log n).

Q: 7. Given 10^5 exam scores that never change, report the 100th highest score once.
A: Selection: `heapq.nlargest(100, scores)[-1]`, quickselect or a sort (Sorting, partitioning and selection). Deciding cue: one question on fixed data; a heap kept up to date over time is not needed. O(n log k) with nlargest, O(n) on average with quickselect.

Q: 8. Given the start and end times of many meetings, find the smallest number of rooms so that no two overlapping meetings share a room.
A: Sweep line over +1/-1 events, or a min-heap of end times (Intervals and sweep line). Deciding cue: start and end pairs, and the answer is the peak overlap. O(n log n).

Q: 9. A family tree lists each person's wealth. Find the largest total wealth of any person together with all of their descendants.
A: Tree recursion returning subtree sums up (Binary trees and tree recursion). Deciding cue: each answer combines a node with the answers of its children. O(n).

Q: 10. Store 10^5 file paths, then answer many queries of the form "how many stored paths begin with this prefix?".
A: Trie with a count at each node (Tries). Deciding cue: many prefix queries over a large shared vocabulary. O(length) per query. (A sorted list with two bisects also works for static data.)

Q: 11. In a city grid with walls, find the fewest moves from the entrance to any exit; every move takes one minute.
A: Breadth-first search, multi-source from all exits or single-source from the entrance (Graph modelling and traversal). Deciding cue: fewest moves when every move costs the same. O(cells).

Q: 12. Roads between depots have different travel times, all positive. Find the quickest time from the main depot to every shop.
A: Dijkstra with a heap (Weighted shortest paths). Deciding cue: weighted edges with non-negative costs, single source. O((V + E) log V).

Q: 13. Courses have prerequisites. Produce an order in which to take all of them, or report that no order exists.
A: Topological sort with Kahn's algorithm or DFS (Graph modelling and traversal). Deciding cue: dependency order, and "no order" means a cycle. O(V + E).

Q: 14. Friendship links are added one at a time. After each addition, report how many separate friend groups exist.
A: Union-find with a component counter (Union-find and minimum spanning trees). Deciding cue: links only added, and only group membership is asked; each successful union lowers the count by one. Near O(1) per link.

Q: 15. From at most 12 distinct numbers, list every selection whose sum is exactly T.
A: Backtracking with pruning (Complete search and backtracking). Deciding cue: "list every" and a tiny n; the output itself can be exponential. O(2^n · n) in the worst case.

Q: 16. Given up to 100 positive numbers, each at most 100, count the selections whose sum is exactly T (T up to 10^4), modulo 10^9 + 7.
A: 0/1 knapsack counting DP (DP on grids, strings and knapsacks). Deciding cue: only a count is asked, with a small target sum, so states (items used, sum) repeat; loop the sums downwards so each number is used once. O(n · T).

Q: 17. Daily prices: make as many buy-then-sell trades as you like, but after selling you must wait one day before buying again. Maximise the profit.
A: State-machine DP with states holding, just sold and resting (Dynamic programming: from recursion to tables). Deciding cue: a mode that changes what you may do next (the cooldown). O(n), O(1) space.

Q: 18. Children each need a biscuit of at least their own appetite size; each biscuit goes to at most one child. Maximise the number of satisfied children.
A: Greedy after sorting both lists, matching the smallest adequate biscuit to each child in order (Greedy algorithms and exchange arguments). Deciding cue: an exchange argument shows giving the smallest biscuit that fits is never worse. O(n log n).

Q: 19. Build a cache with get and put in O(1) that removes the least recently used key when it is full.
A: Hash map plus a doubly linked list, or OrderedDict with move_to_end (Designing data structures). Deciding cue: "implement a class" with O(1) for several operations at once, including an order-based eviction.

Q: 20. In a list where every value appears exactly twice except one, find the lone value using O(1) extra memory.
A: XOR of all values (Bits and number theory). Deciding cue: pairs cancel and O(1) memory rules out a set; x ^ x = 0 and x ^ 0 = x. O(n).

## What you should see

- A first attempt usually takes 25 to 35 minutes; under 20 means you are ready for the review sets at full speed, over 35 means more atlas work first.
- Most misses come from the look-alike pairs placed on purpose: 1 and 2 (prefix sums or window), 6 and 7 (heap or selection), 11 and 12 (BFS or Dijkstra), 15 and 16 (backtracking or DP), 17 and 18 (DP or greedy). If you missed one side of a pair, re-read its row in the look-alike card.
- The error log gains one `technique` line per miss, each naming the cue you overlooked. On the repeat sprint two weeks later the score should rise and the time fall; if a pair is still missed, make a card for its deciding question.

=== practice
- 219 mixed
  cue: Report whether some value repeats with its two positions at most k apart
  hint: When you meet a value, which earlier occurrence of it is the only one worth comparing with?
  insight: Only the most recent previous index of each value matters, because it is the closest. Keep a dict from value to last index and check i - last[x] <= k before updating it; or keep a set of the last k values and remove the one that falls out of range.
  cost: O(n) time, O(min(n, k)) space
  pattern: Hash map of last positions, or a set over the last k values (Hash tables, sets and counting)
  after: prefix
- 1679 mixed
  cue: Remove as many disjoint pairs whose sum is exactly k as possible
  hint: For a value x only one partner value works. How many pairs can x and its partner form together?
  insight: Different value classes never compete: x can only pair with k - x. With a Counter add min(count[x], count[k - x]) for x < k - x, and count[x] // 2 when 2x = k. Sorting and moving two pointers inwards also works: if the sum is too big, the largest value has no partner left.
  cost: O(n) time with a Counter, O(n log n) with sorting
  pattern: Counting complements (Hash tables, sets and counting), or sort and two pointers (Two pointers)
  after: prefix
- 930 mixed
  cue: Count the subarrays of a 0/1 array whose sum is exactly goal
  hint: A subarray's sum is the difference of two running totals. For the current total, which earlier totals complete a subarray with the right sum?
  insight: Keep a Counter of running totals seen so far, seeded with {0: 1}; at each index add count[total - goal], then record the total. Because the values are 0 or 1, atMost(goal) - atMost(goal - 1) with a shrinking window also works.
  cost: O(n) time, O(n) space (O(1) extra with the window version)
  pattern: Prefix sums with a count map (Prefix sums and difference arrays)
  after: prefix
- 438 mixed
  cue: Find every start position where a stretch of s is a rearrangement of p
  hint: Every match has exactly len(p) letters. What changes when the stretch moves one place to the right?
  insight: Slide a window of length len(p) over s with 26 letter counts: add the entering letter, remove the leaving one, and record the start whenever the counts equal those of p. Tracking how many of the 26 counts currently match makes each step O(1).
  cost: O(n) time, O(1) extra space (26 counts)
  pattern: Fixed-size sliding window with letter counts (Sliding window)
  after: prefix
- 189 mixed
  cue: Shift every element k places to the right, wrapping around, in place
  hint: After the shift the array is two blocks that have swapped places. Which simple in-place operation on a range reverses the order of things?
  insight: Set k %= n, reverse the whole array, then reverse the first k elements and the remaining n - k. The full reversal puts the two blocks in the right places but each one backwards; the two partial reversals fix their insides.
  cost: O(n) time, O(1) extra space
  pattern: In-place reversals (Arrays, dynamic arrays, strings and grids)
  after: prefix
- 1657 mixed
  cue: Decide whether two words can be made equal by swapping letters and by exchanging the roles of two letters everywhere
  hint: List what the two operations can never change about a word.
  insight: Swaps keep the multiset of letters; exchanging two letters swaps their counts. So the words are close exactly when they use the same set of letters and their sorted lists of letter counts are equal (a letter missing from one word can never appear, since exchanges only use existing letters).
  cost: O(n) time, O(1) extra space (26 counts)
  pattern: Comparing invariants with counts (Hash tables, sets and counting)
  after: prefix
- 1004 mixed
  cue: Longest run of 1s if you may flip at most k zeros
  hint: Restate it without flipping: which stretches of the array are acceptable as they are?
  insight: A stretch with at most k zeros can be turned into all 1s, so find the longest such stretch. Grow the right end, count zeros, and advance the left end while the count exceeds k; a stretch with too many zeros stays bad as it grows, so the left end never moves back.
  cost: O(n) time, O(1) space
  pattern: Variable sliding window (Sliding window)
  after: prefix
- 523 mixed
  cue: Is there a stretch of at least two numbers whose sum is a multiple of k?
  hint: When do two running totals differ by a multiple of k?
  insight: Two running totals with the same remainder mod k enclose a multiple of k. Store the first index of each remainder, seeding remainder 0 at index -1, and report success when a remainder reappears at least two positions later; keeping only the first index makes each candidate stretch as long as possible.
  cost: O(n) time, O(min(n, k)) space
  pattern: Prefix sums modulo k with a first-index map (Prefix sums and difference arrays)
  after: prefix
- 16 mixed
  cue: Choose three numbers whose sum is as close as possible to a target
  hint: Put the numbers in order first. With one number fixed, if the other two add up to too much, which of them should change?
  insight: Sort, fix i, and move lo and hi inwards: a sum above the target can only get closer by lowering hi, one below it by raising lo. Track the closest sum seen; an exact match can return at once.
  cost: O(n^2) time, O(1) extra space beyond sorting
  pattern: Sort, fix one, two pointers (Two pointers)
  after: prefix
- 2125 mixed
  cue: Count connections between devices on different rows when every row between them is empty
  hint: Do the empty rows matter at all? Which pairs of rows actually connect?
  insight: Drop the empty rows; each remaining row connects only with the next non-empty one, and every pair of devices across them is one beam. Sum count[r] * count[next] over consecutive non-empty rows.
  cost: O(mn) time, O(1) space
  pattern: Row aggregation on a grid (Arrays, dynamic arrays, strings and grids)
  after: prefix
- 946 mixed
  cue: Given a push order and a pop order of distinct values, could one stack have produced both?
  hint: Replay the operations. After each push, when is a pop forced, and why is it never wrong to pop as early as possible?
  insight: Simulate: push each value, then pop while the top equals the next value of the pop order. Popping early is safe because a top value that is due next can never be popped later once something is pushed over it. Valid exactly when the stack ends empty.
  cost: O(n) time, O(n) space
  pattern: Stack simulation (Linked lists, stacks and queues)
  after: mono
- 240 mixed
  cue: Search a matrix whose rows and columns are each sorted ascending, where rows do not continue one another
  hint: Find a corner where one comparison with the target rules out a whole row or a whole column.
  insight: Start at the top-right corner. If the value is larger than the target, everything below it in that column is larger too, so move left; if smaller, everything to its left in that row is smaller, so move down. Each step discards a row or a column: at most m + n steps.
  cost: O(m + n) time, O(1) space
  pattern: Staircase search on a sorted matrix (Binary search and searching the answer)
  after: mono
- 1944 mixed
  cue: For each person in a line, count the people to their right they can see over everyone in between
  hint: If a taller person stands closer, who behind them disappears from view for everyone further left?
  insight: Scan from the right keeping a stack of heights still visible, decreasing from bottom to top. For person i, pop every shorter height (each is visible to i and hidden by i from everyone further left) and count it; if the stack is still non-empty the next taller person is visible too, so add one. Then push i.
  cost: O(n) time, O(n) space
  pattern: Monotonic stack (Monotonic stacks and queues)
  after: mono
- 328 mixed
  cue: Reorder a linked list so the nodes in odd positions come first, then the even ones, in place
  hint: Walk once and grow two separate chains. What must you remember in order to join them at the end?
  insight: Keep the odd tail, the even tail and the even head; repeatedly set odd.next = even.next and even.next = odd.next, advancing both, until even or even.next is None. Then attach the even head after the odd tail.
  cost: O(n) time, O(1) space
  pattern: Pointer rewiring on a linked list (Linked lists, stacks and queues)
  after: mono
- 2300 mixed
  cue: For each spell, count the potions whose product with it reaches a success threshold
  hint: For one spell, which potions work? If the potions were in order, what shape would that group have?
  insight: Sort the potions once. For spell s the working potions are exactly those >= ceil(success / s), a suffix of the sorted list, so the count is m - bisect_left(potions, (success + s - 1) // s).
  cost: O((n + m) log m) time, O(m) for the sorted copy
  pattern: Sort once, then binary search per query (Binary search and searching the answer)
  after: mono
- 1019 mixed
  cue: For every node of a linked list, the value of the first later node that is strictly larger
  hint: Copy the values into a list. Which earlier nodes are still waiting for their answer, and how are their values ordered?
  insight: Walk the list keeping a stack of indices whose answer is unknown; their values decrease from bottom to top. A new value pops and answers every smaller value on top, then waits itself. Indices left on the stack keep the answer 0.
  cost: O(n) time, O(n) space
  pattern: Monotonic stack for the next greater value (Monotonic stacks and queues)
  after: mono
- 1248 mixed
  cue: Count the subarrays that contain exactly k odd numbers
  hint: Only parity matters. Replace each number by 1 if it is odd and 0 if even: what are you counting now?
  insight: It becomes "count subarrays with sum exactly k" on a 0/1 array: a Counter of running totals seeded with {0: 1}, adding count[total - k] at each step; or atMost(k) - atMost(k - 1) with a window.
  cost: O(n) time, O(n) space (O(1) with the window version)
  pattern: Prefix sums with a count map after mapping to parity (Prefix sums and difference arrays)
  after: mono
- 1283 mixed
  cue: Smallest divisor such that the sum of the rounded-up quotients stays within a threshold
  hint: As the divisor grows, what happens to the sum? What does that let you do with the whole range of divisors?
  insight: The sum never increases as the divisor grows, so "sum <= threshold" is False...False True...True over d in [1, max(nums)]. Find the first True with the check sum((x + d - 1) // d) <= threshold, which costs O(n) per probe.
  cost: O(n log max(nums)) time, O(1) space
  pattern: Binary search on the answer (Binary search and searching the answer)
  after: mono
- 2966 mixed
  cue: Split the numbers into groups of three where every group spans at most k
  hint: Which numbers should share a group? Would putting far-apart values together ever help?
  insight: Sort and cut into consecutive triples. If some consecutive triple spans more than k, no grouping works: any valid grouping can be rearranged into consecutive triples without increasing any group's span (an exchange argument from the smallest element upwards).
  cost: O(n log n) time, O(n) for the output
  pattern: Sort, then group neighbours (Sorting, partitioning and selection)
  after: mono
- 1209 mixed
  cue: Repeatedly delete k equal adjacent letters until no such block remains
  hint: A deletion can make the letters on either side meet. What do you need to remember about what you have kept so far?
  insight: Keep a stack of [letter, run length] for the output so far. A letter equal to the top's letter increments its count, and the pair is popped when the count reaches k, which exposes the previous run exactly as a cascade needs; otherwise push [letter, 1]. Join the runs at the end.
  cost: O(n) time, O(n) space
  pattern: Stack of runs (Linked lists, stacks and queues)
  after: mono
- 572 mixed
  cue: Does one tree appear inside another as some node together with all its descendants?
  hint: Split it into two questions: where could the copy start, and how do you check that two trees are identical?
  insight: For every node of the large tree, run an "identical trees" check against the small one (both recursive). That is O(mn) in the worst case; serialising both trees with markers for missing children and searching for one string inside the other (KMP) makes it O(m + n).
  cost: O(m·n) time simply, O(m + n) with serialisation; O(height) recursion space
  pattern: Tree recursion with an equality check (Binary trees and tree recursion)
  after: trie
- 692 mixed
  cue: The k most frequent words, highest count first, ties in alphabetical order
  hint: Can you express the whole ranking rule as one sort key?
  insight: Count with a Counter, then rank by the key (-count, word). sorted(...)[:k] costs O(u log u) for u distinct words; heapq.nsmallest(k, counts, key=lambda w: (-counts[w], w)) costs O(u log k), the follow-up's target.
  cost: O(n + u log k) time, O(u) space
  pattern: Counting plus a size-k heap with a composite key (Heaps and priority queues)
  after: trie
- 1288 mixed
  cue: Count the intervals that are not contained in another interval
  hint: In which order should you visit the intervals so that any interval that covers another is seen before it?
  insight: Sort by start ascending and end descending; then an interval is covered exactly when its end is at most the largest end seen so far. Count the intervals that raise that maximum.
  cost: O(n log n) time, O(1) extra space
  pattern: Sort, then sweep (Intervals and sweep line)
  after: trie
- 103 mixed
  cue: List the tree's values level by level, alternating left to right and right to left
  hint: Visit the tree one level at a time. What changes between consecutive levels, and what does not?
  insight: Plain level-order traversal with a queue, one level per loop iteration; reverse every second level's list (or fill it with appendleft on a deque). The direction never changes which nodes form a level, only the order you report them in.
  cost: O(n) time, O(width) space
  pattern: Breadth-first traversal by levels (Binary trees and tree recursion)
  after: trie
- 1029 mixed
  cue: Send exactly half of 2n people to each of two cities at minimum total cost
  hint: Suppose everyone starts in city B. What does moving one person to city A cost or save?
  insight: Starting with everyone in B, moving person i to A changes the total by a_i - b_i. Choose the n people with the smallest a_i - b_i: sort by that difference and send the first half to A. Any other choice trades a smaller difference for a larger one.
  cost: O(n log n) time, O(1) extra space
  pattern: Greedy by cost difference after sorting (Greedy algorithms and exchange arguments)
  after: trie
- 1233 mixed
  cue: Remove every folder path that lies inside another listed folder
  hint: When is "/a/b" inside "/a", and why is "/ab" not? In sorted order, where does a sub-folder sit relative to its parent?
  insight: Every sub-folder of p starts with p + "/", and since "/" sorts before every letter, all of them come right after p in sorted order. So sort, and keep a path unless it starts with the last kept path + "/". A trie of path components that stops at nodes ending a folder works too.
  cost: O(nL log n) time to sort n paths of length L, O(nL) space
  pattern: Prefix structure: sorted prefix checks or a trie of path parts (Tries)
  after: trie
- 1382 mixed
  cue: Rebuild a binary search tree so that it is height-balanced, with the same values
  hint: Which traversal lists the values in sorted order? Which value of a sorted list should become the root?
  insight: In-order traversal yields the sorted values; build recursively with the middle element as the root and the two halves as its subtrees. At every node the halves differ in size by at most one, so the tree is balanced.
  cost: O(n) time, O(n) space
  pattern: In-order to a sorted list, then build from the middle (Binary search trees and ordered maps)
  after: trie
- 1353 mixed
  cue: Attend as many events as possible, at most one per day, each on some day inside its range
  hint: Go day by day. Among the events you could attend today, which one is the most urgent?
  insight: Sort by start; sweep the days, pushing the end day of every event that starts today onto a min-heap, discarding ends already past, and attending the event with the earliest end. Taking the soonest-ending event is safe: any schedule that uses a later-ending one today can swap them.
  cost: O((n + D) log n) time for D days, O(n) space
  pattern: Sweep the days with a min-heap of end days (Heaps and priority queues)
  after: trie
- 695 mixed
  cue: Size of the largest group of land cells connected up, down, left or right
  hint: Start from an unvisited land cell and walk to everything connected to it. Can the walk report how many cells it covered?
  insight: Flood fill (iterative DFS or BFS) from each unvisited land cell, marking cells visited and counting them; the answer is the largest count. Every cell is visited once.
  cost: O(mn) time and space
  pattern: Flood fill on a grid graph (Graph modelling and traversal)
  after: paths
- 2316 mixed
  cue: Count the pairs of nodes that have no path between them
  hint: Two nodes are unreachable from each other exactly when they lie in different groups. If you knew the group sizes, how would you count the pairs?
  insight: Find the connected components (union-find or DFS) and their sizes; pairs across components are the unreachable ones. Add size * (nodes counted so far) per component, or compute (n^2 - sum of size^2) / 2.
  cost: O(n + E α(n)) time, O(n) space
  pattern: Connected components with union-find or DFS (Union-find and minimum spanning trees)
  after: paths
- 1466 mixed
  cue: Re-orient the fewest one-way roads of a tree so that every city can reach city 0
  hint: Walk outwards from city 0 ignoring direction. Which roads point the wrong way?
  insight: Store each road both ways, marking the original direction with cost 1 and the reverse with cost 0; traverse from 0 and add the cost of every edge you use. An original road pointing away from 0 must be flipped, one pointing towards 0 is fine, and in a tree each road is used exactly once.
  cost: O(n) time and space
  pattern: Traversal with edge directions as weights (Graph modelling and traversal)
  after: paths
- 851 mixed
  cue: For each person, the quietest person among those known to be at least as rich
  hint: The richer-than relation never loops. If you knew the answer for everyone directly richer than x, could you build x's answer?
  insight: Direct edges from richer to poorer: the graph is acyclic. answer[x] is the quietest of x and answer[y] over everyone y directly richer than x; compute it with a memoised DFS over the richer lists, or push answers along a topological order from the richest.
  cost: O(n + E) time and space
  pattern: DP over a DAG in topological order (Graph modelling and traversal)
  after: paths
- 542 mixed
  cue: Distance from every cell to the nearest 0 cell
  hint: One search per cell is far too slow. Could all the zeros start searching at the same moment?
  insight: Multi-source BFS: put every 0 in the queue at distance 0 and expand outwards; the first time a cell is reached gives its distance, because BFS reaches cells in order of distance from the whole set of sources.
  cost: O(mn) time and space
  pattern: Multi-source BFS (Graph modelling and traversal)
  after: paths
- 1786 mixed
  cue: Count paths from 1 to n along which the shortest distance to n strictly decreases at every step
  hint: Work out the distances to n first. Once you have them, what kind of graph do the allowed moves form?
  insight: Dijkstra from n gives dist; an allowed move goes from u to a neighbour v with dist[v] < dist[u], so moves can never cycle. Count paths with DP in increasing order of dist: ways[n] = 1 and ways[u] is the sum of ways[v] over allowed neighbours, modulo 10^9 + 7.
  cost: O(E log V) time, O(V + E) space
  pattern: Dijkstra, then DP in distance order (Weighted shortest paths)
  after: paths
- 909 mixed
  cue: Fewest dice rolls to finish a snakes and ladders board
  hint: Every roll costs the same. What are the states, and what are the up to six moves from each?
  insight: BFS over squares 1..n^2: from square s try s + 1 to s + 6, follow a snake or ladder if one starts there (once only), and record the roll count when a square is first reached. The fiddly part is converting a square number to (row, col), with rows numbered from the bottom and alternating direction.
  cost: O(n^2) time and space
  pattern: BFS on an implicit graph (Graph modelling and traversal)
  after: paths
- 2492 mixed
  cue: Smallest possible weight of the lightest road on any route from 1 to n, where roads may be reused
  hint: Since a route may go back and forth, which roads can a route from 1 to n touch?
  insight: Because revisits are allowed, a route can detour through any road of the component that contains city 1 (and n lies in it). The answer is the smallest weight among those roads: find the component with union-find or BFS from 1 and take the minimum weight over its edges.
  cost: O(n + E α(n)) time, O(n) space
  pattern: Connected component plus a minimum over its edges (Union-find and minimum spanning trees)
  after: paths
- 1882 mixed
  cue: Assign queued tasks to free servers by weight and then index, waiting whenever none is free
  hint: You keep needing two different "best" servers: the best free one, and the one that becomes free soonest.
  insight: Keep a min-heap of free servers keyed (weight, index) and a min-heap of busy servers keyed (free time, weight, index). For task j at time t = max(t, j), release every busy server free by t; if none is free, jump t to the earliest free time and release those. Pop the best free server and push it as busy until t + tasks[j].
  cost: O((n + m) log n) time, O(n) space
  pattern: Two heaps for an event simulation (Heaps and priority queues)
  after: paths
- 2092 mixed
  cue: A secret spreads through meetings, and people meeting at the same instant pass it on instantly
  hint: Group the meetings by time. Within one time, who ends up knowing? What should happen to people who met but did not learn it?
  insight: Process the times in increasing order. For one time, union the people who meet; afterwards everyone connected to person 0's set knows the secret, and everyone else from those meetings is reset to a singleton so later meetings do not inherit a false link. A BFS inside each time slot works the same way.
  cost: O(M log M + M α(n)) time, O(n + M) space
  pattern: Union-find with a reset per time slot (Union-find and minimum spanning trees)
  after: paths
- 279 mixed
  cue: Fewest perfect squares that add up to n
  hint: Suppose you knew the last square used. What problem is left, and how many different leftovers can there be?
  insight: best[0] = 0 and best[i] = 1 + min(best[i - s*s]) over squares s*s <= i: coin change with square coins, n amounts each trying about sqrt(n) coins. (Number theory says the answer is never more than four, which allows faster special-case solutions.)
  cost: O(n sqrt n) time, O(n) space
  pattern: Unbounded coin-change DP (Dynamic programming: from recursion to tables)
  after: greedy
- 40 mixed
  cue: List every combination that sums to the target, each element used at most once, from input with duplicates, with no repeated combinations
  hint: Two equal numbers can produce the same combination twice. At one level of the choices, when is picking a value pointless?
  insight: Sort, then recurse choosing the next element from index start onwards; skip a value equal to the previous one at the same depth (i > start and a[i] == a[i - 1]), and stop the loop once a[i] exceeds the remaining target, since the rest are larger. Recurse with i + 1 because each element is used once.
  cost: Exponential in the worst case (output size times n); the small target keeps it fast
  pattern: Backtracking with sort-and-skip deduplication (Complete search and backtracking)
  after: greedy
- 1035 mixed
  cue: Draw the most non-crossing lines joining equal numbers in two rows
  hint: Two lines do not cross exactly when their endpoints come in the same order in both rows. What are you choosing from each row, then?
  insight: A set of non-crossing lines is a common subsequence of the two arrays and vice versa, so the answer is their longest common subsequence: dp[i][j] = dp[i-1][j-1] + 1 on a match, else max(dp[i-1][j], dp[i][j-1]).
  cost: O(mn) time, O(min(m, n)) space with two rows
  pattern: Longest common subsequence in disguise (DP on grids, strings and knapsacks)
  after: greedy
- 1594 mixed
  cue: Largest non-negative product along a right-and-down path in a grid that contains negative numbers
  hint: A very negative product can become the best one after one more negative cell. What do you need to keep for every cell?
  insight: For every cell keep both the largest and the smallest product of a path reaching it; from the top and left neighbours, multiply both by the cell's value and take the max and the min. The answer is the corner's max modulo 10^9 + 7, or -1 if it is negative; take the modulus only at the end.
  cost: O(mn) time, O(n) space with one row
  pattern: Grid DP with max and min states (DP on grids, strings and knapsacks)
  after: greedy
- 93 mixed
  cue: Every way to split a digit string into a valid IPv4 address
  hint: Exactly four parts, each 1 to 3 digits with value 0 to 255 and no leading zero. How many ways can there possibly be?
  insight: Try each part length 1, 2 or 3 recursively, rejecting parts above 255 or with a leading zero, and prune when the remaining digits cannot fill the remaining parts (fewer than one or more than three per part). There are at most 3^4 = 81 length choices.
  cost: O(1): at most 81 candidate splits, each checked in O(length)
  pattern: Backtracking with pruning (Complete search and backtracking)
  after: greedy
- 2140 mixed
  cue: Answer questions in order; solving one earns points but skips the next brainpower questions
  hint: A decision only affects what comes after it. From which end is it easier to start?
  insight: Solve from the back: dp[i] = max(dp[i + 1], points[i] + dp[i + brainpower[i] + 1]), with dp = 0 past the end. Each question is a take-or-skip choice whose consequences all lie later.
  cost: O(n) time, O(n) space
  pattern: Take-or-skip DP from the back (Dynamic programming: from recursion to tables)
  after: greedy
- 375 mixed
  cue: Least money that guarantees a win at higher-or-lower guessing when a wrong guess x costs x
  hint: You choose the guess; the side is chosen against you. What does the guaranteed cost of a range depend on?
  insight: cost(l, r) = min over guesses g in [l, r] of g + max(cost(l, g - 1), cost(g + 1, r)), with cost 0 on ranges of size 0 or 1. Fill by increasing range length or memoise: a minimax over sub-ranges.
  cost: O(n^3) time, O(n^2) space
  pattern: Interval DP with a minimax step (Advanced dynamic programming; memoised recursion over ranges is enough)
  after: greedy
- 646 mixed
  cue: Longest chain of pairs where each pair starts after the previous one ends
  hint: Which pair should start the chain? Think about which first choice leaves the most room for the rest.
  insight: Sort by end and take each pair whose start is greater than the end of the last pair taken (activity selection). The pair that ends first can replace the first pair of any optimal chain, so taking it is safe. An O(n^2) DP also passes but is not needed.
  cost: O(n log n) time, O(1) extra space
  pattern: Greedy by earliest end (Greedy algorithms and exchange arguments)
  after: greedy
- 712 mixed
  cue: Smallest total of character codes deleted to make two strings equal
  hint: The characters you keep must appear in the same order in both strings. What is the most valuable thing you can keep?
  insight: Minimising the deleted value is maximising the kept value: dp[i][j] = dp[i-1][j-1] + ord(c) on a match, else the larger of dropping one character from either side. The answer is the codes of both strings minus twice the best kept value (or fill deletion costs directly with min).
  cost: O(mn) time, O(n) space with two rows
  pattern: Weighted longest common subsequence (DP on grids, strings and knapsacks)
  after: greedy
- 1653 mixed
  cue: Fewest deletions so that no 'b' appears before an 'a'
  hint: When you reach an 'a', there are two ways to make the prefix acceptable. What does each cost?
  insight: Scan with b_count, the number of b's so far, and best, the answer for the prefix. On 'b', b_count += 1; on 'a', either delete this 'a' (best + 1) or delete every 'b' so far (b_count): best = min(best + 1, b_count). Equivalently, try every split point: b's before it plus a's after it.
  cost: O(n) time, O(1) space
  pattern: One-pass DP over prefixes (Dynamic programming: from recursion to tables)
  after: greedy
- 1140 mixed
  cue: Players take all the stones in the first X piles, 1 <= X <= 2M, after which M becomes max(M, X); maximise the first player's total
  hint: Whatever has happened, the rest of the game depends only on where the remaining piles start and on M. The total of the remaining piles is fixed.
  insight: Let f(i, M) be the most the player to move can collect from piles i onwards. Then f(i, M) = suffix[i] - min over x in 1..2M of f(i + x, max(M, x)), and f(i, M) = suffix[i] when i + 2M >= n. Memoise over (i, M).
  cost: O(n^3) time, O(n^2) space
  pattern: Game DP over (position, M) (Advanced dynamic programming; memoisation is enough)
  after: greedy
- 688 mixed
  cue: Probability that a knight is still on an n x n board after k uniformly random moves
  hint: Instead of following single paths, spread probability over the board one move at a time.
  insight: Keep a board of probabilities. For each move, every cell sends one eighth of its probability to each of its eight knight targets that are still on the board (mass that leaves is dropped). After k moves, sum the board.
  cost: O(k n^2) time (8 moves per cell), O(n^2) space
  pattern: Probability DP over steps (DP on grids, strings and knapsacks)
  after: greedy
- 1442 mixed
  cue: Count triples i < j <= k where the XOR of a[i..j-1] equals the XOR of a[j..k]
  hint: If two values are equal, what is their XOR? What does that say about the whole stretch from i to k?
  insight: a == b exactly when a ^ b = 0, that is when the XOR of a[i..k] is 0, which with running XORs means prefix[i] == prefix[k + 1]. Then every j in (i, k] works: k - i choices. Sum over equal-prefix pairs in O(n^2), or in O(n) with dicts holding the count and the index sum per prefix value.
  cost: O(n) time with dicts (O(n^2) is plenty for n <= 300), O(n) space
  pattern: Prefix XOR (Bits and number theory, with prefix sums)
  after: bitmath
- 1823 mixed
  cue: Friends sit in a circle and every k-th one leaves; who remains?
  hint: After the first friend leaves, the game restarts with n - 1 friends from a new position. How are the two answers related?
  insight: Number from 0. The survivor among n is the survivor among n - 1 shifted by k: f(1) = 0, f(n) = (f(n - 1) + k) % n, and the answer is f(n) + 1. Simulating with a list and pop((i + k - 1) % len) is O(n^2), also fine for n <= 500.
  cost: O(n) time, O(1) space
  pattern: Josephus recurrence (Bits and number theory; recursion)
  after: bitmath
- 1352 mixed
  cue: A stream of numbers with queries for the product of the last k
  hint: Running products let you divide out the part you do not want. What does a zero do to that idea?
  insight: Keep a list P of running products since the last zero, starting [1]. On add(0) reset P to [1]; otherwise append P[-1] * x. A query k returns 0 if k >= len(P) (a zero lies among the last k) and P[-1] // P[-1 - k] otherwise.
  cost: O(1) per operation, O(n) space
  pattern: Prefix products with a reset at zero (Designing data structures, with prefix sums)
  after: bitmath
- 2101 mixed
  cue: Set off one bomb; every exploding bomb sets off all bombs within its own radius; maximise the total
  hint: Does "a reaches b" imply "b reaches a"? What structure does that suggest?
  insight: Build a directed graph with an edge i -> j when (xi - xj)^2 + (yi - yj)^2 <= ri^2 (integers, no square roots), then run BFS or DFS from every bomb and take the largest reachable set. Union-find is wrong here, because reach is not symmetric.
  cost: O(n^3) time (n searches over up to n^2 edges), O(n^2) space
  pattern: Directed reachability by a search from each source (Graph modelling and traversal)
  after: bitmath
- 382 mixed
  cue: Return a uniformly random value from a linked list, possibly of unknown length
  hint: Can you decide on the fly, as the nodes go past, whether the current node should replace your pick?
  insight: Simplest: copy the values into a list once and use random.choice (O(n) space, O(1) per call). Without extra space, reservoir sampling: keep the i-th node with probability 1/i; node i survives every later step with probability (1/i)·(i/(i+1))···((n-1)/n) = 1/n.
  cost: O(n) per call and O(1) space with the reservoir, or O(1) per call and O(n) space with a list
  pattern: Reservoir sampling over a stream (Bits and number theory: randomness and counting)
  after: bitmath
- 1856 mixed
  cue: Maximise min(subarray) × sum(subarray) over all subarrays
  hint: Fix the element that acts as the minimum. How far can its subarray stretch?
  insight: For each i, the best subarray with a[i] as its minimum spans from just after the previous smaller element to just before the next smaller one (values are positive, so wider is better). Find both bounds with a monotonic stack and get range sums from prefix sums; maximise before taking the modulus.
  cost: O(n) time, O(n) space
  pattern: Monotonic stack bounds plus prefix sums (Monotonic stacks and queues)
  after: bitmath
- 2349 mixed
  cue: Change the number stored at an index; query the smallest index currently holding a given number
  hint: Changes leave old entries behind. Do you have to clean them up straight away?
  insight: Keep index -> number in a dict and number -> min-heap of indices. On change, update the dict and push the index onto the new number's heap. On find, pop from the top while the top index no longer holds that number (lazy deletion), then return the top or -1.
  cost: O(log n) amortised per operation, O(n) space
  pattern: Heap with lazy deletion (Designing data structures)
  after: bitmath
- 2402 mixed
  cue: Meetings take the lowest-numbered free room or wait for the room that frees first, keeping their length; which room hosts the most?
  hint: At each meeting you need either the lowest-numbered free room or the room that becomes free soonest: two different orders.
  insight: Sort the meetings by start. Keep a min-heap of free room numbers and a min-heap of (end time, room) for busy rooms. Before each meeting release the rooms with end <= start; if a room is free take the lowest, else pop the earliest (end, room) and run the meeting from that end for its original length. Count meetings per room.
  cost: O(m log m + m log n) time, O(n) space
  pattern: Two heaps for room allocation (Heaps and priority queues)
  after: bitmath
- 1964 mixed
  cue: For each position, the longest non-decreasing course that ends exactly there
  hint: Keep, for every course length seen so far, the lowest height a course of that length can end with. How does a new obstacle change that list?
  insight: The list of lowest ending heights is non-decreasing, so binary search it: the new obstacle extends the longest course whose ending height is <= it (bisect_right, because equal heights may follow), replaces the entry at that position, and its answer is that position + 1.
  cost: O(n log n) time, O(n) space
  pattern: Patience-style longest non-decreasing subsequence (Dynamic programming: from recursion to tables)
  after: bitmath
- 1146 mixed
  cue: An array with snapshots; read any index as it was at any snapshot
  hint: Copying the array at every snapshot is too expensive. What is the least you could store per index?
  insight: Per index keep a list of (snap_id, value), appended on set (overwrite the last entry if it has the same snap_id). get(i, s) binary-searches that list for the last entry with snap_id <= s; an index never set before s returns 0.
  cost: O(1) set, O(log S) get, O(n + number of sets) space
  pattern: Per-key version history with binary search (Designing data structures)
  after: bitmath
