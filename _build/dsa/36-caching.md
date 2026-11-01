---
key: caching
name: Caches and rate limiters in production
stage: prod
summary: How real caches decide what to keep (CLOCK, sampled LRU, W-TinyLFU, S3-FIFO, SIEVE), how to measure them with trace replay, and how production rate limiters count requests.
why: The design module gives you an LRU cache with O(1) operations; production caches go further, because exact LRU wastes space on scans and one-hit wonders and serialises every hit on a shared list. Redis samples instead of keeping a list, Caffeine adds a frequency sketch in front of its queues, and two recent FIFO-based designs (S3-FIFO and SIEVE) beat LRU's miss ratio while doing less work per hit. The same counting ideas protect services from overload: token buckets, GCRA and sliding windows decide which requests to serve at Stripe, Envoy, NGINX and Cloudflare. Knowing these structures lets you choose an eviction policy with evidence (a replayed trace and a miss-ratio curve), size a cache, and build a rate limiter that is correct under bursts and across many servers.
outcomes:
- Explain why exact LRU loses on scans and one-hit wonders, and implement CLOCK and Redis-style sampled LRU
- Implement W-TinyLFU admission with a small count-min sketch and explain why frequency needs ageing
- Implement S3-FIFO and SIEVE from their papers and trace them by hand on a small input
- Replay a trace through several policies, compute an LRU miss-ratio curve in one pass and compare against Belady's optimum
- Build token-bucket, GCRA and sliding-window rate limiters and say which to use in a single process and across a fleet
cues:
- A cache's hit ratio collapses after a nightly batch job, a crawler or a full-table scan runs
- Profiling shows lock contention or allocation on the cache's hit path, not on misses
- Someone proposes "just make the cache bigger" without a miss-ratio curve to justify the size
- An API needs "N requests per second per client, with short bursts allowed", or a downstream service must be protected from overload
- Several stateless servers must enforce one shared limit
traps:
- Judging a policy on a synthetic trace only, or on a trace without warm-up, then shipping it for a workload with scans and bursts
- Treating CLOCK, sampled LRU and SIEVE as exact LRU: their victims differ, and tests that assert LRU order will fail
- Counting with unaged frequency, so yesterday's hot keys block today's
- Using a fixed-window counter and letting clients send twice the limit across a window boundary
- Making the rate limiter a hard dependency: if its store is down, requests should usually fail open
systems:
- Redis evicts with sampled LRU or LFU: it checks maxmemory-samples keys (default 5), keeps a 16-entry pool of good candidates, and stores a 24-bit clock or log counter per key instead of list pointers
- Caffeine (Java) uses W-TinyLFU: a 1% LRU admission window, a segmented-LRU main space, and a 4-bit count-min sketch that halves its counters periodically; hill climbing retunes the window size
- S3-FIFO (SOSP 2023) and SIEVE (NSDI 2024) replace LRU's list with FIFO queues; the SIEVE authors list adopters including ClickHouse, BIND 9 and DragonflyDB
- Stripe rate-limits with token buckets in Redis; Envoy's local limiter is a token bucket, NGINX's limit_req is a leaky bucket, and Cloudflare estimates sliding windows from two counters
further:
- Article · 12 min | Juncheng Yang: Why FIFO is (almost) all you need for cache eviction | https://blog.jasony.me/posts/2026-05-20-fifo-is-all-you-need.html
- Docs · 10 min | Caffeine wiki: Design (eviction policy, adaptivity, HashDoS protection) | https://github.com/ben-manes/caffeine/wiki/Design#eviction-policy
- Paper · 40 min | Zhang et al.: SIEVE is simpler than LRU (NSDI 2024), sections 3 and 5 | https://www.usenix.org/system/files/nsdi24-zhang-yazhuo.pdf
- Article · 15 min | Stripe: Scaling your API with rate limiters | https://stripe.com/blog/rate-limiters
---

=== primer | Why does plain LRU fail, and what do CLOCK and Redis's sampled LRU approximate? | 18 min
goal: Explain where exact LRU loses in production and implement CLOCK and Redis-style sampled LRU, the two cheap approximations most real systems use
tag: caching-clock | CLOCK and sampled LRU
link: Redis docs: Key eviction | https://redis.io/docs/latest/develop/reference/eviction/#apx-lru | 5 min: 'Approximated LRU algorithm' compares sampled eviction with true LRU and explains maxmemory-samples; 'LFU eviction' previews the next card

> [!key]
> Exact LRU has two production problems. Its ranking is wrong for scans and one-hit wonders, because every new key starts at the safest position, and its bookkeeping is expensive, because every hit rewrites a shared linked list. **CLOCK** keeps one reference bit per entry and a hand that sweeps a ring; **Redis's sampled LRU** keeps a timestamp per key and evicts the stalest of a few random samples. Both make hits almost free and land close to LRU's miss ratio, but neither fixes the scan problem; the next three cards do.

## Intuition

Picture a shelf of books where you put every book you touch back at the left end; when the shelf is full, the book at the right end goes to storage. That is LRU, and it works while people reread a few favourites. Now a student walks along and touches every book in the library once for an inventory. Each of those books lands at the left end, and after one shelf's worth of them, every favourite has been pushed off the right end. Nobody wanted the inventory books again.

There is a second, quieter cost: every single touch reshuffles the shelf. With one librarian that is fine. With twenty librarians working the same shelf, they queue for it.

CLOCK stops reshuffling. When you use a book, you stick a note on it and leave it where it is. When space is needed, a pointer walks along the shelf: a book with a note loses the note and is skipped; the first book without a note goes. Redis does something even lazier: it writes a "last used" date inside each book, glances at five random books, and removes the one with the oldest date.

## How it works

### What exact LRU costs

The design module builds LRU from a hash map plus a doubly linked list (Python: `OrderedDict` with `move_to_end` and `popitem(last=False)`). CPython's `functools.lru_cache` does exactly this with a circular doubly linked list and a root sentinel. That costs two pointers per entry, and a hit unlinks a node and relinks it at the head. In a multi-threaded cache those pointer writes need a lock, so the hit path, which should be the cheap path, becomes the contended one. memcached 1.5 split its LRU into hot, warm and cold segments and bumps an item at most once every 60 seconds partly for this reason.

### Where LRU's ranking goes wrong

- **Scans.** A batch job, a crawler or `SELECT *` touches many keys once. Each lands at the head, and after `capacity` of them every hot key has been evicted. In the experiment below (80 hot keys, a cache of 100, and a 500-key scan every 2,000 requests), LRU misses 4.0% of the hot-key requests; a scan-resistant policy misses 0.1%.
- **One-hit wonders.** Many keys are requested once while they are cached. LRU still makes each one travel the whole list before it can leave, occupying space the whole way.

### CLOCK (also called second chance or FIFO-reinsertion)

Keep the keys in a ring of `capacity` slots, one reference bit per slot, and a hand.

- **Hit:** set the slot's bit. Nothing moves.
- **Miss, cache not full:** put the key in the next free slot with its bit clear.
- **Miss, cache full:** look at the slot under the hand. If its bit is set, clear it and advance (the key gets a second chance). Repeat until the hand reaches a clear bit; evict that key, put the new key in its slot with a clear bit, and advance the hand past it.

The SIEVE paper points out that CLOCK and FIFO-reinsertion are the same algorithm: a FIFO queue where a tail object with its bit set is moved back to the head instead of evicted. The ring is just a cheaper way to do the move.

### Redis's sampled LRU

Redis keeps no list at all. Each key's header holds a 24-bit access clock. When memory passes `maxmemory` under `allkeys-lru`, Redis samples `maxmemory-samples` keys (default 5) and evicts the one idle longest, repeating until memory is back under the limit. Since Redis 3.0 it also keeps a pool of 16 good candidates between rounds, so a stale key seen in one sample is not forgotten. The docs report that 10 samples come very close to true LRU, and say plainly why Redis does not use the exact version: it costs more memory.

## Cost

Count work per request on a cache of `C` entries.

