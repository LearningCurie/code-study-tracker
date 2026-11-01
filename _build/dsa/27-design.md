---
key: design
name: Designing data structures
stage: engineer
summary: Turn a list of operations and target costs into a small composition of structures whose invariants stay in sync, then prove it with a model-based test.
why: "Implement a class that supports these operations in O(1)" is one of the most common interview formats, and it is also everyday engineering: a cache in front of a database, a per-client rate limiter, a versioned settings store, an iterator over paged API results. Each built-in container makes one or two operations fast; real requirements want three or four at once. This module teaches the move that solves all of them: write the operations and costs first, give each hard operation its own index, write down the invariant that ties the indexes together, and test the result against a slow but obviously correct model.
outcomes:
- Turn a feature request into an operations table with target costs, then choose and combine structures to meet it
- Build an O(1) LRU cache from a hash map and a doubly linked list, and an O(1) LFU cache from frequency buckets
- Augment stacks, queues and arrays with extra state (running minimum, maximum, index maps, totals) that stays correct after every operation
- Store values that change over time as per-key histories searched with bisect, and keep derived indexes honest with lazy validation
- Implement hit counters and rate limiters (sliding log, fixed window, sliding counter, token bucket) and state exactly what each guarantees
- Write lazy iterators and generators whose has_next and peek can be called any number of times
- Test any stateful structure with random operation sequences against a reference model, including Hypothesis state machines that shrink failures
cues:
- "Design a class" or "implement an object" with several methods and a stated cost such as O(1) average for each
- The same data must be reached two ways: by key, and by some order (recency, frequency, time, rank, position)
- Words such as evict, expire, most recent, in the last N seconds, at time t, snapshot, undo, peek
- A random element, a minimum or a maximum must be reported while elements come and go
traps:
- Updating one index but not the other: the dict still points at a node you unlinked, or the minimum-frequency pointer is stale
- Forgetting that a put on an existing key is also a use, so it must refresh recency or frequency
- Off-by-one window boundaries (is a hit exactly 3000 ms ago inside the window?) and fixed windows that let through twice the limit at a boundary
- A has_next that advances the underlying iterator, so calling it twice loses an element
- Trusting a few hand-written examples instead of thousands of random operation sequences checked against a model
systems:
- CPython's functools.lru_cache keeps a dict from key to link plus a circular doubly linked list with a root sentinel; the C version used at run time mirrors the pure-Python one in Lib/functools.py
- collections.OrderedDict is a dict plus a doubly linked list of keys, which is why move_to_end and popitem(last=False) are O(1) and why the docs recommend it for LRU caches
- Redis does not keep an LRU list at all: it samples maxmemory-samples keys (default 5) and evicts the best candidate, and its LFU mode uses a small probabilistic (Morris) counter that decays over time
- NGINX's limit_req module limits request rates with the leaky bucket method; per-client token buckets are the other common choice in API gateways
further:
- Docs · 15 min | Hypothesis: rule-based state machines, preconditions and invariants | https://hypothesis.readthedocs.io/en/latest/stateful.html#rule-based-state-machines
- Source · 10 min | CPython 3.14 functools.py: the pure-Python lru_cache wrapper (lines 600-700) | https://github.com/python/cpython/blob/v3.14.0/Lib/functools.py#L600-L700
- Docs · 5 min | Python docs: OrderedDict examples and recipes (LRU caches with move_to_end) | https://docs.python.org/3/library/collections.html#ordereddict-examples-and-recipes
- Docs · 10 min | Redis: approximated LRU and LFU eviction | https://redis.io/docs/latest/develop/reference/eviction/#apx-lru
bank: design
---

=== primer | How do you design a data structure from the operations it must support? | 15 min
goal: Turn a list of operations with target costs into fields, one invariant that ties them together, and methods that keep it true
tag: design-compose | Operations first, then compose structures
link: Python docs: time complexity of built-in types | https://docs.python.org/3/builtins/time-complexity.html#list | 10 min: the list, dict and set tables are the menu you compose from; note which costs are amortised and which are average case
practice: 705, 1396

> [!key]
> Start from the interface, not from a structure. List every operation with its target cost, then give each operation that must be fast its own index: a dict for "find by key", a list for "pick by position", a heap or linked list for "the next one in some order". Write one invariant that says how the indexes agree, make every method restore it, and test against a slow model.

## Intuition

Think of a small library. The catalogue finds a book by title, the shelves keep books in call-number order so you can browse a range, and the returns trolley holds the most recently returned books on top. Same books, three indexes, each answering a different question quickly. The librarian's real job is bookkeeping: when a book moves, every index that mentions it must be updated, or the catalogue sends readers to an empty shelf.

Data structure design problems are exactly this. No single container answers every question fast, so you keep several, each specialised, and the difficulty moves from algorithms to keeping them consistent.

## How it works

### Step 1: write the operations table

Take a transit system that records check-ins and check-outs and reports the average trip time between two stations (LeetCode 1396). Before choosing anything, write what each operation must find and how fast:

| Operation | Must find quickly | Target |
|---|---|---|
| check_in(rider, station, t) | nothing: record where and when the rider entered | O(1) |
| check_out(rider, station, t) | the rider's open trip | O(1) |
| average(start, end) | the total time and trip count for that pair | O(1) |

### Step 2: store only what the answers need

The average needs a sum and a count per station pair, not the list of trips. An open trip needs only (station, time) per rider. So two dicts: `open_trips: rider -> (station, t)` and `totals: (start, end) -> [total_time, trips]`. Storing every finished trip would also work, but `average` would then cost O(trips) unless you added a running sum anyway.

### Step 3: write the invariant

*At every moment, `open_trips` holds exactly the riders who have checked in and not out, and `totals[(a, b)]` holds the sum and count of every finished trip from a to b.* Each method must leave this sentence true.

### Step 4: implement each method to restore the invariant

`check_in` adds one entry; `check_out` removes the rider's entry and adds one trip to one pair; `average` reads. Each touches a constant number of dict entries.

### The toolbox

| You need | Use | Cost in CPython |
|---|---|---|
| Find, insert or delete by key | `dict`, `set` | O(1) average |
| Pick by position, a uniformly random element | `list` | O(1) index; O(1) amortised append and pop at the end |
| First in, first out | `collections.deque` | O(1) at both ends |
| Repeatedly take the smallest | `heapq` on a list | O(log n) push and pop |
| Sorted order, floor and ceiling | sorted list plus `bisect` | O(log n) search, O(n) insert |
| Move an item to the end, given a handle to it | doubly linked list, `OrderedDict.move_to_end` | O(1) |

Every design in this module is two or three rows of this table glued together by an invariant.

## Cost

Each `UndergroundSystem` method performs at most two dict lookups and one insert or delete, each O(1) on average, so every operation is **O(1) average**. Space is O(R + P): R riders currently inside the system plus P distinct station pairs ever travelled, independent of how many trips were taken.

For LeetCode 705 (a hash set without built-in hash tables) with m buckets and n keys, a hash that spreads keys evenly gives chains of expected length n/m, so `add`, `remove` and `contains` cost O(1 + n/m) expected. With keys limited to 0..10^6 you can also use a `bytearray` of 10^6 + 1 flags: 1 MB and O(1) worst case, but only because the key range is small.

## When to use it

Reach for this process whenever a statement says "design", "implement a class" or lists several methods with costs. The cue is two different access patterns on the same data (by key and by order), which no single container serves.

Decide early what to keep. Aggregates (sum and count) are small and fast but can only answer the questions you planned for: from a sum and a count you can never recover the median trip time. Raw events answer future questions but cost memory and query time.

| Keep | Memory | `average` | Can later answer the median? |
|---|---|---|---|
| Sum and count per pair | O(P) | O(1) | No |
| Every trip, per pair | O(trips) | O(1) with a running sum | Yes, by sorting or two heaps |

Do not hand-roll a hash set in production code; `set` is faster and better tested. Problems like 705 forbid built-ins precisely so that you practise the mechanics.

## Worked trace

Two riders travel from Oak to Elm. Watch both dicts change:

```steps
check_in(7, "Oak", 2): rider 7 opens a trip
    open_trips  {{7: ("Oak", 2)}}
    totals      {}
---
check_in(9, "Oak", 4): a second open trip; nothing is finished yet
    open_trips  7: ("Oak", 2)   {{9: ("Oak", 4)}}
    totals      {}
---
check_out(7, "Elm", 12): pop rider 7, add 12 - 2 = 10 to the Oak-Elm pair
    open_trips  9: ("Oak", 4)
    totals      {{("Oak", "Elm"): [10, 1]}}
---
check_out(9, "Elm", 18): pop rider 9, add 18 - 4 = 14
    open_trips  {}
    totals      ("Oak", "Elm"): {{[24, 2]}}
---
average("Oak", "Elm") reads one entry: 24 / 2 = 12.0
    totals      ("Oak", "Elm"): [{{24}}, {{2}}]   ->  12.0
```

## Template

Write the operations and the invariant in the docstring before any method; then each method is a few lines. LeetCode names the methods `checkIn`, `checkOut` and `getAverageTime`.

```python
class UndergroundSystem:
    """Average trip time between two stations.

    Invariants: open_trips holds exactly the riders who checked in and have not checked out;
    totals[(a, b)] == [sum of finished trip times from a to b, number of those trips].
    """

    def __init__(self):
        self.open_trips = {}   # rider -> (start station, check-in time)
        self.totals = {}       # (start, end) -> [total time, trips]

    def check_in(self, rider, station, t):
        self.open_trips[rider] = (station, t)

    def check_out(self, rider, station, t):
        start, t0 = self.open_trips.pop(rider)
        rec = self.totals.setdefault((start, station), [0, 0])
        rec[0] += t - t0
        rec[1] += 1

    def average(self, start, end):
        total, trips = self.totals[(start, end)]
        return total / trips
```

The same habit applied to a hash set with chaining (bucket i holds the keys with `key % size == i`):

```python
class MyHashSet:
    def __init__(self, size=1024):
        self.size = size
        self.buckets = [[] for _ in range(size)]

    def add(self, key):
        b = self.buckets[key % self.size]
        if key not in b:
            b.append(key)

    def remove(self, key):
        b = self.buckets[key % self.size]
        if key in b:
            b.remove(key)

    def contains(self, key):
        return key in self.buckets[key % self.size]
```

## Pitfalls

- **Storing too much.** Keeping every trip makes `average` O(trips) unless you also keep a running sum, at which point the list is dead weight.
- **Ambiguous composite keys.** `start + end` as a string key confuses "AB" + "C" with "A" + "BC". Use the tuple `(start, end)`.
- **Integer division.** In Python `total / trips` is a float; in Java or C++ cast before dividing.
- **Bucket counts that share a factor with the keys.** With 1000 buckets and keys that are multiples of 1000, every key lands in bucket 0 and each operation becomes O(n). A prime bucket count such as 1009, or a mixing hash, spreads them.
- **Undefined calls.** Decide what `check_out` does for a rider who never checked in; LeetCode promises it never happens, production code must raise a clear error.

## Check yourself

Q: Run check_in(4, "X", 1), check_in(5, "X", 2), check_out(4, "Y", 6), check_in(4, "Y", 7), check_out(5, "Y", 12), check_out(4, "X", 20). What are `totals`, average("X", "Y") and average("Y", "X")?
A: totals is {("X", "Y"): [15, 2], ("Y", "X"): [13, 1]}. Rider 4 took 5 units from X to Y and rider 5 took 10, so the X-to-Y average is 7.5; rider 4's second trip from Y to X took 13, so that average is 13.0. open_trips ends empty.

