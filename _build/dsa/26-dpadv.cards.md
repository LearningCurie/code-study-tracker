=== card | 486

## The problem

Two opponents share a row of integer scores. On each turn the current player removes either the leftmost or rightmost remaining score and adds it to their own total. Both play optimally for their own final score. Return whether the first player can finish with at least the second player's total; a tie counts as success. For `[1, 5, 2]`, the first player cannot secure a tie.

## Constraints and what they imply

The row contains 1 to 20 nonnegative integers, each at most ten million. Picking from an end leaves a contiguous interval, so there are only quadratically many distinct positions despite exponentially many possible move sequences. Scores can be large, so reason about totals, not merely which player takes the larger number on one turn. Python integers avoid overflow.

## Brute force

Explore both legal end choices until the row is empty, alternating which total receives the chosen value. A minimax search returns the best outcome under optimal opposition. Its branching can create O(2^n) move sequences and O(n) recursion depth. Many sequences reach the same interval; caching or tabulation removes that repeated work.

## The insight

Define the value of an interval as the largest final score difference, current player minus other player, that its player to move can force. If they take the left value, the other player becomes the current player on the remaining interval, whose optimal difference is subtracted. The right choice is symmetric. Each choice really is achievable, and the opponent can enforce the stated remainder, so the larger of the two differences is exactly the minimax value. A singleton has value equal to its number.

For fixed left endpoint, build right endpoints upward. Before updating `dp[j]`, it holds the value for the interval starting one position later; `dp[j-1]` has already been updated for the current left endpoint. Thus the original two-dimensional recurrence needs only one array.

## Optimal solution, traced

On `[1, 5, 2]`:

```steps
Singletons
dp = [1, 5, 2].
---
Left endpoint 1
Interval [5, 2] has value max(5 - 2, 2 - 5) = 3.
---
Left endpoint 0
Interval [1, 5] has value 4. The whole row has value max(1 - 3, 2 - 4) = -2, so the answer is false.
```

## Code

```python
def first_player_can_tie(nums):
    dp = nums[:]
    for i in range(len(nums) - 2, -1, -1):
        for j in range(i + 1, len(nums)):
            dp[j] = max(nums[i] - dp[j], nums[j] - dp[j - 1])
    return dp[-1] >= 0
```

## Complexity

There are O(n²) interval updates, each constant time. The copied array uses O(n) auxiliary space and leaves the input unchanged. The nonempty-row constraint ensures that the final entry exists.

## Mistakes and edge cases

Subtract the opponent's optimal difference rather than adding it; the roles have switched. Iterate right endpoints from left to right, because the opposite order reads an old state for the shorter interval. A singleton is always won under the stated nonnegative constraints, and zero differences must return true. A greedy choice of the bigger endpoint can sacrifice a better future reply.

## Variations

- Retain the full interval table and record decisions to reconstruct optimal moves.
- Return the maximum score difference instead of converting it to a Boolean result.

=== card | 337

## The problem

Each node of a binary tree contains a nonnegative amount. Choose nodes with maximum total value, subject to never choosing both ends of a parent-child edge. Return that maximum. For a root worth 3 with children worth 2 and 4, skipping the root yields 6. The supplied node objects expose `val`, `left`, and `right`.

## Constraints and what they imply

There can be up to 10,000 nodes, with values from zero to 10,000. The tree may be a long chain, so a recursive implementation could exceed Python's recursion limit. A child subtree interacts with the rest of the tree only through whether its root is selected. An empty tree is supported here and contributes zero, even though standard inputs are nonempty.

## Brute force

Enumerate all subsets of the nodes, discard any subset containing an adjacent pair, and maximize the sum. This takes O(n 2^n) time with a straightforward adjacency check and O(n) working space. It ignores that once a parent's choice is fixed, separate child subtrees can be optimized independently.

## The insight

For each subtree calculate two totals: the best if its root is selected and the best if it is skipped. Selecting a root forces both children to be skipped, while skipping it permits the better of each child's two choices. These are exhaustive and independently achievable because the child subtrees have no cross edges. Induction from empty children therefore proves both totals optimal.

Use an explicit stack with an enter/exit marker to obtain postorder without recursive calls. Store child pairs until their parent is processed, and remove them when consumed. The null child contributes `(0, 0)`. The root answer is the larger of its two totals.

## Optimal solution, traced

For a root of value 3 and two leaf children 2 and 4:

```steps
Leaves
The left child reports (take 2, skip 0); the right reports (take 4, skip 0).
---
Root
Taking it gives 3 + 0 + 0 = 3. Skipping it gives 2 + 4 = 6.
---
Result
The maximum of the two root states is 6.
```

## Code

```python
def max_tree_robbery(root):
    if root is None:
        return 0
    stack = [(root, False)]
    values = {}
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
        else:
            left = values.pop(id(node.left), (0, 0))
            right = values.pop(id(node.right), (0, 0))
            values[id(node)] = (node.val + left[1] + right[1],
                                max(left) + max(right))
    return max(values[id(root)])
```

## Complexity

Each node is entered and exited once, so time is O(n). The explicit postorder stack and the retained sibling results occupy O(h) space for tree height h, including a chain's O(n) worst case. Node identities, not values, distinguish equal-valued nodes.

## Mistakes and edge cases

A parent may be skipped even if it is more valuable than either child individually; compare the combined subtree outcomes. Grandchildren may be chosen together with their grandparent. A zero-valued leaf is harmless. Avoid keying states by node value and avoid relying on recursion for a deep tree. The input must be a tree, not a graph with shared children.

## Variations

- Keep take/skip decisions to recover a set of selected nodes.
- Generalize from two children to an arbitrary number of children using sums over their states.

