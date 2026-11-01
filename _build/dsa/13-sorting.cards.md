=== card | 1122
time: 20 min

## The problem

Reorder a list of non-negative integers using a separate priority list: values named there come first in that exact order, with all their occurrences together. Values absent from the priority list follow in ascending order. For `[2, 1, 2, 3, 1]` and `[2, 1]`, return `[2, 2, 1, 1, 3]`. The result must preserve the input's multiset.

## Constraints and what they imply

Input values lie in `0..1000`; priority values are distinct and occur in the input. Repeated input values are separate occurrences. This small, fixed universe makes a count array practical even when the input contains many duplicates. An empty input and an empty priority list are also meaningful extensions.

## Brute force

For each priority value scan the entire input and emit matches, then sort all unmentioned values. With n items and p priorities this takes O(np + n log n) time and O(n + p) space. Scanning repeatedly rediscovers the same frequencies.

## The insight

Count each input value once. Emit the requested buckets in priority order, clearing each emitted bucket so it cannot appear again. Then sweep the whole universe from low to high. Every occurrence is emitted exactly once: either its bucket was cleared by the priority phase or it remains for the ascending phase.

## Optimal solution, traced

```steps
Input [2, 1, 2, 3, 1], priority [2, 1]
    counts: 1 -> 2, 2 -> 2, 3 -> 1
---
Emit 2 twice, then 1 twice; clear both buckets
    result [2, 2, 1, 1]
---
Sweep remaining buckets ascending; emit 3
    result {{[2, 2, 1, 1, 3]}}
```

## Code

```python
def relative_sort(values, priority):
    counts = [0] * 1001
    for value in values:
        counts[value] += 1
    result = []
    for value in priority:
        result.extend([value] * counts[value])
        counts[value] = 0
    for value, count in enumerate(counts):
        result.extend([value] * count)
    return result
```

## Complexity

For universe size V=1001, n input values and p priorities, counting, emission and sweeping take O(n + p + V) time. Counts use O(V) auxiliary space and the returned list uses O(n). Neither input is modified.

## Mistakes and edge cases

- Forgetting to clear a priority bucket emits its values twice.
- A priority list need not be numerically sorted; only leftovers are.
- This array representation assumes the stated non-negative bounded domain; use a map for other values.

## Variations

- For an unbounded universe, count with a dictionary and sort only the unmentioned distinct values.
- Change the final sweep to descending order if leftovers must be largest first.

=== card | 1636
time: 20 min

## The problem

Return the input numbers ordered by increasing occurrence count. When two different numbers have the same count, put the larger number first. For `[4, 4, -1, -1, 2]`, the result is `[2, 4, 4, -1, -1]`. Each occurrence appears as many times as it did originally.

## Constraints and what they imply

Counts refer to the original collection, not a changing prefix. Integers may be negative and duplicates count individually. The input may be empty in this implementation. A lexicographic tuple can encode both priorities without a hand-written comparator.

## Brute force

For every element, scan the list to compute its frequency, cache that element's ordering key and then sort. Frequency computation costs O(n²), followed by O(n log n) sorting; the copied output uses O(n) space. Recounting equal numbers is unnecessary.

## The insight

Build a frequency map in one pass. Sort each number x by `(frequency[x], -x)`. Python compares the frequency first in ascending order; for equal frequencies, negating x makes the larger original value have the smaller key. The tuple exactly expresses the requested two-stage rule.

## Optimal solution, traced

```steps
Input [4, 4, -1, -1, 2]
    frequencies: 4 -> 2, -1 -> 2, 2 -> 1
---
Keys: 2 -> (1, -2), 4 -> (2, -4), -1 -> (2, 1)
    first compare frequencies, then the negated values
---
Sorted keys give {{[2, 4, 4, -1, -1]}}
```

Every pair of distinct values is ordered according to its frequency or, on a tie, its descending numeric value. Sorting the occurrences by that key therefore satisfies the whole rule and cannot change their multiplicities.

## Code

```python
from collections import Counter

def frequency_sort_numbers(values):
    counts = Counter(values)
    return sorted(values, key=lambda value: (counts[value], -value))
```

## Complexity

Counting takes O(n) expected time, and sorting takes O(n log n) time. The frequency map and sorted output together use O(n) space. The caller's list is unchanged.

