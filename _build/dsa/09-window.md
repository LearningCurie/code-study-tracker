---
key: window
name: Sliding window
stage: scan
summary: Keep a contiguous window and a small summary of it, move both edges only forward, and longest, shortest and counting questions over subarrays drop from O(n^2) to O(n), as long as validity is monotone.
why: "Longest substring with...", "shortest subarray whose sum...", "how many subarrays..." all have an O(n^2) brute force over every (start, end) pair. A sliding window turns that into one O(n) pass because each element enters the window once and leaves it at most once. The same mechanics run systems you use every day: rate limiters count requests in the last minute, monitoring dashboards compute rolling rates, TCP lets a sender keep only a window of unacknowledged bytes in flight, and stream processors aggregate events over sliding time windows. The part that separates a correct O(n) solution from a subtly wrong one is knowing when the window is allowed at all: validity must be monotone, which fails as soon as values can be negative or the target is an exact sum.
outcomes:
- Write fixed and variable windows from one template, updating sums, count maps or 26-slot arrays in O(1) per step
- State the monotone-validity condition a variable window needs, and show the counterexample with negative numbers
- Count valid subarrays with right - left + 1 per right end, and get "exactly K" as atMost(K) - atMost(K - 1)
- Find minimum covering windows with a counter of satisfied requirements instead of comparing whole maps
- Recognise when a plain window fails and repair it with a monotonic deque, prefix sums, sorting or a fixed extra parameter
- Compute rolling metrics (requests per sliding minute, distinct users in five minutes) over a large log and compare them with the naive scan and with fixed-window counters
cues:
- "Longest", "shortest" or "how many" contiguous subarrays or substrings satisfying a condition
- A fixed window size k: sums, averages, maxima or letter counts over every block of k
- "At most K distinct", "contains all of", "without repeating", "after at most k changes"
- Non-negative values, or a property that can only get worse as the window grows
- Time-ordered events and a question about "the last N seconds"
traps:
- Using a window when values can be negative or the target is an exact sum: validity is not monotone, so use prefix sums
- Recording the answer before the window is repaired (longest) or after it stops being valid (shortest)
- Comparing whole count maps at every step instead of tracking how many requirements are satisfied
- Leaving zero counts in a dict and then using len(count) as the number of distinct keys
- Forgetting the empty-window and k <= 1 edge cases in product and counting windows
systems:
- Rate limiters: Cloudflare estimates a sliding minute from two fixed-window counters; a sliding log keeps a deque of timestamps; NGINX's limit_req uses a leaky bucket instead
- TCP flow control: the receiver advertises a window, and the sender may only have that many unacknowledged bytes in flight (RFC 9293, section 3.8.6)
- Monitoring: Prometheus' rate() and the <aggregation>_over_time() functions aggregate each series over a trailing range such as [5m]
- Stream processing: Apache Flink and Kafka Streams provide tumbling and sliding (hopping) windows over event streams
further:
- Chapter · 10 min | Competitive Programmer's Handbook, sections 8.1 and 8.3 (PDF pages 87-92) | https://cses.fi/book/book.pdf#page=87
- Article · 10 min | USACO Guide: sliding window minimum with a deque or two stacks | https://usaco.guide/gold/sliding-window#method-1---deque
- Article · 6 min | Cloudflare: 'Sliding windows to the rescue', rate limiting with two counters | https://blog.cloudflare.com/counting-things-a-lot-of-different-things/#:~:text=Sliding%20windows%20to%20the%20rescue
- Docs · 5 min | Apache Flink: sliding windows | https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/#sliding-windows
bank: window
---

=== recap | Fixed-size windows: one in, one out | 10 min
goal: Maintain a window aggregate (sum, count, letter counts) in O(1) per slide and detect windows that match a target multiset
tag: window-fixed | Fixed-size window
link: USACO Guide: Sliding Window | https://usaco.guide/gold/sliding-window#implementation | 4 min: the first 'Implementation' section keeps the window in a sorted container for O(log k) maximum per slide, the general fallback when the aggregate has no O(1) update
practice: 643, 567

> [!key]
> Adjacent windows of size k share k - 1 elements, so never recompute: add the element that enters, remove the one that leaves, and read the answer. Any aggregate with an inverse works this way (sum, count, letter counts, XOR). The first window costs O(k) and every slide O(1): O(n) in all instead of O(nk).

## Internals

- **Invariant**: after processing index `r` (with `r >= k - 1`), the state describes exactly `a[r - k + 1 .. r]`. Each step: add `a[r]`; if `r >= k`, remove `a[r - k]`; then read.
- **Aggregates without an inverse**, such as maximum and minimum, cannot be "un-added". Pair the window with a monotonic deque (O(1) amortised, a later card) or a sorted container (O(log k)).
- **Matching a multiset** (is some window a rearrangement of `p`?). Comparing two `Counter`s per slide costs O(alphabet) and allocates. Instead keep `diff[c] = window count - p's count` for each letter and a number `bad` of letters with `diff != 0`. A slide changes two letters, so `bad` changes in O(1), and a match is `bad == 0`.
- **Python specifics.** `sum(a[i:i + k])` inside a loop copies k references every time: O(nk). For a stream you cannot index back into, `collections.deque(maxlen=k)` keeps the last k items and drops the oldest automatically in O(1). Floating-point sums drift after millions of add-and-subtract steps; use integers (cents, milliseconds) or recompute the sum periodically.
- **Averages**: for a fixed k, maximise the sum and divide once at the end.