=== card | 1986

## The problem

Given a list of indivisible task durations and a fixed session capacity, schedule every task into as few sessions as possible. Tasks may be reordered, but each must fit wholly within one session. Return the number of sessions. For durations `[1, 2, 3]` and capacity 3, two sessions suffice: one with 3 and one with 1 and 2.

## Constraints and what they imply

There are 1 to 14 tasks. Durations are positive and individually no larger than the session capacity, which is at most 15. A task subset can therefore be encoded in 14 bits. The sum divided by capacity gives only a lower bound: indivisible durations can prevent an exact packing. This implementation also accepts an empty list and returns zero.

## Brute force

Assign each task to a labeled session and try all feasible assignments, or enumerate task orders and possible session breaks. The number of possibilities grows exponentially or worse, and many different assignments represent the same set of completed tasks. A mask avoids revisiting equivalent subsets while keeping just enough information about the last session.

## The insight

For each mask store the lexicographically smallest pair `(sessions, load)` among schedules of those tasks, where load is the time used in the most recently opened session. Appending a task either fits there or starts another session. A smaller pair dominates a larger one for all future append operations: if their session counts agree, a smaller load fits at least as much; if one uses fewer sessions, it can open an extra session before falling behind, and when counts become equal its current load is no greater. Thus discarding the larger pair cannot lose an optimal completion.

Every packing can be ordered by listing its sessions and then the tasks within each session. Consequently appending tasks covers an optimal packing. Adding a bit always increases the mask, so increasing numeric order evaluates predecessors first. Seed the empty mask with zero sessions and zero load; the first task explicitly opens a session.

## Optimal solution, traced

For capacity 3 and tasks `[1, 2, 3]`:

```steps
Empty
The state is (0, 0); adding task 1 opens a session and produces (1, 1).
---
Combine
Adding task 2 to that mask fits, producing (1, 3).
---
Finish
Task 3 opens a second session, giving (2, 3). The alternative order with task 3 first also uses two sessions, so the answer is 2.
```

## Code

```python
def min_work_sessions(tasks, capacity):
    n = len(tasks)
    dp = [(n + 1, 0)] * (1 << n)
    dp[0] = (0, 0)
    for mask in range(1 << n):
        sessions, load = dp[mask]
        for i, duration in enumerate(tasks):
            if mask & (1 << i):
                continue
            if sessions and load + duration <= capacity:
                candidate = (sessions, load + duration)
            else:
                candidate = (sessions + 1, duration)
            nxt = mask | (1 << i)
            dp[nxt] = min(dp[nxt], candidate)
    return dp[-1][0]
```

## Complexity

There are 2^n masks and at most n outgoing choices per mask: O(n 2^n) time and O(2^n) auxiliary space. The tuple comparison is constant time. The state represents the used load, not remaining capacity, so smaller is preferable on a tie.

## Mistakes and edge cases

Do not treat each task as splittable across sessions or assume the total-duration lower bound is attainable. Exact capacity fits in the current session. Repeated durations are still distinct tasks, represented by different bits. The code assumes every duration fits by itself; reject oversized tasks separately if a different interface permits them. An empty list requires no sessions.

## Variations

- Store a predecessor per mask to recover one optimal sequence of tasks and its session breaks.
- For a small capacity but many tasks, investigate frequency-based packing rather than a mask over individual tasks.

=== card | 1547

## The problem

A stick runs from coordinate 0 to coordinate `length`. Every coordinate in a given list must be cut once. When a cut is made, its cost is the current length of the piece being divided. Choose an order of cuts with minimum total cost and return that cost. For length 7 and cut positions `[1, 3, 4, 5]`, an optimal total is 16. The coordinates refer to the original stick throughout; cutting does not renumber them.

## Constraints and what they imply

The length is at most 1,000,000, with 1 to 100 distinct integer cuts strictly inside the stick. Since cost depends on the surrounding already-made cuts, sorting by coordinate or always cutting the shortest current piece is not obviously optimal. There are far too many possible orders to enumerate, but every current piece is bounded by two positions in the sorted set of cuts plus the endpoints. This gives O(m²) possible intervals for m cut positions. The function also handles an empty cut list and returns zero.

## Brute force

Try all m! permutations of the cuts. For each permutation simulate the current pieces or maintain sorted boundaries, and add the length of the piece containing the next position. This directly describes the objective but repeats the same segment choices in many orders. A simple simulation with linear boundary searches costs O(m · m!) time and O(m) space, excluding the input. It is useful only for tiny instances and serves as an independent check of a dynamic program.

## The insight

Sort the coordinates and include the two endpoints. Consider the open interval between boundary indices `i` and `j`. If there are no required positions strictly inside it, its remaining cost is zero. Otherwise some interior position `k` must be the first cut in this piece. That first cut always costs the full boundary distance, regardless of where `k` lies. It produces two independent pieces; all subsequent cuts occur in one or the other. Their optimal costs can therefore be added.

Take the minimum over every legal first cut. Any valid cutting order has one such first cut and cannot beat the optimal costs of its two resulting pieces, giving a lower bound. Conversely, perform a minimizing first cut followed by optimal orders for both pieces. This achieves the bound. Induction over the number of interior coordinates proves the recurrence.

Fill intervals by increasing index gap. Both child gaps are strictly smaller than the parent's, so their values are ready. Adjacent boundaries need no work. Copy before sorting so callers retain their original cut order. The algorithm optimizes total cost rather than producing the actual sequence; a recorded minimizing index would recover it.

## Optimal solution, traced

Take length 7 with cuts `[1, 3]`, giving boundaries `[0, 1, 3, 7]`:

```steps
Base intervals
Each pair of adjacent boundaries has cost 0 because it contains no cut.
---
One internal cut
The interval 0 to 3 costs 3, and the interval 1 to 7 costs 6.
---
Whole stick
Cutting at 1 first costs 7 + 0 + 6 = 13. Cutting at 3 first costs 7 + 3 + 0 = 10. Return 10.
```

The first operation is charged once at its own enclosing piece. The child costs already include all later operations, so adding another copy of their boundary lengths would double count.

## Code

```python
def min_cut_cost(length, cuts):
    points = [0] + sorted(cuts) + [length]
    size = len(points)
    dp = [[0] * size for _ in range(size)]
    for gap in range(2, size):
        for left in range(size - gap):
            right = left + gap
            dp[left][right] = points[right] - points[left] + min(
                dp[left][mid] + dp[mid][right]
                for mid in range(left + 1, right)
            )
    return dp[0][-1]
```

## Complexity

There are O(m²) boundary pairs, each considering up to m first cuts, for O(m³) time and O(m²) auxiliary space. Sorting costs O(m log m) and the copied boundary list uses O(m) space, both dominated for the intended sizes. The numerical stick length affects the values but not the number of states.

## Mistakes and edge cases

The cost is the current piece's length, not the distance from the cut to one side. Include 0 and the full length as permanent boundaries, and do not treat them as required cuts. Sort an unsorted input before constructing intervals. One cut costs the full stick length; no cuts cost zero. Duplicate or out-of-range positions violate the contract and should be validated separately if accepted by an application. Choosing a middle cut can help on some inputs but is not a correctness proof.

## Variations

- Save the best first cut per interval and traverse the resulting split tree to reconstruct an optimal order.
- If each cut has an additional fixed fee, add that fee for its selected position in each transition.

=== card | 312

## The problem

A row of balloons has nonnegative integer values. When one is removed, earn its value multiplied by the values of its two current neighbors. Beyond each end, an imaginary neighbor has value 1 and remains present. Continue until the row is empty and return the largest achievable total. For `[3, 1, 5, 8]`, the optimum is 167. Removing a balloon makes its former neighbors adjacent, so their future rewards may change.

## Constraints and what they imply

The row contains at most 300 balloons, each valued from 0 to 100. The official input is nonempty; the implementation also gives zero for an empty row. There are factorially many removal orders, but the useful subproblems can be intervals bounded by balloons that are temporarily retained. Zero values are legal, and removing one can change neighboring products even when its own reward is zero.

## Brute force

For each current row, try removing each index, add its immediate reward, and recursively explore the remaining row. The total is the maximum across the resulting orders. There are n! possible orders and O(n) work per naive removal and copy, giving O(n · n!) time and O(n²) memory along a copying recursion stack. This simulation naturally handles the changing neighbors and is a valuable oracle for short rows, but it does not scale.

## The insight

Choosing the first removal in a segment is awkward: the two sides become neighbors and influence one another. Instead fix the last balloon `k` removed strictly between two retained boundaries `left` and `right`. By that time, every other interior balloon is gone, so its reward is exactly the product of those two boundary values and its own value. The earlier removals lie entirely in the two smaller open intervals. The boundaries remain present throughout, so those two subproblems can be optimized independently.

For any complete order, its final interior removal identifies one such `k`; its earlier rewards are bounded by the best values for the two subintervals. Conversely, run the two optimal suborders in either sequence while keeping the boundaries, then remove `k` last. This achieves their sum plus the final product. Taking the maximum over `k` proves the recurrence. Padding the row with ones handles the external neighbors without special transitions.

Initialize an interval with no interior balloon to zero and increase the gap between boundary indices. Both intervals around a candidate have smaller gaps, ensuring their answers have already been computed. The calculation does not mutate the supplied list. Retaining a maximizing index allows later reconstruction of an order: recursively perform the two interior orders before bursting the recorded last balloon.

## Optimal solution, traced

For `[2, 3]`, padding yields `[1, 2, 3, 1]`:

```steps
Single-balloon intervals
Removing 2 between boundaries 1 and 3 earns 6. Removing 3 between boundaries 2 and 1 earns 6.
---
Choose the last balloon
If 2 is last, the total is 6 + 1*2*1 = 8. If 3 is last, it is 6 + 1*3*1 = 9.
---
Result
Return 9, achieved by removing 2 first and 3 second.
```

The single-balloon subproblem containing 2 uses 3 as its right boundary because 3 has not yet been removed in that candidate order.

## Code

```python
def max_burst_coins(nums):
    values = [1] + list(nums) + [1]
    size = len(values)
    dp = [[0] * size for _ in range(size)]
    for gap in range(2, size):
        for left in range(size - gap):
            right = left + gap
            dp[left][right] = max(
                dp[left][k] + values[left] * values[k] * values[right]
                + dp[k][right]
                for k in range(left + 1, right)
            )
    return dp[0][-1]
```

## Complexity

O(n²) open intervals each try O(n) final balloons, so time is O(n³). The table and padded values use O(n²) auxiliary space. The cost does not depend on the magnitudes except for integer arithmetic; Python's integers avoid fixed-width overflow.

## Mistakes and edge cases

The boundary balloons are not removed inside the state; including them among candidates breaks the recurrence. Reward is based on current neighbors, not the original neighbors. A singleton earns its own value because both outside neighbors equal one. All-zero rows return zero, and an empty row has no reward. Do not assume the same recurrence works unchanged for negative values if using zero as a default for a nonempty interval; the code explicitly maximizes over real candidates.

## Variations

- Record the last choice in every interval and output a maximizing removal order.
- Replace the outside ones with specified permanent boundary values and reuse the interval formulation.

