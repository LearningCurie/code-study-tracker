---
key: intervals
name: Intervals and sweep line
stage: order
summary: Represent ranges cleanly, then sort them (by start, by end, or as +1 and -1 events) and sweep once, carrying a counter or a heap of what is active: merging, inserting, peak overlap, rooms, scheduling, offline queries and free time.
why: Bookings, sessions, leases, shifts, log time windows, genome features and byte ranges are all intervals, and the questions asked about them repeat: do two overlap, what is the union, how busy is the busiest moment, how many rooms or machines are needed, which requests can all be served, when is everyone free. Nearly every answer is "sort once, sweep once" with the right sort key and the right tie-break, plus a heap when you need to know which interval is active. Getting the endpoint convention wrong is the classic off-by-one, and getting the sort key wrong is the classic wrong answer. The same sweeps run inside calendar free/busy lookups, database exclusion constraints, genome tools and kernel interval trees, and this stage's project applies them to time ranges in logs.
outcomes:
- Choose closed or half-open endpoints deliberately and test overlap, intersection and containment without off-by-one errors
- Merge overlapping intervals and prove that sorting by start makes one pass enough, then turn merged busy time into free slots
- Insert into, remove from and query a sorted list of disjoint intervals in one pass or with binary search
- Compute peak concurrency with a +1/-1 event sweep or a difference array, with the tie-break that matches the endpoint convention
- Count and assign rooms with a heap of end times, and prove that the count equals the peak overlap
- Select the most non-overlapping intervals by earliest end with an exchange-argument proof, and answer offline point queries with a sorted sweep and a heap
cues:
- Pairs of start and end times, dates, positions or coordinates
- "Overlap", "merge", "union", "conflict", "covered", "gap", "free time"
- "At the same time", "busiest moment", "minimum number of rooms, machines or groups"
- "Maximum number of non-overlapping", "minimum to remove" or "fewest points that hit every interval"
- Many point or time queries against a fixed set of intervals
traps:
- Mixing closed and half-open endpoints, so touching intervals count as overlapping in one place and not in another
- Sorting by start when the question needs the earliest end (selection, arrows), or by end when it needs the start (merging, rooms)
- Breaking ties between events at the same time the wrong way, which over- or under-counts touching intervals
- Setting a merged block's end to the new interval's end instead of the larger of the two, so a contained interval shrinks the block
- Answering queries in sorted order and returning the answers without restoring the original order
systems:
- Calendar free/busy: iCalendar (RFC 5545) VFREEBUSY components publish busy periods, and finding a slot for a group means pooling everyone's busy periods, sweeping them and taking the gaps
- PostgreSQL range types with an exclusion constraint (EXCLUDE USING GIST (room WITH =, during WITH &&)) make the database itself reject overlapping bookings
- Genomics: bedtools merge collapses overlapping features in a BED file sorted by chromosome and start, the merge-intervals pass at genome scale
- The Linux kernel provides interval trees built on augmented red-black trees for overlap queries that must stay fast while intervals come and go
further:
- Article · 10 min | Tech Interview Handbook: Interval cheatsheet | https://www.techinterviewhandbook.org/algorithms/interval/#techniques
- Article · 15 min | USACO Guide: Sweep Line, Restaurant Customers | https://usaco.guide/plat/sweep-line#restaurant-customers
- Notes · 20 min | Kleinberg and Tardos slides: Greedy Algorithms I, interval scheduling and partitioning (PDF) | https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/04GreedyAlgorithmsI.pdf
- Docs · 10 min | PostgreSQL: Range types, constraints on ranges | https://www.postgresql.org/docs/current/rangetypes.html#RANGETYPES-CONSTRAINT
bank: intervals
---

=== primer | When do two intervals overlap, and should the end be included? | 13 min
goal: Pick closed or half-open endpoints on purpose, and test overlap, intersection and containment without off-by-one errors
tag: intervals-overlap | Overlap and intersection tests
link: Tech Interview Handbook: Interval | https://www.techinterviewhandbook.org/algorithms/interval/#techniques | 5 min: 'Corner cases' and 'Techniques', especially the one-line overlap check and merging two intervals
link: PostgreSQL docs: Range types, inclusive and exclusive bounds | https://www.postgresql.org/docs/current/rangetypes.html#RANGETYPES-INCLUSIVITY | 5 min: how '[' and ')' mark inclusive and exclusive bounds, then 'Discrete Range Types', which explains why integer and date ranges are stored as [lower, upper)
practice: 986

> [!key]
> Store an interval as a (start, end) pair and decide once what the end means. With **half-open** intervals [s, e), two intervals overlap exactly when `a.s < b.e and b.s < a.e`; their intersection is [max of the starts, min of the ends) when that is non-empty; the length is e - s. **Closed** intervals [s, e] use `<=` instead. Half-open is the safer default: touching intervals do not overlap, lengths need no +1, and splitting [s, e) at t gives [s, t) and [t, e) with nothing lost or counted twice.

## Intuition

A meeting from 9:00 to 10:00 and another from 10:00 to 11:00 can share a room: the first ends at the instant the second begins. That is half-open thinking, where the end point is not part of the interval. Hotel stays work the same way: the night you check out is not yours. Seat numbers, page ranges and "the years 1990 to 1999 inclusive" are closed: both ends belong. Most interval bugs come from mixing the two without noticing.

## How it works

### Every way two intervals can sit

```text
time  0  1  2  3  4  5  6  7  8  9  10 11 12
a                 [===========)             a = [4, 8)
b1                               [========) after a: no overlap
b2                            [========)    touches a at 8: no overlap (half-open)
b3                      [===========)       overlaps the right part of a
b4                   [=====)                inside a
b5          [=======================)       contains a
b6       [========)                         touches a at 4: no overlap
b7    [=====)                               before a: no overlap
```

Rather than testing every case, test the only two ways to **fail** to overlap: a ends before b starts (`a.e <= b.s`), or b ends before a starts (`b.e <= a.s`). Overlap is the negation: `a.s < b.e and b.s < a.e`. One line covers partial overlaps on both sides, containment in both directions and touching, which is why it is worth memorising.

### Intersection, union and containment

- **Intersection:** s = max(a.s, b.s) and e = min(a.e, b.e); it is non-empty when s < e (closed: s <= e).
- **Union** of two overlapping or touching intervals: [min of the starts, max of the ends).
- **Containment:** a contains b when a.s <= b.s and b.e <= a.e.

### Converting between conventions

For integers, the closed [s, e] is the half-open [s, e + 1). Convert at the edge of your code and use one convention inside it. Python's `range(s, e)` and slices are half-open. PostgreSQL stores discrete ranges (integers, dates) in the canonical form [lower, upper), whichever form you typed.

### Intersecting two sorted lists

Two people's free time, each a sorted list of disjoint slots: walk both with two pointers. Record the intersection of the current pair if it is non-empty, then advance the slot that **ends first**. It cannot meet anything later in the other list: every later slot there starts after the other list's current slot ends, which is no earlier than this one's end.

## Cost

Each test is O(1). Checking all pairs of n intervals is O(n^2), which the rest of this module replaces with one sort (O(n log n)) and one pass. Intersecting two sorted lists of sizes m and n is O(m + n): every step advances a pointer.

## When to use it

Every interval problem starts here. Read the statement for the endpoint convention before you write code:

| The problem says | Convention | Touching intervals |
|---|---|---|
| meetings or bookings; one ends at 10, the next starts at 10 | half-open | no conflict |
| merge intervals: [1, 4] and [4, 5] become [1, 5] (LeetCode 56) | closed | merge |
| an arrow at x bursts a balloon [s, e] if s <= x <= e (LeetCode 452) | closed | one arrow hits both |
| [1, 2] and [2, 3] do not overlap (LeetCode 435) | half-open | may both be kept |
| a person is not counted in the year they die (LeetCode 1854) | half-open [birth, death) | |
| integer points covered, both ends included (LeetCode 2848) | closed | share a point |

## Worked trace

Common free time of A and B, each a sorted list of disjoint half-open slots, in hours:

```steps
Free time of two people, each a sorted list of disjoint half-open slots. i and j start at the first slot of each
    time   9   10  11  12  13  14  15  16  17  18
    A      {{[=======)}}       [===========)   [===)
    B          {{[===============)}}   [=======)
    common (none yet)
---
A[0] = (9, 11), B[0] = (10, 14): max of starts 10, min of ends 11. 10 < 11, so record (10, 11). A[0] ends first, so it cannot meet any later B slot: i += 1
    time   9   10  11  12  13  14  15  16  17  18
    A      [=======)       {{[===========)}}   [===)
    B          {{[===============)}}   [=======)
    common     [===)
---
A[1] = (13, 16), B[0] = (10, 14): max of starts 13, min of ends 14. 13 < 14, so record (13, 14). B[0] ends first (or tie): j += 1
    time   9   10  11  12  13  14  15  16  17  18
    A      [=======)       {{[===========)}}   [===)
    B          [===============)   {{[=======)}}
    common     [===)       [===)
---
A[1] = (13, 16), B[1] = (15, 17): max of starts 15, min of ends 16. 15 < 16, so record (15, 16). A[1] ends first, so it cannot meet any later B slot: i += 1
    time   9   10  11  12  13  14  15  16  17  18
    A      [=======)       [===========)   {{[===)}}
    B          [===============)   {{[=======)}}
    common     [===)       [===)   [===)
---
A[2] = (17, 18), B[1] = (15, 17): max of starts 17, min of ends 17. 17 >= 17: no overlap. B[1] ends first (or tie): j += 1. B is used up: done, common = [(10, 11), (13, 14), (15, 16)]
    time   9   10  11  12  13  14  15  16  17  18
    A      [=======)       [===========)   {{[===)}}
    B          [===============)   [=======)
    common     [===)       [===)   [===)
```

## Template

```python
def overlaps(a, b):
    """Half-open [start, end): do a and b share at least one point?"""
    return a[0] < b[1] and b[0] < a[1]


def overlaps_closed(a, b):
    """Closed [start, end]: touching endpoints count as overlap."""
    return a[0] <= b[1] and b[0] <= a[1]


def intersection(a, b):
    """Half-open intersection of a and b, or None if they do not overlap."""
    s, e = max(a[0], b[0]), min(a[1], b[1])
    return (s, e) if s < e else None


def common_slots(A, B):
    """Both inputs: sorted, disjoint, half-open intervals. Returns their pairwise
    intersections in order: O(len(A) + len(B))."""
    out, i, j = [], 0, 0
    while i < len(A) and j < len(B):
        s, e = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if s < e:
            out.append((s, e))
        if A[i][1] < B[j][1]:          # the one that ends first cannot meet anything else
            i += 1
        else:
            j += 1
    return out
```

## Pitfalls

