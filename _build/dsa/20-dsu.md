---
key: dsu
name: Union-find and minimum spanning trees
stage: network
summary: Keep groups that only ever merge with near-constant work per operation, recognise the problems that reduce to merging groups, and connect everything at least total cost with Kruskal's and Prim's algorithms.
why: Many questions are about groups that grow: which computers can talk, which accounts belong to one person, which pixels form one object, which variables must be equal. Union-find answers "are these in the same group?" while groups keep merging, with effectively constant work per question and about twenty lines of code, where a fresh graph search per question would walk the whole graph every time. The same structure drives Kruskal's minimum spanning tree, the classic way to connect everything at least cost, and it runs inside image-processing libraries, graph libraries, clustering code and type checkers.
outcomes:
- Specify union-find (find, union, connected, count) and decide when it beats BFS or DFS
- Implement union by size with path compression from memory and explain why the trees stay shallow
- Reduce problems to merging groups: component counts, cycle-closing edges, shared attributes, equality constraints, two kinds of element
- Carry ratios or offsets along union-find links to answer "a / c" style queries
- Answer threshold queries and deletions offline by reordering time so edges are only ever added
- Build minimum spanning trees with Kruskal, heap-based Prim and dense Prim, and justify the greedy choice with the cut property
cues:
- "Are these two connected?" asked many times while connections keep being added
- Things that become "the same" transitively: shared emails, equal variables, swaps that can be repeated, stones sharing a row or column
- "Which edge, if removed, makes it a tree again?" or "the first connection that creates a loop"
- "Connect all points, cities or offices with minimum total cost"
traps:
- Testing parent[a] == parent[b] instead of find(a) == find(b)
- Comparing or updating the size of a non-root, which silently breaks union by size
- Using union-find for directed reachability; it only models symmetric relations
- Treating a minimum spanning tree as a shortest-path tree; they answer different questions
- Recursive find without union by size on a long chain, which exceeds Python's recursion limit
systems:
- scikit-image's measure.label (connected-component labelling) cites Fiorio and Gustedt's 'Two linear time Union-Find strategies for image processing' and Wu, Otoo and Shoshani's work on optimising labelling
- NetworkX builds Kruskal's minimum spanning tree with its UnionFind class, which compresses paths and merges the lighter set into the heavier one
- SciPy ships scipy.cluster.hierarchy.DisjointSet "for incremental connectivity queries", and its single-linkage clustering uses a minimum spanning tree algorithm
- Type inference in the ML family is classically implemented with union-find: unifying two type variables merges their sets
further:
- Article · 30 min | Sedgewick and Wayne, Algorithms 1.5: Case study, union-find (quick-find to weighted quick-union with path compression) | https://algs4.cs.princeton.edu/15uf/
- Article · 20 min | cp-algorithms: Disjoint set union, from path compression to the complexity section | https://cp-algorithms.com/data_structures/disjoint_set_union.html#path-compression-optimization
- Chapter · 40 min | Erickson, Algorithms ch. 7: the only MST algorithm, Prim and Kruskal (PDF pages 3-12) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/07-mst.pdf#page=3
- Visualisation · 10 min | VisuAlgo: Union-find disjoint sets, watch path compression flatten the trees | https://visualgo.net/en/ufds
bank: dsu
---

=== primer | When do you need union-find instead of a graph search? | 12 min
goal: State the union-find interface, recognise "merge groups, then ask about them" problems, and choose between union-find and BFS or DFS by how the edges and questions arrive
tag: dsu-connect | Dynamic connectivity
link: Sedgewick and Wayne: 1.5 Case study, union-find | https://algs4.cs.princeton.edu/15uf/ | 15 min: the opening 'Dynamic connectivity' problem and API, then 'Quick-find'; stop at 'Quick-union' (the next card covers it)
practice: 547, cses:1676

> [!key]
> **Union-find** (disjoint set union, DSU) keeps items in groups that only ever merge. `union(a, b)` merges the groups of a and b; `find(x)` returns a representative of x's group, so `connected(a, b)` is `find(a) == find(b)`. When connections keep arriving and "are these connected?" questions arrive in between, it answers each one in effectively constant time, where a BFS per question costs O(V + E). For a fixed graph asked once, plain BFS or DFS is just as good.

## Intuition

Think of clubs that merge. Every club has a president. To check whether two people are in the same club, ask each for their president and compare. When two clubs merge, one president steps down and reports to the other. Nobody ever needs a map of who knows whom; they only need to know who represents their group.

That is the trade union-find makes: it forgets the edges and remembers only the grouping. It cannot tell you a path or a distance, but "same group or not?" becomes cheap.

## How it works

### The interface

| Operation | Meaning |
|---|---|
| `find(x)` | the representative of x's group (any fixed member) |
| `union(a, b)` | merge the groups of a and b; return False if they were already one group |
| `connected(a, b)` | `find(a) == find(b)` |
| `count` | number of groups: starts at n, drops by one per successful union |
| `size(x)` | how many items share x's group (optional, for "largest group" questions) |

"Connected" here must be an **equivalence relation**: every item is connected to itself, a ~ b implies b ~ a, and a ~ b with b ~ c implies a ~ c. Undirected connectivity, "same person", "equal variables" all qualify. Directed reachability does not: a -> b does not give b -> a, so union-find cannot model it.

### Two simple implementations

- **Slow but obviously right**: keep the edges and answer each question with a DFS. This is your oracle for testing.
- **Quick-find**: store, for every item, the name of its group (`id[x]`). `find` is a single lookup; `union` relabels every member of one group, which scans the whole array: O(n) per union. With n unions that is O(n^2), too slow for 10^5 items, which is why the next card stores groups as trees instead.

### Union-find or a graph search?

| Situation | Use |
|---|---|
| Fixed graph, a few questions | one BFS or DFS labelling all components, O(V + E), then O(1) per question |
| Edges keep arriving, questions in between ("online") | union-find |
| You need the path itself or a distance | BFS |
| Directed edges, "can a reach b?" | BFS or DFS; union-find does not apply |
| Edges are deleted | neither directly; if all deletions are known in advance, replay them backwards as additions (a later card) |
| "Would this edge close a cycle?" (Kruskal, redundant edges) | union-find: the edge closes a cycle exactly when its ends are already connected |

## Cost

The search oracle costs O(V + E) per question, so Q questions after E edges cost O(Q (V + E)): with 10^5 of each, about 10^10 steps. Quick-find costs O(1) per find and O(n) per union. The structure in the next card costs O(alpha(n)) amortised per operation, where alpha is at most 4 for any n that fits in a computer: about 10^5 cheap steps for the same workload.

## When to use it

- "After each new road, how many groups are there, and how big is the largest?"
- "Do these two belong together?" when belonging is transitive and links only accumulate.
- The edge list is huge or arrives as a stream, and you never need paths.
- Not when you need distances, paths or directions, and not when links can be removed in an order you do not know in advance.

## Worked trace

Six people, numbered 0 to 5. Quick-find stores each person's group name in `id`.

```steps
Start: everyone is alone, so there are 6 groups
    id      0  1  2  3  4  5
    groups  {0} {1} {2} {3} {4} {5}     count 6
---
union(0, 1): relabel group 0 as group 1
    id      {{1}}  1  2  3  4  5
    groups  {0,1} {2} {3} {4} {5}       count {{5}}
---
union(2, 3), then connected(1, 2)? id[1] = 1 and id[2] = 3 differ: {{False}}
    id      1  1  {{3}}  3  4  5
    groups  {0,1} {2,3} {4} {5}         count 4
---
union(1, 3): every item labelled 1 becomes 3; this full scan is quick-find's weakness
    id      {{3}}  {{3}}  3  3  4  5
    groups  {0,1,2,3} {4} {5}           count {{3}}
---
connected(0, 2)? id[0] = id[2] = 3: {{True}}, although 0 and 2 were never joined directly
    id      3  3  3  3  4  5
---
union(4, 5), then union(0, 3): already one group, so it returns False and count stays 2
    id      3  3  3  3  {{5}}  5
    groups  {0,1,2,3} {4,5}             count {{2}}
```

## Template

```python
class SlowConnectivity:
    """Reference oracle: keep the edges, answer each question with a fresh DFS. O(V + E) per question."""

    def __init__(self, n):
        self.adj = [[] for _ in range(n)]

    def union(self, a, b):
        self.adj[a].append(b)
        self.adj[b].append(a)

    def connected(self, a, b):
        seen, stack = {a}, [a]
        while stack:
            u = stack.pop()
            if u == b:
                return True
            for v in self.adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        return False


class QuickFind:
    """Each item stores its group's name: find is O(1), union relabels a whole group in O(n)."""

    def __init__(self, n):
        self.id = list(range(n))
        self.count = n

    def find(self, x):
        return self.id[x]

    def union(self, a, b):
        ia, ib = self.id[a], self.id[b]
        if ia == ib:
            return False
        self.id = [ib if g == ia else g for g in self.id]
        self.count -= 1
        return True
```

## Pitfalls

- **Directed problems**: "a follows b" is not symmetric; union-find would wrongly let b reach a.
- **Counting every union call**: decrement `count` only when `union` actually merges (returns True).
- **Re-running BFS per question**: correct but O(Q (V + E)), the classic time-limit failure.
- **Expecting paths**: union-find knows that a path exists, never which one.
- **1-based labels** (CSES, many inputs): allocate n + 1 items or subtract one.

## Check yourself

Q: Continue the trace: after the last step, call union(3, 4). What is `id`, and what is the count?
A: id[3] = 3 and id[4] = 5 differ, so every 3 becomes 5: `id = [5, 5, 5, 5, 5, 5]` and the count drops to 1.

Q: Why can union-find not answer "can a reach b?" in a directed graph?
A: Union-find maintains an equivalence relation: after union(a, b), a and b are interchangeable. Directed reachability is not symmetric (a -> b does not mean b -> a), so merging a and b would claim b reaches a. Directed questions need a search, or strongly connected components for "mutually reachable".

Q: A road network is fixed and you get 10^5 questions "are cities x and y connected?". Union-find, or something simpler?
A: Either works, but the simplest is one BFS or DFS labelling every component (O(V + E)), then each question compares two labels in O(1). Union-find shines when roads are added between questions.

