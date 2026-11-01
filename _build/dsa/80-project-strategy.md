---
key: projectstrategy
name: Build a bounded budget planner
stage: strategy
summary: Compare exhaustive subset search with dynamic programming for a discrete budget.
why: Repeated subproblems and reconstruction make the boundary between search and dynamic programming concrete.
outcomes:
- Define a 0/1 dynamic programming state and transitions.
- Check an optimisation with exhaustive enumeration.
cues:
- Each item may be selected at most once.
- A bounded integer budget makes states finite.
traps:
- Iterating an in-place capacity table forward allows reuse.
- Reporting an optimal value with an invalid reconstructed selection.
---

=== build | 0/1 purchase planner | 6-8 h
goal: Maximise useful value under a fixed budget and return the selected items.
link: Dynamic programming | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=2 | Define subproblems before transitions.
link: Backtracking | https://jeffe.cs.illinois.edu/teaching/algorithms/book/02-backtracking.pdf#page=9 | Use complete search as a small-input oracle.

## The brief
A community group has a fixed budget and proposed items. Build a planner that chooses a subset with maximum total benefit, not a fractional selection. Treat ties as allowing any optimal subset.

## Spec
Each item has a unique string ID, positive integer cost and nonnegative integer benefit. Budget is a nonnegative integer. Reject malformed values and duplicate IDs. Return selected IDs, total cost and total benefit; each ID appears at most once, and cost cannot exceed budget. Empty input and zero budget return the empty selection.

Implement a two-dimensional 0/1 DP over item index and capacity and reconstruct from the table. On ties, consistently skip the later item. Implement exhaustive subset enumeration for small inputs as an independent oracle. Explain the recurrence, base case, why it is complete, and why integer budget makes the `O(n*B)` bound pseudo-polynomial.

## Milestones
1. **1-2 h:** Specify inputs, implement exhaustive enumeration and hand-check a counterexample to benefit-per-cost greedy.
2. **1-2 h:** Implement the DP table and deterministic reconstruction.
3. **1-2 h:** Add seeded differential and reconstruction-validity tests.
4. **1-2 h:** Benchmark varying item count and budget; explain time and storage.

## Done when
- For budget 5 and items `(A,2,3)`, `(B,3,4)`, `(C,4,5)`, return `A,B` with cost 5 and benefit 7.
- A single item of cost 2 and benefit 3 under budget 4 is selected only once; invalid costs and duplicate IDs fail.
- At least 200 seeded cases with at most 12 items match exhaustive optimal benefit, and each reconstructed selection is feasible and sums to the reported totals.
- Benchmark `n=100` with budgets `100, 1,000, 5,000`; report five-run median time and number of DP cells. Separately time the exhaustive oracle only on small inputs.
- Explain `O(n*B)` time and storage for the chosen table, plus `O(n)` reconstruction, and why huge numeric budgets can be impractical.

## Stretch goals
- Implement a one-dimensional value-only version with descending capacities and compare its output with the table.
- Add an item-count constraint as an extra DP dimension and state its new cost.

## Hints
- Express the two alternatives for the current item using the [dynamic programming subproblem pattern](https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=2).
- Keep [backtracking](https://jeffe.cs.illinois.edu/teaching/algorithms/book/02-backtracking.pdf#page=9) as an independent oracle for small cases.
