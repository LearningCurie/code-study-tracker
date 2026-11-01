=== card | 509
time: 15 min

## The problem

The sequence starts with 0 and 1; each subsequent entry is the sum of its two immediate predecessors. Given a nonnegative index `n`, return the value at that index. For example, index 6 gives 8. The index is zero-based, so indices 0 and 1 are distinct base cases.

## Constraints and what they imply

The practice problem restricts `n` to 0 through 30. Even a direct recursive calculation fits this small bound, but its repeated work grows rapidly. Python integers do not overflow, though the cost of arithmetic on arbitrarily large values is not actually constant.

## Brute force

Use the definition literally: return `fib(n - 1) + fib(n - 2)` after handling 0 and 1. This is correct by induction, but recomputes overlapping subproblems; its recursion tree has exponential size and depth O(n). Memoizing those calls would remove repetition at the cost of O(n) stored values.

## The insight

Only the last two values are needed to make the next. Before each iteration, maintain `a = F(i)` and `b = F(i + 1)`. Simultaneous assignment advances both without accidentally using the already updated `a`. Starting with `(0, 1)`, after n iterations the invariant gives `a = F(n)`.

## Optimal solution, traced

```steps
n = 4: start at i = 0 with (a, b) = (0, 1)
---
After one step (1, 1); after two steps (1, 2)
---
After three steps (2, 3); after four steps (3, 5)
---
Return a = {{3}}
```

## Code

```python
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

## Complexity

There are O(n) additions and two stored integer values. Under fixed-width arithmetic this is O(n) time and O(1) space; for unbounded n, Fibonacci numbers have O(n) bits and big-integer arithmetic and storage must also be counted.

## Mistakes and edge cases

- Return zero for n = 0; a loop starting at 2 must still treat both bases correctly.
- Do not update `a` and then compute `b` from its new value.
- The contract requires n >= 0; this function does not validate negative indices.

## Variations

- Return the first n sequence entries instead of one indexed value.
- Use matrix exponentiation or fast doubling to reduce the number of arithmetic operations.

=== card | 344
time: 15 min

## The problem

Reverse a mutable list of characters in place. The caller observes the changed list; the function returns `None`. For `["a", "b", "c"]`, the same list becomes `["c", "b", "a"]`. No second array of characters is needed.

## Constraints and what they imply

The practice input may contain up to 100,000 characters, so an O(n) pass is appropriate. A recursive call per pair can exceed Python's recursion limit even though recursion is a natural proof technique. This implementation uses a loop, and also handles an empty list.

## Brute force

Copy the list in reverse order, then assign that copy back to the original. This takes O(n) time and O(n) auxiliary space. Rebinding the local parameter to a new list would not modify the caller's original object, so it would not satisfy the in-place contract.

## The insight

The outermost unmatched positions belong in each other's places. Swap them, then solve the smaller interior interval. The invariant is that positions outside `[left, right]` already match the reversal of the original list, while the interval still contains its original characters in their original order. Initially the interval is the entire list; each swap extends the correct outside regions. When the pointers meet or cross, at most the middle character remains and it is already correct.

## Optimal solution, traced

```steps
Input [a, b, c, d], left = 0, right = 3
---
Swap a and d: [d, b, c, a], then move inward
---
Swap b and c: [d, c, b, a], pointers cross
---
The same list now contains {{[d, c, b, a]}}
```

## Code

```python
def reverse_chars(chars):
    left, right = 0, len(chars) - 1
    while left < right:
        chars[left], chars[right] = chars[right], chars[left]
        left += 1
        right -= 1
