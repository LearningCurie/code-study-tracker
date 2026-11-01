---
key: arrays
name: Arrays, dynamic arrays, strings and grids
stage: contain
summary: What a Python list really is in memory and why append is amortised O(1), plus the in-place, own-index, string and grid moves that most array problems reduce to.
why: Arrays are the default container in every language and the backing store of most other structures: heaps, hash tables, ring buffers, matrices, column stores, image buffers. Knowing that a Python list is a block of references with spare capacity tells you what `append`, `insert(0, x)`, slicing and `x in a` really cost before you run anything. The in-place moves (two indices and an invariant) are the seed of two pointers, partitioning and sliding windows later on; values-as-indices turns O(n) memory into O(1); and row-major arithmetic turns every board, image and map into plain index calculations.
outcomes:
- Explain what a CPython list stores, estimate its memory, and predict when append reallocates
- Prove that geometric growth makes append amortised O(1) and that additive growth makes it quadratic
- Reverse, rotate and compact an array in place, stating the invariant that makes each pass correct
- Use values in 1..n as indices (sign marking, cyclic sort) to find missing and duplicate numbers in O(1) extra space
- Build and count strings in linear time and know where Unicode breaks the one-character-per-index picture
- Index, traverse and transform grids: row-major arithmetic, neighbours, spiral and diagonal orders, in-place rotation and two-state cells
cues:
- Values lie in 1..n for an array of length n, and extra memory is forbidden or limited to O(1)
- "In place", "O(1) extra space", or the output must overwrite the input
- A grid, board, image or matrix, with moves between neighbouring cells or traversal in a fixed order
- Rotate, reverse, transpose, spiral, diagonal or "next arrangement" in the statement
- Millions of numbers in a list, or repeated insertions and removals at the front
traps:
- `[[0] * m] * n` creates n references to one row, so writing one cell changes every row
- `insert(0, x)`, `pop(0)` and slicing inside loops quietly make code quadratic
- Negative indices wrap around, so an off-grid neighbour at -1 reads the last row or column instead of failing
- The tuple swap `a[i], a[a[i] - 1] = a[a[i] - 1], a[i]` assigns left to right and corrupts cyclic sort
- Rebinding a parameter (`a = a[::-1]`) when the caller expects the list itself to change
systems:
- CPython's `list` over-allocates by about one eighth plus a constant (`list_resize` in Objects/listobject.c); Go slices double up to 256 elements and then grow towards 1.25x (`nextslicecap` in runtime/slice.go)
- Apache Arrow and other columnar formats keep each column in one contiguous buffer plus a validity bitmap, so scans and SIMD kernels read memory sequentially
- NumPy arrays are one block of raw values plus a shape and strides; a transpose or a basic slice is a view that only changes the strides, not a copy
- Images and video frames are row-major pixel buffers: pixel (x, y) sits at byte `y * row_stride + x * bytes_per_pixel`
further:
- Docs · 10 min | Python docs: time complexity of built-in types, the list table and its notes | https://docs.python.org/3/builtins/time-complexity.html#list
- Notes · 20 min | MIT 6.006 recitation 2: sequence implementations (array, linked list, dynamic array) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/c08a3b63dfe5f6f6b32257d35f86ae63_MIT6_006S20_r02.pdf
- Docs · 15 min | NumPy: internal memory layout of an ndarray (strides, C and Fortran order) | https://numpy.org/doc/stable/reference/arrays.ndarray.html#internal-memory-layout-of-an-ndarray
- Docs · 15 min | Apache Arrow: columnar format, physical memory layout | https://arrow.apache.org/docs/format/Columnar.html#physical-memory-layout
bank: matrix
---

=== recap | Python lists: references, capacity and amortised append | 12 min
goal: Predict a list's memory and when append reallocates, and prove that n appends cost O(n) in total
link: Python FAQ: how are lists implemented in CPython? | https://docs.python.org/3/faq/design.html#how-are-lists-implemented-in-cpython | 2 min, the whole short answer: a contiguous array of references with spare room for appends
link: CPython source: list_resize in Objects/listobject.c | https://github.com/python/cpython/blob/main/Objects/listobject.c | 5 min: search the page for 'This over-allocates proportional' and read that comment and the two lines of code after it

> [!key]
> A Python `list` is a **dynamic array of references**: one contiguous block of 8-byte pointers to separately allocated objects, plus a length and a larger **capacity**. Indexing is address arithmetic, so O(1). Appending is **amortised O(1)**: when the block is full, CPython reallocates it about one eighth larger, and the occasional O(n) move is paid for by the cheap appends before it.

## Internals

```text
PyListObject                    ob_item: one contiguous block of pointers
+---------------+              +------+------+------+------+
| ob_size   = 3 |              |  *   |  *   |  *   | free |   capacity 4
| allocated = 4 |              +--|---+--|---+--|---+------+
| ob_item   = *-+------------->     |      |      |
+---------------+                   v      v      v
                                 int 7  float 3.5  str "hi"   (separate objects)
```

- **Memory.** On 64-bit CPython 3.12, `sys.getsizeof([])` is 56 bytes and every slot of capacity adds 8. The elements are separate objects: an `int` is 28 bytes (ints from -5 to 256 are cached and shared), a `float` 24. A list of a million distinct floats therefore takes about 32 MB, while `array('d')` or a NumPy `float64` array stores the raw values contiguously in 8 MB, and NumPy loops over them in C.
- **Growth rule.** When an append needs more room, `list_resize` computes `new_allocated = (newsize + (newsize >> 3) + 6) & ~3`: one eighth extra plus a constant, rounded down to a multiple of 4. Appending one item at a time gives capacities 0, 4, 8, 16, 24, 32, 40, 52, 64, 76, 92, ... The list shrinks only when its size falls below half its capacity. `[0] * n`, `list(range(n))` and `extend` size the block exactly.
- **Why amortised O(1).** With growth factor r > 1, the moves at successive resizes form a geometric series whose largest term is below n, so n appends move fewer than n · r / (r - 1) references: under 2n for doubling, about 9n for CPython's 1.125. Growing by a constant k instead moves about n² / (2k): quadratic. (`realloc` may extend the block in place, so these are upper bounds.)

