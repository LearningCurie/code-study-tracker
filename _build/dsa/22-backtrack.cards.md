=== card | 1863
time: 20 min

## The problem

For each subset of an integer list, XOR its members, then add all of those XOR results. The empty subset contributes zero. For `[2, 5]`, the four contributions are 0, 2, 5, and 7, giving 14. Equal values at different positions still represent distinct choices.

## Constraints and what they imply

The original input has at most 12 positive integers, so visiting all `2^n` subsets is practical. XOR is associative, and zero is its identity. We can keep the XOR of the choices made so far instead of recalculating it at each leaf. The function also handles an empty list.

## Brute force

List all bit masks, and for each mask scan every input position to compute its subset XOR from scratch. Add the results. This takes O(n 2^n) time and O(1) auxiliary space if masks are processed one at a time.

## The insight

At position `i`, a subset either excludes that occurrence or includes it. These two branches partition all remaining choices. Pass the running XOR to the child, toggling it only in the include branch. At the end, return that subset's XOR; adding the two child results accounts for every subset exactly once.

## Optimal solution, traced

```steps
Input [2, 5], start at index 0 with XOR 0
---
Exclude 2: excluding 5 contributes 0, including 5 contributes 5
---
Include 2: excluding 5 contributes 2, including 5 contributes 7
---
Add 0 + 5 + 2 + 7 = {{14}}
```

## Code

```python
def subset_xor_sum(nums):
    def visit(i, value):
        if i == len(nums):
            return value
        return visit(i + 1, value) + visit(i + 1, value ^ nums[i])

    return visit(0, 0)
```

## Complexity

The binary tree has O(2^n) nodes and depth n, giving O(2^n) time and O(n) stack space. An arithmetic shortcut based on bitwise OR can reduce time to O(n), but this search exposes the choices directly.

## Mistakes and edge cases

- Add the leaf XORs, rather than XORing them together.
- The empty subset has value zero; duplicates are separate positions.
- Do not mutate a shared running value without restoring it between branches.

## Variations

- Return the individual subset XORs instead of their sum.
- Derive the OR shortcut by pairing subsets that differ in a position carrying a chosen bit.

=== card | 78
time: 25 min

## The problem

Return every subset of a list of distinct integers, including the empty subset. A subset may appear in any order in the outer result, and its elements need not be reordered. For `[4, 9]`, one possible result is `[[], [4], [4, 9], [9]]`. The result consists of selections, not just selections of a fixed size.

## Constraints and what they imply

The input contains at most ten distinct values. There are exactly `2^n` possible subsets because each position is selected or omitted. Thus writing the answer already takes exponential space, and an algorithm returning all subsets cannot have polynomial total time. The empty selection is a valid answer, including when the input list itself is empty.

## Brute force

Enumerate the `2^n` binary masks and scan all n positions for each one. Construct a list from positions whose mask bits are set. This takes O(n 2^n) time, including constructing the output. It is a useful independent way to check a recursive implementation, though it still performs a full scan for every mask.

## The insight

Build each selection in increasing input-index order. At a node, the current path is itself a complete subset, and a loop chooses its next index from those at or after `start`. After choosing index `i`, recurse starting at `i + 1`, then remove the choice.

Every subset has a unique increasing sequence of selected indices, so there is exactly one path to it. Recording at every node captures subsets of all sizes; starting with an empty path captures the empty subset. A snapshot is necessary because the mutable path is later changed.

## Optimal solution, traced

```steps
Input [4, 9]; record the empty path []
---
Choose 4: record [4], then choose 9 and record [4, 9]
---
Undo both choices; choose 9 at the root and record [9]
---
All four subsets: {{[], [4], [4, 9], [9]}}
```

## Code

```python
def subsets(nums):
    answer = []
    path = []

    def visit(start):
        answer.append(path.copy())
        for i in range(start, len(nums)):
            path.append(nums[i])
            visit(i + 1)
            path.pop()

    visit(0)
    return answer
```

## Complexity

There are `2^n` nodes, one per subset. Copying their paths costs O(n 2^n) total time in the worst case; the output holds O(n 2^n) elements. Excluding output, the path and recursion stack take O(n) space.

## Mistakes and edge cases

- Save a copy, not a reference to the path that will be popped.
- Advance to `i + 1`; restarting at zero permits permutations or reuse.
- Do not omit the root: it represents the empty subset.
- This version assumes distinct input values; equal values require duplicate handling.

## Variations

- Emit only subsets of size k and prune when too few indices remain.
- Enumerate subsets using bit masks instead of recursion.
- Produce a lazy iterator when consumers do not need all answers in memory.

