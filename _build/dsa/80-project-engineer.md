---
key: projectengineer
name: Build a mutable range-sum index
stage: engineer
summary: Implement a Fenwick tree behind a small point-update and range-query API.
why: A purpose-built index trades extra storage and update work for faster repeated range queries.
outcomes:
- Maintain a Fenwick invariant after point updates.
- Measure update and query costs against a list oracle.
cues:
- Values change between aggregate queries.
- The aggregate is a sum over a contiguous range.
traps:
- Mixing internal one-based indices with external zero-based indices.
- Treating assignment as an increment without computing the delta.
---

=== build | Fenwick-backed inventory totals | 6-8 h
goal: Maintain mutable inventory counts and answer range totals.
link: Fenwick tree overview | https://cp-algorithms.com/data_structures/fenwick.html#overview | About 5 min: Review the indexed partial-sum invariant.
link: Point update range sum | https://usaco.guide/gold/PURS#segment-tree | About 5 min: Compare an alternative range-query structure.

## The brief
An inventory report needs totals over shelf ranges while counts change. Build an in-memory library with an explicit range contract; concurrent updates and persistence are out of scope.

## Spec
Initialise from a list of nonnegative integer counts. Provide `set(i, value)` and `sum(left, right)`, where the query is zero-based and half-open. Reject negative counts, invalid indices and ranges outside `0 <= left <= right <= n`; empty ranges return zero. `set` replaces rather than increments the value. Keep the current values to compute the delta, and a one-based Fenwick array for prefix sums.

Describe the invariant for each tree cell and derive the update and prefix loops. Use repeated point updates to initialise in `O(n log n)`; each set and range sum is `O(log n)` worst case and both arrays take `O(n)` auxiliary storage. A separate plain list is the test oracle.

## Milestones
1. **1-2 h:** Specify boundaries and write the plain-list reference and basic tests.
2. **1-2 h:** Implement prefix sums, initialisation and delta-based assignment.
3. **1-2 h:** Differential-test mixed seeded operations and invalid inputs.
4. **1-2 h:** Measure update/query workloads and explain tree steps and memory.

## Done when
- Starting with `[2, 0, 3]`, `sum(0,3)` is 5; after `set(1,4)`, `sum(1,3)` is 7 and `sum(2,2)` is 0.
- Empty data supports only `sum(0,0)`; invalid updates and negative values fail without changing state.
- At least 100 seeded traces of 1,000 operations match a list oracle after every query.
- Benchmark 10,000 mixed operations on sizes 1,000, 10,000 and 100,000, using the same fixed-seed operation stream for both implementations. Report median of five runs, tree-cell visits and reference elements scanned; include initialisation separately.
- Explain the difference between asymptotic bounds and any observed constant-factor crossover.

## Stretch goals
- Implement linear-time Fenwick construction and compare it with repeated updates.
- Add range minimum with a segment tree and explain why the same sum update scheme does not apply.

## Hints
- Draw the partial ranges in the [Fenwick overview](https://cp-algorithms.com/data_structures/fenwick.html#overview) for an eight-element array.
- Compare the [segment-tree point-update/range-sum](https://usaco.guide/gold/PURS#segment-tree) interface with your own.
