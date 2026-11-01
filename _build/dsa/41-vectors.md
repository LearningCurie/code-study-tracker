---
key: vectors
name: Vector search: from brute force to HNSW and DiskANN
stage: aisys
summary: The data structures inside every vector database: exact k-NN with a heap, KD-trees and the curse of dimensionality, LSH, IVF, product quantisation, HNSW and DiskANN, and how to measure recall against latency.
why: Every RAG pipeline, recommendation feed and semantic search box ends in the same query: find the k stored vectors nearest to this one, among millions, in a few milliseconds. The AI page's embeddings module shows you how to use the indexes that answer it; this module opens them up. Each index is a classic DSA idea under pressure from high dimensions: a bounded heap, a space-partitioning tree, hashing with amplification, k-means clustering, lossy compression with lookup tables, a skip list turned into a graph searched best-first with two heaps, and an on-disk layout tuned for SSD round trips. Knowing the mechanics lets you estimate cost before you benchmark, read a FAISS index string or a pgvector setting and know what it does, and explain why recall dropped when the data grew.
outcomes:
- Compute the cost of exact k-NN, implement it with a size-k max-heap or argpartition, and say when exact search is the right answer
- Measure the curse of dimensionality and explain why KD-trees degrade to a full scan beyond about 15 dimensions
- Derive the random-hyperplane collision probability 1 - θ/π and tune LSH bits and tables with the AND-OR formula
- Build IVF and IVF-PQ indexes from k-means and product quantisation, and predict their scan cost and memory
- Implement HNSW's layered best-first search with a candidate min-heap and a result max-heap, and explain M, ef_construction and ef_search
- Explain how DiskANN serves billions of vectors from an SSD with a Vamana graph, robust pruning with α, PQ codes in RAM and beam search
- Measure recall@k against latency, find the Pareto frontier and choose an index for a workload
cues:
- "Nearest", "most similar" or "top k by cosine" over more than a few hundred thousand vectors, or under a latency budget of a few milliseconds
- Vectors with more than about 15-20 dimensions (embeddings have 384 to 3,072): space-partitioning trees will not help
- RAM is the binding constraint (billions of vectors, or many replicas): compressed codes or an SSD-resident graph
- A recall target next to a latency target ("95% recall@10 under 5 ms"): you are tuning an approximate index along a trade-off curve
traps:
- Reporting an index's speed without its recall, or measuring recall with stored vectors as queries
- Mixing metrics: inner product, cosine and L2 rank vectors identically only when every vector has unit length
- Assuming nprobe / nlist is the fraction scanned: unequal list sizes make it larger
- Applying α to squared distances in robust pruning, or mixing squared and plain distances in any pruning test
- Building an index once and never re-measuring recall as the data grows, drifts or is deleted from
systems:
- FAISS: IndexFlatL2 keeps the k best per query in a max-heap and switches from a direct loop to BLAS matrix multiplication once nq × d reaches 128,000; IndexIVFFlat (default nprobe 1), IndexIVFPQ (PQ codes of residuals by default) and IndexHNSWFlat (efConstruction 40, efSearch 16 by default) are this module's structures, written in C++
- pgvector: an HNSW index (m = 16, ef_construction = 64, hnsw.ef_search = 40 by default) and an IVFFlat index built with k-means on a sample (spherical k-means for cosine and inner product; ivfflat.probes = 1 by default)
- Qdrant uses HNSW as its only dense vector index (m = 16, ef_construct = 100 by default), adds extra graph edges for indexed payload fields so filtered search stays connected, and falls back to a full scan when a filter leaves few points; Milvus offers FLAT, IVF_FLAT, IVF_PQ, HNSW and DISKANN among its index types
- DiskANN in production: Milvus's DISKANN index (Vamana graph on disk, PQ codes in memory, a beam width for parallel reads), Azure Cosmos DB's diskANN vector index, Azure SQL's CREATE VECTOR INDEX (TYPE = 'DiskANN', the only type offered) and Timescale's pgvectorscale StreamingDiskANN index for Postgres
further:
- Paper · 45 min | Malkov and Yashunin: Efficient and robust approximate nearest neighbor search using HNSW graphs (read section 3, then Algorithms 1, 2, 4 and 5 and section 4.1 on mL, Mmax0 and efConstruction) | https://arxiv.org/abs/1603.09320
- Paper · 40 min | Subramanya et al.: DiskANN, NeurIPS 2019 (sections 2.2-2.4 on RobustPrune and Vamana, section 3 on the SSD layout, beam search and implicit re-ranking) | https://proceedings.neurips.cc/paper_files/paper/2019/file/09853c7fb1d3f8ee67a61b6bf4a7f8e6-Paper.pdf
- Paper · 45 min | Jégou, Douze and Schmid: Product quantization for nearest neighbor search (sections II-B, III-A and IV: product quantisers, symmetric and asymmetric distances, IVFADC) | https://www.irisa.fr/texmex/people/jegou/papers/jegou_searching_with_quantization.pdf
- Docs · 20 min | FAISS wiki: Faiss indexes (the 'Summary of methods' table gives bytes per vector and parameters for every index in this module) | https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#summary-of-methods
---

=== primer | What does exact k-nearest-neighbour search really cost, and why keep a heap of size k? | 15 min
goal: Compute the cost of brute-force k-NN, implement it with a size-k max-heap and with NumPy, and know when exact search is the right answer
tag: vectors-exact-knn | Exact k-NN with a size-k heap
link: AI page: Approximate nearest neighbour search and HNSW | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-approximate-nearest-neighbour-search-and-hnsw | 3 min: the section 'Why exact search does not scale' puts this card's arithmetic next to real embedding sizes and introduces the index families of the next cards
link: FAISS wiki: Implementation notes | https://github.com/facebookresearch/faiss/wiki/Implementation-notes#matrix-multiplication-to-do-many-l2-distance-computations | 4 min: the first section, how IndexFlatL2 switches from a direct loop to BLAS matrix multiplication when nq × d reaches 128,000, and the numerical caveat of the expanded formula

> [!key]
> Exact k-NN compares the query with all n stored vectors, so it costs n × d multiply-adds and reads n × d × 4 bytes per query: nothing lets you skip a vector. Keeping the best k in a **max-heap of size k** makes the selection O(n log k) in the worst case and close to one comparison per candidate in practice, because the root (the worst of the best k) rejects almost everything. In NumPy you compute the distances as one matrix product and select with `argpartition`.

## Intuition

You want the ten cheapest flights from a list of a million. You do not sort the million. You keep a shortlist of ten with the most expensive of them at the door: each new flight is compared with that one only, and gets in only if it is cheaper, pushing the doorkeeper out. After the first few thousand flights the shortlist is so good that almost nothing gets in, so the work is one comparison per flight.

Vector search is the same, with "price" replaced by the distance between the query and a stored vector. The expensive part is computing the distances, not choosing among them.

## How it works

### The distances

