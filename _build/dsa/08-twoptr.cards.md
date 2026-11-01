=== card | 283
time: 20 min

## The problem

Move every zero in an integer list to its end, retaining the relative order of all nonzero values. Change the given list in place. For `[0, 4, 0, -2]`, the final list is `[4, -2, 0, 0]`.

## Constraints and what they imply

Values can be negative, repeated, or zero. The list may consist entirely of zeros or contain no zeros. Stability applies to nonzero values; sorting is not a valid replacement. The list object must be modified rather than replaced with a separate answer.

## Brute force

Scan for zeros, remove each one and append it at the end, while limiting the scan to the original live prefix. Each deletion shifts a suffix, so many zeros can require O(n²) time. Building a separate nonzero list is linear but uses O(n) auxiliary space.

## The insight

The read index visits each original position once. The write index is the number of nonzeros already seen. When a nonzero is read, swap it with the first unfilled position and increment write. Before each iteration the prefix before write contains exactly the nonzeros seen so far, in order; the region from write to read contains only zeros. Thus the swap extends the prefix without disturbing its order.

## Optimal solution, traced

```steps
Start [0, 4, 0, -2], write = 0
    read 0: skip zero
---
Read 4: swap with index 0
    [4, 0, 0, -2], write = 1
---
Read -2: swap with index 1
    {{[4, -2, 0, 0]}}
```

Each read advances, including when write and read coincide. Once the scan finishes, every position outside the stable nonzero prefix is zero.

## Code

```python
def move_zeroes(nums):
    write = 0
    for read in range(len(nums)):
        if nums[read] != 0:
            nums[write], nums[read] = nums[read], nums[write]
            write += 1
```

## Complexity

The scan takes O(n) time and O(1) auxiliary space. Swapping an element with itself is harmless.

## Mistakes and edge cases

- Advancing write for a zero breaks the prefix invariant.
- Return value is `None`; inspect the mutated list.
- Empty lists and lists with one value need no special case.

## Variations

- Compact values satisfying another predicate while preserving their order.
- Return the length of the retained prefix instead of moving zeros to the end.

=== card | 680
time: 20 min

## The problem

Determine whether a string can read identically from both ends after deleting at most one character. No deletion is required if it is already symmetric. For `"abca"`, removing either `b` or `c` succeeds; `"abc"` cannot be fixed with one deletion.

## Constraints and what they imply

The input is a sequence of characters; comparisons are exact and case-sensitive. The original task uses lowercase English letters. A single deletion can occur at either end of the first mismatching pair, but not at both. Empty and one-character strings are already palindromes.

## Brute force

Try leaving the string unchanged and then deleting each position in turn, checking every resulting string for symmetry. Each check or slice takes O(n), giving O(n²) time and O(n) temporary space.

## The insight

Walk inward while opposite characters agree. At the first mismatch, a valid one-deletion answer must delete one of these two characters: deleting something strictly between them leaves the mismatched endpoints unchanged. Test the two remaining ranges without further deletions. Earlier matched pairs remain valid around either choice.

## Optimal solution, traced

```steps
"abca": compare a with a
    move inward to b and c
---
Mismatch b versus c
    skip b: remaining range is "c", a palindrome
---
One deletion suffices
    return {{True}}
```

If neither candidate range is symmetric, every allowed deletion fails at the first mismatch. A helper uses indices rather than allocating substrings.

## Code

```python
def valid_palindrome(s):
    def symmetric(left, right):
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    left, right = 0, len(s) - 1
    while left < right and s[left] == s[right]:
        left += 1
        right -= 1
    return left >= right or symmetric(left + 1, right) or symmetric(left, right - 1)
```

## Complexity

The initial scan and the two candidate scans together take O(n) time, with O(1) auxiliary space.

## Mistakes and edge cases

- Choosing only the left or only the right deletion misses valid answers.
- Do not allow another deletion inside the helper.
- A mismatch in a two-character string can always be repaired.

## Variations

- Return a deletion index, with a special value when no deletion is needed.
- Permit up to k deletions; use dynamic programming rather than assuming two branches suffice.

=== card | 88
time: 20 min

## The problem

