=== card | 303

## The problem

Prepare an unchanged integer array so that repeated requests can return the sum from a given left index through a given right index, including both endpoints. Construct `NumArray` once and call `sumRange` for each request.

## Constraints and what they imply

Indices are zero based and valid, with left no greater than right. The array can contain negative values, and many queries can share the same array. There are no updates after construction, so preprocessing can be reused. A single query may cover the whole array; summing its elements every time ignores this reuse.

## Brute force

For each query, visit each element in the requested interval and add it. This takes time proportional to the interval length, up to O(n) per query, and constant extra space. It is a useful independent baseline, particularly for singleton and full-array intervals.

## The insight

Let prefix position `i` contain the sum of the first `i` elements. The sum through `right` contains the sum before `left`, so subtracting the latter removes exactly the unwanted portion. The initial zero represents an empty prefix and makes the same formula work when the range begins at index zero.

## Optimal solution, traced

```steps
nums = [3, -2, 5]
---
prefix = [0, 3, 1, 6]
---
query [1, 2]: prefix[3] - prefix[1] = 6 - 3 = 3
---
query [0, 0]: prefix[1] - prefix[0] = 3
```

## Code

```python
class NumArray:
    def __init__(self, nums):
        self.prefix = [0]
        for value in nums:
            self.prefix.append(self.prefix[-1] + value)

    def sumRange(self, left, right):
        return self.prefix[right + 1] - self.prefix[left]
```

## Complexity

Construction takes O(n) time and O(n) space. Each query takes O(1) time and no additional space. The storage belongs to the object and is reused across calls.

## Mistakes and edge cases

Do not subtract the prefix ending at `left`: that would also remove the left endpoint. Do not use `right` instead of `right + 1`. Negative numbers do not invalidate subtraction, and a one-element query uses exactly the same formula. If the array changes later, the stored sums become stale.

## Variations

- For point updates between queries, consider a Fenwick tree instead of a static prefix array.
- For a half-open query `[left, right)`, use `prefix[right] - prefix[left]`.

=== card | 724

## The problem

Find the earliest index in an integer array whose elements strictly before it sum to the same value as those strictly after it. Return -1 if no such index exists. An empty side has sum zero.

## Constraints and what they imply

The array may contain positive, zero, and negative integers. Endpoints are legitimate candidates, and several positions may satisfy the condition. Returning the first rules out merely finding any balanced index. Since the full sum is available in one pass, the right side need not be recomputed at every position.

## Brute force

Try each index and separately sum the portions on both sides. Each pair of sums costs O(n), producing O(n²) time and O(1) auxiliary space if the ranges are traversed without copying. This directly reflects the definition and is convenient for testing.

## The insight

Before inspecting a candidate, maintain the sum strictly to its left. The whole-array total equals left plus the current element plus right, so the right sum is `total - left - current`. Check equality before adding the current value to left. The invariant is true initially because the first index has an empty left side; adding the current value establishes it for the next index.

## Optimal solution, traced

```steps
nums = [1, 7, 3, 6, 5, 6], total = 28
---
i=0: left=0, right=27; advance left to 1
---
i=1: left=1, right=20; advance left to 8
---
i=2: left=8, right=17; advance left to 11
---
i=3: left=11, right=11; return 3
```

## Code

```python
class Solution:
    def pivotIndex(self, nums):
        total = sum(nums)
        left = 0
        for i, value in enumerate(nums):
            if left == total - left - value:
                return i
            left += value
        return -1
```

## Complexity

Computing the total and scanning the candidates take O(n) time overall. The running totals and index use O(1) auxiliary space.

## Mistakes and edge cases

Adding the candidate before testing includes it on the wrong side. Both sides of a single-element array are empty, so index zero qualifies. Negative values can produce surprising ties, and all-zero arrays have multiple answers; scanning in order and returning immediately chooses the earliest one.

## Variations

- Return every balanced index by collecting matches instead of returning early.
- Balance weighted values by replacing each element with its weighted contribution before applying the same invariant.

=== card | 560

## The problem

Count the nonempty contiguous slices of an integer array whose elements add to a given target `k`. Overlapping slices count separately, as do different slices with the same contents.

## Constraints and what they imply

Entries and the target may be negative or zero. Extending a slice can therefore either raise or lower its sum, so the usual monotone sliding-window argument does not apply. Repeated prefix sums are meaningful: they represent distinct starting positions, not duplicate data to discard. The result is a count rather than the length of one slice.

## Brute force

Choose every left endpoint, extend the right endpoint while maintaining a running sum, and increment the answer whenever that sum equals `k`. There are O(n²) slices and each extension costs O(1), so the time is O(n²) and the extra space is O(1). This works with negative values and gives a straightforward oracle.

