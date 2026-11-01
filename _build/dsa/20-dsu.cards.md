=== card | 547
time: 25 min

## The problem

You are given a square matrix describing direct connections between cities. A city belongs to the same province as every city it can reach through one or more connections. Count the provinces, including isolated cities. Connections are undirected: if the matrix connects city `i` to city `j`, it also connects `j` to `i`.

For example, if cities 0 and 1 are connected and city 2 is isolated, the answer is 2. A province is a whole connected component, not just a pair of neighbouring cities.

## Constraints and what they imply

For `n` cities, the input contains `n²` matrix entries, so reading the full matrix already costs quadratic time. A solution that makes a complete graph traversal for each city needlessly repeats work. The diagonal represents a city itself and does not change the answer. Because the matrix is symmetric, inspecting only the entries above the diagonal is enough.

## Brute force

One direct approach is to start a fresh DFS from every city, find all cities it reaches, and store the resulting sets without counting duplicates. There can be `n` traversals, each examining up to `n²` matrix entries, for O(n³) time. The bottleneck is rediscovering the same component from each of its members. One DFS per *unvisited component* is already an O(n²) alternative; union-find offers another way to maintain the groups.

## The insight

Start with `n` separate groups. Every direct connection either joins two previously separate groups, decreasing the answer by one, or connects cities already in the same group, leaving the answer unchanged. Union by size keeps the parent trees shallow, and path compression shortens later searches.

## Optimal solution, traced

```steps
Initial groups for three cities
    {0}  {1}  {2}     count 3
---
Matrix entry (0, 1) is connected. Merge the two roots
    {0, 1}  {2}       count 2
---
Entries (0, 2) and (1, 2) are not connected
    {0, 1}  {2}       count {{2}}
```

Each successful merge reduces the number of components by exactly one. Since every edge is processed, cities linked by a path eventually share a root; cities in distinct components never merge.

## Code

```python
def count_provinces(matrix):
    n = len(matrix)
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    groups = n
    for i in range(n):
        for j in range(i + 1, n):
            if not matrix[i][j]:
                continue
            a, b = find(i), find(j)
            if a == b:
                continue
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
            groups -= 1
    return groups
```

## Complexity

The upper triangle has O(n²) entries; each connection performs at most two finds and one union. The bound is O(n² α(n)) time, where α is the inverse Ackermann function, and O(n) auxiliary space for parents and sizes. Counting the input matrix itself adds O(n²) space, but it is supplied by the caller.

## Mistakes and edge cases

- Decrement only when roots differ: a redundant connection does not remove another province.
- Keep isolated cities in the initial count. A single-city matrix returns 1.
- Do not apply the upper-triangle shortcut to a directed or asymmetric input.

## Variations

- Return a component label for every city instead of only the count.
- Receive connections as an edge list; process only the listed edges.
- Add roads over time and report the current number of provinces after each addition.

=== card | 684
time: 30 min

## The problem

An undirected connected graph was formed by adding one extra edge to a tree. The edges are given in order. Remove one edge so that the result is a tree; if several removals work, return the one occurring latest in the given order. Vertices are labelled from 1 to `n`, and the input has `n` edges.

For edges `[[1, 2], [1, 3], [2, 3]]`, all three edges lie on the cycle, so the requested answer is `[2, 3]`, the latest one.

## Constraints and what they imply

A tree has exactly one fewer edge than vertices, so adding one edge creates exactly one cycle. The graph is undirected and connected, and the input is a valid tree-plus-one-edge instance. A candidate removal must preserve connectivity; removing a bridge would disconnect the graph.

## Brute force

Try removing each edge, preferably in reverse input order. For each candidate, traverse the remaining graph and check that all vertices are reachable. There are `n` candidates and each traversal examines O(n) edges and vertices, for O(n²) time. The repeated connectivity traversal is the bottleneck. A candidate that leaves the graph connected has `n - 1` edges and therefore leaves a tree.

## The insight

Build the graph in input order. Before adding an edge `(u, v)`, ask whether its endpoints are already connected. If not, merging their components is safe. If they are connected, the new edge completes a cycle. Since the final graph has exactly one cycle, this edge is the last edge of that cycle in input order and is the required answer.

## Optimal solution, traced

```steps
Start with three singleton components
    {1}  {2}  {3}
---
Add 1-2, then 1-3. Both pairs had different roots
    {1, 2, 3}
---
Try 2-3. Its endpoints already share a root
    cycle edge {{[2, 3]}}
```

The maintained components are exactly the connected components of the edges already processed. The first rejected edge closes a cycle, and a tree with one additional edge cannot contain a second cycle.

## Code

```python
def redundant_connection(edges):
    n = len(edges)
    parent = list(range(n + 1))
    size = [1] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in edges:
        a, b = find(u), find(v)
        if a == b:
            return [u, v]
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
    raise ValueError("expected a tree with one extra edge")
```

## Complexity

Each of the `n` edges causes two find operations and at most one union. Union by size plus path compression gives O(n α(n)) amortised time and O(n) auxiliary space. The cost is amortised over the sequence; it is not a claim that every individual find takes constant time.