=== card | 46
time: 25 min

## The problem

List every ordering of distinct input integers. Each ordering uses every element exactly once. For `[3, 8, 1]`, both `[3, 8, 1]` and `[8, 3, 1]` belong in the result. The order in which the outer list presents the answers is immaterial.

## Constraints and what they imply

The original input contains at most six distinct integers. There are `n!` outputs for n items, so even a perfect enumerator must do factorial work to write them all. The function also treats the empty input as having one ordering, the empty list; this makes the recursive base case mathematically consistent.

## Brute force

Generate every length-n sequence by selecting any of the n input positions independently at every step. Reject a completed sequence if a position was reused. That considers `n^n` leaves, most of which are invalid for larger n. Testing uniqueness only at the end wastes effort on prefixes that cannot become permutations.

## The insight

Keep a Boolean flag for each index already present in the current path. A recursive call chooses an unused index for the next position. Immediately after the child returns, pop the value and clear its flag so the next sibling sees the same state as before that choice.

Every recorded path contains n distinct indices and is therefore valid. Conversely, following the indices of any desired ordering is always allowed, and the ordering fixes exactly one route through the tree. Distinct input values ensure different routes yield different value lists.

The used flags describe only the current prefix, not every position seen during the entire search. Their lifetime is exactly one recursive choice, which is why removing a flag on return is as important as setting it on entry.

## Optimal solution, traced

```steps
Input [3, 8]; start with empty path and no used positions
---
Choose 3, then 8: record [3, 8]; undo both choices
---
Choose 8, then 3: record [8, 3]
---
No other unused root choices remain: {{2 orderings}}
```

## Code

```python
def permutations(nums):
    answer, path = [], []
    used = [False] * len(nums)

    def visit():
        if len(path) == len(nums):
            answer.append(path.copy())
            return
        for i, value in enumerate(nums):
            if used[i]:
                continue
            used[i] = True
            path.append(value)
            visit()
            path.pop()
            used[i] = False

    visit()
    return answer
```

## Complexity

There are n! leaves, and copying each length-n answer costs O(n n!). The internal loops also fit this bound. The output occupies O(n n!) space; apart from it, flags, path, and recursion occupy O(n).

## Mistakes and edge cases

- Restore both the path and the used flag after exploring a child.
- Record a copy; later mutations must not alter earlier answers.
- Input duplicates need an additional sibling-level rule to avoid repeated outputs.
- With no elements, the base case returns `[[]]`, not an empty collection.

## Variations

- Generate unique permutations from a multiset by skipping equivalent choices.
- Stop after finding the first ordering satisfying a predicate.
- Generate permutations in lexicographic order from sorted input.

=== card | 90
time: 30 min

## The problem

Return all distinct subsets of an integer list that can contain repeated values. Each occurrence may be used at most once, but selecting either of two equal occurrences does not create different answers. For `[1, 2, 2]`, `[2]` appears once, and `[2, 2]` is also a valid subset.

## Constraints and what they imply

The original input has at most ten elements. Up to `2^n` index selections exist, but several may describe the same multiset. The output must distinguish different counts of a repeated value while collapsing selections that differ only by which equal occurrence was picked. Sorting a copy puts equivalent next choices together without changing the caller's list.

## Brute force

Enumerate all index masks, sort each selected list, and insert its tuple into a set. Finally convert the set back into lists. The approach is correct but constructs and hashes duplicate candidates; a straightforward implementation costs O(n 2^n + n log n) time after sorting and can retain O(n 2^n) output-sized space.

## The insight

As with ordinary subsets, record the path at every node and choose only indices from `start` onward. After sorting, if two adjacent values are equal, choosing either as the *next* value at the same node yields equivalent possibilities. Skip the later one only when `i > start`.

The restriction does not prevent choosing the second copy in a child call, because there it is the first available index. Thus `[2, 2]` is retained. Each multiset has one canonical increasing index path: for each value choose the earliest available copies. Every allowed path yields a valid multiset, and the sibling skip eliminates all competing paths.

## Optimal solution, traced

```steps
Sorted input [1, 2, 2]; record []
---
At root choose 1; under it choose the first 2, then the second: record [1, 2, 2]
---
Back at the node after 1, skip the second 2 as an equivalent sibling
---
At root choose the first 2 and its child may choose the second: {{[2, 2]}}
```

## Code

```python
def subsets_with_duplicates(nums):
    values = sorted(nums)
    answer, path = [], []

    def visit(start):
        answer.append(path.copy())
        for i in range(start, len(values)):
            if i > start and values[i] == values[i - 1]:
                continue
            path.append(values[i])
            visit(i + 1)
            path.pop()

    visit(0)
    return answer
```

