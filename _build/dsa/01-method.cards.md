=== card | 1929
time: 15 min

## The problem

Given a list of integers, return a new list consisting of the original sequence followed by the same sequence again. For `[2, 5, 2]`, return `[2, 5, 2, 2, 5, 2]`. Position and repetition both matter.

## Constraints and what they imply

The original task supplies a nonempty integer array. This implementation also accepts an empty list. The result has exactly twice as many positions, so merely writing it requires linear time and space. The input must not be changed.

## Brute force

Start with an empty result and append each input element, then make a second pass appending each element again. This is already O(n) time and O(n) output space; optimizing here means simplifying the construction, not improving its asymptotic cost.

## The insight

List concatenation creates a fresh list and preserves the order of each operand. With `n = len(nums)`, its first `n` slots equal `nums` and its last `n` slots equal `nums` again. These two equalities cover every output position and prove the construction.

## Optimal solution, traced

```steps
Take the original sequence
    nums = [2, 5, 2], n = 3
---
Concatenate two copies
    result = [2, 5, 2, {{2, 5, 2}}]
```

The second copy starts at index three, not at index two.

## Code

```python
def concatenate(nums):
    return nums + nums
```

## Complexity

For n input elements, concatenation copies 2n references: O(n) time and O(n) space for the returned list. The original list is untouched; elements are not deep-copied.

## Mistakes and edge cases

- Adding the list to itself in place would unexpectedly mutate the input.
- An empty list produces an empty list; repeated values stay repeated.
- For mutable elements, the two positions refer to the same objects, not independent deep copies.

## Variations

- Repeat the sequence k times while accounting for the size of the output.
- Produce an iterator over two passes when materializing all output is unnecessary.

=== card | 1480
time: 15 min

## The problem

Return the inclusive running sums of an integer list: output position i contains the sum from position zero through i. For `[3, -1, 4]`, the result is `[3, 2, 6]`. Do not modify the input.

## Constraints and what they imply

Values may be positive, negative, or zero. The order cannot be rearranged, and every position needs an answer. We also define the natural empty-input result as an empty list. The output itself requires linear space.

## Brute force

For each position i, start a new total at zero and add every value from index zero through i. The totals are correct, but the same prefix is added repeatedly: the number of additions is 1 + 2 + ... + n, giving O(n²) time and O(n) output space.

## The insight

The next prefix differs from the preceding prefix by exactly one value. Maintain a total, add the current value, then append it. Before processing index i, the total is the sum of indices strictly before i; after the addition it is the requested inclusive prefix. This invariant starts at zero and establishes every output entry.

## Optimal solution, traced

```steps
Read the first value
    total = 3, output = [3]
---
Read -1 and then 4
    total = 6, output = [3, 2, {{6}}]
```

## Code

```python
def running_sum(nums):
    total = 0
    out = []
    for value in nums:
        total += value
        out.append(total)
    return out
```

## Complexity

The single scan uses O(n) time and O(n) output space, with O(1) additional working space, assuming constant-cost integer arithmetic. Python's arbitrary-size integers can make arithmetic depend on their bit length.

## Mistakes and edge cases

- Appending before adding computes exclusive rather than inclusive prefixes.
- Negative entries can decrease the total; prefix sums need not be sorted.
- The empty input returns `[]` without a special case.

## Variations

- Return exclusive prefixes by appending before each addition.
- Build a leading-zero prefix array to answer many range-sum queries.

=== card | 1512
time: 20 min

## The problem

Count pairs of distinct positions `(i, j)` with `i < j` whose values are equal. For `[4, 1, 4, 4]`, the three pairs are `(0, 2)`, `(0, 3)`, and `(2, 3)`. Equal values at different positions count separately.

## Constraints and what they imply

Input values are integers; their order is fixed for defining pairs, but a value can appear many times. Counting distinct values is insufficient because multiplicity changes the number of pairs. The implementation also handles an empty list.

## Brute force

Examine every pair with the first index less than the second and add one when the values agree. This checks n(n-1)/2 candidates, taking O(n²) time and O(1) working space. It is an excellent oracle for small inputs.

## The insight

When a value appears, it forms exactly one new pair with each earlier occurrence of that value. A frequency table records precisely that number. Add the previous frequency before incrementing it; each valid pair is counted exactly once, at its later index, and no unequal pair is counted.

## Optimal solution, traced

```steps
Read 4 and 1
    frequencies = {4: 1, 1: 1}, pairs = 0
---
Read the remaining two 4s
    add 1 then 2; pairs = {{3}}
```

## Code

```python
def count_equal_pairs(nums):
    seen = {}
    pairs = 0
    for value in nums:
        previous = seen.get(value, 0)
        pairs += previous
        seen[value] = previous + 1
    return pairs
```

## Complexity

Assuming expected constant-time dictionary operations, time is O(n) and auxiliary space is O(d), where d is the number of distinct values. Hashing worst cases can be slower; a bounded value range permits a fixed frequency array instead.

## Mistakes and edge cases

- Incrementing the frequency first counts each element paired with itself.
- Counting only adjacent equal values misses separated occurrences.
- Empty and single-element lists have zero pairs; four identical entries have six.

## Variations

- Compute each frequency c first and add `c * (c - 1) // 2`.
- Count pairs whose values sum to a target by looking up the complement.

=== card | 1365
time: 20 min

## The problem

For each value in an integer list, return how many list positions hold a strictly smaller value. For `[3, 1, 3, 0]`, return `[2, 1, 2, 0]`. Duplicate values receive the same answer and do not count each other.

## Constraints and what they imply

