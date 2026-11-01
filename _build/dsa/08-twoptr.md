---
key: twoptr
name: Two pointers
stage: scan
summary: Move two indices through a sequence so that every step provably discards a candidate that cannot be the answer: pair searches, k-sums, in-place compaction, partitions and merges in one linear pass with O(1) memory.
why: Two pointers is the cheapest optimisation in the toolbox: no extra memory, one pass, and a correctness argument that fits in a sentence. It turns the "try every pair" O(n^2) brute force into O(n) whenever order lets you rule a candidate out for good, and it is how real software merges, joins, compacts and partitions data. Database merge joins, C++'s std::remove_if, quicksort's partition step and Timsort's run merging all walk two indices through memory in order, which is also why they are friendly to CPU caches. The skill to practise is not the loop (it is short) but the argument for each move: once you can say why a discarded index can never be part of an answer, the code writes itself and the off-by-one and duplicate bugs disappear.
outcomes:
- State the discard invariant for opposite-end pointers and prove that each move preserves it
- Count pairs under an inequality in O(n) after sorting, and decide between two pointers, a hash map and sorting
- Write 3Sum and k-sum with duplicate skips that neither lose nor repeat answers, and stress-test them against a brute force
- Compact, de-duplicate and merge arrays in place with read and write pointers, including merging from the back
- Partition in place into two or three regions (Dutch national flag) and explain why three-way partitioning protects quicksort from duplicates
- Solve limiting-side problems (container with most water, trapping rain water) by arguing which side is already settled
cues:
- Sorted input (or sorting is allowed) and a pair, triple or count of pairs meeting a sum or difference condition
- "In place", "O(1) extra space", "keep the relative order of the others": compaction or partition
- A property checked symmetrically from both ends: palindromes, reversals, mirrored comparisons
- Two sorted sequences to merge, intersect or compare, or one array with spare room at its end
- An answer capped by the smaller of two ends, such as water held between two walls
traps:
- Using opposite-end pointers on unsorted data, or sorting when the answer needs the original indices
- Skipping duplicates in the wrong place: a look-ahead skip loses answers, a missing skip repeats them
- Advancing the scan index after swapping in an unexamined value from the right in a three-way partition
- Deleting inside a loop with del or list.remove, which shifts the tail every time and makes the loop O(n^2)
- Moving the taller wall in container problems "because it might help": it never can
systems:
- PostgreSQL's merge join sorts both inputs on the join key and scans them in parallel, one pointer per input; its hash join is the hash-map alternative
- C++'s std::remove_if (the erase-remove idiom) is exactly the read and write pointer loop; std::partition and std::nth_element partition in place
- Quicksort-family sorts and selections (libstdc++'s introsort behind std::sort, NumPy's np.partition introselect) are built on in-place partitioning
- CPython's list.sort (Timsort) merges adjacent sorted runs with one pointer per run, galloping ahead when one run keeps winning
further:
- Chapter · 15 min | Competitive Programmer's Handbook, section 8.1: two pointers method (PDF pages 87-89) | https://cses.fi/book/book.pdf#page=87
- Article · 10 min | Sedgewick and Wayne, algs4 2.3: entropy-optimal sorting with 3-way partitioning | https://algs4.cs.princeton.edu/23quicksort/#:~:text=Entropy-optimal%20sorting
- Docs · 5 min | PostgreSQL docs 51.5.1: nested loop, merge and hash joins | https://www.postgresql.org/docs/current/planner-optimizer.html#PLANNER-OPTIMIZER-GENERATING-POSSIBLE-PLANS
bank: twoptr
---

=== recap | Opposite ends: pair sum and the discard argument | 12 min
goal: Find a pair with a target sum in a sorted array in O(n), prove that no move skips the answer, and count pairs under an inequality the same way
tag: twoptr-ends | Opposite-end pointers
link: USACO Guide: Two Pointers | https://usaco.guide/silver/two-pointers#sum-of-two-values | 5 min: the 'Sum of Two Values' section, the same scan on a CSES problem where the original indices must survive the sort
practice: 167, 881, 611

> [!key]
> Sort, put `lo` on the smallest value and `hi` on the largest, and look at `a[lo] + a[hi]`. Too small means `a[lo]` cannot reach the target even with the biggest partner left, so drop it; too big means `a[hi]` overshoots even with the smallest, so drop it. Every probe discards one index for good: at most n - 1 probes and O(1) memory.

## Internals

**Invariant: if a solution pair exists, both of its indices lie in `[lo, hi]`.** It holds at the start. If `a[lo] + a[hi] < target`, then for every `k` in `(lo, hi]`, `a[lo] + a[k] <= a[lo] + a[hi] < target`, so `lo` belongs to no solution and `lo += 1` keeps the invariant. The "too big" case is the mirror image. The range shrinks by one per probe, so the loop ends; if it ends without a match, the range held no solution.

The same discard argument drives three variants:

- **Counting pairs with `a[i] + a[j] <= t`.** When `a[lo] + a[hi] <= t`, `a[lo]` pairs with *every* index in `(lo, hi]`, because all of them hold values at most `a[hi]`. Add `hi - lo` in one go and move `lo`. A hash map cannot do this: it only answers equality.
- **Greedy pairing.** In Boats to Save People the heaviest person needs a boat whatever happens, and the lightest person is the best companion: if even they do not fit, nobody does. Pair or send alone, then move inward.
- **Fix the largest, count the rest.** For triangle counting, sort, fix the largest side `a[k]`, and run the counting scan on `[0, k - 1]` with the condition `a[lo] + a[hi] > a[k]`.

**Two pointers or a hash map?**

| Situation | Choose | Cost |
|---|---|---|
| Sorted input, equality target | two pointers | O(n) time, O(1) space |
| Unsorted, original indices needed (Two Sum) | hash map from value to index | O(n) time, O(n) space |
| Unsorted, only values needed | sort, then two pointers | O(n log n); CPython's `list.sort` may borrow up to n/2 slots while merging |
| Inequality: count pairs with sum at most t | sort, then the counting scan | O(n log n) |

## Template

