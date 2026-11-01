---
key: sorting
name: Sorting, partitioning and selection
stage: order
summary: How merge sort, quicksort, quickselect and the linear-time sorts really work, what Python's and C++'s built-in sorts do underneath, and how to define custom orders safely.
why: Sorting is the most common preprocessing step in algorithms: once data is ordered, two pointers, binary search, grouping, sweeps and greedy choices become possible. The mechanics matter well beyond interviews. Merging is how databases sort data bigger than memory, partitioning is the heart of quickselect and of every production quicksort, counting and radix sorts beat n log n on small keys, and knowing that Python's sort is a stable, adaptive merge sort tells you when sorting again is nearly free and when a custom comparator is a bug waiting to happen.
outcomes:
- Implement merge sort, keep it stable, and count inversions during the merge
- Partition with Lomuto, Hoare and three-way schemes, state each invariant, and explain how random pivots and introsort avoid quicksort's O(n^2) worst case
- Select the k-th element in expected O(n) with quickselect, and choose between quickselect, heapq.nsmallest and sorting
- Prove the comparison lower bound and beat it with counting, radix and bucket sort when the keys allow
- Explain what CPython's list.sort does (runs, minrun, powersort merges, galloping) and what std::sort and std::stable_sort guarantee
- Write key functions and comparators that define a consistent order, including multi-key sorts
cues:
- Order would unlock a sweep, two pointers, binary search or a greedy choice
- "k-th largest", "top k" or a median of fixed data
- Keys are small integers or fixed-length digit strings
- An unusual ordering rule ("by frequency, then by value descending", "arrange to form the largest number")
- Counting pairs that are out of order, or pairs that satisfy a condition across two halves
traps:
- Assuming quicksort is O(n log n) on sorted or all-equal input with a fixed pivot or a two-way partition
- A comparator that is not a consistent order (not transitive, or true for equal items): garbage in Python, undefined behaviour in C++
- Taking from the right half on ties, which silently breaks stability that a later pass relies on
- Counting sort over a huge value range, where the count array costs more than sorting
- Sorting everything to answer a one-off k-th or top-k question
systems:
- CPython's list.sort is Timsort: it finds natural runs, extends short ones with binary insertion sort, merges them under the powersort policy (since Python 3.11) and gallops when one run keeps winning
- GCC's libstdc++ std::sort is introsort: median-of-three quicksort with a depth limit of 2 log2 n that falls back to heapsort, then one insertion sort pass over pieces of at most 16 elements
- PostgreSQL sorts that exceed work_mem write sorted runs to temporary files and merge them with a balanced k-way merge (polyphase merge was dropped in version 15)
- Rust's slice::sort is driftsort and sort_unstable is ipnsort; Go 1.19 rewrote package sort as pattern-defeating quicksort
further:
- Notes · 20 min | MIT 6.006 (Spring 2020), lecture 5: linear sorting and the comparison lower bound | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/78a3c3444de1ff837f81e52991c24a86_MIT6_006S20_lec5.pdf
- Article · 15 min | Sedgewick and Wayne, Algorithms 2.3: Quicksort (including entropy-optimal three-way sorting) | https://algs4.cs.princeton.edu/23quicksort/
- Source · 30 min | CPython Objects/listsort.txt: Tim Peters' design notes for list.sort | https://github.com/python/cpython/blob/main/Objects/listsort.txt
bank: sorting
---

=== recap | Merge sort: merging, stability and inversions | 12 min
goal: Write merge sort from memory, keep it stable, and count inversions or cross-half pairs during the merge
tag: sorting-merge | Merge sort and counting during the merge
link: Sedgewick and Wayne, Algorithms 2.2: Mergesort | https://algs4.cs.princeton.edu/22mergesort/ | 15 min: 'Top-down mergesort', 'Bottom-up mergesort' and the 'Improvements' list (insertion sort for small pieces, skip the merge when the halves are already in order)
practice: 493, hr:ctci-merge-sort

> [!key]
> Merge sort splits the list in half, sorts each half recursively and merges the two sorted halves in one linear pass. Each level of the recursion merges n elements in total and there are log2 n levels, so it is **O(n log n) in every case**, with O(n) extra memory. Taking from the left half on ties makes it **stable**, and the merge is the moment to count anything that compares the two halves, such as inversions.

## Internals

**The merge invariant.** `out` holds the i + j smallest elements of `left` and `right`, in order, and `left[i]`, `right[j]` are the smallest not yet taken. Taking the smaller of those two keeps the invariant. On a tie, take from the left: equal items then keep their original order, which is what **stable** means and what multi-pass sorts rely on.

**Cost.** T(n) = 2T(n/2) + O(n). The recursion tree has about log2 n levels and each level does O(n) work, so O(n log n) whatever the input. A merge of sizes p and q makes between min(p, q) and p + q - 1 comparisons. Extra memory is O(n) for the merged lists plus an O(log n) stack, so recursion depth is never a problem in Python. The slices `a[:mid]` copy, but that is O(n) per level, the same order as the merge.

**Counting during the merge.** When `right[j]` is taken while `left[i:]` remains, it is smaller than all `len(left) - i` of those, and each such pair is an **inversion** (i < j with a[i] > a[j]) that crosses the halves. Inversions inside each half are counted by the recursive calls, so the total costs O(n log n). Insertion sort performs exactly one shift per inversion, so this number is its work. When the counting condition differs from the merge order, such as reverse pairs with a[i] > 2 a[j], count in a separate two-pointer pass over the two sorted halves *before* merging them.

**In real systems.** Merging works on streams read front to back, which is why sorts of data bigger than memory are usually external merge sorts. PostgreSQL's tuplesort sorts work_mem-sized batches in memory, writes them as sorted runs to temporary files and merges the runs with a balanced k-way merge (before version 15 it used polyphase merge, designed for tape drives). CPython's list.sort is a merge sort of natural runs (see the Timsort card), and bottom-up merging, widths 1, 2, 4 and so on, needs no recursion at all.

