---
key: dpseq
name: DP on grids, strings and knapsacks
stage: strategy
summary: Two-dimensional states over grids, pairs of sequences, ranges and capacities: grid paths, LCS, edit distance, subsequence matching, palindromes, knapsacks and segmentation, with the answer reconstructed from the table.
why: Most dynamic programming you will meet in practice has one of four shapes: a grid walked in one direction, two sequences compared prefix by prefix, a range of one sequence, or a budget filled with items. Learn the four state shapes and their fill orders and a large class of "count", "minimise" and "is it possible" problems becomes routine. The same tables run in real software: diff tools compute common subsequences of lines, spell checkers and PostgreSQL rank words by edit distance, DNA aligners score alignments with the same recurrence, and budgeting problems are knapsacks. This module also teaches the engineering around the tables: one-row memory, reading the answer back, banding and early exit, and knowing when a capacity is too large for a table at all.
outcomes:
- Write the recurrence for a grid path problem, choose the fill direction from its dependencies and keep one row of memory
- Solve longest common subsequence and edit distance with a prefix-pair table, and recover the actual alignment by walking back
- Model matching and counting questions over two sequences (interleaving, wildcards, distinct subsequences) as boolean or counting tables
- Solve palindrome problems with range tables filled in the right order
- Solve 0/1 and unbounded knapsack, subset sum, partition and counting variants, and explain why the one-row loop runs backwards or forwards
- Explain pseudo-polynomial time and say what to do when the capacity is too large for a table
- Build a fast edit-distance spelling suggester and name where these DPs run in real systems
cues:
- Two strings or arrays compared position by position: common, transform, delete to make equal, match, interleave
- A grid with moves only right and down (or down-left, down, down-right): count paths or find the cheapest
- Items with a weight or cost and a capacity or target: can we reach exactly, how many ways, the fewest pieces
- Subsequence (not substring) wording, palindromes inside a string, or fewest insertions and deletions
- Split a string into pieces that come from a dictionary or have a property
traps:
- Mixing string indices and table indices: dp[i][j] describes the prefixes a[:i] and b[:j], so compare a[i - 1] with b[j - 1]
- Looping capacity upwards in 0/1 knapsack (an item is reused) or downwards in unbounded knapsack (reuse is lost)
- Swapping the loop nesting in counting problems, so combinations are counted when ordered sequences were asked for (or the reverse)
- Using 0 as "impossible" in a minimisation (it silently wins every min) instead of infinity
- Keeping only one row when you still need to walk back through the table to rebuild the answer
systems:
- Diff tools: classic Unix diff computed a longest common subsequence of lines; Git's default diff is Myers' O(ND) algorithm, which finds a shortest edit script, with patience and histogram as more readable alternatives
- Fuzzy matching: PostgreSQL's fuzzystrmatch extension provides levenshtein() and levenshtein_less_equal(), an accelerated version for small distances
- Bioinformatics: Needleman-Wunsch (global) and Smith-Waterman (local) alignment are edit-distance tables with scores and gap penalties; Biopython's PairwiseAligner implements them
- Budgeting and packing: knapsack DP when capacities are small integers, solvers such as OR-Tools' branch-and-bound knapsack solver when they are not
further:
- Chapter · 40 min | Erickson, Algorithms ch. 3: 'Edit Distance' and 'Subset Sum' (PDF pages 15-21) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=15
- Article · 15 min | cp-algorithms: Knapsack problem, 0-1 and complete knapsack | https://cp-algorithms.com/dynamic_programming/knapsack.html#0-1-knapsack
- Notes · 15 min | MIT 6.006 lecture 18: Pseudopolynomial (rod cutting, subset sum, PDF pages 2-6) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/mit6_006s20_lec18.pdf#page=2
- Article · 25 min | James Coglan: The Myers diff algorithm, part 1 (the edit graph) | https://blog.jcoglan.com/2017/02/12/the-myers-diff-algorithm-part-1/
bank: knapsack dpgrid dpstr
---

=== primer | How do you count or minimise paths through a grid with DP? | 13 min
goal: Fill a grid table in reading order to count paths or find the cheapest path, with obstacles, in O(mn) time and one row of memory
tag: dpseq-grid | Grid path DP
link: USACO Guide: Paths on Grids | https://usaco.guide/gold/paths-grids#solution---grid-paths | 10 min: the 'Solution - Grid Paths' section, the same recurrence with blocked cells, worked in Python and C++
practice: 64, 221

> [!key]
> When moves only go right or down, every path into cell (r, c) arrives from the cell above or the cell to its left. So the answer for a cell (how many paths, or the cheapest cost) combines two answers you already have, and filling the grid row by row in reading order computes every cell exactly once: **O(mn) time**. Because a cell only looks up and left, **one row of memory** is enough.

## Intuition

Picture a city of square blocks. You walk from the north-west corner to the south-east corner, only ever east or south. How many routes are there? Every route into a crossing comes either from the crossing to its north or from the one to its west, so routes(here) = routes(north) + routes(west). Write the counts on a 3 by 3 grid of crossings and each number is the sum of the one above and the one to the left:

```text
1  1  1
1  2  3
1  3  6      six routes to the far corner
```

Those are Pascal's triangle numbers turned on their side, so an empty grid has a closed form, `math.comb(m + n - 2, m - 1)`. The closed form dies as soon as you add a roadblock or a toll; the table does not care.

## How it works

Run the DP recipe from the previous module once for counting and once for the cheapest path:

| Recipe step | Count the paths | Cheapest path |
|---|---|---|
| Specification | ways[r][c] = number of right/down paths from (0, 0) to (r, c) | best[r][c] = least total cost of a path from (0, 0) to (r, c), both ends included |
| Recurrence | ways[r - 1][c] + ways[r][c - 1], or 0 on a wall | cost[r][c] + min(best[r - 1][c], best[r][c - 1]) |
| Base and outside | ways[0][0] = 1; outside the grid counts 0 | best[0][0] = cost[0][0]; outside the grid is infinity |
| Order | rows top to bottom, each row left to right | the same |
| Answer | ways[m - 1][n - 1] | best[m - 1][n - 1] |

Notice the two different values for "nothing comes from there". In a count, a missing neighbour contributes **0** paths. In a minimum, a missing neighbour must never win the `min`, so it is **infinity**. Mixing them up is the most common grid DP bug: a 0 in a minimisation looks like a free path from outside the grid.

### One row is enough

Keep a single list `ways` for the row being filled. Just before you overwrite `ways[c]`, it still holds the value from the row above, and `ways[c - 1]` has already been updated for this row:

```text
              c - 1        c
row r - 1       .       [above]    <- still stored in ways[c]
row r        [left]      here      <- ways[c - 1] already overwritten
```

So `ways[c] += ways[c - 1]` reads exactly the two values the recurrence needs. The direction matters: sweep right to left instead and `ways[c - 1]` would still be the row above, so you would be adding the up-left diagonal instead of the left neighbour.

### The same idea in other shapes

- **Falling paths** (move down, down-left or down-right): a cell reads three cells of the row above. Seam carving, the content-aware image resizing trick, finds the cheapest such path through a pixel "energy" grid.
- **Squares and shapes ending at a cell**: the answer for (r, c) can depend on up, left and up-left at once. You will derive one in the Lab.
- **Backwards dependencies**: if a cell's value depends on what happens *after* it (for example the least health you need on entering a cell so you survive to the exit, Dungeon Game 174 in the bank), fill from the bottom-right corner towards the top-left.
- **Two walkers at once**: add the second walker's column to the state; it is still a table, just with one more dimension.

## Cost

There are m times n cells and each one does a constant amount of work (two reads, an add or a min), so the time is **O(mn)**. The full table costs O(mn) memory, the rolling row O(n); if the grid is tall and narrow, roll along the shorter side. In pure Python the counting template on a 1000 by 1000 grid takes about 0.4 seconds. Counts grow fast: an empty 100 by 100 grid has `comb(198, 99)`, about 2.3 x 10^58 paths. Python integers do not overflow; in C++ or Java you need the modulus the problem gives you, or a 64-bit type and a proof that it is enough.

## When to use it

Reach for a grid DP when the moves form no cycles (right and down, or any set that always makes progress in one direction) and the question is "how many" or "best". Move sets with cycles need graph search instead.

| Situation | Tool |
|---|---|
| Right/down (or any one-directional) moves; count or optimise | grid DP, O(mn) |
| Four directions, every step costs 1 | BFS from the graphs module (cycles rule out a single fill order) |
| Four directions, weighted cells | Dijkstra from the weighted paths module |
| Count paths in an empty grid | `math.comb(m + n - 2, m - 1)` |
| Four directions but each step must climb to a larger value | memoised DFS: strictly increasing moves cannot cycle (329 in the bank) |

## Worked trace

A 3 by 4 grid with a wall (`#`) at row 1, column 2. `ways` is the single row of memory; the picture on the left shows which cells are final.

```steps
Start: seed ways[0] = 1 ("one way to stand on the start"); nothing else is reached yet
    grid          ways
    . . . .       {{1}}  0  0  0
    . . # .
    . . . .
---
Row 0, left to right: no row above (ways[c] was 0), so each cell copies its left neighbour
    1 1 1 1       {{1  1  1  1}}
    . . # .
    . . . .
---
Row 1, c = 0: nothing on the left, so it keeps the 1 from above
    1 1 1 1       {{1}}  1  1  1      (ways[1..3] still hold row 0)
    1 . # .
---
Row 1, c = 1: above 1 + left 1 = 2
    1 1 1 1        1 {{2}}  1  1
    1 2 # .
---
Row 1, c = 2 is a wall: no path passes through it, so 0
    1 1 1 1        1  2 {{0}}  1
    1 2 # .
---
Row 1, c = 3: above 1 + left 0 = 1 (the only way in is from above)
    1 1 1 1        1  2  0 {{1}}
    1 2 # 1
---
Row 2: 1, then 1 + 2 = 3, then 0 + 3 = 3, then 1 + 3 = 4. Answer: 4 paths
    1 1 1 1       {{1  3  3  4}}
    1 2 # 1
    1 3 3 4
```

Check it another way: an empty 3 by 4 grid has `comb(5, 2) = 10` paths; 3 of the ways reach the wall and 2 continue from it to the corner, so 6 paths use the wall and 10 - 6 = 4 survive.

## Template

```python
def count_paths(grid):
    """Number of right/down paths from the top-left to the bottom-right cell.
    grid[r][c] == 1 marks a blocked cell."""
    n = len(grid[0])
    ways = [0] * n                 # ways[c]: paths into (r, c) for the row being filled
    ways[0] = 1
    for row in grid:
        for c in range(n):
            if row[c] == 1:
                ways[c] = 0        # nothing passes through a wall
            elif c > 0:
                ways[c] += ways[c - 1]   # from above (old ways[c]) + from the left
    return ways[-1]


def min_path_cost(cost):
    """Cheapest right/down path, paying cost[r][c] for every cell visited."""
    INF = float("inf")
    n = len(cost[0])
    best = [INF] * n
    best[0] = 0
    for row in cost:
        for c in range(n):
            left = best[c - 1] if c > 0 else INF
            best[c] = row[c] + min(best[c], left)
    return best[-1]
```

In `min_path_cost` the seed `best[0] = 0` plays the role of "a free cell above the start"; every other cell of the imaginary row above is infinity, so the first real row can only be entered from the left.

## Pitfalls

- **Initialising the first row and column to 1** with walls present. A cell after a wall in the first row is unreachable. The template never special-cases the first row, so it gets this right automatically.
- **A wall on the start or the finish.** The answer is 0; the template handles it, a hand-written base case often does not.
- **0 for "unreachable" in a minimum.** Use `float("inf")` (or a large sentinel in C++), and translate it back if the problem wants -1.
- **`[[0] * n] * m`** makes m references to one row, so writing one cell writes a whole column. Build rows with a comprehension.
- **Memoised recursion on a big grid** recurses m + n deep: 2,000 frames for a 1000 by 1000 grid, past Python's default limit of 1,000. Tabulate instead.

## Check yourself

Q: Trace `count_paths([[0, 0, 0], [0, 1, 0], [0, 0, 0]])`. What is `ways` after each row?
A: After row 0: [1, 1, 1]. After row 1: [1, 0, 1] (the centre is a wall, and the right cell gets 1 from above plus 0 from the left). After row 2: [1, 1, 2]. Two paths: around the wall on either side.

Q: In `min_path_cost`, a colleague writes `best = [0] * n` instead of infinity with `best[0] = 0`. What goes wrong, and on which input?
A: Every cell of row 0 then sees a free cell "above" it, so best[0][c] becomes just cost[0][c] instead of the running sum along the first row: the code pretends you can drop into the grid anywhere along the top edge. On [[1, 9], [9, 1]] it returns 10 instead of 11, and on the single row [[1, 5, 5]] it returns 5 instead of 11.

Q: Moves may now also go diagonally down-right. How do the recurrence and the one-row update change?
A: ways[r][c] = ways[r - 1][c] + ways[r][c - 1] + ways[r - 1][c - 1]. In a single row the up-left value is the old `ways[c - 1]`, which has already been overwritten when you reach c, so save each cell's old value in a variable (say `diag`) before you update it and use it for the next cell. The seed for the start cell must not leak into the diagonal of the first row, so the easiest correct version is a 2D table or a separate previous-row list.

Q: Why does a grid where you may also move up or left need BFS or Dijkstra instead of this table?
A: With moves in all four directions a cell can be reached from cells that come after it in reading order, and paths can loop. There is no order in which every cell's inputs are final before it is computed, which is what a table fill requires. BFS (unit costs) and Dijkstra (weights) settle cells in order of distance instead.

## Lab

