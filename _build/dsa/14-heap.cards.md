=== card | 1046
time: 20 min

## The problem

A collection of positive stone weights undergoes repeated collisions. Choose the two heaviest; if their weights match, both disappear, and otherwise only their positive difference remains. Return the final weight, or zero when no stone survives. For `[2, 7, 4, 1, 8, 1]`, repeated collisions leave weight 1.

## Constraints and what they imply

Weights are positive integers and duplicates represent distinct stones. At most one stone is returned by a collision, so the collection shrinks by at least one per round. Empty and single-element collections have immediate answers. Only the two current maxima matter; the rest need not be sorted.

## Brute force

Sort the remaining weights in every round, remove the final two and append their difference if nonzero. There are O(n) rounds and each sort costs O(n log n), giving O(n² log n) time and O(n) working space for a copy. Repeatedly ordering all the smaller stones is wasted effort.

## The insight

Use Python's min-heap on negated weights. The smallest negated value represents the largest original weight. After popping two values, insert the negative of their difference only when it is positive. Heap operations preserve access to the next maximum even after the set changes.

## Optimal solution, traced

```steps
Weights [2, 7, 4, 1, 8, 1]
    take 8 and 7; insert 1
---
Weights [4, 2, 1, 1, 1]
    take 4 and 2; insert 2
---
Take 2 and 1, then two 1s cancel
    survivor {{1}}
```

Each iteration performs exactly the specified collision because the heap supplies the two largest remaining stones. Replacing them by their difference preserves the actual collection, so induction gives the correct survivor when the loop ends.

## Code

```python
import heapq

def last_stone_weight(stones):
    heap = [-weight for weight in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        largest = -heapq.heappop(heap)
        second = -heapq.heappop(heap)
        if largest != second:
            heapq.heappush(heap, -(largest - second))
    return -heap[0] if heap else 0
```

## Complexity

Heap construction takes O(n); at most n-1 rounds use a constant number of O(log n) heap operations. Total time is O(n log n), with O(n) auxiliary space for the heap. The input is not modified.

## Mistakes and edge cases

- Negate again when reading a heap value; subtracting in the wrong order can create a negative weight.
- Equal maxima both disappear; never push a zero stone.
- All equal stones, a single stone, and an empty collection are handled.

## Variations

- Return the sequence of collisions as well as the final weight.
- If collisions instead choose the two lightest, store the positive weights directly.

=== card | 703
time: 20 min

## The problem

Maintain a sequence of numbers as new values arrive. After each insertion report the kth largest value counting duplicates separately. For k=2, starting from `[4, 2]`, adding 5 reports 4, and adding another 4 reports 4. The rank concerns all values seen so far, not distinct values.

## Constraints and what they imply

The rank k is positive and the caller asks for a result only when at least k numbers have been seen. Initial data may contain fewer than k values. Negative values and equal values are valid. Keeping the entire stream or repeatedly sorting it works, but the result needs only the largest k entries.

## Brute force

Append each new value and sort all values seen so far in descending order; return the entry at index k-1. With t values after an insertion this costs O(t log t) time for that query and O(t) storage. Repeated queries continually sort values that cannot affect the answer.

## The insight

Keep a min-heap containing the largest min(k, t) values encountered. Once it has k entries, its root is the smallest of the retained values, hence the kth largest overall. A new value below the root can be discarded because k values already dominate it; an equal value can also be discarded without changing the rank.

## Optimal solution, traced

```steps
k = 2, initial values [4, 2]
    retained heap values [2, 4], boundary 2
---
Add 5: replace the boundary 2
    retained [4, 5], answer {{4}}
---
Add 4: it does not exceed the boundary
    retained [4, 5], answer {{4}}
```

Inductively, inserting a value into a heap of fewer than k values retains everything. Otherwise either the new value cannot enter the largest k, or replacing the minimum removes exactly the one value that no longer belongs. Thus the root is the requested rank.

## Code

```python
import heapq

class KthLargest:
    def __init__(self, k, nums):
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k
        self.heap = []
        for value in nums:
            self._keep(value)

    def _keep(self, value):
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, value)
        elif value > self.heap[0]:
            heapq.heapreplace(self.heap, value)

    def add(self, value):
        self._keep(value)
        if len(self.heap) < self.k:
            raise ValueError("fewer than k values have been seen")
        return self.heap[0]
```

## Complexity

For n initial values, construction takes O(n log(k+1)) time. Each add takes O(log(k+1)) time in the worst case, and the heap uses O(k) space. A rejected add is O(1); the +1 makes the bound meaningful for k=1.

## Mistakes and edge cases

- Do not use a max-heap: its root would be the largest, not the kth largest.
- Equal numbers occupy separate ranks, even though an equal arrival need not replace the root.
- Calling `add` before k total values exist raises an error after retaining the new value.

## Variations

- Maintain the kth smallest value by reversing the comparison with a max-heap.
- Return the entire retained top-k collection, sorting it only when requested.

=== card | hr:qheap1
time: 30 min

