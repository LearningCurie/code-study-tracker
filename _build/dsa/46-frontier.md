---
key: frontier
name: Frontier: recent results (optional)
stage: frontier
summary: Short, sourced reads on recent algorithmic results and what they did or did not change in real libraries: AlphaDev's sorting kernels, the shortest-path sorting barrier, elastic and funnel hashing, learned indexes, Swiss tables, the new default sorts and RaBitQ.
why: Data structures and algorithms are not finished. Since 2018 a model has replaced index levels in a production database, Rust, Go and CPython have all changed the algorithms behind their standard sort and hash map, a reinforcement-learning agent shortened the sorting kernels in LLVM's C++ library, and theorists broke bounds that had stood for decades: Dijkstra's sorting barrier for directed shortest paths and Yao's conjecture about open addressing. Knowing what these results actually say (the model, the exact bound, the setting of a benchmark) keeps you from both cargo-culting headlines and dismissing real progress, and it tells you which ideas are already in the tools you use every day. Every card is optional and short; read them for perspective after the core modules.
outcomes:
- Explain what AlphaDev changed in libc++ (branchless sort3, sort4 and sort5), how it was measured and why comparisons were not the metric
- State the 2025 and 2026 directed shortest-path bounds exactly, explain the frontier idea, and say why Dijkstra is still what you implement
- State the elastic and funnel hashing bounds, what "greedy" and "without reordering" mean, and why the asymptotic win needs very full tables
- Build an error-bounded piecewise-linear learned index and say where learned indexes have been used for real
- Describe Swiss-table metadata, group matching and probing, and how Go 1.24 adapted the design for incremental growth
- Name the default sorts in Rust, Go and CPython, and implement powersort's merge policy on run lengths
- Explain RaBitQ's random rotation, sign bits and unbiased estimator, and measure its 1/sqrt(D) error
cues:
- A tiny fixed-size sort in a hot loop: sorting networks and branch-free code beat comparison counting
- A hash table that must run nearly full, or whose probe sequences dominate the cost
- Sorted, read-mostly keys with a smooth distribution: a model can stand in for the upper levels of an index
- Vector memory dominating the bill: quantise with an error bound, then rescore the survivors
traps:
- Reading an asymptotic bound as a speed-up: constants and realistic input sizes decide
- Quoting a headline percentage without its setting (input length, data type, CPU, workload)
- Assuming every library's sort is stable, or that a broken comparator is harmless (Rust 1.81 may panic on one)
- Benchmarking a hash map or an index with a single, friendly key distribution
systems:
- LLVM libc++ sort3, sort4 and sort5 are branchless routines derived from AlphaDev's assembly (review D118029, 2022)
- Go 1.24's built-in map is a Swiss table split into tables of at most 1,024 entries; Rust's HashMap has used the SwissTable-based hashbrown since 1.36
- Rust 1.81: slice::sort is driftsort and slice::sort_unstable is ipnsort; Go's sort package has used pdqsort since 1.19
- CPython 3.11's list.sort merges runs with powersort's policy; Faiss 1.11 added a RaBitQ implementation
further:
- Paper · 30 min | Mankowitz et al. 2023, Nature: AlphaDev, sections 'Libc++ sort patch' and 'AlphaDev swap move' | https://www.nature.com/articles/s41586-023-06004-9#Sec16
- Paper · 20 min | Duan et al. 2025: technical overview of the frontier reduction | https://arxiv.org/html/2504.17033v2#S1.SS1.SSS0.Px1
- Article · 15 min | Go blog: Faster Go maps with Swiss Tables | https://go.dev/blog/swisstable#swiss-table
- Notes · 20 min | CPython listsort.txt: runs, the powersort merge pattern and minrun | https://github.com/python/cpython/blob/main/Objects/listsort.txt
---

=== primer | What did AlphaDev change in the C++ standard library's sort, and why did it matter? | 10 min
goal: Explain what AlphaDev discovered, what went into libc++, how it was measured, and what it does not change about sorting
tag: frontier-sortnet | Sorting networks and the 0-1 principle
link: Mankowitz et al. 2023, Nature | https://www.nature.com/articles/s41586-023-06004-9#Sec16 | 'Libc++ sort patch' (one paragraph) for what shipped and the measured gains, then 'AlphaDev swap move' with Table 2 for the one-instruction saving
link: LLVM review D118029 | https://reviews.llvm.org/D118029 | The patch itself: branchless sort3, sort4 and sort5 in libc++'s sort.h, with its benchmarks

> [!key]
> **AlphaDev** (DeepMind; Mankowitz et al., Nature 2023) is a reinforcement-learning agent that writes x86 assembly one instruction at a time and is rewarded for programs that are correct and short or fast. For sorting exactly 3, 4 or 5 numbers it matched or beat human sorting networks (17 instructions against 18 for sort 3, 42 against 46 for sort 5, equal at 28 for sort 4). Reverse-engineered into C++, the routines went into LLVM's libc++, the first change to those sub-routines in over a decade. The paper measured up to 70% faster sorting of length-5 sequences and roughly 1.7% for sequences over 250,000 elements. Big-O did not move: this is a constant factor in the leaves of std::sort.

## Intuition

A large sort spends a surprising share of its time on tiny pieces: the recursion bottoms out on subarrays of a handful of elements, millions of times. For those, the best code has no data-dependent branches (which the CPU mispredicts about half the time on random data) but a fixed sequence of compare-and-swap steps compiled to conditional moves. Shaving one instruction off a routine that runs, by the paper's estimate, trillions of times a day is worth a Nature paper.

## How it works

### Sorting networks

A **sorting network** is a fixed list of comparators (i, j): put the smaller of a[i], a[j] at i and the larger at j. The order never depends on the data, so it compiles to branch-free min/max code. The **0-1 principle** says a comparator network sorts every input if and only if it sorts every input of 0s and 1s, so checking 2^n cases proves it correct. I verified by exhaustive search that 3, 5 and 9 comparators are the minimum for 3, 4 and 5 inputs.

### What AlphaDev searched

The agent played "AssemblyGame": add one instruction (mov, cmp, cmovX and so on) per move, scored on correctness over test inputs and on program length or measured latency. For fixed sizes the benchmarks were sorting networks; for variable sizes (sort up to 3, 4 or 5 elements), AlphaDev found much shorter routines than the human ones (VarSort4: 37 instructions against 66).

### The swap move

The optimal 3-input network applies (B, C), then (A, C), then (A, B). After the first comparator B <= C is guaranteed, so the first output min(A, B, C) equals min(A, B), and computing the shorter expression saves one instruction. The "copy move" is similar: if D >= min(A, C), then max(B, min(A, C, D)) = max(B, min(A, C)).

### What shipped

LLVM review D118029 ("Introduce branchless sorting functions for sort3, sort4 and sort5") added the routines to libc++. The paper credits the gains to both the branch-free code and the swap move, and notes that for sort 5 a 43-instruction AlphaDev variant gave better C++ than the 42-instruction one.

## Cost

The networks use 3, 5 and 9 comparators for 3, 4 and 5 inputs, always. Python's `sorted` on 5 items uses fewer comparisons on average (7.78 over all 120 orderings, counted with `functools.cmp_to_key`) but branches on every one. That is the lesson: for tiny sorts the cost model is instructions and mispredicted branches, not comparisons. The 1.7% for large arrays is small per call, but it applies to every program built against libc++ that sorts.

## When to use it

- Sorting a few values in a hot inner loop (median of three or five, the leaves of a quicksort, small fixed records): use a sorting network with branch-free min/max.
- SIMD and GPU sorting kernels, where all lanes must run the same instruction stream.
- Not in Python: interpreter overhead swamps instruction-level savings; call `sorted`.
- The broader idea, machine search over small programs whose correctness can be checked exhaustively and whose speed can be measured, works best on short kernels like these.

## Worked trace

```steps
The 3-input network on [3, 1, 2]: comparator (1, 2) first
    index   0   1   2
    a       3  {{1}} {{2}}     already ordered: no swap
---
Comparator (0, 2): 3 > 2, so swap
    a      {{2}}  1  {{3}}
---
Comparator (0, 1): 2 > 1, so swap; sorted after exactly 3 comparators
    a      {{1}} {{2}}  3
---
Swap move: after (1, 2), B <= C holds, so the first output min(A, B, C) can be computed as min(A, B)
    A = 3, B = 1, C = 2     min(A, B, C) = 1 = min(A, B)
```

## Template

