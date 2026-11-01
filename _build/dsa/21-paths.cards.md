=== card | 743
time: 30 min

## The problem

A directed communication network has numbered stations and a nonnegative transmission delay on each link. A message starts at one station and can propagate along any directed route. Return the earliest time by which every station can have received it, or -1 if at least one never receives it. A station can forward as soon as it receives the message; simultaneous transmissions do not interfere.

For links 1→2 with delay 2, 1→3 with delay 8, and 2→3 with delay 1, station 3 hears the message at time 3, not 8. The required time is therefore 3.

## Constraints and what they imply

Labels run from 1 through `n`; `start` is a valid label. The standard bounds are `n <= 100`, at most 6,000 links, and delays from 0 through 100. Each link has a nonnegative integer delay, so taking another link cannot make an arrival earlier than the time already spent. The network may be disconnected, may contain cycles, and may have zero-delay links. Its direction matters: a link does not imply the reverse link exists. An adjacency list avoids scanning all possible station pairs.

## Brute force

Enumerate all simple routes from the source and record their durations. Nonnegative cycles can be removed without making a route worse, so a shortest simple route exists. Unfortunately there can be exponentially many such routes, and enumerating them separately for all destinations duplicates work. Another polynomial baseline repeatedly selects the least tentative distance by scanning all stations, which takes O(n² + m) time.

## The insight

Keep the best discovered arrival for each station in a min-heap. When a non-stale minimum is removed, no alternative route through an unprocessed station can improve it: that route must first reach an unprocessed station at least as late, then add a nonnegative delay. Relax outgoing links to discover possible improvements. Multiple entries for the same station are harmless when older, larger entries are discarded.

## Optimal solution, traced

```steps
Start at 1: tentative arrivals are [0, infinity, infinity]
    heap contains (0, 1)
---
Pop 1 and relax both links
    arrivals [0, 2, 8]
---
Pop 2 at 2; 2→3 improves 8 to 3
    arrivals [0, 2, 3]
---
Pop 3 at 3; its old entry at 8 is stale
    all stations heard by time {{3}}
```

The heap invariant makes each non-stale removal final, and each relaxation preserves the best known route. Consequently the largest final arrival is exactly the first time all stations have heard the message. An infinite distance witnesses an unreachable station.

## Code

```python
import heapq


def network_delay(times, n, start):
    graph = [[] for _ in range(n + 1)]
    for u, v, weight in times:
        graph[u].append((v, weight))
    dist = [float('inf')] * (n + 1)
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        cost, u = heapq.heappop(heap)
        if cost != dist[u]:
            continue
        for v, weight in graph[u]:
            candidate = cost + weight
            if candidate < dist[v]:
                dist[v] = candidate
                heapq.heappush(heap, (candidate, v))
    answer = max(dist[1:])
    return -1 if answer == float('inf') else answer
```

## Complexity

Building the lists takes O(n + m) space and time. There are at most O(m) successful relaxations, so the lazy heap has O(m + 1) entries and takes O(n + m log(m + 2)) time overall, with O(n + m) auxiliary space. For a simple graph, log m is O(log n). This includes storing the graph as well as the heap and distances.

## Mistakes and edge cases

- Use directed links only, and include the source's zero arrival in the maximum.
- Return -1 for any unreachable station, not the maximum finite distance.
- A one-station network takes zero time. Zero-delay edges are valid; negative delays invalidate the finalisation argument.

## Variations

- Recover the route to a particular station by storing a predecessor on each strict improvement.
- Start from several simultaneous sources by initialising each source with distance zero.

=== card | 1514
time: 30 min

## The problem

An undirected network has a success probability on each edge. Assuming edge successes are independent, a route succeeds with the product of its edge probabilities. Find the maximum success probability from `start` to `end`; return zero if no successful route connects them. The empty route from a node to itself has probability one.

For edges of probabilities 0.8 from 0 to 1, 0.5 from 1 to 2, and 0.3 directly from 0 to 2, the two-edge route wins with probability 0.4.

## Constraints and what they imply

Nodes are labelled from zero, and every probability lies in the closed interval [0, 1]. The standard problem allows up to 10,000 nodes and 20,000 edges. Probabilities can be zero or one; a longer route need not be more reliable. The factors' upper bound is essential: appending an edge cannot increase a route's probability. Store both directions of every undirected edge. Floating-point comparisons reflect the precision of the supplied probabilities.

## Brute force

Enumerate all simple routes and multiply the probabilities along each one, retaining the largest product. Removing a cycle never reduces a product because each factor is at most one, so considering simple routes suffices. However, the number of simple routes may be exponential, making this infeasible for a large network. Repeatedly scanning all nodes for the best unsettled probability gives an O(n² + m) alternative.

## The insight

Reverse Dijkstra's ordering: remove the largest tentative probability first and extend routes by multiplication. If a supposedly better route to that node existed, its first not-yet-settled node would already have a probability at least as large as the whole route, since later factors cannot increase it. That contradicts choosing the largest tentative value. Strict improvements only are inserted; stale heap entries are ignored.

## Optimal solution, traced

```steps
Start at 0 with probability 1
    best = [1, 0, 0]
---
Explore 0: candidates to 1 and 2 are 0.8 and 0.3
    best = [1, 0.8, 0.3]
---
Explore 1: extending its best route gives 0.8 × 0.5 = 0.4
    best = [1, 0.8, 0.4]
---
The highest remaining entry is node 2 at 0.4
    answer {{0.4}}
```

The first non-stale removal of the destination is optimal by the ordering argument, so the algorithm may return immediately. If no positive-probability route is reached, returning zero covers both disconnection and paths containing a zero edge.

## Code

