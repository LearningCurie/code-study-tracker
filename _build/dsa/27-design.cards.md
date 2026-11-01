=== card | 705
time: 20 min

## The problem

Implement an integer set with add, remove and membership operations without using a built-in hash set or map. Adding a present key and removing an absent key leave the collection unchanged.

## Constraints and what they imply

Keys are integers from 0 through 1,000,000 inclusive. This finite, reasonably small universe permits direct addressing: the key itself identifies a slot. The number of operations can be large, so scanning stored keys on every query is undesirable. We trade fixed memory for worst-case constant operation time.

## Brute force

Keep a list of present keys. Scan it to answer membership and to locate a deletion; also scan before inserting to avoid duplicates. Each operation can take O(n) for n stored keys, using O(n) space.

## The insight

Store one byte per possible key. Its value is one exactly when that key belongs to the set. Assigning a byte twice is harmless, as is clearing an already clear byte. The invariant holds initially because all bytes are zero, and each mutation changes exactly the slot named by its key.

## Optimal solution, traced

```steps
Start empty; add 7 twice
    slot 7 becomes 1 and remains 1
---
Remove 7, then ask for 7
    slot 7 becomes 0; answer {{False}}
---
Remove 7 again
    slot 7 stays 0; other slots do not change
```

The bounded universe is essential to this implementation; arbitrary integers would need a different representation or input validation.

## Code

```python
class MyHashSet:
    def __init__(self):
        self.present = bytearray(1_000_001)

    def add(self, key):
        self.present[key] = 1

    def remove(self, key):
        self.present[key] = 0

    def contains(self, key):
        return bool(self.present[key])
```

## Complexity

Initialization takes O(U) time and space for U = 1,000,001 possible keys. Every later operation takes O(1) worst-case time and O(1) extra space. The allocation depends on the universe, not the number actually stored.

## Mistakes and edge cases

- Allocate one extra slot for the inclusive maximum.
- Keys outside the contract are not checked; negative Python indices would otherwise address the wrong slot.
- A bytearray is direct addressing, not a dynamically sized hash table.

## Variations

- Pack membership bits to reduce the constant factor in space.
- Use chained buckets if the key universe becomes too large for direct addressing.

=== card | 933
time: 20 min

## The problem

Process a sequence of calls, each with a timestamp in milliseconds. For each new call return the number of calls in the inclusive interval from 3000 milliseconds before that timestamp through the current timestamp.

## Constraints and what they imply

Timestamps are positive and strictly increasing. The current call is itself in the answer. A call exactly 3000 milliseconds old still counts. Increasing time is what makes discarded calls permanently irrelevant; this implementation does not support out-of-order events.

## Brute force

Keep every past timestamp. For each new timestamp scan the list and count those within the interval. After n calls the worst-case total is O(n²), and all n timestamps remain stored.

## The insight

The active timestamps form a suffix of arrival order. Append the current time, then remove old timestamps from the front while they are strictly below the lower boundary. Every remaining time is at least the boundary and no greater than the current time. Every discarded time is even older, and cannot reenter any future window because future boundaries only move forward.

## Optimal solution, traced

```steps
Calls at 1 and 1000
    both are in the window; latest answer {{2}}
---
Call at 3001
    boundary is 1, so the first call remains; answer {{3}}
---
Call at 3002
    boundary is 2; remove 1 and answer {{3}}
```

Each timestamp enters once and leaves at most once, even if a single call removes many old entries.

## Code

```python
from collections import deque

class RecentCounter:
    def __init__(self):
        self.times = deque()

    def ping(self, t):
        self.times.append(t)
        while self.times[0] < t - 3000:
            self.times.popleft()
        return len(self.times)
```

## Complexity

Each call costs O(1) amortized, though one call may remove O(n) entries. Space is O(w), the number of calls currently in the window. It can be O(n) if all calls remain active.

## Mistakes and edge cases

- Use `<`, not `<=`, when expiring the inclusive lower endpoint.
- Append the new call before counting it.
- A queue of arrival order is insufficient for out-of-order timestamps.

## Variations

- Change the window length while keeping it fixed across the stream.
- Return a weighted sum by maintaining a running total as entries expire.

=== card | 622
time: 25 min

## The problem

Build a bounded FIFO queue that supports insertion at the rear, removal at the front, inspection of both ends, and empty/full queries. Insertions and removals return whether they succeeded; an empty end inspection returns -1.

## Constraints and what they imply

Capacity k is positive and fixed. Values are nonnegative, so -1 is an unambiguous empty result. The number of operations can greatly exceed k, so a queue that never reuses vacated positions would eventually fail despite having room. Duplicate values are allowed and have no special treatment.

## Brute force

Use a regular list in queue order. Append for insertion and delete index zero for removal, rejecting an insertion when the list has k items. Deleting the first item shifts the remaining entries and takes O(k) time; the list uses O(k) space.

## The insight

