=== card | 64

## The problem

Given a rectangular grid of nonnegative costs, start in its upper-left cell and reach its lower-right cell. Each move goes either right or down. Return the smallest possible sum of the costs of all visited cells, including both endpoints. A one-cell grid therefore returns that cell's cost. For example, on `[[1, 3], [2, 1]]`, the best path costs 1 + 2 + 1 = 4.

## Constraints and what they imply

The grid has 1 to 200 rows and 1 to 200 columns, and cell costs are integers from 0 to 200. It is not empty or ragged. There can be exponentially many routes, but only one subproblem per cell. A row-sized array is enough because moving down never needs information from an earlier row once that row has been consumed.

## Brute force

Enumerate every legal sequence of right and down moves, sum its visited cells, and take the minimum. There are binomially many paths, up to exponential in the combined dimensions, even though many paths finish with the same suffix. Repeatedly computing the best continuation from a cell wastes work for the same reason.

## The insight

Let the value for a cell be the minimum cost of a path ending there. Its final move must come from the cell above or the cell to its left. Removing that last cell leaves an optimal path to one of those predecessors: a cheaper prefix would improve the whole path. Conversely, extending either valid predecessor gives a legal path. Taking their minimum and adding the cell's cost is therefore exact.

During a left-to-right scan, `dp[c]` still holds the previous row's answer, while `dp[c-1]` already holds this row's answer. Infinity represents a nonexistent predecessor; a single zero immediately above the starting cell seeds the first value. The input itself is not changed.

## Optimal solution, traced

For `[[1, 3], [2, 1]]`, use a leading boundary slot:

```steps
Initial state
dp = [infinity, 0, infinity]
---
First row
The two cells produce dp = [infinity, 1, 4].
---
Second row
The left cell becomes 3; the final cell becomes min(4, 3) + 1 = 4.
```

The boundary slot stays infinite, so neither the top nor left edge can invent a free entry into the grid.

## Code

```python
def min_path_sum(grid):
    cols = len(grid[0])
    dp = [float("inf")] * (cols + 1)
    dp[1] = 0
    for row in grid:
        for c, value in enumerate(row, 1):
            dp[c] = min(dp[c], dp[c - 1]) + value
    return dp[cols]
```

## Complexity

For m rows and n columns, the loop visits each cell once: O(mn) time and O(n) auxiliary space. The values in the rolling row are integer sums after their cells are reached. The sentinel does not affect a reachable answer.

## Mistakes and edge cases

Do not initialize every boundary to zero: that permits a path to start partway through an edge. Count the starting cost, even when it is zero, and include the destination. Single-row and single-column inputs have only one route. Returning the last entry rather than the minimum of the row is essential because the destination is fixed.

## Variations

- Store predecessor choices to recover one minimum-cost route.
- Add blocked cells by leaving their state at infinity and detect an unreachable destination.

=== card | 221

## The problem

In a rectangular matrix whose entries are the characters `"0"` and `"1"`, find the largest square containing only ones and return its area, not its side length. For example, `[[ "1", "1" ], [ "1", "1" ]]` has answer 4. A matrix with no ones has answer 0, and a single one yields 1.

## Constraints and what they imply

There are 1 to 300 rows and columns. Entries are character digits rather than integers. Checking all possible squares individually repeats many inspections, whereas a state for every bottom-right corner suffices. Since a square's state depends only on the previous row and the current row, one row plus a saved diagonal is enough.

## Brute force

Try every top-left corner and every side length fitting inside the matrix. Inspect the cells of each candidate and retain the largest all-one square. With m rows, n columns, and k = min(m, n), this direct method takes O(mn k³) time in the worst case: O(k) side choices, each inspecting up to O(k²) cells. It uses constant extra space.

## The insight

Let the state at a cell be the largest side of an all-one square ending at that cell. A zero forces side zero. For a one, any larger square needs a square of side one less above, left, and diagonally above-left. Thus the smallest of those three sides limits the extension. Conversely, those three squares together cover the desired larger square except for the current one, so one plus their minimum is achievable. This proves both the upper bound and the construction.

Scan across each row. Before overwriting a column, its entry is the square above; the previous entry is the square to the left. Preserve the old entry in a temporary variable to become the diagonal for the next column. Track the best side anywhere, then square it.

## Optimal solution, traced

For rows `["1", "1"]` and `["1", "1"]`:

```steps
First row
The rolling row after the two cells is [0, 1, 1]; best side is 1.
---
Second row, first cell
The left boundary is 0, so its side remains 1.
---
Second row, second cell
Above, left, and diagonal are each 1, so the new side is 2 and area is 4.
```

The leading zero is a permanent boundary, and the diagonal is saved before its original column is overwritten.

## Code

