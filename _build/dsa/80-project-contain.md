---
key: projectcontain
name: Build a container-backed task queue
stage: contain
summary: Compose a queue, map and set to manage tasks without repeated scans.
why: The choice of containers determines whether the operations remain efficient as the backlog grows.
outcomes:
- Combine FIFO ordering with keyed membership.
- Account for lazy cancellation and stale queue entries.
cues:
- You need arrival order and lookup by identifier.
- Cancellation should not require scanning the queue.
traps:
- A cancelled identifier is re-added while an old queue entry remains.
- Stale entries accumulate without a bound or measurement.
---

=== build | Cancellation-safe task queue | 6-8 h
goal: Implement a FIFO task queue with keyed cancellation and measurable container costs.
link: Hash table load factor | https://en.wikipedia.org/wiki/Hash_table#Load_factor | Review expected lookup costs and resizing.
link: CPython list implementation | https://docs.python.org/3/faq/design.html#how-are-lists-implemented-in-cpython | Contrast an array-backed list with a queue.

## The brief
Create an in-memory scheduler for a single process. It should return active tasks in arrival order even when tasks are cancelled and identifiers reused. Persistence and concurrency are out of scope.

## Spec
Provide `add(id, payload)`, `cancel(id)` and `pop()`; adding an already active ID and cancelling an absent ID return false. A successful add returns true, cancellation returns true, and `pop` returns the oldest active `(id, payload)` or an explicit empty result. Every successful add receives a distinct generation token. Store `(id, generation)` in a deque and current `(generation, payload)` in a map; skip deque entries whose generation is no longer current. This prevents an old cancelled entry from returning a newly added task too early.

Specify that map operations are expected `O(1)` and deque pushes/pops `O(1)`; a single pop may skip many stale entries, though each entry is removed once. Track queue entries and active tasks separately. Provide `compact()` that rebuilds the deque in arrival order from currently valid entries; do not claim constant-time compaction.

## Milestones
1. **1-2 h:** Define return values and implement a simple list-based reference scheduler.
2. **1-2 h:** Implement deque, map and generation-token operations.
3. **1-2 h:** Add compaction, edge-case tests and seeded command-sequence comparison.
4. **1-2 h:** Measure cancellation-heavy and no-cancellation workloads and explain amortisation and memory.

## Done when
- Add `A`, add `B`, cancel `A`, add `A` again, then pop: IDs are `B`, `A`, then empty.
- Cancelling twice fails the second time; duplicate active adds fail; compaction preserves all subsequent pop results.
- At least 100 seeded command sequences of 1,000 operations match the reference, with repeated IDs and cancellations.
- Benchmark 10,000, 50,000 and 100,000 adds followed by cancellation of every other ID and draining. Report elapsed time, deque entries, active entries and stale entries skipped, with input generation excluded. Compare counts and time before and after compaction.
- Explain `O(a)` total deque removals for `a` successful adds, `O(a)` worst-case retained queue space without compaction and `O(a)` compaction in the worst case.

## Stretch goals
- Trigger compaction when physical entries exceed twice active entries plus a fixed threshold; test the policy separately.
- Add a capacity limit with explicit rejection, not silent eviction.

## Hints
- Review [hash-table load factor](https://en.wikipedia.org/wiki/Hash_table#Load_factor) before explaining expected lookup cost.
- Consider why [array-backed lists](https://docs.python.org/3/faq/design.html#how-are-lists-implemented-in-cpython) are not ideal for repeated front removal.