## Mistakes and edge cases

- Sorting by `(count, value)` reverses the requested tie-break.
- Negating the count instead would sort frequent numbers first.
- Negative values work because negation reverses their numeric order too.

## Variations

- Order equal-frequency values ascending by replacing `-value` with `value`.
- For a tiny bounded integer domain, bucket distinct values by frequency before emitting them.

=== card | 976
time: 20 min

## The problem

Choose three lengths that form a nondegenerate triangle and return the largest achievable perimeter, or zero when no triple works. For `[2, 1, 2, 4]`, the best valid triple is `(2, 2, 1)`, with perimeter 5. Each chosen length must come from a different input position.

## Constraints and what they imply

Lengths are positive integers and there are at least three in the original task. This implementation also accepts shorter lists. Once three positive lengths are sorted as a >= b >= c, only the strict inequality b + c > a needs checking; equality is a flat, invalid triangle.

## Brute force

Enumerate every triple, check its largest side against the other two, and keep the largest valid sum. This takes O(n³) time and O(1) extra space, but repeats the same comparisons among many closely related triples.

## The insight

Sort descending and examine consecutive triples. For any candidate largest side a, the next two available sides are the largest possible partners. If their sum is not greater than a, no other pair below a can make a triangle with it. If they do work, their sum gives the best perimeter among triples with that largest side, and earlier largest sides have already been ruled out. Any later triple has no greater sum.

## Optimal solution, traced

```steps
Input [2, 1, 2, 4]
    descending [4, 2, 2, 1]
---
Try 4, 2, 2: 2 + 2 = 4
    invalid, and no smaller partners can rescue 4
---
Try 2, 2, 1: 2 + 1 > 2
    first valid perimeter {{5}}
```

## Code

```python
def largest_perimeter(lengths):
    ordered = sorted(lengths, reverse=True)
    for i in range(len(ordered) - 2):
        if ordered[i + 1] + ordered[i + 2] > ordered[i]:
            return ordered[i] + ordered[i + 1] + ordered[i + 2]
    return 0
```

## Complexity

Sorting takes O(n log n) time and the scan O(n). The sorted copy uses O(n) space; the original list is untouched.

## Mistakes and edge cases

- Use strict inequality; sides summing exactly to the longest are degenerate.
- Equal lengths can be used if they are separate occurrences.
- Empty, short, and impossible lists return zero.

## Variations

- Return the chosen triple rather than just its perimeter.
- Enumerate all valid triples if the goal is their count, not the maximum.

=== card | 912
time: 30 min

## The problem

Return the input integers in nondecreasing order without relying on a built-in sorting routine. Keep every occurrence, including duplicates. For `[3, -1, 3, 2]`, return `[-1, 2, 3, 3]`. The implementation returns a new list rather than changing the caller's list.

## Constraints and what they imply

The sequence can contain negative values, repeated values, already sorted data, or reverse-sorted data. Input sizes can be large enough that quadratic sorting is unsuitable. The task calls for O(n log n) time and linear auxiliary space is available. Empty and single-element lists are natural base cases.

## Brute force

Repeatedly select the minimum remaining value and append it to the result. A linear search for each of n selections costs O(n²) time; a copied collection and output use O(n) space. Insertion sort has the same worst-case time on reverse-sorted input.

## The insight

Sort two halves independently and merge their sorted runs. The smaller of the two current heads is the smallest value not yet emitted. Once one run is exhausted, its counterpart's remaining suffix is already ordered. Taking the left value on a tie preserves the relative order of equal keys. Recursion bottoms out at length zero or one, which is already sorted.

The proof is inductive: both recursive results are sorted permutations of their halves. Each merge step removes precisely one smallest remaining element, and appending the remaining suffix preserves order. Thus the merged result is a sorted permutation of the whole input, not merely a list that looks ordered.

## Optimal solution, traced

```steps
Input [3, -1, 3, 2]
    split [3, -1] and [3, 2]
---
Sort and merge each pair
    left [-1, 3], right [2, 3]
---
Choose -1, then 2, then the left 3; append the last 3
    result {{[-1, 2, 3, 3]}}
```

## Code

