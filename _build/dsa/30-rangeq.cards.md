=== card | 307
time: 25 min

## The problem

Build an object for an integer sequence that supports replacing one entry and asking for the sum between two positions, endpoints included. A query must reflect every preceding replacement. For example, on `[2, -1, 4]`, the sum from 0 to 2 is 5; after replacing position 1 by 3 it is 9. The operations are online, so future assignments are not known when the object is created.

## Constraints and what they imply

The sequence has up to 30,000 entries and there can be tens of thousands of calls. Values and replacement values may be negative. Valid indices are zero-based, and query endpoints satisfy `left <= right`. A full rescan or a rebuilt prefix array for every call can be too expensive. Python integers also avoid overflow when intermediate sums are large.

## Brute force

Store the values directly. A replacement costs O(1), while a query loops across its interval in O(n) in the worst case. Alternatively, keep all prefix sums: queries become O(1), but changing one entry forces repair of up to n prefixes. Neither trade-off balances a mixed workload.

## The insight

A Fenwick tree stores overlapping power-of-two blocks, each ending at a particular one-based index. Prefix sums combine a logarithmic number of blocks. An assignment is not an increment: retain the old array value, compute `new - old`, then add that delta to every containing block. This invariant allows arbitrary positive, negative, or zero deltas.

## Optimal solution, traced

```steps
Initial values [2, -1, 4]: prefix(3) = 5, prefix(0) = 0
---
Set index 1 to 3: delta = 3 - (-1) = 4; update affected blocks
---
prefix(3) is now 9, so inclusive sum [0, 2] = 9 - 0 = {{9}}
```

Each tree cell contains precisely the sum of its represented block. Construction propagates each completed cell to its parent once, and the update visits exactly the cells whose block contains the changed position. Subtracting the prefix before `left` from the prefix through `right` leaves exactly the requested entries.

## Code

```python
class MutableSum:
    def __init__(self, nums):
        self.values = list(nums)
        self.n = len(nums)
        self.tree = [0] + list(nums)
        for i in range(1, self.n + 1):
            parent = i + (i & -i)
            if parent <= self.n:
                self.tree[parent] += self.tree[i]

    def update(self, index, value):
        delta = value - self.values[index]
        self.values[index] = value
        i = index + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix(self, length):
        total = 0
        while length:
            total += self.tree[length]
            length -= length & -length
        return total

    def sum_range(self, left, right):
        return self.prefix(right + 1) - self.prefix(left)
```

## Complexity

The linear build visits each cell once. An assignment and a query each take O(log n) time, since each Fenwick traversal changes one or more binary digits per step. The copied values and tree require O(n) auxiliary space.

## Mistakes and edge cases

- Adding the new value instead of the difference corrupts repeated assignments.
- Convert external zero-based indices to the tree's one-based positions. Never update position zero: its low bit is zero.
- One element, negative entries, and setting a value to itself all work without special cases.

## Variations

- Support increments directly and omit the copied values.
- Use a segment tree if the desired aggregate has no subtraction operation.
- Batch all updates before querying and rebuild a static prefix table instead.

=== card | cses:1647
time: 25 min

## The problem

Preprocess a fixed integer array so that many questions can ask for the smallest entry between two inclusive positions. For `[7, 2, 5, 1]`, the minimum from indices 1 through 3 is 1. This implementation accepts zero-based indices; convert one-based input endpoints before calling it.

## Constraints and what they imply

Both array size and number of requests can be around 200,000. The data does not change between questions, so a one-time preprocessing cost is useful. Minimum is associative and idempotent: applying it to the same value twice changes nothing. That permits overlapping blocks, unlike a sum query.

## Brute force

Scan each requested interval, tracking its smallest value. This takes O(n) time per query and O(1) extra space, up to O(nq) over q requests. Precomputing the answer for every possible interval gives O(1) queries but requires O(n²) space and preprocessing.

## The insight

Store the minimum for every power-of-two length and starting position. A block of length `2**k` combines the two adjacent half-blocks from level `k-1`. For a query of length `L`, choose the largest power of two no larger than `L`. Its left-aligned and right-aligned blocks cover the interval; overlap is harmless for minimum.

## Optimal solution, traced

```steps
Array [7, 2, 5, 1], query [1, 3], length 3
---
Largest power of two not exceeding 3 is 2
    left block [2, 5] has min 2
    right block [5, 1] has min 1
---
The overlap at value 5 is harmless: min(2, 1) = {{1}}
```

The table invariant holds at level zero for single elements and propagates by combining the two halves. The selected blocks are inside the query and together cover it, so their combined minimum is exactly the answer.

For instance, on a five-element interval the two selected blocks have length four; they overlap on three entries. This overlap saves a separate combination of many disjoint blocks without changing the result.

## Code

```python
class StaticMinimum:
    def __init__(self, nums):
        self.table = [list(nums)]
        width = 2
        while width <= len(nums):
            half = width // 2
            prev = self.table[-1]
            self.table.append([
                min(prev[i], prev[i + half])
                for i in range(len(nums) - width + 1)
            ])
            width *= 2

    def query(self, left, right):
        length = right - left + 1
        level = length.bit_length() - 1
        width = 1 << level
        row = self.table[level]
        return min(row[left], row[right - width + 1])
```

## Complexity

There are O(log n) levels, each with at most n entries. Construction and storage are O(n log n), while each query performs two lookups and one comparison in O(1). The input is nonempty and the method expects valid nonempty intervals.

## Mistakes and edge cases

- Using overlapping blocks for sums double-counts elements; idempotence is essential here.
- A single-element interval selects level zero, and an exact power-of-two interval selects the same block twice.
- Rebuilding is required if the array changes; use a segment tree for online updates.

## Variations

