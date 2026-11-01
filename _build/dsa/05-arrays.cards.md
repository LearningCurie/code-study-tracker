=== card | 566
time: 15 min

## The problem

Repackage a rectangular grid into a requested number of rows and columns, preserving its row-by-row reading order. If the requested shape cannot hold exactly the same number of entries, return the original grid. For example, reshaping `[[1, 2], [3, 4]]` to two rows of two columns changes no values; reshaping it to one row gives `[[1, 2, 3, 4]]`.

## Constraints and what they imply

Assume the input is a nonempty rectangular grid and both requested dimensions are positive. Source dimensions can differ, and cells can contain arbitrary values. A legal reshape needs `rows * cols == m * n`; otherwise it would drop or invent a cell. On failure this implementation returns the original object. On success it creates independent output rows and does not mutate the source.

## Brute force

First copy all values into a flat list, then consume that list into new rows. This is straightforward and takes O(mn) time, but the temporary flat list adds O(mn) storage beyond the output. The mapping below needs only the output and a few indices.

## The insight

Number every cell by its position in row-major order. For a width `n`, index `k` means row `k // n` and column `k % n`. The same `k`, interpreted using the target width, identifies its destination. Both mappings are bijections over the same range, so every input value is copied exactly once to the corresponding output position.

## Optimal solution, traced

```steps
Source [[1, 2, 3], [4, 5, 6]], target 3 x 2: both shapes contain 6 cells.
---
k = 0, 1: source (0,0), (0,1) becomes destination (0,0), (0,1); output starts {{1, 2}}.
---
k = 2, 3: source (0,2), (1,0) becomes destination (1,0), (1,1); second row is {{3, 4}}.
---
k = 4, 5: source (1,1), (1,2) becomes destination (2,0), (2,1); result is [[1, 2], [3, 4], {{5, 6}}].
```

## Code

```python
def reshape(grid, rows, cols):
    m, n = len(grid), len(grid[0])
    if m * n != rows * cols:
        return grid
    out = [[None] * cols for _ in range(rows)]
    for k in range(m * n):
        out[k // cols][k % cols] = grid[k // n][k % n]
    return out
```

## Complexity

There are `m*n` assignments, so time is O(mn). The returned grid occupies O(mn) space; auxiliary space apart from it is O(1). The incompatible-shape case returns immediately in O(1) time and space.

## Mistakes and edge cases

- Use the source width to decode source coordinates and the target width for the destination.
- Construct rows independently: multiplying an outer list aliases rows and corrupts later writes.
- A one-row or one-column shape works without a special traversal. The stated contract excludes an empty or ragged input.

## Variations

- Convert a flat row-major buffer to a grid by applying only the destination mapping.
- For a column-major representation, derive coordinates using the height rather than the width.

=== card | 448
time: 20 min

## The problem

An array of length `n` contains values drawn from `1` through `n`, possibly with repetition. Return all values from that range which do not appear. For `[2, 2, 4, 1]`, the missing values are `[3]`. The returned list is allowed; the working storage beyond it should be constant.

## Constraints and what they imply

Each value has a valid home index `value - 1`. The list may be modified; this implementation restores it before returning, so callers retain its original contents. The sign trick relies on every original value being positive and within range. An empty list naturally returns an empty result.

## Brute force

For each candidate from 1 to n, scan the array for it. This takes O(n²) time and constant working storage. A set makes membership fast in expected O(n) time but needs O(n) extra storage.

## The insight

Use the sign at each home index as a visited bit. For each value `x`, make the value at `abs(x) - 1` negative. The magnitude remains the original value, so later visits can still recover it. At the end, a positive entry at index `i` means nobody visited the home slot of `i + 1`; a negative entry means that value occurred. Negating only positive entries makes repeat visits idempotent.

## Optimal solution, traced

```steps
Start [2, 2, 4, 1]: all home-slot signs are positive.
---
Read 2 then abs(-2) = 2: mark index 1 negative, then leave it negative; array is [2, {{-2}}, 4, 1].
---
Read 4: mark index 3; read abs(-1) = 1 at index 3 and mark index 0. Array is {{[-2, -2, 4, -1]}}.
---
Only index 2 is positive, so output [{{3}}]. Restore all magnitudes to recover [2, 2, 4, 1].
```

## Code

```python
def missing_numbers(a):
    for x in a:
        i = abs(x) - 1
        if a[i] > 0:
            a[i] = -a[i]
    missing = [i + 1 for i, x in enumerate(a) if x > 0]
    for i in range(len(a)):
        a[i] = abs(a[i])
    return missing
```

## Complexity

Three linear passes cost O(n) time. Beyond the returned list, only a few indices are stored, so auxiliary space is O(1). Restoring signs does not require a separate copy.