```python
def maximal_square(matrix):
    dp = [0] * (len(matrix[0]) + 1)
    best = 0
    for row in matrix:
        diagonal = 0
        for c, cell in enumerate(row, 1):
            above = dp[c]
            if cell == "1":
                dp[c] = 1 + min(above, dp[c - 1], diagonal)
                best = max(best, dp[c])
            else:
                dp[c] = 0
            diagonal = above
    return best * best
```

## Complexity

For an m by n matrix, each entry is processed in O(1), so time is O(mn). The rolling row occupies O(n) auxiliary space. Neither the matrix nor its rows are modified.

## Mistakes and edge cases

The return value is area, not side. Do not retain a previous-row value at a zero; it would allow a square to cross a hole. Update the diagonal after using the old value, and reset it at each row boundary. Testing a character digit as a Boolean is wrong because `"0"` is also truthy in Python.

## Variations

- Return a corner of one maximum square by remembering where the best side was found.
- Count all-one squares by summing the state for every bottom-right corner.

=== card | 1143

## The problem

Given two strings, return the length of their longest common subsequence. A subsequence keeps characters in their original order but may skip any number of positions; the chosen positions need not be adjacent. For `"abc"` and `"ac"`, the answer is 2, using `"ac"`. This function also accepts an empty string, producing zero.

## Constraints and what they imply

The usual inputs contain up to 1,000 lowercase letters per string. The implementation also handles empty strings. Repeated characters matter: a matching character occurrence may be used at most once in each string. A prefix-pair state uses O(mn) work, which is feasible at these bounds, and a rolling row suffices when only the length is requested.

## Brute force

Enumerate all subsequences of one input by choosing or skipping each position. For each candidate, scan the other input to see whether it occurs in order; retain the maximum length. This takes O(2^m(m+n)) time in a direct implementation and can generate identical candidate strings from different positions. A set can deduplicate values but does not eliminate the exponential worst case.

## The insight

For prefixes of lengths i and j, consider their last characters. If they agree, some optimum can end with that common character: any optimum not using both last occurrences can be extended or adjusted to use them without shortening it. Removing those two last positions then leaves an optimal common subsequence of the shorter prefixes, so the length increases by one.

If the last characters differ, they cannot both be the last matched pair. Every common subsequence omits at least one of them, so the answer is the larger of the two states obtained by dropping one end. Empty prefixes have answer zero. Induction over prefix lengths establishes the recurrence.

In the rolling row, save the old diagonal before replacing a value; the old current entry is above and the already updated previous entry is left. Put the shorter string on the column axis to minimize storage.

## Optimal solution, traced

For `"ab"` and `"ac"`:

```steps
Empty prefixes
Start with row [0, 0, 0].
---
Read a
The matching a gives 1; the following c carries that 1 leftward.
---
Read b
Neither character matches b, so the final row remains [0, 1, 1] and the answer is 1.
```

The saved diagonal refers to both prefixes before the current characters, not the just-updated left cell.

## Code

```python
def lcs_length(a, b):
    if len(b) > len(a):
        a, b = b, a
    dp = [0] * (len(b) + 1)
    for x in a:
        diagonal = 0
        for j, y in enumerate(b, 1):
            above = dp[j]
            if x == y:
                dp[j] = diagonal + 1
            else:
                dp[j] = max(above, dp[j - 1])
            diagonal = above
    return dp[-1]
```

## Complexity

For lengths m and n, time is O((m+1)(n+1)), or O(mn) when both are nonempty, and auxiliary space is O(min(m, n)+1). Swapping the inputs does not change the answer. The method returns a length only; it does not retain the choices required to reconstruct a subsequence.

## Mistakes and edge cases

Substring matching is different: skipped positions are allowed here. A greedy earliest match can lose a longer later alignment. An empty input returns zero; repeated characters cannot be matched twice to the same position. When a pair differs, taking only the diagonal discards valid solutions that skip one end.

## Variations

- Keep the full table and walk backwards to produce one common subsequence.
- Apply the same prefix recurrence to sequences of tokens or lines rather than characters.

=== card | 72

## The problem

Find the minimum number of single-character edits needed to turn a source string into a target string. One edit inserts a character, deletes a character, or replaces one character with another; each costs one. Matching characters cost nothing. For `"cat"` to `"cut"`, replace the middle character, so the answer is 1. Either input may be empty.

## Constraints and what they imply

Each word has length at most 500 and consists of lowercase letters; an empty word is allowed. Only the distance is requested, not the actual edit sequence. There are at most about a quarter million pairs of nonempty prefixes, so the prefix table is practical. A rolling row reduces storage without changing the recurrence.

## Brute force

Recursively consider every possible final alignment decision: delete a source character, insert a target character, or align the two final characters with a possible replacement. Continue until a prefix is empty. This explores an exponential number of decision paths in the worst case and repeatedly recomputes the distance for the same pair of prefixes. It is a useful conceptual oracle for very short words, not for the largest input.

