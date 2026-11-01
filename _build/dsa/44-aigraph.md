---
key: aigraph
name: Graphs behind AI systems: retrieval and agents
stage: aisys
summary: The graph algorithms inside graph retrieval and agent runtimes: PageRank and personalised PageRank, budgeted k-hop expansion, community detection for GraphRAG, and running agent workflows as DAGs with checkpoints.
why: Graph-based retrieval and agent orchestration look like new AI ideas, but the hard parts are classic graph algorithms with budgets attached. HippoRAG is personalised PageRank over an extracted entity graph; GraphRAG's index is a modularity-based community hierarchy; entity-anchored retrieval is breadth-first search that must not drown in hub nodes; LangGraph-style runtimes are topological scheduling plus checkpoints. If you understand the walk, the cut, the frontier and the in-degree count, you can predict cost, debug strange rankings, bound latency and make long agent runs restartable, whichever framework your team picks. The AI page teaches how to use these systems; this module teaches what runs underneath.
outcomes:
- Compute PageRank by power iteration with damping and dangling nodes, and bound the error after k iterations by 2·d^k
- Rank passages for a multi-hop question with personalised PageRank seeded at the question's entities, as HippoRAG does
- Expand a knowledge graph from seed entities under hop, fan-out, node and token budgets, and explain why hub nodes need caps
- Explain modularity, Louvain-style local moving and what Leiden's refinement adds, and how GraphRAG builds its community hierarchy
- Schedule an agent workflow with Kahn's algorithm in waves, merge parallel branches safely, bound loops and resume after a crash without redoing finished work
cues:
- "Most important" or "most related to these entities" over a link, citation or entity graph: a random walk with restart
- A multi-hop question whose bridge entity is not named in the question
- A neighbourhood that explodes after one or two hops because a few nodes have thousands of edges
- "What are the main themes across everything?": partition the graph into communities before summarising
- Steps with dependencies, some independent, some repeated until a check passes, in runs that must survive a crash
traps:
- Letting dangling nodes leak probability, so scores stop summing to 1 and rankings drift with the iteration count
- Expanding k hops with no fan-out cap or node budget, so one hub entity floods the context window
- Treating community detection output as ground truth: it is a randomised heuristic whose answer depends on the resolution and the seed
- Merging parallel branch outputs in arrival order, or letting two branches overwrite the same key
- Putting non-idempotent side effects (payments, emails) in nodes that may run again after a crash
systems:
- Brin and Page (1998) computed PageRank for 26 million web pages "in a few hours on a medium size workstation", usually with d = 0.85
- HippoRAG (NeurIPS 2024) ranks passages with personalised PageRank from python-igraph, damping 0.5, seeded at the question's entities
- Microsoft GraphRAG clusters its entity graph with hierarchical Leiden from graspologic (default max_cluster_size 10) and writes an LLM summary for every community
- LangGraph runs a graph in Pregel-style super-steps, saves a checkpoint at every super-step boundary and stops runaway loops with a recursion limit
further:
- Paper · 20 min | Brin and Page 1998, section 2.1: the PageRank definition and the random surfer | https://snap.stanford.edu/class/cs224w-readings/Brin98Anatomy.pdf
- Paper · 25 min | Gutiérrez et al. 2024, HippoRAG, section 2.3: indexing, query nodes, PPR and node specificity | https://arxiv.org/html/2405.14831v3#S2.SS3
- Paper · 30 min | Traag, Waltman and van Eck 2019, section III: the Leiden algorithm and its guarantees | https://arxiv.org/html/1810.08473v3#S3
- Docs · 15 min | LangGraph checkpointers: super-steps and pending writes | https://docs.langchain.com/oss/python/langgraph/checkpointers#super-steps
---

=== primer | How does PageRank turn links into scores, and why does power iteration converge? | 15 min
goal: Compute PageRank by power iteration with damping and dangling nodes, and work out how many iterations a tolerance needs
tag: aigraph-pagerank | PageRank by power iteration
link: Brin and Page 1998 | https://snap.stanford.edu/class/cs224w-readings/Brin98Anatomy.pdf | About 5 min: Section 2.1 (one page): the original formula, d = 0.85, the random surfer, and the remark that sending the random jump to chosen pages personalises the ranking
link: NetworkX pagerank | https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html | About 5 min: The parameter list (alpha, personalization, dangling, tol): a reference implementation to check your own scores against, and its N·tol stopping rule

> [!key]
> PageRank scores a node by how often a **random surfer** visits it: with probability d (usually 0.85) follow a random out-link, otherwise jump to a node drawn from a **teleport** distribution. The scores are the stationary distribution of that walk. **Power iteration** applies one step of the walk to a probability vector until it stops changing; each step costs O(n + m), and the error shrinks by at least a factor d per step, so d = 0.85 needs at most about 90 steps to reach 10^-6.

## Intuition

Release a thousand people onto a small web and let each one keep clicking random links. After a while, count where they are. Pages that many paths lead to hold more people, and a link from a crowded page delivers more visitors than a link from a quiet one. That count, as a fraction of the crowd, is PageRank.

Two things break the picture. A page with no out-links (a **dangling node**) is a dead end, and a group of pages that only link to each other is a trap that slowly soaks up everyone. The fix is boredom: at every click, with probability 1 - d, a surfer ignores the links and jumps somewhere chosen by the teleport distribution. That keeps everyone moving and makes the answer unique.

## How it works

### One step of the walk

Let x[u] be the fraction of surfers on node u, and t the teleport distribution (uniform, 1/n each, for plain PageRank). One step moves the crowd:

- each node u with out-links sends d · x[u] / out(u) along every out-link;
- every node v receives (1 - d) · t[v] from the jump;
- the mass sitting on dangling nodes, d · (sum of x over dangling nodes), is handed out in proportion to t, as if a dangling node linked to everything the teleport could reach.

Every unit of mass goes somewhere, so the total stays exactly 1. Start from x = t and repeat until the vector stops changing. Brin and Page wrote the rule per page as PR(A) = (1 - d) + d (PR(T1)/C(T1) + ... + PR(Tn)/C(Tn)), where T1..Tn link to A and C(T) counts T's out-links. Without dangling nodes that is the uniform-teleport version above multiplied by n, so the ranking is the same.

### Why it converges

Write the step as x -> d·S·x + (1 - d)·t, where S is the "follow a link" matrix with each dangling column replaced by t. Every column of S is non-negative and sums to 1, so for any vector e, the L1 norm of S·e is at most the L1 norm of e (mass is moved, never created). Take two vectors x and y and apply the step to both: the teleport term cancels and the difference becomes d·S·(x - y), at most d times smaller. The fixed point x* exists and is unique, and the error after k steps obeys

```text
|x_k - x*|_1  <=  d^k · |x_0 - x*|_1  <=  2 · d^k
```

because two probability vectors differ by at most 2 in L1. The same argument turns the observed change into an error bound: if |x_{k+1} - x_k|_1 < tol then |x_{k+1} - x*|_1 <= tol · d / (1 - d), about 5.7 · tol for d = 0.85.

### Personalisation

Nothing above needs t to be uniform. Put all of t on a few seed nodes and the walk keeps restarting there: that is **personalised PageRank**, the subject of the next card. Brin and Page already noted that sending the jump to a single page or a group of pages personalises the ranking.

## Cost

Count the work in one iteration: one pass over the n nodes for the base and dangling terms, one pass over the m edges to push shares, one pass over the nodes for the change. That is **O(n + m) time per iteration and O(n) extra space** for the two vectors.

The number of iterations comes from the bound above: to guarantee error below e you need d^k <= e/2, so k = ceil(log(e/2) / log d). For e = 10^-6 that is 21 iterations at d = 0.5, 90 at d = 0.85 and 283 at d = 0.95. Higher damping means longer walks, a ranking that follows the links more faithfully, and slower convergence.

The bound is a worst case, and it is tight: on a directed ring of 100 nodes, personalised to one node, the error fell by exactly 0.85 per step and needed 89 steps for 10^-6. Typical graphs mix faster. On the 200-node random graph from this module's lab, reaching an L1 error of 10^-8 took 16, 34 and 43 iterations for d = 0.5, 0.85 and 0.95, against worst-case bounds of 28, 118 and 373.

The exact alternative is to solve the linear system (I - d·S)·x = (1 - d)·t. A dense solve costs O(n^3) time and O(n^2) memory: fine for a few thousand nodes and a good test oracle, hopeless for a web-scale graph, which is why power iteration (sparse, O(n + m) memory) is the production method.