## Template

```python
def window_sums(a, k):
    """Sum of every length-k window, left to right (empty if k > len(a))."""
    if k > len(a):
        return []
    s = sum(a[:k])
    out = [s]
    for r in range(k, len(a)):
        s += a[r] - a[r - k]          # a[r] enters, a[r - k] leaves
        out.append(s)
    return out


def same_letter_windows(s, p):
    """Starts of the len(p)-long windows of s with exactly p's letter counts (letters a-z)."""
    k = len(p)
    if k == 0 or k > len(s):
        return []
    diff = [0] * 26                   # window count minus p's count, per letter
    for c in p:
        diff[ord(c) - 97] -= 1
    bad = sum(1 for d in diff if d)   # letters whose counts still differ
    out = []

    def bump(c, delta):
        nonlocal bad
        i = ord(c) - 97
        bad -= diff[i] != 0
        diff[i] += delta
        bad += diff[i] != 0

    for r, c in enumerate(s):
        bump(c, +1)
        if r >= k:
            bump(s[r - k], -1)
        if r >= k - 1 and bad == 0:
            out.append(r - k + 1)
    return out
```

## Worked example

Window sums of `[4, 2, 7, 1, 8, 3]` with k = 3; the highlighted cells are the current window.

```steps
First window a[0..2]: sum = 13, computed once in O(k)
    index      0    1    2    3    4    5
    a          {{4}}    {{2}}    {{7}}    1    8    3
---
Slide: 1 enters, 4 leaves: sum = 10 (best 13). One addition and one subtraction, whatever k is
    a          4    {{2}}    {{7}}    {{1}}    8    3
---
Slide: 8 enters, 2 leaves: sum = 16 (best 16). One addition and one subtraction, whatever k is
    a          4    2    {{7}}    {{1}}    {{8}}    3
---
Slide: 3 enters, 7 leaves: sum = 12 (best 16). One addition and one subtraction, whatever k is
    a          4    2    7    {{1}}    {{8}}    {{3}}
```

## Pitfalls

- Off-by-one: the first full window ends at `r = k - 1`; record only from there. If `k > n` there is no window at all.
- `ord(c) - 97` assumes lowercase ASCII letters; for general text use a dict and the same `bad` counter.
- Rebuilding the window's `Counter` or slice on every step quietly turns O(n) into O(nk).

## Quick check

Q: What does `same_letter_windows("cbabcacab", "abc")` return?
A: `[0, 2, 3, 6]`: the windows "cba", "abc", "bca" and "cab" each contain one a, one b and one c; "bab", "cac" and "aca" do not.

> [!know]
> You now know how to slide a fixed window in O(1) per step and match windows against a multiset with a single counter.

=== recap | Variable windows: grow, shrink, and why it works | 14 min
goal: Write the longest-window and shortest-window templates from memory and check the monotone-validity condition before trusting them
tag: window-variable | Variable sliding window
link: Competitive Programmer's Handbook, section 8.1 | https://cses.fi/book/book.pdf#page=87 | 8 min: PDF pages 87-89, the subarray-sum example with positive values and the amortised argument that each pointer moves at most n times
practice: 209, 3, 424

> [!key]
> Advance the right edge one step at a time and add the new element to the window's state. If the window became invalid, advance the left edge until it is valid again, then record. Both edges only move forward, so the scan is O(n) amortised. It is correct only when validity is **monotone**: shrinking a valid window keeps it valid (longest problems), or growing a valid window keeps it valid (shortest problems).

## Internals

- **Invariant (longest)**: after the shrink loop, `[left, right]` is the longest valid window that ends at `right`. For each right end the best start is the smallest valid one, and with monotone validity that start never moves backwards as `right` grows, so `left` never has to.
- **Cost**: `right` moves n times and `left` moves at most n times *in total*, so the inner `while` does O(n) work over the whole run, not per step: O(n) amortised, times the cost of one state update.
- **Shortest variant** (sum at least `target`, values non-negative): grow; while the window is valid, record its length and shrink. It needs the mirror condition: if `[l, r]` is valid, so is `[l, r + 1]`.
- **Monotone validity, and the counterexample.** With negative numbers neither direction holds. Longest subarray with sum at most 0 in `[5, -6, 1]`: the window drops 5 (on its own it is invalid) and returns 2 for `[-6, 1]`, but the whole array sums to 0, length 3. A later negative value would have repaired the window that was thrown away. When values can be negative or the target is an exact sum, use prefix sums (with a hash map to count, or a sorted structure for inequalities): the next module.
- **O(1) validity tests**: a running sum; a count map plus "the key just added has count 2"; `len(count)` distinct keys (delete zero counts); for character replacement, `length - max count <= k`. That last one even works with `max count` kept as a running maximum that never decreases: a stale value can keep an invalid window alive, but only at a length some valid window already reached, so the recorded answer stays right.
- **Jumping instead of crawling**: for "no repeats", store each character's last index and set `left = max(left, last[c] + 1)`; same O(n), fewer steps.

## Template