```python
import heapq


def max_probability(n, edges, probabilities, start, end):
    graph = [[] for _ in range(n)]
    for (u, v), p in zip(edges, probabilities):
        graph[u].append((v, p))
        graph[v].append((u, p))
    best = [0.0] * n
    best[start] = 1.0
    heap = [(-1.0, start)]
    while heap:
        negative, u = heapq.heappop(heap)
        probability = -negative
        if probability < best[u]:
            continue
        if u == end:
            return probability
        for v, p in graph[u]:
            candidate = probability * p
            if candidate > best[v]:
                best[v] = candidate
                heapq.heappush(heap, (-candidate, v))
    return 0.0
```

## Complexity

There are O(m) successful improvements and heap entries. Building the graph and running the lazy heap costs O(n + m log(m + 1)) time and O(n + m) auxiliary space. For a simple graph, log m can be replaced by O(log n). A scan-based implementation avoids the heap but usually costs more on sparse networks.

## Mistakes and edge cases

- Do not add probabilities: a route's independent edge successes multiply.
- Negate priorities for Python's min-heap and skip outdated entries.
- `start == end` returns 1, even with no edges. An all-zero route returns 0.

## Variations

- Transform strictly positive probabilities into additive costs with negative logarithms.
- Record predecessors to return a maximum-probability route as well as its probability.

=== card | 1631
time: 30 min

## The problem

Move between orthogonally adjacent cells of a rectangular height map, beginning at the upper-left corner and ending at the lower-right. A move has difficulty equal to the absolute height difference of its two cells. The difficulty of a route is its hardest move, not the sum. Return the least possible route difficulty; a route of zero moves has difficulty zero.

For heights `[[1, 4], [2, 3]]`, going down then right has move difficulties 1 and 1, so the answer is 1 instead of the direct right-first route's 3.

## Constraints and what they imply

The grid is nonempty and rectangular, with at most 100 rows and 100 columns in the standard constraints. Heights are positive and at most one million. Every cell can be entered, and the graph is undirected with nonnegative move difficulties. There are `R*C` vertices and at most four outgoing moves per vertex. A route's difficulty never decreases when extended: its new value is the maximum of the old difficulty and the next step. This monotonicity permits a label-setting search.

## Brute force

Enumerate every simple route, calculate its largest step, and take the minimum. Removing a cycle cannot increase the maximum step, so an optimal simple route exists, but there can be exponentially many simple routes. Alternatively, sort possible step limits and perform a reachability search at each limit; that trades repeated searches for a simpler decision problem.

## The insight

For each cell maintain the least bottleneck found so far. From a cell with effort `d`, an edge of difficulty `w` offers effort `max(d, w)`. Process the smallest label first. Any alternative route through an unsettled cell must have already accumulated at least that cell's label, and later moves cannot lower the maximum. Thus a non-stale popped label is final just as in ordinary Dijkstra, despite the different extension operation.

## Optimal solution, traced

```steps
At (0,0), effort 0; its right and down steps cost 3 and 1
    labels: 0  3 / 1  infinity
---
Pop (1,0) at 1; moving right costs 1
    destination label max(1,1) = 1
---
Pop destination at 1 before the label 3
    optimal effort {{1}}
```

Every tentative label is realised by a route. The minimum-pop argument excludes any better route at finalisation, so returning when the destination is popped is safe.

## Code

```python
import heapq


def minimum_effort(heights):
    rows, cols = len(heights), len(heights[0])
    dist = [[float('inf')] * cols for _ in range(rows)]
    dist[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        effort, r, c = heapq.heappop(heap)
        if effort != dist[r][c]:
            continue
        if (r, c) == (rows - 1, cols - 1):
            return effort
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                step = abs(heights[r][c] - heights[nr][nc])
                candidate = max(effort, step)
                if candidate < dist[nr][nc]:
                    dist[nr][nc] = candidate
                    heapq.heappush(heap, (candidate, nr, nc))
```

## Complexity

There are O(RC) vertices and edges, so heap operations take O(RC log(RC + 1)) time and O(RC) auxiliary space, including labels and heap. Unlike a dense general graph, this grid has only a constant number of neighbours per cell.

## Mistakes and edge cases

- Do not add differences; only the largest step on a route counts.
- A single cell returns zero before considering neighbours.
- Do not mark a cell final when first inserted; a different route may improve its label before removal.

## Variations

- Binary-search an allowed difficulty and test connectivity using BFS.
- Sort grid edges by difficulty and unite endpoints until the two corners connect.

=== card | 787
time: 35 min

## The problem

Given directed flights with prices, find the least total price from `src` to `dst` using at most `k` intermediate stops. Return -1 when no such itinerary exists. A stop is a city between the endpoints, so at most `k` stops means at most `k + 1` flights. If source and destination coincide, the empty itinerary costs zero.

For flights 0→1 costing 2, 1→2 costing 2, and 0→2 costing 7, a zero-stop trip costs 7; allowing one stop reduces it to 4.

## Constraints and what they imply

There are `n` cities numbered from zero, with `n <= 100` and `0 <= k < n` in the standard constraints. Flight prices are positive integers up to 10,000; the code also accepts zero prices. Routes may be directed, disconnected, and include cycles. A low-cost arrival at a city is not enough state by itself if it consumes too many flights: a more expensive arrival with fewer flights remaining may be the only useful one. An edge budget of `k + 1` is explicit in the algorithm.

## Brute force

Enumerate all itineraries up to the permitted number of flights and keep the cheapest one ending at the destination. If a city can have `b` outgoing flights, the search tree can have O(b^(k+1)) nodes. It repeats many equivalent suffixes from the same city and budget. A dynamic program can instead aggregate all routes ending at the same city after each budget.

## The insight

Let the previous array hold the cheapest cost to each city using at most the previous number of flights. For the next budget, copy that array to preserve shorter itineraries, and relax every flight using only values from the previous array. Each new value is therefore either an old route or an old route plus one flight. Induction over the rounds proves the invariant, including paths using fewer than the allowed number of flights.

## Optimal solution, traced

```steps
Start with zero flights: costs [0, infinity, infinity]
---
First round reads only the initial array
    costs [0, 2, 7]
---
Second round reads [0, 2, 7], so 1→2 offers 4
    costs [0, 2, 4], answer {{4}}
```