Q: A colleague's code decrements `count` on every call to `union`. For unions (0, 1), (1, 0), (2, 3) on 4 items, what does it report, and what is right?
A: It reports 4 - 3 = 1 group. The second union merges nothing, so the right answer is 2 groups ({0, 1} and {2, 3}). Decrement only when the two roots differ.

## Lab

- **547 Number of Provinces.** Union every pair (i, j) with `isConnected[i][j] = 1` and report the number of groups (or use one DFS labelling, since the graph is fixed). Expected: O(n^2) to read the matrix; `[[1,1,0,0],[1,1,0,0],[0,0,1,1],[0,0,1,1]]` gives 2, the identity matrix of size 3 gives 3.
- **cses:1676 Road Construction.** Roads arrive one per day; after each, print the number of components and the size of the largest. This is the online case union-find exists for: keep `count` and the size of each root, and update the maximum after every merge. Expected: O((n + m) alpha(n)); for 5 cities and roads (1, 2), (1, 3), (4, 5) the output lines are `4 2`, `3 3`, `2 3`.

> [!know]
> You now know what union-find promises, how to test it against a slow oracle, and when it beats running a graph search again.

=== primer | How do path compression and union by size make union-find almost O(1)? | 15 min
goal: Implement union-find as a forest of parent pointers with union by size and path compression, prove that union by size keeps trees at most log2 n tall, and reproduce the 25-line template from memory
tag: dsu-template | Union-find with size and compression
link: cp-algorithms: Disjoint set union | https://cp-algorithms.com/data_structures/disjoint_set_union.html#path-compression-optimization | 15 min: 'Path compression optimization', 'Union by size / rank' and 'Time complexity' (what the inverse Ackermann bound means)
link: Erickson: Disjoint sets (lecture notes) | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/11-unionfind.pdf#page=4 | optional, 20 min: union by rank and path compression with their analysis (PDF pages 4-6)
practice: 547

> [!key]
> Store each group as a **tree of parent pointers**; the root is the representative, and `find` climbs to it. **Union by size** hangs the root of the smaller tree under the root of the larger one, so no tree is ever taller than log2 n. **Path compression** makes every node visited by `find` point straight at the root, so later finds are shorter still. Together, any m operations on n items take O(m alpha(n)) time, where alpha (the inverse Ackermann function) is at most 4 for every n you will ever store.

## Intuition

A company org chart: to learn who runs your company, ask your manager, who asks theirs, up to the chief executive. When two companies merge, the smaller one's chief reports to the larger one's chief, which adds one level for the fewer people. And after you have walked up the chain once, you write down the chief's name so next time you go straight there. Those two habits are union by size and path compression.

## How it works

### Quick-union: groups as trees

`parent[x]` is x's parent, and a root is its own parent. `find(x)` follows parents to the root. `union(a, b)` finds both roots and makes one the parent of the other. Union is now cheap, but nothing stops a bad sequence of unions from building a chain: then `find` walks n steps. Linking 0 -> 1 -> 2 -> ... -> 7999 and calling `find(0)` 8,000 times takes about 5 seconds in Python.

### Union by size

Keep `size[root]` = number of items in the tree, and always attach the smaller root under the larger. **Claim**: every tree of height h has at least 2^h items, so heights never exceed log2 n. **Proof**: a node's depth grows by one only when its root is attached under another root, and that happens only when its tree is the smaller (or equal) one, so the merged tree has at least twice as many items as the node's old tree. A tree that doubles at most log2 n times before containing all n items lets any node move down at most log2 n times. **Union by rank** (attach by an upper bound on height) gives the same guarantee; size has the bonus of answering "how big is this group?".

### Path compression

During `find(x)`, after reaching the root, walk the path again and set every parent to the root. The work is at most twice the climb, and the next find from any of those nodes takes one step. A popular one-pass variant, **path halving**, sets each node's parent to its grandparent as you climb: `parent[x] = parent[parent[x]]`. Both give the same bound.

### Why "almost O(1)"

With both rules, Tarjan proved that m operations take O(m alpha(n)) in the worst case. alpha(n) grows so slowly that it is at most 4 for any n below a number with far more digits than there are atoms in the universe. Treat each operation as constant time; the proof is beyond this guide. Either rule alone already gives O(log n): union by size bounds height in the worst case, and path compression alone gives O(log n) amortised.

## Cost

| Version | find | union | n unions + n finds |
|---|---|---|---|
| Quick-find | O(1) | O(n) | O(n^2) |
| Quick-union | O(height), up to n | O(height) | O(n^2) on a chain |
| Union by size | O(log n) | O(log n) | O(n log n) |
| Size + compression | O(alpha(n)) amortised | O(alpha(n)) amortised | O(n alpha(n)), effectively linear |

Space is two integer arrays of length n. In Python, plain lists of ints are fine up to millions of items.

## When to use it

Always use both rules: each is two or three lines, and together they remove any need to think about adversarial input. If you need the size of every group, union by size gives it for free. Use the iterative `find` below; a recursive one is safe only when union by size bounds the depth (log2 of a million is 20), and on a long chain without it Python raises `RecursionError`.

## Worked trace

Eight items. Union by size breaks ties by keeping the first root. Parent arrays are shown after each operation; roots have `parent[x] = x`.

```steps
Start: eight trees of one node
    index   0  1  2  3  4  5  6  7
    parent  0  1  2  3  4  5  6  7
---
union(0, 1), union(2, 3): sizes tie, so 1 goes under 0 and 3 under 2
    parent  0  {{0}}  2  {{2}}  4  5  6  7
    size    root 0: 2   root 2: 2
---
union(0, 2): roots 0 and 2 both have size 2; 2 goes under 0, size of 0 becomes 4
    parent  0  0  {{0}}  2  4  5  6  7
---
union(4, 5), union(6, 7), union(4, 6): the same shape on the right half
    parent  0  0  0  2  4  {{4}}  {{4}}  {{6}}
    size    root 0: 4   root 4: 4
---
union(0, 4): sizes 4 and 4, so 4 goes under 0. The deepest node, 7, is 3 levels down: log2 8 = 3, the bound is tight
    parent  0  0  0  2  {{0}}  4  4  6
            0
          / | \
         1  2  4
            |  | \
            3  5  6
                  |
                  7
---
find(7): climb 7 -> 6 -> 4 -> 0, then point 7 and 6 straight at the root
    parent  0  0  0  2  0  4  {{0}}  {{0}}
            0
       / /  |  \  \
      1 2   4   6  7
        |   |
        3   5
---
find(5): climb 5 -> 4 -> 0 and compress; every later find from 5, 6 or 7 takes one step
    parent  0  0  0  2  0  {{0}}  0  0
```

## Template

```python
class DSU:
    """Disjoint sets over 0..n-1 with union by size and path compression."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.count = n                      # number of groups

    def find(self, x):
        root = x
        while self.parent[root] != root:    # climb to the root
            root = self.parent[root]
        while x != root:                    # second pass: point the path at the root
            nxt = self.parent[x]
            self.parent[x] = root
            x = nxt
        return root

    def union(self, a, b):
        """Merge the groups of a and b; False if they were already one group."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra                 # ra is the larger root
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.count -= 1
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)
```

For labels that are not 0..n-1 (strings, tuples), map each label to an integer the first time you see it (`ids.setdefault(label, len(ids))`) and grow the lists, or use dicts for `parent` and `size`.

## Pitfalls

- **`parent[a] == parent[b]`** as the connectivity test: two nodes can share a root without sharing a parent. Always compare `find(a)` and `find(b)`.
- **Sizes of non-roots**: compare and update `size` only at roots (`size[ra]`, not `size[a]`).
- **Linking the wrong way**: `parent[ra] = rb` after swapping so that ra is larger undoes union by size.
- **Recursive find** on deep trees without union by size: RecursionError at depth 1,000.
- **Reading groups too early**: `find(i)` is only final after all unions; group items in a separate pass at the end.

## Check yourself

Q: After the trace's last step, call union(3, 7). What happens to the parent array?
A: find(3) climbs 3 -> 2 -> 0 and compresses 3 to point at 0; find(7) is 0 already. The roots are equal, so union returns False and nothing else changes: `parent = [0, 0, 0, 0, 0, 0, 0, 0]`.

Q: Prove that with union by size, a node's depth increases at most log2 n times.
A: Its depth increases only when its root is attached under another root, which union by size does only if its tree is no larger than the other. The new tree is then at least twice the size of the node's old tree. Sizes start at 1 and never exceed n, so this can happen at most log2 n times.

Q: You need union-find over email addresses, with up to a million distinct emails. Dicts keyed by email, or integer ids?
A: Either is correct. Integer ids (assign each new email `len(ids)` in a dict, then use lists) keep the hot loop on list indexing, which is faster and smaller than dicts in Python; dicts keyed by email are simpler to write. Both keep the near-constant cost per operation.

