=== card | 104

## The problem

Return the maximum number of nodes on a path from the root to a leaf of a binary tree. The empty tree has depth zero. For example, a root with a single child has depth two, not one.

## Constraints and what they imply

There are at most 10,000 nodes, with values from -100 to 100. Values do not affect depth. A tree can be a long chain, so a recursive solution may exceed Python's recursion limit; use an explicit stack instead.

## Brute force

For each leaf, search from the root for that leaf and count the nodes on its path. Keep the largest count. Repeating the search for many leaves can take O(n²) time. Searching from every leaf separately also obscures that many paths share the same prefix.

## The insight

Carry the depth already reached with each node. A child is exactly one level deeper than its parent. Each node therefore needs to be visited only once, and the maximum depth seen anywhere is the leaf depth we want. A non-leaf cannot have greater depth than all its descendants.

## Optimal solution, traced

For root 8 with left child 3 and 3's right child 5:

```steps
Start at the root
stack = [(8, 1)], answer = 0
---
Process the first two nodes
8 then 3 give depths 1 and 2; push (5, 3)
---
Finish at the leaf
5 has depth 3; answer = 3
```

Push existing children with their parent's depth plus one. The order of left and right visits does not matter because we only take a maximum.

## Code

```python
def max_depth(root):
    if root is None:
        return 0
    stack = [(root, 1)]
    best = 0
    while stack:
        node, depth = stack.pop()
        best = max(best, depth)
        if node.left is not None:
            stack.append((node.left, depth + 1))
        if node.right is not None:
            stack.append((node.right, depth + 1))
    return best
```

## Complexity

Each node is pushed and popped once, so time is O(n). The depth-first stack contains at most one deferred sibling per ancestor, giving O(h) auxiliary space for height h. The input tree is not modified.

## Mistakes and edge cases

Count nodes rather than edges and return zero, not one, for an empty tree. A lone root has depth one. Updating only at leaves is also correct, but then make sure a node with just one child is not mistaken for a leaf.

## Variations

- Return a deepest root-to-leaf path by retaining parent links.
- Find minimum depth, treating a missing child differently from a leaf.

=== card | 110

## The problem

Determine whether every node in a binary tree has left and right subtree heights differing by at most one. Height counts nodes on the longest downward path, and an empty subtree has height zero. An empty tree is balanced.

## Constraints and what they imply

There are at most 5,000 nodes, with values between -10,000 and 10,000. Values are irrelevant. A chain can be much deeper than Python's recursion limit, so an explicit postorder traversal avoids a stack overflow.

## Brute force

At every node, separately compute the heights of its two subtrees and compare them, while checking the same condition recursively for its children. The repeated height calculations revisit descendants. On a chain they sum to O(n²) work, even though a subtree's height never changes.

## The insight

Compute each subtree height once after both children are done. At the same moment check the node's height difference. If any difference exceeds one, return false immediately; otherwise record one plus the larger child height. A missing child contributes zero. The explicit two-phase stack schedules children before their parent.

## Optimal solution, traced

Use the chain 1 -> 2 -> 3, with each arrow a left child:

```steps
Schedule postorder
Visit 1, 2, 3 before resolving them in reverse order.
---
Resolve the bottom
height(3) = 1; height(2) = 2 since its child heights are 1 and 0.
---
Resolve the root
child heights at 1 are 2 and 0, so return False.
```

Every stored height belongs to a fully processed subtree, so the local balance test is valid.

## Code

```python
def is_balanced(root):
    heights = {None: 0}
    stack = [(root, False)]
    while stack:
        node, done = stack.pop()
        if node is None:
            continue
        if not done:
            stack.append((node, True))
            stack.append((node.right, False))
            stack.append((node.left, False))
        else:
            left = heights[node.left]
            right = heights[node.right]
            if abs(left - right) > 1:
                return False
            heights[node] = 1 + max(left, right)
    return True
```

## Complexity

Time is O(n), because each node is scheduled and resolved once. The height table costs O(n), and the explicit traversal stack costs O(h), so total auxiliary space is O(n). Here h is tree height. Node objects must be hashable by identity.

## Mistakes and edge cases

Checking only the root is insufficient: an unbalanced descendant can have a balanced-looking root. An empty tree and a single node are balanced. Do not confuse a missing child of height zero with an absent balance check.