```python
def longest_no_repeat(s):
    """Length of the longest substring with no repeated character (grow, then shrink)."""
    count = defaultdict(int)
    left = best = 0
    for right, c in enumerate(s):
        count[c] += 1                          # grow: c enters
        while count[c] > 1:                    # invalid: shrink until valid again
            count[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)     # [left, right] is the longest valid window ending at right
    return best


def shortest_sum_at_least(a, target):
    """Length of the shortest subarray with sum >= target (a >= 0), or 0 if none."""
    total = left = 0
    best = inf
    for right, x in enumerate(a):
        total += x                             # grow
        while total >= target:                 # valid: record, then try a shorter one
            best = min(best, right - left + 1)
            total -= a[left]
            left += 1
    return 0 if best == inf else best
```

## Worked example

Longest substring of `"abcbad"` with no repeated character: the count map and a valid or invalid marker after each move.

```steps
Grow over 'a', 'b', 'c' (r = 0, 1, 2), adding each to the count map. No count above 1: **valid**, best = 3
    index     0   1   2   3   4   5
    s         {{a}}   {{b}}   {{c}}   b   a   d
    counts {a:1, b:1, c:1}   valid
---
Grow: 'b' enters at r = 3. count['b'] = 2, so the window is **invalid**
    index     0   1   2   3   4   5
    s         {{a}}   {{b}}   {{c}}   {{b}}   a   d
    counts {a:1, b:2, c:1}   INVALID
---
Shrink from the left until valid: drop 'a' (left = 1), still two b's; drop 'b' (left = 2). Valid again; best stays 3
    index     0   1   2   3   4   5
    s         a   b   {{c}}   {{b}}   a   d
    counts {b:1, c:1}   valid
---
Grow: 'a' enters at r = 4. No count above 1: **valid**, length 3, best = 3
    index     0   1   2   3   4   5
    s         a   b   {{c}}   {{b}}   {{a}}   d
    counts {a:1, b:1, c:1}   valid
---
Grow: 'd' enters at r = 5. No count above 1: **valid**, length 4, best = 4
    index     0   1   2   3   4   5
    s         a   b   {{c}}   {{b}}   {{a}}   {{d}}
    counts {a:1, b:1, c:1, d:1}   valid
```

## Pitfalls

- Recording inside the shrink loop for "longest" records invalid windows; recording after it for "shortest" misses the shorter valid ones.
- Shrinking with `if` instead of `while`: one step may not restore validity.
- With a "sum at least target" loop and `target <= 0`, the loop can empty the window and push `left` past `right`; handle that case first.
- Applying the template to data with negative values. Before coding, check monotonicity with a brute force on small random inputs that include negatives.

## Quick check

Q: What does `shortest_sum_at_least([1, 4, 2, 2, 5], 7)` return, and when is the answer first recorded?
A: 2. Lengths 3 are recorded at r = 2 ([1, 4, 2]), r = 3 ([4, 2, 2]) and r = 4 ([2, 2, 5]); at r = 4 the loop then drops the first 2, finds [2, 5] still sums to 7 and records 2.

> [!know]
> You now know the grow-then-shrink template, why it is O(n) amortised, and how to check the monotone-validity condition that makes it correct.

=== recap | Counting windows: at most K and exactly K | 12 min
goal: Count subarrays under a monotone condition with right - left + 1 per right end, and derive exactly-K counts by subtracting two at-most counts
tag: window-atmost | At most K, exactly K
link: doocs: LeetCode 992 solutions | https://leetcode.doocs.org/en/lc/992/#solution-1 | 5 min: 'Solution 1' records, for each right end, the leftmost valid start for K and for K - 1 distinct values, then sums the differences: the same subtraction organised per right end
practice: 713, 904, 992

> [!key]
> With monotone validity, the valid windows ending at `right` are exactly those starting anywhere in `[left, right]`: `right - left + 1` of them. Summing that over every right end counts all valid subarrays in O(n). "Exactly K" is not monotone, because shrinking can drop below K, but it is the difference of two monotone counts: exactly(K) = atMost(K) - atMost(K - 1).

## Internals

- **Why `right - left + 1`.** After the shrink loop `[left, right]` is valid, so every `[l, right]` with `l >= left` is valid too (it is a shrunk version), and every `l < left` is invalid (that is why `left` moved past it).
- **Distinct counts.** `len(count)` is the number of distinct values only if keys are deleted when their count reaches 0.
- **Why "exactly K" resists one window.** When the window holds K distinct values, several starts can work for the same end (dropping a duplicate keeps K), and one left pointer cannot represent that range. Two monotone counts can.
- **"At least" conditions** stay true as the window grows. Either use the complement (for distinct values, atLeast(K) = n(n + 1)/2 - atMost(K - 1)), or shrink while the window still qualifies and then add `left`: every start before `left` qualified with this end.
- **Products** (positive values): keep the running product, shrink while it is at least `k`, and return 0 at once when `k <= 1`, since no product of positive integers is below 1.
- **Cost**: two O(n) passes for exactly-K; the count map holds at most K + 1 keys.

## Template

```python
def count_at_most(a, k):
    """Number of subarrays with at most k distinct values."""
    if k < 0:
        return 0
    count = defaultdict(int)
    left = total = 0
    for right, x in enumerate(a):
        count[x] += 1
        while len(count) > k:
            y = a[left]
            count[y] -= 1
            if count[y] == 0:
                del count[y]                   # keep len(count) == number of distinct values
            left += 1
        total += right - left + 1              # every start in [left, right] works with this end
    return total


def count_exactly(a, k):
    return count_at_most(a, k) - count_at_most(a, k - 1)
```

