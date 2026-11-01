=== card | 643
time: 20 min

## The problem

Given a sequence of numbers and a length `k`, find the greatest average of any contiguous block containing exactly `k` elements. For `[2, -1, 4, 3]` and `k = 2`, the best block is `[4, 3]`, with average 3.5. The block cannot skip an element.

## Constraints and what they imply

Assume `1 <= k <= len(nums)`, as in the task. Values can be negative, so a best sum must not be initialized to zero. Every candidate has the same positive denominator; comparing sums is equivalent to comparing averages.

## Brute force

For each starting index, sum the next `k` entries and compare the resulting averages. There are `n-k+1` candidates, giving O((n-k+1)k) time and O(1) extra space. The work overlaps heavily because adjacent blocks share `k-1` entries.

## The insight

Build the first sum once. To advance the block, subtract its outgoing element and add its incoming element. After the update, the maintained sum is exactly the sum of the new block. Induction over the starting index shows that all candidates are compared, and the maximum sum divided by `k` is the maximum average.

## Optimal solution, traced

```steps
First block [2, -1] has sum 1
    best = 1
---
Move right: remove 2, add 4
    sum = 3; best = 3
---
Move right: remove -1, add 3
    sum = 7; answer = 7 / 2 = {{3.5}}
```

The sum is updated before comparison, so the final block is included. Only the running and best sums need to survive a step.

## Code

```python
def max_average(nums, k):
    window = sum(nums[:k])
    best = window
    for right in range(k, len(nums)):
        window += nums[right] - nums[right - k]
        best = max(best, window)
    return best / k
```

## Complexity

Time is O(n), including the initial sum; `nums[:k]` creates an O(k) temporary slice, which is the auxiliary space bound. A loop accumulating the first `k` elements would reduce extra space to O(1).

## Mistakes and edge cases

- Initializing the best to zero fails for all-negative input.
- When `k` equals the sequence length, the first block is the only candidate.
- Remove index `right-k`, not `right-k+1`.

## Variations

- Return the starting index, retaining the earliest index when sums tie.
- Compute all fixed-width sums to feed a stream of moving averages.
- If lengths may differ, comparing sums is no longer sufficient to compare averages.

=== card | 209
time: 30 min

## The problem

Find the minimum length of a contiguous block of positive integers whose sum is at least a positive target. Return zero if no block qualifies. For target 7 and `[2, 3, 1, 2, 4, 3]`, the block `[4, 3]` gives length 2.

## Constraints and what they imply

The target and all entries are strictly positive. A longer block cannot have a smaller sum, and removing an entry strictly decreases the sum. This monotonicity is the reason a one-way left pointer is safe. With negative entries the same argument breaks; for example, discarding a negative prefix can increase the sum.

## Brute force

Try each start and extend to every end, maintaining a running sum. Compare every qualifying length. There are O(n²) start/end pairs, O(n²) time and O(1) extra space. Recomputing each sum from scratch would take even longer.

## The insight

Scan rightward while maintaining the sum of the inclusive window `[left, right]`. Once it reaches the target, record the length and remove the leftmost element. Repeat until the window is too small in sum. A discarded start has already been considered at the earliest right endpoint where it qualifies; any later endpoint would only make its block longer, so it cannot improve the answer.

Conversely, an optimal block cannot be skipped: when its right end arrives, either its start is still present and shrinking examines it, or that start was discarded earlier after producing an even shorter qualifying block. Each endpoint advances at most `n` times.

## Optimal solution, traced

```steps
Target 7; add 2, 3, 1, 2
    sum = 8; record length 4; remove 2 => sum 6
---
Add 4
    sum = 10; record length 4, remove 3; record length 3, remove 1
    sum = 6, so stop shrinking
---
Add 3
    sum = 9; record length 3, remove 2; record length {{2}}, remove 4
```

The remaining sum is 3, so there is no further qualifying window ending at the last element. The best observed length is 2.

## Code

```python
def min_subarray_length(target, nums):
    left = 0
    total = 0
    best = len(nums) + 1
    for right, value in enumerate(nums):
        total += value
        while total >= target:
            best = min(best, right - left + 1)
            total -= nums[left]
            left += 1
    return 0 if best == len(nums) + 1 else best
```

## Complexity

Both pointers move only forward, so total time is O(n), despite the nested loop. The running sum, pointers and best length use O(1) extra space.

## Mistakes and edge cases

- A singleton at least the target is already optimal.
- Use a `while`, not an `if`, to test every shorter qualifying window.
- An unattainable target returns zero; empty input also returns zero.
- This implementation relies on a positive target and positive values.