```python
def merge_sort(values):
    if len(values) <= 1:
        return list(values)
    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

## Complexity

At each of O(log n) levels, splitting and merging process O(n) elements, so time is O(n log n), including sorted and duplicate-heavy inputs. Peak auxiliary space is O(n) for slices, recursive results and the merge output, plus O(log n) stack frames. The returned list is included in that linear bound.

## Mistakes and edge cases

- Append both unconsumed suffixes; exactly one may be nonempty when the loop stops.
- Taking the right side on equality still sorts integers but loses stability for records.
- First-element-pivot quicksort can become quadratic on already sorted data; merge sort does not have that failure mode.
- Returning the original singleton would alias the caller's list, so the base case copies it.

## Variations

- Merge records by a chosen key while preserving the original order of ties.
- Count cross-half inversions during each merge instead of only sorting.
- Use an iterative bottom-up merge to avoid recursive calls.

=== card | 179
time: 30 min

## The problem

Arrange non-negative integers so that writing their decimal representations consecutively produces the largest possible decimal integer. Return that result as a string, since it can be much larger than an integer machine word. For `[3, 30, 34]`, the result is `"34330"`. Multiple zeroes should produce the canonical answer `"0"`.

## Constraints and what they imply

Inputs are non-negative integers, so their decimal forms have no signs. There is at least one element in the original task; this implementation returns `"0"` for an empty list as a useful extension. Sorting numbers numerically or sorting their strings lexicographically does not consistently determine the best concatenation.

## Brute force

Try every permutation, concatenate its decimal strings, and retain the greatest result. All candidates have the same total length, so lexical comparison works. The n! arrangements cost O(n! times D) time for D total digits, and O(D + n) working space aside from permutation generation.

## The insight

For two strings a and b, prefer a before b exactly when `a+b` is lexicographically greater than `b+a`. An adjacent swap that violates this rule improves the whole concatenation: the surrounding prefix and suffix are unchanged, and the compared middle strings have equal length.

This comparator is consistent, not merely a local heuristic. Let A and B be the integer values of the strings and let p and q be their lengths. Comparing `a+b` with `b+a` is equivalent to comparing `A/(10**p - 1)` with `B/(10**q - 1)`, the values represented by repeating each string indefinitely. These rational values have a transitive order. Sorting by it leaves no improving adjacent swap; equivalently, any permutation can be transformed into the sorted order without decreasing its concatenation.

## Optimal solution, traced

```steps
Input [3, 30, 34]
    strings "3", "30", "34"
---
"34" before "3": "343" > "334"
    "3" before "30": "330" > "303"
---
Join ["34", "3", "30"]
    result {{"34330"}}
```

## Code

```python
from functools import cmp_to_key

def largest_number(values):
    parts = [str(value) for value in values]

    def compare(a, b):
        ab, ba = a + b, b + a
        return (ba > ab) - (ba < ab)

    parts.sort(key=cmp_to_key(compare))
    if not parts or parts[0] == "0":
        return "0"
    return "".join(parts)
```

## Complexity

For n numbers with at most L digits each, sorting uses O(n log n) comparisons, each taking O(L) time and temporary space. Conversion and joining take O(nL), so total time is O(n log(n+1) L), with O(nL + n) space for strings, sort keys, and output.

## Mistakes and edge cases

- Numeric descending order fails for `3` and `30`; ordinary string order also fails on other prefixes.
- The comparator must return zero when the two concatenations match, as with `12` and `1212`.
- Without zero normalization, `[0, 0]` would produce `"00"`.
- Negative numbers are outside the contract: a minus sign makes this concatenation order invalid.

## Variations

- Reverse the comparator to produce the smallest concatenation, specifying how leading zeroes should be represented.
- Keep original indices with the strings if the chosen arrangement must also be returned.

=== card | 451
time: 25 min

## The problem

Rearrange a string so that characters with higher frequencies come before characters with lower frequencies. All occurrences of each character form one group. Any ordering among equally frequent characters is acceptable. For `"tree"`, both `"eert"` and `"eetr"` are valid because `e` occurs twice and the other characters once.

## Constraints and what they imply

Characters are individual Python string elements, including digits, punctuation, and Unicode code points; case is significant. The output must be a permutation of the input and retain its length. A frequency is an integer from 1 through n, so it can index a bucket array of size n+1. The empty string should return empty.

## Brute force

Count characters, then repeatedly scan the distinct characters for the highest remaining count, output its group and remove it. With d distinct characters this costs O(n + d²) time and O(n + d) space. Comparing and sorting the distinct counts is also valid, but takes O(d log d) time.

## The insight

Count once, put each distinct character in the bucket indexed by its frequency, and visit buckets from n down to 1. When visiting bucket f, emit each of its characters f times. Every character is placed in exactly one bucket and is emitted with its original multiplicity. Since a higher bucket is processed first, no less frequent group precedes a more frequent group.

Ties need no secondary comparison: their groups have equal frequency, so their order cannot violate the condition. In this implementation insertion order in the frequency map makes the choice deterministic for a given input, but callers should not depend on a particular tie order.

## Optimal solution, traced

```steps
Input "tree"
    counts t:1, r:1, e:2