Using the same array for reads and writes could consume both 0→1 and 1→2 during a single round, violating the budget. The separate snapshot makes the result independent of flight ordering.

## Code

```python
def cheapest_flight(n, flights, src, dst, k):
    dist = [float('inf')] * n
    dist[src] = 0
    for _ in range(k + 1):
        updated = dist[:]
        for u, v, price in flights:
            candidate = dist[u] + price
            if candidate < updated[v]:
                updated[v] = candidate
        dist = updated
    return -1 if dist[dst] == float('inf') else dist[dst]
```

## Complexity

Each of `k + 1` rounds copies `n` entries and checks `m` flights, giving O((k + 1)(n + m)) time and O(n) auxiliary space. The caller-owned flight list is not copied. The separate array is necessary for the round invariant, not merely a convenience.

## Mistakes and edge cases

- Count flights rather than intermediate cities; a direct flight uses one flight and zero stops.
- Do not relax in place. Unreachable origins remain at infinity and cannot produce finite candidates.
- No flights gives -1 unless source equals destination. Duplicate flights are handled independently.

## Variations

- Use a heap on `(city, flights used)` states when a state-space search is preferable.
- Retain a parent for each city and budget to reconstruct an optimal itinerary.

=== card | 1334
time: 30 min

## The problem

A weighted undirected network contains `n` cities. For each city count the other cities whose shortest-route distance is at most a given threshold. Return the city with the smallest count, resolving a tie in favour of the largest city index. A city is never counted as its own neighbour, even though its distance to itself is zero.

For a three-city chain with edge weights 2 and 2 and threshold 2, the endpoint counts are 1 and the middle count is 2. Both endpoints tie, so return city 2.

## Constraints and what they imply

Cities have indices 0 through `n-1`; `n` is positive and small enough for a cubic algorithm, typically at most 100. Edges are undirected and have nonnegative weights. Some pairs may have no route, and duplicate links can be represented safely by keeping the least weight. A threshold comparison is inclusive. All-pairs distances are useful because the question asks about every starting city.

## Brute force

For each source and destination, enumerate every simple route and take the shortest total before comparing with the threshold. In a dense graph the number of routes is exponential, and much of this work is duplicated. Running a single-source shortest-path search from each city is a practical alternative, but a compact all-pairs dynamic program suits the small dense case.

## The insight

Let `dist[i][j]` be the shortest distance using only already-processed intermediate cities. When city `k` becomes allowed, an optimal route either avoids it or can be split into an `i` to `k` route and a `k` to `j` route with earlier intermediates. Replacing each distance by the minimum of those choices establishes the next stage. The intermediate index must be the outer loop for that invariant.

## Optimal solution, traced

```steps
Chain 0 --(2)-- 1 --(2)-- 2 has threshold 2
    initial direct distances: d(0,1)=2, d(1,2)=2, d(0,2)=infinity
---
Allow city 1 as an intermediate
    d(0,2) becomes 2 + 2 = 4
---
Counts within 2 excluding the city itself are [1, 2, 1]
    tie between 0 and 2 selects {{2}}
```

After all intermediates have been allowed, every shortest simple route is represented. Scanning indices in increasing order and replacing the winner on equal counts implements the requested tie break.

## Code

```python
def city_with_fewest(n, edges, threshold):
    dist = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, weight in edges:
        dist[u][v] = min(dist[u][v], weight)
        dist[v][u] = min(dist[v][u], weight)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    answer, smallest = -1, n + 1
    for i in range(n):
        count = sum(i != j and dist[i][j] <= threshold for j in range(n))
        if count <= smallest:
            answer, smallest = i, count
    return answer
```

## Complexity

Initialising and counting use O(n²) time; the three nested relaxation loops take O(n³). The distance matrix uses O(n²) auxiliary space. Infinity naturally stays infinite when added to a finite distance, so unreachable pairs are excluded for a finite threshold.

## Mistakes and edge cases

- Exclude the city itself, compare with `<=`, and choose the larger index on ties.
- Keep `k` outermost; arbitrary loop orders need not compute all pairs correctly.
- With no edges all counts are zero, so the last index wins. A single city returns 0.

## Variations

- Answer many threshold queries by sorting each city's completed distance row.
- Replace Floyd-Warshall with one Dijkstra search per city on a sparse large graph.

=== card | 1976
time: 35 min

## The problem

An undirected road network connects numbered intersections. Each road has a positive travel time. Count distinct shortest routes from intersection 0 to intersection `n-1`, returning the count modulo 1,000,000,007. Two routes differ when their road sequences differ. If the destination cannot be reached, return zero.

For a direct road 0-2 of time 3 and roads 0-1 and 1-2 of times 1 and 2, there are two shortest routes of total time 3.

## Constraints and what they imply

The standard bounds are `n <= 200` and road times up to one billion. Travel times are strictly positive. This matters for counting: along every shortest route the distance strictly increases at each step, so the edges belonging to shortest routes form a directed acyclic graph when oriented by distance. The graph may contain cycles, but no positive cycle can belong to a shortest route. With one vertex the empty route is the single shortest route.

## Brute force

Enumerate all simple routes from the source to the destination, calculate each total, and count those achieving the smallest total. A shortest route is simple because every cycle costs positive time, yet the number of simple routes can be exponential. Even after finding the minimum, separately enumerating all routes tying it repeats shared prefixes.

## The insight

Dijkstra finalises distances in increasing order. Keep a count beside each distance. A strictly better route replaces both the distance and the count with its predecessor's count; a route tying the best distance adds its predecessor's count. Since road times are positive, every shortest predecessor has a smaller distance and is processed before its successor. Thus all contributions arrive before that successor forwards its own count.

## Optimal solution, traced