```python
import itertools

NETWORKS = {
    3: [(1, 2), (0, 2), (0, 1)],
    4: [(0, 1), (2, 3), (0, 2), (1, 3), (1, 2)],
    5: [(0, 1), (3, 4), (2, 4), (2, 3), (0, 3), (0, 2), (1, 4), (1, 3), (1, 2)],
}


def apply(network, values):
    """Run a comparator network: each (i, j) with i < j puts the smaller value at i."""
    a = list(values)
    for i, j in network:
        a[i], a[j] = min(a[i], a[j]), max(a[i], a[j])
    return a


def sorts_everything(n, network):
    """0-1 principle: a comparator network sorts every input iff it sorts all 2**n 0/1 inputs."""
    return all(apply(network, bits) == sorted(bits)
               for bits in itertools.product((0, 1), repeat=n))
```

Each network also sorted 2,000 random integer lists; dropping the last comparator of the 4-input network is caught by `sorts_everything`.

## Pitfalls

- **Comparisons are not the metric.** The networks compare more than an adaptive sort; they win on predictable, branch-free instructions.
- **The 0-1 principle is for comparator networks only.** It does not prove arbitrary sorting code correct.
- **Headlines need their setting.** "Up to 70%" is for length-5 sequences; uint32, uint64 and float on ARMv8, Skylake and Zen 2 CPUs; about 1.7% for long arrays.
- **Preconditions matter.** The swap move is only valid after the (B, C) comparator: with A = 3, B = 2, C = 1, min(A, B, C) = 1 but min(A, B) = 2.

## Check yourself

Q: Run the 3-input network on [2, 3, 1]. What is the array after each comparator?
A: (1, 2): 3 > 1, swap, giving [2, 1, 3]. (0, 2): 2 < 3, no swap. (0, 1): 2 > 1, swap, giving [1, 2, 3].

Q: Why did AlphaDev measure instructions and latency instead of comparisons?
A: Small sorts are compiled to branch-free sequences of compare and conditional-move instructions, so time depends on the number and dependency of instructions, not on how many comparisons a decision tree would need. A routine with more comparisons but no branches can beat one with fewer comparisons and unpredictable branches.

Q: Big-O of std::sort did not change. Why was a 1.7% gain on large arrays still worth shipping?
A: Every large sort ends in many tiny sorts, so a constant-factor gain there applies to every call of a function used across a vast amount of software; the paper estimates these routines run trillions of times a day.

## Lab

- Check all three networks with `sorts_everything`, then delete the last comparator of the 4-input network. Expected: True, True, True, then False.
- Count the comparisons `sorted` makes on each of the 120 orderings of range(5), using `functools.cmp_to_key` with a counter. Expected: 7.78 on average (3.17 for the 6 orderings of 3 items), against a constant 9 (and 3) for the networks.
- Test the swap move over all A, B, C in range(4): with B <= C, min(A, B, C) == min(A, B) every time; without the condition, find a counterexample. Expected: none with the condition; A = 3, B = 2, C = 1 without it.

> [!know]
> You now know what AlphaDev's sorting result changed (branch-free 3 to 5 element kernels in libc++), how to verify a sorting network, and why instructions, not comparisons, were the measure.

=== primer | Has Dijkstra's algorithm been beaten? The sorting barrier for shortest paths | 12 min
goal: State what Duan et al. (2025) and the 2026 follow-up proved, explain the frontier-reduction idea, and explain why Dijkstra is still what you should write
link: Duan, Mao, Mao, Shu and Yin 2025, technical overview | https://arxiv.org/html/2504.17033v2#S1.SS1.SSS0.Px1 | Two pages: the frontier, why it forces sorting, and how k Bellman-Ford steps plus 'pivots' shrink it
link: Castro, Clementino and de Freitas 2025 | https://arxiv.org/abs/2511.03007 | The abstract: an implementation tested on graphs of up to 10 million vertices, where Dijkstra stayed 3 to 4 times faster

> [!key]
> For directed graphs with real non-negative weights, in the **comparison-addition model** (weights may only be compared and added), Dijkstra's algorithm with a Fibonacci heap takes O(m + n log n). In 2025 Duan, Mao, Mao, Shu and Yin gave a deterministic **O(m log^(2/3) n)** algorithm, the first to beat that bound on sparse directed graphs; in 2026 Duan, Mao, Shu and Yin improved it to O(m sqrt(log n) + sqrt(m n log n log log n)), which is O(m sqrt(log n log log n)) on sparse graphs. These algorithms compute distances without listing vertices in distance order, which is what lets them avoid sorting. Dijkstra, which does produce the order, is optimal for that task, and in practice it is still faster.

## Intuition

Dijkstra settles vertices in increasing order of distance, so it sorts them as a side effect. Sorting n items needs about n log n comparisons, so anything that outputs that order pays it. If you only want the distances, maybe you do not need the full order. The new algorithms exploit exactly that gap.

## How it works

### Why Dijkstra sorts

Give a source an edge to each of n vertices with weight equal to a key. Dijkstra pops vertices in distance order, which is sorted key order: one call sorts n keys. So any algorithm that outputs vertices in distance order needs Ω(n log n) comparisons. Haeupler, Hladík, Rozhoň, Tarjan and Tětek showed that Dijkstra with a suitable heap is **universally optimal** for that distance-order problem: on every graph, no algorithm does better against worst-case weights.

### The frontier

At any moment Dijkstra's heap holds a **frontier** S: every incomplete vertex's shortest path passes through some vertex of S. The frontier can hold Θ(n) vertices (on a star, the heap reached 9,999 entries for 10,000 vertices; on a path it never exceeds 1), and always picking its minimum is where the sorting comes from.

### Shrinking the frontier

Bellman-Ford needs no sorting: k rounds of relaxing every edge make exact every vertex whose shortest path uses at most k edges, in O(km) time. The paper combines the two. To settle all vertices closer than a bound B that depend on S, run k relaxation rounds from S. Vertices whose path needs fewer than k more steps are now complete. Any remaining vertex depends on a frontier vertex whose shortest-path tree has at least k vertices; such **pivots** number at most (vertices involved) / k, so only they stay in the frontier. A divide-and-conquer over about (log n) / t levels, with k = floor(log^(1/3) n) and t = floor(log^(2/3) n), applies this at every level, so the expensive work per vertex falls from Θ(log n) to O(log^(2/3) n). The analysis first transforms the graph to constant degree by replacing each vertex with a zero-weight cycle.

### The bounds, side by side

| Result | Graphs | Time |
|---|---|---|
| Dijkstra + Fibonacci heap | directed or undirected | O(m + n log n) |
| Duan, Mao, Shu, Yin 2023 (randomised) | undirected | O(m sqrt(log n · log log n)) |
| Duan, Mao, Mao, Shu, Yin 2025 (deterministic) | directed | O(m log^(2/3) n) |
| Duan, Mao, Shu, Yin 2026 (deterministic) | directed | O(m sqrt(log n) + sqrt(m n log n log log n)) |

A September 2026 preprint by Kadria and Roditty improves the undirected bound again, by a factor of (log log n / log log log n)^(1/4).

## Cost

Ignore constants and compare the expressions with base-2 logarithms. For n = 10^6: log n is 19.9, log^(2/3) n is 7.35, and sqrt(log n log log n) is 9.28. The 2026 expression only drops below the 2025 one once log2 n exceeds about 982, that is, for n above roughly 2^982. Asymptotic progress and practical speed are different questions. The implementation study by Castro, Clementino and de Freitas found Dijkstra 3 to 4 times faster on sparse random graphs, grids and US road networks of up to 10 million vertices, and estimated that the worst-case version would need far more than 10^67 vertices to win.

## When to use it

| Situation | Use |
|---|---|
| Non-negative weights, one source | Dijkstra with a binary heap (`heapq`) |
| Unit weights | BFS, O(n + m) |
| Negative weights, no negative cycles | Bellman-Ford |
| Many queries on a fixed road network | Preprocessing methods (contraction hierarchies), not covered here |
| Integer weights in the word-RAM model | Different rules: Thorup's algorithms are linear for undirected graphs |

The new results matter because they show the sorting barrier was not a law, and because their tools (bounded Bellman-Ford rounds, pivots, frontier reduction) may lead to practical methods. Today they are research.

## Worked trace

Edges: s -> a (2), s -> b (7), a -> b (3), a -> c (6), b -> c (1). Dijkstra settles s, a, b, c with distances 0, 2, 5, 6. Relaxation rounds reach the same answers without any priority order:

```steps
Round 0: only the source is known
    s 0      a inf    b inf    c inf
---
Round 1: relax every edge once from the old estimates; a is exact (its shortest path has 1 edge)
    s 0      {{a 2}}    b 7      c inf
---
Round 2: b improves through a (2 + 3); b is exact (2 edges); c gets a first estimate
    s 0      a 2      {{b 5}}    c 8
---
Round 3: c improves through b (5 + 1); every vertex is exact, because no shortest path has more than 3 edges
    s 0      a 2      b 5      {{c 6}}
```