```

## Complexity

Each pair is swapped once: O(n) time and O(1) auxiliary space. A recursive formulation has the same time but O(n) call-stack space.

## Mistakes and edge cases

- Move both pointers after the swap or the loop may not terminate.
- The middle character of an odd-length list needs no swap.
- Strings themselves are immutable in Python; the contract takes a mutable list.

## Variations

- Reverse only a specified inclusive interval of a list.
- Reverse word order while retaining the characters within each word.

=== card | 231
time: 15 min

## The problem

Given an integer, decide whether it equals `2^k` for some integer `k >= 0`. Thus 1 and 16 qualify, while 0, negative numbers, and 12 do not. Return a Boolean rather than the exponent.

## Constraints and what they imply

The original domain is signed 32-bit integers. Values can be nonpositive, so checking divisibility alone is insufficient: zero would remain zero forever when divided by two. Each valid positive value larger than one has a strictly smaller positive quotient after division.

## Brute force

Start from 1 and repeatedly double until reaching or passing a positive input; report whether equality was reached. It performs O(log n) doublings and uses constant storage, assuming bounded integer operations. A fixed-width implementation should avoid overflow when doubling near its limit.

## The insight

One is the power with exponent zero. For any integer greater than one, it is a power of two exactly when it is even and its half is a power of two. Both directions follow by removing or restoring one factor of two. The loop preserves this equivalence while strictly decreasing n; when it stops, equality with one is exactly the required answer.

## Optimal solution, traced

```steps
n = 12: positive and even, divide to get 6
---
6 is even, divide to get 3
---
3 is odd and not 1, so stop
---
Return {{False}}
```

## Code

```python
def is_power_of_two(n):
    while n > 1 and n % 2 == 0:
        n //= 2
    return n == 1
```

## Complexity

At most O(log n) divisions are performed for positive n, with O(1) auxiliary space under the fixed-width model. A recursive version uses O(log n) stack frames. A positive integer with a single set bit can alternatively be recognized with `n & (n - 1)`.

## Mistakes and edge cases

- Check 1 as a valid power; its exponent is zero.
- Reject zero and negative values rather than repeatedly dividing zero.
- Do not use floating-point logarithms to decide exact integer equality.

## Variations

- Return the exponent when the input is a power, and a sentinel otherwise.
- Test powers of an arbitrary integer base greater than one.

=== card | 326
time: 15 min

## The problem

Determine whether an integer can be written as `3^k` for some nonnegative integer k. For example 1, 3 and 81 qualify; 9 is valid but 12, 0 and -3 are not. Return a Boolean.

## Constraints and what they imply

Inputs lie in the signed 32-bit range in the practice problem. The base case 1 is necessary because it represents exponent zero. Nonpositive inputs must be rejected; otherwise repeatedly dividing zero would not decrease it.

## Brute force

Generate 1, 3, 9 and so on until the value reaches or exceeds the input, then compare. This requires O(log n) multiplications for positive n and O(1) storage. Fixed-width languages must guard the next multiplication against overflow.

## The insight

Any power of three above one is divisible by three, and removing one factor leaves another power of three. Conversely, multiplying any power of three by three produces another one. Repeatedly stripping factors preserves the yes/no answer and strictly decreases a positive input. If the remaining value is one, all factors were three; any other remainder proves the original number was not a power of three.

## Optimal solution, traced

```steps
Start n = 81
---
Divide by 3: 81 -> 27 -> 9
---
Divide twice more: 9 -> 3 -> 1
---
The remainder is one, so return {{True}}
```

## Code

```python
def is_power_of_three(n):
    while n > 1 and n % 3 == 0:
        n //= 3
    return n == 1
```

## Complexity

The number of divisions is O(log n) for positive n, and auxiliary space is O(1) for the iterative implementation. A direct recursive version takes the same number of operations but O(log n) stack space.

## Mistakes and edge cases

- Treat 1 as valid, even though no division is performed.
- Zero and negative inputs must not enter an endless factor-stripping loop.
- Divisibility by three once is not enough: 12 is divisible but is not a power.

## Variations

- Count how many factors of three divide a positive integer.
- For a fixed integer range, investigate using divisibility by its largest representable power of three.

=== card | 779
time: 25 min

## The problem

Start with row 1 containing the single symbol `0`. To make a new row, replace each `0` with `01` and each `1` with `10`. Given a row number `n` and a one-based position `k` within that row, return its symbol as an integer. For instance, row 3 is `0110`, so position 4 contains 0.

## Constraints and what they imply

The practice problem allows `1 <= n <= 30` and `1 <= k <= 2^(n-1)`. The row length doubles at every step, so explicitly constructing row 30 can require hundreds of millions of symbols. Only one symbol is requested; the algorithm should follow its ancestry instead. The position is one-based, which determines the odd/even child rule.

## Brute force

Start with `"0"` and repeatedly build a new string by replacing every symbol with its two children. Index the finished row at `k - 1`. This uses O(2^n) time and space for the final row, and is useful only for very small rows. Constructing it also does work for all the positions we never inspect.

## The insight

Each parent contributes two consecutive children. The parent of position k is at `(k + 1) // 2` in the previous row. An odd-positioned child copies its parent; an even-positioned child flips it. Walk upward, accumulating the parity of the flips. The loop invariant says that the answer at the original position equals the current ancestor's symbol XOR the accumulated flip parity.

