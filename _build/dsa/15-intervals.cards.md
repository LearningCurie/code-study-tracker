=== card | 2848
time: 20 min

## The problem

Each car covers a closed interval of integer positions on a number line. Count the distinct integer positions covered by at least one car. For intervals `[1, 3]` and `[3, 5]`, the covered positions are 1 through 5, so the answer is 5 rather than 6.

## Constraints and what they imply

Endpoints are integers and are included. Intervals may overlap or repeat. Adding their individual lengths double-counts positions in an overlap; any solution must count each position only once.

## Brute force

Insert every integer position in every interval into a set and return the set size. If the total lengths sum to `L`, this takes O(L) expected time and up to O(L) space. It is suitable for the task's short coordinate range, but becomes expensive if intervals cover a very long line.

## The insight

Sort the intervals by start and combine overlapping or adjacent ranges into disjoint blocks. Count each block's integer points once using `end - start + 1`. Adjacent integer ranges may be merged because there is no uncovered integer between them.

## Optimal solution, traced

```steps
Sort [1, 3], [3, 5]
    current block [1, 3]
---
The second interval overlaps
    extend the block to [1, 5]
---
Count inclusive positions
    5 - 1 + 1 = {{5}}
```

After sorting, any next interval that does not reach the current block starts a new disjoint block. The length sum of disjoint blocks counts exactly the covered positions.

## Code

```python
def covered_points(intervals):
    if not intervals:
        return 0
    ordered = sorted(intervals)
    start, end = ordered[0]
    total = 0
    for left, right in ordered[1:]:
        if left <= end + 1:
            end = max(end, right)
        else:
            total += end - start + 1
            start, end = left, right
    return total + end - start + 1
```

## Complexity

Sorting takes O(n log n) time and O(n) space for the sorted copy. The scan is O(n). For the original bounded coordinates, marking points is an alternative with O(L) time and bounded coordinate space.

## Mistakes and edge cases

- Both endpoints count, hence the `+ 1`.
- Repeated intervals must not be counted repeatedly.
- An empty list covers zero points.

## Variations

- Return the merged blocks rather than their total length.
- For continuous intervals, measure total length instead of counting integer points.
- Maintain a difference array when the coordinate domain is small.

=== card | 1854
time: 20 min

## The problem

Each record contains a birth year and a death year. A person counts as alive in their birth year but not in their death year. Return the earliest year with the largest population.

For records `(1990, 1993)` and `(1992, 1994)`, both people count in 1992, so the answer is 1992. The first person no longer counts in 1993.

## Constraints and what they imply

The original task restricts births and deaths to years from 1950 through 2050, with birth strictly before death. Each life is therefore a half-open interval `[birth, death)`. There is at least one record, and ties must choose the earliest year.

## Brute force

For every candidate year, examine every person and count those satisfying `birth <= year < death`. This costs O(nR) time for `n` records and `R` candidate years. The repeated checking of the same life across years is the bottleneck.

## The insight

Only births and deaths change the population. Record `+1` at each birth and `-1` at each death in a difference array. Scan the years in order, accumulating the changes. Update the best year only when the count is strictly greater than the previous maximum, preserving the earliest tie.

## Optimal solution, traced

```steps
Changes: +1 in 1990, +1 in 1992, -1 in 1993, -1 in 1994
    population in 1990 = 1
---
At 1992, apply the second birth
    population {{2}}; best year {{1992}}
---
At 1993, apply the first death
    population 1; best remains 1992
```

The running sum includes exactly the people whose birth change has occurred but whose death change has not.

## Code

```python
def maximum_population_year(logs):
    changes = [0] * 101
    for birth, death in logs:
        changes[birth - 1950] += 1
        changes[death - 1950] -= 1
    population = 0
    best = -1
    year = 1950
    for offset in range(100):
        population += changes[offset]
        if population > best:
            best = population
            year = 1950 + offset
    return year
```

## Complexity

Recording changes takes O(n); scanning the fixed `R = 100` candidate years takes O(R). Auxiliary space is O(R), constant for the task's fixed year range.

## Mistakes and edge cases

- Subtract at the death year, not the following year.
- Use a strict improvement to preserve the earliest year in a tie.
- Include a slot for changes at 2050 even though no person counts in their death year.