## Template

```python
import heapq


def dijkstra(graph, s):
    """graph: {u: [(v, w), ...]}, w >= 0. Returns (dist, order settled)."""
    dist, order, heap = {s: 0}, [], [(0, s)]
    done = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        order.append(u)
        for v, w in graph.get(u, []):
            if d + w < dist.get(v, float("inf")):
                dist[v] = d + w
                heapq.heappush(heap, (d + w, v))
    return dist, order


def relax_rounds(graph, est, k):
    """k rounds of Bellman-Ford from current estimates: afterwards every vertex whose shortest
    path from an exact vertex uses at most k more edges is exact. O(k * m), no sorting."""
    est = dict(est)
    for _ in range(k):
        new = dict(est)
        for u, du in est.items():
            for v, w in graph.get(u, []):
                if du + w < new.get(v, float("inf")):
                    new[v] = du + w
        est = new
    return est


def sort_with_sssp(keys):
    """A star with edge weights = keys: Dijkstra's settle order is the sorted order."""
    graph = {"s": [(i, k) for i, k in enumerate(keys)]}
    _, order = dijkstra(graph, "s")
    return [keys[i] for i in order[1:]]
```

Tested on 300 random graphs against NetworkX: distances match, the settle order is non-decreasing in distance, and after k rounds every vertex with a shortest path of at most k edges is exact. `sort_with_sssp` sorts 1,000 random keys correctly.

## Pitfalls

- **"Dijkstra is obsolete."** No: the new bounds are asymptotic, the constants are large, and Dijkstra is optimal when you need the distance order.
- **Mixing models.** The results are in the comparison-addition model with real weights. Integer-weight results in the word-RAM model are a different line of work.
- **"Sparse" is doing work.** The headline bounds beat O(m + n log n) when m is close to n; for dense graphs Dijkstra's O(m) term already dominates.
- **Negative weights.** None of this applies; use Bellman-Ford or the separate line of negative-weight algorithms.

## Check yourself

Q: Why must any algorithm that outputs vertices in order of distance make Ω(n log n) comparisons?
A: Sorting reduces to it: connect a source to n vertices with edge weights equal to the keys; the distance order is the sorted order, and comparison sorting needs Ω(n log n) comparisons.

Q: After round 2 of the trace, which distances are guaranteed exact and why is c not?
A: s, a and b, whose shortest paths use 0, 1 and 2 edges. c's shortest path s, a, b, c uses 3 edges, so it needs a third round; its estimate 8 (via a) is an upper bound.

Q: A colleague wants to replace Dijkstra in a routing service with the 2025 algorithm. What do you say?
A: The bound is asymptotically better but the measured implementation was 3 to 4 times slower up to 10 million vertices, and the service probably needs path order or uses preprocessing anyway. Keep Dijkstra (or the existing speed-up technique) and watch for practical follow-ups.

## Lab

- Run `sort_with_sssp` on 1,000 random floats and compare with `sorted`. Expected: identical lists.
- Measure the largest heap size during Dijkstra on a star of 10,000 vertices and on a path of 10,000 vertices. Expected: 9,999 and 1.
- Print log2 n, (log2 n)^(2/3) and sqrt(log2 n · log2 log2 n) for n = 10^6, 10^9 and 10^12. Expected: 19.9, 7.35, 9.28; 29.9, 9.63, 12.11; 39.9, 11.67, 14.56.

> [!know]
> You now know what the 2025 and 2026 shortest-path results proved, why avoiding the distance order is the key, and why Dijkstra remains the practical choice.

=== primer | Can open addressing beat uniform probing without moving keys? Elastic and funnel hashing | 12 min
goal: State the elastic and funnel hashing bounds precisely, explain the funnel structure, and judge when the asymptotic gain would matter
link: Farach-Colton, Krapivin and Kuszmaul 2025, introduction | https://arxiv.org/html/2501.02305v2#S1.SS0.SSS0.Px2 | The two theorems, what Yao conjectured, and the matching lower bounds, in two pages
link: Funnel hashing, section 3 | https://arxiv.org/html/2501.02305v2#S3 | The first page: levels of geometrically shrinking arrays split into buckets of size beta, one attempt per level, and the special overflow array

> [!key]
> Insert (1 - δ)n keys into an array of n slots. Each key has a random **probe sequence**, keys never move once placed (**no reordering**), and a key's **probe complexity** is its position in its sequence, which is also what a lookup costs. **Uniform probing** has amortised expected probe complexity Θ(log δ^-1) and worst-case expected O(δ^-1); Yao (1985) proved the first optimal for **greedy** schemes and conjectured the second was too. Farach-Colton, Krapivin and Kuszmaul (2025) built **elastic hashing** (non-greedy): amortised expected O(1) and worst-case expected O(log δ^-1); and **funnel hashing** (greedy): worst-case expected O(log² δ^-1), disproving Yao's conjecture. All bounds come with matching lower bounds.

## Intuition

A car park with one space in a thousand free. Uniform probing drives to random spaces until one is empty: about a thousand tries for the last car. Funnel hashing builds the car park as a stack of levels, each smaller than the last, split into short rows. A car tries one row per level and takes the first free space in it; most cars park on the big early levels, and the few that fail everywhere use a small, mostly empty overflow area.

## How it works

### Uniform probing, counted

When the table is a fraction α full, a random probe hits an empty slot with probability 1 - α, so an insert expects 1 / (1 - α) probes. The last inserts, at α = 1 - δ, expect 1/δ. Averaging over the whole fill gives (1/α) ln(1 / (1 - α)), about ln(1/δ): small on average, terrible at the end.

### Funnel hashing (greedy)

Let α = ceil(4 log δ^-1 + 10) and β = ceil(2 log δ^-1). Set aside a special array of between δn/2 and 3δn/4 slots. Split the rest into levels A1, ..., Aα, each about 3/4 the size of the previous one, each cut into buckets of β slots. To insert, hash the key to one bucket in A1 and take its first free slot; if the bucket is full, try one bucket in A2, and so on; if every level fails, use the special array. Each level only needs to end almost full; the shrinking levels below it catch the overflow. The worst insertion scans α buckets of β slots: O(log² δ^-1). With high probability the worst probe complexity over all insertions is O(log² δ^-1 + log log n).

### Elastic hashing (non-greedy)

Arrays halve in size. During a batch, an insertion may look ahead at a limited number of slots in a fuller array before settling in the next, emptier one: it "probes much further down the probe sequence before snapping back". Not taking the first free slot is essential, because Yao's lower bound for greedy schemes rules out amortised o(log δ^-1).

### Since then

Bender, Kuszmaul and Zhou (STOC 2025) showed that tables that encode information in the arrangement of elements (non-oblivious open addressing) can support constant-time operations even when completely full. Krapivin and Kuszmaul's braided cuckoo hashing (preprint, October 2026, to appear at SODA 2027) supports load factors up to 1 - ε with queries, insertions and deletions in worst-case O(log ε^-1) time with high probability.

## Cost

My simulation, n = 2^20 slots, filled to 1 - δ: mean probe complexity over all keys, the mean over the final δn/4 insertions (the worst-case regime), and the maximum. The funnel version is simplified: its overflow area uses random probing.

| δ | Random probing: mean, tail, max | Funnel: α, β, mean, tail, max |
|---|---|---|
| 2^-4 | 2.96, 14.0, 144 | 26, 8, 25.28, 89.6, 101 |
| 2^-6 | 4.22, 57.5, 504 | 34, 12, 40.90, 193.9, 208 |
| 2^-8 | 5.57, 223.5, 1,620 | 42, 16, 55.85, 339.5, 356 |
| 2^-10 | 6.97, 905.2, 5,642 | 50, 20, 70.32, 558.9, 594 |

The worst case behaves as promised: random probing's tail grows about four times per row (1/δ), funnel's far more slowly. But the constants (α · β = 1,000 slots at δ = 2^-10) mean funnel hashing only wins once the table is more than about 99.6% full, and its average is always worse here. One caveat favours funnel hashing: scanning a bucket of β adjacent slots costs a cache line or two, while every random probe is a separate cache miss, so counting probes understates its advantage.

## When to use it

These are results about what is possible, not drop-in replacements. Production tables avoid the high-load regime: Abseil's Swiss tables cap load at 7/8 and CPython's dict resizes at two-thirds full, where probe sequences are already short (next card). The ideas matter where memory is fixed and tables must run nearly full: hardware tables, compact filters, and the design of future libraries. Note also the model: a sequence of insertions only; deletions are not part of it.

