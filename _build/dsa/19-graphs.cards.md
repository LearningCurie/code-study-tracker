=== card | 1971
time: 20 min

## The problem

There are `n` vertices labelled from zero, and each pair in `edges` describes a connection usable in either direction. Determine whether `destination` can be reached from `source` by following zero or more connections. For example, edges `[[0, 1], [1, 2]]` connect 0 to 2 through 1.

## Constraints and what they imply

Labels are in `0..n-1`; there may be many vertices and edges, so avoid looking through the complete edge list for every step. A vertex is reachable from itself without traversing an edge. Connections need not make the entire graph connected.

## Brute force

Search from the source, but for each discovered vertex scan the whole edge list to find incident edges. With up to `n` discovered vertices this takes O(nE) time. A visited set is still necessary to stop repeated exploration around a cycle.

## The insight

Index the connections by endpoint once. Breadth-first search then expands each discovered vertex and marks neighbours immediately when enqueued. The queue contains only reachable vertices, and every reachable vertex is eventually expanded. Thus discovering the target proves a path exists; exhausting the queue proves none exists.

## Optimal solution, traced

```steps
edges = [[0, 1], [1, 2]], source = 0, destination = 2
    queue [0], seen {0}
---
Expand 0 then 1
    queue [2], seen {0, 1, 2}
---
Remove 2, which is the destination
    return {{True}}
```

## Code

```python
from collections import deque

def valid_path(n, edges, source, destination):
    adjacency = [[] for _ in range(n)]
    for u, v in edges:
        adjacency[u].append(v)
        adjacency[v].append(u)
    queue = deque([source])
    seen = {source}
    while queue:
        u = queue.popleft()
        if u == destination:
            return True
        for v in adjacency[u]:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return False
```

## Complexity

Building and traversing the adjacency lists takes O(V + E) time and O(V + E) space, including the graph representation. The search alone needs O(V) additional space.

## Mistakes and edge cases

- Add both orientations; the pairs describe undirected connections.
- Mark at enqueue time, not after expansion, to avoid duplicate queue entries.
- An isolated source equals the target only when both labels are the same.

## Variations

- Return an actual path by recording each newly discovered vertex's predecessor.
- Answer many queries using connected-component labels computed once.

=== card | 733
time: 20 min

## The problem

Given a rectangular image, a starting row and column, and a replacement colour, recolour exactly the pixels connected to the start through horizontal or vertical steps whose original colour equals the starting colour. Modify and return the image. Diagonal contact alone does not connect pixels.

## Constraints and what they imply

The image is nonempty and the start is in bounds. A whole image can be one region, so recursion depth could be proportional to its area. If the replacement equals the starting colour, changing a pixel cannot serve as a visited mark; return immediately in that case.

## Brute force

Repeatedly scan every pixel, adding a pixel to a set when an already selected neighbour has the starting colour, until a pass makes no changes. A long winding region can require O(mn) passes over O(mn) pixels, giving O((mn)²) time and O(mn) space.

## The insight

Use an explicit stack for a graph search. Change the start before pushing it, and change every eligible neighbour before pushing it too. Since the new colour differs from the old colour, a changed pixel cannot be added twice. The search reaches precisely the old-colour component: each added pixel has an eligible path from the start, and every eligible neighbour of every reached pixel is eventually considered.

## Optimal solution, traced

```steps
image = [[1, 1], [1, 0]], start = (0, 0), replacement = 2
    recolour and push (0, 0)
---
The fill reaches (0, 1) and (1, 0), but not the 0 pixel
    image {{[[2, 2], [2, 0]]}}
```

## Code

```python
def flood_fill(image, sr, sc, color):
    rows, cols = len(image), len(image[0])
    old = image[sr][sc]
    if old == color:
        return image
    image[sr][sc] = color
    stack = [(sr, sc)]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and image[nr][nc] == old:
                image[nr][nc] = color
                stack.append((nr, nc))
    return image
```

## Complexity

Each pixel enters the stack at most once and checks four neighbours: O(mn) time and O(mn) worst-case auxiliary space. The input image is modified in place.

## Mistakes and edge cases

- Returning early for an unchanged colour prevents infinite revisits.
- Check row and column bounds separately; the image need not be square.
- Pixels with the same colour in a separate component remain unchanged.

## Variations

- Preserve the original image by copying it before the fill.
- Fill eight-connected rather than four-connected regions by adding diagonal directions.

=== card | 200
time: 25 min

## The problem

Count the separate land masses in a rectangular grid of `"1"` land and `"0"` water. Land cells belong to the same mass if a chain of horizontal or vertical land neighbours joins them. For `[['1', '0'], ['0', '1']]`, the answer is two: corner contact does not join the cells.