- **Exact LRU:** a hit is O(1) but writes six pointers; memory is the dict plus two pointers per entry.
- **CLOCK, hit:** one dict lookup and one bit write, O(1).
- **CLOCK, eviction:** each hand step either clears a bit or evicts. Bits are set only by hits, so over any run of `R` requests the clears number at most the hits and the evictions at most the misses: at most `R` hand steps in total, **amortised O(1) per request**. One unlucky eviction can take `C` steps (every bit set: the hand clears them all, comes round and evicts the slot it started at).
- **Sampled LRU:** a hit writes one timestamp; an eviction costs O(k) for `k` samples. The victim is the oldest of `k` random keys. If you rank resident keys by age, the minimum of `k` random ranks lands, on average, at about `n / (k + 1)` from the oldest end, so `k = 5` evicts from roughly the oldest sixth and `k = 1` is plain random eviction.

Measured on a Zipf(1.0) trace of 200,000 requests over 10,000 keys with a 100-entry cache (generator in the Lab):

| Policy | Miss ratio |
|---|---|
| Exact LRU | 0.610 |
| CLOCK | 0.596 |
| Sampled, k = 1 (random) | 0.658 |
| Sampled, k = 5 | 0.614 |
| Sampled, k = 10 | 0.611 |
| S3-FIFO, for comparison | 0.495 |

The approximations cost almost nothing in hit ratio. The last row shows the real opportunity: fixing LRU's ranking, not its bookkeeping.

## When to use it

| Policy | Hit cost | Extra memory per entry | Good for |
|---|---|---|---|
| Exact LRU | list relink, needs a lock when shared | two pointers | small, single-threaded caches; tests that need exact order |
| CLOCK | set one bit | one bit | concurrent caches, page caches, buffer pools |
| Sampled LRU | write a timestamp | a timestamp | keys scattered in a huge hash table (Redis) |

Reach for CLOCK or sampling when hits dominate and the cache is shared between threads. Do **not** expect either to survive scans or floods of one-hit wonders: they approximate LRU, including its mistakes. If your workload has scans, read the TinyLFU, S3-FIFO and SIEVE cards next.

## Worked trace

CLOCK with capacity 3 on `A B C A D A E B F`, with exact LRU's choice alongside. A `*` marks a set reference bit.

```steps
A, B, C miss and fill the empty slots; bits start clear, hand at slot 0
    slots   {{A}}  B   C        hand -> slot 0
    LRU     C B A               (most recent first)
---
A hits: CLOCK only sets A's bit; LRU moves A to the front
    slots   {{A*}} B   C        hand -> slot 0
    LRU     A C B
---
D misses with the cache full: A has its bit set, so clear it and advance; B's bit is clear, so B goes and D takes slot 1
    slots   A  {{D}}  C         hand -> slot 2
    LRU     D A C               (LRU also evicted B)
---
A hits again (bit set); E misses: the hand is at C, bit clear, so C goes
    slots   A*  D  {{E}}        hand -> slot 0
    LRU     E A D               (LRU also evicted C)
---
B misses: A* loses its bit and survives, D (clear) is evicted
    slots   A  {{B}}  E         hand -> slot 2
    LRU     B E A               (LRU also evicted D)
---
F misses: the hand is at E (clear), so E goes. LRU evicts A instead, its oldest key
    slots   A   B  {{F}}        hand -> slot 0
    LRU     F B E
```

The first four evictions agree; the last does not. CLOCK only knows "used since the hand last passed", not the full order.

## Template

```python
import random


class Clock:
    """CLOCK (second chance): a ring of slots, one reference bit each, one hand."""

    def __init__(self, capacity):
        self.cap = capacity
        self.keys = []            # slot -> key
        self.ref = []             # slot -> reference bit
        self.slot = {}            # key -> slot
        self.hand = 0

    def access(self, key):
        """Return True on a hit; on a miss, admit key, evicting if full."""
        i = self.slot.get(key)
        if i is not None:
            self.ref[i] = True    # a hit only sets a bit: no list surgery
            return True
        if len(self.keys) < self.cap:              # still filling up
            self.slot[key] = len(self.keys)
            self.keys.append(key)
            self.ref.append(False)
            return False
        while self.ref[self.hand]:                 # second chance: clear, move on
            self.ref[self.hand] = False
            self.hand = (self.hand + 1) % self.cap
        del self.slot[self.keys[self.hand]]        # first slot with bit 0 loses
        self.keys[self.hand], self.ref[self.hand] = key, False
        self.slot[key] = self.hand
        self.hand = (self.hand + 1) % self.cap
        return False


class SampledLRU:
    """Redis-style approximate LRU: evict the stalest of k randomly sampled keys."""

    def __init__(self, capacity, k=5, seed=0):
        self.cap, self.k = capacity, k
        self.last = {}                   # key -> time of last access
        self.keys, self.pos = [], {}     # dense list, so sampling costs O(k)
        self.now = 0
        self.rng = random.Random(seed)

    def access(self, key):
        self.now += 1
        if key in self.last:
            self.last[key] = self.now    # a hit writes one timestamp
            return True
        if len(self.keys) >= self.cap:
            sample = self.rng.sample(self.keys, min(self.k, len(self.keys)))
            self._remove(min(sample, key=self.last.__getitem__))
        self.last[key] = self.now
        self.pos[key] = len(self.keys)
        self.keys.append(key)
        return False

    def _remove(self, key):              # swap with the last slot, then pop: O(1)
        i, tail = self.pos.pop(key), self.keys.pop()
        if tail != key:
            self.keys[i], self.pos[tail] = tail, i
        del self.last[key]
```

## Pitfalls

- **Testing an approximation against exact LRU order.** CLOCK and sampled LRU pick different victims by design (the last step of the trace). Test them against their own reference model (CLOCK against a FIFO-reinsertion queue) or with `k >= capacity`, where sampled LRU must equal LRU exactly.
- **Forgetting to advance the hand past the new key.** Then the newest key is the next candidate, and CLOCK degrades into "evict whatever just arrived".
- **Sampling a dict.** `random.sample(some_dict, k)` is a `TypeError` since Python 3.11, and `list(d)` on every eviction is O(n). Keep a dense list with swap-and-pop removal, as the template does.
- **Redis policy mismatch.** Redis evicts by memory, not by key count, and the `volatile-*` policies only consider keys with a TTL; the docs note they behave like `noeviction` when no key has one, so writes start failing instead of evicting.
- **Expecting scan resistance.** Neither approximation protects the hot set from a scan; measure with a trace that contains one.

## Check yourself

Q: In the worked trace, why did CLOCK evict E at F while LRU evicted A?
A: A had been hit at step 6, but the hand cleared A's bit when B arrived, so by F the hand only sees "A and E both have clear bits" and evicts whichever it reaches first (E). LRU remembers the full order: A's last use (step 6) is older than E's (step 7) and B's, so A goes.

Q: Prove that CLOCK's hand moves at most R times over R requests, so eviction is amortised O(1).
A: Every hand step either clears a set bit or ends in an eviction. A bit can only be set by a hit, and a cleared bit must be set again by another hit before it can be cleared again, so the number of clearing steps is at most the number of hits. Each miss evicts at most once, so eviction steps are at most the number of misses. Hits plus misses equal R.

Q: Redis is configured with `maxmemory-samples 5`. A colleague suggests 50 "to be safe". What changes?
A: The victim gets closer to the true LRU key (the oldest of 50 random keys instead of 5), but every eviction now reads 50 keys' metadata, so eviction CPU grows tenfold. The docs suggest 10 is already very close to true LRU; the miss-ratio gain past that is usually negligible, and the scan problem is untouched.

## Lab

- Replay the worked trace `A B C A D A E B F` through `Clock(3)` and an `OrderedDict` LRU of size 3. Expected: both get 2 hits; the only differing victim is at `F`.
- Generate `trace = random.Random(1).choices(range(10_000), weights=[1 / (r + 1) for r in range(10_000)], k=200_000)` and replay it with capacity 100. Expected miss ratios: LRU 0.610, `Clock` 0.596, `SampledLRU(100, k=5)` 0.614 (seed 0).
- Property test: for 1,000 random traces over 10 keys, `SampledLRU(c, k=c)` must give exactly the same hit sequence as LRU of size `c`. Expected: no failures.