## When to use it

Use PageRank when you need a global importance score for nodes in a directed graph whose edges mean "endorses", "cites" or "depends on": ranking documents, entities in a knowledge graph, packages in a dependency graph, accounts in a follower graph. It is query-independent, so compute it offline and use it as one feature among several.

| Need | Tool | Cost |
|---|---|---|
| Rough popularity, nothing else | In-degree count | O(n + m), one pass |
| Importance that respects who links to you | PageRank by power iteration | O(n + m) per iteration, tens of iterations |
| Importance relative to a query or a user | Personalised PageRank (next card) | Same per query |
| Exact scores for a small graph or a test | Linear solve | O(n^3) |

Do not expect much from it on an undirected similarity graph: on a connected undirected graph, a random walk without teleport spends time in proportion to degree, so PageRank adds little beyond a degree count. Do not compare raw scores across graphs of different sizes: scores sum to 1, so the average is 1/n.

## Worked trace

The graph has four pages: A links to B and C, B links to C, C links to A and D, and D has no out-links.

```text
A -> B, A -> C
B -> C
C -> A, C -> D
D -> (none)        dangling: its mass is spread by the teleport rule
```

```steps
Start with x = t = 1/4 each, d = 0.85
    page     A       B       C       D
    x0     0.2500  0.2500  0.2500  0.2500
---
Iteration 1: base for every page = (0.15 + 0.85 × dangling 0.25) × 1/4 = {{0.0906}}. A gets half of C's 0.2125, B half of A's, C half of A's plus all of B's, D half of C's
    page     A       B       C       D
    x1     0.1969  0.1969  {{0.4094}}  0.1969     change 0.319
---
Iteration 2: dangling mass is now D's 0.1969, so the base drops to 0.0793; C's crowd flows back to A and D
    page     A       B       C       D
    x2     {{0.2533}}  0.1630  0.3304  {{0.2533}}     change 0.226
---
Iteration 3: the swings shrink; notice A and D are always equal, since both receive exactly the base plus half of C
    page     A       B       C       D
    x3     0.2317  0.1990  0.3375  0.2317     change 0.086
---
Iteration 35: the change drops below 10^-10 and the exact linear solve gives the same numbers
    page     A       B       C       D
    x*     0.2340  0.1867  {{0.3453}}  0.2340     sum 1.0000
```

C wins: it collects all of B's vote and half of A's. B is last because only half of A's mass reaches it.

## Template

```python
def pagerank(out_links, d=0.85, teleport=None, tol=1e-10, max_iter=1000):
    """Power iteration. out_links: {node: [targets]}, every target is also a key.
    teleport: {node: weight} for personalised PageRank (default: uniform).
    Returns (scores, iterations). Dangling mass is sent to the teleport vector."""
    nodes = list(out_links)
    if teleport is None:
        teleport = {u: 1.0 for u in nodes}
    total = sum(teleport.values())
    v = {u: teleport.get(u, 0.0) / total for u in nodes}
    x = dict(v)
    for it in range(1, max_iter + 1):
        dangling = sum(x[u] for u in nodes if not out_links[u])
        new = {u: (1 - d + d * dangling) * v[u] for u in nodes}
        for u in nodes:
            targets = out_links[u]
            if targets:
                share = d * x[u] / len(targets)
                for w in targets:
                    new[w] += share
        change = sum(abs(new[u] - x[u]) for u in nodes)
        x = new
        if change < tol:
            return x, it
    raise RuntimeError(f"no convergence in {max_iter} iterations")
```

I checked it on 300 random graphs (with dangling nodes, three damping values, uniform and personalised teleport) against an exact linear solve and against `networkx.pagerank`: every score agreed to within 10^-8.

## Pitfalls

- **Leaking dangling mass.** Skipping dangling nodes makes the total shrink every iteration (to 0.43 after 50 iterations on the trace graph). Redistribute it, or at least renormalise at the end.
- **Edge direction.** PageRank flows along out-links. Build the adjacency as "u links to v", not "v is linked from u", or you compute something else.
- **Tolerance versus size.** NetworkX stops when the L1 change falls below n · tol and warns that if n · tol >= 2 the loop can stop after one step. With a million nodes, tol = 10^-6 is no tolerance at all.
- **Duplicate edges and self-loops.** A repeated link counts twice in `len(targets)`; a self-loop keeps mass in place. Decide whether your data should have them.
- **Iteration count as a quality knob.** Stopping after a fixed 10 iterations gives scores that depend on the start vector. Stop on a tolerance and report the iteration count.

## Check yourself

Q: Using the trace graph, compute C's score after iteration 1 by hand.
A: The base is (0.15 + 0.85 × 0.25) × 0.25 = 0.090625, where 0.25 is the dangling mass on D. C also receives half of A's pushed mass, 0.85 × 0.25 / 2 = 0.10625, and all of B's, 0.85 × 0.25 = 0.2125. Total 0.409375, shown as 0.4094.

Q: Why does the error shrink by at least a factor d per iteration, whatever the graph?
A: The step is x -> d·S·x + (1 - d)·t with S column-stochastic once dangling columns are replaced by t. Subtracting the step applied to x* from the step applied to x leaves d·S·(x - x*), and a column-stochastic matrix never increases the L1 norm of a vector, so the error is multiplied by at most d.

Q: A colleague drops the dangling mass instead of redistributing it and divides by the total at the end. On the trace graph, does the ranking change?
A: No. After 50 iterations the leaky vector sums to 0.4299, and after dividing by that it is exactly 0.2340, 0.1867, 0.3453, 0.2340. With dangling mass sent to the teleport vector, the true solution is a scalar multiple of the leaky one, because the dangling term only adds a multiple of t. It would differ if dangling mass went somewhere other than t.

Q: You need scores for a 50-million-node graph with tol = 10^-6 in NetworkX's convention. What goes wrong, and how do you fix it?
A: NetworkX compares the L1 change with n · tol = 50, larger than the maximum possible change of 2, so it stops after one iteration. Use a per-graph tolerance such as 10^-6 in total L1 change (pass tol = 10^-6 / n), or measure the change yourself.

## Lab

- On the trace graph, run `pagerank(G, d=0.5)`. Expected: A 0.2340, B 0.2128, C 0.3191, D 0.2340 after 20 iterations (with d = 0.85 it takes 35 iterations and C reaches 0.3453): less damping, flatter scores.
- Write the leaky version (no dangling term) and run 50 iterations from uniform. Expected: the total is 0.4299; after dividing by it you get back the d = 0.85 scores above.
- Personalise on B with `teleport={"B": 1}`. Expected: A 0.1510, B 0.3426, C 0.3554, D 0.1510 after 79 iterations; C beats the seed because every walk from B goes through C.

> [!know]
> You now know how to compute PageRank by power iteration, handle dangling nodes, and turn a tolerance into an iteration count with the 2·d^k bound.

=== primer | How does personalised PageRank find passages for a multi-hop question, as HippoRAG does? | 15 min
goal: Rank passages for a question by running personalised PageRank from the question's entities over an entity graph, and explain why bridge entities win
tag: aigraph-ppr | Personalised PageRank retrieval
link: HippoRAG, section 2.3 | https://arxiv.org/html/2405.14831v3#S2.SS3 | About 10 min: The exact pipeline: OpenIE triples, synonym edges, query nodes, the personalised vector, node specificity and passage scores from the node-passage matrix
link: AI page: lighter graph approaches | https://learningcurie.github.io/code-study-tracker/ai.html#l-l-advrag-lighter-graph-approaches-lightrag-entity-linking | About 12 min: How HippoRAG sits next to LightRAG and temporal graphs in a real retrieval stack

> [!key]
> Personalised PageRank (PPR) is PageRank whose random jump always returns to a few **seed** nodes. The stationary mass then measures closeness to the seeds, counting every path, not just the shortest. **HippoRAG** (Gutiérrez et al., NeurIPS 2024) seeds PPR with the entities named in a question, runs it over an entity graph extracted from the corpus, and scores each passage by the PPR mass of the entities it mentions. Entities connected to several seeds collect mass from all of them, so the bridge in a multi-hop question rises to the top in one retrieval step.

## Intuition

Two people start a rumour at the same time, one in Mira's team and one in the Frankfurt office. Every hour, each person who heard it either tells a random acquaintance or forgets and the rumour restarts at its sources. Someone who knows people on both sides hears it twice as often as anyone else. In a question such as "Which team led by Mira Patel deploys to Frankfurt?", the answer is exactly that person: an entity next to both question entities, named in neither.