## Constraints and what they imply

The grid is nonempty and rectangular. It may contain only water or only land, and one connected region can cover every cell. Each cell has a constant number of potential neighbours, so a traversal over the implicit graph is linear in the grid area. The implementation below changes visited land to water; copy the rows first if the caller needs to preserve them.

Mutating the grid changes subsequent calls on the same object: after the first call, all original land has been erased. The number of original water cells is irrelevant to the count except that they separate components. Boundary checks ensure that cells at opposite ends of a row never wrap around.

## Brute force

For each land cell, run a new search to construct its entire reachable set, then deduplicate these sets. If all `mn` cells are land, this repeats a linear-size traversal for each cell: O((mn)²) time. Storing all sets can also require quadratic space. The redundancy is searching the same component from every one of its members.

## The insight

Scan cells in any fixed order. When encountering unmarked land, increment the count and flood its entire component, marking cells as soon as they are pushed. The next unmarked land cannot be in any previously counted component: a complete flood would have marked it. Conversely, every land component contains a first cell in the scan, so each component contributes exactly once.

## Optimal solution, traced

```steps
grid = [['1', '1', '0'], ['0', '1', '1'], ['1', '0', '0']]
    first land at (0, 0), count 1
---
Flood reaches (0, 1), (1, 1), and (1, 2)
    all four become '0'
---
Scan reaches (2, 0), which starts a second flood
    count {{2}}
```

## Code

```python
def num_islands(grid):
    rows, cols = len(grid), len(grid[0])
    islands = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != "1":
                continue
            islands += 1
            grid[r][c] = "0"
            stack = [(r, c)]
            while stack:
                x, y = stack.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == "1":
                        grid[nx][ny] = "0"
                        stack.append((nx, ny))
    return islands
```

## Complexity

The outer scan touches every cell once; all floods together push each land cell once and inspect four neighbours. Total time is O(mn), not O((mn)²). The stack can hold O(mn) cells; the algorithm uses the input itself for marks.

## Mistakes and edge cases

- Compare strings, not integer `1`; the grid stores character values.
- Mark before pushing, otherwise multiple neighbours can push the same land cell.
- Water-only grids return zero; diagonal-only contacts remain separate.
- Iteration avoids a recursive call stack overflow on a large single island.

## Variations

- Record each flood's size to find the largest island.
- Leave the grid unchanged by maintaining a separate set of visited coordinates.
- Count islands under eight-directional connectivity instead.

=== card | 1091
time: 30 min

## The problem

In a square binary grid, find the minimum number of cells in a route from the upper-left cell to the lower-right cell. A route may use any of eight neighbouring directions but may visit only zero-valued cells. Return `-1` if no route exists. For a single open cell, the answer is 1, not 0.

## Constraints and what they imply

The grid is nonempty and square; both endpoints must be open. Each move has the same cost and there are at most eight outgoing moves per cell. Therefore weighted shortest-path machinery is unnecessary. Distance counts cells including the start, so it is one larger than the number of moves.

The search permits a diagonal step whenever its destination is open; it does not require the two adjacent orthogonal cells to be open. That detail matters when the start is surrounded by blocked horizontal and vertical neighbours but has an open diagonal exit.

## Brute force

Enumerate all simple valid paths from start to finish using backtracking and take the shortest. Even a small open grid can have exponentially many simple paths, and storing the current path takes O(n²) space. A visited mark local to each candidate is not enough to avoid repeated exploration across different candidates.

## The insight

Use BFS with the start at distance 1. Its FIFO queue expands states in nondecreasing distance. When an open neighbour is first enqueued, its distance is one more than the current distance, and no shorter route can be found later: that route's predecessor would have been expanded earlier. Marking at enqueue makes each cell enter once. The first removal of the destination therefore gives the minimum number of cells.

## Optimal solution, traced

```steps
grid = [[0, 1, 0], [1, 0, 0], [1, 1, 0]]
    queue [(0, 0, 1)]
---
From (0, 0), the open diagonal (1, 1) is discovered at distance 2
    queue [(1, 1, 2)]
---
(2, 2) is reached from (1, 1) at distance 3
    return {{3}}
```

## Code

```python
from collections import deque

def shortest_path_binary_matrix(grid):
    n = len(grid)
    if grid[0][0] or grid[n - 1][n - 1]:
        return -1
    queue = deque([(0, 0, 1)])
    seen = {(0, 0)}
    while queue:
        r, c, distance = queue.popleft()
        if (r, c) == (n - 1, n - 1):
            return distance
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if (0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0
                        and (nr, nc) not in seen):
                    seen.add((nr, nc))
                    queue.append((nr, nc, distance + 1))
    return -1
```

