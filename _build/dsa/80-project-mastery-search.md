---
key: projectmasterysearch
name: Capstone local search service
stage: mastery
summary: Combine token indexing, ranked retrieval and a bounded cache with end-to-end evaluation.
why: Integrating structures exposes trade-offs that isolated exercises can conceal.
outcomes:
- Compose postings, ranking and cache invalidation.
- Evaluate exact results and workload-sensitive cache behaviour.
cues:
- A stable collection receives repeated search requests.
- Search results need ordering and deterministic ties.
traps:
- A cached answer survives a document replacement.
- A timing improvement is reported without checking ranked results.
---

=== build | Capstone: searchable field notes | 8-12 h
goal: Build a local ranked document search pipeline with an LRU query cache.
link: Keyword search and BM25 | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-keyword-search-and-bm25 | Contrast a production ranking family with the deliberately simpler score here.
link: OrderedDict | https://docs.python.org/3/library/collections.html#ordereddict-objects | Review ordered operations for a bounded LRU cache.

## The brief
Build a single-process field-note search tool. Ingest and replace documents, answer ranked AND queries, and expose counters that explain whether the cache helped. Do not label the toy score BM25.

## Spec
Each document has a unique nonnegative integer ID and ASCII text. Tokenise documents and queries as maximal ASCII-letter runs lowercased. Maintain term-to-document postings with term frequencies. A query matches documents containing all distinct terms and scores each as the sum of those terms' frequencies. Return the top `k` by descending score, then ascending ID; `k` is positive and an empty tokenised query returns no results. Repeated query terms count once.

Provide `put(id,text)` to insert or replace a document, removing old postings before adding new ones. Cache result lists under `(sorted unique terms, k)` in a fixed-capacity LRU; capacity zero disables caching. Every successful put clears the cache. Record hits, misses and evictions. Keep an independent full-scan oracle and copy returned cached lists so callers cannot mutate the cache.

## Milestones
1. **1-2 h:** Implement tokenisation, full-scan ranking and hand-worked cases.
2. **1-2 h:** Build postings with frequencies and intersect candidates.
3. **1-2 h:** Implement replacement, remove empty postings and test index consistency.
4. **1-2 h:** Add LRU caching, invalidation and exposed counters.
5. **1-2 h:** Run seeded end-to-end differential tests and adversarial cache traces.
6. **1-2 h:** Benchmark cold and warm queries and report correctness and cost.

## Done when
- With `1: "red red fox"`, `2: "red fox fox"`, `3: "red"`, query `red fox` with `k=2` returns `[(1,3),(2,3)]`. Replacing document 1 with `blue` makes the next result `[(2,3)]`, even if the earlier result was cached.
- Capacity 2, requests A, B, A, C, B without writes produce one hit, four misses and two evictions; a capacity-zero cache stores nothing.
- At least 100 seeded sequences of 200 puts and queries match a scan-and-sort oracle; returned IDs, scores, order and limits match exactly.
- Benchmark 1,000, 10,000 and 50,000 fixed-seed documents with 1,000 queries, comparing a repeated hot set against a mostly unique query stream. Report build time, five-run median query times, hit/miss/eviction counts and posting visits; reset cache and counters for each trial.
- Explain index space in term-document pairs, query cost in postings visited plus ranking candidates, and cache space in stored result sizes. Include invalidation cost and workload-dependent hit rate.

## Stretch goals
- Add deletions and test invalidation for deleted documents.
- Replace the toy score with a documented ranked formula, retaining the scan oracle.

## Hints
- [Keyword search and BM25](https://learningcurie.github.io/code-study-tracker/ai.html#l-c-keyword-search-and-bm25) provides context without requiring BM25 here.
- [OrderedDict operations](https://docs.python.org/3/library/collections.html#ordereddict-objects) support moving a hit to the most-recent position and evicting the oldest.