Treat the array as a ring. Keep `head`, the physical index of the first element, and `size`, the number of live elements. Logical offset j corresponds to `(head + j) % k`. The next free rear slot is at offset size; the last live element is at offset size - 1. Size distinguishes a completely full ring from an empty one even when their head positions coincide.

Initially size is zero. A successful enqueue fills exactly the next free slot and increases size. A successful dequeue advances head and decreases size, leaving all other logical offsets in the same FIFO order. Full and empty operations do not mutate the invariant.

For example, after a dequeue the former second element becomes logical offset zero. The head can wrap repeatedly without moving any element. We deliberately retain the old bytes in an unused slot: they have no meaning until an enqueue overwrites that slot, and end inspections first check the size.

## Optimal solution, traced

```steps
Capacity 2; enqueue 8, enqueue 4
    head 0, size 2, physical slots [8, 4]
---
Dequeue and enqueue 6
    head 1; new element wraps to slot 0
    logical queue [4, 6]
---
Inspect both ends
    front {{4}}, rear {{6}}; queue is full
```

## Code

```python
class MyCircularQueue:
    def __init__(self, k):
        self.buf = [0] * k
        self.head = 0
        self.size = 0

    def enQueue(self, value):
        if self.isFull():
            return False
        self.buf[(self.head + self.size) % len(self.buf)] = value
        self.size += 1
        return True

    def deQueue(self):
        if self.isEmpty():
            return False
        self.head = (self.head + 1) % len(self.buf)
        self.size -= 1
        return True

    def Front(self):
        return -1 if self.isEmpty() else self.buf[self.head]

    def Rear(self):
        return -1 if self.isEmpty() else self.buf[(self.head + self.size - 1) % len(self.buf)]

    def isEmpty(self):
        return self.size == 0

    def isFull(self):
        return self.size == len(self.buf)
```

## Complexity

Every method takes O(1) time. The fixed buffer occupies O(k) space; each call uses O(1) extra space.

## Mistakes and edge cases

- Check fullness before writing, and emptiness before reading or advancing.
- Capacity one still works: both ends point to the same slot.
- Old values in vacated cells are irrelevant because size determines membership.
- A zero-capacity queue is outside the stated contract.

## Variations

- Implement a bounded deque with insertion and removal at both ends.
- Use a resizing ring buffer when capacity need not remain fixed.

=== card | 1396
time: 25 min

## The problem

Maintain passenger check-ins and check-outs for a transit network, then answer the average completed journey duration for an ordered pair of stations. A journey from A to B is distinct from one from B to A.

## Constraints and what they imply

Each rider has at most one open journey, and a check-out refers to a matching earlier check-in. Times are integers and checkout follows check-in. Queries refer to a station pair with at least one completed trip. Station names and rider identifiers can be used as dictionary keys. These validity guarantees let methods avoid defining error responses for malformed events.

## Brute force

Store each completed trip with its start, end and duration. For each average query, scan all completed trips, summing and counting matching pairs. Check-in and check-out remain constant expected time, but a query takes O(t) for t completed trips and storage grows with all t records.

## The insight

An average depends only on the sum and count, not the individual durations. Keep open trips by rider, and for each ordered station pair maintain the sum and count of completed durations. At check-out, remove the rider's open entry and update exactly one pair. This avoids counting a trip before it finishes and prevents an old check-in from being reused.

Inductively, each open entry represents one active rider, and each aggregate incorporates exactly the completed trips for its pair. The quotient is therefore the desired arithmetic mean. Separate entries for reversed pairs are necessary because direction affects the answer.

The aggregate is updated once per completed journey, regardless of how many riders travel simultaneously. Python's division returns a floating-point result, so clients comparing numerical answers should allow the problem's specified tolerance rather than rounding each individual duration.

## Optimal solution, traced

```steps
Rider 5 enters Oak at time 3 and exits Pine at 11
    (Oak, Pine) has total 8, count 1
---
Rider 9 travels Oak to Pine from 4 to 18
    total becomes 22, count 2
---
Query Oak to Pine
    average {{11.0}}; the reverse direction is separate
```

## Code

```python
class UndergroundSystem:
    def __init__(self):
        self.open = {}
        self.trips = {}

    def checkIn(self, rider, station, t):
        self.open[rider] = (station, t)

    def checkOut(self, rider, station, t):
        start, start_time = self.open.pop(rider)
        pair = (start, station)
        total, count = self.trips.get(pair, (0, 0))
        self.trips[pair] = (total + t - start_time, count + 1)

    def getAverageTime(self, start, end):
        total, count = self.trips[(start, end)]
        return total / count
```

## Complexity

Each operation is O(1) expected time, assuming dictionary operations and bounded station-name lengths. Space is O(a + p) for a active riders and p distinct completed station pairs; trip history is not retained. If names have unbounded length, hashing and comparing them also costs time proportional to their length.

## Mistakes and edge cases