## Complexity

There are n² cells and at most eight checks for each expanded cell, so time and auxiliary space are O(n²). The grid is not modified; the seen set and queue hold the search state.

## Mistakes and edge cases

- Reject blocked start or finish before starting the search.
- Count the starting cell and include diagonal moves.
- Mark cells on enqueue to prevent several parents from queuing the same cell.
- A disconnected open destination must still return `-1`.

## Variations

- Record predecessors and return the actual shortest route.
- If moves have unequal nonnegative costs, replace BFS with Dijkstra's algorithm.
- For four-directional movement remove the diagonal offsets.

=== card | 994
time: 30 min

## The problem

In a rectangular grid, `0` denotes an empty cell, `1` a fresh item and `2` a rotten item. Each minute every rotten item causes its fresh horizontal or vertical neighbours to rot simultaneously. Return the earliest minute when no fresh item remains, or `-1` if some fresh item never rots.

## Constraints and what they imply

The nonempty grid may have several initial sources, none, or no fresh items. Effects spread through adjacent cells, not diagonally and not through empty cells. Because all sources act at once and every step costs one minute, the time for a cell is its shortest distance from any initial rotten cell through occupied cells. The code mutates the grid.

An unreachable fresh cell invalidates the whole result even if other fresh cells did rot.

## Brute force

Make a copy of the grid at the start of each minute and scan every cell to decide which fresh neighbours will change for the next minute. With at most O(mn) productive minutes and O(mn) work per scan, this costs O((mn)²) time and O(mn) space. The snapshot is important: letting newly rotten cells spread immediately in the same scan would produce an incorrect time.

## The insight

Start a single BFS with every initial rotten cell at time zero. All earlier-time cells are processed before later-time cells, so the first rot of a fresh neighbour is its earliest possible time from any source. Mark it rotten when enqueued, decrement the number of fresh cells, and assign its parent time plus one. If the queue empties with fresh cells remaining, no occupied route from any source can reach them.

## Optimal solution, traced

```steps
grid = [[2, 1, 1], [1, 1, 0]]
    sources [(0, 0)] at minute 0; fresh 4
---
At minute 1: (0, 1), (1, 0) rot
    fresh 2
---
At minute 2: (0, 2), (1, 1) rot
    fresh 0; return {{2}}
```

## Code

```python
from collections import deque

def oranges_rotting(grid):
    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c, 0))
            elif grid[r][c] == 1:
                fresh += 1
    elapsed = 0
    while queue:
        r, c, minute = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                elapsed = minute + 1
                queue.append((nr, nc, elapsed))
    return elapsed if fresh == 0 else -1
```

## Complexity

The initial scan and the search both take O(mn) time. Each cell is enqueued at most once and the queue can occupy O(mn) auxiliary space.

## Mistakes and edge cases

- Seed every initial source before starting; separate searches do not model simultaneous spread efficiently.
- No fresh items means zero minutes, even when the queue is empty.
- A fresh region isolated by empty cells produces `-1`.
- Update a cell before enqueueing so two sources do not count it twice.

## Variations

- Return each cell's earliest rot time instead of only the final minute.
- Use weighted edges and multi-source Dijkstra if transmission times vary.
- Stop after a fixed number of minutes and report the remaining fresh cells.

=== card | 417
time: 35 min

## The problem

Each cell in a rectangular height map can send water to a horizontally or vertically adjacent cell of no greater height. One ocean touches the top and left edges, the other the bottom and right edges. Return all coordinates from which water can reach both oceans, in any order. A border cell can reach its adjacent ocean without moving to another cell.

## Constraints and what they imply

The height matrix is nonempty and rectangular. Equal heights allow movement in both directions. Many starting cells may share long drainage paths, so searching separately from every cell repeats work. Both oceans can touch the same cell, especially in a one-row or one-column grid; duplicates in border seeds must not cause duplicate output.

Water may take different routes to the two oceans; the routes do not need to be disjoint or to have the same length. Reaching an edge of the relevant ocean suffices, without traversing any additional cell representing the ocean itself.

## Brute force

For each of the `mn` cells, run a downhill search to see which borders are reachable. A search can inspect O(mn) cells, yielding O((mn)²) time and O(mn) temporary space. It answers the right question but repeatedly traverses the same reachable regions.

## The insight

Reverse every possible water edge. From an ocean border, move to a neighbour only if that neighbour is at least as high as the current cell. A reversed path from a border to a cell corresponds exactly to a valid downhill path from that cell to that border. Perform a multi-source traversal from each ocean's borders and intersect the two reached sets. This equivalence proves both inclusion directions, even across plateaus and around cycles.