## Variations

- Return a pair of boundary indices together with the length.
- For arbitrary signed integers, use prefix sums and a monotonic deque instead.
- For a fixed starting point, binary-search prefix sums when all values are positive.

=== card | 3
time: 25 min

## The problem

Given a string, return the length of its longest contiguous substring in which every character is distinct. For `abba`, the answer is 2, achieved by either `ab` or `ba`. An empty string has answer zero.

## Constraints and what they imply

Characters are compared as Python string characters; the method does not depend on a small alphabet. The desired object is contiguous, so deleting arbitrary repeated characters is not allowed. The dictionary may contain characters that no longer belong to the current window.

## Brute force

Start at each position, extend until a character repeats, and maintain a set for that start. This tries O(n²) extensions in the worst case, with O(min(n, alphabet size)) set space. Rebuilding the set for every start repeats much of the same work.

## The insight

Keep the last index of every character and a left boundary. Before processing the next character, the current window has no duplicates. If the character last appeared within the window, the only way to include the new occurrence without a repeat is to move left past the old one. If its previous occurrence is already outside, leave the boundary alone.

The updated window is the longest distinct suffix ending at this right index: every earlier start would contain both copies, while the retained suffix has no other repeats. Therefore taking the maximum over right endpoints considers an optimal answer. The boundary never moves backwards.

Keeping old positions in the dictionary is safe: the boundary test distinguishes a repeat inside the active window from one that has already been excluded. This avoids deleting entries whenever the boundary advances and keeps the implementation simple.

## Optimal solution, traced

```steps
Read a then b
    window = ab, best = 2
---
Read second b at index 2
    previous b at 1; left becomes 2; window = b
---
Read a at index 3
    previous a at 0 is outside; left stays 2
    window = ba; best = {{2}}
```

The maximum with the existing left boundary is essential: the old `a` must not pull the window back across the repeated `b`.

## Code

```python
def longest_distinct(s):
    last = {}
    left = 0
    best = 0
    for right, char in enumerate(s):
        if char in last:
            left = max(left, last[char] + 1)
        last[char] = right
        best = max(best, right - left + 1)
    return best
```

## Complexity

There are O(n) expected dictionary operations and O(min(n, alphabet size)) auxiliary space for last positions. Hash table operation costs are expected bounds.

## Mistakes and edge cases

- Setting `left` directly to an old index can move it backward on `abba`.
- Update the last position after using the prior one.
- Spaces, punctuation and repeated Unicode characters are treated like other characters.
- One character yields one; the empty input yields zero.

## Variations

- Return the substring by storing the best start and length.
- Allow at most `k` distinct characters by tracking window frequencies.
- Count all distinct-character substrings by adding the current window length.

=== card | 567
time: 30 min

## The problem

Determine whether some contiguous part of `text` is a rearrangement of all characters in `pattern`. Every pattern occurrence matters: for pattern `aab`, `baa` matches, whereas `abb` does not. Return a Boolean rather than the position.

## Constraints and what they imply

The original inputs consist of lowercase English letters, with a nonempty pattern. A matching part must have length exactly `len(pattern)`, and its 26 character frequencies must match the pattern's frequencies. If the pattern is longer than the text, no matching block exists.

## Brute force

For every block of the required length, count its characters from scratch and compare the counts to the pattern counts. This takes O(nm) time for text length `n` and pattern length `m`, and O(26) count space. Sorting every block also works, but repeatedly sorts nearly identical data.

## The insight

Use a frequency difference: pattern count minus current window count. Initially subtract the first window. Maintain `nonzero`, the number of alphabet entries with a nonzero difference. Adjusting one letter requires checking whether its entry was zero before and after the adjustment. Exactly when `nonzero` is zero, all counts agree, so the current fixed-size block is a permutation.

Each slide removes one old text character and inserts one new one. The adjustments restore the difference invariant even when the two characters are the same. Every possible starting position is visited once, so absence of a match after the scan proves the answer is false.

The signed entries may be positive or negative; neither sign alone determines a match. Their combined zero status captures both missing and excess occurrences. This avoids comparing all 26 counts after each shift, while still preserving multiplicities exactly.

## Optimal solution, traced

```steps
pattern = ab; first text block = ei
    differences: a +1, b +1, e -1, i -1; nonzero = 4
---
Slide through text eidba to block db
    differences: a +1, d -1; nonzero = 2
---
Remove d and add a for block ba
    every difference is zero; return {{True}}
```