```steps
At 0: distance 0, ways 1
    relax 1 to (1, 1) and 2 to (3, 1)
---
Pop 1 at distance 1: edge 1-2 offers distance 3
    tie adds one way; node 2 now has (3, 2)
---
Pop 2 after both predecessors have contributed
    shortest-route count {{2}}
```

Every shortest route has one final edge from a smaller-distance predecessor. The update rules partition routes by that final edge, so they neither omit a route nor count a route twice. The modulus preserves addition and keeps counts bounded.

## Code

```python
import heapq


def count_shortest_routes(n, roads):
    mod = 1_000_000_007
    graph = [[] for _ in range(n)]
    for u, v, time in roads:
        graph[u].append((v, time))
        graph[v].append((u, time))
    dist = [float('inf')] * n
    ways = [0] * n
    dist[0], ways[0] = 0, 1
    heap = [(0, 0)]
    while heap:
        cost, u = heapq.heappop(heap)
        if cost != dist[u]:
            continue
        for v, weight in graph[u]:
            candidate = cost + weight
            if candidate < dist[v]:
                dist[v], ways[v] = candidate, ways[u]
                heapq.heappush(heap, (candidate, v))
            elif candidate == dist[v]:
                ways[v] = (ways[v] + ways[u]) % mod
    return ways[-1]
```

## Complexity

Building the graph takes O(n + m). The lazy heap has O(m) insertions, giving O(n + m log(m + 1)) time and O(n + m) auxiliary space. For simple graphs the logarithm is O(log n). Positive weights prevent equal-distance predecessors from requiring additional propagation after finalisation.

## Mistakes and edge cases

- Replace the count on a shorter path; add only on an equal path.
- A zero-weight road breaks the strictly increasing-distance proof and needs different treatment.
- Preserve the empty route for `n == 1`; disconnected destinations have zero ways.

## Variations

- Track a predecessor as well as the count to recover one shortest route.
- After computing distances, explicitly build the shortest-path DAG and count paths in distance order.

=== card | cses:1195
time: 35 min

## The problem

Directed flights connect cities labelled 1 through `n`. A traveller starts at city 1 and wants to reach city `n`. Apply a coupon to exactly one flight, replacing its integer price by its floor-halved price. Find the least total cost; return -1 when no such journey exists.

For flights 1→2 costing 9 and 2→3 costing 5, discounting the first flight costs 4 + 5 = 9, whereas discounting the second costs 9 + 2 = 11.

## Constraints and what they imply

The standard constraints allow up to 100,000 cities and 200,000 flights, with positive integer prices up to one billion; the destination is reachable and `n >= 2`. The function also accepts zero prices and reports unreachable cases. Travel is directed, the coupon cannot be used twice, and odd prices round down after division by two. An arrival with a cheap price but no coupon remaining cannot always replace a more expensive arrival with the coupon available; the future options differ. Therefore each city needs two labels, one for each coupon status.

## Brute force

Enumerate each simple route and try discounting every flight in that route. With distinct endpoints and nonnegative prices, cycles need not help: if the coupon was used on a removed cycle, it can instead be used on a remaining flight without increasing cost. The number of simple routes can be exponential, and every route repeats coupon-placement work. A polynomial alternative runs shortest-path searches from the source and backward from the destination, then tries each flight as the discounted one.

## The insight

Construct a state graph `(city, used)` with two versions of each city. Every original flight keeps the status at full cost; from an unused state it also offers a transition to a used state at floor-half cost. All expanded edge costs are nonnegative, so ordinary Dijkstra applies. Every legal itinerary maps to one expanded path and vice versa, preserving its price.

## Optimal solution, traced

```steps
At (1, unused), cost 0
    flight 1→2 gives (2, unused) at 9 and (2, used) at 4
---
From (2, used), the second flight costs 5
    (3, used) receives cost 9
---
Using the coupon on the second flight instead costs 9 + 2 = 11
    best destination cost {{9}}
```

The first non-stale destination state with the coupon used represents a legal route, and no cheaper expanded path can be waiting behind it because all transitions are nonnegative. An unused destination state is not itself a valid answer.

## Code

```python
import heapq


def discount_flight(n, flights):
    graph = [[] for _ in range(n + 1)]
    for u, v, price in flights:
        graph[u].append((v, price))
    dist = [[float('inf')] * 2 for _ in range(n + 1)]
    dist[1][0] = 0
    heap = [(0, 1, 0)]
    while heap:
        cost, u, used = heapq.heappop(heap)
        if cost != dist[u][used]:
            continue
        if u == n and used:
            return cost
        for v, price in graph[u]:
            if cost + price < dist[v][used]:
                dist[v][used] = cost + price
                heapq.heappush(heap, (cost + price, v, used))
            if not used and cost + price // 2 < dist[v][1]:
                dist[v][1] = cost + price // 2
                heapq.heappush(heap, (dist[v][1], v, 1))
    return -1
```

## Complexity

The expanded graph has 2n states and at most 3m transitions. Lazy Dijkstra takes O(n + m log(m + 1)) time and O(n + m) auxiliary space, including adjacency lists and heap. For simple graphs, the logarithm is O(log n).

## Mistakes and edge cases

- Store separate distances for unused and used coupons; mixing them discards useful future options.
- Apply integer floor division only to the chosen flight, and never apply the coupon twice.
- The coupon must actually be used: an empty journey does not qualify. An unreachable target returns -1.

## Variations

- Compute source distances and reverse destination distances, then minimise over the discounted edge.
- Permit several coupons by adding the number already used to the state.

=== card | 2290
time: 45 min

## The problem

A rectangular board contains open cells marked 0 and removable obstacles marked 1. Starting at the upper-left cell, move one cell up, down, left, or right at a time until reaching the lower-right cell. Entering an obstacle requires removing it. Find the smallest number of obstacles that need to be removed. The starting and ending cells are open; a one-cell board needs no removals.

For `[[0, 1, 0], [0, 1, 0]]`, any route to the last column crosses an obstacle, and one removal suffices. The answer is therefore 1. A longer route can be preferable to a shorter route if it crosses fewer obstacles.