| Operation | Cost | Why |
|---|---|---|
| `a[i]`, `a[i] = x`, `len(a)` | O(1) | address arithmetic |
| `append(x)`, `pop()` | O(1) amortised | work at the end of the block |
| `insert(i, x)`, `pop(i)`, `del a[i]` | O(n - i) | every later pointer shifts |
| `x in a`, `a.index(x)`, `a.count(x)` | O(n) | linear scan with `==` |
| `a[i:j]`, `a.copy()`, `a + b` | O(size of result) | new block, references copied |

C++ `std::vector` and Rust `Vec` are the same structure but store values inline, without boxing; `reserve(n)` pre-sizes them.

## Template

```python
class DynArray:
    """Dynamic array: size <= capacity; grow geometrically when full, shrink when a quarter full."""

    def __init__(self, grow=lambda cap: max(4, 2 * cap)):
        self._grow = grow
        self._cap = self._n = 0
        self._slots = []          # fixed block: never append to it
        self.moves = 0            # element copies done by resizes

    def __len__(self):
        return self._n

    def __getitem__(self, i):
        if not 0 <= i < self._n:
            raise IndexError(i)
        return self._slots[i]

    def append(self, x):
        if self._n == self._cap:
            self._resize(self._grow(self._cap))
        self._slots[self._n] = x
        self._n += 1

    def pop(self):
        if self._n == 0:
            raise IndexError("pop from empty array")
        self._n -= 1
        x, self._slots[self._n] = self._slots[self._n], None
        if self._cap > 4 and self._n <= self._cap // 4:
            self._resize(self._cap // 2)
        return x

    def _resize(self, cap):
        new = [None] * cap
        for i in range(self._n):
            new[i] = self._slots[i]
        self.moves += self._n
        self._slots, self._cap = new, cap
```

## Worked example

CPython's own growth over the first 17 appends:

```steps
Empty list: no block allocated yet
    size 0   capacity 0   moved so far 0
    []
---
Append 1: size 1 exceeds capacity 0, so allocate (1 + 0 + 6) & ~3 = 4 slots
    size 1   capacity {{4}}   moved so far 0
    [a _ _ _]
---
Appends 2 to 4 fit in the spare slots: O(1) each, no allocation
    size {{4}}   capacity 4   moved so far 0
    [a b c d]
---
Append 5: full, so grow to (5 + 0 + 6) & ~3 = 8; realloc may move the 4 pointers
    size 5   capacity {{8}}   moved so far {{4}}
    [a b c d e _ _ _]
---
Append 9: full again, grow to (9 + 1 + 6) & ~3 = 16, moving up to 8 pointers
    size 9   capacity {{16}}   moved so far {{12}}
    [a b c d e f g h i _ _ _ _ _ _ _]
---
Append 17: grow to (17 + 2 + 6) & ~3 = 24, moving up to 16
    size 17   capacity {{24}}   moved so far {{28}}
    28 moves for 17 appends; the ratio stays bounded (below about 9) however long the list gets
```

## Pitfalls

- `b = a` copies nothing: both names refer to one list. `a[:]`, `list(a)` and `a.copy()` are **shallow** copies (new block, same element objects); `copy.deepcopy` also copies nested lists.
- Passing `a[1:]` down a recursion copies n - 1 references per call and turns O(n) into O(n²). Pass indices instead.
- Amortised is not "every time": one append can take O(n). For latency-sensitive code, pre-size (`[None] * n` in Python, `reserve` in C++).
- `insert(0, x)` or `pop(0)` inside a loop is quadratic; a queue needs `collections.deque`.

## Quick check

Q: Starting from `[]`, how many reallocations happen during 20 appends, and what is the final capacity?
A: Four, triggered by appends 1, 5, 9 and 17, giving capacities 4, 8, 16 and 24. The final capacity is 24, which `(sys.getsizeof(a) - 56) // 8` confirms on 64-bit CPython 3.12.

Q: An array grows by 1,000 slots each time it fills. Roughly how many element moves does building 10^6 elements cost, and how does doubling compare?
A: About n² / (2k) = 10^12 / 2,000 = 5 × 10^8 moves (1,000 resizes copying 1,000, 2,000, ... elements). Doubling moves fewer than 2 × 10^6 in total, so the additive scheme is about 250 times more work and gets worse as n grows.

> [!know]
> You now know what a list stores, how CPython grows it, and why append is O(1) amortised but not O(1) every time.

=== recap | In place: reverse, rotate and compact | 10 min
goal: Rewrite an array in O(1) extra space with two indices and an invariant: reverse a range, rotate by three reversals, compact with a write index
tag: arrays-inplace | In-place reverse, rotate and compact
practice: 31, 238
link: Wikipedia: Permutation, generation in lexicographic order | https://en.wikipedia.org/wiki/Permutation#Generation_in_lexicographic_order | 3 min: the four-step algorithm for the next permutation and why the suffix is reversed

> [!key]
> In place means you mutate the given list and use O(1) extra space besides it. Three moves cover most problems: **swap from both ends** to reverse a range, compose **three reversals** to rotate, and keep a **write index** `w` with the invariant "a[:w] is the finished output" to filter or compact in a single pass.

## Internals

