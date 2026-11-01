---
key: mono
name: Monotonic stacks and queues
stage: scan
summary: Keep a stack or deque in sorted order so every element is pushed and popped at most once, answering nearest-greater, span, histogram, contribution and window-extreme questions in O(n).
why: Many array questions ask, for every element, about the first element in some direction that beats it, or about the extreme of every window. The obvious answer scans outwards from each element and costs O(n^2). A monotonic stack or deque throws away every element that can never be an answer again, so the survivors stay sorted and each element enters and leaves once. The same pop-until-valid loop builds Cartesian trees and convex hulls, and Lemire's streaming max-min filter computes running window extremes for signal processing and time series with two monotonic deques. Learning the invariant and the amortised argument once lets you write all of these from memory and prove they are O(n).
outcomes:
- Write the next-greater pass from memory and adapt it to previous or next, greater or smaller, strict or non-strict, circular and online variants
- Prove that a while loop inside a for loop is O(n) overall by counting pushes and pops
- Find each element's left and right limits to solve the largest rectangle in a histogram and sums of subarray minimums, without double counting ties
- Maintain the maximum or minimum of a sliding window with a monotonic deque, including windows over prefix sums
- Recognise greedy problems that hide a monotonic stack, and choose a heap or sorted container when the monotonic argument fails
cues:
- For every element: the nearest greater or smaller value to its left or right, or the distance to it
- "Until something taller, warmer or cheaper appears", spans, visibility, one object blocking another
- A sum or count over all subarrays of their minimum or maximum, or rectangles limited by their shortest bar
- The maximum or minimum of every window of size k, or a recurrence that needs the best of the last k states
- Remove k items to make the smallest (or largest) result while keeping the original order
traps:
- Storing values instead of indices, so widths, distances and expiry cannot be computed
- Using the same strictness on both sides, which counts subarrays with tied extremes twice or not at all
- Forgetting to flush the stack at the end (a sentinel value or a final loop)
- Reading a while loop inside a for loop as O(n^2) and reaching for something more complicated
- Using a monotonic deque when items leave in arbitrary order rather than oldest first
systems:
- Lemire's streaming maximum-minimum filter (2006) keeps two monotonic double-ended queues and needs at most three comparisons per element for running window maxima and minima
- Andrew's monotone chain convex hull keeps each half of the hull on a stack and pops points that would make a wrong turn: the same pop-until-valid loop, after a sort
- A Cartesian tree (used for range-minimum queries) is built in linear time by keeping its right spine on a stack and popping larger values, exactly the previous-smaller pass
further:
- Chapter · 20 min | Competitive Programmer's Handbook 8.2 and 8.3: nearest smaller elements and sliding window minimum | https://cses.fi/book/book.pdf#page=89
- Article · 15 min | cp-algorithms: minimum queue and the minimum of all fixed-length subarrays | https://cp-algorithms.com/data_structures/stack_queue_modification.html#queue-modification-method-1
- Article · 10 min | Wikipedia: all nearest smaller values, the sequential stack algorithm | https://en.wikipedia.org/wiki/All_nearest_smaller_values#Sequential_algorithm
- Article · 20 min | Lemire: streaming maximum-minimum filter using no more than three comparisons per element | https://arxiv.org/abs/cs/0610046
bank: mono
---

=== recap | Next greater element: the monotonic stack and its O(n) bound | 12 min
goal: Answer every nearest-greater or nearest-smaller question in one pass, choose the pop condition that handles duplicates, and prove the pass is O(n)
tag: mono-stack | Monotonic stack (nearest greater or smaller)
link: USACO Guide: Nearest smaller element | https://usaco.guide/gold/stacks#application---nearest-smaller-element | 10 min: 'Application - Nearest Smaller Element' and its implementation, the previous-smaller version of the same pass
practice: 496, 739, 503, 901

> [!key]
> Scan left to right with a stack of indices still waiting for their next greater element. When a value x arrives, every waiting element smaller than x has just found its answer: pop it and record x. Then push x. The waiting values never increase from bottom to top, which is what makes the stack **monotonic**, and each index is pushed once and popped at most once, so the whole pass is **O(n)**.

## Internals