=== card | 2246

## The problem

A rooted tree is described by a parent array and one character per node. A path is valid when every pair of consecutive nodes on it has different characters. Return the maximum number of nodes on any valid simple path; the path may pass through the root, remain inside one subtree, or contain just one node. For parents `[-1, 0, 0]` and labels `"aba"`, the best path has two nodes: node 0 and node 1.

## Constraints and what they imply

There are 1 to 100,000 nodes, root 0 has parent -1, and the other parent entries describe a valid rooted tree. Labels are lowercase letters. Parent indices need not be smaller than their children's indices, so merely scanning indices backward is not necessarily a postorder. A chain can be as deep as the entire tree; an explicit traversal avoids Python recursion limits. Count nodes, not edges.

## Brute force

For each pair of endpoints, find their unique tree path, check every adjacent label pair, and keep the longest valid path. Up to O(n²) pairs each require O(n) work with a simple path search, for O(n³) time and O(n) auxiliary space. This is a useful small-tree oracle. A single traversal can instead reuse the best partial path already computed below each node.

## The insight

Root the tree as given. Any simple path has a highest node: its endpoints lie in at most two different child subtrees of that node, and the rest of the path descends from it. Let each node report its longest valid downward chain including itself. For a parent, only children with a different label can extend such a chain across the connecting edge. Among those, the largest child chain supplies the best downward report, while the two largest together supply the best path whose highest node is the parent.

This considers every possible highest node. For a fixed highest node, using more than two child branches would not form a simple path; using anything shorter than the best eligible chain in a chosen branch cannot improve its length. Conversely, joining the two eligible chains through the node gives a valid path. By induction from leaves, the downward reports and the maximum over all nodes are exact.

Build children lists, then visit nodes from the root to obtain an order. Reversing that order ensures each child is processed before its parent regardless of numeric labels. Store the lengths in an array and retain the largest and second-largest eligible contributions at each node. A global maximum also catches paths that never pass through the root. A leaf has a chain length of one, and zero is a convenient absent-branch length.

## Optimal solution, traced

For parent array `[-1, 0, 0, 1]` and labels `"abca"`:

```steps
Leaves
Nodes 2 and 3 each report a downward chain of length 1.
---
Node 1
Its label b differs from child 3's a, so it reports 2 and offers a two-node path.
---
Node 0
Both children differ from a. Their contributions are 2 and 1, so a path through 0 has 1 + 2 + 1 = 4 nodes.
```

The global answer is 4, corresponding to nodes 3, 1, 0, and 2. The two branches are distinct because each child is examined exactly once.

## Code

```python
def longest_distinct_adjacent_path(parent, labels):
    n = len(parent)
    children = [[] for _ in range(n)]
    for node in range(1, n):
        children[parent[node]].append(node)
    order = [0]
    for node in order:
        order.extend(children[node])
    down = [1] * n
    best = 1
    for node in reversed(order):
        first = second = 0
        for child in children[node]:
            if labels[child] == labels[node]:
                continue
            length = down[child]
            if length > first:
                first, second = length, first
            elif length > second:
                second = length
        down[node] = 1 + first
        best = max(best, 1 + first + second)
    return best
```

## Complexity

Building children, collecting the traversal order, and processing each edge take O(n) time. Children lists, the traversal order, and downward lengths use O(n) auxiliary space. Reversing an existing list does not introduce recursive frames. The answer is at most n.

## Mistakes and edge cases

Comparing labels across a child edge is essential; a same-label child may still contain the best path deeper in its own subtree, so do not discard the entire subtree from processing. The two selected chains must come from different children. The global result may be a leaf, including when every label is identical. A one-node tree returns one, not zero. Parent-array indexing order is not a substitute for a real topological traversal.

## Variations

- Retain the endpoints of the two best chains to reconstruct an actual longest path.
- Replace unequal labels with any symmetric edge predicate; the same path-combination argument still applies.

=== card | 834

## The problem

For every vertex of an undirected tree, compute the sum of its edge distances to all vertices, including itself. Return the sums in vertex-number order. In a three-node path with edges `0-1` and `1-2`, the result is `[3, 2, 3]`: the middle has distance one to each endpoint, while an endpoint has distances one and two to the others.

## Constraints and what they imply

There are 1 to 30,000 vertices numbered from zero and exactly n-1 edges forming a connected tree. Each edge has unit length. One search from each vertex is correct but quadratic, whereas moving the root across one edge changes all distances in a predictable way. A path-shaped tree can have depth n, so iterative passes avoid recursive stack limits. Python integer sums can exceed 32-bit range without overflowing.

## Brute force

Run breadth-first search from every starting vertex, summing the distances discovered in that search. A tree has O(n) vertices and edges, so this costs O(n²) time and O(n) working space, besides the output. It is an excellent oracle for small random trees but repeats nearly identical work for adjacent starting vertices.

## The insight

First choose node 0 as a temporary root. A traversal supplies each node's parent and distance from 0, so summing those distances gives the first answer. In reverse traversal order, add each child's subtree size to its parent, counting every vertex once. Now imagine shifting the root from a parent `p` to its child `c`. All `size[c]` vertices in c's subtree become one edge closer. Each of the remaining `n - size[c]` vertices becomes one edge farther. Therefore the new sum equals the old sum minus `size[c]` plus `n - size[c]`.

Every vertex belongs to exactly one of those groups because removing edge `p-c` separates a tree into two components. This proves the update, not merely a heuristic. Processing children after parents propagates the root answer along the unique path from node 0 to each vertex. The original subtree sizes remain defined with respect to the temporary root; they are not recomputed after each conceptual move.

