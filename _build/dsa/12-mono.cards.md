=== card | 496
time: 20 min

## The problem

Given a list of distinct numbers and a query list drawn from it, return, for each queried number, the first strictly larger number to its right in the original list. Use -1 if there is none. For `[4, 1, 3, 2]`, queries `[1, 4]` produce `[3, -1]`.

## Constraints and what they imply

The source values are distinct and every query occurs in the source. The standard limits allow up to 1,000 values in either list, with values from 0 to 10,000. Thus a value identifies one position unambiguously, and a dictionary can store its answer. The query order need not match source order. The sentinel -1 cannot be confused with a found value in this domain.

## Brute force

Locate each query and walk right until a larger value appears. In the worst case this costs O(mn) for m queries and n source values, even if a position map removes the search for each starting location. The answer list uses O(m) space.

## The insight

Process the source from left to right. Keep unresolved values in a stack whose values decrease from bottom to top. A new value resolves every smaller top entry: nothing between that entry and the current position was larger, or it would already have resolved the entry. A larger unresolved entry blocks the current value, and everything below it is larger still.

## Optimal solution, traced

```steps
Source [4, 1, 3, 2]
    push 4 and 1; waiting [4, 1]
---
See 3: pop 1 and record 1 -> 3
    push 3, then 2; waiting [4, 3, 2]
---
End: remaining values have no answer
    queries [1, 4] yield {{[3, -1]}}
```

By induction the stack contains exactly the seen values without a larger seen successor. Every pop is resolved at the earliest possible index. Unpopped entries have no larger successor anywhere, so their default is correct.

## Code

```python
def next_greater_queries(queries, nums):
    waiting = []
    answer = {}
    for value in nums:
        while waiting and waiting[-1] < value:
            answer[waiting.pop()] = value
        waiting.append(value)
    return [answer.get(value, -1) for value in queries]
```

## Complexity

Each source value is pushed once and popped at most once. Expected time is O(n + m) with dictionary operations; auxiliary storage is O(n), plus O(m) for the returned list. The input lists are unchanged.

## Mistakes and edge cases

- Greater means strict; equality would not resolve a waiting value, although the stated source is distinct.
- Mapping by value breaks when the source has duplicates because the same value can have different successors.
- An empty query list returns an empty list; a decreasing source produces only -1 answers.

## Variations

- Return successor indices instead, using a stack of indices rather than values.
- If duplicates are allowed, query positions rather than values and retain one answer per index.

=== card | 739
time: 25 min

## The problem

For each day's temperature, return the distance to the earliest later day with a strictly higher temperature. Return zero for days without such a later day. For `[70, 72, 71, 73]`, the waits are `[1, 2, 1, 0]`. The value reported is a number of days, not the warmer temperature.

## Constraints and what they imply

The standard input has up to 100,000 days, with temperatures between 30 and 100. Entries can tie, and tied temperatures do not qualify as warmer. Scanning all later days for every position is wasteful at that scale. Integer comparisons are enough, and indices are needed to calculate distances. This implementation also accepts an empty sequence.

## Brute force

For each index, inspect following entries in order until the first warmer temperature appears; if none does, write zero. A decreasing or constant sequence causes n(n-1)/2 comparisons, giving O(n²) time and O(n) output space. This is a useful independent specification, but it repeats work on the same suffixes.

## The insight

Keep indices of unresolved days in a stack. Their temperatures are nonincreasing from bottom to top. When the current temperature is higher than the top, it is that day's first warmer successor: any earlier warmer day would have removed it already. Set the distance and continue popping, since the current day can resolve several older days at once. Push the current index after resolving earlier days.

If a top day is not cooler than today, it stays. All entries underneath are at least as warm, so they cannot be resolved by today either. Equal entries must remain separately because they may have different distances to a future warmer day.

## Optimal solution, traced

```steps
Temperatures [70, 72, 71, 73]
    day 0 waits; day 1 resolves it at distance 1
---
Day 2 is cooler than day 1
    stack indices [1, 2], both unresolved
---
Day 3 resolves day 2 at distance 1 and day 1 at distance 2
    remaining day 3 keeps zero; result {{[1, 2, 1, 0]}}
```

Initially the stack is empty and every answer is zero. At each step, the pop rule establishes the first warmer day for exactly the entries it removes; the rest still have no warmer day in the processed prefix. At termination unresolved entries have no warmer day anywhere, proving their zero answers.

## Code

```python
def daily_temperatures(temperatures):
    result = [0] * len(temperatures)
    waiting = []
    for day, temp in enumerate(temperatures):
        while waiting and temperatures[waiting[-1]] < temp:
            previous = waiting.pop()
            result[previous] = day - previous
        waiting.append(day)
    return result
```

## Complexity

Every index enters and leaves the stack at most once, even though a single day can trigger many pops. The total running time is O(n), auxiliary stack space is O(n), and the returned array occupies O(n). No temperatures are changed.

## Mistakes and edge cases

