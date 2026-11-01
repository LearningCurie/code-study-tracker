---
key: llmserve
name: Inside LLM serving: KV caches, prefix trees and decoding
stage: aisys
summary: The data structures inside an LLM server: a paged block allocator for the KV cache, a radix tree that shares prompt prefixes, heaps and prefix sums for decoding, and the queues that decide what runs at every step.
why: The AI guide shows what PagedAttention, prefix caching, sampling and continuous batching do for you as a user. This module opens them up, and each turns out to be a classic structure working under a tight GPU memory budget: virtual-memory paging with reference counts and copy-on-write, a compressed trie with least-recently-used eviction of leaves, a size-k heap, prefix sums with binary search, and a first-come-first-served queue with preemption. Knowing the structures lets you predict a server's behaviour (why a prompt change kills the cache hit rate, why throughput collapses when memory runs short, why beam search returns short answers) and read the vLLM and SGLang code that implements them. The same patterns recur in operating systems, databases and every cache you will build.
outcomes:
- Implement a KV block pool with block tables, reference counts and copy-on-write, and map each part to operating-system virtual memory
- Build a radix-tree prefix cache with node splitting, path locks and LRU eviction of leaves, and measure its token hit rate
- Implement beam search with a size-k min-heap and choose a length penalty knowing what it does
- Implement temperature, top-k and top-p sampling with a heap, prefix sums and binary search, and state the cost of each step
- Simulate an iteration-level scheduler with a token budget, a KV block limit and preemption by recomputation
- Read the cache and scheduler code of vLLM and SGLang and name the data structure behind each mechanism
cues:
- Buffers that grow one item at a time to an unknown length in a shared memory pool: allocate fixed-size blocks on demand behind a per-owner table
- Many requests that start with the same tokens (system prompts, few-shot examples, earlier chat turns): index them by prefix
- "Keep the best k of many scored candidates" at every step: a size-k heap or a partial selection
- "Sample from the smallest set covering probability p": sort, prefix sums, then binary search
- Jobs of different lengths sharing one machine step by step under memory and time budgets: a queue that is re-planned every step, not fixed batches
traps:
- Writing into a KV block that another sequence still shares, without copying it first
- Evicting a radix-tree node that a running request still uses, or an inner node whose descendants then become unreachable
- Comparing beam hypotheses of different lengths by raw log-probability, which favours short outputs
- Taking the top-p cut on unsorted probabilities, or losing the mapping from sorted positions back to token ids
- Admitting new requests in the same step that had to preempt one, which makes the KV cache thrash
systems:
- vLLM's V1 KV cache manager allocates every block object up front and threads a doubly linked free list through them (FreeKVCacheBlockQueue), so a cached block can be pulled out of the middle in O(1); each block carries a reference count, and a finished request's blocks are freed in reverse order so its tail blocks are evicted first (vLLM design docs, Automatic Prefix Caching)
- vLLM's V1 scheduler (vllm/v1/core/sched in v0.32) keeps waiting requests in a deque for first-come-first-served or a heapq for priority scheduling, schedules running requests before waiting ones within a token budget, and when a block cannot be allocated preempts the last running request (or the lowest priority one), frees its blocks, resets its computed tokens to zero and puts it back at the front of the waiting queue; no waiting request is admitted in that step
- SGLang's RadixCache (python/sglang/srt/mem_cache/radix_cache.py in v0.5.22) keys children by their first token, splits a node when a prompt matches part of an edge, pins in-use paths with a lock_ref counter on every node up to the root, and evicts by popping unlocked leaves from a heap ordered by last access time, pushing a parent once it becomes a childless leaf
- SGLang offers cache-aware scheduling policies such as lpm (longest prefix match) beside fcfs; its paper proves that longest-shared-prefix-first order is a depth-first traversal of the radix tree, which gives the optimal hit rate for a batch when the cache holds at least the longest request
- Hugging Face Transformers (v5.22) builds its sampling pipeline as temperature, then top-k, then top-p, then min-p, and implements top-p by sorting the logits, taking cumulative softmax probabilities and masking the tail
further:
- Paper · 60 min | Kwon et al. 2023, Efficient memory management for LLM serving with PagedAttention (SOSP): read §4.1 to §4.5 for block tables, copy-on-write, beam sharing and preemption | https://arxiv.org/abs/2309.06180
- Paper · 45 min | Zheng et al. 2024, SGLang: read §3 (RadixAttention and cache-aware scheduling, with the nine-step Figure 3) and the proof of Theorem 3.1 in the appendix | https://arxiv.org/abs/2312.07104
- Paper · 30 min | Holtzman et al. 2020, The curious case of neural text degeneration: read §3.1 to §3.3 (nucleus sampling, top-k, temperature) | https://arxiv.org/abs/1904.09751
- Paper · 15 min | Wu et al. 2016, Google's neural machine translation system: read §7 for beam search with length normalisation, coverage penalty and pruning | https://arxiv.org/abs/1609.08144
---

=== primer | How does PagedAttention store a growing KV cache without wasting memory? | 16 min
goal: Implement a paged KV-cache allocator with block tables, reference counts and copy-on-write, and explain each part through operating-system virtual memory
tag: llmserve-paging | Paged KV blocks and block tables
link: vLLM design docs: automatic prefix caching, data structure | https://docs.vllm.ai/en/latest/design/prefix_caching/#data-structure | 10 min: read 'Data Structure', 'Free' and 'Eviction (LRU)': vLLM's real block objects carry a reference count and linked free-list pointers, the production form of this card's pool
link: AI guide: PagedAttention and vLLM | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-pagedattention-and-vllm | About 12 min: The user's side of this card: how paging raises throughput, and the vLLM flags that size the KV pool

> [!key]
> A request's KV cache grows by one token per decoding step and nobody knows its final length. PagedAttention stores it in fixed-size **blocks** taken from a shared pool on demand, and each sequence keeps a **block table** that maps its logical block i to a physical block anywhere in memory. Blocks carry **reference counts**, so forked sequences share them, and a write to a shared block **copies it first**. Waste falls to at most one partly filled block per sequence: the same trade operating systems made with pages.

## Intuition

A hotel hosts conference groups whose size it learns only as people arrive. The old policy reserves a whole corridor for every group, sized for the largest group the hotel has ever seen; most rooms stay empty, and the leftover corridors come in awkward sizes nobody else can use. The new policy hands out rooms one at a time, anywhere in the building, and gives each group a room list. A group never holds more than one half-empty room, and two groups that share a meeting can point at the same room until one of them needs to change it.

The KV cache is the guest list. For every token in a sequence, each layer stores a key vector and a value vector so that later tokens can attend to it without recomputing. Earlier serving systems stored each request's cache contiguously and pre-reserved room for its maximum length. The PagedAttention paper profiled them: only **20.4% to 38.2%** of their KV memory held actual token states, against **96.3%** for vLLM (Kwon et al. 2023, Figure 2).

## How it works

### The pieces, next to the operating system