## Mistakes and edge cases

- Do not return an arbitrary cycle edge: the order requirement chooses the last.
- Allocate `n + 1` entries for labels that start at 1.
- Union roots, not arbitrary endpoints, and update the surviving root's size.
- This argument relies on exactly one extra edge; a general graph can contain several cycles.

## Variations

- Return every edge of the unique cycle, rather than only the last one.
- Process a stream of edges and flag each one that would form a cycle.
- Given weighted edges, use union-find inside Kruskal's minimum-spanning-tree algorithm.

=== card | 990
time: 30 min

## The problem

Each equation compares two lowercase letters using either equality or inequality. Determine whether values can be assigned to the letters so that all equations hold at once. There is no requirement that different letters have different values unless an inequality says so.

For `["a==b", "b==c", "a!=c"]`, the answer is false: equality forces all three letters into the same group. For `["a!=b", "b==c"]`, an assignment with `a` separate from `b` and `c` works.

## Constraints and what they imply

There are only 26 possible variables, but equations may arrive in any order and a letter may be compared with itself. Equality is transitive: if `a == b` and `b == c`, then `a == c`, even if the last equality is not written. Inequality does not have the same transitivity: `a != b` and `b != c` do not imply `a != c`.

## Brute force

For each inequality `x != y`, build the graph of all equality equations and search from `x` to see whether it reaches `y`. If it does, the constraints conflict. With `m` equations, rebuilding and traversing for up to `m` inequalities costs O(m² + 26m) time in a straightforward implementation. The repeated search through the same equality graph is the bottleneck.

## The insight

First merge the endpoints of every equality. These groups capture exactly the equalities implied by transitivity. Then examine every inequality: it is impossible precisely when both letters have the same root. Doing the passes in that order is essential; an equality appearing later can invalidate an earlier inequality.

## Optimal solution, traced

```steps
Equations: a!=c, a==b, b==c. Start with separate letters
    {a}  {b}  {c}
---
First pass: merge both equality pairs
    {{a, b, c}}
---
Second pass: a and c have the same root, but must differ
    answer {{false}}
```

If no inequality is internal to a group, assigning one distinct value per group satisfies every equation. This proves that the check is sufficient as well as necessary.

## Code

```python
def equations_possible(equations):
    parent = list(range(26))
    size = [1] * 26

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for equation in equations:
        if equation[1:3] != "==":
            continue
        a = find(ord(equation[0]) - ord("a"))
        b = find(ord(equation[3]) - ord("a"))
        if a != b:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]

    for equation in equations:
        if equation[1:3] == "!=":
            a = ord(equation[0]) - ord("a")
            b = ord(equation[3]) - ord("a")
            if find(a) == find(b):
                return False
    return True
```

## Complexity

For `m` equations, the two passes perform O(m) union-find operations. The conventional bound is O(m α(26)) amortised time and O(26) auxiliary space. Since the alphabet is fixed, this is O(m) time and O(1) space with respect to the input length.

## Mistakes and edge cases

- A single-pass check is wrong if a later equality merges two groups already checked as different.
- `a!=a` is immediately impossible; `a==a` is harmless.
- Never union the endpoints of an inequality.

## Variations

- Replace single letters with arbitrary strings using a dictionary from names to indices.
- Return one conflicting inequality when no assignment exists.
- Given only equality constraints, report how many equivalence classes are present.

=== card | 1584
time: 30 min

## The problem

Connect every point to every other point through a network of undirected edges at minimum total cost. Connecting points `(x1, y1)` and `(x2, y2)` costs `abs(x1-x2) + abs(y1-y2)`, their Manhattan distance. You may connect any pair; not every pair needs a direct edge.

For points `(0, 0)`, `(2, 0)`, and `(2, 3)`, choosing the first-to-second edge of cost 2 and the second-to-third edge of cost 3 connects all points for total 5.

## Constraints and what they imply

Every pair of distinct points is a possible edge, so `n` points define `n(n-1)/2` edges. Materialising and sorting that complete edge list uses quadratic space and an extra logarithmic factor in time. A connected network with a cycle can drop an edge without losing connectivity, so some minimum solution is a spanning tree.

## Brute force

Enumerate sets of `n - 1` edges, keep the sets that connect all points, and take the smallest sum. There are `n(n-1)/2` candidate edges and a combinatorial number of sets. Connectivity can be checked with a traversal or union-find, but the huge number of candidate sets is the bottleneck, not the check itself.

## The insight

Grow one tree using Prim's algorithm. For each point outside the tree, remember the cheapest edge from any point already inside it. Add the outside point with the smallest remembered cost, then update the remaining costs using edges from that newly added point. The minimum edge crossing this cut is safe by the minimum-spanning-tree cut property.

## Optimal solution, traced

```steps
Start at (0, 0). Its connection cost is zero
    best: [0, infinity, infinity]   total 0
---
Add (0, 0), then measure edges to the other points
    best: [used, 2, 5]             total 0
---
Add (2, 0) for 2. Its edge to (2, 3) costs 3
    best: [used, used, {{3}}]      total 2
---
Add (2, 3) for 3
    total {{5}}
```