## The insight

Define `P[t]` as the sum of the first `t` elements, including `P[0] = 0`. Slice `[s, t)` has sum `P[t] - P[s]`; it reaches the target exactly when `P[s] = P[t] - k`. As each endpoint `t` arrives, count how many earlier prefixes have that value. A frequency map preserves all matching starts. Then record the current prefix for later endpoints.

The map invariant is that it contains precisely prefixes with positions strictly before the endpoint currently being counted. Seeding the empty prefix permits slices starting at zero. Looking up before inserting also prevents counting an empty slice when `k` is zero. Every nonempty slice is associated with its unique ending position and is counted once there.

## Optimal solution, traced

```steps
nums = [1, -1, 1], k = 1; seen = {0: 1}, sum = 0, answer = 0
---
value 1: sum=1, seen[0]=1, answer=1; record 1
---
value -1: sum=0, seen[-1]=0, answer=1; record 0
---
value 1: sum=1, seen[0]=2, answer=3; record 1
```

## Code

```python
from collections import defaultdict

class Solution:
    def subarraySum(self, nums, k):
        seen = defaultdict(int)
        seen[0] = 1
        total = answer = 0
        for value in nums:
            total += value
            answer += seen[total - k]
            seen[total] += 1
        return answer
```

## Complexity

The scan takes expected O(n) time with hash-map operations and O(n) space for up to n distinct prefix values. Python integers avoid fixed-width overflow; in a fixed-width language the sum and answer may need a wider type.

## Mistakes and edge cases

A set loses multiplicity, for example when zeros create several equal prefixes. Inserting before querying adds a spurious empty slice for target zero. The initial zero prefix must have frequency one, not zero. Neither a negative running sum nor a target of zero requires a special case.

## Variations

- Store the earliest index for each prefix instead of frequencies to find the longest target-sum slice.
- Store the latest index to find a shortest nonempty target-sum slice, taking care to query first.

=== card | 974

## The problem

Count nonempty contiguous slices whose sum is divisible by a positive integer `k`. Elements may be negative, and different positions define different slices even if their values are identical.

## Constraints and what they imply

The divisor is positive. Array entries may have either sign, so no increasing-window invariant is available. Divisibility depends only on one of `k` remainder classes, not on the full value of each prefix. A dense table is appropriate when O(k) storage is acceptable; for a very large divisor a sparse map can hold only remainders that occur.

## Brute force

Enumerate the starting index and extend each slice with a running total, checking whether the total has remainder zero. There are O(n²) slices, giving O(n²) time and O(1) extra space. This baseline does not rely on the prefix-remainder observation.

## The insight

With prefix sums `P`, a slice `[s, t)` has sum `P[t] - P[s]`. This difference is divisible by `k` exactly when the two prefixes have equal remainders modulo `k`. Maintain the number of earlier prefixes in each class. For each new prefix, add the current class frequency to the answer, then increase that frequency.

Initially the zero remainder occurs once for the empty prefix. Before counting an endpoint, the frequencies describe precisely the earlier prefix positions, so each matching starting position forms a nonempty slice and every valid slice appears at its unique endpoint. Python's modulo by positive `k` yields a nonnegative remainder even for negative sums.

## Optimal solution, traced

```steps
nums = [4, -1, 2], k = 3; counts = [1, 0, 0], remainder=0, answer=0
---
4: remainder=1, add counts[1]=0; counts becomes [1, 1, 0]
---
-1: remainder=0, add counts[0]=1; counts becomes [2, 1, 0]
---
2: remainder=2, add counts[2]=0; counts becomes [2, 1, 1]
---
return 1
```

## Code

```python
class Solution:
    def subarraysDivByK(self, nums, k):
        counts = [0] * k
        counts[0] = 1
        remainder = answer = 0
        for value in nums:
            remainder = (remainder + value) % k
            answer += counts[remainder]
            counts[remainder] += 1
        return answer
```

## Complexity

Initializing the table costs O(k), and the scan costs O(n), for O(n + k) time and O(k) auxiliary space. A hash map trades the dense initialization for expected O(n) time and at most O(min(n, k)) stored classes.

## Mistakes and edge cases

Record a class after counting, or an empty slice is added at each position. The empty prefix must be counted before the scan so a valid slice beginning at zero is included. When `k` is one, every nonempty slice qualifies. Languages whose remainder can be negative require normalization before indexing.

## Variations

- Count slices with a specified remainder `r` by looking for earlier remainder `(current - r) % k`.
- Determine whether any qualifying slice has length at least two by storing the earliest index for each remainder.