## The problem

Support three operations on a collection of integers: insert a value, delete a specified present value, and report the current minimum. Process operations in order and return the answers to minimum queries. For insertions 5 and 2, deleting 5 leaves minimum 2. A deletion identifies a value, not its position in the heap.

## Constraints and what they imply

Delete requests refer to values currently present, and minimum requests occur only when the collection is nonempty. The original task uses distinct live values; the implementation also supports repeated values by deleting one occurrence at a time. Values can be negative. A heap locates its minimum quickly but gives no fast search for an arbitrary value.

## Brute force

Keep an unsorted list. Insertion appends in O(1), while deletion searches for an occurrence and minimum scans the entire list, both O(n). For Q operations this can be O(Q²) time and O(Q) space. Sorting the list instead moves the linear cost to insertions and deletions.

## The insight

Delete logically first and physically later. Keep a min-heap of inserted entries and a map from value to the number of entries awaiting removal. When a minimum is requested, remove marked roots until the root is live. Equal entries are interchangeable: removing any one physical copy satisfies one pending deletion of that value.

## Optimal solution, traced

```steps
Insert 5, 2, 7
    heap represents [2, 5, 7]
---
Delete 2 and 7 logically
    pending {2: 1, 7: 1}
---
Minimum removes stale root 2; root 5 is live
    answer {{5}}; stale 7 may remain buried
```

Every physical heap entry is either live or accounted for by a pending deletion of the same value. Purging a marked root removes one entry and one mark, preserving that correspondence. After purging, the root is live and no smaller live entry can be hidden below it, so it is the minimum.

## Code

```python
import heapq

def heap_queries(queries):
    heap = []
    deleted = {}
    answers = []
    for query in queries:
        kind = query[0]
        if kind == 1:
            heapq.heappush(heap, query[1])
        elif kind == 2:
            value = query[1]
            deleted[value] = deleted.get(value, 0) + 1
        elif kind == 3:
            while heap and deleted.get(heap[0], 0):
                value = heapq.heappop(heap)
                deleted[value] -= 1
                if deleted[value] == 0:
                    del deleted[value]
            if not heap:
                raise ValueError("minimum of an empty collection")
            answers.append(heap[0])
        else:
            raise ValueError("unknown query")
    return answers
```

## Complexity

Across Q operations, every inserted entry is pushed once and popped at most once. Total time is O(Q log(Q+1)), or O(log(Q+1)) amortised per operation; one minimum query may itself purge many entries. The heap, pending map and answers take O(Q) space. Buried stale entries mean space is not bounded by the current live size.

## Mistakes and edge cases

- A set of deleted values is insufficient when duplicate occurrences can be pending.
- Remove stale roots before reading the minimum, not only after a deletion.
- Reinsertions of a deleted value are safe because equal copies are interchangeable.
- Invalid deletion requests are outside this function's contract.

## Variations

- Return both the minimum and the number of live occurrences, using a separate live count.
- Use an indexed heap or balanced tree to support eager arbitrary deletion.
- Periodically rebuild from live counts if the application requires bounded stale storage.

=== card | 973
time: 25 min

## The problem

Given points with integer coordinates in the plane, return any k points closest to the origin. Distance ties may be returned in any order and k is between zero and the number of points. With `[[1, 1], [3, 0], [-1, 0]]` and k=2, the two selected points are `[-1, 0]` and `[1, 1]`.

## Constraints and what they imply

Points are separate input entries, even if coordinates repeat. The required result is a collection of k points, not necessarily sorted by distance. The squared distance `x*x + y*y` orders points exactly as Euclidean distance does and avoids square roots. The algorithm can discard points once k retained points are at least as close.

## Brute force

Sort a copy of all n points by squared distance and take its first k entries. This costs O(n log n) time and O(n) space for the copy. It works for ties but spends time ordering points that will never be returned.

## The insight

Maintain at most k candidates in a max-heap by distance, represented using negative squared distances. After adding each point, if there are k+1 candidates, remove the farthest. Store negated coordinates as deterministic tie breakers; their particular order is unimportant because either point at the same distance is acceptable.

## Optimal solution, traced

```steps
k = 2; process [1, 1] and [3, 0]
    retained squared distances [2, 9]
---
Process [-1, 0] with squared distance 1
    temporarily retain distances [2, 9, 1]
---
Remove the largest distance, 9
    retained distances {{[1, 2]}}
```

After each point, the heap contains min(k, processed) closest entries. If it overflows, discarding a farthest entry leaves a valid closest set, including when distances tie. The final set therefore satisfies the request.

## Code

```python
import heapq

def k_closest(points, k):
    if not 0 <= k <= len(points):
        raise ValueError("k must be between zero and the number of points")
    if k == 0:
        return []
    heap = []
    for x, y in points:
        distance = x * x + y * y
        heapq.heappush(heap, (-distance, -x, -y))
        if len(heap) > k:
            heapq.heappop(heap)
    return [[-x, -y] for _, x, y in heap]
```