At every iteration `best[v]` is the minimum known crossing edge to `v`. The update examines the new tree vertex, preserving that invariant.

## Code

```python
def min_connect_cost(points):
    n = len(points)
    if not n:
        return 0
    best = [float("inf")] * n
    used = [False] * n
    best[0] = 0
    total = 0

    for _ in range(n):
        u = min((i for i in range(n) if not used[i]), key=best.__getitem__)
        used[u] = True
        total += best[u]
        x, y = points[u]
        for v, (vx, vy) in enumerate(points):
            if not used[v]:
                best[v] = min(best[v], abs(x - vx) + abs(y - vy))
    return total
```

## Complexity

There are `n` iterations. Each scans up to `n` points to choose the next point and another `n` to update crossing costs, giving O(n²) time. The `best` and `used` arrays require O(n) auxiliary space. No complete edge list or priority queue is stored.

## Mistakes and edge cases

- Manhattan distance is the sum of absolute coordinate differences, not Euclidean distance.
- Initialising `best[0]` to zero makes the starting point free; it is not an extra edge.
- A single point costs zero. Negative coordinates work without special handling.
- Do not add all cheapest edges independently: the set must remain connected.

## Variations

- Return the actual chosen edges by recording which tree vertex last improved each `best` value.
- Connect a sparse graph instead and compare heap-based Prim with Kruskal.
- Change the distance function and check whether calculating each pair remains O(1).

=== card | cses:1676
time: 30 min

## The problem

There are `n` cities and initially no roads. Roads are added one at a time. After each addition, report two numbers: how many connected groups of cities exist, and how many cities are in the largest group. A road may join cities that were already connected.

With four cities and roads `(1, 2)`, `(3, 4)`, `(2, 3)`, the reports are `(3, 2)`, `(2, 2)`, and `(1, 4)`. A group includes all cities reachable through any sequence of roads, not only direct neighbours.

## Constraints and what they imply

The full sequence of road additions can be large. Recomputing connectivity from scratch after each road repeats the same work, whereas groups only merge and never split. The output must follow the order of the road additions. Cities start as singleton groups, and the largest group initially has size one when `n` is positive.

## Brute force

After adding each road, build or update an adjacency list, then run a graph traversal from each unvisited city. Count traversals and record the largest traversal size. After `m` roads this takes O(m(n + m)) time in the worst case, because a traversal scans the growing graph again after every update. The repeated graph scans are the bottleneck.

## The insight

Use disjoint-set union with a size stored at each root. Initially there are `n` roots. On a road between different roots, join the smaller group to the larger, decrease the group count, and compare the resulting size to the largest seen. If the roots are already equal, neither reported value changes. The answer can therefore be emitted immediately after each insertion.

## Optimal solution, traced

```steps
Start: four individual cities
    groups {{4}}    largest {{1}}
---
Road 1-2 merges two singleton groups
    groups {{3}}    largest {{2}}
---
Road 3-4 makes another group of two
    groups {{2}}    largest {{2}}
---
Road 2-3 merges both groups
    groups {{1}}    largest {{4}}
```

By induction, every root represents one current connected component and its size is the number of cities in that component. A new road can only leave the partition alone or merge its two endpoint components.

## Code

```python
def road_status(n, roads):
    parent = list(range(n + 1))
    size = [1] * (n + 1)
    groups = n
    largest = 1 if n else 0
    answer = []

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in roads:
        a, b = find(u), find(v)
        if a != b:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
            groups -= 1
            largest = max(largest, size[a])
        answer.append((groups, largest))
    return answer
```

## Complexity

Initialisation uses O(n) time and space. Processing `m` roads requires O(m α(n)) amortised time with union by size and path compression. The parent and size arrays use O(n) space; the returned reports use O(m) additional space. A streaming implementation can print each report instead and avoid retaining the output list.

## Mistakes and edge cases

- Always emit a report, even when a road joins cities already in the same component.
- Update size only at the surviving root, and decrease the group count only after a real merge.
- The city labels in the original task start at 1.

## Variations

- Return the size of the component containing a requested city after each road.
- Report the number of newly connected pairs when two components merge.
- Consider road deletions: ordinary union-find cannot split components, so reverse processing or a different technique is needed.

=== card | 721
time: 30 min

## The problem

Each account contains a person's name followed by one or more email addresses. Accounts that share an email, directly or through other accounts, belong to the same person. Combine each such group into one record containing its name and its distinct email addresses in sorted order. The order of the resulting records is not significant.

For `["Ada", "a@x", "b@x"]` and `["Ada", "b@x", "c@x"]`, the result is one `Ada` record with `a@x`, `b@x`, and `c@x`. Two accounts with the same name but no shared email are not necessarily the same person.

## Constraints and what they imply

Shared emails identify the same person; names alone are not unique identifiers. Each account has at least one email, and accounts of the same person have the same name. An email can occur in several accounts or be repeated; the final list includes each email once. A chain of overlaps must merge all accounts in the chain, even if its endpoints share no email.

