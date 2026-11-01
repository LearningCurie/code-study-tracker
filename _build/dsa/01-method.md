---
key: method
name: Solving problems you have not seen
stage: found
summary: One named loop (Restate, Examples, Brute force, Optimise, Prove, Code, Test, Look back) that turns "I have no idea" into a tested solution, plus the habits that make practice stick.
why: Most failures on unfamiliar problems are not missing knowledge but a missing process: coding before the question is pinned down, skipping the brute force, guessing at the target complexity and testing only the sample cases. The solving loop fixes the order of work so that every step produces what the next one needs, and the brute force written early becomes the test oracle later. Engineers use the same loop on production problems: write the contract, build the simple correct version, read the limits, remove the bottleneck the numbers point at, and keep the simple version to check the fast one. A database planner choosing between a nested loop, a sort-merge and a hash join is this module's optimisation menu, applied by a machine.
outcomes:
- Run the eight-step solving loop on any new problem and say what "solved" means for it
- Turn a vague statement into a written contract with edge rules and hand-worked examples, including one built to break a naive idea
- Write a brute force in minutes by naming its search space (pairs, subarrays, subsets, orders), state its cost and keep it as an oracle
- Read the constraints to set a target complexity before designing, using a CPython budget of about 10^7 simple steps per second
- Name the question a brute force's inner loop keeps asking and remove it with the matching fix from the optimisation menu
- Get unstuck with a short list of Pólya's heuristics and reductions, and practise with timeboxes, staged hints, honest statuses and a four-line journal
cues:
- You have read the problem twice and still cannot name a technique
- The statement is long or story-shaped, or silent about empty input, duplicates, ties or output order
- You have an idea but cannot say what it costs or why it is right
- Your code passes the examples and you are about to submit without any other test
traps:
- Coding before restating the problem and solving one example by hand
- Skipping the brute force as "too slow", then having nothing to test the fast version against
- Designing before reading the constraints, so you either over-engineer or hit the time limit
- Reading a full solution after five minutes, nodding along, and never re-implementing it from a blank file
- Counting a problem as learnt because the judge accepted it once
systems:
- PostgreSQL's planner chooses between nested loop, merge and hash joins: the brute force, sort-then-scan and hash lookup moves of the optimisation menu, picked by estimated cost
- CPython's PEP 399 requires a C accelerator module to pass the same test suite as its pure Python version, so the simple implementation is the oracle for the fast one
further:
- Article · 10 min | Wikipedia: How to Solve It, the four phases and the heuristics dictionary | https://en.wikipedia.org/wiki/How_to_Solve_It#Four_phases
- Article · 10 min | CodePath: the UMPIRE interview strategy, Understand to Evaluate | https://guides.codepath.org/compsci/UMPIRE-Interview-Strategy#understand
- Chapter · 30 min | Competitive Programmer's Handbook, sections 2.3 and 2.4: estimating efficiency, maximum subarray sum | https://cses.fi/book/book.pdf#page=31
- Article · 15 min | Tech Interview Handbook: how to find and optimise solutions | https://www.techinterviewhandbook.org/coding-interview-techniques/#how-to-find-solutions-to-coding-interview-problems
---

=== primer | What does "solved" mean, and what loop gets you there? | 16 min
goal: Run the eight-step solving loop on a new problem from contract to tested code, and know when the problem is really solved
tag: method-loop | The solving loop
link: Wikipedia: How to Solve It, the four phases | https://en.wikipedia.org/wiki/How_to_Solve_It#Four_phases | 5 min: the 'Four phases' section, Pólya's original version of this loop, with the questions he asks in each phase
link: CodePath: UMPIRE interview strategy | https://guides.codepath.org/compsci/UMPIRE-Interview-Strategy#understand | 10 min: 'Understand' and 'Match', the interview version of steps 1, 2 and 4, with sample clarifying questions
practice: 1929, 1480

> [!key]
> A problem is **solved** when your code is correct on every valid input, fast enough for the stated limits, and you can explain why. You get there with one loop, used every time: **Restate, Examples, Brute force, Optimise, Prove, Code, Test, Look back**. Each step produces what the next one needs, and the brute force from step 3 becomes the test oracle in step 7.

## Intuition

A carpenter measures twice, cuts once, then checks the fit. Beginners at algorithms usually do the opposite: read the title, recognise something, start typing, and debug by resubmitting. That works on problems you have already seen. On a new problem it fails, because the typing was never the hard part. The hard parts are knowing exactly what is asked, finding *any* correct method, and then finding a faster one you can trust.

"Accepted by the judge" is not the same as solved. A judge runs a finite sample of tests. Your solution is solved when you can say why it works for every input the statement allows, and you have tested the claim beyond the samples.

## How it works

```flow
Restate: contract and signature -> Examples: by hand, one adversarial -> Brute force: obviously correct
Optimise: remove repeated work -> Prove: one-sentence argument -> Code: from the plan
Test: brute vs fast on random inputs -> Look back: four-line journal
```

| Step | What you produce | The question to ask |
|---|---|---|
| 1. Restate | a one-line contract and the function signature | What are the inputs, the output and the condition linking them? Empty input, duplicates, ties? |
| 2. Examples | three small cases solved by hand, one built to break a naive idea | What did my hands actually do? |
| 3. Brute force | the simplest correct code, and its cost | What is the search space, and how big is it? |
| 4. Optimise | a target complexity from the constraints, and an idea that meets it | Which work does the brute force repeat? Is this a known problem? |
| 5. Prove | one sentence saying why the idea is right | What stays true at every step? |
| 6. Code | the fast version | Does every line follow from the plan? |
| 7. Test | examples, edge cases, and brute versus fast on random inputs | Do they agree on thousands of inputs? |
| 8. Look back | a four-line journal entry | What was the cue? What would make me faster next time? |

**Pólya's four phases** map onto it directly: steps 1 and 2 are *understand the problem*, steps 3 to 5 *devise a plan*, steps 6 and 7 *carry out the plan*, step 8 *look back*. **UMPIRE** (Understand, Match, Plan, Implement, Review, Evaluate) puts "Match: is this a known problem?" inside step 4 and "Review: dry-run your code" inside step 7. What both leave implicit, and this loop makes explicit, are steps 3 and 7: write the brute force, and use it to test.

### The loop on one problem, end to end

*Given a list of at least two integer readings, return the smallest difference between any two of them.*

1. **Restate.** `min_gap(xs) -> int`, with `len(xs) >= 2`; return the minimum of `abs(xs[i] - xs[j])` over positions i != j. Duplicates are allowed, so the answer can be 0. Negative readings are allowed. Do not modify `xs`.
2. **Examples.** [31, 7, 19, 12, 40] gives 5 (7 and 12). [4, 4] gives 0. Now attack the first naive idea, "compare neighbours in the given order": on [1, 10, 2] it says 8, but the answer is 1, because 1 and 2 are not neighbours.
3. **Brute force.** Compare every pair: n(n-1)/2 pairs, O(n^2) time.
4. **Optimise.** With n up to 10^5 that is 5 x 10^9 pairs, hours in Python. The brute force wastes work on pairs that cannot win: once the values are sorted, a pair far apart is never closer than the neighbours between them. So sort, then compare adjacent values only: O(n log n).
5. **Prove.** For sorted a <= b <= c, c - a = (c - b) + (b - a) >= b - a. Any non-adjacent pair is at least as far apart as an adjacent pair inside it, so some adjacent pair achieves the minimum.
6. **Code.** The template below.
7. **Test.** The three examples, then 2,000 random lists comparing `min_gap` with `min_gap_brute`.
8. **Look back.** Cue: "any two elements, order irrelevant, closest". Insight: sorting makes closeness local. Slip: forgetting that equal values give 0. Related: any smallest-difference question.

## Cost

The loop costs minutes and saves sessions. A rough split for a 30-minute medium: restate and examples 5, brute force 5, optimise and prove 10, code 5, test 3, look back 2. An ambiguity caught in step 1 costs a minute; caught after submission, it costs a rewrite.

For the example: the brute force does n(n-1)/2 comparisons, so O(n^2) time and O(1) extra space. The fast version sorts a copy (O(n log n) time, O(n) space; sorting in place would break the "do not modify" rule) and makes one pass over n - 1 neighbours, O(n), for O(n log n) in total.

## When to use it

On every unfamiliar problem. On familiar ones, compress it but never drop Restate or Test. If you recognise a problem instantly, jump to Prove: if you cannot say *why* the known technique applies, you remember it rather than recognise it.

The step you skipped usually shows in the symptom:

| Symptom | Step you skipped |
|---|---|
| Solved the wrong problem ("subsequence" read as "subarray") | Restate |
| Wrong answer on empty, single or all-equal input | Examples |
| A failing fast solution and no idea why | Brute force |
| Time limit exceeded | Optimise (constraints never read) |
| A clever rule that works on the samples only | Prove |
| The same mistake again next month | Look back |

## Worked trace