The order of letters does not matter; their signed frequency differences do.

## Code

```python
def contains_permutation(pattern, text):
    m = len(pattern)
    if m > len(text):
        return False
    diff = [0] * 26
    for char in pattern:
        diff[ord(char) - ord("a")] += 1
    nonzero = sum(value != 0 for value in diff)

    def adjust(char, delta):
        nonlocal nonzero
        i = ord(char) - ord("a")
        nonzero -= diff[i] != 0
        diff[i] += delta
        nonzero += diff[i] != 0

    for right, char in enumerate(text):
        adjust(char, -1)
        if right >= m:
            adjust(text[right - m], 1)
        if right + 1 >= m and nonzero == 0:
            return True
    return m == 0
```

## Complexity

Initialization takes O(m + 26), the scan O(n), and the difference array O(26) space. Each window move performs at most two constant-time adjustments.

## Mistakes and edge cases

- A set loses multiplicities, so it cannot distinguish `aab` from `abb`.
- Check only after a full-size window has formed.
- The code also treats an empty pattern as matching, even though the original domain excludes it.
- The character indexing assumes lowercase English letters.

## Variations

- Collect all matching start indices instead of stopping at the first one.
- Use a dictionary of differences for a much larger alphabet.
- For a streaming input, retain the last `m` characters in a queue.

=== card | 424
time: 30 min

## The problem

Find the longest contiguous string segment that can become all one character after replacing at most `k` positions. For `AABABBA` and `k = 1`, a segment of length 4 can be made uniform. We seek the length, not the actual replacements.

## Constraints and what they imply

The original alphabet is the 26 uppercase English letters and `k` is nonnegative. For any particular window, retaining the most frequent letter minimizes changes; its required replacement count is window length minus that maximum frequency. A window is valid exactly when this count is at most `k`.

## Brute force

Enumerate every substring, count its letters, and test whether length minus the largest count is within the budget. Updating counts as each end advances gives O(26n²) time if the maximum is recomputed for each substring, and O(26) space.

## The insight

Maintain exact window counts and the largest frequency ever observed during this scan. This `peak` may become stale after removing a character, but it never decreases. If window length exceeds `peak + k`, remove from the left until it does not.

Why is a stale peak safe for the answer? When `peak` last increased to its current value, the then-current window really contained that many identical letters. The window length cannot decrease in this algorithm: adding one character increases it by one, and at most one removal is needed to restore the bound. So that earlier window was no longer than the current one. Extend the earlier window to the current length using already scanned characters: it retains those `peak` identical letters and needs at most `length - peak <= k` replacements. Thus a valid window of the reported length exists even if the current window is invalid.

Conversely, an optimal valid window cannot be missed. To move the left edge past that window's start before its right end is reached, the algorithm would have to remove that start when the current window is a subarray of the optimum. That subarray is valid, and its true maximum frequency is at most the historical peak, so the removal condition could not hold. The maintained window therefore reaches at least the optimal length. Together these bounds prove the reported maximum is exact.

## Optimal solution, traced

```steps
Read AABA with k = 1
    peak A count = 3; length 4 needs one replacement; best = 4
---
Add B: length 5, peak 3, so 5 - 3 > 1
    remove first A; left becomes 1; historical peak remains 3
---
Continue through BA
    lengths retained are at most 4; answer = {{4}}
```

The retained window need not itself always be valid under its current frequency counts; this version only promises the optimal length.

## Code

```python
def longest_replacement(s, k):
    counts = [0] * 26
    left = 0
    peak = 0
    best = 0
    for right, char in enumerate(s):
        idx = ord(char) - ord("A")
        counts[idx] += 1
        peak = max(peak, counts[idx])
        while right - left + 1 - peak > k:
            counts[ord(s[left]) - ord("A")] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
```

## Complexity

Each character enters and leaves at most once: O(n) time and O(26) auxiliary space. No scan of the alphabet is needed during shrinking.

## Mistakes and edge cases

- A stale historical maximum is suitable for the length, not automatically for returning a valid witness.
- With `k = 0`, only already uniform runs qualify.
- Replacing all occurrences of the least frequent letter is not always enough; sum all non-majority positions.
- The fixed array requires uppercase English letters.

## Variations

- Recompute the exact maximum from 26 counts to maintain a genuinely valid window and return its boundaries.
- Use a frequency dictionary for a different finite alphabet.
- Assign different replacement costs; the simple majority formula no longer applies.

=== card | 713
time: 30 min

## The problem