## Complexity

The heap holds at most k+1 points, so processing n points costs O(n log(k+1)) time. Auxiliary heap space is O(k), and the returned list also occupies O(k) space. With k=0 the function returns immediately. The input is not changed.

## Mistakes and edge cases

- Negating only a coordinate does not reverse the distance priority; negate the squared distance itself.
- Equal distances do not require a particular output order, but duplicate input points must retain multiplicity.
- For k=n all points are valid; for k=0 return an empty list.

## Variations

- Select by squared distance from an arbitrary fixed centre.
- Use quickselect for expected linear time if modifying or copying the input is acceptable.
- Stream points and report the current closest k after each batch.

=== card | 215
time: 25 min

## The problem

Find the kth largest entry in an unsorted integer array. Rank counts duplicate entries, not distinct values: the second largest of `[3, 3, 1]` is 3. The answer is a value; the array does not need to be rearranged into complete order.

## Constraints and what they imply

The array is nonempty and `1 <= k <= n`. Values can be negative, repeated, or equal throughout. The rank can be at either extreme: k=1 asks for the maximum and k=n for the minimum. A fixed-size heap can keep just the k values that might determine the answer.

## Brute force

Sort a copy in descending order and return its entry at index k-1. This straightforward method takes O(n log n) time and O(n) auxiliary space for the copy. It orders all n entries even though the answer only depends on the boundary of the largest k.

## The insight

Maintain a min-heap of at most k values. Its root is the least of the currently retained values. Once k values are retained, any later value no larger than the root cannot improve the boundary; a larger value replaces that root. Duplicates remain distinct entries in the heap.

## Optimal solution, traced

```steps
Array [3, 1, 5, 3], k = 2
    after 3 and 1 retain [1, 3]
---
Read 5, replacing the root 1
    retain [3, 5]
---
Read 3; it does not exceed the boundary
    second largest is {{3}}
```

The retained entries are the k largest of the prefix after every step. The property is immediate before the heap fills; once full, replacing the smallest exactly when a larger value appears preserves it. At the end, the minimum retained value has exactly the desired rank, with ties counted.

## Code

```python
import heapq

def kth_largest(nums, k):
    if not 1 <= k <= len(nums):
        raise ValueError("invalid rank")
    heap = []
    for value in nums:
        if len(heap) < k:
            heapq.heappush(heap, value)
        elif value > heap[0]:
            heapq.heapreplace(heap, value)
    return heap[0]
```

## Complexity

There are n iterations and each insertion or replacement costs O(log(k+1)), giving O(n log(k+1)) time and O(k) auxiliary space. Discarding an entry costs O(1). Unlike randomized quickselect, this bound is deterministic and does not modify the input.

## Mistakes and edge cases

- The kth largest is not the kth distinct value; `[7, 7]` with k=2 returns 7.
- A min-heap of the largest k values, not a max-heap of those values, exposes the correct boundary.
- Check the rank before accessing the root; k=0 is invalid.

## Variations

- For one offline query, use quickselect for O(n) expected time.
- If k is close to n, maintain the n-k+1 smallest values in a max-heap.
- Return the k largest entries rather than just their boundary.

=== card | 373
time: 30 min

## The problem

Two integer arrays are sorted in nondecreasing order. Form pairs by taking one entry from each array and return up to k pairs with the smallest sums. Index pairs are distinct even when their values match. For `[1, 3]`, `[2, 4]`, and k=3, one valid result is `[[1, 2], [1, 4], [3, 2]]`; the latter two sums tie.

## Constraints and what they imply

Inputs may contain negative or duplicate numbers, k may be zero, and fewer than k pairs may exist. Sortedness makes each fixed-first-index row of pairs nondecreasing as the second index advances. The full Cartesian product can be much larger than the requested output.

## Brute force

Enumerate every index pair, sort the resulting m*n pairs by sum, and return the first k. This costs O(mn log(mn+1)) time and O(mn) space. The approach is simple but materializes many pairs irrelevant to a small output.

## The insight

Treat every first-array entry as the start of a sorted row. Seed the heap with the first pair from each of the first min(k, m) rows. Pop the smallest visible pair, then reveal the next pair from its row. Later rows need not be seeded: their first sums are no smaller than the first k row starts, so they cannot be needed before k already-available pairs; ties can be resolved arbitrarily.

## Optimal solution, traced

```steps
Arrays [1, 3], [2, 4], k = 3
    row heads (1, 2) sum 3 and (3, 2) sum 5
---
Pop (1, 2), then reveal (1, 4) sum 5
    next heads have equal sums
---
Pop both sum-5 pairs
    output {{[[1, 2], [1, 4], [3, 2]]}}
```

For every seeded row, its heap entry is its least unreported pair. Thus the smallest heap entry is the least unreported pair in those rows. The excluded-row argument above guarantees that some valid k smallest pairs lie among seeded rows; stopping earlier on exhaustion also handles a short product.

## Code