## Worked example

`count_at_most([1, 2, 1, 3, 3], 2)`: each step adds the number of valid subarrays that end at `r`.

```steps
r = 0: 1 enters, 1 distinct (valid). Subarrays ending here with a valid start: 1
    index     0   1   2   3   4
    a         {{1}}   2   1   3   3
    counts {1:1}   + 1   total 1
---
r = 1: 2 enters, 2 distinct (valid). Subarrays ending here with a valid start: 2
    index     0   1   2   3   4
    a         {{1}}   {{2}}   1   3   3
    counts {1:1, 2:1}   + 2   total 3
---
r = 2: 1 enters, 2 distinct (valid). Subarrays ending here with a valid start: 3
    index     0   1   2   3   4
    a         {{1}}   {{2}}   {{1}}   3   3
    counts {1:2, 2:1}   + 3   total 6
---
r = 3: 3 makes 3 distinct values, invalid. Shrink: drop 1 and 2 (left = 2). Now 2 subarrays end at r and start in [left, r]
    index     0   1   2   3   4
    a         1   2   {{1}}   {{3}}   3
    counts {1:1, 3:1}   + 2   total 8
---
r = 4: 3 enters, 2 distinct (valid). Subarrays ending here with a valid start: 3. atMost(2) = 11; atMost(1) = 6, so exactly 2 distinct: 11 - 6 = 5
    index     0   1   2   3   4
    a         1   2   {{1}}   {{3}}   {{3}}
    counts {1:1, 3:2}   + 3   total 11
```

## Pitfalls

- Keeping zero counts in the dict, so `len(count)` overstates the number of distinct values and the window shrinks too far.
- Adding 1 per valid window instead of `right - left + 1`.
- `atMost(K - 1)` with K = 0: return 0 for a negative limit rather than running the loop.
- In the product version without the `k <= 1` check, the shrink loop runs `left` past `right` and divides by elements that are no longer in the window.

## Quick check

Q: Which subarrays make up `count_exactly([1, 2, 1, 3, 3], 2) = 5`?
A: [1, 2], [2, 1], [1, 2, 1], [1, 3] and [1, 3, 3]. atMost(2) = 11 counts these plus the six single-value subarrays ([1], [2], [1], [3], [3], [3, 3]), which atMost(1) = 6 removes.

> [!know]
> You now know how to count valid subarrays in O(n) with right - left + 1, and how to turn a non-monotone "exactly" into two monotone "at most" counts.

=== recap | Minimum covering window: the formed counter | 14 min
goal: Find the shortest substring that contains a multiset of required characters in O(m + n) by tracking how many requirements are currently met
tag: window-cover | Minimum covering window
link: doocs: LeetCode 76 solutions | https://leetcode.doocs.org/en/lc/76/#solution-1-counting-two-pointers | 5 min: 'Solution 1' counts matched character occurrences (up to len(t)) instead of satisfied distinct characters; compare the two bookkeeping choices
practice: 76

> [!key]
> Grow the right edge until the window covers every requirement, then shrink from the left while it still does, recording each covering window. To test "covers" in O(1), keep `formed`: the number of distinct required characters whose count in the window has reached its requirement. It changes only when a count crosses its threshold, upwards while growing and downwards while shrinking.

## Internals

- **Monotone in the "shortest" direction**: if `[l, r]` covers `t`, every larger window does too. So this is the shortest-window template with a cheaper validity test.
- **Bookkeeping**: when `have[c]` becomes exactly `need[c]`, `formed += 1` (a surplus copy does not count again). When a drop makes `have[d] < need[d]`, `formed -= 1`. `formed == required` exactly when the window covers `t`.
- **Cost**: each edge moves at most m = len(s) times with O(1) work per move, plus O(n) to count `t`: O(m + n) time and O(alphabet) memory. Comparing two Counters at each step would cost O(alphabet) per step instead.
- **Record positions, not slices**: store `(length, start)` and slice once at the end; slicing on every improvement copies characters.
- **Relatives**: the fixed-window `bad` counter for anagram windows is the same idea; "substrings containing all three letters" counts with the "at least" trick; windows measured in whole words step through the text one word length at a time.

## Template

```python
def min_window(s, t):
    """Shortest substring of s containing every character of t with multiplicity, or ''."""
    need = Counter(t)
    required = len(need)                       # distinct characters to satisfy
    have = defaultdict(int)
    formed = 0                                 # how many of them are satisfied now
    best_len, best_start = inf, 0
    left = 0
    for right, c in enumerate(s):
        have[c] += 1
        if c in need and have[c] == need[c]:
            formed += 1                        # c just became satisfied
        while formed == required:
            if right - left + 1 < best_len:
                best_len, best_start = right - left + 1, left
            d = s[left]
            have[d] -= 1
            if d in need and have[d] < need[d]:
                formed -= 1                    # d just became unsatisfied
            left += 1
    return "" if best_len == inf else s[best_start:best_start + best_len]
```

## Worked example

`min_window("xcbcab", "abc")`: `have` shows the required characters only, and the highlighted cells are the window.