## Optimal solution, traced

```steps
heights = [[1, 2], [4, 3]]
    top/left seeds {(0, 0), (0, 1), (1, 0)}
    bottom/right seeds {(1, 0), (1, 1), (0, 1)}
---
From the first ocean, (1, 1) is reachable uphill from (0, 1)
    first reach set contains all four cells
---
The second ocean cannot climb from its seeds to height 1
    intersection {{[(0, 1), (1, 0), (1, 1)]}}
```

## Code

```python
def pacific_atlantic(heights):
    rows, cols = len(heights), len(heights[0])

    def reach(seeds):
        seen = set(seeds)
        stack = list(seen)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols
                        and (nr, nc) not in seen
                        and heights[nr][nc] >= heights[r][c]):
                    seen.add((nr, nc))
                    stack.append((nr, nc))
        return seen

    first = [(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)]
    second = [(rows - 1, c) for c in range(cols)] + [(r, cols - 1) for r in range(rows)]
    both = reach(first) & reach(second)
    return [(r, c) for r in range(rows) for c in range(cols) if (r, c) in both]
```

## Complexity

Each search visits at most mn cells and examines four neighbours, taking O(mn) time and space. The final row-major scan and the output each cost at most O(mn), so the total bounds remain O(mn) time and space.

## Mistakes and edge cases

- Reverse flow climbs to equal or higher neighbours, not lower ones.
- Use `>=`, not `>`, to include level paths.
- Include all four borders, and deduplicate corners and overlapping ocean borders.
- A single cell is adjacent to both oceans and must be returned.

## Variations

- Return cells reaching either ocean by taking a union instead of an intersection.
- Add more destinations and intersect one reverse-reachability set per destination.
- Track one successor in each reverse search to reconstruct valid drainage paths.

=== card | 752
time: 30 min

## The problem

A lock has four decimal wheels, initially showing `"0000"`. One move turns exactly one wheel one position forward or backward, wrapping between 0 and 9. Certain combinations are forbidden and cannot be entered. Find the fewest moves to a given target, or return `-1` when no legal route exists.

## Constraints and what they imply

Every combination is a four-character digit string, including leading zeroes. There are exactly 10,000 states and each has eight possible one-turn neighbours. All moves have equal cost, and a forbidden initial state prevents the search from starting, even when it equals the target.

The target may be blocked, isolated by blocked neighbours, or equal to the initial state. The first two cases fail, while the last needs zero turns provided the start is allowed. Keeping combinations as strings preserves the leading zeroes necessary to represent a particular wheel configuration.

## Brute force

Enumerate sequences of wheel turns of increasing length and simulate each, rejecting forbidden combinations. Without deduplicating states, many sequences lead back to the same combination and the branching factor is eight. This can take exponential time in the path length and may continue indefinitely unless an explicit bound is imposed.

## The insight

Treat combinations as graph vertices and turns as edges. BFS explores legal states in increasing number of moves. A state discovered for the first time has a shortest route: every shorter candidate would have an earlier-layer predecessor, which BFS already expanded. Record states when enqueued to keep each combination from being explored repeatedly. Forbidden combinations are excluded from the start.

## Optimal solution, traced

```steps
deadends = [], target = "0009"
    queue [("0000", 0)]
---
Turn the last wheel backward, wrapping 0 to 9
    enqueue ("0009", 1)
---
The target is removed at distance 1
    return {{1}}
```

## Code

```python
from collections import deque

def open_lock(deadends, target):
    blocked = set(deadends)
    if "0000" in blocked:
        return -1
    queue = deque([("0000", 0)])
    seen = {"0000"}
    while queue:
        state, distance = queue.popleft()
        if state == target:
            return distance
        for i in range(4):
            digit = int(state[i])
            for step in (-1, 1):
                next_digit = str((digit + step) % 10)
                neighbor = state[:i] + next_digit + state[i + 1:]
                if neighbor not in blocked and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, distance + 1))
    return -1
```

## Complexity

At most 10⁴ states are visited, with eight constant-length neighbour constructions each. Time is O(10⁴ + D) and space is O(10⁴ + D), where D is the number of forbidden entries used to build the set.

## Mistakes and edge cases

- Check a forbidden start before accepting a target equal to the start.
- A forbidden target cannot be reached because it is never enqueued.
- Use modulo for both directions and retain all four digits.
- Mark on enqueue rather than on removal to avoid duplicate work.

## Variations

- Store predecessors to return a shortest sequence of combinations.
- Use bidirectional BFS, expanding one frontier from each endpoint.
- Generalize to `k` wheels with `b` symbols, yielding at most b^k states.

=== card | 785
time: 30 min

