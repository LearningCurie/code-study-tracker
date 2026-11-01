=== card | 136
time: 20 min

## The problem

Every integer in an array occurs exactly twice except for one integer that occurs once. Find that single integer using constant auxiliary space. For `[7, 2, 7]`, the answer is 2.

## Constraints and what they imply

The input contains exactly one unpaired value, but its position is arbitrary. A dictionary of frequencies would find it, at the cost of space proportional to the number of distinct values. The pairing property permits a constant-space cancellation.

## Brute force

For each value, scan the array and count its occurrences until finding the one with count one. This takes O(n²) time and O(1) extra space. The bottleneck is recounting the whole array for every candidate.

## The insight

XOR every value into an accumulator starting at zero. XOR is associative and commutative, each value XOR itself is zero, and XOR with zero leaves a value unchanged. Every pair cancels regardless of order, leaving the unpaired value.

## Optimal solution, traced

```steps
Start with accumulator 0; read 7
    0 XOR 7 = 7
---
Read 2, then the second 7
    7 XOR 2 XOR 7 = {{2}}
```

Reordering is only a proof device; the implementation scans in the input order.

## Code

```python
def single_number(nums):
    answer = 0
    for value in nums:
        answer ^= value
    return answer
```

## Complexity

The scan takes O(n) time and O(1) auxiliary space under the usual fixed-width integer cost model. Python integers can be arbitrarily large, so XOR on very large integers also depends on their bit length.

## Mistakes and edge cases

- The cancellation relies on every other value occurring an even number of times.
- Do not assume duplicates are adjacent.
- A one-element input returns that element.

## Variations

- Find two unpaired values by partitioning on a bit where they differ.
- Find one value appearing once when all others appear three times.
- Use XOR to check whether two sequences have the same elements with matching parity of multiplicity.

=== card | 338
time: 20 min

## The problem

For every integer from 0 through `n`, return how many bits in its binary representation are 1. For `n = 4`, the result is `[0, 1, 1, 2, 1]`.

## Constraints and what they imply

`n` is non-negative, and the result itself has `n + 1` entries. Any algorithm must spend O(n) time writing that output. Counting the bits of every number independently repeats work.

## Brute force

For each integer, shift it right one bit at a time and count the low bits that are set. A number up to `n` may have O(log n) bits, so doing this for every value takes O(n log n) time and O(n) output space.

## The insight

Shifting `i` right removes its lowest bit. The count for `i` is therefore the already-computed count for `i // 2`, plus `i & 1`. Since `i // 2 < i` for positive `i`, filling the table from left to right makes the dependency available.

## Optimal solution, traced

```steps
Start with count[0] = 0
    count[1] = count[0] + 1 = 1
---
For 2 (binary 10), shift to 1 and add low bit 0
    count[2] = 1
---
For 3 (binary 11), shift to 1 and add low bit 1
    count[3] = {{2}}
```

The recurrence accounts for every bit exactly once: the shifted number contains all bits except the removed low bit.

## Code

```python
def count_bits(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    counts = [0] * (n + 1)
    for i in range(1, n + 1):
        counts[i] = counts[i >> 1] + (i & 1)
    return counts
```

## Complexity

Each output entry takes O(1) work, so time is O(n) and output space is O(n). Apart from the returned array, the algorithm uses O(1) auxiliary space.

## Mistakes and edge cases

- Include the count for zero.
- Use the low bit, `i & 1`, rather than the whole number.
- An input of zero returns `[0]`.

## Variations

- Use `counts[i & (i - 1)] + 1`, removing the lowest set bit instead.
- Count the set bits of one integer by repeatedly clearing its lowest set bit.
- Compare against Python's `int.bit_count()` for small inputs.

=== card | 1071
time: 20 min

## The problem

Find the longest nonempty string that can be repeated to form each of two given nonempty strings. If none exists, return the empty string. For `"ABABAB"` and `"ABAB"`, the answer is `"AB"`.

## Constraints and what they imply

Both strings must be exact repetitions of the same unit, not merely share a prefix. A valid unit's length divides both string lengths, so it cannot be longer than their greatest common divisor.

## Brute force