```python
def pair_with_sum(a, target):
    """Indices (lo, hi), lo < hi, with a[lo] + a[hi] == target in sorted a, or None."""
    lo, hi = 0, len(a) - 1
    while lo < hi:
        s = a[lo] + a[hi]
        if s == target:
            return lo, hi
        if s < target:
            lo += 1      # even the largest partner is too small: a[lo] pairs with nothing
        else:
            hi -= 1      # even the smallest partner is too big: a[hi] pairs with nothing
    return None


def count_pairs_at_most(a, target):
    """Number of index pairs i < j with a[i] + a[j] <= target in sorted a."""
    lo, hi, count = 0, len(a) - 1, 0
    while lo < hi:
        if a[lo] + a[hi] <= target:
            count += hi - lo     # a[lo] works with every index in (lo, hi]
            lo += 1
        else:
            hi -= 1
    return count
```

## Worked example

Find two values summing to 10. Each caption gives the argument that makes the move safe; `x` marks indices ruled out for good.

```steps
lo = 0, hi = 5: 1 + 11 = 12 > 10. Even the smallest partner left (1) is too big for 11, so 11 is in no answer: hi -= 1
    index      0    1    2    3    4    5
    a          {{1}}    3    4    6    8   {{11}}
              lo                       hi
---
lo = 0, hi = 4: 1 + 8 = 9 < 10. Even the largest partner left (8) is too small for 1, so 1 is in no answer: lo += 1
    index      0    1    2    3    4    5
    a          {{1}}    3    4    6    {{8}}   11
              lo                  hi    x
---
lo = 1, hi = 4: 3 + 8 = 11 > 10. Even the smallest partner left (3) is too big for 8, so 8 is in no answer: hi -= 1
    index      0    1    2    3    4    5
    a          1    {{3}}    4    6    {{8}}   11
               x   lo             hi    x
---
lo = 1, hi = 3: 3 + 6 = 9 < 10. Even the largest partner left (6) is too small for 3, so 3 is in no answer: lo += 1
    index      0    1    2    3    4    5
    a          1    {{3}}    4    {{6}}    8   11
               x   lo        hi    x    x
---
lo = 2, hi = 3: 4 + 6 = 10: found the pair (indices 2 and 3) after 5 probes instead of up to 15
    index      0    1    2    3    4    5
    a          1    3    {{4}}    {{6}}    8   11
               x    x   lo   hi    x    x
```

## Pitfalls

- Sorting destroys the original indices. If the answer needs them, sort `(value, index)` pairs, or use the hash map.
- Write `while lo < hi`, not `<=`: a pair needs two different indices.
- When counting, add `hi - lo` on the success branch and then move `lo`; adding 1 counts one pair per probe and undercounts.
- In C++ or Java, `a[lo] + a[hi]` can overflow a 32-bit int for values near 2^31. Python integers cannot overflow.

## Quick check

Q: Run `count_pairs_at_most([1, 2, 4, 7], 6)`. What does each probe add, and what is the result?
A: 3. Probe (0, 3): 1 + 7 = 8 > 6, add nothing, hi = 2. Probe (0, 2): 1 + 4 = 5 <= 6, add 2 - 0 = 2 (pairs 1+2 and 1+4), lo = 1. Probe (1, 2): 2 + 4 = 6 <= 6, add 1, lo = 2 and the loop ends.

Q: A colleague moves `lo` when the sum is too big, "to try another value". Give an input where this misses the answer.
A: `[1, 3, 9]` with target 4. The first probe sees 1 + 9 = 10 > 4; moving `lo` discards 1, which was half of the only answer (1 + 3). The correct move discards 9, the value that is too big even with the smallest partner.

> [!know]
> You now know how to find and count pairs in sorted data in one O(n) pass, and how to prove that each discarded index could never be part of an answer.

=== recap | Three-sum and k-sum: sort, fix one, skip duplicates | 12 min
goal: Reduce k-sum to nested two-pointer scans and place the duplicate skips so that every distinct tuple is reported exactly once
tag: twoptr-ksum | k-sum by fixing values
link: Wikipedia: 3SUM | https://en.wikipedia.org/wiki/3SUM#Quadratic_algorithm | 5 min: the 'Quadratic algorithm' section shows the same sort-and-squeeze loop as pseudocode; the '3SUM-hardness' section explains why nobody expects a much faster algorithm
practice: 15, 18

> [!key]
> Sort once. Fix the smallest element `a[i]`; what remains is a pair sum on `a[i + 1:]` with target `-a[i]`, which the opposite-end scan solves in O(n), so 3Sum costs O(n^2). Handle duplicates by skipping, not with a set: skip an `i` whose value equals `a[i - 1]`, and after each match move `lo` past copies of the middle value.

## Internals

- **Reduction.** k-sum is "fix one value, then (k - 1)-sum on the rest", down to the two-pointer base case: O(n^(k-1)) after one O(n log n) sort, so 4Sum is O(n^3). The sort is paid once, not per level.
- **Why `a[i] == a[i - 1]` is a safe skip.** The scan for the first copy of this value, at some `j < i`, searched `[j + 1, n)`, which contains everything the scan for `i` would search (`[i + 1, n)`) with the same first value. So `i` can only rediscover triplets already found. The look-ahead version, `a[i] == a[i + 1]`, is the classic bug: it skips the *first* copy, whose range included the second copy, so triplets that use a value twice, such as (-1, -1, 2), disappear.
- **Why skipping only the middle value is enough.** After recording `(a[i], y, z)` and moving `lo` past every `y`, the next sum still using `z` is larger than zero, so `hi` leaves `z` by itself. Each distinct triplet is produced once: at the first `i` holding its smallest value and the first `lo` holding its middle value.
- **Early exit.** If `a[i] > 0`, all three values are positive: stop.
- **Alternatives.** A hash set per `i` is also O(n^2) but needs O(n) memory and messier de-duplication; `itertools.combinations` gives the O(n^3) oracle for testing. The best known algorithms beat n^2 only by small logarithmic factors, and the "3SUM conjecture" that no O(n^(2 - e)) algorithm exists is used as a hardness assumption in computational geometry.

## Template