## Complexity

There are at most `2^n` distinct outputs. Copying paths costs O(n 2^n) time in the worst case, plus O(n log n) sorting; the output takes O(n 2^n) space. The sorted copy, path, and recursion use O(n) auxiliary space.

## Mistakes and edge cases

- `i > 0` is too broad: it can forbid the second equal value at a deeper level.
- Skipping duplicates requires sorted values; keep a copy if input mutation matters.
- An empty list still has the empty subset, and all-equal inputs retain every possible multiplicity.

## Variations

- Count distinct subsets from the frequency of each value without listing them.
- List only size-k subsets, still avoiding equivalent sibling choices.
- Enumerate unique permutations using a used array and a related duplicate rule.

=== card | 39
time: 30 min

## The problem

Given distinct positive candidate integers and a nonnegative target, list every multiset of candidates whose sum equals the target. Each candidate can be selected repeatedly. For candidates `[2, 3, 5]` and target 8, examples are `[2, 2, 2, 2]`, `[2, 3, 3]`, and `[3, 5]`. Reordering a multiset does not create another answer.

## Constraints and what they imply

All candidates are strictly positive. Consequently each selection decreases the remaining target and the recursion terminates. The original task uses distinct candidates and a positive target; the function additionally defines target zero to have one solution, the empty selection. Sorting allows a loop to stop when its next candidate exceeds the remainder, because every later value also exceeds it.

## Brute force

Generate all ordered sequences of candidates up to length `target / min(candidate)`, sum them, and keep those reaching the target. Sort each successful sequence and deduplicate it in a set. This wastes time exploring different orders of the same multiset, in addition to visiting sequences that have already exceeded the target. Its branching factor is the number of candidates at every level.

## The insight

Force choices to use nondecreasing candidate indices. This gives every multiset one canonical sequence, eliminating ordering duplicates. From a call with `start`, choose an index `i >= start` and recurse from `i`, not `i + 1`, because the same value is allowed again. A zero remainder records a complete solution.

Every recorded path has the requested sum: each recursive step subtracts exactly what it appends. Conversely, sorting any valid multiset produces a nondecreasing sequence that this recursion can follow. Since the candidate values are distinct, that sequence is unique. The sorted cutoff is safe because no later positive candidate fits either.

## Optimal solution, traced

```steps
Candidates [2, 3, 5], target 8; choose 2, remainder 6
---
Choose 3 twice, leaving 0: record [2, 3, 3]
---
Undo; choose 5 after 3 would exceed the remaining 3, so stop that loop
---
Other branches include [2, 2, 2, 2] and {{[3, 5]}}
```

## Code

```python
def combination_sum(candidates, target):
    values = sorted(candidates)
    answer, path = [], []

    def visit(start, remaining):
        if remaining == 0:
            answer.append(path.copy())
            return
        for i in range(start, len(values)):
            value = values[i]
            if value > remaining:
                break
            path.append(value)
            visit(i, remaining - value)
            path.pop()

    visit(0, target)
    return answer
```

## Complexity

Let n be the number of candidates and `d = floor(target / min(candidate))` when candidates are nonempty. A loose bound, including loops and output copies, is O((d + 1) n^(d + 1) + n log n). The depth and path are O(d), and the sorted copy is O(n), excluding output. The empty-candidate case terminates immediately. This bound is intentionally loose because pruning and canonical order reduce the search.

## Mistakes and edge cases

- Recurse from `i`, not `i + 1`, to allow reuse.
- Zero or negative candidates break the termination argument and are outside the contract.
- Sorting plus the start index prevents permutations of the same multiset.
- Target zero returns `[[]]`; no candidates and a positive target returns `[]`.

## Variations

- Allow each occurrence at most once and skip equal siblings.
- Count combinations rather than returning them, using a sum-based dynamic program.
- Restrict the number of selected items as well as their total.

=== card | 22
time: 25 min

## The problem

Generate every correctly nested string made from n opening and n closing parentheses. For two pairs, the strings are `(())` and `()()`. A closing parenthesis must match an earlier unmatched opening one; simply having equal totals at the end is not sufficient.

## Constraints and what they imply

The original task uses a small positive n, at most eight, because the number of results grows rapidly. Every prefix of a valid string has at least as many opens as closes, and the final string has exactly n of each. The function additionally supports zero pairs, returning the single empty string. Results can be returned in any order.

## Brute force

Enumerate all `2^(2n)` sequences of opening and closing characters. Scan each sequence, rejecting it if a prefix balance becomes negative or its final balance is not zero. This uses O(n 4^n) time and constructs many prefixes that are already impossible. The prefix test suggests how to stop exploring those branches earlier.