- Use `<`, not `<=`: equal temperatures do not end a wait.
- Store indices, not only temperatures, so the distance is available.
- The last day and all days in a nonincreasing sequence correctly retain zero.
- A long sequence of equal temperatures is legal and can all be resolved by one later warmer day.

## Variations

- Return the next warmer temperature instead of the distance.
- Require a temperature at least as high as today's; change the comparison and revisit equality.

=== card | 503
time: 25 min

## The problem

For each position in a circular array, find the first strictly greater value encountered by moving right and wrapping at the end. Use -1 when no such value exists. For `[2, 1, 2, 4]`, the answers are `[4, 2, 4, -1]`. Each position is a separate query even if values repeat.

## Constraints and what they imply

The standard input has up to 10,000 values, each between -10⁹ and 10⁹. Values may repeat, so values alone cannot identify waiting positions. One full circuit after an index examines every other position; going farther cannot discover a new candidate. Empty input returns an empty result as an extension. A found value can itself be -1, so the prescribed -1 output cannot distinguish that answer from absence.

## Brute force

For every index, examine offsets 1 through n-1, using modular indexing, until finding a greater value. This takes O(n²) time in a constant or decreasing-like circular input, and O(n) for the answers. Its direct order of inspection also makes it a good oracle.

## The insight

Imagine scanning two copies of the array consecutively, but put each index on the waiting stack only in the first copy. Each virtual position can resolve earlier waiting entries whose values are strictly smaller. A second copy exposes the wrapped part of each search; a third adds no new information. The stack is nonincreasing by value, so once its top cannot be resolved neither can any element below it.

Although an unresolved index can still be present when its own second-copy value appears, it cannot pop itself: equality is not greater. If it has no greater value, it stays unresolved and its default remains -1. Store indices so equal values get independent answers.

## Optimal solution, traced

```steps
Array [2, 1, 2, 4], initial answers all -1
    first 2 waits; 1 waits; next 2 resolves 1
---
4 resolves both 2s and waits itself
    answers [4, 2, 4, -1]
---
The second lap has no value larger than 4
    result {{[4, 2, 4, -1]}}
```

Every pop occurs at the first greater virtual position after its original index, because earlier candidates would already have popped it. The two scans include all possible circular successors. Consequently entries never popped have no valid greater element.

## Code

```python
def next_greater_circular(nums):
    n = len(nums)
    answer = [-1] * n
    waiting = []
    for i in range(2 * n):
        value = nums[i % n]
        while waiting and nums[waiting[-1]] < value:
            answer[waiting.pop()] = value
        if i < n:
            waiting.append(i)
    return answer
```

## Complexity

The loop visits 2n virtual positions. Each index is pushed once and popped at most once, so time is O(n). The stack and output each use O(n) space. For n=0 the loop never evaluates the modulo operation.

## Mistakes and edge cases

- Pushing on both laps duplicates work and can overwrite an answer with a non-first successor.
- Do not pop equal values; an all-equal array returns all -1.
- A singleton has no strictly greater successor, including itself.
- Looking only to the physical end misses valid wrapped answers.

## Variations

- Return the circular distance to the next greater position rather than its value.
- Change the predicate to next strictly smaller, and reverse the stack comparisons.

=== card | 901
time: 25 min

## The problem

Prices arrive in chronological order. After each arrival return the number of consecutive days ending today whose prices are no greater than today's price. For arrivals `[3, 1, 2, 2]`, spans are `[1, 1, 2, 3]`. The count includes today and stops just after the nearest earlier strictly higher price.

## Constraints and what they imply

The standard constraints allow at most 10,000 calls, with positive prices up to 100,000. An online interface must answer without knowing future prices. Equal prices count as covered, and a long increasing run may make the span as large as the number of calls. A data structure may retain history between calls; it need not store every individual day if it can summarize groups without losing future answers.

## Brute force

Append each price to a list and scan backward while entries are no greater than it. One call can inspect the whole history; across n increasing prices the total is O(n²), with O(n) storage. Repeatedly visiting the same covered days is the source of the wasted work.

## The insight

Store pairs `(price, span)` in a stack with strictly decreasing prices. A pair's span represents a contiguous block ending at that price; all earlier prices within that block are at most the pair's price. If a new price is at least the top price, the new span can absorb the entire top block. Pop and add its span, repeating until the remaining top is strictly higher or the stack is empty.

The retained higher price is exactly the barrier that stops today's span. Any popped pair can never again be a better barrier for a future day: the newer price is at least as high and lies closer to that future day. The aggregated count preserves how many days the new pair covers.

## Optimal solution, traced

```steps
Receive 3 then 1
    stack [(3, 1), (1, 1)], spans 1 and 1
---
Receive 2: absorb (1, 1), stop at 3
    push (2, 2), report 2
---
Receive 2: equal top is absorbed
    push (2, 3), report {{3}}
```

