---
key: projectorder
name: Build a room allocation planner
stage: order
summary: Schedule half-open meetings using sorting and a min-heap.
why: Resource allocation is a concrete way to connect ordering, interval boundaries and priority queues.
outcomes:
- Reuse the earliest available resource with a heap.
- Verify the resource count against peak overlap.
cues:
- Intervals must be assigned to reusable identical resources.
- The next resource to become free matters.
traps:
- Touching half-open intervals are treated as overlapping.
- Equal starts cause nondeterministic assignments.
---

=== build | Meeting room allocator | 6-8 h
goal: Assign meetings to the minimum number of rooms and verify the allocation.
link: Interval techniques | https://www.techinterviewhandbook.org/algorithms/interval/#techniques | Revisit sorting and interval boundaries.
link: Heap priority queue notes | https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes | Use a stable tie breaker in heap entries.

## The brief
Given a day's meeting requests, output a deterministic room assignment and the minimum number of rooms required. This is an offline planner; real-time rescheduling and attendee constraints are out of scope.

## Spec
Each meeting has a unique string ID and integer `start < end`, interpreted as `[start, end)`. Reject invalid intervals or duplicate IDs. Sort by `(start, end, id)`. Maintain a min-heap of `(end, room_id)` for occupied rooms and a min-heap of free room IDs. Before assigning a meeting, release every room whose end is at most its start; reuse the lowest free ID, otherwise allocate the next positive ID. Return assignments in original input order.

Independently calculate peak overlap using sorted endpoints with ends processed before starts at equal times. Explain why the number of allocated rooms equals that peak and why assignments cannot overlap within a room.

## Milestones
1. **1-2 h:** Specify boundary rules and write the peak-overlap oracle.
2. **1-2 h:** Implement sorted scheduling and both heaps.
3. **1-2 h:** Test assignment validity, deterministic tie handling and random cases.
4. **1-2 h:** Benchmark and explain sorting, heap costs and memory.

## Done when
- For `A=[0,10)`, `B=[5,7)`, `C=[7,10)` in that order, assignments are `A:1, B:2, C:2`, and peak is 2.
- Empty input uses zero rooms; touching intervals share a room; duplicate IDs and zero-length intervals are rejected.
- On 200 seeded small cases, every meeting is assigned exactly once, same-room intervals do not overlap and room count equals the endpoint-sweep peak.
- Benchmark 1,000, 10,000 and 100,000 seeded intervals with both mostly disjoint and fully overlapping patterns; report median end-to-end times across five runs, room count and peak heap sizes.
- Give `O(n log n)` time and `O(n)` auxiliary space, including sorting and output, and distinguish the number of concurrent rooms from total meetings.

## Stretch goals
- Emit a per-room schedule sorted by start and test that it preserves the assignment.
- Compare heap allocation with a simple scan of all room end times on small cases.

## Hints
- [Interval techniques](https://www.techinterviewhandbook.org/algorithms/interval/#techniques) motivate sorting before assigning rooms.
- See [heap priority queue notes](https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes) for tie-breaking with comparable keys.