Each input value lies between 0 and 100 inclusive. The small fixed domain allows frequency counting regardless of input order. The returned list follows the original order; an empty input is also supported.

## Brute force

For each position, scan the whole list and count elements strictly below its value. This directly matches the definition but performs n scans of n elements: O(n²) time and O(n) space for the answers.

## The insight

First count each possible value. Sweep the domain in increasing order, recording the number seen before the current value, and only then add its frequency. Thus `smaller[v]` equals the number of occurrences with value less than v. Looking up this precomputed count for every original element produces the required list.

## Optimal solution, traced

```steps
Count values in [3, 1, 3, 0]
    frequency[0] = 1, frequency[1] = 1, frequency[3] = 2
---
Sweep values from zero upward
    smaller[0] = 0, smaller[1] = 1, smaller[3] = 2
---
Look up each original element
    output = [2, 1, 2, {{0}}]
```

## Code

```python
def count_smaller(nums):
    frequency = [0] * 101
    for value in nums:
        frequency[value] += 1
    smaller = [0] * 101
    total = 0
    for value in range(101):
        smaller[value] = total
        total += frequency[value]
    return [smaller[value] for value in nums]
```

## Complexity

Time is O(n + 101), including the output pass. Auxiliary space is O(101), excluding the O(n) returned list. More generally a domain of size U gives O(n + U) time and O(U) auxiliary space.

## Mistakes and edge cases

- Adding the current frequency before storing the count mistakenly includes equal values.
- Python negative indices are valid, so values outside the stated domain must not be supplied.
- Both endpoint values, 0 and 100, need slots.

## Variations

- Sort a copy and record the first index of each value for an unbounded domain.
- Change the order of the sweep operations to count values less than or equal to each value.

=== card | 1913
time: 20 min

## The problem

Choose four distinct positions in an array of positive integers to maximize the product of one pair minus the product of the other pair. For `[5, 1, 6, 2]`, the best value is `5 * 6 - 1 * 2 = 28`.

## Constraints and what they imply

There are at least four positions and all values are positive. Positivity makes product comparisons monotone in each factor. Distinct positions are required even when their values happen to be equal.

## Brute force

Try each ordered selection of four distinct positions and evaluate the difference. There are O(n⁴) such selections, using O(1) working space. This is useful for validating the optimized rule on small arrays.

## The insight

The product of any chosen positive pair is at most the product of the two largest entries; any other pair's product is at least the product of the two smallest. Because there are at least four positions, those extreme pairs can be chosen disjointly, including when values tie. Their difference therefore attains both bounds simultaneously. Maintain the two smallest and two largest values in one pass.

## Optimal solution, traced

```steps
Scan [5, 1, 6, 2]
    two smallest = [1, 2], two largest = [6, 5]
---
Combine the disjoint extreme pairs
    6 * 5 - 1 * 2 = {{28}}
```

## Code

```python
def max_product_difference(nums):
    low1 = low2 = float("inf")
    high1 = high2 = float("-inf")
    for value in nums:
        if value <= low1:
            low1, low2 = value, low1
        elif value < low2:
            low2 = value
        if value >= high1:
            high1, high2 = value, high1
        elif value > high2:
            high2 = value
    return high1 * high2 - low1 * low2
```

## Complexity

Scanning n entries takes O(n) time and keeps four extrema, so O(1) auxiliary space under a fixed-width arithmetic model. Python integer multiplication depends on operand bit length for very large numbers.

## Mistakes and edge cases

- Strict-only replacement of the first extreme can lose a duplicate needed as the second.
- The extreme-product argument does not automatically hold with negative values.
- Fewer than four positions violate the contract; equal values still occupy distinct positions.

## Variations

- Sort a copy and take the first and last two entries in O(n log n) time.
- Allow signed values and derive product bounds by considering both ends of a sorted array.

=== card | 169
time: 20 min

## The problem

A nonempty list has one value occurring strictly more than half the time. Return that value. For `[2, 1, 2, 3, 2]`, return `2`. The strict-majority guarantee is essential to the constant-space method.

## Constraints and what they imply

Values are integers and can occur in any order. There is exactly one strict majority, although other values may also repeat. A frequency table is simple, but the follow-up asks for constant auxiliary space.

## Brute force

For each candidate, count its occurrences with a full scan and return one exceeding half the length. This takes O(n²) time and O(1) working space. Alternatively, a hash table reduces expected time to O(n) at the cost of O(n) space.

## The insight

Cancel pairs of different values. Such a cancellation removes at most one majority occurrence and one other occurrence, so the majority remains more numerous than all other remaining values together. The counter summarizes uncancelled copies of a candidate: matching values increase it; a different value cancels one. At zero, a later value starts a fresh group. Since the majority survives all cancellations, the final candidate is the majority.

## Optimal solution, traced

```steps
Read 2, 1, 2
    candidate = 2, balance = 1
---
Read 3, then 2
    balance drops to 0; new candidate = {{2}}, balance = 1
```

## Code

```python
def majority_element(nums):
    candidate = None
    balance = 0
    for value in nums:
        if balance == 0:
            candidate = value
        balance += 1 if value == candidate else -1
    return candidate
```

## Complexity

One pass takes O(n) time and O(1) auxiliary space. The counter is not the final frequency; it is only a cancellation balance.

## Mistakes and edge cases

- Without the promised majority, the final candidate need not be a valid answer; verify it with a second pass.
- Do not return when the balance first reaches zero: more values remain.
- A one-element list returns its sole value.

## Variations

- Verify the candidate when a majority is not guaranteed.
- Track two candidates for values appearing more than one third of the time.