## The insight

Let the state be the edit distance between two prefixes. The last alignment column must either pair their final characters, consume only a source character, or consume only a target character. Those cases cost respectively zero or one for the pair, one deletion, or one insertion, plus the optimal distance for the remaining prefixes. Every edit alignment has one of these last columns, and appending the corresponding operation to an optimal smaller alignment is feasible. Taking the minimum proves the answer.

An empty source needs one insertion per target character, and an empty target needs one deletion per source character. We retain all three possibilities even when the last letters agree; a zero-cost diagonal is always available. In one row, save the old diagonal, use the old column for deletion, and use the new left neighbor for insertion.

## Optimal solution, traced

Transform `"ab"` into `"ac"`:

```steps
Empty source
The initial row is [0, 1, 2], the cost of inserting each target prefix.
---
Source prefix a
Matching a yields 0, and inserting c gives 1: row [1, 0, 1].
---
Source prefix ab
Replacing b with c gives 1, so the final row is [2, 1, 1].
```

The final entry represents the complete source and target, rather than a best match against an arbitrary prefix.

## Code

```python
def edit_distance(source, target):
    dp = list(range(len(target) + 1))
    for i, x in enumerate(source, 1):
        diagonal = dp[0]
        dp[0] = i
        for j, y in enumerate(target, 1):
            above = dp[j]
            dp[j] = min(above + 1, dp[j - 1] + 1,
                        diagonal + (x != y))
            diagonal = above
    return dp[-1]
```

## Complexity

For source length m and target length n, the code performs O(mn) updates and uses O(n) auxiliary space. Initializing the first row costs O(n), and processing empty rows costs O(m), so a bound covering empty strings is O((m+1)(n+1)). The input strings are unchanged.

## Mistakes and edge cases

Replacement costs one, not a deletion plus an insertion. The boundary row is not all zero: converting from an empty word requires insertions. Identical strings have distance zero. When overwriting the row, advancing the diagonal too early confuses the old and new states. One row alone cannot directly reconstruct the operations.

## Variations

- Store the full table and backtrack to show an optimal edit script.
- Assign different nonnegative costs to insertion, deletion, and replacement and adjust the recurrence.

=== card | 97

## The problem

Given strings `a`, `b`, and `merged`, decide whether `merged` can be formed by taking every character from `a` and `b` exactly once while preserving the order within each source. Characters from the sources may alternate arbitrarily. For example, `"ab"` and `"cd"` can produce `"acbd"`, but cannot produce `"bacd"` because the order in the first source is reversed.

## Constraints and what they imply

Each source has length at most 100; the merged string has length at most 200, and empty strings are allowed. The strings contain lowercase letters. Its length must equal the sum of the source lengths. Equal letters may make both sources plausible at the same moment, so a greedy commitment to one source can discard a valid interleaving.

## Brute force

At each merged position, branch on taking the next unused character of either source whenever it matches. Accept if a branch consumes both sources and the entire merged string. The number of source-choice sequences can be binomial, and thus exponential in the total length. Many branches reach the same pair of source positions, so they share the same remaining question.

## The insight

For prefix lengths i and j, the consumed merged prefix has length i+j. This pair of positions completely describes the remaining possibilities; the exact history of how the prefix was assembled is irrelevant. The state is reachable if the last character came from a reachable state with one fewer character of `a`, or from one with one fewer character of `b`, and that source character matches the corresponding merged character.

The empty pair is reachable. These two alternatives cover every possible last choice, and either true alternative builds a legal prefix, proving the recurrence by induction. A one-row scan keeps the previous row's state above and the current row's state to the left. The length check prevents indexing the merged string outside its range and also rules out unused suffixes.

## Optimal solution, traced

For `a = "ab"`, `b = "cd"`, and `merged = "acbd"`:

```steps
Start
Only state (0, 0) is reachable before reading any characters.
---
Build the prefix acb
Take a from the first source, c from the second, then b from the first; state (2, 1) is reachable.
---
Finish
Take d from the second source, reaching (2, 2), so return True.
```

Different choices that reach the same state are merged into one Boolean; no particular source-choice path has to be retained.

## Code

```python
def is_interleave(a, b, merged):
    if len(a) + len(b) != len(merged):
        return False
    dp = [False] * (len(b) + 1)
    dp[0] = True
    for i in range(len(a) + 1):
        for j in range(len(b) + 1):
            if i == 0 and j == 0:
                continue
            k = i + j - 1
            from_a = i > 0 and dp[j] and a[i - 1] == merged[k]
            from_b = j > 0 and dp[j - 1] and b[j - 1] == merged[k]
            dp[j] = from_a or from_b
    return dp[-1]
```