Try each nonempty prefix of the shorter string, from longest to shortest. For each candidate, repeat it enough times to compare with both strings. In the worst case this repeatedly constructs and checks O(m + n) characters for O(min(m, n)) candidates, giving O((m + n) min(m, n)) time.

## The insight

If both strings are repetitions of one unit, concatenating them in either order gives the same string. Conversely, two nonempty strings that commute under concatenation are powers of a common shorter string. Once the concatenations match, the prefix whose length is `gcd(len(first), len(second))` is their longest shared repeating unit.

## Optimal solution, traced

```steps
first = ABABAB, second = ABAB
    both concatenation orders produce ABABABABAB
---
The greatest common divisor of lengths 6 and 4 is 2
    return the length-2 prefix {{AB}}
```

Every common unit length divides both lengths. The common-word property ensures the prefix at the greatest common divisor length repeats to form both strings, so no longer valid unit exists.

## Code

```python
from math import gcd


def gcd_of_strings(first, second):
    if not first or not second:
        raise ValueError("both strings must be nonempty")
    if first + second != second + first:
        return ""
    return first[:gcd(len(first), len(second))]
```

## Complexity

Concatenation and comparison take O(m + n) time and O(m + n) temporary space. Euclid's algorithm takes O(log min(m, n)) arithmetic steps, dominated by the string work.

## Mistakes and edge cases

- Matching prefixes alone are not enough: `"ABAB"` and `"ABA"` have no common repeating unit.
- Check the concatenations before returning the gcd-length prefix.
- The task's input strings are nonempty.

## Variations

- Test every candidate prefix as a brute-force oracle.
- Find the shortest repeating unit of one string.
- Compare strings without constructing concatenations by indexing cyclically.

=== card | 371
time: 30 min

## The problem

Add two integers without using the arithmetic addition or subtraction operators. Return their sum. For 5 and 3, the answer is 8.

## Constraints and what they imply

The original inputs fit comfortably in a signed 32-bit result. Python integers have unbounded sign extension for negative values, so a naive carry loop can continue indefinitely. This implementation deliberately works in a 32-bit two's-complement representation and converts the final bit pattern back to a Python signed integer.

## Brute force

A manual bit-by-bit adder can inspect each bit and carry, building the result one position at a time. This takes O(32) steps for fixed-width integers. Repeatedly incrementing one operand while decrementing the other would depend on the numeric magnitude and does not satisfy the operator restriction.

## The insight

For each bit, XOR gives the sum without carrying, and AND identifies positions that generate a carry. Shift those carries left one position, then repeat with the partial sum and carries. Mask to 32 bits each round so bits beyond the signed representation are discarded.

When the carry becomes zero, all bit positions have been resolved. If the sign bit is set, invert the lower 32-bit complement to obtain the equivalent negative Python integer without using addition or subtraction.

## Optimal solution, traced

```steps
5 = 0101, 3 = 0011
    XOR = 0110; carry = (0001 << 1) = 0010
---
0110 XOR 0010 = 0100; carry = 0100
---
0100 XOR 0100 = 0000; carry = 1000
---
0000 XOR 1000 = {{1000}}; carry = 0
```

Each carry moves at least one position left on the next iteration. Under the fixed 32-bit mask, a carry eventually leaves the representation, so the loop terminates.

For the all-ones 32-bit pattern, `a ^ mask` is zero and its bitwise complement is `-1`, the corresponding signed value. The same conversion works for every pattern with the sign bit set. It uses neither the addition nor subtraction operator.

## Code

```python
def bitwise_sum(a, b):
    mask = 0xFFFFFFFF
    a &= mask
    b &= mask
    while b:
        a, b = (a ^ b) & mask, ((a & b) << 1) & mask
    return a if a <= 0x7FFFFFFF else ~(a ^ mask)
```

## Complexity

For 32-bit operands there are at most 32 carry rounds, so time and space are O(1) for the fixed-width model. The same idea on a width of `w` bits takes O(w) rounds and O(1) fixed-width words.

## Mistakes and edge cases

- Mask intermediate values in Python; otherwise negative numbers retain infinitely many leading sign bits.
- Convert a final value with the sign bit set back to a negative signed integer.
- State the width: this version wraps outside the signed 32-bit range.