> [!know]
> You now know why exact LRU is both expensive and wrongly ranked in production, and how CLOCK and sampled LRU keep its behaviour while making hits nearly free.

=== primer | How do LFU with ageing and TinyLFU admission keep the popular keys cached? | 18 min
goal: Explain why raw frequency must age, separate admission from eviction, and implement W-TinyLFU with a four-row count-min sketch
tag: caching-tinylfu | TinyLFU admission (W-TinyLFU)
link: Caffeine wiki: Design | https://github.com/ben-manes/caffeine/wiki/Design#eviction-policy | 5 min: 'Eviction policy', 'Adaptivity' and 'HashDoS protection' describe the production version of this card's template
link: Einziger, Friedman and Manes: TinyLFU (arXiv) | https://arxiv.org/abs/1512.00727 | Optional, 25 min: section 3 'TinyLFU Architecture' (3.3 'Freshness Mechanism' is the halving reset) and the W-TinyLFU part of the Caffeine section

> [!key]
> Frequency is a better predictor than recency for skewed workloads, but raw counts never forget, so yesterday's hot keys block today's. Production policies **age** their counts: Redis decays an 8-bit logarithmic counter every minute, and TinyLFU halves every counter after a fixed number of requests. TinyLFU also changes the question: instead of choosing a victim, it decides **admission**, letting a newcomer in only if a compact **count-min sketch** says it is requested more often than the victim it would replace. Caffeine's **W-TinyLFU** puts a 1% LRU window in front so short bursts still get cached.

## Intuition

A restaurant has ten tables and a queue at the door. Seating whoever arrived most recently (LRU) means a coach party of one-time tourists can fill every table and turn away the regulars. Seating by "how many times have you eaten here" (LFU) protects the regulars, but a man who ate here daily ten years ago, and has since moved away, keeps his table forever.

The fix has two parts. First, let old visits count for less: every so often, halve everyone's tally. Second, at the door, compare the newcomer's tally with the tally of the diner who would have to leave, and only swap if the newcomer comes more often. To remember tallies for people who are not seated, keep a small notebook that may overcount a little but never undercounts.

## How it works

### LFU and why it needs ageing

The design module builds LFU with O(1) operations: counts per key, a list of keys per count, ties broken by recency. On a stable Zipf workload it beats LRU. When popularity shifts, it collapses: keys from the old hot set hold counts in the thousands and new keys arrive with a count of 1, so every newcomer is the victim. On a trace whose hot set changes halfway (cache of 200), plain LFU misses **98.0%** of the second half's requests, against 47.3% for LRU.

Two ageing schemes are common in production:

- **Redis LFU** (`allkeys-lfu`) stores, in the same 24 bits it uses for the LRU clock, an 8-bit logarithmic counter and a 16-bit "last decrement" time in minutes. A hit increments the counter with probability `1 / ((c - 5) * lfu-log-factor + 1)`, so it saturates at 255 after roughly a million hits with the default factor 10; new keys start at 5 so they are not evicted on arrival. When a key is sampled, its counter drops by one for every `lfu-decay-time` minutes (default 1) since the last decrement. Eviction is still sampled, as in the previous card.
- **TinyLFU reset**: count every request; after `W` requests (Caffeine uses 10 times the cache size), divide every counter by two. A key's count then reflects roughly its last `W` to `2W` requests, and the relative order of hot keys survives each halving.

### Admission instead of eviction

TinyLFU does not pick victims. Some eviction policy proposes a victim, and TinyLFU decides whether the incoming candidate deserves the victim's place: admit only if `freq(candidate) > freq(victim)`, otherwise drop the candidate and keep the victim. One-hit wonders and scan keys have a frequency of 1 and lose almost every duel.

To compare frequencies it must remember keys that are **not** cached. Storing an exact count per key ever seen is unbounded, so it uses a **count-min sketch** (the sketch module covers it in depth): `d` rows of `w` small counters; a key increments one counter per row, chosen by `d` hashes, and its estimate is the minimum of those counters. Collisions only add, so the estimate never undercounts (until counters cap or halve). Caffeine uses four rows of 4-bit counters (maximum 15), sized at about 8 bytes per cache entry.

### W-TinyLFU, as in Caffeine

```flow
Request: every request increments the sketch -> Window LRU: 1% of capacity, no admission test -> Duel: window victim vs probation victim, higher sketch estimate stays -> Main SLRU: probation 20% and protected 80%
```

- New keys always enter the **window**, a small LRU, so a burst of requests to a brand-new key can hit before the key has built up frequency.
- When the window overflows, its LRU key becomes the **candidate**. If the main space has room it simply moves in; otherwise it duels the LRU key of the main space's **probation** segment.
- The main space is a **segmented LRU**: a hit in probation promotes the key to **protected** (80% of the main space); when protected overflows, its LRU key is demoted back to probation.
- Caffeine starts with a 1% window and adapts its size by hill climbing on the observed hit rate. It also defends against hash flooding: an attacker who makes a victim's counters collide with popular keys could get every candidate rejected, so Caffeine admits a rejected candidate with an estimate of at least 6 with probability 1/128.

## Cost

- **Sketch add and estimate:** four hashes and four counter reads or writes, O(1).
- **Reset:** a pass over all `4w` counters, but only once per `W = 10C` adds, so `4w / 10C` extra work per request. With `w = 4C` that is 1.6 counter updates per request, amortised O(1).
- **Window and SLRU:** `OrderedDict` moves and pops, O(1) each; a request causes at most one duel, so **O(1) per request**.
- **Memory:** the cache's own entries plus `4 rows x 4C counters x 4 bits = 8 bytes per entry` for the sketch; no ghost entries are kept for evicted keys.

Measured on traces from the Lab (cache of 100 or 200):

| Trace | LRU | Plain LFU | W-TinyLFU |
|---|---|---|---|
| Hot set of 80 keys plus repeated 500-key scans | 0.232 | not run | 0.201 |
| Hot set changes halfway (second half only) | 0.473 | 0.980 | 0.385 |
| Zipf(1.0), 10,000 keys, cache 100 | 0.610 | not run | 0.496 |

## When to use it

- **Use W-TinyLFU** for general-purpose application caches with skewed popularity, scans and bursts mixed together: it is Caffeine's default for size-bounded caches.
- **Use Redis's LFU mode** when you run Redis as a cache and the hot set is stable for minutes to hours; switch back to LRU if keys are popular in short bursts.
- **Do not use unaged LFU** for anything long-running.
- **Prefer S3-FIFO or SIEVE** (next cards) when hit-path simplicity and multi-core throughput matter more than the last percent of hit ratio, or when you cannot afford a hash per request for the sketch.

## Worked trace

`WTinyLFU(4)`: window 1, main 3, protected at most 2. Numbers after a key are its sketch estimates (exact here: no collisions).

```steps
a a b b c: each new key enters the window; the window overflows, and while the main space has room the candidate simply moves into probation
    window [c1]   probation [a2 b2]   protected []
---
a b: hits in probation promote a and b to protected
    window [c1]   probation []   protected [{{a3 b3}}]
---
x: the window overflows, main has room (2 of 3), so c moves to probation
    window [x1]   probation [{{c1}}]   protected [a3 b3]
---
y: main is full, so x duels probation's LRU key c: 1 > 1 is false, x is dropped
    window [y1]   probation [{{c1}}]   protected [a3 b3]
---
z then d: y and z lose their duels the same way; the scan never touches a or b
    window [d1]   probation [c1]   protected [a3 b3]
---
d d: two hits in the window raise d's estimate to 3
    window [{{d3}}]   probation [c1]   protected [a3 b3]
---
e: candidate d (3) duels c (1) and wins: c is evicted, d joins probation
    window [e1]   probation [{{d3}}]   protected [a3 b3]
```

## Template

