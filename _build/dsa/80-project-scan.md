---
key: projectscan
name: Build a telemetry window analyzer
stage: scan
summary: Answer fixed-duration event queries with two pointers and prefix sums.
why: Ordered streams let small moving state replace repeated searches over the entire history.
outcomes:
- Maintain a half-open time window with duplicate timestamps.
- Compare a scanning implementation with a brute-force oracle.
cues:
- Events arrive in nondecreasing timestamp order.
- Many overlapping windows need counts and totals.
traps:
- Boundary events are counted in two adjacent windows.
- A two-pointer algorithm is applied to unordered events.
---

=== build | Sliding telemetry report | 6-8 h
goal: Produce counts and value sums for many ordered time windows in linear time.
link: Sliding window implementation | https://usaco.guide/gold/sliding-window#implementation | Review the moving-boundary invariant.
link: Prefix sum explanation | https://usaco.guide/silver/prefix-sums#explanation | Use prefix differences for window totals.

## The brief
An operator wants a report over timestamped measurements. Build a local function and a small CLI that reads events and query starts, then returns one row per window.

## Spec
Inputs are events `(timestamp, value)` with integer timestamps in nondecreasing order, nondecreasing integer query starts, and positive integer width `w`. A query at `s` covers `[s, s+w)` and outputs `(count, sum)`; duplicate timestamps and negative values are valid. Reject unordered inputs and nonpositive width. Inputs are finite; no streaming lateness or time-zone conversion is required.

Build prefix sums once and advance two indices to the first timestamps at least `s` and `s+w`. Each event index advances at most `n` times per pointer; compute each sum by prefix subtraction. Also implement a separate scan-all-events oracle. Document `O(n+q)` time for ordered starts and `O(n)` prefix storage, excluding the input and output.

## Milestones
1. **1-2 h:** Specify boundaries and implement the oracle and CLI input validation.
2. **1-2 h:** Implement the two moving indices and prefix sums.
3. **1-2 h:** Differential-test seeded event lists, duplicates, empty inputs and negative values.
4. **1-2 h:** Benchmark and report pointer advances, timing and memory assumptions.

## Done when
- Events `[(1, 2), (2, -1), (2, 4), (5, 3)]`, starts `[1, 2, 3]`, width `2` return `[(3, 5), (2, 3), (0, 0)]`.
- Empty events yield zero rows for each query; an event at `s+w` is excluded; unsorted starts or events are rejected.
- At least 200 seeded small cases match the oracle exactly.
- Benchmark `n = q = 1,000, 5,000, 10,000` with width covering all events; check outputs first, then report medians of five query runs and pointer advances. Each pointer advances at most `n`, while the oracle inspects exactly `n*q` events.
- Explain why sorting arbitrary query starts would add `O(q log q)` and require restoring original order.

## Stretch goals
- Support arbitrary start order by sorting indexed queries and returning results in original order.
- Add a maximum-value report using a monotonic deque and test duplicates.

## Hints
- Use the [sliding-window invariant](https://usaco.guide/gold/sliding-window#implementation) to define exactly which events lie between the pointers.
- [Prefix differences](https://usaco.guide/silver/prefix-sums#explanation) handle negative values without changing pointer movement.
