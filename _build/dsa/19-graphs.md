---
key: graphs
name: Graph modelling and traversal
stage: network
summary: Turn a problem into vertices and edges, then answer it with BFS, DFS or a topological sort: shortest unweighted paths, components, grids, puzzle states, cycles, two-colourings and dependency orders.
why: Most hidden structure in real problems is a graph: cells of a map, states of a puzzle, courses and their prerequisites, packages and their dependencies, people and their friendships. Once you can say what the vertices and edges are, three linear-time traversals (breadth-first, depth-first and topological order) answer a remarkable share of questions: is it reachable, in how many steps, how many groups are there, is there a cycle, in what order can it run. The same code runs inside build tools, package managers, garbage collectors and database deadlock detectors, and this stage's project, a small build system, is built from it.
outcomes:
- Model a statement as a graph: name the vertices, the edges and their direction, and decide whether to build the graph or generate neighbours on the fly
- Write BFS with a queue and parent pointers from memory and explain why it returns shortest paths in unweighted graphs
- Count components and flood-fill regions with recursive and iterative DFS, staying inside Python's recursion limit
- Search grids and puzzle state spaces, including multi-source BFS and states that carry extra information
- Detect cycles with white, grey and black colours, and two-colour a bipartite graph
- Produce a topological order with Kahn's algorithm or DFS finishing times, report impossible orders, and compute critical paths on a DAG
cues:
- Things with pairwise relationships (friends, roads, prerequisites, links), even when the word "graph" never appears
- "Minimum number of moves, steps or transformations" where every move costs the same
- A grid of cells you can walk between, regions to count, or something spreading from several places at once
- "Must happen before", prerequisites, build order, or "is it possible to finish everything"
traps:
- Marking a vertex visited when you dequeue it instead of when you enqueue it, so it enters the queue many times
- Getting edge direction backwards when modelling prerequisites: a pair [course, prerequisite] means prerequisite -> course
- Recursive DFS on a large grid or a long chain: Python stops at 1,000 nested calls by default
- Using a single "visited" flag for directed cycle detection, which mistakes a finished vertex for a cycle
- Using BFS when edges have different weights (that needs Dijkstra, in the shortest paths module)
systems:
- Build tools: make brings prerequisites up to date before their targets, Ninja runs independent build edges in parallel, and Python's graphlib.TopologicalSorter exposes the same ready-set loop (prepare, get_ready, done)
- Package installers: pip computes an installation order as a topological ordering of the dependency graph; resolvers such as uv's PubGrub add backtracking search to choose versions first
- Git history is a DAG of commits; git merge-base walks ancestors to find the best common ancestor for a three-way merge
- Databases detect deadlocks as cycles in a graph of which transaction waits for which (PostgreSQL runs the check after deadlock_timeout)
further:
- Chapter · 40 min | Erickson, Algorithms ch. 5: whatever-first search, variants and flood fill (PDF pages 13-20) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/05-graphs.pdf#page=13
- Chapter · 30 min | Erickson, Algorithms ch. 6: preorder and postorder, detecting cycles, topological sort (PDF pages 3-12) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/06-dfs.pdf#page=3
- Article · 15 min | USACO Guide: Graph traversal, the BFS section with Python code | https://usaco.guide/silver/graph-traversal#bfs
- Visualisation · 10 min | VisuAlgo: Graph traversal, run DFS and BFS on the example graphs | https://visualgo.net/en/dfsbfs
bank: graphs topo
---

