---
key: trees
name: Binary trees and tree recursion
stage: hier
summary: Walk any binary tree depth-first or level by level, and solve tree problems by deciding what flows down as arguments and what flows up as return values.
why: Trees are the shape of hierarchical data: file systems, the DOM, syntax trees, JSON documents, org charts and the indexes inside every database. Tree recursion is also the bridge from loops to graphs, backtracking and dynamic programming: once you can say "this call returns X about its subtree" and "this argument tells the node Y about its ancestors", most tree problems become a few lines of thought and a dozen lines of code. This module makes that habit automatic and adds the engineering details that bite in Python: the recursion limit, iterative traversals, and turning trees into strings and back.
outcomes:
- Store a binary tree as linked nodes, an array or a parent map, and convert LeetCode-style level-order lists to trees and back
- Produce pre-order, in-order, post-order and level-order traversals, recursively and with an explicit stack or queue
- Solve a tree problem by writing the contract "each call returns X about its subtree", the empty-tree value and the combine step
- Pass path state (depth, running maximum, prefix sums) down the tree and decide whether information must flow down, up or both
- Compute global answers such as the diameter and the maximum path sum by separating what a node returns from what it records
- Find lowest common ancestors, rebuild a tree from two traversals, and serialise and deserialise trees
cues:
- Nodes with left and right (or child) pointers, nested folders, org charts, parse trees, nested JSON
- The answer at a node combines answers from its left and right subtrees
- Facts about the path from the root (depth, maximum so far, running sum) decide each node's answer
- "Level", "row", "nearest" or "minimum depth" in the statement
- "Any path" or "between any two nodes": the best path may bend at a node far below the root
traps:
- Recomputing a subtree's height or size inside the recursion, which turns O(n) into O(n^2) on skewed trees
- Returning a two-branch value to the parent, so the "path" forks
- Sharing one mutable path list or counter across branches without undoing it on the way back
- Recursing 10^4 or more levels deep in Python, past the default recursion limit of 1000
- Initialising a global best to 0 when every value can be negative
systems:
- File systems: Python's os.walk yields directories top-down (pre-order) or bottom-up (post-order, for deletes and size totals), and CPython 3.12 implements it with an explicit stack
- The DOM: the WHATWG DOM Standard defines "tree order" as a pre-order, depth-first traversal, the order querySelectorAll returns elements in
- Compilers: CPython parses source into an ast tree and emits bytecode in post-order, operands before their operator
- Serialisation: JSON documents are trees, and Python's json.loads raises RecursionError on extremely deep nesting
further:
- Notes · 20 min | MIT 6.006 (Spring 2020) Lecture 6 notes, Binary Trees I: read Terminology, Traversal Order and Tree Navigation | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/376714cc85c6c784d90eec9c575ec027_MIT6_006S20_lec6.pdf
- Book · 15 min | Open Data Structures 6.1 BinaryTree: 6.1.1 Recursive Algorithms and 6.1.2 Traversing Binary Trees (a traversal with no stack at all) | https://opendatastructures.org/ods-python/6_1_BinaryTree_Basic_Binary.html
- Article · 10 min | USACO Guide, DP on Trees: the Tutorial section, where each node returns a small table built from its children | https://usaco.guide/gold/dp-trees#tutorial
bank: trees
---

=== primer | What do pre-order, in-order and post-order visit, and when do you need each? | 15 min
goal: Store a binary tree, name its parts precisely, and pick the depth-first order whose visiting moment matches the question
tag: trees-dfs | Depth-first traversal orders
link: Wikipedia, Tree traversal | https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search | 10 min: the "Depth-first search" section with its pre-order, post-order and in-order subsections, then the short "Applications" section (copying, deleting, prefix and postfix expressions)
practice: 94, 104

> [!key]
> A depth-first traversal visits the whole tree with one recursive function; pre-order, in-order and post-order differ only in **when** the node itself is handled: before its children, between them, or after them. Choose the order by what the node needs: facts from above (pre-order), its children's results (post-order), or sorted order in a search tree (in-order). All three cost O(n) time and O(h) stack, where h is the height.

## Intuition

Picture walking around the outside of the tree, starting at the root and keeping the tree on your left, like tracing its outline with a pencil. You pass every node three times: once on the way down its left side, once underneath it (between its two subtrees), and once on the way back up its right side.

```text
          1            Trace the outline anticlockwise from the root:
        /   \            pre-order  lists a node the FIRST time you pass it
       2     3           in-order   lists it when you pass UNDER it
      / \     \          post-order lists it the LAST time you pass it
     4   5     6
```

That single walk is the recursion. The three orders are just three places to write `out.append(node.val)`.

## How it works

### Vocabulary you will use all module

- A **node** holds a value and links to at most two **children**, called left and right (the order matters). The node above is its **parent**. The top node is the **root**; a node with no children is a **leaf**.
- The **subtree** of a node is that node plus all its descendants. Every recursive tree function is a statement about subtrees.
- The **depth** of a node is the number of edges from the root to it (the root has depth 0).
- The **height** of a tree, in this module, is the number of nodes on its longest root-to-leaf path, so an empty tree has height 0 and a single node height 1. This matches LeetCode's "maximum depth"; some books count edges instead, which is one less. Diameters (later card) count edges.
- A tree with height h holds at most 2^h - 1 nodes, so n nodes need height at least log2(n + 1). A tree is **balanced** when its height stays O(log n); a **degenerate** tree is a chain of height n.

### Three ways to store a tree

1. **Linked nodes**: a `TreeNode` object with `val`, `left` and `right`. This is what interview problems hand you, and what you use when the shape is irregular.
2. **An array, for complete trees**: store the levels left to right; the children of index i are 2i + 1 and 2i + 2, and its parent is (i - 1) // 2. No pointers at all. Binary heaps use exactly this layout.
3. **A parent array or child lists, for general trees**: `parent[v]` for each vertex, or `children[v]` as a list. File systems, org charts and "n nodes and n - 1 edges" inputs arrive like this.

LeetCode prints trees as a level-order list with `None` for missing children, such as `[1, 2, 3, 4, 5, None, 6]` for the tree above. The next card gives a builder for that format.

### The walk

The function below makes one depth-first pass and records each node at all three moments. Keep only the line you need and you have the traversal you need.

## Cost

Count the calls. `walk` runs once for each of the n nodes and once for each empty child slot. A tree with n nodes has 2n child slots, of which n - 1 hold a node (every node except the root is someone's child), so n + 1 slots are empty. That is 2n + 1 calls, each doing O(1) work apart from its own two calls, so the traversal is **O(n) time**.

Space is the call stack. At any moment the stack holds the frames on one root-to-node path, so its size is at most h + 1: **O(h) space**, about log2 n for a balanced tree and n for a chain. In Python the default recursion limit is 1000 frames, so a chain-shaped tree of a few thousand nodes crashes the recursive version; the card on iterative traversal fixes that.

## When to use it

| Order | Node handled | Use it when | Examples |
|---|---|---|---|
| Pre-order | before its children | the node must act before its subtree: copy, print an outline, pass facts down | serialising a tree, printing a folder outline |
| In-order | between left and right | the left-node-right order means something | sorted keys of a binary search tree, an infix expression |
| Post-order | after its children | the node needs its children's results | heights, sizes, deleting a tree, evaluating an expression |
| Level order | by depth | the question is about levels or the nearest node | next card |

Do not use a depth-first traversal when the question is about levels or the shallowest match (breadth-first finds the nearest leaf without exploring deep branches), or when the tree may be very deep and you are in Python (use an explicit stack).

## Worked trace

One walk over the tree above, recording all three orders. Watch the call stack: it is exactly the path from the root to the current node.

```steps
Call walk(1). First touch of 1, so pre-order records it; then walk descends to the left child
    stack  walk(1)
    pre    {{1}}
    in     -
    post   -
---
walk(2): its first touch puts 2 into pre-order, and the walk descends left again
    stack  walk(1) > walk(2)
    pre    1 {{2}}
    in     -
    post   -
---
walk(4) is a leaf: both child calls return at once, so its three touches happen back to back
    stack  walk(1) > walk(2) > walk(4)
    pre    1 2 {{4}}
    in     {{4}}
    post   {{4}}
---
Back in walk(2), the left call has returned, so 2 goes into in-order; then walk(5), another leaf
    stack  walk(1) > walk(2) > walk(5)
    pre    1 2 4 {{5}}
    in     4 {{2}} {{5}}
    post   4 {{5}}
---
walk(2) finishes: its last touch puts 2 into post-order. Back in walk(1), the left side is done, so 1 goes into in-order
    stack  walk(1)
    pre    1 2 4 5
    in     4 2 5 {{1}}
    post   4 5 {{2}}
---
walk(3): pre-order 3; its left child is None, so its in-order touch comes immediately; then the leaf 6
    stack  walk(1) > walk(3) > walk(6)
    pre    1 2 4 5 {{3}} {{6}}
    in     4 2 5 1 {{3}} {{6}}
    post   4 5 2 {{6}}
---
walk(3) and then walk(1) finish, appending 3 and 1 to post-order. Every node was touched three times
    stack  (empty)
    pre    1 2 4 5 3 6
    in     4 2 5 1 3 6
    post   4 5 2 6 {{3}} {{1}}
```

## Template

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def traverse(root):
    """Return (preorder, inorder, postorder) value lists from one depth-first walk."""
    pre, ino, post = [], [], []

    def walk(node):
        if node is None:
            return
        pre.append(node.val)      # first touch: before the children
        walk(node.left)
        ino.append(node.val)      # second touch: between the children
        walk(node.right)
        post.append(node.val)     # last touch: after the children

    walk(root)
    return pre, ino, post


root = TreeNode(1, TreeNode(2, TreeNode(4), TreeNode(5)), TreeNode(3, None, TreeNode(6)))
print(traverse(root))
# ([1, 2, 4, 5, 3, 6], [4, 2, 5, 1, 3, 6], [4, 5, 2, 6, 3, 1])
```

Appending to lists owned by the outer function keeps the whole walk O(n). For a single order, delete the other two appends.

## Pitfalls

- **Concatenating lists**: `return [node.val] + pre(node.left) + pre(node.right)` copies every sublist at every level. That is O(n log n) on a balanced tree and O(n^2) on a chain. Append to one shared list instead.
- **No base case**: forgetting `if node is None: return` gives `AttributeError: 'NoneType' object has no attribute 'left'` at the first leaf.
- **Depth versus height**: depth is measured down from the root, height up from the leaves, and books disagree on counting nodes or edges. Write your convention in the docstring.
- **In-order needs two children**: it is defined for binary trees only. For a node with many children, only pre-order and post-order make sense.
- **Mutable defaults**: `def walk(node, out=[])` shares one list across every call of the function, including later test cases.
- **Recursion depth**: Python raises `RecursionError` near 1000 nested calls. LeetCode-sized trees (up to 10^4 nodes) can be that deep if they are skewed.

## Check yourself

Q: A binary tree has pre-order `A B D E C F` and in-order `D B E A C F`. What is its post-order?
A: `D E B F C A`. Pre-order says A is the root. In in-order, D B E lies left of A and C F right of it. The left part's pre-order is B D E, so B is its root with D on the left and E on the right. The right part's pre-order is C F and in-order C F, so C has no left child and F is its right child. Post-order is left subtree, right subtree, root: D E B, F C, A.

Q: `walk` is called 2n + 1 times. Why is the traversal still O(n), and why is the extra space O(h) rather than O(n)?
A: Each call does a constant amount of work besides making its two child calls, and 2n + 1 is O(n). A frame is popped as soon as its subtree is finished, so the only frames alive at any moment are those on the path from the root to the current node: at most h + 1 of them.

Q: Which order would you use to (a) print a folder outline with each folder above its contents, (b) compute the total size of every folder, (c) list a binary search tree's keys in increasing order?
A: (a) Pre-order: a folder is printed before anything inside it. (b) Post-order: a folder's total needs its children's totals first. (c) In-order: in a binary search tree everything left of a node is smaller and everything right is larger, so left, node, right comes out sorted.

Q: A colleague's `preorder(node)` returns `[node.val] + preorder(node.left) + preorder(node.right)`. It is fine on the tests but times out on a 30,000-node input. Why, and what is the fix?
A: The large input is probably a chain. Each level copies the whole list returned from below, so the total copying is about 1 + 2 + ... + n, which is O(n^2), around 450 million element copies at n = 30,000. (It also exceeds the recursion limit unless that was raised.) Append to a single shared list, as in the template, for O(n).

## Lab

- **94**: return the in-order values recursively by keeping only the middle `append` of the template. Expected: for `[1, 2, 3, 4, 5, None, 6]` the answer is `[4, 2, 5, 1, 3, 6]`, and `[]` for an empty tree; O(n) time and O(h) extra space. You will solve it again without recursion later in this module.
- **104**: compute the maximum depth with a post-order function (each node needs its children's depths first). Expected: 3 for `[1, 2, 3, 4, 5, None, 6]`, 0 for an empty tree, and 4 for the chain `[1, 2, None, 3, None, 4]`.

> [!know]
> You now know how to store a binary tree, walk it depth-first in O(n), and choose pre-, in- or post-order by when a node needs its information.

=== primer | How do you walk a tree level by level, and why does a queue do it? | 14 min
goal: Traverse a tree in level order with a deque, group nodes by level with the level-size loop, and build test trees from LeetCode-style lists
tag: trees-bfs | Level-order traversal with a queue
link: Python docs, collections.deque | https://docs.python.org/3/library/collections.html#collections.deque | 5 min: the class description: appends and pops at either end are O(1), unlike list.pop(0) and list.insert(0, x), which move every element
link: Wikipedia, Tree traversal | https://en.wikipedia.org/wiki/Tree_traversal#Breadth-first_search | 3 min: the short "Breadth-first search" section, then the matching queue pseudocode under "Implementations"
practice: 102, 104

> [!key]
> Breadth-first search (BFS) visits nodes in order of depth: the root, then all its children, then all grandchildren. A FIFO queue produces this order automatically, because children join the back of the queue behind every node already waiting. Taking `len(queue)` before each round splits the stream into levels. It costs O(n) time and O(w) memory, where w is the widest level.

## Intuition

Drop a stone in a pond: the ripple reaches everything at distance 1, then distance 2, and never jumps ahead. Or think of an org chart read rank by rank: the CEO, then every direct report, then every report of those. A queue is the waiting line that enforces this: whoever was discovered earlier is served earlier, and a node's children are discovered only when the node is served, so they always wait behind the rest of the current level.

A stack would serve the newest node first and dive deep, which is depth-first order. Swapping the container is the only difference between the two traversals.

## How it works

1. Put the root in a `collections.deque`.
2. While the queue is not empty, read `size = len(queue)`. Exactly that many nodes form the current level, because every one of them was enqueued while the previous level was processed.
3. Pop `size` nodes from the front, record them, and push their children on the back. The children belong to the next level and are not touched in this round.
4. Store the finished level and repeat.

Many questions are "BFS plus one line per level": the **right side view** is the last value of each level, the average or maximum of each row is a reduction over the level list, and the **minimum depth** is the level number of the first leaf you pop, at which point you can stop.

For width questions where gaps count, give each node a position as in an array-backed heap (children of i at 2i and 2i + 1) and measure last minus first plus one per level. Subtract each level's first position from the positions on that level so the numbers stay small.

### Level order without a queue

You can also group by level with depth-first recursion: pass `depth` down and append the value to `levels[depth]`, creating the list the first time a depth is reached. Same output, O(h) stack instead of O(w) queue. Use whichever is lighter for the tree's shape.

### The LeetCode list format

`[1, 2, 3, 4, 5, None, 6]` is a level-order listing in which `None` marks a missing child, and the children of missing nodes are simply not listed. It is **not** heap indexing: in `[1, None, 2, 3]`, the 3 is the left child of 2, even though index 3 would be a child of index 1 in an array heap. The builder below consumes the list with the same queue discipline that produced it, so you can make test trees in one line.

## Cost

Each node is appended to the queue once and popped once, both O(1) on a deque, and each pop does O(1) work: **O(n) time**.

The queue holds at most one level plus part of the next, so memory is **O(w)** for the widest level w. On a perfect tree the last level holds (n + 1) / 2 nodes, so w is about n/2 and BFS needs O(n) memory, while depth-first search needs only O(log n). On a chain the opposite holds: w = 1 but h = n.

With a plain list and `pop(0)`, every pop shifts the remaining elements, so the traversal becomes O(n^2) on wide trees.

## When to use it

| Question | Prefer | Why |
|---|---|---|
| Anything "per level" or "per row" | BFS | levels fall out of the level-size loop |
| Nearest node, minimum depth | BFS | stops at the first match without exploring deep branches |
| An answer built from subtree answers | DFS | children's results are ready in post-order |
| Memory on a huge balanced tree | DFS | O(log n) stack against O(n) queue |
| Memory on a deep, skinny tree | BFS | O(1)-ish queue against O(n) stack |

The same loop, with a visited set, is breadth-first search on graphs, where it finds shortest paths in unweighted graphs. You will reuse it unchanged in the graphs module.

## Worked trace

The tree from the previous card, `[1, 2, 3, 4, 5, None, 6]`:

```steps
Start: the queue holds only the root, so len(queue) = 1 and level 0 has one node
    queue   [{{1}}]
    level   []
    levels  []
---
Pop 1, record it, push its children 2 and 3. One pop done: level 0 is complete
    queue   [{{2}}, {{3}}]
    level   [1]
    levels  [{{[1]}}]
---
len(queue) = 2, so level 1 has two nodes. Pop 2 and push 4 and 5 behind 3
    queue   [3, {{4}}, {{5}}]
    level   [{{2}}]
    levels  [[1]]
---
Pop 3 and push its only child 6. Two pops done: level 1 is complete, and the queue now holds exactly level 2
    queue   [4, 5, {{6}}]
    level   [2, {{3}}]
    levels  [[1], {{[2, 3]}}]
---
len(queue) = 3: pop 4, 5 and 6. None has children, so nothing is pushed
    queue   []
    level   [{{4}}, {{5}}, {{6}}]
    levels  [[1], [2, 3], {{[4, 5, 6]}}]
---
The queue is empty, so the walk ends. Its peak size was 3, the width of the widest level
    queue   []
    levels  [[1], [2, 3], [4, 5, 6]]
```

## Template

```python
from collections import deque


def level_order(root):
    """Values grouped by depth: [[root], [depth 1, ...], ...]."""
    if root is None:
        return []
    levels, queue = [], deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):        # exactly the nodes of this level
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        levels.append(level)
    return levels