Inductively each stack pair is a block of consecutive covered days, and the blocks partition the processed history. Absorbing exactly the consecutive suffix of blocks with top prices at most the new price yields precisely the maximal valid suffix ending today. Remaining prices stay strictly decreasing.

## Code

```python
class StockSpanner:
    def __init__(self):
        self.stack = []

    def next(self, price):
        span = 1
        while self.stack and self.stack[-1][0] <= price:
            span += self.stack.pop()[1]
        self.stack.append((price, span))
        return span
```

## Complexity

Each call pushes one pair, and every pair can be popped only once. Over n calls time is O(n), or O(1) amortized per call, though one call may take O(n). The stack occupies O(n) space in a decreasing stream.

## Mistakes and edge cases

- Pop equal prices as well as smaller ones, because both satisfy the span condition.
- Add the whole stored span, not just one per pop.
- Initialize every new span to one for the current day.
- The first price has span one, and a strictly decreasing stream keeps all pairs.

## Variations

- Ask for the closest earlier strictly higher price instead of the number of covered days.
- Keep original day indices to return the left boundary as well as the span.

=== card | 402
time: 30 min

## The problem

Remove exactly k digits from a nonnegative integer written as a digit string. Preserve the relative order of the remaining digits and return the smallest resulting number as a string, without leading zeros. If no nonzero digit remains, return `"0"`. For `"1432"` and k=2, choosing the subsequence `"12"` gives `"12"`.

## Constraints and what they imply

Assume `0 <= k <= len(num)` and that the input contains decimal digits; the standard length limit is 100,000. Standard inputs have no leading zeros except for `"0"`, though the function also normalizes leading zeros on other inputs. The number can be too long for convenient integer conversion, so compare digit characters and build a string. Every candidate has the same number of retained digits before normalization; lexicographic order therefore agrees with numerical order, including candidates beginning with zeros.

## Brute force

Enumerate every choice of k deleted positions, retain the others in order, and take the smallest normalized number. There are binomial(n, k) choices, each requiring O(n) work and O(n) working space. The approach is useful on short strings, but the number of choices grows rapidly.

## The insight

For two adjacent retained candidates where the earlier digit is larger, deleting that earlier digit improves the first position where the resulting strings differ. Maintain a stack of selected digits. When a smaller digit arrives and deletions remain, pop larger digits from the end until that inversion disappears or the budget is exhausted. Then append the new digit.

This exchange is safe: replacing a larger earlier digit by the smaller current one improves the earliest affected position, while leaving the relative order of all other kept digits intact. Applying the exchange repeatedly gives the smallest possible prefix for the spent budget. If the scan ends with unused deletions, the remaining stack is nondecreasing; removing its final digits retains the smallest possible prefix.

## Optimal solution, traced

```steps
num = "1432", k = 2
    push 1, then 4; stack 14
---
Read 3: pop 4, spend one deletion, push 3
    stack 13, one deletion remains
---
Read 2: pop 3 and push 2
    stack 12; normalized answer {{"12"}}
```

Any optimal solution with a larger digit immediately before a smaller available digit can be exchanged for one deleting the larger digit, unless earlier budget choices already determine the prefix. The stack makes these exchanges as early as possible. After all inversions that the budget permits are repaired, deleting the suffix is optimal, so exactly k digits are removed.

## Code

```python
def remove_k_digits(num, k):
    stack = []
    remaining = k
    for digit in num:
        while remaining and stack and stack[-1] > digit:
            stack.pop()
            remaining -= 1
        stack.append(digit)
    if remaining:
        del stack[-remaining:]
    return "".join(stack).lstrip("0") or "0"
```

## Complexity

Each digit is pushed once and popped at most once. Joining and stripping take O(n), giving O(n) time and O(n) stack/output space. The function does not convert the potentially long number to an integer.

## Mistakes and edge cases

- Remove exactly k digits before stripping leading zeros; normalization is not an extra deletion decision.
- Guard the suffix deletion: `stack[-0:]` denotes the entire stack, not an empty suffix.
- Equal digits need not be popped; preserving the earlier one leaves the same prefix with more options later.
- With k equal to n, the result is `"0"`; k=0 still normalizes leading zeros.

## Variations

- Maximize the remaining number by reversing the comparison.
- Return retained indices alongside the normalized value, keeping normalization separate from selection.

=== card | 853
time: 30 min

## The problem

Cars start at distinct positions before a target, each with a positive constant speed until it catches a slower group ahead. Cars cannot pass; after catching, they travel together at the group's speed. Count the groups arriving at the target, including a catch exactly at the target. For target 12, positions `[10, 8, 0]` and speeds `[2, 4, 1]`, the first two meet at the target and the answer is 2.

## Constraints and what they imply

The standard limits permit up to 100,000 cars and a target up to 1,000,000. Positions are distinct, nonnegative, and strictly below the target; speeds are positive integers up to 1,000,000. Each position corresponds to its speed, and the input need not be sorted. A car's independent arrival time is a positive rational number. Comparing ratios by cross multiplication avoids floating-point rounding near a tie; Python integers do not overflow.