```python
import heapq

def k_smallest_pairs(nums1, nums2, k):
    if k <= 0 or not nums1 or not nums2:
        return []
    heap = [(nums1[i] + nums2[0], i, 0)
            for i in range(min(k, len(nums1)))]
    heapq.heapify(heap)
    result = []
    while heap and len(result) < k:
        _, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result
```

## Complexity

Let h=min(k,m), and r=min(k,mn). Heap initialization takes O(h); at most r pops and pushes take O(r log(h+1)), so total time is O(h+r log(h+1)). The heap uses O(h) auxiliary space and the output uses O(r). Empty inputs and nonpositive k return immediately.

## Mistakes and edge cases

- Heap entries need indices as well as sums, so the correct row successor can be generated.
- Do not deduplicate equal values: separate index pairs can have the same coordinates.
- Guard empty arrays before reading `nums2[0]`, and stop if the heap empties before k results.
- Inputs must be sorted; otherwise a row's unseen successor might be smaller than its head.

## Variations

- Return index pairs instead of values to make duplicate positions explicit.
- Merge several sorted sequences using the same one-head-per-sequence strategy.
- Find only the kth sum with a value-domain counting or binary-search approach.

=== card | 1834
time: 30 min

## The problem

A single processor receives tasks, each with a release time and a positive processing duration. Whenever the processor is free, it selects among all released unfinished tasks by shortest duration, breaking duration ties by original input index. A running task cannot be interrupted. Return the indices in execution order.

For `[[1, 2], [2, 4], [3, 2], [4, 1]]`, the order is `[0, 2, 3, 1]`: task 2 is available when task 0 finishes, while task 3 arrives during task 2.

## Constraints and what they imply

Times are nonnegative integers and durations are positive. Several tasks may arrive together; input order is not release-time order. The clock may need to jump over an idle interval. Selection depends on both arrival and priority, so sorting once by either field alone cannot simulate the schedule.

## Brute force

At every decision, scan every unfinished task to find the available task with the smallest `(duration, index)` pair. If none is available, scan for the next arrival and advance time. Up to n decisions each require O(n) work, for O(n²) time and O(n) space to track unfinished tasks and output.

## The insight

Sort task records by release time, keeping their original indices. A pointer moves through this arrival order only once. Before each choice, insert all tasks whose release is at most the current time into a heap ordered by duration and original index. If the heap is empty, advance time directly to the next release rather than ticking through idle time.

## Optimal solution, traced

```steps
At time 1, task 0 is available
    run 0 for 2 units; clock becomes 3
---
Tasks 1 and 2 have arrived
    choose 2, duration 2; clock becomes 5
---
Task 3 is now available and beats task 1
    order {{[0, 2, 3, 1]}}
```

The pointer inserts exactly the released tasks not previously inserted, while the heap retains exactly the released unfinished tasks. Its root therefore implements the required priority and tie break. Jumping only when the heap is empty cannot skip any executable task. Induction over completed tasks proves the order.

## Code

```python
import heapq

def cpu_order(tasks):
    arrivals = sorted((start, duration, i)
                      for i, (start, duration) in enumerate(tasks))
    heap = []
    order = []
    time = 0
    i = 0
    while i < len(arrivals) or heap:
        if not heap and i < len(arrivals):
            time = max(time, arrivals[i][0])
        while i < len(arrivals) and arrivals[i][0] <= time:
            _, duration, index = arrivals[i]
            heapq.heappush(heap, (duration, index))
            i += 1
        duration, index = heapq.heappop(heap)
        order.append(index)
        time += duration
    return order
```

## Complexity

Sorting n tasks costs O(n log n); each enters and leaves the heap once at O(log n) per operation. Total time is O(n log(n+1)), with O(n) auxiliary space for arrivals, heap and result. The size of an idle time gap does not affect the running time.

## Mistakes and edge cases

- Add all tasks released by the current time before selecting, including those released exactly at that time.
- Tie-break by the original index, not by release time or sorted position.
- Do not interrupt a task when a shorter one arrives during execution.
- Empty input returns an empty order; large gaps require a clock jump.

## Variations

- Record start and finish times in addition to the task order.
- Change the priority rule to earliest deadline while keeping the arrival pointer.
- Model preemption separately, because arrivals during execution then affect the running task.

=== card | 1642
time: 30 min

## The problem

You start at the first building in a line. To move to the next building, a positive height increase must be paid either with that many bricks or with one ladder; level and downward moves cost nothing. Return the greatest index reachable using the available bricks and ladders. For heights `[1, 5, 6, 10]`, 4 bricks and 1 ladder, index 2 is reachable but index 3 is not.

## Constraints and what they imply

The sequence is nonempty, and resource counts are nonnegative integers. Each ladder covers one entire positive climb regardless of size. Decisions need not be fixed as soon as a climb is encountered: for deciding reachability of a prefix, an earlier ladder can be reassigned to a later larger climb. Only positive differences need resources.

## Brute force

