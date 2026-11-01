"""DSA field guide: page metadata and stages. Module content lives in dsa/NN-key.md (see build_dsa_guide.py)."""
TRACK = dict(
    file="dsa.html", storageKey="dsa-status", contentDir="dsa-lessons",
    title="Data structures and algorithms: a field guide",
    subtitle=("A work-in-progress guide to problem-solving patterns and the structures inside real software. "
              "Lessons, projects and selected full problem solutions are available; other solution cards are not yet complete. "
              "New lesson references have not all been independently verified."),
    searchHint="Search cards and problems (name or number)",
    projects=("Build a project alongside each stage, then combine the ideas in the mastery capstones. "
              "Each project includes a specification, measurable checks and one-to-two-hour milestones."),
    routine=[
        "Press <b>Start</b>. Today's session lists about an hour of work: new cards, one problem on an idea you have met, and one review item. It ticks off as you go.",
        "<b>Cards</b> teach one idea in 10 to 20 minutes, right on this page. Answer <b>Check yourself</b> before revealing, then press <b>Done, next card</b>.",
        "<b>Problems</b>: open the original statement, solve it in your editor and use the hints if needed. Full in-page solutions are not yet available for every problem.",
        "Mark problems <b>Solved</b> (you wrote brute force and optimal), <b>Brute only</b> or <b>Stuck</b>. Anything not solved, or marked Needs practice, comes back for review after three days.",
        "<b>Projects</b> have independent milestones; tick them as you build. Go deeper links are optional.",
    ],
)

STAGES = [
    dict(key="found", name="Foundations and workflow", short="Foundations",
         intro="The habits everything else relies on: a repeatable routine for problems you have not seen, predicting cost from constraints before you code (including amortised cost and what the Python built-ins really cost), recursion you can trust, and proving and stress-testing that code is correct."),
    dict(key="contain", name="Core containers", short="Containers",
         intro="Compact recaps of arrays, hash tables, linked lists, stacks and queues: how CPython's list, dict, set and deque work inside, the templates worth knowing by heart, and the pitfalls that cost marks."),
    dict(key="scan", name="Scanning patterns", short="Scanning",
         intro="Recaps of the one-pass patterns: two pointers, sliding windows, prefix sums, binary search (and bisect) and monotonic stacks and queues. Each is a small state plus an invariant, with a template and its traps."),
    dict(key="order", name="Order: sorting, heaps and intervals", short="Order",
         intro="Sorting as a recap (including Timsort and powersort inside CPython), then full primers on heaps and priority queues and on interval and sweep-line problems."),
    dict(key="hier", name="Trees", short="Trees",
         intro="Tree recursion in both directions, traversals, binary search trees and the ordered maps you actually use, and tries: the bridge from linear scans to graphs and dynamic programming."),
    dict(key="network", name="Graphs", short="Graphs",
         intro="Model a problem as a graph, then traverse it (BFS, DFS, topological order), connect it (union-find and minimum spanning trees) and find weighted shortest paths."),
    dict(key="strategy", name="Search, dynamic programming and greedy", short="DP and greedy",
         intro="Backtracking explores every choice, dynamic programming shares the subproblems backtracking repeats, and greedy commits to one choice only when it is provably safe. Learned in that order, \"greedy or DP?\" becomes a decision you can make."),
    dict(key="engineer", name="Designing structures and specialist tools", short="Design and tools",
         intro="Compose structures to meet stated costs (LRU and LFU caches, iterators, time-based stores), then the specialist tools some problems need: string algorithms, bits and number theory, and Fenwick and segment trees."),
    dict(key="prod", name="DSA in production systems", short="Production",
         intro="Where the structures live at work: B+ trees, LSM trees and write-ahead logs in storage engines; LRU, TinyLFU, S3-FIFO and SIEVE in caches; inverted indexes and tries in search; consistent hashing and Merkle trees; Bloom filters and sketches; and the algorithms inside diff, merge, regex engines and build tools."),
    dict(key="aisys", name="DSA behind AI systems", short="AI systems",
         intro="The data structures and algorithms inside AI systems: vector indexes from KD-trees to HNSW and DiskANN, paged KV caches and radix-tree prefix caching, decoding and sampling, BPE tokenisers, graph retrieval and agent DAGs, and dataset deduplication. Cross-linked to the AI guide rather than repeating it."),
    dict(key="frontier", name="Frontier (optional)", short="Frontier",
         intro="Short, optional reads on recent results: machine-discovered sorting routines, a faster shortest-path algorithm, new open-addressing bounds, learned indexes, Swiss tables and the newest default sorts, each checked against its primary source."),
    dict(key="mastery", name="Mastery: mixed practice and capstones", short="Mastery",
         intro="Recognition and transfer come from mixed, unlabelled practice and from deriving solutions to problems you have not seen. The review sets open along the route, and the capstones bring the earlier stages together."),
]