## How it works

### Offline: build the entity graph

HippoRAG uses an LLM to extract open triples (subject, relation, object) from every passage, so the graph is schemaless. Each noun phrase becomes a node and each triple an edge. A retrieval encoder adds **synonym edges** between nodes whose embeddings have cosine similarity above a threshold (0.8 in the paper), so "Payments team" and "payments squad" are linked. The index also records which passages each node came from: a node-by-passage count matrix.

### Online: seed, walk, score

1. An LLM extracts the named entities from the question.
2. Each one is matched to its most similar graph node by the same encoder: these are the **query nodes**.
3. The teleport vector puts equal weight on the query nodes, multiplied by **node specificity** s_i = 1 / (number of passages node i came from): an IDF-like signal that favours rare entities.
4. Run PPR. HippoRAG uses python-igraph's implementation with damping 0.5, tuned on 100 MuSiQue training questions.
5. A passage's score is the sum, over the nodes it contains, of node mass times count. Return the top k passages.

### Damping is a hop budget

The number of link steps a walk takes before restarting is geometric: it takes exactly k steps with probability (1 - d)·d^k, so the expected length is d / (1 - d). With d = 0.5 that is one step on average, and mass two hops away is at most a quarter of the total; with d = 0.85 it is about 5.7 steps and the walk wanders far from the question. HippoRAG's 0.5 keeps retrieval local, which suits two-to-four-hop questions.

### Why bridges win

In the first step, each seed sends d times its mass, split evenly across its neighbours. A node adjacent to two seeds receives two shares; a node adjacent to one receives one. Later steps blur the picture, but the bridge keeps its lead, as the trace shows.

The paper reports up to 20% better multi-hop QA than earlier retrievers, and single-step retrieval that matched or beat iterative retrieval (IRCoT) while being 10 to 30 times cheaper and 6 to 13 times faster. Its ablations replaced PPR with "query nodes only" and "query nodes plus direct neighbours": both did clearly worse, and adding neighbours without PPR was worse than the query nodes alone. A follow-up, HippoRAG 2 (ICML 2025), keeps PPR at the core and adds deeper passage integration.

## Cost

Offline, the dominant cost is the LLM extraction: two calls per passage in HippoRAG (named entities first, then triples). Synonym edges need a nearest-neighbour search over node embeddings.

Online, per question: one LLM call for entity extraction, one encoder lookup per entity, then PPR. Each PPR iteration is O(n + m) over the whole graph, and with d = 0.5 the error bound 2 · 0.5^k reaches 10^-6 within 21 iterations. Passage scoring touches each non-zero entry of the node-passage matrix for nodes with mass: at most O(nnz). So a query costs roughly 21 · (n + m) plus the scoring pass, in memory, with no further LLM calls. Compare IRCoT, which interleaves an LLM call with a retrieval call at every reasoning step.

## When to use it

| Question shape | Better tool |
|---|---|
| Single fact stated in one passage | Dense or hybrid retrieval: cheaper and more direct |
| Multi-hop, the bridge entity is unnamed ("the team led by X that deploys to Y") | PPR over an entity graph |
| Multi-hop, each hop needs reasoning about the previous answer | Iterative retrieval, or PPR inside the iterative loop (HippoRAG plus IRCoT gave further gains in the paper) |
| "Main themes across all documents" | GraphRAG community summaries (card 4) |