## Complexity

For source lengths m and n, the scan uses O((m+1)(n+1)) time and O(n) auxiliary space. This bound includes empty-source boundary cases. The strings are not modified; using the shorter source as the column dimension would reduce the space further.

## Mistakes and edge cases

Checking character counts is necessary but not sufficient: order also matters. If both next characters match, do not irrevocably select just one. Three empty strings are a valid interleaving, but an extra target character makes the length check fail. Do not read the target at index i+j before subtracting one for the final consumed character.

## Variations

- Count source-choice interleavings rather than only testing existence.
- Retain predecessor choices and reconstruct which source supplied each character.

=== card | 516

## The problem

Return the length of the longest palindromic subsequence of a string: choose positions in order so that the resulting characters read the same in both directions. Skipping positions is allowed. For `"bbab"`, choosing three b characters gives length 3. This implementation also defines the answer for the empty string as 0.

## Constraints and what they imply

The input has at most 1,000 lowercase letters; the usual problem supplies at least one, but accepting empty input is harmless. There can be exponentially many subsequences, so do not build them all. A state for each interval takes quadratic time, and retaining one rolling row is enough when the result is only a length.

## Brute force

Choose or skip each position, test whether the resulting sequence is a palindrome, and retain the greatest length. Testing a candidate costs O(n), so the direct algorithm takes O(n 2^n) time and O(n) working space for a candidate. Repeated letters can yield the same text through different position choices, but enumerating position subsets still explores all of them.

## The insight

Let the state for an interval be its longest palindromic subsequence length. If the ends agree, there exists an optimum using both: if an optimum omits either end, its matching outer pair can be replaced by the two interval ends without shortening it; if it has length at most one, the equal ends already form a pair. Removing those ends leaves an optimal palindrome inside. Therefore the answer is two plus the inside state.

If the ends differ, no palindrome can use both as its outermost selected characters, so an optimum excludes at least one and is the maximum of the two shorter intervals. Empty intervals contribute zero and single characters contribute one. Fill starting positions from right to left and ending positions from left to right. In the rolling row the old column is the interval below, the updated left neighbor is the interval to the left, and a saved old value is the inner interval.

## Optimal solution, traced

For `"aba"`:

```steps
Single characters
Every length-one interval has value 1.
---
Length two
Intervals "ab" and "ba" each have unequal ends and value 1.
---
Whole interval
The ends match, so add 2 to the inner "b" value 1 and return 3.
```

The scan constructs these intervals in dependency order even though it stores only a single row.

## Code

```python
def longest_palindromic_subsequence(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [0] * n
    for i in range(n - 1, -1, -1):
        dp[i] = 1
        diagonal = 0
        for j in range(i + 1, n):
            below = dp[j]
            if s[i] == s[j]:
                dp[j] = diagonal + 2
            else:
                dp[j] = max(dp[j], dp[j - 1])
            diagonal = below
    return dp[-1]
```

## Complexity

There are O(n²) interval updates, each constant time, and O(n) auxiliary space for the row. The string is not modified. To recover an actual subsequence, store enough interval decisions or recompute them; the compressed row reports only the length.

## Mistakes and edge cases

A palindromic substring must be contiguous, but a subsequence need not be. Two equal endpoints surrounding an empty interval give length two, not three. Reset the saved diagonal for each new starting position. A single character returns one, and an empty string returns zero rather than indexing an empty array.

## Variations

- Store a full interval table and reconstruct one longest palindromic subsequence.
- Compute the minimum insertions needed to make the entire string a palindrome as n minus this length.

=== card | 416

## The problem

Decide whether the elements of a list can be divided into two groups with equal sums. Every position belongs to exactly one group, so duplicate values are distinct available items, not unlimited copies. For `[1, 5, 11, 5]`, one group can contain 11 and the other the remaining numbers, so the answer is true.

## Constraints and what they imply

The standard input has 1 to 200 positive integers, each at most 100. Consequently the sum is at most 20,000, so a Boolean table indexed by half the sum is practical. The implementation also returns true for an empty list: two empty groups have equal sum. It assumes nonnegative integers and does not support negative values.

## Brute force

For each element decide whether it goes into the first group; all remaining positions form the second group. Sum each selection and compare it with half the total. There are 2^n assignments, taking O(n 2^n) time if each subset sum is recomputed directly. Duplicates still represent different choices of positions, although existence only needs one successful assignment.

## The insight

If the total is odd, equal integer group sums are impossible. Otherwise, a subset with sum total/2 is both necessary and sufficient: place that subset in one group and its complement in the other. The problem becomes 0/1 subset sum.