## Variations

- With a large sparse year range, sort change events rather than allocating every year.
- Return the maximum count as well as the earliest year.
- Change the model to inclusive death years and adjust the subtraction.

=== card | 56
time: 30 min

## The problem

Combine overlapping closed intervals into disjoint intervals covering exactly the same points. For `[[1, 3], [2, 6], [8, 10]]`, return `[[1, 6], [8, 10]]`. Intervals sharing an endpoint overlap and should be combined.

## Constraints and what they imply

Each interval has a start no greater than its end. Intervals may arrive in any order and may contain one another. The result should not depend on the input order. Since the ranges are closed, `[1, 2]` and `[2, 4]` meet at 2 and belong in one result interval.

## Brute force

Repeatedly find any pair of overlapping intervals, replace them with their union, and start again until no pair overlaps. A straightforward implementation can perform O(n²) pair comparisons repeatedly, reaching O(n³) time in the worst case. The bottleneck is repeatedly searching among intervals that have already been examined.

## The insight

Sort by start. Once earlier intervals have been merged, the next interval can overlap only the most recent merged block: all earlier blocks end before that block starts. If the next start is at most the last end, extend that end to the larger endpoint. Otherwise append a new block.

## Optimal solution, traced

```steps
Sorted input: [1, 3], [2, 6], [8, 10]
    start with [1, 3]
---
[2, 6] overlaps the last block
    extend it to {{[1, 6]}}
---
[8, 10] starts after 6
    result {{[[1, 6], [8, 10]]}}
```

The output blocks are sorted and disjoint after every step. When a new interval overlaps the last block, the updated block is their exact union. Otherwise, sorting ensures it cannot overlap any earlier block, so starting a new block is safe.

For a nested example, after `[1, 10]` and `[2, 3]`, the current end remains 10: shortening it to 3 would lose covered points. A later `[9, 12]` then extends that same block to `[1, 12]`. The sorted scan handles a chain of overlaps even if the first and last intervals do not directly overlap.

## Code

```python
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
```

## Complexity

Sorting the `n` intervals takes O(n log n) time, and the scan takes O(n). The sorted copy and returned blocks use O(n) space. The input is not modified.

## Mistakes and edge cases

- Do not replace the current end with a smaller end when one interval contains another.
- Use `<=` for closed intervals that touch at an endpoint.
- An empty input produces an empty result.

## Variations

- Insert one interval into an already sorted, disjoint list in linear time.
- Count the covered integer points after merging.
- Change to half-open intervals and define whether touching intervals should be combined.

=== card | 986
time: 25 min

## The problem

Two lists contain closed intervals. Each list is sorted by start and its own intervals are pairwise disjoint. Return all intersections between one interval from the first list and one from the second.

For `[[1, 4], [7, 9]]` and `[[2, 5], [8, 10]]`, the intersections are `[[2, 4], [8, 9]]`. A shared endpoint is an intersection of length zero, such as `[4, 4]`.

## Constraints and what they imply

Both endpoints count. The inputs are already sorted and internally disjoint, so a pointer can move forward without revisiting earlier intervals. If either list is empty, the result is empty. The output itself may contain multiple intervals and must be included when discussing memory use.

## Brute force

Compare every interval in the first list with every interval in the second. For `m` and `n` intervals, that is O(mn) comparisons. Compute the overlap of each pair and keep the nonempty ones. The bottleneck is checking pairs that cannot overlap because they are far apart in the sorted order.

## The insight

Compare the intervals currently at the two pointers. Their overlap is `[max(starts), min(ends)]` when the first endpoint is at most the second. Afterwards advance the interval that ends earlier. It cannot overlap any later interval in the other list, because those later intervals begin after the other current interval ends.

If both end at the same point, advancing either pointer is safe. The remaining interval cannot have another overlap with it beyond that point because intervals within a list are disjoint.

## Optimal solution, traced

```steps
Compare [1, 4] and [2, 5]
    overlap {{[2, 4]}}; first interval ends earlier
---
Compare [7, 9] and [2, 5]
    no overlap; advance the second pointer
---
Compare [7, 9] and [8, 10]
    overlap {{[8, 9]}}
```