```steps
**Restate.** Write the contract before anything else
    min_gap(xs) -> int,  len(xs) >= 2
    answer = min |xs[i] - xs[j]| over positions i != j
    {{duplicates allowed, so the answer may be 0; xs is not modified}}
---
**Examples.** Solve small cases by hand, one built to break a naive idea
    [31, 7, 19, 12, 40]  ->  5     (7 and 12)
    [4, 4]               ->  0
    {{[1, 10, 2]           ->  1     "neighbours in input order" says 8}}
---
**Brute force.** The obviously correct version, and its cost
    compare every pair i < j: n(n-1)/2 comparisons
    {{O(n^2) time, O(1) extra space}}
---
**Optimise.** n up to 10^5 means 5*10^9 pairs: far too slow. Sort first
    sorted   7    12    19    31    40
    gaps        5     7     12     9
    {{answer = smallest adjacent gap = 5}}
---
**Prove.** For a <= b <= c:  c - a = (c - b) + (b - a) >= b - a
    {{a far pair is never closer than a neighbour pair inside it}}
---
**Code and test.** Fast version, then compare with the brute force
    3 hand examples: pass
    {{2000 random lists, sizes 2..8, values -20..20: all agree}}
---
**Look back.** Four lines in the journal
    cue:     closest pair, order does not matter
    insight: sorting makes "close" mean "adjacent"
    slip:    forgot that equal values give 0
    related: any smallest-difference question
```

## Template

One file per problem, laid out in loop order. Copy this shape for every problem you practise.

```python
"""min_gap: smallest |a - b| over two different positions of xs (len(xs) >= 2)."""
import random
from itertools import combinations


def min_gap_brute(xs):
    """Step 3: every pair, O(n^2). Obviously correct, kept as the test oracle."""
    return min(abs(a - b) for a, b in combinations(xs, 2))


def min_gap(xs):
    """Step 6: after sorting, only neighbours can be closest. O(n log n)."""
    s = sorted(xs)                       # a sorted copy: the caller's list is untouched
    return min(b - a for a, b in zip(s, s[1:]))


if __name__ == "__main__":
    examples = [([31, 7, 19, 12, 40], 5), ([4, 4], 0), ([1, 10, 2], 1)]     # step 2
    for xs, want in examples:
        assert min_gap_brute(xs) == want and min_gap(xs) == want, xs
    rng = random.Random(1)                                                  # step 7
    for _ in range(2000):
        xs = [rng.randint(-20, 20) for _ in range(rng.randint(2, 8))]
        assert min_gap(xs) == min_gap_brute(xs), xs
    print("all tests passed")
```

## Pitfalls

- **Accepted is not solved.** A judge samples inputs. Solved means correct for every valid input, within the limits, and explainable.
- **Jumping from examples to code with half an idea.** The brute force costs minutes and gives you an oracle; the half-idea costs an hour of debugging.
- **Proving with examples.** Three passing cases are evidence. The Prove step is one sentence that covers every input.
- **Testing only the statement's examples.** They were chosen to explain the problem, not to break your code.
- **Running the loop silently.** Write the contract and examples into the file as a docstring and asserts. In an interview, say each step aloud.

## Check yourself

Q: A teammate's `min_gap` compares only neighbours in the original order. What does it return on [31, 7, 19, 12, 40], and what is the smallest input size on which such a function can fail?
A: The neighbour gaps in input order are 24, 12, 7 and 28, so it returns 7 instead of 5. It needs at least three elements to fail: with two there is only one pair, which is also the only neighbour pair. [1, 10, 2] is a minimal failing input (it returns 8, the answer is 1).

Q: The stress test passed 2,000 random lists. Why still write the one-sentence proof?
A: Random tests sample small sizes and small values; a bug that needs a large n or a specific structure can slip through. The proof covers every input, and the test catches mistakes in the proof and in the code. Each covers the other's blind spot.

Q: Run steps 3 to 5 quickly for "the largest difference between any two readings".
A: Brute force: every pair, O(n^2). Optimise: the answer is max(xs) - min(xs), one pass, O(n), no sort needed. Prove: every reading lies in [min, max], so no pair is further apart than max - min, and the pair (max, min) achieves it.

## Lab

- **1929 Concatenation of Array**: run all eight steps even though the problem is tiny: write the contract (what is ans[i] for i >= n?), two examples, the code and a test. Expected: [4, 0, 7] gives [4, 0, 7, 4, 0, 7]; O(n) time and O(n) space for the output (`nums + nums` builds it in one C-level copy).
- **1480 Running Sum of 1d Array**: write the brute force first (`sum(nums[:i + 1])` for every i, O(n^2)), then a version that keeps one running total, and compare them on 1,000 random lists. Expected: [3, -1, 4, 1] gives [3, 2, 6, 7]; the fast version is O(n) and agrees with the brute force on every list.

> [!know]
> You now know how to run the eight-step solving loop end to end and what it takes to call a problem solved.

=== primer | How do you pin a problem down before solving it? | 14 min
goal: Turn a vague statement into a written contract with edge rules, then solve small examples by hand, including one designed to break the first idea
tag: method-restate | Restate and work examples
link: Tech Interview Handbook: solve it by hand, then more examples | https://www.techinterviewhandbook.org/coding-interview-techniques/#2-think-about-how-you-would-solve-the-problem-by-hand | 5 min: tips 2 and 3, solving by hand and generating more examples, each with a short worked case
practice: 1929, 1365

> [!key]
> Most wrong answers are right answers to a different question. Before designing anything, write a **contract**: the signature, what each input may contain, what the output must satisfy, and the rule for every edge case (empty, one item, duplicates, ties, negatives). Then solve three small examples by hand, including an **adversarial example** built to break your first idea. What your hands do on paper becomes the code.

## Intuition

A ticket says "return the second largest number". On [7, 7, 3], is it 7 or 3? On [5], is it an error, None or 5? On [-2, -9], it is surely -9, but a version that starts from 0 returns 0. Each answer defines a different function. If you do not decide, the code decides for you, usually inconsistently.

Pólya's first questions are the ones to ask: *What is the unknown? What are the data? What is the condition?*

## How it works

### Restate in three parts

- **Unknown (output):** type, shape, order, and what to return when no answer exists.
- **Data (inputs):** types, sizes, value ranges, sorted or not, may be empty, may repeat.
- **Condition:** the exact relation between them, phrased so that a checker could verify an answer.

For the second-largest ticket, the decision written down:

```python
def second_largest(xs: list[int]) -> int | None:
    """Second largest DISTINCT value of xs, or None if xs has fewer than two distinct values.
    xs may be empty and may contain duplicates and negatives; it is not modified."""
```

### Ask, or decide and write it down

| Question | Why it matters |
|---|---|
| Can the input be empty? How large can it get? | base case; target complexity |
| Are there duplicates, and do they count separately? | "distinct values" or "positions" |
| On ties, which answer is wanted? | deterministic output |
| Negative numbers or zero? | sentinel values such as 0 or -1 break |
| Is it sorted? May I modify it? | in-place work allowed or not |
| Indices or values? 0-based or 1-based? Any order? | output format |

In an interview, ask these out loud. On a judge, the constraints block and the examples answer most of them; decide the rest and write the decision in the docstring.

### Work examples by hand, then read your hands

Pick cases in rising difficulty: trivial (empty, one item), typical, then adversarial. Solve them slowly and notice what you keep track of. Scanning for the second largest, you hold two things in your head: the largest so far, and the largest value below it. Those two variables are the algorithm.

### Build the adversarial example

For every naive idea, look for the input that breaks it:

| Naive idea | Breaking input | It returns | Correct |
|---|---|---|---|
| `sorted(xs)[-2]` | [7, 7, 3] | 7 | 3 |
| start with `first = second = 0` | [-2, -9] | 0 | -9 |
| `elif x > second` without a distinct check | [7, 7] | 7 | None |

## Cost

Restating takes two to five minutes and each hand example one or two. The resulting scan visits each item once with O(1) work: O(n) time, O(1) extra space. The brute force used to check it, `sorted(set(xs))`, is O(n log n) time and O(n) space, which is fine for an oracle.

## When to use it

On every problem, and especially when:

- the statement is a story: strip it to unknown, data and condition;
- words such as *subarray* (contiguous), *subsequence* (order kept, gaps allowed), *subset*, *distinct*, *at most* or *exactly* appear;
- the output is indices, a count or a list whose order or format matters;
- ties or duplicates are possible.

For grids, trees, intervals and pointer problems, draw the example; a picture is a hand example too. On judges, treat the constraints block as part of the contract: it tells you whether empty input can happen (1929 promises n >= 1, so it never does).

## Worked trace

Solving [4, 9, 9, -2, 7] by hand, tracking the two values your eyes keep:

```steps
Start: nothing seen yet
    xs     4   9   9  -2   7
    first = None     second = None
---
x = 4 beats everything so far: it becomes first
    xs     {{4}}   9   9  -2   7
    first = 4        second = None
---
x = 9 beats first: the old first slides down to second
    xs     4   {{9}}   9  -2   7
    first = 9        second = 4
---
x = 9 equals first: a repeat, not a new distinct value, so skip it
    xs     4   9   {{9}}  -2   7
    first = 9        second = 4
---
x = -2 is below second: nothing changes
    xs     4   9   9  {{-2}}   7
    first = 9        second = 4
---
x = 7 is between second and first: it becomes second
    xs     4   9   9  -2   {{7}}
    first = 9        second = 7     answer: 7
```