## Brute force

Compare every pair of accounts for a shared email, construct an account graph, then traverse its components. If there are `a` accounts with up to `k` emails each, pairwise comparisons can take O(a²k) with hash-set membership, plus grouping and sorting. The bottleneck is repeatedly comparing account pairs that have no shared email.

## The insight

Map each email to the first account that used it. When another account contains that email, union its account index with the stored index. Afterwards, assign each unique email to the root of its recorded account. The dictionary detects all overlaps without testing every account pair, and union-find carries transitive connections.

## Optimal solution, traced

```steps
Account 0: a@x, b@x
    owner[a@x] = 0    owner[b@x] = 0
---
Account 1: b@x, c@x. b@x already belongs to account 0
    union(0, 1)       owner[c@x] = 1
---
Group each unique email by its account's final root
    {{Ada: a@x, b@x, c@x}}
```

Every shared email causes a merge, so each connected chain ends in one component. Conversely, an account merge happens only because an email occurs in both components, so distinct people are not joined merely because their names match.

## Code

```python
def merge_accounts(accounts):
    parent = list(range(len(accounts)))
    size = [1] * len(accounts)
    owner = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, account in enumerate(accounts):
        for email in account[1:]:
            if email not in owner:
                owner[email] = i
                continue
            a, b = find(i), find(owner[email])
            if a != b:
                if size[a] < size[b]:
                    a, b = b, a
                parent[b] = a
                size[a] += size[b]

    groups = {}
    for email, i in owner.items():
        root = find(i)
        groups.setdefault(root, []).append(email)
    return [[accounts[root][0], *sorted(emails)] for root, emails in groups.items()]
```

## Complexity

Let `N` be the number of email occurrences and `U` the number of distinct emails. Expected dictionary operations and amortised union-find work take O(N α(a)) time. Sorting all groups takes at most O(U log U) comparisons; string comparisons themselves depend on email length. Auxiliary storage is O(a + U), excluding the returned records.

## Mistakes and edge cases

- Do not merge on name alone.
- Sort the emails, not the name and emails together.
- Group by the *final* root after all unions, not the owner recorded before later merges.
- A repeated email within one account must not appear twice in the output.

## Variations

- Group users by shared phone numbers as well as emails.
- Return the original account indices alongside each merged record.
- Accept new accounts online, then generate a snapshot of merged records.

=== card | 947
time: 30 min

## The problem

Stones occupy distinct integer grid coordinates. A stone may be removed while at least one other remaining stone shares its row or column. Find the greatest number of stones that can be removed.

For stones `(0, 0)`, `(0, 1)`, `(1, 1)`, all three are linked through shared rows or columns, so two can be removed. One stone must remain because the last stone has no partner.

## Constraints and what they imply

The grid can be sparse: a coordinate's numeric value is not a suitable bound on the number of occupied positions. Stones interact only when they share a row or column, including through chains of such relationships. Distinct groups of interacting stones can never help one another remove their last stones.

## Brute force

Treat every stone as a graph vertex and compare each pair, adding an edge if they share a row or column. Count connected components with graph traversal and return `n - components`. This takes O(n²) comparisons and can store O(n²) edges. The bottleneck is testing all pairs even though a row or column can act as a shared key.

## The insight

Create a bipartite graph of occupied row identifiers and occupied column identifiers. Each stone joins its row node to its column node. Namespace rows and columns separately, since row 3 and column 3 are different nodes. Union the two nodes for each stone. Stones are in the same interaction group exactly when their row nodes are connected through this bipartite graph.

One stone must remain in each group. Conversely, choose any spanning tree of the graph whose vertices are stones and remove leaf stones one by one: every removed leaf still has its tree neighbour present. Thus each group can be reduced to one.

## Optimal solution, traced

```steps
Stone (0, 0) links row 0 and column 0
    {row0, col0}
---
Stone (0, 1) links the same row to column 1
    {row0, col0, col1}
---
Stone (1, 1) links row 1 to that component
    {{one stone group}}; 3 stones - 1 group = {{2 removals}}
```

The final number of distinct roots among occupied row nodes is the number of stone groups; every component contains at least one such row node.

## Code

```python
def removable_stones(stones):
    parent = {}
    size = {}

    def add(x):
        if x not in parent:
            parent[x] = x
            size[x] = 1

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for row, col in stones:
        r, c = ("row", row), ("col", col)
        add(r)
        add(c)
        a, b = find(r), find(c)
        if a != b:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
    groups = {find(("row", row)) for row, _ in stones}
    return len(stones) - len(groups)
```

## Complexity

For `n` stones there are at most `2n` row and column nodes and `n` unions. With expected O(1) dictionary operations, union by size and path compression give O(n α(n)) amortised time and O(n) auxiliary space. Coordinate magnitude does not determine the size of the dictionaries.

## Mistakes and edge cases

- Keep row and column namespaces separate; otherwise equal numeric coordinates can create false connections.
- Count only occupied nodes, not every possible grid row or column.
- An isolated stone cannot be removed, and an empty collection has zero removals.