## The problem

An undirected graph is given as adjacency lists, with vertices numbered from zero. Determine whether its vertices can be split into two groups such that every edge connects different groups. Isolated vertices can go in either group. A triangle cannot be split this way, while an even cycle can.

## Constraints and what they imply

The adjacency lists describe an undirected graph and can include disconnected components. A self-loop, if present, makes the condition impossible because its endpoints are the same vertex. The graph can be traversed in O(V + E) time, so testing all possible assignments is unnecessary.

Within one connected component, picking the opposite starting colour merely swaps the two groups; it cannot repair a conflict. Each disconnected component can make that arbitrary choice independently. An empty graph is also bipartite because there are no edges that could violate the condition.

## Brute force

Assign each of V vertices one of two colours, and for each complete assignment check all edges. At most 2^V assignments and O(V + E) work per check yield O(2^V(V + E)) time. The search uses O(V) space for an assignment. The issue is trying assignments that are already forced by previously coloured neighbours.

## The insight

Choose any colour for a new component's first vertex. Every edge forces its other endpoint to have the opposite colour; propagate this rule using a stack. If an edge joins equal colours, the current assignment violates a necessary condition, and the forced parity of paths means no valid colouring exists for that component. If no conflict appears, every examined edge connects opposite colours, so the resulting assignment itself proves success. Repeat from each still-uncoloured vertex.

## Optimal solution, traced

```steps
graph = [[1, 2], [0, 2], [0, 1]]
    colour vertex 0 as 0; its neighbours 1 and 2 as 1
---
Expand vertex 2 and inspect edge 2-1
    both endpoints have colour 1
---
No two-group assignment can satisfy this triangle
    return {{False}}
```

## Code

```python
def is_bipartite(graph):
    colors = [-1] * len(graph)
    for start in range(len(graph)):
        if colors[start] != -1:
            continue
        colors[start] = 0
        stack = [start]
        while stack:
            u = stack.pop()
            for v in graph[u]:
                if colors[v] == -1:
                    colors[v] = 1 - colors[u]
                    stack.append(v)
                elif colors[v] == colors[u]:
                    return False
    return True
```

## Complexity

Each vertex is coloured once and each adjacency entry is inspected once: O(V + E) time. Colours and the stack occupy O(V) auxiliary space.

## Mistakes and edge cases

- Start a traversal in every uncoloured component, not just at vertex zero.
- Compare against previously coloured neighbours instead of blindly overwriting them.
- An isolated vertex is valid, whereas a self-loop conflicts immediately.
- Colour at discovery to avoid repeatedly pushing a vertex.

## Variations

- Return the two vertex groups when the colouring succeeds.
- Extract an odd cycle as a certificate when a conflict is found.
- Check whether a set of pairwise inequality constraints is consistent.

=== card | 210
time: 30 min

## The problem

Courses are labelled `0..n-1`. Each pair `[course, prerequisite]` means the prerequisite must appear before the course. Return any ordering containing every course exactly once and respecting all pairs, or an empty list if no such order exists. With `[[1, 0], [2, 0]]`, both `[0, 1, 2]` and `[0, 2, 1]` work.

## Constraints and what they imply

The course count can be large relative to the number of pairs, and the dependencies need not connect all courses. A course can have several prerequisites, and there may be a directed cycle. Input pairs point opposite to the direction of scheduling influence: completing the prerequisite unlocks the course.

Courses with no relation still belong in the output, even if they can appear anywhere. A prerequisite cycle cannot be resolved by starting with an outside course: every member of that cycle still requires another member to appear earlier.

## Brute force

Try each of the `n!` permutations and verify that every prerequisite precedes its course. Checking a candidate can take O(n + E) time with a position table, so the worst-case time is O(n!(n + E)); storing one candidate and its positions uses O(n) space. Most permutations are rejected because a single prerequisite is out of order.

## The insight

Build edges from prerequisite to dependent and count the unsatisfied incoming edges of each course. Initially every zero-indegree course is eligible. When one is emitted, remove its outgoing edges and enqueue any dependent whose remaining count falls to zero. The invariant is that the count is exactly the number of prerequisite edges not yet removed. Thus every emitted course follows its prerequisites. If the queue empties before all courses appear, the remaining finite directed graph has no zero-indegree vertex and contains a cycle, making a complete ordering impossible.

## Optimal solution, traced

```steps
n = 3, prerequisites = [[1, 0], [2, 0]]
    indegrees [0, 1, 1]; queue [0]
---
Emit 0 and remove 0->1 and 0->2
    indegrees [0, 0, 0]; queue [1, 2]
---
Emit 1 then 2
    order {{[0, 1, 2]}}
```