## Template

```python
def merge(left, right):
    """Merge two sorted lists; stable because ties take from the left."""
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if right[j] < left[i]:            # strictly smaller: only then take from the right
            out.append(right[j])
            j += 1
        else:
            out.append(left[i])
            i += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def merge_sort(a):
    if len(a) <= 1:
        return a[:]
    mid = len(a) // 2
    return merge(merge_sort(a[:mid]), merge_sort(a[mid:]))


def sort_count(a):
    """Return (sorted copy of a, number of pairs i < j with a[i] > a[j])."""
    if len(a) <= 1:
        return a[:], 0
    mid = len(a) // 2
    left, x = sort_count(a[:mid])
    right, y = sort_count(a[mid:])
    out, i, j, cross = [], 0, 0, 0
    while i < len(left) and j < len(right):
        if right[j] < left[i]:
            cross += len(left) - i        # right[j] is below every item in left[i:]
            out.append(right[j])
            j += 1
        else:
            out.append(left[i])
            i += 1
    return out + left[i:] + right[j:], x + y + cross
```

## Worked example

The last merge of `sort_count([3, 5, 8, 1, 5, 6, 9])`: halves [3, 5, 8] and [1, 5, 6, 9] are already sorted. The left 5 is marked 5L to show stability.

```steps
right[0] = 1 < left[0] = 3: take 1; it is below all three left items, so cross += 3
    left    {{3}}  5L  8          right   {{1}}  5  6  9
    out     1                     cross = 3
---
3 <= 5: take 3 from the left
    left    3  {{5L}}  8          right   1  {{5}}  6  9
    out     1  3                  cross = 3
---
5L vs 5: equal, so take from the LEFT first (stability): 5L
    left    3  5L  {{8}}          right   1  {{5}}  6  9
    out     1  3  5L              cross = 3
---
right 5 < left 8: take 5; only 8 remains on the left, so cross += 1
    left    3  5L  {{8}}          right   1  5  {{6}}  9
    out     1  3  5L  5           cross = 4
---
right 6 < 8: take 6, cross += 1
    left    3  5L  {{8}}          right   1  5  6  {{9}}
    out     1  3  5L  5  6        cross = 5
---
8 <= 9: take 8; the left is empty, so append the rest of the right
    left    (done)                right   (done)
    out     1  3  5L  5  6  8  9  cross = {{5}}: (3,1) (5,1) (8,1) (8,5) (8,6)
```

## Pitfalls

- Writing `if left[i] < right[j]: take left else take right` takes from the right on ties: still sorted, no longer stable.
- Counting reverse pairs with the merge comparison itself: the merge orders by a[i] > a[j], the question asks a[i] > 2 a[j], so you miss pairs. Count first, then merge.
- Building many tiny lists is slow in CPython; for speed, merge by index into one preallocated buffer, or let `sorted` do the work when you do not need the counts.

## Quick check

Q: Why does the inversion count only add `len(left) - i` when an element comes from the right, and nothing when one comes from the left?
A: An element taken from the left is no larger than everything left in `right`, so it forms no crossing inversion with them. An element taken from the right is strictly smaller than every remaining left element, each of which sits earlier in the array: exactly `len(left) - i` inversions.

> [!know]
> You now know how to merge stably and how to piggyback cross-half counts on merge sort's O(n log n) passes.

=== recap | Partitioning and quicksort: Lomuto, Hoare and three-way | 14 min
goal: Partition in place with Lomuto, Hoare and three-way schemes, state each invariant, and explain quicksort's expected and worst-case cost and how production sorts guard it
tag: sorting-partition | Partitioning and quicksort
link: Wikipedia: Quicksort, Hoare partition scheme | https://en.wikipedia.org/wiki/Quicksort#Hoare_partition_scheme | 10 min: 'Lomuto partition scheme', 'Hoare partition scheme' (three times fewer swaps on average, balanced on equal keys) and 'Repeated elements' under 'Implementation issues'
practice: 912, 324

> [!key]
> Partitioning rearranges an array around a pivot so that smaller items come first, in O(n) time and O(1) space. Quicksort partitions and recurses on both sides: O(n log n) expected with a random pivot, O(n^2) when the pivots are consistently bad. A **three-way** partition (less, equal, greater) makes duplicates harmless, and recursing into the smaller side first keeps the stack at O(log n).

## Internals

**Lomuto** uses the last element as the pivot and keeps three regions: a[lo:i] < pivot, a[i:j] >= pivot, a[j:hi] unknown. Each step examines a[j]; if it is smaller it is swapped to position i and the first region grows. Finally the pivot is swapped into position i, its sorted place. Easy to prove, but it swaps a lot, and on all-equal input every split is (n - 1, 0): O(n^2) even with a random pivot.

**Hoare** walks two indices inward: i stops at an item >= pivot, j at an item <= pivot, and they swap. It returns j with a[lo..j] <= pivot <= a[j + 1..hi], but the pivot is not necessarily at j, so recurse on [lo, j] and [j + 1, hi]. It does about three times fewer swaps than Lomuto, and equal keys stop both scans, so all-equal input splits evenly.