- Do not average averages: accumulate a sum and its matching count.
- Remove the active entry at checkout so a rider may start another journey.
- Do not mix opposite directions or include unfinished trips.
- Invalid check-outs and unknown query pairs are outside the contract.

## Variations

- Maintain variance using the sum of squared durations as well.
- Retain individual trips if later cancellation or time-range queries are required.

=== card | 146
time: 30 min

## The problem

Design a bounded key-value cache. A successful lookup and every insertion or update make the key most recently used. On insertion into a full cache, remove the least recently used key. Return -1 for a missing lookup.

## Constraints and what they imply

Keys and values are nonnegative integers, so -1 indicates a miss. The stated capacity is positive; the implementation also handles zero capacity. A put of an existing key replaces its value without evicting anything and counts as a use. Both operations need constant expected time rather than a scan through the capacity.

## Brute force

Store values and a logical timestamp of their latest use. On a full insertion scan all keys to find the smallest timestamp and delete that key. Lookups and updates are expected O(1), but eviction takes O(c) for capacity c; storage is O(c).

## The insight

Combine a hash map with an ordered doubly linked list. Python's `OrderedDict` provides this composition: key lookup, moving a known key to the end and popping the first key are expected O(1). Maintain least recent at the beginning and most recent at the end. On a hit move the key to the end; on a put, insert or replace and then move to the end. If the size exceeds capacity, pop the first item.

The invariant holds initially for the empty cache. A hit or update removes just that key from its old position and places it last, preserving the relative order of every other key. A new key becomes newest, and the first key is exactly the eviction candidate if capacity is exceeded. A miss changes nothing.

## Optimal solution, traced

```steps
Capacity 2; put (1, 10), put (2, 20)
    least to most recent: [1, 2]
---
Get 1
    return {{10}}; order becomes [2, 1]
---
Put (3, 30)
    evict 2; order becomes [1, 3], and get 2 gives {{-1}}
```

## Code

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = OrderedDict()

    def get(self, key):
        if key not in self.items:
            return -1
        self.items.move_to_end(key)
        return self.items[key]

    def put(self, key, value):
        self.items[key] = value
        self.items.move_to_end(key)
        if len(self.items) > self.capacity:
            self.items.popitem(last=False)
```

## Complexity

Each get or put takes O(1) expected time with hash-table operations. Space is O(c), with at most c entries retained between calls; an insertion can temporarily add one extra entry. Worst-case adversarial hash collisions are not constant time.

## Mistakes and edge cases

- An update is a use, even if the value stays the same.
- A missing lookup must not change recency or create a key.
- Evict the oldest end, not the newest end.
- Capacity zero immediately evicts every insertion.

## Variations

- Implement the list explicitly with sentinels and a key-to-node map.
- Add expiration times, recognizing that expiry and recency are separate orderings.

=== card | 380
time: 30 min

## The problem

Support insertion, deletion and uniformly random selection from a set of integers. Insertion and deletion return whether the set changed; random selection is called only when the set is nonempty.

## Constraints and what they imply

Values can be negative, zero or positive. Duplicates are not stored. Each random result must have the same probability among currently present values, not among historical insertions. The required expected constant-time operations rule out shifting an arbitrary suffix on deletion.

## Brute force

Store the values in a list. A random position is easy to sample, but membership checks and locating a deletion can scan O(n) entries; deleting from the middle also shifts O(n) entries. Alternatively a set supports membership but constructing a list for each random query takes O(n).

## The insight

Use a dense array of values and a map from each value to its array index. To erase an interior entry, copy the last array value into its position, fix that value's index, and pop the last slot. No order needs to be preserved. Sampling a uniformly random array index then selects each value once, so all currently stored values have equal probability.

Initially both structures are empty. Insertion appends a previously absent value and records its position. Deletion updates the one displaced value and removes the deleted mapping, so the index map remains the inverse of the array. This also handles deleting the last entry: the moved value is the one being removed and its mapping is deleted afterwards.

The array order is deliberately unstable. A client must not infer insertion order from it; this freedom is exactly what avoids shifting elements. Uniformity depends on the random generator choosing indices uniformly, not on the values themselves being consecutive or similarly distributed.

## Optimal solution, traced

```steps
Insert 4, 7, 9
    array [4, 7, 9]; indices {4: 0, 7: 1, 9: 2}
---
Remove 7
    move 9 into slot 1, then pop
    array [4, 9]; indices {4: 0, 9: 1}
---
Choose either slot uniformly
    each of 4 and 9 has probability {{1/2}}
```

## Code

```python
import random

class RandomizedSet:
    def __init__(self):
        self.values = []
        self.index = {}

    def insert(self, val):
        if val in self.index:
            return False
        self.index[val] = len(self.values)
        self.values.append(val)
        return True

    def remove(self, val):
        if val not in self.index:
            return False
        i = self.index[val]
        last = self.values[-1]
        self.values[i] = last
        self.index[last] = i
        self.values.pop()
        del self.index[val]
        return True

    def getRandom(self):
        return random.choice(self.values)
