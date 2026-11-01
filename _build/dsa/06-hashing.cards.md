=== card | 217
time: 15 min

## The problem

Given a sequence of integers, decide whether two different positions contain the same value. Return a Boolean, not the value or positions. For example, `[4, 1, 4]` returns true while `[4, 1, 2]` returns false.

## Constraints and what they imply

The sequence can be large and values may be negative or repeated many times. Equal values need not be adjacent, and their positions matter only in establishing that there are two occurrences. The function also accepts an empty sequence.

## Brute force

Compare every pair of distinct positions. If any pair has equal values, return true; otherwise return false after all comparisons. This takes O(n²) time in the worst case and O(1) additional space. Sorting a copy and checking neighbors is another option in O(n log n) time and O(n) space.

## The insight

Keep the values in the prefix already examined in a set. Before adding the current value, ask whether it is present. If so, its earlier occurrence and current position form a valid pair; otherwise adding it preserves the prefix invariant. If the scan finishes without a hit, no second occurrence exists, because each possible second occurrence was checked.

## Optimal solution, traced

```steps
Start with an empty set
    seen = {}
---
Read 4 and 1
    seen = {4, 1}
---
Read 4 again
    4 is present; return {{true}}
```

## Code

```python
def contains_duplicate(nums):
    seen = set()
    for value in nums:
        if value in seen:
            return True
        seen.add(value)
    return False
```

## Complexity

For n values, expected O(n) time and O(n) auxiliary space use ordinary hash-table assumptions. The function can stop early; pathological hash collisions can make the time worse. It leaves the input unchanged.

## Mistakes and edge cases

- Check membership before inserting, otherwise every first occurrence appears to be a duplicate.
- Empty and single-element sequences return false; repeated zeros and negative values work normally.
- A set intentionally discards multiplicity, but the membership check detects the second occurrence before that information disappears.

## Variations

- Return the first repeated value encountered instead of a Boolean.
- Detect duplicates within a bounded distance by removing elements as they leave a sliding window.

=== card | 1
time: 20 min

## The problem

Given integers and a target sum, return indices of two different elements whose values add to the target. For `[5, 2, 8]` and target 10, indices `[1, 2]` are valid. The usual task guarantees a solution; this implementation returns an empty list if there is none.

## Constraints and what they imply

The array is unsorted, values can repeat or be negative, and the answer consists of original positions. A single element cannot be used twice. Even when the target is twice a value, two separate occurrences are required.

## Brute force

Try each pair of indices with the first smaller than the second and test its sum. Return the first matching pair. This needs O(n²) time and O(1) extra space, without changing the array. Sorting value-index pairs is faster but needs extra bookkeeping to recover original positions.

## The insight

For current value x, only target minus x can complete the sum. Store a mapping from each value already scanned to one of its indices. Query that complement before inserting the current value. The map contains only earlier positions, so a successful lookup cannot reuse the same index. Conversely, when the later index of any valid pair is reached, the earlier value is already in the map, so a pair is found. If there are multiple valid pairs, any returned pair is acceptable.

## Optimal solution, traced

```steps
Target 10, read 5
    need 5; map becomes {5: 0}
---
Read 2
    need 8; map becomes {5: 0, 2: 1}
---
Read 8
    need 2 at index 1; return {{[1, 2]}}
```

## Code

```python
def two_sum(nums, target):
    seen = {}
    for i, value in enumerate(nums):
        complement = target - value
        if complement in seen:
            return [seen[complement], i]
        seen[value] = i
    return []
```

## Complexity

Expected O(n) time and O(n) auxiliary space for n elements, assuming ordinary hash-table behavior. The array is not mutated. In the worst case, unfavorable hashing can degrade the lookup cost.

## Mistakes and edge cases

- Inserting before checking can pair an element with itself when it is half the target.
- Index zero is a valid result, so test dictionary membership rather than the truthiness of a retrieved index.
- Repeated values are supported; for `[3, 3]` and target 6 the second position finds the first.