## The insight

Track how many opens and closes have been appended. An open is legal while fewer than n opens have been used; a close is legal while fewer closes than opens have been used. Thus every generated prefix respects both the quota and the balance rule. When n closes have been placed, n opens must already have been placed, so the path is complete.

For completeness, take any valid answer. Its next character must satisfy the corresponding rule, so the recursion can follow it to a leaf. A string uniquely determines its choices, so no two paths produce the same answer. Saving the joined path at the leaf is safe even though the path is later popped.

## Optimal solution, traced

```steps
n = 2: choose an open, prefix (
---
Choose a second open, then both closes: record (())
---
Backtrack; close the first pair, then open and close: record ()()
---
No other legal next choices remain: {{(()) and ()()}}
```

## Code

```python
def generate_parentheses(n):
    answer, path = [], []

    def visit(opened, closed):
        if closed == n:
            answer.append("".join(path))
            return
        if opened < n:
            path.append("(")
            visit(opened + 1, closed)
            path.pop()
        if closed < opened:
            path.append(")")
            visit(opened, closed + 1)
            path.pop()

    visit(0, 0)
    return answer
```

## Complexity

There are `C_n` answers, where `C_n = binom(2n, n)/(n+1)`. Every legal prefix can be completed and has length at most `2n`, so O(n C_n) time is a safe output-sensitive bound, including string construction. The stack and path take O(n) auxiliary space, excluding O(n C_n) output space.

## Mistakes and edge cases

- Checking only the final counts admits strings with an invalid prefix.
- A close requires `closed < opened`, not merely `closed < n`.
- The zero-pair result is `[""]`; negative n is outside the contract.

## Variations

- Count valid strings without enumerating them using Catalan recurrence.
- Generate strings using several bracket types with a stack of unmatched opens.
- Find the kth lexicographic valid string using counts of completions.

=== card | 131
time: 30 min

## The problem

Split a string into contiguous, nonempty pieces so that every piece is a palindrome. Return all possible lists of pieces. For `"aab"`, the valid partitions are `["a", "a", "b"]` and `["aa", "b"]`. The pieces must concatenate to the original string in order; anagrams or arbitrary subsequences do not qualify.

## Constraints and what they imply

The source task limits the string length to 16, making exponential enumeration feasible. There are `n - 1` possible cut positions, so output size can be exponential: if every character is identical, every cut pattern works. Precomputing palindrome status avoids rescanning the same interval for many different preceding partitions. The implementation also accepts the empty string, for which the empty partition is returned.

## Brute force

Try all `2^(n-1)` patterns of cuts and scan each resulting piece from both ends to test whether it is a palindrome. Checking and writing a candidate costs O(n), giving O(n 2^n) time in the worst case and O(n) working space apart from results. This is already a useful baseline; table-based pruning avoids exploring a prefix as soon as its last piece fails.

## The insight

Let `pal[i][j]` describe the inclusive substring from i through j. It is palindromic exactly when the endpoint characters match and its interior is palindromic, with lengths one and two as base cases. Fill starting indices from right to left so every needed interior entry is ready.

From `start`, try every palindromic piece ending at or after it, append it, recurse on the suffix, and undo the choice. Each finished path covers the entire input and contains only palindromes. Any valid partition chooses one of the tested ends at each step, and its cut positions uniquely determine its route.

## Optimal solution, traced

```steps
For "aab", the table marks "a", "aa", and "b" as palindromes
---
Choose the first "a", then the second "a", then "b": record [a, a, b]
---
Undo to the root and choose "aa", then "b": record [aa, b]
---
The full "aab" is not a palindrome: {{two partitions}}
```

## Code

```python
def palindrome_partitions(s):
    n = len(s)
    pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            pal[i][j] = s[i] == s[j] and (j - i < 2 or pal[i + 1][j - 1])

    answer, path = [], []

    def visit(start):
        if start == n:
            answer.append(path.copy())
            return
        for end in range(start, n):
            if pal[start][end]:
                path.append(s[start:end + 1])
                visit(end + 1)
                path.pop()

    visit(0)
    return answer
```

## Complexity

The table takes O(n²) time and space. Search and output take O(n 2^n) time in the worst case, including substring and result construction. Output can occupy O(n 2^n) space. Beyond output, the table is O(n²), with O(n) recursion and path depth.

## Mistakes and edge cases

- Fill the table in an order where the inner interval is already known.
- Check the inclusive endpoint carefully; slicing uses an exclusive endpoint.
- A single character is a palindrome; an empty input produces `[[]]`.
- Copy the path at completion rather than storing the mutable list.