Let `dp[c]` indicate whether processed positions contain a subset summing to c. The empty subset reaches zero initially. On receiving x, each sum c is reachable either without x, as before, or with x if c-x was reachable before processing x. Scan c downwards so `dp[c-x]` still refers to the previous set of items. An upward scan would allow the current item to feed another update and be used more than once. Induction over the processed items proves the table exactly represents all possible subsets.

## Optimal solution, traced

For `[1, 2, 3]`, the target is 3:

```steps
Initial state
Only sum 0 is reachable.
---
Process 1 and 2
After 1, sums 0 and 1 are reachable; after 2, sums 0, 1, 2, and 3 are reachable.
---
Finish
Sum 3 is reachable, so its complement also sums to 3 and the result is True.
```

The descending updates ensure the single 2 is not used to make 4 or any other sum twice in the same pass.

## Code

```python
def can_partition(nums):
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for x in nums:
        for c in range(target, x - 1, -1):
            dp[c] = dp[c] or dp[c - x]
    return dp[target]
```

## Complexity

If n is the item count and S is half the total, time is O(n(S+1)) and auxiliary space is O(S+1). The bound is pseudo-polynomial: it depends on the numeric sum, not just the number of bits needed to represent the numbers. The list is unchanged.

## Mistakes and edge cases

An even total alone does not guarantee a partition. Do not use an ascending capacity loop for single-use elements. A number larger than the target cannot be included in the chosen subset, but the code safely skips its updates. Zeros, if supplied, do not affect existence; negative values violate the indexing model.

## Variations

- Store predecessor choices to recover one subset and its complement.
- Use a bitset of reachable sums when only existence is required.

=== card | 494

## The problem

Assign either a plus or a minus sign to each position of a nonnegative integer list. Return the number of sign assignments whose signed sum equals `target`. Positions are distinct even if their values match. For `[1, 1]` and target 0, the assignments `+1 -1` and `-1 +1` are two different answers.

## Constraints and what they imply

There are 1 to 20 numbers, each between 0 and 1,000, with total at most 1,000; the target lies between -1,000 and 1,000. Zeros are important: choosing plus zero and minus zero yields the same numeric sum but counts as two assignments. The code also accepts an empty list, for which there is one assignment to target zero.

## Brute force

Try all 2^n sign vectors and add their signed values. Counting those equal to the target takes O(n 2^n) time when every sum is computed from scratch. A recursive enumeration can carry a running sum with O(n) stack space. It distinguishes equal values by position and counts both choices for every zero.

## The insight

Write P for the sum of plus-signed positions and N for the sum of minus-signed positions. Then P+N equals the total and P-N equals the target, so P must equal `(total + target)/2`. If the target's magnitude exceeds the total or that numerator is odd, there are no assignments. Otherwise, choosing the plus positions is a bijection between valid assignments and subsets summing to P.

Count these subsets with a one-dimensional 0/1 knapsack table. Start with one way to choose the empty subset at sum zero. For each value x, add the old count at c-x into the count at c, scanning downward so the same position is not reused. When x is zero, every cell doubles once, correctly recording both sign choices. The induction partitions subsets according to whether the current position is included.

## Optimal solution, traced

For `[0, 1]` and target 1:

```steps
Translate the target
Total is 1, so the required plus-group sum is (1 + 1) / 2 = 1.
---
Process zero
The count for sum 0 doubles from 1 to 2, representing both signs for zero.
---
Process one
The two zero-sum choices extend to sum 1, so the answer is 2.
```

The complement of each selected plus subset is exactly the minus subset, including its zero positions.

## Code

```python
def target_sum_ways(nums, target):
    total = sum(nums)
    if abs(target) > total or (total + target) % 2:
        return 0
    goal = (total + target) // 2
    ways = [0] * (goal + 1)
    ways[0] = 1
    for x in nums:
        for c in range(goal, x - 1, -1):
            ways[c] += ways[c - x]
    return ways[goal]
```

## Complexity

With n items and transformed goal S, there are O(n(S+1)) updates and O(S+1) auxiliary space. This is pseudo-polynomial in the numeric goal. Python integers grow with the number of assignments, so arithmetic on exceptionally large counts is not strictly constant cost.

## Mistakes and edge cases

Do not treat zeros as irrelevant; each contributes a factor of two. Negative targets are valid as long as their magnitude and parity permit a solution. Test parity before dividing. Looping upward would let a positive item appear repeatedly. The formula assumes nonnegative input values; arbitrary signed inputs need a different state model.

## Variations

- Use a map from signed sums to counts when the sum range is sparse.
- Return one sign assignment by retaining a reachable predecessor for each item and sum.

=== card | 322

## The problem

Given distinct positive coin denominations and a nonnegative amount, return the fewest coins whose values sum exactly to that amount. Each denomination is available without limit. Return -1 if no exact sum is possible. For coins `[1, 3, 4]` and amount 6, two coins of value 3 give the answer 2.