- Store maximum or greatest common divisor instead of minimum.
- Return an index as well, using a consistent tie-breaking rule.
- Use disjoint blocks for a different associative operation at O(log n) query cost.

=== card | cses:1649
time: 25 min

## The problem

Keep an integer array under point replacements and answer the minimum on any inclusive interval after all earlier replacements. With `[6, 3, 8]`, changing index 1 to 9 makes the minimum of indices 0 through 1 equal 6. The interface below uses zero-based coordinates, unlike a one-based input stream.

## Constraints and what they imply

Arrays and operation streams can each have around 200,000 entries. Values need not be distinct. Static range-minimum preprocessing is not enough because a replacement can invalidate many stored intervals. Minimum has no inverse, so subtracting two prefix minima cannot recover a range minimum.

## Brute force

Maintain a plain list, replace entries in O(1), and scan each requested interval. A query may cost O(n), producing O(nq) time in a query-heavy sequence. Rebuilding all static answers after each replacement similarly wastes work outside the changed position.

## The insight

Represent adjacent ranges by a binary segment tree. Each node stores the minimum of its descendants, with unused padded leaves holding infinity. A replacement repairs one leaf-to-root path. For a query, move two endpoints inward and combine only nodes completely contained in the interval; these nodes form an exact, disjoint cover.

## Optimal solution, traced

```steps
Array [6, 3, 8], padded with infinity: root minimum is 3
---
Replace position 1 with 9; recompute its parent and the root
    values [6, 9, 8], root minimum 6
---
Query [0, 1]: the node covering those two leaves gives {{6}}
```

The leaves always equal the current values, and every internal node is the minimum of its two children. By induction the stored summary is correct for every represented range. The query combines a partition of the requested range, so no outside value can affect its answer.

The iterative query peels off a boundary node whenever it is wholly contained, then moves upward. At most two boundary nodes are selected per level, making even long intervals efficient.

## Code

```python
class DynamicMinimum:
    def __init__(self, nums):
        self.size = 1
        while self.size < len(nums):
            self.size *= 2
        self.tree = [float("inf")] * (2 * self.size)
        self.tree[self.size:self.size + len(nums)] = nums
        for i in range(self.size - 1, 0, -1):
            self.tree[i] = min(self.tree[2 * i], self.tree[2 * i + 1])

    def update(self, index, value):
        i = self.size + index
        self.tree[i] = value
        i //= 2
        while i:
            self.tree[i] = min(self.tree[2 * i], self.tree[2 * i + 1])
            i //= 2

    def query(self, left, right):
        left += self.size
        right += self.size + 1
        answer = float("inf")
        while left < right:
            if left & 1:
                answer = min(answer, self.tree[left])
                left += 1
            if right & 1:
                right -= 1
                answer = min(answer, self.tree[right])
            left //= 2
            right //= 2
        return answer
```

## Complexity

Rounding up to a power of two still uses O(n) nodes. The bottom-up build is O(n); each update and query is O(log n), with O(n) auxiliary space. A query uses constant additional working space.

## Mistakes and edge cases

- Infinity is the neutral value, not zero: zero would spoil a positive-only range.
- The internal loop uses a half-open interval even though the public query includes `right`.
- Replacing a current minimum can increase the answer, so recompute ancestors rather than only decreasing them.

## Variations

- Store maximum or sum with its appropriate identity.
- Store `(value, index)` pairs to retrieve a minimum's location.
- Add lazy propagation for interval updates rather than point replacements.

=== card | cses:1651
time: 25 min

## The problem

An array receives additions to inclusive intervals, interspersed with requests for the current value at one index. Starting from `[4, 1, 3]`, adding 2 on indices 0 through 1 gives `[6, 3, 3]`, so position 1 now reads 3. Use zero-based indices in the interface below.

## Constraints and what they imply

The input can contain about 200,000 elements and operations, making a linear pass over every updated interval potentially quadratic. Update amounts can be negative, and repeated updates can overlap. Values can exceed narrow integer limits after accumulation, so implementations in fixed-width languages should use a sufficiently wide type.

## Brute force

Keep the current array and add the supplied value to every element in the indicated interval. A point query is then O(1), but a single update can cost O(n). Reversing the work by recording updates and scanning them for every query also has O(nq) worst-case behavior.

## The insight

Maintain only the changes relative to the original array. Their difference array marks where each interval's effect begins and where it stops: add `delta` at `left`, subtract it immediately after `right`. A prefix sum of those markers gives the accumulated change at any position. A Fenwick tree handles each marker update and prefix query logarithmically.

## Optimal solution, traced

```steps
Initial values [4, 1, 3], all difference markers zero
---
Add 2 to [0, 1]: markers become [2, 0, -2]
---
At index 1, marker prefix is 2 and initial value is 1: answer {{3}}
```

For any one update, the prefix of its two markers equals zero before the interval, `delta` inside, and zero after it. Linearity means the prefixes sum the effects of all updates, including negative and overlapping ones. Adding the initial value produces the current value.

## Code

```python
class RangeAddPoint:
    def __init__(self, nums):
        self.values = list(nums)
        self.n = len(nums)
        self.bit = [0] * (self.n + 1)

    def _add(self, index, delta):
        i = index + 1
        while i <= self.n:
            self.bit[i] += delta
            i += i & -i

    def add_range(self, left, right, delta):
        self._add(left, delta)
        self._add(right + 1, -delta)

    def get(self, index):
        i = index + 1
        change = 0
        while i:
            change += self.bit[i]
            i -= i & -i
        return self.values[index] + change
```

## Complexity

Initialization copies n values and zeros the tree in O(n) time and space. Each update uses two O(log n) point changes, and each point query uses one O(log n) prefix sum. The second marker past the final element is intentionally ignored.