The pointer that advances has already been compared with the only current interval it might overlap; the ordering rules out all later intervals in the other list. Thus advancing it cannot discard a missing answer. Both pointers move only forward.

## Code

```python
def interval_intersections(first, second):
    i = j = 0
    result = []
    while i < len(first) and j < len(second):
        left = max(first[i][0], second[j][0])
        right = min(first[i][1], second[j][1])
        if left <= right:
            result.append([left, right])
        if first[i][1] < second[j][1]:
            i += 1
        else:
            j += 1
    return result
```

## Complexity

Each iteration advances at least one pointer, so time is O(m + n). The pointers use O(1) auxiliary space, excluding the O(r) returned intersections.

## Mistakes and edge cases

- Use `<=` when checking whether a closed intersection exists.
- Advance by ending coordinate, not by starting coordinate.
- The linear proof relies on each input list being sorted and internally disjoint.

## Variations

- Find intersections of several sorted interval lists.
- Use half-open ranges, where an equal start and end is empty.
- Count overlapping pairs without storing the intersections.

=== card | 57
time: 30 min

## The problem

Insert one closed interval into a sorted list of pairwise disjoint closed intervals, merging all overlaps. Return the resulting sorted list.

For `[[1, 2], [6, 9]]` and new interval `[2, 7]`, the new interval touches the first and overlaps the second, so the result is `[[1, 9]]`.

## Constraints and what they imply

The existing intervals are already sorted and non-overlapping. Their endpoints are inclusive, so equality at a boundary counts as overlap. A newly inserted interval can expand while it absorbs intervals, and that expansion can make it overlap later intervals that did not overlap its original endpoint.

## Brute force

Append the new interval to a copy of the input, sort the combined list, and run a general interval merge. This takes O(n log n) time and O(n) output space. The sorting is unnecessary because the original intervals are already ordered.

## The insight

Process three consecutive regions. First copy intervals ending strictly before the new start. Next absorb every interval starting at or before the current new end, updating both endpoints as the block grows. Finally append the merged block and copy all remaining intervals, which start strictly after it.

## Optimal solution, traced

```steps
Existing [1, 2], [6, 9]; new [2, 7]
    no existing interval ends strictly before 2
---
[1, 2] overlaps the new block
    block becomes [1, 7]
---
[6, 9] also overlaps
    block becomes {{[1, 9]}}
---
No intervals remain
    result {{[[1, 9]]}}
```

The first region cannot overlap the new block because its intervals end before the block starts. During the second region, the block is exactly the union of the new interval and all absorbed intervals. Once the next interval starts after the block's end, sorted starts ensure all later intervals do too.

The method returns fresh interval lists rather than changing the supplied `new_interval` or the nested lists in the input. This makes the no-mutation behaviour explicit to callers. The input order is preserved for unaffected intervals.

## Code

```python
def insert_interval(intervals, new_interval):
    start, end = new_interval
    result = []
    i = 0
    while i < len(intervals) and intervals[i][1] < start:
        result.append(list(intervals[i]))
        i += 1
    while i < len(intervals) and intervals[i][0] <= end:
        start = min(start, intervals[i][0])
        end = max(end, intervals[i][1])
        i += 1
    result.append([start, end])
    while i < len(intervals):
        result.append(list(intervals[i]))
        i += 1
    return result
```

## Complexity

Every input interval is processed once: O(n) time. The returned list uses O(n) space; excluding that output, only indices and two endpoints are stored.

## Mistakes and edge cases

- Test against the evolving end, not just the original new end.
- Equality at an endpoint is an overlap for closed intervals.
- Handle an empty input or a new interval wholly before or after the existing list.

## Variations

- Insert several intervals, then compare repeated insertion with one batch sort and merge.
- Return only the merged interval and the indices of affected original intervals.
- Adapt the boundary tests for half-open intervals.

=== card | 729
time: 30 min

## The problem

Maintain a calendar of accepted bookings. A new booking occupies a half-open interval `[start, end)` and is accepted only if it does not overlap any existing booking. Return whether each booking was accepted.

If `[10, 20)` is accepted, `[20, 25)` can also be accepted because the first booking has ended at 20. A later `[15, 22)` must be rejected.