## Code

```python
from collections import deque

def find_order(n, prerequisites):
    outgoing = [[] for _ in range(n)]
    indegree = [0] * n
    for course, prerequisite in prerequisites:
        outgoing[prerequisite].append(course)
        indegree[course] += 1
    queue = deque(i for i in range(n) if indegree[i] == 0)
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in outgoing[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return order if len(order) == n else []
```

## Complexity

Constructing the graph and processing each vertex and edge once takes O(n + E) time and O(n + E) space, including the output and adjacency lists.

## Mistakes and edge cases

- Reverse each input pair when building the outgoing adjacency list.
- Check the output length: a partial order is not a valid complete answer.
- Include independent courses, which start with indegree zero.
- If duplicate pairs are supplied, count and remove every occurrence consistently.

## Variations

- Use a min-heap of available courses to choose the lexicographically smallest order.
- Return only whether completion is possible by comparing the processed count to `n`.
- Add durations and compute earliest completion times while processing the DAG.

=== card | 802
time: 35 min

## The problem

In a directed graph, a terminal vertex has no outgoing edges. A vertex is safe if every possible route starting there eventually reaches a terminal vertex. Return the safe vertices in increasing order. A vertex on a directed cycle is unsafe, and so is any vertex that can reach that cycle.

## Constraints and what they imply

The input is an adjacency list with vertex labels `0..n-1`; disconnected regions are possible. Safety depends on *all* outgoing choices, not merely the existence of one route to a terminal. A self-loop is a cycle. The result order is part of the contract, so a traversal's discovery order alone is insufficient.

In a finite graph an infinite route exists exactly when some reachable directed cycle can be followed repeatedly. Consequently a path that can choose either a terminal or a cycle is unsafe, because the adversarial choice can keep following the cycle forever.

## Brute force

For each starting vertex, enumerate all possible paths until finding a cycle or confirming termination. Even in an acyclic graph the number of paths can be exponential due to branching and reconvergence. A separate cycle-detection traversal from every start is a more controlled O(V(V + E)) alternative, but still repeats work across starts; it uses O(V) search space.

## The insight

Terminal vertices are safe immediately. A nonterminal becomes safe once all its successors have been established safe. Reverse the edges and maintain each vertex's number of unresolved outgoing edges. Removing a known-safe successor decreases that number for each predecessor; when the count reaches zero, the predecessor is also safe. By induction every removed vertex is safe. Every vertex left behind has at least one outgoing edge to another remaining vertex, so following remaining edges eventually repeats a vertex and provides an infinite route. Thus all remaining vertices are unsafe.

## Optimal solution, traced

```steps
graph = [[1], [2], [], [3]]
    outdegrees [1, 1, 0, 1]; queue [2]
---
Remove 2, then 1, then 0 as their last successors are resolved
    safe flags [True, True, True, False]
---
Vertex 3 retains its self-loop
    return {{[0, 1, 2]}}
```

## Code

```python
from collections import deque

def eventual_safe_nodes(graph):
    n = len(graph)
    reverse = [[] for _ in range(n)]
    remaining = [len(neighbors) for neighbors in graph]
    for u, neighbors in enumerate(graph):
        for v in neighbors:
            reverse[v].append(u)
    queue = deque(i for i in range(n) if remaining[i] == 0)
    safe = [False] * n
    while queue:
        v = queue.popleft()
        safe[v] = True
        for u in reverse[v]:
            remaining[u] -= 1
            if remaining[u] == 0:
                queue.append(u)
    return [i for i in range(n) if safe[i]]
```

## Complexity

Each vertex and adjacency entry is processed at most once, and the final ordered scan is O(V). Time and space are O(V + E), including reversed edges.

## Mistakes and edge cases

- One safe successor does not make a vertex safe if another leads to a cycle.
- Use outdegree in the original graph, not indegree.
- Scan labels in ascending order for the requested result.
- Duplicate edges, if present, must both count and be removed.

## Variations

- Return unsafe vertices instead by complementing the safe flags.
- Identify strongly connected components to describe the actual cyclic regions.
- Solve the same problem with three-colour DFS and memoized safety states.

=== card | 127
time: 45 min

## The problem

You are given a starting word, a different ending word, and a dictionary of words of the same length. A transformation changes exactly one character, and every word after the starting word must belong to the dictionary. Return the smallest number of words in a valid chain, counting both endpoints; return zero if no chain exists. For example, `"hit"` can reach `"cog"` through `"hot"`, `"dot"`, `"dog"`, and `"cog"`, giving five words.

The start is allowed to be absent from the dictionary. The end is not: reaching an unlisted end is invalid even if it differs from a dictionary word by one character. Reusing a word cannot improve a shortest chain, so a shortest solution does not need a cycle.