---
Bucket 2 contains e; bucket 1 contains t and r
    emit "ee", then the two singleton groups
---
One valid result is {{"eetr"}}
```

## Code

```python
from collections import Counter

def frequency_sort_characters(text):
    counts = Counter(text)
    buckets = [[] for _ in range(len(text) + 1)]
    for char, frequency in counts.items():
        buckets[frequency].append(char)
    groups = []
    for frequency in range(len(text), 0, -1):
        for char in buckets[frequency]:
            groups.append(char * frequency)
    return "".join(groups)
```

## Complexity

Counting, allocating and scanning buckets, placing distinct characters and writing the result all take O(n) expected time. The buckets, groups and output occupy O(n) space. Dictionary operations have their usual expected-time assumption.

## Mistakes and edge cases

- Emitting a character only once loses occurrences; repeat it by its bucket index.
- Buckets go from high to low, not low to high.
- Tied frequencies can appear in either order; tests should check the property, not one particular string.
- Case-distinct characters are distinct; grapheme clusters containing multiple code points are not treated as single characters.

## Variations

- Sort distinct characters by count if the number of distinct characters is much smaller than the string.
- Break ties lexicographically by ordering the characters within each frequency bucket.

=== card | 274
time: 25 min

## The problem

Given the citation count of each paper, find the largest integer h such that at least h papers each have at least h citations. For `[3, 0, 6, 1, 5]`, the answer is 3: three papers have at least three citations, but fewer than four have at least four.

## Constraints and what they imply

Citation counts are non-negative integers and the order of papers is irrelevant. If there are n papers, h cannot exceed n, regardless of how large any citation count is. Therefore counts larger than n can be grouped together without changing any candidate's answer. The empty collection has h-index zero.

## Brute force

For each candidate h from 0 to n, scan all papers and count those with at least h citations, retaining the largest feasible candidate. This takes O(n²) time and O(1) auxiliary space. Sorting the counts and scanning is another solution with O(n log n) time.

## The insight

Build n+1 buckets, placing each paper in `min(citations, n)`. Sweep candidate h downward from n, accumulating all buckets at or above h. That running total is exactly the number of papers with at least h citations: clamping cannot change whether a count reaches any h <= n.

The first candidate for which the cumulative count reaches h is feasible. Every larger candidate has already failed, so this first success is the largest possible h. Candidate zero always succeeds, even when there are no papers.

For example, one paper with a thousand citations still contributes only one paper to the cumulative count. The algorithm is counting papers that cross a threshold, not summing citations or finding an average. Many papers with zero citations never help a positive candidate, although they remain included in the total number of papers.

## Optimal solution, traced

```steps
Input [3, 0, 6, 1, 5], n = 5
    capped buckets: 0:1, 1:1, 3:1, 5:2
---
h=5: 2 papers, then h=4: 2 papers
    neither reaches its candidate
---
h=3: cumulative count 3
    first feasible candidate is {{3}}
```

## Code

```python
def h_index(citations):
    n = len(citations)
    buckets = [0] * (n + 1)
    for count in citations:
        buckets[min(count, n)] += 1
    at_least = 0
    for h in range(n, -1, -1):
        at_least += buckets[h]
        if at_least >= h:
            return h