## Variations

- Implement a fixed-width subtraction using two's-complement negation.
- Add arbitrary-width non-negative integers using the same carry idea.
- Compare the loop with a full adder applied to each bit.

=== card | 260
time: 30 min

## The problem

Exactly two distinct integers occur once, and every other integer occurs twice. Return the two single values in either order using constant auxiliary space. For `[1, 2, 1, 3]`, the answers are 2 and 3.

## Constraints and what they imply

The two unpaired values are distinct, so their XOR is nonzero. Duplicate pairs may appear anywhere in the input. A frequency table is simple but uses space proportional to the number of distinct values.

## Brute force

For each candidate, count its occurrences by scanning the array. This takes O(n²) time and O(1) extra space. The repeated whole-array scans are the bottleneck.

## The insight

XOR all values: paired values cancel, leaving `a XOR b` for the two singles. Any set bit in this XOR is a position where `a` and `b` differ. Partition every input value by that bit and XOR within each group. Each duplicate pair goes into the same group and cancels, while the two single values land in different groups.

The expression `different & -different` isolates the lowest set bit. The proof needs only one differing bit, not a particular one.

## Optimal solution, traced

```steps
XOR [1, 2, 1, 3]
    paired 1s cancel; 2 XOR 3 = 1
---
Use the lowest set bit, 1
    group with bit clear XORs to {{2}}
    group with bit set XORs to {{3}}
```

The partition never separates the two copies of a duplicate, because they have identical bits. The two unpaired values are separated by the selected differing bit, so each group's remaining XOR is exactly one answer.

The XOR of the single values cannot be zero unless those values are equal, which the input rules exclude. Isolating its lowest set bit therefore always provides a usable partition. This remains valid for negative Python integers: their bitwise operations use a consistent two's-complement interpretation, and the isolated bit is shared by equal values. No additional storage is needed for either partition.

## Code

```python
def two_single_numbers(nums):
    different = 0
    for value in nums:
        different ^= value
    bit = different & -different
    first = second = 0
    for value in nums:
        if value & bit:
            first ^= value
        else:
            second ^= value
    return [first, second]
```

## Complexity

Two linear scans take O(n) time and O(1) auxiliary space for fixed-width integers. Python's arbitrary-size integer operations also depend on the bit lengths of the operands.

## Mistakes and edge cases

- Partition the original values, not the combined XOR alone.
- The input promise that the two singles differ makes the chosen bit nonzero.
- The result order is not specified.

## Variations

- Find one unpaired value when all others occur twice.
- Find a missing and a duplicated value in a known integer range using XOR partitions.
- Count occurrences explicitly as a small-input oracle.

=== card | 137
time: 30 min

## The problem

Every integer in an array appears exactly three times except one integer that appears once. Find the single integer using constant auxiliary space. The values are signed 32-bit integers.

For `[2, 2, 2, -3]`, the answer is -3.

## Constraints and what they imply

Simple XOR cancellation removes pairs, not triples: `x XOR x XOR x` is `x`, not zero. Negative numbers must be interpreted using their 32-bit two's-complement bit patterns. The single value may itself be negative.

## Brute force

For each value, scan the array and count its occurrences. The single value has count one. This takes O(n²) time and O(1) auxiliary space; repeated scans are the bottleneck. A frequency dictionary improves time but uses O(n) auxiliary space in the worst case.

## The insight

Treat each of the 32 bit positions independently. Every value appearing three times contributes either zero or three set bits at a position, so its contribution vanishes modulo 3. The remaining bit count modulo 3 is the corresponding bit of the single value. Assemble the 32 bits, then interpret a set sign bit as a negative signed value.

## Optimal solution, traced

```steps
Input [2, 2, 2, 3]
    bit 0 has one set bit; 1 modulo 3 = 1
---
Bit 1 has four set bits
    4 modulo 3 = 1
---
The remaining bit pattern is {{11}}, or 3
```

Each triplicate contributes a multiple of three independently at every bit. Removing those contributions leaves exactly the single value's 32-bit representation.