- **Reverse** a[lo:hi]: swap the two ends and move both inwards. Invariant: everything outside the shrinking window is already in its final position. That is n / 2 swaps.
- **Rotate right by k** means the last k elements move to the front. Write the list as A B with B of length k. Reversing everything gives rev(B) rev(A); reversing each part again gives B A. Three passes, about n swaps, no buffer. Reduce k modulo n first.
- **Compact** (filter in place): a read index r visits every element and a write index w ≤ r marks the end of the output. Invariant: a[:w] holds, in order, the kept elements of a[:r]. Finish with `del a[w:]`, or return w if the array has a fixed size.
- **Next permutation** reuses reversal. Find the rightmost i with a[i] < a[i + 1]: the suffix after i is non-increasing, so it is already the largest arrangement of its values. Swap a[i] with the rightmost suffix element larger than it (the suffix stays non-increasing), then reverse the suffix to make it as small as possible. If no such i exists, the array is the last permutation: reverse all of it.
- **The output as workspace.** When the answer is itself an array, it does not count as extra space. Fill it left to right with one fact (say, a running product of everything to the left), then sweep right to left with one running variable for the other side.
- **What Python gives you.** `a.reverse()` runs in C, in place. `a[::-1]` builds a new list; `reversed(a)` is a lazy iterator. `a[:] = expr` replaces the contents of the same list object, so callers holding a reference see the change, but it builds the right-hand side first (O(n) extra space).

## Template

```python
def reverse(a, lo=0, hi=None):
    """Reverse a[lo:hi] in place."""
    if hi is None:
        hi = len(a)
    hi -= 1
    while lo < hi:
        a[lo], a[hi] = a[hi], a[lo]
        lo, hi = lo + 1, hi - 1


def rotate_right(a, k):
    """Move the last k elements to the front with O(1) extra space."""
    n = len(a)
    if n:
        k %= n
        reverse(a)
        reverse(a, 0, k)
        reverse(a, k, n)


def compact(a, keep):
    """Keep the elements x with keep(x) true, in order, in place; return the new length."""
    w = 0
    for r in range(len(a)):
        if keep(a[r]):
            a[w] = a[r]
            w += 1
    del a[w:]
    return w
```

## Worked example

```steps
Rotate right by k = 3: the result must be 5 6 7 followed by 1 2 3 4
    index  0  1  2  3  4  5  6
    a      1  2  3  4  5  6  7
---
Reverse everything: rev(A B) = rev(B) rev(A)
    index  0  1  2  3  4  5  6
    a      {{7  6  5  4  3  2  1}}
---
Reverse the first k = 3 elements: rev(rev(B)) = B
    index  0  1  2  3  4  5  6
    a      {{5  6  7}}  4  3  2  1
---
Reverse the last n - k = 4 elements: rev(rev(A)) = A; done with about n swaps and no buffer
    index  0  1  2  3  4  5  6
    a      5  6  7  {{1  2  3  4}}
```

Next permutation of [1, 3, 5, 4, 2]: the rightmost ascent is at i = 1 (3 < 5); the rightmost suffix value larger than 3 is 4, so swapping gives [1, 4, 5, 3, 2]; reversing the suffix [5, 3, 2] gives [1, 4, 2, 3, 5].

## Pitfalls

- `a = a[::-1]` inside a function rebinds the local name and the caller's list is unchanged. Mutate with `a.reverse()` or `a[:] = ...`.
- Rotating with k ≥ n, or an empty list: reduce with `k %= n` and guard `n == 0` (`k % 0` raises).
- Removing while iterating (`for x in a: if bad(x): a.remove(x)`) skips the element after each removal and costs O(n²). Compact instead.
- In next permutation the swap partner must be the rightmost larger value; any other choice can leave the suffix out of order, and the final reverse no longer yields the smallest suffix.

## Quick check

Q: What are the next permutations of [2, 3, 1] and of [3, 2, 1]?
A: [3, 1, 2]: the rightmost ascent is at i = 0 (2 < 3); the rightmost suffix value larger than 2 is 3, so swapping gives [3, 2, 1], and reversing the suffix [2, 1] gives [3, 1, 2]. [3, 2, 1] has no ascent, so it is the last permutation and wraps to [1, 2, 3].

> [!know]
> You now know how to reverse, rotate and compact an array in place, and the invariant that proves each pass correct.

=== recap | The array as its own index | 10 min
goal: Use values in 1..n as positions (sign marking, cyclic sort) to find missing and duplicate numbers in O(n) time and O(1) extra space
tag: arrays-ownindex | Array as its own index
practice: 448, 645, 41
link: Tech Interview Handbook: array techniques | https://www.techinterviewhandbook.org/algorithms/array/#techniques | 3 min: the 'Index as a hash key' paragraph, the same idea in one paragraph

> [!key]
> When n values all lie in 1..n, the array already has one slot per possible value: slot v - 1 can record a fact about v. **Sign marking** negates a[v - 1] to say "v was seen" (abs recovers the value); **cyclic sort** swaps every v into slot v - 1. Either finds missing and repeated values in O(n) time and O(1) extra space, where a set would need O(n) memory.

## Internals

- **Why it works.** A seen-set over 1..n is a boolean array of n entries. When the input is an array of length n with values in 1..n, its own sign bits (or its own positions) can play that boolean array, so the extra memory disappears. You give up the original order or must restore the signs afterwards.
- **Sign marking.** For each x, look at slot `abs(x) - 1`: if it is already negative, x is a repeat; otherwise negate it. Afterwards, every slot i that is still positive means i + 1 never appeared.
- **Cyclic sort.** For each i, while a[i] holds a value v in range whose home slot v - 1 does not already hold v, swap it home. Invariant: a value sitting in its home slot never moves again. Every swap puts one value home for good, so there are at most n swaps in total and the nested loop is O(n) overall, an amortised argument. Afterwards a[i] == i + 1 for every value that occurs; the slots that disagree hold the repeats and mark the missing values.
- **Out-of-range values** (zero, negatives, values above n) have no home slot; they stay wherever the swaps leave them. When the answer can be outside the input (the smallest value not present, say), first ask which range the answer must lie in.
- **Alternatives.** A set: O(n) time and O(n) memory, and it does not mutate the input. Sorting: O(n log n). For exactly one missing number, a sum or XOR identity works without touching the array (the bits module covers XOR tricks).

## Template