## Constraints and what they imply

Every booking has `start < end`. Accepted bookings are pairwise disjoint. Half-open intervals overlap only when each starts before the other ends. This differs from closed intervals: equality at a boundary is allowed.

## Brute force

Store accepted bookings in a list. For each new booking, compare it with every accepted booking using `start < old_end and old_start < end`; append only if none overlaps. With `n` accepted bookings, each request costs O(n), for O(n²) total time over many accepted requests. The repeated scan is the bottleneck.

## The insight

Keep accepted bookings sorted by start. Binary search locates where a new start would be inserted. Because existing intervals are disjoint, only the immediate predecessor and successor can overlap the proposed booking. If the predecessor ends after the proposed start, or the successor starts before the proposed end, reject it. Otherwise insert it at that position.

In Python, binary search is O(log n), but inserting into ordinary lists shifts later elements and still costs O(n). A balanced ordered structure can improve insertion cost; the standard list implementation below is simple and correct without an extra dependency.

## Optimal solution, traced

```steps
Existing booking [10, 20)
    request [20, 25): predecessor ends at the new start
---
Boundary touching is allowed
    accept; bookings are [10, 20), [20, 25)
---
Request [15, 22)
    predecessor [10, 20) ends after 15; {{reject}}
```

All intervals before the predecessor end no later than it, and all intervals after the successor start no earlier than it. Therefore, if neither neighbour overlaps, no other accepted booking can overlap the proposed one.

## Code

```python
from bisect import bisect_left


class MyCalendar:
    def __init__(self):
        self.starts = []
        self.ends = []

    def book(self, start, end):
        if start >= end:
            raise ValueError("a booking must have positive duration")
        i = bisect_left(self.starts, start)
        if i > 0 and self.ends[i - 1] > start:
            return False
        if i < len(self.starts) and self.starts[i] < end:
            return False
        self.starts.insert(i, start)
        self.ends.insert(i, end)
        return True
```

## Complexity

Binary search costs O(log n). On acceptance, inserting into Python's lists can shift O(n) items, so a request is O(n) worst case and O(n) space is retained for the bookings. Rejections after the search take O(log n).

## Mistakes and edge cases

- Treat endpoints as half-open: ending at the next start is not an overlap.
- Check both neighbours before modifying either list.
- Keep the start and end lists aligned after insertion.

## Variations

- Return the conflicting booking when rejecting a request.
- Use a balanced ordered map for logarithmic insertion.
- Permit up to two simultaneous bookings and track double-booked intervals separately.

=== card | 2406
time: 30 min

## The problem

Split closed intervals into the fewest groups so that no two intervals in the same group intersect. Return the number of groups. Intervals that share an endpoint intersect.

For `[1, 3]`, `[2, 4]` and `[3, 5]`, all three contain the point 3, so at least three groups are needed; three groups suffice.

## Constraints and what they imply

Intervals are closed, so a group whose last interval ends at the next start cannot be reused for that next interval. Input order is arbitrary. The maximum number of intervals covering a single point is a lower bound: each of those simultaneous intervals needs a separate group.

## Brute force

Try assigning every interval to each existing group or to a new group, rejecting assignments that place overlapping intervals together. Keep the smallest number of groups over all valid assignments. The number of assignments grows exponentially, so exploring many possible groupings is the bottleneck.

## The insight

Sort intervals by start and track the ending point of the most recently assigned interval in each group in a min-heap. For the next interval, if the earliest-ending group ends strictly before its start, reuse that group. Otherwise every group still overlaps the new interval's start, so open a new group.

The heap contains one ending point per group. It is not necessary to remove every already-finished group: only one group is needed for the current interval, and the others remain available for later intervals.

## Optimal solution, traced

```steps
Sort [1, 3], [2, 4], [3, 5]
    add [1, 3]; group ends [3]
---
For [2, 4], the earliest end 3 is not before 2
    open a group; ends [3, 4]
---
For [3, 5], end 3 is not strictly before 3
    open a group; {{3 groups}}
```

When a group is opened, every existing group's most recent interval covers the new start, so no assignment can use fewer groups at that point. Reusing an available group never creates an overlap. Thus the algorithm meets the lower bound while maintaining a valid assignment.

