---
key: rangeq
name: Range queries: Fenwick and segment trees
stage: engineer
summary: Advanced and optional: answer range sums, minimums and counts on data that keeps changing in O(log n) per operation with sparse tables, Fenwick trees and segment trees.
why: This module is advanced and optional. Skip it on a first pass if your goal is interviews, where these structures are uncommon, and come back when a problem mixes updates with range questions or asks how many earlier elements are smaller. It starts where the prefix-sums module stops: a prefix table answers range sums in O(1), but one update rewrites O(n) entries. Fenwick and segment trees keep both operations at O(log n) by storing totals of power-of-two blocks, and the Fenwick tree finds its blocks with the lowest-set-bit trick from the bits module, which comes just before this one in the route. The same block-total idea runs in real systems: Peter Fenwick designed his tree for the cumulative frequency tables of adaptive arithmetic coding, Redis sorted sets answer ZRANK by adding per-link spans in a skip list, the Linux kernel finds overlapping memory mappings with augmented interval trees, and time-series databases keep rollups so long time ranges read a few coarse blocks instead of every sample.
outcomes:
- Decide from the mix of updates and queries whether you need prefix sums, a sparse table, a Fenwick tree or a segment tree
- Build a sparse table and answer static range minimum in O(1), and explain why it needs an idempotent operation
- Write a Fenwick tree from memory and explain why i += i & -i and i -= i & -i visit exactly the right nodes
- Count inversions, smaller-elements-after-self and ranks with a Fenwick tree over compressed values
- Implement a segment tree recursively and iteratively for any associative operation, and add lazy propagation for range updates
- Stress-test every range structure against a naive array and find where each one wins in Python
cues:
- Range sums, minimums or maximums interleaved with point updates, with n and q around 10^5 or more
- "How many earlier (or later) elements are smaller or larger than this one?"
- Many range updates and range queries mixed together
- Static data with a large number of range-minimum or range-maximum queries
- Values up to 10^9 that you would like to use as array indices
traps:
- Mixing a 0-indexed array with the 1-indexed Fenwick tree (add at index 0 loops forever, because 0 & -0 == 0)
- Using a sparse table for sums (overlapping blocks double-count) or on data that changes
- Setting a value with add(i, v) instead of add(i, v - old)
- Forgetting to push a pending lazy update before looking inside a node, or to recombine the parent afterwards
- Reaching for a segment tree when a Fenwick tree, a prefix table or a plain sorted list would do
systems:
- Peter Fenwick introduced his tree in 1994 for cumulative frequency tables in adaptive arithmetic coding, where each symbol bumps one count and the coder needs the total of all smaller symbols
- Redis sorted sets store a span on every skip-list link (how many elements it jumps over), so ZRANK adds spans along the search path in O(log N)
- The Linux kernel's interval_tree_generic.h builds interval trees as augmented red-black trees (each node also keeps the largest end point in its subtree); mm/interval_tree.c uses it to find the memory mappings that cover a file range
- Graphite's Whisper format stores each metric in several archives of decreasing resolution, rolled up from the finer one, and answers a query from the finest archive that covers the whole requested period
further:
- Article · 30 min | cp-algorithms: Fenwick tree, definition and range operations | https://cp-algorithms.com/data_structures/fenwick.html#definition-of-gi
- Article · 40 min | cp-algorithms: Segment tree, from the simplest form to lazy propagation | https://cp-algorithms.com/data_structures/segment_tree.html#simplest-form-of-a-segment-tree
- Article · 30 min | Algorithmica: Segment trees, the bottom-up implementation and its speed | https://en.algorithmica.org/hpc/data-structures/segment-trees/#bottom-up-implementation
- Article · 15 min | Wikipedia: Fenwick tree, its origin in arithmetic coding | https://en.wikipedia.org/wiki/Fenwick_tree#Motivation
bank: rangeq
---

=== primer | Where do prefix sums stop working, and what replaces them? | 12 min
goal: Predict the cost of naive, prefix-rebuild, block and tree approaches for a given mix of updates and queries, and choose one
link: USACO Guide: point update range sum | https://usaco.guide/gold/PURS#segment-tree | 10 min: the opening paragraphs of 'Segment Tree' and 'Binary Indexed Tree', which state the O(log n) per operation contract this card motivates

> [!key]
> A prefix table makes a range sum O(1) but an update O(n); a raw array makes an update O(1) but a range sum O(n). Storing **totals of blocks** sits between the two: one level of blocks of size about √n gives O(√n) for both operations, and a hierarchy of power-of-two blocks (a Fenwick tree or a segment tree) gives O(log n) for both. Choose by the mix of operations, not by habit.

## Intuition

A shop keeps a ledger of sales with a running total in the margin. "How much did we sell between entry 200 and entry 500?" is one subtraction. Then an old entry turns out to be wrong. Every running total after it is now wrong, and fixing them means rewriting the rest of the ledger. A second shop keeps only the raw entries: corrections are instant, but every question means adding up hundreds of lines.

Accountants solve this with page totals. Correct an entry and you fix one line and one page total. Ask about a range and you add the loose lines at each end plus a few whole page totals. Add a total per chapter and per volume, and both questions and corrections touch only a handful of numbers. That hierarchy of totals is exactly what Fenwick trees and segment trees store.

## How it works

### The two extremes

| Store | Update `a[i]` | Sum of `a[l:r]` |
|---|---|---|
| The raw array | O(1) | O(r - l), up to O(n) |
| A prefix table | O(n): rewrite `pre[i+1:]` | O(1) |

### One level of blocks

Split the array into blocks of size b and store each block's sum. An update changes one element and one block sum: O(1). A query walks loose elements up to the first block boundary, adds whole blocks, then walks the loose elements at the far end: at most 2b loose elements and n/b blocks, so O(b + n/b). Choosing b near √n balances the two terms, giving O(√n) per query. This is **square-root decomposition**. It is worth keeping as a fallback because it adapts to operations that do not fit a tree neatly.

### Many levels: trees

Now keep blocks of every power-of-two size. Each element sits in one block per level, about log2 n blocks in all, so an update touches O(log n) totals. Any range splits into O(log n) blocks, so a query reads O(log n) totals. A **segment tree** stores every block of a balanced binary split; a **Fenwick tree** stores a clever half of them, one per index, and finds them with bit arithmetic.

### Special cases that need no tree

- No updates at all: prefix sums for sums; a sparse table for minimum, maximum or gcd in O(1) after O(n log n) preparation.
- Many range updates and then one read of the whole array: a difference array.
- Updates that arrive in batches between long query phases: rebuild the prefix table once per batch.

## Cost

Count the work for n = q = 10^5 when half the operations are updates and half are range sums over random ranges (average length about n/3):

- **Raw array:** 5 x 10^4 queries x 3.3 x 10^4 elements is about 1.7 x 10^9 additions.
- **Prefix table:** 5 x 10^4 updates x about n/2 rewritten entries is about 2.5 x 10^9 writes.
- **Blocks, b = 316:** each query reads at most 2b + n/b, about 950 numbers, so about 5 x 10^7 in all.
- **Fenwick tree:** each operation takes at most 17 loop steps (log2 10^5 is about 16.6), two such loops for a range sum: a few million steps in all.

Python changes the constants but not the conclusion. `sum(a[l:r])` runs in C, so at n = 100 the raw array is as fast as anything; at n = 10^5 one range sum over a list takes over a millisecond while a Fenwick operation takes a few microseconds (the lab measures both).

## When to use it

| Data and operations | Structure | Update | Query |
|---|---|---|---|
| Static, range sums | Prefix sums | none | O(1) |
| Static, range min, max or gcd | Sparse table | none | O(1) after O(n log n) |
| Point updates, range sums or counts | Fenwick tree | O(log n) | O(log n) |
| Point updates, range min, max or any associative operation | Segment tree | O(log n) | O(log n) |
| Range additions, point reads | Fenwick tree over the difference array | O(log n) | O(log n) |
| Range updates, range queries | Lazy segment tree | O(log n) | O(log n) |
| Many range additions, then one read | Difference array | O(1) | O(n) once |

When not to use a tree: n in the low thousands in Python (the C-speed slice sum is competitive), offline problems that can sort their queries and sweep once, and order-statistics questions over arbitrary keys, where `sortedcontainers.SortedList` gives you insert, delete and rank with no index arithmetic.

## Worked trace

One level of blocks on 16 values, block size 4: a query, an update, and the query again.

```steps
Sixteen values in blocks of 4; each block stores its sum: [9, 22, 21, 28]
    index   0  1  2  3 |  4  5  6  7 |  8  9 10 11 | 12 13 14 15
    a       3  1  4  1 |  5  9  2  6 |  5  3  5  8 |  9  7  9  3
    block      9       |     22      |     21      |     28
---
Query `sum(a[2:13])`. Walk loose elements from the left until a block boundary: a[2] + a[3] = 5
    index   0  1  2  3 |  4  5  6  7 |  8  9 10 11 | 12 13 14 15
    a       3  1  {{4}}  {{1}} |  5  9  2  6 |  5  3  5  8 |  9  7  9  3
    block      9       |     22      |     21      |     28
---
Whole blocks 1 and 2 cover a[4:12]: add 22 + 21 = 43 without touching their eight elements
    index   0  1  2  3 |  4  5  6  7 |  8  9 10 11 | 12 13 14 15
    a       3  1  4  1 |  5  9  2  6 |  5  3  5  8 |  9  7  9  3
    block      9       |     {{22}}      |     {{21}}      |     28
---
Loose element on the right: a[12] = 9. Total 5 + 43 + 9 = 57, from 5 reads instead of 11
    index   0  1  2  3 |  4  5  6  7 |  8  9 10 11 | 12 13 14 15
    a       3  1  4  1 |  5  9  2  6 |  5  3  5  8 |  {{9}}  7  9  3
    block      9       |     22      |     21      |     28
---
Update a[6] = 7 (it was 2): change the element and its block's sum, 22 + 5 = 27. A prefix array would have to rewrite every entry after index 6
    index   0  1  2  3 |  4  5  6  7 |  8  9 10 11 | 12 13 14 15
    a       3  1  4  1 |  5  9  {{7}}  6 |  5  3  5  8 |  9  7  9  3
    block      9       |     {{27}}      |     21      |     28
---
The same query now reads 5 + (27 + 21) + 9 = 62. Update O(1), query O(n/b + b): with b = sqrt(n) both sides of the trade are O(sqrt n)
    index   0  1  2  3 |  4  5  6  7 |  8  9 10 11 | 12 13 14 15
    a       3  1  {{4}}  {{1}} |  5  9  7  6 |  5  3  5  8 |  {{9}}  7  9  3
    block      9       |     {{27}}      |     {{21}}      |     28
```

## Template

Keep the naive class: every structure in this module is stress-tested against it.

```python
from itertools import accumulate


class NaiveRange:
    """The oracle: O(1) update, O(n) query."""
    def __init__(self, a):
        self.a = list(a)

    def update(self, i, v):
        self.a[i] = v

    def query(self, l, r):
        return sum(self.a[l:r])


class PrefixRebuild:
    """The other extreme: O(n) update, O(1) query."""
    def __init__(self, a):
        self.a = list(a)
        self.pre = list(accumulate(self.a, initial=0))

    def update(self, i, v):
        self.a[i] = v
        self.pre[i:] = accumulate(self.a[i:], initial=self.pre[i])   # rewrite pre[i+1:]: O(n - i)

    def query(self, l, r):
        return self.pre[r] - self.pre[l]


class SqrtBlocks:
    """One level of block sums: O(1) update, O(sqrt n) query."""
    def __init__(self, a):
        self.a = list(a)
        self.b = max(1, int(len(a) ** 0.5))
        self.blocks = [sum(self.a[i:i + self.b]) for i in range(0, len(a), self.b)]

    def update(self, i, v):
        self.blocks[i // self.b] += v - self.a[i]
        self.a[i] = v

    def query(self, l, r):
        s = 0
        while l < r and l % self.b:            # loose elements on the left
            s += self.a[l]
            l += 1
        while l + self.b <= r:                 # whole blocks
            s += self.blocks[l // self.b]
            l += self.b
        while l < r:                           # loose elements on the right
            s += self.a[l]
            l += 1
        return s
```

## Pitfalls

- **Benchmarks at toy sizes** mislead in both directions: the naive array wins at n = 100 and loses by a factor of hundreds at n = 10^5.
- **Rebuilding after every update** when updates arrive in batches: rebuild once per batch instead.
- **Block size 0** for an empty array: the template guards it with `max(1, ...)`.
- **Throwing the oracle away:** the naive class is ten lines and catches nearly every off-by-one in the fancier structures.

## Check yourself

