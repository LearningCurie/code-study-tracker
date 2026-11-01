---
key: derive
name: Deriving solutions to unfamiliar problems
stage: mastery
summary: Invent a solution you have never seen with small cases, the optimisation ladder, reductions, new representations and the right state; know when to stop; then explain it, work against the clock and learn from what failed.
why: Recognition only helps when a problem resembles one you know. Interviews, contests and real work keep producing problems that do not: a familiar idea with one twist, or constraints that rule out every template. Strong problem solvers do not remember more solutions; they own a small set of moves for generating one (make it small and look for a pattern, find the repeated work in a brute force, reduce to a known problem, change the representation, invent the state) and they can tell when a solution cannot be improved. Each card here works one move end to end on real problems from the bank, dead ends included, and the last cards turn a derivation into a result: explaining it in a minute, working against a clock and learning from an attempt that failed. Engineers use the same moves daily, from profiling and removing the hot loop to noticing that a build order is a topological sort.
outcomes:
- Brute-force small cases, spot a pattern in the table and prove it before trusting it
- Climb from a brute force to an optimal solution one standard fix at a time, keeping each old version as a test oracle
- Recognise a known problem behind an unfamiliar story and check that the translation is exact in both directions
- Change the representation (complement, sort, graph, rewrite the formula) when the direct view only gives a brute force
- Invent the smallest state a scan or DP must remember, and test it with "same state, same future"
- Argue lower bounds from the input, the output and comparison sorting, and stop optimising at the right point
- Explain a solution in about a minute, run timed sessions, and turn a failed attempt into a card that transfers
cues:
- The pattern atlas offers no row, or two rows that both fit badly
- Your brute force is correct but the constraints are far beyond it
- A familiar problem with one constraint changed: negative values, a much larger n, a second dimension
- The answer is a single number that depends on n, with n up to 10^9 or more
- Someone asks "can you do better?" and you do not know whether you can
traps:
- Trusting a pattern from small cases without proving it
- Applying two optimisations at once and losing track of which one broke the code
- Reducing to a problem that is harder than the original, such as a general NP-hard problem instead of a special case
- A state that is too small: the code passes the examples and fails when two histories need different futures
- Optimising past the point where the constraints are already met
systems:
- Performance work follows the optimisation ladder: profile, find the repeated work, apply one standard fix (a cache, an index, batching), measure again
- openSUSE's zypper and Fedora's DNF hand dependency resolution to libsolv, which reduces it to a satisfiability problem and solves it with a SAT solver
- PostgreSQL's planner picks a join order with the near-exhaustive dynamic-programming search introduced by IBM's System R, and switches to a genetic search (GEQO) for queries with 12 or more FROM items by default
- Incident reviews ask the same question as a failed-attempt post-mortem: which step failed, and which check would have caught it
further:
- Chapter · 60 min | Erickson, Algorithms ch. 3: Dynamic programming, from "Smart Recursion" on (PDF page 9) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=9
- Article · 15 min | Pólya's How to Solve It: the four phases and the heuristics dictionary | https://en.wikipedia.org/wiki/How_to_Solve_It#Heuristics_dictionary
- Chapter · 30 min | Competitive Programmer's Handbook ch. 5: Complete search, pruning and meet in the middle (PDF pages 57-66) | https://cses.fi/book/book.pdf#page=57
---

=== primer | How do small cases reveal a pattern you can then prove? | 15 min
goal: Brute-force a problem for n = 1..20, print the answers, spot a pattern, and prove it before you rely on it
tag: derive-small-cases | Small cases first
link: OEIS A001227: number of odd divisors of n | https://oeis.org/A001227 | 2 min: the definition and the first comment, which says this sequence counts the ways to write n as a sum of consecutive positive integers; search OEIS whenever your table of small answers looks unfamiliar
link: Wikipedia: How to Solve It, "Heuristics dictionary" | https://en.wikipedia.org/wiki/How_to_Solve_It#Heuristics_dictionary | 5 min: Pólya's list of heuristics; this card uses "specialisation" and "induction"

> [!key]
> When no technique comes to mind, make the problem small: write the simplest correct program, run it for n = 1..20 and look at the table. A pattern in the numbers (powers of two, divisor counts, always the same answer, Fibonacci-like growth) is a **hypothesis**, not an answer. Prove it with an argument that explains why it holds, then implement the fast version and stress-test it against the brute force you already have.

## Intuition

You cannot see the shape of a curve from one point, but twenty points usually show it. Mathematicians work this way all the time: compute small cases, guess, prove. The brute force costs a few minutes, it is needed later as a test oracle anyway, and it turns "I have no idea" into "I have a table and a question about it".

## How it works

### The loop

1. Write a brute force that is obviously correct, however slow.
2. Print a table for n = 1..20 (or for all small inputs).
3. Look for structure: special values (primes, powers of two), differences and ratios between neighbours, factorisations, or an OEIS search.
4. State a hypothesis and **prove** it. If no proof comes, test it on larger n before investing more.
5. Implement the fast version and stress-test it against the brute force.

### Worked derivation: 829 Consecutive Numbers Sum

*Count the ways to write n as a sum of one or more consecutive positive integers, for n up to 10^9.*

**Constraints first.** n can be 10^9, so even one loop up to n (about 100 seconds in Python) is out. The answer must come from something like O(sqrt n).

**Brute force.** Try every starting number and add consecutive integers until the total reaches or passes n. Fine for n up to a few thousand, hopeless at 10^9, and exactly what we need for a table:

```text
n    :  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20
ways :  1  1  2  1  2  2  2  1  3  2  2  2  2  2  4  1  2  3  2  2
```

**Look.** The powers of two (1, 2, 4, 8, 16) all give 1. The odd primes (3, 5, 7, 11, 13, 17, 19) all give 2. 9 gives 3 and 15 gives 4. What do 9 and 15 have that 3 and 5 lack? More divisors: 15 has 1, 3, 5, 15. But 12 has six divisors and only 2 ways, while its **odd** divisors are 1 and 3. Hypothesis: the answer is the number of odd divisors of n. It fits every column (18 has odd divisors 1, 3, 9: three ways), and OEIS confirms that A001227 is both sequences.

**Prove.** A run of k numbers starting at a >= 1 sums to k·a + k(k - 1)/2, so 2n = k·(2a + k - 1). The two factors differ by 2a - 1, an odd number, so one is odd and the other even, and the second is the larger because a >= 1. Conversely, take any odd divisor d of n and write 2n = d · (2n/d): one factor is odd, the other even. Let k be the smaller one and 2a + k - 1 the larger; then a = (larger - smaller + 1)/2 is a positive whole number. So runs and odd divisors match one to one, and the answer is the number of odd divisors.

**Fast version.** Strip the factors of 2, then count divisors by trial division up to the square root: about 3·10^4 steps for n = 10^9.

### A second one, briefly: 877 Stone Game

Two players take whole piles from either end of a row with an even number of piles and an odd total; does the first player win with best play? A minimax brute force (best score difference for the player to move on piles i..j) on 3,000 random games answered **True** every time. Hypothesis: the first player always wins. Proof: number the piles from 0. On each of her turns the row has even length, so its two ends have different parities, and she can always take the end with the parity she chose; then both ends left for her opponent have the other parity. So she can take every even-indexed pile, or every odd-indexed pile. The total is odd, so one of those two sums is strictly larger; she picks that parity. The answer is `return True`, O(1).

## Cost

For 829, the brute force for the whole table up to 3,000 runs in well under a second; the final solution is O(sqrt n) time and O(1) space. The method itself costs ten to fifteen minutes: a brute force, a table and some staring, which is cheap next to an hour of guessing at formulas.

## When to use it

- The answer is one number that depends on a few parameters (n, k), especially when n can be 10^9 or 10^18 and no array is given.
- Games, counting problems and "for which n is this possible?" questions.
- Not when the input is a large arbitrary array: there is no pattern over n to find. There the same habit becomes exhaustive testing on all small arrays, which finds bugs rather than formulas.

## Worked trace

The derivation of 829, one decision at a time.

```steps
Constraints: n up to 10^9, so no loop to n; aim for about O(sqrt n)
    target: {{O(sqrt n)}} or better
---
Brute force for n = 1..20 prints a table
    n    1 2 3 4 5 6 7 8 9 ... 15 16
    ways 1 1 2 1 2 2 2 1 3 ...  4  1
---
Special values: powers of two give {{1}}, odd primes give {{2}}
    1 2 4 8 16 -> 1        3 5 7 11 13 -> 2
---
Composites: 9 -> 3 and 15 -> 4, but 12 -> 2 despite six divisors
    odd divisors: 9: 1 3 9    15: 1 3 5 15    12: {{1 3}}
---
Hypothesis: ways(n) = number of {{odd divisors}} of n; it fits all twenty columns
---
Proof: 2n = k(2a + k - 1) with factors of {{opposite parity}}; each odd divisor gives one run
---
Implement in O(sqrt n), stress-test against the brute force up to 3,000 and on random n up to 10^9
    all agree
```

## Template

```python
def ways_brute(n):
    """Count runs of consecutive positive integers summing to n, by trying every start."""
    count = 0
    for start in range(1, n + 1):
        total, x = 0, start
        while total < n:
            total += x
            x += 1
        count += total == n
    return count


def odd_divisors(n):
    """829 Consecutive Numbers Sum: the number of odd divisors of n. O(sqrt n)."""
    while n % 2 == 0:
        n //= 2
    count, d = 0, 1
    while d * d <= n:
        if n % d == 0:
            count += 1 if d * d == n else 2
        d += 1
    return count


print("n    :", " ".join(f"{n:2}" for n in range(1, 21)))
print("ways :", " ".join(f"{ways_brute(n):2}" for n in range(1, 21)))
for n in range(1, 3000):                       # the brute force stays as the oracle
    assert ways_brute(n) == odd_divisors(n), n
```

## Pitfalls

- **Believing a pattern without proof.** Put points on a circle and join every pair: the regions number 1, 2, 4, 8, 16, and then 31, not 32. Five matching terms proved nothing.
- **A buggy brute force.** A wrong table produces a confident wrong pattern. Check the brute force against the statement's examples before you study its output.
- **Too few cases.** Print at least fifteen or twenty values; the special cases (squares, powers of two, primes) need room to show up.
- **Shifted indexing.** If your table starts at n = 0 and OEIS starts at n = 1, the search fails; try both offsets.

## Check yourself