## Variations

- Return the number of independent stone groups rather than the number of removals.
- Build the pairwise stone graph for a small input and compare its component count.
- Group records connected by shared attributes using one node per attribute value.

=== card | cses:1675
time: 30 min

## The problem

A set of cities is connected by possible roads, each with a repair cost. Choose roads so that every city can reach every other city and the sum of repair costs is as small as possible. If the available roads cannot connect all cities, report that no solution exists.

For three cities with road costs 4 between 1 and 2, 2 between 2 and 3, and 5 between 1 and 3, repair the first two for total cost 6. The third road would add cost without improving connectivity.

## Constraints and what they imply

The input is a weighted undirected graph. Parallel roads can be considered separately, and a disconnected input has no spanning tree. With one city, no road is needed and the minimum cost is zero. Since redundant cycles can be removed without disconnecting the network, it is enough to find a minimum spanning tree.

## Brute force

Enumerate subsets of roads, check each for connectivity, and keep the cheapest connected subset. With `m` roads there are `2^m` subsets, each potentially requiring a traversal over the graph. The exponential number of candidates is the bottleneck, even if checking one subset is fast.

## The insight

Kruskal's algorithm considers roads from cheapest to most expensive. Keep a road only if its endpoints lie in different components of the roads already chosen. The cheapest road crossing a cut between components is safe by the minimum-spanning-tree cut property. Union-find tracks the components efficiently.

When `n - 1` roads have been kept, the chosen forest is connected and is a spanning tree. If processing ends earlier, no sequence of available roads can connect the remaining components.

## Optimal solution, traced

```steps
Sort roads: 2-3 cost 2, 1-2 cost 4, 1-3 cost 5
    components {1} {2} {3}    cost 0
---
Keep 2-3, then 1-2: each joins separate components
    components {{1, 2, 3}}    cost {{6}}
---
The tree has 2 edges for 3 cities. Stop
    answer {{6}}
```

Chosen roads never form a cycle, because each joins distinct components. The cut property ensures that each chosen road can be part of some minimum spanning tree.

## Code

```python
def min_road_cost(n, roads):
    parent = list(range(n + 1))
    size = [1] * (n + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total = 0
    used = 0
    for u, v, cost in sorted(roads, key=lambda road: road[2]):
        a, b = find(u), find(v)
        if a == b:
            continue
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
        total += cost
        used += 1
        if used == n - 1:
            break
    return total if used == n - 1 else None
```

## Complexity

Sorting `m` roads takes O(m log m) time, and the union-find operations take O(m α(n)) amortised time after O(n) initialisation. The sorted copy needs O(m) space and the parent and size arrays use O(n). In the original task, print the number returned, or `IMPOSSIBLE` when the function returns `None`.

## Mistakes and edge cases

- Check connectivity after processing: a minimum *forest* is not a solution when cities remain disconnected.
- Do not add a road that joins nodes already connected, even if it is cheap.
- Equal costs may yield different trees with the same minimum total.

## Variations

- Return the chosen road IDs as well as the minimum cost.
- Find the minimum spanning forest when full connectivity is not required.
- Compare this edge-sorting approach with Prim's algorithm on a dense graph.

=== card | 399
time: 30 min

## The problem

You are given equations such as `a / b = 2` and queries asking for the ratio between two variables. Return a query's value when the given equations determine it; otherwise return `-1.0`. Variables are strings. The equations use nonzero positive ratios and are consistent with one another.

From `a / b = 2` and `b / c = 3`, the answer to `a / c` is 6. A query involving an unseen variable has no known value, including an unseen variable divided by itself.

## Constraints and what they imply

Ratios compose along a chain: `(a / b) * (b / c) = a / c`. Separate components cannot provide a ratio between their variables. Many queries may ask about the same component, so searching the equation graph anew for each query repeats work. Floating-point answers need approximate comparison, not exact equality.

## Brute force

Construct a graph with a directed weighted edge in each direction for every equation. For each query, run DFS or BFS and multiply edge weights along a path. With `E` equations and `Q` queries, this costs O(Q(V + E)) time in the worst case after constructing the graph. The repeated graph traversals are the bottleneck. This graph search is also a useful independent oracle for testing.

## The insight

Keep a disjoint-set forest where `weight[x]` means `value(x) / value(parent[x])`. A find returns both the root and `value(x) / value(root)`; path compression multiplies ratios along the path. If `a` and `b` share a root, their ratio is `weight_to_root(a) / weight_to_root(b)`.

To join separate roots using `a / b = k`, let `wa = a / root_a` and `wb = b / root_b`. If root_a is attached under root_b, its weight must be `k * wb / wa`. If the direction is reversed, use its reciprocal. Union by size keeps the forest shallow.

## Optimal solution, traced

```steps
Add a/b=2: attach one singleton root to the other
    a / b = {{2}}
---
Add b/c=3. After the union, the root ratios imply
    a / c = (a / b) * (b / c) = {{6}}
---
Query a/c uses the ratio of their weights to the common root
    result {{6}}
```

