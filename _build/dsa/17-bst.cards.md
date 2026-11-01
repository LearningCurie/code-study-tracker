=== card | 700
time: 20 min

## The problem

Given the root of a binary search tree and a target key, return the node containing that key, together with the subtree rooted there. Return `None` if the key is absent. In this tree, every key in a node's left subtree is smaller than the node's key, and every key in its right subtree is larger.

For a root 4 with children 2 and 7, searching for 2 returns the node 2; searching for 5 returns `None`.

## Constraints and what they imply

Keys are distinct, and the input obeys the search-tree ordering. The tree need not be balanced, so its height `h` may be as large as its number of nodes. Returning a node means returning the existing subtree, not constructing a new tree.

## Brute force

Traverse every node until finding the key. A DFS takes O(n) time and O(h) stack space even when the ordering could discard most of the tree. The bottleneck is exploring branches that the ordering has already ruled out.

## The insight

At a node larger than the target, the target cannot lie in its right subtree. At a smaller node, it cannot lie in its left subtree. Follow the only possible child until finding the key or reaching an empty pointer.

## Optimal solution, traced

```steps
Search 5 at root 4
    5 > 4: go right to 7
---
At 7, 5 < 7: go left
    the left pointer is empty
---
No candidate subtree remains
    return {{None}}
```

The remaining pointer always roots the only subtree that can still contain the target.

## Code

```python
def search_bst(root, target):
    node = root
    while node is not None:
        if target == node.val:
            return node
        node = node.left if target < node.val else node.right
    return None
```

## Complexity

At most one node per level is examined: O(h) time and O(1) auxiliary space. This is O(log n) time for a balanced tree but O(n) for a chain.

## Mistakes and edge cases

- Return the matching node, not only its value.
- An empty tree or absent key returns `None`.
- Do not assume the tree is balanced.

## Variations

- Insert an absent key at the empty pointer reached by the search.
- Find the smallest key greater than or equal to the target, remembering candidates on the path.
- Count how many comparisons a search takes in balanced and skewed trees.

=== card | 938
time: 20 min

## The problem

Add the keys in a binary search tree that fall within an inclusive interval `[low, high]`. Keys outside the interval contribute nothing. For a tree with keys 3, 5 and 8, the interval `[4, 8]` has sum 13.

## Constraints and what they imply

Keys in the left subtree of a node are smaller than its key, and keys in the right subtree are larger. The endpoints are included. A tree can be skewed, so an iterative traversal avoids depending on Python's recursion limit.

## Brute force

Visit all `n` nodes and add a key whenever it lies between the bounds. This takes O(n) time and O(h) traversal space. It may inspect large subtrees whose keys are all too small or all too large.

## The insight

If a node is below `low`, its entire left subtree is also below `low`. If it is above `high`, its entire right subtree is above `high`. Only visit a child when that side can contain a key in the interval.

## Optimal solution, traced

```steps
At root 5 with interval [4, 8]
    add 5; both children could contain matches
---
At left child 3
    3 is below 4; skip its left subtree
---
At right child 8
    add 8; skip its right subtree
    total {{13}}
```

Every skipped subtree is excluded by a strict search-tree ordering bound; every potentially matching child remains on the stack.

## Code

```python
def range_sum_bst(root, low, high):
    total = 0
    stack = [root] if root is not None else []
    while stack:
        node = stack.pop()
        if low <= node.val <= high:
            total += node.val
        if node.left is not None and node.val > low:
            stack.append(node.left)
        if node.right is not None and node.val < high:
            stack.append(node.right)
    return total
```

## Complexity

If `k` keys match, the traversal visits those keys and boundary search paths: O(h + k) time, or O(n) in the worst case. The DFS stack uses O(h) auxiliary space. Skewed trees can therefore still require linear time and space.

## Mistakes and edge cases

- Use inclusive comparisons for the sum.
- A subtree may be skipped only because the input really is a search tree.
- An empty tree or interval containing no keys has sum zero.

## Variations

- Return the matching keys in sorted order using a pruned in-order walk.
- Answer many intervals using prefix sums over an in-order array.
- Maintain subtree sums in a dynamically updated tree.