## Variations

- Return all index pairs, storing lists of earlier indices rather than just one per value.
- For sorted input, use two pointers and compare their sum with the target.

=== card | 242
time: 15 min

## The problem

Decide whether two strings contain the same characters with the same multiplicities, regardless of order. Thus `aabb` and `baba` match, but `aabb` and `abbb` do not. This checks exact character equality, not case-insensitive or normalized text equivalence.

## Constraints and what they imply

The original setting uses lowercase English letters, so the alphabet has a fixed size of 26. Different lengths cannot match. This implementation also accepts empty strings and any hashable characters supported by Python strings.

## Brute force

Sort both strings and compare the results. Sorting costs O(n log n + m log m) time and O(n + m) space for lengths n and m in Python. Comparing each character with every position of the other string while consuming matches is slower and must handle duplicates carefully.

## The insight

A rearrangement preserves the count of every character. The reverse also holds: if every count agrees, both strings consist of exactly the same multiset, so one is a rearrangement of the other. Build independent frequency maps and compare them; no positional information is required. Length inequality is a cheap early rejection.

## Optimal solution, traced

```steps
Count the first string aabb
    first = {a: 2, b: 2}
---
Count baba
    second = {b: 2, a: 2}
---
Compare maps
    all counts agree; return {{true}}
```

## Code

```python
from collections import Counter

def valid_anagram(first, second):
    if len(first) != len(second):
        return False
    return Counter(first) == Counter(second)
```

## Complexity

Building and comparing counts takes expected O(n + m) time. Space is O(d) for d distinct characters, which is O(1) for the stated fixed alphabet. Hash-table operations have expected rather than guaranteed constant cost.

## Mistakes and edge cases

- Comparing sets alone misses differing multiplicities such as `aab` versus `abb`.
- Empty strings match; an empty and nonempty string do not.
- Unicode normalization and case folding change the meaning of equality and must be specified separately.

## Variations

- Replace the maps with a 26-entry array when inputs are guaranteed lowercase letters.
- Count how many character insertions or deletions are needed to make the multisets equal.

=== card | 49
time: 25 min

## The problem

Partition a list of words into groups whose members are rearrangements of one another. Each input occurrence belongs to exactly one group, including repeated identical words. For `["eat", "tea", "cat"]`, one valid result is `[["eat", "tea"], ["cat"]]`; group order and the order inside each group do not matter.

## Constraints and what they imply

Words contain lowercase English letters, and lengths may differ. The list can contain duplicates or empty strings, so neither a set of input words nor a set of letters is sufficient. A 26-entry frequency vector is a complete description of each word's character multiset. The implementation returns lists of original strings rather than transformed keys.

## Brute force

Maintain representatives for existing groups. For each new word, compare its character frequencies with each representative until a matching group is found; otherwise start another group. With n words of maximum length k, repeatedly building or comparing representations costs up to O(n²(k + 26)) time and O(nk + n) output and working space. The same group comparisons are repeated for many unrelated words.

## The insight

Map each word to a canonical key made from counts of `a` through `z`. Two words have equal keys exactly when every letter appears equally often in both, which is necessary and sufficient for being rearrangements. A dictionary maps each key to its list of occurrences. At each insertion the invariant is that all processed words appear once in the group of their own key, so after the scan the dictionary values are exactly the required partition.

Unlike sorting each word, the fixed count vector takes linear work in its length. Convert the mutable count list to a tuple before using it as a dictionary key. Separate empty strings have the same all-zero key and are retained as separate list entries.

## Optimal solution, traced

```steps
Read eat
    key has one a, one e, one t; create [eat]
---
Read tea
    same key; group becomes {{[eat, tea]}}
---
Read cat
    a different key creates [cat]
```

## Code

```python
def group_anagrams(words):
    groups = {}
    for word in words:
        counts = [0] * 26
        for ch in word:
            counts[ord(ch) - ord("a")] += 1
        key = tuple(counts)
        groups.setdefault(key, []).append(word)
    return list(groups.values())
```

