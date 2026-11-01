---
key: bsearch
name: Binary search and searching the answer
stage: scan
summary: One invariant-driven template for sorted arrays, rotated arrays, peaks, answer ranges and implicit search spaces, plus the edge cases and tests that make it trustworthy.
why: Binary search turns a billion candidates into thirty questions, but only if the loop is right, and hand-written versions are famously easy to get subtly wrong. Framing every search as "the first point where a monotone predicate turns True" gives one template for lower and upper bounds, rotated arrays, capacity planning and k-th smallest queries, and one invariant to prove it. The same loop runs in production: git bisect finds the commit that broke a build, LevelDB binary-searches index blocks and restart points to find a key on disk, and load tests search for the highest request rate a service can sustain.
outcomes:
- Write first_true from memory and prove it with the invariant "left of lo is False, from hi on is True"
- Express exact search, first and last occurrence, counts and insertion points as predicates, and use bisect (with key=) for them
- Find the rotation point, search a rotated array and find a peak in O(log n)
- Solve minimise-the-maximum and maximise-the-minimum problems by searching the answer with a greedy feasibility check
- Find the k-th smallest of an implicit set by counting, and the median of two sorted arrays by searching a cut
- Test a binary search exhaustively on small inputs and avoid float, overflow and infinite-loop bugs
cues:
- Sorted or rotated sorted input, and limits that want O(log n) per query
- "Minimise the maximum", "maximise the minimum", "smallest speed, capacity or day such that"
- A yes/no condition that stays true once it becomes true as a number grows
- An answer range up to 10^9 or 10^18, far too big to scan, or "k-th smallest" over n^2 items you cannot list
traps:
- Mixing closed [lo, hi] and half-open [lo, hi) conventions, which loops forever or skips the answer
- Binary searching a predicate that is not monotone (unsorted key, "exactly k" instead of "at most k", duplicates in a rotated array)
- Answer bounds that are too tight (a capacity below the heaviest package) or a check that divides by zero
- Comparing floats for equality instead of running a fixed number of halvings
systems:
- git bisect binary-searches commit history for the first bad commit; git bisect run turns a test script's exit code into the predicate
- LevelDB binary-searches an SSTable's index block to pick a data block, then the block's restart points, then scans forward
- Git pack index (.idx) files put a 256-entry fan-out table on the first byte of the object name in front of a binary search over sorted names
- Python's C-accelerated bisect module and C++ std::lower_bound / std::upper_bound are the standard-library forms of the template
further:
- Article · 15 min | USACO Guide: binary search on monotonic functions | https://usaco.guide/silver/binary-search#binary-search-on-monotonic-functions
- Article · 10 min | cp-algorithms: binary search on the answer, and continuous search | https://cp-algorithms.com/num_methods/binary_search.html#binary-search-on-the-answer
- Article · 5 min | Joshua Bloch: nearly all binary searches and mergesorts are broken | https://research.google/blog/extra-extra-read-all-about-it-nearly-all-binary-searches-and-mergesorts-are-broken/
bank: bsearch answer
---

=== recap | Binary search as an invariant | 12 min
goal: Write a binary search that is right first time by keeping one invariant, and turn any "first index where" question into one call
tag: bsearch-boundary | First true: lower and upper bound
link: Python docs: bisect, Searching Sorted Lists | https://docs.python.org/3/library/bisect.html#searching-sorted-lists | 5 min: the recipes index, find_lt, find_le, find_gt and find_ge, each a one-line wrapper around bisect_left or bisect_right
link: cp-algorithms: search on an arbitrary predicate | https://cp-algorithms.com/num_methods/binary_search.html#search-on-arbitrary-predicate | 5 min: the same invariant written with sentinels l = -1 and r = n, a style you will meet in contest code
practice: 35, 34

> [!key]
> Binary search finds a **boundary**, not a value. Phrase the question as "the first index where a monotone predicate becomes True", keep the invariant *everything left of lo is False and everything from hi on is True*, and halve the unknown middle. One template then answers exact search, insertion points, first and last occurrence and "smallest x that works".

## Internals

**The invariant.** Let `pred` be False ... False True ... True on [lo, hi). The loop keeps: indices below lo are False, indices from hi on are True (or past the end), and only [lo, hi) is unknown. If `pred(mid)` is True, the first True is at mid or to its left, so `hi = mid` keeps it. If False, mid and everything left of it are out, so `lo = mid + 1`. Because `lo <= mid < hi`, both branches shrink the range, so the loop ends after at most ceil(log2(n + 1)) probes: **O(log n) time, O(1) space**, times the cost of `pred`. When `lo == hi` nothing is unknown and lo is the boundary (hi itself means "never True").

**What bisect really is.** `bisect_left(a, x)` is the first i with `a[i] >= x`; `bisect_right(a, x)` is the first i with `a[i] > x`. Near its end, `Lib/bisect.py` imports the C module `_bisect`, whose functions replace the Python ones, so they beat any hand-written loop. They call only `<` (never `==`), take `lo` and `hi`, and since Python 3.10 take `key=`, applied to the elements but not to x. `insort` is O(n): the search is O(log n) but `list.insert` shifts the tail. C++ spells them `std::lower_bound` and `std::upper_bound`.

| Question | Predicate for first_true | Answer |
|---|---|---|
| Is x present? First occurrence? | `a[i] >= x` | i, if i < n and a[i] == x |
| Last occurrence | `a[i] > x` | i - 1, if i > 0 and a[i - 1] == x |
| How many x? | both | upper - lower |
| Last index with a[i] < x | `a[i] >= x` | i - 1 (-1 means none) |