## Constraints and what they imply

There are 1 to 12 denominations, each from 1 to 2³¹-1, and the amount is at most 10,000. A coin can exceed the requested amount; it simply cannot participate. The positive-denomination assumption ensures every transition moves to a strictly smaller amount, so the state graph is acyclic.

## Brute force

Explore all sequences of coins whose running sum does not exceed the amount, and retain the shortest sequence reaching it. The recursion depth can reach the amount when a value-one coin is available; branching on each denomination makes the worst-case search exponential. Different sequences can reach the same remaining amount, so the minimum continuation is repeatedly recomputed.

## The insight

For any positive reachable amount, an optimal solution has some final coin. Removing that coin leaves a solution for the smaller amount with one fewer coin. If that remainder could use fewer coins, substituting it would improve the original solution. Conversely, appending a coin to any reachable remainder creates a valid solution. Therefore the minimum over all possible last coins gives the optimum.

Set the zero amount to zero coins and every other state to infinity. Process amounts in increasing order; each positive coin refers only to an earlier amount, allowing the same denomination to occur repeatedly. If all predecessor states are unreachable, the current one stays infinite. The final infinity is converted to the requested sentinel -1.

## Optimal solution, traced

For coins `[1, 3, 4]` and amount 6:

```steps
Initial state
need[0] = 0 and all positive amounts start unreachable.
---
Build smaller amounts
Amounts 1, 2, 3, and 4 need respectively 1, 2, 1, and 1 coins.
---
Reach six
The last coin 3 extends need[3] = 1 to give 2 coins; no option is better.
```

The state records a minimum count, not the number of ways to reach an amount.

## Code

```python
def min_coins(coins, amount):
    need = [float("inf")] * (amount + 1)
    need[0] = 0
    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value:
                need[value] = min(need[value], need[value - coin] + 1)
    return -1 if need[amount] == float("inf") else need[amount]
```

## Complexity

For k denominations and amount A, time is O(kA + A + 1) and auxiliary space is O(A+1). The dependence on A is pseudo-polynomial. No coin list is sorted or modified, and the count does not depend on the input order.

## Mistakes and edge cases

Using zero for an unreachable amount would incorrectly beat every real count. The answer for amount zero is zero even if no coins are needed. A greedy choice of the largest available denomination can fail, as in the trace. Do not use the 0/1 downward update intended for one copy of each coin; here supply is unlimited.

## Variations

- Record the final coin chosen at each amount to reconstruct a minimum-size combination.
- Limit the number of copies of each denomination and use a bounded-knapsack state.

=== card | 518

## The problem

Count the combinations of unlimited coins that sum to a given amount. A combination is determined by how many of each denomination it uses, so reordering its coins does not create another answer. For coins `[1, 2]` and amount 4, the combinations are four ones, two ones and one two, or two twos: the answer is 3.

## Constraints and what they imply

The amount is between 0 and 5,000; there are 1 to 300 distinct positive denominations, each at most 5,000. The original task guarantees its answer fits a signed 32-bit integer, though Python can represent larger counts. Amount zero has exactly one combination: choose no coins. Treating equal denominations as separate types would instead count duplicate representations, so distinctness is part of the contract.

## Brute force

For each denomination, choose a copy count from zero up to the amount divided by its value, then recursively choose counts for later denominations. Count a choice vector only if its total is exactly the amount. This can enumerate exponentially many combinations of count choices, and repeatedly asks for the same remaining amount using the same suffix of coin types.

## The insight

After processing some denominations, let `ways[a]` count combinations using only those types to make a. The empty combination gives `ways[0] = 1`. When introducing a coin c, every new combination either uses no c, already counted at a, or uses at least one c. Removing one c gives a unique combination of amount a-c that may still use c. Thus add the current value at a-c to the old value at a.

Visit amounts in increasing order within each coin pass, so a-c already includes combinations with additional copies of c. Put coin types in the outer loop: each multiset is introduced in a fixed type order and counted once. Reversing the loops instead counts ordered sequences of choices. The two cases and the remove-one-coin mapping establish the invariant by induction.

## Optimal solution, traced

For amount 4 and coins `[1, 2]`:

```steps
Empty set of types
ways = [1, 0, 0, 0, 0].
---
Introduce 1
Each amount has one all-ones combination, so ways = [1, 1, 1, 1, 1].
---
Introduce 2
Update amounts 2, 3, 4 in order; ways becomes [1, 1, 2, 2, 3].
```

The final update can use the newly updated count at amount 2, which represents two copies of coin 2.

## Code

```python
def coin_combinations(amount, coins):
    ways = [0] * (amount + 1)
    ways[0] = 1
    for coin in coins:
        for value in range(coin, amount + 1):
            ways[value] += ways[value - coin]
    return ways[amount]
```

