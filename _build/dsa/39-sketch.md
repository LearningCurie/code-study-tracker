---
key: sketch
name: Filters and sketches: approximate answers in tiny memory
stage: prod
summary: Bloom, cuckoo and XOR filters, HyperLogLog, count-min and heavy hitters, MinHash with LSH, and reservoir sampling: trade a small, stated error for memory that stops growing with the data.
why: Exact answers about huge data need memory proportional to the data: a set of a billion visitor ids, a counter per URL, every pair of documents. Sketches keep a few kilobytes or a few bits per key instead and answer with an error you can calculate in advance, which is why they sit in front of disk reads in RocksDB and Cassandra, behind PFCOUNT in Redis, inside cache admission in Caffeine, and at the start of every large deduplication pipeline. Each one is a short, beautiful piece of probability: learn the derivation once and you can size the structure, predict its error, and prove with a measurement that your implementation matches the theory.
outcomes:
- Size a Bloom filter for n keys at a target false-positive rate p from m = -n ln p / (ln 2)^2 and k = (m/n) ln 2, and predict the rate you will measure
- Choose between Bloom, cuckoo and XOR or binary fuse filters by whether the set changes, whether you must delete, and how many bits per key you can spend
- Count distinct items with HyperLogLog, explain its 1.04/sqrt(m) standard error and small-range correction, and merge sketches from many servers
- Estimate frequencies with a count-min sketch sized from epsilon and delta, and find heavy hitters with Misra-Gries or count-min plus a small table
- Estimate Jaccard similarity with MinHash and tune LSH bands and rows with the S-curve 1 - (1 - s^r)^b
- Keep a uniform or weighted random sample of an unbounded stream with reservoir sampling
- Check any sketch statistically: measured error over many keys or seeds against the formula, never one lucky run
cues:
- "Have we seen this key?" before a slow disk or network lookup, where a rare false yes only costs one wasted lookup
- "How many distinct ...?" or "how often ...?" over billions of events, per minute or per server, with results that must be merged later
- Memory must stay fixed while the stream grows without bound, or the data passes once and cannot be stored
- "Find near-duplicates" or "similar pairs" among millions of items, where comparing every pair is impossible
- An approximate answer is acceptable if its error is bounded and stated (dashboards, admission policies, deduplication), but not for billing or correctness checks
traps:
- Using Python's built-in hash(): it is salted per process for str and bytes and is the identity for small ints, so sketches do not persist or merge and HyperLogLog breaks outright
- Inserting more keys than a filter was sized for: at twice the planned n, a filter sized for 1% false positives gives about 16%
- Reading small counts from a count-min sketch: the error is a fraction of the whole stream, so a tail item seen once can read as 82
- Deleting from a cuckoo filter something that was never inserted: it can remove another key's fingerprint and create a false negative
- Trusting one run: a probabilistic guarantee is checked over many keys or seeds against the formula
systems:
- Redis: PFADD, PFCOUNT and PFMERGE are HyperLogLog with 16,384 six-bit registers in a 12,288-byte dense string (run-length encoded while sparse) and a 0.81% standard error; Redis also ships Bloom, cuckoo, count-min and Top-K (HeavyKeeper) types
- RocksDB: a Bloom filter per SST file, typically configured at about 10 bits per key, with all probes for a key in one CPU cache line; the Ribbon filter (since 6.15.0) keeps the 1% rate in about 7 bits per key for 3-4x the CPU
- Cassandra keeps a Bloom filter per SSTable, tuned by bloom_filter_fp_chance (default 0.01, or 0.1 with leveled compaction) and stored off-heap; Git's commit-graph file can store a changed-path Bloom filter per commit so `git log -- <path>` can skip commits that did not touch the path
- Caffeine's W-TinyLFU cache admission uses a 4-bit count-min sketch of request frequencies; Trino's approx_distinct and BigQuery's HLL_COUNT functions are HyperLogLog sketches that merge across partitions and days
further:
- Notes · 40 min | Roughgarden and Valiant, CS168 lecture 2: heavy hitters and the count-min sketch | https://web.stanford.edu/class/cs168/l/l2.pdf
- Notes · 30 min | Leskovec, CS246 slides 17-53: shingling, MinHash and LSH banding | https://web.stanford.edu/class/cs246/slides/03-lsh.pdf
- Docs · 15 min | RocksDB wiki: Bloom filters in an LSM tree, bits per key and Ribbon filters | https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter
- Article · 30 min | Flajolet, Fusy, Gandouet, Meunier (2007), HyperLogLog: read Figure 3 and section 4 | https://dmtcs.episciences.org/3545
---

=== primer | How does a Bloom filter say "definitely not here" in about 10 bits per key? | 16 min
goal: Size a Bloom filter for n keys and a target false-positive rate, implement it with double hashing, and predict its measured error before you run it
tag: sketch-bloom | Bloom filter sizing
link: Jeff Erickson, Algorithms notes: Filtering and Streaming | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/06-bloom.pdf | 15 min: sections 6.1 'Bloom Filters' and 6.2 'False Positive Rate' (PDF pages 1-3) derive the same rate, and footnote 3 explains why the textbook formula slightly underestimates it
link: RocksDB wiki: RocksDB Bloom Filter | https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter#full-filters-new-format | 10 min: the bits-per-key list at the top (diminishing returns) and 'Full Filters (new format)', where all probes for one key land in one cache line

> [!key]
> A Bloom filter is an array of m bits plus k hash functions. Adding a key sets its k bits; a query says **definitely absent** if any of its k bits is 0 and **maybe present** if all are 1. It never gives a false negative, and its false-positive rate depends only on bits per key: with `m = -n ln p / (ln 2)^2` bits and `k = (m/n) ln 2` hashes you get rate p, about 9.6 bits per key for 1%, however long the keys are.

## Intuition

Picture a wall of 20 light switches, all off. Every guest who arrives flips on three switches chosen by a fixed rule from their name. To check whether Ewe has arrived, look at Ewe's three switches. If any is off, Ewe certainly has not arrived: Ewe would have switched it on. If all three are on, Ewe may have arrived, or other guests may have happened to switch on exactly those three. "No" is certain, "yes" is a guess.

That asymmetry is exactly what you want in front of something slow. A key-value store that keeps data in many files on disk can ask each file's filter "could this key be in you?" and skip every file that answers no. Most lookups for missing keys then touch no disk at all, and the occasional false yes costs one wasted read, never a wrong answer.

## How it works

### Add and query

The filter is a bit array `bits[0..m-1]`, initially all 0, and a rule that maps any key to k positions in it.

- **add(x)**: set the k bits at x's positions to 1.
- **query(x)**: if any of the k bits is 0, return "definitely absent"; otherwise return "maybe present".

No false negatives: once x's bits are set, nothing ever clears them, so a query for x always finds k ones. False positives: an absent key's k bits may all have been set by other keys.

### Where the k positions come from

Computing k independent hashes per key is wasteful. The standard trick, **double hashing**, takes two 64-bit hashes h1 and h2 of the key and uses `g_i = (h1 + i × h2) mod m` for i = 0..k-1. Kirsch and Mitzenmacher showed that this gives the same asymptotic false-positive rate as k independent hashes, and real systems use it: Git's changed-path filters are documented as 32-bit murmur3 with double hashing. One cryptographic-quality hash call (here BLAKE2b, 16 bytes) gives you both h1 and h2.

### What it cannot do

You cannot delete: clearing x's bits might clear bits that other keys rely on, creating false negatives. You cannot list the members, and you cannot count them exactly. Two filters with the same m, k and hashes can be unioned by OR-ing their bit arrays.

## Cost

**Time**: one hash computation plus k bit probes per add or query, so O(k). For a large filter each probe is a likely cache miss, which is why RocksDB's newer filter format keeps all probes for one key inside a single CPU cache line.

**Space and error**, derived step by step for n keys, m bits and k hashes, treating positions as uniformly random:

1. One probe misses a given bit with probability `1 - 1/m`. After n keys with k probes each, the bit is still 0 with probability `(1 - 1/m)^(kn)`, which is about `e^(-kn/m)`.
2. An absent key is a false positive when all k of its bits are 1: `p = (1 - e^(-kn/m))^k`.
3. For a fixed budget of m/n bits per key, more hashes check more bits but also fill the array faster. The minimum is at `k = (m/n) ln 2`, where exactly half the bits are 1, so `p = (1/2)^k`.
4. Substitute that k: `ln p = -(m/n)(ln 2)^2`, so `m = -n ln p / (ln 2)^2`, about `1.44 × n × log2(1/p)` bits.

So 1% costs 9.59 bits per key with k = 7; 0.1% costs 14.38 bits with k = 10. Every tenfold cut in p costs a constant 4.8 more bits per key, and the size of the keys never appears. The information-theoretic minimum is `log2(1/p)` bits per key, so a Bloom filter pays 44% extra; the XOR filter card shows structures that get closer.

Measured with the template below, 100,000 keys and 200,000 absent queries:

| Bits per key | k | Theory | Measured | Fraction of bits set |
|---|---|---|---|---|
| 4 | 3 | 14.69% | 14.77% | 0.528 |
| 6 | 4 | 5.61% | 5.62% | 0.487 |
| 8 | 6 | 2.16% | 2.17% | 0.527 |
| 10 | 7 | 0.82% | 0.83% | 0.503 |
| 12 | 8 | 0.31% | 0.30% | 0.486 |
| 16 | 11 | 0.046% | 0.046% | 0.497 |

The last column confirms step 3: at the best k, about half the bits are set. The same 100,000 keys in a Python `set` took 9.3 MB including the key objects; the 1% filter takes 120 kB.

## When to use it

Use a Bloom filter when a "no" saves real work and a rare false "yes" is cheap: skipping files or partitions on disk, avoiding a network call for keys that do not exist, "have we crawled this URL?", "has this user seen this item?". It fits a set too large to keep exactly, and it is easy to build per shard and OR together.

Do not use one when you need to delete (cuckoo filter or counting Bloom filter), when the set is small enough for a hash set, when false positives are unacceptable, or when the set never changes after you build it (an XOR or binary fuse filter is smaller and faster).

| Need | Hash set | Bloom | Cuckoo | XOR / binary fuse |
|---|---|---|---|---|
| Bits per key, about 1% | whole key plus overhead | 9.6 | about 10.5 (10-bit prints, b = 4) | 8.6 or 7.9 (7-bit prints give 0.78%) |
| Insert after build | yes | yes | yes, until full | no, rebuild |
| Delete | yes | no | yes | no |
| Memory probes per query | about 1 | k (7 at 1%) | 2 buckets | 3 |

In production: RocksDB builds a filter per SST file, and its wiki's example configuration uses about 10 bits per key and shows the diminishing returns (9.9 bits per key is 99% as effective as 100). Cassandra keeps a filter per SSTable, tuned per table with `bloom_filter_fp_chance` (default 0.01, or 0.1 with leveled compaction). Git's commit-graph file can store, for every commit, a Bloom filter of the paths changed against its first parent, so `git log -- <path>` can skip commits whose filter says the path did not change, without diffing their trees; commits with more than 512 changed paths get a tiny all-ones filter that always says maybe.

## Worked trace

A 20-bit filter with k = 3, three animals added, then two queries:

```steps
An empty filter: m = 20 bits, k = 3 probes per key
    pos   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    bit   0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
---
add `cat`: its probes are 19, 14, 9, so set those bits
    pos   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    bit   0  0  0  0  0  0  0  0  0  {{1}}  0  0  0  0  {{1}}  0  0  0  0  {{1}}
---
add `dog`: its probes are 5, 14, 3, so set those bits (bit 14 was already 1)
    pos   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    bit   0  0  0  {{1}}  0  {{1}}  0  0  0  1  0  0  0  0  {{1}}  0  0  0  0  1
---
add `owl`: its probes are 10, 7, 4, so set those bits
    pos   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    bit   0  0  0  1  {{1}}  1  0  {{1}}  0  1  {{1}}  0  0  0  1  0  0  0  0  1
---
query `cow`: probes 17, 0, 3; bit 17 is 0, so `cow` is **definitely absent**
    pos   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    bit   {{0}}  0  0  {{1}}  1  1  0  1  0  1  1  0  0  0  1  0  0  {{0}}  0  1
---
query `ewe`: probes 4, 19, 14 are all 1 (bit 4 by owl, bit 19 by cat, bit 14 by cat and dog): **maybe present**, but `ewe` was never added: a false positive
    pos   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19
    bit   0  0  0  1  {{1}}  1  0  1  0  1  1  0  0  0  {{1}}  0  0  0  0  {{1}}
```

Eight of 20 bits are set, so a random absent key passes all three probes with probability about `0.4^3 = 6%`. That is why real filters keep about half the bits empty at their planned size.

## Template

```python
import hashlib
import math


def bloom_size(n: int, p: float) -> tuple[int, int]:
    """Bits m and hash count k for n keys at false-positive rate p."""
    m = math.ceil(-n * math.log(p) / math.log(2) ** 2)
    k = max(1, round(m / n * math.log(2)))
    return m, k


class BloomFilter:
    def __init__(self, m: int, k: int):
        self.m, self.k = m, k
        self.bits = bytearray((m + 7) // 8)

    @classmethod
    def for_capacity(cls, n: int, p: float) -> "BloomFilter":
        return cls(*bloom_size(n, p))

    def _positions(self, item: bytes) -> list[int]:
        d = hashlib.blake2b(item, digest_size=16).digest()
        h1 = int.from_bytes(d[:8], "little")
        h2 = int.from_bytes(d[8:], "little") | 1      # odd, never 0 (0 would make all k probes equal)
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, item: bytes) -> None:
        for b in self._positions(item):
            self.bits[b >> 3] |= 1 << (b & 7)

    def __contains__(self, item: bytes) -> bool:
        return all(self.bits[b >> 3] >> (b & 7) & 1 for b in self._positions(item))


def bloom_fp_theory(m: int, n: int, k: int) -> float:
    return (1 - math.exp(-k * n / m)) ** k
```

## Pitfalls