For a negative Python integer, right shift extends its sign bit. Masking with `& 1` still reads the requested bit of its low 32-bit representation. Once all 32 positions are assembled, subtracting `2^32` when the sign bit is set converts that unsigned pattern into its signed value. For example, all 32 bits set represent negative one.

## Code

```python
def single_number_thrice(nums):
    result = 0
    for bit in range(32):
        count = sum((value >> bit) & 1 for value in nums)
        if count % 3:
            result |= 1 << bit
    return result if result < (1 << 31) else result - (1 << 32)
```

## Complexity

The algorithm scans `n` values for each of 32 bit positions: O(32n) time, or O(n) with fixed width, and O(1) auxiliary space. The width is part of the argument: for arbitrary-size integers a different bound is needed.

## Mistakes and edge cases

- Interpret the sign bit after assembling the low 32 bits.
- Apply modulo 3 per bit, not to the integer sum.
- The input promise is essential; other multiplicities do not cancel in the same way.

## Variations

- Use two bit masks as a finite-state counter modulo 3.
- Find one value appearing once when all others occur `k` times by counting bits modulo `k`.
- Compare with a frequency table on random small signed inputs.

=== card | 2044
time: 30 min

## The problem

Count the nonempty subsets of an array whose bitwise OR is as large as the maximum OR achievable by any subset. Equal values at different indices represent different choices.

For `[1, 2, 3]`, the maximum OR is 3. Five nonempty subsets reach it: `[3]`, `[1, 2]`, `[1, 3]`, `[2, 3]`, and `[1, 2, 3]`.

## Constraints and what they imply

The array is short enough to enumerate its subsets. OR can only add set bits as elements are included, so the OR of the entire array is the maximum achievable value. The empty subset is not counted, even in a generalised input containing only zeros.

## Brute force

Enumerate each nonempty index subset and independently OR all selected values. There are `2^n - 1` subsets and up to `n` values to inspect per subset, for O(n 2^n) time. Recomputing a subset's OR from scratch is the repeated work.

## The insight

First compute the target OR of all elements. Then build subsets by a depth-first include-or-skip choice, carrying the OR accumulated so far. At a leaf, count it only if at least one element was selected and its OR equals the target. Each recursive edge updates the accumulated OR once rather than rebuilding the subset.

## Optimal solution, traced

```steps
Array [1, 2, 3] has target OR {{3}}
---
Skip 1 and 2, include 3
    OR is 3; count one
---
Include 1 and 2, skip 3
    OR is 3; count one more
---
Continue the include-or-skip tree
    total {{5}} qualifying nonempty subsets
```

Every subset corresponds to exactly one path through the choice tree. The carried OR equals the OR of the chosen indices on that path, so the leaf test counts precisely the requested subsets.

For `[0, 0]`, a generalised input, all three nonempty subsets have the same maximum OR of zero. The `chosen` flag excludes only the empty path. A frequency-based approach must likewise distinguish choices by index rather than collapsing equal values.

## Code

```python
def count_max_or_subsets(nums):
    target = 0
    for value in nums:
        target |= value

    def count(i, current, chosen):
        if i == len(nums):
            return int(chosen and current == target)
        return count(i + 1, current, chosen) + count(i + 1, current | nums[i], True)

    return count(0, 0, False)
```

## Complexity

The choice tree has O(2^n) nodes, each doing O(1) fixed-width bit work. The recursion stack uses O(n) auxiliary space. This is appropriate for the task's small `n`, not for large arrays.

## Mistakes and edge cases

- Count nonempty subsets only.
- Different indices are different choices even when their values match.
- Do not assume a subset with a numerically smaller intermediate OR cannot later reach the target.

## Variations

- Store the OR for each bit mask using its lowest set bit.
- Count subsets reaching any supplied target OR.
- Stop exploring a branch early when every completion can be counted safely.

=== card | 204
time: 30 min

## The problem

Count the prime numbers strictly less than a non-negative integer `n`. A prime is an integer greater than one with no positive divisors other than one and itself. For `n = 10`, the answer is 4: 2, 3, 5 and 7.

## Constraints and what they imply

The upper bound can be large enough that testing every candidate separately repeats many divisibility checks. The upper endpoint itself is excluded. Zero and one are never prime.

