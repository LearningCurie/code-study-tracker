---
key: dpadv
name: Advanced dynamic programming
stage: strategy
summary: Advanced and optional, for after the DP, sequence DP and greedy modules: interval, tree, bitmask and digit DP, counting modulo a prime, faster transitions, and DP seen as paths in a DAG.
why: This module is advanced and optional. Take it after the DP, sequence DP and greedy modules, with tree recursion fresh in mind, and skip it on a first pass if time is short. The earlier DP modules taught you to find a state on a line, a grid or a pair of strings; harder problems hide the state in an interval, a subtree, a subset or the digits of a number, and recognising those four shapes is most of what separates "I know DP" from solving DP problems you have not seen. They come up in demanding interviews and contests, and in real software: NumPy's multi_dot chooses a matrix multiplication order with interval DP, and PostgreSQL's planner searches join orders with DP over subsets of tables until there are so many tables that it switches to a genetic search. The last two cards turn DP into an engineering tool: making transitions cheaper, and reading a DP as a path problem so that graph algorithms apply.
outcomes:
- Recognise interval DP, fill the table by increasing length, and choose between a split point and a "last action" recurrence
- Compute per-node states on a tree in post-order, combine the best two child chains, and reroot to answer for every node in O(n)
- Use subsets as states for n up to about 20 (travelling salesman, assignment) and estimate their time and memory
- Count numbers up to N with a digit property using a tight flag, and handle leading zeros and ranges
- Count modulo 10^9 + 7 correctly, including subtraction and division, in Python and C++
- Speed up transitions with prefix sums, a monotonic deque or binary search, and read a DP as a path problem in a DAG
cues:
- "Merge", "burst", "cut" or "remove" pieces of a sequence, where neighbours change as you go (interval DP)
- Values on tree nodes with a rule linking parents and children, or "for every node, compute ..." (tree DP, rerooting)
- n at most about 20 and you must choose an order or a subset of items, people or cities (bitmask DP)
- "How many integers in [L, R] have ..." with R up to 10^18 or more (digit DP)
- "Return the count modulo 10^9 + 7", or a transition that sums or maximises over a sliding range
traps:
- Filling an interval table row by row instead of by increasing length, so dp[i][j] reads unfinished cells
- Choosing the first action in an interval when only the last action splits it into independent parts
- Recursing over a 10^5-node tree in Python and hitting the recursion limit
- Allocating 2^n × n states for n = 25 (over 800 million) without estimating memory first
- Taking min or max of values that were already reduced modulo a prime, or letting a C++ subtraction go negative
systems:
- NumPy's numpy.linalg.multi_dot picks the cheapest multiplication order for a chain of matrices with the classic O(n³) interval DP (with a shortcut for exactly three matrices)
- PostgreSQL's standard planner builds join orders by dynamic programming over sets of tables, two-table joins first, then three, and so on; at geqo_threshold FROM items (12 by default) it switches to a genetic optimiser because the subset space explodes
- The jieba Chinese word segmenter builds a DAG of candidate words over a sentence and picks the maximum-probability path through it with DP
- Phylogenetics software scores evolutionary trees with Felsenstein's pruning algorithm, a post-order DP over the tree's nodes
further:
- Chapter · 30 min | Erickson, Algorithms ch. 3: 'Dynamic Programming on Trees' (PDF pp. 24-26) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/03-dynprog.pdf#page=24
- Chapter · 30 min | Erickson, Algorithms ch. 6: 'Dynamic Programming in Dags' (PDF pp. 11-14) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/06-dfs.pdf#page=11
- Chapter · 40 min | Competitive Programmer's Handbook, section 10.5: dynamic programming over subsets (PDF pp. 112-117) | https://cses.fi/book/book.pdf#page=112
- Article · 20 min | USACO Guide: Digit DP, with the odometer problem solved with and without DP | https://usaco.guide/gold/digit-dp#solution---odometer
bank: dpadv
---

=== primer | How does interval DP solve problems over every contiguous range [i, j]? | 16 min
goal: Recognise interval DP, fill the table by increasing length, and choose between a split-point and a last-action recurrence
tag: dpadv-interval | Interval DP
link: USACO Guide: Range DP | https://usaco.guide/gold/dp-ranges#tutorial | 10 min: 'Tutorial' and the worked 'Example - Space Jazz', a DP over every subarray processed by increasing length
link: Wikipedia: Matrix chain multiplication | https://en.wikipedia.org/wiki/Matrix_chain_multiplication#A_dynamic_programming_algorithm | 5 min: 'A dynamic programming algorithm', the same recurrence with its O(n³) cost
practice: 486, 1547, 312

> [!key]
> When a problem keeps merging, splitting or removing pieces of a sequence, and a contiguous block interacts with the rest only through its ends, make the **interval** the state: `dp[i][j]` is the best answer for the part i..j. Try every **split point**, or every choice of the **last action** inside the interval, combine two shorter intervals, and fill the table by **increasing length** so both halves are ready. With n² intervals and up to n choices each, that is O(n³).

## Intuition

Multiplying four matrices A0 A1 A2 A3 gives the same result whatever you multiply first, but the work can differ by a factor of ten or more. Look at the **last** multiplication performed: it joins the product of a left block with the product of a right block, for example (A0 A1)(A2 A3) or A0 (A1 A2 A3). Each block is the same problem on a shorter interval, and the two blocks never interact. Try every place for that final split, and you have the whole recurrence.

The same shape appears whenever adjacent pieces combine: merging neighbouring piles, cutting a stick where each cut costs the current piece's length, bursting balloons whose neighbours then touch, parsing a sentence with a grammar, folding an RNA strand, and two players taking turns from either end of a row.

## How it works

### State, recurrence and order

Matrix Ai has shape `dims[i] × dims[i+1]`. Multiplying a p × q matrix by a q × r one costs p·q·r scalar multiplications, so:

```text
dp[i][i] = 0
dp[i][j] = min over k in [i, j) of  dp[i][k] + dp[k+1][j] + dims[i]·dims[k+1]·dims[j+1]
```

`dp[i][j]` reads only strictly shorter intervals, so filling by length (all intervals of length 2, then 3, and so on) always finds its inputs ready. Equivalent orders are i from n - 1 down to 0 with j from i upwards, or a memoised recursion, which finds an order by itself. Recording the best k per interval lets you rebuild the bracketing at the end.

### Split point or last action?

Sometimes the obvious choice breaks the problem. Remove one balloon from a row and its neighbours become adjacent, so the left and right parts now interact: choosing the **first** balloon to burst does not split the problem. Choose instead the balloon burst **last** inside an open interval (l, r): while everything else between l and r disappears, that balloon separates the two sides, and when it finally bursts its neighbours are known, namely l and r. The rule of thumb: pick the action whose context is fixed when it happens, which is usually the last one.

### Game intervals

When two players alternately take from either end of a row, let `dp[i][j]` be the best score **difference** the player to move can force on i..j: `max(a[i] - dp[i+1][j], a[j] - dp[i][j-1])`. Storing the difference lets both players use the same formula. There is no split loop, so this costs O(n²).

## Cost

There are n(n+1)/2 intervals and each tries up to n splits: **O(n³) time, O(n²) space**. In CPython, n = 300 took about 2 seconds for the matrix chain, so n around 500 is the practical ceiling without vectorising the inner loop. Interval games without a split loop are O(n²). Some interval DPs with special structure (optimal binary search trees, certain merging costs) drop to O(n²) with Knuth's optimisation; it is enough to know that it exists.

## When to use it

Cues: "merge adjacent", "burst" or "remove" with neighbours joining, "cut into pieces" with a cost depending on the current piece, "parenthesise", "take from either end", n at most a few hundred. Not interval DP when the chosen items need not be contiguous (that is a subset: bitmask DP or knapsack), or when every decision extends a prefix (a 1D DP suffices).

## Worked trace

dims = [10, 30, 5, 60, 10]: A0 is 10 × 30, A1 is 30 × 5, A2 is 5 × 60, A3 is 60 × 10. Blank cells are not filled yet.

```steps
Length 1: a single matrix needs no multiplication, so the diagonal is 0
          j=0     j=1     j=2     j=3
    i=0     0
    i=1             0
    i=2                     0
    i=3                             0
---
Length 2: one way each. [0,1] = 10·30·5 = 1500, [1,2] = 30·5·60 = 9000, [2,3] = 5·60·10 = 3000
          j=0     j=1     j=2     j=3
    i=0     0   {{1500}}
    i=1             0   {{9000}}
    i=2                     0   {{3000}}
    i=3                             0
---
Length 3, [0,2]: split after A0 costs 0 + 9000 + 10·30·60 = 27000; after A1 costs 1500 + 0 + 10·5·60 = 4500. Keep 4500
          j=0     j=1     j=2     j=3
    i=0     0    1500   {{4500}}
    i=1             0    9000
    i=2                     0    3000
---
Length 3, [1,3]: after A1 costs 0 + 3000 + 30·5·10 = 4500; after A2 costs 9000 + 0 + 30·60·10 = 27000. Keep 4500
          j=0     j=1     j=2     j=3
    i=0     0    1500    4500
    i=1             0    9000   {{4500}}
    i=2                     0    3000
---
Length 4, [0,3]: k=0 gives 0 + 4500 + 3000 = 7500, k=1 gives 1500 + 3000 + 500 = 5000, k=2 gives 4500 + 0 + 6000 = 10500. Best: (A0 A1)(A2 A3) for 5000
          j=0     j=1     j=2     j=3
    i=0     0    1500    4500   {{5000}}
    i=1             0    9000    4500
    i=2                     0    3000
    i=3                             0
```

Multiplying strictly left to right, ((A0 A1) A2) A3, would cost 1500 + 3000 + 6000 = 10500, more than twice the optimum.

## Template