Q: Your manager now wants the median trip time per pair. Why can the current design not answer it, and what would you store instead?
A: A sum and a count discard the distribution, so the median is unrecoverable. Keep the trip times per pair: either a list sorted on demand (O(k log k) per query), or two heaps per pair (a max-heap of the lower half and a min-heap of the upper half), which gives O(log k) inserts and an O(1) median.

Q: A colleague's hash set uses 1000 buckets and stores order ids that are all multiples of 1000. Their benchmark shows O(n) behaviour. Why, and what is the smallest fix?
A: `key % 1000` is 0 for every key, so all n keys share one chain and each operation scans it (in a test with 50 such keys the longest chain was 50). Use a prime number of buckets such as 1009, which spreads multiples of 1000 evenly (longest chain 1 in the same test), or mix the key's bits before taking the remainder.

## Lab

- **705 Design HashSet.** Implement it with buckets and no built-in `set` or `dict`. Expected: O(1 + n/m) per operation; with 1024 buckets, `add(3)` then `add(1027)` puts both in bucket 3 as `[3, 1027]`; after `remove(3)`, `contains(3)` is False and `contains(1027)` is still True.
- **1396 Design Underground System.** Write the operations table and the invariant first, then the code. Expected: O(1) per call; after check_in(1, "A", 3), check_out(1, "B", 8), check_in(2, "A", 10), check_out(2, "B", 22), getAverageTime("A", "B") returns 8.5.

> [!know]
> You now know how to turn a list of operations and costs into fields, an invariant and methods, and how to choose what to store.

=== primer | How do you design an LRU cache with O(1) get and put? | 16 min
goal: Build a least-recently-used cache from a dict and a doubly linked list with a sentinel, explain why each piece is needed, and know when OrderedDict or functools.lru_cache is the better choice
tag: design-lru | Hash map plus doubly linked list (LRU)
link: CPython 3.14 source: functools.py | https://github.com/python/cpython/blob/v3.14.0/Lib/functools.py#L600-L700 | 10 min: read _lru_cache_wrapper, where links are 4-slot lists [PREV, NEXT, KEY, RESULT] around a root sentinel, and see how a full cache reuses the old root as the new link instead of allocating
link: Python docs: OrderedDict | https://docs.python.org/3/library/collections.html#ordereddict-objects | 5 min: why OrderedDict is designed for frequent reordering, then move_to_end and popitem(last=False)
practice: 146

> [!key]
> An LRU cache needs two things fast: find an entry by key, and know which entry was used least recently. A dict answers the first; a doubly linked list kept in recency order answers the second, because a node can be unlinked in O(1) once the dict hands it to you. Every get or put moves the node to the front; eviction removes the node at the back.

## Intuition

Picture a desk with room for three folders. Whenever you use a folder you put it on top of the pile. When a fourth folder arrives and the desk is full, the folder at the bottom goes back to the cabinet: it is the one you have gone longest without touching. You also keep an index card per folder saying where it is in the pile, so you can pull it out without digging.

The pile is the linked list, the index cards are the dict, and "pull it out and put it on top" is unlink plus push to the front.

## How it works

### Why one structure is not enough

- A **dict** alone finds a key in O(1), but has no cheap way to say "move this key to the most recent end" and "remove the oldest" together with a guarantee.
- A **list** in recency order knows the oldest (the end), but finding a key and moving it from the middle costs O(n).
- A **doubly linked list** can move a node in O(1), but only if you already hold the node. The dict supplies exactly that: `key -> node`.

### The layout

```text
          most recent                                least recent
root <-> [c:3] <-> [a:1] <-> [b:2] <-> root        (circular: root.prev is the LRU node)

map: {"a": node_a, "b": node_b, "c": node_c}
```

One **sentinel** node, `root`, sits between the two ends of a circular list. `root.next` is the most recently used node and `root.prev` the least recently used. Because the sentinel is always there, inserting into an empty list, removing the only node, or removing the tail never needs a special case.

### The operations

- `get(key)`: look the node up in the dict; on a miss return -1. On a hit, **unlink** it (`node.prev.next = node.next; node.next.prev = node.prev`) and **push it to the front** (between root and root.next).
- `put(key, value)`: if the key exists, update the value and move the node to the front (a put is a use). Otherwise, if the cache is full, take `root.prev`, unlink it and delete its key from the dict; then create a node, store it in the dict and push it to the front.

The node stores its own **key** for one reason: on eviction you hold the node, and you need its key to delete the dict entry.

### The invariant

*The dict and the list contain exactly the same keys, at most `capacity` of them, and the list order from `root.next` to `root.prev` is the order of last use, newest first.* Every method above restores it before returning.

## Cost

`get` does one dict lookup (O(1) average) and a constant number of pointer assignments: **O(1)**. `put` adds at most one eviction (one unlink, one dict delete) and one insertion: **O(1)**. Space is O(capacity): one node per entry (64 bytes for a node with four `__slots__` fields on 64-bit CPython 3.12) plus one dict entry.

Measured on a 200,000-request skewed trace with capacity 1000 (the lab below), a hand-written linked-list version took about 1.5 µs per request, an `OrderedDict` version about 0.5 µs, and `functools.lru_cache` about 0.4 µs. Same complexity; the built-ins win because their linked lists are in C.

## When to use it

Use LRU when **recency predicts reuse** (temporal locality): user sessions, recently viewed pages, decoded images, database pages. Its weakness is a **scan**: one pass over many keys that will never be used again pushes every hot entry out. If a few keys stay popular for a long time, frequency-based eviction (the next card) keeps them better.

| Option | When |
|---|---|
| `@functools.lru_cache(maxsize=n)` | Memoising a pure function in Python; thread-safe, in C, with `cache_info()` |
| `OrderedDict` with `move_to_end` and `popitem(last=False)` | You need a cache object with your own API (TTL, delete, size in bytes) |
| Hand-written dict plus linked list | Interviews, other languages, or when you need hooks on every move |
| Approximations | Very large caches where a list per entry costs too much memory: Redis samples 5 keys and evicts the oldest of the sample |

Newer policies such as SIEVE, S3-FIFO and TinyLFU admission are covered in the caching module later in the guide.

## Worked trace

Capacity 3. The list is shown most recent first; the dict always holds the same keys.

```steps
put(a, 1), put(b, 2), put(c, 3): three misses, each pushed to the front
    list  root <-> {{c}} <-> b <-> a <-> root
    map   a, b, c
---
get(a) = 1: hit, so unlink a and push it to the front
    list  root <-> {{a}} <-> c <-> b <-> root
    map   a, b, c
---
put(d, 4): full, so evict root.prev = b (its node tells us the key to delete), then push d
    list  root <-> {{d}} <-> a <-> c <-> root
    map   a, c, d        ({{b}} deleted)
---
get(b) = -1: a miss changes nothing
    list  root <-> d <-> a <-> c <-> root
---
put(c, 30): c exists, so update the value and move it to the front; nothing is evicted
    list  root <-> {{c}} <-> d <-> a <-> root
---
put(e, 5): full again; the least recent is now a
    list  root <-> {{e}} <-> c <-> d <-> root
    map   c, d, e        ({{a}} deleted)
---
get(d) = 4: hit, move to front
    list  root <-> {{d}} <-> e <-> c <-> root
```

## Template

```python
class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = self.next = self


class LRUCache:
    """dict key -> node, plus a circular doubly linked list with one sentinel.
    root.next is the most recently used node, root.prev the least recently used."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}
        self.root = _Node()

    def _unlink(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _push_front(self, node):
        node.prev, node.next = self.root, self.root.next
        self.root.next.prev = node
        self.root.next = node

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return -1
        self._unlink(node)
        self._push_front(node)
        return node.value

    def put(self, key, value):
        node = self.map.get(key)
        if node is not None:
            node.value = value
            self._unlink(node)
            self._push_front(node)
            return
        if len(self.map) == self.capacity:
            lru = self.root.prev
            self._unlink(lru)
            del self.map[lru.key]
        node = _Node(key, value)
        self.map[key] = node
        self._push_front(node)
```

The same behaviour with the standard library, which is what you would ship in Python:

```python
from collections import OrderedDict


class OrderedLRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.od = OrderedDict()            # oldest first, newest last

    def get(self, key):
        if key not in self.od:
            return -1
        self.od.move_to_end(key)
        return self.od[key]

    def put(self, key, value):
        if key in self.od:
            self.od.move_to_end(key)
        elif len(self.od) == self.capacity:
            self.od.popitem(last=False)
        self.od[key] = value
```

## Pitfalls

- **A put on an existing key is a use.** Updating the value without moving the node leaves it near the back, so it is evicted too early. Random tests with capacity 2 or more catch this; capacity 1 never does.
- **Evicting before checking whether the key exists.** A full cache that receives `put` for a key it already holds must not evict anything.
- **Forgetting the dict on eviction.** Unlinking the tail but leaving `map[key]` behind makes `len(map)` grow past capacity and later `get` calls return evicted values.
- **Singly linked lists.** Unlinking needs the predecessor; without `prev` you would have to search for it in O(n).
- **Threads.** The pointer updates are several statements; `functools.lru_cache` holds a lock around them, and so must any shared cache of your own.

## Check yourself

Q: Capacity 2. Run put(1, 1), put(2, 2), get(1), put(3, 3), get(2), put(1, 10), put(4, 4). What does get(2) return, which keys remain, and in what recency order?
A: get(2) returns -1, because put(3, 3) evicted 2 (get(1) had made 1 more recent). put(1, 10) updates 1 and moves it to the front, so put(4, 4) evicts 3. The cache holds 4 then 1 (newest first), with 1 mapped to 10.

Q: Why must the list be doubly linked, and why does each node store its key?
A: Unlinking a node in O(1) needs both neighbours: `prev` to repoint its next pointer and `next` to repoint its prev pointer. A singly linked list would need an O(n) search for the predecessor. The key is stored because eviction starts from the node at `root.prev`, and the only way to delete its dict entry is to know its key.

Q: A teammate's `put` begins with "if the cache is full, evict root.prev", then handles the existing-key case. With capacity 2, what does put("a", 1), put("b", 2), put("b", 9), get("a") return, and what should it return?
A: It returns -1: the third call evicts "a" even though "b" was already present and nothing needed to go. The correct cache returns 1. Check for an existing key first; evict only when inserting a new key into a full cache.

Q: You need to memoise an expensive pure function of two integers in Python. Do you write your own LRU class?
A: No. `@functools.lru_cache(maxsize=...)` is implemented in C, is thread-safe, and reports hits and misses through `cache_info()`. Write your own class only when you need behaviour the decorator lacks, such as expiry times, explicit deletes or a size limit in bytes.

## Lab

- **146 LRU Cache.** Implement the dict plus doubly linked list version (no OrderedDict) and then the OrderedDict version. Expected: O(1) per call; with capacity 2, the calls put(5, 50), get(5), put(6, 60), put(5, 55), put(7, 70), get(6), get(5), put(8, 80), get(7), get(8) return 50, -1, 55, -1, 80 for the gets, and the cache ends holding 8 then 5.

> [!know]
> You now know how to combine a dict with a sentinel-based doubly linked list to get O(1) LRU get and put, and when to use OrderedDict or functools.lru_cache instead.