## Mistakes and edge cases

- Using a signed value directly as an index is wrong after earlier visits have marked it.
- Toggling the sign on every occurrence loses the mark after an even number of visits.
- Duplicates can occur many times; no assumption of a single repeated number is needed.
- Do not use this encoding on zero or negative original values: zero cannot encode a sign bit.

## Variations

- Report repeated visits when an already negative home slot is encountered; specify whether repeated copies are emitted once or multiple times.
- Use cyclic placement if reordering the array is permitted instead of sign changes.

=== card | 645
time: 20 min

## The problem

A length-`n` collection should contain each integer from `1` to `n` once, but one value has been replaced by another value already present. Return `[duplicate, missing]`. For `[1, 3, 3, 4]`, the answer is `[3, 2]`.

## Constraints and what they imply

Assume `n >= 2`, all entries are in `1..n`, and exactly one value appears twice while exactly one is absent. Thus every value has a usable home index, there is exactly one repeated visit, and precisely one slot remains unmarked. This function restores the input after temporarily changing its signs.

## Brute force

For every candidate, count its occurrences with a full scan. A count of two identifies the duplicate and a count of zero identifies the missing value. This needs O(n²) time and O(1) workspace; a frequency table reduces time to O(n) but uses O(n) space.

## The insight

Use slot `v - 1` to record whether `v` has been seen. A negative slot means that its value has appeared before. Reading the absolute magnitude preserves the original number even if its position was marked earlier. The second encounter with the duplicate finds a negative slot, while the sole positive slot after the pass corresponds to the missing value. Restoring signs afterwards preserves the caller's data.

## Optimal solution, traced

```steps
Start [1, 3, 3, 4]. Reading 1 marks index 0: {{[-1, 3, 3, 4]}}.
---
Read 3 and mark index 2: [-1, 3, {{-3}}, 4].
---
Read abs(-3) = 3: index 2 is already negative, so duplicate = {{3}}. Read 4 and mark index 3.
---
The only positive slot is index 1, so missing = {{2}}. Restore [1, 3, 3, 4] and return [3, 2].
```

## Code

```python
def set_mismatch(a):
    duplicate = None
    for x in a:
        value = abs(x)
        i = value - 1
        if a[i] < 0:
            duplicate = value
        else:
            a[i] = -a[i]
    missing = next(i + 1 for i, x in enumerate(a) if x > 0)
    for i in range(len(a)):
        a[i] = abs(a[i])
    return [duplicate, missing]
```

## Complexity

Marking, finding the positive slot, and restoring each require at most one linear pass: O(n) time. The workspace is O(1), excluding the fixed-size returned pair.

## Mistakes and edge cases

- Return duplicate first, not the remaining positive index first.
- The number read from the array may already have been negated; take its absolute value.
- Do not use the code on inputs outside the promised range or on multiple errors; its result relies on the stated uniqueness guarantee.
- The missing slot identifies a value by index, not by the magnitude currently stored there.

## Variations

- Track frequencies in a dictionary if the domain is not a dense interval and extra space is allowed.
- Sum and squared-sum differences yield two equations for the duplicate and missing values; watch integer overflow in fixed-width languages.

=== card | 31
time: 30 min

## The problem

Rearrange a list of comparable values into its immediate next lexicographic ordering, using the same elements and modifying the original list. If no larger ordering exists, wrap to the smallest ordering. Equal values are allowed. For `[1, 3, 2]`, the result is `[2, 1, 3]`; for `[3, 2, 1]`, it is `[1, 2, 3]`.

## Constraints and what they imply

Lexicographic order compares the first position where two arrangements differ. Therefore the smallest possible increase changes a position as far right as possible, then makes the suffix as small as possible. The routine works for an empty list and a singleton as well as duplicate values. It returns `None` and mutates the existing list, so references to the original object see the result.

## Brute force

Generate every distinct permutation, sort them, find the current arrangement, and take its successor modulo the count. The number of permutations can be factorial in `n`, and storing them uses factorial space. This is useful only as a tiny-input oracle, not as the algorithm.

## The insight

Scan from the right for the first index `i` with `a[i] < a[i+1]`. Everything to its right is non-increasing, hence already the greatest arrangement of those suffix elements. No change confined to that suffix can increase the whole list. If no such pivot exists, the entire list is greatest and reversing it yields the smallest.

Otherwise change the pivot to the smallest suffix value strictly greater than it. Because the suffix is non-increasing, its rightmost value greater than the pivot is precisely that choice. After swapping, the suffix remains non-increasing: the displaced pivot fits between the values to its left, which were at least the chosen value, and those to its right, which were at most the pivot. Reverse the suffix to obtain the smallest completion. These two choices ensure that no valid ordering lies between the old and new lists.