## Template

```python
def first_true(lo, hi, pred):
    """Smallest x in [lo, hi) with pred(x) True, or hi if there is none.
    pred must be monotone on [lo, hi): False ... False True ... True."""
    while lo < hi:
        mid = (lo + hi) // 2
        if pred(mid):
            hi = mid          # mid may be the answer: keep it
        else:
            lo = mid + 1      # mid is not the answer: drop it
    return lo


def lower_bound(a, x):        # same as bisect.bisect_left(a, x)
    return first_true(0, len(a), lambda i: a[i] >= x)


def upper_bound(a, x):        # same as bisect.bisect_right(a, x)
    return first_true(0, len(a), lambda i: a[i] > x)


def last_true(lo, hi, pred):
    """Largest x in [lo, hi) with pred(x) True, or lo - 1 if there is none.
    pred must be True ... True False ... False."""
    return first_true(lo, hi, lambda x: not pred(x)) - 1
```

## Worked example

Insertion point of 23 in ten sorted numbers. Column 10 is "past the end", where hi starts.

```steps
lo = 0, hi = 10, m = 5: a[5] = 23 >= 23 is True, so the answer is 5 or left of it: hi = 5
    i         0    1    2    3    4    5    6    7    8    9   10
    a         2    5    8   12   16   {{23}}   38   56   72   91
             lo                        m                       hi
---
lo = 0, hi = 5, m = 2: a[2] = 8 >= 23 is False, so drop indices 0 to 2: lo = 3
    i         0    1    2    3    4    5    6    7    8    9   10
    a         2    5    {{8}}   12   16   23   38   56   72   91
             lo         m              hi
---
lo = 3, hi = 5, m = 4: a[4] = 16 >= 23 is False: lo = 5
    i         0    1    2    3    4    5    6    7    8    9   10
    a         2    5    8   12   {{16}}   23   38   56   72   91
                            lo    m   hi
---
lo = hi = 5: nothing is unknown, so the answer is index 5 (three probes, not six)
    i         0    1    2    3    4    5    6    7    8    9   10
    a         2    5    8   12   16   {{23}}   38   56   72   91
                                   lo,hi
```

## Pitfalls

- **Non-monotone predicate.** Binary search silently returns garbage if the list is not sorted by the key you compare or the condition can flip back. Write down the F...FT...T shape before coding.
- **`lo = mid` with a floor midpoint** never moves when hi = lo + 1: an infinite loop. The template never writes it. If you want the last True directly, use the upper midpoint `(lo + hi + 1) // 2` with `lo = mid` and `hi = mid - 1` (LevelDB does exactly this), or negate the predicate as `last_true` does.
- **Mixed conventions.** `while lo <= hi` (closed range) together with `hi = mid` (half-open update) hangs as soon as lo == hi and the predicate is True.
- **Overflow elsewhere.** In C++ or Java, `(lo + hi) / 2` overflows near 2^31; write `lo + (hi - lo) / 2`. Python integers do not overflow.
- **Claiming a match.** `lower_bound` returns where x *would* go; check `i < len(a) and a[i] == x` first.

## Quick check

Q: For a = [1, 3, 3, 3, 8], what do `lower_bound(a, 3)` and `upper_bound(a, 3)` return, and how many 3s are there?
A: 1 and 4: the first index with a value >= 3 is 1, the first with a value > 3 is 4 (the 8). The count is 4 - 1 = 3.

Q: You need the largest r with r * r <= n for n up to 10^18. Write it with the template and say how many probes it takes.
A: `first_true(0, n + 2, lambda r: r * r > n) - 1`. Squares grow with r, so the predicate is monotone; the range has about 10^18 values, so about 60 probes. (In real code, `math.isqrt(n)`.)

> [!know]
> You now know how to turn any "first index where" question into one monotone predicate and one proven loop, and when bisect does it for you.

=== recap | Rotated arrays and peaks | 12 min
goal: Find the rotation point, search a rotated sorted array and find a peak in O(log n) with the same first_true template
tag: bsearch-rotated | Rotated arrays and peaks
link: MIT 6.006 (Fall 2011), lecture 1 notes: peak finding | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/c32185c7158955425455159a8455298b_MIT6_006F11_lec01.pdf | 10 min: pages 2 and 3, 'One-dimensional Version' (the divide and conquer peak finder and its log2 n recurrence); page 4 shows why the naive 2D extension fails
practice: 153, 33, 162

> [!key]
> A rotated sorted array is not sorted, but `a[i] <= a[-1]` is still False ... False True ... True, so the rotation point is one first_true call away; after that both halves are sorted and lower_bound finishes the search. A peak needs no monotone predicate at all, only an invariant that survives halving: "a peak lies in [lo, hi]".

## Internals

**The rotation point.** Take distinct values rotated at k, such as [15, 18, 22, 27, 31, 2, 5, 9, 12] with k = 5. Every element of the left block a[:k] is greater than the last element, and every element of the right block a[k:] is at most the last element. So `pred(i) = a[i] <= a[-1]` is monotone and the minimum sits at `first_true(0, n, pred)`. Compare with the **last** element, not the first: on an unrotated array the predicate is all True and correctly returns 0, with no special case.