## Mistakes and edge cases

- Do not write the negative marker at `right`; that would exclude the last updated element.
- A range ending at the last index has no in-array stopping marker; `_add(n, ...)` safely does nothing.
- Preserve the initial values separately, because the tree stores changes only.

## Variations

- Use two Fenwick trees to support range additions and range sums.
- If all updates precede all queries, apply markers in an array and scan once.
- Use a lazy segment tree for a wider set of interval operations.

=== card | 1395
time: 30 min

## The problem

Count index triples `i < j < k` whose three ratings rise strictly or fall strictly in that order. For `[2, 5, 3, 4]`, only the indices of ratings `[2, 3, 4]` make such a triple. The order of soldiers matters; permuting them would change the count.

## Constraints and what they imply

The original setting has at most 1,000 soldiers with distinct positive ratings. A direct quadratic solution is already practical there; the implementation below illustrates a scalable O(n log n) histogram approach. The strict comparisons also make sense with duplicates, and the code intentionally handles them by excluding equal ratings from both sides.

## Brute force

Enumerate every triple of indices and test the two strict orderings. There are O(n³) triples, so the same comparisons are repeated many times. A useful intermediate approach fixes the middle index and scans both sides, which is O(n²) time and O(1) additional space.

## The insight

For each middle rating, count strictly smaller and strictly larger ratings separately on each side. Increasing triples contribute `smaller_left * larger_right`; decreasing triples contribute `larger_left * smaller_right`. Compress the ratings into ranks, and maintain Fenwick frequency trees for the prefix and suffix while moving the middle position.

## Optimal solution, traced

```steps
Ratings [2, 5, 3, 4], take middle index 2 with rating 3
---
Left [2, 5]: smaller = 1, larger = 1
Right [4]: smaller = 0, larger = 1
---
Contribution 1*1 + 1*0 = 1; other middle positions contribute 0
    total {{1}}
```

Every valid triple has exactly one middle index. At that index the independent left and right choices multiply, and a triple cannot be both increasing and decreasing. The two histograms contain exactly the positions on their respective sides after removing the current rating.

After the contribution is recorded, inserting that rating into the left histogram prepares the next middle position. Thus the histograms move monotonically through the array without rebuilding their counts from scratch.

## Code

```python
def count_teams(ratings):
    ranks = {value: i + 1 for i, value in enumerate(sorted(set(ratings)))}
    m = len(ranks)
    left = [0] * (m + 1)
    right = [0] * (m + 1)

    def add(bit, i, delta):
        while i <= m:
            bit[i] += delta
            i += i & -i

    def prefix(bit, i):
        total = 0
        while i:
            total += bit[i]
            i -= i & -i
        return total

    for value in ratings:
        add(right, ranks[value], 1)
    answer = 0
    for i, value in enumerate(ratings):
        rank = ranks[value]
        add(right, rank, -1)
        less_left = prefix(left, rank - 1)
        greater_left = i - prefix(left, rank)
        less_right = prefix(right, rank - 1)
        greater_right = len(ratings) - i - 1 - prefix(right, rank)
        answer += less_left * greater_right + greater_left * less_right
        add(left, rank, 1)
    return answer
```

## Complexity

Sorting distinct ratings takes O(n log n). Each index performs a constant number of O(log n) Fenwick operations, for O(n log n) total time and O(n) space. Fewer than three ratings naturally contribute zero.

## Mistakes and edge cases

- Remove the middle element from the suffix before computing counts.
- Strictly larger means subtract the count at or below the rating, not merely the count below it.
- Include both directions; all equal ratings contribute no triples.

## Variations

- Count only increasing triples.
- Count increasing subsequences of a fixed length with one frequency tree per length.
- For the original small bound, implement and compare the simpler quadratic middle-index method.

=== card | 315
time: 35 min

## The problem

For every position in an integer sequence, report how many later positions hold a strictly smaller value. Preserve the original order in the returned list. For `[4, 1, 4, 2]`, the answer is `[2, 0, 1, 0]`: the equal 4 is not smaller than the first 4, but both 1 and 2 are.

This is a separate question for each index. It is not enough to compute the total number of inversions, although adding the returned counts would give that total.

## Constraints and what they imply

The sequence can have 100,000 elements, and entries can be negative, repeated, or widely separated. Quadratic comparison may do billions of checks. A frequency structure indexed directly by raw values would need an offset and potentially too much space for a generalized input. Only the relative ordering of values matters, not the distance between them.

Use one-based ranks for the Fenwick tree. The rank of a value must be the same at every occurrence; otherwise equal entries could accidentally be counted as smaller. The empty sequence is also naturally supported by the implementation.

## Brute force

For every index, loop over every index to its right and increment its count when the later value is smaller. This makes O(n²) comparisons in the worst case and needs O(n) output space. A sorted list of the seen values lets binary search locate the boundary, but inserting into a Python list still shifts O(n) entries.

Another conceptual alternative is a merge-sort inversion counter that attaches original indices to values. It achieves O(n log n), but requires careful handling of equal values during merging.

## The insight

Read from right to left. At the moment an element is processed, all and only the elements strictly to its right have already been inserted into a frequency histogram. Rank all distinct values in sorted order and query the number of inserted ranks below the current rank. Then insert the current rank for future positions.

A Fenwick prefix query includes its endpoint. Therefore querying `rank - 1` is the important strictness boundary. Querying the current rank would count duplicates as well. Compression preserves comparisons without depending on the numeric gap between values.

## Optimal solution, traced

```steps
Values [4, 1, 4, 2] have ranks 4->3, 1->1, 2->2
---
Scan right to left: 2 sees 0 smaller; insert rank 2
    4 sees 1 smaller; insert rank 3
---
1 sees 0 smaller; insert rank 1
    first 4 sees ranks 1 and 2, but not equal rank 3
    result {{[2, 0, 1, 0]}}
```

