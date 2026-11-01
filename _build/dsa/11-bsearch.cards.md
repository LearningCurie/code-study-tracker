=== card | 35
time: 20 min

## The problem

Given a sorted list of distinct integers and a target, return its index if present. Otherwise return the index where inserting it would preserve the order. The position can be after every existing element. For example, `[1, 4, 8]` and target 5 give index 2.

## Constraints and what they imply

The input is in increasing order and values can be negative. The original task uses distinct values; the implementation also chooses the first insertion position if equal values occur. A list can be treated as empty, in which case position zero is correct. The requested logarithmic running time rules out inspecting every element in the worst case.

## Brute force

Scan from the beginning until an element is at least the target. Its index is the insertion position; if none qualifies, return the length. This uses O(n) time and O(1) space. It is a useful reference because it directly encodes the meaning of the answer, but a long prefix of smaller values requires a long scan.

## The insight

The comparison `nums[i] >= target` is false for a prefix and true for the rest. Maintain a half-open interval `[lo, hi)` containing the first true index, with `n` allowed as the answer. Indices before `lo` are known smaller; indices at or beyond `hi` are known at least the target. Initially these claims are vacuous. A true midpoint can be the answer, so retain it by setting `hi = mid`. A false midpoint and everything to its left can be discarded. When the bounds meet, no uncertainty remains.

## Optimal solution, traced

```steps
Start with [1, 4, 8], target 5
    lo = 0, hi = 3, mid = 1, value 4 is smaller
---
Discard through index 1
    lo = 2, hi = 3, mid = 2, value 8 qualifies
---
Keep the qualifying midpoint
    lo = hi = {{2}}; insert before 8
```

## Code

```python
def search_insert(nums, target):
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

## Complexity

Each comparison at least halves the candidate interval, so time is O(log(n + 1)); constant indices use O(1) auxiliary space. The input is not changed.

## Mistakes and edge cases

- Do not use `hi = mid - 1` with this half-open invariant: the midpoint may be the first valid position.
- Returning `n` is intentional when the target exceeds every value. Zero covers an empty list and a target below the first element.
- With duplicates, returning an arbitrary equal position is not the lower-bound contract implemented here.

## Variations

- Find the first index with value strictly greater than the target by changing the comparison.
- Count occurrences by subtracting the first at-least position from the first greater position.

=== card | 34
time: 25 min

## The problem

In a nondecreasing integer list, find the first and last indices occupied by a target. Return `[-1, -1]` if it is absent. The list `[1, 2, 2, 2, 7]` with target 2 yields `[1, 3]`. Equal entries are separate positions, and an empty list has no matching range.

## Constraints and what they imply

The input is already sorted and may contain a long run of duplicates. Values may be negative, and the target need not fall between the endpoints. The required logarithmic time excludes finding one occurrence and then walking across a run that could contain every element. Both ends must instead come from ordered comparisons.

## Brute force

Scan the entire list, recording the first and most recent indices equal to the target. If there are no matches, keep the sentinel pair. This needs O(n) time and O(1) space. It is simple even without sortedness, but does not exploit the fact that matches form one contiguous block.

## The insight

Compute two boundaries independently: the first position with value at least the target and the first with value strictly greater. In a sorted list each predicate is a false prefix followed by a true suffix. A half-open binary search returns the list length if the suffix is empty. The first boundary marks where a run could start; if that index is out of range or has another value, there is no run. Otherwise the second boundary is just after the run, so subtract one for the inclusive last index.

For each boundary, discarded left indices are known to fail the predicate and discarded right indices are known to satisfy it. Retaining a qualifying midpoint and excluding a failing one preserves these facts. At convergence the boundary is uniquely determined, including the end sentinel.

## Optimal solution, traced

```steps
Search [1, 2, 2, 2, 7] for 2
    first value at least 2 is at {{1}}
---
Search for the first value greater than 2
    upper boundary is {{4}}, immediately after the run
---
Check the lower boundary and subtract one
    nums[1] = 2, so the inclusive result is {{[1, 3]}}
```

## Code

```python
def search_range(nums, target):
    def boundary(strict):
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = lo + (hi - lo) // 2
            if nums[mid] < target or (strict and nums[mid] == target):
                lo = mid + 1
            else:
                hi = mid
        return lo

    start = boundary(False)
    if start == len(nums) or nums[start] != target:
        return [-1, -1]
    return [start, boundary(True) - 1]