## Complexity

For n words with total length L, constructing all keys takes O(L + 26n) expected time, including dictionary work. Space is O(L + 26n + n) including returned groups and stored keys; the strings themselves are referenced rather than copied. With a fixed alphabet this simplifies to O(L + n) time and space. Hash lookup is expected constant time.

## Mistakes and edge cases

- A set of letters loses multiplicity: `abb` and `aab` must not share a group.
- Lists cannot be dictionary keys; use an immutable tuple, and do not reuse a count list across words.
- This specific array indexing requires lowercase English letters; for arbitrary characters use a suitable immutable sorted frequency representation instead.
- Preserve duplicate inputs and empty words. Do not promise a particular group ordering unless the interface requires one.

## Variations

- Use sorted characters as the canonical key when the alphabet is not fixed.
- Return only groups containing at least two input occurrences.

=== card | 347
time: 25 min

## The problem

Given an integer list and k, return k distinct values with the highest occurrence counts. For `[1, 1, 1, 2, 2, 3]` and k equal to 2, the result contains 1 and 2. Output order is not important. If frequencies tie at the boundary, any selection among tied values is valid.

## Constraints and what they imply

Assume `0 <= k <= d`, where d is the number of distinct input values. The usual instance guarantees a unique selection, but the implementation also gives a valid arbitrary selection when there are ties. Frequency is always between 1 and n for a value that occurs, so it can index a bounded array of buckets. A zero k returns an empty list.

## Brute force

Count occurrences by scanning the whole input separately for every distinct value, then repeatedly choose the largest count. This can take O(n d + d²) time and O(d) extra space. Alternatively, count in one pass and sort distinct values by frequency in O(n + d log d) expected time, which is a useful baseline but does more ordering work than necessary.

## The insight

First build a frequency dictionary. Place each distinct value into the bucket indexed by its frequency, then inspect buckets from n down to 1. Every value in a later bucket has frequency no larger than every value already emitted. Stopping after k values therefore yields a valid top-k selection, including when a bucket contains more values than the remaining slots. Counts establish the buckets, and the descending scan establishes the ranking.

Each value is placed once, not once per occurrence. Bucket zero is unused for a real input value. The count dictionary can be constructed without modifying the input, and no tie-breaking rule is needed unless one is explicitly specified.

## Optimal solution, traced

```steps
Count [1, 1, 1, 2, 2, 3]
    counts = {1: 3, 2: 2, 3: 1}
---
Read bucket 3 then bucket 2
    result = {{[1, 2]}}
---
Already selected k = 2
    return without reading lower buckets
```

## Code

```python
from collections import Counter

def top_k_frequent(nums, k):
    if k == 0:
        return []
    counts = Counter(nums)
    buckets = [[] for _ in range(len(nums) + 1)]
    for value, frequency in counts.items():
        buckets[frequency].append(value)
    result = []
    for frequency in range(len(nums), 0, -1):
        for value in buckets[frequency]:
            result.append(value)
            if len(result) == k:
                return result
    return result
```

## Complexity

Counting, allocating and scanning the buckets, and placing the d distinct values take expected O(n + d) time, hence O(n). The count map, bucket headers, stored values, and result use O(n + d) space. Hash operations are expected constant time; bucket initialization makes the O(n) space bound explicit.

## Mistakes and edge cases

- Stop as soon as k values are collected, even in the middle of a tied bucket.
- Use n + 1 buckets because a value may occur n times.
- Returning all values from the final bucket could exceed k. Empty input is supported when k is zero.
- This function assumes a valid k; it does not raise an error for an invalid request.

## Variations

- Use a size-k min-heap of counts for O(n + d log k) expected time and O(d + k) space.
- Define a deterministic secondary ordering for ties, then explicitly enforce that rule.

=== card | 36
time: 25 min

## The problem