**Searching.** If target <= a[-1] it can only be in the right block [k, n), otherwise only in the left block [0, k). Two O(log n) searches, each a plain lower_bound. The popular one-pass alternative compares a[lo] with a[mid] to learn which half is sorted, then asks whether the target lies inside that half's range. It costs the same but has four branches to get wrong; the two-step version reuses code you have already tested.

**Duplicates.** With repeats, the predicate can break: [1, 1, 2, 0, 1] gives T T F T T. When a[mid] equals a[hi] you cannot tell which side the drop is on, so drop hi (`hi -= 1`) and continue. The worst case becomes O(n), and that is unavoidable: finding one 0 among many 1s needs a look at every cell.

**Peaks.** A peak is larger than its neighbours, with -infinity outside the array and adjacent values distinct. Keep the invariant: a[lo - 1] < a[lo] (or lo = 0) and a[hi] > a[hi + 1] (or hi = n - 1). Climbing right from lo you must come down by hi, so a peak lies in [lo, hi]. If a[mid] > a[mid + 1], `hi = mid` keeps the right-hand condition; otherwise `lo = mid + 1` keeps the left-hand one. The predicate `a[i] > a[i + 1]` is *not* monotone ([1, 3, 2, 4, 1] gives F T F T), yet the loop still lands on a peak. Monotonicity is the commonest invariant, not the only one.

## Template

```python
def find_min_rotated(a):
    """Index of the minimum of a rotated sorted list of distinct values."""
    last = a[-1]
    return first_true(0, len(a), lambda i: a[i] <= last)


def search_rotated(a, target):
    """Index of target in a rotated sorted list of distinct values, or -1."""
    if not a:
        return -1
    k = find_min_rotated(a)                  # a[k:] and a[:k] are each sorted
    lo, hi = (k, len(a)) if target <= a[-1] else (0, k)
    i = first_true(lo, hi, lambda j: a[j] >= target)
    return i if i < hi and a[i] == target else -1


def find_peak(a):
    """Index of an element larger than its neighbours (adjacent values differ)."""
    return first_true(0, len(a) - 1, lambda i: a[i] > a[i + 1])
```

## Worked example

Search for 5 in a rotated array: first find the rotation point, then search the block that can hold 5.

```steps
Phase 1, find k. lo = 0, hi = 9, m = 4: a[4] = 31 <= 12 (the last value) is False: lo = 5
    i         0    1    2    3    4    5    6    7    8    9
    a        15   18   22   27   {{31}}    2    5    9   12
             lo                   m                       hi
---
lo = 5, hi = 9, m = 7: a[7] = 9 <= 12 is True: hi = 7
    i         0    1    2    3    4    5    6    7    8    9
    a        15   18   22   27   31    2    5    {{9}}   12
                                      lo         m        hi
---
lo = 5, hi = 7, m = 6: a[6] = 5 <= 12 is True: hi = 6
    i         0    1    2    3    4    5    6    7    8    9
    a        15   18   22   27   31    2    {{5}}    9   12
                                      lo    m   hi
---
lo = 5, hi = 6, m = 5: a[5] = 2 <= 12 is True: hi = 5, so k = 5 (the minimum, 2)
    i         0    1    2    3    4    5    6    7    8    9
    a        15   18   22   27   31    {{2}}    5    9   12
                                    lo,m   hi
---
Phase 2: 5 <= 12, so search only [5, 9). m = 7: a[7] = 9 >= 5 is True: hi = 7
    i         0    1    2    3    4    5    6    7    8    9
    a        15   18   22   27   31    2    5    {{9}}   12
                                      lo         m        hi
---
lo = 5, hi = 7, m = 6: a[6] = 5 >= 5 is True: hi = 6
    i         0    1    2    3    4    5    6    7    8    9
    a        15   18   22   27   31    2    {{5}}    9   12
                                      lo    m   hi
---
lo = 5, hi = 6, m = 5: a[5] = 2 >= 5 is False: lo = 6 = hi. a[6] == 5, so return 6
    i         0    1    2    3    4    5    6    7    8    9
    a        15   18   22   27   31    2    {{5}}    9   12
                                        lo,hi
```

## Pitfalls

- Comparing with a[0] instead of a[-1] needs a special case for the unrotated array.
- Duplicates (LeetCode 154 and 81) break the predicate; shrink by one on ties and accept O(n) in the worst case.
- The peak search runs over [0, n - 1) so that `a[i + 1]` exists; a one-element list returns 0 without a probe.
- In the one-pass version, test `a[lo] <= a[mid]` with `<=`: when lo == mid the "left half" is one element and is sorted.

## Quick check

Q: In [15, 18, 22, 27, 31, 2, 5, 9, 12], which block does `search_rotated` search for 27, and what does it return?
A: 27 > a[-1] = 12, so only the left block [0, 5); lower_bound there finds index 3, and a[3] == 27, so it returns 3.

Q: What does `find_peak([1, 3, 2, 4, 1])` return, and is it the first peak?
A: 3 (the value 4). The range is [0, 4): m = 2, and 2 > 4 is False, so lo = 3; m = 3, and 4 > 1 is True, so hi = 3; the loop ends at 3. Index 1 (the value 3) is also a peak: the search returns *a* peak, not necessarily the first.

> [!know]
> You now know how to find a hidden boundary in arrays that are not sorted, and why an invariant, not sortedness, is what binary search needs.

