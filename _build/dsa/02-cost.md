---
key: cost
name: Complexity, memory and cost models
stage: found
summary: Predict how code scales in time and memory before you run it, including amortised costs and what Python's built-ins really cost, then confirm the prediction with a doubling experiment.
why: Every design decision in this guide is a cost decision: a set instead of a list, a heap instead of repeated sorting, a deque instead of pop(0). Problem constraints are stated precisely so that you can rule approaches in or out before writing a line, and production code fails the same way at a larger scale: an innocent `x in some_list` inside a loop turns a 10 ms request into a 10 s one once the data grows. This module gives you a cost model you can apply by reading code, the vocabulary to state bounds precisely (O, Theta, Omega, amortised, expected), the Python-specific prices that the textbook model hides, the memory and cache effects that Big-O ignores, and the habit of checking every prediction with a measurement.
outcomes:
- Count the work of sequential, nested, dependent and halving loops, including loops hidden inside built-ins, and state it in Big-O with every relevant size variable
- Use O, Theta and Omega precisely, and say which case (best, worst, average, expected, amortised) a bound describes
- Account for space: auxiliary memory, output, the recursion stack and the real bytes of Python objects
- Prove amortised bounds with the aggregate and credit methods for doubling arrays, two-stack queues and binary counters
- Explain why contiguous scans beat pointer chasing at equal Big-O, using cache lines and locality
- Quote the cost of common list, dict, set, deque, str, heapq and bisect operations and choose the right container
- Run a doubling experiment, estimate the growth exponent and explain where Big-O misleads
cues:
- The constraints give sizes (n up to 10^5, values up to 10^9, a 1000 x 1000 grid): turn them into a target complexity before designing
- You must choose between two approaches, or between two containers for the same job
- Code passes small tests but times out or runs out of memory on large ones
- A loop body calls something that is secretly a loop: `in` on a list, slicing, `pop(0)`, `insert(0, x)`, `sorted`, `sum`
- An operation is usually cheap but occasionally rebuilds, refills or resizes something
traps:
- Treating O as "worst case" and Theta as "average": they are bounds on a function, and each case has its own function
- Missing the hidden loop in one line, such as `x in some_list` or `a[1:]`, inside another loop
- Collapsing several size variables into one n, or forgetting the recursion stack and the output when counting memory
- Assuming `s += piece` in a loop is always fine because CPython often makes it fast; bytes, shared references and other Python implementations make it quadratic
- Trusting one timing: take the best of several repeats at several doubling sizes before concluding anything
systems:
- CPython's list over-allocates by about one eighth (capacities 0, 4, 8, 16, 24, 32, 40, 52, 64, 76, 92, ...), so appends are amortised O(1) with at most about 8 element copies per append on average
- collections.deque is a doubly linked list of 64-slot blocks: appends and pops at both ends never move other items, while d[i] near the middle walks blocks and is O(n)
- Redis rehashes its hash tables incrementally and Go caps each map table at 1,024 entries, because an amortised O(1) bound still allows one O(n) operation that a latency-sensitive server cannot afford
- NumPy, array.array and columnar databases store values contiguously so scans stream through cache lines; summing the same Python floats in shuffled memory order ran about 3 times slower in our measurement
further:
- Article · 30 min | Sedgewick and Wayne: 1.4 Analysis of Algorithms (observations, doubling ratio, memory usage) | https://algs4.cs.princeton.edu/14analysis/
- Notes · 40 min | Jeff Erickson: Amortized Analysis (binary counter four ways, PDF pages 1-5) | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/09-amortize.pdf
- Docs · 15 min | Python docs: time complexity of operations on built-in types | https://docs.python.org/3/builtins/time-complexity.html#list
- Article · 15 min | Algorithmica: memory hierarchy (latency and bandwidth of each level) | https://en.algorithmica.org/hpc/external-memory/hierarchy/
---

=== primer | How do you predict running time before you run the code? | 15 min
goal: Count the basic operations of any loop structure, including loops hidden inside built-ins, and turn the count into Big-O and a rough time in seconds
tag: cost-count | Counting operations
link: USACO Guide: Time Complexity | https://usaco.guide/bronze/time-comp#complexity-calculations | 10 min: 'Complexity Calculations' (loop rules with code), then the table under 'Common Complexities and Constraints'
practice: 1732, 2073, 1588

> [!key]
> Running time is (number of basic steps) x (time per step). The second factor depends on the machine; the first depends only on your code and the input size, so count it: **add** sequential blocks, **multiply** nested loops, **sum** the inner counts of dependent loops, and count halvings with log2 n. Every built-in call that touches many elements (`x in list`, slicing, `sum`, `sorted`) is a loop too, and must be counted.

## Intuition

At a meeting where everyone shakes hands with everyone else once, 5 people make 4 + 3 + 2 + 1 = 10 handshakes, 100 people make 4,950, and 10,000 people make about 50 million. You need no stopwatch to know the last meeting is a disaster. A count written as a formula in n tells you how the cost **grows**, and growth decides whether code survives real input sizes.

## How it works

### Pick a cost model

Decide what one step is: an arithmetic operation on a small integer, a comparison, an assignment, indexing `a[i]`, an average-case dict or set lookup. Each takes roughly constant time. Anything that touches many elements is *not* one step; it costs one step per element it touches.

### Combine the pieces

| Code shape | Steps | Growth |
|---|---|---|
| Two loops one after the other, n and m iterations | n + m | O(n + m) |
| A loop of m inside a loop of n | n x m | O(nm) |
| `for i in range(n): for j in range(i + 1, n)` | (n - 1) + ... + 1 + 0 = n(n - 1)/2 | O(n^2) |
| `while n > 1: n //= 2` | floor(log2 n) | O(log n) |
| `i = 1` then `while i * i <= n: i += 1` | about sqrt(n) | O(sqrt n) |
| `for d in range(1, n + 1): for m in range(d, n + 1, d)` | n/1 + n/2 + ... + n/n | O(n log n) |
| `for i in range(n):` then `j = 1; while j < n: j *= 2` | n x ceil(log2 n) | O(n log n) |

The dependent loop is a triangle, half of an n by n square, so it is still quadratic. The harmonic row deserves a second look: n/1 + n/2 + ... + n/n = n(1 + 1/2 + ... + 1/n), and the bracket (the harmonic number) is about ln n + 0.58. A loop that visits the multiples of every d costs about n ln n, not n^2. Sieves have this shape.

### Find the hidden loops

One line can hide a loop: `x in a_list` scans up to the whole list, `a[i:j]` copies j - i references, `sum(a[:i])` copies and then adds, `s.count(c)` scans the string, `a.pop(0)` and `a.insert(0, x)` shift every other element, `min(a)` scans everything. Put one of these inside a loop over n and you multiply by n.

## Cost

To turn steps into seconds you need the price of a step. On a typical laptop, roughly:

- One iteration of a simple Python loop such as `total += i` costs about 30 to 100 ns. Plan with **about 10^7 simple Python steps per second**; we measured just under 10^7 loop iterations per second on a busy machine.
- A loop that runs inside C, in a built-in such as `sum`, `sorted`, `max`, `x in list` or `str.join`, costs about 1 to 10 ns per element. We measured `sum` over 10^6 integers at about 9 ms, against about 50 ms for the same sum written as a Python `for` loop.

So with Python loops, 10^7 steps take about a second; n^2 with n = 10^4 is 10^8 steps, ten seconds or more; n log2 n with n = 10^6 is about 2 x 10^7 steps, a couple of seconds in pure Python and a fraction of a second when `sorted` does the work. The constraints table in the method module turns these prices into a target complexity for a given n.

## When to use it

Count before you code, every time: it takes a minute and rules out designs that cannot meet the constraints. It also locates the bottleneck, because the dominant term of the count is the line worth optimising. Counting tells you about growth; it cannot tell you which of two O(n) solutions is faster, nor how caches and C built-ins move the constant. For those questions, measure (the last card of this module).

## Worked trace

Count how often the inner line of the dependent double loop runs for n = 5:

```steps
i = 0: j runs over 1, 2, 3, 4, so the inner line runs 4 times
    i        0    1    2    3    4
    inner  {{4}}  .    .    .    .      total 4
---
i = 1: j runs over 2, 3, 4: three more
    i        0    1    2    3    4
    inner    4  {{3}}  .    .    .      total 7
---
i = 2: j runs over 3, 4: two more
    i        0    1    2    3    4
    inner    4    3  {{2}}  .    .      total 9
---
i = 3: j = 4 only
    i        0    1    2    3    4
    inner    4    3    2  {{1}}  .      total 10
---
i = 4: range(5, 5) is empty, so nothing runs
    i        0    1    2    3    4
    inner    4    3    2    1  {{0}}    total 10 = 5 x 4 / 2
---
The counts form a triangle, half an n by n square: n(n - 1)/2 = Theta(n^2)
    n = 10        45 steps
    n = 1,000     499,500 steps
    n = 100,000   about 5 x 10^9 steps: many minutes in pure Python
```

## Template

These counting functions double as a reference card: each returns how often its innermost line runs, and the assertions check the closed forms in the comments.

```python
import math

def dependent_pairs(n):          # n(n - 1)/2
    steps = 0
    for i in range(n):
        for j in range(i + 1, n):
            steps += 1
    return steps

def halvings(n):                 # floor(log2 n) for n >= 1
    steps = 0
    while n > 1:
        n //= 2
        steps += 1
    return steps

def multiples(n):                # n/1 + n/2 + ... + n/n, about n ln n
    steps = 0
    for d in range(1, n + 1):
        for _ in range(d, n + 1, d):
            steps += 1
    return steps

for n in (1, 7, 64, 1000):
    assert dependent_pairs(n) == n * (n - 1) // 2
    assert halvings(n) == n.bit_length() - 1
    assert multiples(n) == sum(n // d for d in range(1, n + 1))
print(multiples(10**5), round(10**5 * math.log(10**5)))   # 1166750 1151293
```

## Pitfalls