=== card | 108
time: 20 min

## The problem

Build a height-balanced binary search tree from a sorted array of distinct integers. A height-balanced tree has child subtree heights differing by at most one at every node. The exact valid shape is not unique.

For `[-3, 0, 4]`, choosing 0 as the root, -3 as its left child and 4 as its right child produces a valid balanced tree.

## Constraints and what they imply

The values are already in strictly increasing order. Choosing the first value repeatedly would form a chain, so the root must divide the remaining input into comparably sized portions. Avoid copying array slices at each recursive call.

## Brute force

Insert the values into an ordinary binary search tree in their existing sorted order. This produces a skewed tree, not the required balanced tree, and takes O(n²) comparisons. Trying every possible tree shape and checking its balance would find a valid shape but has combinatorial cost.

## The insight

Use the middle element as the root and apply the same construction to each half. All elements in the left half are smaller and all elements in the right half are larger. Halving at each level keeps the subtree heights balanced.

## Optimal solution, traced

```steps
Array [-3, 0, 4]: select the middle key
    root {{0}}
---
Build each remaining half
    left [-3] -> -3    right [4] -> 4
---
Both child subtrees have height 1
    return the balanced tree
```

Each recursive call owns a half-open index range. Its two subranges are disjoint, differ in length by at most one, and together contain all remaining values.

## Code

```python
class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def sorted_array_to_bst(values):
    def build(start, end):
        if start == end:
            return None
        middle = (start + end) // 2
        return TreeNode(values[middle], build(start, middle), build(middle + 1, end))

    return build(0, len(values))
```

## Complexity

One node is created per value, so time and output space are O(n). Balanced recursion has O(log n) auxiliary stack space; no array slices are created.

## Mistakes and edge cases

- Use the same half-open range convention for both children.
- Return `None` for an empty range.
- Distinguish the required output nodes from auxiliary stack space.

## Variations

- Construct a balanced search tree from an in-order linked list.
- Return the lower middle rather than the upper middle when the range length is even.
- Verify that the in-order traversal equals the input and every subtree is balanced.

=== card | 235
time: 25 min

## The problem

Given two nodes in a binary search tree, return their lowest common ancestor: the deepest node that has both targets in its subtree. A node is considered an ancestor of itself. Both target nodes are present and keys are distinct.

If root 6 has children 2 and 8, the lowest common ancestor of 2 and 8 is 6. If one target is 2 and the other is a descendant of 2, the answer is 2 itself.

## Constraints and what they imply

The tree is ordered, the target keys are distinct, and both nodes occur in the tree. The height may be linear in the number of nodes, because a binary search tree is not necessarily balanced. Comparing the keys gives enough information to choose a direction without traversing both sides.

## Brute force

Find and store the root-to-target path for each node, then compare the paths until they diverge. In a search tree each path takes O(h) time and O(h) space. A more general binary-tree DFS can scan O(n) nodes. The extra path storage is unnecessary when ordering already identifies the split point.

## The insight

At the current node, if both target keys are smaller, their lowest common ancestor must be in the left subtree. If both are larger, it must be in the right subtree. Otherwise the targets split across the node or one equals it; this node is their lowest common ancestor.

## Optimal solution, traced

```steps
Search for the ancestor of 2 and 8, starting at 6
    2 < 6 < 8
---
The targets lie on opposite sides
    return {{6}}
```

When both targets fall on the same side, the discarded side cannot contain either one, so it cannot contain their lowest common ancestor. At the first split, the current node contains both targets, while neither of its children contains both. This proves it is the lowest such node.

## Code

```python
def bst_lowest_common_ancestor(root, p, q):
    low, high = sorted((p.val, q.val))
    node = root
    while node is not None:
        if high < node.val:
            node = node.left
        elif low > node.val:
            node = node.right
        else:
            return node
    raise ValueError("the targets must be present in the search tree")
```

## Complexity

Only one root-to-leaf path is followed, so time is O(h), with O(1) auxiliary space. That is O(log n) in a balanced tree and O(n) in a chain.

## Mistakes and edge cases