```python
def matrix_chain(dims):
    """Fewest scalar multiplications for A0 A1 ... A(n-1), where Ai is dims[i] x dims[i+1].
    Returns (cost, split) where split[i][j] is the best last split point for Ai..Aj."""
    n = len(dims) - 1
    cost = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):               # shorter intervals first
        for i in range(n - length + 1):
            j = i + length - 1
            cost[i][j] = float("inf")
            for k in range(i, j):                # last product: (Ai..Ak) times (Ak+1..Aj)
                c = cost[i][k] + cost[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]
                if c < cost[i][j]:
                    cost[i][j], split[i][j] = c, k
    return cost[0][n - 1], split


def parenthesise(split, i, j):
    if i == j:
        return f"A{i}"
    k = split[i][j]
    return f"({parenthesise(split, i, k)} {parenthesise(split, k + 1, j)})"
```

`parenthesise(split, 0, 3)` on the trace returns `((A0 A1) (A2 A3))`. To adapt the template, change three things: what an interval means (closed [i, j] here; open (l, r) for balloons), the choices inside it, and the cost of combining.

## Pitfalls

- **Row-by-row filling.** Computing `dp[0][3]` before `dp[1][3]` reads a cell that is still 0 and silently returns a wrong minimum.
- **Open versus closed intervals.** With padding (balloons, cut points including both stick ends) the interval is open and k ranges strictly between l and r; mixing conventions gives off-by-one errors.
- **The first action instead of the last.** If removing a piece changes its neighbours, a "first action" recurrence does not decompose; switch to the last action.
- **Recomputing range sums.** When the combine cost is the sum of a[i..j], precompute prefix sums or the O(n³) becomes O(n⁴).
- **Python speed.** O(n³) with n = 500 is about 2·10^7 inner steps, several seconds in CPython; cache rows in locals or vectorise the inner loop with NumPy.

## Check yourself

Q: Fill the table for dims = [5, 10, 3, 12] (three matrices). What is the minimum cost and the bracketing?
A: [0,1] = 5·10·3 = 150, [1,2] = 10·3·12 = 360. For [0,2], splitting after A0 costs 0 + 360 + 5·10·12 = 960, after A1 costs 150 + 0 + 5·3·12 = 330. Minimum 330, as (A0 A1) A2.

Q: Why does choosing the last balloon burst in (l, r) make the two sides independent, when choosing the first does not?
A: If balloon k bursts last in (l, r), it is still present while everything in (l, k) and (k, r) bursts, so it acts as a wall: each side only ever sees its own balloons plus the fixed ends (l and k, or k and r). Its own coins are then a[l]·a[k]·a[r], known exactly. If k burst first, l's side and r's side would become neighbours afterwards, and the coins on each side would depend on the other.

Q: Adjacent piles of stones are merged two at a time, each merge costing the size of the new pile. Write the recurrence, and give the answer for piles [4, 1, 3, 2].
A: `dp[i][j] = min over k of dp[i][k] + dp[k+1][j] + sum(a[i..j])` with `dp[i][i] = 0`, using prefix sums for the range sum. For [4, 1, 3, 2] the answer is 20: merge 1 and 3 (4), then that pile with 2 (6), then with 4 (10).

## Lab

- **486 Predict the Winner.** `dp[i][j]` is the best difference for the player to move; player 1 wins on a difference of at least 0. Brute force first: plain recursion without memo, exponential. Expected: O(n²) time, O(n²) or O(n) space; `[2, 9, 4]` gives false (difference -3) and `[2, 9, 4, 1]` gives true (difference 4).
- **1547 Minimum Cost to Cut a Stick.** Sort the cuts, add both ends, and run interval DP over consecutive cut positions. Brute force: try every order of cuts (m!) for small m. Expected: O(m³) for m cuts; `n = 10, cuts = [2, 4, 7]` gives 20, and `n = 8, cuts = [1, 6, 3, 5]` gives 19.
- **312 Burst Balloons** (derive). Pad with 1s and choose the last balloon in each open interval. Brute force: try every burst order. Expected: O(n³); `[4, 2, 6, 1]` gives 84 and `[7]` gives 7.

> [!know]
> You now know how to set up interval DP, fill it by increasing length, and pick a split point or the last action so that the subproblems are independent.

=== primer | How do you run DP on a tree, and how does rerooting give every node's answer in O(n)? | 16 min
goal: Compute per-node states children-first without recursion, combine the best two child chains for paths, and reroot to answer for every possible root in O(n)
tag: dpadv-tree | Tree DP and rerooting
link: USACO Guide: DP on trees | https://usaco.guide/gold/dp-trees#tutorial | 10 min: 'Tutorial' and 'Solution - Tree Matching', a dp[v][taken or not] computed from the children in post-order
link: USACO Guide: Solving for all roots | https://usaco.guide/gold/all-roots#solution---tree-distances-i | 15 min: 'Solution - Tree Distances I', one DP array for inside each subtree and one for outside it
practice: 337, 2246, 834

> [!key]
> A rooted tree is already a DAG of subproblems: a node's answer depends only on its children's answers. Give each node a small tuple of states, such as "best if this node is chosen" and "best if it is not", compute children before parents (**post-order**), and combine. For paths through a node, join its **two best child chains**. To answer for **every** possible root, **reroot**: solve once for root 0, then move the root across one edge at a time, adjusting the answer in O(1). Everything is O(n).

## Intuition

Plan an office party where nobody attends together with their direct manager. Each manager waits for every team below to report two numbers, "the best total if my team lead comes" and "the best total if not", and then works out the same two numbers for their own team. The reports flow up the hierarchy; the chief executive's two numbers decide the answer. No manager ever needs to look more than one level down, because each report already summarises a whole subtree.

## How it works

### States per node, children first

Example: place the fewest guards on junctions so that every road (tree edge) has a guard at one of its ends (a minimum vertex cover). For each node v:

```text
guard[v] = 1 + sum over children c of min(guard[c], free[c])
free[v]  =     sum over children c of guard[c]          (an unguarded v forces every child road to be guarded at c)
answer   = min(guard[root], free[root])
```

The maximum-weight version where adjacent nodes cannot both be chosen (house robber on a tree) has the same skeleton: `take[v] = val[v] + sum skip[c]`, `skip[v] = sum max(take[c], skip[c])`.

To get children before parents without recursion, list the nodes in BFS or DFS order from the root (parents before children) and process that list backwards.

### Paths through a node

For "longest path" style questions, let each node return the longest chain going **down** from it. The best path that turns at v joins its two longest child chains: `1 + top1 + top2`. Track the global maximum over all nodes; return `1 + top1` to the parent. Constraints such as "adjacent nodes must differ" just decide which children may extend v's chain; every child is still processed for its own subtree.

### Rerooting

Some questions ask for an answer per possible root: the total distance from each node to all others, the farthest node from each node, or this one: roads in a tree are one-way, and for every city you want the number of roads to reverse so that everyone can drive to it. Naively that is one O(n) pass per root, O(n²) in total. Instead:

1. Root at 0 and compute `ans[0]`: the number of roads pointing **away** from 0.
2. Moving the root from p to a child v changes the meaning of exactly one road, the one between p and v. If it ran p -> v it counted for p but points towards v, so `ans[v] = ans[p] - 1`; if it ran v -> p, it now points away from the new root, so `ans[v] = ans[p] + 1`. Every other road keeps its direction relative to the root.

Walking the tree top-down applies this rule along every edge: O(n) for all roots. For harder answers, the shift needs some subtree information from the first pass (sizes, best chains), but the plan is the same: one pass up, one pass down.

## Cost

Each edge is used once as a parent-child link, so the upward pass costs O(n·k) for k states per node, and rerooting adds one more O(n) pass: **O(n) time and space** for a fixed number of states. Top-two tracking costs O(degree) per node, still O(n) in total. The naive alternative, recomputing from every root, is O(n²): 10^10 steps at n = 10^5.

## When to use it

Cues: the input is a tree (n - 1 edges, a parent array, or a binary tree), a rule ties a node to its parent or children (not both chosen, colours differ), the answer is a best path inside a tree, or the question says "for every node". Not for general graphs: maximum independent set or minimum vertex cover on a graph with cycles is NP-hard, so the tree shape is what makes this fast.

## Worked trace

Fewest guards on this tree (root 0). Processing order: 6, 5, 4, 3, 2, 1, 0 (BFS order reversed).

```text
            0
         /  |  \
        1   2   3
       / \       \
      4   5       6
```

```steps
Leaves 6, 5, 4 and 2: a guard covers nothing below, so guard = 1; with no children, free = 0
    node    0    1    2    3    4    5    6
    guard   .    .   {{1}}    .   {{1}}   {{1}}   {{1}}
    free    .    .   {{0}}    .   {{0}}   {{0}}   {{0}}
---
Node 3 (child 6): guard = 1 + min(1, 0) = 1; free = guard[6] = 1, because road 3-6 then needs a guard at 6
    node    0    1    2    3    4    5    6
    guard   .    .    1   {{1}}    1    1    1
    free    .    .    0   {{1}}    0    0    0
---
Node 1 (children 4, 5): guard = 1 + 0 + 0 = 1; free = 1 + 1 = 2
    node    0    1    2    3    4    5    6
    guard   .   {{1}}    1    1    1    1    1
    free    .   {{2}}    0    1    0    0    0
---
Root 0 (children 1, 2, 3): guard = 1 + min(1,2) + min(1,0) + min(1,1) = 3; free = 1 + 1 + 1 = 3. Answer: 3 guards, for example at 0, 1 and 3, or at 1, 2 and 3
    node    0    1    2    3    4    5    6
    guard  {{3}}    1    1    1    1    1    1
    free   {{3}}    2    0    1    0    0    0
```

## Template

