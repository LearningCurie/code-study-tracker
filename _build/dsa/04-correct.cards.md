=== card | 27
time: 15 min

## The problem

Given a mutable integer list and a target value, remove all occurrences of the target in place. Return the number of retained elements. Only the prefix of that length matters after the call; its order may be arbitrary, and anything beyond it is irrelevant. For `[3, 1, 3, 2]` with target 3, the returned length is 2 and a valid prefix is `[1, 2]`.

## Constraints and what they imply

The practice list has at most 100 elements and may be empty. It is not necessarily sorted, and any number of copies of the target may occur. The output must reside in the original list, so constructing a filtered replacement without writing it back is not enough.

## Brute force

Collect all non-target elements in a separate list and copy them into the original prefix. This is O(n) time and O(n) extra space. Alternatively, deleting matches one by one can shift the remaining suffix repeatedly, making the worst case O(n^2).

## The insight

Read each position once and write each retained value to the next free prefix slot. Before reading index `read`, the prefix `nums[:write]` consists exactly of the non-target values in the original processed prefix, in their original order. Since `write <= read`, a write never destroys an unread value. Skipping a target or appending a non-target preserves the invariant, and the final write count is the required length.

## Optimal solution, traced

```steps
Input [3, 1, 3, 2], target 3; write = 0
---
Skip 3; copy 1 to index 0 and advance write to 1
---
Skip the next 3; copy 2 to index 1 and advance write to 2
---
Return {{2}}; the meaningful prefix is [1, 2]
```

## Code

```python
def remove_element(nums, target):
    write = 0
    for read in range(len(nums)):
        if nums[read] != target:
            nums[write] = nums[read]
            write += 1
    return write
```

## Complexity

One scan takes O(n) time and O(1) auxiliary space. This stable implementation preserves the relative order of retained elements even though the problem does not require that property.

## Mistakes and edge cases

- Check only the returned prefix, not the unspecified suffix.
- An all-target input returns zero; an empty input also returns zero.
- Advance the write pointer only when keeping an item.
- Reassigning `nums` locally does not modify the caller's list.

## Variations

- Allow unstable order and swap unwanted elements with the unprocessed end.
- Remove values satisfying a predicate instead of equality with one target.

=== card | 26
time: 15 min

## The problem

Compress a sorted integer list in place so its leading portion contains each distinct value once, in sorted order. Return the length of that prefix. For `[1, 1, 2, 2, 4]`, the returned length is 3 and the prefix is `[1, 2, 4]`. The remaining positions are not part of the answer.

## Constraints and what they imply

The practice input contains between 1 and 30,000 integers in nondecreasing order. Equal values are therefore contiguous, so detecting the next distinct value needs only the last retained value. The function also supports an empty list even though the original minimum length is one.

## Brute force

Build a separate list by checking whether each value has already appeared in that list, then copy it into the original prefix. Linear membership checks may take O(n^2) time and the list uses O(n) space. A set makes membership faster but still requires extra storage and does not by itself establish sorted order.

## The insight

At the start of each iteration, the prefix before `write` contains exactly the distinct values from the original processed part, in order. With sorted input, a new value either equals the last kept value or is greater than it; no earlier distinct value can reappear later. Copy a new value to `write` and advance it. The write index never exceeds the read index, so the scan does not corrupt unread data. At termination the invariant gives the required prefix and count.

## Optimal solution, traced

```steps
Input [1, 1, 2, 2, 4]; write = 0
---
Keep first 1; skip the second 1
---
Keep first 2, skip the second 2, then keep 4
---
Return {{3}} and keep [1, 2, 4] in the prefix
```

## Code

```python
def remove_duplicates(nums):
    write = 0
    for read in range(len(nums)):
        if write == 0 or nums[read] != nums[write - 1]:
            nums[write] = nums[read]
            write += 1
    return write
```

## Complexity

Each input position is read once, giving O(n) time and O(1) auxiliary space. The caller's list retains its original allocated length; the returned count identifies its meaningful prefix.

## Mistakes and edge cases

- Compare against `nums[write - 1]`, the last kept value.
- Do not inspect that position before any value has been kept.
- This algorithm requires sorted input; separated duplicates on unsorted input are not removed.
- All equal values produce a length of one, not the original length.

## Variations

- Permit at most two copies of each value in the output prefix.
- Return the counts of each distinct value instead of modifying the list.