```steps
Grow over x, c, b, c. The second c pushes have[c] to 2, more than needed; formed counts only characters whose need is met: c and b, so 2 of 3
    index     0   1   2   3   4   5
    s         {{x}}   {{c}}   {{b}}   {{c}}   a   b
    have {a:0, b:1, c:2}   formed 2/3   best -
---
Grow: a arrives, have[a] reaches need[a], so formed = 3/3: the window covers t. Now shrink while it still does
    index     0   1   2   3   4   5
    s         {{x}}   {{c}}   {{b}}   {{c}}   {{a}}   b
    have {a:1, b:1, c:2}   formed 3/3   best -
---
Record best = 'xcbca' (length 5). Drop 'x': not in t, formed stays 3
    index     0   1   2   3   4   5
    s         x   {{c}}   {{b}}   {{c}}   {{a}}   b
    have {a:1, b:1, c:2}   formed 3/3   best xcbca
---
Record best = 'cbca'. Drop 'c': have[c] falls 2 -> 1, still >= need, so formed stays 3 and shrinking continues
    index     0   1   2   3   4   5
    s         x   c   {{b}}   {{c}}   {{a}}   b
    have {a:1, b:1, c:1}   formed 3/3   best cbca
---
Record best = 'bca'. Drop 'b': have[b] falls below need, formed = 2. The window is no longer covering: stop shrinking, grow again
    index     0   1   2   3   4   5
    s         x   c   b   {{c}}   {{a}}   b
    have {a:1, b:0, c:1}   formed 2/3   best bca
---
Grow: b arrives, formed = 3 again for 'cab' (length 3, not shorter than 'bca', so best stays). Drop 'c': formed = 2. The scan ends: the answer is 'bca'
    index     0   1   2   3   4   5
    s         x   c   b   c   {{a}}   {{b}}
    have {a:1, b:1, c:0}   formed 2/3   best bca
```

## Pitfalls

- Incrementing `formed` on every copy of a required character: with `t = "aa"`, a single `a` must not complete the requirement.
- Testing `have[d] <= need[d]` after the decrement instead of `<`: `formed` then drops while the window still covers.
- Using a `defaultdict` for `need` and reading `need[c]` for characters outside `t` inserts them, which breaks `len(need)` if it is computed later; test `c in need` first, as the template does.
- An empty `t`, or a `t` longer than `s`: return "" without scanning.

## Quick check

Q: What does `min_window("abxaab", "aab")` return, and when does `formed` first reach 2?
A: "aab". formed reaches 2 at r = 3, when the window "abxa" first holds two a's and a b. Later windows of length 4 tie, and at r = 5 dropping the x leaves "aab", length 3.

> [!know]
> You now know how to find minimum covering windows in O(m + n) with a satisfied-requirements counter.

=== recap | Window extremes, and when to leave the window behind | 12 min
goal: Track the maximum or minimum of a moving window, and recognise when a plain window breaks and which repair fits each case
tag: window-deque | Window plus a monotonic deque
link: Competitive Programmer's Handbook, section 8.3 | https://cses.fi/book/book.pdf#page=91 | 5 min: PDF pages 91-92, the sliding window minimum with a monotonic queue and the argument that each element is added and removed once
link: Python docs: heapq, priority queue implementation notes | https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes | 4 min: the 'mark an entry as removed' idea is the lazy deletion used by the heap version of the window maximum
practice: 1658, 1838, 395

> [!key]
> A window needs an aggregate you can update when an element leaves and a validity rule that is monotone. Maximum and minimum cannot be "un-added", so pair the window with a **monotonic deque** of indices (O(1) amortised) or a heap with lazy deletion (O(log n)). If validity is not monotone, the window is the wrong tool: switch to prefix sums, sort first, or fix one more parameter so that each pass becomes monotone.

## Internals

- **Deque invariant**: indices increase from front to back and their values strictly decrease, so the front is the maximum of the current window. A new value first pops every smaller or equal value from the back (they are older and smaller, so they can never be a maximum again), then the front is dropped if it has left the window. Each index is pushed once and popped at most once: O(n) total. The monotonic stacks module proves this in depth and reuses it for next-greater problems.
- **Lazy heap**: push `(-value, index)`; before reading, pop tops whose index has left the window. Stale entries can pile up inside the heap, so it may hold up to n items: O(n log n), simpler to adapt when the window moves irregularly.
- **Python**: `collections.deque` appends and pops at both ends in O(1) (it is a linked list of 64-slot blocks); `list.pop(0)` shifts everything, O(n).

When the plain window breaks, match the symptom:

| Symptom | Repair | Cost |
|---|---|---|
| Need the max or min of every window | monotonic deque of indices | O(n) |
| Values can be negative, or the target is an exact sum | prefix sums plus a hash map of earlier prefixes | O(n) |
| Elements can be taken only from both ends (reduce x to zero) | complement: the kept middle is one window with sum total - x | O(n) |
| The condition is about values, not positions (make k increments) | sort, then window over the sorted values | O(n log n) |
| Adding a character can help or hurt (every letter at least k times) | fix the number of distinct letters u = 1..26; each pass is an at-most-u window | O(26n) |

## Template