=== card | 525

## The problem

Given a binary array, return the maximum length of a contiguous slice containing the same number of zeroes and ones. Return zero if no nonempty balanced slice exists.

## Constraints and what they imply

Every entry is either zero or one. A balanced slice can begin anywhere, including index zero, and it can overlap other balanced slices. Because the goal is maximum length rather than count, retaining just a frequency for each state is insufficient: we need the earliest position at which that state occurred.

## Brute force

For every left endpoint, extend the right endpoint and maintain separate counts of zeroes and ones. Whenever they agree, compare the length with the best so far. The O(n²) candidate slices can be checked in O(1) per extension, using O(1) extra space.

## The insight

Treat each one as +1 and each zero as -1. The sum of a slice is zero exactly when its two counts match. A zero-sum slice has equal balances immediately before and after it. At each position, therefore, find the earliest earlier position with the same balance. This gives the longest balanced slice ending here.

Seed balance zero at index -1 to represent the empty prefix before the array. Only record a balance the first time it occurs. The invariant is that the table contains the earliest index for each previously encountered balance; never overwriting it ensures no longer candidate ending at the current position is missed. Taking the maximum over all endpoints gives the global optimum.

## Optimal solution, traced

```steps
nums = [0, 1, 0, 0, 1, 1]; first = {0: -1}, balance=0
---
i=0: balance=-1; record first[-1]=0
---
i=1: balance=0; length=1-(-1)=2
---
i=2: balance=-1; length=2-0=2
---
i=3: balance=-2; record first[-2]=3
---
i=4: balance=-1; length=4-0=4
---
i=5: balance=0; length=5-(-1)=6; return 6
```

## Code

```python
class Solution:
    def findMaxLength(self, nums):
        first = {0: -1}
        balance = best = 0
        for i, value in enumerate(nums):
            balance += 1 if value == 1 else -1
            if balance in first:
                best = max(best, i - first[balance])
            else:
                first[balance] = i
        return best
```

## Complexity

The scan uses expected O(n) time with dictionary lookups and O(n) auxiliary space for distinct balances. There is one entry at most per position plus the initial empty prefix.

## Mistakes and edge cases

Overwriting a first occurrence with a later one shortens subsequent candidates. Initializing balance zero at index zero rather than -1 loses one element for slices beginning at the array's start. All-equal inputs correctly produce zero, while a two-element array `[0, 1]` produces two. The scoring assumes binary inputs.

The answer is always even: every qualifying slice contains two equally sized groups. That observation can help check a result, although it does not identify the optimal boundaries by itself.

## Variations

- Count balanced slices by storing frequencies rather than earliest indices.
- For a longest slice with a fixed excess of ones, look up the balance minus that excess.

=== card | 304

## The problem

Preprocess a fixed integer matrix and answer repeated requests for the sum within an inclusive, axis-aligned rectangle. A request gives top row, left column, bottom row, and right column in zero-based coordinates.

## Constraints and what they imply

The matrix is rectangular and nonempty; queried corners are valid and ordered. Values may be negative. The matrix does not change between requests, so a table of cumulative sums can be built once and reused. Rectangles can touch any boundary, making a zero-padded row and column useful.

## Brute force

For each query visit every cell inside its two row and column bounds. This costs O(area) time per query, up to O(mn), and O(1) auxiliary space. With many large rectangles, the same cells are repeatedly added.

## The insight

Let `P[r][c]` sum the cells in rows before `r` and columns before `c`. The extra top row and left column consist of zeroes. Build a prefix from the cell itself, the prefix above, and the prefix to the left, subtracting their overlap once.

To answer a rectangle, take the prefix through its bottom-right corner, remove the strip above and the strip to the left, then restore their overlap, which was removed twice. This inclusion-exclusion leaves every inside cell exactly once and every outside cell zero times. Shifting the inclusive bottom and right coordinates by one converts them into prefix boundaries.

## Optimal solution, traced

```steps
matrix = [[1, 2], [3, 4]]
---
padded prefix rows: [0, 0, 0], [0, 1, 3], [0, 4, 10]
---
query rows 0..1, column 1..1:
    P[2][2] - P[0][2] - P[2][1] + P[0][1]
    = 10 - 0 - 4 + 0 = 6
```

## Code