## Constraints and what they imply

All words consist of lowercase English letters, have the same positive length L, and the dictionary contains N unique words. The start and end are distinct under the problem's contract. The input describes a potentially dense implicit graph: two words have an edge when exactly one position differs. Constructing every pair of edges explicitly can require O(N²L) comparisons and substantial space. Instead, group potential neighbours by the positions they agree on.

The special marker `*` is not a lowercase letter, so substituting it for one character creates an unambiguous pattern. Words with the same pattern at a position agree everywhere else. A pair of distinct dictionary words sharing that pattern differs in exactly one character. The code also includes the start in the index, since it is a legal starting vertex even when not listed.

## Brute force

One approach is to enumerate simple transformation chains by backtracking, check each possible next word against the current word, and retain the shortest valid chain. The number of chains can be exponential or worse as the dictionary grows, despite using only O(N) space for a path and visited set. Even a BFS that compares a dequeued word with every dictionary word spends O(N²L) time in the worst case, repeatedly comparing pairs which cannot be neighbours.

## The insight

Create L wildcard patterns per indexed word, placing the word in the bucket for each pattern. During BFS, the buckets of the current word list all its one-character neighbours. Assign each newly found word the current distance plus one, and mark it as visited at discovery. BFS processes words in nondecreasing chain length, so the first time the end is removed its length is minimal.

After processing a pattern, remove its bucket. This is safe because the first word that expands a bucket has minimum BFS distance among all words that could expand that bucket. Every undiscovered word in the bucket is then enqueued with the best possible distance through it; any later expansion of that same bucket could only offer an equal or longer route. Clearing buckets avoids repeatedly iterating a large group of mutually adjacent words. Visited words cannot hide a shorter route: their first discovery already came from a predecessor at no greater distance.

## Optimal solution, traced

```steps
begin = "hit", end = "cog"
words = ["hot", "dot", "dog", "cog"]
    queue [("hit", 1)]
---
Pattern h*t joins hit to hot; then *ot joins hot to dot
    distances hit 1, hot 2, dot 3
---
Pattern do* joins dot to dog, then *og joins dog to cog
    distances dog 4, cog 5; return {{5}}
```

In this example each displayed pattern is consumed the first time it is expanded. The final length counts five words, while the number of character changes is four. The trace omits empty buckets, which do not affect the queue.

## Code

```python
from collections import defaultdict, deque

def ladder_length(begin, end, word_list):
    words = set(word_list)
    if end not in words:
        return 0
    words.add(begin)
    length = len(begin)
    buckets = defaultdict(list)
    for word in words:
        for i in range(length):
            pattern = word[:i] + "*" + word[i + 1:]
            buckets[pattern].append(word)
    queue = deque([(begin, 1)])
    seen = {begin}
    while queue:
        word, distance = queue.popleft()
        if word == end:
            return distance
        for i in range(length):
            pattern = word[:i] + "*" + word[i + 1:]
            for neighbor in buckets.pop(pattern, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, distance + 1))
    return 0
```

## Complexity

Let W be the number of distinct indexed words, at most N + 1. There are WL bucket memberships. Creating each length-L pattern using Python string slices and concatenation costs O(L), so preprocessing and searching cost O(WL²) time. Clearing each bucket ensures its memberships are scanned only once in total, O(WL), rather than once per word in that bucket. The pattern keys can occupy O(WL²) characters, and the membership lists, queue, and visited set use O(WL + W) additional references. Thus O(WL²) is a safe total auxiliary space bound for Python strings.

## Mistakes and edge cases

- Check the end is in the dictionary before searching. A reachable-looking unlisted target is not allowed.
- Count the start as length one; returning the number of edges is off by one.
- Include the start in the pattern index but do not require it in the dictionary.
- Mark discovered neighbours when enqueued and clear a bucket only after its full list has been considered.
- The code expects the stated lowercase, equal-length input. A wildcard already present in an input word would invalidate the bucket interpretation.
- If all possible first changes are missing, the queue empties and the answer is zero.

## Variations

- Record all shortest-path predecessors, then backtrack to enumerate every shortest transformation sequence.
- Use bidirectional BFS, carefully preserving distances from both ends, to reduce the explored region.
- Generate 26 substitutions per position instead of indexing wildcard buckets, and check membership in a set.

=== card | 2050
time: 45 min

## The problem

There are `n` courses labelled from 1 to `n`; course `i` takes `time[i-1]` months. Each pair `[a, b]` requires completing `a` before starting `b`. Any number of eligible courses may run simultaneously. Return the minimum number of months by which every course can be completed.