```

## Complexity

Two searches each take O(log(n + 1)) comparisons. Their time is O(log(n + 1)) overall and auxiliary space is O(1); the list is unchanged.

## Mistakes and edge cases

- The upper boundary uses `>` rather than `>=`; otherwise the two searches return the same position.
- Check the lower index before indexing, because it may equal the length.
- An all-equal array has boundaries zero and n. A missing target between values must still return the sentinel pair.

## Variations

- Return the number of matches as upper boundary minus lower boundary.
- Report the half-open matching slice rather than inclusive endpoints.

=== card | 153
time: 25 min

## The problem

A strictly increasing nonempty integer list has been cyclically rotated by an unknown amount. Find its smallest value without restoring the order. For `[7, 9, 1, 3, 5]`, the answer is 1. A rotation by zero is allowed, as is a one-element list.

## Constraints and what they imply

Every value is distinct, so the rotation creates at most one descending break. Each side of the break remains increasing. The minimum occurs at the first element of the right-hand run, or at index zero if there is no break. The nonempty assumption makes the last element and the returned value well defined. Distinctness matters: ties destroy the strict separation used below.

## Brute force

Scan the values and retain the least seen so far. This uses O(n) time and O(1) space, correctly handling every rotation but not taking advantage of the two sorted runs. Alternatively, inspect adjacent pairs for the drop and use the first element if none occurs; that still takes linear time.

## The insight

Fix the original last value as a pivot. If a rotation occurred, every element of the initial run is strictly greater than this pivot, while every element of the final run is at most it. Thus the predicate `nums[i] <= pivot` has a false prefix and a true suffix. In the unrotated case it is true everywhere. Its first true position is exactly the minimum, and the last index always qualifies.

Maintain `[lo, hi)` as the unknown boundary region. A qualifying midpoint might be the first one, so keep it as the new upper boundary; a nonqualifying midpoint and every earlier candidate can be excluded. These updates preserve the first qualifying index until the interval becomes empty at that index.

## Optimal solution, traced

```steps
Start [7, 9, 1, 3, 5], pivot 5
    lo = 0, hi = 5; mid 2 has value 1 and qualifies
---
Keep the left half including the boundary
    lo = 0, hi = 2; mid 1 has value 9 and fails
---
Discard the failing prefix
    lo = hi = 2; minimum is {{1}}
```

## Code

```python
def find_min_distinct(nums):
    pivot = nums[-1]
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] <= pivot:
            hi = mid
        else:
            lo = mid + 1
    return nums[lo]
```

## Complexity

The search takes O(log n) time for nonempty input and O(1) auxiliary space. It does not rotate, copy, or mutate the input.

## Mistakes and edge cases

- The pivot must remain the original last value for this particular monotone predicate.
- With no rotation the boundary is zero; with one element it is also zero.
- Duplicates may make values on both sides equal to the pivot, invalidating the predicate; use the duplicate-aware algorithm instead.

## Variations

- Return the rotation point index instead of its value.
- Use that index to select a sorted segment before searching for a target.

=== card | 33
time: 30 min

## The problem

Given a cyclic rotation of a strictly increasing list and an integer target, return its index or -1 if it is absent. For `[6, 8, 1, 3, 4]`, target 3 is at index 3. A list that has not rotated and an empty list are also handled.

## Constraints and what they imply

Elements are distinct, and the original ordering is increasing. Therefore at most one descent exists and at least one of the two halves around a midpoint is sorted. An arbitrary midpoint comparison alone does not say which side holds the target because the whole array is not sorted. The goal is logarithmic time without making a sorted copy or changing the input.

## Brute force

Check each value until finding the target, returning -1 if the scan ends. This costs O(n) time and O(1) space. It works for any ordering and gives a straightforward reference for testing, but ignores the special shape of the rotated input.

## The insight

Maintain an inclusive candidate interval `[lo, hi]`. If its midpoint is not the target, compare its value with the left endpoint. When the left endpoint is no larger, the left half is sorted. The target lies there precisely when its value is at least the left endpoint and strictly less than the midpoint. Otherwise discard that half and the already checked midpoint. If the left half is not sorted, the right half must be sorted; keep it only if the target is strictly above the midpoint and no larger than the right endpoint.

The rotation structure makes the range tests exact for the sorted side: a target whose value lies within those bounds cannot occur in the other disjoint value range. Every iteration either returns the answer or removes the midpoint and at least half the candidates. By induction the target remains in the retained interval whenever it exists.

## Optimal solution, traced

```steps
Search [6, 8, 1, 3, 4] for 3
    lo = 0, hi = 4, mid = 2, value 1
---
The right half [1, 3, 4] is sorted
    1 < 3 <= 4, so keep indices 3 through 4
---
Check midpoint index 3
    nums[3] = 3, return {{3}}