Signals that PPR retrieval will help: questions mention two or more entities; answers sit in passages that share entities rather than wording; your corpus is entity-rich (people, systems, products). Signals against: poor entity extraction (the paper's error analysis splits failures into NER, OpenIE and PPR errors), or questions with no entities at all.

## Worked trace

Seven passages, one triple each: P1 Mira Patel leads Payments team; P2 Payments team deploys to Frankfurt; P3 Mira Patel spoke at Berlin meetup; P4 Mira Patel mentors Leo Kim; P5 Team Orion deploys to Frankfurt; P6 Team Vega deploys to Frankfurt; P7 Team Orion owns search service. The question's entities are Mira Patel and Frankfurt (each appears in 3 passages, so equal specificity). d = 0.5.

```steps
Start: all mass on the two seeds
    entity  Mira    Frank   Paym    Orion   Vega    Berlin  Leo     search
    x0      0.5     0.5     0       0       0       0       0       0
---
Step 1: each seed keeps 0.25 as restart mass and spreads 0.25 over its 3 neighbours; Payments is next to both seeds
    x1      0.25    0.25    {{0.1667}}  0.0833  0.0833  0.0833  0.0833  0
---
Step 2: Payments sends its mass back to both seeds; the others send to one seed (or on to the search service)
    x2      0.375   0.3542  0.0833  0.0417  0.0417  0.0417  0.0417  0.0208
---
Step 3: the bridge's lead persists while the swings shrink
    x3      0.3125  0.3021  {{0.1215}}  0.0694  0.059   0.0625  0.0625  0.0104
---
Converged after 35 iterations: Payments holds about twice the mass of any other non-seed
    x*      0.3326  0.3189  {{0.1086}}  0.0607  0.0532  0.0554  0.0554  0.0152
---
Passage score = sum of its entities' mass: the two passages through the bridge come first
    P1 0.441  {{P2 0.427}}  P3 0.388  P4 0.388  P5 0.380  P6 0.372  P7 0.076
```

A keyword retriever that returns "passages mentioning a question entity" ties P1 to P6. PPR separates them: P1 and P2 together answer the question.

## Template

```python
from collections import defaultdict


def build_index(passages):
    """passages: {pid: [(subject, relation, object), ...]} from an LLM extractor.
    Returns (graph, where): an undirected entity graph and entity -> set of passage ids."""
    graph, where = defaultdict(set), defaultdict(set)
    for pid, triples in passages.items():
        for s, _, o in triples:
            graph[s].add(o)
            graph[o].add(s)
            where[s].add(pid)
            where[o].add(pid)
    return {u: sorted(vs) for u, vs in graph.items()}, where


def ppr_retrieve(graph, where, query_entities, k=3, d=0.5):
    """Rank passages by the personalised PageRank mass of the entities they mention."""
    seeds = {e: 1 / len(where[e]) for e in query_entities}   # node specificity
    scores, _ = pagerank(graph, d=d, teleport=seeds)          # from the previous card
    passage_score = defaultdict(float)
    for entity, p in scores.items():
        for pid in where[entity]:
            passage_score[pid] += p
    return sorted(passage_score.items(), key=lambda kv: -kv[1])[:k]
```

The entity scores were also checked against a Monte Carlo simulation of 400,000 steps of the random walk with restart (agreement within 0.01). This sketch treats every edge as undirected and counts each entity once per passage; HippoRAG's node-passage matrix counts repeated mentions.

## Pitfalls

- **Hubs.** A node such as "Germany" connected to half the corpus absorbs and leaks mass everywhere. Node specificity down-weights common seeds; for non-seed hubs, consider dropping or down-weighting edges by degree.
- **Unmatched seeds.** If the question's entity maps to the wrong node, PPR faithfully ranks the wrong neighbourhood. Log the chosen query nodes and their similarity.
- **Too much damping.** With d = 0.85 on the trace graph, P5 (another team in Frankfurt) climbs to third place: long walks reward general connectivity over closeness to both seeds.
- **Passages with many entities.** Summing node mass favours long passages that mention many things. Normalise by passage length if this shows up in your evaluations.
- **Fragmented entities.** Without synonym edges or entity resolution, "Payments team" and "payments squad" are different nodes and the bridge breaks.

## Check yourself

Q: In step 1 of the trace, why does Payments team get 0.167 while Team Orion gets 0.083?
A: Each seed keeps 0.25 as restart mass and pushes 0.5 × 0.5 = 0.25 to its three neighbours, 0.083 each. Payments is a neighbour of both seeds, so it receives two shares; Team Orion neighbours only Frankfurt.

Q: What is the expected number of link steps per walk at d = 0.5 and at d = 0.85, and what does that mean for retrieval?
A: d / (1 - d): 1 step at 0.5 and about 5.7 steps at 0.85. Low damping keeps mass within a hop or two of the question's entities, which suits multi-hop questions; high damping spreads mass to well-connected but less relevant parts of the graph.

Q: Why did HippoRAG's ablation "query nodes plus direct neighbours" do worse than PPR, and even worse than query nodes alone?
A: Adding all neighbours with equal weight brings in every neighbour of a seed, relevant or not, which dilutes the ranking. PPR weights a neighbour by how much walk mass reaches it from all seeds, so nodes that connect several seeds stand out and unrelated neighbours stay small.

Q: Your PPR retriever returns passages about a famous city for every question that mentions anyone who ever lived there. Name two fixes.
A: Down-weight the city as a seed with node specificity (it appears in many passages), and reduce its pull as a non-seed by normalising or pruning hub edges; also check whether damping is too high, since longer walks make hubs more important.

## Lab

- Build the index for the seven passages and query `["Mira Patel", "Frankfurt"]` with k = 2. Expected: P1 0.441 and P2 0.427, the two passages that answer the question.
- Query `["Mira Patel"]` alone with k = 4. Expected: P1 0.744, P3 0.739, P4 0.739, then P2 0.143: without Frankfurt as a seed, nothing pulls mass towards the bridge's second passage.
- Rerun the two-seed query with d = 0.85 and k = 4. Expected: P1 0.400, P2 0.377, P5 0.341, P3 0.334: the distractor P5 overtakes P3 as walks get longer.

> [!know]
> You now know how to retrieve passages for multi-hop questions with personalised PageRank from the question's entities, and how damping and node specificity shape the result.

=== primer | How do you expand a knowledge graph k hops from the question without flooding the context? | 14 min
goal: Write a budgeted k-hop expansion (hop limit, fan-out cap, node budget, decaying score) and pack the result into a token budget
tag: aigraph-khop | Budgeted k-hop expansion
link: GraphSAGE, section 3.1 | https://arxiv.org/abs/1706.02216 | About 5 min: In the PDF, the 'Neighborhood definition' paragraph of section 3.1: why fixed-size neighbour samples keep the cost per batch at O(S1·S2) instead of O(|V|) in the worst case
link: GraphRAG local search | https://microsoft.github.io/graphrag/query/local_search/ | About 10 min: The first two sections: entities as entry points, then neighbours, relations and text units prioritised and filtered to fit one context window

> [!key]
> Entity-anchored graph retrieval is **breadth-first search with budgets**. Start from the entities in the question, expand level by level, follow only the f strongest edges of each node (a **fan-out cap**), stop at k hops, keep at most N nodes (a **node budget**) ranked by a score that decays with every hop, then pack the best facts into a **token budget**. Without the caps, a few hub nodes turn two hops into thousands of nodes; with them, the work is bounded by seeds × (f + f^2 + ... + f^k) and by N, whatever the graph looks like.

## Intuition

You need to find out what breaks if a database goes down. You ask the two teams that call it most, and each of them asks their two biggest consumers. You stop after two rounds, and you only write up the six most important answers. You never ask the platform team that "uses" everything, because their answer would be a list of 400 services and none of them would be the point.

## How it works

### Level by level

Keep a dictionary of found nodes with their score and hop. The frontier starts as the seeds (score 1, or the entity-linking confidence). For each hop h = 1..k, look at the out-edges of every frontier node, compute a candidate score for each unseen neighbour, and keep the best score per neighbour. Level-synchronous expansion has an engineering bonus: each level is **one batched query** to the graph store ("neighbours of these 12 nodes"), not 12 round trips.

### The four budgets

1. **Hop limit k.** Two hops answers most entity questions; three is usually the most you can afford.
2. **Fan-out cap f.** Sort every adjacency list by weight once, at index time, so a node's strongest f edges are a slice. This also stops hubs: a node with 40,000 edges still contributes only f.
3. **Node budget N.** After each level, keep only the best candidates that fit in the remaining room (a top-N selection with a heap).
4. **Token budget.** Turn kept nodes and edges into facts, sort by score and greedily add facts while they fit.

### Scoring

A simple, explainable score multiplies along the path: score(child) = score(parent) × edge weight × decay. Weights can be extraction confidence, co-occurrence counts or relation priorities (DEPENDS_ON 1.0, RUNS_ON 0.1); decay (0.5 here) makes every extra hop cost something. Because all factors are at most 1, scores only fall with depth, so a budget cut always drops the most distant, weakest facts first.

### Prior art

GraphSAGE (Hamilton et al., 2017) trains graph networks on neighbourhoods sampled exactly this way: K = 2 levels with fan-outs S1 = 25 and S2 = 10, because "without this sampling the memory and expected runtime of a single batch is unpredictable and in the worst case O(|V|)". Think-on-Graph (ICLR 2024) runs a beam search over a knowledge graph with an LLM choosing which relations and entities to keep, width 3 and depth 3. GraphRAG's local search starts from matched entities, gathers neighbours, relationships and source chunks, and filters them to fit a context window of pre-defined size.

## Cost

Count the nodes. With average out-degree D and no caps, level h can hold up to s · D^h nodes for s seeds: with D = 50, two hops is 2,500 nodes per seed and three hops 125,000. With a fan-out cap, level h holds at most (size of level h-1) × f, so the whole expansion visits at most s · (f + f^2 + ... + f^k) nodes, and never more than N.

Count the work. With pre-sorted adjacency lists, a frontier node costs O(f) to expand. Selecting the best `room` candidates out of c costs O(c log room) with `heapq.nlargest`. Total: **O(N · f · log N) time and O(N · f) memory**, independent of the graph's size and of how big its hubs are. Packing F facts costs O(F log F) for the sort.

## When to use it

| Situation | Choice |
|---|---|
| "What depends on X?", "Who owns the services X calls?" (explicit relations from named entities) | Budgeted k-hop BFS |
| Several question entities, the answer connects them, weights should reflect all paths | Personalised PageRank (previous card) |
| The next hop depends on reasoning about the last one | LLM-guided beam search (Think-on-Graph style) or an agent with a graph tool |
| A precise structural question with a known schema | A graph query (Cypher) with read-only access and a timeout |

Use k-hop expansion when results must be explainable ("checkout is here because it depends on payments-api, which depends on auth-db") and latency must be predictable. Avoid it for global questions about the whole corpus, where community summaries do better.

## Worked trace

Edges point from a component to the services that depend on it. Weights: 1.0 for a direct dependency, 0.6 for an admin tool, 0.1 for "runs on the shared cluster". The node k8s-prod has 40 edges. Seed auth-db, k = 2, f = 2, N = 6, decay 0.5.

```text
auth-db      -> payments-api 1.0, login-svc 1.0, admin-ui 0.6, k8s-prod 0.1
payments-api -> checkout 1.0, refunds 0.9, k8s-prod 0.1
login-svc    -> mobile-app 1.0, web-app 1.0, k8s-prod 0.1
admin-ui     -> k8s-prod 0.1
k8s-prod     -> svc-00 ... svc-39, 0.1 each
```

```steps
Hop 0: found = {auth-db: 1.0}; frontier = [auth-db]
    found     auth-db 1.0
---
Hop 1: auth-db's two strongest edges only (fan-out 2): admin-ui and the hub k8s-prod are never looked at
    candidates  {{payments-api 0.5}}  {{login-svc 0.5}}
    room = 6 - 1 = 5, both kept
---
Hop 2: two edges each from payments-api and login-svc; score = 0.5 × weight × 0.5
    candidates  checkout 0.25  refunds 0.225  mobile-app 0.25  web-app 0.25
    room = 6 - 3 = 3
---
Node budget: keep the best 3 of 4 candidates; refunds (0.225) is cut
    found     auth-db 1.0, payments-api 0.5, login-svc 0.5,
              {{checkout 0.25, mobile-app 0.25, web-app 0.25}}
---
Pack facts of 30 tokens each into a 100-token budget, best first
    kept      payments-api, login-svc, checkout      90 tokens
```

With f = 10 and N = 100 instead, the same call returns 19 nodes, 10 of them `svc-*` nodes reached through the hub: exactly the flood the caps exist to stop.

## Template

```python
import heapq


def khop(graph, seeds, hops=2, fanout=3, max_nodes=20, decay=0.5):
    """Expand from seed entities level by level.
    graph: {node: [(neighbour, weight), ...]} with each list sorted by weight, highest first,
    weights in (0, 1]. seeds: {node: score}. Each node follows at most `fanout` edges,
    nothing deeper than `hops` is visited and at most `max_nodes` nodes are kept.
    Returns {node: (score, hop)}; score = parent score * weight * decay."""
    found = {u: (s, 0) for u, s in seeds.items()}
    frontier = list(seeds)
    for h in range(1, hops + 1):
        cand = {}
        for u in frontier:
            su = found[u][0]
            for v, w in graph.get(u, [])[:fanout]:
                s = su * w * decay
                if v not in found and s > cand.get(v, 0.0):
                    cand[v] = s
        room = max_nodes - len(found)
        if room <= 0 or not cand:
            break
        frontier = heapq.nlargest(room, cand, key=cand.get)
        for v in frontier:
            found[v] = (cand[v], h)
    return found


def pack(facts, token_budget):
    """facts: [(score, tokens, text)]. Greedily keep the highest-scoring facts that fit."""
    kept, used = [], 0
    for score, tokens, text in sorted(facts, key=lambda f: -f[0]):
        if used + tokens <= token_budget:
            kept.append(text)
            used += tokens
    return kept, used
```

Tested on 500 random weighted graphs: with an unlimited budget, the hop of every found node equals its BFS distance over the capped edges and its score equals the best parent on the previous level; with a budget, the result is a subset of the unlimited one and never exceeds `max_nodes`.

## Pitfalls

- **Unsorted adjacency.** `graph[u][:fanout]` is only "the strongest edges" if lists are sorted by weight. Sort once when you build the index, not per query.
- **Edge direction.** "Who depends on auth-db" and "what does auth-db depend on" are different traversals. Store both directions, or the reverse index, explicitly.
- **Cycles.** The `found` check is the visited set: without it, A -> B -> A loops spend the budget on nodes you already have.
- **Ties at the budget line.** Equal scores are cut in insertion order. If that matters, add a tie-breaker (degree, recency) to the key.
- **Budgets in the wrong unit.** A node budget does not bound tokens: one node can carry a 2,000-token description. Always finish with a token-based pack.

## Check yourself

Q: Without caps, roughly how many nodes can three hops reach from one seed when the average out-degree is 50? With f = 5?
A: Up to 50 + 2,500 + 125,000, about 127,550 nodes. With f = 5 at most 5 + 25 + 125 = 155, and fewer if a node budget is set.

Q: Why does the fan-out cap need adjacency lists sorted by weight at index time rather than a sort per query?
A: Sorting a hub's 40,000 edges per query costs O(D log D) for every visit and defeats the point of the cap. With lists sorted once, taking the strongest f edges is an O(f) slice, so the cost per node is independent of its degree.

Q: Your expansion returns the right nodes but the LLM prompt is twice the allowed size. Which budget is missing and how do you add it?
A: A token budget. Convert kept nodes and edges to facts with token counts, sort by score and add them greedily while the running total stays within the limit, as `pack` does.

Q: Why is level-by-level expansion friendlier to a graph database than following one path at a time?
A: Each level becomes a single batched query for the neighbours of the whole frontier, so k hops cost k round trips instead of one per node, and the budget can be applied between levels.

## Lab

- Run `khop` on the dependency graph with hops = 2, fanout = 2, max_nodes = 6. Expected: auth-db 1.0, payments-api 0.5, login-svc 0.5, checkout 0.25, mobile-app 0.25, web-app 0.25 (refunds cut by the budget).
- Rerun with fanout = 10, max_nodes = 100. Expected: 19 nodes, 10 of them `svc-*`, with k8s-prod at score 0.05 and each `svc-*` at 0.0025.
- Add a hub rule: give nodes with more than 20 edges an empty adjacency list before expanding. Expected: 9 nodes (auth-db, payments-api, login-svc, admin-ui, k8s-prod, checkout, refunds, mobile-app, web-app) and no `svc-*`.

> [!know]
> You now know how to expand a graph from a question's entities with hop, fan-out, node and token budgets, and why hubs need caps.

=== primer | How does GraphRAG split an entity graph into communities, and what does Leiden fix in Louvain? | 15 min
goal: Compute modularity, run Louvain-style local moving with Leiden's queue, and explain how GraphRAG builds and uses its community hierarchy
tag: aigraph-leiden | Community detection with modularity
link: From Louvain to Leiden, section III | https://arxiv.org/html/1810.08473v3#S3 | About 15 min: The three phases (local moving, refinement, aggregation), the fast local move queue, and Table 1 of guarantees
link: AI page: GraphRAG for global questions | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-graphrag-for-global-questions | About 14 min: How community reports are written and queried with map-reduce, and what the index costs

> [!key]
> A **community** is a group of nodes with more edges inside than chance would give. **Modularity** Q measures that: the fraction of edges inside communities minus the fraction expected if edges were rewired at random with the same degrees. **Louvain** raises Q greedily by moving single nodes to the neighbouring community with the best gain, then merges each community into one node and repeats. It can leave communities badly connected or even disconnected; **Leiden** (Traag et al., 2019) adds a refinement phase that guarantees connected communities and a queue that revisits only nodes whose neighbourhood changed. GraphRAG runs Leiden recursively to get a hierarchy of communities and writes an LLM summary for each.

## Intuition

You are seating wedding guests. Good tables are full of people who know each other, and a table is impressive only if those friendships are more than you would expect anyway: putting the two most sociable guests together proves nothing, because they know everybody. Modularity is that "more than expected" score. Improving the seating one guest at a time (move a guest to the table where they gain the most) is Louvain's local move.

## How it works

### Modularity

For an undirected graph with m edges, community c with L_c internal edges and degree sum d_c:

```text
Q = sum over communities c of [ L_c / m  -  gamma · (d_c / 2m)^2 ]
```

The first term is the share of edges inside c; the second is the share a random rewiring with the same degrees would put inside c. The **resolution** gamma (1 by default) trades off size: larger gamma, more and smaller communities. On two triangles joined by one edge (7 edges), all singletons give Q = -0.1735, everything in one community gives 0, and the two triangles give 0.3571.

### The gain of one move

Take node u (degree k) out of its community. Putting it into community C, which it touches with k_C edges and whose remaining degree sum is D_C, changes Q by

```text
gain(C) = k_C / m  -  gamma · k · D_C / (2 m^2)
```

Local moving computes this for each neighbouring community (and for going back) and picks the best. Only u's neighbours matter, so evaluating a node costs O(deg u).

### Louvain, and what goes wrong

Louvain alternates two phases: **local moving** until no single move helps, then **aggregation**, where each community becomes one node (internal edges become a self-loop) and local moving runs again on the smaller graph. It is fast and popular, but a node that held a community together can later move out, leaving the rest split, and once communities are aggregated nobody can split them again. Traag et al. found up to 25% of communities badly connected and up to 16% disconnected in their experiments.

### What Leiden adds

- **Fast local moving.** A queue holds all nodes in random order. Pop a node, move it if that helps, and if it moved, append its neighbours that are not in its new community and not already queued. After the first sweep, only nodes whose neighbourhood changed are revisited.
- **Refinement.** Inside each community, start from singletons and merge only nodes that are well connected to the community, picking randomly among improving merges. Aggregation uses these refined pieces, so a community can be split later.
- **Guarantees.** After every iteration, communities are connected (gamma-connected, in the paper's terms). After an iteration that changes nothing, every node is locally optimally assigned. Optimising modularity exactly is NP-hard, so these are guarantees about the heuristic's output, not optimality.

### How GraphRAG uses it

GraphRAG builds an entity graph with an LLM, then runs **hierarchical Leiden** (from the graspologic library): it detects communities, then recursively detects sub-communities inside each one until they are below a size threshold (`max_cluster_size`, default 10). Each level is a complete partition of the nodes. An LLM writes a report for every community, leaves first; a global question is answered by map-reduce over the reports of one level. On the paper's podcast dataset the levels C0 to C3 had 34, 367, 969 and 1,310 communities, and answering from root-level (C0) summaries needed over 97% fewer tokens than map-reduce over the source text.

## Cost

One local-moving pass costs O(n + m): each node is popped once and pays for its degree, plus queue work for each move. The queue makes later passes cheaper than full sweeps. There is no neat bound on the number of passes, but it is small in practice: in my runs of the template on graphs of 90 to 5,000 nodes, local moving became stable within 2 to 4 passes. Aggregation shrinks the graph, so later levels cost less again.

For GraphRAG the graph algorithm is the cheap part: the LLM calls that write one report per community dominate the indexing bill. The size threshold controls how many communities, and therefore how many reports, you pay for.

## When to use it

| Goal | Tool |
|---|---|
| Split into pieces with no edges between them | Connected components (BFS or union-find), O(n + m) |
| Groups of densely linked entities, no target count | Leiden (or Louvain) on modularity |
| A fixed number of clusters of embedding vectors | k-means on the vectors, not the graph |
| Themes of a whole corpus for an LLM to summarise | GraphRAG: hierarchical Leiden, then community reports |

Use communities for summarising, navigating and visualising large entity graphs, for "what are the main themes" questions, and as a preprocessing step that divides LLM work into independent chunks. Do not use them as labels without checking: different seeds give different partitions, and modularity has a **resolution limit** (it can merge small genuine communities into bigger ones).

## Worked trace

Two triangles {0, 1, 2} and {3, 4, 5} joined by the edge 2-3; m = 7. Queue order 0..5, every node starts alone. Gains use the formula above.

```steps
Pop 0 (degree 2): joining 1 gains 0.102, joining 2 gains 0.082; move to C1. Q = -0.071
    node    0  1  2  3  4  5
    comm   {{1}} 1  2  3  4  5      queue [1 2 3 4 5]
---
Pop 1: already with 0; staying is best. Pop 2 (degree 3): C1 gains 0.163, C3 only 0.051; move. Q = 0.092
    comm    1  1 {{1}} 3  4  5      queue [3 4 5]
---
Pop 3: C1 now loses (-0.071, its degree sum is large); C4 and C5 tie at 0.082, take C4; requeue neighbour 2. Q = 0.174
    comm    1  1  1 {{4}} 4  5      queue [4 5 2]
---
Pop 4: C5 (0.102) beats staying with 3 (0.082); move and requeue 3. Q = 0.194
    comm    1  1  1  4 {{5}} 5      queue [5 2 3]
---
Pop 5 and 2: no better move. Pop 3: C5 now gains 0.163, so 3 joins 4 and 5; requeue 2. Q = 0.357
    comm    1  1  1 {{5}} 5  5      queue [2]
---
Pop 2: moving to C5 would lose 0.071; it stays. Queue empty: two triangles, Q = 0.3571
    comm    1  1  1  5  5  5      queue []
```

Node 2 was popped three times and node 3 twice, because their neighbours kept changing; nodes 0, 1, 4 and 5 were popped once each. That is the fast local move doing its job.

## Template

```python
import random
from collections import defaultdict, deque


def modularity(adj, comm, gamma=1.0):
    """adj: {u: set(neighbours)} undirected, no self-loops; comm: {u: community id}.
    Q = sum over communities of L_c/m - gamma * (d_c / 2m)^2."""
    m = sum(len(vs) for vs in adj.values()) / 2
    inside, degree = defaultdict(float), defaultdict(float)
    for u, vs in adj.items():
        degree[comm[u]] += len(vs)
        inside[comm[u]] += sum(1 for v in vs if comm[v] == comm[u]) / 2
    return sum(inside[c] / m - gamma * (degree[c] / (2 * m)) ** 2 for c in degree)


def local_moving(adj, comm, gamma=1.0, seed=0):
    """One pass of Leiden's fast local move: a queue of nodes; move each to the neighbouring
    community with the largest modularity gain; re-queue only neighbours that may now want to
    move. Returns (communities, number of moves)."""
    comm = dict(comm)
    m = sum(len(vs) for vs in adj.values()) / 2
    tot = defaultdict(float)                 # total degree of each community
    for u in adj:
        tot[comm[u]] += len(adj[u])
    order = list(adj)
    random.Random(seed).shuffle(order)
    queue, queued, moves = deque(order), set(order), 0
    while queue:
        u = queue.popleft()
        queued.discard(u)
        k, old = len(adj[u]), comm[u]
        links = defaultdict(int)             # edges from u into each neighbouring community
        for v in adj[u]:
            links[comm[v]] += 1
        tot[old] -= k                        # take u out, then price every option
        gain = lambda c: links[c] / m - gamma * k * tot[c] / (2 * m * m)
        best = max(links, key=gain, default=old)
        if gain(best) <= gain(old):
            best = old
        tot[best] += k
        if best != old:
            comm[u], moves = best, moves + 1
            for v in adj[u]:
                if comm[v] != best and v not in queued:
                    queue.append(v)
                    queued.add(v)
    return comm, moves


def split_disconnected(adj, comm):
    """Give every connected piece of a community its own id (what Leiden's refinement guarantees)."""
    out, next_id = {}, 0
    for u in adj:
        if u in out:
            continue
        stack = [u]
        out[u] = next_id
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if y not in out and comm[y] == comm[u]:
                    out[y] = next_id
                    stack.append(y)
        next_id += 1
    return out


def cluster(adj, gamma=1.0):
    """Repeat local moving until a pass moves nothing, then split disconnected communities."""
    comm, moves = {u: u for u in adj}, 1
    while moves:
        comm, moves = local_moving(adj, comm, gamma)
    return split_disconnected(adj, comm)
```

This is a teaching sketch of one level, without aggregation or Leiden's randomised refinement. I checked that `modularity` matches `networkx` on 200 random partitions (two resolutions), that every final partition is locally optimal (no single move raises Q), and that splitting disconnected pieces never lowers Q. On 60 planted-partition graphs it reached on average 0.963 of the modularity of NetworkX's full Louvain (worst 0.816): aggregation is what closes that gap. In production use graspologic, igraph or the authors' leidenalg package.

## Pitfalls

- **Treating one run as the truth.** Both algorithms are randomised. Fix a seed for reproducible indexes (GraphRAG's config has one) and check stability across seeds before you trust a community's boundaries.
- **The resolution limit.** Modularity can merge small real communities in a big graph. Raise gamma, or recurse inside large communities as GraphRAG does.
- **Edgeless graphs and isolated nodes.** With m = 0 the formula divides by zero; isolated nodes are communities of one. Drop or handle them first.
- **Disconnected communities.** If you use plain Louvain, at least split each community into connected components afterwards; summarising two unrelated fragments as one "theme" produces nonsense reports.
- **Modularity is not accuracy.** A higher Q is not proof that the groups mean anything. Read a sample of communities.

## Check yourself

Q: Compute Q for the two triangles joined by one edge, with each triangle as a community.
A: m = 7. Each triangle has 3 internal edges and degree sum 2 + 2 + 3 = 7. Q = 2 × (3/7 - (7/14)^2) = 2 × (0.4286 - 0.25) = 0.3571.

Q: Why can Louvain end with a disconnected community, and how does Leiden prevent it?
A: A node that bridged two parts of its community can move to another community when that raises Q, and the remaining parts can each still be locally optimal, so nothing moves them. After aggregation the community is a single node and cannot be split. Leiden refines each community into well-connected sub-communities before aggregating and builds the aggregate graph from those, so a community that has become disconnected can still be split in later levels; its guarantee is that communities are connected after every iteration.

Q: In the trace, why did node 3 refuse to join the left triangle even though it has an edge to node 2?
A: Its gain for C1 was 1/7 - 3 × 7 / (2 × 49) = -0.071: the left triangle's degree sum (7) is so large that a random rewiring would already put more than one of node 3's edges there, so one real edge is less than expected.

Q: You run GraphRAG on a corpus and get 40,000 leaf communities, far too many reports to pay for. Which knob do you change first, and what does it trade?
A: Raise `max_cluster_size` (or stop the recursion earlier), so communities are larger and fewer reports are written. Each report then covers more entities, so leaf-level answers are less detailed.

## Lab

- Run `cluster` on the two triangles, then add the edge (1, 4) and run it again. Expected: {0, 1, 2} and {3, 4, 5} both times, with Q = 0.3571 and then 0.25.
- Build a planted graph: 90 nodes in 3 groups of 30, `random.Random(2)`, and for each pair u < v add the edge if `rng.random() < (0.3 if u // 30 == v // 30 else 0.01)`. Expected: 427 edges; the planted split has Q = 0.5973; `cluster` finds 5 communities with Q = 0.5321; NetworkX's `louvain_communities(G, seed=2)` recovered the 3 planted groups (Q = 0.5973) in my run.

> [!know]
> You now know how modularity, local moving and Leiden's refinement work, and how GraphRAG turns them into a hierarchy of communities to summarise.

=== primer | How do you run an agent workflow as a DAG: order, parallel branches, loops and crash recovery? | 15 min
goal: Schedule a workflow with Kahn's algorithm in waves, merge parallel branches safely, bound loops, and resume from a checkpoint without redoing finished nodes
tag: aigraph-dagrun | Waves, checkpoints and resume
link: LangGraph checkpointers | https://docs.langchain.com/oss/python/langgraph/checkpointers#super-steps | About 5 min: 'Super-steps' and 'Pending writes': a checkpoint at every super-step boundary, per-node writes that let a resumed run skip the nodes that already succeeded
link: LangGraph: defer node execution | https://docs.langchain.com/oss/python/langgraph/use-graph-api#defer-node-execution | About 5 min: Fan-in when branches have different lengths: defer=True versus a list-form edge that waits for all listed nodes

> [!key]
> An agent workflow with dependencies is a directed graph of steps. **Kahn's algorithm** gives a safe order: repeatedly run the nodes whose dependencies are all done. Running each "ready" set as a **wave** gives parallel branches for free; merge their updates only after the whole wave, with an explicit rule (a **reducer**) for keys several branches write. Real agents loop, so collapse each loop into a node with a hard round limit and keep a global step limit. Save the state after every wave (a **checkpoint**), and keep the outputs of branches that finished in a failed wave, so a crashed run resumes where it stopped. LangGraph's super-steps, checkpointers and recursion limit follow this design.

## Intuition

Cooking a dinner for friends. Chopping vegetables and boiling water do not depend on each other, so two people do them at once; the sauce needs both. "Taste and adjust" is a loop, but nobody tastes forever: three rounds, then serve. And you keep notes as you go, so if the power cuts out you do not boil the water again: you start from the last note.

## How it works

### Kahn's algorithm in waves

Count, for every node, how many dependencies it is still waiting for (its in-degree). Wave 1 is every node with count 0. When a wave finishes, decrement the count of every node that depends on a finished node; those that reach 0 form the next wave. If nodes remain with a count above 0 when no wave is left, they sit on a cycle (or wait for something on a cycle): report them instead of hanging. Each node lands in the earliest wave possible: its wave number is the length of the longest dependency chain leading to it.

### Parallel branches and merging

Run a wave's nodes concurrently, each on its own copy of the state, and merge their returned updates **after** the wave, in a fixed order. Two rules make the merge safe:

- keys that several branches may write need a **reducer** (here: lists are appended);
- two branches writing the same plain key in one wave is an error, not a race to be won.

LangGraph works the same way: nodes that run in parallel are in the same super-step, a super-step is transactional (if any branch raises, none of that super-step's updates are applied), and its docs warn that updates from a parallel super-step may not arrive in a consistent order.

### Waves versus a ready queue

A wave waits for its slowest node before the next wave starts: a **barrier**. A ready-queue scheduler instead starts each node the moment its own dependencies finish, and needs only the **critical path** (the longest chain of durations). Barriers cost time when branches have different lengths, but they make checkpoints simple: there is a clean, consistent state after every wave. LangGraph chose barriers (Pregel's bulk-synchronous model); when branches have different lengths, its docs offer `defer=True` or a list-form edge, which runs the join node once after all listed nodes finish.

### Loops

A DAG cannot say "revise until the reviewer approves". Take the strongly connected components of the workflow graph (each loop is one component), and the graph of components is a DAG. Run that DAG in waves, and run each component as one node that repeats its body until a check passes or a round limit is hit. Keep a global step limit as well. LangGraph raises `GraphRecursionError` when a run exceeds its recursion limit; its docs give a default of 10,007 super-steps from version 1.1.4 (10,000 between 1.0.6 and 1.1.3), so set a tighter limit yourself.

### Checkpoints and resume

After each wave, persist the state and the set of finished nodes under the run's id. If a node in a wave fails, persist the outputs of the nodes in that wave that succeeded (**pending writes**) and re-raise. A rerun with the same id loads the checkpoint, skips finished nodes, reuses pending outputs and runs only what is left. LangGraph's checkpointer stores per-task writes for exactly this reason: successful nodes in a failed super-step are not rerun on resume.

## Cost

Kahn's algorithm touches every node and edge once: **O(V + E)**. The critical path is a dynamic programme over the same order: finish(u) = duration(u) + max finish of u's dependencies, also O(V + E).

Wall-clock time for wave scheduling is the sum, over waves, of the longest node in each wave; for a ready queue it is the critical path; for one worker it is the sum of all durations. In the trace example these are 22 s, 19 s and 26 s.

Checkpoints cost one state write per wave: O(waves × state size) storage if you keep history (needed for time travel and debugging), O(state size) if you keep only the latest. Large states (long message lists) make this the dominant cost; store large blobs elsewhere and keep references in the state.

## When to use it

| Workflow | Tool |
|---|---|
| Open-ended task, the model decides each step | An agent loop (model, tools, repeat) with a step limit |
| Known steps with dependencies, some parallel, some loops | A graph runtime: waves, reducers, bounded loops, checkpoints (LangGraph and similar) |
| Long-running business process, many external calls, must survive deploys | A durable execution engine (Temporal, Restate, DBOS), or a graph runtime with a durable checkpointer |
| Build or data pipeline with no loops | A DAG scheduler (Make, Bazel, Airflow) |

The AI page's [graph engineering module](https://learningcurie.github.io/code-study-tracker/ai.html#l-l-graphs-why-graphs-workflows-as-state-machines) covers when an explicit graph beats a free agent loop, and [state design and reducers](https://learningcurie.github.io/code-study-tracker/ai.html#l-l-graphs-state-design-and-reducers) shows the same merge rules in LangGraph syntax.

## Worked trace

A research agent: plan, then three searches in parallel, a rerank step after the document search, merge, draft, publish. Durations in seconds: plan 2, search_web 6, search_docs 3, query_db 1, rerank_docs 4, merge 1, draft 8, publish 1. search_web times out on its first attempt.

```steps
In-degrees: plan 0, the three searches 1, rerank_docs 1, merge 3, draft 1, publish 1. Wave 1 = [plan]
    wave 1   {{plan}}
    state    log [plan]          checkpoint: done [plan]
---
plan done: the three searches drop to 0. Wave 2 runs them in parallel; search_web times out
    wave 2   search_web  {{search_docs}}  {{query_db}}
    result   timeout     ok               ok
---
The wave is all-or-nothing: no update is applied, but the two finished branches are saved as pending
    checkpoint: done [plan]
                pending {search_docs: ..., query_db: ...}
---
Resume with the same run id: only search_web runs again; the pending outputs are merged with it
    wave 2   {{search_web}} (retry)   search_docs (pending)   query_db (pending)
    state    log [plan, search_web, search_docs, query_db]
---
search_docs done unlocks rerank_docs; merge still waits (2 of 3 inputs)
    wave 3   {{rerank_docs}}
    in-degree of merge: 3 -> 1
---
Waves 4 to 6 run merge, draft, publish. Every node except search_web ran exactly once
    waves    [plan] [web docs db] [rerank] [merge] [draft] [publish]
    time     waves 22 s, critical path 19 s, sequential 26 s
```

## Template

```python
import copy
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor


def topo_waves(deps):
    """deps: {node: [nodes it waits for]}. Kahn's algorithm, one wave at a time:
    every node in a wave has all its dependencies in earlier waves. Raises on a cycle."""
    indeg = {u: len(ds) for u, ds in deps.items()}
    users = defaultdict(list)
    for u, ds in deps.items():
        for d in ds:
            users[d].append(u)
    wave, waves = [u for u in deps if indeg[u] == 0], []
    while wave:
        waves.append(wave)
        nxt = []
        for u in wave:
            for v in users[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    nxt.append(v)
        wave = nxt
    stuck = [u for u in deps if indeg[u] > 0]
    if stuck:
        raise ValueError(f"cycle: {stuck} never became ready")
    return waves


def run(deps, funcs, state, store, run_id, workers=4):
    """Run node functions wave by wave; funcs[u](state) returns a dict of updates.
    List values are appended (a reducer); two writes to the same plain key in one wave fail.
    A wave is all-or-nothing: if a branch raises, no update is applied, but finished
    branches are saved as pending and are not rerun when the same run_id resumes."""
    saved = store.get(run_id) or {"state": state, "done": [], "pending": {}}
    state, done = copy.deepcopy(saved["state"]), set(saved["done"])
    pending = dict(saved["pending"])
    for wave in topo_waves(deps):
        todo = [u for u in wave if u not in done]
        if not todo:
            continue
        with ThreadPoolExecutor(workers) as pool:          # branches see the same input
            futures = {u: pool.submit(funcs[u], copy.deepcopy(state))
                       for u in todo if u not in pending}
        errors = []
        for u, fut in futures.items():
            try:
                pending[u] = fut.result()
            except Exception as e:
                errors.append(e)
        if errors:
            store[run_id] = {"state": copy.deepcopy(state), "done": sorted(done), "pending": pending}
            raise errors[0]
        written = set()
        for u in todo:                                      # merge only after the whole wave
            for key, val in pending.pop(u).items():
                if isinstance(val, list):
                    state[key] = state.get(key, []) + val
                elif key in written:
                    raise ValueError(f"two branches wrote {key!r} in one wave")
                else:
                    state[key] = val
                    written.add(key)
        done.update(todo)
        store[run_id] = {"state": copy.deepcopy(state), "done": sorted(done), "pending": {}}
    return state


def bounded_loop(step, good_enough, max_rounds):
    """Collapse a cycle (draft -> review -> draft ...) into one node with a hard bound."""
    def node(state):
        out = {}
        for rounds in range(1, max_rounds + 1):
            out = step({**state, **out})
            if good_enough({**state, **out}):
                break
        return {**out, "rounds": rounds}
    return node
```

`store` is any dict-like object; in production it is a database table keyed by run id, written in a transaction. Checks: on 500 random graphs, `topo_waves` respects every dependency, puts each node in its earliest possible wave (the longest-chain depth computed with NetworkX) and detects every cycle that `networkx.is_directed_acyclic_graph` reports; on 200 random DAGs with a failure injected into a random node, `run` produced the same final state as a sequential execution and every node except the failed one ran exactly once.

## Pitfalls

- **Non-idempotent side effects.** A failed node runs again on resume. If it sent an email before failing, the email goes twice. Make side effects idempotent (an idempotency key) or put them in their own node after the checkpoint.
- **Merging in arrival order.** Threads finish in any order; merge in a fixed node order, or sort by a field, so reruns give identical state.
- **Shared mutable state.** Give each branch a copy. Two threads appending to the same list object produce bugs that never reproduce.
- **Unbounded loops.** Every loop needs both its own round limit and the global step limit; the round limit gives a useful answer ("best draft after 5 rounds"), the global limit only an exception.
- **Joins with unequal branches.** In a runtime that triggers a node whenever any input changes, a join after branches of different lengths can run twice. Waves avoid this; in LangGraph use `defer=True` or a list-form edge.
- **Threads for CPU work.** Threads overlap waiting on LLM and HTTP calls; CPU-heavy nodes in Python need processes, or an async runtime for many concurrent calls.

## Check yourself

Q: Give the waves for: plan; search_web, search_docs and query_db depend on plan; rerank_docs on search_docs; merge on search_web, rerank_docs and query_db; draft on merge; publish on draft.
A: [plan], [search_web, search_docs, query_db], [rerank_docs], [merge], [draft], [publish]. merge waits for wave 3 because its in-degree reaches 0 only after rerank_docs finishes.

Q: Why does wave scheduling take 22 s in the trace when the critical path is only 19 s?
A: Wave 2 lasts 6 s (search_web, the slowest), and rerank_docs cannot start until the whole wave ends, although its own input (search_docs, 3 s) finished at second 5. A ready queue would start it then: plan 2 + docs 3 + rerank 4 + merge 1 + draft 8 + publish 1 = 19 s.

Q: Without pending writes, what would happen on resume after search_web failed, and why does it matter for an agent?
A: The whole of wave 2 would run again, repeating search_docs and query_db. With LLM or paid API calls that is wasted money and time, and any non-idempotent effect in those nodes happens twice.

Q: You add an edge review -> draft so the reviewer can send work back. What does `topo_waves` do, and how should you model the loop instead?
A: It raises ValueError naming draft, publish and review, because draft now waits for review, which waits for draft. Collapse draft and review into one `bounded_loop` node (repeat until the review passes or a round limit), so the outer graph stays a DAG.

## Lab

- Run `topo_waves` on the research workflow and compute the three timings from the durations. Expected: the six waves above; sequential 26 s, waves 22 s, critical path 19 s.
- Add `review` with `deps["review"] = ["draft"]` and change draft's dependencies to `["merge", "review"]`. Expected: `ValueError: cycle: ['draft', 'publish', 'review'] never became ready`.
- Make search_web raise `TimeoutError` on its first call, run, catch the error, inspect `store`, and run again. Expected: the checkpoint shows done ['plan'] and pending outputs for search_docs and query_db; after resuming, the log is plan, search_web, search_docs, query_db, rerank_docs, merge, draft, publish, and search_web is the only node called twice.
- Use `bounded_loop` with a step that adds 3 to a score, `good_enough = score >= 8` and `max_rounds = 5`. Expected: {'score': 9, 'rounds': 3}. With a target of 100 and steps of 1: {'score': 5, 'rounds': 5}.

> [!know]
> You now know how to run a dependency graph of agent steps in parallel waves, bound its loops, and checkpoint it so a crash costs only the work that failed.

=== lab | PageRank and personalised PageRank, checked against an exact solve | 45 min
goal: Implement power-iteration PageRank and personalised PageRank on a generated graph, verify them against an exact linear solve, and measure convergence against the 2·d^k bound
link: NetworkX pagerank | https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html | About 5 min: An independent implementation to cross-check your scores (pass alpha, personalization and a small tol)

> [!key]
> Power iteration is cheap and approximate; a linear solve is exact and expensive. On a 200-node graph you can afford both, so use the solve as the oracle, then measure how fast the iteration really converges compared with the worst-case bound.

## Steps

1. Generate the graph. Use exactly this generator so your numbers match the expected ones (it only calls `rng.random()`, which is stable across Python versions):

```python
import random


def generate(n=200, seed=42, max_out=4, p_dangling=0.1):
    rng = random.Random(seed)
    g = {}
    for u in range(n):
        if rng.random() < p_dangling:
            g[u] = []
            continue
        k = 1 + int(rng.random() * max_out)
        targets = set()
        while len(targets) < k:
            w = int(rng.random() * n)
            if w != u:
                targets.add(w)
        g[u] = sorted(targets)
    return g
```

2. Copy `pagerank` from the first card. Run it with d = 0.85 and tol = 10^-10 (it starts from the teleport vector and stops when the L1 change is below tol). Record the iteration count and the top five nodes.
3. Write the exact oracle with NumPy. Build S with S[w, u] = 1/out(u) for every edge u -> w, replace the column of each dangling node with the teleport vector t, and solve (I - d·S)·x = (1 - d)·t:

```python
import numpy as np


def exact_pagerank(g, d=0.85, teleport=None):
    n = len(g)
    v = np.zeros(n)
    if teleport is None:
        v[:] = 1 / n
    else:
        for u, wgt in teleport.items():
            v[u] = wgt
        v /= v.sum()
    S = np.zeros((n, n))
    for u, targets in g.items():
        if targets:
            for w in targets:
                S[w, u] += 1 / len(targets)
        else:
            S[:, u] = v
    return np.linalg.solve(np.eye(n) - d * S, (1 - d) * v)
```

4. Compare the largest absolute difference between the two answers, and check that the power-iteration scores sum to 1.
5. Personalise: teleport `{0: 1, 1: 1}`. Repeat steps 2 to 4, print the out-links of nodes 0 and 1, and count how many nodes end with non-zero mass.
6. Convergence experiment: for d in 0.5, 0.85 and 0.95, start from uniform, apply one step at a time and count steps until the L1 distance to the exact solution drops below 10^-8. Compare with the bound ceil(log(10^-8 / 2) / log d).
7. Tightness: build a directed ring of 100 nodes (u -> u + 1 mod 100), personalise on node 0 with d = 0.85, and print the ratio of successive L1 errors and the number of steps to reach 10^-6.
8. Write two sentences: when would you use the exact solve in production, and what would you check if power iteration needed far more steps than the bound predicts?

## What you should see

- The graph has 200 nodes, 416 edges and 15 dangling nodes.
- PageRank: 43 iterations; the largest difference from the exact solve is far below 10^-10 (3.4e-12 in my run, floating-point rounding); the sum is 1.000000. Top five: node 49 (0.0217), 110 (0.0193), 84 (0.0185), 127 (0.0169), 196 (0.0166).
- Personalised from {0, 1}: 62 iterations, again matching the exact solve to about 10^-12. Top five: 1 (0.1327), 0 (0.1312), 55 (0.1170), 178 (0.0377), 135 (0.0376). Node 0's only out-link is 55, which is why 55 is third; node 1 links to 17, 135 and 178. 166 of the 200 nodes have non-zero mass: the rest cannot be reached from the seeds (dangling mass returns to the seeds, not to them).
- Convergence to 10^-8: 16 steps at d = 0.5 (bound 28), 34 at 0.85 (bound 118), 43 at 0.95 (bound 373). Real graphs beat the bound comfortably.
- The ring: every ratio is exactly 0.85 and it takes 89 steps to reach 10^-6, which is the bound: a ring only rotates the error, so nothing but damping shrinks it.
- If your numbers differ, check, in this order: edge direction in S (column u is the source), the dangling columns, the teleport normalisation, and the stopping rule.