The root weights are 1. Compression changes the parent pointer but multiplies the old edge ratios so the represented value relative to the root stays the same.

## Code

```python
def evaluate_ratios(equations, values, queries):
    parent = {}
    weight = {}
    size = {}

    def add(x):
        if x not in parent:
            parent[x] = x
            weight[x] = 1.0
            size[x] = 1

    def find(x):
        if parent[x] != x:
            root, upstream = find(parent[x])
            weight[x] *= upstream
            parent[x] = root
        return parent[x], weight[x]

    for (a, b), ratio in zip(equations, values):
        add(a)
        add(b)
        ra, wa = find(a)
        rb, wb = find(b)
        if ra == rb:
            continue
        root_ratio = ratio * wb / wa
        if size[ra] < size[rb]:
            parent[ra] = rb
            weight[ra] = root_ratio
            size[rb] += size[ra]
        else:
            parent[rb] = ra
            weight[rb] = 1.0 / root_ratio
            size[ra] += size[rb]

    answer = []
    for a, b in queries:
        if a not in parent or b not in parent:
            answer.append(-1.0)
            continue
        ra, wa = find(a)
        rb, wb = find(b)
        answer.append(wa / wb if ra == rb else -1.0)
    return answer
```

## Complexity

For `E` equations, `Q` queries, and `V` variables, there are O(E + Q) union-find operations. With union by size and path compression they take O((E + Q) α(V)) amortised time, assuming expected O(1) dictionary access. The forest uses O(V) auxiliary space and the returned answers use O(Q).

## Mistakes and edge cases

- Store the direction consistently: the code stores node divided by parent, not the inverse.
- Querying an unseen variable gives `-1.0`; a known variable divided by itself gives 1.
- When a union attaches the other root, invert the derived root ratio.
- This version assumes consistent, positive, nonzero inputs; detecting contradictions is a separate task.

## Variations

- Detect a contradictory equation when both endpoints already share a root.
- Use a weighted graph traversal for small query counts and compare the results.
- Store additive offsets instead of multiplicative ratios.

=== card | 1697
time: 45 min

## The problem

You have an undirected weighted graph and several independent queries. Each query gives two vertices and a limit. Decide whether the vertices can be connected using only edges whose weight is **strictly less** than that limit. Return the answers in the original query order.

For edges `(0, 1, 2)` and `(1, 2, 5)`, vertices 0 and 2 are connected at limit 6. They are not connected at limit 5, because the edge of weight 5 is not strictly below the limit.

## Constraints and what they imply

Both the edge list and the set of queries are supplied before any answer is needed. The input may contain repeated edges and equal weights; self-reachability needs no edges. The number of queries can be large enough that repeatedly scanning the graph becomes expensive. Although queries can be processed in a different order, their answers must be returned in their original positions.

## Brute force

For each query, build or filter the graph to keep edges below its limit, then run BFS or DFS from the first vertex. With `E` edges, `V` vertices and `Q` queries, this costs O(Q(V + E)) time and O(V + E) temporary space for an adjacency list. The bottleneck is rebuilding and traversing almost the same graph for many similar limits.

## The insight

Sort queries by increasing limit and sort edges by weight. As the limit increases, the set of eligible edges only grows. Maintain a union-find for all edges already eligible; before answering the next query, union every remaining edge with weight strictly smaller than that query's limit. The two query vertices are connected exactly when they have the same root.

Remember each query's original index before sorting. Store its boolean result at that index rather than appending in processing order. Edge weights equal to the current limit must wait until a later query with a larger limit.

For several queries with the same limit, the eligible graph is identical. The first query at that limit advances the edge pointer; subsequent queries reuse the same components. Their internal order does not affect the results. Sorting the queries is safe because each asks about the original graph independently and does not change it.

## Optimal solution, traced

```steps
Edges sorted by weight: 0-1 weight 2, 1-2 weight 5
Queries in input order: (0,2,6), (0,2,5)
---
Process the smaller limit 5 first. Add weight 2, not weight 5
    components {0, 1} {2}    answer at index 1: {{false}}
---
Process limit 6. Add the edge of weight 5
    components {0, 1, 2}    answer at index 0: {{true}}
---
Return results in input order
    {{[true, false]}}
```

Immediately before a query at limit `L`, every edge with weight below `L` has been added and no edge of weight `L` or more has been added. This holds initially and is preserved as the sorted query limits increase. Union-find therefore describes exactly the connected components of the graph allowed for that query.

The ordering is an offline optimisation, not a change to the query. If answers must be produced online before future queries are known, this single forward sweep may not be usable: a later query might have a smaller limit and ordinary union-find cannot undo previously added edges.

## Code

```python
def limited_paths(n, edges, queries):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    ordered_edges = sorted(edges, key=lambda edge: edge[2])
    order = sorted(range(len(queries)), key=lambda i: queries[i][2])
    answer = [False] * len(queries)
    edge_index = 0
    for i in order:
        u, v, limit = queries[i]
        while edge_index < len(ordered_edges) and ordered_edges[edge_index][2] < limit:
            a, b, _ = ordered_edges[edge_index]
            ra, rb = find(a), find(b)
            if ra != rb:
                if size[ra] < size[rb]:
                    ra, rb = rb, ra
                parent[rb] = ra
                size[ra] += size[rb]
            edge_index += 1
        answer[i] = find(u) == find(v)
    return answer
```