For each prefix, enumerate subsets of its positive climbs to cover by at most L ladders. Sum the remaining climb sizes and check against the brick budget. With c climbs this can take O(2^c c) time and O(c) working space for a subset, before even considering all prefixes. Repeatedly examining allocations causes the explosion.

## The insight

Among any set of climbs, use ladders on the largest L and bricks on the rest. If a ladder covers a smaller climb while bricks cover a larger one, swapping their assignments never increases brick usage. Maintain the ladder-covered climbs in a min-heap. When a new climb makes the heap exceed L, pay its smallest member with bricks.

## Optimal solution, traced

```steps
Heights [1, 5, 6, 10], bricks 4, ladders 1
    climb 4: tentatively assign the ladder
---
Climb 1: retain 4 for the ladder, pay 1 brick
    remaining bricks 3, reached index 2
---
Climb 4: retain one 4, pay the other 4
    bricks become -1, answer {{2}}
```

After each climb, the heap contains the largest L climbs seen and bricks have paid the rest. The exchange argument makes that brick cost minimal over every assignment of ladders. If even that minimum exceeds the budget, no allocation reaches the next building; since the path is sequential, no later building is reachable either.

## Code

```python
import heapq

def furthest_building(heights, bricks, ladders):
    heap = []
    for i in range(len(heights) - 1):
        climb = heights[i + 1] - heights[i]
        if climb <= 0:
            continue
        heapq.heappush(heap, climb)
        if len(heap) > ladders:
            bricks -= heapq.heappop(heap)
        if bricks < 0:
            return i
    return len(heights) - 1
```

## Complexity

At most n-1 climbs are processed. Each heap operation costs O(log(L+2)), because the heap briefly holds at most L+1 entries. Time is O(n log(L+2)) and auxiliary space is O(min(n,L+1)). The bound remains meaningful when L=0; the input is unchanged.

## Mistakes and edge cases

- When bricks first become negative, return the building before the failed climb, not the next one.
- Equal climbs are interchangeable; paying either yields the same budget.
- With no ladders every positive climb is paid immediately, and zero-cost moves still work with no bricks.
- Assigning ladders permanently to the earliest climbs can waste them on small increases.

## Variations

- Return an actual ladder/brick assignment for the reachable prefix.
- Find the minimum bricks required to reach a specified building with L ladders.
- Investigate a different model where each ladder has a maximum length; the exchange rule changes.

=== card | 295
time: 35 min

## The problem

Design a stream accumulator with an insertion operation and a median query. For an odd number of observations the median is the central value in sorted order; for an even number it is the average of the two central values. For example, after inserting 5, 1, and 3, the median is 3; after inserting another 3 it remains 3. Duplicate observations occupy separate positions.

## Constraints and what they imply

Values can be negative, positive, repeated, and arrive in arbitrary order. A query requires at least one observation. The stream can be much longer than the initial few entries, so sorting everything on every query repeats work. A median query only needs the one or two values bordering the middle, but insertion may put a new value anywhere in the sorted order.

The two middle values need not have appeared recently. Consequently a fixed-size top-k heap is insufficient: discarded values could later become central after enough additional insertions. We retain all observations but organise them around the boundary.

## Brute force

Append each observation to a list. For every query, sort a copy and read its central entry or entries. At stream length n, the query costs O(n log n) time and O(n) temporary space; insertion is O(1). Alternatively, inserting into a sorted list takes O(n) shifting time. Both approaches repeatedly move or reorder many values to expose the middle.

## The insight

Partition the observations into a lower half and an upper half. All lower values must be no greater than all upper values. Store the lower half as a max-heap using negation and the upper half as a normal min-heap. The lower heap has either the same size as the upper heap or exactly one extra value.

The largest lower value and smallest upper value are the two boundary values. Their ordering and the size rule identify the median directly. To insert without special cases, push into the lower heap, transfer its maximum to the upper heap, then transfer the upper minimum back if the lower heap became smaller. These moves repair both invariants, not just the sizes.

## Optimal solution, traced

```steps
Insert 5 and 1
    lower [1], upper [5]; median (1 + 5) / 2 = 3
---
Insert 3: push into lower, move its maximum to upper
    rebalance by moving upper minimum back
    lower [1, 3], upper [5]; median {{3}}
---
Insert another 3
    lower [1, 3], upper [3, 5]; median {{3}}
```

Before insertion, the partition is ordered. After adding to the lower heap, moving its largest value across ensures no remaining lower value exceeds that moved value or any old upper value. If a size repair is needed, moving the upper minimum back preserves the boundary ordering. The size difference is again zero or one, so the roots are exactly the middle one or two values. This inductive argument covers duplicate boundary values as well.

## Code

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.lower = []
        self.upper = []

    def add(self, value):
        heapq.heappush(self.lower, -value)
        heapq.heappush(self.upper, -heapq.heappop(self.lower))
        if len(self.lower) < len(self.upper):
            heapq.heappush(self.lower, -heapq.heappop(self.upper))

    def median(self):
        if not self.lower:
            raise ValueError("median of an empty stream")
        if len(self.lower) > len(self.upper):
            return self.lower[0] * -1
        return (-self.lower[0] + self.upper[0]) / 2
