---
key: hashing
name: Hash tables, sets and counting
stage: contain
summary: How hash tables give expected O(1) lookups, what CPython's dict and set really do underneath, and the complement, counting, grouping and seen-set patterns built on them.
why: Hash maps are the most used data structure in software. Python resolves module globals and class attributes through dicts; caches, symbol tables, database hash joins, deduplication and routing tables are hash tables. In problem solving a dict or set is usually the first optimisation you reach for: it turns "search everything I have seen" from O(n) into O(1) and many O(n²) pair searches into a single pass. Knowing the internals (load factor, probing, tombstones, the hash and equality contract) tells you when that O(1) holds, when it degrades to O(n), and when sorting or a plain array is the better tool.
outcomes:
- Trace inserts, lookups and deletes in chaining and linear-probing tables, including tombstones and a resize
- Explain CPython's compact ordered dict, its perturbed probe sequence and 2/3 load limit, and how set differs
- Apply the hash and equality contract: which objects can be keys, and why lists cannot
- Solve pair and complement problems in one pass by looking up before inserting
- Count and group with Counter, defaultdict and canonical keys
- Choose between hashing, sorting and direct-address arrays, and recognise inputs that make hashing degrade
cues:
- "Have I seen this before?", duplicates, or a membership test inside a loop
- Find a pair (or count pairs) whose sum, difference or combination hits a target, in unsorted input, often with indices required
- Group or count items that are "the same" up to rearrangement, scaling or formatting
- A brute force that, for each element, scans the earlier elements for a partner
- Order does not matter and no range, nearest-value or sorted-output queries are needed
traps:
- Inserting the current element before looking up its complement, so it pairs with itself
- Using a list or another mutable object as a key, or mutating an object while it is a key
- Reading a `defaultdict` to test membership, which silently inserts the key
- Assuming dict and set operations are O(1) in the worst case, or that set iteration order is stable between runs
- Grouping ratios by float division instead of an exact canonical key such as a reduced fraction
systems:
- CPython's compact dict (Objects/dictobject.c) backs module globals, class namespaces and keyword arguments passed as `**kwargs`; set is a separate table (Objects/setobject.c) that mixes linear and perturbed probing
- Swiss tables (Abseil `flat_hash_map`, Rust's standard `HashMap`, Go maps since 1.24) keep 7 hash bits per slot in a control byte and test a group of 8 or 16 slots with one SIMD or bitwise comparison
- Redis keeps its keyspace in a chained hash table that rehashes incrementally, moving a few buckets per operation into a second table, so no single command pays for a full resize
- PostgreSQL hash indexes store 32-bit hash codes and can only answer equality; ranges and ORDER BY need a B-tree
further:
- Notes · 20 min | MIT 6.006 lecture 4 notes: hashing (direct access arrays, chaining, universal hashing) | https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/ce9e94705b914598ce78a00a70a1f734_MIT6_006S20_lec4.pdf
- Source · 15 min | CPython: Objects/dictnotes.txt, design notes on dict use cases and tuning | https://github.com/python/cpython/blob/main/Objects/dictnotes.txt
- Article · 15 min | Abseil: Swiss tables design notes (H1 and H2 hashes, metadata groups) | https://abseil.io/about/design/swisstables
- Article · 15 min | Go blog: Faster Go maps with Swiss Tables | https://go.dev/blog/swisstable
- Visualisation · 10 min | VisuAlgo: hash table (linear probing, quadratic probing, double hashing, chaining) | https://visualgo.net/en/hashtable
bank: arrays
---

=== recap | Hash tables: chaining, probing, tombstones and resizing | 12 min
goal: Trace inserts, lookups and deletes in a chaining or linear-probing table, and explain why tables resize at a fixed load factor
link: Wikipedia: Hash table, load factor | https://en.wikipedia.org/wiki/Hash_table#Load_factor | 5 min: 'Load factor', then 'Separate chaining' and 'Open addressing' under collision resolution
link: Wikipedia: Linear probing, deletion | https://en.wikipedia.org/wiki/Linear_probing#Deletion | 3 min: why an emptied slot breaks later lookups, and the two fixes (tombstones or shifting keys back)

> [!key]
> A hash table maps a key to a slot with `hash(key) % m` and stores the entry there. Collisions go either into a per-slot list (**chaining**) or to the next free slot along a probe sequence (**open addressing**), where a delete must leave a **tombstone**. Keep the **load factor** α = n / m below a constant and a lookup inspects O(1) slots on average; when α passes the limit, build a bigger table and re-insert everything: O(n) once, O(1) amortised.

## Internals

- **Direct addressing first.** If the keys are small integers 0..m-1, an array indexed by key is a perfect table with O(1) worst case. Hashing squeezes a huge key space (strings, tuples, 64-bit ints) into m slots, so different keys can collide.
- **Chaining.** Each slot holds a list. With a uniform hash the expected bucket length is α, so a miss compares about α keys and a hit about 1 + α/2. It tolerates α > 1 but spends a pointer per node and has poor locality. C++ `std::unordered_map` and Java's `HashMap` chain.
- **Linear probing.** On a collision try i + 1, i + 2, ... (mod m). It is cache-friendly, but runs of occupied slots (clusters) grow and merge. Knuth's estimates: ½(1 + 1/(1 - α)) slots per hit and ½(1 + 1/(1 - α)²) per miss, that is 1.5 and 2.5 at α = 1/2, 2 and 5 at α = 2/3, but 5.5 and 50.5 at α = 0.9. That cliff is why open-addressing tables resize well before they are full.
- **Deletion.** Emptying a slot would cut the probe path of every key that collided there and moved on: lookups would stop early and miss them. So a delete writes a **tombstone**. Lookups walk past it; inserts may reuse it once they know the key is not further along. Tombstones count towards the load, and the next resize drops them.
- **Resizing.** When live keys plus tombstones pass the limit, allocate a table sized from the live count and re-insert. The geometric-series argument from dynamic arrays makes n inserts O(n) in total. The template keeps the table at most half full after a resize; CPython's dict picks the smallest power of two at least 3 × the live count.
- **Table size.** With m a power of two, `% m` keeps only the low bits of the hash, so keys that agree in their low bits collide. Real tables use a strong hash (SipHash for Python strings), mix in the high bits (CPython's perturbation), or use a prime m.

## Template

```python
EMPTY, TOMB = object(), object()


class LinearProbeMap:
    """Open addressing with linear probing, tombstones, and a resize above 2/3 full."""

    def __init__(self, m=8):
        self.slots = [EMPTY] * m       # EMPTY, TOMB or a (key, value) pair
        self.n = 0                     # live keys
        self.used = 0                  # live keys + tombstones

    def _find(self, key):
        """Return (slot holding key or None, first reusable slot on key's probe path)."""
        m = len(self.slots)
        i, free = hash(key) % m, None
        while True:                    # ends: the load limit keeps an EMPTY slot
            s = self.slots[i]
            if s is EMPTY:
                return None, (i if free is None else free)
            if s is TOMB:
                if free is None:
                    free = i
            elif s[0] == key:
                return i, None
            i = (i + 1) % m

    def get(self, key, default=None):
        i, _ = self._find(key)
        return default if i is None else self.slots[i][1]

    def put(self, key, value):
        i, free = self._find(key)
        if i is not None:
            self.slots[i] = (key, value)
            return
        if self.slots[free] is EMPTY:
            self.used += 1
        self.slots[free] = (key, value)
        self.n += 1
        if 3 * self.used > 2 * len(self.slots):
            self._resize()

    def delete(self, key):
        i, _ = self._find(key)
        if i is None:
            raise KeyError(key)
        self.slots[i] = TOMB
        self.n -= 1

    def _resize(self):
        live = [s for s in self.slots if s is not EMPTY and s is not TOMB]
        m = 8
        while m < 2 * len(live):       # at most half full afterwards
            m *= 2
        self.slots, self.n, self.used = [EMPTY] * m, 0, 0
        for key, value in live:
            self.put(key, value)
```

## Worked example

Small ints hash to themselves, so key k starts at slot k % 8.

```steps
Insert 3, 11, 19 and 6: the first three all want slot 3, so they take 3, 4 and 5; 6 takes slot 6
    slot     0   1   2   3   4   5   6   7
    key      .   .   .   {{3  11  19}}   6   .      n 4  used 4
---
Delete 11: slot 4 becomes a tombstone, not empty
    slot     0   1   2   3   4   5   6   7
    key      .   .   .   3 {{DEL}}  19   6   .      n 3  used 4
---
Get 19: slot 3 holds 3, slot 4 is a tombstone so keep going, slot 5 holds 19. An empty slot 4 would have ended the search and reported 19 missing
    slot     0   1   2   3   4   5   6   7
    key      .   .   .   {{3 DEL  19}}   6   .
---
Put 27 (27 % 8 = 3): walk 3, DEL (remember slot 4), 19, 6, then the empty slot 7 proves 27 is absent, so reuse slot 4
    slot     0   1   2   3   4   5   6   7
    key      .   .   .   3  {{27}}  19   6   .      n 4  used 4
---
Put 12 (12 % 8 = 4): slots 4, 5 and 6 are taken, so it lands in 7, three slots from home: the cluster grew
    slot     0   1   2   3   4   5   6   7
    key      .   .   .   3  27  19   6  {{12}}      n 5  used 5
---
Put 1 into slot 1: used = 6 and 3 x 6 > 2 x 8, so resize to 16 slots (smallest power of two >= 2 x 6) and re-insert in slot order
    slot    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    key     .  {{1}}  .  {{3 19}}  .  {{6}}  .  .  .  . {{27 12}}  .  .  .
```

After the resize, 27 and 12 have moved away from the cluster and 19 sits one slot from home.

## Pitfalls

- Deleting by emptying the slot. Lookups then fail only after collisions, so small tests rarely catch it.
- Leaving tombstones out of the load count: a table full of tombstones has no empty slot, and a search for an absent key never stops.
- Resizing to `2 * m` regardless of the live count makes a delete-heavy table grow without bound; size from the live keys.
- Iteration order of a plain hash table is slot order: arbitrary, and it changes at every resize.

## Quick check

Q: In the table just before the resize (slots 3 to 7 hold 3, 27, 19, 6, 12), how many slots does a lookup of 35 inspect, and what does it return?
A: Six: 35 % 8 = 3, so it checks slots 3, 4, 5, 6 and 7, all occupied by other keys, then wraps to slot 0, which is empty, and returns "absent". A long cluster makes misses expensive, exactly as the ½(1 + 1/(1 - α)²) estimate predicts.

> [!know]
> You now know how chaining and linear probing store and find keys, why deletes need tombstones, and why a table resizes at a fixed load factor.

=== recap | Inside CPython's dict and set | 12 min
goal: Explain CPython's compact ordered dict, its perturbed probing and 2/3 load limit, the hash and equality contract, and how set differs
link: CPython source: Objects/dictobject.c | https://github.com/python/cpython/blob/main/Objects/dictobject.c | 10 min: the layout comment at the top of the file, then search for 'Major subtleties ahead' to read why the probe sequence brings in the high bits of the hash
link: Raymond Hettinger: More compact dictionaries with faster iteration (python-dev, 2012) | https://mail.python.org/pipermail/python-dev/2012-December/123028.html | 5 min: the whole short proposal, with the old and new memory layouts side by side

> [!key]
> A CPython dict is two arrays: a sparse **index table** of small integers (a power of two in size, at most 2/3 full) and a dense **entries** array of (hash, key, value) in insertion order. A lookup probes the index table with `i = (5*i + 1 + perturb) & mask`, shifting the hash's high bits in through `perturb`, and confirms a match by identity, then stored hash, then `==`. That layout is why dicts keep insertion order (guaranteed since 3.7), stay compact and iterate fast.

## Internals

```text
d = {10: "a", 3: "b", 18: "c"}            small ints hash to themselves

indices (8 slots, 1 byte each)            entries (dense, insertion order)
slot   0   1   2   3   4   5   6   7        0: (hash 10, 10, "a")
      [2, -1,  0,  1, -1, -1, -1, -1]       1: (hash  3,  3, "b")
                                            2: (hash 18, 18, "c")
-1 empty, -2 deleted (tombstone), n >= 0 position in entries
```

- **Compact layout (3.6+).** Index slots are 1 byte wide for tables up to 128 slots, 2 bytes up to 2^15, then 4 or 8, where the old layout spent a 24-byte (hash, key, value) record on every slot, used or not. The 3.6 release notes report 20% to 25% less memory. Iteration walks the dense entries: no empty slots to skip, and insertion order for free.
- **Load and growth.** A new dict has 8 index slots and room for 5 entries (`USABLE_FRACTION` is 2/3). When the entries run out, the table is rebuilt at the smallest power of two at least 3 × the live count (`GROWTH_RATE`), so it doubles when nothing was deleted. A delete writes -2 into the index slot and leaves a hole in the entries; both vanish at the next rebuild.
- **Probing.** Start at `hash & mask`, then repeat `perturb >>= 5; i = (5*i + perturb + 1) & mask`. The 5i + 1 recurrence alone visits every slot of a power-of-two table; `perturb` feeds in the high bits, so keys that share their low bits (multiples of 2^16, say) split up within a few probes instead of piling into one cluster. Consecutive int keys land in consecutive slots with no collisions at all.
- **The contract.** Lookups compare `is` first, then the stored hash, then `==`. So equal objects must have equal hashes, and a key's hash must not change while it is in a dict. That is why `list`, `dict` and `set` are unhashable (use `tuple` or `frozenset`), why a class that defines `__eq__` without `__hash__` becomes unhashable, and why a frozen dataclass is a safe key.
- **Hash values.** `hash(-1)` is -2 (-1 signals an error in C); ints hash modulo 2^61 - 1; `1`, `1.0` and `True` are equal and hash alike, so they are one key. `str` and `bytes` use SipHash-1-3 (since 3.11) with a random per-process seed unless `PYTHONHASHSEED` is set, and a string caches its hash.
- **set** (Objects/setobject.c) is a different table: (key, hash) entries with no insertion order, and each probe also checks up to 9 adjacent slots before jumping with the same perturbation, because neighbouring slots are cheap to read and membership tests miss as often as they hit. It resizes when 60% of its slots (deleted ones included) are in use.

## Template

```python
from dataclasses import dataclass


def probe_slots(h, mask, count):
    """The first `count` index slots CPython's dict tries for hash h."""
    perturb = h & 0xFFFF_FFFF_FFFF_FFFF        # unsigned, as in C
    i = perturb & mask
    out = []
    for _ in range(count):
        out.append(i)
        perturb >>= 5
        i = (i * 5 + perturb + 1) & mask
    return out


@dataclass(frozen=True)
class Point:                 # hashable value object: __eq__ and __hash__ come from the fields
    x: int
    y: int
```

## Worked example

These index tables were read out of a real CPython 3.12 dict's memory, so this is exactly what the interpreter does.

```steps
Insert 10 and 3: slots 10 & 7 = 2 and 3 & 7 = 3 are free
    slot        0   1   2   3   4   5   6   7
    indices  [ -1, -1,  {{0}},  {{1}}, -1, -1, -1, -1 ]
    entries  0: 10   1: 3
---
Insert 18: slot 18 & 7 = 2 holds 10. perturb = 18 >> 5 = 0, so next is (5*2 + 1) & 7 = 3: holds 3. Next (5*3 + 1) & 7 = 0: empty
    slot        0   1   2   3   4   5   6   7
    indices  [  {{2}}, -1,  0,  1, -1, -1, -1, -1 ]
    entries  0: 10   1: 3   {{2: 18}}
---
del d[3]: index slot 3 becomes -2 and entry 1 becomes a hole; the dict does not get that entry space back until it is rebuilt
    slot        0   1   2   3   4   5   6   7
    indices  [  2, -1,  0, {{-2}}, -1, -1, -1, -1 ]
    entries  0: 10   {{1: hole}}   2: 18
---
Look up 18: slot 2 gives entry 0 (hash 10, no), slot 3 is -2 so keep going, slot 0 gives entry 2 (hash 18, key 18): found in 3 probes
    slot        0   1   2   3   4   5   6   7
    indices  [  {{2}}, -1,  {{0}}, {{-2}}, -1, -1, -1, -1 ]
---
Insert 26: slot 2 is taken, the next slot 3 is a tombstone and is reused; the entry is appended, so iteration gives 10, 18, 26
    slot        0   1   2   3   4   5   6   7
    indices  [  2, -1,  0,  {{3}}, -1, -1, -1, -1 ]
    entries  0: 10   1: hole   2: 18   {{3: 26}}
```

## Pitfalls

- Mutating an object after using it as a key (a custom class that hashes mutable fields): the entry stays under the old hash and lookups miss it.
- `d[1]`, `d[1.0]` and `d[True]` are the same entry.
- `float("nan")` is not equal to itself, so a NaN key is found only through the very same object.
- Adding or removing keys while iterating raises `RuntimeError`; iterate over `list(d)` instead.
- String hashes change between runs. Never store `hash()` values or use them to split data across processes; use `hashlib` or `zlib.crc32` for a stable hash.

## Quick check

Q: What does `{1: "a", True: "b", 1.0: "c"}` evaluate to, and why?
A: `{1: 'c'}`. The three keys compare equal and hash alike, so they are one entry: the first key object, 1, is kept, and the value is overwritten twice.

> [!know]
> You now know how CPython's dict and set store and find keys, why dicts are ordered, and which objects can be keys.

=== recap | The complement pattern: look up before you insert | 10 min
goal: Find or count pairs that combine to a target in one pass by keeping a map of the prefix and querying it before inserting
tag: hashing-complement | Complement lookup in one pass
practice: 1, 454, 2131

> [!key]
> To find pairs that combine to a target, keep a map of what you have already seen and, for each new element, ask the map for its **complement before inserting** the element. The map describes the prefix a[:i], so an element never pairs with itself and every pair is found exactly once, when its later member arrives. O(n) expected time and O(n) space instead of O(n²) pairs.

## Internals

- **Invariant.** Before processing index i, `seen` maps every value in a[:i] to what you need about it: its index (to return positions), its count (to count pairs), or its first index (to measure distances).
- **What the complement is** depends on the combination: `target - x` for sums, `x - k` and `x + k` for a difference k, `target ^ x` for XOR, the reversed string for "concatenation reads the same backwards", a canonical form for "matches up to rearrangement".
- **Why one pass suffices.** A pair (j, i) with j < i is examined exactly once: when the scan reaches i, a[j] is already in the map. Looking up before inserting is what excludes j = i.
- **Counting versus finding.** With counts, each arrival adds `seen[complement]` pairs, which also handles duplicates: three equal partners already seen means three new pairs.
- **The alternative.** Sort, then walk two pointers inwards: O(n log n) time and O(1) extra space, but original indices are lost unless you sort (value, index) pairs. Prefer it when memory is tight or the input is already sorted.
- **Python details.** `Counter` returns 0 for a missing key without inserting it; `defaultdict(int)` inserts the key on every read, so a complement probe adds junk keys (memory grows, and iterating the map later shows them). `dict.get(k)` never inserts.

## Template

```python
from collections import Counter


def pair_indices(a, target):
    """Indices (j, i), j < i, with a[j] + a[i] == target, or None."""
    seen = {}                                  # value -> index, for a[:i]
    for i, x in enumerate(a):
        j = seen.get(target - x)
        if j is not None:
            return j, i
        seen[x] = i
    return None


def count_pairs(a, target):
    """Number of index pairs j < i with a[j] + a[i] == target."""
    seen, pairs = Counter(), 0
    for x in a:
        pairs += seen[target - x]              # Counter: a missing key reads as 0
        seen[x] += 1
    return pairs
```

## Worked example

`count_pairs([4, 5, 1, 4, 5, 5], 9)`:

```steps
x = 4 needs 5: none seen yet, pairs stay 0; then record the 4
    a     {{4}}  5  1  4  5  5
    seen  {4: 1}                       pairs 0
---
x = 5 needs 4: one 4 seen, so +1; record the 5
    a     4  {{5}}  1  4  5  5
    seen  {4: 1, 5: 1}                 pairs {{1}}
---
x = 1 needs 8: none; record the 1
    a     4  5  {{1}}  4  5  5
    seen  {4: 1, 5: 1, 1: 1}           pairs 1
---
x = 4 needs 5: one 5 seen, +1; now two 4s
    a     4  5  1  {{4}}  5  5
    seen  {4: 2, 5: 1, 1: 1}           pairs {{2}}
---
x = 5 needs 4: two 4s seen, +2
    a     4  5  1  4  {{5}}  5
    seen  {4: 2, 5: 2, 1: 1}           pairs {{4}}
---
x = 5 needs 4: two 4s seen, +2; done in one pass
    a     4  5  1  4  5  {{5}}
    seen  {4: 2, 5: 3, 1: 1}           pairs {{6}}  (two 4s x three 5s)
```

## Pitfalls

- Inserting before looking up: with target 6 and a 3 in the array, the 3 matches itself.
- Overwriting the stored index for duplicates is harmless when you return the first pair found, but wrong when you need, say, the earliest partner: decide what the map must remember.
- Counting unordered value pairs ("how many distinct pairs of values") is a different question from index pairs; you then need a set of pairs or a sorted pass.
- In C++ or Java, `target - x` can overflow 32-bit ints with values near the limits; Python ints cannot overflow.

## Quick check

Q: How do you count index pairs j < i with |a[i] - a[j]| == k in one pass?
A: Keep a Counter of a[:i]; for each x add `seen[x - k] + seen[x + k]` (only `seen[x]` once if k == 0), then record x. Each pair is counted once, when its later element arrives.

> [!know]
> You now know how to turn a pair search into one pass with a map of the past, and why looking up before inserting is the line that makes it correct.

=== recap | Counting and grouping with canonical keys | 10 min
goal: Count with Counter, group with defaultdict, and design canonical keys so that items belong together exactly when their keys are equal
tag: hashing-group | Counting and canonical-key grouping
practice: 242, 49, 347, 2001, 554
link: Python docs: collections.Counter | https://docs.python.org/3/library/collections.html#collections.Counter | 5 min: most_common, the arithmetic operators and total(), and the note that counts may be zero or negative
link: Python docs: defaultdict examples | https://docs.python.org/3/library/collections.html#defaultdict-examples | 3 min: grouping with list, counting with int, and the setdefault equivalent

> [!key]
> Counting is a map from item to frequency; grouping is a map from a **canonical key** to a list. Choose the key so that two items belong together **exactly when** their keys are equal: sorted letters or a 26-count tuple for anagrams, a reduced fraction for equal ratios, a tuple of a row for equal rows. Keys must be hashable, so build tuples or strings, never lists.

## Internals

- **Counter** is a dict subclass. `Counter(iterable)` counts in a C loop; `most_common(k)` uses `heapq.nlargest` (O(n log k)) and `most_common()` sorts everything (O(n log n)). Missing keys read as 0 without being inserted. `c1 - c2` drops counts that fall to zero or below, `c1.subtract(c2)` keeps them, and since 3.10 two Counters are equal when they agree after treating missing keys as zero.
- **Pairs from counts.** A group of c equal keys contains c(c - 1)/2 unordered pairs; summing over groups counts all "equivalent pairs" in O(n), or add `seen[key]` on each arrival, the complement pattern with the item itself as its own complement.
- **Frequencies are small integers.** Every count lies in 1..n, so values can be bucketed by count in a list of n + 1 buckets: reading buckets from the top gives the most frequent values in O(n), no sorting.
- **Canonical keys.** `"".join(sorted(w))` costs O(k log k) per word; a tuple of 26 counts costs O(k + 26). For ratios w/h, `(w // g, h // g)` with `g = gcd(w, h)` is exact; `w / h` as a float happens to work while numbers stay small (correctly rounded division maps equal fractions to the same float), but it is fragile and fails for huge or approximate inputs. Normalise strings first if the problem says case or punctuation do not matter.
- **Grouping tools.** `defaultdict(list)` creates the list on first access; `d.setdefault(k, []).append(x)` does the same with a plain dict. `itertools.groupby` only groups **adjacent** equal keys, so it needs sorted input.

## Template

```python
from collections import defaultdict


def group_by(items, key):
    """Map key(x) -> list of items with that key, in input order."""
    groups = defaultdict(list)
    for x in items:
        groups[key(x)].append(x)
    return groups


def count_key(word):
    """Anagram key in O(len(word)): a tuple of 26 letter counts."""
    counts = [0] * 26
    for ch in word:
        counts[ord(ch) - ord("a")] += 1
    return tuple(counts)


def equivalent_pairs(items, key):
    """Number of unordered pairs of items with equal keys."""
    sizes = defaultdict(int)
    for x in items:
        sizes[key(x)] += 1
    return sum(c * (c - 1) // 2 for c in sizes.values())
```

## Worked example

Grouping `["pots", "stop", "opt", "tops", "top", "post"]` with the key `"".join(sorted(w))`:

```steps
"pots" has key "opst": a new group
    "opst": [pots]
---
"stop" also sorts to "opst"; "opt" starts a group with key "opt"
    "opst": [pots, {{stop}}]
    "opt":  [{{opt}}]
---
"tops" joins "opst", "top" joins "opt", "post" joins "opst"
    "opst": [pots, stop, {{tops}}, {{post}}]
    "opt":  [opt, {{top}}]
---
Two groups; the same input has equivalent_pairs = 4 x 3 / 2 + 2 x 1 / 2 = 7
    groups: [pots, stop, tops, post]   [opt, top]
```

## Pitfalls

- Using a list as a key (`TypeError: unhashable type: 'list'`): convert with `tuple(...)`.
- `itertools.groupby` on unsorted input splits one group into several.
- A `defaultdict` read inserts the key; test membership with `in`.
- A float ratio as a key: fine for small integers, wrong once values are large or come from measurements. Reduce the fraction instead.

## Quick check

Q: Rectangles (4, 8), (3, 6), (10, 20), (15, 30) and (2, 3): how many pairs have equal width-to-height ratios, and what key finds them?
A: Six. The key (w // g, h // g) with g = gcd(w, h) gives (1, 2) for the first four and (2, 3) for the last, so the count is 4 x 3 / 2 = 6.

> [!know]
> You now know how to count and group with Counter and defaultdict, and how to design a canonical key that makes "the same" mean "equal keys".

=== recap | Sets: membership, de-duplication and set algebra | 10 min
goal: Use sets for O(1) membership, first repeats and de-duplication, model several groups with tuple keys, and know what set operations cost
tag: hashing-set | Seen-sets and membership
practice: 217, 36, 128
link: Python docs: time complexity of set and frozenset | https://docs.python.org/3/builtins/time-complexity.html#set-frozenset | 3 min: the cost of membership, union, intersection and difference, and the worst-case note

> [!key]
> A set answers "have I seen this?" in O(1) expected time. Use one to stop at the first repeat, to de-duplicate, and to replace a nested membership scan with a lookup; give it **tuple keys** to track several groups at once; and use set algebra when the question is about whole collections. When the values are small integers, a plain boolean array is the same idea without hashing.

## Internals

- **Costs.** `x in s`, `add`, `discard` are O(1) on average. `s | t` is O(len(s) + len(t)); `s & t` iterates the smaller set, O(min(len(s), len(t))); `s - t` is O(len(s)); `s <= t` is O(len(s)). Building `set(a)` is O(n).
- **Order.** A set has no insertion order, and string elements come out in a different order on every run (hash randomisation). To de-duplicate while keeping the first-seen order, use `list(dict.fromkeys(a))`.
- **Memory.** `sys.getsizeof(set(range(10**6)))` is about 34 MB for the table alone, before counting the int objects; a `list` of the same ints needs 8 MB of pointers, and a `bytearray` of 10^6 flags 1 MB. When values are bounded, direct addressing wins.
- **Several groups at once.** A key such as `("row", r, value)` or `(r // 3, c // 3, value)` lets one set track membership for many groups. Each item is checked against each of its groups in O(1).
- **Hashable sets.** `frozenset` is immutable and hashable, so it can be a dict key or an element of another set (useful for "the set of letters in a word" as a key).
- **Thinking with membership.** O(1) membership often unlocks a different algorithm: instead of asking "which earlier element pairs with me?", you can ask "is my neighbour value present?", "has this state been visited?", "is this the start of something?". The question you ask the set is the design decision.

## Template

```python
def first_repeat(a):
    """First value that occurs a second time, scanning left to right, or None."""
    seen = set()
    for x in a:
        if x in seen:
            return x
        seen.add(x)
    return None


def dedupe_keep_order(a):
    return list(dict.fromkeys(a))


def conflicts(cells):
    """cells: (row, col, value) triples. Yield the cells that repeat a value in their row or column."""
    seen = set()
    for r, c, v in cells:
        keys = (("row", r, v), ("col", c, v))
        if any(k in seen for k in keys):
            yield r, c, v
        seen.update(keys)
```

## Worked example

`list(conflicts([(0, 0, 5), (0, 2, 7), (1, 0, 7), (1, 1, 5), (2, 0, 5)]))`:

```steps
(0, 0, 5): neither key is present; add ("row", 0, 5) and ("col", 0, 5)
    seen  {row0:5, col0:5}
---
(0, 2, 7) and (1, 0, 7): all four keys are new
    seen  {row0:5, col0:5, {{row0:7, col2:7, row1:7, col0:7}}}
---
(1, 1, 5): ("row", 1, 5) and ("col", 1, 5) are new: no conflict, even though 5 already appears in row 0
    seen  {..., {{row1:5, col1:5}}}
---
(2, 0, 5): ("col", 0, 5) is already present: column 0 holds two 5s, so this cell is reported
    conflicts: [{{(2, 0, 5)}}]
```

## Pitfalls

- `x in a_list` inside a loop is O(n) per test: convert to a set once, outside the loop.
- `set(a)` throws away multiplicities; use a Counter if counts matter.
- Relying on set iteration order, for output or for tie-breaking, gives results that change between runs.
- `{}` is an empty dict, not a set; write `set()`.

## Quick check

Q: You must report the values common to a list `small` of 10 items and a list `big` of 10^6 items, without duplicates. What is the cheapest expression, and what if `big` were already a set?
A: `set(small).intersection(big)`: given a non-set argument, CPython iterates over `big` once and tests each item against the 10-element set, so O(len(big)) time and O(10) extra memory. `set(small) & set(big)` does the same scan plus building a 10^6-element set (about 34 MB). If `big` is already a set, `set(small) & big` costs only O(10), because intersection iterates over the smaller set.

> [!know]
> You now know what sets cost, how to keep order when de-duplicating, and how tuple keys let one set track many groups.

=== recap | Hashing, sorting or an array? When hashing goes wrong | 10 min
goal: Choose between a hash map, sorting and a direct-address array for a task, and recognise inputs and keys that make hashing degrade
tag: hashing-tradeoffs | Hash map, sort or array?
practice: 229
link: Python docs: object.__hash__ | https://docs.python.org/3/reference/datamodel.html#object.__hash__ | 5 min: the contract (equal objects must hash equal), why __eq__ alone makes a class unhashable, and the note on hash randomisation and the denial of service it prevents

> [!key]
> Hashing gives expected O(1) per operation, but no order, an O(n) worst case per operation, and high memory per entry in Python. **Sort** instead when you need order, ranges, nearest values or a guaranteed bound; use a **plain array** when keys are small integers; and remember that an attacker who can choose keys can force collisions unless the hash is seeded.

## Internals

| Need | Hash map or set | Sorted list (+ bisect) | Direct-address array |
|---|---|---|---|
| Membership, counts | O(1) expected | O(log n) after O(n log n) sort | O(1) worst case |
| Order, ranges, nearest, kth | no | yes | only by scanning |
| Worst case | O(n) per operation | O(log n) per query | O(1) |
| Memory for 10^6 int keys | about 34 to 42 MB of table | 8 MB of pointers | 1 MB as a bytearray |
| Keys | any hashable | any comparable | integers in a small range |

- **Worst case.** If many keys share a hash, every insert scans all of them: n inserts cost O(n²). A class with a constant `__hash__` shows it: building a set of 1,000, 2,000 and 4,000 such objects took roughly 0.1, 0.5 and 2.4 seconds on CPython 3.12, against well under a millisecond for ints.
- **Hash flooding.** A 2011 advisory (oCERT-2011-003) showed that one HTTP POST request whose parameter names all collide can pin a web server's CPU, because the framework builds a dict from them in O(n²). Python responded with randomised string hashing (on by default since 3.3, SipHash since 3.4, SipHash-1-3 since 3.11). Integer hashes are not randomised: they are the value modulo 2^61 - 1, so untrusted integer keys can still be made to collide.
- **Other languages.** Since Java 8, `HashMap` turns a bucket that grows beyond 8 entries into a small balanced tree (once the table has at least 64 buckets), capping a flooded bucket at O(log n) for comparable keys. C++ `std::unordered_map` with libstdc++ hashes integers to themselves, so crafted inputs can make it quadratic.
- **When a map is not needed at all.** Small integer keys (letters, ages, values in 1..n) want a list of counts. "Is there a value occurring more than n / k times?" needs at most k - 1 candidates, not a full count table. Sorted data answers duplicates and counts with one scan of neighbours.

## Template

```python
from itertools import groupby


def counts_by_sorting(a):
    """(value, count) pairs in sorted order: O(n log n) time, no hashing."""
    return [(v, len(list(g))) for v, g in groupby(sorted(a))]


class BadKey:
    """Equal by value, but every instance has the same hash: watch a set degrade."""

    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, BadKey) and self.v == other.v

    def __hash__(self):
        return 42
```

## Worked example

Time `set(BadKey(i) for i in range(n))` for n = 1,000, 2,000 and 4,000. Each doubling of n multiplies the time by about 4 to 5: every insert compares the new key with all the earlier ones (they share one probe sequence), so the total is about n²/2 equality checks, 8 million at n = 4,000. The same sizes with plain ints stay under a millisecond. Swap `__hash__` to `return hash(self.v)` and the BadKey version drops back to linear time: the data did not change, only the hash.

## Pitfalls

- Promising O(1) in a latency-critical path where keys come from users: the bound is expected, not guaranteed.
- Persisting `hash()` values or relying on set order between runs: both change with the per-process seed.
- Reaching for a dict when the question needs order (top values, ranges, "next larger"): a sorted list or a heap answers it directly.
- Using a hash map where a 26-slot or n-slot list would do, paying hashing and memory for nothing.

## Quick check

Q: You need, for 10^5 timestamps, the number of events in many arbitrary windows [t1, t2]. Dict or sorted list?
A: Sort once and answer each window with `bisect_right(ts, t2) - bisect_left(ts, t1)`: O(n log n) to build and O(log n) per query. A hash map knows nothing about order, so it cannot answer ranges without scanning everything.

> [!know]
> You now know when hashing is the right tool, when sorting or an array beats it, and how collisions and hash flooding make it degrade.

=== lab | Probe lengths you can see | 40 min
goal: Measure average probes for hits and misses in linear-probing and chaining tables across load factors, compare them with theory, and watch crafted keys destroy a table
link: Open Data Structures 5.2: LinearHashTable | https://opendatastructures.org/ods-python/5_2_LinearHashTable_Linear_.html | 15 min: the del and null markers, the resize rule, and 5.2.1 'Analysis of Linear Probing'

Two minimal tables, no resizing, so the load factor is exactly what you choose. You will measure the cost of hits and misses as the table fills, compare with Knuth's formulas from the first recap, then break the table with keys chosen to collide. (This stage's project builds the full ordered dict; keep this lab small.)

## Steps

1. Save as `probes.py` and run it. Before running, write down your predictions for linear probing misses at load 0.5, 2/3 and 0.9.

```python
import random
import time


def lp_build(keys, m):
    """Linear probing into m slots, no resizing (keep len(keys) < m)."""
    table = [None] * m
    for k in keys:
        i = hash(k) % m
        while table[i] is not None:
            i = (i + 1) % m
        table[i] = k
    return table


def lp_probes(table, k):
    """Slots inspected until k is found or an empty slot proves it is absent."""
    m = len(table)
    i, probes = hash(k) % m, 1
    while table[i] is not None and table[i] != k:
        i = (i + 1) % m
        probes += 1
    return probes


def chain_build(keys, m):
    buckets = [[] for _ in range(m)]
    for k in keys:
        buckets[hash(k) % m].append(k)
    return buckets


def chain_probes(buckets, k):
    """Keys compared: k's position in its bucket if present, the whole bucket if absent."""
    b = buckets[hash(k) % len(buckets)]
    return b.index(k) + 1 if k in b else len(b)


def mean(xs):
    return sum(xs) / len(xs)


rng = random.Random(1)
m = 1 << 16
print(" load   LP hit  (theory)  LP miss  (theory)   chain hit  chain miss")
for load in (0.25, 0.5, 2 / 3, 0.8, 0.9):
    n = int(load * m)
    values = rng.sample(range(1 << 60), n + 5000)
    keys, absent = values[:n], values[n:]
    lp, ch = lp_build(keys, m), chain_build(keys, m)
    hits = rng.sample(keys, 5000)
    print(f"{load:5.2f}  {mean([lp_probes(lp, k) for k in hits]):7.2f}  ({(1 + 1 / (1 - load)) / 2:6.2f})"
          f"  {mean([lp_probes(lp, k) for k in absent]):7.2f}  ({(1 + 1 / (1 - load) ** 2) / 2:6.2f})"
          f"   {mean([chain_probes(ch, k) for k in hits]):9.2f}  {mean([chain_probes(ch, k) for k in absent]):10.2f}")
```

2. Add the crafted-keys experiment to the same file: 4,000 keys that are all multiples of the table size, so every key starts at slot 0. Time the build and the average hit cost, and build a real `dict` from the same keys for comparison.

```python
m, n = 1 << 13, 4000
random_keys = rng.sample(range(1 << 60), n)
bad_keys = [i * m for i in range(n)]            # all congruent to 0 mod m
for name, keys in (("random", random_keys), ("multiples of m", bad_keys)):
    t0 = time.perf_counter()
    table = lp_build(keys, m)
    t1 = time.perf_counter()
    d = dict.fromkeys(keys)
    t2 = time.perf_counter()
    print(f"{name:15} linear probing build {t1 - t0:6.3f} s, mean hit probes "
          f"{mean([lp_probes(table, k) for k in keys]):7.1f};  dict build {(t2 - t1) * 1000:.2f} ms")
```

3. Replace `hash(k) % m` in `lp_build` and `lp_probes` with CPython's probe sequence (the `probe_slots` idea from the dict recap: start at `h & mask`, then `perturb >>= 5; i = (5*i + perturb + 1) & mask`) and rerun step 2 with the multiples of m.
4. Optional: build a table at load 0.8, delete a random half of its keys by overwriting their slots with a tombstone object (`lp_probes` already walks past anything that is not `None` or the key), and measure misses again. Then build a fresh table from the surviving keys and compare.

## What you should see

Measured on CPython 3.12 (the probe counts are deterministic for this seed; times vary by machine):

| Load | LP hit (theory) | LP miss (theory) | Chain hit | Chain miss |
|---|---|---|---|---|
| 0.25 | 1.17 (1.17) | 1.39 (1.39) | 1.12 | 0.25 |
| 0.50 | 1.50 (1.50) | 2.53 (2.50) | 1.25 | 0.51 |
| 0.67 | 2.02 (2.00) | 5.00 (5.00) | 1.32 | 0.67 |
| 0.80 | 2.96 (3.00) | 12.14 (13.00) | 1.40 | 0.78 |
| 0.90 | 5.78 (5.50) | 55.86 (50.50) | 1.46 | 0.90 |

- Linear probing matches Knuth closely up to 2/3, then misses explode: about ten times more work going from 2/3 to 0.9 full. Chaining degrades gently (about 1 + α/2 per hit and α per miss) because buckets never merge, which is why chained tables can run at load 1 while open addressing stops near 2/3.
- With multiples of m, every key lands in one cluster: the build takes over a second (about 8 million probes) and a hit costs about 2,000 probes, against 1.5 for random keys. The real `dict` builds both key sets in about a millisecond, because perturbation brings the high bits of the hash into play after the first probe.
- With the perturbed sequence in step 3, your own table recovers too: the crafted keys spread out after a few probes, the build drops to about 10 ms (about 26,000 probes in total instead of 8 million) and a hit costs about 6 probes.
- In step 4, misses stay at about 12.5 probes, exactly as at load 0.8, although only 40% of the keys are live; a fresh table with the same keys needs about 1.9. A search cannot stop at a tombstone, so only a rebuild recovers the speed.

=== practice
- 217 core
  pattern: hashing-set
  cue: The only question is whether any value occurs twice; positions and order do not matter.
  hint: Comparing every pair is O(n²). What could you remember about the values you have already passed?
  insight: Scan once with a set: the first value already in the set is a duplicate. Equivalently, compare len(set(nums)) with len(nums). Sorting and checking neighbours also works in O(n log n) with O(1) extra space.
  cost: O(n) expected time, O(n) space
- 1 core
  pattern: hashing-complement
  cue: Exactly one pair of positions adds up to a target, the input is unsorted, and you must return the positions.
  hint: When you stand on x, the partner you need is fully determined. Where could you look it up instantly?
  insight: Keep a dict from value to index for the prefix. For each x, check whether target - x is already in it before inserting x, so an element never pairs with itself and the first match returns both indices.
  cost: O(n) expected time, O(n) space
- 242 core
  pattern: hashing-group
  cue: Two strings must use exactly the same letters the same number of times.
  hint: Positions do not matter, only how often each letter occurs.
  insight: Equal lengths and equal letter counts are necessary and sufficient. Compare two Counters, or add for one string and subtract for the other in a 26-slot list and check that every slot ends at zero.
  cost: O(n) time, O(1) extra space for a fixed alphabet
- 49 core
  pattern: hashing-group
  cue: Partition words into groups that are rearrangements of each other.
  hint: Find a value you can compute from a word alone that is identical for every word in its group and different across groups.
  insight: Map a canonical key to a list of words: the sorted letters, or a tuple of 26 counts. Anagrams produce equal keys, so a defaultdict(list) collects each group in one pass.
  cost: O(n k) time with count keys (O(n k log k) with sorted keys), O(n k) space
- 347 core
  pattern: hashing-group
  cue: Return the k most frequent values, and the follow-up asks for better than sorting everything.
  hint: After counting, every frequency is an integer between 1 and n. What can you index with a small integer?
  insight: Count with a Counter, then put each value into bucket[count] of a list of n + 1 buckets and read buckets from the highest count down until k values are collected. A size-k heap (Counter.most_common(k)) gives O(n log k) instead.
  cost: O(n) time, O(n) space
- 36 core
  pattern: hashing-set
  cue: Check that no digit repeats within any row, any column or any 3 x 3 box of a partly filled board.
  hint: Every filled cell belongs to exactly three groups. How can one pass check all three for each cell?
  insight: Keep sets of seen digits per row, per column and per box, with the box identified by (r // 3, c // 3), or one set of tuple keys such as ("box", r // 3, c // 3, d). A digit already present in any of its three groups makes the board invalid.
  cost: O(1) for a fixed 9 x 9 board (O(cells) in general)
- 2001 core
  pattern: hashing-group
  cue: Count pairs of rectangles whose width-to-height ratios are equal.
  hint: Two ratios are equal when their fractions reduce to the same form. What key captures that exactly?
  insight: Key each rectangle by (w // g, h // g) with g = gcd(w, h). A group of c rectangles contributes c(c - 1)/2 pairs; equivalently add the current count of the key before incrementing it. Use a 64-bit integer for the answer in C++ or Java.
  cost: O(n log(max side)) time for the gcds, O(n) space
- 128 derive
  pattern: hashing-set
  cue: Longest run of consecutive integers in an unsorted array, and O(n) time is required.
  hint: Sorting is O(n log n). With every value in a set, which values are worth counting upwards from, and which would only repeat work?
  insight: Put all values in a set and start counting only from values x with x - 1 absent (the starts of runs), walking x + 1, x + 2, ... while present. Each run is walked once from its start, so the total work is O(n) despite the inner loop.
  cost: O(n) expected time, O(n) space
- 454 derive
  pattern: hashing-complement
  cue: Count index quadruples, one from each of four arrays of length n, whose values sum to zero; n is a few hundred.
  hint: Four nested loops are O(n^4). Can you split the four arrays into two halves and combine the halves?
  insight: Meet in the middle: count every sum a + b in a Counter (n² entries), then for every c + d add the count of -(c + d). Each quadruple is counted exactly once, at O(n²) time instead of O(n^4).
  cost: O(n^2) time, O(n^2) space
- 2131 stretch
  pattern: hashing-complement
  cue: Choose some two-letter words and order them so the concatenation is a palindrome as long as possible.
  hint: A word can sit opposite its reversal. Which words could also sit alone in the middle?
  insight: Count words. For a word w with distinct letters, pair it with its reversal: min(count[w], count[rev(w)]) pairs, 4 letters each (count each unordered pair once). For a double-letter word like "gg", count // 2 pairs go opposite each other, and if any double-letter word has an odd count, one copy can sit in the middle for 2 more letters.
  cost: O(n) time, O(1) extra space (at most 26 x 26 distinct words)
- 554 stretch
  pattern: hashing-group
  cue: A vertical line through a wall of rows of bricks should cross as few bricks as possible; passing along a joint between bricks is free.
  hint: Minimising crossed bricks is the same as maximising the number of rows whose joints the line passes through. Where are the joints?
  insight: For each row, accumulate brick widths and count every running sum except the last (the wall's edge) in a Counter of joint positions. The answer is the number of rows minus the most common joint count, or the number of rows if there are no internal joints.
  cost: O(total bricks) time, O(distinct joint positions) space
- 229 stretch
  pattern: hashing-tradeoffs
  cue: Find every value occurring more than n / 3 times, with a follow-up asking for O(1) extra space.
  hint: A Counter solves it in O(n) space. How many values can possibly exceed n / 3, and do you need to count anything else?
  insight: At most two values can exceed n / 3. Keep two candidates with counters (Boyer-Moore voting): increment a matching candidate, fill an empty slot, otherwise decrement both, which cancels three distinct values at a time. A true answer always survives as a candidate; a second pass counts the candidates to confirm.
  cost: O(n) time, O(1) extra space