Q: Using the rule, how many ways are there for n = 45 and for n = 64? List the ways for 45.
A: 45 = 3^2 · 5 has (2 + 1)(1 + 1) = 6 odd divisors, so 6 ways: 45, 22 + 23, 14 + 15 + 16, 7 + 8 + 9 + 10 + 11, 5 + 6 + 7 + 8 + 9 + 10, and 1 + 2 + ... + 9. 64 is a power of two, so its only odd divisor is 1: just 64 itself.

Q: In the proof, why must k and 2a + k - 1 have opposite parity, and why does that matter?
A: They differ by 2a - 1, which is odd, so exactly one of them is even. That is what lets each odd divisor d of n produce exactly one run: in 2n = d · (2n/d) all the factors of 2 sit in one factor, so the odd/even split is forced and gives a unique k and a.

Q: Your brute force for 877 said True on 3,000 random games. Why is that not enough to submit `return True` with confidence, and what made it safe?
A: Random games can miss rare inputs where the pattern fails, so the table is only evidence. The parity argument made it safe: the first player can force taking all even-indexed or all odd-indexed piles, and with an odd total one of those sums is strictly larger, so she wins on every input.

## Lab

Both exercises use bank problems; do them without looking anything up, then check against the expected results.

- **343 Integer Break.** Split n into at least two positive integers to maximise their product. Brute-force n = 2..15 and find the rule before proving it. Expected table for n = 2..15: 1, 2, 4, 6, 9, 12, 18, 27, 36, 54, 81, 108, 162, 243 (so n = 10 gives 36); the rule is "use as many 3s as possible, but finish with a 4 (2 + 2) instead of 3 + 1".
- **561 Array Partition.** Pair up 2n numbers to maximise the sum of the pair minimums. Brute-force every pairing for small arrays and spot the rule. Expected: 3 for `[3, 1, 2, 2]`, 3 for `[5, -1, 4, 0]`, 9 for `[1, 2, 3, 4, 5, 6]`; the rule is "sort, then add every second element starting from the smallest".

> [!know]
> You now know how to turn a blank page into a table of small answers, and a table into a proved formula.

=== primer | How do you climb from a brute force to an optimal solution one fix at a time? | 16 min
goal: Find the repeated work in a brute force, apply the matching standard fix, re-test and re-measure, and repeat until the cost meets the constraints
tag: derive-ladder | The optimisation ladder
link: Tech Interview Handbook: Coding interview techniques, "How to optimize time complexity" | https://www.techinterviewhandbook.org/coding-interview-techniques/#how-to-optimize-time-complexity | 8 min: the four steps, especially "Identify overlapping and repeated computation" and "Try different data structures"
link: Competitive Programmer's Handbook, sections 2.3 and 2.4 | https://cses.fi/book/book.pdf#page=31 | 10 min: PDF pages 31-33, "Estimating efficiency" and "Maximum subarray sum", the classic climb from O(n^3) to O(n^2) to O(n)

> [!key]
> Start from a brute force that is obviously correct, then ask one question at a time: **what is this code computing more than once?** Each kind of repeated work has a standard fix: recomputing a range from scratch becomes a running value, restarting at every left end becomes a window, scanning a list becomes a hash lookup or a binary search, repeated calls become memoisation, and repeated maxima over a sliding range become a monotonic deque. Apply one fix, keep the previous version as the test oracle, measure, and climb again.

## Intuition

A slow program is like a leaky house: you do not rebuild it, you find the biggest leak, fix it, and check again. Each rung of the ladder removes one kind of waste, and because the slower version still exists, every rung is tested against the one below it. The final solution may look clever, but it was reached by steps that were each routine.

## How it works

### The menu of repeated work

| Repeated work you see | Standard fix | Where it is taught |
|---|---|---|
| A range's sum, min or max recomputed from scratch as the range grows | Carry it in a running variable | Prefix sums and difference arrays |
| An inner loop restarted at every left end although validity is monotone | Sliding window or two pointers | Sliding window |
| Scanning a list for a value | A set or dict, or sort plus binary search | Hash tables; Binary search |
| The same recursive call made again and again | Memoise, then build a table | Dynamic programming |
| The minimum or maximum of a changing collection | Heap, or a monotonic deque for a sliding range | Heaps; Monotonic stacks and queues |
| Trying every candidate answer although "works" only flips once | Binary search on the answer | Binary search and searching the answer |

### Worked derivation: 1438 Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit

*Find the length of the longest subarray in which every two elements differ by at most limit; n up to 10^5.*

**Restate.** "Every pair differs by at most limit" is the same as max - min <= limit. **Target:** n = 10^5 means O(n log n) or better.

**Rung 0, O(n^3).** For every pair (i, j), compute max and min of nums[i..j] from scratch. Correct, and it becomes the oracle.