## Worked trace

A toy funnel (not the paper's parameters): buckets of 2 slots; level 1 has 3 buckets, level 2 has 2, level 3 has 1. Each key's hashes pick one bucket per level.

```steps
Insert a (buckets 0, 1, 0): level 1 bucket 0 has room
    L1 [{{a}} .][. .][. .]   L2 [. .][. .]   L3 [. .]    probes 1
---
Insert b (buckets 0, 0, 0): second slot of the same bucket
    L1 [a {{b}}][. .][. .]   L2 [. .][. .]   L3 [. .]    probes 2
---
Insert c (buckets 0, 1, 0): bucket 0 is full, so try level 2, bucket 1
    L1 [a b][. .][. .]   L2 [. .][{{c}} .]   L3 [. .]    probes 3
---
Insert e (buckets 0, 1, 0) after d went to L1 bucket 2: fail on level 1, second slot of level 2 bucket 1
    L1 [a b][. .][d .]   L2 [. .][c {{e}}]   L3 [. .]    probes 4
---
Insert f (buckets 0, 1, 0): both buckets full, level 3 has room, although level 1 still has free slots elsewhere
    L1 [a b][. .][d .]   L2 [. .][c e]   L3 [{{f}} .]    probes 5
```

## Template

```python
import math


def random_probing(n, inserts, rng):
    """Greedy open addressing with an independent random slot per probe. Returns probes per key."""
    used, probes = bytearray(n), []
    for _ in range(inserts):
        p = 1
        slot = rng.randrange(n)
        while used[slot]:
            p += 1
            slot = rng.randrange(n)
        used[slot] = 1
        probes.append(p)
    return probes


def funnel(n, delta, inserts, rng):
    """Simplified funnel hashing: levels of buckets (size beta) shrinking by 3/4; a key tries one
    random bucket per level, scanning it, then falls back to a small overflow area."""
    lg = math.log2(1 / delta)
    alpha, beta = math.ceil(4 * lg + 10), math.ceil(2 * lg)
    spare = math.ceil(delta * n / 2)                    # overflow area A_{alpha+1}
    weights = [(3 / 4) ** i for i in range(alpha)]
    scale = (n - spare) / (beta * sum(weights))
    buckets = [max(1, int(scale * w)) for w in weights]  # buckets per level
    spare = n - beta * sum(buckets)
    assert spare >= delta * n / 2, "table too small for this delta"
    levels = [bytearray(b * beta) for b in buckets]
    overflow, probes = bytearray(spare), []
    for _ in range(inserts):
        p = 0
        for level, nb in zip(levels, buckets):
            start = rng.randrange(nb) * beta
            for k in range(start, start + beta):
                p += 1
                if not level[k]:
                    level[k] = 1
                    break
            else:
                continue
            break
        else:                                            # every level's bucket was full
            slot = rng.randrange(spare)
            p += 1
            while overflow[slot]:
                p += 1
                slot = rng.randrange(spare)
            overflow[slot] = 1
        probes.append(p)
    return probes, alpha, beta
```

Run `random_probing(n, n - int(delta * n), random.Random(e))` and `funnel(n, delta, n - int(delta * n), random.Random(e))` for δ = 2^-e to reproduce the table; the random-probing mean matches (1/α) ln(1 / (1 - α)).

## Pitfalls

- **Reading the bound as a speed-up.** At the load factors real tables use, uniform-style probing is already cheap; the gains appear only at extreme fullness.
- **Probe complexity versus time.** The bounds count probes; time depends on cache lines and branches, which favour contiguous scans.
- **Model mismatch.** The theorems assume random probe sequences, insert-only workloads and no reordering; Robin Hood and cuckoo hashing move keys and live in a different model.
- **Small tables.** The structure needs many levels of many buckets; my sizing fails for δ = 2^-12 with n = 2^20, because the deepest levels round to zero buckets.

## Check yourself

Q: With random probing, how many probes should the next insertion expect when the table is 99.9% full?
A: About 1 / (1 - 0.999) = 1,000, since each probe finds an empty slot with probability 0.001.

Q: What exactly did funnel hashing disprove, and why could it do so while being greedy?
A: Yao's conjecture that every greedy scheme has worst-case expected probe complexity at least (1 - o(1))·δ^-1. Yao's optimality proof covered the amortised cost, which funnel hashing does not beat (it is O(log δ^-1)); its worst case is O(log² δ^-1), which is o(δ^-1).

Q: In the simulation at δ = 2^-6, funnel's tail mean was 193.9 probes against 57.5 for random probing. Is the theorem wrong?
A: No. The theorem is asymptotic: with α = 34 levels and buckets of β = 12, a failing insertion scans hundreds of slots before overflow, which only pays off when 1/δ is much larger. At δ = 2^-10 the ordering flips (558.9 against 905.2).

## Lab

- Run the simulation for δ = 2^-6 and δ = 2^-10 with n = 2^20 and seeds 6 and 10. Expected: random probing mean 4.22 and 6.97 with tails 57.5 and 905.2; funnel mean 40.90 and 70.32 with tails 193.9 and 558.9.
- Compare random probing's mean with (1/α) ln(1 / (1 - α)) for α = 1 - 2^-6. Expected: 4.29 in theory against 4.22 measured (a single run; the mean has some noise).

> [!know]
> You now know what elastic and funnel hashing proved about open addressing without reordering, how funnel hashing is built, and why the gains need very full tables.

=== primer | Can a model replace a B-tree? Learned indexes and what stuck | 10 min
goal: Build an error-bounded piecewise-linear learned index, explain where its speed comes from, and say where learned indexes have been used
tag: frontier-learned-index | Error-bounded learned index
link: Kraska et al. 2018 | https://arxiv.org/abs/1712.01208 | The abstract and section 2 of the PDF: indexes as models of the key distribution (the CDF), and the recursive model index
link: Marcus et al. 2020, SOSD benchmark | https://arxiv.org/abs/2006.12804 | The abstract and introduction: where learned indexes win (read-only, in-memory, dense arrays) and why (cache misses)

> [!key]
> A sorted array's index is a function from key to position, which is n times the key distribution's CDF. Kraska, Beutel, Chi, Dean and Polyzotis (2018) proposed **learning** it: a model predicts a key's position, then a short search in a window around the prediction finishes the job. They reported up to 70% faster lookups than cache-optimised B-trees and an order of magnitude less memory on several real datasets. What stuck: **error-bounded** piecewise-linear indexes such as the PGM-index, updatable designs such as ALEX, a careful benchmark (SOSD) showing wins on read-only in-memory data, and a learned index inside Google's Bigtable.

## Intuition

If surnames were spread evenly through a phone book, you could open it at the right page by arithmetic: "M is about halfway". Real keys are not even, but within short stretches they often are nearly linear. Fit a line to each stretch, guarantee that every key is within ε positions of its line's prediction, and a lookup is: pick the stretch, compute the guess, scan 2ε + 1 slots.

## How it works

### Segments with a guaranteed error

Walk the sorted keys. A segment starts at key k0 in position p0 and keeps a range of slopes for which every key so far is predicted within ±ε. Each new key narrows the range; when it would become empty, close the segment and start a new one. This greedy "shrinking cone" is linear time. The PGM-index computes the optimal number of segments and indexes the segments' first keys recursively with the same structure, which gives its guaranteed I/O-optimal queries.

### Lookup

Find the segment (binary search over the segments' first keys, or another model layer), predict p0 + slope · (x - k0), and binary-search the window [guess - ε, guess + ε + 1].

### What happened next

- **Guarantees.** The PGM-index paper reports 63.3% less space than the FITing-tree and over four orders of magnitude less than a B-tree at the same or better query time.
- **Updates.** ALEX handles inserts, updates and deletes; its paper reports up to 4.1 times faster than B+ trees across read-write workloads.
- **Fair benchmarks.** SOSD confirmed that learned indexes beat tuned traditional indexes in read-only, in-memory workloads over dense arrays, and found cache misses to be the single most important explanatory variable; branch misses did not explain the wins.
- **Production.** A Google workshop paper (2020) integrated a learned index into Bigtable, predicting which block holds a key rather than the exact record, and measured 36% lower latency for point lookups and 22% for scans, with 55% and 28% higher throughput, on average in its evaluation.

## Cost

Build: O(n) for the greedy segmentation. Lookup: O(log s) comparisons to find one of s segments plus O(log ε) in the window. Memory: three numbers per segment. On my one-million-key datasets:

| Keys | ε = 16 | ε = 64 |
|---|---|---|
| Uniform | 1,403 segments | 102 segments |
| Lognormal | 1,420 segments | 164 segments |
| 1,000 tight clusters | 2,037 segments | 1,000 segments |

Comparisons barely change: about 15 to 18 against 20 for binary search over a million keys. The gain is where those comparisons happen. The segment table is tiny and stays in cache, and the final window is a few adjacent cache lines, whereas binary search over 8 MB of keys jumps across the whole array. That matches SOSD's cache-miss finding.

## When to use it

| Data and workload | Choice |
|---|---|
| Sorted, read-mostly, smooth distribution, in memory | Learned index (PGM-style), or a learned top level over blocks |
| Heavy inserts and deletes | B+ tree, or an updatable learned index such as ALEX after benchmarking |
| Point lookups only | A hash table |
| Variable-length string keys | B-tree or trie; models are harder to fit to strings |

Use it inside immutable sorted files (SSTables, column segments, time-series blocks), where the data never changes after the model is built. Always benchmark against a well-tuned B-tree on your own key distribution.

## Worked trace

Keys [2, 4, 6, 8, 10, 40, 41, 42, 43, 44], ε = 1.

```steps
Start a segment at key 2 (position 0); keys 4 to 10 fit slope 0.5 exactly
    keys   2  4  6  8  10 | 40 41 42 43 44
    pos    0  1  2  3  4  |  5  6  7  8  9
---
Key 40 at position 5 would need slope about 0.13: no slope keeps all keys within 1, so close the segment
    segment 1: k0 = 2, p0 = 0, slope 0.5
---
Start segment 2 at key 40 (position 5); the rest fit slope 1
    segment 2: k0 = 40, p0 = 5, slope 1.0
---
Look up 8: segment 1, guess 0 + 0.5 × 6 = 3; search positions 2 to 5
    window  {{6  8  10}}  ->  found at 3
---
Look up 42: segment 2, guess 5 + 1 × 2 = 7; found at 7. Look up 30: guess 14 is outside the array, so the answer is -1
    window  {{41 42 43}}  ->  found at 7
```

## Template

```python
import bisect
import math


def build_segments(keys, eps):
    """keys: sorted, distinct numbers. Greedy 'shrinking cone': each segment (k0, p0, slope)
    predicts the position of every key it covers within +-eps."""
    segs, i, n = [], 0, len(keys)
    while i < n:
        k0, p0, lo, hi = keys[i], i, 0.0, math.inf
        j = i + 1
        while j < n:
            dk = keys[j] - k0
            new_lo, new_hi = max(lo, (j - eps - p0) / dk), min(hi, (j + eps - p0) / dk)
            if new_lo > new_hi:
                break
            lo, hi, j = new_lo, new_hi, j + 1
        slope = 0.0 if hi == math.inf else (lo + hi) / 2
        segs.append((k0, p0, slope))
        i = j
    return segs


def lookup(keys, segs, firsts, eps, x):
    """Index of x in keys, or -1. firsts = [k0 of each segment]."""
    s = max(0, bisect.bisect_right(firsts, x) - 1)      # which segment
    k0, p0, slope = segs[s]
    guess = int(p0 + slope * (x - k0))
    lo, hi = max(0, guess - eps), min(len(keys), guess + eps + 2)
    i = bisect.bisect_left(keys, x, lo, hi)              # last-mile search in a tiny window
    return i if i < len(keys) and keys[i] == x else -1
```

Tested on 200 random key sets with ε from 1 to 64: every key is predicted within ε by its segment, and lookups of present and absent keys agree with `bisect`.

## Pitfalls

- **Average error is not enough.** Without a hard bound, a rare large error turns a lookup into a long scan. Enforce ±ε at build time, as here.
- **Floating point.** Python floats hold integers exactly only up to 2^53; for larger keys compute in integers or subtract k0 first, as `lookup` does.
- **Updates.** Inserting into the array shifts positions and invalidates every model after it; real systems rebuild, leave gaps (ALEX) or buffer inserts.
- **Adversarial or clustered keys.** Many small clusters force many segments (1,000 clusters gave 1,000 segments at ε = 64).

## Check yourself

Q: Learned lookups above use about 15 to 18 comparisons against 20 for binary search. Where does the reported speed-up come from?
A: Memory traffic: the segment table is small enough to stay in cache and the last-mile window is a few adjacent cache lines, while binary search over a large array touches about 20 distant cache lines. SOSD found cache misses to be the most important explanatory variable.

Q: Why did Bigtable's integration predict blocks rather than records?
A: Bigtable reads whole blocks from storage anyway, so knowing the exact record inside a block saves nothing, and a wrong block prediction would cost a whole extra block read. Learning the key-to-block mapping keeps every prediction correct.

Q: Your keys are user IDs inserted thousands of times a second. Learned index or B-tree?
A: Start with a B-tree (or a hash table if you only need point lookups). Constant inserts invalidate a static learned model; consider an updatable learned index only after benchmarking it on your workload.

## Lab

- Build segments for the tiny key list with ε = 1. Expected: [(2, 0, 0.5), (40, 5, 1.0)]; `lookup` returns 3 for 8, 7 for 42 and -1 for 30.
- Generate one million uniform keys (`sorted({rng.randrange(10**12) for _ in range(10**6)})` with `random.Random(8)`) and build with ε = 16 and ε = 64. Expected: roughly 1,400 and 100 segments (I got 1,403 and 102); the counts depend on the sample.

> [!know]
> You now know how a learned index predicts positions with an error bound, why its speed comes from cache behaviour, and where it has been used for real.

=== primer | What makes Swiss tables fast, and why did Go 1.24 switch its map to one? | 12 min
goal: Explain Swiss-table control bytes, group matching, probing and tombstones, implement a small one, and describe Go 1.24's adaptation
tag: frontier-swiss | Swiss-table probing
link: Abseil: Swiss Tables design notes | https://abseil.io/about/design/swisstables#metadata-lookup | 'Metadata layout' and 'Metadata lookup': H1 and H2, one control byte per slot, and the SSE code that matches 16 candidates at once
link: Go blog: Faster Go maps with Swiss Tables | https://go.dev/blog/swisstable#swiss-table | 'Swiss Table' for the 8-slot groups and control words, then 'Incremental growth' for the 1,024-entry tables and extendible hashing

> [!key]
> A **Swiss table** (designed at Google, presented in 2017, open-sourced in Abseil in 2018) is open addressing with a separate array of one-byte **control** entries per slot: empty, deleted, or the low 7 bits of the key's hash (**H2**). The remaining bits (**H1**) choose where probing starts. A lookup compares H2 with every control byte of a **group** of slots in one SIMD instruction (16 slots with SSE2 in Abseil, 8 in Go) and compares full keys only for matching bytes; an empty byte in the group ends the search. Probing a whole group at once makes long probe sequences cheap, so the table can run at 7/8 load. Rust's HashMap has used a Swiss-table design since 1.36, and Go 1.24 rebuilt its built-in map on one.

## Intuition

Searching a car park for your car by walking past every car and reading number plates is slow. Now imagine each bay has a small coloured light showing the last digit of the plate parked there. You glance down a row of 16 lights at once, and only walk to the one or two bays that show your digit. That is the control byte and the group match: most of the "probe" never touches the keys.

## How it works

### Hash split and control bytes

Abseil splits a 64-bit hash into H1 (57 bits, the starting position) and H2 (7 bits, stored in the control byte). A control byte is either a special value (empty, deleted) or the H2 of a full slot, so a random wrong key matches a full slot's byte with probability 1/128.

### Group matching

To find key x: start at the group chosen by H1, build a mask of control bytes equal to H2(x) (in Abseil, `_mm_cmpeq_epi8` plus `_mm_movemask_epi8` on 16 bytes), compare x with the key in each matching slot, and stop as soon as the group contains an empty byte: an insertion of x would have used it. Abseil's source comments estimate that even at high load fewer than 32 wrong keys sit in a probe sequence, so false-positive key comparisons average under 1/8 per lookup.

### Probing, deletion and load

If the group has no match and no empty slot, move to the next group. Abseil uses a triangular progression, offset Width · (i² + i) / 2 at step i, which visits every group exactly once when the number of groups is a power of two. Deleting writes a **tombstone** (deleted byte): probing continues past it, insertion may reuse it. The table grows above 7/8 full, which for 16-wide groups leaves about two empty slots per group.

### Go's version

Go 1.24 uses groups of 8 slots with a 64-bit control word, and solved two Go-specific problems. **Incremental growth**: a Go map is several independent Swiss tables of at most 1,024 entries each, chosen by the upper hash bits (extendible hashing), so one insertion never copies more than 1,024 entries. **Iteration with modification**, which Go's spec allows and Abseil forbids: iterators keep the old table for order but check the new one for current values. The Go team measured map operations up to 60% faster in microbenchmarks and about 1.5% lower CPU time (geometric mean) in full application benchmarks, with some edge cases slower.

## Cost

Measured with the template on 2^14 slots, against linear probing without metadata on the same keys:

| Load | Swiss: groups per miss, key compares per hit, per miss | Linear probing: compares per hit, per miss |
|---|---|---|
| 0.5 | 1.01, 1.033, 0.068 | 1.51, 1.55 |
| 0.75 | 1.23, 1.049, 0.116 | 2.52, 7.99 |
| 0.875 | 2.08, 1.061, 0.230 | 4.64, 34.54 |

At 7/8 load a failed lookup in linear probing compares against 35 keys; the Swiss table inspects about two groups (two SIMD instructions in C++) and compares 0.23 keys. Each key comparison may be a pointer chase and a string compare, so this is where the time goes.

## When to use it

You use Swiss tables through libraries: `absl::flat_hash_map`, Rust's `HashMap`, Go's `map`. Prefer a flat Swiss map for small keys and values that move cheaply. Choose a node-based variant (`absl::node_hash_map`) when references to elements must stay valid across rehashes, because flat tables move elements when they grow. CPython's dict is a different open-addressing design and grows when two-thirds full; the hashing module covers it.

## Worked trace

A 2-group table (32 slots), 20 integer keys inserted, then key 1004 deleted. Control bytes show H2 values, -- for empty and xx for deleted.

```steps
Group 0 and group 1 after the inserts and the delete
    group 0   83 106 23 48 27 98 93 60 56 122 21 -- -- -- -- --
    group 1   08  xx 52 70 25 95 126 81 35 -- -- -- -- -- -- --
---
Look up 1013: H1 picks group 0, H2 = 60. One match in the control bytes
    group 0   83 106 23 48 27 98 93 {{60}} 56 122 21 -- -- -- -- --
---
Compare the full key in that slot: it is 1013. Found after 1 key comparison
    slot 7    key 1013 -> "user1013"
---
Look up 2156 (absent): group 0, H2 = 60 again. The match is a false positive: slot 7 holds 1013
    group 0   83 106 23 48 27 98 93 {{60}} 56 122 21 {{--}} -- -- -- --
---
Group 0 has an empty byte, so 2156 cannot be further on: not found after 1 key comparison. Looking up the deleted 1004 (group 1, H2 = 37) matches nothing and stops at group 1's empty bytes
    group 1   08 {{xx}} 52 70 25 95 126 81 35 {{--}} -- -- -- -- -- --
```

## Template

```python
EMPTY, DELETED, GROUP = 0x80, 0xFE, 16
MASK64 = (1 << 64) - 1


def mix(key):
    """Spread entropy over all 64 bits (Swiss tables need good low and high bits)."""
    h = (hash(key) * 0x9E3779B97F4A7C15) & MASK64
    return h ^ (h >> 29)


class SwissMap:
    def __init__(self, groups=1):
        self.ctrl = bytearray([EMPTY]) * (groups * GROUP)   # metadata: 1 byte per slot
        self.slots = [None] * (groups * GROUP)              # (key, value) pairs
        self.size = self.used = 0                           # used = full + deleted
        self.key_compares = 0

    def _groups(self, h1):
        """Triangular probing: group offsets 0, 1, 3, 6, ... visit every group once
        when the number of groups is a power of two."""
        n = len(self.ctrl) // GROUP
        g = h1 & (n - 1)
        for i in range(n):
            yield g * GROUP
            g = (g + i + 1) & (n - 1)

    def _find(self, key, h1, h2):
        for base in self._groups(h1):
            ctrl = self.ctrl[base:base + GROUP]
            for i, c in enumerate(ctrl):        # a CPU does these 16 byte compares in one instruction
                if c == h2:
                    self.key_compares += 1
                    if self.slots[base + i][0] == key:
                        return base + i
            if EMPTY in ctrl:                   # an empty slot ends the probe sequence
                return None
        return None

    def get(self, key, default=None):
        h = mix(key)
        i = self._find(key, h >> 7, h & 0x7F)
        return default if i is None else self.slots[i][1]

    def put(self, key, value):
        h = mix(key)
        h1, h2 = h >> 7, h & 0x7F
        i = self._find(key, h1, h2)
        if i is not None:
            self.slots[i] = (key, value)
            return
        if (self.used + 1) * 8 > len(self.ctrl) * 7:      # keep load <= 7/8
            self._resize()
        for base in self._groups(h1):
            for j in range(base, base + GROUP):
                if self.ctrl[j] in (EMPTY, DELETED):
                    self.used += self.ctrl[j] == EMPTY
                    self.ctrl[j], self.slots[j] = h2, (key, value)
                    self.size += 1
                    return

    def delete(self, key):
        h = mix(key)
        i = self._find(key, h >> 7, h & 0x7F)
        if i is not None:
            self.ctrl[i], self.slots[i] = DELETED, None   # tombstone: probing must continue past it
            self.size -= 1

    def _resize(self):
        live = [s for s in self.slots if s is not None]
        groups = len(self.ctrl) // GROUP
        if len(live) * 16 > len(self.ctrl) * 7:    # more than half of the 7/8 limit: grow
            groups *= 2
        self.__init__(groups)                      # otherwise same size, tombstones dropped
        for k, v in live:
            self.put(k, v)
```

Checked against `dict` over 40 runs of 3,000 random put, delete and get operations (load always at most 7/8), and triangular probing was confirmed to visit every group exactly once for 1 to 2,048 groups. Integer keys keep the trace reproducible, because `hash()` of a string changes between Python processes.

## Pitfalls

- **Weak hash functions.** With Python's raw `hash()` on sequential integers, 128 consecutive keys share one starting group. In my test at 7/8 load a miss then inspected 14.9 groups instead of 1.7. Abseil's notes stress hashes that spread entropy over all 64 bits.
- **Tombstone build-up.** Many deletes leave deleted bytes that lengthen probes; rebuild at the same size when they pile up, as `_resize` does.
- **Moving elements.** Flat tables relocate entries on growth; never hold pointers into them across inserts.
- **False positives still need equality.** An H2 match is only a candidate; always compare the full key.

## Check yourself

Q: Why can a lookup stop at a group that contains an empty byte, but not at one that contains only deleted bytes?
A: An insertion of the key would have used the first free slot along its probe sequence, so if the key were further along, this empty slot would have been taken. A deleted slot was full when later keys were inserted, so keys inserted after it may sit further on; tombstones must not end the search.

Q: Roughly how many full-key comparisons does a successful lookup make, and why?
A: About one: the matching slot itself plus false positives, which occur with probability 1/128 per wrong full slot examined. With fewer than 32 wrong slots in a typical probe sequence that adds under 1/8 (my measurement at 7/8 load: 1.061 comparisons per hit).

Q: What problem did Go's 1,024-entry tables solve, and what would happen without them?
A: Growth latency. A single Swiss table doubles all at once, copying every entry; a 1 GB map would stall one insertion for the whole copy. With independent 1,024-entry tables selected by upper hash bits, only one small table splits at a time, so no insertion copies more than 1,024 entries.

## Lab

- Build the 2-group table above (keys 1001 to 1020, delete 1004) and look up 1013, 2156 and 1004 while counting key comparisons. Expected: "user1013" with 1 comparison, None with 1 comparison (a false positive), None with 0.
- Fill a 2^14-slot table to 7/8 with keys 0 to 14,335, then probe 14,336 absent keys using `mix` and using plain `hash`. Expected: about 1.66 groups and 0.17 key comparisons per miss with `mix`, against 14.86 groups and 1.73 comparisons with `hash`.

> [!know]
> You now know how Swiss tables use control bytes, group matching, triangular probing and tombstones, and how Go adapted them for incremental growth.

=== primer | Which sorting algorithms do standard libraries use now, and why? | 12 min
goal: Name the current default sorts in Rust, Go and CPython, explain what each optimises, and implement powersort's merge policy on run lengths
tag: frontier-powersort | Powersort merge policy
link: CPython listsort.txt | https://github.com/python/cpython/blob/main/Objects/listsort.txt | 'The Merge Pattern' (powersort and its 'power' of a run boundary) and the minrun section (Pochmann's balanced scheme)
link: Rust std: slice::sort_unstable | https://doc.rust-lang.org/std/primitive.slice.html#method.sort_unstable | 'Current implementation' for ipnsort; the same section under slice::sort describes driftsort

> [!key]
> Standard library sorts are now **hybrid and adaptive**. Unstable sorts build on **pattern-defeating quicksort** (pdqsort, Orson Peters): quicksort with a heapsort fallback and pattern detection. Go's sort package switched to it in 1.19. Rust 1.81 replaced both of its sorts: `sort_unstable` is now **ipnsort** and `sort` is **driftsort** (Bergdoll and Peters), and both may now panic on an ordering that is not a total order. Stable sorts merge natural runs: CPython 3.11 changed list.sort's merge order to **powersort** (Munro and Wild), provably near-optimal in the entropy of the run lengths, and CPython 3.15 balances the merge tree further with a new minimum-run-length scheme.

## Intuition

Real data is rarely random: logs arrive almost sorted, a list is two sorted lists concatenated, a column has only a few distinct values. A modern sort spends linear time on such inputs and still guarantees O(n log n). For merge-based sorts the remaining question is the order in which to merge the runs it finds: merging two big runs early and a tiny one late costs more than the reverse.

## How it works

### The unstable family

- **pdqsort**: quicksort with careful pivots, insertion sort for small parts, a switch to heapsort when partitions keep coming out unbalanced, and a partitioning scheme that its paper shows gives O(nk) worst case for inputs with k distinct values. Go 1.19 adopted it; Rust's `sort_unstable` used it until 1.80.
- **ipnsort** (Rust 1.81+ `sort_unstable`): per the Rust docs, combines quicksort's fast average case with heapsort's worst case, runs in linear time on fully sorted and reversed inputs, and has expected O(n log k) time with k distinct elements.

### The stable family

- **driftsort** (Rust 1.81+ `sort`): combines quicksort's average case with mergesort's worst case and partial run detection; linear on sorted and reversed input; expected O(n log k) with k distinct elements.
- **CPython list.sort**: finds natural runs (extending short ones with binary insertion), pushes them on a stack and merges neighbours. Stability forbids merging non-adjacent runs.

### Powersort's merge policy

For two adjacent runs, take their midpoints as fractions of the list length n. The boundary's **power** is the first bit position at which those two binary fractions differ: the depth of that boundary in an ideal, perfectly balanced merge tree over the positions. When a new run arrives, compute the power of the boundary between it and the top run, merge runs on the stack whose saved power is greater (deeper boundaries are merged first), then push. Powers on the stack strictly decrease, so the stack stays O(log n) deep.

### Broken comparators

Rust 1.81's sorts try to detect orderings that are not total and panic instead of returning arbitrarily ordered data. Python never panics, but an inconsistent `__lt__` gives an unspecified order.

## Cost

Merge cost = total size of all merges (each element is copied once per merge it takes part in). Over 3,000 random run-length sequences, compared with the optimal merge order found by dynamic programming:

| Policy | Worst cost / optimal |
|---|---|
| CPython 3.10 (Timsort's original rules) | 1.536 |
| Powersort (CPython 3.11+) | 1.296 |

On runs [109, 94, 25, 1] the old rules cost 576 and powersort 375, which is optimal. Powersort is not always better: on [100, 1, 1, 100] it costs 404 against 306 for the old rules, the kind of contrived case the CPython changelog warns about. Adaptivity in numbers (CPython 3.12, 10,000 items): sorted and reversed inputs take 9,999 comparisons, two interleaved sorted halves 19,998, random input 119,862.

## When to use it

| Need | Python | Rust | Go |
|---|---|---|---|
| Stable (ties keep input order) | `sorted`, `list.sort`: always stable | `sort` (driftsort) | `sort.Stable` |
| Fastest, ties may move | (no unstable option) | `sort_unstable` (ipnsort) | `sort.Sort` (pdqsort) |

Use a stable sort when you sort by one key after another, or when ties carry meaning (earlier events first). Use an unstable sort when values are plain numbers or you want no extra memory.

## Worked trace

Runs of length 10, 20, 30 and 40 (n = 100).

```steps
Push run 10. Nothing to compare yet
    stack   [10]
---
Run 20 arrives. Midpoints 5/100 and 20/100: binary 0.000... and 0.001..., first difference at bit 3, so the boundary has power 3
    stack   [10 (p3), 20]
---
Run 30 arrives. Boundary 20|30 has power 2. The run below the top has saved power 3 > 2: merge 10 + 20
    merges  {{10+20}}
    stack   [30 (p2), 30]
---
Run 40 arrives. Boundary 30|40 has power 1, and 2 > 1: merge 30 + 30
    merges  10+20, {{30+30}}
    stack   [60 (p1), 40]
---
End: merge what is left. Total cost 30 + 60 + 100 = 190, the optimum for these runs
    merges  10+20, 30+30, {{60+40}}
```

## Template

```python
def power(s1, n1, n2, n):
    """Depth of the boundary between runs [s1, s1+n1) and [s1+n1, s1+n1+n2) in the ideal
    merge tree: the first bit where the run midpoints, as fractions of n, differ."""
    a, b = 2 * s1 + n1, 2 * s1 + 2 * n1 + n2      # twice the two midpoints
    p = 0
    while True:
        p += 1
        if a >= n:
            a, b = a - n, b - n
        elif b >= n:
            return p
        a, b = a << 1, b << 1


def powersort_merges(runs):
    """runs: lengths of the natural runs, left to right. Returns the merges as (left, right) lengths."""
    n, stack, merges, start = sum(runs), [], [], 0      # stack entries: [start, length, power]
    for length in runs:
        if stack:
            p = power(stack[-1][0], stack[-1][1], length, n)
            while len(stack) > 1 and stack[-2][2] > p:   # merge runs deeper than the new boundary
                (s, a, _), (_, b, _) = stack[-2], stack[-1]
                merges.append((a, b))
                stack[-2:] = [[s, a + b, stack[-2][2]]]
            stack[-1][2] = p
        stack.append([start, length, 0])
        start += length
    while len(stack) > 1:
        (s, a, pw), (_, b, _) = stack[-2], stack[-1]
        merges.append((a, b))
        stack[-2:] = [[s, a + b, pw]]
    return merges
```

`power` follows CPython's `powerloop()` and the merge loop follows `found_new_run()`. Over 3,000 random run sequences every policy produced r - 1 merges ending in one run, never beat the dynamic-programming optimum, and powersort was optimal on every 3-run case, as listsort.txt says it always is.

## Pitfalls

- **Assuming stability.** Go's `sort.Sort` and Rust's `sort_unstable` may reorder equal elements; Python's sort is always stable.
- **Inconsistent comparisons.** NaN in a float list, or a `key` that changes, breaks the total order; Rust 1.81 may panic, Python silently returns an unspecified order.
- **Optimising the wrong thing.** For Python, the comparison callback dominates: prefer `key=` (computed once per element) to `functools.cmp_to_key`.
- **Expecting powersort to win every case.** It is near-optimal on every input, not optimal on every input.

## Check yourself

Q: Compute the power of the boundary between runs of length 10 and 20 at the start of a 100-element list.
A: Midpoints are 5/100 = 0.05 and 20/100 = 0.2. In binary, 0.05 = 0.0000110... and 0.2 = 0.0011001...; they first differ at the third bit after the point, so the power is 3.

Q: Why must a stable merge sort only merge adjacent runs?
A: If equal elements appear in runs A, B and C, merging A with C first would place A's and C's copies next to each other and B's after them, breaking the input order of equal elements.

Q: Which Rust and Go functions would you call to sort a million integers as fast as possible, and why are they allowed to be unstable?
A: Rust's `sort_unstable` (ipnsort) and Go's `sort.Sort`, `sort.Ints` or `slices.Sort`. Equal integers are indistinguishable, so moving them is invisible, and an unstable sort avoids the extra memory a stable merge needs.

## Lab

- Compute `powersort_merges` for [10, 20, 30, 40], [100, 1, 1, 100] and [5, 5, 90]. Expected: costs 190, 404 and 110 (the optimal costs are 190, 306 and 110).
- Count list.sort comparisons with a counting `cmp_to_key` on 10,000 sorted, reversed, two-interleaved-halves and random items. Expected: 9,999, 9,999, 19,998 and about 120,000 (119,862 for `random.Random(3).sample(range(10000), 10000)` after the other runs in my script; the random count varies slightly with the permutation).

> [!know]
> You now know which sorts Rust, Go and CPython use, what each optimises, and how powersort decides which runs to merge.

=== primer | How can one bit per dimension still give trustworthy vector distances? RaBitQ | 12 min
goal: Quantise vectors to one bit per dimension with RaBitQ's random rotation, estimate inner products without bias, and measure the 1/sqrt(D) error
tag: frontier-rabitq | RaBitQ one-bit quantisation
link: Gao and Long 2024, section 3 | https://arxiv.org/html/2405.12497v1#S3 | Sections 3.1 and 3.2: normalising, the rotated hypercube codebook, the estimator and Theorem 3.2's error bound
link: AI page: vector compression | https://learningcurie.github.io/code-study-tracker/ai.html#l-l-embeddings-vector-compression-quantisation-and-rescoring | Binary and int8 quantisation with rescoring in a production vector database: the practical setting this result improves

> [!key]
> **RaBitQ** (Gao and Long, SIGMOD 2024) stores a D-dimensional vector as **D bits**. Each vector is first normalised relative to its cluster centroid, then multiplied by a random orthogonal matrix, and only the sign of each coordinate is kept. With one stored scalar, the inner product of the unit vector o with its quantised form ō, the estimator <ō, q> / <ō, o> is **unbiased** for <o, q> and its error is **O(1/sqrt(D))** with high probability, a guarantee product quantisation does not offer. Extended RaBitQ adds more bits per dimension, Faiss 1.11 (2025) ships an implementation, and Google's TurboQuant (2025) builds on the same random-rotation idea.

## Intuition

Keeping only the sign of each coordinate throws away a lot, unless every coordinate carries about the same amount of information. A random rotation makes that true: it smears any vector's energy evenly over all axes, so each sign bit tells you something similar. One number per vector, how closely its signs agree with itself, is then enough to rescale the estimate so it is right on average.

## How it works

### Normalise and rotate

In an IVF index each vector is assigned to a cluster; RaBitQ subtracts the centroid and normalises, giving a unit vector o. One random orthogonal matrix P (shared by the whole index) defines the codebook: the 2^D vectors whose coordinates are ±1/sqrt(D), rotated by P. The quantised vector ō is the codebook vector nearest to o, which is simply the signs of P^T·o. Store the D sign bits and the scalar <ō, o>.

### The estimator

For a query q (normalised the same way), RaBitQ estimates <o, q> by <ō, q> / <ō, o>. The paper proves its expectation is exactly <o, q> and that the error exceeds sqrt((1 - <ō, o>²) / <ō, o>²) · ε0 / sqrt(D - 1) with probability at most 2·exp(-c0·ε0²); in practice ε0 = 1.9. The scalar <ō, o> concentrates near 0.8 (0.798 to 0.800 for D from 10² to 10⁶).

### Re-ranking with the bound

Distances computed from the estimate come with a confidence interval. RaBitQ's IVF search re-ranks a candidate with its exact vector only if the interval's lower bound beats the best exact distance found so far, so there is no "how many to rescore" knob to tune.

### What followed

Extended RaBitQ (Gao et al., 2024) supports more bits per dimension, with an asymptotically optimal trade-off between space and error. Faiss 1.11.0 lists a RaBitQ implementation (with an `IndexIVFRaBitQ`). TurboQuant (Zandieh et al., 2025) also rotates randomly, then applies scalar quantisers per coordinate plus a 1-bit correction on the residual for unbiased inner products, and reports distortion within a factor of about 2.7 of the information-theoretic lower bound.

## Cost

Memory: D bits plus a scalar or two per vector. For D = 768, a float32 vector is 3,072 bytes and the code is 96 bytes: 32 times smaller (ignoring the scalar). Indexing: one D × D rotation per vector. Querying: rotate the query once, then each estimate is a dot product of ±1 signs with the rotated query; the paper's bitwise implementation also quantises the query and averages about 3 times faster than the original table-lookup PQ at equal accuracy.

My measurements, 2,000 random unit vector pairs per row (20 rotations × 100 pairs):

| D | mean <ō, o> | mean error | error std | std × sqrt(D) | max error |
|---|---|---|---|---|---|
| 64 | 0.802 | +0.0002 | 0.0577 | 0.462 | 0.214 |
| 256 | 0.799 | -0.0008 | 0.0296 | 0.473 | 0.109 |
| 1024 | 0.798 | -0.0006 | 0.0148 | 0.475 | 0.056 |

The mean error is zero within noise (unbiased) and std × sqrt(D) is constant: the 1/sqrt(D) law.

## When to use it

Use it when vector memory dominates cost and you can afford a re-ranking step on full vectors: large in-memory IVF indexes, or as the compressed tier in front of vectors stored on disk. It is strongest at high dimension (hundreds to thousands, typical of text embeddings). Do not use it alone where exact top-k order matters between nearly equal distances (the paper notes re-ranking is needed there), or at very low D, where the error is large.

| Method | Bits per dimension | Error guarantee |
|---|---|---|
| Plain sign (binary) quantisation | 1 | None; distances by Hamming count |
| Product quantisation | Usually under 1 to a few | None (the RaBitQ paper reports PQ failing badly on some datasets) |
| RaBitQ | 1 | Unbiased, O(1/sqrt(D)) with high probability |
| Extended RaBitQ | Several | Asymptotically optimal space-error trade-off |

## Worked trace

D = 8 is far too small for accuracy but shows every step.

```steps
Rotate the unit vector o with the random orthogonal P
    P^T o    0.07  0.28  0.14 -0.70  0.19  0.38  0.22 -0.41
---
Keep the signs: 8 bits, stored as one byte
    bits     1  1  1  {{0}}  1  1  1  {{0}}      byte 238
---
Store the scalar <o_bar, o> = 0.849 (o_bar = P · signs / sqrt(8))
    code     238      scalar 0.849
---
Query: estimate <o, q> = (signs · P^T q) / sqrt(8) / 0.849
    estimate 0.855    true value 0.966
---
At D = 8 the error is 0.11; at D = 1024 the typical error is about 0.015
    std at D=1024   {{0.0148}}
```

## Template

```python
import numpy as np


def random_rotation(D, rng):
    q, r = np.linalg.qr(rng.standard_normal((D, D)))
    return q * np.sign(np.diag(r))                     # a uniformly random orthogonal matrix


def quantise(o, P):
    """o: unit vector (data vector minus its cluster centroid, normalised).
    Returns the D-bit code and the stored scalar <o_bar, o>."""
    bits = (P.T @ o) > 0                               # which side of each rotated axis
    o_bar = P @ np.where(bits, 1.0, -1.0) / np.sqrt(len(o))
    return np.packbits(bits), float(o_bar @ o)


def estimate(code, o_dot, q, P):
    """Unbiased estimate of <o, q> for a unit query q from the code alone."""
    D = len(q)
    signs = np.where(np.unpackbits(code)[:D], 1.0, -1.0)
    return float(signs @ (P.T @ q)) / np.sqrt(D) / o_dot
```

Run with `rng = np.random.default_rng(0)`, D in 64, 128, 256, 512 and 1024, 20 rotations of 100 pairs each, to reproduce the table (a query is `unit(o + 0.8 * unit(noise))`).

## Pitfalls

- **Skipping normalisation.** The estimator is for unit vectors; RaBitQ normalises each vector relative to its cluster centroid and keeps the norms to recover real distances.
- **Different rotations.** Data and queries must use the same P.
- **Dropping the correction scalar.** Signs alone give a biased, Hamming-style similarity; dividing by <ō, o> is what makes the estimate unbiased.
- **No rescoring.** One-bit estimates rank near-ties badly; re-rank the candidates whose bounds overlap.

## Check yourself

Q: Your vectors have D = 1,536. Using std × sqrt(D) ≈ 0.47, what typical error should the estimate have?
A: About 0.47 / sqrt(1536) ≈ 0.012 in the inner product of the normalised vectors.

Q: Why does RaBitQ rotate the vectors randomly before taking signs?
A: Without rotation, a vector whose energy sits in a few coordinates would be summarised by signs that mostly describe noise. A random rotation spreads energy evenly over all coordinates, which is what the analysis (a Johnson-Lindenstrauss-style argument) needs for the estimate to be unbiased with error O(1/sqrt(D)).

Q: How does RaBitQ decide which candidates to re-rank with exact distances?
A: It turns the error bound into a lower bound on each candidate's distance and computes the exact distance only for candidates whose lower bound is smaller than the best exact distance found so far; the rest are dropped.

## Lab

- Run the D sweep. Expected: mean <ō, o> between 0.798 and 0.802, mean error within ±0.001 of zero, std falling from 0.0577 at D = 64 to 0.0148 at D = 1024, and std × sqrt(D) between 0.46 and 0.49.
- Compute the compression for D = 768. Expected: 3,072 bytes as float32 against a 96-byte code, 32 times smaller.

> [!know]
> You now know how RaBitQ compresses vectors to one bit per dimension with an unbiased, bounded estimate, and where it fits in a vector index.