## Template

The contract, the hand process as code, an independent oracle, and the examples as executable asserts:

```python
def second_largest(xs):
    """Second largest DISTINCT value of xs, or None if xs has fewer than two distinct values.
    xs may be empty and may contain duplicates and negatives; it is not modified."""
    first = second = None
    for x in xs:
        if first is None or x > first:
            first, second = x, first
        elif x != first and (second is None or x > second):
            second = x
    return second


def second_largest_brute(xs):
    distinct = sorted(set(xs))
    return distinct[-2] if len(distinct) >= 2 else None


EXAMPLES = [                       # trivial, typical, then the adversarial ones
    ([], None), ([5], None), ([7, 7], None),
    ([4, 9, 9, -2, 7], 7), ([7, 7, 3], 3), ([-2, -9], -9),
]
for xs, want in EXAMPLES:
    assert second_largest(xs) == want == second_largest_brute(xs), xs
```

## Pitfalls

- **Sentinels such as 0 or -1 for "nothing yet".** They break on zero or negative data. Use `None`, or `float("-inf")` when the output type allows it.
- **Returning positions when values were asked**, or 1-based indices when 0-based were expected.
- **A decision made in your head but not written down.** The code drifts from it within ten lines.
- **Examples that only confirm.** If every example you wrote passes your idea, you have not yet looked for the one that breaks it.
- **Mutating the input** with `xs.sort()` when the caller still needs the original order.

## Check yourself

Q: Predict `second_largest([3, 3, 3, 1])` and `second_largest([-5, -5])`, tracing first and second.
A: For [3, 3, 3, 1]: first becomes 3, the next two 3s are skipped as repeats, then 1 becomes second, so the answer is 1. For [-5, -5]: first is -5, the second -5 is a repeat, second stays None, so the answer is None.

Q: A colleague writes `first = second = float("-inf")`, then `if x > first: first, second = x, first` and `elif first > x > second: second = x`, and returns `second`. Which inputs break the contract, and what is the fix?
A: Every input with fewer than two distinct values: [], [5] and [7, 7] all return -inf instead of None. Everything else is right (the chained comparison already skips repeats). Fix: `return None if second == float("-inf") else second`.

Q: Write the contract and four examples for "length of the longest run of equal adjacent values".
A: `longest_run(xs) -> int`; empty input gives 0; runs must be contiguous, so [1, 2, 1] gives 1, not 2; any integers; input not modified. Examples: [] gives 0, [5] gives 1, [3, 7, 7, 7] gives 3, and the adversarial [1, 1, 2, 2, 2] gives 3, which breaks any version that updates the best only when a run ends, because the longest run is the last one.

## Lab

- **1929 Concatenation of Array**: write the contract in your own words before coding: input length n, output length 2n, and the rule for ans[i] and ans[i + n]. Expected: [4, 0, 7] gives [4, 0, 7, 4, 0, 7]; the constraints promise 1 <= n <= 1000, so no empty case is needed.
- **1365 How Many Numbers Are Smaller Than the Current Number**: restate the condition precisely (strictly smaller, any other position j) and solve [6, 1, 6, 0, 3] on paper before coding. Expected: [3, 1, 3, 0, 2]; equal values get equal answers, and a value never counts itself.

> [!know]
> You now know how to turn a statement into a written contract and hand-worked examples that expose naive ideas before you code.

=== primer | Why write the brute force first, and how do you write one quickly? | 14 min
goal: Write a correct brute force in minutes by naming its search space, state its cost, and keep it as the oracle for faster versions
tag: method-brute | Brute force as the oracle
link: Python docs: itertools.combinations | https://docs.python.org/3/library/itertools.html#itertools.combinations | 5 min: combinations, then product and permutations just below it; each entry shows equivalent pure Python code and the number of items produced
link: USACO Guide: Complete Search | https://usaco.guide/bronze/intro-complete#solution---maximum-distance | 5 min: 'Solution - Maximum Distance', a contest problem where trying every pair is the intended solution
practice: 1512, 1913

> [!key]
> A brute force tries every candidate answer and keeps the ones that satisfy the condition. Write it first, every time: it proves you understood the problem, it often passes small constraints outright, it shows exactly which work to remove, and it becomes the **oracle** that checks your fast solution on thousands of random inputs. The skill is naming the search space (pairs, subarrays, subsets, orders) and its size.

## Intuition

Looking for lost keys by checking every pocket and drawer in a fixed order is slow, but you are certain to find them and you know the worst case. "Where did I last have them?" is faster when it works. The brute force is the certain version, and you keep it around to check the clever one.

## How it works

### Name the search space

Almost every brute force enumerates one of five shapes:

| Shape | Typical wording | Python | How many |
|---|---|---|---|
| Pairs i < j | "two elements that..." | `combinations(range(n), 2)` | n(n-1)/2 |
| Subarrays [i, j) | "contiguous", "substring" | two nested loops | n(n+1)/2 |
| Subsets | "choose some", "subsequence" | `combinations(xs, r)` for every r, or bitmasks | 2^n |
| Orders | "arrange", "schedule", "visit all" | `permutations(xs)` | n! |
| Sequences of choices | "at each of k steps pick one of m" | `product(options, repeat=k)` | m^k |

### Generate, check, aggregate

A brute force has three parts: a **generator** of candidates, a **checker** of the condition and an **aggregator** (count, min, max, first, any). Write each part in the most obviously correct way, with no early exits and no cleverness. The oracle's only job is to be right.

### Keep it

Do not delete the brute force when the fast version works. Keep both in the file and compare them on random inputs (the Test step). The next card shows how its inner loop tells you what to optimise, and the correctness module turns the comparison into a reusable stress-testing harness.

## Cost

Cost = (number of candidates) x (cost to check one):

- pairs with an O(1) check: n(n-1)/2, so O(n^2);
- subarrays whose sum is recomputed from scratch: about n^2/2 subarrays x O(n) per sum, so O(n^3);
- subsets with an O(n) check: O(n x 2^n);
- orders with an O(n) check: O(n x n!).

At about 10^7 simple steps per second in CPython, these run in a second or so up to roughly n = 3,000 for pairs, n = 200 for cubic subarray sums, n = 20 for subsets and n = 9 for orders. Beyond that, the brute force is only an oracle for small test inputs.

## When to use it

- **Always as your first code**, even if it is three lines.
- **As the final answer** when the constraints allow it: n <= 20 with subsets, n <= 3,000 with pairs. Setters choose tiny limits exactly when exhaustive search is intended.
- **As the oracle** in every test: small random inputs (sizes 0 to 8) find most bugs and keep the brute force fast.
- **Not as the oracle** when even small inputs explode (n! at n = 12 is 479 million), unless you keep the test sizes tiny.

## Worked trace

Count the pairs whose sum is a multiple of 3 in [4, 1, 2, 5] by checking all six pairs in `combinations` order:

```steps
Pair (0, 1): 4 + 1 = 5, not a multiple of 3
    xs    {{4   1}}   2   5
    pairs found: 0
---
Pair (0, 2): 4 + 2 = 6, a multiple of 3
    xs    {{4}}   1   {{2}}   5
    pairs found: {{1}}
---
Pair (0, 3): 4 + 5 = 9, a multiple of 3
    xs    {{4}}   1   2   {{5}}
    pairs found: {{2}}
---
Pair (1, 2): 1 + 2 = 3, a multiple of 3
    xs    4   {{1   2}}   5
    pairs found: {{3}}
---
Pair (1, 3): 1 + 5 = 6, a multiple of 3
    xs    4   {{1}}   2   {{5}}
    pairs found: {{4}}
---
Pair (2, 3): 2 + 5 = 7, no. All n(n-1)/2 = 6 pairs checked
    xs    4   1   {{2   5}}
    pairs found: 4
```

## Template

The five enumerators, then three brute forces built from them:

```python
from itertools import combinations, permutations, product


def pairs(n):
    """All index pairs i < j: n(n-1)/2 of them."""
    return combinations(range(n), 2)


def subarrays(n):
    """All non-empty half-open ranges [i, j): n(n+1)/2 of them."""
    return ((i, j) for i in range(n) for j in range(i + 1, n + 1))


def subsets(xs):
    """All 2^n subsets as tuples, smallest first."""
    return (s for r in range(len(xs) + 1) for s in combinations(xs, r))


def orders(xs):
    """All n! arrangements."""
    return permutations(xs)


def choices(options, k):
    """All len(options)^k sequences of k picks, repeats allowed."""
    return product(options, repeat=k)


def count_pairs_brute(xs, k):
    """Pairs i < j whose sum is a multiple of k."""
    return sum((xs[i] + xs[j]) % k == 0 for i, j in pairs(len(xs)))


def max_block_sum_brute(xs):
    """Largest sum of a non-empty contiguous block."""
    return max(sum(xs[i:j]) for i, j in subarrays(len(xs)))


def subset_with_sum(xs, target):
    """Some subset adding up to target, or None."""
    return next((s for s in subsets(xs) if sum(s) == target), None)
```