```

## Complexity

All methods take O(1) expected time, including amortized dynamic-array append and expected dictionary operations. Space is O(n) for n current values. Random selection relies on `random.choice` selecting array positions uniformly.

## Mistakes and edge cases

- Update the moved value's index even when deleting an interior slot.
- Delete the requested mapping after updating the last value, including when both values are the same.
- Reject duplicate insertions and missing removals without changing state.
- Calling random selection on an empty set is outside the contract.

## Variations

- Permit duplicates by mapping each value to a set of positions.
- Sample several distinct values without replacement, specifying how state should change.

=== card | 284
time: 25 min

## The problem

Wrap an iterator with a `peek` operation that returns the next value without consuming it. Also provide `next` to consume that value and `hasNext` to report whether one exists.

## Constraints and what they imply

The underlying input is a finite Python iterator. It may yield any value, including None, so an ordinary value cannot safely signal exhaustion. Calls to peek and next are valid only when an element exists; this wrapper raises `StopIteration` otherwise. Repeated peeks and availability checks must not advance the logical sequence.

## Brute force

Read the entire iterator into a list and maintain a cursor. Peek and next then take O(1) time, but construction consumes O(n) time and extra space, and the approach cannot support a long or unbounded stream lazily.

## The insight

Maintain one buffered value and a distinct private sentinel for exhaustion. Fill the buffer once during construction. Peek reads the buffer without altering it; next returns the buffer and refills it from the underlying iterator. `hasNext` compares by identity with the sentinel. Since the underlying iterator has already advanced past the buffer, the logical remaining sequence is the buffer followed by its remaining elements.

Initially the invariant follows from one attempted read. Peek and hasNext leave it unchanged. Next removes exactly its first logical item and refills with the next underlying item; an exhausted iterator instead leaves the sentinel. The sentinel is a fresh object inaccessible to callers, so a yielded None is not confused with exhaustion.

The wrapper performs one-element read-ahead, which is observable if the source iterator has side effects. It does not duplicate or rewind the underlying source. Consumers should advance only through the wrapper once it is constructed, since an external advance could otherwise skip a value.

## Optimal solution, traced

```steps
Wrap iterator [None, 5]
    buffer is None; hasNext is {{True}}
---
Peek twice
    both return None; logical sequence is unchanged
---
Next twice
    returns None then 5; buffer becomes exhausted
    hasNext is {{False}}
```

## Code

```python
class PeekingIterator:
    def __init__(self, iterator):
        self.iterator = iter(iterator)
        self.end = object()
        self.buffer = next(self.iterator, self.end)

    def peek(self):
        if not self.hasNext():
            raise StopIteration
        return self.buffer

    def next(self):
        value = self.peek()
        self.buffer = next(self.iterator, self.end)
        return value

    def hasNext(self):
        return self.buffer is not self.end
```

## Complexity

The wrapper uses O(1) additional space. Construction and next each perform at most one underlying advance; peek and hasNext are O(1). The stated time assumes each underlying advance is O(1); a costly or blocking iterator adds its own cost.

## Mistakes and edge cases

- None and other falsey values can be real elements.
- Repeated peek or hasNext must not consume the next element.
- Empty input is exhausted immediately; peek and next raise `StopIteration`.
- A source with externally shared consumption can invalidate the wrapper's assumptions.

## Variations

- Support Python's `__iter__` and `__next__` protocol on the wrapper.
- Buffer k values to support looking farther ahead.

=== card | 2034
time: 30 min

## The problem

Maintain timestamped prices when updates can replace earlier records. Return the price at the greatest timestamp and the minimum and maximum among the current records.

## Constraints and what they imply

Timestamps and prices are positive integers. Updates may arrive in any timestamp order, including repeated corrections. Queries occur only after at least one update. The latest price is determined by the largest timestamp, not the most recently received update. An extrema query must ignore superseded prices.

## Brute force

Keep a timestamp-to-price dictionary. Find the current price using the largest timestamp, and scan all current values for minimum or maximum. An update is O(1) expected time and a query costs O(d) for d distinct timestamps, with O(d) storage.

## The insight

The dictionary is the authoritative current state. Record the largest timestamp ever seen, and push each update into both a min-heap and a max-heap. Heap entries are immutable historical candidates. Before returning an extremum, discard top entries whose stored price differs from the dictionary at that timestamp. A matching top is current; because every update is pushed, every current record has a matching entry in each heap.

Removing stale tops exposes a valid best candidate. If the top is valid, no current price can beat it: its own corresponding heap entry would have appeared earlier. An old entry whose price happens to equal a later correction is harmless, since it is indistinguishable as a candidate for the current value at that timestamp.

The two heaps may contain different stale entries after independent queries. Neither heap is the source of truth, so cleaning one does not require synchronizing the other. The dictionary retains one price for each timestamp regardless of how many corrections were received.

## Optimal solution, traced

```steps
Update time 2 to 9, then time 5 to 4
    current {{4}}, minimum 4, maximum 9