Q: n = 2 x 10^5 and q = 2 x 10^5 operations, half updates and half range sums over random ranges. Estimate the work for the raw array, the prefix table, √n blocks and a Fenwick tree, and say which are feasible in Python.
A: Raw array: 10^5 queries x about 6.7 x 10^4 elements, roughly 7 x 10^9 additions, too slow even in C-speed slices. Prefix table: 10^5 updates x about 10^5 rewritten entries, 10^10, too slow. Blocks with b of about 450: about 1,350 reads per query, roughly 1.4 x 10^8 operations in Python loops, borderline at best. Fenwick: 2 x 10^5 operations x 2 x 18 steps, about 7 x 10^6 steps, comfortably fast.

Q: Your data changes once a night and is queried millions of times during the day. Which structure, and why not a Fenwick tree?
A: A prefix table rebuilt once per night: O(n) per rebuild and O(1) per query. A Fenwick tree would make every one of the millions of queries O(log n) to support updates you do not have.

Q: Why does one level of blocks stop at O(√n), and how do the trees beat it?
A: A query pays up to n/b whole blocks plus up to 2b loose elements; n/b + 2b is smallest near b = √(n/2), which is still O(√n). With blocks of every power-of-two size, any range is covered by O(log n) blocks and each element belongs to O(log n) of them, so both operations drop to O(log n).

## Lab

- **Run the trace yourself:** build `NaiveRange`, `PrefixRebuild` and `SqrtBlocks` on `[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3]` and call `query(2, 13)`, `update(6, 7)`, `query(2, 13)`, `query(0, 16)`. Expected: 57, then 62, then 85 from all three classes.
- **Stress them:** write a loop of 1,000 random operations on random arrays of length 1 to 40 that applies each operation to all three classes and asserts equal answers. Expected: no mismatch. Then break `SqrtBlocks.update` on purpose (forget to update the block) and confirm that the loop catches it within a few operations.

> [!know]
> You now know how to predict which range structure an operation mix needs, and why trees of power-of-two blocks make both updates and queries O(log n).

=== primer | How does a sparse table answer range minimum in O(1)? | 14 min
goal: Build a sparse table in O(n log n) and answer any static range minimum with two lookups, and explain why the trick needs an idempotent operation
tag: rangeq-sparse | Sparse table
link: cp-algorithms: Sparse table | https://cp-algorithms.com/data_structures/sparse-table.html#range-minimum-queries-rmq | 10 min: 'Intuition', 'Precomputation' and 'Range Minimum Queries (RMQ)'; the 'Range Sum Queries' part shows the O(log n) disjoint version for sums
practice: cses:1647

> [!key]
> Precompute the minimum of every block whose length is a power of two: `table[j][i] = min(a[i : i + 2**j])`. Any range `[l, r)` is covered by **two blocks of the same power-of-two length**, one starting at l and one ending at r. They may overlap, but `min` does not care about counting an element twice, so the answer is two lookups: O(1) per query after O(n log n) preparation, for data that never changes.

## Intuition

Measure a 6-metre wall with two 4-metre rulers: put one against the left end and one against the right end. They overlap in the middle, but together they cover the wall exactly. If the question is "what is the lowest point along the wall?", the overlap is harmless: the lowest point is the lower of the two rulers' lowest points. If the question were "what is the total length?", the overlap would be counted twice. That is the whole idea of a sparse table, and also its limit.

## How it works

### The table

Level 0 is the array itself. Level j holds, for every start i, the minimum of the block of length 2^j starting at i. Each level is built from the one below by combining two halves:

`table[j][i] = min(table[j - 1][i], table[j - 1][i + 2**(j - 1)])`

Level j has `n - 2**j + 1` entries, and there are `floor(log2 n) + 1` levels.

### The query

For `[l, r)` with length L = r - l, take the largest power of two that fits: `j = L.bit_length() - 1`, so `2**j <= L < 2**(j + 1)`. The block starting at l, `[l, l + 2**j)`, and the block ending at r, `[r - 2**j, r)`, both lie inside the range, and because each is at least half its length, together they cover all of it. Return the smaller of the two stored minimums.

### Idempotent operations only

The overlap is safe exactly when combining a value with itself changes nothing: `min(x, x) == x`. Minimum, maximum, gcd, bitwise AND and OR all qualify. Sum, product and XOR do not; for them, split the range into disjoint power-of-two blocks (one per set bit of its length) for O(log n) per query, or use prefix sums, which are O(1) anyway for static sums.

### Static data only

Changing one element invalidates every block that contains it: up to 2^j entries on level j, about 2n entries in all. A sparse table is for data that never changes; with updates, use a segment tree.

## Cost

- **Build:** each level has at most n entries and each entry is one `min` of two numbers: at most n(floor(log2 n) + 1) operations, O(n log n) time.
- **Memory:** the same count of list slots. In CPython each slot is an 8-byte pointer; the int objects are shared with the input, because `min` returns one of its arguments rather than a new number. For n = 10^5 that is 17 levels and about 1.6 million slots, roughly 13 MB.
- **Query:** one `bit_length` (a single C call), two lookups and one comparison: O(1).
- **In practice:** for n = 2 x 10^5 a pure-Python build takes about 2 seconds, while 2 x 10^5 queries take well under half a second. Building each level with NumPy (`np.minimum(prev[:-half], prev[half:])`) moves the build into C.

## When to use it

| Need | Best choice | Why |
|---|---|---|
| Static range min or max, many queries | Sparse table | O(1) per query |
| Static range sums | Prefix sums | O(1) per query, O(n) memory |
| Range min with updates | Segment tree | O(log n) for both operations |
| Min of every window of a fixed size k | Monotonic deque | O(n) total, O(k) memory |
| Lowest common ancestor in a static tree | Euler tour plus a sparse table | O(1) per query after O(n log n) |

Do not use it when the data changes, when memory is tight (n log n slots for n = 10^7 is hundreds of millions), or for non-idempotent operations.

## Worked trace

```steps
Level 0 is the array itself: `table[0][i] = a[i]`, blocks of length 1
    i             0  1  2  3  4  5  6  7
    a (len 1)     5  2  4  7  1  3  6  8
---
Level 1: `table[1][i] = min(table[0][i], table[0][i + 1])`, the minimum of each block of length 2
    i             0  1  2  3  4  5  6  7
    a (len 1)     5  2  4  7  1  3  6  8
    j=1 (len 2)   {{2}}  {{2}}  {{4}}  {{1}}  {{1}}  {{3}}  {{6}}
---
Level 2 combines two level-1 entries 2 apart: `table[2][i] = min(table[1][i], table[1][i + 2])` covers 4 elements
    i             0  1  2  3  4  5  6  7
    a (len 1)     5  2  4  7  1  3  6  8
    j=1 (len 2)   2  2  4  1  1  3  6
    j=2 (len 4)   {{2}}  {{1}}  {{1}}  {{1}}  {{1}}
---
Level 3 covers all 8. Total work: about n entries per level, log2(n) + 1 levels: O(n log n)
    i             0  1  2  3  4  5  6  7
    a (len 1)     5  2  4  7  1  3  6  8
    j=1 (len 2)   2  2  4  1  1  3  6
    j=2 (len 4)   2  1  1  1  1
    j=3 (len 8)   {{1}}
---
Query `min(a[0:6])`: length 6, so j = 2 (blocks of 4). Use the block starting at 0 and the one ending at 6, which starts at 2: min(2, 1) = 1. They overlap on a[2:4], and min does not mind
    i             0  1  2  3  4  5  6  7
    a (len 1)     {{5}}  {{2}}  {{4}}  {{7}}  {{1}}  {{3}}  6  8
    j=1 (len 2)   2  2  4  1  1  3  6
    j=2 (len 4)   {{2}}  1  {{1}}  1  1
    j=3 (len 8)   1
---
Query `min(a[2:5])`: length 3, so j = 1. Blocks a[2:4] and a[3:5]: min(4, 1) = 1. Two lookups for any length
    i             0  1  2  3  4  5  6  7
    a (len 1)     5  2  {{4}}  {{7}}  {{1}}  3  6  8
    j=1 (len 2)   2  2  {{4}}  {{1}}  1  3  6
    j=2 (len 4)   2  1  1  1  1
    j=3 (len 8)   1
```

## Template

```python
def build_sparse(a):
    """table[j][i] = min(a[i : i + 2**j]); O(n log n) time and space."""
    table = [list(a)]
    j = 1
    while (1 << j) <= len(a):
        prev, half = table[j - 1], 1 << (j - 1)
        table.append([min(prev[i], prev[i + half]) for i in range(len(a) - (1 << j) + 1)])
        j += 1
    return table


def range_min(table, l, r):
    """min(a[l:r]) for l < r, O(1): two blocks of length 2**j that together cover [l, r)."""
    j = (r - l).bit_length() - 1
    return min(table[j][l], table[j][r - (1 << j)])
```

For maximum or gcd, replace `min` in both functions.

## Pitfalls

- **Sums:** the two blocks overlap, so a sparse table "sum" double-counts the middle.
- **Empty ranges:** `l == r` gives `bit_length() - 1 == -1`; the minimum of nothing is undefined, so reject it before calling.
- **Floating-point logarithms:** `int(math.log2(L))` can round the wrong way for huge L; `bit_length` is exact and faster.
- **Inclusive inputs:** most judges give 1-indexed, inclusive `a..b`; that is `range_min(table, a - 1, b)`.
- **Memory for large n:** a list of lists of 10^6 x 20 slots is about 160 MB; use NumPy arrays or a segment tree (O(n) memory, O(log n) query) instead.

## Check yourself

Q: For `a = [5, 2, 4, 7, 1, 3, 6, 8]`, which two table entries answer `min(a[1:8])`, and what is the answer?
A: The length is 7, so j = 2 (blocks of 4): `table[2][1] = min(a[1:5]) = 1` and `table[2][4] = min(a[4:8]) = 1`. The answer is 1; the blocks overlap on `a[4]`.

Q: Why can the same O(1) trick not answer range sums, and what answers static sums instead?
A: The two blocks overlap, and an overlapped element is added twice; minimum ignores duplicates, addition does not. For sums, split the range into disjoint power-of-two blocks (O(log n)), or simply use a prefix table, which is O(1) for static sums.

Q: You need range maximum on 10^6 static values with 10^6 queries, in Python, with 256 MB of memory. Sparse table or segment tree?
A: A sparse table built with NumPy: 20 levels of int64 are about 160 MB and each query is two lookups. Lists of lists would need a similar number of 8-byte slots plus Python overhead and a slow build. If memory were tighter, a segment tree uses O(n) memory at O(log n) per query.

## Lab

- **cses:1647 Static Range Minimum Queries:** build the table once, then answer each `a b` query with `range_min(table, a - 1, b)`. Expected: correct answers against `min(arr[a - 1:b])` on your own random tests. With n = q = 2 x 10^5, the pure-Python build takes about 2 seconds here, so if the judge times out, build the levels with NumPy or submit with PyPy; the query loop itself is fast.
- **Trace check:** on `[5, 2, 4, 7, 1, 3, 6, 8]`, `range_min` for `(0, 8)`, `(3, 4)`, `(5, 8)` and `(0, 2)` should give 1, 7, 3 and 2.

> [!know]
> You now know how to answer static range minimum in O(1) with two overlapping power-of-two blocks, and why the trick works only for idempotent operations.

=== primer | How does a Fenwick tree keep prefix sums correct under updates in O(log n)? | 18 min
goal: Write a Fenwick tree from memory, trace its update and query jumps on paper, and explain why node i covers exactly the lowbit(i) elements ending at i
tag: rangeq-fenwick | Fenwick tree (binary indexed tree)
link: cp-algorithms: Fenwick tree | https://cp-algorithms.com/data_structures/fenwick.html#overview | 15 min: 'Overview' and 'Definition of g(i)'; it uses a 0-based variant with a different g(i), a useful contrast with the 1-based tree here
link: VisuAlgo: Fenwick tree | https://visualgo.net/en/fenwicktree | 5 min: run a range sum query and an update on the default array and watch which indices each loop visits
practice: 307, cses:1651

> [!key]
> A Fenwick tree is an array `tree[1..n]` in which **node i stores the sum of the lowbit(i) elements ending at position i**, where lowbit(i) = `i & -i` is the value of i's lowest set bit. A prefix sum hops leftwards with `i -= i & -i`, collecting one disjoint chunk per set bit of i; an update hops upwards with `i += i & -i`, visiting exactly the chunks that contain the position. Both loops run at most log2(n) + 1 times.

## Intuition

Write a length in binary and it splits into powers of two: 13 = 8 + 4 + 1. So the first 13 elements split into a chunk of 8, then a chunk of 4, then a chunk of 1. If every position stored the sum of "its" power-of-two chunk, any prefix sum would be at most log2 n stored chunks added together.