Validate a partially filled nine-by-nine number grid. Among filled cells, no digit may appear twice in a row, a column, or any of the nine three-by-three boxes. Empty cells are marked `"."`. The question is whether the current entries satisfy these local rules, not whether the board can be completed.

## Constraints and what they imply

The board has exactly nine rows of nine cells; each cell is either `"."` or a digit from `"1"` through `"9"`. A cell contributes to one row, one column, and one box. The fixed board size means a constant amount of work in the formal complexity model, but describing costs in terms of visited cells is still useful for understanding the method.

## Brute force

For every filled cell, scan the remainder of its row, column, and box for the same digit. There are 81 cells and up to a constant number of comparisons for each on this fixed board. Generalized to a side length s with square boxes, checking all groups this way can take O(s³) time and O(1) auxiliary space. It repeatedly compares cells that have already been checked.

## The insight

Track three families of sets, one per row, column, and box. When visiting a digit, a prior copy in any of its three sets proves a violation. If none contains it, add it to all three. At every step each set contains exactly the previously visited filled digits in that group. Hence a duplicate is rejected when its later cell is processed, while a board that finishes has no duplicate in any group.

The box index `(row // 3) * 3 + col // 3` ranges from 0 to 8. Separate sets for rows, columns, and boxes prevent identical digits in unrelated groups from interfering with each other. Skipping empty cells prevents the placeholder from being treated as a digit.

## Optimal solution, traced

```steps
Read digit 5 at row 0, column 0
    rows[0], cols[0], boxes[0] each receive 5
---
Read digit 3 at row 0, column 1
    none of its three groups contains 3; insert it
---
Read digit 5 at row 1, column 1
    box 0 already contains 5; return {{false}}
```

## Code

```python
def valid_sudoku(board):
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            digit = board[r][c]
            if digit == ".":
                continue
            box = (r // 3) * 3 + c // 3
            if digit in rows[r] or digit in cols[c] or digit in boxes[box]:
                return False
            rows[r].add(digit)
            cols[c].add(digit)
            boxes[box].add(digit)
    return True
```

## Complexity

The 81 cells and at most 243 set insertions give O(1) time and space for the fixed board. For a generalized s-by-s board with suitable square boxes, there are O(s²) cells and O(s²) stored group memberships, with expected O(s²) time and space. The input is not modified.

## Mistakes and edge cases

- Checking only rows and columns misses a repeated digit within one box.
- Do not share one set across every row or count the placeholder as a filled digit.
- Construct independent sets; repeating a single set object in a list aliases all groups.
- A valid partial board need not have any solution. Input shape and symbols are assumed valid.

## Variations

- Return the offending cell and group when a duplicate is detected.
- Generalize to an s-by-s grid whose boxes have side length equal to the integer square root of s.

=== card | 2001
time: 25 min

## The problem

Count pairs of distinct rectangles with equal width-to-height ratios. A pair is unordered, so the pair of positions `(i, j)` is counted once with `i < j`. For `[(2, 4), (3, 6), (3, 4)]`, only the first two rectangles form such a pair.

## Constraints and what they imply

Widths and heights are positive integers. Ratios need exact comparison: nearly equal fractions are not necessarily equal, and floating-point rounding is not a proof of equality. Duplicated dimensions still describe separate rectangles, and all their index pairs count. Since the result can be quadratic in the number of rectangles, fixed-width languages should use a sufficiently wide integer for the answer.

## Brute force

For every pair, test whether `w1 * h2 == w2 * h1`, using integer cross multiplication. This takes O(n²) time and O(1) extra space for n rectangles. It is an excellent reference for small inputs but repeats comparisons among rectangles in the same ratio class.

## The insight

Divide both dimensions by their greatest common divisor to obtain a reduced positive integer pair. By uniqueness of reduced fractions, two rectangles have the same ratio exactly when their reduced pairs match. Store the number of previous occurrences of each key. When a new key appears, all previous rectangles with that key form a new pair with it; add that count to the result and then increment it.