Count the nonempty contiguous subarrays whose product is strictly less than `k`. For `[10, 5, 2, 6]` with `k = 100`, there are 8 such subarrays. A subarray is identified by its indices even if another subarray has the same values.

## Constraints and what they imply

Entries are positive integers and `k` is an integer. Every nonempty product is at least one, so `k <= 1` has answer zero. With positive integers, extending a window cannot decrease its product, and dropping factors cannot increase it. Zeros or fractional values require a different argument.

## Brute force

For each left endpoint, multiply successively through all right endpoints and increment a counter when the product is below `k`. This inspects O(n²) subarrays and uses O(1) extra space. Breaking once the product reaches the threshold is possible under the stated positivity, but does not change the worst case.

## The insight

For each right endpoint, keep the longest suffix whose product is below `k`. Multiply in the incoming value and remove left factors until the product becomes small enough. Because every factor is at least one, any suffix beginning later is also valid, and any earlier start was already too large. Thus there are exactly `right-left+1` valid subarrays ending here.

Adding that number for each right endpoint counts every valid subarray once, by its unique end. Integer division exactly removes a factor of the maintained product. The empty window has product one, which is below `k` after the early return.

An earlier start cannot become useful at a later end: its already excessive product is multiplied by more positive integer factors. Thus permanently discarding it is safe, and the algorithm does not have to reconsider old boundaries.

## Optimal solution, traced

```steps
k = 100: add 10, then 5
    products 10 and 50; add 1 then 2 to count
---
Add 2: product 100 is not strictly below 100
    remove 10; product 10; add 2 valid suffixes
---
Add 6: product 60
    add 3 suffixes; total = 1 + 2 + 2 + 3 = {{8}}
```

When an individual factor is too large, it too is removed, leaving a zero-length contribution for that endpoint.

## Code

```python
def count_product_less_than_k(nums, k):
    if k <= 1:
        return 0
    left = 0
    product = 1
    answer = 0
    for right, value in enumerate(nums):
        product *= value
        while product >= k:
            product //= nums[left]
            left += 1
        answer += right - left + 1
    return answer
```

## Complexity

The pointers make O(n) total moves and use O(1) auxiliary variables. This is the usual arithmetic-operation bound; unbounded integer multiplication and division have costs depending on integer size.

## Mistakes and edge cases

- Strict inequality requires shrinking at equality.
- `k <= 1` must be handled before the loop.
- Ones do not increase the product but still generate many distinct subarrays.
- Do not use this proof for zero or negative values.

## Variations

- Count products at most `k` by changing the threshold comparison.
- For positive real factors below one, the monotonicity assumptions need re-evaluation.
- Return counts per right endpoint instead of their sum.

=== card | 904
time: 25 min

## The problem

Find the longest contiguous run containing at most two distinct item types. For `[1, 2, 1, 3, 3]`, `[2, 1, 3, 3]` has three types, but `[1, 3, 3]` has two, and the maximum length is 3. Identical values represent the same type.

## Constraints and what they imply

Items arrive in a fixed order; only a consecutive run is allowed. Types may repeat arbitrarily. The input values can serve as dictionary keys. The frequency map needs to represent only the current window, including deleting a type once its count falls to zero.

## Brute force

For each start, extend a frequency map through all possible ends and update the best length whenever there are at most two types. This takes O(n²) expected time and up to O(n) space if the map is allowed to hold all types. Stopping at the third distinct type reduces unnecessary work but not the worst case.

## The insight

Advance the right endpoint and increment the incoming type. While the map contains more than two keys, decrement the outgoing type and move left; remove a key when its count becomes zero. After this repair, the window is valid.

It is the longest valid suffix ending at the current right endpoint. Any start discarded during repair had at least three types when discarded; extending its end cannot remove a type. Those starts will therefore never become valid again. All later starts are suffixes of a valid window and are valid too. Comparing the window length at every end finds the optimum.

## Optimal solution, traced

```steps
Read 1, 2, 1
    counts {1: 2, 2: 1}; best = 3
---
Read 3: three types
    remove 1 then 2; counts {1: 1, 3: 1}; left = 2
---
Read another 3
    window [1, 3, 3], length {{3}}; best stays 3
```

Deleting zero counts is part of the invariant, not an optional cleanup: the dictionary's size is the number of types in the window.

## Code

```python
def longest_two_types(items):
    counts = {}
    left = 0
    best = 0
    for right, value in enumerate(items):
        counts[value] = counts.get(value, 0) + 1
        while len(counts) > 2:
            old = items[left]
            counts[old] -= 1
            if counts[old] == 0:
                del counts[old]
            left += 1
        best = max(best, right - left + 1)
    return best
```