=== primer | How do you turn a problem into a graph, and how should you store it? | 15 min
goal: Name the vertices, edges, direction and weights hidden in a statement, store them as adjacency lists, a matrix or a neighbour function, and pick the traversal the question needs
tag: graphs-model | Modelling a problem as a graph
link: Erickson, Algorithms ch. 5 (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/05-graphs.pdf#page=6 | 20 min: sections 5.2 'Representations and Examples' and 5.3 'Data Structures' (PDF pages 6-12), including the comparison of adjacency lists and matrices
practice: 1971

> [!key]
> A graph is a set of **vertices** (things) and **edges** (relationships between pairs of things). Modelling is the real work: decide what a vertex is, when two vertices are joined, whether an edge has a direction or a cost, and what the question asks. Store the graph as **adjacency lists** unless it is dense or tiny, and do not build it at all when you can generate a vertex's neighbours on the fly (grids, puzzles).

## Intuition

Picture a rail map. Stations are vertices and the lines between neighbouring stations are edges. "Can I get from Leeds to Bath?" is reachability. "With the fewest stops?" is a shortest path. "Which stations are cut off after a storm?" is connected components. None of those questions cares how the map is drawn, only who is joined to whom.

Most problems never say "graph". A maze is a graph of open cells joined by single steps. A word game is a graph of words joined when they differ by one letter. A course catalogue is a graph of courses with an arrow from each prerequisite to the course that needs it. A bicycle lock is a graph of the 10,000 combinations joined by single wheel turns. Spotting the graph is usually most of the solution.

## How it works

### Four modelling questions

1. **What is a vertex?** The smallest piece of state the question cares about: a cell, a word, a course, a combination.
2. **When are two vertices joined?** That rule is the edge set: "one step apart", "one letter different", "must come before".
3. **Direction and cost?** "A must come before B" is directed (A -> B). Friendship is undirected. Prices or distances are weights; equal costs mean an unweighted graph.
4. **What is asked?** The question picks the algorithm:

| Statement | Vertices | Edges | Question | Tool |
|---|---|---|---|---|
| Can computer 0 reach computer 5? | computers | cables, undirected | reachable? | BFS or DFS |
| Fewest steps through a maze | open cells | moves to a neighbouring cell | fewest edges | BFS |
| How many islands? | land cells | sideways neighbours | count components | DFS or BFS |
| Can every course be taken? | courses | prerequisite -> course | does an order exist? | topological sort |
| Fewest turns to open a lock | 4-digit combinations | one wheel moved one notch | fewest edges | BFS over states |
| Cheapest flight route | airports | flights with prices | least total weight | Dijkstra (shortest paths module) |
| Cheapest way to cable every office | offices | possible cables with costs | least total to connect all | spanning tree (union-find module) |

### Representations

- **Adjacency lists**: `adj[u]` is the list of u's neighbours. An undirected edge is stored twice, once in each list.
- **Adjacency matrix**: `m[u][v]` is True when u and v are joined. Good for dense graphs and constant-time edge tests.
- **Edge list**: the raw pairs, as most inputs arrive. Good for sorting edges by weight (Kruskal) and little else.
- **Implicit graph**: a function that yields the neighbours of a vertex. Grids and puzzles are never built; you compute neighbours when you need them.

| | Adjacency lists | Matrix | Edge list | Neighbour function |
|---|---|---|---|---|
| Space | O(V + E) | O(V^2) | O(E) | O(1) plus your visited set |
| List the neighbours of u | O(deg u) | O(V) | O(E) | O(deg u) |
| Is (u, v) an edge? | O(deg u), O(1) with sets | O(1) | O(E) | compute it |
| Use for | almost everything | dense graphs, V up to a few thousand | sorting edges, input | grids, puzzles, huge state spaces |

In Python, vertices numbered 0..n-1 get a list of lists. Arbitrary labels (names, tuples) get a `defaultdict(list)`, or you map each label to an integer once and use lists from then on, which is faster and smaller. Use sets of neighbours when you need fast edge tests or must ignore duplicate edges.

## Cost

Building adjacency lists appends each edge once (twice if undirected): O(V + E) time and space. A traversal then visits each vertex once and scans each adjacency list once, so it costs O(V + E) in total, because the lengths of all the lists add up to E (or 2E). With a matrix, finding the neighbours of one vertex scans a whole row of V cells, so a traversal costs O(V^2) even when the graph has few edges.

That difference decides feasibility. With V = 100,000 and E = 200,000, adjacency lists hold 400,000 entries; a matrix would need 10^10 cells. For implicit graphs, count states and moves instead: the lock has V = 10^4 combinations and 8 moves from each, so E = 8 * 10^4 and a BFS is instant.

## When to use it

Model as a graph whenever the input describes things plus a rule for which pairs are related, and the question is about reachability, distance in steps, groups, cycles or order. Watch for near misses:

- A tree given as node objects is already a graph with no cycles: recurse on it directly, no visited set needed.
- A grid where you may only move right or down is a DAG; counting or optimising paths there is dynamic programming, not BFS.
- Different edge costs need Dijkstra; edges that only ever get added, with "are these connected?" queries in between, suit union-find.

## Worked trace

Build directed adjacency lists and in-degrees for four courses, given pairs `[course, prerequisite]`: `[[1, 0], [2, 0], [3, 1], [3, 2]]`. The in-degree of a vertex (how many edges point into it) will drive topological sorting later.

```steps
Pairs are [course, prerequisite]: the edge must point from the prerequisite to the course
    pairs   [1,0]  [2,0]  [3,1]  [3,2]
    adj     0: []   1: []   2: []   3: []
    indeg   0 0 0 0
---
[1, 0]: course 0 comes before course 1, so add the edge 0 -> 1
    adj     0: [{{1}}]   1: []   2: []   3: []
    indeg   0 {{1}} 0 0
---
[2, 0]: edge 0 -> 2
    adj     0: [1, {{2}}]   1: []   2: []   3: []
    indeg   0 1 {{1}} 0
---
[3, 1]: edge 1 -> 3
    adj     0: [1, 2]   1: [{{3}}]   2: []   3: []
    indeg   0 1 1 {{1}}
---
[3, 2]: edge 2 -> 3. Vertex 0 has in-degree 0: nothing must come before it
    adj     0: [1, 2]   1: [3]   2: [{{3}}]   3: []
    indeg   {{0}} 1 1 {{2}}
```

## Template

```python
from collections import defaultdict

def build_adj(n, edges, directed=False):
    """Adjacency lists for vertices 0..n-1 from (u, v) pairs."""
    adj = [[] for _ in range(n)]        # never [[]] * n: that is one shared list
    for u, v in edges:
        adj[u].append(v)
        if not directed:
            adj[v].append(u)
    return adj


def build_adj_labels(edges, directed=False):
    """Adjacency lists keyed by any hashable label (names, tuples, strings)."""
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        if not directed:
            adj[v].append(u)
    return adj


DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def grid_neighbours(grid, r, c):
    """Implicit graph: the open cells next to (r, c); '#' is a wall."""
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != '#':
            yield nr, nc
```

## Pitfalls

- **`[[]] * n`** creates n references to one list, so every vertex shares one neighbour list. Use a comprehension.
- **Backwards edges.** `[course, prerequisite]` is a pair, not an edge. Write the direction in a comment before coding.
- **Forgetting the reverse edge** for undirected input, so traversals miss half the graph.
- **defaultdict surprises.** Vertices with no edges never become keys, so `for u in adj` misses them; and merely reading `adj[x]` inserts x, which raises "dictionary changed size during iteration" inside a loop over `adj`.
- **1-based labels** (common on CSES): allocate `n + 1` lists or subtract one on input.
- **Parallel edges and self-loops** inflate degrees; use sets if the problem says they should count once.

## Check yourself

Q: Trace `build_adj(3, [(0, 1), (0, 2), (2, 1)], directed=True)`. What are the lists and the in-degrees?
A: `adj = [[1, 2], [], [1]]`. In-degrees are 0 for vertex 0, 2 for vertex 1 (from 0 and 2) and 1 for vertex 2.

Q: Why does a traversal cost O(V + E) with adjacency lists but O(V^2) with a matrix, even on the same sparse graph?
A: A traversal looks at the neighbours of every vertex once. With lists that work is the sum of the list lengths, which is E (2E undirected), plus O(1) per vertex. With a matrix, finding the neighbours of one vertex means reading its whole row of V cells, whether or not they are edges, so V rows cost V^2.

Q: A graph has 2,000 vertices and 1.5 million edges, and your algorithm asks "is u joined to v?" millions of times. Which representation?
A: An adjacency matrix: 4 million cells fit easily, the graph is dense (E is close to V^2 / 2 = 2 million), and each test is O(1). Lists would make each test O(deg u), hundreds of steps. A list of sets also gives O(1) average tests at higher memory per edge.

Q: A colleague writes `adj = [[]] * n` and then `adj[u].append(v)` for each edge. What does a BFS from vertex 0 then see?
A: Every `adj[i]` is the same list, so every vertex appears to be joined to every endpoint of every edge. BFS reaches vertices that are not connected to 0 and reports wrong distances.

## Lab

- **1971 Find if Path Exists in Graph.** Build undirected adjacency lists from the edge list, then run any traversal from `source`. Expected: O(V + E) time and space; for n = 6, edges `[[0,1],[1,2],[3,4],[4,5]]` and source 0, destination 2 gives `true` and destination 5 gives `false`.
- **Model it (no code).** A knight starts on a1 of a chessboard and wants to reach h8 in the fewest moves. Name the vertices, the edges and the algorithm. Expected: 64 vertices (squares), an edge for each legal knight move (336 ordered moves, so 168 undirected edges), BFS from a1; the answer is 6 moves.

> [!know]
> You now know how to read a statement as vertices and edges, choose a representation by its costs, and match the question to a traversal.

=== primer | How does BFS find the shortest path in an unweighted graph? | 15 min
goal: Write BFS with a queue, distances and parent pointers from memory, rebuild a path, and explain why the first discovery of a vertex is along a shortest path
tag: graphs-bfs | BFS shortest paths
link: cp-algorithms: Breadth-first search | https://cp-algorithms.com/graph/breadth-first-search.html#description-of-the-algorithm | 10 min: 'Description of the algorithm' (including restoring the path from parents), then skim the 'Applications of BFS' list below it
practice: 1971, 1091

> [!key]
> Breadth-first search explores in rings: the source, then everything one edge away, then everything two edges away. A first-in first-out queue keeps the rings in order, so the **first time you reach a vertex you have found a shortest path** to it (fewest edges). Set `dist[v]` and `parent[v]` **when you enqueue v**, never later, and each vertex enters the queue once: O(V + E) time.

## Intuition

Drop a stone in a pond. The ripple reaches every point at distance 1 before any point at distance 2. BFS is that ripple on a graph: your friends, then friends of friends, then the next ring. The ring a person first appears in is their degree of separation from you.

## How it works

1. Put the source in a queue with `dist[source] = 0`.
2. Pop the oldest vertex u. For each neighbour v that has no distance yet, set `dist[v] = dist[u] + 1` and `parent[v] = u`, and push v.
3. Repeat until the queue is empty. To rebuild the path to t, follow `parent` from t back to the source and reverse.

**Invariant:** the queue always holds vertices in non-decreasing order of distance, and at most two distances are present at once: some d at the front and d + 1 behind them. Popping a vertex at distance d only ever appends vertices at distance d + 1, so the order is kept.

**Why the first discovery is shortest.** Prove by induction on k that every vertex whose true distance is k gets `dist = k`, and that all of them are popped before any vertex at true distance k + 1. For k = 0 it is the source. Take a vertex v at true distance k + 1. Some neighbour w of v has true distance k, so w is popped before any distance-(k + 1) vertex, and when it is popped it discovers v if nobody has yet. Could something discover v earlier? Only a vertex popped earlier, which has true distance at most k; if its distance were less than k, v would be closer than k + 1. So v's discoverer is at distance exactly k and `dist[v] = k + 1`.

### Mark when you enqueue

If you mark a vertex visited only when you pop it, every neighbour that sees it before then pushes it again. On a complete graph of 1,000 vertices that makes 499,501 pushes instead of 1,000; on an open 100 x 100 grid, 19,801 instead of 10,000. Distances can still come out right if you skip repeats when popping, but time and memory balloon and parent pointers get overwritten. Mark at discovery and the problem disappears.

## Cost

Each vertex is pushed at most once (its distance is set on the push) and popped at most once: O(V) queue work, each O(1) with `collections.deque`. Each adjacency list is scanned once, when its vertex is popped, and the lengths sum to E (2E undirected). Total **O(V + E) time and O(V) extra space** for `dist`, `parent` and the queue. With `list.pop(0)` each pop shifts the whole list, which makes BFS O(V^2) on large graphs.

## When to use it

- Fewest edges, moves, hops or transformations, when every step costs the same.
- Anything by levels: "within k steps", "nearest first", "spread one ring per minute".
- Not with different edge weights: a path with more, cheaper edges can win, so you need Dijkstra (or 0-1 BFS when weights are only 0 and 1), both in the shortest paths module.
- For plain reachability or counting components, BFS and DFS are equally good; DFS is shorter to write recursively and gives post-order, BFS never hits a recursion limit.

## Worked trace

BFS from A on this graph (neighbours are scanned in alphabetical order):

```text
    A --- B --- E
    |     |     |
    C --- D --- F --- G
```

```steps
Start: A has distance 0 and is the only vertex in the queue
    queue   [A]
    dist    A=0
---
Pop A. B and C are new: label them 1, record parent A, enqueue
    queue   [{{B}}, {{C}}]
    dist    A=0  {{B=1}}  {{C=1}}
---
Pop B. A is labelled; D and E are new at distance 2
    queue   [C, {{D}}, {{E}}]
    dist    A=0  B=1  C=1  {{D=2}}  {{E=2}}
---
Pop C. A and D already have labels (D was marked when it was enqueued), so nothing is added
    queue   [D, E]
    dist    A=0  B=1  C=1  D=2  E=2
---
Pop D. F is new at distance 3, parent D
    queue   [E, {{F}}]
    dist    ...  D=2  E=2  {{F=3}}
---
Pop E. F already has a label from D, so E adds nothing
    queue   [F]
---
Pop F. G is new at distance 4
    queue   [{{G}}]
    dist    ...  F=3  {{G=4}}
---
Pop G; the queue is empty. Path to G from parents: G <- F <- D <- B <- A
    path    A -> B -> D -> F -> G   (4 edges)
```

## Template

```python
from collections import deque

def bfs(adj, source):
    """Fewest-edge distances and BFS-tree parents from source (unweighted graph)."""
    dist = {source: 0}
    parent = {source: None}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if v not in dist:              # first discovery is a shortest path
                dist[v] = dist[u] + 1      # mark when you enqueue
                parent[v] = u
                queue.append(v)
    return dist, parent


def path_to(parent, target):
    """Vertices from the source to target via parent pointers; [] if target was not reached."""
    if target not in parent:
        return []
    path = []
    while target is not None:
        path.append(target)
        target = parent[target]
    return path[::-1]
```

`adj` can be a list of lists or a dict of lists. For level-by-level work (minutes, rounds), process `for _ in range(len(queue))` pops per round, or keep the current level in a list and build the next one.

## Pitfalls

- **Marking on pop** instead of on push (see above).
- **`list.pop(0)`**: O(n) per pop. Use `deque.popleft()`.
- **Using 0 as "unvisited"** in a distance array: the source has distance 0. Use -1, `None` or `in`.
- **Counting the wrong thing**: some problems count vertices on the path (edges + 1), for example a grid path "of length k cells".
- **Unreachable targets**: decide what to return (-1, `[]`) before coding.
- **Weighted edges**: BFS silently returns the path with fewest edges, not the cheapest.

## Check yourself

Q: Add an edge C - G to the trace graph. What are `dist[G]`, `parent[G]` and `dist[F]` now?
A: When C is popped (third pop), G is new, so `dist[G] = 2` with parent C. The queue is then [D, E, G]; D is popped before G and discovers F at distance 3, so `dist[F] = 3` with parent D, unchanged. The path to G becomes A -> C -> G.

Q: Why must the container be first-in first-out? Give a graph where a stack gives a wrong distance.
A: A FIFO queue pops all distance-d vertices before any at d + 1, which the proof needs. With a stack, take edges A-B, A-C, C-D, D-X, B-X and neighbours in that order. Popping A labels B and C as 1; the stack pops C first and labels D as 2; then pops D and labels X as 3. But X is at distance 2 via B, and B is never given the chance to discover it first.

Q: You need the fewest knight moves between two squares on a 1,000 x 1,000 board, and separately the cheapest flight between two airports. Which uses BFS?
A: The knight: every move costs the same, so BFS over squares (10^6 vertices, 8 edges each) is right. Flights have prices, so the fewest flights may not be the cheapest; use Dijkstra.

Q: A BFS marks a vertex as seen only when it pops it: it pushes every neighbour that has not been popped yet, and skips a popped vertex that was already seen. Is it correct? How many pushes on a complete graph of n vertices?
A: Distances come out right if they are recorded when a vertex is first popped, but every vertex is pushed once for each neighbour popped before it, about n^2 / 2 pushes (499,501 for n = 1,000) instead of n. The queue can hold O(E) entries instead of O(V), and the time grows with it. Mark on push.

## Lab

- **1971 Find if Path Exists in Graph.** Run `bfs` from `source` and check whether `destination` got a distance (or stop early when you reach it). Expected: O(V + E); for n = 6, edges `[[0,1],[1,2],[3,4],[4,5]]`, source 0: destination 2 is reachable, destination 5 is not.
- **1091 Shortest Path in Binary Matrix.** BFS over open cells with eight directions; the answer counts cells, so start at 1. Expected: O(n^2) time and space; `[[0,0,0],[1,1,0],[1,1,0]]` gives 4, and `[[1,0],[0,0]]` gives -1 because the start is blocked.

> [!know]
> You now know how to find fewest-edge paths with BFS, rebuild them from parents, and argue why the first discovery is the shortest.

=== primer | How does DFS find connected components, and when does recursion fail? | 14 min
goal: Count components and flood-fill regions with recursive and iterative depth-first search, read preorder and postorder from a trace, and avoid Python's recursion limit
tag: graphs-dfs | DFS and connected components
link: USACO Guide: Graph traversal | https://usaco.guide/silver/graph-traversal#an-issue-with-deep-recursion | 5 min: the short section 'An Issue With Deep Recursion' (why deep recursive DFS crashes and what to do instead); the 'DFS' section above it has Python code
practice: 733, 200

> [!key]
> Depth-first search follows one path as far as it can, then backs up to the most recent vertex with an unexplored edge. Started from every vertex not yet seen, each start discovers exactly one **connected component**. The recursive version is the shortest to write; the **iterative version with an explicit stack** is the one to use when the graph can be deep, because Python stops at 1,000 nested calls by default.

## Intuition

Explore a cave with a piece of chalk. At every junction take a passage you have not chalked yet; when every passage from here is chalked, walk back the way you came and try again from there. When you are back at the entrance with nothing left, you have seen every chamber connected to it. To count separate cave systems, go to an entrance you have not chalked and start again: each fresh start is a new system.

## How it works

### Recursive DFS and components

`dfs(u)` marks u, then calls itself on each unmarked neighbour. The call stack is the path from the start to the current vertex. A driver loop starts a new search from every unmarked vertex and counts how many searches it started.

Two orders fall out of the recursion and matter later:

- **Preorder**: when a vertex is entered (marked). Useful for copying or printing.
- **Postorder**: when a vertex is left, after all its descendants. A vertex finishes only after everything reachable from it through unvisited vertices has finished. Cycle detection and topological sorting are built on this order.

### Iterative DFS

Replace the call stack with a list. Pop a vertex, push its unmarked neighbours, and **mark them as you push** so nothing is pushed twice. This visits every reachable vertex exactly once, which is all components and flood fill need. It does not reproduce the recursive preorder (on the trace graph below it visits A, C, D, F, G, E, B), and it has no natural "leave" moment; when you need postorder, keep an iterator per stack frame, as in the cycle-detection card.

### Flood fill

On a grid the same search recolours a region: start at a cell, and repeatedly step to sideways neighbours that still have the old colour. Recolouring a cell doubles as marking it visited, so no separate set is needed.

## Cost

Every vertex is marked once and every adjacency list is scanned once: **O(V + E) time**. Space is O(V) for the marks plus the stack. For recursion that stack is the depth of the search, which can be V: a path graph, or a snake-shaped region in a grid, recurses once per vertex.

CPython's default limit is 1,000 frames (`sys.getrecursionlimit()`). A 1,000 x 1,000 all-land grid can recurse a million deep and raises `RecursionError` long before. `sys.setrecursionlimit` raises the ceiling, and since CPython 3.11 pure Python calls no longer use the C stack, so a high limit usually works; on older versions it can crash the interpreter, and deep recursion is slower than a loop either way. The explicit stack has no such limit.

## When to use it

| Need | BFS | DFS |
|---|---|---|
| Fewest edges to a target | yes | no |
| Reachability, components, flood fill | yes | yes |
| Postorder: directed cycles, topological order, subtree totals | no | yes |
| Memory | the widest level | the deepest path |
| Python recursion limit | not an issue | use the iterative form or raise the limit |
| Every path, with choices undone (backtracking) | no | yes |

Choose DFS when you need to visit everything and do not care about distance, or when you need finishing times. When edges arrive one at a time with connectivity questions in between, union-find (next module) beats running DFS again after every edge.

## Worked trace

Recursive DFS from A on the graph from the BFS card (neighbours in alphabetical order). The stack shows the active calls.

```text
    A --- B --- E
    |     |     |
    C --- D --- F --- G
```

```steps
Call dfs(A): mark A. Its first neighbour B is unmarked
    stack   [A]
    pre     A
---
dfs(B): A is marked, D is not, so go deeper before looking at E
    stack   [A, {{B}}]
    pre     A B
---
dfs(D): B is marked, C is not
    stack   [A, B, {{D}}]
    pre     A B D
---
dfs(C): both neighbours (A, D) are marked, so C finishes first
    stack   [A, B, D, {{C}}]
    pre     A B D C
    post    {{C}}
---
Back in D: next neighbour F is unmarked; F's first unmarked neighbour is E, which finishes at once
    stack   [A, B, D, F, {{E}}]
    pre     A B D C F E
    post    C {{E}}
---
Back in F: G is unmarked; G has no other neighbours and finishes
    stack   [A, B, D, F, {{G}}]
    pre     A B D C F E G
    post    C E {{G}}
---
F, D, B and A have no unmarked neighbours left and finish in turn; one component of 7 vertices
    stack   []
    post    C E G {{F D B A}}
```

## Template

```python
def count_components(n, adj):
    """Number of connected components of an undirected graph on 0..n-1 (recursive DFS)."""
    seen = [False] * n

    def dfs(u):
        seen[u] = True
        for v in adj[u]:
            if not seen[v]:
                dfs(v)

    count = 0
    for s in range(n):
        if not seen[s]:
            dfs(s)
            count += 1
    return count


def component_labels(n, adj):
    """Component number of every vertex, with an explicit stack (safe for deep graphs)."""
    label = [-1] * n
    count = 0
    for s in range(n):
        if label[s] != -1:
            continue
        label[s] = count
        stack = [s]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if label[v] == -1:
                    label[v] = count        # mark on push: each vertex is pushed once
                    stack.append(v)
        count += 1
    return label


def flood_fill(grid, r, c, new):
    """Recolour the 4-connected region of equal values containing (r, c), in place."""
    old = grid[r][c]
    if old == new:
        return grid                         # otherwise the loop below never ends
    rows, cols = len(grid), len(grid[0])
    grid[r][c] = new
    stack = [(r, c)]
    while stack:
        i, j = stack.pop()
        for ni, nj in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= ni < rows and 0 <= nj < cols and grid[ni][nj] == old:
                grid[ni][nj] = new          # the new colour is the visited mark
                stack.append((ni, nj))
    return grid
```

## Pitfalls

- **Recursion depth** on grids and long chains: use the iterative version, or BFS.
- **Marking on pop in the iterative version**: a vertex can then sit on the stack many times. Mark on push, or skip already-marked vertices when popping.
- **Flood fill with the same colour**: if `new == old`, recolouring never changes anything, so the region is pushed forever. Return early.
- **Mutating the caller's grid** when they did not expect it; copy first if the input must survive.
- **Strings are immutable**: a grid given as a list of strings must become a list of lists before you recolour it.
- **Diagonal neighbours**: only include them when the statement says cells touching at corners are connected.

## Check yourself

Q: In the trace graph, scan B's neighbours in the order E, D, A instead (all other lists alphabetical). What are the preorder and postorder from A?
A: Preorder A, B, E, F, D, C, G. Postorder C, D, G, F, E, B, A. From B the search goes to E first, then F, then D (F's first neighbour), then C; G is reached from F after D finishes.

Q: Why does each start in the driver loop discover exactly one component?
A: DFS from s marks every vertex reachable from s through unmarked vertices. Nothing in s's component was marked before (otherwise s would have been marked too, since marks spread along all edges of a component), so the search marks the whole component and nothing outside it, because no edge leaves a component.

Q: You must count islands in a 2,000 x 2,000 grid that may be almost entirely land. Recursive DFS, iterative DFS or BFS?
A: Iterative DFS or BFS. A single island can contain 4 million cells, and recursive DFS can nest once per cell, far beyond the default limit of 1,000 frames. Both alternatives keep their own stack or queue on the heap and run in O(rows x cols).

Q: A flood fill recolours by pushing neighbours with `grid[ni][nj] == old` and sets the colour only when a cell is popped. What goes wrong?
A: A cell keeps the old colour while it waits on the stack, so other neighbours push it again; it can be pushed up to four times, wasting time and memory. Recolour (mark) at push time, as in the template.

## Lab

- **733 Flood Fill.** Iterative or recursive fill from the start pixel, with the early return when the colour is unchanged. Expected: O(m n) time; for image `[[1,1,0],[1,0,0],[0,1,1]]`, start (0, 0) and colour 2 the result is `[[2,2,0],[2,0,0],[0,1,1]]` (the 1s at the bottom right are not connected); with colour 1 the image is returned unchanged.
- **200 Number of Islands.** Scan every cell; each unvisited `'1'` starts a fill and adds one island. Expected: O(m n) time; for rows `"10101"`, `"11001"`, `"00011"` the answer is 3 (cells touching only at a corner are separate islands).

> [!know]
> You now know how to count components and fill regions with DFS, read pre- and postorder, and keep deep searches off the call stack.

=== primer | How do you run BFS on a grid, and why start from every source at once? | 14 min
goal: Search a grid as an implicit graph with a direction array and bounds checks, compute distances to the nearest of many sources in one pass, and reverse a search to start from the targets
tag: graphs-grid | Grid and multi-source BFS
link: Red Blob Games: Flow field pathfinding for tower defense | https://www.redblobgames.com/pathfinding/tower-defense/ | 10 min, the whole short article: one BFS from the goal gives every tile its distance and next step, with interactive diagrams of the frontier
practice: 994, 417

> [!key]
> A grid is a graph you never build: each open cell is a vertex and its neighbours come from a **direction array** plus a **bounds check**. To find, for every cell, the distance to the **nearest** of many sources, put **all the sources in the queue at distance 0** and run one BFS: O(rows x cols) instead of one search per source. When every cell asks "can I reach the edge?", turn it around and search once **from** the edge.

## Intuition

Fires break out in three places at the same moment and spread one cell per minute. Each cell catches fire at the minute the nearest fire reaches it. You do not simulate each fire separately and take the minimum; you let all three spread together, ring by ring. That is multi-source BFS.

Another way to see it: invent a "super source" joined to every real source by an edge. BFS from the super source puts all real sources at distance 1, then their neighbours at 2, and so on. Subtract one and you have the distance to the nearest source. Seeding the queue with all sources at distance 0 is exactly that, without the extra vertex.

## How it works

### Grid conventions

- `rows = len(grid)`, `cols = len(grid[0])`; a cell is `(r, c)`.
- `DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))` for 4-neighbours; add the four diagonals for 8.
- Check bounds **before** indexing. In Python `grid[-1]` is silently the last row, so a missing check wraps around instead of failing.
- The distance array doubles as the visited set: -1 means unseen.

### Multi-source BFS

Initialise every source with distance 0 and push them all, in any order. The queue then starts as one complete "level 0", and the usual BFS invariant holds: levels come out in order. The first time a cell is reached, it is reached from its nearest source. If the question is in rounds ("minutes until all oranges rot"), process the queue one level at a time and count levels.

### Reversing the search

"Which cells can reach the border?" asked from every cell costs a BFS per cell. Ask instead "which cells can the border reach, walking the moves backwards?" and one search answers for everyone. On undirected grids the moves are symmetric, so you just start at the border cells. When moves are directed (water flows only to a cell that is not higher), walk the reverse rule: from a cell you may step to a neighbour that is **not lower**.

## Cost

Each cell is pushed once, when its distance is set, and popped once; each pop checks 4 (or 8) neighbours: **O(rows x cols) time and space**, however many sources there are. Running one BFS per source instead costs O(S x rows x cols): on a 1,000 x 1,000 grid with 1,000 sources that is 10^9 cell visits against 10^6.

Speed tips for Python: store distances in a list of lists (or a flat list indexed by `r * cols + c`) rather than a dict of tuples, and hoist `rows`, `cols` and the direction tuple out of the loop.

## When to use it

- "Distance from every cell to the nearest X", "time until everything is infected, burnt or rotten", "distance to the nearest exit or border".
- Several starting points that act simultaneously.
- "Which cells can reach the ocean, the border or the exit": search from the target side once.
- Not when sources start at different times or cells cost different amounts to enter: that is Dijkstra with several starting distances (shortest paths module).
- Not when only one source matters: plain BFS.

## Worked trace

Single source first. BFS from S on a 4 x 5 grid (`#` is a wall). Each step is one level; the highlighted cells get their distance **when they are enqueued**, so no cell can enter the queue twice.

```steps
Level 0: the start cell
    |{{ 0}}  .  .  #  .|
    | .  #  .  .  .|
    | .  #  .  #  .|
    | .  .  .  #  .|
---
Level 1: both open neighbours of S
    | 0 {{ 1}}  .  #  .|
    |{{ 1}}  #  .  .  .|
    | .  #  .  #  .|
    | .  .  .  #  .|
---
Level 2
    | 0  1 {{ 2}}  #  .|
    | 1  #  .  .  .|
    |{{ 2}}  #  .  #  .|
    | .  .  .  #  .|
---
Level 3: the two fronts move around the wall separately
    | 0  1  2  #  .|
    | 1  # {{ 3}}  .  .|
    | 2  #  .  #  .|
    |{{ 3}}  .  .  #  .|
---
Level 4: the upper front labels (1, 3) and (2, 2), the lower front labels (3, 1) (cells are (row, column) from 0)
    | 0  1  2  #  .|
    | 1  #  3 {{ 4}}  .|
    | 2  # {{ 4}}  #  .|
    | 3 {{ 4}}  .  #  .|
---
Level 5: (3, 1) is popped first and labels (3, 2). When (2, 2) is popped next, (3, 2) already has a label, so it is not queued a second time
    | 0  1  2  #  .|
    | 1  #  3  4 {{ 5}}|
    | 2  #  4  #  .|
    | 3  4 {{ 5}}  #  .|
---
Levels 6 and 7: the right-hand column fills downwards; the bottom-right cell is 7 steps away
    | 0  1  2  #  6|
    | 1  #  3  4  5|
    | 2  #  4  #  6|
    | 3  4  5  # {{ 7}}|
```

Now three sources (S) at once on a 5 x 7 grid. Every cell ends up labelled with the distance to its nearest S.

```steps
Level 0: all three sources are in the queue before the loop starts
    |{{ 0}}  .  .  .  #  .  .|
    | .  #  #  .  #  .  .|
    | .  .  .  .  .  . {{ 0}}|
    | #  .  #  #  .  .  .|
    |{{ 0}}  .  .  .  .  .  .|
---
Level 1: each source labels its own neighbours
    | 0 {{ 1}}  .  .  #  .  .|
    |{{ 1}}  #  #  .  #  . {{ 1}}|
    | .  .  .  .  . {{ 1}}  0|
    | #  .  #  #  .  . {{ 1}}|
    | 0 {{ 1}}  .  .  .  .  .|
---
Level 2: the fronts grow; a cell already labelled is never relabelled
    | 0  1 {{ 2}}  .  #  . {{ 2}}|
    | 1  #  #  .  # {{ 2}}  1|
    |{{ 2}}  .  .  . {{ 2}}  1  0|
    | # {{ 2}}  #  #  . {{ 2}}  1|
    | 0  1 {{ 2}}  .  .  . {{ 2}}|
---
Level 3: fronts from different sources meet; each cell keeps the first (smallest) label
    | 0  1  2 {{ 3}}  # {{ 3}}  2|
    | 1  #  #  .  #  2  1|
    | 2 {{ 3}}  . {{ 3}}  2  1  0|
    | #  2  #  # {{ 3}}  2  1|
    | 0  1  2 {{ 3}}  . {{ 3}}  2|
---
Level 4: the last open cells; one pass labelled all 28 open cells
    | 0  1  2  3  #  3  2|
    | 1  #  # {{ 4}}  #  2  1|
    | 2  3 {{ 4}}  3  2  1  0|
    | #  2  #  #  3  2  1|
    | 0  1  2  3 {{ 4}}  3  2|
```

## Template

```python
from collections import deque

def grid_bfs(grid, sources):
    """Steps from the nearest source to every open cell ('#' is a wall); -1 if unreachable."""
    rows, cols = len(grid), len(grid[0])
    dist = [[-1] * cols for _ in range(rows)]
    queue = deque()
    for r, c in sources:
        dist[r][c] = 0
        queue.append((r, c))
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != '#' and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1      # mark on enqueue
                queue.append((nr, nc))
    return dist
```

A single-source search is `grid_bfs(grid, [start])`. For rounds, wrap the body of the loop in `for _ in range(len(queue)):` and count the rounds that changed something.

## Pitfalls

- **Bounds after indexing**: `grid[nr][nc] != '#' and 0 <= nr < rows` reads `grid[-1]` (wraps) or raises `IndexError` before the check runs. Check bounds first.
- **Counting rounds off by one**: the last round may add nothing. Count only rounds that changed a cell, or stop when nothing is left to change.
- **Unreachable targets**: after the search, cells still at -1 (or fresh oranges still fresh) mean "impossible".
- **Duplicate sources**: harmless if you label before pushing and skip already-labelled cells.
- **Searching from the wrong side**: if many cells ask the same question about a fixed target set, start at the targets.

## Check yourself

Q: In the multi-source trace, what is the distance of the cell in row 2, column 1 (counting from 0), and which source gives it?
A: 3, set at level 3. Two sources tie: the top-left S reaches it in three steps (down, down, right) and the bottom-left S also in three (right, up, up). BFS does not care which one labels it first; the distance is the same.

Q: Why does seeding several sources at distance 0 give each cell the distance to its nearest source?
A: It is ordinary BFS from an imaginary super source joined to every real source, with every distance reduced by one. BFS from one source returns shortest distances, and the shortest path from the super source to a cell goes through the nearest real source.

Q: For every cell of a height map you must decide whether water can flow (to equal or lower neighbours) to the top border. What do you search, and from where?
A: One search from all top-border cells, stepping from a cell to a neighbour whose height is greater than or equal to the current one (the reverse of the flow rule). Every cell reached can drain to the top border. That is O(rows x cols) instead of one search per cell.

Q: A colleague's BFS counts minutes by incrementing after every round and returns the count, but gets 1 too many on a grid where everything rots. Why?
A: The final round pops the last cells to rot and finds nothing new, but still increments the counter. Stop when no fresh cells remain (`while queue and fresh:`), or count only rounds that changed something.

## Lab

- **994 Rotting Oranges.** Multi-source BFS seeded with every rotten orange, one level per minute, and a count of fresh oranges left. Expected: O(m n); for `[[2,1,1,0],[0,1,0,1],[1,1,1,2]]` the answer is 3; for `[[2,1,0],[0,0,1]]` it is -1 (the last orange is cut off); for `[[0,2]]` it is 0.
- **417 Pacific Atlantic Water Flow.** Reverse the flow: search uphill (to neighbours that are not lower) from the Pacific edges (top row, left column) and separately from the Atlantic edges (bottom row, right column); answer the cells in both sets. Expected: O(m n); for heights `[[3,3,3],[3,1,3],[0,2,4]]` every cell except the centre pit (1, 1) qualifies, 8 cells in total.

> [!know]
> You now know how to treat a grid as an implicit graph, label every cell with its distance to the nearest source in one pass, and search backwards from targets.

=== lab | Maze lab: BFS, DFS and distance maps | 45 min
goal: Generate mazes, solve them with a queue and with a stack, draw what each explored, check distances against a brute-force oracle, and measure that BFS grows linearly with the number of cells
link: Wikipedia: Maze generation algorithm | https://en.wikipedia.org/wiki/Maze_generation_algorithm#Randomized_depth-first_search | 5 min: 'Randomized depth-first search' and its iterative implementation with an explicit stack, which is the generator used here

You will carve mazes with an explicit-stack DFS, solve them with BFS and with DFS, look at what each one explored, check BFS distances against a slow oracle that uses no queue at all, and time BFS as the maze grows. Everything uses the standard library.

## Steps

1. Save this as `maze_lab.py`. The grid has walls (`#`) between cells; cell (r, c) of the maze sits at grid position (2r + 1, 2c + 1), and the border is solid, so neighbours never fall off the grid.

```python
import random
import time
from collections import deque

OPEN, WALL = ' ', '#'
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def make_maze(h, w, loops=0.0, seed=0):
    """A (2h+1) x (2w+1) grid carved by randomised DFS; `loops` knocks out extra walls."""
    rng = random.Random(seed)
    H, W = 2 * h + 1, 2 * w + 1
    g = [[WALL] * W for _ in range(H)]
    g[1][1] = OPEN
    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        r, c = stack[-1]
        fresh = [(r + dr, c + dc) for dr, dc in STEPS
                 if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in seen]
        if not fresh:
            stack.pop()                                  # dead end: back up
            continue
        nr, nc = rng.choice(fresh)
        g[r + nr + 1][c + nc + 1] = OPEN                 # knock down the wall between the cells
        g[2 * nr + 1][2 * nc + 1] = OPEN
        seen.add((nr, nc))
        stack.append((nr, nc))
    for _ in range(int(loops * h * w)):
        r, c = rng.randrange(1, H - 1), rng.randrange(1, W - 1)
        if (r + c) % 2 == 1:                             # a wall between two cells, not a pillar
            g[r][c] = OPEN
    return g


def solve(g, start, goal, frontier="bfs"):
    """Path start..goal, cells taken off the frontier (queue or stack), and the parent map."""
    parent = {start: None}
    bag = deque([start])
    taken = 0
    while bag:
        cell = bag.popleft() if frontier == "bfs" else bag.pop()
        taken += 1
        if cell == goal:
            break
        r, c = cell
        for dr, dc in STEPS:
            nxt = (r + dr, c + dc)
            if g[nxt[0]][nxt[1]] == OPEN and nxt not in parent:
                parent[nxt] = cell
                bag.append(nxt)
    path, cell = [], goal
    while cell is not None:
        path.append(cell)
        cell = parent[cell]
    return path[::-1], taken, parent


def draw(g, path, explored):
    rows = [row[:] for row in g]
    for r, c in explored:
        rows[r][c] = '.'
    for r, c in path:
        rows[r][c] = 'o'
    return "\n".join("".join(row) for row in rows)


def distance_map(g, sources):
    """Multi-source BFS: steps from every open cell to its nearest source."""
    dist = {s: 0 for s in sources}
    queue = deque(sources)
    while queue:
        r, c = queue.popleft()
        for dr, dc in STEPS:
            nxt = (r + dr, c + dc)
            if g[nxt[0]][nxt[1]] == OPEN and nxt not in dist:
                dist[nxt] = dist[(r, c)] + 1
                queue.append(nxt)
    return dist


def slow_distances(g, sources):
    """Oracle: relax every cell from its neighbours until nothing changes (no queue at all)."""
    cells = [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] == OPEN]
    dist = {cell: float('inf') for cell in cells}
    for s in sources:
        dist[s] = 0
    changed = True
    while changed:
        changed = False
        for r, c in cells:
            for dr, dc in STEPS:
                nb = (r + dr, c + dc)
                if nb in dist and dist[nb] + 1 < dist[(r, c)]:
                    dist[(r, c)] = dist[nb] + 1
                    changed = True
    return {k: v for k, v in dist.items() if v != float('inf')}
```

2. Solve one small maze both ways and look at the pictures (`o` is the path, `.` is every cell the search discovered):

```python
g = make_maze(6, 12, seed=1)
start, goal = (1, 1), (len(g) - 2, len(g[0]) - 2)
for kind in ("bfs", "dfs"):
    path, taken, parent = solve(g, start, goal, kind)
    print(kind, "path cells:", len(path), "taken off the frontier:", taken)
    print(draw(g, path, parent))
```

3. Compare BFS and DFS on 20 mazes of 40 x 40 cells, as perfect mazes (`loops=0`) and with extra openings (`loops=0.1` and `0.3`). For each setting, average the path length and the number of cells taken off the frontier, and put them in a table.
4. Stress-test against the oracle on 200 small random mazes with one to three random sources: `distance_map` must equal `slow_distances`; the BFS path from `solve` must have exactly `distance_map(g, [start])[goal] + 1` cells; the DFS path must be a valid walk (consecutive cells adjacent) and never shorter than the BFS path. Stop at the first mismatch and print the maze.
5. Draw a distance map from two exits (top left and bottom right) of `make_maze(5, 10, seed=3)`, printing `dist % 10` in each open cell. Before running, predict where the largest digits will be.
6. Doubling experiment: build `make_maze(side, side, 0.1, 0)` for side 100, 200, 400 and 800, and time `distance_map(g, [(1, 1)])` (best of three) with `time.perf_counter()`. Compute the ratio between consecutive times.
7. Optional, a preview of A*: replace the deque in `solve` with a heap ordered by Manhattan distance to the goal (greedy best-first search) and compare the cells taken and the path length with BFS on mazes with loops.

## What you should see

- In the small maze, BFS and DFS draw the **same path** (53 cells for seed 1): a perfect maze has exactly one path between any two cells. They differ in how much they explore (66 cells taken off the frontier for BFS against 133 for DFS on this seed).
- With seeds 0 to 19 on 40 x 40 perfect mazes, both paths average about 1,070 cells. With loops the BFS path collapses (about 410 cells at 0.1 and 260 at 0.3) while the DFS path stays around 870: **DFS finds a path, BFS finds the shortest**. DFS often takes fewer cells off its stack than BFS takes off its queue (about 2,100 against 2,700 at 0.1), which shows that exploring less is not the same as finding the best path.
- The oracle test passes silently. If it fails, the usual cause is marking cells when they are popped, or a typo in the direction tuple.
- The distance map counts up from both exits and the largest digits sit in dead ends far from both, where the two waves of the multi-source BFS meet.
- Each doubling of the side multiplies the open cells by 4 and the time by roughly 4 (ratios between 3.5 and 5.5 are normal noise): BFS is linear in the number of cells, a few seconds for the 1.3 million open cells at side 800 in pure Python.
- Greedy best-first search usually takes far fewer cells than BFS on open mazes but can return a longer path; A*, in the shortest paths module, keeps the speed and restores optimality.

=== primer | How do you find the fewest moves through a puzzle's states? | 15 min
goal: Model a puzzle as a graph of states, encode states so they hash, generate neighbours on the fly, estimate the size of the search, and run BFS over it
tag: graphs-state | BFS over a state space
link: Erickson, Algorithms ch. 5 (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/05-graphs.pdf#page=8 | 5 min: the paragraphs on configuration graphs of games and puzzles (PDF page 8, with the Tower of Hanoi figure), then the remark at the top of PDF page 13 that any search runs on a configuration graph through a neighbour function
practice: 752, 127

> [!key]
> When the "position" is a whole configuration (the digits on a lock, a word, the water in two jugs, a cell plus the keys you hold), make each configuration a **vertex** and each legal move an **edge**. BFS over that implicit graph gives the fewest moves. The state must capture **everything that affects what you can do next**, must be **hashable**, and the search costs about (number of states) x (moves per state), so count the states before you code.

## Intuition

You have a 3-litre jug, a 5-litre jug and a tap, and you need exactly 4 litres. Each moment is fully described by two numbers, the water in each jug: (0, 0) at the start. A move (fill, empty or pour one jug into the other) takes you to another pair. There are at most 4 x 6 = 24 pairs, so "fewest moves to get 4 litres" is BFS on a graph of 24 vertices that you never draw.

## How it works

1. **Define the state.** Ask: if I froze the puzzle now, what must I write down to resume it? Jugs: (a, b). Lock: the 4-digit string. Word ladder: the current word. Grid with keys: (row, column, keys held). Grid where you may break k walls: (row, column, breaks left).
2. **Encode it hashably.** Tuples, strings, integers and frozensets work as dict keys; lists and sets do not. Bitmasks are compact for "which of up to 20 items" (`keys | 1 << i`).
3. **Generate neighbours on demand**: a function from a state to the states one move away. Never build the whole graph.
4. **BFS with a visited dict** keyed by the full state. Record parents if you need the moves, not just their number.
5. **Forbidden states** (dead ends, walls) are simplest to pre-mark as visited, so they are never enqueued. Check whether the start itself is forbidden.

### Word ladders: neighbours by pattern

Comparing a word with every other word to find one-letter neighbours costs O(N L) per word. Instead, give every word its L wildcard patterns ("hot" -> `*ot`, `h*t`, `ho*`) and group words by pattern. Two words are neighbours exactly when they share a pattern, so the neighbours of a word come from L bucket lookups. Building the buckets costs O(N L^2) (N words, L patterns each, L characters per pattern).

### Searching from both ends

If every state has b neighbours and the answer is d moves away, BFS from the start touches about b^d states. Growing one search from the start and one from the goal, always expanding the smaller frontier, and stopping when they meet touches about 2 b^(d/2). For word ladders and similar puzzles that is often the difference between seconds and milliseconds.

## Cost

Time is O(S x b x c): S reachable states, b moves from each, and c to build and hash one state. For the lock, S = 10^4, b = 8 and c is a 4-character string, so about 80,000 cheap steps. Memory is O(S) for the visited dict. Before coding, multiply out the state components: (row, column, breaks left) on a 40 x 40 grid with up to 1,600 breaks is 2.6 million states, which tells you to look for a cap (more than rows + columns breaks never help).

## When to use it

| Question | Tool |
|---|---|
| Fewest moves, each move costing the same | BFS over states |
| Moves with different costs | Dijkstra over states (shortest paths module) |
| Count the ways, or optimise, when states never repeat along a path | dynamic programming over states |
| List every solution | backtracking |
| Huge space and a good estimate of the remaining distance | A* (shortest paths module) |

Cues: "minimum number of operations, moves, steps, transformations"; small configurations (4 digits, a 2 x 3 board, words of length 10); a twist that changes what you can do later (keys, remaining breaks, direction), which must go into the state.

## Worked trace

Jugs of 3 and 5 litres, target 4 litres in either jug. Each step is one BFS level; states are (small jug, big jug).

```steps
Level 0: both jugs empty
    frontier  {{(0,0)}}
---
Level 1: fill the small jug, or fill the big jug
    frontier  {{(3,0)}}  {{(0,5)}}
---
Level 2: new states only; emptying a jug leads back to (0,0), which is already visited
    frontier  {{(3,5)}}  {{(0,3)}}  {{(3,2)}}
    seen      (0,0) (3,0) (0,5)
---
Level 3
    frontier  {{(3,3)}}  {{(0,2)}}
---
Level 4
    frontier  {{(1,5)}}  {{(2,0)}}
---
Level 5
    frontier  {{(1,0)}}  {{(2,5)}}
---
Level 6: (3,4) has 4 litres in the big jug. Six moves is the minimum
    frontier  (0,1)  {{(3,4)}}
---
Follow parents back from (3,4): fill big, pour into small, empty small, pour, fill big, pour
    path      (0,0) -> (0,5) -> (3,2) -> (0,2) -> (2,0) -> (2,5) -> {{(3,4)}}
```

## Template

```python
from collections import deque, defaultdict

def bfs_path(start, is_goal, neighbours):
    """Fewest-move list of states from start to a goal state, or None. States must be hashable."""
    parent = {start: None}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        if is_goal(state):
            path = []
            while state is not None:
                path.append(state)
                state = parent[state]
            return path[::-1]
        for nxt in neighbours(state):
            if nxt not in parent:          # visited is keyed by the whole state
                parent[nxt] = state
                queue.append(nxt)
    return None


def jug_moves(state, cap_a=3, cap_b=5):
    """States one move from (a, b): fill, empty, or pour one jug into the other."""
    a, b = state
    ab = min(a, cap_b - b)                 # how much can go from a into b
    ba = min(b, cap_a - a)
    return [(cap_a, b), (a, cap_b), (0, b), (a, 0), (a - ab, b + ab), (a + ba, b - ba)]


def pattern_buckets(words):
    """Wildcard pattern ('h*t') -> words matching it; neighbours share a pattern."""
    buckets = defaultdict(list)
    for w in words:
        for i in range(len(w)):
            buckets[w[:i] + '*' + w[i + 1:]].append(w)
    return buckets


path = bfs_path((0, 0), lambda s: 4 in s, jug_moves)   # 7 states, 6 moves
```

Pre-mark forbidden states by putting them in `parent` before the search starts (and return early if the start is forbidden).

## Pitfalls

- **Visited by position only** when the state has more parts: a cell reached with no keys is not the same state as that cell reached with a key.
- **Unhashable states**: lists cannot be dict keys; convert to tuples or strings.
- **Forbidden start**: if the start state is a dead end, the answer is "impossible", not 0.
- **Counting levels by hand**: store the distance (or the parent) with each state instead of a separate counter that drifts.
- **State explosion**: estimate S before coding; if it is in the hundreds of millions, look for a cap, a symmetry, or a smarter model.
- **Rebuilding expensive neighbour lists**: precompute buckets or move tables once, outside the search.

## Check yourself

Q: In the jug trace, why do only three states appear at level 2 when two states each have six moves?
A: Many moves lead to states already seen. From (3,0): filling the small jug gives (3,0) itself, emptying it gives (0,0), emptying the big jug gives (3,0) again; only (3,5) and (0,3) (pour small into big) are new. From (0,5): (3,5) is already labelled this level, (0,0) is old, and pouring gives (3,2). So level 2 is (3,5), (0,3), (3,2).

Q: In a grid where you must collect keys to open doors, why is (row, column) not a valid state?
A: Whether you can pass a door depends on the keys you hold, so two visits to the same cell with different keys have different futures. Keyed only by position, the first visit (perhaps without a key) blocks a later, more useful visit with the key. The state must be (row, column, keys held), for example with keys as a bitmask.

Q: A grid problem allows breaking up to k walls, with a 40 x 40 grid and k up to 1,600. How many states, and how do you cut them down?
A: (row, column, breaks left) gives 40 x 40 x 1,601, about 2.6 million. Any shortest path needs at most rows + columns - 2 = 78 steps, so with k at least 78 you can walk the straight Manhattan route and return 78 at once; otherwise k is at most 77 and there are at most 40 x 40 x 78 = 124,800 states.

Q: A lock solver puts dead ends in the visited set but returns 0 immediately when the target is "0000". With dead ends `["0000"]` and target "0000", what should it return, and what does it return?
A: It should return -1: the lock starts on a dead end and cannot even begin. It returns 0 because the target check happens before the dead-end check. Test the start against the forbidden set first.

## Lab

- **752 Open the Lock.** States are the 10,000 four-digit strings; each has 8 neighbours (one wheel up or down, with 9 and 0 wrapping). Pre-mark dead ends, and handle a dead start. Expected: O(10^4 x 8) time; target "0009" with no dead ends takes 1 turn; "5555" takes 20; if all eight neighbours of "0000" are dead ends, target "0011" gives -1.
- **127 Word Ladder (stretch).** BFS over words with pattern buckets; the answer counts words, not moves. Expected: O(N L^2); from "cold" to "warm" with the list `["cord","card","ward","warm","worm","word","wore","core","corm"]` the answer is 5 (cold, cord, card, ward, warm); if "warm" is not in the list, 0.

> [!know]
> You now know how to turn a puzzle into a graph of states, choose what a state must contain, and search it with BFS within a predictable budget.

=== primer | How do you detect a cycle, and when can a graph be two-coloured? | 15 min
goal: Detect directed cycles with white, grey and black colours (and recover the cycle), detect undirected cycles with the parent rule, and two-colour a bipartite graph or prove it impossible
tag: graphs-colour | Cycle detection and two-colouring
link: cp-algorithms: Checking a graph for acyclicity and finding a cycle | https://cp-algorithms.com/graph/finding-cycle.html#algorithm | 5 min: 'Algorithm' (three colours for directed graphs, the parent rule for undirected ones, and recovering the cycle from parents)
link: cp-algorithms: Check whether a graph is bipartite | https://cp-algorithms.com/graph/bipartite-check.html#algorithm | 5 min: 'Algorithm', BFS two-colouring and why a conflict means an odd cycle
practice: 785, 210

> [!key]
> In a **directed** graph, run DFS with three colours: white (unseen), grey (on the current path) and black (finished). An edge into a **grey** vertex returns to your own path, so it closes a cycle; an edge into a black vertex does not. In an **undirected** graph, meeting a visited vertex that is not the one you came from closes a cycle. A graph can be **two-coloured** (every edge joins different colours) exactly when it has no odd cycle, and BFS that alternates colours finds out.

## Intuition

Walk through a building unrolling a ball of string behind you, and roll it back up when you retreat from a dead end. The string marks your current path (grey). Rooms you have fully explored and left are black. If a one-way door leads you into a room your string already passes through, you have walked in a circle. If it leads into a black room, you have simply reached territory explored earlier from somewhere else, and nothing in there leads back to you (otherwise you would have found it then).

## How it works

### Directed graphs: three colours

`visit(u)`: colour u grey; for each edge u -> v, if v is grey report a cycle, if v is white visit it; when all edges are done colour u black. A grey vertex is an ancestor of u in the DFS (it is on the call stack), so u -> v plus the tree path v ... u is a cycle. Conversely, if a cycle exists, take its first vertex x that DFS colours grey: every other cycle vertex is still white and reachable from x, so they all turn grey while x is grey, and the edge back into x is examined then, finding x grey.

**Why one "visited" flag is wrong**: in the graph A -> B, A -> C, C -> B, DFS finishes B before reaching it again from C. A single flag says "seen B before: cycle!", but there is none. Black means "finished, cannot lead back to you".

To report the cycle, store each vertex's DFS parent. When the edge u -> v hits grey v, walk parents from u back to v.

### Undirected graphs: the parent rule

Every undirected edge is seen from both ends, so the vertex you just came from always looks visited. Ignore it; any **other** visited neighbour means a cycle. (With parallel edges between the same two vertices, compare edge ids instead of vertices.) A cheaper test when you only need yes or no: a forest has exactly V - C edges, where C is the number of components; any more edges and a cycle exists. Union-find, in the next module, detects the first edge that closes a cycle as edges arrive.

### Two-colouring (bipartite graphs)

Colour a start vertex 0 and give each newly discovered neighbour the opposite colour of the vertex that found it. If an edge ever joins two vertices of the same colour, the graph is not bipartite: following the BFS tree from both ends back to their common ancestor and adding that edge gives a cycle of odd length, and an odd cycle cannot alternate two colours. If no conflict appears, the colouring is a valid split. Run it from every uncoloured vertex, because the graph may be disconnected.

## Cost

Each algorithm is a DFS or BFS: **O(V + E) time, O(V) space**. The recursive three-colour DFS can recurse V deep, so use the iterative version (below) for large graphs.

## When to use it

- "Is it possible to finish all tasks / courses?" (a directed cycle makes it impossible), "find the circular dependency", deadlock detection in a waits-for graph.
- "Can these people be split into two groups with no conflict inside a group?", "can the map be coloured with two colours?", "two shifts with no clash".
- Undirected "is this edge list a tree?" (connected and exactly V - 1 edges, or no cycle and connected).
- Not for "how many cycles" or "longest cycle" in general graphs: those are much harder (only special shapes, such as every vertex having one outgoing edge, are easy).

| Graph | Has a cycle? | Tool |
|---|---|---|
| Directed | edge into a grey vertex | three-colour DFS, or Kahn leaves vertices behind |
| Undirected | visited neighbour that is not the parent | DFS or BFS with parents, or union-find |
| Any, two groups | edge inside a colour class (odd cycle) | BFS two-colouring |

## Worked trace

Directed graph A -> B, A -> C, C -> B, C -> D, D -> E, E -> C. DFS from A.

```steps
Visit A: it turns grey (on the current path)
    A:{{grey}}  B:white  C:white  D:white  E:white
    path  [A]
---
A -> B: B is white, so visit it. B has no edges and finishes: black
    A:grey  B:{{black}}  C:white  D:white  E:white
    path  [A]
---
A -> C: C is white, visit it
    A:grey  B:black  C:{{grey}}  D:white  E:white
    path  [A, C]
---
C -> B: B is black, already finished. Not a cycle (a single visited flag would wrongly say yes)
    A:grey  {{B:black}}  C:grey  D:white  E:white
    path  [A, C]
---
C -> D and D -> E: both white, both turn grey
    A:grey  B:black  C:grey  D:{{grey}}  E:{{grey}}
    path  [A, C, D, E]
---
E -> C: C is grey, it is on the current path. Back edge: the cycle is C -> D -> E -> C
    A:grey  B:black  {{C:grey}}  D:grey  E:grey
    cycle {{C -> D -> E -> C}}
```

## Template

```python
from collections import deque

WHITE, GREY, BLACK = 0, 1, 2

def has_cycle(adj):
    """True if the directed graph on 0..n-1 has a cycle (recursive three-colour DFS)."""
    colour = [WHITE] * len(adj)

    def visit(u):
        colour[u] = GREY                    # u is on the current path
        for v in adj[u]:
            if colour[v] == GREY:           # back edge: v is an ancestor of u
                return True
            if colour[v] == WHITE and visit(v):
                return True
        colour[u] = BLACK                   # u and everything reachable from it are done
        return False

    return any(colour[s] == WHITE and visit(s) for s in range(len(adj)))


def find_cycle(adj):
    """One directed cycle as [v, ..., v], or None. Iterative, so deep graphs are fine."""
    colour = [WHITE] * len(adj)
    parent = [-1] * len(adj)
    for s in range(len(adj)):
        if colour[s] != WHITE:
            continue
        colour[s] = GREY
        stack = [(s, iter(adj[s]))]
        while stack:
            u, edges = stack[-1]
            v = next(edges, None)
            if v is None:                   # every edge of u explored
                colour[u] = BLACK
                stack.pop()
            elif colour[v] == WHITE:
                colour[v] = GREY
                parent[v] = u
                stack.append((v, iter(adj[v])))
            elif colour[v] == GREY:         # u -> v closes a cycle
                cycle = [v]
                while u != v:
                    cycle.append(u)
                    u = parent[u]
                cycle.append(v)
                return cycle[::-1]
    return None


def two_colour(adj):
    """Colours 0/1 with every edge joining different colours, or None if there is an odd cycle."""
    colour = [-1] * len(adj)
    for s in range(len(adj)):
        if colour[s] != -1:
            continue
        colour[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if colour[v] == -1:
                    colour[v] = 1 - colour[u]
                    queue.append(v)
                elif colour[v] == colour[u]:
                    return None
    return colour
```

## Pitfalls

- **One visited flag in a directed graph** reports cycles that do not exist (any vertex reachable two ways).
- **Forgetting disconnected parts**: start from every white vertex, not just vertex 0.
- **Undirected graphs with the directed algorithm**: every edge looks like a back edge to the parent. Use the parent rule.
- **Parallel edges**: two edges between u and v form a cycle of length 2 that the vertex-based parent rule misses; compare edge ids.
- **Deep recursion**: `has_cycle` recurses once per vertex on a long chain; use `find_cycle`'s iterator stack.
- **`next(edges, None)` with None as a real vertex**: fine for integers; use a unique sentinel object if None can be a vertex.

## Check yourself

Q: Run three-colour DFS from A on A -> B, B -> C, A -> C, C -> D. Is there a cycle? Which edge would a single visited flag misreport?
A: No cycle. DFS goes A, B, C, D; D, C and B finish black; then A -> C finds C black. A single visited flag would call A -> C a cycle.

Q: Why does an edge into a black vertex never close a cycle?
A: A vertex turns black only after DFS has explored everything reachable from it. If a black v could reach the current vertex u, then u (white at that time) would have been reached and finished inside v's search, so u would be black too, not grey on the current path. So no path leads from v back to u, and u -> v cannot close a cycle.

Q: Twelve students must be split into two teams so that no pair who dislike each other share a team. You have the list of dislikes. What do you run, and what proves it impossible?
A: BFS (or DFS) two-colouring over the dislike graph, started from every uncoloured student. It is impossible exactly when some dislike edge joins two students of the same colour, which means an odd cycle of dislikes (A dislikes B, B dislikes C, C dislikes A) exists.

Q: Someone checks an undirected graph for cycles with the three-colour DFS and finds a "cycle" in a simple path 0 - 1 - 2. Why?
A: The undirected edge 0 - 1 is stored in both lists. While 1 is grey, DFS from 1 looks at its neighbour 0, which is grey (an ancestor), and reports a back edge. Undirected graphs need the parent rule: skip the vertex you came from.

## Lab

- **785 Is Graph Bipartite?** Two-colour from every uncoloured vertex (the graph may be disconnected). Expected: O(V + E); the 4-cycle `[[1,3],[0,2],[1,3],[0,2]]` gives `true`; the triangle `[[1,2],[0,2],[0,1]]` gives `false`.
- **210 Course Schedule II, cycle half.** Solve it with three-colour DFS: a back edge means return `[]`; otherwise output vertices in reverse finishing order (the next card explains why that order is valid). Expected: O(V + E); n = 2 with `[[0,1],[1,0]]` gives `[]`.

> [!know]
> You now know how to find directed and undirected cycles, recover the cycle itself, and decide whether a graph splits into two conflict-free sides.

=== primer | How do you order tasks that depend on each other? | 15 min
goal: Produce a topological order with Kahn's algorithm and with DFS finishing times, prove each correct, detect when no order exists, and use Python's graphlib
tag: graphs-topo | Topological sort
link: USACO Guide: Topological sort | https://usaco.guide/gold/toposort#bfs | 10 min: the 'BFS' section (Kahn's algorithm with in-degrees) and 'Finding a Cycle' just below it; the 'DFS' section above gives the finishing-order version
link: Python docs: graphlib.TopologicalSorter | https://docs.python.org/3/library/graphlib.html#graphlib.TopologicalSorter | 5 min: the class description (the graph maps each node to its predecessors), static_order, and CycleError
practice: 210, 802

> [!key]
> A **topological order** lists the vertices of a directed graph so that every edge u -> v has u before v. One exists exactly when the graph has **no directed cycle** (it is a DAG). **Kahn's algorithm** repeatedly outputs a vertex with no remaining incoming edges and deletes its outgoing edges; if it outputs fewer than V vertices, the rest are on a cycle or downstream of one. Alternatively, **reverse the DFS finishing order**. Both run in O(V + E).

## Intuition

Getting dressed: socks before shoes, shirt before tie, trousers before belt. At any moment you can put on anything whose prerequisites are already on. Keep doing that and you get a valid order. If socks needed shoes and shoes needed socks, you would get stuck with both still in the drawer: that is a cycle.

## How it works

### Kahn's algorithm

1. Compute every vertex's **in-degree** (number of incoming edges).
2. Put all vertices with in-degree 0 in a "ready" queue: nothing needs to happen before them.
3. Pop a vertex, append it to the order, and decrement the in-degree of each of its successors; any that reach 0 become ready.
4. If the order has V vertices, it is a topological order. Otherwise no order exists.

**Why the order is valid**: a vertex is output only when its in-degree has reached 0, which happens only after every predecessor has been output and has decremented it. **Why a cycle stops it**: on a cycle, every vertex has a predecessor on the same cycle that must be output first, so none of them can ever be the first to reach in-degree 0. Vertices downstream of a cycle are stuck too, because their in-degree still counts an edge from a stuck vertex.

### DFS finishing order

Run DFS (three colours) from every white vertex and record each vertex when it **finishes**. Reverse that list. For any edge u -> v explored while u is grey: if v is white, it is visited and finishes inside u's call, so before u; if v is black, it already finished; v cannot be grey, because that would be a cycle. So every edge goes from a later-finishing vertex to an earlier one, and the reversed finishing order puts u before v. A grey hit doubles as cycle detection.

### Choosing and shaping the order

- **Many valid orders** usually exist. To get the lexicographically smallest, replace the queue with a min-heap (`heapq`). The order is **unique** exactly when the ready set never holds more than one vertex.
- **graphlib** (standard library since Python 3.9) maps each node to its **predecessors**, the opposite of an adjacency list: `{"app": ["lib"]}` means lib comes first. `static_order()` yields a valid order or raises `CycleError` whose second argument lists a cycle.
- **DP on a DAG**: once you have a topological order, any quantity that flows along edges (longest path, number of paths, earliest finish time) can be computed in one pass in that order. The next card does exactly that for build schedules.

## Cost

Computing in-degrees scans every edge once: O(V + E). Each vertex enters and leaves the ready queue once, and each edge is decremented once: O(V + E) in total, O(V) extra space. With a heap for the smallest order, each push and pop costs O(log V): O(V log V + E). The DFS version is O(V + E) as well.

## When to use it

- "Prerequisites", "depends on", "must happen before", "build order", "install order", "is it possible to finish all".
- An alphabet order recovered from a sorted word list (compare adjacent words to get edges, then sort topologically).
- Any DP whose subproblems form a DAG that is not a simple line or grid.
- Prefer **Kahn** when you want waves of tasks that can run together, a deterministic smallest order, or no recursion. Prefer **DFS** when you also need the cycle itself to report it.
- Not for undirected graphs (there is no "before"), and not when cycles are legal and must be collapsed first (strongly connected components, outlined in the shortest paths module).

## Worked trace

Kahn's algorithm on seven tasks where e and f depend on each other by mistake:

```text
    a ---> b ---> d
    |             ^
    +----> c -----+
           |
           v
           e ---> f ---> g
           ^      |
           +------+
```

```steps
In-degrees: only a has none, so the ready queue is [a]
    vertex   a  b  c  d  e  f  g
    indeg    0  1  1  2  2  1  1
    ready    [{{a}}]
    order    []
---
Pop a: b and c drop to 0 and become ready
    indeg    0  {{0}}  {{0}}  2  2  1  1
    ready    [b, c]
    order    [a]
---
Pop b: d drops to 1, not yet ready (it still waits for c)
    indeg    0  0  0  {{1}}  2  1  1
    ready    [c]
    order    [a, b]
---
Pop c: d drops to 0 and is ready; e drops to 1 (it still waits for f)
    indeg    0  0  0  {{0}}  {{1}}  1  1
    ready    [d]
    order    [a, b, c]
---
Pop d: it has no outgoing edges. The ready queue is now empty
    indeg    0  0  0  0  1  1  1
    ready    []
    order    [a, b, c, d]
---
Stuck with 4 of 7 output: e and f wait for each other (a cycle), g waits for f (downstream of it)
    indeg    0  0  0  0  {{1}}  {{1}}  {{1}}
    left     {{e  f  g}}   so there is no topological order
```

## Template

```python
from collections import deque

def topo_kahn(n, edges):
    """Order 0..n-1 so every edge (u, v) has u before v; None if there is a cycle."""
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for u, v in edges:
        adj[u].append(v)
        indeg[v] += 1
    ready = deque(v for v in range(n) if indeg[v] == 0)
    order = []
    while ready:
        u = ready.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                ready.append(v)
    return order if len(order) == n else None


def topo_dfs(n, edges):
    """Reverse DFS finishing order (iterative); None if there is a cycle."""
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    colour = [0] * n                        # 0 white, 1 grey, 2 black
    finished = []
    for s in range(n):
        if colour[s]:
            continue
        colour[s] = 1
        stack = [(s, iter(adj[s]))]
        while stack:
            u, it = stack[-1]
            v = next(it, None)
            if v is None:
                colour[u] = 2
                finished.append(u)
                stack.pop()
            elif colour[v] == 1:
                return None                 # back edge: cycle
            elif colour[v] == 0:
                colour[v] = 1
                stack.append((v, iter(adj[v])))
    return finished[::-1]
```

With the standard library:

```python
from graphlib import TopologicalSorter, CycleError

deps = {"app": ["lib", "config"], "lib": ["utils"], "config": [], "utils": []}   # node -> predecessors
print(list(TopologicalSorter(deps).static_order()))    # ['config', 'utils', 'lib', 'app']

try:
    list(TopologicalSorter({"a": ["b"], "b": ["c"], "c": ["a"]}).static_order())
except CycleError as err:
    print(err.args[1])                                  # ['a', 'c', 'b', 'a']
```

## Pitfalls

- **Edge direction**: from the prerequisite to the dependent. In graphlib it is the other way round: a node maps to its predecessors.
- **Returning a partial order** when a cycle exists: always compare the length with V.
- **Isolated vertices**: build in-degrees for all n vertices, not just those that appear in edges, or they never get output.
- **Duplicate edges** are fine in Kahn as long as each copy is both counted and decremented; do not dedupe one side only.
- **Recursion** in the DFS version on long dependency chains; use the iterative form.
- **Expecting one particular order** when the problem accepts any valid one; check validity, not equality, in your tests.

## Check yourself

Q: Remove the edge f -> e from the trace. What order does Kahn's algorithm (FIFO queue) produce?
A: a, b, c, d, e, f, g. After c is popped, both d and e reach in-degree 0 (e now waits only for c), so the queue holds [d, e]; then e releases f and f releases g.

Q: Why does g end up left behind even though it is not on a cycle?
A: Its in-degree counts the edge f -> g. That edge is removed only when f is output, and f never is, because it waits for e, which waits for f. Kahn's leftovers are the cycle vertices plus everything reachable from them.

Q: You must report "cannot build: gen -> lib -> gen" rather than just "there is a cycle". Kahn, DFS, or both?
A: Kahn tells you a cycle exists and which vertices are stuck, but not the cycle path. Run three-colour DFS (on the stuck vertices, or the whole graph) and walk parents back from the back edge to print the cycle. Build tools typically do both: Kahn for the order, DFS for the error message.

Q: A colleague passes `{"lib": ["app"]}` to TopologicalSorter, meaning "lib must be built before app". What order comes out, and how do you fix it?
A: `['app', 'lib']`: graphlib reads the dict as "lib's predecessors are [app]", so app comes first. Write `{"app": ["lib"]}`: each node maps to the things that must come before it.

## Lab

- **210 Course Schedule II.** Kahn's algorithm with edges prerequisite -> course; return `[]` if fewer than n courses come out. Expected: O(V + E); n = 4 with `[[1,0],[2,0],[3,1],[3,2]]` gives `[0,1,2,3]` (or `[0,2,1,3]`, also valid); n = 2 with `[[0,1],[1,0]]` gives `[]`.
- **802 Find Eventual Safe States (stretch).** A node is safe when every path from it ends at a node with no outgoing edges. Reverse the edges and run Kahn from the terminal nodes using out-degrees: whatever gets output is safe. Expected: O(V + E); `[[1],[2],[0,3],[]]` gives `[3]` (0, 1 and 2 form a cycle); `[[1,2],[2,3],[5],[0],[5],[],[]]` gives `[2,4,5,6]`.

> [!know]
> You now know how to order a DAG with Kahn's algorithm or DFS finishing times, prove the order valid, and report when no order exists.

=== primer | How do build tools run dependent tasks in parallel? | 14 min
goal: Compute earliest finish times and the critical path of a task DAG in one pass over a topological order, bound the best possible schedule, and run tasks in parallel with graphlib's ready-set loop
tag: graphs-sched | Scheduling a DAG and its critical path
link: Python docs: graphlib.TopologicalSorter | https://docs.python.org/3/library/graphlib.html#graphlib.TopologicalSorter | 10 min: the class description, including the parallel example that uses prepare, get_ready, done and is_active with worker threads
link: Ninja manual: design goals | https://ninja-build.org/manual.html#_design_goals | 3 min: the 'Design goals' list, especially "builds are always run in parallel" and "underspecified build dependencies will result in incorrect builds"
practice: 2050

> [!key]
> With unlimited workers, a task can start as soon as its last prerequisite finishes, so `finish[t] = duration[t] + max(finish of t's prerequisites)`, computed in one pass over a **topological order**. The largest finish time is the length of the **critical path**, the longest chain of dependent work, and no number of workers can beat it. Real build tools run the **ready-set loop**: start everything that is ready, and when a task finishes, release the tasks whose last prerequisite it was. Python's `graphlib` gives you that loop directly.

## Intuition

Cooking dinner: rice takes 20 minutes, chopping takes 5 and frying the chopped vegetables takes 10, and the meal is served when both are done. With two cooks, rice and chopping start together; frying starts at minute 5 and ends at 15; dinner is at minute 20, set by the rice. Speeding up the chopping does nothing. Only work on the longest chain, the critical path, moves the finish time.

## How it works

### Earliest finish times (longest path in a DAG)

Process tasks in topological order, so every prerequisite is finished before you look at a task. A task starts at the latest finish among its prerequisites (0 if it has none) and finishes `duration` later. Remember which prerequisite finished last: following those links back from the task that finishes last spells out the critical path. This is dynamic programming over the DAG: the subproblems are tasks, and the topological order is the order to solve them in.

### Lower bounds for P workers

Two facts bound any schedule. It cannot finish before the critical path length L, since that chain runs one task at a time. And P workers do at most P units of work per unit of time, so it cannot finish before W / P, where W is the total work. The simple rule "whenever a worker is free, give it any ready task" (list scheduling) is never worse than (2 - 1/P) times the optimum, a classic result of Graham; preferring the ready task with the longest remaining chain usually does much better in practice.

### The ready-set loop in real tools

- **make** brings a target's prerequisites up to date first, recursively, and rebuilds a target when it is older than a prerequisite; `make -j` runs independent recipes in parallel.
- **Ninja** always builds in parallel, by default based on the number of CPUs, and its manual warns that underspecified dependencies give incorrect builds: if a step reads a file you did not declare, the scheduler is free to run it too early.
- **graphlib**: `prepare()` checks for cycles (raising `CycleError`), `get_ready()` returns every task whose prerequisites are all done, and `done(task)` releases its dependents. `is_active()` stays true while anything is ready or running.
- CI systems (for example jobs with `needs:` in GitHub Actions) and data pipelines (Airflow DAGs) are the same structure: tasks, dependencies, and a scheduler releasing ready work.

## Cost

The earliest-finish pass visits every task once and every dependency once: **O(V + E)** after (or during) the topological sort. The graphlib loop does O(V + E) bookkeeping in total plus the cost of the tasks themselves; with a thread pool, the waiting is in `wait()`, not in a busy loop.

## When to use it

- "Minimum time to finish all courses / jobs, with durations and unlimited parallelism", "earliest time each task can complete", "which tasks are critical".
- Build systems, CI pipelines, data pipelines and project plans (the critical path method in project management).
- With limited workers the exact optimum is NP-hard in general; use list scheduling with the bounds above, or simulate with a heap of finish times.
- Threads suit tasks that wait on I/O or subprocesses (compilers, tests); for CPU-bound Python functions use `ProcessPoolExecutor`, because of the GIL.

## Worked trace

Six build tasks (durations in brackets): fetch (2); lint (1), compile (4) and docs (2) need fetch; test (3) needs compile; package (1) needs test, lint and docs. `static_order()` gives fetch, lint, compile, docs, test, package.

```steps
fetch has no prerequisites: start 0, finish 2
    task     fetch  lint  compile  docs  test  package
    finish   {{2}}
---
lint, compile and docs each need only fetch: they all start at 2
    finish   2  {{3}}  {{6}}  {{4}}
---
test needs compile: start 6, finish 9
    finish   2  3  6  4  {{9}}
---
package needs test (9), lint (3) and docs (4): start at the latest, 9; finish 10
    finish   2  3  6  4  9  {{10}}
---
Walk back along the prerequisite that finished last: the critical path has length 10
    path     {{fetch -> compile -> test -> package}}   (2 + 4 + 3 + 1)
    bounds   total work 13; with 2 workers no schedule beats max(10, 13 / 2) = 10
---
graphlib's waves (call done on each whole batch): independent tasks are released together
    get_ready  ('fetch',)  ('lint', 'compile', 'docs')  ('test',)  ('package',)
```

## Template

```python
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from graphlib import TopologicalSorter

def critical_path(deps, duration):
    """Makespan with unlimited workers and one longest chain. deps maps task -> prerequisites."""
    finish, last = {}, {}
    for task in TopologicalSorter(deps).static_order():
        before = deps.get(task, ())
        last[task] = max(before, key=finish.__getitem__, default=None)  # latest prerequisite
        finish[task] = duration[task] + (finish[last[task]] if last[task] is not None else 0)
    task = max(finish, key=finish.__getitem__)
    makespan, chain = finish[task], []
    while task is not None:
        chain.append(task)
        task = last[task]
    return makespan, chain[::-1]


def run_all(deps, run, workers=4):
    """Call run(task) for every task, each after its prerequisites, up to `workers` at a time."""
    sorter = TopologicalSorter(deps)
    sorter.prepare()                        # raises graphlib.CycleError on a cycle
    with ThreadPoolExecutor(workers) as pool:
        running = {}
        while sorter.is_active():
            for task in sorter.get_ready():
                running[pool.submit(run, task)] = task
            finished, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in finished:
                future.result()             # re-raise a task's exception
                sorter.done(running.pop(future))
```

## Pitfalls

- **Forgetting `done(task)`**: its dependents are never released and the run stops short or waits forever.
- **Swallowed failures**: if you never call `future.result()`, a failed task looks finished and its dependents run on missing outputs.
- **Undeclared dependencies**: a task that reads another's output without saying so works sequentially and breaks in parallel, intermittently.
- **Wrong graph format**: graphlib wants node -> predecessors.
- **Threads for CPU-bound Python**: the GIL serialises them; use processes or subprocesses.
- **Minimising time with limited workers by brute force**: the problem is NP-hard; use the bounds and a good heuristic.

## Check yourself

Q: In the trace, compile now takes 1 instead of 4. What is the makespan with unlimited workers, and which chain is critical?
A: compile finishes at 3, test at 6, docs at 4, lint at 3, so package starts at 6 and finishes at 7. The critical path is still fetch -> compile -> test -> package, now 2 + 1 + 3 + 1 = 7.

Q: Why can no schedule on P workers finish before W / P, where W is the total work?
A: In a schedule of length T, each worker does at most T units of work, so all P together do at most P x T. All W units must be done, so P x T >= W, that is T >= W / P.

Q: Course durations are given and any number of courses can run at once, but a course starts only after all its prerequisites end. How do you get the minimum total time, and in what time complexity?
A: Topological order, then `finish[c] = time[c] + max(finish of c's prerequisites)` (0 if none); the answer is the largest finish. O(V + E), and Kahn's algorithm can compute it as it goes.

Q: A colleague's loop calls `sorter.get_ready()` once, submits those tasks, waits for all of them, and stops. What is wrong?
A: Only the first wave runs. Dependents become ready only after `done()` is called for their prerequisites, so the loop must keep calling `get_ready()` and `done()` while `is_active()` is true, as in the template.

## Lab

- **2050 Parallel Courses III (stretch).** Earliest finish times in topological order; the answer is the largest. Expected: O(n + E); n = 4, relations `[[1,2],[1,3],[2,4],[3,4]]`, times `[2,3,1,4]` gives 9 (courses 1, 2, 4: 2 + 3 + 4).
- **Your own runner.** Run `run_all` on the six build tasks from the trace with `run` sleeping `duration / 10` seconds and printing start and end times, first with `workers=1`, then 2, then 4. Expected: about 1.3 s with one worker (the total work), and about 1.0 s with two or more workers (the critical path); the start times never violate a dependency.

> [!know]
> You now know how to compute earliest finish times and the critical path of a DAG, bound any schedule, and run dependent tasks in parallel with graphlib.

=== practice
- 1971 core
  pattern: graphs-model
  cue: Computers joined by cables given as a list of pairs; can one computer reach another?
  hint: An edge list cannot be walked directly. What structure lets you list a vertex's neighbours quickly, and what do you run on it?
  insight: Build undirected adjacency lists (each edge stored in both lists), then BFS or DFS from the source with a visited set; the answer is whether the destination gets marked. Every vertex and edge is handled once.
  cost: O(V + E) time and space
- 733 core
  pattern: graphs-dfs
  cue: Recolour a pixel and every same-coloured pixel connected to it sideways
  hint: Which pixels change? Those you can reach from the start by stepping only onto the old colour. What stops you from visiting a pixel twice?
  insight: DFS or BFS from the start, stepping to 4-neighbours that still have the old colour and recolouring as you push, so the new colour is the visited mark. If the new colour equals the old one, return at once; otherwise the fill never ends.
  cost: O(m n) time, O(m n) space for the stack in the worst case
- 200 core
  pattern: graphs-dfs
  cue: Count groups of '1' cells that touch sideways
  hint: If you start a fill at a land cell nobody has visited yet, how much of the grid does that one fill account for?
  insight: Scan every cell; each unvisited land cell starts a flood fill (iterative DFS or BFS) that marks its whole island, and adds one to the count. Every cell is marked once, so the scan and all the fills together are linear.
  cost: O(m n) time, O(m n) space
- 1091 core
  pattern: graphs-bfs
  cue: Fewest cells on a path from the top-left to the bottom-right corner through 0-cells, moving in 8 directions
  hint: Every move costs the same. Which search returns the fewest moves the first time it reaches a cell?
  insight: BFS from (0, 0) over open cells with all 8 directions, setting the distance when a cell is enqueued; the first time the bottom-right cell is reached, its distance (counting cells, so the start is 1) is the answer. Return -1 if either corner is blocked or the corner is never reached.
  cost: O(n^2) time and space
- 994 core
  pattern: graphs-grid
  cue: Rot spreads from every rotten orange to its sideways neighbours once a minute; when is everything rotten?
  hint: All the rotten oranges spread at the same time. What if they all start in the queue together?
  insight: Multi-source BFS seeded with every rotten orange at minute 0, one level per minute, counting fresh oranges as they rot. The answer is the number of levels that rotted something, or -1 if any fresh orange is left.
  cost: O(m n) time and space
- 417 derive
  pattern: graphs-grid
  cue: Cells from which water, flowing to equal or lower neighbours, can reach both the top-left edges and the bottom-right edges
  hint: Searching from every cell repeats the same work many times. Can you ask the question from the oceans instead?
  insight: Reverse the flow. From all Pacific border cells, search to neighbours whose height is at least the current cell's (uphill); do the same from the Atlantic border. A cell drains to an ocean exactly when that ocean's reverse search reaches it, so answer the intersection of the two reached sets.
  cost: O(m n) time and space
- 752 core
  pattern: graphs-state
  cue: Fewest single-wheel turns to change a 4-digit lock from 0000 to a target while avoiding forbidden combinations
  hint: How many different combinations exist, and which combinations are one turn away from a given one?
  insight: Each of the 10^4 combinations is a vertex with 8 neighbours (one wheel up or down, wrapping between 9 and 0); BFS from "0000" with the dead ends pre-marked as visited gives the fewest turns. If "0000" is itself a dead end, return -1.
  cost: O(10^4 x 8) time, O(10^4) space
- 785 core
  pattern: graphs-colour
  cue: Can the vertices be split into two sets so that every edge goes between the sets?
  hint: Put one vertex on the left. Where must each of its neighbours go, and then their neighbours?
  insight: Two-colour each component with BFS or DFS, giving each newly found vertex the opposite colour of the vertex that found it; an edge between equal colours means an odd cycle, so the answer is false. Start from every uncoloured vertex, because the graph may be disconnected.
  cost: O(V + E) time, O(V) space
- 210 core
  pattern: graphs-topo
  cue: Return an order in which to take all courses, given [course, prerequisite] pairs, or nothing if no order works
  hint: Which courses can you take straight away? After taking one, which others become available?
  insight: Kahn's algorithm with edges prerequisite -> course: queue every course with in-degree 0, output a course when popped and decrement its dependents, queueing those that reach 0. If fewer than n courses come out, a cycle blocks the rest: return [].
  cost: O(V + E) time and space
- 802 stretch
  pattern: graphs-topo
  cue: Nodes from which every path eventually stops at a node with no outgoing edges
  hint: Nodes with no outgoing edges are safe. Which other nodes become safe once you know that?
  insight: A node is safe when all of its successors are safe. Reverse the edges and run Kahn on out-degrees, starting from the terminal nodes: when a node's last unresolved successor is shown safe, it becomes safe too. Nodes on or leading into a cycle never reach out-degree 0. Return the safe nodes in increasing order.
  cost: O(V + E) time and space
- 127 stretch
  pattern: graphs-state
  cue: Shortest chain of words from a start word to an end word, changing one letter at a time and using only listed words
  hint: Words are states and one-letter changes are moves. How can you find a word's neighbours without comparing it with every other word?
  insight: BFS over words, counting words on the path. Group the words by wildcard patterns (h*t) so the neighbours of a word are the other words in its L buckets; return 0 if the end word is not listed. Searching from both ends at once is faster still.
  cost: O(N L^2) time and space for N words of length L
- 2050 stretch
  pattern: graphs-sched
  cue: Courses have durations and prerequisites, and any number can run at once; minimum months to finish them all
  hint: When can a course start at the earliest? In what order can you compute that for every course?
  insight: A course starts when its slowest prerequisite ends, so finish[c] = time[c] + max(finish[p] over its prerequisites p), computed in topological order (Kahn). The answer is the largest finish time: the length of the critical path.
  cost: O(n + E) time and space
