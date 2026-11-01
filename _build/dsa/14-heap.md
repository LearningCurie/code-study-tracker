---
key: heap
name: Heaps and priority queues
stage: order
summary: The binary heap as a complete tree stored in a list, Python's heapq used well, and the patterns it powers: top-k, k-way merge, running medians, lazy deletion and event simulation.
why: Many problems, and most schedulers, come down to "repeatedly take the most urgent item while new items keep arriving". Sorting answers that once; a heap answers it continuously, in O(log n) per operation, with nothing but a list and two index formulas. The same few lines run Python's asyncio timers, Go's runtime timers, PostgreSQL's top-N sorts and external merges, and Dijkstra's shortest paths. Knowing how sift-up, sift-down and bottom-up heapify work tells you what heapq really costs, why it has no decrease-key, and when a sort, quickselect, sorted container or timing wheel is the better tool.
outcomes:
- Explain the heap property and the parent and child index formulas, and say what a heap does and does not let you find quickly
- Implement push and pop with sift-up and sift-down, and prove that both restore the heap in O(log n)
- Prove that bottom-up heapify is O(n) and use it when all the data is available up front
- Use heapq fluently: max-heaps by negation, tuple keys with a tie-breaking counter, heappushpop, heapreplace, nlargest and merge
- Solve top-k, k-way merge, running-median and scheduling problems, and remove or reprioritise items with lazy deletion or an indexed heap
- Choose between a heap, sorting, quickselect, a sorted container and a timing wheel from the operation mix
cues:
- "Repeatedly take the smallest (or largest)" while new items keep arriving
- "k largest", "k closest", "kth largest so far" or "top k" over a stream or a large input
- Several sorted sources to combine into one sorted output
- A running median, or any rule that needs the largest of a lower group and the smallest of an upper group
- A simulation where things happen at times and the next event, or the best available job, must be found quickly
traps:
- Expecting heapq to be a max-heap, or forgetting to negate the value back when you read it
- Pushing (priority, item) tuples whose items cannot be compared, which crashes on the first tie
- Treating the heap list as sorted: only heap[0] is special, and heap[-1] is not the maximum
- Calling heappop on a list that was never heapified, which silently returns wrong answers
- Deleting or updating an item in the middle of a heap with list.remove or in-place edits, which is O(n) and breaks the heap
systems:
- Event loops keep timers in a min-heap: asyncio's call_later pushes onto the loop's _scheduled list with heapq, libuv keeps a min-heap of timers, and Go's runtime keeps a 4-ary heap per processor (timerHeapN = 4)
- PostgreSQL runs ORDER BY ... LIMIT n as a bounded "top-N heapsort", and merges the sorted runs of a large sort with a heap holding one tuple per run
- RocksDB's MergingIterator combines sorted memtable and SSTable iterators with a heap; LevelDB's merger scans its few children linearly instead
- Kafka's request purgatory and Linux's ordinary timeouts use timing wheels, because there insert and cancel are O(1) instead of O(log n)
further:
- Docs · 15 min | Python docs: heapq, Priority Queue Implementation Notes and Theory | https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes
- Article · 30 min | Sedgewick and Wayne: 2.4 Priority Queues | https://algs4.cs.princeton.edu/24pq/
- Notes · 20 min | MIT 6.006 (Spring 2020): Lecture 8, Binary Heaps (PDF) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/40d4851e550507ca14dc778b9b2266cc_MIT6_006S20_lec8.pdf
- Article · 15 min | Confluent: Apache Kafka, Purgatory, and Hierarchical Timing Wheels | https://www.confluent.io/blog/apache-kafka-purgatory-hierarchical-timing-wheels/
bank: heap
---

=== primer | What does a priority queue promise, and how does a heap fit a tree into a list? | 15 min
goal: Choose a priority-queue implementation by its costs, and move around a binary heap stored in a list with the parent and child formulas
tag: heap-array | Heap as a complete tree in a list
link: MIT 6.006 (Spring 2020): Lecture 8 notes, Binary Heaps (PDF) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/40d4851e550507ca14dc778b9b2266cc_MIT6_006S20_lec8.pdf | 10 min: pages 1 to 3, the priority-queue interface, the table comparing arrays, sorted arrays and heaps, and 'Array as a Complete Binary Tree'
practice: 1046

> [!key]
> A **priority queue** promises two things: add an item, and remove the item with the smallest key (or the largest). It does not search and it does not list items in order. A **binary heap** gives both operations in O(log n), plus an O(1) peek, by keeping a much weaker order than sorting: every parent is no larger than its children. It stores that tree in a plain list with no pointers, because node i's children sit at 2i + 1 and 2i + 2 and its parent at (i - 1) // 2.

## Intuition

Think of a hospital emergency department. Patients arrive all the time, and whenever a doctor is free they must see the most urgent patient. Nobody sorts the whole waiting room by urgency: the order of the tenth and eleventh most urgent patients is wasted effort, because it will change as new patients arrive. The only question that matters, again and again, is "who is most urgent right now?".

A heap is the least amount of order that answers that question cheaply. Picture an org chart in which every manager is more urgent than the people who report to them. The most urgent person is at the top, but two colleagues on the same level are in no particular order, and neither are cousins in different departments. Keeping that partial order up to date is much cheaper than keeping a full ranking.

## How it works

### The interface

| Operation | Meaning | With heapq |
|---|---|---|
| push(x) | add x | `heapq.heappush(h, x)` |
| pop() | remove and return the smallest | `heapq.heappop(h)` |
| peek() | look at the smallest without removing it | `h[0]` |
| size | how many items | `len(h)` |

Two operations are deliberately missing: "find x" and "remove x from the middle". Later cards show what to do when you need them.

### Four ways to build it

| Structure | push | pop the minimum | peek | Good when |
|---|---|---|---|---|
| Unsorted list | O(1) append | O(n) scan, then remove | O(n) | you almost never pop |
| Sorted list, minimum kept at the end | O(n) insert (shifting) | O(1) `pop()` | O(1) | you almost never push |
| Binary heap (`heapq`) | O(log n) | O(log n) | O(1) | pushes and pops are mixed: the default |
| Balanced tree or `SortedList` | O(log n) | O(log n) | O(1) | you also need the maximum, deletion of any item or ordered iteration |

### A complete tree in a list

A binary heap is a **complete binary tree**: every level is full except possibly the last, which fills from the left. Number the nodes level by level, left to right, starting at 0, and store node i at `a[i]`. For n = 10:

```text
              0                  parent(i) = (i - 1) // 2
          /       \              left(i)   = 2 * i + 1
        1           2            right(i)  = 2 * i + 2
      /   \       /   \          leaves    = indices n // 2 to n - 1
     3     4     5     6         levels    = floor(log2 n) + 1
    / \   /
   7   8 9
```

Because the tree is complete, the list has no gaps, so the arithmetic always lands on a real slot and no pointers are needed. Node 4 has only a left child (9), and nodes 5 to 9 are leaves.

### The heap property

A list `a` is a **min-heap** when `a[(i - 1) // 2] <= a[i]` for every i > 0: no node is smaller than its parent. Three consequences follow, and the third surprises people:

1. The minimum is `a[0]`, because each step up to a parent never increases the value.
2. Every root-to-leaf path is sorted.
3. Nothing else is ordered. Siblings, cousins and whole levels are unordered. The second smallest item is `a[1]` or `a[2]`, but the largest can be any leaf, and one set of values has many valid heaps.

A **max-heap** flips the inequality. Python's heapq builds min-heaps (Python 3.14 added `heappush_max` and friends; before that you negate keys, as the heapq card shows). C++'s `std::priority_queue` is a max-heap by default; Java's `PriorityQueue` is a min-heap.

## Cost

- **Index arithmetic** is O(1): a multiply (or shift) and an add.
- **Height.** Level d holds at most 2^d nodes, so n nodes need floor(log2 n) + 1 levels, and a root-to-leaf path has at most floor(log2 n) edges: 19 for a million items, 29 for a billion. Push and pop (next card) walk one such path, which is where their O(log n) comes from.
- **Memory.** n list slots, each an 8-byte reference in CPython, and nothing else. A pointer-based tree node would carry two child pointers and an object header per item.
- **A mixed workload.** With about n items queued and m operations that mix pushes and pops, an unsorted list costs O(n) per pop, so O(mn) in all; a heap costs O(m log n). For n = m = 10^5 that is roughly 10^10 against 2 × 10^6 basic steps.

## When to use it

Reach for a priority queue when the question is "what is the most urgent item **now**", asked again and again while items keep arriving: the next event in a simulation, the closest unvisited vertex in Dijkstra's algorithm, the current k best, the next task to run.

Do not use one when:

- You need everything in order once: sort (Timsort is in C, stable and adaptive).
- You need the kth smallest once, on data in memory: quickselect (expected O(n)) or `heapq.nsmallest`.
- You need to find, delete or update arbitrary items often, or both the minimum and the maximum: a `SortedList` or balanced tree gives all of these in O(log n).
- You only ever need the minimum and never remove it: keep a running `min`.

## Worked trace

Checking the heap property is the quickest way to make the layout stick: compare each node with its parent, once.

```steps
Is `[2, 3, 4, 7, 5, 1, 9, 8]` a min-heap? Node i sits under node (i - 1) // 2; check each pair once
                    2                i   0  1  2  3  4  5  6  7
                /       \            a   2  3  4  7  5  1  9  8
            3               4
          /   \           /   \
        7       5       1       9
       /
      8
---
i = 1: parent is (1 - 1) // 2 = 0; a[0] = 2 <= a[1] = 3, fine
                    {{2}}                i   0  1  2  3  4  5  6  7
                /       \            a   {{2}}  {{3}}  4  7  5  1  9  8
            {{3}}               4
          /   \           /   \
        7       5       1       9
       /
      8
---
i = 2: parent is (2 - 1) // 2 = 0; a[0] = 2 <= a[2] = 4, fine
                    {{2}}                i   0  1  2  3  4  5  6  7
                /       \            a   {{2}}  3  {{4}}  7  5  1  9  8
            3               {{4}}
          /   \           /   \
        7       5       1       9
       /
      8
---
i = 3: parent is (3 - 1) // 2 = 1; a[1] = 3 <= a[3] = 7, fine
                    2                i   0  1  2  3  4  5  6  7
                /       \            a   2  {{3}}  4  {{7}}  5  1  9  8
            {{3}}               4
          /   \           /   \
        {{7}}       5       1       9
       /
      8
---
i = 4: parent is (4 - 1) // 2 = 1; a[1] = 3 <= a[4] = 5, fine
                    2                i   0  1  2  3  4  5  6  7
                /       \            a   2  {{3}}  4  7  {{5}}  1  9  8
            {{3}}               4
          /   \           /   \
        7       {{5}}       1       9
       /
      8
---
i = 5: parent is (5 - 1) // 2 = 2; a[2] = 4 > a[5] = 1: **violation**, so this is not a heap
                    2                i   0  1  2  3  4  5  6  7
                /       \            a   2  3  {{4}}  7  5  {{1}}  9  8
            3               {{4}}
          /   \           /   \
        7       5       {{1}}       9
       /
      8
```

## Template

```python
def parent(i):
    return (i - 1) // 2


def children(i, n):
    """Indices of the children of node i in a heap of size n."""
    return [c for c in (2 * i + 1, 2 * i + 2) if c < n]


def is_min_heap(a):
    """True if every node is >= its parent (the min-heap property)."""
    return all(a[parent(i)] <= a[i] for i in range(1, len(a)))
```

Using the real thing:

```python
import heapq

pq = []                                   # any list can be a heap
heapq.heappush(pq, (2, "reply to email"))
heapq.heappush(pq, (1, "fix outage"))
heapq.heappush(pq, (3, "write report"))
print(pq[0])                              # (1, 'fix outage'): peek in O(1)
print(heapq.heappop(pq))                  # (1, 'fix outage')
print(heapq.heappop(pq))                  # (2, 'reply to email')
```

## Pitfalls

- **Reading the list as sorted.** `print(heap)` shows heap order, not sorted order: `heap[1]` is not necessarily the second smallest and `heap[-1]` is not the largest.
- **Mixing 1-based formulas into 0-based lists.** Many textbooks (algs4 included) put the root at index 1, where the children are 2i and 2i + 1 and the parent is i // 2. In a Python list that starts at 0, use 2i + 1, 2i + 2 and (i - 1) // 2.
- **Starting a parent check at i = 0.** `(0 - 1) // 2` is -1, so `a[-1] <= a[0]` compares the root with the last item. Loops over "node and its parent" start at 1.
- **Expecting fast search.** `x in heap` is a linear scan; a heap is not a search structure.

## Check yourself

Q: In a 0-based heap of 12 items, what are the children of index 5, the parent of index 10, and which indices are leaves?
A: The children of 5 would be 11 and 12; only 11 exists because n = 12. The parent of 10 is (10 - 1) // 2 = 4. The leaves are indices 6 to 11 (n // 2 to n - 1); index 5 is the last parent because 2 * 5 + 1 = 11 < 12.

Q: Where can the largest item of a min-heap be, and how long does finding it take?
A: In any leaf: a node with children is no larger than them, so it cannot be the strict maximum. About n / 2 leaves exist and nothing orders them, so finding the maximum is O(n). If you need both ends, use a sorted container, or two heaps with lazy deletion.