---
Correct time 2 to 1
    dictionary says {2: 1, 5: 4}; old heap entry 9 is stale
---
Ask maximum
    discard stale 9; answer {{4}}
    latest timestamp remains 5 despite the correction
```

## Code

```python
import heapq

class StockPrice:
    def __init__(self):
        self.prices = {}
        self.latest = None
        self.low = []
        self.high = []

    def update(self, timestamp, price):
        self.prices[timestamp] = price
        if self.latest is None or timestamp > self.latest:
            self.latest = timestamp
        heapq.heappush(self.low, (price, timestamp))
        heapq.heappush(self.high, (-price, timestamp))

    def current(self):
        return self.prices[self.latest]

    def minimum(self):
        while self.prices[self.low[0][1]] != self.low[0][0]:
            heapq.heappop(self.low)
        return self.low[0][0]

    def maximum(self):
        while self.prices[self.high[0][1]] != -self.high[0][0]:
            heapq.heappop(self.high)
        return -self.high[0][0]
```

## Complexity

After u updates, each push or pop costs O(log u); each historical heap entry is popped at most once per heap. Thus operations cost O(log u) amortized, though a single extrema query can discard many entries. Current is O(1). Space is O(u), not merely the number of distinct timestamps, because stale entries can remain buried indefinitely.

## Mistakes and edge cases

- Correcting an old timestamp must not change which timestamp is latest.
- Store timestamps in heap entries so validity can be checked.
- Both heaps need independent stale-entry cleanup.
- Querying before the first update is outside the contract.

## Variations

- Use a balanced multiset with explicit deletion to bound storage by live timestamps.
- Periodically rebuild both heaps from the dictionary to reclaim stale entries.

=== card | 460
time: 45 min

## The problem

Build a fixed-capacity key-value cache. A successful get and a put of an existing key both increase that key's use count. When inserting a new key into a full cache, evict a key with the smallest count; among tied keys, evict the one used least recently. New keys start with count one, and missing gets return -1.

## Constraints and what they imply

Keys and values are nonnegative, so -1 is reserved for misses. The capacity may be zero. Every successful use increases a count by exactly one, while insertion creates a count of one. This restricted movement lets us maintain the minimum without searching all counts. A missing get is not a use and cannot change the eviction order. Updating an existing value is a use even if the value is unchanged.

## Brute force

Store each key's value, count and last-use sequence number in a dictionary. On eviction scan every key and select the lexicographically smallest pair of count and last-use time. This model is straightforward and useful as an independent test oracle, but a full-cache insertion takes O(c) for capacity c. Alternatively a heap orders candidates in O(log c) time, but does not meet the constant-time goal.

## The insight

Group keys by frequency, and maintain each group in least-to-most-recent order with an `OrderedDict`. A second dictionary stores each key's value and current frequency. Keep the smallest live frequency in `min_freq`. Because a use moves from f to f + 1, there is no intermediate count to inspect. If the last key in the minimum bucket moves, its new bucket at f + 1 is nonempty and is necessarily the new minimum.

On insertion of a new key, use frequency one and set the minimum to one. If the cache is full, first remove the oldest key from the minimum bucket. We do not need to discover the next minimum after this removal: the immediately following insertion resets it to one. When capacity is zero, return before either step. Within a bucket, only the latest transition into that frequency matters for ordering, since each use moves a key to another bucket.

Initially all maps are empty. Each promotion removes a key from exactly its old bucket and appends it to its new one, updating its recorded frequency. Other keys keep their relative order. Insertion and eviction also preserve the one-bucket-per-key property. Therefore the oldest key in the minimum bucket is exactly the required victim, and successful operations restore every invariant.

The value itself is independent of the bucket position. A replacement changes that value first, then performs precisely the same promotion as a successful lookup. This keeps update and lookup semantics aligned even for repeated updates to the same key.

## Optimal solution, traced

```steps
Capacity 2; put (1, 10), put (2, 20)
    frequency 1, oldest to newest: [1, 2]
---
Get 1
    return {{10}}; bucket 1 is [2], bucket 2 is [1]
---
Put (3, 30)
    evict 2 from minimum bucket; insert 3 at frequency 1
---
Get 3, then put (4, 40)
    bucket 2 is [1, 3]; evict older 1, not 3
```

The order inside frequency two matters even though the two entries have equal counts.

## Code

```python
from collections import OrderedDict