Two sorted lists contain `m` and `n` meaningful values. The first list has `n` extra slots at its end. Merge the second list into the first in nondecreasing order, modifying the first list in place. For `[1, 4, 0, 0]`, `m=2`, and `[2, 3]`, the result is `[1, 2, 3, 4]`.

## Constraints and what they imply

Both meaningful prefixes are sorted, values may repeat or be negative, and either count may be zero. The extra slots are capacity, not data: their initial values must not affect comparisons. The lists are distinct and the first has exactly enough space.

## Brute force

Copy both meaningful ranges into a new list, sort it, and overwrite the first list. This takes O((m+n) log(m+n)) time and O(m+n) extra space. Alternatively, inserting each second-list element into the first can shift many existing values and cost O(mn).

## The insight

Write the largest remaining value at the last unfilled slot. Reading from the back prevents overwriting an unread first-list value: while second-list values remain, the write index is strictly to the right of the first-list read index. After each step the suffix is the sorted collection of the largest values already selected.

## Optimal solution, traced

```steps
[1, 4, _, _] and [2, 3]
    write 4 at index 3
---
Compare 1 and 3, then 1 and 2
    write 3 at index 2 and 2 at index 1
---
The remaining 1 is already in place
    result {{[1, 2, 3, 4]}}
```

When the second list is exhausted, the untouched first-list prefix is already in its final location. If the first prefix runs out first, copy all remaining second-list values.

## Code

```python
def merge_sorted(nums1, m, nums2, n):
    i, j, write = m - 1, n - 1, m + n - 1
    while j >= 0:
        if i >= 0 and nums1[i] > nums2[j]:
            nums1[write] = nums1[i]
            i -= 1
        else:
            nums1[write] = nums2[j]
            j -= 1
        write -= 1
```

## Complexity

At most `m+n` values are written, for O(m+n) time and O(1) auxiliary space.

## Mistakes and edge cases

- Merging forward directly into the first list overwrites unread values.
- Stop only after the second list is exhausted, not when either pointer reaches zero.
- Placeholder zeros are not part of the sorted prefix.

## Variations

- Merge into a new list by scanning forward.
- Merge several sorted lists using a heap of current heads.

=== card | 167
time: 25 min

## The problem

Given a nondecreasing integer array and a target, find two distinct positions whose values sum to the target. Return their one-based indices in increasing order. For `[1, 3, 4, 8]` and target `7`, return `[2, 3]`.

## Constraints and what they imply

The input is sorted and the original task guarantees exactly one valid pair. Indices must refer to the original array and the same element cannot be used twice. Duplicate values can be used if they occupy distinct positions. The function below returns an empty list if no pair exists, which also makes its behavior explicit outside the guarantee.

## Brute force

Inspect every pair of indices `i < j`, returning the first matching sum. There are O(n²) pairs and only O(1) auxiliary space is required. The repeated comparisons ignore the information supplied by sorted order.

## The insight

Start at both ends. If their sum is too small, the left value cannot make the target with any remaining partner, because the right value is the largest available. Discard the left index. If the sum is too large, the right value cannot match even with the smallest available left value, so discard the right index. Equality immediately gives the desired indices.

## Optimal solution, traced

```steps
[1, 3, 4, 8], target 7
    1 + 8 = 9: discard 8
---
1 + 4 = 5: discard 1
    3 + 4 = 7
---
Indices 1 and 2 are zero-based
    return {{[2, 3]}}
```

Every discarded endpoint is proved unable to participate in a solution among the remaining candidates. Therefore a solution remains inside the interval until it is found. The interval strictly shrinks on each mismatch, so the procedure terminates.

For example, with `[2, 2]` and target 4, the initial pointers refer to different positions even though their values match; the returned indices are `[1, 2]`. With `[-5, -1, 3, 9]` and target 2, the sum at the outer endpoints is 4, so moving the right endpoint reveals the pair `-1` and `3`. Negative numbers do not invalidate the argument: only sorted order and the direction of the sum comparison matter.

## Code

```python
def two_sum_sorted(numbers, target):
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return [left + 1, right + 1]
        if total < target:
            left += 1
        else:
            right -= 1
    return []
```

## Complexity

Each step moves one endpoint, so time is O(n) and auxiliary space is O(1), excluding the two-index result.

## Mistakes and edge cases