## Complexity

Each item enters and leaves at most once, giving O(n) expected time with hash operations. At most three keys are present during repair, so auxiliary space is O(1). The empty sequence returns zero.

## Mistakes and edge cases

- Keeping zero-count keys falsely reports extra types.
- The result is a contiguous run, not the total number of two globally frequent types.
- One type throughout permits the whole input.
- Shrink repeatedly: a single removal may not eliminate a type.

## Variations

- Permit at most `k` types and use O(k) map space during repair.
- Count valid runs by adding the window length for every right endpoint.
- Store the best boundaries to return the run itself.

=== card | 1658
time: 30 min

## The problem

At each operation remove one element from either end of a positive integer array and subtract that value from `x`. Find the fewest removals that make the removed total exactly `x`, or return -1 if impossible. For `[1, 1, 4, 2, 3]` and `x = 5`, removing the last two elements costs 2 operations.

## Constraints and what they imply

The original numbers and `x` are positive. Removed values consist of a prefix and a suffix, which do not overlap; the remaining values form one contiguous middle block, possibly empty. Since values are positive, a desired middle sum below zero is impossible.

## Brute force

Choose the number of elements removed from the left and the right, with their sum at most `n`; evaluate their removed sum and minimize the number removed. Prefix and suffix running sums make each pair O(1), so there are O(n²) time and O(n) precomputation space. Testing all pairs without stored sums takes longer.

## The insight

Let `target = sum(nums) - x`. Any successful removal leaves a middle block with sum `target`, and any such middle block can be obtained by removing the complementary prefix and suffix. Minimizing removals is therefore equivalent to maximizing the retained length.

Use a window with nonnegative sum. Extend right, removing from the left while the sum exceeds `target`. Positivity ensures a discarded start cannot produce a target sum at a later end: that sum would only increase. After shrinking, a window equal to the target is the longest possible target-sum window ending there. When the target is zero, the empty window is a valid retained block, representing removal of all elements.

## Optimal solution, traced

```steps
nums = [1, 1, 4, 2, 3], x = 5
    total = 11; retained target = 6
---
Extend through the 4
    window [1, 1, 4] sums to 6; longest retained length = 3
---
The remaining windows do not beat length 3
    remove 5 - 3 = {{2}} elements
```

The complement is constructive: keep indices 0 through 2, remove indices 4 and 3 from the right.

## Code

```python
def min_end_removals(nums, x):
    target = sum(nums) - x
    if target < 0:
        return -1
    left = 0
    total = 0
    longest = 0 if target == 0 else -1
    for right, value in enumerate(nums):
        total += value
        while left <= right and total > target:
            total -= nums[left]
            left += 1
        if total == target:
            longest = max(longest, right - left + 1)
    return -1 if longest < 0 else len(nums) - longest
```

## Complexity

Computing the total and moving the two boundaries takes O(n) time. Only sums, boundaries and the best length are stored, so auxiliary space is O(1).

## Mistakes and edge cases

- If `x` equals the total, retaining an empty block gives `n`, not -1.
- If `x` exceeds the total, no removal sequence can work.
- Checking only prefixes or only suffixes misses mixed removals.
- Negative numbers invalidate this shrinking rule.

## Variations

- With signed integers, use earliest prefix-sum indices to find a longest exact-sum subarray.
- Return counts removed from each side by retaining the best boundaries.
- Ask for the maximum number removed instead; then seek the shortest retained block.

=== card | 76
time: 45 min

## The problem

Given a source string and a target string, find a shortest contiguous source substring containing every target character with at least its target multiplicity. For source `ADOBECODEBANC` and target `ABC`, one shortest answer is `BANC`. Return the empty string when no cover exists.

## Constraints and what they imply

Characters are case-sensitive, and repeated target characters require repeated copies in the answer. The source and target need not have the same length or character set. The original task uses nonempty strings; this implementation also defines an empty target to have an empty answer. If several shortest covers exist, returning any one is acceptable; the strict update below keeps the earliest discovered one.

The length of the source is `n`, and the target has `d` distinct characters. Tracking only target characters avoids allowing irrelevant source characters to affect the validity counter. Hash operations are expected constant time, not an unconditional worst-case guarantee.

## Brute force

Enumerate every start and end, count the substring's characters, and check each target requirement. Maintaining counts as the end advances takes O(n²d) time if each candidate scans the distinct requirements, with O(d) relevant-count space. A naive recount of each substring can add another factor. A valid candidate need not have the same length as the target because irrelevant characters may lie between required ones.

