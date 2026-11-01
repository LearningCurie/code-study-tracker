=== card | 1732
time: 15 min

## The problem

A journey starts at altitude zero. Each entry in a list gives the change in altitude for one successive segment. Return the greatest altitude reached at any point, including the starting point. For `[-3, 5, -1]`, the answer is 2.

## Constraints and what they imply

Changes can be negative, zero, or positive. The initial altitude counts even if every later altitude is negative. The input is normally nonempty; the implementation also returns zero for no segments.

## Brute force

For each stopping point, recompute its altitude by summing all changes from the start, then take the maximum along with zero. Summing overlapping prefixes independently costs O(n²) time and O(1) working space if the maximum is updated immediately.

## The insight

Each next altitude is the previous altitude plus the next change. Keep that running altitude and the largest value encountered so far. Initially both are zero. After processing a segment, the running value is its endpoint altitude and the maximum includes precisely the start and all endpoints processed so far, proving the result after the scan.

## Optimal solution, traced

```steps
Start at zero and take change -3
    altitude = -3, best = 0
---
Take changes 5 and -1
    altitudes = 2, 1; best = {{2}}
```

## Code

```python
def highest_altitude(gain):
    altitude = 0
    best = 0
    for change in gain:
        altitude += change
        best = max(best, altitude)
    return best
```

## Complexity

The loop performs constant work for each of n changes: O(n) time and O(1) auxiliary space under constant-cost arithmetic. Large Python integers can add bit-length-dependent arithmetic costs.

## Mistakes and edge cases

- Initializing the best to the first change omits altitude zero.
- The maximum change is not necessarily the maximum cumulative altitude.
- A journey with only downward changes returns zero.

## Variations

- Return the earliest index at which the highest altitude occurs.
- Track the lowest altitude as well as the highest during the same scan.

=== card | 2073
time: 20 min

## The problem

People in a queue each want a positive number of tickets. On a turn, the front person buys one ticket and, if still needing tickets, moves to the back. Each purchase takes one unit of time. Return the elapsed time when the person originally at index `k` finishes.

## Constraints and what they imply

Ticket counts are positive, and `k` is a valid original index. Only the target person's completion time is needed, not the queue at every moment. For `[2, 3, 2]` and `k = 1`, the answer is 7.

## Brute force

Simulate a queue of remaining counts and original indices, buying one ticket per step until k finishes. It uses O(n) space and O(T) time for T purchases before completion. T can be much larger than n when ticket counts are large.

## The insight

Let t be the target's ticket count. Before the target's last purchase, everyone originally at or before k has had up to t opportunities; everyone after k has had only t - 1. People leave as soon as their own demand is met. Thus their contributions are respectively `min(count, t)` and `min(count, t - 1)`. These counts partition all purchases through the finishing turn.

## Optimal solution, traced

```steps
Target index 1 needs 3 tickets
    indices 0 and 1 contribute min(2, 3) + min(3, 3) = 5
---
Index 2 is after the target
    it contributes min(2, 2) = 2; total = {{7}}
```

## Code

```python
def ticket_time(tickets, k):
    target = tickets[k]
    elapsed = 0
    for i, count in enumerate(tickets):
        limit = target if i <= k else target - 1
        elapsed += min(count, limit)
    return elapsed
```

## Complexity

The scan takes O(n) time and O(1) auxiliary space. It does not depend on the sum of ticket counts, apart from the bit cost of arithmetic on arbitrarily large integers.

## Mistakes and edge cases

- A person after k does not get a turn in the target's final round.
- People with fewer tickets depart early, so use a minimum.
- When the target needs one ticket, later people contribute zero.

## Variations

- Return the completion time for every person, using an appropriate offline counting strategy.
- Simulate the queue when the actual order of purchases is required.

=== card | 2215
time: 20 min

## The problem

Given two integer lists, return two collections: distinct values appearing only in the first list, and distinct values appearing only in the second. For `[1, 1, 2]` and `[2, 3]`, the collections are `[1]` and `[3]`. Order within each collection is immaterial.

## Constraints and what they imply

Duplicates in an input do not create duplicate output entries. The two inputs can have different lengths and may be empty. Integer values are hashable, allowing set membership and set difference.

## Brute force

For each value in the first list, scan the second list and append it only if absent there and not already recorded; repeat in the opposite direction. Linear membership checks and duplicate checks can take O((n + m)²) time, with O(n + m) space for the result.

## The insight