## Code

```python
from heapq import heappush, heapreplace


def minimum_interval_groups(intervals):
    ends = []
    for start, end in sorted(intervals):
        if ends and ends[0] < start:
            heapreplace(ends, end)
        else:
            heappush(ends, end)
    return len(ends)
```

## Complexity

Sorting takes O(n log n), and each of `n` heap operations takes O(log n), giving O(n log n) time. The sorted copy and heap require O(n) space.

## Mistakes and edge cases

- Use `< start`, not `<= start`, because intervals are closed.
- The heap stores the last end for each group, not every interval ever assigned.
- An empty list requires zero groups.

## Variations

- Produce a group number for each interval rather than only the count.
- Find the maximum concurrency with a sweep of start and end events.
- Change to half-open intervals and update the reuse condition.

=== card | 452
time: 30 min

## The problem

Each closed interval represents a balloon's horizontal extent. An arrow fired at a coordinate bursts every balloon containing that coordinate. Find the fewest arrows needed to burst all balloons.

For `[1, 4]`, `[3, 6]`, and `[7, 8]`, one arrow at 4 bursts the first two and one at 8 bursts the last, so the answer is 2.

## Constraints and what they imply

Endpoints are inclusive, so an arrow at an interval's end bursts that balloon. Intervals may be nested or overlap in chains. The coordinate range can be large, so iterating over every possible coordinate is not needed.

## Brute force

Try subsets of candidate coordinates, checking whether every interval contains at least one selected coordinate. It is enough to consider interval endpoints, but there can still be exponentially many subsets. Searching this combinatorial set is the bottleneck.

## The insight

Sort balloons by right endpoint. Fire an arrow at the end of the first balloon not already burst. This arrow hits that balloon and every later balloon that has started by that coordinate. Fire another only when a later balloon starts strictly after the last arrow.

The choice is safe by an exchange argument: any solution must use an arrow within the earliest-ending balloon. Moving such an arrow right to that balloon's end cannot lose a later-ending balloon that the old arrow hit, because that later balloon starts no later than the old arrow and ends no earlier than the chosen endpoint.

After placing this arrow, remove the balloons it hits conceptually and repeat the same argument for the earliest-ending remaining balloon. The implementation achieves this without physically removing entries.

## Optimal solution, traced

```steps
Sort by end: [1, 4], [3, 6], [7, 8]
    fire at {{4}}
---
[3, 6] contains 4
    no new arrow
---
[7, 8] starts after 4
    fire at 8; answer {{2}}
```

Every new arrow is required for an interval whose start lies after the previous chosen endpoint. The exchange argument shows the greedy placement leaves an optimal completion possible after each choice.

## Code

```python
def minimum_arrows(intervals):
    ordered = sorted(intervals, key=lambda interval: interval[1])
    arrows = 0
    position = None
    for start, end in ordered:
        if position is None or start > position:
            arrows += 1
            position = end
    return arrows
```

## Complexity

Sorting takes O(n log n) time and O(n) space for the sorted copy. The subsequent scan takes O(n) time and O(1) additional working space, excluding the copy.

## Mistakes and edge cases

- Sort by end, not by start.
- A balloon starting exactly at the arrow position is already hit.
- Empty input needs zero arrows.

## Variations

- Return the chosen arrow coordinates.
- Select the largest collection of non-overlapping intervals instead.
- Change the endpoint convention and revisit the equality case.

=== card | 435
time: 30 min

## The problem

Remove the fewest intervals so the remaining intervals do not overlap. For this task, two intervals may touch at an endpoint without overlapping.

For `[1, 3]`, `[2, 4]`, and `[3, 5]`, keep the first and third and remove the second, so the answer is 1.

## Constraints and what they imply

Each interval has positive length. The input need not be sorted. Because touching is allowed, an interval starting exactly when the last kept interval ends is compatible. Minimising removals is equivalent to maximising how many intervals remain.

## Brute force

Enumerate every subset of intervals, test whether its members are pairwise non-overlapping, and keep the largest valid subset. There are `2^n` subsets; repeated subset construction and overlap checks are the bottleneck.

## The insight