## Pitfalls

- **Optimising the brute force.** Its value is being obviously right; an early `break` or a clever skip is exactly where bugs hide.
- **Enumerating the wrong space.** Subarray (contiguous), subsequence (order kept), subset (order irrelevant) and permutation are different problems. The Restate step settles which one you have.
- **Mishandling the empty candidate.** `subsets` includes the empty tuple; `max()` of an empty sequence raises `ValueError`.
- **Changing the problem with `set()`.** Pairs i < j count positions, so duplicates are separate candidates.
- **A brute force that shares code with the fast one.** If both call the same buggy helper, they agree on wrong answers. Keep the oracle independent.

## Check yourself

Q: For n = 20, how many candidates are there for pairs, subarrays, subsets and orders, and which brute forces finish in about a second in CPython?
A: 190 pairs, 210 subarrays, 2^20 = 1,048,576 subsets and 20!, about 2.4 x 10^18 orders. The first three are fine (subsets with an O(n) check is about 2 x 10^7 steps, a second or two); orders are hopeless.

Q: Trace `subset_with_sum([3, 5, 2], 7)`: what does it return, and why that subset?
A: (5, 2). Subsets come out by size: (), then (3,), (5,), (2,), then (3, 5) = 8, (3, 2) = 5, (5, 2) = 7, which is the first one whose sum is 7.

Q: Your fast solution and your brute force disagree on [2, 2, 1]. Which do you trust first, and why must they not share helpers?
A: Trust the brute force first, because it is simpler, but check it by hand on that tiny input: an oracle can be wrong too. They must not share helpers, because a shared bug makes both wrong in the same way and the comparison stays silent.

## Lab

- **1512 Number of Good Pairs**: write the brute force with `combinations`, state its cost, and keep it to test your faster version later. Expected: [2, 5, 2, 2, 5, 9] gives 4 (three pairs of 2s, one pair of 5s); O(n^2) is fine for the stated n <= 100.
- **1913 Maximum Product Difference Between Two Pairs**: brute-force all ordered choices of four distinct indices with `permutations(range(n), 4)` on small lists, print which four values win, and form a hypothesis. Expected: [5, 9, 1, 4, 7] gives 59 (9 x 7 - 1 x 4); the brute force is O(n^4), an oracle only, since n can be 10^4.

> [!know]
> You now know how to enumerate a search space, cost a brute force, and keep it as the oracle for faster code.

=== primer | How do the constraints tell you what complexity to aim for? | 13 min
goal: Turn the input limits into a target complexity before designing, using a realistic budget for CPython
tag: method-budget | Constraints to a target complexity
link: USACO Guide: Time Complexity | https://usaco.guide/bronze/time-comp#common-complexities-and-constraints | 5 min: the table 'Common Complexities and Constraints'; its numbers assume C++, so scale them down for Python as this card explains
link: Competitive Programmer's Handbook, section 2.3 | https://cses.fi/book/book.pdf#page=31 | 5 min: 'Estimating efficiency' (the top half of book page 21), the input-size table and why 10^10 operations is too many
practice: 1365, 1913

> [!key]
> The constraints are a hint the problem setter cannot avoid giving. A judge allows about a second, and CPython runs roughly **10^7 simple steps per second** (a loop iteration with an addition or comparison). So n up to a few thousand allows O(n^2), n up to 10^5 or 10^6 needs O(n log n) or O(n), and n up to 10^9 needs O(log n) or a formula. Read the limits first, write the target down, and only develop ideas that can meet it.

## Intuition

An airline's weight limit decides what you can pack before you choose items. A constraint such as n <= 10^5 is that limit: an O(n^2) plan means 10^10 steps, about 17 minutes in Python, so it is ruled out before you write a line.

## How it works

### Know your budget

On a recent workstation with CPython 3.12, `for i in range(10**7): s += i` takes one to two seconds. Built-ins that loop in C (`sum` over a list, `sorted`, `set`, `Counter`, `str.join`) are many times faster per element, so a sort of 10^6 numbers takes well under a second. Measure your own machine once with `measure_budget()` in the template.

### Read the table for Python, not for C++

| Largest n | C++ can afford (about 10^8 to 10^9 steps) | Pure Python can afford (about 10^7 steps) |
|---|---|---|
| 10 | O(n!) | O(n!) only with a cheap check (10! = 3.6 x 10^6) |
| 20 | O(2^n) | O(2^n), since 2^20 is about 10^6; O(n x 2^n) takes a few seconds |
| 500 | O(n^3) | O(n^2 log n); O(n^3) only up to about n = 200 |
| 5,000 | O(n^2) | O(n^2) up to about n = 3,000; above that O(n log n) |
| 10^5 to 10^6 | O(n log n) | O(n log n) or O(n), with the heavy lifting in built-ins |
| 10^9 and more | O(log n) or O(1) | the same |

### Read every constraint, not just n

- **Queries q.** Total cost is preprocessing plus q x (cost per query). With n = q = 10^5, an O(n) scan per query is 10^10 steps, so each query must be O(log n) or O(1) after preprocessing.
- **Value ranges.** Values up to 100 invite a counting array of 101 slots; values up to 10^9 rule that out (use a dict, or sort). Sums of 10^5 values of size 10^9 reach 10^14, past 32-bit range: use `long long` in C++ or `long` in Java. Python integers never overflow.
- **Several sizes.** An n x m grid with n, m <= 1000 has 10^6 cells: O(nm) is fine, O((nm)^2) is not.
- **Memory.** An n x n table for n = 10^4 has 10^8 cells, about 800 MB of pointers in a Python list of lists.
- **A floor as well as a ceiling.** You must read the input (O(n)) and write the output; if the answer lists all pairs, O(n^2) output is unavoidable.

## Cost

Estimate time as steps / 10^7 seconds. For n = 2 x 10^5: n^2 = 4 x 10^10 steps, over an hour; n log2 n is about 3.5 x 10^6 steps, under a second. A doubling experiment checks the estimate later: when n doubles, time multiplies by about 2 for O(n), a little over 2 for O(n log n), 4 for O(n^2) and 8 for O(n^3).

## When to use it

Before designing, on every problem, and when choosing between two ideas. If the limits are generous (n <= 100), stop optimising: the clear O(n^3) beats a buggy O(n log n). In an interview, ask "how large can n get?"; "large" usually means 10^5 to 10^6.

Where the budget misleads: constant factors. A pure Python O(n) loop can lose to an O(n log n) `sorted()` call for every realistic n, because the sort runs in C. Hidden limits also exist in stories: a day has 1,440 minutes and an alphabet has 26 letters, both small enough to enumerate.

## Worked trace

```steps
Read the constraint block before the story
    1 <= n <= 2 * 10^5
    -10^9 <= a[i] <= 10^9
    1 <= q <= 10^5 queries, each about a range [l, r)
---
n = 2*10^5: all pairs is n^2 = 4*10^10 steps, over an hour in Python
    {{O(n^2) is out}}
    n log2 n = 3.5*10^6 steps: under a second
---
q = 10^5 queries: an O(n) scan per query is 2*10^10 steps
    {{each query must cost O(log n) or O(1)}}
    so: preprocess once, then answer fast
---
Values up to 10^9 in size: no array indexed by value
    {{use a dict, or sort and compare}}
    range sums reach 2*10^14: fine in Python, 64-bit in C++/Java
---
Write the target down before any design
    {{O((n + q) log n) time, O(n) extra memory}}
    candidates: prefix sums, or sorting with bisect
```

## Template

A budget helper to call while reading constraints:

```python
import math
import time

BUDGET = 10**7     # simple CPython steps per second; replace with measure_budget() on your machine


def steps(n):
    """Rough step counts of common complexities at input size n."""
    lg = math.log2(max(n, 2))
    return {
        "n!": math.factorial(n) if n <= 20 else math.inf,
        "2^n": 2**n if n <= 60 else math.inf,
        "n^3": n**3,
        "n^2": n**2,
        "n log n": n * lg,
        "n": n,
        "log n": lg,
    }


def affordable(n, seconds=1.0):
    """The complexities whose step count fits the time budget."""
    return [name for name, s in steps(n).items() if s <= BUDGET * seconds]


def measure_budget():
    """Simple loop steps per second on this machine."""
    t0 = time.perf_counter()
    s = 0
    for i in range(10**6):
        s += i
    return 10**6 / (time.perf_counter() - t0)


print(affordable(20))         # ['2^n', 'n^3', 'n^2', 'n log n', 'n', 'log n']
print(affordable(3_000))      # ['n^2', 'n log n', 'n', 'log n']
print(affordable(200_000))    # ['n log n', 'n', 'log n']
```

## Pitfalls