A set removes duplicates while preserving membership information. The set difference `a - b` contains precisely values present in a and absent from b; reversing the operands gives the other collection. Converting the differences to lists satisfies the return shape without imposing an order.

## Optimal solution, traced

```steps
Create sets for [1, 1, 2] and [2, 3]
    first = {1, 2}, second = {2, 3}
---
Subtract in both directions
    first - second = {1}; second - first = {{3}}
```

## Code

```python
def distinct_differences(first, second):
    a = set(first)
    b = set(second)
    return [list(a - b), list(b - a)]
```

## Complexity

Building sets and computing both differences takes O(n + m) expected time and O(n + m) space, including the output, assuming expected constant-time hashing. Adversarial collisions can worsen the running time.

## Mistakes and edge cases

- A list membership test inside a loop can silently introduce quadratic work.
- Returning every occurrence instead of distinct values violates the contract.
- Set iteration order is not a promised output order; compare answers as sets.

## Variations

- Sort each result if a deterministic ascending order is required.
- Find the values common to both inputs with set intersection.

=== card | 557
time: 20 min

## The problem

Reverse the characters inside each word while keeping the words in their original order and preserving spaces. For `"ab cd e"`, return `"ba dc e"`. A space is the separator; the method below also preserves repeated or edge spaces.

## Constraints and what they imply

Strings are immutable in Python, so individual character assignments are unavailable. Using the literal single-space separator rather than the default whitespace split preserves the number and positions of spaces. Empty input is also handled.

## Brute force

Scan each word backwards and repeatedly concatenate individual characters to a result string. This is straightforward, but immutable concatenation can repeatedly copy an expanding prefix, giving O(n²) time in a general cost model. It also needs O(n) space for the output.

## The insight

Splitting on `" "` produces every word and an empty piece for each extra separator. Reverse each piece using a slice, then join with the same separator. Each non-space character remains in its original word and appears in reverse order, while joining restores exactly the separators between pieces.

## Optimal solution, traced

```steps
Split "ab  cd" on single spaces
    pieces = ["ab", "", "cd"]
---
Reverse each piece and join
    ["ba", "", "dc"] becomes {{"ba  dc"}}
```

## Code

```python
def reverse_words(text):
    return " ".join(piece[::-1] for piece in text.split(" "))
```

## Complexity

Splitting, slicing, and joining copy O(n) characters in total, so time and space are O(n), including the output and intermediate pieces. This does not rely on implementation-specific optimizations for repeated string concatenation.

## Mistakes and edge cases

- `split()` without an explicit separator collapses whitespace and loses edge spaces.
- Reversing the entire string also reverses word order.
- Python slices reverse Unicode code points, not necessarily user-perceived grapheme clusters.

## Variations

- Reverse word order instead of characters within each word.
- Use a grapheme-aware library if visual characters rather than code points must be reversed.

=== card | 119
time: 20 min

## The problem

Return row `k` of the triangle whose first row is `[1]` and whose later rows have boundary values 1 and interior values equal to the sum of the two neighboring entries above. Rows are numbered from zero: row 3 is `[1, 3, 3, 1]`.

## Constraints and what they imply

The index k is nonnegative. Only one row is requested, so retaining every earlier row is unnecessary. The answer has k + 1 integers; integer values may grow large.

## Brute force

Build and retain every row from zero through k, deriving each new row from the preceding one. The rows contain a total of O(k²) entries, so this takes O(k²) time and O(k²) space, including all retained rows.

## The insight

Keep one row and append the new right boundary. Update interior positions from right to left: at position j, both `row[j]` and `row[j - 1]` still contain values from the previous row. Their sum is the required new interior value. The left boundary remains 1, so induction gives the correct row after each iteration.

## Optimal solution, traced

```steps
Start with row 0 and build row 1
    [1] -> [1, 1]
---
Build rows 2 and 3, updating from the right
    [1, 2, 1] -> [1, 3, 3, {{1}}]
```

## Code

```python
def pascal_row(k):
    row = [1]
    for length in range(1, k + 1):
        row.append(1)
        for j in range(length - 1, 0, -1):
            row[j] += row[j - 1]
    return row
```

## Complexity

There are O(k²) additions and O(k) space for the returned row, with O(1) additional variables. This counts additions as constant cost; Python's large-integer arithmetic grows with coefficient bit length.

## Mistakes and edge cases

- Updating left to right reuses a value already changed for the new row.
- Row zero is `[1]`, not an empty row.
- Do not overwrite either boundary with an interior sum.

## Variations

- Build every row if the complete triangle is needed.
- Derive successive binomial coefficients using exact multiplication and division.