## The insight

Store `need[c]` for each target character, `have[c]` for its count in the current window, and `formed` for the number of distinct target characters whose count meets or exceeds the requirement. Adding a character changes `formed` only when its count rises exactly to its threshold. Removing one changes `formed` only when its count was exactly at its threshold before removal. Thus `formed == len(need)` is equivalent to coverage, even with repeated characters and surplus copies.

Grow the right boundary one character at a time. While the window covers the target, record it if it is shorter than the best and move the left boundary rightward. Once a removal makes the window invalid, the next rightward addition may restore coverage. Every removed start has already produced its shortest covering window for the current right endpoint; extending that same start later would be longer, so it cannot lead to a better answer.

For completeness, consider any optimal window. When its right endpoint is processed, if its start has already been removed, a no-longer candidate starting there or earlier was recorded at an earlier endpoint. Otherwise the shrinking loop reaches its start or records a shorter covering window first. Thus the best recorded length is optimal. The invariant also explains why removing a surplus copy does not immediately invalidate coverage.

## Optimal solution, traced

```steps
source = ADOBECODEBANC, target = ABC
    after index 5: ADOBEC covers all three; best length 6
---
Advance through index 10 and shrink the old start
    CODEBA covers ABC but has length 6; removing C makes it invalid
---
At index 12, add C and shrink past O, D, E
    BANC covers; length {{4}}; removing B breaks coverage
```

The check happens before each removal, so the last valid window is not lost. The stored start and length describe the actual source substring, not merely a count.

## Code

```python
from collections import Counter

def minimum_cover(source, target):
    if not target:
        return ""
    need = Counter(target)
    have = {char: 0 for char in need}
    formed = 0
    left = 0
    best_start = 0
    best_length = len(source) + 1
    for right, char in enumerate(source):
        if char in need:
            have[char] += 1
            if have[char] == need[char]:
                formed += 1
        while formed == len(need):
            length = right - left + 1
            if length < best_length:
                best_start, best_length = left, length
            old = source[left]
            if old in need:
                if have[old] == need[old]:
                    formed -= 1
                have[old] -= 1
            left += 1
    if best_length > len(source):
        return ""
    return source[best_start:best_start + best_length]
```

## Complexity

Building requirements takes O(m) time for target length `m`. Each source position enters once and leaves at most once, so the scan takes O(n) expected time. The maps use O(d) auxiliary space, excluding the O(answer length) returned slice. The returned empty string represents both no cover and the explicitly defined empty-target result.

## Mistakes and edge cases

- Counting distinct characters alone misses multiplicity, for example target `AAB`.
- Compare with the threshold, not merely a nonzero count.
- Removing an irrelevant character does not change `formed`.
- If a needed character never appears enough times, no best window is recorded.
- A source shorter than the target cannot cover it, but needs no special case.

## Variations

- Return boundary indices rather than materializing a substring.
- Find every minimum-length cover by collecting equal-length candidates.
- On a stream, buffer enough source characters to return a witness; a length alone needs less retained text.

=== card | 992
time: 45 min

## The problem

Count the nonempty contiguous subarrays containing exactly `k` distinct values. Distinctness concerns values, not positions: `[1, 2, 1]` has two distinct values even though it has three entries. For `[1, 2, 1, 2, 3]` with `k = 2`, the answer is 7.

## Constraints and what they imply

The original task uses positive integer values and a positive `k`, but only hashability matters to the algorithm. We count index ranges separately, including equal-valued subarrays at different positions. A single longest valid window is not enough: for a given right endpoint, several different starts may yield exactly `k` types.

The count can be quadratic in `n`, although the algorithm performs only linear window operations. Python integers hold such counts without a fixed-width overflow. For an extension of the interface, `k <= 0` returns zero because a nonempty subarray cannot contain exactly zero or fewer distinct values.

## Brute force

For every start, extend the end while recording frequencies, and add one whenever the number of keys equals `k`. This inspects O(n²) windows, with O(n) worst-case auxiliary space for the frequency dictionary. Breaking when the number of types exceeds `k` can save work, but all-equal input remains quadratic.

## The insight

First solve the easier monotone problem: count subarrays with at most `limit` distinct values. Maintain a window with a frequency map and shrink from the left until it contains at most `limit` keys. For a fixed right endpoint, every suffix starting at or after `left` is valid; each earlier start is invalid because it was discarded only after a window had too many types, and extending the end cannot remove a type. Therefore add `right-left+1` valid subarrays at this endpoint.