- **Overfilling.** The rate climbs fast past the planned n. A filter sized for 1,000,000 keys at 1% gives 5.8% at 1.5 million keys, 15.7% at 2 million and 43.6% at 3 million. Size for the peak, or start a new filter when full (Redis's Bloom type stacks sub-filters for this).
- **The wrong k.** At 10 bits per key the theory gives 9.52% with k = 1, 1.18% with k = 4, 0.82% with k = 7 and 1.90% with k = 14. Too many hashes fill the array; too few check too little.
- **Python's `hash()`.** It is randomised per process for `str` and `bytes`, so a filter saved to disk or built on another machine answers nonsense. Use `hashlib` (or a fixed-seed hash such as xxHash or murmur3) and document which one, as Git's file format does.
- **Weak position derivation.** Taking k slices of one 32-bit hash, or `h2 = 0`, makes the k probes correlated or identical and the real rate far worse than the formula. Test the measured rate against theory.
- **Deleting by clearing bits.** It creates false negatives, the one error a Bloom filter promises never to make.

## Check yourself

Q: You must hold 50 million keys at a 0.1% false-positive rate. How many megabytes and how many hash functions?
A: `m = -n ln p / (ln 2)^2 = 50,000,000 × 6.908 / 0.4805`, about 719 million bits, which is about 90 MB (14.38 bits per key), with `k = 14.38 × 0.693`, about 10 hashes.

Q: Why is the best k the one that leaves half the bits set?
A: With m/n fixed, `ln p = k ln(1 - q)` where q = `e^(-kn/m)` is the fraction of zero bits, and `k = -(m/n) ln q`. So `ln p = -(m/n) ln q ln(1 - q)`, which is symmetric in q and 1 - q and is smallest at q = 1/2. Each probe then rejects an absent key with probability exactly one half, the most information a single bit can give.

Q: A service checks a Bloom filter before every database read. Its false-positive rate in production is 12%, but the filter was sized for 1%. Name two likely causes and how to tell them apart.
A: Either far more keys were inserted than planned, or the k probes are not independent (for example `h2 = 0`, or positions cut from overlapping bits of one short hash), so the filter behaves as if k were 1 or 2. Count the set bits: overfilling pushes the fraction well above one half (about 0.77 at twice the planned keys), while coinciding probes leave it far below (about 0.10 if all 7 probes coincide at 9.6 bits per key).

## Lab

- Compute `bloom_size(1_000_000, 0.01)` and `bloom_size(1_000_000, 0.001)`. Expected: (9585059, 7), which is 1.14 MiB, and (14377588, 10), which is 1.71 MiB.
- Insert `f"user:{i}".encode()` for i < 100,000 into `BloomFilter(1_000_000, 7)` (10 bits per key) and query `f"other:{i}".encode()` for i < 200,000. Expected: theory 0.8194%; the template gives 1,665 false positives, 0.83%. Repeat with k = 1 and k = 14 and compare with 9.52% and 1.90%.
- Count the set bits after the 100,000 inserts. Expected: about half of the 1,000,000 (the template gives 0.503).

> [!know]
> You now know how to size a Bloom filter from n and p, why it never gives false negatives, and how to check its measured error against theory.

=== primer | How does a cuckoo filter support deletion, and when does it beat a Bloom filter? | 15 min
goal: Explain partial-key cuckoo hashing, implement insert, lookup and delete on fingerprints, and choose fingerprint and bucket sizes for a target false-positive rate
tag: sketch-cuckoo | Cuckoo filter
link: Fan, Andersen, Kaminsky, Mitzenmacher (CoNEXT 2014): Cuckoo Filter, Practically Better Than Bloom | https://www.cs.cmu.edu/~dga/papers/cuckoo-conext2014.pdf | 25 min, authors' copy of the paper: read section 3 (Insert, Lookup, Delete, with Algorithm 1), section 5 (why f >= log2(2b/eps)) and Table 2 comparing bits per item with Bloom filters

> [!key]
> A cuckoo filter stores a short **fingerprint** of each key in a hash table of buckets, usually 4 slots each. Every key has two candidate buckets, and the second is `i1 XOR hash(fingerprint)`, so a fingerprint can be moved to its other bucket without knowing the original key. Lookups read two buckets, deletes remove one matching fingerprint, the table fills to about 95%, and with f-bit fingerprints the false-positive rate is about `2b / 2^f`.

## Intuition

A Bloom filter smears each key over shared bits, so you cannot take one key back out. Instead, store a small private token per key: a fingerprint of, say, 12 bits taken from its hash. To test membership, look where the token would be and compare. To delete, remove the token. A false positive now means a different key happens to have the same 12-bit token in the same place, roughly 1 chance in 4,096 per comparison.

Where should tokens live? A plain hash table with one home per key fills badly. **Cuckoo hashing** gives every key two possible homes: if both are full, evict a resident (as a cuckoo chick pushes eggs out of the nest) and move it to its own other home, repeating until someone lands in a free slot. With two homes and buckets of 4 slots, tables fill to about 95% before inserts start failing.

## How it works

### Partial-key cuckoo hashing

Moving an evicted resident needs its other bucket, but the filter has only the fingerprint, not the key. Fan et al. compute the two buckets as:

- `fp = fingerprint(x)` (f bits of the key's hash)
- `i1 = hash(x) mod nb`
- `i2 = (i1 XOR hash(fp)) mod nb`, with nb a power of two

XOR is its own inverse, so from either bucket i the other is `i XOR hash(fp)`: the table can move any fingerprint using only what it stores. The fingerprint is hashed before the XOR so that displaced entries jump anywhere in the table, not just among the 256 neighbours that an 8-bit value could reach.

### Operations

- **Insert**: compute fp, i1, i2. If either bucket has a free slot, store fp there. Otherwise pick one of the two buckets at random, swap fp with a random resident, and send the evicted fingerprint to its other bucket. Repeat up to a limit (the paper uses 500 kicks). If the limit is reached the table is considered full.
- **Lookup**: true if fp is in bucket i1 or i2.
- **Delete**: remove one copy of fp from i1 or i2.

Insert can fail, unlike Bloom insert. When it does, the fingerprint you are holding belongs to some earlier key, so you must keep it (the template's `victim` slot, as in the reference implementation) or you create a false negative.

## Cost

**Lookup and delete**: two buckets, at most two cache misses, independent of the target rate. A Bloom filter at 1% probes 7 bits.

**Insert**: O(1) expected while the load is moderate; near capacity the kick chains grow, and the limit bounds the worst case.

**False positives**, derived: a lookup compares fp with at most 2b stored fingerprints (b slots in each of two buckets). Each matches by accident with probability `1/2^f`, so the rate is `1 - (1 - 2^-f)^(2b×load)`, at most about `2b/2^f`. To guarantee a rate ε you need `f >= log2(2b/ε) = log2(1/ε) + log2(2b)`, which is `log2(1/ε) + 3` for b = 4. Dividing by the load α gives **bits per item** `(log2(1/ε) + 3)/α`, with α about 0.955 for b = 4 in the paper. A variant that sorts each bucket ("semi-sorting") saves one more bit, and the paper finds it smaller than a space-optimised Bloom filter (`1.44 log2(1/ε)`) whenever ε is below about 3%; for the plain variant the formulas cross near 0.4%.

Measured with the template on a table of 131,072 slots, inserting until the first failure:

| f | Load at first failure (3 seeds) | Measured rate | Formula | Bits per item |
|---|---|---|---|---|
| 8 | 96.4%, 96.3%, 96.6% | 3.02% | 2.98% | 8.30 |
| 12 | 96.7%, 96.6%, 96.7% | 0.211% | 0.189% | 12.42 |
| 16 | 95.9%, 96.6%, 96.5% | 0.0100% | 0.0118% | 16.62 |

At 12.42 bits per item the cuckoo filter measured 0.21%; a Bloom filter with the same 12.42 bits per key would give 0.26% in theory, in line with the paper's Table 3 (12-bit fingerprints: 12.60 bits per item and 0.19% for the cuckoo filter, 13.00 bits for a Bloom filter at the same rate).

## When to use it

Use a cuckoo filter when the set changes and you must delete: sessions that expire, items that leave a queue, a blocklist that shrinks. Its lookups are fast at any rate, which suits read-heavy filters at 0.01% to 3%.

Do not use one when you cannot bound the number of keys (it fails when full, while a Bloom filter just degrades), when the same key may be inserted many times (each insert stores another copy and a key inserted 2b + 1 times cannot fit in its two buckets), or when the set is static (XOR and binary fuse filters are smaller).

Redis ships a cuckoo filter type (`CF.ADD`, `CF.EXISTS`, `CF.DEL`, `CF.COUNT`). Its docs give the trade-off for 8-bit fingerprints: one slot per bucket fills to 55% with a 2/256 = 0.78% error rate, four slots fill to 95% with 3.12%. The template measured 3.02% at 96% load with f = 8 and b = 4, matching.

## Worked trace

A toy filter: 4 buckets of 2 slots, 8-bit fingerprints in hex (random seed 0 for the kick choices).

```steps
An empty cuckoo filter: 4 buckets of 2 slots, 8-bit fingerprints shown in hex
    bucket 0: [ --  -- ]
    bucket 1: [ --  -- ]
    bucket 2: [ --  -- ]
    bucket 3: [ --  -- ]
---
add `dog`: fingerprint `d2`, buckets i1 = 1 and i2 = i1 XOR hash(fp) = 0; bucket 1 has room
    bucket 0: [ --  -- ]
    bucket 1: [ {{d2}}  -- ]
    bucket 2: [ --  -- ]
    bucket 3: [ --  -- ]
---
add `emu`: fingerprint `99`, buckets i1 = 1 and i2 = i1 XOR hash(fp) = 0; bucket 1 has room
    bucket 0: [ --  -- ]
    bucket 1: [ d2  {{99}} ]
    bucket 2: [ --  -- ]
    bucket 3: [ --  -- ]
---
add `yak`: fingerprint `96`, buckets i1 = 1 and i2 = i1 XOR hash(fp) = 2; bucket 2 has room
    bucket 0: [ --  -- ]
    bucket 1: [ d2  99 ]
    bucket 2: [ {{96}}  -- ]
    bucket 3: [ --  -- ]
---
add `bee`: fingerprint `20`, buckets i1 = 1 and i2 = i1 XOR hash(fp) = 2; bucket 2 has room
    bucket 0: [ --  -- ]
    bucket 1: [ d2  99 ]
    bucket 2: [ 96  {{20}} ]
    bucket 3: [ --  -- ]
---
add `koi`: fingerprint `6d`, buckets 1 and 2 are both full, so kick a resident out
    bucket 0: [ --  -- ]
    bucket 1: [ d2  99 ]
    bucket 2: [ 96  20 ]
    bucket 3: [ --  -- ]
---
`6d` takes bucket 2 slot 1; the evicted `20` goes to its other bucket, 2 XOR hash(`20`) = 1, which is full too: kick again
    bucket 0: [ --  -- ]
    bucket 1: [ d2  99 ]
    bucket 2: [ 96  {{6d}} ]
    bucket 3: [ --  -- ]
---
`20` takes bucket 1 slot 0; the evicted `d2` goes to its other bucket, computed from bucket 1 and `d2` alone: 0, which has room
    bucket 0: [ {{d2}}  -- ]
    bucket 1: [ {{20}}  99 ]
    bucket 2: [ 96  6d ]
    bucket 3: [ --  -- ]
---
look up `dog`: fingerprint `d2`, check buckets 1 and 0: found in bucket 0: **maybe present**
    bucket 0: [ {{d2}}  -- ]
    bucket 1: [ 20  99 ]
    bucket 2: [ 96  6d ]
    bucket 3: [ --  -- ]
---
look up `cow`: fingerprint `76`, check buckets 3 and 2: in neither: **definitely absent**
    bucket 0: [ d2  -- ]
    bucket 1: [ 20  99 ]
    bucket 2: [ 96  6d ]
    bucket 3: [ --  -- ]
```

The kick moved `dog`'s fingerprint from bucket 1 to bucket 0, yet `dog` is still found, because a lookup always checks both of its buckets.

## Template

```python
import hashlib
import random


class CuckooFilter:
    def __init__(self, capacity: int, fp_bits: int = 12, bucket_size: int = 4, max_kicks: int = 500, seed: int = 0):
        nb = 1
        while nb * bucket_size * 0.95 < capacity:      # power of two keeps i ^ x inside the table
            nb *= 2
        self.nb, self.b, self.f, self.max_kicks = nb, bucket_size, fp_bits, max_kicks
        self.buckets = [[] for _ in range(nb)]
        self.victim = None                             # fingerprint left over by a failed insert
        self.rng = random.Random(seed)

    def _fp_index(self, item: bytes) -> tuple[int, int]:
        h = int.from_bytes(hashlib.blake2b(item, digest_size=8).digest(), "little")
        return (h >> 32) & ((1 << self.f) - 1), h & (self.nb - 1)

    def _alt(self, i: int, fp: int) -> int:
        hf = int.from_bytes(hashlib.blake2b(fp.to_bytes(4, "little"), digest_size=8).digest(), "little")
        return (i ^ hf) & (self.nb - 1)                # works from either bucket: alt(alt(i)) == i

    def add(self, item: bytes) -> bool:
        if self.victim:
            return False                               # full: refuse rather than lose a fingerprint
        fp, i1 = self._fp_index(item)
        i2 = self._alt(i1, fp)
        for i in (i1, i2):
            if len(self.buckets[i]) < self.b:
                self.buckets[i].append(fp)
                return True
        i = self.rng.choice((i1, i2))
        for _ in range(self.max_kicks):
            bucket = self.buckets[i]
            j = self.rng.randrange(len(bucket))
            fp, bucket[j] = bucket[j], fp              # kick out a resident, take its slot
            i = self._alt(i, fp)                       # the evicted fingerprint's other bucket
            if len(self.buckets[i]) < self.b:
                self.buckets[i].append(fp)
                return True
        self.victim = (i, fp)
        return False

    def __contains__(self, item: bytes) -> bool:
        fp, i1 = self._fp_index(item)
        i2 = self._alt(i1, fp)
        if self.victim and self.victim[1] == fp and self.victim[0] in (i1, i2):
            return True
        return fp in self.buckets[i1] or fp in self.buckets[i2]

    def remove(self, item: bytes) -> bool:
        """Only remove items you know were added, or you may delete someone else's fingerprint."""
        fp, i1 = self._fp_index(item)
        for i in (i1, self._alt(i1, fp)):
            if fp in self.buckets[i]:
                self.buckets[i].remove(fp)
                return True
        return False
```

Lists of ints keep the template readable; a real filter packs b fingerprints of f bits into one machine word per bucket.

## Pitfalls

- **Deleting a key that was never added.** If it is a false positive, `remove` deletes another key's identical fingerprint. In one run (1,000-key filter, 8-bit prints, 900 keys) removing the false positive `ghost32` made the real key `k463` disappear. Delete only what you know you inserted.
- **Losing the evicted fingerprint on failure.** A naive insert that gives up after the last kick silently drops some earlier key. Keep a victim slot or undo the kicks.
- **A table size that is not a power of two.** `i XOR h` can then point past the end, and the "other bucket of my other bucket" property breaks unless you use a different, carefully invertible formula.
- **Fingerprint and index from the same bits.** Take them from different parts of the hash, or keys in one bucket will share fingerprints and the error rate soars.
- **Duplicates.** Inserting the same key repeatedly fills its two buckets; check membership first if your keys can repeat (Redis offers `CF.ADDNX`).

## Check yourself

Q: In the trace, `koi` arrived when buckets 1 and 2 were full. Trace what happened and explain why `dog` can still be found.
A: `6d` took a random slot in bucket 2, evicting `20` (bee's fingerprint). `20`'s other bucket was 1, also full, so it evicted `d2` (dog's). `d2`'s other bucket, computed as `1 XOR hash(d2)`, was 0, which had room. A lookup for `dog` checks both of dog's buckets, 1 and 0, so it finds `d2` in bucket 0.

Q: You need a 0.1% false-positive rate with buckets of 4. How long must fingerprints be, and roughly how many bits per item will you pay?
A: `f >= log2(2b/ε) = log2(8 / 0.001) = log2(8000)`, about 12.97, so 13 bits. At about 95.5% load that is `13 / 0.955`, about 13.6 bits per item, against `1.44 × log2(1000)`, about 14.4, for a Bloom filter.

Q: Why can a Bloom filter never return a false negative, while a cuckoo filter can if it is misused?
A: Bloom filter bits only ever go from 0 to 1, so a key's bits stay set. A cuckoo filter removes stored fingerprints on delete; if two keys share a fingerprint and bucket, deleting the wrong one (a key never inserted, or deleting the same key twice) removes the survivor's only copy.

## Lab

- Fill `CuckooFilter(100_000, fp_bits=12)` with `f"key:0:{i}".encode()` until `add` returns False. Expected: it fails at about 96.7% of its 131,072 slots (the template reaches 0.9669), and 200,000 absent queries give about 0.21% false positives.
- Build `CuckooFilter(1000, fp_bits=8, seed=1)`, add `f"k{i}".encode()` for i < 900, find the first `f"ghost{j}".encode()` that tests positive, and remove it. Expected: `ghost32`, after which `k463` tests absent: a false negative caused by deleting a non-member.

> [!know]
> You now know how a cuckoo filter moves fingerprints with partial-key cuckoo hashing, why it can delete, and how to pick f and b for a target rate.

=== primer | How do XOR and binary fuse filters store a fixed set in about 9 bits per key? | 14 min
goal: Build an XOR filter by peeling a random hypergraph, query it with three lookups, and explain how binary fuse filters shrink it to about 1.125 slots per key
tag: sketch-xor | XOR and binary fuse filters
link: Graf and Lemire (2020), Xor Filters: Faster and Smaller Than Bloom and Cuckoo Filters | https://arxiv.org/abs/1912.08258 | 20 min: read section 3 (Algorithms 1 to 4: query, construction, mapping by peeling, assignment) and the bits-per-entry comparison in section 3.3
link: Graf and Lemire (2022), Binary Fuse Filters: Fast and Smaller Than Xor Filters | https://arxiv.org/abs/2201.01174 | 15 min: read section 3 and Table 1 for the segment layout that brings the table to about 1.125n (3-wise) or 1.075n (4-wise)

> [!key]
> If the set never changes, you can do better than Bloom. An **XOR filter** stores an array B of about 1.23n small fingerprints such that, for every key x in the set, `B[h0(x)] XOR B[h1(x)] XOR B[h2(x)] = fingerprint(x)`. Construction "peels" keys one at a time from slots that only they use, then fills those slots in reverse order. Queries cost three lookups, 8-bit fingerprints give a 1/256 = 0.39% rate in 9.84 bits per key, and **binary fuse filters** (three or four consecutive segments) cut the table to about 1.125n or 1.075n.

## Intuition

A Bloom filter wastes space because it must accept new keys at any time, so it keeps about half its bits empty. If you know the whole set up front, you can solve for a table in which every key's answer comes out right: a system of n equations (one per key) in about 1.23n unknowns (the table cells). Each equation involves only three unknowns, so the system is sparse, and a simple greedy method solves it: find an unknown used by only one equation, set it last, remove that equation, repeat.

An absent key reads three cells that were set for other reasons, and their XOR equals its fingerprint by chance with probability `1/2^f`.

## How it works

### Layout

The table B has c = floor(1.23n) + 32 cells split into three equal thirds. Each key hashes to one cell in each third (h0, h1, h2) and to an f-bit fingerprint (8 bits here). The paper's notation: B[h0] XOR B[h1] XOR B[h2] must equal fingerprint(x) for every x in the set.

### Construction: peel, then assign

1. **Map**: for each cell, record how many keys use it and the XOR of their indexes (the paper's counter-and-mask trick, so you never store lists).
2. **Peel**: put every cell with exactly one key on a queue. Pop a cell; if it still has one key, that key will **own** the cell: push (key, cell) on a stack and remove the key from its three cells, which may leave new single-key cells. If every key ends up on the stack, mapping succeeded; if a cluster of keys remains where every cell has two or more (a "2-core"), retry with new hash seeds. At 1.23n the paper measures success with probability above 0.8 for small sets and close to 1 for large ones.
3. **Assign** in reverse peeling order: for key x owning cell p, set `B[p] = fp(x) XOR B[other two cells]`. Why does this never break an earlier key? A key peeled later than x had not been removed when x was peeled, and x was the only key left in p, so no later-peeled key uses cell p. Assigning in reverse, every key assigned after x was peeled before x, so its owned cell is never one of x's cells either. Each cell is written at most once, and `B[p]` is still 0 when its owner is assigned.

### Binary fuse filters

Graf and Lemire's 2022 variant divides the table into many small segments whose size is a power of two, and maps each key to three cells in three **consecutive** segments starting at a random segment. This "spatial coupling" makes peeling succeed with far less slack: about 1.125n cells for large n (within 13% of the lower bound), or 1.075n with four cells per key (within 8%), and construction can be more than twice as fast as for XOR filters because sorting keys by segment makes memory access sequential.

## Cost

**Query**: three hash-derived positions and three memory reads, whatever the rate.

**Space**: f bits × cells per key. With 8-bit fingerprints: XOR `8 × 1.23 = 9.84` bits per key, binary fuse about `8 × 1.125 = 9.0`, and the lower bound is `log2(256) = 8`. A Bloom filter at the same 0.39% needs `1.44 × 8`, about 11.5 bits. In general: XOR `1.23 log2(1/ε)`, 3-wise fuse `1.125 log2(1/ε)`, 4-wise fuse `1.075 log2(1/ε)`, Bloom `1.44 log2(1/ε)`.

**Build**: linear expected time: each key is added to three cells and removed at most once, and a retry is needed rarely. Temporary memory is several times the final filter (the C reference library suggests planning for about 24 bytes per key for binary fuse construction).

Measured with the template and a 3-wise binary fuse version from the verification script (200,000 absent queries):

| Filter | n | Cells | Bits per key | Measured rate | Expected |
|---|---|---|---|---|---|
| XOR | 100,000 | 123,030 | 9.84 | 0.388% | 0.391% |
| Binary fuse | 100,000 | 118,784 | 9.50 | 0.377% | 0.391% |
| Binary fuse | 1,000,000 | 1,130,496 | 9.04 | 0.403% | 0.391% |

The fuse filter's size factor shrinks toward 1.125 as n grows (the paper's sizing rule adds slack for smaller sets).

## When to use it

Use an XOR or binary fuse filter for **immutable** sets: an SST file in an LSM tree (written once, then only read), a shipped blocklist, a dictionary of known-bad passwords, a nightly snapshot of all user ids. You get the smallest common filter and three reads per query.

Do not use one when keys arrive over time (you would rebuild from scratch), when you must delete, or when you cannot afford construction memory. RocksDB offers a static filter for the same reason: its **Ribbon filter** (since 6.15.0), also built once per immutable SST file by solving a linear system over bits, keeps a 1% rate in about 7 bits per key instead of 9.9, at 3 to 4 times the CPU, mostly spent in the background jobs that construct filters. The reference C library for XOR and binary fuse filters lists production users such as Databend and CockroachDB's Pebble.

| | Bloom | Cuckoo | XOR | Binary fuse (3-wise) |
|---|---|---|---|---|
| Bits per key at 0.39% | 11.5 | about 11.5 (11-bit prints, b = 4) | 9.84 | about 9.0 |
| Add after build | yes | yes | no | no |
| Delete | no | yes | no | no |
| Reads per query | about 8 | 2 buckets | 3 | 3 |

## Worked trace

Four keys in a toy 9-cell table (three thirds of 3 cells), 8-bit fingerprints shown in decimal:

```steps
Each key hits one slot per third of a 9-slot table. Count the keys per slot: slots 1, 2, 4, 5 and 6 hold exactly one key
    cat -> 1 3 6   fp 65
    dog -> 0 5 8   fp 200
    owl -> 0 4 8   fp 142
    emu -> 2 3 8   fp 205
    slot       0    1    2    3    4    5    6    7    8
    count      2    {{1}}    {{1}}    2    {{1}}    {{1}}    {{1}}    0    3
---
peel: slot 6 holds only `cat`, so `cat` will own slot 6; remove `cat` from slots 1, 3, 6
    stack  cat@6
    slot       0    1    2    3    4    5    6    7    8
    count      2    {{0}}    1    {{1}}    1    1    {{0}}    0    3
---
peel: slot 3 holds only `emu`, so `emu` will own slot 3; remove `emu` from slots 2, 3, 8
    stack  cat@6 emu@3
    slot       0    1    2    3    4    5    6    7    8
    count      2    0    {{0}}    {{0}}    1    1    0    0    {{2}}
---
peel: slot 5 holds only `dog`, so `dog` will own slot 5; remove `dog` from slots 0, 5, 8
    stack  cat@6 emu@3 dog@5
    slot       0    1    2    3    4    5    6    7    8
    count      {{1}}    0    0    0    1    {{0}}    0    0    {{1}}
---
peel: slot 8 holds only `owl`, so `owl` will own slot 8; remove `owl` from slots 0, 4, 8
    stack  cat@6 emu@3 dog@5 owl@8
    slot       0    1    2    3    4    5    6    7    8
    count      {{0}}    0    0    0    {{0}}    0    0    0    {{0}}
---
assign in reverse: B[8] = fp(owl) XOR B[0] XOR B[4] = 142 XOR 0 XOR 0 = 142
    slot       0    1    2    3    4    5    6    7    8
    B          0    0    0    0    0    0    0    0  {{142}}
---
assign in reverse: B[5] = fp(dog) XOR B[0] XOR B[8] = 200 XOR 0 XOR 142 = 70
    slot       0    1    2    3    4    5    6    7    8
    B          0    0    0    0    0   {{70}}    0    0  142
---
assign in reverse: B[3] = fp(emu) XOR B[2] XOR B[8] = 205 XOR 0 XOR 142 = 67
    slot       0    1    2    3    4    5    6    7    8
    B          0    0    0   {{67}}    0   70    0    0  142
---
assign in reverse: B[6] = fp(cat) XOR B[1] XOR B[3] = 65 XOR 0 XOR 67 = 2
    slot       0    1    2    3    4    5    6    7    8
    B          0    0    0   67    0   70    {{2}}    0  142
---
query `cow`: slots 1, 3, 7 give 0 XOR 67 XOR 0 = 67, but fp(cow) = 62: **absent**. Every stored key checks out, e.g. cat: 0 XOR 67 XOR 2 = 65
    slot       0    1    2    3    4    5    6    7    8
    B          0    {{0}}    0   {{67}}    0   70    2    {{0}}  142
```

## Template

```python
import hashlib


def _xor_hashes(key: bytes, seed: int, seg: int) -> tuple[int, int, int, int]:
    """One slot in each third of the table, plus an 8-bit fingerprint."""
    d = hashlib.blake2b(key, digest_size=32, salt=seed.to_bytes(16, "little")).digest()
    a, b, c, f = (int.from_bytes(d[i:i + 8], "little") for i in range(0, 32, 8))
    return a % seg, seg + b % seg, 2 * seg + c % seg, f & 0xFF


class XorFilter:
    """Static set, 8-bit fingerprints: about 9.84 bits per key, false positives about 1/256."""

    def __init__(self, keys: list[bytes]):
        keys = list(set(keys))                         # duplicates would make peeling impossible
        n = len(keys)
        self.seg = (int(1.23 * n) + 32) // 3
        size = 3 * self.seg
        for seed in range(100):
            hs = [_xor_hashes(k, seed, self.seg) for k in keys]
            count, mask = [0] * size, [0] * size       # per slot: how many keys, XOR of their indexes
            for idx, h in enumerate(hs):
                for p in h[:3]:
                    count[p] += 1
                    mask[p] ^= idx
            queue = [p for p in range(size) if count[p] == 1]
            order = []                                 # (key index, the slot it owns), in peeling order
            while queue:
                p = queue.pop()
                if count[p] != 1:
                    continue
                idx = mask[p]
                order.append((idx, p))
                for q in hs[idx][:3]:
                    count[q] -= 1
                    mask[q] ^= idx
                    if count[q] == 1:
                        queue.append(q)
            if len(order) == n:
                break
        else:
            raise RuntimeError("peeling failed 100 times")
        self.seed, self.B = seed, [0] * size
        for idx, p in reversed(order):                 # last peeled is assigned first
            a, b, c, fp = hs[idx]
            self.B[p] = fp ^ self.B[a] ^ self.B[b] ^ self.B[c]   # B[p] is still 0 here

    def __contains__(self, key: bytes) -> bool:
        a, b, c, fp = _xor_hashes(key, self.seed, self.seg)
        return fp == self.B[a] ^ self.B[b] ^ self.B[c]
```

A production filter stores B as a `bytearray` (one byte per 8-bit cell) and uses a fast seeded 64-bit hash; the list keeps the template short.

## Pitfalls

- **Duplicate keys.** Two copies of a key hit the same three cells, so neither can ever be the only key in a cell and peeling fails on every seed. The template dedupes first; without that line the four keys `a, b, c, a` fail 100 times out of 100.
- **Assigning in peeling order instead of reverse.** Then a later assignment overwrites a cell an earlier key relied on, and stored keys start failing their own check.
- **Expecting to add one more key.** Any change means a rebuild. Keep these filters for data that is rebuilt in batches anyway.
- **Hashing the three cells from overlapping bits** of a short hash. The cells become correlated, peeling fails more often and the error rate drifts from `2^-f`.

## Check yourself

Q: Using the final table of the trace, check that `dog` (cells 0, 5, 8, fingerprint 200) and `owl` (cells 0, 4, 8, fingerprint 142) are both reported present.
A: dog: `B[0] XOR B[5] XOR B[8] = 0 XOR 70 XOR 142 = 200`, which matches. owl: `0 XOR 0 XOR 142 = 142`, which matches. Cells 0 and 4 were never owned by anyone, so they stay 0 and only the owned cells carry information.

Q: Why does assigning in reverse peeling order never break a key that was already satisfied?
A: When x was peeled from cell p, x was the only key left in p, so no key peeled after x uses p. In reverse order those later-peeled keys are assigned before x, so writing `B[p]` cannot disturb them. Every key assigned after x was peeled before x, from a cell that held only that key while x was still in the table, so that cell is not one of x's three cells. Later writes therefore never touch x's cells, and x's check stays true.

Q: You need a filter for 200 million static keys at 0.39%. Compare the memory of Bloom, XOR and binary fuse.
A: Bloom: `1.44 × 8 × 200M`, about 2.3 billion bits, 288 MB. XOR: `9.84 × 200M`, about 246 MB. Binary fuse (3-wise): about `9.0 × 200M`, 225 MB. The fuse filter saves about 63 MB over Bloom and needs 3 reads per query instead of about 8.

## Lab

- Build `XorFilter([f"key:{i}".encode() for i in range(100_000)])` and query `f"absent:{i}".encode()` for i < 200,000. Expected: 123,030 cells, 9.84 bits per key, about 0.39% false positives (the template gives 0.388%) and no false negatives.
- Remove the dedupe line and build from `[b"a", b"b", b"c", b"a"]`. Expected: `RuntimeError: peeling failed 100 times`.

> [!know]
> You now know how XOR and binary fuse filters solve for a table by peeling, why they beat Bloom on static sets, and their cost in bits per key.

=== primer | How does HyperLogLog count billions of distinct items in 12 KB? | 16 min
goal: Explain how the leading zeros of hashes estimate a distinct count, implement HyperLogLog with its small-range correction, and predict the standard error from the number of registers
tag: sketch-hll | HyperLogLog distinct counting
link: Flajolet, Fusy, Gandouet, Meunier (AofA 2007, DMTCS proceedings): HyperLogLog | https://dmtcs.episciences.org/3545 | 20 min: open the PDF from this proceedings page and read Figure 3 (the practical program with both corrections) and section 4 'Discussion' (why registers start at 0, linear counting, the 65/95/99% rule); skip the analysis in sections 2 and 3
link: Redis docs: PFCOUNT | https://redis.io/docs/latest/commands/pfcount/#hyperloglog-representation | 5 min: the sparse and dense encodings, the 16-byte header that caches the last estimate, and why multi-key PFCOUNT is slower

> [!key]
> HyperLogLog hashes every item and keeps m small **registers**. The first p bits of the hash choose a register, which remembers the largest **rank** (position of the first 1 bit in the rest of the hash) it has seen. A rank of r hints that about 2^r distinct items passed by; a harmonic mean over all registers turns those hints into an estimate with standard error `1.04/sqrt(m)`, which is 0.81% for m = 16,384 registers, Redis's 12 KB. Duplicates hash identically and change nothing, and sketches merge by taking register-wise maxima.

## Intuition

Flip a coin until it lands heads and write down how many flips it took. One person will rarely need 10 flips; but if a thousand people do it, someone probably will. So "the longest run anyone reported" tells you roughly how many people took part: a longest run of 10 suggests about 2^10.

Hash values behave like coin flips: half start with a 1 bit, a quarter with `01`, an eighth with `001`. If the most leading zeros you have seen in any hash is 9 (rank 10), you have probably seen around 2^10 distinct hashes. Repeated items give the same hash, so they cannot fake a longer run: the method counts **distinct** items for free.

One maximum is far too noisy, since a single lucky hash can double the answer. So split the stream into m sub-streams by the first p bits of the hash, keep one maximum per sub-stream, and average. The averaging is a **harmonic mean**, which barely notices one register that got unusually lucky.

## How it works

### Add

1. Hash the item to 64 bits.
2. The first p bits give the register index j (m = 2^p registers).
3. In the remaining 64 - p bits, the **rank** is the position of the first 1 bit (leading zeros plus one).
4. `M[j] = max(M[j], rank)`.

### Count

Each register sees about n/m distinct items, so `2^M[j]` is a rough estimate of n/m. The harmonic mean of those estimates is `m / sum(2^-M[j])`, and multiplying by m registers gives the raw estimate

`E = alpha_m × m^2 / sum over j of 2^(-M[j])`

where `alpha_m = 0.7213 / (1 + 1.079/m)` removes a known bias (the paper gives 0.673, 0.697 and 0.709 for m = 16, 32 and 64).

### Corrections at the ends of the range

- **Small range.** With few items, many registers are still 0 and the raw formula is badly biased: an empty sketch would report `alpha_m × m`, about 0.72m. The paper's fix: if `E <= 2.5m` and V registers are 0, use **linear counting**, `m ln(m/V)`. It comes from throwing n balls into m bins: about `m e^(-n/m)` bins stay empty, so seeing V empty bins means n is about `m ln(m/V)`.
- **Large range.** With a 32-bit hash, distinct items start to collide near 2^32, and the paper corrects estimates above `2^32/30`. With a 64-bit hash, as in the template, collisions are negligible at any count you will meet, so the correction is not needed.

### Merge

The sketch of A ∪ B is the register-wise maximum of the sketches of A and B, because each register depends only on the set of distinct hashes that reached it. That is what makes HyperLogLog perfect for "one sketch per server per hour, merge later". Intersections can only be estimated as `|A| + |B| - |A ∪ B|`, with an error relative to the union.

## Cost

**Time**: one hash and one comparison per add, O(1). Counting is O(m), and Redis caches the last estimate so repeated PFCOUNT calls are cheap.

**Memory**: m registers. A 64-bit hash leaves at most `64 - p + 1` as a rank, so 6 bits per register are enough. With p = 14 that is `16,384 × 6 bits = 12,288 bytes`, exactly Redis's dense encoding.

**Error**: the standard error is `1.04/sqrt(m)`, independent of n. Each register is a small, independent estimate; averaging m of them shrinks the relative noise by sqrt(m), and 1.04 is the constant from the analysis (the older LogLog algorithm, with a geometric mean, has 1.30). Halving the error costs four times the registers. The paper adds that estimates fall within one, two and three standard errors of the truth in about 65%, 95% and 99% of cases.

Measured with the template (relative error over several seeds):

| True distinct n | m | Seeds | Mean error | SD of error | Expected SD |
|---|---|---|---|---|---|
| 1,000 | 16,384 | 20 | -0.18% | 0.56% | under 0.81% (linear counting) |
| 10,000 | 16,384 | 20 | -0.39% | 0.55% | under 0.81% (linear counting) |
| 100,000 | 16,384 | 40 | +0.17% | 0.69% | 0.81% |
| 1,000,000 | 16,384 | 5 | -0.58% | 0.81% | 0.81% |
| 20,000 | 1,024 | 200 | +0.42% | 3.37% | 3.25% |

In the 200-seed run, 63% of estimates were within one standard error and 95% within two, as the paper predicts. Without the small-range correction the same sketch reports about 11,866 for 100 items. An exact Python `set` of one million short strings took 88 MB; the sketch takes 16 KB as a `bytearray` (12 KB packed).

## When to use it

Use HyperLogLog for distinct counts at scale: unique visitors per page per day, distinct IPs per minute, distinct search queries (the Redis docs' example), distinct users across a data warehouse table. It shines when counts must be **merged**: Trino stores `approx_distinct` sketches so that daily sketches combine into weekly uniques, and BigQuery's `HLL_COUNT` functions use HyperLogLog++ sketches the same way.

Do not use it for exact counts (billing, quotas), for membership ("was this user counted?" cannot be answered), for small sets (a set of a few thousand ids is cheap and exact), or for intersections of sets that overlap only slightly.

| Distinct count of 10^6 strings | Memory | Error | Merge |
|---|---|---|---|
| Python `set` | 88 MB measured | exact | union of sets, expensive |
| Bitmap with linear counting | about n bits, must be sized for the maximum | small while sparse | OR |
| HyperLogLog, p = 14 | 12 KB | 0.81% standard error | register max |

Redis's HyperLogLog (`PFADD`, `PFCOUNT`, `PFMERGE`) follows this design: the dense form is a 12,288-byte string of 16,384 six-bit counters, a run-length-encoded sparse form is used while few registers are set, a 16-byte header caches the last estimate (so `PFCOUNT` can write to the key), and `PFCOUNT` on several keys merges them on the fly into a temporary sketch, which is slower and cannot be cached.

## Worked trace

A tiny sketch with p = 4 (16 registers), nine adds of eight distinct names:

```steps
`ada`: hash `0001 0101101100...`: the first 4 bits pick register 1; the first 1 in the rest is at position 2, so rank 2: register 1 becomes 2
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    0  {{2}}  0  0  0  0  0  0  0  0  0  0  0  0  0  0
---
`bob`: hash `0111 0100111100...`: the first 4 bits pick register 7; the first 1 in the rest is at position 2, so rank 2: register 7 becomes 2
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    0  2  0  0  0  0  0  {{2}}  0  0  0  0  0  0  0  0
---
`cy`: hash `1000 0100100100...`: the first 4 bits pick register 8; the first 1 in the rest is at position 2, so rank 2: register 8 becomes 2
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    0  2  0  0  0  0  0  2  {{2}}  0  0  0  0  0  0  0
---
`dee`: hash `0000 1111010110...`: the first 4 bits pick register 0; the first 1 in the rest is at position 1, so rank 1: register 0 becomes 1
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    {{1}}  2  0  0  0  0  0  2  2  0  0  0  0  0  0  0
---
`eve`: hash `0011 0011011110...`: the first 4 bits pick register 3; the first 1 in the rest is at position 3, so rank 3: register 3 becomes 3
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    1  2  0  {{3}}  0  0  0  2  2  0  0  0  0  0  0  0
---
`fay`: hash `0011 1111010000...`: the first 4 bits pick register 3; the first 1 in the rest is at position 1, so rank 1: register 3 already holds 3: no change
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    1  2  0  {{3}}  0  0  0  2  2  0  0  0  0  0  0  0
---
`gus`: hash `0101 1101110010...`: the first 4 bits pick register 5; the first 1 in the rest is at position 1, so rank 1: register 5 becomes 1
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    1  2  0  3  0  {{1}}  0  2  2  0  0  0  0  0  0  0
---
`hal`: hash `0010 0100101101...`: the first 4 bits pick register 2; the first 1 in the rest is at position 2, so rank 2: register 2 becomes 2
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    1  2  {{2}}  3  0  1  0  2  2  0  0  0  0  0  0  0
---
`ada`: hash `0001 0101101100...`: the first 4 bits pick register 1; the first 1 in the rest is at position 2, so rank 2: register 1 already holds 2: no change
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    1  {{2}}  2  3  0  1  0  2  2  0  0  0  0  0  0  0
---
count: 9 of 16 registers are still 0, so use linear counting: 16 ln(16/9) = 9.21 (true answer: 8 distinct names)
    reg    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    val    1  2  2  3  {{0}}  1  {{0}}  2  2  {{0}}  {{0}}  {{0}}  {{0}}  {{0}}  {{0}}  {{0}}
```

The raw formula with `alpha_16 = 0.673` would have said 15.5 for these 8 names; the small-range correction gives 9.2.

## Template

```python
import hashlib
import math


class HyperLogLog:
    def __init__(self, p: int = 14):
        self.p, self.m = p, 1 << p
        self.reg = bytearray(self.m)

    def add(self, item: bytes) -> None:
        x = int.from_bytes(hashlib.blake2b(item, digest_size=8).digest(), "big")
        j = x >> (64 - self.p)                         # first p bits choose the register
        w = x & ((1 << (64 - self.p)) - 1)             # the other 64 - p bits
        rank = (64 - self.p) - w.bit_length() + 1      # leading zeros in w, plus one
        if rank > self.reg[j]:
            self.reg[j] = rank

    def count(self) -> float:
        m = self.m
        alpha = 0.7213 / (1 + 1.079 / m)               # the paper's constant for m >= 128
        e = alpha * m * m / sum(2.0 ** -r for r in self.reg)
        zeros = self.reg.count(0)
        if e <= 2.5 * m and zeros:                     # small range: linear counting
            e = m * math.log(m / zeros)
        return e

    def merge(self, other: "HyperLogLog") -> None:
        self.reg = bytearray(map(max, self.reg, other.reg))
```

## Pitfalls

- **Python's `hash()`.** For small ints it is the identity (`hash(5) == 5`), so every small int lands in register 0 with a huge rank and the estimate is nonsense; for `str` it is salted per process, so sketches from two processes cannot be merged. Use a real 64-bit hash.
- **Merging sketches built differently.** Different p, different hash functions or different seeds give registers that mean different things; the merged estimate is garbage. Store p and the hash name with the sketch.
- **A 32-bit hash at billions of items.** Collisions make it undercount; switch to 64 bits rather than relying on the large-range correction.
- **The mid-range bump.** Around 2.5m to 5m items the raw estimate has a small bias. HyperLogLog++ (Heule, Nunkesser and Hall, 2013), the variant behind BigQuery's functions, improves accuracy and memory for small and medium counts.
- **Inclusion-exclusion for intersections.** With |A| = |B| = 60,000 and a true overlap of 20,000, one run estimated 20,639: 3% off, though each count was within 1%. The error belongs to the union, so small overlaps of big sets are hopeless.

## Check yourself

Q: Redis uses p = 14. What standard error and memory would p = 12 give with 6-bit registers?
A: m = 4,096, so the standard error is `1.04/64`, about 1.63% (twice Redis's 0.81%), and the registers take `4,096 × 6 / 8 = 3,072` bytes, a quarter of the memory.

Q: Why a harmonic mean of `2^M[j]` rather than an arithmetic mean?
A: One register that sees an unusually long run of zeros, say rank 30 when its neighbours sit near 10, adds 2^30 to an arithmetic mean and ruins it. In the harmonic mean it adds `2^-30`, almost nothing, to the sum of reciprocals. High outliers are the typical error of maximum-based estimates, and the harmonic mean is what improved LogLog's 1.30/sqrt(m) to 1.04/sqrt(m).

Q: You keep one sketch per hour of unique visitors. How do you report daily uniques, and why not add the 24 hourly counts?
A: Merge the 24 sketches by register-wise maximum and count the result. Adding hourly counts counts a visitor once for every hour they were active; the maximum gives exactly the sketch of the union, because a register only depends on which distinct hashes reached it.

Q: In the trace, the second `ada` changed nothing. Would it change anything if it had been spelt `Ada`?
A: Yes, probably: `Ada` is a different string, so it has an unrelated hash and lands in some register with some rank. HyperLogLog counts distinct byte strings, so normalise items (case, whitespace, canonical ids) before hashing.

## Lab

- Add `f"visitor-{i}".encode()` for i < 1,000,000 to `HyperLogLog(14)`. Expected: the template reports 991,507, -0.85%, about one standard error low.
- Build A from `u0` to `u59999` and B from `u40000` to `u99999`, then merge. Expected: about 60,377 and 59,782 alone, 99,520 merged (true 100,000), and an inclusion-exclusion overlap of about 20,639 (true 20,000).
- Print the raw formula on an empty sketch. Expected: about 11,817 (0.72m) while `count()` returns 0.0, which is why the correction exists.

> [!know]
> You now know how HyperLogLog turns leading zeros into a distinct count with a 1.04/sqrt(m) error, and how to merge sketches across servers and time.

=== primer | How does a count-min sketch estimate how often each item appears, with a guaranteed error? | 15 min
goal: Size a count-min sketch from epsilon and delta, implement updates, point queries and conservative update, and predict which items it estimates well and which it does not
tag: sketch-cms | Count-min sketch
link: Roughgarden and Valiant, Stanford CS168 lecture 2 notes | https://web.stanford.edu/class/cs168/l/l2.pdf | 25 min: sections 2.3 to 2.6 build the sketch, give a heuristic and then a rigorous error analysis with Markov's inequality, and summarise the space as (e/eps) ln(1/delta) counters
link: Redis docs: Count-min sketch | https://redis.io/docs/latest/develop/data-types/probabilistic/count-min-sketch/#sizing | 5 min: what CMS.INITBYPROB's error and probability arguments mean, and why counts below error × total should be ignored

> [!key]
> A count-min sketch is d rows of w counters, each row with its own hash function. Adding x increments one counter in every row; the estimate is the **minimum** of x's d counters. Collisions only ever add, so it never undercounts, and with `w = ceil(e/ε)` and `d = ceil(ln(1/δ))` the overcount is at most εN with probability at least 1 - δ, where N is the total of all counts (Cormode and Muthukrishnan). Frequent items are measured well; rare ones drown in noise.

## Intuition

You must tally votes for a million candidates but have only 2,719 tally boxes. Assign each candidate a box by hashing the name. A box's tally is the candidate's own votes plus the votes of every other candidate sharing that box, so it can only be too high. Do the same with five independent box assignments (rows): somewhere among the five, your candidate probably shares a box with only light neighbours. The smallest of the five tallies is the least contaminated, and it is still never below the truth.

## How it works

### Update and query

- **add(x, c)**: for each row i, `C[i][h_i(x)] += c`.
- **estimate(x)**: `min over i of C[i][h_i(x)]`.

The rows must use **independent** hash functions; the template slices one BLAKE2b digest into d separate 64-bit values.

### Conservative update

When adding c to x, the true count after the update is at most `estimate(x) + c`, so there is no need to push any of x's counters above that. Conservative update raises each of x's counters only to `max(counter, estimate + c)`. The estimate stays an upper bound and contamination drops, but it only works for positive increments.

### Merge

Two sketches with the same w, d and hash functions merge by adding their counter arrays, which gives exactly the sketch of the combined stream: one sketch per minute adds up into hours and days.

## Cost

**Time**: d hash slices and d counter updates per add or query, O(d) = O(log(1/δ)).

**Error**, derived for one item x:

1. In row i, x's counter holds `f_x` plus the counts of every other item hashed to the same column. Each other item y lands there with probability 1/w, so the expected excess is at most `N/w`.
2. The excess is never negative, so Markov's inequality applies: the excess is at least `e × N/w` with probability at most 1/e. With `w = e/ε` that threshold is εN.
3. The rows are independent, and the minimum exceeds εN only if every row does: probability at most `(1/e)^d`. With `d = ln(1/δ)` that is δ.

**Memory**: `w × d = (e/ε) ln(1/δ)` counters, independent of how many distinct items exist. For ε = 0.001 and δ = 0.01: w = 2,719, d = 5, 13,595 counters, 54 kB as 32-bit integers. A `Counter` of the same stream's 64,635 distinct keys took 2.6 MB for its table alone.

Measured with that sketch on 1,000,000 Zipf-distributed page views (100,000 possible pages, exponent 1.1):

| Items | True count | Mean overcount (relative) |
|---|---|---|
| Top 10 | 10,787 to 134,758 | 0.29% |
| Ranks 1,000 to 1,100 | about 60 to 70 | 90% |
| Last 1,000 (seen once or twice) | 1 to 2 | 6,122% |
| All items | | 60.9 on average, worst 374, none above the 1,000 bound |

The top page (134,758 views) read 134,820; a page seen once read 82. Conservative update cut the mean overcount from 60.9 to 32.9 and the worst from 374 to 294.

## When to use it

Use a count-min sketch for frequencies of the items that matter: request counts per key for hot-key detection or rate limiting, popular URLs or queries, flow sizes in network monitoring, and frequency estimates for cache admission (Caffeine's W-TinyLFU uses a 4-bit count-min sketch, growing by 8 bytes per cache entry; the caching module covers it). It needs no list of keys, merges by addition and has a fixed size.

Do not use it for small counts (the error is a fraction of the whole stream; Redis's docs say counts below error × total should be ignored), when you must list the frequent items (it stores no keys: pair it with a table, as in the next card), or when counts can go down below zero (the minimum no longer bounds anything).

| | `Counter` | Count-min | Misra-Gries (next card) |
|---|---|---|---|
| Memory | one entry per distinct key | (e/ε) ln(1/δ) counters | k counters |
| Error | none | overcount at most εN with probability 1 - δ | undercount at most N/(k+1), always |
| Query any key | yes | yes | only tracked keys |
| Merge | add | add arrays | possible but subtler |

Check what your library does with ε and δ. Redis's docs show `CMS.INITBYPROB` with error 0.001 and probability 0.002 producing a sketch of width 2000 and depth 9 (from `CMS.INFO`); the formulas above give 2,719 and 7. Those Redis numbers match 2/ε and log2(1/δ), different constants for the same idea.

## Worked trace

A toy sketch with w = 5 columns and d = 3 rows, the stream `a b a c a b d`:

```steps
add `a`: columns [4, 1, 4] in rows 0, 1, 2; add 1 to each
           col    0   1   2   3   4
    row 0         0   0   0   0   {{1}}
    row 1         0   {{1}}   0   0   0
    row 2         0   0   0   0   {{1}}
---
add `b`: columns [1, 0, 3] in rows 0, 1, 2; add 1 to each
           col    0   1   2   3   4
    row 0         0   {{1}}   0   0   1
    row 1         {{1}}   1   0   0   0
    row 2         0   0   0   {{1}}   1
---
add `a`: columns [4, 1, 4] in rows 0, 1, 2; add 1 to each
           col    0   1   2   3   4
    row 0         0   1   0   0   {{2}}
    row 1         1   {{2}}   0   0   0
    row 2         0   0   0   1   {{2}}
---
add `c`: columns [0, 0, 3] in rows 0, 1, 2; add 1 to each
           col    0   1   2   3   4
    row 0         {{1}}   1   0   0   2
    row 1         {{2}}   2   0   0   0
    row 2         0   0   0   {{2}}   2
---
add `a`: columns [4, 1, 4] in rows 0, 1, 2; add 1 to each
           col    0   1   2   3   4
    row 0         1   1   0   0   {{3}}
    row 1         2   {{3}}   0   0   0
    row 2         0   0   0   2   {{3}}
---
add `b`: columns [1, 0, 3] in rows 0, 1, 2; add 1 to each
           col    0   1   2   3   4
    row 0         1   {{2}}   0   0   3
    row 1         {{3}}   3   0   0   0
    row 2         0   0   0   {{3}}   3
---
add `d`: columns [4, 4, 4] in rows 0, 1, 2; add 1 to each
           col    0   1   2   3   4
    row 0         1   2   0   0   {{4}}
    row 1         3   3   0   0   {{1}}
    row 2         0   0   0   3   {{4}}
---
query `a`: counters [4, 3, 4], estimate = min = 3 (true count 3)
           col    0   1   2   3   4
    row 0         1   2   0   0   {{4}}
    row 1         3   {{3}}   0   0   1
    row 2         0   0   0   3   {{4}}
---
query `d`: counters [4, 1, 4], estimate = min = 1 (true count 1)
           col    0   1   2   3   4
    row 0         1   2   0   0   {{4}}
    row 1         3   3   0   0   {{1}}
    row 2         0   0   0   3   {{4}}
```

All five estimates in this run happen to be exact (`b` reads 2, `c` 1, `e` 0), although every row has collisions: the minimum picked a clean row each time.

## Template

```python
import hashlib
import math


class CountMin:
    def __init__(self, eps: float, delta: float, conservative: bool = False):
        self.w = math.ceil(math.e / eps)
        self.d = math.ceil(math.log(1 / delta))        # at most 8 rows with one 64-byte digest
        self.rows = [[0] * self.w for _ in range(self.d)]
        self.total, self.conservative = 0, conservative

    def _cols(self, item: bytes) -> list[int]:
        d = hashlib.blake2b(item, digest_size=8 * self.d).digest()
        return [int.from_bytes(d[8 * i:8 * i + 8], "little") % self.w for i in range(self.d)]

    def add(self, item: bytes, count: int = 1) -> None:
        cols = self._cols(item)
        self.total += count
        if self.conservative:                          # raise each counter only as far as needed
            target = min(row[c] for row, c in zip(self.rows, cols)) + count
            for row, c in zip(self.rows, cols):
                row[c] = max(row[c], target)
        else:
            for row, c in zip(self.rows, cols):
                row[c] += count

    def estimate(self, item: bytes) -> int:
        return min(row[c] for row, c in zip(self.rows, self._cols(item)))
```

## Pitfalls

- **Correlated rows.** Deriving row i's column as `(h1 + i × h2) mod w` (fine for a Bloom filter) makes rows collide together: two items that share columns in two rows share them in all, and the `e^-d` bound collapses to about `1/w^2`. Give each row its own hash.
- **Reading the tail.** A page seen once read 82. Report only counts well above εN, or use exact counters for the few keys you care about.
- **A bound that grows forever.** εN grows with the stream. Keep one sketch per time window and merge the windows you need, or decay old counts.
- **Counter overflow.** Fixed-width counters (4-bit in Caffeine) saturate; design for it or use wider counters.
- **Treating it as a set.** It cannot tell you which keys exist; querying a never-seen key returns the noise in its columns.

## Check yourself

Q: In the trace, row 1 put `c` in the same column as `b`. What would a sketch with only row 1 report for `b`, and why does the three-row sketch get it right?
A: Row 1's column 0 holds 3 (two `b`s and one `c`), so a one-row sketch says 3. In row 0, `b` shares column 1 with nothing else, so it holds 2, and the minimum over the rows is 2, the true count.

Q: Size a sketch for ε = 0.0001 and δ = 0.001. What does it guarantee on a stream of a billion events?
A: `w = ceil(e/0.0001) = 27,183`, `d = ceil(ln 1000) = 7`, so 190,281 counters, about 761 kB at 4 bytes each. For any single item, the estimate exceeds the truth by more than `0.0001 × 10^9 = 100,000` with probability at most 0.1%.

Q: Why can conservative update never make an estimate fall below the true count?
A: Before the update every counter of x is at least `f_x`, so `estimate(x) >= f_x`. After adding c the truth is `f_x + c <= estimate(x) + c`, and conservative update sets each of x's counters to at least `estimate(x) + c`. Counters of other items only ever increase, so their bounds also survive.

## Lab

- Build `CountMin(0.001, 0.01)` and check `w, d`. Expected: 2719 and 5. Feed the lab's Zipf stream and compare the top page and a page seen once. Expected: about 134,820 for a true 134,758, and about 82 for a true 1.
- Size (ε, δ) = (0.001, 0.002) with the formulas. Expected: (2719, 7), against width 2000 and depth 9 from Redis's `CMS.INFO` example.
- Turn on `conservative=True` on the same stream. Expected: the mean overcount over all pages drops from about 60.9 to about 32.9.

> [!know]
> You now know how a count-min sketch bounds frequency error by εN with probability 1 - δ, how to size it, and why it is only trustworthy for frequent items.

=== primer | How do you find the heavy hitters in a stream without counting everything? | 14 min
goal: Find every item above a frequency threshold in one pass with k counters (Misra-Gries or Space-Saving), state their error bounds, and confirm candidates exactly with a second pass or a count-min sketch
tag: sketch-heavy | Heavy hitters with k counters
link: Roughgarden and Valiant, Stanford CS168 lecture 2 notes | https://web.stanford.edu/class/cs168/l/l2.pdf | 15 min: section 1 (the majority vote, the heavy hitters problem and why an exact one-pass answer needs linear space) and section 2.7 (heavy hitters from a count-min sketch plus a heap)
link: Redis docs: Top-K | https://redis.io/docs/latest/develop/data-types/probabilistic/top-k/ | 5 min: how HeavyKeeper's count-with-exponential-decay keeps small flows out, and the default width, depth and decay

> [!key]
> To find every item that occurs more than N/(k+1) times in a stream of N items, k counters are enough. **Misra-Gries** keeps up to k (item, count) pairs; when a new item arrives and all k are taken, every counter drops by one, which cancels k + 1 occurrences at once. That can happen at most N/(k+1) times, so each count is low by at most N/(k+1) and no heavy item can vanish. **Space-Saving** instead replaces the smallest counter and overcounts by at most N/k. A second pass over the few candidates turns either into exact answers.

## Intuition

Find the majority in a crowd: people pair off with anyone who disagrees with them and both sit down. If one opinion holds more than half the crowd, someone holding it is still standing at the end, because each opponent can cancel only one of them. That is the Boyer-Moore majority vote: one candidate and one counter.

Generalise to k candidates. Whenever a newcomer differs from all k current candidates and there is no free counter, the newcomer and one supporter of each of the k candidates sit down together: k + 1 different items cancel. An item with more than N/(k+1) supporters cannot be cancelled away completely, since each cancellation removes only one of its supporters and there are at most N/(k+1) cancellations.

## How it works

### Misra-Gries

For each item x: if x has a counter, increment it; else if fewer than k counters exist, start x at 1; else decrement every counter and delete those that reach 0 (x is discarded). At the end, every item with true frequency above N/(k+1) has a counter, and each reported count c satisfies `f - N/(k+1) <= c <= f`.

### Space-Saving

Same table, different eviction: if x is new and the table is full, find the item with the smallest count `min`, replace it with x and give x the count `min + 1`. The counts always sum to exactly N, every monitored count is at least the truth and at most the truth plus N/k, and every item above N/k is monitored. Its counts are upper bounds, which suits "show me the top k" directly.

### Count-min plus a small table

Keep a count-min sketch of every item and a table (or min-heap) of the items whose estimate exceeds the threshold, updating an item's entry as it arrives. This also answers point queries for any key. Redis's Top-K type is in this family: a HeavyKeeper sketch, whose 'count-with-exponential-decay' counters let small flows fade, plus a min-heap of the k items with the highest counts.

### Two passes when you can

One pass with small memory cannot give exact answers (CS168 section 1.3 shows it needs linear space). But if the data can be read twice, pass 1 produces at most k candidates and pass 2 counts just those exactly, so false positives disappear.

## Cost

**Misra-Gries memory**: k counters. **Time**: an increment or insert is O(1); a decrement-all step costs O(k). Each such step destroys k + 1 units of count (one from each of the k counters plus the discarded arrival) and the stream only supplies N units, so there are at most N/(k+1) of them, costing O(k × N/(k+1)) = O(N) in total. Amortised **O(1) per item**.

**Error**: an item's counter loses at most 1 per decrement-all step (an arriving item that is discarded loses that occurrence in the same step), so the undercount is at most the number of steps, N/(k+1). Any item with more than N/(k+1) occurrences therefore ends with a positive counter.

**Space-Saving**: the template finds the minimum by scanning, O(k) per eviction; production versions keep counters in a "stream-summary" of linked count buckets for O(1), or a heap for O(log k).

Measured on 1,000,000 Zipf-distributed page views where 10 pages exceed 1% of the traffic (10,787 to 134,758 views):

| Method | k | All 10 found | Worst error | Bound |
|---|---|---|---|---|
| Misra-Gries | 99 | yes | 7,037 low | 10,000 |
| Space-Saving | 99 | yes | 7,120 high | 10,101 |
| Misra-Gries | 200 | yes | 3,106 low | 4,975 |
| Space-Saving | 200 | yes | 3,124 high | 5,000 |
| Two passes (Misra-Gries k = 100, then exact) | 100 | exactly the 10, exact counts | 0 | |
| Count-min (ε = 0.0005) plus a 10-entry table | 10 | yes, in the right order | | |

## When to use it

Use these for "top talkers" questions over streams: hot keys in a cache cluster, the most requested URLs, the busiest network flows, the most frequent error messages, abusive clients. Choose Misra-Gries when you can make a second pass or want counts that are never overstated; Space-Saving when you want a direct top-k with upper-bound counts; count-min plus a table when you also need estimates for arbitrary keys or must merge sketches by addition.

Do not use them when the light items matter (they are discarded by design), or when you need the exact top k in one pass (impossible in small memory; make two passes or accept the bounds).

## Worked trace

Misra-Gries with k = 2 counters on the stream `a b a c a d b a e a` (N = 10):

```steps
item 1: `a` is new and a counter is free: start it at 1
    stream    {{a}}
    counters  a: 1
---
item 2: `b` is new and a counter is free: start it at 1
    stream    a {{b}}
    counters  a: 1, b: 1
---
item 3: `a` has a counter: increment it
    stream    a b {{a}}
    counters  a: 2, b: 1
---
item 4: `c` is new and both counters are taken: decrement every counter, drop zeros, discard `c`
    stream    a b a {{c}}
    counters  a: 1
---
item 5: `a` has a counter: increment it
    stream    a b a c {{a}}
    counters  a: 2
---
item 6: `d` is new and a counter is free: start it at 1
    stream    a b a c a {{d}}
    counters  a: 2, d: 1
---
item 7: `b` is new and both counters are taken: decrement every counter, drop zeros, discard `b`
    stream    a b a c a d {{b}}
    counters  a: 1
---
item 8: `a` has a counter: increment it
    stream    a b a c a d b {{a}}
    counters  a: 2
---
item 9: `e` is new and a counter is free: start it at 1
    stream    a b a c a d b a {{e}}
    counters  a: 2, e: 1
---
item 10: `a` has a counter: increment it
    stream    a b a c a d b a e {{a}}
    counters  a: 3, e: 1
```

The true counts are a = 5, b = 2, e = 1, c = d = 1. `a` is reported as 3, low by 2, within the bound `N/(k+1) = 3.33`; `b` (2) was dropped, which the bound allows; `e` is still in the table although it is light, which is why candidates need checking.

## Template

```python
def misra_gries(stream, k: int) -> dict:
    """At most k counters; every count is low by at most N / (k + 1)."""
    counters = {}
    for x in stream:
        if x in counters:
            counters[x] += 1
        elif len(counters) < k:
            counters[x] = 1
        else:                                          # x and k residents each lose one
            for y in list(counters):
                counters[y] -= 1
                if counters[y] == 0:
                    del counters[y]
    return counters


def heavy_hitters(stream_factory, phi: float, k: int) -> dict:
    """Items with frequency above phi * N, exactly: pass 1 finds candidates, pass 2 counts them."""
    candidates = misra_gries(stream_factory(), k)      # k >= 1/phi guarantees no heavy item is missed
    exact, n = dict.fromkeys(candidates, 0), 0
    for x in stream_factory():
        n += 1
        if x in exact:
            exact[x] += 1
    return {x: c for x, c in exact.items() if c > phi * n}


def space_saving(stream, k: int) -> dict:
    """k counters; every monitored count is high by at most N / k. O(k) per eviction for clarity."""
    counts = {}
    for x in stream:
        if x in counts:
            counts[x] += 1
        elif len(counts) < k:
            counts[x] = 1
        else:
            victim = min(counts, key=counts.get)
            counts[x] = counts.pop(victim) + 1
    return counts
```

`stream_factory` is any zero-argument function that returns a fresh iterator, such as `lambda: open(path, "rb")`, because the data is read twice.

## Pitfalls

- **Off by one in k.** k counters catch everything above N/(k+1). To catch everything above 1% you need k >= 99; k = 100 is the safe round number.
- **Reading counts as frequencies.** Misra-Gries counts are lower bounds and Space-Saving counts are upper bounds. Report the bound with the number, or recount.
- **Reporting candidates as answers.** Light items such as `e` in the trace can sit in the table at the end. Verify with a second pass, a count-min estimate, or by reporting only counts above the bound.
- **Space-Saving's minimum scan in a hot loop.** O(k) per eviction is fine for k = 100 but not for k = 100,000; use a heap with lazy updates or the stream-summary structure.

## Check yourself

Q: Prove that an item with more than N/(k+1) occurrences always survives Misra-Gries.
A: Each decrement-all step removes one unit from each of k counters and discards one arriving item, k + 1 units in all, and the stream contains only N units, so there are at most N/(k+1) steps. The item loses at most one unit per step, so its counter ends at least `f - N/(k+1) > 0`: it is still in the table.

Q: Space-Saving with k counters reports `{x: 40}` after N = 1,000 items with k = 50. What do you know about x's true count?
A: Monitored counts are never below the truth and are at most N/k = 20 above it, so the true count is between 20 and 40. (The minimum counter in the table is a tighter overcount bound if you track it.)

Q: You need the top queries across 50 servers, each running Misra-Gries with the same k on its own stream. Why does the union of the 50 candidate lists contain every query that is above N/(k+1) overall?
A: Suppose a query is not a candidate on any server: then on every server s its local count is at most `N_s/(k+1)`. Summing over servers gives at most `N/(k+1)` overall, so it is not globally heavy. Collect the union of candidates and count them exactly in a second pass (or with merged count-min sketches).

## Lab

- Run `misra_gries("a b a c a d b a e a".split(), 2)`. Expected: `{'a': 3, 'e': 1}`; true counts a = 5 and e = 1, both within 3.33.
- On a 1,000,000-event Zipf stream (the module lab's generator), run `misra_gries(stream, 99)` and `heavy_hitters(lambda: iter(stream), 0.01, 100)`. Expected: all 10 pages above 1% are among the candidates, the worst undercount is 7,037 (bound 10,000), and the two-pass result is exactly those 10 pages with their true counts, from 134,758 down to 10,787.
- Run `space_saving(stream, 99)` and sum the counts. Expected: exactly 1,000,000; worst overcount 7,120.

> [!know]
> You now know how Misra-Gries and Space-Saving find every item above N/(k+1) with k counters, and how a second pass or a count-min sketch confirms them.

=== primer | How can a few hundred numbers estimate how similar two documents are? | 15 min
goal: Turn documents into shingle sets, compute MinHash signatures, prove that two signatures agree in each position with probability equal to the Jaccard similarity, and choose the signature length for the error you can accept
tag: sketch-minhash | MinHash signatures
link: Leskovec, Stanford CS246 slides: Finding similar items | https://web.stanford.edu/class/cs246/slides/03-lsh.pdf | 15 min: slides 17-21 (shingling and Jaccard similarity) and 24-33 (min-hashing, the proof that Pr[h(C1) = h(C2)] = sim(C1, C2), and row hashing instead of permutations)
link: datasketch docs: MinHash | https://ekzhu.com/datasketch/minhash.html#the-affine-permutation-scheme | 5 min: how a production Python library builds its hash functions, and why 32-bit input hashes start to add error past about 100 million elements per set

> [!key]
> Represent each document by its set of **shingles** (overlapping word n-grams) and measure similarity with the **Jaccard index** `J = |A ∩ B| / |A ∪ B|`. Hash every shingle with a random hash function and keep the minimum: two documents get the same minimum with probability exactly J. Repeat with k independent hash functions to get a **signature** of k numbers; the fraction of agreeing positions estimates J with standard error `sqrt(J(1 - J)/k)`, about 0.044 for k = 128 at J = 0.5, however long the documents are.

## Intuition

Put every shingle from either document into one deck and shuffle it. Turn over cards until you reach the first one; it is equally likely to be any card in the union. It belongs to **both** documents with probability `|A ∩ B| / |A ∪ B|`, which is J. Now notice that "the first card of the union" is simply the smaller of "the first card of A" and "the first card of B", and those two are the same card exactly when the first card of the union is in the intersection. So "do A and B have the same first card under a random shuffle?" is a coin that comes up heads with probability J. Flip it 128 times with 128 shuffles and count heads.

## How it works

### Shingles

Normalise the text (lower case, collapse whitespace; often strip punctuation), split into words and take every run of n consecutive words: "the quick brown fox jumps" has the 3-word shingles "the quick brown", "quick brown fox", "brown fox jumps". Hash each shingle to a 64-bit integer so that sets are cheap to store. Word 5-grams are common for web text (both Lee et al. and FineWeb use them).

### Min-hashing

A truly random permutation of all possible shingles is impossible to store, so use a random hash function instead: `h(x) = (a x + b) mod p` with a large prime p (the template uses the Mersenne prime 2^61 - 1) and random a, b. The signature of a set S is `[min of h_i(x) over x in S, for i = 1..k]`, and `estimate(A, B)` is the fraction of positions where the signatures agree.

### Why the probability is exactly J

Under a random permutation, the minimum over A ∪ B is equally likely to be any of its `|A ∪ B|` elements. If that element is in A ∩ B, it is the minimum of A and of B, so they agree. If it is only in A, B's minimum is some other element with a larger value, so they differ (and symmetrically). Hence `P(agree) = |A ∩ B| / |A ∪ B| = J`.

## Cost

**Shingling**: O(L) for a document of L words. **Signature**: k hash evaluations per shingle, O(k × |S|); for a 200-word document and k = 128 that is about 25,600 multiply-mod operations, the dominant cost of the whole pipeline. **Storage**: k numbers per document, 1 KB at k = 128 with 8-byte values, whatever the document length. **Comparison**: O(k).

**Error**, derived: each position agrees independently with probability J, so the number of agreements is binomial(k, J). The estimate (agreements / k) has mean J and standard deviation `sqrt(J(1 - J)/k)`.

Measured with the template on 200 random set pairs with J = 0.5:

| k | Mean estimate | SD measured | SD formula |
|---|---|---|---|
| 16 | 0.498 | 0.114 | 0.125 |
| 64 | 0.498 | 0.060 | 0.0625 |
| 128 | 0.500 | 0.043 | 0.044 |
| 256 | 0.502 | 0.029 | 0.031 |

Quadrupling k halves the error. On real text the shingle size matters as much as k: for "the quick brown fox jumps over the lazy dog near the river bank today" against the same sentence with "cat" for "dog", 2-word shingles give J = 0.733 (11 of 15) and 3-word shingles J = 0.600 (9 of 15), estimated as 0.742 and 0.578 with k = 128. One changed word removes up to n shingles from each side.

## When to use it

Use MinHash when you need set similarity between many large sets: near-duplicate web pages and training documents, plagiarism and boilerplate detection, users with similar sets of items, clustering by shared features. It turns any set into a fixed-size signature that can be stored, compared in O(k) and indexed with LSH (next card).

Do not use it for tiny sets (just compute the exact Jaccard), for similarity of weighted vectors or embeddings (use cosine similarity with random hyperplanes, covered in the vector search module), or when what you mean by "similar" is edit distance or containment: Lee et al. use MinHash only to find candidates and then require an edit similarity above 0.8.

| Shingle size n | Effect |
|---|---|
| Small (1-2 words) | Unrelated documents share many shingles; J is high for everything |
| Medium (3-5 words) | Common choice for near-duplicate text; one edit removes n shingles |
| Large (8+ words) | Only long verbatim overlaps count; small edits look like big changes |

## Worked trace

A toy universe: shingle ids 0 to 10 and six hash functions `h(x) = (a x + b) mod 11`, which are true permutations of 0..10. A = {1, 3, 4, 7, 9} and B = {1, 3, 4, 8, 9}, so J = 4/6 = 0.67. Each row lists `x:h(x)`, with the minimum highlighted:

```steps
h1(x) = (3x + 1) mod 11: min over A is 0 (at 7), over B is 2 (at 4): differ; 0 of 1 agree so far
    A  1:4  3:10  4:2  {{7:0}}  9:6
    B  1:4  3:10  {{4:2}}  8:3  9:6
---
h2(x) = (5x + 4) mod 11: min over A is 2 (at 4), over B is 0 (at 8): differ; 0 of 2 agree so far
    A  1:9  3:8  {{4:2}}  7:6  9:5
    B  1:9  3:8  4:2  {{8:0}}  9:5
---
h3(x) = (7x + 2) mod 11: min over A is 1 (at 3), over B is 1 (at 3): **agree**; 1 of 3 agree so far
    A  1:9  {{3:1}}  4:8  7:7  9:10
    B  1:9  {{3:1}}  4:8  8:3  9:10
---
h4(x) = (2x + 9) mod 11: min over A is 0 (at 1), over B is 0 (at 1): **agree**; 2 of 4 agree so far
    A  {{1:0}}  3:4  4:6  7:1  9:5
    B  {{1:0}}  3:4  4:6  8:3  9:5
---
h5(x) = (4x + 6) mod 11: min over A is 0 (at 4), over B is 0 (at 4): **agree**; 3 of 5 agree so far
    A  1:10  3:7  {{4:0}}  7:1  9:9
    B  1:10  3:7  {{4:0}}  8:5  9:9
---
h6(x) = (6x + 0) mod 11: min over A is 2 (at 4), over B is 2 (at 4): **agree**; 4 of 6 agree so far
    A  1:6  3:7  {{4:2}}  7:9  9:10
    B  1:6  3:7  {{4:2}}  8:4  9:10
```

Four of six positions agree: estimate 0.67, which equals J this time. With six hash functions the standard error is `sqrt(0.67 × 0.33 / 6)`, about 0.19, so that was luck.

## Template

```python
import hashlib
import random

P61 = (1 << 61) - 1                                    # a Mersenne prime


def shingles(text: str, n: int = 5) -> set[int]:
    """64-bit hashes of the word n-grams of text."""
    words = text.lower().split()
    grams = (" ".join(words[i:i + n]) for i in range(max(1, len(words) - n + 1)))
    return {int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "little") for g in grams}


class MinHasher:
    def __init__(self, k: int = 128, seed: int = 1):
        rng = random.Random(seed)
        self.ab = [(rng.randrange(1, P61), rng.randrange(P61)) for _ in range(k)]

    def signature(self, items: set[int]) -> list[int]:
        return [min((a * x + b) % P61 for x in items) for a, b in self.ab]


def estimate_jaccard(s1: list[int], s2: list[int]) -> float:
    return sum(x == y for x, y in zip(s1, s2)) / len(s1)
```

Every document must be signed with the same `MinHasher` (same seed), or the positions do not correspond. For speed, vectorise `signature` with NumPy over all shingles at once.

## Pitfalls

- **Python's `hash()` for shingles.** It is salted per process, so signatures from different runs or machines are incomparable. Use a fixed hash such as BLAKE2b, xxHash or murmur3.
- **Different seeds or k between documents.** Signatures from different hash families agree only by accident.
- **No normalisation.** Case, whitespace, HTML and boilerplate (menus, cookie banners) dominate the shingle sets, and pages look similar because of their templates rather than their content. Extract main text first.
- **k too small for the decision.** At k = 16 the standard deviation is about 0.11, so a pair at 0.7 and a pair at 0.8 are indistinguishable. Choose k from `J(1 - J)/k` and the gap you need to resolve.
- **Expecting order to matter.** A document and the same paragraphs shuffled share almost all shingles except those at paragraph boundaries; MinHash calls them near-duplicates.

## Check yourself

Q: With k = 128 hash functions and J = 2/3, how many agreeing positions do you expect, and what range is normal?
A: `128 × 2/3`, about 85. The count is binomial with standard deviation `sqrt(128 × 2/3 × 1/3)`, about 5.3, so roughly 75 to 96 (two standard deviations) is normal.

Q: Why does replacing a random permutation with `h(x) = (a x + b) mod p` still work in practice?
A: The proof only needs every element of A ∪ B to be equally likely to have the smallest hash. A random linear map modulo a large prime is a permutation of 0..p-1 and spreads distinct inputs almost uniformly; it is not a perfectly min-wise independent family, but the bias is tiny for real data, and measured estimates match `sqrt(J(1 - J)/k)` (0.043 against 0.044 at k = 128).

Q: You want the standard error at J = 0.8 to be at most 0.02. How large must k be?
A: `sqrt(0.8 × 0.2 / k) <= 0.02` means `k >= 0.16 / 0.0004 = 400`.

## Lab

- Compute 3-word shingles for "the quick brown fox jumps over the lazy dog near the river bank today" and the same sentence with "cat" in place of "dog". Expected: 12 shingles each, 9 shared, 15 in the union, J = 0.600; `MinHasher(128, seed=1)` estimates 0.578.
- Repeat the measurement table for k = 64 and k = 256 on 200 random pairs with J = 0.5 (sets of 300 numbers overlapping in 200). Expected: standard deviations near 0.060 and 0.029.

> [!know]
> You now know how MinHash turns a document into k numbers whose agreement rate is an unbiased estimate of Jaccard similarity, and how to choose k.

=== primer | How does LSH banding find similar pairs without comparing every pair? | 15 min
goal: Split MinHash signatures into b bands of r rows, derive the S-curve 1 - (1 - s^r)^b, choose b and r for a target similarity, and turn candidate pairs into clusters of duplicates
tag: sketch-lsh | LSH banding
link: Leskovec, Stanford CS246 slides: Finding similar items | https://web.stanford.edu/class/cs246/slides/03-lsh.pdf | 15 min: slides 35-53: banding, the worked b = 20, r = 5 example at s = 0.8 and s = 0.3, and the S-curve tables for choosing r and b
link: datasketch docs: MinHash LSH | https://ekzhu.com/datasketch/lsh.html#retrieval-characteristics-and-parameter-tuning | 5 min: how a production library picks b and r from a threshold, and how weighting false positives or false negatives moves the curve

> [!key]
> Comparing every pair of a million documents means 5 × 10^11 comparisons. **Locality-sensitive hashing** with banding cuts each k-number MinHash signature into **b bands of r rows** and hashes each band to a bucket; documents that share a bucket in at least one band become **candidate pairs**, and only those are checked. A pair with Jaccard similarity s becomes a candidate with probability `1 - (1 - s^r)^b`, an S-shaped curve that rises steeply near `(1/b)^(1/r)`: pairs well above it are almost always found, pairs well below it are almost never compared.

## Intuition

Requiring a whole band of r positions to agree is strict: it happens with probability s^r, which is tiny unless s is high. Giving the pair b separate bands to try is lenient: one success is enough. Strict-AND inside a band and lenient-OR across bands combine into a sharp switch. Two near-copies (s = 0.9) will almost surely match some band exactly; two unrelated pages (s = 0.1) will almost never match a whole band.

## How it works

### Banding

For each band t = 0..b-1, take positions `t×r .. t×r + r - 1` of every signature, use that tuple (plus the band number) as a bucket key, and group documents by key. Every pair inside a bucket is a candidate.

### Verify

Candidates include false positives, pairs that matched one band by luck. Compute the real similarity for each candidate: exact Jaccard of the shingle sets, the MinHash estimate from the full signature, or an expensive measure such as edit similarity.

### From pairs to clusters

Deduplication wants groups, not pairs. Put confirmed pairs into a **union-find** structure (the union-find module) and keep one document per component. This is **transitive**: if A matches B and B matches C, all three are one cluster even if A and C are not similar, a deliberate choice in FineWeb's pipeline.

## Cost

The S-curve, derived for one pair with similarity s:

1. Each signature position agrees with probability s, independently, so a whole band of r agrees with probability `s^r`.
2. A band fails with probability `1 - s^r`; all b bands fail with `(1 - s^r)^b`.
3. So the pair becomes a candidate with probability `P(s) = 1 - (1 - s^r)^b`.
4. The curve is steepest near the s where `s^r = 1/b`, that is `s* = (1/b)^(1/r)`: the approximate threshold.

| Setting | s* | s = 0.5 | 0.7 | 0.75 | 0.8 | 0.85 | 0.9 |
|---|---|---|---|---|---|---|---|
| b = 20, r = 5 (100 hashes) | 0.549 | 0.470 | 0.975 | 0.996 | 0.9996 | 1.000 | 1.000 |
| FineWeb: 14 bands of 8 (112 hashes) | 0.719 | 0.053 | 0.565 | 0.772 | 0.924 | 0.988 | 0.9996 |
| Lee et al.: 450 bands of 20 (9,000 hashes) | 0.737 | 0.0004 | 0.302 | 0.761 | 0.995 | 1.000 | 1.000 |

For b = 20, r = 5 a pair at s = 0.3 is a candidate with probability 0.0475 (the CS246 slides' example). FineWeb's paper quotes 56%, 77%, 92% and 98.8% at 0.7, 0.75, 0.8 and 0.85, which the formula reproduces. More hashes buy a steeper curve: Lee et al.'s 9,000 hashes miss almost nothing above 0.8 and admit far fewer pairs near 0.6.

**Time**: computing signatures dominates (previous card); banding is O(N × b) bucket insertions plus the candidate pairs, which in a healthy setting are a small multiple of the true pairs. **Memory**: N × b bucket entries. An empirical check with b = 10, r = 5 on 300 synthetic pairs per similarity gave candidate rates 0.257 at J = 0.5 and 0.800 at J = 0.7, against 0.272 and 0.841 from the formula.

## When to use it

Use MinHash LSH whenever you need all similar pairs (or all near-duplicates) in a collection too big for all-pairs comparison: deduplicating web crawls and training corpora, clustering near-identical support tickets or bug reports, finding mirrored pages. Tune it with three knobs: more rows r per band raise the threshold and cut false positives; more bands b lower it and cut false negatives; more hashes in total make the curve steeper but cost more hashing.

Do not use it for a few thousand documents (all pairs is a few million comparisons, fine), when you need guaranteed recall below the curve, or for similarity that is not Jaccard (cosine needs a different LSH family, random hyperplanes).

In production: FineWeb deduplicated each Common Crawl snapshot with 5-gram shingles, 112 hashes in 14 buckets of 8, transitive clustering, and one random document kept per cluster; deduplicating all 96 snapshots against each other (which removed up to 90% of the oldest ones) trained models barely better than no deduplication, so per-snapshot deduplication won. Lee et al.'s NearDup used 9,000 hashes in 450 bands of 20, then required Jaccard and edit similarity above 0.8, and found connected components. The datasketch library chooses b and r from a threshold, and can weight false positives against false negatives.

## Worked trace

Four toy documents with 6-number signatures (the toy hashes of the previous card), b = 3 bands of r = 2:

```steps
Signatures of four documents (6 toy MinHashes each), split into b = 3 bands of r = 2 rows
    d1  0 2  |  1 0  |  0 2
    d2  2 0  |  1 0  |  0 2
    d3  1 1  |  0 2  |  2 0
    d4  1 0  |  0 2  |  3 0
---
band 0: hash each document's pair of values to a bucket; no bucket is shared
    d1  (0, 2)
    d2  (2, 0)
    d3  (1, 1)
    d4  (1, 0)
---
band 1: hash each document's pair of values to a bucket; shared buckets: {d1, d2}, {d3, d4}
    {{d1  (1, 0)}}   <- shares a bucket
    {{d2  (1, 0)}}   <- shares a bucket
    {{d3  (0, 2)}}   <- shares a bucket
    {{d4  (0, 2)}}   <- shares a bucket
---
band 2: hash each document's pair of values to a bucket; shared buckets: {d1, d2}
    {{d1  (0, 2)}}   <- shares a bucket
    {{d2  (0, 2)}}   <- shares a bucket
    d3  (2, 0)
    d4  (3, 0)
---
candidate pairs = pairs that share at least one band: [('d1', 'd2'), ('d3', 'd4')]; verify each with the real Jaccard (both are 0.67)
    (d1, d2)  J = 0.67
    (d3, d4)  J = 0.67
    (d1, d3)  J = 0.00  never compared
```

Only 2 of the 6 possible pairs were ever compared, and both real near-duplicate pairs were found.

## Template

```python
from collections import defaultdict
from itertools import combinations


def lsh_candidates(sigs: dict, b: int, r: int) -> set[tuple]:
    """sigs maps doc id -> MinHash signature (length >= b * r). Returns pairs sharing a band."""
    pairs = set()
    for band in range(b):
        buckets = defaultdict(list)
        for doc, sig in sigs.items():
            buckets[tuple(sig[band * r:(band + 1) * r])].append(doc)
        for docs in buckets.values():
            pairs.update(combinations(sorted(docs), 2))
    return pairs


def s_curve(s: float, b: int, r: int) -> float:
    return 1 - (1 - s ** r) ** b


def choose_bands(k: int, threshold: float) -> tuple[int, int]:
    """Split k MinHashes into b bands of r rows so that (1/b) ** (1/r) is closest to threshold."""
    options = [(b, k // b) for b in range(1, k + 1)]
    return min(options, key=lambda br: abs((1 / br[0]) ** (1 / br[1]) - threshold))
```

## Pitfalls

- **Giant buckets.** Boilerplate pages can put hundreds of thousands of documents in one bucket, and `combinations` then produces billions of pairs. For clustering, union each bucket member with the bucket's first member instead (linear in bucket size), or cap and inspect huge buckets.
- **Mixing bands in one table.** If band 0's key `(3, 7)` and band 1's key `(3, 7)` share a dictionary, unrelated positions match. Key on (band, values), as the template does with one dictionary per band.
- **Setting s* equal to your threshold.** At s* the recall is only about half to two thirds. With 128 hashes, (7, 18) has s* = 0.90 but finds only 68% of pairs at exactly 0.9; (11, 11) has s* = 0.80 and finds 98.4% at 0.9, at the cost of more candidates to verify (63% of pairs at 0.8, 20% at 0.7). Put the curve's steep part below the threshold and verify.
- **Skipping verification.** Candidates near the threshold are often false positives; FineWeb accepted band matches directly, Lee et al. verified with edit similarity. Decide consciously.
- **Notation.** Papers swap the letters: Lee et al. write the probability as `1 - (1 - s^b)^r` with b = 20 hashes per band and r = 450 bands. Check which is which before copying parameters.

## Check yourself

Q: With b = 20 and r = 5, how likely is a pair with s = 0.8 to become a candidate, and one with s = 0.3?
A: `0.8^5 = 0.328`, so `1 - (1 - 0.328)^20 = 0.9996`. `0.3^5 = 0.00243`, so `1 - (1 - 0.00243)^20 = 0.0475`. About 1 in 3,000 true pairs at 0.8 is missed, and about 1 in 21 pairs at 0.3 is a wasted comparison.

Q: FineWeb (112 hashes) and Lee et al. (9,000 hashes) both aim at about 0.75 to 0.8. What does the extra 80 times the hashing buy?
A: A much steeper curve. At s = 0.7 FineWeb makes 56% of pairs candidates against 30% for Lee et al.; at s = 0.8 FineWeb finds 92% against 99.5%. Lee et al. lose fewer true duplicates above the threshold and check fewer pairs just below it.

Q: After banding, documents A-B and B-C are confirmed near-duplicates but A-C has Jaccard 0.4. What does union-find clustering do, and is that acceptable?
A: It puts A, B and C in one cluster and keeps one of them, removing A or C although they are not similar to each other. For deduplication this is usually acceptable (they share a near-copy B, typically templated or boilerplate content) and is what FineWeb does deliberately; if it is not, cluster with a stricter rule, for example keep pairs only and compare each document with the cluster's representative.

## Lab

- Evaluate `s_curve(s, 14, 8)` for s = 0.7, 0.75, 0.8, 0.85. Expected: 0.5645, 0.7716, 0.9235, 0.9884, matching FineWeb's quoted 56%, 77%, 92% and 98.8%.
- Run `choose_bands(112, 0.75)`. Expected: (12, 9), with `(1/12) ** (1/9)` about 0.759.
- Run `lsh_candidates` on the trace's four signatures with b = 3, r = 2. Expected: `{('d1', 'd2'), ('d3', 'd4')}`.

> [!know]
> You now know how banding turns MinHash signatures into candidate pairs, how the S-curve sets the trade-off between missed and wasted pairs, and how to choose b and r.

=== primer | How do you keep a uniform random sample of a stream whose length you do not know? | 12 min
goal: Implement reservoir sampling (Algorithm R), prove that every item ends up in the sample with probability k/n, and extend it to weighted and sharded streams
tag: sketch-reservoir | Reservoir sampling
link: Wikipedia: Reservoir sampling | https://en.wikipedia.org/wiki/Reservoir_sampling#History_and_Algorithm_R | 10 min: 'History and Algorithm R' for the pseudocode and the inductive proof, then 'Optimizing running time by skipping elements' (Algorithm L) and 'Algorithm A-Res' for weighted sampling
link: Dropwizard Metrics manual: Uniform reservoirs | https://metrics.dropwizard.io/4.2.0/manual/core.html#uniform-reservoirs | 3 min: a production histogram that keeps an Algorithm R sample, and the next section on exponentially decaying reservoirs that favour recent data

> [!key]
> To keep k items chosen uniformly at random from a stream of unknown length, keep the first k. For the i-th item after that (counting from 1), pick j uniformly in 1..i; if j <= k, the item replaces reservoir slot j. Item i enters with probability k/i and every resident survives each later step with exactly the right probability, so after n items each one is in the sample with probability k/n. One pass, O(k) memory, O(1) work per item.

## Intuition

You cannot pick 100 random log lines out of N if you do not know N yet. But you can keep a promise as you go: "my reservoir is always a uniform sample of everything seen so far". When item i arrives, a uniform sample of i items would contain it with probability k/i, so admit it with exactly that probability. Admitting it evicts a uniformly chosen resident, and the arithmetic below shows the residents stay uniform too.

## How it works

### Algorithm R

1. Put items 1..k into the reservoir.
2. For item i > k: draw j uniform in 1..i. If j <= k, replace slot j with item i.

The template counts from 0: `j = randrange(i + 1)`, keep if `j < k`. Conditional on `j < k`, j is uniform over the k slots, so the same draw decides both whether and where.

### Why every item has probability k/n

By induction on the number of items seen, n. After n = k items, everything is in the reservoir: probability `k/k = 1`. Suppose after n items each has probability k/n. Item n + 1 enters with probability `k/(n+1)`. A resident is evicted only if the new item enters and picks its slot: `k/(n+1) × 1/k = 1/(n+1)`. So a resident survives with probability `n/(n+1)`, and its total probability is `k/n × n/(n+1) = k/(n+1)`. Every item, old or new, now has `k/(n+1)`.

### Faster: skipping

Most items late in a long stream are rejected. Algorithm L draws, from the right distribution, how many items to skip before the next replacement, so it needs about `O(k (1 + log(n/k)))` random numbers instead of n.

### Weighted sampling

Efraimidis and Spirakis's A-Res: give each item the key `u^(1/w)` with u uniform in (0, 1) and w its weight, and keep the k items with the largest keys in a min-heap. With k = 1, item x wins with probability `w_x / sum(w)`.

### Sharded streams

Give every item a random key and keep, per shard, the k items with the largest keys (exactly what A-Res does with weight 1). The k largest keys overall are among the per-shard top k's, so merging is "keep the top k of the union", and the result is uniform over the whole stream however it was split.

## Cost

Per item: one random number and a comparison, O(1); memory O(k). Replacements are rare: item i enters with probability k/i, so the expected number of replacements is `sum over i from k+1 to n of k/i`, about `k ln(n/k)`. For k = 100 and n = 1,000,000 that is 920.5; five runs of the template's loop gave 932, 927, 921, 923 and 889. For n = 10^9 it is only about 1,612, which is why skipping pays off.

## When to use it

Use reservoir sampling when you want a fixed-size uniform sample from data you see once: log lines or traces to inspect, request latencies for a histogram (Dropwizard Metrics' uniform reservoir is Algorithm R), examples for manual quality review from a training-data stream, a sample of rows from a table scan. It gives a fair sample at any moment, not only at the end.

Do not use it when the population is already in memory as a sequence (use `random.sample(population, k)`; since Python 3.11 the population must be a sequence, so it cannot take a generator), when recent data matters more (use a decaying reservoir, as Dropwizard's exponentially decaying reservoir does), or when you need a fixed number per group (keep one reservoir per group).

| Situation | Tool |
|---|---|
| Sequence in memory | `random.sample(seq, k)` |
| Stream, uniform | Algorithm R (or L for very long streams) |
| Stream, weighted | A-Res keys `u^(1/w)` with a size-k heap |
| Many shards | random keys per item, keep the top k of the union |
| Recent data matters | time-decayed reservoir |

## Worked trace

k = 2 over the stream A to G, with `random.Random(3)` supplying j:

```steps
item 1 `A`: the reservoir is not full, keep it
    seen   A
    sample ['A']
---
item 2 `B`: the reservoir is not full, keep it
    seen   AB
    sample ['A', 'B']
---
item 3 `C`: j = randrange(3) = 0 < 2, so `C` replaces `A` (kept with probability 2/3)
    seen   ABC
    sample ['C', 'B']
---
item 4 `D`: j = randrange(4) = 1 < 2, so `D` replaces `B` (kept with probability 2/4)
    seen   ABCD
    sample ['C', 'D']
---
item 5 `E`: j = randrange(5) = 2 >= 2, so skip `E` (kept with probability only 2/5)
    seen   ABCDE
    sample ['C', 'D']
---
item 6 `F`: j = randrange(6) = 4 >= 2, so skip `F` (kept with probability only 2/6)
    seen   ABCDEF
    sample ['C', 'D']
---
item 7 `G`: j = randrange(7) = 3 >= 2, so skip `G` (kept with probability only 2/7)
    seen   ABCDEFG
    sample ['C', 'D']
```

Each of the seven items had probability 2/7 of ending in the sample; this run kept C and D.

## Template

```python
import heapq
import random


def reservoir_sample(stream, k: int, rng=random) -> list:
    sample = []
    for i, x in enumerate(stream):
        if i < k:
            sample.append(x)
        else:
            j = rng.randrange(i + 1)                   # uniform over 0..i
            if j < k:
                sample[j] = x                          # x is kept with probability k / (i + 1)
    return sample


def weighted_reservoir(stream, k: int, rng=random) -> list:
    """Efraimidis-Spirakis A-Res: keep the k largest keys u ** (1 / w)."""
    heap = []                                          # min-heap of (key, item)
    for item, w in stream:
        key = rng.random() ** (1 / w)
        if len(heap) < k:
            heapq.heappush(heap, (key, item))
        elif key > heap[0][0]:
            heapq.heapreplace(heap, (key, item))
    return [item for _, item in heap]
```

## Pitfalls

- **Off by one in the draw.** `j = randrange(i)` instead of `randrange(i + 1)` admits item i with probability k/i instead of k/(i+1). Over 100,000 runs with n = 10 and k = 3, the first three items ended in the sample 22% of the time and the rest 33%, instead of 30% each.
- **Keeping the first k.** A "sample" of the first lines of a log is a sample of one minute of traffic.
- **Concatenating shard samples.** Taking 100 random items from three shard reservoirs of 100 each over-represents small shards; use random keys and keep the global top k.
- **Weights of zero.** `1 / w` fails; give such items no key at all, since they should never be chosen.
- **Shared random generators across threads.** Use one generator per worker with distinct seeds, or results stop being reproducible.

## Check yourself

Q: In the trace, what was the probability that `A` would be in the final sample, and that `G` would be?
A: Both 2/7. `A` entered with certainty and then had to survive the arrivals of C to G: `2/3 × 3/4 × 4/5 × 5/6 × 6/7 = 2/7`. `G` entered with probability 2/7 and nothing came after it.

Q: Three shards processed 1 million, 10 million and 100 million events and each kept a reservoir of 100. Can you get a uniform sample of 100 over all 111 million events from these 300 items?
A: Not by choosing 100 of the 300 uniformly: each shard would contribute about a third, while the biggest shard holds 90% of the events. If each shard also stored a random key per item (keeping its 100 largest keys), take the 100 largest keys of the union. Otherwise, draw how many to take from each shard in proportion to its size (a multivariate hypergeometric draw), then take that many from its reservoir.

Q: With k = 1 and weights a = 1, b = 2, c = 7, how often should `weighted_reservoir` return each item, and why?
A: About 10%, 20% and 70% of the time: with keys `u^(1/w)`, the probability that an item has the largest key is proportional to its weight. Over 60,000 runs the template's frequencies were within one percentage point of those values.

## Lab

- Run `reservoir_sample(range(10), 3)` 60,000 times with one seeded generator and count how often each value appears. Expected: each about 30% (within one percentage point).
- Run `weighted_reservoir([("a", 1), ("b", 2), ("c", 7)], 1)` 60,000 times. Expected: about 10%, 20% and 70%.
- Count replacements for k = 100 over a stream of 1,000,000. Expected: about 920 (`k ln(n/k)` gives 921).

> [!know]
> You now know how reservoir sampling keeps a uniform sample of any stream in O(k) memory, why it is correct, and how to weight it and merge it across shards.

=== lab | Measure your sketches: error against memory for a Bloom filter and a count-min sketch | 45 min
goal: Implement a Bloom filter and a count-min sketch from this module's templates, sweep their memory, and show where measured error matches the formulas and where the formulas are only loose bounds

> [!note]
> You need the `BloomFilter`, `bloom_fp_theory` and `CountMin` templates from the cards above in a file `sk.py`. Everything else uses the standard library. The full run takes a few minutes in CPython.

## Steps

1. **Data.** Save this harness next to `sk.py` as `lab.py`. It builds 100,000 keys, 200,000 keys that were never added, and two streams of 1,000,000 page views: Zipf-distributed (a few very popular pages, like real traffic) and uniform.

```python
import math
import random
import statistics
from collections import Counter
from itertools import accumulate

from sk import BloomFilter, CountMin, bloom_fp_theory   # your own classes from the templates


def zipf_stream(n_events, n_items, s=1.1, seed=42):
    rng = random.Random(seed)
    cum = list(accumulate(1 / (i ** s) for i in range(1, n_items + 1)))
    return [f"/page/{i}".encode() for i in rng.choices(range(n_items), cum_weights=cum, k=n_events)]


# Part A: Bloom filter, measured against (1 - e^(-kn/m))^k
n = 100_000
keys = [f"user:{i}".encode() for i in range(n)]
absent = [f"other:{i}".encode() for i in range(200_000)]
for bits_per_key in (4, 6, 8, 10, 12, 16):
    m, k = bits_per_key * n, max(1, round(bits_per_key * math.log(2)))
    bf = BloomFilter(m, k)
    for x in keys:
        bf.add(x)
    measured = sum(x in bf for x in absent) / len(absent)
    print(f"A {bits_per_key:2} bits/key k={k:2}: theory {bloom_fp_theory(m, n, k):.4%} measured {measured:.4%}")

# Part B: count-min, measured overcount against N/w and the eps*N bound
N = 1_000_000
for name, stream in (("zipf", zipf_stream(N, 100_000)),
                     ("uniform", [f"/page/{i}".encode() for i in random.Random(7).choices(range(100_000), k=N)])):
    true = Counter(stream)
    for w in (272, 1000, 2719):
        for d in (1, 3, 5):
            cm = CountMin(math.e / w, math.exp(-d))
            for x in stream:
                cm.add(x)
            err = [cm.estimate(x) - c for x, c in true.items()]
            bound = math.e / w * N
            print(f"B {name:7} w={cm.w:5} d={cm.d}: mean overcount {statistics.mean(err):7.1f}  N/w {N / cm.w:7.1f}  "
                  f"max {max(err):6}  share above eps*N {sum(e > bound for e in err) / len(err):.4%}  delta {math.exp(-d):.4f}")
```

2. **Predict first.** Before running, write down for each Bloom row the theoretical rate, and for each count-min row two predictions: the mean overcount with d = 1 (the derivation says about N/w) and the largest share of items above εN that the guarantee allows (δ = e^-d).
3. **Run Part A** and compare measured with theory. Then measure memory: build `set(keys)` under `tracemalloc` and compare with `len(bf.bits)` for the 10-bits-per-key filter.
4. **Run Part B.** For each width, compare d = 1, 3 and 5 on both streams.
5. **Explain three things in writing:** why the d = 1 mean overcount equals N/w, why the d = 1 maximum on the Zipf stream is about 135,000, and why extra rows help a lot on the Zipf stream and little on the uniform one.
6. **Stretch.** Add conservative update to Part B, and repeat Part A with a broken hash (for example `h2 = 0`, so all k probes coincide) to see measured error leave the theoretical curve.

## What you should see

Part A, the Bloom filter tracks the formula to within a few percent of itself:

| Bits per key | k | Theory | Measured |
|---|---|---|---|
| 4 | 3 | 14.69% | 14.77% |
| 6 | 4 | 5.61% | 5.62% |
| 8 | 6 | 2.16% | 2.17% |
| 10 | 7 | 0.82% | 0.83% |
| 12 | 8 | 0.31% | 0.30% |
| 16 | 11 | 0.046% | 0.046% |

The set of 100,000 keys with its key objects takes about 9.3 MB under `tracemalloc`; the 10-bits-per-key filter is 125,000 bytes.

Part B with the templates (your numbers will differ slightly if your hashes differ):

| Stream | w | d | Mean overcount | N/w | Max overcount | Share above εN | δ allowed |
|---|---|---|---|---|---|---|---|
| Zipf | 1000 | 1 | 988.5 | 1000.0 | 135,579 | 4.35% | 36.8% |
| Zipf | 1000 | 3 | 273.2 | 1000.0 | 6,090 | 0.0062% | 5.0% |
| Zipf | 1000 | 5 | 228.7 | 1000.0 | 1,449 | 0% | 0.67% |
| Zipf | 2719 | 1 | 360.6 | 367.8 | 134,822 | 3.38% | 36.8% |
| Zipf | 2719 | 5 | 60.9 | 367.8 | 374 | 0% | 0.67% |
| Uniform | 1000 | 1 | 999.4 | 1000.0 | 1,340 | 0% | 36.8% |
| Uniform | 1000 | 5 | 879.5 | 1000.0 | 1,170 | 0% | 0.67% |
| Uniform | 2719 | 5 | 295.9 | 367.8 | 453 | 0% | 0.67% |

What it means:

- **With one row, the mean overcount is N/w** on both streams (988.5 and 999.4 against 1,000), exactly the expected excess from step 1 of the derivation.
- **The guarantee is loose.** The share of items above εN is 3% to 4% with d = 1, far below the 1/e = 37% that Markov's inequality allows, and essentially zero with d >= 3. Markov's bound holds for any distribution, so it is pessimistic for a particular one.
- **The worst case with one row is a collision with the top page.** Some page shares its single column with `/page/0` (134,758 views), so it reads about 135,000. With three or more rows, the minimum avoids that row.
- **Extra rows help skewed streams most.** On the Zipf stream, d = 5 cuts the mean overcount from 360.6 to 60.9 at w = 2719, because some row usually has only light neighbours. On the uniform stream every counter holds about N/w, so the minimum of five is only a little smaller (295.9).