## Variations

- Find the minimum number of cuts using dynamic programming.
- Return only partitions containing exactly k pieces.
- Count partitions instead of materializing their lists.

=== card | 79
time: 30 min

## The problem

Determine whether a word can be traced through a rectangular character grid by moving one cell up, down, left, or right at a time. A cell cannot be reused within the same trace. For a row `A B A`, the word `"ABA"` exists, but `"ABAB"` does not: it would require revisiting a cell.

## Constraints and what they imply

The original board is at most 6 by 6 and the word has at most 15 characters. The same cell may participate in different attempted paths; only reuse within a single path is forbidden. A word longer than the number of cells is impossible. The implementation does not modify the board and defines the empty word as found, even on an empty board.

## Brute force

Generate all sequences of adjacent grid positions of the requested length from every starting cell, then discard paths with repeated cells or mismatched letters. A naive enumeration branches up to four ways at each move, taking O(mn 4^L) time for an L-character word. It spends effort extending a path even after an early mismatch.

## The insight

Match the next character immediately, and use a path-local set of coordinates. When a matching cell is chosen, add it before exploring neighbours and remove it before returning, whether a continuation succeeds or fails. This restores the state for sibling attempts and for different starts.

The recursive invariant is that the set contains exactly the cells used by earlier characters of the current attempt. Each accepted next cell is adjacent, matches the next character, and is absent from that set. Therefore a successful full match is valid. Conversely, every valid trace starts somewhere in the outer loop, and each of its steps is one of the examined neighbours.

## Optimal solution, traced

```steps
Board [A, B, A], word ABA: start at the left A
---
Mark the left cell; move right to B and mark it
---
The left A is already on the path, but the right A matches
---
Match the last character and return {{true}}; unwind and clear marks
```

## Code

```python
def word_exists(board, word):
    if not word:
        return True
    if not board or not board[0] or len(word) > len(board) * len(board[0]):
        return False
    rows, cols = len(board), len(board[0])
    used = set()

    def visit(r, c, k):
        if (r < 0 or r >= rows or c < 0 or c >= cols or
                (r, c) in used or board[r][c] != word[k]):
            return False
        if k == len(word) - 1:
            return True
        used.add((r, c))
        found = any(visit(r + dr, c + dc, k + 1)
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        used.remove((r, c))
        return found

    return any(visit(r, c, 0) for r in range(rows) for c in range(cols))
```

## Complexity

For L at least one, there are mn starts, at most four first moves and at most three later moves because the immediate predecessor is already used. Time is O(mn 3^L), including constant factors. The set and stack take O(min(L, mn)) space. The input board is unchanged.

## Mistakes and edge cases

- A global permanent visited set wrongly prevents other candidate paths.
- Restore a chosen cell on both successful and unsuccessful returns.
- Diagonal neighbours do not count, and a cell cannot match two positions.
- Empty word is accepted here; rectangular nonempty rows are assumed otherwise.

## Variations

- Find all dictionary words using a trie to share prefix searches.
- Reject impossible letter frequencies before starting DFS.
- Return one coordinate path rather than only a Boolean.

=== card | 698
time: 35 min

## The problem

Decide whether a list of positive integers can be divided into exactly k nonempty groups having equal sums. Every input occurrence must be assigned to one group. For `[2, 1, 4, 5, 6]` with k equal to 3, the groups `[6]`, `[5, 1]`, and `[4, 2]` all total 6, so the answer is true.

## Constraints and what they imply

The original task has at most 16 numbers, positive values, and `1 <= k <= n`. Thus if a solution exists, every group sum must be `sum(nums) / k`. A nonintegral target immediately rules it out. A number larger than the target also makes a solution impossible: positive values cannot cancel it. The small n permits exponential search, but the group labels are arbitrary and create many equivalent assignments.

## Brute force

Assign each of n occurrences independently to one of k labelled groups and test all group sums at the leaves. There are `k^n` assignments, with O(n + k) working space for recursion and sums. Many assignments differ only by a permutation of group labels, and others already exceed the required sum long before the leaf.

## The insight

Sort the values descending so large, restrictive choices are made first. Maintain k running group sums. For each value, try only groups that remain at most the target, and skip any group whose current sum was already tried at this level. Groups with equal sums are interchangeable for all future additions, even when their earlier members differ: the only relevant state for feasibility is remaining capacity.

Every explored placement preserves the target upper bound. At a leaf, all numbers are assigned, and the k sums add to `k * target`; since none exceeds target, all must equal it. Because the target is positive, these groups are nonempty. For completeness, any omitted equal-sum placement is equivalent to a tried one after swapping group labels; capacity pruning cannot reject a valid solution.