```

## Complexity

Filling and sweeping the buckets take O(n) time and O(n) auxiliary space. The input is not modified; very large citation counts do not enlarge the bucket array.

## Mistakes and edge cases

- Accumulate buckets before checking h, so papers with exactly h citations count.
- A paper with more than n citations still contributes to every relevant candidate.
- Zero papers and all-zero citations return zero; negative counts are not part of the contract.
- Return the first successful candidate while sweeping downward, not the number of papers seen.

## Variations

- If counts are already sorted, find the boundary with binary search instead.
- For repeatedly updated citation counts, maintain cumulative frequencies in an indexed tree.

=== card | 1985
time: 30 min

## The problem

Find the kth largest entry among non-negative integers written as decimal strings. Duplicates occupy separate ranks. For `["3", "21", "100", "21"]` and k=2, return `"21"`. Return the original string, not an integer conversion or a distinct-value rank.

## Constraints and what they imply

There are n >= 1 strings and `1 <= k <= n`. Each is a canonical decimal representation: `"0"` or digits without leading zeroes. Strings can contain far more digits than a fixed-width integer, so comparison should not depend on machine integer size. Under this representation, longer strings represent larger numbers, and equal-length strings compare numerically in lexicographic order.

## Brute force

Compare every pair to count how many entries are greater than each candidate, then locate the kth rank with appropriate handling of duplicates. This takes O(n² L) time for maximum length L. Alternatively sort the whole collection in O(n log n) comparisons, which is simple but retains more ordered information than a single rank needs.

## The insight

Maintain a min-heap of at most k tuples `(length, string)`. The tuple is a numeric ordering key under the no-leading-zero contract. If a new key is greater than the heap's minimum, replace that minimum; otherwise discard it. Before the heap is full, insert everything.

By induction the heap holds the largest min(k, processed) entries, including duplicate occurrences. When a full heap sees a larger key, its old minimum is the only retained candidate displaced; a smaller or equal key cannot change the kth value. After all entries, the root's string is the kth largest.

## Optimal solution, traced

```steps
Strings ["3", "21", "100", "21"], k=2
    keep keys (1, "3") and (2, "21")
---
See (3, "100"): replace (1, "3")
    heap contains "21" and "100"
---
See another "21": it ties the boundary
    root gives {{"21"}}
```

## Code

```python
import heapq

def kth_largest_string(numbers, k):
    if not 1 <= k <= len(numbers):
        raise ValueError("k must be between 1 and the number of entries")
    heap = []
    for number in numbers:
        key = (len(number), number)
        if len(heap) < k:
            heapq.heappush(heap, key)
        elif key > heap[0]:
            heapq.heapreplace(heap, key)
    return heap[0][1]
```

## Complexity

There are O(n log(k+1)) heap comparisons in the worst case, each taking O(L) for equal-length strings, for O(n L log(k+1)) time. The heap stores O(k) tuple references; excluding the input strings, auxiliary space is O(k). No numeric conversion or input mutation is needed.

## Mistakes and edge cases

- Lexicographic ordering alone puts `"9"` above `"10"`; compare length first.
- Removing duplicates changes the requested rank.
- Leading zeroes invalidate the length argument and would need normalization first.
- Reject k=0 or k>n instead of returning an unrelated root.

## Variations

- Sort all strings by `(len(s), s)` when simplicity is more important than top-k storage.
- Use randomized quickselect on these keys for expected O(n) comparisons, with a quadratic worst case.

=== card | 164
time: 35 min

## The problem

Find the largest difference between adjacent values in the sorted order of an integer list, without actually comparison-sorting it. Return zero for fewer than two values. For `[3, 6, 9, 1]`, sorting would give `[1, 3, 6, 9]`, so the maximum adjacent gap is 3.

## Constraints and what they imply

The original task asks for linear time and space and uses non-negative integers; this implementation also supports negative integers. Duplicates are allowed. If all values are equal, the answer is zero. Otherwise the integer range from minimum to maximum and the number of gaps give a lower bound on the maximum gap.

## Brute force

Sort a copy and scan adjacent differences. This is straightforward and takes O(n log n) time and O(n) space for the copy, but misses the requested linear bound. Comparing every pair is even slower and does not directly tell which values are adjacent.

## The insight

Let `span = max - min` and `w = ceil(span / (n - 1))`. The n-1 adjacent gaps sum to span, so at least one gap is at least w. Put each value into bucket `(value - min) // w`. Distinct integers within one bucket differ by at most w-1, so a maximum gap cannot lie inside a bucket. It must connect the maximum of one nonempty bucket to the minimum of the next nonempty bucket.