```python
import hashlib
from collections import OrderedDict


class CountMin4:
    """Count-min sketch: 4 rows of counters capped at 15, halved every `sample` adds."""

    def __init__(self, width, sample):
        self.w, self.sample, self.n = width, sample, 0
        self.rows = [[0] * width for _ in range(4)]

    def _cells(self, key):                         # 4 independent 32-bit slices
        d = hashlib.blake2b(repr(key).encode(), digest_size=16).digest()
        return [(r, int.from_bytes(d[4 * r:4 * r + 4], "little") % self.w) for r in range(4)]

    def add(self, key):
        for r, i in self._cells(key):
            if self.rows[r][i] < 15:
                self.rows[r][i] += 1
        self.n += 1
        if self.n == self.sample:                  # ageing: halve every counter
            self.rows = [[c >> 1 for c in row] for row in self.rows]
            self.n //= 2

    def estimate(self, key):
        return min(self.rows[r][i] for r, i in self._cells(key))


class WTinyLFU:
    """W-TinyLFU with a fixed 1% window (Caffeine adapts it by hill climbing)."""

    def __init__(self, capacity):
        self.win_cap = max(1, capacity // 100)
        self.main_cap = capacity - self.win_cap
        self.prot_cap = int(self.main_cap * 0.8)       # SLRU: 80% protected
        self.window = OrderedDict()                     # all three: LRU order,
        self.probation = OrderedDict()                  # first key = least recent
        self.protected = OrderedDict()
        self.sketch = CountMin4(width=4 * capacity, sample=10 * capacity)

    def access(self, key):
        self.sketch.add(key)                            # count every request
        for seg in (self.window, self.protected):
            if key in seg:
                seg.move_to_end(key)
                return True
        if key in self.probation:                       # second hit: protect it
            del self.probation[key]
            self.protected[key] = None
            if len(self.protected) > self.prot_cap:     # demote protected's LRU
                old, _ = self.protected.popitem(last=False)
                self.probation[old] = None
            return True
        self.window[key] = None                         # miss: always enter window
        if len(self.window) > self.win_cap:
            cand, _ = self.window.popitem(last=False)
            if len(self.probation) + len(self.protected) < self.main_cap:
                self.probation[cand] = None
            elif self.probation:                        # duel: candidate vs victim
                victim = next(iter(self.probation))
                if self.sketch.estimate(cand) > self.sketch.estimate(victim):
                    del self.probation[victim]
                    self.probation[cand] = None
        return False
```

## Pitfalls

- **`>=` instead of `>` in the duel.** Ties then favour the newcomer, so every cold key with a count of 1 replaces a cold victim with a count of 1, and the cache churns on scans exactly like LRU.
- **No ageing.** With 4-bit counters, every hot key eventually saturates at 15 and frequency stops discriminating; without halving, a shift in popularity is never noticed.
- **A sketch that is too small.** Collisions inflate estimates, so one-hit wonders look popular and win duels. Size it from the cache capacity (the template uses `4 x capacity` counters per row), not from a constant.
- **Python's `hash()` for the sketch.** String hashes are salted per process, so experiments are not reproducible and an attacker who can choose keys may find collisions. The template uses a fixed BLAKE2 hash; production code uses a fast seeded hash and jitter, as Caffeine does.
- **No window.** Plain TinyLFU rejects every brand-new key at first, so short bursts (a new video, a fresh news story) miss repeatedly. The TinyLFU paper reports exactly this on storage traces with "sparse bursts", which is why W-TinyLFU exists.

## Check yourself

Q: In the worked trace, x, y and z were each requested once and rejected. Would a scan of 1,000 new keys ever evict a or b?
A: No. Each scan key enters the window, then duels probation's LRU key with an estimate of 1. The victim (c, then later d) has an estimate of at least 1, and ties keep the victim, so the scan keys are dropped one by one. Protected keys are never the victim; they only leave protected when another key is promoted past them.

Q: Why halve the counters rather than reset them to zero?
A: Halving keeps the ranking: a key requested 12 times before the reset still beats a key requested twice, so the cache does not suddenly admit one-hit wonders. Old counts fade geometrically (a burst of requests is worth half after one sample period, a quarter after two), so a new hot key overtakes an old one within a period or two. Resetting to zero would throw away all history at once.

Q: A news site's cache is dominated by articles that get thousands of requests in their first hour and then almost none. Which parts of W-TinyLFU help, and what would plain TinyLFU (no window) do?
A: The window lets a new article be cached on its first request and serve the first part of its burst; as the burst continues, the article's estimate grows past the probation victim's, so it wins the duel into main. The halving reset later lets it fade. Plain TinyLFU would reject the new article while its estimate was below the victim's, missing the start of every burst.

## Lab

- Replay `a a b b c a b x y z d d d e` through `WTinyLFU(4)`. Expected: 6 hits, and a final state of window `[e]`, probation `[d]`, protected `[a, b]`.
- Scan trace: with `rng = random.Random(2)`, repeat 40 times "2,000 requests drawn with `rng.randrange(80)`, then 500 brand-new keys requested once each". With capacity 100, expected miss ratios: LRU 0.232, `WTinyLFU` 0.201 (Belady's optimum is also 0.201: the scan keys are compulsory misses). On hot-key requests alone, LRU misses 4.0% and `WTinyLFU` 0.1%.
- Phase change: warm a cache of 200 with `zipf(100_000 requests, 5,000 keys, alpha 1.0, seed 3)`, then measure the miss ratio on a second trace with seed 4 whose keys are shifted by 5,000 (use the Zipf generator from the module lab). Expected: LRU 0.473, plain LFU with exact counts and LRU tie-break 0.980, `WTinyLFU` 0.385.

> [!know]
> You now know how ageing keeps frequency honest, how TinyLFU turns frequency into an admission test, and how W-TinyLFU's window and segmented LRU handle bursts and scans.

=== primer | How does S3-FIFO beat LRU with three FIFO queues? | 17 min
goal: Implement S3-FIFO as specified in the SOSP 2023 paper, trace it by hand, and explain quick demotion, lazy promotion and the ghost queue
tag: caching-s3fifo | S3-FIFO (small, main and ghost queues)
link: Juncheng Yang: Why FIFO is (almost) all you need | https://blog.jasony.me/posts/2026-05-20-fifo-is-all-you-need.html#s3-fifo-filter-first-protect-later | 4 min: the first author's own summary of the three queues, with a diagram; the section before it explains quick demotion and lazy promotion
link: Yang et al.: FIFO queues are all you need for cache eviction (SOSP 2023) | https://jasony.me/publication/sosp23-s3fifo.pdf | Optional, 20 min: section 3 (one-hit wonders and quick demotion), then section 4.1 and Algorithm 1, the exact rules this card implements

> [!key]
> S3-FIFO keeps three FIFO queues: a **small** queue S with 10% of the space, a **main** queue M with 90%, and a **ghost** queue G that remembers only the keys of objects recently dropped from S (as many keys as M holds). A hit never moves anything; it bumps a 2-bit counter capped at 3. New keys enter S; at S's tail a key that was hit more than once moves to M, any other key is dropped and its key goes into G, and a miss on a key found in G goes straight to M. M evicts like CLOCK, reinserting a tail key with a nonzero counter after decrementing it.

## Intuition

A members' club has a small entrance hall and a large main lounge. Everyone new waits in the hall, which empties in arrival order. Most visitors look around once and leave, and they never get near the lounge. A visitor who asks for service a couple of times while in the hall is shown into the lounge. The doorman also keeps a list of names of people who recently left the hall unserved: if one of them comes back soon, they skip the hall and go straight to the lounge. In the lounge, people leave in arrival order too, except that anyone who has been served recently gets to stay for another round.

The point of the hall is speed. A one-time visitor costs the club one hall-sized stretch of time, not a full trip through the lounge, so the lounge stays full of regulars.

## How it works

### Why a small queue: most objects are one-hit wonders while cached

The paper measured 6,594 production traces. Over each full trace, the median share of objects requested only once is 26%. But a cache never sees the full trace before it evicts: it sees a short stretch. In random sequences containing 10% of a trace's unique objects, the median share of one-hit wonders jumps to **72%**. So most objects a cache admits will never be requested again before eviction, and the best thing to do with a new object is to evict it quickly unless it proves itself (**quick demotion**). Meanwhile, objects that have proved themselves should not be shuffled on every hit (**lazy promotion**): decide at eviction time.

### The rules (Algorithm 1 of the paper)

- **Hit** (key in S or M): `freq = min(freq + 1, 3)`. Nothing moves.
- **Miss:** while the cache is full, evict. Then insert the key at the head of **M** if it is in G (removing it from G), otherwise at the head of **S**, with `freq = 0`.
- **Evict:** if S holds at least 10% of the capacity, evict from S; otherwise evict from M.
- **Evict from S:** take S's tail `t`. If `t.freq > 1`, move it to M's head (its counter is cleared, and if M is now over its share, evict from M) and look at the next tail. Otherwise drop `t`'s data, put its key in G (G forgets its oldest key when it holds more than M's share), and stop.
- **Evict from M:** take M's tail `t`. If `t.freq > 0`, reinsert it at M's head with `freq - 1` and look at the next tail; otherwise evict `t` and stop.