```python
class NumMatrix:
    def __init__(self, matrix):
        m, n = len(matrix), len(matrix[0])
        self.prefix = [[0] * (n + 1) for _ in range(m + 1)]
        for r in range(m):
            for c in range(n):
                self.prefix[r + 1][c + 1] = (
                    matrix[r][c] + self.prefix[r][c + 1]
                    + self.prefix[r + 1][c] - self.prefix[r][c]
                )

    def sumRegion(self, row1, col1, row2, col2):
        p = self.prefix
        return (p[row2 + 1][col2 + 1] - p[row1][col2 + 1]
                - p[row2 + 1][col1] + p[row1][col1])
```

## Complexity

Building the table costs O(mn) time and O(mn) space. A query uses four entries, O(1) time, and O(1) additional space.

## Mistakes and edge cases

The overlap needs to be subtracted during construction and added back during a query. Independent rows are essential: multiplying a single row list aliases all rows in Python. A single cell and a rectangle covering the whole matrix are useful tests. Subsequent mutations of the input are not reflected in the prefix table.

As a concrete boundary check, a top-left anchored rectangle subtracts two zero prefixes and adds a zero overlap. For an interior rectangle, both removed strips can contain the same upper-left cells, which explains why the final addition is indispensable even when all matrix entries happen to be positive. With negative entries the same algebra applies; no monotonicity assumption is involved.

## Variations

- For mutable cells, use a two-dimensional Fenwick tree or another dynamic range-sum structure.
- For half-open rectangles, use the same inclusion-exclusion directly on their four prefix boundaries.

=== card | 1109

## The problem

There are `n` flights numbered from one. Each booking `[first, last, seats]` adds its seat count to every flight from `first` through `last`, inclusive. Return the final seat total for every flight in order after all bookings.

## Constraints and what they imply

Each booking has valid ordered flight numbers within `1..n`, and its seat count is positive. Flights and bookings can both be numerous, while only the final totals are requested. Processing each full interval separately can repeat the same work many times. Additions commute, so their boundary effects can be accumulated before any totals are reconstructed.

## Brute force

Start with `n` zero totals. For every booking, add its seats to each flight it covers. This takes O(n + sum of booking lengths), at most O(n times b) for `b` bookings, with O(n) space for the result. It is an easy correctness oracle because it directly performs the specified updates.

## The insight

Instead of storing the totals immediately, store changes between adjacent flights. An inclusive range addition starts contributing at its first flight and stops just after its last. In zero-based coordinates, add `seats` at `first - 1` and subtract it at `last`. A sentinel at index `n` safely receives a stop after the final flight.

Once all boundaries have been marked, scan left to right with a running sum. At each flight, every booking whose start has been passed contributes, and every booking whose stop has been passed no longer contributes. Thus the running value equals exactly the sum of the active bookings for that flight. Superposition makes overlapping bookings work without special cases.

## Optimal solution, traced

```steps
n=4, bookings=[[1, 2, 5], [2, 4, 3]]
---
boundary marks: [5, 3, -5, 0, -3]
---
running totals at flights 1..4: 5, 8, 3, 3
---
the final -3 is a sentinel outside the output
```

## Code

```python
class Solution:
    def corpFlightBookings(self, bookings, n):
        diff = [0] * (n + 1)
        for first, last, seats in bookings:
            diff[first - 1] += seats
            diff[last] -= seats
        total = 0
        result = []
        for i in range(n):
            total += diff[i]
            result.append(total)
        return result
```

## Complexity

Marking `b` bookings and scanning `n` flights take O(b + n) time. The difference array and returned result each use O(n) space.

## Mistakes and edge cases

The stop is at `last`, not `last - 1`, because the input's last flight is inclusive and one based. A booking covering the final flight writes its stop into the sentinel rather than outside the array. Multiple starts or stops at the same boundary must be added, not assigned. An empty booking list yields all zeroes.

## Variations

- Allow signed updates to model cancellations as long as that is permitted by the surrounding application.
- Apply the difference updates to an existing base array by adding each reconstructed change to its base value.

=== card | 1749

## The problem

Return the largest absolute sum obtainable from a contiguous slice of an integer array. An empty slice is allowed and contributes zero, so the answer is never negative.

## Constraints and what they imply

Values may be positive, negative, or zero. The maximum absolute sum may arise from either a large positive sum or a large negative sum, so tracking only the largest ordinary subarray is not enough. Prefix sums can rise and fall, but their largest difference in magnitude is determined by their extrema.

## Brute force

Enumerate each left endpoint and accumulate the sum as the right endpoint advances. Compare the absolute value with the best answer, initialized to zero for the empty slice. This considers O(n²) nonempty slices in O(n²) time and O(1) extra space.

## The insight

Let `P[0] = 0`, and let `P[i]` be the sum of the first `i` elements. The sum of a slice is a difference of two prefixes. The largest possible absolute difference among any prefix values is `max(P) - min(P)`: no pair can exceed that range, and a pair attaining the two extremes achieves it.