The Fenwick tree gives each position i the chunk that **ends at i** and has length lowbit(i), the lowest set bit of i. You met lowbit in the bits module, which comes just before this one in the route: in two's complement, `-i` flips every bit above the lowest set bit, so `i & -i` keeps only that bit. Odd positions (lowbit 1) store one element; position 12 = 1100 stores the 4 elements 9 to 12; position 8 = 1000 stores all of 1 to 8.

```text
pos       1    2    3    4    5    6    7    8
binary  0001 0010 0011 0100 0101 0110 0111 1000
lowbit    1    2    1    4    1    2    1    8

tree[8] [=====================================]    1..8
tree[4] [=================]                        1..4
tree[6]                     [=======]              5..6
tree[2] [=======]                                  1..2
tree[1], tree[3], tree[5], tree[7]: one element each
```

## How it works

### Query: walk left one chunk at a time

`prefix(i)` adds `tree[i]`, which covers `(i - lowbit(i), i]`, then jumps to `i - lowbit(i)`, the position just before that chunk, and repeats until i = 0. The chunks are adjacent and disjoint, so together they tile `[1, i]` exactly. Each jump clears the lowest set bit of i, so the loop runs once per set bit: at most floor(log2 n) + 1 times.

### Update: walk up through every chunk that contains the position

`add(p, delta)` must change every node whose chunk contains p. Those nodes are exactly p, p + lowbit(p), and so on, because of two facts:

1. **The next node covers p.** Let q = p + lowbit(p). Adding lowbit(p) carries into a higher bit, so lowbit(q) is at least 2 x lowbit(p). The chunk of q therefore starts at q - lowbit(q) + 1, which is at most p - lowbit(p) + 1 <= p, and it ends at q > p: it contains p.
2. **Nothing in between covers p.** Any k with p < k < q is p + t with 0 < t < lowbit(p). The low bits of k are just t, so lowbit(k) = lowbit(t) <= t, and k's chunk starts at k - lowbit(k) + 1 >= p + 1: it misses p.

Each jump at least doubles lowbit, so the loop also runs at most floor(log2 n) + 1 times.

### Range sums, setting values and building

- **Range sum:** store `a[k]` (0-indexed) at position k + 1. Then `prefix(i)` is exactly `pre[i]` from the prefix-sums module, the sum of the first i elements, and the sum of `a[l:r]` is `prefix(r) - prefix(l)`. This needs subtraction, so it works for sums, counts and XOR, not for min or max.
- **Setting a value:** the tree only adds. To set `a[k] = v`, keep a copy of the values and call `add(k + 1, v - a[k])`.
- **Linear build:** n calls to `add` cost O(n log n). Instead, give each node its own element and push each node's finished total into its parent `i + lowbit(i)` once, left to right: O(n).

### Range additions with point reads

Run the tree over the **difference array** from the prefix-sums module. Adding v to `a[l:r]` is `add(l + 1, v)` and `add(r + 1, -v)`, and the current value of `a[i]` is `prefix(i + 1)`. Both are O(log n). (Range additions with range sums need two such trees; the cp-algorithms page derives it.)

## Cost

- **Time:** `prefix` and `add` each run at most floor(log2 n) + 1 iterations: 17 for n = 10^5, 20 for n = 10^6. A range sum is two prefix calls. The linear build is O(n).
- **Space:** one list of n + 1 numbers; no pointers, no child arrays. That compactness, plus very short loops, is why a Fenwick tree usually beats a segment tree for sums (by up to about two times in the lab).
- **Python detail:** `i & -i` works on Python's unbounded ints because they behave like infinite two's complement for bitwise operations.

## When to use it

Use a Fenwick tree for point updates plus prefix or range sums (or counts, or XOR), for counting with a histogram over values (the next card), and for range additions with point reads. Prefer a segment tree when the operation has no inverse (min, max, gcd), when you need range assignment, or when each node must hold a richer summary. Prefer a plain prefix table when the data never changes.

| | Prefix table | Fenwick tree | Segment tree |
|---|---|---|---|
| Point update | O(n) | O(log n) | O(log n) |
| Range sum | O(1) | O(log n) | O(log n) |
| Range min or max with updates | no | no | O(log n) |
| Memory | n + 1 | n + 1 | 2n to 4n |
| Lines of code | 3 | about 15 | 25 to 40 |

## Worked trace

Positions 1 to 8 hold `[5, 2, 9, -3, 6, 1, 4, 7]`. First a query:

```steps
Positions 1 to 8. Node i stores the sum of the lowbit(i) = `i & -i` elements ending at i: odd nodes hold one element, node 4 holds 1-4, node 8 holds everything
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  0100  0101  0110  0111  1000
    covers      1   1-2     3   1-4     5   5-6     7   1-8
    a           5     2     9    -3     6     1     4     7
    tree        5     7     9    13     6     7     4    31
---
`prefix(7)`: at i = 7 (0111) add `tree[7] = 4` (covers 7), running sum 4; then `i -= i & -i` clears the lowest set bit: i = 6
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  0100  0101  0110  {{0111}}  1000
    covers      1   1-2     3   1-4     5   5-6     {{7}}   1-8
    a           5     2     9    -3     6     1     4     7
    tree        5     7     9    13     6     7     {{4}}    31
---
`prefix(7)`: at i = 6 (0110) add `tree[6] = 7` (covers 5-6), running sum 11; then `i -= i & -i` clears the lowest set bit: i = 4
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  0100  0101  {{0110}}  0111  1000
    covers      1   1-2     3   1-4     5   {{5-6}}     7   1-8
    a           5     2     9    -3     6     1     4     7
    tree        5     7     9    13     6     {{7}}     4    31
---
`prefix(7)`: at i = 4 (0100) add `tree[4] = 13` (covers 1-4), running sum 24; then `i -= i & -i` clears the lowest set bit: i = 0
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  {{0100}}  0101  0110  0111  1000
    covers      1   1-2     3   {{1-4}}     5   5-6     7   1-8
    a           5     2     9    -3     6     1     4     7
    tree        5     7     9    {{13}}     6     7     4    31
---
i = 0: stop. `prefix(7) = 24` = 5 + 2 + 9 - 3 + 6 + 1 + 4, from three disjoint chunks 7, 5-6 and 1-4: one per set bit of 7 = 0111
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  {{0100}}  0101  {{0110}}  {{0111}}  1000
    covers      1   1-2     3   {{1-4}}     5   {{5-6}}     {{7}}   1-8
    a           5     2     9    -3     6     1     4     7
    tree        5     7     9    {{13}}     6     {{7}}     {{4}}    31
```

Then an update, and the same query again:

```steps
Now `add(3, +5)`: every node whose chunk contains position 3 must change. Start at i = 3 (0011)
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  {{0011}}  0100  0101  0110  0111  1000
    covers      1   1-2     {{3}}   1-4     5   5-6     7   1-8
    a           5     2     9    -3     6     1     4     7
    tree        5     7     {{9}}    13     6     7     4    31
---
`tree[3] += 5` (it covers 3, which contains 3); then `i += i & -i`: 0011 + 0001 = 0100, so i = 4
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  {{0011}}  0100  0101  0110  0111  1000
    covers      1   1-2     {{3}}   1-4     5   5-6     7   1-8
    a           5     2    14    -3     6     1     4     7
    tree        5     7    {{14}}    13     6     7     4    31
---
`tree[4] += 5` (it covers 1-4, which contains 3); then `i += i & -i`: 0100 + 0100 = 1000, so i = 8
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  {{0100}}  0101  0110  0111  1000
    covers      1   1-2     3   {{1-4}}     5   5-6     7   1-8
    a           5     2    14    -3     6     1     4     7
    tree        5     7    14    {{18}}     6     7     4    31
---
`tree[8] += 5` (it covers 1-8, which contains 3); then `i += i & -i`: 1000 + 1000 = 10000, so i = 16, past n = 8: stop
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  0100  0101  0110  0111  {{1000}}
    covers      1   1-2     3   1-4     5   5-6     7   {{1-8}}
    a           5     2    14    -3     6     1     4     7
    tree        5     7    14    18     6     7     4    {{36}}
---
Only nodes 3, 4 and 8 changed. `prefix(7)` again: 4 + 7 + 18 = 29, five more than before
    pos         1     2     3     4     5     6     7     8
    binary   0001  0010  0011  {{0100}}  0101  {{0110}}  {{0111}}  1000
    covers      1   1-2     3   {{1-4}}     5   {{5-6}}     {{7}}   1-8
    a           5     2    14    -3     6     1     4     7
    tree        5     7    14    {{18}}     6     {{7}}     {{4}}    36
```

## Template

```python
class Fenwick:
    """Point add and prefix sum, O(log n) each. Positions are 1..n;
    store a[k] (0-indexed) at position k + 1, then prefix(i) == sum(a[:i])."""

    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)          # tree[0] is unused

    @classmethod
    def from_list(cls, a):
        """O(n) build: each node passes its total up to its parent once."""
        f = cls(len(a))
        for i, x in enumerate(a, 1):
            f.tree[i] += x
            parent = i + (i & -i)
            if parent <= f.n:
                f.tree[parent] += f.tree[i]
        return f

    def add(self, i, delta):
        """a[i] += delta (position i, 1-indexed)."""
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i                    # next node whose chunk contains i

    def prefix(self, i):
        """a[1] + ... + a[i]; prefix(0) == 0."""
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i                    # jump to the chunk just before this one
        return s

    def range_sum(self, l, r):
        """Sum of the 0-indexed half-open slice a[l:r]."""
        return self.prefix(r) - self.prefix(l)


class RangeAddPointQuery:
    """Fenwick tree over the difference array: add v to a[l:r] and read a[i], O(log n) each."""

    def __init__(self, n):
        self.f = Fenwick(n + 1)

    def range_add(self, l, r, v):
        self.f.add(l + 1, v)
        self.f.add(r + 1, -v)

    def value(self, i):
        return self.f.prefix(i + 1)
```

In C++ the same loops use `i & -i` on signed ints or `i & (~i + 1)`; Java is identical. Neither language ships a Fenwick tree, and neither does Python's standard library.

## Pitfalls

- **Position 0:** `add(0, x)` never ends, because `0 & -0 == 0` and i stays 0. Shift 0-indexed positions by one, once, at the boundary.
- **Set versus add:** `add(i, v)` adds v; to set a value you need the old one.
- **Min and max:** a prefix minimum cannot be "subtracted" to give a range minimum, and a decreased value cannot be undone; use a segment tree.
- **Tree size:** `n + 1` slots for positions 1..n; the difference-array version needs one more because `r + 1` can be n + 1.
- **Inclusive judges:** LeetCode 307's `sumRange(left, right)` is inclusive, so it is `range_sum(left, right + 1)`.

## Check yourself

Q: For n = 8, which nodes does `add(5, x)` visit, and which does `prefix(6)` read?
A: `add(5, x)` visits 5 (0101), then 6 (0110), then 8 (1000), and stops at 16. `prefix(6)` reads `tree[6]` (positions 5 to 6) and then `tree[4]` (positions 1 to 4), and stops at 0.

Q: Why does `prefix(i)` never take more than floor(log2 n) + 1 steps, and why are the chunks it adds disjoint?
A: Each step `i -= i & -i` clears the lowest set bit, and a number up to n has at most floor(log2 n) + 1 set bits. The chunk read at i is `(i - lowbit(i), i]` and the next read starts at `i - lowbit(i)`, so consecutive chunks meet without overlapping and tile `[1, i]`.

Q: A colleague's 0-indexed code calls `add(0, 5)` and the program hangs. Why, and what is the fix?
A: With i = 0, `i & -i` is 0, so i never changes and `while i <= n` loops forever (and `tree[0]` is not a real node). Store element k at position k + 1 and convert only at the class boundary.

Q: You need `set(i, v)` and `sum(l, r)` on the same array. What extra state do you keep and what does `set` do?
A: Keep a copy `a` of the current values; `set(i, v)` calls `add(i + 1, v - a[i])` and then stores `a[i] = v`.

## Lab

- **307 Range Sum Query - Mutable:** build with `from_list` in the constructor, implement `update` with the stored delta and `sumRange(left, right)` as `range_sum(left, right + 1)`. Expected: on `[2, 4, 6, 8]`, `sumRange(1, 2)` returns 10; after `update(1, -1)`, `sumRange(0, 3)` returns 15; every call O(log n).
- **cses:1651 Range Update Queries:** use `RangeAddPointQuery`, loading the initial values as length-1 additions. Expected: for `[1, 2, 3, 4, 5]`, adding 10 to positions 2 to 4 (1-indexed, inclusive) makes position 3 read 13, position 5 read 5 and position 1 read 1.
- **Check the build:** `Fenwick.from_list([5, 2, 9, -3, 6, 1, 4, 7]).tree[1:]` should be `[5, 7, 9, 13, 6, 7, 4, 31]`, the same as eight calls to `add`.