Q: This find is meant to compress paths: `while parent[x] != x: x = parent[x]; parent[x] = x`. What does `find(7)` do on the tree from the trace before compression (7 -> 6 -> 4 -> 0)?
A: It steps from 7 to 6 and then sets `parent[6] = 6`, turning 6 into a root, so the loop stops and returns 6. It has cut 6 and 7 out of their group, and later queries will say 7 and 0 are not connected. Compression must point the path nodes at the root found at the end (the template's second pass), or at their grandparents (`parent[x] = parent[parent[x]]` before stepping).

## Lab

- **547 Number of Provinces.** Use the DSU template: union every connected pair and return `count`. Expected: O(n^2 alpha(n)); for `[[1,1,0,0],[1,1,0,0],[0,0,1,1],[0,0,1,1]]` the answer is 2.
- **Feel the difference (no submission).** Link a chain with plain quick-union (`parent[find(i)] = find(i + 1)` for i = 0 .. n - 2), then call `find(0)` n times; repeat with the DSU class. Time both for n = 2,000, 4,000 and 8,000. Expected: quick-union takes about 0.25 s, 1.2 s and 5 s (each doubling multiplies the time by about 4: quadratic), while the DSU stays near 0.01 s throughout.

> [!know]
> You now know how union by size and path compression keep union-find trees flat, and you can write the template from memory.

=== primer | What problems become easy once you can merge groups? | 15 min
goal: Recognise the union-find patterns (counting groups, the edge that closes a cycle, grouping by shared attributes, equalities before inequalities, rearranging within groups, two kinds of element) and choose what to union
tag: dsu-groups | Grouping with union-find
link: cp-algorithms: Disjoint set union, applications | https://cp-algorithms.com/data_structures/disjoint_set_union.html#connected-components-in-a-graph | 10 min: 'Connected components in a graph' and 'Search for connected components in an image', then skim the rest of the applications list for the variety of uses
practice: 990, 721, 947

> [!key]
> Many problems are "link things that belong together, directly or through a chain, then answer a question per group". Union every linked pair, then read the groups off the roots: count them, find the link that was already redundant, check that forbidden pairs ended up apart, or rearrange freely inside each group. The decisive step is **choosing the elements and the links**: cities, accounts, letters, positions, or even rows and columns.

## Intuition

A fraud analyst sees that account A and account B used the same phone number, and B and C used the same email. A and C never shared anything, yet all three are one person. Linking is transitive, which is exactly what union-find maintains: union every pair that shares something, and the groups appear by themselves, however long the chains are.

## How it works

### Count the groups

Start with n groups; every successful union removes one. "How many friend circles?", "how many provinces?". Variant: n computers and some cables; each spare cable (one whose ends are already connected) can be moved, and joining g groups needs g - 1 cables.

### The edge that closes a cycle

Process edges in order. `union(u, v)` returns False exactly when u and v were already connected, so that edge closes a cycle. The first such edge is redundant. A graph on n vertices is a **tree** exactly when it has n - 1 edges and no union fails.

### Group by shared attributes

Records (accounts, people, documents) are linked when they share any attribute (email, phone, hash). Do not compare all pairs of records. Keep a dict from attribute to the first record that had it; when a later record has the same attribute, union the two records. Each attribute is touched once.

### Equalities first, then inequalities

Constraints like `a == b` and `b != c`: union all equalities, and only then check that every inequality joins two different groups. Checking an inequality before all equalities are merged can miss a contradiction created later.

### Rearrange freely within a group

If positions i and j may be swapped any number of times, then within a connected group of positions any permutation is reachable. So "smallest string after swaps" is: group the positions, then sort the characters of each group onto that group's sorted positions.

### Two kinds of element

Stones on a grid are linked when they share a row or a column. Instead of comparing stones pairwise, treat **rows and columns as the elements** and let each stone union its row with its column (offset column ids, or use tuples like `('r', 3)` and `('c', 3)`). Each group of stones can be removed down to a single stone (remove leaves of a spanning tree first), so the answer is stones minus groups.

## Cost

Each pattern is a pass over the input with O(alpha(n)) per union and find: effectively O(n + m) for n elements and m links, plus any sorting the question needs (for example sorting each account's emails). Grouping by attributes is linear in the total number of attributes, against O(n^2) for comparing all pairs of records.

## When to use it

| Statement shape | Elements | Union | Then |
|---|---|---|---|
| Friend circles, provinces, networks | people or nodes | each link | `count` |
| "Which edge makes it no longer a tree?" | vertices | each edge in order | first union that returns False |
| Merge accounts sharing an email | records | record with first owner of each attribute | group by root, sort |
| `a==b`, `b!=c` satisfiable? | variables | every `==` | each `!=` must join different roots |
| Swaps between index pairs, any number of times | positions | each pair | sort inside each group |
| Stones sharing a row or column | rows and columns | row with column per stone | stones minus groups |

Prefer DFS when the graph is fixed and you want the groups once (both are linear); prefer union-find when links arrive as a stream, when you need the first redundant link, or when building adjacency lists would be awkward (attributes, two kinds of element).

## Worked trace

Five customer records; records sharing an email or phone number are the same customer.

```steps
Records and their attributes. owner maps an attribute to the first record that had it
    0: a@x, 555     1: b@y     2: c@z, 555     3: b@y, d@w     4: e@v
    parent  0 1 2 3 4
    owner   {}
---
Record 0: a@x and 555 are new, so record 0 owns both
    owner   {a@x: 0, 555: 0}
    parent  0 1 2 3 4
---
Record 1 owns b@y. Record 2: c@z is new, but 555 belongs to record 0, so union(0, 2)
    owner   {a@x: 0, 555: 0, b@y: 1, c@z: 2}
    parent  0 1 {{0}} 3 4
---
Record 3: b@y belongs to record 1, so union(1, 3); d@w is new
    owner   {..., b@y: 1, d@w: 3}
    parent  0 1 0 {{1}} 4
---
Record 4: e@v is new. Group by find(i): three customers
    parent  0 1 0 1 4
    groups  {{{0, 2}}}  {{{1, 3}}}  {{{4}}}
```

## Template

```python
from collections import defaultdict

def group_records(records):
    """Groups of record indices; records sharing any attribute, directly or via a chain, are together."""
    dsu = DSU(len(records))                 # the class from the previous card
    owner = {}                              # attribute -> first record that had it
    for i, attrs in enumerate(records):
        for a in attrs:
            if a in owner:
                dsu.union(owner[a], i)
            else:
                owner[a] = i
    groups = defaultdict(list)
    for i in range(len(records)):           # read the groups only after every union
        groups[dsu.find(i)].append(i)
    return list(groups.values())


def is_tree(n, edges):
    """True if the undirected edges connect 0..n-1 with no cycle."""
    if len(edges) != n - 1:
        return False
    dsu = DSU(n)
    return all(dsu.union(u, v) for u, v in edges)
```

## Pitfalls

- **Comparing all pairs of records**: O(n^2) when one pass with an attribute dict is linear.
- **Inequalities checked too early**: process every equality first.
- **Namespace clashes**: row 3 and column 3 must be different elements; offset the columns or use tagged tuples.
- **Grouping by `parent[i]`** instead of `find(i)`: nodes deeper than one level land in the wrong group.
- **Forgetting isolated elements**: a record with unique attributes is still a group of one; a stone alone in its row and column still counts.
- **Sorting output wrongly**: when a problem wants emails sorted inside each account, sort the group, not the whole list.

## Check yourself

Q: Add a record 5 with attributes d@w and a@x to the trace. Which unions happen, and what are the groups?
A: d@w belongs to record 3, so union(3, 5) puts 5 into the group {1, 3}; a@x belongs to record 0, so union(0, 5) merges {0, 2} with {1, 3, 5}. The groups become {0, 1, 2, 3, 5} and {4}: two customers.

Q: Why must all equalities be merged before any inequality is checked?
A: An inequality `a != c` is violated only if a and c end up in the same group, and later equalities can still merge them (`a == b` then `b == c`). Checking `a != c` when it is first seen would pass, then the equalities would silently contradict it. After all merges the groups are final, so the check is exact.

Q: Stones at (0, 0), (0, 1), (1, 0) and (2, 2). How many can be removed if a stone may be removed only while another stone shares its row or column, and why is the formula stones minus groups?
A: The first three are linked (row 0 joins the first two, column 0 joins the first and third), (2, 2) is alone: 2 groups, so 4 - 2 = 2 removals. In each group you can remove stones in an order that always leaves a linked partner (leaves of a spanning tree first) until one remains, and the last stone of a group can never be removed because nothing outside its group shares its row or column.

Q: A solution builds groups with `groups[dsu.parent[i]].append(i)` after all unions. When does it give wrong groups?
A: Whenever some node's parent is not the root, for example a node two levels down whose path was never compressed. It is then grouped under its parent instead of its root and appears as a separate group. Use `dsu.find(i)`.

## Lab

- **990 Satisfiability of Equality Equations.** 26 letters as elements; union every `==`, then check every `!=`. Expected: O(n) for n equations; `["a==b","b!=c","c==a"]` gives `false`; `["a==b","b==c","a!=d"]` gives `true`.
- **721 Accounts Merge.** Union accounts that share an email (attribute dict), then output each group's name followed by its sorted emails. Expected: O(N log N) for N emails, dominated by sorting; accounts `[["Ann","a@x","b@x"],["Bob","bob@y"],["Ann","c@x","a@x"],["Ann","d@x"]]` merge into `["Ann","a@x","b@x","c@x"]`, `["Bob","bob@y"]` and `["Ann","d@x"]` (two different people can share a name).
- **947 Most Stones Removed with Same Row or Column (derive).** Union each stone's row with its column (column id offset past the largest row), count groups among the rows and columns actually used, and answer stones minus groups. Expected: O(n alpha(n)); `[[0,0],[0,1],[1,0],[2,2]]` gives 2.

> [!know]
> You now know how to spot "merge then ask" problems and choose the elements and links that turn them into a few unions.

=== primer | How do you keep ratios or offsets along union-find edges? | 13 min
goal: Extend union-find so each node stores its ratio (or offset) to its parent, keep those weights correct through path compression and union, and answer "a / c" or "a - c" queries or detect contradictions
tag: dsu-weighted | Weighted union-find
link: cp-algorithms: Disjoint set union | https://cp-algorithms.com/data_structures/disjoint_set_union.html#support-the-parity-of-the-path-length-checking-bipartiteness-online | 10 min: 'Support the parity of the path length / Checking bipartiteness online', the same idea with offsets modulo 2, plus the 'Support distances up to representative' section just above it
practice: 399

> [!key]
> Store with every node a **weight relative to its parent**: `w[x] = value(x) / value(parent(x))` for ratios (or a difference for offsets). The value of x relative to its root is then the **product of the weights along its path**, and path compression keeps that product as the node's new weight. To record `value(a) / value(b) = k`, find both roots and hang one under the other with the weight that makes the equation hold. Queries `a / c` are `w_a / w_c` when a and c share a root, and unknown otherwise.

## Intuition

Currency exchange. You know 1 euro buys 1.1 dollars and 1 dollar buys 150 yen. Pick one currency per group as the reference (the root) and remember each currency's value in reference units. Then any two currencies in the same group compare by dividing their reference values, however they were originally linked, and currencies in different groups simply cannot be compared.

## How it works

Write `val(x)` for the hidden value of x and keep `w[x] = val(x) / val(parent[x])`; a root has weight 1.

- **find(x)** climbs to the root r and returns `(r, val(x) / val(r))`, which is the product of the weights on the path. While compressing, each node on the path gets parent r and weight equal to its own product up to r. Process the path from the node nearest the root outwards, so each product extends the previous one by one factor.
- **union(a, b, k)** records `val(a) / val(b) = k`. Let `find(a) = (ra, wa)` and `find(b) = (rb, wb)`, so `val(a) = wa * val(ra)` and `val(b) = wb * val(rb)`. If ra and rb differ, set `parent[ra] = rb` and `w[ra] = val(ra) / val(rb) = (val(a) / wa) / (val(b) / wb) = k * wb / wa`. If they are equal, the equation is either implied (`wa / wb == k`) or a **contradiction**.
- **ratio(a, b)** is `wa / wb` when the roots agree; otherwise the equations do not determine it.

**Offsets** work the same way with sums instead of products: `d[x] = val(x) - val(parent[x])`, add along paths, and `d[ra] = k + db - da` for `val(a) - val(b) = k`. With offsets modulo 2 you get **parity union-find**, which checks online whether a growing graph is still bipartite: an edge u - v demands that u and v have different parity, and a contradiction means an odd cycle.

## Cost

Exactly the plain structure's cost plus one multiplication per step: O(alpha(n)) amortised per operation with union by size, and O(log n) amortised with path compression alone, which is what the short template below uses. Each query is two finds.

## When to use it

- "Given a / b = 2.0 and b / c = 3.0, what is a / c?" (ratios), unit conversions, exchange rates.
- "x is 3 more than y" constraints, relative positions, consistency checks on measurements (offsets).
- Online bipartiteness or "same or different" constraints (parity).
- Alternative for a handful of queries on a fixed set of equations: build a weighted graph and DFS from a to c multiplying edge ratios, O(V + E) per query. Weighted union-find wins when equations and queries interleave or queries are many.

## Worked trace

Equations a / b = 2, b / c = 3, d / e = 4, then queries, then one more equation. Each node shows `parent (weight)`.

```steps
union(a, b, 2): a's root a goes under b's root b with weight 2 * 1 / 1 = 2
    a: b (2)    b: b (1)    c: c (1)    d: d (1)    e: e (1)
---
union(b, c, 3): b goes under c with weight 3. Now a -> b -> c
    a: b (2)    b: {{c (3)}}    c: c (1)
---
union(d, e, 4): a separate group
    d: {{e (4)}}    e: e (1)
---
ratio(a, c): find(a) climbs a -> b -> c, multiplies 2 * 3 = 6 and compresses a straight onto c
    a: {{c (6)}}    b: c (3)    c: c (1)
    a / c = 6 / 1 = {{6.0}};  a / e: different roots, so {{unknown}}
---
union(c, e, 0.5): roots c and e differ; c goes under e with weight 0.5 * 1 / 1 = 0.5
    a: c (6)    b: c (3)    c: {{e (0.5)}}    d: e (4)    e: e (1)
---
ratio(a, d): find(a) = (e, 6 * 0.5 = 3) after compression; find(d) = (e, 4); answer 3 / 4
    a: {{e (3)}}    c: e (0.5)    d: e (4)
    a / d = {{0.75}}   (check: e = 1, d = 4, c = 0.5, b = 1.5, a = 3)
```

## Template

```python
class RatioDSU:
    """Variables linked by known ratios; ratio(a, b) = value(a) / value(b) when it is determined."""

    def __init__(self):
        self.parent = {}
        self.w = {}                         # w[x] = value(x) / value(parent[x])

    def find(self, x):
        """Root of x and value(x) / value(root), compressing the path."""
        if x not in self.parent:
            self.parent[x], self.w[x] = x, 1.0
        path = []
        while self.parent[x] != x:
            path.append(x)
            x = self.parent[x]
        ratio = 1.0
        for node in reversed(path):         # nearest the root first
            ratio *= self.w[node]           # now value(node) / value(root)
            self.parent[node], self.w[node] = x, ratio
        return x, ratio

    def union(self, a, b, k):
        """Record value(a) / value(b) = k; False if that contradicts what is already known."""
        ra, wa = self.find(a)
        rb, wb = self.find(b)
        if ra == rb:
            return abs(wa / wb - k) <= 1e-9 * max(1.0, abs(k))
        self.parent[ra] = rb
        self.w[ra] = k * wb / wa            # value(ra) / value(rb)
        return True

    def ratio(self, a, b):
        """value(a) / value(b), or None if the equations do not determine it."""
        if a not in self.parent or b not in self.parent:
            return None
        ra, wa = self.find(a)
        rb, wb = self.find(b)
        return wa / wb if ra == rb else None
```

## Pitfalls

- **Wrong direction of the new weight**: hanging ra under rb needs `val(ra) / val(rb)`, which is `k * wb / wa`, not `k * wa / wb`. Re-derive it from the definitions whenever you adapt the structure.
- **Compressing from the wrong end**: products must be built from the root outwards, or nodes get the wrong weight.
- **Exact float comparison** for contradictions: use a tolerance.
- **Unknown variables**: a variable never mentioned in any equation is not "1.0 divided by itself"; most problems want "unknown" (for example -1.0).
- **Forgetting that a query may introduce new keys**: `find` on an unseen key creates it, so check membership first, as `ratio` does.

## Check yourself

Q: After the trace, record `union(b, d, 0.375)`. Is it consistent, and what does union return?
A: find(b) = (e, 3 * 0.5 = 1.5) and find(d) = (e, 4), same root, so the ratio is already known: 1.5 / 4 = 0.375. It matches, so union returns True and changes nothing (apart from compressing b onto e).

Q: Why does hanging ra under rb use the weight k * wb / wa?
A: By definition `w[ra] = val(ra) / val(rb)`. From `val(a) = wa * val(ra)` and `val(b) = wb * val(rb)` we get `val(ra) / val(rb) = (val(a) / wa) / (val(b) / wb) = (val(a) / val(b)) * wb / wa = k * wb / wa`.

Q: Edges of a graph arrive one at a time; after each, you must say whether the graph is still bipartite. What do you store?
A: Parity union-find: each node stores its colour parity relative to its parent (0 or 1), summed modulo 2 along paths. Adding edge u - v requires different parities: if u and v share a root, check that their parities differ (otherwise an odd cycle has appeared); if not, link the roots with the parity that makes them differ.

## Lab

- **399 Evaluate Division (stretch).** Union each equation with its value, answer each query with `ratio` (or -1.0 when unknown or when either variable never appeared). Expected: O((E + Q) log n) with this template; equations `[["x","y"],["y","z"]]` with values `[4.0, 0.5]` and queries `[["x","z"],["z","x"],["x","w"],["y","y"]]` give `[2.0, 0.5, -1.0, 1.0]`.
- **Offsets instead of ratios.** Adapt the class to differences (`val(a) - val(b) = k`): start weights at 0, add along paths instead of multiplying, and use `d[ra] = k + db - da`. Expected: after `x - y = 3` and `y - z = 4`, the difference `x - z` is 7; recording `x - z = 8` then returns False (a contradiction), while `x - z = 7` returns True.

> [!know]
> You now know how to carry ratios, offsets or parities along union-find links and detect equations that contradict each other.

=== primer | How do you answer connectivity queries offline, or when edges are deleted? | 14 min
goal: Reorder time so that union-find only ever adds edges: sort edges and queries by a threshold and sweep, process deletions backwards as additions, and add vertices in value order
tag: dsu-offline | Offline union-find
link: cp-algorithms: Disjoint set union, painting subarrays offline | https://cp-algorithms.com/data_structures/disjoint_set_union.html#compress-jumps-along-a-segment-painting-subarrays-offline | 5 min: 'Compress jumps along a segment / Painting subarrays offline', another known-in-advance problem solved by processing the queries in reverse order with union-find
practice: 1697, 2421

> [!key]
> Union-find can only merge. When every question is known in advance (offline), you are free to answer them in any order, so choose an order in which the graph only grows: **sort the edges and the questions by their threshold** and add edges as the threshold rises, or **process deletions backwards**, so each deletion becomes an addition. Store each answer at its original index. The cost is one sort plus near-constant work per edge and question.

## Intuition

A flood plain at low tide: islands are separate. As the water level falls (or a "maximum bridge weight" rises), more connections appear and nothing ever disconnects. If you are asked "were A and B connected at level 5?", "at level 3?", "at level 9?", answer the questions in order of level while you watch the connections appear, then hand the answers back in the order they were asked.

Deletions are the same film played backwards: roads closing one by one, seen in reverse, are roads opening one by one.

## How it works

### Threshold sweep

Queries ask "are a and b connected using only edges lighter than L?". The set of usable edges grows with L, so:

1. Sort the edges by weight, and the query indices by L.
2. Walk the queries in increasing L, moving an edge pointer forward and unioning every edge lighter than the current L.
3. Answer with `find(a) == find(b)` and store it at the query's **original** index.

### Deletions in reverse

Given a graph and a list of edges removed one at a time, report the number of components after each removal. Build the final graph (all edges minus the removed ones), then walk the removals backwards: record the current component count, then add the removed edge back. Reverse the recorded list.

### Adding vertices in value order

"Count paths whose two ends have the largest value on the path": activate vertices in increasing value, and union each with already-active neighbours (all have value at most the current one). After processing a value, the vertices with that value in the same group can be paired with each other, because every vertex between them is no larger. Count k(k - 1) / 2 per group of k equal-valued vertices.

### Online alternatives

If a question can depend on the previous answer (forced online) and edges are deleted, union-find alone does not work. That needs fully dynamic connectivity structures, which are beyond this guide. For thresholds asked online, you can store a Kruskal tree or a persistent structure, also beyond scope.

## Cost

Sorting costs O(E log E + Q log Q). The sweep does at most E unions and Q pairs of finds: O((E + Q) alpha(V)). The deletion replay is O(E alpha(V)). Compare a fresh BFS per query: O(Q (V + E)), which is 10^10 steps with 10^5 of each.

## When to use it

- "For each query (a, b, limit), is there a path using only edges below the limit?" with all queries given up front.
- "After each removal, how many components / is it still connected?" with the removal list given up front.
- Counting pairs or paths controlled by a maximum or minimum value: process values in sorted order.
- Not when answers must be produced before the next question is revealed and edges can disappear.

## Worked trace

Edges 0-1 (weight 2), 1-2 (4), 2-3 (8), 0-3 (16). Queries "connected using edges lighter than L?": q0 = (0, 2, L 5), q1 = (0, 3, L 3), q2 = (1, 3, L 9), q3 = (0, 3, L 20).

```steps
Sort the queries by limit: q1 (3), q0 (5), q2 (9), q3 (20). Edges are already sorted by weight
    parent  0 1 2 3
    answer  [?, ?, ?, ?]
---
q1, limit 3: add every edge lighter than 3, which is 0-1 (2). Are 0 and 3 connected? No
    parent  0 {{0}} 2 3
    answer  [?, {{False}}, ?, ?]
---
q0, limit 5: add 1-2 (4). Are 0 and 2 connected? Yes
    parent  0 0 {{0}} 3
    answer  [{{True}}, False, ?, ?]
---
q2, limit 9: add 2-3 (8). Are 1 and 3 connected? Yes
    parent  0 0 0 {{0}}
    answer  [True, False, {{True}}, ?]
---
q3, limit 20: add 0-3 (16), which joins nothing new. Are 0 and 3 connected? Yes
    answer  [True, False, True, {{True}}]
---
Answers are already in the original order because each was stored at its own index
    answer  [True, False, True, True]
```

## Template

```python
def connected_below(n, edges, queries):
    """For each query (a, b, limit): are a and b joined by edges of weight < limit? edges are (u, v, w)."""
    dsu = DSU(n)                            # union by size + path compression, from the earlier card
    edges = sorted(edges, key=lambda e: e[2])
    answer = [False] * len(queries)
    j = 0
    for qi in sorted(range(len(queries)), key=lambda i: queries[i][2]):
        a, b, limit = queries[qi]
        while j < len(edges) and edges[j][2] < limit:
            dsu.union(edges[j][0], edges[j][1])
            j += 1
        answer[qi] = dsu.find(a) == dsu.find(b)
    return answer


def components_after_removals(n, edges, removals):
    """Component count after each removal; removals lists edge indices, each removed once, in order."""
    gone = set(removals)
    dsu = DSU(n)
    for i, (u, v) in enumerate(edges):
        if i not in gone:
            dsu.union(u, v)
    counts = []
    for i in reversed(removals):
        counts.append(dsu.count)            # the state just after removal i
        dsu.union(*edges[i])                # step back in time: the edge returns
    return counts[::-1]
```

## Pitfalls

- **Losing the original order**: sort indices, not the query list, or carry the index inside each query.
- **Strict versus non-strict limits**: "less than" and "at most" differ exactly when an edge weight equals the limit; match the statement in the `while` condition.
- **Recording after re-adding** in the deletion replay: record the count first, then add the edge back.
- **Assuming offline is allowed**: if the input says each query depends on the previous answer, reordering is cheating, not an optimisation.
- **Duplicate removals**: an edge removed twice breaks the replay; validate the input.

## Check yourself

Q: In the trace, add a query q4 = (0, 3, L 8). Where does it go in the sweep, and what is its answer?
A: Between q0 (5) and q2 (9). At that point the edges lighter than 8 are 0-1 and 1-2, so 0 and 3 are not connected yet (2-3 has weight 8, which is not below 8): answer False.

Q: Why is sorting the queries allowed, and why does it make union-find sufficient?
A: Each answer depends only on the set of edges below its limit, not on when it is asked. Sorted by limit, those sets only grow from one query to the next, so the structure needs only additions, which is all union-find supports.

Q: Edges of a 4-cycle 0-1, 1-2, 2-3, 3-0 are removed in the order 0-1, 2-3, 1-2. What counts does the replay produce?
A: The final graph keeps only 3-0: components {0, 3}, {1}, {2}, so 3 after the third removal. Add back 1-2: 2 components after the second removal. Add back 2-3: 1 component after the first removal (the cycle minus one edge is still connected). The result is [1, 2, 3].

## Lab

- **1697 Checking Existence of Edge Length Limited Paths (derive).** Exactly the threshold sweep: sort edges by length and queries by limit, union edges strictly shorter than each limit. Expected: O(E log E + Q log Q + (E + Q) alpha(n)); for n = 4, edges `[[0,1,2],[1,2,4],[2,3,8],[0,3,16]]` and queries `[[0,2,5],[0,3,3],[1,3,9],[0,3,20]]` the answer is `[true,false,true,true]`.
- **2421 Number of Good Paths (stretch).** Activate vertices by increasing value, union each with active neighbours, then count k(k - 1) / 2 pairs per group among the vertices of the current value, plus n single-vertex paths. Expected: O(n log n); values `[1,3,2,1,3]` on the tree `[[0,1],[0,2],[2,3],[2,4]]` give 6 (five single vertices plus 1-0-2-4, whose ends are the two 3s).

> [!know]
> You now know how to reorder known-in-advance questions so that union-find only ever adds edges, and how to replay deletions backwards.

=== primer | How does Kruskal build a minimum spanning tree, and why is the greedy choice safe? | 15 min
goal: Build a minimum spanning tree with Kruskal's algorithm and union-find, prove each chosen edge safe with the cut property, and tell a spanning tree apart from a shortest-path tree
tag: dsu-kruskal | Kruskal's minimum spanning tree
link: cp-algorithms: Minimum spanning tree, Kruskal's algorithm | https://cp-algorithms.com/graph/mst_kruskal.html#proof-of-correctness | 10 min: 'Properties of the minimum spanning tree', 'Kruskal's algorithm' and 'Proof of correctness'
link: Erickson, Algorithms ch. 7 (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/07-mst.pdf#page=3 | optional, 20 min: 'The Only Minimum Spanning Tree Algorithm' (safe and useless edges, PDF pages 3-4), then 'Kruskal's Algorithm' (PDF pages 9-11)
practice: cses:1675, 1489

> [!key]
> A **minimum spanning tree** (MST) of a connected, undirected, weighted graph is a set of V - 1 edges that connects every vertex with the smallest possible total weight. **Kruskal's algorithm** sorts the edges by weight and takes each edge that joins two different components, which union-find answers instantly, skipping edges that would close a cycle. It is correct because of the **cut property**: for any split of the vertices into two sides, the lightest edge crossing the split belongs to some MST. Cost: O(E log E) for the sort.

## Intuition

You must pave roads so that every village can reach every other, paying as little as possible. Look at the cheapest unpaved road. If its two villages are not yet connected by paved roads, pave it: any network that connects them must cross between their two groups somewhere, and no crossing is cheaper than this one. If they are already connected, paving it would only create a loop, which is wasted money.

## How it works

### Definitions

A **spanning tree** connects all V vertices using exactly V - 1 edges and no cycle. Its weight is the sum of its edge weights; an MST minimises that. If the graph is disconnected there is no spanning tree, only a minimum spanning **forest** (one tree per component). If all weights are distinct, the MST is unique; with ties there may be several, all with the same total.

### Kruskal's algorithm

1. Sort the edges by weight.
2. For each edge (u, v) in that order, if `union(u, v)` succeeds (u and v were in different components), keep the edge.
3. Stop after V - 1 kept edges. If you run out first, the graph is disconnected.

### Why each kept edge is safe: the cut property

Take any **cut**, a split of the vertices into two non-empty sides S and the rest. Let e be the lightest edge crossing it. Claim: some MST contains e. Proof by exchange: take an MST T without e. Adding e to T creates a cycle; that cycle crosses the cut at e, so it must cross back at some other edge f of T, and `w(f) >= w(e)` because e is the lightest crossing edge. Then T + e - f is still a spanning tree and weighs no more than T, so it is also an MST, and it contains e.

When Kruskal keeps (u, v), take S to be u's current component. Every lighter edge has already been considered, and each was either kept (so it lies inside a component) or skipped (inside a component too), so none crosses this cut. Hence (u, v) is the lightest edge leaving S, and keeping it is safe. The mirror statement, the **cycle property**, says the heaviest edge on any cycle (with distinct weights) is in no MST, which is why skipped edges are never needed.

### Useful consequences

- **Maximum spanning tree**: sort in decreasing order.
- **Bottleneck paths**: the path between two vertices inside the MST minimises the largest edge weight on the path (a "minimax" path).
- **Clustering into k groups**: stop Kruskal after V - k edges; the components are the single-linkage clusters, the same partition you get by cutting SciPy's single-linkage hierarchy into k clusters (when there are no ties).
- **Is edge e in some MST?** Force it in or leave it out and compare MST weights (or use the cut property directly).

## Cost

Sorting: O(E log E), which is O(E log V) because E <= V^2. Then at most E unions and finds: O(E alpha(V)). Memory: the edge list plus O(V) for union-find. For a graph given as an edge list this is usually the simplest and fastest choice in Python, because `sorted` runs in C.

## When to use it

- "Connect all cities, computers or points with minimum total cost", "minimum cost to repair roads so everything is reachable".
- The graph arrives as an edge list, and E is not close to V^2.
- Not for "cheapest route from A to B": that is a shortest path (Dijkstra). An MST minimises the total of the whole network, not any single route.
- Not for complete graphs given as points (E = V^2 / 2): dense Prim in the next card avoids building and sorting every edge.
- Not for directed graphs: the directed analogue (minimum arborescence) needs a different algorithm.

## Worked trace

```text
    A --1-- B
    | \     |
    4   3   2
    |     \ |
    D --5-- C
     \     /
      6   7
       \ /
        E
```

```steps
Sorted edges: AB 1, BC 2, AC 3, AD 4, CD 5, DE 6, CE 7. Every vertex is its own component
    groups   {A} {B} {C} {D} {E}
    total    0
---
AB 1: A and B are in different components. Keep it
    groups   {{{A,B}}} {C} {D} {E}
    total    1
---
BC 2: keep
    groups   {{{A,B,C}}} {D} {E}
    total    3
---
AC 3: A and C are already connected; this edge would close the cycle A-B-C. Skip
    groups   {A,B,C} {D} {E}
    skipped  {{AC 3}}
---
AD 4: keep. CD 5: C and D are now connected, skip
    groups   {{{A,B,C,D}}} {E}
    total    7
---
DE 6: keep. That is 4 = V - 1 edges, so stop; CE 7 is never examined
    groups   {{{A,B,C,D,E}}}
    tree     AB 1, BC 2, AD 4, DE 6     total {{13}}
```

## Template

```python
def kruskal(n, edges):
    """Minimum spanning forest of an undirected graph on 0..n-1; edges are (weight, u, v) tuples.
    Returns (total weight, chosen edges); fewer than n - 1 chosen edges means it is disconnected."""
    dsu = DSU(n)                            # union by size + path compression
    total, chosen = 0, []
    for w, u, v in sorted(edges):           # weight first, so tuples sort by weight
        if dsu.union(u, v):                 # joins two components: safe by the cut property
            total += w
            chosen.append((u, v, w))
            if len(chosen) == n - 1:
                break
    return total, chosen
```

## Pitfalls

- **Sorting (u, v, w) tuples directly** sorts by u, not by weight. Put the weight first or pass `key=lambda e: e[2]`.
- **Not checking connectivity**: if fewer than V - 1 edges were kept, there is no spanning tree (print "IMPOSSIBLE", return -1).
- **Confusing MST with shortest paths**: in a triangle with AB = 3, BC = 3, AC = 5, the MST is AB + BC, but the shortest route from A to C is the direct edge.
- **Ties**: several MSTs can exist; problems that ask about "every MST" (critical edges) need force-in and force-out tests, not just one run.
- **Self-loops and parallel edges**: harmless for Kruskal (a self-loop never joins two components), but count them correctly in the input.

## Check yourself

Q: In the trace, change the weight of DE from 6 to 8. Which edges does Kruskal keep now, and what is the total?
A: AB 1, BC 2 and AD 4 as before, then CD 5 is skipped and CE 7 becomes the cheapest edge reaching E: the tree is AB, BC, AD, CE with total 14. DE 8 is never examined.

Q: Prove that Kruskal never needs an edge it skipped.
A: An edge is skipped only when its ends are already connected by kept edges, all of which are no heavier (they were considered earlier). So the skipped edge is the heaviest edge on a cycle, and by the exchange argument, replacing it in any spanning tree by a lighter-or-equal edge of that cycle never increases the weight. Some MST avoids it, and Kruskal's result is one.

Q: A delivery company wants the cheapest set of roads keeping all depots connected, and separately the fastest route from the main depot to each customer. Which algorithm for each?
A: The cheapest connected road set is an MST (Kruskal or Prim). The fastest route from one depot to each customer is a shortest-path tree from that depot (Dijkstra). They generally differ: the MST may route the depot to a customer through a long chain of cheap roads.

## Lab

- **cses:1675 Road Reparation.** Plain Kruskal on n cities and m weighted roads; print the total or IMPOSSIBLE if fewer than n - 1 roads were kept. Expected: O(m log m); for 4 cities and roads (1, 2, 5), (1, 3, 3), (2, 3, 2), (3, 4, 7), (2, 4, 9) the total is 12; with only the first three roads it is IMPOSSIBLE (city 4 is unreachable).
- **1489 Find Critical and Pseudo-Critical Edges in Minimum Spanning Tree (stretch).** Compute the MST weight once; an edge is critical if leaving it out raises the weight (or disconnects the graph), pseudo-critical if not critical and forcing it in first still gives the same weight. Expected: O(E^2 alpha(V)) for E up to 200; for n = 4 and edges `[[0,1,1],[1,2,1],[2,3,2],[0,3,2],[0,2,3]]` the answer is `[[0,1],[2,3]]`.

> [!know]
> You now know how to build an MST with Kruskal and union-find, and why the cut property makes each greedy choice safe.

=== primer | When is Prim's algorithm the better choice for a minimum spanning tree? | 14 min
goal: Grow a minimum spanning tree from one vertex with Prim's algorithm, using a heap of crossing edges on sparse graphs and an O(V^2) array on dense or complete graphs, and choose between Prim and Kruskal
tag: dsu-prim | Prim's minimum spanning tree
link: cp-algorithms: Minimum spanning tree, Prim's algorithm | https://cp-algorithms.com/graph/mst_prim.html#dense-graphs-on2 | 10 min: 'Dense graphs: O(n^2)' and 'Sparse graphs: O(m log n)', the two implementations below, then 'Proof' above them
practice: 1584

> [!key]
> **Prim's algorithm** grows a single tree from any start vertex, always adding the **cheapest edge that leaves the tree**; the cut property (tree versus the rest) makes every addition safe. With a min-heap of candidate edges it costs O(E log V), similar to Kruskal. On a **dense or complete graph** keep an array `best[v]` (cheapest edge from the tree to v) and scan it: O(V^2) with no edge list and no sorting, which beats Kruskal's O(V^2 log V) when every pair of points is an edge.

## Intuition

A power company starts at its station and connects one house at a time, always the house that is cheapest to reach from any house already connected. It never needs to plan the whole network: each step looks only at the frontier between "connected" and "not yet".

## How it works

### Heap version (sparse graphs)

1. Push `(0, start)` onto a min-heap.
2. Pop the cheapest `(w, u)`. If u is already in the tree, the entry is stale; skip it. Otherwise add u to the tree and w to the total.
3. Push `(w(u, v), v)` for every neighbour v not yet in the tree. Repeat until the heap is empty; if some vertex was never added, the graph is disconnected.

This is the "lazy" version: old, more expensive entries for a vertex stay in the heap and are skipped when popped, the same trick as Dijkstra with `heapq` (which has no decrease-key).

### Array version (dense graphs)

Keep `best[v]` = weight of the cheapest edge from the tree to v (infinity at first, 0 for the start). V times: pick the vertex outside the tree with the smallest `best` by a linear scan, add it, and lower `best[v]` for every other outside vertex using the new vertex's edges. On a complete graph you can compute each edge weight on the fly (for example a Manhattan distance between points), so the V^2 / 2 edges never exist in memory.

### Why it is correct

At every step the tree's vertices form one side of a cut. The edge Prim adds is the lightest edge crossing that cut, which by the cut property (previous card) belongs to some MST consistent with the edges already chosen. By induction the final tree is an MST.

### Prim is not Dijkstra

The two look alike, but Prim's key for v is the weight of **one edge** from the tree to v, while Dijkstra's key is the **whole distance** from the source to v. Using `dist[u] + w` in Prim builds a shortest-path tree instead, which is usually heavier.

## Cost

- **Heap**: each edge causes at most one push per direction, and each push and pop costs O(log E) = O(log V): **O(E log V)** time, O(E) heap space in the lazy version.
- **Array**: V rounds, each scanning O(V) entries to find the minimum and O(V) to update: **O(V^2)** time, **O(V)** extra space.
- **Kruskal** on a complete graph must build and sort V^2 / 2 edges: O(V^2 log V) time and O(V^2) memory.

Measured in Python on 1,000 random points (499,500 possible edges): the array version took about 0.6 s, Kruskal (building, sorting and joining the edges) about 1.6 s, and heap Prim over prebuilt adjacency lists about 3.5 s.

## When to use it

| Graph | Best choice | Why |
|---|---|---|
| Edge list, sparse (E around V) | Kruskal | one C-level sort, then near-constant unions |
| Adjacency lists, sparse | heap Prim or Kruskal | both O(E log V); heap Prim avoids sorting all edges |
| Complete graph from points, V up to a few thousand | array Prim | O(V^2) with O(V) memory; never materialises the edges |
| Edges arrive in sorted order, or you also need components | Kruskal | union-find gives the forest for free |

## Worked trace

Array Prim on five points with Manhattan distances: P0 (0, 0), P1 (2, 2), P2 (3, 0), P3 (5, 3), P4 (1, 4). `best` is indexed P0 to P4; `-` marks vertices already in the tree.

```steps
Start at P0: best[P0] = 0, every other entry is infinity
    best    0   inf  inf  inf  inf
    total   0
---
Take P0 (cost 0). Update from P0: P1 4, P2 3, P3 8, P4 5
    best    -   {{4}}  {{3}}  {{8}}  {{5}}
    total   0
---
Take P2 (cheapest, 3). From P2: P1 drops to 3, P3 drops to 5; P4 stays 5
    best    -   {{3}}  -    {{5}}  5
    total   {{3}}
---
Take P1 (3; the first of the tied minimum). From P1: P3 drops to 4, P4 drops to 3
    best    -   -    -    {{4}}  {{3}}
    total   {{6}}
---
Take P4 (3). From P4: P3 would be 5, which is not better than 4
    best    -   -    -    4    -
    total   {{9}}
---
Take P3 (4). All five points are connected: edges P0-P2, P2-P1, P1-P4, P1-P3
    total   {{13}}
```

## Template

```python
import heapq

def prim(n, adj, start=0):
    """MST weight of a connected undirected graph; adj[u] lists (weight, v). None if disconnected."""
    in_tree = [False] * n
    heap = [(0, start)]
    total = 0
    while heap:
        w, u = heapq.heappop(heap)
        if in_tree[u]:
            continue                        # stale: u already joined through a cheaper edge
        in_tree[u] = True
        total += w
        for wv, v in adj[u]:
            if not in_tree[v]:
                heapq.heappush(heap, (wv, v))   # key is the edge weight, not a distance
    return total if all(in_tree) else None


def prim_dense(n, weight):
    """MST weight of the complete graph on 0..n-1 with edge weights weight(u, v). O(n^2), no heap."""
    INF = float("inf")
    best = [INF] * n                        # cheapest known edge from the tree to each vertex
    best[0] = 0
    in_tree = [False] * n
    total = 0
    for _ in range(n):
        u = min((v for v in range(n) if not in_tree[v]), key=best.__getitem__)
        in_tree[u] = True
        total += best[u]
        for v in range(n):
            if not in_tree[v]:
                best[v] = min(best[v], weight(u, v))
    return total
```

## Pitfalls

- **Dijkstra's key by mistake**: pushing `total + w` or `dist[u] + w` gives a shortest-path tree, not an MST.
- **No stale check** in the heap version: a vertex is added twice and the total is too large.
- **Disconnected input**: the heap version silently returns a tree for one component unless you check `all(in_tree)`.
- **Building all pairs for Kruskal on points**: V = 10^4 points means 5 * 10^7 edge tuples, several gigabytes in Python. Array Prim needs only three lists of length V.
- **Recomputing expensive weights**: if `weight(u, v)` is costly, cache coordinates in local variables or lists inside the loop.

## Check yourself

Q: Run the array version on the trace's points but start from P3 instead of P0. Is the total the same, and which vertex is added second?
A: The total is 13 again (every MST has the same weight). From P3 the best values are P0 8, P1 4, P2 5, P4 5, so P1 is added second.

Q: Why is the edge Prim adds always safe?
A: The tree's vertex set S and the rest form a cut. Prim adds the lightest edge crossing it, and by the cut property some MST containing all edges chosen so far also contains that edge (the exchange argument swaps it for the other crossing edge on the cycle it creates). Induction over the V - 1 additions gives an MST.

Q: 5,000 delivery points in the plane must be connected with minimum total cable, where any two points can be joined at their Manhattan distance. Which algorithm and roughly how much work?
A: Array Prim: about 5,000^2 = 25 million inner steps with O(5,000) memory (roughly 15 seconds in pure Python, well under a second if each row update is a NumPy vector operation). Kruskal would build and sort 12.5 million edges, far more memory and time.

Q: A colleague's heap Prim pushes `(total + wv, v)` instead of `(wv, v)`. On the triangle A-B 3, B-C 3, A-C 5, starting at A, what does it return?
A: From A it pushes (3, B) and (5, C). It takes B with total 3, then pushes (3 + 3 = 6, C). The heap pops (5, C) first, so it adds edge A-C and returns 3 + 5 = 8, while the MST (A-B and B-C) weighs 6. It has built a shortest-path tree.

## Lab

- **1584 Min Cost to Connect All Points.** A complete graph on the points with Manhattan weights: use array Prim with the weight computed on the fly. Expected: O(n^2) time, O(n) space; points `[[0,0],[2,2],[3,0],[5,3],[1,4]]` give 13 (the trace). Then try Kruskal on all pairs and compare the running time for n = 1,000.

> [!know]
> You now know how to grow an MST with Prim, pick the heap or the array version by density, and avoid confusing it with Dijkstra.

=== primer | How does union-find label connected regions in an image? | 13 min
goal: Implement two-pass connected-component labelling with union-find over provisional labels, compare it with flood fill, and recognise union-find in image processing, clustering and graph libraries
tag: dsu-labelling | Two-pass component labelling
link: Wikipedia: Connected-component labeling, two-pass algorithm | https://en.wikipedia.org/wiki/Connected-component_labeling#Two-pass | 10 min: the 'Two-pass' section, including the worked example of equivalent labels being merged
link: scikit-image: skimage.measure.label | https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.label | 3 min: the parameters (connectivity, background) and the References, which list the union-find and labelling papers behind the implementation

> [!key]
> To label the connected regions of a binary image, scan the pixels row by row. A foreground pixel copies the label of its upper or left neighbour, or gets a fresh provisional label; when both neighbours carry **different** labels, union-find records that those labels are the **same region**. A second pass replaces every label by its group's representative. Two sequential passes plus near-constant union-find work: linear time with cache-friendly memory access, which is why image libraries label this way.

## Intuition

You colour a stencil one row at a time and give each new blob a number. Halfway down a U shape you discover that blob 1 and blob 2 are the two arms of the same U. You cannot go back and recolour cheaply, so you write "2 is really 1" in a notebook and fix everything in a second pass. Union-find is that notebook: it keeps the "is really" notes consistent even when they chain (3 is really 2, which is really 1).

## How it works

### Pass 1: provisional labels

For each foreground pixel in row-major order, look at the neighbours already visited (with 4-connectivity, the pixel above and the pixel to the left):

- neither is foreground: create a new label;
- exactly one is: copy its label;
- both are: take one of their labels and `union` the two (often they are already equal).

### Pass 2: resolve

Replace every pixel's label by `find(label)`, and renumber the representatives 1, 2, 3 in order of appearance so labels are consecutive.

### 8-connectivity

Pixels touching at a corner count as connected: also look at the upper-left and upper-right neighbours in pass 1. The same image can have fewer regions under 8-connectivity.

### Why not a flood fill?

A BFS or DFS from every unlabelled pixel is also linear and simpler to write. Two-pass labelling touches memory strictly in order (good for caches and for images stored row by row), never needs a queue or recursion, and is the basis of the optimised algorithms that libraries use (scikit-image's `label` cites Fiorio and Gustedt's union-find strategies for image processing and Wu, Otoo and Shoshani's labelling optimisations).

### Union-find elsewhere in real software

- **NetworkX** computes Kruskal's MST with its `UnionFind` class (path compression, union by weight).
- **SciPy** has `scipy.cluster.hierarchy.DisjointSet` for incremental connectivity, and its single-linkage clustering is an MST computation: stopping Kruskal early leaves exactly the single-linkage clusters.
- **Percolation** in physics and materials science: does a random porous material conduct from top to bottom? Union-find answers it as sites open (this module's lab).
- **Type inference** in ML-family compilers unifies type variables by merging their sets.

## Cost

Pass 1 visits each of the R x C pixels once, with at most one union and two finds: O(R C alpha(R C)). Pass 2 is one find per foreground pixel. Memory: the label grid plus one parent entry per provisional label (at most about half the pixels). A flood fill costs O(R C) too, but jumps around memory and needs a queue or stack as large as the biggest region.

## When to use it

- Count or label blobs, cells, islands, objects in a raster: images, occupancy grids, game maps, scanned documents.
- Images too large to hold a queue for, or processed in row order from disk.
- When you also need per-region statistics: accumulate area, bounding box or sum per provisional label, then merge them by root in pass 2.
- For a one-off on a small grid, a flood fill is shorter and equally fast.

## Worked trace

A U-shaped blob and one separate pixel, 4-connectivity. Labels shown, `.` is background.

```steps
Row 0: two foreground pixels with no labelled neighbours get new labels 1 and 2
    image          labels
    1 0 0 1 0      {{1}} . . {{2}} .
    1 0 0 1 0      . . . . .
    1 1 1 1 0      . . . . .
    0 0 0 0 1      . . . . .
---
Row 1: each pixel copies the label from above
    labels         1 . . 2 .
                   {{1}} . . {{2}} .
---
Row 2: the first three pixels take 1 from above or the left. The fourth sees 2 above and 1 on the left: label 1 and union(1, 2)
    labels         1 . . 2 .
                   1 . . 2 .
                   1 1 1 {{1}} .
    parent         label 2 -> {{1}}
---
Row 3: the corner pixel has no labelled neighbour above or to the left (diagonals do not count): new label 3
    labels         1 . . 2 .
                   1 . . 2 .
                   1 1 1 1 .
                   . . . . {{3}}
---
Pass 2: find(2) = 1, so the right arm becomes 1; label 3 is renumbered 2. Two regions
    labels         1 . . {{1}} .
                   1 . . {{1}} .
                   1 1 1 1 .
                   . . . . {{2}}
```

## Template

```python
def label_image(image):
    """Two-pass labelling of 4-connected truthy pixels; returns (labels, number of regions)."""
    rows, cols = len(image), len(image[0])
    labels = [[0] * cols for _ in range(rows)]
    parent = [0]                            # parent[0] is the background label

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]   # path halving
            x = parent[x]
        return x

    for r in range(rows):                   # pass 1: provisional labels and equivalences
        for c in range(cols):
            if not image[r][c]:
                continue
            up = labels[r - 1][c] if r else 0
            left = labels[r][c - 1] if c else 0
            if up and left:
                a, b = find(up), find(left)
                labels[r][c] = min(a, b)
                parent[max(a, b)] = min(a, b)   # the two labels are one region
            elif up or left:
                labels[r][c] = up or left
            else:
                parent.append(len(parent))      # a new provisional label
                labels[r][c] = len(parent) - 1
    final = {}
    for r in range(rows):                   # pass 2: one consecutive number per region
        for c in range(cols):
            if labels[r][c]:
                labels[r][c] = final.setdefault(find(labels[r][c]), len(final) + 1)
    return labels, len(final)
```

Linking the larger root under the smaller one (instead of by size) keeps the code short; path halving keeps finds cheap in practice. Add union by size if you need the worst-case bound.

## Pitfalls

- **Forgetting the union** when both neighbours are labelled: U shapes then count as two regions.
- **Reading `labels[r - 1]` when r is 0**: Python's index -1 silently reads the last row. Guard with `if r`.
- **Mixing connectivities**: 8-connectivity must also look at the upper diagonals in pass 1, and the result differs from 4-connectivity.
- **Using provisional labels as final**: they are only meaningful after pass 2.
- **Recursion in the flood-fill alternative** on large images: use an explicit stack or BFS.

## Check yourself

Q: In the trace, change the last row to `0 0 0 1 0`. How many regions are there, and does pass 1 need a new label?
A: The new pixel at row 3, column 3 has label 1 directly above it (row 2, column 3), so it copies label 1; no new label. One region in total.

Q: Why must pass 1 record an equivalence instead of relabelling the earlier pixels on the spot?
A: Relabelling on the spot means finding every pixel of one label and rewriting it, which can cost the whole image each time (quick-find all over again), and a long chain of merges makes it quadratic. Recording the equivalence costs near-constant time, and one final pass resolves all of them at once.

Q: You must count objects in a 20,000 x 20,000 satellite mask stored row by row on disk. Flood fill or two-pass labelling?
A: Two-pass labelling. It reads the image in order, needs only labels and a union-find over provisional labels, never builds a queue the size of a huge region, and never recurses. (Streaming variants keep only the previous row of labels in memory and the equivalence table.)

## Lab

- **Label this image (no submission).** Rows `110011`, `010110`, `011100`, `000010`, `100001`. Expected: 4 regions with 4-connectivity (the large region spans the top, and three single pixels at (3, 4), (4, 0) and (4, 5) stand alone). Then extend pass 1 to 8-connectivity by also checking the upper-left and upper-right neighbours. Expected: 2 regions, because (3, 4) touches the large region at a corner and (4, 5) touches (3, 4); only (4, 0) stays apart.
- **Cross-check (optional).** If scikit-image is installed, `skimage.measure.label(img, connectivity=1, return_num=True)` and `connectivity=2` must report the same numbers of regions as your function. Otherwise compare against a BFS flood fill on 1,000 random 8 x 8 images.

> [!know]
> You now know how two-pass labelling uses union-find to find regions in linear time, and where the same structure appears in real libraries.

=== lab | Percolation: estimate a physical constant with union-find | 45 min
goal: Estimate the site-percolation threshold of a square grid by Monte Carlo simulation with union-find, and measure how quick-find and union by size with path compression scale as the grid doubles
link: Princeton COS 226: Percolation assignment specification | https://coursera.cs.princeton.edu/algs4/assignments/percolation/specification.php | 10 min: 'The model', 'The problem' and 'Monte Carlo simulation'; the FAQ linked from the page names the virtual-top and virtual-bottom trick used below. Ignore the Java API details

An n x n grid of sites starts fully blocked. Open sites at random, one at a time. The system **percolates** when an open path of side-adjacent sites joins the top row to the bottom row. For large n, the fraction of open sites at that moment approaches a constant, about 0.5927 for this square lattice, which nobody has a formula for: physicists estimate it by exactly this simulation. Union-find makes each step near-constant time.

## Steps

1. Save this as `percolation.py`, then paste in the `QuickFind` class from the first card of this module and the `DSU` class from the second.

```python
import random
import statistics
import time


def percolation_threshold(n, make_uf, rng):
    """Open random sites of an n x n grid until top connects to bottom; return the fraction open."""
    top, bottom = n * n, n * n + 1          # two virtual sites
    uf = make_uf(n * n + 2)
    is_open = [False] * (n * n)
    order = list(range(n * n))
    rng.shuffle(order)
    for k, site in enumerate(order, 1):
        is_open[site] = True
        r, c = divmod(site, n)
        if r == 0:
            uf.union(site, top)
        if r == n - 1:
            uf.union(site, bottom)
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < n and 0 <= nc < n and is_open[nr * n + nc]:
                uf.union(site, nr * n + nc)
        if uf.find(top) == uf.find(bottom):
            return k / (n * n)


def estimate(n, trials, make_uf, seed=0):
    rng = random.Random(seed)
    xs = [percolation_threshold(n, make_uf, rng) for _ in range(trials)]
    return statistics.mean(xs), statistics.stdev(xs)
```

2. Explain to yourself why the two virtual sites turn "does any top site connect to any bottom site?" (n^2 pairs) into a single `find` comparison.
3. Estimate the threshold with the `DSU` class for n = 20, 50, 100 and 200, with 100 trials each. Record the mean and the standard deviation.
4. Check the simulation against a slow oracle: for n = 6 and 200 random opening orders, open sites one at a time and, after each opening, decide "percolates?" with a BFS from all open top-row sites; the first step where the BFS reaches the bottom row must equal `k` from `percolation_threshold` (use the same shuffled order for both).
5. Time one simulation, averaged over 5 runs, with `QuickFind` for n = 16, 32, 64, 128 and with `DSU` for n = 16 up to 512. Compute the ratio between consecutive times.
6. Optional: a site is "full" if it connects to the top through open sites. Displaying full sites with a single union-find has a bug called backwash (bottom sites appear full through the virtual bottom). Find it, then fix it with a second union-find that has no virtual bottom.

## What you should see

- The means sit near 0.59 for every n (with `seed=0`: 0.585 at n = 20, 0.593 at n = 100 and 0.591 at n = 200), and the standard deviation shrinks as n grows (about 0.05 at n = 20, under 0.01 at n = 200): bigger grids give sharper estimates of 0.5927. Small grids percolate a little early because a few lucky sites can span a short distance.
- The oracle agrees on every order. If it does not, the usual culprits are a missing union with a virtual site or a wrong neighbour index (`nr * n + nc`).
- Quick-find gets about **16 times slower per doubling** of n (roughly 2 ms, 40 ms, 0.65 s, 9 s): each doubling quadruples the sites, and every union scans all of them, so the cost grows like (n^2)^2. The DSU gets about **4 to 5.5 times slower per doubling**, roughly linear in the n^2 sites (about 0.05 s at n = 128 and 1.3 s at n = 512 in pure Python).
- At n = 128 the DSU is already about 200 times faster than quick-find, and the gap keeps widening; this is the measurement behind "union by size and path compression make it almost O(1)".

=== practice
- 547 core
  pattern: dsu-template
  cue: Count the groups of cities linked directly or through other cities, given an adjacency matrix
  hint: Every direct link merges two groups into one. If you start with n groups, what changes each time two groups merge?
  insight: Union-find over the n cities: union every pair with isConnected[i][j] = 1 and count successful unions; the answer is n minus that count. (One DFS labelling is equally good because the graph never changes.)
  cost: O(n^2 alpha(n)) time, O(n) space
- cses:1676 core
  pattern: dsu-connect
  cue: Roads are built one per day; after each day report the number of connected groups of cities and the size of the largest
  hint: Searching the whole network after every new road is too slow. What do you really need to remember about each group?
  insight: Union-find with sizes: a road between different groups merges them, lowering the count by one and possibly raising the largest size to the merged size; a road inside a group changes nothing. Print both after every road.
  cost: O((n + m) alpha(n)) time, O(n) space
- 684 core
  pattern: dsu-groups
  cue: A tree had one extra edge added; return the edge (the last one in input order if several work) whose removal leaves a tree
  hint: Add the edges one by one. At what moment does an edge stop being useful for connecting anything new?
  insight: Process edges in order with union-find; the first edge whose endpoints already share a root closes the only cycle, and because all later edges are tree edges, it is also the last edge on that cycle in input order. Return it.
  cost: O(n alpha(n)) time, O(n) space
- 990 core
  pattern: dsu-groups
  cue: Equations like a==b and b!=c over single letters; can all hold at once?
  hint: Equality is transitive, so it builds groups. When is a "not equal" condition violated?
  insight: Union the two letters of every == equation first; then every != equation must join letters with different roots. Doing all unions before any check matters, because a later equality can merge two letters that an earlier inequality separated.
  cost: O(n alpha(26)) time, O(1) space
- 721 core
  pattern: dsu-groups
  cue: Merge accounts that share any email address, then output each person's name with all their emails sorted
  hint: Comparing every pair of accounts is quadratic. What could map each email straight to an account that has already used it?
  insight: Keep a dict from email to the first account that listed it; when another account lists the same email, union the two accounts. Then group every email under its account's root, sort each group, and prefix the name of that root's account.
  cost: O(N log N) time for N emails (the sorting dominates), O(N) space
- 947 derive
  pattern: dsu-groups
  cue: Remove stones one at a time, each only while another stone shares its row or column; maximise removals
  hint: Group stones that are linked through shared rows and columns. How many stones must stay in each group, at the least?
  insight: Each linked group can be emptied down to exactly one stone (remove leaves of a spanning tree first), so the answer is stones minus groups. Find the groups without comparing stone pairs by treating rows and columns as the elements: each stone unions its row with its column (offset the column ids).
  cost: O(n alpha(n)) time, O(n) space
- cses:1675 core
  pattern: dsu-kruskal
  cue: Repair a subset of roads, each with a cost, so that every city can reach every other at minimum total cost; or say it is impossible
  hint: Look at the cheapest road first. When is it definitely worth repairing, and when is it wasted?
  insight: Kruskal: sort roads by cost and keep each road that joins two different components (union-find); the kept roads form a minimum spanning tree by the cut property. If fewer than n - 1 roads were kept, print IMPOSSIBLE.
  cost: O(m log m) time, O(n) space
- 1584 core
  pattern: dsu-prim
  cue: Connect all points with minimum total cost, where any two points can be joined at their Manhattan distance
  hint: Every pair of points is a possible edge. How many edges is that for 1,000 points, and do you have to build them all?
  insight: It is a minimum spanning tree of a complete graph. Array-based Prim keeps best[v], the cheapest distance from the growing tree to each point, picks the smallest by a linear scan and updates the rest: O(n^2) with no edge list. Kruskal over all n^2 / 2 pairs also works but sorts half a million edges.
  cost: O(n^2) time, O(n) space
- 1697 derive
  pattern: dsu-offline
  cue: Many queries "is there a path from a to b using only edges shorter than limit?", all given in advance
  hint: Would the answers be easier if the queries came in a particular order? What happens to the usable edge set as the limit grows?
  insight: Offline sweep: sort the edges by length and the query indices by limit; for each query in that order, union every edge strictly shorter than its limit, then compare roots of a and b and store the answer at the query's original index. The edge set only grows, so union-find suffices.
  cost: O(E log E + Q log Q + (E + Q) alpha(n)) time, O(n + Q) space
- 399 stretch
  pattern: dsu-weighted
  cue: Given a / b = 2.0 and b / c = 3.0 style equations, answer queries like a / c, or -1.0 when unknown
  hint: If every variable knew its value relative to one reference variable in its group, how would you answer a / c?
  insight: Weighted union-find: each node stores value(x) / value(parent); find multiplies the weights up to the root and compresses; union(a, b, k) hangs root(a) under root(b) with weight k * wb / wa. A query is wa / wc when the roots match, else -1.0 (also -1.0 for any variable never seen).
  cost: O((E + Q) log n) time with path compression, O(n) space
- 1489 stretch
  pattern: dsu-kruskal
  cue: Classify each edge as in every minimum spanning tree, in some but not all, or in none
  hint: You can compute an MST weight quickly. What happens to that weight if you forbid one edge, or insist on it?
  insight: Compute the MST weight W with Kruskal. Edge e is critical if Kruskal without e gives a weight above W (or cannot connect the graph); otherwise it is pseudo-critical if forcing e in first and running Kruskal on the rest still gives W. With E up to 200, running Kruskal twice per edge is fast enough.
  cost: O(E^2 alpha(V)) time after one O(E log E) sort, O(V + E) space
- 2421 stretch
  pattern: dsu-offline
  cue: Count paths in a tree whose two end nodes have equal values and no node on the path has a larger value
  hint: Suppose you only allow nodes with values up to v. Which pairs of value-v nodes can then be joined by a good path?
  insight: Add nodes in increasing value, uniting each with already-added neighbours (all no larger). After adding every node of value v, nodes of value v in the same group are joined by a path with nothing larger, so add k(k - 1) / 2 for each group of k such nodes, plus n single-node paths.
  cost: O(n log n) time for sorting, O(n) space