=== recap | Binary search on the answer | 14 min
goal: Solve "smallest value that works" and "largest value that works" problems by searching the answer range with a greedy feasibility check
tag: bsearch-answer | Search the answer with a feasibility check
link: USACO Guide: binary search on monotonic functions | https://usaco.guide/silver/binary-search#binary-search-on-monotonic-functions | 15 min: 'Finding the maximum x such that f(x) = true', 'Finding the minimum x such that f(x) = true', then 'Common Mistakes' (off by one, negative bounds, overflow)
practice: 875, 1011, 410

> [!key]
> When a problem asks for the smallest value that works (or the largest) and "works" is monotone in that value, search the **answer range** instead of an array. Each probe runs a feasibility check, usually a greedy O(n) simulation, so the total is O(n log range). "Minimise the maximum" and "maximise the minimum" are the classic signals.

## Internals

**Monotonicity is the proof.** If a ship of capacity c delivers every package within d days, a ship of capacity c + 1 can follow exactly the same plan. So `ok(c)` is False ... False True ... True and the answer is `first_true` over capacities. When maximising (the largest gap that still lets you place m balls), `ok` is True ... True False ... False: the answer is the first failure minus one, which is `last_true`.

**Bounds.** lo is the smallest value that could possibly work, hi a value that surely works. For shipping: lo = max(weights), because a smaller ship cannot carry the heaviest package, and hi = sum(weights), one day for everything. For eating speed: lo = 1 (0 divides by zero), hi = max(piles), one hour per pile. Pass `hi + 1` because the template is half-open. If no answer may exist, check `ok(hi)` first and report failure (LeetCode 1482 returns -1 when m * k > n).

**Why the greedy check is exact.** For a fixed capacity, "load each day until the next package would overflow, then start a new day" uses the fewest days. Exchange argument: take any valid plan; if its first day carries fewer packages than greedy's, move packages from the start of day 2 onto day 1 (they fit, because greedy fitted them). Days never increase, and repeating day by day turns the plan into greedy's. So if greedy needs more than d days, no plan fits in d. Split Array Largest Sum (410) is the same check with "parts" instead of "days".

**Cost.** log2(range) probes, each O(n). Piles up to 10^9 means about 30 probes. Ranges can reach 10^14 (minimum time for a total number of trips, where hi = min(time) * totalTrips), about 47 probes: fine in Python, but C++ needs `long long`.

## Template

```python
def ship_within_days(weights, days):
    """Least capacity that ships the packages, in order, within `days` days."""
    def days_needed(cap):
        used, load = 1, 0
        for w in weights:
            if load + w > cap:            # the next package starts a new day
                used, load = used + 1, 0
            load += w
        return used
    lo, hi = max(weights), sum(weights)   # hi always works: everything in one day
    return first_true(lo, hi + 1, lambda cap: days_needed(cap) <= days)


def min_eating_speed(piles, h):
    """Least integer speed k that finishes every pile within h hours."""
    hours = lambda k: sum((p + k - 1) // k for p in piles)   # exact ceil division
    return first_true(1, max(piles) + 1, lambda k: hours(k) <= h)


def max_min_gap(positions, m):
    """Largest d such that m of the positions can be chosen at least d apart (m >= 2)."""
    p = sorted(positions)
    def fits(d):                          # greedy: take each position as early as possible
        count, last = 1, p[0]
        for x in p[1:]:
            if x - last >= d:
                count, last = count + 1, x
        return count >= m
    return last_true(1, p[-1] - p[0] + 1, fits)
```

## Worked example

Ship weights 1, 2, ..., 10 within 5 days. Each probe is one greedy pass.

```steps
lo = 10 (heaviest package), hi = 56 (sum + 1). Try 33: two days, 2 <= 5 works: hi = 33
    capacity 33: [1..7] = 28 | [8, 9, 10] = 27
    days used:   {{2}}
    unknown:     [10, 56) -> [10, 33)
---
Try 21: three days, works: hi = 21
    capacity 21: [1..6] = 21 | [7, 8] = 15 | [9, 10] = 19
    days used:   {{3}}
    unknown:     [10, 33) -> [10, 21)
---
Try 15: exactly five days, works: hi = 15
    capacity 15: [1..5] = 15 | [6, 7] = 13 | [8] | [9] | [10]
    days used:   {{5}}
    unknown:     [10, 21) -> [10, 15)
---
Try 12: six days, too many: lo = 13
    capacity 12: [1..4] = 10 | [5, 6] = 11 | [7] | [8] | [9] | [10]
    days used:   {{6}}
    unknown:     [10, 15) -> [13, 15)
---
Try 14: still six days: lo = 15 = hi, so the answer is 15
    capacity 14: [1..4] = 10 | [5, 6] = 11 | [7] | [8] | [9] | [10]
    days used:   {{6}}
    unknown:     [13, 15) -> empty, answer {{15}}
```

## Pitfalls

- **lo too small breaks the check**, not just the range: with a capacity below the heaviest package, `days_needed` puts that package on a day of its own and undercounts.
- **Ceil division** as `(p + k - 1) // k` or `-(-p // k)`; `math.ceil(p / k)` goes through a float and can be off for values above 2^53.
- **A check that is not monotone.** "Exactly d days" is not monotone; ask "at most d days".
- **Maximising with first_true** directly returns the first failure: subtract one, or use `last_true`.

## Quick check

Q: With capacity 14, how does the greedy check load weights 1 to 10, and why does that rule out 14?
A: Days carry 1+2+3+4 = 10, 5+6 = 11, 7, 8, 9 and 10: six days. Greedy uses the fewest days for a capacity, so no plan with capacity 14 fits in five.