Sort intervals by end and greedily keep an interval when its start is at least the end of the last kept one. The earliest-ending available interval leaves at least as much room for the rest as any later-ending choice.

To justify the greedy choice, take an optimal schedule and replace its first interval with the earliest-ending interval. The replacement ends no later, so every later interval in that schedule still fits. The resulting schedule has the same size and begins with the greedy choice; repeat on the remaining intervals.

This proof does not depend on the input's original order. After sorting, every interval tested later ends at least as late as the current choice. The algorithm keeps only the last chosen end because earlier chosen intervals finish no later and cannot introduce an additional conflict.

## Optimal solution, traced

```steps
Sort by end: [1, 3], [2, 4], [3, 5]
    keep [1, 3]
---
[2, 4] starts before the last kept end
    remove it
---
[3, 5] starts exactly at that end
    keep it; {{1 removal}}
```

The exchange argument proves that a maximum-size compatible set can always start with each greedy choice. The number removed is the original number of intervals minus the number kept.

## Code

```python
def minimum_interval_removals(intervals):
    ordered = sorted(intervals, key=lambda interval: interval[1])
    kept = 0
    last_end = None
    for start, end in ordered:
        if last_end is None or start >= last_end:
            kept += 1
            last_end = end
    return len(intervals) - kept
```

## Complexity

Sorting takes O(n log n) time and O(n) space for the sorted copy. The scan takes O(n) time and O(1) additional working space.

## Mistakes and edge cases

- The equality case differs from closed-interval grouping: touching is allowed here.
- Sort by ending coordinate to support the exchange argument.
- An empty list needs no removals.

## Variations

- Return the indices of intervals to keep.
- Maximise the number of intervals when each has a weight; a simple greedy is no longer sufficient.
- Compare this activity-selection greedy with the arrow-placement greedy.

=== card | cses:1164
time: 30 min

## The problem

Customers arrive and leave on specified integer days. A room cannot be assigned to two customers present on the same day, including an arrival on another customer's departure day. Assign a room number to every customer and minimise the number of rooms.

For stays `[1, 2]`, `[2, 3]`, and `[3, 4]`, the first two overlap on day 2, and the latter two overlap on day 3. Two rooms suffice: assign the first and third to one room and the middle stay to another.

## Constraints and what they imply

Both arrival and departure days are included. Output room numbers must correspond to the original customer order, even if customers are processed in sorted order. A room whose previous departure equals a new arrival cannot yet be reused.

## Brute force

Try assigning each customer to every compatible existing room or to a new room, then keep the assignment using the fewest rooms. The number of possible assignments grows exponentially. Repeatedly trying equivalent room arrangements is the bottleneck.

## The insight

Sort customers by arrival and keep a min-heap of `(departure, room_number)` for each allocated room. If the earliest departure is strictly before the next arrival, reuse that room. Otherwise every room is occupied on the arrival day and a new room is necessary. Store the chosen room under the customer's original index.

The heap includes rooms whose latest booking has finished; they remain available to be reused. Only one room is needed for each arrival, so there is no need to remove all expired entries at once.

## Optimal solution, traced

```steps
Customer [1, 2] gets room 1
    heap [(2, 1)]
---
Customer [2, 3] arrives on day 2; 2 is not before 2
    allocate room 2; heap [(2, 1), (3, 2)]
---
Customer [3, 4] arrives after room 1's departure
    reuse {{room 1}}; total rooms {{2}}
```

Every assigned room is valid because reuse occurs only after its previous stay ends. Whenever a new room is allocated, all current room-ending days are at least the arrival day, and their most recent customers have already arrived. Those customers and the new one overlap on that day, proving the new room is necessary.

## Code

```python
from heapq import heappop, heappush


def allocate_rooms(stays):
    occupied = []
    assignments = [0] * len(stays)
    rooms = 0
    order = sorted(range(len(stays)), key=lambda i: (stays[i][0], stays[i][1], i))
    for i in order:
        arrival, departure = stays[i]
        if occupied and occupied[0][0] < arrival:
            _, room = heappop(occupied)
        else:
            rooms += 1
            room = rooms
        assignments[i] = room
        heappush(occupied, (departure, room))
    return rooms, assignments
```

## Complexity