Construct a parent-before-child order iteratively. The reverse order computes sizes; the forward order computes the rerooted sums. The parent array doubles as a visited marker, with root assigned itself so it is never revisited through a neighbor. No distances between arbitrary pairs need to be stored.

The choice of initial root is arbitrary: it changes the intermediate sizes and first sum but not the requested output. Every later result follows by applying the same edge argument, so the method does not depend on vertex numbering or adjacency-list order.

## Optimal solution, traced

For the path `0-1-2`:

```steps
Root at 0
Depths are [0, 1, 2], so the root sum is 3. Subtree sizes are [3, 2, 1].
---
Move from 0 to 1
Two vertices get closer and one gets farther: answer[1] = 3 - 2 + 1 = 2.
---
Move from 1 to 2
One vertex gets closer and two get farther: answer[2] = 2 - 1 + 2 = 3.
```

The sizes in the last step are still those measured under root 0; the final array is `[3, 2, 3]`.

## Code

```python
def tree_distance_sums(n, edges):
    graph = [[] for _ in range(n)]
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    parent = [-1] * n
    parent[0] = 0
    depth = [0] * n
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if parent[neighbor] == -1:
                parent[neighbor] = node
                depth[neighbor] = depth[node] + 1
                order.append(neighbor)
    size = [1] * n
    for node in reversed(order[1:]):
        size[parent[node]] += size[node]
    answer = [0] * n
    answer[0] = sum(depth)
    for node in order[1:]:
        answer[node] = answer[parent[node]] + n - 2 * size[node]
    return answer
```

## Complexity

The adjacency list contains 2(n-1) entries. Both traversals and all array initialization take O(n) time, and graph storage plus the working arrays take O(n) auxiliary space. The returned n-element list itself also requires O(n) space. A root-only tree produces `[0]` without any edge transitions.

## Mistakes and edge cases

Distances are measured in edges; the root's own distance is zero. Subtract the child's subtree size and add the complement, not the other way around. Use the same initial rooting when interpreting every size. Do not rely on the input edge orientation: these edges are undirected. The interface assumes a connected tree with n at least one; a disconnected graph or cycle would require separate validation and a different proof.

## Variations

- For positive edge weights, multiply the reroot adjustment by the weight of the crossed edge and use weighted root distances.
- Replace a plain count of vertices with vertex weights to calculate weighted distance sums.

=== card | ac:dp_o

## The problem

There are equally many people on two sides of a matching. A Boolean square matrix says which pairs are allowed. Count the one-to-one assignments that use every person exactly once and use only allowed pairs. Return the count modulo 1,000,000,007. For `[[1, 1], [1, 1]]`, either assignment works, so the answer is 2. Matrix rows identify the first side and columns the second.

## Constraints and what they imply

The matrix has size N by N with 1 <= N <= 21 and entries zero or one. N! assignments are too numerous, but a mask of the used columns has at most 2^21 possibilities. The number of used columns also determines how many rows have already been assigned, so no additional row dimension is needed. The implementation naturally returns one for an empty matrix: the empty assignment.

## Brute force

Enumerate all N! permutations of columns and test each row's chosen entry. This uses O(N · N!) time and O(N) space with a typical permutation generator. It is an independent way to verify small matrices, but most permutations share partial assignments that can be counted together.

## The insight

Let `dp[mask]` count assignments of the first `popcount(mask)` rows to exactly the columns in the mask. Initially the empty mask has one assignment. For a state with k bits, the next row is k; append any allowed column whose bit is not yet set. Adding the state's count to the new mask counts every extension.

Each full assignment has exactly one final column for the last row, and deleting that assignment gives exactly one predecessor. Therefore the recurrence neither misses nor duplicates any assignment. Increasing numeric mask order works because setting an unset bit strictly increases the mask. Reduction after each addition preserves the final residue because addition respects modular equivalence. There is no modular division involved.

## Optimal solution, traced

For `[[1, 1], [1, 1]]`:

```steps
Empty mask
dp[00] = 1. Row 0 may select either column, producing dp[01] = dp[10] = 1.
---
One selected column
From 01, row 1 can select column 1; from 10, it can select column 0.
---
Complete mask
dp[11] = 1 + 1 = 2, the answer.
```

## Code

```python
def count_matchings(allowed):
    mod = 1_000_000_007
    n = len(allowed)
    dp = [0] * (1 << n)
    dp[0] = 1
    for mask in range(1 << n):
        row = mask.bit_count()
        if row == n:
            continue
        for col in range(n):
            if allowed[row][col] and not (mask & (1 << col)):
                nxt = mask | (1 << col)
                dp[nxt] = (dp[nxt] + dp[mask]) % mod
    return dp[-1]
```

## Complexity

There are 2^N masks and at most N column checks per mask, so time is O(N 2^N) and auxiliary space is O(2^N). Modular reduction bounds stored counts. Bit counting and masks are constant-size operations under the stated N <= 21 bound.

## Mistakes and edge cases

Each row must be used once; a compatible column already present in the mask cannot be selected again. An all-zero row forces the result to zero. A 1-by-1 matrix returns its sole entry. Do not iterate the next row after the full mask or reduce Boolean compatibility itself modulo the count. The algorithm assumes a square matrix.

## Variations

- Track predecessors for a single valid assignment rather than its count.
- To handle more columns than rows, stop when the mask has the number of bits equal to the number of rows and sum those states.

=== card | 902

## The problem

You are given a set of allowed nonzero decimal digits and a positive integer bound. Count the positive integers no greater than the bound whose decimal representation uses only digits from that set. Digits may be reused. For digits `['1', '3']` and bound 31, the valid numbers are 1, 3, 11, 13, and 31, so the answer is 5. The bound itself counts when all of its digits are permitted.