def build(values):
    """Tree from a LeetCode-style level-order list such as [1, 2, 3, None, 5]."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue, i = deque([root]), 1
    while queue and i < len(values):
        node = queue.popleft()
        if values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root


def to_list(root):
    """Inverse of build: level order with None gaps, trailing Nones removed."""
    out, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


print(level_order(build([1, 2, 3, 4, 5, None, 6])))   # [[1], [2, 3], [4, 5, 6]]
print(to_list(build([1, None, 2, 3])))                # [1, None, 2, 3]
```

`build` and `to_list` use the `TreeNode` class from the previous card. `range(len(queue))` is evaluated once, before the loop starts, so children pushed during the round do not extend it.

## Pitfalls

- **`list.pop(0)`** is O(n). Use `deque.popleft()`.
- **Merging levels**: replacing the `for _ in range(len(queue))` loop with `while queue` processes everything as one level. You still get level order, but lose the grouping.
- **Pushing `None` children** forces a check on every pop. Either skip them when pushing (as `level_order` does) or skip them when popping (as `to_list` does, because it needs the gaps), but do it consistently.
- **Heap indexing on LeetCode lists**: children of `None` are omitted, so index arithmetic like 2i + 1 does not find children in that format.
- **Empty tree**: return `[]` before creating the queue, or you will pop `None` and crash on `.val`.
- **Exploding positions in width problems**: positions double every level, so subtract the level's first position at each level to keep them small (Python will not overflow, but the numbers grow huge on deep trees, and C++ or Java do overflow).

## Check yourself

Q: For the tree `[1, 2, 3, None, 4, 5, 6, None, None, 7]`, what are the queue contents just after level 1 has been fully processed, and what does `level_order` return?
A: Level 1 is nodes 2 and 3. Popping 2 pushes its only child 4 (its left is None); popping 3 pushes 5 and 6. The queue is then `[4, 5, 6]`. Node 4 has no children here (the two Nones), 5 has left child 7, so the result is `[[1], [2, 3], [4, 5, 6], [7]]`.

Q: Why does BFS find the minimum depth of a tree faster than DFS on a tree with one shallow leaf and one very deep branch?
A: BFS pops nodes in order of depth, so the first leaf it pops is a shallowest leaf and it can return at once, after visiting only the levels above it. DFS has no such guarantee: it may descend the deep branch first, and it must keep exploring (at best pruning branches deeper than the best leaf found so far) before it knows which leaf is shallowest.

Q: You need, for every level, the largest value. Your tree is perfect with 2^20 - 1 nodes. BFS or DFS with a depth parameter, and why?
A: Both are O(n) time, but BFS keeps the whole last level in its queue: 2^19, over half a million node references. DFS with `best[depth] = max(...)` keeps only about 20 frames plus a 20-entry list. DFS is lighter here; BFS would win on a deep, skinny tree.

Q: What does `build([1, None, 2, 3])` produce, and why is the 3 not a child of the root?
A: The root 1 has no left child and a right child 2, and 2 has left child 3. After the root, values are consumed two at a time for each node popped from the queue: `None, 2` are the root's children, and `3` is the left child of the next node popped, which is 2. The missing left child of the root uses up its own slot (the `None`) but never enters the queue, so it has no slots for children.

## Lab

- **102**: return the values grouped by level with the template. Expected: `[[1], [2, 3], [4, 5, 6]]` for `[1, 2, 3, 4, 5, None, 6]`, `[]` for an empty tree, and `[[1], [2], [3]]` for `[1, None, 2, 3]`; O(n) time and O(w) extra space.
- **104**: solve maximum depth again, this time by counting how many levels BFS processes. Expected: 3 for `[1, 2, 3, 4, 5, None, 6]` and 3 for `[1, None, 2, 3]`.

> [!know]
> You now know how to traverse a tree level by level with a deque, split it into levels with the level-size loop, and build test trees from level-order lists.

=== primer | What should each recursive call return? Solving tree problems bottom-up | 16 min
goal: Solve a tree problem by writing the contract for what each call returns about its subtree, its value for an empty tree, and how a node combines its children's answers
tag: trees-up | Return answers up the tree
link: Open Data Structures, 6.1 BinaryTree | https://opendatastructures.org/ods-python/6_1_BinaryTree_Basic_Binary.html | 10 min: the depth computation just before section 6.1.1, then 6.1.1 "Recursive Algorithms": size and height as short recursive functions, the same contracts as this card
practice: 104, 110

> [!key]
> Most tree problems are solved by one function `f(node)` that **returns a fact about the subtree rooted at node**. Write that fact down as a contract, choose what an empty tree returns, and compute a node's answer from its children's answers, trusting the recursive calls. If the parent needs more than the contract gives, **return more** (a tuple or a sentinel) instead of calling a second walk: that keeps the whole solution O(n).

## Intuition

Ask a manager for the head count of her department. She does not count everyone herself: she asks each team lead below her for their team's count, adds them, and adds one for herself. Each team lead does the same. The question flows down, the answers flow up, and nobody does more than a little addition. That is information **flowing up**: an answer at a node depends only on answers about its subtrees.

The leap of faith is the same as in any recursion: assume the calls on the children already return correct answers for their subtrees (the induction hypothesis), and only worry about combining them. If the empty tree is handled correctly and the combine step is correct, induction on the height proves the whole function correct.

## How it works

### The "what does each call return?" template

Answer four questions before writing any code:

1. **Contract**: "f(node) returns ___ about the subtree rooted at node." Write it as the docstring.
2. **Empty tree**: what is f(None)? Pick the value that makes the combine step work with no special cases: 0 for heights, sizes and sums, True for "every node satisfies...", negative infinity for a maximum.
3. **Combine**: f(node) from f(node.left), f(node.right) and node.val. This is the only real thinking.
4. **Report**: the answer is f(root) or one part of it.

| Question | f(node) returns | f(None) | Combine |
|---|---|---|---|
| Number of nodes | size of the subtree | 0 | 1 + L + R |
| Maximum depth | nodes on the longest downward path | 0 | 1 + max(L, R) |
| Sum of values | sum of the subtree | 0 | val + L + R |
| Largest value | maximum in the subtree | -inf | max(val, L, R) |
| Mirror the tree | root of the mirrored subtree | None | swap the mirrored children |
| Is it height-balanced? | height, or -1 if unbalanced anywhere | 0 | -1 if L or R is -1 or abs(L - R) > 1, else 1 + max(L, R) |

### When the contract is too weak, strengthen it

"Is the tree height-balanced?" (every node's two subtrees differ in height by at most one) cannot be answered from two booleans. Both subtrees can be balanced while one has height 1 and the other height 3. The parent needs the heights too. You have two choices:

- **Return a tuple**: `(balanced, height)`. Clear and general.
- **Encode with a sentinel**: return the height, or -1 meaning "unbalanced somewhere below". It works because -1 is never a real height, and it lets the function stop early.

The slow alternative, calling a separate `height()` at every node, re-walks each subtree once per ancestor. That is O(n log n) on a balanced tree and O(n^2) on a chain. Strengthening the return value is the standard cure, and it is the seed of tree dynamic programming: in the advanced DP module, nodes return small tables instead of single numbers.

### Two trees at once

Comparing two trees is the same pattern with two arguments walked in lockstep: `same(a, b)` returns whether the subtrees rooted at a and b are identical. If either is None, they are equal only if both are; otherwise compare values and recurse on `(a.left, b.left)` and `(a.right, b.right)`.

## Cost

Every call does O(1) work besides its two child calls, and there is one call per node plus one per empty slot, so these functions are **O(n) time** and **O(h) stack**. The sentinel version of the balance check can be faster still: once a subtree reports -1, its ancestors return at once without visiting the remaining subtrees.

For contrast, the naive balance check `abs(height(l) - height(r)) <= 1 and balanced(l) and balanced(r)` calls `height` on every subtree from every ancestor. A node at depth d is measured d times, so the total is the sum of all depths: O(n log n) balanced, about n^2/2 on a chain.

## When to use it

Use the bottom-up pattern whenever a node's answer depends on its **descendants**: sizes, heights, sums, "does this subtree contain X", "is this subtree a valid search tree", removing or freeing nodes, and every tree DP. The cue in a problem statement is a quantity defined for "the subtree rooted at each node", or an answer that combines left and right results.

It is the wrong tool when a node's answer depends on its **ancestors** (its depth, the maximum on the path from the root, a running sum). That information has to flow down as an argument, which is the next card. Many problems use both directions at once.

## Worked trace

`h(node)` from the balance check, on this tree (`[1, 2, 3, 4, None, None, None, 5]`):

```text
          1
         / \
        2   3
       /
      4
     /
    5
```

```steps
h(1) calls h(2), which calls h(4), which calls h(5). Nothing can be decided until a leaf answers
    stack    h(1) > h(2) > h(4) > {{h(5)}}
    returned (none yet)
---
h(5): both children are None (height 0), the difference is 0, so it returns 1 + max(0, 0) = 1
    stack    h(1) > h(2) > h(4)
    returned 5 -> {{1}}
---
h(4): left 1, right 0. abs(1 - 0) <= 1, so the subtree at 4 is balanced and has height 2
    stack    h(1) > h(2)
    returned 5 -> 1, 4 -> {{2}}
---
h(2): left 2, right 0. abs(2 - 0) = 2 > 1: unbalanced, so it returns the sentinel -1
    stack    h(1)
    returned 5 -> 1, 4 -> 2, 2 -> {{-1}}
---
h(1): its left answer is -1, so it returns -1 at once. h(3) is never called, and is_balanced returns False
    stack    (empty)
    returned 5 -> 1, 4 -> 2, 2 -> -1, 1 -> {{-1}}
```

## Template

```python
def size(node):
    """Number of nodes in the subtree rooted at node."""
    if node is None:
        return 0
    return 1 + size(node.left) + size(node.right)


def height(node):
    """Nodes on the longest downward path from node (0 for an empty tree)."""
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))


def is_balanced(root):
    """True if at every node the two subtree heights differ by at most one."""
    def h(node):
        """Height of the subtree, or -1 if it is unbalanced anywhere."""
        if node is None:
            return 0
        left = h(node.left)
        if left < 0:
            return -1
        right = h(node.right)
        if right < 0 or abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return h(root) >= 0


def same_tree(a, b):
    """True if the trees rooted at a and b have the same shape and values."""
    if a is None or b is None:
        return a is b
    return a.val == b.val and same_tree(a.left, b.left) and same_tree(a.right, b.right)


def invert(node):
    """Mirror the subtree in place and return its root."""
    if node is None:
        return None
    node.left, node.right = invert(node.right), invert(node.left)
    return node
```

In `invert`, the right-hand side is evaluated completely before either attribute is assigned, so both recursive calls see the original children.

## Pitfalls

- **A walk inside the walk**: calling `height()` or `size()` from inside another recursive function multiplies the cost by the depth. Return the extra fact instead.
- **A base value that breaks the combine**: returning 0 for the maximum of an empty tree is wrong when values can be negative; use `float("-inf")`.
- **Sequential swap**: `node.left = invert(node.right)` followed by `node.right = invert(node.left)` reads the already-replaced left child, so both sides end up as the mirrored right subtree. Use one tuple assignment.
- **Short-circuit surprises**: `return f(node.left) and f(node.right)` skips the right call when the left is False. That is a useful early exit for pure functions and a bug if `f` also updates a counter.
- **Depth and height mixed up**: depth is a property of a node measured from above; height is a property of a subtree measured from below. Only height is a bottom-up quantity.

## Check yourself

Q: Run `height` on the tree `[1, 2, 3, 4, 5, None, 6]`. What does each call return?
A: The leaves 4, 5 and 6 return 1 (both children 0). Node 2 returns 1 + max(1, 1) = 2. Node 3 returns 1 + max(0, 1) = 2. The root returns 1 + max(2, 2) = 3.

Q: Why is it correct for `is_balanced`'s helper to return -1 without even visiting the right subtree when the left reports -1?
A: The contract says -1 means "unbalanced somewhere in this subtree". If the left subtree is unbalanced, the node's subtree contains that unbalanced node too, so -1 is the correct answer for the node whatever the right subtree looks like. Skipping the right call only saves work.

Q: Design the contract for "the largest absolute difference between a node's value and the value of any of its descendants". What does each call return, and where is the answer formed?
A: Let f(node) return the (minimum, maximum) of the subtree. At each node with children, the best difference involving that node as the ancestor is `max(abs(val - lo), abs(val - hi))` over the children's combined minimum and maximum; record the largest such value in an outer variable, and return `(min(val, lo), max(val, hi))` upward. An empty child contributes (inf, -inf). Everything is computed in one O(n) post-order pass.

Q: This invert passes on a single node but fails on `[1, 2, 3]`: `node.left = invert(node.right)` then `node.right = invert(node.left)`. What does it return for that tree, and why?
A: It returns 1 with 3 on both sides, `[1, 3, 3]`. The first line sets `node.left` to the subtree 3. The second line then inverts `node.left`, which is now 3, not 2, so the right child also becomes 3 and node 2 is lost. Evaluate both calls before assigning: `node.left, node.right = invert(node.right), invert(node.left)`.

## Lab

- **104**: maximum depth with the `height` template. Expected: 3 for `[1, 2, 3, 4, 5, None, 6]`, 4 for `[1, 2, 3, 4, None, None, None, 5]`, and 0 for an empty tree; O(n) time, O(h) space.
- **110**: height-balanced check with the -1 sentinel. Expected: True for `[1, 2, 3, 4, 5, None, 6]`, False for `[1, 2, 3, 4, None, None, None, 5]` (node 2 has subtree heights 2 and 0), True for an empty tree; O(n) time and O(h) space, with no second height walk.

> [!know]
> You now know how to solve a tree problem bottom-up by fixing what each call returns, and how to strengthen that return value instead of re-walking subtrees.

=== primer | When should information flow down a tree instead of up? | 16 min
goal: Carry path state (depth, running maximum, running sum, the path itself) down as arguments, combine it with returned counts, and undo shared state on the way back
tag: trees-down | Pass path state down the tree
link: Composing Programs, 2.3.6 Trees | https://composingprograms.com/pages/23-sequences.html#trees | 10 min: section 2.3.6, especially print_parts at the end, which passes the partial answer down as an argument while it explores the tree
practice: 1448, 437

> [!key]
> When a node's answer depends on its **ancestors** (its depth, the largest value above it, the sum of the path from the root), pass that fact down as an **argument**: each call receives what the path above knows and hands an updated copy to its children. Immutable arguments (numbers, tuples) undo themselves when the call returns; shared mutable state (a path list, a counter of prefix sums) must be undone explicitly on the way back up.

## Intuition

Walk down a mountain trail and keep a note of the highest point you have passed. At each viewpoint you can tell immediately whether it is the highest so far, using only your note. Your note is the argument. When the trail forks, you give each branch its own copy of the note; returning to the fork, you are back to the note you had there, because the branches never wrote on yours.

Compare this with the previous card. There, a node waited for its children to report (information up). Here, a node is told by its parent (information down). The two are often combined: the argument goes down, a count comes back up.

## How it works

### The template: state in, answer out

```text
walk(node, state):
    if node is None: return the neutral answer
    look at node using state          (is it good? does a path end here?)
    new_state = update(state, node)   (what the children will be told)
    return combine(here, walk(left, new_state), walk(right, new_state))
```

Typical states and what they solve:

| State passed down | Update | Solves |
|---|---|---|
| depth | depth + 1 | depth of every node, nodes at depth k |
| largest value on the path | max(best, val) | "good" nodes (no larger ancestor) |
| sum of the root path | running + val | root-to-leaf path sum |
| number spelled by the path | number * 10 + val | sum of root-to-leaf numbers |
| allowed range (low, high) | narrow at each step | validating a binary search tree (next module) |
| the path itself (a list) | append, recurse, pop | listing all root-to-leaf paths |

### Two directions in one problem

Counting good nodes uses both: the largest value so far flows down, and each call returns how many good nodes its subtree has. Most "count the nodes such that..." problems look like this.

### Paths that start anywhere: prefix sums along the root path

Counting downward paths with a given sum, starting at any node and ending at any node below it, looks hard: there are O(n h) such paths. Pass the running root-path sum down and keep a counter of the prefix sums on the **current** root path. A downward path ending at the current node with sum `target` exists for every ancestor-prefix equal to `running - target`, exactly like counting subarrays with a given sum in an array (the prefix sums module). The tree twist: when the call returns, the current prefix must be removed from the counter, otherwise a sibling branch would pair with it and count a path that goes up and then down.

## Cost

Every pattern here is one pass: **O(n) time**, **O(h) stack**. The prefix counter adds O(1) expected work per node for its dictionary operations, so the path-sum count is O(n) instead of the O(n h) brute force that starts a walk at every node. The counter only ever holds counts for the current root path, though `Counter` keeps keys that dropped to zero; delete them if memory matters.

Watch out for hidden copies: building `path + [node.val]` at every step copies the path, costing O(n h) in total, and copying `path[:]` is only acceptable at the leaves where you actually store it.

## When to use it

| The answer at a node depends on | Direction | Mechanism |
|---|---|---|
| its ancestors or the path from the root | down | argument |
| its descendants | up | return value |
| both | both | argument in, count or result out |
| a path anywhere in the tree | up, plus a global best | next card |

Cues: "path from the root", "ancestor", "so far", "at depth", "root-to-leaf". Not the right tool if a fact needs the whole subtree (sizes, heights): those must flow up, because a parent cannot know them before its children are processed.

## Worked trace

Count good nodes (no ancestor has a larger value) in `[5, 3, 8, 6, 2, None, 7]`:

```text
          5
         / \
        3   8
       / \    \
      6   2    7
```

```steps
walk(5, best=-inf): nothing is above the root, so 5 is good. Its children will be told best = 5
    stack  {{walk(5, -inf)}}
    good   5
---
walk(3, best=5): 3 < 5, not good. Children are told max(5, 3) = 5
    stack  walk(5, -inf) > {{walk(3, 5)}}
    good   5
---
walk(6, best=5): 6 >= 5, good. Its empty children return 0, so this call returns 1
    stack  walk(5, -inf) > walk(3, 5) > {{walk(6, 5)}}
    good   5 {{6}}
---
walk(2, best=5): 2 < 5, not good; returns 0. walk(3) now returns 0 + 1 + 0 = 1
    stack  walk(5, -inf) > walk(3, 5) > {{walk(2, 5)}}
    good   5 6
---
walk(8, best=5): good. Its child is told best = 8; note it was never told about 3 or 6, which are not its ancestors
    stack  walk(5, -inf) > {{walk(8, 5)}}
    good   5 6 {{8}}
---
walk(7, best=8): 7 < 8, not good. walk(8) returns 1, and walk(5) returns 1 + 1 + 1 = 3
    stack  walk(5, -inf) > walk(8, 5) > {{walk(7, 8)}}
    good   5 6 8   (answer 3)
```

## Template

```python
from collections import Counter


def good_nodes(root):
    """Count nodes whose value is >= every value on the path above them."""
    def walk(node, best):                     # best: largest value above node
        if node is None:
            return 0
        good = 1 if node.val >= best else 0
        best = max(best, node.val)            # what the children are told
        return good + walk(node.left, best) + walk(node.right, best)

    return walk(root, float("-inf"))


def count_paths_with_sum(root, target):
    """Number of downward paths (any start, any end) whose values sum to target."""
    seen = Counter({0: 1})                    # prefix sums on the current root path

    def walk(node, running):
        if node is None:
            return 0
        running += node.val
        found = seen[running - target]        # paths that end at this node
        seen[running] += 1
        found += walk(node.left, running) + walk(node.right, running)
        seen[running] -= 1                    # leaving this node: undo
        return found

    return walk(root, 0)


def root_to_leaf_paths(root):
    """Every root-to-leaf path as a list of values."""
    paths, path = [], []

    def walk(node):
        if node is None:
            return
        path.append(node.val)
        if node.left is None and node.right is None:
            paths.append(path[:])             # copy: path keeps changing
        walk(node.left)
        walk(node.right)
        path.pop()                            # undo before returning

    walk(root)
    return paths
```

In `count_paths_with_sum` the lookup happens before the current prefix is added, so a path is never empty, even when `target` is 0.

## Pitfalls

- **Forgetting to undo shared state**: without `path.pop()` or `seen[running] -= 1`, state from a finished branch leaks into its sibling.
- **Forgetting the seed**: without `Counter({0: 1})`, paths that start at the root are never counted.
- **Storing the live list**: `paths.append(path)` stores a reference, and every stored path ends up empty after the walk. Copy at the leaf.
- **Leaf tests**: a leaf has *both* children None. "Root-to-leaf" problems go wrong when a node with one child is treated as a leaf, or when the empty tree is counted as a path with sum 0.
- **Rebinding in a closure**: assigning to an outer variable inside the nested function needs `nonlocal`. Passing state as an argument avoids that and makes the undo automatic.

## Check yourself

Q: Trace `count_paths_with_sum` on the chain 1 -> 2 -> 3 (1 is the root, each node the left child of the previous) with target 3. What does `seen` contain at node 3, and what is the answer?
A: Running sums are 1, 3 and 6. At node 2 (running 3), `seen` holds {0: 1, 1: 1} and `seen[3 - 3] = seen[0] = 1`: the path 1, 2. At node 3 (running 6), `seen` holds {0: 1, 1: 1, 3: 1} and `seen[6 - 3] = 1`: the path 3 alone. The answer is 2.

Q: Why must `seen[running]` be decremented when a call returns? Give a tree where skipping it gives a wrong count.
A: The counter must describe only the ancestors of the current node; a prefix left behind by a finished branch belongs to a node that is not an ancestor, so pairing with it counts a "path" that climbs up and comes back down. Take `[1, 2, 3]` with target 1: the only answer is the root alone, so the count is 1. Without the undo, the prefix 3 from node 2 is still in `seen` when node 3 is visited (running sum 4), and `seen[4 - 1]` adds a bogus path, giving 2.

Q: For each, which direction does the information flow: (a) the depth of every node, (b) the number of leaves below each node, (c) whether each node's value equals the sum of all its ancestors?
A: (a) Down: depth comes from the parent's depth plus one. (b) Up: a node's leaf count is the sum of its children's. (c) Down: pass the ancestor sum as an argument and compare at each node.

Q: Adapt the template to "sum of all numbers spelled by root-to-leaf paths", where the path 4, 9, 5 spells 495.
A: Pass `number = number * 10 + node.val` down. At a leaf, return that number; otherwise return the sum of the two child calls; an empty child returns 0. For `[3, 1, 4, 2, 5]` the paths spell 312, 315 and 34, so the answer is 661. One pass, O(n) time, O(h) space.

## Lab

- **1448**: count good nodes with the `best` argument. Expected: 3 for `[5, 3, 8, 6, 2, None, 7]` (the nodes 5, 6 and 8), 1 for a single node, and 4 for `[2, 2, 2, 2]` (equal values count as good); O(n) time, O(h) space.
- **437**: count downward paths with the prefix counter. Expected: for `[2, 1, 3, 1, None, -1, 4]`, target 4 gives 3 (the paths 2-1-1, 2-3-(-1) and 4) and target 3 gives 2 (2-1 and 3); O(n) time. Check it against a brute force that starts a walk from every node.

> [!know]
> You now know how to pass path state down a tree, combine it with values returned up, and undo shared state so sibling branches never see each other.

=== primer | How do you find the best path when it does not have to pass through the root? | 16 min
goal: Compute the diameter and the maximum path sum in one pass by separating what a node returns to its parent from the candidate it records globally
tag: trees-global | Global best from local work
link: USACO Guide, DP on Trees | https://usaco.guide/gold/dp-trees#tutorial | 10 min: the "Tutorial" section: every node returns a small summary computed from its children's summaries, the general form of the pattern in this card
practice: 543, 124

> [!key]
> Every path in a tree has exactly one **highest node**, where it bends. So try every node as the bend: there, the best path is the best downward arm into the left subtree plus the node plus the best downward arm into the right subtree. Each call **returns** only a one-armed path (the only shape its parent can extend) and **records** the two-armed candidate in a global best. One post-order pass, O(n).

## Intuition

Lay a string along the longest route through a tree of roads. Pick it up by its highest point and it hangs down in at most two strands, one into each side. Conversely, any node with its two longest strands hanging down is a candidate route. If every node reports "the longest strand that hangs below me" to its parent, each node can form its own candidate (left strand + right strand) and pass up only the longer strand plus itself, because a parent's route can continue through the node into one side only. A route that went into both sides and then up to the parent would visit the node twice: that is a fork, not a path.

## How it works

### Two numbers per node, with different jobs

| Quantity | Shape | Who uses it |
|---|---|---|
| returned value | best path going **down** from the node through at most one child | the parent, to extend |
| candidate | best path whose **highest node** is this one, using up to two children | the global answer only |

The answer is the maximum candidate over all nodes, and it is correct because the bend of the optimal path is some node, and at that node the candidate is exactly the optimal path (its two arms are the best arms, or the path could be improved).

### Diameter (longest path, counted in edges)

Let the call return the height of the subtree in nodes (0 for empty). At a node with child heights L and R, the longest path bending here has L + R edges: L edges down into the left subtree to its deepest node, R into the right. Record `best = max(best, L + R)` and return `1 + max(L, R)`.

On `[1, 2, 3, 4, 5, None, 6]`: the leaves return 1 and record 0; node 2 records 1 + 1 = 2 and returns 2; node 3 records 0 + 1 = 1 and returns 2; the root records 2 + 2 = 4. The diameter is 4, the path 4-2-1-3-6.

### Maximum path sum (values can be negative)

Now the arms have weights. Let `gain(node)` be the best sum of a downward path starting at node. An arm with negative gain should be dropped, so clip it: `l = max(gain(left), 0)` and `r = max(gain(right), 0)`. Record `node.val + l + r` and return `node.val + max(l, r)`. The node itself is always included, so the answer for an all-negative tree is its largest single value, which is why `best` must start at negative infinity, not 0.

## Cost

One post-order pass: each node does O(1) work after its two calls, so **O(n) time** and **O(h) stack**. The brute force tries every pair of nodes as endpoints, finds the path between them and sums it: O(n^2) pairs times O(h) per path. The bend argument collapses all pairs that share a highest node into one O(1) step at that node.

## When to use it

Cues: "any path", "between any two nodes", "the path may or may not pass through the root", "longest" or "maximum" over paths. The same split (return a one-sided summary, record a two-sided candidate) solves the longest path of equal values, the longest zigzag, and many tree DP problems; the advanced DP module extends it to nodes that return small tables (for example "best with this node taken / not taken").

If the path must start at the root or end at a leaf, you do not need the global: return values (or arguments passed down) are enough. If the question is about distances between many specified pairs of nodes, use lowest common ancestors instead (next card).

## Worked trace

`gain` on `[-3, 4, 10, None, None, -6, 8]`:

```text
          -3
         /  \
        4    10
            /  \
          -6    8
```

```steps
gain(4): a leaf, both arms are 0. Candidate 4 + 0 + 0 = 4, so best = 4. Return 4 + max(0, 0) = 4
    node   returns  candidate  best
    4      {{4}}        {{4}}          {{4}}
---
gain(-6): a leaf with a negative value. Candidate -6 does not beat 4. Return -6 (the parent will clip it)
    node   returns  candidate  best
    4      4        4          4
    -6     {{-6}}       {{-6}}         4
---
gain(8): a leaf. Candidate 8 beats 4, so best = 8. Return 8
    node   returns  candidate  best
    -6     -6       -6         4
    8      {{8}}        {{8}}          {{8}}
---
gain(10): l = max(-6, 0) = 0 (the negative arm is dropped), r = 8. Candidate 10 + 0 + 8 = 18, best = 18. Return 10 + max(0, 8) = 18
    node   returns  candidate  best
    8      8        8          8
    10     {{18}}       {{18}}         {{18}}
---
gain(-3): l = 4, r = 18. Candidate -3 + 4 + 18 = 19, best = 19. It returns 15, which nobody uses
    node   returns  candidate  best
    10     18       18         18
    -3     {{15}}       {{19}}         {{19}}
---
The answer is best = 19: the path 4, -3, 10, 8 bends at the root. The -6 was left out because its arm was clipped to 0
    answer {{19}}
```

## Template

```python
def diameter(root):
    """Edges on the longest path between any two nodes."""
    best = 0

    def height(node):                 # returns: nodes on the longest downward path
        nonlocal best
        if node is None:
            return 0
        left, right = height(node.left), height(node.right)
        best = max(best, left + right)     # records: longest path bending here
        return 1 + max(left, right)

    height(root)
    return best


def max_path_sum(root):
    """Largest sum of values on any non-empty path."""
    best = float("-inf")

    def gain(node):                   # returns: best downward path starting at node
        nonlocal best
        if node is None:
            return 0
        left = max(gain(node.left), 0)     # drop arms that only lose value
        right = max(gain(node.right), 0)
        best = max(best, node.val + left + right)   # records: best path bending here
        return node.val + max(left, right)

    gain(root)
    return best
```

`nonlocal best` lets the nested function rebind the outer variable. Without it, the assignment would make `best` local and the first read would raise `UnboundLocalError`.

## Pitfalls

- **Returning the two-armed value**: `return node.val + left + right` lets a parent extend a path that already uses both children of the node: a fork. The answer comes out too large.
- **Starting best at 0** for path sums: on `[-3]` the answer is -3, not 0. Start at negative infinity (or `root.val`).
- **Not clipping negative arms**: then the path is forced to include a losing subtree. Clip with `max(gain, 0)`, but never clip the node's own value.
- **Edges versus nodes**: diameter is usually measured in edges. If your helper returns heights in nodes, `left + right` is already in edges; adding 1 counts nodes.
- **State that outlives the call**: a module-level or class-level `best` that is not reset carries the previous test case's answer into the next one. Keep it local to the outer function.

## Check yourself

Q: Run `diameter` on the chain `[1, 2, None, 3, None, 4]` (each node the left child of the previous). What does each call return and record?
A: Node 4 returns 1 and records 0; node 3 returns 2 and records 1 + 0 = 1; node 2 returns 3 and records 2; node 1 returns 4 and records 3. The diameter is 3 edges, from 1 to 4.

Q: Why is it enough to consider, at each node, only paths whose highest node is that node?
A: Every path has a unique node closest to the root (its highest node), because the path goes up to it and then down. So the set of all paths is partitioned by highest node, and taking the best candidate at each node and then the best over all nodes covers every path exactly once. At a fixed highest node the best path uses the best arm on each side, which the children's returned values provide.

Q: A buggy version returns `node.val + left + right`. On `[1, 2, None, 3, 4]` (2 is the left child of 1, and 3 and 4 are the children of 2), what does it output, and what is correct?
A: The correct answer is 9, the path 3, 2, 4. The buggy `gain(2)` returns 2 + 3 + 4 = 9 to the root, which then records 1 + 9 + 0 = 10, a path that would have to visit 2 twice. It outputs 10.

Q: Adapt the pattern to "the longest path (in edges) on which every node has the same value".
A: Let the call return the longest one-armed same-value chain going down from the node, in edges. For each child, the arm is `child_result + 1` if the child exists and has the same value as the node, else 0. Record `left_arm + right_arm`, return `max(left_arm, right_arm)`. One O(n) pass, global best starting at 0.

## Lab

- **543**: diameter with the `height` helper. Expected: 4 for `[1, 2, 3, 4, 5, None, 6]`, 3 for the chain `[1, 2, None, 3, None, 4]`, 0 for a single node; O(n) time, O(h) space.
- **124**: maximum path sum with clipped arms. Expected: 19 for `[-3, 4, 10, None, None, -6, 8]`, -3 for `[-3]`, 9 for `[1, 2, None, 3, 4]`, and 2 for `[2, -1]`; O(n) time. Compare against an all-pairs brute force on random small trees with negative values.

> [!know]
> You now know how to find the best path anywhere in a tree by returning one-armed answers and recording two-armed candidates at each node.

=== primer | How do you find the lowest common ancestor of two nodes? | 15 min
goal: Find the lowest common ancestor with one recursive pass or with parent pointers, and use a parent map to treat a tree as an undirected graph
tag: trees-lca | Lowest common ancestor and parent maps
link: cp-algorithms, LCA with binary lifting | https://cp-algorithms.com/graph/lca_binary_lifting.html#algorithm | 10 min, optional: the "Algorithm" section: store every node's 2^k-th ancestor so that each of many LCA queries takes O(log n)
link: Git docs, git merge-base | https://git-scm.com/docs/git-merge-base#_description | 3 min: the Description: a merge base is a best common ancestor of two commits, the same idea on a commit graph
practice: 236, 863

> [!key]
> The **lowest common ancestor** (LCA) of p and q is the deepest node that has both in its subtree (a node counts as its own ancestor). One post-order pass finds it: each call returns p or q if it finds one in its subtree, the LCA if it finds both, and None otherwise; the first node that hears back from both sides is the answer. With parent pointers, walk up from p collecting ancestors, then walk up from q until you hit one.

## Intuition

Two employees want to know the most junior manager they both report to, directly or indirectly. One way: the first employee lists her whole management chain up to the CEO; the second walks up his chain until he meets a name on her list. That is the parent-pointer method.

The other way starts at the top: the CEO asks each division "is either of them in your division?" If both divisions say yes, the CEO is the answer. If only one says yes, the answer is inside that division, so the CEO simply passes its reply up. That is the recursive method, and it is just the bottom-up pattern with a clever return value.

## How it works

### One pass from the root

Contract: `lca(node)` returns p or q if exactly one of them is in node's subtree, the LCA if both are, and None if neither is (assuming both are in the tree). Cases at a node:

1. node is None, p or q: return node. If node is p, any q below it would make p the LCA anyway, so there is no need to look further.
2. Ask both children.
3. Both answers non-None: p is on one side and q on the other, so this node is the lowest point that sees both: return it.
4. Otherwise return whichever answer is non-None (or None). Once the true LCA is found, it is the only non-None value on its side all the way up, so it is passed to the root unchanged.

### Parent pointers

If each node knows its parent (or you build a `parent` dictionary in one O(n) traversal), an LCA query needs no search from the root: collect p's ancestors in a set, then walk up from q until the current node is in the set. That is O(h) time per query and O(h) extra memory. Equalising depths first (move the deeper node up until both have the same depth, then move both up together until they meet) needs O(1) extra memory, exactly like finding where two linked lists merge.

### A tree is also a graph

The parent map gives every node up to three neighbours: left, right and parent. With it, "all nodes at distance k from a target" is just breadth-first search from the target for k rounds, with a visited set so you do not walk back the way you came. "Distance between p and q" is depth(p) + depth(q) - 2 depth(lca).

### Many queries

For 10^5 queries on a 10^5-node tree, neither method is fast enough per query on a deep tree. Binary lifting stores each node's 2^k-th ancestor for every k (O(n log n) preprocessing) and answers each query in O(log n). In a binary search tree you do not need any of this: the values tell you which side p and q are on (next module).

## Cost

The recursive version visits each node at most once: **O(n) time, O(h) stack** per query. Building a parent map is O(n) once; each parent-pointer query is then O(h). The distance-k search is O(n): the parent map plus a BFS that visits each node at most once.

## When to use it

Cues: "lowest common ancestor", "common manager", "closest shared folder", "distance between two nodes", "path from one node to another" (the path goes up to the LCA and down again), and version control: Git's merge base of two branches is a best common ancestor in the commit graph, computed so a three-way merge can compare both sides with their shared starting point.

| Situation | Method | Cost |
|---|---|---|
| One query, child pointers only | recursive pass | O(n) |
| Parent pointers available, few queries | ancestor set or depth equalising | O(h) each |
| Many queries on a static tree | binary lifting | O(n log n) build, O(log n) each |
| Binary search tree | follow the values from the root | O(h) each |

## Worked trace

`lca(root, p=5, q=6)` on `[1, 2, 3, 4, 5, None, 6]`:

```steps
lca(1): 1 is neither p nor q, so it asks its left child, which asks its left child: lca(4)
    stack     lca(1) > lca(2) > {{lca(4)}}
    returned  (none yet)
---
lca(4): not p or q, and both of its children return None, so it returns None
    stack     lca(1) > lca(2)
    returned  4 -> {{None}}
---
lca(5): 5 is p, so it returns itself at once without looking below
    stack     lca(1) > lca(2)
    returned  4 -> None, 5 -> {{5}}
---
lca(2): left None, right 5. Only one side found something, so 2 passes 5 up
    stack     lca(1)
    returned  4 -> None, 5 -> 5, 2 -> {{5}}
---
lca(3): its left child is None; lca(6) returns 6 because 6 is q. One side found something: 3 passes 6 up
    stack     lca(1)
    returned  2 -> 5, 6 -> 6, 3 -> {{6}}
---
lca(1): left returned 5 and right returned 6, so p and q are on different sides. The answer is 1
    stack     (empty)
    returned  2 -> 5, 3 -> 6, 1 -> {{1}}
```

For p = 2 and q = 5 the walk stops at node 2 (it is p) and returns 2 without visiting 4 or 5; the right side returns None, so the answer is 2, which is correct because 5 is below 2.

## Template

```python
from collections import deque


def lowest_common_ancestor(root, p, q):
    """LCA of nodes p and q, both assumed to be in the tree."""
    if root is None or root is p or root is q:
        return root
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    if left and right:              # p and q are on different sides
        return root
    return left or right            # both on one side, or neither


def parent_map(root):
    """Map each node to its parent (the root maps to None)."""
    parent, stack = {root: None}, [root]
    while stack:
        node = stack.pop()
        for child in (node.left, node.right):
            if child:
                parent[child] = node
                stack.append(child)
    return parent


def lca_with_parents(p, q, parent):
    ancestors = set()
    while p:
        ancestors.add(p)
        p = parent[p]
    while q not in ancestors:
        q = parent[q]
    return q


def nodes_at_distance(root, target, k):
    """Values of all nodes exactly k edges away from target."""
    parent = parent_map(root)
    seen, frontier = {target}, deque([target])
    for _ in range(k):
        for _ in range(len(frontier)):
            node = frontier.popleft()
            for nxt in (node.left, node.right, parent[node]):
                if nxt and nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
    return [node.val for node in frontier]
```

Nodes are compared with `is` and used as dictionary keys by identity (the default for objects without `__eq__`), so duplicate values are harmless.

## Pitfalls

- **A node that is not in the tree**: the one-pass version assumes both exist. If q is missing, it returns p, which is wrong. When existence is not guaranteed, count how many of p and q were actually found during the walk.
- **Comparing values instead of nodes**: with duplicate values, `node.val == p.val` matches the wrong node. Compare identities.
- **Many queries, one pass each**: 10^5 queries of O(n) each is 10^10 steps. Switch to parent pointers with depths, or binary lifting.
- **Walking back into visited nodes**: in the distance-k search the parent link makes the tree an undirected graph, so a visited set is mandatory, or the search bounces between a node and its parent.
- **Deep trees**: on a chain, the recursive version hits Python's recursion limit; build the parent map iteratively (as `parent_map` does) and use the parent-pointer query.

## Check yourself

Q: On `[1, 2, 3, 4, 5, None, 6]`, what does `lca(2)` return when p = 4 and q = 6, and what is the final answer?
A: `lca(2)` returns 4: its left call finds 4 (which is p) and its right call (node 5) returns None. `lca(3)` returns 6. The root receives 4 from the left and 6 from the right, so the answer is 1.

Q: Why is it safe to return p immediately when the walk reaches p, without checking whether q is below it?
A: Either q is below p, in which case p is the LCA and returning it is right, or q is elsewhere, in which case some ancestor of p will also receive q from its other side and become the answer, and p's reply only says "one of them is here". In both cases the contract (return p, q or the LCA, whichever applies) is satisfied, and the guarantee that both nodes exist removes the need to search further.

Q: How do you compute the number of edges between nodes p and q in a tree you will query 10^5 times?
A: Precompute every node's depth and parent once (O(n)), then answer each query as depth(p) + depth(q) - 2 * depth(lca(p, q)). For deep trees, use binary lifting so each LCA costs O(log n) instead of O(h).

Q: A function finds all nodes at distance k from a target with BFS over left, right and parent, but without a visited set. What goes wrong for target 2, k = 2 on `[1, 2, 3, 4, 5, None, 6]`?
A: In round 1 it reaches 4, 5 and 1. In round 2, 4 and 5 step back to their parent 2 (twice), and 1 steps to 2 and to 3. The answer comes out as 2, 2, 2 and 3 instead of just 3: the target itself is reported several times because the search walked back the way it came.

## Lab

- **236**: one-pass LCA. Expected on `[1, 2, 3, 4, 5, None, 6]`: p = 5, q = 6 gives 1; p = 2, q = 5 gives 2; p = 4, q = 5 gives 2; O(n) time, O(h) space. Check it against a brute force that compares the two root-to-node paths.
- **863**: parent map plus BFS. Expected on the same tree with target 2: k = 1 gives 4, 5 and 1 (any order); k = 2 gives 3; k = 3 gives 6; k = 4 gives an empty list; O(n) time and space.

> [!know]
> You now know how to find lowest common ancestors with one pass or parent pointers, and how a parent map turns a tree into a graph you can search in any direction.

=== primer | How do you rebuild a tree from its traversals, and turn it into a string and back? | 15 min
goal: Rebuild a tree from pre-order and in-order lists in O(n), know which traversal pairs are ambiguous, and serialise and deserialise any tree with one pre-order walk
tag: trees-build | Build and serialise trees
link: Wikipedia, Tree traversal | https://en.wikipedia.org/wiki/Tree_traversal#Applications | 3 min: the "Applications" section: pre-order copies a tree and writes prefix expressions, post-order writes postfix and deletes, in-order lists a search tree in order
practice: 105, 297

> [!key]
> A traversal list alone loses the shape, but two can restore it: **pre-order names the root, in-order splits left from right**, so with distinct values pre-order plus in-order determines the tree. To store a tree, one pre-order walk is enough if you also write a **marker for every missing child**; reading the tokens back in the same order rebuilds it. Both directions are O(n) with an index map and an iterator.

## Intuition

The list `1, 2` in pre-order could be a root 1 with 2 on the left or on the right; the shape is gone. In-order alone fails too: `2, 1` could be 2 above 1 or 1 above 2. Each list keeps a different half of the information. Pre-order tells you, at every step, *which node is the root* of the subtree being built; in-order tells you *how many nodes fall on each side* of it. Together they leave no choice.

Serialisation solves the same problem differently: instead of a second list, write down the gaps. In `1,2,#,#,3,#,#`, after reading 2 you know it is a leaf (two markers follow), so 3 must be the root's right child. HTML does the same with closing tags: an element's opening tag is written at its pre-order moment and its closing tag at its post-order moment, which is why a page can be parsed back into the same DOM tree.

## How it works

### Pre-order plus in-order

1. Map each value to its in-order index (values must be distinct).
2. Consume pre-order left to right with an iterator. The next value is the root of the subtree you are building.
3. Build the subtree whose values are `inorder[lo:hi]`: take the next pre-order value as root, find its index `mid`, build the left subtree from `inorder[lo:mid]`, then the right from `inorder[mid + 1:hi]`. Left before right, because that is the order pre-order lists them.
4. An empty range means an empty subtree.

Post-order plus in-order works the same way from the other end: consume post-order backwards (root last) and build the **right** subtree first. Pre-order plus post-order is **not** enough in general: a root 1 with a single child 2 has pre-order `1, 2` and post-order `2, 1` whether 2 is the left or the right child. It is unique only for full binary trees (every node has 0 or 2 children).

### Serialise with markers

Pre-order, writing `#` for every empty child. Deserialise with the same recursion: read a token; `#` means None; otherwise make a node and read its left subtree, then its right subtree, from the same token stream. Correctness is an induction on the token list: the serialisation of a subtree is a contiguous block that the reader consumes exactly, so after reading the left subtree the stream is positioned at the start of the right one.

Level order with `None` gaps (the LeetCode format from the BFS card) is an equally valid serialisation. It is more readable for wide shallow trees and avoids deep recursion; pre-order with markers streams naturally and is easier to code.

### Using serialisation for comparison

Two subtrees are identical exactly when their marker serialisations are equal strings, so serialising every subtree in post-order and counting the strings in a dictionary finds duplicate subtrees. Strings get long, so production versions map each distinct subtree to a small integer id and serialise as `(left id, value, right id)`.

## Cost

With the index map, each node is created once with an O(1) lookup: **O(n) time**, O(n) for the map, O(h) stack. The textbook version that slices lists and calls `inorder.index(root)` at every level is O(n^2) on a chain: each level searches and copies an O(n) list.

Serialising writes 2n + 1 tokens (n values and n + 1 markers), O(n) time with `",".join`. Deserialising reads each token once: O(n).

## When to use it

- The input is given as traversals (rebuild), or you must store, send, cache or hash a tree (serialise).
- You need to compare or deduplicate subtrees (serialise each one, or give each an id).
- Copying a tree: a pre-order walk that creates each node before its children.

Do not rebuild from pre-order and post-order unless the tree is guaranteed full, and do not use the index map when values repeat: then the split point is ambiguous and the input may not determine a unique tree at all.

## Worked trace

Rebuild from pre-order `[1, 2, 4, 5, 3, 6]` and in-order `[4, 2, 5, 1, 3, 6]`. Brackets mark the in-order range of the subtree being built:

```steps
build(0, 6): the next pre-order value 1 is the root. Its in-order index is 3, so [4 2 5] is its left subtree and [3 6] its right
    pre   {{1}} 2 4 5 3 6
    in    [4 2 5] {{1}} [3 6]
---
build(0, 3): the next pre-order value 2 roots the left subtree. Index 1 splits the range into [4] and [5]
    pre   1 {{2}} 4 5 3 6
    in    [4] {{2}} [5] 1 3 6
---
build(0, 1): the next value 4 has index 0. Both sub-ranges are empty, so 4 is a leaf
    pre   1 2 {{4}} 5 3 6
    in    {{4}} 2 5 1 3 6
---
build(2, 3): the next value 5 is also a leaf. The left subtree of 1 is complete
    pre   1 2 4 {{5}} 3 6
    in    4 2 {{5}} 1 3 6
---
build(4, 6): the next value 3 roots the right subtree. Index 4: its left range is empty, its right range is [6]
    pre   1 2 4 5 {{3}} 6
    in    4 2 5 1 {{3}} [6]
---
build(5, 6): 6 is a leaf. Every pre-order value was consumed exactly once, and the tree is [1, 2, 3, 4, 5, None, 6]
    pre   1 2 4 5 3 {{6}}
    in    4 2 5 1 3 {{6}}
```

## Template

```python
def build_from_pre_in(preorder, inorder):
    """Rebuild a tree with distinct values from its pre-order and in-order lists."""
    where = {v: i for i, v in enumerate(inorder)}
    next_root = iter(preorder)

    def build(lo, hi):                  # the subtree whose values are inorder[lo:hi]
        if lo >= hi:
            return None
        node = TreeNode(next(next_root))
        mid = where[node.val]
        node.left = build(lo, mid)      # left first: pre-order lists it first
        node.right = build(mid + 1, hi)
        return node

    return build(0, len(inorder))


def serialise(root):
    """Pre-order with '#' for every missing child, e.g. '1,2,#,#,3,#,#'."""
    out = []

    def walk(node):
        if node is None:
            out.append("#")
            return
        out.append(str(node.val))
        walk(node.left)
        walk(node.right)

    walk(root)
    return ",".join(out)


def deserialise(data):
    """Inverse of serialise."""
    tokens = iter(data.split(","))

    def walk():
        token = next(tokens)
        if token == "#":
            return None
        node = TreeNode(int(token))
        node.left = walk()
        node.right = walk()
        return node

    return walk()


tree = build_from_pre_in([1, 2, 4, 5, 3, 6], [4, 2, 5, 1, 3, 6])
print(serialise(tree))                    # 1,2,4,#,#,5,#,#,3,#,6,#,#
print(serialise(deserialise("#")))        # #
```

## Pitfalls

- **Right before left**: with pre-order, building `node.right` first assigns the left subtree's values to the right side. (With post-order consumed backwards, it is the other way round.)
- **Duplicate values** break the index map silently: the tree comes back with the wrong shape and no error.
- **No separator**: concatenating `"1" + "23"` and `"12" + "3"` gives the same string. Always separate tokens; a comma also keeps negative numbers like `-7` intact.
- **No markers**: a pre-order list without markers cannot be deserialised; you would need a second traversal.
- **Slicing**: `build(preorder[1:k], inorder[:m])` style code is easy to write and O(n^2) on skewed trees. Pass indices.
- **Deep inputs**: both recursions are as deep as the tree. For long chains, serialise in level order with a queue or use an explicit stack.

## Check yourself

Q: Draw the tree for pre-order `[1, 2, 3]` and in-order `[2, 1, 3]`, and write its serialisation.
A: 1 is the root; in in-order, 2 is to its left and 3 to its right, so both are leaves: `[1, 2, 3]`. The serialisation is `1,2,#,#,3,#,#`.

Q: Why does reading the tokens in pre-order rebuild exactly the original tree?
A: By induction on the tree: the serialisation of an empty tree is the single token `#`, and that of a node is its value, then its left subtree's serialisation, then its right subtree's. The reader mirrors this: it reads a value, then calls itself for the left subtree, which (by the induction hypothesis) consumes exactly the left block and returns that subtree, leaving the stream at the start of the right block. So each recursive call consumes precisely its own block.

Q: Give two different trees with the same pre-order and the same post-order.
A: Root 1 with only a left child 2, and root 1 with only a right child 2. Both have pre-order `1, 2` and post-order `2, 1`. Pre-order and post-order never reveal on which side a single child hangs.

Q: Adapt `build_from_pre_in` to post-order plus in-order.
A: Iterate post-order from the end (`iter(reversed(postorder))`), because the root comes last; build `node.right = build(mid + 1, hi)` before `node.left = build(lo, mid)`, because reading post-order backwards yields root, then the right subtree, then the left. Everything else is unchanged.

## Lab

- **105**: rebuild with the index map and an iterator. Expected: pre-order `[1, 2, 4, 5, 3, 6]` with in-order `[4, 2, 5, 1, 3, 6]` gives `[1, 2, 3, 4, 5, None, 6]` in level order; a single value gives a single node; O(n) time. Test it by generating random trees with distinct values, computing their two traversals, rebuilding, and comparing.
- **297**: serialise and deserialise. Expected: `serialise` of `[1, 2, 3, 4, 5, None, 6]` is `1,2,4,#,#,5,#,#,3,#,6,#,#`, the empty tree is `#`, and `deserialise(serialise(t))` equals `t` for random trees, including negative and repeated values.

> [!know]
> You now know how to rebuild a tree from pre-order and in-order lists in O(n), which traversal pairs are ambiguous, and how to serialise any tree with markers.

=== primer | How do you traverse a tree without recursion, and when do you have to? | 15 min
goal: Replace the call stack with an explicit stack for pre-, in- and post-order, and know when Python's recursion limit forces you to
tag: trees-iter | Iterative traversal with an explicit stack
link: Wikipedia, Tree traversal | https://en.wikipedia.org/wiki/Tree_traversal#Implementations | 10 min: the iterative pre-order, in-order and post-order pseudocode under "Depth-first search implementation", then Morris in-order traversal, which needs no stack at all
link: Python docs, sys.setrecursionlimit | https://docs.python.org/3/library/sys.html#sys.setrecursionlimit | 2 min: why raising the limit is platform-dependent and can crash the interpreter
practice: 94, 104

> [!key]
> Recursion keeps its pending work on the call stack; you can keep the same work on a Python list instead. In-order: push the whole left spine, pop a node, emit it, then move to its right child. Pre-order: pop, emit, push right then left. Post-order: push each node twice, once to expand and once to emit. Same O(n) time and O(h) memory, but no recursion limit, and the walk can pause between values.

## Intuition

When you read a book with footnotes inside footnotes, you keep a finger in each page you left. The fingers are a stack: the most recent one is where you return to first. Recursion keeps those fingers for you, in interpreter frames. An explicit stack keeps them in a list you control. Nothing else changes: the order of work is identical if you push things in the right order.

Why bother? In CPython each recursive call uses a frame, and the interpreter stops at about 1000 nested calls (`sys.getrecursionlimit()` returns 1000 by default). A tree built by inserting sorted keys into a plain search tree, or any "linked list shaped" input, can be 10^4 to 10^5 levels deep. `sys.setrecursionlimit` raises the ceiling, but the real C stack may overflow first and kill the process without a Python exception. A list on the heap has no such limit.

## How it works

### Pre-order: the easy one

Pop a node, emit it, push its right child and then its left child. The left child is on top, so it is processed next, and the right child waits underneath until the whole left subtree is done: exactly the recursive order.

### In-order: walk the left spine

The recursive in-order cannot emit a node until its left subtree is finished. Simulate that:

1. From the current node, go left as far as possible, pushing every node on the way. These are nodes whose left subtrees are in progress.
2. Pop the top. Its left subtree is finished, so emit it.
3. Move to its right child and repeat from step 1.

The loop runs while there is a current node or something on the stack. **Invariant**: the stack holds exactly the ancestors of the current position whose own value has not been emitted yet, deepest on top.

### Post-order: push twice

A node must be emitted after both subtrees. Push `(node, False)` meaning "expand me". When popped, push `(node, True)` ("emit me") first, then the right child, then the left child, so they come off the stack left, right, then the node itself. This "push the steps in reverse" recipe produces any order: move the `(node, True)` push to change pre-, in- or post-order.

A popular shortcut computes the modified pre-order root, right, left and reverses the output. It gives the right list, but only at the end; it cannot emit nodes one by one in post-order, which matters for iterators and for freeing memory as you go.

### Iterators that pause

An explicit stack also lets a traversal stop in the middle and resume later. A generator with the in-order loop above yields one value at a time, and the next module's search-tree iterator is exactly this stack stored in an object. (A recursive generator with `yield from` also pauses, but every level of nesting is still a live frame, so it hits the same recursion limit.)

## Cost

Every node is pushed and popped once (twice in the post-order version), with O(1) work each: **O(n) time**. The stack holds at most one entry per level for pre-order and in-order, plus the pending right children or markers, which is **O(h)**: O(log n) for balanced trees and O(n) for chains, the same as recursion but on the heap.

In CPython the iterative and recursive versions are within a small constant factor of each other: a function call is relatively expensive, but so are the extra list operations and loop tests. Choose for depth and clarity, not for speed. Morris traversal (linked in the Go deeper notes) brings memory to O(1) by temporarily threading right pointers back to ancestors, at the cost of modifying the tree during the walk.

## When to use it

| Situation | Choose |
|---|---|
| The tree may be deeper than about 1000 levels in Python | explicit stack (or BFS if order does not matter) |
| You need to pause and resume (iterators, k-th element, early exit) | explicit stack |
| Balanced or small trees, clarity matters most | recursion |
| O(1) extra memory, and you may modify the tree temporarily | Morris traversal |

Tree problems on LeetCode often allow 10^4 nodes, and a skewed tree of that size is ten times deeper than CPython's default limit, so know the stack version even if a judge happens to raise the limit for you. In production code that walks user-supplied data (JSON, file systems, syntax trees), prefer the stack: CPython's own `os.walk` switched to an explicit stack in Python 3.12.

## Worked trace

Iterative in-order on `[1, 2, 3, 4, 5, None, 6]`:

```steps
node = 1. Walk down the left spine pushing 1, 2 and 4; then node is None
    stack  [1, 2, {{4}}]
    out    []
---
Pop 4, the leftmost unvisited node, and emit it. Its right child is None, so nothing is pushed
    stack  [1, 2]
    out    [{{4}}]
---
Pop 2 and emit it: its left subtree is finished. Move to its right child 5 and push its left spine (just 5)
    stack  [1, {{5}}]
    out    [4, {{2}}]
---
Pop 5 and emit it. It has no right child
    stack  [1]
    out    [4, 2, {{5}}]
---
Pop 1 and emit it. Move to its right child 3 and push it (3 has no left child)
    stack  [{{3}}]
    out    [4, 2, 5, {{1}}]
---
Pop 3, emit it, move to its right child 6 and push it
    stack  [{{6}}]
    out    [4, 2, 5, 1, {{3}}]
---
Pop 6 and emit it. The stack is empty and node is None, so the walk ends. The stack never held more than 3 nodes, the height
    stack  []
    out    [4, 2, 5, 1, 3, {{6}}]
```

## Template

```python
def inorder_iterative(root):
    out, stack, node = [], [], root
    while stack or node:
        while node:                  # push the left spine
            stack.append(node)
            node = node.left
        node = stack.pop()           # leftmost node not yet emitted
        out.append(node.val)
        node = node.right            # then its right subtree
    return out


def preorder_iterative(root):
    out = []
    stack = [root] if root else []
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right:               # pushed first, so popped after the left
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return out


def postorder_iterative(root):
    """Each node is pushed twice: once to expand, once to emit after its children."""
    out, stack = [], [(root, False)]
    while stack:
        node, expanded = stack.pop()
        if node is None:
            continue
        if expanded:
            out.append(node.val)
        else:                        # push in reverse of the order wanted
            stack.append((node, True))
            stack.append((node.right, False))
            stack.append((node.left, False))
    return out


def max_depth_iterative(root):
    best = 0
    stack = [(root, 1)] if root else []
    while stack:
        node, depth = stack.pop()
        best = max(best, depth)
        for child in (node.left, node.right):
            if child:
                stack.append((child, depth + 1))
    return best
```

## Pitfalls

- **Loop condition**: in-order needs `while stack or node`. With only `while stack`, the loop never starts (the stack is empty at first); with only `while node`, it stops at the first node without a right child.
- **Push order**: pushing left before right in pre-order yields root, right, left.
- **Raising the recursion limit as the fix**: `sys.setrecursionlimit(10**6)` silences the Python check, but a deep enough recursion then overflows the C stack and the process dies with a segmentation fault. If you must, also run the work in a thread with a larger stack (`threading.stack_size`); the explicit stack is simpler.
- **Reversed pre-order as post-order**: fine for producing a list, wrong when you need to act on each node at its post-order moment (freeing, streaming).
- **Changing the tree during the walk**: if your loop body reassigns `node.right`, the walk follows the new pointer. Save what you need before changing links.

## Check yourself

Q: In the in-order trace above, what does the stack hold just after 5 is emitted, and what is emitted next?
A: Just `[1]`: node 1 is the only ancestor whose value is still pending. Since 5 has no right child, the next step pops 1 and emits it.

Q: Why does the in-order stack never hold more than h nodes?
A: Every node on the stack is an ancestor of the current position whose value has not been emitted, and those ancestors lie on one root-to-node path, which has at most h nodes. A node is pushed when the walk passes it going left and popped before the walk moves into its right subtree, so no node from a finished subtree remains.

Q: A service receives a binary tree as JSON-like nested objects, up to 200,000 nodes deep in the worst case, and must return its post-order. Recursion, raised limit, or explicit stack?
A: The explicit stack. Plain recursion raises RecursionError near depth 1000; raising the limit to 200,000 risks a hard crash from C stack overflow; the two-push post-order on a Python list handles any depth and keeps O(n) time.

Q: This pre-order loop prints `[1, 3, 2]` for the tree `[1, 2, 3]`: `node = stack.pop(); out.append(node.val); stack.append(node.left); stack.append(node.right)` (with a None check). What is wrong?
A: The left child is pushed first, so it ends up below the right child and is popped after it: the walk visits root, right, left. Push the right child first, then the left.

## Lab

- **94**: solve in-order again with `inorder_iterative`. Expected: `[4, 2, 5, 1, 3, 6]` for `[1, 2, 3, 4, 5, None, 6]`. Then build a left chain of 100,000 nodes with a loop (values 1 to 100,000 going down) and run both versions: the iterative one returns 100,000 values starting with 100000; the recursive one raises `RecursionError`.
- **104**: solve maximum depth with `max_depth_iterative`. Expected: 3 for the example tree, and 100000 for the same chain, with no recursion at all.

> [!know]
> You now know how to run pre-, in- and post-order traversals with an explicit stack, and when Python's recursion limit makes that necessary.

=== primer | Where do trees run in real software, and which traversal does each one use? | 12 min
goal: Recognise file systems, the DOM, syntax trees and JSON documents as trees, and pick the traversal and the safety limits real tools use for them
link: DOM Standard, tree order | https://dom.spec.whatwg.org/#concept-tree-order | 2 min: the opening of section 1.1 "Trees": "tree order is preorder, depth-first traversal", the order in which querySelectorAll and getElementsByTagName return elements
link: Python docs, ast.NodeVisitor | https://docs.python.org/3/library/ast.html#ast.NodeVisitor | 5 min: NodeVisitor and NodeTransformer (depth-first visitors with one method per node type), and the walk function just above them

> [!key]
> Hierarchical data is a tree, and real tools pick traversals for the same reasons you do: **pre-order** when a parent must come first (listing a folder before its contents, document order in the DOM), **post-order** when a parent needs its children's results (folder sizes, deleting a directory, evaluating an expression, generating code), and **breadth-first** when order does not matter or depth must stay bounded. Production code also guards against depth: explicit stacks and nesting limits.

## Intuition

Open a file manager: folders contain folders and files. Open a browser's developer tools: elements contain elements. Look at how Python sees `2 * (3 + 4) - 5`: an operator node whose children are smaller expressions. A JSON config is dictionaries inside lists inside dictionaries. Each is a rooted tree with ordered children, and every operation you run on them is one of this module's traversals.

## How it works

### File systems

Directories are internal nodes and files are leaves. (Hard links and symbolic links can make it a graph; `os.walk` does not follow symlinks unless `followlinks=True`, which avoids cycles.) `os.walk(top)` yields `(dirpath, dirnames, filenames)` for a directory **before** its subdirectories by default (`topdown=True`, pre-order), and you can prune the walk by removing names from `dirnames` in place. With `topdown=False` it yields a directory **after** all its subdirectories (post-order), which is what you need to delete a tree (a directory must be empty before `rmdir`) or to total sizes like `du`. In CPython 3.12, `os.walk` is implemented with an explicit stack rather than recursion, so very deep directory trees do not hit the recursion limit.

### The DOM

A web page is a tree of elements. The DOM Standard defines **tree order** as a pre-order, depth-first traversal, and APIs such as `querySelectorAll` return matches in that order. Serialising a page back to HTML writes each opening tag at the element's pre-order moment and each closing tag at its post-order moment, which is why the text can be parsed back into the same tree.

### Compilers and abstract syntax trees

`ast.parse("2 * (3 + 4) - 5")` returns a tree: `BinOp(-)` with children `BinOp(*)` and `Constant(5)`, and so on. CPython's compiler emits bytecode in **post-order**: operands before their operator. `dis.dis` on `a + b * c` shows `LOAD_NAME a`, `LOAD_NAME b`, `LOAD_NAME c`, `BINARY_OP *`, `BINARY_OP +`. The virtual machine then evaluates with a value stack, exactly like evaluating postfix (reverse Polish) notation. Python's `ast.NodeVisitor` walks depth-first with one `visit_<Type>` method per node type, while `ast.walk` is documented as "in no specified order" (in CPython it uses a deque, so it is breadth-first).

### JSON and other nested documents

Parsed JSON is a tree of dicts and lists. Parsers recurse on nesting, so deeply nested input is a classic denial-of-service vector: CPython's `json.loads` raises `RecursionError` on 100,000 nested arrays. Services that accept untrusted documents either cap the depth before parsing or traverse with an explicit stack.

## Cost

All of these traversals are O(n) in the number of nodes, but the constant differs wildly: a DOM or AST walk touches objects in memory, while `os.walk` makes one system call per directory (a `scandir`), so file-system traversals are I/O-bound and the order you visit directories can matter more than the algorithm. Memory follows the traversal: pre-order and post-order walks hold one path (O(h)), breadth-first walks hold a level (O(w)).

## When to use it

| System | Tree | Traversal | Why |
|---|---|---|---|
| `os.walk(topdown=True)` | directories | pre-order | list or prune a folder before entering it |
| `os.walk(topdown=False)`, `rm -r`, `du` | directories | post-order | children must be deleted or totalled first |
| DOM `querySelectorAll` | elements | pre-order | "document order" is defined as pre-order |
| Compiling or evaluating an expression | AST | post-order | operands before operators |
| Copying or serialising a document | any | pre-order | create the parent before its children |
| Checking a document's depth or size cheaply | any | BFS or explicit stack | no recursion limit, bounded memory per level |

## Worked trace

Evaluating `2 * (3 + 4) - 5` in post-order with a value stack (this is what the bytecode does):

```text
          -
        /   \
       *     5
      / \
     2   +
        / \
       3   4
```

```steps
Post-order visits the leaf 2 first: a constant, so push its value
    visit  {{2}} 3 4 + * 5 -
    stack  [{{2}}]
---
The constants 3 and 4 come next: push both
    visit  2 {{3}} {{4}} + * 5 -
    stack  [2, {{3}}, {{4}}]
---
+ is visited after both of its children: pop 4 and 3, push 3 + 4 = 7
    visit  2 3 4 {{+}} * 5 -
    stack  [2, {{7}}]
---
* comes after its children: pop 7 and 2, push 2 * 7 = 14
    visit  2 3 4 + {{*}} 5 -
    stack  [{{14}}]
---
Push the constant 5
    visit  2 3 4 + * {{5}} -
    stack  [14, {{5}}]
---
The root - is visited last: pop 5 and 14, push 14 - 5 = 9, the value of the expression
    visit  2 3 4 + * 5 {{-}}
    stack  [{{9}}]
```

## Template

```python
import ast
import operator
import os

OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
       ast.Mult: operator.mul, ast.Div: operator.truediv}


def evaluate(node):
    """Evaluate an arithmetic syntax tree in post-order."""
    if isinstance(node, ast.Expression):
        return evaluate(node.body)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        left, right = evaluate(node.left), evaluate(node.right)   # children first
        return OPS[type(node.op)](left, right)
    raise ValueError(f"unsupported node: {type(node).__name__}")


def dir_sizes(top):
    """Total bytes of the files under every directory, computed bottom-up."""
    total = {}
    for path, dirs, files in os.walk(top, topdown=False):
        size = sum(os.path.getsize(os.path.join(path, f)) for f in files)
        size += sum(total.get(os.path.join(path, d), 0) for d in dirs)
        total[path] = size
    return total


def json_depth(value):
    """Nesting depth of dicts and lists, without recursion (a scalar has depth 0)."""
    best, stack = 0, [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if isinstance(item, dict):
            item = list(item.values())
        if isinstance(item, list):
            best = max(best, depth + 1)
            stack.extend((child, depth + 1) for child in item)
    return best


print(evaluate(ast.parse("2 * (3 + 4) - 5", mode="eval")))   # 9
print(json_depth({"a": [1, {"b": []}]}))                    # 4
```

`total.get(..., 0)` covers subdirectory entries that `os.walk` lists but does not enter, such as symbolic links to directories.

## Pitfalls

- **Cycles in "trees"**: symlinks, hard links and object graphs with back-references turn trees into graphs. Keep `followlinks=False` or track visited identities.
- **Pruning needs top-down**: editing `dirnames` in place only affects the walk when `topdown=True`; in post-order the subdirectories were already visited.
- **Errors are silent**: `os.walk` ignores errors such as permission denied unless you pass `onerror`. A size total can be quietly incomplete.
- **Unbounded depth on untrusted input**: a recursive validator or pretty-printer is a crash waiting for a deep payload. Cap the depth or use a stack.
- **Relying on unspecified order**: `ast.walk` promises no order; if you need parents before children, use a `NodeVisitor` or your own traversal.

## Check yourself

Q: In what order does CPython emit the operations for `(a - b) * c`, and which traversal is that?
A: `LOAD_NAME a`, `LOAD_NAME b`, `BINARY_OP -`, `LOAD_NAME c`, `BINARY_OP *`: the subtraction's operands, the subtraction, then the other operand, then the multiplication. Operators come after their operands: post-order.

Q: Why must a recursive delete of a directory be post-order?
A: The operating system removes only empty directories, so every file and subdirectory inside must be gone before the directory itself. Post-order handles a node after all its children, which guarantees that.

Q: Your API accepts JSON configs and validates them with a recursive function. A user sends a 50,000-deep nested list. What happens, and what are two fixes?
A: Parsing (`json.loads`) or the recursive validator raises `RecursionError` (or, with a raised limit, may crash the process). Fixes: reject documents above a maximum size or nesting depth before full processing, and write the validator with an explicit stack, as `json_depth` does.

Q: You call `os.walk(top)` and want to skip every `.git` folder and everything inside it. What do you do, and why does it require the default `topdown=True`?
A: Inside the loop, remove it from the list in place: `dirs[:] = [d for d in dirs if d != ".git"]`. In top-down mode `os.walk` decides which subdirectories to enter after yielding the parent, using that same list, so the pruned folders are never visited. In bottom-up mode the subdirectories have already been walked by the time the parent is yielded.

## Lab

- **Evaluate a syntax tree**: extend `evaluate` with unary minus (`ast.UnaryOp` with `ast.USub`) and `ast.Pow`. Expected: `2 * (3 + 4) - 5` gives 9, `-(2 ** 3) + 10` gives 2, and `print(ast.dump(ast.parse("1 + 2", mode="eval"), indent=2))` shows a `BinOp` whose children are two `Constant` nodes.
- **Folder sizes**: in a scratch folder, create `demo/a/x.txt` with 10 bytes and `demo/a/b/y.txt` with 20 bytes, then call `dir_sizes("demo")`. Expected: 20 for `demo/a/b`, 30 for `demo/a`, 30 for `demo` (paths printed with your platform's separator). Then switch to `topdown=True` and explain why the totals break.
- **Deep JSON**: build `doc = []` nested 100,000 levels deep with a loop (`for _ in range(99_999): doc = [doc]`). Expected: `json_depth(doc)` returns 100000, while `json.loads(json.dumps(doc))` raises `RecursionError` (`json.dumps` already fails on the way out).

> [!know]
> You now know how file systems, the DOM, syntax trees and JSON map onto pre-order, post-order and breadth-first traversals, and how real tools guard against deep trees.

=== lab | Tree toolkit: build, walk, serialise and property-test | 50 min
goal: Assemble a reusable treekit.py with builders, recursive and iterative traversals and serialisation, then prove it with random round-trip tests and a deep-tree test
link: USACO Guide, Stress testing | https://usaco.guide/general/basic-debugging#stress-testing | 5 min: the "Stress Testing" section: run your code against a version you trust on many small random inputs until they disagree

You will collect this module's templates into one file, write a random tree generator, and check every function against an independent version on thousands of random trees. The result is the toolkit you will use for every tree problem: one line to build a test tree, and a stress test ready to catch your next bug.

## Setup

- Python 3.10 or newer, standard library only (if you built the `dsakit` stress harness earlier in the guide, use it for step 4).
- One file `treekit.py` and one test file `test_treekit.py` in a scratch folder.

## Steps

1. **Collect the toolkit.** Copy into `treekit.py`: `TreeNode` and `traverse` (first card), `build`, `to_list` and `level_order` (level-order card), `inorder_iterative`, `preorder_iterative`, `postorder_iterative` and `max_depth_iterative` (iterative card), `serialise`, `deserialise` and `build_from_pre_in` (build card), and `height` (bottom-up card).

2. **Write a random tree generator** that can produce any shape, plus a structural equality check:

```python
import random


def random_tree(n, rng, values=range(-5, 6)):
    """A random binary tree with n nodes: each new node fills a random empty slot."""
    if n == 0:
        return None
    root = TreeNode(rng.choice(values))
    slots = [(root, "left"), (root, "right")]
    for _ in range(n - 1):
        i = rng.randrange(len(slots))
        slots[i], slots[-1] = slots[-1], slots[i]      # O(1) removal of a random slot
        parent, side = slots.pop()
        child = TreeNode(rng.choice(values))
        setattr(parent, side, child)
        slots += [(child, "left"), (child, "right")]
    return root


def same(a, b):
    """Structural equality, without recursion."""
    stack = [(a, b)]
    while stack:
        x, y = stack.pop()
        if x is None or y is None:
            if x is not y:
                return False
            continue
        if x.val != y.val:
            return False
        stack += [(x.left, y.left), (x.right, y.right)]
    return True
```

3. **Write the properties.** For each seed from 0 to 1999, make `rng = random.Random(seed)` and a tree with `rng.randint(0, 30)` nodes, then assert:
    - the three iterative traversals equal the three lists from the recursive `traverse`;
    - `same(build(to_list(t)), t)` (level-order round trip);
    - `same(deserialise(serialise(t)), t)` (marker round trip, including negative values);
    - `max_depth_iterative(t) == height(t)` and `len(level_order(t)) == height(t)`;
    - for a tree whose values are made distinct first (relabel the nodes 0, 1, 2, ... in any order), `same(build_from_pre_in(pre, ino), t)`.

4. **Report the smallest failure.** Wrap the loop so that on the first failing seed it prints the seed, the tree as `to_list(t)`, and which property failed. Sort the seeds by tree size if you want the smallest counterexample first.

5. **Plant a bug and catch it.** In `preorder_iterative`, swap the two `if` blocks so the left child is pushed first. Run the tests and note the first failing tree. Undo the bug.

6. **Go deep.** Build a chain of 100,000 nodes (each node the left child of the previous one). Check that every iterative function and `same` work on it, then call `traverse` on it inside `try`/`except RecursionError`.

7. **Measure.** Build a random tree with 200,000 nodes and time `traverse` against the three iterative functions with `time.perf_counter`, three runs each, keeping the median.

## What you should see

- All 2,000 random trees pass every property in a second or two.
- With the planted bug, almost every seed fails. Sorted by size, the smallest failure has three nodes, a root with two children such as `[-3, -2, 5]`, whose pre-order comes out as `[-3, 5, -2]`. Small random inputs find bugs and explain them at the same time.
- On the 100,000-node chain, the iterative functions return 100,000 values and a depth of 100000, `same` returns True, and `traverse` raises `RecursionError` within about the first thousand levels.
- On the 200,000-node random tree (height around 45), each traversal takes roughly 0.1 seconds, and the two-push post-order about twice that. The single recursive walk that fills all three lists runs about as fast as one iterative walk; neither style is dramatically faster in CPython, so choose by depth and clarity.
- Keep `treekit.py`: the next module (search trees) and the trie module reuse `TreeNode`, `build` and the stress-test loop.

=== practice
- 104 core
  cue: One number for the whole tree, defined by its longest root-to-leaf chain.
  hint: If you already knew the answer for the left and the right subtree, how would you get the root's answer? What is it for an empty tree?
  insight: depth(node) = 1 + max(depth(left), depth(right)) with depth(None) = 0: a post-order function that returns its subtree's depth. Counting BFS levels, or a stack of (node, depth) pairs, gives the same answer without recursion on skewed trees.
  cost: O(n) time, O(h) space
  pattern: trees-up
- 110 core
  cue: A condition must hold at every node, and it compares a measurement of the node's two subtrees.
  hint: Two booleans from the children cannot decide the parent. What number does the parent also need, and can the same call return it?
  insight: Return the subtree's height, or -1 if any node inside is unbalanced. A node returns -1 if either child did or if the two heights differ by more than one, else 1 + max. One pass; calling a separate height function at every node is O(n^2) on a chain.
  cost: O(n) time, O(h) space
  pattern: trees-up
- 543 core
  cue: Longest path between any two nodes, and it need not pass through the root.
  hint: Every path has one highest node where it turns. How long is the longest path that turns at a given node, in terms of its two subtrees?
  insight: A helper returns subtree height in nodes. At each node, left + right is the edge count of the longest path bending there: keep the maximum in an outer variable and return 1 + max(left, right) to the parent, which can only extend one arm.
  cost: O(n) time, O(h) space
  pattern: trees-global
- 94 core
  cue: Values in left-subtree, node, right-subtree order, with a follow-up asking for no recursion.
  hint: While the recursive version is deep inside a left subtree, what is the call stack remembering? Keep those same nodes in a list.
  insight: Push the whole left spine, pop a node and record it, then move to its right child and repeat, looping while the stack or the current node is non-empty. The stack holds exactly the ancestors still waiting to be recorded, so it never exceeds the height.
  cost: O(n) time, O(h) space
  pattern: trees-iter
- 102 core
  cue: Output grouped by distance from the root, top row first.
  hint: A first-in, first-out line serves nodes in order of depth. How can you tell where one level ends and the next begins?
  insight: BFS with a deque. At the start of each round, len(queue) is exactly the number of nodes on the current level, so pop that many, collect their values and push their children for the next round.
  cost: O(n) time, O(w) space for the widest level w
  pattern: trees-bfs
- 1448 core
  cue: Whether a node counts depends on the values of every node above it on its root path.
  hint: A node does not need the whole path, only one number summarising it. Which number, and how does it change for the children?
  insight: Pass the largest value seen on the path so far down as an argument. A node is good when its value is at least that maximum, and its children receive max(best, val). Return 1 or 0 plus the children's counts.
  cost: O(n) time, O(h) space
  pattern: trees-down
- 437 derive
  cue: Count downward paths with a given sum that may start and end at any node, with negative values allowed.
  hint: A downward path from u to v sums to (root-to-v sum) minus (root-to-parent-of-u sum). Where have you counted subarrays with a given sum before?
  insight: Walk down with the running root-path sum and a Counter of the prefix sums on the current path, seeded with {0: 1}. At each node add count[running - target], then increment count[running], recurse, and decrement it on the way back so sibling branches never pair up.
  cost: O(n) time, O(n) space
  pattern: trees-down
- 236 derive
  cue: The deepest node that has both given nodes below it (or is one of them), with child pointers only and no ordering of values.
  hint: Let each call report whether it found p, q or both below it. At which node can a call be sure it is the answer?
  insight: Return the node itself if it is None, p or q; otherwise recurse into both sides. If both sides return something, p and q are split across this node, so it is the answer; otherwise return the non-empty side, which carries p, q or the answer upward unchanged.
  cost: O(n) time, O(h) space
  pattern: trees-lca
- 105 core
  cue: Two traversal lists of the same tree with distinct values, and you must rebuild its shape.
  hint: Which list tells you the root? Once you know the root, what does the other list tell you about how many nodes are on each side?
  insight: The next pre-order value is the root of the subtree being built, and its in-order index splits the in-order range into left and right. Map value to in-order index once, consume pre-order with an iterator, and build left before right over index ranges, never slicing.
  cost: O(n) time, O(n) space
  pattern: trees-build
- 124 core
  cue: Maximum sum over paths that can start and end anywhere, with negative values allowed.
  hint: Separate the path a node can offer its parent (one direction only) from the best path that turns at the node (both directions). What should a negative branch contribute?
  insight: gain(node) = val + max(0, gain(left), gain(right)) is returned upward, while val + max(0, gain(left)) + max(0, gain(right)) updates a global best that starts at negative infinity, so an all-negative tree returns its largest single value.
  cost: O(n) time, O(h) space
  pattern: trees-global
- 297 stretch
  cue: Encode any tree, including its gaps, as one string and decode it back exactly.
  hint: One traversal list loses the shape. What could you write down for the empty children so that a single traversal is enough?
  insight: Write pre-order with a marker such as # for every missing child. Decode by reading tokens from an iterator in the same order: a value creates a node whose left and then right subtrees are read next, and a marker returns None. Each subtree is a contiguous block of tokens.
  cost: O(n) time, O(n) space
  pattern: trees-build
- 863 stretch
  cue: Every node at a fixed distance from a target node, including nodes above it and in other branches.
  hint: Distances can go up through parents, which the nodes do not store. What if every node also knew its parent?
  insight: Build a parent map with one traversal so each node has up to three neighbours, then run BFS from the target for k rounds with a visited set. The frontier after k rounds is the answer.
  cost: O(n) time, O(n) space
  pattern: trees-lca