- Use `left < right`, not `<=`, to prevent using one index twice.
- Convert both indices to one-based positions.
- Applying the discard argument to unsorted input is invalid.
- With no solution, this implementation returns `[]`; under the original guarantee that branch is unreachable.

## Variations

- Count all index pairs under a sum threshold, accounting for duplicates.
- If input is unsorted and original indices are required, use a map or sort value-index pairs.

=== card | 881
time: 30 min

## The problem

People have weights and a boat has a weight limit. Each boat carries at most two people. Find the minimum boats needed to carry everyone. For weights `[1, 2, 2, 3]` and limit `3`, one optimal arrangement is `(1, 2)`, `(2)`, `(3)`, requiring three boats.

## Constraints and what they imply

Every person has positive weight no greater than the limit, so a person can always travel alone. Each person must be assigned exactly once. Two people may share only when their combined weight is at most the limit; duplicate weights represent distinct people. An empty input needs zero boats.

## Brute force

Enumerate the possible singleton and pair groupings, discard those exceeding the limit, and choose one with the fewest groups. The number of groupings grows exponentially. Even a matching formulation explores much more structure than necessary when the order of weights reveals a safe greedy decision.

## The insight

Sort the weights and consider the heaviest remaining person. If even the lightest remaining person cannot fit with them, nobody can, so the heaviest must travel alone. Otherwise pair the two extremes. To justify this, take an optimal arrangement. If the heaviest travels with `p` and the lightest travels with `q`, replace those two boats by `(heaviest, lightest)` and `(p, q)`. The first pair fits by the greedy test; the second fits because `q` weighs at most the heaviest, so `p + q <= p + heaviest <= limit`.

If either extreme was alone, the same exchange uses no more boats: pair the extremes and, if necessary, send the displaced partner alone. Thus an optimal arrangement can always be transformed to include the greedy boat. Repeating the argument on the remaining people proves optimality.

## Optimal solution, traced

```steps
Sorted weights [1, 2, 2, 3], limit 3
    1 + 3 > 3: send 3 alone
---
1 + 2 = 3: pair them
    remaining [2]
---
Send the last 2 alone
    boats = {{3}}
```

Every iteration removes the heaviest person and sometimes the lightest, with one boat counted. The exchange argument preserves the existence of an optimal completion after each choice.

## Code

```python
def rescue_boats(people, limit):
    weights = sorted(people)
    left, right = 0, len(weights) - 1
    boats = 0
    while left <= right:
        if left < right and weights[left] + weights[right] <= limit:
            left += 1
        right -= 1
        boats += 1
    return boats
```

## Complexity

Sorting costs O(n log n) time and O(n) space for the sorted copy. The scan costs O(n) time and O(1) additional working space beyond that copy.

## Mistakes and edge cases

- A remaining single person still needs a boat; use `left <= right`.
- Do not pair the heaviest with someone when the limit would be exceeded.
- The greedy proof relies on at most two occupants and each person fitting alone.

## Variations

- Return actual passenger pairs as well as the count.
- For three or more seats per boat, this exchange rule no longer solves the general packing problem.

=== card | 15
time: 35 min

## The problem

Find every distinct value triple drawn from three different positions whose sum is zero. Return each triple once, regardless of how many index triples produce it. For `[-2, 0, 1, 1, 2]`, the results are `[-2, 0, 2]` and `[-2, 1, 1]`.

## Constraints and what they imply

Values may be negative, positive, or repeated; three equal values are valid when there are at least three occurrences. Order of triples in the answer is immaterial. Since the result is expressed as values, sorting a copy does not lose required original indices. Lists shorter than three have no answer.

## Brute force

Enumerate every index triple `i < j < k`, test its sum, and add each sorted value triple to a set. This takes O(n³) time with space proportional to the distinct results. Repeated index combinations often represent the same value triple.

## The insight

Sort the values. Fix the first index, then search the suffix with opposite-end pointers for the remaining sum. A sum below zero rules out the current left value with every available right value; a sum above zero similarly rules out the current right value. On equality, record the triple and advance past the used values at both ends. Skip a fixed value if it equals the previous fixed value: the earlier occurrence already considered every possible suffix value pair.

## Optimal solution, traced