## Optimal solution, traced

```steps
Start [1, 3, 5, 4, 2]. The suffix [5, 4, 2] is non-increasing; its left neighbour 3 is the rightmost ascent.
---
Pivot index 1 holds 3. Scanning right to left, the first value greater than 3 is {{4}} at index 3.
---
Swap pivot and successor: [1, {{4}}, 5, {{3}}, 2]. The suffix [5, 3, 2] remains non-increasing.
---
Reverse that suffix: [1, 4, {{2, 3, 5}}]. This is the least ordering larger than the original.
```

## Code

```python
def next_permutation(a):
    i = len(a) - 2
    while i >= 0 and a[i] >= a[i + 1]:
        i -= 1
    if i >= 0:
        j = len(a) - 1
        while a[j] <= a[i]:
            j -= 1
        a[i], a[j] = a[j], a[i]
    left, right = i + 1, len(a) - 1
    while left < right:
        a[left], a[right] = a[right], a[left]
        left += 1
        right -= 1
```

## Complexity

Each scan and the reversal touches at most n positions, so time is O(n). A fixed number of indices and swaps gives O(1) extra space. The factorial alternative does not share these bounds.

## Mistakes and edge cases

- Use strict increase at the pivot and a strictly greater swap partner; equal elements do not produce a larger permutation.
- Picking the leftmost larger suffix value can skip valid intermediate arrangements.
- Reverse only the suffix after the swap; when no pivot exists, `i = -1` makes the whole list the suffix.
- Sorting the suffix also works logically but takes O(n log n) in general and is unnecessary.

## Variations

- Find the previous ordering by reversing both inequality directions and making the suffix maximal.
- Iterate this operation to enumerate distinct permutations in lexicographic order from the smallest arrangement.

=== card | 54
time: 30 min

## The problem

Return the entries of a rectangular grid by starting at the upper-left corner, moving right, then repeatedly turning clockwise as the remaining unvisited region narrows. Every cell must appear exactly once. A `2 x 3` grid `[[1, 2, 3], [4, 5, 6]]` yields `[1, 2, 3, 6, 5, 4]`.

## Constraints and what they imply

The grid is rectangular; `[]` and grids with zero columns return an empty list. Neither the grid nor its rows are modified. The result requires one entry per cell, so output space is unavoidable. A single row or column is particularly important: after walking one side, an opposite side may have disappeared.

## Brute force

Keep a visited matrix and a current direction. At each step, mark the current cell, then advance unless the next position is outside the grid or already visited; in that case turn clockwise. This is O(mn) time but needs O(mn) extra visited storage beyond the output. It is also a useful independent way to check the boundary method.

## The insight

The unvisited cells always form a rectangle bounded by `top`, `bottom`, `left`, and `right`, inclusive. Consume the top row and move `top` down; consume the right column and move `right` left. If a row remains, consume its bottom row backwards and move `bottom` up. If a column remains, consume its left column upwards and move `left` right.

Each pass removes exactly one outer edge from the current rectangle. The two checks after removing earlier edges prevent the same remaining row or column being read twice. The invariant is restored with a smaller rectangle, and termination occurs when it is empty; consequently each cell is emitted once in the intended order.

## Optimal solution, traced

```steps
Grid [[1,2,3], [4,5,6], [7,8,9]]; bounds rows 0..2, columns 0..2.
---
Top row emits {{1,2,3}}; top becomes 1. Right column emits {{6,9}}; right becomes 1.
---
Rows remain: bottom row reversed emits {{8,7}}; bottom becomes 1. Columns remain: left column emits {{4}}; left becomes 1.
---
The remaining rectangle is the single cell (1,1). Top emits {{5}}; bounds cross and the checks suppress duplicate edges.
---
Return [1,2,3,6,9,8,7,4,5].
```

## Code

```python
def spiral_order(grid):
    if not grid or not grid[0]:
        return []
    top, bottom = 0, len(grid) - 1
    left, right = 0, len(grid[0]) - 1
    out = []
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            out.append(grid[top][c])
        top += 1
        for r in range(top, bottom + 1):
            out.append(grid[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                out.append(grid[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                out.append(grid[r][left])
            left += 1
    return out
```

## Complexity

Each of the `m*n` cells is appended once: O(mn) time. The output occupies O(mn) space; the four bounds use O(1) additional space. The empty case is constant time.

## Mistakes and edge cases

- Recheck the surviving row and column before their opposite edges; otherwise the middle strip can be duplicated.
- A grid with one row, one column, or only one cell still obeys the boundary invariant.
- Python negative indices wrap, so blindly traversing a crossed boundary can silently read the wrong row.
- Rectangular input is required; rows of unequal lengths need a different definition of traversal.