- **Hidden loops.** `if x in seen` where `seen` is a list turns a single pass into O(n^2). Use a set.
- **Counting the wrong size.** `for d in range(2, isqrt(v) + 1)` is O(sqrt v) in the *value* v: about 10^9 steps for v = 10^18, although the input is a single number. Say what n measures.
- **Assuming nested means quadratic.** A `while` inside a `for` whose pointer never moves backwards (two pointers, sliding windows, monotonic stacks) runs at most n times *in total*. The amortised card shows why.
- **Big integers are not O(1).** Python ints grow without limit, and multiplying two numbers with thousands of digits costs far more than one step.
- **Slices in loops.** `for i in range(n): total = sum(a[:i])` copies i items each time: about n^2/2 steps.

## Check yourself

Q: How often does the body of `i = 1` then `while i < n: i *= 3` run, as a formula? How many times for n = 100?
A: i takes the values 1, 3, 9, 27, 81, ..., so the body runs once per power of 3 below n: ceil(log3 n) times for n > 1. For n = 100 that is 5 times (i = 1, 3, 9, 27, 81). The growth is O(log n); the base only changes the constant factor.

Q: A function loops over n words and, for each, checks `if w not in result` where `result` is a list of the unique words so far, then appends. What is the worst case, and what is the one-line fix?
A: When all n words are distinct, the k-th check scans k - 1 items: about n^2/2 comparisons, O(n^2). Keep a set beside the list (`seen = set()`, test `w not in seen`, then add to both): each check is O(1) on average, the loop is O(n), and the order of first appearance is kept.

Q: `for i in range(1, n + 1):` with the body `j = i` then `while j <= n: j += i`. Which row of the table is this, and what is its growth?
A: The harmonic row: for each i the inner loop runs floor(n / i) times, so the total is n(1 + 1/2 + ... + 1/n), about n ln n. It is O(n log n), not O(n^2).

## Lab

- **1732** Find the Highest Altitude: one pass with a running total. Expected: O(n) time, O(1) extra space; for gains [3, -4, 6, -1] the altitudes are 0, 3, -1, 5, 4 and the answer is 5.
- **2073** Time Needed to Buy Tickets: write the second-by-second simulation first and count its steps, then replace it with a count per person. Expected: the simulation costs about sum(tickets) steps, which depends on ticket values rather than n; the counting version is O(n). For tickets [4, 1, 3, 2] and k = 2 the answer is 9.
- **1588** Sum of All Odd Length Subarrays (stretch): count the three nested loops of the brute force before you optimise. Expected: brute force O(n^3) as written, O(n^2) with prefix sums, O(n) by counting how many odd-length subarrays contain each index; for [2, 5, 1, 4] the answer is 30.

> [!know]
> You now know how to count the steps of loops, dependent loops, halving loops and hidden built-in loops, and convert the count into a time estimate for Python.

=== primer | What do Big-O, Big-Theta and Big-Omega actually promise? | 15 min
goal: State and check simple asymptotic bounds, keep every size variable, and say which case (best, worst, average, expected) a bound describes
tag: cost-bounds | Asymptotic bounds and cases
link: MIT 6.006 Recitation 1 notes (PDF) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/c6d8f06c6f11e3342633dec85498f551_MIT6_006S20_r01.pdf | 20 min: 'Asymptotic Notation' on PDF page 3 (O, Omega, Theta and the shorthand table), then two of the 'Asymptotics Exercises' on page 6
practice: 1351, 2215

> [!key]
> f(n) = O(g(n)) means f grows **at most** like g: beyond some n0, f(n) <= c g(n) for a fixed constant c. Omega means **at least**, and Theta means both, a tight bound. None of them means "worst case": the worst, best, average and expected costs are different functions, and each can be bounded with O, Omega or Theta. Keep every independent size (n, m, k, the output size) in the bound.

## Intuition

A bound is like a builder's quote. "At most 10,000" (O) promises the bill will not be higher, and it stays true if the bill is 50. "At least 5,000" (Omega) promises it will not be lower. "Between 5,000 and 10,000" (Theta) pins it down. "At most a million" is also true, just useless: binary search is technically O(n), but O(log n) is the statement that informs. Aim for the tightest bound you can justify, and say which situation it covers.

## How it works

### The definitions

- f(n) = O(g(n)) if there are constants c > 0 and n0 such that f(n) <= c g(n) for every n >= n0.
- f(n) = Omega(g(n)) if there are constants c > 0 and n0 such that f(n) >= c g(n) for every n >= n0.
- f(n) = Theta(g(n)) if both hold, possibly with different constants.

Example: f(n) = 3n^2 + 10n + 5. For n >= 1, 10n <= 10n^2 and 5 <= 5n^2, so f(n) <= 18n^2: O(n^2) with c = 18 and n0 = 1. Also f(n) >= 3n^2 for every n, so Omega(n^2), and together Theta(n^2). Constant factors and lower-order terms disappear because one fixed multiple absorbs them.

### Rules you use every day

- Drop constant factors and lower-order terms: 5n log n + 100n = Theta(n log n).
- Sum rule: O(f) + O(g) = O(max(f, g)). Product rule: a loop of O(f) iterations doing O(g) work each is O(f x g).
- The base of a logarithm does not matter (log2 n = log10 n / log10 2, a constant factor), but the base of an exponential does: 4^n = (2^n)^2 is not O(2^n).
- The ladder: 1 < log n < sqrt n < n < n log n < n^2 < n^3 < 2^n < n!. Any power of log n grows more slowly than any positive power of n.

### Several variables and the output

When the input has several independent sizes, keep them all. Comparing two arrays of lengths n and m costs O(n + m) with sets and O(nm) with nested loops. A grid is O(rows x cols). A graph search is O(V + E), and E can reach V^2, so "O(V)" would be wrong. Keeping the k smallest of n items in a heap is O(n log k), far better than O(n log n) when k is small.

**Output-sensitive** bounds include the size of the answer: listing every pair that sums to a target costs O(n + p) where p is the number of pairs reported, and p alone can be Theta(n^2). No algorithm beats the size of its own output.

### Which case?

| Case | Taken over | Example |
|---|---|---|
| Worst | The hardest input of size n | Linear search for a missing item: n comparisons |
| Best | The easiest input of size n | Insertion sort on sorted input: n - 1 comparisons |
| Average | Inputs from an assumed distribution | Linear search for an item at a uniformly random position: (n + 1)/2 |
| Expected | The algorithm's own random choices, for every input | Quicksort with random pivots: about 1.39 n log2 n comparisons on any input |
| Amortised | A whole sequence of operations, no probability | n appends to a dynamic array: O(n) in total |

Average and expected differ in what they assume. An average-case bound fails when real inputs do not look like the assumed distribution (already sorted input for a quicksort that always picks the first element). An expected bound holds for every input, because the randomness lives inside the algorithm. "O(1) for a hash table" is an average over keys that hash well, which an attacker can break; the hashing module shows how.

## Cost

What the classes mean at real sizes, at roughly 10^7 simple Python steps per second:

| Growth | n = 10 | n = 1,000 | n = 10^6 | Python at n = 10^6 |
|---|---|---|---|---|
| log2 n | 3.3 | 10 | 20 | instant |
| n | 10 | 1,000 | 10^6 | 0.1 s |
| n log2 n | 33 | 10^4 | 2 x 10^7 | 2 s |
| n^2 | 100 | 10^6 | 10^12 | about a day |
| 2^n | 1,024 | about 10^301 | unthinkable | never |

Notice how little separates the classes at n = 10 and how much at n = 10^6: asymptotic notation is a statement about large n.

## When to use it

- Use **Theta** when you can show the bound is tight; it is the most informative statement. Use **O** when you only need a guarantee ("no worse than") and **Omega** for lower bounds: any algorithm that must read all n inputs is Omega(n), and comparison sorting needs Omega(n log n) comparisons.
- Always name the case. "Insertion sort is Theta(n^2) in the worst case and Theta(n) in the best case" is precise; "insertion sort is Theta(n^2)" is false for sorted input.
- Asymptotics compare growth, not speed at your n. Two O(n) solutions can differ by 10x, and an O(n log n) built-in written in C often beats an O(n) loop written in Python at n = 10^6. When the classes tie or n is small, measure.

## Worked trace

Find where 3n^2 + 10n + 5 <= 4n^2 starts to hold for good, which proves O(n^2) with c = 4:

```steps
n = 1: f(1) = 18 but 4n^2 = 4. Small n: the lower-order terms dominate
    n       1
    f(n)  {{18}}
    4n^2    4
---
n = 5: f(5) = 130, 4n^2 = 100. Still above
    n       1    5
    f(n)   18  {{130}}
    4n^2    4  100
---
n = 10: f(10) = 405, 4n^2 = 400. Just above
    n       1    5    10
    f(n)   18  130  {{405}}
    4n^2    4  100   400
---
n = 11: f(11) = 478 <= 484. From here on 4n^2 - f(n) = n^2 - 10n - 5 only grows
    n       1    5    10    11
    f(n)   18  130   405  {{478}}
    4n^2    4  100   400   484
---
So c = 4, n0 = 11 works, and so does c = 18, n0 = 1. Any c > 3 works with a big enough n0; c = 3 never does
    f(n) / n^2 at n = 10, 100, 1000:   4.05   3.1005   3.010005   -> 3
```

## Template

Two numerical checks catch most mistakes: a ratio table (if f(n)/g(n) settles to a positive constant, f = Theta(g)) and a step counter run on best-case and worst-case inputs.

```python
def ratio_table(f, g, sizes):
    """f(n)/g(n) for growing n: settles to a constant > 0 means Theta(g),
    heads to 0 means f grows slower, keeps growing means f grows faster."""
    return [(n, f(n) / g(n)) for n in sizes]

def insertion_sort_comparisons(a):
    """Sort a copy of a by insertion and return the number of comparisons."""
    a, comparisons = list(a), 0
    for i in range(1, len(a)):
        key, j = a[i], i - 1
        while j >= 0:
            comparisons += 1
            if a[j] <= key:
                break
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return comparisons

n = 1000
print(insertion_sort_comparisons(range(n)))           # best case, sorted: 999
print(insertion_sort_comparisons(range(n, 0, -1)))    # worst case, reversed: 499500
print(ratio_table(lambda n: 3 * n * n + 10 * n + 5, lambda n: n * n, [10, 100, 1000]))
```

## Pitfalls