## Optimal solution, traced

```steps
Values [6, 5, 4, 2, 1], k = 3; total 18 gives target 6
---
Place 6, 5, 4 in different groups: sums [6, 5, 4]
---
Place 2 in the third group, then 1 in the second: [6, 6, 6]
---
Every value is used, so return {{true}}
```

## Code

```python
def partition_equal_groups(nums, k):
    if not 1 <= k <= len(nums):
        return False
    total = sum(nums)
    if total % k:
        return False
    target = total // k
    values = sorted(nums, reverse=True)
    if values[0] > target:
        return False
    groups = [0] * k

    def visit(i):
        if i == len(values):
            return True
        tried = set()
        for j in range(k):
            if groups[j] in tried or groups[j] + values[i] > target:
                continue
            tried.add(groups[j])
            groups[j] += values[i]
            if visit(i + 1):
                return True
            groups[j] -= values[i]
        return False

    return visit(0)
```

## Complexity

Before pruning, there are O(k^n) assignments for k at least two; sorting costs O(n log n). For k equal to one, the traversal costs O(n). Space is O(n + k) for the sorted copy, group sums and recursion, plus at most O(nk) in the worst case for the per-level `tried` sets retained on the stack. Symmetry and capacity pruning improve practice, not the exponential worst case.

## Mistakes and edge cases

- The equal-sum proof relies on positive inputs and a positive target; zeros require extra care about empty groups.
- Restore a bucket when a branch fails, and skip equal current sums only within the same level.
- Require all occurrences to be used, not merely k target-sum groups that leave leftovers.
- Reject invalid k before accessing the largest value.

## Variations

- Use bitmask dynamic programming for O(n 2^n) time.
- Return the groups themselves by storing group memberships.
- Minimize the maximum group sum when exact equality is not required.

=== card | 51
time: 45 min

## The problem

List every arrangement of n queens on an n by n chessboard such that no two attack one another. A queen attacks along its row, column, and both diagonal directions. Represent an arrangement as n strings containing one `Q` and dots elsewhere. For n equal to 4, two arrangements exist; the order of the arrangements is not important.

## Constraints and what they imply

The original task limits n to nine. Since there are n queens and no row may contain two, every valid arrangement must contain exactly one queen per row. We can make that constraint automatic by placing rows in order. Likewise, a column can contain at most one queen, so the choice of columns is a permutation filtered by diagonal conflicts. The function also defines the empty board as one empty arrangement.

The diagonals have simple coordinates. Cells on one diagonal share `row - column`; cells on the other share `row + column`. Each key can be stored in a set. Testing three sets is constant time under the usual hash-table model.

## Brute force

Select n cells from the `n²` board positions, and for each selection compare all pairs of queens for a shared row, column, or diagonal. This considers `binom(n², n)` candidate sets and spends O(n²) per pairwise check, before constructing results. Most candidates already violate the row constraint. Even trying n arbitrary columns in every row without checking conflicts until the end considers `n^n` sequences.

## The insight

Place exactly one queen in the next row. Maintain the occupied columns, difference diagonals, and sum diagonals for the current partial placement. A candidate column is safe exactly when all three corresponding keys are absent. Add the keys and the column, explore the next row, then remove them to restore the parent state.

At a completed placement, every row has one queen and all three sets ensure that no pair shares a column or diagonal. Thus every output is valid. For the other direction, a valid arrangement has a definite queen column in each row; at every depth that choice is not forbidden by earlier queens, so the recursion reaches it. Each row's column sequence is unique, so there are no duplicate boards.

The placement list stores only column indices while searching. Full strings are created at a leaf, avoiding a mutable two-dimensional board in each recursive state. This also separates auxiliary search space from the potentially much larger returned collection.

For example, after putting a queen at `(0, 1)`, a candidate at `(2, 3)` has the same difference key and is rejected even though it has a different row and column. The set test captures that long diagonal attack without scanning either square's intervening cells.

## Optimal solution, traced

```steps
n = 4; place row 0 at column 1, then row 1 at column 3
---
Columns 1 and 3 and their diagonal keys are occupied
---
Row 2 can use column 0; row 3 can then use column 2
---
Columns [1, 3, 0, 2] form {{one valid board}}; undo to explore other choices
```

## Code

