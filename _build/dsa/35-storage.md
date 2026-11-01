---
key: storage
name: Storage engines: B-trees, LSM trees and write-ahead logs
stage: prod
summary: How databases keep data on disk and survive crashes: choose structures from requirements, then B+ trees, write-ahead logs, LSM trees with compaction, skip-list memtables, and the profiling habit that shows where time really goes.
why: Every application that stores data sits on a storage engine, and the two families that dominate, B+ trees (PostgreSQL, SQLite) and log-structured merge trees (LevelDB, RocksDB, Cassandra), are built from structures you already know: sorted arrays, binary search, linked lists, heaps and hash maps, arranged around one fact, that disks and SSDs move data in pages and reward sequential writes. Knowing how they work lets you predict which queries will be fast, why a write-heavy service chooses an LSM store, why an index makes inserts slower, and what "durable" actually costs. It is also the core of system design interviews and of the TinyLSM capstone at the end of this guide.
outcomes:
- Turn operation mix, data size, latency and memory budgets into a shortlist of structures, with page and byte arithmetic done on paper
- Explain why storage engines use wide B+ tree nodes, trace a node split, and answer range queries by walking linked leaves
- Make writes durable with a write-ahead log that uses length and checksum framing, fsync, and replay that stops cleanly at a torn record
- Follow an LSM write from memtable to SSTable, find a key through a sparse index, and explain tombstones and newest-wins reads
- Compare leveled and tiered compaction by read, write and space amplification, and merge sorted runs with a heap
- Implement a skip list and explain why LevelDB and RocksDB use one as the memtable and why Redis used one for sorted sets
- Profile Python code with cProfile and pstats before optimising, and read tottime and cumtime correctly
cues:
- Data larger than memory, or data that must survive a crash or restart
- A write-heavy workload (logs, metrics, events) next to occasional reads or range scans
- Range queries or ordered iteration over keys stored on disk
- Requirements stated as throughput, p99 latency, memory and durability rather than a function signature
- "It is slow" with no measurement yet
traps:
- Choosing a structure by its Big-O alone, without counting bytes, pages and disk round trips
- Calling write() and assuming the data is on disk: without flush and fsync it may sit in a buffer and vanish in a crash
- Forgetting that a delete in an LSM tree is a write (a tombstone) and that reads must check newer runs first
- Quoting LSM trees as "faster" without saying for which workload: they trade read and space amplification for cheaper writes
- Optimising the function you suspect instead of the one the profiler shows
systems:
- PostgreSQL indexes are B-trees implementing Lehman and Yao's algorithm: each page has a right-link and a high key so readers can detect a concurrent split, on 8 kB pages by default
- SQLite stores every table and index as a B-tree of fixed-size pages (4096 bytes by default since version 3.12.0)
- LevelDB appends each update to a log and a skip-list memtable, turns the memtable into a sorted table at about 4 MB, and compacts tables into levels that grow tenfold
- Redis sorted sets kept every element in a hash table plus a skip list (p = 1/4, up to 32 levels); Redis 8.12-rc1 stores large sorted sets in a packed B+ tree instead
further:
- Docs · 15 min | LevelDB implementation notes: log files, sorted tables, compactions, recovery | https://github.com/google/leveldb/blob/main/doc/impl.md#log-files
- Docs · 15 min | RocksDB wiki: Compaction, classic leveled versus tiered | https://github.com/facebook/rocksdb/wiki/Compaction#classic-leveled
- Paper · 20 min | O'Neil et al.: The Log-Structured Merge-Tree (1996), abstract and section 1 | https://www.cs.umb.edu/~poneil/lsmtree.pdf
- Source · 10 min | PostgreSQL nbtree README: the Lehman and Yao algorithm (first 40 lines) | https://github.com/postgres/postgres/blob/master/src/backend/access/nbtree/README#L1-L40
---

=== primer | How do you choose a data structure from requirements? | 15 min
goal: Turn an operation mix, data size, latency target, memory budget and durability need into a shortlist of structures, using arithmetic on bytes, pages and round trips
tag: storage-requirements | Choosing structures from requirements
link: Jonas Bonér: latency numbers every programmer should know | https://gist.github.com/jboner/2841832 | 3 min: the table only; learn the orders of magnitude (cache, memory, SSD, disk seek, network), not the exact figures, which date from around 2012
link: Algorithmica: memory hierarchy | https://en.algorithmica.org/hpc/external-memory/hierarchy/ | 10 min: the comparison table of size, latency and bandwidth per level, then 'Volatile Memory' and 'Non-Volatile Memory'

> [!key]
> Big-O tells you how cost grows; requirements tell you which costs matter. Ask five questions (which operations and in what mix, how much data compared with memory, what latency at which percentile, what memory budget, what must survive a crash), then do the arithmetic: bytes per item, items per page, levels to descend, round trips per request. The structure that fits the numbers is usually obvious once they are on paper.

## Intuition

Choosing a structure is like choosing a vehicle. Nobody asks whether a bus is better than a sports car; they ask how many people, how far, on what roads and on what budget. A hash map is the sports car for point lookups in memory; it is useless for "all orders between 9:00 and 9:05" and impossible for 2 TB of data on one machine. The questions come first, the vehicle second.

## How it works

### The five questions

| Question | Example answer | What it decides |
|---|---|---|
| Operations and mix | 90% get by id, 9% put, 1% range scan by time | Hash index or ordered index; read-optimised or write-optimised |
| Data size against memory | 50 million records of 1 KB = 50 GB, on a 32 GB machine | In memory, or on disk with an index |
| Latency target | p99 under 10 ms | How many random disk reads a request can afford |
| Memory budget | 4 GB for the index | Which index levels can be cached; whether per-item overhead matters |
| Durability | Must survive a crash without losing acknowledged writes | Write-ahead log and fsync on the write path |

### Know the orders of magnitude

From the latency table linked above: an L1 cache reference is about 0.5 ns, a main memory reference about 100 ns, a random 4 KB read from an SSD about 150 µs, a disk seek about 10 ms. One random SSD read costs as much as roughly a thousand memory references, so storage structures count **page reads**, not comparisons.

Python adds its own constants. Measured with `tracemalloc` on CPython 3.12 for 200,000 items:

| Container | Bytes per item |
|---|---|
| `dict` of int to int | 84 |
| `dict` of 15-character str to int | 126 |
| `set` of int | 74 |
| `list` of distinct ints | 40 |
| `array('q')` of ints | 8 |

A dict of 50 million small entries is several gigabytes before you store any payload.

### From numbers to a shortlist

| Situation | Usual choice |
|---|---|
| Fits in memory, point lookups only | Hash map |
| Fits in memory, ordered queries, changing data | Sorted container (`SortedList`), balanced tree or skip list |
| Fits in memory, ordered, rarely changes | Sorted array plus binary search |
| On disk, read-mostly, point and range queries | B+ tree |
| On disk, write-heavy (logs, metrics, events) | LSM tree |
| Any data that must survive a crash | Add a write-ahead log in front |

The rest of this module explains each disk-based row.

## Cost

The estimate is the cost model. For a B+ tree that stores n records in leaf pages of P bytes, with records of r bytes and inner entries (key plus child pointer) of e bytes:

1. Records per leaf: P / r. Leaves: n / (P / r).
2. Fan-out of an inner page: f = P / e.
3. Height: one leaf level plus enough inner levels to reach one root, about log_f(leaves) of them.
4. Inner-page memory: about leaves / f pages for the level just above the leaves, plus a vanishing amount above that.

For 50 million 1 KB records on 4 KB pages with 16-byte entries: 4 records per leaf, 12.5 million leaves, fan-out 256, height 4, and only about 200 MB of inner pages. Cache those and a lookup costs **one random read**.

## When to use it

Do this arithmetic whenever a requirement names sizes or latencies, in design reviews and system design interviews alike, before writing code. Do not use it to replace measurement: the estimate tells you which design to prototype, and a benchmark on realistic data decides (the lab at the end of this module and the capstone both ask for one).

Watch for two traps: a structure that fits the average case but not the p99 (a hash table that occasionally resizes, an LSM store during compaction), and per-item overhead that the Big-O hides (the dict table above).

## Worked trace

Requirement: a session store with 50 million sessions of 1 KB, 20,000 reads and 2,000 writes per second, p99 read latency under 10 ms, and no acknowledged write may be lost. The machine has 32 GB of memory and an SSD.

```steps
Data size: 50,000,000 x 1 KB = 50 GB
    data 50 GB  >  memory {{32 GB}}: an in-memory dict is out
---
Python overhead would make it worse: about 126 bytes per small dict entry on top of the payload
    50M x (1000 + 126) bytes ~ {{56 GB}}
---
On disk with an index: 4 KB pages hold 4 records; 12.5M leaf pages; fan-out 256
    height {{4}}: root, 2 inner levels, leaves
---
Cache the inner levels: about 200 MB, which fits easily, so each read needs one leaf page from the SSD
    one random 4 KB read ~ {{150 us}}  <<  10 ms target
---
Reads: 20,000 per second x 150 us is 3 seconds of SSD time per second, so requests must overlap
    a modern SSD serves many reads in parallel; {{queue depth}} matters, not latency alone
---
Writes: 2,000 per second, each durable before it is acknowledged
    log first (WAL), fsync, and {{group}} several commits per fsync
---
Shortlist: B+ tree on disk with cached inner pages, plus a write-ahead log
    read-mostly, point lookups: {{B+ tree}}; an LSM store becomes attractive if writes dominate
```

## Template

```python
import math
import tracemalloc


def btree_estimate(n, record_bytes, page_bytes=4096, entry_bytes=16):
    """Rough shape of a B+ tree that stores n records in its leaf pages."""
    per_leaf = max(1, page_bytes // record_bytes)
    fanout = page_bytes // entry_bytes            # child pointers per inner page
    leaves = math.ceil(n / per_leaf)
    height, pages, inner_pages = 1, leaves, 0
    while pages > 1:
        pages = math.ceil(pages / fanout)         # one inner page per `fanout` pages below
        inner_pages += pages
        height += 1
    return dict(data_gb=round(n * record_bytes / 1e9, 1), leaves=leaves, fanout=fanout,
                height=height, inner_mb=round(inner_pages * page_bytes / 1e6, 1))


def bytes_per_item(build, n=200_000):
    """Memory allocated by build(n), divided by n, as seen by tracemalloc."""
    tracemalloc.start()
    obj = build(n)
    current, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del obj
    return current / n
```

`btree_estimate(50_000_000, 1000)` returns 12,500,000 leaves, fan-out 256, height 4 and 200.8 MB of inner pages; its heights were checked against a brute-force page count for many sizes.

## Pitfalls

- **Averages instead of percentiles.** A design that meets the mean can miss the p99 because of resizing, garbage collection, compaction or a cold cache.
- **Ignoring per-item overhead.** Python objects carry headers and pointers; 50 million entries cost gigabytes before the payload.
- **Counting comparisons on disk.** One extra page read costs more than thousands of comparisons in memory; count pages.
- **Treating latency as throughput.** 150 µs per read does not cap you at about 6,700 reads per second if the device serves many reads at once; measure under concurrency.
- **Forgetting durability.** "Must not lose acknowledged writes" adds an fsync to the write path, which costs milliseconds on many devices (the write-ahead log card measures it).

## Check yourself

Q: Use `btree_estimate` for one billion records of 100 bytes on 8 KB pages with 16-byte entries. What are the fan-out, the number of leaves, the height and the inner-page memory?
A: 81 records fit in a leaf, so there are 12,345,680 leaves. The fan-out is 8192 / 16 = 512. Leaves divided by 512 gives 24,113 pages, then 48, then 1, so the height is 4 and the inner pages total about 198 MB. With the inner levels cached, a point lookup reads one leaf.