=== primer | How do you build an LFU cache where every operation is O(1)? | 16 min
goal: Implement least-frequently-used eviction with ties broken by recency in O(1) per operation using frequency buckets and a minimum-frequency pointer, and explain why the pointer never needs a search
tag: design-lfu | Frequency buckets with a minimum pointer (LFU)
link: Wikipedia: cache replacement policies, LFU with dynamic aging | https://en.wikipedia.org/wiki/Cache_replacement_policies#LFU_with_dynamic_aging_(LFUDA) | 5 min: the LFUDA section, on how a cache-age factor stops formerly popular items from polluting an LFU cache
link: Redis docs: LFU eviction | https://redis.io/docs/latest/develop/reference/eviction/#lfu-eviction | 5 min: how Redis approximates LFU with a few-bit Morris counter that decays every minute, and the lfu-log-factor table
practice: 460, 432

> [!key]
> Group keys into **buckets by use count**, each bucket ordered by recency, and remember the smallest non-empty count in `min_freq`. A use moves a key from bucket f to bucket f + 1, an eviction pops the oldest key of bucket `min_freq`, and a new key always starts at count 1. Because counts only ever change by one, `min_freq` can be maintained without searching.

## Intuition

A corner shop with one small display shelf keeps the snacks that sell most often. When a new product arrives and the shelf is full, the shopkeeper removes the product with the fewest sales so far; if two products are tied, the one that sold least recently goes. To do that instantly, the shopkeeper keeps the products sorted into trays labelled "sold once", "sold twice", and so on, with each tray in the order of the last sale.

Every sale moves a product to the next tray up. The cheapest product to throw out is always the oldest one in the lowest non-empty tray.

## How it works

### The naive version and its cost

Store `(count, last_used, key)` in a min-heap and pop the smallest. Each use changes a key's count, which leaves a stale heap entry behind, so you need lazy deletion and every operation costs O(log n). The task asks for O(1).

### The O(1) layout

```text
value:   {x: 1, y: 2, z: 3}          key -> value
count:   {x: 3, y: 2, z: 1}          key -> number of uses
buckets: 1: [z]   2: [y]   3: [x]    count -> keys, oldest use first (OrderedDict)
min_freq = 1                         smallest count that has a non-empty bucket
```

- `get(key)`: on a hit, **touch** the key: remove it from bucket f, append it to bucket f + 1, and if bucket f became empty and f was `min_freq`, set `min_freq = f + 1`.
- `put(key, value)` for an existing key: update the value and touch it (a put is a use).
- `put` for a new key into a full cache: pop the oldest key of bucket `min_freq` (`popitem(last=False)`), delete it from both dicts, then insert the new key into bucket 1 and set `min_freq = 1`.

### Why min_freq never needs a search

The invariant: *bucket f holds exactly the keys used f times, in order of last use, and when the cache is not empty `min_freq` is the smallest f with a non-empty bucket.* Only two events can change the minimum:

1. **A new key arrives.** It has count 1, and no count is smaller, so `min_freq = 1`.
2. **A touch empties the minimum bucket.** The key just moved from f to f + 1, so bucket f + 1 is non-empty and nothing lies between f and f + 1. The new minimum is exactly f + 1.

Eviction can also empty the minimum bucket, but eviction is always followed by inserting a new key, which sets the minimum to 1 anyway.

### All O`one: the same insight with decrements

LeetCode 432 lets counts go **down** as well as up and asks for any key with the maximum or the minimum count. Counts still change by exactly one, so a key moves only to a neighbouring bucket. Keep the buckets themselves in a doubly linked list sorted by count, with head and tail sentinels; `key -> bucket` finds a key's bucket, a missing neighbour bucket is created next to it, and an empty bucket is unlinked. The minimum is `head.next`, the maximum is `tail.prev`, both O(1).

## Cost

Every step is a dict or OrderedDict operation: lookup, delete, append at the end, or `popitem(last=False)`, each O(1) (average for the hashing). `get` and `put` therefore cost **O(1)**. Space is O(capacity) for the keys plus at most one bucket per distinct count in use, which is also O(capacity).

## When to use it

LFU suits workloads whose popular items **stay popular**: a fixed catalogue of product images, DNS names, configuration blobs. It resists one-off scans better than LRU, because a scanned key reaches only count 1 and is the first to go.

Its weaknesses: a key that was popular yesterday keeps its high count forever (**cache pollution**), and a brand-new key, at count 1, is always the first victim even if it is about to become popular. Production systems fix both with decay and approximation: Redis's LFU mode keeps a probabilistic Morris counter of a few bits per key, saturating at around a million hits by default, and halves it with time (`lfu-decay-time`, default one minute).

| | LRU | Exact LFU (buckets) | Heap-based LFU |
|---|---|---|---|
| Per operation | O(1) | O(1) | O(log n) |
| Survives a one-off scan | No | Yes | Yes |
| Adapts to shifting popularity | Quickly | Slowly, unless counts decay | Slowly |
| Extra state per key | Two pointers | A count, a bucket slot | A count, heap entries |

## Worked trace

Capacity 2. Buckets are shown as `count: [keys, oldest first]`.

```steps
put(a, 1), put(b, 2): both new, both in bucket 1; a is older
    buckets  1: [a, {{b}}]
    min_freq {{1}}
---
get(a) = 1: a moves from bucket 1 to bucket 2; bucket 1 still holds b, so min_freq stays 1
    buckets  1: [b]   2: [{{a}}]
    min_freq 1
---
put(c, 3): full, so evict the oldest key in bucket min_freq = 1, which is b; c enters bucket 1
    buckets  1: [{{c}}]   2: [a]        ({{b}} evicted)
    min_freq 1
---
get(b) = -1: b is gone; nothing changes
    buckets  1: [c]   2: [a]
---
get(c) = 3: c moves to bucket 2, bucket 1 empties and it was the minimum, so min_freq = 2
    buckets  2: [a, {{c}}]
    min_freq {{2}}
---
get(c) = 3 again: c moves to bucket 3; bucket 2 still holds a, so min_freq stays 2
    buckets  2: [a]   3: [{{c}}]
    min_freq 2
---
put(d, 4): full; the least frequent key is a (count 2), so a is evicted; d starts at count 1
    buckets  1: [{{d}}]   3: [c]        ({{a}} evicted)
    min_freq {{1}}
---
get(a) = -1, then get(d) = 4: d moves to bucket 2 and the minimum follows it
    buckets  2: [{{d}}]   3: [c]
    min_freq {{2}}
```

## Template

```python
from collections import OrderedDict, defaultdict


class LFUCache:
    """key -> value, key -> count, count -> keys in recency order (oldest first), and min_freq."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.value = {}
        self.count = {}
        self.buckets = defaultdict(OrderedDict)
        self.min_freq = 0

    def _touch(self, key):
        f = self.count[key]
        del self.buckets[f][key]
        if not self.buckets[f]:
            del self.buckets[f]
            if self.min_freq == f:
                self.min_freq = f + 1
        self.count[key] = f + 1
        self.buckets[f + 1][key] = None

    def get(self, key):
        if key not in self.value:
            return -1
        self._touch(key)
        return self.value[key]

    def put(self, key, value):
        if self.capacity <= 0:
            return
        if key in self.value:
            self.value[key] = value
            self._touch(key)
            return
        if len(self.value) == self.capacity:
            victim, _ = self.buckets[self.min_freq].popitem(last=False)
            if not self.buckets[self.min_freq]:
                del self.buckets[self.min_freq]
            del self.value[victim], self.count[victim]
        self.value[key] = value
        self.count[key] = 1
        self.buckets[1][key] = None
        self.min_freq = 1
```

This class was checked against a slow reference that scans every key for the smallest (count, last use) pair, on 3,000 random runs of 200 operations with capacities 0 to 5.

## Pitfalls

- **Insert, then evict.** If you add the new key to bucket 1 first and then evict from bucket `min_freq`, you can evict the key you just inserted whenever every other key has a count of 2 or more. Evict first.
- **Capacity 0.** `put` must do nothing; otherwise the eviction pops from an empty bucket.
- **Empty buckets left behind.** They are harmless for correctness here but waste memory and confuse debugging; delete them.
- **Ties.** Within a bucket the oldest use goes first. Re-inserting a touched key at the end of the next bucket keeps that order for free.

## Check yourself

Q: Capacity 3. Run put(x, 1), put(y, 2), get(x), get(x), put(z, 3), get(y), put(w, 4). Which key is evicted, and what are the buckets and min_freq at the end?
A: z is evicted: when w arrives, x has count 3, y count 2 and z count 1, so bucket 1 = [z] is the minimum. The final buckets are 1: [w], 2: [y], 3: [x] with min_freq = 1, and the cache holds w, x and y.

Q: Explain why setting `min_freq = f + 1` inside `_touch` is always right when bucket f becomes empty and f was the minimum.
A: Before the touch no bucket below f was non-empty, because f was the minimum. The touch moved one key from f to f + 1, so bucket f + 1 now contains at least that key, and bucket f is empty. No count strictly between f and f + 1 exists, so the smallest non-empty bucket is f + 1.

Q: A buggy put inserts the new key into bucket 1, sets min_freq = 1, and only then evicts the oldest key of bucket min_freq if the cache is over capacity. With capacity 2, what does put(a, 1), put(b, 2), get(a), get(b), put(c, 3), get(c) return?
A: It returns -1. At the third put, a and b both have count 2, so bucket 1 contains only c; the eviction pops c itself. A correct cache evicts a (count 2, older than b), keeps b and c, and get(c) returns 3.

## Lab