## Variations

- Generate a grid by writing consecutive values in spiral order instead of reading them.
- Change the starting corner or turn direction by changing the edge order and the direction of each pass.

=== card | 498
time: 30 min

## The problem

List a rectangular grid's values in alternating anti-diagonals. Starting at the upper-left, the first diagonal goes upward and right, the next downward and left, and directions alternate thereafter. A `2 x 3` grid `[[1,2,3],[4,5,6]]` produces `[1,2,4,5,3,6]`.

## Constraints and what they imply

All rows have the same number of columns; an empty grid or zero-column grid produces `[]`. For `m` rows and `n` columns, an anti-diagonal contains positions with the same sum `r + c`, ranging from zero through `m + n - 2`. The input is not modified and the output has `m*n` entries.

## Brute force

For each possible diagonal sum, scan all cells and collect those with the required sum, then order that group according to direction. This is correct but repeats a full grid scan for every diagonal, taking O(mn(m+n)) time. Storing all groups at once takes O(mn) extra space.

## The insight

On diagonal `d`, choose row `r` and compute column `d - r`. Valid rows lie between `max(0, d - (n-1))` and `min(m-1, d)`, inclusive. These bounds ensure both coordinates are in range and enumerate each cell exactly once, since each has exactly one sum.

For even `d`, enumerate rows from high to low: that walks upward and right. For odd `d`, enumerate low to high: that walks downward and left. Directly choosing row direction avoids a temporary list for each diagonal. The output order is therefore determined by the diagonal sum first and the alternating row order second.

## Optimal solution, traced

```steps
Grid [[1,2,3], [4,5,6]], m = 2, n = 3. Sums run from 0 to 3.
---
d = 0, even: valid rows 0..0, descending gives {{1}}.
---
d = 1, odd: rows 0..1, ascending gives {{2,4}}.
---
d = 2, even: rows 0..1, descending gives {{5,3}}.
---
d = 3, odd: only row 1 is valid, giving {{6}}. Concatenate to get [1,2,4,5,3,6].
```

## Code

```python
def diagonal_order(grid):
    if not grid or not grid[0]:
        return []
    m, n = len(grid), len(grid[0])
    out = []
    for d in range(m + n - 1):
        lo = max(0, d - n + 1)
        hi = min(m - 1, d)
        rows = range(hi, lo - 1, -1) if d % 2 == 0 else range(lo, hi + 1)
        for r in rows:
            out.append(grid[r][d - r])
    return out
```

## Complexity

Each diagonal performs constant setup and each cell is appended once. For nonempty dimensions `m+n-1 <= m*n`, so time is O(mn). Output space is O(mn), and auxiliary space beyond it is O(1), including the lazy `range` object.

## Mistakes and edge cases

- Confusing `r+c` with `r-c` follows the other family of diagonals.
- Reversing odd rather than even diagonals produces the wrong initial direction.
- Calculate bounds using the column count for the lower row bound; test tall and wide grids, not only squares.
- A one-row or one-column grid naturally preserves its only possible order.

## Variations

- Emit all anti-diagonals in the same direction by always iterating rows upward.
- Group main diagonals by `r-c` to process entries from upper left to lower right.

=== card | 48
time: 30 min

## The problem

Turn a square grid clockwise by a quarter turn, modifying the same grid in place. For instance, `[[1,2], [3,4]]` becomes `[[3,1], [4,2]]`. The cell originally at row `r`, column `c` ends at row `c`, column `n-1-r`.

## Constraints and what they imply

The matrix is square and has independently stored rows. The operation must mutate the caller's outer list and existing rows rather than replace them with a separate rotated grid. Cell values themselves can be arbitrary objects; only their positions matter. An empty square or a one-cell square is already rotated.

## Brute force

Allocate a second `n x n` grid and copy each source cell to `(c, n-1-r)`, then copy all the values back. This is O(n²) time and O(n²) temporary space. It is an easy reference model but violates the constant-workspace requirement.

## The insight

Compose two bijections. First transpose across the main diagonal, mapping `(r,c)` to `(c,r)`. Then reverse each row, sending column `r` to `n-1-r`. Their composition is the desired mapping `(r,c) -> (c,n-1-r)`.

In-place transposition swaps each off-diagonal pair exactly once. Restricting the column loop to `c > r` chooses one member of every pair and leaves diagonal entries alone. Reversing each row then rearranges its entries without another matrix. Since both operations are bijections, they neither lose nor duplicate any cell.

The order of these operations matters: reversing rows before transposing instead gives a counter-clockwise turn. In the clockwise version, an original top-row cell becomes the rightmost entry of its destination row, whereas an original bottom-row cell becomes the leftmost. This provides a quick visual check in addition to the coordinate proof.