```

## Complexity

Each insertion performs a constant number of heap pushes and pops, taking O(log(n+1)) time at stream length n. A median query inspects at most two roots and costs O(1). Both heaps together store all n values, so auxiliary space is O(n). Python integer arithmetic does not overflow when summing the boundary values, although the division returns a floating-point result.

## Mistakes and edge cases

- Compare actual lower values, not the negated representation, when reasoning about order.
- A size balance alone is insufficient if a lower value exceeds an upper value.
- Do not discard duplicates: two equal central observations both contribute.
- The empty stream has no median and this interface raises `ValueError`.
- An even median can be fractional, including for negative numbers.

## Variations

- Expose the two central integers rather than averaging them, preserving exact arithmetic.
- Maintain a different quantile by adjusting the target size ratio between the heaps.
- Support sliding windows by adding deletion bookkeeping; a plain heap cannot remove an arbitrary old value efficiently.

=== card | 502
time: 40 min

## The problem

You have initial capital and a set of projects. Each project has a minimum capital requirement and a nonnegative profit. You may complete at most k distinct projects sequentially; a project is selectable only when your current capital meets its requirement, and completing it adds its profit to capital. Return the maximum capital achievable.

For initial capital 0, k=2, requirements `[0, 1, 1]` and profits `[1, 2, 3]`, doing the first project unlocks the other two. Choosing profit 3 next yields final capital 4.

## Constraints and what they imply

The profit and requirement arrays have the same length, capital and requirements are nonnegative, and profits are nonnegative. k can exceed the number of projects or be zero. Capital is a threshold for eligibility, not an amount consumed by starting a project. With nonnegative profits, available capital never falls, so previously affordable projects remain affordable until selected.

The goal is final capital, not the number of projects. Therefore stopping early is allowed when no project is available. Zero-profit projects do not unlock anything, although selecting one within the limit is harmless. Negative profits would invalidate the monotone-capital assumptions and require a different contract.

## Brute force

Enumerate every feasible ordered sequence of up to k different projects, updating capital after each selection and retaining the best result. There can be O(n^min(k,n)) partial sequences, and scanning n candidates at each node gives a loose O(n^(min(k,n)+1)) bound. A recursion and selected-project bookkeeping need O(n) space. The repeated exploration of equivalent capital choices is the bottleneck.

## The insight

At any choice, taking the highest-profit affordable project cannot make a later opportunity worse. Consider an optimal feasible sequence whose first project is different. If the greedy project occurs later, swap it to the front: its profit is at least the original first project's profit, so all intermediate requirements remain satisfied, and the total capital after both projects is unchanged. If it never occurs, replace the original first project by the greedy one; all later projects remain affordable and final capital cannot decrease.

Thus some optimal sequence begins with the greedy choice. Apply the same exchange at every subsequent step. To implement it, sort projects by requirement and sweep that list as capital grows. Put each newly affordable profit in a max-heap, using negation with Python's min-heap. Pop the largest profit at each of at most k selections.

## Optimal solution, traced

```steps
Capital 0, k = 2
    available profits [1]; requirements for the other projects are 1
---
Choose profit 1
    capital 1; newly available profits [2, 3]
---
Choose profit 3
    final capital {{4}}
```

The sorted pointer never skips an affordable project: before selecting, it advances through every requirement at most the current capital. Because capital is nondecreasing, all unselected entries already in the heap remain affordable. Therefore the heap root is precisely the greedy choice justified by the exchange argument. If the heap is empty, no project can be started and no future capital gain can unlock one.

## Code

```python
import heapq

def maximize_capital(k, capital, profits, requirements):
    projects = sorted(zip(requirements, profits))
    available = []
    i = 0
    for _ in range(k):
        while i < len(projects) and projects[i][0] <= capital:
            heapq.heappush(available, -projects[i][1])
            i += 1
        if not available:
            break
        capital -= heapq.heappop(available)
    return capital