```python
def n_queens(n):
    answer, placement = [], []
    columns, down, up = set(), set(), set()

    def visit(row):
        if row == n:
            answer.append(["." * c + "Q" + "." * (n - c - 1)
                           for c in placement])
            return
        for c in range(n):
            if c in columns or row - c in down or row + c in up:
                continue
            columns.add(c)
            down.add(row - c)
            up.add(row + c)
            placement.append(c)
            visit(row + 1)
            placement.pop()
            up.remove(row + c)
            down.remove(row - c)
            columns.remove(c)

    visit(0)
    return answer
```

## Complexity

There are at most `P(n, r)` partial placements at row r, because columns cannot repeat. Each non-leaf call scans n columns, yielding O(n n!) search time as a safe bound. If S solutions exist, building their boards adds O(S n²) time and output space. The sets, placement, and stack use O(n) auxiliary space beyond the output. This distinguishes the search bound from the cost of actually printing boards.

## Mistakes and edge cases

- Two diagonals need two different keys: use both `row - column` and `row + column`.
- Remove exactly the keys added by the current placement after the recursive call.
- Checking only the previous row misses attacks from more distant queens.
- For n equal to 2 or 3 there are no solutions; n equal to 1 has one.
- A solver that finds one board is not sufficient when all arrangements are requested.

## Variations

- Count arrangements without constructing board strings.
- Use bit masks for occupied columns and diagonals.
- Add blocked cells and search only allowed positions.

=== card | 2305
time: 35 min

## The problem

Distribute all bags of cookies among k children. A bag cannot be divided. The unfairness of a distribution is the largest total received by any child; return the smallest possible unfairness. For bags `[8, 5, 4]` and two children, totals 8 and 9 are possible, so the answer is 9.

## Constraints and what they imply

The original input has at most eight bags with positive sizes and between two and n children. Exponential assignment search is therefore feasible. Labels on children do not affect the objective, so two children with equal current totals are equivalent choices for the next bag. A partial maximum can only increase because all remaining bag sizes are positive.

## Brute force

Try each of the k choices independently for each bag, calculate the largest child total at each leaf, and take the minimum. The `k^n` assignments include many relabelings of the same distribution. They also include branches whose current maximum already exceeds the best complete distribution and can no longer improve it.

## The insight

Process larger bags first and maintain current totals plus the best complete maximum seen. Assign the next bag to one representative of each distinct current total. If the new total is at least the incumbent, that branch cannot improve the answer; skip it. The initial incumbent `sum(bags)` is achievable by placing all bags with one child, so pruning at equality is safe even before a leaf has been explored.

For any skipped equal-total child, swapping child labels maps its continuations to those of a tried child with the same objective. For a pruned large total, nonnegative future additions cannot lower that maximum. All potentially better assignments therefore remain reachable. A leaf updates the incumbent to its actual maximum.

## Optimal solution, traced

```steps
Bags [8, 5, 4], two children; initial achievable bound 17
---
Give 8 to the first child and 5 to the second: [8, 5]
---
Give 4 to the second: [8, 9], improving the bound to 9
---
Other branches cannot beat this bound; return {{9}}
```

## Code

```python
def distribute_cookies(bags, k):
    if not bags:
        return 0
    values = sorted(bags, reverse=True)
    totals = [0] * k
    best = sum(values)

    def visit(i):
        nonlocal best
        if i == len(values):
            best = min(best, max(totals))
            return
        tried = set()
        for j in range(k):
            if totals[j] in tried or totals[j] + values[i] >= best:
                continue
            tried.add(totals[j])
            totals[j] += values[i]
            visit(i + 1)
            totals[j] -= values[i]

    visit(0)
    return best
```

## Complexity

For k at least two, the unpruned k-ary tree has O(k^n) nodes and edges, plus O(n log n) sorting time. For k equal to one, the search is O(n). Totals and sorted values use O(k + n); recursion retains a `tried` set at each level, giving O(nk + n) worst-case auxiliary space. The pruning has no guaranteed polynomial bound.

## Mistakes and edge cases

- Initialize the bound to an achievable assignment, not an arbitrary smaller number.
- Equality can be pruned only because an equally good answer is already known.
- Reset the tried totals at each depth and restore the chosen total after recursion.
- Bag sizes must be nonnegative and k positive; the original problem uses positive bags.

## Variations

- Return an actual assignment alongside its unfairness.
- Use subset dynamic programming to minimize the maximum across groups.
- Impose a maximum number of bags per child.

=== card | 37
time: 50 min

## The problem

Fill the empty cells of a 9 by 9 Sudoku board using characters `"1"` through `"9"`. Each row, each column, and each 3 by 3 box must contain every digit exactly once. Existing digits are fixed. The original task guarantees a valid puzzle with exactly one solution; the function below mutates the given board on success and returns a Boolean indicating whether a completion was found.