Q: Koko has piles [3, 6, 7, 11] and h = 8. What does `min_eating_speed` return?
A: 4. At speed 4 the hours are 1 + 2 + 2 + 3 = 8 <= 8; at speed 3 they are 1 + 2 + 3 + 4 = 10 > 8.

> [!know]
> You now know how to recognise a monotone "does x work?" question, bound it safely and solve it with O(log range) greedy checks.

=== recap | Implicit search spaces: counting and cuts | 14 min
goal: Binary search spaces that are never stored: a matrix as a flat list, the k-th smallest of n^2 values by counting, and the median of two sorted arrays by searching a cut
tag: bsearch-implicit | Implicit spaces: k-th by counting and cuts
link: USACO Guide: Example, Maximum Median | https://usaco.guide/silver/binary-search#example---maximum-median | 10 min: an answer search whose check counts how many operations a candidate median needs, the same "count, then compare with k" shape as this card
practice: 719, 4

> [!key]
> The thing you binary-search need not exist in memory. A matrix whose rows continue each other is a sorted list under index arithmetic. The k-th smallest of n^2 pair distances is the first value d with count(<= d) >= k. The median of two sorted arrays is the first cut where the left parts stop overlapping the right parts. Each needs only a monotone predicate you can evaluate fast.

## Internals

**Index arithmetic (LeetCode 74).** An m x n matrix in which every row starts after the previous row ends is one sorted list of length mn: position k lives at row `k // n`, column `k % n`. Search [0, mn) directly with no copying.

**k-th smallest by counting.** Let count(d) be the number of items <= d. It never decreases as d grows, so the first d with count(d) >= k is the k-th smallest. That d is always a real item: count only changes at item values, so the first d to reach k is one of them, and no "is it present?" check is needed. The work moves into count: for pair distances, sort once, then a two-pointer sweep counts pairs with a[j] - a[i] <= d in O(n) (for each j, i only moves right). For a multiplication table, row i contributes min(d // i, n). Total O(n log n + n log W), where W is the value range.

**A cut, not a value (LeetCode 4).** Put the first i elements of the shorter array A and the first j = half - i elements of B on the left, with half = (m + n + 1) // 2. The cut is right when A[i - 1] <= B[j] and B[j - 1] <= A[i]. As i grows, A[i] grows and B[j - 1] shrinks, so `ok(i) = A[i] >= B[j - 1]` (True when either side runs out) is monotone. first_true finds the smallest such i, and since ok(i - 1) failed, A[i - 1] < B[j]: the other condition holds too. O(log min(m, n)), with no merging.

## Template

```python
def kth_smallest_distance(nums, k):
    """k-th smallest |a - b| over all pairs (1-based k)."""
    a = sorted(nums)
    def pairs_within(d):                  # pairs i < j with a[j] - a[i] <= d
        count, i = 0, 0
        for j in range(len(a)):
            while a[j] - a[i] > d:
                i += 1
            count += j - i
        return count
    return first_true(0, a[-1] - a[0] + 1, lambda d: pairs_within(d) >= k)


def median_two_sorted(A, B):
    if len(A) > len(B):
        A, B = B, A                       # search the shorter array
    m, n = len(A), len(B)
    half = (m + n + 1) // 2               # size of the left part
    def ok(i):
        j = half - i
        return i == m or j == 0 or A[i] >= B[j - 1]
    i = first_true(0, m + 1, ok)
    j = half - i
    left = max(A[i - 1] if i > 0 else float("-inf"), B[j - 1] if j > 0 else float("-inf"))
    if (m + n) % 2:
        return left
    right = min(A[i] if i < m else float("inf"), B[j] if j < n else float("inf"))
    return (left + right) / 2
```

## Worked example

The 4th smallest pair distance of [1, 3, 4, 8]. The six distances are listed only to show what each count means; the algorithm never builds them.

```steps
Range [0, 8). Try d = 4: pairs within 4 are (1,3), (1,4), (3,4), (4,8), count 4 >= 4: hi = 4
    distances, never built:  {{1  2  3  4}}  5  7
    count(4) = {{4}}, unknown [0, 8) -> [0, 4)
---
Try d = 2: only (1,3) and (3,4), count 2 < 4: lo = 3
    distances, never built:  {{1  2}}  3  4  5  7
    count(2) = {{2}}, unknown [0, 4) -> [3, 4)
---
Try d = 3: (1,3), (1,4), (3,4), count 3 < 4: lo = 4
    distances, never built:  {{1  2  3}}  4  5  7
    count(3) = {{3}}, unknown [3, 4) -> [4, 4)
---
lo = hi = 4: the 4th smallest distance is 4, an actual distance (4 to 8)
    distances, never built:  1  2  3  {{4}}  5  7
```

## Pitfalls

- **`<` against `<=` in the count.** count(d) must count items <= d; counting < d returns the next value up.
- **Stopping when count == k.** A probe with count == k may not be an item value. Let first_true finish.
- **Median: search the shorter array**, or j can go negative; and pick `half = (m + n + 1) // 2` so the left part holds the middle element when the total is odd.
- **Sentinels:** use infinities for missing neighbours, and return a float for even totals.

## Quick check

Q: In `pairs_within`, why is the sweep O(n) even though it has a nested while loop?
A: i only moves right and never passes j, so across the whole loop it advances at most n times: each element enters and leaves the window once.

Q: For A = [1, 3] and B = [2], which cut does `median_two_sorted` choose and what does it return?
A: The arrays are swapped first, so A = [2] (the shorter) and B = [1, 3], with half = 2. ok(1) is True (i == m); ok(0) has j = 2 and asks 2 >= B[1] = 3, which is False. So i = 1, j = 1: the left part is {2, 1}, its maximum is 2, and the total of three is odd, so the median is 2.

> [!know]
> You now know how to binary-search spaces you never materialise: by index arithmetic, by counting, or by searching a cut.

=== recap | Floats, overflow, exhaustive tests and production uses | 12 min
goal: Make binary searches trustworthy with fixed iterations, overflow-safe midpoints and exhaustive small tests, and recognise the loop in git, LevelDB and Git pack files
link: Git docs: git bisect run | https://git-scm.com/docs/git-bisect#_bisect_run | 5 min: the exit-code contract (0 good, 1 to 127 bad, 125 skip) and why a test script must be reliable before you automate bisection

> [!key]
> Three habits make binary search trustworthy: on real numbers run a fixed number of halvings instead of testing equality; in fixed-width languages compute the midpoint without overflow; and test every small sorted array against bisect, because the bugs live at sizes 0, 1 and 2. Production systems run the same loop over commits, index blocks and pack files.

## Internals

**Real-valued answers.** Floats do not "meet": `while hi - lo > eps` can spin forever when eps is smaller than the gap between adjacent doubles near the answer. Loop a fixed number of times instead: each halving gains one bit, and a double has a 53-bit significand, so 100 iterations exhaust any range. For integer roots avoid floats entirely: `int(math.sqrt(10**16 - 1))` is 100000000, one too many, while `math.isqrt` is exact for any size.

**Overflow.** In Java or C++, `(lo + hi) / 2` overflows once lo + hi passes 2^31 - 1. Java's own `Arrays.binarySearch` carried that bug for about nine years until it broke a real program; Joshua Bloch, its author, wrote it up in 2006. Write `lo + (hi - lo) / 2`.

**Exhaustive tests.** Every non-decreasing list of length 0 to 6 over the values 0 to 3, probed with x from -1 to 4, is only 1,260 cases and runs in milliseconds. The common mutants (a closed loop with `hi = mid`, `lo = mid`, or `hi = len(a) - 1`) all fail on a one-element list.

**In production.**

- **git bisect** binary-searches history for the first bad commit. The predicate "this commit is bad" must be monotone: once broken, broken. `git bisect run cmd` uses the exit code: 0 means good, 1 to 127 except 125 means bad, and 125 means "cannot test, skip". A thousand commits take about ten builds.
- **LevelDB.** An SSTable's index block has one entry per data block (a key at or above that block's last key), and a lookup binary-searches it to choose the block. Inside the block, `Block::Iter::Seek` binary-searches the restart array for the *last* restart point whose key is below the target, using the upper midpoint `(left + right + 1) / 2` with `left = mid`, then scans forward.
- **Git pack indexes.** A `.idx` file starts with a 256-entry fan-out table: entry b counts the objects whose name starts with a byte <= b, so the first byte narrows the range before a binary search over sorted names, stored "without offset values to reduce the cache footprint of the binary search".