Q: A batch job receives 10^6 tasks with priorities, runs the 10 most urgent and discards the rest. Which implementation would you pick?
A: No long-lived queue is needed. `heapq.nsmallest(10, tasks)` scans once with a heap of only 10 items (O(n log 10)), or `heapq.heapify` the list in O(n) and pop 10 times (O(n + 10 log n)). Pushing a million items one by one does more work, and ten linear scans of an unsorted list (10^7 steps) also work but are the slowest option.

## Lab

- **1046 Last Stone Weight.** First simulate with a plain list (sort, or scan for the two largest, every round), then with heapq storing negated weights. Expected: O(n^2 log n) or O(n^2) for the list versions against O(n log n) for the heap; `[2, 7, 4, 1, 8, 1]` gives 1, `[1]` gives 1 and `[2, 2]` gives 0.
- **Heap or not?** Decide on paper which of these are min-heaps, then confirm with `is_min_heap`: `[1, 2, 3, 4, 5]`, `[1, 3, 2, 4]`, `[1, 1, 1]`, `[2, 1]`, `[0, 5, 1, 6, 4]`. Expected: True, True, True, False, False (in the last one, 4 at index 4 sits under 5 at index 1).

> [!know]
> You now know what a priority queue promises, why a heap is the default way to build one, and how to move around a heap stored in a list.

=== primer | How do push and pop keep a heap valid in O(log n)? | 16 min
goal: Implement push with sift-up and pop with sift-down from memory, and explain why each restores the heap property in O(log n)
tag: heap-sift | Sift up and sift down
link: Sedgewick and Wayne: 2.4 Priority Queues | https://algs4.cs.princeton.edu/24pq/ | 15 min: the 'Algorithms on heaps' part (swim, sink, insert and remove the maximum) with its step-by-step figures; note their heap is a max-heap starting at index 1
practice: 1046, 703

> [!key]
> **Push** appends the new item as the last leaf, which keeps the tree complete, then **sifts it up**: swap it with its parent while it is smaller. **Pop** saves the root, moves the last leaf into the root's place, then **sifts it down**: swap it with its smaller child while that child is smaller. Each operation repairs a single root-to-leaf path, so each costs O(log n).

## Intuition