- **"O means worst case."** O is an upper bound on whatever function you describe. Say "worst-case O(n^2)" or "best-case Theta(n)".
- **Loose bounds passed off as tight.** "Binary search is O(n)" is true and misleading. Prefer Theta when you can show it.
- **Collapsing variables.** O(n + m) is not O(n) when m can be far larger; in graphs E can reach V^2.
- **Hiding a big constant.** An algorithm doing 1000n steps loses to one doing n^2 steps for every n below 1000.
- **Forgetting what n measures.** Trial division up to sqrt(v) is polynomial in the value v but exponential in the number of digits of v.

## Check yourself

Q: True or false, with a reason: (a) 2^(n+1) = O(2^n); (b) 4^n = O(2^n); (c) log2(n^3) = Theta(log n).
A: (a) True: 2^(n+1) = 2 x 2^n, a constant factor. (b) False: 4^n / 2^n = 2^n grows without bound, so no constant c works. (c) True: log2(n^3) = 3 log2 n, a constant factor.

Q: A teammate writes "quicksort is O(n log n)" in a design note. When is that wrong, and how should it be phrased?
A: With a fixed pivot rule such as "first element", sorted or reversed input makes every split maximally unbalanced and the worst case is Theta(n^2). Precise versions: "expected O(n log n) on every input with random pivots", or "worst case Theta(n^2), average Theta(n log n) over random inputs".

Q: You must count how many of m query values occur in an array of n numbers. Give the cost of (a) `q in arr` for each query, (b) building a set once and looking each query up, (c) sorting once and binary searching each query. Which wins for n = 10^6 when m = 10, and when m = 10^5?
A: (a) O(nm), (b) O(n + m) expected, (c) O(n log n + m log n). For m = 10 all three are fine: (a) is ten C-level scans, about the cost of building the set. For m = 10^5, (a) is 10^11 comparisons and hopeless, while (b) stays O(n + m) and (c) about 2 x 10^7 steps. Only by keeping m in the bound can you see that the naive version is acceptable for tiny m and fatal for large m.

## Lab

- **1351** Count Negative Numbers in a Sorted Matrix (derive): write three versions with three different costs before reading any hint. Expected: brute force O(mn); a binary search in each row O(m log n); a walk from one corner that discards a whole row or column at every step, O(m + n). For [[3, 2, -1], [1, -1, -2], [-1, -2, -3]] the answer is 6.
- **2215** Find the Difference of Two Arrays: state the cost with both sizes. Expected: nested membership tests O(n x m); sets O(n + m) expected. For [4, 1, 4, 7] and [7, 2, 2] the answer is [[1, 4], [2]] (each list in any order).

> [!know]
> You now know how to state an honest, tight bound: which case it covers, which variables it depends on, and what O, Omega and Theta each promise.

=== primer | How much memory does a program really use? | 14 min
goal: Count auxiliary space including the recursion stack and copies, keep it separate from the output, and estimate the real bytes of Python data
tag: cost-space | Space accounting
link: Sedgewick and Wayne: 1.4 Analysis of Algorithms | https://algs4.cs.princeton.edu/14analysis/ | 10 min: the 'Memory usage' part near the end of the page (object, array and string sizes in Java); compare each figure with the Python sizes on this card
practice: 119, 557

> [!key]
> Space complexity counts the extra memory an algorithm needs as the input grows: **auxiliary** space for variables, copies, buffers and the recursion stack, stated separately from the input and the output. An algorithm is **in place** when its auxiliary space is O(1) (O(log n) for a recursion stack is usually accepted). In Python, count bytes too: a list stores 8-byte references, and every number it refers to is a separate object of 24 to 32 bytes.

## Intuition

Working at a desk: the input is the pile of books on the shelf, the output is the report you hand in, and auxiliary space is the desk area you clear to work. Two people can write the same report, one with three sticky notes (O(1) extra), one by photocopying every book first (O(n) extra). When memory is the constraint, desk space is what you minimise.

## How it works

### What to count

- **Variables and buffers** you allocate: a set of seen values is O(n); a 26-slot letter count is O(1) because its size is fixed.
- **Copies**: slicing (`a[1:]`), `sorted(a)` (a new list), `list(d)`, and every string operation, because strings are immutable and each "change" builds a new string.
- **The recursion stack**: each active call keeps a frame alive. A recursion n levels deep uses O(n) space even if each call allocates nothing; balanced divide and conquer stays O(log n) deep.
- **The output**, stated separately: returning n strings needs O(n) space whatever you do, so the interesting figure is the auxiliary space.

Count what is alive **at the same moment** (the peak), not everything ever allocated. A loop that builds and drops a temporary list of size n on each of n iterations costs O(n^2) time but only O(n) space.

### Reuse instead of copy

The main way to save space is to keep only the state that later steps still need. A grid computation that looks only at the previous row keeps one row, not the whole table (a **rolling array**, traced below). An in-place algorithm overwrites positions once they are no longer needed (reversing with two indices, compacting with a write pointer). A generator yields items one at a time instead of building a list.

### Python's real bytes

Measured with `sys.getsizeof` on 64-bit CPython 3.12:

| Object | Bytes |
|---|---|
| One reference inside a list or tuple | 8 |
| Empty list | 56 (plus 8 per slot, including spare capacity) |
| `int` below 2^30 in size | 28 (values -5 to 256 are shared, cached objects) |
| `int` near 2^100 | 40 |
| `float` | 24 |
| Tuple of two items | 56 |
| Empty dict / empty set | 64 / 216 |

So `list(range(10**6))` needs about 8 MB of references plus about 28 MB of int objects; `tracemalloc` reported 40 MB in our run. The same numbers in an `array.array("q")` took 8.2 MB, and a NumPy int64 array takes 8 MB. A 10^4 x 10^4 table stored as nested Python lists holds 10^8 references, 800 MB before counting a single distinct int object: a table of that shape must be rolled or vectorised.

## Cost

Two examples, with the space derived step by step:

- `sum([x * x for x in range(n)])` builds the whole list before adding: O(n) auxiliary, a 40 MB peak for n = 10^6 in our run. `sum(x * x for x in range(n))` streams one value at a time: O(1) auxiliary, a peak under 1 kB.
- `def total(a): return 0 if not a else a[0] + total(a[1:])` goes n levels deep, and level k holds its own slice of n - k items. At the deepest point all of them are alive: n + (n - 1) + ... + 1, about n^2/2 references, so O(n^2) space and O(n^2) time for the copying. Passing an index instead of a slice makes it O(n) stack and O(n) time; a loop makes it O(1) space.

## When to use it

Check space whenever n times the per-item size approaches the memory limit (online judges often allow 256 MB; a list of 10^7 distinct Python ints is about 400 MB), whenever recursion depth can grow with n, and whenever data is streamed (logs, files, sockets) so that holding it all is not an option. Do not chase O(1) space at the cost of time or clarity when memory is plentiful: a set that makes the code O(n) is usually the right trade against an O(1)-space O(n^2) scan.

## Worked trace

Count the right-or-down paths from the top-left to the bottom-right of a 3 x 4 grid, keeping a single row. Invariant: while row r is being built, cells left of j already hold row r and cells from j on still hold row r - 1, which is exactly what the update `row[j] = row[j] + row[j - 1]` needs (from above, plus from the left).

```steps
Row 1: one way to reach each cell (keep moving right)
    row  [ 1  1  1  1 ]
---
Row 2, j = 1: from above (old row[1] = 1) plus from the left (new row[0] = 1)
    row  [ 1 {{2}} 1  1 ]
---
Row 2, j = 2: 1 + 2 = 3
    row  [ 1  2 {{3}} 1 ]
---
Row 2, j = 3: 1 + 3 = 4
    row  [ 1  2  3 {{4}} ]
---
Row 3, j = 1: 2 + 1 = 3
    row  [ 1 {{3}} 3  4 ]
---
Row 3, j = 2 and j = 3: 3 + 3 = 6, then 4 + 6 = 10
    row  [ 1  3 {{6}} {{10}} ]
---
Answer 10, which is C(5, 2), using 4 cells instead of a 12-cell table: O(cols) space, O(rows x cols) time
    row  [ 1  3  6 {{10}} ]
```

## Template

```python
import tracemalloc

def peak_bytes(fn, *args):
    """Peak bytes held by Python objects allocated while fn(*args) runs."""
    tracemalloc.start()
    try:
        fn(*args)
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()

def grid_paths(rows, cols):
    """Right/down paths through a rows x cols grid, keeping one row: O(cols) space."""
    row = [1] * cols
    for _ in range(rows - 1):
        for j in range(1, cols):
            row[j] += row[j - 1]
    return row[-1]

print(grid_paths(3, 4))                                              # 10
print(peak_bytes(lambda n: sum([x * x for x in range(n)]), 10**6))   # about 40 million
print(peak_bytes(lambda n: sum(x * x for x in range(n)), 10**6))     # a few hundred
```

## Pitfalls

- **Forgetting the stack.** A recursion n levels deep is O(n) space, and in Python it also hits the default recursion limit near 1,000.
- **Slicing in recursion.** `f(a[1:])` and `f(a[:mid])` copy; pass `lo, hi` indices instead.
- **Keeping references alive.** Appending every intermediate result to a list "for debugging" turns O(1) space into O(n) or worse.
- **Counting the output as waste.** If the answer has n items, O(n) space is unavoidable; report the auxiliary space separately.
- **`sorted` versus `.sort()`.** `sorted(a)` allocates a new list; `a.sort()` sorts in place, though Timsort can still use up to n/2 temporary references while merging.

## Check yourself

Q: What is the auxiliary space of `def has_neg(a): return bool(a) and (a[0] < 0 or has_neg(a[1:]))` on a list with no negatives, and of a version that passes an index?
A: The slice version keeps up to n frames alive and frame k holds a slice of n - k items, so about n^2/2 references are alive at the deepest point: O(n^2) space (and O(n^2) time for the copies). With `has_neg(a, i)` each frame holds O(1), so the stack is O(n); a plain loop needs O(1).

Q: Merge sort and heapsort both take O(n log n) time. Which needs only O(1) auxiliary space, and what does the other need?
A: Heapsort rearranges the array in place: O(1) auxiliary. Merge sort needs an O(n) buffer for merging plus an O(log n) stack, which is the price of its stability.

Q: A computation over two strings of length 10^4 fills a table where each row reads only the previous row. Estimate the memory of the full table as nested Python lists, and of two rolling rows.
A: The full table has 10^8 cells: 800 MB of references alone, and up to about 3.6 GB if the cells hold distinct int objects. Two rows of 10^4 cells are about 160 kB of references plus the ints, under 1 MB. Rolling turns impossible into trivial.

