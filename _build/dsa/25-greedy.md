---
key: greedy
name: Greedy algorithms and exchange arguments
stage: strategy
summary: Commit to one locally best choice at a time, but only after proving it safe with an exchange argument or a stays-ahead argument; otherwise find the counterexample and fall back to dynamic programming.
why: Greedy algorithms are the shortest and fastest solutions you will ever write, usually a sort and one pass, and they are wrong more often than any other technique, because a rule that "obviously" works passes the examples and fails on a case nobody tried. This module makes greedy a disciplined decision instead of a guess: try to break the rule with small cases and a brute-force search, then prove it with one of two short proof patterns, and use DP when neither works. The same reasoning sits inside software you use daily: Huffman coding in zip, gzip and PNG, earliest-deadline-first scheduling in the Linux kernel, Kruskal's, Prim's and Dijkstra's algorithms, and Git's default "greedy" diff.
outcomes:
- Explain what makes an algorithm greedy and the two properties that make a greedy choice safe
- Prove a greedy rule with an exchange argument or a "greedy stays ahead" induction in a few sentences
- Break plausible greedy rules with hand-made counterexamples and with an automatic brute-force search
- Solve reach, jump, running-balance, sort-key and heap-based greedy problems in O(n) or O(n log n)
- Build optimal prefix codes with Huffman's algorithm and heapq, and explain how DEFLATE stores them
- Decide between greedy and DP for a new problem, and derive a greedy from a DP when one option always dominates
cues:
- "Minimum number of" or "maximum number of" with a natural order (by end time, deadline, size, ratio) suggesting itself
- Reach, jump, fuel, balance or coverage questions that look answerable in one left-to-right pass
- Repeatedly take the cheapest, largest or most urgent option among those currently available
- Large n (10^5 or more) where a quadratic DP is too slow and the structure suggests local choices cannot hurt
traps:
- Trusting a rule because it passes the examples: always attack it with small cases or a brute-force search first
- Sorting by the wrong key: start instead of end, value instead of value per weight, or a comparator that is not a consistent order
- Assuming largest-coin-first works for any coins: it does for 1, 2, 5, 10, 20, 50, but not for 1, 3, 4
- Forgetting the feasibility check, such as the total-gas test or the stuck index in a jump game
- "Proving" that the greedy choice is good instead of proving that some optimal solution contains it
systems:
- Huffman coding inside DEFLATE (zip, gzip, PNG and HTTP compression): RFC 1951 stores canonical Huffman codes as code lengths only
- Linux's SCHED_DEADLINE scheduling class runs tasks by earliest deadline first (EDF), a greedy rule with an exchange-argument proof
- Minimum spanning trees (Kruskal, Prim) and Dijkstra's shortest paths are greedy algorithms proved safe by cut and exchange arguments
- Git's default diff (Myers) is documented as "the basic greedy diff algorithm"; patience and histogram trade minimality for readability
further:
- Chapter · 45 min | Erickson, Algorithms ch. 4: Greedy Algorithms (tape storage, class scheduling, Huffman codes, PDF pages 1-11) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/04-greedy.pdf#page=1
- Notes · 30 min | Kleinberg and Tardos (Wayne's slides): Greedy Algorithms I, coin changing, interval scheduling, lateness, caching | https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/04GreedyAlgorithmsI.pdf#page=3
- Chapter · 40 min | Competitive Programmer's Handbook, chapter 6: Greedy algorithms (PDF pages 67-74) | https://cses.fi/book/book.pdf#page=67
- Article · 20 min | USACO Guide: Greedy algorithms with sorting, 'When Greedy Fails' | https://usaco.guide/silver/greedy-sorting#when-greedy-fails
bank: greedy
---

=== primer | What makes an algorithm greedy, and when can you trust it? | 11 min
goal: Recognise the shape of a greedy algorithm and state the two properties that must hold before you trust it
tag: greedy-basics | Greedy choice
link: USACO Guide: Greedy algorithms with sorting | https://usaco.guide/silver/greedy-sorting#introduction | 10 min: 'Introduction' and 'Example - Studying Algorithms': a sort-then-take greedy with its short justification
practice: 455, 860

> [!key]
> A **greedy algorithm** builds its answer one irrevocable choice at a time, each time taking the option that looks best by a simple rule. It is usually a sort plus one pass, so it is fast and short. It is correct only when two things hold: some optimal solution contains the greedy choice (the **greedy-choice property**), and what remains after that choice is a smaller instance of the same problem (**optimal substructure**). Your job is the argument, not the code.

## Intuition

A cashier making 48 pence of change picks the largest coin that fits, again and again: 20, 20, 5, 2, 1. Nobody draws a search tree; each step is final. With today's British coins that always gives the fewest coins. Give the same cashier the pre-1971 coins (1, 3, 6, 12, 24 and 30 pence) and the same rule pays 48 as 30 + 12 + 6, three coins, when two 24-pence florins would do. The rule did not change; the structure under it did. That is greedy in one picture: wonderful when the structure supports it, silently wrong when it does not.

Compare the three strategies of this stage on the same decision tree. **Backtracking** explores every branch. **Dynamic programming** explores every branch but shares identical subtrees. **Greedy** walks down **one** branch and never looks back. It is the cheapest, and it is right only if you can show the branch it picks always leads to an optimum.

## How it works

Every greedy algorithm has the same four parts:

1. **Candidates**: the items, intervals, coins or moves you can choose from.
2. **A selection rule**: an order (sort key) or a "best right now" test (often a heap).
3. **A feasibility check**: can this candidate be added without breaking the constraints?
4. **Commit**: add it and never reconsider.

### Fractional knapsack: a greedy that works

You may take any fraction of each item (flour, fuel, bandwidth). Sort by value per unit of weight and take the densest items first, whole while they fit, then a fraction of the next one. Why is that safe? Suppose an optimal load carries less of the densest item than it could. Then it carries some weight of a less dense item; swap that weight for the same weight of the densest item. The total weight is unchanged and the value does not go down. Repeat until the load agrees with greedy: greedy is optimal. This is an **exchange argument**, the main proof tool of the next card.

### 0/1 knapsack: the same rule fails

Make the items indivisible and the rule breaks: with a 10 kg bag, a 6 kg item worth 30 and two 5 kg items worth 20 each, density first takes the 6 kg item, after which nothing fits (30), while the two 5 kg items give 40. The exchange step above needed to move *part* of an item, which is no longer allowed. The previous module solved this with a capacity table.

### Greedy as a pruned DP

Another way to see a correct greedy: write the DP, which takes the best of several options at each step, then prove that one option *always* wins. The max over options collapses to that one option, and the table collapses to a single pass. The last card of this module does exactly this for a stock-trading problem.

## Cost

Typical costs come from the selection rule: sorting is O(n log n) and the pass after it O(n); a heap of candidates costs O(log n) per push or pop, O(n log n) in total; some greedy algorithms need no sort and run in O(n) with O(1) memory (reach and balance problems). Compare that with the O(n x C) or O(n^2) DPs the same problems would otherwise need.

## When to use it

| Signal | Greedy is promising | Be suspicious |
|---|---|---|
| Choices | one natural order; taking the best now never blocks a better later | an early choice changes what is possible later (capacity, compatibility) |
| Items | divisible, or all the same size | indivisible with different sizes and values |
| Constraints | n up to 10^5 or 10^6, no small numeric bound for a table | small n or a small capacity, where DP is affordable anyway |
| Evidence | a two-line exchange argument | "it works on the examples" |

## Worked trace

Fractional knapsack with a 10 kg bag and items A (6 kg, value 30), B (5 kg, value 20), C (5 kg, value 20).

```steps
Sort by value per kilogram: A is worth 5 per kg, B and C 4 per kg each
    item   kg  value  per kg
    A       6     30     5.0
    B       5     20     4.0
    C       5     20     4.0
---
Take all of A: it fits. Room left: 4 kg, value 30
    item   kg  value  per kg   taken
    {{A       6     30     5.0     6 kg}}
    B       5     20     4.0
---
B does not fit whole: take 4 of its 5 kg, worth 4/5 of 20 = 16. Room left: 0
    item   kg  value  per kg   taken
    A       6     30     5.0     6 kg
    {{B       5     20     4.0     4 kg}}
---
The bag is full: total value 30 + 16 = 46, the best possible when items can be split
    total  46.0
---
Same items, no splitting (0/1): density order takes A and then nothing fits, value 30. Taking B and C gives 40
    greedy 0/1: {{30}}     optimal 0/1: {{40}}
```

## Template

```python
def fractional_knapsack(items, cap):
    """items: (weight, value) pairs; you may take any fraction of an item. Best total value."""
    total = 0
    for w, v in sorted(items, key=lambda it: it[1] / it[0], reverse=True):
        if cap == 0:
            break
        take = min(w, cap)                 # all of it, or whatever still fits
        total += v * take / w
        cap -= take
    return total
```

`fractional_knapsack([(6, 30), (5, 20), (5, 20)], 10)` returns 46.0. When exact ratios matter (ties, large integers), sort with `key=lambda it: Fraction(it[1], it[0])` from the `fractions` module, or compare by cross-multiplication.

## Pitfalls

- **Testing instead of proving.** A rule that passes five examples is a hypothesis. Try to break it (the counterexample card) before you write it.
- **The right rule on the wrong problem.** Value per weight is optimal for divisible items and wrong for indivisible ones; read the statement for "fraction", "at most once", "any number of times".
- **Ties.** If two candidates look equally good, the proof must cover either choice, or you must state the tie-break that makes it work.
- **Floating-point keys.** Ratios like 1/3 and 2/6 can compare unequal in floats; use `Fraction` or cross-multiplication when ties matter.

## Check yourself

Q: Items (4 kg, 20), (3 kg, 9) and (2 kg, 10), bag of 5 kg, fractions allowed. What does the greedy take and what is the value?
A: Densities are 5, 3 and 5. It takes the 4 kg item (20) and then 1 kg of the 2 kg item (5), or the 2 kg item first and 3 of the 4 kg item; either way the value is 25. The 3 kg item (density 3) is never touched.

Q: In one sentence each, what are the greedy-choice property and optimal substructure for fractional knapsack?
A: Greedy choice: some optimal load contains as much of the densest item as fits (proved by swapping weight from a less dense item to it). Optimal substructure: after taking that, the rest is a fractional knapsack on the remaining items with the remaining capacity, and an optimal answer to it completes an optimal answer to the whole.

Q: A colleague sorts the items by value (largest first) for fractional knapsack. Give an input where it loses.
A: Bag of 2 kg, items (2 kg, 3) and (1 kg, 2). By value it takes the 2 kg item (3). By density (2 per kg vs 1.5) the best is the 1 kg item plus half of the other: 2 + 1.5 = 3.5.

## Lab

- **455 Assign Cookies.** Decide which child each cookie should go to; argue why giving the smallest cookie that satisfies the least greedy child is never a mistake. Expected: O(n log n + m log m) time, O(1) extra space; greed factors [1, 4, 2, 3] with cookies [3, 1, 2] satisfy 3 children; greed [5, 6] with cookies [4, 4, 4] satisfy 0.
- **860 Lemonade Change.** Keep counts of the notes you hold; when a 20 arrives, decide which change to give first and say why. Expected: O(n) time, O(1) space; [5, 5, 5, 5, 10, 20, 10] is possible only if the 20 is changed with 10 + 5 (answer true); [5, 10, 10] is false.

> [!know]
> You now know what makes an algorithm greedy, why it is fast, and which two properties you must establish before trusting it.

=== primer | How do you prove a greedy choice is safe: exchange arguments and staying ahead? | 15 min
goal: Write a short exchange-argument proof and a "greedy stays ahead" induction, and know which one fits a given problem
tag: greedy-proof | Exchange and stays-ahead proofs
link: Erickson, Algorithms ch. 4: Greedy Algorithms (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/04-greedy.pdf#page=1 | 25 min: 'Storing Files on Tape' and 'Scheduling Classes' (PDF pages 1-6), two complete exchange proofs, then 'General Pattern' on page 6
link: Kleinberg and Tardos slides: Greedy Algorithms I (PDF) | https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/04GreedyAlgorithmsI.pdf#page=25 | 10 min: slides 25-33, minimising lateness with an inversion-by-inversion exchange, then the summary of proof strategies on slide 33
practice: cses:1630

> [!key]
> Two proof patterns cover almost every greedy you will meet. **Exchange argument:** take any optimal solution that differs from the greedy one, find the first difference, and swap in the greedy choice without making the solution worse or infeasible; repeating this turns the optimum into the greedy answer, so greedy is optimal. **Greedy stays ahead:** pick a measure of progress and show by induction that after every step the greedy partial solution is at least as good as any other solution's after the same number of steps.

## Intuition

Several people queue for one photocopier, each with a job of known length, and you want the total waiting (the sum of everyone's finishing times) as small as possible. Imagine two neighbours in the queue where the longer job goes first. Swap just those two: the people before and after them are unaffected, the short job now finishes much earlier, and the long job finishes exactly when the pair used to finish. The total can only go down. Keep swapping such neighbours and you arrive at "shortest job first". That small swap is an exchange argument.

## How it works

### Exchange argument: shortest job first

Claim: ordering jobs by increasing length minimises the sum of finishing times.

1. Take any order that is not sorted. Then somewhere a job of length x stands directly before a job of length y with x > y (an **adjacent inversion**).
2. Swap them. Everyone else finishes at the same time. Before the swap the pair finished at T + x and T + x + y; after it, at T + y and T + x + y. The sum drops by x - y > 0.
3. So every unsorted order can be strictly improved, hence no unsorted order is optimal (if lengths tie, swapping changes nothing, so a sorted order is still optimal). Each swap removes one inversion, so the process ends, at the sorted order.

The ingredients are always the same: a solution that differs from greedy, a **local swap** that keeps it **feasible**, and a computation showing the swap is **no worse**.

### Greedy stays ahead: interval scheduling

Claim: picking the compatible interval with the **earliest end** at each step gives the most pairwise-disjoint intervals (the intervals module proved this with an exchange; here is the other pattern).

1. Let greedy choose g1, g2, ..., gk and let any other valid choice be o1, o2, ..., om, both sorted by end time.
2. Measure: the end time of the r-th chosen interval. Claim: end(g_r) <= end(o_r) for every r <= k.
3. Base: g1 has the earliest end of all intervals, so end(g1) <= end(o1).
4. Step: o_{r+1} starts after o_r ends, which is at or after g_r ends (induction hypothesis). So o_{r+1} was still available when greedy made its (r + 1)-th choice, and greedy took the earliest-ending available interval: end(g_{r+1}) <= end(o_{r+1}).
5. Conclusion: if m > k, then o_{k+1} starts after end(o_k) >= end(g_k), so it was available when greedy stopped. But greedy only stops when nothing is available. Contradiction, so k >= m.

### Which pattern?

| Use | When the greedy answer is | Example |
|---|---|---|
| Exchange argument | an order or a set you can locally modify | shortest job first, fractional knapsack, Huffman, Smith's rule |
| Stays ahead | built step by step with a natural measure of progress | interval scheduling, jump games, minimum jumps |

### A four-sentence proof template

"Let O be an optimal solution that agrees with greedy G on the first i choices, with i as large as possible. Let g be G's next choice and o be O's. Replacing o by g in O keeps it feasible because ___ and does not make it worse because ___. This gives an optimal solution agreeing with G on i + 1 choices, contradicting the choice of i, so O = G." Filling the two blanks is the whole proof, and if you cannot fill them, suspect the rule.

## Cost

Proofs cost nothing at run time, but they decide what you may run: the proven algorithms here are a sort plus a pass, O(n log n) time and O(1) extra space beyond the sort, against O(n!) orders or O(2^n) subsets for brute force.

## When to use it

Write the proof whenever you are about to submit or ship a greedy rule. In an interview, say the exchange in two sentences. In production code, put it in a comment next to the sort key, because that key is exactly what a later change will "simplify". Before proving, spend two minutes trying to break the rule; the next card shows how.

## Worked trace

Adjacent swaps on the queue of job lengths [5, 2, 3]: each swap removes one inversion and lowers the total of finishing times by (longer - shorter).

```steps
Order 5, 2, 3: finishing times 5, 7, 10. Total 22. The pair (5, 2) is an adjacent inversion
    order      {{5}}  {{2}}   3
    finishes    5     7    10      total 22
---
Swap 5 and 2: the job of length 2 now finishes at 2, the 5 at 7 (as the pair did before). Total drops by 5 - 2 = 3
    order       2  {{5}}  {{3}}
    finishes    2     7    10      total 19
---
Next inversion (5, 3): swap. The 3 finishes at 5 instead of 10, the 5 at 10. Total drops by 5 - 3 = 2
    order       2     3     5
    finishes    2     5    10      total {{17}}
---
No inversions remain: this is the sorted order, and no other order of these jobs has a smaller total
    shortest job first: 2, 3, 5  ->  17
```

## Template

```python
def total_completion_time(lengths):
    """Shortest job first: the order that minimises the sum of finishing times."""
    clock = total = 0
    for t in sorted(lengths):
        clock += t                         # this job finishes at clock
        total += clock
    return total


def max_disjoint(intervals):
    """Most pairwise-disjoint half-open intervals [s, e): earliest end first."""
    count, free_at = 0, float("-inf")
    for s, e in sorted(intervals, key=lambda iv: iv[1]):
        if s >= free_at:                   # compatible with everything chosen so far
            count += 1
            free_at = e
    return count
```

Both are stress-tested against brute force (every permutation, every subset) on random small inputs in this module's verification.

## Pitfalls

- **Proving the wrong statement.** "The greedy choice is a good choice" proves nothing. You must show that *some optimal solution* makes it.
- **Forgetting feasibility after the swap.** Swapping an interval in may create an overlap; swapping a course in may break a deadline. Say why the swapped solution is still valid.
- **Strict versus non-strict.** With ties, a swap may leave the cost unchanged. Prove "no worse", not "strictly better", unless you need strictness.
- **Stress tests are not proofs.** A thousand random passes make a rule plausible; one failure kills it. Use tests to find counterexamples and proofs to rule them out.

## Check yourself

Q: What is the minimum total of finishing times for jobs of lengths [4, 1, 3]?
A: 13. Sorted: 1, 3, 4 finish at 1, 4 and 8, and 1 + 4 + 8 = 13.

Q: In the stays-ahead proof, which step uses the fact that greedy picks the earliest *end* rather than, say, the earliest start?
A: The induction step: o_{r+1} is available to greedy, and because greedy takes the available interval that ends first, end(g_{r+1}) <= end(o_{r+1}). With "earliest start", nothing guarantees that greedy's interval ends early, and the chain of inequalities breaks (one long interval starting first can block several short ones).

Q: Each task has a duration and a deadline, and finishing a task at time f earns (deadline - f), which may be negative. In which order should you do the tasks?
A: Shortest first. The total reward is the sum of deadlines (fixed, whatever the order) minus the sum of finishing times, so you only need to minimise the sum of finishing times: the shortest-job-first exchange argument, with deadlines playing no role.

## Lab

- **cses:1630 Tasks and Deadlines** (stretch). Write the reward as a sum you can split, then reuse the exchange argument from this card. Expected: O(n log n) time; tasks (duration, deadline) (6, 10), (8, 15), (5, 12) give 2; tasks (4, 3), (1, 9), (2, 4) give 5. Use 64-bit integers in C++: the total can exceed 2^31.
- **Stress-test the stays-ahead claim.** Compare `max_disjoint` with a brute force over all subsets for 1,000 random sets of up to 7 intervals. Expected: no mismatch. Then change the sort key to the start time and watch the tester find a failure within a few dozen cases.

> [!know]
> You now know how to prove a greedy rule with an exchange argument or a stays-ahead induction, and how to tell which one a problem needs.

=== primer | How do you find a counterexample that breaks a greedy rule? | 13 min
goal: Break plausible greedy rules by hand and with a brute-force search on random small inputs, and decide coin systems exactly
tag: greedy-counter | Counterexample search
link: Kleinberg and Tardos slides: Greedy Algorithms I (PDF) | https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/04GreedyAlgorithmsI.pdf#page=3 | 10 min: slides 3-8 on the cashier's algorithm (the U.S. postage counterexample on slide 6, the proof for U.S. coins on slide 8) and slide 11, the quiz of interval-scheduling rules
link: USACO Guide: When greedy fails | https://usaco.guide/silver/greedy-sorting#when-greedy-fails | 5 min: the coin change and knapsack examples where the natural greedy is wrong

> [!key]
> Attack a greedy rule before you prove it. First try **small, adversarial cases by hand** (ties, one item that blocks two, a small item that enables a big one). Then let the computer search: a **brute force** that is obviously right, a **generator** of random small inputs, and a loop that stops at the **first disagreement**, trying the smallest sizes first so the failure it reports is near-minimal. One counterexample kills a rule; passing thousands of tests only makes it plausible.

## Intuition

"Largest coin first" feels universal because we grew up with coin systems designed for it. Try the coins 1, 3 and 4 and the amount 6: greedy pays 4 + 1 + 1 (three coins), while 3 + 3 uses two. Found in ten seconds, and it tells you *why* the rule fails: grabbing the 4 left a remainder (2) that only small coins can pay. Most broken greedy rules fail for this reason, an early choice leaves an awkward remainder, and small cases expose it quickly.

## How it works

### By hand: questions that break rules

- **What if the best-looking candidate blocks two others?** One long interval that starts first blocks two short ones (earliest start fails).
- **What if a short candidate sits across two long ones?** A short interval overlapping the end of one and the start of another blocks both (shortest first fails).
- **What if the best ratio leaves wasted capacity?** The 0/1 knapsack example: the densest item leaves room nothing fits into.
- **What if amounts or sizes are equal?** Ties expose rules that depend on an unstated tie-break.

### Coin systems: deciding exactly

A coin system is **canonical** when largest-first is always optimal. Real examples of non-canonical systems: the old Indian 5, 10, 20 and 25 paise (40 = 25 + 10 + 5 by greedy, 20 + 20 optimally), pre-1971 British coins 1, 3, 6, 12, 24, 30 pence (48 = 30 + 12 + 6 versus 24 + 24), and U.S. postage stamps (Kleinberg and Tardos: with 1, 10, 21, 34, 70 and 100, greedy pays 140 with eight stamps, 100 + 34 + six 1s, instead of 70 + 70). You do not have to test every amount forever: Kozen and Zaks (1994) showed that if greedy fails for a system containing 1, it already fails below the sum of the two largest coins. So a DP up to that bound decides the question exactly, and the template below does that.

### Automatic search

The loop is the stress tester from the correctness module, pointed at a rule instead of a bug:

1. **Oracle:** a brute force over every subset, order or coin combination. Slow is fine; obviously correct is the point.
2. **Generator:** random small inputs, sizes 2, 3, 4, ... in that order, so the first failure is about as small as possible. Avoid ties in the rule's key unless ties are what you want to test.
3. **Compare and stop** at the first disagreement; print it.
4. **Shrink** if needed: remove items one at a time while the failure persists.

Random search finds most broken rules within seconds, but not all: "pick the interval with the fewest overlaps" survives random sets of up to 8 intervals and still fails on a carefully built 11-interval instance. Absence of a counterexample is evidence, not proof. The lab runs this search on coins and on three interval-scheduling problems.

## Cost

The oracle is exponential (2^n subsets, n! orders), so keep inputs to roughly n <= 8 to 10; a few thousand trials then take seconds. Deciding a coin system costs O(k x (c_max + c_second)) for k coins with the DP up to the Kozen and Zaks bound.

## When to use it

Every time you invent or remember a greedy rule and cannot yet prove it, and every time a proof attempt gets stuck on one of its blanks. It is the cheapest way to choose between greedy and DP: if the search finds a counterexample, you have saved yourself a wrong submission; if it finds none, go and write the proof.

| Rule | Problem | Verdict from search |
|---|---|---|
| Largest coin first | coins 1, 5, 10, 25 or 1, 2, 5, ..., 200 | never fails (canonical) |
| Largest coin first | coins 1, 3, 4 | fails at 6 |
| Earliest end first | most disjoint intervals | never fails (proved in the previous card) |
| Earliest start, shortest first | most disjoint intervals | fail with three intervals |
| Any single order | weighted intervals (maximise total weight) | fails: needs DP |

## Worked trace

`smallest_counterexample([1, 3, 4])` scans amounts upwards, comparing largest-first with the DP oracle.

```steps
The bound: the two largest coins are 3 and 4, so if greedy ever fails it fails below 7
    coins 1, 3, 4        amounts to check: 1 .. 6
---
Amounts 1 to 3: greedy and the DP agree (1; 1+1; 3)
    amount    1  2  3
    greedy    1  2  1
    optimal   1  2  1
---
Amounts 4 and 5: still equal (4; 4+1)
    amount    1  2  3  4  5
    greedy    1  2  1  1  2
    optimal   1  2  1  1  2
---
Amount 6: greedy takes 4, then 1, then 1 (three coins); the DP finds 3 + 3 (two). First disagreement
    amount    1  2  3  4  5  {{6}}
    greedy    1  2  1  1  2  {{3}}
    optimal   1  2  1  1  2  {{2}}
---
Return 6. The system 1, 3, 4 is not canonical; use the coin-change DP for it
    smallest counterexample: 6
```

## Template

```python
def greedy_change(coins, amount):
    """Largest coin first. Returns the number of coins, or None if it gets stuck."""
    count = 0
    for c in sorted(coins, reverse=True):
        count += amount // c
        amount %= c
    return count if amount == 0 else None


def optimal_change(coins, amount):
    """Fewest coins by DP (the oracle). None if the amount cannot be made."""
    INF = float("inf")
    need = [0] + [INF] * amount
    for a in range(1, amount + 1):
        need[a] = min((need[a - c] + 1 for c in coins if c <= a), default=INF)
    return need[amount] if need[amount] != INF else None


def smallest_counterexample(coins):
    """Smallest amount where largest-coin-first is not optimal, or None if it never fails.
    Kozen and Zaks: if greedy ever fails, it fails below the sum of the two largest coins."""
    top = sorted(coins)[-2:]
    for amount in range(1, sum(top)):
        if greedy_change(coins, amount) != optimal_change(coins, amount):
            return amount
    return None
```

The verification for this module checked the bound empirically too: on 300 random systems of two to five coins containing 1, the first failure found by scanning amounts up to 400 always lay below the sum of the two largest coins.

## Pitfalls

- **Inputs too large for the oracle.** If the brute force cannot finish, the search tests nothing. Small sizes find almost every counterexample anyway.
- **A buggy oracle.** Test it on hand-computed cases first; a wrong oracle "finds" counterexamples that are not.
- **Ties hiding the real failure.** A rule may look broken only because of an arbitrary tie-break. Filter tied inputs (or test both tie orders) before blaming the rule.
- **"It passed 10,000 random tests, so it is correct."** Structured counterexamples (like the 11-interval one) can be vanishingly rare among random inputs. Prove it.

## Check yourself

Q: With the old British coins 1, 3, 6, 12, 24 and 30 pence, what does `smallest_counterexample` return, and what do greedy and the DP pay there?
A: 48. Greedy pays 30 + 12 + 6 (three coins); the DP pays 24 + 24 (two). Every amount below 48 agrees, and the bound to check is 30 + 24 = 54.

Q: Why may `smallest_counterexample` stop at the sum of the two largest coins instead of testing every amount?
A: Because of Kozen and Zaks' theorem: for a coin system containing 1, if largest-first fails for some amount, it already fails for an amount below c_max + c_second. Checking those amounts with the DP is therefore a complete test, not a sample.

Q: Your random search of a scheduling rule has passed 50,000 random inputs of up to 8 items. What do you do next?
A: Try to prove it (exchange or stays ahead). If the proof gets stuck, the stuck step tells you what structure a counterexample needs; build that input by hand, as with the 11-interval instance for "fewest conflicts". Only a proof settles it.

## Lab

- **Decide some coin systems.** Run `smallest_counterexample` on [1, 10, 21, 34, 70, 100], [1, 5, 10, 20, 25] and [1, 2, 5, 10, 20, 50, 100, 200]. Expected: 30 (greedy 21 + nine 1s = 10 stamps, optimal 10 + 10 + 10 = 3), 40 (25 + 10 + 5 versus 20 + 20), and None (the euro and pound coins are canonical).
- **Break a rule automatically.** Write a brute force for "most disjoint intervals" and a generator of 2 to 8 random intervals, then search for the smallest input where "earliest start first" disagrees with it. Expected: a failure with three intervals, of the shape one long interval that starts first and overlaps two short disjoint ones (greedy 1, best 2). The lab after this card does this for several rules at once.

> [!know]
> You now know how to break a greedy rule by hand and with a brute-force search, and how to decide exactly whether a coin system is safe for largest-first.

=== lab | Greedy or not? Let a brute force decide | 40 min
goal: Run greedy rules against exact oracles on random small inputs for coin change and for unweighted and weighted interval scheduling, and record which rules survive
link: Wikipedia: Activity selection problem | https://en.wikipedia.org/wiki/Activity_selection_problem#Weighted_activity_selection_problem | 5 min: 'Weighted activity selection problem': why there is no greedy solution once activities carry weights, and a simple DP; part 3 below uses a faster O(n log n) version (sort by end, binary search for the last compatible job)

Three problems, several plausible greedy rules each, and one exact oracle per problem. The search tries small sizes first and stops at the first disagreement, so every counterexample it prints is close to minimal. You will see which rules survive, and one rule that survives the search but is still wrong.

## Setup

- Python 3.10 or later, standard library only. Runs in about ten seconds.
- If you built `dsakit` in the correctness module, its stress loop and shrinker can replace `hunt` below.

## Steps

1. **Predict first.** For each rule in the table under "What you should see", write down "always optimal" or "fails", and for failures guess the smallest input size.
2. Save this as `greedy_lab.py` and run it.

```python
import itertools
import random
from bisect import bisect_right

rng = random.Random(1)


# ---------- part 1: coin systems ----------
def greedy_change(coins, amount):
    count = 0
    for c in sorted(coins, reverse=True):
        count += amount // c
        amount %= c
    return count if amount == 0 else None


def optimal_change(coins, amount):
    INF = float("inf")
    need = [0] + [INF] * amount
    for a in range(1, amount + 1):
        need[a] = min((need[a - c] + 1 for c in coins if c <= a), default=INF)
    return need[amount] if need[amount] != INF else None


def smallest_counterexample(coins):
    top = sorted(coins)[-2:]
    for amount in range(1, sum(top)):
        if greedy_change(coins, amount) != optimal_change(coins, amount):
            return amount
    return None


def part1(trials=2000):
    bad, examples = 0, []
    for _ in range(trials):
        coins = sorted({1} | set(rng.sample(range(2, 50), 3)))
        x = smallest_counterexample(coins)
        if x is not None:
            bad += 1
            if len(examples) < 3:
                examples.append((coins, x, greedy_change(coins, x), optimal_change(coins, x)))
    print(f"coins: {bad / trials:.0%} of random 4-coin systems with a 1 are not greedy-safe")
    for coins, x, g, o in examples:
        print(f"  {coins}: amount {x}, greedy {g} coins, optimal {o}")
    for coins in ([1, 5, 10, 25], [1, 2, 5, 10, 20, 50, 100, 200], [1, 3, 4], [1, 3, 6, 12, 24, 30]):
        print(f"  {coins}: smallest counterexample {smallest_counterexample(coins)}")


# ---------- part 2: unweighted interval scheduling ----------
def overlaps(p, q):
    return p[0] < q[1] and q[0] < p[1]          # half-open [start, end)


def pick_by(key):
    """Static rule: scan in key order, keep an interval if it fits with everything kept."""
    def rule(ivs):
        kept = []
        for iv in sorted(ivs, key=key):
            if not any(overlaps(iv, k) for k in kept):
                kept.append(iv)
        return len(kept)
    return rule


def fewest_conflicts(ivs):
    """Dynamic rule: repeatedly keep the remaining interval that overlaps the fewest others."""
    left, kept = list(ivs), 0
    while left:
        best = min(left, key=lambda iv: (sum(overlaps(iv, o) for o in left if o is not iv), iv))
        kept += 1
        left = [o for o in left if o is not best and not overlaps(o, best)]
    return kept


def most_disjoint(ivs):
    """Brute force oracle: the largest subset with no overlaps."""
    for k in range(len(ivs), 0, -1):
        for sub in itertools.combinations(ivs, k):
            if all(not overlaps(p, q) for p, q in itertools.combinations(sub, 2)):
                return k
    return 0


def random_intervals(n, span=12):
    out = []
    for _ in range(n):
        s = rng.randrange(span)
        out.append((s, s + rng.randint(1, 6)))
    return out


def hunt(rule, oracle, make, sizes, trials=3000, keyf=None):
    """Smallest counterexample found: try small inputs first, so the first failure is near-minimal."""
    for n in sizes:
        for _ in range(trials):
            x = make(n)
            if keyf and len({keyf(iv) for iv in x}) < len(x):
                continue                       # skip ties, so the failure is the rule's fault
            if rule(x) != oracle(x):
                return x, rule(x), oracle(x)
    return None


def part2():
    rules = {"earliest end": (pick_by(lambda iv: iv[1]), lambda iv: iv[1]),
             "earliest start": (pick_by(lambda iv: iv[0]), lambda iv: iv[0]),
             "shortest first": (pick_by(lambda iv: iv[1] - iv[0]), lambda iv: iv[1] - iv[0]),
             "fewest conflicts": (fewest_conflicts, None)}
    for name, (rule, keyf) in rules.items():
        found = hunt(rule, most_disjoint, random_intervals, range(2, 9), keyf=keyf)
        print(f"{name:16}: " + (f"FAILS on {sorted(found[0])}: greedy {found[1]}, best {found[2]}"
                                if found else "no counterexample found"))


# ---------- part 3: weighted interval scheduling ----------
def best_weight(jobs):
    """DP oracle: jobs (start, end, weight); best[i] = best total using the first i jobs by end."""
    jobs = sorted(jobs, key=lambda j: j[1])
    ends = [e for _, e, _ in jobs]
    best = [0] * (len(jobs) + 1)
    for i, (s, e, w) in enumerate(jobs, 1):
        p = bisect_right(ends, s, 0, i - 1)    # jobs that end by s are compatible
        best[i] = max(best[i - 1], best[p] + w)
    return best[-1]


def weighted_by(key):
    def rule(jobs):
        kept = []
        for j in sorted(jobs, key=key):
            if not any(overlaps(j, k) for k in kept):
                kept.append(j)
        return sum(w for _, _, w in kept)
    return rule


def random_jobs(n):
    return [iv + (rng.randint(1, 9),) for iv in random_intervals(n)]


def part3():
    rules = {"earliest end": lambda j: j[1], "heaviest first": lambda j: -j[2],
             "best weight per hour": lambda j: -j[2] / (j[1] - j[0])}
    for name, key in rules.items():
        found = hunt(weighted_by(key), best_weight, random_jobs, range(2, 7), keyf=key)
        print(f"{name:20}: " + (f"FAILS on {sorted(found[0])}: greedy {found[1]}, best {found[2]}"
                                    if found else "no counterexample found"))


if __name__ == "__main__":
    part1()
    part2()
    part3()
```

3. **Check every counterexample by hand.** Draw each failing interval set on a number line and explain in one sentence why the rule went wrong.
4. **Beat the search.** "Fewest conflicts" survives. Run it on this structured instance and compare with `most_disjoint`: `[(0, 20), (30, 50), (60, 80), (90, 110), (40, 70), (10, 40), (11, 39), (12, 38), (70, 100), (71, 101), (72, 102)]`. Explain which interval it picks first and why that is fatal.
5. **Trust but verify the DP.** `best_weight` is the oracle for part 3, so test it too: compare it with a brute force over all subsets of up to 7 random weighted jobs.
6. **Record the results** in your journal as a table: rule, problem, survives or fails, smallest counterexample. You will reuse it in the "Greedy or DP?" card.

## What you should see

```text
coins: 93% of random 4-coin systems with a 1 are not greedy-safe
  [1, 6, 10, 38]: amount 12, greedy 3 coins, optimal 2
  [1, 9, 18, 33]: amount 36, greedy 4 coins, optimal 2
  [1, 30, 32, 43]: amount 60, greedy 18 coins, optimal 2
  [1, 5, 10, 25]: smallest counterexample None
  [1, 2, 5, 10, 20, 50, 100, 200]: smallest counterexample None
  [1, 3, 4]: smallest counterexample 6
  [1, 3, 6, 12, 24, 30]: smallest counterexample 48
earliest end    : no counterexample found
earliest start  : FAILS on [(6, 12), (7, 8), (11, 17)]: greedy 1, best 2
shortest first  : FAILS on [(5, 8), (7, 9), (8, 14)]: greedy 1, best 2
fewest conflicts: no counterexample found
earliest end        : FAILS on [(1, 6, 1), (5, 8, 3)]: greedy 1, best 3
heaviest first      : FAILS on [(1, 3, 5), (2, 8, 9), (7, 13, 8)]: greedy 9, best 13
best weight per hour: FAILS on [(2, 8, 7), (3, 5, 5)]: greedy 5, best 7
```

- **Coins:** almost every random coin system breaks largest-first; real currencies are chosen to be canonical. The euro, pound and U.S. systems pass the exact Kozen and Zaks check.
- **Unweighted intervals:** earliest end survives (it is proved in the proofs card); earliest start fails when one long interval blocks two short ones; shortest first fails when a short interval straddles two disjoint ones.
- **Fewest conflicts** survives 3,000 random trials at every size up to 8, yet on the 11-interval instance it keeps (40, 70), the interval with only two conflicts, which destroys two of the four intervals of the optimum: greedy 3, best 4. Random search finds most bad rules, not all of them.
- **Weighted intervals:** every single-order rule fails, often with just two jobs. Weights make an early choice's value depend on what it blocks later, which is exactly when you need the DP (sort by end, binary search for the last compatible job).

## Check yourself

Q: Why does `hunt` loop over sizes from small to large instead of drawing random sizes?
A: So the first failure it reports is as small as possible. Small counterexamples are easier to understand by hand, and they point at the structural reason the rule fails.

Q: Why does `hunt` skip inputs with ties in the rule's key?
A: With ties, `sorted` keeps the input order, so the rule's behaviour depends on an arbitrary tie-break. Skipping tied inputs makes sure a reported failure is the rule's fault, not the tie-break's.

> [!know]
> You now know how to let a brute force decide between greedy rules, and why a rule that survives random search still needs a proof.

=== primer | How do you solve reach and jump problems in one pass? | 12 min
goal: Decide reachability with a running furthest reach and count the fewest jumps with breadth-first layers, both in O(n) time and O(1) space, with stays-ahead proofs
tag: greedy-reach | Furthest reach and jump layers
link: Kleinberg and Tardos slides: Greedy Algorithms I (PDF) | https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/04GreedyAlgorithmsI.pdf#page=12 | 5 min: slides 12-14 and 33, the earliest-finish algorithm and its stays-ahead proof, then the summary of greedy proof strategies; the jump proofs here follow the same pattern
practice: 55, 45

> [!key]
> When every position lets you jump **any distance up to** some limit, the set of reachable positions is always one contiguous block starting at 0. So one number describes it: the **furthest reach** so far. Scan left to right, extend the reach with i + jumps[i], and fail as soon as you stand beyond it. For the **fewest jumps**, the positions reachable with k jumps also form a block (breadth-first layer k); scan each layer, track the furthest reach of the next, and count a jump whenever a layer ends.

## Intuition

Stepping stones across a river: from each stone you can leap at most so many stones forwards. You do not need to plan a route to know whether the far bank is reachable. Walk along, remembering only the furthest stone any stone so far can reach. If you ever find yourself standing on a stone beyond that mark, you could never have got there: you are stuck. Otherwise the mark keeps moving forwards and eventually passes the bank.

## How it works

### Can you reach the end?

Invariant: when the loop reaches index i, `reach` is the largest j + jumps[j] over all j < i, and every index up to `reach` is reachable.

- **Why a block:** if index j is reachable you can land anywhere in [j, j + jumps[j]], which overlaps the block you already have (it contains j). The union of overlapping intervals that all contain earlier reachable points is one interval starting at 0.
- **Why stuck means impossible:** if i > reach, every jump from every reachable index lands at or before reach < i, so i and everything after it is unreachable.
- Otherwise i is reachable, so its jump extends the block.

### The fewest jumps

Group indices by the number of jumps needed: layer 0 is index 0; layer k + 1 is everything reachable in one jump from layer k but not earlier. Each layer is a contiguous block, and the end of layer k + 1 is the furthest reach from any index in layers up to k. That is breadth-first search on an implicit graph, but because layers are blocks you never need a queue: keep `layer_end` (where the current layer stops) and `furthest` (the best reach seen so far). When the scan reaches `layer_end`, the current layer is exhausted: count one jump and move `layer_end` to `furthest`.

**Stays ahead:** after k jumps, greedy's block reaches at least as far as any position any k-jump route can stand on. Induction: true for k = 0; any route's (k + 1)-th jump starts inside greedy's first k layers, so it lands no further than greedy's furthest. Hence greedy reaches the end with as few jumps as any route.

### Near misses

- **Exact jumps** (from i you must land on exactly i + a[i] or i - a[i]): reachable positions are no longer a block, so use BFS (the graphs module; Jump Game III, 1306, lives there).
- **Costs per landing**, or a limited number of jumps: the cheapest route needs DP or Dijkstra, not a single reach number.
- **Covering a segment with intervals** (sprinklers, taps, video clips): for each start, record the furthest end of any interval starting there; that turns it into the fewest-jumps scan (1326 in the bank).

## Cost

One pass, constant work per index: **O(n) time, O(1) space**. The obvious alternatives are slower: a DP "fewest jumps to i" that looks back at every j < i is O(n^2), and BFS with explicit edges can touch O(n^2) edges when jumps are long.

## When to use it

| Problem shape | Tool |
|---|---|
| From i you may move anywhere in [i, i + a[i]]; reachable? | furthest reach, O(n) |
| Same moves; fewest jumps | layers (implicit BFS), O(n) |
| Fixed jump lengths, both directions, or obstacles | BFS on the graph |
| Weighted landings or a jump budget | DP or Dijkstra |
| Fewest intervals to cover [0, L] | convert to "furthest end per start", then layers |

## Worked trace

Reachability on jumps = [3, 1, 1, 0, 2], then fewest jumps on [2, 3, 1, 1, 2, 1, 1].

```steps
i = 0: index 0 is reachable (0 <= reach); reach = max(0, 0 + 3) = 3
    index    0  1  2  3  4
    jumps   {{3}} 1  1  0  2      reach = 3
---
i = 1, 2, 3: each stands within reach; 1 + 1, 2 + 1 and 3 + 0 do not beat 3
    index    0  1  2  3  4
    jumps    3 {{1  1  0}} 2      reach = 3
---
i = 4 > reach = 3: nothing can land on index 4. Answer: False (the 0 at index 3 is a trap)
    index    0  1  2  3  4
    jumps    3  1  1  0 {{2}}     stuck
---
Fewest jumps on [2, 3, 1, 1, 2, 1, 1]. Layer 0 is index 0; its furthest reach is 2, so layer 1 = indices 1..2
    index    0  1  2  3  4  5  6
    jumps   {{2}} 3  1  1  2  1  1     jumps = 1, layer_end = 2
---
Scan layer 1 (indices 1, 2): furthest = max(1 + 3, 2 + 1) = 4. At i = 2 the layer ends
    index    0  1  2  3  4  5  6
    jumps    2 {{3  1}} 1  2  1  1     jumps = 2, layer_end = 4
---
Scan layer 2 (indices 3, 4): furthest = max(3 + 1, 4 + 2) = 6, the last index. At i = 4 the layer ends
    index    0  1  2  3  4  5  6
    jumps    2  3  1 {{1  2}} 1  1     jumps = 3, layer_end = 6
---
layer_end covers the last index: 3 jumps (for example 0 -> 1 -> 4 -> 6)
    layers: {0}  {1, 2}  {3, 4}  {5, 6}
```

## Template

```python
def can_reach_end(jumps):
    """jumps[i] is the longest jump allowed from i. Can you get from 0 to the last index?"""
    reach = 0                              # furthest index known to be reachable
    for i, j in enumerate(jumps):
        if i > reach:
            return False                   # i is beyond everything reachable: stuck
        reach = max(reach, i + j)
    return True


def fewest_jumps(jumps):
    """Fewest jumps from 0 to the last index (assumes it is reachable)."""
    count, layer_end, furthest = 0, 0, 0
    for i in range(len(jumps) - 1):        # never jump from the last index
        furthest = max(furthest, i + jumps[i])
        if i == layer_end:                 # every index of this layer has been scanned
            count += 1
            layer_end = furthest
    return count
```

## Pitfalls

- **Looping to the last index in `fewest_jumps`.** If the loop includes n - 1 and the last layer ends exactly there, you count one jump too many. Stop at n - 2.
- **Updating before checking.** In `can_reach_end`, test `i > reach` before using jumps[i]; an unreachable index must not extend the reach.
- **Unreachable input in `fewest_jumps`.** The template assumes the end is reachable (as the classic problem promises). Otherwise `layer_end` stops growing; check with `can_reach_end` first or detect `furthest <= i` at a layer end.
- **Single element.** jumps = [0] is already at the end: reachable, 0 jumps. Both templates handle it.

## Check yourself

Q: Trace `can_reach_end([2, 0, 2, 0, 1])`. What is `reach` after each index?
A: 2, 2, 4, 4, 5, and the answer is True. Index 1 (a 0) adds nothing, but index 2 was already within reach and jumps to 4, the last index.

Q: Why does the reach argument fail if, from i, you may land only on exactly i + a[i]?
A: Reachable positions stop being one block: you may reach 0, 3 and 5 but not 4. One number can no longer describe the set, so "i <= reach" no longer means "i is reachable". You need BFS (or a boolean array) over the actual positions.

Q: Fewest sprinklers to water a garden [0, 10], each sprinkler covering an interval. How do you reuse `fewest_jumps`?
A: For each position p, record the furthest right end of any interval that starts at or before p (clip starts at 0), which plays the role of i + jumps[i]. Then run the layer scan over positions: each "jump" is one more sprinkler. If a layer ends without extending `furthest`, the garden cannot be covered.

## Lab

- **55 Jump Game.** Write `can_reach_end` from a blank file and state its invariant in a comment. Expected: O(n) time, O(1) space; [1, 2, 0, 1, 0, 3] gives false (stuck at index 5 behind the 0 at index 4), [2, 0, 2, 0, 1] gives true.
- **45 Jump Game II.** Write the layer scan, then check it against a BFS on 1,000 random reachable arrays. Expected: O(n) time, O(1) space; [4, 1, 1, 1, 9, 1] needs 2 jumps (0 -> 4 -> 5), [1, 1, 1, 1] needs 3.

> [!know]
> You now know how to answer reach and fewest-jump questions with one number per layer, and why the reachable positions form a block.

=== primer | Why does gas station restart after a negative tank, and why is that correct? | 13 min
goal: Solve circular-route and running-balance problems in one pass, and prove the restart rule with the skipping lemma and the prefix-minimum picture
tag: greedy-balance | Running balance and restarts
link: Wikipedia: Maximum subarray problem, Kadane's algorithm | https://en.wikipedia.org/wiki/Maximum_subarray_problem#Kadane's_algorithm | 10 min: the 'Kadane's algorithm' section, the same "a prefix with a negative running sum never helps, so restart" argument applied to the best subarray
practice: 134, 678

> [!key]
> Walk the stations keeping a **running balance** (gas gained minus gas spent). If it drops below zero after station j, you cannot get past j from the current start, and neither can you from **any station between** the start and j, because each of them arrives with no more fuel than you had. So restart right after j with an empty tank. If the **total** gas covers the total cost, the last start is the answer. One pass, **O(n)** time, **O(1)** space.

## Intuition

You drive a ring road with fuel stations and an empty tank. Station i gives gas[i] and the road to the next station costs cost[i]. Start somewhere, and if the tank would go negative you are stranded. Suppose you start at A and get stranded just after station D. Would starting at B or C (between A and D) help? No: when you passed B coming from A, your tank held at least zero, a head start. Starting at B with an empty tank is never better than arriving there with that head start, and with it you still failed at D. So skip all of them and try the station after D.

## How it works

### The algorithm

1. If sum(gas) < sum(cost), no start works: return -1.
2. Keep `start` and `tank`. For each station i, add gas[i] - cost[i] to `tank`.
3. If `tank` < 0, set `start = i + 1` and `tank = 0`.
4. Return `start`.

### Why skipping is safe (the skipping lemma)

Let d[i] = gas[i] - cost[i]. Starting at s, suppose the running sum first becomes negative at j: d[s] + ... + d[j] < 0, while every shorter sum d[s] + ... + d[k - 1] for s < k <= j is at least 0. Starting at such a k instead, you reach j with d[k] + ... + d[j] = (d[s] + ... + d[j]) - (d[s] + ... + d[k - 1]), which is at most the first sum and therefore negative. So every start in s..j fails at or before j, and the next candidate is j + 1.

### Why the last start works (the prefix-minimum picture)

Let P(i) = d[0] + ... + d[i], with P(-1) = 0. Starting at s, your tank after station i is P(i) - P(s - 1) on the first lap, and P(n - 1) - P(s - 1) + P(i) after wrapping round. Both are non-negative for every i exactly when **P(s - 1) is the smallest prefix sum** and the total P(n - 1) is at least 0. The restart rule resets exactly when the running sum since the last start goes negative, which is when the prefix sum hits a new minimum, so the final start is right after the global minimum:

```text
prefix sum P(i) after each station, d = -1, -2, +1, +3, +1
   2 |                   *
   1 |               *
   0 +----------------------
  -1 |   *
  -2 |           *
  -3 |       *   <- lowest point: start after station 1
         0   1   2   3   4   station
```

### Other running balances

The same invariant appears whenever a quantity must never go negative: **brackets** are valid when the balance (opens minus closes) never drops below 0 and ends at 0; a **bank account** or **stock level** must stay non-negative; Kadane's maximum subarray restarts when its running sum turns negative. When a symbol can mean several things (a wildcard that may be an open bracket, a close bracket or nothing), the balance is no longer one number but a **set of possible balances**; for brackets that set is always a range, so two numbers still suffice (the derive problem in the Lab).

## Cost

Two sums and one pass: **O(n) time, O(1) extra space**. The brute force simulates a full lap from every start, O(n^2).

## When to use it

Cues: a circular route or schedule, "can you complete", "never runs out", "balance never negative", and a total that must cover the demand. If the question asks for the best segment rather than a feasible start, it is Kadane's algorithm; if values can be chosen (signs, wildcards), track the range of balances; if there are several resources or the cost depends on the order of visits, it is no longer a one-number balance and usually needs DP or search.

## Worked trace

gas = [3, 1, 2, 5, 4], cost = [4, 3, 1, 2, 3], so the balance changes d = [-1, -2, +1, +3, +1].

```steps
Totals: gas 15 >= cost 13, so some start works. start = 0, tank = 0
    station   0   1   2   3   4
    d        -1  -2  +1  +3  +1
    tank      .   .   .   .   .     start = 0
---
Station 0: tank = -1 < 0. You cannot reach station 1 from 0: restart at 1 with an empty tank
    station   0   1   2   3   4
    d        -1  -2  +1  +3  +1
    tank    {{-1}}  .   .   .   .     start = 1
---
Station 1: tank = -2 < 0. Restart at 2
    station   0   1   2   3   4
    d        -1  -2  +1  +3  +1
    tank     -1 {{-2}}  .   .   .     start = 2
---
Stations 2, 3, 4: tank 1, 4, 5, never negative. The scan ends with start = 2
    station   0   1   2   3   4
    d        -1  -2  +1  +3  +1
    tank     -1  -2 {{1   4   5}}    start = 2
---
Check the wrap-around from 2: after stations 0 and 1 the tank is 5 - 1 = 4, then 4 - 2 = 2. Never negative: 2 is the answer
    order     2   3   4   0   1
    tank      1   4   5   4  {{2}}
```

## Template

```python
def circuit_start(gas, cost):
    """Index of the station to start from to drive the whole loop, or -1 if impossible."""
    if sum(gas) < sum(cost):
        return -1
    start, tank = 0, 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:                       # cannot reach i + 1 from start: no station in
            start, tank = i + 1, 0         # start..i works either, so restart after i
    return start
```

The verification for this module compares it with a full simulation from every start on random inputs: whenever some start works, the returned start works too, and -1 is returned exactly when none does.

## Pitfalls

- **Skipping the total check.** Without it the loop happily returns a start even when no start works (it never wraps round to notice).
- **Restarting at i instead of i + 1.** Station i itself is one of the failed starts.
- **Strict or non-strict.** A tank of exactly 0 is fine (you arrive with nothing and refuel); restart only on a negative tank.
- **Simulating the wrap-around.** You do not need a second lap: the total check plus the prefix-minimum argument already guarantee it.

## Check yourself

Q: For gas = [5, 1, 2, 3] and cost = [4, 4, 1, 2], what does `circuit_start` return? Trace the tank.
A: 2. Totals 11 and 11, so a start exists. Tank: +1 at station 0, then 1 - 3 = -2 at station 1, so restart at 2; then +1 and +1 to the end. From 2 the full lap is 1, 2, 3, then 0 at station 1: never negative.

Q: State the skipping lemma in one sentence and say where it uses "the tank never went negative before j".
A: If starting at s first fails after station j, every start between s and j also fails by j. It uses the earlier non-negativity to say that each intermediate station is reached from s with a tank of at least 0, so starting there empty can only be worse.

Q: Brackets: is "(()))(" balanced? Which invariant decides it?
A: No. The balance goes 1, 2, 1, 0, -1, so it drops below 0 at the fifth character (a close bracket with nothing to match), even though the final balance is 0. Valid means "never negative and ends at 0".

## Lab

- **134 Gas Station** (derive it). Prove the skipping lemma for yourself before coding, then compare your function with a simulate-every-start brute force. Expected: O(n) time, O(1) space; gas [1, 4, 0, 3] with cost [2, 1, 2, 2] gives 1; gas [2, 2, 2] with cost [3, 2, 2] gives -1.
- **678 Valid Parenthesis String** (derive it). Each `*` may be an open bracket, a close bracket or nothing, so describe the set of balances that are still possible after each character, and when it is hopeless. Expected: O(n) time, O(1) space; "(*))" is valid, ")*(" and "((*" are not.

> [!know]
> You now know how to solve running-balance problems in one pass and prove the restart rule with the skipping lemma and the prefix minimum.

=== primer | How do you find the right sort key for a greedy, and prove it? | 14 min
goal: Derive a greedy sort key from an adjacent-swap comparison, check it is a consistent order, and recognise when the order is forced instead
tag: greedy-sort | Sort by an exchange-derived key
link: Erickson, Algorithms ch. 4: Storing Files on Tape (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/04-greedy.pdf#page=2 | 10 min: PDF pages 2-3, files with access frequencies, where the swap argument produces the sort key L/F (length over frequency)
link: Kleinberg and Tardos slides: minimising lateness (PDF) | https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/04GreedyAlgorithmsI.pdf#page=25 | 10 min: slides 25-32, earliest deadline first and its proof by removing inversions one adjacent pair at a time
practice: 763, 846

> [!key]
> Many greedy algorithms are "sort by the right key, then sweep once". Find the key by comparing two **adjacent** items in both orders: everything else in the solution is unaffected, so the condition under which "a before b" is no worse is your comparator. If that condition compares a number computed from a alone with one computed from b alone, that number is a valid **sort key** and the adjacent-swap argument proves the sorted order optimal.

## Intuition

A print shop has jobs that take different times and customers who value them differently (weight = how much each minute of waiting costs). Which job first? Neither "shortest first" nor "most important first" is right in general. Look at just two neighbouring jobs and ask what swapping them changes: only those two customers' waiting times move, so the better order of the pair depends only on the pair. Turn that comparison into a formula and you have the sort key for the whole queue.

## How it works

### Deriving Smith's rule

Jobs have length t and weight w; minimise the sum of w x (finish time). Put a and b next to each other, starting at time T:

- a then b costs w_a(T + t_a) + w_b(T + t_a + t_b)
- b then a costs w_b(T + t_b) + w_a(T + t_a + t_b)

Subtract: (a first) - (b first) = w_b t_a - w_a t_b. So a should go first when w_b t_a <= w_a t_b, that is when **t_a / w_a <= t_b / w_b**. The comparison splits into a number for a and a number for b, so sort by t / w ascending. If any order has an adjacent pair out of key order, swapping them does not increase the cost (the subtraction above), and repeating such swaps reaches the sorted order: the sorted order is optimal. With all weights equal this is shortest job first; with all lengths equal it is heaviest first.

### When a key exists, and when it does not

The comparison must define a **consistent order** (if a goes before b and b before c, then a before c). A key computed from each item alone, like t / w, gives that automatically. Some problems only give a pairwise rule, such as "put x before y when the string x + y is larger than y + x" (the largest-number problem in the sorting module); then you must check that the rule is transitive and use `functools.cmp_to_key`. An inconsistent comparator makes `sorted` produce an arbitrary order without any error.

### Pairing: smallest with largest

Split an even-length list into pairs so that the largest pair sum is as small as possible (assign two tasks per worker, two people per boat). Sort, then pair the smallest with the largest, the second smallest with the second largest, and so on. Exchange: in any pairing, if the largest value x is paired with y while the smallest value s is paired with z, swap partners to get (x, s) and (y, z). Now x + s <= x + y, and y + z <= y + x, so no pair sum grew. Repeat on the rest. The "boats" problem from the two-pointers module is the same idea with a capacity limit.

### Forced choices: no sort key needed

Sometimes one choice is not just safe but **forced**. Dealing cards into runs of k consecutive values: the smallest card left can only be the *start* of a run, so start one there. Cutting a string into the most pieces so that each letter appears in one piece: a piece that contains a letter must extend at least to that letter's **last occurrence**, so sweep left to right, extend the current piece's end to the last occurrence of each letter you meet, and cut exactly when you reach that end. Both are greedy, and both proofs are one sentence: any other choice is impossible.

### Deadlines

To minimise the **largest** lateness (finish time minus deadline), order jobs by deadline: **earliest deadline first**. The adjacent-swap argument again: swapping an inverted adjacent pair never increases the maximum lateness. Linux's `SCHED_DEADLINE` scheduling class runs real-time tasks by this rule.

## Cost

A sort and a pass: **O(n log n) time**, O(n) for the sorted copy (or O(1) extra with an in-place sort). Forced-choice sweeps like the last-occurrence cut are O(n) after an O(n) table of last positions. A `cmp_to_key` sort costs more per comparison (a Python call each time) than a key sort, but is still O(n log n).

## When to use it

| Objective | Key or rule |
|---|---|
| Minimise the sum of finish times | shortest first (t ascending) |
| Minimise the weighted sum of finish times | t / w ascending (Smith's rule) |
| Minimise the largest lateness | deadline ascending (EDF) |
| Most non-overlapping intervals | end time ascending |
| Minimise the largest pair sum | sort, pair smallest with largest |
| Groups or pieces with forced boundaries | sweep, no comparator: smallest first, or last occurrence |

When the swap comparison depends on the *other* items too (for example on what is left of a capacity), there is no key, and the problem usually needs DP.

## Worked trace

Pair [7, 1, 4, 6, 2, 5] to minimise the largest pair sum.

```steps
Sort first: smallest and largest values are now at the two ends
    sorted   1  2  4  5  6  7
---
Pair the ends: 1 + 7 = 8. Move both pointers inwards
    sorted  {{1}} 2  4  5  6 {{7}}     pair sums: 8
---
Next ends: 2 + 6 = 8
    sorted   1 {{2}} 4  5 {{6}} 7     pair sums: 8, 8
---
Last pair: 4 + 5 = 9. The answer is the largest pair sum: 9
    sorted   1  2 {{4  5}} 6  7     pair sums: 8, 8, 9
---
Compare a natural-looking alternative, neighbours together: 1 + 2, 4 + 5, 6 + 7 has a largest sum of 13
    (1, 2) = 3   (4, 5) = 9   (6, 7) = {{13}}
```

## Template

```python
def weighted_completion_order(jobs):
    """jobs: (length, weight). Order minimising sum of weight * finish time (Smith's rule)."""
    return sorted(jobs, key=lambda j: Fraction(j[0], j[1]))   # length / weight, ascending


def weighted_cost(order):
    clock = total = 0
    for t, w in order:
        clock += t
        total += w * clock
    return total


def min_max_pair(times):
    """Split an even-length list into pairs minimising the largest pair sum."""
    t = sorted(times)
    return max(t[i] + t[-1 - i] for i in range(len(t) // 2))
```

It needs `from fractions import Fraction`, which keeps the key exact: 1/3 and 2/6 compare equal, as they should. The verification compares both functions with brute force over every permutation or pairing of random small inputs.

## Pitfalls

- **Guessing the key.** "Most important first" and "shortest first" are both wrong for weighted completion time; derive the key from the swap instead of picking the more intuitive one.
- **Inconsistent comparators** with `cmp_to_key`: a non-transitive rule gives an arbitrary, input-dependent order.
- **Float keys** for ratios: equal ratios can compare unequal; use `Fraction` or compare t_a w_b with t_b w_a.
- **Sorting by start instead of end** (intervals) or by length instead of deadline (lateness): the classic one-word bugs.

## Check yourself

Q: Jobs (length, weight) (3, 1), (1, 2) and (2, 2). In which order does Smith's rule put them, and what is the cost? What does the input order cost?
A: Keys 3, 0.5 and 1, so (1, 2), (2, 2), (3, 1). Finish times 1, 3 and 6 give 2 x 1 + 2 x 3 + 1 x 6 = 14, the minimum. The input order finishes at 3, 4 and 6: 1 x 3 + 2 x 4 + 2 x 6 = 23.

Q: Why is it enough to compare adjacent jobs, when an optimal order could differ from the sorted one by moving a job far away?
A: Any order that is not sorted by the key has at least one adjacent pair out of order, and swapping that pair never increases the cost. Each such swap removes one inversion, so a finite sequence of non-worsening swaps turns any order (including an optimal one) into the sorted order, which is therefore optimal too.

Q: Cut "abacdcd" into as many pieces as possible so that no letter appears in two pieces. Where do the cuts go?
A: After index 2: "aba" | "cdcd". The first piece must reach the last a (index 2), and no letter inside it appears later, so you cut there; the second piece must reach the last c and d (index 6).

## Lab

- **763 Partition Labels.** Record each letter's last index, then sweep, extending the current piece's end. Expected: O(n) time, O(1) extra space for a fixed alphabet; "abacdcd" gives [3, 4], "abcadefgfh" gives [4, 1, 1, 3, 1].
- **846 Hand of Straights.** Count the cards, then repeatedly start a run at the smallest remaining value. Expected: O(n log n) time, O(n) space; [4, 2, 3, 3, 5, 4] with k = 3 is true (2-3-4 and 3-4-5), [1, 2, 3, 3, 4, 6] with k = 3 is false.

> [!know]
> You now know how to derive a greedy sort key from an adjacent swap, when such a key exists, and how to spot choices that are forced.

=== primer | When does a greedy need a heap, and how do you use one? | 13 min
goal: Recognise greedy problems whose best choice changes as you go, and implement the unlock-then-best and regret patterns with heapq, with their exchange proofs
tag: greedy-heap | Greedy with a heap
link: Python docs: heapq, priority queue implementation notes | https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes | 5 min: tie-breaking with (priority, count, item) tuples and removing entries lazily, the two details every heap greedy needs
practice: 1675

> [!key]
> A sort fixes the order of all choices up front. When the best choice **changes as you go** (new options become available, or a past choice turns out to be expensive), keep the candidates in a **heap**: push options as they become available and pop the best one when you must commit. Two patterns cover most problems: **unlock, then take the best** available, and **take now, regret later** (if the plan breaks, drop the worst item taken so far). Each push and pop is O(log n).

## Intuition

You are planning courses that each take some days and must be finished by their own deadline, one at a time. Go through them in deadline order and simply sign up for each. When a new course pushes you past its deadline, something has to go, and the best thing to drop is the **longest** course you have taken so far: you lose one course either way, and dropping the longest frees the most days for the future. A heap tells you the longest course in O(log n). This is "take now, regret later".

## How it works

### Pattern 1: unlock, then take the best

Options become available over time or as a resource grows; at each step, take the best available one. Example: you have some capital and may complete k projects one after another; each needs a minimum capital to start and adds its profit to your capital. Sort the projects by required capital. Before each choice, push every newly affordable project's profit into a max-heap, then pop the largest.

Why it is safe: capital never decreases, so anything affordable now stays affordable. If an optimal plan starts with some other affordable project, swap in the most profitable one: after that step you have at least as much capital, so every later step of the plan is still possible and ends with at least as much. Repeating the swap turns the plan into the greedy one. Problems of this shape in the heap module include IPO (502), Task Scheduler (621) and Reorganize String (767).

### Pattern 2: take now, regret later

Commit to every option, and when a constraint breaks, undo the commitment that hurts most. Course scheduling: process courses by deadline, push each duration into a max-heap and add it to the day count; if the day count exceeds the current deadline, pop the longest duration and subtract it.

Why it is safe: after processing the first i courses, the heap holds a feasible set of the **largest possible size**, and among such sets one with the **smallest total duration**. Adding a course raises the size by one; if that overflows the deadline, no feasible set of the bigger size exists (the old set already had the least total time), so the size stays, and dropping the longest course restores the least total time. Refuelling stops (871) and climbing buildings with limited ladders (1642), in the heap module, are the same pattern.

### Pattern 3: combine the two smallest

Repeatedly take the two smallest items, merge them and push the result back. It is how Huffman builds optimal codes, the next card.

### heapq details

- `heapq` is a **min-heap** of a list: push `-x` to get a max-heap, and negate again when you pop.
- Push **tuples** `(priority, tie_breaker, item)` when items themselves cannot be compared, or when you need a stable order; a running counter is the usual tie-breaker.
- `heapify` builds a heap from a list in O(n); `heappushpop` and `heapreplace` combine two operations in one O(log n) call.
- C++ has `std::priority_queue` (a max-heap by default); Java has `PriorityQueue` (a min-heap).

## Cost

Sorting the input once is O(n log n); every option is pushed once and popped at most once, O(log n) each, so **O(n log n) time** in total and O(n) space for the heap. For the projects problem with k choices among n projects it is O((n + k) log n).

## When to use it

| Signal | Pattern |
|---|---|
| Options unlock as a resource grows or time passes; take the best available each round | unlock, then best (sort by unlock condition + max-heap of value) |
| A running constraint can break; fix it by dropping the worst past choice | take now, regret later (max-heap of costs) |
| Repeatedly merge the two cheapest parts | combine two smallest (min-heap), Huffman |
| The order of all choices is known up front | no heap: sort once (previous card) |

## Worked trace

Courses (duration, last day) sorted by last day: (4, 4), (2, 5), (3, 8), (2, 8), (5, 12), (1, 12). The heap holds the durations taken; `day` is their total.

```steps
(4, 4): take it. day = 4 <= 4
    heap (durations)  [4]              day = 4
---
(2, 5): take it, day = 6 > 5. Over the deadline: drop the longest course taken, the 4
    heap  [{{4}}, 2]  ->  [2]           day = 6 - 4 = {{2}}
---
(3, 8): day = 5 <= 8. (2, 8): day = 7 <= 8. Both kept
    heap  [2, {{3}}, {{2}}]                 day = 7
---
(5, 12): day = 12 <= 12, kept
    heap  [2, 3, 2, {{5}}]              day = 12
---
(1, 12): day = 13 > 12: drop the longest, the 5. Four courses fit
    heap  [2, 3, 2, {{5}}, 1]  ->  [2, 3, 2, 1]     day = 8
```

## Template

```python
def most_courses(courses):
    """courses: (duration, last_day). Most courses you can finish, one at a time from day 0."""
    taken, day = [], 0                     # max-heap of durations (negated), total time used
    for dur, last in sorted(courses, key=lambda c: c[1]):   # by deadline
        heapq.heappush(taken, -dur)
        day += dur
        if day > last:                     # over the deadline: drop the longest course so far
            day += heapq.heappop(taken)    # (adds a negative number)
    return len(taken)


def best_projects(k, capital, projects):
    """projects: (needed_capital, profit). Do at most k, one at a time; maximise final capital."""
    projects = sorted(projects)
    ready, i = [], 0                       # max-heap of profits that are affordable now
    for _ in range(k):
        while i < len(projects) and projects[i][0] <= capital:
            heapq.heappush(ready, -projects[i][1])
            i += 1
        if not ready:
            break
        capital -= heapq.heappop(ready)
    return capital
```

Both need `import heapq`. The verification compares `most_courses` with a brute force over all subsets (a subset is feasible when, in deadline order, every course ends by its last day) and `best_projects` with a search over every sequence of projects.

## Pitfalls

- **Forgetting to negate** for a max-heap, or negating on push but not on pop.
- **Comparing uncomparable items**: ties in the first tuple field make Python compare the second; add a counter.
- **Sorting by the wrong key before the heap**: courses must be processed by deadline, projects by required capital.
- **Re-sorting inside the loop** instead of using a heap: O(n^2 log n) instead of O(n log n).

## Check yourself

Q: Courses (5, 5), (2, 6), (2, 7). What does `most_courses` keep, and why is that better than keeping the first course?
A: It keeps the two 2-day courses (answer 2). After (2, 6) the day count is 7 > 6, so it drops the 5-day course; then (2, 7) fits at day 4. Keeping the 5-day course would allow only one course in total.

Q: In the projects problem, why can taking the most profitable affordable project never hurt later choices?
A: Taking a project only increases capital, and the more profitable choice increases it at least as much, so every project affordable after the alternative is also affordable after the greedy choice. An exchange from any optimal plan never loses capital at any step.

Q: With k = 2 and capital 0, projects (needed, profit) (0, 1), (1, 2), (1, 3): what is the final capital?
A: 4. Only (0, 1) is affordable at first, so capital becomes 1; then both others are affordable and the heap gives the profit 3: 1 + 3 = 4. With k = 3 it would be 6.

## Lab

- **1675 Minimize Deviation in Array** (stretch). Odd numbers may be doubled once and even numbers halved repeatedly: first move every number to its largest reachable value, then repeatedly halve the current maximum while tracking the minimum. Expected: O(n log n log M) time for values up to M, O(n) space; [6, 10, 3] gives 1 (6, 5, 6), [8, 1, 5] gives 3, [12, 5, 9] gives 3.
- **Regret in action.** Run `most_courses` on the trace's six courses and print the heap after every step. Expected: the same states as the trace, and a final answer of 4.

> [!know]
> You now know when a greedy needs a heap, the unlock-then-best and take-now-regret-later patterns, and how to prove each with an exchange.