The sets of subarrays with at most `k-1` and at most `k` types are nested. Their difference contains precisely those with exactly `k` types. Run the helper twice and subtract the totals. A zero limit is well defined: each insertion is removed immediately, yielding zero nonempty subarrays. A negative limit is handled as zero by the helper so the shrink loop cannot try to remove from an empty window.

The two passes may discard starts at different moments; this is intentional. Their difference counts individual index ranges, not a difference of arbitrary window lengths. Every nonempty range occurs in the at-most-k count exactly once at its right endpoint and is removed by the second count exactly when it has fewer than `k` types. This establishes both no omissions and no double counting.

## Optimal solution, traced

```steps
nums = [1, 2, 1, 2, 3], k = 2
    at-most-2 window lengths by right end: 1, 2, 3, 4, 2
    their sum is 12
---
For at most 1 type, each successive value changes type
    window lengths: 1, 1, 1, 1, 1; sum is 5
---
Subtract nested counts
    exactly two types = 12 - 5 = {{7}}
```

At the last endpoint of the first pass, the window `[2, 3]` is the longest permissible suffix. Its two possible starts contribute two at-most-two subarrays, but only one has exactly two types.

## Code

```python
def exactly_k_distinct(nums, k):
    def at_most(limit):
        if limit < 0:
            return 0
        counts = {}
        left = 0
        total = 0
        for right, value in enumerate(nums):
            counts[value] = counts.get(value, 0) + 1
            while len(counts) > limit:
                old = nums[left]
                counts[old] -= 1
                if counts[old] == 0:
                    del counts[old]
                left += 1
            total += right - left + 1
        return total

    if k <= 0:
        return 0
    return at_most(k) - at_most(k - 1)
```

## Complexity

Each pass moves each boundary at most `n` times, giving O(n) expected time across both passes with hash-table operations. The maps use O(min(n, k + 1)) auxiliary space for positive `k`, including the temporarily inserted extra type. Empty input and a `k` larger than the number of types return zero.

## Mistakes and edge cases

- Exactly-k windows are not simply all suffixes of the longest exactly-k window; shorter suffixes may have fewer types.
- Delete zero-frequency entries before using the map size.
- Count only nonempty windows, especially when the limit is zero.
- For `[1, 1, 1]` and `k = 1`, the answer is 6, not 3.
- Preserve the nested-count interpretation: subtract at most `k-1`, not at most `k+1`.

## Variations

- Count at most `k` types directly with a single pass.
- Count exactly `k` odd entries using the same nested-set subtraction with an odd counter.
- Track two left boundaries in one pass to count the starts lying between them.

=== card | 1838
time: 35 min

## The problem

Given an integer array and an operation budget `k`, one operation increases one element by one. Return the largest frequency of any value achievable with at most `k` operations. For `[1, 2, 4]` and `k = 5`, raising 1 and 2 to 4 costs 3 + 2, giving frequency 3.

## Constraints and what they imply

The original array is nonempty, its values are positive, and `k` is nonnegative. Values can be increased but never decreased. Their original order does not restrict which elements are chosen, so sorting does not change the answer. The implementation uses a sorted copy and does not mutate the input.

## Brute force

For each existing value, consider all subsets of values no larger than that target; calculate the total increase required for each subset and keep the largest affordable one. This costs O(n 2^n) time in a direct implementation and O(n) space for a subset. Enumerating all subsets emphasizes why selecting the cheapest values is useful.

## The insight

An optimal target can be chosen as the largest original value among the selected elements: lowering a larger proposed target to that value never increases cost and does not reduce frequency. For a fixed target, the cheapest other elements to raise are the largest values not exceeding it. In sorted order they form a contiguous block ending at the target.

For sorted block `[left, right]`, the cost to raise everything to `a[right]` is `a[right] * length - sum(block)`. Extend right and shrink left until the cost is within budget. Adding a larger target cannot decrease the cost for an existing block, and removing its smallest value cannot increase it. Therefore any discarded start remains infeasible for later targets, and the repaired window is the largest affordable block ending here. Maximizing over endpoints finds the optimal frequency.

## Optimal solution, traced

```steps
sorted values [1, 2, 4], k = 5
    window [1, 2]: cost 2 * 2 - 3 = 1
---
Add 4
    window sum = 7; cost 4 * 3 - 7 = 5
---
The full window fits
    best frequency = {{3}}
```