```

## Code

```python
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1
```

## Complexity

The candidate interval halves on every unsuccessful iteration. Time is O(log(n + 1)), and auxiliary space is O(1). The input remains unchanged.

## Mistakes and edge cases

- Check equality at the midpoint before using strict inequalities that exclude it.
- Include the outer endpoint of the sorted side; otherwise targets at the ends can be lost.
- Duplicates can make it impossible to identify the sorted side from these comparisons. This implementation assumes distinct values.

## Variations

- Find the minimum first, then binary-search the appropriate sorted run.
- Allow duplicates, shrinking ambiguous equal endpoints at the cost of O(n) worst-case time.

=== card | 162
time: 25 min

## The problem

Find an index of any strict peak in a nonempty integer list: its value must be larger than each immediate neighbor that exists. Imagine the missing neighbors outside the ends are smaller than every list value. For `[1, 4, 2, 5, 3]`, either index 1 or 3 is acceptable.

## Constraints and what they imply

Adjacent values are unequal, though nonadjacent values can repeat and the whole list need not be sorted. This assumption guarantees a strict peak: following rising steps must eventually stop at a descent or the right edge. Either endpoint may be the answer. The logarithmic goal calls for proving that an entire half contains a peak, not for sorting the values or returning the global maximum.

## Brute force

Inspect each index and compare it with its existing neighbors. The first strict peak found is valid; scanning the maximum is another option. Both take O(n) time and O(1) space. A maximum is certainly a peak under the adjacent-unequal assumption, but finding the global maximum performs more work than necessary.

## The insight

Keep an inclusive interval `[lo, hi]` guaranteed to contain a peak. Its outer boundaries face uphill into the interval: when a neighbor outside exists, it is smaller than the adjacent inside endpoint. At midpoint, compare `nums[mid]` with `nums[mid + 1]`. On a rising edge, a peak exists to the right: follow rising edges until a descent or the interval's right boundary. Set `lo = mid + 1`, preserving an uphill left boundary. On a falling edge, a peak exists at or to the left of mid; set `hi = mid` and preserve the uphill right boundary. The unchanged outer boundary supplies the other side of the argument.

At convergence the sole remaining element has both required boundary properties and is a strict peak. Importantly, the slope comparisons across the entire array are not a monotone predicate: many peaks and valleys can occur. The argument relies on the preserved existence invariant instead.

## Optimal solution, traced

```steps
Start [1, 4, 2, 5, 3]
    lo = 0, hi = 4; mid = 2 and 2 < 5
---
A peak lies to the right
    lo = 3, hi = 4; mid = 3 and 5 > 3
---
A peak lies at or left of mid
    lo = hi = {{3}}; value 5 exceeds both neighbors
