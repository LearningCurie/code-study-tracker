=== card | 219

## The problem

Given an integer array and a nonnegative distance `k`, determine whether two different indices hold equal values and differ by at most `k`. For `[1, 2, 3, 1]` and `k = 3`, return true; with `k = 2`, return false. The indices, not the values, determine the distance.

## Constraints and what they imply

The array can contain many repeated and negative values. A value may occur more than twice, and `k` may be zero or larger than the array. Only existence is requested; the actual indices are not required. A quadratic scan is costly for a large array.

## Brute force

Try every pair of indices `i < j`, checking both equality and `j - i <= k`. Stop when a pair passes both tests. There are O(n²) pairs in the worst case and O(1) auxiliary space. Limiting the inner scan to the next k positions improves the bound but can still be quadratic.

## The insight

At each index, remember the most recent index for each value. Among earlier equal values, the most recent is closest to the current index. If that distance is too large, all older occurrences are too far away as well. If it is small enough, the stored occurrence is a valid witness. Update the index after checking so the current element is never paired with itself.

## Optimal solution, traced

```steps
nums = [1, 2, 1], k = 2; initially last = {}
    index 0 stores 1 -> 0; index 1 stores 2 -> 1
---
index 2 sees 1 last at 0; distance 2 <= 2
    return {{True}}
```

The map describes only positions strictly before the current one. Replacing an old position by a newer one preserves every possible future answer because the newer one is never farther away.

## Code

```python
def contains_nearby_duplicate(nums, k):
    last = {}
    for i, value in enumerate(nums):
        if value in last and i - last[value] <= k:
            return True
        last[value] = i
    return False
```

## Complexity

Expected O(n) time with hash-table operations and O(min(n, u)) space, where u is the number of distinct values. The implementation retains every distinct value, even when its last position is older than k.

## Mistakes and edge cases

- `k = 0` cannot match two different indices; equality at exactly distance k is allowed.
- Check before updating the index, or every element matches itself.
- Empty and singleton arrays return false. A later repeat may be close even if an earlier repeat was not.

## Variations

- Maintain a set of only the previous k elements for a bounded-size window.
- Return a pair of qualifying indices instead of a Boolean.

=== card | 1679

## The problem

Given an integer array and a target `k`, repeatedly remove two remaining elements whose sum is `k`. Return the maximum number of operations. Each occurrence may be used only once. For `[1, 2, 3, 4]` with `k = 5`, two operations are possible.

## Constraints and what they imply

The same number may appear many times, so positions are separate resources even when their values agree. The official input has positive integers, but the reasoning also works for zero or negative values. The number of operations, not the chosen pairs, is requested. Large arrays make checking all pairings impractical.

## Brute force

Enumerate all possible first legal pairs, remove each pair in turn, and recursively find the best continuation; also return zero when no pair remains. This explores exponentially many removal sequences and needs linear recursion depth plus copies if arrays are copied. The same remaining multiset can be reached by many different orders.

## The insight

Each value has exactly one possible partner, `k - value`. Therefore one complement class cannot steal a useful partner from another class. While scanning, keep counts of previously seen occurrences that have not yet been paired. If the current value's complement is available, consume one; otherwise store the current value for a future complement. Forming a pair immediately is safe: exchanging it with any later pair using that same complement leaves the same number of possible pairs. This also handles a value equal to its own complement.

## Optimal solution, traced

```steps
nums = [3, 1, 3, 4, 3], k = 6
    store 3, then store 1
---
next 3 consumes the waiting 3; 4 is stored
    final 3 waits; answer = {{1}}
```

After each item, the map represents unused seen occurrences. The counter need not delete zero entries because availability is checked by count, not membership.

For example, four copies of half the target make two pairs, while three copies make only one. The scan consumes them two at a time without requiring a separate special case.

## Code

```python
from collections import defaultdict

def max_operations(nums, k):
    waiting = defaultdict(int)
    answer = 0
    for value in nums:
        partner = k - value
        if waiting[partner] > 0:
            waiting[partner] -= 1
            answer += 1
        else:
            waiting[value] += 1
    return answer
```

## Complexity

Expected O(n) time with hashing and O(n) auxiliary space for counts. Each element is processed once; `defaultdict` may also create entries for queried complements that never appear. The returned integer uses constant space.

## Mistakes and edge cases

- When `2 * value == k`, one operation needs two distinct occurrences, not one.
- Decrement the partner count after matching, or the same occurrence can be reused.
- An empty array, no complementary values, or a single element yields zero.

## Variations

- Sort a copy and use two pointers to obtain O(n log n) time.
- Return the actual index pairs by storing lists of waiting indices.

=== card | 930

## The problem

Given a binary array and an integer `goal`, count its nonempty contiguous subarrays whose sum equals `goal`. Different start or end indices count separately, even if their values are identical. For `[1, 0, 1, 0, 1]` and goal 2, there are four qualifying subarrays.

## Constraints and what they imply

Every entry is zero or one and the requested sum is nonnegative. Zeros can extend a matching subarray without changing its sum. The answer can be quadratic in n even though an efficient algorithm need not enumerate it.

## Brute force

For each starting index, extend an ending index to the right, accumulating the sum and counting each match. There are O(n²) intervals and each extension costs O(1), so time is O(n²) and auxiliary space is O(1). Recomputing each sum from scratch would take even longer.

## The insight

Let the prefix total before an interval be `p` and the total through its end be `t`. Its sum is `t - p`, so each earlier prefix equal to `t - goal` starts a valid interval. Finding just one matching window per endpoint is not enough. Store how often each prefix total has occurred. Seed the empty prefix with frequency one so intervals starting at index zero are counted. Query before recording the current prefix to rule out empty intervals, especially when goal is zero.

## Optimal solution, traced

```steps
nums = [1, 0, 1], goal = 1; counts = {0: 1}
    first total 1 finds one earlier 0; answer 1
---
second total 1 finds another 0; answer 2
    third total 2 finds two earlier totals 1; answer {{4}}
```

The two occurrences of prefix total one correspond to different starts; their multiplicity must be retained. Prefix sums also work for negative values, although this problem supplies binary values.

At each endpoint the lookup counts all valid starts at once, rather than choosing a single window. This distinction is especially important when consecutive zeros give several prefixes the same total.

## Code

```python
from collections import defaultdict

def num_subarrays_with_sum(nums, goal):
    counts = defaultdict(int)
    counts[0] = 1
    total = answer = 0
    for value in nums:
        total += value
        answer += counts[total - goal]
        counts[total] += 1
    return answer
```

## Complexity

Expected O(n) time and O(n) auxiliary space for the frequency map. The largest count can be n(n + 1)/2 for all zeros and goal zero; Python integers grow as necessary.

## Mistakes and edge cases

- Initialising the empty prefix is necessary for matches starting at zero.
- Store frequencies, not just distinct totals; several zero entries create repeated totals.
- Empty input gives zero; goal zero on `[0, 0]` gives three, not two.

## Variations

- For nonnegative entries, subtract the number of sums at most goal minus those at most goal minus one.
- Replace binary entries with arbitrary signed integers; prefix frequencies still apply.

=== card | 438

## The problem

Given lowercase strings `s` and nonempty `p`, return every starting index in `s` where the substring of length `len(p)` is a rearrangement of `p`. Return indices in increasing order. For `s = "cbaebabacd"` and `p = "abc"`, the result is `[0, 6]`.

## Constraints and what they imply

The alphabet has exactly 26 lowercase English letters. A match must have the same length and the same count of every letter; the order inside it is irrelevant. If the pattern is longer than the text, there are no candidates. Overlapping matches are allowed.

## Brute force

For every possible start, slice the candidate substring and sort it and the pattern before comparing. If n is the text length and m the pattern length, this costs O(n m log m) time in a straightforward implementation and O(m) temporary space. Most of the work is repeated between overlapping candidates.

## The insight

All candidates have the same length. The fixed alphabet makes each frequency table a fixed size. Keep one array of letter counts for the pattern and another for the current text window. Add the new rightmost character and remove the character that has just fallen out when the window grows beyond m. Once the window has length m, equal arrays mean equal multisets and hence an anagram. Comparing 26 entries is constant work because the alphabet size is fixed.

## Optimal solution, traced

```steps
s = "abab", p = "ab"; first window "ab"
    counts agree, record 0
---
slide to "ba", then "ab"
    counts agree at both starts; return {{[0, 1, 2]}}
```

Removing the old character before comparison ensures that exactly m text characters contribute. Equal length by itself is insufficient: each of the 26 counts must agree.

For a one-character pattern, the same loop checks every individual text character. The code assumes the stated nonempty pattern; an empty pattern would require a separately defined convention.

## Code

```python
def find_anagrams(s, p):
    m = len(p)
    if m > len(s):
        return []
    target = [0] * 26
    window = [0] * 26
    for ch in p:
        target[ord(ch) - ord('a')] += 1
    answer = []
    for i, ch in enumerate(s):
        window[ord(ch) - ord('a')] += 1
        if i >= m:
            window[ord(s[i - m]) - ord('a')] -= 1
        if i >= m - 1 and window == target:
            answer.append(i - m + 1)
    return answer
```

## Complexity

Time is O(n + m) because comparing 26 counts costs O(1); auxiliary space is O(1) for the fixed alphabet, excluding up to O(n) returned indices. If the alphabet were variable, each full comparison would cost O(alphabet size).

## Mistakes and edge cases

- Do not compare incomplete windows, or report end indices instead of start indices.
- Repeated letters must be counted; sets cannot distinguish `aab` from `abb`.
- A longer pattern returns an empty list; overlapping answers are not skipped.

## Variations

- Track the number of matching count positions to avoid comparing all entries.
- Generalise to arbitrary characters with a map and track the number of nonzero differences.

=== card | 189

## The problem

Rotate an integer array to the right by `k` positions, wrapping elements that leave the end back to the front. Modify the supplied array in place and return no value. For `[1, 2, 3, 4, 5]` and `k = 2`, the array becomes `[4, 5, 1, 2, 3]`.

## Constraints and what they imply

The number of shifts is nonnegative and may exceed the array length. Values may repeat and must retain their relative cyclic order. In-place means the original list object must be changed, not merely a local variable reassigned.

## Brute force

Repeat k times: save the final value, move every other element one position right, and put the saved value at the front. This uses O(1) auxiliary space and O(nk) time. Reducing k modulo n helps but may still leave quadratic work when k is near n.

## The insight

A full cycle of n shifts changes nothing, so only the remainder matters. A right rotation cuts the sequence into an initial block A and a final block B, then produces B followed by A. Reverse the entire list to obtain reverse(B) followed by reverse(A). Reversing each of those two ranges restores the internal order while keeping their new positions. Each reversal swaps its endpoints until the pointers meet, using no copied slices.

## Optimal solution, traced

```steps
[1, 2, 3, 4, 5], k = 2; reverse all
    [5, 4, 3, 2, 1]
---
reverse positions 0..1, then 2..4
    [4, 5, 1, 2, 3] = {{rotated array}}
```

The helper accepts inclusive bounds; an empty range such as `0..-1` requires no swaps. The explicit empty-array guard avoids taking a remainder modulo zero.

The three reversals are a composition, not three separate rotations. Each swap modifies the original list directly. In particular, when k is zero the full reversal and the final reversal cancel, which preserves the input ordering without requiring a special branch.

## Code

```python
def rotate(nums, k):
    n = len(nums)
    if not n:
        return
    k %= n

    def reverse(left, right):
        while left < right:
            nums[left], nums[right] = nums[right], nums[left]
            left += 1
            right -= 1

    reverse(0, n - 1)
    reverse(0, k - 1)
    reverse(k, n - 1)
```

## Complexity

Each reversal touches at most n positions, so time is O(n) and auxiliary space is O(1). The small helper uses a constant number of local variables and does not allocate an array proportional to n.

## Mistakes and edge cases

- Reduce k modulo n only after handling an empty array.
- Reverse both blocks, not just the first, to restore their order.
- Zero shifts and a one-element array leave the original object unchanged.

## Variations

- Rotate left by reversing the corresponding blocks in the opposite arrangement.
- Use cyclic replacement and track how many positions have been written.

=== card | 1657

## The problem

Two lowercase words are called close if one can become the other using any number of position swaps and global exchanges of two existing letters. A global exchange changes every occurrence of each chosen letter into the other. Decide whether the given words are close. For `"abbccc"` and `"cccbba"`, return true.

## Constraints and what they imply

Only the 26 lowercase letters occur. A position swap exchanges two characters at selected positions. A global exchange replaces each occurrence of one selected existing letter by the other, in both directions. Word lengths and counts may be large, so exploring every sequence of operations is not practical.

## Brute force

Treat each distinct word arrangement as a state and perform a graph search over all swaps and allowed global exchanges. This is finite but can have exponentially many states; with n positions even the number of distinct arrangements can approach n!. Storing visited strings also takes substantial space.

## The insight

Two invariants completely describe feasibility: the set of letters present, and the multiset of their positive frequencies. A position swap cannot alter counts; a global exchange cannot introduce a new letter. Position swaps change neither invariant; global exchanges permute the frequencies among the existing letters. Conversely, if both invariants agree, exchange letter identities until every letter has the desired frequency. Then position swaps arrange the resulting multiset into the target word. Equal total length follows from equal positive frequency multisets, though a direct length check is also useful.

## Optimal solution, traced

```steps
word1 = "abbccc": counts a:1, b:2, c:3
    word2 = "aaabbc": counts a:3, b:2, c:1
---
both use {a, b, c}, with frequencies [1, 2, 3]
    exchange a and c; then reorder positions => {{True}}
```

Matching only sorted counts would wrongly accept words whose alphabets differ. Matching only alphabets would miss incompatible multiplicities.

For instance, `aab` and `abb` are close because exchanging the roles of a and b swaps their counts. By contrast, `aab` and `aac` cannot be close because c is absent from the first word.

## Code

```python
from collections import Counter

def close_strings(word1, word2):
    if len(word1) != len(word2):
        return False
    first = Counter(word1)
    second = Counter(word2)
    return (first.keys() == second.keys()
            and sorted(first.values()) == sorted(second.values()))
```

## Complexity

Counting takes O(n + m) time for word lengths n and m. Sorting at most 26 counts is constant work under the fixed-alphabet constraint, and the counters use O(1) auxiliary space. For an unrestricted alphabet of u distinct characters, sorting instead costs O(u log u) and space is O(u).

## Mistakes and edge cases

- Equal frequency multisets alone do not allow replacing a letter that was absent.
- Zero counts need not be sorted because equality of present-letter sets is checked separately.
- Different lengths fail immediately; identical words always pass.

## Variations

- Compare histograms of frequencies rather than sorting them.
- Construct an explicit sequence of relabellings and position swaps when a witness is required.

=== card | 1004

## The problem

Given a binary array and nonnegative `k`, find the greatest length of a contiguous run of ones obtainable by changing at most k zeros to ones. For `[1, 0, 1, 0, 1]` with `k = 1`, the answer is 3. No actual changes need to be returned.

## Constraints and what they imply

The chosen entries must remain contiguous, and fewer than k flips are allowed. Large inputs call for avoiding repeated work over many possible intervals. If k covers every zero, the entire array is feasible.

## Brute force

Try every interval and count its zeros while extending the right endpoint from each fixed left endpoint. Record the longest interval with at most k zeros. This takes O(n²) time and O(1) auxiliary space; recomputing counts from scratch for each interval would be O(n³).

## The insight

A candidate interval is feasible precisely when it contains at most k zeros. Grow a window from left to right and track its number of zeros. Whenever the count exceeds k, remove elements from its left until it becomes valid again. Removing a leftmost zero decreases the count; removing a one does not. Any earlier left endpoint was invalid for the current right endpoint, since it included all zeros in the invalid window. Thus the restored window is the longest feasible one ending at that right endpoint.

## Optimal solution, traced

```steps
[1, 0, 1, 0, 1], k = 1
    first three positions contain one zero; best = 3
---
second zero makes count 2; remove 1 and then 0 from left
    window [1, 0, 1] is valid; best stays {{3}}
```

Both endpoints move only forward. The maximum over all right endpoints is therefore the overall maximum, including intervals ending at the last element.

When removing elements, the left endpoint may pass several ones before reaching a zero. The count changes only when that zero leaves, and the window can temporarily be empty when k is zero.

## Code

```python
def longest_ones(nums, k):
    left = zeros = best = 0
    for right, value in enumerate(nums):
        if value == 0:
            zeros += 1
        while zeros > k:
            if nums[left] == 0:
                zeros -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
```

## Complexity

Each index enters once and leaves at most once, so time is O(n) and auxiliary space is O(1). The nested while loop is amortised linear, not quadratic, because the left pointer never moves backward.

## Mistakes and edge cases

- Shrink until valid, not merely by one position, for the stated window invariant.
- `k = 0` finds the longest existing run of ones; all zeros may produce zero.
- An empty array returns zero; all ones return the array length.

## Variations

- Return the endpoints of a longest feasible interval as well as its length.
- Count intervals with at most k zeros by adding the current valid window length at every endpoint.

=== card | 523

## The problem

Given an array of nonnegative integers and a positive integer `k`, decide whether some contiguous subarray of length at least two has a sum divisible by `k`. For `[23, 2, 4, 6, 7]` and `k = 6`, the answer is true because `[2, 4]` sums to 6. A zero sum is divisible by any positive k.

## Constraints and what they imply

The array can contain zeros and the sum need not equal k: any multiple qualifies. The minimum length rules out a single element even if it is itself divisible by k. Large arrays make checking all intervals expensive. The official k is positive, so remainder by zero is not part of this contract.

## Brute force

For each start, extend an end index and accumulate the sum; test divisibility whenever at least two values have been included. There are O(n²) candidate intervals, giving O(n²) time and O(1) auxiliary space. This repeats work across starts despite maintaining each running sum incrementally.

## The insight

The difference of two prefix sums is divisible by k exactly when the sums have equal remainders modulo k. Record the earliest index for each remainder. A repeat at index i encloses a divisible interval after that earlier index; it is long enough when the distance is at least two. Keeping the earliest occurrence maximises that distance, so later occurrences should not overwrite it. Seed remainder zero at index -1 to represent the empty prefix and allow a subarray beginning at zero.

## Optimal solution, traced

```steps
nums = [23, 2, 4], k = 6; first = {0: -1}
    prefix remainders at indices 0 and 1 are 5 and 1
---
index 2 gives remainder 5, first seen at index 0
    distance 2, so [2, 4] qualifies: {{True}}
```

A repeated remainder at adjacent indices is not enough; keep its original index so a later repeat may still produce a valid length.

## Code

```python
def check_subarray_sum(nums, k):
    first = {0: -1}
    remainder = 0
    for i, value in enumerate(nums):
        remainder = (remainder + value) % k
        if remainder in first:
            if i - first[remainder] >= 2:
                return True
        else:
            first[remainder] = i
    return False
```

## Complexity

Expected O(n) time for hash operations and O(min(n, k)) auxiliary space, up to a constant for the seeded entry. There are only k possible remainders. Python's integer arithmetic avoids fixed-width sum overflow.

## Mistakes and edge cases

- Do not overwrite an earlier index after seeing a remainder again.
- Two zeros qualify; one zero alone does not. An array shorter than two always fails.
- The empty prefix has index -1, not zero; include distance exactly two.

## Variations

- Return a witness interval using the stored first index.
- For a zero divisor under a different specification, look for a length-two-or-more zero-sum subarray using exact prefix sums instead.

=== card | 16

## The problem

Choose three elements at distinct indices whose sum is closest to a given target; return that sum. The input has at least three integers. For `[-1, 2, 1, -4]` and target 1, return 2. The original task guarantees a unique closest sum, so a tie-breaking policy is unnecessary there.

## Constraints and what they imply

Values may be negative, duplicated, or positive, and the sum may be either side of the target. Exactly three occurrences are required, not three different values. The input need not be ordered. A cubic enumeration can become expensive as the input grows.

## Brute force

Enumerate all index triples `i < j < l`, compute each sum, and retain the one with smallest absolute difference from the target. There are O(n³) triples, so time is O(n³) and auxiliary space is O(1), apart from the input. This is straightforward and useful as a test oracle for small arrays.

## The insight

Sort a copy of the numbers and fix the first index, leaving the caller's input unchanged. For the two remaining indices, start at opposite ends. If the current sum is below target, moving the upper pointer left would only decrease it further; after recording this sum, no discarded pair using the current lower pointer and a smaller upper pointer can improve it. Move the lower pointer right instead. Symmetrically, if the sum is above target, move the upper pointer left. An exact match cannot be improved.

