---
key: projectfound
name: Build a cost and correctness workbench
stage: found
summary: Compare two implementations of the same query with reproducible tests and measurements.
why: A repeatable experiment makes an algorithm's assumptions, correctness and cost visible before optimisation.
outcomes:
- Write an oracle and test an invariant against it.
- Measure scaling separately from machine-dependent wall time.
cues:
- You are about to optimise code without a baseline.
- Two implementations need to agree on edge cases.
traps:
- Timing includes input generation for only one implementation.
- A fast result is accepted without checking its answer.
---

=== build | Range-sum experiment bench | 6-8 h
goal: Build a small command-line benchmark and correctness harness for repeated range sums.
link: Complexity calculations | https://usaco.guide/bronze/time-comp#complexity-calculations | Connect operation counts to the measured growth.
link: Four phases | https://en.wikipedia.org/wiki/How_to_Solve_It#Four_phases | Use the phases to write the experiment before optimising.

## The brief
An analyst asks for many sums over one fixed list. Deliver a program, automated tests and a short report comparing direct scans with preprocessing. This is a local educational tool, not a general benchmark framework.

## Spec
Accept a list of signed integers and zero-based half-open queries `(left, right)`, with `0 <= left <= right <= n`. Return one sum per query, in order; an empty range sums to zero. Reject invalid bounds rather than silently clipping them. Implement a direct scan and a prefix-sum implementation independently. State the prefix invariant and preprocessing, query and total costs in terms of `n` and `q`; include storage.

Use the same generated input for both versions. Generate data outside the timed section, check answers before timing, and time preprocessing separately from query execution. Use a fixed random seed, one warm-up and at least five measured repetitions; report medians, runtime version and machine details. Count scan element visits and prefix construction/query accesses independently of time. Discuss the workload where preprocessing is not worthwhile.

## Milestones
1. **1-2 h:** Define the interface and hand-work empty, full and singleton ranges; implement direct scanning.
2. **1-2 h:** Implement prefix sums and document why the subtraction works.
3. **1-2 h:** Add boundary and seeded differential tests, including malformed queries.
4. **1-2 h:** Run the benchmark and write the cost and crossover report.

## Done when
- For `[3, -2, 5]`, queries `(0, 3)`, `(1, 1)`, `(1, 3)` produce `[6, 0, 3]`; an out-of-range query fails.
- At least 200 seeded small lists with random valid ranges match the scan oracle, including empty lists.
- Benchmark `n = 1,000, 5,000, 10,000` with `q = n` full-range queries; report time and counts, rather than asserting an absolute speed. Scan visits are `n*q`; prefix construction visits `n` values and each query uses two prefix entries.
- Report `O(n*q)` worst-case scan time versus `O(n+q)` prefix time, and `O(n)` auxiliary prefix storage; distinguish the input and result storage.

## Stretch goals
- Repeat with one short query and explain why totals can reverse despite better asymptotic query cost.
- Test large integers and discuss integer overflow in a fixed-width language.

## Hints
- Start by stating the [four phases](https://en.wikipedia.org/wiki/How_to_Solve_It#Four_phases); keep the direct implementation as the oracle.
- [Complexity calculations](https://usaco.guide/bronze/time-comp#complexity-calculations) help separate preprocessing from repeated work.