```python
def three_sum(nums):
    """All distinct value triplets with sum 0."""
    a = sorted(nums)
    n, out = len(a), []
    for i in range(n - 2):
        if i > 0 and a[i] == a[i - 1]:
            continue                       # same first value: same triplets again
        if a[i] > 0:
            break                          # the smallest of the three is positive
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = a[i] + a[lo] + a[hi]
            if s < 0:
                lo += 1
            elif s > 0:
                hi -= 1
            else:
                out.append([a[i], a[lo], a[hi]])
                lo += 1
                hi -= 1
                while lo < hi and a[lo] == a[lo - 1]:
                    lo += 1                # skip copies of the middle value just used
    return out


def k_sum(nums, k, target):
    """All distinct value k-tuples (k >= 2) summing to target."""
    a = sorted(nums)

    def go(start, k, target):
        out = []
        if k == 2:
            lo, hi = start, len(a) - 1
            while lo < hi:
                s = a[lo] + a[hi]
                if s < target or (lo > start and a[lo] == a[lo - 1]):
                    lo += 1
                elif s > target:
                    hi -= 1
                else:
                    out.append([a[lo], a[hi]])
                    lo += 1
                    hi -= 1
            return out
        for i in range(start, len(a) - k + 1):
            if i > start and a[i] == a[i - 1]:
                continue
            for rest in go(i + 1, k - 1, target - a[i]):
                out.append([a[i]] + rest)
        return out

    return go(0, k, target)
```

## Worked example

The input `[0, -2, 2, -2, 0, 2, 0]` is full of repeats; `s` marks skipped positions.

```steps
Sorted. i = 0 fixes -2, so the pair must sum to 2. lo = 1, hi = 6: -2 + (-2) + 2 = -2 < 0, too small: lo += 1
    index       0     1     2     3     4     5     6
    a          {{-2}}    {{-2}}     0     0     0     2     {{2}}
                i    lo                            hi
---
lo = 2: -2 + 0 + 2 = 0. Record **(-2, 0, 2)**, then move both pointers: lo = 3, hi = 5
    index       0     1     2     3     4     5     6
    a          {{-2}}    -2     {{0}}     0     0     2     {{2}}
                i          lo                      hi
---
a[3] = 0 repeats the middle value just used, and so does a[4]: skip both (any match would be (-2, 0, 2) again). lo reaches hi, so i = 0 is done
    index       0     1     2     3     4     5     6
    a          {{-2}}    -2     0     0     0     {{2}}     2
                i                 s     s lo,hi
---
i = 1 repeats -2. Its search range [2, 6] lies inside the range i = 0 already searched, so every triplet it could find is already recorded: skip
    index       0     1     2     3     4     5     6
    a          -2    {{-2}}     0     0     0     2     2
                      i
---
i = 2 fixes 0, pair must sum to 0. lo = 3, hi = 6: 0 + 0 + 2 = 2 > 0, too big: hi = 5; still 2 > 0: hi = 4
    index       0     1     2     3     4     5     6
    a          -2    -2     {{0}}     {{0}}     0     2     {{2}}
                            i    lo                hi
---
lo = 3, hi = 4: 0 + 0 + 0 = 0. Record **(0, 0, 0)**; lo = 4, hi = 3, so the scan stops
    index       0     1     2     3     4     5     6
    a          -2    -2     {{0}}     {{0}}     {{0}}     2     2
                            i    lo    hi
---
i = 3 and i = 4 repeat 0 and are skipped. Result [(-2, 0, 2), (0, 0, 0)], each once. With neither skip, this input yields (-2, 0, 2) four times
    index       0     1     2     3     4     5     6
    a          -2    -2     0     {{0}}     0     2     2
                                  i     s
```

## Pitfalls