## Complexity

Sorting costs O(E log E + Q log Q). Each edge is considered once and each query performs two finds, for O((E + Q) α(V)) amortised union-find work. Initialisation costs O(V). The sorted edge copy, query indices, answer list, and forest require O(E + Q + V) space.

## Mistakes and edge cases

- Use `< limit`, not `<= limit`; equal-weight edges are excluded.
- Preserve the original query index when sorting.
- Multiple edges between the same vertices and cycles are harmless; an already-connected pair needs no merge.
- A query from a vertex to itself is true even when no edge qualifies.
- Do not sort the caller's edge list in place unless mutation is permitted.

## Variations

- Change the condition to weights at most the limit; only the comparison in the sweep changes.
- Report the number of components available at each threshold instead of testing a pair.
- Explore maximum-edge-on-path queries using a minimum spanning forest and binary lifting.

=== card | 1489
time: 45 min

## The problem

For a connected weighted undirected graph, classify its edges by their role in minimum spanning trees. An edge is **critical** if every minimum spanning tree needs it. An edge is **pseudo-critical** if at least one minimum spanning tree uses it, but it is not critical. Return the original indices of both groups; edges in neither group are omitted.

For a triangle with weights 1, 2 and 3, the first two edges are critical and the third is in no minimum spanning tree. For a triangle whose three weights are all 1, each edge is pseudo-critical: any two form a minimum spanning tree, and none is required in every one.

## Constraints and what they imply

The graph is connected, but equal edge weights may give many minimum spanning trees. Edges have stable input indices that must survive sorting. The task's moderate edge count makes it practical to run a minimum-spanning-tree algorithm repeatedly, rather than trying to enumerate all trees. Parallel alternatives and ties must be classified by their effect on the *minimum total weight*, not by whether one arbitrary run selected them.

## Brute force

Enumerate every set of `V - 1` edges, retain connected sets, compute the minimum weight, then examine the membership of each edge across all minimum sets. This is a useful oracle on tiny graphs, but the number of combinations grows rapidly with the number of edges. Enumerating all minimum trees is the bottleneck, especially when many equal-weight choices exist.

## The insight

Find the baseline minimum spanning tree weight `W` with Kruskal. For each edge `e`, run Kruskal without it. If the graph becomes disconnected or the best weight rises above `W`, no minimum tree avoids `e`, so it is critical.

Otherwise, run Kruskal with `e` forced in first. If the resulting best spanning tree still has weight `W`, at least one minimum tree contains `e`, so it is pseudo-critical. If the weight is higher, `e` belongs to no minimum tree. Check criticality first, so an edge that is mandatory is not also put in the second group.

Forcing an edge means contracting its endpoints before selecting the other edges. Kruskal then finds the cheapest completion of that fixed edge: a cycle is still avoided by the same union-find check.

If exclusion disconnects the graph, treat its best weight as infinity. That makes the same comparison work for a bridge, without confusing a disconnected forest with a valid spanning tree. The baseline exists because the task promises a connected input.

## Optimal solution, traced

```steps
Triangle AB 1, BC 1, AC 1: baseline Kruskal weight
    W = {{2}}
---
Omit AB. BC and AC still connect all vertices at weight 2
    AB is not critical
---
Force AB, then add the cheapest connecting edge
    weight {{2}}    AB is pseudo-critical
---
The same reasoning applies to BC and AC
    critical []    pseudo-critical [AB, BC, AC]
```

The exclusion test asks whether any optimum can avoid the edge. The inclusion test asks whether any optimum can contain it. These are exactly the definitions, so the two tests are both necessary and sufficient.

## Code

```python
def classify_mst_edges(n, edges):
    ordered = sorted(range(len(edges)), key=lambda i: edges[i][2])

    def mst(skip=-1, force=-1):
        parent = list(range(n))
        size = [1] * n

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(u, v):
            a, b = find(u), find(v)
            if a == b:
                return False
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
            return True

        total = 0
        used = 0
        if force != -1:
            u, v, weight = edges[force]
            if not union(u, v):
                return float("inf")
            total += weight
            used += 1
        for i in ordered:
            if i == skip or i == force:
                continue
            u, v, weight = edges[i]
            if union(u, v):
                total += weight
                used += 1
                if used == n - 1:
                    break
        return total if used == n - 1 else float("inf")

    baseline = mst()
    critical, pseudo = [], []
    for i in range(len(edges)):
        if mst(skip=i) > baseline:
            critical.append(i)
        elif mst(force=i) == baseline:
            pseudo.append(i)
    return [critical, pseudo]
```

## Complexity