## Template

```python
def boundary_real(lo, hi, ok, iterations=100):
    """Approximate the point where ok flips from False to True on [lo, hi]."""
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi


from bisect import bisect_left, bisect_right
from itertools import combinations_with_replacement


def check_all(lower, upper, max_n=6, max_value=3):
    """Compare lower/upper bound functions with bisect on every small sorted list."""
    for n in range(max_n + 1):
        for a in map(list, combinations_with_replacement(range(max_value + 1), n)):
            for x in range(-1, max_value + 2):          # below, inside and above
                assert lower(a, x) == bisect_left(a, x), ("lower", a, x)
                assert upper(a, x) == bisect_right(a, x), ("upper", a, x)
```

## Worked example

LevelDB's last-key-below-target search over the first keys of six restart points, looking for "fox". L and R are `left` and `right` (both inclusive).

```steps
left = 0, right = 5, mid = (0 + 5 + 1) // 2 = 3: "gnu" < "fox" is False, so right = mid - 1 = 2
    i         0    1    2    3    4    5
    key     ant  cat  eel  {{gnu}}  owl  yak
              L              m         R
---
left = 0, right = 2, mid = 1: "cat" < "fox" is True, so left = mid = 1
    i         0    1    2    3    4    5
    key     ant  {{cat}}  eel  gnu  owl  yak
              L    m    R
---
left = 1, right = 2, mid = 2 (rounded up, so left = mid still moves): "eel" < "fox", left = 2
    i         0    1    2    3    4    5
    key     ant  cat  {{eel}}  gnu  owl  yak
                   L  m,R
---
left = right = 2: scan forward from restart point 2 for the first key >= "fox"
    i         0    1    2    3    4    5
    key     ant  cat  {{eel}}  gnu  owl  yak
                      L,R
```

## Pitfalls

- An `eps` loop on floats that never terminates; or floats where exact integers were needed (`math.isqrt`, ceil division).
- Rounding the midpoint down while assigning `left = mid`: rounding up is what makes LevelDB's loop terminate.
- A flaky test inside `git bisect run` breaks monotonicity and blames the wrong commit; exit 125 for "cannot tell".
- Testing only random large inputs: binary search bugs hide at n = 0, 1 and 2, which random tests rarely hit.

## Quick check