- Collecting tuples in a set "fixes" the output but hides a wrong skip and still does the duplicate work. Get the skips right and prove it with the oracle (this module's lab).
- The look-ahead skip `a[i] == a[i + 1]` loses answers that reuse a value; the skip without `i > 0` compares `a[0]` with `a[-1]` and loses `(0, 0, 0)` when every value is zero.
- The middle skip needs its own `lo < hi` guard, or it can run past `hi` and off the end of the list.
- In 4Sum the sum of four values near 10^9 overflows a 32-bit int in Java or C++; use 64-bit there.

## Quick check

Q: What does `three_sum([-1, -1, 0, 1, 2])` return, and what happens at each `i`?
A: `[[-1, -1, 2], [-1, 0, 1]]`. At i = 0 the scan matches (-1, -1, 2), moves both pointers, and matches (-1, 0, 1). i = 1 is skipped because a[1] == a[0]. At i = 2 (value 0) the only pair left sums to 3 > 0, and the loop stops at i = n - 3.

> [!know]
> You now know how to turn any k-sum into nested two-pointer scans and why each skip neither loses nor repeats a tuple.

=== lab | Stress-test three-sum and catch the duplicate bugs | 40 min
goal: Use a brute-force oracle on duplicate-heavy random inputs to catch, shrink and explain the three classic three-sum bugs, then measure O(n^3) against O(n^2)
link: USACO Guide: Basic Debugging | https://usaco.guide/general/basic-debugging#stress-testing | 5 min: the 'Stress Testing' section, the same compare-with-a-slow-solution loop run from a shell script

Three-sum is short, but its duplicate skips are easy to misplace, and a judge only tells you "wrong answer". Here you plant the three classic bugs, let a brute-force oracle find a failing input for each, shrink it to a minimal case and explain it. If you built the stress tester and shrinker in the Foundations project, plug these functions into it; otherwise the script below is self-contained.

## Steps

1. Save this as `three_sum_lab.py`. `fast(nums, bug)` is the template from the previous card with a switch that plants one of three bugs.

```python
import itertools
import random
import time


def brute(nums):
    """Oracle: every distinct value triplet with sum 0, O(n^3)."""
    return sorted({tuple(sorted(c)) for c in itertools.combinations(nums, 3) if sum(c) == 0})


def fast(nums, bug=None):
    """Sort + two pointers. bug plants one classic mistake: 'lookahead', 'nomiddle' or 'noguard'."""
    a = sorted(nums)
    n, out = len(a), []
    for i in range(n - 2):
        if bug == "lookahead":
            if a[i] == a[i + 1]:
                continue                     # skips the FIRST copy of a value
        elif bug == "noguard":
            if a[i] == a[i - 1]:
                continue                     # at i = 0 this compares with a[-1]
        elif i > 0 and a[i] == a[i - 1]:
            continue
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = a[i] + a[lo] + a[hi]
            if s < 0:
                lo += 1
            elif s > 0:
                hi -= 1
            else:
                out.append((a[i], a[lo], a[hi]))
                lo += 1
                hi -= 1
                while bug != "nomiddle" and lo < hi and a[lo] == a[lo - 1]:
                    lo += 1
    return out


def ok(nums, bug):
    got = fast(nums, bug)
    return sorted(got) == brute(nums) and len(got) == len(set(got))


def shrink(nums, bug):
    """Delete elements one at a time while the input still fails."""
    changed = True
    while changed:
        changed = False
        for i in range(len(nums)):
            smaller = nums[:i] + nums[i + 1:]
            if not ok(smaller, bug):
                nums, changed = smaller, True
                break
    return nums


EDGE = [[], [0], [0, 0, 0], [0, 0, 0, 0], [1, 1, 1], [-1, -1, 2], [-2, 1, 1, 1, 1]]


def hunt(bug=None, trials=10_000, edge=False):
    cases = EDGE if edge else []
    rng = random.Random(0)
    for t in range(len(cases) + trials):
        nums = cases[t] if t < len(cases) else [rng.randint(-3, 3) for _ in range(rng.randint(0, 8))]
        if not ok(nums, bug):
            return f"fails on test {t + 1}: {nums}, shrunk to {shrink(nums, bug)}"
    return "no failure found"


def timing():
    rng = random.Random(1)
    for n in (50, 100, 200, 400):
        nums = [rng.randint(-n, n) for _ in range(n)]
        t0 = time.perf_counter()
        b = brute(nums)
        t1 = time.perf_counter()
        f = fast(nums)
        t2 = time.perf_counter()
        assert sorted(f) == b
        print(f"n={n:4d}  brute {t1 - t0:7.3f} s   two pointers {t2 - t1:7.4f} s")
    for n in (1000, 2000, 4000):
        nums = [rng.randint(-n, n) for _ in range(n)]
        t0 = time.perf_counter()
        fast(nums)
        print(f"n={n:4d}  two pointers {time.perf_counter() - t0:7.3f} s")


if __name__ == "__main__":
    for bug in (None, "lookahead", "nomiddle", "noguard"):
        print(f"{bug or 'correct'}: {hunt(bug)}")
    print(f"noguard with edge cases first: {hunt('noguard', edge=True)}")
    timing()
```

2. Before running it, predict the smallest failing input for each bug. Write the three predictions down.
3. Run `python3 three_sum_lab.py`. For each bug, compare the shrunk input with your prediction, trace the buggy code on it by hand, and write one sentence saying which skip lost or repeated which triplet.
4. Look at how many random tests the `noguard` bug needed, then at the run with the edge cases first. Add two more hand-written cases to `EDGE` that you think are risky for any k-sum code.
5. Read the timing table. Compute the ratio between consecutive rows for each column and compare it with the 8x per doubling that O(n^3) predicts and the 4x that O(n^2) predicts.
6. Optional: generalise `fast` with the `k_sum` template and point the same oracle at 4Sum with `itertools.combinations(nums, 4)`.

## What you should see

- The correct version survives all 10,000 random inputs.
- `lookahead` fails within a few dozen tests and shrinks to `[-1, -1, 2]`: the only triplet uses -1 twice, and the look-ahead skip jumps over the first -1, whose range contained the second.
- `nomiddle` shrinks to five values such as `[3, 3, -1, -2, -1]` (sorted: -2, -1, -1, 3, 3): (-2, -1, 3) is recorded twice, once for each -1. Five is the minimum, because one scan must match twice with equal values.
- `noguard` needs about 2,300 random tests before it hits `[0, 0, 0]`, the only kind of input where `a[0] == a[-1]` loses an answer. With the edge cases first it fails on test 3. Random testing is good at common shapes and bad at special ones, which is why a stress tester always starts with a hand-written edge-case list.
- Timings are noisy on a shared machine, but the shape is clear: the brute force grows roughly 8x per doubling and needs seconds at n = 400; the two-pointer version takes milliseconds there and about 4x per doubling from n = 1000 to 4000.

=== recap | Read and write pointers: compact and merge in place | 12 min
goal: Filter, de-duplicate and merge arrays in place in one pass with a read pointer and a write pointer, and explain why the writes never clobber unread data
tag: twoptr-readwrite | Read and write pointers
link: cppreference: std::remove, std::remove_if | https://en.cppreference.com/w/cpp/algorithm/remove#Possible_implementation | 3 min: 'Possible implementation' is this card's loop in C++; the 'Notes' explain why it returns a new logical end instead of shrinking the container (the erase-remove idiom)
practice: 283, 88

> [!key]
> One pointer, `r`, reads every element; another, `w`, marks where the next kept element goes. Because `w <= r` at all times, a write never destroys anything still unread, so filtering, de-duplicating and compacting take one pass and O(1) extra memory. Merging into an array that has free space at its end is the same idea run backwards.

## Internals

- **Invariant: `a[:w]` holds exactly the kept elements of `a[:r]`, in their original order.** Keeping `a[r]` copies it to `a[w]` and advances both; dropping it advances only `r`. At the end `a[:w]` is the answer and `a[w:]` is leftover you can cut with one `del a[w:]`.
- **Only the keep rule changes.** Remove a value: `x != val`. De-duplicate sorted input: `w == 0 or x != a[w - 1]`, comparing with the last *written* value. At most two copies: `w < 2 or x != a[w - 2]`. Move zeroes: keep non-zeros and swap instead of copying, so the zeros drift behind `w`.
- **Why not `del` or `remove` in a loop?** A CPython list is a contiguous array of references. Deleting position i shifts the n - i references after it (a `memmove`), so k deletions cost O(kn) and a filtering loop becomes O(n^2); deleting while iterating with `for` also skips the element after each deletion. Idiomatic O(n) Python is `a[:] = [x for x in a if keep(x)]`: slice assignment refills the same list object, so other references see the change, at the price of a temporary list. The pointer loop is what you write when memory is tight, in C or C++ (`std::remove_if` is exactly this loop), or when the problem forbids extra space.
- **Merging, one pointer per sequence.** Merging sorted `a` and `b` takes the smaller head each time: O(m + n). Checking whether `s` is a subsequence of `t` is the same walk, advancing in `s` only on a match. To merge in place when `a` has `len(b)` free slots at its end, fill **from the back**: write the larger of `a[i]` and `b[j]` into slot `w`. This is safe because `w = i + j + 1`, so `w > i` while `b` still has elements; once `b` is used up, the rest of `a` is already in place.
- **In real systems.** PostgreSQL's merge join scans two inputs sorted on the join key in parallel, one pointer each. CPython's `list.sort` merges adjacent sorted runs the same way, switching to "galloping" (exponential search) when one run keeps winning. `heapq.merge` generalises the merge to k sorted iterables.

## Template

```python
def compact(a, keep):
    """Move the items with keep(x) true to the front of a, in order; return their count."""
    w = 0
    for r in range(len(a)):
        if keep(a[r]):
            a[w] = a[r]
            w += 1
    return w


def move_zeroes(a):
    w = 0
    for r in range(len(a)):
        if a[r] != 0:
            a[w], a[r] = a[r], a[w]
            w += 1


def merge_into(a, m, b):
    """a holds m sorted items followed by len(b) spare slots; merge sorted b into a in place."""
    i, j, w = m - 1, len(b) - 1, m + len(b) - 1
    while j >= 0:
        if i >= 0 and a[i] > b[j]:
            a[w] = a[i]
            i -= 1
        else:
            a[w] = b[j]
            j -= 1
        w -= 1
```

## Worked example

Move the zeros of `[0, 4, 0, 0, 7, 2]` to the end, keeping the other values in order (the swap version of `compact`).

```steps
Start: w = 0 (next slot for a kept value), r scans. a[0] = 0 is not kept, so only r moves
    index      0    1    2    3    4    5
    a          {{0}}    4    0    0    7    2
             r,w
---
r = 1: 4 is kept, swap it into slot w = 0, then w = 1. Everything left of w is the kept values in order
    a          {{4}}    {{0}}    0    0    7    2
                  r,w
---
r = 2 and r = 3 read zeros: skip them. The gap between w and r is all zeros
    a          4    0    {{0}}    {{0}}    7    2
                    w         r
---
r = 4: 7 is kept, swap it into slot w = 1, then w = 2. Everything left of w is the kept values in order
    a          4    {{7}}    0    0    {{0}}    2
                         w         r
---
r = 5: 2 is kept, swap it into slot w = 2, then w = 3. Everything left of w is the kept values in order
    a          4    7    {{2}}    0    0    {{0}}
                              w         r
---
Done: a[:w] = [4, 7, 2] in their original order, a[w:] all zeros. Six reads, three swaps
    a          {{4}}    {{7}}    {{2}}    0    0    0
                              w
```

## Pitfalls

- Comparing with the original neighbour, `a[r - 2]`, instead of the written prefix, `a[w - 2]`: in place, `a[r - 2]` may already be overwritten. On `[1, 1, 1, 2, 2, 3]` the wrong rule returns `[1, 1, 2, 3]` and loses a 2.
- Merging into `a` from the front overwrites elements of `a` you have not read yet.
- Forgetting a tail: a merge into a new list must append both leftovers (`out += a[i:]; out += b[j:]`); the back merge only needs `b`'s.
- Returning the new length but letting callers read past it: only `a[:w]` is meaningful.

## Quick check

Q: Run the "at most two copies" rule, `w < 2 or x != a[w - 2]`, on `[1, 1, 1, 2, 2, 2, 3]`. What is `a[:w]`?
A: `[1, 1, 2, 2, 3]` with w = 5. The third 1 and the third 2 are dropped, because each equals the value two slots back in the already written prefix.

> [!know]
> You now know how to compact, de-duplicate and merge in place with one pass and O(1) memory, and why deleting inside a loop is quadratic.

=== recap | Partitions: two-way and the Dutch national flag | 12 min
goal: Partition an array in place into two or three regions in one pass with an explicit region invariant, and explain why three-way partitioning rescues quicksort on duplicate keys
tag: twoptr-partition | In-place partitioning
link: Wikipedia: Dutch national flag problem | https://en.wikipedia.org/wiki/Dutch_national_flag_problem#The_array_case | 5 min: 'The array case' and its pseudocode: the same four regions under different names; check its loop against the template here
practice: 75

> [!key]
> A partition rearranges items so that everything with one property comes before everything without it. Two-way: converge two pointers and swap each misplaced pair. Three-way (Dijkstra's Dutch national flag): keep **four regions**, `< p | == p | unknown | > p`, and shrink the unknown region by one element per step. One pass, O(1) memory, at most one swap per element.

## Internals

- **Invariant**: `a[:lt] < p`, `a[lt:i] == p`, `a[i:gt]` not yet examined, `a[gt:] > p`. Initially `lt = i = 0` and `gt = n`, so everything is unknown. Then:
  - `a[i] < p`: swap with `a[lt]`, which is a known `== p` element (or `a[i]` itself when the middle region is empty), and advance both `lt` and `i`.
  - `a[i] > p`: decrement `gt` and swap `a[i]` with `a[gt]`. The value now at `i` came from the unknown region, so `i` must **not** advance.
  - `a[i] == p`: advance `i`.
  Each step shrinks `gt - i` by one, so the loop runs exactly n times.
- **Two-way, converging (Hoare style).** `lo` skips elements that belong on the left, `hi` skips those that belong on the right, then the misplaced pair is swapped. It makes fewer swaps than the read/write (Lomuto) version, which swaps every kept element.
- **Not stable.** Equal-keyed items can change relative order. If order matters, use `sorted(a, key=...)` (Timsort is stable, O(n log n)) or a stable compaction into a new list.
- **Why quicksort cares.** A two-way partition that sends keys equal to the pivot to one side (Lomuto's does) piles every duplicate there; on an all-equal array the recursion depth reaches n and the sort costs O(n^2). Hoare's scheme dodges this by stopping on equal keys and swapping them, at the price of many pointless swaps. Three-way partitioning parks every copy of the pivot in the middle, where it is never touched again, so an all-equal array is done after one pass (Sedgewick and Wayne call this entropy-optimal sorting).
- **In real systems.** C++'s `std::partition` and `std::nth_element`, NumPy's `np.partition` (introselect) and the introsort behind libstdc++'s `std::sort` all partition in place. In Python, for a key with three values, counting and rewriting is an equally good O(n) answer; the one-pass version matters when items carry payloads, or inside a quicksort or quickselect.

## Template

```python
def three_way_partition(a, pivot):
    """Rearrange a in place into  < pivot | == pivot | > pivot.  Return (lt, gt) with
    a[:lt] < pivot, a[lt:gt] == pivot, a[gt:] > pivot."""
    lt, i, gt = 0, 0, len(a)
    while i < gt:
        if a[i] < pivot:
            a[lt], a[i] = a[i], a[lt]
            lt += 1
            i += 1
        elif a[i] > pivot:
            gt -= 1
            a[i], a[gt] = a[gt], a[i]     # the value swapped in is unseen: do not advance i
        else:
            i += 1
    return lt, gt


def two_way_partition(a, pred):
    """Hoare-style: items with pred true to the front; return the boundary."""
    lo, hi = 0, len(a) - 1
    while True:
        while lo <= hi and pred(a[lo]):
            lo += 1
        while lo <= hi and not pred(a[hi]):
            hi -= 1
        if lo >= hi:
            return lo
        a[lo], a[hi] = a[hi], a[lo]
        lo += 1
        hi -= 1
```

## Worked example

Sort `[2, 0, 1, 2, 0, 1]` around the pivot 1. The region row shows the invariant after each step.

```steps
Start: everything is unknown (?). Regions: a[:lt] < 1, a[lt:i] == 1, a[i:gt] unknown, a[gt:] > 1
    index      0    1    2    3    4    5
    a          {{2}}    0    1    2    0    1
    region     ?    ?    ?    ?    ?    ?
            lt,i                            gt
---
a[i] = 2 > 1: gt -= 1, then swap a[i] with a[gt]. Do **not** move i: the 1 that arrived from the unknown region has not been examined yet
    index      0    1    2    3    4    5
    a          {{1}}    0    1    2    0    {{2}}
    region     ?    ?    ?    ?    ?    >
            lt,i                       gt
---
a[i] = 1 equals the pivot: it is already in the middle region, so i += 1
    index      0    1    2    3    4    5
    a          {{1}}    0    1    2    0    2
    region     =    ?    ?    ?    ?    >
              lt    i                  gt
---
a[i] = 0 < 1: swap it with a[lt] (a known 1, or itself), then lt += 1 and i += 1
    index      0    1    2    3    4    5
    a          {{0}}    {{1}}    1    2    0    2
    region     <    =    ?    ?    ?    >
                   lt    i             gt
---
a[i] = 1 equals the pivot: it is already in the middle region, so i += 1
    index      0    1    2    3    4    5
    a          0    1    {{1}}    2    0    2
    region     <    =    =    ?    ?    >
                   lt         i        gt
---
a[i] = 2 > 1: gt -= 1, then swap a[i] with a[gt]. Do **not** move i: the 0 that arrived from the unknown region has not been examined yet
    index      0    1    2    3    4    5
    a          0    1    1    {{0}}    {{2}}    2
    region     <    =    =    ?    >    >
                   lt         i   gt
---
a[i] = 0 < 1: swap it with a[lt] (a known 1, or itself), then lt += 1 and i += 1. Now i == gt: nothing is unknown, the array is 0 0 1 1 2 2
    index      0    1    2    3    4    5
    a          0    {{0}}    1    {{1}}    2    2
    region     <    <    =    =    >    >
                        lt      i,gt
```

## Pitfalls

- Advancing `i` after the swap with `gt`: the incoming value is never examined. On `[1, 2, 0]` that version returns `[1, 0, 2]`.
- Looping `while i < n` instead of `while i < gt`: the region from `gt` on is already final, and re-examining it moves 2s back.
- In the converging two-way loop, guard both inner scans with `lo <= hi`, or a pointer runs off the end when every element belongs on one side.
- Expecting stability from an in-place partition.

## Quick check

Q: Partition `[1, 2, 0]` around 1 with the template. What are the final array and `(lt, gt)`?
A: `[0, 1, 2]` and `(1, 2)`. The 1 is skipped (i = 1); the 2 is swapped with the 0 at the end (gt = 2, i stays 1); the 0 is then swapped with a[lt] (lt = 1, i = 2 = gt).

> [!know]
> You now know how to partition in place into two or three regions with an invariant you can check at every step, and why three regions keep quicksort fast on duplicates.

=== recap | Palindromes: converge, skip and allow one deletion | 10 min
goal: Check mirror properties from both ends in O(1) extra space, skip characters that do not count, and handle one allowed deletion with two plain checks
tag: twoptr-palindrome | Converging symmetric checks
link: Python docs: str.isalnum | https://docs.python.org/3/library/stdtypes.html#str.isalnum | 2 min: what counts as alphanumeric; it is Unicode-aware, so the superscript 2 and accented letters count, which matters when a problem means ASCII letters and digits
practice: 680

> [!key]
> Walk `i` up from the left and `j` down from the right, comparing `s[i]` with `s[j]`. Skip characters that do not count before comparing. If one deletion is allowed, the first mismatch leaves only two candidates: delete `s[i]` or delete `s[j]`, then check the inner range plainly. O(n) time, O(1) extra space.

## Internals

- **Invariant**: `s[:i]` mirrors `s[j + 1:]`. Each match extends both by one; the loop ends when the pointers meet, and the middle character of an odd-length string needs no partner.
- **Skipping**: advance `i` past characters that do not count (spaces, punctuation), then `j`, and only compare when both stand on characters that count. Compare `lower()` values for case-insensitive checks, or `casefold()` for real text (German "ß" folds to "ss").
- **One deletion.** Suppose deleting position `p` makes `s` a palindrome. If `p` lies strictly inside `(i, j)`, the shortened inner part would start with `s[i]` and end with `s[j]`, which differ: impossible. If `p` lies outside `[i, j]`, the mirroring forces a run of equal characters from `p` to the mismatch, and deleting `s[i]` (or `s[j]`) gives the same string. So two checks, `s[i + 1 .. j]` and `s[i .. j - 1]`, decide it: O(n) in total.
- **Python cost model.** `s == s[::-1]` builds a reversed copy (O(n) memory) but runs entirely in C, so for a plain check it beats a Python loop; `t = [c.lower() for c in s if c.isalnum()]` then `t == t[::-1]` is a fine O(n) answer to the skipping variant. The pointer version earns its place when memory matters or when the logic branches, as with the deletion.
- **More deletions.** With k deletions the branches multiply; in general the question becomes "is the longest palindromic subsequence at least n - k long?", a dynamic programming problem.

## Template

```python
def is_clean_palindrome(s):
    """Palindrome ignoring case and anything that is not a letter or digit."""
    i, j = 0, len(s) - 1
    while i < j:
        if not s[i].isalnum():
            i += 1
        elif not s[j].isalnum():
            j -= 1
        elif s[i].lower() != s[j].lower():
            return False
        else:
            i += 1
            j -= 1
    return True


def almost_palindrome(s):
    """True if deleting at most one character makes s a palindrome."""
    def plain(i, j):
        while i < j:
            if s[i] != s[j]:
                return False
            i += 1
            j -= 1
        return True

    i, j = 0, len(s) - 1
    while i < j:
        if s[i] != s[j]:
            return plain(i + 1, j) or plain(i, j - 1)
        i += 1
        j -= 1
    return True
```

## Worked example

Can `"cbbcc"` become a palindrome by deleting one character? It needs the second branch.

```steps
i = 0, j = 4: c == c, so this outer pair mirrors: move both inward
    index     0   1   2   3   4
    s         {{c}}   b   b   c   {{c}}
---
i = 1, j = 3: b != c, the first mismatch. Everything outside already mirrors, so one of these two must go
    s         c   {{b}}   b   {{c}}   c
---
Delete s[1]? Then s[2..3] = "bc" must be a palindrome. It is not
    s         c   -   {{b}}   {{c}}   c
---
Delete s[3]? Then s[1..2] = "bb" must be a palindrome. It is: deleting index 3 leaves "cbbc", so the answer is True
    s         c   {{b}}   {{b}}   -   c
```

## Pitfalls

- Trying only one branch at the mismatch: `"cbbcc"` needs the right deletion, `"ccbbc"` needs the left.
- Re-checking the whole string after a deletion instead of only the inner range: still O(n), but it rereads the matched outer pairs and invites index mistakes when building the shortened string.
- `str.isalnum` accepts Unicode letters and digits; if the problem means ASCII only, also test `c.isascii()`.
- A recursive inner check on long strings hits CPython's default recursion limit (1,000 frames); keep it a loop.

## Quick check

Q: Trace `almost_palindrome("abca")`. Which branch succeeds, and what string remains?
A: i = 0, j = 3 match (a, a). At i = 1, j = 2, b != c. Deleting s[1] leaves the inner range "c", a palindrome, so the result is True and the string becomes "aca". (Deleting s[2] would also work: "aba".)

> [!know]
> You now know how to run mirror checks from both ends with skipping and one allowed deletion, and why two candidate deletions are enough.

=== recap | The limiting side: most water and trapped rain | 14 min
goal: Solve container and trapped-water problems in O(n) and O(1) space by arguing that the shorter side is already settled
tag: twoptr-limiting | Limiting-side two pointers
link: doocs: LeetCode 42 solutions | https://leetcode.doocs.org/en/lc/42/#solution-1-dynamic-programming | 5 min: 'Solution 1' builds left and right maximum arrays: the O(n)-space version of the water formula that this card's two-pointer argument compresses to O(1)
practice: 11, 42

> [!key]
> When an answer depends on `min(left side, right side)`, the shorter side is the bottleneck, and that settles it. For the container, the shorter wall has already met its best partner (any other is closer and no taller in effect), so discard it. For trapped water, the side with the lower wall knows its water level exactly, because the other side is guaranteed to be at least as tall. Process that side and move inward.

## Internals

- **Container.** `area(lo, hi) = (hi - lo) * min(h[lo], h[hi])`. If `h[lo] <= h[hi]`, every other pair `(lo, k)` with `lo < k < hi` is narrower and its height is still at most `h[lo]`, so none beats the current area: `lo` is finished. Invariant: the best area seen so far is at least the area of every pair with an endpoint outside `[lo, hi]`. Ties can move either pointer.
- **Water.** The water above bar `x` is `min(max(h[:x + 1]), max(h[x:])) - h[x]`. When `h[lo] < h[hi]`, the right side of `lo` contains a bar at least `h[hi] > h[lo]`; more strongly, every bar that raised `left_max` was processed while an even taller bar stood at `hi` or further right. So the level at `lo` is `left_max`, whatever the exact right maximum is. Add `left_max - h[lo]` and advance; mirror when the right side is lower.
- **Cost.** Each step moves one pointer, so n - 1 steps, O(n) time, O(1) space.
- **Alternatives.** For water: prefix and suffix maximum arrays (O(n) space, the easiest to prove), or a monotonic stack that fills water layer by layer (the monotonic stacks module). For the container there is no simpler O(n) method; the brute force is O(n^2).
- **Recognising it.** The value of a pair is capped by its smaller end, so that end is the one you can settle. Ask "which end can never do better than it already has?" and discard it.

## Template

```python
def max_area(h):
    lo, hi, best = 0, len(h) - 1, 0
    while lo < hi:
        best = max(best, (hi - lo) * min(h[lo], h[hi]))
        if h[lo] < h[hi]:
            lo += 1      # h[lo] limits every pair (lo, k), k < hi: none beats this one
        else:
            hi -= 1      # symmetric: h[hi] is the limit, so drop it
    return best


def trap(h):
    lo, hi = 0, len(h) - 1
    left_max = right_max = water = 0
    while lo < hi:
        if h[lo] < h[hi]:                  # the right side has a wall >= h[lo] somewhere
            left_max = max(left_max, h[lo])
            water += left_max - h[lo]
            lo += 1
        else:
            right_max = max(right_max, h[hi])
            water += right_max - h[hi]
            hi -= 1
    return water
```

## Worked example

Most water for heights `[1, 5, 9, 6, 4, 8, 2]`; `x` marks walls that are finished.

```steps
width 6 x height 1 = 6, best = 6. h[lo] = 1 is the shorter wall: any other partner for it is closer and still capped at 1, so lo is finished: lo += 1
    index      0    1    2    3    4    5    6
    h          {{1}}    5    9    6    4    8    {{2}}
              lo                            hi
---
width 5 x height 2 = 10, best = 10. h[hi] = 2 is the shorter (or equal) wall: hi is finished: hi -= 1
    index      0    1    2    3    4    5    6
    h          1    {{5}}    9    6    4    8    {{2}}
               x   lo                       hi
---
width 4 x height 5 = 20, best = 20. h[lo] = 5 is the shorter wall: any other partner for it is closer and still capped at 5, so lo is finished: lo += 1
    index      0    1    2    3    4    5    6
    h          1    {{5}}    9    6    4    {{8}}    2
               x   lo                  hi    x
---
width 3 x height 8 = 24, best = 24. h[hi] = 8 is the shorter (or equal) wall: hi is finished: hi -= 1
    index      0    1    2    3    4    5    6
    h          1    5    {{9}}    6    4    {{8}}    2
               x    x   lo             hi    x
---
width 2 x height 4 = 8, best = 24. h[hi] = 4 is the shorter (or equal) wall: hi is finished: hi -= 1
    index      0    1    2    3    4    5    6
    h          1    5    {{9}}    6    {{4}}    8    2
               x    x   lo        hi    x    x
---
width 1 x height 6 = 6, best = 24. h[hi] = 6 is the shorter (or equal) wall: hi is finished: hi -= 1. Now lo == hi: the answer is 24
    index      0    1    2    3    4    5    6
    h          1    5    {{9}}    {{6}}    4    8    2
               x    x   lo   hi    x    x    x
```

## Pitfalls

- Moving the taller wall: the width shrinks and the height stays capped by the shorter wall, so the area can only fall.
- In the water problem, adding `left_max - h[lo]` before updating `left_max` with `h[lo]` produces negative water; update first.
- Thinking the pointers must meet at the tallest bar: they meet wherever the comparisons lead, and the answer is still correct.
- Empty or one-bar input: the loop never runs, and the answer is 0 for both problems.

## Quick check

Q: What does `trap([3, 0, 2, 0, 4])` return, and which side is processed first?
A: 7. Since 3 < 4, the left side is processed throughout: left_max becomes 3, then the bars 0, 2 and 0 hold 3, 1 and 3 units, and the pointers meet at the 4.

Q: Why is the container's discard argument wrong if you move the pointer at the *taller* wall?
A: The pair (shorter, taller) is the widest pair the shorter wall can still form; moving the taller wall inward pairs the shorter wall with closer walls, so the height stays capped by the shorter wall while the width drops. Those pairs can never beat the current one, so it is the shorter wall that is finished, not the taller one.

> [!know]
> You now know how to solve min-of-two-ends problems in O(n) and O(1) space by proving which side is already settled.

=== practice
- 283 core
  cue: Rearrange in place so that one kind of value ends up at the back while the others keep their order.
  hint: Keep two positions: where you are reading, and where the next value you keep should go.
  insight: A write index w advances only when a[r] is non-zero; swapping a[w] and a[r] keeps the non-zeros in order at the front while the zeros collect behind w. Each element is read once and moved at most once.
  cost: O(n) time, O(1) space
  pattern: twoptr-readwrite
- 680 core
  cue: You may remove at most one character before checking the mirror property.
  hint: Run the usual inward comparison. What are your options at the first disagreement?
  insight: Everything outside the first mismatch already mirrors, so the deleted character must be s[i] or s[j]; check whether s[i+1..j] or s[i..j-1] is a palindrome. Two linear checks at most.
  cost: O(n) time, O(1) space
  pattern: twoptr-palindrome
- 88 core
  cue: Two sorted arrays, the first with exactly enough empty room at its end; merge without a second buffer.
  hint: Writing from the front overwrites values you have not used yet. Where is the free space?
  insight: Fill from the back: compare the largest unused value of each array and write it at slot i + j + 1, which always lies beyond the unread part of the first array. Once the second array is used up, the rest is already in place.
  cost: O(m + n) time, O(1) extra space
  pattern: twoptr-readwrite
- 167 core
  cue: A sorted array, a pair that hits a target sum, and constant extra space.
  hint: Look at the smallest and largest values together. If their sum is too small, which of the two can never be part of an answer?
  insight: If a[lo] + a[hi] < target, a[lo] fails even with the largest remaining partner, so drop it; if the sum is too large, drop a[hi]. The answer always stays inside [lo, hi], and each probe discards one index.
  cost: O(n) time, O(1) space
  pattern: twoptr-ends
- 881 core
  cue: Boats hold at most two people under a weight limit; minimise the number of boats.
  hint: The heaviest person needs a boat no matter what. Who is the best possible companion for them?
  insight: Sort. The lightest person is the best partner for the heaviest: if even they do not fit, the heaviest goes alone. Either way one boat is used and the heaviest is done, so move inward; an exchange argument shows no other pairing uses fewer boats.
  cost: O(n log n) time for the sort, O(1) extra space
  pattern: twoptr-ends
- 15 core
  cue: All distinct triples of values that sum to zero, and the output must not repeat a triple.
  hint: Fix one value. What problem is left, and does sorting help with both that problem and the repeats?
  insight: Sort; for each i run the pair scan on a[i+1:] for -a[i]. Skip i when a[i] == a[i-1], and after a match move lo past copies of the middle value; each distinct triple is then produced exactly once.
  cost: O(n^2) time, O(1) extra space besides the sort and the output
  pattern: twoptr-ksum
- 75 core
  cue: Only three distinct values, to be sorted in place in a single pass.
  hint: Picture the array as regions whose boundaries move. How many regions do you need, counting the part you have not looked at yet?
  insight: Dutch national flag: a[:lt] holds 0s, a[lt:i] 1s, a[i:gt] is unknown, a[gt:] holds 2s. A 0 swaps to lt (advance both), a 2 swaps to gt - 1 (do not advance i: the incoming value is unseen), a 1 just advances i.
  cost: O(n) time, O(1) space, one pass
  pattern: twoptr-partition
- 11 derive
  cue: Choose two lines; the amount held depends on their distance apart and on the shorter line.
  hint: Start with the widest pair. Moving a pointer inward shrinks the width, so which line could possibly make up for that?
  insight: Moving the taller line can never help: the height stays capped by the shorter line while the width drops. So the shorter line has already met its best partner; discard it. n - 1 moves, keeping the best area seen.
  cost: O(n) time, O(1) space
  pattern: twoptr-limiting
- 42 derive
  cue: The water held above each bar of an elevation profile.
  hint: The water above a bar is min(highest bar to its left, highest bar to its right) minus its height. Do you need to know both maxima exactly?
  insight: Move inward from both ends. When h[lo] < h[hi], a wall at least h[hi] exists on the right, so the level at lo is decided by the left maximum alone: add left_max - h[lo] and advance lo; mirror the step otherwise.
  cost: O(n) time, O(1) space
  pattern: twoptr-limiting
- 18 stretch
  cue: Distinct quadruples with a given sum.
  hint: You already reduce three values to a pair scan. Can the same move apply one level higher?
  insight: Sort, fix two values with duplicate skipping at both levels, and two-pointer the remaining pair; the recursive k-sum template gives any k in O(n^(k-1)).
  cost: O(n^3) time, O(1) extra space besides the output
  pattern: twoptr-ksum
- 611 stretch
  cue: Count index triples whose values can be the sides of a triangle.
  hint: After sorting, which single inequality still needs checking? Fix the largest side.
  insight: For each largest side a[k], scan lo = 0 and hi = k - 1: if a[lo] + a[hi] > a[k], every start from lo to hi - 1 also works with hi, so add hi - lo and decrement hi; otherwise increment lo.
  cost: O(n^2) time, O(1) extra space
  pattern: twoptr-ends