```python
def marks(a):
    """Values in 1..n. Return (repeats, missing) with sign marks, then restore a."""
    repeats = []
    for x in a:
        i = abs(x) - 1
        if a[i] < 0:
            repeats.append(i + 1)      # a value seen k times is reported k - 1 times
        else:
            a[i] = -a[i]
    missing = [i + 1 for i, x in enumerate(a) if x > 0]
    for i in range(len(a)):
        a[i] = abs(a[i])
    return repeats, missing


def cyclic_sort(a):
    """Move every value v in 1..n to index v - 1; out-of-range values stay where they land."""
    n = len(a)
    for i in range(n):
        while 1 <= a[i] <= n and a[a[i] - 1] != a[i]:
            j = a[i] - 1               # compute the target first (see Pitfalls)
            a[i], a[j] = a[j], a[i]
```

## Worked example

```steps
Cyclic sort of [2, 5, 1, 2, 4] (n = 5). i = 0: value 2 belongs at index 1, which holds 5, so swap
    index  0  1  2  3  4
    a      {{2  5}}  1  2  4
---
Still i = 0: value 5 belongs at index 4, which holds 4, so swap
    a      {{5}}  2  1  2  {{4}}
---
Still i = 0: value 4 belongs at index 3, which holds 2, so swap
    a      {{4}}  2  1  {{2}}  5
---
Still i = 0: value 2 belongs at index 1, which already holds 2: a repeat, stop. i = 1 is home
    a      {{2  2}}  1  4  5
---
i = 2: value 1 belongs at index 0, which holds 2, so swap
    a      {{2}}  2  {{1}}  4  5
---
Still i = 2: the 2 that arrived belongs at index 1, which already holds 2, so stop; i = 3 and i = 4 are home
    a      1  2  {{2}}  4  5
---
Final scan: index 2 should hold 3 but holds 2, so 3 is missing and 2 is repeated (4 swaps in all, never more than n)
    index  0  1  2  3  4
    a      1  2  {{2}}  4  5
```

## Pitfalls

- **The tuple-swap trap.** `a[i], a[a[i] - 1] = a[a[i] - 1], a[i]` evaluates the right side first, then assigns targets left to right, so the second target index uses the *new* a[i]. On [2, 1] it leaves the list unchanged and the while loop never ends. Compute `j` first.
- Testing `j != i` instead of `a[j] != a[i]` loops forever on duplicates: two equal values keep swapping.
- After sign marking, read values with `abs()`; a slot may already be negative when you reach it.
- Zero cannot carry a sign mark. Shift values or treat out-of-range values separately.
- These methods mutate the input. Restore it (as `marks` does) or say so in the contract.

## Quick check

Q: Run `marks` on [3, 1, 3, 4, 1] (n = 5). What does it return?
A: ([3, 1], [2, 5]). The marks go to slots 2, 0, then 3 is a repeat, slot 3, then 1 is a repeat; slots 1 and 4 stay positive, so 2 and 5 are missing.

> [!know]
> You now know how to make an array's own slots record what has been seen, and why cyclic sort is O(n) despite its nested loop.

=== recap | Strings as character arrays | 10 min
goal: Build and count text in linear time with list-and-join and 26-slot counts, and know where Unicode breaks the one-character-per-index picture
tag: arrays-strings | Strings as character arrays
practice: 1980
link: Python FAQ: concatenating many strings efficiently | https://docs.python.org/3/faq/programming.html#what-is-the-most-efficient-way-to-concatenate-many-strings-together | 2 min: why repeated concatenation is quadratic in general, and the join and io.StringIO idioms
link: Python Unicode HOWTO: definitions | https://docs.python.org/3/howto/unicode.html#definitions | 5 min: code points versus encodings, so that len() and comparisons behave as you expect

> [!key]
> A Python `str` is an **immutable array of Unicode code points**: `s[i]` and `len(s)` are O(1), but every change builds a new string. Edit text as a list and `"".join` it once; count lowercase letters in a 26-slot list indexed by `ord(ch) - ord("a")`; and remember that `len` counts code points, not the characters a reader sees.

## Internals

- **Storage (PEP 393).** CPython stores each string with 1, 2 or 4 bytes per code point, chosen by its widest character, so indexing stays O(1). On 3.12, `sys.getsizeof` reports 41 bytes for `""`, 141 for 100 ASCII letters, 258 for 100 euro signs and 460 for 100 emoji.
- **Immutability.** `s[i] = "x"` raises `TypeError`. `s += t` must produce a new string, and in general n concatenations copy 1 + 2 + ... + n characters: O(n²). CPython hides this when nothing else references `s` (it resizes in place), but any second reference, another interpreter, or a loop that keeps old strings brings the quadratic cost back. `"".join(parts)` sums the lengths, allocates once and copies once.
- **Slices copy**: `s[i:j]` is O(j - i), and `s[::-1]` is O(n). Methods such as `replace`, `strip` and `lower` return new strings.
- **The hash is cached.** A string computes its hash once and stores it, so repeated dictionary lookups with the same string object do not rehash it.
- **Counting.** For lowercase English letters, `[0] * 26` with `ord(ch) - 97` is a direct-address table: no hashing, and comparing two tables is O(26). Use `collections.Counter` when the alphabet is large or unknown.
- **Bytes.** `bytes` is immutable; `bytearray` is a mutable byte array with in-place `+=`, the right buffer for byte-level protocols and ASCII-only editing.
- **Unicode caveats.** "é" can be one code point or two ("e" plus a combining accent): they look identical but compare unequal until you `unicodedata.normalize("NFC", s)`. Caseless comparison needs `casefold()` (`"ß".casefold()` is `"ss"`). An emoji with a skin tone has `len` 2, a family emoji 5, and `s[::-1]` can split them. When a problem says "lowercase English letters", it is telling you the 26-slot trick is safe.

## Template