> [!know]
> You now know how a Fenwick tree stores one power-of-two chunk per position, why its two loops visit exactly the right chunks, and how to use it for range sums and range additions.

=== primer | How do you count inversions and "smaller after self" with a Fenwick tree? | 15 min
goal: Count, for every element, how many earlier or later elements are smaller or larger, and find the k-th smallest of a changing multiset, in O(log n) per element
tag: rangeq-bitcount | Fenwick tree over values (counting)
link: USACO Guide: inversion counting and the k-th element | https://usaco.guide/gold/PURS#inversion-counting | 10 min: 'Inversion Counting', then 'Finding the K-th Element' under the binary indexed tree section
practice: 1395, 315, 1649

> [!key]
> Index a Fenwick tree **by value** instead of by position and it becomes a live histogram: `add(v, 1)` inserts v, and `prefix(v)` counts the inserted values that are at most v. Scan the array once; before inserting each element, ask the histogram about the elements already inserted (the ones to its left, or to its right if you scan backwards). Each element costs one query and one update, O(n log m) in all, with m the number of distinct values.

## Intuition

Picture people arriving one at a time and joining a queue sorted by height. Each newcomer wants to know how many people already in the room are taller. Counting them one by one is O(n) per person, O(n^2) in all. A tally board with one row per height, plus running totals by height range, answers "how many are at most my height?" in O(log n), and "taller" is everyone seen minus that. The Fenwick tree is that tally board.

## How it works

### A histogram you can query

Give every distinct value a **rank** from 1 to m in sorted order (equal values share a rank). With a Fenwick tree of size m:

- `add(rank, 1)` inserts a value; `add(rank, -1)` removes one.
- `prefix(rank)` counts inserted values that are at most this value.
- `prefix(rank - 1)` counts values strictly smaller.
- `seen - prefix(rank)` counts values strictly greater, where `seen` is how many you have inserted.

Ranks also handle negative numbers and values up to 10^9: `{v: r for r, v in enumerate(sorted(set(a)), 1)}`. The coordinate compression card covers the harder cases, such as query bounds that are not in the data.

### Inversions, scanning left to right

An inversion is a pair i < j with `a[i] > a[j]`. Scan left to right; at element x, the elements already inserted are exactly those to its left, and `seen - prefix(rank[x])` of them are greater. Add that to the total, then insert x.

### Smaller after self, scanning right to left

Reverse the scan and the inserted elements are those to the right: `prefix(rank[x] - 1)` counts the strictly smaller ones.

### Order statistics: the k-th smallest

With non-negative counts you can also ask "which value is the k-th smallest?" in O(log n) by descending through the tree's powers of two: from position 0, try jumping by the largest power of two; if the chunk you would skip holds fewer than k elements, skip it and subtract its count from k; otherwise stay. This works because when `pos` is a multiple of `2 * step`, node `pos + step` holds exactly the positions `pos + 1` to `pos + step`. It turns the tree into a rank-and-select structure for leaderboards and running medians.

### Fixing the middle

Some problems count triples, such as increasing triples `i < j < k`. Fix the middle element j: the number of triples through j is (smaller values on the left) x (larger values on the right), and two histograms, one for each side, give both counts in O(log n).

## Cost

Sorting for ranks is O(n log n). The scan does n queries and n updates on a tree of size m <= n: O(n log m). Memory is O(m). For n = 10^5 that is about 2 x 17 loop steps per element, a few million steps, a fraction of a second in Python. Merge sort can also count inversions in O(n log n) (the recursion module shows it), but it works only offline and only for this one question; the histogram also answers questions while elements arrive.

## When to use it

| Approach | Cost | Use when |
|---|---|---|
| Compare all pairs | O(n^2) | n up to a few thousand; also your stress-test oracle |
| Merge sort counting | O(n log n) | Offline inversion counts only |
| Fenwick histogram | O(n log n) | Counts before or after each element, online inserts and deletes, k-th smallest |
| `sortedcontainers.SortedList` | about O(log n) per operation | Arbitrary keys, no rank mapping, fewer lines |

Recognise it by phrases such as "how many earlier elements are greater", "for each element, the number of smaller ones to its right", "cost depends on how many inserted values are smaller", or "rank of this score".

## Worked trace

```steps
Scan `[3, 1, 4, 1, 5, 2]` left to right. The Fenwick tree is a histogram over values 1..5 (ranks equal values here); it starts empty
    a         3   1   4   1   5   2
    value     1   2   3   4   5
    count     0   0   0   0   0
    inversions 0
---
x = 3: 0 seen so far, `prefix(3) = 0` of them are <= 3, so 0 earlier values are greater; then `add(3, 1)`
    a         {{3}}   1   4   1   5   2
    value     1   2   3   4   5
    count     0   0   {{1}}   0   0
    inversions 0
---
x = 1: 1 seen so far, `prefix(1) = 0` of them are <= 1, so 1 earlier value is greater; then `add(1, 1)`
    a         3   {{1}}   4   1   5   2
    value     1   2   3   4   5
    count     {{1}}   0   1   0   0
    inversions 1
---
x = 4: 2 seen so far, `prefix(4) = 2` of them are <= 4, so 0 earlier values are greater; then `add(4, 1)`
    a         3   1   {{4}}   1   5   2
    value     1   2   3   4   5
    count     1   0   1   {{1}}   0
    inversions 1
---
x = 1: 3 seen so far, `prefix(1) = 1` of them are <= 1, so 2 earlier values are greater; then `add(1, 1)`
    a         3   1   4   {{1}}   5   2
    value     1   2   3   4   5
    count     {{2}}   0   1   1   0
    inversions 3
---
x = 5: 4 seen so far, `prefix(5) = 4` of them are <= 5, so 0 earlier values are greater; then `add(5, 1)`
    a         3   1   4   1   {{5}}   2
    value     1   2   3   4   5
    count     2   0   1   1   {{1}}
    inversions 3
---
x = 2: 5 seen so far, `prefix(2) = 2` of them are <= 2, so 3 earlier values are greater; then `add(2, 1)`
    a         3   1   4   1   5   {{2}}
    value     1   2   3   4   5
    count     2   {{1}}   1   1   1
    inversions 6
---
Total 6 inversions: (3,1), (3,1), (4,1), (3,2), (4,2), (5,2). Each element cost one query and one update: O(n log n) instead of comparing all pairs
    a         3   1   4   1   5   2
    value     1   2   3   4   5
    count     2   1   1   1   1
    inversions 6
```

## Template

```python
def count_inversions(a):
    """Pairs i < j with a[i] > a[j], O(n log n)."""
    rank = {v: r for r, v in enumerate(sorted(set(a)), 1)}   # values -> 1..m
    f = Fenwick(len(rank))
    inversions = 0
    for seen, x in enumerate(a):
        inversions += seen - f.prefix(rank[x])   # earlier values greater than x
        f.add(rank[x], 1)
    return inversions


def smaller_after(a):
    """out[i] = number of j > i with a[j] < a[i], O(n log n)."""
    rank = {v: r for r, v in enumerate(sorted(set(a)), 1)}
    f = Fenwick(len(rank))
    out = [0] * len(a)
    for i in range(len(a) - 1, -1, -1):
        out[i] = f.prefix(rank[a[i]] - 1)         # strictly smaller, already to the right
        f.add(rank[a[i]], 1)
    return out


def kth(f, k):
    """Smallest position p with f.prefix(p) >= k (counts must be non-negative, 1 <= k <= total)."""
    pos = 0
    step = 1 << f.n.bit_length()                 # a power of two above n
    while step:
        nxt = pos + step
        if nxt <= f.n and f.tree[nxt] < k:       # the whole chunk pos+1..nxt is too small
            pos = nxt
            k -= f.tree[nxt]
        step >>= 1
    return pos + 1
```

These use the `Fenwick` class from the previous card.

## Pitfalls

- **Duplicates:** `prefix(rank)` includes values equal to x. Use `prefix(rank - 1)` for strictly smaller and `seen - prefix(rank)` for strictly greater, and decide which one the problem means.
- **Scan direction:** left to right counts elements before; right to left counts elements after.
- **Rank 0:** mapping the smallest value to 0 sends `add` into an endless loop; ranks start at 1.
- **`kth` on negative counts** or with k larger than the total returns nonsense; check `1 <= k <= total` first.
- **Large answers:** the inversion count of n = 10^5 elements can reach about 5 x 10^9; fine in Python, but use 64-bit integers in C++ and Java, and apply the modulus when the problem asks for one.

## Check yourself

Q: What does `smaller_after([4, 1, 3, 1, 2])` return?
A: `[4, 0, 2, 0, 0]`. The 4 has 1, 3, 1, 2 to its right, all smaller; the first 1 has nothing strictly smaller to its right; the 3 has 1 and 2; the last two have nothing smaller after them.

Q: Why does "strictly smaller" use `prefix(rank - 1)` but "strictly greater" use `seen - prefix(rank)`?
A: `prefix(rank)` counts inserted values at most x, equal ones included. Stopping one rank lower excludes the equal values, giving strictly smaller. Subtracting `prefix(rank)` from everything seen removes all values at most x, leaving strictly greater.

Q: For 1,000 distinct ratings you must count increasing or decreasing triples. Is a Fenwick tree worth writing?
A: Not necessarily: fixing the middle and counting both sides with plain loops is O(n^2), about 10^6 steps, which is fast and simpler. With n = 10^5 the same counts need two Fenwick histograms (left and right of the middle) to stay at O(n log n).

## Lab

- **1395 Count Number of Teams:** solve it first in O(n^2) by fixing the middle soldier, then with two Fenwick histograms (insert into `left` as you pass, remove from `right`). Expected: for ratings `[3, 6, 1, 5, 7, 2]` both versions return 4 (three increasing teams and one decreasing), and they agree on random tests.
- **315 Count of Smaller Numbers After Self:** rank the values (they can be negative), then scan right to left with `smaller_after`. Expected: `[2, 0, 3, 1]` gives `[2, 0, 1, 0]`; O(n log n) time.
- **1649 Create Sorted Array through Instructions:** insert values into a histogram over 1..max; each insertion costs `min(smaller, greater)` where smaller is `prefix(v - 1)` and greater is `inserted - prefix(v)`. Expected: `[2, 6, 3, 6, 1, 4]` costs 3 in total (the 3 costs 1 and the final 4 costs 2).

> [!know]
> You now know how to turn "how many earlier or later elements are smaller or larger" into one Fenwick query per element, and how to find the k-th smallest by descending through the tree.

=== primer | When do you need coordinate compression, and how do you do it safely? | 12 min
goal: Map huge or negative values to small consecutive indices without changing any order-based answer, including query bounds that are not in the data and interval end points
tag: rangeq-compress | Coordinate compression and relabelling
link: USACO Guide: coordinate compression | https://usaco.guide/silver/sorting-custom#coordinate-compression | 8 min: the 'Coordinate Compression' section and its example of mapping large values to consecutive indices
practice: 327, 2179

> [!key]
> Fenwick and segment trees are indexed by position, so values up to 10^9 (or negative ones) cannot be used directly. If only the **order** of the values matters, replace each value by its index in the sorted list of distinct values: n values become indices 0 to m - 1 with every comparison preserved. Look values up with `bisect` so that query bounds absent from the data still land in the right place.

## Intuition

A theatre has seats numbered up to a million but only five guests tonight. To ask "how many guests sit between seat 0 and seat 100?", you do not need a million-seat chart: list the occupied seat numbers in order and number them 1 to 5. Anything that depends only on who sits to the left of whom is unchanged. What you must not do is forget the original numbers when distances matter: "how many empty seats lie between guests 2 and 3" needs the real seat numbers.

## How it works

### Points

Collect every value that will be stored, sort and de-duplicate: `xs = sorted(set(values))`. The value `xs[k]` gets index k (Fenwick position k + 1). The mapping is a bijection that preserves order, so "smaller", "greater" and "between" answers are identical in either system. A dict `{v: k}` is O(1) per lookup; `bisect_left(xs, v)` is O(log m) but also works for values that are not in `xs`.

### Query bounds that are not data values

To count stored values in `[lo, hi]`, you need the positions of lo and hi even if neither was ever stored. `bisect_left(xs, lo)` is the number of distinct stored values below lo, and `bisect_right(xs, hi)` the number at most hi, so the count is `prefix(bisect_right(xs, hi)) - prefix(bisect_left(xs, lo))`. The alternative is to add every query bound to the universe before compressing; that also works, at the cost of a bigger tree.

### Intervals