```python
def window_max(a, k):
    """Maximum of every length-k window; deque holds indices with decreasing values."""
    dq, out = deque(), []
    for r, x in enumerate(a):
        while dq and a[dq[-1]] <= x:
            dq.pop()                           # smaller, older values can never be a maximum again
        dq.append(r)
        if dq[0] <= r - k:
            dq.popleft()                       # the front left the window
        if r >= k - 1:
            out.append(a[dq[0]])
    return out


def window_max_heap(a, k):
    """Same answers with a lazy-deletion heap: O(n log n)."""
    heap, out = [], []
    for r, x in enumerate(a):
        heapq.heappush(heap, (-x, r))
        while heap[0][1] <= r - k:
            heapq.heappop(heap)                # stale: its index left the window
        if r >= k - 1:
            out.append(-heap[0][0])
    return out
```

## Worked example

Maximum of every window of size 3 in `[5, 3, 4, 1, 2, 0]`; the deque line shows `index(value)` from front to back.

```steps
r = 0: 5 enters
    index     0   1   2   3   4   5
    a         {{5}}   3   4   1   2   0
    deque  0(5)
---
r = 1: 3 enters
    index     0   1   2   3   4   5
    a         {{5}}   {{3}}   4   1   2   0
    deque  0(5) 1(3)
---
r = 2: 4 enters; pop 3 from the back (smaller and older: never a maximum again); max = a[0] = 5
    index     0   1   2   3   4   5
    a         {{5}}   {{3}}   {{4}}   1   2   0
    deque  0(5) 2(4)
---
r = 3: 1 enters; front index 0 left the window: popleft; max = a[2] = 4
    index     0   1   2   3   4   5
    a         5   {{3}}   {{4}}   {{1}}   2   0
    deque  2(4) 3(1)
---
r = 4: 2 enters; pop 1 from the back (smaller and older: never a maximum again); max = a[2] = 4
    index     0   1   2   3   4   5
    a         5   3   {{4}}   {{1}}   {{2}}   0
    deque  2(4) 4(2)
---
r = 5: 0 enters; front index 2 left the window: popleft; max = a[4] = 2
    index     0   1   2   3   4   5
    a         5   3   4   {{1}}   {{2}}   {{0}}
    deque  4(2) 5(0)
```

## Pitfalls

- Storing values instead of indices in the deque: you can no longer tell when the front has left the window.
- Expiring the front with `if` works for fixed windows (at most one index leaves per step); a variable window whose left edge can jump needs `while`.
- Popping with `<` instead of `<=` keeps equal values in the deque; still correct, just longer. Popping from the front when you meant the back breaks the invariant.
- Forcing a window onto data with negative values: see the counterexample in the variable-window card.

## Quick check

Q: Which tool would you use for "count subarrays whose sum is exactly k" when values may be negative, and why not a window?
A: Prefix sums with a hash map of how often each earlier prefix sum occurred. With negative values, shrinking a window can raise or lower its sum, so there is no left edge that only moves forward; validity is not monotone.

Q: What does `window_max([5, 3, 4, 1, 2, 0], 3)` return?
A: `[5, 4, 4, 2]`, as in the trace: 5 leaves at r = 3, 4 leaves at r = 5.

> [!know]
> You now know how to track window maxima in O(n) and how to spot and repair the cases where a plain sliding window does not apply.

=== lab | Rolling metrics over a log stream | 50 min
goal: Compute sliding-minute request rates, distinct users in five minutes and the busiest window over a million requests, verify them against the naive scan, and compare fixed-window and two-counter estimates with the exact sliding count
link: Cloudflare: How we built rate limiting capable of scaling to millions of domains | https://blog.cloudflare.com/counting-things-a-lot-of-different-things/#:~:text=Sliding%20windows%20to%20the%20rescue | 6 min: the section 'Sliding windows to the rescue': the two-counter estimate you measure in step 5, and its error on 400 million real requests

Windows over time are what monitoring and rate limiting compute all day. Prometheus' `rate(x[5m])` aggregates each series over the trailing five minutes; a rate limiter asks "how many requests has this client sent in the last minute?" on every request; Flink and Kafka Streams run the same windows over event streams. Here you compute these metrics over a synthetic day of one million requests, check them against a naive scan, and measure the two shortcuts real limiters take: fixed clock-minute buckets and Cloudflare's two-counter estimate.

## Steps

1. Save this as `rolling_lab.py`. The time windows are half-open, `(t - width, t]`, and the log is sorted by time, so the left edge only moves forward.