```steps
Sorted [-2, 0, 1, 1, 2]; fix -2
    0 + 2 - 2 = 0: record [-2, 0, 2]
---
Move past 0 and 2
    1 + 1 - 2 = 0: record [-2, 1, 1]
---
Later anchors find no new zero triple
    return {{[[-2, 0, 2], [-2, 1, 1]]}}
```

For each fixed value the pointer discard proof finds every feasible value pair. Skipping equal matched endpoints cannot lose a different triple because the fixed value and the other matched value are unchanged. Repeating an anchor would only reproduce triples already searched with its earlier occurrence. Thus all output triples are valid and unique, and no valid triple is missed.

## Code

```python
def three_sum(nums):
    values = sorted(nums)
    result = []
    for i in range(len(values) - 2):
        if i and values[i] == values[i - 1]:
            continue
        left, right = i + 1, len(values) - 1
        while left < right:
            total = values[i] + values[left] + values[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                result.append([values[i], values[left], values[right]])
                a, b = values[left], values[right]
                while left < right and values[left] == a:
                    left += 1
                while left < right and values[right] == b:
                    right -= 1
    return result
```

## Complexity

Sorting takes O(n log n); at most n suffix scans each take O(n), so total time is O(n²). The sorted copy uses O(n) auxiliary space, excluding the potentially O(n²) output.

## Mistakes and edge cases

- Skip repeated anchors only after an earlier identical anchor was processed.
- Check `left < right` during duplicate skips so indices remain distinct.
- `[0, 0, 0, 0]` produces exactly one triple, not zero or four.

## Variations

- Find triples summing to an arbitrary target by replacing the zero comparison.
- Count index triples rather than distinct value triples; repeated values now affect multiplicity.

=== card | 75
time: 30 min

## The problem

Rearrange a list containing only 0, 1, and 2 into nondecreasing order, in place. For `[2, 0, 2, 1, 0]`, the result is `[0, 0, 1, 2, 2]`.

## Constraints and what they imply

Every element is one of exactly three categories. The required result is a mutation of the input list, not a separate list. Equal items have no individual identity to preserve. Empty and single-element lists are already sorted.

## Brute force

Use a comparison sort on the list, which costs O(n log n) time in a general sorting model. A two-pass alternative counts each category and overwrites the list in O(n) time and O(1) counting space, but does not classify the items in a single traversal.

## The insight

Maintain four regions: zeros before `low`, ones from `low` through `scan - 1`, unknown values from `scan` through `high`, and twos after `high`. When the current value is zero, swap it into the zero region and advance both left boundaries. A one simply joins the middle region. A two moves to the right region; the value swapped in from the unknown right end must be examined before scan advances.

## Optimal solution, traced

```steps
[2, 0, 2, 1, 0], low = scan = 0, high = 4
    swap 2 with index 4: [0, 0, 2, 1, 2]
---
Process the two zeros, then swap the next 2 with 1
    [0, 0, 1, 2, 2]
---
Inspect the swapped-in 1; unknown region is empty
    result {{[0, 0, 1, 2, 2]}}
```

Each action preserves the four regions. In the zero case the swapped-in value is a known one when `low < scan`, or the same zero when the indices coincide, so moving scan is safe. Every action shrinks the unknown region by one, and when it is empty the three ordered regions cover the list.

Consider `[2, 2, 0]`: swapping the first two with the final zero gives `[0, 2, 2]`. The scan must stay at the first index to classify that zero; skipping it would leave the low boundary incorrect and can fail on larger examples. If the current value is one, no swap is needed because extending the middle region preserves its definition. This invariant also explains why the algorithm works without counting individual categories beforehand.

## Code

```python
def sort_colors(nums):
    low, scan, high = 0, 0, len(nums) - 1
    while scan <= high:
        if nums[scan] == 0:
            nums[low], nums[scan] = nums[scan], nums[low]
            low += 1
            scan += 1
        elif nums[scan] == 1:
            scan += 1
        else:
            nums[scan], nums[high] = nums[high], nums[scan]
            high -= 1
```

## Complexity

The unknown region loses one element per iteration, so time is O(n), with O(1) auxiliary space.

## Mistakes and edge cases

- Advancing scan after swapping a two can skip a zero from the right.
- Use an inclusive high index and stop only when `scan > high`.
- The code assumes the promised three-value domain; it does not validate other values.

## Variations

- Partition arbitrary values into less than, equal to, and greater than a pivot.
- Count the three categories first and overwrite in a second pass.