=== card | 58
time: 15 min

## The problem

Given a string of words separated by ordinary spaces, return the length of its last word. Leading, repeated and trailing spaces may occur. For `"  red blue  "`, the answer is 4. A word is a maximal run of non-space characters.

## Constraints and what they imply

The practice input has length at most 10,000, contains English letters and spaces, and has at least one word. The function below additionally returns zero for an empty or all-space string. It treats only the ordinary space character as a separator, matching the stated input domain.

## Brute force

Split the string on spaces, discard empty pieces and return the length of the last remaining piece. This takes O(n) time and O(n) extra space for the pieces. If the extended empty-input contract is desired, first check whether any pieces exist.

## The insight

Nothing after the last word affects its length. Scan backwards, first discarding trailing spaces, then counting consecutive non-space characters. When the second scan stops, either the beginning of the string has been reached or the previous character is a separator. Thus exactly the last maximal word has been counted. The index decreases in both loops, ensuring termination.

## Optimal solution, traced

```steps
Input "  red blue  ": begin at the final space
---
Skip both trailing spaces; the index now points at e
---
Count e, u, l, b moving left; stop at the space
---
Return {{4}}
```

## Code

```python
def last_word_length(s):
    i = len(s) - 1
    while i >= 0 and s[i] == " ":
        i -= 1
    length = 0
    while i >= 0 and s[i] != " ":
        length += 1
        i -= 1
    return length
```

## Complexity

At most n characters are inspected, so worst-case time is O(n), with O(1) auxiliary space. If the last word and trailing spaces are short, the scan need not visit the earlier part of the string.

## Mistakes and edge cases

- Skip trailing spaces before counting, or the result may incorrectly be zero.
- Test `i >= 0` before indexing: Python accepts negative indices.
- A one-character word and a word reaching index zero need no special branch.
- General Unicode whitespace is a different contract from a literal space.

## Variations

- Return the last word itself, using the two discovered boundaries.
- Treat all Unicode whitespace as separators using a clearly specified predicate.

=== card | 66
time: 15 min

## The problem

An array stores a nonnegative integer as decimal digits in most-significant-first order. Add one and return the resulting digit list. For `[1, 2, 9]`, the result is `[1, 3, 0]`; for `[9, 9]`, it is `[1, 0, 0]`. This implementation may mutate the input list.

## Constraints and what they imply

The practice input contains 1 to 100 digits, each from 0 to 9, with no leading zero except for the single digit zero. A carry may propagate through every digit, requiring one additional leading digit. The nonempty valid-digit precondition is assumed rather than checked.

## Brute force

Convert the full digit sequence to an integer, add one, and convert the result back to decimal digits. This is straightforward for small inputs but uses O(n) extra space for conversion and may exceed integer limits in fixed-width languages. It is an independent small-input oracle for the digit algorithm.

## The insight

Adding one starts with carry one at the least significant digit. A nine plus that carry becomes zero and still carries one; a digit below nine absorbs the carry and increases by one. Scan from right to left, maintaining that all already visited positions contain the correct final zeros and the carry still needs to be added to the unvisited prefix. If the scan runs past the front, every digit was nine, so prepend a one.

## Optimal solution, traced

```steps
Input [1, 2, 9]; start at the last digit with carry 1
---
9 becomes 0, and the carry continues
---
2 absorbs the carry and becomes 3
---
Return {{[1, 3, 0]}}
```

## Code

```python
def plus_one(digits):
    for i in range(len(digits) - 1, -1, -1):
        if digits[i] < 9:
            digits[i] += 1
            return digits
        digits[i] = 0
    return [1] + digits
```

## Complexity

At most n digits are visited: O(n) time. Auxiliary space is O(1) when a digit absorbs the carry; the all-nine case creates an O(n) result list. That case also leaves the original list mutated to zeros, so callers should use the returned list.

## Mistakes and edge cases

- Continue the carry after changing a nine to zero.
- Stop immediately after incrementing a smaller digit.
- All nines require a new leading one; `[0]` becomes `[1]`.
- Returning only the original object cannot express the extra digit without resizing it.

## Variations

- Add an arbitrary single decimal digit, tracking its carry.
- Generalize to a base b with digits from 0 to b - 1.

=== card | 1299
time: 15 min

## The problem

Replace each entry of a mutable integer list with the maximum of the entries originally to its right. Replace the final entry with -1. Return the modified list. For `[4, 8, 2, 5]`, the output is `[8, 5, 5, -1]`.

