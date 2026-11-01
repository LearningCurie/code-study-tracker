---
key: bst
name: Binary search trees and ordered maps
stage: hier
summary: Keep keys in order so that search, insert, delete, floor, ceiling, k-th and range queries cost time proportional to the height, and learn which ordered structure to reach for in Python and in production systems.
why: A hash map answers "is it there?" but not "what is the next key after this one?", "every order between 9:00 and 9:05" or "the 100th best score". Ordered structures answer those, and the binary search tree is the idea under all of them: an ordering invariant that turns every query into one walk down one path. The catch is the height. Sorted input turns a plain search tree into a linked list, so real systems use self-balancing trees (C++ std::map, Java's TreeMap, the Linux kernel), B-trees (relational database indexes), skip lists (Redis) or, in Python, sortedcontainers' list of sorted lists. This module teaches the invariant, the operations and why they are correct, why balance matters, and how to pick the ordered map that is fastest in practice.
outcomes:
- Search, insert, find the minimum and maximum, and delete in a binary search tree, including the two-child case with the in-order successor
- Validate a binary search tree by passing bounds down, by an in-order scan, or by returning subtree summaries up, and explain why checking only children fails
- Use in-order order to find the k-th smallest key, successors and an O(h)-memory iterator, and repair a tree in which two keys were swapped
- Explain why sorted insertions make a plain tree degenerate, build a balanced tree from sorted keys, and state the invariants and height bounds of AVL, red-black, treap and B-tree designs
- Choose between bisect on a list, sortedcontainers, heapq and a hand-written tree in Python, and map them to C++ std::map and Java's TreeMap
- Describe how B+ trees in SQLite and PostgreSQL and sorted sets in Redis serve point lookups and range scans
cues:
- "Sorted" together with inserts and deletes over time
- Floor, ceiling, predecessor, successor, "closest value", "next larger"
- The k-th smallest of a set that keeps changing, ranks, leaderboards
- Range queries such as "all keys between lo and hi"
- A tree in which left values are smaller and right values larger
traps:
- Validating by comparing each node only with its children instead of with the bounds set by all its ancestors
- Inserting already-sorted keys into a plain tree and getting a chain of height n
- Deleting a node with two children by copying the successor up but forgetting to delete the successor from the right subtree
- Calling bisect.insort in a loop on a large list (each insert is O(n)) when a SortedList or a heap was needed
- Assuming Python has a built-in balanced tree, or calling std::lower_bound on a std::set instead of its member lower_bound
systems:
- PostgreSQL B-tree indexes implement Lehman and Yao's algorithm: each page has a right-link to its sibling and a high key, so readers can follow concurrent page splits without read locks
- SQLite stores every table and index as a B-tree of fixed-size pages (4096 bytes by default since 3.12.0); table b-trees keep all row data in the leaves
- Redis sorted sets: a hash table plus a skip list up to Redis 8.10, and a packed B+ tree for large sets in the 8.12 release candidate
- C++ std::map is usually a red-black tree, Java's TreeMap is a red-black tree, Rust's BTreeMap is a B-tree, and Python's sortedcontainers uses a list of sorted sublists
further:
- Article · 25 min | Sedgewick and Wayne, algs4 3.2 Binary Search Trees: Basic implementation, Analysis, and Order-based methods and deletion | https://algs4.cs.princeton.edu/32bst/
- Notes · 20 min | MIT 6.006 (Spring 2020) Lecture 7 notes, AVL trees: Height Balance, Rotations and Rotations Suffice | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/a2c80596cf4a2b5fbc854afdd2f23dcb_MIT6_006S20_lec7.pdf
- Docs · 10 min | Sorted Containers: Implementation Details (the list-of-lists design and its positional index) | https://grantjenks.com/docs/sortedcontainers/implementation.html
- Visualisation · 10 min | VisuAlgo: insert a sorted sequence into a plain BST, then into an AVL tree | https://visualgo.net/en/bst
bank: bst
---

=== primer | How does a binary search tree find and insert a key in O(h)? | 15 min
goal: Search, insert, find the minimum and maximum, and prune range queries in a binary search tree by following its ordering invariant down one path
tag: bst-search | Search and insert by the ordering invariant
link: Sedgewick and Wayne, algs4 3.2 Binary Search Trees | https://algs4.cs.princeton.edu/32bst/ | 15 min: "Basic implementation" (search and insert, recursive) and the "Analysis" paragraph on why the cost is the depth of the node
practice: 700, 235, 938

> [!key]
> A binary search tree (BST) keeps one **invariant**: every key in a node's left subtree is smaller than the node's key, and every key in its right subtree is larger. So one comparison at each node tells you which subtree can contain the key, and search, insert, minimum and maximum each walk a **single root-to-node path**: O(h) time, where h is the height. Range queries prune whole subtrees the same way.

## Intuition

Play "guess the number" with a friend who answers "higher" or "lower". Binary search on a sorted array does that with indices. A BST does it with pointers: the root is your first guess, and "lower" sends you to the left subtree, which is itself a smaller guessing game. The difference from a sorted array is what happens on insert: the array must shift everything after the new key, while the tree just hangs a new leaf where the failed search ended.

```text
           40
         /    \
       20      60          left subtree of 40: {10, 20, 30}, all < 40
      /  \    /  \         right subtree of 40: {50, 60, 70}, all > 40
    10   30  50   70       the same holds at every node
```

## How it works

### The invariant and what it buys

For every node x: all keys in `x.left` are less than `x.val`, and all keys in `x.right` are greater. (This module assumes distinct keys; a multiset stores counts in the node, or sends equal keys consistently to one side.) The invariant is about whole subtrees, not just children, and that is what makes the next step safe: if the key you want is smaller than `x.val`, it cannot be anywhere in the right subtree, so you may forget the right subtree entirely.

### Search

Start at the root. If the key equals the node's key, stop. If it is smaller go left, otherwise go right. Reaching None means the key is absent, and the None you reached is exactly where it would be inserted.

### Insert

Search for the key; when you fall off the tree, attach a new node there. Written recursively, `insert(node, key)` **returns the root of the updated subtree**, and each parent reassigns its child pointer: `node.left = insert(node.left, key)`. That "return the new subtree root" pattern makes the empty-tree case and the attach step the same line, and the next card (deletion) uses it again.

### Minimum, maximum and the split point

The minimum is the leftmost node (go left until you cannot), the maximum the rightmost. For two keys p < q, the **split point** is the first node on the path from the root where they stop going the same way: p goes left (or is the node) and q goes right (or is the node). Every node above it has both keys on one side, and the split node has them on different sides, so it is their lowest common ancestor. In a plain binary tree finding it needed a full traversal; here it is one path.

### Range queries prune subtrees

To sum (or list) the keys in [lo, hi]: at a node smaller than lo, the whole left subtree is smaller still, so only the right subtree can contribute; symmetrically for a node larger than hi; a node inside the range contributes itself and both subtrees. You visit the k keys in range plus the nodes on the two boundary paths.

## Cost

Each step of search, insert, minimum, maximum and split-point moves one level down and does O(1) work, so each is **O(h)**. The range query is **O(h + k)** for k reported keys.

h is between log2(n + 1) (a perfectly balanced tree) and n (a chain). Inserting keys in random order gives an expected depth of about 1.39 log2 n per search, but inserting them in sorted order gives a chain, where every operation is O(n). The "why balance matters" card measures this; for now remember that **O(h) is only O(log n) if something keeps the tree balanced**.

Space: the iterative search uses O(1) extra space; the recursive insert uses O(h) stack.

## When to use it

A BST is the right model whenever a problem gives you one, or needs order plus updates: "next larger key", floor and ceiling, sorted iteration while keys change, range counts. Compared with the alternatives:

| Structure | Search | Insert/delete | Next larger key, range scan | Notes |
|---|---|---|---|---|
| Hash set or dict | O(1) average | O(1) average | not supported (no order) | the default when order does not matter |
| Sorted list + bisect | O(log n) | O(n) (shifting) | O(log n + k) | excellent when updates are rare |
| Balanced BST | O(log n) | O(log n) | O(log n + k) | what std::map and TreeMap provide |
| Plain BST | O(h) | O(h) | O(h + k) | fine for random keys, terrible for sorted ones |

In Python you rarely hand-write a BST for production code (the ordered-maps card explains what to use instead), but interview problems hand you BSTs constantly, and the invariant-driven walk is the core of every ordered structure, including B-trees.

## Worked trace

Insert 35 into the tree above, then search for 55:

```steps
insert 35: compare with the root. 35 < 40, so 35 belongs in the left subtree
           {{40}}
         /    \
       20      60
      /  \    /  \
    10   30  50   70
---
35 > 20: go right. Everything in 20's left subtree is smaller than 20, so it is ruled out
           40
         /    \
       {{20}}      60
      /  \    /  \
    10   30  50   70
---
35 > 30: go right. 30 has no right child, so the search falls off the tree here
           40
         /    \
       20      60
      /  \    /  \
    10   {{30}}  50   70
---
Attach 35 as the right child of 30. Three comparisons, one per level, and the invariant still holds
           40
         /    \
       20      60
      /  \    /  \
    10   30  50   70
           \
            {{35}}
---
search 55: 55 > 40 go right, 55 < 60 go left, 55 > 50 go right: None. Absent, and that None is where 55 would go
           40
         /    \
       20      {{60}}
      /  \    /  \
    10   30  {{50}}   70
           \
            35
```

## Template

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def search(node, key):
    """Node holding key, or None. Iterative: O(h) time, O(1) space."""
    while node is not None and node.val != key:
        node = node.left if key < node.val else node.right
    return node


def insert(node, key):
    """Insert key (duplicates are ignored) and return the subtree's root."""
    if node is None:
        return TreeNode(key)
    if key < node.val:
        node.left = insert(node.left, key)
    elif key > node.val:
        node.right = insert(node.right, key)
    return node


def minimum(node):
    """Leftmost node of a non-empty subtree."""
    while node.left is not None:
        node = node.left
    return node


def split_point(root, p, q):
    """Lowest common ancestor of keys p and q, both present: where their paths part."""
    node = root
    while node:
        if p < node.val and q < node.val:
            node = node.left
        elif p > node.val and q > node.val:
            node = node.right
        else:
            return node


def range_sum(node, lo, hi):
    """Sum of keys in [lo, hi], skipping subtrees that cannot contain any."""
    if node is None:
        return 0
    if node.val < lo:
        return range_sum(node.right, lo, hi)
    if node.val > hi:
        return range_sum(node.left, lo, hi)
    return node.val + range_sum(node.left, lo, hi) + range_sum(node.right, lo, hi)


root = None
for key in [40, 20, 60, 10, 30, 50, 70, 35]:
    root = insert(root, key)
print(search(root, 35).val, search(root, 55))   # 35 None
print(minimum(root).val, split_point(root, 10, 35).val, split_point(root, 35, 50).val)   # 10 20 40
print(range_sum(root, 25, 55))   # 155
```

`TreeNode` is the same class as in the binary trees module.

## Pitfalls

- **Comparing only with the parent** when reasoning about where a key can be: the invariant is about whole subtrees, and code that ignores that (for example in validation, two cards ahead) is wrong.
- **Forgetting to reassign the child pointer**: calling `insert(node.left, key)` without `node.left = ...` loses the new node whenever the child was None.
- **Duplicates**: decide a policy (ignore, count, or always go right) and apply it everywhere, or search and delete will disagree with insert.
- **Recursion on degenerate trees**: a recursive insert on a 10^4-node chain exceeds Python's recursion limit. Use the iterative walk (shown in the balance card) when the tree can be skewed.
- **Range pruning the wrong way round**: when `node.val < lo`, the *left* subtree is useless, not the right one.

## Check yourself

Q: In the trace tree (with 35 inserted), which nodes does `range_sum(root, 25, 55)` visit, and what does it return?
A: 40 is in range (add 40, visit both subtrees). 20 < 25, so only its right subtree is visited: 30 is in range (add 30, visit both children: None on the left, 35 on the right, add 35). On the right of the root, 60 > 55, so only its left subtree: 50 is in range (add 50). 10 and 70 are never visited. The sum is 40 + 30 + 35 + 50 = 155.

Q: Why is it safe for search to discard the whole right subtree when the key is smaller than the node's key?
A: The invariant says every key in the right subtree is greater than the node's key, and the key we want is smaller than the node's key, so it is smaller than every key there. It cannot be in that subtree, so ignoring it loses nothing. Applying this at every step proves that if the key exists, the walk reaches it.

Q: You must support "insert a score" and "what is the smallest score greater than x?" for 10^5 operations. Hash set, sorted list with bisect, or a balanced search tree?
A: A hash set cannot answer "smallest greater than x" without scanning. A sorted list answers it in O(log n) but each insert shifts O(n) elements, about 5 * 10^9 element moves in the worst case for 10^5 inserts, though in Python's C memmove that is often still a few seconds. A balanced tree (or, in Python, a SortedList) does both in O(log n), which is the right choice.

Q: Where does the split point of keys 10 and 30 lie in the trace tree, and why is a node higher up not their lowest common ancestor?
A: At 20: from the root both are smaller than 40, so both go left; at 20, 10 goes left and 30 goes right, so their paths part there. 40 is a common ancestor, but not the lowest, because 20 is also a common ancestor and is deeper.

## Lab

- **700**: iterative search. Expected: on the tree built from `[40, 20, 60, 10, 30, 50, 70]`, searching 30 returns the subtree rooted at 30 (level order `[30]`), searching 60 returns `[60, 50, 70]`, and searching 55 returns None; O(h) time, O(1) space.
- **235**: split-point lowest common ancestor. Expected on the same tree: (10, 30) gives 20, (10, 70) gives 40, (50, 60) gives 60 (a node can be its own ancestor); O(h) time, O(1) space.
- **938**: range sum with pruning. Expected on the same tree: [25, 55] gives 120 (30 + 40 + 50), [10, 70] gives 280, [61, 69] gives 0; O(h + k) time. Count the nodes visited for [61, 69] (expected: 40, 60 and 70, then one empty child).

> [!know]
> You now know how a binary search tree turns every lookup, insert, minimum, lowest common ancestor and range query into a walk down one path guided by its ordering invariant.

=== primer | How do you delete a key from a binary search tree without breaking the order? | 15 min
goal: Delete a key in all three cases (leaf, one child, two children) by returning the new subtree root, and trim a tree to a key range
tag: bst-delete | Deletion with successor replacement
link: Sedgewick and Wayne, algs4 3.2 Binary Search Trees | https://algs4.cs.princeton.edu/32bst/ | 10 min: under "Order-based methods and deletion", read "Delete the minimum" and "Delete" (Hibbard deletion), including the note on why repeated deletions skew the tree
practice: 450, 669

> [!key]
> Find the node, then: a **leaf** simply disappears; a node with **one child** is replaced by that child; a node with **two children** takes the key of its **in-order successor** (the smallest key in its right subtree), and that successor, which has no left child, is then deleted from the right subtree by one of the easy cases. Write it as "return the new root of this subtree" and every case is a one-line return.

## Intuition

Think of a tournament bracket or a filing cabinet with a strict order. Removing a folder at the end of a shelf is trivial. Removing one with a single neighbour group behind it means sliding that group into its place. Removing one in the middle of a full shelf needs a replacement that fits exactly between the left and right neighbours: the next folder in order is the natural choice, because everything left of the gap is smaller than it and everything right of it is larger.

## How it works

### Step 1: find it, returning subtree roots

`delete(node, key)` returns the root of the subtree after deletion. If the key is smaller, recurse left and reassign `node.left`; if larger, recurse right; if the subtree is empty, the key is absent and you return None. This is the same shape as insert.

### Step 2: the three cases at the node holding the key

1. **No children**: return None. The parent's pointer becomes None.
2. **One child**: return that child. The whole child subtree moves up one level. Order is preserved because that subtree was already on the correct side of every ancestor.
3. **Two children**: the replacement must be larger than everything on the left and smaller than everything on the right. Two keys qualify: the **predecessor** (maximum of the left subtree) and the **successor** (minimum of the right subtree). Take the successor: walk right once, then left until you cannot. Copy its key into the node, then delete the successor's key from the right subtree. The successor has no left child (otherwise that child would be smaller), so that second deletion is case 1 or 2.

### Why the order survives

After case 3 the node holds s, the minimum of the old right subtree. Every key on the left was smaller than the deleted key, which was smaller than s: fine. Every remaining key on the right was larger than s, since s was the minimum there: fine. Every ancestor's constraint on this subtree was satisfied by s before, because s was already in this subtree. So the invariant holds everywhere.

### Copying keys versus relinking nodes

Copying `succ.val` into the node is what interview solutions do. Libraries usually **relink** the successor node into the deleted node's position instead, because callers may hold references or iterators to nodes and expect a node's key never to change, and because a node may carry a large value payload. The structure of the argument is identical.

### Trimming to a range

Trimming a tree so that only keys in [lo, hi] remain is deletion in bulk with the range-pruning logic from the previous card: a node below lo is dropped together with its whole left subtree, and the trimmed right subtree takes its place; symmetrically above hi; a node in range keeps itself and trims both children.

## Cost

Finding the node is O(h); finding the successor walks at most another O(h) down the same side; the second deletion is O(1) once there. So deletion is **O(h) time** and O(h) stack for the recursive version. Trimming visits every kept node plus the boundary paths: O(n) in the worst case, which is unavoidable when many nodes are kept, since each needs its children rechecked.

Deletion does not rebalance. Always taking the successor is also asymmetric: algs4 shows a 150-key tree, under long random sequences of inserts and successor-only (Hibbard) deletions, becoming visibly skewed to the left. Alternating between successor and predecessor reduces the drift, but only a self-balancing tree guarantees the height, one more reason production code uses them.

## When to use it

- Problems that ask you to delete, trim or prune a BST in place and return the root.
- Any ordered-set implementation; in Python you would normally call `SortedList.remove` instead of writing this.
- Lazy deletion (marking a node as deleted and skipping it) is an alternative when deletions are rare or must be cheap, at the cost of memory and longer paths; heaps use the same trick.

## Worked trace

Delete 40 (two children) from this tree, `[40, 20, 60, 10, 30, 50, 70, None, None, None, None, None, 55]`:

```steps
delete(root, 40): the key is at the root, and the root has two children, so it needs a replacement
           {{40}}
         /    \
       20      60
      /  \    /  \
    10   30  50   70
               \
                55
---
Find the in-order successor: step right to 60, then left while possible: 50. 50 has no left child, so 50 is the successor
           40
         /    \
       20      60
      /  \    /  \
    10   30  {{50}}   70
               \
                55
---
Copy 50 into the root. For a moment 50 appears twice; the tree is not valid yet
           {{50}}
         /    \
       20      60
      /  \    /  \
    10   30  50   70
               \
                55
---
delete(right subtree, 50): 50 < 60, go left; the node 50 has only a right child, so the call returns 55 (case 2)
           50
         /    \
       20      60
      /  \    /  \
    10   30  {{50}}   70
               \
                {{55}}
---
60.left = 55. The in-order sequence is 10 20 30 50 55 60 70: sorted, with 40 gone
           50
         /    \
       20      60
      /  \    /  \
    10   30  {{55}}   70
```

## Template

```python
def delete(node, key):
    """Remove key if present and return the subtree's new root."""
    if node is None:
        return None
    if key < node.val:
        node.left = delete(node.left, key)
    elif key > node.val:
        node.right = delete(node.right, key)
    else:
        if node.left is None:               # no child, or only a right child
            return node.right
        if node.right is None:              # only a left child
            return node.left
        succ = node.right                   # two children: in-order successor
        while succ.left is not None:
            succ = succ.left
        node.val = succ.val                 # copy it up ...
        node.right = delete(node.right, succ.val)   # ... and remove it below
    return node


def trim(node, lo, hi):
    """Keep only keys in [lo, hi] and return the new root; the result is still a BST."""
    if node is None:
        return None
    if node.val < lo:                       # node and its left subtree are too small
        return trim(node.right, lo, hi)
    if node.val > hi:                       # node and its right subtree are too large
        return trim(node.left, lo, hi)
    node.left = trim(node.left, lo, hi)
    node.right = trim(node.right, lo, hi)
    return node
```

The first `if` in the found branch covers both the leaf (returns None) and the right-child-only case.

## Pitfalls

- **Forgetting the second deletion**: copying the successor's key up without deleting it from the right subtree leaves a duplicate key.
- **Deleting the successor by value in the wrong subtree**: it must be deleted from `node.right`, starting at the right child; starting at `node` would find the copied key at the node itself and loop on the two-child case.
- **Not reassigning child pointers**: `delete(node.left, key)` without `node.left = ...` has no effect when the deleted node was the child itself.
- **Losing the root**: always use the return value, `root = delete(root, key)`, because the root itself may be deleted.
- **Successor without a right subtree**: the "right once, then left" walk only works when the right child exists, which is guaranteed in the two-child case. (A general successor query for any node is different; see the in-order card.)

## Check yourself

Q: Starting again from the trace's original tree, delete 20. What is the successor, and what does the tree look like afterwards?
A: 20 has two children (10 and 30). Its successor is the minimum of its right subtree, which is 30 itself (30 has no left child). Copy 30 into the node, then delete 30 from the right subtree: 30 is a leaf, so it disappears. The left subtree of 40 becomes 30 with left child 10 and no right child.

Q: Why does the successor never have a left child, and why does that matter?
A: The successor is the minimum of the right subtree, found by going left until there is no left child; if it had a left child, that child would be smaller and would be the minimum instead. It matters because it guarantees the second deletion is a no-child or one-child case, so the recursion does not need the two-child case again and stays O(h).

Q: For [lo, hi] = [25, 55], trim the trace's original tree. Which nodes survive, and what is the new root?
A: 40 is in range and stays as the root. On the left, 20 < 25, so 20 and 10 go and 20's trimmed right subtree, 30, takes its place. On the right, 60 > 55, so 60 and 70 go and 60's trimmed left subtree replaces it: 50, which is in range, with its right child 55 kept. Result: 40 with left child 30 and right child 50, and 55 to the right of 50.

Q: A colleague's two-child case is `node.val = succ.val; node.right = delete(node, succ.val)`. What happens?
A: The call starts at `node`, whose key now equals `succ.val`, so it lands in the "found" branch at the same node again, finds the same two children and the same successor, and recurses forever (until RecursionError). The second deletion must start at `node.right`.

## Lab

- **450**: deletion with the three cases. Expected: deleting 40 from `[40, 20, 60, 10, 30, 50, 70, None, None, None, None, None, 55]` gives in-order `[10, 20, 30, 50, 55, 60, 70]` with root 50; deleting a key that is absent returns the tree unchanged; deleting the only node returns None. O(h) time. Stress-test it: apply random inserts and deletes and compare the in-order list with a Python `set` sorted after each step.
- **669**: trim to a range. Expected: trimming the same tree to [25, 55] gives level order `[40, 30, 50, None, None, None, 55]`; trimming to [61, 69] gives an empty tree; O(n) time.

> [!know]
> You now know how to delete from a binary search tree in all three cases, why replacing with the in-order successor keeps the order, and how to trim a tree to a range.

=== primer | How do you check that a binary tree really is a binary search tree? | 15 min
goal: Validate a BST by passing (low, high) bounds down, by checking that in-order is strictly increasing, or by returning subtree summaries up, and explain why comparing with children alone fails
tag: bst-bounds | Validation with bounds passed down
link: Wikipedia, Binary search tree | https://en.wikipedia.org/wiki/Binary_search_tree#Operations | 5 min: the opening definition and the "Operations" introduction, which states the invariant over whole subtrees that validation must check
practice: 98, 1373

> [!key]
> Being a BST is a property of **whole subtrees**: a node must be greater than *every* key on its left and smaller than *every* key on its right, so each node is constrained by all its ancestors, not just its parent. Pass the allowed open interval (low, high) down the tree, narrowing it at each step: going left sets high to the parent's key, going right sets low. Equivalent checks: the in-order sequence is strictly increasing, or each subtree reports its (min, max) upward.

## Intuition

A new employee is told "your salary must be below your manager's". That is a local rule, and it is not enough: a company also expects everyone in a department to earn less than its head, and everyone in the sister department to earn more than whatever separates the two. A rule from two levels up still binds you. The bounds are those inherited rules: each time you step down, you inherit your parent's constraints and add one new one.

## How it works

### Why children-only checks fail

```text
          10
         /  \
        5    15
            /  \
           6    20
```

Every node is consistent with its children: 5 < 10 < 15, and 6 < 15 < 20. But 6 sits in the right subtree of 10 and is smaller than 10, so a search for 6 would go left from the root and never find it. The tree is not a BST.

### Bounds passed down

`ok(node, low, high)` asks: are all keys in this subtree strictly between low and high, and is the subtree a BST? The root gets (-inf, inf). A node fails if its key is outside its interval; otherwise its left child gets (low, node.val) and its right child gets (node.val, high). By induction, every key ends up checked against the tightest bound from each ancestor, which is exactly the invariant. This is the "pass information down" pattern from the binary trees module.

### In-order must be strictly increasing

The in-order sequence of a BST is sorted (the next card proves it), and conversely a binary tree whose in-order sequence is strictly increasing is a BST. So walk in-order, remember the previous key, and fail on the first key that is not larger. The iterative walk can stop at the first violation.

### Summaries passed up

Each subtree can report (is_bst, min, max, sum). A node is the root of a BST exactly when both children are, `left.max < node.val < right.min`, with an empty child reporting (True, +inf, -inf, 0) so that it never blocks the comparison. This version answers richer questions in the same pass, such as "the largest key sum of any subtree that is a BST", where the bounds-down version cannot, because a subtree that fails inside a larger tree may still be a valid BST on its own.

### Equal keys and sentinel values

The definitions above are strict, so duplicates make the tree invalid; if your BST allows duplicates on one side, make that comparison non-strict. In Python, `float("-inf")` and `float("inf")` compare with any int. In Java or C++, do not use `Integer.MIN_VALUE` or `INT_MAX` as sentinels when keys can equal them; use nullable bounds or a 64-bit type.

## Cost

All three versions visit each node once with O(1) work: **O(n) time**. Space is O(h) for the recursion or the in-order stack. The children-only check is also O(n), which is why it is tempting, but it answers a different question.

A brute force that checks every node against every key in both of its subtrees is O(n h): O(n log n) balanced, O(n^2) on a chain. It is still worth writing as a stress-test oracle.

## When to use it

| Approach | Best when | Strength |
|---|---|---|
| Bounds passed down | you only need yes or no | stops at the first violation, simple proof |
| In-order strictly increasing | you are already walking in order (iterators, recovery) | reuses the iterative in-order loop |
| Summaries passed up | you need facts about every subtree (largest BST subtree, sums) | answers per-subtree questions in one pass |

The bounds pattern also builds trees: to rebuild a BST from its pre-order list in O(n), create nodes while the next value fits the current (low, high) window.

## Worked trace

`ok(node, low, high)` on the counterexample tree above:

```steps
ok(10, -inf, inf): 10 is inside (-inf, inf). The left child gets (-inf, 10) and the right child gets (10, inf)
    node 10   bounds (-inf, inf)    {{ok}}
---
ok(5, -inf, 10): 5 is inside. It is a leaf, so its empty children return True: the left subtree is valid
    node 5    bounds (-inf, 10)     {{ok}}
---
ok(15, 10, inf): 15 is inside. Its left child gets (10, 15), its right child (15, inf)
    node 15   bounds (10, inf)      {{ok}}
---
ok(6, 10, 15): 6 is NOT greater than 10. The bound came from the root, two levels up, which a children-only check never sees
    node 6    bounds {{(10, 15)}}       {{fails}}
---
The False propagates up through 15 and 10 (the and short-circuits, so 20 is never checked). The tree is not a BST
    result    {{False}}
```

## Template

```python
def is_bst(root):
    """Strict check: every key lies strictly inside the bounds set by its ancestors."""
    def ok(node, low, high):
        if node is None:
            return True
        if not low < node.val < high:
            return False
        return ok(node.left, low, node.val) and ok(node.right, node.val, high)

    return ok(root, float("-inf"), float("inf"))


def is_bst_inorder(root):
    """The same check via an iterative in-order walk: keys must strictly increase."""
    prev, stack, node = None, [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        if prev is not None and node.val <= prev:
            return False
        prev = node.val
        node = node.right
    return True


def max_sum_bst(root):
    """Largest key sum of any subtree that is a BST (0 for the empty subtree)."""
    best = 0

    def walk(node):
        """(is_bst, smallest key, largest key, key sum) of the subtree."""
        nonlocal best
        if node is None:
            return True, float("inf"), float("-inf"), 0
        l_ok, l_min, l_max, l_sum = walk(node.left)
        r_ok, r_min, r_max, r_sum = walk(node.right)
        if l_ok and r_ok and l_max < node.val < r_min:
            total = l_sum + node.val + r_sum
            best = max(best, total)
            return True, min(l_min, node.val), max(r_max, node.val), total
        return False, 0, 0, 0                # the other fields are never read

    walk(root)
    return best
```

## Pitfalls

- **Children-only comparison**: passes every test whose violations are one level deep and fails on the ones that matter.
- **Non-strict comparisons by accident**: `low <= node.val` accepts duplicates; decide on purpose.
- **Overflowing sentinels** in fixed-width languages, as described above.
- **Recursion depth**: a valid but skewed BST of 10^4 nodes is 10^4 deep; the iterative in-order version avoids the limit.
- **Empty child summaries**: if an empty child returned (True, 0, 0, 0), a node with value -5 and no left child would fail `0 < -5`. The infinities make empty children neutral.

## Check yourself

Q: Run `is_bst` on `[8, 3, 12, 1, 9]`. Which call fails, and with which bounds?
A: The root 8 gets (-inf, inf); 3 gets (-inf, 8); 1 gets (-inf, 3) and passes; 9, the right child of 3, gets (3, 8) and fails because 9 > 8. It is larger than its parent, as a right child should be, but it is inside the left subtree of 8.

Q: Why does checking that the in-order sequence strictly increases prove that the tree is a BST?
A: Take any node x. Its left subtree's keys appear immediately before x in the in-order sequence and its right subtree's keys immediately after it. If the whole sequence is strictly increasing, every left-subtree key is smaller than x and every right-subtree key is larger, which is the BST invariant at x. This holds for every x.

Q: To find the largest-sum subtree that is a BST, why can you not reuse `is_bst` on every node?
A: You could, but it would be O(n^2) on a chain (a full check per node), and the bounds version only says yes or no for the whole tree, not for each subtree. Returning (is_bst, min, max, sum) upward answers the question for every subtree in one O(n) pass.

Q: A Java solution uses `Integer.MIN_VALUE` and `Integer.MAX_VALUE` as initial bounds with strict comparisons. Which single-node input breaks it?
A: A tree whose only key is `Integer.MAX_VALUE` (or `Integer.MIN_VALUE`): the check `MIN < val < MAX` is false, so a valid one-node BST is rejected. Use `Long` bounds or null for "no bound".

## Lab

- **98**: bounds passed down. Expected: True for `[40, 20, 60, 10, 30, 50, 70]`, False for `[10, 5, 15, None, None, 6, 20]` and for `[8, 3, 12, 1, 9]`, False for `[2, 2, 2]` (strict), True for an empty tree; O(n) time. Check it against `is_bst_inorder` and a brute force on random trees.
- **1373**: summaries passed up. Expected: 24 for `[5, 2, 8, 1, 9, 6, 10]` (the whole tree fails because 9 sits left of 5, so the best is the subtree 8, 6, 10), 0 for `[-4, -6, -2]` (a valid BST with a negative sum loses to the empty subtree), and the full sum 280 for `[40, 20, 60, 10, 30, 50, 70]`; O(n) time. Compare with a brute force that validates and sums every subtree separately.

> [!know]
> You now know why a binary search tree must be validated against bounds from every ancestor, and three O(n) ways to check it: bounds down, in-order, and summaries up.

=== primer | Why does in-order traversal of a BST come out sorted, and how do you get the k-th smallest, a successor or an iterator? | 16 min
goal: Prove that in-order visits keys in increasing order, and use it for k-th smallest, successor and floor queries, an O(h)-memory iterator, and repairing two swapped keys
tag: bst-inorder | Sorted order from in-order traversal
link: MIT 6.006 (Spring 2020) Lecture 6 notes | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/376714cc85c6c784d90eec9c575ec027_MIT6_006S20_lec6.pdf | 10 min: "Traversal Order" and "Tree Navigation" (page 2): finding a node's successor and predecessor in O(h) with and without a right subtree
practice: 230, 173, 99

> [!key]
> In a BST, in-order (left, node, right) visits keys in **increasing order**, so every "sorted" question becomes a walk. Stop an iterative in-order after k pops for the **k-th smallest**; walk down from the root remembering the last left turn for the **successor**; keep the in-order stack in an object for an **iterator** with O(1) amortised `next` and O(h) memory; and look for **descents** in the in-order sequence to find keys that break the order.

## Intuition

A BST is a sorted list folded into a tree: the root is somewhere in the middle, everything smaller hangs to the left, everything larger to the right. Unfolding it means reading the left part completely, then the root, then the right part, at every level. That is exactly in-order. You can see it by squashing the tree flat: each key drops straight down onto a number line in sorted position.

```text
           40
         /    \
       20      60
      /  \    /  \
    10   30  50   70
    |    |   |    |
    10 20 30 40 50 60 70     in-order: the keys in sorted order
```

## How it works

### The proof

By induction on the size of the tree. An empty tree gives the empty sequence, which is sorted. For a node x, in-order is `in(x.left) + [x] + in(x.right)`. By the induction hypothesis both parts are sorted; by the invariant every key on the left is smaller than x and every key on the right is larger. So the concatenation is sorted.

### k-th smallest: stop early

Run the iterative in-order from the binary trees module and count pops; the k-th pop is the answer. The walk first descends the left spine (O(h)), then each pop is the next key, so it costs **O(h + k)**, not O(n). If you need many k-th queries on a changing tree, store the size of every subtree in its node (an **augmented** tree): at a node with left-subtree size L, the answer is the node if k = L + 1, in the left subtree if k <= L, and the (k - L - 1)-th of the right subtree otherwise. That is O(h) per query and is how order-statistic trees, and SortedList's positional index, answer `s[k]`.

### Successor, predecessor, floor and ceiling

The **successor** of a key is the smallest key larger than it. From the root: if the node's key is larger than the target, it is a candidate, and a smaller candidate can only be in its left subtree, so record it and go left; otherwise go right. The last candidate recorded is the answer. The **ceiling** (smallest key >= x) uses `>=` instead of `>`; the **predecessor** and **floor** mirror both. Each is one path: O(h). With parent pointers, the successor of a given node is the leftmost node of its right subtree if it has one, otherwise its first ancestor that it reaches from the left.

### An iterator that pauses

An iterator must return the next key on each call without walking the whole tree up front. Keep the in-order stack as state: the constructor pushes the left spine from the root; `next` pops a node, pushes the left spine of its right child, and returns the popped key. Memory is the stack, O(h). Over a full iteration each node is pushed once and popped once, so n calls cost O(n) in total: **O(1) amortised** per call, even though a single call can push O(h) nodes. This is the pattern behind iterators in std::map, TreeMap and database cursors.

### Repairing two swapped keys

If two keys of a BST were swapped by mistake, the in-order sequence is sorted except for those two. Swapping neighbours creates one **descent** (a place where a key is followed by a smaller one); swapping distant keys creates two. The first wrong key is the larger key of the first descent, and the second is the smaller key of the last descent. Find them in one in-order pass and swap their values back.

## Cost

| Operation | Time | Extra space |
|---|---|---|
| full in-order | O(n) | O(h) |
| k-th smallest by early stopping | O(h + k) | O(h) |
| k-th smallest with subtree sizes | O(h) | O(1) per node, kept up to date on insert and delete |
| successor, floor, ceiling from the root | O(h) | O(1) |
| iterator, n calls to next | O(n) total, O(1) amortised each | O(h) |
| recover two swapped keys | O(n) | O(h) (O(1) with Morris traversal) |

## When to use it

Any question about a BST that mentions order: the smallest, the k-th, the next, ranks, adjacent differences, merging two BSTs, or "visit keys from largest to smallest" (reverse in-order: right, node, left, which also solves "replace each key by the sum of all keys greater than or equal to it"). If you only need the k-th smallest of a fixed array, quickselect or a heap is cheaper than building a tree; if the set changes and k-th queries are frequent, an augmented or library structure is worth it.

## Worked trace

`BSTIterator` on `[40, 20, 60, 10, 30, 50, 70]`, calling `next` until the stack is empty:

```steps
Constructor: push the left spine from the root: 40, 20, 10
    stack   [40, 20, {{10}}]
    output  []
---
next(): pop 10 and return it. 10 has no right child, so nothing is pushed
    stack   [40, 20]
    output  [{{10}}]
---
next(): pop 20. Push the left spine of its right child: just 30
    stack   [40, {{30}}]
    output  [10, {{20}}]
---
next(): pop 30 (no right child)
    stack   [40]
    output  [10, 20, {{30}}]
---
next(): pop 40. Push the left spine of 60: 60, then 50. This call did the most work: two pushes
    stack   [{{60}}, {{50}}]
    output  [10, 20, 30, {{40}}]
---
next() three more times: pop 50; pop 60 and push 70; pop 70. The stack is empty, so has_next() is False
    stack   []
    output  [10, 20, 30, 40, {{50}}, {{60}}, {{70}}]
```

Seven pushes and seven pops for seven keys: O(1) amortised per call, and the stack never held more than 3 nodes, the height.

## Template

```python
def kth_smallest(root, k):
    """k-th smallest key (1-based), by stopping the in-order walk after k pops."""
    stack, node = [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        node = node.right
    raise ValueError("k is larger than the number of keys")


def successor(root, key):
    """Smallest key strictly greater than key, or None. O(h), no parent pointers."""
    best, node = None, root
    while node:
        if node.val > key:
            best = node.val          # a candidate; a smaller one can only be on the left
            node = node.left
        else:
            node = node.right
    return best


class BSTIterator:
    """Keys in increasing order; next() is O(1) amortised and memory is O(h)."""

    def __init__(self, root):
        self.stack = []
        self._push_left(root)

    def _push_left(self, node):
        while node:
            self.stack.append(node)
            node = node.left

    def has_next(self):
        return bool(self.stack)

    def next(self):
        node = self.stack.pop()
        self._push_left(node.right)
        return node.val


def recover(root):
    """Two keys were swapped: find them in one in-order pass and swap them back."""
    first = second = prev = None
    stack, node = [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        if prev is not None and prev.val > node.val:    # a descent
            if first is None:
                first = prev                             # larger key of the first descent
            second = node                                # smaller key of the latest descent
        prev = node
        node = node.right
    first.val, second.val = second.val, first.val
```

LeetCode's version of the iterator names the methods `hasNext` and `next`; the logic is the same.

## Pitfalls

- **Collecting everything first**: building the full in-order list and indexing `[k - 1]` is O(n) time and memory, and it does not answer the iterator problem's O(h) memory requirement.
- **Off by one in k**: k is 1-based in most statements; decrement before comparing, as in the template.
- **Successor with `>=`**: that is the ceiling, which returns the key itself when present. Read whether "next" means strictly larger.
- **Recovering with only one descent**: when the swapped keys are adjacent in order, there is only one descent, and both nodes come from it; setting `second` at every descent handles both cases.
- **Changing the tree under an iterator**: inserting or deleting while an iterator holds a stack can make it skip or repeat keys, the same reason Python forbids changing a dict's size during iteration.

## Check yourself

Q: In the iterator trace, how many nodes are on the stack right after `next()` returns 40, and what will the next two calls return?
A: Two: 60 and 50 (50 on top). The next call pops 50 and returns it (no right child); the one after pops 60, pushes 70 and returns 60.

Q: Why is `next()` O(1) amortised even though one call can push h nodes?
A: Every node is pushed exactly once (when the walk first reaches it on some left spine) and popped exactly once (when it is returned). Over a full iteration of n calls that is n pushes and n pops in total, O(n), so the average per call is O(1), however unevenly the pushes are spread.

Q: The in-order sequence of a BST with two swapped keys is `[10, 20, 60, 40, 50, 30, 70]`. Which keys were swapped, and how does the algorithm find them?
A: 30 and 60. There are two descents: 60 > 40 and 50 > 30. The first wrong key is the larger element of the first descent (60); the second is the smaller element of the last descent (30). Swapping them back gives 10 20 30 40 50 60 70.

Q: You need the k-th smallest key 10^5 times while keys are also being inserted and deleted. What do you change, and what does each query then cost?
A: Store in every node the size of its subtree and update it along the path on each insert and delete. A query then walks one path, comparing k with the left subtree's size at each node: O(h) per query, O(log n) if the tree is balanced. In Python, `SortedList` gives the same with `s[k - 1]` in about O(log n).

## Lab

- **230**: k-th smallest by early stopping. Expected on `[40, 20, 60, 10, 30, 50, 70]`: k = 1 gives 10, k = 4 gives 40, k = 7 gives 70; O(h + k) time, O(h) space.
- **173**: the iterator. Expected: on the same tree the calls return 10, 20, 30, 40, 50, 60, 70 and then `hasNext` is False; the stack never exceeds the height (3 here). Check with a counter that the total number of pushes equals the number of keys.
- **99**: recover two swapped keys. Expected: swapping 30 and 60 in the same tree (giving in-order `[10, 20, 60, 40, 50, 30, 70]`) is repaired to in-order `[10, 20, 30, 40, 50, 60, 70]`; swapping the adjacent keys 40 and 50 (one descent) is repaired as well; O(n) time, O(h) space.

> [!know]
> You now know why in-order traversal of a binary search tree is sorted and how to use it for k-th smallest, successors, iterators and repairing swapped keys.

=== primer | Why does the shape of a BST decide its speed, and how bad can it get? | 14 min
goal: Predict the height of a plain BST for sorted and random insertion orders, measure it, and build a perfectly balanced tree from sorted keys in O(n)
tag: bst-balance | Balanced build from sorted keys
link: VisuAlgo, Binary Search Tree | https://visualgo.net/en/bst | 10 min, interactive: insert 1, 2, 3, 4, 5, 6, 7 into the plain BST and watch the chain form, then switch to AVL mode and insert the same keys
link: Sedgewick and Wayne, algs4 3.2 Binary Search Trees | https://algs4.cs.princeton.edu/32bst/ | 5 min: the "Analysis" paragraph (random keys give about 1.39 lg N compares) and the best-case, typical and worst-case pictures
practice: 108

> [!key]
> Every BST operation costs O(h), and h depends only on the **insertion order**. Random order gives a height of a small multiple of log2 n (measured: about 47 for a million keys, against 20 for a perfect tree), but sorted or nearly sorted input gives a **chain of height n**, turning every operation into a linear scan and n inserts into O(n^2). If you have the keys up front, build the tree from the sorted list by always choosing the **middle** key as the root: height ceil(log2(n + 1)), in O(n).

## Intuition

A BST is a binary search whose pivots were chosen by whoever inserted first. The first key inserted becomes the root forever (in a plain BST), so if it is the smallest key, the whole rest of the data goes to one side. Insert 1, 2, 3, ... and each new key is the largest so far: it walks to the bottom of the right spine and hangs off the end. You have built a linked list with extra pointers.

Real data loves to arrive sorted: timestamps, auto-increment ids, log lines, files that were sorted by a previous job. That is why the plain BST is a teaching structure, and why the next card exists.

## How it works

### Heights you should expect

| Insertion order | Height of n keys | Cost of n inserts | Cost of one search |
|---|---|---|---|
| sorted or reverse sorted | n | about n^2 / 2 comparisons | up to n |
| random | measured below: about 2 to 2.5 times log2 n | O(n log n) expected | about 1.39 log2 n on average |
| built from sorted keys, middle first | ceil(log2(n + 1)) | O(n) to build | at most log2 n + 1 |

Measured with an iterative insert in CPython (mean over five random orders, one for a million):

| n | log2 n | height, random order | height, sorted order |
|---|---|---|---|
| 1,000 | 10.0 | 22 | 1,000 |
| 10,000 | 13.3 | 32 | 10,000 |
| 100,000 | 16.6 | 41 | 100,000 |
| 1,000,000 | 19.9 | 47 | 1,000,000 |

The average search depth of a random BST is about 2 ln n, roughly 1.39 log2 n, the same as the number of comparisons quicksort makes per element with random pivots: the root of a random BST is a random pivot, and each subtree is the same story recursively. The height (the worst node) is larger, but still logarithmic.

### Building a balanced tree from sorted keys

Pick the middle key as the root, then build the left half and the right half recursively. Each subtree gets a contiguous slice of the sorted keys, so the result is a BST, and sizes of the two halves differ by at most one at every node, so the height is the minimum possible. Use indices, not slices, to keep it O(n).

The same idea **rebalances** any BST: read its keys in-order into a list (O(n)), then rebuild from the middle. Scapegoat trees do exactly that, rebuilding a subtree only when it becomes too lopsided, which keeps the height logarithmic with amortised O(log n) updates and no rotations at all.

### Dealing with unknown order

If you cannot control the order, you have three options: shuffle the keys first if you have them all (random order, expected logarithmic height), use a self-balancing tree (next card), or use a structure that does not care about order at all (a sorted array with bisect for mostly static data, SortedList in Python).

## Cost

Inserting the keys 1..n in order into a plain BST costs 0 + 1 + 2 + ... + (n - 1) = n(n - 1)/2 comparisons: O(n^2). For n = 100,000 that is about 5 * 10^9 comparisons, minutes in CPython. Doubling n quadruples the time, which is the signature to look for in a benchmark.

The balanced build makes one node per key with O(1) work: **O(n) time**, O(log n) recursion depth.

## When to use it

- You receive sorted data and need a tree (a sorted array or list "converted to a BST", a static index built once): build from the middle.
- A tree has become lopsided and you can afford one O(n) pass: in-order to a list, then rebuild.
- You are benchmarking or testing any search tree: always include sorted, reverse-sorted and nearly-sorted inputs, not just random ones, because random data hides the worst case.

## Worked trace

Insert the same five keys in two orders:

```steps
Sorted order. Insert 10, then 20: 20 > 10, so it becomes the right child. One comparison
    10
      \
       {{20}}
---
Insert 30 and 40: each is larger than every key so far and walks the whole right spine: 2, then 3 comparisons
    10
      \
       20
         \
          30
            \
             {{40}}
---
Insert 50: 4 more comparisons. Height 5 for 5 keys: a linked list. Total 0 + 1 + 2 + 3 + 4 = 10 comparisons, and a search for 50 visits every node
    10
      \
       20
         \
          30
            \
             40
               \
                {{50}}
---
Same keys, middle first: insert 30, then 10 and 40 (one comparison each)
         {{30}}
        /    \
      {{10}}      {{40}}
---
Insert 20 and 50 (two comparisons each). Height 3, total 0 + 1 + 1 + 2 + 2 = 6 comparisons. With n keys the gap grows to n^2/2 versus about n log2 n
         30
        /    \
      10      40
        \       \
        {{20}}      {{50}}
```

## Template

```python
def build_balanced(keys):
    """Height-balanced BST from a sorted list of distinct keys: the middle key is the root."""
    def build(lo, hi):                       # the keys in keys[lo:hi]
        if lo >= hi:
            return None
        mid = (lo + hi) // 2
        return TreeNode(keys[mid], build(lo, mid), build(mid + 1, hi))

    return build(0, len(keys))


def insert_iterative(root, key):
    """Plain BST insert without recursion, safe on degenerate trees. Returns the root."""
    new = TreeNode(key)
    if root is None:
        return new
    node = root
    while True:
        if key < node.val:
            if node.left is None:
                node.left = new
                return root
            node = node.left
        elif key > node.val:
            if node.right is None:
                node.right = new
                return root
            node = node.right
        else:
            return root                      # duplicate: ignore


def height_iterative(root):
    """Number of levels, without recursion."""
    best, stack = 0, [(root, 1)] if root else []
    while stack:
        node, depth = stack.pop()
        best = max(best, depth)
        for child in (node.left, node.right):
            if child:
                stack.append((child, depth + 1))
    return best


chain = None
for key in range(1, 2001):
    chain = insert_iterative(chain, key)
print(height_iterative(chain), height_iterative(build_balanced(list(range(1, 2001)))))   # 2000 11
```

## Pitfalls

- **Testing only on random data**: the plain BST looks logarithmic until production feeds it sorted ids.
- **Recursive operations on the chain**: a recursive insert or traversal of a sorted-input tree with more than about 1000 keys raises RecursionError in Python before it even gets slow.
- **Slicing in the balanced build**: `build(keys[:mid])` copies, making the build O(n log n) time and memory; pass indices.
- **Unsorted input to the balanced build**: it silently produces a tree that is balanced but not a BST. Sort first, or assert sortedness in tests.
- **Rebalancing too often**: an O(n) rebuild after every insert makes inserts O(n). Rebuild only when the height exceeds a threshold such as 2 log2 n, as scapegoat trees do.

## Check yourself

Q: What does `build_balanced([1, 2, 3, 4, 5, 6])` produce, in level order?
A: The middle index of 0..6 is 3, so the root is 4. The left part [1, 2, 3] has middle 2, with children 1 and 3. The right part [5, 6] has middle index (4 + 6) // 2 = 5, key 6, with left child 5. Level order: `[4, 2, 6, 1, 3, 5]`, height 3.

Q: Why is inserting n sorted keys into a plain BST Theta(n^2), not just O(n^2)?
A: The i-th key is larger than all i - 1 keys before it, which form a chain along the right spine, so its insert must compare with every one of them: exactly i - 1 comparisons. The total is n(n - 1)/2, so the bound is tight.

Q: You must build a BST index once from 10^6 records that arrive sorted by key, then serve lookups only. Plain inserts, shuffled inserts, or the balanced build?
A: The balanced build: O(n) time and the minimum possible height (20 levels). Plain inserts would take about 5 * 10^11 comparisons and produce a chain; shuffled inserts would work (expected height around 47) but cost O(n log n) and give a taller tree. For lookups only, a sorted list with bisect is simpler still.

Q: A colleague's benchmark shows the plain BST "as fast as SortedList" for 10^5 inserts. What should you ask about the input?
A: Whether the keys were in random order. Random order gives a tree of height around 41 at that size, so the plain BST looks fine; on sorted or nearly sorted keys it degrades to a chain and needs about 5 * 10^9 comparisons. Ask for sorted, reverse-sorted and nearly-sorted runs too.

## Lab

- **108**: balanced build from a sorted array. Expected: `[10, 20, 30, 40, 50, 60, 70]` gives level order `[40, 20, 60, 10, 30, 50, 70]` with the template's middle choice (other balanced answers are also accepted); `[1, 2]` gives `[2, 1]`; the height for 2000 keys is 11; O(n) time.
- **Degenerate versus balanced**: insert 1..2000 with `insert_iterative` and with the recursive insert from the first card. Expected: height 2000 for the iterative version, a `RecursionError` from the recursive one, and height 11 for `build_balanced(list(range(1, 2001)))`. Then time n = 1000, 2000, 4000, 8000 sorted inserts: each doubling should take about four times as long.

> [!know]
> You now know why insertion order decides a binary search tree's height, what heights to expect, and how to build or rebuild a perfectly balanced tree in O(n).

=== primer | How do AVL trees, red-black trees, treaps and B-trees keep the height logarithmic? | 18 min
goal: State the invariant and height bound of AVL, red-black, treap and B-tree designs, explain how rotations and splits restore them without breaking the order, and check the invariants in code
link: MIT 6.006 (Spring 2020) Lecture 7 notes, AVL trees | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/a2c80596cf4a2b5fbc854afdd2f23dcb_MIT6_006S20_lec7.pdf | 20 min: pages 1-3: "Height Balance", "Rotations", "Rotations Suffice" and "AVL Trees: Height Balance" with the three rebalancing cases
link: Sedgewick and Wayne, algs4 3.3 Balanced Search Trees | https://algs4.cs.princeton.edu/33balanced/ | 20 min: "2-3 search trees", then "Red-black BSTs": a red-black tree is a 2-3 tree drawn with binary nodes, which explains its rules

> [!key]
> A self-balancing tree adds a second invariant that forces the height to be O(log n), and repairs it after every update with **local** fixes that preserve the in-order sequence. AVL trees keep sibling subtree heights within 1 (height under 1.44 log2 n); red-black trees forbid two reds in a row and equalise black counts (height at most 2 log2(n + 1)); treaps make the shape random by heap-ordering random priorities (expected O(log n)); B-trees keep many keys per node and all leaves at the same depth (height about log base t of n). Binary trees repair with **rotations**, B-trees with **splits and merges**.

## Intuition

A rotation is the BST version of changing which person in a line you call "the middle". Take a parent y with left child x. Making x the parent and y its right child changes the shape, but if you read the keys left to right they are still in the same order, because only who-sits-above-whom changed, not who-sits-left-of-whom:

```text
          y                         x
         / \     rotate right      / \
        x   C    ----------->     A   y
       / \       <-----------        / \
      A   B      rotate left        B   C

    in-order on both sides: A  x  B  y  C
```

A, B and C are whole subtrees. Rotating right lifts A by one level and lowers C by one; B just changes parent. Three pointer assignments, O(1), and the BST invariant survives. Every balanced binary tree is "a BST plus a rule about shape, plus rotations to restore the rule".

## How it works

### AVL trees: heights within one

**Invariant**: at every node, the heights of the two subtrees differ by at most 1. Each node stores its height. After an insert or delete, walk back up the changed path updating heights; at the first node whose two heights differ by 2, one **single** rotation (when the heavy child leans the same way) or one **double** rotation (when it leans the other way: rotate the child first, then the node) restores the rule. After an insertion one such fix is enough; a deletion may need one per level.

**Why the height is logarithmic**: let N(h) be the fewest nodes an AVL tree of height h can have. Its two subtrees must have heights h - 1 and (at least) h - 2, so N(h) = 1 + N(h - 1) + N(h - 2), the Fibonacci recurrence. Fibonacci numbers grow like 1.618^h, so n >= 1.618^h roughly, giving h < 1.44 log2(n + 2).

### Red-black trees: colours

**Invariant**: every node is red or black; the root is black; empty children count as black; a red node never has a red child; and every path from a node down to an empty child passes through the same number of black nodes (its black-height). The black nodes alone form a perfectly balanced skeleton, and reds can at most double a path's length (no two in a row), so **h <= 2 log2(n + 1)**. Repairs are recolourings plus at most two rotations per insert and three per delete, fewer than AVL, at the price of a slightly taller tree. That trade (cheaper updates, slightly slower lookups) is why general-purpose libraries chose it: Java's `TreeMap` is documented as red-black, C++'s `std::map` is usually one, and the Linux kernel uses rbtrees for timers and I/O schedulers. A red node can be read as glued to its black parent, making a node with 2 or 3 keys: red-black trees are B-trees with at most 3 keys per node in disguise.

### Treaps: let randomness balance

Give every key a **random priority** at insertion. **Invariant**: keys obey BST order, and priorities obey heap order (a parent's priority beats its children's). For distinct keys and priorities the tree is unique: it is exactly the plain BST you would get by inserting the keys in priority order, which is a random order. So the shape is a random BST whatever order the keys arrive in: expected depth about 1.39 log2 n, no worst case an adversary can force without seeing the random numbers. Insert as a leaf, then rotate it up while its priority beats its parent's. Treaps also support **split** (by key) and **merge** in expected O(log n), which makes range operations easy.

### B-trees: wide nodes, level leaves

Each node holds many sorted keys and one more child than keys. With minimum degree t, every node except the root holds between t - 1 and 2t - 1 keys, and **all leaves are at the same depth**. Insert into a leaf; if it overflows, **split** it around its median and push the median up into the parent, which may split in turn. The tree grows only by splitting the root, which is why the leaves stay level. Height is at most about log base t of n: with hundreds of keys per node, three or four levels hold billions of keys. Each node is sized to a disk page or a few cache lines, so one node visit is one I/O. Deletions **borrow** from or **merge** with a sibling. The last card of this module shows how databases use the B+ variant.

### Comparing them

| Design | Invariant | Height | Repair per update | Where you meet it |
|---|---|---|---|---|
| AVL | sibling heights differ by at most 1 | under 1.44 log2(n + 2) | one single or double rotation per insert | read-heavy in-memory indexes, teaching |
| Red-black | no red-red, equal black-heights | at most 2 log2(n + 1) | recolour, at most 2 or 3 rotations | Java TreeMap, C++ std::map, Linux kernel rbtree |
| Treap | BST by key, heap by random priority | expected O(log n) | rotate by priority | randomised ordered sets, split and merge |
| B-tree, B+ tree | t - 1 to 2t - 1 keys per node, level leaves | about log base t of n | split, borrow, merge | databases, file systems, Rust's BTreeMap |
| Skip list | random tower heights | expected O(log n) levels | none, coin flips | Redis sorted sets up to 8.10, LevelDB memtables |

## Cost

All of them make search, insert, delete, floor, ceiling and successor **O(log n)** (worst case for AVL, red-black and B-trees; expected for treaps and skip lists). A rotation is O(1) and the fix-up walk O(log n). Augmentations (subtree sizes, sums, interval maxima) survive rotations because only two nodes' subtrees change, so their summaries are recomputed in O(1): that is how order-statistic and interval trees stay O(log n).

## When to use it

You almost never write one: use the language's ordered map (C++ `std::map`, Java `TreeMap`, Rust `BTreeMap`) or, in Python, `sortedcontainers` (next card). Know the ideas to predict costs and pick variants: AVL when lookups dominate, red-black for general use, treaps for split and merge, B-trees whenever a node visit is expensive (disk pages, cache misses).

## Worked trace

Insert 1 to 7 in order into an AVL tree. A plain BST would become a chain of height 7:

```steps
Insert 1, 2, 3. Node 1 now has an empty left subtree (height 0) and a right subtree of height 2: the rule is broken at 1
    1
     \
      2
       \
        {{3}}
---
The heavy side leans the same way all the way down (right, right), so one left rotation at 1 fixes it. In-order is still 1 2 3
      {{2}}
     / \
    1   3
---
Insert 4: heights at 3 are 0 and 1, at 2 they are 1 and 2. Still within one everywhere, no rotation
      2
     / \
    1   3
         \
          {{4}}
---
Insert 5: node 3 has heights 0 and 2. Rotate left at 3: 4 moves up with children 3 and 5
      2
     / \
    1   {{4}}
       / \
      3   5
---
Insert 6: now the root is unbalanced (left height 1, right height 3). Rotate left at 2: 4 becomes the root, and 3 moves across to be 2's right child
        {{4}}
       / \
      2   5
     / \   \
    1   3   6
---
Insert 7: node 5 has heights 0 and 2. Rotate left at 5. Four rotations in all, and the result is the perfect tree of height 3
        4
       / \
      2   {{6}}
     / \ / \
    1  3 5  7
```

## Template

```python
import math


def avl_height(node):
    """Height of the subtree if every node's two subtree heights differ by at most 1, else -1."""
    if node is None:
        return 0
    left, right = avl_height(node.left), avl_height(node.right)
    if left < 0 or right < 0 or abs(left - right) > 1:
        return -1
    return 1 + max(left, right)


def black_height(node):
    """Black-height of a subtree whose nodes have a boolean .red, or -1 if a colour rule is broken."""
    if node is None:
        return 1                                   # empty children count as black
    if node.red and any(c is not None and c.red for c in (node.left, node.right)):
        return -1                                  # a red node with a red child
    left, right = black_height(node.left), black_height(node.right)
    if left < 0 or left != right:
        return -1                                  # unequal black counts below this node
    return left + (0 if node.red else 1)


def is_red_black(root):
    return (root is None or not root.red) and black_height(root) > 0


def min_avl_nodes(h):
    """Fewest nodes in an AVL tree of height h: N(h) = 1 + N(h - 1) + N(h - 2)."""
    if h == 0:
        return 0
    a, b = 0, 1                                    # N(0), N(1)
    for _ in range(h - 1):
        a, b = b, 1 + a + b
    return b


def max_avl_height(n):
    """Tallest AVL tree that n nodes can form."""
    h = 0
    while min_avl_nodes(h + 1) <= n:
        h += 1
    return h


print([min_avl_nodes(h) for h in range(1, 11)])   # [1, 2, 4, 7, 12, 20, 33, 54, 88, 143]
print(max_avl_height(10**6), math.ceil(math.log2(10**6 + 1)))   # 28 20
```

These checkers are what you would run after every operation in a property test of your own balanced tree (combined with the BST check from the validation card): they test the invariant, not the implementation.

## Pitfalls

- **Rotating without updating heights or colours**: the shape changes but the stored heights become stale, and the next fix-up makes the wrong decision. Recompute the two rotated nodes bottom-up.
- **Single rotation in the zig-zag case**: when the heavy child leans the other way (left child with a heavy right side), one rotation just moves the imbalance to the other side. It needs the double rotation.
- **Forgetting the parent link**: after rotating a subtree, its parent (or the root pointer) must point to the new subtree root. The "return the new subtree root" style from insert and delete makes this automatic.
- **Treating "balanced" as "perfect"**: AVL and red-black trees allow some lopsidedness; their height bounds are about 1.44 and 2 times the perfect height, not equal to it.
- **Using a binary tree for on-disk data**: a lookup in a balanced binary tree of 10^9 keys visits about 30 nodes, each potentially a separate disk read; a B-tree visits 3 or 4.

## Check yourself

Q: Insert 3, then 1, then 2 into an empty AVL tree. Which node is unbalanced, which rotation fixes it, and what is the result?
A: After inserting 2, node 3 has a left subtree of height 2 (1 with right child 2) and an empty right subtree. The heavy child 1 leans right while 3 leans left: the zig-zag case. Rotate left at 1 (making 2 the left child of 3, with 1 below it), then rotate right at 3. The result is 2 with children 1 and 3.

Q: Why can a red-black tree's height never exceed twice the minimum possible height?
A: Every root-to-empty path has the same number b of black nodes, so the black nodes alone form a perfectly balanced skeleton and the tree has at least 2^b - 1 nodes, giving b <= log2(n + 1). Reds cannot be adjacent, so at most every other node on a path is red and a path has at most 2b nodes. Hence h <= 2 log2(n + 1).

Q: Why does a treap's expected height not depend on the order in which the keys arrive?
A: The shape of a treap is determined by the keys and their priorities alone: it equals the plain BST obtained by inserting the keys in order of priority. Priorities are random and independent of the keys, so that order is a uniformly random permutation, and a BST built from a random permutation has expected O(log n) height whatever order the keys were originally given in.

Q: A database stores 10^9 keys. Compare the number of node visits for one lookup in a red-black tree and in a B-tree whose nodes hold about 500 keys.
A: The red-black tree has height between 30 and at most 2 log2(10^9 + 1), about 60, so 30 to 60 node visits, each possibly a random disk read. The B-tree has height about log base 250 to 500 of 10^9, which is 4 levels at most, and the top levels are usually cached in memory, so one or two disk reads. That gap is why disk-based indexes are B-trees.

## Lab

- **By hand, AVL**: insert 1 to 7 in order. Expected: 4 single left rotations (after inserting 3, 5, 6 and 7), final level order `[4, 2, 6, 1, 3, 5, 7]`, height 3. Then insert 3, 1, 2 into an empty tree. Expected: one double rotation and the tree `[2, 1, 3]`. Check your drawings on VisuAlgo in AVL mode.
- **Height bounds**: run the template. Expected: `[1, 2, 4, 7, 12, 20, 33, 54, 88, 143]` and `28 20`: a million-key AVL tree is at most 28 levels deep, against 20 for a perfect tree and at most 39 for a red-black tree (2 log2(n + 1) is about 39.9).
- **Colour rules**: give `TreeNode` a `red` attribute and check three small trees with `is_red_black`. Expected: True for a black root with two red children, False when one of those red children gets a red child of its own, and False when the root itself is red.

> [!know]
> You now know the invariants and height bounds of AVL, red-black, treap and B-tree designs, how rotations and splits restore them without changing the order, and how to test the invariants.

=== primer | Which ordered map should you use in Python, and why does SortedList beat a balanced tree there? | 16 min
goal: Answer floor, ceiling, rank and range queries with bisect on a list or sortedcontainers, map them to C++ std::map and Java TreeMap, and explain with measurements why a list of sorted lists outruns a tree in CPython
tag: bst-ordered | Ordered sets: floor, ceiling and ranges
link: Sorted Containers, Implementation Details | https://grantjenks.com/docs/sortedcontainers/implementation.html | 10 min, the whole (short) page: the _lists, _maxes and _index variables, the load factor of 1,000, and the four reasons a list of lists beats a tree in Python
link: Python docs, bisect | https://docs.python.org/3/library/bisect.html#searching-sorted-lists | 5 min: the "Searching Sorted Lists" recipes find_lt, find_le, find_gt and find_ge, which are predecessor, floor, successor and ceiling
practice: 220

> [!key]
> Python has no built-in balanced tree, and in CPython you rarely want one. For mostly static data, keep a **sorted list** and use `bisect` for floor, ceiling and ranges in O(log n). For data that changes, use `sortedcontainers.SortedList`: a **list of sorted sublists** of about 1,000 items with an index of their maxima, so every operation is two C-level binary searches plus a short `memmove`. It is B-tree-like with two levels, and it beats pointer-based trees in Python on speed and memory: measured here, about twice as fast as even an unbalanced, randomly built BST, with 8 bytes per key against 56.

## Intuition

A balanced tree promises O(log n) by doing a little interpreted work at each of about log2 n levels: load an attribute, compare, branch, follow a pointer to a node somewhere else in memory. In CPython each of those steps is a bytecode instruction costing tens of nanoseconds. `bisect` does the same comparisons inside a C loop over a contiguous array of pointers, and shifting a thousand pointers with `memmove` takes well under a microsecond on modern hardware. So the structure with the "worse" big-O (an O(m) insert into a sublist of length m) wins, because its constant factor is two orders of magnitude smaller. Grant Jenks's docs put it bluntly: tree-based designs have better big-O, "but that ignores the realities of today's software and hardware".

## How it works

### The ordered-set interface

Whatever the implementation, you want: add, remove, contains, minimum and maximum, **floor** (largest key <= x), **ceiling** (smallest key >= x), predecessor and successor (strict versions), **rank** (how many keys are smaller) and **select** (the k-th key), and **range iteration** (all keys in [lo, hi] in order).

| Need | Python | C++ | Java |
|---|---|---|---|
| ordered set or map | `SortedList`, `SortedDict` (sortedcontainers) | `std::set`, `std::map` (usually red-black) | `TreeSet`, `TreeMap` (red-black) |
| ceiling, smallest >= x | `s[s.bisect_left(x)]` | `s.lower_bound(x)` | `ceiling(x)`, `ceilingKey(x)` |
| successor, smallest > x | `s[s.bisect_right(x)]` | `s.upper_bound(x)` | `higher(x)` |
| floor, largest <= x | `s[s.bisect_right(x) - 1]` | `prev(s.upper_bound(x))` | `floor(x)` |
| k-th smallest, rank | `s[k]`, `s.bisect_left(x)` in O(log n) | not built in (policy-based trees in GCC) | not built in |
| range | `s.irange(lo, hi)` | `lower_bound` then iterate | `subSet(lo, true, hi, true)` |
| only the minimum, repeatedly | `heapq` | `std::priority_queue` | `PriorityQueue` |

(Check the index is in range before reading `s[...]`; the floor of a key below the minimum, for example, does not exist.)

### Option 1: a plain sorted list with bisect

`bisect_left(a, x)` is the first index with `a[i] >= x` (ceiling position); `bisect_right(a, x)` the first with `a[i] > x`, so `bisect_right(a, x) - 1` is the floor. Queries are O(log n) in C. Inserting with `bisect.insort` is O(log n) to find the spot plus O(n) to shift the tail: perfectly fine for a few thousand updates, or when keys arrive mostly in increasing order (appending at the end shifts nothing), and painful for 10^5 random inserts into a growing list (measured below: about 3 seconds).

### Option 2: SortedList, a list of lists

From the implementation notes: `_lists` holds sorted sublists, `_maxes` holds the maximum of each sublist, and `_index` is a lazily built tree of sublist lengths for positional queries. To add x: bisect `_maxes` to choose the sublist, `insort` into it, and if the sublist grows past twice the load factor (default 1,000), split it in half. Removal shrinks sublists and merges a sublist that falls below half the load with a neighbour. Lookup is two bisects. Positional access `s[k]` walks the `_index` tree (children of position i at 2i + 1 and 2i + 2, like a heap) in O(log(n/m)).

The library's analysis gives an amortised O(n^(1/3)) insert when the load is about the cube root of n, technically worse than O(log n). In practice, as the docs argue, log2 of a billion is about 30 while the cube root is 1,000: the list of lists only needs to be about 33 times faster per step, and in CPython it is.

### Why trees lose in Python

The implementation page lists four advantages, and you can measure each:

1. **Fewer allocations**: most inserts and deletes allocate nothing; a tree allocates a node per key.
2. **Dense pointers**: a sublist is a C array of pointers; a tree node with `__slots__` is a 56-byte object (measured with `tracemalloc`: 56 bytes per key for a plain BST against 8 to 9 for SortedList, not counting the keys themselves).
3. **One pointer per item**, against at least two child pointers per node.
4. **Fast iteration**: walking contiguous arrays is what CPUs do best.

Add the interpreter: every level of a Python tree costs several bytecode instructions, while bisect runs in C.

## Cost

Measured on 10^5 random integer keys in CPython 3.12 (median of three runs on a shared server; your absolute numbers will differ, the ratios should not):

| Structure | Build by 10^5 adds | 10^5 membership lookups | Memory per key |
|---|---|---|---|
| plain BST, random order (no rebalancing at all) | 0.51 s | 0.41 s | 56 bytes |
| SortedList | 0.32 s | 0.19 s | 8 to 9 bytes |
| list + `bisect.insort` | 3.0 s | 0.22 s | 8 bytes |
| set (no order) | 0.02 s | 0.03 s | about 42 bytes (hash table slots) |

A real balanced tree in Python would be slower than the plain BST row, since it does the same walk plus rebalancing work. On sorted input the plain BST collapses (8,000 sorted keys already take about 4 seconds), `insort` becomes fast (0.05 s, since every insert is an append), and SortedList stays fast (0.11 s).

## When to use it

- Static data, many queries: sorted list + `bisect`.
- Changing data with order queries (floor, ceiling, k-th, ranges): `SortedList` or `SortedDict`. It is a third-party package, missing from some judges and interview environments, so also know the `bisect` fallback and how to describe a balanced tree.
- Only the minimum or maximum, repeatedly: `heapq` (O(log n) push and pop, much lighter).
- Membership only: `set` or `dict`, by an order of magnitude.
- Sliding windows that need "is any value within d of x?": an ordered set of the window, or buckets of width d + 1 (each value can only collide with its own bucket and the two neighbours), which is O(n) overall.

## Worked trace

SortedList internals with the load factor shrunk to 2 for the picture (sublists split when they exceed 2 x 2 = 4 items; the real default is 1,000). These states are what the library really produces:

```steps
Add 50, 10, 40, 20. Everything fits in one sorted sublist, and _maxes records its maximum
    _lists  [[10, 20, 40, 50]]
    _maxes  [50]
---
Add 30: bisect _maxes to pick sublist 0, insort into it. It now has 5 items, more than 4, so it splits after the first load (2) items
    _lists  [[10, 20], {{[30, 40, 50]}}]
    _maxes  [{{20}}, 50]
---
Add 60: it is larger than every maximum, so it goes to the last sublist, whose maximum becomes 60
    _lists  [[10, 20], [30, 40, 50, {{60}}]]
    _maxes  [20, {{60}}]
---
Add 70: the last sublist reaches 5 items and splits again
    _lists  [[10, 20], [30, 40], {{[50, 60, 70]}}]
    _maxes  [20, {{40}}, 70]
---
Add 25 and 35: bisect_left(_maxes, 25) = 1, so both go into the middle sublist. No split, no allocation
    _lists  [[10, 20], [{{25}}, 30, {{35}}, 40], [50, 60, 70]]
    _maxes  [20, 40, 70]
---
Query 35: bisect _maxes (sublist 1), then bisect inside it (position 2). Its rank is 2 + 2 = 4, so s.index(35) is 4 and s[4] is 35
    _lists  [[10, 20], [25, 30, {{35}}, 40], [50, 60, 70]]
    _maxes  [20, {{40}}, 70]
```

## Template

```python
from bisect import bisect_left, bisect_right

from sortedcontainers import SortedList


def floor(keys, x):
    """Largest key <= x in a sorted list, or None."""
    i = bisect_right(keys, x)
    return keys[i - 1] if i else None


def ceiling(keys, x):
    """Smallest key >= x in a sorted list, or None."""
    i = bisect_left(keys, x)
    return keys[i] if i < len(keys) else None


def near_duplicate(nums, index_diff, value_diff):
    """Is there a pair i != j with |i - j| <= index_diff and |nums[i] - nums[j]| <= value_diff?"""
    window = SortedList()                         # the last index_diff values
    for i, x in enumerate(nums):
        j = window.bisect_left(x - value_diff)    # smallest value >= x - value_diff
        if j < len(window) and window[j] <= x + value_diff:
            return True
        window.add(x)
        if i >= index_diff:
            window.remove(nums[i - index_diff])
    return False


keys = [10, 20, 30, 40]
print(floor(keys, 25), ceiling(keys, 25), floor(keys, 5), ceiling(keys, 40))   # 20 30 None 40
scores = SortedList([50, 10, 40, 20, 30])
scores.add(35)
print(list(scores.irange(20, 40)), scores.index(35), scores[-1])   # [20, 30, 35, 40] 3 50
print(near_duplicate([8, 1, 15, 4, 9], 2, 3), near_duplicate([8, 1, 15, 4, 9], 1, 3))   # True False
```

`pip install sortedcontainers` if it is missing; it is pure Python with no dependencies.

## Pitfalls

- **`insort` in a hot loop**: each call shifts the tail of the list, so 10^5 to 10^6 random inserts become seconds to minutes. Switch to SortedList.
- **Mutating keys inside a sorted structure**: if an object's comparison result changes after insertion, the order is silently broken. Remove, change, re-add.
- **Off-by-one in floor and ceiling**: `bisect_left` versus `bisect_right` decides whether an equal key counts. Write both helpers once, test them on keys that are present, absent, below the minimum and above the maximum.
- **`std::lower_bound(s.begin(), s.end(), x)` on a `std::set`**: it does O(log n) comparisons but O(n) iterator steps, because set iterators are not random access. Use the member `s.lower_bound(x)`.
- **Assuming availability**: sortedcontainers is third-party. On a judge without it, a sorted list with bisect (small n) or a heap with lazy deletion (only min or max needed) are the usual fallbacks.

## Check yourself

Q: With `keys = [10, 20, 30, 40]`, what are `bisect_left(keys, 30)`, `bisect_right(keys, 30)`, the floor of 30 and the successor of 30?
A: 2 and 3. The floor is `keys[bisect_right - 1] = keys[2] = 30` (30 itself counts); the successor, the smallest key strictly greater, is `keys[bisect_right] = keys[3] = 40`.

Q: SortedList's insert is O(m) for sublists of length m, worse than a tree's O(log n). Why is it still faster in CPython?
A: The O(m) part is a `memmove` of at most about 2,000 pointers in C, a fraction of a microsecond, and the searches are `bisect` calls in C. A Python tree does about log2 n levels of interpreted work (attribute loads, comparisons, branches) at tens of nanoseconds per bytecode, allocates a node object per key and chases pointers across memory. Constant factors of 30 to 100 dominate the asymptotic difference at any size that fits in memory.

Q: You need, for a stream of 10^5 prices, the number of earlier prices strictly below each new price. Which structure and which call?
A: A SortedList of earlier prices: for each price p, the answer is `s.bisect_left(p)` (the number of stored values below p), then `s.add(p)`. Both are about O(log n), so O(n log n) total. A plain list with `insort` gives the same answers but O(n^2) shifting in the worst case; a Fenwick tree over compressed prices is the other standard answer.

Q: Trace `near_duplicate([8, 1, 15, 4, 9], 1, 3)`. What is in the window when 4 is checked, and why is the answer False?
A: With index_diff 1 the window holds only the previous value. When 4 (index 3) is checked, the window is `[15]`; the smallest window value >= 4 - 3 = 1 is 15, which is greater than 4 + 3 = 7, so no match. Every adjacent pair differs by more than 3 (7, 14, 11, 5), so the function returns False.

## Lab

- **220**: an ordered window with `bisect_left` on the lower edge. Expected: `near_duplicate([8, 1, 15, 4, 9], 2, 3)` is True (1 and 4 are two apart and differ by 3), the same with index_diff 1 is False, and `near_duplicate([5, 5], 1, 0)` is True; O(n log k) time for window size k. Then write the bucket version (bucket id `x // (value_diff + 1)`, check the same and the two neighbouring buckets) and stress-test both against the O(n k) double loop.
- **Floor and ceiling helpers**: expected `floor(keys, 25), ceiling(keys, 25), floor(keys, 5), ceiling(keys, 40)` print `20 30 None 40` for `keys = [10, 20, 30, 40]`; add `ceiling(keys, 41)`, which must return None.

> [!know]
> You now know how to answer floor, ceiling, rank and range queries in Python with bisect and SortedList, what C++ and Java provide instead, and why a list of sorted lists beats a tree in CPython.

=== primer | How do databases and Redis keep huge ordered data fast to search and scan? | 14 min
goal: Explain why disk-based indexes are B+ trees, how a range scan uses linked leaves, how Redis sorted sets pair a hash table with an ordered structure, and estimate an index's height
link: SQLite, Database File Format | https://www.sqlite.org/fileformat2.html#b_tree_pages | 10 min: section "B-tree Pages": table b-trees versus index b-trees, interior pages with K keys and K + 1 child page numbers, and leaf pages
link: PostgreSQL source, nbtree README | https://github.com/postgres/postgres/blob/master/src/backend/access/nbtree/README | 10 min: the first two sections, "Btree Indexing" and "The basic Lehman & Yao Algorithm": right-links and high keys that let searches survive concurrent page splits without read locks

> [!key]
> Storage rewards reading one big block over many small ones, so database indexes are **B+ trees**: interior pages hold hundreds of separator keys that route the search, the rows (or row pointers) live in the **leaves**, and leaves are **linked to their siblings**, so a range query is one descent plus a sequential walk. With a fan-out of a few hundred, three or four levels cover a billion rows. In memory, the trade-offs differ: Redis sorted sets pair a **hash table** (member to score) with an ordered structure, a skip list up to Redis 8.10 and a packed B+ tree for large sets in 8.12.

## Intuition

A library card catalogue has drawers labelled with ranges ("Ka to Ke"), and inside each drawer the cards are in order. To find one author you read the labels, open one drawer and flip to the card: two steps, not thirty. To list every author starting with K you find the first drawer and keep reading cards, moving to the next drawer when one runs out, never going back to the labels. That is a B+ tree: wide nodes so the path is short, and linked leaves so scans are sequential.

## How it works

### Why wide nodes

Disks and SSDs read in pages, and even RAM is read in 64-byte cache lines, so fetching one key from a block costs nearly as much as fetching all of them. A balanced binary tree with a billion keys has about 30 levels, each potentially a separate random read. A B-tree whose nodes are pages holding f keys has about log base f of n levels. SQLite's default page size has been 4096 bytes since version 3.12.0; PostgreSQL stores tables and indexes in pages of usually 8 kB. With keys of a few dozen bytes, an interior page holds hundreds of them.

### B+ trees in SQLite and PostgreSQL

SQLite stores every table and every index as a b-tree in its file. An **interior page** contains K keys and K + 1 pointers to child pages, where a pointer is a 32-bit page number. **Table b-trees** use the 64-bit rowid as key and store all row data in the leaves; **index b-trees** store just the indexed columns plus the rowid. Interior pages are therefore pure routing information, which is what makes their fan-out large.

PostgreSQL's B-tree implementation follows Lehman and Yao's algorithm: each page has a **right-link** to its right sibling and a **high key**, an upper bound on the keys allowed on that page. A search that arrives at a page which has just been split by another backend sees a search key above the high key and simply follows the right-link: no read locks are held while descending. The same sibling links (plus left-links for backward scans) make range scans walk the leaf level directly.

### Range scans

For `WHERE k BETWEEN 100 AND 200`, the database descends once to the leaf containing the first key >= 100, then reads leaves left to right until it passes 200. The cost is about log_f n page reads for the descent plus m / B leaf pages for m matching keys with B per leaf. Without an index on k, the only plan is to scan the whole table. SQLite shows the difference in its query plans: `SEARCH t USING INDEX idx_k (k>? AND k<?)` with the index, `SCAN t` without.

Because an index is sorted by its columns in order, a composite index on (last_name, first_name) serves `last_name = ?` and `last_name = ? AND first_name BETWEEN ...` with one descent and a scan, but not `first_name = ?` alone, whose matches are spread across the whole leaf level.

### Redis sorted sets

A sorted set must answer two different questions fast: "what is this member's score?" and "which members are in this score or rank range?". No single ordered tree does the first in O(1), so Redis keeps two indexes. Up to Redis 8.10, `t_zset.c` adds every element to a hash table mapping members to scores and to a skip list ordered by score, described in its header as "almost a C translation" of William Pugh's skip list, modified to allow repeated scores, to break ties by comparing members, and to keep a back pointer for reverse traversal. (Small sorted sets use a compact listpack encoding instead.) In the 8.12 release candidate of 29 October 2026, the header says large sorted sets "use the packed B+ tree and compact member hash index implemented in zset_btree.c", with leaves linked in both directions, chosen for memory efficiency; the redis.io page still describes the skip list. Documentation lags code, so check the source of the version you run.

Skip lists remain the memtable of LevelDB and RocksDB, and the storage module covers them, LSM trees and B-tree page management in depth.

## Cost

Height of a B+ tree with n rows, B rows per leaf page and fan-out f: about 1 + ceil(log base f of (n / B)) levels. For n = 10^8, B = 100 and f = 300: 10^6 leaves, then 3,334, 12 and 1 interior pages, so **4 levels**. For 10^9 rows it is still 4 (10^7 leaves, then 33,334, 112 and 1). The root and the second level are almost always cached, so a point lookup costs one or two real page reads. The equivalent balanced binary tree has about 27 to 30 levels.

Updates cost more than reads: every insert must update every index on the table, and a full leaf splits into two pages, pushing a separator key into the parent. Keys that arrive in increasing order (timestamps, sequences) keep landing on the rightmost leaf; random keys (such as random UUIDs) scatter inserts across all leaves, so more pages must stay in cache and more of them split.

## When to use it

| Workload | Structure | Example |
|---|---|---|
| Point lookups only, in memory | hash table | Python dict, Redis strings |
| Ordered queries, in memory | balanced tree, skip list, list of lists | std::map, Redis sorted sets, SortedList |
| Ordered queries on disk, read-heavy | B+ tree | SQLite and PostgreSQL indexes |
| Very write-heavy on disk | LSM tree | LevelDB, RocksDB, Cassandra (storage module) |
| Lookups by one key and order by another | two indexes over the same data | Redis sorted sets: hash plus ordered structure |

## Worked trace

A range query for keys in [20, 45] on a small B+ tree whose leaves are linked left to right:

```text
                 [ 30 | 60 ]
               /      |      \
     [10 20] --> [30 40 50] --> [60 70 80]
```

```steps
Read the root page. 20 < 30, so the first matching key can only be under the leftmost child
    page reads  1
    root        [ {{30}} | 60 ]
    output      []
---
Read leaf [10 20]. Binary search inside the page finds 20, the first key >= 20: emit it
    page reads  2
    leaf        [10 {{20}}]
    output      [{{20}}]
---
The leaf is exhausted: follow its sibling link instead of going back up the tree. Emit 30 and 40
    page reads  3
    leaf        [{{30}} {{40}} 50]
    output      [20, {{30}}, {{40}}]
---
50 > 45, so the scan stops. Three page reads: one descent of height 2, then one extra leaf. A billion-row table would need about 4 for the descent and one more per leaf of results
    page reads  3
    leaf        [30 40 {{50}}]
    output      [20, 30, 40]
```

## Template

```python
import math
from bisect import bisect_left


def btree_levels(n_rows, rows_per_leaf, fanout):
    """Levels of a B+ tree: one leaf level plus interior levels until a single root."""
    pages = max(1, math.ceil(n_rows / rows_per_leaf))
    levels = 1
    while pages > 1:
        pages = math.ceil(pages / fanout)
        levels += 1
    return levels


def range_scan(keys, lo, hi):
    """Keys in [lo, hi] from a sorted list: one binary search, then a sequential scan."""
    i = bisect_left(keys, lo)
    while i < len(keys) and keys[i] <= hi:
        yield keys[i]
        i += 1


print(btree_levels(10**8, 100, 300), btree_levels(10**9, 100, 300), btree_levels(10**9, 1, 2))   # 4 4 31
print(list(range_scan([10, 20, 30, 40, 50, 60, 70, 80], 20, 45)))   # [20, 30, 40]
```

`range_scan` is the same "descend once, then walk in order" shape as an index range scan, with the leaf chain replaced by consecutive list positions.

## Pitfalls

- **Indexes are not free**: each one costs space and slows every insert, update and delete of the indexed columns. Index the queries you actually run.
- **Expecting a scan to use an index it cannot use**: a condition on the second column of a composite index, or a function applied to the column, usually means a full scan. Read the plan (`EXPLAIN QUERY PLAN` in SQLite, `EXPLAIN` in PostgreSQL).
- **Thinking in binary-tree heights for disk data**: what matters is page reads, and a B+ tree's height barely grows with n.
- **Random primary keys on write-heavy tables**: they spread inserts and page splits over the whole index; time-ordered keys keep them local.
- **Trusting documentation over source**: Redis's own docs describe the skip list while the 8.12 code uses a B+ tree for large sets. When performance matters, check the version you deploy.

## Check yourself

Q: A table has 10^9 rows, 100 rows fit in a leaf page and interior pages have a fan-out of 300. How many levels does its B+ tree have, and how many disk reads does a point lookup typically need?
A: 10^7 leaves, then 33,334, 112 and 1 interior pages: 4 levels. With the root and the second level cached in memory, a lookup reads about 2 pages from storage (the third level and the leaf), often fewer.

Q: Why does a B+ tree link its leaves, when an in-order traversal of a plain BST manages without links?
A: An in-order traversal climbs back up through ancestors (with a stack or parent pointers) to reach the next subtree, and on disk every one of those ancestor visits can be a page read. Sibling links let a range scan go straight from one leaf page to the next, so after the first descent it reads only leaf pages, in order, which is also friendly to read-ahead.

Q: A table has an index on (last_name, first_name). Which of these can use it as a range scan: `last_name = 'Lee'`, `first_name = 'Ana'`, `last_name = 'Lee' AND first_name >= 'M'`?
A: The first and the third. The index is sorted by last name, then first name, so all 'Lee' entries are contiguous, and within them first names are sorted. Rows with first name 'Ana' are scattered across all last names, so the second query cannot be answered by one descent and a scan.

Q: Why does a Redis sorted set need two structures, and what does each answer?
A: Commands need both "member to score" (`ZSCORE`, and finding the old score on `ZADD` updates) and "order by score" (`ZRANGE`, `ZRANGEBYSCORE`, `ZRANK`). A hash table answers the first in O(1) but knows no order; the ordered structure (skip list, or B+ tree in 8.12) answers ranges and ranks in O(log n + m) but would need a search by score, not by member. Keeping both gives each command its best path, at the cost of updating two structures on every write.

## Lab

- **Index heights**: run the template. Expected: `4 4 31` (a binary tree of a billion single-key nodes needs 31 levels counted this way, against 4 for the B+ tree), then `[20, 30, 40]`. Try 8 KB pages with 40-byte keys (fan-out about 200) and 100 rows per leaf: expected 5 levels for 10^9 rows and 4 for 10^8.
- **Read a real plan**: with Python's built-in `sqlite3`, create a table `t(k INTEGER, v TEXT)` with 100,000 rows and an index `idx_k` on `k`, then run `EXPLAIN QUERY PLAN SELECT v FROM t WHERE k BETWEEN 100 AND 200`. Expected (SQLite 3.45; wording varies slightly by version): a row containing `SEARCH t USING INDEX idx_k (k>? AND k<?)`. The same query on the unindexed column `v` shows `SCAN t`. Time both queries and note the gap.

> [!know]
> You now know why disk indexes are B+ trees with linked leaves, how a range scan reads them, how to estimate an index's height, and how Redis combines a hash table with an ordered structure.

=== lab | Balanced or not: a plain BST against SortedList, bisect and set | 45 min
goal: Measure how insertion order changes a plain BST's height and speed, stress-test it against SortedList, and compare build time, lookup time and memory with SortedList, bisect on a list and a set
link: Sorted Containers, Performance at Scale | https://grantjenks.com/docs/sortedcontainers/performance-scale.html#theory | 10 min: the "Theory" section: the cost of add with sublist length m, and why m near the cube root of n is the theoretical optimum

You will build the simplest possible ordered set, break it with sorted input, prove it correct with a stress test, and race it against the structures Python programmers actually use. The numbers you get are the evidence behind the ordered-maps card.

## Setup

- Python 3.10 or newer, and `pip install sortedcontainers`.
- If you built the `dsakit` benchmark harness earlier in the guide, use its timing function; otherwise the helper below is enough.

## Steps

1. Save the core of a plain BST, iterative throughout so that degenerate trees cannot crash it:

```python
import bisect
import random
import statistics
import time
import tracemalloc

from sortedcontainers import SortedList


class Node:
    __slots__ = ("val", "left", "right")

    def __init__(self, val):
        self.val, self.left, self.right = val, None, None


def insert(root, key):
    new = Node(key)
    if root is None:
        return new
    node = root
    while True:
        if key < node.val:
            if node.left is None:
                node.left = new
                return root
            node = node.left
        elif key > node.val:
            if node.right is None:
                node.right = new
                return root
            node = node.right
        else:
            return root


def contains(root, key):
    node = root
    while node is not None:
        if key == node.val:
            return True
        node = node.left if key < node.val else node.right
    return False


def floor_bst(root, key):
    """Largest key <= key, or None."""
    best, node = None, root
    while node is not None:
        if node.val <= key:
            best, node = node.val, node.right
        else:
            node = node.left
    return best


def height(root):
    best, stack = 0, [(root, 1)] if root else []
    while stack:
        node, depth = stack.pop()
        best = max(best, depth)
        stack += [(c, depth + 1) for c in (node.left, node.right) if c]
    return best


def timed(fn, repeats=3):
    """Median wall-clock time of fn() over a few runs."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def stress(trials=1000, seed=0):
    """Random inserts and queries, checked against SortedList as the model."""
    rng = random.Random(seed)
    for _ in range(trials):
        root, model = None, SortedList()
        for _ in range(rng.randint(1, 30)):
            x = rng.randint(0, 20)
            root = insert(root, x)
            if x not in model:
                model.add(x)
            q = rng.randint(-1, 21)
            i = model.bisect_right(q)
            assert floor_bst(root, q) == (model[i - 1] if i else None)
            assert contains(root, q) == (q in model)
    print("stress test passed")
```

2. Run `stress()`. Then break `floor_bst` on purpose (change `<=` to `<`) and confirm the stress test fails on a tiny case; restore it.

3. **Heights.** For n = 1,000, 10,000 and 100,000, insert `random.sample(range(10 * n), n)` and record the height, next to log2 n. For sorted keys, use n = 1,000 to 8,000 only.

4. **Doubling.** Time sorted inserts for n = 1,000, 2,000, 4,000 and 8,000 and compute the ratio between consecutive times.

5. **Head to head.** With n = 100,000 random keys and 100,000 random queries, time building and querying: the plain BST (insert one by one), `SortedList` (`add` one by one), a list with `bisect.insort`, and a `set`. Use `timed` and keep the medians.

6. **Sorted input.** Repeat the build for `SortedList` and `insort` with the keys sorted (skip the plain BST: it would take many minutes).

7. **Memory.** Wrap each build in `tracemalloc.start()` and `tracemalloc.get_traced_memory()`, building from a list of keys that already exists, and divide by n.

8. **Explain.** Read the Implementation Details page linked from the ordered-maps card and write five sentences explaining your table, using the words allocation, pointer, bisect and load factor.

## What you should see

Numbers from a shared Linux server running CPython 3.12; your absolute times will differ, the shapes should not.

- The stress test passes; the planted bug fails at once, on a query equal to a stored key (the only case where `<` and `<=` differ).
- Random-order heights of roughly 22, 32 and 41 for n = 1,000, 10,000 and 100,000: about two to two and a half times log2 n (10, 13.3, 16.6). Sorted-order height equals n.
- Sorted inserts roughly quadruple each time n doubles (measured: 0.27 s, 1.2 s, 4.1 s for 2,000, 4,000 and 8,000 keys): quadratic, as predicted.
- At n = 100,000 random keys: plain BST about 0.5 s to build and 0.4 s for the lookups; SortedList about 0.3 s and 0.2 s; `insort` about 3 s to build (every insert shifts half the list on average) but the fastest lookups among the ordered options, 0.2 s; `set` about 0.02 s and 0.03 s, with no order at all.
- Sorted input: `insort` about 0.05 s (every insert is an append), SortedList about 0.1 s.
- Memory per key, not counting the key objects: about 56 bytes for the BST (one `__slots__` node) against 8 to 9 for SortedList, the "one pointer per item" the documentation promises.
- The verdict: even a plain BST that never pays for rebalancing, on its best-case random input, loses to SortedList in CPython on speed and memory, and a balanced tree written in Python would be slower still. Hand-written trees are for learning and for interviews; in Python production code, reach for `bisect` or `sortedcontainers`.

=== practice
- 700 core
  cue: Find a key in a tree whose left side is always smaller and right side always larger.
  hint: At each node one comparison rules out an entire subtree. Which one?
  insight: Walk from the root: go left if the target is smaller, right if it is larger, and stop on equality or at None. No stack or recursion is needed.
  cost: O(h) time, O(1) space
  pattern: bst-search
- 938 core
  cue: Sum of the keys of a search tree that fall inside [low, high].
  hint: When a node's key is below low, what do you know about everything in its left subtree?
  insight: Recurse with pruning: below low, only the right subtree can contribute; above high, only the left; inside the range, add the key and recurse into both. You visit the matching keys plus the two boundary paths.
  cost: O(h + k) time for k keys in range (O(n) in the worst case), O(h) space
  pattern: bst-search
- 108 core
  cue: Turn a sorted array into a search tree whose height is as small as possible.
  hint: Which element should be the root so that the two sides end up the same size?
  insight: Make the middle element the root and build the left and right halves recursively over index ranges. At every node the two sides differ in size by at most one, so the height is ceil(log2(n + 1)).
  cost: O(n) time, O(log n) recursion depth
  pattern: bst-balance
- 235 core
  cue: Lowest common ancestor of two nodes, in a tree where the keys are ordered.
  hint: Compare both keys with the current node. When can you be sure that the answer is not further down?
  insight: From the root, go left while both keys are smaller and right while both are larger. The first node where they part (or that equals one of them) is the lowest common ancestor; no subtree ever needs to be searched.
  cost: O(h) time, O(1) space
  pattern: bst-search
- 98 core
  cue: Decide whether a binary tree obeys the search-tree ordering everywhere, not just between parents and children.
  hint: A node deep in the right subtree of the root must still be larger than the root. What range must each node's key lie in?
  insight: Pass an open interval (low, high) down: the left child gets (low, val) and the right child (val, high), and a key outside its interval fails. Equivalently, the in-order sequence must be strictly increasing.
  cost: O(n) time, O(h) space
  pattern: bst-bounds
- 450 core
  cue: Remove one key from a search tree so that it is still a valid search tree.
  hint: Removing a leaf or a node with one child is easy. With two children, which key could take the node's place without breaking the order?
  insight: Recurse and return the new subtree root. At the key: no left child, return the right; no right child, return the left; otherwise copy the minimum of the right subtree (the in-order successor) into the node and delete that key from the right subtree.
  cost: O(h) time, O(h) space
  pattern: bst-delete
- 230 core
  cue: The k-th smallest key of a search tree.
  hint: Which traversal visits a search tree's keys in increasing order, and do you have to finish it?
  insight: Iterative in-order with a stack: push the left spine, pop and count, and return at the k-th pop. If such queries repeat while the tree changes, store subtree sizes in the nodes and answer each in O(h).
  cost: O(h + k) time, O(h) space
  pattern: bst-inorder
- 173 core
  cue: Hand out a search tree's keys one at a time in increasing order, with memory proportional to the height.
  hint: Pause an in-order traversal between calls. What state does it need to keep?
  insight: Keep the in-order stack in the object. The constructor pushes the left spine of the root; next pops a node, pushes the left spine of its right child and returns the key. Each node is pushed and popped once, so next is O(1) amortised.
  cost: O(1) amortised per call, O(h) space
  pattern: bst-inorder
- 99 derive
  cue: Exactly two keys of a search tree were swapped by mistake; fix it without changing the shape.
  hint: Compare the in-order sequence of the broken tree with a sorted one. What do the two misplaced keys leave behind?
  insight: In-order is sorted except for one or two descents (a key followed by a smaller one). The first culprit is the larger key of the first descent and the second is the smaller key of the last descent; swap their values. Morris traversal brings the extra space to O(1).
  cost: O(n) time, O(h) space
  pattern: bst-inorder
- 669 stretch
  cue: Remove every key outside [low, high] from a search tree and return the new root.
  hint: If a node's key is below low, what happens to its left subtree, and what should take the node's place?
  insight: Recurse and return the new subtree root: below low, return the trimmed right subtree; above high, return the trimmed left subtree; inside, trim both children and keep the node. The ordering removes whole subtrees at once.
  cost: O(n) time, O(h) space
  pattern: bst-delete
- 1373 stretch
  cue: The largest key sum of any subtree that is itself a valid search tree, inside a tree that need not be one.
  hint: A parent can tell whether it roots a valid search tree only if each child reports a few facts about itself. Which facts?
  insight: Post-order returns (is_bst, min, max, sum) for each subtree, with the empty subtree as (True, +inf, -inf, 0). A node is valid when both children are and left max < val < right min; record its sum in a running maximum that starts at 0.
  cost: O(n) time, O(h) space
  pattern: bst-bounds
- 220 stretch
  cue: Is there a pair of values within value_diff of each other whose indices are at most index_diff apart?
  hint: Slide a window over the last index_diff values. For a new value x, which single value of the window do you need to look at?
  insight: Keep the window in an ordered set. For each x, find the smallest window value >= x - value_diff (a ceiling query) and check that it is <= x + value_diff; then add x and drop the value that left the window. Buckets of width value_diff + 1 make it O(n).
  cost: O(n log k) time with an ordered set (O(n) with buckets), O(k) space for window size k
  pattern: bst-ordered