## Optimal solution, traced

```steps
Start [[1,2,3], [4,5,6], [7,8,9]]. Each original column should become a row read bottom to top.
---
Transpose the upper triangle: [[1,{{4}},{{7}}], [{{2}},5,{{8}}], [{{3}},{{6}},9]].
---
Reverse each row: [{{[7,4,1]}}, {{[8,5,2]}}, {{[9,6,3]}}].
---
For example, original 4 moves (1,0) -> (0,1) by transpose -> (0,1) by row reversal; original 7 moves (2,0) -> (0,2) -> (0,0).
```

## Code

```python
def rotate_clockwise(matrix):
    n = len(matrix)
    for r in range(n):
        for c in range(r + 1, n):
            matrix[r][c], matrix[c][r] = matrix[c][r], matrix[r][c]
    for row in matrix:
        row.reverse()
```

## Complexity

Transposition performs `n(n-1)/2` swaps and row reversals together perform O(n²) work, so time is O(n²). Only loop variables and swap temporaries are required: O(1) auxiliary space. Python's list `reverse` modifies the row itself.

## Mistakes and edge cases

- Swapping both triangles undoes each swap; use only the strict upper triangle.
- Transpose followed by reversing the order of the rows rotates counter-clockwise, not clockwise.
- Replacing the whole matrix with a newly constructed expression hides O(n²) space and may break row aliases.
- A rectangular grid changes shape on a quarter turn and is outside this in-place square contract.

## Variations

- For a counter-clockwise turn, transpose and reverse the order of rows.
- Rotate four corresponding positions at a time around each concentric layer without a separate transpose pass.

=== card | 289
time: 35 min

## The problem

Update a rectangular board of zeros and ones by one simultaneous generation. Each cell has up to eight surrounding neighbours. A live cell survives with two or three live neighbours; a dead cell becomes live with exactly three. Every other cell is dead in the new generation. Update the board in place.

## Constraints and what they imply

The input is rectangular, with each entry initially exactly `0` or `1`; rows are independent mutable lists. Off-board positions do not contribute neighbours. All decisions must see the original generation, not a mixture of old and new states. Empty boards and zero-column boards are unchanged.

## Brute force

Read all neighbours from the original board while writing each new cell into a second grid, then copy that grid back. It runs in O(mn) time because each cell has at most eight neighbours, but consumes O(mn) extra space. The separate-grid version makes a useful independent oracle for this in-place solution.

## The insight

One integer cell can hold two bits. Keep its old state in bit zero and encode its next state in bit one. During the first pass, count each neighbour with `cell & 1`, which ignores whether that neighbour's next-state bit has already been set. Set bit one if and only if the cell will be alive.

The old generation therefore remains readable throughout the first pass. Once every new state has been computed, shift each cell right once to discard the old bit and expose the new one. The two passes give exactly the same simultaneous result as computing into a separate grid. An originally dead cell that will live is encoded as `2`, and a surviving live cell is encoded as `3`.

## Optimal solution, traced

```steps
Start [[0,0,0], [1,1,1], [0,0,0]], a horizontal line of three live cells.
---
Cell (0,1) sees three live neighbours and is born: store {{2}}. Its low bit remains 0 for later neighbour counts.
---
The centre (1,1) has two live neighbours and survives: store {{3}}. Both endpoints have only one and retain low-bit-only value 1.
---
Cell (2,1) also has three neighbours and becomes {{2}}. After all encodings the board is [[0,2,0], [1,3,1], [0,2,0]].
---
Shift all entries right: [[0,{{1}},0], [0,{{1}},0], [0,{{1}},0]], the vertical line.
```

## Code

```python
def life_step(board):
    if not board or not board[0]:
        return
    m, n = len(board), len(board[0])
    for r in range(m):
        for c in range(n):
            live = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if (dr or dc) and 0 <= nr < m and 0 <= nc < n:
                        live += board[nr][nc] & 1
            old = board[r][c] & 1
            if live == 3 or (old and live == 2):
                board[r][c] |= 2
    for row in board:
        for c in range(n):
            row[c] >>= 1
```

## Complexity

Each cell checks at most eight neighbours and is finalised once, so time is O(mn). The counters and indices occupy O(1) additional space. The board itself is reused to store the new generation.

## Mistakes and edge cases

- Counting `cell == 1` misses a live neighbour already encoded as `3`; always mask the old bit.
- Exclude the current cell itself when counting neighbours.
- Check both coordinate bounds before indexing; negative Python indices otherwise wrap.
- Finalising a cell during the first pass destroys old-state information needed by later cells.
- A solitary live cell dies because it has no live neighbours; an empty board is a no-op.