Whichever extreme appears first supplies the start boundary, so their time order does not invalidate the slice. If both extremes occur at the same position, the range is zero, which the empty slice achieves. Include the initial prefix, then update the running sum and both extrema while scanning. This is equivalent to considering both positive and negative extremes without storing the whole prefix array.

## Optimal solution, traced

```steps
nums = [2, -5, 1]; initial prefix=0, minimum=0, maximum=0
---
after 2: prefix=2, minimum=0, maximum=2
---
after -5: prefix=-3, minimum=-3, maximum=2
---
after 1: prefix=-2, minimum=-3, maximum=2
---
return 2 - (-3) = 5, achieved by the slice [-5]
```

## Code

```python
class Solution:
    def maxAbsoluteSum(self, nums):
        total = low = high = 0
        for value in nums:
            total += value
            low = min(low, total)
            high = max(high, total)
        return high - low
```

## Complexity

One scan takes O(n) time, and the running prefix and extrema take O(1) auxiliary space. No slice or prefix table is materialized.

## Mistakes and edge cases

Omitting the initial zero prefix misses an optimal slice beginning at the first element. The minimum prefix may appear after the maximum: absolute value permits either ordering. All-zero input returns zero. In fixed-width arithmetic, account for the range of cumulative sums and their difference.

An array of entirely negative entries can have its optimum across the whole array; a maximum-positive-sum-only method would miss it. Similarly, returning the larger absolute prefix alone misses a slice whose two endpoints are both away from the beginning.

## Variations

- Track the indices of the extreme prefixes to recover one optimal slice, ordering the two indices before slicing.
- Track maximum and minimum subarray sums separately with two Kadane-style scans and compare their magnitudes.

=== card | 1074

## The problem

Count the nonempty axis-aligned rectangular regions of an integer matrix whose entries sum to a specified target. Rectangles are distinguished by their row and column boundaries, even when their contents happen to be equal.

## Constraints and what they imply

The matrix is nonempty and rectangular. Values and the target may be negative, zero, or positive, so extending a rectangle does not move its sum in a predictable direction. A rectangle has four boundaries; testing all boundary quadruples is expensive. The two dimensions need not be equal, so choosing the smaller dimension for the pair of outer boundaries matters.

The returned count may be large: an all-zero matrix with target zero qualifies at every possible rectangle. Python integers accommodate this naturally, while implementations in fixed-width languages should check the required numeric range. The matrix is read only; no modification or square-grid assumption is needed.

## Brute force

Choose top, bottom, left, and right boundaries, and add every cell in each chosen rectangle. This is O(m³n³) in the worst case, with O(1) auxiliary space if cells are traversed directly. A two-dimensional prefix table would reduce the rectangle sum to O(1), but still leaves O(m²n²) boundary choices and O(mn) table space. Either formulation is useful as an independent oracle on very small grids.

## The insight

Fix two boundaries along one dimension. Collapse all cells between those boundaries into a one-dimensional array: each entry is the sum along the fixed band at one coordinate of the other dimension. Every rectangle inside that band corresponds to exactly one nonempty contiguous slice of this array, and its sum equals the slice sum. The two remaining rectangle boundaries are precisely that slice's endpoints.

For each fixed starting boundary, begin with a zeroed collapsed array and extend the ending boundary one step at a time, adding the newly included row or column. Count target-sum slices in the current array using prefix frequencies: if the current prefix is `s`, a previous prefix `s - target` creates a target-sum slice. Seed the empty prefix and query its frequency before recording the current prefix. Reinitialize this frequency map for every band; prefix positions from different bands must not mix.

Pair boundaries on the smaller dimension. The implementation uses a coordinate choice instead of transposing and copying the matrix: when rows are smaller it reads rows as bands, and otherwise it reads columns as bands. In either orientation the collapsed array has length equal to the larger dimension. This gives the advertised bound even for a very narrow matrix.

For correctness, each outer pair is visited exactly once. Within that pair each valid slice has a unique ending boundary, and the frequency lookup counts exactly its earlier starting boundary. Conversely, every counted pair of prefixes determines a nonempty slice and hence a valid rectangle with the chosen band. These mappings are bijective, so no rectangle is missed or counted twice.

## Optimal solution, traced