## Constraints and what they imply

The digit set contains distinct characters from `'1'` through `'9'`, and the positive bound is at most 10^9. Excluding zero means every choice in a shorter representation is valid as a leading digit. A direct scan to the bound can be far larger than the number of decimal positions. Comparing equal-length decimal strings digit by digit captures numeric order because their lengths match.

## Brute force

Visit each integer from 1 through the bound, convert it to decimal, and check every character against the set. This takes O(bound · L) time in the worst case for L digits and O(L) temporary space for the conversion. Alternatively, generate all allowed digit strings, but there can still be exponentially many in L. Both approaches are practical as checks only for small bounds.

## The insight

Partition candidates by length. Every positive number with fewer digits than the bound is automatically smaller, and each of its positions has d independent choices, giving d^k candidates of length k. For numbers with the same length, scan the bound from left to right while maintaining that the chosen prefix equals its prefix. At each position, choose an allowed digit smaller than the bound's digit: the prefix is now strictly smaller, so every suffix of the remaining length is unrestricted. Add `count_smaller * d^remaining`.

If the bound's digit is allowed, continue along the unique equal-prefix branch. Otherwise that branch cannot represent a valid number and must stop. If all positions are matched, add one for the bound itself. The cases are disjoint: every smaller equal-length number has a unique first position where it differs. They are also exhaustive, because at that first difference the candidate's digit must be smaller. The shorter cases and the bound itself are separate from these branches, proving the count.

No sorted input is required: counting comparisons against each digit yields the same number regardless of order. An empty set, though outside the usual constraints, produces zero. The procedure uses no recursion or state per candidate and does not rely on generating the actual numbers. Leading zeros require a different treatment; they are excluded by this interface rather than silently counted as full-length representations.

## Optimal solution, traced

For digits `['1', '3']` and bound 31:

```steps
Shorter lengths
There are 2 one-digit choices: 1 and 3.
---
First digit of 31
Choosing 1 instead of 3 leaves two choices for the last digit, contributing 11 and 13. Digit 3 is allowed, so follow the equal branch.
---
Second digit and equality
No allowed digit is below 1. Digit 1 is allowed, so add the bound 31 itself. Total: 2 + 2 + 1 = 5.
```

If the first bound digit were absent from the allowed set, all smaller first-digit branches would still be counted before the equality branch stopped.

## Code

```python
def count_allowed_numbers(digits, bound):
    if bound <= 0 or not digits:
        return 0
    text = str(bound)
    d = len(digits)
    total = sum(d ** length for length in range(1, len(text)))
    for i, current in enumerate(text):
        smaller = sum(digit < current for digit in digits)
        total += smaller * d ** (len(text) - i - 1)
        if current not in digits:
            return total
    return total + 1
```

## Complexity

With L bound digits and d allowed digits, there are O(Ld) digit comparisons and O(L) power expressions. Under the fixed official bound and digit alphabet, this is O(Ld) time and O(L) space including the decimal string; integer exponentiation and arbitrary-precision arithmetic are not literally constant time for unbounded L. No array proportional to the bound or number of answers is allocated.

## Mistakes and edge cases

Do not count zero: all allowed digits are nonzero and positive lengths start at one. Include the bound only if every one of its digits is allowed. At a missing equal-prefix digit, add the smaller branches first and then stop. Reuse of digits is allowed, so suffix choices are powers rather than permutations. The interface assumes unique digit characters; duplicates would incorrectly multiply counts. A digit set containing zero needs a separate leading-digit rule.

## Variations

- Count valid values in an inclusive interval by subtracting counts up to one below its lower endpoint.
- Permit zero in the set by treating the first digit separately from later positions.

=== card | ac:dp_s

## The problem

Given a positive decimal integer K as a string and a positive divisor D, count integers from 1 through K whose decimal digit sums are divisible by D. Return the count modulo 1,000,000,007. For K = `"20"` and D = 2, the qualifying numbers include 2, 4, 6, 8, 11, 13, 15, 17, 19, and 20, giving 10.

## Constraints and what they imply

K can contain up to 10,000 digits, and 1 <= D <= 100. Converting K to a machine integer or recursing once per digit is unnecessary and may fail in Python. Its representation has no leading zero and K is positive. Only the remainder of the digit sum matters, so two rolling arrays of D counts suffice for each tightness category.

## Brute force

For a small numeric bound, loop from 1 to K, sum each number's decimal digits, and count remainders equal to zero. This uses O(K · L) time for L digits and O(L) conversion space. It is infeasible for a 10,000-digit bound but is independent enough to test the digit-state implementation on short inputs.

## The insight

Pad all candidates with leading zeros to the length of K. Each integer from 0 to K then has exactly one padded representation, and padding does not change digit sum. Process positions from left to right, recording the sum modulo D and whether the chosen prefix is exactly equal to K's prefix. A tight state may choose at most the current bound digit; a loose state may choose any digit. The new state remains tight only when the old state was tight and the selected digit equals the bound digit.

Every legal padded prefix has exactly one predecessor and last digit. The transitions enumerate those pairs once, so induction gives the correct count for every state. At the end, sum both tightness categories with remainder zero. The all-zero representation is included exactly once; subtract it to restrict the count to positive integers, then reduce modulo the modulus. Leading zeros are safe here because they contribute nothing to the sum.

## Optimal solution, traced

For K = `"12"`, D = 3:

```steps
First digit
Choosing 0 creates a loose prefix with remainder 0; choosing 1 creates a tight prefix with remainder 1.
---
Second digit
The loose prefix can choose 0 through 9, producing remainder zero for 00, 03, 06, and 09. The tight prefix may choose 0 through 2, adding 12.
---
Remove zero
Five padded representations qualify including 00; subtract one to return 4 for 3, 6, 9, and 12.
```