## Constraints and what they imply

The grid is nonempty and rectangular, with values only 0 and 1 and at most 100,000 cells in the standard constraints. Every obstacle is removable, so the destination is reachable. The implicit graph has one vertex per cell and at most four outgoing edges per vertex. A move's cost is the value of the cell being entered, not the value of the cell being left. Thus every edge weight is exactly zero or one, which permits a deque rather than a general priority queue.

If a walk enters the same obstacle repeatedly, the real board requires only one removal. This does not invalidate the graph model: deleting cycles from any walk never increases its graph cost, and a simple route visits each obstacle at most once. Hence some optimal simple route is charged exactly once per obstacle it removes.

## Brute force

Try subsets of obstacle cells in increasing size, temporarily treat the chosen cells as open, and run a reachability search. The first successful subset gives the answer. With `B` obstacles there are up to 2^B subsets, and each reachability test costs O(RC). The exponential choice of removals is the bottleneck, even though testing a fixed choice is easy. A heap-based shortest-path search is already polynomial, but it does not exploit the two possible edge weights.

## The insight

Maintain the best known removal count for each cell. For an improvement through an open cell, place the new entry at the front of a deque; for an improvement through an obstacle, place it at the back. The deque processes non-stale entries in nondecreasing distance: while processing distance `d`, new labels are only `d` or `d+1`, and the former must precede the latter. Store the distance inside each entry so an obsolete entry can be skipped after a later improvement.

This is Dijkstra's label-setting argument specialised to two weights. Once a cell is popped with its current distance, a cheaper path would have had an earlier unsettled predecessor, contradicting the deque order. First discovery is not final: a cell initially reached through an obstacle may later be reached free from a different direction. Strict relaxation allows that correction without repeatedly inserting equal labels.

## Optimal solution, traced

```steps
Board: 0 1 0 / 0 1 0. Start at (0,0) with cost 0
    deque [(0,0,0)]
---
Entering (1,0) costs 0 and entering (0,1) costs 1
    zero-cost entry goes to the front; obstacle entry goes to the back
---
From (1,0), entering (1,1) offers cost 1
    later (1,2) is reachable without an additional removal
---
The destination is popped at cost 1
    minimum removals {{1}}
```

Every tentative distance is realised by a walk. The pop-order invariant proves that the destination's first current entry is optimal. The cycle-removal argument then identifies this edge-weight optimum with the minimum number of distinct obstacles removed on the actual board.

## Code

```python
from collections import deque


def minimum_obstacles(grid):
    rows, cols = len(grid), len(grid[0])
    dist = [[float('inf')] * cols for _ in range(rows)]
    dist[0][0] = 0
    queue = deque([(0, 0, 0)])
    while queue:
        cost, r, c = queue.popleft()
        if cost != dist[r][c]:
            continue
        if (r, c) == (rows - 1, cols - 1):
            return cost
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                weight = grid[nr][nc]
                candidate = cost + weight
                if candidate < dist[nr][nc]:
                    dist[nr][nc] = candidate
                    entry = (candidate, nr, nc)
                    if weight == 0:
                        queue.appendleft(entry)
                    else:
                        queue.append(entry)
```

## Complexity

Let `N = R*C`. There are O(N) edges. Each non-stale cell is expanded once; every expansion examines at most four edges and causes at most one insertion per successful relaxation. Stale entries are skipped. The total time is O(N), and the distances and deque take O(N) auxiliary space. This includes the worst case in which several entries for one cell exist temporarily.

## Mistakes and edge cases

- Do not use ordinary BFS ordered by number of moves; it minimises steps rather than removals.
- Do not mark a cell permanently visited when first enqueued. A later zero-cost detour can improve it.
- Charge the destination cell of a move, and do not charge the open starting cell.
- A single cell returns zero. The procedure does not mutate the supplied board.
- The deque rule relies on weights 0 and 1; arbitrary weights need a different priority structure.

## Variations

- Return an actual minimum-removal route by recording the predecessor on each strict improvement.
- Replace obstacle costs with arbitrary nonnegative entry costs and use heap Dijkstra.
- Ask whether the destination is reachable after at most `b` removals by comparing the result to `b`.

=== card | 1368
time: 45 min

## The problem

Each cell of a rectangular board contains an arrow pointing right, left, down, or up, encoded respectively as 1, 2, 3, or 4. A traveller begins at the upper-left and follows the arrow in each visited cell. Before travelling, any cell's arrow can be changed to another direction at cost one per changed cell. Find the minimum cost that makes it possible to reach the lower-right cell. Arrows may initially point outside the board.

For `[[1, 1], [4, 3]]`, following the top-left arrow reaches the top-right cell. Changing that cell's right arrow to down reaches the destination, for cost 1. The arrow at the destination is irrelevant because travel stops there.

## Constraints and what they imply

The grid is nonempty, rectangular, and consists of codes 1 through 4; each dimension is at most 100 in the standard constraints. Each orthogonal move from a cell costs zero when it agrees with that cell's original arrow, or one when its arrow must be changed. The relevant arrow belongs to the cell being left, not the cell being entered. There are `R*C` vertices and at most four candidate edges per cell; directions pointing out of bounds are simply not usable moves.

A general walk could revisit a cell and request two different outgoing arrows, which a single fixed board cannot provide. However, every reachable walk has a simple path obtained by removing cycles. Removing cycles cannot increase the number of mismatching edges, and on a simple path every cell needs at most one outgoing direction. Thus minimising mismatches over paths is equivalent to minimising the number of changed cells.

## Brute force

Choose a new direction for every cell, simulate travel, and retain the least number of changed arrows among assignments that reach the destination. There are up to 4^(RC) assignments and a simulation may inspect O(RC) cells before reaching the target, leaving the board, or repeating a state. Most assignments differ in cells never visited. Instead of choosing a complete board in advance, a shortest-path search pays only for the directions on a selected route.

## The insight

