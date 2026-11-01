---
key: prefix
name: Prefix sums and difference arrays
stage: scan
summary: Precompute running totals so any range sum costs O(1), count subarrays by remembering earlier prefixes in a hash map, and batch range updates with a difference array.
why: A running total turns "add up this stretch" from O(n) into one subtraction, and pairing prefixes with a hash map counts subarrays with an exact sum, remainder or balance in one pass, even with negative values where sliding windows fail. The same few lines run in real software: the Viola-Jones face detector reads rectangle sums from an integral image (a 2D prefix sum, which OpenCV provides as cv2.integral), Prometheus counters are cumulative so increase() and rate() work from the difference between samples of a running total, and sparse-matrix formats such as CSR store a prefix sum of row lengths. Knowing where prefix sums stop (data that changes between queries) is what motivates the Fenwick and segment trees later in the route.
outcomes:
- Build a prefix array with pre[0] = 0 and answer any half-open range sum in O(1)
- Count, or find the longest, subarray with a given sum, remainder, XOR or balance in O(n) with a prefix map
- Answer rectangle sums in O(1) with a 2D prefix table, and collapse 2D counting problems to 1D
- Apply many range updates in O(1) each with a difference array, then rebuild once, in 1D and 2D
- Solve "everything except me" and "best on each side" questions with left and right passes
- Say when prefix sums stop working (updates interleaved with queries) and what replaces them
cues:
- Many sum queries over ranges of data that does not change
- Count subarrays (or find the longest) with an exact sum, a remainder or a balance, especially when values can be negative
- Many "add v to everything from l to r" updates, then a single read of the whole array
- For each index, combine everything to its left with everything to its right
- Rectangle sums over a grid or an image
traps:
- Off-by-one: forgetting pre[0] = 0, or mixing inclusive and half-open ranges
- Forgetting to seed the map with the empty prefix ({0: 1} for counts, {0: -1} for first indices)
- Recording the current prefix before looking up its partner, which counts empty subarrays when k = 0
- Negative remainders in C++ and Java (Python's % is already non-negative for a positive modulus)
- Using a sliding window when values can be negative, so validity is no longer monotone
systems:
- Computer vision: the Viola-Jones detector evaluates each rectangular Haar feature with a few lookups into an integral image, so the cost does not depend on the rectangle's size; OpenCV exposes the table as cv2.integral
- Prometheus counters are cumulative; increase() and rate() work from the difference between the first and last samples in the window (a range sum as a difference of prefixes), with extrapolation to the window edges and adjustment for counter resets
- Compressed sparse row matrices (scipy.sparse.csr_matrix's indptr) store a prefix sum of row lengths, so row i lives in indices[indptr[i]:indptr[i + 1]]
- Counting sort and radix sort turn key counts into starting positions with a prefix sum
further:
- Article · 25 min | USACO Guide: More on Prefix Sums (2D, difference arrays, max subarray sum) | https://usaco.guide/silver/more-prefix-sums#2d-prefix-sums
- Article · 10 min | Wikipedia: Summed-area table, the algorithm and its uses | https://en.wikipedia.org/wiki/Summed-area_table#The_algorithm
- Article · 20 min | Wikipedia: Prefix sum, parallel algorithms (how GPUs scan in O(log n) steps) | https://en.wikipedia.org/wiki/Prefix_sum#Parallel_algorithms
- Docs · 5 min | Prometheus: rate() on cumulative counters | https://prometheus.io/docs/prometheus/latest/querying/functions/#rate
bank: prefix
---

=== recap | Prefix sums and half-open ranges | 10 min
goal: Build a prefix array with pre[0] = 0 and answer any range sum with one subtraction, without off-by-one errors
tag: prefix-sum | Prefix sum array
link: USACO Guide: Introduction to Prefix Sums | https://usaco.guide/silver/prefix-sums#explanation | 5 min: the 'Explanation' section (the same picture with 1-indexed arrays), then 'Implementation'
link: Python docs: itertools.accumulate | https://docs.python.org/3/library/itertools.html#itertools.accumulate | 3 min: the signature and the initial= argument, which gives you the leading 0
practice: 303

> [!key]
> Store `pre[i]` as the sum of the first i elements, so `pre[0] = 0` and `pre` has n + 1 entries. The sum of the half-open slice `a[l:r]` is then `pre[r] - pre[l]`: one subtraction, whatever the length. You pay O(n) once to build the table and O(1) per query, as long as the data does not change.

## Internals

- **Invariant:** `pre[i] == sum(a[:i])`. It holds for i = 0 (the empty sum) and `pre[i + 1] = pre[i] + a[i]` keeps it. Subtracting two prefixes cancels their shared part, so `pre[r] - pre[l]` is exactly `a[l] + ... + a[r - 1]`.
- **Why half-open:** `a[l:r]` matches Python slicing and has length `r - l`, and the leading zero removes the special case `l == 0`. An inclusive question `[l, r]` becomes `pre[r + 1] - pre[l]`; convert once at the edge of your code, never in the middle.
- **Fence posts:** `pre[i]` sits on the post just before `a[i]`, which is why there is one more post than there are panels.
- **Python costs:** `list(accumulate(a, initial=0))` runs the loop in C, several times faster than a Python `for` loop. Each prefix is its own int object (28 bytes or more, plus an 8-byte list slot); for millions of numbers `numpy.cumsum` stores packed 8-byte integers instead. Python ints never overflow; NumPy's int64 and Java's or C++'s fixed-width integers do, silently.
- **The hidden O(n):** `sum(a[l:r])` inside a loop copies the slice and adds it up every time. A loop of q such queries is O(nq), exactly the cost the table removes.
- **Static data only:** changing `a[i]` invalidates every entry from `pre[i + 1]` on, an O(n) rewrite. When updates and queries interleave, a Fenwick tree keeps both at O(log n); the range-query module builds one.

## Template

```python
from itertools import accumulate


def build_prefix(a):
    """pre[i] = a[0] + ... + a[i-1], so pre[0] = 0 and len(pre) = len(a) + 1."""
    pre = [0] * (len(a) + 1)
    for i, x in enumerate(a):
        pre[i + 1] = pre[i] + x
    return pre


def range_sum(pre, l, r):
    """Sum of a[l:r] (half-open), O(1)."""
    return pre[r] - pre[l]


# The same table in one line, with the loop running in C:
# pre = list(accumulate(a, initial=0))
```

## Worked example

```steps
Start with `pre[0] = 0`, the sum of the first zero elements; `pre` will have one more entry than `a`
    i         0   1   2   3   4   5   6   7
    a         3   1   4   1   5   9   2
    pre       {{0}}
---
`pre[i + 1] = pre[i] + a[i]`: 0 + 3 = 3, then 3 + 1 = 4, then 4 + 4 = 8
    i         0   1   2   3   4   5   6   7
    a         3   1   4   1   5   9   2
    pre       0   {{3}}   {{4}}   {{8}}
---
Carry on to the end: `pre[7] = 25` is the total. Invariant: `pre[i]` is the sum of the `a` values in columns before i
    i         0   1   2   3   4   5   6   7
    a         3   1   4   1   5   9   2
    pre       0   3   4   8   {{9}}  {{14}}  {{23}}  {{25}}
---
Query `sum(a[2:5])`, the 4, 1 and 5: it is everything before column 5 minus everything before column 2
    i         0   1   2   3   4   5   6   7
    a         3   1   {{4}}   {{1}}   {{5}}   9   2
    pre       0   3   {{4}}   8   9  {{14}}  23  25
---
`pre[5] - pre[2] = 14 - 4 = 10`: two lookups, whatever the length of the range
    sum(a[2:5]) = 14 - 4 = 10 = 4 + 1 + 5
```

## Pitfalls

- **Mixed conventions:** answering an inclusive `[l, r]` with `pre[r] - pre[l]` silently drops `a[r]`. Write the convention in the docstring.
- **No leading zero:** building `pre[i] = sum(a[:i + 1])` forces an `if l == 0` branch and invites off-by-one errors.
- **Stale tables:** mutating `a` after building `pre` does not update it.
- **Floats:** differences of large running totals lose precision (cancellation). Keep integers (cents, counts), or use `math.fsum` when exactness matters.
- **Overflow elsewhere:** 2 x 10^5 values up to 10^9 sum to 2 x 10^14, beyond a 32-bit `int`; use `long long` in C++ and `long` in Java.

## Quick check

Q: For `a = [2, -1, 3, 0, 4]`, what is `pre`, and which two entries give the sum of `a[1:4]`?
A: `pre = [0, 2, 1, 4, 4, 8]`. The sum of `a[1:4]` (that is -1, 3 and 0) is `pre[4] - pre[1] = 4 - 2 = 2`.

> [!know]
> You now know how to turn any static range-sum question into two lookups, and why the leading zero and half-open ranges remove the off-by-one errors.

=== recap | Counting subarrays with a prefix map | 12 min
goal: Count, or find the longest, subarray with sum k in O(n), negative values included, by looking up earlier prefixes in a hash map
tag: prefix-map | Prefix sums with a hash map
link: Python docs: collections.Counter | https://docs.python.org/3/library/collections.html#collections.Counter | 3 min: the opening paragraphs, especially that a missing key returns 0 instead of raising KeyError, which is exactly what seen[cur - k] needs
practice: 560

> [!key]
> The subarray `a[j:i]` sums to k exactly when `pre[i] - pre[j] == k`, that is when some **earlier prefix equals `cur - k`**. Scan once with a running sum `cur` and a map from every prefix value seen so far to how often it occurred: add `seen[cur - k]` to the answer, then record `cur`. That is O(n) time and O(n) space, and negative values change nothing.

## Internals

- **Why not a sliding window:** a window shrinks when its sum is too big, which assumes that adding an element never lowers the sum. One negative value breaks that assumption and the window skips valid answers. Prefix differences do not care about signs.
- **Look up, then record:** after adding `a[i]`, `cur` is `pre[i + 1]` and the map holds `pre[0..i]`, so every match is a non-empty subarray ending at i. Recording `cur` first lets it match itself: an empty subarray, which sums to 0 and corrupts the answer when k = 0.
- **Seed `{0: 1}`:** the empty prefix `pre[0] = 0` is what lets subarrays starting at index 0 be counted.
- **Counter, defaultdict or dict.get:** `Counter` returns 0 for a missing key *without inserting it*; `defaultdict(int)` inserts on every read, so failed lookups grow the map; `seen.get(x, 0)` works on a plain dict.
- **One scan, several questions:** to count, map prefixes to counts; for the longest, map each prefix to its *first* index (seed `{0: -1}`, never overwrite); for the shortest, keep the *last* index (overwrite); to test existence, a set is enough.
- **Cost:** n lookups and n inserts at expected O(1) each (the hashing module covers why), plus O(n) space for the distinct prefixes.
- **Two dimensions:** fix a band of rows, collapse each column of the band to its sum, and run this count on that 1D array (the 2D recap shows the band trick).

## Template

```python
from collections import Counter


def count_sum_k(a, k):
    """Number of subarrays with sum exactly k, O(n)."""
    seen = Counter({0: 1})         # the empty prefix, before a[0]
    cur = count = 0
    for x in a:
        cur += x
        count += seen[cur - k]     # earlier prefixes p with cur - p == k
        seen[cur] += 1
    return count


def longest_sum_k(a, k):
    """Length of the longest subarray with sum exactly k (0 if none), O(n)."""
    first = {0: -1}                # prefix value -> first index where it occurred
    cur = best = 0
    for i, x in enumerate(a):
        cur += x
        if cur - k in first:
            best = max(best, i - first[cur - k])
        first.setdefault(cur, i)   # keep the earliest index only
    return best
```

## Worked example

Count the subarrays of `[3, 4, -7, 3, 1, 3]` that sum to k = 7. Watch prefix 0 appear twice: that duplicate is why the map stores counts, not just presence.

```steps
Seed the map with the empty prefix: `seen = {0: 1}`, `cur = 0`, `count = 0`
    a         3   4  -7   3   1   3
    seen  {0: 1}
    count 0
---
i = 0: `cur = 3`, look up `cur - k = -4`: not seen, so no subarray ends here; then record 3
    a         {{3}}   4  -7   3   1   3
    cur   3    need -4    matches 0
    seen  {0: 1, 3: 1}
    count 0
---
i = 1: `cur = 7`, look up `0`: seen once (the empty prefix), so `a[0:2] = [3, 4]` sums to 7
    a         3   {{4}}  -7   3   1   3
    cur   7    need 0    matches 1
    seen  {0: 1, 3: 1, 7: 1}
    count 1
---
i = 2: `cur = 0`, look up `cur - k = -7`: not seen, so no subarray ends here; then record 0, which is now in the map twice
    a         3   4  {{-7}}   3   1   3
    cur   0    need -7    matches 0
    seen  {0: 2, 3: 1, 7: 1}
    count 1
---
i = 3: `cur = 3`, look up `cur - k = -4`: not seen, so no subarray ends here; then record 3
    a         3   4  -7   {{3}}   1   3
    cur   3    need -4    matches 0
    seen  {0: 2, 3: 2, 7: 1}
    count 1
---
i = 4: `cur = 4`, look up `cur - k = -3`: not seen, so no subarray ends here; then record 4
    a         3   4  -7   3   {{1}}   3
    cur   4    need -3    matches 0
    seen  {0: 2, 3: 2, 7: 1, 4: 1}
    count 1
---
i = 5: `cur = 7`, look up `0`: seen 2 times, the empty prefix and the prefix after i = 2, so `a[0:6]` and `a[3:6] = [3, 1, 3]` both sum to 7
    a         3   4  -7   3   1   {{3}}
    cur   7    need 0    matches 2
    seen  {0: 2, 3: 2, 7: 2, 4: 1}
    count 3
```

## Pitfalls

- **Recording before looking up:** counts empty subarrays whenever k = 0.
- **No seed:** misses every subarray that starts at index 0; for the longest variant, seeding `{0: 0}` instead of `{0: -1}` makes those lengths one too short.
- **Overwriting first indices** in the longest variant shortens answers.
- **Using it where a window is better:** with non-negative values and a "sum at most k" condition, a sliding window needs O(1) space. The map is for exact targets and signed data.

## Quick check

Q: What does `count_sum_k([0, 0, 0], 0)` return, and what would it return if the loop recorded `cur` before the lookup?
A: 6, one for each of the 3 + 2 + 1 non-empty subarrays. Recording first lets each step also match itself (an empty subarray ending there), adding 3 more: 9.

> [!know]
> You now know how to count or measure subarrays with an exact sum in one pass by asking the map how many earlier prefixes equal `cur - k`.

=== recap | Remainders, XOR and balance as prefix keys | 10 min
goal: Turn "divisible by k", "XOR equals k" and "as many 0s as 1s" into equal-key lookups over prefixes
tag: prefix-mod | Prefix remainders, XOR and balance
link: Python docs: binary arithmetic operations | https://docs.python.org/3/reference/expressions.html#binary-arithmetic-operations | 3 min: the paragraph on % (the result has the same sign as the second operand), which is why Python needs no fix for negative sums
practice: 974, 525

> [!key]
> Many subarray conditions depend only on a **key** of the two bounding prefixes: equal remainders mod k mean the sum is divisible by k, prefix XORs that differ by k (in XOR terms) mean the subarray's XOR is k, and equal balances (with 0 scored as -1) mean equal counts. Run the same one-pass scan as the prefix map, but store the key instead of the raw sum.

## Internals

| Question about `a[j:i]` | Key per prefix | Look up | Map value |
|---|---|---|---|
| Sum divisible by k | `pre % k` | the same remainder | count |
| Sum a multiple of k, length at least 2 | `pre % k` | the same remainder, two or more positions back | first index |
| XOR equals k | prefix XOR | `cur ^ k` | count |
| As many 0s as 1s | sum with 0 scored as -1 | the same balance | first index |
| Every vowel an even number of times | 5-bit parity mask | the same mask | first index |

- **Why remainders work:** `(pre[i] - pre[j]) % k == 0` exactly when `pre[i] % k == pre[j] % k`.
- **XOR is its own inverse:** `px[i] ^ px[j]` is the XOR of `a[j:i]`, so the XOR is k exactly when `px[j] == px[i] ^ k`.
- **Negative remainders:** Python's `%` takes the sign of the divisor, so `-5 % 3 == 1`. C++ and Java truncate towards zero (`-5 % 3 == -2`); normalise with `((x % k) + k) % k` or equal remainders will not match.
- **Small key spaces:** with keys in `0..k-1` (or 32 parity masks), a list of size k replaces the dict: O(k) space and no hashing.
- **Counting pairs at the end:** a key seen c times contributes c(c - 1)/2 subarrays; the running version adds the same total one step at a time.

## Template

```python
from collections import Counter


def count_equal_keys(a, step, start=0):
    """Subarrays whose two bounding prefix keys are equal; key_(i+1) = step(key_i, a[i])."""
    seen = Counter({start: 1})
    key = start
    count = 0
    for x in a:
        key = step(key, x)
        count += seen[key]
        seen[key] += 1
    return count


def count_xor_k(a, k):
    """Subarrays whose XOR is exactly k: look up cur ^ k instead of cur."""
    seen = Counter({0: 1})
    cur = count = 0
    for x in a:
        cur ^= x
        count += seen[cur ^ k]     # px[j] ^ px[i] == k  <=>  px[j] == px[i] ^ k
        seen[cur] += 1
    return count


# Sums divisible by k: count_equal_keys(a, lambda s, x: (s + x) % k)
# XOR equal to zero:   count_equal_keys(a, lambda s, x: s ^ x)
```

## Worked example

Count the subarrays of `[2, -7, 4, 3, 5]` whose sum is divisible by 3.

```steps
Seed remainder 0 once (the empty prefix). `seen[r]` counts earlier prefixes with remainder r
    a         2  -7   4   3   5
    seen by remainder  r0=1  r1=0  r2=0
    count 0
---
prefix 2, remainder 2: no earlier prefix has remainder 2
    a         {{2}}  -7   4   3   5
    prefix    2
    % 3       {{2}}
    seen by remainder  r0=1  r1=0  r2=1
    count 0
---
prefix -5: Python gives `-5 % 3 = 1` (C++ and Java give -2). No earlier remainder 1
    a         2  {{-7}}   4   3   5
    prefix    2  -5
    % 3       2   {{1}}
    seen by remainder  r0=1  r1=1  r2=1
    count 0
---
prefix -1, remainder 2: 1 earlier prefix shares it, so 1 new subarray ends here
    a         2  -7   {{4}}   3   5
    prefix    2  -5  -1
    % 3       2   1   {{2}}
    seen by remainder  r0=1  r1=1  r2=2
    count 1
---
prefix 2, remainder 2: 2 earlier prefixes share it, so 2 new subarrays end here
    a         2  -7   4   {{3}}   5
    prefix    2  -5  -1   2
    % 3       2   1   2   {{2}}
    seen by remainder  r0=1  r1=1  r2=3
    count 3
---
prefix 7, remainder 1: 1 earlier prefix shares it, so 1 new subarray ends here
    a         2  -7   4   3   {{5}}
    prefix    2  -5  -1   2   7
    % 3       2   1   2   2   {{1}}
    seen by remainder  r0=1  r1=2  r2=3
    count 4
---
Total 4: `[-7, 4]`, `[-7, 4, 3]`, `[3]` and `[4, 3, 5]`. The last one pairs prefixes -5 and 7, which C-style `%` would miss
    a         2  -7   4   3   5
    prefix    2  -5  -1   2   7
    % 3       2   1   2   2   1
    count 4
```

## Pitfalls

- **C-style remainders** in C++ and Java break the matching for negative prefixes (see the last step above).
- **"Length at least 2"** needs positions, not counts: store the first index of each remainder and require `i - first >= 2`.
- **Seeds:** remainder 0 counted once for counts; balance 0 at index -1 for longest-length questions.
- **More than two symbols:** scoring 0 as -1 only works for two categories; for three, use a tuple of differences such as `(count_a - count_b, count_b - count_c)` as the key.

## Quick check

Q: In C++, `-5 % 3` is -2. In the worked example, which subarray would a direct C++ translation miss, and how do you fix it?
A: `[4, 3, 5]`: its bounding prefixes are -5 and 7, whose remainders are -2 and 1 in C++, so they do not match. Normalise with `((x % k) + k) % k`; Python's `%` already does.

Q: What is the longest stretch of `[1, 1, 0, 1, 0, 0, 1]` with equally many 0s and 1s?
A: 6. Scoring 0 as -1 gives balances 1, 2, 1, 2, 1, 0, 1. Balance 0 was first seen at the seed index -1 and again at index 5 (length 6), and balance 1 first at index 0 and again at index 6 (also length 6).

> [!know]
> You now know how to rephrase divisibility, XOR and balance conditions as "two prefixes share a key" and count them in one pass.

=== recap | 2D prefix sums and integral images | 12 min
goal: Answer any rectangle sum in O(1) by inclusion-exclusion, and reduce 2D counting problems to 1D by fixing a band of rows
tag: prefix-2d | 2D prefix sums
link: Wikipedia: Summed-area table | https://en.wikipedia.org/wiki/Summed-area_table#The_algorithm | 5 min: 'The algorithm', with the four-corner picture, plus the note on its use in the Viola-Jones detector
link: USACO Guide: 2D prefix sums | https://usaco.guide/silver/more-prefix-sums#2d-prefix-sums | 10 min: the '2D Prefix Sums' section and its worked grid
practice: 304, 1074

> [!key]
> Let `P[r][c]` be the sum of everything above and to the left of the corner (r, c), with an extra row and column of zeros. A rectangle `[r1, r2) x [c1, c2)` is then `P[r2][c2] - P[r1][c2] - P[r2][c1] + P[r1][c1]`: take the big block, remove the strip above and the strip to the left, and add back the corner you removed twice. O(mn) to build, O(1) per query.

## Internals

```text
           c1         c2
     +----------+---------+
     |    A     |    B    |     P[r1][c1] = A
  r1 +----------+---------+     P[r1][c2] = A + B
     |    C     |  query  |     P[r2][c1] = A + C
  r2 +----------+---------+     P[r2][c2] = A + B + C + query

  query = P[r2][c2] - P[r1][c2] - P[r2][c1] + P[r1][c1]
```

- **Build with the same idea:** `P[r+1][c+1] = g[r][c] + P[r][c+1] + P[r+1][c] - P[r][c]`, one O(1) step per cell.
- **Integral images:** computer vision calls this table an integral image. The Viola-Jones face detector evaluates each rectangular Haar feature with a few lookups, so a feature costs the same at every size and scale; a box blur costs the same per pixel at any radius. OpenCV provides it as `cv2.integral`.
- **NumPy:** `P[1:, 1:] = g.cumsum(axis=0, dtype=np.int64).cumsum(axis=1)` builds it in C. Choose the dtype deliberately: an all-white 5000 x 5000 image sums to 6.4 x 10^9, which wraps a uint32 table (the lab shows it).
- **Fix a band, collapse to 1D:** to count sub-rectangles with sum t, loop over row pairs (top, bottom), keep running column sums for the band, and run the 1D prefix-map count on them. With R rows and C columns that is O(R^2 C), so put the smaller dimension on the outside.
- **Higher dimensions:** the same pattern uses 2^d corners with alternating signs.

## Template

```python
def build_2d(grid):
    """P[r][c] = sum of grid[:r][:c] (the rectangle above and left of (r, c))."""
    m = len(grid)
    n = len(grid[0]) if m else 0
    P = [[0] * (n + 1) for _ in range(m + 1)]
    for r in range(m):
        for c in range(n):
            P[r + 1][c + 1] = grid[r][c] + P[r][c + 1] + P[r + 1][c] - P[r][c]
    return P


def rect_sum(P, r1, c1, r2, c2):
    """Sum of grid[r1:r2][c1:c2] (half-open in both directions), O(1)."""
    return P[r2][c2] - P[r1][c2] - P[r2][c1] + P[r1][c1]
```

## Worked example

```steps
The grid and the query: rows 1 to 2, columns 1 to 2, half-open `[1, 3) x [1, 3)`
    grid
       3   0   1   4
       5   {{6}}   {{3}}   2
       1   {{2}}   {{0}}   1
       4   1   0   5
---
Build `P` (one extra zero row and column). For example `P[2][2] = g[1][1] + P[1][2] + P[2][1] - P[1][1] = 6 + 3 + 8 - 3 = 14`
    P
       0   0   0   0   0
       0   {{3}}   {{3}}   4   8
       0   {{8}}  {{14}}  18  24
       0   9  17  21  28
       0  13  22  26  38
---
Query: start from `P[3][3] = 21`, everything above and left of the bottom-right corner
    P
       0   0   0   0   0
       0   3   3   4   8
       0   8  14  18  24
       0   9  17  {{21}}  28
       0  13  22  26  38
---
Subtract `P[1][3] = 4` (rows above the box) and `P[3][1] = 9` (columns left of it)
    P
       0   0   0   0   0
       0   3   3   {{4}}   8
       0   8  14  18  24
       0   {{9}}  17  21  28
       0  13  22  26  38
---
The top-left block `P[1][1] = 3` was subtracted twice, so add it back: 21 - 4 - 9 + 3 = 11 = 6 + 3 + 2 + 0
    P
       0   0   0   0   0
       0   {{3}}   3   4   8
       0   8  14  18  24
       0   9  17  21  28
       0  13  22  26  38
```

## Pitfalls

- **Inclusive corners:** for an inclusive rectangle (r1, c1) to (r2, c2), shift the far corner: `P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1]`.
- **Aliased rows:** `[[0] * (n + 1)] * (m + 1)` makes every row the same list; build rows with a comprehension.
- **Fixed-width overflow** in NumPy, C++ and Java tables.
- **Empty grids:** `len(grid[0])` raises on `[]`; guard it as the template does.

## Quick check

Q: Using the table `P` in the trace, what is the sum of the bottom row of the grid?
A: It is the rectangle `[3, 4) x [0, 4)`: `P[4][4] - P[3][4] - P[4][0] + P[3][0] = 38 - 28 - 0 + 0 = 10`, which matches 4 + 1 + 0 + 5.

> [!know]
> You now know how to read any rectangle sum from four corners of an integral image, and how to collapse a 2D counting problem to 1D by fixing a band of rows.

=== recap | Difference arrays: many range updates, one rebuild | 10 min
goal: Apply q range additions in O(1) each and recover the array with one running sum, in 1D and 2D
tag: prefix-diff | Difference array
link: USACO Guide: Difference arrays | https://usaco.guide/silver/more-prefix-sums#difference-arrays | 8 min: the 'Difference Arrays' section; its 'Greg and Array' explanation stacks a second difference array over the updates themselves
practice: 1109, 2536, 995

> [!key]
> The difference array `d[i] = a[i] - a[i - 1]` is the inverse of the prefix sum: a running sum of `d` gives `a` back. Adding v to the whole slice `a[l:r]` changes only two differences, `d[l] += v` and `d[r] -= v`. So record each update in O(1) and rebuild once at the end in O(n): O(n + q) instead of O(nq).

## Internals

- **Inverse operations:** prefix sums and differences undo each other, like integrals and derivatives. A range addition is a step up at l and a step down at r.
- **Spare slot:** keep `d` one longer than `a` so an update ending at `r == n` needs no bounds check.
- **Starting from a non-zero array:** either start `d` from the differences of `a`, or rebuild the additions from zeros and add them to `a` element by element.
- **Sweep-line view:** +v at each start and -v at each end, processed in position order, tracks "how many are active right now" (passengers in a car, meetings in progress, flips covering this bit). You can consume `d` while still writing it, left to right, as long as every new update starts at or after the current position.
- **2D:** for `[r1, r2) x [c1, c2)` add +v at (r1, c1), -v at (r1, c2), -v at (r2, c1) and +v at (r2, c2), then take running sums along rows and then down columns.
- **Huge coordinates:** if positions reach 10^9, sort the start and end events (or compress the coordinates) instead of allocating an array.
- **The limit:** a read between updates needs a rebuild each time. Interleaved range updates and point reads call for a Fenwick tree over `d` (the range-query module).

## Template

```python
from itertools import accumulate


def apply_range_adds(n, updates):
    """Each (l, r, v) adds v to a[l:r] (half-open); returns the final array, O(n + len(updates))."""
    d = [0] * (n + 1)              # one spare slot so r == n needs no check
    for l, r, v in updates:
        d[l] += v
        d[r] -= v
    return list(accumulate(d[:n]))
```

## Worked example

Three updates on six zeros: +2 on `a[1:4]`, +3 on `a[2:6]` and -1 on `a[0:2]`.

```steps
Start with `d = [0] * (n + 1)`; slot 6 is the spare that lets `r == n` work without a check
    i         0   1   2   3   4   5   6
    d         0   0   0   0   0   0   0
---
Add +2 to `a[1:4]`: `d[1] += 2` and `d[4] -= 2`. Two writes, however long the range
    i         0   1   2   3   4   5   6
    d         0   {{2}}   0   0  {{-2}}   0   0
---
Add +3 to `a[2:6]`: `d[2] += 3` and `d[6] -= 3`. Two writes, however long the range
    i         0   1   2   3   4   5   6
    d         0   2   {{3}}   0  -2   0  {{-3}}
---
Add -1 to `a[0:2]`: `d[0] -= 1` and `d[2] += 1`. Two writes, however long the range
    i         0   1   2   3   4   5   6
    d        {{-1}}   2   {{4}}   0  -2   0  -3
---
Rebuild with one running sum over `d[:6]`: each value is the total of every start minus every stop so far
    i         0   1   2   3   4   5   6
    d        -1   2   4   0  -2   0  -3
    a        {{-1}}   {{1}}   {{5}}   {{5}}   {{3}}   {{3}}
---
Check one cell: `a[2]` is inside `[1, 4)` and `[2, 6)` but not `[0, 2)`, so 2 + 3 = 5
    i         0   1   2   3   4   5
    a        -1   1   {{5}}   5   3   3
```

## Pitfalls

- **Inclusive, 1-indexed inputs:** for `[first, last]`, write `d[first - 1] += v` and `d[last] -= v`.
- **Reading `d[i]` as a value** before the rebuild.
- **The 2D sign pattern:** two minus corners, two plus corners; a wrong sign leaks the update across the grid.
- **Allocating 10^9 slots** when only a few thousand positions matter.

## Quick check

Q: Five counters start at 0. Add 5 to positions 1 to 3, 10 to positions 2 to 4 and 7 to positions 4 to 5 (1-indexed, inclusive). What is `d` before the rebuild, and what are the final values?
A: The 0-indexed half-open updates are `(0, 3, 5)`, `(1, 4, 10)` and `(3, 5, 7)`, so `d = [5, 10, 0, 2, -10, -7]` and the running sum gives `[5, 15, 15, 17, 7]`.

> [!know]
> You now know how to batch any number of range additions into two writes each and recover every value with one running sum.

=== recap | Left and right passes | 10 min
goal: Answer "everything except me" and "best on each side" questions with one pass from each end, and track running extremes of prefixes
tag: prefix-passes | Prefix and suffix passes
link: USACO Guide: Max subarray sum | https://usaco.guide/silver/more-prefix-sums#max-subarray-sum | 5 min: 'Max Subarray Sum', which pairs each prefix with the smallest prefix before it: the running-extreme pass described here
practice: 724, 1749, 689

> [!key]
> When the answer at index i combines everything to its left with everything to its right, compute `left[i]` (an aggregate of `a[:i]`) in a forward pass and `right[i]` (of `a[i+1:]`) in a backward pass, then combine them per index. Any associative operation with an identity works: sum, product, max, min, gcd. A close cousin keeps a running extreme of the prefix sums themselves.

## Internals

- **Exclusive scans** generalise prefix sums to any associative operation; "exclusive" means `a[i]` itself is left out of both sides.
- **Why not subtract from the total:** subtraction works for sums (the right side of i is `total - left - a[i]`) but there is no inverse for max or min, and dividing a product by `a[i]` fails when `a[i] == 0`. Two passes need no inverse.
- **O(1) extra space:** write `left` straight into the output array, then sweep backwards multiplying by a running right aggregate.
- **Running extremes of prefixes:** the best subarray sum ending at i is `pre[i + 1] - min(pre[0..i])`; the largest absolute subarray sum is `max(pre) - min(pre)` over all prefixes (the empty one included), because the absolute value makes their order irrelevant.
- **Best on each side:** to choose non-overlapping windows, precompute `best_left[i]` (the best window ending at or before i) and `best_right[i]` (the best starting at or after i), then try every middle choice and combine in O(1). When the earliest indices must win ties, use `>` in the forward pass and `>=` in the backward one.
- **Elsewhere in the route:** trapping rain water uses left and right maxima (two pointers module), and next-greater problems refine "everything to my right" with a monotonic stack.

## Template

```python
def exclusive_scans(a, op, identity):
    """left[i] = op over a[:i] and right[i] = op over a[i+1:], both O(n)."""
    n = len(a)
    left, right = [identity] * n, [identity] * n
    for i in range(1, n):
        left[i] = op(left[i - 1], a[i - 1])
    for i in range(n - 2, -1, -1):
        right[i] = op(right[i + 1], a[i + 1])
    return left, right
```

## Worked example

Left and right maxima of `[2, 7, 1, 8, 2, 8]`, using `max` with identity `-inf`.

```steps
Left pass: `left[i] = max(left[i - 1], a[i - 1])`, the largest value strictly before i (identity -inf at i = 0)
    a          2    7    1    8    2    8
    left    {{-inf}}
---
Fill left to right; each entry costs one comparison
    a          2    7    1    8    2    8
    left    -inf    {{2}}    {{7}}    {{7}}    {{8}}    {{8}}
---
Right pass from the end: `right[i] = max(right[i + 1], a[i + 1])`, the largest value strictly after i
    a          2    7    1    8    2    8
    left    -inf    2    7    7    8    8
    right      {{8}}    {{8}}    {{8}}    {{8}}    {{8}} {{-inf}}
---
Combine per index in O(1): `a[i] > left[i]` marks a new record, at indices [0, 1, 3]; swap max for multiplication and `left[i] * right[i]` is the product of everything except `a[i]`
    a          {{2}}    {{7}}    1    {{8}}    2    8
    left    -inf    2    7    7    8    8
    right      8    8    8    8    8 -inf
```

## Pitfalls

- **Wrong identity:** 0 is not the identity for max over negative numbers; use `float("-inf")` (or 1 for products, 0 for sums and gcd).
- **Inclusive versus exclusive** scans differ by one position; decide whether `a[i]` belongs on a side.
- **Ties** in best-left and best-right arrays when the smallest indices must win.
- **Division shortcuts** that break on zeros.

## Quick check

Q: Run the two passes with multiplication on `[3, 1, 2, 5]`. What are `left`, `right` and the product of everything except each element?
A: `left = [1, 3, 3, 6]`, `right = [10, 10, 5, 1]`, and the products are `[10, 30, 15, 6]`.

> [!know]
> You now know how to answer "everything except me" and "best on each side" questions with one pass from each end and an O(1) combine per index.

=== lab | Integral image: region sums and a box blur at any radius | 45 min
goal: Build a 2D prefix table over a large NumPy image, verify it on random rectangles, and measure how its cost stays flat while a naive box blur grows with the radius
link: NumPy docs: numpy.cumsum | https://numpy.org/doc/stable/reference/generated/numpy.cumsum.html | 3 min: the axis and dtype parameters, and the note on which integer type it accumulates in

You will compute region sums over a 2000 x 2000 image naively and with an integral image, check that both agree on 10,000 random rectangles, apply a box blur at four radii both ways, and watch a too-narrow integer type wrap.

## Setup

- Python 3.10+ with `pip install numpy`; about 1 GB of free memory.

## Steps

1. Save this as `integral_lab.py` and run it with `python integral_lab.py`.

```python
import time
import numpy as np

H, W = 2000, 2000
rng = np.random.default_rng(1)
img = rng.integers(0, 256, size=(H, W), dtype=np.uint8)


def integral(img):
    """P[r, c] = img[:r, :c].sum(); one extra row and column of zeros."""
    P = np.zeros((img.shape[0] + 1, img.shape[1] + 1), dtype=np.int64)
    P[1:, 1:] = img.cumsum(axis=0, dtype=np.int64).cumsum(axis=1)
    return P


def region_sum(P, r1, c1, r2, c2):
    """img[r1:r2, c1:c2].sum() in four lookups."""
    return int(P[r2, c2] - P[r1, c2] - P[r2, c1] + P[r1, c1])


t = time.perf_counter()
P = integral(img)
print(f"build integral image: {(time.perf_counter() - t) * 1000:.1f} ms")

rects = []
for _ in range(10_000):
    r1, r2 = sorted(rng.integers(0, H + 1, size=2))
    c1, c2 = sorted(rng.integers(0, W + 1, size=2))
    rects.append((int(r1), int(c1), int(r2), int(c2)))

t = time.perf_counter()
naive = [int(img[r1:r2, c1:c2].sum(dtype=np.int64)) for r1, c1, r2, c2 in rects]
naive_s = time.perf_counter() - t
t = time.perf_counter()
fast = [region_sum(P, *q) for q in rects]
fast_s = time.perf_counter() - t
assert naive == fast
print(f"10,000 rectangles: naive {naive_s:.2f} s, integral {fast_s * 1000:.1f} ms, "
      f"{naive_s / fast_s:.0f}x faster, all equal")


def box_blur_shifts(img, r):
    """Mean over a (2r+1) x (2r+1) window by adding shifted copies: (2r+1)^2 whole-image adds."""
    pad = np.pad(img.astype(np.int64), r, mode="edge")
    acc = np.zeros(img.shape, dtype=np.int64)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            acc += pad[dy:dy + img.shape[0], dx:dx + img.shape[1]]
    return acc // (2 * r + 1) ** 2


def box_blur_integral(img, r):
    """The same blur with four whole-array lookups into the integral image of the padded image."""
    pad = np.pad(img, r, mode="edge")
    P = integral(pad)
    k = 2 * r + 1
    h, w = img.shape
    s = P[k:k + h, k:k + w] - P[0:h, k:k + w] - P[k:k + h, 0:w] + P[0:h, 0:w]
    return s // (k * k)


for r in (1, 3, 7, 15):
    t = time.perf_counter(); a = box_blur_shifts(img, r); ts = time.perf_counter() - t
    t = time.perf_counter(); b = box_blur_integral(img, r); ti = time.perf_counter() - t
    assert np.array_equal(a, b)
    print(f"box blur r={r:>2}: shifted adds {ts * 1000:7.0f} ms, integral image {ti * 1000:5.0f} ms")

white = np.full((5000, 5000), 255, dtype=np.uint8)
P32 = np.zeros((5001, 5001), dtype=np.uint32)
P32[1:, 1:] = white.cumsum(axis=0, dtype=np.uint32).cumsum(axis=1, dtype=np.uint32)
print("uint32 corner:", int(P32[-1, -1]), " true total:", 255 * 5000 * 5000)
```

2. Before you read the output, predict: how many lookups does one region sum take, and how many whole-image additions does the shifted blur do at r = 15?
3. Draw the four corners used by `box_blur_integral` for one pixel on paper and check them against `rect_sum` from the 2D recap: the slices are that formula applied to every pixel at once.
4. Change `rects` to only tiny rectangles (side at most 5). Does the naive approach catch up? Explain why from what each method touches.
5. Fix the overflow line by choosing a dtype that cannot wrap, and state the largest image of 8-bit pixels that a uint32 table can hold safely (255 x H x W must stay below 2^32).

## What you should see

On a recent laptop or server, single-threaded:

- Building the integral image takes roughly 100 to 250 ms; it is two passes of C loops over 4 million pixels.
- The naive region sums take several seconds for 10,000 random rectangles (the average rectangle covers about a ninth of the image, roughly 440,000 pixels), while the integral image answers all of them in a few tens of milliseconds: a few hundred times faster, and every answer equal.
- The shifted-copy blur grows with (2r + 1)^2: roughly 0.1 to 0.2 s at r = 1, 2 to 2.5 s at r = 7 and around 10 s at r = 15. The integral blur stays near 0.1 to 0.25 s at every radius, because it always does four lookups per pixel. At r = 1 the two are about level, or the shifted version wins: nine whole-image additions are cheap, and the integral version also pays to build its table.
- With tiny rectangles the naive sums drop to tens of milliseconds for all 10,000 and the gap shrinks to a few times: each call's Python and NumPy overhead now costs more than the arithmetic. The table's advantage is that its cost never depends on the area.
- The uint32 corner prints 2080032704 instead of 6375000000: the true total wrapped modulo 2^32 without any error. A uint32 table is only safe while 255 x H x W < 2^32, about 16.8 million pixels (for example 4096 x 4096).

=== practice
- 303 core
  cue: Many sum queries over different ranges of an array that never changes after construction.
  hint: Doing the work per query costs O(n) each time. What could you compute once so that each query becomes a couple of lookups?
  insight: Store pre with pre[0] = 0 and pre[i + 1] = pre[i] + nums[i]; the inclusive range left..right is pre[right + 1] - pre[left]. Building is O(n) and every query is two lookups and one subtraction.
  cost: O(n) build, O(1) per query, O(n) space
  pattern: prefix-sum
- 724 core
  cue: Find an index where the total on its left equals the total on its right.
  hint: If you know the total of the whole array and the sum to the left of i, what is the sum to the right of i?
  insight: Keep a running left sum; index i balances when left == total - left - nums[i]. Test before adding nums[i] to left and return the first index that balances, or -1. One pass after computing the total.
  cost: O(n) time, O(1) space
  pattern: prefix-passes
- 560 core
  cue: Count contiguous subarrays with an exact sum, and the values may be negative.
  hint: A window cannot decide when to shrink once values can be negative. Write the sum of nums[j:i] as a difference of two prefix sums: which earlier value are you looking for at step i?
  insight: nums[j:i] sums to k exactly when pre[j] = pre[i] - k, so keep a Counter of earlier prefixes seeded with {0: 1}; at each step add seen[cur - k], then record cur. Looking up before recording keeps every counted subarray non-empty.
  cost: O(n) time, O(n) space
  pattern: prefix-map
- 974 core
  cue: Count subarrays whose sum is a multiple of k, with negative values allowed.
  hint: When is pre[i] - pre[j] a multiple of k? Compare the two prefixes modulo k.
  insight: A difference is divisible by k exactly when both prefixes leave the same remainder, so count remainders in a list of size k (remainder 0 seeded once) and add the count of the current remainder before incrementing it. Python's % already returns 0..k-1 for negative sums; in C++ or Java normalise with ((x % k) + k) % k.
  cost: O(n + k) time, O(k) space
  pattern: prefix-mod
- 525 core
  cue: The longest stretch of a binary array with as many 0s as 1s.
  hint: Can you rewrite "equal counts" as "a sum equals something" by changing how you score each element?
  insight: Score 1 as +1 and 0 as -1; a stretch is balanced when its sum is 0, that is when two prefix balances are equal. Store the first index of each balance (seed balance 0 at index -1) and maximise i - first[balance]; never overwrite a first index.
  cost: O(n) time, O(n) space
  pattern: prefix-mod
- 304 core
  cue: Many rectangle-sum queries on a matrix that does not change.
  hint: Extend the 1D idea: what single number per corner would let you peel any rectangle out of a few stored values?
  insight: Let P[r][c] be the sum of everything above and to the left of corner (r, c) in an (m + 1) x (n + 1) table, built with P[r+1][c+1] = cell + P[r][c+1] + P[r+1][c] - P[r][c]. An inclusive rectangle (r1, c1)..(r2, c2) is P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1].
  cost: O(mn) build, O(1) per query, O(mn) space
  pattern: prefix-2d
- 1109 core
  cue: Many bookings that each add seats to every flight from first to last, and you only need the final totals.
  hint: Touching every flight of every booking is O(n) per booking. Record only where each booking starts and where it stops.
  insight: Difference array: d[first - 1] += seats and d[last] -= seats (the input is 1-indexed and inclusive), then one running sum over d gives every flight's total. The final pass costs O(n) however long the bookings are.
  cost: O(n + b) time for b bookings, O(n) space
  pattern: prefix-diff
- 1749 derive
  cue: The largest absolute value of any subarray sum.
  hint: Every subarray sum is a difference of two prefix sums. Which pair of prefixes gives the largest absolute difference?
  insight: |pre[i] - pre[j]| is largest for the largest and the smallest prefix, the empty prefix 0 included, and with an absolute value their order does not matter. So the answer is max(pre) - min(pre), tracked in one pass with two running extremes.
  cost: O(n) time, O(1) space
  pattern: prefix-passes
- 1074 core
  cue: Count all submatrices whose sum equals a target, in a grid of up to about 100 x 100.
  hint: Fix the top and bottom rows of the submatrix. What 1D problem is left?
  insight: For each pair of rows (top, bottom), keep running column sums for the band; the submatrices inside that band with sum target are exactly the subarrays of the column-sum array with sum target, which the prefix-map count finds in O(columns). Put the smaller dimension in the outer pair loop.
  cost: O(min(m, n)^2 x max(m, n)) time, O(max(m, n)) extra space
  pattern: prefix-2d
- 2536 stretch
  cue: Add 1 to many sub-rectangles of an n x n grid, then return the whole grid.
  hint: The 1D trick marks a start and a stop. What marks does a rectangle need so that a 2D running sum recreates it?
  insight: Use a 2D difference array: +1 at (r1, c1), -1 at (r1, c2 + 1), -1 at (r2 + 1, c1) and +1 at (r2 + 1, c2 + 1) in an (n + 1) x (n + 1) table, then take running sums along each row and then down each column.
  cost: O(q + n^2) time, O(n^2) space
  pattern: prefix-diff
- 995 stretch
  cue: Flip windows of exactly k consecutive bits to turn the whole array into 1s, with as few flips as possible.
  hint: Look at the leftmost 0. Which flips can still change it, and is there any choice about using one?
  insight: Scan left to right keeping the number of active flips with a difference array (+1 where a flip starts, -1 at start + k). If the bit at i is 0 after an even number of flips (or 1 after an odd number), a flip must start at i, since no later flip covers i; if i + k > n, return -1. Each step is O(1).
  cost: O(n) time, O(n) space (O(1) with in-place markers)
  pattern: prefix-diff
- 689 stretch
  cue: Choose three non-overlapping length-k subarrays with the largest total, preferring the smallest starting indices on ties.
  hint: Fix the middle window. What do you need to know about the best window entirely to its left and the best entirely to its right?
  insight: Compute every window sum from prefix sums, then best_left[i] (index of the best window starting at or before i, keeping the earlier one on ties with >) and best_right[i] (best starting at or after i, preferring the earlier one with >= while scanning right to left). Try every middle start and combine three O(1) lookups.
  cost: O(n) time, O(n) space
  pattern: prefix-passes