## Brute force

Sort the cars from front to back, then simulate moving groups and their next catch events until all reach the destination. Alternatively, compare a rear car's path against each group already constructed. Pairwise group scans can take O(n²) after sorting and require O(n) storage. The group immediately ahead is enough, so the extra comparisons are avoidable.

## The insight

Process positions from nearest to farthest. A group ahead has an effective arrival time: the independent time of the slowest limiting car in that group. A following car with independent time no greater than that group's time catches the group by the target, including equality, and inherits its arrival time. A car with a strictly later independent time cannot catch that group and starts a new group behind it.

Only the arrival time of the most recently formed group matters. If the new car cannot catch this nearest group, it cannot pass it to reach any group farther ahead. If it catches, the nearest group's arrival time remains unchanged, so no additional state is needed.

## Optimal solution, traced

```steps
target 12, cars ordered by position 10, 8, 0
    front car time 2/2 = 1; start fleet 1
---
Car at 8 has time 4/4 = 1
    catches at target; fleet count stays 1
---
Car at 0 has time 12/1 = 12 > 1
    starts a second fleet; answer {{2}}
```

The processed cars form valid fleets in front-to-back order. The nearest fleet acts as a barrier to all earlier fleets. Comparing arrival times determines whether the next car reaches that barrier by the destination, so induction preserves both the fleet count and the last fleet's arrival time.

## Code

```python
def car_fleets(target, positions, speeds):
    cars = sorted(zip(positions, speeds), reverse=True)
    fleets = 0
    last_distance, last_speed = 0, 1
    for position, speed in cars:
        distance = target - position
        if distance * last_speed > last_distance * speed:
            fleets += 1
            last_distance, last_speed = distance, speed
    return fleets
```

## Complexity

Sorting n cars costs O(n log n) time and O(n) space for the sorted pairs. The scan is O(n), using constant additional state beyond sorting. Exact integer arithmetic assumes the usual unit-cost comparison model.

## Mistakes and edge cases

- Equal arrival times merge: use strict greater-than for a new fleet.
- Process the closest car first; the reverse direction lacks the fleet barrier information.
- Keep the front fleet's arrival time after a merge, not the following car's shorter time.
- No cars means zero fleets; positive speed and positions before the target are assumed.

## Variations

- Return the members of each fleet by storing a list for each newly formed group.
- If bounded integer positions permit counting sort, trade extra positional storage for faster ordering.

=== card | 907
time: 30 min

## The problem

For every nonempty contiguous subarray, take its minimum and add those minima. Return the sum modulo 1,000,000,007. For `[3, 1, 2]`, the six minima are 3, 1, 1, 1, 1, and 2, yielding 9. Equal values are separate occurrences, even when the resulting minima match.

## Constraints and what they imply

The standard input has at most 30,000 positive integers, each at most 30,000, so listing all subarrays is too expensive. The unreduced total may be large. Python supports arbitrary-size integers, and applying the modulus to the final sum gives the required residue. Empty input can be interpreted as a sum of zero.

## Brute force

Choose a left endpoint, extend the right endpoint one position at a time, and maintain the running minimum. Add it at each extension. This visits n(n+1)/2 subarrays in O(n²) time and O(1) auxiliary space, excluding the input. It is straightforward enough to serve as an independent test oracle.

## The insight

Reverse the counting: assign each subarray to one occurrence of its minimum, and count the subarrays assigned to each index. Choose the rightmost occurrence when equal minima occur. For index i, find the previous strictly smaller value at L and the next smaller-or-equal value at R, using -1 and n if absent. Any left endpoint from L+1 through i and right endpoint from i through R-1 makes i the rightmost minimum.

There are `(i-L) * (R-i)` such endpoint pairs, so i contributes its value times that product. The asymmetry matters: an equal minimum to the left is allowed, but an equal minimum to the right takes ownership. Thus every subarray has exactly one owner rather than being counted twice or omitted.

## Optimal solution, traced

```steps
Array [3, 1, 2]
    previous strictly smaller indices L = [-1, -1, 1]
---
Next smaller-or-equal indices R = [1, 3, 3]
    contributions: 3*1*1, 1*2*2, 2*1*1
---
Sum 3 + 4 + 2 = 9
    residue {{9}}
```

In the left pass, pop values greater than or equal to the current value; the remaining top is the closest strictly smaller index. In the right pass, pop only greater values; the remaining top is the closest smaller-or-equal index. The endpoint rectangle defined by those boundaries is exactly the set owned by i, proving the contribution formula and the sum.

## Code

```python
def sum_subarray_mins(nums):
    n = len(nums)
    left = [-1] * n
    right = [n] * n
    stack = []
    for i, value in enumerate(nums):
        while stack and nums[stack[-1]] >= value:
            stack.pop()
        if stack:
            left[i] = stack[-1]
        stack.append(i)
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and nums[stack[-1]] > nums[i]:
            stack.pop()
        if stack:
            right[i] = stack[-1]
        stack.append(i)
    total = sum(value * (i - left[i]) * (right[i] - i)
                for i, value in enumerate(nums))
    return total % 1_000_000_007
```