```steps
matrix = [[1, -1], [0, 1]], target = 0; pair rows
---
top=0, bottom=0: collapsed=[1, -1]
  prefixes 0, 1, 0: the last 0 matches the initial 0; add 1
---
top=0, bottom=1: collapsed=[1, 0]
  prefixes 0, 1, 1: the last 1 matches the earlier 1; add 1
---
top=1, bottom=1: collapsed=[0, 1]
  prefixes 0, 0, 1: the first new 0 matches the initial 0; add 1
---
return 3
```

## Code

```python
from collections import defaultdict

class Solution:
    def numSubmatrixSumTarget(self, matrix, target):
        m, n = len(matrix), len(matrix[0])
        small, large = min(m, n), max(m, n)
        pair_rows = m <= n
        answer = 0
        for start in range(small):
            collapsed = [0] * large
            for end in range(start, small):
                for j in range(large):
                    collapsed[j] += matrix[end][j] if pair_rows else matrix[j][end]
                seen = defaultdict(int)
                seen[0] = 1
                prefix = 0
                for value in collapsed:
                    prefix += value
                    answer += seen[prefix - target]
                    seen[prefix] += 1
        return answer
```

## Complexity

There are O(s²) bands for `s = min(m, n)`. Updating and counting each band costs expected O(l) with `l = max(m, n)` using a hash map. Total expected time is O(s²l). The collapsed array and its prefix-frequency map use O(l) auxiliary space; the input matrix is not copied.

## Mistakes and edge cases

Forgetting the empty prefix misses slices beginning at the first collapsed coordinate. Inserting a prefix before querying counts an empty slice when the target is zero. Reusing the frequency table across different bands incorrectly combines unrelated prefix sums. With a one-row or one-column matrix, there is only one possible band in the smaller dimension and the procedure reduces to the one-dimensional problem.

A zero target with repeated prefix sums requires frequencies rather than a set. Negative entries make a shrinking sliding window unreliable. If using a physically transposed copy instead of coordinate selection, include that copy in the space analysis.

## Variations

- Replace the frequency count with an earliest-prefix lookup to seek the largest-area target-sum rectangle, while retaining the fixed-band reduction.
- For a binary matrix and target equal to the area, investigate specialized all-ones rectangle methods instead of treating every sum independently.

=== card | 2536

## The problem

Start with an `n` by `n` zero grid. Each query describes an inclusive rectangle by its top-left and bottom-right coordinates; add one to every cell in that rectangle. Return the resulting grid after all queries.

## Constraints and what they imply

Coordinates are zero based, valid, and ordered. Queries may overlap, be identical, cover a single cell, or reach an edge. Only the final grid is requested, so individual updates need not be applied immediately. The output itself contains n² cells, establishing an unavoidable O(n²) output cost.

## Brute force

For each query loop over all its rows and columns, incrementing the affected cells. With `q` queries this costs O(n² + sum of rectangle areas), at most O(qn² + n²), and O(n²) space for the result. It directly models the operation and makes a good oracle for small grids.

## The insight

A one-dimensional range increment can be expressed by a positive change at its start and an opposite change after its end. In two dimensions, mark four corners of a padded difference table: add at the top-left, subtract just to the right and just below the rectangle, and add back at the diagonally opposite corner. The last mark corrects the overlap of the two subtractions.

After marking all queries, prefix-sum the table across rows and then down columns. A cell sees a particular query's four marks exactly when their coordinates are above and to its left. Inclusion-exclusion makes the net contribution one inside that query and zero outside. Adding contributions across queries works because prefix sums are linear. A sentinel row and column allow the stop coordinates to be `n`.

## Optimal solution, traced

```steps
n=3, query=[0, 1, 1, 2]
---
mark +1 at (0,1), -1 at (0,3), -1 at (2,1), +1 at (2,3)
---
after row prefixes, rows 0 and 1 are [0,1,1] and [0,0,0] within the grid
---
after column prefixes, output rows are [0,1,1], [0,1,1], [0,0,0]
---
sentinel column 3 carries the right stop and is not returned
```

## Code

```python
class Solution:
    def rangeAddQueries(self, n, queries):
        diff = [[0] * (n + 1) for _ in range(n + 1)]
        for r1, c1, r2, c2 in queries:
            diff[r1][c1] += 1
            diff[r1][c2 + 1] -= 1
            diff[r2 + 1][c1] -= 1
            diff[r2 + 1][c2 + 1] += 1
        for r in range(n):
            for c in range(1, n):
                diff[r][c] += diff[r][c - 1]
        for r in range(1, n):
            for c in range(n):
                diff[r][c] += diff[r - 1][c]
        return [row[:n] for row in diff[:n]]
```

## Complexity

Marking queries takes O(q) time; the two prefix passes and output copy take O(n²), for O(q + n²) total time. The padded table and returned grid each occupy O(n²) space.