- **Testing one direction only.** `a.s <= b.s < a.e` assumes b starts inside a, so it misses b starting before a: b containing a, or overlapping a from the left.
- **Mixing conventions.** `<` in one function and `<=` in another treats touching intervals inconsistently. Convert at the edges, then use one convention.
- **Lengths.** A closed integer interval has e - s + 1 points; a half-open one has e - s.
- **"Inclusive" times like 23:59:59.** They lose the last second and break at other resolutions. Use the next day's 00:00 as an exclusive end.
- **Floating-point ends.** Equality is unreliable, so "touching" can be decided by rounding error. Store integer units (minutes, milliseconds) where you can.

## Check yourself

Q: Do [1, 5) and [5, 8) overlap? Do the closed [1, 5] and [5, 8]? What is the intersection in each case?
A: Half-open: no, because 5 < 5 is false; the candidate intersection [5, 5) is empty. Closed: yes, they share the point 5, and the intersection is [5, 5], a single point.

Q: Why is `a.s < b.e and b.s < a.e` correct for every relative position, including containment?
A: Two intervals fail to overlap only when one lies entirely before the other: a.e <= b.s or b.e <= a.s. Negating that "or" (De Morgan) gives a.s < b.e and b.s < a.e. Containment satisfies both inequalities, so it needs no special case.

Q: Spot the bug: `def overlaps(a, b): return a[0] <= b[0] < a[1]`.
A: It assumes b starts inside a. For a = (3, 6) and b = (1, 4) the intervals share [3, 4), but the function returns False because b starts before a. Use the symmetric two-sided test.

## Lab

- **986 Interval List Intersections.** Two pointers over two sorted lists of closed intervals: record [max start, min end] when start <= end, then advance whichever ends first. Expected: `[[0, 2], [5, 10], [13, 23], [24, 25]]` and `[[1, 5], [8, 12], [15, 24], [25, 26]]` give `[[1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]]`; O(m + n).
- **Exhaustive check.** Compare `overlaps` and `overlaps_closed` with a brute force on sets of integer points (`set(range(s, e))` for half-open, `set(range(s, e + 1))` for closed), for every pair of intervals inside [0, 8]. Expected: no disagreement in the 1,296 half-open pairs (36 intervals with 0 <= s < e <= 8) or the 2,025 closed pairs (45 intervals with 0 <= s <= e <= 8).

> [!know]
> You now know how to choose an endpoint convention and test overlap, intersection and containment with one line each.

=== primer | How do you merge overlapping intervals, and why is sorting by start enough? | 14 min
goal: Merge any set of intervals in O(n log n) with one pass after sorting by start, prove that one pass suffices, and read gaps and covered length off the merged blocks
tag: intervals-merge | Sort by start and merge
link: cp-algorithms: Length of the union of segments | https://cp-algorithms.com/geometry/length-of-segments-union.html | 5 min, the whole short page: the same union measured by a counting sweep over the 2n sorted endpoints, a useful second view of merging
link: bedtools docs: merge | https://bedtools.readthedocs.io/en/latest/content/tools/merge.html | 5 min: the opening description and its note that input must be sorted by chromosome and start, then the '-d' option, which merges features that are close but not touching
practice: 56, 2848

> [!key]
> Sort the intervals by start and walk through them, keeping the last merged block. Each interval either overlaps (or touches) that block, so you extend the block's end to the larger of the two ends, or starts beyond it, so it begins a new block. Sorting is the whole trick: afterwards an interval can only ever touch the **last** block, so one pass is enough, and the total cost is O(n log n).

## Intuition

Lay strips of tape on a ruler, taking them in order of where they start. Each new strip either overlaps the patch you are building (stick it on; the patch may get longer) or starts beyond the patch's end (begin a new patch). You never go back to an earlier patch, because every strip from now on starts even further to the right.

## How it works

1. Sort by start; ties can be in any order.
2. For each interval (s, e): if the output is non-empty and s <= the last block's end, set that end to max(end, e). Otherwise append [s, e] as a new block.

The test `s <= end` merges touching closed intervals such as [1, 4] and [4, 5], as LeetCode 56 wants; use `s < end` if touching intervals must stay separate.

### Why one pass is enough

**Invariant:** after the first i intervals in sorted order, `out` is exactly their union, as sorted blocks with a gap between neighbours; and every remaining interval starts at or after the last block's start.