- **460 LFU Cache.** Implement the bucket design. Expected: O(1) per call; with capacity 2, put(1, 1), put(2, 2), get(2), get(2), put(3, 3), get(1), get(3), put(4, 4), get(3), get(2), get(4) gives 2, 2, -1, 3, -1, 2, 4 for the gets (put(3, 3) evicts 1; put(4, 4) evicts 3, whose count of 2 is below key 2's count of 3).
- **432 All O`one Data Structure.** Use a doubly linked list of count buckets with `key -> bucket`. Expected: O(1) per call; after inc("x"), inc("y"), inc("y"), getMaxKey() is "y" and getMinKey() is "x"; after dec("y") twice both return "x"; after dec("x") both return "".

> [!know]
> You now know how to make LFU eviction O(1) with frequency buckets and a minimum pointer, and why counts that change by one make the pointer free to maintain.

=== primer | How do you add get-min, get-max or get-random to a structure in O(1)? | 15 min
goal: Augment stacks, queues and arrays with extra state (a running minimum or maximum, an index map, a running total) and keep it correct after every operation
tag: design-augment | Augment a structure with synchronised extra state
link: MIT 6.006 (Spring 2020) lecture 7 notes | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/a2c80596cf4a2b5fbc854afdd2f23dcb_MIT6_006S20_lec7.pdf | 10 min: the section 'Steps to Augment a Binary Tree', the general recipe (choose a property each node can compute from its children, and maintain it on every change) that this card applies to stacks, queues and arrays
practice: 380, 381, 2276

> [!key]
> To answer a new question in O(1), store its answer, and update that stored answer inside every operation that could change it. A min stack keeps "minimum so far" next to each entry; a queue built from two such stacks gets its maximum; an array plus a value-to-index map gets O(1) delete and random choice by moving the last element into the hole. The work is in proving each update is O(1) and never forgotten.

## Intuition

A cashier who must announce the smallest note in the till at any moment could count every note each time. Instead, each time a note goes on top of the pile, they pencil on it "smallest so far: ...". When the top note leaves, the one beneath already carries the right answer for the smaller pile. The answer travels with the data, so it is never recomputed.

## How it works

### Min stack: store the answer with each entry

Push `(x, min(x, previous minimum))`. The minimum of the stack is the second field of the top entry. A pop removes one entry, and the entry below already knows the minimum of everything beneath it, because the stack below never changed after it was pushed. (LeetCode 155, Min Stack, is in the linear structures module's problem set.)

### Max queue: two stacks

A queue can be built from two stacks: push onto `inbox`; pop from `outbox`, and when `outbox` is empty move every element of `inbox` onto it (which reverses the order, turning LIFO into FIFO). Make both stacks max-stacks, each entry storing the maximum of its stack so far, and the queue's maximum is the larger of the two tops. A monotonic deque, from the monotonic stacks module, gives the same result for sliding-window maxima.

### Random choice: an array plus an index map

`random.choice` needs a list (O(1) by index); membership and delete need a dict. Keep both: `values` (a list) and `where` (value -> index). Insert appends and records the index. **Delete swaps with the last element**: move the last value into the deleted value's slot, update that value's index, then pop the end. Popping the end of a list is O(1); deleting from the middle would shift everything after it.

With duplicates (LeetCode 381), one value can sit at several indices, so `where` maps value -> **set** of indices. Delete takes any index of the value, moves the last element there and fixes both index sets.

### Running totals

LeetCode 2276 asks for the number of integers covered by a growing set of intervals. Keep the intervals disjoint and sorted, and keep `total` updated by every `add`: subtract the lengths of the intervals you merge, add the length of the merged one. `count()` then returns a stored number.

## Cost

- **Min stack:** push, pop, top and get_min each touch one entry: **O(1)** worst case. Space doubles (two numbers per entry).
- **Max queue:** each element is pushed onto `inbox` once, moved to `outbox` at most once and popped once, so n operations do O(n) work in total: **O(1) amortised**, although a single pop can cost O(n). `max` is O(1).
- **RandomizedSet:** insert, remove and get_random each do O(1) average dict work and O(1) list work at the end: **O(1) average**.
- **Count intervals:** an `add` that merges k intervals costs O(log n + k) with bisect plus the list splice; each interval is created once and merged away at most once, so the merging is amortised, although the list splice is O(n) in the worst case (a balanced tree or `SortedList` makes it O(log n)). `count` is **O(1)**.

## When to use it

Use augmentation when the question ("current minimum", "a random element", "total covered") is asked often and the structure changes by small steps whose effect on the answer you can compute locally.

| Need | Augment | Instead of |
|---|---|---|
| Minimum of a stack | (value, min so far) per entry | A heap with lazy deletion, O(log n) |
| Maximum of a queue | Two max-stacks, or a monotonic deque | Rescanning, O(n) |
| Uniform random element with deletes | List plus index map, delete by swap | A set (no O(1) random choice) |
| Total covered length | Running total updated on merge | Recounting all intervals |

It fails when one operation can change the answer in a way you cannot compute locally. A min stack works because a pop can only reveal an older minimum that was stored; a plain set with deletions cannot keep its minimum this way, because removing the minimum leaves no stored "next minimum" (use a heap or a sorted structure).

## Worked trace

RandomizedSet holding 10, 20, 30, 40. Watch the swap-with-last delete keep the list dense and the map exact.

```steps
start: four values; where maps each value to its index
    values  [10, 20, 30, 40]
    where   {10: 0, 20: 1, 30: 2, 40: 3}
---
remove(20): its index is 1; pop the last value (40) and write it into slot 1
    values  [10, {{40}}, 30]
    where   {10: 0, 30: 2, {{40: 1}}}        (20 deleted)
---
remove(40): index 1; pop the last value (30) into slot 1
    values  [10, {{30}}]
    where   {10: 0, {{30: 1}}}
---
insert(50): append at index 2 and record it
    values  [10, 30, {{50}}]
    where   {10: 0, 30: 1, {{50: 2}}}
---
remove(50): it is already the last element, so popping it is the whole job
    values  [10, 30]
    where   {10: 0, 30: 1}
---
get_random(): random.choice(values) returns 10 or 30, each with probability 1/2
    values  [{{10}}, {{30}}]
```

## Template

```python
import random


class MinStack:
    """Each entry stores (value, minimum of the stack up to and including it)."""

    def __init__(self):
        self.items = []

    def push(self, x):
        m = x if not self.items else min(x, self.items[-1][1])
        self.items.append((x, m))

    def pop(self):
        return self.items.pop()[0]

    def top(self):
        return self.items[-1][0]

    def get_min(self):
        return self.items[-1][1]


class MaxQueue:
    """A FIFO queue from two max-stacks: push onto inbox, pop from outbox, refill when empty."""

    def __init__(self):
        self.inbox, self.outbox = [], []        # entries are (value, max so far in that stack)

    @staticmethod
    def _push(stack, x):
        stack.append((x, x if not stack else max(x, stack[-1][1])))

    def push(self, x):
        self._push(self.inbox, x)

    def pop(self):
        if not self.outbox:
            while self.inbox:
                self._push(self.outbox, self.inbox.pop()[0])
        return self.outbox.pop()[0]

    def max(self):
        return max(s[-1][1] for s in (self.inbox, self.outbox) if s)


class RandomizedSet:
    """values: a list for O(1) random choice; where: value -> its index in the list."""

    def __init__(self):
        self.values = []
        self.where = {}

    def insert(self, x):
        if x in self.where:
            return False
        self.where[x] = len(self.values)
        self.values.append(x)
        return True

    def remove(self, x):
        i = self.where.pop(x, None)
        if i is None:
            return False
        last = self.values.pop()
        if i < len(self.values):          # x was not the last element: move last into its slot
            self.values[i] = last
            self.where[last] = i
        return True

    def get_random(self):
        return random.choice(self.values)
```

All three were stress-tested against plain Python models (a list for the stack and queue, a set for RandomizedSet) on thousands of random operation sequences; 80,000 calls to `get_random` on eight values gave each value a frequency within one percentage point of 1/8.

## Pitfalls

- **Deleting from the middle of the list.** `values.remove(x)` or `del values[i]` is O(n); always swap with the last element.
- **The last-element case.** If x is the last element, there is nothing to move. The template pops first and only writes back when `i < len(values)`. Code that deletes `where[x]` *before* writing `where[last] = i` re-creates a stale entry for x when x is the last element.
- **Random choice from a set or dict.** `random.choice` needs a sequence; converting `list(s)` each time is O(n).
- **Max queue amortisation.** The O(1) is amortised: one pop may move the whole inbox. If a single slow call matters, the monotonic deque has O(1) worst-case pops (its pushes are the amortised part instead).

## Check yourself

Q: Push 4, 2, 6, 1 onto the MinStack. What does `items` contain, and what is get_min() after two pops?
A: items is [(4, 4), (2, 2), (6, 2), (1, 1)]. Two pops remove (1, 1) and (6, 2), leaving [(4, 4), (2, 2)], so get_min() is 2, read directly from the top entry.

Q: Prove that the two-stack queue does O(n) total work for any sequence of n operations, although one pop can take O(n).
A: Follow one element: it is pushed onto inbox once, moved from inbox to outbox at most once (it never goes back), and popped from outbox at most once. That is at most three constant-time steps per element, so n operations cost at most about 3n steps in total. A single pop that triggers a refill pays for every element moved, but each of those elements is moved only once in its life.

Q: This remove deletes the map entry first: `i = where.pop(x); last = values[-1]; values[i] = last; where[last] = i; values.pop()`. On which input does it break, and how?
A: When x is the last element. Then last is x, so `where[last] = i` writes x back into the map, pointing at index i, and the pop removes that index. Afterwards insert(x) returns False (x looks present) and a later remove(x) reads a stale index. Handle the last-element case first, as the template does.

## Lab

- **380 Insert Delete GetRandom O(1).** Expected: O(1) average per call; insert(4), insert(4), insert(9), remove(4), remove(4) return True, False, True, True, False, and getRandom() then always returns 9.
- **381 Insert Delete GetRandom O(1), duplicates allowed.** Map each value to a set of indices. Expected: O(1) average per call; insert(2), insert(2), insert(5) return True, False, True; after remove(2) returns True, the list holds one 2 and one 5, and getRandom() returns each with probability 1/2.
- **2276 Count Integers in Intervals.** Keep sorted disjoint intervals and a running total. Expected: add(2, 4), add(8, 9) gives count() = 5; add(5, 7) merges everything into [2, 9] and count() = 8; add(1, 3) gives count() = 9.

> [!know]
> You now know how to answer extra queries in O(1) by storing their answers and updating them inside every operation, including delete-by-swap for O(1) random choice.

=== primer | How do you store values that change over time and query them by time or version? | 15 min
goal: Keep per-key histories in time order and answer "value at time t" with bisect, give snapshots for free by recording only changes, and keep derived indexes correct under corrections with lazy validation
tag: design-versioned | Per-key histories with binary search
link: Python docs: bisect, searching sorted lists | https://docs.python.org/3/library/bisect.html#searching-sorted-lists | 5 min: the find_le recipe is exactly "the last write at or before t"; then read Performance Notes (insort is O(n) because of the insertion)
link: PostgreSQL docs: introduction to MVCC | https://www.postgresql.org/docs/current/mvcc-intro.html | 3 min: one page on why a database keeps several versions of a row so that each statement reads a consistent snapshot
practice: 2034

> [!key]
> Never overwrite history you may be asked about. For each key keep a list of (time, value) pairs in time order; a query for time t is a binary search for the last entry at or before t. Snapshots become cheap the same way: record only the cells that changed, tagged with the snapshot id. When values can be corrected, keep one dict as the source of truth and treat every other index (heaps, sorted lists) as a cache you validate against it.

## Intuition

A shared document's version history does not store a full copy of the document for every save. It stores what changed and when. To see the document as it was on Tuesday at noon, you take the latest change to each part made on or before that moment. The question "what was the value at time t?" is a search in a sorted list of changes.

## How it works

### Time-based key-value store

`set(key, value, t)` appends `(t, value)` to the key's history; LeetCode 981 (in the binary search module's problem set) promises that timestamps arrive in increasing order, so appending keeps each history sorted. `get(key, t)` returns the value of the **last entry with time <= t**: `bisect_right(times, t) - 1`, or the empty string if that index is -1. Keeping times and values in two parallel lists lets bisect compare plain numbers.

### Snapshot array

An array of n cells supports `set(i, v)`, `snap()` (returns a snapshot id 0, 1, 2, ...) and `get(i, snap_id)`. Copying the array on every snap costs O(n) per snap. Instead, give each cell its own history of `(snap_id, value)`, starting with `(-1, 0)`, and append only when a cell changes. Several sets to the same cell before the next snap overwrite the last entry, since only the final value of that snapshot is visible. `get(i, s)` is a bisect for the last entry with snap id <= s. LeetCode 1146, Snapshot Array, appears in one of the mixed review sets.

### Corrections: one truth, lazy indexes

LeetCode 2034 streams (timestamp, price) records that may **correct** an earlier timestamp, and asks for the latest price, the maximum and the minimum. Keep `price: timestamp -> price` as the source of truth and the latest timestamp as a number. For the maximum, push `(-price, timestamp)` onto a max-heap on every update and never delete from it. When asked for the maximum, look at the top: if `price[timestamp]` no longer equals that price, the entry is stale (that timestamp was corrected later), so pop it and look again. The first entry that agrees with the dict is the true maximum.

This **lazy validation** pattern appears whenever an index is cheaper to rebuild piecemeal than to update in place: heaps with changed priorities, caches with expiry, search indexes with deleted documents.

## Cost

- **TimeMap:** `set` is an O(1) amortised append; `get` is a bisect, **O(log h)** where h is that key's history length. Space O(total sets).
- **SnapshotArray:** `set` O(1) amortised, `snap` O(1), `get` **O(log c)** where c is the number of changes to that cell. Space O(n + total sets), against O(n x snaps) for copying.
- **StockPrice:** `update` is two heap pushes, O(log u) for u updates so far. A `maximum` call may pop several stale entries, but each pushed entry is popped at most once, so over the whole stream the pops cost O(u log u) in total: **O(log u) amortised** per operation. Space O(u), because stale entries wait in the heaps until they surface.

## When to use it

Cues: "at time t", "as of", "snapshot", "version", "undo", "history", or updates that may arrive for an earlier key. Production versions are everywhere: PostgreSQL's MVCC keeps several versions of each row so that every statement reads a consistent snapshot, time-series databases search sorted timestamps, and Git stores history as a chain of snapshots that share unchanged content.

| Situation | Choose |
|---|---|
| Timestamps arrive in order per key | Append plus bisect |
| Writes may arrive out of order | `bisect.insort` (O(h) per insert) or a `SortedList` |
| Whole-array snapshots, few changes per snap | Per-cell histories |
| Corrections to past records, max or min wanted | Dict of truth plus heaps with lazy validation |

Avoid lazy heaps when corrections vastly outnumber queries and memory is tight: stale entries pile up. Rebuild the heap from the dict when it grows past, say, twice the number of live records.

## Worked trace

SnapshotArray of length 3. Each cell's history is a list of (snap id, value), starting at (-1, 0).

```steps
set(0, 5): cell 0 changes during snapshot 0, so append (0, 5)
    cell 0  (-1,0) {{(0,5)}}
    cell 1  (-1,0)
    cell 2  (-1,0)
    snap_id 0
---
snap() returns 0: nothing is copied, only the counter moves
    cell 0  (-1,0) (0,5)
    snap_id {{1}}
---
set(0, 6), set(2, 1): new entries tagged with snap id 1
    cell 0  (-1,0) (0,5) {{(1,6)}}
    cell 2  (-1,0) {{(1,1)}}
---
set(2, 4): cell 2 already changed during snap 1, so overwrite that entry instead of appending
    cell 2  (-1,0) {{(1,4)}}
---
snap() returns 1
    snap_id {{2}}
---
get(0, 0): last entry of cell 0 with id <= 0 is (0, 5), so 5; get(0, 1) gives 6
    cell 0  (-1,0) {{(0,5)}} (1,6)
---
get(2, 0): cell 2's only entry with id <= 0 is (-1, 0), so 0; get(1, 1) is 0 too
    cell 2  {{(-1,0)}} (1,4)
```

## Template

```python
import heapq
from bisect import bisect_right


class TimeMap:
    """key -> parallel lists of increasing timestamps and their values."""

    def __init__(self):
        self.times = {}
        self.vals = {}

    def set(self, key, value, t):
        self.times.setdefault(key, []).append(t)     # assumes t never decreases per key
        self.vals.setdefault(key, []).append(value)

    def get(self, key, t):
        ts = self.times.get(key)
        if not ts:
            return ""
        i = bisect_right(ts, t) - 1                   # last write at or before t
        return self.vals[key][i] if i >= 0 else ""


class SnapshotArray:
    """Each index keeps a history of (snap_id, value); untouched indices cost nothing."""

    def __init__(self, length):
        self.hist = [[(-1, 0)] for _ in range(length)]
        self.snap_id = 0

    def set(self, index, val):
        h = self.hist[index]
        if h[-1][0] == self.snap_id:
            h[-1] = (self.snap_id, val)        # overwrite within the same snapshot
        else:
            h.append((self.snap_id, val))

    def snap(self):
        self.snap_id += 1
        return self.snap_id - 1

    def get(self, index, snap_id):
        h = self.hist[index]
        i = bisect_right(h, (snap_id, float("inf"))) - 1
        return h[i][1]


class StockPrice:
    """The dict is the truth; the heaps are indexes that may hold stale (price, time) pairs."""

    def __init__(self):
        self.price = {}
        self.latest = 0
        self.maxh, self.minh = [], []

    def update(self, t, p):
        self.price[t] = p
        self.latest = max(self.latest, t)
        heapq.heappush(self.maxh, (-p, t))
        heapq.heappush(self.minh, (p, t))

    def current(self):
        return self.price[self.latest]

    def maximum(self):
        while self.price[self.maxh[0][1]] != -self.maxh[0][0]:
            heapq.heappop(self.maxh)          # stale: that timestamp was corrected later
        return -self.maxh[0][0]

    def minimum(self):
        while self.price[self.minh[0][1]] != self.minh[0][0]:
            heapq.heappop(self.minh)
        return self.minh[0][0]
```

Each class was compared with a brute force (scan the full log, keep full array copies, recompute max and min from the dict) on 2,000 random operation sequences.

## Pitfalls

- **bisect_left instead of bisect_right.** For "last entry at or before t" you need the insertion point *after* any entry equal to t; `bisect_left` would skip an entry written exactly at t.
- **Index -1.** If every entry is after t, `bisect_right(...) - 1` is -1, and `vals[-1]` silently returns the newest value. Check for it, or seed each history with a sentinel as SnapshotArray does.
- **Comparing tuples with mixed types.** Bisecting `(snap_id, value)` pairs with `(s, float("inf"))` works for numbers; for other values, bisect a separate list of ids.
- **Validating against the wrong truth.** A stale heap entry is detected by comparing its price with `price[t]`, not by remembering which entries were pushed; two updates with the same price at the same timestamp are both valid.

## Check yourself

Q: SnapshotArray(2): set(1, 4), snap(), snap(), set(1, 9), set(0, 2), snap(). What do the three snaps return, what are the histories, and what are get(1, 0), get(1, 1), get(1, 2) and get(0, 1)?
A: The snaps return 0, 1 and 2. Cell 0's history is [(-1, 0), (2, 2)] and cell 1's is [(-1, 0), (0, 4), (2, 9)]. get(1, 0) and get(1, 1) are 4 (snapshot 1 recorded no change to cell 1, so it inherits snapshot 0's value), get(1, 2) is 9, and get(0, 1) is 0.

Q: Why is StockPrice's `maximum` O(log u) amortised even though one call may pop many entries?
A: Every update pushes exactly one entry per heap, and an entry, once popped as stale, never returns. So across the whole stream the total number of pops is at most the number of pushes, u, each O(log u). Spreading that total over u operations gives O(log u) amortised per operation.

Q: A colleague's TimeMap uses `bisect_left(times, t) - 1`. With writes at times 1, 5 and 9, which query returns the wrong answer?
A: Any query exactly at a write time: get(key, 5) finds index 1 with bisect_left, subtracts one, and returns the value written at 1 instead of the value written at 5. bisect_right puts the insertion point after equal times, so subtracting one lands on the entry written at t.

## Lab

- **2034 Stock Price Fluctuation.** Keep the dict of truth plus a max-heap and a min-heap with lazy validation. Expected: O(log n) amortised per call; after update(4, 30), update(7, 12), update(4, 5), update(9, 20), update(7, 40), current() is 20, maximum() is 40 and minimum() is 5 (the entries (30, 4) and (12, 7) are stale and get popped when they surface).
- **Exercise: TimeMap.** Implement it and run set("door", "shut", 1), set("door", "open", 5), set("door", "shut", 9). Expected: get("door", t) for t = 0, 1, 4, 5, 8, 9, 100 returns "", "shut", "shut", "open", "open", "shut", "shut", and get("lamp", 3) returns "".

> [!know]
> You now know how to answer "value at time t" with per-key histories and bisect, take snapshots by recording only changes, and keep heaps correct under corrections with lazy validation.

=== primer | How do you count recent events and limit request rates? | 16 min
goal: Implement a hit counter and four rate limiters (sliding log, fixed window, sliding window counter, token bucket), state the exact guarantee and memory cost of each, and get the window boundaries right
tag: design-ratelimit | Sliding windows and token buckets
link: Wikipedia: token bucket | https://en.wikipedia.org/wiki/Token_bucket#Algorithm | 5 min: 'Algorithm', then 'Properties' for the long-run average rate and the largest possible burst
link: NGINX docs: limit_req | https://nginx.org/en/docs/http/ngx_http_limit_req_module.html#limit_req | 5 min: the module summary (a leaky bucket per key) and the burst and nodelay parameters, a real configuration of the ideas in this card
practice: 933, 622

> [!key]
> "How many events in the last W seconds?" is a queue of timestamps: append the new one, pop old ones from the front. A rate limiter is that question plus a decision. Keeping every timestamp (a **sliding log**) is exact but costs memory per request; a **fixed window** counter is one integer but can let through twice the limit across a boundary; a **sliding window counter** blends two windows; a **token bucket** stores two numbers and allows controlled bursts.

## Intuition

A nightclub allows at most 100 people inside per hour of arrivals. The doorman could write down every arrival time and count the last hour (exact, but a long list). He could reset a tally on the hour (cheap, but 100 people at 9:59 and 100 more at 10:00 all get in). Or he could hand out tickets from a jar that a machine refills at a steady rate, letting a group in at once if the jar is full: that is the token bucket.

## How it works

### Hit counter: a queue of timestamps

LeetCode 933 calls `ping(t)` with increasing t and asks how many pings fall in [t - 3000, t]. Append t to a deque; while the front is older than t - 3000, pop it; return the length. Old timestamps never matter again, so discarding them is safe.

### Sliding log limiter

Allow a request at time t if fewer than L requests were allowed in the window (t - W, t]. Keep the allowed timestamps in a deque, drop those <= t - W, then compare the length with L. It is **exact**: no window of length W ever contains more than L allowed requests. Memory is up to L timestamps per client.

Because the log never needs more than L entries, it fits in a **ring buffer of size L** (LeetCode 622 builds one): keep the last L allowed times with the oldest at `head`. If that oldest time is still inside the window, all L are, so reject; otherwise overwrite it with t and advance `head`. Every call is O(1) worst case.

### Fixed window counter

Number the windows `w = t // W` and keep (current window, count). A new window resets the count. One integer per client, but a burst of L requests at the end of one window and L more at the start of the next passes 2L requests within a few seconds. In a measured boundary test (L = 10, W = 60, ten requests at t = 59 and ten at t = 60) the fixed window allowed all 20, the sliding log 10.

### Sliding window counter

Keep the counts of the current and previous fixed windows and estimate the sliding count as `prev x (1 - f) + cur`, where f is how far t is into the current window. It assumes the previous window's requests were spread evenly. Cloudflare has described running this two-counter approximation at scale. In the same boundary test it allowed 10.

### Token bucket

The bucket holds up to `burst` tokens and gains `rate` tokens per second. On each request, first refill lazily: `tokens = min(burst, tokens + (now - last) x rate)`, then spend one token if at least one is there. No timer runs in the background; the refill is computed from the elapsed time. Over any interval of length T, at most `burst + rate x T` requests pass, so the long-run rate is `rate` and the largest burst is `burst`.

## Cost

| Limiter | Time per request | Memory per client | Guarantee |
|---|---|---|---|
| Sliding log (deque) | O(1) amortised: each timestamp is appended once and popped once | Up to L timestamps | Exact: at most L in every window |
| Sliding log (ring of size L) | O(1) worst case | Exactly L slots | Exact, same decisions as the deque |
| Fixed window | O(1) | Two integers | At most L per aligned window, up to 2L across a boundary |
| Sliding window counter | O(1) | Three numbers | Approximate; exact only if traffic is even |
| Token bucket | O(1) | Two floats | At most burst + rate x T in any interval T |

The hit counter is the same as the deque log: O(1) amortised per ping, O(hits in the window) memory.

## When to use it

- **Exactness matters and L is small** (login attempts, password resets): sliding log.
- **Huge numbers of clients, memory is the constraint**: fixed window or sliding counter; accept the boundary effect, or use the sliding counter to blunt it.
- **APIs that should allow short bursts but cap the average**: token bucket. Its state per client is two numbers, so it can live in a shared store.
- **Smoothing traffic rather than rejecting it**: a leaky bucket queues requests and releases them at a fixed rate; NGINX's `limit_req` works this way.

Production concerns (distributed counters, clock skew, per-client state eviction) belong to the production caching and limiting material later in the guide; the data structure choices are the ones above.

## Worked trace

Token bucket with rate 1 token per second and burst 3, starting full at t = 0.

```steps
t = 0: bucket full at 3.0; first request takes a token
    tokens before 3.0   ->  {{allow}}   ->  tokens 2.0
---
t = 0, twice more: no time has passed, so no refill
    tokens 2.0 -> allow -> 1.0;  tokens 1.0 -> allow -> {{0.0}}
---
t = 0, fourth request: empty bucket
    tokens before 0.0   ->  {{reject}}  ->  tokens 0.0
---
t = 1.5: refill 1.5 x 1 = 1.5 tokens, then spend one
    tokens before {{1.5}}   ->  allow   ->  tokens 0.5
---
t = 2: refill 0.5 x 1 = 0.5, reaching 1.0; allow; a second request at t = 2 finds 0.0 and is rejected
    tokens before {{1.0}}   ->  allow, then {{reject}}
---
t = 5: three seconds would add 3.0, but the bucket caps at burst = 3
    tokens before {{3.0}} (capped)   ->  allow, allow, allow, then reject
```

Eleven requests, eight allowed: the three-request burst at t = 0, one each at 1.5 and 2, and three at 5. The bound burst + rate x T = 3 + 1 x 5 = 8 is met exactly.

## Template

```python
from collections import deque


class RecentCounter:
    """Hits in [t - window, t], inclusive. Times must not decrease."""

    def __init__(self, window=3000):
        self.window = window
        self.q = deque()

    def ping(self, t):
        self.q.append(t)
        while self.q[0] < t - self.window:
            self.q.popleft()
        return len(self.q)


class RingLimiter:
    """At most `limit` requests in any window (t - window, t]: remember the last `limit` allowed times."""

    def __init__(self, limit, window):
        self.window = window
        self.times = [float("-inf")] * limit   # ring buffer of allowed times, oldest at head
        self.head = 0

    def allow(self, t):
        if self.times[self.head] > t - self.window:
            return False                       # the last `limit` allowed requests are all inside the window
        self.times[self.head] = t
        self.head = (self.head + 1) % len(self.times)
        return True


class TokenBucket:
    """Refill `rate` tokens per second up to `burst`; a request spends one token."""

    def __init__(self, rate, burst, now=0.0):
        self.rate, self.burst = rate, burst
        self.tokens, self.last = float(burst), now

    def allow(self, now, cost=1):
        self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
```

These were property-tested on random traffic: the ring limiter made the same decision as the deque log on 3,000 random runs; no window of length W ever held more than L requests allowed by the log; and over every interval the token bucket allowed at most burst + rate x T.

## Pitfalls

- **Inclusive or exclusive edges.** LeetCode 933 counts [t - 3000, t], so pop while `front < t - 3000`. The limiter above uses (t - W, t], so it drops times `<= t - W`. Write the interval down before writing the comparison.
- **Fixed windows at boundaries.** They can admit 2L requests in a short span. Say so when you choose one.
- **Timers for refills.** Never run a background job per client to add tokens; compute the refill from the elapsed time on each request.
- **Clocks that go backwards.** `time.time()` can jump; use `time.monotonic()` for elapsed time in a single process.
- **Unbounded per-client state.** A dict of limiters keyed by client id grows forever; evict idle clients (an LRU cache of limiters works well).

## Check yourself

Q: A token bucket has rate 2 per second and burst 4, full at t = 0. Requests arrive at t = 0 (five of them), t = 0.5 (two) and t = 3 (one). Which are allowed, and how many tokens are left at the end?
A: At t = 0 the first four are allowed and the fifth rejected (bucket empty). At t = 0.5 the refill adds 1 token: the first request is allowed, the second rejected. At t = 3 the refill would add 5 but the bucket caps at 4, so the request is allowed and 3 tokens remain.

Q: Why does the ring-buffer limiter reject exactly when the deque sliding log would?
A: The ring holds the last L allowed timestamps with the oldest at `head`. The log allows t only if fewer than L allowed times lie in (t - W, t]. Since times never decrease, the L most recent allowed times are all inside that window exactly when the oldest of them is; so "the oldest is > t - W" is the same condition as "L allowed times are already in the window".

Q: A limiter of 5 requests per 10 seconds receives five requests at t = 9 and five at t = 10. How many does a fixed window allow, and how many does the sliding window counter allow?
A: The fixed window allows all 10: t = 9 falls in window 0 and t = 10 in window 1, each with its own count of 5. The sliding counter allows 5: at t = 10 it is 0% into window 1, so the estimate is 5 x (1 - 0) + 0 = 5, which already reaches the limit.

## Lab

- **933 Number of Recent Calls.** Use a deque of timestamps. Expected: O(1) amortised per ping; pings at 5, 1000, 3005, 3006, 7000 return 1, 2, 3, 3, 1.
- **622 Design Circular Queue.** Store `head` and `size`, and derive the tail as `(head + size - 1) % k`. Expected: O(1) per call; with k = 2, enQueue(7), enQueue(8), enQueue(9) return True, True, False, Rear() is 8, isFull() is True, deQueue() is True, enQueue(9) is True, and then Front() is 8 and Rear() is 9 (the 9 was written into the slot the 7 vacated).

> [!know]
> You now know how to count events in a sliding window with a queue and how to choose between sliding log, fixed window, sliding counter and token bucket limiters by their guarantees and memory.

=== primer | How do you design iterators that flatten, peek or produce values lazily? | 14 min
goal: Write iterator classes whose has_next and peek are safe to call repeatedly, flatten nested data lazily with a stack, and know when a Python generator does the same job in a few lines
tag: design-iterator | Lazy iterators and generators
link: Python docs: Functional Programming HOWTO, Generators | https://docs.python.org/3/howto/functional.html#generators | 10 min: how a generator suspends with its local variables intact, then 'Passing values into a generator' if you are curious
link: Python docs: iterator types | https://docs.python.org/3/library/stdtypes.html#iterator-types | 3 min: the iterator protocol, __iter__ and __next__ raising StopIteration, and the rule that an exhausted iterator stays exhausted
practice: 284

> [!key]
> An iterator is a cursor plus a promise: it remembers where it is and produces one element per request, so memory stays proportional to the cursor, not to the data. The design rule is to **buffer one element of lookahead**: `has_next` and `peek` fill the buffer if it is empty and never consume more, `next` hands the buffer over and clears it. For nested data, the cursor is a stack of positions, one per open level.

## Intuition

Reading a long book, you keep a bookmark, not a photocopy of the remaining pages. To answer "is there another chapter?" you glance ahead without turning the page; doing that twice must not skip a chapter. For a book of nested sections, you keep one bookmark per open section: when a subsection ends, you remove its bookmark and continue in the parent.

## How it works

### Python's protocol

An iterable has `__iter__`, which returns an iterator. An iterator has `__next__`, which returns the next element or raises `StopIteration`. `for` loops, `list()`, `sum()` and `zip()` all speak this protocol. The built-in `next(it, default)` returns `default` instead of raising, which is the cleanest way to read one element of lookahead.

### Peeking iterator: one element of lookahead

LeetCode 284 wraps an iterator and adds `peek()`. Store the next element in a field as soon as you can: in `__init__` read one element ahead; `peek` returns the field; `next` returns it and reads the following element into the field; `has_next` checks whether the field holds a real element. Use a private sentinel object for "exhausted", never `None`, because `None` may be a legitimate element.

### Flattening nested lists: a stack of cursors

Given `[1, [2, [3]], 4]`, produce 1, 2, 3, 4 one at a time. Keep a stack of `[list, index of the next unread item]`. To find the next integer: look at the top entry; if its list is finished, pop it and continue with the parent; if the next item is a list, advance the index and push a new cursor for the sublist (without copying it); if it is an integer, advance the index, store the integer, and stop. LeetCode 341 (Flatten Nested List Iterator) is this exact design and sits in the linear structures module's problem set.

### Making has_next idempotent

LeetCode drives iterators with `while it.hasNext(): it.next()`, but real callers may call `has_next` twice. Keep a `ready` flag: `has_next` does work only when `ready` is False and sets it when it finds an element; `next` calls `has_next`, clears `ready` and returns the buffered value.

### Generators do the bookkeeping for you

A function containing `yield` returns a generator: Python suspends the function at each `yield`, keeping its local variables and position, and resumes it on the next request. A recursive generator with `yield from` flattens nested lists in four lines, and the chain of suspended frames *is* the stack of cursors. Interviewers usually ask for the explicit class; in your own code, prefer the generator.

## Cost

- **Peeking iterator:** every method is **O(1)** plus at most one call to the wrapped iterator. Space O(1).
- **Nested iterator:** each integer is buffered once and each list is pushed and popped once, so producing all n integers from a structure with m lists costs O(n + m) in total, **O(1) amortised per element**. Space is O(d), where d is the nesting depth, against O(n) for flattening everything into a list up front.
- **Recursive generator:** the same total work, but each element is passed up through every suspended generator above it, so an element at depth d costs O(d) to deliver, and Python's recursion limit (about 1000 frames) caps the depth. The explicit stack has neither problem.

## When to use it

Use lazy iterators when the data is large, unbounded or expensive to produce: lines of a file (looping over a file object reads one line at a time, which the Python tutorial calls memory efficient and fast), rows from a database cursor, pages from a paginated API, or an infinite sequence such as `itertools.count()`. They also let a consumer stop early without paying for the rest.

| Approach | Memory | First element available | Notes |
|---|---|---|---|
| Flatten to a list, then iterate | O(n) | After all n are built | Simple; fine for small inputs |
| Explicit stack iterator class | O(depth) | Immediately | Interview standard; no recursion limit |
| Recursive generator with `yield from` | O(depth) frames | Immediately | Shortest; limited by recursion depth |

Do not make an iterator lazy if the caller needs `len()`, random access or several passes; an iterator can be consumed only once.

## Worked trace

Flattening `[1, [2, [3]], 4]` with a stack of `[list, next index]` cursors. `L@i` means "list L, next unread index i".

```steps
start: one cursor on the outer list
    stack  [1, [2, [3]], 4]@{{0}}
---
has_next(): item 0 is the integer 1; advance the index and buffer it
    stack  [1, [2, [3]], 4]@{{1}}
    value  {{1}}  ready
---
next() returns 1. has_next(): item 1 is a list, so advance to 2 and push a cursor for [2, [3]]; its item 0 is 2
    stack  [1, [2, [3]], 4]@2   {{[2, [3]]@1}}
    value  {{2}}
---
next() returns 2. has_next(): [2, [3]] item 1 is the list [3], push it; its item 0 is 3
    stack  [1, [2, [3]], 4]@2   [2, [3]]@2   {{[3]@1}}
    value  {{3}}
---
next() returns 3. has_next(): [3] is finished, pop; [2, [3]] is finished, pop; outer item 2 is 4
    stack  [1, [2, [3]], 4]@{{3}}
    value  {{4}}
---
next() returns 4. has_next(): the outer list is finished, pop it; the stack is empty, so False
    stack  {{(empty)}}
```

## Template

```python
class PeekingIterator:
    """Wraps any iterator; keeps one element of lookahead in self._next."""
    _END = object()

    def __init__(self, it):
        self._it = iter(it)
        self._next = next(self._it, self._END)

    def peek(self):
        return self._next          # caller should check has_next() first

    def next(self):
        x = self._next
        self._next = next(self._it, self._END)
        return x

    def has_next(self):
        return self._next is not self._END


class NestedIterator:
    """Flattens nested lists lazily. Stack entries are [list, index of its next unread item]."""

    def __init__(self, nested):
        self.stack = [[nested, 0]]
        self.ready = False                   # True when self.value holds the next integer
        self.value = None

    def has_next(self):
        while not self.ready and self.stack:
            lst, i = self.stack[-1]
            if i == len(lst):
                self.stack.pop()             # this list is finished: resume its parent
                continue
            self.stack[-1][1] += 1
            if isinstance(lst[i], list):
                self.stack.append([lst[i], 0])   # descend without copying the sublist
            else:
                self.value, self.ready = lst[i], True
        return self.ready

    def next(self):
        if not self.has_next():
            raise StopIteration
        self.ready = False
        return self.value


def flatten(nested):
    """Generator version: Python keeps the stack of suspended frames for you."""
    for x in nested:
        if isinstance(x, list):
            yield from flatten(x)
        else:
            yield x
```

All three were checked against a recursive list-building flatten on 5,000 random nested lists (with `has_next` called an extra time at random), and the peeking iterator was also run over an infinite generator.

## Pitfalls

- **has_next that consumes.** If `has_next` pulls from the underlying iterator without buffering, a second call skips an element.
- **None as "no element".** `None` (or 0, or "") may be a real element; use a private sentinel object.
- **Copying sublists.** Pushing `lst[i][:]` or reversing a copy costs O(size) per list; push a cursor instead.
- **Empty sublists.** `[[], [[]]]` contains no integers; `has_next` must keep popping until it finds one or the stack empties, which the `while` loop does.
- **Exhausted generators.** A generator can be iterated once; `list(gen)` a second time returns `[]`.

## Check yourself

Q: For `NestedIterator([[], [[5]], 6])`, what do has_next(), has_next(), next(), next(), has_next() return in that order?
A: True, True, 5, 6, False. The first has_next pops past the empty list, descends into [[5]] and [5], and buffers 5; the second call sees `ready` already True and does nothing. The first next returns 5; the second next calls has_next, which finishes [5] and [[5]] and buffers 6; the final has_next empties the stack and returns False.

Q: Why does the explicit-stack iterator use O(depth) memory while flattening into a list uses O(n), and why can the recursive generator fail where the class does not?
A: The stack holds one small cursor per currently open list, at most the nesting depth, while a flattened list holds every element. The recursive generator also keeps one suspended frame per open level, but those are Python call frames, so a list nested deeper than the recursion limit (about 1000 by default) raises RecursionError; the explicit stack is an ordinary list with no such limit.

Q: A PeekingIterator stores `None` to mean "exhausted". Which input breaks it?
A: Any iterator that yields `None`, for example `[1, None, 3]`: after 1 is returned, the buffer holds `None`, so `has_next` reports False and the caller never sees None or 3. A private sentinel such as `object()` cannot collide with real data.

## Lab

- **284 Peeking Iterator.** Buffer one element. Expected: O(1) per call; over [7, 8, 9], next(), peek(), next(), next(), hasNext() return 7, 8, 8, 9, False.
- **Exercise: generator flatten.** Write `flatten` with `yield from`, then the explicit-stack version as a generator. Expected: both give [1, 1, 2, 1, 3, 4] for `[[1, 1], 2, [1, [], [3, [4]]]]` and [] for `[[[]], []]`.

> [!know]
> You now know how to build lazy iterators with one element of lookahead, flatten nested data with a stack of cursors, and when a generator is the simpler choice.

=== primer | How do you test a data structure you designed? | 15 min
goal: Test any stateful structure by running random operation sequences against a slow reference model, first with a ten-line stress harness and then with a Hypothesis state machine that shrinks failures to a minimal case
tag: design-model-test | Model-based stateful testing
link: Hypothesis docs: stateful tests | https://hypothesis.readthedocs.io/en/latest/stateful.html#rule-based-state-machines | 15 min: 'Rule-based state machines', then 'Preconditions' and 'Invariants', which are the three tools used below
practice: 432, 460

> [!key]
> A designed structure is only as good as its invariant after the ten-thousandth operation, and hand-written examples rarely reach the states where bugs live. Write a **model**: the same interface implemented in the most obviously correct way, ignoring speed (a list, a scan, a `min()`). Drive both with the same random operations, compare every result and invariant, and when they disagree, **shrink** the failing sequence to the shortest one that still fails.

## Intuition

A bank replacing its interest calculator does not trust a dozen spot checks. It runs the new system and the old one side by side on the same transactions for a month and investigates every difference. The old system is slow and ugly, but trusted; that is what makes it a good judge. In testing, that trusted twin is the **model** (also called the oracle or reference implementation).

## How it works

### 1. Write the model

The model has the same methods and the simplest correct implementation: an LRU cache as a list in recency order with linear scans; an LFU cache as a dict scanned for the smallest (count, last use); a min stack as a list and `min()`. If the model needs cleverness, it is not a model.

### 2. Generate operations from a small space

Bugs live where operations interact: the same key updated twice, an eviction right after an update, a pop that empties the structure. Use **small parameters** so those collisions happen constantly: keys 0 to 6, capacities 1 to 3, values from a short range. A key space of a million makes repeated keys rare.

### 3. Compare after every operation

Compare each return value, and check the structure's own invariants (size never above capacity, dict and list hold the same keys) after each step. Stop at the first disagreement and print the sequence that led to it.

### 4. Shrink

A random failure may be fifty operations long. Shrinking removes operations and simplifies arguments while the failure persists, until nothing more can be removed. You can do this by hand (delete one line at a time and rerun), but **Hypothesis** does it automatically: a `RuleBasedStateMachine` declares rules (operations with argument strategies), preconditions (when a rule may run) and invariants (checked after every step), and on failure prints a minimal program that reproduces the bug.

### 5. Keep the test

Run it in CI with a fixed budget. A planted bug is the test of the test: break the structure on purpose (forget to refresh recency on update) and make sure the test fails.

## Cost

Each trial runs s operations on both objects. If the model costs O(n) per operation on a structure of size n, a test of T trials costs O(T x s x n), which is trivial for the small sizes that find bugs: 2,000 trials of 12 steps finish in well under a second. Hypothesis adds shrinking time only when something fails. The real cost is writing the model, usually 15 to 30 lines, and it pays for itself the first time it catches an ordering bug.

## When to use it

Use model-based testing for anything with state and more than one operation: caches, limiters, iterators, heaps, union-find, interval sets, your LeetCode design classes before you submit them. It is the stateful version of the stress test you use for single functions.

| Technique | Finds | Misses |
|---|---|---|
| Hand-written examples | The cases you thought of | Interactions you did not imagine |
| Random stress test against a model | Wrong results in reachable states | Bugs needing very large sizes; the model's own bugs |
| Hypothesis state machine | The same, plus a minimal reproducing program | The same blind spots, if the strategies are too narrow |
| Differential test against another implementation (e.g. `OrderedDict`) | Disagreements, with no model to write | Bugs shared by both implementations |

For randomised operations (get_random) compare properties, not values: the result is a member of the model's set, and over many calls each member appears about equally often.

## Worked trace

A buggy min stack remembers one minimum and never restores it after a pop. Hypothesis found a failure and shrank it to three operations; here is that run, system under test beside the model.

```steps
push(1): both agree; invariant get_min() == min(model) holds
    sut    items [1]      min {{1}}
    model  [1]            min(model) {{1}}
---
push(0): the new value is smaller, so both minimums become 0
    sut    items [1, 0]   min {{0}}
    model  [1, 0]         min(model) {{0}}
---
pop(): both return 0, but the sut never restores its minimum
    sut    items [1]      min {{0}}
    model  [1]            min(model) {{1}}
---
the invariant fails, and Hypothesis prints the minimal program:
    state = MinStackMachine()
    state.push(x=1)
    state.push(x=0)
    state.pop()
```

## Template

A dependency-free harness, usable for any class with a matching model:

```python
import random


def stress(make_sut, make_model, random_op, trials=2000, max_steps=12, seed=0):
    """Run random operation sequences on both objects; return the first failing log, or None."""
    rng = random.Random(seed)
    for _ in range(trials):
        sut, model, log = make_sut(), make_model(), []
        for _ in range(rng.randint(1, max_steps)):
            name, args = random_op(rng, model)
            want = getattr(model, name)(*args)
            got = getattr(sut, name)(*args)
            log.append(f"{name}({', '.join(map(repr, args))}) -> {got!r}")
            if got != want:
                return log, f"expected {want!r}"
    return None


class ModelMinStack:
    """Obviously correct and slow: a list, and min() over it."""

    def __init__(self):
        self.items = []

    def push(self, x):
        self.items.append(x)

    def pop(self):
        return self.items.pop()

    def get_min(self):
        return min(self.items)


def random_op(rng, model):
    if model.items and rng.random() < 0.4:
        return rng.choice(["pop", "get_min"]), ()
    return "push", (rng.randint(-3, 3),)
```

The Hypothesis version (`pip install hypothesis`; run it with pytest or unittest):

```python
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule


class MinStackMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.sut = MinStack()        # system under test
        self.model = []              # obviously correct, slow reference

    @rule(x=st.integers(-10, 10))
    def push(self, x):
        self.sut.push(x)
        self.model.append(x)

    @precondition(lambda self: self.model)
    @rule()
    def pop(self):
        assert self.sut.pop() == self.model.pop()

    @precondition(lambda self: self.model)
    @invariant()
    def same_min(self):
        assert self.sut.get_min() == min(self.model)


TestMinStack = MinStackMachine.TestCase
```

With the correct `MinStack` from the augmentation card this passed 300 examples of up to 40 steps; with the buggy one it failed every time and printed a three-step program, either the one in the trace or, in another run, push(-1), pop(), push(0). Shrinking finds *a* minimal failure, not always the same one. The plain harness, run on the buggy stack with seed 0, returned the six-step log push(3), push(-2), pop(), push(2), pop(), get_min() -> -2, expected 3.

## Pitfalls

- **A clever model.** If the model shares code or tricks with the structure, it shares its bugs. Make it slow and obvious.
- **A key space that is too large.** With keys up to 10^9, two operations almost never touch the same key, and update and eviction bugs never show. Use 5 to 10 keys.
- **Only capacity 1.** Many recency and frequency bugs need at least two entries to compete: the planted "update does not refresh recency" LRU bug passed every run at capacity 1 and failed at capacities 2 and 3.
- **Comparing random results by value.** For get_random, check membership and frequencies, not equality with the model.
- **Real time inside the structure.** Limiters and expiring caches must take the clock as an argument or an injected function, so tests can control time instead of sleeping.

## Check yourself

Q: Your LRU stress test uses capacity 1 and keys from 0 to 1,000,000, and it has never failed. Why is that weak evidence, and what two changes would you make?
A: With capacity 1 every put evicts the only other entry, so recency order never matters and ordering bugs cannot show; with a million keys, repeated keys (updates and hits on existing entries) almost never happen. Use capacities 1 to 3 and keys 0 to 6 so that updates, hits and evictions interleave constantly.

Q: Hypothesis reports a failing LFU run of six steps: put(1, 0), put(0, 0), get(0), get(1), put(2, 0), get(0). The model returns -1 for the last get, your cache returns 0. Capacity is 2. What is the bug?
A: At put(2, 0) both keys have count 2 and key 0 was used less recently, so the model evicts 0. Your cache kept 0, so it must have evicted 2 itself: it inserted the new key into bucket 1 before evicting from the minimum bucket, which by then was bucket 1 containing only the new key. Evict first, then insert.

Q: Why should the test compare return values and also check invariants after every operation?
A: Some bugs corrupt internal state without changing any return value yet, for example a dict entry left behind on eviction. An invariant check (dict size equals list length, size at most capacity) catches the corruption at the step where it happens, so the shrunk example ends at the faulty operation instead of many steps later when a wrong value finally surfaces.

## Lab

- **432 All O`one Data Structure.** Before submitting, test your class against a model built on `collections.Counter` (max and min by scanning the counter), with five keys and random inc and dec calls (dec only on present keys). Expected: 3,000 random runs of 60 operations pass, checking that the returned max and min keys have the model's maximum and minimum counts (several keys can tie, so compare counts, not keys).
- **460 LFU Cache.** Write a Hypothesis state machine with get and put rules over keys 0 to 4 and capacity 2, against a model that scans for the smallest (count, last use). Expected: the correct cache passes 500 examples; with the insert-then-evict bug planted, Hypothesis prints a six-step failing program like the one in the second question above.

> [!know]
> You now know how to test any stateful structure against a slow model with random operations, and how Hypothesis shrinks a failure to a minimal program.

=== lab | LRU cache, tested and measured | 45 min
goal: Build two LRU caches, prove them equal to a model with a Hypothesis state machine, catch a planted bug, and measure hit rate and latency on a skewed access trace

Real caches are judged by two numbers: how often they hit and how long each request takes. This lab makes you produce both, but only after a test has convinced you the cache is correct.

## Steps

1. In `lru.py`, write `LRUCache` (dict plus circular doubly linked list with a sentinel) and `OrderedLRU` (OrderedDict) from the LRU card, with `get(key)` returning -1 on a miss and `put(key, value)`.
2. Write `ModelLRU`: a list of [key, value] pairs, most recent first, where get and put scan the list. It is O(capacity) per call and obviously correct.
3. In `test_lru.py`, write a `RuleBasedStateMachine` with a `get` rule and a `put` rule over keys 0 to 6 and values 0 to 99, and an invariant that the cache never holds more than `capacity` keys and holds as many keys as the model. Build one machine per class and capacity (1, 2 and 3) and run them with `max_examples=500`.
4. Plant a bug: subclass `LRUCache` so that `put` on an existing key updates the value but does not move the node to the front. Run the machines again and read the shrunk failing program.
5. Generate a skewed trace: 200,000 requests over 10,000 keys drawn from a Zipf distribution with exponent s = 1.0 (weights 1/rank^s; use `itertools.accumulate` on the weights and `bisect` on a uniform random number, with `random.Random(42)`, and shuffle the key names so popular keys are not simply the small numbers).
6. Replay the trace through each cache (on a miss, put the key) for capacities 10, 100, 1000 and 5000, and record the hit rate. Repeat for s = 0.8 and s = 1.2.
7. Time 200,000 requests at capacity 1000 for `LRUCache`, `OrderedLRU` and a function wrapped in `functools.lru_cache(maxsize=1000)`, taking the best of three runs with `time.perf_counter`, and report nanoseconds per request.
8. Write three sentences: which implementation you would ship in Python, how hit rate depends on capacity and skew, and what the planted bug taught you about test parameters.

## What you should see

- Both correct caches pass every machine. The planted bug **passes at capacity 1** (with one slot, recency never matters) and **fails at capacities 2 and 3**, with a shrunk program of five or six steps such as put(0), put(2), put(0), put(1), get(0): the cache evicted 0 although it had just been updated.
- Hit rates (measured for this lab; your exact numbers will differ slightly with the generator):

| Capacity | s = 0.8 | s = 1.0 | s = 1.2 |
|---|---|---|---|
| 10 | 0.03 | 0.13 | 0.34 |
| 100 | 0.16 | 0.39 | 0.66 |
| 1000 | 0.43 | 0.67 | 0.86 |
| 5000 | 0.78 | 0.89 | 0.95 |

  Both of your implementations give identical hit rates, because they make identical eviction decisions. Hit rate rises with capacity with diminishing returns, and a more skewed trace (larger s) hits far more often at small capacities.
- Latency: on the machine used to write this lab, about 1.5 µs per request for the hand-written linked list, 0.5 µs for `OrderedLRU` and 0.4 µs for `functools.lru_cache`. Expect the same order on yours: identical O(1) complexity, but the C implementations are three to four times faster than pure Python pointer updates. Ship `OrderedDict` or `functools.lru_cache` in Python; write the linked list when the language or the interview requires it.

=== practice
- 705 core
  cue: You must build a set of integers without any built-in hash table, and keys go up to a million.
  hint: Split the keys into many small groups by a cheap function of the key, so each operation looks at one small group only.
  insight: An array of m buckets indexed by key % m, each a short list (chaining). With n keys spread evenly a bucket holds about n/m keys, so add, remove and contains are O(1 + n/m) expected. Because keys are bounded by 10^6, a bytearray of 10^6 + 1 flags is an O(1) worst-case alternative using 1 MB.
  cost: O(1 + n/m) expected per operation, O(m + n) space
  pattern: design-compose
- 933 core
  cue: Each call brings a later timestamp and asks how many calls fell in the last 3000 ms, inclusive.
  hint: Once a timestamp is too old for the current call, can it ever matter again?
  insight: Times only increase, so a timestamp that falls out of [t - 3000, t] is out forever. Append t to a deque and pop from the left while the front is below t - 3000; the deque length is the answer. Each timestamp is appended once and popped once.
  cost: O(1) amortised per call, O(calls in the window) space
  pattern: design-ratelimit
- 622 core
  cue: A queue with a fixed capacity, no resizing, and O(1) enqueue and dequeue at opposite ends.
  hint: Store elements in a fixed array and let the positions wrap around the end. What is the least state you need to know where the front and the back are?
  insight: Keep head and size. The front is buf[head], the rear is buf[(head + size - 1) % k], enqueue writes at (head + size) % k, dequeue advances head = (head + 1) % k. Keeping size rather than a tail index removes the full-or-empty ambiguity when head equals tail.
  cost: O(1) per operation, O(k) space
  pattern: design-ratelimit
- 1396 core
  cue: Check-in and check-out events, and queries for an average trip time between two named stations.
  hint: List what each query needs to know. Does the average need every individual trip?
  insight: Two dicts: rider -> (start station, time) for open trips, and (start, end) -> [total time, count] for finished ones. Check-out pops the open trip and adds its duration to the pair; the average is total / count. Store aggregates, not the trips.
  cost: O(1) per operation, O(riders inside + station pairs) space
  pattern: design-compose
- 146 core
  cue: A fixed-capacity key-value store whose get and put must both be O(1), evicting the entry unused for the longest time.
  hint: One structure finds keys; another keeps recency order and can move or remove any entry in O(1) if you can reach it directly. How does the first give you direct access into the second?
  insight: A dict from key to node of a doubly linked list kept in recency order around a sentinel. get and put move the node to the front; eviction removes root.prev and deletes its key, which is why nodes store their keys. A put on an existing key is a use and must move the node too.
  cost: O(1) per operation, O(capacity) space
  pattern: design-lru
- 380 core
  cue: A set that must also return a uniformly random element, with insert, remove and random all O(1) on average.
  hint: Random choice in O(1) needs positions 0..n-1 with no gaps. How can you delete from the middle of an array without shifting everything?
  insight: A list of values plus a dict from value to index. To remove x, move the last value into x's slot, update that value's index, and pop the end; if x is the last element, just pop. random.choice on the list is then uniform.
  cost: O(1) average per operation, O(n) space
  pattern: design-augment
- 284 core
  cue: Wrap an existing iterator and add a method that shows the next element without consuming it.
  hint: The underlying iterator cannot un-read an element. What could you hold on to?
  insight: Keep one element of lookahead in a field, read in the constructor. peek returns it, next returns it and reads the following one, hasNext checks whether the field holds a real element (use a private sentinel for exhausted, not None).
  cost: O(1) per call, O(1) extra space
  pattern: design-iterator
- 2034 derive
  cue: Price records arrive with timestamps, a later record may correct an earlier timestamp, and you are asked for the latest, maximum and minimum price.
  hint: A heap cannot change an entry in the middle. What if you never change entries, and instead learn to recognise the outdated ones when they reach the top?
  insight: A dict timestamp -> price is the truth, plus the largest timestamp seen. Push (price, time) onto a min-heap and (-price, time) onto a max-heap on every update. To answer, pop heap tops whose price disagrees with the dict (they were corrected later); the first top that agrees is the answer. Each entry is popped at most once.
  cost: O(log n) amortised per operation, O(n) space
  pattern: design-versioned
- 460 derive
  cue: Evict the least frequently used key, breaking ties by least recent use, with get and put both O(1).
  hint: A heap ordered by (count, last use) is O(log n). Use counts change by exactly one: where does a key move when it is used, and how can the smallest count change?
  insight: key -> value, key -> count, and count -> OrderedDict of keys in recency order, plus min_freq. A use moves a key from bucket f to f + 1 and, if bucket f empties and was the minimum, sets min_freq = f + 1. A new key goes to bucket 1 and sets min_freq = 1. Evict popitem(last=False) from bucket min_freq before inserting.
  cost: O(1) per operation, O(capacity) space
  pattern: design-lfu
- 432 core
  cue: Counts per key go up and down by one, and you must report a key with the maximum and a key with the minimum count, all in O(1).
  hint: A key only ever moves to the bucket of a neighbouring count. What structure keeps buckets in count order and lets you add or remove a bucket next to a known one in O(1)?
  insight: A doubly linked list of buckets in increasing count order (with head and tail sentinels), each holding a set of keys, plus key -> bucket. inc and dec move the key to the neighbouring bucket, creating it if the next count is missing and unlinking buckets that become empty. Min is head.next, max is tail.prev.
  cost: O(1) per operation, O(number of keys) space
  pattern: design-lfu
- 381 stretch
  cue: Like insert, delete and getRandom in O(1), but the same value can be inserted several times and getRandom must weight values by multiplicity.
  hint: Keep the array-plus-index-map design. What does the map have to store now that a value can sit at several positions?
  insight: A list of values plus a dict value -> set of indices. To remove x, take any index i of x, move the last element (at index n - 1) into slot i, replace n - 1 by i in that element's index set (careful when it is x itself), and pop. random.choice on the list weights by multiplicity automatically.
  cost: O(1) average per operation, O(n) space
  pattern: design-augment
- 2276 stretch
  cue: Intervals are added one by one, and after any add you may be asked how many distinct integers are covered.
  hint: Recounting is too slow. Keep the covered set in a shape where each add changes it locally, and keep the answer up to date as you go.
  insight: Keep disjoint, sorted intervals and a running total. On add(l, r), find with bisect all intervals that overlap or touch [l, r], subtract their lengths, replace them by their union, and add its length. Each interval is merged away at most once, so merging is amortised; count() returns the stored total.
  cost: O(log n) amortised search per add (plus the list splice), O(1) per count, O(n) space
  pattern: design-augment