## Optimal solution, traced

```steps
sorted [-4, -1, 1, 2], target 1; fix -4
    -4 + -1 + 2 = -3; move lower pointer right
---
-4 + 1 + 2 = -1; next fix -1
    -1 + 1 + 2 = 2, closest sum = {{2}}
```

The initial best is a real triple, so the algorithm has a valid answer even if every sum is far from the target.

No special duplicate skipping is necessary for correctness: repeated values can lead to redundant comparisons but never cause an invalid triple, since the pointers always refer to different positions.

## Code

```python
def three_sum_closest(nums, target):
    values = sorted(nums)
    best = sum(values[:3])
    for i in range(len(values) - 2):
        left, right = i + 1, len(values) - 1
        while left < right:
            current = values[i] + values[left] + values[right]
            if abs(current - target) < abs(best - target):
                best = current
            if current == target:
                return current
            if current < target:
                left += 1
            else:
                right -= 1
    return best
```

## Complexity

Sorting costs O(n log n); n fixed indices each have a linear two-pointer scan, for O(n²) time total. The sorted copy uses O(n) space. The pointer variables themselves use O(1) space.

## Mistakes and edge cases

- Keep three different indices even if values repeat; stop when pointers meet.
- Compare absolute differences, not sums themselves. If ties are allowed, this code retains its first best sum.
- Exactly three elements still provide one valid candidate.

## Variations

- Return the three values along with the closest sum.
- Find a closest pair by using the same two-pointer scan without fixing a third element.

=== card | 2125

## The problem

A bank is a rectangular grid of `0` and `1` characters; a `1` is a security device. A beam connects each pair of devices in different rows when every row strictly between them contains no device. Count all such beams. In `["101", "000", "011", "010"]`, the answer is 6.

## Constraints and what they imply

Columns and horizontal distance do not restrict a beam. A row can have zero, one, or many devices, and empty rows can occur anywhere. Multiple devices in the same row do not connect to one another. The grid may be large, so it is important to avoid testing every device pair separately.

## Brute force

List all devices, inspect every pair in different rows, and scan the rows between them to check whether they are empty. With D devices and R rows this can take O(D²R) time; storing the device list takes O(D) space. It checks the same intervening rows repeatedly.

## The insight

Only consecutive nonempty rows can have beams between them. Any pair with another nonempty row between is blocked, while consecutive nonempty rows have no intervening devices. If those rows contain a and b devices, each of the a devices connects to each of the b, giving a times b beams. Scan rows in order and remember the previous nonempty count; empty rows do not replace it.

## Optimal solution, traced

```steps
rows "101", "000", "011", "010"
    first count 2; skip the empty row
---
next count 2 contributes 2 * 2 = 4
    final count 1 contributes 2 * 1 = 2; total {{6}}
```

The stored count always belongs to the most recent row with a device, so every legal row pair is counted once and no blocked pair is considered.

For example, two devices in one row and three in the next nonempty row contribute six regardless of their columns. Leading and trailing empty rows contribute nothing to the total.

## Code

```python
def number_of_beams(bank):
    previous = answer = 0
    for row in bank:
        count = row.count('1')
        if count:
            answer += previous * count
            previous = count
    return answer
```

## Complexity

For R rows and C columns, counting devices scans O(RC) characters and uses O(1) auxiliary space. The input itself is not copied. The answer can be much larger than the number of cells; Python integers support large counts.

## Mistakes and edge cases

- Do not reset the previous nonempty count when an empty row appears.
- Include the last nonempty row's contribution; a single nonempty row yields zero.
- Devices in the same row do not form beams, and columns do not have to align.

## Variations

- Return the beam contribution for each consecutive pair of nonempty rows.
- If devices are given as row counts directly, scan those counts instead of the full grid.

=== card | 946

## The problem

Given two sequences of distinct values, `pushed` and `popped`, decide whether a stack starting empty can push all values in the first order and pop all values in the second order. For `[1, 2, 3, 4, 5]` and `[4, 5, 3, 2, 1]`, the answer is true.

## Constraints and what they imply

The official sequences have the same length and consist of the same distinct values. Pushes must follow their specified order, but pushes and pops may interleave. A stack can pop only its current top. Merely checking that the sequences contain the same values cannot establish a valid ordering.

## Brute force

Explore every legal choice to push the next value or pop the current top, maintaining the remaining orders. An attempted pop is legal only if the top is the next required value. The number of interleavings can be exponential, with O(n) stack and recursion space per path. Many choices are unnecessary because an available required pop can be done immediately.

## The insight

Replay pushes in order. After each push, repeatedly pop while the stack top equals the next required output. Doing that pop immediately is safe: if a valid schedule delayed it, moving the pop earlier does not disturb any already required output, and later pushes still occur in their original order. If the top is not the next output, a pop cannot help, so the only possible progress is another push. Success means every requested pop was produced.

## Optimal solution, traced

```steps
pushed [1, 2, 3], popped [2, 3, 1]
    push 1, push 2; top equals 2, pop it
---
push 3, pop 3, then pop 1
    all required values produced: {{True}}
```

The index into `popped` is the count already produced. Guarding that index prevents reading beyond the end, including for empty sequences.

If all pushes have been processed while some requested pop remains, no legal push is left to reveal a different stack top. The simulation has therefore ruled out every possible schedule.

## Code

```python
def validate_stack_sequences(pushed, popped):
    if len(pushed) != len(popped):
        return False
    stack = []
    j = 0
    for value in pushed:
        stack.append(value)
        while stack and j < len(popped) and stack[-1] == popped[j]:
            stack.pop()
            j += 1
    return j == len(popped)
```

## Complexity

Each value is pushed once and popped at most once, so time is O(n) and auxiliary space is O(n) for the simulated stack. The while loop cannot perform more than n pops over the whole scan.

## Mistakes and edge cases

- A single push can expose several consecutive required pops, so use a while loop.
- Stop comparing when all requested pops are consumed.
- Two empty sequences are valid. A different length is rejected before simulation.

## Variations

- Produce the sequence of push and pop operations as a witness.
- If repeated values are allowed, simulate the same procedure but distinguish occurrences only when the specification requires their identities.

=== card | 240

## The problem

Given a rectangular matrix whose rows are nondecreasing left to right and whose columns are nondecreasing top to bottom, determine whether it contains a target. For `[[1, 4, 7], [2, 5, 8], [3, 6, 9]]`, searching for 6 returns true and searching for 10 returns false.

## Constraints and what they imply

Rows and columns are individually ordered, but the first element of one row need not exceed the last element of the previous row. Duplicate values are possible, and ranges of values from different rows can overlap.

## Brute force

Examine every cell until the target is found or the matrix is exhausted. For R rows and C columns this takes O(RC) time and O(1) auxiliary space. Searching each row independently with binary search improves this to O(R log C), but does not exploit both orderings at once.

## The insight

The matrix cannot generally be treated as one globally sorted flattened array. Instead, start at the top-right cell of the remaining rectangle. If its value is too large, all values below it in that column are at least as large, so discard that column by moving left. If it is too small, all values to its left in that row are at most as small, so discard that row by moving down. Equality succeeds. Each comparison removes an entire row or column without removing any possible match.

## Optimal solution, traced

```steps
matrix [[1, 4, 7], [2, 5, 8], [3, 6, 9]], target 6
    at 7: too large, move left to 4
---
4 and then 5 are too small, move down twice
    reach 6 and return {{True}}
```

The candidate region is the rows at or below the current row and columns at or left of the current column. When either coordinate leaves the matrix, the candidate region is empty.

An equality check must come before discarding a row or column; equal values may appear in several positions, but the question only asks whether at least one exists.

## Code

```python
def search_matrix(matrix, target):
    if not matrix or not matrix[0]:
        return False
    row, col = 0, len(matrix[0]) - 1
    while row < len(matrix) and col >= 0:
        value = matrix[row][col]
        if value == target:
            return True
        if value > target:
            col -= 1
        else:
            row += 1
    return False
```

## Complexity

Each step reduces the number of remaining rows or columns, so time is O(R + C) and auxiliary space is O(1). The empty-matrix guard also supports an empty input beyond the usual nonempty-grid constraint.

## Mistakes and edge cases

- Start at a corner where the two available directions have opposite order; the top-left corner does not provide that property.
- Do not binary-search the flattened array without a global ordering guarantee.
- One-row and one-column matrices work, as do repeated values and absent targets.

## Variations

- Start at the bottom-left and move up or right symmetrically.
- Count values at most a target by accumulating discarded column portions.

=== card | 1944

## The problem

People stand in a line with distinct heights. For each person, count the people to their right whom they can see. Person i sees person j when every person strictly between them is shorter than both endpoints. Return one count per person. For `[10, 6, 8, 5, 11, 9]`, the result is `[3, 1, 2, 1, 1, 0]`.

## Constraints and what they imply

Heights are distinct in the official problem; equality would need an explicitly specified blocking rule and different handling. A person always sees the immediate neighbour to the right, but a tall intermediate person can hide many others. The output has n entries, and large n rules out a separate full scan from each person in the worst case.

## Brute force

For each i, inspect every j to its right while tracking the maximum height strictly between i and j. Count j exactly when that maximum is less than both endpoint heights. Update the maximum after the comparison so the target person is not included among the intervening people. Each pair is inspected once, giving O(n²) time, O(1) working space, and O(n) output space. This direct definition is valuable for small independent tests.

## The insight

Process people from right to left, keeping a stack of candidates visible from positions still farther left. Its heights decrease from bottom to top. For a new height h, the top is the nearest remaining candidate. If it is shorter than h, it is visible: everyone between h and that candidate is shorter than that candidate. Pop it and count it. It is now hidden from every future person to the left by h, which is closer and taller. Continue until the stack is empty or its top is taller than h. A remaining taller top is also visible, but blocks every candidate behind it for h; count it once and stop. Push h as a future candidate.

Why can a popped candidate never matter again? Any observer left of h who might see the popped shorter person must also look past h. Because h exceeds that person's height, the strict visibility condition fails regardless of the observer's own height. Conversely, candidates not popped retain the same relative blocking relationships. This establishes the invariant inductively, beginning with an empty stack at the right edge.

## Optimal solution, traced

```steps
heights [10, 6, 8, 5, 11, 9], scan from the right
    9 sees nobody; 11 pops 9 and sees one; stack [11]
---
5 sees 11; 8 pops 5 and sees 11: count 2
    6 sees 8; stack from bottom is [11, 8, 6]
---
10 pops 6 and 8, then sees 11
    counts from left to right are {{[3, 1, 2, 1, 1, 0]}}
```

The stack stores heights rather than indices because the output is written at the current index and a height comparison is all that is needed. The first taller person is counted but retained: it may be visible to a later observer farther left.

## Code

```python
def can_see_persons_count(heights):
    answer = [0] * len(heights)
    stack = []
    for i in range(len(heights) - 1, -1, -1):
        while stack and stack[-1] < heights[i]:
            stack.pop()
            answer[i] += 1
        if stack:
            answer[i] += 1
        stack.append(heights[i])
    return answer
```

## Complexity

Each height is pushed once and popped at most once. Despite the nested loop, the total time is O(n). The stack can contain n heights, so auxiliary space is O(n); the returned array is another O(n). A strictly increasing input exhibits a large stack in this scan direction.

## Mistakes and edge cases

- Count the first taller person but do not pop it; that person blocks all remaining candidates for the current observer.
- Count every shorter candidate popped, rather than only the last one.
- The final person sees nobody. An increasing line gives one visible neighbour per position except the last; a decreasing line does too, because the immediate taller-than-the-rest neighbour blocks those behind it.
- Distinct heights are essential to this exact comparison: duplicate heights require a separate treatment consistent with strict visibility.

## Variations

- Return the indices of visible people instead of counts; the output itself can be larger than linear.
- Count visibility in the opposite direction by reversing the traversal.
- Compute the next greater element for each person instead of the complete visibility count.

=== card | 328

## The problem

Reorder a singly linked list so that nodes originally at odd positions come first, followed by nodes originally at even positions. Positions are one-based; preserve the relative order within each group. Rewire the existing nodes and return the new head. Thus `1 -> 2 -> 3 -> 4 -> 5` becomes `1 -> 3 -> 5 -> 2 -> 4`.

## Constraints and what they imply

The grouping depends on position, not whether a node's value is odd or even. The list may be empty or have only one node, and node values can repeat. The intended solution uses constant extra space and preserves the actual nodes rather than constructing replacement nodes. Every `next` update must avoid losing the remainder of the list or forming a cycle.

## Brute force

Traverse the list and save its node references in an array; then relink odd-position references in their original order, followed by the even-position references. This uses O(n) time and O(n) auxiliary space. Saving references makes the reordering easy but exceeds the constant-space goal.

## The insight

Keep tails for the growing odd-position chain and even-position chain, and save the first even node for the final connection. Initially the first and second nodes are those tails. While an even tail has a successor, link the odd tail to that successor and advance the odd tail. Then link the even tail to the next node after the new odd tail and advance the even tail. The unprocessed suffix remains reachable through the even tail until it ends. Finally append the saved even head to the odd tail.

## Optimal solution, traced

```steps
1 -> 2 -> 3 -> 4 -> 5; odd = 1, even = 2, saved even head = 2
    link 1 to 3, then 2 to 4; tails become 3 and 4
---
link 3 to 5, then 4 to None; append saved 2 after 5
    return {{1 -> 3 -> 5 -> 2 -> 4}}
```

The even tail terminates the even chain as it advances. A two-node list does not enter the loop and the final link simply preserves its order.

## Code

```python
def odd_even_list(head):
    if head is None:
        return None
    odd = head
    even = even_head = head.next
    while even is not None and even.next is not None:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head
```

## Complexity

Every node is visited a constant number of times, so time is O(n) and auxiliary space is O(1). The output reuses the input nodes; no node-value copies or auxiliary arrays are required.

## Mistakes and edge cases

- Save the even head before moving the even tail; otherwise the second group is lost.
- Stop when either the even tail or its successor is absent.
- Group by original position, not by value. Empty and one-node lists remain unchanged.

## Variations

- Stably partition nodes by a predicate on their values using two head-and-tail pairs.
- Group nodes by position modulo three, preserving the order inside each group.

=== card | 2300

## The problem

Given positive integer spell strengths, positive potion strengths, and a positive success threshold, return for each spell how many potions produce a product at least the threshold. A potion may be reused for each independent spell. With spells `[5, 1, 3]`, potions `[1, 2, 3, 4, 5]`, and success 7, the answer is `[4, 0, 3]`.

## Constraints and what they imply

Spells and potions can each be numerous, and their original orders matter only for the spell answers. Values and threshold can be large, so exact integer comparisons are preferable to floating-point rounding. Strengths are strictly positive. Repeated strengths count as separate potions.

## Brute force

For each spell, multiply it by every potion and count products reaching the threshold. With n spells and m potions, this costs O(nm) time and O(1) auxiliary space beyond the O(n) output. It does not reuse any work between spells.

## The insight

Sort a copy of the potions. Multiplying by a positive spell preserves their order, so all successful potions form a suffix of that sorted array. The smallest sufficient potion has value at least `ceil(success / spell)`, computed exactly as `(success + spell - 1) // spell`. Binary search for the first potion at least that value; all positions from there through the end are successful. This also handles a threshold larger than every potion or satisfied by all potions.

## Optimal solution, traced

```steps
potions [1, 2, 3, 4, 5], success 7, spell 5
    minimum potion is ceil(7 / 5) = 2; first qualifying index is 1
---
there are 5 - 1 = 4 successes
    spells 1 and 3 give 0 and 3; return {{[4, 0, 3]}}
```

The lower-bound search places all qualifying duplicates in the suffix, including values whose product is exactly equal to success.

Each answer is appended in the original spell order. Sorting only the potions means there is no need to remember original potion indices or to restore their order afterward.

## Code

```python
from bisect import bisect_left

def successful_pairs(spells, potions, success):
    ordered = sorted(potions)
    answer = []
    for spell in spells:
        minimum = (success + spell - 1) // spell
        first = bisect_left(ordered, minimum)
        answer.append(len(ordered) - first)
    return answer
```

## Complexity

Sorting takes O(m log m); the n binary searches take O(n log m), with the usual constant-time handling of an empty list. The sorted copy needs O(m) auxiliary space, plus O(n) for the returned counts. Python integers avoid fixed-width product or ceiling overflow.

## Mistakes and edge cases

- Use a lower bound, not an upper bound: a product equal to the threshold succeeds.
- Compute a ceiling rather than floor division. Floating-point division can lose precision for large integers.
- One potion may succeed for many different spells; do not consume it between queries.

## Variations

- Sort spells as well and advance a monotone potion pointer, restoring answer order afterward.
- Binary-search directly on the product comparison instead of computing a ceiling.

=== card | 1019

## The problem

For each node of a singly linked list, return the value of the first later node whose value is strictly greater. If no such node exists, return zero for that position. For `2 -> 1 -> 5`, the result is `[5, 5, 0]`. The returned array follows the list's original order.

## Constraints and what they imply

The official list contains positive values, so zero unambiguously indicates no later greater value. Equal values are not greater, and a closer smaller node does not prevent a later larger node from being the answer. Random access is unavailable in the linked list, but the result needs one entry per node anyway.

## Brute force

For each node, walk forward until finding the first greater value or reaching the end. On a nonincreasing list, every scan reaches the end, producing O(n²) time. Beyond the O(n) output, this approach uses O(1) auxiliary space.

## The insight

Maintain a stack of unresolved nodes as `(index, value)` pairs while traversing from left to right. When a new value is strictly greater than the stack top, it is the first greater value for that top: any intervening larger value would already have resolved it. Pop and fill its answer, repeating while the new value is greater. Then push the new node, which has not yet seen any later values. Remaining stack entries keep the initial zero answer.

## Optimal solution, traced

```steps
list 2 -> 1 -> 5
    push (0, 2), then (1, 1); neither has an answer yet
---
5 pops 1 and 2, filling both answers with 5
    push 5; it stays unresolved: {{[5, 5, 0]}}
```

The unresolved values are nonincreasing from bottom to top. Equal values may coexist on the stack, since neither resolves the other, and a later larger value resolves both.

The list itself is traversed only once. The stored pair supplies the old value needed for a comparison and the output position needed when a matching later node finally appears.

## Code

```python
def next_larger_nodes(head):
    answer = []
    stack = []
    node = head
    while node is not None:
        value = node.val
        while stack and stack[-1][1] < value:
            index, _ = stack.pop()
            answer[index] = value
        stack.append((len(answer), value))
        answer.append(0)
        node = node.next
    return answer
```

## Complexity

Each node is pushed and popped at most once, so time is O(n). The unresolved stack uses O(n) auxiliary space in the worst case, and the answer uses O(n) output space. The list is not modified.

## Mistakes and edge cases

- Use a strict comparison so an equal later value is not reported as greater.
- Store indices as well as values to write answers in original order.
- A single node returns `[0]`; an empty list returns an empty list.

## Variations

- Return the number of nodes until the next greater value instead of that value.
- Find the next smaller node by reversing the comparison.

=== card | 1248

## The problem

Count nonempty contiguous subarrays containing exactly `k` odd numbers. For `[1, 1, 2, 1, 1]` and `k = 3`, the answer is 2. Two intervals with different boundaries count separately, even if they contain the same odd values.

## Constraints and what they imply

Even values can be included at either end without changing an interval's odd count. Different choices of endpoints are counted separately. The official k is positive, but the implementation also handles zero.

## Brute force

For every starting position, extend the end to the right, incrementing a count when the new value is odd. Add one whenever that count equals k. This examines O(n²) intervals, taking O(n²) time and O(1) auxiliary space. It is an effective reference for small arrays.

## The insight

Only the parity of each integer affects whether an interval qualifies. Map each value to one if odd and zero if even. A subarray has exactly k odds when its mapped sum is k. If the running odd count at the current end is total, any earlier prefix with odd count `total - k` defines a valid start. Keep a frequency table of previous prefix counts; different previous positions with the same count create different intervals. Seed count zero once for the empty prefix and query before adding the current prefix.

## Optimal solution, traced

```steps
nums = [2, 1, 2], k = 1; prefix counts initially {0: 1}
    after first even, zero has frequency 2
---
odd gives total 1 and contributes 2; final even contributes another 2
    answer = {{4}}
```

