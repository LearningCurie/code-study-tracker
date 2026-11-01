---
key: correct
name: Correctness: invariants, testing and debugging
stage: found
summary: Say exactly what code must do, prove loops and greedy choices with invariants and exchange arguments, then attack your own code with edge cases, a stress-testing harness and property-based tests.
why: Code that passes the examples is not code that is correct. This module gives you the two halves of trusting an algorithm. The first is reasoning: a contract that says what "correct" means, a loop invariant and a variant that prove a loop right and finite, region invariants for in-place rearrangements, and exchange arguments for greedy choices. The second is attack: an edge-case catalogue, a reusable stress harness that compares a fast solution with a brute force on thousands of random inputs and shrinks the first failure to a tiny case, property-based tests with Hypothesis, and a debugging checklist. Every later module states an invariant and stress-tests against a brute force, so these habits pay off weekly. Production teams work the same way: SQLite's core carries thousands of asserts on preconditions, postconditions and loop invariants, and CPython's sort was patched in 2015 when a proof attempt showed it did not maintain the invariant its analysis relied on.
outcomes:
- Write a contract (preconditions and postconditions) as a docstring and as an executable checker, including for problems with many valid answers
- Prove a loop with an invariant (initialise, maintain, use) and a variant, and keep ranges half-open to avoid off-by-one errors
- Keep in-place rearrangements correct by naming their regions: read and write pointers, and the three regions of the Dutch national flag
- Prove a greedy ordering with an exchange argument and a shortcut with proof by contradiction
- Hunt counterexamples with an edge-case catalogue, and debug wrong answers, crashes and timeouts from a checklist
- Use a reusable stress.py that compares a fast solution with a brute force on random inputs and shrinks the first failure
- Express properties (sorted, permutation, round trip, idempotent, agrees with an oracle) as Hypothesis tests
cues:
- Several indices move in one loop, or an array is rearranged in place
- An off-by-one error keeps coming back, or a loop sometimes never ends
- A greedy rule "obviously" works but you cannot say why
- Your code passes the samples but fails a hidden test, and an obviously correct slow solution is easy to write
traps:
- Testing only the statement's examples, which were chosen to explain the problem, not to break your code
- Mixing closed [lo, hi] and half-open [lo, hi) ranges in one loop
- Comparing outputs with == when the problem accepts many valid answers
- Letting the oracle share code, or the same misunderstanding, with the fast version
- Leaving a random test unseeded, so the failure it found cannot be reproduced
systems:
- SQLite's core contains thousands of assert() statements that check preconditions, postconditions and loop invariants; they make it about three times slower, so production builds compile them out
- CPython fixed list.sort's merge_collapse in 2015 (bpo-23515) after researchers showed it did not maintain the run-stack invariant Timsort relies on; Java's version of the same logic could be made to fail on real hardware
- Java's Arrays.binarySearch computed mid = (low + high) / 2, which overflows for arrays of about a billion elements or more; the bug sat unnoticed for about nine years because no test used such an input
further:
- Article · 10 min | Wikipedia: Loop invariant, informal example and Floyd-Hoare logic | https://en.wikipedia.org/wiki/Loop_invariant#Informal_example
- Article · 5 min | Dijkstra, EWD831: why numbering should start at zero (the case for half-open ranges) | https://www.cs.utexas.edu/~EWD/transcriptions/EWD08xx/EWD831.html
- Docs · 15 min | Hypothesis quickstart: write your first test | https://hypothesis.readthedocs.io/en/latest/quickstart.html#write-your-first-test
- Article · 10 min | SQLite: How SQLite is tested, the Assert section | https://www.sqlite.org/testing.html#assert
---

=== primer | How do you state exactly what a function must do? | 13 min
goal: Write a function's contract as preconditions and postconditions, and turn the postcondition into a checker that works even when many answers are valid
tag: correct-spec | Contracts and checkers
link: Python docs: bisect.bisect_left | https://docs.python.org/3/library/bisect.html#bisect.bisect_left | 3 min: the paragraph stating that the insertion point 'partitions' the list, a real postcondition written as two all(...) expressions
practice: 27, 58

> [!key]
> You cannot prove or test "correct" until you have written down what correct means. A **contract** has two parts: the **precondition** (what the caller guarantees: sorted input, n >= 1) and the **postcondition** (what the function guarantees on return, stated as a relation between input and output). Write the postcondition as a small **checker** function; checking an answer is usually much easier than computing it, and the checker becomes your first test.

## Intuition

A contract with a builder says what you get, not how the bricks are laid: "three bedrooms, passes inspection". The inspector does not rebuild the house; they check it against the list. A specification is that list for a function. It also says what *you* owe: if you give the builder the wrong plot (a precondition broken), the result is not their fault.

## How it works

### Preconditions and postconditions

- **Precondition:** what must be true of the arguments for the function to promise anything. "a is sorted ascending." If the caller breaks it, the bug is in the caller, and the function may raise or return nonsense.
- **Postcondition:** what is true when the function returns, as a relation between inputs and result. "0 <= i <= len(a), every item of a[:i] is < x, every item of a[i:] is >= x."
- **What is not said is free.** If the spec says "the first k slots hold the kept values, in any order", then order is not part of the answer, and a test that compares with `==` is testing the wrong thing.

Python's own documentation states `bisect_left` this way: the returned insertion point *partitions* the list so that everything to its left is less than x and everything from it onwards is at least x. That sentence is a postcondition you can execute.

### Checking is easier than solving

| Task | Solving costs | Checking an answer costs |
|---|---|---|
| Sort a list | O(n log n), with a subtle algorithm | O(n) for "ordered" plus O(n) with a Counter for "same items" |
| Insertion point in a sorted list | O(log n), easy to get off by one | O(n): two `all(...)` scans |
| Remove every val in place, any order | O(n) with two pointers | O(n): compare counts of the kept items |
| Shortest path length | Dijkstra | still hard: needs a second algorithm |

When a checker is cheap, write it before the solution. When many answers are valid (any valid order, any peak, any one of several optimal schedules), a checker is the *only* correct way to test.

### Contracts in code

Put the contract in the docstring, and while developing, check it automatically with a small decorator (the template). For in-place functions the postcondition must compare the arguments **before** the call with the arguments **after** it, so the decorator keeps a deep copy.

## Cost