## Complexity

For k denominations and amount A, time is O(k(A+1)) and auxiliary space is O(A+1), counting arithmetic operations. Very large Python integers make each addition depend on the number of digits. The algorithm is pseudo-polynomial in A and leaves the inputs unchanged.

## Mistakes and edge cases

Amount zero returns one, not zero. A denomination greater than the amount contributes no updates. An ascending amount loop is intentional because supply is unlimited; descending would use each coin at most once. Do not move the amount loop outside if order should not matter. Zero-valued denominations invalidate the finite-combination model.

## Variations

- Count ordered sequences by making the amount the outer loop.
- Limit each coin type's supply and sum only the permitted copy counts.

=== card | 10

## The problem

Decide whether an entire text matches a simple pattern. A lowercase letter matches itself, a dot matches any one character, and a star means zero or more copies of the single pattern element immediately before it. The match must consume the whole text and the whole pattern. Thus `"aab"` matches `"c*a*b"`: the first starred unit contributes no characters, the second contributes two, and the final literal contributes one.

The dot-star combination can consume any sequence, including an empty one, but an ordinary dot always consumes exactly one character. This is a deliberately small pattern language, not Python's complete regular-expression syntax. There are no groups, anchors, alternation, escapes, or other operators.

## Constraints and what they imply

The standard bounds are text length up to 20 and pattern length up to 20; text contains lowercase letters and the pattern contains lowercase letters, dots, and stars. Every star is guaranteed to follow a letter or dot, and consecutive stars are invalid. This implementation additionally accepts empty text and an empty pattern. Invalid patterns are outside its contract rather than being diagnosed.

Many different repetition choices can lead to the same prefix pair. Even at modest sizes, tracking all choices separately makes the reasoning and running time unnecessarily complicated. A Boolean table for text and pattern prefixes records precisely the information needed for whole-string matching.

## Brute force

Parse the pattern into atoms, each optionally followed by a star. For a plain atom, consume one matching text character. For a starred atom, try every feasible repetition count from zero through the remaining text length, then recurse on the rest of the atoms. A branch succeeds only if both streams end together. The same suffix pair can arise through many choices, so the naive search may take exponential time in the input lengths. Its recursion and candidate counts are still useful as an independent oracle on very short examples.

## The insight

Let `dp[i][j]` mean that the first i text characters match the first j pattern characters. Empty prefixes match each other. A plain final atom consumes exactly one character, so it matches only when the last text character agrees and `dp[i-1][j-1]` is true. The match test allows either an equal literal or a dot.

When the pattern prefix ends in a star, the preceding atom and its star form a unit. A successful match either uses zero copies, reducing the pattern prefix by two, or uses at least one copy. In the latter case the last text character must match the atom; after removing that character, the same starred unit is still available, giving `dp[i-1][j]`. These cases are exhaustive and construct valid matches, so induction on prefix lengths proves the recurrence. In particular, the zero-copy case is what makes patterns such as `"a*b*"` match empty text.

The scan visits pattern prefixes left to right and text prefixes from empty upward. The zero-copy dependency lies earlier in the current row; the one-more-copy dependency lies in the preceding text row. No general regex engine is needed.

## Optimal solution, traced

For text `"aab"` and pattern `"c*a*b"`:

```steps
Empty text
The empty prefix matches c* and then c*a* by taking zero copies of each starred unit.
---
Consume both a characters
The a* unit stays available while each a is consumed, making (text prefix "aa", pattern prefix "c*a*") reachable.
---
Consume b
The final literal b matches the last text character from that reachable state; the whole match is True.
```

If a character did not match the repeated atom, only the zero-copy branch could apply. A success for an intermediate prefix is not enough unless the final table cell is also true.

## Code

```python
def regex_match(text, pattern):
    m, n = len(text), len(pattern)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    for i in range(m + 1):
        for j in range(1, n + 1):
            if pattern[j - 1] == "*":
                atom = pattern[j - 2]
                dp[i][j] = dp[i][j - 2] or (
                    i > 0 and (atom == "." or atom == text[i - 1])
                    and dp[i - 1][j]
                )
            elif i > 0:
                dp[i][j] = (
                    (pattern[j - 1] == "." or pattern[j - 1] == text[i - 1])
                    and dp[i - 1][j - 1]
                )
    return dp[m][n]
```

## Complexity

For text length m and pattern length n, the table uses O((m+1)(n+1)) time and space. This includes the boundary row and column, important when either string is empty. Each state performs constant work. Rolling rows can reduce space to O(n), but the full table makes the dependencies explicit and can support reconstruction.

## Mistakes and edge cases