The invariant is that the map stores counts for exactly the processed prefix and the answer counts all matching pairs wholly inside that prefix. Adding the previous count counts each new pair exactly once, at its later index. No comparisons between unrelated ratio classes are required.

## Optimal solution, traced

```steps
Read (2, 4)
    gcd 2; key (1, 2), previous count 0, answer 0
---
Read (3, 6)
    key (1, 2), previous count 1; answer becomes {{1}}
---
Read (3, 4)
    key (3, 4) is new; answer remains 1
```

## Code

```python
from math import gcd

def interchangeable_rectangles(rectangles):
    seen = {}
    pairs = 0
    for width, height in rectangles:
        divisor = gcd(width, height)
        key = (width // divisor, height // divisor)
        pairs += seen.get(key, 0)
        seen[key] = seen.get(key, 0) + 1
    return pairs
```

## Complexity

Let M be the largest side length. Euclid's algorithm takes O(log M) time per rectangle, and expected dictionary work is O(1) per rectangle, for O(n log M) expected time. The dictionary stores at most n ratio keys, using O(n) auxiliary space. Python integers avoid overflow in the pair count.

## Mistakes and edge cases

- Reducing width and height independently or swapping their order changes the ratio.
- A float key may merge distinct rational numbers; reduced integer pairs are exact.
- Add the old count before incrementing, or the rectangle would pair with itself.
- The positivity assumption avoids zero denominators and ambiguous zero-by-zero rectangles. An empty list returns zero.

## Variations

- Count pairs with equal slopes by reducing signed direction vectors and fixing a sign convention.
- Group rectangle indices by ratio instead of returning only the number of pairs.

=== card | 128
time: 25 min

## The problem

Find the length of the longest run of consecutive integer values present in an unsorted list. Values need not appear consecutively in the input, and duplicate occurrences do not lengthen a run. For `[7, 2, 4, 3, 2]`, the run 2, 3, 4 has length 3. Return zero for an empty list.

## Constraints and what they imply

The list can contain negative values and duplicates. Its ordering provides no direct evidence of neighboring integer values, and the intended target is linear expected time. A set supports membership tests while removing duplicates, so it captures exactly which values are available without recording their input positions.

## Brute force

For each input value, repeatedly search the entire list for the next integer and count how far the sequence continues. A membership search costs O(n), and trying many starting points repeats the same suffixes, producing up to O(n³) time in a straightforward implementation. Sorting a copy and scanning unique neighbors gives O(n log n) time and O(n) extra space and is a simpler baseline.

## The insight

Only start a walk at a value whose predecessor is absent. Such a value is the unique beginning of its maximal consecutive run. Walk upward until a value is missing, update the best length, and ignore all other values as potential starts. Every run in the set has exactly one start and is fully visited from that start, so the maximum found is the correct answer.

Iterate over the set rather than the original list. Otherwise repeated copies of a start could each trigger a full walk and destroy the linear bound. Although there is an inner loop, successful walk iterations across all starts total at most the number of distinct values. There is also one terminating failed lookup per run.

## Optimal solution, traced

```steps
Build set from [7, 2, 4, 3, 2]
    values = {2, 3, 4, 7}
---
2 has no predecessor
    walk 2, 3, 4; best becomes {{3}}
---
3 and 4 have predecessors; 7 starts a run of length 1
    best remains 3
```

## Code

```python
def longest_consecutive(nums):
    values = set(nums)
    best = 0
    for start in values:
        if start - 1 not in values:
            end = start
            while end in values:
                end += 1
            best = max(best, end - start)
    return best
```

## Complexity

Creating the set, checking each distinct value, and walking all runs take expected O(n) time for n input elements under usual hash-table assumptions. The set holds O(n) values, so auxiliary space is O(n). Integer arithmetic is treated as constant time for bounded input integers. The input is unchanged.

## Mistakes and edge cases

- Starting a walk from every value repeats suffixes and can be quadratic.
- Iterate over distinct set members, not duplicate entries in the input.
- Do not confuse consecutive values with adjacent positions. Negative values and zero work naturally.
- The empty set yields zero; a list of identical numbers yields one.