**Three-way (Dijkstra's Dutch national flag)** keeps a[lo:lt] < p, a[lt:i] == p, a[i:gt] unknown and a[gt:hi] > p. Every key equal to the pivot is finished in this pass and never touched again, so a list of few distinct values sorts in close to linear time.

**Cost.** With a random pivot, quicksort makes about 2n ln n, roughly 1.39 n log2 n, comparisons on average. The worst case is O(n^2): a first- or last-element pivot on sorted input, or Lomuto on equal keys. Each partition pass is O(n); recursing into the smaller part and looping on the larger bounds the stack at log2 n frames.

**Production quicksorts are hybrids.** GCC's `std::sort` (introsort) takes the median of three elements as the pivot, leaves pieces of at most 16 elements for later, switches a range to heapsort once the recursion depth passes 2 log2 n, and finishes with one insertion sort pass over the whole array. The standard requires O(n log n) comparisons in the worst case (defect report LWG 713; average-case used to be enough, which allowed plain quicksort), and LLVM's libc++ met that only in LLVM 14. Go 1.19 moved to pattern-defeating quicksort, and Rust's `sort_unstable` uses ipnsort, a quicksort with a heapsort fallback.

## Template

```python
import random


def lomuto(a, lo, hi):
    """Partition a[lo..hi] around the pivot a[hi]; return the pivot's final index."""
    pivot, i = a[hi], lo
    for j in range(lo, hi):              # a[lo:i] < pivot <= a[i:j]
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]
    return i


def hoare(a, lo, hi):
    """Partition a[lo..hi] (lo < hi); return p with a[lo..p] <= pivot <= a[p+1..hi]."""
    pivot = a[(lo + hi) // 2]            # never the last element, or it can loop forever
    i, j = lo - 1, hi + 1
    while True:
        i += 1
        while a[i] < pivot:
            i += 1
        j -= 1
        while a[j] > pivot:
            j -= 1
        if i >= j:
            return j
        a[i], a[j] = a[j], a[i]


def partition3(a, lo, hi, pivot):
    """Rearrange a[lo:hi] into < pivot, == pivot, > pivot; return (lt, gt)."""
    lt, i, gt = lo, lo, hi
    while i < gt:
        if a[i] < pivot:
            a[lt], a[i] = a[i], a[lt]
            lt += 1
            i += 1
        elif a[i] > pivot:
            gt -= 1
            a[gt], a[i] = a[i], a[gt]
        else:
            i += 1
    return lt, gt


def quicksort(a, lo=0, hi=None):
    """Sort a[lo:hi] in place: random pivot, three-way partition, small side first."""
    if hi is None:
        hi = len(a)
    while hi - lo > 1:
        lt, gt = partition3(a, lo, hi, a[random.randrange(lo, hi)])
        if lt - lo < hi - gt:
            quicksort(a, lo, lt)         # recurse on the smaller side...
            lo = gt                      # ...and loop on the larger one
        else:
            quicksort(a, gt, hi)
            hi = lt
```

## Worked example

Lomuto on [7, 2, 9, 4, 3, 8, 5] with pivot 5. The bottom row shows the regions: `<` below the pivot, `>=` at least the pivot, `?` not yet seen, `p` the pivot.

```steps
j = 0: 7 >= 5, leave it; the >= region grows to [0, 1)
    i         0    1    2    3    4    5    6
    a         {{7}}    2    9    4    3    8    5
             >=    ?    ?    ?    ?    ?    p
---
j = 1: 2 < 5, swap it to position i = 0; i becomes 1
    i         0    1    2    3    4    5    6
    a         {{2}}    {{7}}    9    4    3    8    5
              <   >=    ?    ?    ?    ?    p
---
j = 2: 9 >= 5, leave it
    i         0    1    2    3    4    5    6
    a         2    7    {{9}}    4    3    8    5
              <   >=   >=    ?    ?    ?    p
---
j = 3: 4 < 5, swap with a[1] = 7; i becomes 2
    i         0    1    2    3    4    5    6
    a         2    {{4}}    9    {{7}}    3    8    5
              <    <   >=   >=    ?    ?    p
---
j = 4: 3 < 5, swap with a[2] = 9; i becomes 3
    i         0    1    2    3    4    5    6
    a         2    4    {{3}}    7    {{9}}    8    5
              <    <    <   >=   >=    ?    p
---
j = 5: 8 >= 5, leave it. The unknown region is empty
    i         0    1    2    3    4    5    6
    a         2    4    3    7    9    {{8}}    5
              <    <    <   >=   >=   >=    p
---
Swap the pivot into position i = 3: everything left is smaller, everything right is at least 5
    i         0    1    2    3    4    5    6
    a         2    4    3    {{5}}    9    8    7
              <    <    <    =   >=   >=   >=
```

Hoare on the same list (pivot 4, the middle element) needs two swaps and returns 2, leaving [3, 2, 4 | 9, 7, 8, 5].

## Pitfalls

- **Hoare's bounds.** Recurse on [lo, p] and [p + 1, hi], not around p as if the pivot sat there; and never take a[hi] as Hoare's pivot: on [1, 2] it returns p = hi and the recursion never shrinks.
- **First or last element as the pivot** makes sorted input quadratic, and the recursion depth n overflows Python's default limit of 1000 frames after a few thousand items.
- **Two-way partitions on many duplicates** degrade to O(n^2) (Lomuto) or do needless work; use three-way.
- **Quicksort is not stable.** Use it when the order of equal keys does not matter.

## Quick check

Q: All n keys are equal. What does each scheme do, and what is the total cost of quicksort with it?
A: Lomuto puts everything in the `>=` region, so each pass removes only the pivot: O(n^2). Hoare stops at every element and swaps, splitting near the middle: O(n log n). Three-way puts everything in the equal region in one pass and stops: O(n).

> [!know]
> You now know how to partition in place with an invariant you can state, and why production quicksorts randomise, use three-way splits and fall back to heapsort.

=== recap | Quickselect: the k-th element without sorting | 12 min
goal: Find the k-th smallest element in expected O(n) with quickselect, and choose between quickselect, heapq.nsmallest and sorting for a given n and k
tag: sorting-select | Quickselect and top-k choices
link: Wikipedia: Quickselect, Algorithm | https://en.wikipedia.org/wiki/Quickselect#Algorithm | 5 min: 'Algorithm' (recurse into one side only) and 'Time complexity' (average linear, worst quadratic, and median of medians)
practice: 1985, 324

> [!key]
> To find the k-th smallest you do not need the whole order: partition once, see which side position k falls on, and continue in that side only. With a random pivot the expected work is about n + n/2 + n/4 + ..., which is O(n); the worst case is O(n^2). In Python, weigh it against `heapq.nsmallest` (O(n log k)) and `sorted` (O(n log n), but in C).

## Internals

**Narrowing.** Keep [lo, hi) as the slice that still contains position k: everything before lo belongs before position k in sorted order and everything from hi on belongs after it. A three-way partition around p returns lt and gt. If k < lt, continue in [lo, lt); if k >= gt, continue in [gt, hi); otherwise a[k] equals p and you are done. Because it only ever recurses into one side, a loop replaces the recursion.

**Expected O(n).** A random pivot lands in the middle half of the current slice with probability 1/2, and then the slice shrinks to at most three quarters of its size. So on average every two rounds cut the slice by a quarter, and the total work is a geometric series bounded by a constant times n. Measured for the median of 100,000 random floats, the partitions scanned about 3.4n elements in total, matching the textbook 2(1 + ln 2)n. The worst case, always picking an extreme pivot, is O(n^2); the median-of-medians pivot guarantees O(n) but is slower in practice. C++ offers `std::nth_element`, which in libstdc++ is introselect: quickselect with a heap-based fallback after too many bad splits. Python has no built-in quickselect.

**Choosing in Python.** Theory favours quickselect, but constants decide. On CPython 3.12, finding the median of a million random floats took about 1.3 s with the pure-Python quickselect below and about 0.9 s with `sorted(xs)[k]`, because the sort runs in C. `heapq.nsmallest(10, xs)` took 0.03 s.

| Need | Best tool | Cost |
|---|---|---|
| k smallest, k small | `heapq.nsmallest(k, xs)` | O(n log k); it uses `min` when k = 1 and `sorted` when k >= n |
| one k-th element, huge n, C or NumPy | quickselect (`std::nth_element`, `numpy.partition`) | O(n) expected |
| one k-th element in pure Python | usually `sorted(xs)[k]` | O(n log n), but in C |
| many order queries on fixed data | sort once | O(n log n), then O(1) per query |
| top k of a stream | a size-k heap | O(n log k) time, O(k) memory |

## Template

```python
import random


def quickselect(a, k):
    """k-th smallest of a (k = 0 is the minimum) in expected O(n); a is not modified.
    Uses partition3 from the partitioning card, so duplicates are harmless."""
    a = list(a)
    lo, hi = 0, len(a)
    while True:
        lt, gt = partition3(a, lo, hi, a[random.randrange(lo, hi)])
        if k < lt:
            hi = lt
        elif k >= gt:
            lo = gt
        else:
            return a[k]
```

## Worked example

The 6th smallest (k = 5) of [7, 2, 9, 4, 6, 1, 8, 3]. The pivots shown are what the random choice happened to pick; the highlighted cells are the pivot's equal block.

```steps
Pivot 4 on [0, 8): smaller items go left. Equal block [3, 4); k = 5 >= 4, so keep [4, 8)
    i         0    1    2    3    4    5    6    7    8
    a         3    2    1    {{4}}    6    8    9    7
             lo                        k             hi
---
Pivot 8 on [4, 8): equal block [6, 7); k = 5 < 6, so keep [4, 6)
    i         0    1    2    3    4    5    6    7    8
    a         3    2    1    4    6    7    {{8}}    9
                                 lo    k             hi
---
Pivot 7 on [4, 6): equal block [5, 6) contains k = 5: the answer is 7
    i         0    1    2    3    4    5    6    7    8
    a         3    2    1    4    6    {{7}}    8    9
                                 lo    k   hi
```

Three partitions touched 8 + 4 + 2 = 14 cells; a full sort would have ordered all eight.

## Pitfalls

- **Off by one on k.** "k-th largest" (1-based) is index n - k in ascending order.
- **Two-way partitions** make all-equal input quadratic; use the three-way version.
- **Comparing numbers stored as strings** (LeetCode 1985): compare by (length, string), never by string alone ("9" > "10" as text).
- **Mutating the caller's list**: copy first, as the template does, unless in-place is the point.

## Quick check

Q: You need the 100 largest of 10 million scores, once. Which tool and why?
A: `heapq.nlargest(100, scores)`: O(n log 100) with a 100-item heap, one pass and almost no memory, and it runs in C. Quickselect would need a copy of all 10 million items and still has to sort the 100 afterwards if order matters.

> [!know]
> You now know how to select the k-th element in expected linear time, and how to pick the fastest tool in Python for a given n and k.

=== recap | Counting, radix and bucket sort, and the n log n floor | 14 min
goal: Prove that comparison sorts need about n log2 n comparisons, and beat that bound with counting, radix and bucket sort when keys are small or evenly spread
tag: sorting-counting | Counting, radix and bucket sort
link: Open Data Structures, 11.2: Counting Sort and Radix Sort | https://opendatastructures.org/ods-python/11_2_Counting_Sort_Radix_So.html | 10 min: 11.2.1 counting sort (stable, via prefix sums of the counts) and 11.2.2 radix sort (digit by digit, relying on that stability)
link: MIT 6.006 (Spring 2020), lecture 5 notes | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/78a3c3444de1ff837f81e52991c24a86_MIT6_006S20_lec5.pdf | 15 min: 'Comparison Sort Lower Bound', then 'Counting Sort', 'Tuple Sort' and 'Radix Sort'
practice: 1122, 274, 164

> [!key]
> A sort that only compares items needs at least log2(n!), about n log2 n - 1.44n, comparisons in the worst case, because it must tell all n! orders apart. Sorts that use keys as array indices escape the bound: counting sort is O(n + k) for integer keys below k, radix sort runs a stable counting sort per digit, and bucket sort spreads evenly distributed values into about n buckets.

## Internals

**The lower bound.** Draw any comparison sort as a binary decision tree: each internal node is one comparison, each leaf one final order. All n! inputs need different leaves, and a tree of height h has at most 2^h leaves, so h >= log2(n!) = n log2 n - n log2 e + O(log n). For n = 100,000 that is about 1.52 million comparisons; CPython's sort used 1.53 million on random floats. The bound says nothing about sorts that never compare.

**Counting sort.** Count each key, turn the counts into starting positions with a prefix sum, then place items left to right, advancing each key's position. Placing left to right makes it **stable**. O(n + k) time and space: excellent when k is O(n), wasteful when keys reach 10^9.

**Radix sort (least significant digit first).** Sort by the last digit, then the next, each pass a stable counting sort. By induction, after pass t the items are ordered by their last t digits, and stability is exactly what keeps the earlier passes' order among equal digits. d digits in base b cost O(d(n + b)): 32-bit integers in base 256 need four passes.

**Bucket sort and pigeonholes.** n values spread over [lo, hi] go into about n equal-width buckets; if they are roughly uniform each bucket holds O(1) items, so sorting the buckets is O(n) expected. The same pigeonhole idea solves Maximum Gap (164): the largest gap between neighbours is at least (hi - lo) / (n - 1), so it never lies inside a bucket of that width, and only each bucket's minimum and maximum matter.

**When not to.** Floats, strings and composite keys usually want comparisons; a huge key range wastes memory; and in CPython `sorted` runs in C, so a pure-Python radix sort rarely wins unless the key range is small. In production, NumPy's `np.sort(kind="stable")` uses radix sort for integer data, and PostgreSQL builds its sorted runs with quicksort or radix sort.

## Template

```python
def counting_sort(a, key=lambda x: x, k=None):
    """Stable sort of a by integer keys in [0, k). O(n + k) time and space."""
    if k is None:
        k = max(map(key, a), default=-1) + 1
    start = [0] * (k + 1)
    for x in a:
        start[key(x) + 1] += 1
    for v in range(k):                    # prefix sums: start[v] = first slot for key v
        start[v + 1] += start[v]
    out = [None] * len(a)
    for x in a:                           # left to right keeps equal keys in order
        out[start[key(x)]] = x
        start[key(x)] += 1
    return out


def radix_sort(a, base=256):
    """Sort non-negative integers: one stable counting sort per base-`base` digit."""
    shift = 1
    while a and shift <= max(a):
        a = counting_sort(a, key=lambda x: x // shift % base, k=base)
        shift *= base
    return a
```

## Worked example

Counting sort of five records by their key (0, 1 or 2). The letters show that equal keys keep their input order.

```steps
Count the keys, stored one slot to the right: two 0s, one 1, two 2s
    records  2a  0b  2c  1d  0e
    start    [0, 2, 1, 2]
---
Prefix sums turn counts into first slots: key 0 starts at 0, key 1 at 2, key 2 at 3
    records  2a  0b  2c  1d  0e
    start    [{{0}}, {{2}}, {{3}}, 5]
---
Place 2a at slot start[2] = 3, then start[2] becomes 4
    out      [ _,  _,  _, {{2a}},  _ ]
    start    [0, 2, 4, 5]
---
Place 0b at slot 0 and 2c at slot 4: 2c lands after 2a, as in the input
    out      [{{0b}},  _,  _, 2a, {{2c}}]
    start    [1, 2, 5, 5]
---
Place 1d at slot 2 and 0e at slot 1: done, stable
    out      [0b, {{0e}}, {{1d}}, 2a, 2c]
    start    [2, 3, 5, 5]
```

## Pitfalls

- **Negative keys:** shift by the minimum first (`key = x - lo`).
- **Placing right to left** without iterating the input in reverse breaks stability, and LSD radix sort then gives wrong answers.
- **Radix sort on negative integers** needs the sign handled separately (sort by sign first, or offset).
- **Counting sort with k far larger than n** spends its time on the count array. Clamp when the problem allows it: for H-Index (274), any count above n acts like n, so n + 1 buckets suffice.

## Quick check

Q: Why can no comparison sort beat 3 comparisons in the worst case for 3 items, even though 2 comparisons sometimes suffice?
A: Three items have 3! = 6 orders, so the decision tree needs 6 leaves; a binary tree of height 2 has at most 4. Some input must take 3 comparisons. (Sorted input can finish after 2, which is why the bound is a worst case.)

> [!know]
> You now know why n log n is a floor only for comparison sorts, and how to sort small integer keys in linear time, stably.

=== recap | How Python and C++ sort: Timsort, powersort and introsort | 14 min
goal: Explain what CPython's list.sort does with runs, minrun, powersort merges and galloping, what std::sort and std::stable_sort promise, and use sorting as a preprocessing step with confidence
tag: sorting-builtin | Built-in sorts and sorting first
link: Wikipedia: Timsort, Operation | https://en.wikipedia.org/wiki/Timsort#Operation | 10 min: 'Operation' (runs, merge criteria, galloping mode during merge) and 'Analysis' (linear on presorted input)
link: CPython Objects/listsort.txt | https://github.com/python/cpython/blob/main/Objects/listsort.txt | 20 min: the primary source; read 'Intro', 'Runs', 'Computing minrun', 'The Merge Pattern' (the powersort policy) and 'Galloping'
practice: 976

> [!key]
> CPython's `list.sort` and `sorted` are **Timsort**: a stable, adaptive merge sort that finds runs already in order, extends short runs with binary insertion sort, merges neighbouring runs under the **powersort** policy (Python 3.11 and later) and **gallops** when one run keeps winning. It is O(n log n) in the worst case and O(n) on sorted or reversed input. C++'s `std::sort` is an unstable introsort with an O(n log n) worst case; `std::stable_sort` is a merge sort.

## Internals

**Runs.** One left-to-right pass finds the next run: ascending (non-decreasing) or descending, and a descending run is reversed in place in a way that keeps the sort stable. A run shorter than **minrun** is extended to minrun with binary insertion sort. Under 64 items minrun is the whole list; for longer lists it lies between 32 and 64, chosen so runs merge in balanced pairs.

**Merging.** Only neighbouring runs merge (see the quick check). Pending runs sit on a stack. Since Python 3.11 the merge order follows Munro and Wild's powersort, which is provably near-optimal for the mix of run lengths; earlier versions used Tim Peters' original stack rules. A merge copies only the shorter run to temporary memory, and first binary-searches where B[0] belongs in A and where A[-1] belongs in B, skipping elements already in place.

**Galloping.** If one run wins MIN_GALLOP = 7 times in a row, the merge switches to exponential search (look 1, 3, 7, 15, ... ahead, then binary-search) and copies whole chunks. The threshold adapts: it rises when galloping does not pay and falls when it does.

**Guarantees.** Only `<` is called, a `key` runs once per element, and `reverse=True` keeps equal items in input order. Comparisons for 100,000 floats on CPython 3.12:

| Input | Comparisons |
|---|---|
| already sorted | 99,999 |
| reversed | 99,999 |
| 16 sorted runs, concatenated | 499,985 |
| ten distinct values | 711,477 |
| random | 1,529,071 (the lower bound log2(n!) is about 1,516,704) |

**C++ and friends.** `std::sort` must make O(n log n) comparisons in the worst case and is not stable; GCC implements it as introsort (see the partitioning card). `std::stable_sort` is a merge sort: O(n log n) comparisons with enough extra memory, O(n log^2 n) without. Rust's `slice::sort` is driftsort (stable) and `sort_unstable` is ipnsort; both run in linear time on fully sorted or reversed input. Go 1.19 rewrote `sort` as pattern-defeating quicksort.

**Sorting first.** Once sorted, equal items are adjacent, pairs fall to two pointers, ranges to bisect, and many greedy choices become one scan, as in `largest_perimeter` below.

## Template

```python
class Counted:
    """Wrap values to count how many comparisons a sort makes."""
    calls = 0

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        Counted.calls += 1
        return self.v < other.v


def comparisons(xs):
    Counted.calls = 0
    sorted(map(Counted, xs))
    return Counted.calls


def largest_perimeter(sides):
    """Sort once, then a single scan: the first valid consecutive triple wins."""
    a = sorted(sides, reverse=True)
    for i in range(len(a) - 2):
        if a[i] < a[i + 1] + a[i + 2]:
            return a[i] + a[i + 1] + a[i + 2]
    return 0
```

## Worked example

`comparisons(range(10))` returns 9: one pass finds a single ascending run and nothing is merged. `comparisons(range(9, -1, -1))` also returns 9: one strictly descending run, reversed in place. A shuffled list of 10 is a single binary insertion sort, about log2(i) comparisons to insert item i: 23 on average and never more than 26 in 20,000 trials, against 45 for plain insertion sort's worst case. At 100,000 items the table above shows the adaptivity: 16 runs cost a third of a random input.

## Pitfalls

- `xs.sort()` returns `None`; `xs = xs.sort()` loses the list.
- Mixed types (`None` among ints) raise `TypeError`, and NaN breaks the order silently: `sorted([3, float("nan"), 1, 2])` returns `[3, nan, 1, 2]`.
- Re-sorting nearly sorted data is cheap, so keeping a list sorted by appending and calling `sort()` again can beat clever structures for small batches; measure before replacing it.
- `std::sort` is not stable; use `std::stable_sort` when equal keys must keep their order.

## Quick check

Q: Why does Timsort only merge neighbouring runs, even when merging two non-neighbours first would be cheaper?
A: Stability. If runs A, B and C all contain an equal key, merging A with C first would place C's copy before B's. Merging neighbours, (A+B)+C or A+(B+C), keeps every equal key in input order.

> [!know]
> You now know what Python's and C++'s built-in sorts really do, what they cost on real inputs, and when to sort first.

=== recap | Custom orders: keys, comparators and consistency | 12 min
goal: Express any ordering as a key function or a consistent comparator, including multi-key and mixed-direction sorts, and prove a comparator such as "largest concatenated number" is a valid order
tag: sorting-comparator | Custom orders: keys and comparators
link: Python docs: Sorting Techniques, Sort Stability and Complex Sorts | https://docs.python.org/3/howto/sorting.html#sort-stability-and-complex-sorts | 5 min: multi-key sorts done in passes thanks to stability; then 'Comparison Functions' (cmp_to_key) a few sections below
practice: 1636, 179

> [!key]
> Prefer a **key function**: it maps each item to a value Python already knows how to order, computed once per item. Multi-key orders are tuple keys (negate numbers to flip a direction) or several stable passes. When the order is only defined pairwise, use `functools.cmp_to_key`, and make sure the comparator is a genuine order (irreflexive, transitive, consistent about ties); otherwise the result is garbage in Python and undefined behaviour in C++.

## Internals

**Keys.** `sorted(xs, key=f)` calls f once per element and sorts the results, which is the old decorate-sort-undecorate idiom built in. Tuples compare left to right, so `key=lambda x: (freq[x], -x)` sorts by increasing frequency and breaks ties by decreasing value. Strings cannot be negated: sort by the secondary key, then by the primary with `reverse=True`; stability keeps the secondary order inside each primary group.

**Comparators.** `cmp_to_key(cmp)` wraps each item in an object whose `<` calls `cmp(a, b) < 0`, so every comparison is a Python function call. Sorting 200,000 numeric strings by (length, value) took about 0.63 s with a tuple key and 1.8 s with the equivalent comparator: roughly three times slower.

**Consistency.** A valid "less than" must be irreflexive (never a < a), transitive (a < b and b < c give a < c), and treat "neither is less" as an equivalence that is itself transitive. Common violations: `<=` instead of `<`, NaN among floats (every comparison with NaN is False), "rock, paper, scissors" rules, and comparators that depend on outside state. Python never crashes, but the output depends on the input order. In C++ it is undefined behaviour: with GCC's `std::sort`, a `<=` comparator on 100 equal ints made the comparator read memory outside the range thousands of times in our test.

**Largest number (179).** Put a before b when the string a + b is greater than b + a. This is consistent because, for digit strings, a + b > b + a exactly when a / (10^len(a) - 1) > b / (10^len(b) - 1): it compares the repeating decimals 0.aaa... and 0.bbb..., which are real numbers, so it is transitive. Then handle the all-zeros case, where the answer is "0", not "000".

## Template

```python
from collections import Counter
from functools import cmp_to_key


def concat_order(a, b):
    """Negative when a should come first: a + b forms the larger number."""
    return (b + a > a + b) - (b + a < a + b)


def largest_number(nums):
    s = "".join(sorted(map(str, nums), key=cmp_to_key(concat_order)))
    return "0" if s[0] == "0" else s


def frequency_sort(nums):
    """Increasing frequency; equal frequencies by decreasing value."""
    freq = Counter(nums)
    return sorted(nums, key=lambda x: (freq[x], -x))


def sort_by_score_desc_then_name(records):
    """(name, score) pairs: score descending, then name ascending, in two stable passes."""
    by_name = sorted(records, key=lambda r: r[0])
    return sorted(by_name, key=lambda r: r[1], reverse=True)
```

## Worked example

Largest number from [3, 30, 34, 5, 9]: each decision compares the two concatenations.

```steps
9 vs 5: "95" > "59", so 9 goes first
    pair   "9" + "5" = {{95}}    "5" + "9" = 59
---
3 vs 30: "330" > "303", so 3 goes before 30, although 3 < 30 as numbers
    pair   "3" + "30" = {{330}}  "30" + "3" = 303
---
34 vs 3: "343" > "334", so 34 goes before 3
    pair   "34" + "3" = {{343}}  "3" + "34" = 334
---
The consistent order puts 9, 5, 34, 3, 30 in sequence
    result {{9534330}}
```

## Pitfalls

- A comparator returning a bool (`lambda a, b: a + b > b + a`) is wrong: `cmp_to_key` needs a negative, zero or positive number, and True/False read as 1/0, so "less than" never happens.
- Sorting digit strings as text: "10" < "9". Compare by (length, string) for non-negative integers without leading zeros.
- Forgetting the all-zeros case in largest number.
- Negating a key that is not numeric: use two stable passes instead.

## Quick check

Q: Spot the bug: `sorted(words, key=cmp_to_key(lambda a, b: len(a) <= len(b)))`. What does it actually do?
A: The lambda returns True or False, read as 1 or 0, never negative, so no word is ever "less" than another. With nothing to reorder, the output is simply the input order (Timsort sees one long non-decreasing run). Use `key=len`.

> [!know]
> You now know how to express any ordering as a key or a consistent comparator, and how to prove a comparator is a real order.

=== lab | Sorting showdown | 50 min
goal: Implement insertion, merge, quick and counting sort, benchmark them against sorted() on four input shapes at doubling sizes, and explain every result from the mechanics
link: CPython Objects/listsort.txt, Intro | https://github.com/python/cpython/blob/main/Objects/listsort.txt | 10 min: the 'Intro' and the table of comparison counts by input shape, which predicts what you will see for sorted()

## Steps

1. **Implement** in `sorts.py`: `insertion_sort`, `merge_sort` (stable), `quick` (copy, then the random three-way `quicksort`), `naive_quick` (first element as pivot, two-way, recursive), and `counting(a, k)` for integers in [0, k). Each returns a new sorted list.
2. **Stress-test first.** For 2,000 random lists of length 0 to 30 with values 0 to 9, assert every function equals `sorted(xs)`. For stability, sort (key, tag) pairs by key with `merge_sort` (wrap them so `<` compares keys only) and check the tags of equal keys stay in input order.
3. **Inputs.** For each n build four lists of integers below 1,000: random, sorted, reversed, and "few distinct" (values 0 to 4).
4. **Time** with the best of three `time.perf_counter()` runs. Use n = 1,000, 2,000, 4,000 for `insertion_sort` and `naive_quick`, and n = 50,000, 100,000, 200,000 for the rest. Print one table: algorithm, input shape, times, and the ratio between successive sizes.
5. **Recursion.** Run `naive_quick(list(range(3000)))` with the default recursion limit. What happens, and why?
6. **Count comparisons** of `sorted()` with the `Counted` wrapper from the Timsort card on the four shapes at n = 100,000, and compare with log2(n!) (`math.lgamma(n + 1) / math.log(2)`).
7. **Read** the Intro of listsort.txt and write three sentences explaining your `sorted()` numbers.

## What you should see

Exact times depend on the machine; on a busy one take the best of three runs and trust the ratios more than the numbers.

- **Insertion sort**: roughly 4x per doubling on random, reversed and few-distinct input (quadratic), but almost instant on sorted input, where it is the fastest hand-written sort: one comparison per item.
- **Merge sort and three-way quicksort**: a little over 2x per doubling (n log n) on every shape. Quicksort is usually faster than merge sort on random data (in place, no list building) and far faster on few-distinct input, where the equal blocks finish in one pass.
- **Naive quicksort**: fine on random input, quadratic on sorted and reversed input, and at n = 3,000 sorted it raises `RecursionError` (depth about n, default limit 1,000).
- **Counting sort** with k = 1,000: linear, and faster than `sorted()` at these sizes because the key range is small.
- **`sorted()`**: 10 to 20 times faster than your best pure-Python n log n sort on random data, and far faster still on sorted or reversed input. Comparisons: 99,999 for sorted and reversed, about 1.53 million for random against a lower bound of about 1.52 million, and fewer for few-distinct input.
- The explanation: C code and no interpreter overhead per comparison; natural runs make sorted and reversed input a single pass; and on random data Timsort sits within about 1% of the information-theoretic minimum number of comparisons.

=== practice
- 1122 core
  pattern: sorting-counting
  cue: Values are small non-negative integers (at most 1,000) and the target order is given by a second list, with leftovers ascending.
  hint: With values this small, do you need comparisons at all? What if you counted each value first?
  insight: Count arr1 into a 1,001-slot array, emit each arr2 value as many times as counted (zeroing the count), then sweep the remaining values in increasing order. That is counting sort with a custom output order: O(n + V), no comparisons.
  cost: O(n + V) time, O(V) space, where V is the value range
- 1636 core
  pattern: sorting-comparator
  cue: Order numbers by how often they occur, and break ties in the opposite direction from the main order.
  hint: Can the whole rule be one value per element that Python already orders correctly?
  insight: Count with Counter, then sort with key=lambda x: (freq[x], -x): the tuple compares frequency first, and negating the value flips the tie-break to descending. One key, computed once per element, no comparator.
  cost: O(n log n) time, O(n) space
- 976 derive
  pattern: sorting-builtin
  cue: Pick three lengths that form a triangle with the largest perimeter.
  hint: Fix the longest side. Which two other sides give it the best chance of satisfying the triangle inequality?
  insight: Sort descending. For longest side a[i], the best partners are the next two, a[i+1] and a[i+2]; if a[i] >= a[i+1] + a[i+2], no smaller pair can work, so a[i] can never be the longest side. The first i with a[i] < a[i+1] + a[i+2] gives the answer.
  cost: O(n log n) time, O(1) extra space
- 912 core
  pattern: sorting-partition
  cue: Sort an array yourself in O(n log n), without the built-in sort; the tests include sorted and heavily duplicated arrays.
  hint: Which algorithms keep O(n log n) on sorted input and on arrays where most values are equal? What goes wrong with a first-element pivot?
  insight: Use quicksort with a random pivot and a three-way partition (equal keys finish in one pass, sorted input is no longer adversarial), recursing on the smaller side; or merge sort, which is O(n log n) on every input at the price of O(n) extra memory.
  cost: O(n log n) expected time, O(log n) extra space (quicksort) or O(n) (merge sort)
- 179 core
  pattern: sorting-comparator
  cue: Arrange numbers so that their concatenation is as large as possible.
  hint: For just two numbers, how do you decide which goes first? Is that rule safe to use as a sort order?
  insight: Sort the strings with cmp_to_key, putting a before b when a + b > b + a. It is a valid order because it compares the repeating decimals 0.aaa... and 0.bbb..., which is transitive. Return "0" when the first string is "0".
  cost: O(n log n) comparisons of O(L) each, where L is the number of digits; O(nL) space
- 451 core
  pattern: sorting-counting
  cue: Rearrange the characters of a string by decreasing frequency.
  hint: Frequencies are whole numbers no larger than the string's length. Could each frequency be a bucket?
  insight: Count characters, then put each character into bucket[freq] (a list of lists of size n + 1) and read the buckets from high to low, writing each character freq times. Bucket sort by frequency is O(n); sorting the distinct characters by count is also fine because there are at most a few dozen.
  cost: O(n) time with buckets, O(n) space
- 274 core
  pattern: sorting-counting
  cue: The largest h such that at least h papers have at least h citations each, with citations up to 1,000 and n up to 5,000.
  hint: Does it matter whether a paper has n citations or a million?
  insight: Clamp every count to n and counting-sort into n + 1 buckets. Sweep h from n down to 0, accumulating how many papers have at least h citations; the first h where that total reaches h is the answer. (Sorting descending and finding the last i with c[i] >= i + 1 also works in O(n log n).)
  cost: O(n) time, O(n) space
- 1985 core
  pattern: sorting-select
  cue: The k-th largest of numbers given as strings of up to 100 digits, with no leading zeros.
  hint: How do you compare two such numbers without converting them? Do you need the full order to find one position?
  insight: Compare by (len(s), s): a longer string is a larger number, and equal lengths compare as text. Then quickselect for index n - k in ascending order (expected O(n) comparisons), or keep a size-k min-heap of those keys, or simply sort with that key.
  cost: O(n) expected comparisons of O(L) each with quickselect; O(n log k) with a heap
- 164 derive
  pattern: sorting-counting
  cue: The maximum difference between neighbours in sorted order, required in linear time and space.
  hint: With n values between lo and hi, how small can the largest gap possibly be? Could the answer lie inside a narrow bucket?
  insight: The n - 1 gaps add up to hi - lo, so the largest is at least w = ceil((hi - lo) / (n - 1)). Put each value in bucket (x - lo) // w (about n buckets): two values in the same bucket differ by less than w, so the answer is a jump from one non-empty bucket's maximum to the next non-empty bucket's minimum. Store only each bucket's min and max.
  cost: O(n) time, O(n) space
- 493 core
  pattern: sorting-merge
  cue: Count pairs i < j with nums[i] > 2 * nums[j] in an array of up to 50,000 values.
  hint: Merge sort already brings the left half and the right half together in sorted order. What can you count cheaply when both halves are sorted?
  insight: Inside merge sort, before merging two sorted halves, sweep j over the right half while a pointer over the left half finds the first left value > 2 * right[j]; every left value from there on pairs with right[j]. The pointer only moves forward, so counting is O(n) per level; then merge normally. Do not count inside the merge loop: its order is by a[i] > a[j], not 2 * a[j].
  cost: O(n log n) time, O(n) space
- 324 stretch
  pattern: sorting-partition
  cue: Reorder so that nums[0] < nums[1] > nums[2] < nums[3]..., with repeated values allowed.
  hint: Split the values into a small half and a large half. Where must copies of the median go so that they never touch?
  insight: Sort a copy; fill the even indices with the small half in reverse and the odd indices with the large half in reverse, so copies of the median end up at opposite ends and never become neighbours. The O(n) time version finds the median by quickselect and places values with a three-way partition over "virtual" indices (1, 3, 5, ..., 0, 2, 4, ...).
  cost: O(n log n) time and O(n) space with sorting; O(n) expected time, O(1) extra space with quickselect and virtual indexing
- hr:ctci-merge-sort stretch
  pattern: sorting-merge
  cue: Count how many adjacent swaps insertion sort would make, for arrays of up to 100,000 elements and several test cases.
  hint: Each adjacent swap fixes exactly one pair that is out of order. How can merge sort count those pairs in bulk?
  insight: The answer is the number of inversions. During merge sort, whenever an element is taken from the right half while left[i:] remains, add len(left) - i. Ties must take from the left, or equal values are counted as inversions. Use Python ints (the total can exceed 2^31).
  cost: O(n log n) time, O(n) space