```python
def letter_counts(s):
    """Counts of 'a'..'z' in s; s must contain only lowercase English letters."""
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - ord("a")] += 1
    return counts


def shift_letters(s, k):
    """Caesar shift by k: collect characters in a list, join once."""
    out = []
    for ch in s:
        out.append(chr((ord(ch) - ord("a") + k) % 26 + ord("a")))
    return "".join(out)
```

## Worked example

`letter_counts("listen")` and `letter_counts("silent")` both have a 1 in the slots for e, i, l, n, s and t, so the two words are anagrams: O(n + 26) instead of comparing sorted copies in O(n log n).

Timing three ways of building a string of n characters, one run of CPython 3.12 on a shared server (milliseconds; doubling n should double a linear cost and quadruple a quadratic one):

| n | `s += "x"` | `s += "x"` with a second reference to `s` | `"".join(parts)` |
|---|---|---|---|
| 50,000 | 5 | 54 | 4 |
| 100,000 | 12 | 352 | 8 |
| 200,000 | 21 | 2,829 | 15 |

The plain loop looks linear only because of the in-place optimisation; one extra reference (`t = s` before the `+=`) makes every step copy the whole string, and the cost grows at least fourfold per doubling.

## Pitfalls

- `ord(ch) - 97` on input with capitals, digits or accents indexes the wrong slot or raises `IndexError`; check the stated alphabet.
- `sorted(s)` returns a list of characters; use `"".join(sorted(s))` when you need a string.
- Calling `s.replace`, `s.find` or slicing inside a loop over the same long string repeats O(n) work each time.
- `len(s)` is not the number of visible characters, and reversing a string with combining marks or emoji modifiers can corrupt it.

## Quick check

Q: Why can `for w in words: line += w + " "` be quadratic even though it is often fast on CPython, and what is the portable fix?
A: Each `+=` may build a new string and copy everything so far, which is O(L²) in the total length L. CPython often avoids the copy by resizing in place when `line` has no other reference, but that is an implementation detail. `" ".join(words)` is O(L) everywhere.

> [!know]
> You now know how Python stores strings, how to build and count them in linear time, and which Unicode facts break naive indexing.

=== recap | Grids: row-major indexing, neighbours and traversal orders | 12 min
goal: Index any cell by row-major arithmetic, walk neighbours with direction arrays and safe bounds, and produce spiral and diagonal orders
tag: arrays-grid | Grid indexing and traversal orders
practice: 566, 54, 498
link: Python FAQ: how do I create a multidimensional list? | https://docs.python.org/3/faq/programming.html#how-do-i-create-a-multidimensional-list | 2 min: why [[None] * w] * h shares one row, and the comprehension that fixes it

> [!key]
> A grid is an array of rows. In **row-major** order, cell (r, c) of an R x C grid is flat index `r * C + c`, and flat index k is cell `(k // C, k % C)`. Move with a **direction array** and one bounds check, peel a spiral with four shrinking boundaries, and recognise diagonals by an invariant: `r - c` is constant along a top-left to bottom-right diagonal, `r + c` along an anti-diagonal.

## Internals

- **Lists of lists.** Each row is its own list object, so `g[r][c]` is two pointer hops and rows may differ in length. `[[0] * C] * R` holds R references to one row: write one cell and the whole column changes. Build `[[0] * C for _ in range(R)]`.
- **NumPy and C** store a 2D array as one block (row-major, `order="C"`, by default) with strides: element (r, c) sits at byte offset `r * strides[0] + c * strides[1]`. Scanning row by row reads consecutive memory, so in C and NumPy the last index should vary fastest.
- **Negative indices wrap.** `g[-1]` is the last row, so a neighbour at r - 1 = -1 silently reads the wrong cell instead of failing. Check `0 <= nr < R and 0 <= nc < C` every time.
- **Directions.** `DIRS4 = ((0, 1), (1, 0), (0, -1), (-1, 0))` lists east, south, west, north, so turning right is `d = (d + 1) % 4`. Add the four diagonals for 8-neighbourhoods.
- **Spiral.** Invariant: the unvisited cells are exactly the rectangle rows top..bottom, columns left..right. Walk its top row, then its right column; walk the bottom row only if rows remain and the left column only if columns remain, shrinking one boundary after each side.
- **Diagonals.** Group cells by `r - c` (R + C - 1 groups) to check or sort each diagonal; group by `r + c` to walk anti-diagonals, reversing every other one for a zigzag.
- **Transpose** of a non-square grid makes a new C x R grid: `[list(col) for col in zip(*g)]` (`zip` yields tuples).

## Template

```python
DIRS4 = ((0, 1), (1, 0), (0, -1), (-1, 0))           # E, S, W, N: clockwise


def neighbours(r, c, R, C, dirs=DIRS4):
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < R and 0 <= nc < C:
            yield nr, nc


def spiral(g):
    """Cells of g in clockwise spiral order from the top-left corner."""
    out = []
    if not g or not g[0]:
        return out
    top, bottom, left, right = 0, len(g) - 1, 0, len(g[0]) - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            out.append(g[top][c])
        top += 1
        for r in range(top, bottom + 1):
            out.append(g[r][right])
        right -= 1
        if top <= bottom:
            for c in range(right, left - 1, -1):
                out.append(g[bottom][c])
            bottom -= 1
        if left <= right:
            for r in range(bottom, top - 1, -1):
                out.append(g[r][left])
            left += 1
    return out
```

## Worked example