- **Invariant.** After processing a[0..i], the stack holds exactly the indices j ≤ i with no greater element in (j, i], in index order, and their values are non-increasing from bottom to top. (If j < j' were both on the stack with a[j] < a[j'], then a[j'] would be a greater element after j, and j would already have been popped.)
- **Why the pop is correct.** When x = a[i] pops j, x > a[j], and nothing between j and i was greater than a[j], or it would have popped j earlier. So x is the *first* greater element. Stopping at the first top that is at least x is safe, because everything below it is at least as large. Indices still on the stack at the end have no greater element.
- **Why it is O(n).** The inner `while` looks quadratic, so count pops instead of iterations. Each index is pushed once and popped at most once, so all the inner loops together pop at most n times. Total work: n pushes, at most n pops, and n comparisons that end a while loop, at most 3n steps. With a potential function, let Φ be the stack size: a step with p pops costs 1 + p and changes Φ by 1 - p, so cost plus change in Φ is always 2. A single step can still pop O(n): on 5, 4, 3, 2, 1, 6 the last value pops five.
- **Variants** (flip every comparison for smaller):

| Question | Pop while | Answer is |
|---|---|---|
| next greater | `a[top] < x` | x, for each popped index |
| next greater or equal | `a[top] <= x` | x, for each popped index |
| previous greater | `a[top] <= x` | the top after popping, or -1 |
| previous greater or equal | `a[top] < x` | the top after popping, or -1 |

- **Shapes of the same pass.** Distances instead of values (days until warmer): record `i - j` at pop time. Circular arrays: loop i over 0 to 2n - 1 using `a[i % n]` and push only during the first lap. Online spans: store `(price, span)` pairs and add each popped span to today's, because the days a popped price covered are covered by today too.

## Template

```python
def next_greater(a):
    """ans[i] = first value to the right of i that is greater than a[i], or -1."""
    ans = [-1] * len(a)
    stack = []                          # indices still waiting; their values never increase upwards
    for i, x in enumerate(a):
        while stack and a[stack[-1]] < x:
            ans[stack.pop()] = x        # x is the first greater value for that index
        stack.append(i)
    return ans


def prev_greater(a):
    """Index of the nearest element to the left that is > a[i], or -1."""
    res, stack = [-1] * len(a), []
    for i, x in enumerate(a):
        while stack and a[stack[-1]] <= x:
            stack.pop()                 # can never be anyone's previous greater again
        res[i] = stack[-1] if stack else -1
        stack.append(i)
    return res


class StockSpanner:
    def __init__(self):
        self.stack = []                 # (price, span); prices strictly decrease upwards

    def next(self, price):
        span = 1
        while self.stack and self.stack[-1][0] <= price:
            span += self.stack.pop()[1]  # absorb the days that price covered
        self.stack.append((price, span))
        return span
```

## Worked example

```steps
i = 0, x = 5: the stack is empty, nothing to resolve; push index 0 (shown as index:value)
    index    0   1   2   3   4   5
    a        5   3   1   4   2   6
    ans     -1  -1  -1  -1  -1  -1
    stack   [{{0:5}}]
---
i = 1, x = 3: the top 5 is not smaller, so nothing is resolved; push
    ans     -1  -1  -1  -1  -1  -1
    stack   [0:5, {{1:3}}]
---
i = 2, x = 1: push. Values 5, 3, 1 never increase upwards: the invariant
    ans     -1  -1  -1  -1  -1  -1
    stack   [0:5, 1:3, {{2:1}}]
---
i = 3, x = 4: 1 < 4, pop index 2 and record 4; 3 < 4, pop index 1 and record 4; 5 is not smaller, stop; push
    ans     -1  {{ 4}}  {{ 4}}  -1  -1  -1
    stack   [0:5, {{3:4}}]
---
i = 4, x = 2: the top 4 is not smaller; push
    ans     -1   4   4  -1  -1  -1
    stack   [0:5, 3:4, {{4:2}}]
---
i = 5, x = 6: pops indices 4, 3 and 0 in turn, recording 6 for each; push 5
    ans     {{ 6}}   4   4  {{ 6}}  {{ 6}}  -1
    stack   [{{5:6}}]
---
End: index 5 was never popped, so it has no greater element and keeps -1. Six pushes, five pops
    ans      6   4   4   6   6  -1
    stack   [5:6]
```

## Pitfalls

- Storing values instead of indices: you cannot fill answers by position or compute distances.
- Strictness with duplicates: `<` versus `<=` decides whether an equal value counts. Test on `[2, 2]`.
- Circular arrays: push only in the first lap (pushing again in the second lap is wasted work), and never push `i` itself past n - 1.
- Forgetting the default for indices never popped: -1 for values, 0 for distances.

## Quick check

Q: Run `next_greater` on `[2, 7, 3, 5, 4, 6, 8]`. Which indices does the value 6 pop, and what is the final answer list?
A: At 6 the stack holds indices 1, 3, 4 (values 7, 5, 4); 6 pops index 4 and then index 3, and stops at 7. The final answers are `[7, 8, 5, 6, 6, 8, -1]`.

> [!know]
> You now know how to answer nearest greater or smaller questions in one pass and prove the pass is O(n) by counting pops.

=== recap | Largest rectangle in a histogram | 12 min
goal: Find the largest rectangle under a histogram in one pass by reading each bar's left and right limits at the moment it is popped
tag: mono-histogram | Rising stack of bars (histogram)
link: Competitive Programmer's Handbook, section 8.2 | https://cses.fi/book/book.pdf#page=89 | 10 min: 'Nearest smaller elements' (book page 79, PDF page 89), the stack pass and its amortised argument that this card builds on
practice: 84, 85

> [!key]
> The best rectangle has some bar as its shortest bar, and with that bar fixed it spreads left and right until a lower bar stops it. Keep a stack of bars with increasing heights. When a lower bar arrives, the bar on top is popped, and at that moment both of its limits are known: the arriving bar on the right and the bar below it in the stack on the left. One pass, O(n).

## Internals

- **From brute force.** For each bar, walk outwards to the nearest lower bar on each side: O(n^2). Those limits are exactly the previous smaller and next smaller elements, so two monotonic passes give O(n); the one-pass version reads both limits at pop time.
- **Invariant.** The stack holds indices with strictly increasing heights (an equal bar pops its twin). For the top bar t, the bar below it, `left`, is the nearest bar to the left of t that is lower, and every bar strictly between them is at least as tall as t.
- **Width at pop time.** When bar i pops t, `heights[i] <= heights[t]`, and every bar between t and i is at least `heights[t]` tall (a lower one would have popped t first). So a rectangle of height `heights[t]` fits across the open interval (left, i): width `i - left - 1`.
- **Duplicates.** With `>=`, an equal bar pops its twin, and the twin may record a width that is too short. That is harmless: take any optimal rectangle and its *rightmost* shortest bar. That bar is popped by a strictly lower bar (or the sentinel), and its left limit is exact, so its full width is recorded. Popping only on `>` is also correct; then the leftmost shortest bar gets the full width.
- **Sentinel.** Appending a height-0 bar pops everything at the end, so no second loop is needed.
- **In 2D** (Maximal Rectangle): for each row, let `heights[c]` count the consecutive 1s ending at that row in column c; each row is then a histogram, so run the pass per row for O(rows × cols).
- **Cost.** Each index is pushed and popped once: O(n) time, O(n) space for the stack.

## Template

```python
def largest_rectangle(heights):
    stack = []                          # indices of bars with increasing heights
    best = 0
    for i, h in enumerate(heights + [0]):           # the 0 flushes every bar at the end
        while stack and heights[stack[-1]] >= h:
            top = stack.pop()                       # i is the first bar right of top that is not taller
            left = stack[-1] if stack else -1       # nearest bar left of top that is lower
            best = max(best, heights[top] * (i - left - 1))
        stack.append(i)
    return best


def maximal_rectangle(grid):
    if not grid:
        return 0
    heights, best = [0] * len(grid[0]), 0
    for row in grid:
        heights = [h + 1 if c == "1" else 0 for h, c in zip(heights, row)]
        best = max(best, largest_rectangle(heights))
    return best
```

## Worked example

```steps
Heights 2, 4, 5, 3, 1, 3. The answer is 9: height 3 across bars 1 to 3. i = 0: push bar 0
                #
            #   #
            #   #   #       #
        #   #   #   #       #
        #   #   #   #   #   #
        0   1   2   3   4   5
    stack [{{0}}]   heights on stack 2   best 0
---
i = 1 (h 4) and i = 2 (h 5): each is taller than the top, so both are pushed
    stack [0, 1, {{2}}]   heights on stack 2 4 5   best 0
---
i = 3 (h 3): pop bar 2 (h 5, left 1, width 3 - 1 - 1 = 1, area 5), then bar 1 (h 4, left 0, width 2, area 8); push 3
    stack [0, {{3}}]   heights on stack 2 3   best {{8}}
---
i = 4 (h 1): pop bar 3 (h 3, left 0, width 4 - 0 - 1 = 3, area 9), then bar 0 (h 2, left -1, width 4, area 8); push 4
    stack [{{4}}]   heights on stack 1   best {{9}}
---
i = 5 (h 3): taller than the top, push
    stack [4, {{5}}]   heights on stack 1 3   best 9
---
i = 6 is the sentinel 0: pop bar 5 (h 3, left 4, width 1, area 3), then bar 4 (h 1, left -1, width 6, area 6). Answer 9
    stack [{{6}}]   heights on stack 0   best 9
```

## Pitfalls

- Width off by one: it is `i - left - 1` with `left = -1` when the stack is empty, not `i - top`.
- No final flush: without the sentinel, `[1, 2, 3]` never pops and returns 0 instead of 4.
- Appending the sentinel to the caller's list mutates it; `heights + [0]` makes a copy.
- In other languages, `height * width` can overflow 32-bit integers.

## Quick check

Q: In the trace, why is the area for bar 3 (height 3) computed at i = 4 and not earlier, and which limits does it get?
A: A bar stays on the stack until a bar no taller than it arrives, and bar 4 (height 1) is the first. At that moment the bar below it in the stack is bar 0 (height 2), so its rectangle spans bars 1 to 3: width 4 - 0 - 1 = 3, area 9.

> [!know]
> You now know how to find every bar's limits with one rising stack and turn them into the largest rectangle in O(n).

=== recap | Contribution counting: sum of subarray minimums | 12 min
goal: Sum the minimum (or maximum) over all subarrays in O(n) by counting how many subarrays each element is credited with, using one strict and one non-strict boundary
tag: mono-contrib | Contribution counting with nearest smaller
link: Wikipedia: All nearest smaller values | https://en.wikipedia.org/wiki/All_nearest_smaller_values#Sequential_algorithm | 5 min: 'Sequential algorithm', the stack pass that finds each element's nearest smaller neighbour
practice: 907

> [!key]
> Instead of visiting all n(n + 1)/2 subarrays, turn the sum around: each element a[i] is the minimum of a whole block of subarrays, those that start after its previous smaller element and end before its next smaller element. Count that block with two monotonic passes, multiply by a[i], add up: O(n). With equal values, make one side strict and the other non-strict, so every subarray's minimum is credited to exactly one position.

## Internals

- **The block.** Let L be the index of the previous element *strictly* smaller than a[i] (or -1), and R the index of the next element *smaller than or equal to* a[i] (or n). Every subarray that starts in (L, i] and ends in [i, R) has a[i] as its minimum, and a[i] is its *rightmost* minimum: values between L and i are at least a[i], values between i and R are greater. There are `(i - L) * (R - i)` such subarrays (choices of start times choices of end).
- **Exactly once.** Every subarray has exactly one rightmost minimum, so the blocks partition all subarrays: the counts add up to n(n + 1)/2. With both sides strict, a subarray containing two equal minima is credited to both: `[2, 2]` would give 8 instead of 6. With both non-strict, it is credited to neither.
- **Two passes.** Previous strictly smaller: scan left to right, popping while `a[top] >= a[i]`. Next smaller or equal: scan right to left, popping while `a[top] > a[i]`. Each is the monotonic stack pass, so O(n) time and space in total.
- **One pass.** When index j is popped by i (with `a[i] <= a[j]`), i is j's right limit and the new top is its left limit; add `a[j] * (j - left) * (i - j)` and flush with a minus-infinity sentinel.
- **Relatives.** Flip the comparisons to sum maxima; sum of subarray ranges (in the problem bank) is the sum of maxima minus the sum of minima. "Fix the element that is the minimum, find its block" also drives problems that combine the minimum with a range sum (add prefix sums).
- **Modulo.** The answer to the practice problem is taken modulo 10^9 + 7. Python integers never overflow, so reduce at the end; in C++ or Java use 64-bit arithmetic and reduce every product.

## Template

```python
def sum_subarray_mins(a):
    n = len(a)
    left, right = [0] * n, [0] * n
    stack = []
    for i in range(n):                  # previous strictly smaller
        while stack and a[stack[-1]] >= a[i]:
            stack.pop()
        left[i] = i - (stack[-1] if stack else -1)
        stack.append(i)
    stack = []
    for i in range(n - 1, -1, -1):      # next smaller or equal
        while stack and a[stack[-1]] > a[i]:
            stack.pop()
        right[i] = (stack[-1] if stack else n) - i
        stack.append(i)
    return sum(x * l * r for x, l, r in zip(a, left, right))
```

## Worked example

For `a = [3, 1, 2, 1]` (ten subarrays):

```text
index                    0    1    2    3
a                        3    1    2    1
L: prev strictly smaller -1   -1    1   -1
R: next smaller or equal  1    3    3    4
i - L                     1    2    1    4
R - i                     1    2    1    1
subarrays credited        1    4    1    4    total 10 = 4 * 5 / 2
contribution              3    4    2    4    sum 13
```

Index 1 is credited with `[1]`, `[3, 1]`, `[1, 2]` and `[3, 1, 2]`: its block stops before index 3, the equal 1. The two subarrays containing both 1s, `[1, 2, 1]` and `[3, 1, 2, 1]`, go to index 3, their rightmost minimum. A brute force over all ten subarrays also gives 13.

## Pitfalls

- Same strictness on both sides: double counting (both strict) or missing subarrays (both non-strict). Test on `[2, 2]` (answer 6) and `[1, 1, 1]` (answer 6).
- Off by one: the count of starts is `i - L`, not `i - L - 1`.
- Swapping which pass gets the strict comparison is fine, as long as the two passes differ.

## Quick check

Q: For `a = [2, 2]`, compute L, R and the count for each index with the template's rules, and show that the total is 6.
A: Index 0: no previous strictly smaller (L = -1), next smaller or equal is index 1 (R = 1), so it gets 1 × 1 = 1 subarray, `[2]`. Index 1: L = -1, R = 2, so 2 × 1 = 2 subarrays, `[2, 2]` and the second `[2]`. Total 2 × (1 + 2) = 6, which matches 2 + 2 + 2.

> [!know]
> You now know how to sum a minimum or maximum over all subarrays by crediting each one to a single element, ties included.

=== recap | Monotonic deque: the maximum of every window | 12 min
goal: Report the maximum or minimum of every sliding window in O(n) with a deque of candidates, and adapt the idea to two-sided limits and to prefix sums
tag: mono-deque | Monotonic deque (window extremes)
link: USACO Guide: Sliding window maximum with a deque | https://usaco.guide/gold/sliding-window#method-1---deque | 10 min: 'Method 1 - Deque', then 'Method 2 - Two Stacks' for the alternative built from two max-stacks
practice: 239, 1438, 862

> [!key]
> Keep a deque of indices whose values strictly decrease from front to back. A new value first drops every smaller or equal value from the back (they are older and no larger, so they can never be a window maximum again), then joins at the back; the front leaves when it slides out of the window. The front is always the window maximum, and each index enters and leaves once: O(n) total, O(k) space.

## Internals

- **Dominance.** If j < i and a[j] <= a[i], then j leaves every future window before i does and is never larger, so j is useless from now on. Removing all dominated indices leaves candidates with decreasing values, and the oldest surviving candidate is the largest.
- **Invariant.** After step i, the deque holds, in increasing index order, exactly the indices j in the window [i - k + 1, i] whose value is greater than every later value in the window. Their values strictly decrease, so the front is the maximum.
- **Expiry.** The window moves one step at a time, so at most one index, the oldest, expires per step: check `dq[0] <= i - k` before reading the front.
- **Cost.** n appends, at most n pops from the back and n from the front: O(n). On random data almost every index leaves from the back; only about n/k expire from the front (the lab measures this).
- **Both extremes** (longest subarray whose max - min is within a limit): keep a decreasing deque for the maximum and an increasing one for the minimum under a grow-and-shrink window; while the fronts differ by more than the limit, advance the left edge and drop fronts that fall behind it.
- **On prefix sums** (shortest subarray with sum at least K, negatives allowed): keep start indices with increasing prefix sums. Pop the front while the current prefix minus it reaches K, recording the length (a later end could only be longer for that start), and pop the back while its prefix is at least the current one (a later, lower start is strictly better).
- **Alternatives.** A heap of `(-value, index)` with lazy deletion (pop the top while it has expired) is O(n log n) and hard to get wrong. A queue made of two max-stacks gives amortised O(1) per step. A sparse table answers arbitrary ranges on fixed data, not just sliding ones.

## Template

```python
from collections import deque


def window_max(a, k):
    dq = deque()                        # indices in the window; values strictly decrease front to back
    out = []
    for i, x in enumerate(a):
        if dq and dq[0] <= i - k:
            dq.popleft()                # the front slid out of the window
        while dq and a[dq[-1]] <= x:
            dq.pop()                    # older and not larger: can never be a maximum again
        dq.append(i)
        if i >= k - 1:
            out.append(a[dq[0]])
    return out


def shortest_subarray_at_least(a, k):
    """Shortest non-empty subarray with sum >= k (negatives allowed), or -1."""
    pre = [0]
    for x in a:
        pre.append(pre[-1] + x)
    best, dq = len(a) + 1, deque()      # candidate starts j with increasing pre[j]
    for i, p in enumerate(pre):
        while dq and p - pre[dq[0]] >= k:
            best = min(best, i - dq.popleft())   # no later end can give this start a shorter answer
        while dq and pre[dq[-1]] >= p:
            dq.pop()                    # i is a later and lower start: strictly better
        dq.append(i)
    return best if best <= len(a) else -1
```

## Worked example

```steps
a = 9 7 8 3 6 2 5 1, k = 3. i = 0 and i = 1: 9 and 7 join; 9 > 7, so both stay as candidates
    index    0   1   2   3   4   5   6   7
    a        9   7   8   3   6   2   5   1
    deque   [0:9, {{1:7}}]           out []
---
i = 2, x = 8: 7 <= 8, so drop index 1 from the back; append 2. First full window [0, 2]: the front gives 9
    deque   [0:9, {{2:8}}]           out [{{9}}]
---
i = 3, x = 3: index 0 is now outside the window [1, 3], so it expires from the front; append 3. Max 8
    deque   [{{2:8}}, 3:3]           out [9, {{8}}]
---
i = 4, x = 6: drop index 3 (3 <= 6) from the back; 8 > 6 stays. Max of window [2, 4] is still 8
    deque   [2:8, {{4:6}}]           out [9, 8, {{8}}]
---
i = 5, x = 2: index 2 expires from the front; append 5. The next candidate, 6, becomes the maximum
    deque   [{{4:6}}, 5:2]           out [9, 8, 8, {{6}}]
---
i = 6, x = 5: drop index 5 (2 <= 5); 6 stays. Max 6
    deque   [4:6, {{6:5}}]           out [9, 8, 8, 6, {{6}}]
---
i = 7, x = 1: index 4 expires; append 7. Max 5. Eight appends, three drops, three expiries
    deque   [{{6:5}}, 7:1]           out [9, 8, 8, 6, 6, {{5}}]
```

## Pitfalls

- Storing values in the deque: you cannot tell when they expire. Store indices.
- Reading the front before expiring it, or emitting output before the first full window (`i >= k - 1`).
- `<` versus `<=` when dropping from the back: both give correct maxima; `<=` keeps fewer equal values.
- Using a plain sliding window when values can be negative: growing the window no longer only increases the sum, which is why the prefix-sum deque exists.

## Quick check

Q: In the trace, why does index 2 (value 8) survive the arrival of 6 at i = 4, while index 3 (value 3) is dropped?
A: 3 is not larger than 6 and index 3 is older, so it can never be a window maximum again. 8 is larger than 6, so it is still the maximum of the window [2, 4]; it leaves only when it expires at i = 5.

> [!know]
> You now know how to maintain window maxima and minima with a monotonic deque, and how to extend it to prefix sums.

=== recap | Recognising monotonic structure, and when a heap is simpler | 10 min
goal: Spot problems that hide a monotonic stack or deque, including greedy smallest-result and fleet problems, and choose a heap or sorted container when the monotonic argument fails
tag: mono-greedy | Greedy pops on a monotonic stack
link: Python docs: heapq, priority queue implementation notes | https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes | 5 min: marking entries as removed and skipping them when popped (lazy deletion), the usual alternative when items leave in any order
practice: 402, 853

> [!key]
> Reach for a monotonic stack when an element becomes useless *forever* as soon as a better one arrives after it: a larger value for next greater, a smaller digit for the smallest number, a slower car ahead for fleets. If a discarded element could matter again, because items leave in arbitrary order or you need the k-th best rather than the best, the structure is not monotonic: use a heap or a sorted container.

## Internals

| You read | Think |
|---|---|
| next or previous greater or smaller, days until warmer, consecutive days before | monotonic stack; answer at pop time or after popping |
| until a taller one blocks the view, visible people, skylines | monotonic stack scanned from the blocking side |
| sum of min or max over all subarrays, largest rectangle | nearest smaller on both sides, then contribution or width |
| maximum or minimum of every window, best of the last k states | monotonic deque |
| remove k digits or letters for the smallest result | increasing stack, pop larger items while removals remain |
| objects that cannot overtake (fleets, collisions) | sort by position, keep a stack of groups |

- **Greedy pops.** For the smallest number after removing k digits, the most valuable removal is the first digit that is followed by a smaller one: deleting it lowers the most significant place that can change. The stack keeps a non-decreasing prefix, and each new digit pops larger digits while removals remain. Leftover removals come off the end, where the kept digits are largest.
- **Fleets.** Sort cars by position from the target backwards. A car whose solo arrival time is no later than the fleet in front catches it and merges; only a strictly later time starts a new fleet. Only the top of that stack is ever compared, so it collapses to one variable.
- **When a heap is simpler.**

| Situation | Use |
|---|---|
| Items expire strictly oldest first (sliding windows) | monotonic deque, O(n) |
| Items leave in any order (intervals end, deletions by key) | heap with lazy deletion, O(n log n) |
| You need the k-th best or the top k, not just the best | heap, or `sortedcontainers.SortedList` |
| Arbitrary range queries on fixed data | sparse table or segment tree |
| n is small or the code must be obviously right | brute force or a heap first, then optimise if measured |

## Template

```python
def remove_k_digits(num, k):
    stack = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()                 # a larger digit before a smaller one: drop it
            k -= 1
        stack.append(d)
    if k:
        stack = stack[:-k]              # still owe removals: the tail is non-decreasing, cut the end
    return "".join(stack).lstrip("0") or "0"


def car_fleet(target, position, speed):
    fleets = 0
    lead_d = lead_s = None              # the fleet ahead arrives at time lead_d / lead_s
    for p, s in sorted(zip(position, speed), reverse=True):
        d = target - p
        if fleets == 0 or d * lead_s > lead_d * s:   # arrives strictly later: cannot catch up
            fleets += 1
            lead_d, lead_s = d, s
    return fleets
```

## Worked example

```steps
Remove k = 3 digits from 5283419. Digit 5: the stack is empty, push
    stack   {{5}}       k 3
---
Digit 2: 5 > 2, and removing the 5 makes the leading digit smaller, so pop it; push 2
    stack   {{2}}       k 2
---
Digit 8: no larger digit to pop; push
    stack   2 {{8}}     k 2
---
Digit 3: 8 > 3, pop 8; 2 < 3 stops; push 3
    stack   2 {{3}}     k 1
---
Digit 4: push
    stack   2 3 {{4}}   k 1
---
Digit 1: 4 > 1, pop it; now k is 0, so 3 stays even though it is larger; push 1
    stack   2 3 {{1}}   k 0
---
Digit 9: push. No removals are owed, no leading zeros: the answer is 2319
    stack   2 3 1 {{9}} k 0
```

## Pitfalls

- Removal problems: leftover k (cut from the end), leading zeros (strip them) and an empty result (return "0").
- Floating-point arrival times can make equal times compare unequal; compare `d1 * s2` with `d2 * s1` in integers, as the template does.
- Applying a monotonic structure when the "useless forever" argument fails, such as the largest value among intervals that end in arbitrary order.

## Quick check

Q: Why can a monotonic deque not maintain the maximum of a set from which arbitrary elements are deleted?
A: It discards an element as soon as a larger, newer one arrives, which is safe only if the newer one is guaranteed to stay at least as long. With arbitrary deletions the newer element may be deleted first, and the discarded one would be needed again. A heap with lazy deletion, or a sorted container, keeps every element and copes.

> [!know]
> You now know how to recognise monotonic structure from a problem statement, and when to choose a heap instead.

=== lab | Count the pops: measuring the amortised bound | 40 min
goal: Instrument next-greater and window-maximum, confirm that pushes and pops never exceed n on any input shape, and stress-test both against O(n^2) versions
link: Competitive Programmer's Handbook, sections 8.2 and 8.3 | https://cses.fi/book/book.pdf#page=89 | 20 min: book pages 79 to 82 (PDF 89 to 92), the stack and deque passes with their amortised proofs

The "while inside a for" shape makes many people guess O(n^2). Here you count the operations instead: four input shapes, doubling sizes, and a brute-force oracle to prove the fast versions right first. If you built the `dsakit` stress runner in the correctness module, plug these functions into it; the code below is self-contained.

## Steps

1. Save this as `count_pops.py`.

```python
import random
import time
from collections import deque


def next_greater_counted(a):
    ans, stack = [-1] * len(a), []
    pushes = pops = 0
    for i, x in enumerate(a):
        while stack and a[stack[-1]] < x:
            ans[stack.pop()] = x
            pops += 1
        stack.append(i)
        pushes += 1
    return ans, pushes, pops


def window_max_counted(a, k):
    dq, out = deque(), []
    pushes = drops = expiries = 0
    for i, x in enumerate(a):
        if dq and dq[0] <= i - k:
            dq.popleft()
            expiries += 1
        while dq and a[dq[-1]] <= x:
            dq.pop()
            drops += 1
        dq.append(i)
        pushes += 1
        if i >= k - 1:
            out.append(a[dq[0]])
    return out, pushes, drops, expiries


def next_greater_slow(a):
    n = len(a)
    return [next((a[j] for j in range(i + 1, n) if a[j] > a[i]), -1) for i in range(n)]


def window_max_slow(a, k):
    return [max(a[i:i + k]) for i in range(len(a) - k + 1)]


INPUTS = {
    "random": lambda n, rng: [rng.randint(0, 10**6) for _ in range(n)],
    "increasing": lambda n, rng: list(range(n)),
    "decreasing": lambda n, rng: list(range(n, 0, -1)),
    "all equal": lambda n, rng: [7] * n,
}


def stress(trials=3000, seed=1):
    rng = random.Random(seed)
    for _ in range(trials):
        n = rng.randint(0, 40)
        a = [rng.randint(0, 5) for _ in range(n)]
        assert next_greater_counted(a)[0] == next_greater_slow(a)
        if n:
            k = rng.randint(1, n)
            assert window_max_counted(a, k)[0] == window_max_slow(a, k)
    print(f"stress: {trials} random arrays agree with the O(n^2) versions")


if __name__ == "__main__":
    stress()
    rng = random.Random(0)
    k = 100
    print(f"{'input':>11} {'n':>8} | NGE pushes   pops | window pushes  drops  expiries | NGE ms  window ms")
    for name, make in INPUTS.items():
        for n in (100_000, 200_000, 400_000, 800_000):
            a = make(n, rng)
            t0 = time.perf_counter()
            _, p1, q1 = next_greater_counted(a)
            t1 = time.perf_counter()
            _, p2, d2, e2 = window_max_counted(a, k)
            t2 = time.perf_counter()
            assert q1 <= p1 == n and d2 + e2 <= p2 == n
            print(f"{name:>11} {n:>8} | {p1:>10} {q1:>6} | {p2:>13} {d2:>6} {e2:>9} | "
                  f"{(t1 - t0) * 1e3:6.0f} {(t2 - t1) * 1e3:10.0f}")
```

2. Before running it, write down your prediction of the pops for next greater and of the drops and expiries for the window, for each of the four input shapes.
3. Run `python3 count_pops.py`. The stress test must pass before you trust any count.
4. Plot (or just tabulate) pushes plus pops against n for each shape, and the time ratio between consecutive sizes.
5. Break the window code on purpose: move the expiry check after the `append`, and change `<=` to `<` in the drop loop. Which change breaks correctness, and which only changes the counts? Use the stress test to check your answer.
6. Optional: add a lazily deleted heap version of the window maximum and time it against the deque at n = 800,000.

## What you should see

- Pushes always equal n, and pops (or drops plus expiries) never exceed n, on every shape: the amortised bound in numbers.
- Next greater: increasing input pops n - 1 times (every new value resolves the previous one); decreasing and all-equal input never pop; random input pops all but a handful (the elements left are the ones with nothing greater to their right, about ln n of them, roughly a dozen here).
- Window maximum with k = 100: increasing and all-equal input drop n - 1 from the back and expire nothing; decreasing input drops nothing and expires n - k from the front; random input drops about 99% of indices and expires about n/k, because an element survives to expire only if it is the largest of the k values starting at it, which happens with probability about 1/k.
- Time roughly doubles when n doubles (about 30 to 50 ms for next greater at 100,000 on the machine used here; single runs on a busy machine are noisy, so repeat and take the minimum). No column grows four-fold.
- Moving the expiry check after the append is still correct (the newly appended index can never be the expired one when k is at least 1); changing `<=` to `<` is also correct but keeps equal values, so on all-equal input nothing is dropped and n - k indices expire from the front instead.

## Check yourself

Q: On decreasing input with k = 100, why do almost all indices leave through the front of the deque, and does that change the O(n) bound?
A: Each new value is smaller than everything in the deque, so nothing is ever dropped from the back; indices leave only when they slide out of the window, n - k of them. The bound is unchanged: every index is still appended once and removed at most once, whichever end it leaves by.

=== practice
- 496 core
  cue: For each value in a short query list, report the first larger value to its right in a longer list.
  hint: Answer the question once for every element of the longer list, then look the queries up.
  insight: One pass over the longer list with a stack of values still waiting; each new value pops every smaller waiting value and is its next greater. Store those answers in a dict (values are distinct) and map each query through it, defaulting to -1.
  cost: O(n + m) time, O(n) space
  pattern: mono-stack
- 739 core
  cue: For each day, how many days until a strictly warmer one.
  hint: Think about the days that have not found a warmer day yet. In what order are their temperatures?
  insight: Keep a stack of indices of days still waiting; their temperatures never increase upwards. A warmer day i pops each cooler waiting day j and sets answer[j] = i - j; days never popped keep 0.
  cost: O(n) time, O(n) space
  pattern: mono-stack
- 503 core
  cue: The next larger value for each element when the array wraps around at the end.
  hint: Wrapping means an element's answer may lie before it. How far past the end do you need to look?
  insight: Run the usual next-greater pass over i from 0 to 2n - 1 using a[i % n], but push indices only during the first lap; the second lap only resolves elements still waiting. Whatever is never popped (the maximum values) keeps -1.
  cost: O(n) time, O(n) space
  pattern: mono-stack
- 901 core
  cue: Prices arrive one at a time; for each, report how many consecutive days up to today had a price no higher than today's.
  hint: Once a higher price arrives, the cheaper days just before it are covered by it for every future query.
  insight: Keep (price, span) pairs with strictly decreasing prices. For a new price, pop every pair whose price is at most today's and add its span to today's span (which starts at 1), then push (price, span). Each day is pushed and popped once.
  cost: O(1) amortised per call, O(n) space
  pattern: mono-stack
- 402 core
  cue: Delete exactly k digits from a number written as a string so the result is as small as possible.
  hint: Compare two neighbouring digits. When is deleting the left one clearly the best possible move?
  insight: Scan with a stack kept non-decreasing: while removals remain and the top digit is greater than the new digit, pop it. If removals are still owed at the end, cut them from the end. Strip leading zeros and return "0" if nothing is left.
  cost: O(n) time, O(n) space
  pattern: mono-greedy
- 853 derive
  cue: Cars on a single lane cannot pass each other; count the groups that reach the target.
  hint: Process cars starting from the one closest to the target. When does a car end up in the group ahead of it?
  insight: Sort by position, closest to the target first, and compute each car's arrival time if it drove alone. A car whose time is no later than the fleet ahead catches it and merges; a strictly later time starts a new fleet. Only the latest fleet's time matters; compare d1 * s2 with d2 * s1 to avoid float ties.
  cost: O(n log n) time for the sort, O(n) space
  pattern: mono-greedy
- 907 derive
  cue: Add up the minimum of every contiguous subarray, with n in the tens of thousands.
  hint: Flip the sum around: for one element, in how many subarrays is it the minimum?
  insight: a[i] is the credited minimum of every subarray that starts after its previous strictly smaller element and ends before its next smaller-or-equal element, so it adds a[i] * (i - L) * (R - i). Find L and R with two monotonic stack passes; the mixed strictness counts tied minima once. Reduce modulo 10^9 + 7.
  cost: O(n) time, O(n) space
  pattern: mono-contrib
- 84 core
  cue: The largest rectangle that fits under a row of adjacent bars of different heights.
  hint: Fix which bar is the shortest one in the rectangle. How far can the rectangle spread from it?
  insight: Keep a stack of bar indices with increasing heights and append a height-0 sentinel. When bar i pops index t, i is t's right limit and the new top is its left limit, so the area is heights[t] * (i - left - 1) with left = -1 for an empty stack; keep the maximum.
  cost: O(n) time, O(n) space
  pattern: mono-histogram
- 239 core
  cue: The maximum of each window of length k as it slides one position at a time.
  hint: If an element is older than another and no larger, can it ever be a window's maximum again?
  insight: Keep a deque of indices with strictly decreasing values. Drop the front when it leaves the window, drop from the back while values are at most the new one, append the new index; once i >= k - 1 the front holds the window maximum.
  cost: O(n) time, O(k) space
  pattern: mono-deque
- 1438 stretch
  cue: The longest contiguous stretch in which the largest and smallest values differ by at most a limit.
  hint: A grow-and-shrink window works if you can read the window's maximum and minimum quickly at every step.
  insight: Keep a decreasing deque for the maximum and an increasing deque for the minimum. Extend the right edge; while front(max) - front(min) exceeds the limit, advance the left edge and drop deque fronts that fall behind it. Record the window length at each step.
  cost: O(n) time, O(n) space
  pattern: mono-deque
- 862 stretch
  cue: The shortest subarray whose sum reaches a target when values can be negative.
  hint: A plain sliding window fails with negatives. Rewrite subarray sums with prefix sums: which earlier prefixes are still worth remembering?
  insight: Over prefix sums P, keep a deque of start indices with increasing P. For each i, pop the front while P[i] - P[front] >= K (record i - front; later ends would only be longer), pop the back while P[back] >= P[i] (a later, lower start dominates), then append i.
  cost: O(n) time, O(n) space
  pattern: mono-deque
- 85 stretch
  cue: The largest rectangle containing only 1s in a binary grid.
  hint: Look at the grid one row at a time. What does a row look like together with the 1s stacked above it?
  insight: Keep heights[c] = the number of consecutive 1s ending at the current row in column c (reset to 0 on a 0). Each row is then a histogram, so run the largest-rectangle stack pass on it and keep the maximum over all rows.
  cost: O(rows * cols) time, O(cols) space
  pattern: mono-histogram