## Brute force

For each integer below `n`, test divisors from 2 through its square root. A straightforward upper bound is O(n sqrt(n)) time, with O(1) auxiliary space. Testing the same small divisors against many candidates is the bottleneck.

## The insight

Use the sieve of Eratosthenes. Initially mark every number below `n` as potentially prime, then mark zero and one as non-prime. For each still-marked `p` up to `sqrt(n - 1)`, mark its multiples starting at `p*p` as composite. Smaller multiples of `p` already have a smaller prime factor and were marked earlier.

## Optimal solution, traced

```steps
Numbers below 10 start as candidates except 0 and 1
    candidates 2 3 4 5 6 7 8 9
---
For p=2, mark 4, 6 and 8
---
For p=3, mark 9
    remaining {{2, 3, 5, 7}}; count 4
```

Every marked number has a nontrivial divisor and is composite. Every composite below `n` has a prime factor at most its square root, so it will be marked when that factor is processed.

For example, the multiple `3 * 4 = 12` is already marked when processing 2, so the 3-stride can start at `3 * 3 = 9`. Once `p*p` is at least `n`, no remaining unmarked composite can first be discovered by `p`: its smaller factor would already have been processed. The byte-array slice updates exactly the multiples within the exclusive upper bound.

The temporary zero-filled slice has the same number of entries as the positions being marked, as Python's extended slice assignment requires.

## Code

```python
from math import isqrt


def count_primes(n):
    if n < 2:
        return 0
    prime = bytearray(b"\x01") * n
    prime[0:2] = b"\x00\x00"
    for p in range(2, isqrt(n - 1) + 1):
        if prime[p]:
            start = p * p
            count = (n - 1 - start) // p + 1
            prime[start:n:p] = b"\x00" * count
    return sum(prime)
```

## Complexity

The sieve takes O(n log log n) time by the standard harmonic bound over prime multiples and O(n) space for the byte array and temporary slice data. Counting the remaining entries is O(n).

## Mistakes and edge cases

- Count primes strictly below `n`, not through `n`.
- Start crossing off at `p*p`; starting at `p` would erase the prime itself.
- Inputs below 2 return zero.

## Variations

- Return the primes instead of only their count.
- Use a segmented sieve when the full range does not fit in memory.
- Compare results with trial division on small bounds.

=== card | 50
time: 30 min

## The problem

Compute a floating-point base raised to an integer exponent. For example, `2^10` is 1024 and `2^-3` is 0.125.

## Constraints and what they imply

The exponent can be large and can be negative, so multiplying the base once per exponent step is too slow. A zero base with a negative exponent is not a valid input because division by zero would be required. Floating-point results may have rounding error.

## Brute force

Multiply the base by itself `|n|` times, then take the reciprocal for a negative exponent. This uses O(|n|) multiplications and O(1) space. Its bottleneck is the number of repeated multiplications when the exponent is large.

## The insight

Read the bits of the non-negative exponent. Keep a current power of the base and a result. When the current low bit is one, multiply the result by that power. Square the current power and shift the exponent right on every iteration. For a negative exponent, first replace the base by its reciprocal and negate the exponent.

## Optimal solution, traced

```steps
Compute 2^10: result 1, base 2, exponent 10
    low bit 0; square base to 4, shift exponent to 5
---
Low bit 1
    result 4; square base to 16, exponent becomes 2
---
Low bit 0, then exponent 1 with base 256
    result 4 * 256 = {{1024}}
```

At each step, `result * base^remaining_exponent` equals the original requested power, apart from floating-point rounding. When the remaining exponent reaches zero, the result is the answer.

For a negative exponent such as -3, replacing the base 2 with 0.5 changes the remaining exponent to 3 while preserving the requested value. The low bit selects 0.5, squaring changes the base to 0.25, and the final low bit gives 0.125. An exponent of zero performs no loop iterations. Python's unbounded integer exponent also avoids the fixed-width negation overflow that other languages must handle explicitly.

Squaring and multiplying can still accumulate floating-point error, so the mathematical invariant is approximate in machine arithmetic. Underflow or overflow can also occur.

## Code