```steps
3 x 4 grid, unvisited rectangle rows 0..2, columns 0..3. Walk the top row, then top = 1
    top 0  bottom 2  left 0  right 3      out: a b c d
          c0 c1 c2 c3
      r0   {{a  b  c  d}}
      r1   e  f  g  h
      r2   i  j  k  l
---
Walk the right column, rows 1..2, then right = 2
    top 1  bottom 2  left 0  right 3      out: ... h l
          c0 c1 c2 c3
      r0   .  .  .  .
      r1   e  f  g  {{h}}
      r2   i  j  k  {{l}}
---
Rows remain (1 <= 2): walk the bottom row right to left, columns 2..0, then bottom = 1
    top 1  bottom 2  left 0  right 2      out: ... k j i
          c0 c1 c2 c3
      r0   .  .  .  .
      r1   e  f  g  .
      r2   {{i  j  k}}  .
---
Columns remain (0 <= 2): walk the left column upwards, rows 1..1, then left = 1
    top 1  bottom 1  left 0  right 2      out: ... e
          c0 c1 c2 c3
      r0   .  .  .  .
      r1   {{e}}  f  g  .
      r2   .  .  .  .
---
Second lap, rectangle rows 1..1, columns 1..2: top row gives f g, then top = 2 and right = 1
    top 2  bottom 1  left 1  right 1      out: ... f g
          c0 c1 c2 c3
      r1   .  {{f  g}}  .
---
top 2 > bottom 1: the bottom-row walk is skipped (without the check, f would be emitted twice); the left column is empty; the loop ends
    out: a b c d h l k j i e f g   (12 cells, each exactly once)
```

## Pitfalls

- `[[0] * C] * R` aliasing, described above; it passes tests that only read the grid.
- Swapping R and C: `len(g)` is the row count and `len(g[0])` the column count. Test with a non-square grid.
- Dropping the two re-checks in the spiral emits the middle row or column twice when the remaining rectangle is one cell thick.
- An empty grid (`[]` or `[[]]`): `g[0]` raises on `[]`, so guard first.

## Quick check

Q: In a 3 x 5 grid, which cell has flat index 11, which flat index does cell (2, 3) have, and which cells lie on the anti-diagonal r + c = 3?
A: Cell (2, 1), since 11 // 5 = 2 and 11 % 5 = 1. Cell (2, 3) is 2 * 5 + 3 = 13. The anti-diagonal r + c = 3 holds (0, 3), (1, 2) and (2, 1).

> [!know]
> You now know how to index a grid with row-major arithmetic, walk it safely, and produce spiral and diagonal orders from boundary and diagonal invariants.

=== recap | Transforming matrices in place | 10 min
goal: Rotate a square matrix with transpose plus reverse, and update cells that depend on old neighbour values without a second grid
tag: arrays-matrix-inplace | In-place matrix transforms
practice: 48, 289, 73
link: Wikipedia: Conway's Game of Life, rules | https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life#Rules | 2 min: the birth and survival rules, applied to every cell simultaneously

> [!key]
> Build a transform from simple in-place passes: a clockwise quarter turn is a **transpose followed by reversing each row**. When every new value depends on old neighbours, do not copy the grid: keep **both states in each cell** (bit 0 old, bit 1 new), or store flags in cells whose information you no longer need, then finalise in a second pass.

## Internals

- **Where a cell goes.** A clockwise turn sends (r, c) to (c, n - 1 - r). Transposing sends (r, c) to (c, r); reversing each row then sends (c, r) to (c, n - 1 - r). Counter-clockwise: transpose, then reverse the order of the rows (`m.reverse()`). Half turn: reverse the rows and every row.
- **Transpose in place** works only for square matrices (the shape changes otherwise) and must swap only the upper triangle, c > r: swapping every pair twice puts everything back.
- **Layer by layer** is the alternative: rotate four cells at a time around each ring. Same O(n²), one pass, more index arithmetic to get wrong.
- **Two states per cell.** In a synchronous update (every next state uses the current neighbours, as in the Game of Life), store the next state in bit 1: read neighbours with `cell & 1`, set `cell |= 2` when the cell will be alive, and after the whole pass shift every cell right by one. Any encoding works if the old state stays recoverable until the last cell is computed.
- **Borrowed storage.** If you need one flag per row and per column in O(1) extra space, some cells of the matrix itself can hold the flags once their own information is saved, provided the final pass never overwrites a flag before reading it. Working out which cells, and in which order to apply them, is the exercise.
- **Python reality.** `m[:] = [list(row) for row in zip(*m[::-1])]` rotates clockwise in one line but builds a whole new grid: fine in production, not when O(1) extra space is required. NumPy's `np.rot90(a, -1)` returns a view (it only rearranges strides), so it costs O(1) until you copy it.

## Template

```python
def rotate_clockwise(m):
    """Rotate a square matrix 90 degrees clockwise in place."""
    n = len(m)
    for r in range(n):
        for c in range(r + 1, n):              # upper triangle only
            m[r][c], m[c][r] = m[c][r], m[r][c]
    for row in m:
        row.reverse()


def commit_next_states(g):
    """After a pass that set bit 1 (g[r][c] |= 2) for every cell alive next, make it current."""
    for row in g:
        for c in range(len(row)):
            row[c] >>= 1
```

## Worked example

```steps
Start: the left column 1 4 7 must become the top row, read bottom to top: 7 4 1
    1  2  3
    4  5  6
    7  8  9
---
Transpose: swap m[r][c] with m[c][r] for c > r (three swaps); the diagonal 1 5 9 stays put
    1  {{4}}  {{7}}
    {{2}}  5  {{8}}
    {{3}}  {{6}}  9
---
Reverse each row: (c, r) moves to (c, n - 1 - r), completing (r, c) -> (c, n - 1 - r)
    {{7  4  1}}
    {{8  5  2}}
    {{9  6  3}}
```

Two-state cells in the Game of Life: a live cell (1) with two live neighbours survives, so it becomes 3 (binary 11); a dead cell (0) with three live neighbours is born, so it becomes 2 (binary 10). Neighbours keep reading bit 0, which still holds the old state. After the pass, `>>= 1` turns 3 and 2 into 1, and 1 and 0 into 0.

## Pitfalls

- Transposing both triangles swaps each pair twice: nothing changes.
- Testing `cell == 1` after encoding: a live cell may already be 3. Read `cell & 1`.
- Writing a final value before every neighbour has read the old one: exactly the bug the two-state trick prevents.
- With borrowed flag cells, applying the flags of the borrowed row or column first destroys flags you still need.

