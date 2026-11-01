---
key: search
name: Search engines: inverted indexes, ranking and type-ahead
stage: prod
summary: How a search box answers in milliseconds over millions of documents: posting lists, fast intersection, BM25 ranking, top-k pruning, compressed postings, prefix completion and typo tolerance.
why: Search is the clearest case of DSA deciding whether a product works. A naive scan touches every byte for every query; a search engine does the work once at index time (an inverted index of sorted posting lists) and then answers each query by touching a few lists, intersecting them with galloping search, scoring with BM25, keeping the best k in a heap and skipping documents that cannot make the cut. The same structures sit inside Elasticsearch, OpenSearch, Solr, PostgreSQL full-text search, SQLite FTS5 and the keyword half of every hybrid retrieval (RAG) system, so understanding them lets you predict latency, size an index and debug "why is this result missing?" instead of guessing.
outcomes:
- Build a positional inverted index and answer AND, OR and phrase queries from it
- Intersect posting lists with merge or galloping search and choose between them from the list sizes
- Compute BM25 scores from index statistics, term at a time or document at a time
- Return the top k results with a size-k heap and explain how WAND and block-max WAND skip documents safely
- Compress posting lists with gaps, varints and bit-packed blocks, and estimate the bytes per posting
- Serve top-k prefix completions from a trie with subtree maxima, and explain where Lucene uses FSTs and tries
- Find dictionary words within edit distance k with a trie walk, a BK-tree or symmetric deletes, and say which scales
cues:
- "Find documents containing these words" over data that is queried far more often than it changes
- One list is tiny and the other is huge (a rare word AND a common word): skip, do not scan
- "Only the top 10 matter" while thousands of documents match
- An index that must fit in RAM or be read from disk quickly: sorted integers with small gaps
- Suggestions on every keystroke, or "did you mean" for misspelled queries
traps:
- Indexing with one analyser (lowercase, stemming) and querying with another, so lookups silently miss
- Scoring every matching document when only k are shown, or sorting all matches to take the first k
- Galloping when both lists are similar in size (a plain merge is faster), or merging a 10-item list against a million
- Forgetting that a deleted document is only marked dead until segments merge, so counts and statistics lag
- Using plain Levenshtein for typos and missing transpositions ("teh" is 2 edits from "the" without them)
systems:
- Lucene (inside Elasticsearch, OpenSearch and Solr): immutable segments merged in the background, d-gap postings packed in 256-integer blocks in the 10.4 format, skip data with per-block impacts for block-max WAND, a per-field prefix FST (Lucene 9) or trie (Lucene 10.3 and later) over on-disk term blocks
- PostgreSQL's GIN index is a generalised inverted index: it stores (key, posting list) pairs for full-text and array search; SQLite FTS5 ships a built-in bm25() ranking function
- Redis Search keeps autocomplete suggestions in a trie (FT.SUGADD, FT.SUGGET, with a FUZZY option for one edit); Lucene's AnalyzingSuggester stores suggestions in a weighted FST
- Lucene's FuzzyQuery matches up to 2 edits (Damerau-Levenshtein by default) by intersecting a Levenshtein automaton with the term dictionary
further:
- Docs · 15 min | Lucene 10.4 index file formats: definitions, segments and document numbers | https://lucene.apache.org/core/10_5_0/core/org/apache/lucene/codecs/lucene104/package-summary.html#Segments
- Article · 15 min | Elastic: Faster retrieval of top hits with block-max WAND | https://www.elastic.co/blog/faster-retrieval-of-top-hits-in-elasticsearch-with-block-max-wand
- Article · 45 min | Andrew Gallant: Index 1,600,000,000 keys with automata and Rust | https://burntsushi.net/transducers/#finite-state-machines-as-data-structures
- Lesson · 12 min | AI guide: Hybrid search and reciprocal rank fusion | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-hybrid-search-and-score-fusion
---

=== primer | How does a search engine find every document that contains a word? | 15 min
goal: Build a positional inverted index, answer AND, OR and phrase queries from it, and explain how a real engine keeps one up to date
tag: search-invidx | Inverted index
link: Lucene 10.4 index file formats | https://lucene.apache.org/core/10_5_0/core/org/apache/lucene/codecs/lucene104/package-summary.html#Segments | 10 min. Read 'Inverted Indexing', 'Segments' and 'Document Numbers': how a production engine splits the index into independent segments, merges them, and why document numbers change after a merge
link: AI guide: Keyword search and BM25 | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-keyword-search-and-bm25 | 12 min. Where the inverted index sits in a retrieval pipeline and the queries on which keyword search beats embeddings

> [!key]
> An **inverted index** maps every term to its **posting list**: the ascending ids of the documents that contain it, usually with counts and positions. A query never scans text. It looks up a few lists and combines them: AND is an intersection of sorted lists, OR is a union, and a phrase is an intersection followed by a check that the positions line up.

## Intuition

Think of the index at the back of a textbook: "heap, 112, 140, 301". Nobody reads the book to find heaps; the author read it once, while building the index. A search engine does the same for every word of every document, and it keeps the page numbers (document ids) **in ascending order**, because two sorted lists can be combined in one pass.

The alternative is a scan. `grep` over 10 GB of text reads 10 GB for every query. An inverted index reads only the lists of the query's terms, which for a rare word may be a few hundred integers. You pay once at index time so that every query is cheap.

## How it works

### Text to terms

Documents and queries go through the same **analyser**: lowercase, split into tokens, often strip accents and reduce words to a stem ("running" to "run"). Whatever the analyser does at index time, it must do at query time too, or the lookup misses. The template below uses the simplest analyser: lowercase, keep runs of letters and digits.

### Building

Give documents ids 0, 1, 2, ... in arrival order. For each token at position p of document d, append d (and p) to the term's entry. Because ids only grow, **every posting list is sorted for free**: there is no sorting step. Keep each document's length as well, because ranking needs it.

```text
doc 0: "The cat sat on the mat"   doc 1: "The dog chased the cat"   doc 2: "A dog sat down"

term     posting list (doc: positions)
the      0:[0,4]  1:[0,3]
cat      0:[1]    1:[4]
sat      0:[2]    2:[2]
dog      1:[1]    2:[1]
mat 0:[5]   on 0:[3]   chased 1:[2]   a 2:[0]   down 2:[3]
```

### Querying

- **AND** (`cat sat`): intersect [0, 1] with [0, 2] to get [0]. Start with the rarest term: the result can only shrink, so the shortest list bounds the work.
- **OR**: merge the lists into their union.
- **NOT** (`dog -sat`): walk the first list and skip ids that appear in the second.
- **Phrase** (`"the cat"`): run the AND, then in each candidate document keep the start positions p of "the" for which p + 1 is a position of "cat". That is why the index stores positions.

### Keeping it up to date: segments

A single dictionary that grows forever does not survive production. Lucene (the library inside Elasticsearch, OpenSearch and Solr) splits the index into **segments**: each one is a complete, independent, immutable index. New documents go into a new small segment; background merges combine small segments into larger ones; a search runs over every segment and combines the results. A deletion does not rewrite anything: a per-segment "live documents" bitmap marks the document dead, and it physically disappears when its segment is merged. Document numbers are per segment plus a base offset, which is why Lucene warns that they change after merges. If you know LSM trees from the storage module, this is the same shape: write small sorted runs, merge them later.

## Cost

Let T be the total number of tokens in the corpus and f(t) the length of term t's posting list.

- **Build:** one dictionary update per token, so O(T) expected time. Memory is about one integer per token with positions, or one per (term, document) pair without them.
- **AND:** a merge-based intersection of two lists costs O(f1 + f2). For q terms sorted rarest first, each step costs at most the current result plus the next list, so the total is at most the sum of the list lengths. The next card cuts the cost of a short list against a long one to O(f1 log(f2 / f1)).
- **Phrase:** the AND, plus reading the position lists of the candidate documents.
- **Scan for comparison:** O(T) per query. With T = 10^9 tokens and a query whose lists hold 10^4 postings, the index touches about 100,000 times less data.

## When to use it

Reach for an inverted index when many queries hit a corpus that changes more slowly than it is queried, and queries are made of words or exact tokens (names, error codes, identifiers). Do not use it for:

- **Arbitrary substrings or regular expressions** (`%ase%` inside "database", code search): use a trigram index or a suffix array.
- **Meaning** ("money back" should find "refund"): use embeddings, and usually combine them with keyword search (the AI guide's hybrid search lesson).
- **A one-off search over a small file:** just scan.

| Approach | Work per query | Good at | Weak at |
|---|---|---|---|
| Scan (`grep`, `LIKE '%x%'`) | the whole corpus | small data, ad hoc questions | anything large |
| Inverted index | the posting lists of the query terms | words, phrases, ranking, filters | substrings, synonyms |
| Trigram index | lists of the query's trigrams, then verify | substrings, regex | memory, very short queries |
| Vector index | a few hundred distance computations | meaning, paraphrase | exact ids, rare names |

### In production

Lucene's file-format documentation calls its terms index "an inverted index" because "it can list, for a term, the documents that contain it". PostgreSQL's GIN index is a generalised inverted index: it stores (key, posting list) pairs for full-text search and array containment. SQLite's FTS5 extension is an inverted index with a built-in `bm25()` ranking function.

## Worked trace

Building the index for the three documents above, then answering an AND query and a phrase query.

```steps
Doc 0 "The cat sat on the mat" becomes six tokens; each appends its position to the term's list
    the    -> {{0:[0,4]}}
    cat    -> {{0:[1]}}
    sat    -> {{0:[2]}}
    on     -> {{0:[3]}}
    mat    -> {{0:[5]}}
---
Doc 1 "The dog chased the cat": new postings go at the end, so every list stays sorted by doc id
    the    -> 0:[0,4]  {{1:[0,3]}}
    cat    -> 0:[1]    {{1:[4]}}
    dog    -> {{1:[1]}}
    chased -> {{1:[2]}}
---
Doc 2 "A dog sat down": the index is complete; doc lengths are [6, 5, 4]
    sat    -> 0:[2]  {{2:[2]}}
    dog    -> 1:[1]  {{2:[1]}}
    a      -> {{2:[0]}}
    down   -> {{2:[3]}}
---
Query cat AND sat: both lists have two entries; compare heads 0 and 0, equal, so output 0 and advance both
    cat  {{0}}  1
    sat  {{0}}  2        result [0]
---
Next heads 1 and 2: 1 < 2, so advance cat; cat is exhausted, stop
    cat  0  {{1}}
    sat  0  {{2}}        result [0]
---
Phrase "the cat": the AND gives candidates [0, 1]. Doc 0: starts of "the" are {0, 4}; "cat" at 1 means a start at 1 - 1 = 0
    doc 0   the {0, 4}  cat-1 {0}   overlap {{0}}  -> match
---
Doc 1: starts of "the" {0, 3}; "cat" at 4 means a start at 3; overlap {3}, so both documents match
    doc 1   the {0, 3}  cat-1 {3}   overlap {{3}}  -> match: result [0, 1]
```

## Template

```python
import re
from collections import defaultdict

TOKEN = re.compile(r"[a-z0-9]+")


def tokenise(text):
    """Lowercase and split on anything that is not a letter or digit."""
    return TOKEN.findall(text.lower())


def intersect(a, b):
    """Doc ids present in both ascending lists, by a linear merge."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out


class InvertedIndex:
    """Positional inverted index: term -> {doc_id: [positions]}, doc ids in ascending order."""

    def __init__(self):
        self.index = defaultdict(dict)
        self.doc_len = []                       # tokens per document, for ranking later

    def add(self, text):
        doc_id = len(self.doc_len)              # ids only grow, so every posting list stays sorted
        tokens = tokenise(text)
        for pos, term in enumerate(tokens):
            self.index[term].setdefault(doc_id, []).append(pos)
        self.doc_len.append(len(tokens))
        return doc_id

    def docs(self, term):
        return list(self.index.get(term, {}))

    def search_all(self, query):
        """Documents containing every query term (AND), rarest term first."""
        terms = sorted(set(tokenise(query)), key=lambda t: len(self.index.get(t, {})))
        if not terms:
            return []
        result = self.docs(terms[0])
        for term in terms[1:]:
            result = intersect(result, self.docs(term))
            if not result:
                break
        return result

    def search_phrase(self, phrase):
        """Documents where the terms appear next to each other, in order."""
        terms = tokenise(phrase)
        hits = []
        for doc in self.search_all(phrase):
            starts = set(self.index[terms[0]][doc])
            for offset, term in enumerate(terms[1:], 1):
                starts &= {p - offset for p in self.index[term][doc]}
            if starts:
                hits.append(doc)
        return hits
```

Each posting list is a Python dict, which keeps insertion order, so its keys are the ascending doc ids. A real engine stores flat integer arrays instead (the compression card shows how).

## Pitfalls

- **Analyser mismatch.** Stemming or lowercasing at index time but not at query time (or the reverse) gives silent misses, not errors. Test the analyser on both paths.
- **Stop words.** "the" is in nearly every document, so its list is as long as the corpus. Dropping stop words shrinks the index but breaks phrase queries such as "to be or not to be"; modern engines keep them and rely on ranking and skipping (two cards on).
- **Positions are not free.** They cost about one integer per token, often more than the rest of the index. Store them only for fields that need phrase or proximity queries.
- **Updates are delete plus add.** A changed document gets a new id; the old one is marked dead and lingers until a merge, so document counts and statistics drift until then.
- **Using `self.index[term]` on a missing term** with a `defaultdict` silently inserts an empty entry. Read with `.get` on query paths, as the template does.

## Check yourself

Q: Using the template, index "red fish", "blue fish", "red red fish". What are `docs("red")`, `search_all("fish red")` and `search_phrase("red fish")`?
A: `docs("red")` is [0, 2]. The AND sorts terms rarest first: "red" (2 docs) before "fish" (3 docs), then intersects [0, 2] with [0, 1, 2] to get [0, 2]. The phrase also gives [0, 2]: in doc 2, "red" is at positions 0 and 1 and "fish" at 2, so the start 1 survives.

Q: Why do posting lists come out sorted without any sort, and what breaks if you assign document ids by hashing the URL instead?
A: Ids are handed out in increasing order and each document appends to the end of its terms' lists, so every list is ascending by construction. With hashed ids, appends arrive in random id order, so lists are unsorted: the linear merge intersection is wrong, and you would have to sort every list (or use sets, losing cheap merges and gap compression).

Q: A product team wants "search inside words" (typing "ase" should find "database"). Is the inverted index the right tool?
A: Not on its own: it indexes whole terms, so "ase" is never a key. Use a trigram (n-gram) index, which turns any substring of 3 or more characters into an AND of trigram lists followed by a verification step, or a suffix array; keep the word index for ordinary queries.

## Lab

- Index "To be or not to be", "To do is to be", "Let it be" and "Not today" with the template. Expected: `index["be"]` is {0: [1, 5], 1: [4], 2: [2]}, `search_all("be not")` is [0], `search_phrase("to be")` is [0, 1], `search_phrase("be or not")` is [0], and `doc_len` is [6, 5, 3, 2].
- Add `search_any(query)` (OR) as a sorted union of the lists. Expected on the same four documents: `search_any("let today")` is [2, 3]. Then add NOT: `search_all("be")` minus the docs of "not" should give [1, 2].

> [!know]
> You now know how to build a positional inverted index and answer AND, OR, NOT and phrase queries by combining sorted posting lists instead of scanning text.

=== primer | How do you intersect a short posting list with a huge one without reading all of it? | 15 min
goal: Intersect sorted posting lists by merging or by galloping (exponential) search, predict from the two lengths which wins, and explain skip pointers
tag: search-intersect | Galloping intersection
link: CPython listsort.txt: Galloping | https://github.com/python/cpython/blob/main/Objects/listsort.txt | 10 min. Search the page for the 'Galloping' heading and read it with 'Galloping with a Broken Leg': the same probe pattern inside Python's sort, why it can lose on random data, and the set-intersection paper it came from

> [!key]
> Merging two sorted lists costs O(m + n), which is wasteful when one list has 50 entries and the other a million. **Galloping** takes each id x of the short list and searches forward in the long list from where the last search stopped: jump 1, 2, 4, 8, ... positions further each time until you overshoot x, then binary-search that last gap. A jump of distance d costs O(log d), so the whole intersection costs **O(m log(n / m))**. Engines also store **skip pointers** (or per-block last ids) so they can jump over compressed blocks without decoding them.

## Intuition

You are looking for 7, 40 and 41 in a 14-entry sorted list. A merge walks the long list one entry at a time and compares at every step. Galloping behaves like someone looking for a page in a book: flip ahead a little, then further and further until you pass the page, then narrow down. If the next wanted id is just ahead, you find it in two probes; if it is far ahead, the doubling covers the distance in a logarithmic number of jumps. Either way you never look at most of the long list.

## How it works

### Merge (the baseline)

Two cursors i and j. If `a[i] == b[j]`, output it and advance both; otherwise advance the cursor on the smaller value. Every step discards one element, so it takes at most m + n steps. This is exactly right when the lists are of similar length.

### Galloping (exponential search)

Keep a cursor j into the long list b. For the next id x of the short list a:

1. If `b[j] >= x`, the answer position is j.
2. Otherwise probe `b[j+1]`, `b[j+3]`, `b[j+7]`, `b[j+15]`, ... (each jump twice as long as the last) until a probe is `>= x` or you run off the end. The invariant is that the last probe that was `< x` sits at `prev`.
3. The first entry `>= x` lies in the gap after `prev`; binary-search just that gap (`bisect_left` with `lo` and `hi`).
4. If it equals x, output x. Either way, the next search starts from here: later ids of a are larger, so nothing before this point can match.

### Many terms

For q terms, sort the lists by length and intersect from the shortest up: the running result can only shrink, and every later step is "short against long", which is galloping's best case. Lucene does the same: its conjunction iterator sorts the sub-iterators by cost so that "the sparser iterator" leads, then calls `advance(target)` on the others, which means "move to the first document id `>= target`". That one method is the galloping primitive.

### Skip pointers and blocks

On disk, posting lists are compressed in blocks (next-but-one card), so you cannot binary-search raw integers. Instead the index stores, for each block, the last document id in it (a **skip pointer**). To advance to a target, read skip entries until one reaches the target, then decode only that block. Lucene's postings format keeps two levels of skip data for this, recording per block "by how much the doc ID should be incremented in case the block gets skipped". A classic rule of thumb is about sqrt(n) evenly spaced skips for a list of length n: more skips mean shorter jumps but more skip entries to read and store.

```text
blocks of 4:   [ 3  9 14 20 ] [ 27 31 40 52 ] [ 55 61 70 88 ] [ 91 95 97 99 ]
skip entries:        20              52              88              99
advance(60): 20 < 60, 52 < 60, 88 >= 60  ->  decode only block 3, find 61
```

## Cost

**Merge:** each comparison advances at least one cursor, so at most m + n comparisons: O(m + n).

**Galloping:** suppose the i-th search jumps a distance d_i in b. Doubling reaches past d_i after about log2(d_i) probes, and the binary search over a gap smaller than d_i takes about log2(d_i) more, so the i-th search costs O(1 + log d_i). The jumps never go backwards, so d_1 + d_2 + ... + d_m <= n. The sum of log d_i under that constraint is largest when all jumps are equal (log is concave), at d_i = n / m. Total: **O(m log(n / m + 1))**. For m = n this is O(n), the same order as a merge but with a bigger constant; for m = 10 and n = 10^6 it is about 10 x 2 x 17 = 340 comparisons instead of a million.

Measured with the template (comparisons, random ids below 10^6):

| short x long | common | merge comparisons | galloping comparisons |
|---|---|---|---|
| 1,000 x 1,000 | 1 | 1,998 | 3,606 |
| 1,000 x 10,000 | 8 | 10,989 | 7,924 |
| 1,000 x 100,000 | 83 | 100,889 | 13,807 |
| 100 x 100,000 | 13 | 99,888 | 2,046 |
| 10 x 100,000 | 0 | 95,712 | 270 |

Averaged over five random runs with 1,000 short ids, galloping overtakes the merge between a length ratio of 4 (4,990 against 5,887 comparisons) and 6 (6,985 against 6,716). The template switches at 8 to stay on the safe side, because the merge's inner loop is simpler.

## When to use it

- **Similar lengths** (within a factor of about 8): merge. It is simple, branch-friendly and touches each element once.
- **Very different lengths** (a rare term AND a common one): gallop, or advance through skip pointers. This is the normal case in search, since term frequencies follow Zipf's law.
- **Many short lists against one huge list:** consider a bitmap for the huge list (one bit per document), making each membership test O(1). Lucene's conjunction code has a special path for bit-set iterators for exactly this case.
- **Unsorted data, in memory, small:** Python's `set(a) & set(b)` is fine, but building the sets costs O(m + n) each time and loses the order. Posting lists are already sorted, so exploit that.

| Method | Cost | Needs |
|---|---|---|
| Merge | O(m + n) | two sorted lists |
| Galloping | O(m log(n / m)) | random access into the long list |
| Skip pointers | O(sqrt(n) + m sqrt(n)) worst case with sqrt(n) skips; better with two levels | per-block last ids |
| Hash set or bitmap | O(m) probes | a prebuilt set or bitmap |

## Worked trace

Short list [7, 40, 41] against the long list below (indices on top).

```steps
x = 7, start at j = 0: b[0] = 1 < 7, so gallop: probe b[1] = 3 (< 7), then b[3] = 7 (>= 7, stop)
    i      0  1  2  3  4  5  6  7  8  9 10 11 12 13
    b      1 {{3}} 5 {{7}} 9 12 15 20 26 33 40 48 52 60
---
Binary-search the gap (indices 2 to 3) for the first value >= 7: index 3 holds 7, a match; next search starts at j = 4
    i      0  1  2  3  4  5  6  7  8  9 10 11 12 13
    b      1  3  5 {{7}} 9 12 15 20 26 33 40 48 52 60      out [7]
---
x = 40 from j = 4: b[4] = 9 < 40; probe b[5] = 12, b[7] = 20 (both < 40), then b[11] = 48 (>= 40, stop)
    i      0  1  2  3  4  5  6  7  8  9 10 11 12 13
    b      1  3  5  7  9 {{12}} 15 {{20}} 26 33 40 {{48}} 52 60
---
Binary-search the gap 8 to 11: index 10 holds 40, a match; next search starts at j = 11
    i      0  1  2  3  4  5  6  7  8  9 10 11 12 13
    b      1  3  5  7  9 12 15 20 26 33 {{40}} 48 52 60     out [7, 40]
---
x = 41 from j = 11: b[11] = 48 >= 41 at once, and 48 != 41, so no match. The short list is done
    i      0  1  2  3  4  5  6  7  8  9 10 11 12 13
    b      1  3  5  7  9 12 15 20 26 33 40 {{48}} 52 60     out [7, 40]
```

On a list this short galloping saves little: it read 10 of the 14 entries. The payoff grows with the length ratio, as the table in Cost shows.

## Template

```python
from bisect import bisect_left


def intersect_merge(a, b):
    """Linear merge of two ascending lists: O(m + n)."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out


def gallop(b, x, lo):
    """First index i >= lo with b[i] >= x (len(b) if none): probe lo+1, lo+3, lo+7, ..., then binary search."""
    n = len(b)
    if lo >= n or b[lo] >= x:
        return lo
    prev, step = lo, 1                   # invariant: b[prev] < x
    while prev + step < n and b[prev + step] < x:
        prev += step
        step *= 2
    return bisect_left(b, x, prev + 1, min(prev + step + 1, n))


def intersect_gallop(small, large):
    """For each id of the short list, gallop forward in the long one: O(m log(n/m))."""
    out, j = [], 0
    for x in small:
        j = gallop(large, x, j)
        if j == len(large):
            break
        if large[j] == x:
            out.append(x)
            j += 1
    return out


def intersect_all(lists):
    """AND of many posting lists: shortest first, so the candidate set only shrinks."""
    lists = sorted(lists, key=len)
    if not lists:
        return []
    result = lists[0]
    for other in lists[1:]:
        if not result:
            break
        if len(other) > 8 * len(result):
            result = intersect_gallop(result, other)
        else:
            result = intersect_merge(result, other)
    return result
```

## Pitfalls

- **Restarting each search from 0.** Galloping from the start of b for every x turns O(m log(n/m)) into O(m log n) at best and loses the "never go backwards" argument; always resume from the last position.
- **Off-by-one in the final binary search.** The answer lies strictly after `prev` and at most at `prev + step`; the `hi` bound is `min(prev + step + 1, n)`. Test with x smaller than everything, larger than everything and equal to the last element.
- **Galloping the wrong way round.** Iterate over the short list and search in the long one. Swapping them gives O(n log(m / n)) probes that are never shorter than a merge.
- **Duplicates.** Posting lists never repeat a document id; if you reuse this code for general multisets, decide whether 2 copies AND 3 copies should give 2.
- **Measuring Python time naively.** The merge loop runs in the interpreter while `bisect_left` runs in C, so wall-clock times exaggerate galloping's advantage. Count comparisons to compare algorithms, time them to choose an implementation.

## Check yourself

Q: Starting from j = 0, which entries of b = [1, 3, 5, 7, 9, 12, 15, 20, 26, 33, 40, 48, 52, 60] does `gallop(b, 26, 0)` probe in the doubling phase, and what does it return?
A: b[0] = 1 < 26, then it probes b[1] = 3, b[3] = 7 and b[7] = 20, all smaller. The next probe would be index 15, past the end, so it binary-searches indices 8 to 13 (reading b[11], b[9], b[8]) and returns 8, where 26 is.

Q: Why is galloping O(m log(n / m)) and not O(m log n)?
A: Each search starts where the previous one stopped, so the jump distances d_i add up to at most n. A search over distance d costs O(log d), and the sum of log d_i with the d_i summing to n is maximised when all are n / m (concavity of log), giving m log(n / m).

Q: A query ANDs "the" (19,000,000 documents), "error" (2,000,000) and "E1234" (40). In which order do you intersect, and with which method at each step?
A: Start from "E1234" (40 ids). Gallop those 40 into the "error" list (ratio 50,000 to 1), giving at most 40 survivors, then gallop the survivors into "the". Each step costs a few hundred comparisons at most; a merge would read millions of entries.

## Lab

- Run `intersect_gallop([7, 40, 41], [1, 3, 5, 7, 9, 12, 15, 20, 26, 33, 40, 48, 52, 60])` and `intersect_all([list(range(0, 100, 2)), list(range(0, 100, 3)), list(range(0, 100, 5))])`. Expected: [7, 40] and [0, 30, 60, 90].
- Count reads of the long list: wrap it in `class Counting(list)` whose `__getitem__` increments a counter (`bisect_left` calls it too). With `a = list(range(0, 1_000_000, 1000))` and `b = Counting(range(0, 1_000_000, 7))`, both methods return 143 common ids; expected about 287,001 reads of b for the merge and 16,985 for galloping.

> [!know]
> You now know how to intersect posting lists with a merge or with galloping search, why galloping costs O(m log(n/m)), and how skip pointers let an engine jump over compressed blocks.

=== primer | How does a search engine turn posting lists into a BM25 ranking? | 15 min
goal: Compute BM25 scores from the statistics an index already stores, and evaluate them term at a time or document at a time knowing what each costs
tag: search-bm25 | BM25 from postings
link: AI guide: Keyword search and BM25 | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-keyword-search-and-bm25 | 12 min. The formula one idea at a time with a support-ticket example, and where BM25 beats vector search; this card is about how an engine computes it
link: Lucene BM25Similarity | https://lucene.apache.org/core/10_5_0/core/org/apache/lucene/search/similarities/BM25Similarity.html | 5 min. The defaults k1 = 1.2 and b = 0.75, the idf formula, and avgFieldLength computed as sumTotalTermFreq / docCount from index statistics

> [!key]
> **BM25** scores a document by summing, over the query terms it contains, idf(t) x tf (k1 + 1) / (tf + K(d)), where K(d) grows with the document's length. Everything it needs is already in the index: df is the length of the posting list, tf sits in the posting, document lengths sit in a per-document array. Engines evaluate it **term at a time** (one list after another, adding into per-document accumulators) or **document at a time** (walk all lists together by doc id and finish each document before the next), and the second is what makes top-k skipping possible.

## Intuition

A good answer to "cheap paris flights" contains the query's words, and the rare ones count for more: "paris" narrows things down far more than "cheap". Saying "cheap" three times should help a little, not three times as much. And a short listing that mentions all three words is a better bet than a 5,000-word travel guide that happens to mention them once each. BM25 is those three judgements turned into one formula: **rarity (idf), saturating repetition (k1) and length normalisation (b)**.

## How it works

### The formula

```text
score(d, q) = sum over terms t of q that occur in d:   idf(t) * tf * (k1 + 1) / (tf + K(d))

idf(t) = ln(1 + (N - df + 0.5) / (df + 0.5))        K(d) = k1 * (1 - b + b * |d| / avgdl)
defaults (Lucene, Elasticsearch): k1 = 1.2, b = 0.75
```

The tf part, tf (k1 + 1) / (tf + K), rises with tf but levels off at k1 + 1 = 2.2. For a document of average length (K = k1 = 1.2) it is 1.00 at tf = 1, 1.38 at tf = 2, 1.57 at tf = 3, 1.77 at tf = 5, 1.96 at tf = 10 and 2.17 at tf = 100. For a document twice the average length, K = 1.2 x (0.25 + 1.5) = 2.1, and the same counts give 0.71, 1.07, 1.29, 1.55, 1.82 and 2.15: long documents need more occurrences for the same credit. The AI guide's BM25 lesson walks through the intuition with a support-ticket example; here the question is where each number comes from.

### Where each number lives

| Quantity | Meaning | Where the engine gets it |
|---|---|---|
| N | documents in the index | a counter per field (Lucene: docCount) |
| df(t) | documents containing t | the length of t's posting list, stored in the term dictionary |
| tf(t, d) | occurrences of t in d | inside the posting, next to the doc id |
| \|d\| | length of d in tokens | a per-document array (Lucene's norms files) |
| avgdl | average length | total tokens / N (Lucene: sumTotalTermFreq / docCount) |

So two things are precomputed: **idf per query term** (q logarithms per query) and **K(d) per document** (one array for the whole index, recomputed only when avgdl drifts). After that, each posting costs one multiply-add and one division.

### Term at a time (TAAT)

Take the query terms one by one. For each posting (d, tf) of term t, add idf(t) x tf (k1 + 1) / (tf + K(d)) into `acc[d]`. When all lists are done, the accumulators hold the full scores; take the best k. Each list is read once, sequentially, which suits disks, but the accumulator table can grow to the number of matching documents, and no score is final until the last list is read.

### Document at a time (DAAT)

Open a cursor on every query term's list and keep the cursors in a min-heap keyed by their current doc id. The smallest doc id at the top is the next document to score: pop every cursor sitting on it, add their contributions, advance them and push them back. When no cursor is left on that id, the document's score is **final**, so it can go straight into a size-k heap of results. Memory is O(q) cursors plus O(k) results, whatever the number of matches, and because scores are final one document at a time, the engine can decide to **skip** documents that cannot reach the top k (next card). Lucene's query evaluation is built on document-at-a-time iterators (`DocIdSetIterator`) for this reason.

## Cost

Let F = f(t1) + ... + f(tq) be the total length of the query terms' posting lists and M the number of distinct matching documents (M <= F).

- **Precompute:** q logarithms per query; K(d) once per index, O(N).
- **TAAT:** one constant-time update per posting, so O(F) time; the accumulator dictionary holds M entries, O(M) memory. Picking the top k from it costs O(M log k) with a size-k heap.
- **DAAT:** every posting is pushed and popped once in a heap of q cursors, so O(F log q) time and O(q + k) memory. The log q factor is small (queries have a handful of terms) and buys final scores in doc order.
- **A common word dominates F.** "the" in 19 million of 20 million documents makes F about 19 million for any query containing it, though it barely changes the ranking (idf near 0). That waste is what WAND removes.

## When to use it

BM25 is the default lexical ranking in Lucene, Elasticsearch and OpenSearch, and SQLite FTS5 has a `bm25()` function. Use it as the first-stage ranker for keyword queries and as the keyword half of hybrid search. Tune k1 (saturation) and b (length normalisation) on labelled queries rather than by taste: b near 0 suits fields whose length carries no meaning (titles, tags), b near 1 suits long free text.

| Choice | Prefer it when | Cost |
|---|---|---|
| TAAT | lists on disk read sequentially, short queries, you need all scores (e.g. for facets) | O(F) time, O(M) memory |
| DAAT | you only show the top k, you want early termination | O(F log q) time, O(q + k) memory |
| BM25 vs plain TF-IDF | almost always BM25: saturation and length normalisation fix TF-IDF's main failures | the same postings |
| BM25 vs embeddings | identifiers, names, codes, jargon: BM25; paraphrase and meaning: vectors; usually both, fused | see the AI guide |

## Worked trace

Four documents: d0 "cheap flights to paris" (4 tokens), d1 "paris hotels and cheap paris flights" (6), d2 "cheap cheap cheap deals" (4), d3 "flights from london" (3). So N = 4 and avgdl = 4.25, giving K = [1.147, 1.571, 1.147, 0.935]. Query: cheap paris flights. Term at a time:

```steps
Precompute idf: cheap is in 3 docs, so idf = ln(1 + 1.5 / 3.5) = 0.357; paris (2 docs) 0.693; flights (3 docs) 0.357
    cheap    df 3  idf 0.357   postings d0:1  d1:1  d2:3
    paris    df 2  idf 0.693   postings d0:1  d1:2
    flights  df 3  idf 0.357   postings d0:1  d1:1  d3:1
---
List "cheap": d0 adds 0.357 x 2.2 / (1 + 1.147) = 0.365; d1 adds 0.305 (longer doc); d2 has tf 3 and adds 0.568
    acc  d0 {{0.365}}   d1 {{0.305}}   d2 {{0.568}}
---
List "paris": d0 adds 0.710; d1 has tf 2 and adds 0.854
    acc  d0 {{1.076}}   d1 {{1.159}}   d2 0.568
---
List "flights": d0 adds 0.365, d1 adds 0.305, d3 (new accumulator) adds 0.405
    acc  d0 {{1.441}}   d1 {{1.465}}   d2 0.568   d3 {{0.405}}
---
All lists read, so the scores are final: d1 narrowly beats d0 thanks to its second "paris"
    rank  d1 1.465   d0 1.441   d2 0.568   d3 0.405
```

Document at a time gives the same numbers in a different order of work: it finishes d0 (1.441) first, then d1, d2 and d3.

## Template

```python
import heapq
import math
from collections import Counter, defaultdict


def build(docs):
    """postings: term -> {doc_id: tf}; doc_len: tokens per doc. docs are lists of tokens."""
    postings = defaultdict(dict)
    for doc_id, tokens in enumerate(docs):
        for term, tf in Counter(tokens).items():
            postings[term][doc_id] = tf
    return postings, [len(t) for t in docs]


def bm25_weights(postings, doc_len, k1=1.2, b=0.75):
    """Per-term idf and per-document length factor K(d), computed once per index."""
    n = len(doc_len)
    avgdl = sum(doc_len) / n
    idf = {t: math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in postings.items()}
    norm = [k1 * (1 - b + b * dl / avgdl) for dl in doc_len]
    return idf, norm


def score_taat(query, postings, idf, norm, k1=1.2):
    """Term at a time: walk each query term's list, adding into per-document accumulators."""
    acc = defaultdict(float)
    for term in query:
        for doc, tf in postings.get(term, {}).items():
            acc[doc] += idf[term] * tf * (k1 + 1) / (tf + norm[doc])
    return acc


def score_daat(query, postings, idf, norm, k1=1.2):
    """Document at a time: merge the lists by doc id and finish each document before the next."""
    lists = [(t, iter(sorted(postings[t].items()))) for t in query if t in postings]
    heap = []
    for i, (term, it) in enumerate(lists):
        first = next(it, None)
        if first:
            heap.append((first[0], i, first[1]))
    heapq.heapify(heap)
    out = {}
    while heap:
        doc = heap[0][0]
        total = 0.0
        while heap and heap[0][0] == doc:          # every list positioned on this doc
            _, i, tf = heapq.heappop(heap)
            term, it = lists[i]
            total += idf[term] * tf * (k1 + 1) / (tf + norm[doc])
            nxt = next(it, None)
            if nxt:
                heapq.heappush(heap, (nxt[0], i, nxt[1]))
        out[doc] = total                            # doc is final: could go straight into a top-k heap
    return out
```

To rank, feed the scores into a size-k heap: `heapq.nlargest(10, scores.items(), key=lambda kv: kv[1])`.

## Pitfalls

- **Comparing raw scores across engines or indexes.** Scores depend on N, df and avgdl, and libraries differ in idf variants and constant factors. Compare rankings, not numbers.
- **Statistics are local.** Each Lucene segment or Elasticsearch shard computes df and avgdl from its own documents. Elasticsearch's default `query_then_fetch` scores "using local term and document frequencies for the shard"; `dfs_query_then_fetch` first gathers global ones, slower but more accurate. Small or skewed shards rank the same document differently.
- **Deleted documents still count.** Lucene's term statistics do not take deleted documents into account, so df and avgdl include dead documents until their segment merges.
- **Classic idf can go negative.** The original Robertson-Sparck Jones form ln((N - df + 0.5) / (df + 0.5)) is negative for terms in more than half the documents, so containing a common word lowers the score. The "1 +" inside Lucene's logarithm keeps idf positive.
- **Repeated query terms.** The template adds a term's contribution once per occurrence in the query. Decide whether "paris paris" should count twice, and deduplicate if not.
- **TAAT memory blow-up.** A query with a very common term creates an accumulator for nearly every document. Use DAAT or prune accumulators for large indexes.

## Check yourself

Q: In the trace, d2 ("cheap cheap cheap deals") contains "cheap" three times, yet scores only 0.568 while d0 scores 1.441. Why?
A: d2 matches only one query term, and BM25 sums per-term contributions. Repetition saturates: tf = 3 gives 0.357 x 2.2 x 3 / (3 + 1.147), about 0.57, far less than three times the tf = 1 value. d0 matches all three terms, including the rarer "paris" with idf 0.693.

Q: Why does document-at-a-time evaluation make top-k pruning possible, while term-at-a-time does not?
A: In DAAT a document's score is final as soon as the cursors move past it, so the engine always knows the current k-th best score and can compare a document's best possible score against it before doing the work. In TAAT no score is final until every list has been read, so nothing can be ruled out early.

Q: An Elasticsearch index has 20 shards and a rare product code appears 30 times, all on one shard. Users report that the code's documents rank inconsistently between similar queries. What is going on and what are the fixes?
A: With the default query_then_fetch, each shard scores with its local df and avgdl. On the shard holding all 30 documents the code looks common (lower idf) while elsewhere it is absent, so idf, and the ranking across shards, is skewed. Fixes: use dfs_query_then_fetch to gather global statistics, use fewer shards for a small index, or route documents so that shards are statistically similar.

## Lab

- Score "cheap paris flights" on the four documents of the trace with `score_taat` and with `score_daat`. Expected from both: d1 1.465, d0 1.441, d2 0.568, d3 0.405 (rounded).
- Rebuild the weights with `b=1.0` and then `b=0.0`. Expected: with b = 1, the shorter d0 overtakes d1 (1.453 against 1.408); with b = 0, d1 wins by more (1.666 against 1.406), because length no longer counts against it.
- Reproduce the AI guide's worked example (N = 1,000, avgdl = 100): one function `term(N, df, tf, dl, avgdl)` and two sums. Expected: chunk X scores 7.495 and chunk Y 5.755.

> [!know]
> You now know how to compute BM25 from the statistics an index already holds, and when to evaluate it term at a time or document at a time.

=== primer | How does a search engine return the top 10 without scoring every match? | 16 min
goal: Keep the best k results in a size-k min-heap, use WAND's per-term upper bounds to skip documents that cannot enter it, and explain what block-max WAND changed in Lucene and Elasticsearch
tag: search-wand | Top-k with WAND
link: Elastic: Faster retrieval of top hits with block-max WAND | https://www.elastic.co/blog/faster-retrieval-of-top-hits-in-elasticsearch-with-block-max-wand | 15 min. Read 'The end of the tunnel', 'Further improvements' and 'Practical implications': how Lucene 8 adopted WAND, then block-max WAND, and why total hit counts became a lower bound
link: Lucene WANDScorer source | https://github.com/apache/lucene/blob/main/lucene/core/src/java/org/apache/lucene/search/WANDScorer.java | 10 min. Read only the class comment: the two papers it implements and the three structures (tail heap, lead list, head heap) that hold the cursors

> [!key]
> Keep the best k scores in a **size-k min-heap**; its smallest entry θ is the bar every new document must beat. **WAND** gives each query term an upper bound UB(t) on the score it can add. Sort the cursors by their current doc id and add up their bounds in that order: the first cursor where the sum exceeds θ is the **pivot**. Any document before the pivot's doc can only contain terms whose bounds sum to at most θ, so it cannot get in, and all cursors jump straight to the pivot doc. The result is exactly the exhaustive top k, after scoring a fraction of the matches.

## Intuition

You are shortlisting 10 candidates and the weakest on your list scored 61. A new applicant who could score at most 55 even with full marks on every remaining test is not worth interviewing. You do not need their actual score, only a cheap upper bound. In search, most matches for "the fjord boat" contain only "the", whose contribution is tiny; once the shortlist is full of documents mentioning "fjord", a document that only has "the" cannot possibly beat it, so the engine stops looking at those documents.

## How it works

### The size-k heap

Walk the matches (document at a time, so each score is final when computed). While the heap has fewer than k entries, push. After that, compare with the root `heap[0]`, the k-th best so far: if the new score is larger, `heapreplace` evicts the root; otherwise drop the document. This is O(log k) per match instead of sorting all M matches, and θ = `heap[0][0]` only ever rises.

### Upper bounds

For each term, UB(t) is the largest contribution any of its postings makes: the best combination of high tf and short document. It is computed once at index time and stored with the term. Common words have tiny bounds (low idf); rare words have large ones.

### One WAND step

1. Sort the live cursors by current doc id.
2. Add their bounds in that order; the **pivot** is the first cursor at which the running sum exceeds θ. If there is none, no remaining document can enter the heap: stop.
3. Let p be the pivot's doc. If the first cursor is already on p, then every cursor up to the pivot is on p (they are sorted): compute p's full score and offer it to the heap.
4. Otherwise advance a cursor that is before p straight to the first doc `>= p` (galloping or skip pointers), and repeat.

Why is skipping safe? A document x < p can only appear in lists whose cursors sit before the pivot (the others are already past x), and those bounds sum to at most θ. So x's true score is at most θ and it could never displace the k-th best.

### Block-max WAND

A single bound per term is loose: one outlier posting with a huge tf sets UB(t) for the whole list. **Block-max** indexes store the maximum contribution of each block of postings (the same blocks that skip pointers jump over), so the bound used for a candidate is the block's maximum, which is usually much smaller. Lucene's `WANDScorer` comment says it implements Broder et al.'s WAND "enhanced with techniques described in" Ding and Suel's block-max paper, and the Lucene 10.4 postings format stores per-block "impacts" (frequency and length pairs) in its skip data so the bounds are available without decoding the block.

Elastic's write-up of the change (Lucene 8.0, Elasticsearch 7.0) records two consequences. Scores may no longer be negative, because the bound argument assumes that matching more terms never lowers a score. And the total hit count became a lower bound: `hits.total` now carries a `relation` of `gte` unless you ask for exact counting with `track_total_hits`, because the engine no longer visits every match.

## Cost

Let M be the number of matching documents and F the total posting-list length.

- **Exhaustive DAAT plus heap:** O(F log q) to merge the cursors, plus O(M log k) heap work.
- **WAND, worst case:** the same. If every document scores about the same, θ never separates them and nothing is skipped; each step also costs O(q log q) to reorder cursors (real implementations keep them in heaps, as Lucene's tail and head heaps do).
- **WAND, typical case:** once θ exceeds the bounds of the common terms, only documents containing a high-bound term are scored, and the cursors on common terms jump in O(log gap) each.

Measured with the template on a synthetic corpus of 20,000 Zipf-distributed documents, real BM25 contributions and k = 10 (wN is the N-th most frequent word):

| Query | List lengths | Docs scored, exhaustive | Docs scored, WAND |
|---|---|---|---|
| w0 w1500 | 19,898 and 180 | 19,898 | 1,651 |
| w3 w40 w2000 | 17,695, 4,900 and 120 | 18,021 | 629 |
| w10 w400 | 12,447 and 603 | 12,634 | 719 |
| w1 w2 w3 | 19,379, 18,607 and 17,695 | 19,924 | 16,447 |

The last row is the worst case in practice: three common words with similar small bounds, so θ rarely rules a document out.

## When to use it

Use WAND (or the engine's built-in version) whenever users see the top k of many matches: web and site search, log search sorted by relevance, the first stage of retrieval for a RAG system. It needs scores that are **sums of non-negative per-term contributions** with precomputed bounds, which BM25 provides.

Do not expect help, or switch it off, when:

- you need the **exact total** number of matches or facet counts over all of them (every match must be visited anyway);
- k is a large fraction of the matches (θ stays low);
- scores can be negative or are not decomposable per term (a learned reranker): run WAND for the first stage, then rerank its top few hundred.

| Method | Docs fully scored | Exact top k? | Exact hit count? |
|---|---|---|---|
| Score all, sort | M | yes | yes |
| Score all, size-k heap | M | yes | yes |
| WAND | often far fewer than M | yes | no (lower bound) |
| Block-max WAND | fewer still | yes | no (lower bound) |
| Stop after the first N matches | N | no | no |

## Worked trace

Three terms, k = 2. "the" is in 8 documents with bound 0.6, "fjord" in 2 with bound 2.0, "boat" in 2 with bound 1.1. The postings are (doc: contribution): the 1:0.3 2:0.5 3:0.4 4:0.6 5:0.2 6:0.5 7:0.4 9:0.3; fjord 4:2.0 9:1.8; boat 2:1.1 9:1.0.

```steps
Heap empty, so theta = -inf and the first cursor is the pivot: score doc 1 (only "the")
    cursors  the@1 (ub 0.6)   boat@2 (ub 1.1)   fjord@4 (ub 2.0)
    heap     {{(0.3, d1)}}
---
Still fewer than k = 2 results: score doc 2 (the + boat = 1.6)
    cursors  the@2   boat@2   fjord@4
    heap     {{(1.6, d2)}}  (0.3, d1)
---
theta = 0.3; the alone (0.6) beats it, so pivot is doc 3: score 0.4, which evicts d1
    cursors  the@3   fjord@4   boat@9
    heap     (1.6, d2)  {{(0.4, d3)}}
---
theta = 0.4; the (0.6) still exceeds it, pivot doc 4: the + fjord = 2.6 evicts d3
    cursors  the@4   fjord@4   boat@9
    heap     {{(2.6, d4)}}  (1.6, d2)
---
theta = 1.6; the alone is 0.6 (not enough), the + fjord = 2.6 is: pivot is fjord at doc 9, so "the" jumps from 5 to 9
    cursors  {{the@5 -> the@9}}   fjord@9   boat@9
    skipped  docs 5, 6 and 7 are never scored
---
All three cursors are on doc 9: score 0.3 + 1.8 + 1.0 = 3.1, which evicts d2; then every list is exhausted
    heap     {{(3.1, d9)}}  (2.6, d4)
    scored   5 documents (1, 2, 3, 4, 9) instead of 8
```

## Template

```python
import heapq
from bisect import bisect_left


def topk_exhaustive(lists, k):
    """Score every matching doc, keep the best k in a size-k min-heap. lists: [(doc, score)] per term."""
    acc = {}
    for plist in lists:
        for doc, s in plist:
            acc[doc] = acc.get(doc, 0.0) + s
    heap = []
    for doc, s in acc.items():
        if len(heap) < k:
            heapq.heappush(heap, (s, doc))
        elif s > heap[0][0]:
            heapq.heapreplace(heap, (s, doc))   # evict the current k-th best
    return sorted(heap, reverse=True), len(acc)


def topk_wand(lists, k):
    """WAND: skip documents whose best possible score cannot beat the current k-th best (k >= 1)."""
    cur = []                                    # per term: [docs, scores, position, upper bound]
    for plist in lists:
        if plist:
            docs, scores = zip(*plist)
            cur.append([docs, scores, 0, max(scores)])
    heap, scored = [], 0
    while True:
        cur = [c for c in cur if c[2] < len(c[0])]
        if not cur:
            break
        cur.sort(key=lambda c: c[0][c[2]])      # by current doc id
        theta = heap[0][0] if len(heap) == k else float("-inf")
        bound, pivot = 0.0, None
        for i, c in enumerate(cur):
            bound += c[3]
            if bound > theta:
                pivot = i
                break
        if pivot is None:                       # even all terms together cannot beat theta
            break
        pdoc = cur[pivot][0][cur[pivot][2]]
        if cur[0][0][cur[0][2]] == pdoc:        # all cursors up to the pivot sit on pdoc: score it
            s = 0.0
            for c in cur:
                if c[0][c[2]] == pdoc:
                    s += c[1][c[2]]
                    c[2] += 1
            scored += 1
            if len(heap) < k:
                heapq.heappush(heap, (s, pdoc))
            elif s > heap[0][0]:
                heapq.heapreplace(heap, (s, pdoc))
        else:                                   # docs before pdoc cannot qualify: jump a cursor
            c = cur[0]
            c[2] = bisect_left(c[0], pdoc, c[2])
    return sorted(heap, reverse=True), scored
```

Each list holds (doc, contribution) pairs sorted by doc, as the BM25 card would produce them; the bound is the list's maximum. The tests compare the returned scores with `topk_exhaustive` on thousands of random inputs.

## Pitfalls

- **Bounds that are not bounds.** If UB(t) was computed with an old avgdl, a different k1, or before a boost was applied, a document can score above its "upper bound" and be skipped wrongly. Results then silently differ from exhaustive search. Recompute bounds whenever the scoring inputs change, or pad them.
- **Negative contributions.** The safety argument assumes extra terms never lower a score. That is why, from Elasticsearch 7, scores may no longer be negative.
- **Promising exact hit counts.** With WAND the engine no longer visits all matches. Show "1,000+ results" or request exact counts explicitly (and pay for them).
- **Ties at θ.** The template only admits a document whose score is strictly greater than θ, so among equal scores the earliest found wins. Exhaustive search with the same rule gives the same scores but may keep different documents; compare score lists in tests, not document ids.
- **Forgetting cursors beyond the pivot.** When scoring the pivot doc, also add any cursor after the pivot that happens to sit on the same doc; the template loops over all cursors for this reason.

## Check yourself

Q: In the trace, suppose "boat" also contained doc 7 with contribution 0.9. At the step where θ = 1.6 and the cursors are the@5, boat@7, fjord@9, what does WAND do next?
A: Sorted by doc: the@5 (bound 0.6), boat@7 (1.1), fjord@9 (2.0). The running sum is 0.6, then 1.7 > 1.6, so the pivot is boat at doc 7. "the" is before it, so it jumps from 5 to 7; then both sit on doc 7 and it is scored: 0.4 + 0.9 = 1.3, which does not beat 1.6. Docs 5 and 6 are still skipped.

Q: Why can WAND skip document 5 in the trace without ever computing its score?
A: Doc 5 is before the pivot doc 9, so only cursors before the pivot (here just "the") can contain it; the others are already past it. Its score is therefore at most UB(the) = 0.6, which does not exceed θ = 1.6, so it could never enter the top 2.

Q: A team needs both the top 20 results and the exact number of matching documents for a "1,234 results" banner. What changes with WAND, and what would you suggest?
A: Exact counting forces a visit to every match, which removes most of WAND's savings. Options: show a lower bound ("1,000+ results", as Elasticsearch does by default), count exactly only up to a threshold (`track_total_hits` set to a number), or compute an approximate count separately (for example from document frequencies).

## Lab

- Run both functions on the trace's lists with k = 2. Expected: both return [(3.1, 9), (2.6, 4)] (scores rounded); exhaustive scores 8 documents, WAND 5.
- Build `A = [(d, 0.1) for d in range(10_000)]` and `B = [(d, 2.0) for d in range(0, 10_000, 250)]` and ask for k = 10. Expected: both return ten documents scoring 2.1 (docs 0, 250, ..., 2250); exhaustive scores 10,000 documents, WAND only 19 (the first 10, then the next 9 documents of B, after which nothing can beat θ = 2.1).

> [!know]
> You now know how to return the top k with a size-k heap and how WAND's upper bounds skip documents that cannot make the cut, and why that turns hit counts into lower bounds.

=== primer | How do search engines shrink posting lists to about a byte per document? | 14 min
goal: Compress ascending doc ids with gaps plus varints or bit-packed blocks, decode them, and estimate the bytes per posting from how common a term is
tag: search-varint | Gap and varint compression
link: Lucene 10.4 postings format | https://lucene.apache.org/core/10_5_0/core/org/apache/lucene/codecs/lucene104/Lucene104PostingsFormat.html | 10 min. Read 'Basic idea' (packed blocks of 256 and VInt blocks), then under the .doc file the notes on PackedDocDeltaBlock (d-gaps) and skip data: the production version of this card

> [!key]
> Posting lists are ascending, so store the **gaps** between consecutive doc ids instead of the ids. Gaps are small for common terms and small numbers need few bits. Write each gap as a **varint** (7 data bits per byte, the top bit says "more bytes follow") or **bit-pack** a block of gaps using the width of the largest one. Either way a typical posting costs one or two bytes instead of four or eight, and decoding is a running sum.

## Intuition

House numbers on a long street: instead of "1043, 1047, 1052, 1060" you can write "1043, +4, +5, +8". The first number is big, the rest are tiny, and tiny numbers are cheap to write down. A word that appears in 10% of documents has an average gap of 10, which fits in 4 bits; there is no reason to spend 32.

## How it works

### Gaps (delta encoding)

Keep the first id as it is, then each later entry as the difference from the previous one: [3, 7, 21, 150, 300, 1000] becomes [3, 4, 14, 129, 150, 700]. Decoding is a running sum. This only works because lists are sorted; an unsorted list would produce negative gaps.

### Varints

Split a number into 7-bit groups, lowest group first. Every byte carries one group in its low 7 bits; the top bit is 1 if another byte follows and 0 on the last byte. Numbers below 128 take one byte, below 16,384 two bytes, and so on. This is the format of Lucene's VInt and of Protocol Buffers' "base 128 varints" (where 150 is the two bytes `96 01`, exactly as below).

### Bit-packed blocks

Varints decode one byte at a time with a branch per byte. Faster decoders work on fixed-size blocks: find the bit width of the largest gap in the block, write the width once, then every gap in exactly that many bits (often called frame of reference). Decoding a block is a fixed pattern of shifts and masks with no branches, which compilers turn into SIMD code. Lucene 10.4 does this: its postings format encodes "most integer data as a packed block" of 256 integers with one bit width, encodes blocks whose values are all equal specially, and writes the leftover tail of a list (fewer than 256 entries) as VInts. Frequencies use "patching": a few outliers are stored separately so they do not widen the whole block.

### Compression and skipping work together

You cannot binary-search a varint stream, because entry i does not start at a known byte. So engines compress in blocks and keep, per block, its last doc id and its byte offset (the skip data from the intersection card). Advancing to a target reads skip entries, jumps to one block and decodes only that block.

## Cost

Let a term appear in a fraction p of N documents. Its list has pN entries and the average gap is about 1/p.

- **Bits needed:** a gap of g needs about log2(g) + 1 bits, so a posting costs about log2(1/p) + 1 bits at best. A term in 1% of documents needs about 8 bits; one in 0.1% about 11.
- **Varint:** rounds each gap up to a multiple of 7 data bits, never less than 1 byte. So common terms (gaps below 128) cost exactly 1 byte per posting, and rare ones 2 or 3.
- **Bit-packed blocks:** every gap in a block pays the width of the block's largest gap, plus a byte per block. For dense lists this goes below 1 byte per posting.
- **Time:** encoding and decoding are O(n) for n postings, with small constants; packed blocks decode faster than varints.

Measured with the template (random lists in a collection of N = 1,000,000 documents, blocks of 256):

| Documents with the term | Average gap | int32 bytes | varint bytes | per doc | packed bytes | per doc | Python list of ints |
|---|---|---|---|---|---|---|---|
| 1,000 | 1,000 | 4,000 | 1,893 | 1.89 | 1,658 | 1.66 | 36,056 |
| 10,000 | 100 | 40,000 | 12,811 | 1.28 | 12,218 | 1.22 | 360,056 |
| 100,000 | 10 | 400,000 | 100,000 | 1.00 | 79,155 | 0.79 | 3,600,056 |
| 500,000 | 2 | 2,000,000 | 500,000 | 1.00 | 244,014 | 0.49 | 18,000,056 |

The last column is what `sys.getsizeof` reports for a Python list plus its int objects: about 36 bytes per posting, up to 70 times the compressed size. That is why real engines are written over byte arrays, not object lists.

## When to use it

Compress whenever posting lists live on disk or must fit in memory, which is always in production. The choice is about decode speed against size:

| Encoding | Bytes per posting | Decode speed | Notes |
|---|---|---|---|
| Raw int32 array | 4 | fastest, random access | fine for small in-memory indexes |
| Gaps + varint | 1 to 3 | good, sequential | simple; one branch per byte |
| Gaps + packed blocks (FOR) | often below 1 for common terms | very fast, SIMD friendly | Lucene's choice, with a varint tail |
| Bit-level codes (Elias gamma, Golomb) | smallest | slow | rarely worth it today |
| Bitmap | N / 8 per list, whatever its length | fastest AND / OR | wins for very dense lists |

For sets that are dense in some ranges and sparse in others, **Roaring bitmaps** pick a container per chunk of 65,536 ids (an array, a bitmap or runs). The Roaring project lists Apache Lucene, Elasticsearch, Druid, Spark, ClickHouse and Redis among its users.

## Worked trace

Encoding the ids [3, 7, 21, 150, 300, 1000] with gaps and varints.

```steps
Turn ids into gaps: the first stays as it is, the rest are differences
    ids    3   7  21  150  300  1000
    gaps  {{3   4  14  129  150   700}}
---
Gaps 3, 4 and 14 are below 128: one byte each, top bit 0
    3   -> {{0}}0000011
    4   -> {{0}}0000100
    14  -> {{0}}0001110
---
Gap 129 = 1 0000001 in binary: emit the low 7 bits with the top bit set, then the remaining 1
    129 -> {{1}}0000001  {{0}}0000001        (hex 81 01)
---
Gap 150 = 1 0010110: low 7 bits 0010110 with the top bit set, then 1
    150 -> {{1}}0010110  {{0}}0000001        (hex 96 01)
---
Gap 700 = 101 0111100: low 7 bits 0111100, then the remaining 101 (= 5)
    700 -> {{1}}0111100  {{0}}0000101        (hex bc 05)
---
Total 9 bytes against 24 as int32. Decoding: read until a byte with top bit 0, add the value to a running sum
    bytes   03 04 0e 81 01 96 01 bc 05
    decode  3, 3+4 = 7, 7+14 = 21, 21+129 = 150, 300, {{1000}}
---
Bit-packing the same six gaps: the largest, 700, needs 10 bits, so 6 x 10 = 60 bits = 8 bytes, plus 1 width byte
    width 10   payload 8 bytes   total {{9}} bytes (a block of 256 amortises the width byte)
```

## Template

```python
def encode_varint_gaps(doc_ids):
    """Delta-encode ascending doc ids, then write each gap as a varint (7 bits per byte)."""
    out = bytearray()
    prev = 0
    for doc in doc_ids:
        gap = doc - prev
        prev = doc
        while gap >= 0x80:                   # more than 7 bits left: emit low 7, set the continue bit
            out.append((gap & 0x7F) | 0x80)
            gap >>= 7
        out.append(gap)                      # last byte: high bit clear
    return bytes(out)


def decode_varint_gaps(data):
    docs, value, shift, prev = [], 0, 0, 0
    for byte in data:
        value |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
        else:
            prev += value                    # undo the delta
            docs.append(prev)
            value = shift = 0
    return docs


def pack_block(gaps):
    """Frame-of-reference bit packing: one width byte, then every gap in exactly `width` bits."""
    width = max(1, max(gaps).bit_length())
    bits = 0
    for i, g in enumerate(gaps):
        bits |= g << (i * width)
    return bytes([width]) + bits.to_bytes((len(gaps) * width + 7) // 8, "little")


def unpack_block(data, count):
    width = data[0]
    bits = int.from_bytes(data[1:], "little")
    mask = (1 << width) - 1
    return [(bits >> (i * width)) & mask for i in range(count)]
```

`pack_block` uses one Python integer as a bit buffer, which is clear but slow; a production codec packs into machine words. The block's length is stored elsewhere (here passed as `count`), as Lucene does with its fixed block size.

## Pitfalls

- **Unsorted input.** A negative gap makes `out.append` raise `ValueError` here; in C it becomes a huge unsigned number and a corrupt list. Sort and deduplicate before encoding.
- **The first gap.** It is the absolute first id (the gap from 0). Forgetting it shifts every decoded id.
- **One outlier widens a block.** A single gap of 100,000 in a block of small gaps forces 17 bits on all 256 entries. Patching (storing exceptions separately) or smaller blocks fix it.
- **No random access.** Entry i of a varint stream is not at a known offset. If you need to skip, keep per-block skip data; if you need constant-time access, keep fixed-width arrays.
- **Format versioning.** Encoded bytes outlive code. Lucene's file formats start with a codec header that records the format version; do the same in anything you persist.

## Check yourself

Q: What bytes does the template produce for the single id 300, and for the list [300, 301]?
A: 300 is 10 0101100 in binary: the low 7 bits 0101100 with the top bit set give 0xAC, then 300 >> 7 = 2 gives 0x02, so `ac 02`. For [300, 301] the second gap is 1, so `ac 02 01`: three bytes in total.

Q: Why do gaps make common terms cheaper per posting than rare terms, the opposite of raw ids?
A: Raw ids cost the same for every term (about log2 N bits each). Gaps average N / df, so the more documents contain a term, the smaller its gaps and the fewer bits each needs: a term in half the documents has gaps around 2 (1 to 2 bits), a term in 0.1% has gaps around 1,000 (10 bits).

Q: A filter "in stock" matches 60% of 50 million products. Would you store it as a compressed posting list or as a bitmap?
A: A bitmap: 50,000,000 bits is about 6.25 MB, with O(1) membership tests and word-at-a-time AND with other filters. The list would hold 30 million entries at roughly 1 byte each with varints (about 30 MB), or about 0.4 bytes each packed, and AND would need decoding. Dense sets favour bitmaps; Roaring picks per chunk automatically.

## Lab

- Encode [3, 7, 21, 150, 300, 1000] and print `encode_varint_gaps(ids).hex(" ")`. Expected: `03 04 0e 81 01 96 01 bc 05` (9 bytes), and decoding gives the ids back. `len(pack_block([3, 4, 14, 129, 150, 700]))` is also 9.
- With `rng = random.Random(55)`, draw `sorted(rng.sample(range(1_000_000), df))` for df = 1,000, 10,000, 100,000 and 500,000 in that order, and compute bytes per posting for varints and for packed blocks of 256 gaps. Expected: varint 1.89, 1.28, 1.00, 1.00; packed 1.66, 1.22, 0.79, 0.49.

> [!know]
> You now know how to compress posting lists with gaps, varints and bit-packed blocks, decode them, and predict the bytes per posting from how common a term is.

=== primer | How does a search box suggest the best completions after two keystrokes? | 15 min
goal: Return the top k weighted completions of a prefix with a trie that stores subtree maxima and a best-first heap, and explain where Lucene uses FSTs and tries over its term dictionary
tag: search-typeahead | Top-k prefix completion
link: Andrew Gallant: Index 1,600,000,000 keys with automata and Rust | https://burntsushi.net/transducers/#finite-state-machines-as-data-structures | 25 min. Read 'Ordered sets', 'Ordered maps' and 'Construction': how a trie becomes a minimal automaton by sharing suffixes as well as prefixes, and how a transducer attaches values to keys
link: Redis: Autocomplete with Redis | https://redis.io/docs/latest/develop/ai/search-and-query/advanced-concepts/autocomplete/ | 5 min. FT.SUGADD and FT.SUGGET over a trie of weighted suggestions, including the FUZZY option for one typo

> [!key]
> Type-ahead is two problems: find the strings that start with the prefix, and return only the best k of them by weight (popularity, recency). A trie answers the first in O(length of the prefix). Store at every node the **largest weight in its subtree** and the second becomes a **best-first search**: a heap always expands the most promising subtree, so the work depends on k and the word length, not on how many thousands of strings match. Real engines share prefixes the same way in their term dictionaries: Lucene 9 kept a per-field FST over term prefixes, Lucene 10.3 replaced it with a trie, and Lucene's suggesters use weighted FSTs.

## Intuition

The prefix "s" matches about 8,000 English words, and you want the 10 that users pick most. Reading all 8,000 and sorting them is wasteful when the answer is decided by a handful. Picture a filing cabinet where every drawer label also says "most popular item in here: 412". You open the drawer with the biggest label first, and inside it the sub-drawer with the biggest label, and you never open a drawer whose label is smaller than the 10 items you already hold.

## How it works

### Finding the prefix

Walk the trie one character at a time from the root; if a character is missing, there are no completions. With a sorted array of strings instead, `bisect_left(keys, prefix)` finds the first string with that prefix and the matches are the contiguous run after it. Both cost O(|p|) or O(|p| log n) to locate the range; the difference is what happens next.

### Subtree maxima

When inserting (phrase, weight), update `best = max(best, weight)` on every node along the path, root included. Now each node knows the largest weight anywhere below it, which is an **upper bound** for every completion in that subtree.

### Best-first search

Push the prefix node with priority `best`. Repeatedly pop the highest-priority entry:

- if it is a **finished word**, output it (it beats everything still in the heap);
- if it is a **subtree**, push its own word (if a phrase ends there) with its exact weight, and each child with the child's `best`.

Stop after k words. Priorities never increase along a path (a child's best is at most its parent's), so when a word reaches the top of the heap, nothing unseen can beat it. Ties are broken alphabetically by putting the text second in the heap tuple.

### Term dictionaries: the same idea, compressed

A search engine must also find terms by prefix, for prefix queries (`comp*`), fuzzy queries and simply to locate a term's postings. Lucene's block-tree terms dictionary keeps terms on disk in blocks of 25 to 48 entries that share a prefix. In Lucene 9, the per-field index (the .tip file) was an **FST** mapping a term prefix "to the on-disk block that holds all terms starting with that prefix"; in Lucene 10.3's format the .tip file holds "a separate trie for each field" with the same job. An FST (finite state transducer) is a minimal automaton: it shares suffixes as well as prefixes, and it attaches an output (such as a block address or a weight) to each key. Lucene's `util.fst` package builds the minimal FST from sorted input and offers "N-shortest-paths search by weight", which is exactly top-k completion; its `AnalyzingSuggester` stores suggestions "to a weighted FST".

## Cost

Let p be the prefix, L the longest completion, σ the alphabet size and m the number of strings with the prefix.

- **Collect and sort:** O(|p|) to reach the node, then O(m) to visit every completion and O(m log k) for a size-k heap. For a one-letter prefix, m is a sizeable share of the dictionary.
- **Best-first:** the nodes popped all have `best` at least the k-th answer's weight, and they lie on the paths to at most k winners (plus ties), so about k x L pops, each pushing at most σ children. That is O(k L σ log(k L σ)), independent of m.
- **Memory:** a trie of Python objects is heavy. Measured: 73,445 dictionary words (0.6 MB of text) became 170,375 nodes and about 35 MB. Production systems use compact arrays, radix trees (one node per branching point), or FSTs.

Measured with the template on that word list, random Pareto weights and k = 10:

| Prefix | Matches | Heap pops, best-first | Trie best-first | Sorted array + scan |
|---|---|---|---|---|
| s | 8,436 | 90 | 0.30 ms | 5.7 ms |
| co | 2,680 | 85 | 0.22 ms | 1.7 ms |
| comp | 236 | 66 | 0.17 ms | 0.19 ms |
| compute | 10 | 28 | 0.03 ms | 0.02 ms |

Short prefixes are where best-first wins, and they are exactly the first keystrokes users type.

## When to use it

| Approach | Query cost | Update cost | Memory | Use when |
|---|---|---|---|---|
| Sorted array, bisect, then `nlargest` | O(log n + m log k) | rebuild | smallest | small sets or long prefixes |
| Trie with subtree maxima (this card) | about O(k L log) | O(L) to raise a weight | large in Python | live weights, short prefixes |
| Top-k list cached at every node | O(\|p\|) | expensive: update every ancestor's list | k entries per node | read-heavy, rarely updated |
| FST (Lucene suggesters) | O(\|p\|) plus N-shortest paths | rebuild from sorted input | smallest of all | large static dictionaries |

Redis Search keeps suggestions in a trie (`FT.SUGADD`, `FT.SUGGET`) and its FUZZY option also accepts prefixes within one edit, which needs the typo-tolerance techniques of the next card.

## Worked trace

Items: car 50, card 20, care 90, cart 40, cat 70, dog 60. Query: prefix "ca", k = 3. Heap entries are (priority, text, kind); a subtree's priority is its best weight.

```steps
Walk c, a from the root; the "ca" node's best is 90 (from "care"). Push it
    heap  {{(90, ca, subtree)}}
---
Pop "ca": no word ends here; push its children with their bests: "car" subtree (90) and "cat" subtree (70)
    heap  {{(90, car, subtree)}}  {{(70, cat, subtree)}}
---
Pop "car" subtree: push its own word (50) and children card (20), care (90), cart (40)
    heap  {{(90, care, subtree)}}  (70, cat, subtree)  {{(50, car, word)}}  {{(40, cart, subtree)}}  {{(20, card, subtree)}}
---
Pop "care" subtree: it is a leaf, so push the word care with its exact weight 90
    heap  {{(90, care, word)}}  (70, cat, subtree)  (50, car, word)  (40, cart, subtree)  (20, card, subtree)
---
Pop the word care: output it. Nothing left in the heap can beat 90
    out   {{care 90}}
---
Pop "cat" subtree, push the word cat (70); pop it and output it
    out   care 90, {{cat 70}}
---
Pop the word car (50): output it. k = 3, stop; card and cart were never expanded
    out   care 90, cat 70, {{car 50}}
```

## Template

```python
import heapq
from bisect import bisect_left


class Node:
    __slots__ = ("kids", "weight", "best")

    def __init__(self):
        self.kids = {}
        self.weight = None                   # set if a suggestion ends here
        self.best = float("-inf")            # the highest weight anywhere below this node


class Completer:
    """Trie whose nodes remember the best weight in their subtree, for best-first top-k completion."""

    def __init__(self, items=()):
        self.root = Node()
        for phrase, weight in items:
            self.add(phrase, weight)

    def add(self, phrase, weight):
        node = self.root
        node.best = max(node.best, weight)
        for ch in phrase:
            node = node.kids.setdefault(ch, Node())
            node.best = max(node.best, weight)
        node.weight = weight

    def top(self, prefix, k):
        """The k heaviest suggestions starting with prefix, heaviest first (ties: alphabetical)."""
        node = self.root
        for ch in prefix:
            node = node.kids.get(ch)
            if node is None:
                return []
        heap = [(-node.best, prefix, 1, node)]   # (priority, text, 0 = finished word / 1 = subtree, node)
        out = []
        while heap and len(out) < k:
            neg, text, kind, nd = heapq.heappop(heap)
            if kind == 0:
                out.append((text, -neg))
                continue
            if nd.weight is not None:
                heapq.heappush(heap, (-nd.weight, text, 0, nd))
            for ch, kid in nd.kids.items():
                heapq.heappush(heap, (-kid.best, text + ch, 1, kid))
        return out


def top_sorted(keys, weights, prefix, k):
    """Baseline: binary-search the block of keys with this prefix, then pick the k heaviest."""
    lo = bisect_left(keys, prefix)
    hi = lo
    while hi < len(keys) and keys[hi].startswith(prefix):
        hi += 1
    best = heapq.nsmallest(k, ((-weights[i], keys[i]) for i in range(lo, hi)))
    return [(text, -neg) for neg, text in best]
```

The heap tuple never compares two `Node` objects: (text, kind) is unique per entry, because a node's subtree entry and its word entry share the text but differ in kind.

## Pitfalls

- **Lowering a weight.** `add` only raises `best` on the path. If a phrase's weight drops (or the phrase is deleted), ancestors keep a stale maximum: results stay correct (the bound is still an upper bound) but the search slows down. Recompute `best` bottom-up along the path from the children, or rebuild periodically.
- **Normalisation.** Lowercase and strip accents consistently for the lookup key, but return the original display text ("New York", not "new york"); Lucene's analysing suggester keeps the two forms apart for this reason.
- **Python memory.** About 200 bytes per node even with `__slots__`. Past a few hundred thousand phrases, switch to arrays, a radix tree, or a library FST.
- **Only prefixes.** "york" will not suggest "New York". Index each word start of a phrase (infix suggestions) or use an n-gram index.
- **Ties and determinism.** Without a tie-breaker in the heap tuple, equal weights compare the next field; here that is the text, which also makes results stable across runs.

## Check yourself

Q: With the trace's six items, what do `top("car", 2)` and `top("", 2)` return?
A: `top("car", 2)` gives [("care", 90), ("car", 50)]: the "car" subtree holds car 50, card 20, care 90 and cart 40. `top("", 2)` gives [("care", 90), ("cat", 70)]; dog (60) comes third.

Q: Why can best-first output a word as soon as it reaches the top of the heap, even though many subtrees are unexplored?
A: Every unexplored completion lies under some subtree entry in the heap, and that entry's priority (the subtree's best) is at least the completion's weight. The popped word's weight is at least every priority in the heap, so no unexplored completion can exceed it.

Q: Your product has 50 million query strings with weights recomputed nightly, and a 20 ms budget per keystroke. Trie of objects, sorted arrays, or an FST?
A: An FST (or a compact array-based trie) built offline each night from the sorted strings: weights change only in batch, so a static, minimal, memory-mapped structure is ideal, and top-k by weight is a built-in operation. A Python object trie would need tens of gigabytes; sorted arrays fit but scanning the millions of matches for a one-letter prefix blows the budget.

## Lab

- With the six items, expected: `top("ca", 3)` is [("care", 90), ("cat", 70), ("car", 50)], `top("d", 5)` is [("dog", 60)] and `top("x", 3)` is [].
- Build every string of length 1 to 6 over "abcd" in the order `["".join(p) for n in range(1, 7) for p in itertools.product("abcd", repeat=n)]` (5,460 strings) with weight `(i * 7919) % 10007` for the i-th string. Count heap pops by wrapping `heapq.heappop`. Expected for k = 5: prefix "" returns ccdda (10006) first after 32 pops instead of visiting all 5,460 strings; prefix "abc" returns abcbb (9843), abcacd (9784), abccad (9707), abcdcd (9630), abccc (9410) after 18 pops out of 85 matches.

> [!know]
> You now know how to return the top k completions of a prefix with subtree maxima and a best-first heap, and how engines compress the same prefix sharing into tries and FSTs.

=== primer | How does search still find "receive" when you type "recieve"? | 16 min
goal: Find dictionary words within edit distance k of a query with a trie walk that carries a DP row, a BK-tree or symmetric deletes, and explain how Lucene's Levenshtein automata do the same over the term dictionary
tag: search-fuzzy | Typo-tolerant lookup
link: Andrew Gallant: Levenshtein automata | https://burntsushi.net/transducers/#levenshtein-automata | 15 min. Why intersecting a Levenshtein automaton with a sorted key set rules out whole regions of the dictionary without visiting them, with a worked example
link: Lucene FuzzyQuery | https://lucene.apache.org/core/10_5_0/core/org/apache/lucene/search/FuzzyQuery.html | 5 min. The class description: Damerau-Levenshtein (optimal string alignment) by default, at most 2 edits, and why larger distances are rarely useful

> [!key]
> Comparing a misspelt query with every dictionary word costs a full edit-distance computation per word. Three structures avoid most of that work. A **trie walk** carries one DP row per node and abandons a branch as soon as every entry of the row exceeds k; that row is the state of a **Levenshtein automaton**, which Lucene compiles into a DFA and intersects with its term dictionary. A **BK-tree** prunes with the triangle inequality. **Symmetric deletes** (SymSpell) precompute every word's deletions so a lookup is a handful of hash probes, paid for in memory.

## Intuition

A misspelt word is "close" to the right one: a few insertions, deletions or substitutions apart. Checking all 73,000 words of a dictionary one by one takes seconds in Python. But closeness has structure. If "do" is already 2 edits from every prefix of "cat", then "dog", "dot" and "door" cannot be within 1 edit of "cat": you can rule out a whole branch of the trie from its first two letters. That single observation is what Levenshtein automata, and Lucene's fuzzy queries, are built on.

## How it works

### Edit distance, one row at a time

The Levenshtein distance between a and b fills a DP table where cell (i, j) is the distance between the first i characters of a and the first j of b; each cell is the minimum of a deletion, an insertion and a substitution (free when the characters match). Row i depends only on row i - 1, so two rows suffice. Lucene's FuzzyQuery uses Damerau-Levenshtein (optimal string alignment) by default, which also counts swapping two adjacent letters as one edit: "recieve" is 1 edit from "receive" there but 2 in plain Levenshtein.

### Walking a trie with rows (the automaton view)

Make the dictionary a trie and the query q fixed. The row for a trie node with prefix P holds the distances between P and every prefix of q. A child's row is computed from its parent's row in O(|q|), so words sharing a prefix share that work. Two rules:

- at a node where a word ends, the last entry of the row is that word's distance to q;
- if **every** entry of a row exceeds k, prune the subtree: any longer word's alignment passes through this row, and distances never shrink along it.

The row is all you need to know about the prefix read so far, so it is a state, and the walk is an automaton over the dictionary. Schulz and Mihov showed how to precompute these states into a deterministic automaton for a given q and k; Lucene's `LevenshteinAutomata` class constructs such "DFAs that match a word within some edit distance", and FuzzyQuery runs it against the term dictionary, which is a sorted set of terms with a prefix index.

### BK-trees

Edit distance is a metric, so it obeys the triangle inequality. Build a tree where each child edge is labelled with the child's distance from its parent. To search for q within k: compute d = dist(q, node); any word x in the child subtree on edge e satisfies |d - e| <= dist(q, x), so only edges with d - k <= e <= d + k can contain matches. This works for any metric, but at k = 2 on short words the band covers most edges.

### Symmetric deletes (SymSpell)

If dist(q, w) <= k, there is a string you can reach from both q and w with at most k deletions each: delete the substituted characters from both, the extra characters from whichever has them. So precompute, for every dictionary word, all strings obtained by deleting up to k characters, in a hash map from deletion to words. A lookup generates the query's own deletions (a few dozen), probes the map and verifies each candidate with the real distance. The SymSpell README puts it as "an average 5 letter word has about 3 million possible spelling errors within a maximum edit distance of 3, but SymSpell needs to generate only 25 deletes to cover them all".

## Cost

Let N be the dictionary size, L the word length and k the distance.

- **Brute force:** N edit distances at O(L^2) each. Measured: 3.9 s per query over 73,445 words in pure Python.
- **Trie walk:** O(visited nodes x |q|). Pruning keeps the visited set near the query's neighbourhood, but it grows quickly with k.
- **BK-tree:** O(distance computations x L^2); the pruning is good at k = 1 and weak at k = 2.
- **SymSpell:** a word of length L has about C(L, k) deletions at distance k, so the index holds about N x L^k / k! keys; a lookup generates that many deletions of q and probes each in O(1).

Measured with the template on 73,445 dictionary words:

| Query | k | Matches | Trie walk | BK-tree (share of words compared) | SymSpell lookup |
|---|---|---|---|---|---|
| recieve | 1 | relieve | 12 ms | 203 ms (4%) | |
| recieve | 2 | 14, incl. receive | 95 ms | 1,107 ms (31%) | 3.1 ms |
| algoritm | 2 | algorithm, algorithms | 124 ms | 1,238 ms (28%) | 0.4 ms |
| teh | 2 | 290 | 32 ms | 671 ms (38%) | 7.0 ms |

SymSpell's speed costs memory: its k = 2 index held 2,215,387 distinct deletion keys for those 73,445 words and took 13 s to build.

## When to use it

| Method | Query cost | Memory | Updates | Use when |
|---|---|---|---|---|
| Brute force | N distances | none | free | a few thousand words, offline jobs |
| Trie or FST + automaton | the dictionary's neighbourhood of q | the dictionary itself | as easy as the trie | search engines (Lucene FuzzyQuery), k <= 2 |
| BK-tree | many distances at k >= 2 | one node per word | insert only | arbitrary metrics, k = 1 |
| Symmetric deletes | a few dozen hash probes | many times the dictionary | re-derive deletions | spell checkers, very low latency, small k |

Keep k small. Lucene's FuzzyQuery stops at 2 edits and its documentation warns that larger distances "will match a significant amount of the term dictionary". Do not fuzz identifiers, error codes or product numbers: "E1243" is not a typo of "E1234". Rank candidates by distance first and popularity second (Peter Norvig's spelling corrector does the latter with word frequencies).

## Worked trace

Dictionary cart, cast, cat, cut, dog as a trie; query "cat", k = 1. Each row lists the distance from the node's prefix to "", "c", "ca", "cat".

```steps
Root (empty prefix): its distances to the query prefixes are just their lengths
    (root)  row [0, 1, 2, 3]
---
Child "d": d versus "", "c", "ca", "cat" gives [1, 1, 2, 3]. The minimum is 1 <= k, so keep going
    d       row [1, {{1}}, 2, 3]
---
Child "do": [2, 2, 2, 3]. Every entry exceeds k = 1, so prune: "dog" (and any do... word) is never visited
    do      row {{[2, 2, 2, 3]}}   pruned
---
Child "c": [1, 0, 1, 2]; then "cu": [2, 1, 1, 2]; then "cut" ends a word with last entry 1: a match
    cut     row [3, 2, 2, {{1}}]   match, distance 1
---
"ca": [2, 1, 0, 1]; "cat" ends a word with last entry 0: an exact match
    cat     row [3, 2, 1, {{0}}]   match, distance 0
---
"cas" [3, 2, 1, 1], then "cast" ends a word with last entry 1
    cast    row [4, 3, 2, {{1}}]   match, distance 1
---
"car" [3, 2, 1, 1], then "cart" ends a word with last entry 1. Result: cat 0, cart 1, cast 1, cut 1
    cart    row [4, 3, 2, {{1}}]   match, distance 1
```

Every row cost one pass over the 3 characters of "cat", and the prefix rows ("c", "ca") were computed once for all the words below them.

## Template

```python
from collections import defaultdict


def levenshtein(a, b):
    """Edit distance (insert, delete, substitute) with two DP rows."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def trie_fuzzy(trie, query, k):
    """Walk a dict-of-dicts trie ('$' marks a word end) carrying one DP row per node; prune rows > k."""
    found = []
    stack = [(trie, "", list(range(len(query) + 1)))]
    while stack:
        node, prefix, row = stack.pop()
        if "$" in node and row[-1] <= k:
            found.append((row[-1], prefix))
        for ch, child in node.items():
            if ch == "$":
                continue
            nxt = [row[0] + 1]
            for j, qc in enumerate(query, 1):
                nxt.append(min(row[j] + 1, nxt[j - 1] + 1, row[j - 1] + (qc != ch)))
            if min(nxt) <= k:                      # some completion could still be within k
                stack.append((child, prefix + ch, nxt))
    return sorted(found)


class BKTree:
    """Each child edge is labelled with its distance to the parent; the triangle inequality prunes."""

    def __init__(self, words):
        words = iter(words)
        self.root = (next(words), {})
        for w in words:
            self.add(w)

    def add(self, word):
        node = self.root
        while True:
            d = levenshtein(word, node[0])
            if d == 0:
                return
            if d not in node[1]:
                node[1][d] = (word, {})
                return
            node = node[1][d]

    def search(self, query, k):
        found, stack, computed = [], [self.root], 0
        while stack:
            word, kids = stack.pop()
            d = levenshtein(query, word)
            computed += 1
            if d <= k:
                found.append((d, word))
            for edge, child in kids.items():
                if d - k <= edge <= d + k:          # any match below has distance in this band
                    stack.append(child)
        return sorted(found), computed


def deletes(word, k):
    """word plus every string made by deleting up to k characters."""
    out, frontier = {word}, {word}
    for _ in range(k):
        frontier = {w[:i] + w[i + 1:] for w in frontier for i in range(len(w))}
        out |= frontier
    return out


class SymSpell:
    """Symmetric delete: index the deletes of every word; look up the deletes of the query."""

    def __init__(self, words, k=2):
        self.k = k
        self.by_delete = defaultdict(set)
        for w in words:
            for d in deletes(w, k):
                self.by_delete[d].add(w)

    def search(self, query):
        candidates = set()
        for d in deletes(query, self.k):
            candidates |= self.by_delete.get(d, set())
        scored = ((levenshtein(query, w), w) for w in candidates)
        return sorted((d, w) for d, w in scored if d <= self.k)
```

Build the trie for `trie_fuzzy` with `node = node.setdefault(ch, {})` per character and `node["$"] = True` at the end of each word. All three searches return the same (distance, word) list; the tests check them against brute force on thousands of random dictionaries.

## Pitfalls

- **Transpositions.** Plain Levenshtein charges 2 for "teh" to "the" and "recieve" to "receive", so with k = 1 the template suggests "relieve" for "recieve". Use optimal string alignment (one extra case in the DP) for typing errors, as Lucene does by default.
- **Short words and k = 2.** Within 2 edits, "teh" matches 290 dictionary words. Scale k with length: Elasticsearch's default AUTO fuzziness allows 0 edits for terms of up to 2 characters, 1 edit for 3 to 5 and 2 beyond.
- **Fuzzy prefixes are a different problem.** For type-ahead, "recie" should match words starting with "recei". In the trie walk, once a node's last row entry (the distance from its prefix to the whole query) is within k, every word below that node is a fuzzy-prefix match.
- **SymSpell memory.** Deletions grow like L^k per word: millions of keys for a modest dictionary at k = 2. Cap the word length used for deletions (SymSpell has a prefix length option) or use k = 1.
- **BK-trees and duplicates.** The template ignores a word at distance 0 from an existing node; keep counts or payloads in the node if duplicates matter.

## Check yourself

Q: In the trace, what row does the trie walk compute for the prefix "cu", and why is "cu" kept although "u" is not in "cat"?
A: [2, 1, 1, 2]: "cu" is 2 from "", 1 from "c" (insert u), 1 from "ca" (substitute u for a) and 2 from "cat". Its minimum is 1 <= k, so a word below it, such as "cut", may still be within 1 edit, as it is.

Q: Why is it safe to prune a trie branch when every entry of its row exceeds k?
A: Every alignment of a longer word that starts with this prefix against the query passes through some cell of this row, and moving to later cells never lowers the cost (each step adds 0 or 1). So the final distance of every word below is at least the row's minimum, which is already above k.

Q: You need typo tolerance for a 30-million-term index that is updated continuously, with k up to 2. SymSpell, BK-tree, or an automaton over the term dictionary?
A: An automaton over the term dictionary, as Lucene does: it needs no extra index (the sorted terms and their prefix structure already exist), handles updates for free, and prunes by prefix. SymSpell would need hundreds of millions of deletion keys and rebuilding on updates; a BK-tree would compare a large share of the 30 million terms at k = 2.

## Lab

- Expected: `SymSpell(["receive", "recipe", "relieve", "deceive", "review"], 2).search("recieve")` returns [(1, "relieve"), (2, "receive"), (2, "recipe")], and `len(deletes("receive", 2))` is 28.
- Insert book, books, cake, boo, cape, cart, boon, cook (in that order) into a `BKTree`. Expected: `search("bork", 1)` returns ([(1, "book")], 5): five of the eight words were compared, because the "cake" subtree (edge 4, outside the band 0 to 2) was skipped.
- Add the transposition case to `levenshtein` (if `a[i-1] == b[j-2]` and `a[i-2] == b[j-1]`, also try the cell two rows and two columns back plus 1; you need three rows). Expected: "recieve" to "receive" and "teh" to "the" both become 1.

> [!know]
> You now know how to find words within k edits of a query by walking a trie with DP rows, pruning a BK-tree or probing symmetric deletes, and why Lucene intersects a Levenshtein automaton with its term dictionary.

=== lab | Race merge against galloping on a Zipf-shaped index | 45 min
goal: Build an inverted index over a 20,000-document corpus with realistic word frequencies and measure when galloping beats merging for posting-list intersection
link: Lucene ConjunctionDISI source | https://github.com/apache/lucene/blob/main/lucene/core/src/java/org/apache/lucene/search/ConjunctionDISI.java | 10 min, optional. Find the comment 'Sort the list first to allow the sparser iterator to lead the matching' and the doNext loop: Lucene's AND is the shortest-first, advance-to-target strategy you measure here

You will generate a corpus whose word frequencies follow Zipf's law (a few words everywhere, most words rare, as in real text), build an inverted index, and intersect pairs of posting lists with a merge and with galloping. You will count the work, time it, and see the crossover the intersection card predicted.

## Setup

- Python 3.10 or newer, standard library only. About 200 MB of RAM.
- Building the corpus takes about 10 seconds; every later step is instant.

## Steps

1. Save this as `postings_lab.py`. The corpus is seeded, so you get exactly the same documents as the expected results below.

```python
import random
import time
from bisect import bisect_left
from collections import defaultdict


def make_corpus(n_docs=20_000, vocab=5_000, seed=7):
    """Documents whose word frequencies follow Zipf's law, like real text."""
    rng = random.Random(seed)
    words = [f"w{i}" for i in range(vocab)]
    weights = [1 / (rank + 1) for rank in range(vocab)]
    return [rng.choices(words, weights, k=rng.randint(20, 200)) for _ in range(n_docs)]


def build_index(docs):
    index = defaultdict(list)
    for doc_id, tokens in enumerate(docs):
        for term in set(tokens):
            index[term].append(doc_id)      # doc ids arrive in order: lists are sorted
    return index


def merge(a, b):
    i = j = steps = 0
    out = []
    while i < len(a) and j < len(b):
        steps += 1
        if a[i] == b[j]:
            out.append(a[i]); i += 1; j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out, steps


def gallop_intersect(small, large):
    """For each id in the short list, gallop forward in the long list, then binary-search the last jump."""
    out, j, steps, n = [], 0, 0, len(large)
    for x in small:
        prev, step = j - 1, 1               # large[prev] < x is already known (-1: nothing yet)
        while prev + step < n and large[prev + step] < x:
            prev, step = prev + step, step * 2
            steps += 1
        lo, hi = prev + 1, min(prev + step + 1, n)
        steps += 1 + (hi - lo).bit_length()  # the probe that stopped us, plus the binary search
        j = bisect_left(large, x, lo, hi)
        if j == n:
            break
        if large[j] == x:
            out.append(x)
            j += 1
    return out, steps


def timed(fn, *args, repeat=20):
    best = float("inf")
    for _ in range(repeat):
        t = time.perf_counter()
        result = fn(*args)
        best = min(best, time.perf_counter() - t)
    return result, best * 1e6


if __name__ == "__main__":
    t0 = time.perf_counter()
    docs = make_corpus()
    index = build_index(docs)
    print(f"{len(docs):,} docs, {sum(map(len, docs)):,} tokens, {len(index):,} terms, "
          f"built in {time.perf_counter() - t0:.1f} s")
    for t in ["w0", "w9", "w99", "w999", "w4999"]:
        print(t, len(index[t]))
    pairs = [("w0", "w1"), ("w0", "w99"), ("w9", "w999"), ("w0", "w999"), ("w0", "w4999")]
    print(f"{'pair':<14}{'sizes':>16}{'common':>8}{'merge steps':>13}{'gallop steps':>14}"
          f"{'merge us':>10}{'gallop us':>11}{'set us':>8}")
    for a, b in pairs:
        A, B = index[a], index[b]
        small, large = (A, B) if len(A) <= len(B) else (B, A)
        (r1, s1), t1 = timed(merge, small, large)
        (r2, s2), t2 = timed(gallop_intersect, small, large)
        r3, t3 = timed(lambda x, y: sorted(set(x) & set(y)), small, large)
        assert r1 == r2 == r3
        print(f"{a + ' & ' + b:<14}{len(small):>7,} x {len(large):>6,}{len(r1):>8,}{s1:>13,}{s2:>14,}"
              f"{t1:>10,.0f}{t2:>11,.0f}{t3:>8,.0f}")
```

2. Before running it, write down a prediction for each pair: which method needs fewer steps, and roughly by how much? Use the cost formulas O(m + n) and O(m log(n / m)).
3. Run `python3 postings_lab.py` and compare with your predictions. The `assert` checks both methods against Python's set intersection.
4. Measure a three-term AND two ways: merge "w0" with "w9" and then with "w999" (largest first), against galloping "w999" into "w9" and the result into "w0" (smallest first). Add up the steps of each plan.
5. Optional: add skip pointers. Split the long list into blocks of 128 and keep each block's last id; to advance to x, scan the block maxima, then binary-search one block. Count steps the same way and compare with galloping on the "w0 & w999" pair.

## What you should see

The corpus line and list lengths should match exactly (they did on CPython 3.12):

```text
20,000 docs, 2,198,251 tokens, 5,000 terms, built in 8.9 s
w0 19898
w9 12966
w99 2215
w999 249
w4999 47
```

| Pair | Sizes | Common | Merge steps | Gallop steps | Merge time | Gallop time | Set time |
|---|---|---|---|---|---|---|---|
| w0 & w1 | 19,379 x 19,898 | 19,294 | 19,983 | 39,932 | 4,202 us | 11,626 us | 1,729 us |
| w0 & w99 | 2,215 x 19,898 | 2,212 | 19,896 | 14,279 | 5,017 us | 3,713 us | 1,512 us |
| w9 & w999 | 249 x 12,966 | 183 | 12,967 | 2,694 | 2,680 us | 489 us | 642 us |
| w0 & w999 | 249 x 19,898 | 248 | 19,806 | 2,970 | 5,305 us | 640 us | 1,145 us |
| w0 & w4999 | 47 x 19,898 | 46 | 19,883 | 805 | 5,387 us | 204 us | 1,472 us |

- **Step counts are exact**; times depend on your machine, but the ratios should look similar.
- With equal lengths (w0 & w1) the merge needs half the steps of galloping and runs about 3 times faster.
- From a length ratio of about 9 (w0 & w99) galloping wins on steps, and the gap widens with the ratio: 25 times fewer steps for w0 & w4999.
- The set intersection is fast because it runs in C, but it builds two hash sets per query (the timing includes that), it loses the order, and it cannot read compressed lists from disk. Engines gallop over sorted, compressed lists instead.
- Step 4: the largest-first merge plan takes 32,865 steps; the smallest-first galloping plan takes 5,012. Both return 183 documents. This is why engines sort the lists of an AND by length first.

> [!tip]
> If your gallop counts are far higher than in the table, check that each search starts from the previous position (`j`) rather than from 0, and that you gallop over the long list, not the short one.