Use 0-1 BFS on the implicit directed graph. The outgoing edge matching the current cell's arrow has cost zero; all other valid outgoing edges cost one. Maintain the smallest cost found for each cell, adding a zero-cost improvement to the front of a deque and a one-cost improvement to the back. Each entry stores its cost, so obsolete entries can be ignored without suppressing a later improvement.

At any point the deque's current-distance entries are ordered like a priority queue: from distance `d`, only `d` and `d+1` can be inserted, and the zero extension is inserted before larger candidates. Therefore a non-stale popped cell has its minimum mismatch cost. Marking a cell visited as soon as it is enqueued would be unsafe because a cheaper route may be discovered before that pop.

## Optimal solution, traced

```steps
Board 1 1 / 4 3: start (0,0), cost 0
    right agrees with arrow: enqueue (0,1) at front with cost 0
---
At (0,1), the arrow points outside; down requires a change
    enqueue destination (1,1) at back with cost 1
---
Other routes cannot improve the popped destination below 1
    minimum changed arrows {{1}}
```

A path produced by the graph can be made executable by changing exactly its mismatching outgoing arrows; its simplicity ensures no conflicting requirements on a cell. Conversely, following any successful modified board gives a path whose mismatches cannot exceed the number of modified cells. These two directions prove equality of the optima.

## Code

```python
from collections import deque


def minimum_arrow_changes(grid):
    rows, cols = len(grid), len(grid[0])
    directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
    dist = [[float('inf')] * cols for _ in range(rows)]
    dist[0][0] = 0
    queue = deque([(0, 0, 0)])
    while queue:
        cost, r, c = queue.popleft()
        if cost != dist[r][c]:
            continue
        if (r, c) == (rows - 1, cols - 1):
            return cost
        for arrow, (dr, dc) in enumerate(directions, 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                weight = int(grid[r][c] != arrow)
                candidate = cost + weight
                if candidate < dist[nr][nc]:
                    dist[nr][nc] = candidate
                    entry = (candidate, nr, nc)
                    if weight == 0:
                        queue.appendleft(entry)
                    else:
                        queue.append(entry)
```

## Complexity

With `N = R*C` cells, there are O(N) edges. Each current-distance cell is expanded at most once, so all neighbour checks and successful insertions take O(N) time; stale deque entries are discarded. Distances and the deque together use O(N) auxiliary space. The board is not modified.

## Mistakes and edge cases

- Compare the move direction with the arrow at the source cell, not the neighbour's arrow.
- Treat arrows pointing out of bounds as unusable moves, not as free exits.
- A single-cell board costs zero even if its arrow points outside.
- A directed zero-cost cycle does not require endlessly revisiting cells: only strict improvements enter the deque.
- Do not count changes at the destination; no departure is needed there.

## Variations

- Recover the cells to repaint by recording the predecessor and chosen direction for each improvement.
- Assign arbitrary repaint prices per cell and use Dijkstra instead of 0-1 BFS.
- Compute the cost to reach every cell, rather than stopping at the first destination pop.

=== card | 2203
time: 50 min

## The problem

A directed weighted network has two starting vertices and one destination. Choose a set of edges that allows each start to reach the destination, paying an edge's weight only once even if both routes use it. Return the smallest possible total weight of the chosen set, or -1 if the required connectivity is impossible. The starts and destination may coincide.

For edges 0→2 costing 2, 1→2 costing 3, and 2→3 costing 4, both travellers can meet at 2 and share the last edge. The set costs 2 + 3 + 4 = 9, rather than paying for that last edge twice.

## Constraints and what they imply

Vertices are numbered 0 through `n-1`; weights are nonnegative and edges are directed. The standard constraints allow up to 100,000 vertices and 100,000 edges, with positive weights at most 100,000; the function also accepts zero weights. A set may contain parallel edges, and an unreachable destination must be reported explicitly. Nonnegative weights allow unnecessary edges to be deleted without increasing the cost. The answer concerns the union of edges, not the sum of two independently chosen route prices, so separate shortest routes to the destination may fail to account for useful sharing.

The candidate meeting vertex can be either source or the destination itself. To obtain distances *to* the destination with one search, reverse every edge and run a shortest-path algorithm from the destination in the reversed network. Such a reversed route corresponds exactly to an original route in the opposite order, with the same weight.

## Brute force

Enumerate all subsets of the `m` edges. For each subset check by directed traversal whether both sources can reach the destination, and minimise the total weight of successful subsets. This is a direct model of paying each edge once, but it needs O(2^m(n + m)) time. Enumerating pairs of simple source-to-destination routes has the same exponential difficulty and must carefully deduplicate their common edges.

## The insight

For each candidate junction `v`, add the shortest distance from the first source to `v`, the shortest distance from the second source to `v`, and the shortest distance from `v` to the destination. Three Dijkstra searches supply all such values: two on the original graph and one from the destination on the reverse graph. Taking the smallest finite sum gives the optimum.

Why does a single shared suffix suffice? Consider an optimal edge set and discard edges not needed to reach the destination. Within the remaining set select one outgoing edge at every relevant vertex that moves closer in *hop count* to the destination. These choices cannot cycle, and they preserve both sources' reachability while using no additional edges. The resulting directed paths merge at some vertex and then share their suffix. Their three segments have total cost no greater than the original set, and replacing each segment by a shortest path can only lower the candidate sum.

Conversely, for any candidate vertex, the union of three selected shortest paths connects both sources to the destination. Its actual edge-set cost is at most the sum, because overlapping edges are paid once and weights are nonnegative. Together the two inequalities prove that the minimum candidate sum equals the true minimum union cost, even if independently selected shortest paths overlap before the nominated junction.

## Optimal solution, traced

```steps
Edges 0→2 (2), 1→2 (3), 2→3 (4); destination 3
    distances to 2 from the sources are 2 and 3
---
Search from 3 on reversed edges
    distance from 2 to 3 in the original network is 4
---
At junction 2 the candidate is 2 + 3 + 4 = 9
    minimum edge-set cost {{9}}
```