```python
def min_guards(n, edges, root=0):
    """Fewest guarded junctions so every road (tree edge) has a guard at one end."""
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    parent = [-1] * n
    order = [root]                               # preorder: parents before children
    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    guard = [1] * n                              # best for u's subtree if u has a guard
    free = [0] * n                               # best for u's subtree if u has none
    for u in reversed(order):                    # children before parents
        p = parent[u]
        if p != -1:
            guard[p] += min(guard[u], free[u])
            free[p] += guard[u]                  # an unguarded parent forces a guarded child
    return min(guard[root], free[root])


def reversals_for_every_capital(n, roads):
    """roads: one-way (a, b) pairs forming a tree (drive a -> b). For every city c, how many
    roads must be reversed so every city can drive to c. Rerooting: two passes, O(n)."""
    adj = [[] for _ in range(n)]
    for a, b in roads:
        adj[a].append((b, 1))                    # stepping a -> b follows the road
        adj[b].append((a, 0))                    # stepping b -> a goes against it
    parent, away = [-1] * n, [0] * n             # away[v]: the road runs parent[v] -> v
    order = [0]
    for u in order:                              # preorder from root 0
        for v, along in adj[u]:
            if v != parent[u]:
                parent[v], away[v] = u, along
                order.append(v)
    ans = [0] * n
    ans[0] = sum(away)                           # roads pointing away from root 0 must flip
    for v in order[1:]:                          # move the root across one edge at a time
        ans[v] = ans[parent[v]] + (-1 if away[v] else 1)
    return ans
```

Appending to `order` while iterating over it is a compact BFS: the loop visits every node exactly once.

## Pitfalls

- **Recursion depth.** A path-shaped tree of 10^5 nodes recurses 10^5 deep; Python's default limit is 1000. Use the order-list pattern, or raise the limit only for modest depths.
- **Walking back to the parent.** An undirected edge list must be rooted: skip the parent (by tracking it), or the "children" include the node you came from.
- **Unclear state meaning.** Write one sentence per state ("best total in v's subtree if v is guarded") before coding the combine step; most tree DP bugs are mixed meanings.
- **Top-two chains.** Start both at 0, and remember that a child excluded by a rule (same label, blocked edge) contributes nothing to v's chain but still needs its own subtree answer.
- **Rerooting shifts.** The O(1) update must remove exactly the moved child's contribution and add the parent side's; test it against the naive "solve from every root" on small random trees.

## Check yourself

Q: Give node 2 a child 7 in the trace tree. What are guard[2], free[2] and the final answer?
A: Node 7 is a leaf (guard 1, free 0), so guard[2] = 1 + min(1, 0) = 1 and free[2] = guard[7] = 1. At the root, guard = 1 + 1 + 1 + 1 = 4 and free = 1 + 1 + 1 = 3, so the answer is 3: guards at 1, 2 and 3.

Q: Why must the nodes be processed in post-order (children first)?
A: A node's states are sums or extremes over its children's states. If a parent is combined before a child is finished, it reads the child's initial values, and that error is never revisited because each node is combined exactly once.

Q: With roads 0 -> 1, 2 -> 1 and 1 -> 3, what does `reversals_for_every_capital` return, and why is city 3 a perfect capital?
A: [2, 1, 2, 0]. Every road already points towards 3 (0 and 2 drive into 1, and 1 drives into 3), so nothing needs reversing; capital 0 needs 0 -> 1 and 1 -> 3 flipped, which is 2.

## Lab

- **337 House Robber III.** Return a pair (rob this node, skip this node) from each subtree. Brute force: try every subset of nodes for tiny trees. Expected: O(n) time, O(h) stack; the tree `[4,1,5,2,3,null,1]` gives 10, and `[2,7,1,1,null,null,9]` gives 16.
- **2246 Longest Path With Different Adjacent Characters.** Each node returns its longest valid downward chain and combines its two best children whose letters differ from its own. Brute force: check the path between every pair of nodes. Expected: O(n); `parent = [-1,0,0,1,1,2,2], s = "abbacca"` gives 5, `parent = [-1,0,1,2], s = "abab"` gives 4, and `parent = [-1,0,0], s = "aaa"` gives 1.
- **834 Sum of Distances in Tree** (derive). First pass: subtree sizes and the root's total; second pass: shift the total across each edge. Brute force: BFS from every node, O(n²). Expected: O(n); `n = 5, edges = [[0,1],[1,2],[1,3],[3,4]]` gives `[8, 5, 8, 6, 9]`, and the star `n = 4, edges = [[0,1],[0,2],[0,3]]` gives `[3, 5, 5, 5]`.

> [!know]
> You now know how to run DP on a tree children-first, combine the best two child chains for paths, and reroot to answer for every node in O(n).

=== primer | How does bitmask DP turn n! orderings into 2^n subsets? | 17 min
goal: Use a bitmask of used items as the DP state (travelling salesman, assignment, grouping), rebuild the best order, and estimate time and memory before coding
tag: dpadv-bitmask | Bitmask DP over subsets
link: Competitive Programmer's Handbook, section 10.5 | https://cses.fi/book/book.pdf#page=112 | 20 min: PDF pages 112-117, 'Optimal selection', 'From permutations to subsets' (the elevator problem) and 'Counting subsets'
link: USACO Guide: Bitmask DP | https://usaco.guide/gold/dp-bitmasks#tutorial | 10 min: 'Tutorial' and its solution, a DP over (mask, last) like the one below
practice: 1986, ac:dp_o, 943

> [!key]
> Many ordering problems care only about **which** items are used so far and **where you are now**, not about the order in which you used them. Encode the used set as an integer whose bit i means "item i is used" and make (mask, last) the state. The travelling salesman over n cities then drops from (n - 1)! orders to 2^n · n states with n choices each: **O(2^n · n²)**, the Held-Karp algorithm. That is practical up to n of about 20 in C++ and about 15 to 16 in Python, and memory, 2^n · n entries, is usually the real limit.

## Intuition

A delivery driver at 3 pm has visited shops A, C and D and is now standing at D. For planning the rest of the day, it does not matter whether the morning went A, C, D or C, A, D: only the set {A, C, D}, the current shop D and the distance driven so far matter. So of those two histories, keep the cheaper and forget the other. Every set of permutations with the same "visited set and current position" collapses into one state. There are n! orders but only 2^n · n such states, and that gap is the whole trick: for n = 15, about 8.7·10^10 tours from a fixed start against fewer than 500,000 states.

## How it works

### Masks in Python

| Operation | Code |
|---|---|
| is item i in the set? | `mask >> i & 1` |
| add item i | `mask \| 1 << i` |
| remove item i | `mask & ~(1 << i)` |
| size of the set | `mask.bit_count()` (Python 3.10+) or `bin(mask).count("1")` |
| every item | `(1 << n) - 1` |

Adding an item makes the number larger, so looping over masks in increasing order always handles a set before any of its supersets: a valid DP order for free.

### The travelling salesman (Held-Karp)

`best[mask][v]` is the shortest route that starts at city 0, visits exactly the cities in mask, and ends at v. Start with `best[{0}][0] = 0`. From each state, extend to every unvisited city u: `best[mask | u][u] = min(..., best[mask][v] + d[v][u])`. The tour length is the minimum over v of `best[full][v] + d[v][0]`. Fixing city 0 as the start is safe because a tour is a cycle; it also halves the masks (only odd ones contain city 0). Storing the predecessor of each state lets you walk the tour back.

### Other shapes

- **Assignment.** n workers and n jobs: with jobs taken given by mask, the next worker to place is number `popcount(mask)`, so the state is the mask alone: O(2^n · n). Sum instead of minimising and you count perfect matchings.
- **Packing into bins.** "Fewest trips or sessions": let `dp[mask]` be the pair (trips used, load of the current trip), minimised lexicographically; adding an item either fits in the current trip or opens a new one. O(2^n · n).
- **Covering.** "Smallest team covering every skill": the mask is the set of skills covered, and each person ORs in their skills.
- **Partitions into groups.** Iterate the submasks of a mask with `s = (s - 1) & mask`; over all masks this costs O(3^n).

## Cost

Held-Karp has 2^n · n states and n transitions each: **O(2^n · n²) time, O(2^n · n) space**. For n = 15 that is about 7·10^6 inner steps, which took under a second in CPython, while brute force over permutations took 15 seconds already at n = 11 (3.6 million tours). Each extra city roughly doubles the time: the template took 1.8 s at n = 16 and 7.6 s at n = 18. At n = 20 the count is about 4·10^8 steps (half that with city 0 fixed): around a second in C++, well over half a minute in CPython. Memory: the two tables (`best`, `prev`) peaked at about 15 MB for n = 15 and 136 MB for n = 18; at n = 20 one table has 21 million entries, about 170 MB of list pointers alone in Python, or 84 MB as 32-bit integers in C++. Estimate this before you allocate.

## When to use it

Cues: n at most about 20, and the task is to visit, assign, order, cover or group **all** of a small set of items; the decisions so far can be summarised by "which ones are used" plus a little extra. Not for n of 25 or more (2^25 · 25 is about 8·10^8 states): reach for heuristics, branch and bound or an integer programming solver. Not when the set can be summarised by a count, as in "how many items taken" (that is ordinary DP).

## Worked trace

Four cities, symmetric distances: d(0,1) = 10, d(0,2) = 15, d(0,3) = 20, d(1,2) = 35, d(1,3) = 25, d(2,3) = 30. Masks are written as sets and in binary (city 0 is the lowest bit).

```steps
Only city 0 visited, standing at 0, distance 0
    {0}        0001   end 0: {{0}}
---
Sets of size 2: go straight from 0
    {0,1}      0011   end 1: {{10}}
    {0,2}      0101   end 2: {{15}}
    {0,3}      1001   end 3: {{20}}
---
Size 3: each entry keeps the cheaper of the two orders. {0,1,2} ending at 2: 0 1 2 = 10+35 = 45; ending at 1: 0 2 1 = 15+35 = 50
    {0,1,2}    0111   end 1: 50    end 2: {{45}}
    {0,1,3}    1011   end 1: 45    end 3: {{35}}   (0 1 3 = 10+25)
    {0,2,3}    1101   end 2: 50    end 3: {{45}}   (0 2 3 = 15+30)
---
All four: end 1 = min(50+35, 45+25) = 70; end 2 = min(45+35, 35+30) = 65; end 3 = min(50+25, 45+30) = 75
    {0,1,2,3}  1111   end 1: 70    end 2: {{65}}    end 3: 75
---
Close the tour with the edge back to 0: 70+10 = 80, 65+15 = 80, 75+20 = 95. Shortest tour: 80, for example 0 2 3 1 0 (or its reverse 0 1 3 2 0)
    end 1: 80    end 2: {{80}}    end 3: 95
```

