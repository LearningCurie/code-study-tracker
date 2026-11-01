---
key: projectnetwork
name: Build a route planner
stage: network
summary: Model a weighted network and compare shortest-path results with a reference.
why: Graph modelling and path reconstruction are as important as selecting the search algorithm.
outcomes:
- Represent directed weighted edges and reconstruct a shortest path.
- Verify Dijkstra against a small exhaustive reference.
cues:
- The cheapest route can involve more edges than a direct route.
- Edge weights are nonnegative.
traps:
- Marking a node final when it is first inserted into the heap.
- Accepting negative weights without changing algorithms.
---

=== build | Weighted delivery routes | 6-8 h
goal: Find deterministic minimum-cost routes through a directed network.
link: Dijkstra proof | https://cp-algorithms.com/graph/dijkstra.html#proof | Understand when a popped distance is final.
link: Graph representation | https://jeffe.cs.illinois.edu/teaching/algorithms/book/05-graphs.pdf#page=6 | Review vertices, edges and adjacency.

## The brief
Build a command-line route calculator for a static map. A route is a sequence of directed edges and its cost is their sum; no live traffic or negative weights are supported.

## Spec
Input lists unique string vertex IDs and directed `(from, to, weight)` edges with nonnegative integer weights. Reject unknown vertices and negative weights; allow parallel edges and self-loops. Given a valid source and destination, return minimum cost and a path, or an explicit unreachable result. For source equal to destination return cost zero and the single vertex.

Use adjacency lists and Dijkstra with a min-heap; ignore stale heap entries. Sort adjacency entries by `(destination, weight)` and use `(distance, vertex_id)` heap keys; update parents only on strict improvement so ties are reproducible. A reference Bellman-Ford implementation on small graphs checks distances. Verify returned paths using actual edges; parallel-edge tests should retain the selected edge's weight or edge identity.

## Milestones
1. **1-2 h:** Define graph input and write the reference distance calculator.
2. **1-2 h:** Implement Dijkstra, edge-aware parent reconstruction and unreachable handling.
3. **1-2 h:** Differential-test seeded graphs, ties, zero edges and invalid weights.
4. **1-2 h:** Measure graph families and document heap and adjacency costs.

## Done when
- Edges `A->B:5`, `A->C:1`, `C->B:1` give `A,C,B` with cost 2; an isolated destination is unreachable.
- Source-to-self gives zero; zero-weight and parallel edges work; negative weights and missing vertices are rejected.
- At least 200 seeded graphs of up to 12 vertices agree with Bellman-Ford on all destination distances; every returned path's edge weights sum to its reported distance.
- Benchmark sparse directed graphs of 1,000, 5,000 and 10,000 vertices with four generated edges per vertex. Report five-run median query time, relaxations and maximum heap entries; exclude graph generation.
- For lazy heap insertion state `O((V+E) log(V+E))` time and `O(V+E)` graph and heap space; explain stale entries.

## Stretch goals
- Add unweighted BFS and compare hop count with weighted cost.
- Return all distances for a source and test against individual destination requests.

## Hints
- The [Dijkstra proof](https://cp-algorithms.com/graph/dijkstra.html#proof) explains why nonnegative edges matter.
- Use an [adjacency representation](https://jeffe.cs.illinois.edu/teaching/algorithms/book/05-graphs.pdf#page=6) so relaxation visits only outgoing edges.
