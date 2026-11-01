---
key: bitmath
name: Bits and number theory
stage: engineer
summary: How integers really look in binary, the mask and XOR tricks that follow from it, subsets as bitmasks, and the number theory (gcd, modular arithmetic, primes, combinations, exact arithmetic) that problems and production code keep needing.
why: Integers are bits, and a handful of identities about those bits turn O(n) space into O(1), a 2^n search into a loop over masks, and a Fenwick tree into a few lines. Number theory is the other half: answers "modulo 10^9 + 7", gcd-reduced keys, sieves and binomial coefficients appear in every problem set, and the same ideas run hashing, cryptography, RAID parity and file permissions. Getting them exactly right also means knowing where machines differ from maths: 32-bit overflow in C++ and Java, Python's unbounded ints, and floats that cannot store 0.1.
outcomes:
- Convert between a negative number and its fixed-width two's complement pattern, and emulate 32-bit wrap-around in Python with a mask
- Set, clear, toggle and test bits, and isolate or drop the lowest set bit with x & -x and x & (x - 1)
- Find unpaired values with XOR in O(n) time and O(1) space, and answer range XOR queries with prefix XOR
- Enumerate all subsets as masks and all submasks of a mask, and judge whether 2^n or 3^n fits the limit
- Compute gcd, lcm, modular powers and modular inverses, and explain why each is fast
- Sieve primes up to 10^7, factorise with trial division or a smallest-prime-factor table, and answer nCr mod p queries in O(1)
- Keep arithmetic exact with cross products, reduced fractions and math.isqrt, and use tolerances when floats are unavoidable
cues:
- "Every element appears twice (or three times) except one", parity, or O(1) extra space on integers
- n is at most about 20 and the answer depends on which subset is chosen
- "Return the answer modulo 10^9 + 7", huge exponents, or counts that obviously overflow 64 bits
- Primes, divisors, gcd, ratios, slopes or "reduce the fraction"
- Points, lines, areas or money, where floating-point error could flip a comparison
traps:
- Assuming Python ints wrap at 32 or 64 bits: they never overflow, ~x is -x - 1, and 32-bit problems need explicit masking and a conversion back to signed
- Precedence: in Python 1 << n - 1 is 1 << (n - 1) and x & y + 1 is x & (y + 1); in C++ and Java x & 1 == 0 means x & (1 == 0); parenthesise bitwise expressions
- Dividing under a modulus: (a / b) % m is wrong; multiply by the modular inverse
- Float slopes, == on computed floats and int(math.sqrt(n)) where exact integers (cross products, gcd-reduced pairs, math.isqrt) are needed
- Overflow in C++ and Java: a * b % MOD needs 64-bit operands, abs(INT_MIN) overflows, and 1 << 32 is undefined in C++ but equals 1 in Java
systems:
- Unix permission bits (0o755 is rwxr-xr-x) and flag sets such as re.IGNORECASE | re.MULTILINE or os.O_CREAT | os.O_WRONLY are bitmasks combined with OR and tested with AND
- RAID 5 stores the XOR of each stripe's data blocks as parity, so the blocks of any one failed disk are rebuilt by XOR-ing the survivors
- RSA and Diffie-Hellman are modular exponentiation (Python's three-argument pow uses square-and-multiply), and CPython hashes a non-negative int as its value modulo the prime 2^61 - 1 on 64-bit builds
- Fenwick trees (the next module) walk their array with i & -i, and chess engines such as Stockfish store the board as 64-bit bitboards, so a question such as "which enemy pieces does this piece attack" is a single AND
further:
- Chapter · 40 min | Competitive Programmer's Handbook, ch. 10 Bit manipulation (book pages 95-107) | https://cses.fi/book/book.pdf#page=105
- Chapter · 30 min | Competitive Programmer's Handbook, ch. 21 Number theory (book pages 197-206) | https://cses.fi/book/book.pdf#page=207
- Article · 20 min | cp-algorithms: Bit manipulation, from 'Useful tricks' to 'Language and compiler support' | https://cp-algorithms.com/algebra/bit-manipulation.html#useful-tricks
- Visualisation · 10 min | VisuAlgo: Bitmask (set, clear, toggle and check bits and watch the binary form) | https://visualgo.net/en/bitmask
bank: bits math
---

=== primer | How does two's complement store negative numbers, and what changes in Python? | 15 min
goal: Convert a negative number to and from its fixed-width bit pattern, predict overflow in C++ and Java, and emulate 32-bit arithmetic in Python with masks
tag: bitmath-twos | Two's complement and fixed-width masks
link: Python docs: bitwise operations on integer types | https://docs.python.org/3.12/library/stdtypes.html#bitwise-operations-on-integer-types | 5 min: the opening sentence (results are computed as if in two's complement with infinitely many sign bits), the precedence paragraph and the notes under the operator table; then int.bit_length() and int.bit_count() just below
link: Wikipedia: Two's complement | https://en.wikipedia.org/wiki/Two%27s_complement#Procedure | 8 min: 'Procedure' (invert and add one), then 'Most negative number' further down, which explains why -2^(n-1) has no positive partner
practice: 371, 137, 50

> [!key]
> A machine integer is a fixed number of bits, and **two's complement** gives the top bit a negative weight: in 8 bits the weights are -128, 64, 32, ..., 1. To negate, invert every bit and add one, so `-x == ~x + 1`. The same adder then serves signed and unsigned numbers, and results **wrap modulo 2^n**. Python ints never wrap: they act as if they had **infinitely many sign bits**, so whenever a problem wants 32-bit behaviour you mask with `& 0xFFFFFFFF` and convert back.

## Intuition

A three-digit odometer wraps from 999 to 000. Wind it back one click from 000 and it shows 999, and 999 behaves exactly like -1: add 1 and you get 0. Two's complement is that odometer in binary. An 8-bit register has 256 patterns; read the top half as negative, so 11111111 means -1 and 10000000 means -128. The adder does not change at all. Only your reading of the top bit does.

## How it works

### Weights and range

In an n-bit two's complement number, bit i is worth 2^i, except the top bit, which is worth -2^(n-1). So 8 bits cover -128 to 127, 32 bits cover -2,147,483,648 to 2,147,483,647 (about plus or minus 2.1 × 10^9), and 64 bits about plus or minus 9.2 × 10^18. The top bit acts as a sign bit: 1 means negative.

### Negating: invert and add one

For any pattern x, `x + ~x` is all ones, which is -1. Therefore `~x == -x - 1` and `-x == ~x + 1`. Equivalently, the n-bit pattern of a negative value v is the unsigned number 2^n + v: -12 in 8 bits is 256 - 12 = 244 = 11110100.

### Why one adder serves both

Addition keeps only n bits; the carry out of the top is thrown away, so arithmetic is modulo 2^n. A negative v is stored as 2^n + v, which is the same number as v modulo 2^n, so adding the patterns gives the right pattern for the signed sum. That is why every mainstream CPU uses two's complement, and why C++20 finally requires it.

### Overflow

When the true result does not fit, it wraps: 127 + 1 in 8 bits is 10000000, which reads as -128. Java defines int arithmetic to wrap like this. In C and C++, signed overflow is **undefined behaviour** (the optimiser may assume it never happens), while unsigned arithmetic wraps by definition. The usual overflow sites in problems: `(lo + hi) / 2`, `a * b` before `% MOD`, sums of 10^5 values near 10^9, and negating the most negative number (`abs(INT_MIN)`, or `-n` for n = -2^31), which has no positive partner.

### Python: unbounded ints with infinite sign bits

A Python int is arbitrary precision (CPython stores the magnitude as an array of 30-bit digits plus a sign), so `2**31 - 1 + 1` is simply 2147483648. Bitwise operators behave as if the number were written in two's complement with infinitely many sign bits: -12 is ...1111110100, with ones forever to the left. Consequences you will meet:

- `~x == -x - 1` for every int: `~5 == -6`, `~0 == -1`.
- `x >> k` is floor division by 2^k: `-5 >> 1 == -3` and `-1 >> 10 == -1`. There is no unsigned (logical) right shift.
- `bin(-12)` prints `'-0b1100'` (sign and magnitude), not the bit pattern. Mask first: `format(-12 & 0xFF, '08b') == '11110100'`.
- `x & 0xFFFFFFFF` is the unsigned 32-bit pattern of any int; turning a pattern back into a signed value takes one subtraction (the template).
- `(-5).bit_count()` counts the bits of 5, the absolute value. Count a 32-bit pattern with `(x & 0xFFFFFFFF).bit_count()`.

## Cost

On fixed-width integers each of these operations is one machine instruction: O(1). A Python int operation costs O(d) for d 30-bit digits, which is effectively O(1) below about 2^60 and grows only when numbers get huge. Masking also bounds loops: the carry loop of problem 371 runs forever on unbounded ints with a negative operand (the carry keeps growing), but with a 32-bit mask the carry falls off the top within 32 rounds.

## When to use it

- The statement says "32-bit signed integer", "unsigned integer", "without using + or -", or "if the result overflows, return 0": emulate the width with masks, then convert back.
- Per-bit counting over numbers that can be negative (problem 137): count over 32 positions, then read bit 31 as the sign.
- A C++ or Java solution gives wrong answers that the same Python code gets right: suspect overflow first.
- Not needed when values are small and Python's exact ints already give the answer; do not sprinkle masks "just in case".

| Language | Signed overflow | Right shift of a negative | Shift count of the width or more |
|---|---|---|---|
| Python | never (unbounded) | floor, sign kept | fine (`1 << 100` works); a negative count raises ValueError |
| Java | wraps, defined | `>>` keeps the sign, `>>>` shifts in zeros | the count is masked: `1 << 32 == 1` for an int |
| C++ | undefined behaviour | arithmetic since C++20 | undefined behaviour |

## Worked trace

Encode -12 in 8 bits, check it with the adder, then watch an overflow.

```steps
Start from +12. The top bit will carry the weight -128
    weight  -128  64  32  16   8   4   2   1
    +12        0   0   0   0   1   1   0   0
---
Invert every bit: this is `~12`, which equals -13 (-128 + 64 + 32 + 16 + 2 + 1)
    weight  -128  64  32  16   8   4   2   1
    ~12        {{1   1   1   1   0   0   1   1}}
---
Add 1: the two trailing ones become zeros and the carry stops at bit 2
    weight  -128  64  32  16   8   4   2   1
    ~12 + 1    1   1   1   1   0   {{1   0   0}}   = -12
---
Read it back: -128 + 64 + 32 + 16 + 4 = -12. Read as unsigned, the same bits are 244 = 256 - 12
    pattern    1   1   1   1   0   1   0   0
    signed -12          unsigned 244
---
Check with the adder: 12 + 244 = 256 needs nine bits. The ninth is dropped, leaving 0
       00001100    (12)
    +  11110100    (-12, or 244)
    = {{1}}00000000    the carry leaves the register: 0
---
Overflow: 127 + 1 carries into the sign bit, so the result reads as -128
      01111111    (127)
    + 00000001
    = {{1}}0000000     -128 (undefined behaviour for a signed int in C++)
```

## Template

```python
def to_unsigned(x: int, bits: int = 32) -> int:
    """The bit pattern a bits-wide register holds for x, read as a non-negative int."""
    return x & ((1 << bits) - 1)


def to_signed(x: int, bits: int = 32) -> int:
    """Read the low bits of x as a two's complement signed integer."""
    x &= (1 << bits) - 1
    return x - (1 << bits) if x >> (bits - 1) else x


def bits_of(x: int, bits: int = 8) -> str:
    """The bits-wide two's complement pattern of x as text: bits_of(-12) == '11110100'."""
    return format(to_unsigned(x, bits), f"0{bits}b")
```

`to_signed(a + b)` gives exactly what Java's 32-bit `a + b` returns, so it doubles as an overflow simulator: `to_signed(2**31 - 1 + 1) == -2**31`.

## Pitfalls

- **Reading `bin()` of a negative as its pattern.** `bin(-12)` is `-0b1100`; mask to a width first.
- **Bit loops that never end.** `while x: ...; x >>= 1` spins forever for negative x in Python, because `-1 >> 1 == -1`. Mask to a width first or loop a fixed 32 times.
- **Forgetting to convert back.** After masking, the pattern of -1 is 4294967295 in Python, not -1. Call `to_signed` before returning.
- **The most negative number.** -2^31 has no 32-bit positive partner: `abs` and unary minus overflow in C++ and Java (Java's `Math.abs(Integer.MIN_VALUE)` is still negative). Problem 50 tests n = -2^31; in C++ or Java widen to a 64-bit type before negating.
- **Multiplying before reducing in C++ or Java.** `a * b % MOD` with a and b near 10^9 overflows 32 bits; write `1LL * a * b % MOD` or use `long`.

## Check yourself

Q: Which 8-bit pattern stores -20, and what do `~19`, `-20 >> 2` and `format(-20 & 0xFF, '08b')` give in Python?
A: 20 is 00010100; invert to 11101011 and add one to get 11101100 (unsigned 236 = 256 - 20). `~19 == -20`, because `~x == -x - 1`. `-20 >> 2 == -5`, the floor of -20 / 4. `format(-20 & 0xFF, '08b') == '11101100'`, the pattern itself.

Q: Why does the same adder give correct results for both signed and unsigned numbers?
A: Both are arithmetic modulo 2^n. A negative v is stored as 2^n + v, which is congruent to v modulo 2^n, and addition modulo 2^n gives the same remainder whichever representative you started from. Only the reading of the top bit differs afterwards, and with it which results count as overflow.

Q: A Python popcount `c = 0; while x: c += x & 1; x >>= 1` passes tests with non-negative inputs. What happens for x = -3, and how do you count the 32-bit pattern instead?
A: It never terminates: -3 >> 1 is -2, then -1, and -1 >> 1 stays -1 forever, because Python shifts in infinite sign bits. Mask first with `x &= 0xFFFFFFFF` (the loop then ends within 32 steps and counts 31 ones for -3), or use `(x & 0xFFFFFFFF).bit_count()`.

Q: Counting each bit position modulo 3 over a list (problem 137), you assemble the answer's 32 bits as 4294967292. What is the answer?
A: Bit 31 is set, so the pattern is negative: 4294967292 - 2^32 = -4. That is what `to_signed(4294967292)` returns.

## Lab

- **371 Sum of Two Integers.** Add with `a ^ b` (the sum without carries) and `(a & b) << 1` (the carries), masking both to 32 bits each round, then convert back with `to_signed`. Expected: (5, 7) gives 12, (-9, 4) gives -5, (-1000, -1000) gives -2000, (-1, 1) gives 0, each in at most 32 rounds; without the mask (-1, 1) loops forever.
- **137 Single Number II** (the sign part). After counting bits modulo 3, reinterpret bit 31. Expected: [5, 5, 8, 5] gives 8, and [-4, 6, 6, 6, -2, -2, -2] gives -4 (the raw 32-bit result before conversion is 4294967292).
- **50 Pow(x, n)** (the edge case). n can be -2^31. Expected: (2.0, -3) gives 0.125, (1.0, -2147483648) gives 1.0 and (2.0, -2147483648) gives 0.0; in Python `-n` is safe, in Java or C++ copy n into a 64-bit variable first. The fast squaring loop itself is the modular power card's template.

> [!know]
> You now know how fixed-width integers store negatives, where they overflow in C++ and Java, and how to get exact 32-bit behaviour from Python's unbounded ints with a mask and one subtraction.

=== primer | How do you set, clear and test bits, and why does x & -x isolate the lowest set bit? | 15 min
goal: Manipulate single bits with masks, isolate or drop the lowest set bit, visit only the set bits of a number, and explain the identities a Fenwick tree relies on
tag: bitmath-masks | Bit masks and the lowest set bit
link: cp-algorithms: Bit manipulation | https://cp-algorithms.com/algebra/bit-manipulation.html#useful-tricks | 10 min: 'Useful tricks' from 'Set/flip/clear a bit' through 'Brian Kernighan's algorithm', then 'Language and compiler support' for the C++ built-ins
link: Python docs: int.bit_count | https://docs.python.org/3.12/library/stdtypes.html#int.bit_count | 2 min: bit_count (Python 3.10+) counts the ones of the absolute value; bit_length just above gives the position of the highest set bit plus one
practice: 338, 137, 260

> [!key]
> A **mask** picks bit positions: `1 << i` picks bit i. OR with it sets, AND with its inverse clears, XOR toggles, and `(x >> i) & 1` tests. Two identities do the rest: `x & (x - 1)` **drops the lowest set bit** and `x & -x` **keeps only the lowest set bit**, because subtracting one (or negating) flips exactly the trailing zeros and that lowest one. Loops built on them visit only the set bits, and the Fenwick tree in the next module walks its array with `i & -i`.

## Intuition

Picture a row of light switches whose on/off state is the integer x. A mask is a stencil laid over some switches: OR with it turns those on, AND with its inverse turns them off, XOR flips them, and AND with it shows which of them are on. The lowest set bit is the right-most switch that is on, and most tricks in this card are about finding or removing it in one step.

## How it works

### The four single-bit operations

| Goal | Expression | On x = 0b1010 (10), i = 0 |
|---|---|---|
| Test bit i | `(x >> i) & 1` | 0 |
| Set bit i | `x \| (1 << i)` | 0b1011 (11) |
| Clear bit i | `x & ~(1 << i)` | 0b1010 (10), already clear |
| Toggle bit i | `x ^ (1 << i)` | 0b1011 (11) |

Masks with several bits work the same way: `x & 0xFF` keeps the low byte, `x | flags` sets several bits at once, and `(1 << k) - 1` is k ones, a mask for the low k bits.

### What subtracting one does

Write x as `prefix 1 00...0`: some higher bits, the lowest set bit, then t zeros. Subtracting 1 borrows through the zeros, so `x - 1 = prefix 0 11...1`. The prefix is untouched; the lowest one and everything below it flip. Hence:

- `x & (x - 1) = prefix 0 00...0`: the lowest set bit is gone.
- `~x = (~prefix) 0 11...1`, and adding one carries through those ones: `-x = ~x + 1 = (~prefix) 1 00...0`. So `x & -x` keeps only the lowest set bit, because a prefix and its inverse share no ones.

Both work for any x > 0 and give 0 for x = 0. In Python they work on ints of any size, since `-x` is exact. To turn the isolated bit into its index (the number of trailing zeros), use `(x & -x).bit_length() - 1`.

### Visiting only the set bits

`while x: low = x & -x; ...; x ^= low` handles each set bit once, lowest first. Counting the rounds of `x &= x - 1` is Brian Kernighan's popcount. In Python just call `x.bit_count()` (3.10+) or `bin(x).count("1")` on older versions. C++20 has `std::popcount` and `std::countr_zero` (GCC also has `__builtin_popcount` and `__builtin_ctz`); Java has `Integer.bitCount` and `Integer.lowestOneBit`.

### Why the Fenwick tree cares

A Fenwick tree stores at index i the sum of the `i & -i` elements that end at i. A prefix query walks down with `i -= i & -i`, which is the same as `i & (i - 1)`: 13 = 1101, then 12 = 1100, then 8 = 1000, then 0, one step per set bit. An update walks up with `i += i & -i`: 5, 6, 8, 16, ... Each walk takes O(log n) steps, because the query removes a set bit every step and the update moves the lowest set bit at least one place left. If `x & -x` is solid now, that module is mostly bookkeeping.

## Cost

Each mask operation is one instruction on fixed-width integers and O(1) on Python ints below about 2^60. Visiting set bits with `x &= x - 1` costs one round per set bit, O(popcount(x)), instead of one per bit position, O(bit_length(x)). `int.bit_count()` runs in C over the int's internal 30-bit digits, so it is effectively O(1) for word-sized values.

## When to use it

- Flags and small sets: permissions, feature toggles, "which of the 26 letters appear" (`mask |= 1 << (ord(c) - 97)`), the visited set in bitmask DP.
- Counting ones, checking for a power of two (`x > 0 and x & (x - 1) == 0`), finding the lowest or highest set bit (`bit_length`).
- "For every number up to n" questions, where `i & (i - 1)` and `i >> 1` point to a smaller number whose answer you already have.
- Answers that decompose by bit position (AND, OR or XOR of many numbers, counts modulo 3): loop over the 32 positions and test each.
- Not for big sets: a mask over 10^6 elements is a 10^6-bit int, and since Python ints are immutable every single-bit update builds a new one. Use a `bytearray` or a `set` instead.

## Worked trace

Take x = 44 = 00101100 (8-bit view) and compute both identities.

```steps
x = 44. Its lowest set bit is bit 2 (value 4), with two zeros below it
    x          0 0 1 0 1 {{1}} 0 0    = 44
---
x - 1 borrows through the trailing zeros: the lowest one and every bit below it flip
    x          0 0 1 0 1 {{1 0 0}}    = 44
    x - 1      0 0 1 0 1 {{0 1 1}}    = 43
---
x & (x - 1): the prefix 00101 survives and the low part is all zeros, so the lowest set bit is dropped
    x & (x-1)  0 0 1 0 1 {{0 0 0}}    = 40
---
~x inverts everything: the prefix becomes 11010 and the low part 011
    x          0 0 1 0 1 1 0 0
    ~x         {{1 1 0 1 0}} 0 1 1    = -45
---
-x = ~x + 1: the carry ripples through the trailing ones and stops at bit 2
    ~x         1 1 0 1 0 0 1 1
    -x         1 1 0 1 0 {{1 0 0}}    = -44
---
x & -x: the two prefixes are inverses, so only the lowest set bit survives
    x          0 0 1 0 1 1 0 0
    -x         1 1 0 1 0 1 0 0
    x & -x     0 0 0 0 0 {{1}} 0 0    = 4, at index 4.bit_length() - 1 = 2
```

## Template

```python
def test_bit(x: int, i: int) -> bool:
    return (x >> i) & 1 == 1


def set_bit(x: int, i: int) -> int:
    return x | (1 << i)


def clear_bit(x: int, i: int) -> int:
    return x & ~(1 << i)


def toggle_bit(x: int, i: int) -> int:
    return x ^ (1 << i)


def lowest_bit(x: int) -> int:
    """Value of the lowest set bit: 44 (0b101100) -> 4. Zero for x == 0."""
    return x & -x


def drop_lowest_bit(x: int) -> int:
    """x with its lowest set bit cleared: 44 -> 40."""
    return x & (x - 1)


def set_bit_indices(x: int):
    """Indices of the set bits of x >= 0, lowest first, in O(number of set bits)."""
    while x:
        low = x & -x
        yield low.bit_length() - 1
        x ^= low
```

## Pitfalls

- **Precedence.** In Python, arithmetic binds tighter than shifts, shifts tighter than `&`, then `^`, then `|`, and all of them tighter than comparisons. So `1 << n - 1` is `1 << (n - 1)` and `x & y + 1` is `x & (y + 1)`. In C, C++ and Java comparisons bind tighter than `&`, so `x & 1 == 0` means `x & (1 == 0)`. Parenthesise every bitwise expression.
- **Zero.** `x & -x` and `x & (x - 1)` both return 0 for x = 0, so `while x` loops are safe, but `(x & -x).bit_length() - 1` gives -1, which is not an index.
- **Negative numbers.** `bit_count()` counts the absolute value's ones, and `x & -x` for negative x isolates the lowest set bit of the infinite pattern. Mask to a width first if you mean a 32-bit pattern.
- **Narrow literals in C++ and Java.** `1 << i` is a 32-bit int; for i of 31 or more use `1ULL << i` or `1L << i`.
- **Huge bitsets as Python ints.** Fine for one-off set algebra, slow for millions of single-bit updates.

## Check yourself

Q: Trace a Fenwick prefix query from i = 22: list the indices visited by `i -= i & -i` until 0. How does the number of steps relate to 22's binary form?
A: 22 = 10110, then 20 = 10100, then 16 = 10000, then 0. Three steps, one per set bit of 22, because each step removes the lowest set bit.

Q: Prove that `x & -x` is a power of two for every x > 0.
A: Write x as P followed by a 1 at position t and t zeros. Then ~x is ~P, a 0 at position t and t ones; adding 1 turns those ones into zeros and the 0 at t into a 1, leaving ~P above it. AND with x: the high parts give P & ~P = 0, position t gives 1 & 1 = 1, and the low t bits give 0. Exactly one bit is set, so the result is 2^t.

Q: How do you test, without a loop, whether x has exactly one set bit, and whether it has at most two?
A: Exactly one: `x > 0 and x & (x - 1) == 0` (dropping the only bit leaves zero). At most two: let `y = x & (x - 1)`; then x has at most two set bits exactly when `y & (y - 1) == 0`, because two drops must clear everything.

Q: A colleague writes `def lowbit_index(x): return (x & -x).bit_length()`. What is wrong?
A: It is off by one: for x = 1 (bit 0) it returns 1, and in general it returns index + 1, because `bit_length` of 2^t is t + 1. It also returns 0 for x = 0, which looks like a valid index. Subtract one and handle zero separately.

## Lab

- **338 Counting Bits.** Fill `bits[0..n]` in one pass, each entry from an earlier one in O(1). Expected: n = 5 gives [0, 1, 1, 2, 1, 2] and n = 8 gives [0, 1, 1, 2, 1, 2, 2, 3, 1], in O(n) total with no inner loop over bits.
- **137 Single Number II** (the counting part). Test bit i of every number with `(x >> i) & 1` and keep the counts modulo 3. Expected: [5, 5, 8, 5] gives 8, in O(32n) time and O(1) space.
- **260 Single Number III.** You will need `x & -x` to split the numbers into two groups (the XOR card explains the split). Expected: [4, 9, 4, 6, 2, 2] gives 6 and 9, in either order.

> [!know]
> You now know how to set, clear, toggle and test bits, drop or isolate the lowest set bit, and walk the set bits of a number, which is all the bit machinery a Fenwick tree needs.

=== primer | Why does XOR find the number that appears once? | 12 min
goal: Use XOR's cancellation laws to find unpaired values in O(n) time and O(1) space, separate two unknowns by a bit where they differ, and answer range XOR queries with prefix XOR
tag: bitmath-xor | XOR cancellation and prefix XOR
link: Wikipedia: Exclusive or, properties | https://en.wikipedia.org/wiki/Exclusive_or#Properties | 5 min: the list of properties (commutativity, associativity, 0 as the identity, every value its own inverse); skip the logic notation
link: Wikipedia: Standard RAID levels | https://en.wikipedia.org/wiki/Standard_RAID_levels#RAID_5 | 5 min: 'RAID 5' (striping with distributed parity), then the first paragraph of 'RAID 6', which states that the P parity block is the XOR of the data, as in RAID 5
practice: 136, 260

> [!key]
> XOR is addition without carries, bit by bit. It is commutative and associative, `x ^ 0 == x` and `x ^ x == 0`. So XOR-ing a whole list, in any order, **cancels every value that occurs an even number of times** and leaves the XOR of the rest: one pass and one variable find the single unpaired value. The same laws find a missing number, two unknowns (split by a bit where they differ) and the XOR of any range from prefix XORs.

## Intuition

Treat each bit of an accumulator as a light switch that a number may flip. A value that appears twice flips the same switches twice, leaving them as they were. After the whole list, only the switches flipped by the lonely value are on, so the accumulator spells that value. The order of the flips does not matter, just as a switch's final state depends only on how many times it was flipped.

## How it works

### The laws

- `a ^ b == b ^ a` and `(a ^ b) ^ c == a ^ (b ^ c)`: you may regroup and reorder freely.
- `a ^ 0 == a`: 0 is the identity, so a fold starts at 0.
- `a ^ a == 0`: every value is its own inverse, so `a ^ b ^ b == a` (XOR undoes itself).

They hold for negative Python ints too, because every bit position, including the infinite sign bits, is handled independently.

### One unpaired value (problem 136)

Fold the list with XOR. By the first law you may imagine equal values grouped together; each pair becomes 0 and vanishes, leaving the single value.

### A missing number (problem 268, in the bank)

XOR every index 0..n together with every value: each present number now appears twice and cancels, and the missing one appears once. `0 ^ 1 ^ ... ^ n` even has a closed form with period 4, the template's `xor_upto`.

### Two unpaired values (problem 260)

XOR everything to get `d = a ^ b`, which is non-zero because a and b differ. Any set bit of d marks a position where exactly one of a and b has a 1; take the lowest, `low = d & -d` (masks card). Split the numbers by that bit. a and b land in different groups, while both copies of any duplicated value land in the same group and still cancel. So XOR-ing one group gives a, and `d ^ a` gives b.

### Range XOR with prefixes

Like prefix sums: with `px[i] = nums[0] ^ ... ^ nums[i - 1]`, the XOR of `nums[l..r]` is `px[r + 1] ^ px[l]`, because the shared prefix cancels. Problems 1310 and 1442 build on this, and "which letters have an odd count so far" is a prefix XOR of one-bit masks.

### What XOR cannot do

It cancels pairs, not triples. If every other value appears three times (problem 137), the fold leaves the single value mixed with every other value, which is useless. Count each bit position modulo 3 instead (masks card).

## Cost

One pass with one integer of state: **O(n) time and O(1) extra space**, against O(n) extra space for a Counter or set, or O(n log n) to sort and compare neighbours. The two-unknowns version makes two passes, still O(n). Prefix XOR costs O(n) to build and O(1) per range query.

## When to use it

| The statement says | Use |
|---|---|
| every value twice except one, O(1) extra space | fold everything with XOR |
| one value of 0..n is missing | XOR of all indices and values (or n(n + 1)/2 minus the sum) |
| two values once, all others twice | XOR, then split by the lowest bit of a ^ b |
| every value three times except one | per-bit counts modulo 3, not XOR |
| XOR of a range, many queries | prefix XOR |
| parity of letter counts in substrings | prefix XOR of letter masks plus a dict of seen masks |

If space is not tight, a Counter is clearer and copes with any multiplicity. Reach for XOR when O(1) space is required, or when the problem is literally about XOR.

## Worked trace

Fold [4, 1, 2, 1, 2], showing three bits.

```steps
acc starts at 0. Fold in 4: bit 2 switches on
    acc 000  ^  x 100  =  {{100}}   (4)
---
Fold in 1: bit 0 switches on
    acc 100  ^  x 001  =  {{101}}   (5)
---
Fold in 2: bit 1 switches on
    acc 101  ^  x 010  =  {{111}}   (7)
---
The second 1 switches bit 0 off again
    acc 111  ^  x 001  =  {{110}}   (6)
---
The second 2 switches bit 1 off: only the switch flipped once is still on
    acc 110  ^  x 010  =  {{100}}   (4), the single number
```

## Template

```python
from itertools import accumulate
from operator import xor


def xor_all(nums) -> int:
    """XOR of every value; values seen an even number of times cancel out."""
    acc = 0
    for x in nums:
        acc ^= x
    return acc


def xor_upto(n: int) -> int:
    """0 ^ 1 ^ ... ^ n in O(1): the result repeats with period 4."""
    return (n, 1, n + 1, 0)[n % 4]


def prefix_xor(nums) -> list[int]:
    """px[i] = nums[0] ^ ... ^ nums[i - 1]; the XOR of nums[l..r] is px[r + 1] ^ px[l]."""
    return list(accumulate(nums, xor, initial=0))
```

`functools.reduce(operator.xor, nums, 0)` is the one-line form of `xor_all`.

## Pitfalls

- **Wrong multiplicity.** XOR only cancels even counts; for triples or unknown counts use bit counting or a Counter.
- **Splitting by the wrong bit.** In the two-unknowns trick the bit must come from `a ^ b`. A bit taken from anywhere else (say the top bit of the largest value) can put both unknowns in one group.
- **Negating INT_MIN in C++.** If `a ^ b` is -2^31, then `d & -d` negates the most negative int, which is undefined behaviour; compute the split bit on an unsigned copy.
- **The XOR swap.** `a ^= b; b ^= a; a ^= b` zeroes the value when both names refer to the same slot (`arr[i]` and `arr[j]` with i == j). In Python write `a, b = b, a`.
- **Empty input.** The fold of an empty list is 0, which may be a legitimate value; check the contract.

## Check yourself

Q: What does `xor_all([7, 3, 5, 3, 7, 5, 9])` return? The prefix XORs are [0, 7, 4, 1, 2, 5, 0, 9]: what is the XOR of `nums[1..5]`?
A: 9, because 7, 3 and 5 each appear twice. The range [1, 5] holds 3, 5, 3, 7, 5, and its XOR is px[6] ^ px[1] = 0 ^ 7 = 7: the two 3s and the two 5s cancel, leaving 7.

Q: Why must the split bit be a set bit of `a ^ b`, and why are the two copies of a duplicated value never separated?
A: A set bit of a ^ b is a position where a and b differ, so exactly one of them has it and they go to different groups. Two copies of one value have identical bits, so they always choose the same group and cancel inside it. Each group therefore XORs to exactly one unknown.

Q: n - 1 distinct values from 1..n arrive once each on a stream and you have O(1) memory. How do you find the missing one, and why might XOR be safer than the sum formula in C++ or Java?
A: XOR all of 1..n (with `xor_upto`) and every arriving value; the result is the missing number. The sum n(n + 1)/2 overflows a 32-bit int once n reaches 65,536, while an XOR never needs more bits than the values themselves. (A sum in a 64-bit type, or wrapping arithmetic, also works.)

## Lab

- **136 Single Number.** One pass, one variable. Expected: [7, 3, 5, 3, 7] gives 5 and [-1] gives -1, in O(n) time and O(1) space.
- **260 Single Number III.** XOR everything, isolate `low = d & -d`, fold the two groups separately. Expected: [4, 9, 4, 6, 2, 2] gives 6 and 9, and [-3, 0] gives -3 and 0, in O(n) time and O(1) space (two passes).

> [!know]
> You now know why XOR cancels pairs, how to find one or two unpaired values in O(1) space, and how prefix XOR answers range XOR queries.

=== primer | How do you enumerate every subset, and every submask of a mask, with bits? | 15 min
goal: Enumerate all 2^n subsets as masks and all submasks of a mask with s = (s - 1) & mask, fill per-subset values in O(2^n), and decide whether 2^n or 3^n fits the time limit
tag: bitmath-subsets | Subsets and submasks as bitmasks
link: cp-algorithms: Enumerating submasks of a bitmask | https://cp-algorithms.com/algebra/all-submasks.html#enumerating-all-submasks-of-a-given-mask | 8 min: both sections: why s = (s - 1) & m visits every submask in decreasing order, and the 3^n bound for all masks with all their submasks
link: Competitive Programmer's Handbook, section 10.3 | https://cses.fi/book/book.pdf#page=108 | 6 min: 'Representing sets' (book pages 98-99, PDF pages 108-109): set operations as bit operations and the loops for iterating through subsets
practice: 2044, 1178

> [!key]
> With n items, the integers 0 to 2^n - 1 are exactly the subsets: bit i set means item i is in. Loop over `range(1 << n)` to visit them all, and build any per-subset value from **the same mask without its lowest bit**, so all 2^n values cost O(2^n). To visit only the subsets of a given mask, start at `s = mask` and step **`s = (s - 1) & mask`** down to 0: each of its 2^k submasks appears once. Doing that for every mask costs 3^n in total, not 4^n.

## Intuition

A subset is a row of yes/no answers, one per item, which is exactly what a binary number is. With three friends a, b and c, the number 5 = 101 means "a and c are invited". Counting from 0 to 7 lists every guest list once. A submask of 101 is a guest list that only invites people from {a, c}: 101, 100, 001 and 000.

## How it works

### All subsets

`for mask in range(1 << n)` visits every subset once. Item i is in the subset when `(mask >> i) & 1` is 1. Set algebra becomes bit algebra: union `a | b`, intersection `a & b`, difference `a & ~b`, complement within n items `mask ^ ((1 << n) - 1)`, size `mask.bit_count()`, add item i with `mask | (1 << i)`.

### A value for every subset in O(2^n)

Recomputing each subset's sum from its bits costs O(n) per mask, O(n·2^n) in all. But a mask and `mask ^ low`, where `low = mask & -mask` is its lowest set bit, differ by exactly one item, and `mask ^ low` is a smaller number, so its value is already in the table. Hence `sums[mask] = sums[mask ^ low] + a[index of low]`, O(1) per mask. The same move works for OR, AND, XOR, products or any value built one item at a time.

### The submasks of one mask

Listing the submasks of `mask` by testing every number below it wastes time when the mask is sparse. The step `s = (s - 1) & mask` jumps straight to the next smaller submask: subtracting 1 clears the lowest set bit of s and sets every bit below it, and `& mask` keeps only the positions the mask allows. Think of the mask's k set bits as a k-bit counter living in scattered positions; the step decrements that counter. It visits all 2^k submasks in decreasing order and reaches 0 last. Because `(0 - 1) & mask == mask`, the loop must stop explicitly after handling 0.

### Every mask with every submask: 3^n

For each pair (mask, sub) with sub inside mask, every item is in one of three states: in neither, in the mask only, or in both. So there are exactly 3^n pairs, and that is what the nested enumeration costs. For n = 15 that is about 1.4 × 10^7, fine; for n = 20 it is about 3.5 × 10^9, far too slow in Python.

## Cost

| Loop | Iterations | n = 16 | n = 20 |
|---|---|---|---|
| all masks | 2^n | 65,536 | 1,048,576 |
| all masks, testing every bit | n·2^n | about 1.0 × 10^6 | about 2.1 × 10^7 |
| submasks of one mask with k set bits | 2^k | at most 65,536 | at most 1,048,576 |
| all masks with all their submasks | 3^n | about 4.3 × 10^7 | about 3.5 × 10^9 |

At roughly 10^7 simple Python steps per second, n·2^n reaches about 2 × 10^7 at n = 20, a few seconds in pure Python (the lab measures it), so prefer the O(2^n) incremental table there; 3^n fits up to about n = 14 or 15. A table indexed by mask needs 2^n entries; for n = 20 the list alone is 8 MB of pointers.

## When to use it

- n at most about 20 and the answer depends on which subset is chosen: try every mask.
- Items with small attribute sets (letters a to z, ten skills, the seven letters of a puzzle): encode each as a mask, then compare with AND and OR, or look up submasks in a dict (problem 1178).
- Bitmask DP (the advanced DP module): `dp[mask]` over the set of items used so far; this card is its machinery.
- n up to about 40: split into two halves of 20 and combine the half results (meet in the middle) instead of 2^40.
- Not when pruning matters: include/exclude recursion can skip a whole branch once it fails, while a mask loop always pays for all 2^n subsets. Not when order matters (permutations, n!), unless the state can be "set used so far plus last item", which is bitmask DP.

| Approach | Visits | Strength |
|---|---|---|
| `range(1 << n)` | every subset | simple, no recursion, masks index tables directly |
| `itertools.combinations` by size | the subsets of each size k | runs in C, natural for "exactly k items" |
| backtracking | only branches that survive pruning | skips dead branches, builds the subset step by step |

## Worked trace

Enumerate the submasks of mask = 1011.

```steps
mask = 1011 has three set bits, so it has 2^3 = 8 submasks. Start with s = mask
    mask    1 0 1 1
    s       {{1 0 1 1}}   (11)
---
s - 1 = 1010, which lies inside the mask, so the next submask is 1010
    s - 1   1 0 1 0
    s       {{1 0 1 0}}   (10)
---
s - 1 = 1001, inside the mask again
    s       {{1 0 0 1}}   (9)
---
s - 1 = 1000
    s       {{1 0 0 0}}   (8)
---
s - 1 = 0111 sets bit 2, which the mask does not have; & mask removes it
    s - 1   0 1 1 1
    & mask  0 {{0}} 1 1
    s       {{0 0 1 1}}   (3)
---
Then 0010 and 0001: the two low bits count down like a two-bit counter
    s       {{0 0 1 0}}   (2), then {{0 0 0 1}} (1)
---
s - 1 = 0000: the empty set comes last. Handle it, then stop, because 0 - 1 would wrap back to the mask
    s       {{0 0 0 0}}   (0)
    visited: 11, 10, 9, 8, 3, 2, 1, 0
```

## Template

```python
def subsets(items):
    """Every subset of items, one per mask 0 .. 2^n - 1 (bit i set = items[i] chosen)."""
    n = len(items)
    for mask in range(1 << n):
        yield [items[i] for i in range(n) if (mask >> i) & 1]


def submasks(mask: int):
    """Every submask of mask, from mask itself down to 0."""
    s = mask
    while True:
        yield s
        if s == 0:
            return
        s = (s - 1) & mask


def subset_sums(a: list[int]) -> list[int]:
    """sums[mask] = total of a[i] over the bits i of mask, in O(2^n) overall."""
    sums = [0] * (1 << len(a))
    for mask in range(1, 1 << len(a)):
        low = mask & -mask
        sums[mask] = sums[mask ^ low] + a[low.bit_length() - 1]
    return sums
```

## Pitfalls

- **Losing or looping on the empty submask.** `while s:` skips 0, and `while s >= 0` never ends in Python because `(0 - 1) & mask == mask`. Use the yield-then-check shape of the template.
- **Ignoring the limit.** 2^25 is about 3.4 × 10^7 masks, too slow for a Python loop that does real work per mask. Check n before choosing masks.
- **Inconsistent bit order.** Decide once that bit i means `items[i]` and keep it when you turn a mask back into items.
- **Building lists in the hot loop.** `[items[i] for i in ...]` per mask costs O(n) and many allocations; compute the value you need incrementally instead.
- **Width in C++ and Java.** `1 << n` overflows an int for n of 31 or more; use `1LL << n` or `1L << n`.

## Check yourself

Q: List the submasks of 0b10100 in the order the template yields them. How many submasks does 0b1111011 have?
A: 10100 (20), 10000 (16), 00100 (4), 00000 (0). 0b1111011 has six set bits, so it has 2^6 = 64 submasks.

Q: Why does enumerating every mask together with every one of its submasks take exactly 3^n steps?
A: Each (mask, submask) pair assigns every item one of three states: outside the mask, in the mask but not the submask, or in both. Each assignment of states gives exactly one pair and every pair gives one assignment, so there are 3^n pairs, and the submask loop spends O(1) per pair.

Q: You need the heaviest subset of 18 items whose weight stays under a capacity, with weights up to 10^9. Mask loop, backtracking or a knapsack table?
A: Weights up to 10^9 rule out a table indexed by capacity. 2^18 = 262,144 subsets is small, so a mask loop with incremental sums (O(2^n)) is simple and fast; backtracking that stops as soon as the weight exceeds the capacity also works and may visit fewer subsets. With 40 items you would split them into two halves of 20 (meet in the middle).

## Lab

- **2044 Count Number of Maximum Bitwise-OR Subsets.** Work out the largest OR any subset can reach, then count the masks that reach it, computing each mask's OR from the mask without its lowest bit. Expected: [3, 1] gives 2, [2, 2, 2] gives 7 and [5, 1, 4, 2] gives 5, in O(2^n) time for n up to 16.
- **1178 Number of Valid Words for Each Puzzle** (stretch). Count words by letter mask in a dict, then for each puzzle enumerate the submasks of its other six letters and add the first letter's bit. Expected: words ["cab", "bad", "ace", "dabble", "deed"] with puzzles ["abcdefg", "baedcxy", "edcbazy"] give [3, 2, 2]; each puzzle costs 2^6 = 64 lookups instead of a scan over every word.

> [!know]
> You now know how to enumerate every subset as a mask and every submask with `(s - 1) & mask`, fill per-subset values in O(2^n), and judge 2^n against 3^n for a time limit.

=== primer | Why does Euclid's algorithm find the greatest common divisor so fast? | 12 min
goal: Compute gcd, lcm and Bezout coefficients, prove that gcd(a, b) = gcd(b, a mod b), bound the number of steps, and use the gcd to build exact keys for ratios and directions
tag: bitmath-gcd | Euclid's algorithm, gcd and lcm
link: cp-algorithms: Euclidean algorithm | https://cp-algorithms.com/algebra/euclid-algorithm.html#time-complexity | 6 min: 'Time Complexity' (Lamé: consecutive Fibonacci numbers are the worst case) and 'Least common multiple'
link: Python docs: math.gcd | https://docs.python.org/3.12/library/math.html#math.gcd | 2 min: gcd and lcm accept any number of arguments since Python 3.9 and always return a non-negative result (the 3.15 docs also list them under the new math.integer module)
practice: 1071, 149

> [!key]
> Any common divisor of a and b also divides a - q·b, so **gcd(a, b) = gcd(b, a mod b)**, and the pair shrinks until the remainder is 0; the last non-zero value is the gcd. The first number at least halves every two steps, so Euclid takes **O(log min(a, b))** iterations: under 90 even for numbers near 10^18. The lcm is `a // gcd(a, b) * b`, and dividing a pair by its gcd gives an exact, canonical key for a ratio, a slope or a direction.

## Intuition

Tile a 1071 by 462 floor with the largest square tiles that fit exactly. Squares of side 462 cover two 462 by 462 blocks and leave a 147 by 462 strip. Any tile that fits the whole floor must also fit that strip, so the problem shrinks to 462 by 147, then to 147 by 21, and 21 divides 147 exactly: tiles of side 21. Each step cuts off as many full squares as fit and keeps only the leftover rectangle.

## How it works

### The invariant

If d divides a and b, it divides a - q·b for every q, in particular `a mod b`. Conversely, if d divides b and `a mod b`, it divides a = q·b + (a mod b). So the pairs (a, b) and (b, a mod b) have exactly the same common divisors, and therefore the same greatest one. The loop keeps "gcd(a, b) equals the gcd of the original pair" true at every step; when b reaches 0, gcd(a, 0) = a.

### Termination and speed

b strictly decreases (a mod b < b), so the loop ends. Better: two steps later the first number has at least halved. If b ≤ a/2, then a mod b < b ≤ a/2. If b > a/2, the quotient is 1 and a mod b = a - b < a/2. So there are at most about 2·log2(a) steps. Lamé's theorem sharpens this: consecutive Fibonacci numbers are the worst case, because every quotient is 1; even a pair near 10^18 needs only 86 steps.

### The lcm

gcd(a, b) · lcm(a, b) = a · b, so `lcm = a // gcd(a, b) * b`. Divide first: in C++ or Java `a * b / gcd` can overflow even when the lcm itself fits. Python has `math.lcm(*nums)` (3.9+).

### Extended Euclid

Tracking coefficients through the same loop yields integers x and y with a·x + b·y = gcd(a, b) (Bezout's identity). When gcd(a, m) = 1, that x is the inverse of a modulo m, which is how `pow(a, -1, m)` works for any modulus. The next card uses inverses to divide.

### Canonical keys

To group equal ratios p/q or parallel directions (dx, dy), divide both parts by their gcd and fix a sign convention, so that (-4, 6) and (2, -3) both become (2, -3). Equal keys then mean exactly equal ratios, with no floating-point error and no special case for vertical lines. Problem 149 counts points around an anchor by this key. The gcd of lengths matters too: a pattern that tiles strings of lengths m and n must have a length dividing both, and the candidates stop at gcd(m, n).

## Cost

O(log min(a, b)) iterations of one division with remainder each: O(log n) time and O(1) space for word-sized numbers. For huge Python ints each remainder costs more, and CPython's `math.gcd` switches to Lehmer's algorithm, which does most of its work on machine-word approximations. The gcd of a list is a fold, `math.gcd(*nums)` or `functools.reduce(math.gcd, nums)`, costing O(n log max).

## When to use it

- "Reduce the fraction", ratios, aspect ratios, slopes, "same direction": divide by the gcd for an exact key.
- Periodic events that must line up: two lights blinking every 4 and 6 seconds flash together every lcm(4, 6) = 12 seconds.
- "Can steps of size a and b reach exactly k" (water jugs, two coin values with change): only multiples of gcd(a, b) are reachable.
- Rotating an array in place by k positions with cycles: there are gcd(n, k) cycles.
- Not when the inputs are floats: convert to integers (scale, or use Fraction) first. Not when you need the gcd of every pair among 10^5 numbers: count multiples with a sieve over divisors instead.

## Worked trace

```steps
Start with (a, b) = (1071, 462). 462 fits twice into 1071 with 147 left over
    a = 1071   b = 462    1071 = 2 * 462 + {{147}}
---
Replace (a, b) by (b, a mod b) = (462, 147): the same common divisors, smaller numbers
    a = 462    b = 147    462 = 3 * 147 + {{21}}
---
(147, 21): 21 divides 147 exactly
    a = 147    b = 21     147 = 7 * 21 + {{0}}
---
b = 0, so the gcd is a = 21, after three steps. Check: 1071 = 51 * 21 and 462 = 22 * 21
    a = {{21}}     b = 0
---
Worst case for comparison: consecutive Fibonacci numbers, where every quotient is 1
    (55, 34) -> (34, 21) -> (21, 13) -> (13, 8) -> (8, 5)
    -> (5, 3) -> (3, 2) -> (2, 1) -> (1, 0): 8 steps to reach gcd {{1}}
```

## Template

```python
def gcd(a: int, b: int) -> int:
    """Greatest common divisor by Euclid's algorithm; gcd(0, 0) == 0."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """Least common multiple; divide before multiplying to keep numbers small."""
    if a == 0 or b == 0:
        return 0
    return abs(a // gcd(a, b) * b)


def ext_gcd(a: int, b: int) -> tuple[int, int, int]:
    """(g, x, y) with a*x + b*y == g == gcd(a, b), for a, b >= 0."""
    x0, y0, x1, y1 = 1, 0, 0, 1
    while b:
        q = a // b
        a, b = b, a - q * b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return a, x0, y0


def direction_key(dx: int, dy: int) -> tuple[int, int]:
    """Canonical key for the direction (dx, dy) != (0, 0): equal keys exactly when parallel."""
    g = gcd(dx, dy)
    dx, dy = dx // g, dy // g
    if dx < 0 or (dx == 0 and dy < 0):
        dx, dy = -dx, -dy
    return dx, dy
```

In real code prefer `math.gcd` and `math.lcm` (written in C); keep `ext_gcd` for when you need the coefficients.

## Pitfalls

- **Negative inputs.** Python's `%` takes the sign of the divisor, so normalise with `abs` first (the template does; `math.gcd` already returns a non-negative result).
- **gcd(0, 0) = 0.** Dividing by it crashes. `direction_key` needs a non-zero vector, so in problem 149 count duplicate points separately.
- **No sign convention.** Without one, (1, -2) and (-1, 2) become different keys for the same line.
- **lcm overflow in C++ and Java.** Compute `a / gcd(a, b) * b` in 64 bits, and check against the limit when folding over many numbers, because lcms grow very fast.

## Check yourself

Q: Trace gcd(252, 198) and give lcm(252, 198).
A: (252, 198), then (198, 54), then (54, 36), then (36, 18), then (18, 0): the gcd is 18. lcm = 252 // 18 * 198 = 14 * 198 = 2772.

Q: Prove that after two iterations the first number is less than half of what it was.
A: Take the pair (a, b) with a ≥ b; two steps later the first number is a mod b. If b ≤ a/2, then a mod b < b ≤ a/2. If b > a/2, the quotient is 1, so a mod b = a - b < a/2. Either way it at least halves, giving at most about 2·log2(a) iterations.

Q: Which of the points (2, 4), (-3, -6) and (1, 3) lie on one line through the origin, judged by `direction_key`?
A: (2, 4) reduces to (1, 2). (-3, -6) reduces to (-1, -2), and the sign convention flips it to (1, 2). (1, 3) stays (1, 3). So (2, 4) and (-3, -6) share a line through the origin and (1, 3) does not, with no division or float involved.

## Lab

- **1071 Greatest Common Divisor of Strings** (derive). First decide when any common repeating unit can exist at all, then how long the longest one is. Expected: ("XYXYXY", "XYXY") gives "XY", ("XYX", "XY") gives "", and ("AAAA", "AA") gives "AA", in O(m + n) time.
- **149 Max Points on a Line.** For each anchor point, count the later points by `direction_key` and take the largest group plus one. Expected: [(1, 1), (2, 2), (3, 3), (5, 1), (4, 0)] gives 3, and [(0, 0), (94911151, 94911150), (94911152, 94911151)] gives 2 (float slopes wrongly report 3); O(n^2 log C) time for coordinates up to C.

> [!know]
> You now know why Euclid's algorithm is correct and logarithmic, how to get the lcm and Bezout coefficients, and how to turn ratios and directions into exact gcd-reduced keys.

=== primer | How do you compute huge powers and divide under a modulus like 10^9 + 7? | 15 min
goal: Apply the rules of modular arithmetic, compute a^b mod m by repeated squaring in O(log b), and divide modulo a prime with Fermat's little theorem or pow(b, -1, m)
tag: bitmath-modpow | Modular arithmetic and fast power
link: cp-algorithms: Binary exponentiation | https://cp-algorithms.com/algebra/binary-exp.html#algorithm | 8 min: 'Algorithm' and 'Implementation' (the same square-and-multiply loop), then the application 'Effective computation of large exponents modulo a number'
link: cp-algorithms: Modular multiplicative inverse | https://cp-algorithms.com/algebra/module-inverse.html#finding-the-modular-inverse-using-binary-exponentiation | 6 min: the Fermat method, then 'Finding the modular inverse for array of numbers modulo m', which inverts n values with one power and O(n) multiplications
practice: 50, cses:1079

> [!key]
> Reduce after every addition, subtraction and multiplication, because `(a * b) % m == ((a % m) * (b % m)) % m`; numbers then never grow past m^2. Compute a^b by **square and multiply**: walk the bits of b, square the base at every step and multiply it into the result when the bit is 1, so an exponent of 10^18 takes about 60 rounds instead of 10^18. Division has no such rule: multiply by the **modular inverse**, which for a prime p is `pow(b, p - 2, p)` (Fermat) and in Python 3.8+ is `pow(b, -1, m)` for any m coprime to b.

## Intuition

A 12-hour clock only shows remainders: 9 o'clock plus 5 hours is 2 o'clock whether you add 5, 17 or 29 hours. Problems ask for answers "modulo 10^9 + 7" for the same reason. The true count may have thousands of digits, but its remainder is enough to check the answer, and every intermediate value can stay on the clock face.

For powers: 3^13 takes 12 multiplications the slow way. But 13 = 8 + 4 + 1, so 3^13 = 3^8 · 3^4 · 3^1, and 3^2, 3^4 and 3^8 come from squaring three times. That is a handful of multiplications instead of twelve, and for an exponent of 10^18, about 120 instead of 10^18.

## How it works

### The rules

For m ≥ 1, the remainders of a + b, a - b and a · b modulo m depend only on the remainders of a and b. So you may reduce at any point. Python's `%` returns a value in [0, m) for positive m, so `(a - b) % m` is already non-negative (`-7 % 3 == 2`). In C++ and Java `%` keeps the sign of the left operand (`-7 % 3 == -1`), so write `((a - b) % m + m) % m`.

Why 10^9 + 7? It is prime, so every value that is not a multiple of it has an inverse, and it is just below 2^30: the sum of two residues fits a signed 32-bit int, and the product of two, at most about 10^18, fits a signed 64-bit int (limit about 9.2 × 10^18).

### Square and multiply

Keep the invariant `result · base^exp ≡ a^b (mod m)`; it holds at the start with result = 1, base = a, exp = b. Each round: if exp is odd, move one factor of base into result (`result = result * base % m`, conceptually exp - 1); then square the base and halve the exponent (`base = base * base % m`, `exp >>= 1`). Both moves keep the invariant, so when exp reaches 0 the result is the answer. This is the loop form of the divide-and-conquer power from the recursion module. Python's built-in `pow(a, b, m)` runs the same idea in C (scanning the bits from the top, with a sliding window for long exponents); use it in real code.

### Division needs an inverse

`(a / b) mod m` is not `(a mod m) / (b mod m)`: 12 / 4 = 3, but 12 mod 5 = 2 and 2 / 4 is not even an integer. Instead find the inverse of b, the number b' with b · b' ≡ 1 (mod m), and multiply by it. It exists exactly when gcd(b, m) = 1.

- **Fermat's little theorem**: for a prime p and b not divisible by p, b^(p-1) ≡ 1 (mod p), so b^(p-2) is the inverse: `pow(b, p - 2, p)`.
- **Extended Euclid** (gcd card) works for any m coprime to b. Python's `pow(b, -1, m)` does this and raises ValueError when no inverse exists.

### Real-valued powers (problem 50)

The same loop works on floats with no modulus: result and base are floats, and a negative n means computing (1/x)^|n|. Only the edge case differs from the modular version: n = -2^31 cannot be negated inside a 32-bit int (two's complement card).

## Cost

The exponent loses one bit per round, so there are floor(log2 b) + 1 rounds with at most two modular multiplications each: **O(log b) multiplications and O(1) space**. With m below 2^31 every product fits 64 bits, and in Python products below about 10^18 are only a few 30-bit digits, so each step is effectively O(1). Without a modulus the numbers grow: 3^(10^6) has 477,122 digits, and multiplying d-digit numbers costs more than O(d), so never compute a huge power and reduce it at the end. An inverse costs one more power, O(log p).

## When to use it

- "Return the answer modulo 10^9 + 7" (or 998244353): reduce after every operation and divide only through inverses.
- a^b with b up to 10^18, or any associative operation repeated b times (matrix powers for Fibonacci-like recurrences, applying a permutation b times).
- Fractions modulo a prime: an expected value P/Q is reported as P · Q^(-1) mod p.
- Not when the modulus is composite and the divisor shares a factor with it: no inverse exists, so restructure (cancel factors first, use Pascal's rule, or split the modulus with the Chinese remainder theorem).

| Need | Python | C++ or Java |
|---|---|---|
| a^b mod m | `pow(a, b, m)` | the square-and-multiply loop with 64-bit products |
| inverse modulo a prime p | `pow(b, p - 2, p)` | the same loop |
| inverse modulo any m | `pow(b, -1, m)` | extended Euclid |
| exact huge power | `a ** b` (big int) | a big-integer library |

## Worked trace

Compute 3^13 mod 1000, with 13 = 1101 in binary.

```steps
Invariant: result * base^exp = 3^13 (mod 1000). Start with result = 1, base = 3
    exp = 1101   result = 1     base = 3
---
The lowest bit of exp is 1: multiply base into result. Then square base and shift exp
    exp = 110{{1}}   result = {{3}}     base: 3 -> {{9}}
---
The bit is 0: result stays. Square base (9 -> 81) and shift
    exp = 11{{0}}    result = 3     base: 9 -> {{81}}
---
The bit is 1: result = 3 * 81 = 243. Square: 81 * 81 = 6561, which is 561 mod 1000
    exp = 1{{1}}     result = {{243}}   base: 81 -> {{561}}
---
The bit is 1: result = 243 * 561 = 136323, which is 323 mod 1000. exp becomes 0, so stop
    exp = {{1}}      result = {{323}}   base: 561 -> 721 (not needed)
---
Check: 3^13 = 1594323, whose last three digits are 323. Four rounds for exponent 13
    3^13 = 1 594 {{323}}
```

## Template

```python
MOD = 10**9 + 7


def power(base: int, exp: int, mod: int) -> int:
    """base**exp % mod by repeated squaring, exp >= 0 (the built-in pow(base, exp, mod) does the same in C)."""
    result = 1 % mod
    base %= mod
    while exp > 0:
        if exp & 1:                       # this bit of exp is set: multiply its power in
            result = result * base % mod
        base = base * base % mod          # base becomes the next power of two of the original
        exp >>= 1
    return result


def inverse(a: int, p: int) -> int:
    """Inverse of a modulo a prime p (Fermat: a^(p-2)); a must not be a multiple of p."""
    if a % p == 0:
        raise ZeroDivisionError("no inverse")
    return power(a, p - 2, p)


def divide(a: int, b: int, p: int = MOD) -> int:
    """(a / b) mod p for a prime p, valid whenever b is not a multiple of p."""
    return a * inverse(b, p) % p
```

## Pitfalls

- **Reducing only at the end.** Python stays correct but slows down as the numbers grow; C++ and Java overflow silently.
- **Negative remainders in C++ and Java.** `(a - b) % m` can be negative there; add m before the final `% m`.
- **Dividing with `/`.** `(a / b) % m` gives a float and a wrong answer; multiply by the inverse.
- **Inverting a multiple of p.** Fermat silently returns 0 (`pow(0, p - 2, p) == 0`), while `pow(b, -1, m)` raises ValueError. Check divisibility when b can be a multiple of p.
- **`pow(a, b) % m` instead of `pow(a, b, m)`.** The two-argument form builds the full huge number first.
- **Starting with `result = 1`.** For m = 1 every answer is 0; `1 % mod` handles that edge case.

## Check yourself

Q: Trace `power(2, 10, 1000)`: give exp (in binary), result and base after each round.
A: Start: exp 1010, result 1, base 2. Bit 0: result 1, base 4, exp 101. Bit 1: result 4, base 16, exp 10. Bit 0: result 4, base 256, exp 1. Bit 1: result 4 · 256 = 1024, which is 24 mod 1000, and exp becomes 0. Answer 24; indeed 2^10 = 1024.

Q: Why does `pow(b, p - 2, p)` give the inverse of b, and why must p be prime?
A: Fermat's little theorem says b^(p-1) ≡ 1 (mod p) for a prime p and b not divisible by p, so b · b^(p-2) ≡ 1, which is the definition of the inverse. For a composite modulus the theorem fails even for coprime b: `pow(3, 8, 10) == 1`, but 3 · 1 = 3 is not 1 mod 10; the real inverse is 7 = `pow(3, -1, 10)`.

Q: A colleague computes C(n, k) mod 10^9 + 7 as `fact[n] // (fact[k] * fact[n - k]) % MOD`, where `fact` holds factorials already reduced mod MOD. What goes wrong, and what is the fix?
A: Integer division of reduced residues is meaningless: the residue of n! need not be divisible by the product of the other residues, so the result is wrong (or even 0). Multiply by inverses instead: `fact[n] * inverse(fact[k] * fact[n - k] % MOD, MOD) % MOD`, or precompute inverse factorials (combinations card).

## Lab

- **50 Pow(x, n).** Square and multiply on floats; for n < 0 invert x and use -n. Expected: (2.0, 10) gives 1024.0, (2.0, -3) gives 0.125, (0.5, 4) gives 0.0625 and (2.0, -2147483648) gives 0.0, in O(log |n|) multiplications (32 rounds for the largest |n|).
- **Exercise: check `power` against the built-in.** Compute `power(2, 10**18, MOD)` and `inverse(2, MOD)`. Expected: 719476260 and 500000004 (and `2 * 500000004 % MOD == 1`), both matching `pow`, each in about 60 rounds or fewer.
- **CSES 1079 Binomial Coefficients** (stretch). It needs exactly one Fermat inverse for a whole table; the combinations card builds it. Expected: C(5, 3) = 10, C(8, 1) = 8 and C(9, 5) = 126 (unchanged modulo 10^9 + 7).

> [!know]
> You now know the rules for computing modulo m, the square-and-multiply loop and its invariant, and how to divide modulo a prime with an inverse.

=== primer | How does the sieve of Eratosthenes find every prime up to n in O(n log log n)? | 15 min
goal: Test primality and factorise by trial division up to the square root, sieve every prime up to 10^7 with a bytearray, and factorise many numbers quickly with a smallest-prime-factor table
tag: bitmath-sieve | Trial division and the sieve of Eratosthenes
link: cp-algorithms: Sieve of Eratosthenes | https://cp-algorithms.com/algebra/sieve-of-eratosthenes.html#asymptotic-analysis | 10 min: 'Asymptotic analysis' (the sum of n/p over primes), then 'Sieving till root' and 'Memory consumption and speed of operations' (why compact flag arrays are faster)
link: Python docs: math.isqrt | https://docs.python.org/3.12/library/math.html#math.isqrt | 2 min: the exact integer square root (Python 3.8+), the safe bound for divisor loops
practice: 204

> [!key]
> To test one number, try divisors only up to √n: if n = a·b with a ≤ b, then a ≤ √n. To find **every** prime up to n, sieve instead: for each prime p from 2 to √n, cross out p², p² + p, p² + 2p and so on; whatever survives is prime. Prime p costs about n/p crossings and the sum over all primes is about **n ln ln n**, practically linear. In Python keep the flags in a `bytearray` and cross out each prime's multiples with one slice assignment.

## Intuition

Write 2 to 30 on a board. 2 is prime, so strike every second number after it. The next survivor, 3, must be prime (nothing smaller divides it), so strike every third number. Then 5. You can stop before 7: every composite up to 30 has a factor no larger than √30, about 5.5, so it is already struck. Instead of asking "is this one prime?" thirty times, you let each prime announce its multiples.

## How it works

### Trial division

n is composite exactly when it has a divisor d with 2 ≤ d ≤ √n, because divisors come in pairs d and n/d and one of each pair is at most √n. So test d up to `math.isqrt(n)`, the exact integer square root; `int(math.sqrt(n))` can be off by one for large n because of float rounding. Factorising works the same way: divide out each d while it divides n, and if more than 1 is left at the end, that remainder is a prime factor larger than the square root of the original n.

### The sieve

Keep one flag per number, initially "prime". For p = 2, 3, ... up to √n, if p is still flagged, cross out its multiples **starting at p²**. Smaller multiples p·k with k < p have a smaller prime factor (one of k's), and that prime already crossed them out. At the end, every composite has been crossed out by its smallest prime factor, which is at most √n, and every prime survives because nothing crosses out a number without a smaller prime factor.

### Python mechanics

`bytearray([1]) * (n + 1)` makes n + 1 one-byte flags: 10 MB for n = 10^7, against 80 MB for a list, which stores an 8-byte pointer per slot. `is_p[p*p::p] = bytes(count)` crosses out a whole arithmetic progression in one C-level call; the right-hand side must have exactly the slice's length, `len(range(p*p, n + 1, p))`. `itertools.compress(range(n + 1), is_p)` lists the survivors. NumPy (`is_p[p*p::p] = False` on a bool array) does the same; the lab measures all of these.

### Smallest prime factors

A variant stores, for every x, its smallest prime factor `spf[x]`. Then x factorises by repeated division, `x //= spf[x]`, in O(log x) steps, because each step at least halves x. Build the table once up to 10^6 or 10^7 and every "factorise x" or "how many divisors does x have" query becomes almost free: p1^e1 · ... · pk^ek has (e1 + 1)···(ek + 1) divisors.

## Cost

- **Trial division**: O(√n) divisions per number, about 31,623 for n = 10^9. Fine for a few numbers, hopeless for 10^6 of them.
- **Sieve**: the outer loop stops at √n. Prime p crosses out about n/p numbers, and the sum of n/p over primes p is about n ln ln n (a theorem of Mertens). ln ln 10^7 is only about 2.8, so the sieve does a small constant times n work: **O(n log log n) time and O(n) bytes**. Starting at p² instead of 2p saves less than you might think (about 2.12 million crossings instead of 2.20 million for n = 10^6); its real value is that it makes stopping at √n correct.
- **SPF table**: the same sieve cost once, then O(log x) per factorisation.

## When to use it

| Task | Tool | Cost |
|---|---|---|
| is n prime, for a few n up to about 10^12 | trial division to `isqrt(n)` | O(√n) each |
| every prime up to 10^7 | sieve on a bytearray | O(n log log n) time, n bytes |
| factorise many x up to 10^6 | smallest-prime-factor table | sieve once, then O(log x) each |
| is n prime, n up to 10^18 | Miller-Rabin with fixed bases | a dozen modular powers |
| primes in [L, R] with R up to 10^12 and R - L up to 10^6 | segmented sieve using the primes up to √R | about (R - L) log log R + √R |

Miller-Rabin and the segmented sieve are beyond this card (the cp-algorithms pages cover them). Do not sieve when you only need to test one huge number: a sieve to 10^12 would need a terabyte of flags.

## Worked trace

Sieve n = 30. Struck numbers become `.`, and the numbers struck in the current step are highlighted.

```steps
All of 2..30 start as candidates. isqrt(30) = 5, so only p = 2, 3, 5 will cross anything out
     2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
    17 18 19 20 21 22 23 24 25 26 27 28 29 30
---
p = 2 is unmarked, so it is prime: cross out 4, 6, 8, ..., 30, starting at 2 * 2 = 4
     2  3  {{4}}  5  {{6}}  7  {{8}}  9 {{10}} 11 {{12}} 13 {{14}} 15 {{16}}
    17 {{18}} 19 {{20}} 21 {{22}} 23 {{24}} 25 {{26}} 27 {{28}} 29 {{30}}
---
p = 3: start at 9 and step by 3. 12, 18, 24 and 30 were already struck by 2, so only 9, 15, 21 and 27 are new
     2  3  .  5  .  7  .  {{9}}  . 11  . 13  . {{15}}  .
    17  . 19  . {{21}}  . 23  . 25  . {{27}}  . 29  .
---
p = 4 is struck, so skip it. p = 5: start at 25; 30 is already struck
     2  3  .  5  .  7  .  .  . 11  . 13  .  .  .
    17  . 19  .  .  . 23  . {{25}}  .  .  . 29  .
---
The loop ends at p = 5 because 6 * 6 > 30. The survivors are the ten primes up to 30
      {{2}}  {{3}}  .  {{5}}  .  {{7}}  .  .  . {{11}}  . {{13}}  .  .  .
     {{17}}  . {{19}}  .  .  . {{23}}  .  .  .  .  . {{29}}  .
```

## Template

```python
from itertools import compress
from math import isqrt


def is_prime(n: int) -> bool:
    """Trial division by 2 and odd d up to isqrt(n): O(sqrt n)."""
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    for d in range(3, isqrt(n) + 1, 2):
        if n % d == 0:
            return False
    return True


def factorise(n: int) -> dict[int, int]:
    """Prime factorisation of n >= 1 by trial division: {prime: exponent}."""
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:                      # no factor up to its square root is left: n is prime
        factors[n] = factors.get(n, 0) + 1
    return factors


def primes_upto(n: int) -> list[int]:
    """All primes <= n with the sieve of Eratosthenes on a bytearray."""
    if n < 2:
        return []
    is_p = bytearray([1]) * (n + 1)
    is_p[0] = is_p[1] = 0
    for p in range(2, isqrt(n) + 1):
        if is_p[p]:
            is_p[p * p :: p] = bytes(len(range(p * p, n + 1, p)))   # cross out p*p, p*p + p, ...
    return list(compress(range(n + 1), is_p))


def smallest_prime_factors(n: int) -> list[int]:
    """spf[x] = smallest prime dividing x, for 2 <= x <= n; factorise x by x //= spf[x]."""
    spf = list(range(n + 1))
    for p in range(2, isqrt(n) + 1):
        if spf[p] == p:                      # p is prime
            for m in range(p * p, n + 1, p):
                if spf[m] == m:
                    spf[m] = p
    return spf
```

## Pitfalls

- **Off by one at the top.** Problem 204 counts primes strictly **less than** n; `primes_upto(n)` includes n itself.
- **Missing the square root.** `range(2, int(n ** 0.5))` never tests 5 for n = 25; use `range(2, isqrt(n) + 1)`.
- **Slice length mismatch.** Assigning to an extended slice needs a right-hand side of exactly the same length, or Python raises ValueError. Compute it with `len(range(...))` or `(n - p*p) // p + 1`.
- **Memory.** A list of 10^8 flags is 800 MB, a bytearray 100 MB; go further with an odd-only sieve or a packed bitset.
- **0 and 1.** Neither is prime; clear both flags before the loop.

## Check yourself

Q: For n = 50, which values of p cross numbers out, and which number does p = 7 cross out first?
A: isqrt(50) = 7, so p runs from 2 to 7 and the primes among them, 2, 3, 5 and 7, cross numbers out (4 and 6 are already struck and skipped). p = 7 starts at 49, its only multiple from 7² up to 50.

Q: Why is it safe to start crossing out at p² rather than at 2p?
A: Every multiple p·k with k < p has a prime factor q that divides k, so q ≤ k < p. That smaller prime was processed earlier and already crossed p·k out. The first multiple of p that no smaller prime handles is p·p.

Q: You must answer 10^5 queries "how many divisors does x have?" with x up to 10^6. Trial division per query, or something else?
A: Trial division costs up to about 1,000 divisions per query, around 10^8 in total: too slow in Python. Build a smallest-prime-factor table up to 10^6 once, factorise each x in O(log x) by repeated division, and multiply (e + 1) over its exponents. That is CSES 1713 Counting Divisors, in this module's problem bank.

## Lab

- **204 Count Primes.** Count the primes strictly below n with a bytearray sieve. Expected: n = 10 gives 4, n = 30 gives 10, n = 2 gives 0, n = 10^6 gives 78,498 and n = 5 × 10^6 gives 348,513, the last in well under a second.
- **Exercise: factorise with a table.** Build `smallest_prime_factors(10**6)` and factorise 360, 997,920 and 999,983 by repeated division. Expected: {2: 3, 3: 2, 5: 1}, {2: 5, 3: 4, 5: 1, 7: 1, 11: 1} (so 997,920 has 6 · 5 · 2 · 2 · 2 = 240 divisors) and {999983: 1}, the largest prime below 10^6.

> [!know]
> You now know how to test and factorise by trial division, sieve every prime up to 10^7 in about n ln ln n steps, and answer many factorisation queries with a smallest-prime-factor table.

=== lab | Bits for speed: sieves and subset loops, measured | 45 min
goal: Measure how the representation (list, bytearray, NumPy) and the loop structure (Python loop, slice assignment, mask loop, incremental table, pruned recursion) change the speed and memory of the same algorithm
link: cp-algorithms: Sieve of Eratosthenes | https://cp-algorithms.com/algebra/sieve-of-eratosthenes.html#memory-consumption-and-speed-of-operations | 5 min: 'Memory consumption and speed of operations': why compact flag arrays win on cache, and what a packed bitset costs per access
practice: 204, 2044

You will write one sieve four ways and one subset count four ways, check that every version agrees with a brute force, and then time them while the input doubles. Two effects this module keeps relying on become visible: moving the inner loop into C, and shrinking the data so more of it fits in cache.

## Setup

- Python 3.10 or newer, and NumPy (`pip install numpy`).
- If you built the dsakit stress tester and doubling benchmark in the correctness module's project, use them in place of the small helpers in the script.

## Steps

1. Save this as `bits_lab.py`.

```python
import random
import sys
import time
from itertools import combinations, compress
from math import isqrt

import numpy as np


def sieve_loop(n):
    """List of bools, crossing out one number per interpreted step."""
    flags = [True] * (n + 1)
    flags[0:2] = [False] * len(flags[0:2])
    for p in range(2, isqrt(n) + 1):
        if flags[p]:
            for m in range(p * p, n + 1, p):
                flags[m] = False
    return flags


def sieve_list(n):
    """Same list, one slice assignment (run in C) per prime."""
    flags = [True] * (n + 1)
    flags[0:2] = [False] * len(flags[0:2])
    for p in range(2, isqrt(n) + 1):
        if flags[p]:
            flags[p * p :: p] = [False] * len(range(p * p, n + 1, p))
    return flags


def sieve_bytes(n):
    """One byte per number instead of one 8-byte pointer."""
    flags = bytearray([1]) * (n + 1)
    flags[0:2] = bytes(len(flags[0:2]))
    for p in range(2, isqrt(n) + 1):
        if flags[p]:
            flags[p * p :: p] = bytes(len(range(p * p, n + 1, p)))
    return flags


def sieve_numpy(n):
    flags = np.ones(n + 1, dtype=bool)
    flags[:2] = False
    for p in range(2, isqrt(n) + 1):
        if flags[p]:
            flags[p * p :: p] = False
    return flags


def primes_from(flags):
    if isinstance(flags, np.ndarray):
        return np.flatnonzero(flags).tolist()
    return list(compress(range(len(flags)), flags))


def count_subsets_recursive(a, target):
    """Include-or-exclude recursion: 2^n leaves."""
    def go(i, total):
        if i == len(a):
            return 1 if total == target else 0
        return go(i + 1, total + a[i]) + go(i + 1, total)
    return go(0, 0)


def count_subsets_masks(a, target):
    """Rebuild every subset's sum from its bits: O(n 2^n)."""
    n, count = len(a), 0
    for mask in range(1 << n):
        total = 0
        for i in range(n):
            if (mask >> i) & 1:
                total += a[i]
        count += total == target
    return count


def count_subsets_lowbit(a, target):
    """sums[mask] = sums[mask without its lowest bit] + that item: O(2^n)."""
    sums = [0] * (1 << len(a))
    for mask in range(1, 1 << len(a)):
        low = mask & -mask
        sums[mask] = sums[mask ^ low] + a[low.bit_length() - 1]
    return sums.count(target)


def count_subsets_itertools(a, target):
    return sum(1 for k in range(len(a) + 1) for c in combinations(a, k) if sum(c) == target)


def seconds(fn, *args, repeat=1):
    """Result of fn(*args) and its best time over repeat runs."""
    best = float("inf")
    for _ in range(repeat):
        start = time.perf_counter()
        out = fn(*args)
        best = min(best, time.perf_counter() - start)
    return out, best


SIEVES = (sieve_loop, sieve_list, sieve_bytes, sieve_numpy)
SUBSETS = (count_subsets_recursive, count_subsets_masks, count_subsets_lowbit, count_subsets_itertools)

if __name__ == "__main__":
    # 1. Every version must agree with a brute force before any timing counts.
    def brute(n):
        return [k for k in range(2, n + 1) if all(k % d for d in range(2, isqrt(k) + 1))]
    for n in list(range(0, 60)) + [random.randint(60, 5000) for _ in range(30)]:
        assert all(primes_from(f(n)) == brute(n) for f in SIEVES), n
    for _ in range(50):
        a = [random.randint(-5, 5) for _ in range(random.randint(0, 10))]
        t = random.randint(-6, 6)
        assert len({f(a, t) for f in SUBSETS}) == 1, (a, t)
    print("all versions agree")

    # 2. Sieves, doubling n (sieving only).
    for n in (10**6, 2 * 10**6, 4 * 10**6, 8 * 10**6):
        cells = [f"{f.__name__} {seconds(f, n, repeat=3)[1]:.3f}s" for f in SIEVES]
        print(f"n={n:>9,}  " + "  ".join(cells))

    # 3. Turning flags into a list of primes, n = 10^7.
    n = 10**7
    for f in (sieve_bytes, sieve_numpy):
        flags, t_sieve = seconds(f, n)
        primes, t_list = seconds(primes_from, flags)
        print(f"{f.__name__}: sieve {t_sieve:.3f}s, list of {len(primes):,} primes {t_list:.3f}s")
    print(f"flag memory for n = 10^7: list {sys.getsizeof([True] * (n + 1)) / 1e6:.0f} MB, "
          f"bytearray {sys.getsizeof(bytearray(n + 1)) / 1e6:.0f} MB, numpy {np.ones(n + 1, bool).nbytes / 1e6:.0f} MB")

    # 4. Subsets: each +2 in n means 4x as many subsets.
    for n in (14, 16, 18, 20):
        a = [random.randint(1, 100) for _ in range(n)]
        target = sum(a) // 2
        cells = [f"{f.__name__.removeprefix('count_subsets_')} {seconds(f, a, target)[1]:.3f}s" for f in SUBSETS]
        print(f"n={n}  " + "  ".join(cells))
```

2. Before running it, write down predictions: the time ratio between consecutive sieve rows (n doubles, and n log log n is nearly linear), the order of the four sieves from slowest to fastest, and the time ratio between consecutive subset rows (n grows by 2).
3. Run `python bits_lab.py` and check that the first line reads "all versions agree". No timing counts until it does.
4. Copy the sieve rows into a table and add the ratio between consecutive rows for each version. Compare with your predictions, and explain which version gained most from the slice assignment and which from the smaller element size.
5. Read the extraction lines for n = 10^7. Explain why building the list of primes can cost more than the sieve itself, and why NumPy's `flatnonzero` avoids most of that cost.
6. Read the memory line and explain the 8x gap between the list and the bytearray.
7. Add a pruned version of the recursion: return 0 as soon as `total > target` (valid because the values are positive). Time it against `count_subsets_lowbit` for n = 20, 22 and 24, first with `target = sum(a) // 2`, then with `target = sum(a) // 5`.
8. Stretch: write `sieve_odd`, which stores only odd numbers (index i stands for 2i + 1), check it against `sieve_bytes` with the same brute force, and measure the time and memory it saves.

## What you should see

Measured on a shared Linux server with Python 3.12; your absolute numbers will differ, the ratios are the point.

- The Python inner loop is the slowest sieve by far: about 0.1 to 0.2 s at n = 10^6 and 1.3 to 2 s at 8 × 10^6, roughly doubling with n. List slices are 3 to 6 times faster. The bytearray and NumPy sieves are roughly 10 to 30 times faster than the loop and close to each other, because both cross out each prime's multiples in one C call.
- For n = 10^7 the sieve itself takes well under 0.3 s, but `list(compress(range(n + 1), flags))` takes about 0.6 s: `range` creates a Python int object for each of the 10^7 indices it offers. `np.flatnonzero(flags).tolist()` finds the indices in C and creates only the 664,579 ints it returns, in about 0.1 s.
- Flag memory for n = 10^7: list 80 MB (one 8-byte pointer per slot, all pointing at the shared True and False objects), bytearray 10 MB, NumPy 10 MB.
- Subsets: at n = 20 the O(n·2^n) mask loop takes about 3.5 to 5 s, while recursion, the O(2^n) lowest-bit table and itertools each take about 0.5 s. Each step of +2 in n multiplies the times by about 4.
- Pruning depends on the data. With the target at half the total, the pruned recursion is no faster than the mask table (most branches stay alive). With the target at a fifth of the total it finishes n = 24 in about 0.1 s, while the mask table still needs several seconds, because a mask loop always pays for all 2^n subsets.
- Takeaway: in Python, which loop runs in C matters as much as the complexity class, compact representations (bytes, bits, masks) win on both memory and time, and pruning beats exhaustive enumeration only when many branches die early.

=== primer | How do you count combinations modulo a prime for many queries? | 14 min
goal: Count with the product rule, permutations and binomial coefficients, build Pascal's triangle, and answer C(n, k) mod p in O(1) after precomputing factorials and inverse factorials
tag: bitmath-ncr | Binomial coefficients modulo a prime
link: cp-algorithms: Binomial coefficients | https://cp-algorithms.com/combinatorics/binomial-coefficients.html#binomial-coefficient-modulo-large-prime | 8 min: 'Binomial coefficient modulo large prime' (factorials and inverse factorials), then glance at 'Pascal's Triangle' and 'Binomial coefficient for large n and small modulo' (Lucas's theorem)
link: Python docs: math.comb | https://docs.python.org/3.12/library/math.html#math.comb | 2 min: exact comb(n, k) and perm(n, k) (Python 3.8+); both return 0 when k > n
practice: cses:1079

> [!key]
> C(n, k) counts the k-element subsets of n items: n! / (k! (n - k)!). Python's `math.comb` computes it exactly with big ints. **Modulo a prime p larger than n**, precompute `fact[i]` and `inv_fact[i]` up to the largest n in O(n), with one Fermat inverse at the top and the walk `inv_fact[i - 1] = inv_fact[i] * i` down, and every query becomes two multiplications: `fact[n] * inv_fact[k] * inv_fact[n - k] % p`. Pascal's rule C(n, k) = C(n - 1, k - 1) + C(n - 1, k) needs no division, so it works for any modulus at O(n·k) cost.

## Intuition

How many 5-card hands come from a 52-card deck? Dealing five cards in order gives 52 · 51 · 50 · 49 · 48 sequences, and each hand turns up in 5! = 120 of them, so there are 52 · 51 · 50 · 49 · 48 / 120 = 2,598,960 hands. Dividing out the orderings you do not care about is the heart of C(n, k). Pascal's rule says the same thing recursively: a hand either contains the ace of spades (choose the other 4 from 51) or it does not (choose all 5 from 51).

## How it works

### Counting rules

- **Product rule**: independent choices multiply; 3 shirts and 4 trousers make 12 outfits.
- **Permutations**: ordered selections of k from n, n! / (n - k)!, which is `math.perm(n, k)`.
- **Combinations**: unordered selections, C(n, k) = n! / (k! (n - k)!), which is `math.comb(n, k)`. Symmetry: C(n, k) = C(n, n - k).
- **Stars and bars**: ways to share n identical items among k labelled groups, some possibly empty: C(n + k - 1, k - 1).
- **Grid paths**: right/down paths across an r by c grid choose which r of the r + c moves go down: C(r + c, r).

### Pascal's triangle

Row n holds C(n, 0) to C(n, n), and every inner entry is the sum of the two above it. It needs only addition, so it is exact with big ints and works modulo any m, prime or not. All rows up to n cost O(n²), fine up to a few thousand.

### Factorials and inverse factorials modulo p

For many queries with n up to 10^6, store `fact[i] = i! mod p`. The division by k! (n - k)! becomes multiplication by inverses. Rather than one Fermat power per value, compute `inv_fact[N] = pow(fact[N], p - 2, p)` once and walk down: since 1/(i - 1)! = i · (1/i!), set `inv_fact[i - 1] = inv_fact[i] * i % p`. The build costs O(N + log p) and each query O(1). It needs N < p, so that no factorial is a multiple of p; with p = 10^9 + 7 and N up to 10^6 that holds easily.

### When n reaches p

With a small prime modulus, or n larger than p, every `fact[i]` with i ≥ p is 0, and the table quietly answers 0: with p = 13, the table gives C(14, 1) = 0 instead of 14 mod 13 = 1. Lucas's theorem fixes this by writing n and k in base p and multiplying the binomials of the digits; it is a go-further topic.

## Cost

| Method | Build | Per query | Use when |
|---|---|---|---|
| `math.comb(n, k)` | none | grows with the size of the result | exact answers for moderate n; C(10^6, 5 · 10^5) has 301,027 digits |
| Pascal's triangle | O(n²), or O(n·k) for k columns | O(1) | n up to a few thousand, any modulus |
| factorials and inverse factorials mod p | O(N + log p) | O(1) | many queries, prime p > N |
| multiplicative formula with one inverse | none | O(k + log p) | a few queries with small k, any n |

## When to use it

- "How many ways", "count the arrangements", "number of paths", with the answer modulo a prime: find the formula with the counting rules, then evaluate it with the table.
- Many C(n, k) queries for n up to 10^6 or 10^7: the table.
- A modulus that is not prime (or smaller than n): Pascal's rule, or Lucas's theorem for a small prime.
- Counting that does not factor into a closed formula (constraints between choices): dynamic programming, not a binomial.
- Always check a formula against brute force for n up to 6 or so with `itertools.combinations`, `permutations` or `product` before trusting it.

## Worked trace

Build both tables modulo 13 up to N = 6, then answer C(6, 2).

```steps
Build fact[i] = i! mod 13. The exact factorials grow fast; their remainders stay below 13
    i            0    1    2    3    4    5    6
    i!           1    1    2    6   24  120  720
    fact         1    1    2    6   {{11}}    {{3}}    {{5}}
---
One Fermat inverse for the top entry: inv_fact[6] = 5^(13 - 2) mod 13 = 8, because 5 * 8 = 40 = 3 * 13 + 1
    fact         1    1    2    6   11    3    5
    inv_fact     .    .    .    .    .    .    {{8}}
---
Walk down with inv_fact[i - 1] = inv_fact[i] * i: 8 * 6 = 48 = 9 (mod 13), then 9 * 5 = 45 = 6
    inv_fact     .    .    .    .    {{6}}    {{9}}    8
---
Continue: 6 * 4 = 24 = 11, then 11 * 3 = 33 = 7, then 7 * 2 = 14 = 1, then 1 * 1 = 1
    inv_fact     {{1}}    {{1}}    {{7}}   {{11}}    6    9    8
---
Every pair multiplies to 1 mod 13; for example fact[4] * inv_fact[4] = 11 * 6 = 66 = 5 * 13 + 1
    fact         1    1    2    6   11    3    5
    inv_fact     1    1    7   11    6    9    8
    product      1    1    1    1    {{1}}    1    1
---
Query C(6, 2) = fact[6] * inv_fact[2] * inv_fact[4] = 5 * 7 * 6 = 210, and 210 = 16 * 13 + 2. Exactly, C(6, 2) = 15 and 15 mod 13 = 2
    C(6, 2) mod 13 = {{2}}
```

## Template

```python
def pascal(n: int) -> list[list[int]]:
    """Rows 0..n of Pascal's triangle: C[i][k] = C[i-1][k-1] + C[i-1][k]. Exact, O(n^2)."""
    rows = [[1]]
    for i in range(1, n + 1):
        prev = rows[-1]
        rows.append([1] + [prev[k - 1] + prev[k] for k in range(1, i)] + [1])
    return rows


class Binomial:
    """C(n, k) mod a prime p in O(1) per query after O(n_max) precomputation (needs n_max < p)."""

    def __init__(self, n_max: int, p: int = 10**9 + 7):
        fact = [1] * (n_max + 1)
        for i in range(1, n_max + 1):
            fact[i] = fact[i - 1] * i % p
        inv_fact = [1] * (n_max + 1)
        inv_fact[n_max] = pow(fact[n_max], p - 2, p)       # one Fermat inverse
        for i in range(n_max, 0, -1):                       # 1/(i-1)! = i * 1/i!
            inv_fact[i - 1] = inv_fact[i] * i % p
        self.fact, self.inv_fact, self.p = fact, inv_fact, p

    def comb(self, n: int, k: int) -> int:
        if k < 0 or k > n:
            return 0
        return self.fact[n] * self.inv_fact[k] % self.p * self.inv_fact[n - k] % self.p
```

## Pitfalls

- **A table that reaches p.** Entries silently become 0 (the C(14, 1) example above). Keep n_max below p, or use Lucas's theorem.
- **Missing range check.** Without `k < 0 or k > n`, a negative index wraps around in a Python list and returns a wrong number instead of an error.
- **An inverse per query.** Calling `pow(x, p - 2, p)` three times per query works, but each call squares about 30 times for p = 10^9 + 7, so a query costs over a hundred modular multiplications instead of two; build the table once.
- **`math.comb(n, k) % p` in a loop.** Each call builds the exact number, hundreds of thousands of digits for large n.
- **Ordered or unordered?** Decide whether order matters before choosing C or P, and confirm on tiny cases with itertools.
- **Overflow in C++ and Java.** 21! already exceeds 2^63; reduce every product, and multiply in 64 bits.

## Check yourself

Q: How many right/up paths lead from (0, 0) to (3, 2), and in how many ways can 4 identical balls go into 3 labelled boxes?
A: A path is 5 moves of which 2 go up: C(5, 2) = 10. Stars and bars: C(4 + 3 - 1, 3 - 1) = C(6, 2) = 15.

Q: Why does the backward loop `inv_fact[i - 1] = inv_fact[i] * i` produce inverse factorials?
A: (i - 1)! = i! / i, so 1/(i - 1)! = i · (1/i!). Multiplying the inverse of i! by i therefore gives the inverse of (i - 1)!, all modulo p. One Fermat power for the top entry plus N multiplications fill the whole table.

Q: You need C(10^18, 3) mod 10^9 + 7. The table is impossible (n is huge). What do you do?
A: Use the multiplicative formula: n(n - 1)(n - 2) / 3!, reducing each factor mod p and multiplying by the inverse of 6 (`pow(6, p - 2, p)`). It is valid because 3! has no factor p, so it is invertible, and C(n, 3) · 3! equals the falling product exactly. Cost O(k + log p). In Python `math.comb(10**18, 3) % p` also works instantly, since the exact result has only 54 digits.

## Lab

- **CSES 1079 Binomial Coefficients** (stretch). Precompute up to 10^6 once, read all input at once with `sys.stdin.buffer`, and answer each query in O(1). Expected: (5, 3) gives 10, (8, 1) gives 8, (9, 5) gives 126, and C(10^6, 5 · 10^5) mod 10^9 + 7 is 996692777. Building the table takes around a second in CPython, so the time limit is tight; submit under PyPy if needed.
- **Exercise: check stars and bars by brute force.** Count the triples of non-negative integers with sum 4 using `itertools.product(range(5), repeat=3)`. Expected: 15, which equals C(6, 2); then compare `Binomial(2000).comb(2000, k)` with `pascal(2000)[2000][k] % (10**9 + 7)` for every k (all equal).
- From the problem bank: 1359 Count All Valid Pickup and Delivery Options (the product rule modulo p) and 60 Permutation Sequence (choices of (n - 1)! blocks).

> [!know]
> You now know the counting rules behind C(n, k), when Pascal's triangle is enough, and how to answer many binomial queries modulo a prime in O(1) each after an O(n) build.

=== primer | Why is 0.1 + 0.2 != 0.3, and how do you keep geometry and fractions exact? | 15 min
goal: Explain binary floating-point error, compare floats with tolerances when you must, and keep answers exact with integers, cross products, Fraction, Decimal and math.isqrt
tag: bitmath-exact | Exact arithmetic and cross products
link: Python tutorial: Floating-point arithmetic, issues and limitations | https://docs.python.org/3.12/tutorial/floatingpoint.html#representation-error | 10 min: read from the top of the page through 'Representation Error', which works out exactly which double 0.1 becomes
link: cp-algorithms: Basic geometry | https://cp-algorithms.com/geometry/basic-geometry.html#cross-product | 6 min: 'Cross product': its sign gives the orientation and its magnitude is twice the triangle's area
practice: 149

> [!key]
> A float is a 53-bit binary fraction times a power of two, so most decimals (0.1, 0.2, 0.3) are stored rounded, and the rounding errors leak into comparisons and sums. In algorithms the robust fix is to **stay in integers**: compare a/b with c/d as a·d against c·b, decide orientation with the integer **cross product**, key ratios by gcd-reduced pairs, take square roots with `math.isqrt`, and use `Fraction` or `Decimal` when exact rationals or exact decimal money are required. When floats are unavoidable, compare with `math.isclose` and a tolerance that suits the data.

## Intuition

In decimal you cannot write 1/3 exactly: 0.333... has to stop somewhere. Binary has the same problem with 1/10, which is 0.000110011001100... forever, so the computer keeps the nearest 53-bit value. 0.1 is stored as 0.1000000000000000055511151231257827..., 0.2 and 0.3 as their own nearest neighbours, and the sum of the first two lands on a different neighbour from the third. Integers below 2^53 have no such problem: they are stored exactly and add exactly.

## How it works

### IEEE 754 doubles

A Python float is a C double: a sign bit, 11 exponent bits and 52 stored fraction bits (53 significant bits with the implicit leading 1). That gives 15 to 17 significant decimal digits, exact integers up to 2^53 = 9,007,199,254,740,992, and every operation rounds its exact result to the nearest representable value. Consequences: `float(2**53 + 1) == float(2**53)`, `1e16 + 1 - 1e16 == 0.0`, and `int(math.sqrt(n))` goes wrong well before that: for n = 94906265² - 1, about 9 × 10^15, it returns 94906265 instead of 94906264.

### Stay in integers

- **Ratios**: compare a/b < c/d as a·d < c·b (with b, d > 0); key equal ratios by gcd-reduced pairs (gcd card).
- **Square roots**: `math.isqrt(n)` is the exact floor square root of any int; test for a perfect square with `isqrt(n) ** 2 == n`.
- **Money**: integer cents, or `decimal.Decimal("0.10")` built from a string (`Decimal(0.1)` copies the float's error).
- **Rationals**: `Fraction(1, 10) + Fraction(2, 10) == Fraction(3, 10)` is exact; every operation reduces by a gcd, so it is slower and the numbers can grow.

### Geometry with the cross product

For points O, A and B, the cross product of OA and OB is `(A.x - O.x)(B.y - O.y) - (A.y - O.y)(B.x - O.x)`. Positive means the path O, A, B turns counter-clockwise (left), negative means clockwise (right), and zero means the three points are collinear. Its absolute value is twice the area of the triangle OAB. With integer coordinates every one of these answers is exact: no slopes, no division and no special case for vertical lines. Summing cross products around a polygon gives twice its signed area (the shoelace formula). Orientation tests are the building block of convex hulls, segment intersection and point-in-polygon tests.

```text
                B           cross(O, A, B) > 0: B is to the left of O -> A

    O ----------------> A

                B'          cross(O, A, B') < 0: B' is to the right
```

### When floats are unavoidable

Compare with `math.isclose(a, b, rel_tol=1e-9, abs_tol=...)`. The relative tolerance scales with the magnitude, and the absolute floor matters near zero, where a purely relative test always fails (`math.isclose(1e-15, 0)` is False). Sum many floats with `math.fsum`, which is correctly rounded. Since Python 3.12 the built-in `sum()` of floats is also compensated, so `sum([0.1] * 10) == 1.0`, but a `+=` loop still drifts to 0.9999999999999999.

## Cost

Integer arithmetic on word-sized values is O(1). With coordinates up to 10^9 in absolute value, each difference is below 2 × 10^9 and the cross product below 8 × 10^18, inside a signed 64-bit integer (`long long` in C++), while Python never overflows at all, at the price of slower big-int arithmetic if numbers grow. A Fraction operation costs a gcd, logarithmic in the size of the numbers, and long chains of fractions can grow their denominators. Decimal runs in C (libmpdec) and is slower than float but fine for money.

## When to use it

| Situation | Do this |
|---|---|
| slopes, directions, collinearity | cross product, or gcd-reduced (dx, dy) keys |
| comparing fractions | cross-multiply the integers |
| perfect squares, square-root bounds | `math.isqrt` |
| money, decimal output with exact rounding rules | integer cents or `Decimal` built from strings |
| exact rational answers on small inputs | `Fraction` |
| physics, statistics, measurements that are genuinely real numbers | floats with `math.isclose` and a justified tolerance |
| output accepted "within 10^-6 of the answer" | floats are fine; exactness is not required |

## Worked trace

First watch error build up in a float sum, then see the same kind of rounding fool a geometry test that the cross product gets right.

```steps
Add 0.1 three times with s += 0.1: the third sum is not the double nearest 0.3
    s = 0.1  ->  0.2  ->  {{0.30000000000000004}}
---
Keep going: some errors cancel and then they pile up, so after ten additions s is not 1.0
    s = 0.4, 0.5, 0.6, 0.7, {{0.7999999999999999}},
        0.8999999999999999, {{0.9999999999999999}}
---
Geometry: are O = (0, 0), A = (94911151, 94911150) and B = (94911152, 94911151) on one line? Compare float slopes
    slope OA = 94911150 / 94911151 = {{0.9999999894638303}}
    slope OB = 94911151 / 94911152 = {{0.9999999894638303}}   equal as doubles
---
The true slopes differ by about 1.1 * 10^-16, one step of a double near 1, so both round to the same float and the test says "collinear". Use the cross product instead
    cross = (Ax - Ox)(By - Oy) - (Ay - Oy)(Bx - Ox)
          = 94911151 * 94911151 - 94911150 * 94911152
---
In exact integers this is n^2 - (n - 1)(n + 1) = 1 for n = 94911151: not zero, so the points are not collinear, and B is a left turn from OA
    cross = {{1}}  > 0: counter-clockwise, not collinear
```

## Template

```python
import math


def cross(o, a, b) -> int:
    """Cross product of the vectors o->a and o->b.
    > 0: o, a, b turn counter-clockwise (left); < 0: clockwise (right); 0: collinear."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def twice_area(poly) -> int:
    """Twice the signed area of a simple polygon (shoelace formula); exact for integer points,
    positive when the vertices run counter-clockwise."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))


def nearly_equal(a: float, b: float) -> bool:
    """Float comparison with a relative tolerance and an absolute floor for values near zero."""
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
```

## Pitfalls

- **`==` on computed floats.** Use a tolerance, or better, avoid the floats.
- **A purely relative tolerance near zero.** `math.isclose(x, 0.0)` is True only when x is exactly 0; pass `abs_tol`.
- **Float dictionary keys.** Slopes as keys collide when nearly equal (the trace) and fail on vertical lines (division by zero).
- **Building exact types from floats.** `Fraction(0.1)` is 3602879701896397/36028797018963968 and `Decimal(0.1)` has 55 digits; build them from strings or integer pairs.
- **Rounding surprises.** `round(2.675, 2) == 2.67`, because 2.675 is stored just below, and `round(2.5) == 2`, because Python rounds halves to even.
- **`int(math.sqrt(n))` for large n.** It can be off by one; use `math.isqrt`.

## Check yourself

Q: Predict: `0.1 * 3 == 0.3`, `1 - 0.9`, `Fraction(1, 3) * 3 == 1` and `math.isqrt(10**30 + 1)`.
A: False (the product is 0.30000000000000004); 0.09999999999999998; True, because Fraction arithmetic is exact; and exactly 10**15, because isqrt works on the integer itself with no float involved.

Q: Why does the sign of the cross product say which way the path turns, and why is it exact for integer points?
A: The cross product of OA and OB equals |OA| · |OB| · sin θ, where θ is the counter-clockwise angle from OA to OB. sin θ is positive for a left turn, negative for a right turn and zero when the vectors are parallel. The formula uses only subtraction and multiplication of coordinates, so with integers every step is exact; there is no division and no square root.

Q: To check whether all points lie on one line, a colleague compares the slopes `(y - y0) / (x - x0)` to the first point. Give two ways it fails and the fix.
A: A vertical line divides by zero, and large coordinates can make different slopes round to the same float (the trace) or equal slopes computed from different points round differently. Fix: check `cross(p0, p1, p) == 0` for every point p, all in integers, O(n).

Q: A payment service adds up a million amounts such as 19.99. Float, Decimal or int?
A: Integer cents, or Decimal built from the original strings. Floats accumulate representation error, while money needs exact sums and explicit, auditable rounding rules, which Decimal's rounding modes provide.

## Lab

- **149 Max Points on a Line.** Solve it with gcd-reduced direction keys, then write an O(n^3) brute force that counts, for every pair, the points with `cross == 0`, and stress-test the two against each other on random points in a small grid. Expected: [(1, 1), (2, 2), (3, 3), (5, 1), (4, 0)] gives 3, and [(0, 0), (94911151, 94911150), (94911152, 94911151)] gives 2, while a float-slope version returns 3.
- **Exercise: signed area.** Compute `twice_area` for [(0, 0), (4, 0), (4, 3), (0, 3)] and for the same points in reverse order. Expected: 24 and -24 (area 12; the sign gives the orientation).
- From the problem bank: 1232 Check If It Is a Straight Line (one cross product per point) and 587 Erect the Fence (a convex hull built from orientation tests).

> [!know]
> You now know why binary floats misbehave, how to keep comparisons, geometry and fractions exact with integers, and how to compare floats safely when you have no choice.

=== practice
- 136 core
  cue: Every value appears exactly twice except one, and extra memory must be O(1).
  hint: Look for an operation under which a value combined with itself disappears and the order of combining does not matter.
  insight: Fold the array with XOR starting from 0. x ^ x = 0, x ^ 0 = x, and XOR is commutative and associative, so every pair cancels wherever its two copies sit and only the single value is left.
  cost: O(n) time, O(1) space
  pattern: bitmath-xor
- 338 core
  cue: You need the number of 1 bits of every integer from 0 to n, faster than counting each one separately.
  hint: Every i is some smaller number with one bit added back. Which smaller number's answer do you already have?
  insight: Dropping the lowest set bit gives a smaller index, so bits[i] = bits[i & (i - 1)] + 1 (or, shifting off the last bit, bits[i >> 1] + (i & 1)). Fill the table from left to right.
  cost: O(n) time, O(n) for the output
  pattern: bitmath-masks
- 1071 derive
  cue: The answer is the longest string that, repeated, builds both inputs.
  hint: If both strings are made of the same unit, does the order in which you glue them together matter? And which lengths can a unit dividing both strings have?
  insight: A common unit exists exactly when s + t == t + s (both are repetitions of one word). Then the longest unit is the prefix of length gcd(len(s), len(t)): any unit length divides both lengths, and the gcd-length prefix repeats correctly because both strings are powers of the same word.
  cost: O(m + n) time, O(m + n) space
  pattern: bitmath-gcd
- 371 core
  cue: Add two integers without using + or -.
  hint: Split addition into the sum without carries and the carries themselves. Which bit operations compute each? What stops Python's unbounded ints from looping forever on negative inputs?
  insight: a ^ b adds without carries and (a & b) << 1 is the carry; repeat until the carry is 0. Mask both with 0xFFFFFFFF every round so the carry falls off after 32 bits, then convert back to signed (subtract 2^32 when bit 31 is set).
  cost: O(32) rounds, O(1) space
  pattern: bitmath-twos
- 260 core
  cue: Exactly two values appear once and every other value twice, with O(1) extra space.
  hint: XOR everything and you get a ^ b. What does any set bit of that value tell you about a and b?
  insight: Any set bit of d = a ^ b is a position where a and b differ. Take low = d & -d and XOR separately the numbers that have that bit and those that do not: duplicates stay together and cancel, so one group gives a and d ^ a gives b.
  cost: O(n) time, O(1) space
  pattern: bitmath-xor
- 137 derive
  cue: Every value appears three times except one, with O(1) extra space, and values may be negative.
  hint: XOR cancels pairs, not triples. Look at one bit position: what is the number of ones there, modulo 3?
  insight: For each of the 32 bit positions, count the numbers with that bit set; the count modulo 3 is the single number's bit. Assemble the bits and read bit 31 as the sign (subtract 2^32 if it is set). The two-mask version (ones, twos) does the same counting for all positions at once.
  cost: O(32 n) time, O(1) space
  pattern: bitmath-masks
- 2044 core
  cue: At most 16 numbers, and the question ranges over every non-empty subset.
  hint: Which OR value is the largest any subset can reach? Then count the subsets that reach it without recomputing every OR from scratch.
  insight: OR never decreases as elements are added, so the maximum is the OR of all numbers. Loop over masks 1 to 2^n - 1 with or_of[mask] = or_of[mask ^ low] | nums[index of low], where low = mask & -mask, and count the masks equal to the maximum.
  cost: O(2^n) time and space (O(n 2^n) if each OR is recomputed)
  pattern: bitmath-subsets
- 204 core
  cue: Count every prime below n, with n up to 5 * 10^6.
  hint: Testing each number separately repeats work. What if every prime marked the numbers it rules out?
  insight: Sieve of Eratosthenes: for each p up to the square root that is still marked prime, cross out p*p, p*p + p, and so on (smaller multiples were crossed out by smaller primes). In Python use a bytearray with one slice assignment per prime, then count the survivors below n.
  cost: O(n log log n) time, O(n) bytes
  pattern: bitmath-sieve
- 50 core
  cue: Raise x to an integer power n, with n anywhere in the 32-bit range and a float answer.
  hint: x^n = (x^(n/2))^2 when n is even. How many squarings is that, and what does a negative n turn into?
  insight: Square and multiply over the bits of |n|: multiply the result by the current base when the bit is 1 and square the base every round. For n < 0 use 1/x and -n; in Java or C++ widen n to 64 bits first, because -(-2^31) overflows.
  cost: O(log |n|) time, O(1) space
  pattern: bitmath-modpow
- 149 core
  cue: Points with integer coordinates; find the largest number of them on one straight line.
  hint: Fix one point: every line through it is a direction. How can two directions compare equal exactly, without floating-point slopes?
  insight: For each anchor i, reduce (dx, dy) to every later point by their gcd with a fixed sign (dx > 0, or dx == 0 and dy > 0), count the keys with a Counter, and take the largest count plus one. Float slopes break on vertical lines and on nearly equal steep slopes.
  cost: O(n^2 log C) time for coordinates up to C, O(n) space
  pattern: bitmath-gcd
- cses:1079 stretch
  cue: Up to 10^5 queries of C(a, b) modulo 10^9 + 7, with a up to 10^6.
  hint: Division is the obstacle. What can you precompute once so that each query is a couple of multiplications?
  insight: Precompute fact[i] = i! mod p, then inv_fact[N] = fact[N]^(p - 2) mod p by Fermat and inv_fact[i - 1] = inv_fact[i] * i walking down. Each query is fact[a] * inv_fact[b] * inv_fact[a - b] mod p. In Python read all input at once.
  cost: O(N + q) time plus O(log p) for the one inverse, O(N) space
  pattern: bitmath-ncr
- 1178 stretch
  cue: Many words and many 7-letter puzzles; a word counts for a puzzle if it contains the puzzle's first letter and uses only the puzzle's letters.
  hint: Only the set of letters in a word matters. How many different letter sets can one 7-letter puzzle accept?
  insight: Count words by their 26-bit letter mask in a dict. For each puzzle, enumerate the 2^6 = 64 submasks of its other six letters with s = (s - 1) & rest, add the first letter's bit, and sum the counts of those masks.
  cost: O(total word length + 64 * puzzles) time, O(distinct word masks) space
  pattern: bitmath-subsets