class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}
        self.buckets = {}
        self.min_freq = 0

    def _touch(self, key):
        value, freq = self.entries[key]
        bucket = self.buckets[freq]
        del bucket[key]
        if not bucket:
            del self.buckets[freq]
            if self.min_freq == freq:
                self.min_freq = freq + 1
        new_freq = freq + 1
        self.buckets.setdefault(new_freq, OrderedDict())[key] = None
        self.entries[key] = (value, new_freq)

    def get(self, key):
        if key not in self.entries:
            return -1
        value = self.entries[key][0]
        self._touch(key)
        return value

    def put(self, key, value):
        if self.capacity == 0:
            return
        if key in self.entries:
            _, freq = self.entries[key]
            self.entries[key] = (value, freq)
            self._touch(key)
            return
        if len(self.entries) == self.capacity:
            bucket = self.buckets[self.min_freq]
            victim, _ = bucket.popitem(last=False)
            del self.entries[victim]
            if not bucket:
                del self.buckets[self.min_freq]
        self.entries[key] = (value, 1)
        self.buckets.setdefault(1, OrderedDict())[key] = None
        self.min_freq = 1
```

## Complexity

Each operation takes O(1) expected time using hash tables and constant-time ordered-dictionary moves and removals. Each live key is in one entry and one bucket, and empty buckets are deleted, so space is O(c). Python's unbounded integer counts grow in bit length after arbitrarily many operations; the usual complexity model treats these counters and hashes as machine-word operations.

## Mistakes and edge cases

- A put on an existing key promotes it rather than resetting its frequency.
- Emptying the minimum bucket during promotion differs from emptying it during eviction: insertion immediately resets the latter minimum.
- Ties require recency within each frequency, not globally oldest creation time.
- Capacity zero must not attempt eviction from an empty bucket.
- Delete empty buckets to avoid storage growing with past frequencies.

## Variations

- Store explicit linked-list nodes instead of relying on `OrderedDict`.
- Change eviction to pure LFU with arbitrary tie-breaking; bucket order then need not track recency.
- Add deletion, but update the minimum carefully because deletion can leave a gap in frequency.

=== card | 432
time: 45 min

## The problem

Maintain positive counts for string keys. Increment adds one, creating an absent key at one. Decrement subtracts one from an existing key and removes it when its count becomes zero. Return any key with the minimum or maximum count, or the empty string if no keys exist.

## Constraints and what they imply

Keys are nonempty strings, and decrements refer to present keys. Counts change by exactly one per update, so the destination count, if already present, must be next to the current count in sorted bucket order. Different keys may have the same count and any tied key is an acceptable answer. Scanning counts or sorting keys on every extremum query would miss the intended constant-time bound.

## Brute force

Maintain a dictionary of counts. Increment and decrement are expected O(1), but finding either extreme scans all k keys and costs O(k). This simple model is useful for testing because it independently specifies the valid set of answers, including ties.

## The insight

Maintain a doubly linked list of nonempty buckets ordered by increasing count. Each bucket holds its keys in an `OrderedDict`, and a map points each key directly to its bucket. Two sentinels mark the ends. For an increment, inspect the next bucket: it either represents count f + 1 or a new bucket with that count belongs immediately after the current bucket. Decrement is symmetric, except a count-one key disappears instead of moving to zero.

Creating an absent key is equivalent to moving from the head sentinel to count one. After moving a key, unlink an empty old bucket. The first and last real buckets contain exactly the minimum and maximum counts. Ordered dictionaries provide direct key removal and access to their first key without scanning a bucket; their internal order has no semantic importance here.

The proof is by induction over operations. Initially there are no real buckets and the map is empty. A unit change can skip no integer count between source and destination, so inspecting only the neighboring bucket finds the unique correct destination or position for a new one. Moving the key and deleting any empty source retains strictly increasing, nonempty buckets. The key map then points to its new bucket, or has no entry if the key was removed. Thus the endpoints always answer correctly, even after an extreme bucket vanishes.

This representation does not allocate buckets for missing counts. For example, counts one and ten may be adjacent in the list. An increment from one creates a count-two bucket in between; it must not move directly to count ten. The same reasoning applies in reverse for a decrement.

## Optimal solution, traced

```steps
Increment red twice and blue once
    buckets: 1:{blue} < 2:{red}
---
Increment blue
    move blue next to red; remove the empty bucket 1
    minimum and maximum may both return {{red}} or {{blue}}
---
Decrement red twice
    create bucket 1, then remove red completely
    only blue remains, at count {{2}}
```

Sentinels are not answer buckets and must never be returned as keys.

## Code

```python
from collections import OrderedDict

class _Bucket:
    def __init__(self, count):
        self.count = count
        self.keys = OrderedDict()
        self.prev = None
        self.next = None