Only the minimum and maximum of each bucket are needed. Sweeping nonempty buckets in increasing order compares exactly those cross-bucket neighbors. There are at most n buckets because `w >= span/(n-1)`, so the bucket holding the maximum has index at most n-1. Duplicate values do not change this argument; when span is zero we return before dividing.

## Optimal solution, traced

```steps
Input [3, 6, 9, 1]: n=4, min=1, max=9
    span=8, width=ceil(8/3)=3
---
Nonempty buckets: [1,3], [6], [9]
    record only minimum and maximum of each
---
Cross gaps 6-3=3 and 9-6=3
    maximum is {{3}}
```

## Code

```python
def maximum_gap(values):
    n = len(values)
    if n < 2:
        return 0
    low, high = min(values), max(values)
    if low == high:
        return 0
    width = (high - low + n - 2) // (n - 1)
    size = (high - low) // width + 1
    mins = [None] * size
    maxs = [None] * size
    for value in values:
        index = (value - low) // width
        if mins[index] is None:
            mins[index] = maxs[index] = value
        else:
            mins[index] = min(mins[index], value)
            maxs[index] = max(maxs[index], value)
    best = 0
    previous_max = None
    for bucket_min, bucket_max in zip(mins, maxs):
        if bucket_min is None:
            continue
        if previous_max is not None:
            best = max(best, bucket_min - previous_max)
        previous_max = bucket_max
    return best
```

## Complexity

Finding extrema, distributing values and scanning at most n buckets take O(n) time and O(n) auxiliary space under constant-time integer arithmetic. The input is unchanged. For arbitrary-precision integers, arithmetic also depends on the number of digits.

## Mistakes and edge cases

- Floor division without rounding up can create too many buckets or fail the within-bucket gap proof.
- Use `None`, not zero, to mark empty buckets: zero and negative values are legitimate.
- Skip empty buckets, comparing the nearest nonempty neighbors.
- Handle all-equal input before computing the bucket index, avoiding division by zero.

## Variations

- Return the two values on either side of the largest gap as well as its size.
- For floating-point inputs, define precision and bucket boundaries carefully before adapting the proof.

=== card | 493
time: 45 min

## The problem

Count index pairs `(i, j)` with `i < j` for which the value at i is strictly greater than twice the value at j. For `[1, 3, 2, 3, 1]`, the answer is 2: the two occurrences of 3 before the final 1 each form a qualifying pair with it. Return a count, not the pairs themselves, and do not reorder the caller's input.

## Constraints and what they imply

Inputs can contain negative numbers, zero, duplicates and large-magnitude integers; the original task allows tens of thousands of entries. A quadratic pair scan is too slow at that scale. The inequality is strict, and the order of indices matters even though the values will be sorted internally. Python integers avoid overflow in both doubling and the count; fixed-width implementations must widen before multiplying.

For negative values, a value can form a qualifying pair with an equal value: for example `-1 > 2 * -1`. Consequently, shortcuts that assume a reverse pair is always an ordinary inversion are incorrect. Empty and singleton inputs have no pairs.

## Brute force

Use two nested loops over i and j, with j starting at i+1, and increment the answer whenever the inequality holds. This directly reflects the definition and costs O(n²) time with O(1) auxiliary space. It is an excellent oracle for small inputs but performs roughly n(n-1)/2 checks on large arrays.

## The insight

Recursively split the original index range. Every pair belongs to exactly one of three categories: both indices in the left half, both in the right half, or one in each half. Recursive calls count the first two categories while returning sorted copies of the corresponding values. The third category can be counted before merging because every original left index precedes every original right index.

For each left value in ascending order, advance a right pointer while `left_value > 2 * right[pointer]`. The qualifying right values form a prefix because doubling preserves order. As left values increase, the pointer never needs to move backward, so its position is the number of qualifying right values for that left value. Summing those positions counts every cross pair exactly once in linear time. Then merge the sorted halves in the ordinary way for the caller's next level.