```python
"""The rolling-metrics lab from dsa/09-window.md, as printed there (run: python3 rolling_lab.py)."""
import random
import time
from collections import defaultdict


def make_log(n, seed=0):
    """n (timestamp, user) requests over one day, sorted by time, with a busy lunchtime and a few heavy users."""
    rng = random.Random(seed)
    times = sorted(rng.uniform(0, 86_400) if rng.random() < 0.8 else rng.gauss(45_000, 1_800) % 86_400
                   for _ in range(n))
    users = [rng.randrange(20) if rng.random() < 0.3 else rng.randrange(100_000) for _ in range(n)]
    return times, users


def last_minute_naive(times):
    """For each request i: how many requests fell in (t_i - 60, t_i]. Scans backwards: O(n * w)."""
    out = []
    for i, t in enumerate(times):
        j = i
        while j >= 0 and times[j] > t - 60:
            j -= 1
        out.append(i - j)
    return out


def last_minute(times, width=60):
    """Same answers with a variable window: the left edge only moves forward. O(n)."""
    out, left = [], 0
    for right, t in enumerate(times):
        while times[left] <= t - width:
            left += 1
        out.append(right - left + 1)
    return out


def distinct_users_naive(times, users, width=300):
    out = []
    for i, t in enumerate(times):
        seen, j = set(), i
        while j >= 0 and times[j] > t - width:
            seen.add(users[j])
            j -= 1
        out.append(len(seen))
    return out


def distinct_users(times, users, width=300):
    """Distinct users in (t - width, t] at each request: window plus a count map."""
    count = defaultdict(int)
    out, left = [], 0
    for right, t in enumerate(times):
        count[users[right]] += 1
        while times[left] <= t - width:
            u = users[left]
            count[u] -= 1
            if count[u] == 0:
                del count[u]
            left += 1
        out.append(len(count))
    return out


def fixed_minute_max(times):
    """Busiest clock minute ([60k, 60k + 60)): what a fixed-window counter sees."""
    buckets = defaultdict(int)
    for t in times:
        buckets[int(t // 60)] += 1
    return max(buckets.values())


def sliding_counter_estimate(times, width=60):
    """Cloudflare-style estimate at each request: previous bucket weighted by overlap plus current bucket."""
    buckets = defaultdict(int)
    out = []
    for t in times:
        b = int(t // width)
        buckets[b] += 1
        elapsed = t - b * width
        out.append(buckets[b - 1] * (width - elapsed) / width + buckets[b])
    return out


if __name__ == "__main__":
    times, users = make_log(1_000_000)
    small = times[:10_000]
    t0 = time.perf_counter(); a = last_minute_naive(small); t1 = time.perf_counter()
    b = last_minute(small); t2 = time.perf_counter()
    assert a == b
    print(f"last minute, 10k requests: naive {t1 - t0:.2f} s, window {t2 - t1:.4f} s")
    t0 = time.perf_counter(); a = distinct_users_naive(small, users[:10_000]); t1 = time.perf_counter()
    b = distinct_users(small, users[:10_000]); t2 = time.perf_counter()
    assert a == b
    print(f"distinct users in 5 min, 10k requests: naive {t1 - t0:.2f} s, window {t2 - t1:.4f} s")

    t0 = time.perf_counter(); rate = last_minute(times); t1 = time.perf_counter()
    dist = distinct_users(times, users); t2 = time.perf_counter()
    print(f"1M requests: last-minute counts {t1 - t0:.2f} s, distinct users {t2 - t1:.2f} s")
    busiest = max(range(len(times)), key=rate.__getitem__)
    print(f"busiest sliding minute: {rate[busiest]} requests, ending at t = {times[busiest]:.0f} s")
    print(f"busiest clock minute (fixed window): {fixed_minute_max(times)} requests")
    print(f"most distinct users in 5 min: {max(dist)}")
    est = sliding_counter_estimate(times)
    err = [abs(e - r) / r for e, r in zip(est, rate)]
    print(f"sliding-counter estimate: mean relative error {sum(err) / len(err):.2%}, max {max(err):.1%}")
```

2. Before running it, predict: how much faster is the window than the naive scan for 10,000 requests, given that a minute holds a few hundred requests and five minutes a few thousand? Will the busiest clock minute be higher or lower than the busiest sliding minute?
3. Run `python3 rolling_lab.py` (about 20 seconds; the naive distinct-users scan is the slow part). The asserts prove the window versions agree with the naive ones.
4. Explain the fixed-window result: why can the busiest clock minute never exceed the busiest sliding minute, and why does a limit enforced on clock minutes let up to twice the limit through in 60 seconds (L requests at 0:59, L more at 1:00)?
5. Look at the two-counter estimate's error. Sort the requests by error and look at the timestamps of the worst ones, then compare the mean error during the lunchtime peak (40,000 < t < 50,000) with the rest of the day. Which is larger, and why?
6. Turn `last_minute` into a limiter: a class with `allow(t)` that keeps a `deque` of accepted timestamps for one client, pops from the left while the oldest is at least 60 seconds old, and accepts only if fewer than L remain. Test it with a burst of 2L requests around a minute boundary and check that it never accepts more than L in any 60-second span.

## What you should see

- For 10,000 requests the naive last-minute count takes about a second and the window a few milliseconds, a speed-up of over 100x; for distinct users the naive scan takes several seconds against tens of milliseconds. The gap grows with the number of requests per window, because the naive scan rereads the whole window for every request.
- On a million requests both window passes finish in one or two seconds of pure Python.
- With the seed in the script: busiest sliding minute 3,387 requests (during the lunchtime peak, around t = 44,800 s), busiest clock minute 3,288. A clock minute is one particular 60-second window, so it can only miss the peak, never exceed it.
- The two-counter estimate has a mean relative error of about 1% and a worst case of about 10%. The estimate assumes the previous minute's requests were spread evenly, and random clumps break that assumption; the worst cases sit off-peak, and the mean error is about 0.8% during the peak against 1.3% elsewhere, because relative noise shrinks as counts grow. Cloudflare measured something different, wrong allow or block decisions, and found them on 0.003% of 400 million requests: a limiter only needs the estimate to be accurate near the limit.
- The sliding-log limiter from step 6 is exact but stores one timestamp per accepted request per client; the two-counter version stores two integers. Cloudflare chose the estimate for this kind of reason: a per-request log was too costly in memory and processing, while two counters need only the GET, SET and INCR operations their memcached cluster offered atomically.