For intervals, compress the **end points**. With sorted distinct end points `xs`, elementary segment k is the half-open piece `[xs[k], xs[k + 1])` and it has a real length `xs[k + 1] - xs[k]`. A segment tree over the m - 1 elementary segments can then track coverage or heights, multiplying by those lengths when an area or a total length is needed. Half-open intervals matter here: two squares that touch at x = 3 share an end point but no elementary segment, so they do not overlap.

### Relabelling

Sometimes the right coordinates are not the values at all. If two permutations must agree on the order of three elements, relabel every element by its position in the second permutation; walking the first permutation then turns the question into "count increasing triples" in a single array.

### Offline only

Compression needs every value (and every query bound, if you add them to the universe) before you start. When values arrive online and cannot be known in advance, use `sortedcontainers.SortedList`, a balanced tree, or a pointer-based segment tree over the full range that creates nodes only where values land.

## Cost

Sorting is O(n log n) and building the dict is O(n); each lookup afterwards is O(1) with the dict or O(log m) with `bisect`. The payoff is the tree size: m <= n slots instead of the value range (10^9), which is the difference between a few megabytes and an impossible allocation.

## When to use it

Use it when values are huge, negative or real-valued but only their order matters, and when every value is known before the queries start. Do not bother when values are already small non-negative integers (an offset is enough), and do not use it alone when distances matter: keep the original coordinates for lengths and areas.

## Worked trace

```steps
The values, all known before any query (offline). Used directly as indices they would need a Fenwick tree with a million slots and negative positions
    values  [1000000, -5, 42, 42, 7]
---
Sort and de-duplicate: `xs = [-5, 7, 42, 1000000]`. Value `xs[k]` lives at Fenwick position k + 1; order is preserved
    k                0        1        2        3
    xs              -5        7       42  1000000
    position         1        2        3        4
---
Insert all five with `add(bisect_left(xs, v) + 1)`: the tree now counts values per position
    xs              -5        7       42  1000000
    position         1        2        3        4
    count            1        1        2        1
---
`count_between(0, 100)`: neither 0 nor 100 is in xs, so bisect instead of a dict lookup. `bisect_left(xs, 0) = 1` positions hold values below 0; `bisect_right(xs, 100) = 3` hold values <= 100
    xs              -5        {{7}}       {{42}}  1000000
    position         1        2        3        4
    count            1        {{1}}        {{2}}        1
---
`prefix(3) - prefix(1) = 4 - 1 = 3`: the values 7, 42 and 42
    xs              -5        {{7}}       {{42}}  1000000
    count            1        {{1}}        {{2}}        1
    answer 3
```

## Template

```python
from bisect import bisect_left, bisect_right


class ValueCounter:
    """Multiset over a universe of values known in advance (offline):
    add(v) and count of stored values in [lo, hi], O(log m) each, where m = distinct values."""

    def __init__(self, universe):
        self.xs = sorted(set(universe))
        self.f = Fenwick(len(self.xs))

    def add(self, v, times=1):
        self.f.add(bisect_left(self.xs, v) + 1, times)    # v must be in the universe

    def count_between(self, lo, hi):
        """How many stored values v satisfy lo <= v <= hi; lo and hi need not be in the universe."""
        if lo > hi:
            return 0
        return self.f.prefix(bisect_right(self.xs, hi)) - self.f.prefix(bisect_left(self.xs, lo))
```

It reuses the `Fenwick` class from the Fenwick card.

## Pitfalls

- **`KeyError` on query bounds:** a dict only knows stored values; use `bisect` for bounds.
- **`bisect_left` versus `bisect_right`:** for an inclusive upper bound use `bisect_right(xs, hi)`; for an inclusive lower bound use `bisect_left(xs, lo)`. Swapping them drops or double-counts values equal to the bounds.
- **Forgetting `set`:** duplicates in `xs` give equal values different indices and break equality.
- **Off by one with Fenwick positions:** compressed indices start at 0, Fenwick positions at 1.
- **Lost lengths:** after compressing intervals, store `xs[k + 1] - xs[k]` per elementary segment, or areas come out as counts.

## Check yourself

Q: With `xs = [-5, 7, 42, 1000000]` and all five values `[1000000, -5, 42, 42, 7]` inserted, what does `count_between(-10, 10)` return, and which Fenwick prefixes does it read?
A: 2 (the values -5 and 7). `bisect_left(xs, -10)` is 0 and `bisect_right(xs, 10)` is 2, so it returns `prefix(2) - prefix(0) = 2 - 0`.

Q: Rectangles have x coordinates up to 10^9. After compressing the x end points to indices 0..m-1, what must you keep so that areas stay correct?
A: The width of each elementary segment, `xs[k + 1] - xs[k]`. The compressed indices preserve order but not distance, so any length or area must be computed from the original coordinates.

Q: Why must compression be offline, and what do you use when values arrive one at a time and cannot be known in advance?
A: The index of a value depends on how many distinct values are smaller, which a late arrival can change for everyone. Online, use a structure keyed by the values themselves: `SortedList`, a balanced tree, or a dynamic segment tree over the whole value range.

## Lab

- **327 Count of Range Sum (derive it):** a subarray sum is a difference of two prefix sums, so for each prefix you count earlier prefixes inside a window of values. Work out which window, compress every prefix sum, and use `count_between`. Expected: for `nums = [3, -1, 2]`, `lower = 1`, `upper = 3` the answer is 4 (`[3]`, `[3, -1]`, `[-1, 2]` and `[2]`); O(n log n), checked against an O(n^2) brute force.
- **2179 Count Good Triplets in an Array:** relabel each value by its position in `nums2`, then count increasing triples in the relabelled `nums1` by fixing the middle (smaller before it from a Fenwick histogram, larger after it by subtraction). Expected: `nums1 = [3, 0, 4, 1, 2]` and `nums2 = [0, 3, 1, 4, 2]` give 4.

> [!know]
> You now know how to compress huge values into small indices without changing any order-based answer, and how to handle query bounds, intervals and relabelling safely.

=== primer | How does a segment tree answer any associative range query in O(log n)? | 18 min
goal: Build a segment tree for any associative operation, trace how a query splits into O(log n) stored nodes, and implement it both recursively and bottom-up
tag: rangeq-segtree | Segment tree
link: USACO Guide: segment tree implementations | https://usaco.guide/gold/PURS#dynamic-range-minimum-queries | 10 min: 'Dynamic Range Minimum Queries' with both the recursive and the iterative implementation
link: Algorithmica: bottom-up segment trees | https://en.algorithmica.org/hpc/data-structures/segment-trees/#bottom-up-implementation | 15 min: 'Bottom-up implementation', the same leaves-at-n layout as the template here (in C++); 'Comparisons' then shows how far array-based layouts outrun the pointer-based tree
practice: cses:1649, 2407

> [!key]
> A segment tree stores, for every node of a balanced binary split of the array, the combined value of its range: node 1 covers everything, and a node covering `[lo, hi)` has children covering `[lo, mid)` and `[mid, hi)`. A point update recomputes one leaf-to-root path; a range query uses the nodes that lie fully inside the range, and **at most four nodes per level** are visited. Any associative operation with an identity works: sum, min, max, gcd, or a custom tuple.

## Intuition

A knockout tournament is a segment tree for "who is best". Each match stores its winner, the final stores the champion. If one player's rating changes, only the matches on their path to the final are replayed: log2 n of them. To ask "who is best among players 3 to 11?", you do not replay anything: you combine the winners of a few whole sub-brackets that exactly cover players 3 to 11, plus a single player or two at the edges.

## How it works

### Shape and stored values

Node 1 covers `[0, n)`; node v covering `[lo, hi)` has children 2v and 2v + 1, split at `mid = (lo + hi) // 2`; leaves cover one element. Each node stores `op(left child, right child)`. The tree needs only two properties of `op`: it is **associative** (`op(op(x, y), z) == op(x, op(y, z))`, so any grouping of a range gives the same answer) and it has an **identity** e with `op(e, x) == x` (0 for sum, infinity for min, 0 for gcd). Commutativity is not needed if you keep left and right in order.

### Query: three cases per node

```python
def seg_build(a, t, node, lo, hi):
    """Fill t (size 4n) so that t[node] = sum of a[lo:hi]."""
    if hi - lo == 1:
        t[node] = a[lo]
        return
    mid = (lo + hi) // 2
    seg_build(a, t, 2 * node, lo, mid)
    seg_build(a, t, 2 * node + 1, mid, hi)
    t[node] = t[2 * node] + t[2 * node + 1]


def seg_query(t, node, lo, hi, l, r):
    """Sum of a[l:r] using node `node`, which covers [lo, hi)."""
    if r <= lo or hi <= l:           # disjoint: contributes nothing
        return 0
    if l <= lo and hi <= r:          # fully inside: use the stored answer
        return t[node]
    mid = (lo + hi) // 2             # partial overlap: ask both children
    return seg_query(t, 2 * node, lo, mid, l, r) + seg_query(t, 2 * node + 1, mid, hi, l, r)
```

### Why at most four nodes per level

A node is visited only if its parent was partial. A partial node must contain one of the query's two boundaries (l or r) strictly inside it, and on each level only one node contains a given boundary, so at most two nodes per level are partial. Their children, at most four, are the only nodes visited on the next level. With about log2 n levels, a query visits O(log n) nodes and uses at most two fully covered nodes per level.

### Update: one path

Change the leaf, then recompute each ancestor from its two children: log2 n + 1 nodes.

### Bottom-up layout

Put the leaves at `t[n:2n]`, so the parent of i is `i // 2` and the children of i are `2i` and `2i + 1`. A query starts at both ends, `l += n` and `r += n`, and climbs: whenever l is a right child it cannot be merged with its sibling into a parent that stays inside the range, so take it and step right; symmetrically for `r - 1`. It needs 2n slots instead of 4n, no recursion, and works for any n, not only powers of two, as long as the left and right partial results are combined in order.

### Richer nodes

Each node can hold a tuple combined by a custom function: (maximum, count of the maximum); (sum, best prefix, best suffix, best subarray) for range maximum-subarray queries; a (candidate, count) pair from the Boyer-Moore majority vote. If the combine is associative and O(1), every query and update stays O(log n).

## Cost

- **Build:** n - 1 combines, O(n).
- **Update:** one combine per level, about log2 n.
- **Query:** at most four visited nodes per level, O(log n).
- **Memory:** the recursive layout needs up to 4n slots (the last level of a tree over a non-power-of-two n is uneven); the bottom-up layout needs exactly 2n.
- **Python:** recursion costs a function call per visited node, so the recursive version is a few times slower than the bottom-up one, and both are slower than a Fenwick tree for sums (the lab measures it). Recursion depth is only about log2 n, so the recursion limit is never a problem.

## When to use it

Choose a segment tree when the operation has no inverse (min, max, gcd), when nodes need custom summaries, when you need "first index where the prefix reaches x" style descents, or when range updates follow (lazy propagation, a later card). For plain sums and counts, a Fenwick tree is shorter and faster; for static data, prefix sums or a sparse table win.

| Need | Fenwick | Segment tree | Sparse table |
|---|---|---|---|
| Range sum, point update | yes, fastest | yes | no |
| Range min or max, point update | no | yes | no |
| Range min or max, static | no | O(log n) | O(1) |
| Custom associative summary | no | yes | only if idempotent |

## Worked trace

Query `sum(a[2:7])` on eight values. Marks: `~` partial, `+` fully inside (used), `x` disjoint.

```steps
A sum tree over `[5, 2, 9, -3, 6, 1, 4, 7]`. Each node shows the positions it covers and their sum; query `sum(a[2:7])`, positions 2-6
    depth 0                           0-7:31
    depth 1             0-3:13                      4-7:18
    depth 2      0-1:7         2-3:6         4-5:7         6-7:11
    depth 3     5      2      9     -3      6      1      4      7
---
The root (0-7) overlaps the query only partly (~): ask both children
    depth 0                          {{~0-7:31}}
    depth 1             0-3:13                      4-7:18
    depth 2      0-1:7         2-3:6         4-5:7         6-7:11
    depth 3     5      2      9     -3      6      1      4      7
---
0-3 is partial too. Its left child 0-1 is disjoint (x, contributes 0); its right child 2-3 lies inside (+): take its stored 6 and do not descend
    depth 0                          {{~0-7:31}}
    depth 1            {{~0-3:13}}                      4-7:18
    depth 2      {{x0-1:7}}        {{+2-3:6}}        4-5:7         6-7:11
    depth 3     5      2      9     -3      6      1      4      7
---
4-7 is partial: 4-5 lies inside, take 7; 6-7 is partial, so split it once more
    depth 0                          {{~0-7:31}}
    depth 1            {{~0-3:13}}                     {{~4-7:18}}
    depth 2      {{x0-1:7}}        {{+2-3:6}}        {{+4-5:7}}       {{~6-7:11}}
    depth 3     5      2      9     -3      6      1      4      7
---
Leaf 6 is inside: take 4; leaf 7 is disjoint. Answer 6 + 7 + 4 = 17 from three stored nodes. Only the nodes on the two boundary paths are ever partial
    depth 0                          {{~0-7:31}}
    depth 1            {{~0-3:13}}                     {{~4-7:18}}
    depth 2      {{x0-1:7}}        {{+2-3:6}}        {{+4-5:7}}       {{~6-7:11}}
    depth 3     5      2      9     -3      6      1     {{+4}}     {{x7}}
```