Twelve (mask, end) entries replaced the six orderings of cities 1, 2, 3; at n = 15 it is 491,520 entries against 87 billion orderings.

## Template

```python
def tsp(dist):
    """Held-Karp: length of the shortest tour from city 0 through every city and back,
    plus the tour itself. O(2^n n^2) time, O(2^n n) space."""
    n = len(dist)
    INF = float("inf")
    full = 1 << n
    best = [[INF] * n for _ in range(full)]      # best[mask][v]: path from 0 over mask, ending at v
    prev = [[-1] * n for _ in range(full)]
    best[1][0] = 0
    for mask in range(1, full, 2):               # odd masks: city 0 is always visited
        for v in range(n):
            here = best[mask][v]
            if here == INF:
                continue
            for u in range(n):
                if mask >> u & 1:
                    continue
                nxt = mask | 1 << u
                if here + dist[v][u] < best[nxt][u]:
                    best[nxt][u] = here + dist[v][u]
                    prev[nxt][u] = v
    last = min(range(n), key=lambda v: best[full - 1][v] + dist[v][0])
    length = best[full - 1][last] + dist[last][0]
    tour, mask = [], full - 1
    while last != -1:                            # walk the choices back
        tour.append(last)
        mask, last = mask ^ (1 << last), prev[mask][last]
    return length, tour[::-1] + [0]
```

On the trace, `tsp` returns `(80, [0, 2, 3, 1, 0])`.

## Pitfalls

- **Operator precedence in C, C++ and Java.** There, `mask & 1 << i == 0` means `mask & ((1 << i) == 0)`, because `==` binds tighter than `&`; write `(mask >> i & 1) == 0`. Python's comparisons bind more loosely than `&`, so the same line works in Python, which makes ports dangerous.
- **Allocating before estimating.** Multiply 2^n by the per-state size first; for large n use `array`, NumPy, or a rolling layer per set size.
- **Path versus tour.** A Hamiltonian path that may end anywhere takes the minimum of `best[full][v]` without the closing edge; a tour must add `d[v][0]`.
- **Not fixing the start.** Letting every city start multiplies the work by n for no benefit when the answer is a cycle.
- **Brute force as an oracle.** `itertools.permutations` over n - 1 cities is a perfect test oracle up to n = 9 or 10, and useless beyond.

## Check yourself

Q: In the trace, where does `best[{0,1,2,3}][2] = 65` come from, and which candidate was discarded?
A: From `best[{0,1,3}][3] = 35` (route 0 1 3) plus d(3,2) = 30, giving the route 0 1 3 2. The other candidate, `best[{0,1,3}][1] = 45` (route 0 3 1) plus d(1,2) = 35 = 80, was discarded, and no later state can ever need it.

Q: Why is it safe to keep only the cheapest history for each (set, end) pair?
A: Every way of finishing the tour depends only on which cities remain (the complement of the set) and where you stand (the end city). Replace a history with a cheaper one for the same set and end and every completion gets cheaper by the same amount, so a more expensive history can never be part of an optimal tour.

Q: Someone wants an exact tour for 18 cities in Python. Estimate the cost.
A: 2^18 · 18 · 18 is about 8.5·10^7 inner steps, half that with city 0 fixed: the template above took about 8 seconds and 136 MB in CPython, and C++ needs well under a second. Feasible for one run in Python; for repeated runs use arrays instead of lists of lists, or C++.

## Lab

- **1986 Minimum Number of Work Sessions to Finish the Tasks.** `dp[mask]` = (sessions used, time used in the current session), minimised lexicographically. Brute force: assign each task to one of n sessions (n^n) for n up to 6. Expected: O(2^n · n); `tasks = [4,3,3,2,2,1], sessionTime = 5` gives 3, and `tasks = [6,2,2,2], sessionTime = 6` gives 2.
- **AtCoder DP O, Matching.** Man number `popcount(mask)` is paired next; sum the counts modulo 10^9 + 7. Expected: O(2^N · N); the compatibility matrix `[[1,1,0],[1,1,1],[0,1,1]]` gives 3, the all-ones 4 × 4 matrix gives 24, and `[[1,0],[1,0]]` gives 0.
- **943 Find the Shortest Superstring** (stretch). Precompute pairwise overlaps, then a (mask, last) DP that maximises total overlap, and rebuild the order. Expected: O(n² · 2^n + n² · L); `["dcab","abxy","xyz"]` gives a 7-letter answer ("dcabxyz"), and `["pq","qr","rp"]` a 4-letter one such as "pqrp".

> [!know]
> You now know how to use subsets as DP states, rebuild the best order, and decide from n whether 2^n · n states fit in time and memory.

=== lab | Travelling salesman for 15 cities: permutations vs bitmask DP | 45 min
goal: Implement brute-force and Held-Karp TSP, verify them against each other, find the crossover point, and measure how time and memory grow

You will hit the exponential wall twice, once at n! and once at 2^n · n², and measure exactly where each one stops you. Use the stress-test loop and doubling timer from your `dsakit` if you built it.

## Setup

```python
import itertools
import math
import random


def cities(n, seed):
    """n random points in a 100 x 100 square; distances rounded to 3 decimals."""
    rnd = random.Random(seed)
    pts = [(rnd.uniform(0, 100), rnd.uniform(0, 100)) for _ in range(n)]
    return [[round(math.dist(a, b), 3) for b in pts] for a in pts]


def brute_force(d):
    """Shortest tour from city 0 by trying every order of the other cities."""
    best = float("inf")
    for p in itertools.permutations(range(1, len(d))):
        tour = (0,) + p + (0,)
        best = min(best, sum(d[a][b] for a, b in zip(tour, tour[1:])))
    return best
```

## Steps

1. Copy `tsp` from the bitmask card.
2. Verify first: for n from 2 to 9, run 50 random instances each and assert that `brute_force` and `tsp` agree (compare floats with a tolerance of 1e-6), that the returned tour visits every city once, and that its length matches the reported one.
3. Time `brute_force` for n = 4 to 11 and `tsp` for n = 4 to 16 (`time.perf_counter`, best of three for small n). Print one table and mark the crossover.
4. Compute the ratio between consecutive times for each method. Predict the ratios before looking: brute force should grow by about n per step, the DP by a little over 2.
5. Use your n = 11 brute-force time to predict how long brute force would take at n = 15.
6. Measure peak memory of `tsp` with `tracemalloc` for n = 12 to 16, in a separate run from the timings (tracemalloc slows Python down several times).
7. Write a nearest-neighbour heuristic (always drive to the closest unvisited city) and record its gap to the optimum over 30 instances with n = 12.
8. Optional: halve the memory by storing only odd masks (index `mask >> 1`), or by using `array("d")` rows, and measure again.

## What you should see

- The two methods agree on every instance; if not, check the closing edge back to city 0 and the n = 1 and n = 2 cases.
- The crossover is tiny: around n = 6 the DP is already faster (about 1 ms each). At n = 9 brute force took about 0.26 s against about 0.01 s for the DP; at n = 11, about 15 s against 0.02 s.
- Brute force grows by roughly n per step (×7 to ×10 here); the DP by about ×2 to ×2.5 per step, reaching under a second at n = 15 and about 2 s at n = 16.
- Predicted brute force at n = 15: 15 s × (14!/10!) = 15 s × 24,024, about 4 days.
- Peak memory for n = 15 is about 15 MB; each extra city roughly doubles it (and n = 18 reached about 136 MB).
- Nearest neighbour is instant but was 14% longer than optimal on average over 30 instances, and 40% longer in the worst one: exact DP is worth having while n is small.

> [!note]
> For dozens or thousands of cities nobody solves TSP exactly with DP; real routing uses heuristics and local search (2-opt, Lin-Kernighan) or integer programming solvers. The DP is the exact baseline you check those heuristics against on small instances.

=== primer | How do you count the numbers up to N that have a digit property? | 15 min
goal: Count integers in [0, N] with a digit property using the state (position, summary, tight), handle leading zeros, and answer ranges as two prefix counts
tag: dpadv-digit | Digit DP with a tight flag
link: USACO Guide: Digit DP | https://usaco.guide/gold/digit-dp#solution---odometer | 15 min: 'Solution - Odometer', comparing 'Without Dynamic Programming' with 'With Dynamic Programming' for the same counting question
practice: 902, ac:dp_s, 2376

> [!key]
> To count the x in [0, N] whose digits have some property, build x from the left one digit at a time and remember only three things: the **position**, a small **summary** of the digits so far (their sum, a remainder, the last digit, the set of digits used), and a **tight** flag saying whether the prefix still equals N's prefix, which caps the next digit at N's digit. Once a prefix drops below N's, the remaining digits are free, and the count depends only on (position, summary), so memoisation shares it across every such prefix. Answer a range as f(R) - f(L - 1).

## Intuition

Count the numbers from 0 to 253 whose digits add up to 7. Write every number with three digits (7 is 007). The first digit can be 0, 1 or 2. If it is 0 or 1, the number is already below 253 whatever comes next, so the last two digits are free: you just need "two digits with a given sum", a question that has nothing to do with 253 any more. Only the branch with first digit 2 stays on the edge, where the next digit is capped at 5. So the work is one narrow path along N's digits, with free sub-counts peeling off at each step, and those free sub-counts repeat endlessly across different prefixes. That repetition is what memoisation removes.

## How it works

### The state

`go(pos, total, tight)` counts the ways to fill positions pos onwards so that the final digit sum equals the target, given the sum so far and whether the prefix is still equal to N's.

- `limit = digits[pos] if tight else 9`.
- For each digit d from 0 to limit, recurse into `go(pos + 1, total + d, tight and d == limit)`: the prefix stays tight only if it copied N's digit.
- At the end (pos equals the number of digits), count 1 if the total matches, else 0. Prune early when the total already exceeds the target.

The summary is whatever the property needs and nothing more: `total % D` for "digit sum divisible by D", the last digit for "no two equal neighbours", a 10-bit mask for "all digits distinct", a count of 7s for "exactly k sevens".

### Leading zeros