## Complexity

Each index is pushed and popped at most once in each pass. Time is O(n); the boundary arrays and stack use O(n) auxiliary space. Modulo arithmetic does not change the asymptotic operation count.

## Mistakes and edge cases

- Using strict comparisons on both sides double-counts intervals with equal minima; using non-strict boundaries on both sides misses some.
- The boundary positions themselves are excluded, hence the endpoint counts use distances rather than distances plus one.
- On `[2, 2]`, the rightmost 2 owns the two-element subarray; the sum is 6.
- Empty input yields zero, and one element contributes itself modulo the modulus.

## Variations

- Sum subarray maxima by reversing the comparisons and choosing a consistent tie owner.
- Return each index's contribution separately to inspect the partition of subarrays.

=== card | 84
time: 40 min

## The problem

A histogram consists of adjacent unit-width bars with nonnegative heights. Find the largest area of a rectangle lying entirely under the bar tops. A rectangle spans a consecutive run of bars and its height cannot exceed any bar in that run. For heights `[2, 1, 2]`, the best area is 3, achieved by spanning all three bars at height 1.

## Constraints and what they imply

The standard limit is 100,000 bars, each of height 0 through 10,000. Bars can have equal heights and zeros. Width is the number of consecutive bars, not the difference between bar heights. An empty histogram has area zero as an extension. Since a rectangle can be lowered until its top meets a shortest bar in its span, considering areas associated with bar heights suffices; arbitrary real heights need not be enumerated.

## Brute force

For each left endpoint, extend a right endpoint across the histogram, maintaining the smallest height seen. The best rectangle for that span has area `minimum * width`. Taking the maximum over every span takes O(n²) time and O(1) working space. It independently checks the optimized method for small examples, including repeated heights.

## The insight

Maintain a stack of indices whose heights are nondecreasing. When the current height is lower than the height at the top, pop that bar: the current index is the first position to the right that prevents a rectangle at the popped height. The new stack top is a left boundary at height no greater than the popped height, or -1 if none remains. The rectangle between these boundaries has width `right - left - 1`.

The left boundary can be equal, not strictly smaller. This choice avoids popping equal bars during the scan. When equal bars are eventually popped from right to left, the leftmost equal bar gets the full width that includes the whole equal-height plateau. Thus at least one bar representing any optimum minimum receives enough width, even though other equal bars may receive smaller widths.

Process a virtual height zero after the last real bar. It flushes every positive height still on the stack, providing a right boundary at n. Zero-height bars may remain, but they cannot improve an area. The sentinel is virtual, so the input is not modified.

## Optimal solution, traced

```steps
Heights [2, 1, 2], best = 0
    push index 0; height 1 pops it, width 1, area 2
---
Push index 1 then index 2
    stack heights [1, 2], best 2
---
Virtual zero at index 3 pops height 2: area 2
    then pops height 1: width 3, area 3; result {{3}}
```

The stack invariant holds initially and after each push: when a lower height arrives, all taller entries are removed before the current index is added. Every popped rectangle is valid because no intervening bar is lower than its height. Conversely, take an optimal span and its leftmost minimum bar. Before the first lower bar to its right, it stays on the stack; after taller bars are removed, the boundary to its left cannot cut into the span because no bar there is lower and this is the leftmost minimum. Its computed rectangle covers that span. Therefore the maximum of the candidates is optimal.

## Code

```python
def largest_rectangle(heights):
    stack = []
    best = 0
    n = len(heights)
    for right in range(n + 1):
        current = heights[right] if right < n else 0
        while stack and heights[stack[-1]] > current:
            height = heights[stack.pop()]
            left = stack[-1] if stack else -1
            best = max(best, height * (right - left - 1))
        if right < n:
            stack.append(right)
    return best
```

## Complexity

The loop visits n real bars and one sentinel. Each index is pushed once and popped at most once, so total time is O(n), despite the nested while loop. The stack takes O(n) auxiliary space for an increasing or equal-height sequence. The input is unchanged and the output is a single integer.

## Mistakes and edge cases

- The right boundary is excluded, as is the surviving left boundary; the width is not `right - left`.
- A final flush is necessary for bars that never meet a shorter real bar.
- Equality requires a consistent policy. This implementation keeps equal bars and lets the leftmost one span their plateau.
- A zero height breaks positive rectangles; all zeros and the empty list return zero.
- This implementation assumes nonnegative heights; a zero sentinel would not flush negative heights.

## Variations

- Return a maximizing interval as well as its area by recording `left + 1` and `right - 1` on improvement.
- For variable positive bar widths, store cumulative horizontal coordinates and compute geometric width between boundaries.

=== card | 239
time: 40 min

## The problem