A star modifies only its immediately preceding atom; it is not an independent wildcard. Dot without star consumes exactly one character. A star must be able to consume zero copies even when the text is already empty. Do not require a substring or prefix match: leftover characters on either side make the answer false. For empty text and empty pattern return true, whereas a nonempty plain pattern cannot match empty text. The code assumes syntactically valid patterns, so callers must validate arbitrary external pattern text separately.

## Variations

- Keep predecessor decisions to recover how many characters each starred atom consumed.
- Add an operator for exactly zero or one occurrence and derive its separate skip-or-consume transition.

=== card | 132

## The problem

Partition a string into nonempty contiguous pieces such that every piece is a palindrome, and return the smallest number of cuts between pieces. A palindrome reads the same in both directions. For `"aab"`, splitting as `"aa" | "b"` needs one cut; splitting into three single characters is valid but uses two. A whole-string palindrome needs no cuts.

The return value counts boundaries, not pieces. This function also defines the empty-string result as zero; the usual problem supplies a nonempty string. A valid partition always exists because every individual character is a palindrome.

## Constraints and what they imply

The input consists of up to 2,000 lowercase letters. At that size, trying all possible cut patterns is impractical, but O(n²) interval and prefix work is reasonable in the intended model. The implementation uses O(n²) Boolean table entries as well, so memory can be significant in Python; storing packed flags or using a center-expansion approach can reduce memory in a constrained environment.

Pieces must be contiguous. A palindrome subsequence that skips positions cannot serve as one piece. The order of the input is fixed, and each cut separates adjacent positions, so no character may be left out or reused.

## Brute force

For each of the n-1 gaps, independently choose whether to cut. Check every resulting piece by comparing it to its reverse, then take the fewest cuts among valid partitions. There are 2^(n-1) cut patterns and O(n) character work per pattern if pieces are checked directly. This gives an independent small-input reference, but it repeats palindrome checks across many partitions.

## The insight

Separate the problem into two questions. First, `pal[i][j]` records whether the inclusive interval from i through j is a palindrome. An interval is palindromic exactly when its endpoints agree and its inside is palindromic, with lengths one and two as base cases. Fill starting indices from right to left, so the inner interval has already been resolved. This table turns each later palindrome check into a constant-time lookup.

Second, let `cuts[k]` be the minimum cuts for the prefix of length k. For a nonempty prefix, consider every starting position j for its last piece. If `s[j:k]` is a palindrome, an optimal partition of the earlier prefix plus that piece uses `cuts[j] + 1` cuts. Set `cuts[0] = -1`: when the entire prefix is the last piece, the formula correctly produces zero cuts rather than one. The special empty-input return remains zero because no actual negative number of cuts is possible.

Every valid partition has some palindromic final piece, so it appears among these candidates. Conversely, adjoining a candidate piece to an optimal earlier partition yields a valid partition. Induction over prefix length therefore proves that taking the minimum finds the optimum. Single-character final pieces guarantee a finite candidate for every nonempty prefix.

## Optimal solution, traced

For `"aab"`:

```steps
Mark palindrome intervals
Each single character is palindromic; the first two characters "aa" also form a palindrome, while "ab" and "aab" do not.
---
Process the first two prefixes
cuts[0] = -1, cuts[1] = 0, and the whole palindrome "aa" gives cuts[2] = 0.
---
Process the full prefix
The last piece "b" extends the first two characters, so cuts[3] = cuts[2] + 1 = 1.
```

The sentinel is only an accounting device for a prefix before the first piece. It never represents a real cut in the returned nonempty partition.

## Code

```python
def min_palindrome_cuts(s):
    n = len(s)
    if n == 0:
        return 0
    pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            pal[i][j] = s[i] == s[j] and (
                j - i < 2 or pal[i + 1][j - 1]
            )
    cuts = [-1] + [n] * n
    for end in range(1, n + 1):
        for start in range(end):
            if pal[start][end - 1]:
                cuts[end] = min(cuts[end], cuts[start] + 1)
    return cuts[n]
```

## Complexity

There are O(n²) interval checks and O(n²) candidate last pieces, for O(n²) time. The palindrome table uses O(n²) auxiliary space and the cuts array adds O(n). Python's table is a list of lists of references, so real memory usage is higher than one bit per interval. No slices are created in the inner loops, and the input string remains unchanged.

## Mistakes and edge cases

Return zero for a single character or an already-palindromic whole string. Do not return the number of pieces: that is one larger than the number of cuts for a nonempty input. The interval table uses inclusive endpoints while `cuts` uses prefix lengths; mixing them causes off-by-one errors. Fill the inner interval first and treat one- and two-character intervals as base cases. Greedily taking the longest palindrome at the front need not minimize the total number of cuts.

## Variations

- Retain the best starting index per prefix and reconstruct an optimal partition.
- Expand around palindrome centers and update prefix cuts in a suitable order to avoid storing the full interval table.
