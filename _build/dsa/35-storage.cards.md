=== card | 1206
time: 50 min

## The problem

Implement an ordered multiset supporting search, insertion, and removal of one occurrence. `search(value)` returns whether a value is present; `add(value)` inserts another copy; `erase(value)` returns false when absent and otherwise removes one copy and returns true. For example, after adding 4 twice, erasing 4 once must still leave 4 searchable.

## Constraints and what they imply

Values must have a consistent total order; this implementation is intended for integers. Duplicates are separate nodes, not a single Boolean membership flag. Operations may be interleaved arbitrarily, including deletion from an empty structure. A sorted singly linked list would support easy pointer updates but require a linear search. A skip list trades deterministic worst-case balance for independent random node heights and expected logarithmic navigation, without relying on a library balanced tree.

## Brute force

Keep all values in an unsorted Python list. Search and erase scan O(n) entries; insertion appends in amortized O(1) time, while removing an interior entry also shifts later list elements. Space is O(n). Sorting the list permits binary search, but inserting or deleting in the middle still shifts O(n) entries. The repeated linear work is undesirable for a long sequence of mixed operations.

## The insight

Each node has a tower of forward links. Level zero contains every node in nondecreasing order. A node promoted to level j also appears on every lower level, and each promotion occurs independently with probability one half. Consequently roughly half the nodes reach each next level, so the upper lists are increasingly sparse. Search starts at the top left, moves right while the next value is strictly smaller than the target, and drops down when it cannot advance. No skipped value can be the target because all passed nodes are smaller.

During the descent, record the last strictly smaller node at every level. These predecessors identify all splice points. Insertion gives a fresh node a random height and links it after the predecessor on each of its levels; if its tower exceeds the current head height, extend the head and use it as predecessor for the new levels. Inserting before equal keys preserves sorted order at every level. The search result is the successor at level zero, which is an equal node exactly when the target exists.

For deletion, select that particular level-zero successor. Unlink it only at levels where the recorded predecessor points to that same node. This identity check is essential with duplicates: an older equal node might be present on a higher level even though the selected newer node is not. Finally remove empty top head levels. By induction, all remaining levels are sorted and contain exactly the nodes whose towers reach them, so search and subsequent updates continue to work.

## Optimal solution, traced

```steps
Add 4 twice, then add 2
    level zero contains 2 -> 4(newer) -> 4(older)
---
Erase 4: predecessors stop at 2; unlink the first 4 only where it appears
    level zero now contains 2 -> 4, so search(4) is {{true}}
```

Different random heights change the upper-level links but not the multiset result. The injected random generator makes tests reproducible; normal use creates an independent generator automatically. Randomness is for balancing, not a security guarantee.

## Code

```python
import random


class _Node:
    def __init__(self, value, height):
        self.value = value
        self.next = [None] * height


class SkipList:
    def __init__(self, rng=None):
        self.head = _Node(None, 1)
        self.rng = rng if rng is not None else random.Random()

    def _predecessors(self, value):
        update = [None] * len(self.head.next)
        node = self.head
        for level in range(len(self.head.next) - 1, -1, -1):
            while node.next[level] is not None and node.next[level].value < value:
                node = node.next[level]
            update[level] = node
        return update

    def search(self, value):
        node = self._predecessors(value)[0].next[0]
        return node is not None and node.value == value

    def add(self, value):
        update = self._predecessors(value)
        height = 1
        while self.rng.randrange(2) == 0:
            height += 1
        while len(self.head.next) < height:
            self.head.next.append(None)
            update.append(self.head)
        node = _Node(value, height)
        for level in range(height):
            node.next[level] = update[level].next[level]
            update[level].next[level] = node

    def erase(self, value):
        update = self._predecessors(value)
        node = update[0].next[0]
        if node is None or node.value != value:
            return False
        for level in range(len(node.next)):
            if update[level].next[level] is node:
                update[level].next[level] = node.next[level]
        while len(self.head.next) > 1 and self.head.next[-1] is None:
            self.head.next.pop()
        return True
```

## Complexity

With independent fair promotions, search and update take expected O(log n) time for n stored nodes, and expected total link space is O(n): each node has expected height 1 + 1/2 + 1/4 + ... = 2. The predecessor array and a new tower take expected O(log n) temporary space in an operation. These are probabilistic bounds, not deterministic guarantees: unusually tall towers or a poorly shaped list can cost much more. The analysis assumes the operation sequence does not choose keys based on the hidden random heights.

## Mistakes and edge cases

- Deleting every equal node or decrementing all levels by value loses duplicates.
- Use node identity when unlinking higher levels, not merely equality of values.
- A node reached at a level necessarily has that level's link; only descend, never access a higher link after moving.
- Remove an empty top level but always retain level zero for an empty list.
- Search should stop before equal nodes; insertion and deletion then have consistent predecessor positions.
- This educational structure has no synchronization, persistence, crash recovery, or page layout; it is not itself a durable storage engine.

## Variations

- Store a count per key instead of a node per occurrence, updating the count on erase.
- Add span counts to support rank and select queries.
- Walk level zero from a lower-bound predecessor to implement a range scan.