## Variations

- Return the first unbalanced node rather than a Boolean.
- Generalize the permitted height difference from one to a parameter.

=== card | 543

## The problem

Return the diameter of a binary tree: the largest number of edges on a simple path between any two nodes. The path need not include the root. A single node has diameter zero.

## Constraints and what they imply

The tree contains 1 to 10,000 nodes, with values from -100 to 100. Shape, not value, determines the answer. Deep chains can exceed Python's recursion limit, so the implementation performs postorder with an explicit stack.

## Brute force

For every pair of nodes, find the unique path between them and count its edges. There are O(n²) pairs and a naive path search can take O(n) per pair, for O(n³) time. Even recomputing heights at every possible turning point can take O(n²).

## The insight

Every path has a unique highest node. The longest path with that node as its highest point joins its deepest left descendant to its deepest right descendant. If child heights count nodes, their sum is exactly the number of edges in that path. The parent only needs the larger height, not both arms.

## Optimal solution, traced

For root A with left child B, B's left child D, and right child C:

```steps
Resolve the leaves
height(D) = height(C) = 1; each has candidate diameter 0.
---
Resolve B
child heights 1 and 0 give candidate 1 and height(B) = 2.
---
Resolve A
child heights 2 and 1 give candidate 3, the path D-B-A-C.
```

Take the maximum candidate over all nodes, including internal nodes below the root.

## Code

```python
def diameter(root):
    heights = {None: 0}
    stack = [(root, False)]
    best = 0
    while stack:
        node, done = stack.pop()
        if node is None:
            continue
        if not done:
            stack.append((node, True))
            stack.append((node.right, False))
            stack.append((node.left, False))
        else:
            left = heights[node.left]
            right = heights[node.right]
            best = max(best, left + right)
            heights[node] = 1 + max(left, right)
    return best
```

## Complexity

Each node is visited twice, yielding O(n) time. The stored heights take O(n) auxiliary space; the traversal stack is O(h), where h is height. The implementation uses node identity as a dictionary key.

## Mistakes and edge cases

Do not add one to the candidate: that would count nodes rather than edges. A chain's diameter is its node count minus one. The best path can lie entirely inside a child subtree, so a root-only calculation is wrong.

## Variations

- Return the endpoints as well as the diameter.
- Find the weighted diameter when each edge has a nonnegative length.

=== card | 94

## The problem

Return a binary tree's node values in inorder: all values from the left subtree, then the node, then all values from the right subtree. Return an empty list for an empty tree. The follow-up asks for an iterative traversal.

## Constraints and what they imply

The tree has 0 to 100 nodes and values between -100 and 100. Values can repeat: their occurrences still belong in the output. Avoid recursion to demonstrate how the call stack can be represented directly.

## Brute force

One direct approach is recursive traversal, building a fresh list at every node by concatenating its left result, its value, and its right result. It gives the correct order, but repeated copying can cost O(n²) on a chain. A shared output list avoids that copying.

## The insight

The recursion must remember ancestors whose left subtrees are being explored but whose own values have not yet been emitted. Store precisely those nodes on a stack. Descend left until there is no more left child, emit the most recent waiting node, and then explore its right subtree.

## Optimal solution, traced

Let 1 have right child 2, and let 2 have left child 3.

```steps
Descend from 1
stack = [1]; pop 1 and emit it; move to 2.
---
Descend through 2's left child
stack = [2, 3]; pop 3 and emit it.
---
Finish
pop and emit 2; output = [1, 3, 2].
```

Each time a node is popped its entire left subtree has already been processed, while its right subtree has not yet been visited.

## Code

```python
def inorder(root):
    result = []
    stack = []
    node = root
    while node is not None or stack:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        result.append(node.val)
        node = node.right
    return result
```

## Complexity

Each node is pushed and popped once: O(n) time. The explicit stack uses O(h) auxiliary space for tree height h, excluding the O(n) output list.

## Mistakes and edge cases

The outer loop must continue while either the current node or stack is nonempty; a null current node can still leave waiting ancestors. Emit after descending left, not when pushing. Equal values are separate visits.

## Variations

- Produce preorder or postorder by changing when a node is emitted.
- Yield values lazily instead of collecting the entire list.

=== card | 102

## The problem