At each step the row number decreases, and the parent position stays in range, so the walk reaches row 1. That root symbol is zero; XOR with zero leaves the accumulated parity as the answer. This is an induction on the row number as well as a termination argument.

## Optimal solution, traced

```steps
n = 4, k = 6, flip = 0
---
6 is an even child: flip = 1; parent is row 3, position 3
---
3 is odd: flip stays 1; parent is row 2, position 2
---
2 is even: flip becomes 0; parent is row 1, position 1
---
Root is 0; 0 XOR 0 gives {{0}}
```

## Code

```python
def kth_symbol(n, k):
    flip = 0
    while n > 1:
        flip ^= (k % 2 == 0)
        k = (k + 1) // 2
        n -= 1
    return int(flip)
```

## Complexity

There is one iteration per row, so time is O(n) and auxiliary space is O(1), under bounded integer arithmetic. Recursive ancestry uses O(n) stack frames. Another characterization counts the set bits of `k - 1` modulo two; the ancestor walk makes the construction rule explicit.

## Mistakes and edge cases

- Position k is one-based: it is even positions, not odd ones, that flip.
- The parent position is rounded up, not down.
- Row 1 contains only one valid position; return zero there.
- Do not build an entire large row or confuse a child's index with its parent index.

## Variations

- Compute the answer from the parity of the set bits of `k - 1`.
- Answer many queries in the same row and compare the ancestor method with bit counting.

=== card | 1922
time: 25 min

## The problem

Count length-n decimal digit strings whose zero-based even positions contain even digits and whose odd positions contain prime digits. Leading zero is permitted because these are strings of a fixed length. Return the count modulo 1,000,000,007. For n = 2 there are 5 choices at position 0 and 4 at position 1, so the answer is 20.

## Constraints and what they imply

The practice problem permits n as large as 10^15, far too large to construct a string or multiply once per position. Even positions admit 0, 2, 4, 6, 8; odd positions admit 2, 3, 5, 7. A string of odd length has one more even position than odd position. Modular arithmetic bounds intermediate values, while exponentiation by repeated squaring makes the enormous exponent manageable.

## Brute force

Enumerate all `10^n` digit strings and test the rule at every position, counting those that pass. This uses O(n 10^n) time and O(n) space for a candidate, and is practical only as a tiny-input oracle. Even multiplying the appropriate number of choices n times remains O(n), which is infeasible at the stated upper bound.

## The insight

Choices at distinct positions are independent: choosing a digit at one position does not change any other position's allowed set. By the product rule, the unmodded answer is `5^ceil(n/2) * 4^floor(n/2)`. For a power, write the exponent in binary. Whenever its current low bit is one, multiply the result by the current base; square the base and halve the exponent each round.

The exponentiation invariant is that the product of the accumulated result and the current base raised to the remaining exponent equals the original power modulo the modulus. Squaring and halving preserves it for even exponents, and multiplying once additionally handles odd exponents. When the exponent reaches zero, the accumulator is the required power.

## Optimal solution, traced

```steps
n = 3: even positions 0 and 2 have five choices each
---
Odd position 1 has four choices
---
Compute 5^2: square 5 to 25, then use the remaining binary bit
---
Multiply 25 by 4 and reduce modulo 1,000,000,007: {{100}}
```

## Code

```python
def count_good_numbers(n):
    mod = 1_000_000_007

    def power(base, exponent):
        result = 1
        while exponent:
            if exponent % 2:
                result = result * base % mod
            base = base * base % mod
            exponent //= 2
        return result

    return power(5, (n + 1) // 2) * power(4, n // 2) % mod
```