Q: A teammate proposes a Python dict for 80 million user records of about 200 bytes on a 16 GB machine because "dict lookups are O(1)". What is wrong with the argument?
A: The complexity is fine but the memory is not: the payload alone is 16 GB, and each small dict entry adds roughly 80 to 130 bytes of overhead in CPython, so the total is well over the machine's memory. The data belongs on disk behind an index (or in a compact encoding), with only the hot part cached.

Q: Which requirement most often turns a B+ tree design into an LSM design, and why?
A: A write-heavy workload, especially many small random writes. A B+ tree updates pages in place, so each random write touches a random leaf page; an LSM tree turns writes into sequential appends and sorted batch writes, paying later with compaction and reads that may check several runs.

## Lab

- **Exercise: size it.** Run `btree_estimate(10**6, 100)` and `bytes_per_item(lambda n: {f"user:{i:010d}": i for i in range(n)})`. Expected: 25,000 leaves, fan-out 256, height 3 and 0.4 MB of inner pages; and about 120 to 130 bytes per dict entry on 64-bit CPython 3.12 (126 when this card was written).
- **Exercise: write the requirements.** For a URL shortener (100 million links, 10,000 redirects per second, 100 new links per second, links never deleted), fill in the five-question table and pick a structure. Expected: about 10 GB of data if a link averages 100 bytes (too much for a Python dict, comfortable on disk), read-dominated point lookups, a small write rate; a B+ tree or hash index on disk with a cached upper level, plus a write-ahead log.

> [!know]
> You now know how to turn requirements into numbers and numbers into a shortlist of structures.

=== primer | Why do databases index with B+ trees instead of binary search trees? | 17 min
goal: Explain why wide nodes suit pages, insert into a B+ tree with leaf and inner splits, and answer point and range queries with one descent plus a walk along linked leaves
tag: storage-btree | B+ tree indexes and range scans
link: Open Data Structures: 14.2 B-Trees | https://opendatastructures.org/ods-python/14_2_B_Trees.html | 20 min: the introduction (the external-memory model and why node size matches the block size), then the 'Addition' discussion of splitting around Figure 14.5
link: PostgreSQL source: nbtree README | https://github.com/postgres/postgres/blob/master/src/backend/access/nbtree/README#L1-L40 | 5 min: the first 40 lines, on Lehman and Yao's right-links and high keys, which let readers survive a concurrent page split without read locks

> [!key]
> Disks and SSDs read whole pages (4 to 16 KB), so the cost of a lookup is the number of pages touched, not the number of comparisons. A **B+ tree** packs hundreds of keys into each node so that the tree is only three or four levels deep even for billions of keys. All records live in the leaves, inner nodes hold only separator keys, and the leaves are linked in key order, so a range query is one descent followed by a sequential walk.

## Intuition

A binary search tree over a billion keys is about 30 levels deep. If each node is a separate page on an SSD, a lookup costs about 30 random reads, roughly 4.5 ms at 150 µs each. Now give each node the whole page: instead of one key and two children, store 255 keys and 256 children. The tree becomes four levels deep and the top three fit in memory. A lookup costs one read.

It is the same move as a book's thumb index: one glance at the tabs takes you to the right letter, a second glance at the page headers to the right page.

## How it works

### Shape and invariants

- Every leaf is at the same depth.
- Each node holds at most `max_keys` sorted keys; every node except the root is at least about half full.
- An inner node with keys k1 < k2 < ... has one more child than keys; child i holds keys between separator i - 1 (inclusive) and separator i (exclusive).
- Leaves hold all the keys with their values (or row pointers), and each leaf points to its right neighbour.

A **B-tree** (without the plus) stores values in inner nodes too; databases prefer the B+ variant because inner nodes then hold only keys, so they have more fan-out, and because the leaf chain makes range scans sequential.

### Search

Start at the root. In each inner node, binary-search the separators (`bisect_right`) to choose the child, and descend. In the leaf, binary-search the keys. The number of pages read is the height.

### Range scan

Descend to the leaf that would contain the lower bound, then walk right along the leaf chain until a key reaches the upper bound. The walk reads consecutive leaves, which is as close to sequential I/O as an index gets.

### Insert and split

Insert into the right leaf in sorted position. If the leaf now holds more than `max_keys` keys, **split** it: keep the left half, move the right half to a new leaf, link it into the chain, and **copy** the new leaf's first key up to the parent as a separator. If the parent overflows in turn, split it too, but **move** its middle key up (inner separators are not repeated below). If the root splits, a new root is created: B+ trees grow at the top, which is why all leaves stay at the same depth.

### Deletion, briefly

Remove from the leaf; if it becomes less than half full, borrow a key from a sibling or merge with it, and fix the separator above. Many real systems relax this: PostgreSQL leaves pages under-full and reclaims space with VACUUM rather than merging eagerly.

## Cost

- **Height.** With fan-out f and n keys, the height is about log_f(n). For a billion keys, f = 2 gives 30 levels; f = 300 gives 4. In memory, the comparisons are still O(log2 n) in total (binary search inside each node), but the **page reads** drop to O(log_f n).
- **Search and insert:** O(log_f n) pages; within each page, O(log2 f) comparisons with binary search. A split costs O(f) to copy half a node, and splits are rare: a node splits only after about f/2 inserts have landed in it.
- **Range scan returning k keys:** O(log_f n + k / leaf capacity) pages.
- **Space:** leaves are typically between half full and full. PostgreSQL builds B-tree indexes with a default fill factor of 90% so that later inserts have room before a split.

A quick check from the tested implementation below: 100,000 random keys with at most 64 keys per node produced a tree of height 3.

## When to use it

Use a B+ tree for data on disk (or in pages of any kind) with point lookups, **range queries**, ordered iteration, or prefix searches on sorted keys. It is the default index in PostgreSQL, SQLite and most relational databases, and Redis 8.12-rc1 now stores large sorted sets in a packed B+ tree for memory efficiency, even though the data never leaves RAM.

| Structure | Point lookup | Range of k keys | Writes | Typical home |
|---|---|---|---|---|
| Hash index | O(1) pages | Not supported | In place | Equality-only lookups |
| Binary search tree | O(log2 n) nodes | O(log2 n + k) | In place, rebalancing | In-memory ordered maps |
| B+ tree | O(log_f n) pages | O(log_f n + k / page) | In place, occasional splits | On-disk indexes |
| LSM tree | Several runs, Bloom filters help | Merge of several runs | Sequential appends plus compaction | Write-heavy stores |

Prefer an LSM tree when random writes dominate (the comparison card later in this module works through it).

## Worked trace

A B+ tree with at most 3 keys per node. Inserting 10, 20, 30 fills the root leaf.

```steps
insert 25: the leaf [10, 20, 25, 30] overflows; split it and copy the right half's first key up
    root   {{[25]}}
    leaves [10, 20] -> [{{25}}, 30]
---
insert 40 and 50: 40 fits; 50 overflows [25, 30, 40, 50], so split and copy 40 up
    root   [25, {{40}}]
    leaves [10, 20] -> [25, 30] -> [{{40}}, 50]
---
insert 60 and 70: 70 overflows [40, 50, 60, 70]; split and copy 60 up; the root is now full
    root   [25, 40, {{60}}]
    leaves [10, 20] -> [25, 30] -> [40, 50] -> [{{60}}, 70]
---
insert 80, then 90: [60, 70, 80, 90] overflows, split, copy 80 up, and the root overflows: [25, 40, 60, 80]
    root   [25, 40, 60, {{80}}]   (4 keys: too many)
---
split the root: move its middle key 60 up into a new root; the tree is one level taller
    root   {{[60]}}
    inner  [25, 40]        [80]
    leaves [10, 20] -> [25, 30] -> [40, 50] -> [60, 70] -> [80, 90]
---
search 70: root 70 >= 60 goes right; inner [80]: 70 < 80 goes left; leaf [60, 70] has it
    root [{{60}}] -> inner [{{80}}] -> leaf [60, {{70}}]   (3 pages)
---
range 25 <= k < 61: descend to the leaf holding 25, then follow the leaf links
    [{{25}}, {{30}}] -> [{{40}}, {{50}}] -> [{{60}}, 70]   stop at 70
```

## Template

```python
from bisect import bisect_left, bisect_right


class Leaf:
    __slots__ = ("keys", "vals", "next")

    def __init__(self):
        self.keys, self.vals, self.next = [], [], None


class Inner:
    __slots__ = ("keys", "kids")

    def __init__(self, keys, kids):
        self.keys, self.kids = keys, kids      # len(kids) == len(keys) + 1


class BPlusTree:
    """Every value lives in a leaf; inner nodes hold separator keys only.
    kids[i] holds keys k with keys[i-1] <= k < keys[i]. Leaves are chained left to right."""

    def __init__(self, max_keys=4):
        self.max_keys = max_keys
        self.root = Leaf()

    def _leaf_for(self, key):
        node = self.root
        while isinstance(node, Inner):
            node = node.kids[bisect_right(node.keys, key)]
        return node

    def get(self, key, default=None):
        leaf = self._leaf_for(key)
        i = bisect_left(leaf.keys, key)
        return leaf.vals[i] if i < len(leaf.keys) and leaf.keys[i] == key else default

    def range(self, lo, hi):
        """Yield (key, value) for lo <= key < hi: one descent, then walk the leaf chain."""
        leaf = self._leaf_for(lo)
        i = bisect_left(leaf.keys, lo)
        while leaf is not None:
            while i < len(leaf.keys):
                if leaf.keys[i] >= hi:
                    return
                yield leaf.keys[i], leaf.vals[i]
                i += 1
            leaf, i = leaf.next, 0

    def put(self, key, value):
        split = self._put(self.root, key, value)
        if split is not None:                       # the root split: the tree grows one level
            sep, right = split
            self.root = Inner([sep], [self.root, right])

    def _put(self, node, key, value):
        """Insert below node; return (separator, new right sibling) if node split, else None."""
        if isinstance(node, Leaf):
            i = bisect_left(node.keys, key)
            if i < len(node.keys) and node.keys[i] == key:
                node.vals[i] = value
                return None
            node.keys.insert(i, key)
            node.vals.insert(i, value)
            if len(node.keys) <= self.max_keys:
                return None
            mid = len(node.keys) // 2
            right = Leaf()
            right.keys, right.vals = node.keys[mid:], node.vals[mid:]
            node.keys, node.vals = node.keys[:mid], node.vals[:mid]
            right.next, node.next = node.next, right
            return right.keys[0], right                  # copy the first right key up
        i = bisect_right(node.keys, key)
        split = self._put(node.kids[i], key, value)
        if split is None:
            return None
        sep, right = split
        node.keys.insert(i, sep)
        node.kids.insert(i + 1, right)
        if len(node.keys) <= self.max_keys:
            return None
        mid = len(node.keys) // 2
        up = node.keys[mid]                              # move the middle key up
        new = Inner(node.keys[mid + 1:], node.kids[mid + 1:])
        node.keys, node.kids = node.keys[:mid], node.kids[:mid + 1]
        return up, new
```

It was checked against a dict on 400 random runs of up to 300 inserts with node sizes 3, 4, 5 and 8, verifying point lookups, random range scans, sorted keys, separator bounds, equal leaf depths, minimum fill and the order of the leaf chain.

## Pitfalls