Counting and merging must be separate passes: the comparison used for sorted merging is `left <= right`, not `left > 2 * right`. The former alone cannot decide the latter, especially for negative values. Induction over the recursion tree proves completeness: the three categories partition all pairs, and the cross sweep counts exactly the third.

## Optimal solution, traced

```steps
Input [1, 3, 2, 3, 1]
    split into original index halves [1, 3] and [2, 3, 1]
---
Recursive results: left [1, 3] with 0 pairs
    right [1, 2, 3] with 1 pair from its own 3 before 1
---
Cross count: left 1 qualifies with none; left 3 qualifies with right 1
    add 1 cross pair; merge to [1, 1, 2, 3, 3]
---
Total 0 + 1 + 1 = {{2}}
```

The sorted values in the trace represent original subranges, not a license to forget index order. Sorting a half is safe only after pairs entirely inside it have already been counted. A cross pair has the correct original index order regardless of the positions in the sorted copies.

## Code

```python
def reverse_pairs(values):
    def solve(part):
        if len(part) <= 1:
            return list(part), 0
        mid = len(part) // 2
        left, left_count = solve(part[:mid])
        right, right_count = solve(part[mid:])
        count = left_count + right_count
        j = 0
        for value in left:
            while j < len(right) and value > 2 * right[j]:
                j += 1
            count += j
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count

    return solve(values)[1]
```

## Complexity

At each recursion level, cross counting, slicing, and merging process O(n) values. With O(log n) levels, time is O(n log n). Peak live slices and merged lists use O(n) auxiliary space, plus O(log n) recursion frames. This is a peak-space claim, not a claim that no intermediate lists are allocated.

## Mistakes and edge cases

- Use `>` rather than `>=`; equality with twice the right value is not a qualifying pair.
- Do not reset the right pointer for every left value, which would make the cross pass quadratic.
- Do not test only ordinary inversions: negative numbers can reverse the intuition about doubling.
- In fixed-width languages, widen before multiplying by two and store the pair count in a sufficiently wide type.
- Sorting the entire array before counting destroys the original index-order condition.

## Variations

- Count ordinary inversions by counting left-side suffixes during the merge.
- Replace the factor 2 by a positive constant and keep the monotone sweep; a negative factor requires a different ordering argument.
- Use coordinate compression and a Fenwick tree to count earlier values above each threshold while scanning the original array.

=== card | 324
time: 35 min

## The problem

Rearrange the given numbers in place into the strict pattern `a[0] < a[1] > a[2] < a[3] > ...`. The result must preserve all occurrences. For `[1, 5, 1, 1, 6, 4]`, one valid result is `[1, 6, 1, 5, 1, 4]`. The original task guarantees that some valid arrangement exists.

## Constraints and what they imply

Equal values are allowed, but equality is forbidden between adjacent positions. A single element is already valid. We assume a feasible input rather than detecting impossibility; for example, no algorithm can make `[1, 1]` strict. The task permits a sorted-copy construction; a more involved expected-linear selection and virtual-index partition is an alternative.

## Brute force

Enumerate permutations until one satisfies every neighboring inequality. In the worst case this examines O(n!) permutations, each requiring O(n) checks; storing a candidate uses O(n) space. Duplicates make many permutations equivalent but do not eliminate the factorial worst case.

## The insight

Sort the values, split them into a lower half of ceil(n/2) values and an upper half of floor(n/2), then fill even positions from the lower half in reverse and odd positions from the upper half in reverse. Peaks come from the upper half; valleys come from the lower half. Reversing both halves spreads equal boundary values apart instead of lining them up in adjacent positions.

Why strict? Write the sorted values as `s[0..n-1]`, and let `m=ceil(n/2)`. For peak number j the constructed value is `s[n-1-j]`; its left valley is `s[m-1-j]`, and, if present, its right valley is `s[m-2-j]`. If the left comparison failed, the sorted interval between those indices would consist of one repeated value. For even n=2k, that gives k+1 equal copies, more than the k nonadjacent positions available. For odd n=2k+1, it gives k+1 copies; these would have to occupy all even positions, leaving only larger values at the intervening peaks. But the equal interval starts at index k-j, which is positive for every peak, so at least one other sorted value is no larger than those copies. That contradicts feasibility. The right valley is no larger than the left valley, making its comparison strict too.