Sorting takes O(n log n). Each customer causes at most one heap pop and one push, each O(log n), so the total is O(n log n). The heap, sorted indices and returned assignment use O(n) space.

## Mistakes and edge cases

- Use departure `<` arrival, not `<=`, for inclusive days.
- Keep each customer's original index through sorting.
- Store one heap entry per allocated room, updating it whenever the room is reused.

## Variations

- Return only the room count using a sweep of arrival and departure events.
- If stays are half-open, allow reuse when departure equals arrival.
- Use the same heap pattern to schedule other non-overlapping resources.

=== card | 1851
time: 45 min

## The problem

Given closed integer intervals and query points, return the length of the shortest interval containing each query. An interval `[left, right]` has length `right - left + 1`. Return `-1` when no interval contains the point. Answers must follow the original query order.

For intervals `[1, 4]`, `[2, 4]`, `[3, 6]` and queries `2, 5`, the answers are 3 and 4: `[2, 4]` is shortest for 2, and `[3, 6]` is the only one containing 5.

## Constraints and what they imply

Both interval endpoints are included. There can be many intervals and many queries, including repeated query values. All queries are known before answers are needed, so they may be processed in sorted order as long as their original indices are retained. The value range may be large, so allocating one array cell per possible coordinate is not appropriate.

## Brute force

For every query, scan all `n` intervals, test `left <= query <= right`, and take the minimum length among matches. For `q` queries this takes O(nq) time and O(q) output space. The bottleneck is repeatedly scanning intervals that start too late or have already ended for many queries.

## The insight

Sort the intervals by left endpoint and sort query indices by query value. Sweep queries from left to right. Before answering a query, insert every interval whose left endpoint is at most that query into a min-heap keyed by `(length, right_endpoint)`. Remove heap entries whose right endpoint is less than the current query. The top, if any, is the shortest interval that can cover the query.

Removal is lazy. An expired interval buried below a shorter valid heap entry cannot change the current answer. If that expired interval later reaches the top, it is removed before the top is read. Since future query points only increase, an expired interval can never become valid again.

## Optimal solution, traced

```steps
Intervals sorted by start: [1, 4], [2, 4], [3, 6]
Queries sorted by value: 2, 5
---
At query 2, add [1, 4] length 4 and [2, 4] length 3
    shortest valid length {{3}}
---
At query 5, add [3, 6] length 4
    discard expired heap tops ending at 4
    shortest valid length {{4}}
```

Immediately before the answer is read, every interval starting at or before the query has been considered. Any heap top ending before the query is removed. Thus a surviving top contains the query. Every containing interval remains in the heap, because its end has not expired; the heap's length ordering makes the top no longer than any other containing interval.

Sorting queries is safe because the queries do not modify the original problem. The result array maps each processed query back to its input index, including repeated query values.

For a query before every interval starts, nothing has been inserted and its answer remains `-1`. For two covering intervals with equal length, either may appear first in the heap because only the minimum length is requested. The right endpoint is included in the heap entry to detect expiration, not to change the required answer.

## Code

```python
from heapq import heappop, heappush


def minimum_covering_intervals(intervals, queries):
    ordered = sorted(intervals)
    order = sorted(range(len(queries)), key=queries.__getitem__)
    answer = [-1] * len(queries)
    heap = []
    i = 0
    for query_index in order:
        point = queries[query_index]
        while i < len(ordered) and ordered[i][0] <= point:
            left, right = ordered[i]
            heappush(heap, (right - left + 1, right))
            i += 1
        while heap and heap[0][1] < point:
            heappop(heap)
        if heap:
            answer[query_index] = heap[0][0]
    return answer
```

## Complexity

Sorting costs O(n log n + q log q). Each interval is pushed once and popped at most once, costing O(n log n) total heap work; each query inspects the heap in O(1) after removals. Overall time is O(n log n + q log q), with O(n + q) space for the sorted inputs, heap, indices and returned answers.

## Mistakes and edge cases

- The interval length includes both endpoints, so add one.
- An interval ending exactly at the query still contains it; expire only when `right < query`.
- Preserve query indices when sorting, especially with duplicate queries.
- Do not assume every expired entry is immediately removed; only the heap top must be valid before answering.

## Variations