class AllOne:
    def __init__(self):
        self.head = _Bucket(0)
        self.tail = _Bucket(0)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.where = {}

    def _after(self, node, count):
        new = _Bucket(count)
        new.prev, new.next = node, node.next
        node.next.prev = new
        node.next = new
        return new

    def _remove_empty(self, node):
        if not node.keys:
            node.prev.next = node.next
            node.next.prev = node.prev

    def inc(self, key):
        old = self.where.get(key)
        prev = old if old is not None else self.head
        count = old.count + 1 if old is not None else 1
        target = prev.next
        if target is self.tail or target.count != count:
            target = self._after(prev, count)
        target.keys[key] = None
        self.where[key] = target
        if old is not None:
            del old.keys[key]
            self._remove_empty(old)

    def dec(self, key):
        old = self.where[key]
        if old.count == 1:
            del self.where[key]
        else:
            target = old.prev
            if target is self.head or target.count != old.count - 1:
                target = self._after(old.prev, old.count - 1)
            target.keys[key] = None
            self.where[key] = target
        del old.keys[key]
        self._remove_empty(old)

    def getMaxKey(self):
        node = self.tail.prev
        return "" if node is self.head else next(iter(node.keys))

    def getMinKey(self):
        node = self.head.next
        return "" if node is self.tail else next(iter(node.keys))
```

## Complexity

Each operation is O(1) expected time under constant-time hashing and ordered-dictionary operations, with fixed-size keys and count arithmetic. There are at most k nonempty buckets for k live keys, so space is O(k). If key length is unbounded, hashing and comparing strings also costs time in their lengths. Unbounded Python integer counts likewise have nonconstant bit-operation cost.

## Mistakes and edge cases

- Returning a particular tied key is not required, and tests must allow all tied extrema.
- Removing the final key of a bucket must reconnect both neighboring links.
- A decrement to zero deletes the key instead of creating a zero bucket.
- Empty structure queries return the empty string, not a sentinel key.
- Non-unit count changes cannot use this neighbor-only method unchanged.

## Variations

- Return the extreme count along with a representative key.
- Return all tied keys, paying time proportional to the output size.
- Allow arbitrary count jumps with a sorted tree, accepting logarithmic updates.

=== card | 381
time: 45 min

## The problem

Design a collection that permits repeated integer values. Insertion returns whether the value was previously absent; removal deletes one occurrence and returns whether one existed. A random operation returns an occurrence uniformly, so a value appearing twice is twice as likely as a value appearing once.

## Constraints and what they imply

Values may be negative, zero or positive. Random selection is requested only when the collection is nonempty. The collection has no order requirement. A value can occupy several positions, so a single value-to-index mapping is insufficient. Every live occurrence must remain represented, including when a removal and the array's last slot hold equal values.

## Brute force

Store occurrences in a list. Append on insertion and use a random index for sampling, but scan to decide whether a value was present and to find an occurrence to remove. Removing from the middle also shifts a suffix. These operations can take O(n) time for n occurrences, although the list correctly weights random results by multiplicity.

## The insight

Keep a dense occurrence array and a dictionary from each value to a set of all indices containing it. Insertion adds the new last index to the appropriate set. To remove an occurrence, take any one of its indices i, move the last value into position i, change the moved value's index set from the old last position to i, and pop the last array entry.

The ordering of updates matters when both values are equal. First remove i from the requested value's set; if i is not the last position, remove the old last index from the last value's set and add i. These operations work even when both sets are the same object. If i is already the last position, no relocation is necessary. Delete a dictionary entry once its set becomes empty. Each occupied position then appears in exactly one index set, namely the set for its array value.

Inductively, insertion establishes this invariant for one new index. Deletion removes the selected occurrence; if another occurrence moves, replacing its index restores the invariant for that one position and no other indices change. Because each occurrence occupies exactly one array slot, choosing a uniform slot returns a value with probability equal to its count divided by the total number of occurrences. Repeated insertions therefore affect probability rather than being silently coalesced.

The set of positions need not be sorted: the identity of the removed occurrence is unobservable. This freedom lets the implementation take an arbitrary position without searching. Tests can inspect all slots directly rather than rely on a probabilistic frequency test that might occasionally fail despite a correct implementation.

## Optimal solution, traced

```steps
Insert 5, 5, 8
    array [5, 5, 8]; positions 5:{0,1}, 8:{2}
---
Remove the occurrence of 5 at index 0
    move 8 from 2 to 0; array [8, 5]
    positions 8:{0}, 5:{1}
---
Insert 5
    three slots contain [8, 5, 5]
    probability of 5 is {{2/3}}
```

The actual removal may choose another index for 5; either choice preserves the same multiset.

## Code

```python
import random

class RandomizedCollection:
    def __init__(self):
        self.values = []
        self.indices = {}

    def insert(self, val):
        fresh = val not in self.indices
        self.indices.setdefault(val, set()).add(len(self.values))
        self.values.append(val)
        return fresh

    def remove(self, val):
        if val not in self.indices:
            return False
        i = self.indices[val].pop()
        last_index = len(self.values) - 1
        last = self.values[last_index]
        if i != last_index:
            self.values[i] = last
            self.indices[last].remove(last_index)
            self.indices[last].add(i)
        self.values.pop()
        if not self.indices[val]:
            del self.indices[val]
        return True

    def getRandom(self):
        return random.choice(self.values)