```python
def fast_power(x, exponent):
    if exponent < 0:
        x = 1.0 / x
        exponent = -exponent
    result = 1.0
    while exponent:
        if exponent & 1:
            result *= x
        x *= x
        exponent >>= 1
    return result
```

## Complexity

The exponent is halved each round, giving O(log(|n| + 1)) multiplications and O(1) auxiliary space. Python integers can represent the positive counterpart of the smallest signed 32-bit exponent; fixed-width languages should widen before negating it.

## Mistakes and edge cases

- Any valid base to exponent zero returns 1.
- Handle negative exponents before shifting.
- Compare floating-point test results with a tolerance rather than exact decimal equality.

## Variations

- Compute modular exponentiation with an integer modulus.
- Derive the same method recursively.
- Work with exact rational numbers when floating-point rounding is unacceptable.

=== card | 149
time: 45 min

## The problem

Given distinct points with integer coordinates, find the largest number lying on one straight line. For `(0, 0)`, `(1, 1)`, `(2, 2)` and `(0, 1)`, three points lie on the diagonal line.

## Constraints and what they imply

Coordinates are integers and input points are distinct. Lines can be vertical or horizontal. Floating-point slopes can round two distinct rational slopes to the same value or treat equal slopes inconsistently, so an exact direction representation is preferable.

## Brute force

For every pair of points, examine every point and test collinearity using a cross product. This takes O(n³) time and O(1) extra space apart from the input. Repeatedly testing all points for many pairs on the same line is the bottleneck.

## The insight

Fix an anchor point and group every other point by its direction from that anchor. Reduce `(dx, dy)` by `gcd(abs(dx), abs(dy))` and choose a canonical sign: make `dx` positive, or make `dy` positive when `dx` is zero. Opposite directions then use the same key because they describe the same line through the anchor.

The largest direction count plus one for the anchor is the largest line through that anchor. Repeat for each anchor and take the maximum. Processing only later points is enough: for any optimal line, its earliest input point sees all other points on that line.

## Optimal solution, traced

```steps
Anchor (0, 0); examine (1, 1), (2, 2), (0, 1)
    directions (1, 1), (2, 2), (0, 1)
---
Reduce by the coordinate gcd
    (2, 2) becomes (1, 1)
---
Direction (1, 1) occurs twice
    with the anchor, the line contains {{3 points}}
```

Two nonzero integer direction vectors through the same anchor describe the same line exactly when one is a nonzero scalar multiple of the other. Reducing by the gcd and choosing one sign gives the same primitive pair for those vectors and different pairs for different slopes. Vertical and horizontal lines need no special division: their reduced directions are `(0, 1)` and `(1, 0)`.

At the earliest-index point of any line with `k` input points, all other `k - 1` points are included in the later-point scan and have the same normalised direction. The algorithm therefore considers a count of at least `k`, while every counted point really is on that line.

For example, from anchor `(0, 0)`, vectors `(2, 4)` and `(-1, -2)` point in opposite directions but both normalise to `(1, 2)`. Treating the signs separately would split one line into two counts. A vertical vector `(0, -3)` normalises to `(0, 1)`, so no division by a horizontal difference is needed.

The anchor's counter is reset for each new anchor: equal direction keys from different anchors need not describe the same line. The final answer adds one to the best count because the counter records only the other points. Distinct input coordinates also matter: a repeated point would have direction `(0, 0)` and requires separate duplicate handling.

Horizontal points on either side of an anchor likewise share `(1, 0)` after sign normalisation. The method counts lines rather than rays, including points beyond both sides of the anchor.

## Code

```python
from collections import Counter
from math import gcd


def max_collinear_points(points):
    n = len(points)
    if n < 2:
        return n
    best = 1
    for i, (x, y) in enumerate(points):
        counts = Counter()
        for nx, ny in points[i + 1:]:
            dx, dy = nx - x, ny - y
            divisor = gcd(abs(dx), abs(dy))
            dx //= divisor
            dy //= divisor
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            counts[(dx, dy)] += 1
            best = max(best, counts[(dx, dy)] + 1)
    return best
```

## Complexity