Using the parity remainder also works for negative Python integers. The approach counts intervals, not just groups of consecutive odd positions.

For the trace, the four intervals are the odd element alone, its extension by either even neighbour, and the interval including both neighbours. Each has a different pair of boundaries.

## Code

```python
from collections import defaultdict

def number_of_nice_subarrays(nums, k):
    frequencies = defaultdict(int)
    frequencies[0] = 1
    total = answer = 0
    for value in nums:
        total += value % 2
        answer += frequencies[total - k]
        frequencies[total] += 1
    return answer
```

## Complexity

Expected O(n) time and O(n) auxiliary space for the frequency table. At most n + 1 distinct prefix odd counts occur, and the result can be quadratic in n when k is zero and all elements are even.

## Mistakes and edge cases

- Seed the empty prefix or intervals beginning at index zero are lost.
- Keep counts of repeated prefix totals; even numbers cause repeats.
- Query before inserting the current prefix to avoid counting an empty interval when k is zero.

## Variations

- Subtract the counts of intervals with at most k and at most k - 1 odd numbers.
- Replace parity with any Boolean predicate and count intervals containing exactly k matches.

=== card | 1283

## The problem

Given positive integers and a threshold, find the smallest positive divisor such that the sum of each number divided by that divisor and rounded up is at most the threshold. For `[1, 2, 5, 9]` and threshold 6, the answer is 5: the rounded quotients sum to 1 + 1 + 1 + 2 = 5.

## Constraints and what they imply

The numbers are positive and the official threshold is at least the array length, ensuring that a valid divisor exists. Each rounded quotient is at least one, so a threshold below n would be impossible. Individual values can be large; checking every potential divisor can be too slow.

## Brute force

Try divisors in increasing order from one through the maximum input value, compute every rounded-up quotient, and return the first feasible divisor. For n numbers and maximum M, this takes O(nM) time and O(1) auxiliary space. Its simple enumeration is useful for checking small examples.

## The insight

As the divisor increases, no positive rounded-up quotient increases, so the feasibility predicate `sum <= threshold` is false for an initial range and true thereafter. A divisor equal to the maximum input value M gives a sum of n and is therefore feasible. Binary search the first feasible divisor in `[1, M]`. When the middle is feasible, keep it as a possible answer and discard larger values; otherwise discard it and all smaller values. Compute each ceiling exactly as `(x + d - 1) // d`.

## Optimal solution, traced

```steps
nums = [1, 2, 5, 9], threshold = 6; search [1, 9]
    d = 5 gives sum 5, so keep [1, 5]
---
d = 3 gives sum 7, so keep [4, 5]; d = 4 gives sum 7
    first feasible divisor is {{5}}
```

The right endpoint always remains feasible, and every divisor below the left endpoint is known to be infeasible. When the endpoints meet, both facts identify the minimum.

For a single positive number and threshold one, the minimum divisor is the number itself. When the threshold is at least the sum of all inputs, divisor one is already feasible.

## Code

```python
def smallest_divisor(nums, threshold):
    left, right = 1, max(nums)
    while left < right:
        mid = (left + right) // 2
        total = sum((value + mid - 1) // mid for value in nums)
        if total <= threshold:
            right = mid
        else:
            left = mid + 1
    return left
```

## Complexity

Each feasibility check scans n numbers and there are O(log M) checks, for O(n log M) time. The generator and search variables use O(1) auxiliary space. If M is one, there are no checks and the known feasible endpoint is returned.

## Mistakes and edge cases

- Round each quotient up before summing, not the sum of ordinary quotients.
- Keep a feasible midpoint when looking for the first true value.
- The stated contract requires a nonempty array and threshold at least its length.

## Variations

- Stop computing a feasibility sum early once it exceeds the threshold.
- Find the largest feasible value in a different monotone predicate by reversing the binary-search boundary choices.

=== card | 2966

## The problem

Divide the array into groups of exactly three values, using every occurrence once, so that the difference between the maximum and minimum within each group is at most `k`. Return any valid list of triples or an empty list if no division exists. The array length is a multiple of three. For `[1, 3, 4, 8, 7, 9]` and `k = 2`, `[[1, 3, 4], [7, 8, 9]]` is invalid because the first span is 3; no valid grouping exists.

## Constraints and what they imply

Numbers may repeat, and occurrences rather than distinct values must be used. Group order and the order inside each triple do not matter. The bound is inclusive and applies to every pair, equivalently to the maximum minus minimum. A large array makes enumeration of partitions impractical.

## Brute force

Choose three remaining occurrences for the first group, reject it if its span is too large, and recursively partition the rest. The number of partitions grows super-exponentially with the number of groups; recursion and copied remaining arrays can use O(n²) space along a path. This can still serve as an oracle for very small inputs.

## The insight

Sort the numbers and form consecutive triples. To justify this, take the three smallest remaining occurrences a, b, c in a valid partition. The valid group containing a has two other members at least as large as b and c, so `c - a <= k`. Replace that group by `[a, b, c]`, exchanging any missing b or c for a displaced member x from a's group. Each such x is at least the occurrence it replaces and at most a + k. In the recipient group, if x is no larger than its old maximum, the span cannot increase; otherwise x becomes the maximum and every member is at least a, so the span is still at most k. Repeat on the remaining values. Thus failure of a consecutive triple proves impossibility.

## Optimal solution, traced

```steps
nums [1, 3, 4, 8, 7, 9], k = 3; sorted [1, 3, 4, 7, 8, 9]
    first triple [1, 3, 4] spans 3 and is valid
---
second triple [7, 8, 9] spans 2
    return {{[[1, 3, 4], [7, 8, 9]]}}
```

The proof uses the smallest remaining values at each step, including duplicates. The result uses a sorted copy and does not change the supplied array.

## Code

```python
def divide_array(nums, k):
    values = sorted(nums)
    answer = []
    for i in range(0, len(values), 3):
        if values[i + 2] - values[i] > k:
            return []
        answer.append(values[i:i + 3])
    return answer
```

## Complexity

Sorting costs O(n log n) time; the final pass costs O(n). The sorted copy and returned triples each use O(n) space. A failed result may still allocate the sorted copy and previously constructed groups.

## Mistakes and edge cases

- A span exactly k is valid; reject only a strictly larger span.
- Treat duplicates as separate occurrences and include every occurrence once.
- The code assumes length is divisible by three, as promised; an empty input produces an empty result.

## Variations

- Partition into groups of another fixed size with the same maximum-span condition.
- Return the minimum possible largest group span for a fixed group size.

=== card | 1209

## The problem

Repeatedly remove any run of exactly `k` equal adjacent characters from a string until no such group remains. Return the final string. For `s = "deeedbbcccbdaa"` and `k = 3`, the result is `"aa"`. Removing a group may bring equal letters together and trigger further deletions.

## Constraints and what they imply

The official input uses lowercase letters and `k >= 2`. A run longer than k can be reduced by repeatedly removing k characters. The string can be long, so repeatedly rebuilding it after each deletion may be costly. The order of the surviving characters must remain unchanged.

## Brute force

Search the whole current string for a block of k equal neighbours; delete the first one found by slicing and concatenation, then start again. There can be O(n/k) deletions, each requiring O(n) scanning and copying, so a straightforward implementation takes O(n²) time and O(n) space. It provides a direct small-input simulation.

## The insight

Process the characters from left to right, keeping the fully reduced prefix as a stack of character and run-length pairs. If the next character matches the top run, increment that run; otherwise start a new one. When the top count reaches k, remove that run. The exposed previous run can then merge with future characters, naturally handling cascades. At every step the stack is exactly the reduced form of the processed prefix: the only new removable group must end at the newly added character.

## Optimal solution, traced

```steps
s = "abbba", k = 3
    push a:1; then b counts 1, 2, 3 and is removed
---
last a joins the exposed a run to make a:2
    no count reaches 3; return {{"aa"}}
```

A run is removed immediately on reaching k, so a stored count is always below k. Reconstruct the result once after the scan rather than repeatedly concatenating in the loop.

## Code

```python
def remove_duplicates(s, k):
    stack = []
    for ch in s:
        if stack and stack[-1][0] == ch:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()
        else:
            stack.append([ch, 1])
    return ''.join(ch * count for ch, count in stack)
```

## Complexity

Each character causes constant stack work and the final join emits at most n characters, giving O(n) time. The stack and output use O(n) space in the worst case. The temporary strings built for the join contain O(n) characters in total.

## Mistakes and edge cases

- Remove a run as soon as its count reaches k, then allow future input to meet the exposed run.
- Do not use repeated immutable string concatenation inside the main scan.
- A string shorter than k remains unchanged; a run of 2k identical characters disappears completely.

## Variations

- For k = 2, use a character stack and cancel matching adjacent pairs.
- Return both the reduced string and the number of removed groups.

=== card | 572
time: 25 min

## The problem

Given two nonempty binary trees, decide whether the second appears as a complete subtree of the first. A match starts at a node and includes every descendant, including the absence of children; matching only some values or branches is not enough. For example, a single node 4 matches a leaf 4 but not a node 4 with a child.

## Constraints and what they imply

The larger input has at most 2,000 nodes and the candidate has at most 1,000. Values range from -10,000 to 10,000 and may repeat. Either shape can be skewed, so tree height can be linear in node count. The function below accepts `None` for an empty tree as well, interpreting an empty candidate as a subtree of any tree.

## Brute force

At every node, compare the whole candidate with the subtree rooted there. Compare values and recursively compare both corresponding children, treating one missing child as a mismatch. With many repeated values, almost every comparison can examine most of the candidate, so this takes O(mn) time in the worst case.

## The insight

Encode each tree in preorder as a sequence of typed tokens, explicitly representing null children. A value token is distinct from a null token and from every other value, so neither a multi-digit value nor a missing branch can produce an accidental partial match. This encoding is self-delimiting: a value begins exactly two encoded child trees, while a null completes one child. Therefore an occurrence of the candidate sequence starts at a real node and describes exactly that node's subtree.

Search the candidate tokens in the larger sequence using the prefix-function form of KMP. On a mismatch, the prefix table tells us the longest prefix that might still match, without revisiting earlier text tokens.

## Optimal solution, traced

```steps
Main tree has root 3, left leaf 4, right leaf 5; candidate is leaf 4
    main tokens: 3, 4, null, null, 5, null, null
---
Candidate tokens are 4, null, null
    the first main token does not match
---
The next three main tokens match in order
    answer {{True}}
```

Serialisation uses an explicit stack rather than recursion, so a long chain does not exceed Python's recursion limit. The prefix table and search each advance or fall back only a linear number of times.