## Mistakes and edge cases

The diagonal correction must be positive, not negative. An inclusive bottom or right edge uses a stop one position later. Do not construct the table by multiplying one inner list, which would alias rows. Sentinel cells need not be integrated because they lie outside every returned coordinate. Empty queries produce an all-zero grid.

## Variations

- Give each query its own signed increment by replacing the four unit marks with that increment and its negation.
- Support a rectangular `m` by `n` grid by padding and scanning each dimension separately.

=== card | 995

## The problem

Given a binary array and a positive window length `k`, a move toggles every bit in one contiguous window of exactly that length. Return the smallest number of moves that makes every bit one, or -1 if this cannot be done. A toggle changes zero to one and one to zero.

## Constraints and what they imply

The array contains only zeroes and ones, and `1 <= k <= n`. A move may start only where its entire window fits. Windows may overlap, so a bit can be toggled several times; only the parity of that count affects its final value. A naive implementation that toggles each of `k` bits per chosen move can take O(nk), which is unnecessary when windows are long.

The procedure below does not change the supplied array. Its boundary table is separate, and therefore the solution can be called again with the same input. A window of length one and a window covering the entire array are both within the contract and exercise different boundary cases.

## Brute force

One direct small-input oracle is to enumerate subsets of all possible window starts, apply each selected window to a copy, and choose the fewest selected windows that make the copy all ones. There are `n-k+1` possible starts, so at most O(2^(n-k+1) nk) work with a direct simulation and O(n) working space. Considering each start at most once is sufficient because two identical toggles cancel; removing both never worsens the move count. A breadth-first search over bit arrays gives another independent baseline.

## The insight

Scan from left to right. When position `i` is reached, all decisions at earlier starts have been made, and no future start greater than `i` can affect position `i`. If its effective bit is zero, a flip starting exactly at `i` is forced in any completion of those decisions. If its effective bit is one, starting a flip here would make it zero permanently, so no flip is allowed at this start. If a forced window would extend past the array, the instance is impossible.

This is a proof by induction over positions. Initially there are no earlier decisions. Assuming every feasible solution agrees with the decisions before `i`, the final value at `i` forces the next decision as described. Thus the algorithm either detects an impossibility shared by all solutions or produces the only useful choice at each start. The resulting valid sequence is optimal: repeating the same window twice would cancel and can never improve a minimum solution.

To avoid toggling an entire window, maintain the parity of flips currently covering `i`. A difference array records where each chosen flip expires: toggle a marker at `i+k`. At each position first apply its expiration marker, then compute the effective bit as the original bit XOR the active parity. When that bit is zero, toggle the active parity, record its future expiration, and increase the answer. A sentinel at `n` safely handles windows ending at the last element.

The loop invariant is that before testing the effective bit, active parity equals the number of earlier chosen windows still covering this index modulo two. Expiration happens before the test because a length-k window beginning at `s` covers only `s` through `s+k-1`, not `s+k`. This representation yields the same effective bits as actually applying all chosen windows.

## Optimal solution, traced

```steps
nums=[0, 0, 0, 1, 0, 1, 1, 0], k=3; active=0, flips=0
---
i=0: effective 0, flip [0..2], active=1, expire at 3, flips=1
---
i=1: effective 1; i=2: effective 1
---
i=3: expire to active=0; effective 1, no flip
---
i=4: effective 0, flip [4..6], active=1, expire at 7, flips=2
---
i=5: effective 0, flip [5..7], active=0, expire at 8, flips=3
---
i=6: effective 1; i=7: expire to active=1, effective 1
---
return 3
```

## Code

```python
class Solution:
    def minKBitFlips(self, nums, k):
        n = len(nums)
        expires = [0] * (n + 1)
        active = answer = 0
        for i, bit in enumerate(nums):
            active ^= expires[i]
            if bit ^ active == 0:
                if i + k > n:
                    return -1
                answer += 1
                active ^= 1
                expires[i + k] ^= 1
        return answer
```

## Complexity

The scan does O(1) work per bit, so time is O(n). The expiration table takes O(n) auxiliary space. A mutation-based encoding can reduce auxiliary space, but then the input contract and cleanup become important.

## Mistakes and edge cases

Expiration is at `i+k`, not the last included index `i+k-1`. Check whether the window fits before recording it. An already all-one array requires zero moves, while a late effective zero with no room to start a window requires -1. Overlapping flips cancel in parity; counting only the most recent flip fails. Use XOR or counts modulo two consistently.

## Variations

- Return the start indices as well as the count by appending `i` whenever a forced flip is made.
- If changing window lengths are allowed, the forced-decision argument no longer fixes a unique action; formulate a different optimization rather than reusing this greedy proof.