The loop invariant is that the tree contains the multiplicity of each value in the already processed suffix. It is initially empty, so the invariant holds for the last element. The prefix below the current rank counts exactly the required suffix values; inserting this value then establishes the invariant for the next iteration. All output positions are assigned once.

The rank dictionary is built before scanning, but knowing future ranks does not put those values into the histogram. Only explicit increments contribute to a query, so the tree still represents the correct suffix.

## Code

```python
def smaller_after(nums):
    ranks = {value: i + 1 for i, value in enumerate(sorted(set(nums)))}
    bit = [0] * (len(ranks) + 1)
    answer = [0] * len(nums)
    for pos in range(len(nums) - 1, -1, -1):
        rank = ranks[nums[pos]]
        i = rank - 1
        while i:
            answer[pos] += bit[i]
            i -= i & -i
        i = rank
        while i < len(bit):
            bit[i] += 1
            i += i & -i
    return answer
```

## Complexity

Sorting at most n distinct values costs O(n log n). Each of the n entries performs one prefix query and one insertion, both O(log n), so the total is O(n log n) time. The ranks, tree, and answer each occupy O(n) space. For an empty input, no update is attempted and the answer is empty.

## Mistakes and edge cases

- Query before insertion, so the tree models the suffix independently of the current position.
- Use `rank - 1` for strict inequality; all-equal input should yield only zeroes.
- Negative values need no special treatment after ranking. Large gaps do not create extra tree cells.
- Do not use rank zero for an update: the low-bit increment would never advance.
- A decreasing array yields counts `n-1, n-2, ... , 0`; an increasing one yields zeroes.

## Variations

- Reverse the direction to count smaller elements before each index.
- Sum the returned values to obtain the total inversion count.
- Count values in a specified interval to the right using two prefix counts.

=== card | 1649
time: 35 min

## The problem

Read instructions one at a time and conceptually insert each value into a sorted collection. Its insertion charge is the smaller of the number of previously inserted values strictly below it and the number strictly above it. Return the sum of all charges modulo 1,000,000,007. Equal values count on neither side.

For `[1, 5, 6, 2]`, the first three insertions each cost zero. At 2, one earlier value is smaller and two are larger, so the total cost becomes 1.

## Constraints and what they imply

There can be 100,000 instructions, with positive values up to 100,000 in the original problem. An array indexed by value is feasible for that bound, but coordinate compression also works if the magnitudes change or negative values are allowed. The incoming order cannot be rearranged: only earlier instructions contribute to a charge.

Repeated values are significant because each occurrence is a separate inserted item, yet none of the equal occurrences is strictly less or strictly greater. Keep frequencies, not merely a set of seen values. An empty stream has zero cost in this generalized interface.

## Brute force

Keep all earlier instructions in a list and scan it for each new value, counting both sides. The work is O(n²) time and O(n) storage. Maintaining an actual sorted Python list does not improve the worst-case time: although a binary search finds an insertion point in O(log n), insertion can shift O(n) items.

The problem asks only for the charge, so physically maintaining sorted values is unnecessary. It is sufficient to support counts by value.

## The insight

Use a frequency Fenwick tree over the sorted distinct instruction values. Before processing value `v`, let `rank` be its one-based compressed rank. The prefix through `rank - 1` counts strictly smaller prior values. The prefix through `rank` counts all prior values no greater than `v`, so subtracting that prefix from the number already inserted counts strictly larger values.

Add the smaller count to the running answer, and only then add one to the current rank. This ordering makes the histogram's interpretation obvious even when several consecutive instructions are equal.

## Optimal solution, traced

```steps
Instructions [1, 5, 6, 2]: the first three costs are 0
---
Before inserting 2, histogram represents [1, 5, 6]
    smaller = 1; at most 2 = 1; larger = 3 - 1 = 2
---
Charge min(1, 2) = 1; cumulative cost {{1}}
```

Initially the tree contains no items. At each step its frequencies are exactly the earlier instructions, so its prefix queries partition them into below, equal, and above groups. The computed charge is therefore the stated minimum. Inserting the current item restores the invariant for the next step. Modular reduction preserves the final sum because addition respects congruence.

For example, inserting another 2 after the traced example sees the first 2 in the equal group; that occurrence changes neither strict count. Frequency updates nevertheless retain it for later instructions.

## Code

```python
def insertion_cost(instructions):
    mod = 1_000_000_007
    ranks = {value: i + 1 for i, value in enumerate(sorted(set(instructions)))}
    bit = [0] * (len(ranks) + 1)

    def prefix(i):
        total = 0
        while i:
            total += bit[i]
            i -= i & -i
        return total

    answer = 0
    for inserted, value in enumerate(instructions):
        rank = ranks[value]
        smaller = prefix(rank - 1)
        larger = inserted - prefix(rank)
        answer = (answer + min(smaller, larger)) % mod
        i = rank
        while i < len(bit):
            bit[i] += 1
            i += i & -i
    return answer
```

## Complexity

Sorting and ranking require O(n log n) time. Two prefix queries and one increment per instruction each cost O(log n), so the full algorithm is O(n log n) time and O(n) auxiliary space. With a fixed maximum value M, direct indexing instead yields O(n log M + M) time and O(M) space, including initialization.

## Mistakes and edge cases

- Subtract the count at or below the current value when computing the larger side, not just the strictly smaller count.
- Always record the insertion, even when its charge is zero.
- The first instruction, a monotone stream, and an all-equal stream all have zero total cost.
- Compression uses all distinct values, including values not yet inserted; their frequencies remain zero until their turn.
- Apply the modulus to the accumulated result, not to the underlying frequencies.