Return the values of a binary tree grouped by depth, starting with the root's level and proceeding downward. Within each level, list nodes from left to right. Return an empty list for an empty tree. For a root 1 with children 2 and 3, return [[1], [2, 3]].

## Constraints and what they imply

The input contains 0 to 2,000 nodes, and values are between -1,000 and 1,000. Values may repeat, so preserve every occurrence. The tree may be skewed or wide. A queue gives a direct representation of the current level and avoids Python's recursion-depth limit.

## Brute force

First compute the height. Then, for each level number, start at the root and recursively search for nodes at that depth, collecting them in left-to-right order. Nodes near the top are repeatedly revisited; for a chain the total work is O(n²). The method also requires an extra full traversal to obtain the height.

## The insight

Breadth-first search visits nodes in increasing depth. Before processing a level, the queue contains exactly its nodes in left-to-right order. Save the queue's current length, remove exactly that many nodes, and append their existing children in left-then-right order. The children form the next level behind the remaining current nodes.

## Optimal solution, traced

For root 1 with left child 2 and right child 3, where 2 has right child 4:

```steps
Start the first level
queue = [1], width = 1; output [1] and enqueue 2, 3.
---
Process the second level
queue = [2, 3], width = 2; output [2, 3] and enqueue 4.
---
Process the last level
queue = [4], width = 1; output [4]; queue is empty.
```

The saved width is essential: the queue can grow during the loop, but newly added children must wait for the next group. Left-to-right ordering follows from processing parents in that order and adding each left child before its right child.

The queue thus acts as a boundary between work at consecutive depths. Missing children are simply skipped; no placeholder is necessary because the result groups existing nodes rather than reconstructing the shape.

## Code

```python
from collections import deque

def level_order(root):
    if root is None:
        return []
    queue = deque([root])
    levels = []
    while queue:
        level = []
        width = len(queue)
        for _ in range(width):
            node = queue.popleft()
            level.append(node.val)
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)
        levels.append(level)
    return levels
```

## Complexity

Every node enters and leaves the queue once, so time is O(n). Let w be the maximum level width. The queue holds at most parts of two adjacent levels, so auxiliary space is O(w), excluding the O(n) returned groups.

## Mistakes and edge cases

Do not iterate until the queue becomes empty inside a single level: that mixes depths. Do not use a normal list's front deletion, which shifts remaining entries and can make traversal quadratic. The empty root must not be put into the queue as a node.

## Variations

- Reverse alternate level lists for zigzag traversal.
- Compute the average or maximum value separately for each level.

=== card | 1448

## The problem

Count nodes that are at least as large as every value on their root-to-node path. Such a node is called good. The root is always good because the path contains only the root. Equality counts: a node tied with the previous maximum is good.

## Constraints and what they imply

There are 1 to 100,000 nodes; values range from -10,000 to 10,000. Negative values and duplicate values are possible. A chain may contain all 100,000 nodes, so use an explicit stack rather than Python recursion.

## Brute force

For each node independently, recover its root-to-node path and scan the values to decide whether that node is maximal on the path. This repeats work on shared prefixes. A naive root search for every node can take O(n²) total time and a path can use O(h) temporary space.

## The insight

The entire ancestor path can be summarized by its maximum value. Pass that maximum down with the node. Compare the node's value with the incoming maximum to decide whether it contributes one, then pass the larger of the two values to both children. Each stack entry has its own path state, so one branch cannot contaminate the other.

## Optimal solution, traced

Take root 3, left child 1 with child 3, and right child 4.

```steps
Visit the root
incoming maximum = 3; 3 is good, count = 1.
---
Visit the left path
1 < 3, so it is not good; its child 3 equals the maximum and is good.
---
Visit the right child
4 >= 3, so it is good; final count = 3.
```

The initial maximum can be the root's own value, which makes the root qualify without relying on a particular numeric lower bound. Inductively, each child's incoming maximum includes exactly its ancestors.

This invariant also explains why the test happens before updating the maximum: it compares the current value against the path above it. Updating first would give the same result with a non-strict comparison, but obscures which values have already been visited.

## Code

```python
def good_nodes(root):
    if root is None:
        return 0
    stack = [(root, root.val)]
    count = 0
    while stack:
        node, best = stack.pop()
        if node.val >= best:
            count += 1
        best = max(best, node.val)
        if node.left is not None:
            stack.append((node.left, best))
        if node.right is not None:
            stack.append((node.right, best))
    return count
```