=== card | 689

## The problem

Select exactly three non-overlapping contiguous windows of length `k` from an integer array. Maximize their combined sum, and among equally good choices return the lexicographically smallest triple of starting indices in increasing order.

## Constraints and what they imply

The input admits three windows: `k >= 1` and `len(nums) >= 3*k`. In the standard setting values are positive, but the code also works with negative values. Windows of equal length do not overlap exactly when consecutive starts differ by at least `k`. A tie must be resolved on the full ordered triple, not merely on its total or its last index.

There are O(n) possible starts for a single window. Three nested choices have cubic worst-case cost, even if each window sum is available in constant time. The key is to fix the middle window: after it is fixed, the legal left and right choices lie in separate ranges and can be optimized independently.

## Brute force

Enumerate every triple of starts `a < b < c` with `a+k <= b` and `b+k <= c`. Sum the three windows and keep the greatest total, breaking ties lexicographically. Directly summing the windows costs O(n³k) in the worst case; precomputing window sums reduces this to O(n³ + n) time and O(n) space. A direct triple enumeration is particularly useful as an oracle for small inputs and negative values.

## The insight

First compute all length-k window sums with a rolling sum. Let `w[i]` be the sum of the window starting at `i`, with `L = n-k+1` possible starts. Build `left[i]`, the best starting index among `0..i`; when two sums tie, retain the earlier index. Build `right[i]`, the best starting index among `i..L-1`; while scanning from right to left, replace on equality so the newly encountered, smaller index wins.

For a fixed middle start `b`, the best legal left start is `left[b-k]`, and the best legal right start is `right[b+k]`. These ranges are independent: any left candidate ends before `b`, and any right candidate begins after the middle window. Maximizing each side separately therefore maximizes the combined total for that middle. The earliest best index on each side also gives the lexicographically smallest triple for that particular middle.

Enumerate middle starts from `k` through `L-k-1`, inclusive. Compare the candidate triples first by total and then explicitly by lexicographic order. This explicit comparison enforces the global tie rule without relying on scan order. Initialize the best total with `None`, rather than zero, so an all-negative extension of the input contract still works.

For correctness, each valid triple has exactly one middle start in the enumeration. For that start, replacing either outer window by its precomputed best cannot reduce its sum and preserves disjointness. Among equal-sum replacements the stored outer indices are earliest. Consequently the selected candidate is at least as good as any triple with the same middle, including its tie order. Comparing all candidates gives the global optimum and its lexicographically smallest representative.

## Optimal solution, traced

```steps
nums=[1, 2, 1, 2, 1, 2], k=2; window sums=[3, 3, 3, 3, 3]
---
left=[0, 0, 0, 0, 0]; right=[0, 1, 2, 3, 4]
---
only middle start b=2 is legal
---
left[0]=0, middle=2, right[4]=4; total=9
---
return [0, 2, 4]
```

## Code

```python
class Solution:
    def maxSumOfThreeSubarrays(self, nums, k):
        n = len(nums)
        window = sum(nums[:k])
        sums = [window]
        for i in range(k, n):
            window += nums[i] - nums[i - k]
            sums.append(window)
        count = len(sums)
        left = [0] * count
        best = 0
        for i in range(count):
            if sums[i] > sums[best]:
                best = i
            left[i] = best
        right = [0] * count
        best = count - 1
        for i in range(count - 1, -1, -1):
            if sums[i] >= sums[best]:
                best = i
            right[i] = best
        best_total = None
        answer = None
        for middle in range(k, count - k):
            a, c = left[middle - k], right[middle + k]
            total = sums[a] + sums[middle] + sums[c]
            candidate = [a, middle, c]
            if best_total is None or total > best_total or (total == best_total and candidate < answer):
                best_total, answer = total, candidate
        return answer
```

## Complexity

The rolling sums, two best-index arrays, and middle scan each take O(n) time. The three arrays use O(n) auxiliary space. Python's constant-size triple comparison is O(1).

## Mistakes and edge cases

Using `>=` in the left-to-right pass overwrites an earlier tied left index; using `>` in the right-to-left pass keeps a later tied right index. The right boundary is `middle+k`, not `middle+k-1`, because windows must not overlap. The smallest valid array has exactly one triple. Many equal windows exercise tie rules, while negative test values expose an incorrectly zero-initialized optimum.

## Variations

- Return the maximum total instead of indices by keeping only the best candidate's score.
- For a general number of windows, consider dynamic programming over the number chosen and the allowed prefix, with explicit tie handling.