## Quick check

Q: Which two in-place passes rotate a square matrix 90 degrees counter-clockwise?
A: Transpose, then reverse the order of the rows (`m.reverse()`). The transpose sends (r, c) to (c, r) and reversing the row order sends row c to row n - 1 - c, so (r, c) ends at (n - 1 - c, r), which is the counter-clockwise position. Reversing each row first and then transposing also works.

> [!know]
> You now know how to compose rotations from transposes and reversals, and how to update a grid synchronously without copying it.

=== lab | Build a dynamic array and measure growth factors | 45 min
goal: Measure element moves, wasted capacity and speed for growth factors 2, 1.5 and 1.125 and for additive growth, and reproduce CPython's list capacities
link: Wikipedia: Dynamic array, growth factor | https://en.wikipedia.org/wiki/Dynamic_array#Growth_factor | 3 min: the table of growth factors used by real libraries and the time versus memory argument

You will extend the `DynArray` from the first recap, prove it correct against `list` with a random tester, and then measure what the growth factor buys and costs. Predict every number before you run it.

## Setup

- Python 3.10 or later, standard library only. Save everything in `dynarray_lab.py`, starting with the `DynArray` class from the first recap.

## Steps

1. Add `__setitem__(i, x)` with the same bounds check as `__getitem__`, and `insert(i, x)` for 0 <= i <= len: grow if full, shift a[i:] one slot right starting from the end, then write x. Count shifted elements in `self.moves` too.
2. Stress-test it against a plain list. A mismatch prints the seed, so you can replay the failing run:

```python
import random


def stress(runs=300, ops=300):
    for seed in range(runs):
        rng = random.Random(seed)
        a, model = DynArray(), []
        for _ in range(ops):
            op = rng.choice("aaapis")
            if op == "a":
                x = rng.randint(0, 99)
                a.append(x)
                model.append(x)
            elif op == "p" and model:
                assert a.pop() == model.pop(), seed
            elif op == "i":
                i, x = rng.randint(0, len(model)), rng.randint(0, 99)
                a.insert(i, x)
                model.insert(i, x)
            elif op == "s" and model:
                i, x = rng.randrange(len(model)), rng.randint(0, 99)
                a[i] = x
                model[i] = x
            assert len(a) == len(model) and [a[i] for i in range(len(a))] == model, seed
            assert a._n <= a._cap and (a._cap <= 4 or a._n > a._cap // 4), seed
    print("stress test passed")


stress()
```

3. Measure moves per append and the average share of unused capacity for three geometric factors and for additive growth. Before running, write down the band you expect from the recap: between 1 / (r - 1) and r / (r - 1) moves per append.

```python
def factor(r):
    return lambda cap: max(4, cap + 1, int(cap * r))


def profile(grow, n):
    a, wasted = DynArray(grow), 0.0
    for i in range(n):
        a.append(i)
        wasted += (a._cap - len(a)) / a._cap
    return a.moves / n, wasted / n


for name, grow in [("x2", factor(2)), ("x1.5", factor(1.5)), ("x1.125", factor(1.125)),
                   ("+16", lambda cap: cap + 16)]:
    sizes = (10**4, 10**5) if name == "+16" else (10**4, 10**5, 10**6)
    for n in sizes:
        moves, wasted = profile(grow, n)
        print(f"{name:7} n={n:>9,}  moves/append={moves:8.2f}  unused={wasted:5.1%}")
```

4. Reproduce CPython's growth from the outside: append 100 items to a real list and record the capacity whenever it changes, using `(sys.getsizeof(a) - sys.getsizeof([])) // 8`.
5. Time one million appends to `DynArray` and to `list` with `time.perf_counter`, three runs each, and report the best.
6. Measure memory with `tracemalloc`: one million distinct floats in a `list`, in `array('d')`, and in your `DynArray`.
7. Optional: change the shrink rule in `pop` from a quarter to a half (`self._n <= self._cap // 2`), then alternate append and pop 10,000 times on an array of 4,096 items whose capacity is exactly 4,096 (build it by appending 4,096 items with doubling). Count `moves` under both rules.

## What you should see

These numbers come from CPython 3.12 on a shared Linux server; yours will differ in the second digit, not the first.

- The stress test passes. If it fails, the usual culprits are shifting from the front in `insert` (it overwrites before copying) and forgetting to grow before inserting into a full block.
- Moves per append at n = 10^6 land inside the predicted band: about 1.05 for x2 (band 1 to 2), 2.1 for x1.5 (band 2 to 3) and 8.7 for x1.125 (band 8 to 9). They wobble with n because the last resize may or may not have just happened. Additive +16 gives about 312 moves per append at 10^4 and about 3,100 at 10^5: ten times the elements, a hundred times the total work.
- Average unused capacity is roughly 26 to 29% for x2, 17 to 18% for x1.5 and under 6% for x1.125: the memory you save by growing slowly is paid for in moves.
- CPython's capacities come out as 4, 8, 16, 24, 32, 40, 52, 64, 76, 92, 108, matching the comment in `listobject.c`.
- A million `DynArray.append` calls take about 0.45 s against about 0.06 s for `list.append` in the same Python loop, so roughly 5 to 10 times slower. The shape matches; the constant is your resize and bookkeeping code running in the interpreter instead of C.
- A million floats take about 32 MB as a `list` and about the same in `DynArray` (both store references to 24-byte float objects), against 8 MB in `array('d')`.
- With the half-full shrink rule, alternating append and pop at the boundary triggers a resize on every operation: 4,096 moves per operation, about 41 million in total, against a single resize (4,096 moves in all) with the quarter rule. This is why real dynamic arrays shrink late.

## Check yourself

Q: Your measurement for x1.5 says 2.77 moves per append at n = 100,000 but 2.10 at 1,000,000. Is something wrong?
A: No. The average depends on where n falls relative to the last resize: just after a resize the array has paid for a large copy that later appends have not yet amortised. Both values lie inside the band from 1 / (r - 1) = 2 to r / (r - 1) = 3.