There are O(n²) point pairs. Computing a gcd takes O(log C) arithmetic steps for coordinates bounded in magnitude by `C`, giving O(n² log C) time under that arithmetic model. The direction counter and temporary slice use O(n) auxiliary space per anchor.

## Mistakes and edge cases

- Normalise signs so opposite rays through the anchor are counted on the same line.
- Use an exact reduced pair rather than a floating-point slope.
- Distinct points guarantee the gcd divisor is nonzero.
- One point forms a line count of one; this helper also returns zero for an empty input.

## Variations

- Return a representation of a line achieving the maximum.
- Count collinear triples instead of only the largest line.
- For a tiny input, use cross products as an independent cubic-time oracle.

=== card | cses:1079
time: 30 min

## The problem

Answer many queries asking for the binomial coefficient `C(a, b)` modulo the prime `1,000,000,007`. The coefficient counts how many ways to choose `b` items from `a` distinct items.

For `(a, b) = (5, 2)`, the answer is 10. Choosing none or choosing all items gives 1.

## Constraints and what they imply

The original task's `a` values are at most one million, below the modulus, and there can be many queries. Recomputing a complete factorial for every query repeats the same work. Division modulo a prime means multiplying by a modular inverse; ordinary integer division after reducing modulo the prime is not valid.

## Brute force

For each query, compute `a!`, `b!`, and `(a-b)!` as exact integers and divide before reducing modulo the prime. This is mathematically correct but constructs enormous integers and repeats work across queries. A small-input oracle can instead use Pascal's recurrence.

## The insight

Precompute factorials modulo the prime through the largest requested `a`. Since each factorial is nonzero modulo the prime for this input range, Fermat's little theorem gives its inverse as `factorial^(p-2) mod p`. Compute the inverse of the largest factorial once, then fill smaller inverse factorials backwards using `inv_fact[i-1] = inv_fact[i] * i mod p`.

Each answer is then `fact[a] * inv_fact[b] * inv_fact[a-b] mod p`.

## Optimal solution, traced

```steps
For queries up to a=5, build factorials modulo p
    fact[5] = 120
---
Build inverse factorials from inv_fact[5] backwards
    each inverse factorial becomes available
---
For (5, 2), combine fact[5], inv_fact[2], inv_fact[3]
    answer {{10}}
```

The forward recurrence stores `i! mod p`. Since `(i!)^-1 * i = ((i-1)!)^-1 mod p`, the backward recurrence produces the correct inverse for every smaller factorial.

The modulus is prime and every factorial in this task's range is nonzero modulo it, which is why Fermat's inverse exists. For `a = 0`, the initial factorial and inverse factorial are both 1, so query `(0, 0)` works without a special branch.

## Code

```python
def binomial_queries(queries):
    modulus = 1_000_000_007
    if not queries:
        return []
    if any(a < 0 or b < 0 or b > a or a >= modulus for a, b in queries):
        raise ValueError("queries require 0 <= b <= a < modulus")
    limit = max(a for a, _ in queries)
    fact = [1] * (limit + 1)
    for i in range(1, limit + 1):
        fact[i] = fact[i - 1] * i % modulus
    inverse = [1] * (limit + 1)
    inverse[limit] = pow(fact[limit], modulus - 2, modulus)
    for i in range(limit, 0, -1):
        inverse[i - 1] = inverse[i] * i % modulus
    return [fact[a] * inverse[b] * inverse[a - b] % modulus for a, b in queries]
```

## Complexity

For maximum argument `N` and `q` queries, precomputation costs O(N + log p) modular operations, including one modular exponentiation. Answers cost O(q); factorial arrays use O(N) space and the output uses O(q).

## Mistakes and edge cases

- The factorial inverse method here requires `a < p`; a factorial at or above `p` is zero modulo `p`.
- Use modular inverses, not ordinary division of reduced values.
- Handle `b = 0` and `b = a`, both of which yield 1.

## Variations

- Use Pascal's recurrence for a small input and compare every answer.
- Investigate Lucas's theorem when arguments may reach the modulus.
- Precompute combinations for one fixed `a` instead of many arbitrary queries.

=== card | 1178
time: 45 min

## The problem