## Variations

- Change the birth and survival counts while preserving the two-bit synchronous-update scheme.
- A toroidal board wraps both coordinates modulo the dimensions instead of treating the edges as boundaries.

=== card | 73
time: 35 min

## The problem

Given a rectangular matrix, replace every cell in any row or column containing an original zero with zero. Perform the change in place using constant extra storage. For `[[1,0,3], [4,5,6]]`, the result is `[[0,0,0], [4,0,6]]`.

## Constraints and what they imply

Rows have equal length and are independent mutable lists. Values need only support comparison with zero and assignment of zero. New zeros must not themselves cause additional rows or columns to be cleared: the affected sets are determined from the original matrix. The implementation handles an empty matrix and zero columns as no-ops.

## Brute force

First record all original zero-containing row indices and column indices in two sets, then clear every cell whose row or column is recorded. This takes O(mn) time and O(m+n) extra space. Re-scanning the matrix separately for each cell would reduce storage but repeat work. Directly zeroing rows when a zero is encountered is incorrect because new zeros could propagate.

## The insight

Use the first cell of each row as its row flag and the first cell of each column as its column flag. The shared corner cannot independently represent both the first row and first column, so remember in a separate boolean whether column zero originally contained a zero. The corner itself serves as the first-row flag.

Scan rows from top to bottom. Before marking a row, inspect its first cell to preserve whether column zero originally contained a zero. For each zero in columns 1 onward, set the corresponding row and column flags to zero. Once this marking pass ends, every inner cell can be cleared if either of its flags is zero. Finally clear the first row if the corner indicates it, then clear the first column if the saved boolean indicates it. This order keeps all flags intact until their consumers have read them.

## Optimal solution, traced

```steps
Start [[1,2,3], [4,0,6], [0,8,9]]. Column 0 already has an original zero in row 2, so save col_zero = {{True}}.
---
The zero at (1,1) marks row 1 and column 1: matrix becomes [[1,{{0}},3], [{{0}},0,6], [0,8,9]].
---
Using the flags, clear inner positions in rows 1 and 2 and column 1: [[1,0,3], [0,0,{{0}}], [0,{{0,0}}]].
---
Corner is 1, so do not clear all of row 0. Saved col_zero is true, so clear the first column: [[{{0}},0,3], [0,0,0], [0,0,0]].
```

## Code

```python
def set_zeroes(matrix):
    if not matrix or not matrix[0]:
        return
    m, n = len(matrix), len(matrix[0])
    col_zero = False
    for r in range(m):
        if matrix[r][0] == 0:
            col_zero = True
        for c in range(1, n):
            if matrix[r][c] == 0:
                matrix[r][0] = 0
                matrix[0][c] = 0
    for r in range(1, m):
        for c in range(1, n):
            if matrix[r][0] == 0 or matrix[0][c] == 0:
                matrix[r][c] = 0
    if matrix[0][0] == 0:
        for c in range(n):
            matrix[0][c] = 0
    if col_zero:
        for r in range(m):
            matrix[r][0] = 0
```

## Complexity

The mark and clear passes each visit at most all `m*n` cells, and the final border passes are O(m+n), so time is O(mn) for nonempty dimensions. Only one boolean and loop indices are added: O(1) auxiliary space.

## Mistakes and edge cases

- A zero originally at the corner sets both first-row and first-column flags; they must remain independent.
- Clearing the first row or column before the inner cells destroys markers still needed.
- Inspect column zero before setting the current row's flag, or a zero elsewhere in that row is misclassified as an original column-zero entry.
- Test one-row and one-column matrices: one of the inner loops is empty, but the border logic still applies.

## Variations

- If O(m+n) space is acceptable, keep separate row and column sets to avoid modifying the grid during discovery.
- Replace every affected row and column with another sentinel, while retaining a distinct test for the original trigger.

=== card | 41
time: 45 min

## The problem

Find the least strictly positive integer absent from an integer list. The input may contain negative values, zero, duplicates and values much larger than the list. For example, `[3, 4, -1, 1]` is missing `2`, while `[1, 2, 3]` is missing `4`. Aim for linear time and constant extra workspace, and allow the list to be reordered.

## Constraints and what they imply

For length `n`, only the numbers `1` through `n` need dedicated slots. If all of them occur, the answer is `n+1`; otherwise the first absent one is already in that range. This follows from there being only `n` input positions, and it holds even with duplicates or an empty list. Values outside this range cannot be the first missing positive unless the answer is `n+1`, and they need not be placed.

The implementation mutates the list but preserves its multiset of values through swaps. It accepts arbitrary Python integers and returns a positive integer. An empty list returns `1`. A read-only input or a requirement to preserve order would require a different trade-off, such as a set or an explicit copy.