While the cache is still filling, nothing is evicted, so S simply holds everything. The 10% is a threshold, not a hard cap: the cache evicts from S whenever S holds at least 10%, so S shrinks to its 10% share only as M fills with promoted keys and ghost hits. The paper chose 10% for S after experiments on 10 traces and found it generalised well. Note the test is `freq > 1`, two hits while in S, in the pseudo-code and in the authors' libCacheSim (`move-to-main-threshold=2`).

### Implementation notes from the paper

The queues can be linked lists (easy to retrofit into an LRU cache) or ring buffers (no per-object pointers, sequential memory, friendly to flash). The ghost queue need not store keys: the paper stores a fingerprint and an insertion time per ghost entry in a hash table. Because hits only set a counter and evictions touch the queue tails, S3-FIFO needs no lock on the hit path; the paper's Cachelib prototype reached **6x** the throughput of an optimised LRU at 16 threads, and across 6,594 traces it had the lowest mean miss ratio on 10 of 14 datasets.

## Cost

- **Hit:** one dict lookup and at most one counter write. A key already at 3 needs no write at all, which is what makes the hit path scale.
- **Miss:** one eviction call, which may loop. Each loop step in S either ends the eviction or moves a key to M, and a key is moved from S to M at most once per insertion. Each loop step in M either ends it or decrements a counter, and counters only grow through hits (by at most 3 per key between decrements). So the total loop steps over a run are at most `misses + hits`, **amortised O(1) per request**.
- **Memory:** per resident object, 2 bits plus queue links (or a ring-buffer slot); per ghost entry, a key or fingerprint. G holds up to 90% as many entries as the cache, but entries are tiny compared with cached values.

## When to use it

| Situation | S3-FIFO? |
|---|---|
| Web, CDN and key-value caches with skewed popularity and many one-hit wonders | Yes: this is the workload it was designed and evaluated on |
| Multi-threaded caches where LRU's hit-path lock is a bottleneck | Yes: hits only touch a counter |
| Flash caches | Yes: FIFO writes are sequential |
| Workloads where most objects are requested exactly twice, with the second request arriving after the object would have left S | No: the paper names this as its adversarial pattern (it also hurts TinyLFU, 2Q and others that partition the cache) |
| You need exact LRU order (tests, expiry semantics) | No |

Against the previous card: W-TinyLFU uses a frequency sketch and a hash per request; S3-FIFO uses a tiny counter and a ghost queue, and is simpler to make lock-free. Their miss ratios are close on the traces in this module.

## Worked trace

`S3FIFO(5)`: S gets `max(1, int(0.5)) = 1` slot, M gets 4, G remembers up to 4 keys. Queues are shown head (newest) first; the digit after a key is its counter.

```steps
a b c d e: misses while the cache fills; nothing is evicted, so S holds everything
    S [e0 d0 c0 b0 a0]   M []   G []
---
a a: two hits only bump a's counter
    S [e0 d0 c0 b0 {{a2}}]   M []   G []
---
f: full, and S holds at least 1 slot, so evict from S. Tail a has 2 > 1: it moves to M with its counter cleared. Next tail b has 0: dropped, key kept in G
    S [{{f0}} e0 d0 c0]   M [{{a0}}]   G [{{b}}]
---
b: a miss, but b is in G. First evict from S (c goes to G), then b goes straight to M
    S [f0 e0 d0]   M [{{b0}} a0]   G [c]
---
a g c h d: a hits in M; g and h enter S; c and d were in G when they returned, so they skip S
    S [h0]   M [{{d0 c0}} b0 a1]   G [g f e]
---
i i i: i misses into S, then two hits make its counter 2
    S [{{i2}}]   M [d0 c0 b0 a1]   G [h g f e]
---
j: evict from S: i (2 > 1) moves to M, so M is over its 4 slots and evicts: tail a has 1, so it is reinserted with 0; then b has 0 and is evicted. S is now empty, so j enters S
    S [{{j0}}]   M [{{a0 i0}} d0 c0]   G [h g f e]
```

Five hits in 18 requests. The last step shows both halves of the design: i earned its place in M by being hit twice in S, and a survived one more round in M because it was hit while there.

## Template

```python
from collections import OrderedDict, deque


class S3FIFO:
    """S3-FIFO (Yang et al., SOSP 2023), counting objects instead of bytes."""

    def __init__(self, capacity, small_ratio=0.1):
        self.cap = capacity
        self.s_cap = max(1, int(capacity * small_ratio))   # S: 10% of the space
        self.m_cap = capacity - self.s_cap                 # M: the other 90%
        self.S, self.M = deque(), deque()   # left end = tail (oldest)
        self.G = OrderedDict()              # ghost: keys only, FIFO order
        self.freq = {}                      # resident key -> 0..3

    def access(self, key):
        if key in self.freq:                         # hit: bump a 2-bit counter
            self.freq[key] = min(self.freq[key] + 1, 3)
            return True
        while len(self.S) + len(self.M) >= self.cap:
            self._evict()
        if key in self.G:                            # came back soon: skip S
            del self.G[key]
            self.M.append(key)
        else:
            self.S.append(key)
        self.freq[key] = 0
        return False

    def _evict(self):
        if len(self.S) >= self.s_cap:
            self._evict_s()
        else:
            self._evict_m()

    def _evict_s(self):
        while self.S:
            t = self.S.popleft()
            if self.freq[t] > 1:                     # reused while in S: promote
                self.freq[t] = 0
                self.M.append(t)
                if len(self.M) > self.m_cap:
                    self._evict_m()
            else:                                    # one-hit wonder: drop data,
                del self.freq[t]                     # remember the key in G
                self.G[t] = None
                if len(self.G) > self.m_cap:
                    self.G.popitem(last=False)
                return

    def _evict_m(self):
        while self.M:
            t = self.M.popleft()
            if self.freq[t] > 0:                     # reinsert, one count poorer
                self.freq[t] -= 1
                self.M.append(t)
            else:
                del self.freq[t]
                return
```

## Pitfalls

- **Promoting on one hit.** The paper's rule is `freq > 1` (two hits while in S). Promoting after a single hit is a tempting simplification, but it is a different, more permissive policy; name it as such if you change the threshold.
- **Checking the ghost before evicting.** In the paper, the cache evicts first and then checks G. The eviction can push the arriving key's own ghost entry out of G (it happens in tiny caches), so the order matters if you compare against a reference.
- **Capping S during warm-up.** S is not a hard-capped queue; it only shrinks through evictions. Routing new keys into M while the cache fills changes early behaviour. The authors' simulator, libCacheSim, does this and also chooses between S and M slightly differently; its miss ratios differed from this template's by at most 0.003 on the Zipf traces we tested.
- **Ghosts holding data.** G must store keys (or fingerprints) only. If it keeps values, the cache silently uses almost twice its memory budget.
- **Byte-sized objects.** The template counts objects. Real caches with variable sizes size S, M and G in bytes and may evict several objects to fit one.

## Check yourself