For squared Euclidean distance, ‖q − x‖² = ‖q‖² − 2 q·x + ‖x‖². You compute ‖x‖² once per stored vector, ‖q‖² is the same for every candidate (so you can drop it when ranking), and the only per-pair work is a dot product. For unit-length embeddings, cosine similarity is q·x and ranks exactly like L2 (the AI page's [embeddings lesson](https://learningcurie.github.io/code-study-tracker/ai.html#l-c-text-embeddings-and-semantic-similarity) shows why). For m queries at once, all the dot products form one matrix product Q Xᵀ, which BLAS runs close to the processor's peak speed.

### The selection: a max-heap of size k

Keep the best k so far in a **max-heap keyed by distance**, so the root is the *worst* of the current best k. For each new candidate:

1. If the heap holds fewer than k items, push it.
2. Otherwise, if it is closer than the root, replace the root (`heapq.heapreplace`: one sift-down, O(log k)).
3. Otherwise discard it, after one comparison.

Why a max-heap? The question you ask n times is "does this candidate beat the worst one I am keeping?", and a max-heap answers it in O(1) by looking at the root. Python's `heapq` is a min-heap, so the template stores `-distance`. The heap never holds more than k items, so memory is O(k) however large n is, which matters when distances stream in from disk or when you merge the top-k lists of several shards.

### How often does the heap change?

In random order, the i-th candidate is among the best k of the first i with probability k / i. Summing from i = k + 1 to n gives k (H_n − H_k) ≈ k ln(n / k) replacements. For n = 100,000 and k = 10 that is 91.6; over 40 random streams on this machine the average was 90.6. Every other candidate costs one comparison. CPython's `heapq.nsmallest` uses exactly this algorithm, and the comments in its source do the same count.

### NumPy: argpartition

With the distances in an array, `np.argpartition(d, k - 1)` runs introselect: an O(n) average partial sort that moves the k smallest values to the front in no particular order. Then sort just those k. Total O(n + k log k), with the loop in C.

## Cost

Per query, for n vectors of dimension d:

| Step | Work | Example: n = 1,000,000, d = 768, float32 |
|---|---|---|
| Distances | n × d multiply-adds | 768 million |
| Memory read | n × d × 4 bytes | 3.07 GB |
| Heap selection | n comparisons + about k ln(n/k) sifts of log k | 1 million comparisons + about 115 sifts |
| argpartition | O(n) average + O(k log k) | 1 million element moves at most |

The distances dominate, and for a single query they are limited by **memory bandwidth**, not arithmetic: a matrix-vector product does 2 floating-point operations per 4 bytes it reads. Measured on one core of this machine (a shared Xeon server): for 20,000 × 64 vectors, `X @ q` took 0.6 ms and `argpartition` 0.16 ms (a full `argsort` took 0.8 ms); for 200,000 × 128 vectors (102 MB), `X @ q` took 14 ms. Batching changes the picture: 100 queries against those 200,000 vectors as one matrix product cost 1.8 ms *per query*, eight times less, because each block of X loaded into cache is reused by all 100 queries. The same 20,000 × 64 search in pure Python (`knn_heap` below) took 560 ms: interpreter overhead, not the algorithm, is what NumPy removes.

## When to use it

Exact search is the right answer more often than people expect:

- **Small collections.** Below about 100,000 vectors a flat scan takes around a millisecond and has perfect recall: nothing to build, tune or rebuild.
- **Few queries.** FAISS's guidelines say that if you will run only 1,000 to 10,000 searches, building an index does not pay for itself and a flat index is the most efficient option.
- **Heavily filtered queries.** If a filter leaves 2,000 rows (one tenant, one day), scan those exactly. Qdrant's query planner switches to a full scan by itself below its `full_scan_threshold`.
- **Ground truth and re-ranking.** Every approximate index is measured against exact results (the last card), and approximate candidates are often re-ranked exactly.

When not: when n × d × 4 bytes per query exceeds your latency budget at your query rate. Tens of millions of vectors at hundreds of queries per second need an index from the following cards, or GPUs.

| Selection method | Time | Extra memory | Use when |
|---|---|---|---|
| Sort everything | O(n log n) | O(n) | never, for top-k |
| Size-k max-heap | O(n log k), about O(n) on random order | O(k) | streams, merging shard results, small k |
| argpartition | O(n) average + O(k log k) | O(n) | distances already in an array |

## Worked trace

```steps
k = 3; distances arrive as 5.0, 2.0, 9.0, 1.0, 7.0, 3.0, 0.5. Push the first three; the largest sits at index 0, the root
    heap   [{{9.0}}, 2.0, 5.0]      root = worst kept = 9.0
---
1.0 < 9.0: replace the root and sift down. 9.0 leaves and 5.0 becomes the worst kept
    heap   [{{5.0}}, 2.0, 1.0]
---
7.0 > 5.0: one comparison, discarded. In a long stream almost every candidate takes this path
    heap   [{{5.0}}, 2.0, 1.0]      7.0 rejected
---
3.0 < 5.0: replace the root
    heap   [{{3.0}}, 2.0, 1.0]
---
0.5 < 3.0: replace the root; the sift-down moves 2.0 up to the root
    heap   [{{2.0}}, 0.5, 1.0]
---
End of the stream: sort the k survivors and report them nearest first
    result  0.5, 1.0, 2.0
```

## Template

```python
import heapq

import numpy as np


def knn_heap(query, vectors, k):
    """Exact k nearest by squared L2 in one pass, keeping a max-heap of the best k so far."""
    heap = []                                  # (-distance, id): heap[0] holds the worst of the best k
    for i, v in enumerate(vectors):
        d = sum((a - b) ** 2 for a, b in zip(query, v))
        if len(heap) < k:
            heapq.heappush(heap, (-d, i))
        elif d < -heap[0][0]:                  # beats the current worst: evict it
            heapq.heapreplace(heap, (-d, i))
    return [i for _, i in sorted(heap, reverse=True)]   # nearest first


def knn_numpy(Q, X, k, x_sq=None):
    """Exact k nearest for a batch of queries Q (m x d) against X (n x d), squared L2.
    x_sq: squared row norms of X; compute them once per dataset, not once per query."""
    if x_sq is None:
        x_sq = np.einsum("ij,ij->i", X, X)
    d2 = x_sq[None, :] - 2 * Q @ X.T                     # |q|^2 is the same for a whole row: skip it
    idx = np.argpartition(d2, k - 1, axis=1)[:, :k]                  # k smallest per row, unordered
    order = np.argsort(np.take_along_axis(d2, idx, axis=1), axis=1)   # sort just those k
    return np.take_along_axis(idx, order, axis=1)
```

`knn_heap` shows the algorithm in plain Python, and is what you want when distances arrive one by one or when you merge per-shard lists. `knn_numpy` is what you run on arrays. Both were checked against a full sort on 200 random inputs.

## Pitfalls

- **Recomputing the norms per query.** Compute ‖x‖² once per dataset. On the 20,000 × 64 array, `(X * X).sum(1)` took 2.8 ms here, four times the matrix-vector product itself (`np.einsum` took 0.44 ms).
- **Cancellation in the expanded formula.** ‖q‖² − 2 q·x + ‖x‖² can come out slightly negative, or lose precision when the vectors are long and close together; FAISS's implementation notes warn about it. Clamp at 0, or compute (q − x)² directly where exact values matter.
- **Mixing metrics.** Inner product, cosine and L2 give the same ranking only for unit-length vectors. Normalise once when storing and once per query, or use the metric the embedding model was trained with.
- **k larger than n, and ties.** `argpartition(d, k - 1)` raises an error when k > n, so clamp k. Ties are broken arbitrarily, so two correct implementations can return different ids at equal distance: test by comparing distances, not ids.
- **Heapifying everything.** `heapify` of all n distances then k pops costs O(n + k log n) time but O(n) memory, and cannot work on a stream.

## Check yourself

Q: A size-3 max-heap (heapq on negated values) shows the array [4.0, 1.0, 3.0]. The next distances are 3.5, 6.0 and 0.2. What is the array after each?
A: 3.5 < 4.0 replaces the root, and 3.5 is still larger than both children: [3.5, 1.0, 3.0]. 6.0 > 3.5 is rejected after one comparison. 0.2 < 3.5 replaces the root; the sift-down swaps it with its larger child 3.0, giving [3.0, 1.0, 0.2]. The best three are 0.2, 1.0 and 3.0.

Q: Why is the expected number of heap replacements about k ln(n/k) rather than n, and when does that fail?
A: In random order the i-th candidate is among the best k of the first i with probability k / i, since every rank is equally likely. Summing k / i from k + 1 to n gives k (H_n − H_k) ≈ k ln(n/k): about 92 for n = 100,000 and k = 10. It fails for adversarial order: if the candidates arrive sorted by decreasing distance, every one replaces the root, which is the O(n log k) worst case.

Q: Each of 8 shards returns its own exact top 10 for a query. How do you get the global top 10, and what does it cost?
A: Run the same size-10 max-heap over the 80 candidates (or `heapq.nsmallest(10, ...)`, or `heapq.merge` of the 8 sorted lists, taking 10): O(80 log 10), negligible. The merge is exact because the global top 10 must lie within the union of the shards' top 10s; this is how distributed vector search combines shards.

Q: A service stores 2 million 384-dimensional float32 embeddings and must answer 50 queries per second. Estimate the brute-force cost.
A: Per query: 2,000,000 × 384 = 768 million multiply-adds and 3.07 GB read. At the roughly 7 GB/s that one core sustained in the measurement above, that is about 0.4 s per query, so 50 queries per second would need about 20 cores, or heavy batching. An index pays for itself here; at 20,000 vectors it would not.

## Lab

- Count the heap's work. Generate 100,000 distances with `np.random.default_rng(0).random(100_000)`, run the size-10 heap over them and count root replacements. Expected: 78 for this seed (the average over many seeds is about 91, matching k (H_n − H_k) = 91.6), against 99,912 one-comparison rejections. Then feed the same values sorted in decreasing order. Expected: 99,990 replacements, the worst case.
- Time single against batched. On the lab dataset at the end of this module (20,000 × 64), time `knn_numpy` for one query and for all 200 queries at once, with `x_sq` precomputed. Expected: the batch costs at least twice less per query (0.59 ms against 0.31 ms on this machine, where most of the batched time is the selection, not the matrix product).

> [!know]
> You now know what brute-force k-NN costs, why a size-k max-heap selects with about one comparison per candidate, and when an exact scan beats any index.

=== primer | Why do KD-trees work in 2-D but collapse in 100 dimensions? | 15 min
goal: Build and search a KD-tree with exact pruning, and measure and explain why it degrades to a full scan as the dimension grows
tag: vectors-kdtree | KD-tree search and its limits
link: scikit-learn user guide: choice of nearest neighbours algorithm | https://scikit-learn.org/stable/modules/neighbors.html#choice-of-nearest-neighbors-algorithm | 8 min: how query cost depends on N, D, structure and k, and the rule that algorithm='auto' falls back to brute force when D > 15; the 'K-D Tree' section just above says the tree is fast below about 20 dimensions

> [!key]
> A KD-tree splits space at the median of one coordinate per level. A query descends to its own leaf, then backtracks only into boxes that could hold something closer: the far side of a split is skipped when the squared gap between the query and the splitting plane is at least the current k-th best squared distance. In 2 or 3 dimensions that prunes almost everything. In high dimensions all distances look alike, the gaps are never large enough, and the tree measures every point: 98% of 20,000 points at d = 16 and 100% from d = 32 in the measurement below.

## Intuition

Find the nearest café on a map. Split the map into west and east at the median longitude, each half into south and north at the median latitude, and so on. To answer a query, go to your own small rectangle, find the best café in it, then ask of each neighbouring rectangle: "could anything in there be closer than what I have?" If even its nearest edge is farther than your current best, skip it and everything inside. On a 2-D map, almost every rectangle is skipped.

Now give every point 64 coordinates. Your best distance is barely smaller than the distance to a random point, and the gap along any single coordinate is small. The question "could anything in that box be closer?" is answered "maybe" every time.

## How it works

### Build

At depth t, split on coordinate t mod d at the median, so each child gets half the points; stop when a node holds at most `leaf_size` points. Finding the median with a linear-time partition (`np.argpartition`) costs O(n) per level over O(log n) levels.

### Search with pruning

Keep the best k found so far in a size-k max-heap, exactly as in the previous card. At an internal node with splitting coordinate a and value s, let gap = q[a] − s:

1. Visit the child on the query's side first (gap < 0 means the lower side).
2. Coming back, visit the other child only if gap² < the current k-th best squared distance.

Skipping is safe because every point x on the far side has x[a] on the other side of s, so ‖q − x‖² ≥ (q[a] − x[a])² ≥ gap². The invariant: **a subtree is skipped only when a lower bound on all its distances is at least the current k-th best**. So the search is exact; the tree only saves work, it never changes the answer.

```text
9 |    h                 |
8 |                      | g             root: x = 6
7 |----------------d-----|               left half:  y = 7
6 |                      |-------------c right half: y = 6
5 |                      |         q
4 |                    b |             leaves: {a, b} {d, h}
3 |        a             |                     {e, f} {c, g}
2 |                      |     f
1 |                      |         e
0 |                      |
  +----------------------------------------
   0   1   2   3   4   5   6   7   8   9
```

### Why it collapses: the curse of dimensionality, measured

Pruning needs gap² < (k-th best distance)², where the gap is measured along one coordinate. Two things break as d grows:

1. **Distances concentrate.** For random data, the nearest and the farthest point end up at almost the same distance. Averaged over queries on 20,000 uniform points in the unit cube, the ratio nearest / farthest was 0.01 at d = 2, 0.19 at d = 8, 0.35 at d = 16 and 0.62 at d = 64. When your best candidate is 62% as far away as the worst, a gap along one coordinate almost never rules a box out.
2. **Too few splits per coordinate.** A balanced tree over 20,000 points with leaves of 8 has about 11 levels. At d = 64 most coordinates are never split, so the cells are long slabs, not small boxes. The usual rule of thumb is that a KD-tree needs n much larger than 2^d.

Measured with this card's template (20,000 uniform points, 200 random queries, leaf size 8; the share of points whose distance was computed):

| d | exact 1-NN | exact 10-NN | nearest / farthest distance | n / 2^d |
|---|---|---|---|---|
| 2 | 0.1% | 0.2% | 0.01 | 5,000 |
| 4 | 0.3% | 1.0% | 0.07 | 1,250 |
| 8 | 5.5% | 17.8% | 0.19 | 78 |
| 16 | 98.2% | 100% | 0.35 | 0.3 |
| 32 | 100% | 100% | 0.50 | about 0 |
| 64 | 100% | 100% | 0.62 | about 0 |

The collapse happens exactly where n / 2^d drops below 1. On the clustered 64-dimensional lab data the tree also measured 100% of the points for 10-NN, so it was strictly slower than brute force. Embeddings have hundreds to thousands of dimensions; their *intrinsic* dimension is lower than that, but still far too high for splits along single coordinates.

## Cost

- **Build:** O(n) partition work per level × about log2(n / leaf_size) levels = **O(n log n)** time, O(n) memory.
- **Query, low dimension:** descend O(log n) levels and check a few neighbouring leaves: at d = 2 the table shows 0.1% of 20,000 points, about 20 distances.
- **Query, high dimension:** **O(n)** distances plus the cost of the recursion, so slower than a vectorised scan.

## When to use it

| Situation | Use |
|---|---|
| 2-D or 3-D points: maps, game worlds, point clouds, colours | KD-tree (`scipy.spatial.KDTree`, scikit-learn `KDTree`) |
| Up to about 15 dimensions, many queries, mostly static data | KD-tree or ball tree; measure the visited share |
| More than about 20 dimensions (embeddings) | brute force for small n, otherwise IVF, HNSW or DiskANN |

scikit-learn encodes the same advice: with `algorithm='auto'` it chooses brute force when D > 15, and its guide says KD-trees are very fast below about 20 dimensions and approach O(DN) above that. That is why none of the vector databases in this module use KD-trees for embeddings.

## Worked trace

The eight points in the diagram, query q = (8, 5), k = 1, leaf size 2:

```steps
Root splits on x at 6. gap = 8 - 6 = 2 >= 0, so the near side is the right half {e, f, c, g}
    q = (8, 5)   near: x >= 6   far: x <= 6, held back with gap² = 4
---
The right node splits on y at 6. gap = 5 - 6 = -1, so the near child is the leaf {e, f}
    near: {e (8,1), f (7,2)}   far: {c, g}, held back with gap² = 1
---
Leaf {e, f}: measure both. e at d² 16, f at d² 10: best so far is f, 10
    e 16   {{f 10}}             best = 10
---
Back at the right node: gap² = 1 < 10, so the far leaf might hold something closer. Visit it
    c (9,6) d² 2   g (6,8) d² 13   ->   best = {{c, 2}}
---
Back at the root: gap² = 4 is not below 2, so no point with x <= 6 can beat c. Skip the whole left half
    skipped: a, b, d, h   (4 of 8 points never measured)
---
Answer c = (9, 6) at squared distance 2, after measuring 4 of the 8 points. Brute force agrees
    d²:  a 40  b 10  {{c 2}}  d 20  e 16  f 10  g 13  h 65
```

## Template

```python
import heapq

import numpy as np


class KDTree:
    """Exact k-nearest-neighbour search by squared L2. self.visited counts the points measured."""

    def __init__(self, X, leaf_size=8):
        self.X, self.leaf_size = X, leaf_size
        self.root = self._build(np.arange(len(X)), depth=0)

    def _build(self, ids, depth):
        if len(ids) <= self.leaf_size:
            return ids                                  # a leaf is just an array of ids
        axis = depth % self.X.shape[1]                  # cycle through the coordinates
        vals = self.X[ids, axis]
        mid = len(ids) // 2
        part = np.argpartition(vals, mid)               # median split in linear time
        return (axis, vals[part[mid]],
                self._build(ids[part[:mid]], depth + 1),   # coordinate <= split
                self._build(ids[part[mid:]], depth + 1))   # coordinate >= split

    def search(self, q, k=1):
        self.visited = 0
        heap = []                                       # (-dist2, id): worst of the best k on top

        def worst():
            return -heap[0][0] if len(heap) == k else np.inf

        def visit(node):
            if isinstance(node, np.ndarray):            # leaf: measure every point in it
                self.visited += len(node)
                for i, d in zip(node, ((self.X[node] - q) ** 2).sum(1)):
                    if d < worst():
                        if len(heap) == k:
                            heapq.heapreplace(heap, (-d, i))
                        else:
                            heapq.heappush(heap, (-d, i))
                return
            axis, split, left, right = node
            gap = q[axis] - split
            near, far = (left, right) if gap < 0 else (right, left)
            visit(near)
            if gap * gap < worst():                     # the far side could still hold a closer point
                visit(far)

        visit(self.root)
        return [int(i) for _, i in sorted(heap, reverse=True)]
```

Tested against brute force on 150 random trees (1 to 300 points, 1 to 5 dimensions, leaf sizes 1 to 9, including grids full of tied coordinates).

## Pitfalls

- **Comparing a plain gap with a squared distance.** If the heap holds squared distances, prune with gap², as the template does. Mixing the two prunes wrongly or never prunes.
- **Pruning with the 1st best when k > 1.** The bound is the k-th best, and it is infinite until the heap holds k points (`worst()` handles both).
- **Ties at the median.** Equal coordinates can land on both sides of the split. That is fine as long as the pruning bound uses "lower side: ≤ split, upper side: ≥ split", which the gap test respects.
- **Unbalanced trees.** Inserting points one by one without median splits (for example in sorted order) can degenerate the tree into a list, with O(n) depth and recursion-limit errors. Build from the whole set, or rebuild periodically.
- **Trusting a 2-D demo.** A tree that looks magical on 2-D data says nothing about 64-D embeddings. Measure the visited share on your own data.

## Check yourself

Q: In the trace, suppose the query is (6.5, 5) instead of (8, 5). Which parts of the tree are skipped, and what is the answer?
A: From the right half, f gives 9.25 and then c gives 7.25. At the root the gap to x = 6 is 0.5 and 0.25 < 7.25, so the left half must be visited. Its node splits on y at 7 with gap −2: the near leaf {a, b} gives b = (5, 4) at 3.25, and since 4 is not below 3.25 the leaf {d, h} is skipped. The answer is b, after measuring 6 of the 8 points.

Q: Why is the pruning test still exact even though it only looks at one coordinate?
A: Because it is a lower bound. Any point on the far side differs from q by at least |gap| in the splitting coordinate, so its squared distance is at least gap². Skipping a subtree whose lower bound is already no better than the k-th best cannot remove a true neighbour. Libraries tighten the bound with the distance to the whole bounding box, but no lower bound helps once distances concentrate.

Q: You need the nearest of 5 million GPS points for each of 10,000 queries. KD-tree or brute force?
A: KD-tree (or a spatial index in your database). With d = 2, n is vastly larger than 2^d, and each query measures a handful of points in O(log n) steps, while brute force reads all 5 million per query. The opposite holds for 768-dimensional embeddings.

## Lab

- Reproduce the curse. Build trees over `np.random.default_rng(d).random((20_000, d))` for d = 2, 4, 8 and 16, run 200 random 1-NN queries from the same generator and record `visited / 20_000`. Expected: about 0.1%, 0.3%, 5.5% and 98%, with the jump where 20,000 / 2^d falls below 1. Compute the mean nearest/farthest distance ratio for the same data. Expected: about 0.01, 0.07, 0.19 and 0.35.

> [!know]
> You now know how a KD-tree prunes, why the pruning bound fails once distances concentrate, and why vector indexes for embeddings use clustering, hashing or graphs instead.

=== primer | How can random hyperplanes hash similar vectors into the same bucket? | 16 min
goal: Derive the collision probability of random-hyperplane hashing, choose bits and tables with the AND-OR formula, and implement multi-table LSH with exact re-ranking
tag: vectors-lsh | Random-hyperplane LSH
link: Charikar: Similarity estimation techniques from rounding algorithms (STOC 2002) | https://www.cs.princeton.edu/courses/archive/spr04/cos598B/bib/CharikarEstim.pdf | 10 min: section 3, 'Random hyperplane based hash functions for vectors', which defines the sign hash and states Pr[h(u) = h(v)] = 1 − θ(u, v)/π
link: FAISS wiki: IndexLSH and cell-probe methods | https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#indexlsh-and-its-relationship-with-cell-probe-methods | 4 min: the two drawbacks of classic LSH in practice, and why FAISS implements IndexLSH as binary codes compared by Hamming distance

> [!key]
> Draw a random direction r and record one bit: which side of the hyperplane r·x = 0 a vector lies on. Two vectors at angle θ get the same bit with probability exactly **1 − θ/π**, so near vectors usually agree and unrelated ones agree only half the time. Concatenate K bits into one bucket key (AND: only close vectors still collide) and build L independent tables (OR: a true neighbour needs to collide in just one); then re-rank the union of candidates exactly. A neighbour with per-bit probability p becomes a candidate with probability **1 − (1 − p^K)^L**.

## Intuition

Throw a random wall through a crowded room. Two friends standing side by side almost always end up on the same side; two people at opposite ends are separated about half the time. Throw ten walls and give everyone a 10-bit "side code": people who share a code are probably close. Bad luck still splits some pairs of friends, so repeat with fresh walls several times, and call anyone who shares a code with you in *any* round a candidate. Then measure the candidates properly.

## How it works

### One bit and its collision probability

Draw r with independent standard normal entries, so its direction is uniform, and set h(x) = 1 if r·x > 0, else 0. For vectors u and v at angle θ, only the part of r in the plane spanned by u and v affects the two signs, and that part points in a uniformly random direction in the plane. The signs differ exactly when the line perpendicular to it passes between u and v, or between their opposites: two arcs of θ out of 2π. So

Pr[h(u) = h(v)] = 1 − θ / π.

Measured with 200,000 random hyperplanes in 64 dimensions: 0.8330 at θ = 30° (theory 0.8333), 0.6665 at 60° (0.6667) and 0.5012 at 90° (0.5000). Only the angle matters, so this family hashes for **cosine similarity**; vector length is ignored.

### AND: K bits per key

One bit is a weak filter, since unrelated vectors still agree half the time. A key of K independent bits collides with probability p^K. With K = 10, a neighbour at cosine 0.9 (p = 0.856) still collides with probability 0.21, but an unrelated vector at cosine 0 (p = 0.5) only 0.001. A larger K means smaller, purer buckets.

### OR: L tables

One table now misses most neighbours, so build L tables with independent hyperplanes and take the union of the query's L buckets. A vector becomes a candidate if it collides in at least one table:

P[candidate] = 1 − (1 − p^K)^L

| cosine to the query | p = 1 − θ/π | K = 1, L = 1 | K = 10, L = 1 | K = 10, L = 32 | K = 10, L = 128 |
|---|---|---|---|---|---|
| 0.9 | 0.856 | 0.856 | 0.212 | 1.000 | 1.000 |
| 0.7 | 0.747 | 0.747 | 0.054 | 0.831 | 0.999 |
| 0.5 | 0.667 | 0.667 | 0.017 | 0.429 | 0.893 |
| 0.3 | 0.597 | 0.597 | 0.006 | 0.168 | 0.522 |
| 0.0 | 0.500 | 0.500 | 0.001 | 0.031 | 0.118 |

As a function of similarity this is an S-curve: K moves the steep part towards higher similarity (fewer false candidates), L lifts the curve (fewer misses). It is the same banding idea that MinHash LSH uses for Jaccard similarity on sets.

### The query

Hash the query with each table's K hyperplanes, collect its L buckets, remove duplicates, and compute exact similarities for those candidates only, keeping the top k with the first card's selection. LSH never ranks anything itself; it only proposes candidates.

## Cost

- **Build:** n × L × K × d multiply-adds for the projections, n × L bucket inserts, and memory for L × n ids, because every vector appears once per table.
- **Query:** L × K × d multiply-adds to hash the query (128 × 10 × 64 = 81,920), L lookups, then |candidates| × d to re-rank. The expected number of candidates is the sum of P[candidate] over all stored vectors, so the cost depends on how many *unrelated* vectors still slip in.

Measured on the lab data (20,000 clustered unit vectors, d = 64; the 10th true neighbour has mean cosine only 0.50, a hard but realistic setting):

| L | K | recall@10 | share re-ranked | median time per query |
|---|---|---|---|---|
| 8 | 10 | 0.187 | 1.1% | 0.5 ms |
| 32 | 10 | 0.512 | 4.1% | 0.3 ms |
| 128 | 10 | 0.929 | 14.6% | 1.4 ms |
| 64 | 8 | 0.941 | 24.8% | 2.5 ms |
| 128 | 8 | 0.995 | 41.5% | 5.0 ms |

Brute force in NumPy took 0.56 ms on the same data. LSH reached 0.93 recall only by re-ranking 15% of the collection, plus the cost of gathering buckets in Python, so it was *slower* than scanning everything. The next card's IVF reaches 0.94 recall while scanning 0.7%.

## When to use it

- **Where it shines:** you need guarantees that do not depend on the data (theory gives sublinear query time for approximate near neighbours), vectors arrive as a stream and must be searchable at once with no training, or you want short binary signatures: the K bits of one table form a sketch compared by Hamming distance. FAISS's IndexLSH is exactly that, a flat index of binary codes.
- **Where it loses:** dense embeddings in production. The hash functions ignore the data, so good recall needs many tables (memory) and many candidates (time). The FAISS wiki names both drawbacks, and the DiskANN paper notes that LSH methods are outperformed by graph-based methods on real datasets. IVF learns its partitions from the data; HNSW follows the data's own neighbourhoods.
- **Names to know:** multi-probe LSH also checks buckets whose keys differ from the query's in its least certain bits (projections close to 0), getting the recall of many tables from fewer; the p-stable family h(x) = ⌊(a·x + b) / w⌋ hashes for Euclidean distance.

## Worked trace

Three hyperplanes in 2-D with normals r1 = (1, 0), r2 = (0.6, 0.8), r3 = (−0.6, 0.8); bit i of the key is worth 2^i.

```steps
Hash a = (0.8, 0.5), which is 8 degrees from the query. Signs of r1·a, r2·a, r3·a
    r·a = 0.80, 0.88, -0.08   ->  bits 1 1 0  ->  key {{3}}
---
Hash b = (-0.5, 0.9), 95 degrees from the query
    r·b = -0.50, 0.42, 1.02   ->  bits 0 1 1  ->  key {{6}}
---
Hash c = (0.7, -0.6), 65 degrees from the query. The table now has three buckets
    r·c = 0.70, -0.06, -0.90  ->  bits 1 0 0  ->  key {{1}}
    table: {3: [a], 6: [b], 1: [c]}
---
Query q = (0.9, 0.4): same projections, bucket 3. The only candidate is a
    r·q = 0.90, 0.86, -0.22   ->  bits 1 1 0  ->  key 3  ->  candidates {{[a]}}
---
Re-rank the candidates exactly (just a here) and return it. b and c never had a distance computed
    answer: a
---
The odds behind it: per bit p = 1 - θ/180°, per 3-bit key p³, and with L = 4 tables 1 - (1 - p³)⁴
    a: p 0.956  key 0.873  4 tables {{1.000}}
    c: p 0.641  key 0.264  4 tables 0.706
    b: p 0.472  key 0.105  4 tables 0.358
```

## Template

```python
import numpy as np


class HyperplaneLSH:
    """L hash tables; each key is K sign bits of random projections (angular / cosine similarity)."""

    def __init__(self, X, n_tables=32, n_bits=10, seed=0):
        rng = np.random.default_rng(seed)
        self.X, self.L, self.K = X, n_tables, n_bits
        self.planes = rng.standard_normal((n_tables * n_bits, X.shape[1])).astype(X.dtype)
        self.pow2 = 1 << np.arange(n_bits)
        keys = self._keys(X)                                    # shape (n, L)
        self.tables = []
        for t in range(n_tables):
            order = np.argsort(keys[:, t], kind="stable")       # group ids by bucket key
            uniq, start = np.unique(keys[order, t], return_index=True)
            stop = np.append(start[1:], len(order))
            self.tables.append({int(u): order[a:b] for u, a, b in zip(uniq, start, stop)})

    def _keys(self, V):
        bits = (V @ self.planes.T > 0).reshape(len(V), self.L, self.K)
        return bits @ self.pow2                                  # K bits -> one integer per table

    def search(self, q, k=10):
        keys = self._keys(q[None, :])[0]
        hits = [self.tables[t].get(int(key)) for t, key in enumerate(keys)]
        hits = [h for h in hits if h is not None]
        if not hits:
            return np.array([], dtype=np.int64), 0
        cand = np.unique(np.concatenate(hits))                  # union over tables (OR)
        scores = self.X[cand] @ q                                # re-rank candidates exactly
        top = np.argsort(-scores)[:k]
        return cand[top], len(cand)
```

`search` returns the ids and the number of candidates re-ranked, so you can measure both sides of the trade-off. Tested: every stored vector finds itself first, every id appears in exactly one bucket per table, and results come back in order of similarity.

## Pitfalls

- **Using sign hashes for Euclidean distance on unnormalised vectors.** Sign bits see only the angle. Normalise first if the model's metric is cosine; otherwise use the p-stable family.
- **Too many bits.** With K = 20, p^K is tiny even for good neighbours and buckets are nearly empty, so you need hundreds of tables. A useful start: choose K so that n / 2^K, the average bucket size, is about the number of items you are willing to re-rank per table (about 20 at K = 10 for 20,000 vectors).
- **Forgetting the memory.** Each table stores every id once: L = 128 tables over 20,000 vectors is 2.56 million ids, about 20 MB with 8-byte ids, four times the 5 MB of float32 vectors.
- **Judging by candidates instead of time.** "Re-ranks only 15%" sounds good until you time the bucket gathering. Measure end to end.
- **Correlated tables.** Reusing hyperplanes across tables breaks the independence that 1 − (1 − p^K)^L assumes, and recall falls below the formula.

## Check yourself

Q: Two unit vectors have cosine similarity 0.5. What is the probability that they share a 4-bit key in one table, and in at least one of 10 tables?
A: θ = arccos 0.5 = 60°, so p = 1 − 60/180 = 2/3. One table: (2/3)⁴ = 16/81 ≈ 0.198. At least one of 10: 1 − (1 − 0.198)¹⁰ ≈ 1 − 0.111 = 0.889.

Q: Why does a random hyperplane separate u and v with probability exactly θ/π?
A: Only the component of r in the plane of u and v affects the signs of r·u and r·v, and for a Gaussian r that component's direction is uniform on the circle. The signs differ when the line perpendicular to it falls inside the angle between u and v or inside the opposite angle: two arcs of θ out of 2π, so θ/π.

Q: Your LSH index has recall 0.6. Do you raise K or L, and what does it cost?
A: Raise L. Each extra table gives every neighbour another chance, so recall moves towards 1 − (1 − p^K)^L, at the cost of one more id per vector in memory and more candidates to re-rank. Raising K does the opposite: fewer candidates and lower recall.

## Lab

- Check the formula. In 64 dimensions take u = e1 and v = cos 60° e1 + sin 60° e2, draw 200,000 Gaussian hyperplanes with `np.random.default_rng(0)` and count how often the signs agree. Expected: 0.6665 (theory 0.6667); for 30° and 90°, 0.8330 and 0.5012.
- Tune the tables. With `HyperplaneLSH(X, n_tables=L, n_bits=10, seed=0)` on the lab data, find the smallest L (in steps of 8) that reaches recall@10 of 0.9. Expected: L = 112 (0.911); L = 104 gives 0.896 and L = 64 only 0.749.

> [!know]
> You now know why a random hyperplane collides with probability 1 − θ/π, how K bits and L tables shape the candidate set, and why learned partitions and graphs beat LSH on embeddings.

=== primer | How does an IVF index use k-means to scan only a few clusters? | 16 min
goal: Train a k-means coarse quantiser, build inverted lists, search the nprobe nearest lists, and choose nlist and nprobe from the cost formula and a recall measurement
tag: vectors-ivf | IVF: k-means lists and nprobe
link: FAISS wiki: cell-probe methods (IndexIVF) | https://github.com/facebookresearch/faiss/wiki/Faiss-indexes#cell-probe-methods-indexivf-indexes | 6 min: nlist and nprobe, why the scanned share exceeds nprobe/nlist, and the rule of thumb nlist = C × √n
link: pgvector README: IVFFlat | https://github.com/pgvector/pgvector/blob/master/README.md#ivfflat | 5 min: the same index inside Postgres, with its starting points lists = rows / 1000 (up to a million rows) and probes = √lists

> [!key]
> An **inverted file (IVF)** index runs k-means once to place nlist centroids (the **coarse quantiser**), files every vector in the list of its nearest centroid, and at query time scans only the **nprobe** lists whose centroids are nearest the query. A query costs about nlist × d to rank the centroids plus (nprobe / nlist) × n × d to scan the lists, so nlist near √n balances the two. Recall is lost only when a true neighbour sits in a list you did not probe, which is why raising nprobe trades speed for recall smoothly.

## Intuition

A librarian looking for a book on volcanoes does not search every shelf: she goes to the geology section, and if the book is not there, to the neighbouring sections. IVF builds the "sections" from the data itself with k-means, so each one holds vectors that are near each other, and searches only the few sections nearest the query. The risk is a book shelved in the section next door; probing more sections fixes that, at a price.

## How it works

### Training: Lloyd's k-means

1. Pick nlist starting centroids (random rows in the template; k-means++ seeding is a common improvement).
2. **Assign** every training vector to its nearest centroid.
3. **Update** every centroid to the mean of the vectors assigned to it.
4. Repeat steps 2 and 3 for a fixed number of iterations (FAISS runs 25 by default).

Neither step can increase the total squared distance from vectors to their centroids (assignment picks the nearest centroid, and the mean minimises squared distance within a cluster), so the algorithm converges, to a local optimum. The assignment step is itself a nearest-neighbour search of n vectors against nlist centroids, n × nlist × d multiply-adds per iteration, and dominates training. FAISS prints a warning below 39 training vectors per centroid, and its guidelines ask for 30 × nlist to 256 × nlist; pgvector samples 50 rows per list, at least 10,000.

### The inverted lists

Assign every vector to its nearest centroid and store it in that centroid's list. The template sorts the vectors by list, so list c is one contiguous block from `start[c]` to `start[c + 1]`: the layout of a CSR sparse matrix, good for cache and for vectorised scanning. Real indexes store an id next to each vector or code; FAISS's IndexIVFFlat uses 4 × d + 8 bytes per vector, the float32 vector plus a 64-bit id.

### Searching

1. Compute the query's distance to all nlist centroids and take the nprobe nearest (`argpartition`).
2. Gather those lists and compute exact distances to their vectors.
3. Keep the top k.

Inside the probed lists the search is exact, so the only way to miss a neighbour is the **boundary effect**: a vector just across a cell boundary is close to the query but filed under another centroid. On the lab data with nlist = 141, the query's nearest list held 75.7% of its true top 10, the nearest 4 lists 85.4% and the nearest 16 lists 94.1%: exactly the recall at nprobe = 1, 4 and 16.

## Cost

Per query, with equal lists:

cost(nlist) ≈ nlist × d (rank the centroids) + (nprobe / nlist) × n × d (scan the lists)

The derivative 1 − nprobe × n / nlist² is zero at nlist = √(nprobe × n). For nprobe = 1 that is √n: about 141 for the lab's 20,000 vectors, giving 141 + 142 distances per query instead of 20,000. FAISS's wiki makes the same balance with a constant C (scanning lists is less efficient per vector than ranking centroids in a batch), giving nlist = C × √n, and its guidelines suggest 4√n to 16√n below a million vectors. pgvector suggests rows / 1000 up to a million rows and √rows beyond.

Lists are never equal. With nlist = 141 on the lab data, list sizes ranged from 51 to 293 (mean 142), and because queries land more often in big, dense clusters, nprobe = 8 scanned 7.2% of the vectors instead of nprobe / nlist = 5.7%. The FAISS wiki warns about exactly this underestimate.

Measured on the lab data (20,000 × 64, one core, NumPy; brute force took 0.56 ms per query in the same run):

| nlist | nprobe | recall@10 | scanned | median time per query |
|---|---|---|---|---|
| 141 | 1 | 0.757 | 0.9% | 0.08 ms |
| 141 | 4 | 0.854 | 3.6% | 0.15 ms |
| 141 | 16 | 0.941 | 14.3% | 0.62 ms |
| 141 | 32 | 0.975 | 28.1% | 1.00 ms |
| 566 | 1 | 0.754 | 0.3% | 0.15 ms |
| 566 | 4 | 0.944 | 0.7% | 0.16 ms |
| 566 | 16 | 0.975 | 3.0% | 0.28 ms |

Two lessons. First, nprobe is a smooth dial: each doubling buys a few points of recall for twice the scan. Second, nlist matters as much: with 566 lists (4√n) the cells follow the data's clusters more closely, so 4 probes give the recall that needed 16 with 141 lists, at a fifth of the scan. Training took 1.4 s for 141 lists and 2.7 s for 400 lists (20 iterations, NumPy).

## When to use it

- **Good fit:** large, static or slowly changing collections; tight memory (IVF adds only an id per vector); GPUs (scanning lists is dense, regular work); and as the outer layer of compressed indexes (IVF-PQ, next card). Training is fast compared with building a graph.
- **Weak spots:** lower recall than HNSW at the same speed; the centroids are trained once, so when the data drifts some lists swell and recall drops until you retrain; inserts are cheap (file under the nearest centroid) but deletions leave holes.
- **Settings to start from:** nlist ≈ 4√n to 16√n (FAISS) or rows / 1000 (pgvector, below a million rows), then raise nprobe until recall meets your target; pgvector suggests starting at probes = √lists.

| | IVF | HNSW (later card) |
|---|---|---|
| Build | k-means: seconds to minutes | one graph insert per vector: much slower |
| Memory beyond the vectors | an 8-byte id per vector | about 150 bytes of links per vector at M = 16 |
| Recall at equal speed | lower | higher |
| Query-time dial | nprobe | ef_search |
| With compression | natural (IVF-PQ) | possible (HNSW over compressed vectors) |

## Worked trace

```steps
Train k-means with k = 2 on six 1-D values, starting from centroids 1 and 2. Assign each value to its nearest centroid
    values     1   2   3   8   9  13
    list       0   1   1   1   1   1
---
Update: each centroid moves to the mean of its list. List 0 = {1} gives 1; list 1 = {2, 3, 8, 9, 13} gives 7
    centroids  {{1}}  {{7}}
---
Assign again: 2 and 3 are now nearer to 1 than to 7
    values     1   2   3   8   9  13
    list       0  {{0   0}}  1   1   1
---
Update: centroids 2 and 10. Another round changes nothing, so k-means has converged
    centroids  {{2}}  {{10}}      lists {1, 2, 3} and {8, 9, 13}
---
Now a 2-D index with three lists, trained by k-means on nine points. Query q = (4, 5.5): rank the centroids by squared distance
    list 0  centroid (1.33, 1.33)  d² 24.47  holds (1,1) (2,1) (1,2)
    list 1  centroid (7.5, 7.5)    d² 16.25  holds (8,8) (9,8) (8,9) (5,5)
    list 2  centroid (1.5, 8.5)    d² {{15.25}}  holds (1,8) (2,9)
---
nprobe = 1 scans list 2 only and answers (1, 8) at d² 15.25. Wrong: the true nearest, (5, 5) at d² 1.25, is in list 1, just across the boundary
    scanned  {{(1,8) 15.25}}  (2,9) 16.25
---
nprobe = 2 also scans list 1, a close second at 16.25, and finds (5, 5). Recall recovered, at the price of scanning 6 of 9 points instead of 2
    scanned  (1,8) 15.25  (2,9) 16.25  (8,8) 22.25
             (9,8) 31.25  (8,9) 28.25  {{(5,5) 1.25}}
```

## Template

```python
import numpy as np


def kmeans(X, k, iters=20, seed=0):
    """Lloyd's algorithm: returns centroids C (k x d) and each row's cluster."""
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)].copy()           # start from k random rows
    for _ in range(iters):
        assign = np.argmin((C * C).sum(1) - 2 * X @ C.T, axis=1)  # nearest centroid (|x|^2 dropped)
        sums = np.zeros_like(C)
        np.add.at(sums, assign, X)
        counts = np.bincount(assign, minlength=k)
        moved = counts > 0                                       # empty clusters keep their centroid
        C[moved] = sums[moved] / counts[moved, None]
    return C, np.argmin((C * C).sum(1) - 2 * X @ C.T, axis=1)


class IVF:
    """Inverted file: vectors grouped by nearest centroid; a query scans only nprobe lists."""

    def __init__(self, X, nlist, seed=0):
        self.C, assign = kmeans(X, nlist, seed=seed)
        order = np.argsort(assign, kind="stable")
        self.ids = order                                         # original ids, grouped by list
        self.X = X[order]                                        # each list is one contiguous block
        self.norms = (self.X ** 2).sum(1)
        self.start = np.searchsorted(assign[order], np.arange(nlist + 1))

    def search(self, q, k=10, nprobe=1):
        dc = (self.C * self.C).sum(1) - 2 * self.C @ q
        probe = np.argpartition(dc, nprobe - 1)[:nprobe]          # the nprobe nearest centroids
        rows = np.concatenate([np.arange(self.start[c], self.start[c + 1]) for c in probe])
        d2 = self.norms[rows] - 2 * self.X[rows] @ q              # squared L2 minus the constant |q|^2
        top = np.argsort(d2)[:k]
        return self.ids[rows[top]], len(rows)
```

Tested: assignments match the nearest centroid, every id appears in exactly one list, and with nprobe = nlist the results equal brute force.

## Pitfalls

- **Training on too little, or unrepresentative, data.** k-means on 1,000 vectors for 4,096 lists gives junk centroids. Respect the 30 × nlist minimum and train on a random sample, not the first rows loaded (often one tenant or one day).
- **Never retraining.** If new data drifts away from the training distribution, it piles into a few lists: scanned share and latency grow while recall falls. Monitor list sizes and retrain.
- **Trusting the default nprobe.** FAISS's nprobe and pgvector's `ivfflat.probes` both default to 1: fast, with poor recall. Sweep it on your own queries.
- **Empty clusters.** Lloyd's algorithm can empty a cluster. The template keeps the old centroid; FAISS re-seeds it by splitting a large cluster. Either way, check for empty lists.
- **Filtering after the scan.** With `WHERE tenant = 42` applied after an approximate scan, a selective filter can leave fewer than k results; pgvector's iterative index scans and the AI page's [filtering lesson](https://learningcurie.github.io/code-study-tracker/ai.html#l-l-embeddings-metadata-filtering-and-multi-tenancy) cover the fixes.

## Check yourself

Q: 1,000,000 vectors of dimension 256, nlist = 1,000, nprobe = 10, equal lists. How many distance computations per query, against brute force?
A: 1,000 centroids + 10 lists × 1,000 vectors = 11,000 distances, against 1,000,000 for brute force: about 90 times fewer. In practice somewhat more are scanned, because the probed lists tend to be the larger ones.

Q: Why is recall exactly 1 at nprobe = nlist, yet well below 1 at nprobe = 1 even with perfect k-means?
A: At nprobe = nlist every list is scanned exactly, which is brute force. At nprobe = 1, any true neighbour just across a cell boundary (closer to the query, but nearer to another centroid) is never examined. k-means minimises the average distance to centroids; it does nothing about boundaries, and many queries land near one.

Q: You raised nlist from 141 to 566 and recall at nprobe = 4 went up while the scanned share went down. How?
A: Finer cells follow the data's clusters more closely, so the 4 nearest cells contain more of the true neighbours, while each cell holds a quarter as many vectors. On the lab data: recall 0.854 at 3.6% scanned with 141 lists, 0.944 at 0.7% with 566. The price is ranking 566 centroids per query and a longer k-means.

## Lab

- Measure the boundary effect. Build `IVF(X, nlist=141)` on the lab data and, for each query, find where the list holding each true neighbour ranks among the query's nearest centroids. Expected: 75.7% of true neighbours are in the nearest list, 85.4% within the nearest 4 and 94.1% within the nearest 16, equal to recall@10 at nprobe = 1, 4 and 16.
- Find the knee. Sweep nprobe over 1, 2, 4, 8, 16, 32 for nlist = 141 and nlist = 566, recording recall and scanned share. Expected: 566 lists reach 0.944 at nprobe = 4 while scanning 0.7%; 141 lists need nprobe = 16 and 14% for 0.941.

> [!know]
> You now know how IVF turns k-means into an index, why nlist near √n balances the centroid and list costs, and how nprobe trades latency for recall.

=== primer | How does product quantisation shrink a vector to a few bytes and still rank it? | 18 min
goal: Train product-quantisation codebooks, encode vectors into m bytes, rank codes with asymmetric distance tables, and combine PQ with IVF lists and exact re-ranking
tag: vectors-pq | Product quantisation and ADC tables
link: Jégou, Douze and Schmid: Product quantization for nearest neighbor search | https://www.irisa.fr/texmex/people/jegou/papers/jegou_searching_with_quantization.pdf | 25 min: section II-B (product quantisers), III-A (symmetric and asymmetric distances with Figure 2) and IV (IVFADC: a coarse quantiser plus PQ codes of residuals)
link: AI page: Vector compression, quantisation and rescoring | https://learningcurie.github.io/code-study-tracker/ai.html#l-l-embeddings-vector-compression-quantisation-and-rescoring | 5 min: where PQ sits next to int8 and binary quantisation, and how oversampling and rescoring look in pgvector and Qdrant

> [!key]
> **Product quantisation (PQ)** splits each d-dimensional vector into m sub-vectors, runs k-means with 256 centroids in each sub-space, and stores only the m centroid ids: m bytes instead of 4d. To rank stored codes against a query, build an **ADC table** once per query, the squared distance from each query sub-vector to each of the 256 centroids (m × 256 numbers); each stored vector's approximate distance is then m table lookups and additions. **IVF-PQ** files the codes in IVF lists and encodes the residual (vector minus its list's centroid), and an exact re-rank of a few hundred candidates restores most of the lost ordering.

## Intuition

Describe a colour by naming the closest crayon in a box of 256: one byte instead of three numbers. One box cannot describe a 64-number vector well, since 256 crayons for a 64-dimensional space is hopelessly coarse. But 8 boxes, one for each block of 8 numbers, give 256^8 ≈ 1.8 × 10^19 combinations from only 8 × 256 stored centroids. That is the "product": the codebook is the Cartesian product of small codebooks, so it is enormous while what you train and store stays tiny.

## How it works

### Training and encoding

Split the d dimensions into m contiguous blocks of d/m (d must be divisible by m). For each block j, run k-means with 256 centroids on that block of the training vectors, giving codebook C_j of shape 256 × d/m. To encode x, pick the nearest centroid in each block: the code is (c_1, ..., c_m), one byte each. Decoding concatenates the chosen centroids.

### Asymmetric distance computation (ADC)

Squared L2 distance splits over blocks: ‖q − x‖² = Σ_j ‖q_j − x_j‖². Replace x_j by its centroid C_j[c_j] and the distance becomes Σ_j T[j][c_j], where T[j][i] = ‖q_j − C_j[i]‖² is the ADC table. It costs 256 × d multiply-adds per query, independent of n. Scanning n codes then costs n × m lookups and additions, with no multiplications. "Asymmetric" because the query stays exact and only the stored side is quantised. The symmetric version (SDC) also quantises the query and reads centroid-to-centroid tables; it is less accurate for no memory saving worth having, and the paper recommends ADC. On the lab data with m = 8: recall@10 of 0.464 with ADC against 0.276 with SDC.

ADC is exact *for the reconstruction*: Σ_j T[j][c_j] equals ‖q − decode(x)‖², which the template's test checks. The only error is x's quantisation error.

### IVF-PQ (IVFADC)

Combine with the previous card: a k-means coarse quantiser with nlist lists, and in each list the PQ codes of the **residual** r = x − centroid. Residuals are smaller than the vectors themselves (here mean ‖r‖² was 0.74 against ‖x‖² = 1; on image descriptors the reduction is larger), so the same bytes describe them more precisely. For each probed list c, build the table from q − centroid_c, one table per probed list, and scan the list's codes. This is FAISS's IndexIVFPQ, which encodes residuals by default (`by_residual = True`) and is written "IVF4096,PQ64" in its index factory strings.

### Re-ranking

PQ scrambles the fine order near the top, but the true neighbours stay near the top. So take the top 100 by ADC and re-rank them with full vectors held in RAM, on disk, or as a second finer code. With m = 8 on the lab data, the ADC top 10 held 46% of the true top 10, the ADC top 100 held 94%, and re-ranking those 100 exactly gave recall@10 of 0.937.

## Cost

Measured on the lab data (20,000 × 64, 256 centroids per block):

| | float32 | PQ, m = 8 | PQ, m = 16 |
|---|---|---|---|
| Bytes per vector | 256 | 8 (32× smaller) | 16 (16× smaller) |
| Mean ‖x − decode(x)‖² (with ‖x‖² = 1) | 0 | 0.292 | 0.088 |
| recall@10 from ADC alone | 1.000 | 0.464 | 0.660 |
| recall@10 after exact re-rank of the ADC top 100 | 1.000 | 0.937 | 0.996 |
| Training (NumPy) | none | 4.1 s | 7.9 s |

Per query, flat PQ costs 256 × d multiply-adds for the table and n × m lookups. With m = 8 the table is 8 × 256 floats, 8 KB, so it stays in L1 cache; that is why production scanners are fast, and FAISS's 4-bit "fast-scan" codes go further by keeping 16-entry tables inside SIMD registers. In NumPy, the gather `table[np.arange(m), codes]` was slower than a float32 matrix-vector product on this small dataset (3.4 ms against 0.6 ms), because fancy indexing is not a SIMD lookup: do not judge PQ's speed from NumPy.

Memory is the point. One billion 128-dimensional vectors take 512 GB as float32 and 16 GB as 16-byte codes. The DiskANN paper keeps codes like these (for example 32 bytes per point) in RAM while the full vectors stay on SSD.

## When to use it

- **Memory decides the cost** (billions of vectors, or RAM-bound replicas): PQ gives 16× to 64× compression and, with re-ranking, keeps most of the recall.
- **Inside other indexes:** IVF-PQ is the classic billion-scale index in FAISS and Milvus (IVF_PQ); DiskANN keeps PQ codes in RAM to steer its SSD graph search; Qdrant offers product quantisation as one of its compression modes (up to 64× in its documentation).
- **When not:** collections that fit in RAM as float32, float16 or int8, where scalar int8 quantisation keeps far more quality at 4× (the AI page's compression lesson); or when you cannot afford the training step and the re-ranking.

| | Scalar int8 | Binary (1 bit per dimension) | PQ (m bytes) |
|---|---|---|---|
| Compression of a 768-dim float32 vector | 4× | 32× | 3,072 / m: 48× at m = 64 |
| Training | a range per dimension | none | m runs of k-means |
| Distance | int8 dot product | Hamming: XOR and popcount | m table lookups |
| Typical role | the first thing to try | candidate filter, then rescoring | billion scale, IVF-PQ, DiskANN |

## Worked trace

d = 4 split into m = 2 blocks, with only 2 centroids per block (instead of 256) so everything fits:

```steps
Codebooks. Block 0 (dims 0-1) has centroids (0,0) and (1,1); block 1 (dims 2-3) has (1,0) and (0,2)
    C0[0] = (0, 0)    C0[1] = (1, 1)
    C1[0] = (1, 0)    C1[1] = (0, 2)
---
Encode x = (0.9, 0.8 | 0.1, 1.7). Block 0 is nearest C0[1], block 1 nearest C1[1]; the stored code is two ids
    x     (0.9, 0.8)   (0.1, 1.7)
    code      {{1}}            {{1}}         decodes to (1, 1, 0, 2)
---
A query arrives, q = (1.0, 0.5 | 0.0, 1.0). Build the ADC table once: squared distance from each query block to each centroid
    T[0] = [ |(1,0.5)-(0,0)|², |(1,0.5)-(1,1)|² ] = [1.25, 0.25]
    T[1] = [ |(0,1)-(1,0)|²,   |(0,1)-(0,2)|²   ] = [2.00, 1.00]
---
Score code (1, 1): two lookups and one addition, no multiplications
    T[0][1] + T[1][1] = 0.25 + 1.00 = {{1.25}}
---
Check: 1.25 is exactly |q - (1, 1, 0, 2)|². The true |q - x|² is 0.60; the difference is x's quantisation error
    |q - decode(x)|² = 0 + 0.25 + 0 + 1 = 1.25      |q - x|² = 0.60
---
The same table scores every possible code. With 256 centroids and m = 8 it has 2,048 entries and each stored vector costs 8 lookups
    (0,0) {{3.25}}   (0,1) {{2.25}}   (1,0) {{2.25}}   (1,1) {{1.25}}
```

## Template

```python
import numpy as np

# kmeans(X, k, iters, seed) is the function from the IVF card


class PQ:
    """Product quantiser: split vectors into m sub-vectors; store each as the id of its nearest of ks centroids."""

    def __init__(self, X, m=8, ks=256, seed=0):
        assert X.shape[1] % m == 0 and ks <= 256              # ids must fit in one byte
        self.m, self.ds = m, X.shape[1] // m
        self.books = np.stack([kmeans(self.sub(X, j), ks, seed=seed + j)[0]
                               for j in range(m)])            # shape (m, ks, ds)

    def sub(self, X, j):
        return X[:, j * self.ds:(j + 1) * self.ds]

    def encode(self, X):
        codes = np.empty((len(X), self.m), dtype=np.uint8)
        for j, book in enumerate(self.books):
            S = self.sub(X, j)
            codes[:, j] = np.argmin((book * book).sum(1) - 2 * S @ book.T, axis=1)
        return codes

    def decode(self, codes):
        return np.hstack([self.books[j][codes[:, j]] for j in range(self.m)])

    def table(self, q):
        """ADC table: squared distance from each query sub-vector to each centroid, shape (m, ks)."""
        return ((self.books - q.reshape(self.m, 1, self.ds)) ** 2).sum(2)

    def adc(self, table, codes):
        """Approximate squared distances: m table lookups and adds per stored vector."""
        return table[np.arange(self.m), codes].sum(1)


class IVFPQ:
    """IVF lists holding PQ codes of residuals (vector minus its list centroid)."""

    def __init__(self, X, nlist, m=8, seed=0):
        self.C, assign = kmeans(X, nlist, seed=seed)
        R = X - self.C[assign]                                # residuals are small: easier to quantise
        self.pq = PQ(R, m, seed=seed)
        order = np.argsort(assign, kind="stable")
        self.ids, self.codes = order, self.pq.encode(R[order])
        self.start = np.searchsorted(assign[order], np.arange(nlist + 1))

    def search(self, q, k=10, nprobe=8):
        dc = ((self.C - q) ** 2).sum(1)
        dists, ids = [], []
        for c in np.argpartition(dc, nprobe - 1)[:nprobe]:
            a, b = self.start[c], self.start[c + 1]
            T = self.pq.table(q - self.C[c])                  # residual query: one table per list
            dists.append(self.pq.adc(T, self.codes[a:b]))
            ids.append(self.ids[a:b])
        d, i = np.concatenate(dists), np.concatenate(ids)
        return i[np.argsort(d)[:k]]
```

Tested: ADC distances equal the exact distances to the decoded vectors, codes pick the nearest centroid in every block, and with every list probed IVF-PQ ranks exactly by distance to the reconstructions. On the lab data IVF-PQ with m = 8 and nprobe = 8 reached recall@10 of 0.50 (nlist = 141) and 0.56 (nlist = 400) before re-ranking.

## Pitfalls

- **d not divisible by m, or blocks of very unequal importance.** Pad the vectors, or rotate them first: OPQ learns a rotation that balances the blocks, and FAISS's guidelines put it in front of PQ.
- **Too little training data.** 256 centroids per block need thousands of training vectors; FAISS warns below 39 × 256 = 9,984.
- **No re-ranking.** Flat PQ recall@10 of 0.46 looks like a broken index; it is what 8 bytes buy. Always measure how many true neighbours sit inside the PQ top R, and re-rank.
- **Choosing SDC because it looks tidier.** Quantising the query throws information away and saves nothing that matters; use ADC.
- **One table for all lists in IVF-PQ.** With residual codes, the table depends on each list's centroid; reusing one table gives wrong distances. FAISS speeds this up with precomputed terms, described in its implementation notes.

## Check yourself

Q: How much memory do PQ codes take for 100 million 768-dimensional vectors with m = 96, and how big is the ADC table per query?
A: 100,000,000 × 96 bytes = 9.6 GB, against 307 GB as float32 (32× smaller). The table is 96 × 256 = 24,576 floats, about 98 KB, built with 256 × 768 ≈ 197,000 multiply-adds per query.

Q: Why does ADC give exactly ‖q − decode(x)‖² and not an approximation of it?
A: Squared L2 distance is a sum over dimensions, so it splits into a sum over the m blocks. The decoded vector's block j is exactly C_j[c_j], and T[j][c_j] is exactly ‖q_j − C_j[c_j]‖², so the sum of lookups is the exact distance to decode(x). The only approximation is that decode(x) differs from x.

Q: Your IVF-PQ index gives recall@10 of 0.5, and the true neighbours appear in the ADC top 100 95% of the time. What do you change first?
A: Keep the index and add a re-ranking step: take the top 100 by ADC and recompute exact distances with the full vectors (from disk, or a refinement index such as FAISS's IndexRefineFlat). Recall@10 then rises to about the 0.95 that the top 100 contains. Raising m also helps, but costs memory for every vector.

## Lab

- Score by hand, then in code. With the trace's codebooks, encode x = (0.2, 0.1, 0.9, 0.2) and compute its ADC distance to q = (1.0, 0.5, 0.0, 1.0). Expected: code (0, 0), ADC distance T[0][0] + T[1][0] = 1.25 + 2.00 = 3.25, true squared distance 2.25. Check with `T = ((books - q.reshape(2, 1, 2)) ** 2).sum(2)`.
- Measure the re-rank. Train `PQ(X, m=8)` on the lab data, take the ADC top 100 for each query and re-rank exactly. Expected: recall@10 of about 0.46 from ADC alone and 0.94 after re-ranking; with m = 16, about 0.66 and 0.996.

> [!know]
> You now know how PQ compresses vectors into m bytes, why an ADC table turns each distance into m lookups, and how IVF-PQ plus re-ranking fits billion-scale collections in memory.

=== primer | How does HNSW find near neighbours with a few hundred distance computations? | 20 min
goal: Implement HNSW's layered best-first search with a candidate min-heap and a result max-heap, explain M, ef_construction and ef_search, and predict its memory and search cost
tag: vectors-hnsw | HNSW: layers and two-heap search
link: Malkov and Yashunin: the HNSW paper (arXiv 1603.09320) | https://arxiv.org/abs/1603.09320 | 30 min: open the PDF; read section 3 (the skip-list idea and the neighbour heuristic, Figure 2), then Algorithms 1, 2, 4 and 5 in section 4 and the paragraphs of 4.1 on mL, Mmax0 and efConstruction
link: AI page: Approximate nearest neighbour search and HNSW | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-approximate-nearest-neighbour-search-and-hnsw | 5 min: the user's view, with the parameter table and pgvector defaults, memory per vector and operating advice on bulk loading, deletes and monitoring recall
link: Daliri et al. 2026: graph-search worst cases | https://arxiv.org/abs/2610.38133 | 5 min: the abstract's lower bound for standard graph search and its distinction from the Steiner-point construction

> [!key]
> HNSW links every vector to a few near but diverse neighbours, and stacks these proximity graphs in layers like a skip list: every node is on layer 0, and a node reaches layer l with probability M^−l, so upper layers are sparse with long links. A search walks greedily down the upper layers to a good entry point, then runs **best-first search** on layer 0 with two heaps: a **min-heap of candidates** to expand and a **max-heap of the ef best results**, stopping when the nearest unexpanded candidate is farther than the worst result. ef_search sets how wide that search is (recall against time), M sets the links per node (recall against memory), and ef_construction sets how carefully the graph is built.

## Intuition

Driving to a house in another city, you take the motorway (few junctions, long hops), then main roads, then streets. HNSW's upper layers are the motorways: few nodes, long links. On the bottom layer you search the street network properly, but you start next door to your destination.

Within one layer the search works like exploring a city with a shortlist: keep the ef best places found so far, always walk on from the most promising place you have not explored yet, and stop when that place is already worse than everything on your shortlist.

## How it works

### Layers: a skip list in many dimensions

Each inserted node draws its top layer l = ⌊−ln(U) × mL⌋ with U uniform in (0, 1]. Then P(l ≥ j) = P(U ≤ e^(−j/mL)) = e^(−j/mL), and with the paper's choice mL = 1 / ln M that is M^(−j): with M = 16, one node in 16 reaches layer 1 and one in 256 reaches layer 2. In 20,000 draws: 1,230 nodes reached layer 1 (expected 1,250), 83 layer 2 (78) and 5 layer 3 (4.9). Summing those probabilities gives an expected M / (M - 1) layers per node, a constant. This is a storage expectation, not a worst-case bound on search work.

### Searching one layer: best-first with two heaps (Algorithm 2)

The state is a `visited` set, `candidates` (a min-heap by distance: the frontier to expand) and `results` (a max-heap by distance holding at most ef entries: the answer so far).

1. Pop the nearest candidate c.
2. If c is farther than the worst result, stop.
3. Otherwise, for each unvisited neighbour e of c: mark it visited and compute its distance; if `results` holds fewer than ef entries or e beats the worst result, push e onto both heaps, and if `results` now holds ef + 1 entries, pop its worst.

Each step needs the nearest candidate and the farthest kept result. The result heap has at most ef entries, but the candidate heap and visited set can grow larger; a candidate-heap operation costs O(log C) for its current size C, not necessarily O(log ef). This is best-first search, like Dijkstra's algorithm with "distance to the query" as the priority. The stopping rule is a heuristic, not a proof: a far candidate could link to something near. A larger ef generally explores more and improves recall, but does not impose a strict bound on total work. Python's `heapq` is a min-heap, so the template stores negated distances in `results`.

### The full search (Algorithm 5)

Start at the entry point on the top layer. On each upper layer run the layer search with ef = 1 (a pure greedy walk) and use its answer as the entry point one layer down. On layer 0 run it with ef = max(ef_search, k) and return the k best.

### Insertion (Algorithm 1) and the neighbour heuristic (Algorithm 4)

Draw the new node's level l. Walk greedily (ef = 1) down to layer l + 1; then on each layer from min(l, top) down to 0, run the layer search with ef_construction and choose M neighbours with the **heuristic**: go through the candidates nearest first and keep one only if it is closer to the new node than to every neighbour already kept. That prefers neighbours in *different directions* over the M absolute nearest, which might all sit in one clump; it keeps bridges between clusters and approximates a relative neighbourhood graph. Links go both ways. When a neighbour's list exceeds its cap (Mmax = M on upper layers, Mmax0 = 2M on layer 0, as the paper recommends), it is pruned with the same heuristic.

## Cost

- **Search.** The paper argues for O(log n) scaling (a bounded number of hops per layer, about log n layers) and confirms it on low-dimensional data; in high dimensions it is an empirical observation. What you control is ef: the work is roughly the number of expansions times the degree. Measured with this card's template on the lab data (20,000 × 64, M = 16, ef_construction = 100), next to hnswlib built with the same settings:

  Daliri et al. (October 2026, preprint) prove that standard greedy graph-based ANN methods, including flat and hierarchical variants, cannot guarantee sublinear worst-case query time for Euclidean approximate nearest-neighbour search. Their construction with extra Steiner points has different theoretical guarantees. This does not contradict the strong measured performance of HNSW on many real datasets, and is not a recommendation to replace a production index.

| ef_search | recall@10 (template) | distances per query | recall@10 (hnswlib) |
|---|---|---|---|
| 10 | 0.882 | 324 (1.6% of n) | 0.877 |
| 20 | 0.943 | 470 (2.4%) | 0.949 |
| 40 | 0.974 | 758 (3.8%) | 0.976 |
| 80 | 0.990 | 1,377 (6.9%) | 0.988 |
| 160 | 0.997 | 2,629 (13.1%) | 0.996 |

As the collection grew at fixed ef = 40, the work barely moved: 614 distances per query at n = 1,250, 723 at 2,500, 794 at 5,000, 796 at 10,000 and 758 at 20,000, with recall steady at 0.97, while brute force grew 16-fold. hnswlib (C++) answered ef = 40 queries in about 0.1 ms on one core against 0.56 ms for the NumPy brute force; the Python template took 1.7 ms because each small distance batch pays interpreter overhead.

- **Build.** Each insert first descends the upper graph layers, then searches with ef_construction on the new node's layers and applies the neighbour heuristic; the paper reports O(n log n) on low-dimensional data. The template needed 2,432 distance computations per insert and 147 s in Python; hnswlib built the same index in 6.8 s on one core.
- **Memory.** The vectors plus links. With Mmax0 = 2M, Mmax = M and all layer caps filled, the expected link capacity is 2M + M / (M - 1) ids per node: about 33.1 ids, or 132 bytes at 4 bytes per id, for M = 16. Actual link counts and implementation overhead vary. The paper estimates 60 to 450 bytes per object for M between 6 and 48; FAISS's guidelines count (d × 4 + M × 2 × 4) bytes per vector.

## When to use it

- **The default when the vectors fit in RAM** and you want high recall at low latency: it is the graph index in pgvector, Qdrant (its only dense index), Milvus, FAISS (IndexHNSWFlat) and hnswlib.
- **Tune in this order:** ef_search first, at query time, with no rebuild (pgvector `hnsw.ef_search`, default 40; FAISS efSearch, default 16; hnswlib `ef`, default 10). Then M and ef_construction, which need a rebuild. The paper suggests M from 5 to 48, smaller for low dimensions or low recall, larger for high dimensions or high recall, and an ef_construction large enough that recall during construction is close to 1 (0.95 is enough for most uses).
- **Watch for:** RAM (graph and full vectors; compress with the previous card's codes or scalar quantisation, or move to DiskANN), slow builds, deletions (FAISS's HNSW cannot remove vectors; hnswlib marks them deleted and leaves them out of results), and selective filters, which disconnect the walk (Qdrant adds extra edges for indexed payload fields; pgvector rescans iteratively).

## Worked trace

A layer-0 graph of eight nodes, query q = (6, 5), ef = 3, entering at A. Numbers are squared distances to q.

```text
6 |                            H          edges: A-B A-C B-C B-D C-E D-E
5 |                    G   q                     D-F E-G F-G F-H G-H
4 |            E
3 |    C                   F              d² to q: A 61  B 32  C 29  D 13
2 |                D                               E 10  F 4   G 1   H 2
1 |        B
0 |A
  +--------------------------------
   0   1   2   3   4   5   6   7
```

```steps
Start: A is the entry point, visited and in both heaps
    candidates (min-heap)  A 61
    results (max-heap)     A 61                worst = 61
---
Pop A (61). Results hold fewer than ef = 3, so both neighbours enter both heaps
    candidates  C 29, B 32
    results     {{A 61}}, B 32, C 29           worst = 61
---
Pop C (29 < 61). Its new neighbour E (10) beats the worst: push it, evict A
    candidates  E 10, B 32
    results     {{B 32}}, C 29, E 10           worst = 32
---
Pop E (10). New neighbours D (13) and G (1) both beat the worst: B, then C, are evicted
    candidates  G 1, D 13, B 32
    results     {{D 13}}, E 10, G 1            worst = 13
---
Pop G (1). New neighbours F (4) and H (2) enter; D and E are evicted
    candidates  H 2, F 4, D 13, B 32
    results     {{F 4}}, H 2, G 1              worst = 4
---
Pop H (2), then F (4): all their neighbours are already visited, nothing changes
    candidates  D 13, B 32
    results     F 4, H 2, G 1                  worst = 4
---
Pop D (13): 13 > worst 4, so stop. B is never expanded. Return the k best: G, H, F
    answer  {{G 1, H 2, F 4}}
```

## Template

```python
import heapq
import math
import random

import numpy as np


class HNSW:
    """Hierarchical navigable small world graph, squared L2 (Malkov and Yashunin, Algorithms 1, 2, 4, 5)."""

    def __init__(self, X, M=16, ef_construction=100, seed=0):
        self.X, self.M, self.M0, self.efc = X, M, 2 * M, ef_construction
        self.mL = 1 / math.log(M)                     # P(level >= l) = M ** -l
        self.rng = random.Random(seed)
        self.links = []                               # links[layer][node] -> list of neighbour ids
        self.entry, self.top, self.ndist = None, -1, 0
        for i in range(len(X)):
            self.insert(i)

    def dist(self, q, ids):
        self.ndist += len(ids)
        diff = self.X[ids] - q
        return np.einsum("ij,ij->i", diff, diff)

    def search_layer(self, q, entries, ef, layer):
        """Best-first search with two heaps. Returns up to ef (dist, id) pairs, nearest first."""
        visited = set(entries)
        cand = list(zip(self.dist(q, entries).tolist(), entries))  # min-heap: nearest to expand next
        heapq.heapify(cand)
        res = [(-d, e) for d, e in cand]                           # max-heap: worst kept result on top
        heapq.heapify(res)
        while len(res) > ef:
            heapq.heappop(res)
        while cand:
            d, c = heapq.heappop(cand)
            if d > -res[0][0]:
                break                                 # nearest candidate is worse than every result
            new = [e for e in self.links[layer][c] if e not in visited]
            visited.update(new)
            if not new:
                continue
            for de, e in zip(self.dist(q, new).tolist(), new):
                if len(res) < ef or de < -res[0][0]:
                    heapq.heappush(cand, (de, e))
                    heapq.heappush(res, (-de, e))
                    if len(res) > ef:
                        heapq.heappop(res)
        return sorted((-d, e) for d, e in res)

    def select(self, cands, M):
        """Neighbour heuristic: keep a candidate only if it is closer to the base than to all kept ones."""
        kept = []
        for d, e in cands:                            # nearest first
            if len(kept) == M:
                break
            if not kept or (self.dist(self.X[e], kept) >= d).all():
                kept.append(e)
        return kept

    def insert(self, i):
        q = self.X[i]
        level = int(-math.log(1.0 - self.rng.random()) * self.mL)
        while len(self.links) <= level:
            self.links.append({})
        for layer in range(level + 1):
            self.links[layer][i] = []
        if self.entry is None:
            self.entry, self.top = i, level
            return
        ep = [self.entry]
        for layer in range(self.top, level, -1):      # above the new node's level: greedy, ef = 1
            ep = [self.search_layer(q, ep, 1, layer)[0][1]]
        for layer in range(min(self.top, level), -1, -1):
            W = self.search_layer(q, ep, self.efc, layer)
            self.links[layer][i] = self.select(W, self.M)
            cap = self.M0 if layer == 0 else self.M
            for e in self.links[layer][i]:            # link back; shrink lists that grew too long
                nb = self.links[layer][e]
                nb.append(i)
                if len(nb) > cap:
                    self.links[layer][e] = self.select(sorted(zip(self.dist(self.X[e], nb).tolist(), nb)), cap)
            ep = [e for _, e in W]
        if level > self.top:
            self.entry, self.top = i, level

    def search(self, q, k=10, ef=50):
        ep = [self.entry]
        for layer in range(self.top, 0, -1):          # zoom in through the sparse upper layers
            ep = [self.search_layer(q, ep, 1, layer)[0][1]]
        return [e for _, e in self.search_layer(q, ep, max(ef, k), 0)[:k]]
```

Tested on random data (degree caps hold, links stay within their layer, recall@10 above 0.95) and on graphs of 1 to 5 nodes. `self.ndist` counts distance computations, so you can measure the work directly.

## Pitfalls

- **ef smaller than k.** The result heap holds ef items, so it cannot return k results when ef < k; use max(ef, k), as the template and the libraries do.
- **Stopping on the wrong comparison.** Compare the nearest *candidate* with the farthest *result*. Comparing with the nearest result stops after one step.
- **Marking nodes visited too late.** Mark a neighbour visited when it is first seen, not when it is expanded, or the same node is measured many times.
- **Keeping the M nearest instead of using the heuristic.** On clustered data the M nearest all sit in one cluster and the graph can split into islands; the heuristic keeps the bridges (the paper's Figure 2).
- **Comparing builds on one seed.** Random levels and insertion order change the graph; compare configurations over a few seeds.
- **Removing nodes outright.** Deleting a node can disconnect parts of the graph, which is why libraries mark deletions and repair or rebuild later.

## Check yourself

Q: Rerun the trace with ef = 1 instead of 3. Which nodes are expanded and what is returned?
A: With ef = 1 only the single best result is kept. From A, C (29) becomes the result; expanding C finds E (10); expanding E finds G (1), while D (13) is not good enough to enter; expanding G finds F (4) and H (2), neither better than 1. B (32) is then worse than G, so the search stops: expanded A, C, E, G, returned G. Here greedy still finds the true nearest, but with no second-best kept there is no backtracking, so in a less friendly graph it can stop at a local minimum.

Q: With M = 32 and mL = 1 / ln M, what share of nodes appear on layer 2 or above, and how many ids does a node store on average?
A: P(l ≥ 2) = M^−2 = 1/1,024, about 0.1%. On average a node stores Mmax0 + mL × Mmax = 64 + 32 / ln 32 ≈ 64 + 9.2 = 73.2 ids, about 293 bytes with 4-byte ids.

Q: Your HNSW index gives recall@10 of 0.90 and you need 0.98. Which parameter do you change first, and how do you know when to change the others?
A: Raise ef_search first: it costs only query time and needs no rebuild, so sweep it (for example 40, 80, 160) and plot recall against latency. If recall flattens below 0.98, or the ef needed makes queries too slow, the graph itself is the limit: rebuild with a larger M (more links, more memory) or a larger ef_construction (better neighbour choices, slower build).

## Lab

- Watch the work stay flat. Build the template's `HNSW` (M = 16, ef_construction = 100) on the first 2,500, 5,000 and 10,000 lab vectors, reset `ndist` before each query, and average it over 200 queries at ef = 40. Expected: about 723, 794 and 796 distance computations per query, with recall@10 near 0.97 throughout; the share of the collection measured halves each time n doubles.
- Count the layers. Draw 20,000 levels with `random.Random(0)` and l = ⌊−ln(1 − U) / ln 16⌋. Expected: 1,230 nodes at layer 1 or above, 83 at layer 2 or above and 5 at layer 3, against 1,250, 78 and 4.9 from M^−l.

> [!know]
> You now know how HNSW's layers give a good entry point, how best-first search with two heaps and ef finds neighbours with a few hundred distance computations, and which parameter to tune first.

=== primer | How does DiskANN search a billion vectors from an SSD? | 18 min
goal: Explain Vamana's robust pruning with α and its two-pass build, implement greedy and beam search, and explain how DiskANN's layout keeps a query to a few dozen SSD reads
tag: vectors-diskann | Vamana graphs and DiskANN
link: Subramanya et al.: DiskANN (NeurIPS 2019) | https://proceedings.neurips.cc/paper_files/paper/2019/file/09853c7fb1d3f8ee67a61b6bf4a7f8e6-Paper.pdf | 30 min: section 2.2-2.4 (RobustPrune, the Vamana algorithm and how it differs from HNSW and NSG), then section 3 (overlapping-cluster build, disk layout, beam search, caching and implicit re-ranking) and the SIFT1B results in 4.3-4.4

> [!key]
> In-memory indexes are limited by RAM: a billion 128-dimensional float vectors take 512 GB before any graph. DiskANN keeps only **PQ codes in RAM** (tens of bytes per vector) and stores each vector's **full coordinates and neighbour list together in one fixed-size record on SSD**. Its graph, **Vamana**, is built with **RobustPrune**, which drops a candidate neighbour p′ once an already chosen neighbour p* satisfies α · d(p*, p′) ≤ d(p, p′); with α > 1 more long edges survive, so searches need fewer hops. A **beam search** reads the W most promising records per SSD round trip, steering by PQ distances and re-ranking with the full vectors that arrived in the same reads.

## Intuition

An SSD needs a few hundred microseconds to serve a random read, but it can serve hundreds of thousands of reads per second if you ask for many at once. So the cost of a graph search on SSD is not distance computations but **round trips**: every hop that must wait for the previous one pays a full read latency. Two ideas follow. Make paths short, by keeping some long edges in the graph. And make each round trip count, by fetching several promising nodes at once and getting everything about a node (its vector and its neighbours) in a single read.

## How it works

### GreedySearch (Algorithm 1)

The same best-first search as HNSW's layer 0: keep a candidate list of at most L nodes, repeatedly expand the nearest unexpanded one, add its neighbours, and trim the list back to the L closest. It returns the k nearest found and the set of all visited nodes; the build uses the visited set.

### RobustPrune (Algorithm 2)

To choose at most R out-neighbours for p from candidates V (together with p's current neighbours):

1. Let p* be the candidate nearest p; add the edge p → p*.
2. Remove every candidate p′ with α · d(p*, p′) ≤ d(p, p′): p′ is "covered", because going through p* already gets you α times closer to p′ than p is.
3. Repeat until p has R edges or no candidates remain.

With α = 1 this is HNSW's neighbour heuristic; the paper points out that HNSW and NSG implicitly use α = 1. With α > 1 the removal test is harder to pass, so fewer candidates are removed and longer edges survive. The paper's argument: if every node chose its neighbours this way from all other points, a greedy search would reach any data point in a logarithmic number of steps when α > 1, because each step brings it closer by a constant factor.

### The Vamana build (Algorithm 3)

1. Start from a random graph with R out-edges per node, and take the medoid as the search start s (DiskANN's code uses the point closest to the centroid).
2. For each point p in random order: run GreedySearch(s, x_p, 1, L), then RobustPrune(p, visited, α, R). For each new neighbour j, add the back edge j → p; if j now has more than R edges, run RobustPrune on j.
3. Make two passes, the first with α = 1 and the second with the chosen α.

The differences from HNSW (section 2.4 of the paper): pruning considers *every visited node*, not just the final candidate list, which brings in long edges; there is no hierarchy; the start is a random graph instead of an empty one; there are two passes; and α is tunable.

### The SSD system (section 3)

- **Layout.** For each point, its full-precision vector followed by up to R neighbour ids, padded to a fixed size, so the record for point i is at offset i × record size and needs no offset table in RAM. With degree 128, the ids take 4 × 128 = 512 bytes and share a 4 KB sector with the vector.
- **RAM.** PQ codes for every point (for example 32 bytes), used for the approximate distances that steer the search.
- **BeamSearch.** Expand the W best unvisited candidates per round with W parallel reads. W = 1 is plain greedy search; the paper found W of 2 to 8 a good balance, while 16 or more wastes compute and SSD bandwidth.
- **Caching.** Keep the nodes within C = 3 or 4 hops of the start in DRAM, since every search passes through them.
- **Implicit re-ranking.** The full vector arrives in the same read as the neighbour list, so the final top k is ranked by exact distances at no extra I/O.
- **Building a billion-point graph in 64 GB.** k-means into 40 clusters, each point assigned to its 2 nearest; a Vamana graph per cluster; then the union of all edges. The overlap keeps the merged graph connected.

On SIFT1B (one billion 128-byte vectors) the paper reports more than 5,000 queries per second at under 3 ms mean latency and 95%+ 1-recall@1 on a 16-core workstation with 64 GB of RAM, where compression-based IVF methods of similar memory plateaued around 50% 1-recall@1.

## Cost

- **RAM:** n × m bytes of PQ codes plus the cache: one billion points at 32 bytes is 32 GB.
- **SSD:** n × record size; the paper's merged billion-point index took 348 GB.
- **Per query:** records read ≈ nodes expanded (about L, a little more with a wide beam); round trips ≈ reads / W; PQ distances for every neighbour of every expanded node; one exact distance per expanded node.

Measured with this card's template on the first 10,000 lab vectors (R = 32, build L = 64, α = 1.2; PQ with m = 16, so 16 bytes per vector in "RAM" against 256 bytes of float32; search L = 40):

| beam width W | recall@10 | round trips | records read | read at 4 KiB per record |
|---|---|---|---|---|
| 1 | 0.963 | 45.2 | 45 | 181 KiB |
| 2 | 0.963 | 24.4 | 47 | 188 KiB |
| 4 | 0.965 | 14.2 | 51 | 205 KiB |
| 8 | 0.969 | 9.5 | 61 | 242 KiB |

W = 4 cuts the round trips to a third for about 13% more reads. If a round trip costs 100 µs, that is 4.5 ms against 1.4 ms of waiting per query. Recall stays high although the search is steered by 16-byte codes, because the final ranking uses the full vectors.

The effect of α shows best where long edges are rare. On 4,000 uniform 2-D points (R = 12, L = 40), α = 1 left a mean out-degree of 3.5 and a pure greedy walk (L = 1) took 27.9 hops on average; α = 1.2 raised the degree to 8.1 and cut the walk to 6.8 hops; α = 2 filled the degree budget (12.0) with less useful edges and the walk grew back to 11.0 hops. On the 64-dimensional lab data the α = 1 graph already had a mean out-degree of 27 out of 32, and α = 1.2 made no measurable difference to recall at equal L (0.975 against 0.970 at L = 40). The paper's gains, 2 to 3 times fewer hops than HNSW and NSG at large degrees, come from large datasets.

## When to use it

- **Bigger than RAM, high recall wanted:** hundreds of millions to billions of vectors on one machine with an NVMe SSD, where IVF-PQ in the same memory plateaus at lower recall.
- **In memory, too:** in the paper's tests Vamana matched or beat HNSW and NSG on SIFT1M, GIST1M and DEEP1M, and built faster.
- **In production:** Milvus's DISKANN index, Azure Cosmos DB's diskANN vector index, Azure SQL's `CREATE VECTOR INDEX` (DiskANN is its only type) and pgvectorscale's StreamingDiskANN for Postgres.
- **When not:** collections that fit comfortably in RAM (in-memory HNSW is simpler), storage with high per-read latency such as network disks (every round trip costs more), and workloads dominated by updates, which the original static design does not address.

| | HNSW in RAM | IVF-PQ in RAM | DiskANN |
|---|---|---|---|
| RAM per vector | vector + about 150 bytes of links | m bytes + 8-byte id | m bytes (+ cache) |
| Where the full vectors live | RAM | nowhere, or on disk for re-ranking | SSD, next to the neighbour lists |
| Recall at a given memory | high, but memory is large | limited by compression | high, re-ranked exactly |
| What a query waits for | memory | memory | SSD round trips |

## Worked trace

RobustPrune for p = 0 on a line, with candidates at 1, 2, 3, −1 and −2.5 (their distances to p are 1, 2, 3, 1 and 2.5), R large:

```steps
alpha = 1. Nearest candidate p* = 1: keep the edge. Remove p' when 1 × d(1, p') <= d(0, p'): 2 (1 <= 2) and 3 (2 <= 3) go
    kept {{1}}       removed 2, 3       left -1, -2.5
---
alpha = 1. Next p* = -1: keep it. -2.5 goes, since d(-1, -2.5) = 1.5 <= 2.5. Done: only the two immediate neighbours remain
    kept 1, {{-1}}   removed -2.5        left (none)
---
With alpha = 1 every point on a line links only to its neighbours: a path graph. A greedy walk from one end to the other takes n - 1 hops
    0 -> 1 -> 2 -> 3 ...      diameter grows with n
---
alpha = 2. p* = 1 again. Remove p' when 2 × d(1, p') <= d(0, p'): only 2 goes (2 × 1 <= 2). 3 survives: 2 × 2 = 4 > 3
    kept {{1}}       removed 2           left 3, -1, -2.5
---
alpha = 2. p* = -1: nothing more is removed (2 × 1.5 = 3 > 2.5 keeps -2.5). Then p* = -2.5, then p* = 3
    kept 1, -1, {{-2.5, 3}}
---
Result: 0 links to 1, -1, -2.5 and 3. A search from 0 towards 3 now takes one hop instead of three: the long edges are what alpha buys
    alpha = 1: [1, -1]      alpha = 2: [1, -1, -2.5, 3]
```

## Template

```python
import numpy as np


def greedy_search(X, graph, start, q, L, k=1):
    """Algorithm 1 (GreedySearch): returns the k nearest ids found and the set of visited ids."""
    dist = lambda ids: ((X[ids] - q) ** 2).sum(1)
    pool = {start: float(dist([start])[0])}                 # the candidate list, id -> distance
    visited = set()
    while True:
        frontier = [p for p in pool if p not in visited]
        if not frontier:
            break
        p = min(frontier, key=pool.get)                     # nearest unexpanded candidate
        visited.add(p)
        new = [e for e in graph[p] if e not in pool]
        if new:
            pool.update(zip(new, dist(new).tolist()))
        if len(pool) > L:                                   # keep only the L closest
            pool = dict(sorted(pool.items(), key=lambda kv: kv[1])[:L])
    return sorted(pool, key=pool.get)[:k], visited


def robust_prune(X, graph, p, V, alpha, R):
    """Algorithm 2 (RobustPrune): pick at most R out-neighbours of p, keeping long edges when alpha > 1."""
    V = np.array(sorted((set(V) | set(graph[p])) - {p}))
    d_p = np.sqrt(((X[V] - X[p]) ** 2).sum(1))              # true distances: alpha scales a distance
    alive = np.ones(len(V), dtype=bool)
    out = []
    while alive.any() and len(out) < R:
        j = np.flatnonzero(alive)[np.argmin(d_p[alive])]    # closest surviving candidate p*
        out.append(int(V[j]))
        d_star = np.sqrt(((X[V] - X[V[j]]) ** 2).sum(1))
        alive &= alpha * d_star > d_p                       # drop p' when alpha * d(p*, p') <= d(p, p')
    graph[p] = out


def build_vamana(X, R=32, L=64, alpha=1.2, seed=0):
    """Algorithm 3: random R-regular start, then two passes (alpha = 1, then alpha) in random order."""
    rng = np.random.default_rng(seed)
    n = len(X)
    graph = []
    for i in range(n):
        others = rng.choice(n - 1, R, replace=False)
        graph.append([int(j + (j >= i)) for j in others])   # R random out-edges, no self-loop
    start = int(np.argmin(((X - X.mean(0)) ** 2).sum(1)))   # medoid, approximated by the point nearest the mean
    for a in (1.0, alpha):
        for p in rng.permutation(n).tolist():
            _, visited = greedy_search(X, graph, start, X[p], L)
            robust_prune(X, graph, p, visited, a, R)
            for j in graph[p]:                              # backward edges, pruned if j overflows
                if p in graph[j]:
                    continue
                if len(graph[j]) + 1 > R:
                    robust_prune(X, graph, j, graph[j] + [p], a, R)
                else:
                    graph[j].append(p)
    return graph, start


def beam_search(X, graph, start, q, L, W, approx):
    """DiskANN search: approx(ids) ranks candidates from PQ codes in RAM; each round reads the
    W best unvisited nodes' records (full vector + neighbour ids) from SSD in one round trip."""
    pool = {start: float(approx([start])[0])}
    visited, exact, hops = set(), {}, 0
    while True:
        frontier = sorted((p for p in pool if p not in visited), key=pool.get)[:W]
        if not frontier:
            break
        hops += 1
        for p in frontier:
            visited.add(p)
            exact[p] = float(((X[p] - q) ** 2).sum())        # full vector came with the record: re-rank for free
            new = [e for e in graph[p] if e not in pool]
            if new:
                pool.update(zip(new, approx(new).tolist()))
        if len(pool) > L:
            pool = dict(sorted(pool.items(), key=lambda kv: kv[1])[:L])
    return sorted(exact, key=exact.get), hops, len(visited)
```

To steer by PQ codes, pass `approx = lambda ids: pq.adc(pq.table(q), codes[ids])` with the previous card's `PQ` (build the table once per query). Tested on 800 random points: out-degrees stay within R with no self-loops or duplicates, greedy search reaches recall@10 above 0.95, and the line example gives [1, −1] for α = 1.

## Pitfalls

- **Applying α to squared distances.** α · d² ≤ d² is the test for α² on plain distances, a different graph. The template takes square roots before comparing.
- **Forgetting the current neighbours.** RobustPrune works on V together with p's existing out-neighbours (the paper's first line); pruning only the new candidates throws good edges away.
- **A random start node.** Starting from the medoid shortens every search; a random start adds hops to every query.
- **Too wide a beam.** A beam of 16 or more wastes compute and bandwidth, and a backlogged SSD answers more slowly; the paper ran its SSD at 30-40% load with beams of 2 to 8.
- **Returning PQ-ranked results.** The full vectors arrive with each record, so the final ranking should use them; ranking by PQ distances alone gives back the compression error.

## Check yourself

Q: In the trace, for which values of α is point 2 kept as a neighbour of 0?
A: Point 2 is removed by p* = 1 when α · d(1, 2) ≤ d(0, 2), that is α × 1 ≤ 2. So it is kept only for α > 2 (with α = 2.5 the template keeps it, and then 2 itself covers 3, giving [1, −1, 2, −2.5]).

Q: One billion 96-dimensional float32 vectors, degree R = 64, PQ codes of 32 bytes. Estimate RAM and SSD.
A: RAM: 1,000,000,000 × 32 bytes = 32 GB of codes, plus a cache. SSD: each record holds 96 × 4 = 384 bytes of vector and 64 × 4 = 256 bytes of ids, 640 bytes, so about 640 GB. Keeping the full vectors in RAM instead would need 384 GB for the vectors alone.

Q: Why does DiskANN use a beam of 4 rather than a beam of 1 or of 32?
A: A beam of 1 waits a full SSD latency for every hop. A beam of 4 issues four reads per round trip, which costs almost the same time as one, so round trips drop to about a third (45 to 14 in the measurement) for a few more reads. A beam of 32 fetches many nodes that the search would never have expanded, wasting bandwidth and compute and raising latency under load.

## Lab

- Prune by hand. Run `robust_prune` for p = 0 on the 1-D points 0, 1, 2, 3, −1, −2.5 with α = 1, 1.5, 2 and 2.5 (R = 10). Expected: [1, −1], [1, −1], [1, −1, −2.5, 3] and [1, −1, 2, −2.5]. Explain why α = 1.5 changes nothing here: 3 is removed because 1.5 × 2 ≤ 3, and −2.5 because 1.5 × 1.5 ≤ 2.5.
- Sweep the beam. Build `build_vamana(X[:2000], R=32, L=64, alpha=1.2)` on the lab data and run `beam_search` with L = 40 and W = 1, 2, 4, 8, steering with a `PQ(X[:2000], m=16)`. Expected: about 42, 22, 13 and 8 round trips for about 42 to 51 records read, with recall@10 between 0.97 and 0.98.

> [!know]
> You now know how RobustPrune's α keeps long edges, how Vamana builds its graph, and how DiskANN's layout and beam search turn a graph search into a few dozen SSD reads.

=== primer | How do you measure recall@k against latency and choose an index? | 15 min
goal: Build ground truth, compute recall@k correctly, measure latency percentiles, find the Pareto frontier of index configurations and choose an index for a workload
tag: vectors-recall | Recall against latency and index choice
link: FAISS wiki: Guidelines to choose an index | https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index#is-memory-a-concern | 8 min: the question-by-question guide (few searches, exact results, memory, dataset size) with the index string for each answer and the training-set sizes
link: AI page lab: Exact versus HNSW on 100,000 vectors | https://learningcurie.github.io/code-study-tracker/ai.html#l-lab-embeddings-exact-versus-hnsw-on-100-000-vectors | 45 min: the same measurement with FAISS on 100,000 384-dimensional vectors, sweeping ef_search and plotting the curve

> [!key]
> **recall@k** for one query is the share of the true k nearest neighbours (from brute force) that the index returned; average it over held-out queries that come from the same distribution as real ones, never over stored vectors. An approximate index is not one number but a **curve**: sweep its query-time dial (nprobe, ef_search, L) and record recall against latency per query (median and 99th percentile), plus build time and memory. Keep the configurations on the **Pareto frontier**, those that no other configuration beats on both recall and latency, and choose the cheapest one that meets your recall target.

## Intuition

A car's top speed says little without its fuel consumption; a search index's speed says nothing without its recall. Any index can be made fast by returning junk, and any index can be made exact by scanning everything. The useful question is: "for the recall I need, how fast is it, and what does it cost in memory and build time?" That needs a measured curve, not a single benchmark number.

## How it works

### Ground truth

Hold out a set of queries (a few hundred to a few thousand) that look like production queries: real user questions embedded with the same model, not stored documents. Compute their exact top k with brute force (the first card) once and save it. Using stored vectors as queries inflates recall, because each one sits in its own list or bucket at distance 0: on the lab data IVF with nprobe = 1 scored 0.842 with stored vectors as queries against 0.757 with held-out ones.

### The metric

For query i with true set G_i (size k) and returned list X_i, recall@k = |X_i ∩ G_i| / k; average over queries. This is the DiskANN paper's "k-recall@k". Variants you will meet:

- **1-recall@100:** is the true nearest neighbour anywhere in the top 100? Compressed indexes often report it; the DiskANN paper calls it a weaker notion that may not be acceptable in many applications. On the lab data, PQ with m = 8 scored 0.985 on 1-recall@100 but only 0.464 on recall@10.
- **Ties:** with duplicate vectors, two correct answers can contain different ids. Count a returned id as correct if its distance is at most the k-th true distance (plus a small tolerance).
- **Not relevance.** ANN recall measures agreement with exact search. Whether the exact neighbours are *relevant* to the user is a separate question, measured with labelled data (the AI page's [retrieval metrics lesson](https://learningcurie.github.io/code-study-tracker/ai.html#l-l-embeddings-measuring-retrieval-recall-mrr-and-ndcg)).

### Latency, memory and the rest

Warm up first (caches, lazy loading), then time each query separately and report the median and the 99th percentile; tail latency is what users notice. Compare algorithms single-threaded; measure throughput (queries per second) under concurrency separately, since batching and parallel queries change the picture. Record build time, bytes per vector, and whether the index supports inserts, deletes and filters.

### The Pareto frontier

Sort the configurations by latency. Walk through them, keeping each one whose recall beats every faster configuration kept so far. Everything else is dominated: some other setting is both faster and more accurate.

## Cost

- **Ground truth:** nq × n × d multiply-adds, as one batched matrix product. For 1,000 queries over a million 768-dimensional vectors that is 768 billion, minutes on one core and seconds with BLAS on many cores or a GPU; do it once and store the result.
- **Each configuration:** nq queries × the index's query cost, repeated a few times to steady the timings (the table below uses the best of 3 passes).
- **The frontier:** sorting P configurations, O(P log P).

Measured on the lab data with this module's NumPy templates (20,000 × 64, 200 queries, one core):

| configuration | recall@10 | scanned | median ms | on the frontier? |
|---|---|---|---|---|
| brute force | 1.000 | 100% | 0.56 | yes |
| LSH L=32, K=10 | 0.512 | 4.1% | 0.31 | no |
| LSH L=128, K=10 | 0.929 | 14.6% | 1.36 | no |
| IVF 141 lists, nprobe 1 | 0.757 | 0.9% | 0.08 | yes |
| IVF 141 lists, nprobe 4 | 0.854 | 3.6% | 0.15 | yes |
| IVF 141 lists, nprobe 16 | 0.941 | 14.3% | 0.62 | no |
| IVF 566 lists, nprobe 4 | 0.944 | 0.7% | 0.16 | yes |
| IVF 566 lists, nprobe 16 | 0.975 | 3.0% | 0.28 | yes |
| PQ m=16, re-rank top 100 | 0.996 | 100% codes | 4.33 | no |

For comparison, compiled hnswlib on the same data gave 0.976 at about 0.1 ms (ef = 40). Implementation language moves the whole curve, so compare algorithms within one implementation, and libraries with each other.

## When to use it

Measure before choosing, then use this as the starting point:

| Workload | Start with |
|---|---|
| Under about 100,000 vectors, few queries, or filters that leave few rows | exact search (flat) |
| Fits in RAM, needs high recall at low latency | HNSW; sweep ef_search |
| RAM is tight, fast builds, or GPUs | IVF (lists ≈ 4√n to 16√n), or IVF-PQ with re-ranking |
| Larger than RAM, high recall needed | DiskANN (PQ codes in RAM, graph on SSD) |
| Already running Postgres | pgvector HNSW; pgvectorscale for larger collections |

FAISS's guidelines follow the same questions: if you run only a few searches, use Flat; if memory is not a concern, HNSW; as memory gets tighter, IVF with PQ or OPQ codes; and the dataset size picks the number of lists. Revisit the choice as data grows, because recall at fixed settings drifts.

## Worked trace

```steps
Recall for two queries with k = 3. Query 1: true {4, 9, 2}, returned [4, 2, 8]. Two of three are correct
    G1 = {4, 9, 2}   X1 = [4, 2, 8]   |X1 ∩ G1| = {{2}}   recall 2/3
---
Query 2: true {7, 1, 3}, returned [7, 1, 3]. Average over the queries: (2/3 + 3/3) / 2
    G2 = {7, 1, 3}   X2 = [7, 1, 3]   recall 1   ->   mean recall@3 = {{0.833}}
---
Now the frontier. Sort the measured configurations by median latency and walk through them, tracking the best recall so far
    0.08 ms IVF141/1  0.757 -> keep, best = 0.757
---
0.15 ms IVF141/4 (0.854) beats 0.757: keep. 0.16 ms IVF566/4 (0.944): keep
    best = {{0.944}}
---
0.28 ms IVF566/16 (0.975): keep. 0.31 ms LSH 32x10 (0.512): dominated. 0.56 ms brute force (1.000): keep
    best = {{1.000}}
---
Everything slower than 0.56 ms is dominated by brute force: IVF141/16, LSH 128x10, PQ + re-rank. Pick the cheapest frontier point meeting the target
    target 0.90 -> IVF566/4 (0.16 ms)   target 0.97 -> IVF566/16 (0.28 ms)
```

## Template

```python
import time

import numpy as np


def recall_at_k(found, truth, k):
    """Mean share of each query's true top k that appears in its returned top k."""
    return float(np.mean([len(set(f[:k]) & set(t[:k])) / k for f, t in zip(found, truth)]))


def benchmark(search, queries, truth, k=10, warmup=10):
    """search(q) -> ids. Returns (recall@k, median ms, p99 ms) over the queries, one at a time."""
    for q in queries[:warmup]:
        search(q)
    found, ms = [], []
    for q in queries:
        t0 = time.perf_counter()
        found.append(search(q))
        ms.append((time.perf_counter() - t0) * 1e3)
    return recall_at_k(found, truth, k), float(np.median(ms)), float(np.percentile(ms, 99))


def pareto(points):
    """points: (name, recall, ms). Keep the ones that no other point beats on both recall and time."""
    frontier, best = [], -1.0
    for name, recall, ms in sorted(points, key=lambda p: (p[2], -p[1])):
        if recall > best:
            frontier.append((name, recall, ms))
            best = recall
    return frontier
```

`pareto` was checked against a brute-force dominance test on random point sets, and on the table above it returns the five points marked "yes".

## Pitfalls

- **Queries drawn from the stored vectors.** They find themselves and inflate recall (0.842 against 0.757 above). Hold out real queries.
- **Speed without recall,** or recall at a single setting. Report the curve, or at least the latency at your target recall.
- **Timing the first query, or timing in a busy notebook.** Warm up, repeat, and report medians and the 99th percentile; on a shared machine take the best of several passes, as the tables in this module do.
- **Comparing a C++ library with a Python prototype** and concluding the algorithm is better. Compare algorithms inside one implementation.
- **Forgetting filters, updates and growth.** Recall measured on a static snapshot without filters can collapse with a selective filter or after millions of inserts. Re-measure on a schedule, from a sample of production queries.

## Check yourself

Q: An index returns [3, 5, 8, 1] for a query whose true top 4 is {1, 2, 3, 4}. What is its recall@4, and what is its 1-recall@4 if the true nearest is 1?
A: recall@4 = |{3, 5, 8, 1} ∩ {1, 2, 3, 4}| / 4 = 2/4 = 0.5. 1-recall@4 asks only whether the true nearest (1) appears in the top 4: it does, so 1.

Q: Configuration A gives 0.95 recall at 2.0 ms, B gives 0.97 at 1.5 ms, C gives 0.99 at 4.0 ms. Which are on the Pareto frontier, and which do you choose for a 0.96 target?
A: B dominates A (more recall, less time), so the frontier is B and C. For a 0.96 target choose B, the cheapest frontier point that meets it.

Q: A colleague reports "our IVF index has 99% recall at 0.2 ms" from a test where queries were 1,000 random stored documents. What do you ask them to change?
A: Use held-out queries from the real query distribution (for example embedded user questions), since stored vectors find themselves and land in their own list. Then report the recall-latency curve over nprobe with median and 99th-percentile latency, measured after warm-up.

## Lab

- Find the frontier. Feed the nine rows of the table above to `pareto`. Expected: IVF 141/1, IVF 141/4, IVF 566/4, IVF 566/16 and brute force, in that order. Then pick for targets 0.90, 0.97 and 0.99. Expected: IVF 566/4 (0.16 ms), IVF 566/16 (0.28 ms) and brute force (0.56 ms), since nothing else in NumPy reaches 0.99 faster.

> [!know]
> You now know how to build ground truth, compute recall@k honestly, read a recall-latency curve and choose an index from its Pareto frontier.

=== lab | Brute force, LSH and IVF on 20,000 vectors | 50 min
goal: Implement exact search, random-hyperplane LSH and IVF in NumPy on a seeded dataset, and measure recall@10, the share of vectors scanned and query time for each

You will build three of this module's indexes over the same 20,000 clustered unit vectors, measure each against brute-force ground truth, and see the trade-offs from the cards with your own numbers.

## Setup

- Python 3.10 or later with NumPy (`pip install numpy`). No GPU, about 200 MB of RAM, about 30 seconds of computing per full run.
- Your implementations of `HyperplaneLSH`, `kmeans` and `IVF`. Write them yourself first, then compare with the templates in the LSH and IVF cards.

## Steps

1. Save the harness below as `vector_lab.py`. It makes the dataset (300 Gaussian clusters in 64 dimensions, normalised to unit length, like embeddings), computes exact ground truth with brute force, and times any search function one query at a time on one core.

```python
import os
os.environ["OMP_NUM_THREADS"] = "1"          # one core, so the timings compare like with like
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import sys
import time

import numpy as np

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0
N, NQ, D, K = 20_000, 200, 64, 10


def make_data(seed=SEED, n_clusters=300, noise=1.2):
    rng = np.random.default_rng(seed)
    centres = rng.standard_normal((n_clusters, D)).astype(np.float32)

    def sample(m):
        x = centres[rng.integers(0, n_clusters, m)] + noise * rng.standard_normal((m, D)).astype(np.float32)
        return x / np.linalg.norm(x, axis=1, keepdims=True)

    return sample(N), sample(NQ)


def brute_force(X, q, k=K):
    scores = X @ q                                       # unit vectors: dot product = cosine
    top = np.argpartition(-scores, k - 1)[:k]
    return top[np.argsort(-scores[top])], len(X)


def evaluate(name, search, Q, truth):
    for q in Q[:10]:
        search(q)                                        # warm-up
    hits, scanned, ms = 0, 0, []
    for q, t in zip(Q, truth):
        t0 = time.perf_counter()
        ids, n = search(q)
        ms.append((time.perf_counter() - t0) * 1e3)
        hits += len(set(ids[:K].tolist()) & set(t.tolist()))
        scanned += n
    print(f"{name:<24} recall@10 {hits / (K * len(Q)):.3f}   scanned {scanned / len(Q) / N:6.1%}   "
          f"median {np.median(ms):6.3f} ms   p99 {np.percentile(ms, 99):6.3f} ms")


X, Q = make_data()
truth = np.array([brute_force(X, q)[0] for q in Q])
evaluate("brute force", lambda q: brute_force(X, q), Q, truth)
```

2. Run `python vector_lab.py`. Brute force must report recall 1.000 and 100% scanned; note its median time as your baseline.
3. Add your `HyperplaneLSH` (its `search(q, k)` must return the ids and the number of candidates re-ranked) and evaluate it for (L, K) = (32, 10), (128, 10) and (64, 8):

```python
for L, Kb in [(32, 10), (128, 10), (64, 8)]:
    lsh = HyperplaneLSH(X, n_tables=L, n_bits=Kb, seed=SEED)
    evaluate(f"LSH L={L} K={Kb}", lsh.search, Q, truth)
```

4. Add your `kmeans` and `IVF` (its `search(q, k, nprobe)` must return the ids and the number of vectors scanned) and sweep nprobe for 141 lists (about √n), then for 566 lists (4√n):

```python
ivf = IVF(X, nlist=141, seed=SEED)
for nprobe in (1, 4, 16, 32):
    evaluate(f"IVF nlist=141 nprobe={nprobe}", lambda q: ivf.search(q, K, nprobe), Q, truth)
ivf2 = IVF(X, nlist=566, seed=SEED)
for nprobe in (4, 16):
    evaluate(f"IVF nlist=566 nprobe={nprobe}", lambda q: ivf2.search(q, K, nprobe), Q, truth)
```

5. Put the rows in a table and mark the Pareto frontier with the last card's `pareto`. Pick the cheapest configuration with recall@10 of at least 0.9 and at least 0.97.
6. Run again with seeds 1 and 2 (`python vector_lab.py 1`). Note which numbers move and which stay put.
7. Optional: add the HNSW card's template, or `pip install hnswlib` and index the same `X` with M = 16 and ef_construction = 100, and add its points for ef = 10 to 160.

## What you should see

Measured on one core of a shared Xeon server for seeds 0, 1 and 2. Recall and the scanned share should match closely even if your code differs in details; times depend on your machine, so compare them with your brute-force baseline rather than with these numbers.

| configuration | recall@10 | scanned | median time here |
|---|---|---|---|
| brute force | 1.000 | 100% | 0.50-0.56 ms |
| LSH L=32, K=10 | 0.49-0.51 | about 4.1% | 0.3-0.5 ms |
| LSH L=128, K=10 | 0.91-0.93 | about 14.7% | 1.3-1.7 ms |
| LSH L=64, K=8 | 0.93-0.94 | about 24.7% | 2.1-2.5 ms |
| IVF 141, nprobe 1 | 0.74-0.81 | about 0.8-0.9% | 0.06-0.14 ms |
| IVF 141, nprobe 4 | 0.85-0.90 | about 3.5% | 0.13-0.19 ms |
| IVF 141, nprobe 16 | 0.94-0.95 | about 14% | 0.47-0.62 ms |
| IVF 141, nprobe 32 | 0.97-0.98 | about 28% | 1.0-1.1 ms |
| IVF 566, nprobe 4 | 0.92-0.94 | about 0.8% | 0.14-0.19 ms |
| IVF 566, nprobe 16 | 0.965-0.975 | about 3% | 0.19-0.28 ms |

- **Brute force** is perfect and, at 20,000 vectors, fast: a fraction of a millisecond.
- **LSH** needs many tables, and re-ranks 15-25% of the collection, to pass 0.9 recall; in NumPy it ends up *slower* than brute force. Its build is instant and needs no training.
- **IVF** reaches 0.9 recall while scanning a few per cent, and the finer 566-list index gets 0.94 from 4 probes at under 1% scanned: the fastest route to 0.9 and 0.97 in this lab.
- Across seeds the recall moves by a few hundredths and the scanned shares hardly move; the times move with machine load, which is why you compare against your own baseline.
- With hnswlib (step 7), expect about 0.95 recall at ef = 20 and 0.98-0.99 at ef = 80, at around 0.1-0.2 ms per query on one core.

## Check yourself

Q: Why does IVF with nprobe = 16 and 141 lists scan 14% of the vectors although 16 / 141 is only 11%?
A: The lists have unequal sizes (51 to 293 vectors here), and queries come from the same clusters as the data, so the lists near a query tend to be the larger, denser ones. The probed share therefore exceeds nprobe / nlist, as the FAISS wiki warns.

Q: Your brute force takes 0.5 ms and you will never have more than 50,000 vectors. Which index do you deploy?
A: Probably none: exact search at about 1.3 ms per query (2.5 times the data) with perfect recall, no training and no tuning. Revisit when the collection or the query rate grows, or when latency at your query rate stops fitting the budget.