Given an array and a window length k, report the maximum in every contiguous window of exactly k elements, from left to right. For `[1, 3, 2, 5]` and k=2, the windows have maxima `[3, 3, 5]`. A window advances by one index at a time, and equal values are valid.

## Constraints and what they imply

The standard input contains up to 100,000 elements between -10,000 and 10,000. Assume `1 <= k <= len(nums)`: there is at least one complete window. The function raises `ValueError` for other k values, including an empty array. Values may be negative or repeated, so neither zero nor a value alone can mark an expired entry. The result has exactly n-k+1 elements.

## Brute force

For each window, inspect all k values and record the greatest. This requires O((n-k+1)k) time and O(n-k+1) output space, with O(1) extra working space. It treats each window independently and repeats comparisons for the k-1 entries shared by adjacent windows.

## The insight

Keep a deque of candidate indices in increasing index order and strictly decreasing value order. Before inserting index i, remove expired indices from the front: any index at most i-k lies outside the window ending at i. Then remove indices from the back while their values are at most the new value. The new index is later and no smaller, so any future window containing the older candidate also contains the newer one until the older expires. The older candidate can never be needed as a maximum.

Append the new index. Once a full window exists, the deque's front has the largest retained value. Removed candidates are either outside the current window or dominated by a later candidate. Repeated equal values are safe to remove from the back because the newer equal value has the same maximum value and expires later.

The deque stores only indices in the current window. Removing from both ends is important: expiry happens by age at the front, while domination happens by value at the back. A plain stack cannot perform both operations efficiently.

For example, with window size three and values `[5, 5, 1, 2]`, the second 5 replaces the first as a candidate. It remains available for the second window after the older 5 has expired, so both windows correctly report 5.

## Optimal solution, traced

```steps
nums [1, 3, 2, 5], k = 2
    insert 1; insert 3 and discard 1; first maximum 3
---
Insert 2: deque indices [1, 2]
    window [3, 2] has maximum 3
---
Index 1 expires; 5 dominates 2
    deque [3], final maximum 5; result {{[3, 3, 5]}}
```

After each insertion, indices are current and ordered, and values decrease because all no-larger suffix entries were removed. Every discarded in-window value has a later retained dominator, possibly through a chain of replacements; as long as it remains in a window, that dominator also remains. Hence the largest window value is represented and must be at the front. Output begins only after k values have been processed, giving exactly one result per valid window.

## Code

```python
from collections import deque

def sliding_window_max(nums, k):
    if not 1 <= k <= len(nums):
        raise ValueError("k must be between 1 and the array length")
    candidates = deque()
    answer = []
    for i, value in enumerate(nums):
        while candidates and candidates[0] <= i - k:
            candidates.popleft()
        while candidates and nums[candidates[-1]] <= value:
            candidates.pop()
        candidates.append(i)
        if i >= k - 1:
            answer.append(nums[candidates[0]])
    return answer
```

## Complexity

Each index is appended once and removed at most once, from either end. Total time is O(n), even if a single arrival removes many candidates. The deque holds at most k indices, so auxiliary space is O(k); the returned list requires O(n-k+1) space. The input is not changed.

## Mistakes and edge cases

- Store indices rather than just values, so expiry is determined correctly when duplicates occur.
- Drop index `i-k` before reading the maximum; it is just outside the new window.
- Do not emit a result until the first full window ends at k-1.
- With k=1 the answer copies the input; with k=n there is exactly one maximum.
- Keeping equal values is also possible, but then expiry and the claimed deque ordering must match that choice.

## Variations

- Compute window minima by reversing the value comparison.
- Report the index of the maximum; specify whether the oldest or newest equal maximum wins before choosing the equality rule.

=== card | 1438
time: 30 min

## The problem

Find the greatest length of a contiguous subarray whose maximum minus minimum is at most a given nonnegative limit. For `[8, 2, 4, 7]` with limit 4, `[2, 4]` and `[4, 7]` are valid, and the answer is 2. Individual elements always form valid windows under the stated limit.

## Constraints and what they imply

The standard input has up to 100,000 positive values, each at most 10⁹, and a limit from zero to 10⁹. This implementation also handles negative values and empty input. Duplicate values are allowed. A nonnegative limit makes the validity condition meaningful for a singleton. The window endpoints move only forward, because deleting elements cannot increase its maximum-minus-minimum range. Recomputing both extrema after each boundary move would lose the linear bound.

## Brute force

Choose each left endpoint and extend right while tracking its minimum and maximum. Test every span and keep the largest valid length. This takes O(n²) time and O(1) working space, and is suitable as a small-input oracle. Testing only neighboring differences is insufficient because the true extremes can be far apart.

## The insight

Maintain two deques of indices inside the current window: decreasing values for the maximum and increasing values for the minimum. On insertion, drop older no-better candidates from each back, then append the new index. Their fronts give the current extrema. If the range exceeds the limit, advance the left edge and remove any deque fronts that leave the window; repeat until valid.