Q: In the worked trace, b was hit once while in S (before f arrived) yet was dropped to G. Was that a mistake, and what happened next?
A: It is the rule: one hit is not enough to enter M (`freq > 1` is needed). The ghost queue repairs the cost: when b was requested again shortly after, it was found in G and inserted straight into M, skipping S. A key that keeps coming back is lost from the cache at most once.

Q: Why does S3-FIFO need no lock on a hit, while LRU does?
A: An LRU hit unlinks a node and relinks it at the head of a shared list, which must not interleave with other threads doing the same. An S3-FIFO hit only increments a small counter on the object itself (an atomic increment, and none at all once it is 3). Only evictions and insertions touch the queues, and they happen at the queue ends.

Q: A trace mixes 80 hot keys (one request per step, chosen at random) with one brand-new object per step, and each new object is requested exactly once more, 15 to 25 steps later. The cache holds 100. Predict how LRU and S3-FIFO do on the new objects' second requests.
A: LRU hits them: between an object's two requests there are fewer than 100 distinct keys, so it is still cached. S3-FIFO misses them: each object is hit zero times in S and is dropped to G after about 10 insertions, long before its second request. That request then finds it in G and moves it into M, where it is never used again, which keeps M full and S at its 10%. In a seeded simulation of 30,000 steps, LRU hits 100% of the second requests and S3-FIFO 1.5%, with S averaging 9.5 slots. This is the adversarial pattern the paper reports.

## Lab

- Replay `a b c d e a a f b a g c h d i i i j` through `S3FIFO(5)`. Expected: 5 hits, final state S `[j]`, M head-to-tail `[a, i, d, c]`, G head-to-tail `[h, g, f, e]`.
- Replay the Zipf trace from the first card (`random.Random(1).choices(...)`, 200,000 requests, 10,000 keys) with capacity 100. Expected miss ratios: LRU 0.610, `S3FIFO` 0.495.
- Replay the scan trace from the TinyLFU card with capacity 100. Expected: `S3FIFO` 0.201, the same as Belady's optimum, against LRU's 0.232.

> [!know]
> You now know how S3-FIFO's small queue demotes one-hit wonders quickly, how its counters promote lazily, and how the ghost queue rescues keys that return.

=== primer | How does SIEVE evict with one queue and a moving hand? | 15 min
goal: Implement SIEVE as specified in the NSDI 2024 paper, explain exactly how its hand differs from CLOCK's, and recognise the workloads where it loses
tag: caching-sieve | SIEVE eviction
link: SIEVE authors' blog: SIEVE is simpler than LRU | https://cachemon.github.io/SIEVE-website/blog/2023/12/17/sieve-is-simpler-than-lru/#design | 6 min: 'Design' (with an animation of the hand), then 'SIEVE is not scan-resistant', where the authors explain the workloads it loses on
link: Zhang et al.: SIEVE is simpler than LRU (NSDI 2024) | https://www.usenix.org/system/files/nsdi24-zhang-yazhuo.pdf | Optional, 15 min: section 3.1 and Algorithm 1 (the rules), and Figure 1, which shows the few lines that turn CLOCK into SIEVE

> [!key]
> SIEVE keeps one FIFO list (new objects at the head), one **visited** bit per object and one **hand**. A hit sets the bit and moves nothing. On a miss with a full cache, the hand starts where it last stopped, walks from the tail towards the head clearing set bits, and evicts the first object whose bit is clear; it then waits at that object's newer neighbour. Unlike CLOCK, a survivor **stays where it is** instead of moving to the head, so new objects and proven survivors never mix, and the hand spends its time sifting the new ones.

## Intuition

Think of a queue of people waiting at a stall, newest at the back. A steward walks along the queue from the front to the back. Anyone who has bought something since the steward last passed gets a nod and keeps their place; the first person who has not bought anything is asked to leave, and the steward stops right there, picking up from the same spot next time.

With CLOCK, the steward would send each nodded-at buyer to the back of the queue, among the newcomers. With SIEVE, the regulars stay put at the front, the steward quickly passes them, and spends most of the time near the back, where the newcomers are, asking the ones who have not bought anything to leave. That is **quick demotion** for newcomers and **lazy promotion** for regulars, with no reordering at all.

## How it works

### The rules (Algorithm 1 of the paper)

- **Hit:** `visited = 1`. For a popular object whose bit is already 1, there is nothing to do.
- **Miss, cache full:** let `o` be the object under the hand, or the tail if the hand is unset. While `o.visited` is 1: set it to 0 and move `o` one step towards the head, wrapping to the tail after the head. Evict `o`, and set the hand to `o`'s newer neighbour (unset if `o` was the head).
- **Insert:** the new object goes to the head with `visited = 0`.

### Why it differs from CLOCK

The paper's Figure 1 shows the whole difference in code. CLOCK (FIFO-reinsertion) always examines the tail and moves a visited object to the head. SIEVE examines the object under its hand and leaves a visited object in place. Two consequences:

- **Survivors cluster near the tail.** The hand passes over them in one quick sweep, clearing their bits, and they stay cached as long as they are hit again before the hand comes back.
- **New objects are examined soon.** After the first sweep, the hand lingers in the newer part of the list. A new object that is not hit before the hand reaches it is evicted, typically long before it would have reached the tail of an LRU list.

### What the paper reports

On 1,559 traces from 7 datasets, SIEVE reduced ARC's miss ratio by up to 63.2% (mean 1.5%), and it had a lower miss ratio than every other algorithm tested on more than 45% of the traces. Because hits only set a bit, its prototype reached twice the throughput of an optimised LRU at 16 threads, and adding it to five production cache libraries (Cachelib, groupcache, mnemonist, lru-dict, lru-rs) took fewer than 20 changed lines on average.

## Cost

- **Hit:** a dict lookup and at most one bit write, O(1), with no lock on the list.
- **Eviction:** every hand step either clears a bit or evicts. As with CLOCK, a bit is set only by a hit, so over `R` requests the hand moves at most `R` times in total: **amortised O(1)**, worst case one full lap of `C` steps.
- **Memory:** one bit per object, plus the list links. Evicting from the middle of the list needs a doubly linked list (two pointers per object, the same as LRU), but the pointers are only written on insert and evict, never on a hit.

## When to use it

| Situation | SIEVE? |
|---|---|
| Web, CDN and key-value caches with skewed popularity | Yes: its home ground in the paper |
| Replacing LRU in an existing library with minimal code | Yes: add a bit and a hand to the existing list |
| Block or storage caches where scans mix with popular objects | No: the authors note both get evicted quickly, and with no ghost queue SIEVE cannot recognise a popular object that returns |
| Objects that are each requested twice, shortly apart, alongside a hot set | No: a new object is usually evicted before its second request. On the trace from the S3-FIFO card's last question, SIEVE hit 0.3% of second requests (S3-FIFO 1.5%, LRU 100%) |

SIEVE also works as a building block: the authors report that swapping SIEVE in for the LRU queues inside LeCaR, 2Q and ARC improved all three.

## Worked trace

`Sieve(4)` on `A B C D A B E F A G C`. The list is shown head (newest) first; `*` marks a visited bit.

```steps
A B C D miss and fill the cache; the hand is unset, which means "start at the tail"
    head  D  C  B  A  tail      hand: unset
---
A and B hit: only their bits change
    head  D  C  {{B* A*}}  tail      hand: unset
---
E misses: start at the tail. A* is cleared and stays, B* is cleared and stays, C is unvisited and is evicted. The hand waits at D, C's newer neighbour
    head  {{E}}  D  B  A  tail      hand: D
---
F misses: the hand is at D, unvisited, so D goes at once. The hand moves to E
    head  {{F}}  E  B  A  tail      hand: E
---
A hits: its bit is set again, it stays near the tail
    head  F  E  B  {{A*}}  tail      hand: E
---
G misses: E is unvisited and goes; then C misses: F goes. B and A were never touched again by the hand
    head  {{C  G}}  B  A*  tail      hand: G
```

After the first sweep, every eviction hit a recent arrival that had not been requested again, while A and B, which had shown reuse, sat untouched at the tail. CLOCK on the same trace would have moved A and B to the head on the first sweep, among the newcomers.

