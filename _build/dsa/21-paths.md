---
key: paths
name: Weighted shortest paths
stage: network
summary: Dijkstra, Bellman-Ford, 0-1 BFS, Floyd-Warshall, DAG relaxation and A*, when each one is correct, what each costs, and how routers and map services use them.
why: Once edges carry costs (minutes, euros, latency, risk), "fewest hops" is no longer the question and BFS is no longer right. Every algorithm in this module repeats one move, relaxing an edge that offers a shorter route, in an order that makes the answer provably final; which order is safe depends on the weights, so choosing the algorithm means reading the weights. Interviewers use these problems to see whether you can model costs and states as a graph and pick what the weights permit. Production systems run them constantly: OSPF routers rerun Dijkstra whenever a link changes, RIP is a distributed Bellman-Ford, and map services answer route queries in milliseconds by preprocessing road graphs.
outcomes:
- Implement Dijkstra with heapq and lazy deletion from memory, and prove that a popped distance is final
- Build the counterexample that breaks Dijkstra on a negative edge, and use Bellman-Ford for negative edges, negative-cycle detection and "at most k edges" limits
- Solve 0/1-weight problems in linear time with a deque, and bottleneck or stateful problems with a modified Dijkstra
- Compute all-pairs distances with Floyd-Warshall and explain why the intermediate vertex must be the outer loop
- Relax a DAG in topological order for shortest, longest and counted paths, and recognise it as dynamic programming
- Choose an algorithm from the weights, the graph and the query pattern, and use A* with an admissible heuristic
cues:
- Edges or moves have different costs and you want the minimum total (time, price, effort, risk)
- "At most k stops" or "within k moves" on a weighted graph
- Costs are only 0 or 1, such as free moves and paid moves on a grid
- The cost of a route is its worst edge (minimise the maximum) or a product of probabilities
- Distances between every pair of a few hundred places, or the number of cheapest routes
traps:
- Using BFS when weights differ, or Dijkstra when some weight is negative
- Marking a vertex as done when it is pushed instead of when it is popped, which freezes the first route found
- Relaxing in place during a hop-limited Bellman-Ford round, so one round sneaks in several edges
- Putting the intermediate vertex k in an inner loop of Floyd-Warshall
- Stopping A* when the target is first pushed, or using a heuristic that can overestimate
systems:
- OSPF and IS-IS routers flood link states and run Dijkstra to build a shortest-path tree; the first hop of each tree path becomes the forwarding entry (RFC 2328, sections 16.1 and 16.1.1)
- RIP is distance-vector routing, a distributed Bellman-Ford, with a metric of 16 meaning "unreachable" so that routing loops cannot count upwards forever (RFC 2453)
- OSRM, the open-source router for OpenStreetMap data, preprocesses road graphs with contraction hierarchies or multi-level Dijkstra so each query touches a tiny part of the graph
- Game engines move units with A* over grids and navigation meshes; arbitrage detection looks for a negative cycle after replacing each exchange rate r by -log r
further:
- Chapter · 60 min | Erickson, Algorithms ch. 8: generic relaxation (p. 4), Dijkstra (pp. 12-16), Bellman-Ford (pp. 17-24) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/08-sssp.pdf#page=4
- Notes · 20 min | MIT 6.006 (Spring 2020) lecture 13: Dijkstra, with the table comparing BFS, DAG relaxation, Bellman-Ford and Dijkstra | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/d819e7f4568aced8d5b59e03db6c7b67_MIT6_006S20_lec13.pdf
- Visualisation · 15 min | VisuAlgo: single-source shortest paths (run Dijkstra and Bellman-Ford on graphs with negative edges) | https://visualgo.net/en/sssp
- Visualisation · 20 min | Red Blob Games: Introduction to A* (BFS, Dijkstra, greedy best-first and A* side by side) | https://www.redblobgames.com/pathfinding/a-star/introduction.html#dijkstra
bank: paths advgraph
---

=== primer | How does Dijkstra's algorithm find shortest paths, and why is a popped distance final? | 18 min
goal: Implement Dijkstra with heapq and lazy deletion, trace its heap including stale entries, and prove that each popped distance is final
tag: paths-dijkstra | Dijkstra with a lazy heap
link: cp-algorithms: Dijkstra's algorithm | https://cp-algorithms.com/graph/dijkstra.html#proof | 10 min: the 'Proof' section (the same argument as below, in different words), then 'Restoring Shortest Paths'
link: cp-algorithms: Dijkstra on sparse graphs | https://cp-algorithms.com/graph/dijkstra_sparse.html#priority_queue | 5 min: the 'priority_queue' section, on why the stale-entry check is required and what it costs without it
practice: 743, 1514

> [!key]
> Dijkstra finalises vertices in order of their distance from the source. A min-heap holds tentative distances; each pop takes the closest unfinished vertex, and with **non-negative weights** that distance is already final, because any other route would have to leave the finished region through a vertex that is at least as far away. Relaxing the popped vertex's edges improves its neighbours. With `heapq` and **lazy deletion** (skip stale entries) it runs in O((V + E) log V).

## Intuition

BFS finds the route with the fewest edges, which is the cheapest route only when every edge costs the same. Give the edges weights and BFS is simply wrong:

```text
        10
   A ---------> B        BFS: B is one hop away, so dist(B) = 10
   |            ^        truth: A -> C -> B costs 1 + 1 = 2
 1 |            | 1
   +---> C -----+
```

Picture water poured in at the source and flowing along every pipe at the same speed, a pipe's weight being its length. Vertices get wet in order of distance, and the moment a vertex gets wet you know its distance: nothing can reach it sooner. Dijkstra simulates that wavefront. It does not move water continuously; it jumps from event to event ("the next vertex to get wet"), and a priority queue tells it which event comes next.

## How it works

### Relaxation, the one move

Keep `dist[v]`, the cost of the best route to v found so far (infinity at first, 0 for the source). **Relaxing** the edge u -> v with weight w asks: is going through u better?

```text
if dist[u] + w < dist[v]:  dist[v] = dist[u] + w;  parent[v] = u
```

`dist[v]` only ever goes down, and it is always the cost of a real route, so it is an upper bound on the true distance. Every algorithm in this module is "relax edges until nothing improves"; they differ only in the order of relaxations, and the order is what makes each one fast and correct for its kind of weights.

### The loop

1. Push `(0, source)` on a min-heap.
2. Pop the smallest `(d, u)`. If `d > dist[u]`, the entry is **stale** (u was already reached more cheaply): skip it.
3. Otherwise u is **final**. Relax each edge u -> v; whenever `dist[v]` improves, push `(dist[v], v)`.
4. Repeat until the heap is empty (or until the target is popped, if you want one target).

Python's `heapq` has no "decrease key", so instead of updating an entry in place you push a second, smaller entry and let the old one go stale. That is **lazy deletion**: simpler and usually faster in Python than an indexed heap.

### Why a popped distance is final

Invariant: *every finalised vertex holds its true distance, and every other vertex holds the cheapest route whose vertices, except the last, are all finalised.*

Suppose the first failure happens when `(d, u)` is popped (not stale) but some route P from the source to u costs less than d. P starts inside the finalised set and ends at u, outside it. Walk along P to the first edge x -> y that leaves the set: x is finalised, y is not. When x was finalised its edges were relaxed, and x's distance was correct (this is the first failure), so `dist[y]` is at most the cost of P up to y. All weights are non-negative, so the cost of P up to y is at most the cost of all of P, which is less than d. So the heap contains `(dist[y], y)` with a key below d. But a heap pops its smallest key, and it popped d. Contradiction. (If y is u itself, then `dist[u] < d`, contradicting `d == dist[u]`.)

The proof uses non-negativity in exactly one place: "a prefix of P costs no more than P". The next card shows what happens without it.

## Cost

- Each vertex is finalised once, so each adjacency list is scanned once: O(E) relaxations in total.
- Each successful relaxation pushes one entry, so at most E + 1 entries ever enter the heap, and at most E + 1 pops happen (stale ones included).
- Each push or pop costs O(log(heap size)) = O(log E), and log E is at most log V² = 2 log V.
- Total: **O((V + E) log V) time, O(V + E) space** (the heap can hold E stale entries).

In CPython this runs a graph with 10^5 vertices and 3·10^5 edges in about 0.7 seconds. For dense graphs (E close to V²), the original array version, which scans all unfinished vertices for the minimum at each step, costs O(V²) and beats O(V² log V). Fibonacci heaps reach O(E + V log V) on paper but lose to a binary heap in practice.

## When to use it

Use Dijkstra for a single source (or a single source and target) when every weight is **non-negative**: travel times, prices, latencies, efforts. Python handles V and E up to a few hundred thousand.

Prefer something else when the weights allow it: BFS when all weights are equal, the 0-1 BFS deque when weights are 0 or 1, relaxation in topological order on a DAG (all three are O(V + E)), and Bellman-Ford when some weight is negative. The choosing card later in this module puts them all in one table.

## Worked trace

Edges: A->B 4, A->C 1, C->B 2, B->D 1, C->D 5, C->E 8, D->E 3. The heap is listed smallest first (inside `heapq` the array order differs).

```steps
Start: dist[A] = 0, everything else unknown; the heap holds only the source
    dist   A=0   B=inf  C=inf  D=inf  E=inf
    final  { }
    heap   (0,A)
---
Pop (0,A): A is final. Relax A->B (0+4) and A->C (0+1); both improve, so push both
    dist   A=0   B={{4}}    C={{1}}    D=inf  E=inf
    final  {A}
    heap   (1,C) (4,B)
---
Pop (1,C): final. C->B gives 1+2 = 3 < 4, so B improves and (3,B) is pushed; (4,B) is now **stale**. C->D gives 6, C->E gives 9
    dist   A=0   B={{3}}    C=1    D={{6}}    E={{9}}
    final  {A, C}
    heap   (3,B) (4,B)stale (6,D) (9,E)
---
Pop (3,B): final at 3. B->D gives 3+1 = 4 < 6, push (4,D); (6,D) goes stale
    dist   A=0   B=3    C=1    D={{4}}    E=9
    final  {A, C, B}
    heap   (4,B)stale (4,D) (6,D)stale (9,E)
---
Pop (4,B): 4 > dist[B] = 3, so it is stale. Skip it without relaxing anything
    dist   A=0   B=3    C=1    D=4    E=9
    final  {A, C, B}
    heap   {{(4,D)}} (6,D)stale (9,E)
---
Pop (4,D): final. D->E gives 4+3 = 7 < 9, push (7,E); (9,E) goes stale
    dist   A=0   B=3    C=1    D=4    E={{7}}
    final  {A, C, B, D}
    heap   (6,D)stale (7,E) (9,E)stale
---
Pop (6,D): stale, skip. Pop (7,E): final. Pop (9,E): stale, skip. The heap is empty
    dist   A=0   B=3    C=1    D=4    E=7
    final  {A, C, B, D, E}
    parent B<-C  C<-A  D<-B  E<-D, so the route to E is A C B D E
```

Three of the eight pops were stale. Each was skipped in O(log V) without touching any edges, which is why lazy deletion stays within the bound.

## Template

```python
import heapq


def dijkstra(graph, src):
    """Shortest distances from src. graph[u] is a list of (v, w) pairs with w >= 0.
    Returns (dist, parent); unreachable vertices keep dist inf and parent -1."""
    dist = [float("inf")] * len(graph)
    parent = [-1] * len(graph)
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:                  # stale entry: u was finalised with a smaller distance
            continue
        for v, w in graph[u]:
            if d + w < dist[v]:          # relax u -> v
                dist[v] = d + w
                parent[v] = u
                heapq.heappush(heap, (dist[v], v))
    return dist, parent


def path_to(parent, t):
    """Vertices from the source to t (call only if t is reachable)."""
    path = []
    while t != -1:
        path.append(t)
        t = parent[t]
    return path[::-1]
```

Build `graph` as `[[] for _ in range(n)]` and append `(v, w)` for each edge (both directions if undirected). For a single target, `return d` as soon as you pop it.

## Pitfalls

- **Marking visited on push** (the BFS habit) freezes the first route found to each vertex. On the trace graph it reports B = 4.
- **No stale check.** The answer stays correct, but every stale pop rescans an adjacency list, which can blow the cost up towards O(V·E).
- **Stopping when the target is pushed** instead of popped: a pushed distance can still improve.
- **Unreachable vertices** keep `inf`; convert to the problem's -1 at the end, and never add to `inf` in languages where it is a large integer.
- **Ties with incomparable payloads.** `(dist, node)` tuples compare the node on ties; if nodes are objects, push `(dist, counter, node)`.
- **C++ and Java:** `priority_queue` is a max-heap by default (use `greater<>` or negate), and sums need `long long`.

## Check yourself