If no vertex has all three finite distances, no connecting edge set exists. Otherwise the junction argument and the union construction establish both feasibility and optimality.

## Code

```python
import heapq


def minimum_shared_weight(n, edges, src1, src2, dest):
    graph = [[] for _ in range(n)]
    reverse = [[] for _ in range(n)]
    for u, v, weight in edges:
        graph[u].append((v, weight))
        reverse[v].append((u, weight))

    def distances(start, adjacency):
        dist = [float('inf')] * n
        dist[start] = 0
        heap = [(0, start)]
        while heap:
            cost, u = heapq.heappop(heap)
            if cost != dist[u]:
                continue
            for v, weight in adjacency[u]:
                candidate = cost + weight
                if candidate < dist[v]:
                    dist[v] = candidate
                    heapq.heappush(heap, (candidate, v))
        return dist

    first = distances(src1, graph)
    second = distances(src2, graph)
    suffix = distances(dest, reverse)
    answer = min(first[v] + second[v] + suffix[v] for v in range(n))
    return -1 if answer == float('inf') else answer
```

## Complexity

Each lazy Dijkstra run costs O(n + m log(m + 1)) time, including graph setup terms. Three runs change only the constant factor, and scanning candidate junctions costs O(n). The graph, reverse graph, three distance arrays, and heap require O(n + m) auxiliary space. With a simple graph, log m is O(log n).

## Mistakes and edge cases

- Reverse the graph for the destination search; forward distances from the destination answer a different question.
- Do not merely add two independently shortest source-to-destination distances; shared edges are paid once.
- Evaluate every vertex, including the sources and destination, and retain infinity until reachability is checked.
- If both sources equal the destination, the empty set has cost zero. Zero-weight and parallel edges remain valid.
- The proof and Dijkstra both rely on nonnegative weights.

## Variations

- Record predecessors in each run and reconstruct one optimal connecting edge set, deduplicating overlaps.
- If the network is a DAG, compute the three distance arrays using topological relaxation instead of a heap.
- Generalise to more than two sources; a single junction is no longer sufficient to describe every optimum.

=== card | 864
time: 50 min

## The problem

A traveller moves orthogonally through a rectangular character grid. `#` is a wall, `.` is floor, `@` is the starting cell, lowercase letters are keys, and an uppercase letter is a locked door opened by its matching lowercase key. Keys are retained after use. Return the fewest moves needed to collect all keys, or -1 if this is impossible. If there are no keys, the answer is zero.

For the single row `@.aA.b`, the traveller takes five moves to collect both keys: the `a` key permits passage through `A`, then the final step reaches `b`.

## Constraints and what they imply

The board is nonempty and rectangular, with each dimension at most 30, exactly one start and at most six distinct keys in the usual setting. Each key type appears once; keys need not be adjacent letters in the alphabet in this implementation. A door whose matching key does not appear is permanently impassable. Every legal move costs one and keys are never consumed, so breadth-first search finds minimum moves in a graph whose vertices contain both position and inventory.

Position alone is insufficient: a cell visited before finding a key may need to be revisited afterwards to pass a door. Represent the set of collected key types by a bit mask. For `k` distinct key types, each cell can have at most 2^k different inventory states. A state may collect a key as it enters that cell; a door must be checked against the inventory held before entering it.

## Brute force

Enumerate sequences of moves until all keys have been visited. This can revisit the same cell indefinitely, especially around cycles, and even a finite depth cutoff explores many duplicate histories. Enumerating orders in which keys are collected is also awkward: a proposed segment can pass through other keys or doors, so a plain distance between locations loses necessary inventory information. Recording complete position-and-inventory states merges histories with identical future possibilities.

## The insight

Start BFS at `(start row, start column, empty mask)`. For each legal neighbour, reject walls and locked doors without a matching owned bit. If the neighbour contains a key, set its bit in the new mask. Enqueue a state only the first time that exact position and mask appear. The first state with every key bit set is optimal because BFS processes states by nondecreasing move count.

This representation is sufficient: given the same cell and the same set of keys, the legal next moves are identical regardless of how the traveller arrived. Keys never disappear, and opening a door has no additional persistent effect. Thus removing a duplicate state cannot remove a uniquely useful future. Different masks at the same cell must still remain distinct, even if one of them was seen earlier.

## Optimal solution, traced

```steps
Row @.aA.b: initial state is position 0, mask 00, distance 0
---
Move twice to a and collect it
    position 2, mask 01, distance 2
---
Enter A using a, then pass the floor and enter b
    position 5, mask 11, distance 5
---
Both key bits are set on the first such BFS state
    minimum moves {{5}}
```

Every queued transition is a legal single move, and every legal move is represented by a transition. BFS therefore explores all feasible states in distance order; exhaustion without a full mask proves that collecting all keys is impossible.

## Code

```python
from collections import deque


def shortest_collect_keys(grid):
    rows, cols = len(grid), len(grid[0])
    keys = sorted({cell for row in grid for cell in row if 'a' <= cell <= 'z'})
    bits = {key: 1 << i for i, key in enumerate(keys)}
    goal = (1 << len(keys)) - 1
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == '@':
                start = (r, c)
    queue = deque([(start[0], start[1], 0, 0)])
    seen = {(start[0], start[1], 0)}
    while queue:
        r, c, mask, steps = queue.popleft()
        if mask == goal:
            return steps
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            cell = grid[nr][nc]
            if cell == '#':
                continue
            if 'A' <= cell <= 'Z':
                bit = bits.get(cell.lower(), 0)
                if not (mask & bit):
                    continue
            new_mask = mask | bits.get(cell, 0)
            state = (nr, nc, new_mask)
            if state not in seen:
                seen.add(state)
                queue.append((nr, nc, new_mask, steps + 1))
    return -1
```

## Complexity