=== card | 11
time: 35 min

## The problem

An array gives the heights of vertical lines at consecutive horizontal positions. Choose two lines to form the sides of a container; its capacity is their horizontal separation times the shorter height. Return the largest capacity. For heights `[1, 4, 2, 3]`, lines at indices 1 and 3 hold area 6.

## Constraints and what they imply

At least two nonnegative heights are supplied in the original task. The container sides must use different indices; no slant changes their effective width. Zero heights produce zero area. Heights need not be sorted, so pointer movement must be justified by the area bound, not by value order.

## Brute force

Evaluate every pair `i < j`, compute `(j-i) * min(height[i], height[j])`, and retain the maximum. This takes O(n²) time and O(1) auxiliary space. The quadratic search repeatedly considers narrow containers whose limiting side has already been bounded by a wider one.

## The insight

Start with the widest possible pair. After recording its area, discard a side with the smaller height. Suppose the left side is no taller. Any container using that same left side and an interior right endpoint has smaller width and height at most the left height, so it cannot beat the current area. Therefore discarding that left side cannot discard a strictly better answer. The argument is symmetric for the right side.

When heights tie, either side can be discarded by the same reasoning. We have already accounted for the only pair using both current endpoints. Consequently an optimal area either has already been recorded or remains among the surviving indices. The interval shrinks until no pair remains.

## Optimal solution, traced

```steps
[1, 4, 2, 3]: endpoints 0 and 3
    area = 3 * 1 = 3; discard height 1
---
Endpoints 1 and 3
    area = 2 * 3 = {{6}}; discard height 3
---
Endpoints 1 and 2 give area 2
    best remains {{6}}
```

In the first move every other container using index 0 has width below 3 and height at most 1. In the next move every other container using index 3 and a remaining interior endpoint has width below 2 and height at most 3. Those pairs cannot improve the recorded best.

## Code

```python
def max_container(height):
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        best = max(best, (right - left) * min(height[left], height[right]))
        if height[left] <= height[right]:
            left += 1
        else:
            right -= 1
    return best
```

## Complexity

Each iteration shrinks the range, so O(n) time and O(1) auxiliary space suffice.

## Mistakes and edge cases

- Moving the taller side lacks the necessary discard guarantee.
- Width is the difference of indices, not the number of bars between them.
- Equal heights permit either movement; all-zero inputs return zero.

## Variations

- Return the indices as well as the maximum area, choosing a tie rule.
- With irregular x-coordinates, use their actual separation; the discard argument still holds for ordered coordinates.

=== card | 42
time: 45 min

## The problem

The array gives nonnegative bar heights at consecutive unit-width positions. After rain, water fills depressions but can escape past either end. Compute the total number of unit squares of water held above the bars. For `[2, 0, 1, 0, 2]`, the water depths are `[0, 2, 1, 2, 0]`, totaling 5.

## Constraints and what they imply

The bars have unit width and nonnegative integer heights. Water above a position cannot exceed the shorter of the highest wall on its left and the highest wall on its right. A boundary position cannot hold water because one side has no higher wall outside the array. The implementation also accepts empty or short arrays, returning zero; no bar is changed.

Do not confuse the answer with the maximum container area: water is counted above each individual bar, and an interior bar occupies space that cannot hold water. Local dips alone are insufficient to determine the water depth, because a taller boundary may occur much farther away.

## Brute force

For each position, scan the whole prefix to find its maximum and the whole suffix to find its maximum. The position contributes `min(left_max, right_max) - height[i]`. Adding these independent depths takes O(n²) time and O(1) working space if maxima are computed by loops. Precomputing both maximum arrays reduces time to O(n) at the cost of O(n) extra space.

The two-pointer approach retains only the strongest boundary found from each end. It decides when one position's limiting boundary is known without storing an answer or maximum for every position.

## The insight

Keep indices `left` and `right` for the unprocessed interval and maxima `left_max` and `right_max` for bars already processed from their respective sides. If `left_max <= right_max`, process the next left bar. After incorporating that bar into `left_max`, its final water level is determined: when the updated left maximum remains at most `right_max`, an already seen right wall is at least as high as that maximum, so the left maximum is the limiting wall. If the new bar itself exceeds `right_max`, its water depth is zero, and including it as the new left maximum still gives the correct contribution of zero.