=== practice
- 566 core
  pattern: arrays-grid
  cue: Two grid shapes contain the same cells in the same reading order.
  hint: Number the cells 0, 1, 2, ... in reading order. How do you turn that number into a row and column for each shape?
  insight: If m * n != r * c the reshape is impossible, so return the input. Otherwise flat index k is cell (k // n, k % n) in the source and (k // c, k % c) in the target, so one loop over k copies everything in row-major order.
  cost: O(m n) time, O(m n) for the output
- 448 core
  pattern: arrays-ownindex
  cue: Values lie in 1..n in an array of length n, and the follow-up asks for no extra space.
  hint: Each value names a slot. How can you mark that slot as visited without losing the number stored in it?
  insight: For every x, negate slot abs(x) - 1 if it is still positive. Afterwards slot i is positive exactly when i + 1 never appeared; abs() recovers values that were marked before you reached them.
  cost: O(n) time, O(1) extra space besides the output
- 645 core
  pattern: arrays-ownindex
  cue: A permutation of 1..n where one value was overwritten by a copy of another, and you must name both.
  hint: Mark the slot of each value as you go. What do you see when you arrive at a slot that is already marked?
  insight: With sign marking, the value whose slot is already negative is the duplicate; after the pass, the one slot still positive gives the missing value (index + 1). Sum identities also work: the duplicate minus the missing value equals sum(a) - n(n + 1)/2.
  cost: O(n) time, O(1) extra space
- 31 core
  pattern: arrays-inplace
  cue: Rearrange into the next larger ordering of the same values, in place, wrapping to the smallest at the end.
  hint: Look at the array from the right. Which suffix is already as large as it can possibly be?
  insight: Find the rightmost i with a[i] < a[i + 1]; the suffix after it is non-increasing. Swap a[i] with the rightmost suffix element larger than it, then reverse the suffix to make it as small as possible. If there is no such i, reverse the whole array.
  cost: O(n) time, O(1) extra space
- 54 core
  pattern: arrays-grid
  cue: Read every cell of a rectangle once, going round its edge clockwise and moving inwards.
  hint: Describe the cells not yet visited as a rectangle. Which boundary moves after you finish each side?
  insight: Keep top, bottom, left and right. Walk the top row and the right column, shrinking those bounds; walk the bottom row only if top <= bottom still holds and the left column only if left <= right, so a one-cell-thick middle is not read twice.
  cost: O(m n) time, O(1) extra space besides the output
- 498 core
  pattern: arrays-grid
  cue: Output the cells along anti-diagonals, alternating direction on each one.
  hint: What do all cells on one anti-diagonal have in common?
  insight: Cells with equal r + c form one anti-diagonal, so loop d from 0 to m + n - 2, collect the valid cells of diagonal d from the top row down, and reverse every even d so it reads bottom-left to top-right.
  cost: O(m n) time, O(min(m, n)) extra space per diagonal
- 48 core
  pattern: arrays-matrix-inplace
  cue: Rotate a square matrix a quarter turn without allocating another matrix.
  hint: Can the rotation be written as two simpler rearrangements that are each easy to do in place?
  insight: Transpose by swapping across the main diagonal (upper triangle only), then reverse every row. Together they send (r, c) to (c, n - 1 - r), which is exactly a clockwise quarter turn.
  cost: O(n^2) time, O(1) extra space
- 289 core
  pattern: arrays-matrix-inplace
  cue: Every cell's next state depends on its neighbours' current states, and the update must happen in place.
  hint: Each cell holds 0 or 1, but an int has room for more. What if a cell could remember its old state and its new one at the same time?
  insight: Count live neighbours with cell & 1, and set cell |= 2 when the cell is alive in the next generation (2 or 3 neighbours if alive, exactly 3 if dead). After the full pass, shift every cell right by one.
  cost: O(m n) time, O(1) extra space
- 73 derive
  pattern: arrays-matrix-inplace
  cue: Zero every row and column that contains a zero, in place, with constant extra memory.
  hint: You need a flag per row and per column. Is there a row and a column whose cells could store those flags, once you remember what they themselves held?
  insight: Use row 0 and column 0 as the flag arrays, plus one boolean for whether column 0 itself contained a zero (row 0's own flag lives in cell (0, 0)). Mark flags in one pass, zero the inner cells from the flags, then zero row 0 and finally column 0, so no flag is overwritten before it is read.
  cost: O(m n) time, O(1) extra space
- 41 derive
  pattern: arrays-ownindex
  cue: Smallest positive integer that is absent, in O(n) time and constant extra space, with negatives, zeros and huge values mixed in.
  hint: An array of length n can contain at most n distinct positives. Which values can the answer possibly be, and which inputs can you therefore ignore?
  insight: The answer lies in 1..n + 1. Cyclic sort: swap each value v in 1..n into index v - 1 until that slot already holds v, ignoring everything else. Then the first index i with a[i] != i + 1 gives i + 1; if every slot matches, the answer is n + 1.
  cost: O(n) time, O(1) extra space
- 238 stretch
  pattern: arrays-inplace
  cue: Each output is the product of all other elements, division is not allowed, and the output array does not count as extra space.
  hint: Split each answer into what lies to its left and what lies to its right.
  insight: Fill the output left to right with prefix products (out[i] = product of a[:i]), then sweep right to left with one running suffix product, multiplying it into out[i] before including a[i]. Zeros need no special case.
  cost: O(n) time, O(1) extra space besides the output
- 1980 stretch
  pattern: arrays-strings
  cue: Produce any length-n binary string missing from a list of n distinct length-n strings.
  hint: You only have to differ from each listed string somewhere. Can you choose one position per string?
  insight: Cantor's diagonal argument: make character i the opposite of strings[i][i]. The result differs from string i at position i, so it equals none of them. Build it in a list and join once.
  cost: O(n) time, O(n) for the output