Let `N = R*C` and `k` be the number of distinct keys. There are at most `N*2^k` states and four transitions from each, so BFS takes O(N*2^k) time and space. Finding the keys and start costs O(N), and sorting the key types costs O(k log k). With at most six keys, the state factor is at most 64.

## Mistakes and edge cases

- Store `(row, column, mask)` in `seen`; storing only coordinates incorrectly prevents useful revisits.
- Test a lock against the corresponding lowercase key, including the case where that key does not exist.
- Build a compact key-to-bit mapping rather than assuming present letters are consecutive.
- Check the empty goal mask before taking a move. An inaccessible key yields -1.
- The mask describes keys collected, not doors visited; a key remains available indefinitely.

## Variations

- Track predecessors for full states to recover a shortest sequence of moves.
- Add consumable keys or switches to the state; the current key-mask model alone would no longer suffice.
- Change moves to nonuniform costs and run Dijkstra over the same state space.

=== card | 1192
time: 50 min

## The problem

An undirected network consists of numbered vertices and connections. A connection is critical when deleting that one connection increases the number of connected components. Return all such connections in any order and either endpoint order. An isolated vertex contributes no connection to the answer; the algorithm also handles disconnected networks and parallel connections.

For edges 0-1, 1-2, 2-0, and 1-3, the first three form a cycle and survive deletion individually. The edge 1-3 is the only critical connection because removing it isolates vertex 3.

## Constraints and what they imply

The network may contain up to roughly 100,000 vertices, so recursive DFS can exceed Python's recursion limit on a long chain. An explicit stack avoids that failure. Undirected edges appear in both adjacency lists, but they are a single connection: attach an edge ID to each adjacency entry so that the DFS skips only the exact parent edge. This detail also makes the implementation correct when two edges have the same endpoints.

A bridge is a tree edge in every depth-first forest. A non-tree edge already has an alternative tree path between its endpoints, so deleting it cannot disconnect its component. For a tree edge, the issue is whether its child subtree has a different way back to the parent or an ancestor.

## Brute force

For each edge, remove that exact edge and traverse the graph to count connected components. If the count increases compared with the original graph, the edge is critical. A traversal takes O(n + m), and repeating it for all `m` edges costs O(m(n + m)) time, with O(n + m) graph and traversal space. It is a useful small-input oracle but is too expensive for a large sparse graph.

## The insight

Give each vertex a discovery time `tin` as DFS first enters it. Let `low[u]` be the earliest discovery time reachable from the DFS subtree rooted at `u` using zero or more tree edges downward and at most one non-tree edge back upward. On completing a child `v`, combine `low[v]` into `low[u]`. The parent edge `u-v` is a bridge exactly when `low[v] > tin[u]`: no edge from the child's subtree reaches `u` or any ancestor of `u`.

The strict inequality matters. If `low[v] == tin[u]`, a back edge reaches `u` itself and supplies an alternative route, so the tree edge is not critical. A connection to a descendant encountered after that descendant was explored cannot lower `low[u]` below `tin[u]`, and is harmless. Edge IDs distinguish the one tree edge to skip from another parallel edge, which is a valid back edge.

## Optimal solution, traced

```steps
Explore 0-1-2, then see the back edge 2-0
    tin[0]=0, tin[1]=1, tin[2]=2; low[2] becomes 0
---
Finish 2 and propagate low 0 to 1
    low[2] is not greater than tin[1], so 1-2 is not critical
---
Explore and finish leaf 3 from 1
    low[3]=3 > tin[1]=1, so 1-3 is critical
---
Finish 1: low[1]=0 equals tin[0]
    only bridge is {{1-3}}
```

An explicit stack holds the next adjacency index for each active vertex. Completion occurs only after all neighbours have been examined, exactly when a recursive DFS would return and propagate the child's low value. This postorder timing is essential to the bridge test.

## Code

```python
def critical_connections(n, edges):
    graph = [[] for _ in range(n)]
    for edge_id, (u, v) in enumerate(edges):
        graph[u].append((v, edge_id))
        graph[v].append((u, edge_id))
    tin = [-1] * n
    low = [0] * n
    parent = [-1] * n
    parent_edge = [-1] * n
    clock = 0
    bridges = []
    for root in range(n):
        if tin[root] != -1:
            continue
        tin[root] = low[root] = clock
        clock += 1
        stack = [(root, 0)]
        while stack:
            u, index = stack[-1]
            if index == len(graph[u]):
                stack.pop()
                p = parent[u]
                if p != -1:
                    if low[u] > tin[p]:
                        bridges.append([p, u])
                    low[p] = min(low[p], low[u])
                continue
            v, edge_id = graph[u][index]
            stack[-1] = (u, index + 1)
            if edge_id == parent_edge[u]:
                continue
            if tin[v] == -1:
                parent[v], parent_edge[v] = u, edge_id
                tin[v] = low[v] = clock
                clock += 1
                stack.append((v, 0))
            else:
                low[u] = min(low[u], tin[v])
    return bridges
```

## Complexity

Building adjacency lists takes O(n + m). Each vertex is pushed and popped once, and each edge has two adjacency entries, so the full DFS forest takes O(n + m) time. Graph storage, discovery arrays, and the explicit stack use O(n + m) auxiliary space. The output can itself contain O(m) edges.

## Mistakes and edge cases

- Use `low[child] > tin[parent]`, not greater-than-or-equal, and test only after finishing the child's entire subtree.
- Skip the exact parent edge ID, not every edge to the parent vertex: parallel edges protect one another.
- Start DFS from every undiscovered vertex if disconnected inputs are allowed.
- A chain has every edge critical; a cycle has none. Self-loops are never bridges.
- Avoid relying on recursion depth for a graph shaped like a very long chain.

## Variations

- Find articulation vertices using related discovery and low values, with a special rule for DFS roots.
- Contract all non-bridge edges to build a bridge forest of two-edge-connected components.
- Answer repeated edge-failure queries after preprocessing the bridge forest.