The other case is symmetric. Each side's maximum contains all bars scanned from that boundary, and any unprocessed interior wall can only increase the opposite-side maximum. Therefore, when a known opposite boundary is already high enough, no unseen bar can change the limiting level. The code counts each position exactly once and narrows the interval until it is empty.

## Optimal solution, traced

```steps
[2, 0, 1, 0, 2]: left_max = right_max = 0
    process left 2: left_max = 2, water = 0
---
Process right 2: right_max = 2, water = 0
    left_max <= right_max, so process the remaining left side
---
Heights 0, 1, 0 contribute 2, 1, 2
    total water = {{5}}
```

For a second boundary case, `[3, 0, 1]` first establishes left maximum 3 and right maximum 1. The right side is now limiting, so the middle zero contributes only 1, not 3. If all heights increase monotonically, the side being processed never has a positive depth, yielding zero.

The correctness invariant has two parts: the total equals the exact water over processed positions, and each maximum is the highest processed bar on its side. Processing a bar updates its side's maximum before adding its contribution, so the contribution cannot be negative. The limiting-side argument establishes that this contribution is final; updating a maximum preserves the second part. As each iteration consumes one unprocessed bar, all positions are covered at termination.

## Code

```python
def trapped_water(height):
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    total = 0
    while left <= right:
        if left_max <= right_max:
            left_max = max(left_max, height[left])
            total += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            total += right_max - height[right]
            right -= 1
    return total
```

## Complexity

Every bar is consumed once, so time is O(n). Only indices, maxima, and the total are stored, giving O(1) auxiliary space. Python integers grow as necessary; in fixed-width languages, the accumulator may require a wider type than a single height.

## Mistakes and edge cases

- Using only the maximum on one side overestimates water when the other boundary is lower.
- Update the relevant maximum before computing the depth, especially for a new record-height bar.
- A flat array, monotone array, empty array, or one or two bars all contain zero water.
- The result sums water depths, not the area between outermost bars.

## Variations

- Return the water depth at each index using prefix and suffix maxima arrays.
- Use a monotone stack to fill bounded basins by horizontal layers.
- For a two-dimensional elevation map, use a boundary min-heap instead of this one-dimensional argument.

=== card | 18
time: 40 min

## The problem

Find every distinct quadruple of values from four different array positions that sums to a given target. For `[1, 0, -1, 0, -2, 2]` and target zero, the distinct answers are `[-2, -1, 1, 2]`, `[-2, 0, 0, 2]`, and `[-1, 0, 0, 1]`.

## Constraints and what they imply

Values and target can be negative, zero, or positive, and duplicate values can be used as often as distinct positions permit. Output is unique by value, not by position. Sorting a copy is safe because original indices are not requested. An array with fewer than four entries yields no quadruples.

## Brute force

Enumerate all index quadruples `i < j < k < l`, retain those whose sum is the target, and place sorted value tuples in a set. That costs O(n⁴) time, plus space for the unique results. Large groups of equal values cause many different index choices to produce the same answer.

## The insight

Sort the values, fix two indices in increasing order, then find the remaining pair with opposite-end pointers in the suffix. A sum below the target cannot be fixed by retaining the left endpoint and moving the right endpoint inward; a sum above the target cannot be fixed by retaining the right endpoint and moving the left inward. Each comparison thus safely eliminates one endpoint.

Skip duplicate first and second fixed values within their respective loops. After a match, move both suffix pointers past their matched values. Earlier occurrences have already searched the same value combinations with at least as much suffix available, so these skips eliminate duplicate results rather than distinct quadruples.

## Optimal solution, traced

```steps
Sort [-2, -1, 0, 0, 1, 2], target 0
    fix -2 and -1; pair 1 and 2 gives [-2, -1, 1, 2]
---
Fix -2 and 0; pair 0 and 2 gives [-2, 0, 0, 2]
    skip the second equal fixed 0
---
Fix -1 and 0; pair 0 and 1
    final additional answer {{[-1, 0, 0, 1]}}
```

For a fixed prefix, the two-pointer discard rule visits every feasible distinct pair. Any sorted valid quadruple has an earliest equivalent choice of the two fixed values; that choice has enough remaining occurrences to realize the suffix. Hence skipping later equal anchors does not remove its first representation. Index order ensures four distinct positions, while duplicate skips give one output per value quadruple.