## Template

```python
class Node:
    __slots__ = ("key", "visited", "prev", "next")

    def __init__(self, key):
        self.key, self.visited = key, False
        self.prev = self.next = None


class Sieve:
    """SIEVE (Zhang et al., NSDI 2024): one FIFO list, a visited bit, a hand."""

    def __init__(self, capacity):
        self.cap = capacity
        self.map = {}
        self.head = self.tail = None    # head = newest, tail = oldest
        self.hand = None                # next eviction candidate (None = tail)

    def access(self, key):
        node = self.map.get(key)
        if node:
            node.visited = True         # a hit never moves anything
            return True
        if len(self.map) >= self.cap:
            self._evict()
        node = Node(key)                # insert at the head
        node.next = self.head
        if self.head:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node
        self.map[key] = node
        return False

    def _evict(self):
        o = self.hand or self.tail
        while o.visited:                # survivors stay where they are
            o.visited = False
            o = o.prev or self.tail     # walk towards the head, wrap at the end
        self.hand = o.prev              # resume here next time
        if o.prev:                      # unlink o
            o.prev.next = o.next
        else:
            self.head = o.next
        if o.next:
            o.next.prev = o.prev
        else:
            self.tail = o.prev
        del self.map[o.key]
```

Here `prev` points towards the head (newer) and `next` towards the tail (older), so the hand walks along `prev`.

## Pitfalls

- **Restarting the hand at the tail on every eviction.** That turns SIEVE into a slow variant of CLOCK without reinsertion; the stored hand position is the whole idea.
- **Moving survivors.** If you move a visited object to the head, you have written CLOCK again.
- **Forgetting the wrap.** When the hand walks past the head it must continue from the tail; without the wrap, `o.prev` becomes `None` and the loop crashes when every object near the head is visited.
- **Losing the hand on deletion.** If your cache supports explicit deletes or expiry, deleting the object under the hand must move the hand to that object's newer neighbour first, or the hand dangles.
- **Expecting ghost-like recovery.** SIEVE forgets an evicted object completely; a popular object evicted during a burst of new keys starts again from scratch.

## Check yourself