## Constraints and what they imply

The practice list has 1 to 10,000 positive integers, each at most 100,000. Positivity matters: -1 is smaller than every real element and can represent the empty suffix at the last position. The function also accepts an empty list and returns it unchanged.

## Brute force

For each position, scan the original suffix to its right for a maximum, using -1 for the empty suffix. Preserve a copy or create a separate output so earlier mutations cannot affect later scans. The nested scans take O(n^2) time and the separate storage takes O(n) space.

## The insight

Moving right to left, maintain the maximum of the original elements strictly to the right of the current position. This is initially the empty-suffix sentinel -1. Save the current original value before overwriting it with the suffix maximum, then incorporate that saved value into the maximum for the next position. The invariant is true before the first iteration, maintained by the update, and supplies the required answer at every write.

## Optimal solution, traced

```steps
Input [4, 8, 2, 5]; best = -1
---
Write -1 at the last index, then update best to 5
---
Write 5 over 2, then 5 over 8; update best to 8
---
Write 8 over 4: result {{[8, 5, 5, -1]}}
```

## Code

```python
def replace_with_right_max(nums):
    best = -1
    for i in range(len(nums) - 1, -1, -1):
        old = nums[i]
        nums[i] = best
        best = max(best, old)
    return nums
```

## Complexity

One backwards pass uses O(n) time and O(1) auxiliary space. No suffix arrays are required. If the input can contain values below -1, the sentinel needs separate treatment instead of participating in the maximum.

## Mistakes and edge cases

- Update best using the saved original value, not the replacement.
- Write before updating best; otherwise the current value wrongly participates in its own suffix.
- A single-element input becomes `[-1]`.
- The positive-input assumption is essential to using -1 in `max`.

## Variations

- Compute suffix maxima for arbitrary signed values using a separate empty-suffix state.
- Replace each value by the minimum strictly to its left.

=== card | 374
time: 15 min

## The problem

A hidden integer is in the inclusive range 1 through n. A supplied function `guess(x)` returns -1 if the hidden number is lower than x, 1 if it is higher, and 0 if x is correct. Find the hidden number while making as few calls as logarithmic search needs. For n = 10 and a hidden value of 7, a search can find it without trying every number.

## Constraints and what they imply

The practice range has `1 <= n <= 2^31 - 1`, so linear guessing is too slow. The response is consistent with one fixed hidden number, and the callback follows the sign convention above. The implementation uses a half-open interval and assumes the stated preconditions; the search may return the last remaining candidate without calling the callback on it.

## Brute force

Call `guess` on 1, 2, and so on until the response is zero. In the worst case this uses n calls and O(1) space. It is an uncomplicated oracle for small simulated ranges but not for the largest allowed n.

## The insight

Maintain a candidate interval `[lo, hi)` containing the hidden number. Initially it is `[1, n + 1)`. Query its midpoint. If the hidden number is lower, discard the midpoint and everything above it; if higher, discard the midpoint and everything below it. A correct response can be returned immediately. The interval stays nonempty and contains the target; each nonzero response strictly decreases its size. When one candidate remains, it must be the hidden number.

## Optimal solution, traced

```steps
n = 10, hidden = 7: candidates [1, 11), midpoint 6
---
Response 1 means higher; candidates become [7, 11)
---
Midpoint 9 gets response -1; candidates become [7, 9)
---
Midpoint 8 gets response -1; only 7 remains, return {{7}}
```

## Code

```python
def guess_number(n, guess):
    lo, hi = 1, n + 1
    while hi - lo > 1:
        mid = lo + (hi - lo) // 2
        response = guess(mid)
        if response == 0:
            return mid
        if response < 0:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

## Complexity

Each query removes at least about half the candidates, giving O(log n) callback calls and O(1) auxiliary space. The half-open upper endpoint n + 1 needs a sufficiently wide integer type in fixed-width languages; Python integers do not overflow.

## Mistakes and edge cases

- Check the callback's sign convention; the meaning of lower and higher must not be reversed.
- A midpoint ruled out by a nonzero response must not remain in the interval.
- For n = 1 the initial interval already contains only the answer.
- Inconsistent callback answers violate the contract and are not detected here.

## Variations

- Find the first true position of a monotone Boolean predicate.
- Use an inclusive interval and prove its endpoint updates separately.