| Operating-system virtual memory | PagedAttention |
|---|---|
| Page (for example 4 KiB) | KV block of B tokens (vLLM's default B is 16) |
| Process | Sequence |
| Page table | Block table: a list of physical block ids |
| Frame allocated on first touch | Block allocated when the previous one is full |
| `fork()` shares pages copy-on-write | Parallel samples and beam candidates share blocks copy-on-write |
| Swap pages to disk | Swap blocks to CPU memory, or drop them and recompute |

### Address translation

The token at position `pos` lives in physical block `table[pos // B]` at offset `pos % B`. The attention kernel does exactly this lookup when it gathers keys and values, which is the part the name "PagedAttention" refers to.

### Append, fork and free

- **Append.** Compute `slot = n % B`. If `slot == 0`, the sequence has no block yet or its last block is full, so pop a block from the free list. Otherwise the token goes into the last block, unless that block's reference count is above one: then **copy on write** first (allocate a new block, copy the `slot` filled entries, drop one reference to the old block, point the table at the copy).
- **Fork.** Copy the table, which is a short list of integers, and add one to the reference count of every block in it. No key or value is copied.
- **Free.** Drop one reference per block; a block whose count reaches zero goes back to the free list.

Blocks fill from left to right and only the last one is ever written, so every earlier block is immutable once full. That is why copy-on-write never copies more than one block per fork, as the paper notes for beam search.

### When the pool runs dry

Sequences grow at every step, so a batch that fitted can stop fitting. The paper's answer (§4.5) is preemption with an all-or-nothing rule: evict every block of a sequence or none, then either swap the blocks to CPU memory or simply free them and recompute the cache later from the prompt plus the tokens generated so far. vLLM's current engine recomputes. The continuous batching card simulates this.

### Sharing across requests

The same reference counts let one cached prompt prefix appear in many block tables, which is how prefix caching reuses work across requests (next card). vLLM's V1 design keeps block tables append-only and shares only full blocks through its prefix cache.

## Cost

**Memory per token.** Each layer stores one key and one value vector per KV head, so bytes per token = 2 × layers × KV heads × head dimension × bytes per value. For 32 layers, 8 KV heads of dimension 128 and 16-bit values that is 2 × 32 × 8 × 128 × 2 = 131,072 bytes, 128 KiB per token, and a 16-token block is 2 MiB. The AI guide's KV-cache memory lesson works through real model configs.

**Waste.** Reserving `max_len` contiguously wastes `max_len - n` slots per sequence. Paging wastes only the unfilled tail of the last block: at most B − 1 slots, about B/2 on average when lengths are random. On a synthetic workload of 1,000 requests (log-normal lengths, mean 541 tokens, capped at 2,048), contiguous reservation put tokens in 26.4% of reserved slots; paging with B = 16 put tokens in 98.6%, wasting 7.5 slots per sequence on average, close to B/2 = 8.

**Operations.** Append is O(1), plus one O(B) block copy the first time a forked sequence writes. Fork and free are O(number of blocks), which is n/B, instead of copying O(n) vectors. Translation is O(1) but adds an indirection to the attention kernel: the paper measured 20 to 26% higher attention-kernel latency than FasterTransformer's contiguous kernel (§7.1), repaid many times over by larger batches.

## When to use it

Reach for paging when many variable-length buffers grow unpredictably inside one fixed pool, or when buffers must share long common parts cheaply.

| Approach | Waste per sequence | Growth | Fork or share | Read |
|---|---|---|---|---|
| Reserve the maximum length contiguously | `max_len - n` slots, plus external fragmentation | free until the cap | copy everything | direct |
| Grow a contiguous buffer by doubling, like a Python list | up to n slots of slack, plus copies on every growth | amortised O(1) with copying | copy everything | direct |
| Paged blocks with a block table | under B slots | O(1), no copying | O(n/B) table copy | one table lookup |

Do not bother when every buffer has the same known size (fixed-length classification inputs, say): a contiguous arena wastes nothing and avoids the indirection. Block size is itself a trade-off. Too small and the kernel cannot read enough in parallel; too large and internal fragmentation rises and less is shared. The paper found 16 to 128 best on one trace, while on a trace of short sequences larger blocks degraded performance, so vLLM chose 16 (§7.2).

## Worked trace

Block size 4. The free list hands out blocks 7, 1, 3, 0, ... in that order, which reproduces Figures 6 and 8 of the paper: a 7-token prompt, then two samples that share it.

```steps
A writes a 7-token prompt: slots 0 and 4 start new blocks, so A takes block 7, then block 1
    A table  [7, 1]   n = 7
    block 7  t0 t1 t2 t3     ref 1
    block 1  t4 t5 t6 __     ref 1
    free     next out: 3, 0, 2, ...
---
Fork B from A for a second sample: copy the table, add a reference to each block. Nothing else moves
    A table  [7, 1]   B table  [7, 1]
    block 7  t0 t1 t2 t3     ref {{2}}
    block 1  t4 t5 t6 __     ref {{2}}
---
A appends a7 at slot 7 % 4 = 3 of block 1, but block 1 is shared: copy on write into block 3
    A table  [7, {{3}}]   B table  [7, 1]
    block 3  t4 t5 t6 {{a7}}   ref 1
    block 1  t4 t5 t6 __     ref {{1}}
---
B appends b7: block 1 now has one owner, so B writes in place with no copy
    B table  [7, 1]
    block 1  t4 t5 t6 {{b7}}   ref 1
---
B appends b8 at slot 8 % 4 = 0: its last block is full, so it takes a fresh block (0)
    B table  [7, 1, {{0}}]
    block 0  {{b8}} __ __ __   ref 1
---
Read A's position 5: block A.table[5 // 4] = A.table[1] = 3, offset 5 % 4 = 1, which holds t5
    A table  [7, {{3}}]   block 3  t4 {{t5}} t6 a7
---
Free A: block 7 drops to 1 reference (B still uses it); block 3 drops to 0 and returns to the free list
    refs     block 0: 1   block 1: 1   block 3: {{0}}   block 7: {{1}}
    free     next out: {{3}}, 2, 4, ...
```

## Template

```python
class BlockPool:
    """Fixed-size KV blocks shared by reference count, as in PagedAttention."""

    def __init__(self, num_blocks, block_size, order=None):
        self.block_size = block_size
        order = list(range(num_blocks)) if order is None else list(order)
        self.free = order[::-1]                # a stack: pop() hands out order[0] first
        self.ref = [0] * num_blocks
        self.slots = [[None] * block_size for _ in range(num_blocks)]  # stands in for K and V

    def alloc(self):
        if not self.free:
            raise MemoryError("no free KV blocks: preempt a sequence")
        b = self.free.pop()
        self.ref[b] = 1
        return b

    def release(self, b):
        self.ref[b] -= 1
        if self.ref[b] == 0:
            self.free.append(b)


class Sequence:
    """One sequence's view of the cache: a block table plus a token count."""

    def __init__(self, pool):
        self.pool, self.table, self.n = pool, [], 0

    def append(self, kv):
        pool, slot = self.pool, self.n % self.pool.block_size
        if slot == 0:                          # no block yet, or the last one is full
            self.table.append(pool.alloc())
        elif pool.ref[self.table[-1]] > 1:     # last block is shared: copy on write
            old, new = self.table[-1], pool.alloc()
            pool.slots[new][:slot] = pool.slots[old][:slot]
            pool.release(old)
            self.table[-1] = new
        pool.slots[self.table[-1]][slot] = kv
        self.n += 1

    def fork(self):
        child = Sequence(self.pool)
        child.table, child.n = self.table[:], self.n
        for b in self.table:
            self.pool.ref[b] += 1
        return child

    def free(self):
        for b in self.table:
            self.pool.release(b)
        self.table, self.n = [], 0

    def read(self, pos):
        b, off = divmod(pos, self.pool.block_size)
        return self.pool.slots[self.table[b]][off]
```

A random stress test (create, append, fork, free, then compare every `read` with plain Python lists and check that each block's reference count equals the number of tables holding it) passes 300 runs of 300 operations; deleting the copy-on-write branch makes it fail.

## Pitfalls

- **Writing into a shared block.** Without copy-on-write, a sample's new token silently overwrites its sibling's cache entry, and the sibling generates from corrupted state with no error.
- **Reference counts that drift.** Forgetting the increment on fork, or freeing twice, returns a block to the free list while a table still maps it: a use-after-free that surfaces as another request's tokens. Assert that counts equal table occurrences in tests.
- **Off-by-one on allocation.** Allocate when `n % B == 0`, which includes the very first token, not when the block is about to fill.
- **Leaks on cancellation.** A cancelled, preempted or failed request must free its table, or the pool shrinks until every request is preempted.
- **Forgetting the indirection cost.** Paging trades a little kernel speed for memory. With fixed, equal lengths you pay that cost for nothing.

## Check yourself

Q: With B = 16, a sequence holds 40 tokens. How many blocks does it use, where is token 33, and how many slots are wasted?
A: ceil(40 / 16) = 3 blocks. Token 33 is in `table[33 // 16] = table[2]` at offset 33 % 16 = 1. The blocks have 48 slots for 40 tokens, so 8 are wasted, all in the last block.

Q: Why can copy-on-write never need to copy more than one block per forked sequence?
A: Blocks fill strictly left to right, so every block except the last is full and never written again. A shared full block can stay shared forever. Only the shared, partly filled last block can receive a write, and after it is copied the sequence owns its tail, so later appends either write in place or open fresh blocks.

Q: A colleague's `fork` copies the table but does not increment the reference counts. Describe two things that go wrong.
A: First, appends never trigger copy-on-write (the count is still 1), so parent and child write into the same last block and corrupt each other. Second, when the parent frees, the counts hit zero and the blocks return to the free list while the child still maps them; the next allocation hands them to another sequence, which overwrites the child's cache.

Q: A batch classifier runs 512-token inputs and produces exactly one output token each. Is paging worth it here?
A: Hardly. Every sequence has the same known length, so a contiguous slot per request wastes nothing and avoids the block-table indirection, which the paper measured at 20 to 26% extra attention-kernel latency. Paging pays when lengths vary and grow unpredictably or when sequences share prefixes.

## Lab

- Fork a 7-token prompt into four sequences (block size 4), append one token to each, and count blocks in use (pool size minus free blocks). Expected: 5 (one shared full block plus four private copies of the partly filled block); after a second token each, 9; without any sharing, 4 × ceil(9 / 4) = 12.
- For lengths [5, 17, 300, 1000, 2047], compute allocated slots for B = 1, 16 and 128, then the fraction used if each request reserved 2,048 contiguous slots. Expected: 3,369, 3,408 and 3,712 slots (waste 0, 39 and 343); contiguous reservation needs 10,240 slots, of which 32.9% are used.
- Write the random stress test described under the template, run it, then delete the copy-on-write branch. Expected: the intact version passes every run; the mutant fails an assertion in the first run that forks and appends.

> [!know]
> You now know how to manage a growing KV cache with a block pool, block tables, reference counts and copy-on-write, and why that is virtual memory again.

=== primer | How does a radix tree let an LLM server reuse the KV cache of shared prompts? | 17 min
goal: Build a radix-tree prefix cache with node splitting, path locks and LRU eviction of leaves, and compare it with vLLM's chained block hashes
tag: llmserve-radix | Radix-tree prefix cache with LRU leaves
link: SGLang source: RadixCache (v0.5.22) | https://github.com/sgl-project/sglang/blob/v0.5.22/python/sglang/srt/mem_cache/radix_cache.py#L552-L580 | 15 min: read evict (lines 552 to 580), then _match_prefix_helper and _split_node further down: the production version of this card's template, with page sizes and priorities added
link: AI guide: Prefix caching and RadixAttention in servers | https://learningcurie.github.io/code-study-tracker/ai.html#l-l-serving-prefix-caching-and-radixattention-in-servers | About 12 min: The user's side: designing prompts and routing so requests actually hit the cache

> [!key]
> Keep every cached token sequence in a **radix tree**: a trie whose edges carry runs of tokens, where siblings start with different tokens. A new prompt walks down from the root, and the depth it reaches is the number of tokens whose KV cache can be reused, found in time proportional to the prompt length however many sequences are cached. Inserting splits an edge where sequences diverge. When memory runs short, evict **leaves** in least-recently-used order, never a node that a running request has **locked**, so shared system prompts near the root survive longest.

## Intuition

Picture every conversation a server has handled written on one branching sheet. The system prompt is the trunk; each conversation branches off where it first differs from the others, and each new turn of a conversation extends its own branch. When a request arrives, you trace it along the sheet as far as it agrees with something already written: that much of its prefill is already done.

That is worth a lot. Prefill costs roughly 2 × parameters floating-point operations per token, so a 1,200-token system prompt re-read by every request of a busy app is a large slice of the server's work. The SGLang paper (Zheng et al. 2024) reports up to 6.4 times higher throughput than other systems on tasks such as agent control, few-shot benchmarks and multi-turn chat, with RadixAttention's KV reuse as one of its main optimisations.

## How it works

### From trie to radix tree

A trie over token ids would store one node per token. A **radix tree** compresses every chain of single-child nodes into one edge labelled with a run of tokens. When every inner node is a branching point, N stored sequences need fewer than 2N nodes however long they are (splits made while matching, below, can add a few single-child nodes). Children are keyed by the first token of their edge, which is unique among siblings, so choosing the next edge is one dictionary lookup.

```text
root
 └─ [SYS be]                        shared by every request of this app
     ├─ [kind]
     │   ├─ [Q1 hello]
     │   │   └─ [A1 hi Q3 bye]      conversation 1, turn 2
     │   └─ [Q2 weather]            conversation 2
     └─ [terse Q4 joke]             a variant of the system prompt
```

Each node also stores the KV cache for the tokens on its edge (in SGLang, indices into a token-granular pool: the paper uses a page size of one token).

### Match, splitting as you go

Walk from the root. At each node, look up the child whose edge starts with the next prompt token, then compare tokens along that edge. If the whole edge matches, descend and continue. If it matches only partly, **split** the edge at the mismatch, so the matched part becomes a node of its own, and stop. The matched length is the reusable prefix, and the node where the walk ends marks exactly the reused part, which you need for locking.

### Insert

Match, then hang the unmatched remainder of the sequence as one new leaf under the node where the match stopped. Servers insert the prompt and the generated output, so the next turn of the same conversation matches all of it.

### Locks and least-recently-used eviction

Every node keeps a **lock count**: the number of running requests whose prefix passes through it. Starting a request adds one to every node from its end node up to the root; finishing subtracts one. Every node also keeps the time it was last on a matched path.

To free memory, collect the unlocked leaves into a min-heap keyed by last access time, pop the oldest, delete it, and if its parent has just become an unlocked leaf, push the parent too. Evicting only leaves keeps the tree consistent: a token's key and value depend on every token before it, so an inner node's cache is useless without its ancestors, and a subtree under a deleted node could never be reached again. Since a parent is touched whenever any of its children is, it is never older than its most recent child, so leaves-first agrees with plain LRU.

### Scheduling for hits

SGLang defines the **cache hit rate** as cached prompt tokens divided by prompt tokens. The order of waiting requests matters: alternating between unrelated prompts thrashes the cache. Its longest-shared-prefix-first policy is a depth-first walk of the radix tree of waiting requests, and Theorem 3.1 of the paper shows that order achieves the optimal hit rate for a batch when the cache holds at least the longest request.

### The other design: chained block hashes

vLLM finds reusable prefixes without a tree. Each **full** block of B tokens gets a hash of its parent block's hash and its own tokens, so one hash identifies the whole prefix up to that block; a new request hashes its prompt block by block and looks each hash up in a dictionary until the first miss.

| | Radix tree (SGLang) | Chained block hashes (vLLM) |
|---|---|---|
| Reuse granularity | any token | whole blocks only (a partial last block is never reused) |
| Lookup | walk the tree: O(L) token comparisons | hash each block: O(L) hashing, O(L/B) dictionary lookups |
| Eviction unit | a whole leaf, of any length | one block, least recently used first |
| Structure | pointers and splits | flat dictionary and append-only block tables |

## Cost

Let L be the prompt length. **Match** consumes at least one prompt token per child lookup and compares each prompt token at most once, so it is O(L), independent of how many sequences are cached; the brute-force alternative compares the prompt with every cached sequence, O(N × L). A split slices one edge, O(edge length) in Python. **Insert** is O(L). **Lock and unlock** are O(depth). The template's **evict** rescans the tree for unlocked leaves, O(nodes), then pops E leaves from the heap, O(E log E); SGLang keeps a running set of evictable leaves instead of rescanning. The tree's own memory (a few pointers and integers per node) is negligible next to 128 KiB of KV per token.

## When to use it

Use a prefix cache when prompts share long beginnings: one system prompt per app, few-shot examples, documents queried repeatedly, multi-turn chat (turn n re-sends turns 1 to n − 1), agent loops, several samples of one prompt. Prefer a radix tree when sharing is deep and branchy and you want token-level reuse; chained block hashes are simpler and fit a block allocator directly. Do not expect gains when prompts are unique, and remember that prefix caching only shortens prefill: it does nothing for long generations. In multi-tenant servers, keep tenants' caches apart (vLLM supports a per-request cache salt), because hit timing can leak whether someone else sent a prompt.

## Worked trace

Tokens are written as words. Times count operations; each node shows its last access time t.

```steps
Insert R1 "SYS be kind Q1 hello" into an empty tree: no match, one leaf with five tokens
    [SYS be kind Q1 hello]  t=1
    cached 5 tokens; hit 0 of 5
---
Insert R2 "SYS be kind Q2 weather": the edge matches 3 tokens, then Q2 differs from Q1, so split
    {{[SYS be kind]  t=2}}
        [Q1 hello]  t=1
        {{[Q2 weather]  t=2}}
    cached 7; hit 3 of 5
---
Insert R3, conversation 1's second turn "SYS be kind Q1 hello A1 hi Q3 bye": 5 tokens match, append a leaf
    [SYS be kind]  t=3
        [Q1 hello]  t=3
            {{[A1 hi Q3 bye]  t=3}}
        [Q2 weather]  t=2
    cached 11; hit 5 of 9
---
Insert R4 "SYS be terse Q4 joke": only "SYS be" matches, so the top edge splits again
    {{[SYS be]  t=4}}
        {{[kind]  t=3}}
            [Q1 hello]  t=3
                [A1 hi Q3 bye]  t=3
            [Q2 weather]  t=2
        {{[terse Q4 joke]  t=4}}
    cached 14; hit 2 of 5
---
Evict at least 4 tokens. Unlocked leaves by age: Q2 weather (t=2), A1 hi Q3 bye (t=3), terse Q4 joke (t=4)
    pop {{[Q2 weather]}}: frees 2; its parent [kind] still has a child
    pop {{[A1 hi Q3 bye]}}: frees 4; its parent [Q1 hello] becomes a leaf and joins the heap
    freed 6 >= 4: stop
---
After eviction: the shared system prompt survives; R2 asked again would reuse 3 tokens
    [SYS be]  t=4
        [kind]  t=3
            [Q1 hello]  t=3
        [terse Q4 joke]  t=4
    cached 8 tokens
```

## Template

```python
import heapq
import itertools


class Node:
    __slots__ = ("children", "parent", "key", "lock", "last", "id")
    ids = itertools.count()

    def __init__(self, parent=None, key=()):
        self.children = {}          # first token of the child's edge -> child
        self.parent = parent
        self.key = key              # the run of tokens on the edge into this node
        self.lock = 0               # running requests whose prefix passes through here
        self.last = 0               # logical time of the last access
        self.id = next(Node.ids)


class RadixCache:
    def __init__(self):
        self.root = Node()
        self.root.lock = 1          # the root is never evicted
        self.clock = itertools.count(1)
        self.size = 0               # cached tokens

    def _split(self, child, k):
        """Cut child's edge after k tokens; return the new node for the first part."""
        mid = Node(child.parent, child.key[:k])
        mid.lock, mid.last = child.lock, child.last
        child.parent.children[mid.key[0]] = mid
        child.key, child.parent = child.key[k:], mid
        mid.children[child.key[0]] = child
        return mid

    def match(self, tokens):
        """Longest cached prefix of tokens: (its length, the node where it ends)."""
        now, node, i = next(self.clock), self.root, 0
        node.last = now
        while i < len(tokens) and tokens[i] in node.children:
            child = node.children[tokens[i]]
            k = 0
            while k < len(child.key) and i + k < len(tokens) and child.key[k] == tokens[i + k]:
                k += 1
            if k < len(child.key):
                child = self._split(child, k)
            child.last = now
            node, i = child, i + k
        return i, node

    def insert(self, tokens):
        """Cache tokens; return (tokens that were already cached, node at the end)."""
        hit, node = self.match(tokens)
        if hit < len(tokens):
            leaf = Node(node, tuple(tokens[hit:]))
            leaf.last = node.last
            node.children[leaf.key[0]] = leaf
            self.size += len(leaf.key)
            node = leaf
        return hit, node

    def lock(self, node, delta):
        """delta=+1 pins the path root..node while a request runs; -1 unpins it."""
        while node is not self.root:
            node.lock += delta
            node = node.parent

    def evict(self, n):
        """Free at least n tokens, least recently used unlocked leaves first."""
        heap = []
        stack = [self.root]
        while stack:
            x = stack.pop()
            stack.extend(x.children.values())
            if not x.children and x.lock == 0:
                heap.append((x.last, x.id, x))
        heapq.heapify(heap)
        freed = 0
        while freed < n and heap:
            _, _, x = heapq.heappop(heap)
            del x.parent.children[x.key[0]]
            freed += len(x.key)
            p = x.parent
            if not p.children and p.lock == 0:
                heapq.heappush(heap, (p.last, p.id, p))
        self.size -= freed
        return freed
```

Tested against brute force: `match` equals the longest common prefix with any cached root-to-leaf sequence (500 random runs with inserts, locks and evictions), `evict` frees exactly what a rescan-every-time reference frees, and locked paths always survive.

## Pitfalls

- **Matching without splitting.** If a match can end in the middle of an edge, there is no node that marks the reused part, so you cannot lock exactly it and cannot hang the new suffix in the right place.
- **Evicting inner nodes.** Deleting a node strands its subtree: memory that can never be matched again. Evict leaves and let parents become leaves.
- **Forgetting locks.** Evicting a node that a running request is reading frees KV memory still in use.
- **Updating only the end node's time.** Every node on the matched path was used; if ancestors keep old times, LRU order is wrong.
- **Text instead of token ids.** The tree is keyed by token ids. A changed chat template, a timestamp near the top or a different tokenisation of the same text misses from that point on.
- **Coarse eviction.** A leaf goes as a whole, even if it is a 3,000-token conversation. With a small cache, a block-granular LRU can keep more useful heads than a leaf-granular one (the lab measures this).

## Check yourself

Q: After the trace's four inserts (before the eviction), what does `match` return for "SYS be terse Q5 pun" and for "SYS be kind Q1 hello A1 hi Q9", and what happens to the tree?
A: 3 and 7. The first walks [SYS be] then matches only "terse" on [terse Q4 joke], splitting it into [terse] and [Q4 joke]. The second walks [SYS be], [kind], [Q1 hello], then matches "A1 hi" on [A1 hi Q3 bye], splitting it into [A1 hi] and [Q3 bye]. The tree now has 9 nodes including the root and still caches 14 tokens: matching splits nodes but never adds or removes tokens.

Q: Why does the cache evict leaves first instead of the least recently used node anywhere in the tree?
A: A node's key and value tensors were computed with all earlier tokens in context, so a node is only useful together with its ancestors, and a subtree below a deleted node can never be reached by a match again. Evicting leaves keeps the cache a set of complete prefixes. It also agrees with LRU, because every match that touches a child touches its parent too, so a parent is never older than its newest child.

Q: A 1,000-token prompt equals a cached one except for its last token. How many tokens does a radix tree reuse, and how many does a chained block hash with B = 16 reuse?
A: The radix tree reuses 999 tokens. The block cache reuses only full matching blocks: the first 62 blocks cover tokens 0 to 991 and match, while the last 8 tokens form a partial block, which is never cached, so it reuses 992.

Q: An implementation keys each node's children by the whole edge label instead of its first token. What breaks?
A: To continue a match you know only the next prompt token, not the length or content of the edge that should follow, so you cannot look the child up; you would have to scan all children. Keying by the first token works because siblings always start with different tokens, which the split operation maintains.

## Lab

- Rebuild the trace, then run the two matches from the first question. Expected: 3 and 7, a tree of 9 nodes including the root, and `size` still 14.
- Continue from that state: match the full second turn of conversation 1 ("SYS be kind Q1 hello A1 hi Q3 bye"), lock the returned node, and call `evict(100)`. Expected: 5 tokens freed ([Q2 weather], then [Q4 joke], then its parent [terse] once it becomes a leaf) and 9 tokens left, all on the locked path. Unlock and call `evict(100)` again: 9 more freed, size 0.
- Write a brute-force checker that collects all root-to-leaf sequences and computes the longest common prefix with a query; compare it with `match` after random inserts and evictions. Expected: no mismatch in a few hundred random runs.

> [!know]
> You now know how to cache and reuse KV across requests with a radix tree, lock the paths in use, and evict least recently used leaves.

=== primer | How does beam search keep the k best hypotheses, and why normalise by length? | 15 min
goal: Implement beam search with a size-k min-heap, trace it on a toy model, and choose a length penalty knowing what it changes
tag: llmserve-beam | Beam search with a size-k heap
link: Hugging Face Transformers: generation strategies, beam search | https://huggingface.co/docs/transformers/generation_strategies#beam-search | 5 min: when beam search fits (input-grounded tasks such as captioning or speech recognition) and the num_beams switch; the length_penalty entry of GenerationConfig on the text generation page gives the exact length division
link: AI guide: Sampling, temperature, top-p and friends | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-sampling-temperature-top-p-and-greedy | About 14 min: Greedy decoding from the user's side, and why open-ended chat samples instead of searching

> [!key]
> Greedy decoding commits to the single most likely token at every step and can miss a sequence that is more likely overall. **Beam search** keeps the k best partial sequences: at each step it extends every beam by every token, scores the candidates by summed log-probability and keeps the best k with a **size-k min-heap**. Finished hypotheses leave the beam. Each token adds a negative log-probability, so raw scores favour short outputs; comparing **log P / length^α** corrects for that.

## Intuition

You are choosing a route through a city with a map that only rates the next street. Taking the best-rated street every time (greedy) can lead you into a district with only bad exits. Keeping your two or three best partial routes open, and extending each by one street at a time, lets a route with a mediocre first street win if what follows is excellent.

A toy model shows it. From the start, "the" has probability 0.5 and "a" 0.4. After "the", the end-of-sequence token has 0.4; after "a", "cat" has 0.9. Greedy takes "the" and ends with probability 0.5 × 0.4 = 0.2. The sequence "a cat <eos>" has 0.4 × 0.9 × 0.6 = 0.216: more likely, but invisible to greedy.

## How it works

### State

A beam is a pair (log-probability, tokens). Sum log-probabilities instead of multiplying probabilities: the product of hundreds of probabilities underflows to 0.0 in floating point, while the sum of their logarithms stays well scaled.

### One step

For every live beam and every vocabulary token, form the candidate (log P + log p(token), tokens + token). Keep the k best of these k × V candidates. A **size-k min-heap** does that in one pass: push until it holds k items; afterwards, if a candidate beats the heap's minimum, replace the minimum (`heapq.heapreplace`). The heap always holds the k best seen so far, and its root is the weakest of them, the one to beat.

A useful shortcut: at most k survivors can come from one beam, and they must be among that beam's own k best tokens. So real implementations take each beam's top k first (a partial selection over V) and then select the k best of k × k.

### Finished hypotheses

A candidate ending in the end-of-sequence token goes to a finished list instead of the next beam, so the live beam shrinks. In the template, the search stops when no live beam remains or the length limit is reached. Libraries differ in how they refill the beam and when they stop early, so read their documentation before comparing outputs.

### Length normalisation

Every extra token adds a negative log-probability, so with raw scores a long hypothesis must be much more probable per token to beat a short one. Google's translation system (Wu et al. 2016, §7) first divided by the length, then by length^α with α between 0.6 and 0.7, and finally used lp(Y) = ((5 + |Y|) / 6)^α. Hugging Face's `length_penalty` divides the summed log-probability by length raised to that power, so values above 0 favour longer outputs. With α = 0 nothing changes; with α = 1 you compare average log-probability per token.

For example, a 2-token hypothesis with log P = −2.0 beats a 6-token one with −3.0 on raw score. At α = 0.6 their scores are −1.320 and −1.024, and at α = 1 they are −1.0 and −0.5: the longer one wins.

### Sharing memory between beams

Beams share their prefix. PagedAttention (§4.4) maps the shared blocks into every beam's table with reference counts; when a beam drops out, its blocks' counts fall and blocks reaching zero are freed, and only the last, partly filled block is ever copied.

## Cost

Per step, scoring k × V candidates with the heap costs O(kV log k) comparisons; with the per-beam shortcut and a linear-time partial selection it is O(kV + k² log k). Over T steps: O(T × kV log k) for selection, plus the model work, which dominates: one forward pass per beam per step, usually batched as one pass of batch size k. Memory is k sequences of up to T tokens, much less with shared KV blocks. Exhaustive search would score V^T sequences: with V = 50,000 and T = 20 that is about 10^94.

## When to use it

| Decoder | Deterministic | Good for | Weak at |
|---|---|---|---|
| Greedy (k = 1) | yes | cheap baselines, short extractions | misses better sequences, loops |
| Beam search (k = 4 to 12) | yes | input-grounded tasks: translation, speech recognition, captioning | open-ended text: bland and repetitive |
| Sampling with top-k or top-p | no | chat, creative and open-ended text | exact reproducibility |

The nucleus sampling paper (Holtzman et al. 2020) shows that maximising probability in open-ended generation produces degenerate, repetitive text, which is why chat models sample. Wider beams give diminishing returns: Google's translation system kept 8 to 12 hypotheses and found 4 or 2 only slightly worse.

## Worked trace

The toy model above, k = 2. Probabilities are shown instead of log-probabilities for readability; the heap stores (log P, tokens) and compares log P.

```steps
Step 1 from the start: candidates the 0.5, a 0.4, <eos> 0.1. Keep the two best
    beams    {{the 0.5}}   {{a 0.4}}
---
Step 2, scanning beam "the": "the cat" 0.15 and "the dog" 0.15 fill the size-2 heap
    heap (min first)   the cat 0.15 | the dog 0.15
---
"the <eos>" 0.20 beats the root 0.15: heapreplace drops "the cat"
    heap (min first)   the dog 0.15 | {{the <eos> 0.20}}
---
Scanning beam "a": "a cat" 0.36 beats 0.15, replacing "the dog"; "a <eos>" 0.04 does not beat 0.20
    heap (min first)   the <eos> 0.20 | {{a cat 0.36}}
    finished: the <eos> 0.20      live: a cat
---
Step 3: one live beam gives "a cat <eos>" 0.216 and "a cat sat" 0.144; both fit in the heap
    finished: the <eos> 0.20, {{a cat <eos> 0.216}}      live: a cat sat
---
Step 4: "a cat sat <eos>" 0.144 finishes; no live beam remains, so stop
    finished: the <eos> 0.200, a cat <eos> 0.216, {{a cat sat <eos> 0.144}}
---
Rank the finished hypotheses by log P / length^alpha
    hypothesis        len   alpha 0    alpha 0.6   alpha 1
    the <eos>          2    -1.609     -1.062      -0.805
    a cat <eos>        3    {{-1.532}}     {{-0.793}}      -0.511
    a cat sat <eos>    4    -1.938     -0.844      {{-0.484}}
```

Beam search beats greedy (0.216 against 0.2), and the length penalty decides between the two "a cat" hypotheses.

## Template

```python
import heapq


def beam_search(next_logprobs, k, max_len, eos, alpha=1.0):
    """Best hypothesis under score = log P / len**alpha, keeping k live beams.

    next_logprobs(tokens) returns {token: log probability} for the next token.
    """
    beams = [(0.0, ())]                          # (cumulative log prob, tokens)
    finished = []                                # (score, log prob, tokens)
    for _ in range(max_len):
        best = []                                # min-heap holding the k best extensions
        for logp, toks in beams:
            for tok, lp in next_logprobs(toks).items():
                item = (logp + lp, toks + (tok,))
                if len(best) < k:
                    heapq.heappush(best, item)
                elif item > best[0]:
                    heapq.heapreplace(best, item)    # evict the weakest of the k
        beams = []
        for logp, toks in best:
            if toks[-1] == eos:
                finished.append((logp / len(toks) ** alpha, logp, toks))
            else:
                beams.append((logp, toks))
        if not beams:
            break
    pool = finished or [(lp / len(t) ** alpha, lp, t) for lp, t in beams]
    return max(pool)


def greedy(next_logprobs, max_len, eos):
    toks, logp = (), 0.0
    for _ in range(max_len):
        tok, lp = max(next_logprobs(toks).items(), key=lambda kv: kv[1])
        toks, logp = toks + (tok,), logp + lp
        if tok == eos:
            break
    return logp, toks
```

Tested on 150 random toy models: with k at least V^4 the result equals exhaustive search over all sequences up to length 4 for α = 0, 0.6 and 1, and with k = 1 it equals `greedy`.

## Pitfalls

- **Raw scores across lengths.** Without normalisation the search prefers stopping early; decide α on purpose and report it with results.
- **Multiplying probabilities.** Products underflow to 0.0 for long outputs, after which every hypothesis ties. Add log-probabilities.
- **Keeping finished hypotheses in the beam.** Extending a hypothesis past its end token wastes beam slots and can produce text after the end.
- **Ties.** Equal scores are broken by whatever comparison follows (here the token tuples): deterministic, but arbitrary. Fix the rule if outputs must be reproducible across implementations.
- **Assuming a wider beam is better.** More search finds higher-probability text, which for open-ended prompts is often duller text.

## Check yourself

Q: Run the template on the toy model with k = 1. What does it return, and why can it never find "a cat <eos>"?
A: "the <eos>" with probability 0.2, the same as greedy. With one beam, step 1 keeps only "the" (0.5 beats 0.4), and every later candidate extends "the", so no hypothesis starting with "a" is ever formed.

Q: Why is it safe to take each beam's own top k tokens before selecting the k best overall?
A: If a beam contributed a candidate that is not among its own k best tokens, then that beam's k better candidates would all outrank it, so the global top k would already hold at least k candidates better than it, a contradiction. Every survivor is therefore in its beam's top k, and selecting from k × k candidates gives the same answer as selecting from k × V.

Q: You are building an English-to-French translator and a story-writing assistant. Which decoder do you choose for each?
A: Beam search (with a modest k and a tuned length penalty) for translation, where the output is tightly determined by the input and the most probable output is usually a good one. Sampling with top-p or top-k for stories: maximising probability on open-ended text gives repetitive, generic prose, as the nucleus sampling paper shows.

Q: A colleague scores hypotheses with `math.prod(probs)` and sees all beams tie at 0.0 on long outputs. What is wrong and what is the fix?
A: Multiplying hundreds of probabilities below one underflows below the smallest positive float, so every score becomes 0.0 and comparisons are meaningless. Sum log-probabilities instead; length normalisation is then a division of that sum.

## Lab

- Run `beam_search` on the toy model (use the table in this card) with k = 1, 2 and 3 and α = 0 and 1. Expected: k = 1 returns "the <eos>" (P = 0.200) for both α; k = 2 and k = 3 return "a cat <eos>" (P = 0.216) with α = 0 and "a cat sat <eos>" (P = 0.144) with α = 1.
- Write an exhaustive search over all sequences up to length 4 for random models with 2 to 4 tokens, and compare it with `beam_search` at k = V^4. Expected: identical best hypotheses and scores for every model and every α.
- Add the per-beam top-k shortcut with `heapq.nlargest(k, ...)` on each beam's distribution before the global selection. Expected: identical results on all your random models, with far fewer heap operations when V is large.

> [!know]
> You now know how to run beam search with a size-k heap and decide how strongly to normalise by length.

=== primer | How do top-k and top-p sampling choose the next token efficiently? | 15 min
goal: Implement temperature, top-k and nucleus (top-p) sampling with a heap, prefix sums and binary search, and state the cost of each step for a 100,000-token vocabulary
tag: llmserve-topp | Top-k and nucleus sampling
link: Holtzman et al. 2020, nucleus sampling | https://arxiv.org/abs/1904.09751 | 15 min: §3.1 defines the nucleus as the smallest set whose probability reaches p, and §3.2 shows why one fixed k fails on both flat and peaked distributions
link: AI guide: Sampling, temperature, top-p and friends | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-sampling-temperature-top-p-and-greedy | About 14 min: The user's view: which settings to choose per use case, plus min-p and repetition penalties

> [!key]
> Sampling turns V logits into one token. Divide the logits by the **temperature** and apply a softmax, subtracting the maximum first; **top-k** keeps the k most likely tokens, found with a size-k heap or a linear-time partition; **top-p** keeps the smallest set of most likely tokens whose probabilities reach p, found by sorting, taking **prefix sums** and **binary searching** for p. The draw itself is one more binary search: take u uniform in [0, 1) and find where u × total falls among the cumulative sums.

## Intuition

Give every token raffle tickets in proportion to its probability and lay them end to end along a line one metre long. Throwing a dart at a uniformly random point on the line picks a token with exactly its probability. Temperature reshapes the tickets: below 1 the favourite's share grows, above 1 the shares even out. Top-k and top-p tear the tail off the line, the many unlikely tokens whose combined share would otherwise produce occasional nonsense, and stretch what is left back to one metre.

## How it works

### Temperature and a stable softmax

p_i = exp(z_i / T) / Σ_j exp(z_j / T). Logits can be large, and `math.exp(1000)` overflows, so subtract the largest scaled logit before exponentiating: the result is unchanged because the factor cancels, and every exponent is now at most 0. T = 0 means "always the top token" and must be special-cased as argmax, since dividing by zero is undefined.

### Top-k

Keep the k largest probabilities. Three ways:

- `heapq.nlargest(k, ids, key=...)`: one pass with a size-k heap, O(V log k).
- `numpy.argpartition`: a selection algorithm (introselect) that places the k largest in front in O(V) on average, unordered.
- Sorting everything: O(V log V), simplest when you need the order anyway.

### Top-p (the nucleus)

The nucleus is the smallest set whose total probability is at least p (Holtzman et al. 2020, §3.1). Sort ids by probability, descending. Among all sets of a given size, the top prefix of that order has the most mass, so the smallest set reaching p is a prefix: compute prefix sums `cum` and the answer is the first index where `cum[i] >= p`. Because probabilities are non-negative, `cum` is sorted, so `bisect_left(cum, p)` finds that index in O(log V). Keep `m = index + 1` tokens. The nucleus adapts: when the model is confident it holds one or two tokens; when unsure, hundreds.

### Drawing: inverse-CDF sampling

Build prefix sums over the kept ids, take `target = u * cum[-1]` (this renormalises without dividing every probability) and return the id at `bisect_right(cum, target)`: the first prefix that exceeds the target. Each id owns an interval of the line as long as its probability.

### Order of operations

Hugging Face Transformers (v5.22) applies temperature, then top-k, then top-p, then min-p; each stage works on the survivors of the previous one, renormalised. Its top-p sorts the whole vocabulary, takes the cumulative softmax and masks the tail. The template below follows the same order.

## Cost

For V = 128,000 and k = 50:

| Step | Method | Cost |
|---|---|---|
| Temperature and softmax | one pass for the max, one for the sum | O(V) |
| Top-k | size-k heap | O(V log k) |
| Top-k | `argpartition` | O(V) average |
| Top-p over the whole vocabulary | sort, prefix sums, bisect | O(V log V) + O(V) + O(log V) |
| Top-p after top-k | sort only the k survivors | O(k log k) |
| Draw | prefix sums, bisect | O(m) + O(log m) for m kept ids |

Running top-k first shrinks top-p's sort from V to k items. If you need many draws from one distribution (several samples of one prompt), build the prefix sums once and pay O(log m) per draw.

## When to use it

Sample when you want varied, natural text: chat, writing, brainstorming, several candidate answers to vote on. Top-p adapts to the model's confidence, which a fixed k cannot (Holtzman et al. §3.2: a flat distribution needs a large k, a peaked one a small k). Top-k is the cheaper cut and a guard against a long tail when the distribution is flat. Do not sample when you need exactly reproducible output, such as extraction into fixed fields; use greedy decoding there, and remember the AI guide's determinism lesson: even temperature 0 is not bit-reproducible on a busy server.

## Worked trace

Six tokens: sunny, cloudy, rainy, windy, foggy, purple with logits 3.0, 2.2, 1.5, 1.0, 0.2, −2.0. Temperature 0.7, p = 0.9, u = 0.73.

```steps
Divide by T = 0.7, subtract the max (3.0 / 0.7), exponentiate and normalise
    token   sunny  cloudy  rainy  windy  foggy  purple
    prob    0.661  0.211   0.078  0.038  0.012  0.001
---
Sort ids by probability, descending (already in order here), and take prefix sums
    sorted  sunny  cloudy  rainy  windy  foggy  purple
    cum     0.661  0.872   0.949  0.987  0.999  1.000
---
bisect_left(cum, 0.9) = 2: the first prefix reaching 0.9 ends at index 2, so keep m = 3 tokens
    cum     0.661  0.872  {{0.949}}  0.987  0.999  1.000
    nucleus {{sunny  cloudy  rainy}}   mass 0.949
---
Draw: prefix sums over the nucleus; target = u x total = 0.73 x 0.949 = 0.693
    cum     0.661  0.872  0.949
    target  0.693
---
bisect_right(cum, 0.693) = 1: the first prefix exceeding the target is cloudy's
    cum     0.661 {{0.872}} 0.949
    sample  {{cloudy}}
```

Every u below 0.661 / 0.949 = 0.697 gives sunny, u up to 0.919 gives cloudy, and the rest gives rainy: each token's share of the nucleus.

## Template

```python
import bisect
import heapq
import itertools
import math


def softmax(logits, temperature=1.0):
    """Probabilities from logits divided by temperature (> 0)."""
    z = [x / temperature for x in logits]
    m = max(z)                                   # subtract the max: exp never overflows
    e = [math.exp(x - m) for x in z]
    s = sum(e)
    return [x / s for x in e]


def top_k(probs, k):
    """Ids of the k most likely tokens: O(V log k) with a size-k heap."""
    return heapq.nlargest(k, range(len(probs)), key=probs.__getitem__)


def top_p(probs, p):
    """Smallest set of most likely ids whose mass reaches p (the nucleus)."""
    order = sorted(range(len(probs)), key=probs.__getitem__, reverse=True)
    cum = list(itertools.accumulate(probs[i] for i in order))
    m = bisect.bisect_left(cum, p) + 1           # first prefix whose sum is >= p
    return order[:min(m, len(order))]


def draw(probs, ids, u):
    """Inverse-CDF draw among ids, renormalised; u is uniform in [0, 1)."""
    cum = list(itertools.accumulate(probs[i] for i in ids))
    j = bisect.bisect_right(cum, u * cum[-1])
    return ids[min(j, len(ids) - 1)]             # guard against rounding at u near 1


def sample(logits, u, temperature=1.0, k=None, p=None):
    """Temperature, then top-k, then top-p on the renormalised survivors, then draw."""
    probs = softmax(logits, temperature)
    ids = top_k(probs, k) if k else list(range(len(probs)))
    if p is not None:
        total = sum(probs[i] for i in ids)
        keep = top_p([probs[i] / total for i in ids], p)
        ids = [ids[j] for j in keep]
    return draw(probs, ids, u)
```

In real use, pass `u = random.random()`. Tested: `top_p` against brute force over all subsets (3,000 random cases with V up to 7), `draw` against exact shares on a grid of 20,000 values of u, and `sample` against a NumPy version built on `argpartition`, `cumsum` and `searchsorted` (3,000 random cases).

## Pitfalls

- **Overflow.** `exp` of a large logit overflows; always subtract the maximum first.
- **Temperature 0.** Dividing by zero; treat it as argmax.
- **Cutting unsorted probabilities.** Prefix sums only find the nucleus after sorting by probability.
- **Losing the ids.** Sorting probabilities without carrying their ids along (sort ids by key, as the template does) returns positions in the sorted list, not tokens.
- **Ties at the boundary.** If two tokens share the boundary probability, the nucleus is not unique; implementations keep whichever their sort puts first.
- **Rounding at u close to 1.** `u * cum[-1]` can round up to `cum[-1]`, and `bisect_right` then returns one past the end; clamp the index.

## Check yourself

Q: At T = 1.0 the six probabilities are 0.533, 0.240, 0.119, 0.072, 0.032 and 0.004. Which tokens does top-p = 0.9 keep?
A: The prefix sums are 0.533, 0.773, 0.892, 0.964, ...; `bisect_left(cum, 0.9)` is 3, so four tokens: sunny, cloudy, rainy and windy (0.892 after three tokens is still short of 0.9).

Q: Why does the first prefix of the sorted order that reaches p give the smallest possible set?
A: For any size s, the s most likely tokens have at least as much mass as any other set of s tokens. If the first prefix reaching p has m tokens, the prefix of m − 1 tokens falls short of p, so every set of m − 1 or fewer tokens falls short too. No smaller set can reach p.

Q: With V = 128,000 and k = 50, how would you compute top-k in pure Python and in NumPy?
A: In pure Python, `heapq.nlargest` with a size-50 heap: O(V log k), one pass, no full sort. In NumPy, `argpartition` selects the 50 largest in O(V) in compiled code (then sort those 50 if you need them ordered). Both avoid the O(V log V) full sort.

Q: A colleague writes `cum = list(accumulate(sorted(probs, reverse=True)))` and returns `bisect_right(cum, u)` as the sampled token id. Name two bugs.
A: The index refers to a position in the sorted list, not a token id, because the ids were not sorted along with the probabilities. And `u` was not scaled by the kept mass, so after truncation (where `cum[-1]` is below 1) values of u above it fall off the end.

## Lab

- Compute the nucleus for p = 0.9 at temperatures 0.3, 0.7, 1.0 and 2.0 for the six-token example. Expected: 1, 3, 4 and 5 tokens (sunny alone at 0.3; foggy joins at 2.0).
- Call `sample(logits, u, temperature=1.0, p=0.9)` for u = 0.05, 0.5 and 0.95. Expected: sunny, sunny, windy.
- Call `sample(logits, 0.73, temperature=0.7, k=3, p=0.9)` and explain the result. Expected: sunny; after top-3 the survivors renormalise to 0.696, 0.222 and 0.082, so the nucleus is only sunny and cloudy, and the target 0.73 × 0.872 = 0.637 falls in sunny's interval.
- Write a brute-force nucleus (try every subset, smallest size first) and compare it with `top_p` on random distributions of up to 7 tokens. Expected: the same size and the same mass every time.

> [!know]
> You now know how to apply temperature, top-k and top-p with heaps, prefix sums and binary search, and what each step costs.

=== primer | How does continuous batching decide what runs at each step? | 16 min
goal: Simulate an iteration-level scheduler with a waiting queue, a per-step token budget, a KV block limit and preemption by recomputation, and relate each rule to vLLM's scheduler
tag: llmserve-sched | Iteration-level scheduling with preemption
link: Yu et al. 2022, Orca (OSDI) | https://www.usenix.org/conference/osdi22/presentation/yu | 20 min in the PDF linked on the page: §3 'S1: Iteration-level scheduling', then §4.2 and Algorithm 1; note that Orca reserves each request's maximum KV space at admission, which paging later removed
link: AI guide: Continuous batching | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-continuous-batching | About 12 min: The user's side: chunked prefill, load-testing a server and tuning max-num-batched-tokens

> [!key]
> A server runs the model one step at a time over a batch, and **continuous batching** (Orca's iteration-level scheduling) rebuilds that batch at every step. Underneath are four structures: a FIFO **waiting queue**, a **running list** in admission order, a per-step **token budget** shared by decode tokens and prefill chunks, and a pool of KV **blocks**. Running requests are planned first, then waiting ones are admitted in order while budget and blocks last. When a running request cannot get a block, the newest running request is **preempted**: its blocks are freed and it returns to the front of the queue, to be recomputed later.

## Intuition

A city bus does not wait at the depot until forty passengers have booked and then drive them all to the end of the line. It stops at every stop: whoever has arrived gets off, whoever is waiting gets on if there is a seat. Static batching is the depot bus: a batch runs until its slowest member finishes, and early finishers leave empty seats. Continuous batching is the city bus, re-planned at every step. The seats are KV memory and the bus's speed limit is the per-step token budget.

## How it works

### One counter per request

vLLM's V1 scheduler has no separate prefill and decode phases. Each request has a number of tokens whose KV is already computed, and each step tries to let that number catch up with the request's current length (prompt plus output so far). A new request needs its whole prompt computed, possibly in several chunks (chunked prefill); a decoding request needs one token (the one it just produced). When a request's computed count reaches its length, the step emits its next token.

### The step loop

1. **Running requests first**, in admission order: give each `min(need, budget left)` tokens, growing its block table if the new tokens cross a block boundary.
2. **Out of blocks?** Preempt the newest running request: free all its blocks, reset its computed count to zero, put it back at the front of the waiting queue. Repeat until the current request fits, or until the request preempted is the current one.
3. **Admit waiting requests**, first come first served, while there is budget, a free sequence slot and blocks for the first chunk. Stop at the first request that does not fit, so later arrivals cannot overtake it. If this step preempted anything, admit nothing.
4. **Run the step**, emit tokens, and retire finished requests, returning their blocks.

### Why newest first, all or nothing

The PagedAttention paper serves requests first come first served and preempts the latest arrivals first, so the earliest requests always make progress. It evicts all of a sequence's blocks or none, because a sequence needs all of its blocks at every step. Recovery is by swapping blocks to CPU memory or by recomputation; recomputation is cheaper than it sounds, because the prompt and the tokens already generated are reprocessed as one parallel prefill. vLLM's current engine recomputes, and its V1 scheduler admits no waiting request in a step that preempted, which avoids thrashing.

### Priorities and the alternative

vLLM also offers priority scheduling: the waiting queue becomes a heap (Python `heapq`) and the victim is the running request with the largest (priority, arrival time). Orca, the original iteration-level scheduler, avoided preemption by reserving each request's maximum KV size when it was first scheduled. That is safe but over-reserves, the waste PagedAttention removed.

## Cost

Per step the scheduler touches each running request once and each admitted request once: O(R + A), with O(1) deque operations, or O(log W) per heap operation in priority mode. It runs on the CPU between GPU steps of a few milliseconds to tens of milliseconds, so it must stay this simple.

The payoff, from a seeded simulation of 200 requests (prompts of 20 to 200 tokens, outputs of 5 to 120, at most 16 running):

| Scheduler | Mean latency (steps) | Makespan (steps) |
|---|---|---|
| Static batches of 16 (whole prompt in one step) | 670.4 | 1,572 |
| Continuous, unlimited budget and memory | 320.1 | 901 |
| Continuous, 512 tokens per step, 120 blocks of 16 | 487.5 (88 preemptions) | 1,213 |

In the static run only 52% of sequence slots produced a token. A preemption costs a recomputation of P + G tokens (prompt plus generated) and, more importantly, latency for the victim; frequent preemptions are a sign the KV pool is too small for the admitted load.

## When to use it

| Policy | What it buys | What it costs |
|---|---|---|
| Static batching | simplest; fine for offline jobs with equal lengths | idle slots, long queueing |
| Iteration-level, reserve maximum KV at admission (Orca) | never preempts | admits far fewer requests |
| Iteration-level with paged KV and preemption (vLLM) | high utilisation and large batches | recomputation and latency spikes under memory pressure |
| Priority queue instead of FIFO | latency classes (interactive versus batch) | starvation risk unless priorities age |

Use the continuous scheme for any online service with varied lengths. Tune two knobs: the token budget (small protects the latency of streams already running; large finishes prompts sooner) and the KV pool (too small and you preempt constantly).

## Worked trace

Block size 2 tokens, 5 blocks, at most 3 running, budget 6 tokens per step. Requests (arrival step, prompt tokens, output tokens): A (0, 5, 3), B (0, 3, 4), C (1, 4, 3), D (2, 2, 2). Blocks are counted while the step runs.

```steps
Step 0: admit A with its whole prompt (5 tokens, 3 blocks) and B with a 1-token chunk; A emits its first token
    plan     {{A:5  B:1}}          blocks 4/5
    running  A B                   waiting  -
---
Step 1: A decodes 1, B finishes its prompt (2); C arrived but its 3-token chunk needs 2 blocks and none is free
    plan     A:1  B:2              blocks {{5/5}}
    running  A B                   waiting  {{C}}
---
Step 2: A needs a 4th block: preempt the newest running request, B, and requeue it at the front. A then finishes
    plan     A:1                   {{preempt B}}, finish A
    running  -                     waiting  {{B}} C D
---
Step 3: no admission was allowed last step; now B is recomputed (prompt 3 + 1 generated = 4 tokens) and C starts
    plan     {{B:4  C:2}}          blocks 3/5
    running  B C                   waiting  D
---
Step 4: B decodes, C finishes its prompt; D waits for blocks
    plan     B:1  C:2              blocks 5/5
    running  B C                   waiting  D
---
Step 5: C needs a 3rd block and is itself the newest: C preempts itself. B emits its 4th token and finishes
    plan     B:1                   {{preempt C}}, finish B
    running  -                     waiting  C D
---
Step 6: C is recomputed (4 + 1 = 5 tokens) and D gets the last budget token
    plan     {{C:5  D:1}}          blocks 4/5
    running  C D                   waiting  -
---
Steps 7 and 8: C finishes at step 7, D at step 8
    finish   A:2  B:5  C:{{7}}  D:{{8}}
```

With unlimited memory and budget every request would finish at arrival + output − 1: A 2, B 3, C 3, D 3. Memory pressure and the two preemptions cost B 2 steps and C 4.

## Template

```python
import math
from collections import deque


class Request:
    def __init__(self, rid, arrival, prompt, output):
        self.rid, self.arrival, self.prompt, self.output = rid, arrival, prompt, output
        self.computed = 0        # tokens whose K and V are in the cache
        self.generated = 0       # output tokens emitted so far
        self.blocks = 0          # KV blocks held
        self.finish = None

    def need(self):
        """Tokens to compute before the next output token can be emitted."""
        return self.prompt + self.generated - self.computed


def serve(requests, max_seqs, budget, num_blocks, block_size, log=None):
    """Iteration-level scheduling: every step admits, runs and retires requests."""
    arrivals = deque(sorted(requests, key=lambda r: (r.arrival, r.rid)))
    waiting, running = deque(), []
    free, step = num_blocks, 0

    def grow(r, n):              # blocks so r can hold computed + n tokens; False if short
        nonlocal free
        extra = math.ceil((r.computed + n) / block_size) - r.blocks
        if extra > free:
            return False
        free -= extra
        r.blocks += extra
        return True

    def release(r):
        nonlocal free
        free += r.blocks
        r.blocks = 0

    while arrivals or waiting or running:
        while arrivals and arrivals[0].arrival <= step:
            waiting.append(arrivals.popleft())
        left, plan, events, preempted = budget, {}, [], False
        i = 0
        while i < len(running) and left > 0:           # 1. running requests first
            r = running[i]
            n = min(r.need(), left)
            while not grow(r, n):                       # out of blocks: preempt the newest
                victim = running.pop()                  # not yet planned this step
                release(victim)
                victim.computed = 0                     # recompute its KV later
                waiting.appendleft(victim)
                events.append(f"preempt {victim.rid}")
                preempted = True
                if victim is r:
                    break
            if r in running:
                plan[r.rid] = n
                left -= n
                i += 1
        while not preempted and waiting and left > 0 and len(running) < max_seqs:  # 2. admit, FCFS
            r = waiting[0]
            n = min(r.need(), left)
            if not grow(r, n):
                break
            running.append(waiting.popleft())
            plan[r.rid] = n
            left -= n
        held = num_blocks - free
        for r in list(running):                         # 3. run one step, retire finished
            if r.rid not in plan:
                continue
            r.computed += plan[r.rid]
            if r.computed == r.prompt + r.generated:
                r.generated += 1
                if r.generated == r.output:
                    r.finish = step
                    running.remove(r)
                    release(r)
                    events.append(f"finish {r.rid}")
        if log is not None:
            log.append((step, plan, [x.rid for x in waiting], [x.rid for x in running], held, events))
        step += 1
    return requests
```

It assumes every single request fits in the pool on its own (real servers reject longer requests up front). Tested on 400 random workloads: the budget, the sequence cap and the pool are never exceeded, every request emits exactly its output length, and with unlimited resources each request finishes at arrival + output − 1.

## Pitfalls

- **Admitting before running.** If new prompts take the budget and blocks first, streams already running stall or get preempted; plan running requests first, as vLLM does.
- **Forgetting the reset.** A preempted request's KV is gone; if its computed count is not reset to zero, later steps read freed blocks.
- **Preempting the request you are planning.** The victim can be the current request itself; handle that case or the loop never ends.
- **Thrashing.** Admitting new work in the step that just preempted refills the memory you freed and preempts again next step.
- **Head-of-line blocking.** Strict first come first served stops at the first request that does not fit, even if a smaller one behind it would. That is the price of fairness; skipping ahead raises utilisation but can starve large requests.
- **Starvation under priorities.** Low-priority requests can wait forever unless priority ages with waiting time (SGLang, for example, offers a highest-response-ratio-next policy).

## Check yourself

Q: In step 1 of the trace a sequence slot and 3 tokens of budget were free. Why was C not admitted?
A: Admission needs blocks for the first chunk: 3 tokens at block size 2 is 2 blocks, and all 5 blocks were held by A and B. The scheduler stops at the first waiting request that does not fit.

Q: Why does the scheduler preempt the newest running request rather than the oldest?
A: Serving in arrival order means the earliest requests must keep making progress, so the latest arrivals give way first; otherwise a stream of new requests could starve old ones. The newest request has also usually done the least work, so recomputing it is cheapest.

Q: Rerun the trace with 8 blocks instead of 5. What changes?
A: No preemption happens. C is admitted at step 1 alongside A and B, D joins at step 3, and the finish steps become A 2, B 4, C 4, D 4.

Q: A scheduler admits waiting requests before planning the running ones. What do users see under load?
A: Long new prompts take the token budget and the free blocks, so requests that are already streaming get fewer tokens per step or are preempted: output stalls mid-sentence and inter-token latency spikes. Planning running requests first protects them.

## Lab

- Rerun the trace with 8 blocks. Expected: no preemptions; finish steps A 2, B 4, C 4, D 4.
- Rerun it with 5 blocks and a budget of 3 tokens per step. Expected: preemptions of B at step 3 and C at step 7; finish steps A 3, B 7, C 10, D 11.
- Rerun it with unlimited budget, blocks and slots. Expected: A 2, B 3, C 3, D 3, each equal to arrival + output − 1.
- Generate 200 requests with `rng = random.Random(2026)`, drawing for each request in this order: the arrival gap `rng.choice([0, 0, 1, 1, 2, 3])` added to the previous arrival, the prompt `rng.randint(20, 200)` and the output `rng.randint(5, 120)`. Write a static-batching simulator (when idle, take up to 16 requests that have arrived; the whole prompt runs in one step; a batch lasts as long as its longest output) and compare mean latency (finish − arrival + 1) with `serve(max_seqs=16, budget=10**9, num_blocks=10**9, block_size=16)`. Expected: 670.4 steps static against 320.1 continuous, and makespans of 1,572 against 901 steps.

> [!know]
> You now know how an LLM server plans every step from a waiting queue, a token budget and a block pool, and when and whom it preempts.

=== lab | Measure prefix-cache reuse on simulated chat traffic | 50 min
goal: Replay multi-turn chat traffic that shares system prompts through your radix-tree cache, and measure how capacity, eviction granularity and scheduling order change token reuse
link: Zheng et al. 2024, SGLang | https://arxiv.org/abs/2312.07104 | About 5 min: §3 'Cache-aware scheduling' defines the hit rate you measure here and the longest-shared-prefix-first order you test in step 5

You will build the workload, replay it through the `RadixCache` from the radix-tree card, and compare it with a vLLM-style block cache and with two scheduling orders. Everything is seeded, so your numbers should match the ones below exactly if you copy the generator.

## Steps

1. Put `Node` and `RadixCache` from the radix-tree card in `prefix_lab.py`.
2. Add a workload generator: four apps with system prompts of 300, 500, 800 and 1,200 random token ids, 120 conversations of 1 to 6 turns (each user turn 20 to 80 tokens, each reply 50 to 200), interleaved at random while keeping each conversation's turns in order:

```python
import random
from collections import OrderedDict


def chat_workload(seed=0, apps=(300, 500, 800, 1200), conversations=120, vocab=50_000):
    """Requests (prompt, reply) from multi-turn chats that share per-app system prompts."""
    rng = random.Random(seed)
    systems = [[rng.randrange(vocab) for _ in range(n)] for n in apps]
    weights = [8, 4, 2, 1]                                # some apps are busier than others
    convs = []
    for _ in range(conversations):
        history = list(rng.choices(systems, weights)[0])
        turns = []
        for _ in range(rng.randint(1, 6)):
            history += [rng.randrange(vocab) for _ in range(rng.randint(20, 80))]   # user turn
            reply = [rng.randrange(vocab) for _ in range(rng.randint(50, 200))]
            turns.append((list(history), reply))
            history += reply
        convs.append(turns)
    stream, live = [], [c[:] for c in convs]              # interleave, keeping turn order
    while live:
        c = rng.choice(live)
        stream.append(c.pop(0))
        if not c:
            live.remove(c)
    return stream
```

3. Replay the stream. For each request, count the matched prompt tokens, insert prompt plus reply, then evict down to the capacity while the current request's node is locked. The hit rate is reused prompt tokens divided by prompt tokens (SGLang's definition). Run capacities 2,000, 5,000, 10,000, 20,000, 50,000 and unlimited (`10**9`):

```python
def replay(stream, capacity):
    cache = RadixCache()
    hit = total = 0
    for prompt, reply in stream:
        h, _ = cache.match(prompt)
        hit += h
        total += len(prompt)
        _, node = cache.insert(prompt + reply)
        if cache.size > capacity:
            cache.lock(node, +1)                          # never evict the running request
            cache.evict(cache.size - capacity)
            cache.lock(node, -1)
    return hit / total
```

4. Implement the vLLM-style alternative with B = 16: key each full block by (parent key, block tokens), look blocks up until the first miss, and keep an `OrderedDict` as an LRU of blocks. Touch a sequence's blocks from tail to head so that heads stay most recent (vLLM frees a request's blocks in reverse order for the same reason):

```python
def replay_blocks(stream, capacity, B=16):
    """vLLM-style: chained keys of full blocks, LRU over blocks."""
    lru = OrderedDict()
    hit = total = 0
    for prompt, reply in stream:
        key, n = None, 0
        for i in range(0, len(prompt) - B + 1, B):
            key = (key, tuple(prompt[i:i + B]))
            if key not in lru:
                break
            n += B
        hit += n
        total += len(prompt)
        seq, key, keys = prompt + reply, None, []
        for i in range(0, len(seq) - B + 1, B):
            key = (key, tuple(seq[i:i + B]))
            keys.append(key)
        for k in reversed(keys):                          # tail first, so heads stay hotter
            lru[k] = True
            lru.move_to_end(k)
        while len(lru) * B > capacity:
            lru.popitem(last=False)
    return hit / total
```

5. Test scheduling order. Build a batch of 200 single-turn requests from 8 few-shot prompts of 600 tokens (25 questions of 40 tokens each, shuffled), all waiting at once. Serve them first in arrival order (FCFS), then always picking the waiting request with the longest cached prefix (longest prefix match, as SGLang's `lpm` policy does), at capacities 1,500, 3,000 and 6,000:

```python
def few_shot_batch(seed=1, apps=8, per_app=25, shot_len=600, q_len=40, vocab=50_000):
    rng = random.Random(seed)
    shots = [[rng.randrange(vocab) for _ in range(shot_len)] for _ in range(apps)]
    reqs = [(shots[a] + [rng.randrange(vocab) for _ in range(q_len)], [rng.randrange(vocab) for _ in range(30)])
            for a in range(apps) for _ in range(per_app)]
    rng.shuffle(reqs)
    return reqs


def replay_batch(reqs, capacity, policy):
    cache = RadixCache()
    waiting = list(reqs)
    hit = total = 0
    while waiting:
        if policy == "lpm":
            j = max(range(len(waiting)), key=lambda i: cache.match(waiting[i][0])[0])
        else:
            j = 0
        prompt, reply = waiting.pop(j)
        h, _ = cache.match(prompt)
        hit += h
        total += len(prompt)
        _, node = cache.insert(prompt + reply)
        if cache.size > capacity:
            cache.lock(node, +1)
            cache.evict(cache.size - capacity)
            cache.lock(node, -1)
    return hit / total
```

6. Explain each result in two sentences in your notes: what limits reuse, and which data-structure choice causes it.

## What you should see

The stream has 388 requests and 318,523 prompt tokens. The whole run takes a few seconds.

| Capacity (tokens) | Radix tree | Blocks of 16 |
|---|---|---|
| 2,000 | 28.2% | 32.8% |
| 5,000 | 50.5% | 51.9% |
| 10,000 | 68.5% | 67.9% |
| 20,000 | 80.9% | 80.2% |
| 50,000 | 91.7% | 90.7% |
| unlimited | 93.0% | 92.1% |

- **The ceiling is 93%.** Even an unlimited cache must compute every system prompt once and every new user turn, which is the remaining 7%.
- **Token granularity wins when memory is plentiful.** The radix tree also reuses the partial last block of each prefix, so it leads by about one point at 50,000 and above.
- **Eviction granularity wins when memory is tight.** At 2,000 tokens the block cache is ahead: the radix tree evicts whole leaves, often a long conversation history at once, while block LRU trims tails 16 tokens at a time and keeps the hot heads.
- **Scheduling order dominates under pressure.** With 1,500, 3,000 and 6,000 tokens of cache, FCFS reaches 22.0%, 38.4% and 84.4%, while longest prefix match reaches 90.0% each time. That is the best possible here: each app's 600-token prefix must be computed once and every 40-token question is new, so at most 8 × 24 × 600 = 115,200 of the 200 × 640 = 128,000 prompt tokens can be reused. Grouping requests that share a prefix is the depth-first order of SGLang's Theorem 3.1.
