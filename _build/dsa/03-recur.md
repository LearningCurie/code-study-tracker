---
key: recur
name: Recursion, induction and divide and conquer
stage: found
summary: Write recursive functions you can trust by treating the recursive call as an induction hypothesis, find their running time with recursion trees and the master theorem, and run them safely in Python.
why: Recursion is how you think about anything defined in terms of smaller copies of itself: nested data, trees, expressions, search spaces and divide and conquer. Trees, backtracking, dynamic programming and graph search in later modules are all recursion with extra bookkeeping, so the habits here (state what the function returns, handle the smallest cases, trust the smaller call, count the work level by level) pay off in every later module. In real software recursion walks file systems, JSON documents, syntax trees and the DOM, and its failure mode is just as real: Python stops at about 1,000 nested calls, so production code needs to know when to convert recursion into a loop with an explicit stack.
outcomes:
- Prove simple statements and recursive functions correct by weak and strong induction
- Trace call frames on the call stack and tell recursion depth (space) apart from the number of calls (time)
- Design recursive functions with the simplify-and-delegate recipe, with base cases that cover every smallest input and a measure that always decreases
- Write recurrences for recursive code and solve them with recursion trees, the master theorem and numerical checks
- Implement merge sort, inversion counting and fast modular exponentiation as divide and conquer, and justify their costs
- Run recursion safely in Python (recursion limit, memoisation with functools.cache) and convert recursion into an explicit stack with identical output
cues:
- The problem is defined in terms of smaller copies of itself (a row from the previous row, a string from its halves, n from n // 2)
- The input is nested or tree shaped: folders, JSON, expressions, brackets
- A huge exponent or index (up to 10^9 or 10^18) that must be reached by halving, not by stepping
- "Split into halves" or "combine the answers of two parts", where the work across the split can be counted cheaply
- Not if: the same subproblem is solved again and again (memoise it, which is dynamic programming), or the depth can reach 10^5 in Python (use a loop or an explicit stack)
traps:
- A base case that some inputs never reach (n - 2 jumping over 1, an empty list not handled), giving infinite recursion or a RecursionError
- Calling the same subproblem twice per level (`half = power(x, n // 2) * power(x, n // 2)`), which silently turns O(log n) into O(n)
- Forgetting the work outside the recursive calls, such as slicing, when writing the recurrence
- Assuming Python will optimise tail calls or allow deep recursion: the default limit is about 1,000 frames
- Applying the master theorem to recurrences it does not cover, such as T(n) = T(n - 1) + n or unequal splits
systems:
- CPython's compiler walks syntax trees recursively: compiling one expression of 10,000 chained additions raised "RecursionError: maximum recursion depth exceeded during compilation" in our test
- `json.dumps` and `copy.deepcopy` recurse through nested containers, so pathological nesting is a known way to exhaust the stack
- External merge sort (divide into sorted runs, then merge) is how databases such as PostgreSQL sort data larger than memory
- Python's built-in `pow(base, exp, mod)` uses fast exponentiation, the core operation of RSA and Diffie-Hellman key exchange
further:
- Chapter · 40 min | Jeff Erickson: Algorithms, chapter 1 Recursion (simplify and delegate, Hanoi, mergesort, recursion trees, PDF pages 1-14) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/01-recursion.pdf
- Notes · 30 min | Jeff Erickson: Appendix II, Solving Recurrences (guess and confirm, recursion trees, PDF pages 2-10) | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/99-recurrences.pdf
- Chapter · 25 min | Composing Programs 1.7: Recursive Functions (Python, tree recursion) | https://composingprograms.com/pages/17-recursive-functions.html#the-anatomy-of-recursive-functions
---

=== primer | How does a proof by induction work, and why does it prove recursive code correct? | 14 min
goal: Write weak and strong induction proofs, and use the same structure to argue that a recursive function returns the right answer for every input
tag: recur-induction | Proof by induction
link: Jeff Erickson: Appendix I, Proof by Induction (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/98-induction.pdf | 20 min: '3 Stamps and Recursion' on PDF pages 6-8 (a boilerplate strong-induction proof), then '10 Recursive Functions' on page 19
practice: 231, 326

> [!key]
> To prove a claim P(n) for every n from some starting point, prove it for the smallest cases (the **base cases**), then prove that if it holds for smaller values it also holds for n (the **inductive step**). Weak induction assumes only P(n - 1); **strong induction** may assume P(k) for every k < n. A recursive function has exactly this shape: its base cases are the base cases of the proof, and trusting the recursive call on a smaller input is the inductive hypothesis.

## Intuition

A row of dominoes falls completely if you can show two things: the first one falls, and any domino that falls knocks over the next. You never watch all of them; the two facts together cover every domino. Induction is that argument written down, and a recursive function relies on it every time it calls itself on a smaller input.

## How it works

### Weak induction

Claim: 1 + 2 + ... + n = n(n + 1)/2 for every n >= 1.

- **Base case**, n = 1: the sum is 1 and 1 x 2 / 2 = 1.
- **Inductive step**: assume the formula holds for n - 1, that is, 1 + ... + (n - 1) = (n - 1)n/2. Then 1 + ... + n = (n - 1)n/2 + n = n(n + 1)/2.

Each step uses only the case directly before it.

### Strong induction

Claim: every amount n >= 12 can be paid exactly with 4p and 5p stamps.

- **Base cases**: 12 = 4 + 4 + 4, 13 = 4 + 4 + 5, 14 = 4 + 5 + 5, 15 = 5 + 5 + 5.
- **Inductive step**: for n >= 16, assume every amount from 12 to n - 1 can be paid. Since n - 4 >= 12, pay n - 4 and add one 4p stamp.

The step reaches back four places, so it needs four base cases: with only 12 as a base, the step for 17 would rely on 13, which nothing proved. The rule to remember: **the base cases must cover everything the step can land on**.

### From proofs to code

The proof is an algorithm. Paying n means paying n - 4 and adding a stamp:

- the base cases 12 to 15 are the `if` branches that return directly;
- the inductive hypothesis is the recursive call `postage(n - 4)`, which you trust because n - 4 is smaller and still at least 12;
- the inductive step is the line that turns that answer into the answer for n.

To prove a recursive function correct, write down what it returns (the claim), check the base cases, and show that if every call on a smaller input returns the right thing, this call does too. To prove that it **terminates**, name a quantity (a **variant**, here n) that is a whole number, is bounded below, and strictly decreases with every call.

## Cost

Induction also proves running times. Claim: the function T(n) = 2T(n - 1) + 1 with T(0) = 0 equals 2^n - 1. Base: T(0) = 0 = 2^0 - 1. Step: if T(n - 1) = 2^(n-1) - 1, then T(n) = 2(2^(n-1) - 1) + 1 = 2^n - 1. This "guess, then confirm by induction" method solves recurrences that the recursion-tree card does not cover.

The `postage` recursion makes about (n - 12)/4 calls, each doing O(1) work: O(n) time and O(n) stack depth. Halving recursions such as "n is a power of two if n is 1, or n is even and n / 2 is a power of two" make about log2 n calls: O(log n) time and depth.

## When to use it

Use induction whenever correctness depends on "and so on": loops (where it becomes a loop invariant, in the correctness module), recursive functions, recurrences for running time, and structural claims about trees (every binary tree with n nodes has n + 1 empty child slots). Use strong induction when the step needs a case further back than n - 1, which is the normal situation for divide and conquer (the halves are about n/2). When you are not sure the claim is even true, test it on many small cases first: a brute-force check is cheaper than a failed proof.

## Worked trace

Strong induction as a chain: each amount from 16 on is built from the amount four below it.

```steps
Base cases, checked by hand: 12, 13, 14 and 15
    12 = 4+4+4   13 = 4+4+5   14 = 4+5+5   15 = 5+5+5
---
16: n - 4 = 12 is a base case, so 16 = (4+4+4) + 4
    {{16}} <- 12
---
17: uses 13, also a base case: 17 = (4+4+5) + 4
    16 <- 12    {{17}} <- 13
---
18 and 19 use 14 and 15
    16 <- 12    17 <- 13    {{18}} <- 14    {{19}} <- 15
---
20 uses 16, which was itself proved from 12: the chain keeps going
    {{20}} <- 16 <- 12
---
Why four base cases? 17 needs 13, 18 needs 14, 19 needs 15. With only 12 proved, 17 would rest on nothing
    17 <- {{13 ?}}
```

## Template

The recursive function mirrors the proof line by line, and a brute-force loop checks the claim on many values before you trust it:

```python
def postage(n):
    """Return (fours, fives) with 4 * fours + 5 * fives == n, for n >= 12."""
    if n < 12:
        raise ValueError("amounts below 12 cannot all be paid")
    base = {12: (3, 0), 13: (2, 1), 14: (1, 2), 15: (0, 3)}
    if n in base:                       # base cases of the proof
        return base[n]
    fours, fives = postage(n - 4)       # inductive hypothesis: trust the smaller case
    return fours + 1, fives             # inductive step

for n in range(12, 900):
    fours, fives = postage(n)
    assert fours >= 0 and fives >= 0 and 4 * fours + 5 * fives == n
assert all(n * (n + 1) // 2 == sum(range(1, n + 1)) for n in range(1, 500))
print(postage(31))                      # (4, 3)
```

## Pitfalls

- **Base cases that do not cover the step.** If the step reaches back k places, you need k consecutive base cases (or a step that always lands on a proved case).
- **A step that fails at the smallest size.** The classic false proof that "all horses are the same colour" works for every step except from 1 horse to 2, where the two groups of n - 1 horses do not overlap.
- **Assuming what you want to prove.** The hypothesis is about smaller inputs only; using P(n) to prove P(n) is circular.
- **A claim too weak to carry the step.** Sometimes you must prove something stronger (for a tree: "returns the height **and** whether it is balanced") so that the hypothesis gives the step enough to work with.
- **Termination is a separate proof.** Correct base cases are useless if some input never reaches them; name the variant that decreases.

## Check yourself

Q: Prove by induction that a recursive function `count(n)` defined as `0 if n == 0 else 1 + count(n // 2)` returns the number of binary digits of n for n >= 1 (and 0 for n = 0). Which kind of induction do you need?
A: Strong induction, because the call is on n // 2, not n - 1. Base: count(0) = 0, and n = 0 has no digits by convention. Step: for n >= 1, n // 2 drops the last binary digit, so it has one digit fewer than n (for n = 1, n // 2 = 0 has 0 digits and 1 has 1). By the hypothesis count(n // 2) is that smaller number of digits, so 1 + count(n // 2) is the number of digits of n. It terminates because n // 2 < n for n >= 1.

Q: Someone proves "every amount n >= 12 can be paid with 4p and 5p stamps" with the single base case 12 and the step "pay n - 4, add a 4p stamp". Where exactly does the proof break?
A: The step for n = 13 needs n - 4 = 9, which is below 12 and not covered; so do 14 (needs 10) and 15 (needs 11). The proof only reaches 12, 16, 20, ... The fix is base cases 12, 13, 14 and 15.

Q: Which claim would you prove by induction to show that a recursive "is this a power of 3?" test returns True exactly for 1, 3, 9, 27, ...?
A: For every n >= 1: the function returns True if and only if n = 3^j for some j >= 0. Base: n = 1 is 3^0 and returns True; n not divisible by 3 (other than 1) returns False and is not a power of 3. Step: if 3 divides n, then n is a power of 3 exactly when n / 3 is, and by the hypothesis the call on n / 3 < n answers that correctly.

## Lab

- **231** Power of Two: write it recursively (n is a power of two if it is 1, or if it is even and n / 2 is one), then prove it correct with the template above, then compare with the bit test `n > 0 and n & (n - 1) == 0`. Expected: O(log n) time and O(log n) stack for the recursion, O(1) for the bit test; 1 -> True, 0 -> False, 96 -> False, 1024 -> True, -8 -> False.
- **326** Power of Three: the same shape with 3. Expected: O(log3 n) calls; 1 -> True, 243 -> True, 45 -> False, 0 -> False.

> [!know]
> You now know how to prove a claim for all n by induction, and that a correct recursive function is that proof turned into code.

=== primer | What happens on the call stack when a function calls itself? | 13 min
goal: Trace call frames by hand, read a traceback as a picture of the stack, and tell recursion depth (memory) apart from the number of calls (time)
tag: recur-stack | Call stack and frames
link: Composing Programs 1.7: Recursive Functions | https://composingprograms.com/pages/17-recursive-functions.html#the-anatomy-of-recursive-functions | 15 min: 1.7.1 'The Anatomy of Recursive Functions' (environment diagrams of each frame), then 1.7.3 'Printing in Recursive Functions'
practice: 509, 344

> [!key]
> Every call creates a **frame**: its own copies of the parameters and local variables, plus the place to resume in the caller. Frames sit on the **call stack**; a call pushes one, a return pops it and hands a value to the frame below. A recursive function therefore has many frames of the same function alive at once, each with its own `n`. The deepest the stack gets (the **depth**) costs memory; the total number of frames ever created (the **calls**) costs time.

## Intuition

A stack of sticky notes on your desk. You are halfway through a task when it needs a smaller task done first, so you write "come back here, I was at step 3, n was 13" on a note, put it on the pile, and start the smaller task on a fresh note. When a task finishes you remove its note, read the one underneath and carry on where it says. Only the top note is ever active, and each note remembers its own numbers.

## How it works

### Frames

A frame holds the arguments, the local variables, and the instruction to resume at in the caller. In CPython each frame also holds the evaluation stack for the expression in progress, which is how `to_binary(n // 2) + str(n % 2)` remembers that it still has to add the last digit after the inner call returns. Because every frame has its own locals, the `n` in one call is never overwritten by the `n` of a deeper call.

### Push, run, pop

1. A call evaluates its arguments, pushes a new frame and jumps into the function.
2. The function runs until it returns, possibly making calls of its own (more frames on top).
3. `return` pops the frame and delivers the value to the caller's frame, which resumes exactly where it stopped.

### Depth versus calls

A **linear** recursion (one recursive call per frame, like `to_binary`) creates a chain: depth equals the number of calls. A **tree** recursion (several calls per frame, like naive Fibonacci) creates a tree of calls but at any moment only one root-to-leaf path is on the stack. `fib(30)` makes 2,692,537 calls, yet the stack never holds more than 30 Fibonacci frames at once, because each subtree is finished and popped before its sibling starts.

### What Python adds

A traceback is a printout of the stack at the moment of the error, oldest frame first. CPython refuses to go deeper than the **recursion limit** (`sys.getrecursionlimit()`, 1000 by default) and raises `RecursionError`; in our test a simple recursive function managed 999 nested calls and failed on the 1,000th. Python never removes frames for tail calls, so a recursion n levels deep always needs n frames. The safety card at the end of this module covers raising the limit and replacing recursion with a loop.

## Cost

- **Time** = (number of calls) x (work per call, excluding the recursive calls). `to_binary(n)` makes floor(log2 n) + 1 calls doing O(1) work each (ignoring the string building): O(log n). Naive `fib(n)` makes 2F(n + 1) - 1 calls, about 1.618^n: exponential.
- **Space** = (maximum depth) x (frame size), plus whatever the frames hold. `to_binary` is O(log n) deep, `fib(n)` is n deep: O(n) space for an exponential number of calls. A frame is small but not free: our pure-Python test reached a depth of 500,000 with a raised limit, and the process grew by about 73 MB, roughly 150 bytes per level.

## When to use it

Trace frames by hand when a recursive function misbehaves on a small input: write each frame's arguments and what it is waiting for, as in the worked trace. Reason about depth whenever recursion depth grows with the input (linked lists, degenerate trees, n - 1 recursions): in Python anything beyond a few thousand levels needs a loop or an explicit stack. Reason about the number of calls whenever a function calls itself more than once per frame: that is where exponential time hides.

## Worked trace

`to_binary(13)` returns `"1101"`. Each line in the state is a frame; the top line is the active one.

```steps
Call to_binary(13): n = 13 is not below 2, so it must first call to_binary(6)
    {{to_binary(n=13)  waiting: to_binary(6) + "1"}}
---
to_binary(6) pushes a frame with its own n = 6, and calls to_binary(3)
    {{to_binary(n=6)   waiting: to_binary(3) + "0"}}
    to_binary(n=13)  waiting: to_binary(6) + "1"
---
to_binary(3) calls to_binary(1)
    {{to_binary(n=3)   waiting: to_binary(1) + "1"}}
    to_binary(n=6)   waiting: to_binary(3) + "0"
    to_binary(n=13)  waiting: to_binary(6) + "1"
---
to_binary(1) is a base case: n < 2, so it returns "1" with no further call. Depth 4, the maximum
    {{to_binary(n=1)   returns "1"}}
    to_binary(n=3)   waiting: to_binary(1) + "1"
    to_binary(n=6)   waiting: to_binary(3) + "0"
    to_binary(n=13)  waiting: to_binary(6) + "1"
---
Pop. The n = 3 frame resumes exactly where it stopped: "1" + "1" = "11"
    {{to_binary(n=3)   returns "11"}}
    to_binary(n=6)   waiting: to_binary(3) + "0"
    to_binary(n=13)  waiting: to_binary(6) + "1"
---
Pop. The n = 6 frame: "11" + "0" = "110"
    {{to_binary(n=6)   returns "110"}}
    to_binary(n=13)  waiting: to_binary(6) + "1"
---
Pop. The first frame: "110" + "1" = "1101", and the stack is empty again
    {{to_binary(n=13)  returns "1101"}}
```

## Template

A tracing decorator shows the stack for any recursive function: each call and each result, indented by depth. Decorating rebinds the name, so the recursive calls go through the wrapper too.

```python
import functools

def trace(fn):
    """Decorator: print each call and its result, indented by recursion depth."""
    depth = 0

    @functools.wraps(fn)
    def wrapper(*args):
        nonlocal depth
        print("  " * depth + f"{fn.__name__}({', '.join(map(repr, args))})")
        depth += 1
        try:
            result = fn(*args)
        finally:
            depth -= 1
        print("  " * depth + f"-> {result!r}")
        return result
    return wrapper

@trace
def to_binary(n):
    """Binary digits of n >= 0 as a string."""
    if n < 2:
        return str(n)
    return to_binary(n // 2) + str(n % 2)

to_binary(13)
```

It prints:

```text
to_binary(13)
  to_binary(6)
    to_binary(3)
      to_binary(1)
      -> '1'
    -> '11'
  -> '110'
-> '1101'
```

## Pitfalls

- **Forgetting `return`.** Writing `to_binary(n // 2) + str(n % 2)` without `return` computes the answer and throws it away; the caller receives `None`.
- **Shared state that should be per frame.** A global counter or a mutable default argument (`def f(n, seen=[])`) is shared by every frame and every later call; pass state explicitly or create it inside.
- **Confusing depth with calls.** `fib(40)` is only 40 deep, so it does not hit the recursion limit; it is slow because it makes about 330 million calls.
- **Deep linear recursion.** Recursing once per element of a list or linked list of 10^4 items exceeds the default limit.
- **Reading tracebacks upside down.** Python prints the oldest frame first and the failing frame last; in a RecursionError the repeated middle lines are the recursion itself.

## Check yourself

Q: With the decorator above, how many lines does `to_binary(2)` print, and what are they?
A: Four lines: `to_binary(2)`, then indented `to_binary(1)` and `-> '1'`, then `-> '10'`. The call on 2 is waiting for to_binary(1); the base case returns "1", and the outer frame adds "0".

Q: `def total(a, i): if i == len(a): return 0` then `total(a, i + 1) + a[i]` (with no `return` on the second line). What does `total([1, 2, 3], 0)` do?
A: It raises a TypeError. The base case returns 0 to the frame for i = 2, which computes 0 + 3 and discards it, returning None. The frame for i = 1 then evaluates None + 2. The missing `return` breaks the chain of values back down the stack.

Q: Naive `fib(n)` calls `fib(n - 1)` and `fib(n - 2)`. For n = 30, how deep does the stack get and how many calls are made? Which of the two numbers is the problem?
A: The deepest path is fib(30), fib(29), ..., fib(1): 30 frames. The number of calls is 2F(31) - 1 = 2,692,537. Depth is harmless; the call count is the problem, and memoisation fixes it by making each fib(k) compute once.

## Lab

- **509** Fibonacci Number: write the naive recursion and count calls with a counter (or the decorator, for small n). Expected: fib(10) = 55 with 177 calls; fib(30) = 832,040 with 2,692,537 calls but a stack only 30 deep; with `functools.cache` the same answer takes 31 calls.
- **344** Reverse String: reverse the list in place by recursion on two indices, then trace the frames for a five-letter input. Expected: about n/2 frames deep (3 for five letters), O(n) time; the recursion needs O(n) stack, so beyond a few thousand characters it exceeds the default limit, while a two-index loop is O(1) space.

> [!know]
> You now know how frames are pushed and popped, why depth and number of calls measure different costs, and how to read a recursive computation off the stack.

=== primer | How do you write a recursive function without tracing every call? | 15 min
goal: Design recursive functions with the simplify-and-delegate recipe: a precise contract, base cases that cover every smallest input, a strictly smaller recursive call that you trust, and a combine step
tag: recur-delegate | Simplify and delegate
link: Jeff Erickson: Algorithms, chapter 1 Recursion (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/01-recursion.pdf | 20 min: 'Simplify and Delegate' on PDF pages 2-3 (the Recursion Fairy), then 'Tower of Hanoi' on pages 4-6
practice: 344, 779

> [!key]
> Do not trace a recursion to design it. Write the **contract** (exactly what the function returns for any valid input), solve the **smallest inputs** directly, and for anything bigger, make one or more **strictly smaller** instances, **trust** the recursive calls to honour the contract (Erickson calls this handing them to the Recursion Fairy), and **combine** their answers. If the contract, the base cases and the combine step are right, induction guarantees the whole function is right.

## Intuition

A manager asked to count every file in a department does not open every folder herself. She counts the loose files on her own desk and asks each team lead for their team's total, trusting each lead to do the same with their own teams. She does not need to know how the leads do it, only that each one answers the same question for a smaller part of the organisation and that the smallest teams answer directly.

## How it works

### The recipe

1. **Contract.** One sentence: "`flatten(x)` returns a flat list of all the non-list items inside x, in left-to-right order." Vague contracts produce wrong combine steps.
2. **Base cases.** The inputs too small to split: the empty list, a single item, n = 0 or 1, i >= j. Every input must eventually reach one of them.
3. **Reduce.** Make strictly smaller instances of the *same* problem: drop the first element, halve n, move both indices inward, recurse into each child.
4. **Trust and combine.** Assume each recursive call returns exactly what the contract says, and build this call's answer from those answers. Do not trace inside them.
5. **Check progress.** Name a whole-number measure that decreases with every call and is bounded below (n, j - i, the length of the list, the depth of nesting). That proves the recursion ends.

### Example: Tower of Hanoi

Move a tower of n discs from peg A to peg C, one disc at a time, never placing a larger disc on a smaller one. Simplify: to move the largest disc, everything above it must be out of the way, on the spare peg B. Delegate: "move n - 1 discs from A to B" is the same problem, smaller, so trust it. Then move the largest disc from A to C, and trust "move n - 1 discs from B to C". Base case: 0 discs, do nothing. Three lines, and correct for every n, because each delegated tower sits on discs larger than all of its own.

### Base cases and progress

Two bugs cause most recursion failures. **An unreachable base case**: `f(n) = f(n - 2)` with the single base case `n == 1` never stops for even n, because it jumps from 2 to 0 to -2 and onwards. **No progress**: a recursive call on an input that is not smaller, such as a binary search over the half-open range [lo, hi) that recurses on [mid, hi): a one-element range gives mid = lo, so the call repeats itself forever. Check both on the smallest inputs: for every size from 0 up to the size of your base cases, ask "which branch runs, and is the next call smaller?".

### Several calls, one problem

The recipe is the same when you make several calls (one per child folder, one per half, one per choice). Each call must be a smaller instance of the same contract, and the combine step must use their answers only through the contract.

## Cost

Delegating hides work, so count it: write how many calls each frame makes, on what sizes, and how much work it does outside them. Hanoi makes two calls on n - 1 plus one move: T(n) = 2T(n - 1) + 1, so 2^n - 1 moves (proved by induction in the first card); 64 discs would need about 1.8 x 10^19 moves. `flatten` does O(1) work per item and per list (plus list concatenation), so its cost is about the total size of the nested structure, and its depth is the depth of nesting. The next card turns this counting into a method.

## When to use it

Use recursion when the problem is naturally self-similar: nested data (folders, JSON, expressions), trees, "split into parts and combine", and search over choices. In Python, prefer a loop when the recursion is a simple chain over a long sequence (one call per element), because each frame costs time and the depth limit is about 1,000. When the same smaller instance is requested many times, add memoisation (`functools.cache`), which turns the recursion into dynamic programming, the subject of a later module.

## Worked trace

Hanoi with 3 discs, A to C. Moves 1 to 3 are the delegated call "move 2 discs from A to B", move 4 is the largest disc, and moves 5 to 7 are "move 2 discs from B to C".

```steps
Start: three discs on A, largest at the bottom
    A: 3 2 1    B:          C:
---
Move 1, A to C (inside the delegated move of 2 discs from A to B)
    A: 3 2      B:          C: {{1}}
---
Move 2, A to B
    A: 3        B: {{2}}      C: 1
---
Move 3, C to B: the delegated call is done, 2 discs now on B
    A: 3        B: 2 {{1}}    C:
---
Move 4, A to C: the largest disc moves once, onto an empty peg
    A:          B: 2 1      C: {{3}}
---
Move 5, B to A (inside the second delegated call: 2 discs from B to C)
    A: {{1}}      B: 2        C: 3
---
Move 6, B to C
    A: 1        B:          C: 3 {{2}}
---
Move 7, A to C: done in 2^3 - 1 = 7 moves
    A:          B:          C: 3 2 {{1}}
```

## Template

```python
def hanoi(n, src="A", dst="C", via="B"):
    """Yield the moves (from_peg, to_peg) that carry n discs from src to dst."""
    if n == 0:                                   # base case: nothing to move
        return
    yield from hanoi(n - 1, src, via, dst)       # trust: clear the n - 1 smaller discs
    yield (src, dst)                             # move the largest disc
    yield from hanoi(n - 1, via, dst, src)       # trust: put them back on top

def flatten(x):
    """Flat list of the non-list items inside x, left to right."""
    if not isinstance(x, list):
        return [x]                               # base case: a single item
    out = []
    for part in x:                               # every part is smaller than x
        out += flatten(part)
    return out

def is_palindrome(s, i=0, j=None):
    """True if s[i..j] reads the same both ways."""
    if j is None:
        j = len(s) - 1
    if i >= j:                                   # base case: 0 or 1 characters left
        return True
    return s[i] == s[j] and is_palindrome(s, i + 1, j - 1)   # j - i shrinks by 2

print(list(hanoi(2)))                            # [('A', 'B'), ('A', 'C'), ('B', 'C')]
print(flatten([1, [2, [3, []], 4], [[5]]]))      # [1, 2, 3, 4, 5]
print(is_palindrome("racecar"), is_palindrome("abca"))   # True False
```

## Pitfalls

- **Tracing instead of trusting.** If you find yourself simulating the inner calls to design the outer one, go back to the contract.
- **A contract that changes between calls.** If the top-level call returns a list but the recursive call is used as if it returned a count, the combine step is wrong for every n.
- **Base cases that some inputs skip** (n - 2 recursions, odd and even lengths, empty input).
- **Calls that are not smaller**, or smaller in a quantity that is not bounded below (negative n).
- **Slicing to make smaller instances.** `f(s[1:-1])` copies the string at every level, O(n^2) in total; pass indices as `is_palindrome` does.

## Check yourself

Q: Fill in the missing line so that `count_items(x)` returns the number of non-list items inside a nested list: `def count_items(x): if not isinstance(x, list): return 1` then `return ______`.
A: `return sum(count_items(part) for part in x)`. Each part is smaller, the contract says each call returns its own count, and the combine step adds them. The empty list gives `sum` of nothing, 0, so it needs no separate base case.

Q: `def half_down(n): return 0 if n == 1 else 1 + half_down(n - 2)` is meant to count steps of 2 from n down to 1. For which inputs does it never reach the base case, and how do you fix it?
A: Every even n (and every n below 1): from an even number, n - 2 stays even, skips 1, and goes below zero forever until the recursion limit stops it. Fix the base case to cover the whole bottom range, for example `if n <= 1: return 0`, and decide what the function should mean for even n.

Q: How many moves does `hanoi(10)` yield, and why is that the minimum possible?
A: 2^10 - 1 = 1023. By induction: the largest disc must move at least once, and before its first move all other n - 1 discs must be on the spare peg (at least T(n - 1) moves), and after its last move they must be moved onto it (at least T(n - 1) more). So any solution needs at least 2T(n - 1) + 1 moves, the same recurrence.

## Lab

- **344** Reverse String: write it with the recipe. Contract: "reverse(s, i, j) reverses s[i..j] in place". Base case: fewer than two characters left. Reduce: swap the ends, then trust the call on the inside. Expected: O(n) time, about n/2 frames of stack; ["r", "o", "t", "o", "r"] stays the same and ["d", "r", "a", "w"] becomes ["w", "a", "r", "d"].
- **779** K-th Symbol in Grammar (derive): do not build the rows. Write the contract for kth(n, k), then ask which symbol of row n - 1 produced position k of row n. Expected: O(n) time and stack; rows 1 to 4 are 0, 01, 0110, 01101001, so n = 4, k = 5 gives 1 and n = 4, k = 6 gives 0. Building the whole row instead costs O(2^n).

> [!know]
> You now know how to design a recursive function from its contract, base cases and a trusted smaller call, and how to check that it always ends.

=== primer | How do you find the running time of a recursive function? | 16 min
goal: Write the recurrence for recursive code, solve it with a recursion tree or the master theorem, and confirm the answer numerically
tag: recur-tree | Recursion trees and recurrences
link: MIT 6.006 Recitation 3 notes (PDF) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/1869dbf640ded6b31f1bd369d2001ef5_MIT6_006S20_r03.pdf | 15 min: the recurrences and 'Master Theorem' part on PDF pages 5-6, with its three cases drawn as recursion trees (leaves dominate, balanced, root dominates)
link: Jeff Erickson: Appendix II, Solving Recurrences (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/99-recurrences.pdf | 25 min: '3 Divide and Conquer Recurrences (Recursion Trees)' on PDF pages 6-10, which derives the three cases from level sums
practice: 509, 779

> [!key]
> Write the cost as a **recurrence**: T(n) = (number of calls) x T(smaller size) + (work outside the calls). Draw the **recursion tree**, add the work level by level, and sum the levels. For T(n) = a T(n/b) + f(n), the **master theorem** compares the root's work f(n) with the leaves' count n^(log_b a): whichever grows faster dominates, and if they match, every level costs the same and you multiply by the log n levels. Always check the answer numerically by computing T(n) for growing n.

## Intuition

An organisation chart: every manager does some work personally and splits the rest among a few reports, each handling a smaller share. Total effort is the sum over all levels of the chart. If each level's total shrinks fast, the top manager's own work dominates; if each level's total grows, the people at the bottom dominate; if every level costs the same, the total is one level's cost times the number of levels.

## How it works

### Step 1: write the recurrence

Read it off the code. Count the recursive calls and their input sizes, then add the work done outside them, including hidden work such as slicing.

| Code | Recurrence | Solution |
|---|---|---|
| Binary search: one call on half, O(1) besides | T(n) = T(n/2) + 1 | Theta(log n) |
| Sum of a list by `a[0] + f(a[1:])` (slice is O(n)) | T(n) = T(n - 1) + n | Theta(n^2) |
| Merge sort: two halves plus an O(n) merge | T(n) = 2T(n/2) + n | Theta(n log n) |
| Visit every node of a balanced tree | T(n) = 2T(n/2) + 1 | Theta(n) |
| Tower of Hanoi | T(n) = 2T(n - 1) + 1 | 2^n - 1 |
| Naive Fibonacci | T(n) = T(n - 1) + T(n - 2) + 1 | Theta(1.618^n) |

### Step 2: draw the tree and sum the levels

For T(n) = 2T(n/2) + n: level 0 is one node doing n work; level 1 has two nodes of size n/2, together n; level i has 2^i nodes of size n/2^i, together n again. There are log2 n levels above the leaves, so the total is n log2 n. For T(n) = T(n - 1) + n the "tree" is a chain with work n, n - 1, ..., 1: total n(n + 1)/2. For T(n) = 2T(n - 1) + 1 level i has 2^i nodes doing 1 each, and there are n levels: 2^n - 1.

### Step 3: the master theorem, for T(n) = a T(n/b) + f(n)

Level i has a^i nodes of size n/b^i, and the tree has log_b n levels, so it has a^(log_b n) = n^(log_b a) leaves. Call c = log_b a the critical exponent and compare f(n) with n^c:

| Case | Condition | Who dominates | T(n) |
|---|---|---|---|
| 1 | f(n) = O(n^(c - e)) for some e > 0 | the leaves (level sums grow geometrically) | Theta(n^c) |
| 2 | f(n) = Theta(n^c) | nobody: every level costs about the same | Theta(n^c log n) |
| 3 | f(n) = Omega(n^(c + e)), and a f(n/b) <= k f(n) for some k < 1 | the root (level sums shrink geometrically) | Theta(f(n)) |

| Recurrence | a, b, f | c = log_b a | Case | T(n) |
|---|---|---|---|---|
| Binary search T(n/2) + 1 | 1, 2, 1 | 0 | 2 | Theta(log n) |
| Merge sort 2T(n/2) + n | 2, 2, n | 1 | 2 | Theta(n log n) |
| Tree traversal 2T(n/2) + 1 | 2, 2, 1 | 1 | 1 | Theta(n) |
| Karatsuba multiplication 3T(n/2) + n | 3, 2, n | 1.585 | 1 | Theta(n^1.585) |
| Block matrix product 8T(n/2) + n^2 | 8, 2, n^2 | 3 | 1 | Theta(n^3) |
| Strassen 7T(n/2) + n^2 | 7, 2, n^2 | 2.807 | 1 | Theta(n^2.807) |
| 2T(n/2) + n^2 | 2, 2, n^2 | 1 | 3 | Theta(n^2) |

### When the theorem does not apply

- **Subtract-and-conquer** recurrences such as T(n - 1) + n or 2T(n - 1) + 1: sum the levels directly, or guess and confirm by induction.
- **Unequal splits** such as T(n/3) + T(2n/3) + n: the tree has n work per level and between log3 n and log1.5 n levels, so Theta(n log n).
- **Gaps between the cases**: 2T(n/2) + n log n has f just above n^1 but not by a power of n. The tree gives levels n log(n/2^i), summing to Theta(n log^2 n).

## Cost

Confirm every solution numerically: compute T(n) exactly from the recurrence for growing n and divide by your answer. If the ratio settles to a constant, the answer is right. Our checks (with T(1) = 1, n a power of 2):

| Recurrence | T(n) / guess at n = 16 | n = 1,024 | n = 2^20 |
|---|---|---|---|
| 2T(n/2) + n, guess n log2 n | 1.25 | 1.10 | 1.05, tending to 1 |
| 3T(n/2) + n, guess n^1.585 | 2.61 | 2.97 | 3.00 |
| 7T(n/2) + n^2, guess n^2.807 | 2.19 | 2.33 | 2.33 |
| 2T(n/2) + n^2, guess n^2 | 1.94 | 2.00 | 2.00 |
| 2T(n/2) + n log2 n, guess n log2^2 n | 0.63 | 0.55 | 0.53, tending to 0.5 |

T(n) = T(n/3) + T(2n/3) + n divided by n log2 n gave 1.05, 1.06, 1.06 and 1.07 at n = 10^3 to 10^6, slowly approaching a constant near 1.09: Theta(n log n), as the tree argument predicted. Naive Fibonacci's call counts grow by a factor of 1.618 per step (2,692,537 calls for n = 30).

## When to use it

Write a recurrence whenever a function calls itself, before you run it on big inputs. Use the master theorem for "divide into a parts of size n/b" recurrences, a recursion tree for anything else, and induction to confirm a guess. The numerical check takes two minutes and catches most algebra slips. Recurrences tell you when a design cannot work: a recursion that calls itself twice on n - 1 is exponential no matter how cheap each call is.

## Worked trace

The recursion tree of merge sort on n = 8, level by level (T(n) = 2T(n/2) + n, T(1) = 0):

```steps
Level 0: one call on 8 items, merging costs 8
    [8]                                       level work 8
---
Level 1: two calls on 4 items, each merges 4
    [4] [4]                                   level work {{8}}
---
Level 2: four calls on 2 items
    [2] [2] [2] [2]                           level work {{8}}
---
Level 3: eight calls on 1 item: base cases, no merging
    [1] [1] [1] [1] [1] [1] [1] [1]           level work 0
---
Three levels of 8 work each: T(8) = 8 x log2 8 = 24. Every level costs n, so case 2: Theta(n log n)
    total 8 + 8 + 8 = {{24}}
---
Compare 2T(n/2) + 1 (visiting a tree): level work 1, 2, 4, then 8 leaves. Leaves dominate: Theta(n)
    level work  1   2   4   8   total 15 = 2n - 1
```

## Template

Evaluate a recurrence exactly and divide by a guess; a master-theorem helper for f(n) = n^k:

```python
import math
from functools import cache

def ratio(T, guess, sizes):
    """T(n) / guess(n) for growing n: a settling ratio confirms the guess."""
    return [(n, round(T(n) / guess(n), 3)) for n in sizes]

def master(a, b, k):
    """Theta class of T(n) = a T(n/b) + Theta(n^k), for a >= 1, b > 1, k >= 0."""
    c = math.log(a, b)
    if math.isclose(c, k):
        return f"Theta(n^{k:g} log n)"
    return f"Theta(n^{max(c, k):.3f})"

@cache
def karatsuba_cost(n):
    return 1 if n <= 1 else 3 * karatsuba_cost(n // 2) + n

print(master(2, 2, 1), master(3, 2, 1), master(2, 2, 2), master(1, 2, 0))
print(ratio(karatsuba_cost, lambda n: n ** math.log2(3), [2**4, 2**10, 2**20]))
```

It prints `Theta(n^1 log n) Theta(n^1.585) Theta(n^2.000) Theta(n^0 log n)`, where n^0 log n means Theta(log n), and the ratios `[(16, 2.605), (1024, 2.965), (1048576, 2.999)]`.

## Pitfalls

- **Missing the hidden work.** A recursion that slices (`f(a[1:])`, `f(a[:mid])`) does O(n) work per call before recursing: binary search with slicing is T(n/2) + n = Theta(n), not log n.
- **Counting depth instead of calls.** Naive Fibonacci is only n deep but makes exponentially many calls.
- **"It halves, so it is O(log n)."** Only if it makes one call. 2T(n/2) + 1 is Theta(n); 2T(n/2) + n is Theta(n log n).
- **Using the master theorem outside its form**: n - 1 recursions, unequal splits, or f(n) in a gap between cases.
- **Base cases with no progress.** In our own check, T(n) = T(n // 3) + T(n - n // 3) + n with the base case n <= 1 never ended: for n = 2, n // 3 = 0 and n - n // 3 = 2 again. Check the smallest sizes.

## Check yourself

Q: Solve T(n) = 4T(n/2) + n and T(n) = 4T(n/2) + n^2.
A: c = log2 4 = 2. For f(n) = n, f grows more slowly than n^2 by a power, so case 1: Theta(n^2). For f(n) = n^2 = n^c, case 2: Theta(n^2 log n).

Q: A recursive maximum is written `max(a[0], rec_max(a[1:]))`. Write its recurrence and solve it. What changes if it passes an index instead of slicing?
A: Each call slices off one element, copying n - 1 items: T(n) = T(n - 1) + n, so Theta(n^2) time (and Theta(n^2) memory alive at the deepest point). With an index, T(n) = T(n - 1) + 1 = Theta(n), with Theta(n) stack depth.

Q: Why can the master theorem not solve T(n) = T(n - 1) + T(n - 2) + 1, and what is the answer?
A: The subproblems shrink by subtracting, not dividing, so it is not of the form a T(n/b) + f(n). The call counts satisfy the Fibonacci recurrence, so T(n) = 2F(n + 1) - 1 = Theta(phi^n) with phi = 1.618..., which you can prove by induction.

## Lab

- **509** Fibonacci Number: write the recurrence for the number of calls of the naive version and check it against a counter. Expected: calls(n) = calls(n - 1) + calls(n - 2) + 1, giving 177 calls for n = 10 and 2,692,537 for n = 30 (a ratio near 1.618 per step); with memoisation T(n) = T(n - 1) + O(1), so O(n).
- **779** K-th Symbol in Grammar: write the recurrence for your solution and for building the rows. Expected: one call on n - 1 with O(1) work, T(n) = T(n - 1) + 1, so O(n); building every row costs 1 + 2 + 4 + ... + 2^(n-1), Theta(2^n), which is impossible for n = 30.

> [!know]
> You now know how to turn recursive code into a recurrence, solve it with a recursion tree or the master theorem, and confirm the answer with numbers.

=== primer | How does divide and conquer sort a list and count its inversions in O(n log n)? | 16 min
goal: Implement merge sort and inversion counting as split, recurse, combine; prove them correct by induction and derive their cost
tag: recur-dc | Divide and conquer
link: Sedgewick and Wayne: 2.2 Mergesort | https://algs4.cs.princeton.edu/22mergesort/ | 15 min: 'Abstract in-place merge' and 'Top-down mergesort' with their trace figures, then the proposition that it uses between 1/2 N lg N and N lg N compares
link: Jeff Erickson: Algorithms, chapter 1 Recursion (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/01-recursion.pdf | 15 min: 'Mergesort' on PDF pages 6-9, including its correctness proof by induction
practice: 241, 395

> [!key]
> **Divide and conquer** splits the input into parts, solves each part recursively, and **combines** the answers. It pays off when the combine step can account for everything that crosses the split cheaply. Merge sort splits in half, sorts each half, and merges two sorted lists in linear time: T(n) = 2T(n/2) + n = Theta(n log n). Counting inversions (pairs i < j with a[i] > a[j]) rides on the same merge: when an element of the right half is placed before the remaining left elements, it forms an inversion with every one of them.

## Intuition

Sorting a pile of 200 exam scripts by mark with a friend: split the pile, each of you sorts half, then you merge by repeatedly taking whichever of the two top scripts has the lower mark. Merging needs only a glance at two scripts per step, because each half is already sorted. The hard work happens in the halves, and the halves are the same problem, smaller.

## How it works

### The pattern

1. **Divide**: split the input into smaller instances (often two halves).
2. **Conquer**: solve each instance recursively; tiny instances are base cases.
3. **Combine**: build the answer for the whole from the answers for the parts, plus whatever crosses the boundary between them.

The design question is always the combine step: what information about each part makes the cross-boundary work cheap? For sorting, "each half is sorted" makes merging linear.

### Merging

Keep an index i into the sorted left half and j into the sorted right half. Repeatedly append the smaller of `left[i]` and `right[j]` and advance that index; when one side runs out, append the rest of the other. **Invariant**: the output holds the smallest i + j elements of both halves, in order. Taking from the left on ties (`<=`) keeps equal elements in their original order, so merge sort is **stable**.

### Counting inversions on the way

An inversion is a pair of positions i < j with a[i] > a[j]; it measures how far a list is from sorted (0 when sorted, n(n - 1)/2 when reversed). Every inversion lies entirely in the left half, entirely in the right half, or **across** the halves. The recursive calls count the first two kinds. The cross ones are counted during the merge: when `right[j]` is taken while left elements `left[i:]` remain, each of those remaining elements is larger than `right[j]` and sits before it in the original list, so add `len(left) - i`. Taking left on ties ensures equal elements never count.

### Why it is correct

By strong induction on n. Base: a list of 0 or 1 elements is sorted and has no inversions. Step: by the hypothesis the recursive calls return the two halves sorted, with their internal inversion counts. The merge invariant gives a sorted output, and each cross pair (x in left, y in right, x > y) is counted exactly once, at the moment y is taken, since x is still waiting in the left half then. Adding the three counts gives every inversion once.

### Other combine steps

The same shape solves problems far from sorting. "All values of an expression under every bracketing" splits at each operator, solves both sides, and combines every pair of results. "Longest substring in which every character appears at least k times" splits at any character that appears fewer than k times in the whole string, because no valid substring can contain it.

## Cost

The merge does O(n) work, and there are two calls on halves: T(n) = 2T(n/2) + n, which the recursion-tree card solved as Theta(n log n) (exactly n log2 n = 24 element moves for n = 8 under T(1) = 0). Inversion counting adds O(1) per element taken, so it stays Theta(n log n), against Theta(n^2) for checking every pair. Space: an O(n) buffer for merging plus O(log n) stack depth; slicing the halves, as in the template, also costs O(n log n) extra copying in total but no worse asymptotically. In practice Python's built-in `sorted` (Timsort, in C) is tens of times faster than a pure-Python merge sort, so write your own only when the merge does extra work, like counting.

## When to use it

Use divide and conquer when the answer for the whole can be built from answers for parts plus a cheap account of the boundary: sorting, counting pairs with an order condition, closest pairs, and splitting at a separator. Do not use it when the parts overlap heavily (the same subproblem appears many times: memoise, which is dynamic programming) or when the combine step needs to look at all pairs across the boundary anyway, which gives T(n) = 2T(n/2) + n^2 = Theta(n^2) and no gain over brute force.

## Worked trace

The final merge of [2, 5, 8] and [1, 3, 9], counting cross inversions:

```steps
i = 0, j = 0: compare 2 and 1. 1 is smaller, take it from the right: 2, 5 and 8 all come before it and are larger, so add 3
    left  [{{2}} 5 8]   right [{{1}} 3 9]
    out   [1]          inversions 3
---
i = 0, j = 1: compare 2 and 3. Take 2 from the left (no inversions added)
    left  [{{2}} 5 8]   right [1 {{3}} 9]
    out   [1 2]        inversions 3
---
i = 1, j = 1: compare 5 and 3. Take 3 from the right: 5 and 8 remain on the left, so add 2
    left  [2 {{5}} 8]   right [1 {{3}} 9]
    out   [1 2 3]      inversions 5
---
i = 1, j = 2: compare 5 and 9. Take 5
    left  [2 {{5}} 8]   right [1 3 {{9}}]
    out   [1 2 3 5]    inversions 5
---
i = 2, j = 2: compare 8 and 9. Take 8; the left half is now empty
    left  [2 5 {{8}}]   right [1 3 {{9}}]
    out   [1 2 3 5 8]  inversions 5
---
Append what is left of the right half. Cross inversions: (2,1) (5,1) (8,1) (5,3) (8,3), five in all
    out   [1 2 3 5 8 {{9}}]   inversions 5
```

## Template

```python
def sort_count(a):
    """Return (sorted copy of a, number of pairs i < j with a[i] > a[j])."""
    if len(a) <= 1:
        return list(a), 0
    mid = len(a) // 2
    left, inv_left = sort_count(a[:mid])
    right, inv_right = sort_count(a[mid:])
    out, i, j, cross = [], 0, 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:              # ties go left: stable, and not an inversion
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
            cross += len(left) - i           # right[j] jumps over everything left in left
    out += left[i:]
    out += right[j:]
    return out, inv_left + inv_right + cross

print(sort_count([2, 5, 8, 1, 3, 9]))        # ([1, 2, 3, 5, 8, 9], 5)
print(sort_count([3, 1, 2]))                 # ([1, 2, 3], 2)
```

## Pitfalls

- **Using `<` instead of `<=` in the merge.** Equal elements then come from the right first: the sort is no longer stable, and equal pairs are counted as inversions.
- **Forgetting the leftovers.** After the loop one side still has elements; append both tails.
- **Recursing on a split that does not shrink.** With `mid = len(a) // 2`, a one-element list must be a base case, or the call on `a[mid:]` repeats forever.
- **Overflow in other languages.** Inversions reach n(n - 1)/2, about 5 x 10^9 for n = 10^5, beyond a 32-bit int; use 64-bit counters in C++ or Java.
- **Rewriting what the library does.** For plain sorting call `sorted`; write merge sort when the merge must do extra work.

## Check yourself

Q: How many inversions does [4, 3, 2, 1] have, and how does `sort_count` split that number between the halves and the merge?
A: 6, the maximum n(n - 1)/2 for n = 4. The left half [4, 3] has 1, the right half [2, 1] has 1, and the merge of [3, 4] with [1, 2] adds 2 when 1 is taken and 2 when 2 is taken: 1 + 1 + 4 = 6.

Q: Why is it correct to add `len(left) - i` when `right[j]` is taken, rather than 1?
A: The left half is sorted, so if `left[i] > right[j]` then every element of `left[i:]` is also greater than `right[j]`, and all of them came before it in the original list. Each forms one cross inversion with `right[j]`, and none will be counted again, because `right[j]` leaves the merge now.

Q: A colleague's divide and conquer for "count pairs i < j with a[i] > 2 * a[j]" loops over every left element and every right element in the combine step. What is its cost, and how could the sorted halves help?
A: The combine step is O(n^2) per call, so T(n) = 2T(n/2) + n^2 = Theta(n^2): no better than brute force. Because both halves come back sorted, one pointer can sweep the right half while another sweeps the left, counting cross pairs in O(n) before the ordinary merge, which restores T(n) = 2T(n/2) + n = Theta(n log n).

## Lab

- **241** Different Ways to Add Parentheses (stretch): split at every operator, solve both sides recursively, and combine every pair of results. Expected: "1+2*3" gives [9, 7] in some order; the number of results grows like the Catalan numbers, so memoising on the substring helps when the same sub-expression recurs.
- **395** Longest Substring with At Least K Repeating Characters (stretch): any character that occurs fewer than k times in the current string cannot be in an answer, so split around it and recurse on the pieces. Expected: at most 26 levels of splitting, so O(26 n) time; for "ababbcdc" with k = 2 the answer is 5 ("ababb").

> [!know]
> You now know how to design divide and conquer around a cheap combine step, and how merge sort counts inversions in O(n log n).

=== primer | How do you compute x^n with only O(log n) multiplications? | 13 min
goal: Implement fast exponentiation recursively and iteratively, with and without a modulus, and use it to count with huge exponents
tag: recur-fastpow | Fast exponentiation
link: cp-algorithms: Binary Exponentiation | https://cp-algorithms.com/algebra/binary-exp.html#algorithm | 15 min: 'Algorithm' and 'Implementation' (recursive and iterative versions), then skim 'Applications' for matrix powers and modular powers
link: Python docs: built-in pow | https://docs.python.org/3/library/functions.html#pow | 3 min: pow(base, exp, mod), and pow(x, -1, m) for modular inverses
practice: 1922

> [!key]
> x^n = (x^(n // 2))^2 when n is even, and x times that when n is odd. Computing x^(n // 2) **once** and squaring it halves the exponent at every step, so x^n takes about 2 log2 n multiplications instead of n - 1: T(n) = T(n/2) + O(1) = O(log n). With a modulus, reduce after every multiplication so the numbers never grow. Python's `pow(x, n, m)` does exactly this in C.

## Intuition

To compute 3^16 you do not need 15 multiplications: square 3 to get 3^2, square that to get 3^4, then 3^8, then 3^16. Four squarings. Exponents that are not powers of two are sums of powers of two (13 = 8 + 4 + 1), so 3^13 = 3^8 x 3^4 x 3^1: square repeatedly and multiply in the pieces that appear in the binary form of the exponent.

## How it works

### Recursive form

- Base case: x^0 = 1.
- Delegate: compute h = x^(n // 2) once (trust it).
- Combine: return h x h if n is even, h x h x x if n is odd.

Correct by strong induction: if h = x^(n // 2), then h^2 = x^(2(n // 2)), which is x^n for even n and x^(n - 1) for odd n, fixed by one more factor of x.

### Iterative form: read the bits

Walk through the bits of n from the lowest. Keep `base` equal to x^(2^i) for the current bit i by squaring it each step, and multiply it into `result` whenever bit i is 1. **Invariant**: result x base^e equals x^n_original at every step, where e is what remains of the exponent; when e reaches 0, result is the answer.

### With a modulus

(a x b) mod m = ((a mod m) x (b mod m)) mod m, so reduce after every multiplication and all intermediate values stay below m^2. Without the modulus the numbers themselves grow: x^n has about n log2 x bits, so with big integers the multiplications get slower even though there are only O(log n) of them.

### Beyond numbers

The same squaring works for anything with an associative multiplication: matrices (the n-th Fibonacci number from a 2 x 2 matrix power in O(log n) multiplications), permutations applied k times, and polynomial or string transformations. Associativity is what lets you regroup x x x x ... x as (x x x)(x x x)...

## Cost

Recursion depth and the number of squarings are both floor(log2 n) + 1, and there is at most one extra multiplication per bit set in n: at most about 2 log2 n multiplications. For n = 10^18 that is about 120 multiplications instead of 10^18. With a modulus below about 3 x 10^9, every product of two reduced values fits in 64 bits, so each multiplication is O(1) in C++ or Java as well. Python's `pow(3, 10**18, 10**9 + 7)` returns instantly.

## When to use it

Use it whenever an exponent or a repetition count is huge: modular counting ("how many strings of length 10^15 ..."), modular inverses by Fermat's little theorem (x^(m - 2) mod m for prime m), matrix powers for linear recurrences, and cryptography (RSA and Diffie-Hellman are built on modular exponentiation). In Python production code call `pow(x, n, m)`; write the loop yourself when the "multiplication" is your own operation (matrices, permutations). For small exponents, or floats, plain `x ** n` is fine.

## Worked trace

Iterative 3^13 mod 1000. 13 is 1101 in binary; the answer is 1,594,323 mod 1000 = 323.

```steps
Start: result = 1, base = 3, e = 13 (binary 1101)
    result 1     base 3      e 1101
---
Lowest bit of e is 1: result = 1 x 3 = 3. Then square base to 9 and shift e
    result {{3}}     base 9      e 110
---
Lowest bit is 0: result unchanged. Square base: 81
    result 3     base {{81}}     e 11
---
Lowest bit is 1: result = 3 x 81 = 243. Square base: 81^2 = 6561, mod 1000 = 561
    result {{243}}   base 561    e 1
---
Lowest bit is 1: result = 243 x 561 = 136,323, mod 1000 = 323. e becomes 0, so stop
    result {{323}}   base 721    e 0
---
Four squarings and three multiplications instead of twelve multiplications; matches pow(3, 13, 1000)
    3^13 = 3^8 x 3^4 x 3^1 = 6561 x 81 x 3 = 1,594,323
```

## Template

```python
def power_mod(x, n, m):
    """x^n mod m for n >= 0, recursively: O(log n) multiplications."""
    if n == 0:
        return 1 % m
    half = power_mod(x, n // 2, m)          # computed once, then squared
    result = half * half % m
    return result * x % m if n % 2 else result

def power_mod_iter(x, n, m):
    """x^n mod m for n >= 0, reading the bits of n from the lowest."""
    result, base = 1 % m, x % m
    while n > 0:
        if n & 1:                           # this bit contributes base = x^(2^i)
            result = result * base % m
        base = base * base % m
        n >>= 1
    return result

print(power_mod(3, 13, 1000), power_mod_iter(3, 13, 1000), pow(3, 13, 1000))   # 323 323 323
```

## Pitfalls

- **Two recursive calls.** `power(x, n // 2) * power(x, n // 2)` computes the half twice: T(n) = 2T(n/2) + 1 = Theta(n) multiplications, all the speed lost. Store the half in a variable.
- **Forgetting to reduce.** Without `% m` after each multiplication, Python's numbers grow to millions of digits and each multiplication slows down; in C++ or Java they overflow silently.
- **The modulus 1.** x^0 mod 1 must be 0, not 1; `1 % m` handles it.
- **Negative exponents.** The recursion never reaches 0; handle them separately (1 / x^-n for floats, or a modular inverse).
- **Floats for exact answers.** `math.pow` and `**` on floats lose precision beyond about 2^53; use integers with `pow(x, n, m)`.

## Check yourself

Q: How many multiplications does `power_mod_iter` perform for n = 13, and for n = 2^20?
A: For 13 (binary 1101): 4 squarings of base and 3 multiplications into result, 7 in total (the last squaring is wasted but harmless). For 2^20 (a 1 followed by 20 zeros): 21 squarings and 1 multiplication into result.

Q: A colleague writes `def p(x, n): return 1 if n == 0 else p(x, n // 2) * p(x, n // 2) * (x if n % 2 else 1)`. It gives correct answers. What is its cost, and why?
A: Theta(n) multiplications. It makes two calls on n // 2, so T(n) = 2T(n/2) + 1, whose recursion tree has about n leaves (case 1 of the master theorem). Computing the half once gives T(n) = T(n/2) + 1 = Theta(log n).

Q: There are 5 choices for each even position and 4 for each odd position of a string of length n = 10^15 (positions 0 to n - 1). How do you count the strings modulo 10^9 + 7?
A: Positions 0, 2, 4, ... number (n + 1) // 2 and odd positions n // 2, so the count is 5^((n + 1) // 2) x 4^(n // 2). Compute each power with `pow(base, e, 10**9 + 7)` and multiply modulo the same number: each exponent has about 49 bits, so at most a couple of hundred multiplications in all.

## Lab

- **1922** Count Good Numbers: count the choices per position, then raise to huge powers. Expected: O(log n) time; n = 1 gives 5, n = 3 gives 100, n = 4 gives 400 and n = 10 gives 3,200,000; it must handle n up to 10^15 instantly, so a loop over n is impossible.
- Exercise: time `power_mod_iter(3, 10**18, 10**9 + 7)` against `pow(3, 10**18, 10**9 + 7)`. Expected: both return the same value in tens of microseconds; the built-in is roughly twice as fast because its loop runs in C.

> [!know]
> You now know how to raise numbers, or anything with an associative multiplication, to huge powers in O(log n) steps.

=== primer | How do you run deep recursion safely in Python, or turn it into a loop? | 15 min
goal: Predict when Python recursion fails, choose between raising the limit, memoising and an explicit stack, and convert a recursive function into a loop with identical output
tag: recur-explicit-stack | Recursion to an explicit stack
link: Python docs: sys.setrecursionlimit | https://docs.python.org/3/library/sys.html#sys.setrecursionlimit | 3 min: what the limit protects against and why a too-high limit can crash the interpreter
link: Python docs: functools.cache | https://docs.python.org/3/library/functools.html#functools.cache | 5 min: cache and lru_cache, the factorial example, and cache_info() for counting hits and misses
practice: 509, 344

> [!key]
> CPython stops recursion at about 1,000 nested calls with `RecursionError`, and never eliminates tail calls. For recursion whose depth grows with the input, you have three tools: raise the limit with `sys.setrecursionlimit` (fine for plain Python recursion in 3.12, but not through C code such as a `functools.cache` wrapper), **memoise** with `functools.cache` when the problem is repeated subproblems rather than depth, or **convert to an explicit stack**: keep the pending work in your own list and loop until it is empty. The explicit stack is the production answer: no depth limit, and often faster.

## Intuition

Recursion lets the interpreter keep your to-do pile for you, on a shelf with room for about a thousand notes. When the job might need a million notes, keep the pile yourself on the floor: a Python list can hold millions of small tasks. Each loop iteration takes the top task, does it, and puts any follow-up tasks back on the pile in the order you want them done.

## How it works

### What the limit protects

Every Python call needs a frame, and calls that pass through C code (built-ins, decorators written in C, `__repr__` of nested containers) also use the C stack, which is small and fixed; overflowing it crashes the process instead of raising an exception. Hence the limit. In our tests on CPython 3.12:

- A plain recursive function managed 999 nested calls under the default limit of 1,000.
- With `sys.setrecursionlimit(10**6)`, the same function recursed 500,000 deep in 0.4 s. Since 3.11, calls from Python to Python functions do not consume the C stack, and since 3.12 the limit applies only to Python code.
- The same function decorated with `functools.cache` stopped at about 3,300 levels even with the limit at 10^6, because each call passes through the C-implemented cache wrapper, which 3.12 protects with a separate C-level limit.
- `json.dumps`, `copy.deepcopy` and `repr` all raised `RecursionError` on a list nested 100,000 deep.

Exact figures differ between versions, which is itself the lesson: deep recursion in Python is fragile. Some code also runs the recursion in a `threading.Thread` after raising `threading.stack_size()`; treat that as a last resort for code you cannot rewrite.

### Tail recursion becomes a while loop

When the recursive call is the last thing a function does, the frame has nothing left to do afterwards, so the recursion is a loop in disguise: replace the call by updating the parameters and jumping back to the top. `gcd(a, b) = gcd(b, a % b)` becomes `while b: a, b = b, a % b`.

### Everything else becomes an explicit stack

1. Put the initial task on a list `stack`.
2. Loop while the stack is not empty: pop a task and do its work.
3. Where the recursive version would call itself, push a task instead. Because a stack pops the last item first, push follow-ups in **reverse** order of when they should run.
4. If the recursive version does work **after** a call returns (post-order work, or combining results), push a marker task for that work before pushing the call, so it pops after the call's own tasks are finished.

### Memoisation, briefly

When a recursion is slow because it solves the same subproblem many times (naive Fibonacci), depth is not the problem: decorate it with `@functools.cache`, which stores each result by its arguments. The arguments must be hashable (tuples, not lists), and `cache_info()` reports hits and misses. The dynamic programming module builds on this.

## Cost

An explicit stack does the same work as the recursion: the same number of tasks, each O(1) to push and pop, plus O(maximum pending tasks) memory, which is about the depth times the branching. A Python list entry is an 8-byte reference to a small tuple, against a full frame per call, so iterative versions are usually somewhat faster as well as limit-free. Memoising turns naive Fibonacci from about 1.618^n calls into n + 1 distinct computations: fib(30) drops from 2,692,537 calls to 31.

## When to use it

Keep recursion when the depth is logarithmic (balanced trees, divide and conquer, fast power) or bounded by a small constant: it is clearer and safe. Convert to a loop or an explicit stack when the depth can grow with the input: linked lists, degenerate trees, depth-first search on graphs with 10^5 nodes, one call per character of a string. Raise the limit only for plain Python recursion in scripts and contest code, and never as a fix for infinite recursion. Memoise when the same arguments recur; convert when the depth is the problem; both when both are.

## Worked trace

Tower of Hanoi with 2 discs through an explicit stack (top of the stack on the right). "solve k X->Y" means move k discs from X to Y.

```steps
Start with the whole job as one task
    stack [ {{solve 2 A->C}} ]
    moves []
---
Pop solve 2 A->C. Push its three parts in reverse order, so the first part ends on top
    stack [ solve 1 B->C, move A->C, {{solve 1 A->B}} ]
    moves []
---
Pop solve 1 A->B: push solve 0 C->B, move A->B, solve 0 A->C
    stack [ solve 1 B->C, move A->C,
            solve 0 C->B, move A->B, {{solve 0 A->C}} ]
    moves []
---
Pop solve 0 (nothing to do), pop move A->B (record it), pop solve 0
    stack [ solve 1 B->C, {{move A->C}} ]
    moves [ {{A->B}} ]
---
Pop move A->C: record it
    stack [ {{solve 1 B->C}} ]
    moves [ A->B, {{A->C}} ]
---
Pop solve 1 B->C: its parts pop in turn, recording B->C. The stack is empty
    stack [ ]
    moves [ A->B, A->C, {{B->C}} ]   identical to the recursive version
```

## Template

```python
from functools import cache

def hanoi_iterative(n, src="A", dst="C", via="B"):
    """Same moves, in the same order, as the recursive hanoi, with no recursion."""
    moves, stack = [], [("solve", n, src, dst, via)]
    while stack:
        task = stack.pop()
        if task[0] == "move":
            moves.append(task[1:])
            continue
        _, k, s, d, v = task
        if k == 0:
            continue
        stack.append(("solve", k - 1, v, d, s))    # runs last
        stack.append(("move", s, d))
        stack.append(("solve", k - 1, s, v, d))    # runs first: pushed last
    return moves

def flatten_iterative(x):
    """Non-list items inside a nested list, left to right, with any nesting depth."""
    out, stack = [], [x]
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(reversed(item))           # reversed, so item[0] pops first
        else:
            out.append(item)
    return out

@cache
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

deep = [1, [2, 3]]
for _ in range(100_000):                           # nest it 100,000 levels deep
    deep = [deep]
print(hanoi_iterative(2))                          # [('A', 'B'), ('A', 'C'), ('B', 'C')]
print(flatten_iterative([1, [2, [3, []], 4]]), flatten_iterative(deep)[:3])   # [1, 2, 3, 4] [1, 2, 3]
print(fib(30), fib.cache_info().misses)            # 832040 31
```

## Pitfalls

- **Raising the limit to hide a bug.** If the recursion is infinite (a missing or unreachable base case), a higher limit only delays the error, or crashes the process.
- **Very high limits with C code in the loop.** Recursion through C (cached functions, `repr`, `deepcopy`, some callbacks) can still hit a C-level limit or overflow the C stack.
- **Pushing children in the wrong order.** A stack reverses order; push the last child first if you need left-to-right output.
- **Losing post-order work.** If the recursive version combines results after its calls return, the loop needs a marker task or a second phase; popping a node and processing it immediately gives pre-order.
- **Caching with unhashable or mutable arguments.** `@cache` raises `TypeError` for list arguments, and a cache kept across test cases can return stale answers; call `cache_clear()` between runs.

## Check yourself

Q: A recursive depth-first search on a linked chain of 50,000 nodes raises RecursionError. List three fixes and say which you would ship.
A: Raise the limit with `sys.setrecursionlimit` (works for plain Python recursion in recent versions, fragile across versions and with C code in the call chain); run it in a thread with a larger `threading.stack_size` (a workaround); or rewrite it with an explicit stack (no limit). Ship the explicit stack.

Q: In `flatten_iterative`, what goes wrong if you write `stack.extend(item)` instead of `stack.extend(reversed(item))`?
A: The last element of each list would be popped first, so the items come out right to left at every level: [1, [2, 3]] would flatten to [3, 2, 1]. All items are still visited exactly once; only the order is wrong.

Q: Naive `fib(35)` is slow but only 35 deep. Which tool fixes it, and what does `fib.cache_info().misses` report after `fib(35)` with that fix?
A: Memoisation with `@functools.cache`, because the problem is repeated subproblems, not depth. Each of fib(0) to fib(35) is computed once, so there are 36 misses; every other lookup is a hit.

## Lab

- **509** Fibonacci Number: write three versions: naive recursion, `@cache`, and a loop keeping only the last two values. Expected: all agree for n = 0 to 30; the cached version computes n + 1 values, and the loop needs O(1) space and no recursion at all.
- **344** Reverse String: compare your recursive two-index version with a `while` loop on the same indices. Expected: identical results; the recursion fails with RecursionError for a list of about 2,000 or more characters under the default limit (it is about n/2 deep), while the loop handles 10^5 characters in O(1) extra space.

> [!know]
> You now know when Python recursion breaks, and how to fix depth with an explicit stack and repeated work with memoisation.

=== lab | See the recursion tree: count calls, memoise, then remove the recursion | 45 min
goal: Instrument naive Fibonacci, merge sort and the Tower of Hanoi to count calls and depth, check the counts against their recurrences, memoise Fibonacci, and convert Hanoi to an explicit stack with identical output
link: Composing Programs 1.7: Recursive Functions | https://composingprograms.com/pages/17-recursive-functions.html#tree-recursion | 10 min: '1.7.4 Tree Recursion', the picture of fib's call tree that this lab measures

You will make three recursive functions report on themselves: how many calls they make, how deep they go, and how that compares with the recurrence you would write down. Then you will fix one with memoisation and rewrite another without recursion, proving the rewrite correct by comparing outputs.

## Setup

Python 3.10 or later; nothing to install. Put everything in one file, `recursion_lab.py`.

## Steps

1. Start with a small instrument: a counter for calls and the deepest level reached.

```python
import sys
from functools import cache

class Probe:
    """Counts calls and the maximum depth of a recursive function."""

    def __init__(self):
        self.calls = self.depth = self.max_depth = 0

    def enter(self):
        self.calls += 1
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)

    def leave(self):
        self.depth -= 1


def fib(n, p):
    p.enter()
    result = n if n < 2 else fib(n - 1, p) + fib(n - 2, p)
    p.leave()
    return result


def merge_sort(a, p):
    p.enter()
    if len(a) <= 1:
        p.leave()
        return list(a)
    mid = len(a) // 2
    left, right = merge_sort(a[:mid], p), merge_sort(a[mid:], p)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    p.leave()
    return out + left[i:] + right[j:]


def hanoi(n, src, dst, via, moves, p):
    p.enter()
    if n > 0:
        hanoi(n - 1, src, via, dst, moves, p)
        moves.append((src, dst))
        hanoi(n - 1, via, dst, src, moves, p)
    p.leave()


for n in (10, 15, 20, 25):
    p = Probe()
    value = fib(n, p)
    print(f"fib({n}) = {value}: {p.calls} calls, depth {p.max_depth}")
for n in (8, 1000, 1024):
    p = Probe()
    assert merge_sort(list(range(n, 0, -1)), p) == list(range(1, n + 1))
    print(f"merge_sort n={n}: {p.calls} calls, depth {p.max_depth}")
for n in (3, 10, 16):
    p, moves = Probe(), []
    hanoi(n, "A", "C", "B", moves, p)
    print(f"hanoi({n}): {len(moves)} moves, {p.calls} calls, depth {p.max_depth}")
```

2. Before running it, write down your predictions from the recurrences: calls(n) = calls(n - 1) + calls(n - 2) + 1 for fib, 2n - 1 calls and about log2 n + 1 depth for merge sort, 2^n - 1 moves for Hanoi. Then run the file and compare.
3. Memoise: add `@cache` to a copy of fib without the probe (`def fib_memo(n): return n if n < 2 else fib_memo(n - 1) + fib_memo(n - 2)`), compute `fib_memo(25)` and print `fib_memo.cache_info()`. Then try `fib_memo(5000)` on a fresh cache and read the error.
4. Remove the recursion from Hanoi: write `hanoi_iterative(n)` with an explicit stack of tasks (the template from the card "How do you run deep recursion safely in Python, or turn it into a loop?"). Assert that its move list equals the recursive one for every n from 0 to 16.
5. Draw (on paper or in a text file) the call tree of fib(5) and of merge sort on 8 items, and mark the maximum depth on each. Which tree is lopsided, and why does that not change the depth by much?
6. Journal three lines: the biggest gap between calls and depth you saw, the recurrence that predicted it, and the fix you would use in production for each function.

## What you should see

- **Fibonacci**: fib(10) = 55 with 177 calls, fib(15) = 610 with 1,973 calls, fib(20) = 6,765 with 21,891 calls and fib(25) = 75,025 with 242,785 calls, each about 1.618^5 = 11 times the previous: exponential growth. The depth is only n: 10, 15, 20, 25.
- **Memoised Fibonacci**: `cache_info()` after fib_memo(25) shows 26 misses (one per value from 0 to 25) and 23 hits. On CPython 3.12 a fresh fib_memo(5000) raises RecursionError even if you raise the limit, because each cached call passes through C code; computing fib_memo for 0, 500, 1000, ... in order first, or a loop, avoids it.
- **Merge sort**: exactly 2n - 1 calls (15 for n = 8, 1,999 for n = 1,000, 2,047 for n = 1,024) and depth 4, 11 and 11: about log2 n + 1. Linear calls, logarithmic depth, n log n total work.
- **Hanoi**: 7, 1,023 and 65,535 moves, which is 2^n - 1; the number of calls is 2^(n+1) - 1 (counting the empty n = 0 calls) and the depth only n + 1.
- **The explicit-stack Hanoi** produces exactly the same move list for every n you test, with no recursion at all.

=== practice
- 509 core
  cue: Each value is defined by the two values before it, with two given starting values.
  hint: Write the definition directly as a recursive function first. How many calls does it make for n = 30? Which calls repeat, and what could remember them?
  insight: The naive recursion is correct but makes 2F(n + 1) - 1 calls because the same fib(k) is recomputed in many subtrees. Remembering each result (`functools.cache`) or looping forward while keeping only the last two values computes each fib(k) once: n steps.
  cost: O(n) time; O(1) space with the loop, O(n) with memoisation
  pattern: recur-tree
- 344 core
  cue: An in-place change that pairs the first position with the last, the second with the second to last, and so on.
  hint: State the contract for a function on the range from i to j. What is the smallest range that needs no work, and what single action turns the problem into the same problem on a smaller range?
  insight: reverse(i, j): if i >= j there is nothing to do; otherwise swap s[i] and s[j] and trust reverse(i + 1, j - 1). The range shrinks by 2 each call, so it ends after about n/2 calls. The recursion uses O(n) stack; the same idea as a while loop uses O(1).
  cost: O(n) time; O(n) stack recursively, O(1) iteratively
  pattern: recur-delegate
- 231 core
  cue: A yes/no question about whether a number is built by repeatedly multiplying by the same base.
  hint: If n is a power of two and bigger than 1, what must be true of n % 2, and what is n // 2? What are the answers for n = 1 and for n <= 0?
  insight: n is a power of two exactly when n == 1, or n is even and n // 2 is a power of two; anything below 1 is not. Strong induction proves it, and the recursion makes about log2 n calls. The bit test `n > 0 and n & (n - 1) == 0` works because a power of two has exactly one 1 bit, which subtracting 1 clears.
  cost: O(log n) time recursively, O(1) with the bit test
  pattern: recur-induction
- 326 core
  cue: The same yes/no question as for powers of two, but with base 3, where no single-bit trick applies.
  hint: Peel off one factor of 3 at a time. What must hold before you may divide, and which inputs are base cases?
  insight: n is a power of three exactly when n == 1, or n is divisible by 3 and n // 3 is a power of three; n < 1 never is. Each call divides by 3, so there are about log3 n calls. (Without recursion: 3^19 = 1162261467 is the largest power of 3 below 2^31, and a positive n is a power of 3 within that range exactly when it divides 3^19.)
  cost: O(log n) time, O(log n) stack recursively or O(1) with a loop
  pattern: recur-induction
- 779 derive
  cue: Each row is built from the previous row by a fixed rule, rows double in length, and only one position of a deep row is asked for.
  hint: Row n has 2^(n-1) symbols, so building it is hopeless for n = 30. Which position of row n - 1 produced position k of row n, and how does the symbol change depending on whether k is odd or even?
  insight: Every symbol of row n - 1 expands into two symbols of row n, so position k comes from position (k + 1) // 2 of row n - 1. The first child (odd k) copies its parent and the second child (even k) flips it: kth(n, k) = kth(n - 1, (k + 1) // 2), flipped when k is even, with kth(1, 1) = 0. One call per row: O(n).
  cost: O(n) time, O(n) stack (or O(1) with a loop)
  pattern: recur-delegate
- 1922 core
  cue: A count of digit strings of a given length with separate rules for even and odd positions, the length is enormous, and the answer is taken modulo 10^9 + 7.
  hint: The positions are independent, so the count is a product of per-position choices. How many choices does an even position have, how many an odd one, and how do you raise numbers to a power around 10^15 quickly?
  insight: Even positions take one of 5 even digits and odd positions one of 4 prime digits, so the answer is 5^((n + 1) // 2) x 4^(n // 2) mod 10^9 + 7. Fast exponentiation (`pow(base, e, mod)`) computes each power with about 2 log2 n modular multiplications.
  cost: O(log n) time, O(1) space (O(log n) stack with a recursive power)
  pattern: recur-fastpow
- 241 stretch
  cue: Return every value an expression can take under all possible bracketings.
  hint: Every bracketing has a last operation applied. If you choose which operator is applied last, what are the two subproblems, and how do their answer lists combine?
  insight: For each operator position, recursively compute all values of the left part and of the right part, then apply the operator to every pair; a lone number is the base case. Memoising on the substring avoids recomputing shared sub-expressions. The number of results grows like the Catalan numbers, so the output size, not the recursion, dominates the cost.
  cost: Exponential in the number of operators (Catalan-sized output); fine for the small inputs given
  pattern: recur-dc