## Code

```python
def count_digit_sum_multiples(bound, divisor):
    mod = 1_000_000_007
    loose = [0] * divisor
    tight = [0] * divisor
    tight[0] = 1
    for char in bound:
        limit = int(char)
        next_loose = [0] * divisor
        next_tight = [0] * divisor
        for remainder in range(divisor):
            for digit in range(10):
                target = (remainder + digit) % divisor
                next_loose[target] = (next_loose[target] + loose[remainder]) % mod
            for digit in range(limit + 1):
                target = (remainder + digit) % divisor
                if digit == limit:
                    next_tight[target] = (next_tight[target] + tight[remainder]) % mod
                else:
                    next_loose[target] = (next_loose[target] + tight[remainder]) % mod
        loose, tight = next_loose, next_tight
    return (loose[0] + tight[0] - 1) % mod
```

## Complexity

For L decimal digits, each position updates at most 20D digit transitions, giving O(L D · 10) time and O(D) auxiliary space, excluding the input string. Counts are reduced throughout so they remain bounded. The explicit iteration handles long bounds without a recursion limit or integer conversion.

## Mistakes and edge cases

Subtract zero once, not once per leading-zero length. Preserve tightness only for an equal digit selected from a tight prefix; a loose prefix never becomes tight again. When D is 1, every positive number qualifies, so the answer is K modulo the modulus. Reducing the subtraction handles a negative intermediate residue correctly. The contract requires a positive divisor and a valid nonnegative decimal string.

## Variations

- Subtract the counts for two bounds to answer an inclusive range query, taking care at the lower endpoint.
- Track another finite-state property, such as a forbidden adjacent digit pair, alongside the remainder.

=== card | 943

## The problem

Given a collection of words, return any shortest string containing every word as a contiguous substring. The same character positions may serve several words when their endings and beginnings overlap. For `['ab', 'bc', 'ca']`, one valid shortest answer is `abca`; other equally short answers are acceptable. The output is the string itself, not just its length. Input order does not constrain the order in the result.

## Constraints and what they imply

There are at most 12 nonempty lowercase words, each of length at most 20. The standard instance excludes a word contained inside another; the implementation also removes duplicates and contained words safely before solving. At most 12 independent words makes a subset-and-last-word dynamic program feasible, whereas trying all orderings becomes expensive. If the collection is empty, the function returns the empty string as a useful extension.

## Brute force

After removing redundant contained words, enumerate all permutations. For each ordering, append each word using its longest suffix-prefix overlap with the previous one, and keep the shortest result. There are n! orders; a direct overlap scan takes O(L²) per pair with ordinary string slices, for O(n! · n L²) time and O(nL) working space apart from permutation generation. A different independent oracle can enumerate short candidate strings by length and test substring membership, avoiding dependence on the ordering argument.

## The insight

First deduplicate and remove any word contained in another. This preserves the set of valid superstrings. For remaining words compute `overlap[i][j]`, the largest number of trailing characters of word i equal to leading characters of word j. Appending j after i then costs `len(j) - overlap[i][j]` new characters. The state `dp[mask][last]` is the maximum total saved overlap of an ordering of exactly the words in the mask ending in `last`. Extend it with an unused word and add the corresponding pair overlap; save a predecessor on improvement.

Why do orderings suffice? In any superstring, select an occurrence of each remaining word and sort them by starting position. Since no remaining word is contained in another, their ending positions also strictly increase. Consecutive occurrences overlap by a suffix-prefix match, or have a gap. Replace each gap by zero characters and replace each actual overlap with the largest possible overlap for that pair. Gluing in this order produces a superstring no longer than the original. Thus at least one ordering reaches the optimum. Conversely every glued ordering is a valid superstring, because appending preserves the previous word and creates the next one. Maximizing savings over all orderings therefore minimizes the resulting length.

For each state the previous word and mask summarize everything needed to price a next append. Every ordering has one predecessor obtained by removing its last word, so the recurrence considers all orders. Setting a bit increases the mask; processing masks in increasing order makes each predecessor available. Parent pointers reconstruct a word order, which is then glued using the precomputed overlaps. Ties may return any optimum.

## Optimal solution, traced

For `['ab', 'bc', 'ca']`, each neighboring pair in the cycle has overlap one:

```steps
Singletons
Each one-word state has total overlap 0.
---
Extend
The order ab -> bc saves one character and produces abc. Extending it with ca saves one more character.
---
Reconstruct
The order ab -> bc -> ca glues to abca with total overlap 2 and length 2 + 2 + 2 - 2 = 4.
```

No three-character string can contain all three distinct length-two words: it has only two length-two windows. Thus this result is shortest, although another ordering may give another optimum.

## Code

```python
def shortest_superstring(words):
    unique = list(dict.fromkeys(words))
    words = [word for word in unique
             if not any(word != other and word in other for other in unique)]
    n = len(words)
    if n == 0:
        return ""
    overlap = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for k in range(min(len(words[i]), len(words[j])), 0, -1):
                if words[i][-k:] == words[j][:k]:
                    overlap[i][j] = k
                    break
    dp = [[-1] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    for i in range(n):
        dp[1 << i][i] = 0
    for mask in range(1 << n):
        for last in range(n):
            if dp[mask][last] < 0:
                continue
            for nxt in range(n):
                if mask & (1 << nxt):
                    continue
                new_mask = mask | (1 << nxt)
                candidate = dp[mask][last] + overlap[last][nxt]
                if candidate > dp[new_mask][nxt]:
                    dp[new_mask][nxt] = candidate
                    parent[new_mask][nxt] = last
    mask = (1 << n) - 1
    last = max(range(n), key=lambda i: dp[mask][i])
    order = []
    while last != -1:
        order.append(last)
        previous = parent[mask][last]
        mask ^= 1 << last
        last = previous
    order.reverse()
    result = words[order[0]]
    for i, j in zip(order, order[1:]):
        result += words[j][overlap[i][j]:]
    return result
```