## Complexity

Each node is processed once, giving O(n) time. A depth-first stack holds at most one deferred sibling per ancestor, so auxiliary space is O(h), with h the height. The input tree is not modified.

## Mistakes and edge cases

Use greater-than-or-equal, not strict greater-than. Starting with zero would incorrectly reject negative roots; using the root value handles negative values naturally. Do not keep one global running maximum across branches, since sibling paths do not include one another.

## Variations

- Return the good node objects rather than only their count.
- Count nodes smaller than or equal to every ancestor by tracking a path minimum.

=== card | 105

## The problem

Reconstruct a binary tree from its preorder and inorder lists. Preorder visits root, left subtree, then right subtree. Inorder visits left subtree, root, then right subtree. Return the root of any tree with those traversals; under the stated uniqueness assumptions its shape is determined.

## Constraints and what they imply

The lists have the same length, between 1 and 3,000, and contain the same distinct integer values from -3,000 to 3,000. They are valid traversals of a binary tree. Distinctness makes each inorder position unambiguous. A skewed input can exceed Python's recursion limit, motivating iterative reconstruction.

## Brute force

Take the first preorder value as the root, linearly search for it in inorder, split both lists around the resulting left-subtree size, and repeat recursively. On a chain, repeated searches and list slices cost O(n²) time and may use O(n²) total live slice space. The splitting idea is correct, but repeatedly copying and scanning is avoidable.

## The insight

Preorder supplies nodes in the order they are created. A stack tracks constructed nodes whose inorder visit is still pending. If its top is not the next inorder value, the next preorder node is its left child. Otherwise, pop all ancestors matching the next inorder values: the next preorder node becomes the right child of the last popped node.

The inorder index advances only on a pop. This simulates returning from completed left subtrees without recursion or a value-to-index lookup. Distinct values make the top comparison identify exactly the node whose inorder turn has arrived.

## Optimal solution, traced

For preorder [3, 9, 20, 15, 7] and inorder [9, 3, 15, 20, 7]:

```steps
Create 3, then 9
3 does not match next inorder 9; attach 9 as 3.left.
---
Create 20
pop 9 then 3 as they match inorder; attach 20 as 3.right.
---
Create 15 and 7
attach 15 as 20.left; pop 15 then 20; attach 7 as 20.right.
```

The stack's remaining nodes are precisely the open ancestors. Once a matching node is popped, its left side and its own inorder position are complete. The last node popped is the ancestor whose right subtree the next preorder value starts.

## Code

```python
class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(preorder, inorder):
    if not preorder:
        return None
    root = TreeNode(preorder[0])
    stack = [root]
    i = 0
    for value in preorder[1:]:
        child = TreeNode(value)
        if stack[-1].val != inorder[i]:
            stack[-1].left = child
        else:
            while stack and stack[-1].val == inorder[i]:
                parent = stack.pop()
                i += 1
            parent.right = child
        stack.append(child)
    return root
```

## Complexity

Each node is pushed and popped at most once, so time is O(n). The stack and the preorder slice use O(n) auxiliary space in the worst case, excluding the O(n) output tree. The inorder index only moves forward.

## Mistakes and edge cases

Attach to the last popped node, not necessarily the first: several ancestors may finish together. The algorithm assumes valid, distinct traversals and does not validate malformed inputs. A single node, an all-left chain, and an all-right chain should all reconstruct correctly.

## Variations

- Rebuild from inorder and postorder, processing roots in reverse.
- Determine whether arbitrary supplied traversal sequences are consistent before building.

=== card | 124

## The problem

Given a nonempty binary tree with integer node values, return the largest sum obtainable along any nonempty simple path. A path is a sequence of nodes joined by parent-child edges; no node may appear twice. It may start and end anywhere and does not have to include the root or a leaf. For example, with root -10, children 9 and 20, and 20's children 15 and 7, the answer is 42 from 15 through 20 to 7.

## Constraints and what they imply

There are 1 to 30,000 nodes, each valued from -1,000 to 1,000. Negative values are allowed, including an entirely negative tree. The answer must represent at least one node, so zero is not a valid default for an all-negative input. A tree can be a chain of 30,000 nodes, far deeper than Python's default recursive call limit. An explicit postorder traversal avoids depending on that limit.