- Equality is a valid split: a target can be its own ancestor.
- Use both keys when choosing a direction, not just one.
- This reasoning requires search-tree ordering and the promised target membership.

## Variations

- Find the lowest common ancestor in an arbitrary binary tree without ordering.
- Return the distance between two nodes after locating their ancestor.
- For many static tree queries, preprocess binary-lifting ancestor tables.

=== card | 98
time: 25 min

## The problem

Decide whether a binary tree is a valid binary search tree. Every node's entire left subtree must contain strictly smaller keys, and its entire right subtree strictly larger keys. Equal keys are not permitted.

The tree with root 5, right child 7 and that child's left child 4 is invalid: 4 is locally smaller than 7, but it is in the right subtree of 5 and therefore must also be greater than 5.

## Constraints and what they imply

The input is an arbitrary binary tree, not necessarily a search tree. Checking only a node and its immediate children cannot detect violations against more distant ancestors. Values may be negative or outside a chosen fixed sentinel range. A skewed input can have height `n`.

## Brute force

At every node, traverse its complete left subtree and confirm every key is smaller, then traverse its complete right subtree and confirm every key is larger. Repeat for all nodes. A chain causes O(n²) total visits because the same descendants are checked for many ancestors. The repeated subtree scans are the bottleneck.

## The insight

Carry the interval allowed by all ancestors down the tree. A left child inherits the lower bound and gains its parent's key as an exclusive upper bound; a right child gains the parent's key as an exclusive lower bound. If a node fails either bound, the tree is invalid.

An alternative is to check that an in-order traversal is strictly increasing, but the explicit bounds make the ancestor constraint visible.

## Optimal solution, traced

```steps
Root 5 has no bounds
    valid; its right child must be > 5
---
Node 7 is in interval (5, infinity)
    valid; its left child must be in (5, 7)
---
Node 4 is not greater than 5
    return {{false}}
```

By induction, the interval on each stack entry contains exactly the restrictions imposed by its ancestors. If all nodes satisfy them, every node is correctly ordered with respect to every ancestor, which is the search-tree property.

## Code

```python
def is_valid_bst(root):
    stack = [(root, None, None)] if root is not None else []
    while stack:
        node, low, high = stack.pop()
        if low is not None and node.val <= low:
            return False
        if high is not None and node.val >= high:
            return False
        if node.right is not None:
            stack.append((node.right, node.val, high))
        if node.left is not None:
            stack.append((node.left, low, node.val))
    return True
```

## Complexity

Each node is pushed and popped at most once, so time is O(n). Depth-first traversal holds at most O(h) pending nodes for tree height `h`. The explicit stack avoids recursion-depth failures, but a chain can still use O(n) space in the worst-case height bound.

## Mistakes and edge cases

- Bounds are strict: duplicate keys make the tree invalid.
- Checking only parent-child relationships misses ancestor violations.
- `None` denotes an absent bound, so valid integers are not confused with arbitrary finite sentinels.

## Variations

- Validate by checking that in-order keys are strictly increasing.
- If duplicates are allowed on exactly one side, change the relevant bound to inclusive.
- Return the first node that violates its allowed interval.

=== card | 450
time: 30 min

## The problem

Remove a given key from a binary search tree and return the resulting root. If the key is not present, leave the tree unchanged. The remaining nodes must still satisfy the strict search-tree ordering.

For a root 5 with left child 3 and right subtree rooted at 7 with left child 6, deleting 5 can replace its value with 6, the smallest value in its right subtree, then remove the original node 6.

## Constraints and what they imply

Keys are distinct, and the input is a valid binary search tree. The root itself may need to be removed, so a deletion can change the root pointer. A node has zero, one or two children; the two-child case cannot simply discard either subtree.

## Brute force

Traverse the tree, collect all keys except the one to remove, and construct a new search tree from those keys. This takes at least O(n) time and O(n) storage for the list and reconstructed nodes. It also replaces the original tree rather than editing only the affected path. The full traversal and rebuilding are the bottleneck when the tree is large and balanced.

## The insight

