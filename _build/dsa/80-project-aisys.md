---
key: projectaisys
name: Build a vector retrieval evaluator
stage: aisys
summary: Compare exact nearest neighbours with a simple random-hyperplane candidate index.
why: Approximate retrieval must be judged by both answer quality and resource use, not latency alone.
outcomes:
- Compute exact neighbours and recall at a fixed k.
- Evaluate an approximate candidate filter without presenting it as HNSW.
cues:
- Similarity queries repeat over a fixed vector collection.
- A faster approximate answer may miss true neighbours.
traps:
- Evaluating recall against the approximate method itself.
- Treating missing candidates as successful matches.
---

=== build | Approximate vector retrieval lab | 6-8 h
goal: Measure recall and distance computations for a simple approximate index against exact search.
link: Nearest neighbour algorithm choice | https://scikit-learn.org/stable/modules/neighbors.html#choice-of-nearest-neighbors-algorithm | Relate dimensions and dataset size to search strategy.
link: FAISS IndexLSH | https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#indexlsh-and-its-relationship-with-cell-probe-methods | Compare the idea of binary signatures with this toy candidate filter.

## The brief
Build a reproducible experiment on synthetic vectors. It demonstrates an approximation trade-off, not a production embedding service and not an implementation of FAISS or HNSW.

## Spec
Use unique integer IDs and finite, nonzero vectors of fixed dimension. Normalise vectors and queries, then rank by descending cosine similarity, breaking ties by ascending ID. Reject zero vectors, mismatched dimensions and non-finite values. Exact search scores every vector.

For the approximate method generate a positive number `b` of seeded random hyperplanes, encode each vector by the signs of its dot products (zero counts as nonnegative), and score only vectors in the query's exact signature bucket. Require positive `k` and return up to `k` results; a sparse bucket may return fewer or none. Define recall@k as the number of returned IDs in the exact top `min(k,n)` divided by `min(k,n)`; use nonempty collections for recall experiments. Count exact similarity evaluations separately from signature dot products.

## Milestones
1. **1-2 h:** Implement validation, cosine ranking and a small hand-computed exact test.
2. **1-2 h:** Implement seeded signatures, bucket lookup and deterministic ordering.
3. **1-2 h:** Test recall, empty buckets, ties and invalid inputs.
4. **1-2 h:** Compare parameter settings and report recall, time and memory proxies.

## Done when
- For vectors `1:(1,0)`, `2:(0,1)`, `3:(-1,0)` and query `(1,0)`, exact top 2 is `[1,2]`; identical scores break by ID.
- Recall is 1 when the returned top-k IDs match exact, and 0 for an empty candidate set; zero and mismatched vectors fail.
- For at least 100 seeded small datasets, approximate results are exactly the exact-score ordering restricted to their candidate bucket; every candidate is a stored ID.
- Benchmark 1,000, 5,000 and 10,000 vectors of dimension 16 with 100 held-out seeded queries, `k=10` and `b=2,4,8`. Report build time, average recall@10, candidate count, signature work, distance evaluations and five-run median query time for each setting; use the same vectors and queries.
- Explain `O(n*d)` exact query scoring, signature work `O(b*d)` per query plus candidate scoring, and storage for vectors, signatures and buckets. Do not promise monotonic recall or a fixed speedup.

## Stretch goals
- Probe buckets at Hamming distance one and quantify extra candidates and recall.
- Repeat with clustered and uniformly distributed vectors and explain differences.

## Hints
- [Nearest-neighbour algorithm choice](https://scikit-learn.org/stable/modules/neighbors.html#choice-of-nearest-neighbors-algorithm) motivates comparing workload shapes.
- [FAISS IndexLSH](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#indexlsh-and-its-relationship-with-cell-probe-methods) is context for signatures, not a claim that this bucket scheme reproduces it.