- **64 Minimum Path Sum.** Change the counting template's `+` into `min` with the right "nothing" value. Expected: O(mn) time, O(n) extra space; on [[2, 9, 1], [1, 4, 8], [7, 1, 3]] the answer is 11 (2, 1, 4, 1, 3).
- **221 Maximal Square** (derive it). Define side[r][c] as the side of the largest all-1 square whose bottom-right corner is (r, c), then draw a few cases to find how it depends on its three neighbours above and to the left. Expected: O(mn) time, O(n) space; for the rows "10111", "01111", "11111", "00110" the answer is 9 (a 3 by 3 square in the top-right corner).
- **Check the closed form.** Assert `count_paths([[0] * n for _ in range(m)]) == math.comb(m + n - 2, m - 1)` for all m, n up to 8. Expected: all pass; a 10 by 10 grid gives 48620.

> [!know]
> You now know how to turn a grid with one-directional moves into a table filled in reading order, with the right "nothing" value and one row of memory.

=== primer | How does the LCS table find the longest common subsequence, and how do you read it back? | 15 min
goal: Fill the prefix-pair table for the longest common subsequence, prove its recurrence, and walk back from the corner to recover one LCS
tag: dpseq-lcs | Two-sequence prefix DP (LCS)
link: MIT 6.006 lecture 16 notes (PDF) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/28461a74f81101874a13d9679a40584d_MIT6_006S20_lec16.pdf#page=2 | 10 min: 'Longest Common Subsequence (LCS)' on PDF pages 2-3, the same recurrence over suffixes in SRT BOT form, with the argument for why a first-character match can be used
practice: 1143

> [!key]
> Let L[i][j] be the length of the longest common subsequence of the prefixes a[:i] and b[:j]. Look only at the last characters: if they are equal, some LCS ends with that pair, so L[i][j] = L[i - 1][j - 1] + 1; if not, at least one of them is unused, so L[i][j] = max(L[i - 1][j], L[i][j - 1]). Fill the (m + 1) by (n + 1) table row by row in **O(mn)**, then walk back from the bottom-right corner to read off an actual subsequence.

## Intuition

A **subsequence** keeps some characters in their original order and drops the rest: "ONE" is a subsequence of "STONE" and of "LONGEST", so it is a common subsequence of both. (A **substring** must be contiguous; that is a different problem.) Version control asks the same question about lines: which lines survive unchanged, in the same order, from the old file to the new one? Everything else is a deletion or an insertion.

Brute force lists all 2^m subsequences of one string and checks each against the other: hopeless beyond about 25 characters. The DP replaces "which subsequence?" with a much smaller question about the last characters of two prefixes. There are only (m + 1)(n + 1) pairs of prefixes, and each needs constant work.

## How it works

| Recipe step | LCS |
|---|---|
| Specification | L[i][j] = length of an LCS of a[:i] and b[:j] |
| Recurrence | L[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1], else max(L[i - 1][j], L[i][j - 1]) |
| Base cases | L[0][j] = L[i][0] = 0 (an empty prefix shares nothing) |
| Order | i from 1 to m, j from 1 to n: each cell needs up, left and up-left |
| Answer | L[m][n], then walk back for the subsequence itself |

### Why the recurrence is right

Call the last characters x = a[i - 1] and y = b[j - 1].

- **x == y.** Take any LCS Z of the two prefixes. If Z does not use x at the end of both prefixes, either its last character is matched to earlier copies (re-match it to these last positions: same length) or x is free in both prefixes (append it: Z was not longest, a contradiction). So some LCS ends with this pair, and the rest of it is an LCS of a[:i - 1] and b[:j - 1].
- **x != y.** They cannot be matched to each other, and a common subsequence ends with at most one character, so at least one of x, y is unused. Drop the unused one: the answer is the better of dropping x (L[i - 1][j]) or dropping y (L[i][j - 1]).

### Reading the answer back

The table stores lengths, not strings. Start at (m, n). If the characters match, that character is in the LCS: record it and move diagonally. Otherwise move towards the neighbour (up or left) that holds the same value as the current cell, because that is where the value came from. Stop at row or column 0 and reverse what you recorded. When up and left tie, either choice gives a valid LCS of the same length; the tie-breaking rule only decides *which* one you get.

### Relatives you can now solve

- **Fewest deletions to make two strings equal:** m + n - 2L (583 in the bank).
- **Shortest common supersequence:** m + n - L characters, built by the same walk back while emitting every character (1092 in the bank).
- **Longest palindromic subsequence:** the LCS length of s and reversed(s), which the palindrome card solves directly.
- **Diff:** with only insertions and deletions allowed, the shortest edit script has m + n - 2L operations; the real-systems card shows how tools avoid the full table.

## Cost

(m + 1)(n + 1) cells at constant work each: **O(mn) time**. Walking back needs the whole table, O(mn) memory; the length alone needs only the previous row, **O(min(m, n))** if you put the shorter sequence on the inside. In pure Python, `lcs_length` on two random 2,000-character DNA strings (4 million cells) takes about 2 seconds, so 10^4 by 10^4 (10^8 cells, also hundreds of megabytes as a full table of Python ints) is out of reach. Hirschberg's divide-and-conquer trick recovers the subsequence itself in linear space for about twice the time; diff tools use Myers' O((m + n)D) algorithm, where D is the number of edits.

## When to use it

Cues: two sequences, order must be preserved, elements are matched one to one and the question is "most kept", "fewest removed" or "how similar". It works on any comparable items: characters, words, lines, or numbers.

| Question | Tool |
|---|---|
| Longest run of matches in order, gaps allowed | LCS table (this card) |
| Longest common *substring* (contiguous) | L[i][j] = L[i - 1][j - 1] + 1 on a match, else 0; take the maximum cell |
| Fewest inserts, deletes and substitutions | edit distance (next card) |
| Is t a subsequence of s at all? | two pointers, O(m + n); no table needed |
| Two huge, nearly identical files | trim common ends, then Myers' algorithm (real-systems card) |

## Worked trace

LCS of a = "STONE" (rows) and b = "LONGEST" (columns).

```steps
Row 0 and column 0 are 0 (empty prefix). Row S: S matches only the S of LONGEST, so that cell is diagonal 0 + 1 = 1; the T column inherits 1 from its left
          L  O  N  G  E  S  T
       0  0  0  0  0  0  0  0
    S  0  0  0  0  0  0 {{1}} 1
---
Row T: (T, T) is a match, so diagonal (S, S) = 1 plus 1 = 2
          L  O  N  G  E  S  T
       0  0  0  0  0  0  0  0
    S  0  0  0  0  0  0  1  1
    T  0  0  0  0  0  0  1 {{2}}
---
Row O: (O, O) = diagonal 0 + 1 = 1, carried right by max(up, left); the last cell keeps max(up 2, left 1) = 2
          L  O  N  G  E  S  T
       0  0  0  0  0  0  0  0
    S  0  0  0  0  0  0  1  1
    T  0  0  0  0  0  0  1  2
    O  0  0 {{1}} 1  1  1  1  2
---
Row N: (N, N) = diagonal (O, O) = 1 plus 1 = 2
          L  O  N  G  E  S  T
    T  0  0  0  0  0  0  1  2
    O  0  0  1  1  1  1  1  2
    N  0  0  1 {{2}} 2  2  2  2
---
Row E: (E, E) = diagonal (N, G) = 2 plus 1 = 3. The corner holds the answer: 3
          L  O  N  G  E  S  T
    O  0  0  1  1  1  1  1  2
    N  0  0  1  2  2  2  2  2
    E  0  0  1  2  2 {{3}} 3 {{3}}
---
Walk back from the corner: (E, T) and (E, S) differ and the left cell holds the same 3, so go left twice; (E, E) matches: record E, go diagonal
          L  O  N  G  E  S  T
    O  0  0  1  1  1  1  1  2
    N  0  0  1  2 {{2}} 2  2  2
    E  0  0  1  2  2 {{3  3  3}}
---
(N, G) differs, left holds 2 again: go left. (N, N) matches: record N, diagonal. (O, O) matches: record O, diagonal
          L  O  N  G  E  S  T
    T  0 {{0}} 0  0  0  0  1  2
    O  0  0 {{1}} 1  1  1  1  2
    N  0  0  1 {{2  2}} 2  2  2
---
(T, L) differs and both neighbours are 0: go up, then up again to row 0 and stop. Recorded E, N, O; reversed: "ONE"
    LCS = "ONE", length 3
```

## Template

```python
def lcs(a, b):
    """One longest common subsequence of a and b, as a list."""
    m, n = len(a), len(b)
    L = [[0] * (n + 1) for _ in range(m + 1)]   # L[i][j]: LCS length of a[:i], b[:j]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                L[i][j] = L[i - 1][j - 1] + 1
            else:
                L[i][j] = max(L[i - 1][j], L[i][j - 1])
    out, i, j = [], m, n                        # walk back from the bottom-right corner
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i, j = i - 1, j - 1
        elif L[i - 1][j] >= L[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return out[::-1]


def lcs_length(a, b):
    """LCS length in O(min(m, n)) extra space: keep only the previous row."""
    if len(b) > len(a):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]
```

Both work on any sequences of comparable items: `lcs(old_lines, new_lines)` gives the lines a diff keeps.

## Pitfalls

- **Index shift.** The table has an extra row and column for the empty prefix, so cell (i, j) compares `a[i - 1]` with `b[j - 1]`. Comparing `a[i]` with `b[j]` either crashes at i = m or silently shifts every match.
- **Storing strings in cells** (`L[i][j] = L[i - 1][j - 1] + a[i - 1]`) multiplies time and memory by the LCS length. Store lengths and walk back.
- **Rolling rows when you need the subsequence.** Two rows give the length only; keep the full table, or use Hirschberg, if you must rebuild it.
- **Substring or subsequence?** Read the statement twice: "contiguous", "substring" and "subarray" need the reset-to-0 recurrence instead.
- **Memoised recursion** goes m + n deep; for two 1,000-character strings that already exceeds Python's default recursion limit.

## Check yourself

Q: What does `lcs("ABAB", "BABA")` return, and is it the only answer?
A: It returns ['A', 'B', 'A'] (length 3). "BAB" is another LCS of the same length; the walk back prefers moving up on ties, which decides which one you get.

Q: Why is it safe to take the diagonal + 1 on a match without also comparing max(up, left)?
A: Because some LCS of the two prefixes ends with the matched pair (re-match the last character of any LCS to these positions, or append the pair if it was unused), so L[i - 1][j - 1] + 1 is optimal. It can never be smaller than up or left either, because those differ from the diagonal value by at most 1.

Q: How many characters must you delete, in total, to make "STONE" and "LONGEST" equal?
A: 6. Only a common subsequence can survive in both, so the best you can do is keep the LCS "ONE": delete 5 - 3 = 2 characters from STONE and 7 - 3 = 4 from LONGEST, m + n - 2L = 12 - 6.

Q: To save allocations, a colleague creates `cur = [0] * (len(b) + 1)` once before the outer loop, fills `cur[j]` in place for each row, and ends each row with `prev = cur`. Find a small input where it is wrong, and explain.
A: `lcs_length("AB", "BB")` returns 2 instead of 1. After the first row, `prev` and `cur` are the same list, so `prev[j - 1]` is no longer the row above: it has already been overwritten in this row. In row B, cell 2 reads the freshly written cell 1 (value 1) as its "diagonal" and adds 1, matching the single B twice. Each row needs a fresh list (or swap two lists with `prev, cur = cur, prev`).

## Lab

- **1143 Longest Common Subsequence.** Write the two-row version from a blank file, then the full table with the walk back, and check the walk-back result is a subsequence of both inputs. Expected: O(mn) time, O(min(m, n)) space for the length; "dynamic" and "pragmatic" give 4 ("amic").
- **Shortest common supersequence length.** Using only `lcs_length`, compute the length of the shortest string that contains both "STONE" and "LONGEST" as subsequences. Expected: 5 + 7 - 3 = 9.

> [!know]
> You now know how to compare two sequences prefix by prefix, prove the match and mismatch cases, and walk back through the table to recover the subsequence itself.