## Variations

- Return the individual insertion charges instead of their sum.
- Support deletions by decreasing a frequency when a valid item is removed.
- Use a balanced order-statistics tree if future values are not available for offline compression.

=== card | 327
time: 40 min

## The problem

Given integers and inclusive bounds `lower` and `upper`, count nonempty contiguous slices whose sum lies within those bounds. For `[-2, 5, -1]` with bounds `[-2, 2]`, the qualifying sums are `-2`, `2`, and `-1`, giving 3. Slices with equal sums are still different if their endpoints differ.

Negative values are allowed, so extending a slice can either increase or decrease its sum. A sliding window that discards an endpoint based only on the current sum has no general monotonicity guarantee.

## Constraints and what they imply

There may be 100,000 entries, with signed values large enough that prefix sums need more than a 32-bit integer in fixed-width languages. Assume `lower <= upper`. A quadratic scan of all slices is too slow. The answer can also be quadratic in n, so count in a wide integer. Python integers naturally handle both concerns.

The coordinate set should include every prefix value, including the initial zero and the final total. The limits of a query need not themselves be prefix values; binary search locates their insertion positions without adding them to the compressed coordinates.

## Brute force

Start at each left endpoint, accumulate a running sum while moving the right endpoint, and test whether it lies in the permitted interval. This takes O(n²) time and O(1) working space beyond the input. It is simple and useful as an independent test oracle for small arrays.

Recomputing each slice sum from scratch would take O(n³); maintaining the running sum avoids that extra factor but still enumerates every possible slice.

## The insight

Let `P[j]` denote the sum of the first j entries, with `P[0] = 0`. A slice ending just before j has sum `P[j] - P[i]`, where `i < j`. Rearranging the bound gives `P[j] - upper <= P[i] <= P[j] - lower`. Thus each current prefix asks how many earlier prefixes fall inside a closed value interval.

Process prefixes in order using a Fenwick frequency tree over their compressed values. Binary search gives the number of distinct coordinates strictly below the lower endpoint and the number at or below the upper endpoint. Subtract the two corresponding frequency prefixes. Insert the current prefix only after asking the question, ensuring the slice is nonempty.

## Optimal solution, traced

```steps
Values [-2, 5, -1], bounds [-2, 2]; prefixes [0, -2, 3, 2]
---
Insert 0. For -2, earlier prefixes in [-4, 0] are [0]: count 1
---
For 3, earlier prefixes in [1, 5] are none
    for 2, earlier prefixes in [0, 4] are [0, 3]: count 2
    total {{3}}
```

Before processing `P[j]`, the histogram contains exactly `P[0]` through `P[j-1]`, including repeated prefixes with their multiplicities. The rearranged inequalities select precisely the starting indices that form legal slices ending at j. Inserting afterward restores the invariant. Every nonempty slice has one unique ending prefix, so it is counted once.

Notice that compression only ranks values; the arithmetic bounds are computed on the original prefix sums. Replacing these sums by their ranks before subtraction would not preserve numerical differences and would give incorrect windows.

## Code

```python
from bisect import bisect_left, bisect_right


def count_range_sum(nums, lower, upper):
    prefixes = [0]
    for value in nums:
        prefixes.append(prefixes[-1] + value)
    coords = sorted(set(prefixes))
    bit = [0] * (len(coords) + 1)

    def count_first(i):
        total = 0
        while i:
            total += bit[i]
            i -= i & -i
        return total

    answer = 0
    for current in prefixes:
        lo = bisect_left(coords, current - upper)
        hi = bisect_right(coords, current - lower)
        answer += count_first(hi) - count_first(lo)
        i = bisect_left(coords, current) + 1
        while i < len(bit):
            bit[i] += 1
            i += i & -i
    return answer
```

## Complexity

There are n+1 prefixes. Sorting them takes O(n log n), and each prefix performs a constant number of binary searches and Fenwick operations in O(log n). Total time is O(n log n), with O(n) space for prefixes, coordinates, and frequencies. Repeated prefix values are represented by a frequency, not multiple coordinates.

## Mistakes and edge cases

- Insert after querying, or a zero-length slice is counted whenever zero is in the allowed range.
- Use `bisect_left` for the lower bound and `bisect_right` for the upper bound so both endpoints are included.
- An all-zero input with bounds `[0, 0]` counts every nonempty slice.
- Do not assume that either search boundary occurs in `coords`.
- Return zero for an empty input; the one prefix is queried against an empty histogram.

## Variations

- Replace the Fenwick tree with merge-sort counting of qualifying prefix pairs.
- Count sums strictly between the bounds by changing both binary-search boundaries.
- Return counts per ending position rather than only the total.

=== card | 2407
time: 40 min

## The problem

Find the length of the longest subsequence whose values strictly increase and whose adjacent chosen values differ by at most `k`. A subsequence keeps input order but may skip elements. For `[1, 5, 3, 4]` with `k = 2`, one best choice is `[1, 3, 4]`, of length 3. The value 5 cannot directly follow 1 when the permitted jump is 2.

The jump restriction applies between consecutive selected values, not between their array indices. A single element is a valid subsequence on its own.

## Constraints and what they imply

The original values are positive and at most 100,000, with up to 100,000 entries. The implementation also accepts arbitrary signed integers by compressing values. `k` is nonnegative. A position-based dynamic program with a scan of all previous positions costs quadratic time, while the legal previous values form a contiguous interval on the value axis.

Equal values are not a valid strictly increasing transition. An ordinary longest-increasing-subsequence tails array does not directly enforce the maximum allowed value gap, because the best predecessor may be neither the smallest tail nor the globally longest tail.

## Brute force