=== practice
- 643 core
  cue: The best average over contiguous blocks of exactly k elements.
  hint: Two neighbouring blocks share all but two elements. What changes when the block moves by one?
  insight: Keep the block sum: add the element entering on the right and subtract the one leaving on the left. Track the best sum and divide by k once at the end.
  cost: O(n) time, O(1) space
  pattern: window-fixed
- 209 core
  cue: The shortest contiguous run whose sum reaches a target, and every value is positive.
  hint: With positive values, what happens to the sum when you drop the leftmost element of a run that already reaches the target?
  insight: Extend right; while the sum is still at least the target, record the length and drop from the left. Positivity makes validity monotone, so the left edge never moves back and the scan is O(n).
  cost: O(n) time, O(1) space
  pattern: window-variable
- 3 core
  cue: The longest substring with no character repeated.
  hint: Grow a run to the right. When a repeat appears, what is the least you must cut from the left?
  insight: Keep counts (or the last index) of each character in the window; on a repeat, move left past the earlier copy, never backwards (left = max(left, last[c] + 1)). Record the length after each repair.
  cost: O(n) time, O(alphabet) space
  pattern: window-variable
- 567 core
  cue: Does any substring of s2 contain exactly the letters of s1, in any order?
  hint: Any such substring has exactly len(s1) characters. How can you compare letter counts without recounting every candidate?
  insight: Slide a window of len(s1) over s2 with 26 count differences and a counter of letters whose difference is non-zero; each slide changes two letters, and a match is a zero counter.
  cost: O(n) time, O(26) space
  pattern: window-fixed
- 424 core
  cue: The longest substring that becomes a single repeated letter after at most k replacements.
  hint: For a given substring, how many replacements are needed? It depends on one count only.
  insight: A window needs length - (count of its most common letter) replacements; shrink while that exceeds k. The maximum count can even be kept as a running maximum that never decreases: a stale value never lets the window exceed a length that some valid window reached.
  cost: O(n) time, O(26) space
  pattern: window-variable
- 713 core
  cue: Count contiguous subarrays whose product is below k, with positive values.
  hint: For a fixed right end, which left ends work? Are they scattered or one block?
  insight: Shrink while the product is at least k; then every start in [left, right] works, so add right - left + 1. Return 0 straight away when k <= 1.
  cost: O(n) time, O(1) space
  pattern: window-atmost
- 904 core
  cue: The longest run that uses at most two different kinds of item.
  hint: Rephrase it as a window condition on the number of distinct values. What do you do when a third kind enters?
  insight: Keep a count per kind in the window and delete kinds whose count reaches zero; shrink from the left while there are more than two kinds, and record the length after each step.
  cost: O(n) time, O(1) space (at most three keys)
  pattern: window-atmost
- 1658 derive
  cue: Remove elements only from the two ends so that the removed ones sum to x, with as few removals as possible.
  hint: Look at what is left over rather than what is removed. What shape does it have?
  insight: Removing from both ends leaves one contiguous middle block, which must sum to total - x. Values are positive, so find the longest window with exactly that sum (shrink while the sum is too big); the answer is n minus its length, or -1.
  cost: O(n) time, O(1) space
  pattern: window-variable
- 76 core
  cue: The shortest substring of s that contains every character of t, counting repeats.
  hint: Grow until the window covers t, then shrink while it still does. How can you tell "covers" in O(1)?
  insight: Keep need counts, window counts and formed, the number of distinct characters whose need is met; it changes only when a count crosses its threshold. Record while formed equals the number of distinct characters in t.
  cost: O(m + n) time, O(alphabet) space
  pattern: window-cover
- 992 derive
  cue: Count subarrays with exactly K distinct integers.
  hint: Shrinking a window with exactly K distinct values can keep it at K, so one left pointer cannot capture all valid starts. Which related count is monotone?
  insight: Exactly K = atMost(K) - atMost(K - 1), where atMost adds right - left + 1 for each right end of a standard shrinking window over distinct counts.
  cost: O(n) time, O(n) space
  pattern: window-atmost
- 1838 stretch
  cue: Up to k increments of +1; maximise how often one value appears.
  hint: Only raise values towards a value that already exists, and the nearest smaller values are the cheapest to raise. What order makes "nearest" contiguous?
  insight: Sort. Window [l, r] can be levelled up to a[r] when a[r] * (r - l + 1) - window sum <= k; this cost only grows as the window grows, so shrink while it exceeds k and keep the longest window.
  cost: O(n log n) time, O(1) extra space
  pattern: window-variable
- 395 stretch
  cue: The longest substring in which every character appears at least k times.
  hint: Adding a character can make the window better or worse, so no shrink rule is monotone. Which extra quantity, if you fixed it, would make one?
  insight: For each u = 1..26, run a window that allows at most u distinct letters, tracking how many letters reach k; whenever distinct == u and all u reach k, the window qualifies. Divide and conquer on letters rarer than k also works.
  cost: O(26 n) time, O(26) space
  pattern: window-atmost