## Constraints and what they imply

The board has fixed dimensions and uses `"."` for an empty cell. A digit cannot be placed where it already occurs in the corresponding row, column, or box. A valid partial board may still be impossible to complete, so local legality alone is not proof of a solution. The implementation additionally rejects duplicate givens and restores the original board when a valid-looking puzzle has no completion.

Searching arbitrary digits in a fixed cell order can spend substantial time guessing in flexible areas while a nearly forced cell waits elsewhere. Track the digits already used in each unit and choose the empty cell with the fewest legal values at every depth. A cell with zero choices proves that the current branch cannot succeed.

## Brute force

With e empty cells, assign each one any of nine digits, then check all rows, columns, and boxes after filling the board. This examines up to `9^e` complete assignments, with substantial repeated checking. It also explores invalid partial boards long after a conflict has become apparent. Checking constraints immediately is still exponential, but cuts off those impossible branches.

## The insight

Maintain three families of sets: used digits per row, per column, and per box. The box index is `(row // 3) * 3 + column // 3`. For each remaining empty cell, legal digits are those absent from all three sets. Pick a cell with the smallest candidate set, temporarily move it into the current recursion slot, and try its candidates.

Whenever a candidate is placed, update the board and all three sets. If its recursive continuation fails, reverse every update before trying the next candidate. On success leave the board filled; swapping the empty-cell list back is harmless because the board itself is the requested result. If no candidate works, restore the cell ordering and report failure.

The invariant is that all placed digits satisfy the three local constraints, and the sets exactly describe the board. At a leaf no empty cells remain; each unit has nine distinct digits drawn from nine possibilities, so it contains every digit. Conversely, in any valid completion the chosen cell's digit is among its candidates. Trying every candidate therefore cannot discard a valid completion; the most-constrained-first rule only changes the order of search.

## Optimal solution, traced

```steps
A valid partial grid has an empty cell whose row already uses 1 through 8
---
Its column and box also permit 9, so this cell has one candidate
---
Write 9 and add it to the row, column, and box sets
---
If a later cell has no candidates, erase 9 and remove all three marks
---
If every remaining cell is filled, retain the board and return {{true}}
```

## Code

```python
def solve_sudoku(board):
    digits = set("123456789")
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empty = []
    for r in range(9):
        for c in range(9):
            digit = board[r][c]
            box = (r // 3) * 3 + c // 3
            if digit == ".":
                empty.append((r, c))
            elif digit not in digits or digit in rows[r] or digit in cols[c] or digit in boxes[box]:
                return False
            else:
                rows[r].add(digit)
                cols[c].add(digit)
                boxes[box].add(digit)

    def candidates(r, c):
        box = (r // 3) * 3 + c // 3
        return digits - rows[r] - cols[c] - boxes[box]

    def visit(i):
        if i == len(empty):
            return True
        best = min(range(i, len(empty)),
                   key=lambda j: len(candidates(*empty[j])))
        empty[i], empty[best] = empty[best], empty[i]
        r, c = empty[i]
        box = (r // 3) * 3 + c // 3
        for digit in candidates(r, c):
            board[r][c] = digit
            rows[r].add(digit)
            cols[c].add(digit)
            boxes[box].add(digit)
            if visit(i + 1):
                empty[i], empty[best] = empty[best], empty[i]
                return True
            boxes[box].remove(digit)
            cols[c].remove(digit)
            rows[r].remove(digit)
            board[r][c] = "."
        empty[i], empty[best] = empty[best], empty[i]
        return False

    return visit(0)
```

## Complexity

With e initially empty cells, a conservative upper bound is O(e² 9^e) time: there are at most `9^e` search leaves and each node may scan up to e remaining cells for candidates. For this fixed 9 by 9 board, each candidate computation examines at most nine digits. Space is O(e + 81) for the empty list, recursion, and constraint sets, excluding the input board. Most-constrained-first is a heuristic, not a polynomial-time guarantee.

## Mistakes and edge cases

- Recompute the best cell after each placement; candidate counts change as constraints change.
- A zero-candidate cell must cause backtracking, not an attempted arbitrary digit.
- Restore the board and all three sets after every failed choice; a successful path intentionally stays filled.
- Check the initial givens for conflicts before searching. A completed valid board succeeds without mutation.
- The code expects exactly nine mutable rows of nine valid characters; uniqueness is not needed to find one completion.

## Variations

- Count solutions, continuing after a leaf instead of stopping at the first one.
- Encode digit sets as nine-bit masks and use bit operations for candidates.
- Propagate all single-candidate cells before making a branching guess.