- **bisect_left in inner nodes.** A key equal to a separator belongs to the *right* child (the separator is the right leaf's first key), so descend with `bisect_right`.
- **Copy up versus move up.** Leaf splits copy the separator (the key must stay in a leaf); inner splits move it (inner separators are not repeated). Mixing the two duplicates or loses keys.
- **Forgetting the leaf chain on split.** The new right leaf must take over the old leaf's `next`, or range scans silently skip data.
- **Random keys and page fill.** Random keys (such as random UUIDs) spread writes over every leaf, and half-and-half splits leave leaves about 70% full on average (the template measured 70% to 73%). Increasing keys always land in the rightmost leaf; split it in half and every page stays 50% full (the template's behaviour), which is why engines special-case the right edge: PostgreSQL fills such pages to the fill factor, 90% by default, before moving on.
- **Concurrency.** Real engines must let readers run during splits; PostgreSQL follows Lehman and Yao, giving every page a right-link and a high key so a reader that lands on a page that just split can move right.

## Check yourself

Q: Continue the trace: in the final tree (root [60], inner [25, 40] and [80], five leaves), insert 85 and then 95 with at most 3 keys per node. What changes?
A: 85 goes into leaf [80, 90], making [80, 85, 90]. 95 makes it [80, 85, 90, 95], which overflows: it splits into [80, 85] and [90, 95], and 90 is copied up, so the right inner node becomes [80, 90]. That inner node has 2 keys, within the limit, so the root stays [60] and the height stays 3.

Q: Why does a B+ tree with fan-out 256 need about 4 page reads for a billion keys while a binary search tree needs about 30, even though both do about 30 comparisons?
A: The height is log base fan-out: log_256(10^9) is about 3.7, so 4 levels, against log_2(10^9), about 30, for a binary tree. Each level is one page read. Inside each B+ tree page, binary search over 255 keys still does about 8 comparisons, so the comparison count is similar; what shrinks is the number of slow page reads.

Q: A colleague descends inner nodes with `bisect_left(node.keys, key)`. Which lookups fail?
A: Lookups of keys equal to a separator. After a leaf split, the separator is the first key of the right leaf, so `bisect_left` sends the search to the left child, which does not contain it: in the trace, get(25) would search leaf [10, 20] and return nothing. `bisect_right` sends equal keys right.

## Lab

- **Exercise: build and check.** Insert the keys 1 to 1000 in random order into `BPlusTree(max_keys=4)`, then verify `list(t.range(100, 200))` against a sorted list. Expected: 100 pairs, keys 100 to 199 in order, and a height of 6 (it was 6 for every shuffle tried while writing this card: with at most 4 keys per node, each level multiplies capacity by only 3 to 5).
- **Exercise: count the pages.** Add a counter to `_leaf_for` and measure nodes visited per `get` for 100,000 random keys with `max_keys` = 4, 16 and 64. Expected: the count equals the height on every lookup, and the height falls as nodes widen: 9, 5 and 3 levels for 4, 16 and 64 keys per node when this card was written.

> [!know]
> You now know why storage engines use wide B+ tree nodes, how splits keep every leaf at the same depth, and how leaf links make range scans sequential.

=== primer | How does a write-ahead log make writes survive a crash? | 16 min
goal: Make every change durable by appending a checksummed record to a log and syncing it before acknowledging, then rebuild state after a crash by replaying the log up to the first torn record
tag: storage-wal | Write-ahead logging and crash recovery
link: PostgreSQL docs: Write-Ahead Logging (WAL) | https://www.postgresql.org/docs/current/wal-intro.html | 5 min: one page; the central rule (log before data), why one sequential log sync is cheaper than flushing data pages, and roll-forward recovery
link: LevelDB docs: log format | https://github.com/google/leveldb/blob/main/doc/log_format.md | 10 min: records with a CRC, a length and a type inside 32 KB blocks, and how a reader skips a corrupt block

> [!key]
> Before changing any data structure, **append a description of the change to a log and force it to disk**; only then apply it and acknowledge the client. After a crash, the log is the truth: replay it from the start (or from the last checkpoint) to rebuild the state. Frame each record with its length and a checksum, so replay can recognise a record that was only half written and stop there.

## Intuition

A shopkeeper writes each sale in a bound ledger before handing over the goods. If the till is lost, the day's state can be rebuilt from the ledger. If the pen was interrupted mid-line, the half-written last line is obviously incomplete and is ignored; every complete line before it is trusted.

The ledger is cheap to keep because it is only ever appended to, in order, which is the fastest way to write to any storage device.

## How it works

### The rule

1. Encode the change (put key=value, or delete key) as a record.
2. Append it to the log file.
3. Make it durable: `f.flush()` moves Python's buffer to the operating system, and `os.fsync(f.fileno())` asks the operating system to push its cache to the device. Without both, an acknowledged write can vanish in a power cut.
4. Apply the change to the in-memory structure (a dict, a memtable, a cached page).
5. Acknowledge.

PostgreSQL states the same rule: changes to data files must be written only after the WAL records describing them have been flushed to permanent storage.

### Framing: length plus checksum

Each record is `crc32(payload)` (4 bytes), `len(payload)` (4 bytes), then the payload. Replay reads a header, reads `len` bytes, recomputes the checksum and compares. Three things can go wrong at the end of a log after a crash: fewer than 8 bytes of header, fewer payload bytes than the length promises, or a checksum mismatch because a sector was half written. In each case replay **stops**, treats everything before as valid, and truncates the tail so new records follow valid ones. LevelDB's log uses the same idea with a CRC, a length and a record type in 32 KB blocks.

### Recovery and checkpoints

On start-up, read the log from the beginning and apply each valid record in order. Replaying a long log is slow, so systems periodically write their state somewhere durable and start a fresh log: LevelDB writes the memtable out as a sorted table and then deletes the old log file; SQLite in WAL mode appends changes to a separate WAL file and later copies them back into the database file in a **checkpoint**. After that point, the old log is no longer needed for recovery.

### Group commit

An fsync is expensive, so busy systems sync once for a batch: several clients append their records, one fsync makes them all durable, then they are all acknowledged. PostgreSQL's documentation notes that one fsync of the WAL may suffice to commit many concurrent transactions.

## Cost

- **Append:** O(record size) bytes written sequentially. Measured on the machine used for this card: about 9 µs per small append without fsync, about 6 ms with an fsync per append. The device and file system dominate; three orders of magnitude between "buffered" and "durable" is common, so measure yours with the template.
- **Replay:** O(log size) time, reading sequentially, plus applying each record.
- **Space:** the log grows until a checkpoint lets you delete or recycle it.

The sequential pattern is the point: one append to the end of one file instead of updating pages scattered across a data file.

## When to use it

Any time a state change must survive a crash: databases (PostgreSQL WAL, SQLite WAL mode, the LevelDB and RocksDB log in front of the memtable), message queues, file system journals, and your own services that keep important state in memory. If the state can be rebuilt from elsewhere (a cache), skip the log.

| Choice | Durability | Cost per write |
|---|---|---|
| Write to memory only | Lost on crash | Lowest |
| Append, no fsync | Survives a process crash, not a power cut | Low |
| Append and fsync each record | Survives power loss | One device sync per write |
| Group commit | Survives power loss | One sync per batch; adds a little latency |

## Worked trace

A key-value store logs four changes; each record is an 8-byte header plus a short JSON payload.

```steps
put(a, 1): append record 1, fsync, then apply
    log   [crc|13|["put","a",1]]                       bytes 0..21
    data  {{a: 1}}
---
put(b, 2) and delete(a): two more records, each synced before it is applied
    log   ... [crc|13|["put","b",2]] [crc|16|["del","a",null]]   bytes 21..66
    data  {{b: 2}}
---
put(c, 3): the header is written but the power fails after 10 of the 13 payload bytes
    log   ... [crc|13|["put","c"   {{(torn)}}                    file ends at byte 84
---
restart: replay record 1, 2, 3; each length and checksum matches
    data  a: 1  ->  a: 1, b: 2  ->  {{b: 2}}
---
record 4 promises 13 payload bytes but only 10 remain: stop, and truncate the file at byte 66
    valid log ends at {{66}}; data {b: 2}
---
put(d, 4) after recovery appends at byte 66, so the log stays a clean sequence of whole records
    data  {b: 2, {{d: 4}}}   (and a second restart rebuilds exactly this)
```

put(c, 3) was never acknowledged, because the crash came before its fsync returned, so losing it breaks no promise.

## Template

```python
import json
import os
import struct
import zlib

HEADER = struct.Struct("<II")          # crc32 of payload, payload length (little-endian, 8 bytes)


class WAL:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "ab")

    def append(self, record, sync=True):
        payload = json.dumps(record, separators=(",", ":")).encode()
        self.f.write(HEADER.pack(zlib.crc32(payload), len(payload)) + payload)
        if sync:
            self.f.flush()                   # Python buffer -> operating system
            os.fsync(self.f.fileno())        # operating system cache -> disk

    def close(self):
        self.f.close()


def replay(path):
    """Return every complete, intact record in order, and the byte offset where the valid log ends."""
    records, pos = [], 0
    with open(path, "rb") as f:
        data = f.read()
    while pos + HEADER.size <= len(data):
        crc, n = HEADER.unpack_from(data, pos)
        payload = data[pos + HEADER.size: pos + HEADER.size + n]
        if len(payload) < n or zlib.crc32(payload) != crc:
            break                            # torn or corrupt tail: everything after it is untrusted
        records.append(json.loads(payload))
        pos += HEADER.size + n
    return records, pos


class KV:
    """A dict made durable by logging every change before applying it."""

    def __init__(self, path):
        self.data = {}
        if os.path.exists(path):
            records, end = replay(path)
            for op, key, value in records:
                if op == "put":
                    self.data[key] = value
                else:
                    self.data.pop(key, None)
            with open(path, "r+b") as f:     # cut off a torn tail so new records follow valid ones
                f.truncate(end)
        self.wal = WAL(path)

    def put(self, key, value):
        self.wal.append(["put", key, value])  # 1. log (and fsync)
        self.data[key] = value                # 2. then apply

    def delete(self, key):
        self.wal.append(["del", key, None])
        self.data.pop(key, None)
```

The recovery test cut a log of random records at **every byte offset** and checked that replay returned exactly the records that fit completely; it also flipped one byte inside a random record and checked that replay returned only the records before it.

## Pitfalls

- **write() is not durable.** Without `flush()` the bytes may still be in Python's buffer; without `fsync()` they may be in the operating system's cache. Both vanish in a power cut.
- **Applying before logging.** If the in-memory change happens first and the process dies before the log write, readers may have seen a state that recovery cannot rebuild.
- **No checksum.** A length alone cannot detect a half-written sector full of garbage; replay would parse it as data.
- **Continuing after a bad record.** Everything after a torn record is untrusted; keep the valid prefix and truncate.
- **New files and renames.** Creating or renaming a file changes the directory, which needs its own fsync on POSIX systems; replace small metadata files atomically by writing a temporary file, syncing it and calling `os.replace`.

## Check yourself

Q: A log holds records of 21, 21, 24 and 21 bytes (87 bytes in total). The file is cut at byte 50 by a crash. What does replay return, and where is the file truncated?
A: Records 1 and 2 end at bytes 21 and 42, so both are complete. Record 3 starts at 42; its 8-byte header fits (42 to 50) but none of its 16 payload bytes do, so replay stops. It returns the first two records and truncates the file at byte 42.

Q: Why is appending to one log and syncing it cheaper than writing each changed page of a data file directly, even though the log means writing the data twice?
A: The log is written sequentially to one place and needs one sync per commit (or per batch of commits), while the changed pages are scattered across the data file and would each need a random write and a sync before every commit. With a WAL, the data pages can be written later, in the background and in bulk, and a crash is repaired by replaying the log.

Q: A service appends each change with `f.write(...)` and `f.flush()`, then acknowledges. It survives `kill -9` in tests but loses acknowledged writes after a power cut. Why?
A: `flush()` hands the bytes to the operating system, which survives the process being killed, but the operating system keeps them in its page cache until it chooses to write them. A power cut loses that cache. An `os.fsync` (or group commit) before acknowledging fixes it.

## Lab

- **Exercise: crash at every byte.** Write 8 random records with `sync=False`, record the file offset after each, then for every cut position from 0 to the file size write the truncated bytes and call `replay`. Expected: for a cut at c, replay returns exactly the records whose end offset is at most c, and reports the end of the last of them as the valid length.
- **Exercise: measure durability.** Time 300 appends with `sync=False` and 300 with `sync=True`. Expected: microseconds per append without sync and milliseconds with it on most machines (about 9 µs and 6 ms when this card was written), which is why group commit exists.

> [!know]
> You now know how a write-ahead log makes changes durable, how checksummed framing lets recovery stop at a torn record, and what fsync really costs.

=== primer | How does an LSM tree turn random writes into sequential ones? | 17 min
goal: Follow a write from memtable to an immutable sorted table, find a key through a sparse index while checking newest data first, and explain why deletes are tombstones
tag: storage-lsm | LSM trees: memtable, SSTables and tombstones
link: LevelDB docs: implementation notes, sorted tables | https://github.com/google/leveldb/blob/main/doc/impl.md#sorted-tables | 10 min: 'Log files', 'Sorted tables' and 'Level 0': the 4 MB log and memtable, deletion markers, and the young level
link: LevelDB docs: table format | https://github.com/google/leveldb/blob/main/doc/table_format.md | 5 min: items 1 to 5 at the top: data blocks, meta blocks, and the index block with one entry per data block (the sparse index)

> [!key]
> An **LSM tree** (log-structured merge tree) never updates data in place. Writes go to a write-ahead log and an in-memory sorted map, the **memtable**. When the memtable is full it is written out once, sequentially, as an immutable sorted file, an **SSTable**. A read checks the memtable and then the SSTables from newest to oldest, and the first version found wins. Deletes write a **tombstone**. Background **compaction** later merges SSTables to discard old versions.

## Intuition

A busy office does not refile every new document into the main cabinet the moment it arrives. New papers go into an in-tray (the memtable). When the tray is full, it is sorted and stored as one bundle with a contents page (an SSTable). To find a document you check the in-tray, then the bundles from newest to oldest, stopping at the first copy. A cancelled document gets a "void" slip (a tombstone) rather than being hunted down in old bundles. Now and then someone merges old bundles into one, throwing away superseded copies and void slips (compaction).

## How it works

### The write path

1. Append the change to the write-ahead log (previous card) so it survives a crash.
2. Insert it into the memtable, a sorted in-memory map. LevelDB and RocksDB use a skip list (next cards); the template uses a dict and sorts at flush time, which gives the same files.
3. When the memtable reaches its size limit (about 4 MB of log in LevelDB, 64 MB by default in RocksDB), freeze it, start a new memtable and log, and write the frozen one to disk as an SSTable in one sequential pass. Its log can then be deleted.

Every disk write in this path is sequential: appends to the log and whole sorted files. No page is ever rewritten in place.

### An SSTable and its sparse index

An SSTable is a file of sorted (key, value) entries split into blocks of a few kilobytes. An **index block** at the end stores one entry per data block (LevelDB: a key at least as large as the block's last key, plus the block's offset). The index is small enough to keep in memory, so a lookup binary-searches the index to choose one block, reads that block, and searches inside it: one disk read per table. The template keeps the first key of every block, `keys[::block]`, and uses `bisect_right(index, key) - 1` to find the only block that can hold the key.

### Reads: newest first

`get(key)` checks the memtable, then each SSTable from newest to oldest, and returns the first version it finds. If that version is a tombstone, the key is deleted, even if older tables still hold a value. A range scan merges the memtable and all tables with a heap (`heapq.merge`), keeping only the newest version of each key and skipping tombstones.

Production stores add a small Bloom filter per table so that most lookups for keys a table does not contain skip it without reading a block; the probabilistic filters module explains how they work.

### Deletes are writes

You cannot remove a key from an immutable file, and removing it only from the memtable would let an older table's value reappear. So a delete inserts a tombstone that **shadows** older versions. LevelDB keeps deletion markers "to hide obsolete values present in older sorted tables" and drops them during compaction only when no older level could still contain the key.

## Cost

Let m be the memtable limit, B the block size and T the number of SSTables.

- **put / delete:** O(1) average into a dict memtable (O(log m) in a skip list), plus an O(record) log append. Each flush sorts m entries, O(m log m), and writes them sequentially: amortised O(log m) per write.
- **get:** O(1) for the memtable, then for each table a binary search of its sparse index plus a scan of one block: O(T x (log(n / B) + B)) comparisons and at most **one block read per table**. That is why T must be kept small, by compaction.
- **scan of k results:** a heap merge over T + 1 sources, O((k + T) log T) plus the blocks read.
- **Space:** every overwritten or deleted key occupies space in older tables until compaction removes it.

## When to use it

Choose an LSM design for **write-heavy** workloads, many small writes, time series, logs, and ingestion pipelines, especially on SSDs where large sequential writes are cheap and small random rewrites wear the device. LevelDB, RocksDB and Cassandra (Dynamo-style partitioning on top of an LSM storage engine) are the standard examples, and the TinyLSM capstone builds one.

Avoid it when reads dominate and must be predictable, when a key is read far more often than written, or when range scans over freshly written data must touch as few files as possible; a B+ tree is simpler there. The comparison card later in this module quantifies the trade.

## Worked trace

Memtable limit 3, blocks of 2 entries. Values in brackets are the sparse index.

```steps
put(m, 1), put(c, 2): both go to the memtable (and to the log)
    memtable {m: 1, c: 2}
---
put(x, 3): the memtable is full, so flush it as one sorted file
    memtable {}
    sst1     {{c:2 m:1 x:3}}   index [c, x]
---
put(c, 20), delete(m): the newer value and a tombstone go to the new memtable; sst1 is untouched
    memtable {{c: 20, m: DEL}}
    sst1     c:2 m:1 x:3
---
put(a, 5): full again, so flush sst2; it shadows c and m in sst1
    sst2     {{a:5 c:20 m:DEL}}   index [a, m]
    sst1     c:2 m:1 x:3
---
get(m): memtable empty; sst2 is newest; index says block 1; it holds the tombstone, so m is deleted
    sst2     a:5 c:20 {{m:DEL}}    ->  None   (sst1's m:1 is never read)
---
get(c) finds 20 in sst2's block 0; get(x) finds nothing in sst2's block 1 and falls back to sst1
    sst2     a:5 {{c:20}} m:DEL
    sst1     c:2 m:1 {{x:3}}
---
compact: merge both tables newest first; drop c:2 (shadowed), m:1 and the tombstone (nothing older remains)
    sst1     {{a:5 c:20 x:3}}   index [a, x]
```

## Template

```python
import heapq
from bisect import bisect_left, bisect_right

TOMBSTONE = object()                      # marks a deleted key until compaction can drop it


def _tag(items, age):
    """Label each (key, value) with -age so that, for equal keys, the newest source sorts first."""
    for k, v in items:
        yield k, -age, v


def merge_newest_first(sources):
    """sources: sorted (key, value) iterables, oldest first. Yield one (key, value) per key: the newest."""
    tagged = [_tag(src, age) for age, src in enumerate(sources)]
    last = None
    for k, _, v in heapq.merge(*tagged, key=lambda x: (x[0], x[1])):
        if k != last:
            last = k
            yield k, v


class SSTable:
    """An immutable sorted run. A sparse index keeps the first key of every block of `block` entries."""

    def __init__(self, items, block=4):
        self.keys = [k for k, _ in items]
        self.vals = [v for _, v in items]
        self.block = block
        self.index = self.keys[::block]   # first key of each block: the only part kept in memory

    def get(self, key):
        """Return (found, value). Reads one block: binary search the sparse index, then scan."""
        b = bisect_right(self.index, key) - 1
        if b < 0:
            return False, None
        start = b * self.block
        for i in range(start, min(start + self.block, len(self.keys))):
            if self.keys[i] == key:
                return True, self.vals[i]
        return False, None

    def items(self, lo, hi):
        i = bisect_left(self.keys, lo)
        while i < len(self.keys) and self.keys[i] < hi:
            yield self.keys[i], self.vals[i]
            i += 1


class TinyLSM:
    def __init__(self, memtable_limit=4, block=4):
        self.mem = {}                     # newest writes; a real store also appends them to a WAL
        self.tables = []                  # oldest first
        self.limit, self.block = memtable_limit, block

    def put(self, key, value):
        self.mem[key] = value
        if len(self.mem) >= self.limit:
            self.flush()

    def delete(self, key):
        self.put(key, TOMBSTONE)

    def flush(self):
        if self.mem:
            self.tables.append(SSTable(sorted(self.mem.items()), self.block))
            self.mem = {}

    def get(self, key, default=None):
        if key in self.mem:
            v = self.mem[key]
            return default if v is TOMBSTONE else v
        for t in reversed(self.tables):   # newest table first: the first hit is the latest version
            found, v = t.get(key)
            if found:
                return default if v is TOMBSTONE else v
        return default

    def scan(self, lo, hi):
        """Yield live (key, value) pairs with lo <= key < hi in key order, newest version of each key."""
        sources = [t.items(lo, hi) for t in self.tables]
        sources.append(sorted((k, v) for k, v in self.mem.items() if lo <= k < hi))
        for k, v in merge_newest_first(sources):
            if v is not TOMBSTONE:
                yield k, v

    def compact(self):
        """Merge all tables into one. Nothing older remains below it, so tombstones can be dropped."""
        merged = [(k, v) for k, v in merge_newest_first(zip(t.keys, t.vals) for t in self.tables)
                  if v is not TOMBSTONE]
        self.tables = [SSTable(merged, self.block)] if merged else []
```

`TinyLSM` was tested against a dict on 1,500 random runs mixing puts, deletes, gets, range scans and compactions with memtable limits 1 to 5 and block sizes 1 to 4.

## Pitfalls

- **Late binding in generator expressions.** A first version of `merge_newest_first` built its sources as `((k, -age, v) for k, v in ...)` inside a list comprehension over `age`; every generator read the *final* value of `age` when it ran, so all sources tied and the oldest value won. The random test caught it within milliseconds. Bind loop variables through a function argument, as `_tag` does.
- **Searching oldest first.** The first match must come from the newest source; reverse the table list.
- **Deleting by removing.** Dropping a key from the memtable lets an older table's value reappear. Write a tombstone.
- **Dropping tombstones too early.** A compaction may drop a tombstone only when no older data that it shadows remains outside the compaction.
- **Unbounded table count.** Without compaction, every flush adds a table and every miss reads one block from each.

## Check yourself

Q: In the trace, after the two flushes and before compaction, a new put(m, 7) arrives and the memtable holds only it. What do get(m) and scan("a", "z") return?
A: get(m) returns 7, because the memtable is checked first. The scan merges the memtable, sst2 and sst1, keeping the newest version of each key: a:5, c:20, m:7 and x:3. The tombstone in sst2 is older than m:7, so it no longer hides m.

Q: Why does every LSM write turn into sequential disk I/O, and where does the random work go?
A: A write is a log append plus a memory insert; the only disk writes are appends to the log and whole SSTables written in one pass at flush time. The random work becomes deferred merging: compaction later reads and rewrites sorted files (sequentially too, but repeatedly), and reads pay by checking several tables.

Q: A colleague implements delete as `self.mem.pop(key, None)`. Which sequence shows the bug?
A: put(k, 1), then enough puts to flush it into an SSTable, then delete(k), then get(k). The pop removes nothing (k is no longer in the memtable), and get(k) finds k = 1 in the table, so the deleted key comes back. A tombstone in the memtable would shadow it.

## Lab

- **Exercise: follow the trace.** Build `TinyLSM(memtable_limit=3, block=2)` and run put(m, 1), put(c, 2), put(x, 3), put(c, 20), delete(m), put(a, 5). Expected: two tables, sst1 keys [c, m, x] with index [c, x] and sst2 keys [a, c, m] with index [a, m]; get(m) is None, get(c) is 20, get(x) is 3; after compact(), one table with keys [a, c, x].
- **Exercise: count block reads.** Add a counter to `SSTable.get`, write 100,000 random keys with a memtable limit of 10,000, then look up 1,000 keys that were never written. Expected: 10 tables, so 10 block reads per missing key (one per table whose index covers it); after `compact()`, 1 per missing key. This is the cost that Bloom filters remove.

> [!know]
> You now know how an LSM tree writes sequentially through a memtable and immutable SSTables, reads newest first through sparse indexes, and deletes with tombstones.

=== primer | What does compaction cost, and how do leveled and tiered compaction trade read, write and space amplification? | 16 min
goal: Define read, write and space amplification, merge sorted runs with a heap so the newest version wins, and choose between leveled and tiered compaction for a workload using measured numbers
tag: storage-compaction | Compaction and amplification
link: RocksDB wiki: Compaction | https://github.com/facebook/rocksdb/wiki/Compaction#classic-leveled | 10 min: 'Classic Leveled' and 'Tiered': which amplification each minimises, per-level write amplification of up to the fan-out versus 1, and the transient space cost of tiered merges
link: LevelDB docs: implementation notes, compactions | https://github.com/google/leveldb/blob/main/doc/impl.md#compactions | 10 min: 'Compactions' and 'Timing': level sizes of 10^L MB, picking a file and its overlapping files, and the worst-case 26 MB read and write per compaction

> [!key]
> Compaction merges sorted runs to drop overwritten values and tombstones and to keep the number of runs a read must check small. Every storage engine balances three costs: **write amplification** (bytes written to storage per byte the user wrote), **read amplification** (runs or pages checked per read) and **space amplification** (bytes stored per byte of live data). **Leveled** compaction keeps one run per level and rewrites data often: low read and space amplification, high write amplification. **Tiered** compaction lets several runs pile up and merges them together: low write amplification, more runs to read and more space.

## Intuition

Back to the office with its bundles. One clerk keeps exactly one tidy binder per shelf and, whenever a shelf overflows, merges it into the binder on the next shelf, even if that means rewriting a big binder for a few new pages: finding anything is quick, nothing is duplicated for long, but the clerk is always rewriting (leveled). Another clerk waits until four bundles of similar size have piled up and then merges them into one bigger bundle: much less rewriting, but a search has to look through several bundles, and superseded copies linger (tiered).

## How it works

### Merging runs with a heap

Every compaction is a **k-way merge** of sorted runs. Push the first entry of each run onto a min-heap keyed by (key, newest first); repeatedly pop the smallest, emit it if it is the first time this key appears (that is the newest version), skip it otherwise, and push the next entry from the same run. When the output is the bottom-most data for its key range, tombstones can be dropped too. RocksDB's `MergingIterator` combines its inputs with a min/max heap; LevelDB's merger simply scans all children for the smallest key, with a comment that a heap might help when there are many children, a reminder that for small k a linear scan is competitive.

### Leveled compaction

Level L holds one sorted run (split into files by key range), and each level is about T times larger than the one above (LevelDB: 10 MB for level 1, 100 MB for level 2, and so on; RocksDB's default multiplier is also 10). When a level exceeds its target, part of it is merged into the overlapping part of the next level. A key's data is rewritten each time the level below receives new data overlapping it, so per-level write amplification can reach T in the worst case; the RocksDB wiki notes it tends to be less in practice.

### Tiered compaction

Each level holds up to T runs of similar size; when T runs accumulate, they are all merged into one run in the next level. Each byte is written once per level, so per-level write amplification is about 1. A read may have to check up to T runs per level, and old versions survive until their runs are merged. RocksDB calls this style universal compaction.

### Amplification in a simulator

The template below counts entries written by flushes and compactions. With a 1,000-entry memtable and fan-out 10, on two workloads of 200,000 writes:

| Workload | Strategy | Write amp | Sorted runs | Space amp |
|---|---|---|---|---|
| 20,000 hot keys, each overwritten about 10 times | Leveled | 7.3 | 2 | 1.49 |
| | Tiered | 1.8 | 15 | 4.86 |
| 200,000-key space, mostly new keys | Leveled | 9.9 | 3 | 1.20 |
| | Tiered | 2.3 | 19 | 1.40 |

The shape matches the RocksDB description: tiered writes about four times less, but a point lookup may have to probe six to eight times as many runs, and with heavy overwriting it stores almost five copies of the live data until a big merge cleans up.

## Cost

With N entries of live data, memtable size m, fan-out T and L = log_T(N / m) levels:

- **Leveled:** write amplification O(T x L) worst case (each level rewrites up to T times); read amplification O(L) runs, one per level; space amplification about 1 + 1/(T - 1), because all upper levels together are only about 1/(T - 1) the size of the last.
- **Tiered:** write amplification O(L) (each entry is rewritten once per level); read amplification O(T x L) runs; space amplification up to about 2 temporarily when the largest runs are merged, and more with heavy overwriting until they are.
- **The merge itself:** O(n log k) for n entries from k runs with a heap, O(n x k) with a linear scan.

Bloom filters and block caches reduce the practical read cost of extra runs, which is why write-heavy stores can afford tiered layouts.

## When to use it

| Workload | Prefer | Why |
|---|---|---|
| Heavy ingestion, few reads (logs, metrics, events) | Tiered | Least rewriting; SSD wear and write bandwidth matter most |
| Read-heavy or point lookups with tight p99 | Leveled | One run per level keeps reads short |
| Disk space is the constraint | Leveled | Little duplicated data |
| Data that expires by time (time series with a retention window) | FIFO-style dropping of whole old files | No merging needed at all |

Compaction also needs headroom: it competes with foreground work for disk bandwidth, and when it falls behind, level 0 fills up and engines slow down or stall writes (LevelDB's notes discuss throttling writes when level 0 grows).

## Worked trace

Compaction of three runs into the bottom level. Runs are listed oldest first; for equal keys the newer run pops first.

```steps
start: push the first entry of each run; the heap orders by (key, newest first)
    run1 a:1 c:3 e:5     run2 b:2 c:30 d:4     run3 a:10 d:DEL
    heap {{a:10 (run3)}}, a:1 (run1), b:2 (run2)
---
pop a:10 from run3: a new key, emit it; push run3's next entry, d:DEL
    out  {{a:10}}
    heap a:1 (run1), b:2 (run2), d:DEL (run3)
---
pop a:1 from run1: key a was already emitted, so this older version is skipped; push c:3
    out  a:10        ({{a:1 dropped}})
    heap b:2, c:3, d:DEL
---
pop b:2: emit; push run2's next, c:30, which sorts before c:3 because run2 is newer
    out  a:10 {{b:2}}
    heap {{c:30 (run2)}}, c:3 (run1), d:DEL (run3)
---
pop c:30: emit; then c:3 is an older version: skip
    out  a:10 b:2 {{c:30}}      ({{c:3 dropped}})
    heap d:DEL (run3), d:4 (run2), e:5 (run1)
---
pop d:DEL: the newest version of d is a tombstone and nothing older survives below, so drop it; then d:4 is shadowed: skip
    out  a:10 b:2 c:30      ({{d gone}})
    heap e:5
---
pop e:5: emit. Nine entries in, four out
    out  a:10 b:2 c:30 {{e:5}}
```

## Template

The merge is `merge_newest_first` from the previous card. This simulator compares the two strategies by counting entries written:

```python
import random


class Sim:
    """Counts entries written by flushes and compactions under two strategies.
    leveled: one sorted run per level, level i holds at most mem * fanout**(i + 1) entries.
    tiered: runs grouped by size class; when `fanout` runs share a class, merge them into one."""

    def __init__(self, strategy, mem=1000, fanout=10):
        self.strategy, self.mem_limit, self.fanout = strategy, mem, fanout
        self.mem = {}
        self.runs = []                      # leveled: list index = level; tiered: list of (tier, run dict)
        self.written = 0                    # entries written to "disk": flushes plus compaction output
        self.user_writes = 0

    def put(self, k, v):
        self.user_writes += 1
        self.mem[k] = v
        if len(self.mem) >= self.mem_limit:
            run, self.mem = dict(self.mem), {}
            self.written += len(run)        # the flush itself
            (self._leveled if self.strategy == "leveled" else self._tiered)(run)

    def _leveled(self, run):
        """Merge the incoming run into each level until it fits; a merge with existing data rewrites it all.
        Real LevelDB and RocksDB move one file at a time; whole-level merges keep the simulator simple."""
        level = 0
        while True:
            if level == len(self.runs):
                self.runs.append({})
            existing = self.runs[level]
            merged = dict(existing)
            merged.update(run)                          # newer data wins
            if len(merged) <= self.mem_limit * self.fanout ** (level + 1):
                if existing:
                    self.written += len(merged)         # rewrite this level's run
                self.runs[level] = merged
                return
            self.runs[level] = {}
            run, level = merged, level + 1              # too big: carry everything to the next level

    def _tiered(self, run):
        self.runs.append((0, run))
        while True:
            tiers = {}
            for t, r in self.runs:
                tiers.setdefault(t, []).append(r)
            full = [t for t, rs in tiers.items() if len(rs) >= self.fanout]
            if not full:
                return
            t = min(full)
            group = [r for tt, r in self.runs if tt == t]
            self.runs = [(tt, r) for tt, r in self.runs if tt != t]
            merged = {}
            for r in group:                  # oldest first, so newer values overwrite
                merged.update(r)
            self.written += len(merged)
            self.runs.append((t + 1, merged))

    def stats(self, live):
        runs = [r for r in self.runs if r] if self.strategy == "leveled" else [r for _, r in self.runs]
        stored = sum(len(r) for r in runs) + len(self.mem)
        return dict(write_amp=round(self.written / self.user_writes, 2), sorted_runs=len(runs),
                    space_amp=round(stored / live, 2))


rng = random.Random(7)
ops = [rng.randrange(20_000) for _ in range(200_000)]
for strategy in ("leveled", "tiered"):
    s = Sim(strategy)
    for k in ops:
        s.put(k, 1)
    print(strategy, s.stats(len(set(ops))))
```

## Pitfalls

- **Quoting one amplification.** "Tiered is faster" is half a sentence: faster to write, slower to read, larger on disk. Always name all three.
- **Dropping tombstones in a non-bottom compaction.** If an older level still holds the key, dropping the tombstone resurrects the old value.
- **Equal keys in the heap.** Break ties by source age, or the merge may keep an old version; tuples of (key, -age) do it.
- **Ignoring compaction debt.** Throughput measured before compaction catches up is not sustainable; benchmark long enough to reach a steady state.
- **Simulators are models.** Real engines compact file by file, use Bloom filters and caches, and overlap work; use the simulator for shape and direction, and measure real engines for numbers.

## Check yourself

Q: With fan-out T = 10 and leveled compaction, why is space amplification only about 1.11 even if every key in the upper levels is an obsolete version?
A: Each level is ten times the one above, so all upper levels together hold about 1/10 + 1/100 + ... of the last level, which sums to about 1/9 of it. Even if all of that is duplicated data, the store holds about 1 + 1/9 = 1.11 times the live data. (The simulator's small runs give somewhat higher numbers, 1.2 to 1.5, because the memtable and level 0 are large relative to the data.)

Q: In the trace, suppose run3 were not the bottom of the tree: older data for key d also exists in a level below the compaction output. What must change, and why?
A: The tombstone d:DEL must be written to the output instead of dropped, and d:4 is still discarded. If the tombstone vanished, a later read would miss it, fall through to the older level and return d's old value, resurrecting a deleted key.

Q: A metrics service ingests 500,000 points per second and is queried a few times a minute for recent ranges. Which compaction style would you start with, and what would you watch?
A: Tiered (or time-window style) compaction, because write amplification and write bandwidth dominate and reads are rare. Watch read latency and the number of runs per query, disk space headroom for large merges, and whether compaction keeps up with ingestion over hours, not minutes.

## Lab

- **Exercise: amplification sweep.** Run `Sim` for both strategies with fan-out 4 and 10 on 200,000 writes over 20,000 keys and over 200,000 keys (seed 7). Expected: with fan-out 4 the write amplification is about 4.7 (leveled) and 2.8 (tiered) on the hot workload; with fan-out 10 it rises to 7.3 for leveled and falls to 1.8 for tiered, while tiered's run count grows from 6 to 15. Larger fan-out sharpens the trade in both directions.
- **Exercise: merge by hand.** Merge the runs [b:1, d:2], [a:3, d:DEL], [d:9, e:4] (oldest first) into the bottom level. Expected: a:3, b:1, d:9, e:4; the newest d is 9 from the third run, so both the tombstone and d:2 are discarded as older.

> [!know]
> You now know how compaction merges runs with a heap and how leveled and tiered strategies trade read, write and space amplification.

=== primer | Why do LevelDB and Redis use skip lists? | 15 min
goal: Implement a skip list with random levels, trace a search from the top lane down, derive its expected costs, and explain why it suits memtables and sorted sets
tag: storage-skiplist | Skip lists
link: Open Data Structures: 4.1 Skiplists, the basic structure | https://opendatastructures.org/ods-python/4_1_Basic_Structure.html | 10 min: the whole short section, with Figure 4.1 and the search path; continue to 4.2 for add and remove
link: LevelDB source: skiplist.h | https://github.com/google/leveldb/blob/main/db/skiplist.h#L1-L50 | 5 min: the opening comment on thread safety (writers need a lock, readers need none), then search the file for kMaxHeight and kBranching
practice: 1206

> [!key]
> A **skip list** is a sorted linked list with express lanes. Every key is on level 0; each key is promoted to the next level up with probability p (a coin flip), so each level holds about a fraction p of the one below. A search starts on the top lane, moves right while the next key is smaller, and drops down a level when it would overshoot. Searches, inserts and deletes take **O(log n) expected** time with nothing more than pointer updates, which makes skip lists simple to make safe for concurrent readers.

## Intuition

A city has stopping trains that call at every station and express trains that call at a few. To reach a small station quickly, you take the express as far as you can without passing your destination, then change to the stopping train for the last few stops. Add a super-express and the journey shortens again. A skip list builds those lines at random: each station flips a coin to decide whether the express also stops there.

## How it works

### Structure

Each node holds a key and an array `next` of forward pointers, one per level it belongs to. A head node with the maximum height starts every level. The **invariant**: every level is a sorted linked list, and each level's keys are a subset of the level below.

### Search

Start at the head on the highest level in use. On each level, move right while the next node's key is smaller than the target; when it is not, drop down one level. After level 0, the next node is the target if the target is present. The positions where the search dropped down are exactly the **predecessors** of the key on each level.

### Insert

Run the search, remembering the predecessor on every level. Choose a random height h (keep flipping: with probability p go up one more level, up to a maximum). Create the node and splice it in after its predecessor on levels 0 to h - 1: two pointer writes per level.

### Erase

Find the predecessors; if the node on level 0 holds the key, unlink it on every level it occupies. Duplicates (LeetCode 1206 allows them) need no special care: each copy is its own node, and erase removes the first.

### Concurrency: why memtables like it

An insert changes only a few pointers, and a new node can be published by linking it from the bottom level up, so a reader always sees a valid sorted list. LevelDB's `skiplist.h` says writes require external synchronisation (a mutex) while reads need no internal locking, and it uses a maximum height of 12 with a new level added with probability 1 in 4. RocksDB's default memtable is a skip list too. Level 0 is already in key order, so flushing a memtable to an SSTable is a single walk along the bottom lane.

### Redis sorted sets

Redis kept each sorted set as a hash table (member to score) plus a skip list ordered by (score, member), "almost a C translation" of Pugh's original, with up to 32 levels, p = 1/4, a back pointer for reverse traversal, and a span on each forward link so that ZRANK can count positions while it descends. In Redis 8.12-rc1, large sorted sets switch to a packed B+ tree with a compact member index for memory efficiency, and the skip list remains only as a temporary structure inside ZUNION, ZINTER and ZDIFF.

## Cost

- **Height:** level i holds about n x p^i nodes, so the highest level with any nodes is about log_{1/p} n. For a million keys and p = 1/2 that is about 20.
- **Search:** read the search path backwards: from the target, each step either goes up (if the node was promoted, probability p) or left. The expected number of left steps before going up is (1 - p)/p, at most 1/p moves per level, so the expected search length is O((1/p) log_{1/p} n) = **O(log n)**.
- **Insert and erase:** a search plus O(height) pointer changes: O(log n) expected.
- **Space:** the expected number of pointers per node is 1 + p + p^2 + ... = 1/(1 - p): 2 for p = 1/2 and 1.33 for p = 1/4. Measured over 100,000 random heights: 2.00 and 1.33, with tallest towers of 15 and 9 levels.
- **Worst case:** O(n), if the coin flips are terrible; the probability is negligible, but it is expected-case, not guaranteed.

## When to use it

| Need | Skip list | Balanced tree (red-black, AVL) | Sorted array |
|---|---|---|---|
| Ordered map with inserts and deletes | O(log n) expected | O(log n) worst case | O(n) insert |
| Concurrent readers without locks | Natural | Hard (rotations move many pointers) | Copy on write |
| Memory per entry | 1.33 to 2 pointers plus the node | 2 or 3 pointers plus colour or height | Smallest |
| Code size | Small | Large | Tiny |

Use a skip list when you need an ordered in-memory structure with concurrent readers or very simple code: memtables, sorted sets, schedulers. In everyday Python, prefer `sortedcontainers.SortedList` (a list of sorted lists), which is faster than any pure-Python tree or skip list because most of its work runs inside C list operations.

## Worked trace

A skip list with nine keys (heights chosen for the picture). Search for 42.

```steps
the layout: level 0 holds every key; higher levels hold the promoted ones
    L3: head  .  .  .  .  .  31  .  .  .
    L2: head  .  7  .  .  .  31  .  .  .
    L1: head  .  7  . 19  .  31  . 42  .
    L0: head  3  7 12 19 25  31 38 42 55
---
level 3: next is 31 < 42, move right to 31; next is the end, so drop down
    L3: head ----------------> {{31}} -> end
---
level 2: from 31, next is the end: drop down
    L2: ... {{31}} -> end
---
level 1: from 31, next is 42, which is not < 42: drop down
    L1: ... {{31}} -> 42
---
level 0: from 31, next is 38 < 42, move to 38; next is 42, not < 42: stop
    L0: ... 31 -> {{38}} -> 42
---
after level 0 the next node holds 42: found, after 2 moves right and 4 levels
    L0: ... 38 -> {{42}}
---
insert 40 with height 2: the predecessors recorded by the same search are 38 on L0 and 31 on L1; splice after each
    L1: head  .  7  . 19  .  31  . {{40}} 42  .
    L0: head  3  7 12 19 25  31 38 {{40}} 42 55
```

## Template

```python
import random


class _Node:
    __slots__ = ("key", "next")

    def __init__(self, key, height):
        self.key = key
        self.next = [None] * height            # next[i]: the following node on level i


class SkipList:
    """Sorted linked lists stacked in levels; level 0 holds every key, each higher level about P of the one below."""
    MAX_LEVEL = 16
    P = 0.5

    def __init__(self, rng=None):
        self.head = _Node(None, self.MAX_LEVEL)
        self.level = 1                        # number of levels currently in use
        self.rng = rng or random.Random()

    def _random_height(self):
        h = 1
        while h < self.MAX_LEVEL and self.rng.random() < self.P:
            h += 1
        return h

    def _predecessors(self, key):
        """For each level, the last node whose key is < key (the head counts as minus infinity)."""
        update = [self.head] * self.MAX_LEVEL
        node = self.head
        for i in range(self.level - 1, -1, -1):
            while node.next[i] is not None and node.next[i].key < key:
                node = node.next[i]           # move right while the next key is smaller
            update[i] = node                  # then drop down one level
        return update

    def search(self, key):
        nxt = self._predecessors(key)[0].next[0]
        return nxt is not None and nxt.key == key

    def add(self, key):
        update = self._predecessors(key)
        h = self._random_height()
        if h > self.level:
            self.level = h                    # new top levels start from the head
        node = _Node(key, h)
        for i in range(h):
            node.next[i] = update[i].next[i]
            update[i].next[i] = node

    def erase(self, key):
        update = self._predecessors(key)
        node = update[0].next[0]
        if node is None or node.key != key:
            return False
        for i in range(len(node.next)):
            update[i].next[i] = node.next[i]  # unlink from every level it appears on
        while self.level > 1 and self.head.next[self.level - 1] is None:
            self.level -= 1
        return True
```

It was tested against a `Counter` on 1,500 random runs of adds, erases and searches with duplicates, checking the bottom level against the sorted multiset and that each level is a sorted subset of the one below.

## Pitfalls

- **Raising `self.level` too late.** If a new node is taller than the current level, its upper predecessors are the head; the template initialises `update` with the head for every level, so this works.
- **Unlinking only level 0.** An erased node left on upper levels keeps express lanes pointing at it.
- **Using `<=` while moving right.** The search then stops after the last equal key, so `update[0].next[0]` is never the key itself, and search and erase report present keys as missing. Move right only while the next key is strictly smaller.
- **Unbounded heights.** Cap the height (16 to 32 is plenty) so one unlucky node cannot allocate a huge array.
- **Testing with one random seed.** Inject the random generator, and test many seeds; some bugs show only with particular heights.

## Check yourself

Q: In the trace's skip list (before inserting 40), what path does a search for 12 take?
A: Level 3: the head's next is 31, not smaller than 12, so drop. Level 2: move right to 7; its next is 31, so drop. Level 1: from 7 the next is 19, not smaller, so drop. Level 0: from 7 the next is 12, not smaller, so stop; the next node holds 12, found after one move right.

Q: Why is the expected number of pointers per node 1/(1 - p), and what does Redis gain by choosing p = 1/4 instead of 1/2?
A: Every node has level 0; it reaches level 1 with probability p, level 2 with probability p^2, and so on, so the expected count is 1 + p + p^2 + ... = 1/(1 - p). With p = 1/4 that is 1.33 pointers per node instead of 2, saving memory, at the price of a few more moves per level (up to 1/p = 4 instead of 2) on a shorter tower.

Q: Why is a skip list a better fit than a red-black tree for a memtable that many threads read while one thread writes?
A: An insert only splices a new node into a few lists, and if it is linked bottom-up, readers always see a sorted list that either contains the node or does not. A red-black tree insert may rotate subtrees, changing several parents and children at once, so readers would need locks or a far more complex design. LevelDB's skip list lets readers proceed with no locks at all.

## Lab

- **1206 Design Skiplist.** Implement search, add and erase with duplicates allowed. Expected: O(log n) expected per call; add(5), add(5), add(9), then search(5) is true, erase(5) is true, search(5) is still true (one copy remains), erase(5) is true, search(5) is false, erase(7) is false and search(9) is true.
- **Exercise: measure the levels.** Generate 100,000 heights with p = 1/2 and with p = 1/4. Expected: average height (pointers per node) about 2.0 and 1.33, and a tallest tower of about log_{1/p}(100,000), roughly 17 and 8 (measured 15 and 9).

> [!know]
> You now know how skip lists search and insert through randomised express lanes, what they cost, and why storage engines use them as memtables.

=== primer | When does a B+ tree beat an LSM tree, and when does it lose? | 15 min
goal: Compare the two engine families on the write path, the read path, range scans, space and predictability with explicit arithmetic, and pick one for a stated workload
link: O'Neil et al.: The Log-Structured Merge-Tree (1996) | https://www.cs.umb.edu/~poneil/lsmtree.pdf | 15 min: the abstract and section 1, Introduction: the original argument that batching writes into sorted runs beats in-place B-tree updates when inserts dominate
link: Python docs: sqlite3 transaction control | https://docs.python.org/3/library/sqlite3.html#transaction-control | 5 min: how the module opens transactions implicitly before INSERT and why nothing is saved until commit(), which the lab measures

> [!key]
> A **B+ tree** updates data in place: a read touches one root-to-leaf path, a range scan walks neighbouring leaves, but every random update eventually rewrites a whole page. An **LSM tree** never updates in place: writes become sequential appends and batch merges, but a read may consult several runs and the store carries old versions until compaction. Read-heavy, range-heavy and latency-sensitive workloads favour B+ trees; write-heavy ingestion favours LSM trees.

## Intuition

Two ways to keep a phone book up to date. One clerk finds the right page and corrects the entry with a pen each time a number changes: lookups are instant, but every correction means walking to a different page. Another clerk writes corrections on slips in a tray and, once a day, prints a new supplement merged with the old ones: corrections are effortless, but a lookup must check the tray and the supplements newest first.

## How it works

### The write path

- **B+ tree:** append the change to the WAL; find the leaf (inner pages are usually cached); read the leaf if it is not in memory; change it in the buffer pool; later write the whole dirty page back. If updates are random across data much larger than memory, a page rarely collects a second change before it is written, so each small update costs about one page of random writing.
- **LSM tree:** append to the WAL; insert into the memtable; nothing is read. Later the record is written again at flush and rewritten by compaction, each time inside large sequential writes.

### The read path

- **B+ tree:** one descent, usually one random read for the leaf. Predictable.
- **LSM tree:** memtable, then each level that may contain the key, newest first. Bloom filters let most levels be skipped without I/O, so a point lookup is typically about one read, but a lookup that misses the filters and the cache can cost one read per run.

### Range scans

A B+ tree reads consecutive leaves. An LSM tree must merge the matching ranges from every level and the memtable, so short scans touch more files.

### Space and predictability

B+ tree pages are partly empty (PostgreSQL builds indexes 90% full by default; random inserts settle near 70%). LSM files are packed and compress well because they are immutable, but they hold obsolete versions until compaction, and compaction is background work that can steal bandwidth and cause latency spikes or write stalls if it falls behind.

## Cost

A model for random updates of 100-byte records on 4 KB pages, data far larger than memory, leveled LSM with write amplification about 10:

| Per update | B+ tree | LSM tree (leveled) |
|---|---|---|
| Reads before writing | 1 random leaf read | None (for a blind put) |
| WAL | 108 bytes, sequential | 108 bytes, sequential |
| Data writes | About 4,096 bytes, random | About 1,000 bytes (100 x 10), in large sequential batches |
| Total written | About 4.2 KB, about 40x the record | About 1.1 KB, about 11x the record |
| Point read | 1 random read | About 1 random read with Bloom filters |

The model ignores real effects that move the numbers (several updates landing on a hot page before it is written, compression, full-page images in the WAL, the actual compaction pattern), but the direction is robust: for scattered small writes, the LSM tree writes several times fewer bytes and never writes randomly.

## When to use it

| Workload | Choose | Real examples |
|---|---|---|
| OLTP with many point reads, range queries, secondary indexes, steady latency | B+ tree | PostgreSQL and SQLite indexes |
| Heavy ingestion: events, logs, metrics, messages, time series | LSM tree | LevelDB, RocksDB, Cassandra |
| Read-mostly data that is rebuilt in bulk | Either; or immutable sorted files | Static lookup tables |
| Small data that fits in memory | Neither matters much | An in-memory structure plus a WAL |

For a decision that matters, prototype both on your real workload and measure throughput, p99 latency and bytes written for long enough that compaction and caches reach a steady state.

## Worked trace

The model above, one update at a time, for a 100-byte record in a 100 GB table on 4 KB pages.

```steps
B+ tree, step 1: descend; the inner pages are cached, the leaf is not
    read 1 random page  ({{4 KB}})
---
B+ tree, step 2: append the change to the WAL and fsync it at commit; modify the page in memory
    WAL +108 bytes (sequential);  page marked {{dirty}}
---
B+ tree, step 3: before this page sees another change it is evicted and written back whole
    write {{4,096 bytes}} at a random position  ->  about 4.2 KB written for 100 bytes of data
---
LSM tree, step 1: append to the WAL and insert into the memtable; no read at all
    WAL +108 bytes;  memtable insert ({{memory only}})
---
LSM tree, step 2: the memtable is flushed with thousands of others: this record's share is 100 bytes, sequential
    flush {{100 bytes}}
---
LSM tree, step 3: compaction rewrites the record as it moves down the levels, about 9 more times in total
    compaction ~{{900 bytes}}, all inside large sequential merges  ->  about 1.1 KB in total
---
Point read later: the B+ tree reads one leaf; the LSM tree checks the memtable and asks each level's Bloom filter first
    B+ tree {{1 read}};  LSM about {{1 read}}, plus about 1% extra per level from filter false positives
```

## Template

A key-value store on SQLite's B-tree, with the same interface as `TinyLSM`, and the model from the table:

```python
import sqlite3


class SqliteKV:
    """put/get/delete/scan on SQLite, whose tables and indexes are B-trees."""

    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS kv (k INTEGER PRIMARY KEY, v BLOB) WITHOUT ROWID")

    def put(self, k, v):
        self.db.execute("INSERT OR REPLACE INTO kv VALUES (?, ?)", (k, v))

    def get(self, k, default=None):
        row = self.db.execute("SELECT v FROM kv WHERE k = ?", (k,)).fetchone()
        return row[0] if row else default

    def delete(self, k):
        self.db.execute("DELETE FROM kv WHERE k = ?", (k,))

    def scan(self, lo, hi):
        yield from self.db.execute("SELECT k, v FROM kv WHERE k >= ? AND k < ? ORDER BY k", (lo, hi))

    def commit(self):
        self.db.commit()


def bytes_written_per_update(record, page=4096, lsm_write_amp=10, wal_header=8):
    """Steady-state model for random updates on data much larger than the cache."""
    wal = record + wal_header
    btree = wal + page                  # the WAL record, then the whole dirty leaf page
    lsm = wal + record * lsm_write_amp  # the WAL record, then flush and compactions
    return btree, lsm
```

`SqliteKV` was checked against a dict on 200 random runs of puts, deletes, gets and range scans. `WITHOUT ROWID` makes the integer key the B-tree key itself.

## Pitfalls

- **Benchmarking a cache.** If the data fits in memory, both engines serve reads from RAM and the comparison says nothing about disk behaviour. Use data larger than the cache, or say that you did not.
- **Stopping before compaction catches up.** LSM write throughput in the first minutes overstates what it can sustain.
- **Forgetting to commit.** Python's `sqlite3` opens a transaction implicitly before an INSERT; nothing is durable until `commit()`, and committing after every statement makes each insert wait for the disk.
- **Comparing unequal durability.** A store that fsyncs every commit will lose to one that does not, whatever its structure. Match the settings before comparing.
- **One number.** Report throughput, p99 latency, bytes written and disk space, for reads and writes separately.

## Check yourself

Q: Use `bytes_written_per_update` for 200-byte records on 8 KB pages with an LSM write amplification of 15. Which engine writes fewer bytes per update, and by how much?
A: The B+ tree writes 208 + 8,192 = 8,400 bytes; the LSM tree writes 208 + 3,000 = 3,208 bytes. The LSM tree writes about 2.6 times fewer bytes, and all of them sequentially, while the B+ tree's page writes are random.

Q: Under the model, when do the two engines write about the same number of bytes, and what does that say about large records?
A: When page + record is about record x (1 + write amp), that is, when the record is about page / write amp. With 4 KB pages and write amplification 10, records of roughly 400 bytes break even; larger records favour the B+ tree, because rewriting a page that is mostly the record wastes little, while the LSM tree keeps rewriting the whole record during compaction.

Q: A team stores user profiles (read on every page view, updated a few times a day) and asks for an LSM store "because it is faster". What do you tell them?
A: That workload is read-dominated with rare updates, so the LSM tree's cheap writes buy little while its reads may check several runs and its compaction adds background work. A B+ tree (any relational database, or SQLite) gives predictable single-read lookups; reconsider only if writes come to dominate.

## Lab

- **Exercise: what a commit costs.** With `SqliteKV` on a file, time 300 inserts with `commit()` after each, then 30,000 inserts in one transaction. Expected: milliseconds per insert in the first case and microseconds in the second, two to three orders of magnitude apart (22.8 ms against 13.8 µs on the machine used to write this card, in SQLite's default rollback-journal mode with full sync). Batching commits is the same idea as group commit.
- **Exercise: break-even record size.** Call `bytes_written_per_update` for record sizes 50, 100, 200, 400, 800 and 1,600 bytes. Expected: the LSM tree writes less for small records (about 1.1 KB against 4.2 KB at 100 bytes); the two are about equal near 400 bytes; at 1,600 bytes the B+ tree writes less (about 5.7 KB against 17.6 KB).

> [!know]
> You now know how B+ trees and LSM trees differ on writes, reads, scans, space and predictability, and how to argue for one with numbers.

=== primer | How do you find the real bottleneck before optimising? | 15 min
goal: Profile Python code with cProfile and pstats, read ncalls, tottime and cumtime correctly, choose between tracing, sampling and line profilers, and confirm a fix by re-measuring
tag: storage-profile | Profiling to find the bottleneck
link: Python docs: profiling, choosing a profiler | https://docs.python.org/3/library/profiling.html#choosing-a-profiler | 8 min: the table comparing statistical sampling and deterministic tracing, then 'Understanding profile output' for direct time, cumulative time and call counts (the profiling package is new in Python 3.15; cProfile still works)
link: Python docs: pstats, reading and displaying profile data | https://docs.python.org/3/library/pstats.html#reading-and-displaying-profile-data | 5 min: loading a saved profile, sort_stats with SortKey.CUMULATIVE and SortKey.TIME, and filtering the printed rows

> [!key]
> Programmers are bad at guessing where time goes, so measure before you change anything. A **profiler** reports, for each function, how many times it ran (ncalls), the time spent in its own code (tottime) and the time including everything it called (cumtime). Sort by cumulative time to find the expensive part of the program, look at total time to see where the work actually happens, fix the top item, check the output is unchanged, and measure again.

## Intuition

A doctor does not operate on the organ the patient points at; tests come first. Performance work is the same: a service that "feels slow in the database layer" often spends its time formatting log lines. The profile is the blood test, and it frequently disagrees with the patient.

## How it works

### Two kinds of profiler

- **Deterministic (tracing):** records every function call and return. Exact call counts and per-function times, but extra overhead on every Python call, which can exaggerate programs made of many tiny functions. In the standard library this is `cProfile`; from Python 3.15 it lives in `profiling.tracing`, and `cProfile` remains as an alias.
- **Statistical (sampling):** looks at the call stack many times a second and counts where it finds the program. Almost no overhead and safe in production, but the numbers are estimates. `py-spy` does this from outside the process without restarting it, and Python 3.15 adds `profiling.sampling` to the standard library, which can also attach to a running process.

Two more tools complete the kit: **line_profiler** times each line of chosen functions, and **tracemalloc** (standard library) shows where memory is allocated. For timing a small snippet precisely, use `timeit`, not a profiler.

### Reading the report

`pstats` prints one row per function:

- `ncalls`: how many times it was called.
- `tottime`: time inside the function's own code, excluding functions it called.
- `cumtime`: time from entry to exit, including callees.

Sort by `cumulative` to see which call tree is expensive, then look for the row whose `tottime` is large: that is where the CPU burns. Built-in operations that are not function calls, such as `x in some_list`, `a + b` or indexing, are charged to the calling function's `tottime`. A function with a huge `tottime` and cheap callees is doing expensive work in its own lines, which is when line_profiler earns its keep.

### The loop

1. Reproduce the slowness with realistic input sizes (a 100-item test hides an O(n^2)).
2. Profile; find the top item by cumulative and total time.
3. Form a hypothesis (wrong data structure, repeated work, I/O in a loop) and fix only that.
4. Check that the output is unchanged (keep the old version as an oracle for a stress test).
5. Measure again; stop when the target is met, not when the profile is flat.

## Cost

Profiling costs a run of the program plus overhead: tracing adds a fixed cost to every Python-level call, so code with millions of tiny calls can run several times slower under `cProfile`, and the relative numbers between cheap and expensive functions shift. Sampling adds almost nothing but needs enough samples (seconds of run time) to be accurate. The cost of not profiling is larger: hours spent optimising code that accounts for 2% of the run time.

The upper bound on any fix is Amdahl's arithmetic: if a part takes a fraction f of the run time and you make it s times faster, the whole program speeds up by 1 / ((1 - f) + f / s). Halving a part that takes 10% saves only 5%.

## When to use it

Profile whenever code is slower than its requirement, before rewriting anything in C or adding caches, and after each optimisation to see what is now on top. Use a sampling profiler on production processes, a tracing profiler in development when you need exact counts, line_profiler when one function dominates, and tracemalloc when memory, not time, is the problem.

| Question | Tool |
|---|---|
| Which functions take the time? | `cProfile` plus `pstats` (or `profiling.tracing` in 3.15) |
| Where is a live production process spending time? | `py-spy`, or `profiling.sampling` in 3.15 |
| Which line inside this function? | `line_profiler` |
| Who allocates the memory? | `tracemalloc` snapshots |
| Is version A faster than version B for this snippet? | `timeit`, with several repeats |

## Worked trace

A log report parses 20,000 lines, keeps the unique paths of successful requests and prints the first ten in order. It takes about two seconds. Profile it:

```steps
profile report(lines) sorted by cumulative time: report takes 1.942 s in total
    ncalls  tottime  cumtime  function
         1    0.000    1.942  report
         1    1.859    1.862  {{unique_paths}}
         1    0.046    0.075  parse
---
unique_paths has 1.859 s of tottime and almost no callees: the cost is in its own lines
    if status == 200 and path not in seen:    # seen is a {{list}}
        seen.append(path)
---
hypothesis: `path not in seen` scans the list, O(len(seen)) per line, about O(n^2) overall
    10,000 distinct paths  x  20,000 lines  ->  {{up to 10^8}} comparisons
---
fix only that: keep a set for membership and a list for the output order; check both versions give the same report
    seen = {{set()}}; out = []   ->   report(lines) == old report(lines)
---
measure again: the whole report now takes 0.062 s; unique_paths is down to 0.012 s cumulative
    ncalls  tottime  cumtime  function
         1    0.028    0.045  {{parse}}
         1    0.008    0.012  unique_paths_fast
---
the top item is now parsing, which is linear and reasonable; check the scaling instead of polishing further
    200,000 lines -> {{0.32 s}}: roughly linear, target met, stop
```

## Template

```python
import cProfile
import io
import pstats


def profile_call(fn, *args, top=6, sort="cumulative"):
    """Run fn(*args) under cProfile and return (result, the top rows of the report as text)."""
    prof = cProfile.Profile()
    result = prof.runcall(fn, *args)
    buf = io.StringIO()
    pstats.Stats(prof, stream=buf).strip_dirs().sort_stats(sort).print_stats(top)
    return result, buf.getvalue()


def unique_paths(records):
    seen = []
    for path, status in records:
        if status == 200 and path not in seen:       # list membership: O(len(seen)) each time
            seen.append(path)
    return seen


def unique_paths_fast(records):
    seen, out = set(), []
    for path, status in records:
        if status == 200 and path not in seen:       # set membership: O(1) average
            seen.add(path)
            out.append(path)
    return out
```

From the command line, `python -m cProfile -s cumulative script.py` does the same for a whole script, and `python -m pstats` opens a saved profile interactively.

## Pitfalls

- **Profiling tiny inputs.** At 100 items the quadratic loop is invisible; use production-sized data.
- **Reading cumtime as "where the work is".** The top-level function always has the largest cumtime; look for the large tottime underneath.
- **Expecting built-in operations as rows.** `in`, `+` and indexing are not calls; their cost appears in the caller's tottime.
- **Trusting tracing overhead on tiny functions.** If the program makes millions of small calls, confirm with a sampling profiler or `timeit`.
- **Optimising without an oracle.** Every speed-up must leave the output unchanged; keep the slow version and compare on random inputs.
- **CPU time versus waiting.** A program blocked on the network or disk can look idle to a CPU profile; use wall-clock mode (the 3.15 sampling profiler offers wall-clock and CPU modes) or time the I/O directly.

## Check yourself

Q: A profile sorted by cumulative time shows main 10.0 s cumtime, load 6.5 s cumtime with 0.2 s tottime, json.loads 6.2 s tottime called 40,000 times, and render 3.1 s cumtime with 3.0 s tottime. Where would you look first?
A: At json.loads inside load: 6.2 of the 10 seconds are spent parsing JSON, 40,000 times. The question is whether that parsing is necessary (parse once and cache, parse lazily, a faster parser, or a binary format). render, with 3.0 s of its own time, is second; main's 10 s cumtime is just the total.

Q: Why did `unique_paths` show 1.859 s of tottime but no expensive callees, and which tool would have pointed at the exact line?
A: The membership test `path not in seen` on a list is a bytecode operation, not a function call, so the profiler charges its time to `unique_paths` itself. line_profiler, which times each line of a decorated function, would show nearly all the time on the `if` line.

Q: A part of a request handler takes 20% of the time and you make it 4 times faster. What is the best possible overall speed-up, and what does that suggest?
A: 1 / (0.8 + 0.2 / 4) = 1 / 0.85, about 1.18, an 18% speed-up at most. It suggests checking first whether a larger part (the other 80%) can be improved, which is exactly what the profile tells you.

## Lab

- **Exercise: profile the log report.** Build 20,000 log lines of the form `2026-11-01T10:MM:00 GET /item/N STATUS` with N below 10,000 and STATUS 200 or 404, write `parse`, `unique_paths` and `report` as in the trace, and profile with `profile_call`. Expected: `unique_paths` accounts for over 90% of the run time (about 1.9 s of 1.9 s here); with `unique_paths_fast` the whole report runs about 30 times faster, gives the same output, and `parse` becomes the top item.
- **Exercise: profile a read path.** Profile 20,000 `get` calls on the `TinyLSM` from the LSM card with 10 SSTables (a memtable limit of 10,000 and 100,000 random keys), then again after `compact()`. Expected: for 20,000 keys that were never written, `SSTable.get` runs 200,000 times before compaction (once per table) and 20,000 times after it, and the total time falls roughly tenfold (1.3 s to 0.1 s here). For keys that exist, the count before compaction is about 110,000, because a lookup stops at the newest table that holds the key, on average halfway down.

> [!know]
> You now know how to find the real bottleneck with a profiler, read its numbers correctly, and prove a fix with a second measurement.

=== lab | Measure a real B-tree, then choose an engine | 50 min
goal: Load, read, scan and update SQLite's on-disk B-tree, compare what you measure with the module's models, and write a short engine choice for two workloads backed by those numbers

SQLite is a B+ tree engine that ships with Python, so you can measure a real on-disk B-tree in minutes. This lab checks the module's arithmetic against it and then uses the LSM simulator for the other side of the comparison. Keep every script and number: they become the evidence in your design note.

## Steps

1. Create `SqliteKV` (from the comparison card) on a file in a scratch folder. Load 200,000 rows with distinct random integer keys below 10^9 and 100-byte values, in **one** transaction, and time it.
2. Read the file size and `PRAGMA page_count`. Compute bytes per row and rows per page, and compare with `btree_estimate(200_000, 108)` from the requirements card.
3. Load the same number of rows into a second file using increasing keys 0, 1, 2, ... and compare load time and file size with step 1.
4. Time 20,000 random `get` calls for keys that exist, and 2,000 range scans that each return about 100 consecutive rows (pick the bounds from the sorted key list).
5. Time 20 batches of 1,000 random **updates** (existing keys, new values) with a commit after each batch, then 20 batches of 1,000 **appends** of new keys larger than any existing key. Report microseconds per row for each.
6. Run the compaction simulator (`Sim`, fan-out 10, memtable 1,000) on 400,000 random updates over 200,000 keys, for leveled and tiered, and record write amplification, sorted runs and space amplification.
7. Use `bytes_written_per_update(108)` and your leveled write amplification from step 6 to estimate bytes written per random update for each engine.
8. Write a design note of at most one page choosing an engine for (a) a user-profile service, 20,000 point reads and 50 updates per second, and (b) an event log ingesting 50,000 small events per second and queried a few times a minute by time range. Cite at least three of your measurements.

## What you should see

Numbers from the machine used to write this lab (SQLite 3 through Python 3.12, rollback-journal mode, 4 KB pages); yours will differ, but the ratios should be similar.

| Measurement | Result |
|---|---|
| Load 200,000 random keys, one transaction | 5.6 s, about 28 µs per row |
| File size | 25.8 MB in 6,297 pages, about 129 bytes per row for a 108-byte payload (about 32 rows per page, against the model's 37: SQLite adds per-cell headers and leaves some free space) |
| Load 200,000 increasing keys | 1.9 s, 24.9 MB: three times faster, every insert lands in the rightmost leaf |
| Random get | about 33 µs |
| Range scan of 100 rows | about 0.3 ms, about 3 µs per row returned |
| Random updates, commit per 1,000 | about 135 µs per row |
| Appends at the right edge, commit per 1,000 | about 44 µs per row |
| LSM model, leveled (fan-out 10) | write amplification about 10.8, 3 sorted runs, space amplification about 1.4 |
| LSM model, tiered (fan-out 10) | write amplification about 2.5, 20 sorted runs, space amplification about 1.9 |

What the numbers say: random writes into a B-tree cost about three times as much as appends because each commit dirties many scattered pages, while the same appends are cheap because they keep hitting one hot leaf; reads and short scans are fast and predictable. The models put an LSM store's random-update cost at roughly a third of the B-tree's bytes (step 7: about 1.3 KB against 4.2 KB per 108-byte update with leveled write amplification 10.8), paid for with up to 3 to 20 runs to consult on reads. A reasonable note picks the B+ tree for the profile service (read-dominated, few updates) and an LSM store, probably with tiered or time-window compaction, for the event log, and names the measurement that would change each decision.

=== practice
- 1206 core
  cue: An ordered set with search, insert and delete in about O(log n), duplicates allowed, and no library sorted containers or balanced trees.
  hint: A sorted linked list is easy to update but slow to search. What if some nodes also belonged to a sparser list above it, and some of those to a sparser one still?
  insight: Give each new node a random height (keep adding a level with probability 1/2). Search from the top level of a head node, moving right while the next key is smaller and dropping down otherwise; the drop points are the predecessors on each level. Insert splices the node after each predecessor up to its height; erase unlinks it on every level it occupies.
  cost: O(log n) expected per operation, O(n) expected space
  pattern: storage-skiplist