- **Using the C++ table for Python.** 10^8 simple steps is a second in C++ and roughly ten seconds in CPython.
- **Reading only n.** Queries, value ranges, test-case counts and grid sizes all change the target.
- **Multiplying wrongly.** A loop over queries with a loop over n inside is O(n x q), not O(n + q).
- **Over-optimising** when the limits are small: a clear brute force that meets the target is the best answer.
- **Trusting Big-O at small n.** Below a few thousand items, constants and C built-ins dominate; measure.

## Check yourself

Q: n <= 10^5 and your idea is O(n x sqrt(n)). Is it plausible in Python?
A: n x sqrt(n) is 10^5 x 316, about 3.2 x 10^7 steps, roughly three seconds of pure Python: borderline. It is fine in C++, but in Python look for O(n log n) first, or push the inner work into built-ins.

Q: A problem says n <= 18. What does that suggest, and why would a setter choose 18 rather than 10^5?
A: An exponential search over subsets: 2^18 = 262,144 subsets, and with O(n) work each about 4.7 x 10^6 steps. Setters choose tiny limits only when the intended solution is exponential (all subsets, bitmask DP); otherwise they would allow larger inputs to rule out brute force.

Q: Spot the mistake: "n <= 10^5 and q <= 10^5; my answer scans the array once per query, so it is O(n + q)."
A: The scan runs once per query, so the total is O(n x q) = 10^10 steps. Costs multiply when one loop runs inside another. The target is O(log n) or O(1) per query after an O(n) or O(n log n) preprocessing step.

## Lab

- **1365 How Many Numbers Are Smaller Than the Current Number**: read the limits (n <= 500, values 0 to 100) and decide whether the O(n^2) brute force is acceptable, then use the small value range for a counting solution. Expected: both return [3, 1, 3, 0, 2] for [6, 1, 6, 0, 3]; the brute force is at most 250,000 comparisons, fine here; the counting version is O(n + 101) and scales to any n.
- **1913 Maximum Product Difference Between Two Pairs**: with n up to 10^4, rule out the O(n^4) brute force (10^16 quadruples) and set the target before designing. Expected: sorting, O(n log n) and about 1.3 x 10^5 steps, is comfortably enough; an O(n) pass that tracks the two largest and two smallest values also works; both return 59 for [5, 9, 1, 4, 7].

> [!know]
> You now know how to read the constraints as a time budget and write down a target complexity before designing anything.

=== primer | How do you find the bottleneck in a brute force and remove it? | 15 min
goal: Name the question a brute force's inner loop keeps asking and remove it with the matching tool from the optimisation menu
tag: method-bottleneck | Find and remove the bottleneck
link: Tech Interview Handbook: repeated computation | https://www.techinterviewhandbook.org/coding-interview-techniques/#2-identify-overlapping-and-repeated-computation | 5 min: 'Identify overlapping and repeated computation' and 'Try different data structures', two short worked examples
link: PostgreSQL docs: generating possible plans | https://www.postgresql.org/docs/current/planner-optimizer.html#PLANNER-OPTIMIZER-GENERATING-POSSIBLE-PLANS | 5 min: the three join strategies (nested loop, merge join, hash join), a database applying this menu automatically
practice: 1512, 1480

> [!key]
> In a brute force, the slow part is almost always an **inner loop that answers the same kind of question again and again**. Say that question in words ("how many earlier elements have remainder r?", "what is the sum of xs[i:j]?"), then answer it with the matching structure: a hash map, a sort, a precomputed table, two pointers, binary search, a heap or a memo. One question, one fix; repeat until the cost meets the target.

## Intuition

A shop assistant asked "do we have this shoe in size 42?" walks to the stockroom and opens every box, for every customer. Walking faster is not the fix. A list on the counter (a hash map), or boxes arranged by size (sorting, then binary search), answers the same question instantly. The bottleneck is a repeated question; the fix is remembering or organising the answers.

## How it works

### 1. Find the inner loop and say what it asks

In `count_pairs_brute` from the previous card, for each j the inner loop over i < j asks: *how many earlier elements x satisfy (x + xs[j]) % k == 0?* Equivalently: *how many earlier elements have remainder (k - xs[j] % k) % k?* That is a counting question about the past.

### 2. Pick the fix from the menu

| The inner loop keeps asking... | Fix | Cost afterwards |
|---|---|---|
| "Have I seen x, or x's partner, before? How many times?" | `set`, `dict` or `Counter` of the past | O(1) average per question |
| "What is the sum (or max) of this range?" | precompute: prefix sums, running max | O(1) per question after O(n) |
| "Which elements are close, or equal?" | sort first, then look at neighbours | O(n log n) once |
| "Where does a condition flip?" in sorted data | binary search (`bisect`) | O(log n) |
| "Which pairs?" in sorted data, moving one way | two pointers | O(n) in total |
| "Smallest or largest of a changing set?" | heap (`heapq`) | O(log n) per change |
| "The same subproblem again?" in recursion | memoise (`functools.cache`) | each state once |

### 3. Check the new cost against the target, and repeat

Each fix usually removes one factor of n. If you are still over the target, find the next repeated question. Then test the new version against the brute force before moving on.

For the pairs problem, the fix is a `Counter` of remainders seen so far. Scan left to right; for each element, **look up its partners among earlier elements, then record it**. Looking up first means an element never pairs with itself and each pair is counted exactly once (at its later element).

## Cost

The brute force makes n(n-1)/2 checks: O(n^2). The scan makes n iterations with one lookup and one update each, O(1) on average for a dict, so O(n) time; the counter holds at most min(n, k) remainders, so O(min(n, k)) extra space. You traded memory for time, the most common trade in this guide. (Hash tables are O(1) on average, not in the worst case; the hashing module explains when that matters.)

## When to use it

When the brute force is correct but over the target. The ladder is: brute force, find the bottleneck question, apply one fix, test against the brute force, repeat.

Stop when the target is met; n <= 100 needs no fix at all. Check that the fix does not change the problem: sorting destroys positions (sort `(value, index)` pairs when indices matter), and `set()` loses duplicates when they count.

| Hash map or sort? | Hash map | Sort |
|---|---|---|
| Time | O(n) average | O(n log n) |
| Keeps order information | no | yes: enables neighbours, two pointers, bisect |
| Extra space | O(n) | O(1) in place (or O(n) for a copy) |
| Worst case | degrades with adversarial keys | guaranteed |

## Worked trace

The scan on [4, 1, 2, 5, 3, 6] with k = 3. `seen` counts the remainders of earlier elements:

```steps
Scan left to right; look up partners first, then record the element
    xs    4  1  2  5  3  6
    rem   1  1  2  2  0  0
    seen {}                        pairs 0
---
x = 4, r = 1, partner remainder (3 - 1) % 3 = 2: none seen yet
    xs    {{4}}  1  2  5  3  6
    seen {1: 1}                    pairs 0
---
x = 1, r = 1, partner 2: still none
    xs    4  {{1}}  2  5  3  6
    seen {1: 2}                    pairs 0
---
x = 2, r = 2, partner 1: two earlier elements (4 and 1)
    xs    4  1  {{2}}  5  3  6
    seen {1: 2, 2: 1}              pairs {{2}}
---
x = 5, r = 2, partner 1: two more (4 + 5, 1 + 5)
    xs    4  1  2  {{5}}  3  6
    seen {1: 2, 2: 2}              pairs {{4}}
---
x = 3, r = 0, partner (3 - 0) % 3 = 0: none yet
    xs    4  1  2  5  {{3}}  6
    seen {1: 2, 2: 2, 0: 1}        pairs 4
---
x = 6, r = 0, partner 0: one earlier (3 + 6)
    xs    4  1  2  5  3  {{6}}
    seen {1: 2, 2: 2, 0: 2}        pairs {{5}}
```

## Template

The general shape is: for each item, answer the question from a memory of the past, then add the item to the memory.

```python
from collections import Counter


def count_pairs_divisible(xs, k):
    """Pairs i < j with (xs[i] + xs[j]) % k == 0, in O(n) time."""
    seen = Counter()                     # remainder -> how many earlier elements have it
    pairs = 0
    for x in xs:
        r = x % k
        pairs += seen[(k - r) % k]       # earlier partners that complete a multiple of k
        seen[r] += 1                     # record x only after looking up its partners
    return pairs
```

## Pitfalls

- **Recording before looking up.** The element then pairs with itself whenever it is its own partner (remainder 0, or k/2 when k is even), so the count is too high.
- **`k - r` instead of `(k - r) % k`.** Remainder 0 needs partner 0, not k.
- **Negative numbers in other languages.** Python's `%` with a positive k is never negative (`-4 % 3 == 2`); in C++ and Java `-4 % 3` is -1, so normalise with `((x % k) + k) % k`.
- **Hidden inner loops.** `x in some_list`, `list.index`, `list.pop(0)`, `s += piece` on strings in a loop and slices such as `xs[:i]` are all O(n) each.
- **A fix that changes the answer.** Sorting when positions matter; `set()` when duplicates count.

## Check yourself