**Rung 1, O(n^2).** Repeated work: for a fixed i, the max of nums[i..j] is recomputed for every j although it changes by at most one element. Fix: carry `hi` and `lo` as j grows. A second observation helps too: once [i, j] is invalid, every longer [i, j'] is invalid (the max can only rise and the min only fall), so break at the first violation. Measured on one run: 0.6 s at n = 1,000 and 2.2 s at n = 2,000 in the worst case; doubling n quadrupled the time, so n = 10^5 would take about an hour and a half.

**Rung 2, the window.** Repeated work: the loop restarts at every i, but validity is monotone (a sub-range of a valid range is valid), so the best window ending at j starts no earlier than the best window ending at j - 1. Fix: a sliding window with both ends moving forwards only. New obstacle: when the left end moves, the maximum might leave the window, and a running max cannot "un-max".

**A dead end and two ways out.** Recomputing the max on every shrink is rung 1 again. A sorted container (`SortedList`) or two heaps with lazy deletion give O(n log n), which already meets the target.

**Rung 3, O(n).** Keep two monotonic deques of indices: `maxq` with decreasing values (its front is the window's max) and `minq` with increasing values (its front is the min). An index that a later, larger value has overtaken can never be the max again, so it is popped from the back. When the left end passes the index at a front, pop it from the front. Every index enters and leaves each deque at most once.

## Cost

Rung 0 is O(n^3); rung 1 is O(n^2) time and O(1) space; the sorted-container version is O(n log n); rung 3 is O(n) time and O(n) space. The O(n) bound is amortised: each index is appended to each deque once and popped at most once, so all the inner `while` loops together run at most 4n times. On one run, rung 3 took 0.14 s at n = 10^5.

## When to use it

Use the ladder whenever you have a correct brute force and the target from the constraints is not yet met. Name the repeated work in a sentence before choosing a fix. If two rungs in you cannot name any repeated work, the problem probably needs a different kind of idea: a reduction, a new representation or a new state (the next cards).

## Worked trace

Rung 3 on `nums = [10, 1, 2, 4, 7, 2]`, limit 5. The deques are shown as values.

```steps
right = 0, x = 10: both deques hold 10; window [0, 0], best = 1
    maxq [10]   minq [10]   left = 0   best = 1
---
right = 1, x = 1: maxq keeps 10 (larger), minq drops 10; 10 - 1 > 5, so left = 1 and 10 leaves maxq
    maxq [{{1}}]   minq [{{1}}]   left = {{1}}   best = 1
---
right = 2, x = 2: 2 pops 1 from maxq; minq keeps 1; 2 - 1 <= 5
    maxq [2]   minq [1, {{2}}]   left = 1   best = {{2}}
---
right = 3, x = 4: maxq [4]; minq [1, 2, 4]; 4 - 1 <= 5
    maxq [{{4}}]   minq [1, 2, 4]   left = 1   best = {{3}}
---
right = 4, x = 7: 7 - 1 > 5, so left = 2 and the 1 leaves the front of minq
    maxq [7]   minq [{{2}}, 4, 7]   left = {{2}}   best = 3
---
right = 5, x = 2: maxq [7, 2]; the new 2 pops 7, 4 and the old 2 from minq; 7 - 2 <= 5
    maxq [7, 2]   minq [{{2}}]   left = 2   best = {{4}}  (2, 4, 7, 2)
```

## Template

```python
from collections import deque


def rung1(nums, limit):
    """O(n^2): extend j while carrying the running max and min; stop at the first violation."""
    n, best = len(nums), 0
    for i in range(n):
        hi = lo = nums[i]
        for j in range(i, n):
            hi, lo = max(hi, nums[j]), min(lo, nums[j])
            if hi - lo > limit:
                break
            best = max(best, j - i + 1)
    return best


def longest_subarray(nums, limit):
    """O(n): sliding window; maxq and minq hold indices whose values decrease and increase."""
    maxq, minq = deque(), deque()
    left = best = 0
    for right, x in enumerate(nums):
        while maxq and nums[maxq[-1]] <= x:
            maxq.pop()
        maxq.append(right)
        while minq and nums[minq[-1]] >= x:
            minq.pop()
        minq.append(right)
        while nums[maxq[0]] - nums[minq[0]] > limit:
            left += 1
            if maxq[0] < left:
                maxq.popleft()
            if minq[0] < left:
                minq.popleft()
        best = max(best, right - left + 1)
    return best


import random
for _ in range(3000):                          # each rung is tested against the one below it
    nums = [random.randint(1, 12) for _ in range(random.randint(1, 12))]
    limit = random.randint(0, 8)
    assert rung1(nums, limit) == longest_subarray(nums, limit)
```

## Pitfalls

- **Two fixes at once.** If the code breaks you will not know which fix did it. One rung, one test run.
- **Throwing the brute force away.** It is the only thing that can tell you the clever version is wrong on input 4,817.
- **Optimising the wrong part.** Measure, or at least count: a fix to an O(n) setup does nothing for an O(n^2) main loop.
- **Stale deque fronts.** If the left end moves without popping fronts whose index is now outside the window, the deque reports a max or min that is no longer there and the window shrinks too far.

## Check yourself

Q: Why may rung 1 stop the inner loop at the first violation instead of checking every longer subarray?
A: Extending a subarray can only raise its maximum or lower its minimum, so max - min never decreases as j grows. Once it exceeds the limit, every longer subarray starting at i is invalid too.

Q: In the trace, why does the 2 at index 5 remove the 2 at index 2 from `minq`, although they are equal?
A: For the minimum, an earlier value that is not smaller than a later one can never be needed again: the later one stays in the window at least as long and is at least as small. Popping equal values keeps the deque short; keeping them would also be correct.

Q: Name the repeated work and the fix: "answer 10^5 queries, each asking for the sum of nums[l..r], on an array that never changes".
A: Each query re-adds a range that overlaps the others; precompute prefix sums once in O(n), then each query is pre[r + 1] - pre[l] in O(1).

## Lab

- **1052 Grumpy Bookstore Owner (bank).** Write the brute force that tries every placement of the calm period and recounts everything (O(n · minutes)), name the repeated work, and climb to O(n). Expected: 10 for `customers = [4, 0, 3, 2, 5, 1], grumpy = [1, 0, 1, 1, 0, 1], minutes = 2`.
- **2090 K Radius Subarray Averages (bank).** Climb from O(n · k) to O(n). Expected: `[-1, 3, 5, 7, -1]` for `[1, 3, 5, 7, 9], k = 1`, and `[-1, -1]` for `[2, 4], k = 1`.

> [!know]
> You now know how to climb from a brute force to the target complexity one tested fix at a time.

=== primer | How do you spot that a new problem is a known one in disguise? | 15 min
goal: Translate an unfamiliar statement into a known problem (a sequence DP after sorting, shortest paths, interval scheduling, two-colouring, knapsack) and check that the translation keeps every constraint
tag: derive-reduce | Reductions
link: Jeff Erickson, Algorithms, chapter 1 "Recursion" (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/01-recursion.pdf | 5 min: PDF page 1, the section "Reductions": solving one problem by using an algorithm for another as a black box
link: CodePath: UMPIRE interview strategy, "Match" | https://guides.codepath.org/compsci/UMPIRE-Interview-Strategy#match | 3 min: the Match step and its list of problem categories to compare against

> [!key]
> Most "new" problems are old ones in a costume. Strip the story, write down the objects (items, people, states) and the rule that relates them, and compare against a short catalogue of targets: an increasing subsequence after sorting, shortest paths, interval scheduling, two-colouring, knapsack, topological order. Then check the translation **in both directions**: every solution of your problem must map to a solution of the known one, and back, or the known algorithm answers a different question.

## Intuition

A sat-nav does not know about your errand; it knows about shortest paths. You turn "visit the chemist before it closes" into nodes, edges and weights, and a solved problem does the rest. The skill is the translation, and the risk is losing a constraint on the way.

## How it works

### The catalogue

| If you can say... | ...it may be | Check before you trust it |
|---|---|---|
| "Pick a subset in which every pair is compatible, and compatibility follows an order" | Sort, then a longest (or heaviest) non-decreasing subsequence | After sorting, is compatibility exactly "in order"? |
| "States and moves; fewest or cheapest moves" | Shortest path on a state graph | Few enough states? Equal or non-negative costs? |
| "Things with a start and an end; choose non-overlapping ones" | Interval scheduling (earliest end first) | Closed or half-open ends? Weighted? |
| "Split into two groups; some pairs must differ" | Two-colouring (bipartite check) | Only "must differ"? "Must be together" needs union-find first |
| "Choose items under a budget, or reach a target sum" | Knapsack | Are weights small integers? |
| "Do these before those" | Topological sort | Is a cycle possible, and what then? |

### Worked derivation: 1626 Best Team With No Conflicts

*Players have an age and a score. A team may not contain a younger player with a strictly higher score than an older player (equal ages never conflict). Maximise the team's total score; n up to 1,000.*

**Brute force.** Every subset: 2^1000. Only the oracle for tiny n.

**Dead end: greedy by score.** Take the best player, drop everyone in conflict, repeat. Counterexample from a quick check: scores [5, 4, 4] and ages [1, 2, 2]. The youngest player has the top score 5, which conflicts with both older players, so greedy returns 5, while the two older players together make 8.

**Look for order.** A conflict compares the order of ages with the order of scores. Sort players by (age, score). For two players i before j in this order, age_i <= age_j; if the ages are equal, the scores are in order too; if age_i < age_j, there is no conflict exactly when score_i <= score_j. So a team is conflict-free **if and only if** its scores are non-decreasing in sorted order, and the problem is the **heaviest non-decreasing subsequence**, a member of the longest increasing subsequence family.

**Solve the known problem.** dp[i] = score_i + the best dp[j] over earlier j with score_j <= score_i. O(n^2) = 10^6 steps for n = 1,000, which fits (a Fenwick tree over scores gives O(n log n) if n were 10^5).

### A second one: 886 Possible Bipartition

*Split n people into two groups so that no two people who dislike each other share a group.* Make each person a vertex and each dislike an edge: a valid split is exactly a colouring of the graph with two colours where no edge joins equal colours. BFS colours each component, and an edge between equal colours means no split exists (it closes an odd cycle of dislikes). The translation is exact in both directions, so the answer is the bipartite check: O(n + m).

## Cost

1626: O(n log n) to sort plus O(n^2) for the DP, O(n) space. 886: O(n + m) time and space. The translation itself costs minutes; a wrong translation costs the whole attempt, so the two-direction check is worth its time.

## When to use it

When the story is long and the structure is short: you can restate the objects and the rule in one sentence. When the constraints look like a known problem's (n up to 1,000 with pairs: an O(n^2) DP; n up to 10^5 with links: a graph). Avoid it when the translation needs an extra condition the target cannot express; then either add a step (union-find before colouring) or look for a different target.

## Worked trace

The 1626 derivation on scores [4, 5, 6, 5] and ages [2, 1, 2, 1].

```steps
Brute force: every subset of 4 players is fine here, but 2^1000 is not; keep it as the oracle
    16 subsets   ->   oracle only
---
Greedy by score fails on scores [5, 4, 4], ages [1, 2, 2]: it keeps the 5 and loses both 4s
    greedy {{5}}   best {{8}}
---
Sort by (age, score): conflicts now mean "a higher score earlier in the list"
    (1,5) (1,5) (2,4) (2,6)
---
So a team is valid exactly when its scores are {{non-decreasing}} in this order
---
dp[i] = score + best dp[j] before it with a score <= its own
    scores  5    5    4    6
    dp      5  {{10}}  4  {{16}}
---
Answer: max(dp) = 16, the two age-1 players with 5 and the age-2 player with 6
```

## Template

```python
from collections import deque


def best_team(scores, ages):
    """1626: sort by (age, score); valid teams are exactly the non-decreasing score subsequences."""
    players = sorted(zip(ages, scores))
    dp = []
    for i, (_, s) in enumerate(players):
        dp.append(s + max((dp[j] for j in range(i) if players[j][1] <= s), default=0))
    return max(dp)


def possible_bipartition(n, dislikes):
    """886: two-colour each component by BFS; an edge inside one colour means no split exists."""
    adj = [[] for _ in range(n + 1)]
    for a, b in dislikes:
        adj[a].append(b)
        adj[b].append(a)
    colour = [0] * (n + 1)                     # 0 = not yet placed, 1 and -1 = the two groups
    for start in range(1, n + 1):
        if colour[start]:
            continue
        colour[start] = 1
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if colour[v] == colour[u]:
                    return False
                if not colour[v]:
                    colour[v] = -colour[u]
                    queue.append(v)
    return True


assert best_team([4, 5, 6, 5], [2, 1, 2, 1]) == 16
assert best_team([5, 4, 4], [1, 2, 2]) == 8
assert possible_bipartition(3, [[1, 2], [1, 3], [2, 3]]) is False
```

## Pitfalls

- **A lossy translation.** Sorting 1626 by age alone (not by score within an age) makes equal-age players look like conflicts and loses teams.
- **Reducing to something harder.** "Split into two groups of equal total" is the partition problem, NP-hard in general; check whether small values make it a knapsack DP before giving up.
- **One-direction checks.** Showing that every valid team is a non-decreasing subsequence is half the proof; you also need every non-decreasing subsequence to be a valid team.
- **Forgetting disconnected parts.** 886 must start a BFS from every uncoloured vertex, not only from person 1.

## Check yourself

Q: In 1626, what goes wrong if you sort by age only, and the order within an age happens to be (age 2, score 6) then (age 2, score 4)?
A: The DP treats any team as valid only if scores never decrease along the list, so it refuses to take both of these players, although equal ages never conflict. Sorting by score within each age puts them as 4 then 6 and the problem disappears.

Q: For 886, the dislikes form a cycle 1-2-3-4-5-1. Is a split possible? Why?
A: No. Going round the cycle the colours must alternate, and a cycle of odd length (five edges) would need the first and last person to differ and match at once. Any odd cycle of dislikes makes the split impossible; even cycles are fine.

Q: "n tasks, each with a start and an end time; one worker; maximise the number of tasks done." Which known problem, and which choice is safe?
A: Interval scheduling: sort by end time and take each task that starts after the last taken one ends. The task that ends first can replace the first task of any optimal schedule, so taking it is safe.

## Lab

- **1129 Shortest Path with Alternating Colors (bank).** Reduce it to BFS on states (node, colour of the last edge). Expected: `[0, 1, 2, 1]` for `n = 4, redEdges = [[0, 1], [2, 3]], blueEdges = [[1, 2], [0, 3]]`, and `[0, 1, -1]` for `n = 3, redEdges = [[0, 1], [1, 2]], blueEdges = []`.
- **1024 Video Stitching (bank).** Reduce it to covering a segment with the fewest intervals. Expected: 3 for `clips = [[0, 3], [2, 5], [4, 8], [1, 6]], time = 8`, and -1 for `[[0, 2], [3, 5]], time = 5`.

> [!know]
> You now know how to translate a new story into a known problem and check that nothing was lost in the translation.

=== primer | When does changing the representation crack a problem? | 15 min
goal: Try the standard re-representations (take the complement, sort or index by value, build a graph, reverse time, rewrite the formula) when the direct view only gives a brute force
tag: derive-represent | Changing the representation
link: cp-algorithms: Manhattan distance, "Farthest pair of points in Manhattan distance" | https://cp-algorithms.com/geometry/manhattan-distance.html#farthest-pair-of-points-in-manhattan-distance | 5 min: rewriting |x1 - x2| + |y1 - y2| as a maximum over sign choices turns a pairwise problem into one pass, the same move as 1499 below

> [!key]
> If a problem is hard in its own terms, describe the same object differently. "Take k cards from the two ends" is the same as "leave one middle window of n - k cards". "Maximise yi + yj + |xi - xj| over pairs" becomes "(yj + xj) + (yi - xi)" once you know which point is on the right, and the pair splits into two independent parts. The standard moves are few: **complement**, **sort or index by value**, **graph**, **reverse time**, **separate the variables**.

## Intuition

Multiplying 37 by 24 in Roman numerals is miserable; in positional notation it is routine. The numbers did not change, only how they were written. Problems are the same: the statement's description is chosen to tell a story, not to make the solution visible.

## How it works

### The moves

| Move | Before | After | Example |
|---|---|---|---|
| Complement | Choose what to take | Choose what to leave, or count the bad cases | 1423: the untaken cards form one window |
| Sort or index by value | Positions in input order | Positions in value order | 962: indices sorted by value, then a running minimum |
| Build a graph | Rules about moves | Vertices and edges, then a search | 1306: jumps are edges |
| Reverse time | Deletions, or decisions that depend on the future | Insertions, or a scan from the end | Union-find handles deletions offline backwards |
| Separate the variables | f(i, j) mixes both indices | g(i) + h(j) under a known order | 1499: (yj + xj) + (yi - xi) |

### Worked derivation 1: 1423 Maximum Points You Can Obtain from Cards

*Take exactly k cards, each from the left or the right end of the row; maximise the points taken; n up to 10^5.*

**Direct view.** Every sequence of k choices: 2^k. Then notice that the order does not matter, only how many come from the left: l from the left and k - l from the right, k + 1 options with an O(k) sum each, O(k^2), or O(k) with prefix sums.

**Complement view.** Whatever you take, the cards you **leave** are one contiguous window of length n - k. Maximising the taken points is minimising the left window's sum: a fixed-size sliding window. For `[1, 2, 3, 4, 5, 6, 1]` with k = 3, the windows of length 4 sum to 10, 14, 18 and 16; the smallest is 10, so the answer is 22 - 10 = 12.

### Worked derivation 2: 1499 Max Value of Equation

*Points sorted by strictly increasing x. Maximise yi + yj + |xi - xj| over pairs i < j with xj - xi <= k; n up to 10^5.*

**Direct view.** All pairs: about 5·10^9 for n = 10^5, far too slow.

**Rewrite the formula.** Since i < j means xi < xj, the absolute value is xj - xi, and the value is (yj + xj) + (yi - xi). The two halves no longer interact: for each j, you need the largest yi - xi among earlier points with xj - xi <= k. That is a **sliding window maximum** over points ordered by x: a monotonic deque of (x, y - x) with decreasing y - x, expiring points from the front when they are more than k to the left. A heap with lazy deletion also works in O(n log n).

## Cost

1423: O(n) time and O(1) extra space. 1499: O(n) time and O(n) space, because each point enters and leaves the deque at most once. Building a new representation must be cheaper than what it saves: sorting is O(n log n), a graph with n^2 edges may already be too big.

## When to use it

- The objective mixes two indices: try to separate them under an order.
- "From both ends", "at least one", "remove some": try the complement.
- Elements removed over time: try reversing time so they are added.
- Manhattan distances: rewrite |a| + |b| as a maximum over sign choices, or rotate coordinates to (x + y, x - y).
- Not when the new view is as large as the brute force itself.

## Worked trace

The 1499 deque on points (1, 3), (2, 0), (5, 10), (6, -10) with k = 1. The deque stores (x, y - x).

```steps
(1, 3): deque empty, nothing to pair; push (1, 2)
    best = -inf   deque [(1, {{2}})]
---
(2, 0): (1, 2) is within k = 1, so value = 0 + 2 + 2 = 4; push (2, -2) behind the larger 2
    best = {{4}}   deque [(1, 2), (2, {{-2}})]
---
(5, 10): both points are more than 1 to the left: expire them; nothing to pair; push (5, 5)
    best = 4   deque [(5, {{5}})]
---
(6, -10): (5, 5) is within k, so value = -10 + 6 + 5 = 1, less than 4; push (6, -16)
    best = 4   deque [(5, 5), (6, {{-16}})]
---
Answer {{4}}: points 1 and 2 give 3 + 0 + |1 - 2| = 4
```

## Template

```python
from collections import deque


def max_score(cards, k):
    """1423: the untaken cards form one window of length n - k; minimise its sum. O(n), O(1)."""
    n, w = len(cards), len(cards) - k
    window = sum(cards[:w])
    smallest = window
    for right in range(w, n):
        window += cards[right] - cards[right - w]
        smallest = min(smallest, window)
    return sum(cards) - smallest


def find_max_value_of_equation(points, k):
    """1499: for i < j the value is (yj + xj) + (yi - xi); keep the best yi - xi within reach
    in a deque whose y - x values decrease from front to back. O(n)."""
    dq = deque()                                # (x, y - x)
    best = float("-inf")
    for x, y in points:
        while dq and x - dq[0][0] > k:
            dq.popleft()
        if dq:
            best = max(best, x + y + dq[0][1])
        while dq and dq[-1][1] <= y - x:
            dq.pop()
        dq.append((x, y - x))
    return best


assert max_score([1, 2, 3, 4, 5, 6, 1], 3) == 12
assert find_max_value_of_equation([[1, 3], [2, 0], [5, 10], [6, -10]], 1) == 4
```

## Pitfalls

- **Off-by-one in the complement.** The window has length n - k; when k = n it is empty, its sum is 0 and the answer is the total. The template handles it because `sum(cards[:0])` is 0 and the loop does not run.
- **Dropping the order assumption.** (yj + xj) + (yi - xi) holds only because xi < xj; without sorted x you would need both sign cases.
- **Storing values without positions.** The deque must keep x to know when a point has fallen out of range.
- **Popping in the wrong place.** Expire stale fronts before reading the best candidate, and push the current point only after using the deque, so a point never pairs with itself.

## Check yourself

Q: In the trace, why does (5, 10) find the deque empty before it is pushed?
A: Both earlier points are more than k = 1 to its left (5 - 1 = 4 and 5 - 2 = 3), so they expire from the front first. With no candidate left, it cannot pair, and it is pushed as (5, 5).

Q: Why may the deque discard an older point whose y - x is at most a newer point's?
A: The newer point has a larger x, so it stays within range for at least as long as the older one, and its y - x is at least as large. The older point can never again be the better partner, so keeping it would only cost time.

Q: "Count the subsets of n numbers that contain at least one even number." Which move, and what is the answer if the set has e even and o odd numbers?
A: The complement: count all subsets and subtract those with no even number. 2^(e + o) - 2^o (this counts the empty set as having no even number, so it is excluded automatically).

## Lab

- **962 Maximum Width Ramp (bank).** Find the largest j - i with i < j and nums[i] <= nums[j]. Try sorting the indices by value, then scanning while keeping the smallest index seen so far. Expected: 3 for `[3, 1, 4, 1, 2]` and 0 for `[5, 4, 3]`.
- **2483 Minimum Penalty for a Shop (bank).** Rewrite the penalty for each closing hour as a running balance instead of recounting. Expected: 4 for `"YNYY"` (penalties by closing hour 0 to 4: 3, 2, 3, 2, 1) and 0 for `"NYNN"` (1, 2, 1, 2, 3).

> [!know]
> You now know the standard ways to re-describe a problem so that its structure, and a fast algorithm, become visible.

=== primer | How do you decide what state a scan or a DP must remember? | 16 min
goal: Find the smallest summary of the past that lets a scan or a DP decide the future correctly, and test it by checking that two histories with the same state always have the same best future
tag: derive-state | Inventing the state
link: Jeff Erickson, Algorithms, chapter 3 "Dynamic Programming" (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=9 | 10 min: "The Pattern: Smart Recursion" on PDF page 9: describe the subproblem in words before writing the recurrence

> [!key]
> A scan or a DP works when you can forget most of the past. Ask: **what must I know about what I have already processed to make the best decision from here on?** Start with the obvious state (the position), look for two histories that end in the same state but need different futures, and add exactly the information that tells them apart: a last direction, a half-filled column, a mode flag. Stop when every history with the same state has the same best future.

## Intuition

In chess, the position decides the best move, not the moves that led to it, with a few exceptions such as whether the king has already moved (castling rights) and whose turn it is. Those exceptions are exactly the extra state the board alone does not show. Every DP state is a "position" plus its castling rights.

## How it works

### The test: same state, same future

Write the state you think is enough. Then try to build two different pasts that leave you in that state but where the best continuation differs. If you can, the state is missing something; add the smallest piece of information that separates them, and test again. If you cannot, the state is complete, and the recurrence follows: the best future from a state is the best over the next choices of (gain now + best future from the next state).

### Worked derivation 1: 376 Wiggle Subsequence

*Find the longest subsequence whose consecutive differences strictly alternate in sign; n up to 1,000, with an O(n) follow-up.*

**Brute force.** All 2^n subsequences: the oracle.

**First state: "the longest wiggle subsequence ending at index i".** Two histories ending at the same element can need different futures: one whose last step went up must go down next, one whose last step went down must go up. So add the direction: `up[i]` and `down[i]`, the longest wiggle ending at i whose last step went up or down. up[i] = 1 + max(down[j]) over j < i with nums[j] < nums[i], and symmetrically. O(n^2).

**Shrink the state.** Do we need every j? Scanning left to right, keep only `up` and `down` for the best subsequences so far. When x > prev, the best subsequence ending with an upward step can always be taken to end at x: extend the best downward one with x, or replace its last element with x, which is at least as good because a larger last value only makes the next downward step easier. So up = down + 1; symmetrically for x < prev; equal neighbours change nothing. O(n) time, O(1) space.

### Worked derivation 2: 790 Domino and Tromino Tiling

*Count the tilings of a 2 x n board with dominoes and L-shaped trominoes (any rotation), modulo 10^9 + 7; n up to 1,000.*

**First state: full(i), the tilings of a 2 x i board.** A tromino sticks out by one cell, so some partial tilings end with one column half-filled, and full(i) cannot describe them. Two histories with "i columns done" differ in whether a cell of column i + 1 is already covered: add that.

**Second state: part(i), the tilings of a 2 x i board plus one extra cell in column i + 1** (top or bottom; mirror images have equal counts, so one number covers both).

**Transitions.** Look at what covers the last column. For full(i): a vertical domino (from full(i - 1)), two horizontal dominoes (from full(i - 2)), or a tromino that completes a half-filled column (from part(i - 2), twice for the two mirror images). For part(i): the sticking-out cell is covered by a horizontal domino (from part(i - 1)) or by a tromino that also fills column i (from full(i - 1)).

full(i) = full(i - 1) + full(i - 2) + 2·part(i - 2) and part(i) = part(i - 1) + full(i - 1), with full(0) = full(1) = 1 and part(0) = 0.

A brute-force tiler that tries every placement agrees for n = 1..10: 1, 2, 5, 11, 24, 53, 117, 258, ... And the small-cases habit finds a bonus: full(n) = 2·full(n - 1) + full(n - 3), which can be proved from the two recurrences.

## Cost

376: O(n) time, O(1) space (the O(n^2) table first, then the compression). 790: O(n) time with O(n) arrays, or O(1) space with rolling variables. In general a DP costs (number of states) x (work per state), so every piece of state you add multiplies the cost; add only what the "same state, same future" test demands.

## When to use it

- A recurrence that "almost works": it fails on an input where the past matters in a way the state ignores.
- Modes in the statement: holding or not, cooldown, "no two adjacent", alternating, the last colour used.
- Partly built structures: tilings, profiles, open brackets.
- When the state you need grows with n (a set of used items for n = 100), the decomposition is wrong: look for another order or a greedy argument, or accept bitmask DP for n <= 20.

## Worked trace

The O(n) wiggle scan on `[1, 17, 5, 10, 13, 15, 10, 5, 16, 8]`.

```steps
Start: one element is a wiggle of length 1 either way
    up = 1   down = 1
---
17 > 1: up = down + 1
    x = 17   up = {{2}}   down = 1
---
5 < 17: down = up + 1
    x = 5    up = 2   down = {{3}}
---
10 > 5: up = down + 1 = 4; then 13 and 15 keep rising: up stays 4 (they only replace the peak)
    x = 10, 13, 15   up = {{4}}   down = 3
---
10 < 15: down = 5; then 5 < 10 keeps falling: down stays 5
    x = 10, 5   up = 4   down = {{5}}
---
16 > 5: up = 6; 8 < 16: down = 7. Answer max(up, down) = {{7}}
    x = 16, 8   up = 6   down = 7
```

## Template

```python
def wiggle_max_length(nums):
    """376: up/down = longest wiggle so far whose last step went up/down. O(n) time, O(1) space."""
    up = down = 1
    for prev, x in zip(nums, nums[1:]):
        if x > prev:
            up = down + 1
        elif x < prev:
            down = up + 1
    return max(up, down)


def num_tilings(n):
    """790: full[i] tiles a 2 x i board exactly; part[i] tiles 2 x i plus one cell of column i + 1."""
    MOD = 10**9 + 7
    full = [1, 1] + [0] * (n - 1)
    part = [0] * (n + 1)
    for i in range(1, n + 1):
        if i >= 2:
            full[i] = (full[i - 1] + full[i - 2] + 2 * part[i - 2]) % MOD
        part[i] = (part[i - 1] + full[i - 1]) % MOD
    return full[n]


assert wiggle_max_length([1, 17, 5, 10, 13, 15, 10, 5, 16, 8]) == 7
assert [num_tilings(n) for n in range(1, 9)] == [1, 2, 5, 11, 24, 53, 117, 258]
```

## Pitfalls

- **A state that is too small.** It passes the examples and fails where two pasts need different futures; stress-test against a brute force, which finds exactly those inputs.
- **A state that is too big.** Every extra field multiplies the number of states; a set of used items for n = 100 is 2^100 states.
- **Forgetting symmetry.** The factor 2 in 2·part(i - 2) counts the two mirror images; leaving it out gives 1, 2, 4, ... instead of 1, 2, 5, ...
- **Equal neighbours.** In the wiggle scan an equal value is neither up nor down; treating it as either breaks the strict alternation.

## Check yourself

Q: Give two histories for the wiggle problem that end at the same element but need different futures.
A: For [1, 5, 3] the subsequence 1, 5, 3 ends with a downward step, so the next step must go up; the subsequence 3 alone (or 1, 3) ends with no step or an upward one. Both end at the element 3, but one needs a larger next value and the other a smaller one, so "ending at 3" is not enough state: the last direction must be added.

Q: Using the recurrences, compute full(6) from full = 1, 1, 2, 5, 11, 24 and part = 0, 1, 2, 4, 9, 20 (indices 0 to 5).
A: full(6) = full(5) + full(4) + 2·part(4) = 24 + 11 + 2·9 = 53, matching the brute-force tiler.

Q: "Maximise profit from buying and selling a share any number of times, with a fee per sale." What is the state?
A: The day and whether you hold a share: hold[i] = max(hold[i - 1], free[i - 1] - price[i]) and free[i] = max(free[i - 1], hold[i - 1] + price[i] - fee). The flag separates histories that need different futures (one can sell tomorrow, the other can only buy).

## Lab

- **2466 Count Ways To Build Good Strings (bank).** State: only the current length matters. Expected: 8 for `low = 3, high = 4, zero = 1, one = 2`.
- **1218 Longest Arithmetic Subsequence of Given Difference (bank).** State: the best length of a subsequence ending with each value, kept in a dict. Expected: 4 for `[3, 1, 5, 2, 7, 9]` with difference 2, and 4 for `[4, 3, 2, 1]` with difference -1.

> [!know]
> You now know how to find the smallest state that makes a scan or a DP correct, and how to test it.

=== primer | How do you know your solution cannot be improved? | 13 min
goal: Compare a solution with three lower bounds (reading the input, writing the output, comparison sorting) and with the constraints, and stop optimising when they meet
tag: derive-lower-bound | Lower bounds
link: Wikipedia: Comparison sort, "Number of comparisons required to sort a list" | https://en.wikipedia.org/wiki/Comparison_sort#Number_of_comparisons_required_to_sort_a_list | 6 min: why any comparison sort needs about n log2 n comparisons (log2 of n! leaves of a decision tree)
link: Tech Interview Handbook: Coding interview techniques, "Identify the best theoretical time complexity of the solution" | https://www.techinterviewhandbook.org/coding-interview-techniques/#1-identify-the-best-theoretical-time-complexity-of-the-solution | 3 min: the "you must at least read the input" argument applied to interview questions

> [!key]
> Three bounds settle most "can I do better?" questions. You must **read the input**: Ω(n) for an array, Ω(n + m) for a graph. You must **write the output**: listing every path costs at least the total length of the paths. And any **comparison sort** needs Ω(n log n) comparisons. When your solution matches the best bound that applies, or already fits the constraints with room to spare, stop optimising and spend the time on testing.

## Intuition

You cannot count the votes without looking at every ballot, and you cannot publish a list of a million names faster than it takes to write them. Lower bounds are arguments of that kind: they do not tell you how to solve a problem, they tell you when to stop looking for something faster.

## How it works

### The bounds

| Bound | Argument | Consequence |
|---|---|---|
| Read the input | If an algorithm skips some element, an adversary changes that element so the answer changes, and the algorithm cannot notice | Ω(n) for most array problems: an O(n) scan is optimal |
| Write the output | Every output item takes at least one step to produce | Listing all subsets of n items is Ω(n·2^n); listing all paths is Ω(total length) |
| Comparison sorting | A decision tree that sorts must have n! leaves, so its depth is at least log2(n!), about n log2 n - 1.44n | Sorting by comparisons is Ω(n log n); counting sort escapes it by using integer keys as indices |
| Element distinctness | In the comparison-based (algebraic decision tree) model, deciding whether all n values differ is also Ω(n log n) | Hashing beats it on average, with expected O(n), because hashing is not comparison-based |
| The constraints | The setter chose n so that the intended complexity runs in time | n <= 1,000 makes O(n^2) a complete answer; a faster algorithm is optional |

### Worked derivation 1: 797 All Paths From Source to Target

*List every path from node 0 to node n - 1 in a directed acyclic graph with n <= 15 nodes.*

DFS from 0 with a path list: append a node when entering, pop it when leaving, and copy the path when it reaches n - 1. Is there anything faster? Consider the complete DAG with an edge i -> j for every i < j. Every path from 0 to n - 1 chooses, for each of the n - 2 middle nodes, whether to visit it, so there are 2^(n-2) paths: 8,192 for n = 15, with 69,632 node entries in total. Any algorithm must write all of them, so the output alone costs Ω(2^(n-2)) entries, and on this graph DFS spends work proportional to the output. Nothing asymptotically faster exists; stop.

### Worked derivation 2: 2104 Sum of Subarray Ranges

*Sum max - min over all subarrays; n <= 1,000, with an O(n) follow-up.*

**The constraint bound.** For each start i, extend the end j and carry the running max and min: O(n^2), about 5·10^5 steps at n = 1,000, a fraction of a second. That already answers the problem as set.

**The input bound for the follow-up.** Any algorithm must read all n values, so Ω(n). Reaching O(n) needs a new view: the total is (sum over subarrays of their max) minus (sum of their min), and each element is the maximum of a countable number of subarrays. If left is the nearest index to the left with a strictly larger value and right the nearest to the right with a larger or equal value, nums[i] is the maximum of exactly (i - left)·(right - i) subarrays. A monotonic stack finds every left and right in one pass. O(n) matches the bound, so this is optimal.

## Cost

797: O(2^n · n) in the worst case, proportional to the output. 2104: O(n^2) simple, O(n) with contribution counting, O(n) space. The method costs one minute: name the bound, compare, decide.

## When to use it

Before a second round of optimisation; when an interviewer asks "can you do better?" (answer with the bound, then say whether you have met it); when the output itself is large. Remember what a lower bound does not say: it does not promise an algorithm that meets it.

## Worked trace

Contribution counting for the maxima of `[3, 1, 2]` (the minima work the same way with the comparisons flipped).

```steps
Element 3 at index 0: nothing larger on either side, left = -1, right = 3
    3 is the max of (0 + 1) * (3 - 0) = {{3}} subarrays: [3] [3,1] [3,1,2]
---
Element 1 at index 1: left = 0 (3 > 1), right = 2 (2 >= 1)
    1 is the max of (1 - 0) * (2 - 1) = {{1}} subarray: [1]
---
Element 2 at index 2: left = 0 (3 > 2), right = 3
    2 is the max of (2 - 0) * (3 - 2) = {{2}} subarrays: [2] [1,2]
---
Sum of maxima = 3*3 + 1*1 + 2*2 = {{14}}; the same method gives sum of minima = {{9}}
---
Sum of ranges = 14 - 9 = {{5}}: check by hand: [3,1] 2 + [1,2] 1 + [3,1,2] 2 = 5
```

## Template

```python
def all_paths(graph):
    """797: DFS from 0 copying the path at the target. O(P * n) for P paths: the output size."""
    target, out, path = len(graph) - 1, [], [0]

    def dfs(u):
        if u == target:
            out.append(path[:])
            return
        for v in graph[u]:
            path.append(v)
            dfs(v)
            path.pop()
    dfs(0)
    return out


def sum_of_extremes(nums, better):
    """Sum over all subarrays of their max (better = >) or min (better = <). nums[i] is the extreme of
    (i - left) * (right - i) subarrays; an equal value stops it on the right only, so each subarray
    counts once. O(n)."""
    n = len(nums)
    left, right, stack = [-1] * n, [n] * n, []
    for i, x in enumerate(nums):
        while stack and not better(nums[stack[-1]], x):
            right[stack.pop()] = i
        left[i] = stack[-1] if stack else -1
        stack.append(i)
    return sum(nums[i] * (i - left[i]) * (right[i] - i) for i in range(n))


def sub_array_ranges(nums):
    return sum_of_extremes(nums, lambda a, b: a > b) - sum_of_extremes(nums, lambda a, b: a < b)


assert len(all_paths([list(range(i + 1, 15)) for i in range(15)])) == 2 ** 13
assert sub_array_ranges([3, 1, 2]) == 5 and sub_array_ranges([4, -2, -3, 4, 1]) == 59
```

## Pitfalls

- **Confusing the problem's bound with your algorithm's cost.** "Sorting is Ω(n log n)" does not make your O(n^2) sort optimal.
- **Applying the sorting bound to integers in a small range.** Counting sort runs in O(n + k) because it never compares.
- **Ignoring output-sensitive costs.** Copying each path is part of the work; so is building each answer string.
- **Over-optimising.** With n <= 1,000, the O(n^2) version of 2104 is a complete answer; the O(n) version is for the follow-up, or for practice.

## Check yourself

Q: A colleague claims an O(log n) algorithm for the maximum of an unsorted array. Why is that impossible?
A: An algorithm that reads fewer than n elements leaves some element unread; an adversary can make that element larger than everything else without changing what was read, so the algorithm gives the same, now wrong, answer. Any correct algorithm reads all n elements: Ω(n).

Q: What is the best possible complexity for "return all subsets of n <= 20 distinct numbers", and does backtracking reach it?
A: The output has 2^n subsets with n·2^(n-1) numbers in total, so Ω(n·2^n). Backtracking (or bitmask enumeration) produces each subset with O(n) work to copy it, O(n·2^n) in total: optimal.

Q: Can you sort 10^6 integers in the range 0 to 1,000 faster than O(n log n)? Explain without contradicting the sorting bound.
A: Yes: counting sort in O(n + k) with k = 1,001 counters. The Ω(n log n) bound applies only to algorithms that learn about the order by comparing elements; counting sort uses the values as indices instead.

## Lab

- **977 Squares of a Sorted Array (bank).** Expected: `[1, 4, 9, 16]` for `[-3, -1, 2, 4]`. Write the O(n) two-pointer version and explain in two sentences why O(n) is optimal and why "square and sort" (O(n log n)) is not.
- **118 Pascal's Triangle (bank).** Expected: `[[1], [1, 1], [1, 2, 1], [1, 3, 3, 1]]` for 4 rows. State the output-size bound: n rows hold n(n + 1)/2 numbers, so Θ(n^2) is the best possible.

> [!know]
> You now know how to argue from the input, the output and comparison sorting that a solution cannot be beaten, and when to stop optimising.

=== primer | How do you explain a solution in 60 seconds? | 13 min
goal: State the approach, the invariant, the cost and the edge cases of any solution in about a minute, in the order a listener needs them
tag: derive-explain | Explaining a solution in 60 seconds
link: Tech Interview Handbook: Coding interview cheatsheet, "Work out and optimize your approach with the interviewer" | https://www.techinterviewhandbook.org/coding-interview-cheatsheet/#3-work-out-and-optimize-your-approach-with-the-interviewer | 5 min: what to say before coding; the next section covers talking while you code

> [!key]
> A good explanation has four parts in a fixed order: the **approach** in one sentence (the technique and the decision it makes), the **invariant** or recurrence that makes it correct, the **cost** with its reason, and the **edge cases** you handled. Practise it on every problem you solve. If you cannot say the invariant in one sentence, you do not yet know why your code works.

## Intuition

A good commit message or pull request description works the same way: what changed, why it is right, what it costs, what could break. A listener cannot read your mind; they can follow four short claims in a logical order, and each claim gives them a hook to ask about.

## How it works

### The four parts, with a time budget

| Part | About | Says |
|---|---|---|
| Approach | 15 s | The technique and the key decision: "grow a window from k, always towards the larger neighbour" |
| Why it is correct | 20 s | The invariant, recurrence or exchange argument, in one or two sentences |
| Cost | 10 s | Time and space, with the reason ("each element enters once") |
| Edge cases | 15 s | The inputs you thought about: empty, one element, ends of the array, ties, overflow |

### Worked derivation: 1793 Maximum Score of a Good Subarray

*The score of a subarray is min(subarray) × length; find the best score among subarrays that contain index k; n up to 10^5.*

**Brute force.** For each left end i <= k and right end j >= k, a running minimum gives O(n^2). Too slow, but it is the oracle.

**Observation.** As a good subarray grows, its minimum can only fall. Fix a value m: among good subarrays whose minimum is at least m, the best is the widest one, the maximal stretch around k where every value is at least m. So the answer only ever needs these maximal stretches.

**Idea.** Start with [k, k] and grow one element at a time, always stepping towards the **larger** neighbour, recording min × width after every step. Stepping towards the larger neighbour lowers the minimum as little as possible, so the window absorbs every value at least m before it touches any value below m.

**Why it is correct.** Take an optimal subarray [p, q] with minimum m. The greedy windows grow from [k, k] to the whole array one element at a time, so consider the first window that is not inside [p, q]; it was made by stepping to p - 1 or q + 1, say p - 1. If the right end were still short of q, the right neighbour would be at least m (it is inside [p, q]), and the greedy step chose p - 1 because nums[p - 1] is at least that neighbour, so [p - 1, q] would have minimum at least m and be wider than [p, q], contradicting optimality. So the window just before was exactly [p, q], and its score was recorded.

### The 60-second version

"I grow a window outwards from k one element at a time, always taking the larger of the two neighbours, and record min times width after each step. It is correct because for any minimum value m the best good subarray is the widest window around k with all values at least m, and taking the larger neighbour first means the window passes through exactly that window before it absorbs anything smaller. It takes n - 1 steps of O(1) work, so O(n) time and O(1) space. Edge cases: when k is at an end of the array I treat the missing neighbour as 0 so the other side is taken; a single element scores itself; ties between neighbours can go either way."

## Cost

O(n) time and O(1) space for 1793. The explanation costs a minute to say and three minutes to write after solving; writing it is the fastest way to find a gap in your own argument.

## When to use it

In interviews (before coding, then again after testing), in code review and pull requests, and in your problem journal, where the four parts make a perfect entry. Do not narrate code line by line; nobody can hold that in their head.

## Worked trace

The expansion on `nums = [1, 4, 3, 7, 4, 5]` with k = 3.

```steps
Start at [3, 3]: min = 7, score 7
    1  4  3 [{{7}}] 4  5        best = 7
---
Neighbours 3 (left) and 4 (right): take the larger, 4
    1  4  3 [7  {{4}}] 5        min 4, width 2, score 8, best = {{8}}
---
Neighbours 3 and 5: take 5
    1  4  3 [7  4  {{5}}]       min 4, width 3, score 12, best = {{12}}
---
Right side exhausted (treated as 0): take 3 on the left
    1  4 [{{3}}  7  4  5]       min 3, width 4, score 12, best = 12
---
Take 4 on the left: min stays 3
    1 [{{4}}  3  7  4  5]       min 3, width 5, score {{15}}, best = 15
---
Take 1: min drops to 1, score 6; the answer is {{15}}
    [{{1}}  4  3  7  4  5]      min 1, width 6
```

## Template

```python
def maximum_score(nums, k):
    """1793 Maximum Score of a Good Subarray.
    Approach: grow [i, j] from [k, k] towards the larger neighbour, recording min * width.
    Why: for each minimum m, the best good subarray is the widest window around k with values >= m,
         and taking the larger neighbour first passes through that window.
    Cost: O(n) time, O(1) space.
    Edges: k at either end (missing neighbour counts as 0), n = 1, ties go either way."""
    n = len(nums)
    i = j = k
    low = best = nums[k]
    while i > 0 or j < n - 1:
        left = nums[i - 1] if i > 0 else 0
        right = nums[j + 1] if j < n - 1 else 0
        if left >= right:
            i -= 1
            low = min(low, left)
        else:
            j += 1
            low = min(low, right)
        best = max(best, low * (j - i + 1))
    return best


assert maximum_score([1, 4, 3, 7, 4, 5], 3) == 15
assert maximum_score([5, 5, 4, 5, 4, 1, 1, 1], 0) == 20
```

The docstring is the 60-second explanation in writing: every function you are proud of deserves one.

## Pitfalls

- **Starting with details.** "First I set i and j to k..." loses the listener; lead with the idea.
- **"It works because I tested it."** Tests show it worked on some inputs; the invariant says why it works on all.
- **Forgetting space and edge cases.** They take ten seconds and are exactly what a reviewer checks next.
- **Getting library costs wrong.** `sorted` is O(n log n), `x in list` is O(n), `list.pop(0)` is O(n); say them correctly or not at all.

## Check yourself

Q: State in one sentence why the 1793 expansion never skips the optimal window.
A: Because it always takes the larger neighbour, it absorbs every value of at least m that is connected to k through values of at least m before it takes any value below m, so for every m the window passes through the widest stretch around k whose values are all at least m (the trace shows it: [1, 5] with minimum 3 is reached before the 1).

Q: Why does the code treat a missing neighbour as 0?
A: All values are at least 1, so 0 is smaller than any real neighbour; the comparison then always chooses the side that still has elements, without a special case.

Q: An explanation reads: "I use a monotonic stack, O(n)." What is missing, and what would you ask?
A: The decision the stack makes (what is popped and what each pop answers), the invariant (what is true of the stack), the space, and the edge cases. Ask: "What does the stack hold, and why is each element popped at most once?"

## Lab

- **1475 Final Prices With a Special Discount in a Shop (bank).** Solve it, then write and time a 60-second explanation with all four parts. Expected: `[2, 0, 3, 1, 2]` for `prices = [5, 3, 6, 3, 2]`, and an explanation that names what the stack holds.
- **1094 Car Pooling (bank).** Expected: true for `trips = [[3, 0, 4], [2, 2, 6], [1, 4, 7]]` with capacity 5, false with capacity 4. Your explanation must say why drop-offs at a point are counted before pick-ups there.

> [!know]
> You now know how to explain any solution in about a minute: approach, why it is correct, cost, edge cases.

=== primer | How do you run a timed session or a mock interview? | 14 min
goal: Run 45- and 75-minute sessions with a fixed plan for the clock, think aloud, and finish every session with a written post-mortem
tag: derive-timed | Timed sessions and mock interviews
link: Tech Interview Handbook: Coding interview cheatsheet, "Upon receiving the question, make clarifications" | https://www.techinterviewhandbook.org/coding-interview-cheatsheet/#2-upon-receiving-the-question-make-clarifications | 5 min: the clarifying questions for the first minutes; read on through "Code out your solution while talking through it"

> [!key]
> Practise under the conditions you will be tested in: a timer, no hints, your reasoning **spoken aloud**, and a plan for the clock (understand, examples and brute force, optimise, code, test). Afterwards write a **post-mortem** while it is fresh: where the time went, which step failed or dragged, and the single change you will make next time. A timed session that ends without a post-mortem is only half a session.

## Intuition

Musicians rehearse with a metronome and fire services run drills, because skills that work in a calm room fall apart under a clock and an audience. The aim is not to be fast at everything; it is to have a routine so practised that the pressure has nothing to disturb.

## How it works

### A plan for the clock

| Phase | 45 min (one Medium) | 75 min (two problems, or one Hard) |
|---|---|---|
| Restate, ask questions, constraints to a target | 0-5 | 0-7 |
| Examples by hand, brute force stated with its cost | 5-12 | 7-17 |
| Optimise: idea, invariant, cost | 12-22 | 17-35 |
| Code | 22-35 | 35-60 |
| Test: examples, edge cases, a trace | 35-42 | 60-70 |
| Spare, then the 60-second explanation | 42-45 | 70-75 |

If the optimise phase overruns, code the brute force cleanly at the checkpoint, test it, and say what the bottleneck is. A correct slow solution with a clear diagnosis beats an unfinished clever one.

### Thinking aloud

Say decisions, not keystrokes: "n is 10^5, so quadratic is out", "this is the brute force, it costs n times depth", "the repeated work is walking the same chain". When stuck, say what you are trying. In a mock interview, the interviewer gets the problem and its hints in advance, gives a hint only after a few silent minutes, and notes where you hesitated; then swap roles.

### Worked session: 1376 Time Needed to Inform All Employees

*A company's management forms a tree; the head knows some news, and manager m needs informTime[m] minutes to tell all direct reports. How long until everyone knows? n up to 10^5.* A 45-minute run, with what was said at each checkpoint, is in the trace below.

### The post-mortem, five lines

1. Result and time: Solved, Brute only or Stuck; minutes used against the plan.
2. Where the time went, phase by phase.
3. What went well and should stay.
4. The step that failed or dragged, and why (the next card shows how to find it).
5. One change for the next session.

## Cost

A session costs 45 or 75 minutes plus about 15 minutes of post-mortem. In the mastery stage, one per week is a good rhythm; before interviews, two or three per week. For 1376 itself: O(n) time and space.

## When to use it

Once a technique is familiar, and always on problems you have not seen. Do not time first contact with a new technique: learning needs room to be slow. Use the 45-minute plan for single Mediums and the 75-minute plan for the timed mock that ends this module.

## Worked trace

The 45-minute session on 1376, checkpoint by checkpoint.

```steps
00:00 Restate aloud: "each employee hears after the sum of informTime of everyone above them; answer = the max"
    phase: restate      plan: 0-5
---
03:00 Constraints: n = 10^5, so {{O(n)}} or O(n log n); informTime <= 1000, so the answer stays below 10^8
    phase: constraints  target: O(n)
---
06:00 Examples: a star gives informTime[head]; a chain gives the sum along it
    star -> 1        chain of 4 with 1 each -> 3
---
09:00 Brute force: walk up from every employee: O(n * depth), {{10^10}} on a chain, too slow
    phase: brute force  cost stated
---
13:00 Repeated work: the same chains are walked again and again; time(e) = time(manager) + informTime[manager]
    idea: one pass {{top-down}} from the head
---
16:00 Depth can be 10^5, past the recursion limit: use an iterative BFS from the head
    invariant: a node's time is final once dequeued (manager first)
---
20:00 to 32:00 Code; 32:00 to 40:00 test: n = 1 -> 0, the star -> 1, a 10^5 chain -> 99,999 in about 0.1 s
    phase: test         all pass
---
40:00 The 60-second explanation, then the post-mortem: "brute force took 4 minutes; next time state its cost sooner"
```

## Template

```python
import time
from collections import deque


def num_of_minutes(n, head, manager, inform_time):
    """1376: BFS from the head carrying the time each employee hears the news. O(n) time and space."""
    children = [[] for _ in range(n)]
    for e, m in enumerate(manager):
        if m != -1:
            children[m].append(e)
    best = 0
    queue = deque([(head, 0)])
    while queue:
        u, t = queue.popleft()
        best = max(best, t)
        for v in children[u]:
            queue.append((v, t + inform_time[u]))
    return best


class Session:
    """Mark when each phase of a timed attempt begins; report minutes per phase for the post-mortem."""

    def __init__(self, clock=time.monotonic):
        self.clock, self.phases = clock, []

    def begin(self, name):
        self.phases.append((name, self.clock()))

    def report(self):
        times = [t for _, t in self.phases] + [self.clock()]
        return [(name, round((times[i + 1] - times[i]) / 60, 1)) for i, (name, _) in enumerate(self.phases)]


assert num_of_minutes(6, 2, [2, 2, -1, 2, 2, 2], [0, 0, 1, 0, 0, 0]) == 1
assert num_of_minutes(4, 0, [-1, 0, 0, 1], [2, 3, 0, 0]) == 5
```

## Pitfalls

- **Coding before stating the approach.** Five minutes of silence and typing hides your reasoning and often the wrong idea.
- **Skipping tests to "finish".** An untested solution is a guess; keep the test phase even when time is short.
- **No post-mortem.** The session's lesson is in the post-mortem; without it you repeat the same overrun next week.
- **Only problems you have seen.** A timed re-solve trains recall; a mock needs unseen problems.

## Check yourself

Q: It is minute 25 of a 45-minute session and you have no optimal idea. What do you do?
A: Code the brute force now, cleanly, and test it; state its cost and exactly where the repeated work is. Then use any time left to try one optimisation from the ladder. A tested correct solution with a clear diagnosis is worth far more than an unfinished fast one.

Q: For 1376, what is the answer for manager = [-1, 0, 0, 1], informTime = [2, 3, 0, 0], head 0?
A: 5. Employees 1 and 2 hear at minute 2 (from the head); employee 3 reports to 1 and hears at 2 + 3 = 5, the latest.

Q: Why is an iterative BFS safer than a recursive DFS for 1376 in Python?
A: A chain of 10^5 employees makes the recursion 10^5 calls deep, far beyond Python's default limit of 1,000, so a recursive DFS raises RecursionError; the BFS keeps its frontier in a deque and has no depth limit.

## Lab

Run two 45-minute sessions on different days, with the `Session` timer and a five-line post-mortem each.

- **1162 As Far from Land as Possible (bank).** Expected: 2 for `[[1, 0, 0], [0, 0, 0], [0, 0, 1]]` and 4 for `[[1, 0, 0], [0, 0, 0], [0, 0, 0]]`; O(n^2) for an n x n grid.
- **1306 Jump Game III (bank).** Expected: true for `arr = [2, 0, 1, 3], start = 3`, and false for `arr = [1, 2, 0], start = 1`.
- Expected for the Lab: two post-mortems whose fifth lines name concrete changes, and a second session whose phase times sit closer to the plan.

> [!know]
> You now know how to run timed sessions and mock interviews with a plan for the clock, and how to learn from them with a post-mortem.

=== primer | How do you learn the most from a failed attempt? | 13 min
goal: Locate the exact step of the solving loop that failed, re-derive the missing step without looking, and write the insight as a card that transfers to new problems
tag: derive-postmortem | Learning from a failed attempt
link: Andy Matuschak: How to write good prompts, "Procedural knowledge" | https://andymatuschak.org/prompts/#procedural-knowledge | 6 min: how to write cards about how to do things (the decisions and their conditions), which is what an insight card is

> [!key]
> A failed attempt is the most informative event in practice, if you find **where** it failed. Walk the solving loop (restate, examples, brute force, optimise, prove, code, test) and find the first step that went wrong. Then close the solution, re-derive the missing step yourself, and write the insight as a general card ("when X, do Y, because Z"), not as a fact about one problem. Test the card on a second problem.

## Intuition

When a bridge fails, engineers do not just rebuild it; they find the one design assumption that broke and change the standard so no bridge repeats it. "I should have known the trick" is not a finding. "In the optimise step I never asked what was repeated" is a finding, and it applies to every future problem.

## How it works

### Locate the failure

| Step of the loop | Symptom that it failed |
|---|---|
| Restate | You solved a different problem, or missed a constraint |
| Examples | Your idea broke on a case you never tried by hand |
| Brute force | You never had a correct baseline, so you could not test anything |
| Optimise | Correct but too slow; the repeated work was never named |
| Prove | The idea "felt right" and was wrong on some input |
| Code | The idea was right, the implementation was not |
| Test | It failed on an edge case you did not run |

### Worked failure: 945 Minimum Increment to Make Array Unique

*Each move adds 1 to one element; find the fewest moves that make all values distinct; n up to 10^5, values up to 10^5.*

**The attempt.** Sort; for each value, walk upwards to the next unused number using a set, and add the distance to the moves. Correct on every example, and then a time-out on a test with 10^5 equal values.

**Measure it.** On all-equal inputs, 2,000 values took about a quarter of a second and 4,000 about a second: doubling n quadrupled the time, so it is quadratic, and 10^5 values would take over ten minutes.

**Find the step.** Restate, examples, brute force and correctness were fine. The **optimise** step failed: every walk re-checks numbers already known to be taken, the same repeated work each time, and the question "what am I recomputing?" was never asked.

**Re-derive without looking.** After sorting, the final values are strictly increasing, and each one is either the value itself (if it is free) or one more than the previous final value. So carry the previous final value: target = max(x, previous target + 1). One pass after sorting: O(n log n).

**The card.** "When values must become distinct by only increasing (or only decreasing) them: sort, then each target is max(own value, previous target + 1); carry the previous target instead of searching for a free slot."

**Transfer test: 1647 Minimum Deletions to Make Character Frequencies Unique.** Deleting characters lowers letter counts, which must become distinct (zero may repeat). Apply the card downwards: sort the counts in decreasing order; each target is min(count, previous target - 1), never below 0; add count - target to the deletions. "aaabbbcc" has counts 3, 3, 2, which become 3, 2, 1 with two deletions. The card worked on a new problem, so it is a real insight.

## Cost

945: O(n log n) to sort plus O(n) for the pass. 1647: O(n) to count plus sorting at most 26 counts. The post-mortem itself takes ten to fifteen minutes; more than that turns into rereading.

## When to use it

After every Stuck and every Brute only result, and after any wrong submission that took more than a few minutes to fix. Combine it with the error log: the category says what kind of mistake it was, the post-mortem says which step and what the missing insight is.

## Worked trace

The re-derived pass on `[3, 2, 1, 2, 1, 7]`, sorted to `[1, 1, 2, 2, 3, 7]`.

```steps
x = 1: nothing taken yet, target = {{1}}, no moves; next free value 2
    targets 1                   moves 0
---
x = 1: 1 is taken, target = max(1, 2) = {{2}}, one move; next free 3
    targets 1 2                 moves {{1}}
---
x = 2: target = max(2, 3) = {{3}}, one move; next free 4
    targets 1 2 3               moves 2
---
x = 2: target = max(2, 4) = {{4}}, two moves; next free 5
    targets 1 2 3 4             moves {{4}}
---
x = 3: target = max(3, 5) = {{5}}, two moves; next free 6
    targets 1 2 3 4 5           moves {{6}}
---
x = 7: 7 is free, target = {{7}}, no moves. Answer {{6}}
    targets 1 2 3 4 5 7         moves 6
```

## Template

```python
from collections import Counter


def min_increment_slow(nums):
    """The failed attempt, kept as an oracle: walk each value up to a free number. O(n^2) on equal values."""
    used, moves = set(), 0
    for x in sorted(nums):
        y = x
        while y in used:
            y += 1
        used.add(y)
        moves += y - x
    return moves


def min_increment_for_unique(nums):
    """945: sort; each target is max(itself, previous target + 1). O(n log n)."""
    moves, nxt = 0, -1                 # nxt: the smallest value still free for the next element
    for x in sorted(nums):
        target = max(x, nxt)
        moves += target - x
        nxt = target + 1
    return moves


def min_deletions(s):
    """1647: the same card, downwards: sort counts high to low; target = min(count, previous - 1) >= 0."""
    deletions, cap = 0, float("inf")
    for c in sorted(Counter(s).values(), reverse=True):
        target = max(0, min(c, cap))
        deletions += c - target
        cap = target - 1 if target > 0 else 0
    return deletions


assert min_increment_for_unique([3, 2, 1, 2, 1, 7]) == min_increment_slow([3, 2, 1, 2, 1, 7]) == 6
assert min_deletions("aaabbbcc") == 2 and min_deletions("ceabaacb") == 2
```

## Pitfalls

- **"I should have known X."** Not actionable. Name the step and the question you skipped.
- **A card too specific to transfer.** "945: use max(prev + 1)" helps with 945 only; the condition ("values must become distinct by increasing them") is what lets it fire on 1647.
- **Reading the whole solution.** Read one hint or one paragraph, close it, and re-derive the rest; otherwise the insight is borrowed, not found.
- **Never testing the card.** An insight that has not solved a second problem is a hypothesis.

## Check yourself

Q: You wrote a DP that passed every example and failed a hidden test with n = 1. Which step of the loop failed?
A: Test (and possibly examples): the case n = 1 was never run. The fix is in the testing habit (sizes 0, 1, 2 every time), not in the DP.

Q: What does the 945 pass return for `[0, 0, 0, 5]`, and how?
A: 3. Sorted, the targets are 0, 1, 2 and then 5, which is free: moves 0 + 1 + 2 + 0 = 3.

Q: Rewrite the card "945: sort and take the max" so that it transfers.
A: "When values must become pairwise distinct and each may only move in one direction, sort them in that direction and give each the nearest allowed value next to the previous target: max(x, previous + 1) for increases, min(x, previous - 1) for decreases. Carry the previous target instead of searching for a free value."

## Lab

- **1846 Maximum Element After Decreasing and Rearranging (bank).** Apply the card's move (sort, then carry the previous target) before reading anything else; here each value may only decrease and neighbours may differ by at most 1. Expected: 4 for `[5, 1, 3, 3]` and 3 for `[7, 7, 7]`.
- **1578 Minimum Time to Make Rope Colorful (bank).** If your first attempt fails, write the post-mortem table: the step, the missing insight, the card. Expected: 1 for colours `"aaba"` with times `[3, 1, 2, 5]`, and 5 for `"abbbc"` with `[1, 4, 2, 3, 5]`.

> [!know]
> You now know how to find the exact step where an attempt failed and turn the missing insight into a card that transfers.

=== lab | Timed mock: two unseen problems in sixty minutes | 75 min
goal: Solve two unseen, unlabelled problems in 60 minutes with the full solving loop, write a post-mortem, and compare your reasoning with the derivations in the answer key

Two stretch-level problems from the bank, chosen because they appear in no practice set of this guide. They are restated below in plain words; do not open their pages on the judge or look at their tags until the post-mortem is written.

**Problem A (1383 Maximum Performance of a Team).** There are n engineers (n up to 10^5), each with a speed (up to 10^5) and an efficiency (up to 10^8). Choose at most k of them, at least one, to maximise the team's performance: the sum of the chosen speeds multiplied by the smallest efficiency among them. Return the maximum modulo 10^9 + 7. Example: speeds [2, 10, 3, 1, 5, 8], efficiencies [5, 4, 3, 9, 7, 2], k = 2 gives 60.

**Problem B (2366 Minimum Replacements to Sort the Array).** An array holds n positive integers (n up to 10^5, values up to 10^9). One operation replaces an element, in place, by two positive integers that add up to it. Find the fewest operations that make the array non-decreasing. Example: [3, 9, 3] needs 2 (9 becomes 3, 6 and then 3, 3, 3).

## Steps

1. Prepare a blank file for each problem, a 60-minute timer and the `Session` helper from the timed-sessions card. No hints, no notes, no judge pages.
2. Budget 30 minutes per problem. For each, follow the loop aloud or on paper: restate, constraints to a target complexity, examples by hand, brute force with its cost, then optimise, prove, code and test.
3. Write a brute force for each problem first and keep it: use it to stress-test your fast version on small random inputs before the timer ends.
4. At minute 30, move to the second problem whatever the state of the first; at minute 55, stop coding and test what you have.
5. When the timer ends, write the five-line post-mortem for each problem. Only then open the answer key below, one question at a time, and compare your derivation step by step.
6. Mark both problems in your own journal as Solved, Brute only or Stuck, add any missing insight as a card, and schedule re-solves.

## What you should see

- Two brute forces that work on small inputs within the first 15 minutes of each problem. If not, the first step of your next session is "state the brute force and its cost by minute 10".
- For A, the key moment is fixing one quantity (the smallest efficiency) so the rest becomes "pick the fastest". For B, it is working from the right end, where the last element sets a cap. If you got neither, that is normal for stretch problems: the post-mortem and the re-solve are where the value is.
- Your post-mortems name concrete changes, and your own answers to the questions below match the key on at least the brute force and the target complexity.

## Answer key

Q: Problem A: what is the brute force, and which tempting greedy ideas fail?
A: The brute force tries every team of 1 to k engineers: up to C(n, k) teams, hopeless beyond n of about 20, but fine as an oracle. "Take the k fastest" fails: with speeds [10, 1, 1], efficiencies [1, 10, 10] and k = 2, the two fastest give (10 + 1) × 1 = 11, while the two efficient engineers give (1 + 1) × 10 = 20. "Take the k largest speed × efficiency products" fails for the same reason: the minimum efficiency couples the whole team.

Q: Problem A: what is the key idea?
A: Fix the weakest member. If engineer e is the team member with the smallest efficiency, the performance is eff(e) × (sum of speeds), and every other member must have efficiency at least eff(e). For that fixed e, the best team is e plus the k - 1 fastest engineers among those with efficiency at least eff(e). Visiting engineers in decreasing order of efficiency makes "those with efficiency at least eff(e)" exactly the engineers seen so far.

Q: Problem A: what is the algorithm, why is it correct, and what does it cost?
A: Sort by efficiency, highest first. Keep a min-heap of the kept speeds and their running sum; for each engineer push the speed, and if the heap holds more than k speeds pop the smallest. After each step, candidate = sum × current efficiency; keep the maximum and take the modulus only at the end. On the example with k = 2 the candidates are 9, 42, 35, 60, 45 and 36, so the answer is 60. When the current engineer's own speed is the one popped, the candidate uses a team that does not contain them, but every kept engineer has efficiency at least the current one, so the candidate never exceeds a real team's performance; and the optimal team is counted exactly when its weakest member is processed. Cost: O(n log n) for the sort plus O(n log k) for the heap, O(n) space.

Q: Problem B: what do small cases and the last element tell you?
A: The last element never needs to be split: splitting it can only make the end of the array smaller, which makes the condition harder for everything before it. So scan from the right with a cap, the largest value the current element's pieces may have: initially the last element. Any element at most the cap stays whole and becomes the new cap.

Q: Problem B: how should an element x larger than the cap be split, and why is that optimal?
A: Each piece must be at most the cap, so x needs at least p = ceil(x / cap) pieces, which costs p - 1 operations; fewer is impossible. Among all splits into p pieces, the most even one makes the smallest piece (the first one, which becomes the new cap) as large as possible: x // p. A larger cap is never worse for the elements further left, so taking the fewest pieces and the most even split is optimal at every step. Example: x = 10 with cap 3 needs 4 pieces (3 operations), split as 2, 2, 3, 3, so the new cap is 2.

Q: Problem B: what is the final algorithm and its cost, and what are the traps?
A: ops = 0, cap = last element; for x from right to left (excluding the last): if x <= cap, cap = x; otherwise p = (x + cap - 1) // cap, ops += p - 1, cap = x // p. O(n) time, O(1) space. Traps: scanning from the left (the right end is the only fixed point); using x // cap pieces instead of the ceiling; setting the new cap to cap instead of x // p (the pieces cannot all equal the old cap unless it divides x); worrying about overflow, which Python avoids but C++ must handle (up to 10^9 operations per element, so use 64-bit integers for the total).

> [!example]
> Reference solutions, checked against brute force on thousands of random small inputs. Read them only after your post-mortem.
>
> ```python
> import heapq
>
>
> def max_performance(n, speed, efficiency, k):
>     """1383: fix the weakest member; keep the k fastest seen so far in a min-heap."""
>     best = total = 0
>     fastest = []
>     for eff, spd in sorted(zip(efficiency, speed), reverse=True):
>         heapq.heappush(fastest, spd)
>         total += spd
>         if len(fastest) > k:
>             total -= heapq.heappop(fastest)
>         best = max(best, total * eff)
>     return best % (10**9 + 7)
>
>
> def minimum_replacement(nums):
>     """2366: scan from the right; split x into ceil(x / cap) pieces as evenly as possible."""
>     ops, cap = 0, nums[-1]
>     for x in reversed(nums[:-1]):
>         if x > cap:
>             parts = (x + cap - 1) // cap
>             ops += parts - 1
>             cap = x // parts
>         else:
>             cap = x
>     return ops
>
>
> assert max_performance(6, [2, 10, 3, 1, 5, 8], [5, 4, 3, 9, 7, 2], 2) == 60
> assert minimum_replacement([3, 9, 3]) == 2
> ```