## Variations

- Return the actual endpoints of one longest run, not just its length.
- For an online stream, maintain merged interval lengths at the endpoints of each run.

=== card | 454
time: 30 min

## The problem

Given four integer arrays, count choices of one index from each whose values sum to zero. Different index choices count separately even if their values are identical. For `[1, 1]`, `[-1]`, `[0]`, and `[0]`, there are two valid choices. The function also supports arrays of unequal lengths and empty arrays.

## Constraints and what they imply

The usual setting gives four arrays of the same length n, which can be large enough that enumerating n to the fourth choices is too slow. Values may be positive, negative, or zero. Counting rather than merely detecting a sum requires retaining the number of index pairs that produce each intermediate sum.

## Brute force

Use four nested loops and increment the answer whenever the four selected values add to zero. This uses O(n⁴) time and O(1) auxiliary space for equal-length arrays. It naturally handles duplicates because it enumerates index choices, but performs the same partial-sum work many times.

## The insight

Split every quadruple into an index pair from the first two arrays and an index pair from the last two. Count all first-half sums in a dictionary. For each second-half sum s, exactly the stored pairs with sum `-s` complete it to zero. Add their frequency rather than just testing membership.

Each possible quadruple has one unique decomposition into its first and second index pairs. It is counted when the second pair is visited if and only if the corresponding first pair has the needed sum. This proves both completeness and absence of double counting. Multiplicity is essential: two equal first-half sums from different index pairs represent two distinct quadruples for the same second pair.

## Optimal solution, traced

```steps
Arrays [1, 1], [-1], [0], [0]
    first-half sum 0 occurs twice
---
Visit second-half pair (0, 0)
    need sum 0; add its frequency 2
---
No more second-half pairs
    return {{2}}
```

## Code

```python
from collections import Counter

def four_sum_count(a, b, c, d):
    first_sums = Counter(x + y for x in a for y in b)
    total = 0
    for x in c:
        for y in d:
            total += first_sums.get(-(x + y), 0)
    return total
```

## Complexity

For equal-length arrays, O(n²) pair sums are counted and O(n²) complements are queried, for expected O(n²) time and O(n²) auxiliary space in the worst case. More generally the bounds are O(len(a) len(b) + len(c) len(d)) expected time and O(len(a) len(b)) space. A smaller side can be chosen for storage if memory matters.

## Mistakes and edge cases

- Store frequencies, not just a set of sums, or duplicate index combinations disappear.
- Negate the entire second-half sum; checking an unnegated sum solves a different problem.
- An empty array yields zero choices. Python supports large counts; fixed-width implementations need an adequate count type.
- The input arrays are not modified, and equal values at different indices remain distinct choices.

## Variations

- Count quadruples with a given target by looking up `target - x - y`.
- For uneven array sizes, choose a partition that balances storage and iteration costs.

=== card | 2131
time: 30 min

## The problem

Choose and arrange any number of two-letter words to make a character-level palindrome of maximum possible length. Each occurrence may be used at most once. Return the length, not the constructed string. For `["ab", "ba", "cc"]`, all three can be arranged as `abccba`, giving length 6.

## Constraints and what they imply

Every word consists of exactly two lowercase English letters; duplicate words are separate available occurrences. There are at most 26² distinct word types, regardless of the number of input occurrences. The empty selection has length zero. Because all blocks have even length, reversal maps block boundaries to block boundaries in the resulting palindrome.

## Brute force

Try each ordered selection of distinct word occurrences, concatenate it, and test whether the resulting string equals its reversal. This explores factorially many arrangements and needs O(n) space for a recursion path, excluding constructed strings. Even testing subsets alone is not enough unless an ordering is also examined.

## The insight

In a palindrome, a word on the left must be mirrored by its reversed word on the right. For different-letter words, a type and its reverse contribute as many pairs as the smaller frequency. Process each unordered type pair once. For a double-letter word such as `cc`, pairs of identical copies can occupy mirrored positions. At most one leftover double-letter copy can occupy the center.