## Complexity

Let n be the number of input words and L their maximum length; filtering can only reduce n. The naive substring filtering and overlap comparisons take O(n² L²) time in the worst case with ordinary string matching and slicing. The subset transitions take O(n² 2^n) time, and reconstructing the result takes at most O(n² L) time with repeated immutable-string concatenation. Space is O(n 2^n + n² + nL), including tables, overlaps, retained words and output. These bounds reflect this particular code rather than assuming a linear-time string-matching primitive.

## Mistakes and edge cases

A word already inside another should not be forced into the order as a separate endpoint; remove it first. Handle duplicates before that removal so identical words do not eliminate each other. An overlap is a suffix of the previous word and a prefix of the next, not an arbitrary shared substring. Use `-1` for unreachable states, because zero overlap is a valid reachable score. A single word returns itself, and an empty collection returns an empty string. Multiple shortest answers are normal; test length and containment rather than one fixed spelling.

## Variations

- Return the minimum length only, dropping predecessor storage and reconstruction.
- Attach directional costs to transitions and solve a different subset-ordering problem using the same state structure.

=== card | 2376

## The problem

Count positive integers no greater than a given positive bound whose decimal representations have no repeated digit. For bound 20, all positive integers except 11 qualify, so the answer is 19. Zero is not included. A repeated zero matters after a number has started: 100 is invalid, whereas the padding zeros before a shorter number are not part of its representation.

## Constraints and what they imply

The bound is between 1 and 2,000,000,000, so it has at most ten decimal digits. A ten-bit mask can record which digits have occurred. A separate started flag distinguishes the number's real first digit from leading padding. The equality flag restricts a prefix that still matches the bound. There are only a fixed number of masks per position, even though the number of candidate integers can be huge.

## Brute force

Inspect every integer from 1 through the bound, convert it to decimal, and compare the number of distinct characters to its length. This takes O(bound · L) time for L decimal positions and O(L) temporary space. It is a useful independent oracle for small bounds, but scanning billions of candidates is too costly.

## The insight

Represent each integer with exactly L positions by padding on the left with zeros. Keep counts indexed by `(mask, tight, started)` after each position. The mask contains only digits of the actual representation. While `started` is false, choosing zero leaves the mask empty and still represents padding. Choosing a nonzero digit starts the number and sets that digit's bit. Once started, any digit including zero is legal only if its bit is absent, after which that bit is set.

If tight is true, the next digit cannot exceed the corresponding bound digit; otherwise any decimal digit can be selected. Tight remains true exactly when the old prefix was tight and the new digit equals the bound digit. At the end sum counts whose started flag is true, excluding the unique all-padding representation of zero.

Every number in the range has one padded representation, and every transition corresponds to one next digit. Inductively each state count is exactly the number of legal prefixes with its mask and flags. Rejecting a used bit forbids precisely the repeated-digit prefixes; leading zeros do not reserve the zero bit until the number actually begins. Consequently the final sum counts every valid positive integer exactly once. Use a fresh mapping for each digit so newly created states cannot be consumed again in the same position.

## Optimal solution, traced

For bound 20, consider its two positions:

```steps
First position
Choosing 0 leaves an unstarted loose prefix; choosing 1 creates a loose prefix with mask {1}; choosing 2 creates a tight prefix with mask {2}.
---
Second position
The unstarted branch yields the nine one-digit positives. The 1 branch yields ten choices except another 1, adding nine two-digit values.
---
Bound branch
The tight 2 branch permits only digit 0, producing 20. The all-padding zero is excluded, so 9 + 9 + 1 = 19.
```

The 0 chosen after the leading 2 is a real digit and sets its bit. By contrast, the first-position 0 on the shorter-number branch does not.

## Code

```python
def count_distinct_digit_numbers(bound):
    if bound <= 0:
        return 0
    states = {(0, True, False): 1}
    for char in str(bound):
        limit = int(char)
        following = {}
        for (mask, tight, started), count in states.items():
            upper = limit if tight else 9
            for digit in range(upper + 1):
                new_tight = tight and digit == limit
                if not started and digit == 0:
                    key = (mask, new_tight, False)
                else:
                    bit = 1 << digit
                    if mask & bit:
                        continue
                    key = (mask | bit, new_tight, True)
                following[key] = following.get(key, 0) + count
        states = following
    return sum(count for (_, _, started), count in states.items() if started)
```

## Complexity

At each of L positions there are at most 2^10 masks and four flag combinations, each trying at most ten digits. Time is O(L · 2^10 · 10), and the two rolling mappings use O(2^10) auxiliary space, apart from the O(L) string conversion. The official bound keeps counts small enough for ordinary integer operations; no modulus is required.

## Mistakes and edge cases

Do not mark leading padding zeros as used digits: doing so would incorrectly reject numbers such as 10. Conversely, after starting, zero is a normal digit and a second zero is forbidden. Do not count the all-padding state. A loose state cannot become tight again. A one-digit bound counts every positive value through that bound; a nonpositive bound returns zero in this extended interface. Repeated digits in the bound do not themselves invalidate smaller candidates.

## Variations

- Count valid integers in a range by subtracting prefix counts, including the lower endpoint carefully.
- Add a remainder state to require the number itself to be divisible by a chosen modulus.