=== card | 1656
time: 25 min

## The problem

Design a stream with positions 1 through n. Values arrive once each, in arbitrary position order. After inserting a value, return the longest consecutive run of already-arrived values starting at the next position not yet returned. Advance that next position past the run.

## Constraints and what they imply

Each position is valid and inserted exactly once; values are strings. An insert can release several previously stored values or none. `None` is reserved internally as an unfilled marker, so even an empty string works as a value.

## Brute force

Store arrivals in a dictionary. On each insertion, search all stored positions for the next releasable one and continue until finding a gap. Repeated full searches can cost O(n²) over all insertions and require O(n) space.

## The insight

An array indexes directly by position, and a pointer identifies the first value not yet emitted. After storing an arrival, walk forward while the pointer's slot is filled. Every emitted slot is consecutive and begins at the pointer; stopping at the first missing slot prevents skipping. The pointer never retreats, so across all calls it advances at most n times.

## Optimal solution, traced

```steps
Insert position 2 before position 1
    slots = [empty, "b"]; next = 1; output = []
---
Insert position 1
    emit "a", then "b"; next = 3; output = {{"a", "b"}}
```

## Code

```python
class OrderedStream:
    def __init__(self, n):
        self.slots = [None] * (n + 1)
        self.next = 1

    def insert(self, position, value):
        self.slots[position] = value
        chunk = []
        while self.next < len(self.slots) and self.slots[self.next] is not None:
            chunk.append(self.slots[self.next])
            self.next += 1
        return chunk
```

## Complexity

Initialization takes O(n) time and space. One insert can take O(n) time when it releases a large chunk, but all n inserts together take O(n), or O(1) amortized per insert, counting returned entries. A chunk uses space proportional to its length.

## Mistakes and edge cases

- Checking truthiness would incorrectly treat an empty string as unfilled.
- Do not move past a missing position, even if later positions are present.
- Duplicate or out-of-range inserts are outside this contract.

## Variations

- Support repeated updates by defining whether previously emitted values can be revised.
- Use a sparse map if the possible position range is huge relative to arrivals.

=== card | 1351
time: 20 min

## The problem

Count negative entries in a rectangular matrix whose rows and columns are each sorted in non-increasing order. For `[[3, 0, -2], [1, -1, -3]]`, return 3. Zero is not negative.

## Constraints and what they imply

The row and column monotonicity both matter: moving right or down cannot increase a value. The usual input is nonempty and rectangular; this implementation also accepts an empty matrix or rows of length zero.

## Brute force

Visit every cell and increment a counter when the value is below zero. This takes O(mn) time and O(1) working space for m rows and n columns. It is an independent way to check small examples.

## The insight

Start at the bottom-left. If the current cell is negative, all cells to its right in the same row are also negative; count them and move up, leaving the counted row. Otherwise this cell and all cells above it in the same column are nonnegative, so move right and discard that column. Each move eliminates an unprocessed row or column, and the two cases count every negative exactly once.

## Optimal solution, traced

```steps
Start at bottom-left, value 1
    it is nonnegative; move right to -1
---
Count the bottom row suffix, then inspect the upper row
    add 2, move up; 0 is nonnegative, move right
---
Count the upper suffix
    add 1; total = {{3}}
```

## Code

```python
def count_negatives(grid):
    if not grid or not grid[0]:
        return 0
    row = len(grid) - 1
    col = 0
    count = 0
    width = len(grid[0])
    while row >= 0 and col < width:
        if grid[row][col] < 0:
            count += width - col
            row -= 1
        else:
            col += 1
    return count
```

## Complexity

At most m upward and n rightward moves occur, so time is O(m + n) and auxiliary space is O(1). The empty checks are constant time.

## Mistakes and edge cases

- Treating zero as negative overcounts.
- Row sorting alone does not justify discarding the column above a nonnegative cell.
- Counting only the current negative cell misses its entire rightward suffix.

## Variations

- Binary-search the first negative in each row in O(m log n) time.
- Count entries below a different threshold by changing the comparison.

=== card | 1588
time: 20 min

## The problem

Sum the sums of all contiguous odd-length subarrays of an integer list. For `[1, 2, 3]`, the odd-length subarrays are the three singletons and the whole list, giving `1 + 2 + 3 + 6 = 12`.

## Constraints and what they imply

Every eligible subarray contributes its elements, including overlapping occurrences. A direct enumeration considers quadratically many ranges. The contribution argument works for negative or zero integers too, and an empty input produces zero.