These are upper bounds because every noncentral block must have its reverse opposite it and there is only one central position. They are achievable: place every selected left block in any order, put one leftover symmetric block in the center if available, then place the reversed partners in reverse block order. Each mirrored pair contributes four characters and the possible center contributes two, proving optimality.

## Optimal solution, traced

```steps
Counts for [ab, ba, cc]
    ab: 1, ba: 1, cc: 1
---
Pair ab with ba
    length = 4
---
One cc can be the center
    return {{6}}
```

## Code

```python
from collections import Counter

def longest_palindrome_words(words):
    counts = Counter(words)
    length = 0
    center = False
    for word, count in counts.items():
        reverse = word[::-1]
        if word == reverse:
            length += (count // 2) * 4
            if count % 2:
                center = True
        elif word < reverse:
            length += min(count, counts.get(reverse, 0)) * 4
    return length + (2 if center else 0)
```

## Complexity

Counting n fixed-length words takes expected O(n) time; the subsequent scan is bounded by the number of distinct words, at most 676. Auxiliary space is O(1) under the fixed alphabet constraint, or O(d) for d distinct word types if the alphabet is allowed to grow. The returned length fits Python integers and the input is unchanged.

## Mistakes and edge cases

- Do not count both a word and its reverse as separate mirrored pairs.
- A double-letter word can be central, but multiple odd leftovers cannot all be placed at the center.
- A pair contributes four characters, not two. Identical repeated occurrences can be used independently.
- With no usable pairs or symmetric word, return zero. The fixed two-character assumption is essential to this block-level argument.

## Variations

- Construct an actual maximum palindrome by saving chosen pairs and a center word.
- If all words have an equal length other than two, use reversal pairs and permit one self-reversing center block.

=== card | 554
time: 25 min

## The problem

Given a wall represented by rows of positive brick widths, choose a vertical line strictly inside the wall that crosses the fewest bricks. A line exactly along a joint between adjacent bricks crosses neither of those bricks in that row. Every row has the same total width. Return the minimum number of crossed bricks.

## Constraints and what they imply

Each row is nonempty, every width is a positive integer, and total row widths agree. The line cannot run along the outer left or right boundary. Since widths are positive, internal joints in a row occur at distinct prefix sums; a row can contribute at most one joint at a given position. If the total width is one, interpret the line as any real coordinate strictly between its edges.

## Brute force

Consider every internal joint position from every row as a candidate, and for each candidate scan all bricks to determine whether it is a joint in each row. Also consider a non-joint position for the case with no internal joints. If B is the total number of bricks, this direct comparison takes O(B²) time in the worst case and O(B) space for candidate positions.

## The insight

At a fixed interior coordinate, a row is crossed unless that coordinate is one of its internal joints. Therefore minimizing crossings is the same as maximizing how many rows have a joint there. Accumulate the widths in each row and count each prefix except the full row width. The most common internal joint saves exactly that many crossings.

Every potentially beneficial coordinate appears as a counted joint; any other interior coordinate crosses every row. Positive widths ensure one row cannot inflate a position's count by contributing it twice. Thus the number of rows minus the largest joint frequency is attainable and is no larger than the count at any other coordinate. If there are no internal joints, use a largest frequency of zero.

## Optimal solution, traced

```steps
Rows [1, 2] and [2, 1]
    internal joints occur at 1 and 2
---
Add row [1, 1, 1]
    joints 1 and 2 each now occur twice
---
Three rows minus best count 2
    minimum crossings = {{1}}
```

## Code

```python
from collections import Counter

def least_bricks(wall):
    joints = Counter()
    for row in wall:
        position = 0
        for width in row[:-1]:
            position += width
            joints[position] += 1
    return len(wall) - max(joints.values(), default=0)
```

## Complexity

