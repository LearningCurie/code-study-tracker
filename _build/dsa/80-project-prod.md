---
key: projectprod
name: Build an inverted search index
stage: prod
summary: Index a small document collection and evaluate conjunctive keyword queries.
why: Inverted postings turn a document scan into a comparison of candidate sets, a foundation of search systems.
outcomes:
- Build and intersect sorted postings lists.
- Compare index work with a full document scan.
cues:
- Many queries search the same collection.
- Terms occur in a minority of documents.
traps:
- Repeated occurrences create duplicate document IDs in a posting.
- Query and document tokenisation disagree.
---

=== build | Local document search | 6-8 h
goal: Build a deterministic inverted index for AND keyword search.
link: Lucene segments | https://lucene.apache.org/core/10_5_0/core/org/apache/lucene/codecs/lucene104/package-summary.html#Segments | See how production indexing groups index data.
link: Keyword search | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-keyword-search-and-bm25 | Contrast this exact Boolean index with ranked retrieval.

## The brief
Make a local searchable catalogue of short text documents. This is a toy in-memory index, not Lucene, a ranked search engine or a durable production service.

## Spec
Documents have unique nonnegative integer IDs and ASCII text. Tokenise both documents and queries into maximal runs of ASCII letters, lowercased. Index each term to sorted unique document IDs. An AND query returns IDs containing every distinct query term, sorted ascending; an empty tokenised query returns an empty list. Repeated query terms have no extra effect. Reject duplicate document IDs.

Intersect postings using two pointers, starting with the shortest posting; a missing term returns no results. Implement an independent oracle that tokenises and scans each document. State build cost in total characters plus postings sorting, query cost in postings visited, and memory in distinct term-document pairs; do not imply ranking or phrase matching.

## Milestones
1. **1-2 h:** Define tokenisation and implement the scanning oracle.
2. **1-2 h:** Build postings and implement shortest-first intersection.
3. **1-2 h:** Test duplicates, missing terms, empty queries and seeded corpora.
4. **1-2 h:** Benchmark query work and describe index construction and memory.

## Done when
- Documents `1: "Red red fox"`, `2: "red bird"`, `3: "BLUE fox"` return `[1]` for `red fox`, `[1, 2]` for `RED red`, and `[]` for punctuation-only input.
- Postings contain no duplicate IDs; unknown terms return no results; duplicate document IDs are rejected.
- At least 200 seeded corpora and queries match the scan oracle, including terms absent from the corpus.
- Benchmark 1,000, 10,000 and 50,000 documents with fixed-seed common and rare terms, 100 queries each. Check results, then report index build time, posting-pair count, median query time and postings compared versus documents scanned.
- Explain why common terms can still require long postings scans and why this design does not implement ranking, updates or durability.

## Stretch goals
- Add document replacement and deletion, maintaining unique postings.
- Persist a versioned snapshot and test loading a corrupt or unsupported format.

## Hints
- Read [Lucene's segment description](https://lucene.apache.org/core/10_5_0/core/org/apache/lucene/codecs/lucene104/package-summary.html#Segments) for context; keep the toy implementation deliberately smaller.
- [Keyword search and BM25](https://learningcurie.github.io/code-study-tracker/ai.html#l-c-keyword-search-and-bm25) shows what ranking would add beyond Boolean matching.