For example, with durations `[3, 2, 5]` and prerequisites `[[1, 3], [2, 3]]`, courses 1 and 2 can start together. Course 3 must wait until month 3 and then needs five months, so all work completes at month 8. Summing all durations would incorrectly serialize independent work.

## Constraints and what they imply

The course count is positive, durations are positive integers, labels are one-based, and the given prerequisite graph is a DAG. There is no limit on how many courses can run in parallel. Thus a course's earliest start is controlled by its latest-finishing prerequisite, not by the sum of prerequisite times. A disconnected course still contributes to the final completion time.

A DAG admits a topological ordering: for every edge, its source appears before its destination. Calculating finish times in this order means every prerequisite value is available when it is needed. There can be many valid orders, but the earliest finish of each course and the final answer are independent of which order is used.

## Brute force

One direct but expensive method enumerates all directed paths, totals the durations along each path, and returns the largest total. Every chain is a lower bound because its courses must run sequentially. In a branching and reconverging DAG the number of paths can be exponential, so listing them can require exponential time even though the input graph is small. A depth-first enumeration uses O(n) stack space for one current path, but repeatedly evaluates shared suffixes.

An alternative exhaustive scheduler could try possible execution orders, but this introduces needless choices. Starting an available course earlier never delays another course when resources are unlimited, so no search over schedules is needed. The useful quantity is the longest weighted prerequisite path ending at each course.

## The insight

For each course `v`, let `finish[v]` be its earliest completion time. If it has no prerequisites, it can finish after its own duration. Otherwise, it must wait for *all* immediate prerequisites, so
`finish[v] = duration[v] + max(finish[u])` over all edges `u -> v`. Process this recurrence using Kahn's topological algorithm.

Maintain a remaining-indegree count and a `ready` value: the largest finish time among prerequisites processed so far. Initially courses with zero indegree enter the queue, and each ready value is zero. When popping `u`, its finish is `ready[u] + duration[u]`. Propagate this value to every dependent with a maximum update, decrement its indegree, and enqueue it when the last incoming edge has been processed.

The invariant is that `ready[v]` is the maximum finish among already removed predecessors. When `v` enters the queue, all its predecessors have been removed, so the invariant gives its exact earliest start. Induction over the queue order proves each computed finish is attainable by starting courses at their earliest starts and necessary because no course can begin before any prerequisite ends. The maximum finish over all vertices is therefore both achievable and a lower bound for finishing everything. It is the weighted critical-path length.

## Optimal solution, traced

```steps
n = 3, relations = [[1, 3], [2, 3]], time = [3, 2, 5]
    ready [0, 0, 0], indegree [0, 0, 2], queue [1, 2]
---
Finish 1 at 3 and 2 at 2; propagate their maximum to course 3
    ready [0, 0, 3], indegree [0, 0, 0], queue [3]
---
Finish course 3 at 3 + 5 = 8
    maximum finish {{8}}
```

The two prerequisites run concurrently; the smaller completion time does not delay course 3 past the larger one. The queue need not process 1 before 2: the maximum update is independent of that order.

## Code

```python
from collections import deque

def minimum_time(n, relations, time):
    outgoing = [[] for _ in range(n)]
    indegree = [0] * n
    for a, b in relations:
        outgoing[a - 1].append(b - 1)
        indegree[b - 1] += 1
    ready = [0] * n
    queue = deque(i for i in range(n) if indegree[i] == 0)
    answer = 0
    while queue:
        u = queue.popleft()
        finish = ready[u] + time[u]
        answer = max(answer, finish)
        for v in outgoing[u]:
            ready[v] = max(ready[v], finish)
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return answer
```

## Complexity

Building adjacency lists and indegrees costs O(n + E), where E is the number of prerequisite pairs. Every course is queued once, and each relation is processed once, giving O(n + E) total time and O(n + E) auxiliary space. Python integers grow as necessary for large duration sums. The algorithm relies on the promised DAG; it does not report cycles.

## Mistakes and edge cases

- Convert one-based relation labels to zero-based indices for the duration array.
- Use a maximum, not a sum, when merging predecessor finish times.
- Enqueue a dependent only after *all* of its incoming edges have been handled.
- With no relations the answer is the largest individual duration, not their sum.
- A long chain gives the sum of that chain's durations; a disconnected longer chain can determine the answer.
- If adapting to arbitrary directed graphs, count processed vertices and explicitly report a cycle instead of returning a partial result.

## Variations

- Store the maximizing predecessor for each course to reconstruct one critical path.
- Return every course's earliest start and finish rather than only the makespan.
- Add a limit on simultaneous courses: the unlimited-resource critical-path recurrence alone no longer solves the scheduling problem.