For a fixed right endpoint, the first valid left endpoint after shrinking gives the longest valid window ending there. Any earlier left endpoint was invalid and remains invalid when more elements are added. Therefore scanning all right endpoints while never moving left backward still examines a longest candidate for each endpoint.

## Optimal solution, traced

```steps
nums [8, 2, 4, 7], limit 4
    [8] is valid; adding 2 makes range 6
---
Remove 8 from the window; [2, 4] has range 2
    best length becomes 2
---
Adding 7 makes [2, 4, 7] invalid
    remove 2; [4, 7] is valid, result {{2}}
```

Each deque retains undominated in-window indices, so its front is the correct extremum. Shrinking terminates because a singleton has range zero. At each right endpoint the algorithm maintains the earliest feasible left boundary; the maximum recorded length is thus globally optimal.

## Code

```python
from collections import deque

def longest_bounded_range(nums, limit):
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    high, low = deque(), deque()
    left = best = 0
    for right, value in enumerate(nums):
        while high and nums[high[-1]] <= value:
            high.pop()
        while low and nums[low[-1]] >= value:
            low.pop()
        high.append(right)
        low.append(right)
        while nums[high[0]] - nums[low[0]] > limit:
            if high[0] == left:
                high.popleft()
            if low[0] == left:
                low.popleft()
            left += 1
        best = max(best, right - left + 1)
    return best
```

## Complexity

Each index enters and leaves each deque at most once, and the left boundary advances at most n times. Total time is O(n), with O(n) worst-case auxiliary space. The input remains unchanged.

## Mistakes and edge cases

- Expire indices in both deques independently; an index can be both extrema.
- Shrink in a loop, not just once, because several leftmost elements may need removal.
- Duplicate extrema are handled by keeping the newer equal candidate, which expires later.
- With limit zero, the answer is the longest contiguous run of equal values.

## Variations

- Return the start and end indices of a longest valid window, with a stated tie rule.
- Count all valid subarrays by adding the current valid window length at every right endpoint.

=== card | 862
time: 45 min

## The problem

Find the minimum length of a nonempty contiguous subarray whose sum is at least a positive target k. Elements may be negative. Return -1 if no such subarray exists. For `[2, -1, 2]` and k=3, the whole array qualifies and the answer is 3; no shorter span does.

## Constraints and what they imply

The standard limits allow 100,000 values in the range -100,000 to 100,000 and a positive target up to 10⁹. A simple grow-until-large, shrink-until-small window is not reliable: adding a negative number can decrease the sum, and removing one can increase it. Prefix sums allow any subarray sum to be computed as a difference, without assuming monotonicity of the original values. An empty array contains no nonempty candidate.

## Brute force

For each start position, accumulate sums while extending the end and record the shortest qualifying length. Inspect all ends, because a negative value can make the sum decrease after it first crosses k. This takes O(n²) time and O(1) working space. It is an independent way to verify small cases.

## The insight

Define `prefix[i]` as the sum of the first i values. The sum of `[j, i)` is `prefix[i] - prefix[j]`, and its length is i-j. As i moves from 0 to n, maintain a deque of possible starting prefix indices in increasing index order and strictly increasing prefix-sum order.

First, while the front yields a sum of at least k, record its length and remove it. Any future end paired with that same start will be farther away, so it cannot improve on the valid length just found. A later start at the next deque position may also qualify and gives a shorter length, so continue until the front no longer qualifies.

Then remove from the back every index j whose prefix sum is at least the current prefix sum. The current index is later and no higher: for every future end, it offers a sum at least as large and a strictly shorter length than j. Thus j is dominated. Append i only after checking earlier starts, so the algorithm never accepts an empty interval even for a nonpositive target.

## Optimal solution, traced

```steps
nums [2, -1, 2], k = 3; prefix sums [0, 2, 1, 3]
    insert prefix index 0, then index 1
---
At index 2, prefix 1 dominates index 1's prefix 2
    deque indices become [0, 2]
---
At index 3, 3 - 0 reaches target
    record length 3, remove index 0; result {{3}}
```

By induction, the deque contains undominated starts that have not already produced a qualifying interval at an earlier end. Removing a dominated start cannot lose an optimal interval: replacing it with its later, no-higher prefix gives a shorter valid interval for the same future end. Removing a qualifying front is also safe, because this end is its earliest qualifying end among the endpoints processed while it was retained, and later ends are longer. If the front fails the threshold, all later deque prefixes have larger sums and fail too. Therefore every potentially optimal interval is either recorded or improved by a retained alternative.

## Code

```python
from collections import deque

def shortest_subarray_at_least(nums, k):
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    starts = deque()
    best = len(nums) + 1
    for end, total in enumerate(prefix):
        while starts and total - prefix[starts[0]] >= k:
            best = min(best, end - starts.popleft())
        while starts and prefix[starts[-1]] >= total:
            starts.pop()
        starts.append(end)
    return best if best <= len(nums) else -1
```