## Brute force

Enumerate every unordered pair of nodes as potential endpoints, including a node paired with itself. For each pair, find the unique connecting path, add its node values, and retain the largest sum. A fresh path search can take O(n), producing O(n³) time over O(n²) pairs. Even if paths are calculated more efficiently, considering every pair is unnecessary because many pairs share long path segments.

The path must be simple. In particular, adding three child or parent directions at a branching node would produce a branched structure, not a path. This observation is the reason the information returned upward must differ from the best complete path seen so far.

## The insight

Choose the unique highest node on a path, meaning the node closest to the root among its members. The path can use at most one descending arm in each child subtree. At a node, a child's best downward gain either helps, if positive, or can be omitted entirely, if negative. Therefore the best path turning at the node is its value plus the positive part of each child's gain.

To extend a path from this node to its parent, however, only one child arm can be used: otherwise the parent edge would create a branch. Return the node value plus the larger of zero and the two child gains. Separately update a global best with the two-arm candidate. Processing nodes in postorder ensures both child gains are available before their parent.

Every valid path has a highest node and is bounded by the candidate calculated there. Conversely, each candidate corresponds to an actual simple path. Thus the maximum candidate is exactly the desired answer. Initializing that maximum to negative infinity preserves the best single-node answer when every value is negative.

## Optimal solution, traced

Use the tree with root -10, left child 9, right child 20, and children 15 and 7 under 20:

```steps
Resolve the leaves
gains are 9, 15, and 7; best candidate so far is 15.
---
Resolve node 20
turning candidate = 20 + 15 + 7 = 42; upward gain = 20 + 15 = 35.
---
Resolve node -10
turning candidate = -10 + 9 + 35 = 34; global best remains 42.
```

The downward gain from 20 cannot include both 15 and 7 when connected to -10, although both are legal in the complete path centered at 20. For a single node -3, the candidate and answer are -3; the empty path with sum zero is never offered as the global answer.

## Code

```python
def max_path_sum(root):
    gains = {None: 0}
    stack = [(root, False)]
    best = float("-inf")
    while stack:
        node, done = stack.pop()
        if node is None:
            continue
        if not done:
            stack.append((node, True))
            stack.append((node.right, False))
            stack.append((node.left, False))
        else:
            left = max(0, gains[node.left])
            right = max(0, gains[node.right])
            best = max(best, node.val + left + right)
            gains[node] = node.val + max(left, right)
    return best
```

## Complexity

Each node is scheduled and resolved once, so time is O(n). The gain table requires O(n) auxiliary space and the traversal stack O(h), where h is height. The total is O(n). The implementation keys the table by node identity and assumes a nonempty tree as specified; it does not mutate the tree.

## Mistakes and edge cases

Do not initialize the global answer to zero, because that silently chooses an illegal empty path for an all-negative tree. Do not return both child gains to a parent: that makes a three-way branch. Do not require the path to include the root, a leaf, or two distinct endpoints. A negative node may still be necessary between two sufficiently valuable arms, so do not simply delete all negative nodes.

The code clips each child gain, not the current node's value. This distinction allows a negative current node to connect profitable descendants while ensuring an unprofitable entire child arm is omitted. For a skewed tree, the result may start or end at any interior node.

## Variations

- Return the actual maximizing path by recording each selected child and the best turning node.
- Find the maximum root-to-leaf sum, where a missing child cannot be chosen as a completed path.
- Replace node values with edge weights and define whether a zero-edge path is permitted.

=== card | 437

## The problem

Count nonempty downward paths whose node values sum to a target. A path may begin and end at any nodes, but every step must go from a parent to one of its children. The path need not start at the root or end at a leaf. Different starting or ending nodes define different paths, even when their values match.

## Constraints and what they imply

There are 0 to 1,000 nodes, node values range from -1,000,000,000 to 1,000,000,000, and the target ranges from -1,000 to 1,000. Negative values and zero mean that exceeding the target does not justify pruning. Python integers avoid overflow in accumulated sums, and an explicit stack handles a chain near the recursion limit.

## Brute force