Take the next interval x. Each earlier block ends before the next block starts, so every block before the last ends before the last block starts, which is no later than x starts (starts are sorted). So x cannot touch any block except the last. Either x overlaps or touches the last block, and their union is [last start, max(last end, x's end)], or x starts after it and becomes a new block. Either way the invariant holds for i + 1 intervals.

The `max` matters: an interval can lie entirely inside the last block, like [4, 5] inside [1, 6], and taking its end would shrink the block.

### What merged blocks give you

- **Covered length:** the sum of the block lengths (e - s + 1 for closed integer blocks), with nothing counted twice.
- **Gaps:** the stretches between consecutive blocks are exactly the uncovered time. Merge everyone's busy periods and the gaps are when everyone is free; the last card of this module does that in one pass with a cursor.
- **Coalescing:** adjacent or overlapping ranges become one, as in IP allow lists, byte ranges of a download, or dirty regions of a screen.

## Cost

Sorting is O(n log n); the pass is O(n), with O(1) work per interval; the output holds at most n blocks. If the input already arrives sorted by start (as many tools require of their input files), merging is O(n) and streams in one pass, holding only the current block in memory.

## When to use it

Cues: "merge overlapping", "union", "total covered length", "how many points are covered", "coalesce adjacent ranges", "gaps", "free time".

In production: `bedtools merge`, the standard genomics tool for collapsing overlapping features, requires its BED input to be sorted by chromosome and start and then makes exactly this pass; its `-d` option merges features up to d bases apart, which is the same as relaxing the touching rule.

Not when you need multiplicity: merging throws away how many intervals cover each point, so "how busy is the busiest moment" needs the sweep with a counter (a later card). Not when you need to know which original intervals ended up in each block, unless you carry their ids along.

## Worked trace

Merge `[[8, 10], [1, 3], [2, 6], [15, 18], [17, 20], [4, 5]]` (closed intervals, touching merges):

```steps
Sort by start: [[1, 3], [2, 6], [4, 5], [8, 10], [15, 18], [17, 20]]
    sorted [[1, 3], [2, 6], [4, 5], [8, 10], [15, 18], [17, 20]]
    out    []
---
[1, 3]: out is empty, start the first block
    sorted {{[1, 3]}}  [2, 6]  [4, 5]  [8, 10]  [15, 18]  [17, 20]
    out    [[1, 3]]
---
[2, 6] starts at 2 <= 3, the last end: extend the end to max(3, 6) = 6
    sorted [1, 3]  {{[2, 6]}}  [4, 5]  [8, 10]  [15, 18]  [17, 20]
    out    [[1, 6]]
---
[4, 5] starts at 4 <= 6, the last end, and lies inside it: end stays max(6, 5) = 6
    sorted [1, 3]  [2, 6]  {{[4, 5]}}  [8, 10]  [15, 18]  [17, 20]
    out    [[1, 6]]
---
[8, 10] starts after the last end 6: start a new block
    sorted [1, 3]  [2, 6]  [4, 5]  {{[8, 10]}}  [15, 18]  [17, 20]
    out    [[1, 6], [8, 10]]
---
[15, 18] starts after the last end 10: start a new block
    sorted [1, 3]  [2, 6]  [4, 5]  [8, 10]  {{[15, 18]}}  [17, 20]
    out    [[1, 6], [8, 10], [15, 18]]
---
[17, 20] starts at 17 <= 18, the last end: extend the end to max(18, 20) = 20
    sorted [1, 3]  [2, 6]  [4, 5]  [8, 10]  [15, 18]  {{[17, 20]}}
    out    [[1, 6], [8, 10], [15, 20]]
```

## Template

```python
def merge(intervals):
    """Union of closed intervals [s, e] as sorted, disjoint intervals: O(n log n)."""
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:            # overlaps or touches the last block
            out[-1][1] = max(out[-1][1], e)    # max: the new one may lie inside
        else:
            out.append([s, e])                 # a fresh list, never the caller's
    return out
```

## Pitfalls

- **`end = e` instead of `max(end, e)`.** A contained interval shrinks the block: `[[1, 6], [2, 3]]` would become `[[1, 3]]`.
- **Sorting by end.** Then a later interval may start before an earlier block. `[[2, 3], [1, 10]]` is already sorted by end, and the pass produces `[[2, 10]]` instead of `[[1, 10]]`.
- **Aliasing the input.** `out.append(iv)` followed by `out[-1][1] = ...` edits the caller's list; append a fresh `[s, e]`.
- **The touching rule.** `<=` merges [1, 4] and [4, 5]; `<` keeps them apart. Match the problem's convention.
- **Empty input.** The template returns `[]` with no special case.

## Check yourself

Q: Merge `[[1, 10], [2, 3], [4, 5], [11, 12]]` with the template. What happens at [2, 3] and at [11, 12]?
A: The list is already sorted. [1, 10] starts the first block. [2, 3] starts at 2 <= 10, and max(10, 3) keeps the end at 10; [4, 5] does the same. [11, 12] starts at 11 > 10, so it begins a new block: the result is `[[1, 10], [11, 12]]`.

Q: After sorting by start, why can the next interval never touch a block before the last one?
A: The blocks are separated by gaps, so every earlier block ends before the last block starts, and the last block starts no later than the next interval, because starts are sorted. The next interval therefore starts after every earlier block has ended.

Q: How many integer points do the closed intervals `[[3, 6], [1, 5], [4, 7]]` cover, and why not just add their lengths?
A: Merging gives `[[1, 7]]`, which covers 7 - 1 + 1 = 7 points. Adding the lengths (4 + 5 + 4 = 13) counts the shared points several times.

## Lab

- **56 Merge Intervals.** Expected: `[[1, 3], [2, 6], [8, 10], [15, 18]]` gives `[[1, 6], [8, 10], [15, 18]]`, and `[[1, 4], [4, 5]]` gives `[[1, 5]]`; O(n log n).
- **2848 Points That Intersect With Cars.** Merge the closed ranges and add e - s + 1 per block (a difference array over 1 to 100 also works). Expected: `[[3, 6], [1, 5], [4, 7]]` gives 7, and `[[1, 3], [5, 8]]` gives 7.

> [!know]
> You now know how to merge intervals in one pass after sorting by start, why that is enough, and how to read covered length and gaps off the result.

=== primer | How do you insert or remove a range in a sorted list of disjoint intervals? | 14 min
goal: Insert, remove and query ranges in a sorted list of disjoint intervals, either in one linear pass or with binary search on the starts and the ends
tag: intervals-insert | Sorted sets of disjoint ranges
link: Python docs: bisect, Searching Sorted Lists | https://docs.python.org/3/library/bisect.html#searching-sorted-lists | 5 min: the find_lt, find_le, find_gt and find_ge recipes, which are exactly the neighbour lookups this card uses
link: PostgreSQL docs: Constraints on ranges | https://www.postgresql.org/docs/current/rangetypes.html#RANGETYPES-CONSTRAINT | 5 min: the exclusion-constraint examples that reject overlapping reservations, the database version of a booking calendar
practice: 57, 729

> [!key]
> In a sorted list of disjoint intervals, a new range splits the list into three parts: intervals entirely **before** it, intervals that **overlap or touch** it (absorb them all into one), and intervals entirely **after** it. One pass finds the parts in O(n). Because the starts *and* the ends of a sorted disjoint list are both sorted, binary search finds the two boundaries in O(log n), leaving only the splice. Removing a range is the mirror image: keep whatever sticks out on either side.

## Intuition

Add a booking to a diary sorted by time. Everything that finishes before the new booking starts stays put; everything that starts after it finishes stays put; whatever lies in between collides with it and is absorbed into one longer entry.

## How it works

### One pass (closed intervals, touching ones merge)

1. Copy every interval whose end is < the new start (before).
2. While the next interval starts <= the new end, absorb it: new start = min of the starts, new end = max of the ends.
3. Append the merged new interval, then copy the rest (after).

### With binary search

In a sorted list of disjoint intervals each interval ends before the next one starts, so the ends are sorted in the same order as the starts. Keep them as two parallel lists:

- `i = bisect_left(ends, s)`: the first interval that ends at or after s. Everything before i ends before s, so it is untouched.
- `j = bisect_right(starts, e)`: the first interval that starts after e. Everything from j on is untouched.
- Intervals i to j - 1 overlap or touch [s, e). Replace that slice with the single interval [min(s, starts[i]), max(e, ends[j - 1])).

The searches are O(log n); the slice assignment shifts the tail of each list, which is O(n) in the worst case but a fast C memmove. A `SortedList` or a balanced tree removes even that cost when n is large and updates are frequent.

### Removing a range

To remove [s, e), the affected intervals are those that end after s and start before e: `i = bisect_right(ends, s)` and `j = bisect_left(starts, e)`. Replace them with at most two pieces: [starts[i], s) if it is non-empty and [e, ends[j - 1]) if it is non-empty. An interval that contains [s, e) is split in two.

### Queries

- **Is [s, e) fully covered?** Find the last interval that starts at or before s; it is covered if that interval ends at or after e. (The stored intervals are merged, so a covered range lies inside a single one.)
- **Does [s, e) touch anything stored?** Find the first interval that ends after s; there is a conflict if it starts before e. That is the check a booking calendar makes before accepting an event.

## Cost

| Operation | One pass over a list | Bisect, then splice a list | `SortedList` or tree |
|---|---|---|---|
| insert or remove | O(n) | O(log n + k) to find, O(n) to shift | O(log n + k) |
| covered? or conflict? | O(n) | O(log n) | O(log n) |

Here k is the number of intervals absorbed. Each add creates one interval and each remove at most two, and an interval can be absorbed only once, so over any sequence of operations k is O(1) amortised.

## When to use it

Cues: maintain a set of covered ranges under add and remove ("range module", "reserve", "release", "free memory regions"); "insert an interval into a sorted list"; "is this slot free?" for a calendar.

In production: PostgreSQL's range types with an exclusion constraint, `EXCLUDE USING GIST (room WITH =, during WITH &&)`, make the database reject a booking that overlaps an existing one for the same room. That is this card's conflict check, with a GiST index finding the neighbours instead of bisect, and it holds even when two clients insert at the same moment.

Not when the stored intervals may overlap each other and you need to know how many cover a point: that is a counting problem for the sweep, or for a segment tree in the range-query module.

## Worked trace

Add [4, 8) to five disjoint ranges, the half-open version of LeetCode 57's second example:

```steps
Add [4, 8) to five sorted, disjoint ranges kept as two parallel sorted lists
    index     0   1   2   3   4
    starts    1   3   6   8  12
    ends      2   5   7  10  16
    time   0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16
    ranges    [==)  [=====)  [==)  [=====)     [===========)
    new                [===========)
---
i = bisect_left(ends, 4) = 1: ranges before i end before 4, so they are untouched (phase 1)
    index     0   1   2   3   4
    starts    1   3   6   8  12
    ends      2   {{5}}   7  10  16
---
j = bisect_right(starts, 8) = 4: ranges from j on start after 8, also untouched (phase 3)
    index     0   1   2   3   4
    starts    1   3   6   8  {{12}}
    ends      2   5   7  10  16
---
Ranges 1 to 3 overlap or touch [4, 8) (phase 2): replace them with [min(4, 3), max(8, 10)) = [3, 10)
    index     0   1   2   3   4
    starts    1   {{3}}   {{6}}   {{8}}  12
    ends      2   {{5}}   {{7}}  {{10}}  16
---
One slice assignment per list: starts[1:4] = [3] and ends[1:4] = [10]. Result [(1, 2), (3, 10), (12, 16)]
    starts    1   {{3}}  12
    ends      2  {{10}}  16
    time   0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16
    ranges    [==)  {{[====================)}}     [===========)
```

## Template

```python
from bisect import bisect_left, bisect_right


class RangeSet:
    """A set of points stored as sorted, disjoint, half-open ranges [s, e).
    starts and ends are parallel sorted lists, so both can be binary searched."""

    def __init__(self):
        self.starts, self.ends = [], []

    def add(self, s, e):
        i = bisect_left(self.ends, s)          # first range that ends at or after s
        j = bisect_right(self.starts, e)       # ranges from j on start after e
        if i < j:                              # ranges i..j-1 overlap or touch [s, e)
            s, e = min(s, self.starts[i]), max(e, self.ends[j - 1])
        self.starts[i:j] = [s]
        self.ends[i:j] = [e]

    def remove(self, s, e):
        i = bisect_right(self.ends, s)         # first range that ends after s
        j = bisect_left(self.starts, e)        # ranges from j on start at or after e
        if i < j:                              # ranges i..j-1 overlap [s, e): keep what sticks out
            left = [(self.starts[i], s)] if self.starts[i] < s else []
            right = [(e, self.ends[j - 1])] if self.ends[j - 1] > e else []
            kept = left + right
            self.starts[i:j] = [a for a, _ in kept]
            self.ends[i:j] = [b for _, b in kept]

    def covers(self, s, e):
        """Is all of [s, e) in the set? (s < e)"""
        i = bisect_right(self.starts, s) - 1   # the last range starting at or before s
        return i >= 0 and self.ends[i] >= e

    def overlaps(self, s, e):
        """Does any stored point lie in [s, e)?"""
        i = bisect_right(self.ends, s)         # first range that ends after s
        return i < len(self.starts) and self.starts[i] < e
```

## Pitfalls

- **Forgetting the "after" part** in the one-pass version: every interval after the new one silently disappears from the output.
- **The touching rule.** `RangeSet` merges [1, 3) and [3, 5) into [1, 5), because together they cover one continuous stretch; a booking calendar treats them as two compatible bookings. Both are right for their purpose; know which you are writing.
- **Bisecting a list of pairs.** `bisect(intervals, [s, e])` compares lists element by element, which works for starts but is easy to get subtly wrong. Keep parallel lists of starts and ends, or use `key=` (Python 3.10 and later).
- **Mutating the list while iterating over it** in the one-pass version; build a new list instead.
- **Strict versus non-strict in removal.** Removing [3, 5) from [1, 10) must leave [1, 3) and [5, 10); the wrong bisect leaves an empty [3, 3) behind or loses a point.

## Check yourself

Q: Insert the closed [4, 8] into `[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]]`, touching intervals merging. Which intervals are before, absorbed and after, and what is the result?
A: Before: [1, 2], which ends before 4. Absorbed: [3, 5], [6, 7] and [8, 10], which start at or before 8 and end at or after 4. After: [12, 16]. The merged interval is [min(4, 3), max(8, 10)] = [3, 10], so the result is `[[1, 2], [3, 10], [12, 16]]`.

Q: Why does binary search work on the ends of a sorted disjoint list?
A: Sorted by start and pairwise disjoint means each interval ends before the next one starts, so the ends increase in the same order as the starts. Both lists are sorted, so "the first interval ending at or after s" and "the first interval starting after e" are each one bisect.

Q: A `RangeSet` holds [1, 10). What does it hold after `remove(3, 5)`, and what do `covers(1, 3)` and `covers(2, 6)` return?
A: [1, 3) and [5, 10). `covers(1, 3)` is True, since [1, 3) is still there. `covers(2, 6)` is False, because 3 and 4 are no longer in the set.

## Lab

- **57 Insert Interval.** The one-pass version with closed intervals. Expected: `[[1, 3], [6, 9]]` with `[2, 5]` gives `[[1, 5], [6, 9]]`; `[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]]` with `[4, 8]` gives `[[1, 2], [3, 10], [12, 16]]`; O(n).
- **729 My Calendar I.** Before booking [start, end), find the first booking that ends after start and reject the new one if that booking starts before end. Expected: book(10, 20) returns true, book(15, 25) false, book(20, 30) true; O(log n) search per booking.

> [!know]
> You now know how to insert, remove and query ranges in a sorted disjoint list, in one pass or with two binary searches.

=== primer | How many intervals overlap at the busiest moment? | 15 min
goal: Find peak concurrency with a sweep over +1 and -1 events, pick the tie-break that matches the endpoint convention, and switch to a difference array or two bisects when that is cheaper
tag: intervals-sweep | Sweep line with +1/-1 events
link: USACO Guide: Sweep Line | https://usaco.guide/plat/sweep-line#restaurant-customers | 10 min: 'Introduction' and 'Restaurant Customers': arrivals and departures become events, sorted and scanned with a counter
practice: 1854, 2406

> [!key]
> Turn every interval into two **events**: +1 at its start and -1 at its end. Sort the events by time and sweep through them with a running count of active intervals; the largest count is the peak overlap. At equal times, the order of +1 and -1 encodes the endpoint convention: for half-open intervals process ends first, so touching intervals are never counted together. When times are small integers, a **difference array** gives the same counts in O(n + range) without sorting.

## Intuition

A clicker at a restaurant door: +1 when someone comes in, -1 when someone leaves. You never need to know who is inside, only how many, and the busiest moment is simply the highest reading. Putting the clicks in time order is all the work there is.

## How it works

### Events and the running count

Each interval [s, e) contributes the events (s, +1) and (e, -1). Sort them and add the deltas in order, recording the largest running total.

**Invariant:** after all the events at times <= t have been processed, `active` equals the number of intervals that contain t (those with s <= t < e). The maximum over t is reached right after some +1 event, so taking the maximum after every event finds it.

### Tie-breaking

Because the maximum is taken after every single event, the order *within* one timestamp matters, even though the count after all of that timestamp's events is the same either way.

- **Half-open [s, e):** ends before starts at equal times, so an interval that ends at t is never counted together with one that starts at t. Sorting `(time, delta)` tuples in Python does this for free, because -1 < +1.
- **Closed [s, e]:** both intervals contain t, so starts must come first: sort by `(time, -delta)`, or convert integer intervals to [s, e + 1) and keep the default order.

### Difference array

When times are integers in a small range [lo, hi), skip the sort: `diff[s - lo] += 1` and `diff[e - lo] -= 1` for every interval, then a running sum gives the count at every time. That is O(n + (hi - lo)), and you get the whole load curve, not just its peak (the prefix-sums module's difference arrays).

### Count at a given time

With the starts and the ends sorted separately, the number of half-open intervals containing t is (number of starts <= t) - (number of ends <= t): two bisects, O(log n) per query after sorting. For closed intervals count the ends < t instead.

### Covered length

While sweeping, add (time - previous time) to a total whenever `active > 0`, and you get the length covered by at least one interval; with `active >= 2`, the length covered at least twice.

## Cost

2n events: O(n log n) to sort, O(n) to sweep, O(n) memory. The alternatives:

| Method | Time | Grows with the time resolution? |
|---|---|---|
| sweep over sorted events | O(n log n) | no |
| difference array | O(n + R) for R time steps | yes |
| mark every time step of every interval | O(total length of all intervals) | yes |
| compare every pair | O(n^2) | no, and it finds pairs, not the peak |

At minute resolution over a week, marking every minute of 50,000 bookings is still feasible; at second resolution it does 60 times more work, while the sweep does not change at all. The lab measures exactly that.

## When to use it

Cues: "the maximum number at the same time", "peak load", "busiest moment", "how many are active at time t", the minimum number of rooms or platforms when only the count is needed, population by year, total covered length.

Not when you must say which interval goes where (room assignment, the next card), or when intervals arrive online between queries (a sorted map of deltas, or a segment tree from the range-query module).

## Worked trace

Four half-open bookings [1, 4), [2, 6), [4, 7) and [5, 8):

```steps
Four half-open bookings become 8 events, sorted by (time, delta); at time 4 the end (-1) sorts first
    time   0  1  2  3  4  5  6  7  8  9
    #0        [========)
    #1           [===========)
    #2                 [========)
    #3                    [========)
    events (1,+1) (2,+1) (4,-1) (4,+1) (5,+1) (6,-1) (7,-1) (8,-1)
---
(1, +1): active = 1, new best 1
    events {{(1,+1)}} (2,+1) (4,-1) (4,+1) (5,+1) (6,-1) (7,-1) (8,-1)
    active 1   best 1
---
(2, +1): active = 2, new best 2
    events (1,+1) {{(2,+1)}} (4,-1) (4,+1) (5,+1) (6,-1) (7,-1) (8,-1)
    active 2   best 2
---
(4, -1): active = 1. Ending first means [1, 4) and [4, 7) are never counted together
    events (1,+1) (2,+1) {{(4,-1)}} (4,+1) (5,+1) (6,-1) (7,-1) (8,-1)
    active 1   best 2
---
(4, +1): active = 2
    events (1,+1) (2,+1) (4,-1) {{(4,+1)}} (5,+1) (6,-1) (7,-1) (8,-1)
    active 2   best 2
---
(5, +1): active = 3, new best 3
    events (1,+1) (2,+1) (4,-1) (4,+1) {{(5,+1)}} (6,-1) (7,-1) (8,-1)
    active 3   best 3
---
(6, -1): active = 2
    events (1,+1) (2,+1) (4,-1) (4,+1) (5,+1) {{(6,-1)}} (7,-1) (8,-1)
    active 2   best 3
---
The remaining ends bring active back to 0. Peak: 3 bookings at once, during [5, 6)
    events (1,+1) (2,+1) (4,-1) (4,+1) (5,+1) (6,-1) (7,-1) (8,-1)
    active 0   best 3
```

## Template

```python
from bisect import bisect_right


def max_overlap(intervals):
    """Most half-open intervals [s, e) that share one point: O(n log n)."""
    events = []
    for s, e in intervals:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()                              # at equal times (t, -1) comes before (t, 1)
    best = active = 0
    for _, delta in events:
        active += delta
        best = max(best, active)
    return best


def busiest_time(intervals, lo, hi):
    """Integer times in [lo, hi), half-open intervals inside it. Returns (count, earliest time
    with that count) using a difference array: O(n + (hi - lo))."""
    diff = [0] * (hi - lo + 1)
    for s, e in intervals:
        diff[s - lo] += 1
        diff[e - lo] -= 1
    best, when, active = 0, lo, 0
    for t in range(lo, hi):
        active += diff[t - lo]
        if active > best:
            best, when = active, t
    return best, when


def active_at(starts, ends, t):
    """How many half-open intervals contain t, given their starts and ends each sorted: O(log n)."""
    return bisect_right(starts, t) - bisect_right(ends, t)
```

## Pitfalls

- **The wrong tie order.** Starts before ends counts the half-open [1, 4) and [4, 7) as overlapping at 4. Python's default tuple order is right for half-open intervals and wrong for closed ones.
- **Difference array off by one.** The -1 for a half-open [s, e) goes at index e; for a closed [s, e] at e + 1. Size the array so that index exists.
- **When the peak happens.** Record the time at the event that raised `active` to a new maximum; the peak lasts until the next event.
- **Losing identity.** Sorting starts and ends separately is fine for counting but cannot tell you which intervals are active.

## Check yourself

Q: Half-open [1, 3), [2, 4) and [3, 5): list the sorted events with the running count. What is the peak?
A: (1, +1) gives 1, (2, +1) gives 2, (3, -1) gives 1, (3, +1) gives 2, (4, -1) gives 1, (5, -1) gives 0. The peak is 2: the end at 3 is processed before the start at 3, so [1, 3) and [3, 5) are never counted together.

Q: For half-open intervals, why must ends come before starts at the same time, when the count after all of that time's events is the same either way?
A: The maximum is taken after every single event. Processing the start first would briefly count an interval that has already ended together with one that is starting, so the reported peak could be one too high even though the final count at that time is right.

Q: The closed meetings [1, 3] and [3, 5] are swept with Python's default `(time, delta)` order. What peak is reported, and what is correct?
A: It reports 1, because (3, -1) sorts before (3, +1). Closed intervals both contain time 3, so the correct peak is 2. Sort by `(time, -delta)`, or convert to [1, 4) and [3, 6) first.

## Lab

- **1854 Maximum Population Year.** A difference array over 1950 to 2050; a person is not counted in the year they die, so each life is half-open. Expected: `[[1993, 1999], [2000, 2010]]` gives 1993; `[[1950, 1961], [1960, 1971], [1970, 1981]]` gives 1960, the earliest year with the maximum; O(n + 101).
- **2406 Divide Intervals Into Minimum Number of Groups.** Here [left, right] is inclusive, so two intervals sharing a point clash: sweep with starts before ends, or convert to [left, right + 1). Expected: `[[5, 10], [6, 8], [1, 5], [2, 3], [1, 10]]` gives 3, and `[[1, 3], [5, 6], [8, 10], [11, 13]]` gives 1; O(n log n). The next card explains why the number of groups equals the peak.

> [!know]
> You now know how to find the busiest moment with a +1/-1 sweep, break ties to match the endpoint convention, and when a difference array or two bisects are simpler.

=== primer | How many rooms do you need, and which room gets each meeting? | 14 min
goal: Assign meetings to the fewest rooms with a heap of end times, prove that the count equals the peak overlap, and hand out room numbers
tag: intervals-rooms | Rooms with a heap of end times
link: Kleinberg and Tardos slides: Greedy Algorithms I (PDF) | https://www.cs.princeton.edu/~wayne/kleinberg-tardos/pdf/04GreedyAlgorithmsI.pdf | 10 min: the 'Interval partitioning' slides, PDF pages 17 to 23: earliest-start-time-first, the depth lower bound, and the proof that the greedy uses exactly depth classrooms (a large file, about 9 MB)
practice: 2406, cses:1164

> [!key]
> Sort meetings by start and keep a **min-heap of the end times** of rooms in use. For each meeting, if the room that frees up earliest is free by the meeting's start, reuse it (replace its end time); otherwise open a new room. The number of rooms opened equals the **maximum overlap**: no schedule can use fewer, because when the last room was opened every room was busy, and the greedy never opens a room it does not need. Store (end, room) pairs to report which room each meeting gets.

## Intuition

A hotel front desk at check-in time: the clerk only needs to know which occupied room is vacated soonest. If that guest has already left, the newcomer takes the room. If not, nobody else has left either, so a new room is needed.

## How it works

1. Sort meetings by start.
2. For each meeting [s, e): if the smallest end time in the heap is <= s, that room is free: `heapreplace(ends, e)`. Otherwise `heappush(ends, e)` opens a new room.
3. Reuse pops one end and pushes one, so the heap never shrinks: its final size is the number of rooms.

### Why it is optimal

- **No schedule can do better.** Suppose the greedy opens its kth room for a meeting that starts at s. At that moment the other k - 1 rooms are all busy: each holds a meeting that started at or before s (meetings come in start order) and ends after s (otherwise the earliest end would be <= s). Together with the new meeting, k meetings contain the point s, so any valid schedule needs at least k rooms.
- **The greedy is valid.** It reuses a room only after that room's last meeting has ended, so no room ever holds two overlapping meetings.

So the number of rooms is exactly the maximum overlap, the answer of the sweep in the previous card. For the count alone the two are interchangeable; the heap also produces an assignment and works online, meeting by meeting in start order.

### Room numbers

Keep (end, room) pairs in the heap: reusing pops a pair and hands its room number to the new meeting. If the rules ask for "the lowest-numbered free room", add a second heap of free room numbers: before each meeting, move every room whose end is <= s from the busy heap to the free heap, then take the smallest free number.

### Why start order

The proof needs every meeting already placed to have started by s. Process meetings in order of end instead and the greedy can waste a room: for [0, 1), [0, 2), [2, 3), [1, 4) in end order it opens three rooms, while two suffice ([0, 1) then [1, 4) in one room, [0, 2) then [2, 3) in the other).

## Cost

O(n log n) to sort, plus n heap operations on a heap of at most k rooms: O(n log k). Memory O(k), plus the assignment if you keep one.

## When to use it

Cues: "minimum number of rooms, platforms, machines, groups or colours", "assign each to a resource", "no two in the same group may overlap", "servers become free at different times".

Sweep or heap? Use the sweep when you only need the number, and the heap when you need the assignment or receive meetings one at a time in start order.

The lower bound is useful far beyond puzzles: whatever the scheduler, a set of jobs with fixed start and end times can never run on fewer machines than their peak concurrency, so the peak is the capacity to provision.

## Worked trace

Five meetings, half-open, already in start order:

```steps
Meetings sorted by start. busy is a min-heap of (end, room) for rooms in use, shown sorted
    meetings (0, 30)  (5, 10)  (10, 25)  (15, 20)  (25, 35)
    busy     []
---
(0, 30): no rooms yet: open room 0
    busy     [(30, 0)]   rooms opened 1
---
(5, 10): earliest end 30 > 5, every room is busy: open room 1
    busy     [(10, 1), (30, 0)]   rooms opened 2
---
(10, 25): earliest end 10 <= 10, so room 1 is free again: reuse it
    busy     [(25, 1), (30, 0)]   rooms opened 2
---
(15, 20): earliest end 25 > 15, every room is busy: open room 2
    busy     [(20, 2), (25, 1), (30, 0)]   rooms opened 3
---
(25, 35): earliest end 20 <= 25, so room 2 is free again: reuse it. Answer: 3 rooms
    busy     [(25, 1), (30, 0), (35, 2)]   rooms opened 3
```

## Template

```python
import heapq


def min_rooms(meetings):
    """Fewest rooms for half-open meetings [s, e): O(n log n)."""
    ends = []                                  # end times of the rooms in use
    for s, e in sorted(meetings):
        if ends and ends[0] <= s:              # the earliest-finishing room is free again
            heapq.heapreplace(ends, e)
        else:
            heapq.heappush(ends, e)            # every room is busy: open a new one
    return len(ends)


def assign_rooms(meetings):
    """Room numbers 0, 1, ... for half-open meetings, using the fewest rooms.
    Returns (rooms used, room of each meeting in input order)."""
    order = sorted(range(len(meetings)), key=lambda i: meetings[i])
    busy, room, rooms = [], [0] * len(meetings), 0     # busy: heap of (end, room)
    for i in order:
        s, e = meetings[i]
        if busy and busy[0][0] <= s:
            _, r = heapq.heappop(busy)         # reuse the room that freed up first
        else:
            r, rooms = rooms, rooms + 1
        room[i] = r
        heapq.heappush(busy, (e, r))
    return rooms, room
```

## Pitfalls

- **Sorting by end.** As shown above, the greedy can then open more rooms than necessary.
- **`<` versus `<=`.** Half-open meetings can reuse a room that frees at exactly their start (`ends[0] <= s`). Inclusive intervals, like LeetCode 2406's, need `ends[0] < s`.
- **Reading the heap size at the wrong moment.** If you pop every finished room before pushing, the heap shrinks, and its final size is the number of rooms busy at the end, not the peak. Track the maximum size, or reuse with `heapreplace` as the template does.
- **"Any free room" versus "the lowest-numbered free room".** The second needs the extra heap of free room numbers.

## Check yourself

Q: Meetings [0, 30), [5, 10) and [15, 20). How many rooms does the template open, and why is that optimal?
A: Two. [0, 30) opens room 0; for [5, 10) the earliest end is 30 > 5, so room 1 opens; for [15, 20) the earliest end is 10 <= 15, so room 1 is reused. Two is optimal because [0, 30) and [5, 10) both contain time 5.

Q: Prove in two sentences that no schedule can use fewer rooms than the greedy.
A: When the greedy opens its kth room at time s, each of the other k - 1 rooms holds a meeting that started by s and has not ended at s. So k meetings contain the point s, and any schedule needs k rooms at that instant.

Q: A colleague pops every finished room (`while ends and ends[0] <= s: heappop(ends)`), pushes e, and returns `len(ends)` at the end. What is wrong?
A: The heap now shrinks, so its final size counts only the rooms busy after the last meeting starts, not the most ever needed. Keep `best = max(best, len(ends))` after each push and return best, or reuse with `heapreplace` so the size never drops.

## Lab

- **2406 Divide Intervals Into Minimum Number of Groups.** The rooms greedy with inclusive intervals: reuse a group only if its last right end is strictly less than the new left end. Expected: `[[5, 10], [6, 8], [1, 5], [2, 3], [1, 10]]` gives 3 and `[[1, 3], [5, 6], [8, 10], [11, 13]]` gives 1; O(n log n).
- **CSES 1164 Room Allocation (stretch).** Print the number of rooms and a room for every customer, in input order; arrival and departure days are inclusive, so a room is free for a customer arriving the day after the previous guest leaves. Expected: customers (1, 2), (2, 4) and (4, 4) need 2 rooms, assigned 1 2 1 (any valid assignment is accepted); O(n log n) for n up to 2 · 10^5.

> [!know]
> You now know how to count and assign rooms with a heap of end times, and why the count always equals the peak overlap.

=== primer | Why does picking the earliest end give the most non-overlapping intervals? | 15 min
goal: Select a largest set of non-overlapping intervals by earliest end, prove it with an exchange argument, and reuse it for fewest removals and fewest stabbing points
tag: intervals-select | Earliest end first
link: Jeff Erickson: Algorithms, chapter 4, Greedy Algorithms (PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/04-greedy.pdf | 15 min: the section 'Scheduling Classes' (PDF pages 3 to 6): the same greedy, why other rules fail, and the exchange proof written out in full; then 'General Pattern' on page 6
link: USACO Guide: Greedy with sorting, the scheduling problem | https://usaco.guide/silver/greedy-sorting#example---the-scheduling-problem | 5 min: why 'earliest start' fails and 'earliest end' works, with code
practice: 435, 452

> [!key]
> To keep the most intervals with no two overlapping, sort by **end** and take each interval that starts at or after the end of the last one taken. Finishing first leaves the most room for everything else, and the **exchange argument** makes that precise: any optimal answer can swap its first interval for the earliest-ending one without losing anything, and induction does the rest. The same greedy gives the fewest removals (n minus the number kept) and the fewest points that stab every interval.

## Intuition

To fit the most appointments into a day, always book the one that frees you soonest. Starting early does not help if the appointment runs all day, and being short does not help if it sits across two others. All that matters for the rest of the day is when you are free again.

## How it works

1. Sort by end.
2. Set last_end to minus infinity. For each interval: if its start is >= last_end (half-open, so touching is fine), take it and set last_end to its end; otherwise skip it.

### Rules that look right and fail

| Rule | Counterexample (half-open) | That rule keeps | Best |
|---|---|---|---|
| earliest start | [0, 10), [1, 2), [3, 4) | 1: [0, 10) blocks both | 2 |
| shortest first | [0, 5), [4, 7), [6, 10) | 1: [4, 7) clashes with both | 2 |

Earliest end gets 2 on both examples.

### The exchange argument

Let g be the interval with the earliest end. Take any optimal solution O and list its intervals by end: o1, o2, ..., ok.

1. **Exchange.** g ends no later than any interval, so end(g) <= end(o1). Replace o1 with g. Every other interval of O starts at or after end(o1), which is >= end(g), so none of them overlaps g. The result is still valid and still has k intervals, so **some optimal solution starts with g**.
2. **Induction.** Remove g and every interval that starts before end(g) (all of them clash with g). What is left is a smaller instance of the same problem. The optimal solution that starts with g, minus g, is a valid solution of it with k - 1 intervals, and by induction the greedy finds an optimal one there. So the greedy's total, g plus its choices on the rest, is k.

An equivalent proof says the greedy **stays ahead**: its ith chosen interval ends no later than the ith interval of any valid selection, so it can never run out of room first.

### Same greedy, other questions

- **Fewest removals so the rest do not overlap:** n minus the most you can keep.
- **Fewest points that stab every interval** (arrows through balloons): sort by end, place a point at the end of the first interval not yet stabbed, skip every interval containing that point, repeat. Each point is placed as late as possible while still hitting the current interval, so it hits every later interval any other choice could. The count equals the most pairwise-disjoint intervals: no point can hit two disjoint intervals, and the intervals that triggered new points are themselves disjoint.

### When greedy is not enough

If intervals carry weights and you maximise the total weight, earliest end can be badly wrong: one long interval worth 100 beats two short ones worth 1 each. That needs dynamic programming over intervals sorted by end, with a binary search for the last compatible interval; the greedy module's lab compares the two.

## Cost

O(n log n) to sort and O(n) to scan, with O(1) extra memory beyond the sort.

## When to use it

Cues: "maximum number of non-overlapping intervals", "minimum number to remove", "fewest points, arrows or checks that hit every interval", "attend as many whole events as possible".

Not: weighted intervals (DP); "minimum number of rooms" (sort by start, the rooms card); choosing one day inside each interval rather than the whole interval (a heap-based variant of this idea).

## Worked trace

Six half-open intervals, sorted by end:

```steps
Sort by end. last = the end of the last chosen interval (none yet)
    time   0  1  2  3  4  5  6  7  8  9  10
    (1, 3)    [=====)
    (2, 5)       [========)
    (4, 6)             [=====)
    (6, 8)                   [=====)
    (5, 9)                [===========)
    (8, 10)                        [=====)
---
(1, 3) ends first of all: take it, last = 3
    time   0  1  2  3  4  5  6  7  8  9  10
    (1, 3)    {{[=====)}}  take
    (2, 5)       [========)
    (4, 6)             [=====)
    (6, 8)                   [=====)
    (5, 9)                [===========)
    (8, 10)                        [=====)
---
(2, 5) starts at 2 < last end 3: it clashes, skip
    time   0  1  2  3  4  5  6  7  8  9  10
    (1, 3)    [=====)  take
    (2, 5)       {{[========)}}  skip
    (4, 6)             [=====)
    (6, 8)                   [=====)
    (5, 9)                [===========)
    (8, 10)                        [=====)
---
(4, 6) starts at 4 >= last end 3: take it, last = 6
    time   0  1  2  3  4  5  6  7  8  9  10
    (1, 3)    [=====)  take
    (2, 5)       [========)  skip
    (4, 6)             {{[=====)}}  take
    (6, 8)                   [=====)
    (5, 9)                [===========)
    (8, 10)                        [=====)
---
(6, 8) starts at 6 >= last end 6: take it, last = 8
    time   0  1  2  3  4  5  6  7  8  9  10
    (1, 3)    [=====)  take
    (2, 5)       [========)  skip
    (4, 6)             [=====)  take
    (6, 8)                   {{[=====)}}  take
    (5, 9)                [===========)
    (8, 10)                        [=====)
---
(5, 9) starts at 5 < last end 8: it clashes, skip
    time   0  1  2  3  4  5  6  7  8  9  10
    (1, 3)    [=====)  take
    (2, 5)       [========)  skip
    (4, 6)             [=====)  take
    (6, 8)                   [=====)  take
    (5, 9)                {{[===========)}}  skip
    (8, 10)                        [=====)
---
(8, 10) starts at 8 >= last end 8: take it, last = 10. Chosen: 4 intervals
    time   0  1  2  3  4  5  6  7  8  9  10
    (1, 3)    [=====)  take
    (2, 5)       [========)  skip
    (4, 6)             [=====)  take
    (6, 8)                   [=====)  take
    (5, 9)                [===========)  skip
    (8, 10)                        {{[=====)}}  take
```

## Template

```python
def max_non_overlapping(intervals):
    """A largest set of pairwise disjoint half-open intervals, by earliest end: O(n log n)."""
    chosen, last_end = [], float("-inf")
    for s, e in sorted(intervals, key=lambda iv: iv[1]):
        if s >= last_end:                      # compatible with everything chosen so far
            chosen.append((s, e))
            last_end = e
    return chosen
```

## Pitfalls

- **Sorting by start and taking whatever fits:** the earliest-start rule, which fails as shown. (Sorting by start does work if, on a clash, you keep whichever of the two ends earlier; that is the same greedy in disguise.)
- **Touching.** Half-open intervals (LeetCode 435) may touch: `s >= last_end`. For closed intervals, such as balloons where an arrow at x hits [s, e] when s <= x <= e, a new arrow is needed only when `s > arrow`.
- **A sentinel that is not small enough.** Starting last_end at 0 breaks when coordinates are negative (balloon coordinates go down to -2^31); use minus infinity or the first interval.
- **Weighted versions.** The greedy is only correct when every interval counts the same.

## Check yourself

Q: Run the greedy on [1, 4), [3, 5), [0, 6), [5, 7), [3, 9), [5, 9), [6, 10), [8, 11), [8, 12), [2, 14), [12, 16), which are already sorted by end. Which intervals are taken?
A: Take [1, 4). [3, 5) and [0, 6) start before 4: skip. Take [5, 7). [3, 9), [5, 9) and [6, 10) start before 7: skip. Take [8, 11). [8, 12) and [2, 14) start before 11: skip. Take [12, 16). Four intervals: [1, 4), [5, 7), [8, 11), [12, 16).

Q: In the exchange step, why does replacing o1 with g create no overlap?
A: g ends no later than o1, because it has the earliest end of all intervals, and every other interval of the optimal solution starts at or after o1's end. So they all start at or after g's end and cannot overlap g.

Q: Show with three intervals that "shortest first" can fail.
A: [0, 5), [4, 7) and [6, 10). The shortest, [4, 7), overlaps both others, so shortest-first keeps one interval, while [0, 5) and [6, 10) together give two. Earliest end takes [0, 5), skips [4, 7), takes [6, 10).

## Lab

- **435 Non-overlapping Intervals (derive it).** The fewest removals is n minus the most you can keep, and touching intervals may stay together. Expected: `[[1, 2], [2, 3], [3, 4], [1, 3]]` gives 1; `[[1, 2], [1, 2], [1, 2]]` gives 2; `[[1, 2], [2, 3]]` gives 0; O(n log n).
- **452 Minimum Number of Arrows to Burst Balloons.** Sort by end, shoot at the end of the current balloon, and fire a new arrow only when a balloon starts strictly after the current arrow. Expected: `[[10, 16], [2, 8], [1, 6], [7, 12]]` gives 2; `[[1, 2], [3, 4], [5, 6], [7, 8]]` gives 4; `[[1, 2], [2, 3], [3, 4], [4, 5]]` gives 2.

> [!know]
> You now know how to pick the most non-overlapping intervals by earliest end, prove it with an exchange argument, and reuse it for removals and stabbing points.

=== primer | How do you answer many point queries against many intervals at once? | 15 min
goal: Answer point queries offline by sorting the queries and sweeping, with a heap of active intervals keyed by what each query asks for, and know the online alternatives
tag: intervals-offline | Offline queries with a sweep and a heap
link: Linux kernel docs: Red-black trees, support for augmented rbtrees | https://docs.kernel.org/core-api/rbtree.html#support-for-augmented-rbtrees | 5 min: 'Support for augmented rbtrees' and its 'Sample usage', an interval tree whose nodes store the largest end in their subtree: the online structure for the same queries
practice: 1851, 218

> [!key]
> When every query is known in advance, answer them in **sorted order** instead of the order given. Sweep the query points from left to right: push an interval onto a heap when the sweep reaches its start, and lazily drop it from the top once the sweep has passed its end. Key the heap by whatever the query asks for (shortest length, greatest height), so after cleaning, the top is the answer. Keep each query's original index to put the answers back in order. Cost: O((n + q) log n + q log q) instead of O(n q).

## Intuition

You have a list of house numbers to check on a long street at night, and each streetlight covers a stretch of houses. Walking from the top of the street for every house on your list wastes most of the walking. Sort your list and walk once: lights come into range as you pass their first house and fall out of range after their last one, and at each house on your list you look at what is lit.

## How it works

1. Sort the intervals by start. Sort the query **indices** by query value.
2. Keep a pointer i into the intervals and a heap of active candidates keyed by the answer's criterion, for example (length, end).
3. For each query q in sorted order:
   - push every interval with start <= q (advance i);
   - pop from the top while the top's end < q (it has ended);
   - the top, if any, answers q; store it at the query's original index.

**Why lazy removal is safe.** Queries arrive in increasing order, so an interval that ended before q has also ended before every later query; once popped it is never needed again. Ended intervals buried below the top do no harm, because only the top is ever read, and they are popped if they surface. Each interval is pushed once and popped at most once.

### The skyline is the same sweep

The outline of overlapping buildings changes only at building edges. Sweep the edge x-coordinates in order with a max-heap of (height, right edge) for the active buildings: push buildings whose left edge is <= x, pop tops whose right edge is <= x, and the current height is the top's height, or 0 if the heap is empty. Emit a key point whenever that height changes. The three moves are the same: add at the start, expire lazily at the end, read the top.

### Counting instead of choosing

If a query only asks how many intervals contain it, no heap is needed: with the starts and the ends each sorted, the count for closed intervals is (number of starts <= q) - (number of ends < q), two bisects per query (the sweep card's `active_at` is the half-open version).

### Online alternatives

When queries arrive one at a time, interleaved with insertions and deletions, you cannot sort them first. Use an **interval tree**: a balanced search tree ordered by start in which every node also stores the largest end in its subtree, so a search can skip any subtree that ends too early. The Linux kernel provides a generic interval tree built this way on its augmented red-black trees. A segment tree over compressed coordinates (the range-query module) is the other standard answer.

## Cost

Sorting the intervals is O(n log n) and the queries O(q log q); at most n pushes and n pops cost O(n log n), and q peeks O(q). In total O((n + q) log n + q log q) time and O(n + q) memory. Checking every interval against every query is O(n q): 10^10 steps for n = q = 10^5.

## When to use it

Cues: "for each query point or time, find the smallest, largest or number of intervals containing it", many queries, all of them given up front; outlines, and "at each position, the tallest active".

Not: queries that arrive online mixed with updates (interval tree or segment tree); a single query (just scan).

## Worked trace

Intervals [1, 4], [2, 4], [3, 6] and [4, 4] (closed), queries 2, 3, 4 and 5; the answer is the size r - l + 1 of the smallest interval containing the query:

```steps
Intervals sorted by left end; queries visited in increasing order. Heap entries are (size, right, left), shown sorted
    intervals [[1, 4], [2, 4], [3, 6], [4, 4]]
    queries   [2, 3, 4, 5]
---
q = 2: push [1, 4], [2, 4]; the top fits, answer 3
    heap [(3, 4, 2), (4, 4, 1)]
    answers {2: 3}
---
q = 3: push [3, 6]; the top fits, answer 3
    heap [(3, 4, 2), (4, 4, 1), (4, 6, 3)]
    answers {2: 3, 3: 3}
---
q = 4: push [4, 4]; the top fits, answer 1
    heap [(1, 4, 4), (3, 4, 2), (4, 4, 1), (4, 6, 3)]
    answers {2: 3, 3: 3, 4: 1}
---
q = 5: pop (1, 4, 4), (3, 4, 2), (4, 4, 1) (right end < q); the top fits, answer 4
    heap [(4, 6, 3)]
    answers {2: 3, 3: 3, 4: 1, 5: 4}
```

## Template

```python
import heapq


def best_containing(intervals, queries, key):
    """For each query point q, the closed interval (l, r) with l <= q <= r that minimises
    key(l, r), or None. Offline sweep: O((n + m) log n + m log m)."""
    intervals = sorted(intervals)
    answer = [None] * len(queries)
    heap, i = [], 0                            # heap of (key, r, l): intervals with l <= q
    for qi in sorted(range(len(queries)), key=queries.__getitem__):
        q = queries[qi]
        while i < len(intervals) and intervals[i][0] <= q:
            l, r = intervals[i]
            heapq.heappush(heap, (key(l, r), r, l))
            i += 1
        while heap and heap[0][1] < q:         # ended before q, so before every later query too
            heapq.heappop(heap)
        if heap:
            _, r, l = heap[0]
            answer[qi] = (l, r)
    return answer
```

For a "largest" criterion, negate the key: `key=lambda l, r: -height_of(l, r)`.

## Pitfalls

- **Losing the original order.** Sort indices, not values, and write each answer at its query's index.
- **The expiry test.** A closed [l, r] contains q when l <= q <= r, so expire when r < q; a half-open [l, r) expires when r <= q.
- **Popping only one expired entry.** Several may sit on top; use `while`.
- **Pushing by end order.** Intervals must enter by start, or ones that have not begun yet sit in the heap and can be reported.
- **Duplicate query values.** Harmless: they get the same answer.

## Check yourself

Q: In the trace, why is [1, 4] still in the heap at q = 4 even though it is not the answer?
A: It contains 4 (1 <= 4 <= 4), so it has not expired; it is simply not the shortest. [4, 4], of size 1, is on top. At q = 5 it has ended, and it is popped along with the other expired entries.

Q: Why can an interval popped as expired never be needed again?
A: It was popped because its right end is smaller than the current query, and every later query is at least as large, so it can never contain one of them.

Q: Users send queries one at a time, and new intervals are added between queries. Does this card's method still work?
A: No: it relies on processing all the queries in sorted order after seeing them. Use an online structure: an interval tree, or a segment tree over compressed coordinates.

## Lab

- **1851 Minimum Interval to Include Each Query (derive it).** Key the heap on the size r - l + 1 and answer -1 when the heap is empty after cleaning. Expected: intervals `[[1, 4], [2, 4], [3, 6], [4, 4]]` with queries `[2, 3, 4, 5]` give `[3, 3, 1, 4]`; intervals `[[2, 3], [2, 5], [1, 8], [20, 25]]` with queries `[2, 19, 5, 22]` give `[2, -1, 4, 6]`; O((n + q) log n + q log q).
- **218 The Skyline Problem (stretch).** Sweep the building edges with a max-heap of (-height, right edge), expire tops whose right edge is <= x, and emit [x, height] whenever the height changes. Expected: `[[2, 9, 10], [3, 7, 15], [5, 12, 12], [15, 20, 10], [19, 24, 8]]` gives `[[2, 10], [3, 15], [7, 12], [12, 0], [15, 10], [20, 8], [24, 0]]`; `[[0, 2, 3], [2, 5, 3]]` gives `[[0, 3], [5, 0]]`; O(n log n).

> [!know]
> You now know how to answer many point queries in one sorted sweep with a lazily cleaned heap, and when an interval tree is needed instead.

=== primer | Which sort order does an interval problem need, and where do sweeps run in production? | 14 min
goal: Match an interval question to its sort key and the state to carry, avoid the common near-misses, find common free time for a group, and recognise the same sweeps in calendars, databases, genome tools and kernels
tag: intervals-gaps | Free slots from busy intervals
link: RFC 5545 (iCalendar): Free/Busy Component | https://www.rfc-editor.org/rfc/rfc5545#section-3.6.4 | 5 min: section 3.6.4, the VFREEBUSY component and its FREEBUSY periods, the format calendar servers use to publish busy time that a scheduler then merges

> [!key]
> Most interval questions are answered by sorting once and sweeping once; what changes is the **sort key** and the **state** you carry. Union, gaps and free time: sort by start, carry the furthest end. Peak overlap: sort the +1/-1 events, carry a counter. Assigning rooms: sort by start, carry a heap of end times. Most non-overlapping, fewest stabbing points: sort by end, carry the last end. Point queries: sort the queries too, carry a heap of active intervals. Production systems run the same sweeps: calendar servers merge busy time, PostgreSQL refuses overlapping ranges, genome tools merge sorted features, and kernels keep interval trees when the set never stops changing.

## Intuition

Before writing code, ask what the answer depends on. If it depends on where covered stretches begin and end, you need the starts in order. If it depends on how many intervals are active at once, you need every start and end in time order. If it depends on leaving room for later intervals, you need the ends in order. The question picks the order, and the order picks the algorithm.

## How it works

### The decision table

| The question asks | Sort by | Carry | Card | Cost |
|---|---|---|---|---|
| do two intervals overlap; their intersection | nothing | an O(1) test | overlap | O(1) |
| union, merged blocks, covered length, gaps, free time | start | the furthest end so far | merge, and this card | O(n log n) |
| add or remove a range in a disjoint set | kept sorted | bisect positions | insert | O(log n + k) |
| how many at once; the peak | events (time, delta) | a counter | sweep | O(n log n) |
| fewest rooms, and who goes where | start | a heap of end times | rooms | O(n log n) |
| most non-overlapping, fewest removals, fewest stabbing points | end | the last chosen end | select | O(n log n) |
| for each query point, the best or the number of containing intervals | start, and the queries | a heap of active intervals, or two bisects | offline | O((n + q) log n) |
| the most total weight of non-overlapping intervals | end | DP plus binary search | greedy and DP modules | O(n log n) |

### Near-misses

- **Merge or count?** Merging throws away multiplicity, so a peak-load question cannot be answered from merged blocks.
- **Most non-overlapping or fewest rooms?** The first sorts by end and discards intervals; the second sorts by start and keeps every interval, just in different rooms.
- **Fewest arrows or fewest rooms?** Arrows are points that may hit many intervals at once (sort by end); rooms hold intervals that must not overlap (sort by start). Their answers are different numbers.
- **The endpoint convention** decides every tie: read whether touching counts before choosing `<` or `<=`.

### Free time for a group

Pool everyone's busy intervals, sort them by start, and walk them with a **cursor**: the furthest end seen so far. Whenever the next busy interval starts after the cursor, the stretch from the cursor to that start is free for everyone. This is merging without building the merged list: the cursor carries all the merged blocks need to tell you.

### In production

- **Calendars.** iCalendar's VFREEBUSY component publishes a person's busy periods as FREEBUSY values. Finding a slot for a meeting is the free-time sweep above: pool the periods, walk them with a cursor, and keep the gaps that are long enough.
- **Databases.** PostgreSQL range types record whether each bound is inclusive or exclusive, and discrete ranges are normalised to [lower, upper). An exclusion constraint such as `EXCLUDE USING GIST (room WITH =, during WITH &&)` makes the database itself refuse an overlapping booking, with a GiST index finding the candidates.
- **Genomics.** `bedtools merge` collapses overlapping features in a BED file sorted by chromosome and start: the merge pass at genome scale, streamed because the input is pre-sorted.
- **Kernels.** When intervals are inserted and removed all the time and overlap queries must stay fast, Linux uses interval trees built on augmented red-black trees rather than a one-off sweep.

## Cost

Every row of the table is dominated by one sort, O(n log n), followed by a linear pass with O(1) or O(log n) work per item. When the input already arrives sorted, as in time-ordered logs and sorted BED files, the sort disappears and most of these become one streaming pass with very little memory. The free-time sweep is O(n log n) for n busy intervals across all people, however many people there are.

## When to use it

Use the table at the start of every interval problem: name the question, then the sort key, then the state. Intervals hide in time ranges ("sessions", "bookings", "leases", "shifts"), in positions ("genome features", "byte ranges", "IP ranges") and in geometry (segments on a line).

## Worked trace

Alice is busy 09:00-10:00 and 12:00-13:00, Bob 09:30-11:00 and 15:00-16:00, Cara 13:00-14:30. Find slots of at least 30 minutes between 09:00 and 17:00 when all three are free:

```steps
Pool everyone's busy slots and sort by start. cursor = 09:00, the start of the working day
    busy   09:00-10:00  09:30-11:00  12:00-13:00  13:00-14:30  15:00-16:00
    cursor 09:00   free (none yet)
---
09:00-10:00 starts at or before the cursor 09:00: no gap. cursor = max(09:00, 10:00) = 10:00
    busy   {{09:00-10:00}}  09:30-11:00  12:00-13:00  13:00-14:30  15:00-16:00
    cursor 10:00   free (none yet)
---
09:30-11:00 starts at or before the cursor 10:00: no gap. cursor = max(10:00, 11:00) = 11:00
    busy   09:00-10:00  {{09:30-11:00}}  12:00-13:00  13:00-14:30  15:00-16:00
    cursor 11:00   free (none yet)
---
12:00-13:00 starts after the cursor 11:00: 11:00-12:00 is free for everyone. cursor = max(11:00, 13:00) = 13:00
    busy   09:00-10:00  09:30-11:00  {{12:00-13:00}}  13:00-14:30  15:00-16:00
    cursor 13:00   free 11:00-12:00
---
13:00-14:30 starts at or before the cursor 13:00: no gap. cursor = max(13:00, 14:30) = 14:30
    busy   09:00-10:00  09:30-11:00  12:00-13:00  {{13:00-14:30}}  15:00-16:00
    cursor 14:30   free 11:00-12:00
---
15:00-16:00 starts after the cursor 14:30: 14:30-15:00 is free for everyone. cursor = max(14:30, 16:00) = 16:00
    busy   09:00-10:00  09:30-11:00  12:00-13:00  13:00-14:30  {{15:00-16:00}}
    cursor 16:00   free 11:00-12:00, 14:30-15:00
---
After the last block, 16:00-17:00 is free until the day ends. Keep slots of at least 30 minutes
    free   11:00-12:00, 14:30-15:00, 16:00-17:00
```

## Template

```python
def free_slots(calendars, day_start, day_end, min_len=1):
    """Half-open slots of at least min_len inside [day_start, day_end) when everyone is free.
    calendars: one list of half-open busy intervals per person. O(n log n)."""
    busy = sorted(iv for cal in calendars for iv in cal)
    free, cursor = [], day_start               # cursor: everything before it is busy or past
    for s, e in busy:
        if cursor >= day_end:
            break
        if s > cursor:
            free.append((cursor, min(s, day_end)))
        cursor = max(cursor, e)
    if cursor < day_end:
        free.append((cursor, day_end))
    return [(a, b) for a, b in free if b - a >= min_len]
```

## Pitfalls

- **Choosing by the problem's title.** "Meeting rooms" can ask for a peak count, an assignment or a selection; read the question, not the story.
- **Local times across time zones or daylight-saving changes.** Convert to UTC timestamps (integers) before sweeping.
- **Intersecting free time pairwise.** Computing each person's free time and intersecting pairs is more code and more work; pooling every busy interval into one sweep is simpler.
- **Forgetting the edges of the day.** Time before the first busy interval and after the last one counts, and busy intervals that start before or end after the working day must be clipped.

## Check yourself

Q: Which sort key and state does each question need? (a) The total hours a server was under any load. (b) The largest number of simultaneous logins. (c) The most talks one person can attend in full.
A: (a) Sort by start and carry the furthest end (merge), adding block lengths; or sweep the events and add elapsed time while the counter is positive. (b) Sort the +1/-1 events and carry a counter, with ends before starts at equal times for half-open sessions. (c) Sort by end and carry the last chosen end: earliest end first.

Q: Why can the free-slot template skip building a merged list?
A: After sorting by start, the merged blocks are only needed to know where covered time currently ends, and the cursor, the furthest end seen so far, holds exactly that. A gap exists precisely when the next busy interval starts after the cursor.

Q: A booking service checks for conflicts with bisect before inserting, and runs on two servers. Why can it still double-book a room, and what does PostgreSQL offer?
A: Both servers can check at the same moment, each see no conflict, and both insert: a race between the check and the write. An exclusion constraint makes the database enforce non-overlap atomically on insert, using a GiST index on the range column, so one of the two inserts fails.

## Lab

- **Free slots for a team.** Run the template on the trace's calendars in minutes since midnight. Expected: 11:00-12:00, 14:30-15:00 and 16:00-17:00 with a 30-minute minimum; only 11:00-12:00 and 16:00-17:00 with a 45-minute minimum.
- **Classify before you code.** Name the sort key and the state for each, then check against the table: (1) the fewest TV channels needed to broadcast programmes whose times may overlap; (2) the total length of road covered by at least one roadworks zone; (3) the number of visitors present at each of 10^5 query times. Expected: (1) sort by start with a heap of end times (rooms); (2) sort by start and merge, adding block lengths, or a +1/-1 sweep adding length while the count is positive; (3) sort the starts and the ends separately and answer each time with two bisects, or sort the queries and sweep.

> [!know]
> You now know how to pick the sort key and state for any interval question, find free time for a group, and recognise these sweeps in real calendars, databases, genome tools and kernels.

=== lab | Calendar sweeps: peak load, rooms and free time for 50,000 bookings | 45 min
goal: Run the sweep, the difference array and the rooms heap on a week of 50,000 bookings, check every answer against a brute force over time steps, and see which costs depend on the time resolution
link: USACO Guide: Sweep Line, Restaurant Customers | https://usaco.guide/plat/sweep-line#restaurant-customers | 5 min: the same peak-count sweep on the CSES version of the problem, with a short C++ and Java implementation to compare with yours

You will generate a week of random bookings, compute the peak number of simultaneous bookings three ways, assign every booking to a room and prove no room is double-booked, find common free time for a small team, and check everything against the slowest possible oracle: marking every minute. Then you will plant a tie-break bug and watch the oracle catch it.

## Setup

- Python 3.10 or later, standard library only.
- Put your templates from this module into `intervals_kit.py`: at least `max_overlap`, `busiest_time`, `min_rooms`, `assign_rooms` and `free_slots`, with their imports (`heapq`, `bisect`).

## Steps

1. Save this as `calendar_lab.py` next to `intervals_kit.py`:

```python
import random
import sys
import time
from collections import defaultdict

from intervals_kit import assign_rooms, busiest_time, free_slots, max_overlap, min_rooms

SCALE = int(sys.argv[1]) if len(sys.argv) > 1 else 1   # 1: minutes; 60: seconds (step 5)
WEEK = 7 * 24 * 60 * SCALE                              # time steps in a week


def bookings(n, seed=1):
    """n random half-open bookings [start, end), 15 to 120 minutes long, in units of 1 / SCALE minutes."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        dur = 15 * rng.randint(1, 8)
        start = rng.randrange(0, 7 * 24 * 60 - dur)
        out.append((start * SCALE, (start + dur) * SCALE))
    return out


def peak_brute(books):
    """Oracle: add 1 to every time step of every booking."""
    load = [0] * WEEK
    for s, e in books:
        for t in range(s, e):
            load[t] += 1
    return max(load)


def timed(label, fn):
    t = time.perf_counter()
    result = fn()
    print(f"{label:<26} {1000 * (time.perf_counter() - t):8.1f} ms   -> {result}")
    return result


books = bookings(50_000)
peak = timed("peak: sweep", lambda: max_overlap(books))
timed("peak: difference array", lambda: busiest_time(books, 0, WEEK)[0])
if SCALE == 1:
    assert timed("peak: every time step", lambda: peak_brute(books)) == peak
rooms = timed("rooms: heap of end times", lambda: min_rooms(books))
assert rooms == peak

used, room = assign_rooms(books)
by_room = defaultdict(list)
for (s, e), r in zip(books, room):
    by_room[r].append((s, e))
for r, bs in by_room.items():
    bs.sort()
    assert all(a[1] <= b[0] for a, b in zip(bs, bs[1:])), f"room {r} is double-booked"
print(f"assigned {len(books)} bookings to {used} rooms; no room is double-booked")


def team_calendars(people, meetings, seed=2):
    """Each person gets random meetings inside working hours, 09:00-17:00, Monday to Friday."""
    rng = random.Random(seed)
    cals = []
    for _ in range(people):
        cal = []
        for _ in range(meetings):
            day = rng.randrange(5)
            dur = 15 * rng.randint(2, 6)
            start = day * 1440 + 9 * 60 + 15 * rng.randrange((8 * 60 - dur) // 15 + 1)
            cal.append((start, start + dur))
        cals.append(cal)
    return cals


if SCALE == 1:
    cals = team_calendars(people=5, meetings=10)
    slots = []
    for day in range(5):
        slots += free_slots(cals, day * 1440 + 9 * 60, day * 1440 + 17 * 60, min_len=30)
    busy = {t for cal in cals for s, e in cal for t in range(s, e)}
    grid = []                                           # oracle: walk every working minute
    for day in range(5):
        t, end = day * 1440 + 9 * 60, day * 1440 + 17 * 60
        while t < end:
            u = t
            while u < end and u not in busy:
                u += 1
            if u - t >= 30:
                grid.append((t, u))
            t = u + 1 if u == t else u
    assert slots == grid
    hm = lambda m: f"{m % 1440 // 60:02d}:{m % 60:02d}"
    print(f"{len(slots)} common free slots of 30+ minutes, {sum(e - s for s, e in slots)} minutes in all;",
          "Monday:", [f"{hm(s)}-{hm(e)}" for s, e in slots if s < 1440])
```

2. Run `python calendar_lab.py`. Every `assert` compares a fast method with a slow, obviously correct one; if one fails, shrink the number of bookings until the failing case is small enough to trace by hand.
3. **Plant the tie-break bug.** In your `max_overlap`, sort the events with `events.sort(key=lambda ev: (ev[0], -ev[1]))`, so starts come before ends at equal times. Run again and note what the oracle says. Restore the correct order.
4. **Plant the rooms bug.** In `min_rooms`, sort the meetings by end instead of start. Does the oracle catch it on this data? Then try the four meetings [0, 1), [0, 2), [2, 3), [1, 4).
5. **Change the resolution.** Run `python calendar_lab.py 60`: the same bookings in seconds. The script skips the per-second oracle; estimate its cost by timing `peak_brute` on the first 5,000 bookings and multiplying by 10.
6. **Extend the sweep.** Add a function that returns the number of minutes during which at least 380 bookings are active: sweep the sorted events and add (time - previous time) while the count is >= 380. Check it against the oracle's `load` array.

## What you should see

Measured with CPython 3.12 on a busy shared server; your timings will differ, but the shape should not.

- Step 2: the peak is 403 simultaneous bookings, found by all three methods, and the rooms heap opens exactly 403 rooms with none double-booked. The sweep takes roughly 0.2 to 0.3 s, the difference array 10 to 30 ms (only 10,080 minutes to scan), marking every minute 0.4 to 0.5 s, and the rooms heap 0.06 to 0.2 s. The team of five has 8 common free slots of at least 30 minutes, 600 minutes in all, and on Monday only 14:45-17:00.
- Step 3: the buggy sweep reports 406, and the assertion against the oracle fails: with bookings on a 15-minute grid, many end exactly when others start.
- Step 4: sorted by end, the greedy opens 663 rooms instead of 403, and the assertion `rooms == peak` fails at once; on the four meetings it opens 3 rooms where 2 suffice.
- Step 5: in seconds the answer is still 403 and the sweep's time barely changes, the difference array grows to about 0.1 to 0.15 s (604,800 steps), and the per-second oracle would take tens of seconds (about 5 s for 5,000 bookings here). The sweep's cost depends only on the number of bookings; the other two depend on the resolution.
- Step 6: 105 minutes of the week have at least 380 bookings active, from both the sweep and the oracle.

## Check yourself

Q: In step 2 the rooms heap was usually faster than the sweep, although both are O(n log n). Why?
A: Constants. The sweep builds and sorts 100,000 event tuples and runs a Python loop with a `max` call per event; the rooms heap sorts 50,000 tuples and does most of its per-meeting work inside heapq's C functions. Big-O tells you how each grows, not which is faster at a given size, so measure.

> [!know]
> You now know how to check interval sweeps against a brute-force oracle, catch tie-break and sort-order bugs with it, and predict which methods depend on the time resolution.

=== practice
- 2848 core
  cue: Several closed ranges of integer positions on a short line; count the positions covered by at least one of them.
  hint: Adding up the lengths counts shared positions more than once. How can you make the ranges disjoint first?
  insight: Sort by start and merge overlapping ranges, then add e - s + 1 for each merged block. With coordinates only up to 100, a difference array or a set of covered points also works.
  cost: O(n log n) time, O(n) space
  pattern: intervals-merge
- 1854 core
  cue: Birth and death years for many people; find the earliest year with the most people alive, where nobody counts in the year they die.
  hint: The years span only about a century. Instead of walking through each life year by year, what if you only recorded where the count changes?
  insight: Each life is the half-open [birth, death). Add +1 at birth and -1 at death in a difference array over 1950 to 2050, then take the running sum and return the first year where it reaches its maximum.
  cost: O(n + R) time for R years, O(R) space
  pattern: intervals-sweep
- 56 core
  cue: Combine every set of overlapping intervals into one, where intervals that touch also combine.
  hint: If the intervals were in order of start, which earlier interval could the next one possibly overlap?
  insight: Sort by start. An interval can then only overlap the last merged block: extend that block's end to max(end, new end) when the new start is <= the block's end, otherwise start a new block.
  cost: O(n log n) time, O(n) space
  pattern: intervals-merge
- 986 core
  cue: Two lists of disjoint closed intervals, each sorted; report every overlap between an interval from one list and an interval from the other.
  hint: This is like merging two sorted lists. After comparing the current pair, which of the two can never overlap anything further on?
  insight: Two pointers: the overlap of the current pair is [max of the starts, min of the ends] when start <= end. Then advance whichever interval ends first, because every later interval in the other list starts after it has ended.
  cost: O(m + n) time, O(1) extra space
  pattern: intervals-overlap
- 57 core
  cue: A sorted list of disjoint intervals and one new interval to add, merging where necessary.
  hint: The existing intervals fall into three groups relative to the new one. What are they, and what happens to each?
  insight: Copy every interval that ends before the new start; absorb every interval that starts at or before the new end into the new interval (min of starts, max of ends); append it; copy the rest. One pass, because the list is already sorted.
  cost: O(n) time, O(n) space
  pattern: intervals-insert
- 729 core
  cue: Accept a stream of half-open bookings, rejecting any that would overlap an accepted one.
  hint: If the accepted bookings are kept sorted, how many of them can the new booking possibly clash with?
  insight: Keep accepted bookings sorted by start. Only the neighbours of the new booking can clash: find the first accepted booking that ends after the new start (bisect) and reject if it starts before the new end; otherwise insert.
  cost: O(log n) search per booking (O(n) list insertion, or O(log n) with a sorted container), O(n) space
  pattern: intervals-insert
- 2406 core
  cue: Split inclusive intervals into the fewest groups so that no two intervals in a group share a point.
  hint: Look at the busiest single moment. What does it force, and can you always achieve that bound?
  insight: The answer is the maximum number of intervals containing one point. Sort by left end and keep a min-heap of each group's last right end: reuse the group whose right end is smallest if it is strictly less than the new left end, otherwise open a group. The heap's size is the answer.
  cost: O(n log n) time, O(n) space
  pattern: intervals-rooms
- 452 core
  cue: Closed intervals on a line; find the fewest points such that every interval contains at least one of them.
  hint: Look at the interval that ends first. Where should a point that hits it go to hit as many others as possible?
  insight: Sort by end. Put a point at the end of the first interval not yet hit; it hits every interval that starts at or before it. Start a new point only when an interval starts strictly after the current point.
  cost: O(n log n) time, O(1) extra space
  pattern: intervals-select
- 435 derive
  cue: The fewest intervals to delete so that the remaining ones do not overlap, where touching is allowed.
  hint: Deleting the fewest is keeping the most. Which interval should a maximum set of kept intervals start with?
  insight: Keep intervals greedily in order of end time, taking one whenever it starts at or after the last kept end; answer n minus the number kept. The earliest-ending interval can always replace the first interval of an optimal set without creating an overlap.
  cost: O(n log n) time, O(1) extra space
  pattern: intervals-select
- 1851 derive
  cue: Many intervals and many query points; for each query, the size of the smallest interval containing it.
  hint: The queries do not have to be answered in the order given. If you visited them from left to right, which intervals would be candidates at each one?
  insight: Sort intervals by left end and queries by value, keeping original indices. For each query push every interval starting at or before it into a heap keyed by size, pop while the top ends before the query, and read the top. Expired intervals can never contain a later query.
  cost: O((n + q) log n + q log q) time, O(n + q) space
  pattern: intervals-offline
- cses:1164 stretch
  cue: Customers with arrival and departure days (both inclusive); give each a room so that no two overlapping stays share one, using as few rooms as possible.
  hint: Process customers by arrival. When a customer arrives, which occupied room should you check first?
  insight: Sort customers by arrival and keep a min-heap of (departure, room) for occupied rooms. If the earliest departure is before the arrival day, reuse that room; otherwise open a new one. The room count equals the most stays overlapping on one day.
  cost: O(n log n) time, O(n) space
  pattern: intervals-rooms
- 218 stretch
  cue: Overlapping rectangular buildings on a line; output the points where the height of the outline changes.
  hint: The outline can only change at a building's left or right edge. At each such x, what do you need to know about the buildings standing there?
  insight: Sweep the edges in order with a max-heap of (height, right edge) for buildings that have started. At each x, push the buildings starting there, pop tops whose right edge is <= x (lazy removal), and emit [x, top height or 0] when it differs from the previous height.
  cost: O(n log n) time, O(n) space
  pattern: intervals-offline