Each puzzle contains seven distinct lowercase letters. A word matches a puzzle when it contains the puzzle's first letter and every distinct letter in the word belongs to the puzzle. Count matching words for each puzzle; repeated words are counted separately.

For words `["a", "ab", "abc", "d"]` and puzzle `"abcdefg"`, the first three match: they contain `a` and use only puzzle letters. The word `"d"` lacks the required first letter.

## Constraints and what they imply

Only the set of letters in a word matters, not their order or repeated occurrences. Every valid word mask must be a subset of a puzzle's seven-letter mask and include its first-letter bit. Comparing every word with every puzzle can be too slow when both lists are large. Seven distinct puzzle letters allow only `2^6 = 64` subsets that include the required letter.

## Brute force

For each puzzle, scan every word, build its set of letters, and check whether it contains the required letter and is a subset of the puzzle's set. With `W` words and `P` puzzles this takes O(PW) set checks in addition to processing characters. Repeating the word scan for every puzzle is the bottleneck.

## The insight

Represent each word's distinct letters as a 26-bit mask and count how often each mask occurs. For a puzzle, take the bit of its first letter as required and the remaining six bits as `rest`. Enumerate every submask of `rest`, OR in the required bit, and add the stored word frequency for that mask.

Starting from `rest`, the expression `(submask - 1) & rest` visits the next submask. Include zero before stopping: it represents a word whose only distinct letter is the required first one.

## Optimal solution, traced

```steps
Words a, ab, abc, d produce masks {a}, {a,b}, {a,b,c}, {d}
    each mask has frequency 1
---
Puzzle abcdefg requires a
    enumerate subsets of {b,c,d,e,f,g}, adding a to each
---
The masks {a}, {a,b}, {a,b,c} each contribute 1
    answer {{3}}
```

Every enumerated mask includes the first letter and uses only puzzle letters, so any word with that mask is valid. Conversely, removing the required bit from any valid word mask leaves one of the enumerated submasks. Each mask is enumerated once, and its stored frequency counts repeated words correctly.

A word with more than seven distinct letters cannot match any seven-letter puzzle; omitting it from the frequency table is a safe optimisation. Repeated letters within a word do not add bits, so words such as `"aab"` and `"ab"` have the same mask but each contributes to its frequency.

For a smaller illustration, let `rest` contain bits `b` and `c`. The descending submask loop visits `{b,c}`, `{c}`, `{b}`, and the empty set. OR-ing the required `a` bit produces exactly four possible masks, including `{a}`. Subtracting one can set lower bits that were not in `rest`; the subsequent AND removes those unrelated bits.

The algorithm does not construct an array for all `2^26` possible masks. It stores only masks actually found in the words, and a missing mask contributes zero through the counter. This distinction keeps memory proportional to the input rather than to the full alphabet's power set.

## Code

```python
from collections import Counter


def valid_word_counts(words, puzzles):
    counts = Counter()
    for word in words:
        mask = 0
        for char in word:
            mask |= 1 << (ord(char) - ord("a"))
        if mask.bit_count() <= 7:
            counts[mask] += 1

    answers = []
    for puzzle in puzzles:
        required = 1 << (ord(puzzle[0]) - ord("a"))
        rest = 0
        for char in puzzle[1:]:
            rest |= 1 << (ord(char) - ord("a"))
        subset = rest
        total = 0
        while True:
            total += counts[subset | required]
            if subset == 0:
                break
            subset = (subset - 1) & rest
        answers.append(total)
    return answers
```

## Complexity

Building masks takes O(total word characters) time and stores O(U) distinct word masks. Each seven-letter puzzle requires O(7 + 2^6) expected dictionary operations, so total time is O(total word characters + P * 64). The frequency map and returned answers use O(U + P) space.

## Mistakes and edge cases

- Count each word occurrence, not just each distinct mask.
- Include the zero submask, corresponding to the required letter alone.
- The `2^6` bound relies on the task's seven distinct puzzle letters.
- Ignore repeated letters within a word when building its mask.

## Variations

- Enumerate submasks for a puzzle with a different fixed number of distinct letters.
- Use direct set comparisons as an oracle for small random inputs.
- Return the matching word masks rather than only their total frequency.