## Brute force

Enumerate each start and end, and for odd lengths explicitly sum the selected slice. There are O(n²) ranges and each sum can take O(n), for O(n³) time and O(1) working space if sums are computed by loops without slicing.

## The insight

For index i, there are `i + 1` choices of left endpoint and `n - i` choices of right endpoint. The length is odd exactly when the number of positions chosen on each side has matching parity. Among the product of those choices, exactly `(product + 1) // 2` pairs have matching parity: each side alternates parity and starts with an even distance. Multiply that count by the value and sum over indices; swapping the summation order preserves the total.

## Optimal solution, traced

```steps
For [1, 2, 3], count odd ranges containing each index
    products = [3, 4, 3]; odd counts = [2, 2, 2]
---
Add the contributions
    1*2 + 2*2 + 3*2 = {{12}}
```

## Code

```python
def odd_subarray_sum(nums):
    n = len(nums)
    total = 0
    for i, value in enumerate(nums):
        choices = (i + 1) * (n - i)
        total += value * ((choices + 1) // 2)
    return total
```

## Complexity

One pass takes O(n) time and O(1) auxiliary space under constant-cost integer arithmetic. Python's unbounded integer operations can cost more as values grow.

## Mistakes and edge cases

- Count position occurrences, not distinct values.
- Use integer division after adding one; ordinary division yields a float.
- Counting all containing subarrays without restricting parity overcounts.

## Variations

- Count contributions from even-length ranges instead.
- Use prefix sums to enumerate all odd ranges in O(n²) time as a second oracle.

=== card | 1381
time: 30 min

## The problem

Implement a bounded stack with three operations: push a value if there is room, pop and return the top value or `-1` if empty, and add an increment to each of the bottom `k` current elements. A push to a full stack is ignored. For example, pushing 2 and 5, incrementing the bottom two by 3, then popping yields 8 followed by 5.

## Constraints and what they imply

The capacity and k are nonnegative integers. Increment values and stored values are integers; increments can be negative. If k exceeds the current size, every existing element is incremented. The operation must affect elements present at that moment, not values pushed later. The empty-stack sentinel is `-1`, even though a valid stored value might also equal `-1`.

## Brute force

Represent the stack with a list. A push or pop is constant time amortized for Python's list, while increment loops over the first `min(k, size)` elements. This uses O(capacity) space and can take O(capacity) time for a single increment. Repeating large increments before any pops repeats work unnecessarily.

## The insight

Record a deferred increment at the highest affected index instead of updating every element. Interpret `pending[j]` as an increment owed to all currently present positions from zero through j. The value owed to a particular position is the sum of pending entries at that position and above. On pop, the top receives its pending increment; propagate that amount one position down so the remaining affected positions still receive it. A new push starts with zero pending, so it cannot inherit increments issued before it existed. Each operation preserves this representation and does constant work.

## Optimal solution, traced

```steps
Push 2 and 5, then increment bottom 2 by 3
    values = [2, 5], pending = [0, 3]
---
Pop the top and propagate its pending amount
    return 8; values = [2], pending = [3]
---
Pop again
    return {{5}}; stack is empty
```

## Code

```python
class CustomStack:
    def __init__(self, max_size):
        self.max_size = max_size
        self.values = []
        self.pending = []

    def push(self, value):
        if len(self.values) < self.max_size:
            self.values.append(value)
            self.pending.append(0)

    def pop(self):
        if not self.values:
            return -1
        extra = self.pending.pop()
        value = self.values.pop()
        if self.pending:
            self.pending[-1] += extra
        return value + extra

    def increment(self, k, value):
        count = min(k, len(self.values))
        if count:
            self.pending[count - 1] += value
```

## Complexity

Each operation performs O(1) work, with O(capacity) maximum space. Python list append and pop at the end are amortized O(1), so the push/pop bound in this implementation is amortized, not a strict worst-case guarantee; increment is O(1) worst-case under constant-cost arithmetic. A fixed-size array and explicit size would avoid resizing.

## Mistakes and edge cases

- Updating the top pending entry rather than the last affected entry changes too many values when k is small.
- Failing to propagate on pop loses an increment owed to lower elements.
- Incrementing an empty stack or using k = 0 does nothing; a later push must not receive that old increment.
- Negative k is outside the stated contract, and `-1` alone cannot distinguish an empty pop from a stored `-1`.

## Variations

- Use preallocated arrays to make push and pop worst-case constant time under the fixed-width model.
- Design a structure supporting increments on arbitrary intervals rather than prefixes.