Q: `boundary_real(0, 2, lambda x: x ** 3 >= 2)` returns about what, and why is a fixed count safe where `while hi - lo > 1e-18` is not?
A: About 1.2599210498948732, the cube root of 2. After about 53 halvings lo and hi are adjacent doubles and the midpoint equals one of them, so the gap stops shrinking: a 1e-18 tolerance would loop forever, while a fixed count simply stops.

> [!know]
> You now know how to make a binary search terminate on floats, survive fixed-width integers and pass an exhaustive test, and where the same loop runs in real systems.

=== lab | Binary search torture test | 45 min
goal: Prove your bounds functions against bisect exhaustively and at scale, watch the tester catch planted bugs, then find a service's capacity by searching the answer
link: Python docs: bisect functions | https://docs.python.org/3/library/bisect.html#bisect-functions | 5 min: the exact partition contracts of bisect_left and bisect_right (all(elem < x ...) on the left slice), which are the properties your tests check

## Steps

1. **Write the code under test.** In `bsearch_lab.py`, write `first_true`, `lower_bound` and `upper_bound` from memory (no peeking), plus `check_all` from the previous card.
2. **Exhaustive check.** Run `check_all(lower_bound, upper_bound)`. Count the cases it runs.
3. **Random check at scale.** For 2,000 trials, build sorted lists of random length up to 1,000 (every hundredth trial up to 100,000) with many duplicates, pick x inside and outside the value range, and compare with `bisect`.
4. **Count probes.** Wrap the predicate in a counter and assert the number of calls never exceeds `math.ceil(math.log2(n + 1))` for n from 0 to 200 and every x. What is the bound for n = 100,000?
5. **Plant three bugs** and let the exhaustive tester find the smallest failing input for each (stop a mutant after 100 iterations and report a hang): (a) `while lo <= hi` with `hi = len(a) - 1` and `hi = mid`; (b) `lo = mid` instead of `lo = mid + 1`; (c) `hi = len(a) - 1` with the half-open loop.
6. **Capacity planning by searching the answer.** Paste this simulator of a one-worker service:

```python
import random


def p99_latency_ms(rate, n=20_000, seed=7):
    """p99 latency in ms of a one-worker FIFO service receiving `rate` requests/s.
    The random draws are fixed by the seed, so a higher rate only shrinks the gaps."""
    rng = random.Random(seed)
    base_gaps = [rng.expovariate(1.0) for _ in range(n)]          # mean 1, scaled below
    service = [rng.uniform(0.5, 1.5) / 1000 for _ in range(n)]    # 0.5 to 1.5 ms
    wait, prev_service, latencies = 0.0, 0.0, []
    for g, s in zip(base_gaps, service):
        wait = max(0.0, wait + prev_service - g / rate)           # Lindley's recurrence
        latencies.append((wait + s) * 1000)
        prev_service = s
    latencies.sort()
    return latencies[int(0.99 * n) - 1]
```

   Find the highest whole rate in [1, 1000) whose p99 latency is at most 10 ms, using `last_true`. Count the simulations. Then find it again with a linear scan from 1 and count those.

7. **Explain the monotonicity.** Why does a fixed seed make "p99 <= 10 ms" monotone in the rate, and what would happen to the search with a fresh random seed per call?

## What you should see

- The exhaustive check runs **1,260 cases** and passes; the random check passes too.
- No search makes more than ceil(log2(n + 1)) probes; for n = 100,000 the bound is **17**.
- Each mutant fails on a **one-element list**: (a) hangs on `[0]` with x = -1, (b) hangs on `[0]` with x = 1, (c) returns 0 instead of 1 for `[0]` with x = 1 (it can never answer "after the end").
- The highest rate is **754 requests/s** (p99 about 10.0 ms; at 755 it is about 10.02 ms). The binary search needs **10 simulations**; the linear scan needs **755**. For reference, p99 is about 4.8 ms at 500 requests/s, 11.8 ms at 800 and 21.5 ms at 900: latency explodes as the rate approaches the service's capacity of about 1,000 requests/s.
- With the seed fixed, every rate sees the same arrivals squeezed closer together, and Lindley's recurrence `wait = max(0, wait + service - gap)` can only grow when gaps shrink, so the predicate is monotone. With a fresh seed per call, noise near the boundary makes the predicate flip back and forth, and binary search may return any rate in the noisy band: real load tests repeat runs or use a fixed replayed trace for this reason.

=== practice
- 35 core
  pattern: bsearch-boundary
  cue: You need the index of a value in a sorted array, or the place it would go if it is missing.
  hint: Ask for the first index whose value is at least the target. What should you return if no index qualifies?
  insight: This is lower_bound: first_true(0, n, lambda i: nums[i] >= target). The invariant (left of lo is smaller, from hi on is at least the target) makes the final lo both the match position and the insertion point; hi = n covers "insert at the end".
  cost: O(log n) time, O(1) space
- 34 core
  pattern: bsearch-boundary
  cue: Sorted array with repeats; you need where a run of equal values starts and where it ends.
  hint: Both ends are boundaries of predicates you already know. Which two predicates, and how do you turn the second one into "last index"?
  insight: start = lower_bound(x) (first a[i] >= x) and end = upper_bound(x) - 1 (first a[i] > x, minus one). If start == n or a[start] != x the value is absent: return [-1, -1]. Two O(log n) searches, no linear walk over the run.
  cost: O(log n) time, O(1) space