```

## Code

```python
def find_peak(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] < nums[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

## Complexity

Each iteration halves the interval, giving O(log n) time and O(1) space for a nonempty input. Only adjacent elements are compared, and the input is unchanged.

## Mistakes and edge cases

- Do not claim the slope predicate is globally monotone. The list may have many peaks.
- The loop condition ensures `mid + 1` is in bounds. A single element immediately returns index zero.
- If adjacent equal values are allowed, a strict peak need not exist and the proof must change.

## Variations

- Return the peak value instead of its index.
- For a promised strictly increasing-then-decreasing list, find its unique summit with the same slope search.

=== card | 875
time: 30 min

## The problem

A worker processes positive-sized piles at a fixed positive integer rate. In one hour the worker handles at most one pile, finishing it if fewer units remain; unused time in that hour cannot be spent on another pile. Given a deadline in hours, return the minimum rate that finishes every pile. For piles `[3, 6, 7]` and 8 hours, rate 3 is sufficient, while rate 2 is not.

## Constraints and what they imply

Piles are nonempty and contain positive integers. The deadline is at least the number of piles, since each pile requires a separate hour; otherwise no rate is feasible. A rate of one is the smallest meaningful candidate, and the largest pile size always finishes each pile in one hour. Large pile values make enumerating every possible rate too expensive.

## Brute force

Try rates from 1 through the largest pile, compute each pile's rounded-up processing time, and return the first that meets the deadline. For n piles and maximum pile size M, this costs O(nM) time and O(1) auxiliary space. It is an excellent oracle on tiny values but repeats a similar feasibility calculation for many rates.

## The insight

For rate r, a pile of size p takes `(p + r - 1) // r` hours. Increasing r never increases any pile's rounded-up time, so total hours are nonincreasing. Consequently feasible rates form a suffix of `[1, M]`, and M is known feasible. Binary search for the first feasible rate while preserving that the answer lies in the inclusive interval `[lo, hi]`. A feasible midpoint may be optimal, so retain it; an infeasible midpoint rules out all smaller rates. Once the bounds meet, the remaining rate is feasible and all smaller candidates have been excluded.

Integer ceiling division avoids rounding errors that can arise when large numbers are converted to floating point. The check counts hours per pile rather than dividing the total work by the rate, because partly used hours cannot be combined.

## Optimal solution, traced

```steps
Piles [3, 6, 7], deadline 8
    lo = 1, hi = 7; rate 4 requires 1 + 2 + 2 = 5 hours
---
Rate 4 is feasible; keep it and smaller rates
    lo = 1, hi = 4; rate 2 requires 2 + 3 + 4 = 9 hours
---
Rate 2 fails; try the remaining boundary
    lo = 3, hi = 4; rate 3 needs 1 + 2 + 3 = 6 hours
---
Retain rate 3
    lo = hi = {{3}}
```

## Code

```python
def min_eating_speed(piles, hours):
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        needed = sum((pile + mid - 1) // mid for pile in piles)
        if needed <= hours:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

## Complexity

Each feasibility check scans n piles. The candidate range halves on each step, yielding O(n log(M + 1)) time and O(1) auxiliary space, where M is the largest pile. No input is changed.

## Mistakes and edge cases

- Round each pile separately; summing sizes before dividing can underestimate the hours.
- A deadline equal to the pile count forces every pile to take exactly one hour, so the maximum pile size is the answer.
- If the deadline is smaller than the number of piles, the stated assumptions fail and the upper bound is not feasible.

## Variations

- Return the hours consumed at the minimum rate along with the rate.
- Find the smallest rate meeting a deadline when each task has a different fixed setup time, provided feasibility stays monotone.

=== card | 1011
time: 30 min

## The problem

Ship positive package weights in their given order, loading a consecutive group each day. Find the smallest integer daily capacity that sends everything in at most the allowed number of days. For weights `[1, 2, 3, 4]` and two days, capacity 6 works by shipping `[1, 2, 3]` and `[4]`, whereas capacity 5 needs three days.

## Constraints and what they imply

There is at least one package, every weight is positive, and the allowed number of days is positive. Packages cannot be reordered or divided between days. A capacity below the largest individual weight is impossible. A capacity equal to the total weight sends all packages in one day, so the search has a feasible upper bound. The condition is at most the deadline; unused days are harmless.

## Brute force

Try each integer capacity from the largest weight through the total. For each, determine the fewest days by enumerating every placement of cuts between packages, and stop at the first capacity with a feasible partition. There are up to 2^(n-1) cut patterns per capacity; the direct enumeration illustrates the requirement but does not scale. Even using the greedy check below while trying all capacities costs O(n times the total weight).

## The insight

For a fixed capacity, greedily extend the current day's shipment until the next package would overflow, then start the next day. Greedy's first day reaches at least as far as the first day of any feasible schedule: otherwise that schedule could not include the next package either. Repeating the argument for the remaining suffix shows that greedy uses no more days than any other schedule. Positivity guarantees removing a prefix from a feasible group does not increase its weight.

A larger capacity never invalidates an existing schedule, so the feasibility predicate is false then true. Binary-search the first capacity whose greedy day count is within the deadline. Each update retains every still-possible minimum and a known feasible upper endpoint. At convergence that endpoint is the least feasible capacity.

## Optimal solution, traced

```steps
Weights [1, 2, 3, 4], days 2
    capacity bounds [4, 10]; try 7: [1, 2, 3] | [4], feasible
---
Retain capacities through 7
    try 5: [1, 2] | [3] | [4], three days, infeasible
---
Only capacity 6 remains
    [1, 2, 3] | [4] fits; answer {{6}}
```

## Code

```python
def ship_within_days(weights, days):
    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        used, load = 1, 0
        for weight in weights:
            if load + weight > mid:
                used += 1
                load = 0
            load += weight
        if used <= days:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

## Complexity

With n weights and total S, each check takes O(n), and binary search performs O(log(S + 1)) checks. Time is O(n log(S + 1)); auxiliary space is O(1). The input is not modified.

## Mistakes and edge cases

- Never test a capacity smaller than the largest package with this check: it assumes every package fits alone.
- Start with one day, and reset the load before adding the overflowing package to the new day.
- A deadline at least n gives the largest package weight; one day gives the total.

## Variations

- Recover the greedy daily groups after finding the minimum capacity.
- Give each day a different capacity and redesign the feasibility check; the simple single-capacity proof no longer suffices.

=== card | 1552
time: 30 min

## The problem

Choose m positions from a collection of distinct integer coordinates to maximize the minimum distance between any two chosen positions. For positions `[1, 2, 4, 8, 9]` and m = 3, choosing 1, 4, and 8 gives minimum distance 3, and no placement achieves 4.

## Constraints and what they imply

There are n distinct positions and `2 <= m <= n`. Coordinates may be treated as arbitrary integers; only their order and differences matter. Sorting does not change the available choices. In sorted chosen positions, the smallest pairwise distance is attained by neighboring chosen positions, because every non-neighboring distance is a sum of positive gaps. The answer is at least 1 for distinct integer coordinates and at most the full coordinate span.

## Brute force

Enumerate all combinations of m positions. For each combination, find its smallest pairwise distance and retain the largest such value. There are binomial(n, m) combinations and a direct pairwise evaluation costs O(m²) per combination, with O(m) space for a chosen combination. This provides a compact independent test for small n but grows rapidly.

## The insight

For a candidate minimum distance d, sort the coordinates and choose the first position, then repeatedly choose the earliest position at least d from the last chosen one. This greedy placement is optimal for the feasibility question: its first choice is no later than any alternative's first choice, and by induction its next choice is no later than the corresponding choice in any feasible alternative. Therefore, if any m positions fit, greedy finds at least m.

Feasibility is monotone in the opposite direction from minimum-capacity problems: every smaller distance also fits. Search the last feasible value in `[0, span]`, using an upper midpoint so the loop progresses even when two candidates remain. Zero is feasible and serves as a useful lower sentinel; after convergence the preserved feasible lower bound is the maximum distance.

## Optimal solution, traced

```steps
Positions [1, 2, 4, 8, 9], m = 3
    span = 8; try distance 4: greedy picks 1, 8, only two positions
---
Distance 4 fails, so try below it
    try 2: greedy picks 1, 4, 8; feasible
---
Try 3 in the remaining interval
    greedy picks 1, 4, 8; answer {{3}}
```

## Code

```python
def max_min_distance(positions, m):
    ordered = sorted(positions)
    lo, hi = 0, ordered[-1] - ordered[0]
    while lo < hi:
        mid = lo + (hi - lo + 1) // 2
        count, last = 1, ordered[0]
        for position in ordered[1:]:
            if position - last >= mid:
                count += 1
                last = position
        if count >= m:
            lo = mid
        else:
            hi = mid - 1
    return lo
```

## Complexity

Sorting a copy costs O(n log n) time and O(n) space. If W is the coordinate span, binary search adds O(n log(W + 1)) time. Python's sorting machinery may also use O(n) working space. The caller's list remains unchanged.

## Mistakes and edge cases

- Use an upper midpoint when assigning `lo = mid`; a lower midpoint can loop forever on adjacent bounds.
- The check must place from left to right, not select arbitrary eligible coordinates.
- For m = 2, the extremes give the entire span. The stated contract excludes m greater than n and m less than 2.

## Variations

- Return one greedy placement after computing the best distance.
- Maximize the minimum gap on a circle; the choice of starting point now requires additional reasoning.

=== card | 410
time: 40 min

## The problem

Partition a nonempty array of nonnegative integers into exactly k nonempty contiguous parts. Minimize the largest sum among those parts and return that minimum. For `[7, 2, 5, 10, 8]` with k = 2, the split `[7, 2, 5] | [10, 8]` has largest sum 18; no split has a smaller largest sum.

## Constraints and what they imply

The contract is `1 <= k <= n`, and values are nonnegative. Every element must appear once, in its original order, and parts cannot be empty. Any largest part sum is at least the largest element, and the total sum is always feasible with one part. Nonnegative values are essential: extending a part cannot reduce its sum, and splitting a part cannot increase either resulting sum. With negative numbers, both the greedy feasibility check and its proof can fail.

The requirement says exactly k parts, not merely at most k. Fortunately, a valid partition with fewer than k parts can be refined: while there are fewer than k parts, some part contains at least two elements because k is at most n. Split that part into two nonempty pieces. Both new sums are at most the old sum, so the capacity bound remains valid. Repeating produces exactly k parts.

## Brute force

Choose k-1 cut locations among the n-1 gaps. Calculate each resulting part sum and take the largest; then minimize over all choices. There are binomial(n-1, k-1) partitions. Evaluating each directly takes O(n), for O(n times binomial(n-1, k-1)) time and O(k) space to store the cut positions. This exhaustive method expresses the objective independently and works well for small test cases, but its number of partitions can be exponential.

## The insight

Instead of selecting cuts directly, ask whether some partition has every part sum at most a candidate bound S. Build a part from left to right until the next value would exceed S, then cut immediately before that value. This greedy check is defined only for S at least the largest element, so every singleton fits. The first greedy part ends no earlier than the first part of any valid partition: any longer first part would exceed S. Removing the greedy prefix from an alternative partition can only shorten its remaining first part, which cannot increase its sum. Applying the same argument repeatedly shows greedy uses the fewest parts among all partitions under S.

Feasibility is monotone: a partition that fits bound S also fits every larger bound. Search the inclusive range from the maximum element to the total, maintaining a feasible upper endpoint. If greedy uses at most k parts, the midpoint is feasible even when it uses fewer than k, by the refinement argument. Otherwise all smaller bounds are infeasible. Each iteration preserves the least feasible value in the interval; when the endpoints coincide it is exactly the optimum.

This reframing separates two proofs: greedy must correctly answer the fixed-bound question, and binary search must exploit the resulting monotone yes/no answers. Neither conclusion follows merely from the fact that the input is an array.

## Optimal solution, traced

```steps
Input [7, 2, 5, 10, 8], k = 2
    bounds [10, 32]; try 21: [7, 2, 5] | [10, 8], feasible
---
Bounds [10, 21]; try 15
    greedy produces [7, 2, 5] | [10] | [8], three parts, infeasible
---
Bounds [16, 21]; try 18
    [7, 2, 5] | [10, 8], feasible
---
Try 17 in bounds [16, 18]
    [7, 2, 5] | [10] | [8], infeasible; answer {{18}}
```

## Code

```python
def split_array(nums, k):
    lo, hi = max(nums), sum(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        parts, current = 1, 0
        for value in nums:
            if current + value > mid:
                parts += 1
                current = 0
            current += value
        if parts <= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

## Complexity

Let S be the sum and n the length. The greedy check takes O(n) time and O(1) space. The numeric range has at most S + 1 values, so total time is O(n (1 + log(S + 1))) with O(1) auxiliary space, including initialization. When S is zero, the bounds already coincide and initialization still takes O(n). The input is not modified.

## Mistakes and edge cases

- Requiring greedy to use exactly k parts can reject a feasible bound. Fewer parts can be split further under the nonnegative contract.
- Starting below the maximum element makes the check incorrectly treat an oversized singleton as if it were valid.
- With k = 1 the answer is the total, and with k = n it is the maximum. All-zero arrays have optimum zero.
- Negative values break the refinement and maximal-prefix arguments. Do not silently reuse the algorithm for them.

## Variations

- Reconstruct exactly k groups after finding the bound by splitting eligible greedy groups without exceeding it.
- Use dynamic programming over prefix lengths and part counts when the values can be negative.

=== card | 719
time: 40 min

## The problem

For an integer list, form the absolute difference of each pair of distinct indices. Return the kth smallest difference, counting equal differences separately. For `[1, 3, 1]`, the pair differences are 2, 0, and 2, so the second smallest is 2. A pair is identified by its indices even when its values are equal.

## Constraints and what they imply

There are at least two values and `1 <= k <= n(n-1)/2`. Input values may repeat, and this implementation also supports negative values. Explicitly storing every pair requires quadratic space, which is costly for the large input sizes this task allows. After sorting, the absolute distance between a left index and a right index is simply their difference, and all differences lie between zero and the total value span. The answer must be an integer in this interval.

A zero distance is possible when two values match. Sorting changes the original index order but not the multiset of pair distances: each original pair corresponds to exactly one pair in the sorted arrangement, with multiplicity preserved. The algorithm returns only the distance, not the pair of original indices.

## Brute force

Enumerate all index pairs, calculate their absolute differences, sort the resulting list, and take index k-1. There are N = n(n-1)/2 differences, so the method costs O(n² + N log N) time and O(N) space. It naturally counts duplicates and is an independent way to verify small cases. Selecting without sorting could reduce the selection cost, but generating all pairs is still quadratic.

## The insight

For a proposed threshold d, count the pairs whose distance is at most d. With sorted values, process each right endpoint in increasing order and keep a left pointer at the first value close enough to it. While the difference exceeds d, advance left. Once the condition holds, all indices from left through right-1 form valid pairs with this right endpoint, contributing `right - left` to the count.

The left pointer never needs to move backward: increasing the right value cannot make a previously too-distant left value become close enough. Every valid pair is counted exactly once, at its right endpoint, and no invalid pair is included. Each pointer advances at most n times, making one threshold check linear after sorting. The count is nondecreasing as d grows, because a larger threshold keeps every pair accepted by a smaller one.

Search the first distance whose count is at least k. The full span includes every pair, so it is feasible; zero is the smallest possible difference. If the count is already at least k at a midpoint, preserve that midpoint and smaller candidates. Otherwise discard it and all smaller thresholds. At convergence the boundary equals the kth sorted difference: before that value fewer than k pairs qualify, and at that value at least k qualify, even when multiple pairs share the same distance.

## Optimal solution, traced

```steps
Sort [1, 3, 1] to [1, 1, 3], k = 2
    candidate distances range from 0 to 2; try d = 1
---
Count distances at most 1
    right 1 contributes 1; right 2 contributes 0; total 1, too few
---
The only remaining candidate is 2
    all three pairs qualify; kth distance is {{2}}
```

## Code

```python
def kth_pair_distance(nums, k):
    ordered = sorted(nums)
    lo, hi = 0, ordered[-1] - ordered[0]
    while lo < hi:
        mid = lo + (hi - lo) // 2
        left, count = 0, 0
        for right in range(len(ordered)):
            while ordered[right] - ordered[left] > mid:
                left += 1
            count += right - left
        if count >= k:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

## Complexity

Sorting a copy costs O(n log n) time and O(n) auxiliary space. Each count is O(n), and binary search uses O(log(W + 1)) checks for value span W. Including sorting, total time is O(n log n + n log(W + 1)); auxiliary space is O(n), including the copied sorted list and sort workspace. When W is zero no check is needed, and the answer is zero. The caller's list remains unchanged.

## Mistakes and edge cases

- Count pairs rather than distinct distance values. A threshold can add several equal distances at once.
- Use `> mid` when moving the left pointer so pairs exactly at the threshold are included.
- Never reset the left pointer for each right endpoint if claiming linear check time.
- Validate k against the number of index pairs in a broader API; the implementation assumes the stated bounds.

## Variations

- Count pairs whose distance lies in a closed interval by subtracting counts at two thresholds.
- Return an original pair witnessing the answer with additional index tracking after the distance is known.

=== card | 4
time: 45 min

## The problem

Two integer lists are individually sorted in nondecreasing order. Return the median of their combined multiset without materializing the merged list. If the total length is odd, the median is the central value; if even, it is the arithmetic mean of the two central values. For `[1, 4]` and `[2, 3]`, the result is 2.5.

## Constraints and what they imply

Either list can be empty, but not both. Values can repeat or be negative. Sorting within each list is required, while their lengths can be very different. A logarithmic search in the shorter list avoids scanning a huge longer list when the shorter list is tiny. Equal values are separate occurrences, so all boundary comparisons must allow equality.

Let m be the shorter length and n the longer length. We need `(m + n + 1) // 2` elements in the lower half. If the total is odd, this gives the lower half one extra element. Choosing i elements from the short list fixes j, the number from the long list, to `half - i`. Since m <= n, every i from zero through m gives a valid j between zero and n. This fact prevents invalid cuts when the search operates on the full short-list range.

## Brute force

Merge the sorted lists and take the middle one or two values. A conventional merge takes O(m + n) time and O(m + n) space if the full result is stored. One can instead stream the merge up to the middle using O(1) extra space, but it still takes linear time. The materialized merge is a transparent independent reference for small tests, including repeated values and empty inputs.

## The insight

A cut takes the first i values from the short list and first j values from the long list into the left half. Each individual list is already sorted. Therefore the cut is globally correct exactly when the short left boundary is no greater than the long right boundary and the long left boundary is no greater than the short right boundary. Missing left boundaries act like negative infinity and missing right boundaries like positive infinity; they represent absent values, not actual input elements.

If the short left boundary exceeds the long right boundary, too many short-list elements are on the left. Decrease i. If the long left boundary exceeds the short right boundary, too few short-list elements are on the left. Increase i. These moves cannot discard a valid cut: moving i further in the wrong direction only increases the offending boundary and decreases the other. The finite interval shrinks until a valid partition is found. A valid cut always exists because one can conceptually merge the lists and take the lower half; that merge selects prefixes from both sorted lists.

At a valid cut, every left-side value is no greater than every right-side value. Thus the maximum left boundary is the middle value for an odd total. For an even total, the next value is the minimum right boundary, so their mean is the median. Ties are safe because the inequalities are non-strict. The proof concerns partition order, not the numerical midpoint of the values.

## Optimal solution, traced

```steps
A = [1, 4], B = [2, 3], half = 2
    try i = 1, j = 1; left boundaries 1 and 2, right boundaries 4 and 3
---
Both cross-boundary inequalities hold
    lower middle = max(1, 2) = 2; upper middle = min(4, 3) = 3
---
The total length is even
    median = (2 + 3) / 2 = {{2.5}}
```

## Code

```python
def median_two_sorted(first, second):
    if len(first) > len(second):
        first, second = second, first
    m, n = len(first), len(second)
    if m + n == 0:
        raise ValueError("at least one value is required")
    half = (m + n + 1) // 2
    lo, hi = 0, m
    while lo <= hi:
        i = lo + (hi - lo) // 2
        j = half - i
        left_a = first[i - 1] if i else float('-inf')
        right_a = first[i] if i < m else float('inf')
        left_b = second[j - 1] if j else float('-inf')
        right_b = second[j] if j < n else float('inf')
        if left_a > right_b:
            hi = i - 1
        elif left_b > right_a:
            lo = i + 1
        elif (m + n) % 2:
            return max(left_a, left_b)
        else:
            return (max(left_a, left_b) + min(right_a, right_b)) / 2
    raise ValueError("inputs must be sorted")
```

## Complexity

The shorter list has m elements, giving m + 1 possible cuts. Binary search takes O(log(m + 2)) time, including constant work when m is zero, and O(1) auxiliary space. Neither input is copied or mutated. The even result uses Python floating-point division; extremely large integers can exceed its floating-point range or precision, so use an exact rational representation if such inputs are required.

## Mistakes and edge cases

- Swap by length before searching; otherwise j can leave the long list's valid index range.
- Use the larger left boundary and smaller right boundary, not the average of arbitrary cut neighbors.
- Empty one-sided inputs, unequal lengths, duplicates, and cuts at either end require the infinity sentinels. Both-empty input is explicitly rejected.
- Inputs are assumed sorted; the final exception does not promise to detect every unsorted input.

## Variations

- Return the two middle elements separately to avoid floating-point rounding.
- Generalize the cut to select an arbitrary rank by changing the desired left-half size and restricting the feasible cut range.

=== card | 154
time: 40 min

## The problem

Find the minimum in a nonempty nondecreasing integer list that was cyclically rotated, when equal values are allowed. For `[2, 2, 3, 1, 2]`, return 1. The input need not have an observable drop, and every value may be identical.

## Constraints and what they imply

The original list is sorted with duplicates and rotated at some boundary. Each side of that boundary is nondecreasing, but equal values can occur on both sides. A one-element list is valid. Unlike the distinct-value version, comparing against a fixed last element does not necessarily produce a single false prefix followed by a true suffix: `[1, 1, 0, 1]` is a counterexample for the predicate `value <= last`.

The algorithm must preserve at least one occurrence of the minimum, not necessarily every occurrence or the original rotation index. This distinction permits removing one value when it has an equal copy. It also means the returned result is a value; identifying a unique rotation point is ambiguous when the values are all equal.

## Brute force

Scan the entire array and retain the smallest value. This always takes O(n) time and O(1) auxiliary space and is the appropriate simple reference. Finding the first adjacent drop also works if one exists, falling back to the first value otherwise, but likewise can require a complete scan. The binary-search approach can eliminate many candidates on informative comparisons without guaranteeing logarithmic worst-case time.

## The insight

Keep an inclusive interval `[lo, hi]` containing at least one minimum. Compare its midpoint with its right endpoint. If the midpoint is greater, the interval cannot be nondecreasing all the way from midpoint to hi: the rotation drop lies to its right, so a minimum lies in `[mid + 1, hi]`. Discard through mid. If the midpoint is smaller, a minimum lies in `[lo, mid]`; the segment from mid to hi cannot contain the wrap to a strictly smaller value that is hidden from the comparison, so retain mid and discard the right side.

When the two values are equal, the comparison does not locate the drop. However, the right endpoint can be discarded safely: if it is a minimum, the identical midpoint is another minimum that remains; if it is not, discarding it cannot remove the minimum. Thus decrement hi by one. In all three cases the interval shrinks and still contains a minimum. At convergence its only element is a minimum.

Equality creates unavoidable uncertainty on inputs such as a long run of the same value with a single smaller value hidden somewhere. Until that location is inspected, an adversary can place the smaller value among the uninspected positions. Consequently no comparison algorithm can guarantee logarithmic worst-case time on this input family. Informative strict comparisons halve the interval, but equality steps can remove only one candidate each; an average-case claim requires a specified input distribution.

## Optimal solution, traced

```steps
Input [2, 2, 3, 1, 2]
    lo = 0, hi = 4, mid = 2; 3 > 2, so keep indices 3 through 4
---
Compare mid index 3 with hi index 4
    1 < 2, so keep index 3 and anything to its left in the interval
---
Bounds meet at index 3
    minimum value is {{1}}
```

For `[1, 1, 0, 1]`, the first comparison is equal; discarding the rightmost 1 retains the hidden minimum. This is why equality must not be treated as evidence that either whole half is safe to remove.

## Code

```python
def find_min_with_duplicates(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        elif nums[mid] < nums[hi]:
            hi = mid
        else:
            hi -= 1
    return nums[lo]
```

## Complexity

There are at most n-1 iterations because each strictly reduces the candidate interval. Worst-case time is O(n), as on all-equal input, and auxiliary space is O(1). If every iteration is a strict comparison, time is O(log n); mixed inputs have a cost depending on the number of equality steps. The list is unchanged.

## Mistakes and edge cases

- On equality, removing an entire half can discard the unique smaller element. Remove only one duplicated endpoint.
- Use `hi = mid` on a smaller midpoint, since mid itself can be the minimum.
- The nonempty input assumption is necessary before indexing the result. Unrotated, one-element, and all-equal arrays are valid.
- The minimum value can appear on both sides of the rotation. Do not infer a unique cut from the returned value.

## Variations

- Search for a target with duplicates by shrinking ambiguous equal endpoints, accepting linear worst-case time.
- Return an index of a minimum rather than its value, without promising the original rotation point.