Find the target using the search-tree ordering. If it has at most one child, replace its parent's pointer with that child. If it has two children, copy the in-order successor's value into the target: the successor is the smallest node in the right subtree, so it is greater than every key on the left and no larger than any remaining key on the right. Then remove the successor from its original location. The successor has no left child, reducing the problem to the one-child case.

## Optimal solution, traced

```steps
Delete root 5 with children 3 and 7; 7 has left child 6
    successor is {{6}}
---
Copy 6 into the target and remove the original leaf 6
    root 6, left 3, right 7
---
All remaining keys are ordered
    return the updated root
```

The successor is the smallest key greater than the deleted key, so substituting it preserves both subtree bounds. Removing its original node avoids leaving a duplicate. The other pointers are unchanged.

## Code

```python
def delete_bst(root, key):
    parent = None
    node = root
    while node is not None and node.val != key:
        parent = node
        node = node.left if key < node.val else node.right
    if node is None:
        return root

    if node.left is not None and node.right is not None:
        successor_parent = node
        successor = node.right
        while successor.left is not None:
            successor_parent = successor
            successor = successor.left
        node.val = successor.val
        parent, node = successor_parent, successor

    child = node.left if node.left is not None else node.right
    if parent is None:
        return child
    if parent.left is node:
        parent.left = child
    else:
        parent.right = child
    return root
```

## Complexity

The search path and the successor path together have length O(h), where `h` is tree height. The algorithm uses O(1) auxiliary space and modifies the tree in place. In a skewed tree, O(h) can be O(n).

## Mistakes and edge cases

- Return the replacement child when deleting a root with at most one child.
- Delete the successor from its old location after copying its value.
- The successor may be the target's immediate right child or may itself have a right child.
- Searching for a missing key must leave the tree unchanged.

## Variations

- Use the in-order predecessor from the left subtree instead of the successor.
- Return whether a deletion occurred as well as the new root.
- Maintain subtree sizes to support order-statistic queries after deletion.

=== card | 230
time: 25 min

## The problem

Return the `k`-th smallest key in a binary search tree, using one-based `k`. For a tree whose sorted keys are `[1, 3, 5, 8]`, `k = 3` returns 5.

## Constraints and what they imply

The tree has distinct keys and `k` is within the number of nodes. An in-order traversal of a valid search tree visits keys in strictly increasing order. The tree may be skewed, so an explicit stack avoids relying on recursion depth.

## Brute force

Traverse all `n` nodes, collect their values, sort them, and read position `k - 1`. This uses O(n log n) time and O(n) space. Even a full in-order traversal and list uses O(n) time and space; neither needs to keep visiting nodes after the requested rank has been reached.

## The insight

Perform in-order traversal lazily. Push the current node's left spine, pop the next smallest node, and then move to its right subtree. Decrease `k` on every pop. The node popped when `k` reaches zero is the answer.

## Optimal solution, traced

```steps
Sorted order of the tree is 1, 3, 5, 8; request k = 3
    pop 1: remaining rank 2
---
Pop 3
    remaining rank 1
---
Pop 5
    remaining rank 0; return {{5}}
```

The stack holds ancestors whose left subtrees have been handled but which have not yet been emitted. Popping therefore yields the next smallest key, and exactly `k` pops reach the desired rank.

For example, after visiting a node with a right child, do not immediately return that child's key: its own left subtree may contain smaller keys. Following that child's left spine before the next pop restores the correct order. The algorithm stops as soon as the answer appears, so a small rank need not require traversing the rest of the tree. Already visited nodes need not remain on the stack.

## Code

```python
def kth_smallest(root, k):
    if k < 1:
        raise ValueError("k must be positive")
    stack = []
    node = root
    while node is not None or stack:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        node = node.right
    raise ValueError("k exceeds the number of nodes")
```

## Complexity

The traversal visits the first `k` keys and at most one additional left spine, for O(h + k) time and O(h) stack space. The worst case is O(n) time and O(n) space on a skewed tree.

## Mistakes and edge cases

- `k` is one-based; decrement on a pop, not on a push.
- Visit a popped node before its right subtree.
- For repeated queries on an unchanged tree, consider preprocessing the sorted keys rather than repeating the walk.