## Complexity

Each power uses O(log(n + 1)) modular multiplications and O(1) auxiliary space under fixed-width arithmetic. The two powers are computed sequentially, not by enumerating strings. The modulus keeps each intermediate product bounded, although a fixed-width language must use a type wide enough for a product before reduction.

## Mistakes and edge cases

- Index positions from zero and include zero among the even digits.
- Do not treat 1 as prime or 2 as an odd-position invalid digit.
- For odd n, the even positions get the extra choice.
- Reducing after multiplication is safe; reducing the exponent modulo the modulus without further proof is not.

## Variations

- Use Python's three-argument `pow` for modular exponentiation.
- Count strings when each position belongs to one of several repeating classes of allowed digits.

=== card | 241
time: 35 min

## The problem

Given an expression of nonnegative integer literals joined by `+`, `-`, and `*`, return all values obtainable by inserting parentheses in every possible binary grouping. Include repeated values when different groupings yield the same result. For `2-1-1`, the two groupings yield 2 and 0; either ordering of those results is acceptable.

## Constraints and what they imply

The practice expression has at most 20 characters, contains valid nonnegative integer operands and the three operators, and has no pre-existing parentheses. Operands can contain more than one digit. There may be exponentially many groupings, so returning all results already requires exponential output space. Negative intermediate results are possible even though every input literal is nonnegative.

## Brute force

Generate every full binary parenthesization, turn each into an expression, and evaluate it separately. The number of groupings with m operators is the Catalan number C_m; each evaluation can take O(m) work in addition to constructing the trees. This approach makes a good independent oracle at small sizes, but repeatedly evaluates identical subexpressions.

## The insight

Every binary grouping has exactly one final operation at its root. Choose each operator in turn as that root. The operands on its left and right form two smaller contiguous expressions; independently enumerate their possible results and combine every left result with every right result using the chosen operation. A single literal has exactly one result, itself.

For completeness, every grouping has a root operator that the loop chooses, and both of its child groupings are generated by induction. For uniqueness of grouping, its root and both child groupings determine it. Equal numeric results are deliberately not deduplicated because distinct trees may evaluate identically. Cache each interval's list as a tuple to reuse repeated subproblems without mutating the cached results.

## Optimal solution, traced

```steps
Input 2-1-1; consider the first minus as root
---
Its right side 1-1 evaluates to 0, giving 2-0 = 2
---
Consider the second minus as root: left side 2-1 is 1, giving 1-1 = 0
---
Return both grouping results: {{[2, 0]}}
```

## Code

```python
from functools import cache

def different_results(expression):
    numbers, operators = [], []
    start = 0
    for i, char in enumerate(expression):
        if char in "+-*":
            numbers.append(int(expression[start:i]))
            operators.append(char)
            start = i + 1
    numbers.append(int(expression[start:]))

    @cache
    def solve(left, right):
        if left == right:
            return (numbers[left],)
        result = []
        for split in range(left, right):
            op = operators[split]
            for a in solve(left, split):
                for b in solve(split + 1, right):
                    if op == "+":
                        result.append(a + b)
                    elif op == "-":
                        result.append(a - b)
                    else:
                        result.append(a * b)
        return tuple(result)

    return list(solve(0, len(numbers) - 1))
```

## Complexity

Let m be the number of operators and C_m the m-th Catalan number. All interval result lists together contain O((m + 1)^2 C_m) entries, a conservative upper bound; constructing them takes O((m + 1)^3 C_m) arithmetic and iteration work, also a safe upper bound. Output alone has C_m entries. Cached interval lists and recursion take O((m + 1)^2 C_m) space. Integer arithmetic is treated as constant time.

## Mistakes and edge cases

- Preserve multiplicity: `[2, 2]` can represent two different groupings.
- Parse multi-digit literals as whole numbers, not individual characters.
- Subtraction is directional: apply left minus right, never the reverse.
- A lone number is a complete base expression; cache immutable results.
- This contract excludes unary minus and malformed input.

## Variations

- Return the grouping trees alongside their values.
- Return only distinct values, or count how many groupings produce each value.