For each position i, examine each earlier position j. If `nums[j] < nums[i]` and the difference is at most k, extend the best subsequence ending at j. Taking the maximum over such predecessors produces the answer in O(n²) time and O(n) space. This dynamic program is a useful independent checker on short sequences.

Enumerating every subsequence explicitly also works but takes exponential time. The quadratic formulation reveals the useful state without needing that much work.

## The insight

Maintain the best length of any already processed subsequence ending at each value. When a new value v arrives, eligible ending values lie in `[v-k, v)`. A segment tree can query the maximum over that interval and update the leaf for v. Compression preserves order and binary search locates the interval even when `v-k` is absent.

The query happens before the update, preserving original input order. Multiple occurrences of the same value share a leaf; keep the larger length already stored rather than blindly assuming a replacement is always safe.

## Optimal solution, traced

```steps
Values [1, 5, 3, 4], k = 2; initial best lengths are zero
---
Process 1 -> length 1; process 5 -> length 1
    process 3: eligible [1, 3), best is 1, so length 2
---
Process 4: eligible [2, 4), best at 3 is 2
    length 3, global answer {{3}}
```

By induction, each leaf holds the best length among processed subsequences ending with its value. Every valid subsequence ending at v is either the singleton v or extends a previous valid subsequence whose ending value is inside the queried interval. Conversely, extending any stored optimum in that interval remains valid. Taking the maximum and updating v therefore preserves the invariant and finds the optimum.

The root's aggregate is not sufficient by itself: it might describe a subsequence ending too far below v or at a value not strictly smaller than v. The bounded query filters both cases.

## Code

```python
from bisect import bisect_left


def constrained_lis(nums, k):
    coords = sorted(set(nums))
    size = 1
    while size < len(coords):
        size *= 2
    tree = [0] * (2 * size)
    answer = 0
    for value in nums:
        left = size + bisect_left(coords, value - k)
        right = size + bisect_left(coords, value)
        best = 0
        while left < right:
            if left & 1:
                best = max(best, tree[left])
                left += 1
            if right & 1:
                right -= 1
                best = max(best, tree[right])
            left //= 2
            right //= 2
        length = best + 1
        i = size + bisect_left(coords, value)
        tree[i] = max(tree[i], length)
        i //= 2
        while i:
            tree[i] = max(tree[2 * i], tree[2 * i + 1])
            i //= 2
        answer = max(answer, length)
    return answer
```

## Complexity

Sorting the distinct values takes O(n log n). Each of n elements performs binary searches, a range maximum query, and a point repair in O(log n). Overall time is O(n log n), and the coordinates and segment tree use O(n) space. The empty input returns zero. An uncompressed tree over a bounded universe M instead uses O(M) space and O(n log M + M) time.

## Mistakes and edge cases

- The right endpoint is exclusive: including v permits equal values to extend each other.
- The lower bound is inclusive, so a jump of exactly k is permitted.
- If `k = 0`, no distinct strictly smaller value is eligible, and any nonempty input returns 1.
- Do not process sorted values instead of original positions; that changes subsequence order.
- Zero is the identity for maximum because valid lengths are nonnegative.

## Variations

- Store predecessor indices with lengths to reconstruct an optimal subsequence.
- Count the number of maximum-length solutions, handling equal-length merges carefully.
- Use direct value indexing when the universe is small and fixed.

=== card | 699
time: 45 min

## The problem

Squares are dropped in order onto a horizontal surface. Each square is specified by its left coordinate and positive side length, and it falls vertically until its bottom meets the highest occupied point below its horizontal footprint. After every drop, report the greatest height reached anywhere so far. Horizontal footprints that merely touch at an endpoint do not overlap.

For `[(1, 2), (2, 3), (6, 1)]`, the first top is 2, the second lands on it and reaches 5, and the third lands on the ground. The reported maxima are `[2, 5, 5]`.

## Constraints and what they imply

There are at most 1,000 squares, but coordinates can be very large compared with that count. Allocating a cell for each unit coordinate is therefore a poor general strategy. The manageable n also permits an O(n²) scan, which is an excellent oracle for testing a more scalable tree.

Footprints are modeled as half-open intervals `[left, left + side)`. The horizontal right edge is excluded, making endpoint-only contact non-overlap. Heights and right endpoints should use a wide integer in a fixed-width language.

## Brute force

Keep the footprint and top height of every previous square. For each new square, inspect all earlier footprints that overlap it and take the largest top height, defaulting to zero. Add the new side length and record the result. There are O(n²) pair checks and O(n) stored squares. This works because the top of each previous square is constant across its footprint.

It would be wrong to sum the heights of all overlapping squares: only the highest contact point determines where the falling square stops.

## The insight

Compress all left and right boundaries. Each leaf represents the elementary interval between adjacent coordinates, not a single coordinate. For a new square, find the maximum height on all leaves under its footprint, add the side length, and assign that new top height to the entire footprint. Maintain a global maximum for the outputs.

A lazy segment tree supports both range maximum and range assignment. A node's pending assignment means its entire interval has that height, even if its children are stale. Push that assignment before partially descending. Since every new top is strictly above every previous height under the footprint, assignment accurately models the new exposed surface.

## Optimal solution, traced

```steps
Drop [1, 3): ground maximum 0, assign top height 2
---
Drop [2, 5): overlap with [1, 3) has height 2
    assign height 2 + 3 = 5; global maximum 5
---
Drop [6, 7): ground height 0, assign 1
    reported maxima {{[2, 5, 5]}}
```

Initially all elementary intervals have height zero. Inductively, the range query returns the highest existing surface below the new footprint, so its bottom and top are correct. Every point under that square now has the same new exposed top; points outside remain unchanged. The lazy assignment preserves these values while postponing work. Taking the running maximum yields the requested height after each drop.

## Code