Q: Predict `count_pairs_divisible([3, 3, 3], 3)`, tracing `seen`.
A: 3. The first 3 has remainder 0 and finds no partners; seen = {0: 1}. The second finds one (pairs 1); seen = {0: 2}. The third finds two (pairs 3). All three pairs sum to 6.

Q: A brute force decides whether any value repeats by testing `xs[i] in xs[i + 1:]` for every i. What is its cost, the bottleneck question, and the fix?
A: O(n^2): each slice copies O(n) items and each `in` scans O(n). The repeated question is "has this value appeared among the other elements?"; a set of values seen so far answers it in O(1) on average, so one scan finds a repeat in O(n).

Q: Why must the scan look up before it records? Give the smallest input where record-first goes wrong.
A: Recording first lets an element count itself as its own partner. With k = 3, the input [3] has no pairs, but record-first stores remainder 0 and then finds it, reporting 1.

## Lab

- **1512 Number of Good Pairs**: start from your O(n^2) brute force, name the inner loop's question ("how many earlier elements equal this one?") and answer it with a `Counter`. Expected: [2, 5, 2, 2, 5, 9] gives 4; O(n) time; brute force and fast version agree on 1,000 random lists with values 1 to 5.
- **1480 Running Sum of 1d Array**: the brute force recomputes `sum(nums[:i + 1])` for every i; keep one running total instead. Expected: [3, -1, 4, 1] gives [3, 2, 6, 7] in O(n); `itertools.accumulate(nums)` computes the same running totals in C.

> [!know]
> You now know how to name the repeated question in a brute force and remove it with the matching tool from the optimisation menu.

=== primer | What do you do when you are stuck? | 14 min
goal: Get unstuck with a short list of Pólya's heuristics and by reducing the problem to one you already know
tag: method-stuck | Getting unstuck: heuristics and reductions
link: Wikipedia: How to Solve It, heuristics dictionary | https://en.wikipedia.org/wiki/How_to_Solve_It#Heuristics_dictionary | 5 min: the table of heuristics; every row is a question you can ask yourself when stuck
practice: 169, 1512

> [!key]
> Being stuck means your current view of the problem suggests no move. Change something on purpose: **specialise** (solve tiny cases and look for a pattern), **drop a condition**, **work backwards** from the goal, **change the representation** (sort it, draw it, count the complement), or **reduce** it to a problem you already know. Ask each question for a few minutes, in order, before taking a hint.

## Intuition

A locked door does not open if you push harder. You try the back door (work backwards), a smaller window (a simpler problem), or notice that the house is one you have entered before (a reduction). Rereading the statement for the fifth time is pushing harder. Each heuristic below forces you to write something new.

## How it works

### The short list

| Heuristic | Question to ask | Example |
|---|---|---|
| Specialise | What happens for n = 1, 2, 3? Print a table. | The locker puzzle below: the answers step up at 1, 4, 9, 16 |
| Drop a condition | Can I solve it without the hardest constraint? | "Best block sum with at most one deletion": solve it with no deletion first, then add one more piece of state |
| Work backwards | What must the last step look like? | Fewest moves from 1 to n using +1 and x2: from n, halve when even, else subtract 1 |
| Change the representation | Would sorting, a graph or a picture help? | Overlapping meetings: sort by start time and compare neighbours |
| Count the complement | Is the opposite easier to count? | Pairs with different values = all pairs minus pairs with equal values |
| Look at the unknown | What shape does the answer have? | "Smallest capacity that works": feasibility only improves as capacity grows, so search the answer |
| Reduce | Is this a known problem in disguise? | "Are any two readings within d?" is "is min_gap(xs) <= d?" |

### Specialise with a script

For programmers, the strongest heuristic is to let the computer produce the small cases. You already have a brute force; run it for n = 1 to 20, print a table, guess the pattern, then prove it (or at least test the guess far beyond the cases you looked at).

The locker puzzle: n lockers start closed; on pass p (p = 1 to n) you toggle every p-th locker. How many are open at the end? The table of answers, 1, 1, 1, 2, 2, 2, 2, 2, 3, ..., steps up exactly at the perfect squares. Proof: locker i is toggled once for each divisor of i. Divisors pair up as d and i/d, except when d = i/d, which happens only when i is a perfect square. So squares are toggled an odd number of times and end open, and the answer is `isqrt(n)`.

### Reduce or design

MIT 6.006 frames algorithm design as two routes: **reduce** to a problem you know how to solve (sorting, searching, shortest paths), or **design** your own (brute force, decrease and conquer, divide and conquer, dynamic programming, greedy). A reduction is two mappings: turn your input into the known problem's input, and turn its answer back into yours. Check both.

## Cost

Each heuristic costs a few minutes; a table of small cases costs one brute force you already have. The locker brute force toggles n/1 + n/2 + ... + n/n times, about n ln n (the harmonic sum), so it is O(n log n). The insight replaces it with `math.isqrt(n)`, effectively O(1) for numbers of normal size.

## When to use it

After about 10 minutes on an easy problem (15 on a medium or hard) without a new idea, run the list before taking a hint. Specialise first when the input is a single number or the answer smells like a formula; reduce first when the statement is a long story; work backwards when the goal is clearer than the start (reaching a target, games). If you have a plan and it is merely failing tests, you are not stuck, you are debugging: go back to Test.

## Worked trace

Ten lockers. Specialising on n = 10 by hand shows which lockers survive (`o` is open):

```steps
Ten closed lockers. Pass p toggles lockers p, 2p, 3p, ...
    locker   1  2  3  4  5  6  7  8  9 10
    state    .  .  .  .  .  .  .  .  .  .
---
Pass 1 toggles every locker: all open
    locker   1  2  3  4  5  6  7  8  9 10
    state    {{o  o  o  o  o  o  o  o  o  o}}
---
Pass 2 toggles 2, 4, 6, 8, 10
    locker   1  2  3  4  5  6  7  8  9 10
    state    o  {{.}}  o  {{.}}  o  {{.}}  o  {{.}}  o  {{.}}
---
Pass 3 toggles 3, 6, 9
    locker   1  2  3  4  5  6  7  8  9 10
    state    o  .  {{.}}  .  o  {{o}}  o  .  {{.}}  .
---
Pass 4 toggles 4 and 8
    locker   1  2  3  4  5  6  7  8  9 10
    state    o  .  .  {{o}}  o  o  o  {{o}}  .  .
---
Passes 5 to 10 touch only a few lockers each. Final state: 1, 4 and 9 are open
    locker   1  2  3  4  5  6  7  8  9 10
    state    {{o}}  .  .  {{o}}  .  .  .  .  {{o}}  .
---
Specialise further with the brute force: open lockers for n = 1..20
    n      1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20
    open   1  1  1  {{2}}  2  2  2  2  {{3}}  3  3  3  3  3  3  {{4}}  4  4  4  4
    the count steps up at 1, 4, 9, 16: answer = isqrt(n)
```

## Template

```python
import math


def lockers_brute(n):
    """n closed lockers; pass p = 1..n toggles every p-th locker. How many end open?"""
    is_open = [False] * (n + 1)
    for p in range(1, n + 1):
        for i in range(p, n + 1, p):
            is_open[i] = not is_open[i]
    return sum(is_open)


def small_cases(f, ns):
    """Specialise: tabulate f on small inputs, then look for the pattern."""
    for n in ns:
        print(f"{n:>3}  {f(n)}")


small_cases(lockers_brute, range(1, 21))
# the answers step up at 1, 4, 9, 16, so guess isqrt(n), then test the guess far beyond the table
assert all(lockers_brute(n) == math.isqrt(n) for n in range(500))
```

## Pitfalls

- **Rereading instead of acting.** Rereading is not a heuristic. Write something new: a table, a drawing, a smaller problem.
- **Trusting a pattern from a few cases.** 1, 2, 4, 8, 16 looks like powers of two, but the number of regions formed by chords between n points on a circle goes 1, 2, 4, 8, 16, 31. Prove the pattern, or test it much further with the brute force.
- **A reduction that loses information.** Check that every input of your problem maps to a valid input of the known one and that the answer maps back.
- **Taking a hint too early, or too late.** Run the list first; past about 1.5 times your timebox, take the hint (next card).

## Check yourself

Q: Specialise: in a league where each of n teams plays every other team once, tabulate the number of games for n = 1 to 5 and give the formula.
A: 0, 1, 3, 6, 10, which is n(n-1)/2: each game is a pair of teams, the same count as the pairs brute force.

Q: Work backwards: with the moves +1 and x2, what is the fewest number of moves from 1 to 23, and which moves?
A: 7. Backwards from 23: odd, so 22; then 11; odd, so 10; then 5; odd, so 4; then 2; then 1. Forwards: 1, 2, 4, 5, 10, 11, 22, 23.

Q: Count the complement: how many pairs i < j in [2, 5, 2, 2, 5, 9] have *different* values?
A: 11. There are 6 x 5 / 2 = 15 pairs in total, and 4 pairs with equal values (three among the 2s, one among the 5s), so 15 - 4 = 11.

## Lab