## Lab

- **119** Pascal's Triangle II: build row k in a single list of length k + 1. Expected: O(k^2) time and O(k) extra space; rowIndex 5 gives [1, 5, 10, 10, 5, 1]. If your one-list version produces wrong numbers, compare the direction of your inner loop with the invariant in the worked trace: which old value does each update still need?
- **557** Reverse Words in a String III: reverse each word, keep the word order. Expected: O(n) time; the output needs O(n) space because strings are immutable, and the list of reversed pieces is O(n) auxiliary; "deep sea fish" becomes "peed aes hsif".

> [!know]
> You now know how to count auxiliary space, including the stack and hidden copies, and estimate the real memory of Python data.

=== primer | Why is list.append O(1) when a resize copies the whole list? | 16 min
goal: Prove amortised bounds with the aggregate and credit methods, and recognise the "each element is moved a constant number of times" argument in loops that look quadratic
tag: cost-amortised | Amortised analysis
link: Jeff Erickson: Amortized Analysis notes (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/09-amortize.pdf | 25 min: PDF pages 1-5, the binary counter analysed four ways (summation, taxation, charging, potential), then '9.5 Generalities and Warnings' on page 7
link: CPython source: list_resize in listobject.c | https://github.com/python/cpython/blob/main/Objects/listobject.c | 5 min: search the page for 'over-allocates proportional' and read that comment and the growth formula just below it
practice: 1656, 1381

> [!key]
> An **amortised** bound limits the total cost of any sequence of n operations, then divides by n. A dynamic array that doubles when full copies 1 + 2 + 4 + ... < 2n elements during n appends, so each append is O(1) amortised although a single append can cost O(n). No probability is involved: the bound holds for every sequence. The same accounting, "each element is moved only a constant number of times", explains two-stack queues, binary counters, sliding windows and monotonic stacks.

## Intuition

An annual rail pass costs a lot once, but spread over every journey of the year it is cheap per trip. Amortised analysis does the same accounting for code: a rare expensive operation is paid for by the many cheap ones around it, provided the expensive one cannot happen too often.

## How it works

### Aggregate method: add up, then divide

A dynamic array keeps `size` items in a block of `capacity` slots. Appending into a free slot costs one write. Appending when full first allocates a block twice as big and copies all `size` items across. Starting from capacity 1, copies happen when the size reaches 1, 2, 4, ..., up to the largest power of two below n, so the copies total 1 + 2 + 4 + ... + 2^k < 2^(k+1) <= 2n. Adding the n writes, n appends cost under 3n steps: **O(1) amortised per append**.

### Credit (banker's) method: pay ahead

Charge every append 3 coins: one pays for its own write and two are saved with the new item. When a block of capacity c fills up, the c/2 items added since the last resize hold c coins between them, exactly enough to copy all c items. The bank never goes negative, so 3 coins per append pays for everything, including the copies.

### Any constant growth factor works; a constant increment does not

Growing by a factor r > 1 costs about 1/(r - 1) copies per append on average: about 1 for r = 2 and 2 for r = 1.5. Growing by a fixed number of slots does not work: with +16 the copies are 16 + 32 + 48 + ..., about n^2/32 in total, roughly 3,100 copies per append at n = 10^5 in our simulation, and growing linearly with n.

CPython grows lists by about one eighth: `new_allocated = (newsize + (newsize >> 3) + 6) & ~3`. Reading capacities from `sys.getsizeof` while appending reproduces the comment in the source: 0, 4, 8, 16, 24, 32, 40, 52, 64, 76, 92. A factor of about 1.125 means at most about 8 copies per append on average (our simulation of the rule gave 8.0 at 10^5 appends and 8.5 at 10^6), often fewer because `realloc` can sometimes extend the block in place. The payoff is memory: just after a resize at most about 11% of the slots are spare, against up to 50% with doubling.

### Shrinking without thrashing

If an array halved its capacity as soon as it fell to half full, alternating one append and one pop at that boundary would resize every time: O(n) per operation. The fix is a gap: shrink only when the array is a quarter full, so Theta(n) cheap operations separate any two resizes. CPython reallocates a list smaller only when its size falls below half the capacity, and keeps an eighth of slack when it does, so there is room to move in both directions.

### Two stacks make a queue

Push onto `inbox`. To pop, if `outbox` is empty, move everything from `inbox` onto `outbox` (which reverses the order, so the oldest item ends on top), then pop from `outbox`. One pop can move n items, but each item is pushed onto inbox once, moved once and popped once: a constant number of stack operations per item, so n queue operations cost O(n) in total.

### The binary counter

Incrementing a binary counter flips the trailing 1s to 0 and one 0 to 1. A single increment can flip log2 n bits, but bit 0 flips on every increment, bit 1 on every second, bit i on every 2^i-th: n + n/2 + n/4 + ... < 2n flips in total. Increments 1 to 8 flip 1, 2, 1, 3, 1, 2, 1, 4 bits: 15 in all, below 16.

### "Each element enters and leaves once"

The same argument explains loops that look quadratic. In a sliding window the left edge only moves right, so the inner `while` that advances it runs at most n times over the whole scan, not n times per step. In a monotonic stack every element is pushed once and popped at most once. Count the total over the run, not the worst single iteration.

## Cost

- Doubling array: n appends cost fewer than 3n element writes including copies, O(1) amortised; one append is O(n) in the worst case. In our run, 10^5 appends made 131,071 copies, 1.31 per append.
- Two-stack queue: n operations cost at most 4n stack operations; a single pop can cost O(n).
- Binary counter: n increments flip fewer than 2n bits (199,994 for n = 10^5); a single increment can flip O(log n).

## When to use it

Reach for amortised analysis whenever an operation is usually cheap but occasionally rebuilds, refills or resizes, and whenever a nested loop's inner pointer never moves backwards. Do **not** rely on an amortised bound when each operation has its own deadline: a request that happens to trigger a 1 GB resize is slow however good the average is. That is why Redis rehashes its hash tables a few buckets at a time during normal operations, and why Go splits each map into tables of at most 1,024 entries, so that a single growth step copies at most 1,024 entries.

## Worked trace

Nine appends into a doubling array that starts with capacity 1:

```steps
append a: a slot is free
    slots [{{a}}]
    capacity 1, copied 0, total copies 0
---
append b: full, so allocate 2 slots and copy 1 item first
    slots [a {{b}}]
    capacity 2, copied 1, total copies 1
---
append c: full, allocate 4 and copy 2
    slots [a b {{c}} .]
    capacity 4, copied 2, total copies 3
---
append d: a slot is free, no copy
    slots [a b c {{d}}]
    capacity 4, copied 0, total copies 3
---
append e: full, allocate 8 and copy 4
    slots [a b c d {{e}} . . .]
    capacity 8, copied 4, total copies 7
---
append f, g, h: three cheap appends fill the block
    slots [a b c d e {{f g h}}]
    capacity 8, copied 0, total copies 7
---
append i: full, allocate 16 and copy 8
    slots [a b c d e f g h {{i}} . . . . . . .]
    capacity 16, copied 8, total copies 15
---
After 9 appends: 15 copies + 9 writes = 24 <= 3 x 9. Each expensive append doubles the room for cheap ones
    copies so far: 1 + 2 + 4 + 8 = 15 < 2 x 9
```

## Template

```python
class DynamicArray:
    """A list-like array that doubles its capacity when full and counts element copies."""

    def __init__(self):
        self.capacity, self.size = 1, 0
        self.slots = [None]
        self.copies = 0

    def append(self, x):
        if self.size == self.capacity:            # full: move everything to a bigger block
            self.capacity *= 2
            bigger = [None] * self.capacity
            for i in range(self.size):
                bigger[i] = self.slots[i]
            self.copies += self.size
            self.slots = bigger
        self.slots[self.size] = x
        self.size += 1

    def __getitem__(self, i):
        if not 0 <= i < self.size:
            raise IndexError(i)
        return self.slots[i]

    def __len__(self):
        return self.size


class TwoStackQueue:
    """FIFO queue from two stacks: amortised O(1) per operation."""

    def __init__(self):
        self.inbox, self.outbox = [], []

    def push(self, x):
        self.inbox.append(x)

    def pop(self):
        if not self.outbox:                       # refill only when empty
            while self.inbox:
                self.outbox.append(self.inbox.pop())
        return self.outbox.pop()

    def __len__(self):
        return len(self.inbox) + len(self.outbox)


arr = DynamicArray()
for x in range(100_000):
    arr.append(x)
print(arr.copies)                                 # 131071, below 2 x 100000
```

## Pitfalls

- **Amortised is not average.** There is no probability: the bound holds for every sequence, but it limits the total, not each operation.
- **The slow operation still happens.** Latency-sensitive code (games, trading, request handlers) may need incremental resizing, or preallocation such as `[None] * n` when the size is known.
- **Additive growth.** Growing by a fixed number of slots makes appends O(n) amortised.
- **Shrinking at half full** makes alternating push and pop thrash.
- **Replaying the expensive state.** If a structure can be copied, undone or persisted, an adversary can force the "rare" expensive step again and again from the same state, and the amortised bound no longer holds.
- **Refilling too eagerly.** In a two-stack queue, moving items into `outbox` while it still holds items breaks FIFO order; refill only when it is empty.

## Check yourself

Q: Continue the trace: after 17 appends to the doubling array, what are the capacity and the total number of copies? Is it below 2n?
A: The 17th append finds the array full at 16 items, allocates 32 slots and copies 16, so capacity 32 and total copies 1 + 2 + 4 + 8 + 16 = 31, below 2 x 17 = 34.

Q: Why can no element move from inbox to outbox twice in a two-stack queue, and why does that give amortised O(1)?
A: Once an element is in outbox it only leaves by being popped as the front of the queue; nothing ever moves it back to inbox. So each element is pushed once, moved once and popped once: at most 4 stack operations per element over its lifetime, so n queue operations cost O(n) in total.

Q: A colleague grows a buffer by 1,000 slots each time it fills. Roughly how many copies do 10^6 appends make, and what is the fix?
A: Copies happen at sizes 1,000, 2,000, ..., 999,000: 1,000 x (1 + 2 + ... + 999), about 5 x 10^8 copies, or about 500 per append, and the figure grows in proportion to n. Grow by a constant factor (x 1.5 or x 2) instead.

Q: How many bits do increments 1 to 16 of a binary counter flip in total, and why is it below 32?
A: 31. Bit 0 flips 16 times, bit 1 eight times, bit 2 four, bit 3 twice and bit 4 once (when the counter reaches 16). In general bit i flips floor(n / 2^i) times, so the total is below n(1 + 1/2 + 1/4 + ...) = 2n.

## Lab

- **1656** Design an Ordered Stream: a pointer that only ever moves forward. Expected: O(n) total work for n inserts, so O(1) amortised per insert, even though a single insert can return a long run of values; with n = 3, inserting ids 3, 1, 2 (values "c", "a", "b") returns [], then ["a"], then ["b", "c"].
- **1381** Design a Stack With Increment Operation (stretch): first write `increment(k, val)` as a loop over the bottom k items, then make it O(1). Expected: every operation O(1) in the worst case, not just amortised, by storing pending increments lazily; push 1, push 2, increment(2, 5), pop, pop returns 7 then 6.

> [!know]
> You now know how to prove that a sequence of operations is cheap per operation even when single operations are expensive, and when that guarantee is not enough.

=== primer | Why does scanning an array beat chasing pointers when both are O(n)? | 14 min
goal: Explain the memory hierarchy, cache lines and locality, and predict which of two traversals with equal Big-O is faster
tag: cost-locality | Locality and caches
link: Algorithmica: Memory Hierarchy | https://en.algorithmica.org/hpc/external-memory/hierarchy/ | 10 min: the table of latency and bandwidth for each level, from registers down to disk
link: Algorithmica: Cache Lines | https://en.algorithmica.org/hpc/cpu-cache/cache-lines/ | 10 min: the strided-loop experiment showing that memory moves in 64-byte lines, so touching one byte costs as much as touching its neighbours

> [!key]
> The word-RAM model behind Big-O charges every memory access one step. That is right for growth and wrong by up to 100x in practice: a value already in the L1 cache arrives in about a nanosecond, one in main memory in about 100. Memory moves in 64-byte **cache lines** and the hardware prefetches sequential lines, so code that walks memory in order (arrays, row by row) runs several times faster than code that jumps around (linked nodes, column by column, shuffled order) with exactly the same operation count.

## Intuition

A library with a reading desk: fetching a book from the stacks takes minutes, but each trip brings back the whole shelf section. If the next books you need are neighbours on that shelf, they are already on your desk. Reading in shelf order costs one trip per section; reading in random order costs one trip per book. Same number of books, very different afternoon.

## How it works

### The model and the machine

Algorithm analysis uses the **word-RAM**: memory is one huge array of machine words, and reading or writing any address costs one step. That is why `a[i]` is O(1): the address is the base address plus i times the element size, one multiplication and one load. Real hardware adds small, fast copies of recently used memory close to each core:

| Level | Typical size | Latency, roughly |
|---|---|---|
| L1 cache | 32 to 64 kB per core | 1 ns |
| L2 cache | 0.5 to 2 MB per core | 3 to 5 ns |
| L3 cache | tens of MB, shared | 10 to 40 ns |
| Main memory | GBs | 80 to 100 ns |
| SSD random read | TBs | about 100 µs |

One miss to main memory costs as much as about a hundred additions. Sequential streams are different: the prefetcher recognises the pattern and loads lines before you ask, so a scan runs at bandwidth (tens of GB/s) rather than paying the latency for every line.

### Cache lines and locality

Memory moves in 64-byte lines on most x86 and ARM processors (Apple's M-series chips use 128 bytes). Reading one 8-byte value brings its seven neighbours along. **Spatial locality** means using those neighbours next; **temporal locality** means reusing data while it is still cached.

### Contiguous versus linked

An array keeps its elements side by side: a scan touches each line once, in order. A linked list keeps nodes wherever the allocator put them, and each `node.next` is a load from an address the CPU cannot know until the previous load finishes, so misses cannot overlap.

### What this means in Python

A Python list is a contiguous array of **references**; the objects live elsewhere on the heap. Objects created one after another usually sit close together, so scanning a freshly built list is fairly cache-friendly, but shuffle the list and the same objects are visited in random address order. `array.array` and NumPy store raw values contiguously, 8 bytes per float with no object headers, which is smaller and faster to scan, and NumPy's loops run in C. A nested list `grid[i][j]` is a list of separate row lists, so walking row by row stays within one row's references at a time.

## Cost

Measured on a typical laptop, roughly (CPython 3.12, NumPy 1.26), with identical operation counts in each pair:

| Experiment | In order | Out of order | Ratio |
|---|---|---|---|
| `sum` over 10^7 floats: list in creation order vs the same objects shuffled | 138 ms | 458 ms | 3.3x |
| The same at 10^6 floats | 7.5 ms | 18 ms | 2.4x |
| NumPy 4000 x 4000: sum each row slice vs each column slice | 33 ms | 122 ms | 3.7x |
| Nested lists 2000 x 2000, `grid[i][j]`: row-major vs column-major double loop | 524 ms | 872 ms | 1.7x |
| Python loop over a list of 10^6 ints vs walking 10^6 linked `Node` objects | 58 ms | 109 ms | 1.9x |

Two lessons hide in the table. The gap grows with size, because small data fits in cache whatever the order. And pure-Python loops show smaller gaps, because tens of nanoseconds of interpreter work per step hide part of each miss; C loops, where the work per element is tiny, expose the full cost.

## When to use it

Think about locality when the data is bigger than the caches (more than a few MB), when a loop is hot, and when choosing between structures with equal Big-O: prefer arrays to linked lists, traverse 2D data in the order it is stored (row by row for nested lists and C-ordered NumPy arrays), and keep the fields you scan together in their own array (a struct of arrays). On disk the same idea becomes B-trees with wide nodes and log files written sequentially. Do not tune access order for loops over a few thousand items: it all fits in cache, and in Python choosing a C built-in matters far more.

## Worked trace

A 4 x 8 matrix of 8-byte floats stored row by row, so each row fills exactly one 64-byte line. Pretend the cache holds only 2 lines (real caches hold thousands, but a large matrix overflows them in the same way):

```steps
Row-major, read M[0][0]: miss, so line 0 (all of row 0) is loaded
    cache [ {{row0}}  -   ]     reads 1, misses 1
---
M[0][1] to M[0][7] are all in line 0: seven hits
    cache [ row0  -   ]         reads 8, misses 1
---
M[1][0]: miss, load row 1, then seven hits
    cache [ row0 {{row1}} ]     reads 16, misses 2
---
Rows 2 and 3 the same way: one miss per eight reads
    cache [ {{row2}} {{row3}} ] reads 32, misses 4
---
Column-major instead, read M[0][0] then M[1][0]: two misses fill the cache
    cache [ {{row0}} {{row1}} ] reads 2, misses 2
---
M[2][0] and M[3][0]: two more misses evict rows 0 and 1
    cache [ {{row2}} {{row3}} ] reads 4, misses 4
---
M[0][1]: row 0 was evicted, so it misses again; every column-order read misses
    cache [ {{row0}} row3 ]     reads 5, misses 5
---
Column-major total: 32 reads and 32 misses, against 4 misses row-major. Same Big-O, 8 times the memory traffic
    row-major 4 misses     column-major 32 misses
```

## Template

```python
import random
import timeit

def order_effect(n=10**6, seed=1):
    """Time sum() over the same float objects in creation order and in shuffled order."""
    in_order = [float(i) for i in range(n)]
    shuffled = in_order[:]
    random.Random(seed).shuffle(shuffled)
    t_in = min(timeit.repeat(lambda: sum(in_order), number=5, repeat=5)) / 5
    t_sh = min(timeit.repeat(lambda: sum(shuffled), number=5, repeat=5)) / 5
    return t_in, t_sh

t_in, t_sh = order_effect()
print(f"in order {t_in * 1e3:.1f} ms, shuffled {t_sh * 1e3:.1f} ms, ratio {t_sh / t_in:.1f}")
```

## Pitfalls

- **Trusting Big-O alone when classes tie.** Two O(n) traversals can differ by 3x or more.
- **Column loops over row-major data**: nested lists, C-ordered NumPy arrays, images.
- **Linked structures in Python.** Each node is a full object and each step a dependent load plus interpreter work; a list or a deque is almost always faster.
- **Benchmarking tiny inputs.** Everything fits in L1 or L2, so locality effects vanish; test at realistic sizes.
- **Tuning order before choosing tools.** In Python, moving the loop into C (`sum`, `sorted`, NumPy) usually matters more than access order. Measure first.

## Check yourself

Q: A NumPy array of shape (4000, 4000) is stored in C order. Which is faster, `sum(M[i, :].sum() for i in range(4000))` or `sum(M[:, j].sum() for j in range(4000))`, and why?
A: The row version. Each row slice is 4000 contiguous floats streamed line by line; each column slice reads one float from each of 4000 rows, 32,000 bytes apart, so almost every element needs its own cache line. We measured about 33 ms against 122 ms.

Q: Why do databases index data with B-trees holding hundreds of keys per node rather than with binary search trees?
A: Each node visit costs one expensive transfer (a disk page, or a run of cache lines), whereas comparisons inside a node are cheap and contiguous. With B keys per node the height is about log_B n instead of log2 n: for n = 10^9 and B = 500, about 4 levels instead of 30, so about 4 transfers per lookup.

Q: You store 10^6 points and repeatedly need the mean x. Compare a list of `(x, y)` tuples with two `array('d')` arrays for memory and scan speed.
A: The tuple list holds 10^6 references (8 MB), 10^6 tuples (56 bytes each) and 2 x 10^6 float objects (24 bytes each): about 112 MB, with the x values scattered across the heap. Two arrays hold raw doubles side by side: 16 MB, and the mean of x reads 8 MB sequentially. The struct of arrays wins on both counts.

## Lab

No tracker problem drills this directly; run the experiment instead.

- Run `order_effect()` from the template at n = 10^5, 10^6 and 10^7 (the last needs about 400 MB; use 3 x 10^6 if memory is tight). Expected: a ratio near 1.5 at 10^5, roughly 2 to 3 at 10^6 and roughly 3 to 4 at 10^7, growing as the data outgrows the caches.
- Time the row-slice and column-slice sums of a 4000 x 4000 NumPy array, and `M.sum()`. Expected: column slices roughly 3 to 4 times slower than row slices, and `M.sum()` faster than both.

> [!know]
> You now know why memory access order changes speed at equal Big-O, and how to lay out and traverse data so that it streams through the caches.

=== primer | What do Python's built-in operations really cost? | 16 min
goal: Quote the cost of common list, dict, set, deque, str, heapq and bisect operations, spot the expensive ones inside loops, and replace them with the right container
tag: cost-python | Python cost sheet
link: Python docs: Time complexity of operations on built-in types | https://docs.python.org/3/builtins/time-complexity.html#list | 15 min: the tables for list, dict, set and str, then the Notes (amortised appends, shifting on insert and pop, why concatenating in a loop is quadratic)
link: PEP 8: Programming Recommendations | https://peps.python.org/pep-0008/#programming-recommendations | 2 min: the first bullet, on not relying on CPython's in-place string concatenation
practice: 2215, 557

> [!key]
> Python hides loops inside innocent-looking operations. Indexing, `len`, `append`, `pop()` from the end and dict or set lookups are O(1) (amortised, or on average); `x in list`, `insert(0, x)`, `pop(0)`, slicing, `bisect.insort` and string concatenation are O(n). Built-ins run their loops in C, roughly 5 to 50 times faster per element than a Python loop. Choose the container by the operations you need, and keep hidden O(n) calls out of loops.

## Intuition

A shop has a price list. Paying item by item at the till is a Python loop; a bulk order processed in the warehouse is a built-in like `sum` or `sorted`, done at machine speed. Knowing the price list lets you find the one line that turns a sub-second program into a ten-minute one.

## How it works

### The cost sheet (CPython; n is the container's length)

| Structure | O(1) | O(log n) | O(n) or more |
|---|---|---|---|
| `list` | `a[i]`, `a[i] = x`, `len`, `append` (amortised), `pop()` | | `x in a`, `index`, `count`, `remove`, `insert(i, x)` and `pop(i)` (O(n - i)), `a[i:j]` (O(j - i)), `a + b`, `min`, `max`, `sum`; `sort` is O(n log n), O(n) on sorted or reversed input |
| `dict`, `set` | get, set, `in`, delete (on average) | | iteration and copy; any single operation in the worst case; `s & t` is O(min(len s, len t)), `s \| t` O(len s + len t) |
| `collections.deque` | `append`, `appendleft`, `pop`, `popleft`, `d[0]`, `d[-1]` | | `d[i]` near the middle, `x in d`; `rotate(k)` is O(k) |
| `str`, `bytes` | `s[i]`, `len` | | `s + t`, `s[i:j]`, `t in s`, `find`, `split`, `replace`, `join` (total length); building by `+=` in a loop is quadratic in general |
| `heapq` on a list | `h[0]` (the minimum) | `heappush`, `heappop`, `heapreplace` | `heapify` O(n); `nsmallest(k, xs)` O(n log k) |
| `bisect` on a sorted list | | `bisect_left`, `bisect_right` | `insort`: O(log n) to find the place, then O(n) to shift |

### Why each surprise happens

- **A list is one contiguous block of references** with spare room at the end (the amortised card). The end is cheap; the front is not: `insert(0, x)` and `pop(0)` move every other reference by one slot. That is a fast `memmove`, but still n moves.
- **A deque is a doubly linked list of 64-slot blocks.** Both ends are O(1) and nothing else moves; the price is that `d[i]` must walk block by block towards the middle.
- **dict and set are hash tables**: O(1) on average when hashing spreads keys well (the hashing module shows when it does not). A `str` caches its hash, so repeated lookups with the same string object do not rehash it.
- **Strings and bytes are immutable**, so `s + t` builds a new object of length len(s) + len(t). CPython has a special case: when `s` is a `str` with no other references, `s += t` may resize it in place, so a loop of `s += piece` is often linear in practice. The trick is fragile: a second reference to `s`, a `bytes` object, or another Python implementation such as PyPy makes the loop quadratic, and both the docs and PEP 8 tell you not to rely on it. Collect pieces in a list and `"".join` them.
- **`bisect.insort`** finds the slot in O(log n) and then inserts into a list: O(n). Inserting n items one at a time is O(n^2); a heap, or one sort at the end, is O(n log n).
- **Built-ins run in C.** A Python-level step costs tens of nanoseconds; the same step inside `sum`, `sorted`, `max`, `str.join`, `set(...)`, `x in list` or `Counter(...)` costs a few. An O(n log n) `sorted` can beat an O(n) Python loop.
- **Integers have arbitrary precision.** Arithmetic on small ints is O(1); on numbers with thousands of digits it is not.

## Cost

Measured on a typical laptop, roughly (CPython 3.12):

| Operation | Time |
|---|---|
| `x in list` with 10^6 items, value absent | 14 ms |
| `x in set` with 10^6 items | 30 to 40 ns, about 400,000 times faster |
| `d[k]` | about 50 ns |
| `sum(a)` over 10^6 ints, and the same as a Python `for` loop | 9 ms and 50 ms |
| `sorted` on 10^6 random floats, and on already sorted ones | 620 ms and 29 ms |
| Drain 10^5 items with `list.pop(0)`, and with `deque.popleft()` | 2.7 s and 5 ms |
| 10^5 calls of `bisect.insort`, and of `heapq.heappush` | 2.6 s and 13 ms |
| `bytes +=` 10^5 times, and 2 x 10^5 times | 0.31 s and 1.43 s (quadratic) |
| `str +=` 4 x 10^5 times on a local, and `"".join` of the same pieces | 30 ms and 17 ms |
| `str +=` 4 x 10^4 times while a list also holds every partial string | 0.94 s (quadratic) |

## When to use it

| You need | Use | Avoid |
|---|---|---|
| Membership tests, de-duplication | `set`, `dict` | `x in list` inside a loop |
| FIFO queue, BFS frontier, sliding window | `collections.deque` | `list.pop(0)` |
| Stack | `list` with `append` and `pop()` | |
| The smallest or largest, again and again | `heapq` | `min(a)` in a loop, `insort` |
| Sorted data, many queries, few inserts | a sorted `list` with `bisect` | |
| Sorted data with many inserts and deletes | `sortedcontainers.SortedList` (third party) | `insort` for large n |
| Counting | `collections.Counter` | `list.count` in a loop |
| Building text | a list of pieces and one `"".join` | `+=` on `bytes`, or on a shared `str` |

## Worked trace

Why `pop(0)` on a list costs O(n) but `popleft()` on a deque costs O(1):

```steps
A list stores its references in one block, with index 0 at the start
    list   [ {{a}} b c d e f ]
---
list.pop(0) returns a, then shifts the other five references one slot left
    list   [ {{b c d e f}} . ]          5 moves
---
pop(0) again: four moves. Draining n items moves (n-1) + (n-2) + ... + 0, so O(n^2)
    list   [ {{c d e f}} . . ]          4 moves
---
A deque of a..f: one 64-slot block, items in slots 32 to 37, leftindex = 32
    block  [ ... {{a}} b c d e f ... ]  leftindex 32
---
deque.popleft() returns a and only increments leftindex: no item moves
    block  [ ... . {{b}} c d e f ... ]  leftindex 33
---
popleft() again: leftindex 34. When a block empties it is unlinked, still O(1); draining n items is O(n)
    block  [ ... . . {{c}} d e f ... ]  leftindex 34
```

## Template

Cost-aware idioms in one place, each replacing a hidden O(n) with the right tool:

```python
from bisect import bisect_left
from collections import Counter, deque
import heapq

def unique_in_order(items):
    """Order-preserving de-duplication: O(n) with a set, not O(n^2) with `in list`."""
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def bfs_order(graph, start):
    """Breadth-first visiting order: deque.popleft is O(1), list.pop(0) would be O(n)."""
    seen, order, queue = {start}, [], deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in graph.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return order

def contains_sorted(sorted_items, x):
    """O(log n) membership test in a sorted list."""
    i = bisect_left(sorted_items, x)
    return i < len(sorted_items) and sorted_items[i] == x

def report(rows):
    """Build text with one join: O(total length)."""
    return "\n".join(f"{name}: {count}" for name, count in rows)

def top_words(words, k):
    """k most common words: building the Counter is O(n); most_common(k) uses a heap, O(n log k)."""
    return Counter(words).most_common(k)

def k_smallest(nums, k):
    return heapq.nsmallest(k, nums)             # O(n log k)
```

## Pitfalls

- `x in some_list` inside a loop: O(n) per check.
- `list.pop(0)`, `list.insert(0, x)` or `del a[0]` used as a queue: use a `deque`.
- `bisect.insort` in a loop over n items: O(n^2); use a heap, or sort once.
- `sorted(...)`, `min(...)` or `len(set(...))` recomputed inside a loop when the data has not changed.
- `+=` on `bytes`, or on a `str` that something else also references: quadratic. Collect the pieces and `join`.
- `list(d)[0]` or `list(s)[i]` to read one item: builds an O(n) list first. Use `next(iter(d))`.
- `Counter.most_common()` with no argument sorts every item, O(n log n); pass k when you need only the top k.

## Check yourself

Q: Which line makes this O(n^2), and what is the fix? `def dedupe(xs): out = []` then `for x in xs: if x not in out: out.append(x)` then `return out`.
A: `if x not in out`: `out` is a list, so each check scans it, up to n checks of up to n items. Keep a `seen` set beside `out` and test `x not in seen`: O(n) in total, with the order kept.

Q: In CPython, a loop of `s += p` over 4 x 10^5 pieces took about as long as `"".join(pieces)`. Why, and why should you still use join?
A: CPython notices `s += t` on a `str` that nothing else references and resizes it in place, so the loop is usually linear. The trick fails when another reference to `s` exists (a list holding it, an attribute, a debugger), for `bytes`, and on implementations such as PyPy, where the loop is quadratic: 0.94 s for only 4 x 10^4 pieces with a second reference in our run. `join` is linear everywhere.

Q: Values arrive one at a time (10^5 of them), and after each arrival you must report how many earlier values are smaller. Why is a list kept sorted with `insort` a poor choice, and what are the alternatives?
A: Each `insort` shifts up to n references, so 10^5 arrivals cost up to about 5 x 10^9 moves (we measured 2.6 s for 10^5 insorts, against 13 ms for heap pushes). Use `sortedcontainers.SortedList`, whose `add` and `bisect_left` are fast in practice, or a Fenwick tree over compressed values (the range-query module), both about O(log n) per arrival.

## Lab

- **2215** Find the Difference of Two Arrays: write the version with sets, then swap one set for a list and time both at n = m = 10^4 (use `timeit`). Expected: the set version is O(n + m) and takes a few milliseconds; the list version is O(n x m) and runs hundreds of times slower (seconds).
- **557** Reverse Words in a String III: build the result two ways, with one `join` and with `+=` on a string. Expected: both look linear in CPython for a local string, for the reason above; only the `join` version is guaranteed O(n). "deep sea fish" becomes "peed aes hsif".

> [!know]
> You now know what Python's containers really charge for each operation, and how to keep hidden O(n) calls out of your loops.

=== primer | How do you measure running time and estimate the growth exponent? | 15 min
goal: Time code reliably with timeit, run a doubling experiment, estimate the exponent from the ratios, and recognise when Big-O misleads at your input sizes
tag: cost-doubling | Doubling experiments
link: Sedgewick and Wayne: 1.4 Analysis of Algorithms | https://algs4.cs.princeton.edu/14analysis/ | 15 min: 'Observations' (the doubling ratio test, with Java code) and 'Mathematical models' up to the table of order-of-growth classifications
link: Python docs: timeit.Timer.repeat | https://docs.python.org/3/library/timeit.html#timeit.Timer.repeat | 5 min: repeat() and autorange(), and the note on why the minimum of the repeats is the number to report
practice: 1588, 1351

> [!key]
> Measure with `timeit`: repeat the run and keep the **minimum**, because noise only ever adds time. Then time at sizes that double. If T(2n)/T(n) is about 2^b, the code grows like n^b: a ratio of 2 means linear, 4 quadratic, 8 cubic, and a little over 2 means n log n. Fit b across several sizes, predict the next size, and check. Big-O gives the slope; measurement gives the constant, and at small n the constant often decides.

## Intuition

Weighing yourself: same scale, same time of day, several readings. One reading tells you little, but how the readings change tells you whether you are gaining. A single timing depends on the machine; how the time changes when n doubles is a property of the code.

## How it works

### Timing correctly

- `time.perf_counter()` is the high-resolution clock for wall time; use it for a single phase of a program.
- `timeit` runs a statement many times with garbage collection switched off and returns total times. `Timer.autorange()` picks a loop count that takes at least 0.2 s, and `Timer.repeat()` repeats the measurement; report `min(...) / number`. Noise (other processes, frequency scaling) only adds time, so the minimum is the cleanest estimate.
- Build inputs outside the timed call, use the same inputs for every variant, and keep the machine quiet; laptops on battery throttle.

### The doubling method

Time the code at n, 2n, 4n and 8n. If T(n) is about a x n^b, then T(2n)/T(n) = 2^b, so **b is about log2 of the ratio**. For n log n the ratio is 2(1 + 1/log2 n), a little above 2 (about 2.12 at n = 10^5), so b comes out near 1.1. With four or more sizes, fit a straight line through the points (log n, log T): its slope is b, and it is much less sensitive to one noisy timing than a single ratio. Then predict: T(10n) is about 10^b x T(n). Run the prediction and compare.

### When Big-O misleads

- **Constant factors.** Same class, very different constants: `sum` over 10^6 ints in 9 ms against 50 ms for a Python loop.
- **Small n.** Below a crossover the "worse" algorithm wins. We timed `x in list` (a C linear scan) against a binary search written in Python, looking up the last element: the scan won up to about 32 to 64 items, while `bisect_left`, which is also in C, won from about 8 to 16 items. Timsort sorts short runs with insertion sort for the same reason.
- **Caches.** Equal operation counts, different memory order: 2 to 4 times apart (the locality card).
- **Drifting exponents.** At small n fixed overheads flatten the curve (b comes out low); when the data stops fitting in cache, b jumps. Measure over the range of n you actually care about.
- **Input shape.** Sorting 10^6 floats took 29 ms when they were already sorted and 620 ms when random; an adversarial hash pattern or a rare resize can change the picture just as much.

## Cost

A doubling experiment's own running time is dominated by its largest size: with b = 2 each size takes four times the previous one, so the last size takes about three quarters of the whole experiment. Choose the starting n so that the largest size takes a few seconds. Fitting the line is trivial: a handful of logarithms and one division.

## When to use it

Measure before optimising (to find what actually grows), to check a complexity claim, to choose between two correct solutions in the same class, and to find crossovers for hybrid algorithms. Do not use timings to *prove* a bound: noise and caches bend the ratios. Derive the cost by counting, then use the experiment to confirm or refute the prediction.

## Worked trace

Doubling `count_zero_pairs` (two nested loops over n items, from the lab) on a busy machine:

```steps
n = 500: 12.5 ms. One number alone says nothing about growth
    n          500
    time      {{12.5 ms}}
---
n = 1,000: 61.6 ms. Ratio 4.9, so b is about log2 4.9 = 2.3
    n          500     1,000
    time      12.5 ms  {{61.6 ms}}
    ratio               4.9    b ~ 2.3
---
n = 2,000: 263 ms. Ratio 4.3, b about 2.1
    n          500     1,000     2,000
    time      12.5 ms  61.6 ms  {{263 ms}}
    ratio               4.9       4.3   b ~ 2.1
---
n = 4,000: 1,194 ms. Ratio 4.5, b about 2.2
    n          500     1,000     2,000     4,000
    time      12.5 ms  61.6 ms  263 ms   {{1,194 ms}}
    ratio               4.9       4.3       4.5
---
Fit over all four sizes: b = 2.18. Quadratic, as the count n(n-1)/2 predicts; noise pushed it slightly above 2
    predict n = 8,000:  1,194 ms x 2^2.18, about 5.4 s
---
Lesson from an earlier run of the same code: one noisy ratio (2.8) suggested b = 1.5. Never conclude from a single pair
    repeat, keep the minimum, fit across sizes
```

## Template

```python
import math
import timeit

def time_it(fn, repeat=3):
    """Best time of one call to fn(), in seconds, with enough loops to beat timer noise."""
    timer = timeit.Timer(fn)
    number, _ = timer.autorange()             # loop count that takes at least 0.2 s
    return min(timer.repeat(repeat=repeat, number=number)) / number

def doubling(name, make, run, sizes):
    """Time run(make(n)) for doubling n; print ratios, exponent estimates and a fitted exponent."""
    print(f"\n{name}")
    rows = []
    for n in sizes:
        data = make(n)
        rows.append((n, time_it(lambda: run(data))))
    for (n0, t0), (n, t) in zip([(None, None)] + rows, rows):
        extra = f"  ratio {t / t0:5.2f}  b ~ {math.log2(t / t0):5.2f}" if t0 else ""
        print(f"  n = {n:>8,}  {t * 1e3:10.3f} ms{extra}")
    xs = [math.log(n) for n, _ in rows]
    ys = [math.log(t) for _, t in rows]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    print(f"  fitted exponent b = {b:.2f}")
    return b
```

## Pitfalls

- **Timing the setup.** Building the input inside the timed call measures the wrong thing.
- **One run, or the mean of runs with outliers.** Repeat and keep the minimum.
- **Microsecond timings.** Timer resolution and call overhead dominate; let `autorange` choose the loop count.
- **Mutating the input in the timed code.** `a.sort()` sorts `a` on the first call; every later repeat measures the already sorted case.
- **Concluding from one pair of sizes.** Fit across four or more.
- **Comparing across machines, Python versions or power states.** Compare variants in the same session.

## Check yourself

Q: Timings at n = 1,000, 2,000, 4,000 and 8,000 are 0.12, 0.49, 1.95 and 7.9 s. Estimate b and predict n = 16,000.
A: The ratios are about 4.1, 4.0 and 4.05, so b is about log2 4 = 2: quadratic. Predict 7.9 x 4, about 32 s.

Q: Why does `timeit.repeat(lambda: data.sort(), number=1, repeat=5)` report a misleading minimum for random data?
A: The first call sorts `data` in place, so the other four sort an already sorted list, which Timsort finishes with n - 1 comparisons in O(n). The minimum therefore measures the sorted case. Time `sorted(data)`, or rebuild the input for each run.

Q: Your O(n log n) solution is slower than a colleague's O(n^2) one on tests where n is at most 50. Is something wrong?
A: Not necessarily. At n = 50, n^2 is 2,500 basic steps and n log2 n about 280, so constant factors decide: an O(n^2) solution with tiny steps or a C-level inner loop can beat an O(n log n) one with heavy Python steps. Big-O predicts the winner as n grows; measure at the sizes that matter.

## Lab

- **1588** Sum of All Odd Length Subarrays (stretch): write the O(n^3), O(n^2) (prefix sums) and O(n) (count, for each index, the odd-length subarrays that contain it) versions, stress-test them against each other on random arrays, then time each with `doubling`. Expected: fitted exponents close to 3, 2 and 1; on [1, 2, 3, 4, 5] all three return 57.
- **1351** Count Negative Numbers in a Sorted Matrix: time your O(mn) and O(m + n) versions on square sorted grids with n = 250 to 2,000. Expected: b near 2 for the brute force and near 1 for the corner walk, and a gap of hundreds of times at n = 2,000.

> [!know]
> You now know how to measure code honestly, estimate its growth exponent with a doubling experiment, and recognise when Big-O does not predict the winner.

=== lab | Doubling experiments: predict, then measure | 45 min
goal: Predict the growth exponent of eight everyday Python snippets, measure them with a doubling experiment, and explain every gap between prediction and measurement
link: Sedgewick and Wayne: 1.4 Analysis of Algorithms | https://algs4.cs.princeton.edu/14analysis/ | 10 min: 'Observations', for the doubling-ratio experiment this lab reproduces in Python

You will predict, then measure, how eight snippets grow: the built-ins you use every day, two classic traps and one surprise. The script takes about two minutes on a typical laptop. Keep the output: later labs reuse the harness.

## Setup

- Python 3.10 or later; nothing to install.
- Close heavy programs and plug the laptop in, because noise and power saving bend the ratios.

## Steps

1. Start a file `doubling.py` with the imports, `time_it` and `doubling` from the Template of the card "How do you measure running time and estimate the growth exponent?". Add `import random` and `from collections import deque` to the imports.
2. Before running anything, copy this table into your notes and fill in the "Predicted b" column (0 for constant, 1 for linear, about 1.1 for n log n, 2 for quadratic). Write one line of reasoning for each.

| Snippet | Predicted b | Measured b | Explanation |
|---|---|---|---|
| 1. `sum(a)` | | | |
| 2. `sorted(a)`, random data | | | |
| 3. count pairs with two nested loops | | | |
| 4a. 100 lookups in a list / 4b. in a set | | | |
| 5. n calls of `list.insert(0, x)` | | | |
| 6a. drain with `list.pop(0)` / 6b. with `deque.popleft()` | | | |
| 7a. `s += "ab"` on a str / 7b. on bytes / 7c. `"".join` | | | |
| 8. build a dict from n items | | | |

3. Append the snippets and the main block below to `doubling.py`, and run `python doubling.py`.

```python
def rand_list(n):
    return [random.randrange(-n, n) for _ in range(n)]


def count_zero_pairs(a):
    count = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if a[i] + a[j] == 0:
                count += 1
    return count


def lookups(container):
    return sum(1 for q in range(100) if q in container)


def insert_front(n):
    a = []
    for i in range(n):
        a.insert(0, i)


def drain_list(n):
    q = list(range(n))
    while q:
        q.pop(0)


def drain_deque(n):
    q = deque(range(n))
    while q:
        q.popleft()


def concat(n):
    s = ""
    for _ in range(n):
        s += "ab"
    return s


def concat_bytes(n):
    s = b""
    for _ in range(n):
        s += b"ab"
    return s


def join(n):
    return "".join(["ab" for _ in range(n)])


def build_dict(a):
    return {x: i for i, x in enumerate(a)}


if __name__ == "__main__":
    random.seed(1)
    big = [100_000, 200_000, 400_000, 800_000]
    small = [10_000, 20_000, 40_000, 80_000]
    doubling("1. sum(a)", rand_list, sum, big)
    doubling("2. sorted(a), random data", rand_list, sorted, big)
    doubling("3. count pairs with two nested loops", rand_list, count_zero_pairs, [250, 500, 1000, 2000])
    doubling("4a. 100 lookups in a list", lambda n: list(range(n, 2 * n)), lookups, big)
    doubling("4b. 100 lookups in a set", lambda n: set(range(n, 2 * n)), lookups, big)
    doubling("5. n calls of list.insert(0, x)", lambda n: n, insert_front, small)
    doubling("6a. drain with list.pop(0)", lambda n: n, drain_list, small)
    doubling("6b. drain with deque.popleft()", lambda n: n, drain_deque, small)
    doubling("7a. s += 'ab' on a str", lambda n: n, concat, big)
    doubling("7b. s += b'ab' on bytes", lambda n: n, concat_bytes, [12_500, 25_000, 50_000, 100_000])
    doubling("7c. ''.join(parts)", lambda n: n, join, big)
    doubling("8. build a dict", rand_list, build_dict, big)
```

4. Copy each fitted exponent into the table. Where the single ratios jump around, run that snippet again and keep the run with the smallest times.
5. Explain every row where measured and predicted b differ by more than about 0.3. Use the cost sheet and the amortised and locality cards; the questions are: is there a hidden loop, a hidden optimisation, or a cache effect?
6. Change one thing and predict first: time `sorted` on `sorted(rand_list(n))` instead of random data, and `x in range(10**9)` instead of a list. Then measure.
7. Write a three-line journal entry: the biggest surprise, why it happens, and the rule you will apply in your own code.

## What you should see

On a typical laptop with CPython 3.12 (your times will differ; the exponents should not by much):

- **sum, join, deque.popleft, list lookups**: b close to 1. Linear, with C-level constants: `sum` over 800,000 ints takes around 10 milliseconds.
- **sorted on random data**: b about 1.1, the n log n signature. On already sorted data b is close to 1 and the times are roughly 20 times smaller, because Timsort finds a single run.
- **Set lookups and `x in range`**: b close to 0; the times hardly move with n (ratios bounce around 1 because the work is tiny).
- **Nested pairs, `insert(0, x)`, `pop(0)` and bytes `+=`**: b about 2 at the larger sizes. At the smallest sizes the ratios can be lower than 4, because `memmove` on data that fits in cache is very fast; that is the drifting exponent from the measuring card.
- **str `+=` on a local variable**: b close to 1, not 2. This is CPython's in-place resize for a string with no other references; bytes have no such trick, which is why 7b is quadratic. Do not rely on it (PEP 8).
- **Building a dict**: b a little above 1 (1.1 to 1.3) at these sizes, because as the table outgrows the caches each insertion costs more cache misses. Still linear in operation count.
- Noise: on a busy machine single ratios can swing between 1.5 and 3 for a linear snippet. The fitted exponent over four sizes is far more stable, which is the point of fitting.

## Check yourself

Q: Snippet 7a measured b = 1.1 but snippet 7b measured b = 2.2. Both build a string of 2n characters by repeated `+=`. Why the difference?
A: For a `str` with no other references, CPython resizes the string in place instead of copying it, so each `+=` costs O(length of the piece) amortised. `bytes` objects do not get this treatment, so every `+=` copies the whole buffer: 2 + 4 + ... + 2n characters in total, Theta(n^2).

=== practice
- 1732 core
  cue: You are given the changes between consecutive points, and the question is about the points themselves.
  hint: If you knew every altitude, the answer would be a max. Can each altitude be computed from the previous one in constant time, without storing the others?
  insight: The altitude after i steps is the running sum of the first i gains, and the start altitude 0 counts too. Keep the running sum and the best value seen so far in one pass: n additions and comparisons, no list of altitudes.
  cost: O(n) time, O(1) extra space
  pattern: cost-count
- 2073 core
  cue: People rejoin the back of a queue after each purchase, and you only need the moment one particular person finishes.
  hint: A second-by-second simulation is correct, but its cost depends on the ticket values, not just n. How many tickets does each other person buy before person k is done?
  insight: Person k finishes on their t[k]-th turn. Anyone at or before k in the line gets min(t[i], t[k]) turns by then; anyone after k gets min(t[i], t[k] - 1), because k's last turn comes before theirs in that round. Summing these is O(n), against about sum(t) steps for the simulation.
  cost: O(n) time, O(1) extra space
  pattern: cost-count
- 2215 core
  cue: Two arrays, values that occur in one but not the other, and duplicates must not repeat in the answer.
  hint: Checking `x not in other_list` for every x hides a loop inside a loop. Which structure answers membership in O(1) and drops duplicates for free?
  insight: Turn both arrays into sets; the answers are the set differences s1 - s2 and s2 - s1. Building the sets is O(n + m) and each difference is linear in its left operand, against O(n x m) for list membership tests.
  cost: O(n + m) expected time, O(n + m) space
  pattern: cost-python
- 557 core
  cue: Every word is transformed independently and the spaces stay where they are.
  hint: Strings are immutable, so every concatenation builds a new string. How can you produce each reversed word and assemble the result with linear total work?
  insight: Split on single spaces, reverse each word with a slice, and join the pieces with one `" ".join(...)`. Each character is copied a constant number of times, so the work is O(n); appending character by character with `+=` is only linear thanks to a fragile CPython optimisation.
  cost: O(n) time, O(n) space for the output and the pieces
  pattern: cost-python
- 119 core
  cue: Only one row of a triangle is wanted, and each row is built from the previous one.
  hint: You never need rows older than the previous one. Can a single list of length k + 1 hold the previous row and become the next row, if you choose the order of updates carefully?
  insight: Append a 1, then update `row[j] += row[j - 1]` for j from right to left. Going right to left, `row[j - 1]` still holds the previous row's value when row[j] needs it, exactly the rolling-array invariant. k rows of up to k updates: O(k^2) time in O(k) space.
  cost: O(k^2) time, O(k) extra space
  pattern: cost-space
- 1656 core
  cue: Items arrive out of order and you must release the longest run of consecutive items that is ready, starting from the next one owed.
  hint: One insert can release many values, so a single call is not O(1). What is the total work over all n inserts if the "next owed" index never moves backwards?
  insight: Store each value in an array at its id and keep a pointer to the next id owed. On each insert, advance the pointer while the slot is filled, collecting values. The pointer moves forward at most n times over the whole run, so n inserts cost O(n) in total: O(1) amortised each.
  cost: O(n) total time for n inserts (O(1) amortised per insert), O(n) space
  pattern: cost-amortised
- 1351 derive
  cue: A grid sorted in non-increasing order along every row and every column, and a count of values below zero.
  hint: Brute force is O(mn), and a binary search per row gives O(m log n). Start at a corner where one direction makes values smaller and the other makes them larger. What does one comparison there tell you about a whole row or column?
  insight: Start at the bottom-left. If the value is negative, every value to its right in that row is negative too, so add (n - col) and move up a row; otherwise move one column right. Every step discards a row or a column, so there are at most m + n steps.
  cost: O(m + n) time, O(1) extra space
  pattern: cost-bounds
- 1588 stretch
  cue: A sum over all subarrays of odd length, with a follow-up asking for linear time.
  hint: Instead of enumerating subarrays, ask how many times each a[i] is counted. How many subarrays contain index i, and how many of those have odd length?
  insight: Index i is in (i + 1) x (n - i) subarrays (choose a start at or before i and an end at or after i). The odd-length ones are ((i + 1) x (n - i) + 1) // 2 of them, because start and end positions split almost evenly between equal and different parities. Summing a[i] times that count is O(n), against O(n^3) for brute force and O(n^2) with prefix sums.
  cost: O(n) time, O(1) extra space
  pattern: cost-count
- 1381 stretch
  cue: A stack with an operation that changes the bottom k elements, where a loop over k items per call is too slow for the worst case.
  hint: Do you need the incremented values now, or only when each element is popped? Where could a pending increment wait so that pops can pick it up and pass it on?
  insight: Keep an array `inc` beside the stack. `increment(k, val)` adds val to `inc[min(k, size) - 1]`. `pop` returns `stack[top] + inc[top]`, then adds `inc[top]` to `inc[top - 1]` (the increment still applies to everything below) and clears it. Every operation is O(1) in the worst case.
  cost: O(1) per operation, O(maxSize) space
  pattern: cost-amortised