Q: Continue the worked trace with one more request, `H`. Which object is evicted, and where does the hand end up?
A: The hand is at G, which is unvisited, so G is evicted and the hand moves to C (G's newer neighbour). The list becomes `H C B A*`. B and A again are not touched.

Q: Both CLOCK and SIEVE evict amortised O(1). Why can SIEVE still evict different objects from CLOCK on the same trace, given the same bits?
A: The order in which the hand meets objects differs. CLOCK moves each survivor to the head, so survivors and newcomers interleave and the hand always starts at the tail. SIEVE leaves survivors at the tail and resumes from where it stopped, which is usually among the newest objects, so it meets (and evicts) new unvisited objects first.

Q: A storage system's block cache sees long sequential scans mixed with random reads of a popular set. Would you pick SIEVE or S3-FIFO, and why?
A: S3-FIFO. Its ghost queue recognises a popular block that was evicted during a scan and returns it straight to the main queue, and its small queue keeps scan blocks out of the main queue. SIEVE has no ghost, and the authors themselves note that when scans intermingle with popular objects, both are evicted quickly.

## Lab

- Replay `A B C A D B E A F B G A H B A C D A E A` (20 requests) with capacity 3 through `Sieve`, `Clock` and LRU. Expected hits: SIEVE 6, CLOCK 4, LRU 4.
- Replay the Zipf trace from the first card with capacity 100. Expected miss ratio: `Sieve` 0.492 (LRU 0.610, S3-FIFO 0.495).
- Stress test: compare `Sieve` with a slow reference that stores the list as a Python list and the hand as an index, on 2,000 random traces with capacities 1 to 8. Expected: identical hit sequences.

> [!know]
> You now know how SIEVE's stationary survivors and resuming hand give quick demotion and lazy promotion in a single queue, and where its lack of a ghost queue hurts.

=== primer | How do you measure a cache with trace replay and miss-ratio curves? | 17 min
goal: Replay a trace through candidate policies, compute an LRU miss-ratio curve for every cache size in one pass, bound it with Belady's optimum, and read the curve to size a cache
tag: caching-mrc | Miss-ratio curves from trace replay
link: Waldspurger et al.: SHARDS (FAST 2015) | https://www.usenix.org/system/files/conference/fast15/fast15-paper-waldspurger.pdf | Optional, 20 min: section 2 (Mattson's stack algorithm and why exact curves are expensive), section 3.1 'Basic SHARDS', and 4.3.3, the SHARDS-adj correction the template uses

> [!key]
> A hit ratio belongs to a policy, a size and a workload together, so measure it by **replaying a real trace**. Plot miss ratio against cache size and you get a **miss-ratio curve** (MRC), which tells you what memory buys. For LRU, one pass produces the whole curve: a request hits in every LRU cache larger than its **reuse distance** (the number of distinct other keys since its previous request), so a histogram of distances answers every size at once (Mattson et al.). **Belady's MIN**, which evicts the key needed furthest in the future, gives the floor no online policy can beat.

## Intuition

Keep a pile of books, most recently used on top. Each time you need a book, pull it out from wherever it is in the pile and put it back on top. A shelf that holds `c` books always contains exactly the top `c` of the pile, whatever `c` is. So if a book was found at depth 7 (seven other books above it), it was on every shelf holding 8 or more books and on no smaller shelf. Write down the depth of every request once, and you know the hit ratio of every shelf size.

## How it works

### Replay first, opinions second

A trace is the sequence of requests the cache saw: at least a key per request, ideally also object size, time, operation (get, set, delete) and TTL. Replay it through each candidate policy at each candidate size and count misses. Report:

- **Miss ratio** (misses / requests): what your backend feels. A miss ratio that falls from 0.10 to 0.05 halves the backend's load, even though the hit ratio only moved from 90% to 95%.
- **Byte miss ratio** when objects vary in size and bandwidth or disk is the bottleneck.
- **Cold misses** separately: the first request for each key always misses, so long traces or a warm-up period are needed before comparing policies.

### Mattson's stack algorithm for LRU

LRU has the **inclusion property**: a cache of size `c` holds the `c` most recently used keys, so a bigger LRU cache always holds a superset of a smaller one. A request with reuse distance `d` therefore hits exactly in the caches with `c > d`. One pass computing `d` for every request gives the full curve: `miss(c) = 1 - (requests with d < c) / N`.

Computing `d` naively (a list of keys in recency order, find and move) costs O(number of distinct keys) per request. The template does it in O(log N): keep a Fenwick tree over request positions with a 1 at each key's **latest** position. The distinct keys requested since key `k`'s previous position `p` are exactly the 1s strictly between `p` and now. The range-queries module explains Fenwick trees; here you only need "add at a position" and "count up to a position".

### What other policies need

FIFO, CLOCK, S3-FIFO, SIEVE and W-TinyLFU are not stack algorithms: a bigger cache does not necessarily hold a superset, so you replay once per size. FIFO even shows **Belady's anomaly**: on `1 2 3 4 1 2 5 1 2 3 4 5` it misses 9 times with 3 slots and 10 times with 4.

### Sampling: SHARDS

Exact curves need memory proportional to the trace. SHARDS samples **keys**, not requests: keep a request only if `hash(key)` falls below a threshold (rate `R`), compute distances on the sampled stream, and multiply them by `1 / R`. Sampling by key keeps every request for the sampled keys, so their reuse patterns stay intact. The paper reports that `R = 0.001` gives very accurate curves on its storage traces. Its **SHARDS-adj** correction fixes samples that caught too many or too few hot keys: add the difference between the expected and actual number of sampled requests to the distance-0 bucket. Accuracy depends on how many distinct keys the sample contains:

| Zipf(0.9), 200,000 requests, 50,000 keys | size 1,000 | size 5,000 |
|---|---|---|
| Exact | 0.607 | 0.412 |
| SHARDS-adj, R = 0.1 (about 5,000 keys sampled) | 0.610 | 0.422 |
| SHARDS-adj, R = 0.01 (about 500 keys sampled) | 0.625 | 0.471 |

### Reading the curve

A steep start then a flat tail means a small hot set: size the cache near the **knee**, where an extra gigabyte stops buying much. A **cliff** (a sudden drop at one size) means a loop: LRU misses every request of a loop over `L` keys when it holds fewer than `L`, and none once it holds `L`. The gap between your policy's curve and Belady's tells you how much a smarter policy could still win at that size; the gap between Belady and zero is cold misses and genuinely unpredictable traffic.

## Cost

- **Replaying one policy at one size:** O(N) for the O(1)-per-request policies in this module; S sizes times P policies costs O(S x P x N).
- **Mattson with a Fenwick tree:** each request does two prefix queries and two point updates, each O(log N): **O(N log N) time**, O(N) memory for the tree (a balanced tree keyed by time would make it O(distinct keys)). It replaces S separate LRU replays.
- **SHARDS:** the sampled stream has about `R x N` requests over `R x M` keys, so time and memory shrink by the factor `R` (plus one hash per request to decide).
- **Belady:** needs the future, so precompute each request's next use in one backward pass, then keep cached keys in a max-heap by next use: O(N log C).

## When to use it

- **Before changing a policy or a size**, and in every capacity-planning discussion: an MRC turns "add more RAM" into "1 GB more cuts backend load by X%".
- **When a hit ratio drops**, replay yesterday's and today's traces through the same policy: if the curves differ, the workload changed; if not, look at the cache.
- **Not with an unrepresentative trace.** A synthetic Zipf trace has no scans, bursts or diurnal shifts; use it to test code, not to choose production policy. When keys are sensitive, hash them before recording; the replay only needs equality.

## Worked trace

LRU stack (most recent first) on `a b c a b d a d b c`; `d` is the number of distinct keys above the requested key.

```steps
a b c: three cold misses (no previous request)
    stack  c  b  a
---
a is found below c and b: d = 2, so it hits only in caches of 3 or more
    stack  {{a}}  c  b          d = 2
---
b is below a and c: d = 2. Then d (the key) is new: a cold miss
    stack  {{d}}  b  a  c       b: d = 2, d: cold
---
a: d = 2 (below d and b)
    stack  {{a}}  d  b  c       d = 2
---
d: d = 1 (only a above it), a hit in any cache of 2 or more
    stack  {{d}}  a  b  c       d = 1
---
b: d = 2; then c: d = 3 (below b, d and a)
    stack  {{c  b}}  d  a       b: d = 2, c: d = 3
---
Histogram: d = 1 once, d = 2 four times, d = 3 once, 4 cold. Hits at size c are the requests with d < c
    size       1     2     3     4
    LRU miss  1.0   0.9   0.5   0.4
    Belady    1.0   0.7   0.5   0.4
```

At size 2, Belady saves two misses that LRU cannot: it knows which of the two cached keys comes back sooner.

## Template

```python
import hashlib
import heapq
from collections import Counter


def lru_mrc(trace, max_size, rate=1.0):
    """Miss ratio of an LRU cache of every size 1..max_size, from one pass.
    rate < 1 samples keys by hash (SHARDS) and rescales distances by 1/rate."""
    def sampled(key):
        h = int.from_bytes(hashlib.blake2b(repr(key).encode(), digest_size=8).digest(), "big")
        return h < rate * 2**64
    expected = len(trace) * rate       # how many requests a fair sample would have
    trace = [k for k in trace if rate >= 1 or sampled(k)]
    n = len(trace)
    tree = [0] * (n + 1)               # Fenwick tree: 1 at each key's latest position

    def add(i, v):
        i += 1
        while i <= n:
            tree[i] += v
            i += i & -i

    def marks_before(i):               # number of 1s at positions < i
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & -i
        return s

    last, dist = {}, Counter()         # dist[d] = re-uses with d other keys in between
    for t, key in enumerate(trace):
        if key in last:
            p = last[key]
            d = marks_before(t) - marks_before(p + 1)   # distinct keys since last use
            dist[int(d / rate)] += 1
            add(p, -1)
        add(t, 1)
        last[key] = t
    dist[0] += expected - n            # SHARDS-adj: fix a sample with too many or too few hot keys
    curve, hits = [], 0                # a re-use hits in size c iff d < c
    for c in range(1, max_size + 1):
        hits += dist[c - 1]
        curve.append(1 - hits / expected)
    return curve


def belady_misses(trace, capacity):
    """Misses of Belady's MIN: when full, evict the key whose next use is furthest away."""
    nxt, seen = [0] * len(trace), {}
    for i in range(len(trace) - 1, -1, -1):        # next use of each request's key
        nxt[i] = seen.get(trace[i], float("inf"))
        seen[trace[i]] = i
    cached, heap, misses = {}, [], 0               # key -> next use; max-heap by next use
    for i, key in enumerate(trace):
        if key not in cached:
            misses += 1
            if len(cached) >= capacity:
                while True:                        # skip entries made stale by later uses
                    neg_next, _, k = heapq.heappop(heap)
                    if cached.get(k) == -neg_next:
                        del cached[k]
                        break
        cached[key] = nxt[i]
        heapq.heappush(heap, (-nxt[i], i, key))
    return misses
```

## Pitfalls

- **Off-by-one in the distance.** Define `d` as the number of *other* distinct keys (so an immediate re-request has `d = 0` and hits in a cache of 1). Using the 1-based stack depth and then scaling by `1 / R` adds `1 / R - 1` to every sampled distance and biases the curve upwards.
- **Sampling requests instead of keys.** Dropping random requests breaks reuse: a key's second request may be kept while its first is dropped. Sample by key hash.
- **Too few sampled keys.** On a small, skewed trace a 1% sample holds only a few hundred keys and misses badly (0.471 against 0.412 in the table). Sample rates like 0.001 work on traces with millions of keys.
- **Comparing policies on different traces or without warm-up.** Use the same trace, the same sizes and the same treatment of cold misses for every candidate.
- **Using an LRU curve for a non-LRU cache.** The curve is exact for LRU only; for S3-FIFO or W-TinyLFU, replay them, or use the LRU curve only as a rough guide.

## Check yourself

Q: In the worked trace, which request is the only one that hits in a cache of size 2, and why does no other?
A: The second `d` (position 8), with `d = 1`: only `a` was requested since the previous `d`. Every other re-request has `d >= 2`, so it needs at least 3 slots.

Q: Why does a single pass give the LRU miss ratio for every size, but not the FIFO miss ratio?
A: LRU's content at size `c` is always the top `c` of one recency stack, so whether a request hits at size `c` depends only on its depth in that stack. FIFO's content depends on the size itself (when each key was inserted depends on earlier evictions, which differ between sizes), so there is no single stack, and Belady's anomaly shows a bigger FIFO cache can even miss more.

Q: Your service's cache has a 0.08 miss ratio at 16 GB and the MRC shows 0.05 at 32 GB. The backend handles 50,000 requests per second at present. What does doubling the cache buy?
A: Backend load is request rate times miss ratio, so it falls from `0.08 x R` to `0.05 x R`, a 37.5% cut. If 50,000 requests per second reach the backend now, about 31,250 would after doubling.

## Lab

- Run `lru_mrc(list("abcabdadbc"), 4)` and `belady_misses` for sizes 1 to 4. Expected: LRU `[1.0, 0.9, 0.5, 0.4]`; Belady misses `[10, 7, 5, 4]` out of 10.
- Stress test `lru_mrc(trace, 14)` against replaying an `OrderedDict` LRU at every size 1 to 14 on 300 random traces of up to 80 requests over at most 12 keys. Expected: equal to 12 decimal places.
- Replay FIFO on `1 2 3 4 1 2 5 1 2 3 4 5`. Expected: 9 misses with 3 slots and 10 with 4 (Belady's anomaly). Then check that `lru_mrc` on the same trace never increases as the size grows.

> [!know]
> You now know how to measure a cache instead of guessing: replay a trace, build an LRU miss-ratio curve in one pass, sample it with SHARDS, and compare against Belady's floor.