- **169 Majority Element** (derive it): solve it three ways and note which heuristic produced each: counting every value by brute force (O(n^2)), a `Counter` (O(n) time, O(n) space), and the middle element after sorting (O(n log n)). Then specialise on tiny arrays to find an O(1)-space method: what happens if you repeatedly cross out two *different* values? Expected: [3, 7, 3, 3, 1, 3, 7] gives 3; the final version runs in O(n) time with O(1) extra space and agrees with the `Counter` version on 1,000 random arrays that have a majority.
- **1512 Number of Good Pairs**: specialise on a single value repeated c times for c = 1 to 5 and find the formula for the number of equal pairs. Expected: 0, 1, 3, 6, 10, so c(c - 1) / 2 per value; summing it over a `Counter` gives 4 for [2, 5, 2, 2, 5, 9].

> [!know]
> You now know how to get unstuck by specialising, simplifying, working backwards, changing the representation and reducing to a known problem.

=== primer | How should you use timeboxes, hints and solutions so practice sticks? | 12 min
goal: Run a practice session with a timebox, staged hints, honest statuses, a blank-file re-solve and a four-line journal entry
tag: method-practice | Timebox, hint, re-solve, journal
link: USACO Guide: Practicing, Reading Solutions | https://usaco.guide/general/practicing#reading-solutions | 10 min: the 'Reading Solutions' section, several competitors' advice on when to read an editorial and why to implement it afterwards
practice: 169, 1365

> [!key]
> Practice works when it is effortful, spaced and honest. **Timebox** each attempt (easy 15-20 minutes, medium 30-40, hard 50-60), take **one hint at a time** when the timebox runs out, and if you read a solution, close it and **re-implement it from a blank file**. Mark the problem honestly (Solved only if you wrote both the brute force and the optimal solution yourself), write a **four-line journal entry**, and solve it again from scratch days later: the second solve is where the learning sets.

## Intuition

Watching someone lift weights does not build your muscles, and rest days are part of training. Reading a solution feels like learning because it is fluent, the same illusion as rereading notes. Retrieval (writing it from a blank file) and spacing (coming back days later) are what last. Learning research is consistent here: practice testing and spreading practice over time are among the most effective study techniques, while rereading is among the weakest (Dunlosky and colleagues, 2013). In one study, spreading the same practice problems over two sessions clearly beat doing them in one, while tripling the number of problems in a single session made no measurable difference weeks later (Rohrer and Taylor, 2006).

## How it works

### The timebox and the hint ladder

- Set a timer and run the loop. A working brute force with no optimisation yet is real progress.
- When the timebox runs out, spend five minutes on the stuck list. Still nothing? Open **hint 1** (What to notice). Give each hint about five minutes of real effort before opening the next: **hint 2** (A nudge), then **hint 3** (Key insight). Every practice problem on this page has these three buttons.
- After hint 3, write the solution yourself. If you still cannot, read a written solution one paragraph at a time and stop as soon as you have the next idea.
- In learning mode allow up to 1.5 times the timebox; beyond that, the next hint teaches more than more staring.

### Honest statuses

| Status | Meaning on this page | What happens next |
|---|---|---|
| **Solved** | you wrote the brute force and the optimal solution yourself (hint 1 at most), tested them, and can state the cost and why it works | re-solve from your journal schedule |
| **Brute only** | a correct but slow solution, or you needed hint 2 | returns in Today's session after three days |
| **Stuck** | you needed hint 3 or a written solution | returns in Today's session after three days |

### Read solutions for the idea, then rebuild

Read for the cue and the invariant, not the code. Then close it, wait a few minutes, write it from a blank file and test it against your brute force. If you cannot, you have not got it yet: reread only the part you lost.

### The four-line journal

1. **Cue:** what in the statement pointed to the approach.
2. **Insight:** the decisive idea and why it works, in one sentence.
3. **Slip:** the bug or wrong turn, and the test that caught it.
4. **Links:** related problems, and the next re-solve date.

### Spaced re-solving

Re-solve after about 3 days, 1 week, 3 weeks and 2 months. A clean re-solve from a blank file moves the problem up a rung; a failure sends it back to 3 days.

## Cost

A 45-minute session: 5 minutes re-solving something due, 30 minutes on one new problem with the full loop, 10 minutes comparing with a reference and writing the journal. That is one or two new problems per session, and never more than three of the same technique in a day: extra same-day repetitions add little, spacing adds a lot.

## When to use it

In every practice session, and most of all on medium and hard problems, where an hour disappears easily. In the last weeks before interviews, switch to strict timeboxes with no hints, as in a mock. Reading a primer for the first time is study, not practice; timebox the problems, not the reading.

## Worked trace

A 45-minute session with 1365 as the new problem:

```steps
0:00 Warm-up: 1512 is due today (Brute only, three days ago)
    blank file, no notes: brute force, then the Counter version
    {{clean re-solve in 8 minutes: now Solved}}
---
0:08 New problem 1365, easy: timebox 20 minutes. Run the loop
    restate: count j != i with nums[j] < nums[i], strictly
    example: [6, 1, 6, 0, 3] -> [3, 1, 3, 0, 2]
    {{brute force: O(n^2), fine for n <= 500}}
---
0:15 Optimise: values only 0..100, but how do counts give "smaller than"?
    five minutes on the stuck list: specialise on [2, 2, 1]...
    {{no idea yet: open hint 1}}
---
0:25 Hint 1 points at the value range; you see it yourself
    smaller_than[v] = count[0] + count[1] + ... + count[v - 1]
    {{write it, test against the brute force on 1,000 lists}}
---
0:33 Status: both versions written by you, hint 1 only
    {{Solved}}; re-solve in a week
---
0:35 Journal, four lines
    cue:     values only 0..100; n small
    insight: count each value; smaller-than-v = counts below v
    slip:    used <= at first; [5, 5] caught it (want [0, 0])
    links:   1512; re-solve on day 7
```

## Template

A helper that formats the journal entry and its re-solve date:

```python
from datetime import date, timedelta

RESOLVE_AFTER = {"Brute only": [3], "Stuck": [3], "Solved": [7, 21, 60]}   # days


def journal_entry(problem, status, cue, insight, slip, links, today, rung=0):
    """Four lines plus the next re-solve date. rung counts clean re-solves so far."""
    gaps = RESOLVE_AFTER[status]
    due = today + timedelta(days=gaps[min(rung, len(gaps) - 1)])
    return "\n".join([
        f"{problem} [{status}] re-solve on {due.isoformat()}",
        f"  cue:     {cue}",
        f"  insight: {insight}",
        f"  slip:    {slip}",
        f"  links:   {links}",
    ])


print(journal_entry(
    "1365 How Many Numbers Are Smaller", "Solved",
    cue="values only 0..100; n small",
    insight="count each value; smaller-than-v = sum of counts below v",
    slip="used <= at first; [5, 5] caught it (want [0, 0])",
    links="1512, counting sort",
    today=date(2026, 11, 1)))
```

## Pitfalls

- **Reading the solution after five minutes.** You skip the struggle that makes the idea stick, and you never learn whether you would have found it.
- **Grinding for two hours.** Past 1.5 times the timebox, take the next hint.
- **Marking Solved because the judge accepted code you wrote after reading the editorial.** Statuses schedule your reviews; dishonest ones schedule the wrong ones.
- **Re-solving from memory of the code.** If you cannot state the insight in one sentence, you memorised characters, not the idea.
- **Ten problems of one technique in a day.** Mix techniques and spread them out instead.

## Check yourself

Q: You solved a medium in 50 minutes after hint 2, then read the official solution, which was cleaner. Which status, and what do you do in the next ten minutes?
A: Brute only, because you needed hint 2. Close the official solution, re-implement the cleaner idea from a blank file, test it against your brute force and write the journal entry. It returns in Today's session after three days.

Q: Why does one blank-file re-solve a week later teach more than three new problems of the same type today?
A: Retrieving the idea after a delay strengthens both the memory and the cue that triggers it, while same-day repetitions feel productive but add little lasting retention. A problem met cold also tests recognition, which the module label gives away when you practise a block of similar problems.

Q: Write the journal "insight" line for `min_gap` from the first card.
A: "Sorting makes closeness local: for a <= b <= c, c - a >= b - a, so only neighbours in sorted order can be the closest pair." One sentence with the idea and the reason.

## Lab

- **169 Majority Element**: run a full timed session: 20-minute timebox, hints one at a time, an honest status and a four-line journal entry with its re-solve date. Expected: [3, 7, 3, 3, 1, 3, 7] gives 3; your entry names the cue ("appears more than n/2 times"), and Solved requires both your brute force and your own O(n) solution.
- **1365 How Many Numbers Are Smaller Than the Current Number**: if you solved it earlier, re-solve it now from a blank file without opening your old code. Expected: [6, 1, 6, 0, 3] gives [3, 1, 3, 0, 2] within 10 minutes; if not, mark it Brute only and log the slip.

> [!know]
> You now know how to timebox, take hints one at a time, mark progress honestly and schedule blank-file re-solves.