Start a downward traversal at every node. Accumulate the sum as the traversal goes down, counting each endpoint where it equals the target. There are n possible starts, each potentially reaching O(n) descendants, for O(n²) time on a chain and O(h) traversal space. It is important to continue after finding a match, since later negative or zero values can yield another matching endpoint.

## The insight

Let a prefix sum be the sum from the root through a node, with a virtual zero prefix before the root. A downward path ending at the current node has sum target exactly when an earlier prefix on its current root path equals current sum minus target. A frequency map counts all such earlier prefixes, including duplicates.

The map must contain only prefixes of ancestors, not prefixes from previously visited sibling branches. Increment the current sum before visiting children and remove it after both children are complete. An exit frame implements this backtracking even without recursion. Seed the map with one zero so paths starting at the root are counted.

## Optimal solution, traced

For root 1 with children -1 and 1, target 1:

```steps
Enter root 1
sum = 1; frequency[0] = 1, so count = 1; record prefix 1.
---
Enter left child -1
sum = 0; frequency[-1] = 0, so count stays 1; remove prefix 0 on exit.
---
Enter right child 1
sum = 2; frequency[1] = 1, so count = 2; then remove its prefix.
```

The second counted path is the right child by itself. Removing the left prefix before visiting the right branch prevents invalid cross-branch paths. Looking up before incrementing also prevents an empty path when the target is zero.

## Code

```python
from collections import defaultdict

def path_sum_count(root, target):
    frequency = defaultdict(int)
    frequency[0] = 1
    stack = [(root, 0, False)]
    answer = 0
    while stack:
        node, prefix, leaving = stack.pop()
        if node is None:
            continue
        if leaving:
            frequency[prefix] -= 1
            if frequency[prefix] == 0:
                del frequency[prefix]
            continue
        current = prefix + node.val
        answer += frequency.get(current - target, 0)
        frequency[current] += 1
        stack.append((node, current, True))
        stack.append((node.right, current, False))
        stack.append((node.left, current, False))
    return answer
```

## Complexity

Each node is entered and exited once, giving O(n) expected time with hash-map operations. The active prefix map and depth-first stack use O(h) auxiliary space, where h is height; in a chain this is O(n). Zero-count entries are deleted so completed branches do not accumulate in the map.

## Mistakes and edge cases

Store frequencies, not just a set, since equal prefixes can occur at different depths and correspond to distinct paths. Remove the current prefix on exit, not immediately after pushing children. Negative values make early stopping invalid. An empty tree returns zero; a zero-valued node with target zero contributes one nonempty path.

## Variations

- Count paths with a sum in a range using a data structure over ancestor prefix sums.
- Count only root-to-leaf target-sum paths by checking leaf status.

=== card | 236

## The problem

Given a binary tree and two distinct node references p and q, return their lowest common ancestor: the deepest node having both targets in its subtree. A node is considered a descendant of itself, so if p is an ancestor of q, the answer is p. The tree is not necessarily a search tree.

## Constraints and what they imply

There are 2 to 100,000 nodes, all node values are distinct and in the range -1,000,000,000 to 1,000,000,000. Both targets are distinct and are guaranteed to be present. The height may be 100,000, so an iterative approach is safer than recursive Python. Work with node identity rather than relying on values.

## Brute force

For each candidate node, search its subtree separately for p and q, and choose the deepest candidate containing both. Each subtree search can take O(n); across n candidates this can take O(n²) time. Depth information is also necessary to distinguish a lowest common ancestor from a higher common ancestor.

## The insight

Traverse from the root once to record each node's parent. Then walk from p upward to the root, placing its ancestors, including p itself, in a set. Walk from q upward until reaching the first member of that set. That first shared node is the deepest common ancestor: q encounters its ancestors in order from deepest to shallowest, and membership means the node also lies on p's ancestor chain.

The parent map converts upward movement, which child-only tree nodes do not provide, into constant-time steps. Stop the initial search as soon as both target nodes are discovered, because their entire ancestor chains are already recorded.

## Optimal solution, traced

Let root A have left child B and right child C; B has children D and E. Query D and E.

```steps
Record parents
parent(B) = A, parent(C) = A, parent(D) = B, parent(E) = B.
---
Walk from D
ancestor set = {D, B, A}.
---
Walk from E
E is not in the set; its parent B is, so return B.
```