## Variations

- Yield all keys lazily with the same stack.
- Find the `k`-th largest by reversing left and right.
- Maintain subtree sizes to answer rank queries in O(h) as the tree changes.

=== card | 173
time: 25 min

## The problem

Create an iterator over a binary search tree that returns its keys in ascending order. `has_next()` reports whether another key remains; `next()` returns that key and advances the iterator.

For a tree with keys 2, 5 and 8, three calls to `next()` return 2, 5 and 8. Afterwards `has_next()` is false.

## Constraints and what they imply

The tree remains unchanged while the iterator is in use. The goal is O(h) iterator space, where `h` is tree height, rather than storing every key. An individual operation may walk a long left spine, so distinguish worst-case per-call time from amortised time over the full iteration.

## Brute force

Traverse the whole tree in-order in the constructor, save all keys in an array, and return them by index. The constructor takes O(n) time and stores O(n) keys even if the caller requests only one. The eager materialisation is the bottleneck in memory and startup work.

## The insight

Pause an iterative in-order traversal between calls. Store a stack of nodes whose left subtrees have been explored but which have not been returned. The constructor pushes the root's left spine. Each `next()` pops the next node and pushes the left spine of that node's right subtree.

## Optimal solution, traced

```steps
Tree root 5, left 2, right 8: push the left spine
    stack [5, 2]
---
Pop 2; it has no right subtree
    return {{2}}; stack [5]
---
Pop 5, then push the left spine of its right child 8
    return {{5}}; stack [8]
---
Pop 8
    return {{8}}; stack empty
```

At every step, the top of the stack is the smallest not-yet-returned key. Pushing a right subtree's left spine restores that invariant after its predecessor is returned.

Calling `has_next()` only inspects the stack; it does not consume a key. This means repeated checks have no effect on the next value. The iterator assumes the underlying tree is not modified between calls, because its stored traversal state would otherwise become stale.

## Code

```python
class BSTIterator:
    def __init__(self, root):
        self.stack = []
        self._push_left(root)

    def _push_left(self, node):
        while node is not None:
            self.stack.append(node)
            node = node.left

    def has_next(self):
        return bool(self.stack)

    def next(self):
        if not self.stack:
            raise StopIteration("the tree iterator is exhausted")
        node = self.stack.pop()
        self._push_left(node.right)
        return node.val
```

## Complexity

The stack stores O(h) nodes. Each node is pushed once and popped once, so a complete iteration takes O(n) time: `next()` is O(1) amortised, though a particular call can take O(h) while pushing a left spine. The constructor can also take O(h).

## Mistakes and edge cases

- Popping without pushing the right child's left spine skips keys.
- An empty tree has no next value.
- Do not describe every `next()` as worst-case O(1); the guarantee is amortised.

## Variations

- Iterate in descending order by swapping left and right.
- Make the class conform to Python's `__iter__` and `__next__` protocol.
- Explore what extra coordination would be needed if the tree could change during iteration.

=== card | 99
time: 30 min

## The problem

Exactly two values in a binary search tree have been swapped. Restore the search-tree ordering by swapping those values back, without changing the tree's shape.

For an in-order sequence that should be `[1, 2, 3, 4, 5]` but is now `[1, 4, 3, 2, 5]`, swap 4 and 2. The same method also handles adjacent swapped values, such as `[1, 3, 2, 4]`.

## Constraints and what they imply

The original keys are distinct and the tree shape was not changed. Its in-order traversal should therefore be strictly increasing once corrected. A tree can be skewed, so recursion may use O(n) stack frames. The task requires an in-place repair rather than constructing a replacement tree.

## Brute force

Collect all nodes in in-order, sort their values, and write the sorted values back into the nodes. This uses O(n log n) time and O(n) extra space. The sorting and stored list are unnecessary because only two values are wrong.

## The insight

During in-order traversal, look for a descent: a previous value greater than the current value. The larger value at the first descent is the first misplaced node. The smaller value at the last descent is the other misplaced node. Adjacent swapped values give one descent; non-adjacent swapped values give two. Swap those two values after traversal.