```

## Complexity

Sorting n projects takes O(n log(n+1)) time. Each project enters the heap once and at most min(k,n) projects are popped, for O((n+min(k,n)) log(n+1)) further time. Total time is O(n log(n+1)); sorted records and the heap occupy O(n) space. No operation depends on the numeric magnitude of capital.

## Mistakes and edge cases

- Requirements are eligibility thresholds, not costs to subtract from capital.
- Insert all currently affordable projects before selecting the largest profit.
- Preserve the matching between each requirement and its profit when sorting.
- With no affordable project, stop; waiting alone cannot raise capital.
- k=0, an empty project set, repeated requirements and zero profits all have natural results.

## Variations

- Return the selected project indices along with the final capital.
- Introduce project prerequisites; the simple independent-project exchange no longer applies.
- Allow losses or capital consumption and reconsider both stopping and affordability arguments.

=== card | 632
time: 45 min

## The problem

Given several nonempty integer lists, each sorted in nondecreasing order, find an inclusive interval containing at least one entry from every list. Minimise its width, right endpoint minus left endpoint. If several intervals have the same width, choose the one with the smaller left endpoint. Return `[left, right]`.

For `[[1, 5], [2, 6], [3, 7]]`, interval `[1, 3]` covers all three lists and has width 2. Interval `[5, 7]` also has width 2 but loses the left-endpoint tie break.

## Constraints and what they imply

There is at least one list and every list has at least one value. Values may be negative, repeated within or across lists, and may match exactly. Since an optimal interval can be tightened until each endpoint is an input value, considering ranges between selected entries is sufficient. Sorting within each list allows a forward-only sweep; arbitrary unsorted lists would require preprocessing.

One selected value per list witnesses that a range is valid. Its smallest and largest witnesses are the tightest interval for that selection. The challenge is to change those witnesses without enumerating every possible combination.

## Brute force

Choose one value from every list, calculate the minimum and maximum of that combination, and compare its range with the best. If list lengths are `n1,...,nk`, this requires O(k times the product of those lengths) time and O(k) space for a combination. Even moderate numbers of lists make the product impractical. Enumerating all endpoint pairs and scanning the lists is another correct but repeated-work approach.

## The insight

Keep one current value from each list in a min-heap and track their maximum separately. The current minimum and maximum form a valid range. To potentially improve it, advance a list supplying the minimum: advancing a different list cannot raise the current minimum, and cannot lower the maximum, so it cannot make the range narrower at this step.

Every replacement in a sorted list is at least the value it replaces. The current maximum therefore never decreases, even when the removed minimum was also the maximum. Update it with the new value. When a minimum's list has no successor, stop: with all other pointers fixed, that list cannot supply a higher left boundary, so further advancing other lists cannot improve this range.

## Optimal solution, traced

```steps
Lists [1, 5], [2, 6], [3, 7]
    current values 1, 2, 3; best [1, 3]
---
Advance the list containing 1 to 5
    current values 5, 2, 3; range [2, 5]
---
Advance 2 to 6, then 3 to 7
    later best-width range [5, 7] loses the tie
    answer {{[1, 3]}}
```

For a completeness proof, fix any optimal interval `[L, R]`. Until every current value is at least L, only a current minimum below L is advanced. Each new value in its list is no greater than that list's first value inside `[L, R]`; the initial values also have that property. Such a list cannot exhaust before reaching L because it has a witness inside the interval. Thus the algorithm reaches a state where all selected values lie in `[L, R]`. Its range is no wider than optimal; optimality makes the widths equal, and the explicit tie comparison chooses the smallest left endpoint. The same argument applies when values or lists tie.

## Code

```python
import heapq

def smallest_range(lists):
    if not lists or any(not row for row in lists):
        raise ValueError("each of at least one list must be nonempty")
    heap = [(row[0], i, 0) for i, row in enumerate(lists)]
    heapq.heapify(heap)
    maximum = max(value for value, _, _ in heap)
    best_left, best_right = heap[0][0], maximum
    while True:
        minimum, i, j = heapq.heappop(heap)
        if (maximum - minimum, minimum) < (best_right - best_left, best_left):
            best_left, best_right = minimum, maximum
        if j + 1 == len(lists[i]):
            break
        value = lists[i][j + 1]
        maximum = max(maximum, value)
        heapq.heappush(heap, (value, i, j + 1))
    return [best_left, best_right]
```

## Complexity

Let k be the number of lists and N the total number of entries. Building the heap takes O(k); at most N heap removals and insertions each cost O(log(k+1)), so time is O(N log(k+1)). The heap holds one entry per list, for O(k) auxiliary space. The input lists are not changed.

## Mistakes and edge cases

- Compare width first and left endpoint second; comparing right endpoints alone gives the wrong tie rule.
- Stop after evaluating the current range when a list is exhausted, not before.
- A common value in every list produces a zero-width range; one list produces `[x, x]` for its smallest value.
- Do not assume values are distinct; heap entries include list and position to identify the successor.

## Variations

- Return one witness position from each list for the chosen interval.
- Merge all values with list labels and use a covering sliding window instead.
- Require multiple entries from each list, maintaining per-list counts in a window.

=== card | 480
time: 50 min

## The problem

For an integer array and a window size k, report the median of every consecutive window of exactly k entries, from left to right. The median of an odd-size window is its middle sorted value; for an even-size window it is the average of its two middle values. Duplicates count separately.

For `[1, 3, -1, -3, 5]` and k=3, the windows have medians `[1, -1, -1]`. An outgoing value may be buried inside a heap rather than at its root, which makes the streaming-median method alone insufficient.

## Constraints and what they imply

The array is nonempty and `1 <= k <= len(nums)`. Values can be negative, equal, or repeated at the boundary between the two halves. There are exactly n-k+1 output medians. A single-element window returns its sole value; the window equal to the full input produces one result.

The algorithm must distinguish physical heap length from the number of live window entries. Deleting a buried item eagerly would require locating it, which a standard Python heap does not support efficiently. A delayed deletion map can keep such an item until it reaches a root.

## Brute force

For each window, copy its k entries, sort them, and read the central one or two. This costs O((n-k+1) k log(k+1)) time and O(k) temporary space, excluding the O(n-k+1) output. Consecutive windows differ by only two entries, but sorting starts over every time.

## The insight

Keep a max-heap for the lower half and a min-heap for the upper half, with every live lower value no greater than every live upper value. The lower half has the same number of live entries as the upper half or one extra. The two live roots therefore determine the median.

On departure, increment a delayed-deletion count for the value and decrement the live size of the half it belongs to. Compare it to the current lower maximum to choose a half. If the value equals the boundary, any equal occurrence is interchangeable; assigning that deletion to the lower half is valid. Purge marked entries whenever they reach a root, and rebalance by moving a live root between heaps. An incoming value is inserted into the appropriate half and the sizes are rebalanced again.

The maps count occurrences rather than merely recording values, so repeated departures are not collapsed. Each live-size adjustment happens at logical deletion, not when the stale entry is finally popped. Pruning changes physical storage but must not decrement live size again.

## Optimal solution, traced

```steps
Window [1, 3, -1], k = 3
    lower live values [-1, 1], upper [3]; median 1