## Optimal solution, traced

```steps
Input [1, 5, 1, 1, 6, 4]
    sorted [1, 1, 1, 4, 5, 6]; split [1, 1, 1] | [4, 5, 6]
---
Reverse each half for placement
    valleys [1, 1, 1], peaks [6, 5, 4]
---
Interleave valley then peak
    result {{[1, 6, 1, 5, 1, 4]}}
```

## Code

```python
def wiggle_sort(values):
    ordered = sorted(values)
    middle = (len(values) + 1) // 2
    values[::2] = ordered[:middle][::-1]
    values[1::2] = ordered[middle:][::-1]
```

## Complexity

Sorting takes O(n log n) time; slicing and assignment take O(n). The sorted copy and slices require O(n) auxiliary space. The function modifies the supplied list and returns `None`.

## Mistakes and edge cases

- Alternating the two halves in forward order can place equal boundary values next to each other.
- A non-strict `<=` check does not satisfy the requested wiggle.
- Use ceil(n/2) lower-half entries because even positions are more numerous when n is odd.
- Without the feasibility promise, a strict arrangement may not exist; this function does not report that situation.

## Variations

- Use quickselect for a median and three-way partition through virtual indices for expected O(n) time and O(1) auxiliary partition space.
- Return a new arrangement instead of modifying the input list.

=== card | hr:ctci-merge-sort
time: 35 min

## The problem

Count the adjacent swaps performed by insertion sort on a list of integers. Insertion sort moves an element left while it is strictly smaller than its predecessor. For `[2, 1, 3, 1]`, the count is 3. Compute each test case independently; the function below returns one case's count and leaves its input unchanged.

## Constraints and what they imply

Lists can contain duplicates, negative integers, and up to many thousands of elements. Equal values are not swapped by the stated stable insertion procedure. The answer can be as large as n(n-1)/2, exceeding a 32-bit signed integer; Python integers grow as needed. Empty and single-element inputs have zero swaps.

## Brute force

Simulate insertion sort and increment a counter on every adjacent swap. It is O(n²) in the worst case and O(n) space if a copy is used. Alternatively directly test every pair of indices. Both are useful small-input checks but too slow for large reverse-ordered cases.

## The insight

The answer equals the number of inversions: pairs `i < j` whose left value is strictly greater than the right value. Swapping adjacent out-of-order values removes exactly their mutual inversion and does not change their order relative to any third element. The sorted final list has no inversions, so insertion sort performs exactly one swap per initial inversion.

Count those pairs using merge sort. Recursively count inversions within each original half, then merge the sorted halves. If the next right value is smaller than the next left value, it is also smaller than every remaining left value. Add the entire remaining left suffix length. If the values tie, take the left first so equal values do not count as inversions. Every cross pair is counted exactly when its right value is emitted, and every pair belongs to exactly one recursive split.

## Optimal solution, traced

```steps
Input [2, 1, 3, 1]
    left [2, 1] has 1 inversion; right [3, 1] has 1
---
Sorted halves [1, 2] and [1, 3]
    take left 1 on the tie; then right 1 is smaller than left 2
---
Add 1 cross inversion, then finish the merge
    total 1 + 1 + 1 = {{3}}
```

## Code

```python
def insertion_swap_count(values):
    def solve(part):
        if len(part) <= 1:
            return list(part), 0
        mid = len(part) // 2
        left, left_count = solve(part[:mid])
        right, right_count = solve(part[mid:])
        count = left_count + right_count
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                count += len(left) - i
                merged.append(right[j])
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, count

    return solve(values)[1]
```

## Complexity

The merge and slicing work per level is O(n), and there are O(log n) levels, yielding O(n log n) time. Peak auxiliary storage for live slices and merged lists is O(n), with O(log n) recursion frames. Python's integer count does not overflow.

## Mistakes and edge cases

- Counting equal values as inversions overcounts swaps; choose the left value on ties.
- Adding only one when taking a smaller right value misses the rest of the left suffix.
- Sorting before counting loses original index order.
- Reset state for each test case; the displayed function keeps the counter local to each call.

## Variations

- Count inversions online with coordinate compression and a Fenwick tree.
- Return both the sorted list and the count when downstream work needs the sorted values.