If the query instead uses B and D, B is already in its own ancestor set, and D's upward walk reaches B. No special ancestor case is needed.

## Code

```python
def lowest_common_ancestor(root, p, q):
    parent = {root: None}
    stack = [root]
    while p not in parent or q not in parent:
        node = stack.pop()
        for child in (node.left, node.right):
            if child is not None:
                parent[child] = node
                stack.append(child)
    ancestors = set()
    while p is not None:
        ancestors.add(p)
        p = parent[p]
    while q not in ancestors:
        q = parent[q]
    return q
```

## Complexity

Building parent links visits at most n nodes, and the two ancestor walks cost O(h), so time is O(n). The parent map and traversal stack take O(n) auxiliary space in the worst case; the ancestor set uses O(h). Nodes must be hashable by identity. The algorithm relies on both targets being present.

## Mistakes and edge cases

Do not assume the tree is ordered by value. Compare node objects, not just their values, and include each target in its own ancestor chain. If target presence is not guaranteed, detect an exhausted search and define a separate missing-target result rather than popping an empty stack.

## Variations

- Answer many queries after preprocessing ancestors for binary lifting.
- Handle missing targets explicitly and report when no valid answer exists.

=== card | 297

## The problem

Design a serializer and deserializer for binary trees. Serialization converts a tree to a string; deserialization reconstructs a tree with exactly the same node values and left/right shape. There is no prescribed wire format, but the two operations must agree. For example, a node with only a left child must not decode as a node with only a right child. An empty tree must also round-trip.

## Constraints and what they imply

The tree contains 0 to 10,000 nodes, with integer values between -1,000 and 1,000. Values can repeat, so values alone do not identify positions. Both negative and multi-digit values must be encoded unambiguously. A 10,000-node chain can exceed Python's recursion limit, so both directions below use explicit stacks. The judge may supply its own node class; the self-contained code includes a compatible class.

## Brute force

One possible approach is to write down the node values and separately record, for each node, the indices of its left and right children. Decoding allocates all nodes and then reconnects the indexed edges. It uses O(n) time and space and is valid, but needs an index assignment, a node table, and careful handling of missing child indices. Merely writing the values of one traversal without shape information is not a valid serialization: different shapes can have the same preorder.

Another conceptual approach is to try every possible tree shape until one matches a list of values, but the number of shapes grows rapidly and the representation still cannot distinguish multiple trees with the same traversal. Explicit null markers directly encode the missing information.

## The insight

In preorder, write a node's value and then serialize its left and right subtrees. For every absent child, write a dedicated marker, here `#`. A decoder reads a marker as an empty subtree and a value as a node followed by exactly two encoded subtrees. This grammar uniquely determines where each subtree ends.

The iterative decoder keeps a stack of nodes with unfilled child slots. A frame's flag says whether its left or right slot is next. Attach the next token to that slot; when a value creates a node, push a frame for the new node before processing its children. When a frame receives its right child, remove that frame because both of its slots are filled. A newly created right child still gets its own frame.

The serializer uses a stack in the reverse push order: push right before left so left is emitted first. It writes one token for every real node and every missing child. An n-node binary tree has n + 1 missing child slots, hence 2n + 1 tokens, including the single marker for an empty tree.

## Optimal solution, traced

Take root 1, no left child, and right child -2:

```steps
Serialize the root and its gaps
preorder tokens = [1, #, -2, #, #].
---
Decode the first two tokens
create root 1; attach None to its left slot; its right slot is next.
---
Decode the right subtree
attach -2 as 1.right, then fill both of -2's slots with None.
```

The first marker cannot be confused with the negative number because tokens are comma-separated and `#` is not an integer. A one-token string `#` represents an empty tree. Repeated values are safe because child slots, rather than values, determine placement. Inductively each consumed token fills exactly the next slot in preorder, so both shape and values are restored.

## Code

```python
class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Codec:
    def serialize(self, root):
        tokens = []
        stack = [root]
        while stack:
            node = stack.pop()
            if node is None:
                tokens.append("#")
            else:
                tokens.append(str(node.val))
                stack.append(node.right)
                stack.append(node.left)
        return ",".join(tokens)

    def deserialize(self, data):
        tokens = iter(data.split(","))
        first = next(tokens)
        if first == "#":
            return None
        root = TreeNode(int(first))
        stack = [(root, False)]
        for token in tokens:
            node, right_slot = stack.pop()
            child = None if token == "#" else TreeNode(int(token))
            if right_slot:
                node.right = child
            else:
                node.left = child
                stack.append((node, True))
            if child is not None:
                stack.append((child, False))
        return root
```