---
Remove 1, add -3
    lower [-3, -1], upper [3]; median {{-1}}
---
Remove 3, add 5
    lower [-3, -1], upper [5]; median {{-1}}
```

Insertion places the value on the correct side of the current boundary, so ordering survives. Deletion removes one logical occurrence from a valid side; pruning only disposes of already-deleted physical copies. Rebalancing moves the largest live lower value or smallest live upper value across, preserving ordering and restoring the size rule. By induction the roots are the sorted window's middle values, even when identical values straddle the boundary.

Each entry is pushed once, transferred only a constant number of times per window change, and eventually either popped as stale or remains stored. A single operation may prune many stale entries, so its worst-case cost is not necessarily logarithmic even though total work is bounded.

## Code

```python
import heapq

def median_sliding_window(nums, k):
    if not 1 <= k <= len(nums):
        raise ValueError("invalid window size")
    lower, upper = [], []
    delayed = {}
    lower_size = upper_size = 0

    def prune(heap, sign):
        while heap:
            value = sign * heap[0]
            if not delayed.get(value, 0):
                break
            heapq.heappop(heap)
            delayed[value] -= 1
            if delayed[value] == 0:
                del delayed[value]

    def balance():
        nonlocal lower_size, upper_size
        if lower_size > upper_size + 1:
            heapq.heappush(upper, -heapq.heappop(lower))
            lower_size -= 1
            upper_size += 1
            prune(lower, -1)
        elif lower_size < upper_size:
            heapq.heappush(lower, -heapq.heappop(upper))
            upper_size -= 1
            lower_size += 1
            prune(upper, 1)

    def add(value):
        nonlocal lower_size, upper_size
        if not lower or value <= -lower[0]:
            heapq.heappush(lower, -value)
            lower_size += 1
        else:
            heapq.heappush(upper, value)
            upper_size += 1
        balance()

    def remove(value):
        nonlocal lower_size, upper_size
        delayed[value] = delayed.get(value, 0) + 1
        if value <= -lower[0]:
            lower_size -= 1
            if value == -lower[0]:
                prune(lower, -1)
        else:
            upper_size -= 1
            if upper and value == upper[0]:
                prune(upper, 1)
        balance()

    for value in nums[:k]:
        add(value)
    result = []
    for i in range(k, len(nums) + 1):
        if k % 2:
            result.append(-lower[0])
        else:
            result.append((-lower[0] + upper[0]) / 2)
        if i < len(nums):
            remove(nums[i - k])
            add(nums[i])
    return result
```

## Complexity

Across n insertions and n-k removals, each entry has only O(1) heap transfers attributable to each size change, and each physical entry is eventually pruned at most once. Heap operations can involve O(n) physical entries, so total time is O(n log(n+1)); median lookup is O(1) after maintenance. Auxiliary space is O(n) for heaps and pending counts, plus O(n-k+1) output. It is not necessarily O(k): monotone inputs can leave stale values buried for many windows.

## Mistakes and edge cases

- Rebalance using live sizes, not `len(heap)`, which includes stale entries.
- Purge a stale root before inspecting or transferring it; do not subtract its live size twice.
- Equal values may appear in both halves: a count map and interchangeable occurrences handle them.
- k=1, k=n, all-equal inputs, and fractional even medians need explicit checks.
- Do not claim every individual update is O(log k): lazy cleanup can remove many entries and physical heaps can grow to O(n).

## Variations

- Use an indexed heap or balanced multiset to erase entries eagerly and maintain O(k) active storage.
- Return the two middle integers to avoid floating-point rounding in an exact-median application.
- Generalise the live-size target to a sliding percentile rather than the median.