## Template

The bottom-up version is the one to reproduce from memory; it handles any associative operation.

```python
class SegTree:
    """Iterative (bottom-up) segment tree for any associative op with an identity.
    set(i, v) and query(l, r) = op over a[l:r], both O(log n). Leaves live at t[n:2n]."""

    def __init__(self, a, op, identity):
        self.n = len(a)
        self.op, self.e = op, identity
        self.t = [identity] * self.n + list(a)
        for i in range(self.n - 1, 0, -1):
            self.t[i] = op(self.t[2 * i], self.t[2 * i + 1])

    def set(self, i, v):
        i += self.n
        self.t[i] = v
        while i > 1:
            i //= 2
            self.t[i] = self.op(self.t[2 * i], self.t[2 * i + 1])

    def query(self, l, r):
        left, right = self.e, self.e      # results from the left and right edges, kept in order
        l += self.n
        r += self.n
        while l < r:
            if l & 1:                     # l is a right child: take it, step past it
                left = self.op(left, self.t[l])
                l += 1
            if r & 1:                     # r is a right child, so r - 1 is inside: take it
                r -= 1
                right = self.op(self.t[r], right)
            l //= 2
            r //= 2
        return self.op(left, right)
```

Usage: `SegTree(a, min, float("inf"))`, `SegTree(a, max, float("-inf"))`, `SegTree(a, math.gcd, 0)`, `SegTree(a, operator.add, 0)`.

## Pitfalls

- **Wrong identity:** 0 as the identity for min makes every query over positive numbers return 0.
- **Non-associative combine:** averages are not associative; store (sum, count) and divide at the end.
- **Order for non-commutative operations:** keep separate left and right accumulators, as the template does.
- **Array size:** the recursive layout needs 4n slots; 2n overflows for some n.
- **Inclusive inputs:** judges usually give 1-indexed inclusive `a..b`; that is `query(a - 1, b)`.

## Check yourself

Q: In the trace's tree over `[5, 2, 9, -3, 6, 1, 4, 7]`, which stored nodes does a query for positions 1 to 4 (`sum(a[1:5])`) use, and what is the answer?
A: Leaf 1 (value 2), the node for positions 2-3 (value 6) and leaf 4 (value 6): 14. The root, 0-3, 0-1, 4-7 and 4-5 are partial; leaf 0, leaf 5 and the node 6-7 are disjoint.

Q: Why can a query never have more than two partial nodes on one level?
A: A node is partial only if one of the query's boundaries falls strictly inside its range. There are two boundaries, and on any level each position belongs to exactly one node, so at most two nodes per level are partial, and only their children are visited next.

Q: Range maximum with point updates: Fenwick tree or segment tree?
A: Segment tree. A Fenwick tree answers ranges by subtracting prefixes, and maximum has no inverse; a prefix-maximum Fenwick tree also cannot handle a value that decreases.

Q: A teammate builds `SegTree(a, min, 0)` over positive prices and every query returns 0. What is wrong?
A: The identity for min must be larger than every value, such as `float("inf")`; 0 wins every comparison, so the padding and empty partial results pollute the answers.

## Lab

- **cses:1649 Dynamic Range Minimum Queries:** `SegTree(values, min, float("inf"))`; a "set position k to u" update is `set(k - 1, u)` and a query `a b` is `query(a - 1, b)`. Expected: for `[3, 8, 4, 6, 5]`, the minimum of positions 2 to 4 is 4; after setting position 3 to 9 it is 6.
- **2407 Longest Increasing Subsequence II (derive it):** the usual LIS DP is indexed by position, but here the condition is on values (each step up by at most k). Index a max segment tree by value, so `dp[v] = 1 + max(dp[v - k .. v - 1])` is one range query and one point update. Expected: `[4, 1, 6, 2, 7, 3, 8]` with k = 2 gives 4 (4, 6, 7, 8); O(n log M) for values up to M.

> [!know]
> You now know how a segment tree splits any range into O(log n) stored nodes, how to write it bottom-up for any associative operation, and when it beats a Fenwick tree.

=== lab | Range query benchmark: naive, prefix rebuild, Fenwick and segment tree | 45 min
goal: Stress-test four range-sum structures against each other on mixed workloads, then measure where each one wins in Python and explain the crossovers
link: USACO Guide: iterative segment tree | https://usaco.guide/gold/PURS#iterative-implementation | 5 min: the iterative implementation, to compare line by line with the SegTree template you are benchmarking

You will run the same random sequences of point updates and range sums through a naive list, a prefix table that rebuilds after each update, a Fenwick tree and a bottom-up segment tree, check that all four always agree, and time them for array sizes from 100 to 100,000 and update shares from 0% to 90%.

## Setup

- Python 3.10+, no packages needed.
- Copy the `Fenwick` class from the Fenwick card and the `SegTree` class from the segment tree card into a file `rq.py` in the same folder.

## Steps

1. Save this as `bench.py` next to `rq.py`:

```python
import operator
import random
import time
from itertools import accumulate

from rq import Fenwick, SegTree


class Naive:
    def __init__(self, a):
        self.a = list(a)

    def update(self, i, v):
        self.a[i] = v

    def query(self, l, r):
        return sum(self.a[l:r])


class PrefixRebuild:
    def __init__(self, a):
        self.a = list(a)
        self.pre = list(accumulate(self.a, initial=0))

    def update(self, i, v):
        self.a[i] = v
        self.pre[i:] = accumulate(self.a[i:], initial=self.pre[i])

    def query(self, l, r):
        return self.pre[r] - self.pre[l]


class Fen:
    def __init__(self, a):
        self.a = list(a)
        self.f = Fenwick.from_list(a)

    def update(self, i, v):
        self.f.add(i + 1, v - self.a[i])
        self.a[i] = v

    def query(self, l, r):
        return self.f.range_sum(l, r)


class Seg:
    def __init__(self, a):
        self.s = SegTree(a, operator.add, 0)

    def update(self, i, v):
        self.s.set(i, v)

    def query(self, l, r):
        return self.s.query(l, r)


def workload(n, q, p_update, seed):
    rng = random.Random(seed)
    ops = []
    for _ in range(q):
        if rng.random() < p_update:
            ops.append((0, rng.randrange(n), rng.randint(-1000, 1000)))
        else:
            l, r = sorted((rng.randint(0, n), rng.randint(0, n)))
            ops.append((1, l, r))
    return ops


def run(cls, a, ops):
    s = cls(a)
    out = []
    t = time.perf_counter()
    for kind, x, y in ops:
        if kind:
            out.append(s.query(x, y))
        else:
            s.update(x, y)
    return out, (time.perf_counter() - t) / len(ops) * 1e6


print(f"{'n':>7} {'updates':>7} | {'naive':>8} {'prefix':>8} {'fenwick':>8} {'segtree':>8}   (microseconds per operation)")
for n in (100, 1_000, 10_000, 100_000):
    a = [random.randint(-1000, 1000) for _ in range(n)]
    for p in (0.0, 0.1, 0.5, 0.9):
        ops = workload(n, 3000, p, seed=n + int(p * 100))
        results, times = None, []
        for cls in (Naive, PrefixRebuild, Fen, Seg):
            out, us = run(cls, a, ops)
            if results is None:
                results = out
            assert out == results, cls.__name__      # the stress test: all four must agree
            times.append(us)
        print(f"{n:>7} {p:>7.0%} | " + " ".join(f"{t:>8.1f}" for t in times))
```

2. Before running it, write down your prediction for n = 100,000 with 50% updates: which structure is fastest, and roughly how many microseconds per operation does the naive list need?
3. Run `python bench.py` (about a minute). If an `assert` fires, one of your classes is wrong: shrink n to 10 and print the operations up to the first mismatch.
4. Plant a bug to see the stress test work: in `Fen.update`, forget the `- self.a[i]`. Run again and note how quickly the assertion fails, then undo it.
5. Add a fifth column for `SqrtBlocks` from the first card of this module and rerun. Where does it sit between the naive list and the trees?
6. For each update share, find the smallest n at which the Fenwick tree beats the naive list, and explain the crossover from what each operation costs and what runs in C.

## What you should see

Exact numbers vary by machine and from run to run (rerun if one cell looks odd); the shape does not.

- **All four agree** on every operation. The planted bug fails within the first few updates.
- **With 0% updates** the prefix table wins at every size (under a microsecond per query): with no updates there is nothing to rebuild. The naive list grows linearly with n, to over a millisecond per query at n = 100,000.
- **At n = 100** everything costs a few microseconds and the naive list is often the fastest, because `sum(a[l:r])` over a few dozen numbers runs in C while the trees run Python loops.
- **The crossover with the naive list depends on the mix.** With mostly queries, the Fenwick tree overtakes the naive list around n = 1,000. With 90% updates, which cost the naive list O(1), the naive list holds out until about n = 10,000. At n = 100,000 the Fenwick tree is roughly 30 to 300 times faster.
- **The prefix rebuild collapses as soon as updates appear:** tens of microseconds per operation at n = 10,000 with 10% updates, and several milliseconds at n = 100,000 with 50% or more. Its rebuild runs in C, which is why it survives longer than a pure-Python O(n) loop would.
- **The Fenwick tree** stays at a few microseconds (roughly 2 to 10) at every size and mix: O(log n) with a tiny constant.
- **The segment tree** also stays flat, usually somewhat slower than the Fenwick tree for sums (up to about twice as slow). Pay that price when you need min, max or custom summaries.
- **The square-root blocks** land between the naive list and the trees at large n: around 100 microseconds per query-heavy operation at n = 100,000, as the first card predicted.

=== primer | How does lazy propagation make range updates O(log n)? | 18 min
goal: Add pending updates to a segment tree so that "add v to a whole range" and "sum of a range" both cost O(log n), and adapt the idea to assignment and coverage counts
tag: rangeq-lazy | Lazy propagation
link: cp-algorithms: lazy propagation | https://cp-algorithms.com/data_structures/segment_tree.html#range-updates-lazy-propagation | 15 min: 'Addition on segments', 'Assignment on segments' and 'Adding on segments, querying for maximum'
link: USACO Guide: lazy segment tree | https://usaco.guide/plat/RURQ#lazy-segment-tree | 10 min: the lazy segment tree explanation, then 'BIT Revisited' for range add with range sum using two Fenwick trees
practice: 699, 850

> [!key]
> This card is optional, even within an optional module. A range update would touch O(n) leaves, so do not touch them: apply it to the **O(log n) nodes that exactly cover the range**, fix their stored totals at once, and leave a **pending note** saying "my children have not received this yet". Before any later operation looks inside a node, it **pushes** the note down one level. Each operation does O(1) extra work per visited node, so updates and queries both stay O(log n).

## Intuition

Head office announces "everyone in the sales department gets a 5% raise". The department head updates the department's salary total immediately and writes a sticky note, "+5% for everyone, not yet passed on", instead of visiting every desk. If someone later asks for the payroll of one team inside sales, the head first hands the note to the team leads (who update their own totals and keep the note for their teams), and only then answers. Questions about the whole department never needed the note to move at all.

## How it works

### Two arrays and one invariant

Keep `total[node]` and `pending[node]`. The invariant: `total[node]` is the true sum of the node's range, counting every update applied at that node or above it; `pending[node]` is an addition that the node's children have not yet received. Leaves can carry a note too; it is simply never pushed.

### Apply: O(1) on one node

`_apply(node, v)` adds v to every element under the node without visiting them: `total += v x (number of elements)` and `pending += v`. This works because a range addition changes a sum by v times the length. Any update type works the same way if you can (1) recompute a node's summary from its old summary, the update and the length, and (2) compose two pending updates into one.

### Push: before looking inside

`_push(node)` applies the node's pending value to both children and clears it. Every operation that descends into a node's children calls it first, so the children's totals are correct by the time anyone reads them.

### Update and query share one decomposition

Both walk the same three cases as an ordinary segment tree query: disjoint, return; fully inside, apply (update) or return the total (query) and stop; partial, push, recurse into both children, and for an update recombine `total[node]` from the children afterwards.

### Other update types