## Code

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def is_subtree(root, sub_root):
    if sub_root is None:
        return True

    def tokens(node):
        result = []
        stack = [node]
        while stack:
            current = stack.pop()
            if current is None:
                result.append((0,))
            else:
                result.append((1, current.val))
                stack.append(current.right)
                stack.append(current.left)
        return result

    text, pattern = tokens(root), tokens(sub_root)
    prefix = [0] * len(pattern)
    j = 0
    for i in range(1, len(pattern)):
        while j and pattern[i] != pattern[j]:
            j = prefix[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        prefix[i] = j
    j = 0
    for token in text:
        while j and token != pattern[j]:
            j = prefix[j - 1]
        if token == pattern[j]:
            j += 1
        if j == len(pattern):
            return True
    return False
```

## Complexity

For m and n nodes, serialisation and KMP take O(m + n) time and O(m + n) auxiliary space for the token sequences, table and traversal stack. Each binary tree contributes one null token per missing child, so token count is linear.

## Mistakes and edge cases

- Values alone cannot distinguish a left child from a right child. Keep null markers and token boundaries.
- A leaf cannot match a node that has extra descendants. Repeated values are allowed.
- The empty-candidate convention is explicit; both original inputs are nonempty.

## Variations

- Return the matching root rather than a boolean by retaining token-to-node positions.
- Check exact tree equality by comparing the two complete serialisations.

=== card | 692
time: 30 min

## The problem

Given a list of words and an integer k, return the k distinct words that appear most often. Order results by decreasing frequency and break equal-frequency ties in ascending alphabetical order. For `["tea", "eat", "tea", "eat", "ice"]` and k = 2, the answer is `["eat", "tea"]`.

## Constraints and what they imply

There are at most 500 words, each containing one to ten lowercase English letters. The supplied k is between one and the number of distinct words. Repeated words contribute separately to frequency; the output contains each selected word only once. The ranking order is part of the answer, not merely a set of winners. A follow-up asks for a solution whose selection cost depends logarithmically on k.

## Brute force

Count the frequency of each distinct word by repeatedly scanning the full input, then sort all distinct words using their counts and spelling. This is straightforward, but the repeated scans cost O(nu) for n words and u distinct words. Even if counts are built efficiently, sorting all u candidates costs O(u log u), regardless of whether k is small.

## The insight

Count in one pass. A word's complete ranking key is `(-frequency, word)`: smaller keys are better because a larger count becomes a smaller negative number, and equal counts then use normal alphabetical order. Select the k smallest keys with a bounded heap rather than ordering every distinct candidate. Finally, the library returns the selected words in key order.

The two parts of the key are essential. A heap that keeps only counts might retain an arbitrary word at the frequency boundary, and sorting the chosen words afterward cannot recover a better word already discarded. The composite ranking decides both membership and output order.

## Optimal solution, traced

```steps
Count tea twice, eat twice, and ice once
    keys: tea (-2, tea), eat (-2, eat), ice (-1, ice)
---
Select the two smallest keys
    eat precedes tea because their counts tie
---
Return the selected words in ranking order
    answer {{[eat, tea]}}
```

`heapq.nsmallest` maintains a bounded selection heap for k smaller than the candidate count. When k covers every candidate, its full-sort shortcut has the same asymptotic bound expressed in terms of k.

## Code

```python
from collections import Counter
from heapq import nsmallest


def top_k_frequent(words, k):
    counts = Counter(words)
    return nsmallest(k, counts, key=lambda word: (-counts[word], word))
```

## Complexity

Let n be the number of words and u their distinct count. Counting costs O(n), and selection plus output ordering costs O(u log(k + 1)) comparisons. Counts and the selection structure occupy O(u) auxiliary space. Comparing words also costs up to the word length; the standard length bound is constant.

## Mistakes and edge cases

- Reverse only the frequency, not the alphabetical tie-breaker.
- k can equal u, in which case every distinct word must be returned in rank order.
- A tie at the selection boundary still needs alphabetical resolution.

## Variations

- Return frequencies alongside the chosen words using the same counter.
- If all distinct words are required, sort all keys directly instead.

=== card | 1288
time: 30 min

## The problem

Given intervals `[left, right]`, count those not covered by another interval. Interval `[a, b]` is covered by `[c, d]` when `c <= a` and `b <= d`. For `[[1, 4], [2, 3], [3, 6]]`, the middle interval is covered, so the answer is 2. Intervals are compared as intervals, not as individual points.

## Constraints and what they imply

There are at most 1,000 intervals; endpoints are nonnegative integers up to 100,000, each left endpoint is strictly less than its right endpoint, and the original intervals are unique. Equal starts and equal ends are possible. A covering interval may have the same start or the same end, so both inequalities are inclusive. The input need not arrive in any useful order.

## Brute force

For each interval, compare it with every other interval and mark it covered if both endpoint inequalities hold. This directly implements the definition and costs O(n²) time. It uses O(1) additional space if the count is maintained directly, but repeats comparisons among intervals whose relative positions already rule out coverage.

## The insight

Sort by increasing left endpoint, breaking ties by decreasing right endpoint. A possible covering interval then appears before the interval it covers. For an equal start, the longer interval must come first; otherwise a shorter interval would be incorrectly counted before its cover appears.

Maintain the largest right endpoint among intervals already processed. The current interval is covered exactly when its right endpoint is at most that maximum: some earlier interval attains the maximum and starts no later. Otherwise no earlier interval covers it, and no later interval can cover it because later starts are larger, or equal starts have no larger end. Count it and update the maximum.

## Optimal solution, traced

```steps
Sort [1,4], [2,3], [3,6]
    largest end initially absent
---
Visit [1,4] and then [2,3]
    first is kept; 3 is at most 4, so the second is covered
---
Visit [3,6]
    6 exceeds 4, so the count becomes {{2}}
```

The stored maximum includes covered intervals too, although a covered interval cannot increase it. Thus the same invariant holds after every processed prefix.

## Code

```python
def remove_covered_intervals(intervals):
    ordered = sorted(intervals, key=lambda interval: (interval[0], -interval[1]))
    largest_end = float('-inf')
    count = 0
    for left, right in ordered:
        if right > largest_end:
            count += 1
            largest_end = right
    return count
```

## Complexity

Sorting takes O(n log n) time, and the scan takes O(n). This non-mutating version allocates O(n) space for the sorted copy. It also leaves the caller's interval order intact. An in-place sort avoids that copy, though Python's sorting implementation can still use O(n) temporary space.

## Mistakes and edge cases

- Ascending ends for equal starts produce a false survivor.
- Equality of right endpoints still means coverage.
- One interval survives; the implementation also returns zero for an empty list.

## Variations

- Return the surviving intervals instead of just their count.
- If duplicates are allowed and coverage requires a distinct interval, decide explicitly whether to remove all copies.

=== card | 103
time: 30 min

## The problem

Return the values of a binary tree grouped by depth, starting at the root. Report the first level from left to right, the next from right to left, and continue alternating. For a root 1 with children 2 and 3 and grandchildren 4 and 5 under 2, the output is `[[1], [3, 2], [4, 5]]`. An empty tree produces an empty list.

## Constraints and what they imply

The tree contains up to 2,000 nodes, with integer values between -100 and 100. Values may repeat and are not identifiers. The shape can be uneven or a long chain. A level consists of every node at the same depth, even when parents are missing children. Only the order of reported values alternates; the definition of a child or a depth does not change.

## Brute force

For each depth, traverse the tree again and collect nodes at that depth, reversing the list on alternating levels. This correctly groups nodes but revisits upper levels repeatedly. On a chain of n nodes, there are n levels and the total work is O(n²); even a balanced tree repeats work across its height.

## The insight

Keep a queue of nodes awaiting processing. At the start of each iteration, its current length is exactly the number of nodes at the next depth. Remove exactly that many nodes, collecting their values while appending their existing children in normal left-to-right order. Their children form the next level, not part of the one currently being collected.

Reverse the completed value list on every other level. The queue stays in natural order regardless of output direction, avoiding complicated changes to the child insertion order. Each node enters and leaves the queue once, and each value is reversed at most once.

## Optimal solution, traced

```steps
Queue starts with root 1
    report [1], enqueue 2 then 3
---
Process exactly two nodes at depth 1
    values [2,3] reverse to [3,2]; enqueue 4 then 5
---
Process the next two nodes in natural order
    output {{[[1], [3,2], [4,5]]}}
```

The fixed level length is crucial: otherwise children appended during the iteration would be consumed prematurely. Alternating a boolean after finishing a whole level makes the root level left to right.

## Code

```python
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def zigzag_level_order(root):
    if root is None:
        return []
    queue = deque([root])
    answer = []
    left_to_right = True
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        if not left_to_right:
            level.reverse()
        answer.append(level)
        left_to_right = not left_to_right
    return answer
```

## Complexity

Each node is enqueued and removed once, and reversals touch at most n values in total, so time is O(n). The queue holds at most two adjacent levels, O(w) space for maximum width w; output storage is O(n). A chain needs only a small queue even though it has n levels.

## Mistakes and edge cases

- Toggle direction per level, not per node.
- Take the queue length before processing that level.
- An empty root returns `[]`; repeated values must all remain in the output.

## Variations

- Report ordinary level order by omitting the reversal.
- Produce a flat alternating sequence by extending a single result with each completed level.

=== card | 1029
time: 30 min

## The problem

There are `2n` people and two cities. Person i has a cost to fly to each city. Send exactly n people to each city and minimize total cost. For `[[10,20], [30,200], [400,50], [30,20]]`, sending the first two to A and the other two to B costs 110. Choosing each person's cheaper city independently may violate the required quota.

## Constraints and what they imply

The original input has an even number of people, between 2 and 100, and each positive cost is at most 1,000. Costs and cost differences can tie; multiple assignments may therefore achieve the same minimum. Both quotas are exact, and every person must be assigned once. We return only the cost, not the chosen assignments.

## Brute force

Try every subset of n people for city A and assign everyone else to B. Compute each assignment's cost and take the minimum. This is correct because every feasible assignment corresponds to one such subset, but there are `C(2n, n)` choices, which grows exponentially. Merely choosing the lowest absolute A costs is not sufficient because the alternative B costs matter too.

## The insight

Imagine everyone assigned to B first. Moving person i to A changes the total by `A_i - B_i`; this difference can be negative, zero, or positive. Exactly n people must move. Therefore select the n smallest differences and add those changes to the baseline. Sorting differences places those people first.

For an exchange proof, consider any feasible selection containing a larger difference while leaving out a smaller one. Swapping the two preserves both city quotas and does not increase cost. Repeating such swaps reaches the selection of the n smallest differences. Ties are harmless because exchanging equal differences leaves the total unchanged.

## Optimal solution, traced

```steps
Assign everyone to B
    baseline is 20 + 200 + 50 + 20 = 290
---
Differences A minus B are -10, -170, 350, 10
    choose the two smallest: -170 and -10
---
Apply those changes to the baseline
    answer {{110}}
```

The algorithm sorts a new list of numeric differences, so the input remains untouched. Negative differences are savings, but the exact quota still requires selecting n people even if fewer than n moves save money.

## Code

```python
def two_city_cost(costs):
    baseline = sum(b for a, b in costs)
    changes = sorted(a - b for a, b in costs)
    return baseline + sum(changes[:len(costs) // 2])
```

## Complexity

Computing the baseline and differences is O(n), and sorting 2n differences takes O(n log n) time. The list of differences, slice, and Python's sorting workspace use O(n) auxiliary space. The cost does not depend on the magnitude of the prices.

## Mistakes and edge cases

- Sort by the difference, not by either city cost alone.
- Select exactly half, even when all differences are positive.
- Equal costs and equal differences may yield many optimal assignments.

## Variations

- Return the chosen people as well by sorting indexed differences.
- If the quotas differ, select exactly the required number for A rather than half.

=== card | 1233
time: 30 min

## The problem

Given a collection of absolute folder paths, remove every path that is a subfolder of another path in the collection. Return the remaining paths in any order. For `["/a", "/a/b", "/ab", "/c/d"]`, the result is `["/a", "/ab", "/c/d"]`. `/a/b` is below `/a`, while `/ab` is a different folder rather than a child of `/a`.

## Constraints and what they imply

There are up to 40,000 distinct paths, each of length at most 100. Paths start with a slash and contain lowercase folder names separated by single slashes; no input is the root path itself. A descendant relationship must cross a slash boundary after the parent path. A path's parent need not itself appear in the input, so it must be retained unless some listed ancestor covers it.

## Brute force

For each path, check every other path as a possible ancestor. A path is removable if it starts with the other path followed immediately by `/`. This exactly implements the component-boundary rule but may perform O(n²) prefix comparisons. Each comparison can inspect up to L characters, giving O(n²L) time for maximum path length L.

## The insight

Sort the paths lexicographically. A path precedes its descendants, because it is a prefix of each. All strings beginning with `parent + "/"` form one contiguous block, and `/` sorts before the lowercase letters that might extend the final folder name. Consequently that block follows the parent before paths like `/ab`.

Scan the sorted list, retaining a path only when it is not below the most recently retained one. If a parent was discarded because it was itself a descendant, its retained ancestor also covers the child's entire descendant block. Once another non-descendant is retained, no later path can return to the previous ancestor's contiguous block. Thus one retained path is enough for the check.

## Optimal solution, traced

```steps
Sort /a, /a/b, /ab, /c/d
    keep /a first
---
/a/b begins with /a plus a slash
    discard it; /ab does not, so keep /ab
---
/c/d is not under /ab
    answer {{[/a, /ab, /c/d]}}
```

The precise character alphabet matters to the one-previous-path argument. For arbitrary path characters or a different collation, use a component trie or explicitly verify the ordering property rather than assuming it.

## Code

```python
def remove_subfolders(folders):
    answer = []
    for path in sorted(folders):
        if not answer or not path.startswith(answer[-1] + '/'):
            answer.append(path)
    return answer
```

## Complexity

Sorting costs O(n log n) string comparisons, each up to O(L), and the scan makes O(n) prefix checks of length at most L. Time is O(nL log n); the sorted copy and answer require O(n) references, plus O(L) for a temporary prefix. The original strings are not copied.

## Mistakes and edge cases

- Test `parent + "/"`, not merely `parent`; `/a` does not cover `/ab`.
- A discarded intermediate folder can still have descendants.
- A lone path is retained, even if its own parent is not listed.

## Variations

- Use a trie of path components and stop exploring below any listed folder.
- Return removed paths as well, remembering the ancestor responsible for each.

=== card | 1382
time: 30 min

## The problem

Rebuild a binary search tree so it has the same values but is height-balanced: at every node, the heights of its two child subtrees differ by at most one. Return the new root. A chain containing 1, 2, 3 can become root 2 with children 1 and 3. Any correctly balanced tree with the same values is acceptable.

## Constraints and what they imply

The original tree has between 1 and 10,000 nodes with distinct positive values up to 100,000. It obeys the binary search tree ordering, but it may be a chain of linear height. The result may use new nodes; it must not omit values or merely balance the root while leaving a lower subtree unbalanced.

## Brute force

Try possible tree shapes with the same values and check both ordering and height balance at every node. The number of ordered binary-tree shapes grows exponentially, so exhaustive construction is infeasible. Alternatively, inserting values in the original order into a fresh ordinary search tree can simply reproduce the original skew and provides no balance guarantee.

## The insight

An in-order traversal of a search tree lists its values in increasing order. After collecting this list, choose a middle element as the root, recursively use the left half for its left subtree and the right half for its right subtree. All left values are smaller and all right values are larger, so the search-tree property holds at each node.

The two slices have sizes differing by at most one. Applying the same construction within each slice yields child heights differing by at most one, and induction gives balance at every node. Using index boundaries avoids copying sublists. Iterative in-order traversal handles a severely skewed input, while the construction recursion has logarithmic depth.

## Optimal solution, traced

```steps
Input search tree is a chain 1 → 2 → 3
    in-order values are [1,2,3]
---
Choose the middle value 2 as the new root
    left range contains 1; right range contains 3
---
Build each one-element range as a leaf
    balanced tree has root {{2}} and children 1 and 3
```

The snippets use `TreeNode`, defined below, with the conventional `val`, `left`, and `right` attributes. They work with any input node exposing those same attributes; output nodes are instances of this class.

## Code

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def balance_bst(root):
    values, stack = [], []
    node = root
    while node or stack:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        values.append(node.val)
        node = node.right

    def build(lo, hi):
        if lo >= hi:
            return None
        mid = (lo + hi) // 2
        return TreeNode(values[mid], build(lo, mid), build(mid + 1, hi))

    return build(0, len(values))
```

## Complexity

Traversal and construction visit each of n nodes once, for O(n) time. The values list and traversal stack require O(n) auxiliary space in the worst case; construction recursion is O(log n) deep. The new output tree itself uses O(n) nodes.

## Mistakes and edge cases

- Choosing only a new root without rebuilding both subtrees does not guarantee balance.
- Avoid recursive traversal of the potentially skewed input.
- A single node remains a valid balanced tree; this implementation also accepts an empty input.

## Variations

- Reuse existing nodes collected in order rather than allocate new nodes.
- For a sorted array instead of a tree, begin directly with the middle-element construction.

=== card | 1353
time: 30 min

## The problem

Each event is available on every integer day in its inclusive interval `[start, end]`. Attend at most one event per day, with each event attended at most once. Return the largest possible number attended. For `[[1,2], [2,3], [3,4]]`, three events can be attended on days 1, 2, and 3.

## Constraints and what they imply

There are up to 100,000 events, with `1 <= start <= end <= 100,000`. Intervals can overlap, be identical, or last only one day. Attending an event consumes one day, not its entire interval. An event ending today is still available today. Large inputs make checking every remaining event every day too slow.

## Brute force

Try assigning each event either to one available day or to no day, rejecting assignments that reuse a day. Choose the largest valid assignment. This enumerates all possibilities and is correct but can grow exponentially in the number of events and available days. Another direct approach scans every event at each day to find an eligible one, costing O(nD) over D days even when the choice is correct.

## The insight

Process events by their start day and keep the end days of currently available, unattended events in a min-heap. On each day, remove expired events and attend the event with the earliest end. If no event is available, jump to the next start day rather than scanning an empty gap.

The choice is safe by exchange. If an optimal schedule attends a later-ending event today, swap it with the earliest-ending event: the latter is available today, and the later-ending event remains valid on the earliest event's former day. If the earliest event was not scheduled, replace today's event with it. If today was idle, move that event to today, or add it if it was unscheduled. In all cases the count does not decrease. Repeating this argument fixes the greedy choice without reducing an optimum.

## Optimal solution, traced

```steps
Day 1: add event [1,2]
    attend it; count is 1
---
Day 2: add [2,3]
    attend it; count is 2
---
Day 3: add [3,4] and attend it
    answer {{3}}
```

When the heap empties, advancing to the next start avoids a dependency on the largest day number. Removing all ends strictly less than today preserves events whose final eligible day is today.

## Code

```python
import heapq


def max_events(events):
    ordered = sorted(events)
    heap = []
    i = count = day = 0
    while i < len(ordered) or heap:
        if not heap and i < len(ordered):
            day = max(day, ordered[i][0])
        while i < len(ordered) and ordered[i][0] <= day:
            heapq.heappush(heap, ordered[i][1])
            i += 1
        while heap and heap[0] < day:
            heapq.heappop(heap)
        if heap:
            heapq.heappop(heap)
            count += 1
            day += 1
    return count
```

## Complexity

Sorting takes O(n log n), and each event enters and leaves the heap once, also O(n log n) total. Empty gaps are jumped, and every other iteration removes or attends an event, so the sweep adds O(n) iterations. The ordered copy and heap require O(n) auxiliary space.

## Mistakes and edge cases

- Remove only events with end strictly less than the current day.
- Add every event that has already started before selecting one.
- An empty list returns zero; repeated intervals are separate events.

## Variations

- Record the chosen event IDs and days by storing `(end, id)` in the heap.
- If an event consumes its entire duration rather than one day, this greedy argument no longer applies.

=== card | 695
time: 30 min

## The problem

Find the largest area of an island in a binary grid. An island is a maximal group of land cells connected horizontally or vertically, and its area is the number of cells in that group. Diagonal contact alone does not connect islands. For `[[1,0,1], [1,0,1]]`, the answer is 2; if there is no land, the answer is zero.

## Constraints and what they imply

The grid has between 1 and 50 rows and columns, and each cell is either zero for water or one for land. An island can touch an edge or fill the whole grid. The input may contain several islands of the same size. Cells are identified by their row and column, not by their values. The function should leave the input unchanged.

## Brute force

For each land cell, independently explore all land cells reachable from it and take the maximum size found. Each exploration computes a valid island area, but every cell in an island starts the same exploration again. A grid containing one large island can therefore require O((rc)²) work for r rows and c columns.

## The insight

Once one exploration has discovered an entire island, none of its cells needs to start another exploration. Scan the grid, and whenever an unvisited land cell appears, walk all its reachable land neighbours using a stack. Mark a cell when adding it to the stack, so two neighbours cannot add the same cell twice. The number removed from the stack is exactly that island's area.

Every cell reached belongs to the starting island because each step crosses a valid land adjacency. Conversely, every cell in the island is reachable by a sequence of such steps and will eventually be discovered. After the walk, update the best area and continue scanning for a different island.

## Optimal solution, traced

```steps
Grid rows are [1,0,1] and [1,0,1]
    start at the upper-left land cell
---
Visit it and the land directly below it
    first island area is 2
---
The right column forms another area-2 island
    largest area is {{2}}
```

The explicit stack avoids recursion depth problems when a connected region winds through many cells. Visiting water during the outer scan has constant cost and never starts a walk.

## Code

```python
def max_area_of_island(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen = set()
    best = 0
    for r in range(rows):
        for c in range(cols):
            if not grid[r][c] or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            area = 0
            while stack:
                x, y = stack.pop()
                area += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if 0 <= a < rows and 0 <= b < cols and grid[a][b] and (a, b) not in seen:
                        seen.add((a, b))
                        stack.append((a, b))
            best = max(best, area)
    return best
```

## Complexity

There are rc cells and each land cell is pushed at most once, with four neighbour checks. Time is O(rc); the visited set and stack take O(rc) auxiliary space in the worst case. The input grid is not modified.

## Mistakes and edge cases

- Do not connect diagonal cells.
- Mark on insertion, not only on removal, to avoid duplicate work.
- All water returns zero; all land returns the full grid area.

## Variations

- Return the number of islands by counting each new walk.
- Include diagonal neighbours if the definition explicitly permits eight-directional connectivity.

=== card | 2316
time: 30 min

## The problem

An undirected graph contains n labelled nodes and a list of edges. Count unordered pairs of distinct nodes for which no path connects the two nodes. For n = 5 and edges `[[0,1], [2,3]]`, the unreachable pairs are `{0,2}`, `{0,3}`, `{0,4}`, `{1,2}`, `{1,3}`, `{1,4}`, `{2,4}`, and `{3,4}`, giving 8. Each pair is counted once, not once in each direction.

## Constraints and what they imply

There can be up to 100,000 nodes and 200,000 edges. Nodes are numbered from zero through n minus one. Isolated nodes are valid components, and an edge connects its endpoints in both directions. The answer can exceed a 32-bit signed integer; Python integers expand as needed. Enumerating all pairs directly is too expensive when n is large.

## Brute force

For each pair of nodes, run a graph search from one endpoint to determine whether the other can be reached. This checks the definition directly, but there are O(n²) pairs and each search can cost O(n + m) for m edges. Even computing reachability once per source still takes O(n(n + m)) time and repeats much of the same work.

## The insight

Reachability in an undirected graph partitions nodes into connected components. Two nodes form an unreachable pair exactly when they lie in different components. Traverse each component once to find its size. Maintain the number of nodes in components already processed; a new component of size s contributes `s * previous` pairs, one for each choice of a new node and an earlier node.

Each cross-component pair is counted when the later of its two components is processed, and no within-component pair is counted. An isolated node simply has size one. This avoids needing all pairs or dividing a count by two.

## Optimal solution, traced

```steps
Components have sizes 2, 2, 1
    first component contributes 2 × 0 = 0
---
Second component contributes 2 × 2 = 4
    four nodes have now been processed
---
Last component contributes 1 × 4 = 4
    total unreachable pairs {{8}}
```

An explicit stack discovers each component without relying on the Python recursion limit. Marking nodes when they are pushed prevents repeated stack entries when the graph has cycles.

## Code

```python
def count_unreachable_pairs(n, edges):
    graph = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)
    seen = [False] * n
    previous = answer = 0
    for start in range(n):
        if seen[start]:
            continue
        seen[start] = True
        stack = [start]
        size = 0
        while stack:
            u = stack.pop()
            size += 1
            for v in graph[u]:
                if not seen[v]:
                    seen[v] = True
                    stack.append(v)
        answer += size * previous
        previous += size
    return answer
```

## Complexity

Constructing the adjacency lists and traversing them takes O(n + m) time for m edges. The graph, visited array, and stack use O(n + m) auxiliary space. Each undirected edge is stored twice and inspected at most twice.

## Mistakes and edge cases

- Count unordered pairs only once.
- Include isolated nodes as components of size one.
- A connected graph returns zero; an edgeless graph returns `n * (n - 1) // 2`.

## Variations

- Compute components with union-find, then combine their sizes in the same way.
- Count reachable pairs instead by summing `s * (s - 1) // 2` over components.

=== card | 1466
time: 30 min

## The problem

Cities are connected by one-way roads whose underlying undirected graph is a tree. Reverse the fewest roads so that every city can reach city 0 following directions. For roads `[[0,1], [2,1], [2,3]]`, reversing 0→1 and 2→3 suffices, so the answer is 2. A reversal changes one road's direction.

## Constraints and what they imply

There are between 2 and 50,000 cities labelled from 0 to n minus one and exactly n minus one roads. Ignoring direction, the roads form a connected tree, so each city has exactly one undirected route to city 0. Roads can initially point either way. The answer counts roads, not paths; a road may serve many cities after its direction is corrected.

## Brute force

Try every subset of roads to reverse and, for each resulting orientation, search from every city to see whether it reaches zero. The first valid subset with the fewest roads gives the answer. However, there are `2^(n-1)` subsets, and repeatedly verifying reachability adds further work. This approach ignores the unique-route structure of a tree.

## The insight

Walk outward from city 0 while ignoring the original road direction. For a tree edge from a visited parent to its child, all cities below the child must cross that edge toward the parent to reach zero. Therefore an originally outward road must be reversed, whereas an originally inward road must not be reversed.

Store both directions of each road in an adjacency list. The original direction gets cost one when traversed outward from the root, and the reverse direction gets cost zero. Summing these costs during a traversal counts exactly the roads that need reversal. Every such reversal is necessary by uniqueness of the route, and making all of them is sufficient for every route to point toward zero.

## Optimal solution, traced

```steps
Start at 0: road 0→1 points outward
    reverse it; count is 1
---
From 1 visit 2 over original road 2→1
    this road already points toward 0; count stays 1
---
From 2 visit 3 over original road 2→3
    reverse it; answer {{2}}
```

The parent check is enough because the undirected graph is a tree. No separate visited set is needed, and an iterative stack avoids a deep recursive call chain.

## Code

```python
def min_reorder(n, connections):
    graph = [[] for _ in range(n)]
    for u, v in connections:
        graph[u].append((v, 1))
        graph[v].append((u, 0))
    answer = 0
    stack = [(0, -1)]
    while stack:
        u, parent = stack.pop()
        for v, cost in graph[u]:
            if v != parent:
                answer += cost
                stack.append((v, u))
    return answer
```

## Complexity

Building and traversing the adjacency lists takes O(n) time because a tree has n minus one roads. The graph and traversal stack use O(n) auxiliary space. Every road is inspected in both directions but contributes at most once.

## Mistakes and edge cases

- Count edges pointing away from zero, not toward it.
- The parent-only traversal relies on the tree guarantee; general graphs need visited tracking and a different proof.
- If all roads already point toward zero, the answer is zero.

## Variations

- Return the roads to reverse by storing their identifiers alongside the cost.
- Use a different destination as the root and apply the same reasoning.

=== card | 851
time: 30 min

## The problem

For each person, return the index of the quietest person who is at least as rich as that person. Each pair `[a,b]` says a is strictly richer than b, and richness is transitive. Everyone is considered at least as rich as themselves. If `richer = [[1,0],[2,1]]` and `quiet = [3,2,1]`, the result is `[2,2,2]`.

## Constraints and what they imply

There are at most 500 people and up to n(n-1)/2 richer pairs. The stated relations are consistent with a strict ordering and therefore contain no directed cycle. Quietness values are distinct integers from 0 through n minus one, so the quietest choice is unique. Not every pair of people has a known relationship; only relations implied by the input are usable.

## Brute force

For each person, traverse all chains of richer people and choose the smallest quietness among those reached, including the person. This is correct but repeats searches through the same richer subgraph for many people. In the worst case it takes O(n(n + m)) time, where m is the number of stated relationships.

## The insight

Direct every edge from richer to poorer. Process the resulting directed acyclic graph in topological order, starting with people who have no incoming richer edge. Initially each person's best candidate is themselves. When processing a richer person, pass their best candidate to each directly poorer neighbour if it is quieter than that neighbour's current candidate.

All incoming richer neighbours are processed before a person leaves the queue. Their propagated candidates include everyone richer along paths ending at those neighbours. Thus, when the person's indegree reaches zero, their candidate is the quietest among all known richer-or-equal people. This invariant also covers disconnected groups, each of which has its own starting nodes.

## Optimal solution, traced

```steps
Relations are 2 richer than 1, and 1 richer than 0
    initial candidates [0,1,2], with 2 ready first
---
Process 2 and pass candidate 2 to person 1
    person 1 becomes ready and passes candidate 2 to person 0
---
Process 0
    answer {{[2,2,2]}}
```

Indegrees count unprocessed incoming edges. They are decremented even if a candidate does not improve, because readiness concerns processed relationships rather than successful updates.

## Code

```python
from collections import deque


def loud_and_rich(richer, quiet):
    n = len(quiet)
    graph = [[] for _ in range(n)]
    indegree = [0] * n
    for rich, poor in richer:
        graph[rich].append(poor)
        indegree[poor] += 1
    answer = list(range(n))
    queue = deque(i for i in range(n) if indegree[i] == 0)
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if quiet[answer[u]] < quiet[answer[v]]:
                answer[v] = answer[u]
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return answer
```

## Complexity

The graph, indegrees, and queue require O(n + m) auxiliary space. Each node is processed once and each edge once, giving O(n + m) time. The result uses O(n) additional entries and is included in this bound.

## Mistakes and edge cases

- Include each person as their own candidate.
- Propagate from richer to poorer; reversing the edge answers a different question.
- With no relations the answer is `[0,1,...]`; cycles violate the problem's consistency guarantee.

## Variations

- Use memoised search through directly richer neighbours when recursion depth is safe.
- Return the quietness values instead of indices by mapping through the result.

=== card | 542
time: 30 min

## The problem

Given a binary matrix, return a matrix of the same dimensions in which each entry is the distance to the nearest zero. Distance is the number of horizontal or vertical moves. For `[[0,1,1], [1,1,1]]`, the answer is `[[0,1,2], [1,2,3]]`. A zero has distance zero to itself.

## Constraints and what they imply

The matrix has at least one row and column, at most 10,000 cells in total, and contains at least one zero. Each cell contains either zero or one. Moves cross grid edges, not diagonals, and every cell is traversable; ones are not obstacles. Multiple zeros can be equally close, but only the minimum distance is needed. The implementation returns a new matrix without changing the input.

## Brute force

For every cell, compare its Manhattan distance to every zero and take the minimum. Because there are no obstacles, Manhattan distance is exactly the shortest number of grid moves. However, with r times c cells and a similar number of zeros, this costs O((rc)²) time. Searching independently from each cell repeats much of the same work as well.

## The insight

Put all zero cells in one queue at distance zero, then expand outward one grid step at a time. This is equivalent to introducing a virtual source with zero-cost links to every zero and starting the ordinary breadth-first wave from all of them simultaneously. A cell's first discovery is its minimum distance from the entire set of zeros.

The queue processes cells in nondecreasing distance. Every newly discovered neighbour is one step farther than its predecessor, so a shorter route would have reached it in an earlier layer. Mark the distance as soon as the neighbour is enqueued; that prevents duplicate additions from different equally close paths.

## Optimal solution, traced

```steps
Matrix is [[0,1,1], [1,1,1]]
    queue starts with the zero at (0,0), distance 0
---
Expand distance 0, then distance 1
    cells (0,1) and (1,0) get 1; the next layer gets 2
---
The farthest cell (1,2) gets 3
    answer {{[[0,1,2], [1,2,3]]}}
```

The sentinel -1 denotes an undiscovered cell. The presence of at least one zero ensures that every matrix cell is eventually assigned a finite distance.

## Code

```python
from collections import deque


def update_matrix(mat):
    rows, cols = len(mat), len(mat[0])
    dist = [[-1] * cols for _ in range(rows)]
    queue = deque()
    for r in range(rows):
        for c in range(cols):
            if mat[r][c] == 0:
                dist[r][c] = 0
                queue.append((r, c))
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))
    return dist
```

## Complexity

Each cell is queued at most once and examines four neighbours, so time is O(rc). The distance output and queue use O(rc) space. A matrix containing only zeros is already fully seeded and returns all zeros.

## Mistakes and edge cases

- Seed every zero before expanding; processing zeros one at a time is not the same search.
- Mark when enqueuing, not after removal.
- Do not treat ones as blocked cells. The input guarantee excludes a matrix without zeros.

## Variations

- With obstacles, keep the same multi-source search but skip blocked neighbours.
- Record a parent when discovering each cell to recover a shortest route to a zero.

=== card | 1786
time: 35 min

## The problem

In an undirected weighted graph, define `distance(u)` as the shortest distance from u to node n. Count paths from node 1 to node n for which this distance strictly decreases at every step. Return the count modulo 1,000,000,007. For edges 1–2 weight 1, 2–3 weight 1, and 1–3 weight 4, both 1–2–3 and 1–3 qualify.

## Constraints and what they imply

There are up to 20,000 nodes and 40,000 undirected edges, with positive integer weights at most 100,000. The original graph is connected, and nodes are numbered from 1 through n. A qualifying path need not itself be a shortest path: it is the shortest distance to n at each vertex that must decrease. Equal distances cannot be joined by an allowed step.

## Brute force

First compute all distances to n, then enumerate simple paths from 1 to n and test the strict-decrease condition. This directly counts qualifying paths but can take exponential time because a graph can contain exponentially many simple paths. Recomputing shortest distances separately for each path would add even more repeated work.

## The insight

Use Dijkstra's algorithm from n to find all shortest distances. Now orient every usable step from a larger distance to a smaller one. Strict decrease forbids cycles, so the allowed steps form a directed acyclic graph. Let `ways[n] = 1`, representing the empty suffix at the destination. For every other node, sum `ways[v]` over neighbours v with smaller distance.

Compute this recurrence in increasing order of distance. Every required neighbour has already been processed, while equal-distance neighbours are deliberately ignored. The recurrence counts each qualifying path once by its first step; different first neighbours give disjoint path sets. Reduce each total modulo the required modulus.

## Optimal solution, traced

```steps
Distances to node 3 are: d[3]=0, d[2]=1, d[1]=2
    ways[3] = 1
---
Node 2 has smaller-distance neighbour 3
    ways[2] = 1
---
Node 1 can step to 2 or directly to 3
    ways[1] = 1 + 1 = {{2}}
```

The direct edge of weight 4 is allowed even though it is not on a shortest path. Dijkstra computes distances, but the path-counting step tests only the strict comparison between endpoint distances.

## Code

```python
import heapq


def count_restricted_paths(n, edges):
    graph = [[] for _ in range(n + 1)]
    for u, v, weight in edges:
        graph[u].append((v, weight))
        graph[v].append((u, weight))
    dist = [float('inf')] * (n + 1)
    dist[n] = 0
    heap = [(0, n)]
    while heap:
        cost, u = heapq.heappop(heap)
        if cost != dist[u]:
            continue
        for v, weight in graph[u]:
            candidate = cost + weight
            if candidate < dist[v]:
                dist[v] = candidate
                heapq.heappush(heap, (candidate, v))
    ways = [0] * (n + 1)
    ways[n] = 1
    for u in sorted(range(1, n + 1), key=lambda x: dist[x]):
        if u != n:
            ways[u] = sum(ways[v] for v, _ in graph[u] if dist[v] < dist[u]) % 1_000_000_007
    return ways[1]
```

## Complexity

With n vertices and m edges, lazy Dijkstra costs O(n + m log(m + 1)); sorting nodes costs O(n log n), and the DP scans all adjacency entries in O(m). Space is O(n + m), including the graph and heap. Python's integers avoid distance overflow.

## Mistakes and edge cases

- A restricted path is not necessarily a shortest path.
- Use strict inequality; equal distances cannot be traversed.
- Start the destination with one empty suffix, not zero; ignore stale heap entries.

## Variations

- Count paths from every starting node by returning the `ways` array.
- Replace path counts with another DAG aggregate, such as a minimum number of allowed steps.

=== card | 909
time: 30 min

## The problem

A numbered snakes-and-ladders board has n² squares. Starting on square 1, roll a die to move one through six squares without passing n². If the landing square has a snake or ladder, move immediately to its destination once. Return the fewest rolls needed to reach n², or -1 if impossible. A destination that itself has a snake or ladder is not followed again on the same roll.

## Constraints and what they imply

The board is an n by n array with `2 <= n <= 20`. Square numbering begins at the bottom-left, runs across the bottom row, and alternates direction on successive rows upward. Each entry is -1 or a destination square number; the first and last squares have no jump. Jumps may go backward and create cycles, so revisiting positions needs care. Only the dice roll counts as a move.

## Brute force

Enumerate all sequences of die outcomes and simulate each until reaching the finish. Without a length bound this can loop forever on boards with backward jumps, and even bounded sequences branch up to six ways per roll. Checking all sequences through depth d takes O(6^d) time before accounting for repeated board positions.

## The insight

Model each square reached after any single landing jump as a state. A roll gives up to six equally costly transitions, each followed by at most one jump. Breadth-first search from square 1 discovers each state in order of increasing roll count, so the first discovery of the final square is optimal. A visited set eliminates cycles and repeated states.

To decode square s, let `(row_from_bottom, offset) = divmod(s - 1, n)`. The array row is `n - 1 - row_from_bottom`. The column is offset on an even row from the bottom and `n - 1 - offset` on an odd row. This handles the alternating numbering independently of the search.

## Optimal solution, traced

```steps
Use a 3×3 board with no jumps, starting at square 1
    first roll can reach squares 2 through 7
---
Square 3 can roll to square 9
    the finish is reached after two rolls
---
No first roll reaches 9
    minimum rolls {{2}}
```

Mark the destination after applying a jump, not the intermediate landing square. A jump to a different jump square ends the current move there; its own jump is not chained.

## Code

```python
from collections import deque


def snakes_and_ladders(board):
    n = len(board)
    finish = n * n
    queue = deque([(1, 0)])
    seen = {1}
    while queue:
        square, rolls = queue.popleft()
        if square == finish:
            return rolls
        for landing in range(square + 1, min(square + 6, finish) + 1):
            row, offset = divmod(landing - 1, n)
            col = offset if row % 2 == 0 else n - 1 - offset
            jump = board[n - 1 - row][col]
            destination = landing if jump == -1 else jump
            if destination not in seen:
                seen.add(destination)
                queue.append((destination, rolls + 1))
    return -1
```

## Complexity

There are n² states and at most six transitions per state. Time is O(n²), and the queue and visited set use O(n²) auxiliary space. The board itself is read but not modified.

## Mistakes and edge cases

- Reverse column direction on alternate rows counted from the bottom.
- Follow only one snake or ladder per roll, even when its destination has another.
- Bound a roll by the final square and use visited states to stop cycles.

## Variations

- Store predecessors and chosen die values to reconstruct one shortest sequence of rolls.
- Change the die size by replacing six with the supplied maximum roll.

=== card | 2492
time: 30 min

## The problem

Roads connect cities in both directions and each road has a positive distance. The score of a route is the smallest road distance appearing on that route. Find the minimum possible score of a route from city 1 to city n. A route may revisit cities and reuse roads. For roads 1–2 of length 7, 2–4 of length 5, 1–3 of length 3, and 3–4 of length 8, with n = 4, the route 1–3–4 has score 3, which is the smallest possible score.

## Constraints and what they imply

There are up to 100,000 cities and 100,000 roads; cities are labelled from 1 through n, and road distances are positive. The problem guarantees a route from 1 to n. Revisiting and backtracking are permitted. Only the score is requested, not the route itself.

## Brute force

Enumerating simple paths from 1 to n and taking their lowest score is not correct because the optimal route may need a detour and repeated vertices. A correct finite baseline for tiny graphs can explore states `(city, smallest_distance_seen)` and keep every reachable state; the number of distance states per city can grow with the number of roads. It does substantially more work than necessary.

## The insight

The answer is the smallest road weight anywhere in the connected component of city 1. No route starting at 1 can use a road outside this component, so its score cannot be below that minimum. Conversely, for any road in the component, travel from 1 to one endpoint, cross the road, and then travel to n. The graph is undirected and 1 is connected to n, so these walks exist; revisits are allowed.

Traverse the component from 1, inspecting each incident road and updating a running minimum. This inspects every road in that component, including branches not on a simple path to the destination. The lower bound and the constructed detour prove equality.

## Optimal solution, traced

```steps
For n = 4, use roads 1–2 of weight 7, 2–4 of weight 5, and 2–3 of weight 1
    from 1 follow the road of weight 7 to 2
    smallest inspected weight is 7
---
From 2 inspect roads to 4 with weight 5 and to 3 with weight 1
    component minimum becomes 1
---
Walk 1→2→3→2→4
    route score {{1}}
```

The minimum is taken over every incident edge, even when its other endpoint was visited earlier. Visited tracking controls traversal, not whether an edge's weight is considered.

## Code

```python
def min_score(n, roads):
    graph = [[] for _ in range(n + 1)]
    for u, v, weight in roads:
        graph[u].append((v, weight))
        graph[v].append((u, weight))
    seen = {1}
    stack = [1]
    answer = float('inf')
    while stack:
        u = stack.pop()
        for v, weight in graph[u]:
            answer = min(answer, weight)
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return answer
```

## Complexity

Building the graph costs O(n + m), and the traversal examines each road in the reachable component twice, for O(n + m) total time. The adjacency lists, visited set, and stack use O(n + m) auxiliary space. The connectivity guarantee ensures a finite answer.

## Mistakes and edge cases

- The score is a minimum edge weight, not a sum or maximum.
- Do not restrict attention to simple routes: detours may improve the score.
- Roads in other connected components cannot occur on a route starting at 1.

## Variations

- Return a witnessing walk by retaining traversal paths to the minimum-weight edge and to n.
- If repeated vertices are forbidden, this component-minimum proof no longer suffices.

=== card | 1882
time: 35 min

## The problem

Servers have weights, and task j arrives at time j with a positive duration. Tasks wait in arrival order. Whenever a task can start, assign it to the free server with smallest weight, breaking ties by smallest server index. A task starting at time t with duration d releases its server at time t+d. Return the assigned server index for each task.

For server weights `[3,1]` and durations `[2,1,2]`, the assignment is `[1,0,1]`: server 1 handles the first task, is still busy at time 1, and is free again at time 2.

## Constraints and what they imply

There are up to 200,000 servers and tasks. Weights and durations are positive integers up to 200,000. Several tasks may be waiting when servers become free, and several servers can become free simultaneously. Waiting tasks retain their original order, but assignments at the same time must still use the weight and index tie rules. A server released at time t is available to a task starting at t.

## Brute force

Simulate each time unit, scan all servers for every assignment, and choose the best free server. This follows the specification but can inspect many servers repeatedly and can spend enormous time in gaps while all servers are busy. Its cost depends on the elapsed time as well as the number of tasks and servers.

## The insight

Maintain two priority queues. The free heap is ordered by `(weight, index)`, the exact assignment preference. The busy heap is ordered by `(finish_time, weight, index)` so its first entry identifies the next release. For each task in arrival order, advance the current time to at least its arrival and release all servers finishing by that time. If none are free, jump to the earliest finish and release every server finishing at that instant.

Then take the best free server and insert it into the busy heap with its new finish time. Releasing all simultaneous finishers before choosing is necessary: the earliest busy heap entry alone need not have the best weight among all servers available at that time. The current time never goes backward, preserving task order.

## Optimal solution, traced

```steps
At time 0 choose server 1, weight 1, for duration 2
    server 1 becomes free at time 2
---
At time 1 server 1 is busy, so server 0 receives the next task
    server 0 also becomes free at time 2
---
At time 2 release both and choose lower weight server 1
    assignment {{[1,0,1]}}
```

The code processes both releases before assigning the third task, so the lower-weight server wins.

## Code

```python
import heapq


def assign_tasks(servers, tasks):
    free = [(weight, i) for i, weight in enumerate(servers)]
    heapq.heapify(free)
    busy = []
    answer = []
    time = 0
    for arrival, duration in enumerate(tasks):
        time = max(time, arrival)
        while busy and busy[0][0] <= time:
            _, weight, i = heapq.heappop(busy)
            heapq.heappush(free, (weight, i))
        if not free:
            time = busy[0][0]
            while busy and busy[0][0] <= time:
                _, weight, i = heapq.heappop(busy)
                heapq.heappush(free, (weight, i))
        weight, i = heapq.heappop(free)
        answer.append(i)
        heapq.heappush(busy, (time + duration, weight, i))
    return answer
```

## Complexity

Heap construction is O(n), and each of m tasks inserts and later releases at most one server, with O(log n) per heap operation. Total time is O(n + m log(n + 1)); auxiliary space is O(n) for the heaps, plus O(m) for the returned assignment list. Time jumps do not scan empty time units.

## Mistakes and edge cases

- Release servers finishing at the current time before assigning.
- Release all simultaneous finishers before comparing their weights and indices.
- Do not allow later tasks to jump ahead of waiting tasks.

## Variations

- Return each task's start time as well as its assigned server.
- Change the free-heap key to support a different explicitly specified server preference.

=== card | 2092
time: 40 min

## The problem

Person 0 initially knows a secret and tells `first_person` at time zero. Meetings are triples `[x,y,time]`. A person who knows the secret at a meeting time tells the other participant, and transmission within a time instant is immediate: knowledge may travel through any chain of meetings all happening at that time. Return all people who eventually know the secret, in any order.

For `n = 5`, `first_person = 1`, and meetings `[[1,2,3], [3,4,3], [2,3,3]]`, all five people learn it. The input ordering of meetings at time 3 must not limit that instantaneous chain.

## Constraints and what they imply

There are up to 100,000 people and 100,000 meetings, with positive meeting times up to 100,000. A person may attend several meetings at exactly the same time, and the same pair can meet at different times. Initial knowledge is permanent. A connection made during a meeting when nobody in that connected group knows the secret does not transfer knowledge later unless another meeting occurs.

Meetings at different times must be processed chronologically; input order is not guaranteed. The result is a collection of people, not a record of who told whom or when.

## Brute force

Sort the meetings by time, then repeatedly scan every meeting at a given time until an entire pass spreads no new knowledge. This computes the instantaneous closure: each successful update adds a person, so the process terminates. However, an adversarial ordering of a long chain can require one new person per pass. Across a time group with k meetings, this can take O(k²) work.

Another incorrect shortcut is to join all meetings into one timeless graph. A person who learns the secret tomorrow cannot retroactively tell someone they met yesterday. Chronological processing is necessary as well as closure within each time group.

## The insight

For each distinct time, build an undirected graph only from meetings at that time. Seed a queue with every participant who already knows the secret before this group. Traverse that temporary graph; every reached participant learns immediately, and is added to the permanent known set. Discard the temporary graph before moving on.

The invariant before processing time t is that the known set contains exactly the people who could learn from initial information and meetings strictly before t. Within a connected component of the time-t graph, if any participant is already known, a sequence of simultaneous meetings transmits the secret to the entire component. If no participant is known, nobody in that component can start transmission. Thus the traversal produces exactly the correct known set after time t.

This formulation uses no persistent links between past meeting partners. People keep their knowledge, not the ability to communicate outside the specified meeting times. Handling every meeting in a time group before beginning the traversal prevents input order within the group from changing the answer.

## Optimal solution, traced

```steps
Initially persons 0 and 1 know the secret
    time 3 meetings connect 1–2, 3–4, and 2–3
---
Build the entire time-3 graph and seed person 1
    propagation reaches 2, then 3, then 4
---
No meetings remain
    known people {{[0,1,2,3,4]}}
```

If only 3–4 met at an earlier time, that meeting would not let person 4 learn from person 3 later without a new meeting. Conversely, the chronological ordering of different groups makes information gained earlier available as a seed in a later group.

## Code

```python
from collections import defaultdict, deque


def find_all_people(n, meetings, first_person):
    known = {0, first_person}
    ordered = sorted(meetings, key=lambda meeting: meeting[2])
    i = 0
    while i < len(ordered):
        time = ordered[i][2]
        graph = defaultdict(list)
        while i < len(ordered) and ordered[i][2] == time:
            x, y, _ = ordered[i]
            graph[x].append(y)
            graph[y].append(x)
            i += 1
        queue = deque(person for person in graph if person in known)
        reached = set(queue)
        while queue:
            u = queue.popleft()
            for v in graph[u]:
                if v not in reached:
                    reached.add(v)
                    queue.append(v)
        known.update(reached)
    return sorted(known)
```

## Complexity

For M meetings, sorting takes O(M log(M + 1)). Across all time groups, the temporary graphs contain O(M) total edge occurrences and at most O(M) participant occurrences, so all traversals together take O(M) time. Sorting the returned people costs O(n log(n + 1)) in the worst case; it is optional because output order is unrestricted. Space is O(n + M) for the known set, sorted input, a time group's graph, and its queue.

## Mistakes and edge cases

- Process all meetings at one time as a group, not as sequential opportunities in input order.
- Do not retain connectivity from a time group whose participants did not know the secret.
- With no meetings, exactly persons 0 and `first_person` know; duplicate simultaneous meetings do not change the result.
- Mark visited participants locally even if they already know the secret, so cycles and multiple seeds are safe.

## Variations

- Return the earliest learning time by recording the current time when a person is first reached.
- Process each time group with a temporary union-find, discarding its components after propagating knowledge.
- If communication takes positive time instead of being instantaneous, model those delays explicitly rather than using same-time closure.

=== card | 279
time: 30 min

## The problem

Given a positive integer n, return the fewest perfect-square positive integers whose sum is n. Squares may be used more than once. For n = 12, the answer is 3 because `4 + 4 + 4 = 12`; taking 9 first would require four terms, `9 + 1 + 1 + 1`.

## Constraints and what they imply

The original range is `1 <= n <= 10,000`. The square 1 is always available, so every target has a solution. A square larger than the current amount cannot be its final summand. We need the minimum number, not the number of representations or a particular representation. This implementation also defines the natural extension that zero requires zero squares.

## Brute force

Recursively try every square not exceeding the remaining amount, and take one plus the smallest answer among the resulting remainders. This is correct by considering the final square, but many different sequences reach the same remainder and recompute it. The search tree can grow exponentially. Always taking the largest possible square is not correct, as the example 12 demonstrates.

## The insight

Store the optimal answer for every amount from zero through n. Set `best[0] = 0`. For amount x, consider each square s² no larger than x and take `1 + best[x - s²]`; the smallest such value is optimal. Every remainder is smaller than x, so an increasing iteration order guarantees that it has already been solved.

For correctness, every candidate adds one square to a valid solution of the remainder, so it is achievable. Conversely, remove the last square from an optimal representation of x: its remaining squares form a representation of one of the tested remainders, whose optimum cannot be larger. Therefore the smallest candidate equals the true optimum.

## Optimal solution, traced

```steps
Set best[0]=0; fill amounts in increasing order
    best[4]=1 because 4 itself is square
---
For 8, square 4 leaves amount 4
    best[8]=2
---
For 12, square 4 leaves amount 8
    best[12]={{3}}; choosing 9 leaves 3 and needs 4 terms
```

Precompute squares up to n once. The inner loop can stop at the first square greater than the current amount because the square list is increasing.

## Code

```python
from math import isqrt


def num_squares(n):
    squares = [i * i for i in range(1, isqrt(n) + 1)]
    best = [0] + [n + 1] * n
    for amount in range(1, n + 1):
        for square in squares:
            if square > amount:
                break
            best[amount] = min(best[amount], 1 + best[amount - square])
    return best[n]
```

## Complexity

There are n amounts and at most `floor(sqrt(n))` candidate squares per amount, giving O(n sqrt(n)) time. The table uses O(n) space and the square list O(sqrt(n)), for O(n) auxiliary space total. The bound also includes the initial list construction.

## Mistakes and edge cases

- The largest square first is not always optimal.
- Reuse squares freely; the same square can occur multiple times.
- A perfect square needs one term; the explicit zero extension returns zero.

## Variations

- Store the chosen square per amount to reconstruct a minimum representation.
- Treat sums as states in a breadth-first search, where each edge adds one square.

=== card | 40
time: 30 min

## The problem

Given candidate numbers and a target, return all distinct combinations whose sum equals the target. Each input occurrence may be used at most once, even when multiple occurrences have the same value. Combinations differing only in order are the same. For candidates `[1,1,2,5]` and target 3, the only answer is `[[1,2]]`.

## Constraints and what they imply

There are at most 100 candidates, each between 1 and 50; the target is between 1 and 30. Values can repeat. The answer can contain many combinations, but duplicate value lists are forbidden. Positivity means that once a chosen value exceeds the remaining target, no larger value can help; it also means a completed combination need not be extended with zero-valued candidates.

## Brute force

Enumerate all subsets of input indices, keep those whose values sum to the target, sort each value list, and deduplicate the results. This is complete because every legal combination uses a subset of occurrences. However, there are 2^n subsets, many of which collapse to the same value combination when the input contains duplicates.

## The insight

Sort candidates and build each combination in nondecreasing order. At a recursion level, try each possible next index at most once per distinct value: if the same value was tried immediately before at that level, choosing it again would produce identical value combinations from equivalent remaining occurrences. After selecting index i, recurse from i+1, so that occurrence cannot be reused.

Equal values at deeper levels remain allowed. For example, two copies of 1 can both appear if the input contains them: the second is chosen in a different recursive call. As all numbers are positive and sorted, stop the loop when the next value exceeds the remaining target. Reaching zero records one complete combination.

## Optimal solution, traced

```steps
Sort [1,1,2,5] and start with remainder 3
    choose the first 1; remainder becomes 2
---
At the next depth, a second 1 is allowed, but cannot complete the target
    choosing 2 records [1,2]
---
At the root skip the second 1 as a duplicate choice
    answer {{[[1,2]]}}
```

Every combination has a nondecreasing representation, and the earliest available equal value represents each choice at a given depth. Skipping later equals therefore removes duplicates without losing distinct value combinations.

## Code

```python
def combination_sum2(candidates, target):
    values = sorted(candidates)
    answer = []
    path = []

    def search(start, remaining):
        if remaining == 0:
            answer.append(path.copy())
            return
        for i in range(start, len(values)):
            if i > start and values[i] == values[i - 1]:
                continue
            if values[i] > remaining:
                break
            path.append(values[i])
            search(i + 1, remaining - values[i])
            path.pop()

    search(0, target)
    return answer
```

## Complexity

Sorting costs O(n log n). The search has at most exponentially many index subsets and may copy O(n) values per result, so a safe worst-case time bound is O(n 2^n + n log n). The sorted copy, current path, and recursion use O(n) auxiliary space, excluding the potentially exponential output.

## Mistakes and edge cases

- Skip equal values only at the same depth, not globally.
- Advance to i+1 to use each input occurrence at most once.
- Copy the path when saving it; otherwise later backtracking changes saved results.

## Variations

- Allow unlimited reuse by recurring from i instead, while retaining same-depth deduplication.
- Count combinations rather than returning them, taking care not to count duplicate value lists.

=== card | 1035

## The problem

Two rows contain integers. Draw lines between equal values in different rows, using each position at most once, without any two lines crossing. Return the largest possible number of lines. Positions matter even if their values repeat. For example, `[1, 4, 2]` and `[1, 2, 4]` allow two lines, not three.

## Constraints and what they imply

Each row contains 1 to 500 elements, with values from 1 to 2000. Explicitly listing all line selections is too expensive. The two rows may have different lengths and can contain repeated numbers. Only the number of lines, not their actual endpoints, is requested.

## Brute force

Enumerate all subsets of positions in the first row and all equally sized subsets in the second row, matching chosen positions in order. Check whether each aligned pair has the same value and retain the largest valid size. This explores exponentially many subsets and repeats work for identical prefixes.

## The insight

Noncrossing lines have endpoints in the same relative order in both rows. Their values therefore form a common subsequence, and every common subsequence gives noncrossing lines. The problem is exactly to find the largest such sequence. For two prefixes, if their last values match, an optimal sequence can include that pair: any solution not using both can replace its last occurrence with these later positions without reducing its length. Otherwise at least one of the final positions is unused, so take the best answer after removing either one.

A rolling row stores answers for the previous first-row prefix. Build a fresh row for the next element: the left entry already describes the current prefix, and the previous row supplies the upper and diagonal entries. Swapping the inputs makes the stored row the shorter one. The zero row handles an empty prefix naturally.

## Optimal solution, traced

For rows `[1, 4, 2]` and `[1, 2, 4]`:

```steps
Start
The empty prefix has row [0, 0, 0, 0].
---
First two elements
Processing 1 gives [0, 1, 1, 1]; processing 4 gives [0, 1, 1, 2].
---
Finish
Processing 2 gives [0, 1, 2, 2], so the result is 2.
```

## Code

```python
def uncrossed_lines(a, b):
    if len(b) > len(a):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for x in a:
        row = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            row[j] = prev[j - 1] + 1 if x == y else max(prev[j], row[j - 1])
        prev = row
    return prev[-1]
```

## Complexity

For lengths m and n, the nested scan takes O(mn) time and O(min(m, n)) extra space. The input arrays are not changed. Reconstructing the actual matching pairs would require retaining additional information or recomputing portions of the table.

## Mistakes and edge cases

Matching equal values greedily from left to right can sacrifice more useful later matches. Repeated values are separate positions, not one shared item. A row with no values in common returns zero, and an all-equal input returns the shorter length. In the mismatch case both removal choices must be considered; using only the diagonal loses valid lines.

## Variations

- Return one set of matching position pairs by retaining predecessor choices.
- Give each matched value a weight and maximize the total weight instead of the count.

=== card | 1594

## The problem

Start at the top-left of an integer grid and move only right or down to its bottom-right corner. Multiply every value on the chosen path, including both endpoints. Return the largest nonnegative path product modulo 1,000,000,007, or -1 if every path has a negative product. For `[[1,-2],[3,4]]`, the best product is 12.

## Constraints and what they imply

There are 1 to 15 rows and columns, and values lie between -4 and 4. A cell can reverse the order of products when it is negative. Python integers preserve exact intermediate values, which is essential because residues do not preserve the ordering of signed products.

## Brute force

Enumerate each sequence of right and down moves, multiply the cells on the resulting path, then compare full products before applying the modulus. The number of routes is a binomial coefficient, exponential in the combined grid dimensions in the worst case. Many routes share a destination cell and repeat the same continuation.

## The insight

At each cell preserve both the smallest and largest exact product among paths ending there. When the current value is positive, multiplying a maximum gives the best candidate; when it is negative, the minimum gives the best candidate instead. Zero maps both extremes to zero. Every path arrives from above or left, and multiplication by a fixed number attains its extremes at an endpoint of the predecessor range. Thus comparing both extremes from both available predecessors gives exact new extremes.

A row of pairs suffices. Before processing a cell, its entry belongs to the previous row; its left neighbor has already been updated for the current row. The starting cell is a special base case, and inaccessible neighbors are omitted instead of inventing a zero product.

## Optimal solution, traced

For `[[1,-2],[3,4]]`:

```steps
First row
The reachable product pairs are (1, 1) and (-2, -2).
---
Second row
The left cell has pair (3, 3). The destination candidates are -8 and 12.
---
Result
The destination extrema are (-8, 12); the nonnegative maximum is 12.
```

## Code

```python
def max_product_path(grid):
    mod = 1_000_000_007
    cols = len(grid[0])
    dp = [None] * cols
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if r == 0 and c == 0:
                dp[c] = (value, value)
                continue
            candidates = []
            for previous in (dp[c], dp[c - 1] if c else None):
                if previous is not None:
                    candidates.extend((previous[0] * value, previous[1] * value))
            dp[c] = (min(candidates), max(candidates))
    answer = dp[-1][1]
    return answer % mod if answer >= 0 else -1
```

## Complexity

For m rows and n columns, each cell examines at most four products: O(mn) arithmetic operations and O(n) auxiliary space. Python's integer multiplication has a size-dependent cost, although the stated bounds keep these integers modest. The input grid remains unchanged.

## Mistakes and edge cases

Do not discard the minimum: two negatives can make a large positive. Do not reduce modulo while comparing, since that changes order and loses sign. A zero path is a valid nonnegative result, even if all other products are negative. A one-cell grid returns its value or -1 according to its sign.

## Variations

- Store predecessor choices to recover a path attaining the best product.
- Allow blocked cells and explicitly represent cells that are unreachable.

=== card | 93

## The problem

Given a string of decimal digits, return every valid IPv4 address obtained by inserting exactly three dots without rearranging or removing digits. An address has four decimal parts, each between 0 and 255 inclusive, with no leading zero unless the part is exactly `0`. For `"1010"`, the only result is `"1.0.1.0"`.

## Constraints and what they imply

The input has 1 to 20 digits. Each part uses one to three digits, so any input longer than 12 or shorter than four has no answer. Every output has the same digits in the same order as the input, with exactly three additional dots. Return all valid addresses rather than choosing a single one.

## Brute force

Try every combination of three distinct cut positions in the string, create four pieces, and validate their lengths, numeric bounds, and leading zeros. There are O(n³) combinations before validation, and each candidate may scan O(n) characters. This is feasible for small input but makes many cuts that cannot form valid parts.

## The insight

Build the address from left to right. At each position, try the next part with length one, two, or three. Every valid address has exactly one such sequence of lengths, so this search is complete and does not produce duplicates. Reject a multi-digit piece beginning with zero and any piece above 255 immediately; neither can become valid by adding more digits.

If r parts remain and d digits remain, a solution requires r <= d <= 3r. Check that bound before branching. Once four parts have been chosen, only an exhausted string is acceptable. Keep the chosen pieces on a path, append a joined copy on success, and undo each choice before trying another length.

## Optimal solution, traced

For `"1010"`:

```steps
First choice
Choose 1; three digits remain for three parts, so each must have length one.
---
Continue
Choose 0, then 1, then 0. All parts are valid and no digits remain.
---
Other choices
Longer first pieces leave too few digits for the remaining parts, so the sole address is 1.0.1.0.
```

## Code

```python
def restore_ip_addresses(s):
    result = []
    def search(pos, parts):
        remaining = 4 - len(parts)
        if not remaining <= len(s) - pos <= 3 * remaining:
            return
        if remaining == 0:
            result.append('.'.join(parts))
            return
        for size in range(1, 4):
            piece = s[pos:pos + size]
            if len(piece) != size:
                break
            if size > 1 and piece[0] == '0':
                break
            if int(piece) > 255:
                break
            parts.append(piece)
            search(pos + size, parts)
            parts.pop()
    search(0, [])
    return result
```

## Complexity

There are at most 3⁴ length sequences and each piece has at most three characters, so time and recursion space are O(1) under the fixed IPv4 format, excluding the bounded output. The length check also rejects overlong input immediately. Output order is not important.

## Mistakes and edge cases

`0` is legal but `00` and `01` are not. The value 255 is allowed, but 256 is not. Exactly four parts must consume every input digit; accepting a partial address is incorrect. The recursive path must be popped after each attempt so a sibling branch does not inherit it.

## Variations

- Count valid addresses instead of returning their strings.
- Generalize to a specified number of parts and maximum part value.

=== card | 2140

## The problem

Questions appear in a fixed order. Question i has a point reward and a brainpower value: solving it earns the reward but forces you to skip that many following questions. Skipping it earns nothing and advances by one. Return the maximum total points obtainable. For `[[3,2],[4,3],[4,4],[2,5]]`, the answer is 5.

## Constraints and what they imply

There are up to 100,000 questions; rewards and brainpower values are positive and can be large. A search through every combination is impractical, and recursion may exceed Python's call stack. A solved question may skip past the end, in which case there are no further questions to answer.

## Brute force

For every question branch between skipping and solving, then follow the forced skips. Evaluate all legal decision sequences and retain the largest sum. The tree can have exponentially many branches, with the same suffix reached repeatedly through different earlier choices. Its recursion depth may also be linear.

## The insight

Let `dp[i]` be the best reward from question i onward. Every legal plan either skips i, giving `dp[i+1]`, or solves it, giving its points plus the best suffix beginning at `i + brainpower + 1`. These choices cover all plans and do not overlap in their first decision. Taking their maximum is optimal because any better continuation could replace the one selected after that first decision.

All referenced suffixes start later, so scan backwards. A jump beyond the array contributes zero; clamping the destination to n lets a single extra zero entry represent every such jump. The answer for the entire input is the first state.

## Optimal solution, traced

For `[[3,2],[4,3],[4,4],[2,5]]`:

```steps
Suffixes
At the last question, taking it yields 2. At index 2, taking yields 4, beating 2.
---
Index 1
Taking yields 4 and skipping also yields 4, so dp[1] is 4.
---
Index 0
Taking gives 3 plus dp[3] = 5; skipping gives 4. Return 5.
```

## Code

```python
def most_points(questions):
    n = len(questions)
    dp = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        points, brainpower = questions[i]
        following = min(n, i + brainpower + 1)
        dp[i] = max(dp[i + 1], points + dp[following])
    return dp[0]
```

## Complexity

Each question is processed once with constant work, giving O(n) time and O(n) auxiliary space. Python integers support totals larger than a fixed 32-bit integer. The algorithm leaves the question list unchanged, and the sentinel also makes an empty extension return zero.

## Mistakes and edge cases

The solved question itself is followed by the skipped questions, so the next usable index includes the extra one. A jump past the end is valid and simply has no future reward. Do not force the last question to be skipped because its brainpower exceeds the number remaining. The largest immediate reward need not lead to the largest total.

## Variations

- Save the chosen branch at each index to reconstruct which questions are solved.
- Change the score to allow negative rewards; skipping still provides a zero baseline.

=== card | 375

## The problem

A hidden integer is chosen from 1 through n. After an incorrect guess, you pay the value guessed and learn whether the hidden integer is higher or lower; a correct guess costs nothing. Return the least amount of money sufficient to guarantee finding the number regardless of the hidden choice. For n = 2, guessing 1 guarantees a cost of 1.

## Constraints and what they imply

The range has 1 to 200 possible values. The opponent can choose the most expensive consistent outcome, so minimizing an average cost is not enough. The guaranteed amount must cover every possible hidden number, including either endpoint of the range.

## Brute force

Enumerate every possible decision tree of guesses. For each tree, evaluate the maximum cost over all hidden numbers, then select the tree with the smallest maximum. There are exponentially many trees and many repeated subintervals; choosing only a median without evaluating costs also fails because larger incorrect guesses cost more.

## The insight

Define the guarantee for an interval as the minimum over first guesses of the maximum cost forced by a remaining side. Guess g either succeeds for free or fails and costs g, after which the answer lies in the lower or upper interval. For an interval containing multiple candidates, at least one side is nonempty, and the adversary can select the more costly continuation. Thus the candidate guarantee is `g + max(left, right)`. A zero- or one-element interval costs zero, because its answer is already determined.

Fill intervals by increasing length so both smaller sides are known. Any strategy has some first guess, and its remaining strategies cannot do better than the corresponding optimal subinterval costs. Conversely, picking the minimizing guess and using those optimal strategies achieves the stated guarantee, proving both bounds.

## Optimal solution, traced

For n = 3:

```steps
Length two
Intervals [1,2] and [2,3] cost 1 and 2, respectively.
---
Try 2 first
Either remaining side contains only one value, so the worst incorrect cost is 2.
---
Compare
Guess 1 costs 1 + 2 = 3; guess 3 costs 3 + 1 = 4. The answer is 2.
```

## Code

```python
def guaranteed_guess_cost(n):
    dp = [[0] * (n + 2) for _ in range(n + 2)]
    for length in range(2, n + 1):
        for left in range(1, n - length + 2):
            right = left + length - 1
            dp[left][right] = min(
                guess + max(dp[left][guess - 1], dp[guess + 1][right])
                for guess in range(left, right + 1)
            )
    return dp[1][n]
```

## Complexity

There are O(n²) intervals, and each considers O(n) guesses: O(n³) time and O(n²) space. Extra rows and columns represent empty intervals at either end. The computation is iterative and does not depend on recursion depth.

## Mistakes and edge cases

Pay only for wrong guesses; in a singleton interval no money is needed. The adversary chooses the worse remaining side, whereas the player chooses the best first guess: reversing min and max changes the problem. A guess at an endpoint has one empty side and must still be considered. For n = 1 return zero.

## Variations

- Store the minimizing guess for every interval and reconstruct the guaranteed strategy.
- Replace guess cost with an arbitrary nonnegative cost per value and use the same interval recurrence.

=== card | 646

## The problem

You are given pairs `[a, b]` with a < b. A pair may follow another only if its first value is strictly greater than the previous pair's second value. Choose and order pairs to make the longest chain, and return its length. For `[[1,2],[2,3],[3,4]]`, the answer is 2: the first and last pairs can be chained.

## Constraints and what they imply

There are 1 to 1000 pairs and endpoints are between -1000 and 1000. Equality at the boundary is not sufficient. Input order is not a restriction: pairs may be rearranged. Negative endpoints are allowed. The answer counts pairs rather than the distance covered by the chain.

## Brute force

Try subsets and all their orders, test the strict chain condition, and keep the maximum length. Even selecting subsets is exponential, and permutations add more work. A quadratic dynamic program over sorted pairs is also possible, but comparing every compatible predecessor is not necessary for the count.

## The insight

Among available pairs, choose one ending earliest. In any optimal nonempty chain, its first pair can be replaced by this earliest-ending pair: the replacement ends no later, so every later pair that followed the original first pair still fits. This exchange preserves the number of pairs. Apply the same argument to the remaining pairs whose starts exceed the selected end. Therefore repeatedly taking the compatible pair with the earliest end produces an optimal chain.

Sort pairs by end and scan once. If a pair starts after the last selected end, select it; otherwise it cannot follow the current choice. Use negative infinity as the initial end so even a pair beginning at the smallest allowed value is accepted. `sorted` makes a new list rather than changing the caller's input.

## Optimal solution, traced

For `[[1,2],[2,3],[3,4]]`:

```steps
Sort
The pairs are already ordered by end: 2, 3, 4.
---
Select
Take [1,2]. The next start equals 2, so [2,3] cannot follow it.
---
Finish
The start 3 exceeds 2, so take [3,4]. The count is 2.
```

## Code

```python
def longest_pair_chain(pairs):
    end = float('-inf')
    count = 0
    for start, finish in sorted(pairs, key=lambda pair: pair[1]):
        if start > end:
            count += 1
            end = finish
    return count
```

## Complexity

Sorting n pairs takes O(n log n) time; the scan takes O(n). The copied sorted list and Python's sorting machinery use O(n) auxiliary space. Only the count is retained, although keeping selected pairs would recover a chain.

## Mistakes and edge cases

Use strict `>` rather than `>=`; touching endpoints do not chain. Sorting by start alone does not justify selecting the first compatible pair, because it may finish very late. A single pair returns one, including when both endpoints are negative. Duplicate pairs cannot follow each other under the strict rule.

## Variations

- Return the selected pairs as well as their count.
- Maximize total pair weights; earliest finishing alone is then insufficient and a weighted scheduling method is needed.

=== card | 712

## The problem

Given two strings, delete characters from either until the remaining strings are equal. Each deletion costs the deleted character's ASCII code. Return the smallest total cost. For `"sea"` and `"eat"`, deleting `s` and `t` costs 115 + 116 = 231. Characters that remain must keep their original order.

## Constraints and what they imply

Each string has 1 to 1000 lowercase English letters, so the costs are positive ASCII codes. Only the total cost is requested, not the resulting common string or the indices of deleted characters. The two strings need not have the same length.

## Brute force

Enumerate all subsequences of each string, compare equal subsequences, and total the cost of deleting all other characters. This explores exponentially many subsets, even though many possibilities share the same prefixes. Alternatively, recursively try deleting the first character from either string without caching; that repeats the same suffix comparisons many times.

## The insight

Let the state for two prefixes be their minimum deletion cost. If the last characters match, keep both: there exists an optimum retaining that equal pair because replacing a kept occurrence of the same character with these later occurrences cannot increase cost. The state is then the diagonal predecessor. If they differ, at least one final character must be deleted, so compare deleting the first string's last character with deleting the second string's last character. Add that character's ASCII cost to the appropriate predecessor.

The empty-prefix boundary equals the sum of all codes in the other prefix. In a row scan, the previous row represents the preceding first-string prefix, and the current row's left cell is already computed. The final entry compares the full strings.

## Optimal solution, traced

For `"a"` and `"b"`:

```steps
Boundary
The empty first prefix costs 0 against empty and 98 against b.
---
Process a
Deleting a from a versus empty costs 97. The final characters differ.
---
Compare
Either 98 + 97 or 97 + 98 is 195, so both characters are deleted.
```

## Code

```python
def minimum_delete_sum(a, b):
    if len(b) > len(a):
        a, b = b, a
    prev = [0]
    for char in b:
        prev.append(prev[-1] + ord(char))
    for x in a:
        row = [prev[0] + ord(x)]
        for j, y in enumerate(b, 1):
            if x == y:
                row.append(prev[j - 1])
            else:
                row.append(min(prev[j] + ord(x), row[j - 1] + ord(y)))
        prev = row
    return prev[-1]
```

## Complexity

For lengths m and n, the scan uses O(mn) time and O(min(m, n)) extra space. The row swap is valid because deletion cost is symmetric between the two input strings. Boundary sums are accumulated once.

## Mistakes and edge cases

Minimizing the number of deletions does not necessarily minimize their ASCII sum. Count deletions from both strings and use `ord`, not the digit value or a zero-based alphabet index. Equal strings cost zero. If one string is empty, the cost is the sum of all character codes in the other.

## Variations

- Recover the characters deleted on both sides by storing predecessor decisions.
- Replace ASCII codes with supplied nonnegative character weights.

=== card | 1653

## The problem

A string contains only `a` and `b`. Delete as few characters as possible so that no `b` appears before an `a` in the remaining string. Equivalently, all remaining `a` characters precede all remaining `b` characters. Return the minimum number of deletions. For `"baba"`, deleting both b's or deleting the first b and last a costs 2.

## Constraints and what they imply

The length is between 1 and 100,000, so enumerating subsequences is not viable. Each character has only two possible values, and the objective is a count rather than the resulting string. The empty string is balanced, and removing all occurrences of either letter always produces a valid result.

## Brute force

Try every subset of characters to delete, check whether the survivors contain a `b` before any later `a`, and select the fewest deletions. This takes exponential time in the length. A simpler polynomial baseline tests every split position and counts b's before it plus a's after it, taking O(n²) if each count scans its side.

## The insight

Maintain the best deletion count for the prefix and the number of b's seen. A new b can always be appended to a balanced result without further deletion. For a new a, either delete that a, costing one more than the previous optimum, or keep it and delete every earlier b. The latter leaves only earlier a's and the new a, costing exactly the count of earlier b's. These are exhaustive: if a kept a has a preceding kept b, the result is invalid.

Taking the smaller option maintains the optimal prefix count by induction. The raw b count tracks the cost of the second option even if a different optimal prefix had already deleted some characters. Neither a split list nor an explicit resulting string is needed.

## Optimal solution, traced

For `"baba"`:

```steps
First b
There is one b and the best deletion count is 0.
---
First a and next b
For a, min(delete it, remove earlier b) = 1. The next b raises the seen count to 2, without changing the best.
---
Final a
min(1 + 1, 2) = 2, so return 2.
```

## Code

```python
def minimum_balanced_deletions(s):
    b_count = 0
    best = 0
    for char in s:
        if char == 'b':
            b_count += 1
        else:
            best = min(best + 1, b_count)
    return best
```

## Complexity

The scan visits n characters once: O(n) time and O(1) auxiliary space. The input is not modified. The stored count is at most n, and no recursion is involved.

## Mistakes and edge cases

Already balanced strings, including all a's or all b's, need zero deletions. A balanced result may contain only one letter or be empty. Counting every inversion is wrong because one deletion can remove many inversions. `b_count` counts all original b's seen, not just those kept by one particular optimal prefix.

## Variations

- Return a split position and the actual indices to delete.
- Assign different deletion costs to characters and compare weighted prefix and suffix totals.

=== card | 1140

## The problem

Players alternate taking stones from the front of a row of piles. Initially M is 1; on a turn a player takes X piles, where 1 <= X <= 2M and at most the number remaining, then M becomes max(M, X). Both players play optimally to maximize their own stones. Return the first player's total. For `[2,7,9,4,4]`, the answer is 10.

## Constraints and what they imply

There are 1 to 100 piles, each with 1 to 10,000 stones. The total number of stones is fixed and all piles are positive. Each turn must take at least one pile, and taking all remaining piles is legal when the current limit permits it.

## Brute force

Generate every legal sequence of moves until all piles are taken, alternating players and choosing the best outcome for the current player. The branching factor and depth can grow with the number of piles, producing an exponential game tree. Repeated states do not depend on the exact earlier moves once the next index and M are fixed.

## The insight

Let `best(i, m)` be the maximum stones the player about to move can obtain from the remaining suffix. The suffix total is fixed. After taking x piles, the opponent obtains `best(i+x, max(m,x))`; everything else belongs to the current player. Therefore choose x minimizing the opponent's optimal share, or equivalently maximize suffix total minus that share. If at most 2m piles remain, the current player can take all of them and this is optimal because every pile is positive.

Precompute suffix sums, then memoize the two-argument recurrence. Each call either returns the remaining total immediately or advances the index, so the recursion is acyclic. The same definition applies on both players' turns, avoiding separate turn-specific cases.

## Optimal solution, traced

For `[1,2,3]` with M = 1:

```steps
Take one
The opponent faces [2,3] with M = 1 and can take both, leaving the first player 1.
---
Take two
The opponent receives the remaining 3, leaving 1 + 2 = 3 for the first player.
---
Choose
The larger guaranteed share is 3.
```

## Code

```python
from functools import lru_cache

def stone_game_ii(piles):
    n = len(piles)
    suffix = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + piles[i]
    @lru_cache(None)
    def best(i, m):
        if 2 * m >= n - i:
            return suffix[i]
        return suffix[i] - min(best(i + x, max(m, x))
                               for x in range(1, 2 * m + 1))
    return best(0, 1)
```

## Complexity

There are O(n²) possible `(i, m)` states and each tries at most O(n) moves, for O(n³) time in this direct bound. Memoization and suffix sums use O(n²) space, including O(n) recursion depth. The actual number of reachable states may be smaller.

## Mistakes and edge cases

The opponent is also optimizing, so taking the largest immediate pile total is not always best. Update M with the number of piles taken, not their stone sum. A single pile is taken in full. The shortcut relies on positive piles and on being allowed to take all remaining piles.

## Variations

- Store the best move at each state and reconstruct one optimal play sequence.
- Return the score difference rather than the first player's total.

=== card | 688

## The problem

A knight starts at a specified cell on an n by n chessboard and makes exactly k independent moves. Each move chooses one of its eight standard offsets with equal probability, even if it leaves the board. Once off the board it cannot return. Return the probability that it is still on the board after k moves. On a 1 by 1 board with one move, the probability is 0.

## Constraints and what they imply

The board size is 1 to 25, k is 0 to 100, and the starting cell is valid. There are exponentially many possible move sequences; leaving the board on any intermediate move counts as failure. A floating-point answer is expected with tolerance; no random simulation is needed for the computed result.

## Brute force

Enumerate all 8^k move sequences, test whether every prefix remains on the board, and divide the number of survivors by 8^k. This is exact but infeasible for large k. A random estimate avoids enumeration but cannot guarantee the requested precision and introduces sampling error.

## The insight

A state stores the probability mass at each board cell after a given number of moves, counting only paths that never left. Initially the start cell holds probability one. At each step, send one eighth of each cell's mass to every legal knight destination; the remaining shares disappear off the board. Different paths arriving at the same cell can be added because their future behavior depends only on that cell and the number of moves left.

Use a new board for each step, so mass arriving during a step is not moved again in that same step. Summing all cells after k steps gives the probability of survival. When k is zero the initial mass remains intact, including on a one-cell board.

## Optimal solution, traced

For n = 3, one move from the center `(1,1)`:

```steps
Initial mass
The center has probability 1 and every other cell has probability 0.
---
Distribute
Each of the eight knight offsets leaves the board, so no mass reaches a legal destination.
---
Total
The new board sums to 0; survival probability is 0.
```

## Code

```python
def knight_probability(n, k, row, column):
    offsets = [(dr, dc) for dr, dc in ((1,2),(1,-2),(-1,2),(-1,-2),
                                        (2,1),(2,-1),(-2,1),(-2,-1))]
    current = [[0.0] * n for _ in range(n)]
    current[row][column] = 1.0
    for _ in range(k):
        following = [[0.0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                for dr, dc in offsets:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        following[nr][nc] += current[r][c] / 8.0
        current = following
    return sum(map(sum, current))
```

## Complexity

There are k rounds over n² cells and eight fixed moves, so time is O(kn²) and auxiliary space is O(n²) for two boards. Floating-point rounding can cause tiny errors; compare results using a tolerance rather than exact equality.

## Mistakes and edge cases

Do not divide by the number of legal moves: an off-board choice still has probability one eighth and is lost. Updating a board in place would allow extra moves in one round. Zero moves has answer 1. Position coordinates are zero-based, and all eight signed offsets must be included exactly once.

## Variations

- Compute survival probabilities from every starting cell for a fixed number of moves.
- Change the move distribution to nonuniform probabilities that sum to one.

=== card | 1442

## The problem

For an integer array, count index triples i < j <= k such that the XOR of `arr[i:j]` equals the XOR of `arr[j:k+1]`. Both parts are nonempty. For `[2,3,1,6,7]`, four triples satisfy the condition. Return the number of triples, not their index lists.

## Constraints and what they imply

The array has 1 to 300 elements, each between 1 and 100,000,000. Quadratic work is comfortably feasible. The two ranges must both contain at least one element. Different split positions within the same outer interval count as different triples.

## Brute force

Try all O(n³) triples and explicitly XOR the two selected parts, costing up to O(n) per triple and O(n⁴) overall. Prefix XORs reduce each comparison to constant time but still leave O(n³) choices. The split index can instead be counted in bulk once the outer interval is known.

## The insight

The two part XORs are equal exactly when their combined XOR is zero: XORing equal quantities gives zero, and if `a XOR b` is zero then a equals b. For a fixed interval from i through k whose XOR is zero, every j in `i+1` through k is valid. There are exactly k-i such splits, provided k > i.

Enumerate each start i and extend its end k while maintaining the XOR of the current interval. Whenever that XOR is zero, add k-i. This counts every triple exactly once because its outer endpoints determine a unique interval, and its split belongs to precisely the counted range. A length-one zero interval would contribute zero automatically.

## Optimal solution, traced

For `[1,3,2]`:

```steps
Start at 0
The running XORs are 1, 2, then 0.
---
Zero interval
For i = 0 and k = 2, j can be 1 or 2, so add 2.
---
Other starts
Neither remaining interval has XOR zero; the answer is 2.
```

## Code

```python
def count_xor_triplets(arr):
    answer = 0
    for i in range(len(arr)):
        value = 0
        for k in range(i, len(arr)):
            value ^= arr[k]
            if value == 0:
                answer += k - i
    return answer
```

## Complexity

There are n(n+1)/2 intervals, each extended in constant time: O(n²) time and O(1) auxiliary space. This matches the small input constraint. The count can be much larger than the array length; Python integers retain the exact result.

## Mistakes and edge cases

The split j may equal k, leaving one element on the right, but it may not equal i. Adding k-i+1 would count an empty left part. XOR is not ordinary addition, and a zero interval contributes multiple triples rather than one. A one-element input returns zero.

## Variations

- Use prefix XOR frequencies and index sums to count contributions in linear time.
- Return the valid triples themselves, accepting output-sensitive cost.

=== card | 1823

## The problem

Number n friends from 1 through n around a circle. Starting at friend 1, count k people including the current person, remove the kth, and continue from the next remaining person. Repeat until one friend remains; return that friend's original number. For n = 5 and k = 2, the survivor is 3.

## Constraints and what they imply

Both n and k are between 1 and 500. Direct list removal is possible at this scale but can shift O(n) elements per deletion. The identity of the survivor depends on the circular position, so zero-based indexing makes wraparound arithmetic especially simple.

## Brute force

Keep the current circle in a list. Repeatedly move `(k-1)` positions forward modulo the list length, remove that element, and continue at the same list index modulo the new length. This simulation is intuitive but requires O(n²) time in Python because removing from the middle shifts elements. It uses O(n) space.

## The insight

Suppose the survivor's zero-based position in a circle of size s-1 is known, where counting starts immediately after a removal. In the original circle of size s, that reduced circle begins at position k modulo s. Shifting the survivor by k and wrapping modulo s maps it back to the original numbering. Therefore `winner(s) = (winner(s-1) + k) % s`, with `winner(1) = 0`.

Build the answer from size one upward. The reduction and reverse shift are valid even when k exceeds the circle size, because only its remainder determines the removed position. Convert the final zero-based position back to the requested one-based friend number.

## Optimal solution, traced

For n = 5, k = 2:

```steps
Base
At size 1 the survivor index is 0.
---
Grow
Sizes 2, 3, and 4 produce indices 0, 2, and 0 respectively.
---
Finish
At size 5 the index is (0 + 2) % 5 = 2, corresponding to friend 3.
```

## Code

```python
def circular_winner(n, k):
    winner = 0
    for size in range(2, n + 1):
        winner = (winner + k) % size
    return winner + 1
```

## Complexity

The loop performs n-1 constant-time arithmetic operations: O(n) time and O(1) auxiliary space. It does not construct the circle or the elimination order. Python arithmetic naturally handles larger k as well.

## Mistakes and edge cases

Counting includes the current person, so the first removal in a zero-based list is at k-1, not k. The recurrence shifts by k because the next start is one position beyond that removed person. With k = 1 the last numbered friend survives; with n = 1 the answer is 1 regardless of k.

## Variations

- Simulate the circle to return the complete elimination order.
- Use an order-statistics structure to efficiently retrieve eliminated positions for very large n.

=== card | 1352

## The problem

Design a stream supporting `add(num)` and `getProduct(k)`. The latter returns the product of the last k added numbers. For additions 3, 0, 2, 5, querying the last two returns 10, while querying the last three returns 0. Queries always refer to at least one and no more than the number of inserted values.

## Constraints and what they imply

Numbers are between 0 and 100, and there are at most 40,000 operations. The problem guarantees queried products fit in a signed 32-bit integer. The stream may contain zeros, including consecutive zeros, and each query refers to the current end of the stream. Exact integer arithmetic is available in Python.

## Brute force

Keep all inserted numbers and multiply the last k entries on each query. An addition takes O(1), but a query takes O(k), making a long sequence of large queries expensive. It is nevertheless a useful reference implementation because it treats zeros and repeated values naturally.

## The insight

Within the suffix since the most recent zero, keep cumulative products starting with a sentinel 1. Adding a nonzero number multiplies the last prefix product and appends the result. If k is less than the prefix list length, the requested window lies wholly inside that zero-free suffix. Its product is the newest prefix divided exactly by the prefix immediately before the window.

When a zero is added, discard previous prefix products and restart at `[1]`. If k is at least the new list length, the requested window reaches that zero, so its answer is zero. This also handles consecutive zeros. The division is exact because each prefix is a product of the same initial zero-free sequence; integer division avoids floating-point rounding.

## Optimal solution, traced

After adding 3, 0, 2, 5:

```steps
Reset
Adding 0 resets the prefix list to [1].
---
New suffix
Adding 2 and 5 produces [1, 2, 10].
---
Queries
k = 2 gives 10 // 1 = 10. k = 3 reaches the preceding zero, so returns 0.
```

## Code

```python
class ProductOfNumbers:
    def __init__(self):
        self.prefix = [1]

    def add(self, num):
        if num == 0:
            self.prefix = [1]
        else:
            self.prefix.append(self.prefix[-1] * num)

    def getProduct(self, k):
        if k >= len(self.prefix):
            return 0
        return self.prefix[-1] // self.prefix[-k - 1]
```

## Complexity

Each operation uses O(1) arithmetic operations amortized, and the list uses O(a) space after a additions without zero. Resetting can release O(a) stored entries at once, charged to their earlier additions. Python integer multiplication and division have size-dependent costs if cumulative products grow large, even if queried products fit the problem guarantee. Resetting releases the old list.

## Mistakes and edge cases

A window ending just after a zero must include that zero when k equals the current prefix list length. A window of size one returns the latest value, including zero. Do not divide by a prefix containing zero, and do not use floating-point division. The API assumes valid positive k as specified.

## Variations

- Return products modulo a prime, taking care that division requires invertible factors.
- Support arbitrary range products by tracking zero counts and prefix products per segment.

=== card | 2101

## The problem

Each bomb has integer coordinates and a blast radius. Detonating a bomb immediately detonates every other bomb whose center lies within or on its radius; those bombs can trigger more bombs. Choose one initial bomb and return the largest number that eventually detonate. For `[[0,0,2],[2,0,1],[3,0,1]]`, starting at the first triggers all three.

## Constraints and what they imply

There are 1 to 100 bombs; coordinates and radii can be as large as 100,000. A blast relation is directional because radii differ. A bomb is included in its own final detonation count. Coordinates need not be distinct, and touching the blast boundary is sufficient.

## Brute force

For each possible initial bomb, repeatedly scan all detonated and undetonated bombs, adding any bomb currently in range, until no further changes occur. A straightforward implementation can perform O(n) rounds of O(n²) comparisons per starting bomb, for O(n⁴) time. It is a useful direct simulation but repeatedly checks the same relationships.

## The insight

Construct a directed edge from bomb i to bomb j exactly when squared distance between centers is at most radius i squared. A chain of detonations corresponds to a directed path; every bomb on such a path eventually detonates, and every detonated bomb has a path from the initial bomb. Thus the number of bombs triggered is precisely the reachable vertex count.

Run a depth-first search from each vertex, marking a bomb when it is first added to the stack. The visited set prevents cycles and duplicate counting. Take the largest count. Directed reachability, rather than undirected connected components, is essential when a large-radius bomb reaches a small-radius bomb that cannot reach back.

## Optimal solution, traced

For `[[0,0,2],[2,0,1],[3,0,1]]`:

```steps
Edges
The first bomb reaches the second on its boundary; the second reaches the third.
---
Search
Starting at the first visits it, then the second, then the third.
---
Result
All three bombs are reachable, so the maximum is 3.
```

## Code

```python
def maximum_detonation(bombs):
    n = len(bombs)
    graph = [[] for _ in bombs]
    for i, (x, y, radius) in enumerate(bombs):
        for j, (xx, yy, _) in enumerate(bombs):
            if i != j and (x - xx) ** 2 + (y - yy) ** 2 <= radius ** 2:
                graph[i].append(j)
    answer = 0
    for start in range(n):
        seen = {start}
        stack = [start]
        while stack:
            for nxt in graph[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        answer = max(answer, len(seen))
    return answer
```

## Complexity

Building the graph takes O(n²) time and space. Each of n searches costs O(n + e), giving O(n³) worst-case time for a dense graph and O(n²) total auxiliary space. Python integers avoid overflow in squared distances.

## Mistakes and edge cases

Include bombs exactly on the radius boundary. A blast need not be reciprocal, and transitive triggering can reach bombs outside the initial radius. Mark visited nodes before pushing them to avoid repeated stack entries. A single bomb always yields one, even if it reaches nothing else.

## Variations

- Return an initial bomb achieving the maximum as well as the count.
- Compute reachability for all starts using a transitive-closure matrix.

=== card | 382

## The problem

A nonempty singly linked list is provided to a sampler. Each call to `getRandom()` must return a node's value, with every node equally likely, without assuming the list length is known. Repeated values may occur: the probability requirement applies to nodes, not distinct values. For a three-node list, each node must be chosen with probability one third.

## Constraints and what they imply

The list has 1 to 10,000 nodes, node values range from -10,000 to 10,000, and at most 10,000 calls are made. The follow-up asks for constant extra space and permits a list too large to store. The algorithm therefore cannot rely on an indexed array of all nodes.

## Brute force

Traverse the list once, copy all values into an array, and choose a uniformly random array index on each query. Construction takes O(n) time and space, while a query is O(1). This works for a fixed list but violates the constant-extra-space follow-up and uses memory proportional to the list length.

## The insight

Scan the list once per query. When visiting the ith node, replace the current candidate with probability 1/i, using an unbiased integer draw. For any earlier node, its selection probability after i-1 nodes is 1/(i-1), and it survives the new replacement with probability (i-1)/i. Their product is 1/i. The new node is selected with probability 1/i as well, establishing uniformity by induction without knowing the final length.

The first node is always selected. Only the current node, a counter, and one candidate value are stored. A new random scan on each call gives an independent selection when the underlying random draws are independent. If equal values appear on several nodes, their returned value's probability is the sum of those nodes' probabilities.

## Optimal solution, traced

For a list A -> B -> C:

```steps
First node
Choose A with probability 1.
---
Second node
Replace A by B with probability 1/2, leaving each with probability 1/2.
---
Third node
Replace by C with probability 1/3; A and B each survive with probability 1/2 times 2/3 = 1/3.
```

## Code

```python
import random

class RandomNode:
    def __init__(self, head):
        self.head = head

    def getRandom(self):
        node = self.head
        chosen = None
        count = 0
        while node is not None:
            count += 1
            if random.randrange(count) == 0:
                chosen = node.val
            node = node.next
        return chosen
```

## Complexity

For n nodes each call traverses the list once, taking O(n) time and O(1) auxiliary space. Initialization stores only the head in O(1) time and space. The list is assumed nonempty and unchanged during a call.

## Mistakes and edge cases

Choosing every node with the same fixed replacement probability biases toward later nodes. Sampling a value uniformly among distinct values is also wrong when duplicates occur. A single-node list always returns that value. Do not use modulo on a biased random integer source; `randrange(count)` directly supplies a uniform choice.

## Variations

- Sample k distinct nodes uniformly using a reservoir of size k.
- Precompute an array for a static list when O(n) memory is acceptable and calls must be fast.

=== card | 1856

## The problem

For each nonempty contiguous subarray of positive integers, multiply its minimum element by its sum. Return the largest such min-product modulo 1,000,000,007. Choose the largest exact product before reducing it modulo the constant. For `[1,2,3,2]`, subarray `[2,3,2]` gives 2 times 7, or 14.

## Constraints and what they imply

The array contains 1 to 100,000 positive values, each at most 10,000,000. The true answer is guaranteed to fit a signed 64-bit integer, though intermediate arithmetic in Python remains exact. The subarray must be contiguous and nonempty. The modulo affects the returned representation, not which subarray is considered largest.

## Brute force

Enumerate all O(n²) subarrays, incrementally maintaining their minimum and sum, then compare their products. This takes O(n²) time and constant extra space, but is too slow for the largest input. The same candidate minimum appears in many overlapping intervals, so considering its maximal span is enough.

## The insight

Fix a position as a minimum. Its best interval extends until a strictly smaller value blocks it on each side: all included values are at least the chosen value, and positivity makes the widest valid interval at least as good as any narrower one. Prefix sums give the sum of an interval in constant time.

A stack of indices with nondecreasing values finds these spans in one scan. When a smaller value appears, pop each larger stack top; the current position is its first strictly smaller right boundary. The new stack top is a previous value no greater than the popped value. Equal values are allowed to remain: the leftmost equal minimum eventually obtains the whole span, so at least one representative covers every optimal interval. A final sentinel flushes the stack. Compare exact products before applying the modulus.

## Optimal solution, traced

For `[1,2,3,2]`:

```steps
First decline
At the last 2, pop 3: its span is only [3], giving 9.
---
Flush
The later 2 covers [3,2], while the earlier 2 covers [2,3,2], giving 14.
---
Compare
The 1 covers the whole array and gives 8. The maximum is 14.
```

## Code

```python
def max_sum_min_product(nums):
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + value)
    stack = []
    best = 0
    for right in range(len(nums) + 1):
        while stack and (right == len(nums) or nums[stack[-1]] > nums[right]):
            index = stack.pop()
            left = stack[-1] + 1 if stack else 0
            total = prefix[right] - prefix[left]
            best = max(best, nums[index] * total)
        stack.append(right)
    return best % 1_000_000_007
```

## Complexity

Every index is pushed and popped at most once, so time is O(n). Prefix sums and the stack occupy O(n) auxiliary space. The end sentinel is appended only after the final flush and is never dereferenced.

## Mistakes and edge cases

The maximal-span argument relies on positive inputs; it fails for arbitrary negative values. Equal minima need a consistent tie rule, not accidental omission of all full spans. Do not compare reduced residues. A single element produces its square, and an all-equal array uses its entire sum.

## Variations

- Return the boundaries of a maximizing subarray along with its product.
- Find the largest rectangle in a histogram using a related stack of limiting heights.

=== card | 2349

## The problem

Design a system supporting `change(index, number)`, which assigns or replaces the number at an index, and `find(number)`, which returns the smallest index currently assigned that number, or -1 if none. For changes `(2,10)`, `(1,10)`, then `(1,20)`, finding 10 returns 2 and finding 20 returns 1.

## Constraints and what they imply

Indices and numbers are positive integers up to 10⁹, and there are at most 100,000 operations. Most possible indices may never be assigned, and a query may ask about a number that has never been assigned. Reassignments must be reflected in queries, including repeated assignments of the same number.

## Brute force

Store only a dictionary from index to current number. To find a number, scan all assignments and return the smallest matching index. Changes are O(1), but each query costs O(d) for d assigned indices, which can make a long operation sequence quadratic.

## The insight

Keep the authoritative current number for each index, and separately keep a min-heap of candidate indices for each number. On change, update the dictionary and push the index into the new number's heap. Old heap entries are allowed to remain. On find, repeatedly remove the smallest heap entry while the dictionary says that index currently holds a different number. The first valid entry, if any, is the smallest current index because every current assignment was inserted and a heap presents candidates in increasing order.

A reassigned index can return to an earlier number, leaving duplicate valid entries. They do not affect the minimum and become removable if the index later changes again. Each pushed entry is popped at most once, so cleanup is amortized across operations, although one find may perform many removals.

## Optimal solution, traced

For `change(2,10)`, `change(1,10)`, `change(1,20)`:

```steps
Changes
The heap for 10 contains indices 1 and 2, but the current mapping says index 1 holds 20.
---
Find 10
Remove stale top 1; index 2 is current and is returned.
---
Find 20
Its heap contains valid index 1, so return 1.
```

## Code

```python
import heapq

class NumberContainers:
    def __init__(self):
        self.current = {}
        self.heaps = {}

    def change(self, index, number):
        self.current[index] = number
        heapq.heappush(self.heaps.setdefault(number, []), index)

    def find(self, number):
        heap = self.heaps.get(number, [])
        while heap and self.current.get(heap[0]) != number:
            heapq.heappop(heap)
        return heap[0] if heap else -1
```

## Complexity

For q operations, each change pushes once and each entry is removed at most once. Total heap work is O(q log q), or O(log q) amortized per operation, with O(q) space. A single find may remove many stale entries, so its worst-case latency is not O(log q).

## Mistakes and edge cases

A heap alone cannot determine whether an old assignment is still current. Do not return its top without validating against the authoritative dictionary. A never-seen number returns -1. Repeated changes to the same number may create duplicates; these are harmless but consume space until removed or the structure is discarded.

## Variations

- Use ordered sets to delete old assignments eagerly and bound a query's cleanup work.
- Return the largest assigned index using max-heaps and the same validity check.

=== card | 2402

## The problem

There are n rooms numbered from 0. Meetings have distinct original start times and half-open intervals `[start, end)`. Process meetings in order of original start. A meeting uses the smallest-numbered room free at its start. If none is free, delay it until the earliest room becomes free, preserving its duration; if several rooms free at that time, choose the smallest number. Earlier original starts have priority over later starts when waiting. Return the room hosting the most meetings, breaking count ties by smallest room number.

For two rooms and meetings `[[0,10],[1,5],[2,7],[3,4]]`, the third meeting waits until time 5 and the fourth waits until time 10. Room 0 hosts two meetings and room 1 hosts two, so return 0.

## Constraints and what they imply

There are 1 to 100 rooms and up to 100,000 meetings. Start times are unique, durations are positive, and the original end is at most 500,000. Delayed finish times can greatly exceed original times, so arithmetic must accommodate accumulated durations. The input order is not guaranteed to match the order of original start times. A room whose meeting ends exactly at a start is free for that start.

## Brute force

Sort by original start, keep each room's next available time, and examine all n rooms for each meeting. If any available time is at most the start, choose the smallest such index; otherwise choose the minimum pair `(available time, room index)`. Update that room and increment its count. This direct simulation is O(m log m + mn) time and O(n) state, excluding the sorted copy. It is an excellent oracle for small cases, but scans rooms even when only one is relevant.

## The insight

There are two distinct orderings to maintain. Among currently free rooms, only the smallest room number matters. Among occupied rooms, the earliest ending time matters first and the room number breaks ties. Use a min-heap of free indices and a min-heap of `(actual end, room)` pairs for busy rooms. At the start of each original meeting, move every room with actual end at most the original start into the free heap. If any are free, choose the smallest and schedule at the original start. Otherwise pop the earliest busy pair and schedule at its end, retaining the original duration.

Processing by original start enforces the waiting priority: any previously delayed meeting has already reserved its room before a later request is processed. A busy heap entry can represent a meeting scheduled in the future, not just one active at the current original time. Its end still correctly represents when its room next becomes available. All rooms whose prior end is at most the current start must be released before choosing, since a room that finished earlier but has a larger number must not automatically beat a lower-numbered free room.

For correctness, each room is in exactly one heap after a meeting is assigned. Releasing completed entries preserves the set of free rooms. If the free heap is nonempty, its minimum implements the first rule. Otherwise, the lexicographically smallest busy pair implements the earliest possible start and room tie rule. Replacing the chosen entry with its new end preserves this invariant for the next meeting. Induction over sorted meetings proves every assignment and count is correct.

## Optimal solution, traced

For two rooms and `[[0,10],[1,5],[2,7],[3,4]]`:

```steps
First two meetings
Room 0 is busy until 10 and room 1 until 5; each count is 1.
---
Meeting [2,7)
No room is free at 2. Room 1 frees first at 5, so duration 5 moves it to [5,10); its count becomes 2.
---
Meeting [3,4)
Both rooms next free at 10. The tie chooses room 0, whose delayed meeting ends at 11. Both counts are 2, so return 0.
```

## Code

```python
import heapq

def most_booked(n, meetings):
    free = list(range(n))
    heapq.heapify(free)
    busy = []
    counts = [0] * n
    for start, end in sorted(meetings):
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(free, room)
        if free:
            room = heapq.heappop(free)
            finish = end
        else:
            available, room = heapq.heappop(busy)
            finish = available + end - start
        counts[room] += 1
        heapq.heappush(busy, (finish, room))
    return max(range(n), key=lambda room: (counts[room], -room))
```

## Complexity

For m meetings, sorting costs O(m log m). Each meeting inserts and removes at most one busy and one free heap entry, taking O(m log n) total heap time. The heaps and counts use O(n) space, and the sorted copy adds O(m). Python's unbounded integers avoid overflow in delayed end times. Returning the maximum count scans the n rooms once.

## Mistakes and edge cases

Use `<=` when releasing rooms because intervals are half-open. Do not select the earliest-ending room when any room is already free: the lowest-numbered free room wins even if it freed more recently. A delayed meeting keeps its duration, not its original end. When multiple busy rooms end together, tuple ordering must break ties by room number. Process by original start, not delayed start, to preserve waiting priority. One room simply serializes every meeting; unused rooms have count zero.

## Variations

- Return each meeting's assigned room and actual start and end times.
- Change the tie rule to prioritize another room attribute, adjusting both heaps and the final count comparison.

=== card | 1964

## The problem

For every position in an array of obstacle heights, find the maximum length of a nondecreasing subsequence that ends at that exact position. Selected obstacles must preserve their original order, but need not be adjacent. Equal heights may follow each other. Return one answer per position. For `[1,2,3,2]`, the answers are `[1,2,3,3]`.

## Constraints and what they imply

There are 1 to 100,000 obstacles, each between 1 and 10⁷. The answer for each position depends only on the prefix through that position. A course ending at one position need not include the immediately preceding obstacle. The result contains one length for every input position.

## Brute force

For each position i, examine every earlier position j whose height is at most height i, and set the answer to one plus the largest answer at such a j, or one if none exists. This directly implements the definition and costs O(n²) time and O(n) space. Enumerating all subsequences would be exponential and is unnecessary even as a baseline.

## The insight

Maintain `tails[length-1]`, the smallest possible final height among nondecreasing subsequences of that length in the processed prefix. A smaller tail is at least as useful as a larger tail for extending a subsequence later. The tails are nondecreasing: removing the last item of a minimum-tail length L course gives a valid shorter course with a tail no greater than the longer course's final value.

For new height x, find the first tail strictly greater than x. All preceding tails are at most x, so the longest of them can be extended by x. If the insertion position is p, this yields a course of length p+1 ending at x. No longer course ending at x exists: removing x from one would produce a length p+1 course with tail at most x, contradicting the position of the first greater tail. Thus p+1 is exactly the required answer for this position.

Replace `tails[p]` with x, or append x if p is at the end. Replacement cannot discard a better future possibility: x is smaller than the previous tail at this length and therefore can be followed by everything that could follow the old tail. The preceding tail is at most x, and the following tails are at least the old value, so sorted order survives. Binary search for the first strictly greater element is `bisect_right`; searching for the first greater-or-equal element would mistakenly disallow equal heights.

The array of tails is a collection of separate optimal witnesses. Its entries need not themselves describe one subsequence, and replacing an entry does not retroactively change the answers already returned. The procedure records the new element's own extension length, rather than the length of the longest course anywhere in the prefix. This distinction matters when a low obstacle arrives after a long increasing run.

## Optimal solution, traced

For `[1,2,3,2]`:

```steps
First three
Heights 1, 2, 3 append in turn. Tails become [1,2,3], with answers 1, 2, 3.
---
Last height 2
The first tail strictly greater than 2 is 3 at position 2. Replace it with 2.
---
Finish
Tails are [1,2,2], and the last answer is 3 from course [1,2,2]. The full output is [1,2,3,3].
```

## Code

```python
from bisect import bisect_right

def longest_obstacle_course(obstacles):
    tails = []
    answers = []
    for height in obstacles:
        position = bisect_right(tails, height)
        if position == len(tails):
            tails.append(height)
        else:
            tails[position] = height
        answers.append(position + 1)
    return answers
```

## Complexity

Each of n obstacles performs one binary search in a list of at most n tails, for O(n log n) time. The tail list and returned answers use O(n) space. The input is not modified. Appending and replacing a list entry are amortized O(1); no insertion in the middle is performed.

## Mistakes and edge cases

Use `bisect_right`, because equal heights can extend one another. A decreasing array produces all ones, while an all-equal array produces 1 through n. Return the position-specific length even when a previous obstacle ended a longer course. Replacing a tail rather than inserting it is essential: inserting would change the meaning of the later indices. A single obstacle yields `[1]`.

## Variations

- Require strictly increasing heights, using the first tail greater than or equal to the current height.
- Track predecessor indices to reconstruct a longest course ending at each requested position.

=== card | 1146

## The problem

Design an array initialized to zeros with `set(index, val)`, `snap()`, and `get(index, snap_id)`. A snapshot returns an increasing identifier starting at 0; a later get returns the value at that index when that snapshot was taken. Setting an index multiple times before a snapshot keeps only its last value in that snapshot. For a length-one array, set 5, snap, then set 6; get at snapshot 0 returns 5.

## Constraints and what they imply

The length is 1 to 50,000, values are 0 to 10⁹, and at most 50,000 operations occur. Each get refers to an existing snapshot and a valid index. A snapshot can be taken without any intervening changes, and unchanged positions retain their prior values.

## Brute force

Keep the current array and append a full copy whenever snap is called. A get is then a direct lookup in the stored copy. This simple simulation costs O(length) time and space per snapshot, which is wasteful when snapshots are frequent and updates sparse.

## The insight

Store a chronological change history separately for each index. A history starts with `(0,0)`, representing its initial value. The current snapshot identifier denotes the version being edited. On set, append `(current id, value)` unless the latest record already has that id, in which case replace it. A snap returns the current id and increments it; no per-index copying is needed.

For get at version s, find the last record whose identifier is at most s. Every earlier change has been superseded, and every later change happened after the snapshot. Histories have increasing identifiers because same-version writes are coalesced, so binary search locates this predecessor. Searching just identifiers avoids assuming a maximum value for tuple tie-breaking.

## Optimal solution, traced

For a length-one array:

```steps
Write and snap
Set index 0 to 5; history is [(0,5)]. Snap returns 0 and advances the current id to 1.
---
Write again
Set index 0 to 6; history becomes [(0,5),(1,6)].
---
Read old version
The latest record at or before 0 is (0,5), so get(0,0) returns 5.
```

## Code

```python
class SnapshotArray:
    def __init__(self, length):
        self.history = [[(0, 0)] for _ in range(length)]
        self.version = 0

    def set(self, index, val):
        records = self.history[index]
        if records[-1][0] == self.version:
            records[-1] = (self.version, val)
        else:
            records.append((self.version, val))

    def snap(self):
        result = self.version
        self.version += 1
        return result

    def get(self, index, snap_id):
        records = self.history[index]
        lo, hi = 0, len(records)
        while lo < hi:
            mid = (lo + hi) // 2
            if records[mid][0] <= snap_id:
                lo = mid + 1
            else:
                hi = mid
        return records[lo - 1][1]
```

## Complexity

Initialization costs O(length) time and space. Set and snap are O(1) amortized; get takes O(log h) for h recorded versions at that index. Total space is O(length + number of sets), since each set adds at most one record. Same-version writes may use less.

## Mistakes and edge cases

A get must use the latest change at or before the snapshot, not just an exact identifier match. Unchanged indices remain zero across arbitrarily many snapshots. Replacing a record is safe only while its snapshot has not yet been taken. Repeated snaps without writes do not require new history entries. The API assumes existing snapshot ids.

## Variations

- Add a method that enumerates indices changed between two snapshots, using a separate change log.
- Store a persistent tree when snapshots must also support efficient range aggregates.