## Complexity

Both operations process 2n + 1 tokens, so they take O(n) time, treating bounded-size integer conversion as constant time. Serialization stores the output tokens in O(n) space and uses an O(h) traversal stack. Deserialization splits the string into O(n) token storage and uses an O(h) frame stack, excluding the O(n) reconstructed tree. Here h is the tree height. Space remains linear even for a chain.

## Mistakes and edge cases

Do not omit markers: `[1, 2]` alone cannot distinguish a left child from a right child. Push right before left when encoding with a LIFO stack. Do not lose the parent's pending right slot when descending into its left child. The code assumes its input was produced by this serializer; it is not a validator for truncated, extra, or malformed tokens. If untrusted input is required, validate slot counts, token syntax, and resource limits separately.

The empty tree serializes to `#`; a single node has two following markers. A negative sign belongs to a number token, not to the separator or the null marker. The returned tree is newly allocated, not aliased to the original.

## Variations

- Encode in level order with explicit gaps and trim redundant trailing null markers.
- Define a versioned format and reject malformed or oversized inputs before allocation.
- Encode an n-ary tree by recording each node's child count.

=== card | 863

## The problem

Given a binary tree, a target node in that tree, and a nonnegative integer k, return the values of all nodes exactly k edges from the target. A path may move up to a parent as well as down to a child. Return the values in any order. When k is zero, the target itself is the only answer.

## Constraints and what they imply

There are 1 to 500 nodes. Node values are distinct integers from 0 to 500; the target is guaranteed to be present, and k is between 0 and 1,000. Since k can exceed the tree's diameter, an empty answer is possible. Node identity is a convenient way to track visits independently of values.

## Brute force

For each node, find its unique path to the target by searching the tree or comparing root-to-node paths, then count the edges. Repeating a linear search for each candidate takes O(n²) time. This is correct even when the path goes through a common ancestor, but repeats much of the same search.

## The insight

View each tree edge as undirected. Child pointers provide downward neighbors; a single traversal constructs the missing parent pointer for every node. Then run breadth-first search from the target. Each BFS round crosses exactly one edge, and the queue after k rounds contains precisely the nodes at distance k.

Track visited node objects so the search does not immediately return to the node it came from. A tree has a unique simple path between any two nodes, and BFS first reaches each node along a shortest path. Stopping when the queue is empty handles distances greater than every possible path.

## Optimal solution, traced

Let A have children B and C, and B have child D. Start at B with k = 2.

```steps
Build parent links
parent(B) = A, parent(C) = A, parent(D) = B.
---
Expand distance zero
frontier [B] discovers D and A at distance one.
---
Expand distance one
D adds nothing new; A discovers C; frontier at distance two is [C].
```

The edge back to B is ignored because B was already visited. A different traversal order may change the output order, which the problem permits.

## Code

```python
from collections import deque

def distance_k(root, target, k):
    parent = {root: None}
    stack = [root]
    while stack:
        node = stack.pop()
        for child in (node.left, node.right):
            if child is not None:
                parent[child] = node
                stack.append(child)
    queue = deque([target])
    seen = {target}
    distance = 0
    while queue and distance < k:
        for _ in range(len(queue)):
            node = queue.popleft()
            for neighbor in (node.left, node.right, parent[node]):
                if neighbor is not None and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        distance += 1
    return [node.val for node in queue]
```

## Complexity

Parent construction and BFS each visit every node at most once, so time is O(n), including when k is much larger than the tree height. The parent map, visited set, and queue use O(n) auxiliary space. Node objects must be hashable by identity.

## Mistakes and edge cases

Do not restrict the search to the target's descendants: answers may be ancestors or lie in sibling subtrees. Mark nodes visited when enqueuing, not after repeatedly rediscovering them. For k zero, return the target value without expanding; for excessive k, return an empty list.

## Variations

- Return all nodes within distance k rather than exactly at distance k.
- Answer many target-distance queries after preprocessing an appropriate tree index.