## Optimal solution, traced

```steps
In-order values: 1, 4, 3, 2, 5
    first descent 4 > 3: record first = 4, second = 3
---
Second descent 3 > 2
    keep first = 4; update second = {{2}}
---
Swap the recorded values
    in-order becomes {{1, 2, 3, 4, 5}}
```

In the original strictly increasing sequence, a too-large value moved left is followed by a smaller value, creating the first descent. A too-small value moved right is preceded by a larger value, creating the last. If they were adjacent, the same descent identifies both.

## Code

```python
def recover_bst(root):
    stack = []
    node = root
    previous = first = second = None
    while node is not None or stack:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        if previous is not None and previous.val > node.val:
            if first is None:
                first = previous
            second = node
        previous = node
        node = node.right
    if first is None or second is None:
        raise ValueError("expected exactly two swapped values")
    first.val, second.val = second.val, first.val
```

## Complexity

The traversal visits all `n` nodes once, for O(n) time. The explicit stack uses O(h) auxiliary space for height `h`. A threaded Morris traversal can reduce auxiliary space, but temporarily changes pointers and needs extra care to restore them.

## Mistakes and edge cases

- Keep the first node from the first descent; update the second at every descent.
- Do not assume there are always two descents: adjacent swapped values produce only one.
- Swapping node links would change the shape; swap the two stored values instead.

## Variations

- Identify the two out-of-order values without modifying the tree.
- Use Morris traversal to reduce auxiliary space while restoring every temporary thread.
- Check a repaired tree with the bounds-based validator.

=== card | 669
time: 30 min

## The problem

Remove every key outside the inclusive interval `[low, high]` from a binary search tree and return the new root. Keep the remaining keys in a valid search tree.

For root 3 with left child 1 and right child 5, trimming to `[2, 4]` leaves only node 3. If the original root is outside the interval, a descendant can become the new root.

## Constraints and what they imply

The input is a valid search tree with distinct keys. Both interval endpoints are included. Whole subtrees can be discarded using the ordering: if a node is below `low`, its left subtree is also below `low`; the symmetric rule applies above `high`.

## Brute force

Traverse every node, collect keys in the range, and build a new search tree from the retained sorted keys. This takes O(n) time plus O(n) storage for the traversal and new nodes. The full copy is unnecessary: the existing pointers can be adjusted along the interval boundaries.

## The insight

Move the root down until it is in range: below `low` move right, and above `high` move left. Then trim the left boundary. If a node's left child is below `low`, replace that child by its right child, since the low-valued child's left subtree is entirely too small. Walk down the retained left side and repeat. Do the mirror operation on the right boundary for values above `high`.

All interior subtrees are already bounded by their ancestors and need no further processing.

## Optimal solution, traced

```steps
Root 3 lies in [2, 4]
    keep 3
---
Its left child 1 is below 2
    replace that child with its right subtree, here empty
---
Its right child 5 is above 4
    replace that child with its left subtree, here empty
    return {{3}}
```

Discarded branches cannot contain valid values by the search-tree ordering. The replacement child is the only side that might still contain valid keys, and linking it preserves the ancestor's ordering constraints.

## Code

```python
def trim_bst(root, low, high):
    while root is not None and (root.val < low or root.val > high):
        root = root.right if root.val < low else root.left
    node = root
    while node is not None:
        while node.left is not None and node.left.val < low:
            node.left = node.left.right
        node = node.left
    node = root
    while node is not None:
        while node.right is not None and node.right.val > high:
            node.right = node.right.left
        node = node.right
    return root
```

## Complexity

Every followed or discarded node is visited at most a constant number of times, so time is O(n) in the worst case. The iterative pointer updates require O(1) auxiliary space. Entire out-of-range subtrees can be skipped without visiting their interiors.

## Mistakes and edge cases

- Root adjustment must happen before adjusting its descendants.
- Keep keys equal to either endpoint.
- An interval containing no keys returns `None`.
- When removing a too-small left child, keep its right subtree, not its left.

## Variations