Push: a new hire joins at the bottom of the org chart and is promoted past every manager who is less urgent than they are, then stops. Pop: the person at the top leaves; the most junior person is put in the empty chair (the only move that keeps the chart's shape), then moved down, each time swapping with the more urgent of their two reports, until both reports are less urgent than they are.

Why the smaller child? The child that moves up becomes the parent of its former sibling, so it must be no larger than that sibling. Of the two children, only the smaller one can sit above both.

## How it works

### Sift up, after a push

1. Append x at index n, the next free leaf.
2. While x is not the root and x is smaller than its parent: swap them and continue from the parent's index.

**Invariant:** every parent-child pair is in order except possibly x and its parent, and x's parent is no larger than x's children. The second half is what makes each swap safe. When x moves up, its parent p moves down into x's old slot, whose new children (if any) were p's descendants before, so they are no smaller than p. And x's new children are p (larger than x, which is why we swapped) and p's other child, which was already no smaller than p.

### Sift down, after a pop

1. Save `a[0]`, the answer. Pop the last item off the list; if the list is now empty, that item was the answer.
2. Otherwise put the last item, y, at the root.
3. While y has a child smaller than y: swap y with its **smaller** child and continue from there.

**Invariant:** every pair is in order except possibly y and its children. Swapping with the smaller child m fixes this level: m now sits above y (m < y) and above its old sibling (m is the smaller of the two), and m is no smaller than its new parent because it used to be that parent's descendant. Only y and its new children can be out of order, one level lower.

Both loops stop at the root or a leaf at the latest. When they stop early, the invariant plus "no violation at x (or y)" means the whole list is a heap again.

## Cost

Every iteration moves one level, and there are at most floor(log2 n) levels to cross.

- **Push:** at most floor(log2 n) swaps and as many comparisons. On random input it is much cheaper, because a new item usually belongs near the bottom. Measured over 2^20 random pushes, the average was about 1.3 swaps per push; in decreasing order (the worst case for a min-heap) it was 18.
- **Pop:** at most floor(log2 n) swaps and 2 floor(log2 n) comparisons (pick the smaller child, then compare it with y). The moved leaf is usually large, so a pop almost always travels most of the way down: up to about 38 comparisons for a million items.

CPython's heapq pops with a refinement due to Floyd: it moves the hole all the way down, promoting the smaller child at each level (one comparison per level), drops y into the leaf it reaches and sifts it up the short distance it usually needs. Beware the names in its source: there `_siftdown` moves an item towards the root and `_siftup` towards the leaves, the opposite of most textbooks.

In Python the constant matters more than the bound. A pure-Python heap like the template below ran about 5 to 11 times slower than heapq (written in C) when pushing and then popping 10^5 to 10^6 random floats. Write your own heap to understand it, or when you need something heapq lacks (changing a priority in place, a d-ary layout); otherwise use heapq.

## When to use it

- In production Python you rarely write these loops: heapq runs them in C. You write them when an interviewer asks you to implement a heap, when you need an operation heapq does not expose (the lazy-deletion card builds a heap with in-place priority changes), or in a language without a ready-made heap.
- C++ gives you the loops as `std::push_heap` and `std::pop_heap` over a vector (that is what `std::priority_queue` uses); Java's `PriorityQueue` hides them.
- The same two loops are the core of every heap variant: d-ary heaps (children of i at d·i + 1 to d·i + d), indexed heaps, heapsort.

## Worked trace

Push 1 into a heap of nine items, then pop. The tree and the list are the same data; watch both.

```steps
A valid min-heap of 9 items: every parent is <= its children
                    2                i   0  1  2  3  4  5  6  7  8
                /       \            a   2  5  3  8  6  4  9 10 12
            5               3
          /   \           /   \
        8       6       4       9
       / \
     10  12
---
push(1): append at index 9, the next free leaf, whose parent is index 4 (value 6)
                    2                i   0  1  2  3  4  5  6  7  8  9
                /       \            a   2  5  3  8  {{6}}  4  9 10 12  {{1}}
            5               3
          /   \           /   \
        8       {{6}}       4       9
       / \     /
     10  12   {{1}}
---
1 < 6: swap up to index 4. Next compare with its parent, index 1 (value 5)
                    2                i   0  1  2  3  4  5  6  7  8  9
                /       \            a   2  {{5}}  3  8  {{1}}  4  9 10 12  6
            {{5}}               3
          /   \           /   \
        8       {{1}}       4       9
       / \     /
     10  12   6
---
1 < 5: swap up to index 1. Next compare with its parent, index 0 (value 2)
                    {{2}}                i   0  1  2  3  4  5  6  7  8  9
                /       \            a   {{2}}  {{1}}  3  8  5  4  9 10 12  6
            {{1}}               3
          /   \           /   \
        8       5       4       9
       / \     /
     10  12   6
---
1 < 2: swap up to index 0. It is the root, so stop: 3 swaps, one per level
                    {{1}}                i   0  1  2  3  4  5  6  7  8  9
                /       \            a   {{1}}  2  3  8  5  4  9 10 12  6
            2               3
          /   \           /   \
        8       5       4       9
       / \     /
     10  12   6
---
pop(): remember the root (1), move the last leaf (6) into the hole. Compare 6 with its children 2 and 3
                    {{6}}                i   0  1  2  3  4  5  6  7  8
                /       \            a   {{6}}  {{2}}  {{3}}  8  5  4  9 10 12
            {{2}}               {{3}}
          /   \           /   \
        8       5       4       9
       / \
     10  12
---
The smaller child 2 < 6: swap down to index 1. Children now: 8, 5
                    2                i   0  1  2  3  4  5  6  7  8
                /       \            a   2  {{6}}  3  {{8}}  {{5}}  4  9 10 12
            {{6}}               3
          /   \           /   \
        {{8}}       {{5}}       4       9
       / \
     10  12
---
The smaller child 5 < 6: swap down to index 4. Index 4 has no children (2 * 4 + 1 = 9 >= 9), so stop and return 1
                    2                i   0  1  2  3  4  5  6  7  8
                /       \            a   2  5  3  8  {{6}}  4  9 10 12
            5               3
          /   \           /   \
        8       {{6}}       4       9
       / \
     10  12
```

## Template

```python
class MinHeap:
    """Binary min-heap in a list: a[(i - 1) // 2] <= a[i] for every i > 0."""

    def __init__(self):
        self.a = []

    def __len__(self):
        return len(self.a)

    def peek(self):
        return self.a[0]                      # IndexError when empty, like heapq

    def push(self, x):
        self.a.append(x)                      # new leaf at the end keeps the tree complete
        self._sift_up(len(self.a) - 1)

    def pop(self):
        a = self.a
        last = a.pop()                        # IndexError when empty
        if not a:
            return last                       # it was the only item
        top, a[0] = a[0], last                # last leaf fills the hole at the root
        self._sift_down(0)
        return top

    def _sift_up(self, i):
        a = self.a
        while i > 0:
            p = (i - 1) // 2
            if not a[i] < a[p]:
                break                         # parent is no larger: heap is valid again
            a[i], a[p] = a[p], a[i]
            i = p

    def _sift_down(self, i):
        a, n = self.a, len(self.a)
        while True:
            smallest = i
            for c in (2 * i + 1, 2 * i + 2):
                if c < n and a[c] < a[smallest]:
                    smallest = c
            if smallest == i:
                return                        # no child is smaller: heap is valid again
            a[i], a[smallest] = a[smallest], a[i]
            i = smallest
```

## Pitfalls

- **Swapping with the left child by default.** If the right child is smaller, promoting the left one leaves a parent larger than its new right child. Always pick the smaller child.
- **Popping a one-item heap.** Code that pops the last item and then writes it to `a[0]` crashes when the list just became empty. The template returns the popped item in that case.
- **Child bounds.** The left child exists only if `2 * i + 1 < n` and the right only if `2 * i + 2 < n`; testing `<= n` reads past the end.
- **`<=` in sift-up.** It still yields a valid heap, but it swaps equal keys for nothing. Equal keys never need to move.
- **Recursion.** A recursive sift is fine (the depth is only log n), but the loop is just as short and has no call overhead.

## Check yourself

Q: Push 0 into the heap `[1, 3, 2, 7]`. Write the list after the append and after each swap.
A: Append at index 4, whose parent is index 1: `[1, 3, 2, 7, 0]`. 0 < 3, swap: `[1, 0, 2, 7, 3]`. 0 < 1 at the root, swap: `[0, 1, 2, 7, 3]`. The root is reached after two swaps.

Q: Why must sift-down swap with the smaller child? Give a three-item example where swapping with the larger child breaks the heap.
A: The child that moves up becomes the parent of its former sibling, so it must be the smaller of the two. With `[9, 1, 2]` (9 just moved to the root), swapping with the larger child 2 gives `[2, 1, 9]`, whose root 2 is larger than its child 1. Swapping with 1 gives the valid `[1, 9, 2]`.

Q: A colleague's pop is `top = a[0]; last = a.pop(); a[0] = last; sift_down(0); return top`. On which input does it crash, and how do you fix it?
A: On a heap with exactly one item: `a.pop()` empties the list, so `a[0] = last` raises `IndexError: list assignment index out of range`. Pop the last item first and return it at once if the list is now empty, as the template does.

Q: At most how many comparisons does the template's pop make on a heap of 1,000,000 items?
A: floor(log2 10^6) = 19 levels to descend, with at most two comparisons per level (one per child): at most 38.

## Lab

- **1046 Last Stone Weight.** Solve it with your `MinHeap` storing negated weights: push `-x`, and negate what you pop. Expected: `[2, 7, 4, 1, 8, 1]` gives 1 and `[3, 7, 2]` gives 2; O(n log n).
- **703 Kth Largest Element in a Stream.** Keep a `MinHeap` of at most k items (the top-k card explains why a min-heap). Expected: k = 3 with initial `[4, 5, 8, 2]`, then adding 3, 5, 10, 9 and 4 returns 4, 5, 5, 8, 8; O(log k) per add.
- **Stress test.** Run 10,000 random push and pop sequences against heapq, asserting the same values come out and that `is_min_heap(h.a)` holds after every operation. Expected: no mismatch. Then plant the "always swap with the left child" bug: a failing sequence appears within the first few sequences.

> [!know]
> You now know how sift-up and sift-down repair one path of the tree, why the smaller child must move up, and why push and pop cost O(log n).

=== primer | Why is building a heap O(n), not O(n log n)? | 15 min
goal: Build a heap bottom-up in linear time, prove the O(n) bound by summing node heights, and know when heapify beats pushing items one at a time
tag: heap-heapify | Bottom-up heapify
link: MIT 6.006 (Spring 2020): Recitation 8 notes (PDF) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/701c2f339890cbf9c0c2a3495d007f26_MIT6_006S20_r08.pdf | 10 min: page 4, 'O(n) Build Heap': the same bound written as a sum over depths, with code that loops backwards over the array
practice: 215

> [!key]
> **Heapify** turns any list into a heap by running sift-down on every parent, from the last parent (index n // 2 - 1) back to the root. A sift-down costs at most the **height** of its node, and most nodes are near the bottom: half are leaves (cost 0), a quarter have height 1, an eighth height 2. The sum of all heights is less than n, so building a heap is O(n). Pushing items one at a time costs each item its **depth** instead, and most nodes are deep, so that build is O(n log n) in the worst case.

## Intuition

Organise a pyramid of teams from the bottom up. First, every small team at the bottom settles who leads it: a tiny job, but there are many such teams. Then each manager one level up compares themselves with their two team leads and steps down if needed, and so on. Each person's work is "how far down might I have to move", which is small for almost everyone; only the person at the very top can travel the full height.

Pushing one at a time is the opposite: every newcomer arrives at the bottom and may climb all the way to the top, and almost everyone arrives on one of the bottom levels.

## How it works

### Why bottom-up order

Sift-down at node i only works if both subtrees of i are heaps already; then it has a single item to place. Processing indices from high to low guarantees that: when you reach i, its children 2i + 1 and 2i + 2 have larger indices, so they were finished earlier, and leaves are one-item heaps from the start.

**Invariant:** after processing index i, every subtree rooted at an index >= i is a heap. When i = 0 has been processed, the whole list is a heap.

### Where to start

Indices n // 2 and above have no children (2i + 1 >= n), so they are leaves and need no work. n // 2 - 1 is the last index with a child, and the loop runs from there down to 0.

### Heapsort for free

Build a heap, then repeatedly swap the root with the last item of the heap region and sift down inside the shrinking region. With a min-heap this leaves the list in descending order, in place: O(n log n) time, O(1) extra space, not stable. That guaranteed bound with no extra memory is why C++'s `std::sort` (introsort) falls back to heapsort when quicksort's recursion gets too deep.

## Cost

Call the **height** of a node the number of edges on the longest path from it down to a leaf. A sift-down that starts at height h makes at most h swaps (and 2h comparisons).

In a heap of n items, at most about n / 2^(h+1) nodes have height h: half are leaves, a quarter sit just above them, and so on. So the total number of swaps is at most

```text
  sum over h >= 0 of   (n / 2^(h+1)) * h   =   (n / 2) * (1/2 + 2/4 + 3/8 + 4/16 + ...)
                                           =   (n / 2) * 2
                                           =   n
```

The series 1/2 + 2/4 + 3/8 + ... converges to 2, which is the whole proof. (The exact counts round up, which adds only a lower-order term.) For a perfect tree you can count exactly: with n = 2^(k+1) - 1 nodes the heights add up to n - k - 1. Fifteen nodes have 8 leaves at height 0, 4 nodes at 1, 2 at 2 and 1 at 3, which is 4 + 4 + 3 = 11 = 15 - 3 - 1.

Pushing one at a time, the item at index i can climb floor(log2(i + 1)) levels, and about half the items land on the bottom level at depth about log2 n, so the worst case is about n log2 n swaps: Θ(n log n). The two builds differ because **height** is small for most nodes while **depth** is large for most nodes.

Swaps per item, measured in CPython with n = 2^20:

| Input | heapify | n separate pushes |
|---|---|---|
| random order | 0.74 | 1.28 |
| decreasing (worst case for a min-heap) | 1.00 | 18.0 |

On random data pushes are cheap on average, so the practical gap is the worst case plus the per-call overhead: `heapq.heapify` on a million floats ran about 3 times faster than a million `heappush` calls in random order, and about 13 times faster in decreasing order.

## When to use it

- **All the items are known before the first pop.** Heapify, then pop as needed. For the kth largest of a fixed array: negate, heapify and pop k times, O(n + k log n). Event simulations and Dijkstra push as they go, so they cannot use it.
- **You need everything sorted.** Just call `sorted`: Timsort is in C, stable and adaptive. Heapsort matters where memory is fixed or the worst case must be guaranteed, as inside introsort.
- **Python:** `heapq.heapify(lst)` is this bottom-up build, in place, returning None. `heapq.nsmallest(k, data)` instead keeps a heap of only k items, which is better for small k or for a stream.

## Worked trace

The worst case for a min-heap is input in decreasing order: every parent must sink all the way.

```steps
Input in decreasing order (the worst case for a min-heap). Leaves (indices 4 to 8) are already one-item heaps; start at the last parent, index n // 2 - 1 = 3
                    9                i   0  1  2  3  4  5  6  7  8
                /       \            a   9  8  7  {{6}}  5  4  3  2  1
            8               7
          /   \           /   \
        {{6}}       5       4       3
       / \
      2   1
---
sift_down(3): 6 sinks to index 8 (1 swap). Every subtree rooted at index >= 3 is now a heap
                    9                i   0  1  2  3  4  5  6  7  8
                /       \            a   9  8  7  {{1}}  5  4  3  2  {{6}}
            8               7
          /   \           /   \
        {{1}}       5       4       3
       / \
      2   {{6}}
---
sift_down(2): 7 sinks to index 6 (1 swap). Every subtree rooted at index >= 2 is now a heap
                    9                i   0  1  2  3  4  5  6  7  8
                /       \            a   9  8  {{3}}  1  5  4  {{7}}  2  6
            8               {{3}}
          /   \           /   \
        1       5       4       {{7}}
       / \
      2   6
---
sift_down(1): 8 sinks to index 3 then index 7 (2 swaps). Every subtree rooted at index >= 1 is now a heap
                    9                i   0  1  2  3  4  5  6  7  8
                /       \            a   9  {{1}}  3  {{2}}  5  4  7  {{8}}  6
            {{1}}               3
          /   \           /   \
        {{2}}       5       4       7
       / \
      {{8}}   6
---
sift_down(0): 9 sinks to index 1 then index 3 then index 8 (3 swaps). Every subtree rooted at index >= 0 is now a heap
                    {{1}}                i   0  1  2  3  4  5  6  7  8
                /       \            a   {{1}}  {{2}}  3  {{6}}  5  4  7  8  {{9}}
            {{2}}               3
          /   \           /   \
        {{6}}       5       4       7
       / \
      8   {{9}}
---
Done: 7 swaps in all, equal to the sum of the heights of the 4 parents (3 + 2 + 1 + 1). Pushing the 9 items one by one in this order would cost 16 swaps
                    1                i   0  1  2  3  4  5  6  7  8
                /       \            a   1  2  3  6  5  4  7  8  9
            2               3
          /   \           /   \
        6       5       4       7
       / \
      8   9
```

## Template

```python
def sift_down(a, i, n):
    """Move a[i] down until it is <= its children; only a[:n] is the heap."""
    while True:
        smallest = i
        for c in (2 * i + 1, 2 * i + 2):
            if c < n and a[c] < a[smallest]:
                smallest = c
        if smallest == i:
            return
        a[i], a[smallest] = a[smallest], a[i]
        i = smallest


def heapify(a):
    """Rearrange list a into a min-heap in place: O(n)."""
    for i in range(len(a) // 2 - 1, -1, -1):  # last parent back to the root
        sift_down(a, i, len(a))


def heapsort_desc(a):
    """Sort a in place, largest first: O(n log n) time, O(1) extra space, not stable."""
    heapify(a)
    for end in range(len(a) - 1, 0, -1):
        a[0], a[end] = a[end], a[0]           # current minimum goes to the back
        sift_down(a, 0, end)                  # the heap is now a[:end]
```

The extra parameter n in `sift_down` is what lets heapsort shrink the heap region while the sorted tail grows behind it.

## Pitfalls

- **Going forwards.** Running sift-down for i = 0, 1, 2, ... works on subtrees that are not heaps yet, and the result is usually not a heap. (Sifting each item *up* in increasing index order does work, but that is the O(n log n) push-by-push build.)
- **Forgetting to heapify at all.** `heapq.heappop` on an arbitrary list does not raise: it returns `lst[0]` and leaves a broken heap behind. Heapify any list you did not build with `heappush`.
- **`h = heapq.heapify(lst)`** sets h to None; the list itself is changed in place.
- **Expecting a stable heapsort.** Equal keys can come out in any order; use `sorted` when stability matters.

## Check yourself

Q: Apply the template's `heapify` to `[5, 4, 3, 2, 1]` and give the list after each `sift_down` call.
A: n = 5, so the parents are indices 1 and 0. sift_down(1): 4's children are 2 and 1, so swap with 1: `[5, 1, 3, 2, 4]`. sift_down(0): 5's children are 1 and 3, swap with 1; at index 1 the children are 2 and 4, swap with 2: `[1, 2, 3, 5, 4]`. (`heapq.heapify` gives the same list here.)

Q: Prove that about half the nodes need no work during heapify, and say which half.
A: Node i has a child only if 2i + 1 < n, that is, only if i < n // 2. So indices n // 2 to n - 1, about half of them, are leaves. A single item is already a heap, so sift-down would do nothing there, and the loop starts at n // 2 - 1.

Q: You need the 100 smallest of 10^7 numbers already in a list. Compare heapify plus 100 pops, `heapq.nsmallest(100, lst)` and `sorted(lst)[:100]`.
A: Heapify plus pops: O(n + 100 log n), in place, but it rearranges your list. `nsmallest`: O(n log 100) in the worst case and close to O(n) in practice, because most items fail the "smaller than the current 100th" test with one comparison; it needs only O(100) extra memory and leaves the list alone. `sorted`: O(n log n) time and a second list of 10^7 references (about 80 MB). All three finish in seconds at this size; `sorted` does the most work and uses the most memory.

## Lab

- **215 Kth Largest Element in an Array.** Negate the numbers, heapify, and pop k times. Expected: O(n + k log n); `[3, 2, 1, 5, 6, 4]` with k = 2 gives 5, and `[3, 2, 3, 1, 2, 4, 5, 5, 6]` with k = 4 gives 4. You will solve it again with a size-k heap in the top-k card.
- **Count the swaps.** Add a swap counter to `sift_down` and run `heapify` on random and on decreasing lists of 2^10, 2^14 and 2^17 items; then count the swaps of pushing the same items one at a time. Expected: heapify stays at or below 1 swap per item at every size (about 0.75 for random input, 1.0 for decreasing), while one-at-a-time pushes in decreasing order grow with log2 n: 8, 12 and 15 swaps per item.

> [!know]
> You now know how to build a heap bottom-up in O(n), why the sum of heights proves it, and when to heapify instead of pushing.

=== primer | How do you use Python's heapq for max-heaps, records and ties? | 14 min
goal: Use heapq correctly for max-heaps, prioritised records, ties and the combined operations, and know what each call costs
tag: heap-heapq | heapq idioms
link: Python docs: heapq, Priority Queue Implementation Notes | https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes | 10 min: the four challenges (stability, incomparable tasks, changing a priority, removal) and the [priority, count, task] recipe; then skim the function list at the top of the page, including the 3.14 max-heap functions
practice: 1046, 973

> [!key]
> heapq is a handful of functions that treat a plain list as a **min-heap**. For a max-heap, push negated numbers (or, from Python 3.14, use `heappush_max` and friends). For records, push tuples `(priority, counter, item)`: tuples compare field by field, so the counter breaks ties in arrival order and the items themselves are never compared. Learn the combined calls `heappushpop` and `heapreplace`, and the helpers `nsmallest`, `nlargest` and `merge`, with their real costs.

## Intuition

heapq has no Heap class. A heap is simply a list you have agreed to change only through heapq's functions, in the same way that a sorted list is one you only change with `bisect.insort`. Nothing enforces the agreement: append to the list directly, sort half of it, or edit an item's priority in place, and heapq will not notice. It will just return wrong answers later.

## How it works

### The calls and what they cost

| Call | Does | Cost |
|---|---|---|
| `heapify(x)` | turn list x into a heap, in place | O(n) |
| `heappush(h, x)` | add x | O(log n) |
| `heappop(h)` | remove and return the smallest | O(log n) |
| `h[0]` | peek at the smallest | O(1) |
| `heappushpop(h, x)` | push x, then pop the smallest; returns x at once if x <= h[0] | O(log n), often O(1) |
| `heapreplace(h, x)` | pop the smallest, then push x; size unchanged | O(log n) |
| `nsmallest(k, it, key=None)`, `nlargest` | the k smallest or largest, as a sorted list | O(n log k) time, O(k) memory |
| `merge(*sorted_iterables, key=None)` | lazily merge already-sorted inputs | O(log k) per item for k inputs |

The core functions are written in C (the `_heapq` module), so one heap operation costs about as much as a few attribute lookups. `nsmallest` and `nlargest` are Python loops over the input that call the C functions; they take shortcuts to `min`/`max` when k is 1 and to `sorted` when k is at least the input's length.

### Max-heaps

For numbers, store `-x` and negate again when you read: `heappush(h, -x)`, `-h[0]`, `-heappop(h)`. For tuples, negate only the numeric fields you want reversed: `(-score, name)` puts the highest score first and, among equal scores, the alphabetically first name. For values you cannot negate (strings, or tuples you want fully reversed), wrap them in a small class whose `__lt__` is reversed, since heapq only ever uses `<`. Python 3.14 added `heapify_max`, `heappush_max`, `heappop_max`, `heappushpop_max` and `heapreplace_max`, so on 3.14 and later you can skip the negation.

### Records and ties

`heappush(h, (priority, task))` works until two tasks share a priority. Then Python compares the tasks: dicts or objects without `<` raise `TypeError: '<' not supported between instances of 'dict' and 'dict'`, and strings silently break ties alphabetically, which may not be what you want. The fix is a unique counter between the priority and the payload: `(priority, next(counter), task)`. Ties then come out first in, first out (a **stable** priority queue), and the comparison never reaches the payload. The docs' alternative is a `@dataclass(order=True)` whose payload field is declared with `field(compare=False)`.

### Other languages

C++ `std::priority_queue<T>` is a max-heap; `std::priority_queue<T, std::vector<T>, std::greater<T>>` is a min-heap. Java's `PriorityQueue<E>` is a min-heap; pass `Comparator.reverseOrder()` for a max-heap, and note that its `remove(Object)` is O(n).

## Cost

The table gives each call's cost. The practical costs worth remembering:

- Tuples cost more to compare than ints, and a `key` function on `nsmallest` runs once per input item. In a hot loop, push precomputed numeric keys.
- `heappushpop(h, x)` beats `heappush` followed by `heappop`: when x is no larger than the top it returns x without touching the heap, and otherwise it does one sift instead of two.
- `heapreplace(h, x)` is the call for a fixed-size heap that is already full (the top-k pattern): one sift instead of two.
- `queue.PriorityQueue` wraps the same heapq calls in a lock for use between threads. Inside one thread it only adds overhead.

## When to use it

| You need | Use |
|---|---|
| the smallest item, once | `min(data)` |
| the k smallest, once, k much smaller than n | `heapq.nsmallest(k, data)` |
| the k smallest, once, k close to n | `sorted(data)[:k]` |
| repeated pops while items keep arriving | a list with `heappush` and `heappop` |
| to merge already-sorted files or iterators | `heapq.merge` |
| the k most common items | `Counter.most_common(k)` (it calls `nlargest` for you) |
| a priority queue shared between threads | `queue.PriorityQueue` |

## Worked trace

Four tasks, two priorities, and a counter that records arrival order:

```steps
push('email', priority 2) stores (2, 0, 'email'); the counter 0 records arrival order
    heap[0] = {{(2, 0, 'email')}}
---
push('page', priority 1) stores (1, 1, 'page'); the counter 1 records arrival order
    heap[0] = {{(1, 1, 'page')}}
    heap[1] = (2, 0, 'email')
---
push('backup', priority 2) stores (2, 2, 'backup'); the counter 2 records arrival order
    heap[0] = {{(1, 1, 'page')}}
    heap[1] = (2, 0, 'email')
    heap[2] = (2, 2, 'backup')
---
push('deploy', priority 1) stores (1, 3, 'deploy'); the counter 3 records arrival order
    heap[0] = {{(1, 1, 'page')}}
    heap[1] = (1, 3, 'deploy')
    heap[2] = (2, 2, 'backup')
    heap[3] = (2, 0, 'email')
---
pop() returns 'page': the smallest priority value comes first, and among equal priorities the lower counter (earlier push) wins
    heap[0] = {{(1, 3, 'deploy')}}
    heap[1] = (2, 0, 'email')
    heap[2] = (2, 2, 'backup')
---
pop() returns 'deploy': the smallest priority value comes first, and among equal priorities the lower counter (earlier push) wins. The strings themselves are never compared
    heap[0] = {{(2, 0, 'email')}}
    heap[1] = (2, 2, 'backup')
```

## Template

```python
import heapq
import itertools


class TaskQueue:
    """Min-priority queue; equal priorities come out first in, first out."""

    def __init__(self):
        self._heap = []
        self._seq = itertools.count()

    def push(self, task, priority):
        heapq.heappush(self._heap, (priority, next(self._seq), task))

    def pop(self):
        priority, _, task = heapq.heappop(self._heap)
        return task, priority

    def __len__(self):
        return len(self._heap)


class Desc:
    """Wrap any comparable value so heapq orders it largest first (max-heap of strings, tuples)."""
    __slots__ = ("x",)

    def __init__(self, x):
        self.x = x

    def __lt__(self, other):
        return other.x < self.x
```

Max-heaps by negation, and the helpers:

```python
import heapq

nums = [3, 1, 4, 1, 5, 9, 2, 6]
max_heap = [-x for x in nums]
heapq.heapify(max_heap)
print(-max_heap[0])                       # 9: peek at the largest
print(-heapq.heappop(max_heap))           # 9
print(heapq.nlargest(3, nums))            # [9, 6, 5]
words = ["pear", "fig", "banana", "kiwi"]
print(heapq.nsmallest(2, words, key=len)) # ['fig', 'pear']: ties keep input order
```

## Pitfalls

- **Negating twice, or not at all.** Negate at every push and every read, and name the list `max_heap` so readers expect it.
- **Negating a tuple.** `-(3, 'a')` is a TypeError; negate the numeric fields inside it.
- **Payload comparisons on ties.** Add the counter, as above.
- **`heapreplace` versus `heappushpop`.** `heapreplace` always removes the old top, even when the new item is smaller, so it can return something larger than what you pushed. In a full top-k heap, call it only after checking `x > h[0]`, or use `heappushpop`.
- **Editing a priority in place.** Changing a field of an object already in the heap does not move it, and the heap is now silently wrong. Push a new entry and discard the old one lazily (see the lazy-deletion card).

## Check yourself

Q: Start with `h = []` and push 5, 1 and 4. What do `heapq.heappushpop(h, 0)` and then `heapq.heapreplace(h, 0)` return, and what is h after each?
A: After the pushes h is `[1, 5, 4]`. `heappushpop(h, 0)` returns 0 straight away because 0 <= h[0], and h is unchanged. `heapreplace(h, 0)` pops 1 and pushes 0, so it returns 1 and h becomes `[0, 5, 4]`.

Q: A Dijkstra implementation pushes `(dist, node)` where node is an instance of a small class without `__lt__`. Most tests pass. Which inputs fail, and what is the fix?
A: Any graph where two entries with equal distances are in the heap together: comparing the tuples falls through to the nodes and raises TypeError. Push `(dist, counter, node)`, or push the node's integer id instead of the object.

Q: You need the three highest-scoring players and, among equal scores, the alphabetically first names. Which single call does it?
A: `heapq.nsmallest(3, players, key=lambda p: (-p.score, p.name))`: the key orders by score descending, then name ascending. `nlargest` with the key `(p.score, p.name)` would break ties towards the alphabetically last name instead.

## Lab

- **1046 Last Stone Weight.** Rewrite your solution with heapq and negation: heapify the negated list, then pop twice per round. Expected: `[2, 7, 4, 1, 8, 1]` gives 1; about ten lines; O(n log n).
- **973 K Closest Points to Origin.** Solve it twice: with `heapq.nsmallest(k, points, key=...)` on the squared distance, and with a size-k max-heap of `(-d2, x, y)` that pops whenever it grows past k. Expected: `[[1, 3], [-2, 2]]` with k = 1 gives `[[-2, 2]]`; `[[3, 3], [5, -1], [-2, 4]]` with k = 2 gives `[[3, 3], [-2, 4]]` in any order; O(n log k), no square roots.

> [!know]
> You now know how to get max-heaps, stable tie-breaking and safe records out of heapq, and which heapq call fits each job.

=== primer | How do you keep the k largest items of a stream? | 14 min
goal: Keep the top k of a stream in O(log k) per item and O(k) memory, and choose between a size-k heap, heapify, sorting and quickselect
tag: heap-topk | Top-k with a size-k heap
link: Wikipedia: Partial sorting | https://en.wikipedia.org/wiki/Partial_sorting#Heap-based_solution | 5 min: 'Heap-based solution' and 'Solution by partitioning selection', the two standard ways to get the k smallest, with their costs
practice: 703, 215, 1642

> [!key]
> To keep the k **largest** items, keep a **min-heap** of size k. Its root is the smallest of your current top k: the bar a newcomer must beat. Each new item either fails against the bar in O(1) or replaces it in O(log k). That is O(n log k) time and O(k) memory, it works on a stream you never store, and at every moment the root is the kth largest so far.

## Intuition

A club has k seats. The doorman only needs to know who the weakest member inside is: anyone stronger gets in, and the weakest member leaves to make room. Keeping the whole queue outside in order, just to admit the best k, would be wasted work.

The counter-intuitive part is the direction. The k largest need a **min**-heap, because the item you must be ready to throw out is the smallest one you are keeping.

## How it works

1. Push items until the heap holds k.
2. For each later item x: if x > heap[0], call `heapreplace(heap, x)` (drop the bar, admit x); otherwise ignore x.
3. At any moment `heap[0]` is the kth largest so far, and `sorted(heap, reverse=True)` is the top k.

**Invariant:** after the first i items, the heap holds exactly the min(i, k) largest of them. It holds while the heap fills. When the heap is full and x arrives: if x <= heap[0], at least k kept items are no smaller than x, so x is not needed and the heap is still right; if x > heap[0], the old bar is now beaten by k items (the other k - 1 plus x), so it drops out and x comes in. With ties at the bar, keeping either copy gives the same values.

### Variants

- **k smallest:** the mirror image, a max-heap of size k (negated keys), whose root is the largest you keep.
- **kth largest after every insertion:** the same invariant, reading `heap[0]` after each add.
- **Top k by a key** (closest points, most frequent words, slowest requests): push `(key, ...)` tuples, or call `heapq.nlargest(k, items, key=...)`, which runs exactly this algorithm.
- **Top k by count:** count first with a `Counter`, then select the k largest counts; `Counter.most_common(k)` does the selection with `nlargest`.

## Cost

Each item costs O(1) when rejected and O(log k) when admitted, so the worst case is O(n log k) time and O(k) extra memory. On random order it is close to linear: the ith item belongs to the top k of the first i items with probability k / i, so only about k ln(n / k) items ever touch the heap, and the rest cost one comparison each.

| Method | Time | Extra memory | Works on a stream? | Best when |
|---|---|---|---|---|
| size-k heap (`nlargest`) | O(n log k) | O(k) | yes | k much smaller than n |
| heapify everything, pop k | O(n + k log n) | none if in place | no | the data is already a list you may rearrange |
| sort, take k | O(n log n) | O(n) | no | k is close to n, or you need it sorted anyway |
| quickselect | O(n) expected, O(n^2) worst | none if in place | no | one kth query on a big in-memory array |

Measured in CPython: counting 2 million Zipf-distributed words (about 50,000 distinct) took about 0.5 s, and picking the 100 most frequent from the counts took roughly 70 to 200 ms with `sorted`, 11 to 17 ms with `nlargest` or a hand-written size-k heap, and 6 to 10 ms with `most_common(100)`, which calls `nlargest` with a C-level key function. (The ranges are from repeated runs on a shared server.) With k = 50,000 the heap's advantage disappears and `nlargest` itself falls back to sorting.

PostgreSQL does the same thing for `ORDER BY ... LIMIT n`: once the input exceeds twice the limit, its sort switches to a bounded heap of n tuples, and `EXPLAIN ANALYZE` reports "Sort Method: top-N heapsort".

## When to use it

Cues: "k largest", "k smallest", "k closest", "k most frequent", "kth largest", "top k", a stream or a file too large to hold, k much smaller than n.

Not a size-k heap when:

- k is close to n: just sort.
- You need one kth element of an in-memory array and speed matters most: quickselect (the sorting module).
- The set changes by deletions as well as insertions: a sorted container, or lazy deletion (a later card).
- You need the maximum of a sliding window: a monotonic deque does it in O(1) amortised per step.

## Worked trace

The three largest of the stream 5, 1, 9, 3, 7, 8, 2:

```steps
x = 5: fewer than k = 3 kept, so push it
    stream {{5}}  1  9  3  7  8  2
    heap   [5]
---
x = 1: fewer than k = 3 kept, so push it
    stream 5  {{1}}  9  3  7  8  2
    heap   [1, 5]
---
x = 9: fewer than k = 3 kept, so push it
    stream 5  1  {{9}}  3  7  8  2
    heap   [1, 5, 9]   bar = heap[0] = 1
---
x = 3 > bar 1: 1 drops out, 3 joins (heapreplace)
    stream 5  1  9  {{3}}  7  8  2
    heap   [3, 5, 9]   bar = heap[0] = 3
---
x = 7 > bar 3: 3 drops out, 7 joins (heapreplace)
    stream 5  1  9  3  {{7}}  8  2
    heap   [5, 7, 9]   bar = heap[0] = 5
---
x = 8 > bar 5: 5 drops out, 8 joins (heapreplace)
    stream 5  1  9  3  7  {{8}}  2
    heap   [7, 8, 9]   bar = heap[0] = 7
---
x = 2 <= bar 7: it cannot be in the top 3, skip in O(1)
    stream 5  1  9  3  7  8  {{2}}
    heap   [7, 8, 9]   bar = heap[0] = 7
---
End: the top 3 are [9, 8, 7] and the 3rd largest is heap[0] = 7
    heap   [7, 8, 9]
```

## Template

```python
import heapq


def k_largest(stream, k):
    """The k largest items of any iterable, largest first: O(n log k) time, O(k) memory."""
    if k <= 0:
        return []
    heap = []                                 # min-heap holding the best k so far
    for x in stream:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:                     # beats the weakest of the k
            heapq.heapreplace(heap, x)
    return sorted(heap, reverse=True)


class KthLargest:
    """kth largest value after each add (needs at least k values once you read it)."""

    def __init__(self, k, nums=()):
        self.k, self.heap = k, []
        for x in nums:
            self.add(x)

    def add(self, x):
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, x)
        elif x > self.heap[0]:
            heapq.heapreplace(self.heap, x)
        return self.heap[0]
```

## Pitfalls

- **Wrong direction.** A max-heap of size k keeps the k smallest. For the largest you need a min-heap.
- **Pushing everything, then popping.** Correct, but O(n) memory and O(n log n) time; the whole point is to cap the heap at k.
- **`heapreplace` before the heap is full,** or on an empty heap (IndexError). Fill it to k first.
- **k = 0, or fewer than k items.** Decide what to return; the template returns `[]` for k <= 0 and every item when there are fewer than k. LeetCode 703 promises at least k items whenever you read.
- **Ties between records.** With `(count, word)` tuples, equal counts fall back to comparing words. Decide whether that order is what the problem wants, and encode it in the key.

## Check yourself

Q: Run the template with k = 2 on the stream 4, 10, 3, 10, 7. What is the heap after each item, and what is returned?
A: `[4]`, then `[4, 10]`; 3 <= 4 so it is skipped; 10 > 4 so the heap becomes `[10, 10]`; 7 <= 10 is skipped. It returns `[10, 10]`: duplicates are separate items, so the second largest is 10.

Q: Why does a rejected item cost O(1), and why does that make the method close to linear on randomly ordered input?
A: Rejecting is one comparison with `heap[0]`; nothing else is touched. In random order the ith item is among the top k so far with probability k / i, so about k ln(n / k) items reach the heap in total. For n = 10^6 and k = 100 that is about 100 × 9.2, roughly 900 heap operations, against a million single comparisons.

Q: Find the 10 slowest requests in a 50 GB access log, one request per line, on a machine with 1 GB of memory. What do you keep, and what does it cost?
A: Read the file line by line and keep a min-heap of at most 10 `(latency, line)` entries, replacing the root whenever a slower request appears. Memory is 10 entries plus one line; time is one pass over the file with O(log 10) work per admitted line. Sorting would need the whole file in memory or an external sort.

## Lab

- **703 Kth Largest Element in a Stream.** Expected: k = 3 with initial `[4, 5, 8, 2]`, then adding 3, 5, 10, 9 and 4 returns 4, 5, 5, 8, 8; O(log k) per add and O(k) memory.
- **215 Kth Largest Element in an Array.** This time keep a size-k min-heap, and compare it with your heapify version and with quickselect. Expected: 5 for `[3, 2, 1, 5, 6, 4]` with k = 2, and 4 for `[3, 2, 3, 1, 2, 4, 5, 5, 6]` with k = 4; O(n log k).
- **1642 Furthest Building You Can Reach (derive it).** You learn the climbs one at a time, but you may change your mind about earlier ones: which climbs deserve the ladders? Expected: heights `[4, 2, 7, 6, 9, 14, 12]`, bricks 5, ladders 1 gives 4; `[4, 12, 2, 7, 3, 18, 20, 3, 19]`, bricks 10, ladders 2 gives 7; `[14, 3, 19, 3]`, bricks 17, ladders 0 gives 3; O(n log L) for L ladders.

> [!know]
> You now know how to keep the top k of a stream with a size-k min-heap and when sorting, heapify or quickselect is the better choice.

=== primer | How do you merge k sorted lists with a heap? | 14 min
goal: Merge k sorted sources in O(N log k) with a heap holding one candidate per source, and apply the same idea to lists that are only implicitly sorted
tag: heap-kmerge | k-way merge
link: Wikipedia: k-way merge algorithm | https://en.wikipedia.org/wiki/K-way_merge_algorithm#Heap | 5 min: the 'Heap' subsection, then 'Tournament Tree' for the replacement-selection idea used to build long sorted runs
link: Python docs: heapq.merge | https://docs.python.org/3/library/heapq.html#heapq.merge | 2 min: the lazy, iterator-based merge with key and reverse, and the warning that inputs must already be sorted
practice: 373, 632

> [!key]
> Put the first item of each sorted list in a min-heap as `(value, list id, position)`. Pop the smallest, output it, and push the next item from the same list. The smallest item not yet output is always at the front of some list, and the heap holds exactly those fronts, so every pop is correct; the heap never holds more than k entries, so N items cost O(N log k). `heapq.merge` does this lazily over iterators.

## Intuition

Several bank queues must merge into one line ordered by ticket number. Each queue is already in ticket order, so you never need to look past the person at the front of each queue: compare the k front people, let the smallest ticket through, and the next person in that queue steps forward.

## How it works

**Invariant:** the heap holds exactly one entry per non-empty list: that list's first item not yet output. Each list is sorted, so the smallest item left anywhere is the smallest of these fronts, which is the heap's root. Popping it and pushing its successor from the same list restores the invariant.

The list id in the tuple does two jobs. It tells you where to fetch the successor, and it breaks ties: equal values come out in list order (a stable merge), and the comparison never reaches anything that cannot be compared. `heapq.merge` uses the same trick internally.

### Lists that only exist implicitly

Nothing requires the lists to be stored. Anything that produces items in sorted order per source works:

- **Pairs from two sorted arrays, by sum.** For each index i of the first array, the pairs (i, 0), (i, 1), (i, 2), ... come in increasing order of sum, so each i is a sorted list. Seed the heap with (i, 0) for the first k values of i (no other row can contribute to the k smallest), and when (i, j) pops, push (i, j + 1).
- **A matrix whose rows are sorted.** Each row is a sorted list; the kth smallest overall is the kth item popped.
- **The smallest range touching every list.** Keep one current item per list in the heap plus the maximum of those items. The range [heap minimum, maximum] touches every list; to shrink it, only advancing the list that holds the minimum can help. Stop when that list runs out.

## Cost

Each of the N items is pushed once and popped once on a heap of at most k entries: O(N log k) time and O(k) extra memory, plus the output.

| Method | Time | Extra memory | Notes |
|---|---|---|---|
| heap merge (`heapq.merge`) | O(N log k) | O(k) | lazy; streams from files |
| scan the k fronts every step | O(N k) | O(k) | fine when k is tiny |
| merge pairwise, one list after another | O(N k) | O(N) | the easy wrong choice |
| merge in pairs, tournament style | O(N log k) | O(N) | like merge sort's merge passes |
| concatenate and `sorted` | O(N log N) worst | O(N) | Timsort detects the k runs and merges them |

Measured in CPython on N = 10^6 floats already in memory: `sorted(itertools.chain(*runs))` took 0.07 s for k = 2 and 0.43 s for k = 1,000, while `list(heapq.merge(*runs))` took 0.48 s and 1.85 s. In memory, Timsort's C merging of runs wins. `heapq.merge` earns its place when the inputs are iterators over files or sockets, when you want the first items before reading everything, or when the data does not fit in memory at all.

## When to use it

Cues: "merge k sorted ...", several sorted files, logs from several servers each ordered by time, "kth smallest" over sorted rows, any setting where each source is sorted and you need one global order.

In real systems:

- **External sorting** (this stage's project): sort chunks that fit in memory, write them out as sorted runs, then k-way merge the runs. PostgreSQL's tuplesort works this way, with a heap holding the front tuple of each run; since version 15 it uses a plain balanced k-way merge instead of the tape-era polyphase merge.
- **LSM-tree storage engines** merge sorted memtables and SSTables on every range scan and compaction. RocksDB's `MergingIterator` uses a heap; LevelDB's merger scans its children linearly, with a source comment that a heap might be worth it if there were many children, because LevelDB expects only a few.

## Worked trace

Merge A = [1, 4, 7], B = [2, 5, 8] and C = [3, 6]. Heap entries are (value, list, position):

```steps
Seed the heap with the head of each list as (value, list, index); heapify
    A = [1, 4, 7]  B = [2, 5, 8]  C = [3, 6]
    heap   {{(1,A,0)}}  (2,B,0)  (3,C,0)
    output []
---
Pop 1 from A, output it, push A's next item 4
    A = [1, 4, 7]  B = [2, 5, 8]  C = [3, 6]
    heap   {{(2,B,0)}}  (4,A,1)  (3,C,0)
    output [1]
---
Pop 2 from B, output it, push B's next item 5
    A = [1, 4, 7]  B = [2, 5, 8]  C = [3, 6]
    heap   {{(3,C,0)}}  (4,A,1)  (5,B,1)
    output [1, 2]
---
Pop 3 from C, output it, push C's next item 6
    A = [1, 4, 7]  B = [2, 5, 8]  C = [3, 6]
    heap   {{(4,A,1)}}  (6,C,1)  (5,B,1)
    output [1, 2, 3]
---
Pop 4 from A, output it, push A's next item 7
    A = [1, 4, 7]  B = [2, 5, 8]  C = [3, 6]
    heap   {{(5,B,1)}}  (6,C,1)  (7,A,2)
    output [1, 2, 3, 4]
---
Pop 5 from B, output it, push B's next item 8
    A = [1, 4, 7]  B = [2, 5, 8]  C = [3, 6]
    heap   {{(6,C,1)}}  (8,B,2)  (7,A,2)
    output [1, 2, 3, 4, 5]
---
... and so on until every list is used up
    A = [1, 4, 7]  B = [2, 5, 8]  C = [3, 6]
    heap   (empty)
    output [1, 2, 3, 4, 5, 6, 7, 8]
```

## Template

```python
import heapq


def merge_sorted(lists):
    """Yield the items of k sorted lists in sorted order: O(N log k) time, O(k) extra space."""
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]
    heapq.heapify(heap)
    while heap:
        value, i, j = heap[0]
        yield value
        if j + 1 < len(lists[i]):
            heapq.heapreplace(heap, (lists[i][j + 1], i, j + 1))   # successor from the same list
        else:
            heapq.heappop(heap)                                    # list i is used up
```

With iterators, use the library version; files opened with `open()` work the same way as these in-memory ones:

```python
import heapq
import io

a = io.StringIO("2026-11-01T10:00:01 GET /\n2026-11-01T10:00:05 GET /api\n")
b = io.StringIO("2026-11-01T10:00:02 POST /login\n2026-11-01T10:00:09 GET /\n")
for line in heapq.merge(a, b, key=lambda s: s[:19]):    # merge on the timestamp
    print(line, end="")
```

## Pitfalls

- **Ties that compare payloads.** `(value, iterator)` crashes on equal values because iterators do not support `<`; put a list id in the second position.
- **Seeding too much.** For the k smallest pairs, pushing all n1 × n2 sums defeats the purpose; seed at most k rows and expand lazily.
- **Duplicate expansion.** If a popped (i, j) pushed both (i + 1, j) and (i, j + 1), the same cell could enter the heap twice. Either keep a visited set or seed one entry per row as above, which reaches every cell exactly once.
- **Empty lists** when seeding: `lst[0]` raises on an empty list, so filter them out.
- **Unsorted inputs.** `heapq.merge` does not check; unsorted inputs give unsorted output, silently.

## Check yourself

Q: In the trace, after 1, 2, 3, 4 and 5 have been output, what is in the heap, and what are the next two outputs?
A: (6, C, 1), (7, A, 2) and (8, B, 2). The next output is 6; C is then used up, so the heap shrinks to two entries. The output after that is 7, after which A is used up and only (8, B, 2) remains.

Q: Why does the heap never need more than k entries, and what does that buy in an external sort of 100 GB with 1 GB of memory?
A: Each list contributes only its current front. With 100 sorted runs of 1 GB each, the merge needs one heap entry and one read buffer per run, so all 100 runs merge in a single pass, reading and writing every byte once, with O(N log 100) comparisons.

Q: LevelDB merges its children by scanning their fronts linearly. When is that the better choice than a heap?
A: When k is tiny, a handful of levels or files: a scan costs k - 1 comparisons per output with no heap bookkeeping, which for k between 2 and about 8 is as cheap as or cheaper than a heap's log k swaps and comparisons. The O(N k) cost only hurts as k grows, which is why engines that merge many inputs at once use a heap.

## Lab

- **373 Find K Pairs with Smallest Sums.** Treat each index i of nums1 as the sorted list of pairs (i, 0), (i, 1), ...; seed with j = 0 for the first k values of i. Expected: `[1, 7, 11]`, `[2, 4, 6]`, k = 3 gives `[[1, 2], [1, 4], [1, 6]]`; `[1, 1, 2]`, `[1, 2, 3]`, k = 2 gives `[[1, 1], [1, 1]]`; O(k log k).
- **632 Smallest Range Covering Elements from K Lists (stretch).** A heap of fronts plus the running maximum of the fronts. Expected: `[[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]` gives `[20, 24]`; `[[1, 2, 3], [1, 2, 3], [1, 2, 3]]` gives `[1, 1]`; O(N log k).

> [!know]
> You now know how to merge k sorted sources with a heap of k fronts, why it costs O(N log k), and when Timsort or a linear scan is the better tool.

=== lab | Top-k over a stream: your heap against heapq, sort and Counter | 45 min
goal: Stress-test your own binary heap against heapq, then measure four ways to find the most frequent words in two million and see where each one wins
link: Python docs: heapq.nlargest | https://docs.python.org/3/library/heapq.html#heapq.nlargest | 2 min: when nlargest beats sorted, and when min or max is the better call

You will check your heap against heapq with random operations (the brute-force oracle habit from the foundations), plant a bug and watch the tester catch it, then measure what a size-k heap buys over sorting on a realistic workload. Every script runs in under a minute.

## Setup

- Python 3.10 or later, standard library only.
- Your `MinHeap` class from the push and pop card, saved as `myheap.py`.

## Steps

1. **Stress-test the heap.** Save this as `stress_heap.py` and run it:

```python
import heapq
import random

from myheap import MinHeap


def check(trials=10_000, seed=0):
    rng = random.Random(seed)
    for t in range(trials):
        mine, ref, ops = MinHeap(), [], []
        for _ in range(rng.randint(0, 60)):
            if ref and rng.random() < 0.45:
                ops.append("pop")
                got, want = mine.pop(), heapq.heappop(ref)
                assert got == want, (t, ops, got, want)
            else:
                x = rng.randint(-20, 20)
                ops.append(f"push {x}")
                mine.push(x)
                heapq.heappush(ref, x)
            assert all(mine.a[(i - 1) // 2] <= mine.a[i] for i in range(1, len(mine.a))), ops
    print("ok:", trials, "random sequences")


check()
```

2. **Break it on purpose.** In `_sift_down`, replace the smaller-child search with "swap with the left child whenever it is smaller than the parent". Run the tester again, read the failing operation list it prints, and replay it by hand. Then restore the correct code.
3. **Time it.** Push 10^5 random floats and then pop them all, once with your heap and once with `heapq.heappush` and `heapq.heappop`; time both with `time.perf_counter()`. Repeat at 10^6 if you are patient.
4. **The 100 most frequent words.** Save this as `topk_words.py` and run it with `python topk_words.py 100`:

```python
import heapq
import random
import sys
import time
from collections import Counter


def zipf_words(n_words, vocab, seed=2):
    """A stream of n_words drawn from vocab words with Zipf-like frequencies."""
    rng = random.Random(seed)
    words = [f"w{i}" for i in range(vocab)]
    weights = [1 / (r + 1) for r in range(vocab)]
    return rng.choices(words, weights, k=n_words)


def top_k_heap(counts, k):
    heap = []                                  # min-heap of (count, word), size <= k
    for word, c in counts.items():
        if len(heap) < k:
            heapq.heappush(heap, (c, word))
        elif (c, word) > heap[0]:
            heapq.heapreplace(heap, (c, word))
    return sorted(heap, reverse=True)


def timed(label, fn):
    t = time.perf_counter()
    result = fn()
    print(f"{label:<12} {1000 * (time.perf_counter() - t):8.1f} ms")
    return result


k = int(sys.argv[1]) if len(sys.argv) > 1 else 100
stream = zipf_words(2_000_000, 50_000)
counts = timed("Counter", lambda: Counter(stream))
key = lambda kv: (kv[1], kv[0])
a = timed("sorted", lambda: sorted(counts.items(), key=key, reverse=True)[:k])
b = timed("nlargest", lambda: heapq.nlargest(k, counts.items(), key=key))
c = timed("most_common", lambda: counts.most_common(k))
d = timed("own size-k", lambda: top_k_heap(counts, k))
assert a == b == [(w, n) for n, w in d]
assert [n for _, n in a] == [n for _, n in c]   # most_common may order equal counts differently
print(len(counts), "distinct words; top 3:", a[:3])
```

5. **Vary k.** Run it again with k = 10, 1,000 and 50,000, and put the four timings in a table.
6. **Memory on a true stream.** Find the 100 largest of 2 million random numbers produced by a generator, once with `heapq.nlargest(100, gen)` and once with `sorted(list(gen))[-100:]`, measuring peak memory with `tracemalloc.start()` and `tracemalloc.get_traced_memory()`. (tracemalloc slows everything down, so ignore the timings in this step.)

## What you should see

Measured with CPython 3.12 on a busy shared server; your absolute numbers will differ, the ratios should not.

- Step 1 prints `ok: 10000 random sequences`. With the planted bug in step 2, the first or second sequence already fails, and the failing list of operations is short enough to replay on paper.
- Step 3: your heap is about 5 to 11 times slower than heapq, the price of running sift loops in Python instead of C.
- Step 4: counting 2 million words takes about half a second and finds 49,732 distinct words, with w0 first (175,123 times). Selecting the top 100 takes roughly 70 to 200 ms with `sorted`, 11 to 17 ms with `nlargest` or your size-k heap, and 6 to 10 ms with `most_common`, which calls `nlargest` with a C-level key. The selection is cheap next to the counting, whichever you choose.
- Step 5: for k from 10 to 1,000 the heap methods stay far ahead of sorting. At k = 50,000 (more than the number of distinct words) `nlargest` simply calls `sorted`, and your own heap is no faster than sorting: a size-k heap only pays when k is much smaller than n.
- Step 6: `nlargest` peaks well under 1 MB, while building the list and sorting it peaks at about 90 MB for 2 million floats.

## Check yourself

Q: Why can `most_common(100)` beat your own size-k heap even though both run the same algorithm?
A: `most_common` calls `heapq.nlargest` with `operator.itemgetter(1)` as the key, which runs in C, and nlargest's loop compares single integers. Your heap compares `(count, word)` tuples in a Python-level loop. Same O(n log k), smaller constant.

> [!know]
> You now know how to prove a heap correct against heapq with random operations, and when a size-k heap beats sorting in time and memory.

=== primer | How do two heaps give you a running median? | 13 min
goal: Maintain the median of a growing stream in O(log n) per insert and O(1) per query with a max-heap and a min-heap, and extend the idea to other quantiles and to sliding windows
tag: heap-twoheaps | Two heaps around the middle
link: Python docs: heapq, Other Applications | https://docs.python.org/3/library/heapq.html#other-applications | 3 min: the official running-median recipe; it uses the Python 3.14 max-heap functions, so on older versions negate as in this card
practice: 295, 480

> [!key]
> Split the numbers seen so far into a **lower half** in a max-heap and an **upper half** in a min-heap. Keep two invariants: everything in the lower half is <= everything in the upper half, and the lower half is the same size as the upper half or one larger. The median is then the top of the lower half (odd count) or the average of the two tops (even count). Each insert is at most three heap operations, O(log n); reading the median is O(1).

## Intuition

Line people up by height with a rope across the middle. You never need the whole line in order: only the tallest person left of the rope and the shortest person right of it. A max-heap hands you the first, a min-heap the second. When a newcomer arrives, they join the correct side, and if one side gets too long, the person nearest the rope steps across.

## How it works

### Insert

1. Push x into the lower half (a max-heap, stored negated in heapq).
2. Move the lower half's largest item into the upper half.
3. If the upper half is now bigger, move its smallest item back into the lower half.

Why both invariants hold afterwards: step 2 moves the largest of (lower half plus x) to the right, so whatever x was, everything left behind is no larger than everything on the right. Step 3, if needed, moves the smallest item on the right to the left, which also keeps the order. Before the insert the sizes were equal or the lower half was one larger; step 2 makes the upper half one larger or equal, and step 3 restores "equal or lower one larger".

Routing every insert through the lower half and out again costs an extra heap operation or two, but you never have to reason about which side x belongs on, or about empty heaps.

### Query

With an odd count the median is the lower top, `-lo[0]`; with an even count it is `(-lo[0] + hi[0]) / 2`.

### Variants

- **Any fixed quantile.** For the 90th percentile, keep the lower heap at about 90% of the items and read its top; the same three steps work with a different size rule.
- **Sliding window median.** Items also leave the window, and a heap cannot delete from its middle. Mark leaving items dead and discard them when they reach a top (lazy deletion, the next card), and balance on the counts of live items.

## Cost

- **add:** at most three pushes or pops on heaps of about n / 2 items: O(log n).
- **median:** O(1), just two peeks.
- **memory:** O(n), because every number is stored; an exact median needs that in the worst case.

| Method | add | median | Notes |
|---|---|---|---|
| two heaps | O(log n) | O(1) | the standard answer |
| `bisect.insort` into a sorted list | O(n) (shifting) | O(1) | fast C memmove, fine up to about 10^5 items |
| `SortedList` | O(log n) amortised | O(log n) by index | also supports deletion, so sliding windows are easy |
| quickselect per query | O(1) | O(n) | only if queries are rare |

For approximate percentiles over huge streams, production systems use sketches with small fixed memory instead; a later module covers them.

## When to use it

Cues: "median of a data stream", "the middle value after each insertion", "balance two halves", or any rule that needs the largest of a lower group and the smallest of an upper group at the same time.

Not when: you need one median of fixed data (sort, or quickselect once); arbitrary deletions are frequent (a `SortedList` is simpler); you need percentiles of billions of values (sketches).

## Worked trace

The stream 5, 15, 1, 3, 8, 7, with the halves shown sorted for readability (inside the heaps they are in heap order):

```steps
add(5): median = 5, the top of the lower half
    lower half (max-heap) [5]   top {{5}}
    upper half (min-heap) []   top -
---
add(15): median = 10.0, the average of the two tops 5 and 15
    lower half (max-heap) [5]   top {{5}}
    upper half (min-heap) [15]   top {{15}}
---
add(1): median = 5, the top of the lower half
    lower half (max-heap) [5, 1]   top {{5}}
    upper half (min-heap) [15]   top {{15}}
---
add(3): median = 4.0, the average of the two tops 3 and 5
    lower half (max-heap) [3, 1]   top {{3}}
    upper half (min-heap) [5, 15]   top {{5}}
---
add(8): median = 5, the top of the lower half
    lower half (max-heap) [5, 3, 1]   top {{5}}
    upper half (min-heap) [8, 15]   top {{8}}
---
add(7): median = 6.0, the average of the two tops 5 and 7
    lower half (max-heap) [5, 3, 1]   top {{5}}
    upper half (min-heap) [7, 8, 15]   top {{7}}
```

## Template

```python
import heapq


class RunningMedian:
    """lo: max-heap (stored negated) of the smaller half; hi: min-heap of the larger half.
    Invariants: max(lo) <= min(hi), and len(lo) == len(hi) or len(hi) + 1."""

    def __init__(self):
        self.lo, self.hi = [], []

    def add(self, x):
        heapq.heappush(self.lo, -x)                         # 1. x joins the lower half
        heapq.heappush(self.hi, -heapq.heappop(self.lo))    # 2. lower half's largest moves up
        if len(self.hi) > len(self.lo):                     # 3. restore the size rule
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def median(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2
```

Steps 1 and 2 can be fused into `heapq.heappush(self.hi, -heapq.heappushpop(self.lo, -x))`, which skips the sift when x is the new maximum.

## Pitfalls

- **Pushing x straight into the smaller heap.** The sizes balance but the order breaks; see the third question below.
- **Forgetting the minus sign** when reading the lower top, so the median comes out negative.
- **Integer division.** `(a + b) // 2` floors, losing the .5 and rounding negative averages down; use `/ 2` and return a float, as LeetCode 295 expects.
- **Peeking into an empty heap.** Read `hi[0]` only when the count is even (so hi is non-empty); with the size rule, lo is non-empty as soon as anything has been added.

## Check yourself

Q: Continue the trace: after 5, 15, 1, 3, 8 and 7, add 9. What are the two halves and the median?
A: 9 enters the lower half and is its largest, so it moves straight up: lower {5, 3, 1}, upper {7, 8, 9, 15}. The upper half is now bigger, so its smallest, 7, moves down: lower {7, 5, 3, 1}, upper {8, 9, 15}. Seven numbers, so the median is the lower top, 7 (sorted: 1 3 5 7 8 9 15).

Q: Why does the insert go through the lower heap and back instead of comparing x with the two tops?
A: Pushing into the lower heap and then moving its maximum across guarantees that the largest of (lower half plus x) ends up on the right, so the order invariant holds whatever x is; the final size fix moves only an extreme item, which cannot break the order. Comparing with the tops also works, but needs extra cases for empty heaps and ties.

Q: Spot the bug: `if len(lo) > len(hi): heappush(hi, x)` `else: heappush(lo, -x)`, with nothing else.
A: It balances sizes and ignores order. Adding 100, 1 and 50 gives lo = {100, 50} and hi = {1}, so it reports 100 as the median of {1, 50, 100} instead of 50. Fix: push into one heap, move that heap's extreme across, then rebalance the sizes.

## Lab

- **295 Find Median from Data Stream.** Expected: addNum(1), addNum(2), then findMedian() gives 1.5; addNum(3), then findMedian() gives 2.0; O(log n) per add and O(1) per median.
- **480 Sliding Window Median (stretch).** Add lazy deletion from the next card and balance on live counts. Expected: `[1, 3, -1, -3, 5, 3, 6, 7]` with k = 3 gives `[1.0, -1.0, -1.0, 3.0, 5.0, 6.0]`; `[1, 2, 3, 4, 2, 3, 1, 4, 2]` with k = 3 gives `[2.0, 3.0, 3.0, 3.0, 2.0, 3.0, 2.0]`; O(n log n).

> [!know]
> You now know how to keep a running median with two heaps, why the routing through one heap keeps both invariants, and how the idea extends to quantiles and windows.

=== primer | How do you delete or reprioritise an item buried in a heap? | 16 min
goal: Remove or update arbitrary heap entries with lazy deletion, keep the garbage bounded, and know when an indexed heap with a position map is worth its extra code
tag: heap-lazy | Lazy deletion and indexed heaps
link: cp-algorithms: Dijkstra on sparse graphs | https://cp-algorithms.com/graph/dijkstra_sparse.html#priority_queue | 5 min: the 'priority_queue' section: never delete stale pairs, push a fresh pair on every improvement, and skip popped pairs that no longer match
link: Go docs: container/heap, Fix | https://pkg.go.dev/container/heap#Fix | 3 min: Fix and Remove, an indexed heap's update and delete in O(log n), and the PriorityQueue example in which every item stores its own index
practice: hr:qheap1, 480

> [!key]
> A heap can only remove its top cheaply. To delete an entry from the middle, **mark it dead** and leave it where it is; whenever you look at the top, pop dead entries first. To change a priority, push a new entry and mark the old one dead. Each entry is pushed once and popped at most once, so this **lazy deletion** costs O(log n) amortised per operation; the price is memory for dead entries, reclaimed by an occasional rebuild. When you need true in-place updates, keep a **position map** from item to index and sift the item up or down: an **indexed heap**, O(log n) in the worst case.

## Intuition

A deli counter with numbered tickets: when someone leaves the queue, nobody reprints the list; their number is crossed off. When a crossed-off number is called, nobody answers, and the next number is called straight away. The cost of the departure is paid only when that number reaches the front, and it is tiny.

## How it works

### Lazy deletion

State: the heap list, a record of what is dead, and a count of live items.

- **Delete x:** record it as dead. If values can repeat, keep a `Counter` of dead copies; for unique records, a set of ids or a flag inside the entry is enough. O(1).
- **Top or pop:** while the root is dead, pop it (and decrement its dead count). Then the root is the true minimum.
- **Size:** keep your own live counter; `len(heap)` includes the dead.
- **Change a priority:** push a new entry with the new priority and mark the old entry dead. The heapq docs' recipe keeps a dict from each task to its current entry and overwrites the old entry's task field with a REMOVED marker.

**Invariant:** the live items are the heap's entries minus the dead copies, and after cleaning, the root is live. Dead entries deeper down do no harm, because you only ever read the root.

### Keeping the garbage bounded

Dead entries stay until they surface. If deletions outnumber pops, the heap fills with garbage, so rebuild now and then: filter out the dead entries and heapify, O(n). Production code does exactly this:

- **asyncio** leaves cancelled timer handles in its heap. When more than half of over 100 scheduled handles are cancelled, the loop rebuilds the heap with `heapq.heapify`; otherwise it just pops cancelled handles off the top.
- **Go's runtime** counts "zombie" timers in each processor's heap and forces a cleanup once they exceed a quarter of it.
- **Kafka's** old request purgatory, built on Java's heap-based `DelayQueue`, left completed requests in the queue to be purged later; when purging fell behind, brokers could run out of memory. That is one reason it was replaced by timing wheels (see the scheduling card).

### Indexed heap (decrease-key)

Keep `pos[key]`, the key's index in the heap list, and update it for both entries on every swap. Then:

- **set(key, p):** overwrite the priority at `pos[key]`, then sift up and down (only one of them will move it).
- **remove(key):** swap it with the last entry, pop it off the end, and sift the moved entry up or down.

Go's `heap.Fix` and `heap.Remove` are exactly these operations; your element type stores its own index. Java's `ScheduledThreadPoolExecutor` does the same internally: each scheduled task remembers its `heapIndex`, so a cancelled task can be removed in O(log n) without a search when the remove-on-cancel policy is enabled.

## Cost

- **Lazy deletion:** every entry ever pushed is popped at most once, so m operations cost O(m log m) in total, O(log m) amortised each, where m counts dead entries too. A single `top()` can pop many dead entries, but each of those pops was paid for by an earlier deletion. Memory is O(entries pushed since the last rebuild), not O(live items).
- **Indexed heap:** O(log n) worst case per operation, memory O(live items), but every swap also writes two dict entries, so in Python it runs noticeably slower than heapq with lazy deletion.

| You need | Use |
|---|---|
| occasional deletions, mostly pops | lazy deletion on heapq |
| many priority changes per item, tight memory | an indexed heap |
| deletions plus the minimum, the maximum or ranks | `SortedList` or a balanced tree |
| Dijkstra in Python | lazy: push duplicates, skip stale pops |

## When to use it

Cues: "remove an element", "cancel", "update the priority", a heap over a sliding window, timers that can be stopped, Dijkstra's "decrease-key".

## Worked trace

A lazy min-heap of values that may repeat, with a Counter of dead copies:

```steps
push(4)
    heap [4]
    dead {}   live size 1
---
push(9)
    heap [4, 9]
    dead {}   live size 2
---
push(2)
    heap [2, 9, 4]
    dead {}   live size 3
---
push(7)
    heap [2, 7, 4, 9]
    dead {}   live size 4
---
remove(2): just count it as dead, O(1); the heap is untouched
    heap [2, 7, 4, 9]
    dead {2: 1}   live size 3
---
remove(4): just count it as dead, O(1); the heap is untouched
    heap [2, 7, 4, 9]
    dead {2: 1, 4: 1}   live size 2
---
top(): pop 2 dead entries off the top, then answer 7
    heap [7, 9]
    dead {}   live size 2
---
remove(7): just count it as dead, O(1); the heap is untouched
    heap [7, 9]
    dead {7: 1}   live size 1
---
push(1)
    heap [1, 9, 7]
    dead {7: 1}   live size 2
---
top(): heap[0] = 1 is live, answer 1
    heap [1, 9, 7]
    dead {7: 1}   live size 2
```

## Template

```python
import heapq
from collections import Counter


class LazyMinHeap:
    """Min-heap that can remove any stored value, by lazy deletion.
    Invariant: live items = what is in self.heap minus the copies counted in self.dead."""

    def __init__(self):
        self.heap = []
        self.dead = Counter()                 # value -> copies deleted but still in the heap
        self.size = 0                         # live items only

    def push(self, x):
        heapq.heappush(self.heap, x)
        self.size += 1

    def remove(self, x):
        """Delete one copy of x, which must be live (QHEAP1 guarantees it)."""
        self.dead[x] += 1
        self.size -= 1

    def _clean_top(self):
        heap, dead = self.heap, self.dead
        while heap and dead[heap[0]]:
            dead[heap[0]] -= 1
            heapq.heappop(heap)

    def top(self):
        self._clean_top()
        return self.heap[0]

    def pop(self):
        self._clean_top()
        self.size -= 1
        return heapq.heappop(self.heap)

    def compact(self):
        """Drop every dead entry and rebuild in O(n); worth it once most entries are dead."""
        keep = []
        for x in self.heap:
            if self.dead[x]:
                self.dead[x] -= 1
            else:
                keep.append(x)
        heapq.heapify(keep)
        self.heap = keep

    def __len__(self):
        return self.size
```

When you need in-place updates, the indexed version:

```python
class IndexedMinHeap:
    """Min-heap of keys by priority with set(key, p) and remove(key) in O(log n).
    pos[key] is the key's index in self.a and is updated on every swap."""

    def __init__(self):
        self.a = []                           # [priority, key] pairs
        self.pos = {}

    def __len__(self):
        return len(self.a)

    def set(self, key, p):
        """Insert key, or change its priority in either direction."""
        if key in self.pos:
            self.a[self.pos[key]][0] = p
        else:
            self.a.append([p, key])
            self.pos[key] = len(self.a) - 1
        self._up(self.pos[key])
        self._down(self.pos[key])

    def pop(self):
        """Remove and return (key, priority) with the smallest priority."""
        key = self.a[0][1]
        return key, self.remove(key)

    def remove(self, key):
        i = self.pos[key]
        self._swap(i, len(self.a) - 1)        # move it to the end, where removal is free
        p, _ = self.a.pop()
        del self.pos[key]
        if i < len(self.a):                   # the item swapped into i may need to move
            moved = self.a[i][1]
            self._up(i)
            self._down(self.pos[moved])
        return p

    def _swap(self, i, j):
        a = self.a
        a[i], a[j] = a[j], a[i]
        self.pos[a[i][1]], self.pos[a[j][1]] = i, j

    def _up(self, i):
        while i > 0 and self.a[i][0] < self.a[(i - 1) // 2][0]:
            self._swap(i, (i - 1) // 2)
            i = (i - 1) // 2

    def _down(self, i):
        n = len(self.a)
        while True:
            m = i
            for c in (2 * i + 1, 2 * i + 2):
                if c < n and self.a[c][0] < self.a[m][0]:
                    m = c
            if m == i:
                return
            self._swap(i, m)
            i = m
```

## Pitfalls

- **Reading `heap[0]` without cleaning.** The root may be dead; always go through `top()`.
- **Using `len(heap)` as the size.** It counts dead entries; keep a live counter.
- **Deleting something that is not there.** With a dead Counter, a phantom deletion later kills a legitimate copy pushed afterwards. Delete only items you know are live, or check against a live Counter first.
- **A set for repeatable values.** If the same value can be in the heap twice, a set cannot say how many copies are dead; use a Counter.
- **Unbounded garbage.** A long-running service that cancels most of its timers needs a rebuild rule, or memory grows without limit.
- **A missed `pos` update** in an indexed heap: one forgotten swap and later updates move the wrong entry. Route every swap through one helper, as `_swap` does.

## Check yourself

Q: Continue the trace from its last state: call `remove(1)`, then `top()`. Which entries are popped, and what is returned?
A: `remove(1)` records 1 as dead: dead {7: 1, 1: 1}, live size 1. `top()` pops the dead 1; the new root 7 is also dead, so it is popped too; the root is now 9, which is live, so `top()` returns 9 and the heap is `[9]`.

Q: One `top()` call can pop many dead entries. Why is lazy deletion still O(log n) amortised per operation?
A: Each entry is pushed once and popped at most once in its lifetime. Charge the pop of a dead entry to the `remove` that killed it: over any sequence of m operations, the total number of pops never exceeds the number of pushes, so the total work is O(m log m), even if a single call does a burst of pops.

Q: Dijkstra with heapq pushes a new (distance, vertex) pair whenever it finds a shorter distance, and skips popped pairs whose distance is larger than the best known. Which technique is that, and how big can the heap get?
A: Lazy deletion, where a stale entry is recognised by comparing it with the current best distance instead of a dead set. One entry is pushed per successful relaxation, so the heap can hold O(E) entries, and the run costs O(E log E) = O(E log V).

## Lab

- **QHEAP1 (HackerRank).** Three query types: add a value, delete a value that is guaranteed to be present, print the minimum. Expected: the sample `1 4`, `1 9`, `3`, `2 4`, `3` prints 4 and then 9; O(log n) amortised per query.
- **480 Sliding Window Median (stretch).** The two heaps from the previous card plus one dead Counter shared by both: when the window slides, mark the leaving number dead, adjust the live sizes, rebalance, and clean both tops. Expected: `[1, 3, -1, -3, 5, 3, 6, 7]` with k = 3 gives `[1.0, -1.0, -1.0, 3.0, 5.0, 6.0]`; O(n log n).

> [!know]
> You now know how to delete and reprioritise inside a heap with lazy deletion, keep the garbage bounded, and build an indexed heap when you need true decrease-key.

=== primer | How do schedulers and timers use a heap, and when does a timing wheel win? | 15 min
goal: Simulate events in time order with a heap, combine a time-sorted input with a heap of ready jobs, and explain why event loops use heaps while Kafka and Linux use timing wheels for timeouts
tag: heap-sim | Event simulation with a heap
link: Confluent: Apache Kafka, Purgatory, and Hierarchical Timing Wheels | https://www.confluent.io/blog/apache-kafka-purgatory-hierarchical-timing-wheels/ | 15 min, the whole post: why the heap-based DelayQueue was replaced, how a hierarchical timing wheel gets O(1) insert and delete, and the benchmark
link: Python docs: asyncio, Scheduling delayed callbacks | https://docs.python.org/3/library/asyncio-eventloop.html#scheduling-delayed-callbacks | 3 min: call_later and call_at, the calls that push timer handles onto the event loop's heap
practice: 1834, 502

> [!key]
> A **discrete-event simulation** keeps future events in a min-heap keyed by time: pop the earliest, jump the clock to it, handle it, and push any events it causes. When jobs arrive over time and a worker picks the best job that has arrived, use two structures: the jobs sorted by arrival with a pointer, and a heap of the jobs already waiting; when nothing is waiting, jump the clock to the next arrival. Event loops (asyncio, libuv, Go's runtime) keep their timers in heaps; systems with huge numbers of timeouts that are usually cancelled (Kafka's purgatory, Linux's ordinary timers) use timing wheels, where insert and cancel are O(1).

## Intuition

A to-do list sorted by alarm time: you sleep until the next alarm, deal with it (which may set new alarms), and sleep again. You never tick through the empty minutes in between. Jumping straight to the next event is what makes simulations fast: the cost depends on the number of events, not on how much simulated time passes.

## How it works

### The event loop

State: the current time `now` and a heap of `(time, seq, callback)`. Loop: pop the earliest entry, set `now` to its time, run the callback, which may schedule more entries at `now + delay`. The sequence number breaks ties, so events at the same time run in the order they were scheduled and callbacks are never compared.

**Invariant:** every entry in the heap has a time >= now, so the clock never runs backwards, as long as callbacks schedule only into the present or the future.

### The ready queue: arrivals plus a choice

Many problems add a second ordering: items arrive over time, and whenever a resource is free it takes the best item that has arrived (the shortest job, the highest profit, the lowest server id).

1. Sort the items by arrival time and keep a pointer k into that order.
2. When the resource becomes free at time t, push every item with arrival <= t into a heap keyed by the choice rule.
3. If the heap is empty, jump t to the next arrival and go back to step 2. Otherwise pop the best item and run it: t += its duration.

The sorted pointer answers "has it arrived yet?" and the heap answers "which is best?". Each item is pushed and popped once.

A variant without a clock is **unlock, then choose**: with capital w you may start any project costing at most w, and finishing one raises w. Sort projects by cost, push the profit of every newly affordable project into a max-heap, take the best, repeat. Capital only grows, so a project that is affordable now stays affordable, and taking the most profitable one first never hurts.

### What real systems do

- **asyncio:** `loop.call_later(delay, callback)` creates a timer handle and pushes it onto the loop's `_scheduled` list with `heapq.heappush`; each pass of the loop pops the handles that are due. Cancelled handles stay in the heap until they surface or a rebuild removes them (the lazy-deletion card).
- **libuv**, the event loop under Node.js, keeps its timers in a min-heap. **Go's runtime** keeps a 4-ary min-heap of timers per processor: the tree is half as tall as a binary one, and a node's four children sit next to each other in memory.
- **Timing wheels** are an array of buckets, one per tick, like a clock face. A timer goes into the bucket of its expiry tick, so insert and cancel are O(1), and each tick expires one bucket. Hierarchical wheels (think seconds, minutes, hours) cover long delays by moving timers down a level as their time approaches. Kafka replaced its heap-based `DelayQueue` with hierarchical timing wheels: tens of thousands of requests can be waiting at once, each one inserts a timer that is usually cancelled when the request completes, and the heap paid O(log n) per insert while leaving completed requests behind until a purge. Linux keeps a timer wheel for ordinary timeouts, most of which are cancelled before they fire, and a red-black tree for high-resolution timers, which need exact ordering.

## Cost

- **Event loop:** one push and one pop per event, so E events cost O(E log E), whatever the span of simulated time.
- **Ready queue:** O(n log n) to sort plus O(n log n) for the heap operations.
- **d-ary heaps:** height log_d n, so sift-up crosses fewer levels (log_4 n is half of log_2 n), while sift-down compares d children per level (about d log_d n comparisons). With d = 4, the children of a node fit in one or two cache lines.

| Timer structure | insert | cancel | next expiry | Good for |
|---|---|---|---|---|
| binary heap | O(log n) | O(log n) indexed, or lazy | O(1) peek, O(log n) pop | event loops, simulations |
| 4-ary heap | O(log n), shallower | as above | O(1) peek, pop compares 4 children per level | the same, with fewer cache misses |
| timing wheel | O(1) | O(1) | O(1) per tick (plus moving timers between levels) | huge numbers of coarse timeouts |
| red-black tree | O(log n) | O(log n) | O(1) via a cached leftmost node | exact ordering with frequent cancels |

## When to use it

Cues: "simulate", "process in time order", "at each moment pick the best available", servers or CPUs that become free, tasks with arrival times, "whichever finishes first".

Not when every event is known up front and handling one never creates another: then sort once and sweep (the intervals module).

## Worked trace

Shortest job first on one worker. Jobs are (arrival, duration); note the idle jump at the end:

```steps
Jobs as (arrival, duration). One worker; when free it runs the shortest waiting job (the ready heap is shown sorted)
    jobs  0:(0, 8)  1:(1, 4)  2:(2, 9)  3:(3, 5)  4:(30, 2)
    t = 0   ready = []
---
t = 0: job 0 arrived and joined the heap. Pop (duration 8, job 0) and run it 0 to 8
    ready (duration, job) after pop: []
    clock now 8
---
t = 8: jobs 1, 2, 3 arrived and joined the heap. Pop (duration 4, job 1) and run it 8 to 12
    ready (duration, job) after pop: [(5, 3), (9, 2)]
    clock now 12
---
t = 12: Pop (duration 5, job 3) and run it 12 to 17
    ready (duration, job) after pop: [(9, 2)]
    clock now 17
---
t = 17: Pop (duration 9, job 2) and run it 17 to 26
    ready (duration, job) after pop: []
    clock now 26
---
Worker idle at t = 26: jump the clock to the next arrival, 30. t = 30: job 4 arrived and joined the heap. Pop (duration 2, job 4) and run it 30 to 32
    ready (duration, job) after pop: []
    clock now 32
```

## Template

```python
import heapq
import itertools


class EventLoop:
    """Discrete-event simulation: callbacks run in time order and may schedule more."""

    def __init__(self):
        self.now = 0
        self._q = []
        self._seq = itertools.count()         # tie-breaker: same time runs in schedule order

    def call_at(self, when, fn, *args):
        heapq.heappush(self._q, (when, next(self._seq), fn, args))

    def call_later(self, delay, fn, *args):
        self.call_at(self.now + delay, fn, *args)

    def run(self):
        while self._q:
            when, _, fn, args = heapq.heappop(self._q)
            self.now = when                   # jump straight to the next event
            fn(*args)


def shortest_job_first(jobs):
    """jobs[i] = (arrival, duration); one worker that, when free, starts the shortest waiting
    job (ties: lower index). Returns (index, start, finish) in run order. O(n log n)."""
    order = sorted(range(len(jobs)), key=lambda i: jobs[i][0])
    ready, out, t, k = [], [], 0, 0
    while k < len(order) or ready:
        if not ready and t < jobs[order[k]][0]:
            t = jobs[order[k]][0]             # idle: jump the clock to the next arrival
        while k < len(order) and jobs[order[k]][0] <= t:
            i = order[k]
            heapq.heappush(ready, (jobs[i][1], i))
            k += 1
        duration, i = heapq.heappop(ready)
        out.append((i, t, t + duration))
        t += duration
    return out
```

## Pitfalls

- **Ticking the clock one unit at a time.** That is O(time span) instead of O(events): fatal when times reach 10^9.
- **Forgetting the idle jump.** With nothing ready, popping crashes; only adding arrivals at the current time can wait forever.
- **Adding only one arrival per step.** After a jump, or after a long job, many items may have arrived; push all of them before choosing.
- **Ties.** Problems usually fix a tie-break (lower index first); encode it in the key, as in `(duration, index)`.
- **Overflow in other languages.** Summing 10^5 durations of up to 10^9 reaches 10^14: use 64-bit integers in C++ or Java.

## Check yourself

Q: In the trace, suppose job 3 had duration 4 instead of 5. Which job runs at t = 8, which at t = 12, and why?
A: At t = 8 the ready heap holds (4, 1), (9, 2) and (4, 3). Jobs 1 and 3 tie on duration, and the index breaks the tie, so job 1 runs from 8 to 12; job 3 runs next, from 12 to 16, then job 2.

Q: Why is a heap fine for an event loop's timers, while a message broker with tens of thousands of waiting requests, each with a timeout, moved to a timing wheel?
A: An event loop usually has at most thousands of timers, so O(log n) is a few dozen comparisons and the heap gives exact order for free. The broker inserts a timer for almost every request and cancels it when the request completes, so it pays O(log n) twice per request, at a high request rate, on a large heap; a wheel makes both O(1) in exchange for coarse tick resolution.

Q: k servers each handle one request at a time; requests arrive at known times with known durations and go to any free server, waiting if none is free. How do you compute each request's finish time?
A: Keep a min-heap of server free times, starting with k zeros. For each request in arrival order, pop the earliest free time f, start at max(arrival, f), push back start + duration, and record it. O(n log k). (If the rules say which free server to pick, by index or by weight, add a second heap of free servers.)

## Lab

- **1834 Single-Threaded CPU.** The ready-queue pattern with `(processing time, index)` keys. Expected: `[[1, 2], [2, 4], [3, 2], [4, 1]]` gives `[0, 2, 3, 1]`; `[[7, 10], [7, 12], [7, 5], [7, 4], [7, 2]]` gives `[4, 3, 2, 0, 1]`; O(n log n).
- **502 IPO (stretch).** Unlock, then choose: sort by required capital, push every affordable profit into a max-heap, take the best up to k times, and stop early if nothing is affordable. Expected: k = 2, w = 0, profits `[1, 2, 3]`, capital `[0, 1, 1]` gives 4; k = 3, w = 0, profits `[1, 2, 3]`, capital `[0, 1, 2]` gives 6; O(n log n).

> [!know]
> You now know how to drive a simulation from a heap of timed events, pair a sorted input with a heap of ready jobs, and choose between heaps and timing wheels for timers.

=== practice
- 1046 core
  cue: You must repeatedly take the two largest values from a collection that keeps changing.
  hint: Sorting after every round works but costs O(n log n) per round. Which structure hands you the largest item cheaply, again and again?
  insight: Store negated weights in a heapq min-heap so the heaviest stone sits at the root. Pop two, push back the negated difference if they differ, and stop when at most one stone is left. Each round is O(log n).
  cost: O(n log n) time, O(n) space
  pattern: heap-heapq
- 703 core
  cue: After every insertion into a stream, report the kth largest value seen so far.
  hint: Values below the kth largest can never matter again. How many values must you remember, and which one of them do you need instantly?
  insight: Keep a min-heap of the k largest values so far; its root is the kth largest. A new value larger than the root replaces it with heapreplace, and a smaller one is ignored, because k kept values already beat it.
  cost: O(log k) per add, O(k) space
  pattern: heap-topk
- hr:qheap1 core
  cue: A collection must support insert, delete of a given value, and report of the current minimum, in any order.
  hint: A heap gives the minimum cheaply but cannot delete from its middle. What if a deletion only took effect once the deleted value reached the top?
  insight: Keep a heap plus a record of deleted values. Deleting only records the value; before reporting the minimum, pop the root while it is recorded as deleted. Every value is pushed and popped once, so each query is O(log n) amortised.
  cost: O(log n) amortised per query, O(n) space
  pattern: heap-lazy
- 973 core
  cue: Return the k points nearest the origin from a long list of points.
  hint: Distances are only compared, never reported. Do you need the square root, and do you need to order all n points?
  insight: Compare squared distances x*x + y*y. Keep a max-heap of size k (push (-d, x, y) and pop when it grows past k), or call heapq.nsmallest(k, points, key=...): either way only k candidates are kept.
  cost: O(n log k) time, O(k) extra space
  pattern: heap-topk
- 215 core
  cue: The kth largest element of an unsorted array, asked once.
  hint: A full sort orders everything, but you need one position. What is the least you must keep to know the kth largest?
  insight: Scan with a size-k min-heap whose root is the kth largest so far (O(n log k)); or heapify the negated array and pop k times (O(n + k log n)); or quickselect with a random pivot (O(n) expected). None of them sorts everything.
  cost: O(n log k) with a heap, O(n) expected with quickselect
  pattern: heap-topk
- 373 core
  cue: The k pairs with the smallest sums taken from two sorted arrays, where there may be far more pairs than k.
  hint: Fix the index into the first array: the pairs it forms are already in increasing order of sum. How do you combine many sorted sequences without building them?
  insight: Treat each nums1[i] as a sorted list of pairs (i, 0), (i, 1), ... Seed a heap with (nums1[i] + nums2[0], i, 0) for the first k values of i; each time (i, j) pops, record it and push (i, j + 1). Every pop is the next smallest pair.
  cost: O(k log k) time, O(k) space
  pattern: heap-kmerge
- 1834 core
  cue: Tasks arrive over time, and one processor, whenever it is free, picks the shortest task that has arrived.
  hint: Two orders are involved: when tasks arrive and which arrived task is best. Can one sorted list and one heap cover both?
  insight: Sort task indices by enqueue time. Whenever the CPU is free, push every arrived task into a heap of (processing time, index), jumping the clock to the next enqueue time if the heap is empty; then pop the top and run it.
  cost: O(n log n) time, O(n) space
  pattern: heap-sim
- 1642 derive
  cue: Two kinds of resource, one plentiful but proportional to the need and one scarce that covers any need, spent along a path to get as far as possible.
  hint: You learn the needs one at a time, but you may revise earlier choices in hindsight. Which needs should the scarce resource have covered?
  insight: Push every climb into a min-heap; when it holds more climbs than there are ladders, pop the smallest and pay it with bricks. The heap always holds the largest climbs so far, the best use of ladders; stop at the first building where the bricks go negative.
  cost: O(n log L) time for L ladders, O(L) space
  pattern: heap-topk
- 295 core
  cue: Report the median after each number arrives in a stream.
  hint: The median depends only on the middle of the sorted order. What if you kept a lower half and an upper half, with only their inner edges at hand?
  insight: A max-heap for the lower half and a min-heap for the upper half, every lower value <= every upper value, the lower half equal in size or one larger. Insert through the lower heap, move its top across, rebalance sizes; the median is the lower top or the average of both tops.
  cost: O(log n) per add, O(1) per median, O(n) space
  pattern: heap-twoheaps
- 502 stretch
  cue: Choose at most k projects in sequence; each needs a minimum capital to start and adds its profit to your capital.
  hint: At any moment some projects are affordable and some are not, and finishing one can only unlock more. Which affordable project should you take now?
  insight: Sort projects by required capital. Each round, push the profits of all newly affordable projects into a max-heap and take the largest; capital only grows, so taking the most profitable affordable project never hurts. Stop after k rounds or when nothing is affordable.
  cost: O(n log n + k log n) time, O(n) space
  pattern: heap-sim
- 632 stretch
  cue: The smallest range that contains at least one number from each of k sorted lists.
  hint: Hold one candidate from each list at a time. Moving which candidate forward is the only move that can shrink the range?
  insight: Keep a heap of the current element of each list and the maximum of those elements; the range is [heap minimum, maximum]. Record it, pop the minimum and push its successor from the same list, updating the maximum; stop when that list is exhausted, because the minimum can no longer advance.
  cost: O(N log k) time for N numbers in total, O(k) space
  pattern: heap-kmerge
- 480 stretch
  cue: The median of every window of size k as the window slides along an array.
  hint: The running-median structure handles insertions. What do you do with the number leaving the window, which may be buried inside a heap?
  insight: Two heaps around the median plus lazy deletion: mark the outgoing number dead, adjust the live sizes and rebalance, and pop dead entries whenever they reach either top. Each number is pushed and popped a constant number of times.
  cost: O(n log n) time, O(n) space
  pattern: heap-lazy