## Complexity

Building n+1 prefix sums takes O(n) time and space. Every prefix index enters the deque once and leaves at most once, so the scan is also O(n) time and O(n) space. Python integer arithmetic avoids fixed-width sum overflow; fixed-width implementations need a sufficiently wide type.

## Mistakes and edge cases

- Start with prefix sum zero, or subarrays beginning at index zero are missed.
- The front loop must run before inserting the current prefix, to ensure a positive length.
- Remove equal prefix sums from the back: the later equal sum dominates the earlier one.
- A negative element can invalidate ordinary sliding-window reasoning even if the total of the full array is positive.
- Return -1 when no qualifying interval exists; a single large element gives length one.

## Variations

- Return interval endpoints by saving the start and end when the best length improves.
- Find the shortest subarray with sum at most a negative threshold by negating all values and the threshold.

=== card | 85
time: 45 min

## The problem

Given a rectangular grid of `"0"` and `"1"` characters, return the largest area of an axis-aligned rectangle containing only ones. A rectangle must use consecutive rows and consecutive columns. For `[["1", "0", "1"], ["1", "1", "1"]]`, the largest area is 3, using the whole second row.

## Constraints and what they imply

Assume each row has the same number of columns and every cell is the string `"0"` or `"1"`; the standard grid has at most 200 rows and 200 columns. Either dimension may be zero in this implementation, in which case the answer is zero. Enumerating all rectangles and inspecting every cell is expensive. The result is an area, not a count of all possible rectangles.

## Brute force

Enumerate top, bottom, left, and right boundaries, and check whether every cell inside each rectangle is one. On an r by c grid there are O(r²c²) boundary choices and checking each costs up to O(rc), for O(r³c³) time and O(1) extra space. A two-dimensional prefix sum can speed the validity checks, but still considers quadratically many boundary pairs in each dimension.

## The insight

Process one row at a time. At column c, keep the number of consecutive ones ending at the current row. A zero resets that height to zero, while a one extends it by one. These heights form a histogram. Every all-one rectangle whose bottom is the current row corresponds to consecutive histogram bars whose heights are at least the rectangle's height, and conversely every rectangle under this histogram represents a valid all-one grid rectangle.

Find the largest histogram rectangle with a nondecreasing stack of indices. When a lower bar arrives, the popped height cannot extend past that bar on the right; after the pop, the new top is its left boundary. Equal heights remain on the stack, so the leftmost equal bar eventually gets the entire plateau. A virtual zero after the final column flushes the positive bars. Repeat for every row and retain the maximum.

This reduces a two-dimensional search to r one-dimensional searches. The heights array is updated in place, but the grid itself is never changed. The sentinel is read as zero rather than appended, so it does not disturb the next row's heights.

## Optimal solution, traced

```steps
Grid rows ["1", "0", "1"] and ["1", "1", "1"]
    first row heights [1, 0, 1], best area 1
---
Second row updates heights to [2, 1, 2]
    height 1 pops the first 2, area 2
---
The virtual zero flushes the last 2 and then the 1
    height 1 spans all three columns; result {{3}}
```

Inductively each height counts exactly the consecutive ones above and including the current row. In the histogram pass, every popped area is valid because the bars between its boundaries are at least that tall. For any best histogram span, its leftmost minimum bar eventually pops with a width covering that span, including equal-height bars. Thus the histogram maximum is found. Every grid rectangle has a unique bottom row, so taking the maximum over rows covers every candidate and returns the global optimum.

## Code

```python
def maximal_rectangle(matrix):
    if not matrix or not matrix[0]:
        return 0
    columns = len(matrix[0])
    heights = [0] * columns
    best = 0
    for row in matrix:
        for col, cell in enumerate(row):
            heights[col] = heights[col] + 1 if cell == "1" else 0
        stack = []
        for right in range(columns + 1):
            current = heights[right] if right < columns else 0
            while stack and heights[stack[-1]] > current:
                height = heights[stack.pop()]
                left = stack[-1] if stack else -1
                best = max(best, height * (right - left - 1))
            if right < columns:
                stack.append(right)
    return best
```

## Complexity

Updating heights takes O(c) per row. Each column index is pushed and popped at most once in that row's histogram pass, also O(c). Overall time is O(rc), and heights plus the stack take O(c) auxiliary space. The input grid is unchanged.

## Mistakes and edge cases

- Reset a column height to zero on a zero cell; a rectangle cannot bridge that cell.
- Use a fresh stack for each row and flush at its right edge.
- This interface accepts character cells, not integer 1; mixing representations silently gives the wrong heights.
- Equal heights are deliberately retained, and the leftmost equal bar supplies their widest candidate.
- Empty grids, empty rows, all-zero grids, one-row grids, and one-column grids are covered.

## Variations

- Track coordinates of the best rectangle using the popped height, current row, and histogram boundaries.
- Find the largest all-zero rectangle by reversing which cell extends a height.