- Return a sorted list of matching keys without changing the tree.
- Trim recursively and compare the stack-space trade-off on a skewed tree.
- Count the retained keys while trimming.

=== card | 1373
time: 45 min

## The problem

Given an arbitrary binary tree of integer values, find the largest sum among its subtrees that are valid binary search trees. A subtree contains a node and all its descendants. The empty subtree is allowed and has sum zero, so the answer is never negative.

If a root 5 has left child 3 and right child 8, the whole tree is a search tree with sum 16. If all node values are negative, choosing the empty subtree gives zero rather than a negative answer.

## Constraints and what they imply

The input is not guaranteed to be a search tree. A valid candidate needs strict ordering throughout both child subtrees, not merely between a node and its children. The tree may be deep, so a recursive implementation can exceed Python's recursion limit. Negative values mean a valid subtree's sum is not necessarily better than the empty choice.

## Brute force

For each node, independently validate its entire subtree using bounds and sum its keys if valid. On a chain, subtree sizes are `n`, `n-1`, and so on, giving O(n²) time. Rechecking descendants for each possible root is the bottleneck.

## The insight

Process nodes bottom-up. For every subtree record whether it is a search tree, its minimum key, its maximum key, and its sum. A node forms a valid search tree precisely when both child summaries are valid and `left_max < node.val < right_min`. In that case compute the new minimum, maximum and sum and update the best answer.

An empty child is valid with minimum positive infinity, maximum negative infinity and sum zero. These sentinels make the strict comparisons work without special cases. An invalid child makes its parent invalid regardless of its bounds. A separate best value starts at zero to represent the allowed empty subtree.

## Optimal solution, traced

```steps
Leaf 3 returns valid, min 3, max 3, sum 3
    best 3
---
Leaf 8 returns valid, min 8, max 8, sum 8
    best 8
---
Root 5 sees left max 3 < 5 < right min 8
    subtree sum {{16}}; best {{16}}
```

The summary is sufficient: the child validity flags establish ordering inside each subtree, while the two extreme keys establish all cross-boundary comparisons with the parent. Conversely, if either child is invalid or an extreme violates the bound, the parent's full subtree cannot be valid.

The explicit post-order stack first schedules a node for a later visit, then processes its children. On that later visit both summaries exist. This avoids dependence on the Python recursion limit; the summary table retains one record per node.

For a leaf with value `-4`, the two empty summaries allow the leaf to be classified as valid with sum `-4`, but the global best stays zero. If a parent and child both have value 5, the strict comparison rejects the parent even though each leaf is valid by itself. Invalid summaries carry placeholder bounds that are never used unless their validity flag is true.

## Code

```python
def maximum_sum_bst(root):
    if root is None:
        return 0
    empty = (True, float("inf"), float("-inf"), 0)
    summaries = {}
    best = 0
    stack = [(root, False)]
    while stack:
        node, visited = stack.pop()
        if not visited:
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
            continue
        left = summaries.get(node.left, empty)
        right = summaries.get(node.right, empty)
        if left[0] and right[0] and left[2] < node.val < right[1]:
            total = left[3] + node.val + right[3]
            summaries[node] = (True, min(left[1], node.val), max(right[2], node.val), total)
            best = max(best, total)
        else:
            summaries[node] = (False, 0, 0, 0)
    return best
```

## Complexity

Each node is pushed and processed a constant number of times, so time is O(n) with expected O(1) dictionary operations. The summary table uses O(n) space, and the explicit traversal stack uses O(h) for tree height `h`. This is more space than a recursive implementation that returns child summaries without retaining a table, but it works on deep trees without changing the recursion limit.

## Mistakes and edge cases

- Test both child validity flags before using their minimum and maximum.
- Ordering is strict, so duplicates cannot belong to the same valid search-tree subtree.
- Start the best sum at zero: all-negative trees still have answer zero.
- Do not confuse an arbitrary connected set of nodes with a subtree containing all descendants.

## Variations

- Return the root of the best subtree as well as its sum.
- Count valid search-tree subtrees instead of maximising their sum.
- Compute the size of the largest valid search-tree subtree.

=== card | 220
time: 45 min

## The problem