Q: Rerun the trace with C->B weighing 5 instead of 2. Which heap entries end up stale, and what is dist[E]?
A: Popping C no longer improves B (1 + 5 = 6 > 4), so only (6,D) and (9,E) go stale: B is popped at 4 and improves D to 5, and D improves E to 8. dist[E] = 8 along A B D E.

Q: Where exactly does the finality proof need non-negative weights?
A: In "the cost of P up to y is at most the cost of all of P". The rest of P, from y to u, must cost at least zero. With a negative edge after y the prefix could cost more than d while the whole route costs less, so y's heap key would not be below d and the contradiction disappears.

Q: A colleague adds `seen = {src}` and pushes a neighbour only `if v not in seen`, adding it to `seen` at that moment. Why is this wrong, and what does it print for B on the trace graph?
A: It fixes each vertex's distance the first time the vertex is discovered, which is BFS discovery order, not distance order. B is discovered from A with 4 and the later improvement through C (3) is ignored, so it prints 4.

Q: You need distances from one source in a road network with 2·10^5 junctions and travel times, then in a maze where every step costs 1. Which algorithm for each, and why?
A: Dijkstra for the road network: non-negative, unequal weights, O((V + E) log V) is well under a second. Plain BFS for the maze: with equal weights, BFS order is distance order, so you get the same answer in O(V + E) without a heap.

## Lab

- **743 Network Delay Time.** Brute force first: relax every edge repeatedly until nothing changes (O(V·E)). Then Dijkstra from k; the answer is the largest distance, or -1 if some node is unreachable. Expected: O(E log V); for `n = 4, k = 1, times = [[1,2,4],[1,3,1],[3,2,2],[2,4,1],[3,4,6]]` the answer is 4, and for `n = 3, k = 1, times = [[1,2,4],[3,2,1]]` it is -1.
- **1514 Path with Maximum Probability.** Same loop with a max-heap (push negated probabilities) and multiplication instead of addition; multiplying by a probability never increases the value, which is what the finality proof needs. Expected: O(E log V); for `n = 4, edges = [[0,1],[1,3],[0,2],[2,3],[0,3]], succProb = [0.9,0.8,0.5,0.5,0.6], start = 0, end = 3` the answer is 0.72 (up to float rounding); with no route it is 0.

> [!know]
> You now know how to run Dijkstra with a lazy heap, trace its stale entries, and prove why a popped distance never changes.

=== primer | Why do negative edges break Dijkstra, and how does Bellman-Ford handle them and "at most k stops"? | 16 min
goal: Build the counterexample that breaks Dijkstra, run Bellman-Ford with negative-cycle detection, and answer hop-limited queries by relaxing from last round's copy
tag: paths-bellman | Bellman-Ford and hop limits
link: cp-algorithms: Bellman-Ford | https://cp-algorithms.com/graph/bellman_ford.html#the-proof-of-the-algorithm | 10 min: 'The proof of the algorithm', 'The case of a negative cycle' and the short SPFA section after it
link: Erickson, Algorithms ch. 8 | https://jeffe.cs.illinois.edu/teaching/algorithms/book/08-sssp.pdf#page=18 | 15 min: PDF pages 18-23, a full run of Dijkstra on a graph with negative edges (figure on page 18), then 'Relax ALL the Edges: Bellman-Ford' up to its dynamic programming formulation
practice: 787

> [!key]
> With a negative edge, a vertex that Dijkstra has already finalised can still get cheaper, so "popped means final" is false. **Bellman-Ford** makes no such bet: it relaxes every edge, round after round, and after round i each vertex is at least as good as the best route with at most i edges. V - 1 rounds suffice without negative cycles; an edge that still improves in round V proves a **negative cycle**; and stopping after k rounds, while reading only the previous round's values, answers "at most k edges". Cost O(V·E).

## Intuition

Here is the smallest graph that breaks Dijkstra:

```text
       2          1
  S ------> A ------> T        S A T      costs 2 + 1     = 3
  |         ^                  S B A T    costs 3 - 2 + 1 = 2
 3|         | -2
  +-> B ----+
```

Textbook Dijkstra, with a set of finished vertices, pops S, then A at distance 2 and declares it final, so T gets 3. Then it pops B at 3; the edge B -> A would give A a distance of 1, but A is finished and never looks at its edges again. It reports A = 2 and T = 3; the truth is 1 and 2. The proof broke exactly where the last card said it would: the prefix S B costs 3, more than the whole route to A.

Two tempting fixes do not work:

- **Re-expanding vertices whose distance drops** (the lazy template happens to do this) gives the right answer, but "final" no longer means anything, and on bad graphs vertices are re-expanded exponentially often (Erickson's chapter 8 builds such graphs).
- **Adding a constant to every weight** punishes routes with many edges. Add 2 here and S A T costs 4 + 3 = 7 while S B A T costs 5 + 0 + 3 = 8, so the shifted graph prefers the route that is really more expensive. (Johnson's algorithm reweights with a potential per vertex instead, which preserves route order; it is the correct version of this idea.)

Negative weights are real: refunds, energy recovered going downhill, and -log of an exchange rate.

## How it works

### Rounds of relaxation

Relax every edge once; that is a round. Repeat V - 1 times.

The invariant, by induction on i: *after round i, `dist[v]` is at most the cost of the cheapest route to v with at most i edges.* The cheapest such route is a cheapest route with at most i - 1 edges to some u, plus the edge u -> v. After round i - 1, `dist[u]` is at most that cost, and round i relaxes u -> v. (Within a round, in-place updates can only make values better than the bound, which is harmless here.)

Why V - 1 rounds? If no negative cycle exists, some shortest route repeats no vertex (cutting out a cycle never makes a route more expensive), and a route without repeats has at most V - 1 edges. If a round changes nothing, every later round would change nothing either, so stop early.

### Detecting a negative cycle

After V - 1 rounds, relax every edge once more. If any `dist` still drops, a **negative cycle** is reachable from the source and "shortest" is undefined there (go round the cycle again and the cost falls further). Conversely, if no edge can be relaxed, then `dist[v] <= dist[u] + w` for every edge, and adding these inequalities around any reachable cycle shows its total weight is at least zero.

This is how arbitrage is detected: give each exchange edge the weight -log(rate). A cycle whose rates multiply to more than 1 has a negative total weight.

### At most k edges

For "at most k edges" (k stops means k + 1 flights), the in-place shortcut becomes a bug: an update made early in a round can be used later in the **same** round, so one round can add several edges. Read from a copy of the previous round and write into the current one; then after round i, `dist[v]` is exactly the cheapest route with at most i edges.

## Cost

V - 1 rounds of E relaxations: **O(V·E) time, O(V) space**; the hop-limited version costs O(k·E) time and O(V) extra for the copy. Early exit helps on typical inputs but not in the worst case. With V = 10^4 and E = 10^5 that is up to 10^9 relaxations, far too slow for Python, so Bellman-Ford is a tool for small graphs, small k, or graphs where Dijkstra is not allowed. SPFA (relax only out of vertices whose distance just changed, using a queue) is often faster in practice but has the same worst case.

## When to use it

| Situation | Use |
|---|---|
| Some weights negative, graph small (V·E up to about 10^7 in Python) | Bellman-Ford |
| "Does a negative cycle exist?" (arbitrage, inconsistent constraints) | Bellman-Ford's extra round |
| At most k edges, any weights | k rounds, reading last round's copy |
| At most k edges, non-negative weights, k large | Dijkstra over (vertex, edges used) states |
| Each node knows only its neighbours (routers) | distributed Bellman-Ford: distance-vector routing such as RIP |
| Negative weights but the graph is a DAG | relax in topological order, O(V + E) |
| All weights non-negative, no hop limit | Dijkstra |

## Worked trace

Edges, in this order: 0->1 100, 1->2 100, 0->2 500, 2->3 100, 1->3 600. Cheapest route from 0 to 3 with at most 1, 2 and 3 edges.

```steps
Before any round: only the source is known
    dist   0   inf   inf   inf
---
Round 1 reads prev = [0, inf, inf, inf]: only edges out of 0 can help. No edge 0->3, so "at most 1 edge" is impossible
    prev   0   inf   inf   inf
    dist   0   {{100}}   {{500}}   inf
---
Round 2 reads prev = [0, 100, 500, inf]: 1->2 gives 200, 2->3 gives 500+100 = 600, 1->3 gives 700. Best with at most 2 edges: 600
    prev   0   100   500   inf
    dist   0   100   {{200}}   {{600}}
---
Round 3 reads prev = [0, 100, 200, 600]: 2->3 now gives 200+100 = 300, the three-edge route 0 1 2 3
    prev   0   100   200   600
    dist   0   100   200   {{300}}
---
The bug: one round **in place**. 0->1 writes 100, 1->2 reads that fresh 100 and writes 200, 2->3 reads the fresh 200 and writes 300. "One round" has used three edges
    dist   0   {{100}}   {{200}}   {{300}}
```

## Template

```python
def bellman_ford(n, edges, src):
    """edges: (u, v, w) triples, w may be negative.
    Returns the distance list, or None if a negative cycle is reachable from src."""
    dist = [float("inf")] * n
    dist[src] = 0
    for _ in range(n - 1):
        changed = False
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                changed = True
        if not changed:                  # nothing moved: every distance is final
            break
    for u, v, w in edges:
        if dist[u] + w < dist[v]:        # still tense after n - 1 rounds
            return None
    return dist


def cheapest_with_at_most(n, edges, src, dst, max_edges):
    """Cheapest src -> dst cost using at most max_edges edges (inf if impossible)."""
    dist = [float("inf")] * n
    dist[src] = 0
    for _ in range(max_edges):
        prev = dist[:]                   # read last round, write this round
        for u, v, w in edges:
            if prev[u] + w < dist[v]:
                dist[v] = prev[u] + w
    return dist[dst]
```

## Pitfalls

- **In-place hop-limited rounds.** Whether the bug shows depends on the edge order (with the edges above reversed, one in-place round happens to be right), so a few passing tests prove nothing.
- **Off by one.** k stops means k + 1 edges.
- **Infinity arithmetic.** In Python `float("inf") + (-5)` is still infinity, so unreachable vertices never relax anything. In C++ or Java, guard with `dist[u] != INF` or INF minus a weight becomes a real-looking number.
- **Which cycles you detect.** Only cycles reachable from the source show up. To find a negative cycle anywhere, start every vertex at 0 (as if a virtual source had a 0-weight edge to each).
- **Vertices behind a negative cycle** have no shortest distance at all (minus infinity); if you must report them, mark everything reachable from a vertex that still relaxed.
- **Undirected graphs.** One negative undirected edge is already a negative cycle (u -> v -> u).

## Check yourself

Q: Run one in-place round on the trace graph, but with the edge list in reverse order (1->3 first, 0->1 last). What is dist after that round, and what does it tell you about testing the in-place version?
A: dist = [0, 100, 500, inf]: when 1->3, 2->3 and 1->2 are relaxed, their sources are still infinite, and only 0->2 and 0->1 improve. That is the correct "at most one edge" answer, so the in-place bug hides for some edge orders. Tests must use edge orders that let fresh values flow forwards in the same round, or better, compare against a brute force.

Q: Why do V - 1 rounds always suffice when there is no negative cycle?
A: After round i every vertex is at least as good as its best route with at most i edges. Without negative cycles, removing a cycle from a route never raises its cost, so some shortest route repeats no vertex and therefore has at most V - 1 edges. After round V - 1 every vertex is at least as good as that route, and no value can go lower than the true distance.

Q: The exchange rates are USD to EUR 0.9, EUR to GBP 0.9 and GBP to USD 1.3. How would Bellman-Ford spot the arbitrage, and what is the cycle's weight?
A: Use weight -ln(rate) on each edge. The cycle's weight is -ln(0.9 × 0.9 × 1.3) = -ln(1.053), about -0.052, which is negative, so the extra round still finds a relaxable edge. A negative cycle means the product of the rates exceeds 1: converting round the loop makes money.

## Lab

- **787 Cheapest Flights Within K Stops.** Run k + 1 rounds that read last round's copy. Expected: O(k·E) time, O(n) space; with `n = 4, flights = [[0,1,100],[1,2,100],[0,2,500],[2,3,100],[1,3,600]], src = 0, dst = 3` the answers for k = 0, 1, 2 are -1, 600 and 300. Then rerun with in-place updates and find an edge order that gives a wrong answer.
- **Exercise: detect a negative cycle.** Expected: `bellman_ford(4, [(0,1,1),(1,2,-2),(2,1,1),(2,3,4)], 0)` returns None (1 -> 2 -> 1 weighs -1), and removing the edge (2,1,1) gives `[0, 1, -1, 3]`.

> [!know]
> You now know why negative edges break Dijkstra and how to use Bellman-Ford for negative weights, negative cycles and hop limits.

=== primer | How do you find shortest paths when every edge costs 0 or 1? | 13 min
goal: Replace Dijkstra's heap with a deque for 0/1 weights, explain why the deque stays sorted, and model "free move or paid move" grids as 0-1 graphs
tag: paths-01bfs | 0-1 BFS with a deque
link: cp-algorithms: 0-1 BFS | https://cp-algorithms.com/graph/01_bfs.html#algorithm | 5 min: 'Algorithm', then 'Dial's algorithm' for small integer weights
link: USACO Guide: 0/1 BFS | https://usaco.guide/gold/unweighted-shortest-paths#extension---01-bfs | 10 min: 'Extension - 0/1 BFS' and its worked grid problem 'Tracks in the Snow'
practice: 2290, 1368

> [!key]
> With weights of only 0 and 1, Dijkstra's heap only ever holds two distinct keys, d and d + 1. A **deque** can do the heap's job: a vertex reached through a 0-edge has the same distance as the current one, so it goes to the **front**; a vertex reached through a 1-edge goes to the **back**. The deque stays sorted, popping the front is exactly Dijkstra's order, and the whole search costs O(V + E).

## Intuition

Many grid problems have two kinds of moves: free ones and paid ones. Walking on empty cells is free but entering a wall cell means breaking it (cost 1); following the arrow printed in a cell is free but going any other way means repainting the arrow (cost 1). The question is always "the fewest paid moves".

Think in layers, as in BFS. Layer d holds every cell reachable with exactly d paid moves. A free move does not leave the layer, so the cell it reaches must be handled before anything in layer d + 1: put it at the front of the queue. A paid move reaches the next layer: put it at the back.

## How it works

Pop u from the front. For each edge u -> v with weight w, relax: if `dist[u] + w < dist[v]`, update and push v to the front when w = 0, to the back when w = 1.

**Invariant:** *reading the distances recorded when each entry was pushed, the deque is sorted from front to back and spans at most two values, d at the front and d + 1.* Popping u at distance d: a 0-edge neighbour gets d and goes to the front, which keeps the order; a 1-edge neighbour gets d + 1 and goes to the back, and the back was at most d + 1. So vertices are popped in non-decreasing distance order, which is all that Dijkstra's finality proof needs.

A vertex can be in the deque twice: first at d + 1 through a 1-edge, then at d through a 0-edge. The old copy is popped later and its relaxations improve nothing, so it is harmless. It cannot happen a third time: once a vertex holds d, the smallest value in the deque, nothing can lower it.

Grids become graphs with one vertex per cell. Decide whether the cost belongs to the **move** (an arrow cell: moving its way is free) or to the **destination** (an obstacle cell: entering it costs 1), and keep the start cell free.

**Dial's algorithm** generalises the trick: for integer weights 0..C keep C + 1 buckets in rotation, O(V·C + E). If every weight is 0 or c, run 0-1 BFS with c treated as 1 and multiply the answer by c.

## Cost

Each vertex enters the deque at most twice and each edge is relaxed once per pop of its source, so the work is **O(V + E) time and O(V) space**. `collections.deque` appends and pops at both ends in O(1) (it is a linked list of fixed-size blocks). On a 500 × 500 grid of random free and wall cells this version took 0.29 s against 0.72 s for heap-based Dijkstra, the same answer about 2.5 times faster, because there is no log factor and no tuple comparisons.

## When to use it

| Weights | Algorithm | Cost |
|---|---|---|
| all equal | BFS | O(V + E) |
| only 0 and 1 (or 0 and c) | 0-1 BFS | O(V + E) |
| small integers 0..C | Dial's buckets | O(V·C + E) |
| any non-negative | Dijkstra | O((V + E) log V) |

Cues: "minimum number of walls to break", "fewest changes or flips", "free unless", "cost 1 to switch direction". If the weights are 1 and 2, this is not 0-1 BFS: use Dijkstra, Dial's buckets, or split every 2-edge into two 1-edges through a new vertex and run plain BFS.

## Worked trace

Edges: S->A 1, S->B 0, B->A 0, A->C 1, B->C 1, C->D 0.

```text
   S --1--> A --1--> C --0--> D
   |        ^        ^
   0        0        1
   |        |        |
   +------> B -------+
```

```steps
Start: the deque holds the source
    dist   S=0  A=inf  B=inf  C=inf  D=inf
    deque  [S]
---
Pop S (0). S->A costs 1: A = 1, push to the **back**. S->B costs 0: B = 0, push to the **front**
    dist   S=0  A={{1}}  B={{0}}  C=inf  D=inf
    deque  [B, A]
---
Pop B (0). B->A costs 0: A improves from 1 to 0 and goes to the front. B->C costs 1: C = 1, back. The old A entry is now a stale copy
    dist   S=0  A={{0}}  B=0  C={{1}}  D=inf
    deque  [A, A(stale), C]
---
Pop A (0). A->C would give 0+1 = 1, which is not below 1: nothing changes
    dist   S=0  A=0  B=0  C=1  D=inf
    deque  [A(stale), C]
---
Pop the stale copy of A. dist[A] is already 0, so its relaxations improve nothing: harmless
    dist   S=0  A=0  B=0  C=1  D=inf
    deque  [C]
---
Pop C (1). C->D costs 0: D = 1, front. Then pop D; the deque is empty
    dist   S=0  A=0  B=0  C=1  D={{1}}
    deque  []
```

## Template

```python
from collections import deque


def zero_one_bfs(graph, src):
    """graph[u] is a list of (v, w) with w in {0, 1}."""
    dist = [float("inf")] * len(graph)
    dist[src] = 0
    dq = deque([src])
    while dq:
        u = dq.popleft()
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                if w == 0:
                    dq.appendleft(v)     # same distance as u: serve it next
                else:
                    dq.append(v)         # one more than u: serve it later
    return dist
```

On a grid, use `(r, c)` pairs or the index `r * cols + c` as the vertex, generate the four neighbours inside the loop, and compute w from the move or the cell entered.

## Pitfalls

- **A list instead of a deque.** `list.insert(0, x)` shifts every element: O(n) per push.
- **A visited set filled on push** (the BFS habit). A vertex first reached by a paid move must stay improvable by a free one.
- **Cost on the wrong thing.** "Entering an obstacle costs 1" puts the weight on the destination cell; "moving against the arrow costs 1" puts it on the move from the source cell.
- **Weights that are not 0/1.** The deque silently stops being sorted and the answers are wrong without any error.
- **Early exit.** You may stop when the target is popped, as in Dijkstra, but not when it is first pushed: a later free move can still improve it.

## Check yourself

Q: In the trace, make S->B cost 1 instead of 0. What is the deque after popping S, and what are the final distances?
A: Both A and B get 1 and go to the back: [A, B]. Popping A gives C = 2 at the back: [B, C]. Popping B improves nothing (B->A gives 1, B->C gives 2). Popping C gives D = 2 at the front. Final: S 0, A 1, B 1, C 2, D 2.

Q: Why does the deque never hold three different distances?
A: The front holds the smallest value d, and every push is either d (front) or d + 1 (back), where d is the distance of the vertex being popped, which is the current minimum. Values below d cannot appear, because d is the smallest tentative distance among unfinished vertices, and values above d + 1 are never created while the front is d.

Q: A grid problem charges 0 for moving onto a road cell and 3 for moving onto grass. How do you solve it in linear time?
A: Every weight is 0 or 3, so run 0-1 BFS with grass moves weighing 1 and multiply the final answer by 3. If grass cost 3 and mud cost 5, that would no longer work: use Dial's buckets (C = 5) or Dijkstra.

## Lab

- **2290 Minimum Obstacle Removal to Reach Corner.** Entering an obstacle cell costs 1, anything else 0. Expected: O(mn) time and space; for `[[0,1,1,0],[1,1,0,1],[0,0,1,0]]` the answer is 2, and for `[[0,0,0],[1,1,0],[0,0,0]]` it is 0.
- **1368 Minimum Cost to Make at Least One Valid Path in a Grid.** Moving the way a cell's sign points is free, any other direction costs 1 (the sign is changed). Expected: O(mn); for `[[2,2],[2,2]]` the answer is 2, for `[[3,1,3],[4,4,3],[1,2,4]]` it is 1, and for `[[1,1,3],[4,2,3],[2,2,2]]` (already a valid path) it is 0.

> [!know]
> You now know how to run 0-1 BFS with a deque in linear time and model free-or-paid moves as 0/1 edges.

=== primer | How do you adapt Dijkstra when a route's cost is not a plain sum, or the state is more than a vertex? | 16 min
goal: Run Dijkstra on bottleneck and probability costs, and on augmented states such as (vertex, coupon used) or (cell, keys held), knowing exactly which cost rules keep it correct
tag: paths-variants | Dijkstra over costs and states
link: Wikipedia: Widest path problem | https://en.wikipedia.org/wiki/Widest_path_problem#Single_source | 5 min: the 'Single source' section, the bottleneck form of Dijkstra (here maximising the smallest edge) and why it can run as fast as sorting the edges
practice: 1631, cses:1195, 864

> [!key]
> Dijkstra's proof needs only two things from a route's cost: **extending a route never makes it better**, and **a better way to reach a vertex stays better after both routes are extended the same way**. Sums of non-negative weights, the maximum edge on a route, and products of probabilities (maximised) all qualify, so only the combine step changes. When the future depends on more than where you are (a coupon left, keys held, a station passed), make that information part of the **state** and run Dijkstra over (vertex, extra) pairs: a shortest path in a layered copy of the graph.

## Intuition

A lorry carrying a tall load cares only about the lowest bridge on its route; a hiker with bad knees cares only about the steepest step. Both want to minimise the *largest* edge, not the total, and both will happily take a long detour that avoids one bad edge. A message relayed over unreliable links arrives with the *product* of the link probabilities.

Now give a traveller one half-price ticket. Being in Lyon with the ticket unused and being in Lyon with it spent are different situations: the cheapest way to reach the first need not lead to the cheapest finish. So treat them as two vertices, Lyon-0 and Lyon-1. The graph becomes two copies of the map: ordinary edges inside each copy, and half-price edges from copy 0 to copy 1.

## How it works

### What the finality proof really needs

Write `extend(c, w)` for the cost of a route of cost c followed by an edge of weight w. Dijkstra stays correct when:

1. **Monotone:** `extend(c, w)` is never better than c. Otherwise a route through a far vertex could beat a near one, as with negative weights.
2. **Order-preserving:** if c1 is at least as good as c2, then `extend(c1, w)` is at least as good as `extend(c2, w)`. Then the best route to any vertex is a best route to the vertex before it plus one edge, so keeping one value per vertex loses nothing.

| Route cost | extend(c, w) | Heap order | Notes |
|---|---|---|---|
| total time or price | c + w, w >= 0 | smallest first | plain Dijkstra |
| bottleneck (worst step) | max(c, w) | smallest first | also: binary search on a limit plus BFS, or union-find adding edges in increasing order |
| reliability | c × p, 0 <= p <= 1 | largest first (push -c) | or use weights -log p and plain Dijkstra |
| (stops, price) priorities | add each component | lexicographic | Python compares tuples for you |

### Augmented states

When the best continuation depends on extra information, the state is (vertex, extra). Each state's edges are the vertex's edges, plus whatever changes the extra part: "use the coupon" moves from layer 0 to layer 1, "pick up key b" sets a bit in a key mask, "pass a fuel station" flips a flag. The answer is the best over all final states, for example `min(dist[(t, 0)], dist[(t, 1)])`. If every move costs 1, the same state graph needs only BFS.

## Cost

With k values of the extra part, there are S = V·k states and T = E·k transitions, so Dijkstra costs O((S + T) log S). One coupon doubles the graph; a mask of 6 keys multiplies a grid by 64; a remaining budget of up to 10^9 would multiply it by 10^9, so that state is not an option and the problem needs another idea. Changing only the combine step (max, product) leaves the cost at O((V + E) log V).

## When to use it

Cues: "minimise the largest height difference", "the earliest time the water level allows", "maximum probability of success", "you may use one discount, teleport or skip", "with the keys you have collected". Do not use it when the cost can improve as a route grows (rewards, negative weights), when you want the *longest* route (extending makes it better, so nothing is ever final), or when the extra information has too many values to enumerate.

## Worked trace

Bottleneck version: undirected edges S-A 4, S-B 7, A-B 2, A-C 9, B-C 3, C-T 5, B-T 8; a route costs its largest edge.

```steps
Pop (0,S). Neighbours get max(0, w): A = 4, B = 7
    best   S=0  A={{4}}  B={{7}}  C=inf  T=inf
    heap   (4,A) (7,B)
---
Pop (4,A): final. A-B gives max(4, 2) = 4 < 7, so B improves; A-C gives max(4, 9) = 9
    best   S=0  A=4  B={{4}}  C={{9}}  T=inf
    heap   (4,B) (7,B)stale (9,C)
---
Pop (4,B): final. B-C gives max(4, 3) = 4 < 9; B-T gives max(4, 8) = 8
    best   S=0  A=4  B=4  C={{4}}  T={{8}}
    heap   (4,C) (7,B)stale (8,T) (9,C)stale
---
Pop (4,C): final. C-T gives max(4, 5) = 5 < 8
    best   S=0  A=4  B=4  C=4  T={{5}}
    heap   (5,T) (7,B)stale (8,T)stale (9,C)stale
---
Pop (5,T): final. The best route is S A B C T with worst edge 5, four edges long, beating S B T (worst edge 8); the rest of the heap is stale
    best   S=0  A=4  B=4  C=4  {{T=5}}
```

## Template

```python
import heapq


def dijkstra_states(start, moves):
    """Dijkstra over any hashable, comparable states.
    moves(state, cost) yields (next_state, next_cost) with next_cost >= cost."""
    best = {start: 0}
    heap = [(0, start)]
    while heap:
        cost, s = heapq.heappop(heap)
        if cost > best[s]:
            continue
        for t, c in moves(s, cost):
            if c < best.get(t, float("inf")):
                best[t] = c
                heapq.heappush(heap, (c, t))
    return best


def bottleneck(graph, s, t):
    """Smallest possible largest edge on an s -> t route."""
    def moves(u, cost):
        for v, w in graph[u]:
            yield v, max(cost, w)
    return dijkstra_states(s, moves).get(t, float("inf"))


def via_station(graph, stations, s, t):
    """Cheapest s -> t route that passes through at least one vertex in stations."""
    def moves(state, cost):
        u, seen = state
        for v, w in graph[u]:
            yield (v, seen or v in stations), cost + w
    best = dijkstra_states((s, s in stations), moves)
    return best.get((t, True), float("inf"))
```

The dictionary makes the template work for any state shape; for speed, switch to arrays indexed by `vertex * k + extra` once the state is fixed.

## Pitfalls

- **Maximising with a min-heap.** Push the negated value (or transform with -log), or you will pop the worst state first.
- **States that cannot be compared.** Heap entries compare the state on equal costs: use tuples of ints and bools, and bitmask ints rather than sets for "keys held".
- **Forgetting the extra state.** Keeping one value per vertex lets the cheapest arrival, which may have spent the coupon, block a route that would finish cheaper.
- **Reading one final state.** The answer is usually the best over every value of the extra part at the target.
- **Floating-point products.** Tiny probabilities underflow towards 0; summing -log p is more robust.

## Check yourself

Q: In the trace, change A-B from 2 to 6. What is T's bottleneck value now, and along which route?
A: 6, along S A B C T (edges 4, 6, 3, 5). S B C T has worst edge 7, S B T has 8 and S A C T has 9. Dijkstra pops A at 4, then B at max(4, 6) = 6, then C at 6, and T at max(6, 5) = 6.

Q: Why can't Dijkstra find the route with the largest total weight, even with positive weights?
A: Extending a route makes it better, so the monotone condition fails: a popped vertex can always be improved by a longer route that reaches it later. Longest simple path is NP-hard in general graphs; in a DAG it is easy by topological order.

Q: With one half-price ticket, a friend suggests "find the cheapest route, then halve its most expensive edge". Give a counterexample.
A: Route 1 has edges 5 and 5 (total 10), route 2 has edges 1 and 11 (total 12). The plain cheapest is route 1, which becomes 2 + 5 = 7 after halving one 5 (rounding down). Route 2 with its 11 halved costs 1 + 5 = 6, which is better. The (vertex, used) states find 6.

## Lab

- **1631 Path With Minimum Effort.** Grid cells are vertices, an edge's weight is the height difference, and a route costs its largest edge. Expected: O(mn log(mn)); for `[[1,8,2],[2,9,3],[5,4,4]]` the answer is 3, and for the single cell `[[7]]` it is 0.
- **CSES 1195 Flight Discount.** States (city, coupon used); using the coupon on a flight costs `c // 2` and moves to layer 1. Expected: O((n + m) log n); with 4 cities and flights 1->2 3, 2->4 5, 1->3 8, 3->4 1, 2->3 2 the answer is 4 (1 2 3 4, halving the 3).
- **864 Shortest Path to Get All Keys** (stretch). Every move costs 1, so BFS over (row, col, key mask). Expected: O(mn·2^k); for `["@..aA", "..B#.", "....b"]` the answer is 6, and for `["@Aa"]` it is -1.

> [!know]
> You now know how to run Dijkstra on bottleneck, probability and lexicographic costs, and over augmented states such as coupons and keys.

=== primer | How does Floyd-Warshall find all-pairs shortest paths, and why must k be the outer loop? | 14 min
goal: Compute all-pairs distances with Floyd-Warshall, justify the loop order from its recurrence, and detect negative cycles from the diagonal
tag: paths-floyd | Floyd-Warshall all pairs
link: cp-algorithms: Floyd-Warshall | https://cp-algorithms.com/graph/all-pair-shortest-path-floyd-warshall.html#description-of-the-algorithm | 10 min: 'Description of the algorithm' (the phase argument), then 'Retrieving the sequence of vertices in the shortest path' and 'The case of negative cycles'
practice: 1334

> [!key]
> Floyd-Warshall is dynamic programming over **which vertices a route may pass through**. After phase k, `d[i][j]` is the shortest i -> j route whose intermediate vertices all lie in {0, ..., k}. Phase k asks one question per pair, "is it better to go through k?": `d[i][j] = min(d[i][j], d[i][k] + d[k][j])`. Three nested loops with **k outermost**: O(n³) time, O(n²) space, negative edges allowed, and a negative cycle shows up as `d[i][i] < 0`.

## Intuition

Think of airline hubs. Start with direct flights only: that is the distance table with no stopovers allowed. Now allow changing planes in Amsterdam: some pairs get cheaper. Then allow Dubai as well (Amsterdam stays allowed), and routes such as Lima, Amsterdam, Dubai, Perth appear, because the Lima to Dubai entry already includes the Amsterdam stop. After every airport has been allowed as a stopover, the table holds the true distances.

## How it works

### The recurrence

Let `d_k[i][j]` be the shortest i -> j route using only intermediates from {0..k}. Such a route either avoids k, costing `d_{k-1}[i][j]`, or passes through k exactly once (with no negative cycle, a shortest route need not repeat a vertex), splitting into an i -> k part and a k -> j part that use only {0..k-1}. So:

```text
d_k[i][j] = min( d_{k-1}[i][j],  d_{k-1}[i][k] + d_{k-1}[k][j] )
```

The base case `d_{-1}` is the edge matrix: 0 on the diagonal, the cheapest edge weight between i and j, infinity elsewhere. The answer is the last layer.

### One table is enough

Each layer depends only on the previous one, and during phase k row k and column k do not change: `d[i][k]` could only become `d[i][k] + d[k][k]`, and `d[k][k]` is 0 (unless k is on a negative cycle). So updating one n × n table in place is safe.

### Why k must be the outer loop

The recurrence says phase k needs the *finished* phase k - 1 for every pair. With k inside the i and j loops, `d[i][j]` is finalised while the entries it should combine are still incomplete. On the trace graph below, an i, j, k loop order reports `d[1][0] = 7` instead of 5: the route 1, 2, 3, 0 needs `d[1][3]` and `d[2][0]` to be improved first, and they are computed later in that order.

### Routes and negative cycles

To print routes, keep `nxt[i][j]`, the first hop on the best i -> j route: start with j for every edge, and set `nxt[i][j] = nxt[i][k]` whenever going through k wins. After the loops, `d[i][i] < 0` means i lies on a negative cycle, and any pair i, j with some such k reachable from i and reaching j has no shortest distance at all.

Replace min and + by `or` and `and` and the same loops compute reachability between every pair (Warshall's transitive closure).

## Cost

n phases × n² pairs: **O(n³) time, O(n²) space**, regardless of the number of edges. In CPython (with the row-caching template below) n = 200 took about 0.7 s and n = 400 about 7 s. A NumPy version that updates the whole matrix per phase, `d = np.minimum(d, d[:, k, None] + d[None, k, :])`, did n = 400 in about 0.6 s. The alternative for all pairs is Dijkstra from every vertex, O(n (n + m) log n), which wins on large sparse graphs with non-negative weights but cannot handle negative edges.

## When to use it

- All-pairs distances, or many queries, on a **small** graph: n up to about 400 in pure Python, a few thousand in C++ or NumPy.
- Negative edges are present (no negative cycles), or you need to detect negative cycles everywhere.
- A tiny alphabet of states with conversion costs (26 letters: 26³ = 17,576 steps) or a reachability matrix.
- Not for one source on a large sparse graph (use Dijkstra), and not for n = 10^4 (10^12 steps).

## Worked trace

Directed edges: 0->1 3, 0->3 7, 1->0 8, 1->2 2, 2->0 5, 2->3 1, 3->0 2. Rows are sources, columns are targets.

```steps
Before any phase: direct edges only (no intermediate vertices allowed)
    from\to   0    1    2    3
    0         0    3  inf    7
    1         8    0    2  inf
    2         5  inf    0    1
    3         2  inf  inf    0
---
k = 0: routes may now pass through 0. 1 0 3 = 8+7 = 15, 2 0 1 = 5+3 = 8, 3 0 1 = 2+3 = 5
    from\to   0    1    2    3
    0         0    3  inf    7
    1         8    0    2 {{15}}
    2         5  {{8}}    0    1
    3         2  {{5}}  inf    0
---
k = 1: also through 1. 0 1 2 = 3+2 = 5, and 3 .. 1 2 = 5+2 = 7 (the 5 already contains the stop at 0)
    from\to   0    1    2    3
    0         0    3  {{5}}    7
    1         8    0    2   15
    2         5    8    0    1
    3         2    5  {{7}}    0
---
k = 2: also through 2. 0 .. 2 3 = 5+1 = 6, 1 2 0 = 2+5 = 7, 1 2 3 = 2+1 = 3
    from\to   0    1    2    3
    0         0    3    5  {{6}}
    1         {{7}}    0    2  {{3}}
    2         5    8    0    1
    3         2    5    7    0
---
k = 3: also through 3. 1 .. 3 0 = 3+2 = 5, 2 3 0 = 1+2 = 3, 2 3 .. 1 = 1+5 = 6. These are the final distances
    from\to   0    1    2    3
    0         0    3    5    6
    1         {{5}}    0    2    3
    2         {{3}}  {{6}}    0    1
    3         2    5    7    0
```

## Template

```python
def floyd_warshall(n, edges):
    """All-pairs shortest distances; d[i][i] < 0 afterwards means i is on a negative cycle."""
    INF = float("inf")
    d = [[INF] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0
    for u, v, w in edges:
        d[u][v] = min(d[u][v], w)        # keep the cheapest parallel edge
    for k in range(n):                   # allow k as an intermediate vertex
        dk = d[k]
        for i in range(n):
            dik = d[i][k]
            if dik == INF:
                continue
            di = d[i]
            for j in range(n):
                if dik + dk[j] < di[j]:
                    di[j] = dik + dk[j]
    return d
```

Caching the rows `d[k]` and `d[i]` in locals and skipping unreachable `d[i][k]` roughly halves the time in CPython. For undirected graphs, add each edge in both directions.

## Pitfalls

- **k in an inner loop.** It still runs, still looks plausible, and is wrong (the trace graph gives 7 instead of 5 for 1 -> 0).
- **`[[INF] * n] * n`** makes n references to one row: every update changes every row. Build rows in a comprehension.
- **Initialisation.** Set the diagonal to 0 and keep the minimum of parallel edges; the last edge read is not necessarily the cheapest.
- **Infinity in C++ or Java.** INF + INF overflows a 32-bit or even 64-bit sentinel; skip pairs where `d[i][k]` is INF, as the template does.
- **Negative cycles.** Distances involving them are meaningless; check the diagonal before trusting any value.

## Check yourself

Q: After phase k = 1 in the trace, `d[3][2]` is 7. Which route is that, and why could phase 1 build it when 3 has no edge to 1?
A: 3 -> 0 -> 1 -> 2, costing 2 + 3 + 2. Phase 0 had already set `d[3][1] = 5` (the route 3 0 1, through vertex 0), and phase 1 combined it with `d[1][2] = 2`. Each phase builds on routes through all earlier intermediates.

Q: Why is it safe to update the table in place during phase k?
A: Phase k reads only row k and column k besides the cell it writes. `d[i][k]` would become `min(d[i][k], d[i][k] + d[k][k])`, and `d[k][k]` is 0, so row and column k do not change during the phase. Every value read is therefore the phase k - 1 value the recurrence asks for (or an equal one).

Q: You must convert one 10^5-character string into another, where changing letter x into letter y has a cost given by up to 2,000 rules that can be chained. How do you compute the total cheaply?
A: Make a 26-vertex graph with an edge x -> y per rule (keeping the cheapest), run Floyd-Warshall once (26³ steps), then sum `d[s[i]][t[i]]` over the positions, answering -1 if any entry is infinite. Total O(26³ + rules + length).

## Lab

- **1334 Find the City With the Smallest Number of Neighbors at a Threshold Distance.** Floyd-Warshall, then count, for each city, the others within the threshold; ties go to the largest index. Expected: O(n³) for n up to 100; with `n = 5, edges = [[0,1,2],[1,2,3],[2,3,1],[3,4,2],[0,4,9]], distanceThreshold = 4` the counts are [1, 3, 3, 3, 2] and the answer is 0; with `n = 4, edges = [[0,1,1],[1,2,5],[2,3,1]], distanceThreshold = 2` every city has one neighbour in range and the answer is 3.
- **Exercise: routes.** Add the `nxt` table to the template and print the route from 1 to 0 on the trace graph. Expected: 1 2 3 0 with cost 5.

> [!know]
> You now know how to compute all-pairs distances with Floyd-Warshall, why k is the outer loop, and how the diagonal reveals negative cycles.

=== primer | How do you find shortest and longest paths in a DAG in linear time, even with negative edges? | 14 min
goal: Relax a DAG in topological order for shortest, longest and counted routes, see why it is dynamic programming, and count shortest routes on the DAG that Dijkstra leaves behind
tag: paths-dag | Relaxation in topological order
link: Competitive Programmer's Handbook, section 16.2 | https://cses.fi/book/book.pdf#page=161 | 10 min: PDF pages 161-163, 'Dynamic programming' on DAGs (counting paths), then 'Extending Dijkstra's algorithm' (the DAG of shortest paths)
link: Erickson, Algorithms ch. 8 | https://jeffe.cs.illinois.edu/teaching/algorithms/book/08-sssp.pdf#page=11 | 10 min: PDF pages 11-12, shortest paths in a DAG written as a recurrence over incoming edges and as relaxation of outgoing edges in topological order
practice: 1976

> [!key]
> In a DAG, relax each vertex's outgoing edges **in topological order**. By the time you reach u, every edge into u has been relaxed from a vertex that was already final, so u is final too: one pass, **O(V + E)**, with any weights, negative included. Swap min for max and you get longest paths; swap it for a sum and you count routes. It is dynamic programming in disguise: `dist[v] = min(dist[u] + w)` over edges into v, evaluated so that inputs come first.

## Intuition

Dependencies have a direction and no loops: a course before the one that requires it, a build step before the step that uses its output, a cake baked before it is iced. In such a graph you never need to come back to a vertex. Process the vertices so that every arrow points forwards, and when you reach a vertex everything that can lead to it is already settled: there is nothing left to wait for.

## How it works

### Order, then one pass

Get a topological order with Kahn's algorithm (repeatedly take a vertex with no remaining incoming edges), then walk it once, relaxing every outgoing edge. Correctness, by induction along the order: the vertices before u are final; every edge into u starts at one of them and has been relaxed; so `dist[u]` is the minimum over all routes into u. Nothing in this argument looks at the sign of a weight, which is why negative edges are fine here while they break Dijkstra: the processing order comes from the structure, not from the distances.

### Longest paths and the critical path

Longest simple path is NP-hard in general graphs, but a DAG has no cycles to go round, so use max instead of min (start at minus infinity). This is the **critical path** of a project: with unlimited workers, the earliest finish time of a task is its duration plus the latest finish among its prerequisites, and the whole project takes as long as the longest chain.

### It is dynamic programming

The recurrence `dist[v] = min over edges (u, v) of dist[u] + w(u, v)`, with `dist[s] = 0`, is a DP whose subproblems are the vertices and whose dependencies are the edges; a topological order is a valid evaluation order. Memoised recursion that pulls from incoming edges is the same computation in DFS order. Conversely, every DP can be drawn as a DAG whose answer is a shortest, longest or counted path, a view the advanced DP module develops.

### Counting shortest routes

With positive weights, the **tight** edges, where `dist[u] + w == dist[v]` after Dijkstra, form a DAG that contains exactly the shortest routes, and Dijkstra's pop order is a topological order of it (a tight predecessor has a strictly smaller distance, so it pops earlier). So you can count inside Dijkstra: when relaxing u -> v, a strictly better distance sets `ways[v] = ways[u]`, an equal one adds `ways[u]`. With zero-weight edges that order argument fails; build the tight-edge DAG and sort it topologically instead.

## Cost

Kahn's algorithm touches each vertex and edge once, and so does the relaxation pass: **O(V + E) time, O(V + E) space**. Compare O((V + E) log V) for Dijkstra and O(V·E) for Bellman-Ford, which is what you would otherwise need with negative edges. Counting or longest paths cost the same; counting shortest routes inside Dijkstra adds nothing to Dijkstra's bound.

## When to use it

Cues: prerequisites, deadlines and task durations; events ordered in time; moves that only go right or down, or to a larger index; "the maximum total along a chain"; "how many routes". If the graph might contain a cycle, Kahn's algorithm tells you: fewer than V vertices come out. Then fall back to Dijkstra (non-negative weights) or Bellman-Ford.

## Worked trace

Edges: S->A 5, S->B 3, B->A -4, A->C 6, A->D 2, B->D 7, D->C -1, C->T 1, D->T 4. Kahn's algorithm gives the order S, B, A, D, C, T.

```text
          5            6            1
   S ----------> A ----------> C ----------> T
   |             ^ \           ^             ^
   | 3        -4 |  \ 2        | -1          | 4
   v             |   v         |             |
   B ------------+   D --------+-------------+
   |                 ^
   +------- 7 -------+
```

```steps
Order S B A D C T; only the source is known
    order  S    B    A    D    C    T
    dist   0  inf  inf  inf  inf  inf
---
Relax out of S: A = 5, B = 3
    order  S    B    A    D    C    T
    dist   0  {{3}}  {{5}}  inf  inf  inf
---
Relax out of B (final at 3): B->A gives 3 - 4 = -1 < 5; B->D gives 10. A's value can still change because A comes later in the order
    order  S    B    A    D    C    T
    dist   0    3  {{-1}}  {{10}}  inf  inf
---
Relax out of A (final at -1): A->C gives 5, A->D gives 1 < 10
    order  S    B    A    D    C    T
    dist   0    3   -1  {{1}}  {{5}}  inf
---
Relax out of D (final at 1): D->C gives 0 < 5, D->T gives 5
    order  S    B    A    D    C    T
    dist   0    3   -1    1  {{0}}  {{5}}
---
Relax out of C (final at 0): C->T gives 1 < 5. T has no edges. Done: the route is S B A D C T, cost 1
    order  S    B    A    D    C    T
    dist   0    3   -1    1    0  {{1}}
```

## Template

```python
from collections import deque


def dag_shortest(n, edges, src):
    """Shortest distances in a DAG (any weights) by relaxing in topological order."""
    graph = [[] for _ in range(n)]
    indeg = [0] * n
    for u, v, w in edges:
        graph[u].append((v, w))
        indeg[v] += 1
    order = []
    ready = deque(v for v in range(n) if indeg[v] == 0)
    while ready:                         # Kahn's algorithm
        u = ready.popleft()
        order.append(u)
        for v, _ in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                ready.append(v)
    if len(order) < n:
        raise ValueError("the graph has a cycle")
    dist = [float("inf")] * n
    dist[src] = 0
    for u in order:                      # every edge into u is already relaxed
        if dist[u] == float("inf"):
            continue
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist
```

For longest paths, start from `-inf` and keep the larger value; for route counts, start `ways[src] = 1` and add `ways[u]` into each successor.

## Pitfalls

- **A cycle you did not expect.** Without the length check, vertices on or behind a cycle never enter the order and silently keep infinity.
- **Longest paths initialised to 0** instead of minus infinity, which lets routes start anywhere instead of at the source.
- **Counting inside Dijkstra with zero-weight edges.** A tight predecessor can pop after its successor, so counts are missed.
- **Big counts.** Problems ask for counts modulo 10^9 + 7; reduce as you add (Python will not overflow, but huge integers are slow, and other languages overflow).
- **Deep recursion.** A memoised DFS over 10^5 vertices exceeds Python's default recursion limit of 1000; Kahn's loop has no such limit.

## Check yourself

Q: What is the *longest* S -> T route in the trace DAG, and its cost?
A: S B D T, costing 3 + 7 + 4 = 14. The relaxation pass with max gives S 0, B 3, A 5, D 10, C 11, T 14; the alternatives through C are at most 12.

Q: Why does the negative edge B -> A not break this algorithm, when the same kind of edge breaks Dijkstra?
A: Dijkstra decides that a vertex is final by its distance, assuming nothing cheaper can arrive later; a negative edge breaks that assumption. Here a vertex is final when all its incoming edges have been relaxed, which the topological order guarantees regardless of weights. A was not processed until B, its predecessor, was done.

Q: Courses have durations and prerequisites, and any number can run in parallel. How do you find the shortest possible time to finish them all?
A: Treat courses as vertices and prerequisites as edges. In topological order, `finish[v] = duration[v] + max(finish[u] for u in prerequisites of v)` (0 if none). The answer is the largest finish time: the longest path, with weights on the vertices. O(V + E).

## Lab

- **1976 Number of Ways to Arrive at Destination.** Dijkstra from 0 that also keeps `ways`: a strictly better distance copies the count, an equal one adds it, modulo 10^9 + 7 (all times are positive, so pop order is a topological order of the tight edges). Expected: O(E log V); with `n = 5, roads = [[0,1,1],[0,2,1],[1,3,1],[2,3,1],[3,4,2],[0,4,4],[1,2,1]]` the answer is 3 (0 1 3 4, 0 2 3 4 and the direct road, each costing 4).
- **Exercise: count all routes.** Count every S -> T route in the trace DAG with `ways` in topological order. Expected: 8.

> [!know]
> You now know how to relax a DAG in topological order for shortest, longest and counted routes, and why that is dynamic programming.

=== primer | Which shortest-path algorithm should you choose, and how does A* use a heuristic without losing optimality? | 16 min
goal: Choose a shortest-path algorithm from the weights, the graph and the query pattern, and run A* with an admissible heuristic, explaining why the first popped target is optimal
tag: paths-astar | Choosing an algorithm, and A*
link: Red Blob Games: Introduction to A* | https://www.redblobgames.com/pathfinding/a-star/introduction.html#astar | 15 min, interactive: 'Dijkstra's Algorithm', 'Greedy Best First Search' and 'A* Algorithm', watching the heuristic pull the frontier towards the goal
link: Wikipedia: A* search algorithm | https://en.wikipedia.org/wiki/A*_search_algorithm#Admissibility | 5 min: 'Admissibility', then 'Optimality and consistency' for why consistent heuristics never reopen a vertex
practice: 2203

> [!key]
> Choose by the **weights** first (equal: BFS; 0/1: deque; DAG: topological order; non-negative: Dijkstra; negative: Bellman-Ford), then by the **query** (one source, one pair, all pairs, millions of repeated queries). For one source and one target, the A* search orders the heap by f = g + h: the cost so far plus an estimate of the cost still to go. If h never overestimates (**admissible**), the first time the target is popped its cost is optimal; if also h(u) <= w(u, v) + h(v) (**consistent**), A* is exactly Dijkstra on reweighted edges and never reopens a vertex.

## Intuition

Dijkstra grows a circle around the source. It settles vertices directly behind you as eagerly as vertices towards the goal, because it has no idea where the goal is. A* is Dijkstra with a compass: among the frontier vertices it prefers the one whose "distance so far plus straight-line distance left" is smallest, so the explored region stretches into an ellipse towards the target. The compass must be optimistic, never claiming the goal is further away than it really is: as the crow flies on roads, Manhattan distance on a grid with four moves.

## How it works

### The decision table

| Weights or structure | Query | Algorithm | Cost |
|---|---|---|---|
| all equal | one source | BFS | O(V + E) |
| only 0 and 1 | one source | 0-1 BFS | O(V + E) |
| DAG, any weights | one source | relax in topological order | O(V + E) |
| non-negative | one source | Dijkstra | O((V + E) log V) |
| non-negative, with geometry | one pair | A* or bidirectional Dijkstra | at most Dijkstra's work, usually far less |
| some negative, no negative cycle | one source | Bellman-Ford | O(V·E) |
| at most k edges | one source | k rounds of Bellman-Ford | O(k·E) |
| any, n up to about 400 | all pairs | Floyd-Warshall | O(n³) |
| non-negative, sparse | all pairs | Dijkstra from every vertex | O(V (V + E) log V) |
| huge static road network | millions of pairs | preprocessing (contraction hierarchies) | milliseconds per query |

Two tricks extend every row. Distances *to* one target from everywhere are distances *from* it in the reversed graph. Distances from the nearest of several sources come from pushing every source at distance 0.

### A* and admissibility

Keep g (the best cost found so far) per vertex, push `(g + h(v), g, v)`, pop the smallest f, and **stop when the target is popped**. With h = 0 this is Dijkstra.

Why the first popped target is optimal when h is admissible (h(v) <= true distance from v to t, so h(t) = 0): let C* be the optimal cost and take an optimal route s = v0, ..., vk = t. Until t is popped with cost C*, look at the first vertex vi on that route that has not been expanded with its optimal g. Its predecessor has been, so vi sits in the heap with g = its optimal cost and key f = g + h(vi) <= g + (true rest of the route) = C*. A wrong entry for t has key g(t) + 0 > C*. The heap pops smaller keys first, so a wrong entry for t can never come out before the right one.

**Consistency** is stronger: h(u) <= w(u, v) + h(v) for every edge, the triangle inequality. Then the reweighted edges `w(u, v) - h(u) + h(v)` are non-negative and every s -> t route shifts by the same constant, so A* is Dijkstra on that graph: each vertex is final when first popped. Manhattan distance on a 4-way grid is consistent.

**Overestimating** (weighted A*, f = g + 2h) explores far less and returns routes up to twice the optimum: a deliberate trade in games and robotics, never an accident to make in an interview.

Heuristics that work: Manhattan distance times the cheapest step on 4-way grids; the octile distance on 8-way grids; straight-line distance divided by the top speed for travel times; and landmark bounds (ALT), which use precomputed distances to a few landmarks and the triangle inequality.

## Cost

The worst case is Dijkstra's O((V + E) log V) (h = 0 is allowed), plus the cost of evaluating h on every push. The gain depends entirely on how tight h is. On a 200 × 200 grid with 20% walls, start and target 100 cells apart (the lab's setup): with every step costing 1, Dijkstra settled 19,229 cells and A* with Manhattan distance 1,418. With terrain costing 1, 3 or 5 per step, Manhattan distance underestimates by a factor of two or more; Dijkstra settled 19,606 cells and A* 6,463. From corner to corner on that terrain, A* saved almost nothing, because nearly every cell lies inside the ellipse.

## When to use it

A* fits one source and one target on a big graph with a natural, cheap lower bound: maps, grids, puzzles. Skip it when you need distances to every vertex (it is just Dijkstra then), when no meaningful lower bound exists (abstract graphs), or when the same graph serves millions of queries, where preprocessing pays off (the real-systems card).

## Worked trace

Undirected edges S-E 1, E-F 1, S-A 2, S-B 3, A-C 3, B-C 2, C-T 2, A-T 5. Heuristic h: S 6, E 7, F 8, A 4, B 4, C 2, T 0 (the true distances to T are 7, 8, 9, 5, 4, 2, 0, so h is admissible, and it is consistent). Heap entries are (f, g, vertex).

```text
   F --1-- E --1-- S --2-- A --5-- T
                   |       |       |
                   3       3       2
                   |       |       |
                   B --2-- C ------+
```

```steps
Start with the source: f = 0 + h(S) = 6. (Dijkstra, with h = 0, would pop S, E, F, A, B, C and T: seven pops, two of them behind the start)
    heap   (6,0,S)
---
Pop S. Push A (g 2, f 2+4 = 6), B (g 3, f 3+4 = 7) and E (g 1, f 1+7 = 8): E is close but points away from T
    heap   {{(6,2,A)}} (7,3,B) (8,1,E)
---
Pop A (f 6). Push C (g 5, f 5+2 = 7) and T (g 7, f 7+0 = 7)
    heap   (7,3,B) {{(7,5,C)}} {{(7,7,T)}} (8,1,E)
---
Pop B (f 7). B-C would give g 5, not better than 5: no push
    heap   (7,5,C) (7,7,T) (8,1,E)
---
Pop C (f 7). C-T would give g 7, not better than 7: no push
    heap   (7,7,T) (8,1,E)
---
Pop T: the target, with g = 7, the optimal cost. Five pops; E was never expanded and F never even reached
    heap   (8,1,E)
    answer {{7}}
```

## Template

```python
import heapq


def astar(graph, src, dst, h):
    """Cost of a shortest src -> dst path, or inf.
    h(v) must never overestimate the true distance from v to dst (admissible)."""
    g = {src: 0}
    heap = [(h(src), 0, src)]
    while heap:
        f, cost, u = heapq.heappop(heap)
        if u == dst:                     # stop when the target is popped, not pushed
            return cost
        if cost > g[u]:
            continue
        for v, w in graph[u]:
            if cost + w < g.get(v, float("inf")):
                g[v] = cost + w
                heapq.heappush(heap, (cost + w + h(v), cost + w, v))
    return float("inf")
```

The stale check lets a vertex be reopened if a cheaper g turns up later, which keeps the template correct even for heuristics that are admissible but not consistent. Keep a parent dictionary next to `g` to recover the route.

## Pitfalls

- **Stopping when the target is pushed.** A later pop can still offer a cheaper route; only the pop is safe.
- **An overestimating heuristic**, for example Manhattan distance on a grid where diagonal moves are allowed, or distance in metres when the weights are minutes. The search gets faster and the answers get wrong.
- **A closed set with an inconsistent heuristic.** Refusing to reopen vertices can return a suboptimal route; either reopen (as the template does) or make h consistent.
- **Ties.** Many vertices share the same f on grids; preferring the larger g (or smaller h) among equals cuts the work noticeably.
- **Expensive heuristics.** h runs on every push; precompute what you can.

## Check yourself

Q: In the trace, which vertices would plain Dijkstra pop before reaching T, and how many pops does A* save?
A: Dijkstra pops by distance: S 0, E 1, then A and F at 2, B 3, C 5, T 7, so seven pops including E and F, which lead away from T. A* pops S, A, B, C, T: five, and never expands E or F.

Q: Why does A* with an admissible heuristic never return a route that is too expensive?
A: Before the optimal entry for t is popped, some vertex of an optimal route sits in the heap with its optimal g, and its key g + h is at most the optimal cost C*, because h underestimates the rest of the route. Any wrong entry for t has key g(t) > C* (h(t) = 0). The heap therefore always pops something else before a wrong target entry.

Q: For each case, name the algorithm: (a) a 1000 × 1000 maze, every step costs 1, distances from one cell to all; (b) 300 warehouses, all pairwise travel times; (c) a city of 10^5 junctions, distance from every junction to the one hospital along one-way streets.
A: (a) BFS, O(cells). (b) Floyd-Warshall, 2.7·10^7 steps, or Dijkstra from each; Floyd is simplest at n = 300. (c) One Dijkstra from the hospital on the reversed graph, since "distance to the hospital" along one-way streets is "distance from the hospital" with every street reversed.

## Lab

- **2203 Minimum Weighted Subgraph With the Required Paths** (stretch). The two routes merge at some vertex and share the rest: run Dijkstra from src1, from src2, and from dest on the reversed graph, and take the minimum of the three distances summed at each vertex. Expected: O(E log V); with `n = 5, edges = [[0,2,4],[1,2,1],[2,4,3],[0,3,1],[3,4,5],[1,3,2]], src1 = 0, src2 = 1, dest = 4` the answer is 8, and with `n = 4, edges = [[0,3,2],[1,2,1]], src1 = 0, src2 = 1, dest = 3` it is -1.
- **Exercise: count pops.** Run the template on the trace graph, counting pops. Expected: cost 7 after 5 pops with h as given, and 7 pops with h = 0.

> [!know]
> You now know how to choose a shortest-path algorithm from the weights and the query, and how to use A* with an admissible heuristic safely.

=== lab | Route planner on a grid: BFS vs Dijkstra vs A* | 50 min
goal: Build one grid planner with three search strategies, verify it against Bellman-Ford, and measure when A* pays off and when it does not

You will plan routes across generated terrain with BFS, Dijkstra and A*, check correctness with a brute-force oracle, then let measurements show what the heuristic buys. Reuse the stress-test loop and timer from your `dsakit` if you built it in the correctness module. This stage's project takes the same ideas to real road data.

## Setup

```python
import heapq
import random
from collections import deque

COST = {".": 1, ",": 3, "^": 5}          # road, grass, forest; "#" is a wall


def make_grid(rows, cols, walls=0.2, seed=0):
    rnd = random.Random(seed)
    grid = []
    for _ in range(rows):
        row = []
        for _ in range(cols):
            x = rnd.random()
            row.append("#" if x < walls else "." if x < 0.55 else "," if x < 0.8 else "^")
        grid.append(row)
    return grid


def neighbours(grid, cell):
    """Yield (next_cell, cost of entering it) for the four moves."""
    r, c = cell
    for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
            yield (nr, nc), COST[grid[nr][nc]]
```

## Steps

1. Generate a 200 × 200 grid, put the start at row 100, column 50 and the target at row 100, column 150, force both cells to `"."`, and regenerate with a new seed until BFS can reach the target.
2. Write `bfs(grid, s, t)` that ignores costs, then measures the real cost of the route it found. Return `(cost, settled)`, where settled counts cells taken off the queue.
3. Write `dijkstra(grid, s, t)` from the template, stopping when t is popped; count settled cells as non-stale pops.
4. Write `astar(grid, s, t, weight=1.0)` with `h = weight * (abs(r - tr) + abs(c - tc))`. The cheapest step costs 1, so with weight 1 this never overestimates. Break ties on equal f in favour of the smaller h.
5. Verify before you measure. Run 1,000 random graphs (up to 8 vertices, up to 20 edges, weights 0 to 9) through your graph Dijkstra and a Bellman-Ford oracle and assert equal distance lists; then assert that A* and Dijkstra return the same cost on 200 random small grids.
6. Measure cost, settled cells and milliseconds for BFS, Dijkstra, A* and A* with weight 2 in three scenarios: uniform terrain (replace every non-wall with `"."`), mixed terrain, and mixed terrain from corner to corner.
7. Print the grid with settled cells marked and the route drawn, once for Dijkstra and once for A*, and look at the shapes.
8. Write three sentences: when A* helped, when it did not, and why weighted A* is faster but not exact.

## What you should see

Reference numbers from one run with seed 0 (other seeds and your own code will differ, the pattern should not):

| Scenario | BFS cost | Dijkstra settled | A* settled | A* (weight 2) settled and cost |
|---|---|---|---|---|
| uniform, 100 apart | 126 (optimal) | 19,229 | 1,418 | 250, cost 130 |
| mixed terrain, 100 apart | 334 (optimal is 240) | 19,606 | 6,463 | 1,672, cost 242 |
| mixed, corner to corner | 1,030 (optimal 666) | 31,922 | 31,553 | 1,038, cost 708 |

- BFS finds the fewest steps, which is optimal on uniform terrain and 40 to 55% too expensive on mixed terrain.
- Dijkstra settles a disc around the start: almost every open cell within the target's distance. A* settles an ellipse towards the target: 13 to 20 times fewer cells on uniform terrain (across seeds), but only about 3 times fewer on mixed terrain, because Manhattan distance assumes every step costs 1 while the average step costs more than 2. Corner to corner, the ellipse covers nearly the whole grid and A* saves nothing.
- Weighted A* is dramatically faster and a few percent worse: it is no longer admissible.
- Dijkstra and Bellman-Ford agree on all 1,000 graphs. If they do not, check the stale-entry test and that you stop at the pop, not the push.
- In CPython, Dijkstra on about 30,000 open cells takes a few hundred milliseconds; A* on uniform terrain takes a few tens of milliseconds at most.

> [!note]
> The lesson for production: a heuristic is only as good as its tightness. Road routers either use better lower bounds (landmarks) or preprocess the graph, as the real-systems card explains.

=== primer | What else can graph search reveal: Euler paths, bridges and strongly connected components? (optional) | 15 min
goal: Build an Euler path with Hierholzer's algorithm, find bridges with low-link values, and outline how strongly connected components are found
tag: paths-structure | Euler paths, bridges and SCCs
link: cp-algorithms: Finding bridges | https://cp-algorithms.com/graph/bridge-searching.html#algorithm | 10 min: 'Algorithm', the entry time and low-link values and the bridge condition low[to] > tin[v], and how the parent edge is skipped
link: cp-algorithms: Eulerian path | https://cp-algorithms.com/graph/euler_path.html#algorithm | 10 min: 'Algorithm', the degree conditions and the stack-based construction
practice: 1192

> [!key]
> Three DFS-based structures answer questions that distances cannot. An **Euler path** uses every edge exactly once; it exists when the degrees allow it and the edges are connected, and **Hierholzer's algorithm** builds it in O(E) by walking until stuck and splicing in detours. A **bridge** is an edge whose removal disconnects the graph; one DFS with **low-link** values finds them all in O(V + E). **Strongly connected components** group vertices that can reach each other in a directed graph; Kosaraju's two DFS passes find them in O(V + E), and shrinking each to one vertex leaves a DAG.

## Intuition

Drawing a figure without lifting the pen, or a snow plough that must clear every street once, is an Euler path. A single road joining two halves of a town, or the one cable between two data centres, is a bridge: a single point of failure. In a city of one-way streets, a district where you can drive from anywhere to anywhere and back is a strongly connected component; between districts traffic can flow only one way.

## How it works

### Euler paths with Hierholzer's algorithm

Conditions. Undirected: zero or two vertices of odd degree (start at an odd one if there are two). Directed: every vertex has in-degree equal to out-degree, except possibly a start with one extra outgoing edge and an end with one extra incoming edge. In both cases every edge must lie in one connected piece.

Algorithm: keep a stack, starting with the start vertex. If the top has an unused edge, take it and push its other end; if not, pop the top onto the answer. Reverse the answer at the end. A walk can only get stuck at the path's end (every other vertex has as many ways out as in), so each pop finalises the next vertex from the back, and the vertices still on the stack are where unused detours get spliced in. Each edge is pushed and popped once: O(E). For the lexicographically smallest itinerary, sort each adjacency list in reverse and pop from its end.

### Bridges with low-link values

Run DFS and record `disc[v]`, the time v was discovered. Let `low[v]` be the smallest discovery time reachable from v's DFS subtree using tree edges downwards plus **one** back edge. When v finishes, its parent p takes `low[p] = min(low[p], low[v])`. The tree edge p - v is a **bridge** exactly when `low[v] > disc[p]`: nothing below v can climb back to p or above without that edge. With `>=` and a non-root p, the same test finds **articulation points** (vertices whose removal disconnects); the DFS root is one if it has two or more DFS children. Skip the edge you arrived on by its id, not by the parent vertex, so that parallel edges count as a cycle.

### Strongly connected components, in outline

Kosaraju: run DFS on the graph and list vertices by finishing time. Then run DFS on the **reversed** graph, starting from vertices in decreasing finishing time; each search tree is one component. The vertex that finishes last lies in a component with no incoming edges from other components, and in the reversed graph it can reach only its own component, so the first search collects exactly that component, and so on. Tarjan's algorithm does it in one DFS with low-links and a stack. Shrinking each component gives the **condensation**, a DAG, on which the previous card's DAG techniques apply (and 2-SAT reduces to it).

## Cost

All three are linear: **O(V + E) time and space**. In Python write them iteratively (as below): recursive DFS on a path of 10^5 vertices exceeds the default recursion limit of 1000, and raising the limit risks crashing the interpreter's C stack.

## When to use it

- "Use every ticket, edge or domino exactly once", "a string containing every combination": Euler path or circuit (a de Bruijn sequence is an Euler circuit).
- "Critical connections", "single points of failure", "which roads, if closed, cut the town in two": bridges and articulation points.
- "Mutually reachable", "groups in a directed graph", "the fewest edges to make everything reachable": strongly connected components, then reason on the DAG.
- Not for anything about distances: these structures ignore weights.

## Worked trace

Bridges in this graph: triangle 0 1 2, edge 2 - 3, triangle 3 4 5, edge 5 - 6.

```text
  0 ----- 1            4
   \     /           /   \
    \   /           /     \
      2 ---------- 3 ----- 5 ----- 6
```

```steps
DFS from 0 discovers 1 (time 1) and 2 (time 2). At 2, the edge 2 - 0 goes back to an ancestor, so low[2] = disc[0] = 0
    disc   0  1  2  -  -  -  -
    low    0  1  {{0}}  -  -  -  -
---
From 2, discover 3 (time 3), 4 (time 4), 5 (time 5). At 5, the edge 5 - 3 is a back edge: low[5] = 3
    disc   0  1  2  3  4  5  -
    low    0  1  0  3  4  {{3}}  -
---
From 5, discover 6 (time 6). 6 has no other edges and finishes: low[6] = 6 > disc[5] = 5, so 5 - 6 is a **bridge**
    disc   0  1  2  3  4  5  6
    low    0  1  0  3  4  3  {{6}}
---
5 finishes: low[5] = 3 is not > disc[4] = 4, no bridge; 4 inherits low 3. 4 finishes: 3 is not > disc[3] = 3, no bridge
    disc   0  1  2  3  4  5  6
    low    0  1  0  3  {{3}}  3  6
---
3 finishes: low[3] = 3 > disc[2] = 2, so 2 - 3 is a **bridge**: nothing beyond 3 climbs back above it
    disc   0  1  2  3  4  5  6
    low    0  1  0  {{3}}  3  3  6
---
2 finishes with low 0, so 1 inherits 0; then 1 and 0 finish with no more bridges. Answer: 5 - 6 and 2 - 3
    disc   0  1  2  3  4  5  6
    low    0  {{0}}  0  3  3  3  6
```

## Template

```python
from collections import defaultdict


def find_bridges(n, edges):
    """Bridges of an undirected multigraph given as (u, v) pairs, by DFS low-links (iterative)."""
    graph = [[] for _ in range(n)]
    for i, (u, v) in enumerate(edges):
        graph[u].append((v, i))
        graph[v].append((u, i))
    disc = [-1] * n                      # discovery time
    low = [0] * n                        # earliest discovery time reachable via one back edge
    bridges, timer = [], 0
    for root in range(n):
        if disc[root] != -1:
            continue
        disc[root] = low[root] = timer
        timer += 1
        stack = [(root, -1, iter(graph[root]))]
        while stack:
            u, via, it = stack[-1]
            for v, i in it:
                if i == via:             # do not reuse the edge we came in on
                    continue
                if disc[v] == -1:        # tree edge: descend
                    disc[v] = low[v] = timer
                    timer += 1
                    stack.append((v, i, iter(graph[v])))
                    break
                low[u] = min(low[u], disc[v])   # back edge
            else:                        # u is finished
                stack.pop()
                if stack:
                    p = stack[-1][0]
                    low[p] = min(low[p], low[u])
                    if low[u] > disc[p]:
                        bridges.append(edges[via])
    return bridges


def euler_path(edges, start):
    """Hierholzer: a path using every directed edge once, assuming one exists from start."""
    out = defaultdict(list)
    for u, v in edges:
        out[u].append(v)
    stack, path = [start], []
    while stack:
        u = stack[-1]
        if out[u]:
            stack.append(out[u].pop())   # follow an unused edge
        else:
            path.append(stack.pop())     # dead end: u is next from the back
    return path[::-1]
```

The `for ... else` runs the `else` part only when the adjacency iterator is exhausted, that is, when u has no undiscovered neighbours left.

## Pitfalls

- **Recursion depth** in Python: use explicit stacks for graphs of more than a few thousand vertices.
- **Skipping the parent vertex instead of the parent edge** reports false bridges: two parallel edges between p and v are never a bridge, but skipping every edge back to p hides the second one.
- **Euler conditions unchecked.** Hierholzer assumes a path exists; check the degrees and that all edges are connected, and choose the right start vertex.
- **Undirected Euler paths** must mark each edge used by its id, because it appears in two adjacency lists.
- **Kosaraju's second pass on the original graph** instead of the reversed one merges components that are only one-way connected.

## Check yourself

Q: Add the edge 1 - 3 to the trace graph. Which edges are bridges now?
A: Only 5 - 6. The new edge closes the cycle 1 2 3 1, so when 3 finishes its low value is 1 (through the back edge to 1), which is not greater than disc[2] = 2, and 2 - 3 stops being a bridge.

Q: Why is the bridge test `low[v] > disc[p]` strict, while the articulation point test uses `>=`?
A: If low[v] equals disc[p], something below v has a back edge to p itself. Then the edge p - v is not needed (there is another way back to p), so it is not a bridge, but removing the vertex p still cuts v's subtree off from everything above p, so p is an articulation point.

Q: Plane tickets are directed edges between airports, and you must use every ticket once starting from a given airport. Which algorithm, and how do you get the alphabetically smallest itinerary?
A: A directed Euler path with Hierholzer's algorithm from the given start. Sort each airport's destinations in reverse and pop from the end so the smallest unused destination is always taken first; the reversed finishing order is then the smallest valid itinerary.

## Lab

- **1192 Critical Connections in a Network** (stretch). Bridges by low-link, written iteratively. Expected: O(V + E); with `n = 6, connections = [[0,1],[1,2],[2,0],[1,3],[3,4],[4,5],[5,3]]` the answer is `[[1,3]]`.
- **Exercise: Hierholzer.** `euler_path([(0,1),(1,2),(2,0),(0,3),(3,0)], 0)` must use all five edges. Expected with the template: `[0, 3, 0, 1, 2, 0]`.

> [!know]
> You now know how to build Euler paths with Hierholzer's algorithm, find bridges with low-link values, and outline strongly connected components.

=== primer | How do routers and map services compute shortest paths at scale? | 14 min
goal: Explain how link-state routing runs Dijkstra, how distance-vector routing is a distributed Bellman-Ford, and how contraction hierarchies make road queries fast
tag: paths-systems | Shortest paths in production
link: RFC 2328, OSPF version 2, section 16 | https://www.rfc-editor.org/rfc/rfc2328#section-16 | 15 min: the opening of section 16 and 16.1 'Calculating the shortest-path tree for an area' (Dijkstra over the link-state database); skim 16.1.1 on next hops
link: Wikipedia: Contraction hierarchies | https://en.wikipedia.org/wiki/Contraction_hierarchies#Preprocessing_phase | 10 min: 'Preprocessing phase' (contraction and witness search), then 'Query phase' (the upward bidirectional search)

> [!key]
> Production systems run this module's algorithms with engineering around them. **Link-state** routing (OSPF, IS-IS) gives every router the whole topology; each runs Dijkstra from itself and keeps only the **first hop** of every route. **Distance-vector** routing (RIP) is Bellman-Ford spread across routers, exchanging distance tables with neighbours, with a small "infinity" to stop slow bad news. Road routers cannot run Dijkstra over a continent for every query, so they **preprocess**: contraction hierarchies add shortcut edges once, and each query becomes a tiny search.

## Intuition

Two ways to find your way round a city. Buy the full map, then plan every route yourself: that is link state, costly to keep current but fast to react, because when a road closes you only need the news and your own replanning. Or ask your neighbours how far they are from everywhere and trust the best answer plus the walk to them: that is distance vector, cheap and simple, but when a road closes the bad news spreads one conversation at a time.

For road maps the problem is volume: a continental road graph has tens of millions of junctions, and a routing service answers huge numbers of queries. Precomputing "motorway" shortcuts once means each query skips the side streets in the middle of the route.

## How it works

### Link state: OSPF and IS-IS

Each router floods a small advertisement listing its links and their costs. Every router assembles the same **link-state database**, a weighted directed graph, and runs Dijkstra rooted at itself (RFC 2328 calls it the shortest-path tree calculation). The router does not need full routes, only where to send each packet next: the **next hop** for a destination is the first vertex on its tree path. When a link changes, a new advertisement is flooded and every router reruns the calculation (implementations throttle reruns during bursts of changes). Keeping every tight first hop instead of one gives equal-cost multipath.

### Distance vector: RIP

Each router keeps a table of its best known distance to every destination and periodically sends it to its neighbours. On receiving a neighbour's table it relaxes: `dist[d] = min(dist[d], link_cost + neighbour_dist[d])`. That is Bellman-Ford, run asynchronously by many machines. Good news spreads fast; bad news does not: when a link fails, two routers can keep quoting each other's stale distance, raising it one step per exchange (**counting to infinity**). RIP limits the damage by defining a metric of 16 as unreachable (RFC 2453), which also limits a RIP network to 15 hops.

### Road networks: contraction hierarchies

Order the vertices by importance (cul-de-sacs low, motorway junctions high) and **contract** them from least to most important. Contracting v removes it, and for each pair of its remaining neighbours u, w adds a **shortcut** u - w with weight w(u, v) + w(v, w), but only if no **witness** route from u to w that avoids v is as short (found by a small, bounded Dijkstra). A query then runs Dijkstra from both ends, each side only moving to more important vertices; the two searches meet near the top of the hierarchy, and shortcuts are unpacked into real roads at the end. OSRM, the open-source router for OpenStreetMap data, offers this pipeline and a second one, multi-level Dijkstra (MLD), which partitions the map into cells; its documentation recommends MLD by default because it can absorb weight changes such as live traffic quickly, and CH where raw query speed matters most, especially for large distance matrices ([OSRM wiki: how to run the tool chain](https://github.com/Project-OSRM/osrm-backend/wiki/Running-OSRM#how-to-run-the-tool-chain)).

## Cost

- **OSPF:** one Dijkstra per change, O((V + E) log V) with V routers in an area, typically hundreds to a few thousand vertices: milliseconds.
- **RIP:** after a change, distances settle in about as many exchange rounds as the network's diameter, but counting to infinity can take up to 16 rounds per bad route, and each round is a timer period, so convergence can take minutes.
- **Contraction hierarchies:** preprocessing takes seconds to hours, depending on the graph; queries then touch a small fraction of the graph, which turns milliseconds-to-seconds Dijkstra queries into microseconds-to-milliseconds ones. The price is extra memory for shortcuts and recontraction (or MLD's customisation step) when weights change.

## When to use it

| Need | Approach |
|---|---|
| Routers that must react fast and can store the topology | link state (Dijkstra per change) |
| Small, simple networks; minimal state per router | distance vector (distributed Bellman-Ford) |
| A mostly static graph with very many queries | preprocessing: contraction hierarchies, landmarks (ALT) |
| Weights that change often (traffic) | partition-based schemes such as MLD, or A* with live weights |
| One-off queries on a modest graph | plain Dijkstra or A*; preprocessing would not pay for itself |

## Worked trace

Contract a small road graph: A-B 1, B-C 1, C-D 1, D-A 1, A-C 3, C-E 4, in the order B, E, D (A and C are the most important).

```text
    A ---1--- B
    | \       |
    1   3     1
    |     \   |
    D ---1--- C ---4--- E
```

```steps
Contract B. Its neighbours A and C would need a shortcut of 1 + 1 = 2. Witness search from A to C avoiding B finds A D C, also 2, so no shortcut is needed
    removed  B
    edges    A-D 1, D-C 1, A-C 3, C-E 4
    added    (none: witness A D C = 2)
---
Contract E. It has only one neighbour, C, so there is no pair to connect
    removed  B, E
    edges    A-D 1, D-C 1, A-C 3
    added    (none)
---
Contract D. A and C would need 1 + 1 = 2. The best route avoiding D is the direct edge, 3 > 2, so add the **shortcut** A-C 2
    removed  B, E, D
    edges    {{A-C 2}}  (replaces A-C 3)
    added    A-C 2 = A-D-C
---
Query B to E. Each search moves only to vertices contracted later. From B: A at 1, C at 1. From E: C at 4. They meet at C: 1 + 4 = 5, the true distance B C E
    forward  B: A=1, C={{1}}
    backward E: C={{4}}
    answer   {{5}}
```

## Template

```python
import heapq


def next_hops(graph, src):
    """Routing table: for each destination, the neighbour of src to forward to."""
    dist, parent = dijkstra(graph, src)
    hop = [-1] * len(graph)
    for t in range(len(graph)):
        if t == src or dist[t] == float("inf"):
            continue
        v = t
        while parent[v] != src:
            v = parent[v]
        hop[t] = v
    return hop


def contract(adj, v):
    """Remove v from an undirected weighted graph adj[u] = {x: w}, adding a shortcut
    between two neighbours only when no path avoiding v (a witness) is as short."""
    nbrs = adj.pop(v)
    for u in nbrs:
        del adj[u][v]
    added = []
    for u, wu in nbrs.items():
        for x, wx in nbrs.items():
            if u >= x:
                continue
            via = wu + wx
            if witness_distance(adj, u, x, via) > via:
                adj[u][x] = adj[x][u] = via
                added.append((u, x, via))
    return added


def witness_distance(adj, s, t, limit):
    """Dijkstra from s in adj, giving up beyond limit; returns dist(s, t) or inf."""
    dist = {s: 0}
    heap = [(0, s)]
    while heap:
        d, u = heapq.heappop(heap)
        if u == t:
            return d
        if d > dist[u] or d > limit:
            continue
        for x, w in adj[u].items():
            if d + w < dist.get(x, float("inf")):
                dist[x] = d + w
                heapq.heappush(heap, (d + w, x))
    return float("inf")
```

`next_hops` reuses `dijkstra` from the first card. The walk back from each destination costs up to O(V) per vertex; a production version assigns hops top-down along the tree in one pass. Real contraction also bounds the witness search by a hop or settle limit, adding a few unnecessary shortcuts in exchange for much faster preprocessing.

## Pitfalls

- **Stopping a bidirectional search when the two searches first meet.** The meeting vertex need not be on the best route; stop when the two heap minimums together reach the best total seen so far.
- **Admissible heuristics in the wrong units.** Straight-line distance must be divided by the top speed when weights are travel times, which makes the bound loose wherever there are motorways.
- **Forgetting that preprocessing freezes weights.** Contraction hierarchies must be rebuilt (or customised, in MLD) when costs change.
- **Distance-vector loops.** Without a finite infinity, split horizon or similar safeguards, a failed link can keep routers incrementing distances indefinitely.

## Check yourself

Q: In the trace, suppose D-A weighed 2 instead of 1. Does contracting B now need a shortcut, and what happens when D is contracted?
A: Yes. Through B, A to C costs 2, and the best witness avoiding B is A D C = 3 (the direct edge is also 3), so the shortcut A-C 2 is added. When D is contracted later, A to C through D costs 2 + 1 = 3, and the shortcut already gives 2, so no new shortcut is needed.

Q: Why does RIP define 16 as infinity, and what does that cost?
A: After a link fails, routers can keep advertising stale routes to each other, each raising its distance by one per exchange; with a true infinity this could go on for ever. Capping the metric at 16 guarantees the count stops after a bounded number of exchanges and the route is declared unreachable. The cost is that a RIP network cannot have routes longer than 15 hops.

Q: A delivery company replans its fleet every few minutes on a city graph whose travel times change with traffic. Would you pick contraction hierarchies?
A: Not plain CH: every weight change would force expensive recontraction. A partition-based scheme with fast customisation (as MLD offers), or A*/Dijkstra on the live graph if the city is small enough, fits frequently changing weights better.

## Lab

- **Exercise: a routing table.** Run `next_hops` from A on the first card's trace graph (A->B 4, A->C 1, C->B 2, B->D 1, C->D 5, C->E 8, D->E 3, with A..E numbered 0..4). Expected: `[-1, 2, 2, 2, 2]`: every destination is reached through C first.
- **Exercise: contraction on a line.** Build the path a-b-c-d-e with every edge weighing 1 and contract b, then d, then c. Expected shortcuts: a-c 2, then c-e 2, then a-e 4.

> [!know]
> You now know how link-state and distance-vector routing apply Dijkstra and Bellman-Ford, and how contraction hierarchies make road queries fast.

=== practice
- 743 core
  cue: A signal leaves one node and travels along directed links with different delays; when has every node heard it?
  hint: Every node hears the signal at its earliest possible arrival time. How do you get those times, and which one answers "every node"?
  insight: Run Dijkstra from k with a heap of (time, node), skipping stale entries; delays are non-negative, so each pop is final. The answer is the largest distance, or -1 if some node stays at infinity.
  cost: O(E log V) time, O(V + E) space
  pattern: paths-dijkstra
- 1514 core
  cue: You want the route whose success chance, the product of the edge chances, is as large as possible.
  hint: Every extra edge multiplies by a number between 0 and 1. Does that let you settle the most reliable node first, as you settle the nearest node with distances?
  insight: Dijkstra with a max-heap (push negated probabilities) and multiplication as the combine step. Because every factor is at most 1, a route never improves as it grows, so the first pop of each node is final. Plain Dijkstra on weights -log p is equivalent.
  cost: O(E log V) time, O(V + E) space
  pattern: paths-dijkstra
- 1631 core
  cue: A route across a grid of heights is judged by its single worst step, not by its total.
  hint: If a route costs its largest step, can extending it ever make it cheaper? What does that allow?
  insight: Dijkstra where moving to a neighbour costs max(current effort, height difference). max never decreases and preserves order, so popped cells are final. Binary search on the effort limit with a BFS check, or union-find adding edges by weight, also work.
  cost: O(mn log(mn)) time, O(mn) space
  pattern: paths-variants
- 787 derive
  cue: The cheapest price between two cities, but you may change planes at most k times.
  hint: Keeping one best price per city can keep a cheap route that used too many flights. What does "the cheapest price using at most i flights" depend on?
  insight: Bellman-Ford limited to k + 1 rounds, each relaxing every flight from a copy of the previous round's prices, so after round i each price is exactly the cheapest with at most i flights. Relaxing in place lets one round chain several flights.
  cost: O(k·E) time, O(n) space
  pattern: paths-bellman
- 1334 core
  cue: For each of up to 100 cities you need how many others lie within a distance limit.
  hint: You need distances between every pair of cities. With n at most 100, what does n³ cost?
  insight: Floyd-Warshall gives all-pairs distances in about 10^6 steps; count, for each city, the others within the threshold and keep the smallest count, breaking ties towards the larger index (scan upwards and replace on <=).
  cost: O(n³) time, O(n²) space
  pattern: paths-floyd
- 1976 core
  cue: Count how many different routes achieve the minimum total travel time, modulo 10^9 + 7.
  hint: A route is shortest exactly when every edge on it is tight. In what order can you add counts so that a node's count is complete before you pass it on?
  insight: Dijkstra from 0 with a ways array: a strictly shorter arrival sets ways[v] = ways[u], an equal one adds ways[u]. With positive times a tight predecessor always pops first, so the pop order is a topological order of the shortest-path DAG.
  cost: O(E log V) time, O(V + E) space
  pattern: paths-dag
- cses:1195 core
  cue: One coupon halves the price of a single flight; find the cheapest trip from city 1 to city n.
  hint: Arriving somewhere with the coupon unused is a different situation from arriving with it spent. How many situations does each city have?
  insight: Dijkstra over states (city, used): each flight leads to (v, used) at full price and, from used = 0, also to (v, 1) at price // 2; the answer is the smaller of the two states at n. Alternatively run Dijkstra from 1 and from n on the reversed graph and try halving each flight u -> v.
  cost: O((n + m) log n) time, O(n + m) space
  pattern: paths-variants
- 2290 core
  cue: Cross a grid from corner to corner, where stepping onto an obstacle means removing it; minimise removals.
  hint: Moves onto empty cells are free and moves onto obstacles cost exactly one. What can replace the heap when only two edge costs exist?
  insight: 0-1 BFS with a deque: entering an empty cell weighs 0 (appendleft), entering an obstacle weighs 1 (append). The deque stays sorted by distance, so each cell is final when popped, in linear time.
  cost: O(mn) time and space
  pattern: paths-01bfs
- 1368 derive
  cue: Every cell shows an arrow; repainting an arrow costs 1; make the arrows lead from the top-left corner to the bottom-right.
  hint: From any cell one move is free and the other three each cost one repaint. What graph is that, and what are its weights?
  insight: Cells are nodes with four edges each, weight 0 in the arrow's direction and 1 otherwise; 0-1 BFS from (0, 0) gives the fewest repaints at the far corner. No cell needs repainting twice because a shortest route visits each cell once.
  cost: O(mn) time and space
  pattern: paths-01bfs
- 2203 stretch
  cue: Two sources must both reach one destination, and each edge used is paid for only once.
  hint: In an optimal answer, where do the two routes join, and what do they share after that point?
  insight: The routes meet at some vertex v and share v's route to dest. Run Dijkstra from src1, from src2, and from dest on the reversed graph; the answer is the minimum over v of d1[v] + d2[v] + d3[v], or -1 if every sum is infinite.
  cost: O(E log V) time, O(V + E) space
  pattern: paths-astar
- 864 stretch
  cue: Collect every key in a grid where each locked door opens only with its matching key; minimise steps.
  hint: Revisiting a cell is useful once you hold more keys. Besides your position, what must the search remember?
  insight: BFS over states (row, col, key mask): a lock is passable when its bit is set, a key sets its bit, and the first state with every bit set gives the answer. With at most 6 keys there are 64 states per cell.
  cost: O(mn·2^k) time and space
  pattern: paths-variants
- 1192 stretch
  cue: Find every connection whose failure would split the network into separate pieces.
  hint: An edge is safe if some other route joins its two ends. In a DFS tree, how can a subtree prove it has another way back up?
  insight: Low-link DFS: low[v] is the earliest discovery time reachable from v's subtree using one back edge, and the tree edge p - v is critical exactly when low[v] > disc[p]. Write the DFS iteratively in Python for 10^5 nodes.
  cost: O(V + E) time and space
  pattern: paths-structure