Writing short numbers with leading zeros (7 as 007) is harmless for sums and remainders, because zeros add nothing. It is wrong for properties that look at the digits themselves: with "all digits distinct", 007 would use the digit 0 twice. Add a fourth flag, **started**: while it is false, a 0 is padding, does not enter the summary, and keeps started false; the first non-zero digit sets it. The number 0 itself (never started) is then handled explicitly.

### Ranges, big N and counting from 1

The count over [L, R] is `f(R) - f(L - 1)`, with f(-1) = 0. If the problem counts from 1, subtract the number 0 when it qualifies. When N has thousands of digits, pass it as a string, reduce counts modulo the requested prime, and fill a table position by position instead of recursing.

## Cost

There are L positions (the number of digits), S summary values and 2 tight values, and each state tries at most 10 digits: **O(L · S · 10) time, O(L · S) memory**. For N = 10^18 and digit sums up to 162, that is about 19 × 163 × 2 × 10, roughly 62,000 steps, against 10^18 for enumerating every number. The tight states form a single chain (one per position), so almost all the work and almost all the sharing happens in the free states. With a 10-bit used-digits mask, S is 1024: still only tens of thousands of states.

## When to use it

Cues: "how many integers in [L, R]" or "up to N" with N as large as 10^18 or given as a long string, and a property checked digit by digit with a small summary. Not when the property needs the whole number at once with no small summary (whether x is prime), though "x mod 7" is fine because a remainder updates digit by digit (`r = (10 r + d) % 7`). For very simple properties a closed formula may be shorter, but digit DP is the method that generalises.

## Worked trace

Count x in [0, 253] with digit sum 7.

```steps
Position 0, tight: N's first digit is 2, so the first digit can be 0, 1 or 2
    N        2  5  3
    prefix   _  _  _      sum 0   tight
---
First digit 0 or 1: the prefix is now below N, so two **free** digits remain. Two digits summing to 7: 8 ways (07, 16, ..., 70); summing to 6: 7 ways. These are memoised states go(1, 0, free) and go(1, 1, free)
    prefix   0  _  _   ->  {{8}}
    prefix   1  _  _   ->  {{7}}
---
First digit 2: still tight, sum 2, so the second digit is capped at N's 5. Digits 0 to 4 make the prefix smaller: one free digit must bring the sum to 7, exactly one way each (205, 214, 223, 232, 241)
    prefix   2  0..4  _  ->  {{5}}
---
Second digit 5: still tight, sum 7, last digit capped at 3. Only 0 keeps the sum at 7 (the number 250); 1 to 3 overshoot and are pruned
    prefix   2  5  0     ->  {{1}}
    prefix   2  5  1..3  ->  0
---
Add up the branches: 8 + 7 + 5 + 1 = 21 numbers. Without the tight flag every three-digit string would count, giving 36
    total    {{21}}
```

## Template

```python
from functools import cache


def count_digit_sum(n, target):
    """How many integers x in [0, n] have digit sum equal to target."""
    digits = [int(c) for c in str(n)]

    @cache
    def go(pos, total, tight):
        if total > target:
            return 0
        if pos == len(digits):
            return 1 if total == target else 0
        limit = digits[pos] if tight else 9
        return sum(go(pos + 1, total + d, tight and d == limit) for d in range(limit + 1))

    return go(0, 0, True)
```

The cache lives inside the call, so each n gets a fresh one. To adapt it, replace `total` with the summary your property needs, change the final check, and add `started` if leading zeros matter.

## Pitfalls

- **No tight flag.** Counting every string of N's length counts numbers above N: 36 instead of 21 in the trace.
- **Leading zeros as real digits.** Properties about which digits appear need the `started` flag.
- **Off by one on ranges.** Use f(R) - f(L - 1), define f(-1) = 0, and check whether 0 itself should count.
- **Deep recursion.** The recursion is as deep as N has digits; Python fails somewhere past about 1,000 digits (the template raised RecursionError at 1,500). For long inputs, fill a table from the last position backwards.
- **Huge counts.** With thousands of digits the counts have thousands of digits too; reduce modulo the requested prime at every addition.

## Check yourself

Q: What does `count_digit_sum(99, 7)` return, and which numbers are they?
A: 8: 7, 16, 25, 34, 43, 52, 61 and 70. Both digits of 99 are 9s, so the tight cap never bites, and the count is just "two digits summing to 7".

Q: Why does memoisation help so much here, when the tight path visits each position only once?
A: The tight path is a single chain, but every step off it creates a free state (position, sum), and there are only L × S of those. Every prefix that drops below N with the same position and sum asks the same question, so its answer is computed once and reused, instead of enumerating all suffixes again.

Q: How would you count the numbers in [1, N] with no two equal adjacent digits?
A: State (pos, last digit, tight, started). Digit d is allowed if the number has not started yet or d differs from the last digit. Leading zeros keep started false and do not set the last digit; at the end count 1 only if started is true (this drops 0, as required for a range starting at 1).

## Lab

- **902 Numbers At Most N Given Digit Set.** Shorter lengths are all free; for N's length, walk N's digits counting smaller allowed digits times the free choices, and stop if N's digit itself is not allowed. Brute force: test every x up to N for small N. Expected: O(L · |digits|); `digits = ["2","5","7"], n = 300` gives 21, `digits = ["1","4"], n = 41` gives 5, and `digits = ["3"], n = 2` gives 0.
- **AtCoder DP S, Digit Sum.** Count x in [1, K] whose digit sum is divisible by D, modulo 10^9 + 7, with K up to 10^10000: state (pos, sum mod D, tight), filled as a table, then subtract the number 0. Expected: O(len(K) · D · 10); K = 50, D = 5 gives 10, K = 1000, D = 7 gives 139, and K = 9, D = 10 gives 0.
- **2376 Count Special Integers** (stretch). Distinct digits: state (pos, used-digits mask, tight, started). Expected: O(L · 2^10 · 10); n = 30 gives 28 (11 and 22 are excluded), n = 100 gives 90, n = 1000 gives 738.

> [!know]
> You now know how to count numbers up to N with a digit property using a tight flag, a started flag and a small summary state.

=== primer | How do you count ways modulo 10^9 + 7 without getting wrong answers? | 13 min
goal: Reduce sums, differences, products and quotients modulo a prime correctly in Python and C++, and know which DP values must never be reduced
tag: dpadv-mod | Counting modulo a prime
link: cp-algorithms: Binomial coefficients | https://cp-algorithms.com/combinatorics/binomial-coefficients.html#binomial-coefficient-modulo-large-prime | 5 min: 'Binomial coefficient modulo large prime', factorials and inverse factorials precomputed in O(n)
link: cp-algorithms: Modular inverse | https://cp-algorithms.com/algebra/module-inverse.html#finding-the-modular-inverse-using-binary-exponentiation | 5 min: 'Finding the Modular Inverse using Binary Exponentiation', Fermat's little theorem in practice
practice: ac:dp_o, ac:dp_s