=== lab | Maximum subarray: from O(n^3) to O(n) | 50 min
goal: Take one problem through the whole loop: three versions, a stress test against each other, doubling timings and a journal entry
link: Competitive Programmer's Handbook, section 2.4 | https://cses.fi/book/book.pdf#page=31 | 15 min: 'Maximum subarray sum' (book pages 21-24, starting halfway down the page), the same three algorithms in C++ with an efficiency comparison table; note that it allows the empty subarray

You will solve a classic with the full solving loop: *given a non-empty list of integers, return the largest sum of a contiguous, non-empty block.* You will write three versions, each removing one repeated computation, check them against each other on random inputs, and time them as n doubles.

## Setup

- Python 3.10 or later; no packages.
- A file `maxsub_lab.py` in a practice folder.

## Steps

1. **Restate and examples.** Write the contract as a comment: non-empty input, non-empty block, any integers. Solve by hand: [2, -3, 4, -1, 2, -5, 3] gives 5 (the block 4, -1, 2); [-2, -5] gives -2 (the block must be non-empty, so the best is one element); [7] gives 7.
2. **Save the three versions and the harness** below as `maxsub_lab.py`.

```python
import random
import time


def max_sub_cubic(a):
    """Try every block a[i:j] and add it up from scratch: O(n^3)."""
    best = a[0]
    for i in range(len(a)):
        for j in range(i + 1, len(a) + 1):
            s = 0
            for k in range(i, j):
                s += a[k]
            best = max(best, s)
    return best


def max_sub_quadratic(a):
    """Extend the sum of a[i:j] by one item to get a[i:j+1]: O(n^2)."""
    best = a[0]
    for i in range(len(a)):
        s = 0
        for j in range(i, len(a)):
            s += a[j]
            best = max(best, s)
    return best


def max_sub_linear(a):
    """Kadane: cur is the best sum of a block that ends at the current item: O(n)."""
    best = cur = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def stress(fast_versions, trials=3000, seed=1):
    rng = random.Random(seed)
    for _ in range(trials):
        a = [rng.randint(-6, 6) for _ in range(rng.randint(1, 9))]
        want = max_sub_cubic(a)
        for f in fast_versions:
            if f(a) != want:
                print(f"MISMATCH in {f.__name__}: a = {a}, expected {want}, got {f(a)}")
                return False
    print(f"OK: {trials} random arrays, all versions agree")
    return True


def doubling(f, sizes, seed=2):
    rng = random.Random(seed)
    prev = None
    for n in sizes:
        a = [rng.randint(-100, 100) for _ in range(n)]
        t = float("inf")
        for _ in range(3):                      # best of three runs filters out noise
            t0 = time.perf_counter()
            f(a)
            t = min(t, time.perf_counter() - t0)
        ratio = f"x{t / prev:.1f}" if prev else ""
        print(f"{f.__name__:18} n = {n:>9,}  {t:8.4f} s  {ratio}")
        prev = t


if __name__ == "__main__":
    stress([max_sub_quadratic, max_sub_linear])
    doubling(max_sub_cubic, [50, 100, 200, 400])
    doubling(max_sub_quadratic, [400, 800, 1_600, 3_200])
    doubling(max_sub_linear, [125_000, 250_000, 500_000, 1_000_000])
```

3. **Run it** with `python maxsub_lab.py` (about 30 seconds) and copy the timings into a table.
4. **Explain each removal in one sentence.** Cubic to quadratic: the inner `k` loop recomputes the sum of a[i:j] although the sum of a[i:j-1] was computed one step earlier, so keep a running sum. Quadratic to linear: the best block ending at position j is either a[j] alone or a[j] added to the best block ending at j - 1, so one running value per position is enough.
5. **Prove the linear step.** Show that an optimal block never starts with a prefix whose sum is negative: if it did, dropping that prefix would give a larger sum, a contradiction. That is why `cur` restarts at x when `cur + x < x`, that is, when the old `cur` is negative.
6. **Plant a bug and watch the oracle catch it.** In `max_sub_linear`, start from `best = cur = 0` and loop over all of `a`. Rerun, read the mismatch, then undo the change.
7. **Extrapolate.** From your timings, estimate each version at n = 10^5 by scaling with n^3, n^2 and n.
8. **Look back.** Write the four-line journal entry: cue ("best contiguous block"), insight (best block ending here is x or x plus the best ending just before), slip (the planted bug or your own), links (prefix sums, the dynamic programming module).

This stage ends with a project that packages a stress harness and a doubling benchmark like these into a reusable kit called dsakit.

## What you should see

- `OK: 3000 random arrays, all versions agree`.
- Doubling ratios near 8 for the cubic version, 4 for the quadratic and 2 for the linear. Timings on a busy machine are noisy: across several runs on a shared workstation, individual ratios ranged from about 6 to 14, 3 to 6 and 1.5 to 3, which is why the harness takes the best of three runs.
- Rough absolute times on a recent CPU: about 1 second for the cubic version at n = 400, 2 to 3 seconds for the quadratic at n = 3,200, under a second for the linear at n = 10^6.
- Extrapolated to n = 10^5: the cubic version needs about 250^3 times its n = 400 time, around six months; the quadratic about 1,000 times its n = 3,200 time, roughly 40 minutes; the linear version under a tenth of a second.
- The planted bug is caught immediately: `MISMATCH in max_sub_linear: a = [-2, -5], expected -2, got 0`. An all-negative array is exactly the edge case the contract's "non-empty" rule creates.

## Check yourself

Q: Why does Kadane's update use `cur = max(x, cur + x)` rather than `cur = max(0, cur + x)`?
A: The block must be non-empty. `max(0, ...)` allows the empty block with sum 0, which is wrong when every value is negative (it returns 0 instead of the largest element). Restarting at x keeps at least one element in the block.

Q: Your cubic timings doubled by about 10 between n = 200 and 400 rather than 8. Is the analysis wrong?
A: No. The cubic version does about n^3/6 inner steps, so the ratio tends to 8, but single measurements on a shared machine are noisy and small sizes include fixed overheads. Repeat the runs, take the best of several, or use larger sizes before doubting the exponent.

> [!know]
> You now know how to take one problem from a brute force to an optimal solution, with an oracle and timings to back every step.

=== practice
- 1929 core
  cue: The output is the input written out twice, one copy after the other.
  hint: Write down what ans[i] and ans[i + n] must be for each i, then look for a one-line way to build that list.
  insight: ans[i] = ans[i + n] = nums[i], so the answer is the list concatenated with itself; `nums + nums` builds it in one C-level copy. Writing the contract first is the whole solution here.
  cost: O(n) time, O(n) space for the output
  pattern: method-restate
- 1480 core
  cue: Each output value is the sum of everything up to and including that position.
  hint: The brute force recomputes a sum from the start for every position. What does the answer at i share with the answer at i - 1?
  insight: out[i] = out[i - 1] + nums[i], so one running total replaces the inner loop and each value is computed in O(1) from the previous one; itertools.accumulate does exactly this.
  cost: O(n) time, O(1) extra space beyond the output
  pattern: method-loop
- 1512 core
  cue: You must count pairs of positions that hold equal values.
  hint: The brute force checks every pair. For a new element, how many good pairs does it complete with the elements before it?
  insight: Scanning left to right, an element completes one good pair with every earlier equal element, so add count[x] before incrementing count[x]; equivalently each value seen c times contributes c(c - 1)/2 pairs.
  cost: O(n) time, O(n) space (or O(101) with a fixed array, since values are at most 100)
  pattern: method-bottleneck
- 1365 core
  cue: For each element, count how many others are strictly smaller, and the values are tiny (0 to 100).
  hint: With n at most 500 the O(n^2) brute force passes. For a version that scales, what could you precompute about every possible value once?
  insight: Count how often each value 0..100 occurs, then a running sum gives smaller[v] = count[0] + ... + count[v - 1]; each answer is a lookup. Sorting a copy and taking each value's first index (bisect_left) gives the same in O(n log n).
  cost: O(n + 101) time, O(101) extra space
  pattern: method-budget
- 1913 core
  cue: Choose four different positions to make (a x b) - (c x d) as large as possible, with all values positive.
  hint: Brute-force small arrays and look at which four values win. How would you make one product as large as possible and the other as small as possible?
  insight: With positive values the first product is largest for the two largest numbers and the second smallest for the two smallest, and these four positions are distinct when n >= 4; sort and use the ends, or track the top two and bottom two in one pass.
  cost: O(n) time and O(1) extra space with four tracked values (O(n log n) with sorting)
  pattern: method-brute
- 169 derive
  cue: One value occupies more than half of the positions, and the follow-up asks for O(1) extra space.
  hint: A Counter or a sort works; for O(1) space, imagine repeatedly crossing out two different values. What must be left at the end?
  insight: Boyer-Moore voting: keep a candidate and a counter; a matching value adds 1, a different one subtracts 1, and at 0 the next value becomes the candidate. Each decrement cancels two different values, so it removes at most one copy of the majority; the majority has more copies than all other values together, so it can never be cancelled out and is the final candidate.
  cost: O(n) time, O(1) extra space
  pattern: method-stuck