## Brute force

Test candidates `1, 2, ...` in order, scanning the whole list for each until one is absent. The answer cannot exceed `n+1`, so this uses O(n²) time in the worst case and O(1) working space. Alternatively, build a set of all values and query the candidates in expected O(n) time with O(n) extra space.

Sorting a copy and looking for gaps gives another reference method, but a general sort costs O(n log n) time and the copy needs O(n) space. Even an in-place sort does not meet the requested linear bound. The bounded candidate range suggests using the list positions as a direct-address table instead.

## The insight

The home of a value `v` in `1..n` is index `v-1`. At each index `i`, if the value there is in range and its home does not already hold it, swap it with the value at its home. Reconsider the newly arrived value at `i`, because it may also have an unfilled home. If the current value is out of range or its home already contains the same value, move to the next index.

The key invariant is that a correctly placed value never leaves its home. A swap targets the home of the value being moved and is performed only if that home is not already correct. Thus each swap permanently fixes at least one previously incorrect slot. There are at most `n` such swaps across the whole algorithm, even though a `while` loop is nested inside a `for` loop. The other work is constant per index and per swap.

When processing stops, any in-range value that occurs has a correct copy at its home: otherwise some occurrence would have had an eligible swap when its index was processed. Later swaps cannot remove a correct value. Scanning positions left to right therefore finds the least absent value as `i+1` at the first mismatch. If every position matches, return `n+1`. The duplicate guard is essential: swapping two equal copies cannot make progress.

## Optimal solution, traced

```steps
Start [3, 4, -1, 1], n = 4. At i = 0, value 3 belongs at index 2; swap to get {{[-1, 4, 3, 1]}}.
---
i = 0 now holds -1, which has no home in 1..4. Advance to i = 1; value 4 belongs at index 3.
---
Swap indices 1 and 3: [-1, {{1}}, 3, {{4}}]. The new value 1 at i = 1 belongs at index 0.
---
Swap indices 1 and 0: [{{1, -1}}, 3, 4]. Index 1 is out of range; indices 2 and 3 are home already.
---
First mismatch is index 1: expected {{2}}, found -1. Return 2. Each swap permanently fixed a distinct home.
```

## Code

```python
def first_missing_positive(a):
    n = len(a)
    for i in range(n):
        while 1 <= a[i] <= n and a[a[i] - 1] != a[i]:
            home = a[i] - 1
            a[i], a[home] = a[home], a[i]
    for i, value in enumerate(a):
        if value != i + 1:
            return i + 1
    return n + 1
```

## Complexity

The first pass performs at most n successful swaps plus n loop exits; the final scan is also linear. Total time is O(n), including adversarial orderings and duplicates. Only the index, home and value variables are used, so auxiliary space is O(1). The list itself is modified in place.

## Mistakes and edge cases

- Check `1 <= a[i] <= n` before indexing its home; negative Python indices silently wrap and large indices raise.
- Check whether the home already contains the same value, not merely whether its index differs from `i`. Equal duplicates otherwise cause an infinite swap loop.
- Compute `home` before the tuple assignment. Using `a[a[i]-1]` as an assignment target after assigning `a[i]` can use the changed value when Python evaluates targets.
- `[]` returns 1, `[1]` returns 2, and an array containing only nonpositive numbers returns 1. All values in place returns `n+1`.
- The final mismatch yields its index plus one, not the misplaced number at that index.

## Variations

- With values guaranteed in `1..n`, identify every missing value by collecting all mismatched home slots after cyclic placement.
- Preserve the original order by using a set, accepting O(n) extra memory.
- If an input copy is allowed but the original is read-only, run the same placement method on that copy and count its storage.

=== card | 238
time: 30 min

## The problem

For each position in a list of integers, return the product of all values at other positions. Division is not allowed. For `[2, 3, 4]` the output is `[12, 8, 6]`; for `[2, 0, 4]` it is `[0, 8, 0]`. The result array is not counted as auxiliary workspace.

## Constraints and what they imply

The input may contain negative numbers and zeros, so division by a total product is not a robust strategy even if division were permitted. Products are exact Python integers; in a fixed-width language the numeric contract must instead guarantee no overflow or use wider arithmetic. The empty product is 1, so a singleton produces `[1]` and an empty input produces `[]`.

## Brute force

For every index, multiply all entries except the one at that index. This performs O(n²) multiplications and requires only the output plus constant workspace. A prefix array and a suffix array reduce time to O(n), but use O(n) additional storage. The output itself can hold one of those arrays.

## The insight

Split the product for position `i` into the product strictly to its left and the product strictly to its right. First fill `out[i]` with the left product, maintaining a running prefix that is updated only after writing the current position. Then traverse from right to left, multiplying `out[i]` by the running right product before including `a[i]` in that product.