## Code

```python
def four_sum(nums, target):
    values = sorted(nums)
    n = len(values)
    result = []
    for i in range(n - 3):
        if i and values[i] == values[i - 1]:
            continue
        for j in range(i + 1, n - 2):
            if j > i + 1 and values[j] == values[j - 1]:
                continue
            left, right = j + 1, n - 1
            while left < right:
                total = values[i] + values[j] + values[left] + values[right]
                if total < target:
                    left += 1
                elif total > target:
                    right -= 1
                else:
                    result.append([values[i], values[j], values[left], values[right]])
                    a, b = values[left], values[right]
                    while left < right and values[left] == a:
                        left += 1
                    while left < right and values[right] == b:
                        right -= 1
    return result
```

## Complexity

There are O(n²) anchor pairs and each suffix scan takes O(n), so time is O(n³), including the asymptotically smaller sort. The sorted copy uses O(n) auxiliary space, excluding up to O(n³) output.

## Mistakes and edge cases

- Skip the second anchor only relative to the start of its own loop.
- Do not use the same index twice; all four indices must increase.
- In fixed-width languages, summing four values may require a wider integer type.

## Variations

- Generalize to k-sum by recursively fixing values and using a two-pointer base case.
- Count index quadruples rather than unique value quadruples, preserving multiplicities.

=== card | 611
time: 35 min

## The problem

Count index triples whose three lengths can form a triangle with positive area. Each index can be used once per triple, and equal lengths at different indices are distinct choices. For `[2, 2, 3, 4]`, three triples work: the two choices of `(2, 3, 4)` and `(2, 2, 3)`.

## Constraints and what they imply

Lengths are nonnegative in the original task; zero cannot participate in a valid triangle. A triangle requires the sum of any two sides to exceed the third. After sorting, it suffices to check that the two smaller values sum to more than the largest. We count index triples, not distinct length triples, so duplicates contribute separately.

## Brute force

Enumerate every `i < j < k` and test all three triangle inequalities, incrementing the answer for each valid triple. There are O(n³) triples, and the scan needs O(1) working space. Repeating the same inequality for many nearby index pairs is unnecessary after sorting.

## The insight

Sort the lengths and fix the largest index `k`. Use `left=0` and `right=k-1`. If `values[left] + values[right] > values[k]`, then every index between left and right also pairs with right to make a triangle, since those values are at least `values[left]`. Count `right-left` such pairs at once and move right down. Otherwise the current left value cannot work with any available partner, because right is the largest one; increase left.

Each iteration either counts all still-eligible pairs ending at right or discards a left index that cannot be part of a valid pair in the current range. No pair is counted twice, because counted pairs are assigned to a unique right endpoint and largest index. All valid triples are eventually counted.

## Optimal solution, traced

```steps
Sorted [2, 2, 3, 4]; fix 4
    2 + 3 > 4: count 2 pairs, move right to index 1
---
2 + 2 is not greater than 4
    discard left; no further pair for 4
---
Fix 3: 2 + 2 > 3 adds 1
    total = {{3}}
```

For the first count, the two equal twos are at different indices and both pair with the 3. A strict comparison correctly rejects degenerate triples whose smaller lengths sum exactly to the largest. Zeros automatically fail because a nonnegative smaller side cannot combine with zero to exceed the largest.

## Code

```python
def triangle_count(nums):
    values = sorted(nums)
    total = 0
    for k in range(len(values) - 1, 1, -1):
        left, right = 0, k - 1
        while left < right:
            if values[left] + values[right] > values[k]:
                total += right - left
                right -= 1
            else:
                left += 1
    return total
```

## Complexity

Sorting costs O(n log n); each of n fixed largest indices has an O(n) scan, for O(n²) time overall. The sorted copy uses O(n) auxiliary space.

## Mistakes and edge cases

- Using `>=` counts zero-area degenerate triples.
- Deduplicating equal lengths loses valid index triples.
- Fewer than three entries and all-zero arrays return zero.

## Variations

- Count triples with sum below a threshold using a related sorted pair-counting scan.
- Return the valid index triples, retaining original indices and accepting output-sensitive cost.