Sorting `E` indices once costs O(E log E). Each of at most `2E + 1` Kruskal runs initialises O(V) state and scans at most `E` edges, costing O(E(V + E α(V))) total after sorting. The graph, ordered indices, and one union-find use O(V + E) auxiliary space. This is suitable for the problem's moderate input, not a claim that the repeated algorithm is optimal for arbitrarily large graphs.

## Mistakes and edge cases

- Record original indices before sorting, and distinguish parallel edges by index.
- A failed exclusion run has infinite cost; it makes the excluded edge critical.
- Equal weights do not automatically make an edge pseudo-critical: forcing it must still permit the baseline weight.
- Use a fresh union-find for every run. A forest from the previous test has the wrong connectivity.

## Variations

- Return one actual minimum spanning tree as well as the classifications.
- Test a small graph by enumerating every spanning tree and comparing edge membership.
- Investigate faster classification by processing equal-weight groups and finding bridges in the contracted graph.

=== card | 2421
time: 45 min

## The problem

Each vertex of an undirected tree has a value. Count paths whose two endpoints have equal values and whose internal vertices have values no greater than the endpoint value. Every one-vertex path counts. A path and its reverse are the same path.

For the chain with values `[1, 2, 1]`, the three single-vertex paths count, but the path between the two 1-valued vertices does not: it passes through a 2. If the values are `[2, 1, 2]`, that longer path also counts, giving four.

## Constraints and what they imply

The input is a tree, so each pair of vertices has exactly one simple path. Directly examining every pair requires quadratically many candidate paths, and following a path for every pair adds more work. Equal-valued vertices can be processed together: for a fixed value `v`, a path is valid exactly when its endpoints both have value `v` and it stays within vertices of value at most `v`.

## Brute force

For every unordered pair of vertices with matching values, search for the unique tree path and check its maximum value. Add one for each single vertex. There are O(n²) pairs and a graph search may take O(n), for O(n³) time in a straightforward implementation. Repeatedly discovering paths between the same regions is the bottleneck.

## The insight

Process distinct values in increasing order. When considering value `v`, activate each vertex of value `v` and union it with neighbours whose values are at most `v`. Vertices connected in this union-find are exactly those connected through the subgraph induced by values at most `v`.

Within one component, if `c` vertices have value `v`, each unordered pair of those vertices gives a valid path, contributing `c(c-1)/2`. Count these pairs for all components and values, then add the `n` singleton paths.

Process *all* vertices with value `v` and their eligible edges before counting that value. Counting too early misses paths that join two equal-valued vertices through another vertex of the same value.

## Optimal solution, traced

```steps
Chain values 2 - 1 - 2. Start with 3 singleton paths
    answer {{3}}
---
At value 1, the middle vertex has no active neighbours
    no equal-value pair; answer 3
---
At value 2, activate both ends and union both edges
    the two value-2 vertices share one root
---
There are 2 endpoints of value 2 in that component
    add 2*1/2 = 1; answer {{4}}
```

After processing value `v`, every edge with both endpoints at most `v` has been joined: its higher-valued endpoint, or either endpoint in a tie, processed it. No edge touching a higher-valued vertex was joined. Thus each DSU component matches one component of the allowed subgraph. In a tree, two vertices share such a component exactly when their unique path stays inside it, proving that the counted pairs are precisely the valid non-singleton paths.

Each pair is counted once, at its endpoints' common value. The singleton paths are included separately, so they cannot be accidentally counted twice.

Vertices with different endpoint values never form a qualifying pair, even if they are in the same allowed component. That is why the counter collects only vertices in the current value group, rather than counting all vertices in the component.

## Code

```python
from collections import Counter
from itertools import groupby


def count_good_paths(values, edges):
    n = len(values)
    neighbours = [[] for _ in range(n)]
    for u, v in edges:
        neighbours[u].append(v)
        neighbours[v].append(u)
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(u, v):
        a, b = find(u), find(v)
        if a == b:
            return
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]

    order = sorted(range(n), key=values.__getitem__)
    answer = n
    for value, group in groupby(order, key=values.__getitem__):
        nodes = list(group)
        for u in nodes:
            for v in neighbours[u]:
                if values[v] <= value:
                    union(u, v)
        counts = Counter(find(u) for u in nodes)
        answer += sum(c * (c - 1) // 2 for c in counts.values())
    return answer
```

## Complexity

Sorting the `n` vertices takes O(n log n). Every adjacency entry is inspected once when its vertex is processed; for a tree there are `2(n - 1)` entries. Union-find work costs O(n α(n)) amortised time, and counting roots adds O(n) expected dictionary operations. The adjacency lists, ordering, forest and per-value counters use O(n) auxiliary space.

## Mistakes and edge cases

- Union all edges eligible at the current value before counting equal-value vertices.
- Count combinations `c(c-1)/2`, not ordered pairs, and separately include the `n` singleton paths.
- A higher-valued internal vertex blocks a path between lower-valued endpoints.
- The proof uses the tree's unique path; counting distinct paths in a general cyclic graph is a different problem.

## Variations

- Return how many good paths have each endpoint value.
- For a tiny tree, enumerate all vertex pairs and verify the maximum on their unique paths.
- Instead count pairs connected under each supplied value threshold.