- **Assignment** ("set every value in the range to x"): the note is "assigned x, or nothing"; a later assignment replaces an earlier one, and the total becomes x times the length.
- **Add with range maximum:** the maximum also shifts by v, so `best += v` and `pending += v`.
- **Flip a 0/1 range:** ones become length minus ones; two flips cancel.
- **Coverage without pushing:** for the union of rectangles, a sweep adds +1 to a y-range when a rectangle starts and -1 when it ends. Each node keeps a cover count and the covered length (its full length if the count is positive, otherwise the sum of its children). Because every -1 exactly matches an earlier +1 on the same nodes, nothing ever needs to be pushed, and the root's covered length is the answer. This is the idea behind Bentley's 1977 sweep-line algorithm for the area of a union of rectangles (Klee's measure problem in two dimensions), which runs in O(n log n).

## Cost

An update or a query visits the same nodes as an ordinary segment tree query, at most four per level, and does O(1) extra work (one push) at each: O(log n) per operation. Memory is two arrays of 4n. In Python the constant is large (recursion plus two arrays), so when the operations allow it, simpler structures are faster: a Fenwick tree over differences for range add with point reads, two Fenwick trees for range add with range sums, and a plain difference array when all updates come before all reads.

## When to use it

| Updates | Queries | Use |
|---|---|---|
| Range add, all before any read | Read everything once | Difference array |
| Range add | Point value | Fenwick tree over differences |
| Range add | Range sum | Two Fenwick trees, or a lazy segment tree |
| Range add or assign | Range min or max | Lazy segment tree |
| Matched +1 and -1 on ranges | Total covered length | Cover-count segment tree (no push) |

## Worked trace

Eight 1s; add 5 to positions 0-3, then ask for the value at position 2.

```steps
Eight 1s. Each node shows `positions:total`, and `(+v)` when it holds a pending add its children have not received
    depth 0                           0-7:8
    depth 1             0-3:4                       4-7:4
    depth 2      0-1:2         2-3:2         4-5:2         6-7:2
    depth 3     1      1      1      1      1      1      1      1
---
`range_add(0, 4, +5)`: the root is partial; its child 0-3 is fully covered, so `_apply` sets its total to 4 + 5 x 4 = 24 and records pending +5, then stops. The root is recombined: 24 + 4 = 28
    depth 0                           {{0-7:28}}
    depth 1           {{0-3:24(+5)}}                    4-7:4
    depth 2      0-1:2         2-3:2         4-5:2         6-7:2
    depth 3     1      1      1      1      1      1      1      1
---
Below 0-3 every node is now stale (2 instead of 12, 1 instead of 6). That is the point: the update touched O(log n) nodes, not the four elements, and the pending note makes the stale values recoverable
    depth 0                           0-7:28
    depth 1           0-3:24(+5)                    4-7:4
    depth 2      {{0-1:2}}         {{2-3:2}}         4-5:2         6-7:2
    depth 3     {{1}}      {{1}}      {{1}}      {{1}}      1      1      1      1
---
`range_sum(2, 3)` reaches 0-3, which is only partly inside the query, so it must look at the children: `_push` first hands +5 to both (total += 5 x 2 = 12 each, pending +5) and clears its own note
    depth 0                           0-7:28
    depth 1             {{0-3:24}}                      4-7:4
    depth 2    {{0-1:12(+5)}}    {{2-3:12(+5)}}      4-5:2         6-7:2
    depth 3     1      1      1      1      1      1      1      1
---
Descend into 2-3: partial again, so push again: leaves 2 and 3 become 6 with pending +5 (a note on a leaf is harmless; it is never pushed further)
    depth 0                           0-7:28
    depth 1             0-3:24                      4-7:4
    depth 2    0-1:12(+5)      {{2-3:12}}        4-5:2         6-7:2
    depth 3     1      1    {{6(+5)}}  {{6(+5)}}    1      1      1      1
---
Leaf 2 is inside the query: return 6 = 1 + 5. Node 0-1 still carries +5 for its children; it moves only if a later operation needs to look inside 0-1
    depth 0                           0-7:28
    depth 1             0-3:24                      4-7:4
    depth 2    {{0-1:12(+5)}}      2-3:12        4-5:2         6-7:2
    depth 3     1      1    {{6(+5)}}  6(+5)    1      1      1      1
```

## Template

```python
class LazySegTree:
    """Range add and range sum on a[0:n], O(log n) per operation.
    Invariant: total[node] is correct for its whole range, including every add recorded at
    the node or above; pending[node] is an add its children have not received yet."""

    def __init__(self, a):
        self.n = len(a)
        self.total = [0] * (4 * max(1, self.n))
        self.pending = [0] * (4 * max(1, self.n))
        if self.n:
            self._build(1, 0, self.n, a)

    def _build(self, node, lo, hi, a):
        if hi - lo == 1:
            self.total[node] = a[lo]
            return
        mid = (lo + hi) // 2
        self._build(2 * node, lo, mid, a)
        self._build(2 * node + 1, mid, hi, a)
        self.total[node] = self.total[2 * node] + self.total[2 * node + 1]

    def _apply(self, node, lo, hi, v):
        """Add v to every element under node, in O(1): fix the total, remember the debt."""
        self.total[node] += v * (hi - lo)
        self.pending[node] += v

    def _push(self, node, lo, hi):
        """Hand the pending add down to both children before looking inside node."""
        if self.pending[node]:
            mid = (lo + hi) // 2
            self._apply(2 * node, lo, mid, self.pending[node])
            self._apply(2 * node + 1, mid, hi, self.pending[node])
            self.pending[node] = 0

    def range_add(self, l, r, v, node=1, lo=0, hi=None):
        """Add v to a[l:r]."""
        if hi is None:
            hi = self.n
        if r <= lo or hi <= l:
            return
        if l <= lo and hi <= r:
            self._apply(node, lo, hi, v)
            return
        self._push(node, lo, hi)
        mid = (lo + hi) // 2
        self.range_add(l, r, v, 2 * node, lo, mid)
        self.range_add(l, r, v, 2 * node + 1, mid, hi)
        self.total[node] = self.total[2 * node] + self.total[2 * node + 1]

    def range_sum(self, l, r, node=1, lo=0, hi=None):
        """Sum of a[l:r]."""
        if hi is None:
            hi = self.n
        if r <= lo or hi <= l:
            return 0
        if l <= lo and hi <= r:
            return self.total[node]
        self._push(node, lo, hi)
        mid = (lo + hi) // 2
        return (self.range_sum(l, r, 2 * node, lo, mid) +
                self.range_sum(l, r, 2 * node + 1, mid, hi))
```

## Pitfalls

- **Forgetting to push** before descending, in either the update or the query: children are read with stale totals.
- **Forgetting to recombine** `total[node]` after an update recurses: ancestors keep old totals.
- **Ignoring the length** in `_apply`: a node over 4 elements gains 4v, not v.
- **Composing notes in the wrong order:** with both assignment and addition, an assignment must wipe an older pending addition, while an addition after an assignment adds to the assigned value.
- **Using it when a Fenwick tree suffices:** a lazy tree is the slowest structure in this module per operation.

## Check yourself

Q: Starting from eight 1s, after `range_add(0, 4, 5)` and then `range_sum(2, 3)`, which nodes hold a pending +5?
A: The node for positions 0-1 and the leaves for positions 2 and 3. The note on 0-3 was pushed to 0-1 and 2-3 during the query, and the note on 2-3 was pushed again to its two leaves; 0-1 was never looked inside, so its note stays.

Q: The range in `range_add` can contain all n elements. Why is it still O(log n)?
A: It only visits the nodes of the range's decomposition and the partial nodes above them, at most four per level. A fully covered node absorbs the update in O(1) through `_apply` and is not descended into, so the cost does not depend on how many elements the range holds.

Q: A version of `range_add` applies the update to fully covered nodes but never runs `self.total[node] = ...` after recursing. What goes wrong?
A: Ancestors of the updated nodes keep their old totals. A later query that is answered from a high, fully covered node (the root for a whole-array sum, for example) misses the update, while queries that descend to the updated nodes see it, so answers become inconsistent.

## Lab

- **699 Falling Squares:** compress the x end points of all squares (left and left + side, half-open), then for each square read the maximum height over its span, add its side, and assign that height to the whole span: a lazy tree with range assignment and range maximum (an O(n^2) scan also passes for n up to 1,000, and makes a good oracle). Expected: squares `(left, side)` = `(1, 3)`, `(3, 2)`, `(6, 4)`, `(2, 1)` give tallest-stack heights `[3, 5, 5, 5]`.
- **850 Rectangle Area II:** sweep vertical edges left to right; each rectangle adds +1 to its compressed y-range at its left edge and -1 at its right edge; before each event, add covered length x distance moved. Use the cover-count tree (no push). Expected: rectangles `[0, 0, 2, 2]` and `[1, 1, 3, 3]` cover area 7; `[0, 0, 3, 1]` and `[1, 0, 2, 4]` cover 6.

> [!know]
> You now know how pending notes let a segment tree apply range updates in O(log n), when to push them, and which simpler structure to choose when the operations allow it.

=== primer | Where do range-query structures run in real systems? | 14 min
goal: Recognise block totals, cumulative counts and augmented trees in compression, databases, kernels and monitoring, and build a rank-and-select leaderboard on a Fenwick tree
link: Wikipedia: Fenwick tree, motivation | https://en.wikipedia.org/wiki/Fenwick_tree#Motivation | 5 min: 'Motivation', on cumulative frequencies in adaptive arithmetic coding, the problem the structure was published for
link: Linux kernel docs: augmented rbtrees | https://docs.kernel.org/core-api/rbtree.html#support-for-augmented-rbtrees | 10 min: 'Support for augmented rbtrees', which uses an interval tree (each node keeps the largest end point below it) as its worked example

> [!key]
> Production systems rarely ship a textbook segment tree, but they use the same three ideas constantly: **keep totals of blocks** so a long range reads a few numbers (rollups, spans, Fenwick nodes), **augment a balanced tree** with a summary of each subtree (largest end point, subtree size) so a search can skip whole subtrees, and **pay at write time to make reads cheap**. Recognising those ideas tells you which structure a feature needs.

## Intuition

A library catalogue does not count its books every time someone asks how many titles fall between "M" and "P": each shelf, aisle and floor has a running count on a card, and a correction updates one card per level. Every system below is a version of that card system, tuned to its own data and its own write-to-read ratio.

## How it works

### Arithmetic coding: the original Fenwick tree

An adaptive arithmetic coder encodes each symbol using the total frequency of all smaller symbols, then increments that symbol's count. With a plain array one of those two steps is O(alphabet size). Peter Fenwick's 1994 paper, "A new data structure for cumulative frequency tables", made both O(log n): the update is `add`, the cumulative frequency is `prefix`, and decoding, which must find the symbol whose cumulative range contains a given value, is the same downward search as the k-th element.

### Ranks in Redis sorted sets

ZRANK returns a member's position in score order in O(log N). Redis keeps a skip list in which every forward link stores its **span**, the number of elements it jumps over; a search adds the spans of the links it follows, exactly as a Fenwick query adds chunk totals. Leaderboards ("what is my rank?", "who is tenth?") are this problem; when scores are small integers, a Fenwick tree over score buckets answers both questions with less memory.

### Interval trees in the Linux kernel and in databases

`include/linux/interval_tree_generic.h` turns the kernel's red-black tree into an interval tree by storing, in every node, the largest end point in its subtree; an overlap search skips any subtree whose largest end lies before the query. `mm/interval_tree.c` instantiates it for memory mappings, so the kernel can find every mapping of a given file range. PostgreSQL's range types reach a similar goal with indexes: an exclusion constraint such as `EXCLUDE USING GIST (room WITH =, during WITH &&)` (with the btree_gist extension for the room column) makes the database reject overlapping bookings of the same room.

### Rollups in time-series storage

Graphite's Whisper format stores each metric in several archives, for example one point per minute for a day and one per hour for a year, with each coarser archive aggregated from the finer one at write time. A query uses the finest archive that covers the whole requested period, so a year-long graph reads thousands of hourly points instead of half a million minute samples. That is the sparse-table trade: extra storage and write work for cheap long-range reads.

### Sweep lines in geometry and design tools

The classic algorithm for the area of a union of rectangles, a question that comes up with chip layouts and map overlays, is Bentley's sweep line with a cover-count segment tree: the structure from the lazy propagation card.

## Cost

| System | Write | Read | Structure |
|---|---|---|---|
| Arithmetic coder | O(log n) count update | O(log n) cumulative count | Fenwick tree |
| Redis ZRANK | O(log N) expected insert | O(log N) expected rank | Skip list with spans |
| Kernel interval tree | O(log n) insert | O(log n + k) for k overlaps | Augmented red-black tree |
| Whisper rollups | one write per archive | points in one archive | Pre-aggregated blocks |

The pattern is constant: a write updates one summary per level, a read combines a logarithmic (or constant) number of summaries.

## When to use it

Reach for these ideas when a feature asks for ranks or percentiles over changing data (leaderboards, latency percentiles over buckets), overlap queries over intervals (calendars, memory maps, genome annotations), or fast aggregates over long time ranges (dashboards). Do not build a custom tree when the platform already has one: a sorted set in Redis, range types in PostgreSQL, or `sortedcontainers` in Python cover most needs with less risk.

## Worked trace

A leaderboard keeps a Fenwick tree over scores 0 to 7 (counts of players per score). Who is 4th highest? The 4th highest of 8 is the 5th lowest, and the k-th lowest comes from descending through the tree.

```steps
Scores 0..7 at positions 1..8; `count` is players per score, `tree` the Fenwick nodes. The 4th highest of 8 players is the 5th lowest, so call `kth(5)`
    score      0    1    2    3    4    5    6    7
    pos        1    2    3    4    5    6    7    8
    count      0    2    1    0    3    0    1    1
    tree       0    2    1    3    3    3    1    8
---
pos = 0, step = 16: position 16 is past n = 8, so skip this step
    score      0    1    2    3    4    5    6    7
    pos        1    2    3    4    5    6    7    8
    count      0    2    1    0    3    0    1    1
    tree       0    2    1    3    3    3    1    8
---
pos = 0, step = 8: `tree[8] = 8` counts positions 1-8, at least k = 5, so the answer is inside them: keep pos = 0
    score      0    1    2    3    4    5    6    7
    pos        1    2    3    4    5    6    7    8
    count      0    2    1    0    3    0    1    1
    tree       0    2    1    3    3    3    1    {{8}}
---
pos = 0, step = 4: `tree[4] = 3` counts positions 1-4, fewer than k = 5, so the answer lies beyond them: pos = 4, k = 5 - 3 = 2
    score      0    1    2    3    4    5    6    7
    pos        1    2    3    4    5    6    7    8
    count      0    2    1    0    3    0    1    1
    tree       0    2    1    {{3}}    3    3    1    8
---
pos = 4, step = 2: `tree[6] = 3` counts positions 5-6, at least k = 2, so the answer is inside them: keep pos = 4
    score      0    1    2    3    4    5    6    7
    pos        1    2    3    4    5    6    7    8
    count      0    2    1    0    3    0    1    1
    tree       0    2    1    3    3    {{3}}    1    8
---
pos = 4, step = 1: `tree[5] = 3` counts position 5, at least k = 2, so the answer is inside them: keep pos = 4
    score      0    1    2    3    4    5    6    7
    pos        1    2    3    4    5    6    7    8
    count      0    2    1    0    3    0    1    1
    tree       0    2    1    3    {{3}}    3    1    8
---
Steps exhausted: the answer is position pos + 1 = 5, score 4. Sorted high to low the scores are 7, 6, 4, 4, 4, 2, 1, 1: the 4th is 4. Four probes for n = 8
    score      0    1    2    3    {{4}}    5    6    7
    pos        1    2    3    4    {{5}}    6    7    8
    count      0    2    1    0    3    0    1    1
    tree       0    2    1    3    3    3    1    8
```

## Template

```python
class Leaderboard:
    """Scores are integers 0..max_score. rank(s) = 1 + number of players with a strictly higher score."""

    def __init__(self, max_score):
        self.m = max_score + 1
        self.f = Fenwick(self.m)
        self.players = 0

    def add(self, score):
        self.f.add(score + 1, 1)
        self.players += 1

    def remove(self, score):
        self.f.add(score + 1, -1)
        self.players -= 1

    def rank(self, score):
        return 1 + self.players - self.f.prefix(score + 1)

    def kth_highest(self, k):
        return kth(self.f, self.players - k + 1) - 1
```

It uses `Fenwick` from the Fenwick card and `kth` from the counting card. Every operation is O(log S) for S possible scores.

## Pitfalls

- **Unbounded or fractional scores:** a Fenwick tree needs a fixed range of integer positions; bucket the scores (and accept approximate ranks) or use a sorted container.
- **Ties:** decide whether equal scores share a rank (as here) or are broken by time, and encode the tie-break in the key if needed.
- **Stale summaries:** every system above updates its summaries on the write path; forgetting one level (a span, a rollup, a subtree maximum) silently corrupts reads.
- **Building what you can borrow:** a production feature should use Redis sorted sets, database range types or a tested library before a hand-written tree.

## Check yourself

Q: A game has 10 million players with integer scores from 0 to 1,000,000 and needs "what is my rank?" a thousand times a second. Fenwick tree over scores, sorted list of players, or Redis sorted set?
A: Any of the three can work; the choice is about where the data lives. A Fenwick tree over a million score buckets answers in about 20 steps and needs about a million counters (8 MB as 64-bit integers), ideal inside one process. A Redis sorted set gives O(log N) ranks shared by many servers, with persistence, and is the usual production answer. A Python list kept sorted with `bisect.insort` costs O(n) per insert, too slow at 10 million.

Q: Why does Whisper answer a year-long query from the hourly archive rather than adding up minute samples, and what does it give up?
A: The hourly archive already holds pre-aggregated blocks, so a year is about 8,800 points instead of 525,600. It gives up resolution (minute-level detail is gone for old data) and storage for the extra archives, and it does the aggregation work at write time.

## Lab

- **Build the leaderboard:** with `Leaderboard(1000)`, add scores 620, 880, 450, 880 and 710. Expected: `rank(700)` is 4, `rank(880)` is 1, `kth_highest(1)` is 880 and `kth_highest(3)` is 710. After `remove(880)`, `rank(700)` is 3 and `kth_highest(2)` is 710.
- **Stress it:** apply 1,000 random adds, removes and queries to the leaderboard and to a plain Python list (rank by counting higher scores, k-th by sorting). Expected: no mismatch, and the Fenwick version stays at microseconds per operation while the list version grows with the number of players.

> [!know]
> You now know how block totals, spans and augmented trees appear in real systems, and how to build a rank-and-select leaderboard on a Fenwick tree.

=== practice
- 307 core
  cue: An array receives point assignments interleaved with many range-sum questions, up to about 3 x 10^4 of each.
  hint: A prefix table answers sums instantly but rewrites O(n) entries per change. Which structure keeps both operations logarithmic, and what do you need to turn "set" into "add"?
  insight: Keep a Fenwick tree (built in O(n)) plus a copy of the values; update(i, v) adds v - nums[i] at position i + 1 and stores v; sumRange(l, r) is prefix(r + 1) - prefix(l). Both loops visit at most log2(n) + 1 nodes.
  cost: O(n) build, O(log n) per update and per query, O(n) space
  pattern: rangeq-fenwick
- cses:1647 core
  cue: A fixed array of up to 2 x 10^5 values and up to 2 x 10^5 range-minimum questions, with no changes.
  hint: The data never changes and min does not mind counting an element twice. What could you precompute for blocks whose lengths are powers of two?
  insight: Sparse table: table[j][i] is the minimum of the block of length 2^j starting at i, built level by level. A query [a, b] takes j = floor(log2(length)) and returns min(table[j][a], table[j][b - 2^j + 1]); the two blocks overlap but cover the range exactly.
  cost: O(n log n) build, O(1) per query, O(n log n) space
  pattern: rangeq-sparse
- cses:1649 core
  cue: Range-minimum questions on an array whose values are also reassigned one position at a time.
  hint: The previous problem's table breaks on updates, and minimum has no inverse, so prefix tricks fail. What tree stores a summary per range and repairs one path on a change?
  insight: Segment tree with min (identity infinity): a point update rewrites the leaf and recomputes its ancestors, and a query combines the O(log n) stored nodes that exactly cover the range.
  cost: O(n) build, O(log n) per update and per query, O(n) space
  pattern: rangeq-segtree
- cses:1651 core
  cue: Add a value to every element in a range, interleaved with questions about single elements.
  hint: In the prefix-sums module a range addition became two changes in a difference array. What do you need to read one element of the array back quickly when those changes keep coming?
  insight: Keep a Fenwick tree over the difference array: adding u to [a, b] is add(a, u) and add(b + 1, -u), and the current value at k is the initial value plus prefix(k). Both are O(log n).
  cost: O(log n) per operation, O(n) space
  pattern: rangeq-fenwick
- 1395 core
  cue: Count triples of soldiers whose ratings are strictly increasing or strictly decreasing in line order.
  hint: Fix the middle soldier. Which counts on each side determine how many triples pass through them?
  insight: For a middle j, the triples through it are less_left x greater_right + greater_left x less_right. Plain loops make that O(n^2), fine for n up to 1,000; two Fenwick histograms over rating ranks (left side filling, right side emptying) make it O(n log n).
  cost: O(n^2) simple or O(n log n) with Fenwick trees, O(n) space
  pattern: rangeq-bitcount
- 315 core
  cue: For each element, how many elements to its right are strictly smaller? Values may be negative.
  hint: Process the array from the right, so that "elements to my right" are exactly the ones you have already seen. What structure counts seen values below a threshold?
  insight: Rank the distinct values from 1, scan right to left, record prefix(rank - 1) of a Fenwick histogram as the answer for each element, then add 1 at its rank. Duplicates are handled by the strict rank - 1 bound. (Merge sort that counts during merging also works.)
  cost: O(n log n) time, O(n) space
  pattern: rangeq-bitcount
- 1649 core
  cue: Values are inserted one by one, and each insertion costs the smaller of "how many inserted values are smaller" and "how many are larger".
  hint: Both counts are questions about values inserted so far, by value, not by position. Values are at most 10^5.
  insight: Keep a Fenwick tree indexed by value: smaller = prefix(v - 1), larger = inserted - prefix(v); add min of the two to the total, then add(v, 1). Reduce the total modulo 10^9 + 7.
  cost: O(n log M) time for values up to M, O(M) space
  pattern: rangeq-bitcount
- 327 derive
  cue: Count subarrays whose sum lies between lower and upper, with negative values and n up to 10^5.
  hint: Every subarray sum is a difference of two prefix sums. For a fixed right end, which earlier prefix values give a sum inside [lower, upper]?
  insight: For prefix P[j], count earlier prefixes in [P[j] - upper, P[j] - lower], then insert P[j] (start with P = 0 inserted). Compress all prefix sums, and use bisect for the window bounds so they need not be stored values; a Fenwick tree counts each window in O(log n). Merge sort with two moving pointers is the classic alternative.
  cost: O(n log n) time, O(n) space
  pattern: rangeq-compress
- 2407 derive
  cue: Longest strictly increasing subsequence in which consecutive chosen values differ by at most k; values up to 10^5.
  hint: The ordinary LIS state is indexed by position. Index it by value instead: which earlier states can extend to value v?
  insight: Let best[v] be the longest valid subsequence ending with value v. Scanning left to right, best[v] = 1 + max(best[v - k .. v - 1]), a range maximum, followed by a point update at v. A max segment tree over values does both in O(log M).
  cost: O(n log M) time, O(M) space
  pattern: rangeq-segtree
- 699 stretch
  cue: Squares fall one after another onto a line and stack on whatever is below their span; report the tallest stack after each drop.
  hint: Each square lands at the highest point under its span and then raises that whole span. Which range operations does that need, and how do you shrink coordinates up to 10^8?
  insight: Compress all square edges as half-open intervals [left, left + side); for each square, h = range max over its span, then assign h + side to the whole span (lazy range assignment with range max), and keep a running global maximum. For n up to 1,000 an O(n^2) scan over earlier squares also passes and is a good oracle.
  cost: O(n log n) time, O(n) space
  pattern: rangeq-lazy
- 2179 stretch
  cue: Two permutations of 0..n-1; count triples whose relative order is the same in both.
  hint: Rename the values so that one of the permutations becomes 0, 1, 2, ... What does the condition become in the other?
  insight: Map each value to its position in nums2 and rewrite nums1 with those positions; good triplets are now increasing triples. For each middle element, smaller-before comes from a Fenwick histogram and larger-after follows by subtraction ((n - 1 - pos) - (i - smaller_before)); sum the products.
  cost: O(n log n) time, O(n) space
  pattern: rangeq-compress
- 850 stretch
  cue: Total area covered by a union of axis-aligned rectangles, with coordinates up to 10^9, modulo 10^9 + 7.
  hint: Sweep a vertical line from left to right. Between two consecutive events, the covered area is a covered length times a width. How do you maintain the covered length?
  insight: Each rectangle adds +1 to its compressed y-range at its left edge and -1 at its right edge. A segment tree over elementary y-segments keeps a cover count and covered length per node (full length if the count is positive, otherwise the children's sum); no push is needed because removals match additions. Add root length x dx before each event.
  cost: O(n log n) time, O(n) space
  pattern: rangeq-lazy