A checker usually costs O(n) or O(n log n) per call, so wrapping every call can turn an O(log n) function into an O(n) one. That is fine in tests and wrong in production: switch the checks off once the tests pass (the template's `CHECK` flag, or run Python with `-O`, which strips `assert` statements). Deep-copying arguments costs O(size of the input) per call as well.

## When to use it

- Before coding any non-trivial function, and always when the output allows several valid answers.
- When the statement is vague: writing the postcondition exposes every undecided case (ties, empty input, output order).
- In tests: the checker replaces `==` against a single expected answer.

Not every property is cheap to check. If verifying an answer is as hard as finding it (is this path really the shortest?), compare with a brute force instead, which is the stress-testing card's subject.

## Worked trace

Checking candidate answers for the insertion point of x = 3 in a = [1, 3, 3, 7] against the postcondition "a[:i] < x <= a[i:]":

```steps
Candidate i = 1: left part [1] is all < 3, right part [3, 3, 7] is all >= 3
    a      1 | 3  3  7
    {{valid: the first index where a[i] >= 3}}
---
Candidate i = 2: left part [1, 3] contains 3, which is not < 3
    a      1  {{3}} | 3  7
    invalid: breaks "everything left of i is < x"
---
Candidate i = 0: right part [1, 3, 3, 7] contains 1, which is not >= 3
    a    | {{1}}  3  3  7
    invalid: breaks "everything from i on is >= x"
---
Candidate i = 4: left part [1, 3, 3, 7] contains 3 and 7
    a      1  {{3  3  7}} |
    invalid; the checker says why, which == against "1" would not
```

## Template

```python
import copy
import functools
from collections import Counter

CHECK = True     # switch off once the tests pass


def contract(pre=None, post=None):
    """Check pre(*args) before the call and post(old_args, new_args, result) after it."""
    def wrap(fn):
        @functools.wraps(fn)
        def checked(*args):
            if not CHECK:
                return fn(*args)
            if pre is not None:
                assert pre(*args), f"precondition failed: {fn.__name__}{args!r}"
            old = copy.deepcopy(args)               # in-place functions change args
            result = fn(*args)
            if post is not None:
                assert post(old, args, result), f"postcondition failed: {fn.__name__}{old!r} -> {result!r}"
            return result
        return checked
    return wrap


def is_sorted(a):
    return all(p <= q for p, q in zip(a, a[1:]))


def sorts_ok(old, new, result):
    """A sort's postcondition: ordered, and the same items with the same counts."""
    return is_sorted(result) and Counter(result) == Counter(old[0])


def insertion_point_ok(old, new, i):
    """bisect_left's postcondition: a[:i] < x <= a[i:]."""
    a, x = old
    return 0 <= i <= len(a) and all(v < x for v in a[:i]) and all(v >= x for v in a[i:])


@contract(pre=lambda a, x: is_sorted(a), post=insertion_point_ok)
def insertion_point(a, x):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


@contract(post=sorts_ok)
def my_sort(a):
    return sorted(a)
```

## Pitfalls

- **Specifying the algorithm instead of the result.** "Uses two pointers" is a design, not a postcondition; "the first k slots hold the kept values" is.
- **Comparing with `==` when several answers are valid.** Use the checker; otherwise correct solutions fail your tests.
- **Forgetting the old input.** A postcondition such as "the same items as before" needs a copy taken before an in-place call.
- **A weak postcondition.** "The output is sorted" alone is satisfied by `return []`; a sort must also return a permutation of its input.
- **Shipping the checks.** O(n) checks around an O(log n) function in production defeat the point; turn them off, as SQLite does with its asserts.

## Check yourself

Q: Which postcondition does `def bad_sort(a): return []` satisfy, and which property catches it?
A: It satisfies "the output is ordered" (an empty list is ordered). It fails "the output is a permutation of the input", for example `Counter([]) != Counter([2, 1])`. A sort needs both properties.

Q: Write the postcondition for "remove every occurrence of val from nums in place and return k", where the order of the kept values does not matter.
A: With `old` the list before the call and `new` the list after it: k equals the number of items of `old` different from val, and `Counter(new[:k]) == Counter(x for x in old if x != val)`. Nothing is promised about `new[k:]`.

Q: The precondition says a is sorted, and a caller passes [3, 1, 2]. Whose bug is it, and what should `insertion_point` do?
A: The caller's: the contract promises nothing for unsorted input. During development, the `pre` check should fail loudly so the caller is fixed; in production the function may return any index, which is why the precondition is written down.

## Lab

- **27 Remove Element**: write the postcondition as a checker first (the Q above), then the solution, and test it with the checker rather than `==`. Expected: nums = [4, 1, 4, 2, 4], val = 4 gives k = 2 with {1, 2} in the first two slots in either order; nums = [] gives k = 0; O(n) time, O(1) extra space.
- **58 Length of Last Word**: write the contract in your own words: what is a word, what happens with trailing spaces, and what the constraints guarantee (at least one word). Expected: "  fly to   the moon  " gives 4; "a" gives 1; an oracle for tests is `len(s.split()[-1])`.

> [!know]
> You now know how to write a contract with pre- and postconditions and turn it into a checker that tests answers even when many are valid.

=== primer | How do you prove a loop is correct, and that it stops? | 15 min
goal: Prove a loop with an invariant (initialise, maintain, use) and a variant, and keep its ranges half-open to avoid off-by-one errors
tag: correct-invariant | Loop invariants and variants
link: Wikipedia: Loop invariant | https://en.wikipedia.org/wiki/Loop_invariant#Informal_example | 5 min: the 'Informal example', a max-finding loop annotated with its invariant, and how the invariant plus the exit condition gives the result
link: Dijkstra, EWD831: why numbering should start at zero | https://www.cs.utexas.edu/~EWD/transcriptions/EWD08xx/EWD831.html | 5 min: the whole one-page note; the argument for writing ranges as lo <= i < hi
practice: 1299, 374

> [!key]
> A **loop invariant** is a statement about the loop's variables that is true before every iteration. Prove three things: it holds before the first iteration (**initialise**), one iteration keeps it true (**maintain**), and when the loop exits, the invariant plus the exit condition gives the answer (**use**). Add a **variant**, a non-negative integer that strictly decreases each iteration, and the loop must stop. Write ranges as half-open [lo, hi), and most off-by-one errors disappear.

## Intuition

Climbing a ladder: if you can reach the first rung, and from any rung you can reach the next, you can reach them all. That is induction, and an invariant is induction applied to a loop. The variant is the number of rungs left: it goes down by at least one per step and cannot go below zero, so the climb ends.

## How it works

### Initialise, maintain, use: the running maximum

```python
def running_max(a):
    """Largest item of a non-empty list."""
    best = a[0]
    for i in range(1, len(a)):
        # invariant: best == max(a[:i])
        if a[i] > best:
            best = a[i]
    return best
```

- **Initialise:** before the first iteration i = 1 and best = a[0] = max(a[:1]).
- **Maintain:** if best = max(a[:i]), then after comparing with a[i], best = max(a[:i + 1]).
- **Use:** the loop exits with i = len(a), so best = max(a[:len(a)]) = max(a).
- **Variant:** len(a) - i falls by one per iteration and never drops below zero.

### Insertion sort

The invariant of the outer loop: *before iteration i, a[:i] holds the original first i items, in sorted order.* Each iteration takes x = a[i], shifts the larger items of the sorted prefix one slot right, and drops x into the gap, so a[:i + 1] is sorted: maintained. At exit i = n, so the whole list is sorted. The inner loop has its own variant: j falls by one per step and stops at 0.

Finding the invariant is the creative part. A good recipe: write the postcondition, then **weaken it with the loop variable**. "best is the max of a" becomes "best is the max of a[:i]"; "a is sorted" becomes "a[:i] is sorted".

### Half-open ranges

Write every range as [lo, hi): lo is included, hi is not. Then:

- the length is hi - lo, and the range is empty exactly when lo == hi;
- adjacent ranges share a boundary: [lo, mid) and [mid, hi) cover [lo, hi) with no gap and no overlap;
- it matches `range(lo, hi)`, slicing `a[lo:hi]` and C++ iterators, so you never translate.

Dijkstra's EWD831 makes the case in one page: with an inclusive upper bound, the empty range starting at 0 would need an upper bound of -1, which is not a natural number. Many off-by-one errors are **fencepost errors**: a 10-metre fence with a post every metre needs 11 posts. With half-open ranges, n items have n + 1 boundaries and n - 1 gaps, and the number of pages of size k for n items is `(n + k - 1) // k`.

### Termination in searches

In a search over the candidate range [lo, hi), the variant is the range size hi - lo. Every iteration must make it strictly smaller; an update such as `lo = mid` when mid can equal lo is the classic infinite loop. The template's `floor_sqrt` keeps "the answer is in [lo, hi)" and loops while the range holds more than one candidate.

## Cost

Proving a loop costs a few sentences, and the invariant often *is* the cost argument: the variant bounds the number of iterations (len(a) - i gives n - 1 for the running maximum; hi - lo halving gives about log2 n for a search). Insertion sort's inner loop runs at most i times, so the total is at most 1 + 2 + ... + (n - 1) = n(n - 1)/2 shifts: O(n^2) in the worst case (reversed input) and O(n) on sorted input, where the inner loop never runs.

## When to use it

- Any loop with more than one moving index, any in-place rearrangement, any search: write the invariant as a comment *before* the loop body.
- When an off-by-one error keeps coming back: the invariant tells you whether `<` or `<=`, `mid` or `mid + 1` is right.
- When a loop sometimes hangs: find the variant; if you cannot, there may be an iteration where nothing shrinks.

Simple `for x in xs` loops with an obvious accumulator do not need a written proof; a one-line comment is enough.

## Worked trace

Insertion sort on [4, 1, 3, 9, 2]. The bracketed prefix a[:i] is always sorted:

```steps
Before i = 1: the prefix [4] is sorted (one item). Initialised
    a    {{[4]}}  1   3   9   2
---
i = 1, x = 1: shift 4 right, drop 1 at index 0
    a    {{[1   4]}}  3   9   2
---
i = 2, x = 3: shift 4 right, 1 is not larger, so drop 3 at index 1
    a    {{[1   3   4]}}  9   2
---
i = 3, x = 9: nothing in the prefix is larger; 9 stays at index 3
    a    {{[1   3   4   9]}}  2
---
i = 4, x = 2: shift 9, 4 and 3 right, drop 2 at index 1
    a    {{[1   2   3   4   9]}}
---
Exit with i = 5 = len(a): invariant + exit condition = all of a is sorted
    variant n - i went 4, 3, 2, 1, 0
```

## Template

```python
CHECK = True     # turn the invariant checks off once the tests pass


def insertion_sort(a):
    """Sort a in place and return it."""
    for i in range(1, len(a)):
        if CHECK:      # invariant: a[:i] is sorted
            assert all(a[k] <= a[k + 1] for k in range(i - 1)), (i, a)
        x, j = a[i], i
        while j > 0 and a[j - 1] > x:      # variant: j, which falls by 1 and stops at 0
            a[j] = a[j - 1]
            j -= 1
        a[j] = x
    return a


def floor_sqrt(n):
    """Largest r with r * r <= n, for n >= 0."""
    lo, hi = 0, n + 1            # invariant: the answer is in [lo, hi), i.e. lo*lo <= n < hi*hi
    while hi - lo > 1:           # variant: hi - lo, which shrinks every iteration
        mid = (lo + hi) // 2     # lo < mid < hi, because hi - lo >= 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid
    return lo


def pages(n, k):
    """Pages needed for n items, k per page (a fencepost-safe ceiling division)."""
    return (n + k - 1) // k
```

## Pitfalls

- **An invariant that is true but useless.** "i >= 0" is maintained but, combined with the exit condition, proves nothing. The use step is the test of a good invariant.
- **Mixing conventions.** `hi = len(a) - 1` (closed) with `while lo < hi` (half-open) skips the last element; pick one convention and derive every line from it.
- **No progress on some path.** `lo = mid` with `mid = (lo + hi) // 2` makes no progress when hi = lo + 1. Check that every branch shrinks the variant.
- **Invariants that hold only "most of the time".** It must hold at the top of *every* iteration, including the first and after the last.
- **Fenceposts.** n items, n - 1 gaps; the last index is n - 1; `range(n)` stops before n.

## Check yourself

Q: Predict the state of insertion sort on [5, 2, 4, 6, 1, 3] just before i = 4, and how many shifts the i = 4 step makes.
A: Before i = 4 the prefix a[:4] is the first four items sorted: [2, 4, 5, 6, 1, 3]. At i = 4, x = 1 is smaller than all four, so 6, 5, 4 and 2 each shift right: 4 shifts, giving [1, 2, 4, 5, 6, 3].

Q: Why does `floor_sqrt` loop on `hi - lo > 1` rather than `lo < hi`, and what goes wrong with `lo < hi`?
A: Its invariant keeps lo itself a valid answer (lo*lo <= n), so the search is done when [lo, hi) holds exactly one candidate. With `lo < hi`, a range of size one gives mid = lo, the branch sets `lo = mid` (no change), and the loop never ends: the variant stops shrinking.

Q: Fill in the invariant for a loop that computes the right-to-left running maximum: `best = -1`, then `for i in range(n - 1, -1, -1): out[i] = best; best = max(best, a[i])`.
A: Before processing index i, best = max(a[i + 1:]), or -1 when that slice is empty. Initialised (i = n - 1, empty slice, -1); maintained (after writing out[i], best takes a[i] into account, which is max(a[i:]) for the next index); used at each step, since out[i] = max(a[i + 1:]).

## Lab

- **1299 Replace Elements with Greatest Element on Right Side**: write the invariant first (the last Check yourself question), then the loop. Expected: [7, 3, 5, 1] gives [5, 5, 1, -1]; [9] gives [-1]; O(n) time with one right-to-left pass, against O(n^2) for the brute force that takes `max(arr[i + 1:])` at every i.
- **374 Guess Number Higher or Lower**: keep the candidates in a half-open range [lo, hi) starting at [1, n + 1), and state the invariant and variant before coding. Expected: with n = 10 and pick = 7 your guesses are 6, 9, 8, 7 (four guesses); the worst case is n.bit_length() guesses, 31 for n = 2^31 - 1.

> [!know]
> You now know how to prove a loop correct and terminating with an invariant and a variant, and to write ranges half-open.

=== primer | How do you rearrange an array in place without losing track? | 14 min
goal: Keep in-place algorithms correct by naming the regions of the array and the invariant on each, from read/write compaction to the three-way Dutch national flag partition
tag: correct-inplace | Region invariants for in-place work
link: Wikipedia: Dutch national flag problem, the array case | https://en.wikipedia.org/wiki/Dutch_national_flag_problem#The_array_case | 5 min: the pseudocode with its three indices and the invariant that defines the four regions
practice: 27, 26

> [!key]
> An in-place algorithm keeps everything in one array, so the array itself must tell you what is done and what is not. Split it into **regions** with indices as boundaries, and write one invariant per region: "a[:w] holds the kept items, in order", "a[:lt] < pivot, a[lt:i] == pivot, a[i:gt] unknown, a[gt:] > pivot". Every step moves one item out of the unknown region while keeping all the region invariants true.

## Intuition

Sorting a pile of laundry into three baskets is easy. Sorting it on one shelf, without baskets, needs chalk marks: "left of this mark is done whites, right of that mark is done darks, the middle is unsorted". The algorithm is just the rules for moving the marks. Lose a mark and you lose track.

## How it works

### Read and write pointers

To keep only some items, in their original order: the **read pointer** r visits every item; the **write pointer** w marks where the next kept item goes.

```text
    a:  [ kept items | already read, discarded | not read yet ]
          0         w                          r              n
```

Invariant: *a[:w] holds exactly the kept items of a[:r], in their original order.* Initially w = r = 0, both regions empty. Each step reads a[r]: if it is kept, copy it to a[w] and advance w. Since w <= r always, the write never overwrites an unread item. At exit r = n, so a[:w] is the answer and w is its length. This one invariant covers removing a value, removing duplicates from a sorted list (keep a[r] when it differs from the last kept item), moving zeroes to the end and compacting with any predicate.

### Three regions: the Dutch national flag

Rearrange around a pivot into less, equal and greater, in one pass. Four regions, three moving boundaries:

```text
    a:  [  < pivot  |  == pivot  |  unknown  |  > pivot  ]
          0         lt           i           gt          n
```

Each step examines a[i], the first unknown item:

- **less:** swap it with a[lt] (the first equal item, or a[i] itself when the equal region is empty), then advance lt and i;
- **equal:** advance i;
- **greater:** decrement gt and swap a[i] with a[gt]. The item that arrives at i came from the unknown region, so **do not advance i**.

The loop runs while the unknown region [i, gt) is non-empty.

## Cost

Read/write compaction reads every item once and writes at most n times: O(n) time, O(1) extra space. The flag partition shrinks the unknown region gt - i by exactly one per step (either i rises or gt falls), so it takes exactly n steps and at most n swaps: O(n) time, O(1) space. Compare the obvious alternatives: building new lists costs O(n) extra space; calling `list.remove` in a loop costs O(n) per call, O(n^2) in total.

## When to use it

- The problem says "in place" or "O(1) extra space", or the data is too large to copy.
- Filtering or compacting while preserving order: read/write pointers.
- Partitioning by a key with few values (three-way partition; quicksort with many duplicates; sorting 0, 1, 2 values in one pass).

When not: if order must be preserved *and* you are partitioning into several groups, the swap-based partition is not stable (it reorders items within a region); use a stable pass with extra space, or `sorted` with a key. If extra space is allowed, a list comprehension is clearer: `[x for x in a if keep(x)]`.

## Worked trace

The flag partition on [2, 0, 2, 1, 1, 0] with pivot 1. Regions: less is a[:lt], equal a[lt:i], unknown a[i:gt], greater a[gt:]:

```steps
Start: everything is unknown (?). Regions: < is a[:lt], = is a[lt:i], ? is a[i:gt], > is a[gt:]
    a         2  0  2  1  1  0
    region    ?  ?  ?  ?  ?  ?
    lt = 0, i = 0, gt = 6
---
a[0] = 2 > pivot: gt = 5, swap a[0] and a[5]; i stays, because the new a[0] is unknown
    a         {{0}}  0  2  1  1  {{2}}
    region    ?  ?  ?  ?  ?  >
    lt = 0, i = 0, gt = 5
---
a[0] = 0 < pivot: swap with a[lt] (here itself), then lt = 1, i = 1
    a         {{0}}  0  2  1  1  2
    region    <  ?  ?  ?  ?  >
    lt = 1, i = 1, gt = 5
---
a[1] = 0 < pivot: swap with a[lt] (here itself), then lt = 2, i = 2
    a         0  {{0}}  2  1  1  2
    region    <  <  ?  ?  ?  >
    lt = 2, i = 2, gt = 5
---
a[2] = 2 > pivot: gt = 4, swap a[2] and a[4]; i stays, because the new a[2] is unknown
    a         0  0  {{1}}  1  {{2}}  2
    region    <  <  ?  ?  >  >
    lt = 2, i = 2, gt = 4
---
a[2] = 1 == pivot: i = 3
    a         0  0  {{1}}  1  2  2
    region    <  <  =  ?  >  >
    lt = 2, i = 3, gt = 4
---
a[3] = 1 == pivot: i = 4. No ? left: return (lt, gt) = (2, 4)
    a         0  0  1  {{1}}  2  2
    region    <  <  =  =  >  >
    lt = 2, i = 4, gt = 4
```

## Template

```python
def keep_if(a, keep):
    """Move the items with keep(item) True to the front of a, in order; return their count.
    Invariant: a[:w] holds exactly the kept items of a[:r], in their original order."""
    w = 0
    for r in range(len(a)):
        if keep(a[r]):
            a[w] = a[r]
            w += 1
    return w


def three_way_partition(a, pivot):
    """Rearrange a in place into  < pivot | == pivot | > pivot  and return (lt, gt).
    Invariant: a[:lt] < pivot, a[lt:i] == pivot, a[i:gt] unknown, a[gt:] > pivot."""
    lt, i, gt = 0, 0, len(a)
    while i < gt:                         # variant: gt - i, the size of the unknown region
        if a[i] < pivot:
            a[lt], a[i] = a[i], a[lt]
            lt += 1
            i += 1
        elif a[i] > pivot:
            gt -= 1
            a[i], a[gt] = a[gt], a[i]     # the item swapped in is unknown: do not advance i
        else:
            i += 1
    return lt, gt
```

## Pitfalls

- **Advancing i after swapping with gt.** The item that arrives at i has not been examined; skipping it leaves a large value in the middle.
- **Writing before reading.** If w could pass r, a write would destroy an unread item; the invariant w <= r is what makes compaction safe.
- **Off-by-one boundaries.** Is gt the first greater item or the last unknown one? Write the region invariant with half-open slices and the code follows.
- **Expecting stability.** Swaps reorder equal-region items relative to each other; read/write compaction is stable, the flag partition is not.
- **Returning the wrong thing.** Many in-place problems return a length and judge only `a[:k]`; anything beyond k is free.

## Check yourself

Q: Fill the missing condition: remove duplicates from a *sorted* list in place with `w = 1` and `for r in range(1, len(a)): if ____: a[w] = a[r]; w += 1` (for non-empty a). What invariant justifies it?
A: `a[r] != a[w - 1]`. Invariant: a[:w] holds the distinct values of a[:r], in order, so a[w - 1] is the last kept value; in a sorted list, a[r] is new exactly when it differs from that value. (Comparing with a[w] instead is a classic bug: a[w] is not a kept item.)

Q: Trace `three_way_partition([1, 2, 0], 1)`: the final list and (lt, gt).
A: i = 0: a[0] = 1 is equal, i = 1. a[1] = 2 is greater: gt = 2, swap a[1] and a[2], giving [1, 0, 2]. a[1] = 0 is less: swap with a[lt = 0], giving [0, 1, 2], then lt = 1, i = 2 = gt, stop. Result [0, 1, 2] with (lt, gt) = (1, 2).

Q: Why does the flag partition take exactly n iterations, never more?
A: Each iteration either increases i or decreases gt by one, so the unknown region gt - i shrinks by exactly one per iteration; it starts at n and the loop stops at 0.

## Lab

- **27 Remove Element**: use read and write pointers with the invariant "a[:w] holds the items of a[:r] that differ from val". Expected: [4, 1, 4, 2, 4] with val = 4 gives k = 2 and [1, 2] in the first two slots (your order may differ if you swap from the end); one pass, O(1) extra space.
- **26 Remove Duplicates from Sorted Array**: the first Check yourself question is the whole idea; write it with its invariant as a comment. Expected: [0, 0, 1, 1, 1, 4, 5, 5] gives k = 4 with [0, 1, 4, 5] in the first four slots; O(n) time, O(1) extra space.

> [!know]
> You now know how to keep in-place rearrangements correct by naming each region of the array and the invariant that defines it.

=== primer | How do you prove that a greedy choice is safe? | 14 min
goal: Prove an ordering rule with an exchange argument, prove a shortcut by contradiction, and use a brute force to test a rule before trying to prove it
tag: correct-exchange | Exchange arguments and contradiction
link: Erickson, Algorithms, chapter 4 (Greedy) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/04-greedy.pdf | 15 min: section 4.1 'Storing Files on Tape' only (the first three pages): the same exchange argument as this card, including the version with access frequencies

> [!key]
> A greedy rule ("always do the shortest job first") is safe when you can show that **any** optimal solution can be changed into the greedy one without getting worse. The **exchange argument** does this by swapping two adjacent items that are out of greedy order and showing the cost does not rise; repeat until the order is greedy. **Proof by contradiction** shows a property must hold because its failure would allow a strictly better solution. Before proving, let a brute force try to break the rule.

## Intuition

At a supermarket with one till, letting the customer with one item go before the customer with a full trolley costs the trolley owner a minute and saves the one-item customer twenty. Total waiting drops. Any queue in which a long job stands just before a short one can be improved by swapping those two, so the best queue has no such pair: it is sorted shortest first.

## How it works

### The exchange argument, step by step

Jobs have a processing time t and a weight w (importance); a job's completion time C is when it finishes. Minimise the total weighted completion time, the sum of w x C.

Take any order and two **adjacent** jobs p then q, starting at time s. Only their own completion times change if you swap them; everything before and after is untouched.

- p first: w_p(s + t_p) + w_q(s + t_p + t_q)
- q first: w_q(s + t_q) + w_p(s + t_q + t_p)

The difference (p first minus q first) is **w_q t_p - w_p t_q**. So p should go first exactly when t_p w_q <= t_q w_p, that is, when t_p / w_p <= t_q / w_q. The rule: **sort by t / w ascending** (Smith's rule, 1956). With equal weights it is "shortest job first".

The proof that sorting is optimal: take any optimal order. If it is not sorted by t / w, some adjacent pair is out of order; swapping it does not increase the cost (by the formula). Each swap removes one inversion, so after finitely many swaps the order is sorted, and its cost is no higher than the optimum. So the sorted order is optimal.

### Proof by contradiction: why the best block never starts with a negative prefix

In the maximum-subarray lab, the linear algorithm abandons the running sum when it goes negative. Why is that safe? Suppose an optimal block a[i:j] began with a prefix a[i:k] (k < j) whose sum is negative. Then a[k:j] = (whole) - (prefix) has a strictly larger sum, contradicting optimality. So an optimal block never starts with a negative-sum prefix, and discarding such prefixes loses nothing.

### Test before you prove

A brute force over all orders (n <= 8 is 40,320 orders) checks a candidate rule in seconds on random instances. It quickly rejects tempting wrong rules such as "heaviest first" or "shortest first" when weights differ, and it gives you confidence before you spend time on a proof.

## Cost

The greedy algorithm is one sort, O(n log n), plus an O(n) pass to compute the cost. The brute force over all n! orders with an O(n) cost each is O(n x n!), fine as an oracle up to n = 8 or 9. The proof itself is a single algebraic identity plus "repeat the swap", the usual size of an exchange argument.

## When to use it

- A problem orders or selects items to optimise a sum (scheduling, file placement, interval selection) and a local comparison of two neighbours decides which goes first.
- You have a greedy rule that "feels right": derive the swap formula, and if it shows that some pair should go the other way, the rule is wrong.
- Use contradiction for structural facts (an optimal block never starts with a negative prefix; a shortest path never repeats a vertex).

When not: if swapping two items also changes what is feasible later (budgets, capacities, deadlines with penalties), the local swap does not tell the whole story and greedy often fails; that is where dynamic programming takes over. The greedy module returns to exchange arguments and the "stays ahead" proof.

## Worked trace

Jobs as (t, w): (3, 1), (1, 2), (2, 2), (4, 3), with ratios t / w = 3, 0.5, 1, 1.33. Fix one adjacent inversion at a time and watch the total fall:

```steps
Start in the given order: total weighted completion time 53
    order   (3,1) (1,2) (2,2) (4,3)
    finish    3     4     6    10       cost 3 + 8 + 12 + 30 = 53
---
(3,1) before (1,2) is inverted (ratio 3 > 0.5): swap. Change = w_q t_p - w_p t_q = 2*3 - 1*1 = 5
    order   {{(1,2) (3,1)}} (2,2) (4,3)
    finish    1     4     6    10       cost {{48}}
---
(3,1) before (2,2) is inverted (3 > 1): swap. Saves 2*3 - 1*2 = 4
    order   (1,2) {{(2,2) (3,1)}} (4,3)
    finish    1     3     6    10       cost {{44}}
---
(3,1) before (4,3) is inverted (3 > 1.33): swap. Saves 3*3 - 1*4 = 5
    order   (1,2) (2,2) {{(4,3) (3,1)}}
    finish    1     3     7    10       cost {{39}}
---
No adjacent pair is inverted: sorted by t / w. A brute force over all 24 orders agrees
    {{39 is the minimum}}
```

## Template

```python
from functools import cmp_to_key
from itertools import permutations


def weighted_completion(order):
    """Sum of w * (finish time) for jobs (t, w) run in this order."""
    clock = total = 0
    for t, w in order:
        clock += t
        total += w * clock
    return total


def smith_order(jobs):
    """Optimal order for jobs (t, w) with w > 0: ascending t / w, compared exactly by cross-multiplying."""
    return sorted(jobs, key=cmp_to_key(lambda p, q: p[0] * q[1] - q[0] * p[1]))


def best_cost_brute(jobs):
    """The oracle: try every order (n! of them)."""
    return min(weighted_completion(order) for order in permutations(jobs))
```

## Pitfalls

- **Swapping non-adjacent items.** Swapping p and q with jobs between them also shifts those jobs; the clean formula holds for adjacent pairs, which is why the argument works with them.
- **Floating-point ratios.** Sorting by `t / w` as floats can misorder near-equal ratios; compare `t_p * w_q` with `t_q * w_p` in integers.
- **Proving the rule on the examples only.** An exchange argument must work for *any* pair in *any* optimal solution, not for the sample.
- **Assuming greedy because it worked twice.** Let the brute force search for a counterexample first; it costs minutes.
- **Zero weights.** The ratio t / w is undefined; the cross-multiplied comparison still orders zero-weight jobs last.

## Check yourself

Q: With all weights equal to 1, what does the swap formula w_q t_p - w_p t_q reduce to, and what rule follows?
A: t_p - t_q. Putting p first is no worse exactly when t_p <= t_q, so the rule is shortest job first.

Q: For the four jobs in the trace, what do "shortest first" and "heaviest first" cost, and why do they lose to 39?
A: Shortest first, (1,2) (2,2) (3,1) (4,3), costs 2 + 6 + 6 + 30 = 44: it runs the heavy, long job (4,3) last. Heaviest first, (4,3) (1,2) (2,2) (3,1), costs 12 + 10 + 14 + 10 = 46: it makes two light-but-short jobs wait behind a long one. Each rule ignores one of the two quantities in the ratio t / w.

Q: Prove by contradiction that an optimal maximum-sum block never *ends* with a suffix whose sum is negative.
A: Suppose an optimal block a[i:j] ends with a suffix a[k:j] (i < k) whose sum is negative. Then a[i:k] has sum (whole) - (suffix), which is strictly larger, contradicting optimality. (Here i < k keeps a[i:k] non-empty.)

## Lab

- Run `smith_order` against `best_cost_brute` on 500 random instances of 1 to 7 jobs with t in 1..9 and w in 1..9, and count mismatches in cost. Expected: 0 mismatches, and for [(3, 1), (1, 2), (2, 2), (4, 3)] both give 39.
- Replace the comparator with "heaviest first" (sort by -w) and rerun. Expected: the brute force finds counterexamples on most random instances; the trace's four jobs give 46 against 39.

> [!know]
> You now know how to prove a greedy ordering with an adjacent exchange argument and a structural shortcut by contradiction.

=== primer | How do you find the input that breaks your code, and then the bug? | 15 min
goal: Attack code with an edge-case catalogue, then find the bug systematically: reproduce, shrink, print the invariant, form one hypothesis at a time, and use the wrong answer, crash and timeout checklists
tag: correct-edges | Edge cases and systematic debugging
link: USACO Guide: Debugging Checklist | https://usaco.guide/general/debugging-checklist#wrong-answer-or-runtime-error | 5 min: 'Wrong Answer or Runtime Error' and 'Time Limit Exceeded', two short checklists to compare with the ones on this card
practice: 66, 58

> [!key]
> Bugs live at the edges: empty input, one item, all equal, already sorted, reversed, the largest values, the last element. Attack your code with an **edge-case catalogue** before the judge does. When something fails, debug like a scientist: **reproduce** with the smallest failing input, **print the invariant** each iteration to find where state goes wrong, form **one hypothesis**, test it, fix, then rerun every test. Assertions turn invariants into alarms that fire at the first wrong step.

## Intuition

A bridge inspector does not drive one family car across and declare it safe. They check the heaviest truck, the strongest wind and the coldest night. Normal inputs rarely break code; extreme and degenerate ones do. Debugging is the same mindset after a failure: you do not stare at the whole program, you narrow the gap between "where state is still right" and "where it is wrong".

## How it works

### The edge-case catalogue

| Case | Example | What it breaks |
|---|---|---|
| Empty | `[]`, `""` | `a[0]`, `max(a)`, answers that start at 1 |
| One item | `[5]` | loops starting at index 1, pair logic |
| Two items | `[5, 3]` | swaps, neighbour logic |
| All equal | `[7, 7, 7]` | strict versus non-strict comparisons, distinctness |
| Sorted, reversed | `[1, 2, 3]`, `[3, 2, 1]` | best and worst cases, pivots |
| Extremes | 0, negatives, 10^9, n at its maximum | sentinels, overflow in C++/Java, time limits |
| The last element | the answer sits at the end | updates that run only when something changes |
| Strings | spaces only, trailing spaces, one character | split and strip logic, empty words |

Generate the catalogue in code (the template) and run every case through both your fast solution and a brute force.

### Debugging, step by step

1. **Reproduce** the failure with a fixed input, and **shrink** it: delete items and simplify values while it still fails. A failure on `[7, 7, 7]` is far easier to read than one on 10,000 random numbers.
2. **Print the invariant**, not random variables. If the loop claims "best is the longest run that has ended before i, cur is the run ending at i", print i, best and cur each iteration and find the first line where the claim is false.
3. **One hypothesis at a time.** Write it down ("the last run is never compared"), predict what a change will do, make one change, and rerun.
4. **Fix, then rerun everything**: the catalogue, the stress test and the examples. Fixes often break a different edge.
5. **For regressions**, binary-search history: `git bisect run ./test.sh` finds the first commit whose test fails.

### Checklists by verdict

- **Wrong answer:** edge cases above; a misread statement (strict or not, indices or values, 0- or 1-based); the last element or last group never processed; state left over between test cases (globals, class attributes, mutable default arguments); integer division `//` with negatives; comparing floats with ==.
- **Runtime error:** index out of range at a boundary; `None` where a value was expected; a missing dict key; `RecursionError` (CPython's default limit is 1,000 frames); modifying a list or dict while iterating over it.
- **Time limit:** the constraint budget was not met; hidden O(n) inside a loop (`x in list`, `list.pop(0)`, `list.insert(0, x)`, slicing, string `+=`); recursion without memoisation; printing debug output in a hot loop; a loop that never ends (check the variant).

### Assertions as executable invariants

`assert cur >= 1, (i, cur)` stops the program at the first broken step, with the state in the message. Python removes all asserts when run with `-O`, so never use them for input validation, only for "this cannot happen" checks during development. SQLite takes the same line: thousands of asserts in debug builds, compiled out of production builds.

## Cost

The catalogue is about ten tiny inputs: microseconds to run and minutes to write once, then reusable for every list problem. Shrinking by hand costs a few minutes; the stress card automates it. Printing the invariant costs one line. The expensive path is the alternative: guessing, changing three things at once and resubmitting.

## When to use it

- Before every submission: run the catalogue against your brute force.
- After any failure: the five debugging steps, in order.
- Assertions whenever a loop has an invariant you could state; remove or disable them once the tests pass if they cost more than O(1).

When not: hand-picked edges complement random testing, they do not replace it. Interactions between features (duplicates *and* negatives at the end) are what random testing finds better.

## Worked trace

A `longest_run` that returns `best` after the loop (the template's buggy version), debugged on [3, 7, 7, 7] by printing its invariant:

```steps
Reproduce: the catalogue's "all equal" case already fails
    longest_run([7, 7, 7]) = 1, brute force says 3
    {{also fails: [] gives 1, want 0}}
---
Use a slightly richer failing input and print the invariant
    claim: best = longest run that ended before i,
           cur  = length of the run ending at i
    xs = [3, 7, 7, 7]
---
i = 1: 7 != 3, a run ended: best = max(1, 1) = 1, cur = 1
    i  xs[i]  best  cur
    1    7     1     1      claim holds
---
i = 2 and i = 3: equal neighbours, cur grows
    i  xs[i]  best  cur
    2    7     1     2
    3    7     1     {{3}}    claim holds
---
Loop ends; the function returns best = 1. The run 7 7 7 never "ended"
    {{hypothesis: the final run is never compared with best}}
---
Fix: return max(best, cur), and 0 for empty input. Rerun everything
    catalogue: 0 failures
    {{stress test against the brute force: passes}}
```

## Template

```python
def edge_lists(lo=-3, hi=3):
    """The edge-case catalogue for a single list argument."""
    yield []                                   # empty
    yield [lo]                                 # one item
    yield [lo, hi]                             # two items
    yield [hi, lo]
    yield [hi] * 4                             # all equal
    yield list(range(lo, hi + 1))              # sorted
    yield list(range(hi, lo - 1, -1))          # reversed
    yield [0, hi, 0, hi, 0]                    # alternating repeats
    yield [lo] * 2 + [hi] * 3                  # the longest run is last


def check_edges(fast, brute, cases):
    """Run every case through both versions; return (input, want, got) for each mismatch."""
    failures = []
    for xs in cases:
        want = brute(list(xs))
        try:
            got = fast(list(xs))
        except Exception as e:                 # a crash is a result too
            got = repr(e)
        if got != want:
            failures.append((xs, want, got))
    return failures


def longest_run_brute(xs):
    n = len(xs)
    return max((j - i for i in range(n) for j in range(i + 1, n + 1) if len(set(xs[i:j])) == 1), default=0)


def longest_run_buggy(xs):
    best = cur = 1
    for i in range(1, len(xs)):
        if xs[i] == xs[i - 1]:
            cur += 1
        else:
            best = max(best, cur)
            cur = 1
    return best


for case in check_edges(longest_run_buggy, longest_run_brute, edge_lists()):
    print(case)
# ([], 0, 1)
# ([3, 3, 3, 3], 4, 1)
# ([-3, -3, 3, 3, 3], 3, 2)
```

## Pitfalls

- **Changing several things at once.** If the test then passes you do not know which change fixed it, or what else you broke.
- **Debugging the big input.** Shrink first; a five-item failure is usually readable at a glance.
- **Printing everything.** Print the invariant's variables at the top of each iteration; the first line where the claim fails points at the bug.
- **Asserts for input validation.** `python -O` deletes them; raise `ValueError` for bad input instead.
- **Stopping at the first fix.** Rerun the catalogue and the stress test; a fix for the empty case often breaks the one-item case.

## Check yourself

Q: Which catalogue cases expose `def last_word_length(s): return len(s.split(" ")[-1])`, and what does it return on them?
A: Trailing spaces: "fly me " splits on single spaces into ['fly', 'me', ''], so it returns 0. A string of spaces returns 0 for the same reason. `s.split()` with no argument splits on runs of whitespace and drops empty pieces, which fixes it.

Q: A solution passes all samples but gets a time limit on n = 10^5. The loop body contains `if x in seen:` with `seen = []`. Explain and fix.
A: `x in list` scans the list: O(n) per check, O(n^2) overall, about 10^10 steps. Make `seen` a set, so each check is O(1) on average and the loop is O(n).

Q: A plus-one function on a list of digits passes [1, 2, 3] and [4, 9]. Name the catalogue case most likely to break it and the expected output.
A: All digits 9, the extreme carry: [9] should give [1, 0] and [9, 9] should give [1, 0, 0]. Code that only propagates the carry inside the list forgets the new leading digit.

## Lab

- **66 Plus One**: write the catalogue for digit lists first ([0], [9], [9, 9], [1, 9], [8, 9, 9]), with Python's integers as the oracle (`int("".join(map(str, d))) + 1`). Expected: [9, 9] gives [1, 0, 0], [1, 2, 9] gives [1, 3, 0], [0] gives [1]; O(n) time.
- **58 Length of Last Word**: run your solution on the string catalogue (one letter, trailing spaces, several spaces between words, leading spaces) against the oracle `len(s.split()[-1])`. Expected: "  fly to   the moon  " gives 4, "a" gives 1, "a " gives 1; an O(1)-space solution scans from the end, skipping spaces, then counting letters.

> [!know]
> You now know how to attack code with an edge-case catalogue and debug a failure by reproducing, shrinking and checking the invariant one hypothesis at a time.

=== primer | How do you stress-test a solution against a brute force? | 16 min
goal: Use a reusable stress.py that generates random inputs, compares a fast solution with a brute-force oracle, stops at the first mismatch and shrinks it to a minimal failing case
tag: correct-stress | Stress testing with a brute-force oracle
link: USACO Guide: Basic Debugging, Stress Testing | https://usaco.guide/general/basic-debugging#stress-testing | 10 min: 'Stress Testing' and 'Option 1: A Single Program', the same loop in competitive-programming form, with C++ and Python scripts
practice: 26, 1299

> [!key]
> Keep the slow, obviously correct solution and let the computer search for disagreements: **generate** a small random input, run the **brute force** and the **fast** version, **compare**, and stop at the first mismatch. Then **shrink** it: keep deleting items and moving numbers towards zero while the two versions still disagree. Thousands of small random cases find most bugs in seconds, and the shrunk case usually shows the bug at a glance.

## Intuition

A new recipe and a trusted one should give the same cake. You do not need to know which step of the new recipe is wrong to discover *that* something is wrong: bake both a thousand times with random ingredients and compare. When they differ, bake again with fewer and fewer ingredients until removing anything makes the difference disappear. What is left points at the bug.

## How it works

### The four parts

- **Generator:** `gen(rng)` returns a tuple of arguments. Keep sizes small (0 to 8 items) and value ranges narrow (-5 to 5), so duplicates, ties, zeros and negatives turn up constantly. Pass a seeded `random.Random`, so every failure can be reproduced.
- **Oracle:** the brute force from the solving loop, independent of the fast code.
- **Compare:** `==` by default; a custom `same` for answers that may differ but both be valid (or compare canonical forms, such as sorted lists). A crash in the fast version counts as a mismatch; a crash in the oracle is reported as a broken oracle.
- **Shrink:** from the failing input, try simpler candidates (delete everything, then halves, then single items; replace numbers by 0, by half, or by one step towards 0) and move to the first one that still fails; repeat until no candidate fails. The result is **locally minimal**: no single simplification still fails.

In-place functions are wrapped so the harness sees everything the contract promises: for "remove duplicates and return k", the wrapper returns `nums[:k]` (and k), not just k. The harness passes deep copies, so an in-place function cannot corrupt the input it is compared on. If a precondition must hold (the list is sorted), pass `valid=` so shrinking never produces an invalid input.

### stress.py

Save this once and reuse it in every lab of this guide. It is also the first piece of dsakit, the toolkit project that ends this stage.

```python
"""stress.py: compare a fast solution with a brute-force oracle on random inputs, then shrink the first failure.

    from stress import stress
    stress(gen, brute, fast)      # gen(rng) returns a tuple of arguments

A crash in `fast` counts as a failure; a crash in `brute` is reported as a broken oracle.
"""
import copy
import random


def run(fn, args):
    """Call fn on a fresh deep copy of args, so in-place functions cannot corrupt the test case."""
    try:
        return "ok", fn(*copy.deepcopy(args))
    except Exception as e:
        return "crash", repr(e)


def simpler(x):
    """Yield values a little simpler than x: shorter lists and strings, numbers nearer 0."""
    if isinstance(x, bool):
        if x:
            yield False
    elif isinstance(x, int):
        for y in dict.fromkeys((0, x // 2 if x > 0 else -(-x // 2), x - 1 if x > 0 else x + 1)):
            if abs(y) < abs(x):
                yield y
    elif isinstance(x, (list, str)):
        size = len(x)
        while size >= 1:                          # delete chunks: everything, halves, ..., single items
            for start in range(0, len(x) - size + 1, size):
                yield x[:start] + x[start + size:]
            size //= 2
        if isinstance(x, list):
            for i, item in enumerate(x):
                for y in simpler(item):
                    yield x[:i] + [y] + x[i + 1:]
    elif isinstance(x, tuple):                    # an argument tuple: simplify one argument at a time
        for i, item in enumerate(x):
            for y in simpler(item):
                yield x[:i] + (y,) + x[i + 1:]


def shrink(args, still_fails):
    """Greedily move to a simpler input that still fails, until no simpler candidate fails."""
    improved = True
    while improved:
        improved = False
        for candidate in simpler(args):
            if still_fails(candidate):
                args, improved = candidate, True
                break
    return args


def stress(gen, brute, fast, trials=2000, seed=0, same=None, valid=None):
    """Run fast and brute on trials random inputs; on the first mismatch print a shrunk case and return it."""
    same = same or (lambda want, got: want == got)

    def fails(args):
        if valid is not None and not valid(*args):
            return False                           # shrinking must keep the precondition true
        want, got = run(brute, args), run(fast, args)
        if want[0] == "crash":
            raise RuntimeError(f"the oracle crashed on {args!r}: {want[1]}")
        return got[0] == "crash" or not same(want[1], got[1])

    rng = random.Random(seed)
    for trial in range(trials):
        args = gen(rng)
        if fails(args):
            small = shrink(args, fails)
            print(f"FAIL on trial {trial} (seed {seed})")
            print(f"  found:  {args!r}")
            print(f"  shrunk: {small!r}")
            print(f"  brute:  {run(brute, small)[1]!r}")
            print(f"  fast:   {run(fast, small)[1]!r}")
            return small
    print(f"OK: {trials} random tests passed (seed {seed})")
    return None


def rand_list(rng, max_len=8, lo=-5, hi=5):
    """A short list of small integers: small ranges force duplicates, ties and equal neighbours."""
    return [rng.randint(lo, hi) for _ in range(rng.randint(0, max_len))]
```

## Cost

Each trial costs one brute-force call plus one fast call. With inputs of at most 8 items, even an O(n^3) brute force does a few hundred steps, so 2,000 trials take well under a second in CPython. Shrinking is greedy: each accepted step strictly shortens the input or brings a number closer to 0, so it terminates, and each round tries O(size) candidates; on small inputs it finishes in milliseconds. Deep copies add O(input size) per call, negligible at these sizes.

## When to use it

- Whenever an obviously correct slow solution exists: almost every algorithm in this guide. It is the default check in every later lab.
- Before submitting a tricky solution, and immediately when a hidden test fails.
- For refactors: keep the old version as the oracle while you optimise.

When not: it cannot find bugs that need large inputs (overflow at 2^31, recursion depth, time limits); add a few large targeted tests and a timing run. If no brute force exists, test properties instead (next card). A random test that passes is evidence, not proof: pair it with the invariant.

## Worked trace

The harness on `second_largest` with a planted bug: the `elif` branch lost its `x != first` check (the restate card in the method module shows the correct version).

```steps
Trial 0: both versions agree
    xs = [1, -5, -1, 3, 2, 1]           brute 2     fast 2
---
Trial 1: both agree
    xs = [2, 0, 4, -2]                  brute 2     fast 2
---
Trial 2: mismatch. Stop and shrink
    xs = [-3, -1, -3, -4, 4, -1, 3, 4]  brute 3     fast {{4}}
---
Delete everything: [] passes (both None). Delete the first half: still fails, keep it
    xs = {{[4, -1, 3, 4]}}                  brute 3     fast 4
---
Delete single items: removing -1 still fails, keep it
    xs = {{[4, 3, 4]}}                      brute 3     fast 4
---
Removing 3 still fails, keep it
    xs = {{[4, 4]}}                         brute None  fast 4
---
No simpler candidate fails: [4], [], [0, 4], [2, 4], [3, 4] all pass
    shrunk: [4, 4]   {{a repeated maximum is counted as second}}
```

The real output of `stress(lambda r: (rand_list(r),), second_largest_brute, buggy)`:

```text
FAIL on trial 2 (seed 0)
  found:  ([-3, -1, -3, -4, 4, -1, 3, 4],)
  shrunk: ([4, 4],)
  brute:  None
  fast:   4
```

## Template

Using the harness: a generator, an oracle, the fast version and, for in-place code, a wrapper that returns everything the contract promises.

```python
from stress import rand_list, stress


def dedupe_sorted(a):
    """Remove repeats from sorted a in place; return k, with a[:k] holding each value once."""
    if not a:
        return 0
    w = 1
    for r in range(1, len(a)):
        if a[r] != a[w - 1]:
            a[w] = a[r]
            w += 1
    return w


def dedupe_fast(a):                  # wrapper: compare the whole promised result
    k = dedupe_sorted(a)
    return k, a[:k]


def dedupe_brute(a):
    distinct = sorted(set(a))
    return len(distinct), distinct


stress(lambda rng: (sorted(rand_list(rng)),), dedupe_brute, dedupe_fast,
       valid=lambda a: a == sorted(a))
# OK: 2000 random tests passed (seed 0)
```

## Pitfalls

- **Large random inputs.** Big inputs make the brute force slow and the failures unreadable; small sizes with narrow value ranges find more bugs per second.
- **Unseeded randomness.** Without a seed you cannot rerun the failure; the harness prints the seed and the trial.
- **An oracle that shares code** (or the same misreading of the statement) with the fast version: both agree on the wrong answer.
- **Comparing too little.** For in-place functions, compare the array contents the contract promises, not just the returned length.
- **Treating "OK" as proof.** Random tests miss what they never generate: values near 2^31, n = 10^5, deep recursion. Add those as targeted tests.
- **A hanging fast version.** The harness waits forever on an infinite loop; print the trial's input before running it, or add a step counter, to find which input hangs.

## Check yourself

Q: The shrinker stops at `([0, -1], 5)` for a rotate function. Why can it not reach `([0, -1], 3)`, which also fails, and is that a problem?
A: From 5 it only tries 0, 2 and 4 (zero, half, one step towards zero); with two items those rotations equal 0, 0 and 0 steps, so all pass. 3 is not a single simplification away, so 5 is locally minimal. That is fine: the case is already tiny, and you can finish by hand (rotating two items by 5 should equal rotating by 1).

Q: Why does `run` deep-copy the arguments before every call?
A: In-place functions modify their input. Without copies, the fast version would receive a list the brute force had already changed (or the reverse), and the comparison, and any shrinking, would be on corrupted inputs.

Q: Your generator draws lists of length 0 to 1,000 with values up to 10^9, and the stress test finds nothing. What would you change?
A: Shrink the ranges: lengths 0 to 8 and values -5 to 5. Small values force duplicates, zeros and ties, where most bugs live; small lengths make each trial cheap (more trials per second) and keep the brute force fast.

## Lab

- **26 Remove Duplicates from Sorted Array**: plug your solution into the template above (wrap it so it returns `(k, nums[:k])`), then break it on purpose by comparing `a[r]` with `a[w]` and rerun. Expected: `OK: 2000 random tests passed (seed 0)` for the correct version; the broken one shrinks to `([0, 1],)`, where it returns k = 1 instead of 2.
- **1299 Replace Elements with Greatest Element on Right Side**: stress your O(n) right-to-left pass against `[max(arr[i + 1:], default=-1) for i in range(len(arr))]` with values from 1 to 9 (non-empty lists, so pass `valid=lambda arr: len(arr) > 0`). Expected: `OK: 2000 random tests passed`; [7, 3, 5, 1] gives [5, 5, 1, -1].

> [!know]
> You now know how to stress-test any solution against a brute force with a reusable harness that stops at the first failure and shrinks it.

=== primer | What does property-based testing add, and how do you use Hypothesis? | 14 min
goal: State properties (agrees with an oracle, ordered, permutation, round trip, idempotent) as Hypothesis tests and read the shrunk failing case it reports
tag: correct-pbt | Property-based testing with Hypothesis
link: Hypothesis docs: Quickstart | https://hypothesis.readthedocs.io/en/latest/quickstart.html#write-your-first-test | 10 min: 'Write your first test', 'Arguments to @given' and 'Filtering inside a test'
practice: 66, 26

> [!key]
> A **property** is a statement that must hold for every valid input: "the output is ordered and is a permutation of the input", "decode(encode(s)) == s", "my answer equals the brute force's". **Hypothesis** generates hundreds of inputs per property, including nasty ones you would not think of, and when one fails it **shrinks** it to a minimal example and remembers it for the next run. Use it when you can state properties, even without a brute force.

## Intuition

An example test asks "does 2 + 3 give 5?". A property test asks "is a + b always equal to b + a?", and lets a machine pick the a and b. You stop guessing which examples matter and write down what must always be true. The machine is good at picking examples: empty strings, enormous integers, Unicode digits, lists of 50 equal items.

## How it works

### Properties that work for algorithms

| Property | Example |
|---|---|
| Agrees with an oracle | `my_sort(xs) == sorted(xs)`; `fast(a) == brute(a)` |
| Postcondition | output ordered, and `Counter(out) == Counter(xs)` (a permutation) |
| Round trip | `decode(encode(s)) == s`; `deserialise(serialise(tree)) == tree` |
| Idempotent | `my_sort(my_sort(xs)) == my_sort(xs)`; normalising twice changes nothing |
| Invariant preserved | after every operation, the heap property still holds |
| Metamorphic | shuffling the input does not change the answer of a sort or a sum |

### Writing a test

`@given(strategy)` feeds generated values into a test function; pytest runs it. Strategies describe valid inputs:

- `st.integers(-5, 5)`, `st.lists(st.integers(), max_size=30)`, `st.text(alphabet="ab ")`;
- preconditions by construction: `st.lists(st.integers()).map(sorted)` gives sorted lists;
- `assume(cond)` or `.filter(cond)` to discard rare invalid inputs (prefer construction: heavy filtering slows generation).

### Shrinking and the example database

When a property fails, Hypothesis shrinks the input towards the simplest version that still fails (shorter lists, smaller numbers, simpler characters) and reports it as the failing test case. It saves the failure in a local `.hypothesis` directory and replays it first on the next run, so a fixed bug stays fixed. Add `@example(...)` to always include specific edge cases, and `@settings(max_examples=1000)` to search harder.

### A real run

The test file below checks four properties of insertion sort (they pass) and the round trip of a run-length encoder that writes "aaab" as "3a1b". In one derandomised run, Hypothesis reported **two distinct failures**: `s='0'`, where the encoding "10" is read back as a count of ten followed by nothing, and `s='²:'`, where `str.isdigit()` accepts the superscript ² but `int()` rejects it. The second is a Unicode corner that hand-written examples almost never cover.

## Cost

By default each `@given` test runs 100 examples, plus the shrinking steps after a failure; for small algorithmic inputs that is well under a second per property. `max_examples` trades time for thoroughness. Strategies with heavy filtering or large sizes slow down generation; Hypothesis's health checks fail the test when it has to reject too many inputs.

## When to use it

- When you can state properties but have no brute force (encoders, parsers, data structures).
- When the input space is structured (Unicode text, nested lists, floats with NaN and infinities): Hypothesis's strategies explore it better than `random.randint`.
- For data structures, its stateful testing drives random sequences of operations against a simple model; the design module uses it for an LRU cache.

| | stress.py | Hypothesis |
|---|---|---|
| Needs | a brute-force oracle | any property (an oracle is one kind) |
| Inputs | your generator | rich strategies, edge-biased |
| Shrinking | simple greedy | sophisticated, per strategy |
| Remembers failures | no (rerun with the seed) | yes, in `.hypothesis` |
| Dependencies | none | `pip install hypothesis pytest` |

Both are worth having: the harness is one short file you understand fully and can run anywhere; Hypothesis is stronger at finding and minimising strange inputs.

## Worked trace

Failing inputs Hypothesis tried for the round-trip property during one shrinking run (encoder output and decoder output in brackets; the decoder should return the input):

```steps
First failure: a nine-character string of random Unicode containing the digit 9
    the encoder writes "19" for the run "9"; the decoder glues those digits
    to the next count, reads "191" and prints 191 copies of the next character
---
A smaller failure: four zeros
    s = '0000'   encode -> '40'    decode -> ''
---
Two characters, a digit then a letter
    s = '0ú'     encode -> '101ú'  decode -> 101 copies of 'ú'
---
Two zeros
    s = '00'     encode -> '20'    decode -> ''
---
Nothing simpler fails: reported as the failing test case
    {{s = '0'      encode -> '10'    decode -> ''}}
    the format cannot tell a count's digits from data digits
```

## Template

Save as `test_props.py` and run `pytest test_props.py` (after `pip install hypothesis pytest`):

```python
from collections import Counter

from hypothesis import given, strategies as st


def insertion_sort(a):
    """Sort a in place and return it."""
    for i in range(1, len(a)):
        x, j = a[i], i
        while j > 0 and a[j - 1] > x:
            a[j] = a[j - 1]
            j -= 1
        a[j] = x
    return a


@given(st.lists(st.integers()))
def test_sort_properties(xs):
    out = insertion_sort(list(xs))
    assert all(p <= q for p, q in zip(out, out[1:]))      # ordered
    assert Counter(out) == Counter(xs)                    # a permutation of the input
    assert insertion_sort(list(out)) == out               # idempotent
    assert out == sorted(xs)                              # agrees with a trusted oracle


def rle_encode(s):
    """'aaabcc' -> '3a1b2c': each run becomes its length followed by its character."""
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{j - i}{s[i]}")
        i = j
    return "".join(out)


def rle_decode(code):
    out, count = [], ""
    for ch in code:
        if ch.isdigit():
            count += ch
        else:
            out.append(ch * int(count))
            count = ""
    return "".join(out)


@given(st.text())
def test_rle_round_trip(s):
    assert rle_decode(rle_encode(s)) == s     # fails: Hypothesis reports s='0'
```

## Pitfalls

- **Re-implementing the code in the test.** A property that recomputes the answer the same way shares the bug; state relations (ordered, permutation, round trip) or use a genuinely different oracle.
- **Too-weak properties.** "Output is ordered" alone passes `return []`; combine properties.
- **Filtering instead of constructing.** `.filter(is_sorted)` on random lists rejects almost everything; `.map(sorted)` builds valid inputs directly.
- **Unbounded sizes for slow code.** An O(n^2) function on lists of thousands of items makes tests slow; set `max_size`.
- **Deleting `.hypothesis`, or ignoring a flaky report.** The saved examples are regression tests; a failure that "goes away" on rerun usually depends on hidden state.

## Check yourself

Q: Why does `test_sort_properties` check both "ordered" and "permutation" when it also compares with `sorted(xs)`?
A: The oracle comparison alone is enough for correctness here, but the separate properties say *which* promise broke when it fails, and they still work in projects where no trusted oracle exists. Each property alone is too weak (an empty output is ordered; the input itself is a permutation).

Q: How would you make the RLE format survive digits in the text, and which property proves the fix?
A: Make the format unambiguous: write the character first, then its count, then a separator, so "aaab" becomes "a3;b1;". The decoder takes exactly one character (whatever it is, digits and separators included), then reads the digits up to the next ";". The same round-trip property, `rle_decode(rle_encode(s)) == s` over `st.text()`, then passes.

Q: Write a strategy for valid inputs to "remove duplicates from a sorted list" with values from -100 to 100.
A: `st.lists(st.integers(-100, 100), min_size=1).map(sorted)`: generate any list in range, then sort it, so every input meets the precondition without rejections.

## Lab

- **66 Plus One**: write the property "as an integer, the output is the input plus one, and it has no leading zero" with the strategy `st.lists(st.integers(0, 9), min_size=1).filter(lambda d: d[0] != 0 or len(d) == 1)`. Expected: your correct solution passes; a version that forgets the new leading digit fails and Hypothesis shrinks it to `d=[9]`.
- **26 Remove Duplicates from Sorted Array**: properties "a[:k] is strictly increasing" and "set(a[:k]) == set(input)" over `st.lists(st.integers(-100, 100), min_size=1).map(sorted)`. Expected: the correct version passes 100 examples; comparing `a[r]` with `a[w]` instead of `a[w - 1]` fails with `a=[0, 1]`.

> [!know]
> You now know how to state properties of an algorithm and let Hypothesis search for, and shrink, the inputs that break them.

=== lab | Break it, then prove it | 45 min
goal: Find a failing input for five subtly wrong functions with the stress harness, then fix each one by writing its invariant first

Five short functions each pass a quick read and a couple of examples. Your job: let `stress.py` find and shrink a failing input for each, then repair each function by stating the invariant it should keep and deriving the fix from it, not by trial and error.

## Setup

- Python 3.10 or later; `stress.py` from the stress-testing card, in the same folder.
- Two new files: `buggy.py` (the functions) and `break_it.py` (the oracles and the stress calls).

## Steps

1. Save the five functions as `buggy.py`. Read each one and predict, before running anything, whether you think it is correct.

```python
"""Five functions that pass a quick glance and fail somewhere. Find a failing input for each."""


def partition(a, pivot):
    """Rearrange a in place so that a[:k] < pivot <= a[k:]; return k."""
    i, j = 0, len(a) - 1
    while i < j:
        if a[i] < pivot:
            i += 1
        elif a[j] >= pivot:
            j -= 1
        else:
            a[i], a[j] = a[j], a[i]
    return i


def merge(a, b):
    """Merge two sorted lists into one sorted list."""
    out, i, j = [], 0, 0
    while i < len(a) or j < len(b):
        if j == len(b) or a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    return out


def dedupe(a):
    """Remove repeats from sorted a in place; return k so that a[:k] holds each value once."""
    if not a:
        return 0
    w = 1
    for r in range(1, len(a)):
        if a[r] != a[w]:
            a[w] = a[r]
            w += 1
    return w


def rotate(a, k):
    """Return a copy of a rotated right by k >= 0 steps: rotate([1, 2, 3], 1) == [3, 1, 2]."""
    if not a:
        return []
    return a[-k:] + a[:-k]


def lower_bound(a, x):
    """First index i with a[i] >= x in sorted a, or len(a) if there is none."""
    lo, hi = 0, len(a) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] >= x:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

2. Save the oracles and stress calls as `break_it.py`. Each oracle is written the obvious way; the wrappers report everything a contract promises.

```python
import bisect

import buggy
from stress import rand_list, stress


def is_sorted(a):
    return all(p <= q for p, q in zip(a, a[1:]))


def partition_brute(a, pivot):
    small = [x for x in a if x < pivot]
    return len(small), sorted(small), sorted(x for x in a if x >= pivot)


def partition_fast(a, pivot):
    k = buggy.partition(a, pivot)
    return k, sorted(a[:k]), sorted(a[k:])


def dedupe_fast(a):
    k = buggy.dedupe(a)
    return a[:k]


def rotate_brute(a, k):
    out = list(a)
    for _ in range(k):                   # one step at a time: obviously right
        out = out[-1:] + out[:-1]
    return out


stress(lambda r: (rand_list(r), r.randint(-5, 5)), partition_brute, partition_fast)
stress(lambda r: (sorted(rand_list(r)), sorted(rand_list(r))), lambda a, b: sorted(a + b), buggy.merge,
       valid=lambda a, b: is_sorted(a) and is_sorted(b))
stress(lambda r: (sorted(rand_list(r)),), lambda a: sorted(set(a)), dedupe_fast, valid=is_sorted)
stress(lambda r: (rand_list(r), r.randint(0, 12)), rotate_brute, buggy.rotate, valid=lambda a, k: k >= 0)
stress(lambda r: (sorted(rand_list(r)), r.randint(-6, 6)), bisect.bisect_left, buggy.lower_bound,
       valid=lambda a, x: is_sorted(a))
```

3. Run `python break_it.py`. For each FAIL, copy the shrunk input and work out by hand what the function does on it.
4. For each function, **write the invariant first** as a comment (what is true of i, j, w, lo, hi at the top of every iteration), then change only the lines that break it. The Check yourself answers below give the fixes; try each before you look.
5. Rerun `python break_it.py` until all five print `OK`. Then raise `trials` to 20,000 and try other seeds.
6. Write one journal line per bug: the edge it lived on (empty, one item, equal values, k >= n, the last index).

## What you should see

With seed 0, five failures, each shrunk to a tiny case:

- `partition`: shrunk to `([0], 1)`. It returns k = 0, but 0 < 1 belongs on the left.
- `merge`: shrunk to `([], [0])`, and the fast version crashes with `IndexError`. A crash counts as a failure.
- `dedupe`: shrunk to `([0, 1],)`. It returns `[0]`, losing the 1.
- `rotate`: shrunk to `([0, -1], 5)`. Rotating two items by 5 should equal rotating by 1, giving `[-1, 0]`; it returns the list unchanged. The shrinker stops at 5 because 0, 2 and 4 (its only simplifications) all pass.
- `lower_bound`: shrunk to `([0], 1)`. It returns 0; the answer is 1 (past the end).

After the fixes, each line reads `OK: 2000 random tests passed (seed 0)`.

## Check yourself

Q: Fix `partition` by writing its invariant first.
A: Use half-open regions: `i, j = 0, len(a)` with the invariant a[:i] < pivot, a[j:] >= pivot, a[i:j] unknown. Loop `while i < j`: if `a[i] < pivot`, then `i += 1`; otherwise `j -= 1` and swap a[i] with a[j]. Return i. The original closed version stopped with one unexamined item when i met j.

Q: Fix `merge`.
A: Invariant: out is the sorted merge of a[:i] and b[:j]. Take from a only when a still has items and either b is exhausted or a[i] <= b[j]: `if i < len(a) and (j == len(b) or a[i] <= b[j]):`. The original read a[i] after a was exhausted.

Q: Fix `dedupe` and `rotate`.
A: `dedupe`: the invariant is "a[:w] holds the distinct values of a[:r]", so the last kept value is a[w - 1]: compare `a[r] != a[w - 1]`. `rotate`: rotating by k equals rotating by k % n, so set `k %= len(a)` and return `a[len(a) - k:] + a[:len(a) - k]`, which also avoids the `a[-0:]` trap when k becomes 0.

Q: Fix `lower_bound`.
A: The answer can be len(a), so the candidate range is the half-open [0, len(a) + 1), expressed as `lo, hi = 0, len(a)` with the invariant "everything left of lo is < x, everything from hi on is >= x". The original `hi = len(a) - 1` excluded the past-the-end answer.

> [!know]
> You now know how to make a random tester find and shrink a failing input, and how to fix the bug by restoring the invariant it broke.

=== practice
- 27 core
  cue: Remove every copy of one value in place, return how many remain, and the order of what remains is free.
  hint: Use one index to read every item and another to mark where the next item you keep should go. What is true of the part before the second index?
  insight: Read/write pointers: a[:w] always holds the non-val items of a[:r]; copy a[r] to a[w] when it is not val. Since w <= r, nothing unread is overwritten, and w is the answer when r reaches the end.
  cost: O(n) time, O(1) extra space
  pattern: correct-inplace
- 26 core
  cue: The array is sorted and each value must appear once at the front, in place.
  hint: In a sorted array, equal values sit next to each other. Which already-kept value must a new item differ from?
  insight: Keep a write index w with the invariant "a[:w] holds the distinct values of a[:r]"; a[r] is new exactly when it differs from the last kept value a[w - 1], so copy it to a[w] and advance. Comparing with a[w] instead is the classic bug.
  cost: O(n) time, O(1) extra space
  pattern: correct-inplace
- 58 core
  cue: The string may end with spaces, and only the last run of letters matters.
  hint: Where does the last word end, and where does it start? Think about walking from the right end of the string.
  insight: Scan from the end: skip trailing spaces, then count letters until a space or the start. The edge cases (trailing spaces, a single word, leading spaces) are handled by the two loops; s.split()[-1] is an O(n)-space oracle for tests.
  cost: O(n) time, O(1) extra space
  pattern: correct-edges
- 66 core
  cue: A number is stored as a list of decimal digits and you add one to it.
  hint: Do it as you would on paper from the rightmost digit. Which input makes the result longer than the input?
  insight: Walk from the right, turning 9s into 0s while the carry continues; the first digit below 9 is incremented and you are done. If every digit was 9, the answer is a 1 followed by all zeros, the edge case most solutions forget.
  cost: O(n) time, O(1) extra space apart from the possible new list
  pattern: correct-edges
- 1299 core
  cue: Each position must be replaced by the largest value strictly to its right, and the last becomes -1.
  hint: The brute force takes a maximum over every suffix. What could you carry from one position to the next if you walked in the other direction?
  insight: Walk right to left with best = max of everything already passed (initially -1); write best into position i, then update best with the old a[i]. The invariant "best = max(a[i + 1:])" makes each answer O(1).
  cost: O(n) time, O(1) extra space
  pattern: correct-invariant
- 374 core
  cue: You can only ask higher, lower or correct about a hidden number in 1..n, with n up to 2^31 - 1.
  hint: Keep the range of numbers that could still be the answer. What should each question do to that range, and how do you write it so it always shrinks?
  insight: Keep the candidates in a half-open range [lo, hi), starting at [1, n + 1); guess mid = (lo + hi) // 2 and set hi = mid if the pick is lower, lo = mid + 1 if higher. The range always shrinks, so at most n.bit_length() guesses (31) are needed.
  cost: O(log n) guesses, O(1) space
  pattern: correct-invariant