=== primer | How does edit distance turn one word into another, and how do you recover the edits? | 15 min
goal: Compute the Levenshtein distance with a prefix-pair table, justify its three moves, and walk back to the actual insertions, deletions and substitutions
tag: dpseq-edit | Edit distance and alignment
link: Erickson, Algorithms ch. 3: Edit Distance (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=15 | 20 min: the 'Edit Distance' section, PDF pages 15-19: the alignment picture, 'Recursive Structure', 'Recurrence' and the filled table for ALGORITHM and ALTRUISTIC
link: Wikipedia: Levenshtein distance, Computation | https://en.wikipedia.org/wiki/Levenshtein_distance#Computation | 10 min: the iterative two-row version and the note on rebuilding the edit sequence
practice: 72

> [!key]
> D[i][j] is the fewest single-character edits (insert, delete, substitute) that turn a[:i] into b[:j]. If the last characters match, D[i][j] = D[i - 1][j - 1]; otherwise it is 1 plus the cheapest of substitute (D[i - 1][j - 1]), delete (D[i - 1][j]) and insert (D[i][j - 1]). The base cases are D[i][0] = i and D[0][j] = j. Fill row by row in **O(mn)**; walk back from the corner to recover the edits.

## Intuition

Write one word above the other and line them up column by column, allowing gaps:

```text
k  i  t  t  e  n  -
s  i  t  t  i  n  g
S  .  .  .  S  .  I        S = substitute, I = insert, . = keep
```

Every column of an **alignment** is one of four kinds: two equal letters (free), two different letters (a substitution), a letter of the first word over a gap (a deletion), or a gap over a letter of the second word (an insertion). The edit distance is the cheapest alignment. "kitten" becomes "sitting" in 3 edits, and no alignment does better.

## How it works

| Recipe step | Edit distance |
|---|---|
| Specification | D[i][j] = fewest edits turning a[:i] into b[:j] |
| Recurrence | D[i - 1][j - 1] if a[i - 1] == b[j - 1]; else 1 + min(D[i - 1][j - 1], D[i - 1][j], D[i][j - 1]) |
| Base cases | D[i][0] = i (delete everything), D[0][j] = j (insert everything) |
| Order | row by row; each cell needs up, left and up-left |
| Answer | D[m][n]; walk back for the operations |

### Why three moves are enough

Look at the **last column** of an optimal alignment of a[:i] and b[:j]. It is a pair (keep or substitute), a[i - 1] over a gap (delete) or a gap over b[j - 1] (insert). Remove that column and what remains is an alignment of smaller prefixes, and it must be an optimal one: if a cheaper alignment of those prefixes existed, gluing the last column back on would beat the optimum. So the answer is the best of the three ways to finish, each added to the optimal answer for what is left. That cut-and-paste argument is the whole proof.

### Recovering the edits

Keep the full table. From (m, n), ask which move produced the current value: the diagonal (free if the letters match, a substitution if not), the cell above plus 1 (delete `a[i - 1]`) or the cell on the left plus 1 (insert `b[j - 1]`). Step there and repeat until (0, 0), then reverse. Checking the diagonal first prefers substitutions over delete-plus-insert pairs, which reads more naturally.

### Variations you will meet

- **Only insertions and deletions** (no substitution): the distance is m + n - 2 x LCS, the diff tool's model.
- **Weighted edits**: give each operation (or each pair of letters) its own cost; the recurrence is unchanged except for the numbers. Needleman-Wunsch alignment in biology is exactly this, with a substitution score matrix and gap penalties.
- **Adjacent swaps** ("teh" for "the"): plain Levenshtein charges 2 for a swap. The optimal string alignment variant adds a fourth case, D[i - 2][j - 2] + 1 when the two last letters are swapped; the lab measures how much that helps a spell checker.
- **Small distances only**: if you only care whether the distance is at most k, cells with |i - j| > k can never matter, and you can stop as soon as a whole row exceeds k. The lab builds this.

## Cost

(m + 1)(n + 1) cells, constant work each: **O(mn) time**. The distance alone needs two rows, O(n) space; the edit script needs the full table, O(mn). For two random 2,000-letter strings the template takes about 3.5 seconds in pure Python. With a bound k, only about (2k + 1) cells per row matter, so the banded version is O(k x min(m, n)); PostgreSQL's `levenshtein_less_equal` is this idea in C.

## When to use it

Use edit distance when "how different are these two short sequences, letter by letter?" is the question: spelling correction, fuzzy search, record matching, measuring OCR or speech-recognition errors (word error rate is edit distance over words), and DNA or protein alignment.

| Need | Better tool |
|---|---|
| Is the distance exactly 0 or 1? | one pass with two pointers, O(m + n) |
| Diff two long files that are nearly equal | prefix/suffix trimming, then Myers' O((m + n)D) |
| Search a whole dictionary for close words | bound k, filter by length, then banded DP (the lab); BK-trees or SymSpell to avoid scanning |
| Similarity that "looks right" to people | `difflib.SequenceMatcher.ratio()` (not an edit count) |

## Worked trace

"kitten" (rows) into "sitting" (columns).

```steps
Base cases: row 0 costs j inserts, column 0 costs i deletes
          s  i  t  t  i  n  g
       {{0  1  2  3  4  5  6  7}}
    k  {{1}}
    i  {{2}}
    t  {{3}}
---
Row k: k differs from s, so 1 + min(diagonal 0, up 1, left 1) = 1 (substitute). Further right, inserts add 1 each
          s  i  t  t  i  n  g
       0  1  2  3  4  5  6  7
    k  1 {{1}} 2  3  4  5  6  7
---
Row i: (i, i) matches, so it copies the diagonal (k, s) = 1; the matching t's below copy the diagonal too
          s  i  t  t  i  n  g
       0  1  2  3  4  5  6  7
    k  1  1  2  3  4  5  6  7
    i  2  2 {{1}} 2  3  4  5  6
    t  3  3  2 {{1}} 2  3  4  5
    t  4  4  3  2 {{1}} 2  3  4
---
Row e: (e, i) differs: 1 + min(diagonal 1, up 2, left 2) = 2 (substitute e by i)
          s  i  t  t  i  n  g
    t  4  4  3  2  1  2  3  4
    e  5  5  4  3  2 {{2}} 3  4
---
Row n: (n, n) copies the diagonal 2; (n, g) = 1 + min(diagonal 3, up 4, left 2) = 3. Distance: 3
          s  i  t  t  i  n  g
    t  4  4  3  2  1  2  3  4
    e  5  5  4  3  2  2  3  4
    n  6  6  5  4  3  3 {{2  3}}
---
Walk back from 3: it came from the left (2 + 1), so insert g. (n, n) = 2 came free from the diagonal: keep n
          s  i  t  t  i  n  g
    e  5  5  4  3  2 {{2}} 3  4
    n  6  6  5  4  3  3 {{2  3}}
---
(e, i) = 2 came from diagonal 1 + 1: substitute e by i. Then t, t, i are free diagonals, and (k, s) = 1 is diagonal 0 + 1: substitute k by s
          s  i  t  t  i  n  g
       {{0}} 1  2  3  4  5  6  7
    k  1 {{1}} 2  3  4  5  6  7
    i  2  2 {{1}} 2  3  4  5  6
    t  3  3  2 {{1}} 2  3  4  5
    t  4  4  3  2 {{1}} 2  3  4
    e  5  5  4  3  2 {{2}} 3  4
---
Reversed, the operations are the alignment from the Intuition section
    sub k->s, keep i, keep t, keep t, sub e->i, keep n, insert g
```

## Template

```python
def edit_distance(a, b):
    """Levenshtein distance: fewest insertions, deletions and substitutions turning a into b."""
    prev = list(range(len(b) + 1))           # row 0: build b[:j] from nothing with j inserts
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)             # column 0: delete all i characters
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1]
            else:
                cur[j] = 1 + min(prev[j - 1],    # substitute a[i-1] -> b[j-1]
                                 prev[j],        # delete a[i-1]
                                 cur[j - 1])     # insert b[j-1]
        prev = cur
    return prev[-1]


def edit_script(a, b):
    """The operations of one optimal alignment, in order: (op, char_from_a, char_from_b)."""
    m, n = len(a), len(b)
    D = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        D[i][0] = i
    for j in range(n + 1):
        D[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            same = a[i - 1] == b[j - 1]
            D[i][j] = min(D[i - 1][j - 1] + (not same), D[i - 1][j] + 1, D[i][j - 1] + 1)
    ops, i, j = [], m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i][j] == D[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            ops.append(("keep" if a[i - 1] == b[j - 1] else "sub", a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and D[i][j] == D[i - 1][j] + 1:
            ops.append(("del", a[i - 1], ""))
            i -= 1
        else:
            ops.append(("ins", "", b[j - 1]))
            j -= 1
    return ops[::-1]
```

`edit_script` uses the full-table form of the recurrence (`not same` is 0 or 1), which is equivalent: when the letters match, the free diagonal is never worse than the other two moves.

## Pitfalls

- **Base row and column of zeros.** D[0][j] must be j (you have to insert j letters), not 0. With zeros the distance from "" to "abc" comes out as 0.
- **Charging for a match.** On equal letters the diagonal is free; writing `1 + min(...)` unconditionally gives 1 for two identical one-letter words.
- **Confusing insert and delete.** Moving up (i - 1) consumes a letter of `a` without producing one: that is a deletion from `a`. Swap them and your script turns b into a.
- **Walking back without the full table.** The two-row version cannot rebuild the edits.
- **Unicode.** "é" can be one code point or "e" plus a combining accent; normalise both strings with `unicodedata.normalize("NFC", s)` first, or a visually equal pair has distance 1 or 2.

## Check yourself

Q: Compute the distance from "flaw" to "lawn" and the operations `edit_script` returns.
A: 2: delete f, keep l, keep a, keep w, insert n. A substitution-based alignment (f to l, l to a, a to w, w to n) would cost 4.

Q: Why is D[i][0] = i rather than 0, and what does the cell D[3][0] mean?
A: D[3][0] is the cost of turning the first three letters of a into the empty string, which takes exactly three deletions. A 0 there would claim you can erase letters for free, and every distance computed from that column would be too small.

Q: A form must flag names whose distance to a known customer is at most 1, for a million lookups a day. Which approach do you choose?
A: Not the full table. Check distance at most 1 directly in O(m + n): if the lengths differ by more than 1, no; otherwise walk both strings with two pointers, allow one mismatch (skipping a letter in the longer string when the lengths differ) and stop at the second. Or use the banded `within(a, b, 1)` from the lab, which does the same work in table form.

Q: A colleague's `edit_distance` returns 1 for ("a", "a"). What is the bug?
A: The match case is missing: the code always takes `1 + min(...)`. When `a[i - 1] == b[j - 1]` the cell must copy the diagonal for free.

## Lab

- **72 Edit Distance.** Write the two-row version from a blank file, then `edit_script`, and apply the script to `a` to check you really get `b`. Expected: O(mn) time, O(n) space for the distance; "sunday" to "saturday" is 3 (insert a, insert t, substitute n by r), "snow" to "slow" is 1, "" to "abc" is 3.
- **Stress test.** Compare `edit_distance` with a plain recursive version (the recurrence without a table) on 500 random strings of length up to 6 over "abc". Expected: no mismatches, and the recursive version is visibly slower already at length 8.

> [!know]
> You now know how to compute edit distance, prove its three moves with the last-column argument, and recover an optimal alignment from the table.

=== lab | Spelling suggestions with edit distance | 50 min
goal: Build a spelling suggester over 50,000 words, make it several times faster with a length filter and a banded early-exit DP, and compare it with difflib
link: PostgreSQL docs: fuzzystrmatch, levenshtein | https://www.postgresql.org/docs/current/fuzzystrmatch.html#FUZZYSTRMATCH-LEVENSHTEIN | 5 min: the levenshtein section; levenshtein_less_equal is the same banded, early-exit idea you build here, in C inside a database
link: Peter Norvig: How to Write a Spelling Corrector | https://norvig.com/spell-correct.html | 20 min: read up to the evaluation; his corrector generates every string within 2 edits instead of scanning the dictionary, the opposite trade-off to this lab

You will build the core of a spell checker: given a misspelt word, rank dictionary words by edit distance (closest first, then most common). The naive version scans 50,000 words with a full table each; you will make it faster without changing a single answer, measure it, and compare it with Python's `difflib.get_close_matches`. The diff tool is this stage's project, so this lab stays with words.

## Setup

- Python 3.10 or later, no packages. The script downloads Peter Norvig's word-frequency list (about 5 MB, the 333,333 most common English words with counts from a web corpus) once, and keeps the top 50,000.
- Reuse your `dsakit` stress harness from the correctness module if you have it; the steps include a stand-alone version.

## Steps

1. Save this as `spell_lab.py`. It contains the full-table distance from the edit distance card, a banded version with early exit, four suggesters and a seeded test set of 200 typos (one or two random edits of common words: substitute, delete, insert or swap two neighbours).

```python
import difflib
import random
import time
import urllib.request
from pathlib import Path

# 1. The dictionary: the 50,000 most frequent English words, with their counts.
path = Path("count_1w.txt")
if not path.exists():
    urllib.request.urlretrieve("https://norvig.com/ngrams/count_1w.txt", path)
rows = [line.split("\t") for line in path.read_text().splitlines()[:50_000]]
WORDS = [w for w, _ in rows]
FREQ = {w: int(c) for w, c in rows}


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1]
            else:
                cur[j] = 1 + min(prev[j - 1], prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


def within(a, b, k):
    """Edit distance if it is at most k, else None: only the band |i - j| <= k, with early exit."""
    if abs(len(a) - len(b)) > k:
        return None
    BIG = k + 1
    prev = [j if j <= k else BIG for j in range(len(b) + 1)]
    for i in range(1, len(a) + 1):
        cur = [BIG] * (len(b) + 1)
        if i <= k:
            cur[0] = i
        lo, hi = max(1, i - k), min(len(b), i + k)
        for j in range(lo, hi + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1]
            else:
                cur[j] = 1 + min(prev[j - 1], prev[j], cur[j - 1])
            cur[j] = min(cur[j], BIG)
        if min(cur[max(0, lo - 1):hi + 1]) > k:
            return None
        prev = cur
    return prev[-1] if prev[-1] <= k else None


def rank(scored, n):
    """Closest first, then the more common word."""
    return [w for d, w in sorted(scored, key=lambda dw: (dw[0], -FREQ[dw[1]]))[:n]]


def suggest_full(word, k=2, n=5):
    return rank([(d, w) for w in WORDS if (d := edit_distance(word, w)) <= k], n)


def suggest_filtered(word, k=2, n=5):
    return rank([(d, w) for w in WORDS
                 if abs(len(w) - len(word)) <= k and (d := edit_distance(word, w)) <= k], n)


def suggest_banded(word, k=2, n=5):
    return rank([(d, w) for w in WORDS if (d := within(word, w, k)) is not None], n)


def suggest_difflib(word, n=5):
    return difflib.get_close_matches(word, WORDS, n=n, cutoff=0.75)


# 2. Test set: real words with one or two random typos (seeded, so the run is repeatable).
rng = random.Random(42)


def typo(w):
    i = rng.randrange(len(w))
    c = rng.choice("abcdefghijklmnopqrstuvwxyz")
    kind = rng.choice(["sub", "del", "ins", "swap"])
    if kind == "sub":
        return w[:i] + c + w[i + 1:]
    if kind == "del":
        return w[:i] + w[i + 1:]
    if kind == "ins":
        return w[:i] + c + w[i:]
    i = min(i, len(w) - 2)
    return w[:i] + w[i + 1] + w[i] + w[i + 2:]


targets = rng.sample([w for w in WORDS[:10_000] if len(w) >= 5], 200)
tests = []
for w in targets:
    bad = typo(w)
    if rng.random() < 0.3:
        bad = typo(bad)
    tests.append((bad, w))


# 3. Time each method and score it: is the intended word first, or anywhere in the top 5?
def evaluate(name, fn, cases):
    t0 = time.perf_counter()
    got = [fn(bad) for bad, _ in cases]
    ms = (time.perf_counter() - t0) / len(cases) * 1000
    top1 = sum(g[:1] == [w] for g, (_, w) in zip(got, cases)) / len(cases)
    top5 = sum(w in g for g, (_, w) in zip(got, cases)) / len(cases)
    print(f"{name:9} {ms:8.1f} ms/query   top-1 {top1:.0%}   top-5 {top5:.0%}")
    return got


if __name__ == "__main__":
    few = tests[:20]
    full = evaluate("full", suggest_full, few)
    filt = evaluate("filtered", suggest_filtered, few)
    band = evaluate("banded", suggest_banded, few)
    assert full == filt == band, "the three exact methods must agree"
    band = evaluate("banded", suggest_banded, tests)
    diff = evaluate("difflib", suggest_difflib, tests)
    for (bad, w), b, d in list(zip(tests, band, diff))[:6]:
        print(f"{bad:>12} (meant {w}): banded {b[:3]}  difflib {d[:3]}")
```

2. **Predict, then run.** Before running, write down how much faster you expect the length filter and the banded version to be than the full scan, and why. Then run `python spell_lab.py` (a few minutes: the full scan is slow on purpose, so it only gets 20 queries). Copy the timing table.
3. **Explain the speed-ups.** The length filter is safe because the distance is at least the length difference. The band is safe because a cell with |i - j| > k needs at least |i - j| insertions or deletions. The early exit is safe because row minimums never decrease from one row to the next. Write one sentence for each in your journal.
4. **Stress-test the fast version.** The assertion in the script only covers 20 words. Add a random tester: for 2,000 pairs of random strings of length 0 to 12 over "abcd" and every k from 0 to 4, check `within(a, b, k) == (d if d <= k else None)` where `d = edit_distance(a, b)`, and stop at the first mismatch. Then break `within` on purpose (drop the `min(cur[j], BIG)` clamp, or use `cur[lo:hi + 1]` in the early-exit test) and watch the tester catch it.
5. **Vary k.** Re-run the banded suggester on the 200 typos with k = 1 and k = 3. Record time per query and top-5 accuracy.
6. **Count a swap as one edit.** Two neighbouring letters swapped cost 2 in Levenshtein. Add the optimal-string-alignment case to `within`: keep the row before `prev` as `before`, and when `a[i - 1] == b[j - 2]` and `a[i - 2] == b[j - 1]`, also allow `before[j - 2] + 1`. Stress-test it against a full-table version first, then measure accuracy again.
7. **Read difflib's trick.** Open `difflib.get_close_matches` (run `import inspect, difflib; print(inspect.getsource(difflib.get_close_matches))`) and find the two cheap upper bounds it checks before the expensive `ratio()`. Compare them with your length filter.

## What you should see

Timings below are from one machine (pure Python 3.12); yours will differ, but the ratios should be similar.

| Method (k = 2) | Time per query | Top-1 | Top-5 |
|---|---|---|---|
| Full table against all 50,000 words | about 2,100 ms | same answers as banded | same answers as banded |
| Length filter, then full table | about 1,100 ms | same | same |
| Banded with early exit | about 700 ms | 76% | 88% |
| `difflib.get_close_matches` (cutoff 0.75) | about 230 ms | 80% | 94% |

- The three exact methods return identical lists (the assertion passes): the speed-ups change the cost, never the answer. The length filter alone halves the time because about half of the dictionary is too long or too short; the band then skips most cells, and the early exit rejects most of the remaining words after three or four rows (k + 1 is the earliest possible).
- k = 1 is about three times faster than k = 2 but finds the intended word in the top 5 only about 57% of the time, because 30% of the test words have two typos. k = 3 finds about 90% but takes roughly twice as long as k = 2 and returns more noise.
- Counting a swap as one edit lifts the banded suggester to about 86% top-1 and 95% top-5 at the same speed: real typing errors are often transpositions, which plain Levenshtein overcharges.
- difflib is faster because `get_close_matches` rejects most words with `real_quick_ratio()` (lengths only) and `quick_ratio()` (letter counts) before running its expensive matcher, the same "cheap bound first" idea as your length filter. Its scores are not edit distances, so its ranking differs on close calls.
- Every method still scans the whole dictionary. To go further you index it: Norvig's corrector generates candidate strings instead, SymSpell precomputes deletions, and a BK-tree prunes by the triangle inequality.

## Check yourself

Q: Why can the length filter never remove a word that the full scan would suggest?
A: Every insertion or deletion changes the length by one and a substitution does not change it, so turning a word of length m into one of length n needs at least |m - n| edits. If |m - n| > k the distance is above k and the full scan would have rejected the word too.

Q: You "simplify" `within` by creating each row as `[0] * (len(b) + 1)` instead of `[BIG] * (len(b) + 1)`. What does `within("aaa", "b", 2)` return, and why?
A: 1 instead of None (the true distance is 3). Cells outside the band are never computed, so they keep their initial value, and a 0 there looks like a free way to reach that cell. In row 3, column 0 (which should cost three deletions) stays 0, the band reads it, and the distance collapses. Outside the band the placeholder must be something above k, which is what `BIG` is.

> [!know]
> You now know how to turn edit distance into a practical suggester: prune with a cheap bound, band the table, exit early, stress-test the fast version against the slow one, and measure what each change buys.

=== primer | How do you match or count one sequence inside another (distinct subsequences, wildcards, interleaving)? | 14 min
goal: Model "does it match?" and "in how many ways?" questions over two sequences as prefix-pair tables, writing the transition by asking where the last character came from
tag: dpseq-match | Matching and counting over two sequences
link: Wikipedia: Matching wildcards | https://en.wikipedia.org/wiki/Matching_wildcards#Definition | 10 min: 'Definition' (the prefix recurrence this card builds) and 'Recursive algorithms' (why naive recursion on * is exponential, and how the wildmatch code in Git and rsync avoids it)
practice: 97, 10

> [!key]
> The prefix-pair table from LCS answers more than "how long". Let M[i][j] describe the first i items of one sequence against the first j of the other, then ask **how the last character could have been produced**. List every possibility: for a yes/no question combine them with **or**, for a count **add** them. Distinct subsequences, wildcard and regex matching, and interleaving are all this one move, each O(mn).

## Intuition

How many ways can you pick "bc" out of "abcbc", keeping order? Read "abcbc" left to right and keep a tally for each prefix of the target: how many ways you can already spell "" (always 1), "b" and "bc". Every time you read a b, each way of spelling "" becomes a way of spelling "b". Every time you read a c, each way of spelling "b" becomes a way of spelling "bc". The tally for "bc" at the end is the answer, 3. No list of positions was ever built: the counts carried all the information.

## How it works

### Counting: distinct subsequences

Let W[i][j] be the number of ways t[:j] occurs as a subsequence of s[:i]. The last character of s, `s[i - 1]`, is either not used (W[i - 1][j] ways) or, if it equals `t[j - 1]`, used as the final character of t (W[i - 1][j - 1] ways). Those cases are disjoint, so add them:

W[i][j] = W[i - 1][j] + (W[i - 1][j - 1] if s[i - 1] == t[j - 1] else 0), with W[i][0] = 1 (the empty target occurs once) and W[0][j] = 0 for j > 0.

In one row, sweep j **downwards**, exactly like the 0/1 knapsack later in this module: going down, `ways[j - 1]` still means "before this character of s", so each character of s is used at most once per occurrence.

### Yes or no: wildcard matching

`?` matches any one character and `*` matches any run, including the empty one. Let M[i][j] be "pattern p[:j] matches text s[:i]". Ask what the last pattern symbol did:

- `p[j - 1]` is a letter or `?`: it consumed `s[i - 1]` (if they fit), so M[i - 1][j - 1].
- `p[j - 1]` is `*`: either it matched nothing (M[i][j - 1]) or it swallowed `s[i - 1]` and may swallow more (M[i - 1][j], the star stays available).

Base: M[0][0] is true, an empty pattern matches no non-empty text, and M[0][j] is true only while the pattern so far is all stars.

### Two sources: interleaving

Is s3 an interleaving of s1 and s2 (both kept in order, merged)? State: I[i][j] = "s1[:i] and s2[:j] can merge into s3[:i + j]". The last character of s3[:i + j] came either from s1 or from s2, so two cases joined by **or**. The table matters because the greedy rule "take from s1 whenever it fits" fails: with s1 = "aa", s2 = "ab" and s3 = "abaa", greedy takes the first a from s1, then needs b from s1 and is stuck, yet taking "ab" from s2 first works. You will write this one in the Lab.

### Regular expressions with `.` and `*`

Here `*` repeats the *previous* element, so `x*` is one unit: either skip the whole unit (j - 2) or, if x fits `s[i - 1]`, consume one character and keep the unit (i - 1, j). It is the wildcard table with a different last-symbol analysis: the stretch problem in the Lab.

## Cost

Each table has (m + 1)(n + 1) cells with O(1) work: **O(mn) time**, and O(n) space with one rolling row (the full table only if you need to reconstruct a match). Compare that with naive backtracking: a recursive matcher that tries every split for each `*` can take exponential time on patterns with many stars that almost match, which is exactly the problem the Wikipedia section describes in old shell and FTP-server glob code. Python's `re` module is also a backtracking engine, so some regular expressions take exponential time: `re.fullmatch(r"(a*)*b", "a" * 24)` runs for about 3 seconds, and each extra a roughly doubles it. A table never does that.

## When to use it

| Question | State and combine |
|---|---|
| Is t a subsequence of s? | no table: two pointers, O(m + n) |
| How many times does t occur as a subsequence of s? | W[i][j], add the two cases |
| Does a glob or simple regex match the whole string? | M[i][j], or the cases for the last pattern symbol |
| Is s3 a merge of s1 and s2? | I[i][j] over the two sources, or |
| Longest or cheapest way to align them | LCS or edit distance (previous cards), max or min |

Recognise it by two sequences plus a question about *all* ways of lining them up. If you only need one left-to-right scan with no choices (plain subsequence check), skip the table.

## Worked trace

Count the occurrences of t = "bc" in s = "abcbc" with one row, `ways[j]` = ways to spell t[:j] so far, j swept downwards.

```steps
Start: the empty prefix of t can be spelt in exactly one way, the others in none
    t prefix   ""   "b"  "bc"
    ways        1    0    0
---
Read a: it matches neither b nor c, so nothing changes
    ways        1    0    0
---
Read b (j = 2: c != b, skip; j = 1: b == b): ways[1] += ways[0]
    ways        1  {{1}}   0
---
Read c (j = 2: c == c): ways[2] += ways[1]. One way so far: b1 c2
    ways        1    1  {{1}}
---
Read b: ways[1] += ways[0]. Two b's now available to start "bc"
    ways        1  {{2}}   1
---
Read c: ways[2] += ways[1] = 1 + 2. Answer 3: b1 c2, b1 c4, b3 c4
    ways        1    2  {{3}}
```

Had j been swept upwards, a single character could extend a prefix it had just created: with s = "bb" and t = "bb", the upward sweep counts 3 instead of 1.

## Template

```python
def count_subsequences(s, t):
    """How many ways t can be picked out of s as a subsequence (positions differ)."""
    ways = [1] + [0] * len(t)          # ways[j]: ways to form t[:j] from the part of s read so far
    for ch in s:
        for j in range(len(t), 0, -1):  # right to left: this ch extends each t-prefix at most once
            if t[j - 1] == ch:
                ways[j] += ways[j - 1]
    return ways[-1]


def wildcard_match(s, p):
    """Does pattern p match all of s? '?' is any one character, '*' any run, even empty."""
    m, n = len(s), len(p)
    M = [[False] * (n + 1) for _ in range(m + 1)]   # M[i][j]: p[:j] matches s[:i]
    M[0][0] = True
    for j in range(1, n + 1):
        M[0][j] = M[0][j - 1] and p[j - 1] == "*"    # only stars match the empty string
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j - 1] == "*":
                M[i][j] = M[i][j - 1] or M[i - 1][j]  # star matches nothing, or eats s[i-1]
            else:
                M[i][j] = M[i - 1][j - 1] and p[j - 1] in ("?", s[i - 1])
    return M[m][n]
```

`wildcard_match` agrees with the standard library's `fnmatch.fnmatchcase` on patterns made of letters, `?` and `*` (the stress test in the verification compares them on thousands of random cases); `fnmatch` translates the pattern into a regular expression instead.

## Pitfalls

- **Sweeping upwards in a one-row count**, so a character of s is used twice (the "bb" example above).
- **The base row of a match table.** Only leading stars match the empty text: M[0][j] must stop being true at the first non-star symbol.
- **Treating `*` as "one or more"**, or forgetting that in regex syntax the star belongs to the previous symbol.
- **Huge counts.** Distinct-subsequence counts grow exponentially (s = "aaaa...a", t = "aaa"); in C++ or Java use the problem's modulus or a 64-bit type; Python is fine.
- **Reaching for the table when a scan is enough.** "Is t a subsequence of s?" is two pointers.

## Check yourself

Q: Does `wildcard_match("axxbc", "a*b?")` return True? Which cells make it so?
A: True. `a` matches `a`, the star swallows "xx" (moving down its column), `b` matches `b` and `?` matches `c`. In the table, M[1][1], M[1][2], M[2][2], M[3][2], M[4][3] and M[5][4] are all true along that route.

Q: Why does the count recurrence add W[i - 1][j] and W[i - 1][j - 1] rather than take a maximum?
A: Because the two cases (the last character of s is not used, or it is used as the last character of t) never describe the same occurrence, and together they cover every occurrence. Disjoint and exhaustive cases are added when counting; max or min is for optimising.

Q: In the interleaving problem, why does "take from s1 whenever its next character fits" fail, and what does the table do instead?
A: When both s1 and s2 offer the same next character, the choice affects what remains possible later, and a greedy choice can strand you (s1 = "aa", s2 = "ab", s3 = "abaa"). The table keeps every (i, j) split that is still possible, so it never commits to one choice.

## Lab

- **97 Interleaving String.** Define I[i][j] as above, write the two cases, and roll it to one row. Expected: O(mn) time, O(n) space; with s1 = "aa" and s2 = "ab", s3 = "abaa" gives true (all of s2 first) and "aaba" gives true; with s1 = "ab" and s2 = "ac", "abca" gives false.
- **10 Regular Expression Matching** (stretch). Treat `x*` as one unit with two options, and be careful with the base row (patterns like `a*b*` match the empty string). Expected: O(mn) time; "aaab" matches "a*.b" (true), "ab" against ".*c" is false, "abcd" against "d*" is false. Compare your answers with `re.fullmatch` on random small cases.

> [!know]
> You now know how to write a matching or counting table over two sequences by asking where the last character came from, and why such tables beat backtracking matchers.

=== primer | How do range tables solve palindrome problems? | 13 min
goal: Solve palindromic subsequence and substring questions with a table over ranges s[i..j], filled in an order that respects its dependencies
tag: dpseq-pal | Palindromic range DP
link: USACO Guide: Range DP | https://usaco.guide/gold/dp-ranges#tutorial | 10 min: the 'Tutorial' section, dp over every subarray [l, r] processed by increasing length, the general form of this card's tables
practice: 516

> [!key]
> For palindromes the natural subproblem is a **range** s[i..j]. Its answer comes from the range with both ends removed (when the two end characters match) or with one end removed (when they do not). Fill the table so that shorter ranges are ready first: by increasing length, or with **i descending and j ascending**. That gives n(n + 1) / 2 states with O(1) work each: **O(n^2)**.

## Intuition

A palindrome is built from the outside in. Peel "racecar": the outer r's match, leaving "aceca"; the a's match, leaving "cec"; then "e". So the question "how long a palindrome can I find inside s[i..j]?" only depends on smaller ranges inside it. If the two ends are equal, they can wrap whatever is best inside. If they are not, at least one of them is not part of the answer, so drop the end that hurts less.

## How it works

### Longest palindromic subsequence

| Recipe step | LPS |
|---|---|
| Specification | P[i][j] = length of the longest palindromic subsequence of s[i..j] (inclusive) |
| Recurrence | P[i + 1][j - 1] + 2 if s[i] == s[j]; else max(P[i + 1][j], P[i][j - 1]) |
| Base cases | P[i][i] = 1; an empty range (i > j) is 0 |
| Order | i from n - 1 down to 0, and for each i, j from i + 1 up to n - 1 |
| Answer | P[0][n - 1] |

The matching case is safe for the same reason as in LCS: if s[i] == s[j], some longest palindrome inside uses both ends as its outer pair (if it used only one of them, swap that one for the other end: same length; if it used neither, wrap them around it: longer). So LPS(s) also equals the LCS length of s and reversed(s), a useful cross-check.

### Which cells are ready?

P[i][j] reads the cell below it (i + 1, j), the cell to its left (i, j - 1) and the one diagonally down-left (i + 1, j - 1):

```text
            j-1     j
  i          <-   [i, j]        left: same i, shorter range
  i+1      [ / ]    v           below and down-left: larger i
```

So process rows from the **bottom up** (i descending) and each row **left to right** (j ascending). Filling top to bottom reads row i + 1 before it exists: Python happily reads the zeros and returns a wrong answer without any error.

### The boolean palindrome table

is_pal[i][j] = (s[i] == s[j]) and (j - i < 2 or is_pal[i + 1][j - 1]): same order, same shape. It answers "is this substring a palindrome?" in O(1) after O(n^2) work, which is exactly what partitioning a string into palindromes needs (the segmentation card).

### Related questions

- **Fewest insertions to make s a palindrome**: n - LPS(s). The characters you never insert must already form a palindromic subsequence (1312 in the bank).
- **Longest palindromic substring** and **counting palindromic substrings**: the boolean table works, but expanding around each of the 2n - 1 centres (the string algorithms module) does it in O(n^2) time with O(1) space.

## Cost

There are n(n + 1) / 2 ranges with i <= j, each filled in O(1): **O(n^2) time**. The full table is O(n^2) memory, n = 10,000 means 10^8 cells, far too many Python ints. Because row i only reads rows i and i + 1, LPS can keep **two rows, O(n) space**; the boolean table is usually needed whole, so keep it only when you will query many ranges.

## When to use it

Cues: palindromes, "remove from either end", or any question about a contiguous range whose answer is assembled from smaller ranges inside it.

| Problem | Best tool |
|---|---|
| Longest palindromic subsequence | range DP (this card), or LCS with the reverse |
| Longest palindromic substring, count of palindromic substrings | expand around centres, O(n^2) time, O(1) space; Manacher for O(n) |
| Is s[i..j] a palindrome, for many (i, j) | the boolean table, O(1) per query |
| Split into fewest palindromes | boolean table plus a prefix DP (segmentation card) |
| Ranges where you try every split point (merging, bursting) | interval DP, the advanced DP module |

## Worked trace

Longest palindromic subsequence of s = "abcbda", shown range length by range length (the template's bottom-up row order computes the same cells, just in a different sequence). Row i, column j holds P[i][j].

```steps
Length 1: every single character is a palindrome of length 1
          a  b  c  b  d  a
       a {{1}}
       b    {{1}}
       c       {{1}}
       b          {{1}}
       d             {{1}}
       a                {{1}}
---
Length 2: no two neighbours are equal, so each is max(drop left, drop right) = 1
          a  b  c  b  d  a
       a  1 {{1}}
       b     1 {{1}}
       c        1 {{1}}
       b           1 {{1}}
       d              1 {{1}}
---
Length 3: "bcb" has equal ends: inner "c" (1) + 2 = 3. The others stay 1
          a  b  c  b  d  a
       a  1  1 {{1}}
       b     1  1 {{3}}
       c        1  1 {{1}}
       b           1  1 {{1}}
---
Length 4: "abcb" = max(P[b..b] = 3, P[a..c] = 1) = 3; "bcbd" = 3; "cbda" = 1
          a  b  c  b  d  a
       a  1  1  1 {{3}}
       b     1  1  3 {{3}}
       c        1  1  1 {{1}}
---
Length 5: "abcbd" and "bcbda" both inherit 3 from "bcbd"
          a  b  c  b  d  a
       a  1  1  1  3 {{3}}
       b     1  1  3  3 {{3}}
---
Length 6: the ends are both a: inner "bcbd" (3) + 2 = 5. Answer: 5, for example "abcba"
          a  b  c  b  d  a
       a  1  1  1  3  3 {{5}}
```

## Template

```python
def longest_pal_subseq(s):
    """Length of the longest palindromic subsequence, by a range table."""
    n = len(s)
    if n == 0:
        return 0
    P = [[0] * n for _ in range(n)]          # P[i][j]: answer for s[i..j] inclusive
    for i in range(n - 1, -1, -1):           # i descending so P[i+1][...] is ready
        P[i][i] = 1
        for j in range(i + 1, n):            # j ascending so P[i][j-1] is ready
            if s[i] == s[j]:
                P[i][j] = P[i + 1][j - 1] + 2  # for j == i+1 this reads P[i+1][i] == 0
            else:
                P[i][j] = max(P[i + 1][j], P[i][j - 1])
    return P[0][n - 1]


def palindrome_table(s):
    """is_pal[i][j] is True when s[i..j] (inclusive) reads the same both ways."""
    n = len(s)
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            is_pal[i][j] = s[i] == s[j] and (j - i < 2 or is_pal[i + 1][j - 1])
    return is_pal
```

The comment on the matching line matters: when j = i + 1 the inner range is empty, and the cell P[i + 1][i] (below the diagonal) is never written, so it is still 0, which is the right value for an empty range.

## Pitfalls

- **Top-down row order.** `for i in range(n)` reads row i + 1 before filling it; with a zero-initialised table nothing crashes, the answer is just wrong.
- **The two-character case.** "aa" must give 2: the inner range is empty and must read as 0 (or handle j - i < 2 explicitly, as the boolean table does).
- **Subsequence versus substring.** "Longest palindromic substring" needs contiguity; the subsequence recurrence happily skips characters.
- **Quadratic memory.** At n = 5,000 the full table already holds 25 million entries. Roll to two rows when you only need the length.

## Check yourself

Q: Fill in: for s = "abcbda", what is P[1][3] and why, and what is the fewest number of characters you must insert to make "abcbda" a palindrome?
A: P[1][3] = 3: the range "bcb" has equal ends, so 1 (for "c") + 2. The whole string has LPS 5, so 6 - 5 = 1 insertion suffices, for example a d after the first a: "adbcbda".

Q: Why must i run from n - 1 down to 0? Name a cell that would be read too early otherwise.
A: P[i][j] reads P[i + 1][j] and P[i + 1][j - 1], which belong to row i + 1. With i ascending, computing P[0][2] reads P[1][2] and P[1][1] before row 1 exists, so it sees zeros.

Q: You need the number of palindromic substrings of a 2,000-character string. Range table or centre expansion?
A: Centre expansion: for each of the 2n - 1 centres, expand while the ends match, counting as you go. Same O(n^2) time in the worst case but O(1) memory instead of a 4-million-cell table, and it stops early on most centres of a typical string. On "abcbda" both methods count 7.

## Lab

- **516 Longest Palindromic Subsequence.** Write the range table, then roll it to two rows. Cross-check with `lcs_length(s, s[::-1])` on random strings. Expected: O(n^2) time, O(n) space after rolling; "character" gives 5 ("carac"), "agbcba" gives 5 ("abcba").
- **Count palindromic substrings with the boolean table.** Sum `palindrome_table(s)` over all i <= j, then rewrite it with centre expansion and compare on random strings. Expected: "abcbda" has 7 (six single letters and "bcb").

> [!know]
> You now know how to set up a range table for palindrome questions, prove its matching case, and fill it in an order where every cell's inputs are ready.

=== primer | How does 0/1 knapsack work, and why does the one-row loop run backwards? | 15 min
goal: Solve 0/1 knapsack, subset sum and equal partition with a capacity table, compress it to one row with a downward loop, rebuild the chosen items, and explain pseudo-polynomial time
tag: dpseq-knap01 | 0/1 knapsack and subset sum
link: cp-algorithms: Knapsack problem | https://cp-algorithms.com/dynamic_programming/knapsack.html#0-1-knapsack | 10 min: the '0-1 Knapsack' section: the 2D table, then the one-row version iterated from high capacity to low
link: MIT 6.006 lecture 18 notes: Pseudopolynomial (PDF) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/mit6_006s20_lec18.pdf#page=4 | 10 min: 'Subset Sum' and 'Pseudopolynomial', PDF pages 4-6: why O(nS) is not polynomial in the size of the input
practice: 416, 494

> [!key]
> For each item you either take it or skip it, once. Let best[i][c] be the best value using the first i items within capacity c: best[i][c] = max(best[i - 1][c], best[i - 1][c - w] + v). That is **O(n x C)** time. One row is enough if you loop the capacity **downwards**, so best[c - w] still means "without this item"; loop upwards and an item can be taken again and again. Subset sum and equal partition are the yes/no version of the same table.

## Intuition

You have a 10 kg bag and three items: a 6 kg item worth 30 and two 5 kg items worth 20 each. "Best value per kilogram first" takes the 6 kg item (5 per kg) and then nothing else fits: 30. Taking both 5 kg items gives 40. Each item is a yes/no choice, and an early choice changes what fits later, so no simple rule works (the next module shows exactly when such rules are safe). Trying all 2^n subsets works but explodes at n = 40.

The saving insight: after deciding the first i items, **the future only cares about how much capacity is left**, not which items used it. Two different subsets that leave the same capacity are interchangeable, so keep only the best value for each capacity. That collapses 2^n subsets into at most C + 1 states per item.

## How it works

| Recipe step | 0/1 knapsack |
|---|---|
| Specification | best[i][c] = most value from items 0..i-1 with total weight at most c |
| Recurrence | best[i][c] = max(best[i - 1][c] (skip item i - 1), best[i - 1][c - w] + v (take it, if w <= c)) |
| Base cases | best[0][c] = 0: no items, no value |
| Order | items in any fixed order; for each item, every capacity |
| Answer | best[n][C]; walk back to list the items |

**Rebuilding the choice:** walk the items backwards from capacity C. If best[i][c] differs from best[i - 1][c], item i - 1 must have been taken (skipping it would have kept the value), so record it and subtract its weight from c.

### From a table to one row

Row i only reads row i - 1, so one list can hold both, provided each cell reads the *old* values. Cell c reads cells c and c - w, which are at or to the left of c. Sweep **from high capacity to low**: when you update c, every cell left of it is still the old row, so the item cannot be used twice. Sweep from low to high and best[c - w] may already include this item, which is precisely the unbounded knapsack of the next card. The trace below shows both.

### Subset sum and equal partition

"Can some subset of these numbers sum to exactly S?" is a knapsack where the weight is the value and the question is yes/no: reach[c] = reach[c] or reach[c - x], swept downwards. In Python, a big integer is a faster bitset: bit s set means "sum s is reachable", and `bits |= bits << x` adds x to every reachable sum at once, with the shifting done in C. On 200 numbers up to 100 it is over a thousand times faster than the list loop. **Equal partition** is subset sum to total / 2 (impossible if the total is odd). The **counting** version (how many subsets reach S) replaces `or` by `+` with reach[0] = 1; the derive problem in the Lab reduces to it.

### Pseudo-polynomial: when the table is too big

O(n x C) looks polynomial, but C is a *number* in the input, written in about log2(C) bits. Double the number of digits of C and the table squares in size. That is **pseudo-polynomial** time, and knapsack is NP-hard in general, so no algorithm is known that is polynomial in the input size. Practical escapes:

- **Values small, weights huge**: swap the roles, minw[v] = least weight achieving value exactly v (AtCoder Knapsack 2 in the bank).
- **n up to about 40**: meet in the middle, enumerating 2^(n/2) subsets of each half and combining with sorting and binary search.
- **Large real instances**: integer-programming or branch-and-bound solvers, such as OR-Tools' knapsack solver.

## Cost

n items x (C + 1) capacities, constant work each: **O(nC) time**. The full table is O(nC) memory (needed to list the chosen items); the one-row version is **O(C)**. The bitset subset sum is still O(nS) bit operations, but 30 to 64 bits are processed per machine operation, so the constant is tiny.

## When to use it

Cues: items with a size and (optionally) a value, a capacity or exact target, each item used **at most once**: "choose a subset", "split into two groups", "assign + or - to each number", "can we reach exactly".

| Variant | Approach |
|---|---|
| Each item at most once, small integer capacity | this card, downward loop |
| Unlimited copies of each item | unbounded knapsack, upward loop (next card) |
| Items can be split (take 40% of an item) | fractional knapsack: greedy by value per weight (next module) |
| Capacity around 10^9, n small | meet in the middle, or swap the roles of weight and value |
| Many constraints, real budgets | an integer-programming solver |

## Worked trace

Items A (weight 2, value 3) and B (weight 3, value 4), capacity 5. First the bug, then the fix.

```steps
Start: best[c] = best value within capacity c, no items yet
    c        0  1  2  3  4  5
    best     0  0  0  0  0  0
---
WRONG, upward loop for A: c = 2 and c = 3 read best[0], best[1] (old zeros): 3, 3
    c        0  1  2  3  4  5
    best     0  0 {{3  3}} 0  0
---
WRONG, continued: c = 4 reads best[2], which already contains A, so 3 + 3 = 6: A taken twice
    c        0  1  2  3  4  5
    best     0  0  3  3 {{6  6}}
---
RIGHT, downward loop for A: c = 5 reads best[3], still the old 0, so 3; c = 4 reads best[2] = 0, so 3
    c        0  1  2  3  4  5
    best     0  0  0  0 {{3  3}}
---
RIGHT, continued: c = 3 and c = 2 also become 3. A is used at most once everywhere
    c        0  1  2  3  4  5
    best     0  0 {{3  3}} 3  3
---
Item B, downward: c = 5 = max(3, best[2] + 4 = 7) = 7, which is A and B together
    c        0  1  2  3  4  5
    best     0  0  3  3  3 {{7}}
---
c = 4 = max(3, best[1] + 4) = 4; c = 3 = max(3, best[0] + 4) = 4. Answer best[5] = 7
    c        0  1  2  3  4  5
    best     0  0  3 {{4  4}} 7
```

## Template

```python
def knapsack_01(items, cap):
    """items: (weight, value) pairs, each usable once. Best value with total weight <= cap."""
    best = [0] * (cap + 1)            # best[c]: best value within capacity c, items so far
    for w, v in items:
        for c in range(cap, w - 1, -1):   # downwards: best[c - w] still excludes this item
            best[c] = max(best[c], best[c - w] + v)
    return best[cap]


def knapsack_pick(items, cap):
    """Best value and the indices of one optimal choice (full table, then walk back)."""
    n = len(items)
    T = [[0] * (cap + 1) for _ in range(n + 1)]   # T[i][c]: first i items, capacity c
    for i, (w, v) in enumerate(items, 1):
        for c in range(cap + 1):
            T[i][c] = T[i - 1][c]
            if w <= c and T[i - 1][c - w] + v > T[i][c]:
                T[i][c] = T[i - 1][c - w] + v
    picked, c = [], cap
    for i in range(n, 0, -1):
        if T[i][c] != T[i - 1][c]:     # value changed, so item i-1 was taken
            picked.append(i - 1)
            c -= items[i - 1][0]
    return T[n][cap], picked[::-1]


def subset_sums(nums):
    """Bit s of the result is 1 when some subset of nums sums to s (non-negative ints)."""
    bits = 1                           # only the empty sum 0
    for x in nums:
        bits |= bits << x              # every old sum, with and without x
    return bits


def can_split_evenly(nums):
    total = sum(nums)
    return total % 2 == 0 and (subset_sums(nums) >> (total // 2)) & 1 == 1
```

`knapsack_pick([(6, 30), (5, 20), (5, 20)], 10)` returns `(40, [1, 2])`: the two 5 kg items from the Intuition section.

## Pitfalls

- **Upward capacity loop** in a 0/1 problem: items get reused, and answers come out too large.
- **Looping down to 0 instead of w.** `range(cap, -1, -1)` makes `c - w` negative for small c, and Python's negative indexing silently reads from the *end* of the list. With items [(3, 5), (2, 1)] and capacity 4, that version returns 11 instead of 5.
- **Swapping the loops** (capacity outer, items inner) changes the meaning: you no longer process one item at a time, so "each item once" is lost.
- **Counting base case.** For "how many subsets", reach[0] = 1 (the empty subset), not 0.
- **Huge capacity.** Check C before allocating: a list of 10^9 entries does not fit in memory.

## Check yourself

Q: With the buggy upward loop, what does a single item (weight 2, value 3) give for capacity 6, and what should it give?
A: 9 instead of 3. The upward sweep sets best[2] = 3, then best[4] reads best[2] and gets 6, then best[6] reads best[4] and gets 9: the item is used three times.

Q: Why is it enough to keep, for each capacity, only the best value so far, and forget which items produced it?
A: Because the remaining decisions depend only on the capacity left, not on which items used the rest. If two partial choices leave the same capacity, any completion of the worse one also fits after the better one and ends with at least as much value, so discarding the worse one loses nothing. That is the optimal-substructure argument behind the table.

Q: Stones must be split into two piles whose weights differ as little as possible (Last Stone Weight II, 1049 in the bank). How does this card solve it?
A: Find the largest reachable subset sum s that is at most total / 2 (subset sum, downward loop or bitset). The other pile weighs total - s, so the smallest difference is total - 2s.

Q: Your partition check uses `subset_sums`, and a test with a 0 in the list fails. Is the bitset wrong for zeros?
A: No: `bits << 0` is `bits`, so a zero adds nothing, which is correct for reachability. The likely bug is elsewhere, for example testing bit `total // 2` without first checking that the total is even. Zeros only matter for *counting* subsets, where each zero doubles the count.

## Lab

- **416 Partition Equal Subset Sum.** Use the downward boolean loop, then rewrite it with the integer bitset and time both. Expected: O(n x S) time, O(S) space with S = total / 2; [3, 1, 5, 9, 4] gives false, [4, 3, 9, 2, 6] gives true (9 + 3 = 4 + 2 + 6).
- **494 Target Sum** (derive it). Signs split the numbers into a plus group P and a minus group N; write two equations for the sums of P and N and turn the question into counting subsets. Expected: O(n x S) time, O(S) space; [1, 2, 3, 4] with target 2 has 2 ways, [2, 2, 2] with target 2 has 3 ways.

> [!know]
> You now know how to solve 0/1 knapsack and subset sum with a capacity table, why the one-row loop must run downwards, and when the capacity is too large for a table.

=== primer | What changes when items can be reused: unbounded knapsack, coin change and counting order? | 13 min
goal: Solve unbounded knapsack, fewest coins and the two kinds of counting (combinations and ordered sequences), choosing loop direction and nesting on purpose
tag: dpseq-unbounded | Unbounded knapsack and counting order
link: cp-algorithms: Complete knapsack | https://cp-algorithms.com/dynamic_programming/knapsack.html#complete-knapsack | 5 min: the 'Complete Knapsack' section: the same one-row code with the capacity loop running forwards
link: USACO Guide: Knapsack DP | https://usaco.guide/gold/knapsack#tutorial | 10 min: the 'Tutorial' section, in particular when the order of the items matters and how that changes the loops
practice: 322, 518

> [!key]
> If each item may be used any number of times, loop the capacity **upwards**: best[c - w] may already include this item, which is now exactly what you want. For counting, the **loop nesting** decides what is counted: items outer counts **combinations** (1 + 2 and 2 + 1 once), amounts outer counts **ordered sequences** (twice). For "fewest", unreachable amounts must start at infinity.

## Intuition

A cashier with unlimited 2 p and 5 p coins makes 11 p: 5 + 2 + 2 + 2, four coins. A carpenter sells pieces of a rod and may cut as many pieces of each length as she likes. In both, after using an item you face the same kind of problem with a smaller amount *and the same item still available*. That is the only difference from 0/1 knapsack, and it lives entirely in the loop direction.

## How it works

### The forward loop

best[c] = max(best[c], best[c - w] + v), with c rising from w to C. When you reach c, best[c - w] has already been updated for this item, so it may contain one or more copies of it; adding one more copy is allowed. The 0/1 trace in the previous card showed the forward loop "reusing an item": here that reuse is the feature. For items (2, 3) and (3, 5) and capacity 7, the 0/1 answer is 8 and the unbounded answer is 11 (2 + 2 + 3).

### Three questions, one table

| Question | Recurrence for each amount a | Start values |
|---|---|---|
| Most value (rod cutting) | best[a] = max(best[a], best[a - w] + v) | all 0 |
| Fewest coins (coin change) | need[a] = min(need[a], need[a - coin] + 1) | need[0] = 0, others infinity |
| Number of ways | ways[a] += ways[a - coin] | ways[0] = 1, others 0 |

Fewest coins is not the same as "largest coin first": with coins 5, 10, 20 and 25 the DP makes 40 from two 20s, while largest-first uses 25 + 10 + 5. The next module is about when such greedy rules are safe.

### Combinations or sequences?

**Coins outer, amounts inner** counts each multiset once. Think of building every combination in coin order: first decide how many 1s, then how many 2s, and so on. When the loop is at coin x, ways[a - x] only contains combinations made of coins up to x, so each multiset is built exactly once.

**Amounts outer, coins inner** counts ordered sequences. ways[t] = sum over x of ways[t - x] says "the *last* number in the sequence is x, and anything summing to t - x comes before it". Different last numbers give different sequences, so 1 + 2 and 2 + 1 are both counted. This is the problem behind "how many ways to climb n stairs taking 1 or 2 steps".

### Bounded copies

If item i has k_i copies, split it into items of 1, 2, 4, ... copies plus a remainder (for k = 13: 1, 2, 4, 6). Every count from 0 to k is a sum of a subset of those parts, so a 0/1 knapsack over the parts solves it in O(C x sum of log k_i).

### Quick reference

| Variant | Loops | Capacity direction | Combine |
|---|---|---|---|
| 0/1, best value | items outer | downwards | max |
| Unbounded, best value | items outer | upwards | max |
| Fewest coins | items outer (either nesting works) | upwards | min of +1 |
| Count combinations | items outer | upwards | + |
| Count ordered sequences | amounts outer | upwards | + |
| Count 0/1 subsets | items outer | downwards | + |

## Cost

Every variant does one constant-time update per (item, amount) pair: **O(n x C) time** and **O(C) space**. Counting answers grow exponentially with the amount, so C++ and Java need the problem's modulus; Python's integers just grow.

## When to use it

Cues: "unlimited supply", "each coin can be used any number of times", "how many ways to make", "fewest pieces". Read twice whether order matters: "combinations" or "sets" (1 + 2 equals 2 + 1) versus "sequences", "orderings" or "ways to climb" (they differ). If the coins form a system where largest-first is provably optimal, a greedy loop is O(number of coins); otherwise use this table.

## Worked trace

Coins 1 and 2, amount 4: the same recurrence, two nestings.

```steps
Coins outer. Start: one way to make 0 (use nothing)
    amount   0  1  2  3  4
    ways     1  0  0  0  0
---
Coin 1, amounts 1..4: each ways[a] += ways[a - 1]. Only all-1 combinations so far
    amount   0  1  2  3  4
    ways     1 {{1  1  1  1}}
---
Coin 2: ways[2] += ways[0], ways[3] += ways[1], ways[4] += ways[2] (already 2). Answer 3: 1111, 112, 22
    amount   0  1  2  3  4
    ways     1  1 {{2  2  3}}
---
Amounts outer. Start again: ways[0] = 1
    amount   0  1  2  3  4
    ways     1  0  0  0  0
---
t = 1: last number 1, ways[0] = 1. t = 2: last 1 (ways[1]) or last 2 (ways[0]): 2
    amount   0  1  2  3  4
    ways     1 {{1  2}} 0  0
---
t = 3: ways[2] + ways[1] = 3. t = 4: ways[3] + ways[2] = 5. Answer 5: 1111, 112, 121, 211, 22
    amount   0  1  2  3  4
    ways     1  1  2 {{3  5}}
```

## Template

```python
def knapsack_unbounded(items, cap):
    """Each (weight, value) item may be used any number of times."""
    best = [0] * (cap + 1)
    for w, v in items:
        for c in range(w, cap + 1):        # upwards: best[c - w] may already use this item
            best[c] = max(best[c], best[c - w] + v)
    return best[cap]


def fewest_coins(coins, amount):
    INF = float("inf")
    need = [0] + [INF] * amount            # need[a]: fewest coins for a; INF = impossible
    for coin in coins:
        for a in range(coin, amount + 1):
            need[a] = min(need[a], need[a - coin] + 1)
    return need[amount] if need[amount] != INF else -1


def count_combinations(coins, amount):
    """Multisets of coins summing to amount (1+2 and 2+1 count once)."""
    ways = [1] + [0] * amount
    for coin in coins:                     # coins outer: each multiset is built in coin order
        for a in range(coin, amount + 1):
            ways[a] += ways[a - coin]
    return ways[amount]


def count_sequences(nums, target):
    """Ordered sequences summing to target (1+2 and 2+1 count twice)."""
    ways = [1] + [0] * target
    for t in range(1, target + 1):         # amounts outer: any number can come last
        for x in nums:
            if x <= t:
                ways[t] += ways[t - x]
    return ways[target]
```

## Pitfalls

- **0 instead of infinity** in `fewest_coins`: every amount then looks reachable with 0 coins and the answer is 0.
- **Returning infinity.** Problems usually want -1 for "impossible"; translate at the end, not inside the table.
- **Swapped nesting.** Counting sequences when combinations were asked (or the reverse) is the classic wrong answer that still passes the first example.
- **Downward loop for an unbounded item** silently turns it back into a 0/1 knapsack.
- **Amount 0.** There is exactly one way to make 0 (take nothing) and it needs 0 coins; make sure your base cases say so.

## Check yourself

Q: With coins 2 and 3 and amount 7, how many combinations and how many ordered sequences are there?
A: One combination (2 + 2 + 3) and three sequences (2 2 3, 2 3 2, 3 2 2).

Q: Why does putting the coins in the outer loop count each combination exactly once?
A: While the outer loop is at coin x, the table only contains combinations of coins up to x. Each multiset is therefore built in a fixed order (all its smallest coins first, then the next kind, and so on), and there is exactly one such build order per multiset.

Q: What is the fewest number of perfect squares that sum to 18, and how does this card compute it?
A: 2 (9 + 9). It is `fewest_coins` with the coins 1, 4, 9 and 16 (every square up to 18); the unbounded loop allows 9 twice.

Q: A colleague's `fewest_coins` returns 0 for coins [2] and amount 3, where the answer is -1. What is the bug?
A: The table was initialised with zeros instead of infinity. need[3] starts at 0 and `min(0, anything)` stays 0, so the code reports 0 coins. Unreachable amounts must start at infinity, so that they never win a min and so that "still infinity at the end" means impossible.

## Lab

- **322 Coin Change.** Fewest coins with the forward loop and an infinity start. Expected: O(amount x coins) time, O(amount) space; coins [2, 5] and amount 11 give 4 (5 + 2 + 2 + 2), amount 3 gives -1.
- **518 Coin Change II.** Count combinations with coins in the outer loop, then swap the loops and see which test fails. Expected: O(amount x coins) time, O(amount) space; coins [2, 3] and amount 7 give 1; coins [1, 2] and amount 4 give 3 (the swapped version gives 5).

> [!know]
> You now know how to solve unbounded knapsack and coin problems, and how loop direction and nesting decide between 0/1 and unlimited items and between combinations and sequences.

=== primer | How do you split a string into dictionary words (or palindromes) with DP? | 12 min
goal: Decide, rebuild, count or minimise segmentations of a string with a DP over prefix lengths, bounded by the longest word
tag: dpseq-segment | Segmentation over prefixes
link: Erickson, Algorithms ch. 3: Interpunctio Verborum Redux (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=9 | 10 min: PDF pages 9-10, text segmentation turned from exponential backtracking into an O(n^2) table, then 'The Pattern: Smart Recursion'
practice: 132

> [!key]
> Let ok[i] mean "the prefix s[:i] can be split into words". It is true when some earlier cut j has ok[j] true and s[j:i] is a word, so you try every **last word**. Record which j worked to rebuild a split; replace "or" with "+" to **count** splits, or with min to find the **fewest pieces**. Bounding j by the longest word gives O(n x L) checks.

## Intuition

Read "thecatsat" from the left and you are tempted to grab the first word you see. Greedy grabbing breaks on harmless inputs: with the words {a, ab, bc}, grabbing the longest word first turns "abc" into "ab" + "c" and gets stuck, although "a" + "bc" works. Instead, look at it from the end: whatever the split is, it has a **last word**, and before that last word sits a shorter prefix that must itself be splittable. That shorter prefix is a smaller instance of the same question, and there are only n + 1 prefixes.

## How it works

| Recipe step | Word break |
|---|---|
| Specification | ok[i] = True if s[:i] splits into dictionary words |
| Recurrence | ok[i] = any(ok[j] and s[j:i] in words) for j in [i - L, i) |
| Base case | ok[0] = True: the empty prefix splits into zero words |
| Order | i from 1 to n |
| Answer | ok[n]; follow the stored cuts back for an actual split |

Here L is the length of the longest dictionary word: a last word longer than L cannot be in the dictionary, so there is no point trying it. Put the words in a `set` so each lookup is an O(length) hash, not a scan.

### Rebuild, count, minimise

- **Rebuild one split:** store `cut[i] = j` for the first j that works, then from n follow `cut` back to 0.
- **Count splits:** ways[i] = sum of ways[j] over valid last words s[j:i], ways[0] = 1. Counts can be exponential: "aaaaaaaaaa" with the words {a, aa} has 89 splits.
- **Fewest pieces:** pieces[i] = min(pieces[j] + 1). The same shape with a palindrome test instead of a dictionary gives "fewest cuts so every piece is a palindrome", using the boolean palindrome table from the range DP card to make each test O(1).
- **List every split:** the output itself can be exponential, so that is a backtracking problem (the backtracking module), ideally pruned by this table: never recurse into a prefix with ok false.

### Tries instead of slices

Each check `s[j:i] in words` copies up to L characters and hashes them. Walking a trie (the tries module) from position j forward finds every dictionary word starting at j in one pass without slicing, which pays off when L is large.

## Cost

n + 1 states; each tries at most L last words; each try slices and hashes up to L characters. Total **O(n x L^2)** time in the worst case with slicing, O(n x L) trie steps with a trie, and **O(n)** extra space. Without the L bound it is O(n^2) slices of up to n characters, O(n^3) in the worst case.

## When to use it

Cues: split, segment, break, partition a string (or any sequence) into consecutive pieces that each satisfy a test, and the question is "possible?", "how many?", "fewest pieces?" or "best score?".

| Situation | Tool |
|---|---|
| Possible, count, fewest, best score | this prefix DP |
| Pieces must come from a huge dictionary with long words | the same DP, with a trie for the inner loop |
| List every segmentation | backtracking, pruned by ok[] |
| Real language text with probabilities | the same DP maximising total log-probability (Viterbi-style) |

That last row is how real segmenters work: Python's `jieba` library for Chinese builds a graph of candidate words and runs this kind of DP to find the most probable path.

## Worked trace

s = "thecatsat", words = {the, cat, cats, sat, at, a}, longest word L = 4. `cut[i]` is the start of the last word in a split of s[:i] (`-` means no split).

```steps
Base: the empty prefix splits into nothing, so cut[0] = 0
    i        0  1  2  3  4  5  6  7  8  9
    s[:i]       t  h  e  c  a  t  s  a  t
    cut     {{0}} -  -  -  -  -  -  -  -  -
---
i = 1, 2: "t", "th", "h" are not words. i = 3: j = 0, "the" is a word and cut[0] exists
    cut      0  -  - {{0}} -  -  -  -  -  -
---
i = 4, 5: no splittable j gives a word ("c", "ca", "ec" ... are not words)
    cut      0  -  -  0 {{-  -}} -  -  -  -
---
i = 6: j = 3 gives "cat". i = 7: j = 3 gives "cats"
    cut      0  -  -  0  -  - {{3  3}} -  -
---
i = 8: j = 4..7; only j = 7 is splittable and gives a word, "a"
    cut      0  -  -  0  -  -  3  3 {{7}} -
---
i = 9: j = 6 is splittable and s[6:9] = "sat" is a word, so ok[9] is true
    cut      0  -  -  0  -  -  3  3  7 {{6}}
---
Walk back: 9 -> 6 gives "sat", 6 -> 3 gives "cat", 3 -> 0 gives "the"
    split = ["the", "cat", "sat"]   (counting finds 2: also "the cats at")
```

## Template

```python
def segment(s, words):
    """One way to split s into dictionary words, or None if there is none."""
    words = set(words)
    longest = max(map(len, words), default=0)
    n = len(s)
    cut = [None] * (n + 1)          # cut[i]: start of the last word in a split of s[:i]
    cut[0] = 0                      # the empty prefix splits trivially
    for i in range(1, n + 1):
        for j in range(max(0, i - longest), i):
            if cut[j] is not None and s[j:i] in words:
                cut[i] = j
                break
    if cut[n] is None:
        return None
    out, i = [], n
    while i > 0:                    # walk back through the recorded cuts
        out.append(s[cut[i]:i])
        i = cut[i]
    return out[::-1]


def count_segmentations(s, words):
    words = set(words)
    longest = max(map(len, words), default=0)
    ways = [1] + [0] * len(s)
    for i in range(1, len(s) + 1):
        for j in range(max(0, i - longest), i):
            if s[j:i] in words:
                ways[i] += ways[j]
    return ways[-1]
```

`cut[i]` doubles as the boolean (`None` means "cannot split"), so one list does both jobs. The loop tries the longest possible last word first and stops at the first success, which is enough for existence.

## Pitfalls

- **Forgetting the base case** ok[0] = True: nothing is ever splittable.
- **Greedy grabbing** of the longest or shortest prefix word, which fails on {a, ab, bc} and "abc".
- **No length bound**: trying every j from 0 makes each position cost O(n) slices even when no word is that long.
- **Words in a list**: `x in list` is a linear scan, turning each check into O(dictionary size).
- **Listing all splits with DP tables of lists**: memory explodes on inputs like "aaaa...a"; count with integers, list with pruned backtracking.

## Check yourself

Q: What do `segment("abc", {"a", "ab", "bc"})` and `count_segmentations("abc", {"a", "ab", "bc"})` return?
A: ["a", "bc"] and 1. cut[1] = 0 ("a") and cut[2] = 0 ("ab"). For i = 3 the loop starts at j = 1 (the longest word has two letters), and s[1:3] = "bc" is a word after a splittable prefix. The other candidate last word, "c", is not a word, so this is the only split.

Q: Why may the decision loop `break` at the first j that works, while the counting loop must not?
A: For existence one witness is enough, and any working j gives a valid split. Counting needs every last word that works, because each one starts a different family of splits; stopping early would undercount.

Q: Each piece must be a palindrome and you want the fewest cuts. What are the state, the recurrence and the cost?
A: pieces[i] = fewest palindromes that make up s[:i], with pieces[0] = 0 and pieces[i] = min(pieces[j] + 1) over all j with s[j:i] a palindrome. Precompute the boolean palindrome table so each test is O(1): O(n^2) time and space overall. The fewest cuts is pieces[n] - 1.

## Lab

- **132 Palindrome Partitioning II** (stretch). Build the boolean palindrome table, then the prefix DP above. Expected: O(n^2) time and space (O(n) extra space if you expand around centres instead of storing the table); "banana" needs 1 cut ("b" | "anana"), "noonabbad" needs 2 ("noon" | "abba" | "d").
- **Exponential counts.** Run `count_segmentations("a" * n, {"a", "aa"})` for n = 1 to 10 and explain the sequence. Expected: 1, 2, 3, 5, 8, ..., 89: Fibonacci numbers, because the last word is "a" (leaving n - 1) or "aa" (leaving n - 2).

> [!know]
> You now know how to split a sequence into valid pieces with a DP over prefix lengths, and how to rebuild, count or minimise the splits.

=== primer | Where do sequence DPs run in real software, and what changes at scale? | 12 min
goal: Explain how diff tools, spell checkers, aligners and budget solvers use these tables, and apply the standard scale-ups: interning, trimming common ends, banding and output-sensitive algorithms
tag: dpseq-scale | Scaling sequence DP in practice
link: Git documentation: git diff --diff-algorithm | https://git-scm.com/docs/git-diff#Documentation/git-diff.txt---diff-algorithmpatienceminimalhistogrammyers | 3 min: the four algorithms Git offers (default Myers, minimal, patience, histogram) and what each trades
link: James Coglan: The Myers diff algorithm, part 1 | https://blog.jcoglan.com/2017/02/12/the-myers-diff-algorithm-part-1/ | 25 min: the edit-graph picture, in which a diff is a shortest path through the LCS table that skips most of its cells

> [!key]
> The textbook tables are the core of diff tools, spell checkers and DNA aligners, but production code rarely fills a full m by n table. It **interns** items to small integers, **trims** the common prefix and suffix, **bounds** the work by the size of the answer (banding, Myers' O((m + n)D) diff), and accepts heuristics where a minimal answer is not what users want. The recurrence stays; the amount of table you touch shrinks.

## Intuition

Two 10,000-line versions of a file differ in three lines. A full LCS table has 10^8 cells, minutes of Python and gigabytes of memory, to discover an answer that a human sees at a glance. Almost all of that table describes lines that are identical and in the same place. Every production technique below is a way of not computing the boring part.

## How it works

### Diff: LCS over lines

The original Unix `diff` (Hunt and McIlroy, 1976) is built on the longest common subsequence of the two files' lines: lines outside the LCS are deletions or insertions. Modern tools keep that model but change the algorithm:

- **Interning.** Map each distinct line to a small integer with a dict, so every comparison is an integer comparison instead of a string comparison.
- **Trimming.** Strip the common prefix and suffix first; for a typical edit that removes nearly everything, and it never changes the LCS.
- **Myers' algorithm.** Git's default ("the basic greedy diff algorithm", in the Git docs) finds a shortest edit script in O((m + n)D) time, where D is the number of inserted and deleted lines, by exploring the table along diagonals in order of edit cost. Few changes means little work, whatever the file size.
- **Readability over minimality.** `--diff-algorithm=patience` and `histogram` anchor on lines that are unique in both files, which avoids aligning stray braces and blank lines. Python's `difflib` uses a different, Ratcliff-Obershelp-style matcher (longest matching block first, then recurse on both sides), and its documentation says plainly that it makes no claim to minimal diffs.

This stage's project builds a diff tool, so here you only need the vocabulary and the lab exercise below.

### Spelling and fuzzy matching

Spell checkers rank candidates by edit distance, but never against every word with a full table. They bound the distance (usually 1 or 2), filter by length, and band the table, as in this module's lab. PostgreSQL's `fuzzystrmatch` extension provides `levenshtein()` and `levenshtein_less_equal()`, the bounded version for "when only small distances are of interest". Others avoid scanning the dictionary altogether: Peter Norvig's corrector generates every string within two edits and looks them up, SymSpell precomputes deletions, and BK-trees prune with the triangle inequality.

### Biology: alignment with scores

Needleman-Wunsch (global alignment) is the edit distance table maximising a score: a substitution matrix rewards similar amino acids, and gaps cost a penalty. Smith-Waterman (local alignment) clamps every cell at 0 so the best-matching *region* wins. Biopython's `PairwiseAligner` implements both. For whole genomes O(mn) is far too slow, so tools such as BLAST find short exact seeds first and only run banded DP around them.

### Signals, images and budgets

Dynamic time warping aligns two time series (speech, gestures, sensor traces) with the grid recurrence of this module's first card. Seam carving resizes images by removing the cheapest top-to-bottom path of pixels, a falling-path grid DP. Knapsack DP is used when capacities are small integers; real budgets in cents with many constraints go to integer-programming solvers such as OR-Tools, whose knapsack solver uses branch and bound.

## Cost

| Approach | Time | Memory | Use when |
|---|---|---|---|
| Full table | O(mn) | O(mn), or O(min(m, n)) for the value only | short sequences, need the alignment |
| Trim common ends, then table | O(m'n') on the differing middle | same, on the middle | typical edits to long files |
| Banded with bound k | O(k x min(m, n)) | O(n) | only small distances matter |
| Myers diff | O((m + n)D) | O(m + n) plus history to rebuild the script | long, similar files |

In this module's measurements, a full pure-Python LCS on two 2,000-character strings took about 2 seconds; the same pair with 10 changes would be trimmed and diffed by Myers in milliseconds.

## When to use it

Ask three questions before filling a table over large inputs. Is the answer small compared with the inputs (few edits)? Then use an output-sensitive method: trimming, banding, Myers. Do users want minimal or readable output? For code review, readable (patience, histogram). Are you comparing one item against many? Then index the collection (BK-tree, SymSpell, a trie) instead of running the DP against every entry.

## Worked trace

Diff two five-line files that differ in one line, the way a real tool prepares the problem before any DP.

```steps
Two versions of a file: only the third line changed
    a: import os | def area(r): | return 3.14*r*r | (blank) | print(area(2))
    b: import os | def area(r): | return math.pi*r*r | (blank) | print(area(2))
---
Intern: every distinct line gets a small integer, in order of first appearance
    a ids:  0  1  {{2}}  3  4
    b ids:  0  1  {{5}}  3  4
---
Trim the common prefix: 0 = 0, 1 = 1, then 2 != 5, so p = 2
    a ids: {{0  1}}  2  3  4
    b ids: {{0  1}}  5  3  4
---
Trim the common suffix: 4 = 4, 3 = 3, then 2 != 5, so s = 2
    a ids:  0  1  2 {{3  4}}
    b ids:  0  1  5 {{3  4}}
---
Only the middle needs a table: [2] against [5], 1 cell instead of 25. Its LCS is empty
    middle a: {{2}}     middle b: {{5}}
    LCS = 2 (prefix) + 0 (middle) + 2 (suffix) = 4 lines kept
---
Edit script: delete old line 3, insert new line 3; m + n - 2 x LCS = 10 - 8 = 2 edits
    - return 3.14*r*r
    + return math.pi*r*r
```

## Template

```python
def trim_common(a, b):
    """Lengths of the common prefix and common suffix (they never overlap)."""
    p = 0
    while p < len(a) and p < len(b) and a[p] == b[p]:
        p += 1
    s = 0
    while s < len(a) - p and s < len(b) - p and a[-1 - s] == b[-1 - s]:
        s += 1
    return p, s


def intern_lines(a, b):
    """Replace every distinct line by a small int, so comparisons are integer compares."""
    ids = {}
    return ([ids.setdefault(x, len(ids)) for x in a],
            [ids.setdefault(x, len(ids)) for x in b])
```

Use them in front of any LCS or edit-distance routine: intern, trim, run the DP on `a[p:len(a) - s]` and `b[p:len(b) - s]`, and add p + s back. The verification for this module checks on random inputs that trimming never changes the LCS length.

## Pitfalls

- **Overlapping prefix and suffix.** For a = "aa" and b = "aaa", a careless trim counts 2 + 2 matches out of a 2-letter string. Bound the suffix scan by what the prefix left, as `trim_common` does.
- **Assuming minimal means good.** A minimal diff can align unrelated closing braces; tools offer patience and histogram for a reason.
- **Comparing text that only looks equal**: trailing spaces, Windows line endings and Unicode normalisation make lines differ. Decide what "equal" means and normalise before interning.
- **Full tables on big inputs.** Two 5,000-line files need 25 million cells; as Python ints in lists that is hundreds of megabytes.

## Check yourself

Q: Two 20,000-line files differ in 5 lines, spread through the file. Roughly how much work is a full LCS table, and how much is Myers' algorithm?
A: The table has 4 x 10^8 cells, far too slow in Python and too big to keep. Myers costs about (m + n) x D = 40,000 x 10 = 4 x 10^5 steps (D counts each changed line as one deletion plus one insertion), a thousand times less. Trimming helps only for the unchanged ends, since the changes are spread out.

Q: Why can difflib's output contain more changed lines than a minimal diff?
A: It does not compute an LCS. It finds the longest contiguous matching block, commits to it, and recurses on the parts to the left and right. An early commitment can rule out matches that an LCS would keep, which the Lab shows on three lines.

Q: What does PostgreSQL's `levenshtein_less_equal(a, b, 2)` return when the true distance is 5, and why is that enough for a spell checker?
A: According to the documentation it returns some value greater than 2, not necessarily 5. A spell checker only needs to know "close enough or not" for words beyond the bound, so the function may stop early, exactly like `within` in this module's lab.

## Lab

- **Minimal or not?** Run `lcs(["}", "return x", "}"], ["return x", "log(x)", "}"])` from the LCS card and `difflib.SequenceMatcher(None, a, b).get_matching_blocks()` on the same lists. Expected: the LCS keeps 2 lines ("return x" and "}"); difflib matches only 1 (it commits to the first "}" in a, matched with the last line of b), so its diff deletes and inserts one line more than necessary.
- **Measure trimming.** Take any source file of about 1,000 lines, change one line in the middle, intern both versions and run `trim_common`. Expected: p + s = 999, so the DP runs on a 1 by 1 middle instead of about 10^6 cells.

> [!know]
> You now know where sequence DPs run in production and the standard ways to make them scale: intern, trim, bound the distance, and prefer output-sensitive algorithms when the answer is small.

=== practice
- 64 core
  cue: A grid of costs, moves only right or down, and the cheapest way from one corner to the other
  hint: Which cells can the last step into (r, c) come from? What should a cell outside the grid contribute to a minimum?
  insight: best[r][c] = grid[r][c] + min(best above, best left), filled row by row; one list works because best[c] still holds the row above and best[c - 1] is already this row. Outside cells must be infinity, not 0.
  cost: O(mn) time, O(n) extra space
  pattern: dpseq-grid
- 221 derive
  cue: A 0/1 matrix and the area of the biggest all-1 square
  hint: Describe the largest square whose bottom-right corner is a given cell. How does it relate to the squares ending just above, just left and diagonally up-left?
  insight: side[r][c] = 1 + min(side above, side left, side up-left) for a 1 cell (0 for a 0 cell): each neighbour bounds how far the square can extend in one direction. The answer is the largest side squared.
  cost: O(mn) time, O(n) extra space
  pattern: dpseq-grid
- 1143 core
  cue: Two strings and the longest sequence of characters appearing in both in the same order, gaps allowed
  hint: Compare only the last characters of two prefixes. What can you conclude when they are equal, and when they differ?
  insight: L[i][j] = L[i - 1][j - 1] + 1 on a match, else max(L[i - 1][j], L[i][j - 1]); a match can always be used because some optimal answer ends with it. Two rows suffice for the length.
  cost: O(mn) time, O(min(m, n)) space
  pattern: dpseq-lcs
- 72 core
  cue: Fewest single-character insertions, deletions and replacements to turn one word into another
  hint: Line the words up column by column. What kinds of column can the last one be, and what remains when you remove it?
  insight: D[i][j] = D[i - 1][j - 1] if the last letters match, else 1 + min(replace D[i - 1][j - 1], delete D[i - 1][j], insert D[i][j - 1]), with D[i][0] = i and D[0][j] = j.
  cost: O(mn) time, O(n) space
  pattern: dpseq-edit
- 97 core
  cue: Three strings; can the third be formed by merging the first two while keeping each one's order?
  hint: Taking from the first string whenever it fits fails when both offer the same character. What small state describes how much of each string you have used?
  insight: I[i][j] = (I[i - 1][j] and s1[i - 1] == s3[i + j - 1]) or (I[i][j - 1] and s2[j - 1] == s3[i + j - 1]), with I[0][0] true and a length check first; one row is enough.
  cost: O(mn) time, O(n) space
  pattern: dpseq-match
- 516 core
  cue: The longest subsequence of a string that reads the same backwards
  hint: Look at the two ends of a substring. What happens to the best answer inside when they are equal, and when they are not?
  insight: P[i][j] = P[i + 1][j - 1] + 2 if s[i] == s[j], else max(P[i + 1][j], P[i][j - 1]); fill i from the end and j forwards. It also equals the LCS of s and its reverse.
  cost: O(n^2) time, O(n) space with two rows
  pattern: dpseq-pal
- 416 core
  cue: Can an array of positive integers be split into two groups with equal sums?
  hint: If it can, what must one group's sum be? Now it is a yes/no question about subsets.
  insight: Odd total means no; otherwise ask whether some subset reaches total / 2 with a boolean table swept downwards (each number once), or with a Python int bitset updated by bits |= bits << x.
  cost: O(n x S) time, O(S) space, S = total / 2
  pattern: dpseq-knap01
- 494 derive
  cue: Put a plus or minus sign in front of every number and count the ways to reach a target
  hint: The plus numbers form one group P and the minus numbers another N. You know P - N and P + N.
  insight: P = (total + target) / 2, so count subsets summing to P (ways[0] = 1, ways[c] += ways[c - x], c downwards); the answer is 0 if total + target is odd or abs(target) > total.
  cost: O(n x S) time, O(S) space
  pattern: dpseq-knap01
- 322 core
  cue: Fewest coins to make an amount, with an unlimited supply of each denomination
  hint: Think about the last coin used. What smaller amount is left, and what should an unreachable amount hold in a minimum?
  insight: need[a] = min(need[a], need[a - coin] + 1) with amounts swept upwards so coins can repeat; start with need[0] = 0 and infinity elsewhere, and report -1 if the target stays infinite.
  cost: O(amount x coins) time, O(amount) space
  pattern: dpseq-unbounded
- 518 core
  cue: Number of ways to make an amount from unlimited coins, where 1 + 2 and 2 + 1 are the same way
  hint: How do you make sure each combination is built in only one order?
  insight: Loop the coins in the outer loop and the amounts upwards inside: ways[a] += ways[a - coin]. Every multiset is then built coin type by coin type, exactly once; swapping the loops counts ordered sequences instead.
  cost: O(amount x coins) time, O(amount) space
  pattern: dpseq-unbounded
- 10 stretch
  cue: Whole-string matching with '.' for any character and '*' meaning zero or more of the previous element
  hint: Treat "x*" as one unit. What are its two options, and when is the second one allowed?
  insight: M[i][j]: if p[j - 1] is '*', M[i][j - 2] (skip the unit) or (p[j - 2] matches s[i - 1] and M[i - 1][j]); otherwise M[i - 1][j - 1] and p[j - 1] matches s[i - 1]. The empty-text row is true for prefixes like "a*b*".
  cost: O(mn) time, O(mn) space (O(n) with rolling rows)
  pattern: dpseq-match
- 132 stretch
  cue: Cut a string so that every piece is a palindrome, using as few cuts as possible
  hint: Two tables help: one answers "is s[j..i] a palindrome?" in O(1), the other is a prefix DP over where the last piece starts.
  insight: Precompute is_pal by range DP (or expand around centres), then cuts[i] = min(cuts[j] + 1) over j with s[j:i] a palindrome, with cuts[0] = -1 so a whole-palindrome prefix needs 0 cuts.
  cost: O(n^2) time, O(n^2) space (O(n) extra with centre expansion)
  pattern: dpseq-segment