> [!key]
> Counting DPs produce astronomically large numbers, so problems ask for the count modulo a prime p, usually 10^9 + 7. Addition, subtraction and multiplication survive reduction, so reduce after every step. **Subtraction** must end non-negative (automatic with Python's `%`, add p in C++). **Division** becomes multiplication by an inverse, `pow(b, p - 2, p)`, which exists because p is prime. What you may never do is **compare** reduced values: min, max and "which is larger" lose their meaning after a mod.

## Intuition

Clock arithmetic: ten hours after 9 o'clock is 7 o'clock, and adding or multiplying hours works perfectly on the clock face. But the clock face cannot tell you whether 7 o'clock is earlier or later than 9 o'clock, because it forgot how many times the hand went round. Counting modulo p is the same: every sum and product of the true counts can be tracked exactly "on the clock", while comparisons cannot.

Why 10^9 + 7? It is prime, so every non-zero value has an inverse. It fits in a signed 32-bit integer, the sum of two residues is below 2^31, and the product of two residues is below 2^60, which fits in a signed 64-bit integer before reduction. (998244353, also prime, is the other common choice.)

## How it works

### The rules

| Operation | Python | C++ |
|---|---|---|
| a + b | `(a + b) % p` | `(a + b) % p` (fits in 32 bits) |
| a - b | `(a - b) % p` (never negative in Python) | `((a - b) % p + p) % p` |
| a × b | `a * b % p` | `(long long)a * b % p` |
| a / b | `a * pow(b, p - 2, p) % p`, or `pow(b, -1, p)` (Python 3.8+) | fast power for the inverse |
| a < b, min, max | meaningless on reduced values | meaningless |

Python's integers never overflow, so you could count exactly and reduce once at the end. It is correct and painfully slow: the exact number of ways to climb 10^5 stairs with steps of 1 to 3 has about 26,000 digits. Computing all of them exactly took 1.45 s and about 590 MB; reducing at every step took 0.04 s.

### Subtraction: sliding sums

The ways to climb i stairs with steps of 1 to k are the sum of the previous k values. Keeping a running window sum costs O(1) per step: add the newest value, subtract the one that falls out. That subtraction is where C++ code goes negative.

### Division: binomials by inverse factorials

C(n, r) = n! / (r! (n - r)!). Precompute factorials modulo p, take one inverse with Fermat's little theorem (`pow(fact[n], p - 2, p)`), and walk it down with `inv_fact[i - 1] = inv_fact[i] · i`. After O(n) setup, every C(n, r) costs three multiplications.

### What not to reduce

Optimisation values (fewest coins, longest path) are never reduced: they are small anyway, and reducing breaks every min and max. In mixed DPs, such as "the number of cheapest routes", keep the cost exact and reduce only the count. And a reduced count of 0 does not prove that nothing is possible (the true count may be a multiple of p): track feasibility separately when it matters.

## Cost

Each reduced operation works on machine-sized numbers: O(1). A modular inverse by fast power costs O(log p), about 30 squarings for 10^9 + 7. Factorial tables cost O(n) time and space once. Unreduced big integers cost time proportional to their length per addition, so an n-step counting DP with exponential growth costs O(n²) digit operations instead of O(n).

## When to use it

Whenever a statement says "return it modulo 10^9 + 7": counting paths, matchings, arrangements, subsets, digit strings. Whenever a formula divides (combinations, expected values written as fractions modulo p). Never on the values being minimised or maximised.

## Worked trace

Ways to climb with steps of 1, 2 or 3, using a running window sum and a tiny modulus, p = 7, so that wrap-around is visible. The true counts are 1, 1, 2, 4, 7, 13, 24, 44.

```steps
i = 1 to 3: the window just accumulates (nothing has fallen out yet)
    i        0  1  2  3
    ways     1  {{1}}  {{2}}  {{4}}
    window   after i = 3: 1 + 1 + 2 = 4
---
i = 4: add ways[3] = 4, giving 8 % 7 = 1; subtract ways[0] = 1, giving 0. True count 7, and 7 % 7 = 0
    i        0  1  2  3  4
    ways     1  1  2  4  {{0}}
---
i = 5: add ways[4] = 0, giving 0; subtract ways[1] = 1, giving **-1**. Python's -1 % 7 is 6; in C++ -1 % 7 is -1, a wrong answer. True count 13, and 13 % 7 = 6
    i        0  1  2  3  4  5
    ways     1  1  2  4  0  {{6}}
---
i = 6: add 6, giving 12 % 7 = 5; subtract ways[2] = 2, giving 3. True count 24, and 24 % 7 = 3
    i        0  1  2  3  4  5  6
    ways     1  1  2  4  0  6  {{3}}
---
i = 7: add 3, giving 6; subtract ways[3] = 4, giving 2. True count 44, and 44 % 7 = 2: every residue matches
    i        0  1  2  3  4  5  6  7
    ways     1  1  2  4  0  6  3  {{2}}
```

## Template

```python
MOD = 10**9 + 7


def ways_to_climb(n, k):
    """Ways to climb n steps taking 1..k steps at a time, mod MOD, in O(n)."""
    ways = [0] * (n + 1)
    ways[0] = 1
    window = 0                                   # ways[i-k] + ... + ways[i-1], mod MOD
    for i in range(1, n + 1):
        window = (window + ways[i - 1]) % MOD
        if i - k - 1 >= 0:
            window = (window - ways[i - k - 1]) % MOD    # Python's % is never negative
        ways[i] = window
    return ways[n]


def binomials(n_max):
    """comb(n, r) mod MOD for 0 <= n <= n_max, after O(n_max) precomputation."""
    fact = [1] * (n_max + 1)
    for i in range(1, n_max + 1):
        fact[i] = fact[i - 1] * i % MOD
    inv_fact = [1] * (n_max + 1)
    inv_fact[n_max] = pow(fact[n_max], MOD - 2, MOD)     # Fermat: a^(p-2) is 1/a mod p
    for i in range(n_max, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    def comb(n, r):
        if r < 0 or r > n:
            return 0
        return fact[n] * inv_fact[r] % MOD * inv_fact[n - r] % MOD

    return comb
```

Test any modular DP against the exact count: on small inputs, Python computes the true big-integer answer for free, so `exact % MOD == fast` is a perfect oracle.

## Pitfalls

- **Negative remainders in C++ and Java**, where `%` keeps the sign of the dividend: add p before the final `%`.
- **Overflow in C++**: `a * b` with two `int` residues overflows before the `%`; cast to `long long` first. `pow` in C++ is floating point: write your own fast power.
- **Dividing with `/` or `//`.** Neither is modular division; multiply by the inverse.
- **No inverse.** 0 has no inverse, and neither does any multiple of p: factorial tables only work for n < p.
- **Reducing optimisation values** or comparing reduced counts.

## Check yourself

Q: Continue the trace to i = 8. What is `ways[8]` modulo 7, and what is the true count?
A: Add `ways[7] = 2` to the window 2, giving 4; subtract `ways[4] = 0`, giving 4. The true count is 13 + 24 + 44 = 81, and 81 % 7 = 4.

Q: A DP stores "the fewest coins" and someone reduces it modulo 10^9 + 7 "to be safe". Why is that a bug even though the values are small?
A: It only stays correct as long as no value reaches p; if an intermediate value were ever reduced, min would compare residues instead of true values (5 against 10^9 + 8, which reduces to 1, would pick the wrong one). More importantly, it signals a misunderstanding: reduction is for counts that are only ever added and multiplied, never for values that are compared.

Q: How do you compute C(10^5, 5·10^4) modulo 10^9 + 7, and what is it?
A: Build `binomials(10**5)` once and call `comb(10**5, 5 * 10**4)`. It returns 149033233, which matches `math.comb(10**5, 5 * 10**4) % MOD` computed exactly with big integers.

## Lab

- **AtCoder DP O, Matching** (counting part). Sum the bitmask DP counts with a reduction at every addition. Expected: `[[1,1,0],[1,1,1],[0,1,1]]` gives 3, and the all-ones 21 × 21 matrix gives 21! mod 10^9 + 7 = 72847302.
- **AtCoder DP S, Digit Sum** (modular part). The DP counts 0 as well, so the answer is `(count - 1) % MOD`, which must stay correct when count is a multiple of p. Expected: K = 1000, D = 7 gives 139, and K = 9, D = 10 gives 0 (only 0 qualifies, and it is removed).

> [!know]
> You now know how to count modulo a prime safely: reduce sums and products, keep subtractions non-negative, divide with inverses, and never reduce what you compare.

=== primer | How do you speed up a DP whose transitions scan a whole range? | 15 min
goal: Replace a range scan inside a DP with prefix sums, a monotonic deque or binary search, and verify the faster version against the slow one
tag: dpadv-speedup | Faster DP transitions
link: USACO Guide: Sliding window maximum with a deque | https://usaco.guide/gold/sliding-window#method-1---deque | 10 min: 'Method 1 - Deque', the monotonic deque used below, and the difference between storing indices and storing values

> [!key]
> Many DPs are correct but slow because each state loops over a range of earlier states: `dp[i] = combine(dp[j] for j in a range)`. When the range moves predictably, maintain the combination incrementally instead of recomputing it. **Prefix sums** give a range sum in O(1); a **monotonic deque** gives a sliding-window maximum or minimum in amortised O(1); **binary search** finds the single earlier state that matters when states are sorted. The recurrence stays the same; the cost drops from O(n·k) or O(n²) to O(n) or O(n log n).

## Intuition

The recurrence is the specification; the inner loop is just one way to evaluate it. A bank that reports "total spending over the last 30 days" every morning does not re-add 30 days of transactions: it adds today's and subtracts the day that dropped out. Each technique below is that idea for a different kind of combine: sum, maximum, or "the latest compatible one".

## How it works

### Prefix sums over transitions

Share exactly K sweets among n children, where child i may get between 0 and `caps[i]`. Processing children one by one, `new[j] = ways[j] + ways[j-1] + ... + ways[j-cap]`: a sum over a contiguous window of the previous row. Build that row's prefix sums once, and every `new[j]` is one subtraction: `prefix[j+1] - prefix[max(0, j-cap)]`. The work drops from O(n·K·cap) to O(n·K). AtCoder DP M (Candies) is exactly this problem.

### A monotonic deque for window maxima

Choose a non-empty subsequence with maximum sum where consecutive chosen indices are at most k apart. `best[i] = vals[i] + max(0, max(best[i-k..i-1]))`. The window max is the same problem the monotonic stack module solved with a deque: keep indices whose `best` values decrease from front to back; drop the front when it leaves the window; before appending i, pop every back index whose value is not larger than `best[i]` (it is older and no better, so it can never be the maximum again). The front is always the window's maximum. LeetCode 1425 (Constrained Subsequence Sum) and 1696 (Jump Game VI), both listed in the monotonic stack module, have this shape.

### Binary search inside the DP

Weighted interval scheduling: jobs with start, end and profit; take a profitable set of non-overlapping jobs. Sort by end time; `best[i+1] = max(best[i], best[p] + profit_i)`, where p counts the jobs ending no later than job i starts. The ends are sorted, so `bisect_right` finds p in O(log n) instead of a scan. LeetCode 1235 (Maximum Profit in Job Scheduling), listed in the DP module, is this problem; the O(n log n) longest increasing subsequence uses the same idea.

### Spotting which one applies

Write the slow recurrence first and look at its inner loop. A sum over a contiguous range: prefix sums. A maximum or minimum over a window that slides forwards: a monotonic deque. One relevant earlier state located by a sorted key: binary search, or two pointers when the queries also move monotonically. Further optimisations (the convex hull trick, divide and conquer optimisation, Knuth's) exist for contest problems and are beyond this guide.

## Cost

| Transition shape | Naive | Faster | Why |
|---|---|---|---|
| sum over a window of width k | O(n·k) | O(n) | one prefix array per row |
| max or min over the last k | O(n·k) | O(n) | each index enters and leaves the deque once |
| latest compatible state by a sorted key | O(n²) | O(n log n) | `bisect` per state |

Measured in CPython: the sweets DP with 30 children, K = 1,000 and caps up to 1,000 took 1.38 s naively and 0.07 s with prefix sums; the gap-limited subsequence with n = 10^4 and k = 1,000 took 0.40 s naively and 0.008 s with the deque. The gains grow with k.

## When to use it

When the plain DP is correct but too slow by a factor equal to the range length, for example n·k = 10^10 with n = k = 10^5. Keep the slow version: it is the oracle for testing the fast one. Not applicable when the range is not contiguous or does not move monotonically; "sum of dp[j] over all j < i with a[j] < a[i]" needs a Fenwick tree over values (the range queries module).

## Worked trace

The deque version on vals = [3, -5, -2, 4, -1, 2] with k = 2. The deque holds indices; their `best` values are shown beside them.

```steps
i = 0, value 3: the window is empty, so best[0] = 3. Push 0
    best    3
    deque   [0]      values [3]
---
i = 1, value -5: front 0 is in the window, best = -5 + 3 = -2. -2 is smaller than 3, so push 1 behind it
    best    3  {{-2}}
    deque   [0, 1]   values [3, -2]
---
i = 2, value -2: front 0 still in the window (2 - 2 = 0), best = -2 + 3 = 1. Pop index 1 (-2 is not larger than 1), push 2
    best    3  -2  {{1}}
    deque   [0, 2]   values [3, 1]
---
i = 3, value 4: front 0 is out of the window (it needs index 1 or later), pop it. best = 4 + 1 = 5. Pop 2 (1 <= 5), push 3
    best    3  -2  1  {{5}}
    deque   [3]      values [5]
---
i = 4, value -1: best = -1 + 5 = 4, push 4. i = 5, value 2: best = 2 + 5 = 7; pop 4 and 3, push 5
    best    3  -2  1  5  4  {{7}}
    deque   [5]      values [7]
---
Answer max(best) = 7: indices 0, 2, 3, 5, that is 3 - 2 + 4 + 2, with gaps of 2, 1 and 2
    answer  {{7}}
```

## Template

```python
from bisect import bisect_right
from collections import deque

MOD = 10**9 + 7


def share_sweets(caps, total):
    """Ways to hand out exactly total sweets when child i may get 0..caps[i], mod MOD.
    Prefix sums turn each O(cap) transition into O(1): O(n * total) overall."""
    ways = [1] + [0] * total                     # ways[j] for the children so far
    for cap in caps:
        prefix = [0] * (total + 2)
        for j in range(total + 1):
            prefix[j + 1] = (prefix[j] + ways[j]) % MOD
        ways = [(prefix[j + 1] - prefix[max(0, j - cap)]) % MOD for j in range(total + 1)]
    return ways[total]


def best_with_gaps(vals, k):
    """Maximum sum of a non-empty subsequence whose consecutive chosen indices are at most k apart.
    best[i] = vals[i] + max(0, max(best[i-k..i-1])); a decreasing deque gives that max in O(1)."""
    best = [0] * len(vals)
    dq = deque()                                 # indices, best[] decreasing from front to back
    for i, v in enumerate(vals):
        if dq and dq[0] < i - k:
            dq.popleft()                         # fell out of the window
        best[i] = v + max(0, best[dq[0]] if dq else 0)
        while dq and best[dq[-1]] <= best[i]:
            dq.pop()                             # dominated: older and no better
        dq.append(i)
    return max(best)


def max_profit_jobs(jobs):
    """jobs: (start, end, profit), a job may start when the previous ends. O(n log n)."""
    jobs = sorted(jobs, key=lambda j: j[1])
    ends = [e for _, e, _ in jobs]
    best = [0] * (len(jobs) + 1)                 # best[i]: using only the first i jobs
    for i, (s, e, p) in enumerate(jobs):
        fits = bisect_right(ends, s, 0, i)       # jobs ending at or before s
        best[i + 1] = max(best[i], best[fits] + p)
    return best[-1]
```

One element leaves the window per step, so a single `if` is enough to evict from the front; the `while` at the back may pop many, but each index is popped at most once overall.

## Pitfalls

- **Prefix off-by-ones.** With `prefix[j+1] = prefix[j] + ways[j]`, the sum of `ways[a..b]` is `prefix[b+1] - prefix[a]`; clamp a at 0.
- **Prefix sums modulo p.** The subtraction can go negative in C++: add p.
- **Values instead of indices in the deque.** You cannot tell when a value has left the window; store indices.
- **Evicting after reading.** Drop out-of-window indices before using the front.
- **`bisect_left` where `bisect_right` is needed.** A job may start exactly when another ends; the right boundary includes it.
- **Optimising before testing.** Verify the slow DP on small cases, then compare fast against slow on random inputs.

## Check yourself

Q: Run the deque version on vals = [5, -1, -1, -1, 6] with k = 2. What is the answer, and which indices achieve it?
A: best = [5, 4, 4, 3, 10], so the answer is 10: indices 0, 2 and 4 (5 - 1 + 6), each gap exactly 2. At i = 4 the window holds indices 2 and 3 with best values 4 and 3, so the front gives 4.

Q: The deque loop has a `while` inside a `for`. Why is the total cost still O(n)?
A: Each index is appended exactly once and removed at most once (from the front or the back), so the total number of pops over the whole run is at most n. The `while` cannot pop more than was pushed, so all the iterations together cost O(n): an amortised bound.

Q: Which speed-up fits `dp[i] = cost[i] + min(dp[j] for j in range(i - k, i))`, and which fits `dp[i] = sum(dp[j] for j in range(i - k, i))`?
A: The first is a sliding-window minimum: a monotonic deque with increasing values. The second is a sliding-window sum: prefix sums, or simply a running window total as in the modular counting card.

## Lab

- **Exercise: sweets.** Expected: `share_sweets([1, 2, 3], 4)` gives 5 and `share_sweets([3, 3, 3], 5)` gives 12. Write the O(n·K·cap) version and compare on 200 random cases.
- **Exercise: gaps.** Expected: `best_with_gaps([10, -2, -10, -5, 20], 2)` gives 23 (indices 0, 1, 3, 4). Time the naive and deque versions for n = 10^4 and k = 10, 100 and 1,000, and check that the speed-up grows roughly in proportion to k.
- **Exercise: jobs.** Expected: `max_profit_jobs([(0, 2, 5), (1, 4, 8), (2, 6, 7), (4, 7, 4)])` gives 12, and replacing `bisect_right` with `bisect_left` gives a wrong answer on this input. Then solve LeetCode 1235 (listed in the DP module) the same way.

> [!know]
> You now know how to speed up DP transitions with prefix sums, a monotonic deque or binary search, keeping the slow DP as the oracle.

=== primer | Why is a DP a shortest or longest path in a DAG, and what does that view buy you? | 14 min
goal: Draw any DP as a graph of states and transitions, read its answer as a shortest, longest or counted path, and switch to graph search when the state graph has cycles or is mostly unreachable
tag: dpadv-dag | DP as paths in a state graph
link: MIT 6.006 (Spring 2020) lecture 15 notes | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/9eb3e9a51a7b5b60b0f67c2277f8b0ee_MIT6_006S20_lec15.pdf#page=3 | 10 min: pages 3-5, 'Re-using Subproblem Solutions' (subproblem dependencies drawn as a DAG), 'Dynamic Programming' and 'DAG Shortest Paths' written in the SRT BOT recipe
link: Erickson, Algorithms ch. 6 | https://jeffe.cs.illinois.edu/teaching/algorithms/book/06-dfs.pdf#page=11 | 15 min: PDF pages 11-14, 'Dynamic Programming in Dags', including edit distance as a path in its dependency DAG

> [!key]
> Make every DP state a vertex and every transition an edge weighted by its cost. A DP never depends on itself, so the graph is a **DAG**: a topological order is an evaluation order, the base case is the source, and when each state builds on one predecessor the answer is a **shortest or longest path** (optimisation), a **number of paths** (counting) or **reachability** (feasibility). Memoised recursion is a DFS over this DAG. The view pays off three ways: reconstruction is following parent pointers, a state graph **with cycles** still yields to Dijkstra or BFS, and when few states are **reachable**, a graph search touches only those.

## Intuition

Picture the DP table as a road map: the cells are towns, each transition is a one-way road with a toll, and the recurrence "the best of my predecessors plus the road from them" is exactly the relaxation step of the weighted shortest paths module. Filling the table in order is driving through the towns in topological order. Once you see the map, two questions open up: what if the roads form loops, and what if most towns can never be reached from the start?

## How it works

### The dictionary

| DP | Graph |
|---|---|
| state (subproblem) | vertex |
| transition with cost c | edge with weight c |
| base case | source vertex |
| evaluation order | topological order |
| min or max recurrence | shortest or longest path |
| counting recurrence | number of paths |
| memoised recursion | DFS with a visited cache, following edges backwards |
| reconstructing the answer | following parent pointers from the target |

Most DPs in this guide fit directly. Edit distance is a shortest path through the grid of (i, j) states, moving right, down or diagonally; Myers' algorithm, behind Git's default diff, searches that same edit graph. 0/1 knapsack is a longest path through (item, capacity used) states. Held-Karp is a shortest path through (mask, last) states. The jieba word segmenter makes sentence positions the vertices and candidate words the edges, weighted by -log probability, so the most probable segmentation is a shortest path.

Interval and tree DPs are the one twist: a state such as `dp[i][j]` combines **two** smaller states (the two halves of a split), so its solution is a tree of subproblems rather than a single path (a hyperpath, in the jargon). The dependency graph is still a DAG and still fixes the evaluation order; only the "answer is one path" reading needs that adjustment.

### When the state graph has cycles

Some problems have transitions that can return to an earlier state: walking on a grid in all four directions, toggling switches back and forth, a robot that can undo a move. Then no topological order exists, "fill the table in order" has no order to follow, and memoised recursion loops forever. The graph view tells you what to do instead: with non-negative costs run **Dijkstra over the states**, with unit costs run **BFS**. That is exactly how the paths module handled (cell, keys held) and (vertex, coupon used): DP states, graph algorithms.

### When most states are unreachable

A table fills every state whether or not it matters. A search from the start touches only states that can actually occur. Take "the fewest operations to turn n into 1, where an operation subtracts 1, halves an even number or divides a multiple of 3 by 3". A bottom-up table needs an entry for every number up to n. A BFS from n reached 1 after visiting only 2,840 numbers when n = 10^9: the numbers that matter are those near n divided by small powers of 2 and 3.

## Cost

A DP costs O(states + transitions) when each transition is O(1), which is the cost of one pass over its DAG; building no explicit graph is the usual implementation. Swapping the table for BFS costs the same order on the reachable part only, with hashing overhead per state (a dictionary instead of a list). Swapping it for Dijkstra adds a log factor: O((S + T) log S). Counting paths stays linear in the DAG's size but needs care with modular arithmetic.

## When to use it

Use the DAG view when you design a DP (draw a few states and their edges before writing a recurrence), when you need the actual solution rather than its value (store parents), when the "DP" has transitions that can loop (switch to Dijkstra or BFS), and when the state space is huge but sparse (search from the start). Stay with a plain table when every state is reachable and the order is obvious: arrays beat dictionaries by a large constant factor in Python.

## Worked trace

Fewest operations from 10 to 1 (subtract 1, halve if even, divide by 3 if divisible), as BFS over states, levels in order.

```steps
Start at 10 with distance 0. Its successors are 9 (subtract 1) and 5 (halve)
    pop      10 (d=0)
    new      9, 5
    queue    [9, 5]
---
Pop 9 (d=1): successors 8 (subtract 1) and 3 (divide by 3)
    pop      9 (d=1)
    new      8, {{3}}
    queue    [5, 8, 3]
---
Pop 5 (d=1): only 4. Pop 8 (d=2): 7 (its half, 4, is already known)
    pop      5, then 8
    new      4, 7
    queue    [3, 4, 7]
---
Pop 3 (d=2): successors 2 and 1. The first time 1 is discovered, its distance is 3: 10, 9, 3, 1
    pop      3 (d=2)
    new      2, {{1}} (d=3)
    queue    [4, 7, 2, 1]
---
BFS pops 1 at distance 3 and stops. Ten states touched; a table would have filled all of 1..10, and at n = 10^9 the search touches 2,840 states instead of a billion
    answer   {{3}}   (10 -> 9 -> 3 -> 1)
```

## Template

```python
from collections import deque


def fewest_steps_to_one(n):
    """Fewest operations (subtract 1, halve if even, third if divisible by 3) to turn n into 1.
    Breadth-first search over the DAG of numbers: states are numbers, edges are operations."""
    dist = {n: 0}
    queue = deque([n])
    while queue:
        x = queue.popleft()
        if x == 1:
            return dist[x]
        for y in (x - 1, x // 2 if x % 2 == 0 else 0, x // 3 if x % 3 == 0 else 0):
            if y >= 1 and y not in dist:
                dist[y] = dist[x] + 1
                queue.append(y)
```

The same skeleton becomes Dijkstra by swapping the deque for a heap of (cost, state), and becomes a counted-paths DP by processing states in topological order and adding counts along edges.

## Pitfalls

- **Memoised recursion on a cyclic state graph** never terminates (or returns a value read from a half-finished state). If transitions can return to a state, use BFS or Dijkstra.
- **Dictionaries everywhere.** For dense state spaces, arrays indexed by an encoded state are several times faster in Python.
- **Reachability is not optimality.** BFS gives fewest steps only with unit costs; with varying costs use Dijkstra.
- **Huge sparse spaces need a target.** Searching from the start without an end condition explores everything reachable, which can still be enormous.

## Check yourself

Q: In the trace, 2 is discovered at distance 3 and also has 1 as a successor. Why does 1 keep distance 3?
A: BFS processes states level by level, so 1 was discovered from 3 at distance 3 before 2 was ever popped. A route through 2 would give 1 a distance of 4, and BFS ignores states already in `dist`, because with unit costs a later discovery can never be shorter.

Q: Why can't you fill a table for "fewest moves for a knight to reach each square of a chessboard"?
A: Knight moves go back and forth, so the state graph has cycles and no topological order exists: a square's value depends on squares that depend on it. BFS from the start square computes the same quantities in distance order, which is the order that a cyclic graph with unit costs allows.

Q: You need not just the minimum edit distance but the actual edits. What does the DAG view tell you to store?
A: A parent pointer per state, the predecessor (left, up or diagonal) that gave the minimum. Walking the pointers back from (m, n) to (0, 0) lists the edits in reverse, exactly like rebuilding a route from Dijkstra's parent array.

## Lab

- **Exercise: steps to one.** Expected: `fewest_steps_to_one(10)` gives 3 and `fewest_steps_to_one(10**9)` gives 30 while storing only a few thousand states. Write the bottom-up table version, check that both agree for every n up to 3,000, and compare their memory at n = 10^7.
- **Exercise: a DP as a graph.** Draw the state DAG of the four-city TSP trace in the bitmask card: vertices are (set, end) pairs, edges add one city and weigh its distance. Expected: 13 vertices from ({0}, 0) to the three full-set states, and the optimal tour is the path ({0}, 0), ({0,2}, 2), ({0,2,3}, 3), ({0,1,2,3}, 1) plus the closing edge back to 0: 15 + 30 + 25 + 10 = 80.

> [!know]
> You now know how to read any DP as a path problem in a DAG, rebuild solutions from parents, and switch to BFS or Dijkstra when states loop or are sparse.

=== practice
- 486 core
  cue: Two players alternately take a number from either end of a row; can the first player finish with at least as much as the second?
  hint: Both players always face the same kind of position, a contiguous stretch of the row. What single number about a stretch would let both use one formula?
  insight: Let dp[i][j] be the best score difference the player to move can force on nums[i..j]: max(nums[i] - dp[i+1][j], nums[j] - dp[i][j-1]). Fill by increasing length; player 1 wins when dp[0][n-1] >= 0.
  cost: O(n²) time, O(n) space with one row
  pattern: dpadv-interval
- 337 core
  cue: Houses form a binary tree, and two directly linked houses cannot both be robbed.
  hint: A node's best total depends on whether the node itself is robbed. How many numbers should each subtree report upwards?
  insight: Each subtree returns a pair (rob, skip): rob = val + left.skip + right.skip and skip = max(left) + max(right), computed children-first; the answer is the larger number of the root's pair.
  cost: O(n) time, O(h) space
  pattern: dpadv-tree
- 1986 core
  cue: At most 14 tasks must be packed into the fewest work sessions of a fixed length.
  hint: With so few tasks, the set of finished tasks can be the whole state. What else do you need to know to place the next task?
  insight: dp[mask] = (sessions used, time used in the current session), minimised as a pair; adding task i either fits in the current session or opens a new one. Masks in increasing order are a valid evaluation order.
  cost: O(2^n · n) time, O(2^n) space
  pattern: dpadv-bitmask
- 1547 core
  cue: Cut a stick at given points, each cut costing the length of the piece it splits; find the cheapest order.
  hint: Look at a segment between two neighbouring positions in the final set of cuts. What does the first cut made inside it leave behind?
  insight: Sort the cuts and add 0 and n; for positions i < j, dp[i][j] = c[j] - c[i] + min over k strictly between of dp[i][k] + dp[k][j]. The first cut inside a segment splits it into two independent segments.
  cost: O(m³) time, O(m²) space for m cuts
  pattern: dpadv-interval
- 312 derive
  cue: Burst balloons in a row for coins equal to the product of a balloon and its current neighbours; maximise the total.
  hint: Choosing the first balloon to burst makes its neighbours touch and tangles the two sides. Which balloon in a stretch has neighbours you know for certain?
  insight: Pad with 1s and let dp[l][r] be the best for the balloons strictly between l and r. If k bursts last there, its neighbours are l and r, so dp[l][r] = max over k of dp[l][k] + a[l]·a[k]·a[r] + dp[k][r], filled by increasing gap.
  cost: O(n³) time, O(n²) space
  pattern: dpadv-interval
- 2246 core
  cue: The longest path in a tree on which neighbouring nodes always carry different letters.
  hint: As with a diameter, every path has a highest node. What should each node report upwards, and what does it combine at its own level?
  insight: Each node returns its longest valid downward chain; at node u, keep the two longest chains from children whose letter differs from u's and update the answer with 1 + top1 + top2. Process nodes children-first using the parent array, without recursion.
  cost: O(n) time and space
  pattern: dpadv-tree
- 834 derive
  cue: For every node of a tree, the sum of its distances to all other nodes.
  hint: Solve it for one root first. When the root moves across one edge, which distances grow by one and which shrink by one?
  insight: One children-first pass computes subtree sizes and the root's total; moving the root from p to its child c gives ans[c] = ans[p] - size[c] + (n - size[c]), applied top-down from the root.
  cost: O(n) time and space
  pattern: dpadv-tree
- ac:dp_o core
  cue: Count the ways to pair N men with N women (N at most 21) when only some pairs are compatible, modulo 10^9 + 7.
  hint: If the men are paired in a fixed order, the number of women already taken tells you which man comes next. So what is the state?
  insight: dp[mask] counts the ways to pair the first popcount(mask) men with exactly the women in mask; the next man can take any compatible woman j outside mask, adding dp[mask] into dp[mask | 1 << j] modulo p.
  cost: O(2^N · N) time, O(2^N) space
  pattern: dpadv-bitmask
- 902 core
  cue: Count the positive integers up to n that can be written using only digits from a given set.
  hint: Numbers shorter than n are unrestricted. For numbers as long as n, what happens once a digit is smaller than n's digit at the same place?
  insight: Add d^len for every shorter length. Then walk n's digits: at each place add (allowed digits smaller than n's digit) times d^(places left), continue only if n's digit itself is allowed, and add 1 if all of n's digits are allowed.
  cost: O(L · d) time, O(1) extra space
  pattern: dpadv-digit
- ac:dp_s core
  cue: Count the integers from 1 to K, where K has up to 10,000 digits, whose digit sum is a multiple of D, modulo 10^9 + 7.
  hint: You can never list the numbers, only choose their digits from the left. What is the least you must remember about the digits chosen so far?
  insight: Digit DP over (position, digit sum mod D, tight), filled as a table over K's digits rather than by recursion; it also counts 0, so subtract 1 and reduce modulo p.
  cost: O(len(K) · D · 10) time, O(D) space per position
  pattern: dpadv-digit
- 943 stretch
  cue: Find a shortest string that contains each of up to 12 given words.
  hint: Writing the words one after another, each consecutive pair saves its overlap. Which famous ordering problem is that?
  insight: Precompute overlap[i][j]; dp[mask][last] is the largest total overlap of an order of the words in mask ending with last. Rebuild the order from parent pointers and glue the words, skipping each overlap.
  cost: O(n² · 2^n + n² · L) time, O(n · 2^n) space
  pattern: dpadv-bitmask
- 2376 stretch
  cue: Count the integers from 1 to n whose digits are all different.
  hint: Build numbers from the left. What must you remember about the digits so far, and how do you stop leading zeros counting as used digits?
  insight: Digit DP over (position, used-digit mask, tight, started): leading zeros keep started false and leave the mask alone; a digit is allowed only if its bit is not set; count the states that end with started true.
  cost: O(L · 2^10 · 10) time, O(L · 2^10) space
  pattern: dpadv-digit
