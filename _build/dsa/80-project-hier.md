---
key: projecthier
name: Build a prefix directory
stage: hier
summary: Index names in a trie and return deterministic prefix completions.
why: A trie makes the distinction between shared path structure and stored values observable.
outcomes:
- Implement trie insertion, lookup and ordered prefix enumeration.
- Account for prefix traversal and output-sensitive cost.
cues:
- Many keys share prefixes.
- Results must be limited and ordered.
traps:
- A key that is also a prefix is not marked as a complete key.
- Enumeration visits children in arbitrary order.
---

=== build | Trie-backed name directory | 6-8 h
goal: Build a case-sensitive directory with exact lookup and lexicographic autocomplete.
link: Trie operations | https://en.wikipedia.org/wiki/Trie#Operations | About 5 min: Review path traversal and terminal markers.
link: Tree depth-first traversal | https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search | About 5 min: Use traversal to enumerate descendants.

## The brief
Create an in-memory name index suitable for a command-line contact picker. Store unique, nonempty lowercase ASCII names; this keeps ordering and validation explicit rather than implying full Unicode support.

## Spec
Expose `insert(name)`, `contains(name)` and `complete(prefix, limit)`. Duplicate insertions are no-ops; invalid names, invalid prefixes and negative limits are rejected. The empty prefix is valid and selects the entire directory. Completion returns at most `limit` unique names in lexicographic order, including the prefix itself if it is a stored name; limit zero returns an empty list. Use terminal flags and child maps; traverse child characters in sorted order. Use an iterative traversal so a long valid name does not depend on recursion depth.

Analyse insertion and lookup in the key length, and completion in prefix length plus visited subtree and output characters; sorting child keys has a cost, bounded here by the fixed alphabet. Memory is proportional to trie nodes plus stored edges.

## Milestones
1. **1-2 h:** Specify validation and implement insertion and exact lookup.
2. **1-2 h:** Add iterative, ordered prefix enumeration and limit handling.
3. **1-2 h:** Compare against filtering a set and add boundary and long-key tests.
4. **1-2 h:** Benchmark shared-prefix and unrelated-key datasets; report node counts.

## Done when
- Insert `an`, `ant`, `and`, `bee`, `an`; `complete('an', 2)` returns `['an', 'and']` and `contains('a')` is false.
- Empty prefix, missing prefix, zero limit and a 2,000-character name behave as specified; invalid input fails.
- At least 200 seeded dictionaries and prefixes match `sorted(name for name in names if name.startswith(prefix))[:limit]`.
- Benchmark 1,000, 10,000 and 50,000 distinct names in both shared-prefix and varied-prefix datasets. Report build time, node count, and median time for 100 fixed queries; compare results with the set-filter oracle.
- Explain why returning many long names can dominate query time even when finding the prefix is cheap.

## Stretch goals
- Add deletion and prune nodes only when they have no children and are not terminal.
- Compare trie memory and query latency with sorted keys plus binary-search bounds.

## Hints
- [Trie operations](https://en.wikipedia.org/wiki/Trie#Operations) distinguish terminal keys from internal prefixes.
- A [depth-first traversal](https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search) can enumerate a prefix subtree without scanning unrelated branches.