```

## Complexity

Insert and remove take O(1) expected amortized time, assuming expected constant-time dictionary and set operations and amortized array append. Random selection is O(1) with a uniform array-index choice. Space is O(n) for n live occurrences, including the index sets. As with ordinary Python hash tables, adversarial collisions can worsen the expected bound.

## Mistakes and edge cases

- When the removed and last values agree, their index sets are the same set; do not delete the mapping before relocation finishes.
- When removing the last slot itself, do not remove its index twice.
- Remove an empty index set so the next insertion correctly reports that the value was absent.
- Sampling distinct keys uniformly would produce the wrong distribution.
- A random query on an empty collection is outside the stated contract.

## Variations

- Maintain a distinct-value set and sample unique values uniformly instead.
- Add a count operation returning the size of the value's index set.
- Support weighted sampling for arbitrary weights using a different cumulative-weight structure.

=== card | 2276
time: 45 min

## The problem

Start with no covered integers. Repeatedly add a closed integer interval and report how many distinct integers are covered by at least one interval so far. Overlap and repeated additions must not be counted twice.

## Constraints and what they imply

Each added interval has 1 <= left <= right <= 1,000,000,000. The domain is much too large to allocate one flag per integer. Additions only increase coverage; there is no removal. The inclusive length of a covered interval is right - left + 1. Count queries may occur between arbitrary additions, so the total must remain ready after every update.

## Brute force

Insert every integer from left through right into a set, and return its size. This is easy to reason about for small domains but an interval can contain a billion integers. Another model stores all intervals and sorts and merges them whenever asked; that avoids per-integer storage but repeats work across queries and can take O(m log m) after m additions.

## The insight

Use an implicit segment tree for the fixed domain. Each node represents an inclusive interval and stores the number of covered integers in that interval. Its children are created only when an update partially overlaps it. A fully covered node needs no further work: all future additions leave its answer unchanged. If an update fully contains a node's range, mark its count as the range length and discard any children because their details can no longer change the answer.

On partial overlap, split the range at its midpoint, update only intersecting halves, and set the node's count to the sum of its children's counts, treating missing children as zero. The root count is therefore the desired distinct total. The recursion stops at full coverage or a leaf; an intersecting leaf is always fully covered by an integer-bounded update. The implementation uses a count equal to range length as the full-coverage marker, avoiding a separate flag.

Initially the root count is zero. For a fully covered update, assigning the segment length counts each integer exactly once. For a partial update, the disjoint child ranges partition the parent, so summing their correct counts gives the correct parent count. By induction on tree height, the root is correct after every addition. A node already full can return immediately because additions never uncover any integer.

## Optimal solution, traced

```steps
Add [2, 4]
    root count becomes 3
---
Add [4, 6]
    integer 4 was already covered; root count becomes {{5}}
---
Add [2, 6] again
    every covered segment is already full; count remains {{5}}
```

The example shows the logical coverage; the actual tree partitions the entire billion-element domain, not only the displayed numbers.

## Code

```python
class _Node:
    def __init__(self):
        self.count = 0
        self.left = None
        self.right = None

class CountIntervals:
    def __init__(self):
        self.root = _Node()
        self.limit = 1_000_000_000

    def add(self, left, right):
        def update(node, lo, hi):
            if node.count == hi - lo + 1:
                return
            if left <= lo and hi <= right:
                node.count = hi - lo + 1
                node.left = node.right = None
                return
            mid = (lo + hi) // 2
            if left <= mid:
                if node.left is None:
                    node.left = _Node()
                update(node.left, lo, mid)
            if right > mid:
                if node.right is None:
                    node.right = _Node()
                update(node.right, mid + 1, hi)
            node.count = ((node.left.count if node.left else 0) +
                          (node.right.count if node.right else 0))

        update(self.root, 1, self.limit)

    def count(self):
        return self.root.count
```

## Complexity

Let U be the domain size and m the number of additions. At each tree depth at most two nodes are partially intersected; their fully covered siblings need no descent. An add therefore visits O(log U) nodes and takes O(log U) time in the usual unit-cost model; count takes O(1). The tree uses O(m log U) space in the worst case, with O(log U) recursion depth. Fully covered nodes discard descendants, which can require time proportional to the discarded subtree's size for reference-counting garbage collection. Thus in Python the strict per-call bound includes this cleanup; over all updates, total cleanup is bounded by the total number of nodes created, giving O(log U) amortized update time.

## Mistakes and edge cases

- Closed intervals include both endpoints; a singleton has length one.
- An overlap must not be added directly to the existing count.
- A full node cannot need descendants for future add-only operations.
- Updates outside the domain or with left greater than right are outside the contract.
- Supporting removals would invalidate the shortcut that discards covered descendants.

## Variations

- Use sorted disjoint intervals and a running total; account for the cost of list shifts.
- Coordinate-compress known endpoints offline to reduce the tree domain.
- Support removals with coverage counters and retained descendant information.