Given an array and two non-negative limits, decide whether there are two distinct indices whose distance is at most `index_diff` and whose values differ by at most `value_diff`.

For `[1, 5, 3]`, `index_diff = 2` and `value_diff = 2`, the pair 1 and 3 qualifies. With the same values but `index_diff = 1`, neither adjacent pair qualifies.

## Constraints and what they imply

The limits are inclusive, and the two indices must be different. Values can be negative, so a bucket calculation must handle negative numbers consistently. If `index_diff` is zero, no distinct pair can qualify. For each new value, only the previous `index_diff` values need to be considered.

## Brute force

For each index, compare its value with every earlier value within the allowed index distance. This costs O(nk) time for `k = min(index_diff, n)` and O(1) extra space. When the allowed distance is large, repeated comparisons with the same window become quadratic.

## The insight

Use buckets of integer width `value_diff + 1`. Any two integers in the same bucket differ by at most `value_diff`, so finding an existing value in the new value's bucket immediately proves a match. A match can also straddle a bucket boundary, but only in the two neighbouring buckets; check the actual difference there.

Keep buckets only for the previous `index_diff` positions. Check the current value before inserting it, so it cannot match itself. After inserting, evict the value that will be too old for the next iteration. If a bucket already contained a value, the algorithm would have returned; therefore each active bucket has at most one stored value.

Python's `//` is floor division, which gives consistent contiguous buckets for negative values as well as positive ones. The buckets are not based on truncation towards zero.

## Optimal solution, traced

```steps
Values [1, 5, 3], index limit 2, value limit 2
    bucket width = 3
---
Insert 1 into bucket 0; insert 5 into bucket 1
    window holds both values
---
Value 3 is in bucket 1, already occupied by 5
    |3 - 5| = 2; return {{true}}
```

If two integers are within `value_diff`, their bucket numbers differ by at most one: two buckets separated by an entire bucket have a minimum gap of `value_diff + 2`. Checking the same bucket and its two neighbours therefore considers every possible qualifying value. The maintained window ensures every considered index is close enough, so the returned match is valid.

When no bucket matches, inserting the current value and evicting the oldest value preserves the invariant for the next index. By induction, no qualifying pair is missed. These bounds concern integer values; for real-valued inputs, bucket endpoints and precision require a different treatment.

When `value_diff` is zero, the bucket width is one, so two equal integers share a bucket and distinct integers do not. For a negative example with width three, `-1 // 3` is `-1` and `0 // 3` is `0`; those adjacent buckets are still checked against each other. Their actual difference is one.

## Code

```python
def contains_nearby_almost_duplicate(nums, index_diff, value_diff):
    if index_diff < 0 or value_diff < 0:
        raise ValueError("distance limits must be non-negative")
    if index_diff == 0:
        return False
    width = value_diff + 1
    buckets = {}
    for i, value in enumerate(nums):
        bucket = value // width
        if bucket in buckets:
            return True
        if bucket - 1 in buckets and value - buckets[bucket - 1] <= value_diff:
            return True
        if bucket + 1 in buckets and buckets[bucket + 1] - value <= value_diff:
            return True
        buckets[bucket] = value
        if i >= index_diff:
            del buckets[nums[i - index_diff] // width]
    return False
```

## Complexity

Each value makes a constant number of expected O(1) dictionary operations, so expected time is O(n). The active window stores at most `min(n, index_diff)` values, giving O(min(n, index_diff)) auxiliary space. The expected bound relies on ordinary hash-table behaviour; it is not a worst-case guarantee against adversarial hashing.

## Mistakes and edge cases

- Width is `value_diff + 1`, including when the permitted value difference is zero.
- Use floor division for negative integers; truncation towards zero gives inconsistent bucket ranges.
- Evict by index, not by comparing values, and check before inserting the current index.
- Do not evict before checking the value exactly `index_diff` positions back; that pair is allowed.

## Variations

- Use an ordered multiset and check the smallest active value at least `x - value_diff`.
- Return the matching pair of indices by storing an index with each bucket value.
- Count qualifying pairs instead of merely detecting one; a single value per bucket is no longer sufficient.