```python
from bisect import bisect_left


def falling_squares(positions):
    if not positions:
        return []
    coords = sorted({edge for left, side in positions
                     for edge in (left, left + side)})
    n = len(coords) - 1
    maximum = [0] * (4 * n)
    lazy = [None] * (4 * n)

    def apply(node, value):
        maximum[node] = value
        lazy[node] = value

    def push(node):
        if lazy[node] is not None:
            apply(node * 2, lazy[node])
            apply(node * 2 + 1, lazy[node])
            lazy[node] = None

    def query(node, lo, hi, left, right):
        if left <= lo and hi <= right:
            return maximum[node]
        push(node)
        mid = (lo + hi) // 2
        result = 0
        if left < mid:
            result = max(result, query(node * 2, lo, mid, left, right))
        if mid < right:
            result = max(result, query(node * 2 + 1, mid, hi, left, right))
        return result

    def assign(node, lo, hi, left, right, value):
        if left <= lo and hi <= right:
            apply(node, value)
            return
        push(node)
        mid = (lo + hi) // 2
        if left < mid:
            assign(node * 2, lo, mid, left, right, value)
        if mid < right:
            assign(node * 2 + 1, mid, hi, left, right, value)
        maximum[node] = max(maximum[node * 2], maximum[node * 2 + 1])

    answer = []
    for left, side in positions:
        start = bisect_left(coords, left)
        end = bisect_left(coords, left + side)
        height = query(1, 0, n, start, end) + side
        assign(1, 0, n, start, end, height)
        answer.append(maximum[1])
    return answer
```

## Complexity

At most 2n distinct boundaries produce O(n) elementary intervals. Sorting costs O(n log n); each of n drops makes a range query and range assignment in O(log n), for O(n log n) total time. The tree, lazy tags, coordinates, and output take O(n) space. Recursion depth is O(log n).

## Mistakes and edge cases

- An endpoint touch is not overlap. Compress intervals between boundaries, not the boundaries as occupied points.
- This is assignment to the landing height, not addition of the side to each previous height.
- Push a pending tag before descending into a partially covered node.
- `None` distinguishes no pending assignment from a legitimate assigned height of zero.
- Repeated identical footprints stack; distant footprints preserve the earlier global maximum.

## Variations

- Use the quadratic overlap scan when the number of drops is small.
- Return each square's own top rather than the running maximum.
- Support online, unknown coordinates with an implicit segment tree over a bounded coordinate domain.

=== card | 2179
time: 40 min

## The problem

Two arrays are permutations of the same values. Count triples of distinct values that appear in the same relative order in both arrays. For `[0, 1, 2, 3]` and `[0, 2, 1, 3]`, the good triples are `(0, 1, 3)` and `(0, 2, 3)`, so the answer is 2.

The triple need not occupy adjacent positions. A different triple of values counts separately even when its positions are close to those of another triple.

## Constraints and what they imply

The arrays have the same length, up to 100,000, and each contains each value from 0 to n-1 once. This uniqueness lets a position map translate values without ambiguity. The result can be as large as `n choose 3`, so use a wide integer when implementing in a fixed-width language.

Brute force over triples is cubic, and even examining all pairs around every middle element is quadratic. Transforming the two orderings into one sequence allows a frequency structure to count the required choices efficiently.

## Brute force

Choose every triple of indices in the first array and look up their positions in the second. Count a triple if those three positions increase. With a precomputed position map, the check is constant time, but there are O(n³) triples. Alternatively, fix a middle index and directly scan both sides in O(n²).

The brute-force test must compare relative positions, not the numerical values of the original labels: relabeling the same permutation pair cannot change the answer.

## The insight

Map every value to its index in the second permutation. Replace each value in the first permutation by that index. A good triple is now exactly a strictly increasing triple in the transformed sequence. For each index i, multiply the number of smaller earlier transformed values by the number of larger later transformed values.

Maintain a Fenwick histogram of values already encountered. If the current transformed position is `p`, query how many inserted positions are below p. Because the transformed sequence is a permutation of `0..n-1`, exactly `n-1-p` positions are greater than p overall. Of the i earlier entries, `i - smaller_before` are greater, so subtract them to obtain `larger_after`.

## Optimal solution, traced

```steps
First [0, 1, 2, 3], second [0, 2, 1, 3]
    mapped sequence [0, 2, 1, 3]
---
At mapped value 2: smaller before = 1, larger after = 1, contribution 1
---
At mapped value 1: smaller before = 1, larger after = 1, contribution 1
    other contributions are 0, total {{2}}
```

At index i, the tree contains exactly the transformed values at indices less than i. Since all ranks are distinct, the prefix below p gives the smaller earlier count and all other earlier entries are greater. Subtracting those greater earlier entries from all values greater than p gives the greater later count. Multiplying pairs every legal left choice with every legal right choice. Each good triple has exactly one middle element, so the sum counts each once.

## Code

```python
def good_triplets(first, second):
    n = len(first)
    position = {value: i for i, value in enumerate(second)}
    bit = [0] * (n + 1)
    answer = 0
    for i, value in enumerate(first):
        p = position[value]
        cursor = p
        smaller_before = 0
        while cursor:
            smaller_before += bit[cursor]
            cursor -= cursor & -cursor
        larger_after = n - 1 - p - (i - smaller_before)
        answer += smaller_before * larger_after
        cursor = p + 1
        while cursor <= n:
            bit[cursor] += 1
            cursor += cursor & -cursor
    return answer
```

## Complexity

The map is constructed in O(n). Each of n iterations performs a prefix query and update in O(log n), giving O(n log n) time and O(n) space. Arrays shorter than three produce zero naturally. For identical permutations the result is `n choose 3`; for reversed permutations it is zero.