- Return the original index of a shortest covering interval, breaking ties explicitly.
- Report the number of intervals containing each query using a sweep of endpoint events.
- If queries arrive online, investigate a different indexed structure rather than relying on sorted future queries.

=== card | 218
time: 45 min

## The problem

Each building is described by a left coordinate, a right coordinate and a positive height. A building occupies the half-open horizontal range `[left, right)`. Return the skyline as points `[x, height]` where the visible outline changes height. The outline returns to height zero after the final building.

For buildings `[1, 4, 3]` and `[2, 5, 5]`, the outline rises to 3 at 1, rises to 5 at 2, and falls to 0 at 5: `[[1, 3], [2, 5], [5, 0]]`. The first building ending at 4 causes no visible change because the taller building still covers that point.

## Constraints and what they imply

Buildings can overlap, be nested or share endpoints. A building is active at its left coordinate and inactive at its right coordinate. The skyline can change only at a building endpoint, not between endpoints. Multiple starts and ends at the same coordinate must be considered together; otherwise the output may contain spurious repeated points at the same `x`.

## Brute force

Collect all distinct endpoints. At each endpoint, inspect every building and find the maximum height among those with `left <= x < right`. Emit a point when that maximum differs from the previous height. With `n` buildings and at most `2n` endpoints, this takes O(n²) time. Repeatedly examining every building at every endpoint is the bottleneck.

## The insight

Sweep endpoints from left to right. At each `x`, add all buildings starting there to a max-heap represented by negative heights. Each heap entry also records the building's right endpoint. Remove entries from the heap top while they have ended at or before `x`. The remaining top is the greatest active height; a zero-height sentinel handles an empty skyline.

An expired building can remain buried in the heap: while another active building is taller, the expired one cannot affect the visible height. When an expired entry reaches the top, the removal loop discards it before reporting. Add all starts and remove expired tops before comparing the height, so simultaneous events produce at most one point.

## Optimal solution, traced

```steps
At x=1, add height 3 ending at 4
    visible height {{3}}; emit [1, 3]
---
At x=2, add height 5 ending at 5
    visible height {{5}}; emit [2, 5]
---
At x=4, height 3 has ended but is below the active height 5
    visible height stays 5; emit nothing
---
At x=5, discard expired heap tops
    visible height {{0}}; emit [5, 0]
```

At each endpoint, every building starting no later than that coordinate has been added. The loop ensures the top entry is still active. Any active building taller than that top would precede it in the heap, so the top gives the correct visible height. Expired entries below the top cannot change the maximum until they rise to the top, when they are removed.

The skyline is constant between consecutive endpoints because no building starts or ends there. Emitting only when the height changes therefore captures the complete outline without redundant adjacent points of equal height.

For example, if one height-3 building ends exactly where another height-3 building starts, the outline remains at height 3 there. Processing both events before emitting avoids a false drop to zero and a second rise at the same coordinate.

## Code

```python
from heapq import heappop, heappush


def skyline(buildings):
    starts = {}
    endpoints = set()
    for left, right, height in buildings:
        starts.setdefault(left, []).append((height, right))
        endpoints.add(left)
        endpoints.add(right)
    heap = [(0, float("inf"))]
    result = []
    previous = 0
    for x in sorted(endpoints):
        for height, right in starts.get(x, []):
            heappush(heap, (-height, right))
        while heap[0][1] <= x:
            heappop(heap)
        height = -heap[0][0]
        if height != previous:
            result.append([x, height])
            previous = height
    return result
```

## Complexity

There are at most `2n` distinct endpoints. Sorting them takes O(n log n); each building is pushed once and popped at most once, giving O(n log n) heap work. The endpoints, start lists, heap and returned skyline use O(n) space.

## Mistakes and edge cases

- Treat right edges as exclusive: remove an entry when `right <= x`.
- Process all events at one coordinate before emitting a height change.
- A hidden expired building may remain in the heap; do not assume every heap entry is active.
- Return to height zero after the last building, and avoid consecutive points with the same height.

## Variations

- Return the visible area under the skyline using consecutive output points.
- Maintain a multiset of active heights with explicit removal rather than lazy heap expiration.
- Compute an outline for buildings arriving online, where future endpoints are not known in advance.
