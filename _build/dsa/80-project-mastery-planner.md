---
key: projectmasteryplanner
name: Capstone dependency planner
stage: mastery
summary: Combine graph validation, topological scheduling and critical-path analysis.
why: Real dependency planning needs explicit cycle handling, reproducible ordering and a defensible time model.
outcomes:
- Detect cycles and produce a deterministic topological order.
- Compute earliest completion times and a critical path in a DAG.
cues:
- Tasks must finish before downstream tasks start.
- Unlimited parallel workers make the longest prerequisite chain decisive.
traps:
- Reporting a partial topological order as a successful plan.
- Confusing critical-path duration with a resource-limited schedule.
---

=== build | Capstone: parallel build planner | 8-12 h
goal: Plan a dependency graph and calculate its earliest finish and a critical path.
link: Graph representation | https://jeffe.cs.illinois.edu/teaching/algorithms/book/05-graphs.pdf#page=6 | About 5 min: Model tasks and prerequisite edges.
link: Dynamic programming | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=2 | About 5 min: Treat each task's earliest finish as a DAG subproblem.

## The brief
Plan an idealised build with unlimited workers. Every task has a duration and prerequisites; independent tasks may run simultaneously. A cycle makes the plan invalid. There are no resource limits, retries or network delays.

## Spec
Accept unique string task IDs, nonnegative integer durations and directed prerequisite edges `u -> v`. Reject missing IDs and duplicate edges; a self-edge is a cycle. Empty input returns empty order, finish zero and empty path. Use Kahn's algorithm with a min-heap of ready IDs for a deterministic topological order. If not all tasks are emitted, return a cycle error, never a partial success.

In topological order compute `start[v] = max(finish[u])` over prerequisites, default zero, and `finish[v] = start[v] + duration[v]`. Keep the predecessor yielding the maximum, breaking ties by smallest ID. The project finish is the maximum task finish, with smallest ID on a tie; backtrack the chosen predecessor chain. For a nonempty all-zero graph, still return a valid nonempty path. Output each start and finish, the topological order, finish time and path.

## Milestones
1. **1-2 h:** Define graph input, validation and deterministic tie rules.
2. **1-2 h:** Implement heap-based topological sort and explicit cycle rejection.
3. **1-2 h:** Compute earliest starts, finishes and a critical path.
4. **1-2 h:** Build a small exhaustive path oracle and random DAG tests.
5. **1-2 h:** Benchmark sparse and dense graphs and document costs.

## Done when
- Tasks `A:2`, `B:3`, `C:4` with edges `A->C`, `B->C` produce starts `A=0,B=0,C=3`, finish 7 and critical path `B,C`.
- Empty input and all-zero durations follow the spec; a cycle, unknown ID or duplicate edge is rejected; every emitted edge respects order and earliest times.
- For 200 seeded DAGs of at most 10 tasks, compare project duration to exhaustive enumeration of directed paths, and verify that the returned path uses edges and sums to that duration.
- Benchmark 1,000, 5,000 and 10,000 vertices with four forward edges per vertex where possible; also run a dense 500-vertex DAG. Report five-run medians, vertices, edges and peak ready-heap size.
- Explain `O((V+E) log V)` as a safe heap-based bound, `O(V+E)` graph storage, and why the critical path is only a lower bound with limited workers.

## Stretch goals
- Produce a concrete schedule for a fixed number of workers and compare its makespan with the critical-path lower bound.
- Report one actual cycle on failure using an iterative DFS of the remaining subgraph.

## Hints
- Use the [graph representation](https://jeffe.cs.illinois.edu/teaching/algorithms/book/05-graphs.pdf#page=6) to orient every edge consistently from prerequisite to dependent.
- The [dynamic programming perspective](https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=2) applies after a topological order exists.