## Mistakes and edge cases

- Query before inserting the middle position. The current item belongs to neither side.
- The subtraction shortcut relies on unique ranks covering exactly `0..n-1`; it does not apply unchanged to duplicate values.
- Querying with `cursor = p` counts positions strictly below p because Fenwick indices are one-based.
- Neither input must be numerically sorted. Only their relative orders matter.
- Do not count triples that are increasing in only one permutation.

## Variations

- Count agreement on pairs, which reduces to counting increasing pairs in the transformed sequence.
- Use a second right-side histogram if the transformed values are not a complete permutation.
- Count common increasing subsequences of a fixed longer length with dynamic-programming layers.

=== card | 850
time: 50 min

## The problem

Compute the area covered by the union of axis-aligned rectangles, returning the result modulo 1,000,000,007. Overlapping regions count only once. Each rectangle is `[x1, y1, x2, y2]` with positive width and height. For `[[0, 0, 2, 2], [1, 1, 3, 3]]`, the individual areas total 8, but the overlap has area 1, so the union area is 7.

Shared boundaries have zero area; it does not matter which rectangle owns such a boundary. The algorithm treats all intervals as half-open to make event bookkeeping precise.

## Constraints and what they imply

The original input has up to 200 rectangles, with coordinates as large as 10⁹. A grid indexed by every coordinate is infeasible, and multiplying coordinates can exceed 32-bit arithmetic. Python's unbounded integers avoid overflow; in other languages use a sufficiently wide type before applying the modulus.

The number of distinct rectangle edges is only O(n). Between adjacent x coordinates, the active set cannot change, and between adjacent y coordinates, coverage is uniform. Coordinate compression preserves the actual lengths of these intervals, not merely their ranks.

## Brute force

Collect and sort all distinct x and y edges. For each elementary cell between consecutive edges, check whether any rectangle covers it, then add its actual width times height if so. There are O(n²) cells and O(n) rectangle checks per cell, for O(n³) time and O(n) coordinate storage apart from input. This is straightforward for small instances and is useful for independent verification.

Simply summing rectangle areas double-counts overlaps, while subtracting pairwise intersections alone fails when three or more rectangles overlap.

## The insight

Sweep from left to right. At each rectangle's left edge add its vertical interval; at its right edge remove it. Between consecutive events, multiply the width by the total length currently covered on the y-axis. The difficult part is maintaining the union length, not the sum of active rectangle heights.

Build a segment tree over elementary y intervals. Each node stores a cover count for updates that fully span its interval, and its covered length. If the count is positive, the node's whole geometric length is covered. Otherwise a leaf has length zero, and an internal node's length is the sum of its children's lengths. Descendant information remains available underneath a fully covered node, so it reappears when the covering count returns to zero.

## Optimal solution, traced

```steps
Rectangles [0, 0, 2, 2] and [1, 1, 3, 3]
---
From x=0 to x=1, active y coverage is [0, 2): add 1*2 = 2
    from x=1 to x=2, union coverage is [0, 3): add 1*3 = 3
---
From x=2 to x=3, coverage is [1, 3): add 1*2 = 2
    total area {{7}}
```

Between event coordinates no rectangle starts or ends, so the active y union is constant and its length times the slab width is exactly that slab's covered area. The tree invariant gives this length at its root: a positive cover count covers the whole node; otherwise coverage comes only from its children. Each add has a matching removal over the identical compressed range, so these node counts remain valid. Slabs partition the union except for zero-area boundaries, proving the accumulated sum.

## Code

```python
from bisect import bisect_left


def rectangle_union_area(rectangles):
    if not rectangles:
        return 0
    mod = 1_000_000_007
    ys = sorted({y for x1, y1, x2, y2 in rectangles for y in (y1, y2)})
    events = []
    for x1, y1, x2, y2 in rectangles:
        start = bisect_left(ys, y1)
        end = bisect_left(ys, y2)
        events.append((x1, 1, start, end))
        events.append((x2, -1, start, end))
    events.sort()
    n = len(ys) - 1
    cover = [0] * (4 * n)
    length = [0] * (4 * n)

    def update(node, lo, hi, left, right, delta):
        if left <= lo and hi <= right:
            cover[node] += delta
        else:
            mid = (lo + hi) // 2
            if left < mid:
                update(node * 2, lo, mid, left, right, delta)
            if mid < right:
                update(node * 2 + 1, mid, hi, left, right, delta)
        if cover[node]:
            length[node] = ys[hi] - ys[lo]
        elif hi - lo == 1:
            length[node] = 0
        else:
            length[node] = length[node * 2] + length[node * 2 + 1]

    area = 0
    previous_x = events[0][0]
    for x, delta, left, right in events:
        area += (x - previous_x) * length[1]
        update(1, 0, n, left, right, delta)
        previous_x = x
    return area % mod
```

## Complexity

There are 2n events and at most 2n distinct y coordinates. Sorting costs O(n log n), and each event performs an O(log n) interval update, for O(n log n) total time. The event list, compressed coordinates, cover counts, and lengths use O(n) space. Recursive depth is O(log n). Events at the same x contribute zero width between them, so their internal ordering does not affect area.

## Mistakes and edge cases

- Use actual coordinate differences for length, not the number of compressed leaves.
- Accumulate the slab area before applying the event at its right boundary.
- A cover count is necessary: removing one of two overlapping rectangles must not uncover the other's portion.
- Do not discard child state when a parent becomes fully covered.
- Duplicate, nested, touching, and disjoint rectangles all work. The interface assumes strictly positive width and height.

## Variations

- Return exact area without the final modulus where integer capacity permits.
- Compute union perimeter by additionally tracking covered segments and changes across event boundaries.
- Sweep horizontally instead, swapping the x and y axes.