For B total bricks, accumulating prefixes and finding the largest frequency takes expected O(B) time. At most B distinct joint positions are stored, so auxiliary space is O(B). The row slice uses at most O(B) transient space; an iterator could avoid that copy. Hash-map costs are expected. The input is unchanged.

## Mistakes and edge cases

- Counting the final prefix would allow the forbidden right boundary and falsely give zero crossings.
- Do not count the left boundary either; the scan adds only after an interior brick.
- Single-brick rows have no internal joints and must always be crossed.
- An empty wall returns zero here, although normal wall inputs are nonempty. Equal totals and positive widths are assumed.

## Variations

- Return an interior coordinate achieving the minimum, using a non-joint coordinate if no joint exists.
- Weight crossings by row and maximize the sum of weights saved at each joint.

=== card | 229
time: 30 min

## The problem

Return every integer occurring strictly more than one third of the length of an input list. The order of the returned values does not matter. For `[1, 2, 1, 3, 1, 2, 2]`, both 1 and 2 occur three times and qualify because three is greater than seven divided by three.

## Constraints and what they imply

Values may be negative or repeated, and the threshold is strict: a value occurring exactly n/3 times does not qualify. At most two different values can qualify, because three such frequencies would sum to more than n. The desired follow-up uses constant auxiliary space rather than a frequency map. The implementation also accepts an empty list.

## Brute force

For each distinct value, scan the entire list to count its occurrences and keep it if the count passes the threshold. This uses O(n²) time and O(n) space if a set of tested values is retained. A frequency dictionary reduces expected time to O(n) but uses O(n) additional space, so it does not meet the constant-space follow-up.

## The insight

Maintain two candidate values and their residual counters. A matching value increments its counter; otherwise fill a zero counter if possible. If both counters are positive and neither candidate matches, decrement both: this removes one occurrence from each candidate together with the current third distinct value. Think of these as canceled triples of different values.

Every canceled triple removes at most one occurrence of any particular value. A value occurring more than n/3 times cannot be completely removed by at most n/3 such triples, so it must remain among the final positive-count candidates. Residual counts are not the original frequencies, however, and a surviving candidate might not qualify. A second pass counts the candidates in the original input and applies the strict threshold.

Testing candidate matches before filling empty slots avoids representing one value twice. Only positive-count slots are verified, and the final loop keeps the output unique. The proof does not depend on the input order.

## Optimal solution, traced

```steps
Read 1, 2, 1
    candidates 1 and 2, residual counts 2 and 1
---
Read 3
    three different values cancel; counts become 1 and 0
---
Read 1, 2, 2
    candidates 1 and 2 survive; verification finds {{3 each}}
```

## Code

```python
def majority_thirds(nums):
    first = second = None
    count_first = count_second = 0
    for value in nums:
        if count_first and value == first:
            count_first += 1
        elif count_second and value == second:
            count_second += 1
        elif count_first == 0:
            first, count_first = value, 1
        elif count_second == 0:
            second, count_second = value, 1
        else:
            count_first -= 1
            count_second -= 1
    result = []
    for candidate, count in ((first, count_first), (second, count_second)):
        if count and candidate not in result:
            occurrences = sum(value == candidate for value in nums)
            if occurrences > len(nums) // 3:
                result.append(candidate)
    return result
```

## Complexity

The candidate pass and at most two verification scans take O(n) time. There are only two candidates, two counters, and at most two returned values, so auxiliary space is O(1), including the output. The input is read repeatedly but not modified.

## Mistakes and edge cases

- The residual counters are not true frequencies; omitting verification can return false positives.
- Use a strict comparison against `n // 3`, not a greater-than-or-equal comparison.
- Do not verify an inactive slot or return the same candidate twice.
- Empty input returns an empty list. A single element qualifies, and exactly n/3 occurrences do not.

## Variations

- For the threshold n/k, keep k-1 candidate counters and cancel k distinct values at a time.
- If extra space is allowed, count with a dictionary and filter by the threshold in a single simpler approach.