For a smaller budget, remove the smallest value until the same cost formula is within budget; the maximum is updated after this repair.

## Code

```python
def max_frequency_after_increments(nums, k):
    ordered = sorted(nums)
    left = 0
    total = 0
    best = 0
    for right, value in enumerate(ordered):
        total += value
        while value * (right - left + 1) - total > k:
            total -= ordered[left]
            left += 1
        best = max(best, right - left + 1)
    return best
```

## Complexity

Sorting takes O(n log n) time and O(n) space for the copy; the scan takes O(n) time and O(1) additional variables beyond that copy. An in-place sort can avoid the explicit copy but its sorting workspace is implementation-dependent.

## Mistakes and edge cases

- The target is the rightmost value, not the mean; decreases are forbidden.
- Use a wide enough integer type for `value * length` outside Python.
- When `k = 0`, existing duplicates can still form the best answer.
- This function returns zero for an empty list as an extension.

## Variations

- Return the chosen target and original indices by sorting value-index pairs.
- If both increments and decrements are allowed, a median-based cost replaces the maximum-target cost.
- Use prefix sums and binary search to find the largest feasible length.

=== card | 395
time: 35 min

## The problem

Find the length of the longest contiguous substring in which every character that appears appears at least `k` times. For `aaabb` and `k = 3`, `aaa` qualifies and the answer is 3. Characters absent from the chosen substring have no minimum requirement.

## Constraints and what they imply

The original input uses lowercase English letters, with positive `k`. A substring can become invalid when a new character enters only once, and become valid again after more copies arrive. Consequently, simply shrinking whenever a character is underrepresented is not a sound monotone window rule. The alphabet contains at most 26 distinct letters.

## Brute force

Enumerate each start and end and maintain character counts for the candidate. At each end inspect the at most 26 counts and record the length if every positive count is at least `k`. This costs O(26n²) time and O(26) space. It is straightforward but repeatedly revisits overlapping substrings.

## The insight

Fix a number `goal` of distinct characters and sweep a window with at most `goal` types. Track both the number of nonzero counts, `distinct`, and the number of types whose count has reached `k`, `qualified`. Shrink only when `distinct > goal`, a monotone condition. When `distinct == goal == qualified`, the window itself meets the frequency condition.

Why do these passes find an optimum? Take any optimal substring with `u` types. During the pass for `goal = u`, at its right endpoint the maintained window begins no later than its left endpoint: that substring itself has at most `u` types, so shrinking cannot discard its start. The maintained window has exactly `u` types because it contains the optimum. Adding extra copies of those same types cannot make any of them fail the lower bound, so the maintained window is valid and at least as long as the optimum. Checking every `u` from 1 through 26 covers all possibilities.

## Optimal solution, traced

```steps
s = aaabb, k = 3, goal = 1
    after aaa: distinct = 1, qualified = 1; best = 3
---
Add b: distinct = 2, so remove all three a characters
    window b has one type but qualified = 0
---
Pass goal = 2 sees aaabb
    a qualifies, b does not; best remains {{3}}
```

Counts cross the threshold in both directions. On removal, decrement `qualified` before lowering a count that currently equals `k`.

## Code

```python
def longest_at_least_k(s, k):
    if k <= 1:
        return len(s)
    best = 0
    for goal in range(1, 27):
        counts = [0] * 26
        left = 0
        distinct = 0
        qualified = 0
        for right, char in enumerate(s):
            idx = ord(char) - ord("a")
            if counts[idx] == 0:
                distinct += 1
            counts[idx] += 1
            if counts[idx] == k:
                qualified += 1
            while distinct > goal:
                old = ord(s[left]) - ord("a")
                if counts[old] == k:
                    qualified -= 1
                counts[old] -= 1
                if counts[old] == 0:
                    distinct -= 1
                left += 1
            if distinct == goal and qualified == goal:
                best = max(best, right - left + 1)
    return best
```

## Complexity

There are 26 passes, each O(n), for O(26n) time and O(26) auxiliary space. For a variable alphabet of size `A`, this becomes O(An) time and O(A) space if a suitable indexed alphabet is provided.

## Mistakes and edge cases

- A letter at frequency one is not automatically a reason to discard it.
- Only characters present in the substring must reach `k`.
- `k = 1` makes the entire string valid; `k > len(s)` yields zero.
- This array implementation assumes lowercase English characters.

## Variations

- Recursively split at characters whose total frequency in a segment is below `k`.
- Return a witness by recording the best boundaries.
- For a general alphabet, enumerate its distinct characters and use a frequency dictionary.