At the start of each forward iteration, `prefix` contains exactly the elements preceding `i`. At the start of each backward iteration, `suffix` contains exactly the elements following `i`. Thus the multiplication combines precisely all positions except `i`, even when zeros occur. A single zero contributes to every output except its own; two zeros make every output zero automatically.

## Optimal solution, traced

```steps
Input [2,0,4]. Start prefix = 1. Write left products before multiplying each current value: output becomes {{[1,2,0]}}.
---
Start suffix = 1 at i = 2: out[2] remains 0, then suffix becomes 4.
---
i = 1: multiply out[1] by 4, producing {{8}}; then include input 0, making suffix 0.
---
i = 0: multiply out[0] by 0. Return {{[0,8,0]}}; no division or zero-specific branch is needed.
```

## Code

```python
def product_except_self(a):
    out = [1] * len(a)
    prefix = 1
    for i, value in enumerate(a):
        out[i] = prefix
        prefix *= value
    suffix = 1
    for i in range(len(a) - 1, -1, -1):
        out[i] *= suffix
        suffix *= a[i]
    return out
```

## Complexity

The two passes perform O(n) arithmetic operations and the output occupies O(n) space. Apart from the output, the two running products and indices use O(1) auxiliary space in the usual unit-cost arithmetic model. Python's arbitrary-precision multiplication and integer storage can cost more as products grow.

## Mistakes and edge cases

- Update the running product after using it, or the current element is included in its own answer.
- Do not divide by an element: zeros break division and it is disallowed by the contract.
- Check zero, multiple zeros, negative values, a singleton, and the empty list.
- If the caller counts output as workspace, total allocated space is O(n), not O(1).

## Variations

- Replace multiplication with another associative operation and an identity to obtain all-but-one aggregates where order is preserved.
- Return only the product modulo a given positive modulus, reducing intermediate magnitude when that is the required result.

=== card | 1980
time: 30 min

## The problem

Given `n` distinct binary strings each of length `n`, construct any binary string of length `n` that is not in the input. For `["00", "11"]`, both `"01"` and `"10"` are valid answers. The answer need not be the lexicographically smallest missing string.

## Constraints and what they imply

Each entry must contain only `0` and `1` and have length exactly `n`, so character `i` exists in input string `i`. Distinctness is promised but is not actually needed by the construction. With `n >= 1`, there are more binary strings of length `n` than the n supplied strings. The implementation also returns `""` on an empty list under the natural extension of the contract.

## Brute force

Enumerate the `2**n` candidate binary strings and test each against the input, using a set for membership. This can examine exponentially many candidates and needs storage for the input set and generated strings. Enumerating integer encodings is fine as an independent tiny-input checker, but unnecessary when any absent answer is acceptable.

## The insight

Give each input string its own position at which the answer is guaranteed to differ. For each `i`, look at `strings[i][i]` and put its opposite binary digit into position `i` of the result. The result differs from input string `i` at position `i`, so it differs from every input string. This is a direct constructive proof and does not rely on testing membership or searching the candidate space.

Building a list of characters followed by one join keeps construction linear. Random selection might repeatedly hit an existing string and has no deterministic bound on the number of attempts. Diagonal construction always makes exactly n character decisions.

## Optimal solution, traced

```steps
Input ["010", "111", "001"], n = 3. Reserve position i for disagreeing with string i.
---
i = 0: string 0 has {{0}} at position 0, so append 1.
---
i = 1: string 1 has {{1}} at position 1, so append 0.
---
i = 2: string 2 has {{1}} at position 2, so append 0.
---
Join to get {{100}}. It differs from strings 0, 1, and 2 at positions 0, 1, and 2 respectively.
```

## Code

```python
def missing_binary_string(strings):
    chars = []
    for i, s in enumerate(strings):
        chars.append("1" if s[i] == "0" else "0")
    return "".join(chars)
```

## Complexity

There are n indexed reads, n appends and one join, so time is O(n). The character list takes O(n) auxiliary space and the returned string takes O(n) output space. This implementation does not claim constant auxiliary space; Python strings are immutable.

## Mistakes and edge cases

- Flipping a fixed column does not guarantee a distinct result for each input; string `i` needs its own position `i`.
- The construction needs at least n characters in each string and a binary alphabet; validate inputs separately if those promises are absent.
- Do not assume the diagonal answer is the smallest missing one.
- Distinct inputs are unnecessary for correctness, but they are part of the stated input contract.

## Variations

- For a larger alphabet, choose any symbol different from each diagonal character.
- To require the lexicographically smallest absent string, use a search or trie with appropriate missing-subtree information rather than this arbitrary-answer construction.