- 153 core
  pattern: bsearch-rotated
  cue: A sorted array of distinct values was rotated by an unknown amount; you want its minimum in logarithmic time.
  hint: Compare every element with the last one. Which elements are larger than it, and which are not?
  insight: Elements before the rotation point are all greater than a[-1]; the rest are at most a[-1]. So a[i] <= a[-1] is False...True and the minimum is at first_true(0, n, lambda i: a[i] <= a[-1]). Comparing with the last element also handles the unrotated case.
  cost: O(log n) time, O(1) space
- 33 core
  pattern: bsearch-rotated
  cue: Search for a target in a rotated sorted array of distinct values in O(log n).
  hint: Once you know where the rotation point is, which block can the target possibly be in?
  insight: Find the rotation point k with first_true on a[i] <= a[-1]. If target <= a[-1] it can only be in a[k:], otherwise only in a[:k]; run lower_bound in that block and check equality. (One-pass alternative: whichever of [lo, mid] or [mid, hi] is sorted tells you whether the target is in it.)
  cost: O(log n) time, O(1) space
- 162 derive
  pattern: bsearch-rotated
  cue: Find any element larger than its neighbours in an unsorted array, faster than a scan; outside the array counts as minus infinity.
  hint: Look at a[mid] and a[mid + 1]. If the values rise to the right, what must exist somewhere to the right?
  insight: Keep "a[lo - 1] < a[lo] and a[hi] > a[hi + 1]", which guarantees a peak in [lo, hi]. If a[mid] > a[mid + 1] set hi = mid, else lo = mid + 1: first_true(0, n - 1, lambda i: a[i] > a[i + 1]). The predicate is not monotone; the invariant is what makes halving safe.
  cost: O(log n) time, O(1) space
- 875 core
  pattern: bsearch-answer
  cue: Find the smallest integer rate that finishes all the work within a deadline of h hours.
  hint: If speed k finishes in time, does speed k + 1? What are the smallest and largest speeds worth trying?
  insight: hours(k) = sum(ceil(p / k)) only falls as k grows, so search k in [1, max(piles)] for the first k with hours(k) <= h. Use (p + k - 1) // k for exact ceiling division; max(piles) always works because each pile then takes one hour.
  cost: O(n log max(piles)) time, O(1) space
- 1011 core
  pattern: bsearch-answer
  cue: Packages must ship in their given order within d days; find the least ship capacity.
  hint: Fix a capacity. How would you load the ship to use as few days as possible, and is that check monotone in the capacity?
  insight: Greedy loading (start a new day only when the next package would overflow) uses the fewest days for a capacity, by an exchange argument. Feasibility is monotone, so search capacity in [max(w), sum(w)] for the first value needing <= d days. lo = max(w) matters: below it the greedy count is wrong.
  cost: O(n log sum(w)) time, O(1) space
- 1552 core
  pattern: bsearch-answer
  cue: Place m items at given positions so that the closest pair is as far apart as possible.
  hint: Guess the minimum distance d. Can you check quickly whether m items fit at least d apart? What happens to the answer of that check as d grows?
  insight: Sort; fits(d) places each item at the first position at least d past the previous one (taking the earliest position never hurts later choices). fits is True...False, so the answer is the last d that fits: last_true(1, span + 1, fits).
  cost: O(n log n + n log(span)) time, O(1) extra space
- 410 core
  pattern: bsearch-answer
  cue: Split an array into k contiguous non-empty parts so that the largest part sum is as small as possible.
  hint: Fix an allowed largest sum S. How many parts are you forced to use if you extend each part as long as possible?
  insight: The greedy part count for S never grows when S grows, so search S in [max(a), sum(a)] for the first S needing <= k parts. Using fewer than k parts is fine, because a part can always be split further without raising its sum. Same check as ship capacity.
  cost: O(n log sum(a)) time, O(1) space
- 719 derive
  pattern: bsearch-implicit
  cue: The k-th smallest absolute difference among all pairs, with n up to 10^4 so n^2 pairs cannot be listed.
  hint: You cannot list the distances, but can you count how many are at most d quickly once the array is sorted?
  insight: Sort; count(d) of pairs with a[j] - a[i] <= d is a two-pointer sweep in O(n) because i only moves right. count is monotone, so the first d with count(d) >= k (first_true over [0, max - min]) is the answer, and it is always a real distance.
  cost: O(n log n + n log W) time where W = max - min, O(1) extra space
- 4 stretch
  pattern: bsearch-implicit
  cue: Median of two sorted arrays in logarithmic time, without merging them.
  hint: Do not search for a value. Search for how many elements of the shorter array belong to the lower half.
  insight: With i from A and j = half - i from B on the left (half = (m + n + 1) // 2), the cut is right when A[i - 1] <= B[j] and B[j - 1] <= A[i]. ok(i) = A[i] >= B[j - 1] is monotone in i, so first_true over [0, m] finds the cut; the median is the max of the left side, or the mean of that and the min of the right side.
  cost: O(log min(m, n)) time, O(1) space
- 154 stretch
  pattern: bsearch-rotated
  cue: Minimum of a rotated sorted array that may contain duplicates.
  hint: When a[mid] equals a[hi], can you tell which side of mid the drop is on? Which element can you discard safely anyway?
  insight: Compare a[mid] with a[hi]: greater means the minimum is right of mid (lo = mid + 1), smaller means at mid or left (hi = mid), equal means a[hi] has a copy at mid, so drop it (hi -= 1). Average O(log n), worst case O(n) when almost everything is equal, which no algorithm can beat.
  cost: O(log n) typical, O(n) worst case time, O(1) space
