---
key: tokens
name: Tokenisers: byte-pair encoding and friends
stage: aisys
summary: How tokenisers are built and run: what BPE learns, training it fast with a lazy heap and linked lists, encoding by merge rank, byte-level BPE with regex pre-tokenisation, and how WordPiece and Unigram differ.
why: Every prompt passes through a tokeniser before the model sees it, and the tokeniser's choices decide what the model can see at all: whether a leading space changes a word, how numbers are chopped, why an emoji arrives as fragments, why some strings make a model behave strangely. The AI guide's tokens lesson covers counting tokens and what they cost; this module builds the algorithms. They are a compact tour of core DSA: BPE is greedy compression, its naive training is quadratic and its fast version needs a priority queue with lazy deletion plus doubly linked lists; encoding is a small priority-queue simulation; WordPiece is greedy longest match; Unigram is dynamic programming (Viterbi). You will train a real BPE on a book and reproduce GPT-2's token ids exactly.
outcomes:
- Explain what BPE learns (an ordered list of merge rules) and train it by hand on a small word-frequency table
- Implement BPE training with pair counts, a lazily updated max-heap, a pair-to-positions index and doubly linked symbol lists, and show it matches the naive trainer
- Encode text by repeatedly merging the lowest-ranked pair, with a linear scan or a heap, and reproduce GPT-2's token ids
- Explain byte-level BPE, GPT-2's byte-to-character table and its regex pre-tokeniser, and predict where they split text
- Contrast WordPiece's greedy longest match and Unigram's Viterbi segmentation with BPE, and recognise tokeniser pitfalls from verified examples
cues:
- "Merge the most frequent adjacent pair, again and again": greedy merges driven by pair counts, and a heap once it must be fast
- Repeatedly taking a global maximum while many counts change a little: a heap with lazy invalidation instead of decrease-key
- Many local edits in a sequence that must keep track of neighbours: a doubly linked list over array positions
- "Most probable way to split a string into dictionary pieces": dynamic programming over prefixes (Viterbi)
- "Longest dictionary prefix first": greedy longest match, as in WordPiece
traps:
- Breaking ties between equally frequent pairs by dictionary order, so two implementations learn different vocabularies from the same data
- Merging overlapping occurrences ("a a a") wrongly, or forgetting to update the neighbouring pairs after a merge
- Assuming a word with and without a leading space is the same token
- Decoding and printing token by token, which splits multi-byte characters into replacement characters
- Reusing token counts or splits from one tokeniser for a model that uses another
systems:
- Hugging Face tokenizers' BPE trainer (tokenizers/src/models/bpe/trainer.rs in v0.23.3) keeps pair counts in a hash map, an index from each pair to the words that contain it, and an 8-ary max-heap of candidate merges refreshed lazily: a popped entry whose count is stale is pushed back with the current count, and ties go to the smaller pair
- Hugging Face tokenizers applies merges when encoding (word.rs, merge_all) with a min-heap of (rank, position) over symbols linked by prev and next indices, skipping heap entries that no longer match their position
- tiktoken (0.14.0) encodes pieces shorter than 100 bytes with a linear scan for the lowest-rank pair, with a source comment that this O(mn) scan beats a heap on short pieces because of cache locality, and uses a heap with invalidated entries for longer pieces
- GPT-2's encoder.py maps the 256 byte values to printable characters, splits text with a regex before BPE, merges the lowest-ranked bigram repeatedly and caches each chunk's result; its vocabulary has 50,257 entries: 256 bytes, 50,000 merges and one end-of-text token
- BERT's WordPiece tokeniser (google-research/bert tokenization.py) uses greedy longest-match-first with a ## continuation prefix and emits [UNK] for a whole word when any piece is missing or the word exceeds 200 characters; SentencePiece writes spaces as ▁ (U+2581) so that tokenisation is lossless, and supports both BPE and Unigram models
further:
- Paper · 20 min | Sennrich, Haddow and Birch 2016, Neural machine translation of rare words with subword units: read §3.2 and Algorithm 1 | https://arxiv.org/abs/1508.07909
- Paper · 30 min | Kudo 2018, Subword regularization: read §3.2 for the Unigram language model, its Viterbi segmentation and the EM-and-prune training loop | https://arxiv.org/abs/1804.10959
- Paper · 15 min | Kudo and Richardson 2018, SentencePiece: read §3.1 (lossless tokenisation with ▁) and §3.2 (O(N log N) BPE segmentation with a heap) | https://arxiv.org/abs/1808.06226
- Paper · 20 min | Land and Bartolo 2024, Fishing for Magikarp: read §1 and §2 on how under-trained 'glitch' tokens arise and how to detect them | https://arxiv.org/abs/2405.05417
---

=== primer | What does byte-pair encoding actually learn? | 16 min
goal: Train BPE by hand and in code on a small word-frequency table, and explain why what it learns is an ordered list of merge rules
tag: tokens-bpe | BPE merge rules
link: Sennrich, Haddow and Birch 2016 | https://arxiv.org/abs/1508.07909 | 10 min: §3.2 and Algorithm 1, the original subword BPE with its end-of-word symbol and a 20-line Python learner on the same toy dictionary as this card
link: AI guide: Tokens and tokenisation | https://learningcurie.github.io/code-study-tracker/ai.html#l-c-tokens-and-tokenisation | About 12 min: The user's side: counting tokens, and why code and other languages cost more

> [!key]
> BPE starts from single characters (or bytes), counts every adjacent pair of symbols weighted by how often each word occurs, merges the most frequent pair into one new symbol everywhere, records that **merge rule**, and repeats. What it learns is the **ordered list of merges**; the vocabulary is the base symbols plus one new symbol per merge. To tokenise a new word, split it into characters and replay the merges in the same order, so no word is ever unknown and frequent words end up as single tokens.

## Intuition

Taking notes in a fast lecture, you invent shorthand. First you abbreviate the letter pair you write most often, then pairs that include your abbreviation, and after a while whole common words have their own squiggle, while rare words are still spelt out from smaller squiggles. BPE does exactly this, greedily, with a frequency table. It began as a compression scheme that replaced the most frequent pair of bytes with an unused byte (Gage, 1994); Sennrich, Haddow and Birch (2016) applied it to words so that a translation model could handle rare and unseen words with a fixed vocabulary.

## How it works

### The input: words with counts

Split the text into words first (pre-tokenisation) and count them. Pairs never cross word boundaries, so training needs only the table of distinct words and their counts, not the text itself. Each word starts as a tuple of characters plus an end-of-word marker `</w>`, which keeps "est" at the end of "newest" apart from "est" inside "estimate". (GPT-2 instead attaches the space to the start of the next word; see the byte-level card.)

### The loop

1. Count every adjacent pair across all words, weighting each by its word's count.
2. Pick the most frequent pair (a, b). Break ties with a fixed rule: here, the smallest pair in sorted order.
3. Replace every occurrence of a followed by b with the new symbol ab, scanning each word from left to right so that overlapping occurrences such as "a a a" become "aa a".
4. Append (a, b) to the merge list. Repeat until you have M merges or no pair is left.

### What comes out

The merge list, in order. Its position is a merge's **rank**. The vocabulary is the base alphabet plus one symbol per merge, so its size is the base size plus M, and M is the only knob (Sennrich et al. §3.2). Real tokenisers choose M so the vocabulary lands near a target, such as GPT-2's 50,000 merges.

### Using the merges on new words

Split the word into characters, then apply the merges in rank order. "lowest" never appeared in the toy corpus below, yet it becomes `low` + `est</w>`: two known pieces. The tokeniser card shows how to do this fast.

## Cost

Let S be the total number of symbols in the distinct-word table. One naive merge recounts every pair, O(S), and rewrites every word, O(S), so M merges cost **O(M × S)**. Deduplicating words is what makes even this affordable: *Pride and Prejudice* has 166,681 pre-tokenised words but only 9,694 distinct ones with 78,072 symbols, and the naive trainer took about 78 ms per merge on my machine (78 s for 1,000 merges). The next card removes the factor M.

Each merge of a pair with count c shortens the training corpus by c symbols (fewer if occurrences overlap, as in "a a a", where the count is 2 but only one merge fits). Greedy choice of the most frequent pair is therefore the locally best compression step, but not a globally optimal vocabulary.

## When to use it

| Unit | Vocabulary | Unseen words | Sequence length |
|---|---|---|---|
| Whole words | every inflection needs an entry, still incomplete | become an unknown token | shortest |
| Characters or bytes | tiny (256 for bytes) | never unknown | longest |
| BPE subwords | chosen size, commonly tens of thousands to a few hundred thousand | spelt from smaller pieces | in between |

Choose BPE when you need an open vocabulary with a fixed budget: frequent words cost one token, rare words a few. With a byte base, nothing is ever unknown. Its weaknesses come from its greediness and its training data: merges reflect the corpus, so under-represented languages, numbers and code get fewer, shorter tokens, and the AI guide's tokens lesson measures what that costs.

## Worked trace

Sennrich's toy dictionary: low ×5, lower ×2, newest ×6, widest ×3, each ending in `</w>`. Ties go to the smallest pair.

```steps
Count pairs, weighted by word counts. Three pairs tie at 9; the smallest is (e, s)
    l o w </w> x5   l o w e r </w> x2   n e w e s t </w> x6   w i d e s t </w> x3
    {{(e,s) 9}}  (s,t) 9  (t,</w>) 9  (w,e) 8  (l,o) 7  (o,w) 7
---
Merge 1: e s -> es in newest and widest. The corpus shrinks from 95 to 86 symbols
    n e w {{es}} t </w>   w i d {{es}} t </w>
    (es,t) 9  (t,</w>) 9  (l,o) 7  (o,w) 7  (e,w) 6  (n,e) 6
---
Merges 2 and 3: (es, t) then (est, </w>), both with count 9
    n e w {{est</w>}}   w i d {{est</w>}}
---
Merges 4 and 5: (l, o) then (lo, w), count 7 each
    {{low}} </w>   {{low}} e r </w>
---
Merges 6 to 8: (e, w), (ew, est</w>) and (n, ewest</w>) with count 6; the tie at 6 between (e, w) and (n, e) went to (e, w)
    {{newest</w>}} x6
---
Merges 9 and 10: (low, </w>) count 5, (d, est</w>) count 3. The corpus is now 28 symbols
    low</w> x5   low e r </w> x2   newest</w> x6   w i dest</w> x3
---
Apply the 10 merges, in order, to words never seen in training
    lowest -> {{low  est</w>}}
    newer  -> n  ew  e  r  </w>
    wider  -> w  i  d  e  r  </w>
```

Notice "newer": because the tie went to (e, w), the corpus never formed `new`, so "newer" splits oddly. Sennrich's own Algorithm 1 breaks ties by dictionary order instead, picks (n, e) at merge 6, and turns "newer" into `new e r </w>`. Same data, same algorithm, different vocabulary.

## Template

```python
from collections import Counter


def pair_counts(words):
    """Weighted count of every adjacent symbol pair. words: {tuple of symbols: count}."""
    counts = Counter()
    for symbols, freq in words.items():
        for pair in zip(symbols, symbols[1:]):
            counts[pair] += freq
    return counts


def merge_word(symbols, pair, new):
    """Replace non-overlapping occurrences of pair, scanning left to right."""
    out, i = [], 0
    while i < len(symbols):
        if i + 1 < len(symbols) and (symbols[i], symbols[i + 1]) == pair:
            out.append(new)
            i += 2
        else:
            out.append(symbols[i])
            i += 1
    return tuple(out)


def train_naive(words, num_merges):
    """Learn up to num_merges merge rules; ties go to the smallest pair."""
    merges = []
    for _ in range(num_merges):
        counts = pair_counts(words)
        if not counts:
            break
        best = min(counts, key=lambda p: (-counts[p], p))
        merges.append(best)
        words = {merge_word(w, best, best[0] + best[1]): c for w, c in words.items()}
    return merges, words
```

Call it as `train_naive({tuple("low") + ("</w>",): 5, ...}, 10)`. It returns the merges and the final segmentation of every training word. It is slow on purpose: it is the oracle the fast trainer in the next card is tested against.

## Pitfalls

- **Unstable ties.** Python's `max(counts, key=counts.get)` returns the first maximum in dictionary order, which depends on insertion order. Write the tie rule down; Hugging Face's trainer, for instance, prefers the smaller pair.
- **Overlaps.** "a a a" has two (a, a) pairs but only one merge fits; merge left to right and expect counts to overestimate the saving.
- **Crossing word boundaries.** Counting pairs across words is slower and learns tokens that glue words together; train on the distinct-word table.
- **Applying merges in the wrong order.** At encoding time apply merges by rank, not by how frequent the pair is in the new text.
- **Leftover intermediate symbols.** A symbol can be merged away almost everywhere during training, so it exists in the vocabulary but almost never appears on its own (Sennrich et al. mention 'safeguar', always absorbed into 'safeguard'). Such tokens get little training signal; the last card returns to this.

## Check yourself

Q: Train three merges on tea ×4, ten ×6, net ×3 (no end-of-word marker). What are the merges, and how is "net" segmented at the end?
A: The pair counts are (t,e) 10, (e,n) 6, (e,a) 4, (e,t) 3, (n,e) 3, so the merges are (t, e), then (te, n) with 6, then (te, a) with 4. "net" contains no "t e" (its pairs are n-e and e-t), so it stays `n e t`.

Q: Why is the vocabulary size exactly the base alphabet size plus the number of merges?
A: Each merge creates exactly one new symbol (the concatenation of the pair) and never deletes one, since the parts stay in the vocabulary even if they no longer occur in the corpus. Starting from the base symbols, M merges add M symbols (assuming no merge recreates a string that already exists).

Q: Your tokeniser must handle any text in any language without an unknown token. What base alphabet do you choose, and what does it cost?
A: Bytes: 256 base symbols cover every UTF-8 string, so nothing is unknown. The cost is that rare characters (most of Unicode) take two to four byte tokens until merges cover them; with a character base you would need over 130,000 base symbols instead.

Q: Two teams train BPE on the same corpus with the same number of merges and get different vocabularies. Name the most likely cause.
A: Different tie-breaking between equally frequent pairs, for example dictionary iteration order in one and smallest-pair order in the other. Once one merge differs, all later counts differ. The worked trace shows a single tie changing how "newer" is split.

## Lab

- Run `train_naive` on the toy dictionary with 10 merges. Expected: (e,s), (es,t), (est,</w>), (l,o), (lo,w), (e,w), (ew,est</w>), (n,ewest</w>), (low,</w>), (d,est</w>); "lowest" becomes `low est</w>`.
- Track the corpus length (sum of symbols times word count) after each merge. Expected: 95, 86, 77, 68, 61, 54, 48, 42, 36, 31, 28; each merge saves exactly its pair count here, because no occurrences overlap.
- Replace the tie rule with `max(counts, key=counts.get)`. Expected: the first five merges agree; merge 6 becomes (n, e), followed by (ne, w), (new, est</w>), (low, </w>), (w, i), and "newer" becomes `new e r </w>`.

> [!know]
> You now know what BPE learns: an ordered list of greedy merges that compresses the training words and spells any new word from known pieces.

=== primer | How do you train BPE fast enough for a real corpus? | 17 min
goal: Implement BPE training with incremental pair counts, a pair-to-positions index, doubly linked symbol lists and a lazily updated max-heap, and prove it learns the same merges as the naive trainer
tag: tokens-bpe-heap | BPE training with a lazy heap and linked lists
link: Hugging Face tokenizers: BPE trainer (v0.23.3) | https://github.com/huggingface/tokenizers/blob/v0.23.3/tokenizers/src/models/bpe/trainer.rs#L489-L608 | 15 min: the merge loop; see the heap of merges, the stale-count check right after each pop and where_to_update, the production version of this card
link: subword-nmt: learn_bpe.py | https://github.com/rsennrich/subword-nmt/blob/master/subword_nmt/learn_bpe.py | 10 min: Sennrich's own trainer; read update_pair_statistics (incremental neighbour updates) and prune_stats (a frequency threshold instead of a heap)

> [!key]
> The naive trainer recounts every pair after every merge. But a merge only changes pairs next to the occurrences it merges: x a b y becomes x ab y, so (x, a), (a, b) and (b, y) lose counts and (x, ab) and (ab, y) gain them. Keep **pair counts** up to date incrementally, an **index from each pair to its positions**, a **doubly linked list** over each word's symbols so merging unlinks one symbol in O(1), and a **max-heap** of pairs by count. Python's heap cannot update a key, so push a fresh entry when a count rises and, when you pop an entry whose stored count is stale, fix it **lazily**: push the current count back, or drop it if zero.

## Intuition

A shop tracks which product is its bestseller. Recounting every receipt after each sale is the naive trainer. Keeping a running tally per product, and adjusting only the tallies a sale touches, is the incremental version. The leaderboard is a heap: when a tally drops, nobody erases the old board entry right away; whoever reads the top checks it against the live tally and corrects it if it is out of date.

## How it works

### What one merge changes

Merging one occurrence of (a, b) with left neighbour x and right neighbour y in a word that occurs c times changes exactly five counts:

```text
before:  x  a  b  y          after:  x  ab  y
(x, a)  -c      (x, ab) +c
(b, y)  -c      (ab, y) +c
(a, b)  -c
```

Everything else is untouched, so the work per merge is proportional to the number of occurrences of the merged pair, not to the corpus.

### Doubly linked symbols

Store each distinct word as arrays: `sym[i]`, `prv[i]`, `nxt[i]`. Positions never move. Merging the pair at i and j = nxt[i] writes the new symbol into i, marks j dead, and relinks `nxt[i] = nxt[j]` and `prv[nxt[j]] = i`: O(1), with no shifting of the rest of the word.

### The position index

`where[pair]` holds (word, i) for every place the pair starts. When a merge creates (x, ab) or (ab, y), add those positions. Entries can go stale (a symbol was merged away), so check before merging that `sym[i] == a` and `sym[nxt[i]] == b`. Process a pair's positions in increasing order inside each word; then "a a a a" merges as `aa aa`, exactly as the naive left-to-right scan does, and the skipped overlap fails the check.

### The lazy max-heap

`heapq` is a min-heap, so store (−count, pair); among equal counts the smaller pair comes first, which is the naive trainer's tie rule. After each merge, push an entry for every touched pair whose count is positive. When you pop (−c, p):

- if c equals the current count of p, it is the true maximum: merge it;
- otherwise the entry is stale: push (−current, p) if the current count is positive, drop it if zero, and pop again.

Why the first fresh pop is the true maximum: an entry is pushed every time a pair's count rises, so every pair with a positive count has an entry whose stored count is at least its true count. Any pair that should come first therefore has an entry that pops first, either fresh (merged) or stale and too high (corrected and re-pushed).

## Cost

Let S be the symbols in the distinct-word table, P the distinct pairs, and occ_m the occurrences merged at step m.

- Indexing: one pass, O(S), plus `heapify`, O(P).
- Merge m: sort its positions, O(occ_m log occ_m), then O(1) list work and at most four count changes per occurrence, and at most four heap pushes, each O(log H).
- Stale pops: every pop that is not a merge removes an entry some push created, so stale pops never outnumber pushes.

Total: about **O(S + Σ occ_m log H)** instead of O(M × S). Measured on *Pride and Prejudice* (737,950 bytes, 9,694 distinct words, 78,072 symbols) on one core of my machine:

| Merges | Naive | Heap | Speed-up |
|---|---|---|---|
| 100 | 9.6 s | 0.31 s | 31× |
| 300 | 25.4 s | 0.39 s | 66× |
| 1,000 | 78.4 s | 0.49 s | 160× |
| 10,000 | (not run) | 1.15 s | |

Both produced identical merge lists. Most of the heap trainer's time at 100 merges is the initial indexing, about 0.3 s; after that each merge is cheap because later merges touch rarer pairs.

## When to use it

Use the naive trainer for teaching, tiny corpora and as the test oracle. Use the incremental trainer for anything real; production trainers do the same in compiled code. Hugging Face's trainer keeps word indices rather than positions in its index and rescans each affected word, which is fine because pre-tokenised words are short. Positions plus linked lists pay off when "words" are long, for example when training without pre-tokenisation. Sennrich's subword-nmt takes a third route: it updates counts incrementally but finds the maximum among pairs above a frequency threshold, recomputing that candidate set when it runs out, instead of using a heap.

## Worked trace

The toy dictionary again (low ×5, lower ×2, newest ×6, widest ×3 with `</w>`). Watch the heap hand back stale entries.

```steps
Index once: 13 pair counts, heap of (-count, pair). The top entry (e,s) is fresh: merge 1
    heap top   {{(-9,(e,s))}}  (-9,(s,t))  (-9,(t,</w>))  (-8,(w,e))  (-7,(l,o))
    where[(e,s)] = {(newest, 3), (widest, 3)}
---
newest x6 at position 3: x = w, y = t. Five counts change; position 4 (s) is unlinked
    (w,e) -6  (w,es) +6  (s,t) -6  (es,t) +6  (e,s) -6
    n e w {{es}} t </w>      nxt = [1, 2, 3, {{5}}, 5, 6, -1]
---
widest x3 at position 3: x = d, y = t. Push every touched pair whose count is positive
    (d,e) -3  (d,es) +3  (s,t) -3  (es,t) +3  (e,s) -3
    counts now  (e,s) 0  (s,t) 0  (es,t) {{9}}  (w,e) 2  (w,es) 6  (d,es) 3
---
Pop (-9,(es,t)): fresh, merge 2. It sorts before (s,t) because 'es' < 's'. Then (est,</w>) pops fresh: merge 3
    n e w {{est</w>}}   w i d {{est</w>}}
---
Pop (-9,(s,t)): stored 9, actual 0, drop it. Pop (-9,(t,</w>)): actual 0, drop it
    stale entries left behind by merges 1 and 2
---
Pop (-8,(w,e)): stored 8, actual 2 (only lower still has w e). Re-push (-2,(w,e))
    heap top   {{(-7,(l,o))}}  (-7,(o,w))  (-6,(e,w)) ...  (-2,(w,e))
---
Pop (-7,(l,o)): fresh, merge 4; then (lo,w), merge 5. Same five merges as the naive trainer
    merges  (e,s) (es,t) (est,</w>) (l,o) (lo,w)
```

## Template

```python
import heapq
from collections import defaultdict


def train_fast(words, num_merges):
    """Same merges as train_naive, but each merge only touches the pair's occurrences."""
    sym, prv, nxt, cnt = [], [], [], []
    pairs = defaultdict(int)                 # pair -> weighted count
    where = defaultdict(set)                 # pair -> {(word, index of left symbol)}
    for w, (word, c) in enumerate(words.items()):
        n = len(word)
        sym.append(list(word))
        prv.append(list(range(-1, n - 1)))   # doubly linked list over the symbols
        nxt.append(list(range(1, n)) + [-1])
        cnt.append(c)
        for i in range(n - 1):
            pairs[word[i], word[i + 1]] += c
            where[word[i], word[i + 1]].add((w, i))
    heap = [(-c, p) for p, c in pairs.items()]
    heapq.heapify(heap)
    merges = []
    while heap and len(merges) < num_merges:
        negc, p = heapq.heappop(heap)
        if -negc != pairs[p]:                # stale: the count changed after this push
            if pairs[p] > 0:
                heapq.heappush(heap, (-pairs[p], p))
            continue
        a, b = p
        new = a + b
        merges.append(p)
        touched = set()
        for w, i in sorted(where.pop(p)):    # left to right inside each word
            s, L, R, c = sym[w], prv[w], nxt[w], cnt[w]
            j = R[i]
            if s[i] != a or j == -1 or s[j] != b:
                continue                     # already consumed by an overlapping merge
            l, r = L[i], R[j]
            if l != -1:                      # left neighbour: (x, a) becomes (x, ab)
                pairs[s[l], a] -= c
                pairs[s[l], new] += c
                where[s[l], new].add((w, l))
                touched.update([(s[l], a), (s[l], new)])
            if r != -1:                      # right neighbour: (b, y) becomes (ab, y)
                pairs[b, s[r]] -= c
                pairs[new, s[r]] += c
                where[new, s[r]].add((w, i))
                touched.update([(b, s[r]), (new, s[r])])
            pairs[p] -= c
            s[i], s[j] = new, None           # unlink j
            R[i] = r
            if r != -1:
                L[r] = i
        for q in touched:
            if pairs[q] > 0:
                heapq.heappush(heap, (-pairs[q], q))
    return merges
```

Tested against `train_naive` on 400 random corpora over alphabets of one to four letters (where overlaps such as "aaaa" are common) and on the whole of *Pride and Prejudice* for up to 1,000 merges: identical merge lists every time.

## Pitfalls

- **Forgetting a neighbour update.** Counts drift silently and the trainer picks wrong merges a few hundred steps later. Always test against the naive trainer.
- **Unsorted positions.** Sets iterate in arbitrary order; merging "a a a a" from the middle first gives `a aa a` instead of `aa aa`.
- **Trusting the index.** Positions in `where` can be stale; check the symbols before merging, as the template does.
- **Decrease-key with heapq.** It does not exist. Either push duplicates and fix them lazily, or use an indexed heap or a sorted container.
- **Mismatched tie-breaking.** The heap's (−count, pair) order must equal the naive trainer's rule, or the two stop agreeing at the first tie.

## Check yourself

Q: After merge 1, (e, s), in the trace, which counts changed and what are they now?
A: (w,e) 8 → 2, (w,es) 0 → 6, (s,t) 9 → 0, (es,t) 0 → 9, (d,e) 3 → 0, (d,es) 0 → 3 and (e,s) 9 → 0. Nothing else changed.

Q: Why is the first popped entry whose stored count equals the current count really the most frequent pair?
A: Every time a pair's count rises, a fresh entry with the new count is pushed; when it falls, the old entry stays with an overestimate. So every pair with a positive count has an entry whose stored count is at least its true count. If some pair q had a higher priority than the popped fresh entry, q's entry would sort earlier and would have been popped first, merged if fresh or corrected if stale. Hence no such q exists.

Q: Train two merges on {"aaaa": 1, "aaa": 1}. What are the pair counts at the start, the merges, and the final words?
A: (a, a) occurs 3 times in "aaaa" and twice in "aaa", so its count is 5 and it is merged first, giving `aa aa` and `aa a`. Now (aa, aa) and (aa, a) both have count 1; the tie goes to the smaller pair, ('aa', 'a') (since 'a' sorts before 'aa'), so "aaa" becomes `aaa` and "aaaa" stays `aa aa`.

Q: A variant iterates `for w, i in where.pop(p)` without sorting. On which input does it disagree with the naive trainer?
A: Any word with three or more consecutive copies of a doubled symbol, such as "aaaa": if position 1 is processed first it merges the middle pair, leaving `a aa a`, while the naive left-to-right scan gives `aa aa`. The pair counts and every later merge then differ.

## Lab

- Run both trainers on 400 random corpora (alphabet of one to four letters, one to fifteen words of length one to nine, counts one to five, up to 30 merges). Expected: identical merge lists in every case.
- Add a counter for stale pops and run the first five merges of the toy dictionary. Expected: three stale pops, (s,t) and (t,</w>) dropped and (w,e) re-pushed with count 2, exactly as in the trace.
- Run `train_fast({tuple("aaaa"): 1, tuple("aaa"): 1}, 2)`. Expected: [('a', 'a'), ('aa', 'a')], matching `train_naive`, which also reports the final words `aa aa` and `aaa`.

> [!know]
> You now know how to train BPE in near-linear time with incremental counts, linked symbols and a lazily corrected heap, and how to prove it against the naive trainer.

=== primer | How does a tokeniser apply merge ranks to new text? | 15 min
goal: Encode a word by repeatedly merging its lowest-ranked adjacent pair, with an O(n²) scan and an O(n log n) heap, and reproduce GPT-2's token ids exactly
tag: tokens-encode | Encoding by lowest merge rank
link: tiktoken source: byte-pair merge (0.14.0) | https://github.com/openai/tiktoken/blob/0.14.0/src/lib.rs#L140-L211 | 10 min: read _byte_pair_merge with its O(mn) comment, then byte_pair_encode, which switches to the heap version for pieces of 100 bytes or more
link: Kudo and Richardson 2018, SentencePiece | https://arxiv.org/abs/1808.06226 | 5 min: §3.2 contrasts naive O(N²) BPE segmentation with SentencePiece's O(N log N) binary-heap version

> [!key]
> Encoding never counts anything. Each merge's **rank** is its position in the training list. To encode a word, split it into base symbols and repeatedly merge the adjacent pair with the **lowest rank**, leftmost first on ties, until no adjacent pair has a rank. A linear scan per merge costs O(n²) per word, fine for short pre-tokenised chunks; a **min-heap of (rank, position)** over a doubly linked list costs O(n log n). Cache results per chunk, because the same words recur.

## Intuition

The merge list is a recipe book ordered by when each shortcut was invented. To shorten a new word, always use the oldest shortcut that applies anywhere in it. That replays the training merges that touch this word, in the order training applied them, so the word ends up exactly as training would have left it. On 300 random training runs, all 3,196 training words re-encoded this way matched the trainer's own final segmentation.

## How it works

### Ranks

`ranks = {pair: index}` for the training merges. GPT-2 ships them as `vocab.bpe`: a version line, then 50,000 merges, one pair per line. tiktoken stores them differently, as a rank for each token's bytes, and merges by looking up the rank of the concatenated bytes; its source notes this is equivalent as long as BPE is trained the usual way.

### Linear scan (tiktoken, short pieces)

Keep the parts in a list. Each round, scan all adjacent pairs, find the lowest rank, merge it, repeat. Each round is O(n) and there are at most n − 1 rounds: O(n²). tiktoken does this for pieces under 100 bytes; its source comment counts it as O(mn) for m merges and n parts, and argues that for short pieces cache locality beats a heap's better complexity.

### Heap (tiktoken's long pieces, Hugging Face, SentencePiece)

Link the symbols with `prv` and `nxt`. Push (rank, i) for every adjacent pair that has a rank. Pop the minimum: if the pair now at i is no longer that pair, the entry is stale; skip it. Otherwise merge (write the joined symbol into i, unlink the right one) and push the two new pairs that now touch i: (left neighbour, new) and (new, right neighbour). Hugging Face's `merge_all` works like this, and tiktoken switches to a heap for pieces of 100 bytes or more.

### GPT-2's own variant

GPT-2's `encoder.py` takes the lowest-ranked bigram and merges all its occurrences in one left-to-right pass, then recomputes. It gives the same result as merging leftmost occurrences one at a time: all three encoders in this card agreed on every test string.

### Caching

Pre-tokenisation splits text into chunks (words with their leading space, numbers, punctuation runs), and the same chunks recur constantly. GPT-2's encoder memoises each chunk's result in a dictionary, so most chunks cost one lookup.

## Cost

For a chunk of n base symbols:

| Encoder | Per merge | Whole chunk | Comment |
|---|---|---|---|
| Linear scan | O(n) scan plus an O(n) list splice | O(n²) | best for short chunks |
| Heap with linked list | O(log n) pop plus at most 2 pushes | O(n log n) | stale pops never outnumber pushes |
| Cached chunk | one dictionary lookup | O(n) to hash the key | the common case in real text |

Measured with GPT-2's merges on runs of random lowercase letters (a single chunk, since the regex keeps letters together): 100 letters took 0.7 ms linear and 0.2 ms with the heap; 1,000 letters 84 ms and 4.5 ms; 5,000 letters 3.6 s and 8.5 ms. The quadratic encoder is fine for words and dangerous for adversarial input such as a long run of characters with no spaces, which is why tiktoken switches at 100 bytes.

## When to use it

Use the linear scan when pre-tokenisation guarantees short chunks (ordinary prose and code) and simplicity matters. Use the heap whenever chunk length is not bounded: no pre-tokenisation, long URLs or base64 blobs, or inputs an attacker controls. Use a per-chunk cache in front of either. Encode by rank, never by frequency in the text being encoded: the tokenisation of a word must not depend on the rest of the document.

## Worked trace

GPT-2's real ranks on " lowest". Byte-level BPE writes the leading space as Ġ (the next card explains why).

```steps
Split into base symbols and look up every adjacent pair's rank. The lowest is (e, s) at 18
    parts   Ġ  l  o  w  e  s  t
    ranks   (Ġ,l) 44  (l,o) 5183  (o,w) 66  (w,e) 476  {{(e,s) 18}}  (s,t) 45
---
Merge e s. The new pair (w, es) has no rank; (es, t) has 139. Lowest now: (Ġ, l) at 44
    parts   Ġ  l  o  w  {{es}}  t
    ranks   {{(Ġ,l) 44}}  (l,o) 5183  (o,w) 66  (w,es) none  (es,t) 139
---
Merge Ġ l. Lowest now: (o, w) at 66
    parts   {{Ġl}}  o  w  es  t
    ranks   (Ġl,o) 2120  {{(o,w) 66}}  (w,es) none  (es,t) 139
---
Merge o w, then (es, t) at 139
    parts   Ġl  {{ow}}  {{est}}
    ranks   (Ġl,ow) 1621  (ow,est) none
---
Merge Ġl ow at 1621, then Ġlow est at 8760: one token, id 9016, as tiktoken also returns
    parts   {{Ġlow}}  est   ->   {{Ġlowest}}
```

## Template

```python
import heapq


def encode_linear(word, ranks):
    """Repeatedly merge the lowest-ranked adjacent pair (leftmost on ties). O(n^2) per word."""
    parts = list(word)
    while len(parts) > 1:
        best, at = None, -1
        for i in range(len(parts) - 1):
            r = ranks.get((parts[i], parts[i + 1]))
            if r is not None and (best is None or r < best):
                best, at = r, i
        if best is None:
            break
        parts[at:at + 2] = [parts[at] + parts[at + 1]]
    return parts


def encode_heap(word, ranks):
    """Same result in O(n log n): a min-heap of (rank, position) over a linked list."""
    s = list(word)
    nxt = list(range(1, len(s))) + [-1]
    prv = list(range(-1, len(s) - 1))
    heap = [(ranks[s[i], s[i + 1]], i) for i in range(len(s) - 1) if (s[i], s[i + 1]) in ranks]
    heapq.heapify(heap)
    while heap:
        r, i = heapq.heappop(heap)
        j = nxt[i]
        if s[i] is None or j == -1 or ranks.get((s[i], s[j])) != r:
            continue                                  # stale entry: that pair has changed
        s[i], s[j] = s[i] + s[j], None
        nxt[i] = nxt[j]
        if nxt[i] != -1:
            prv[nxt[i]] = i
        for left in (prv[i], i):                      # the two pairs that now touch s[i]
            if left != -1 and nxt[left] != -1 and (s[left], s[nxt[left]]) in ranks:
                heapq.heappush(heap, (ranks[s[left], s[nxt[left]]], left))
    return [x for x in s if x is not None]
```

Build `ranks` with `{pair: r for r, pair in enumerate(merges)}`. Tested: both encoders and a GPT-2-style all-occurrences encoder agree on random words for 300 trained merge lists, reproduce the trainer's segmentation of every training word, and, with GPT-2's merges and the next card's byte mapping, return exactly tiktoken's GPT-2 token ids on 3,023 test strings.

## Pitfalls

- **Merging by frequency at encode time.** The rank order is the whole model; recomputing "most frequent pair in this text" gives a different, context-dependent tokenisation.
- **Skipping the staleness check.** A heap entry can describe a pair that has since been merged into something else; merging it anyway corrupts the word.
- **Ties at the same rank.** The same pair can occur several times; merge the leftmost first (the heap's (rank, position) order does this), or "a a a" and similar runs come out different.
- **Unbounded chunks.** Without pre-tokenisation, a quadratic encoder turns one long input into a denial of service.
- **Unknown base symbols.** With a character-level base, a character never seen in training has no symbol at all; byte-level BPE (next card) removes the problem.

## Check yourself

Q: With ranks {(a,a): 0, (aa,aa): 1, (aa,a): 2}, encode "aaaa" and "aaaaa".
A: "aaaa": merge (a,a) at position 0 to get `aa a a`; the lowest is now (a,a) at position 1, giving `aa aa`; then (aa,aa) gives `aaaa`. "aaaaa": the same steps give `aa aa a`, then (aa,aa) at rank 1 beats (aa,a) at rank 2, giving `aaaa a`, and no pair `(aaaa, a)` has a rank, so the result is `aaaa`, `a`.

Q: Why is the heap encoder O(n log n)?
A: It starts with at most n − 1 entries. Each merge pops one entry and pushes at most two, and there are at most n − 1 merges, so at most 3n entries are ever pushed; every pop, stale or not, removes one of them. That is O(n) heap operations of O(log n) each.

Q: Your service tokenises user-uploaded files that may contain megabyte-long lines without spaces. Which encoder, and what else do you add?
A: The heap encoder, because chunk length is unbounded and the quadratic scan could take minutes on one line. Also cap or split very long chunks, and keep a cache for ordinary short chunks.

Q: A colleague's heap encoder pops (rank, i) and merges `s[i]` with `s[nxt[i]]` without checking that this pair still has rank r. Give an input where it goes wrong.
A: With ranks {(a,b): 0, (b,c): 1} and the word "abc", the heap holds (0, 0) and (1, 1). Popping (0, 0) merges `ab c` and unlinks position 1. Later (1, 1) pops; position 1 is dead (its symbol is None), and without the check the code would join None with the next symbol and crash, or with other bookkeeping silently merge the wrong pair.

## Lab

- Encode " lowest" with GPT-2's merges (download `vocab.bpe` and `encoder.json` from the URLs that tiktoken's `openai_public.py` lists for the gpt2 encoding). Expected: merges at ranks 18, 44, 66, 139, 1621 and 8760, ending in one token, `Ġlowest`, id 9016.
- Compare `encode_linear` and `encode_heap` on words of 100, 1,000 and 5,000 random lowercase letters. Expected: identical outputs, and timings that grow roughly with n² for the scan (thousands of milliseconds at 5,000) and n log n for the heap (a few milliseconds).
- Encode "aaaa" and "aaaaa" with the ranks from the first question using both encoders. Expected: `['aaaa']` and `['aaaa', 'a']` from both.

> [!know]
> You now know how to encode text with ranked merges, when a linear scan is enough and when you need a heap over a linked list.

=== primer | How does byte-level BPE encode any string, and what does GPT-2's pre-tokeniser do? | 16 min
goal: Map UTF-8 bytes to GPT-2's printable alphabet, split text with its pre-tokenisation regex, apply BPE per chunk, and predict the resulting token boundaries
tag: tokens-bytelevel | Byte-level BPE and regex pre-tokenisation
link: GPT-2 source: encoder.py | https://github.com/openai/gpt-2/blob/master/src/encoder.py | 10 min: bytes_to_unicode, the regex with its comment about IGNORECASE, bpe() with its cache, and decode() with errors='replace'
link: Radford et al. 2019, the GPT-2 paper | https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf | 5 min: §2.2 Input Representation explains the byte base, and why merges are kept from crossing character categories except for spaces

> [!key]
> Byte-level BPE runs on the UTF-8 **bytes** of the text, so the base vocabulary is just 256 symbols and no string is ever unknown. GPT-2 maps each byte to a printable character (a space becomes `Ġ`) so the BPE code can work on ordinary strings. Before BPE, a **regex** splits the text into chunks (contractions, letters with an optional leading space, digits, other symbols, whitespace), and merges never cross a chunk. The vocabulary is 256 bytes + 50,000 merges + 1 end-of-text token = 50,257.

## Intuition

Character-level BPE needs every character it will ever see in its base alphabet, and Unicode has far more than 130,000 code points, so either the base is enormous or some characters become "unknown". Bytes are the universal alphabet underneath every character: UTF-8 spells each character with one to four bytes. Start from the 256 byte values and let merges build up the common characters and words. The price is that rare characters cost several tokens.

Without pre-tokenisation, BPE would happily learn "dog.", "dog!" and "dog?" as separate tokens. The GPT-2 paper reports exactly that waste and fixes it by keeping merges from crossing character categories, with an exception for spaces: a word keeps its leading space, so " dog" is one token.

## How it works

### Bytes to printable characters

GPT-2's table keeps the 188 bytes that are already visible Latin-1 characters (`!` to `~`, `¡` to `¬`, `®` to `ÿ`) as themselves and maps the other 68 (control bytes, space, and a few more) in order to code points 256 and up. Space (byte 32) becomes `Ġ` (U+0120) and newline (byte 10) becomes `Ċ` (U+010A). The table is a bijection, so decoding is exact: map characters back to bytes, then decode UTF-8.

### The pre-tokenisation regex

```text
's|'t|'re|'ve|'m|'ll|'d          English contractions
| ?\p{L}+                        letters, with one optional leading space
| ?\p{N}+                        digits (any length), optional leading space
| ?[^\s\p{L}\p{N}]+              other symbols: punctuation, emoji
|\s+(?!\S)|\s+                   whitespace: a run before a word gives its last space away
```

`\p{L}` (any letter) and `\p{N}` (any number) need the third-party `regex` module; Python's `re` does not support them. The `\s+(?!\S)` alternative takes a run of spaces but leaves the last one for the following word, so "  hello" (two spaces) becomes " " and " hello".

### BPE per chunk

Each chunk's UTF-8 bytes are mapped to characters and encoded with the previous card's encoder; chunks never merge with each other. With GPT-2's real merges, this module's code returns the same token ids as `tiktoken.get_encoding("gpt2")` on 3,023 test strings (prose, code, numbers, accents, Chinese, emoji, odd whitespace).

### Newer patterns

OpenAI's later `cl100k_base` pattern, visible in tiktoken, matches contractions case-insensitively, splits digit runs into groups of at most three, and treats newlines separately. The same text therefore splits differently: "1234567" is `123 45 67` under GPT-2 but `123 456 7` under cl100k_base.

## Cost

The regex is one linear pass over the text. Each chunk costs its BPE encoding, usually a cache hit. Byte-level input is longer than character input for non-ASCII text (two to four bytes per character) until merges cover those characters. The vocabulary's 50,257 entries cost embedding and output-layer rows, which is why vocabulary size is a model-design trade-off.

## When to use it

| Base | Unknown input | Rare characters | Typical use |
|---|---|---|---|
| Characters (with an unknown token) | possible | one symbol each, if in the alphabet | older subword systems |
| Bytes, GPT-2 style | impossible | two to four tokens until merged | GPT-2 and tiktoken encodings |
| Characters with byte fallback | impossible | characters seen in training are single symbols; others fall back to bytes | some SentencePiece models |

Choose byte-level when the input is open-ended: code, many languages, emoji, binary-looking text. Choose the pre-tokenisation pattern deliberately, because it decides which merges are even possible, for instance whether digits can merge into long numbers.

## Worked trace

"Hi naïve 😊!!" through GPT-2's pipeline. The ids match tiktoken's.

```steps
The regex makes three chunks. The space joins the following chunk; the emoji and "!!" are both "other symbols", so they form one chunk
    'Hi'  |  ' naïve'  |  ' 😊!!'
---
UTF-8 bytes of ' naïve': ï takes two bytes, 195 and 175
    32  110  97  {{195  175}}  118  101
---
Map bytes to characters: 32 -> Ġ, 195 -> Ã, 175 -> ¯; BPE merges the whole chunk into one known token
    Ġ n a {{Ã ¯}} v e   ->   {{ĠnaÃ¯ve}}   id 41492
---
' 😊!!' is 7 bytes; the emoji's 4 bytes (240 159 152 138) map to ð Ł ĺ Ĭ, and BPE splits the chunk in three
    ĠðŁĺĬ!!   ->   {{ĠðŁĺ}}  {{Ĭ}}  !!   ids 30325, 232, 3228
---
Final ids. Decoding 30325 alone gives ' ' plus a replacement character: it holds only 3 of the emoji's 4 bytes
    [17250, 41492, {{30325, 232}}, 3228]
    decode one by one: 'Hi' ' naïve' ' �' '�' '!!'
```

## Template

```python
def byte_alphabet():
    """Map each byte 0..255 to a printable character (GPT-2's trick).

    Printable Latin-1 bytes stand for themselves; the other 68 bytes (controls,
    space, a few others) are shifted to code points 256 and up, in byte order.
    """
    keep = [*range(ord("!"), ord("~") + 1), *range(ord("¡"), ord("¬") + 1),
            *range(ord("®"), ord("ÿ") + 1)]
    table, extra = {}, 256
    for b in range(256):
        if b in keep:
            table[b] = chr(b)
        else:
            table[b] = chr(extra)
            extra += 1
    return table


GPT2_SPLIT = r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""


def gpt2_encode(text, ranks, vocab, encode_word):
    """Pre-tokenise with the regex, map bytes to characters, apply BPE per chunk."""
    import regex                                         # pip install regex (for \p{L})
    to_char = byte_alphabet()
    ids = []
    for chunk in regex.findall(GPT2_SPLIT, text):
        word = "".join(to_char[b] for b in chunk.encode("utf-8"))
        ids.extend(vocab[piece] for piece in encode_word(word, ranks))
    return ids
```

Pass `encode_heap` from the previous card as `encode_word`, the ranks from `vocab.bpe` and the token-to-id map from `encoder.json`. `byte_alphabet()` equals GPT-2's `bytes_to_unicode()` table exactly.

## Pitfalls

- **Leading spaces.** "hello" is id 31373 and " hello" is 23748 in GPT-2: different tokens. A prompt that ends with a space, or a template that adds one, changes what the model sees.
- **Trailing spaces.** "trailing space " ends in a lone space token (id 220), a token that rarely ends text in training data.
- **Streaming decode.** Tokens can end in the middle of a character. Buffer bytes until they form complete UTF-8 before printing, or you show replacement characters, as in the trace.
- **Case-sensitive contractions.** GPT-2's regex lists only lowercase contractions, so "it's" is `it 's` but "IT'S" is `IT ' S`; the source even carries a comment saying IGNORECASE should have been added. cl100k_base matches them case-insensitively and gives `IT 'S`.
- **Numbers are chopped arbitrarily.** GPT-2 splits "1234567" as `123 45 67`, "2024" as `20 24` and "1000000" as `1 000000`; place value is not visible in the tokens.
- **Using `re` instead of `regex`.** Python's built-in module does not understand `\p{L}`; approximating it changes the splits for non-ASCII text.

## Check yourself

Q: How many bytes does GPT-2's table keep as themselves, and what do space and newline become?
A: 188 bytes map to themselves (94 from `!` to `~`, 12 from `¡` to `¬`, 82 from `®` to `ÿ`); the other 68 are shifted to code points 256 to 323 in byte order. Space, the 33rd shifted byte, becomes U+0120 `Ġ`, and newline becomes U+010A `Ċ`.

Q: Why does the regex attach the space to the start of the next word instead of making spaces separate tokens?
A: Almost every word in prose follows a space, so " the" as one token halves the number of tokens compared with " " plus "the". Keeping the space inside the chunk also lets BPE learn word tokens without letting merges glue words to punctuation. The GPT-2 paper says this exception "significantly improves the compression efficiency".

Q: You stream a model's output to a web page token by token and users see � next to emoji. What is happening and how do you fix it?
A: Byte-level tokens can end partway through a multi-byte UTF-8 character (an emoji is 4 bytes, and GPT-2 splits 😊 across two tokens), so decoding each token alone produces replacement characters. Accumulate bytes and only emit text up to the last complete character, or use an incremental UTF-8 decoder such as `codecs.getincrementaldecoder("utf-8")`.

Q: What is the size of GPT-2's vocabulary, and where does each part come from?
A: 50,257: 256 single-byte tokens, 50,000 tokens created by the merges in `vocab.bpe`, and one special `<|endoftext|>` token (id 50256), which ordinary text never produces.

## Lab

- Check `byte_alphabet()` against GPT-2's `bytes_to_unicode()`. Expected: identical dictionaries; 188 bytes kept, 68 shifted; space to `Ġ` (0x120), newline to `Ċ` (0x10a).
- Encode "Hi naïve 😊!!" with `gpt2_encode` and with `tiktoken.get_encoding("gpt2").encode`. Expected: [17250, 41492, 30325, 232, 3228] from both.
- Encode "it's", "IT'S", "hello", " hello" and "1234567" with GPT-2 and cl100k_base in tiktoken. Expected with GPT-2: [270, 338], [2043, 6, 50], [31373], [23748], and `123 45 67`; with cl100k_base "IT'S" is two tokens (`IT`, `'S`) and "1234567" is `123 456 7`.
- Write a stress test with 3,000 random strings over an alphabet of letters, digits, punctuation, tabs, newlines, accented letters, a Chinese character and an emoji. Expected: your ids equal tiktoken's GPT-2 ids for every string.

> [!know]
> You now know how byte-level BPE makes every string encodable, and how GPT-2's byte table and regex decide where tokens can and cannot form.

=== primer | How do WordPiece and Unigram differ from BPE, and which tokeniser quirks bite? | 17 min
goal: Implement WordPiece's greedy longest match and Unigram's Viterbi segmentation, compare them with BPE, and recognise the tokeniser pitfalls that are documented and reproducible
tag: tokens-wp-unigram | WordPiece longest match and Unigram Viterbi
link: Hugging Face LLM course: WordPiece tokenisation | https://huggingface.co/learn/llm-course/chapter6/6#training-algorithm | 10 min: the score used to pick merges (with the warning that Google never released its training code) and the longest-match tokenisation; chapter 6.7 does the same for Unigram
link: Google BERT source: tokenization.py | https://github.com/google-research/bert/blob/master/tokenization.py | 5 min: WordpieceTokenizer.tokenize, about 40 lines: greedy longest-match-first, the ## prefix, and [UNK] for the whole word

> [!key]
> **WordPiece** (BERT) stores only a vocabulary. To encode a word it takes the **longest vocabulary prefix**, then the longest continuation piece (written with a `##` prefix) from where that ended, and so on; if any step fails, the whole word becomes `[UNK]`. **Unigram** (Kudo 2018, used through SentencePiece) gives every piece a probability and picks the segmentation with the highest total log-probability by **dynamic programming** (Viterbi). It trains top-down: start from a large vocabulary and repeatedly drop the pieces whose removal hurts the likelihood least. BPE, by contrast, stores ordered merges and replays them.

## Intuition

Three ways to read an unfamiliar compound word. BPE replays the shortcuts it learnt, oldest first. WordPiece reads left to right and grabs the longest chunk it recognises each time, like a hurried reader. Unigram weighs every possible way to cut the word and keeps the cut whose pieces are most probable together, like a careful one. The hurried reader can be fooled: grabbing "lowe" first leaves "st", while "low" + "est" would have been the better reading.

## How it works

### WordPiece encoding: greedy longest match

```text
start = 0
while start < len(word):
    try end = len(word), len(word) - 1, ... until word[start:end] (with "##" if start > 0) is in the vocabulary
    no piece found -> the whole word is [UNK]
    emit the piece; start = end
```

BERT's version also gives up with `[UNK]` on words longer than 200 characters. Its docstring example: "unaffable" becomes `un ##aff ##able`.

### WordPiece training

Like BPE it merges pairs bottom-up, but Hugging Face's reconstruction (Google never released the training code) scores a pair as count(ab) / (count(a) × count(b)), preferring pairs whose parts are rare on their own over pairs that are merely frequent.

### Unigram: a probability per piece

A segmentation's probability is the product of its pieces' probabilities, so its log-probability is a sum. The best segmentation of a word is a shortest-path problem on its prefixes:

```text
best[0] = 0
best[i] = max over j < i of  best[j] + log p(word[j:i])   for pieces in the vocabulary
```

Keep a back-pointer to the j that won; walk back from the end to read the pieces. That is the Viterbi algorithm. Correctness is the usual dynamic-programming argument: the best segmentation of `word[:i]` ends with some last piece `word[j:i]`, and what comes before it must be a best segmentation of `word[:j]`, or swapping in a better one would improve the whole.

### Unigram training

Kudo's loop (§3.2): build a large seed vocabulary (for example frequent substrings); then repeat: fit the piece probabilities with EM, compute for each piece how much the corpus likelihood would drop without it, and keep the best 80% (η = 80 in the paper), always keeping single characters so every word stays encodable, until the vocabulary is small enough. Because it is a probability model, it can also **sample** segmentations during training (subword regularisation), which the paper uses as data augmentation.

### SentencePiece

SentencePiece treats the input as a raw character stream, writes spaces as `▁` (U+2581) so that decoding is exact (lossless tokenisation), and can train either BPE or Unigram models. The Hugging Face course lists ALBERT, T5, mBART, Big Bird and XLNet as models using Unigram through SentencePiece, and BERT, DistilBERT, MobileBERT, Funnel Transformers and MPNET as WordPiece models.

### Comparison

| | BPE | WordPiece | Unigram |
|---|---|---|---|
| Training | bottom-up: merge the most frequent pair | bottom-up: merge the best-scoring pair | top-down: prune the least useful pieces |
| Stored | ordered merges (ranks) | vocabulary | vocabulary with log-probabilities |
| Encoding | replay merges by rank | greedy longest match | Viterbi over prefixes |
| Can sample segmentations | no (BPE-dropout is a separate trick) | no | yes |

### Quirks you can verify

All of these come from running tiktoken or reading the cited source:

- **Glitch tokens.** " SolidGoldMagikarp" is a single GPT-2 token (id 43453), yet cl100k_base splits it into five pieces. Land and Bartolo (2024) call such tokens under-trained: present in the vocabulary but nearly or entirely absent from the model's training data, so the model behaves unpredictably on them. They found them across many models and detect them from the embedding weights plus test prompts.
- **Numbers.** GPT-2 splits "1000000" as `1 000000` and "2024" as `20 24`; cl100k_base gives `100 000 0` and `202 4`.
- **Whitespace.** A word with and without a leading space are different tokens; a trailing space is a token of its own.
- **One unknown character spoils a WordPiece word.** If any piece is missing, BERT emits a single `[UNK]` for the whole word.

## Cost

For a word of n characters and a longest piece of L characters:

- WordPiece, as written: at each start it tries ends from the far end down, so O(n) substring lookups per piece and O(n²) per word in the worst case; capping candidate length at L gives O(n × L). BERT bounds n at 200.
- Viterbi: for each end i, try the L possible starts: O(n × L) dictionary lookups and O(n) memory.
- Unigram training: each EM round runs a forward-backward pass over every word, and pruning needs the likelihood loss for every piece; the whole loop is far heavier than BPE training, which is why tools prune 20% at a time instead of one piece at a time.

## When to use it

Use WordPiece when you must match a BERT-family model; its greedy encoder is simple and fast. Use Unigram when you want principled segmentation and the option to sample segmentations as augmentation, usually through SentencePiece, which also handles languages written without spaces. Use byte-level BPE when nothing may ever be unknown. And whatever you build or use, count and split with the target model's own tokeniser: the three algorithms, and even two BPE vocabularies, cut the same text differently.

## Worked trace

A toy Unigram vocabulary with probabilities: l .04, o .04, w .04, e .08, s .06, t .06, lo .05, low .10, lowe .06, we .04, es .05, st .06, est .09, west .03. Segment "lowest"; log-probabilities are natural logarithms.

```steps
best[1] for 'l': only the piece 'l', log 0.04
    i=1  best -3.219  via 'l' from 0
---
best[2] and best[3]: the single pieces 'lo' and 'low' beat any split of them
    i=2  best -2.996  via 'lo' from 0
    i=3  {{best -2.303  via 'low' from 0}}
---
best[4] for 'lowe': 'lowe' alone (-2.813) beats 'low' + 'e' (-2.303 - 2.526 = -4.829)
    i=4  best -2.813  via 'lowe' from 0
---
best[5] for 'lowes': 'low' + 'es' (-2.303 - 2.996 = -5.298) beats 'lowe' + 's' (-5.627)
    i=5  best -5.298  via 'es' from 3
---
best[6] for 'lowest': 'low' + 'est' = -2.303 - 2.408 = -4.711 beats 'lowe' + 'st' (-5.627) and 'lo' + 'west' (-6.502)
    i=6  {{best -4.711  via 'est' from 3}}
---
Walk the back-pointers 6 -> 3 -> 0. Greedy longest match on a WordPiece vocabulary with the same pieces takes 'lowe' first
    Viterbi   {{low  est}}     log P -4.711   (P = 0.009)
    greedy    lowe ##st        the same pieces score -5.627
```

## Template

```python
import math


def wordpiece(word, vocab, unk="[UNK]", max_chars=200):
    """Greedy longest-match-first, as in BERT: continuation pieces carry a ## prefix."""
    if len(word) > max_chars:
        return [unk]
    pieces, start = [], 0
    while start < len(word):
        end = len(word)
        while end > start:
            piece = word[start:end] if start == 0 else "##" + word[start:end]
            if piece in vocab:
                break
            end -= 1
        if end == start:
            return [unk]                     # one missing piece spoils the whole word
        pieces.append(piece)
        start = end
    return pieces


def unigram_viterbi(word, logp):
    """Most probable segmentation under a unigram model: best[i] covers word[:i]."""
    n = len(word)
    best = [0.0] + [-math.inf] * n
    back = [0] * (n + 1)
    longest = max(map(len, logp))
    for i in range(1, n + 1):
        for j in range(max(0, i - longest), i):
            piece = word[j:i]
            if piece in logp and best[j] + logp[piece] > best[i]:
                best[i], back[i] = best[j] + logp[piece], j
    if best[n] == -math.inf:
        return None, -math.inf
    pieces, i = [], n
    while i > 0:
        pieces.append(word[back[i]:i])
        i = back[i]
    return pieces[::-1], best[n]
```

Tested against brute force (every possible segmentation for words of up to 10 characters) and against Hugging Face `tokenizers`: its `Unigram` model gave the same segmentations in 5,000 random cases and its `WordPiece` model the same pieces in 4,000.

## Pitfalls

- **Greedy is not optimal.** Longest match can commit to a long first piece that forces poor pieces later, as "lowe ##st" shows.
- **Forgetting the `##` prefix.** Continuation pieces live in a separate namespace; looking up "st" instead of "##st" mid-word gives wrong splits.
- **Ties in Viterbi.** Two segmentations can have exactly the same score (the same pieces in another order); which one wins depends on the comparison (`>` versus `>=`), so pick one and test it.
- **Log of zero.** Pieces with probability 0 must be absent, not log(0); `-inf` arithmetic hides bugs.
- **Trusting folklore about glitch tokens.** Verify with the tokeniser itself (is the string one token?) and cite measurements, as the Magikarp paper does; many claims online are anecdotes.

## Check yourself

Q: With the vocabulary {un, ##aff, ##able, aff, able, ##a, ##ff, ##ab, ##le, u, ##n}, what does `wordpiece` return for "unaffable" and for "unaffablx"?
A: "unaffable": from 0 the longest piece in the vocabulary is "un"; from 2 it is "##aff"; from 5 it is "##able", giving `un ##aff ##able`. "unaffablx": after `un ##aff`, no piece starting with "##a" covers the rest ("##ablx", "##abl" and so on are missing, and "##ab" is found but then "##lx" and "##l" are not), so the whole word becomes `[UNK]`.

Q: Why does Viterbi find the most probable segmentation without trying all 2^(n−1) of them?
A: The best segmentation of the first i characters ends with some last piece `word[j:i]`, and the part before it must itself be a best segmentation of the first j characters (otherwise replacing it with a better one would improve the total). So `best[i]` only needs `best[j]` for the L values of j where a piece fits, giving O(n × L) work instead of exponential.

Q: A team fine-tunes a BERT model and, to save time, tokenises its data with a GPT-2 BPE tokeniser instead of BERT's WordPiece. What goes wrong?
A: The model's embedding rows correspond to BERT's WordPiece vocabulary ids. GPT-2's ids index different strings (and go beyond BERT's vocabulary size), so the model receives nonsense or out-of-range ids. Always use the model's own tokeniser.

Q: Someone claims "token X is a glitch token in model M". How would you check the claim with the tools from this module?
A: First check that X really is a single token in M's tokeniser (encode it and count). Then follow Land and Bartolo: look for under-training signs in the model's embedding weights for that id and test prompts that ask the model to repeat the token; a model that cannot reproduce it confirms the claim. Without the tokeniser check, the string may not even be one token.

## Lab

- Run `unigram_viterbi("lowest", logp)` with the trace's probabilities. Expected: `['low', 'est']` with log-probability −4.711; `wordpiece("lowest", {"l", "lo", "low", "lowe", "##w", "##e", "##s", "##t", "##st", "##est", "##we", "##o"})` returns `['lowe', '##st']`.
- Compare your functions with Hugging Face `tokenizers.models.Unigram` and `WordPiece` on random vocabularies over a small alphabet. Expected: identical results (compare scores rather than pieces for Unigram if two segmentations tie).
- With tiktoken, encode " SolidGoldMagikarp", "1000000" and "2024" with the gpt2 and cl100k_base encodings. Expected: 1 token (id 43453) against 5; `1 000000` against `100 000 0`; `20 24` against `202 4`.

> [!know]
> You now know how WordPiece and Unigram segment text, how they differ from BPE, and how to check tokeniser quirks instead of trusting folklore.

=== lab | Train a byte-level BPE on Pride and Prejudice: naive versus heap | 45 min
goal: Train byte-level BPE on a public-domain novel with both trainers, confirm identical merges, measure the speed-up, and see how compression grows with the number of merges
link: Project Gutenberg: Pride and Prejudice, plain text | https://www.gutenberg.org/cache/epub/1342/pg1342.txt | About 5 min: The plain UTF-8 text of eBook 1342, public domain in the USA; strip the licence header and footer as in step 1

You will combine every card of this module: pre-tokenisation, the byte alphabet, both trainers and the heap encoder.

## Steps

1. Download the text and keep only the book between the Gutenberg markers:

```python
import re
import time
from collections import Counter

text = open("pg1342.txt", encoding="utf-8").read()
start = text.index("\n", text.index("*** START OF")) + 1
text = text[start:text.index("*** END OF")]
```

2. Pre-tokenise with a standard-library approximation of GPT-2's regex (`[^\W\d_]` stands for letters, `\d` for digits), map each chunk's bytes through `byte_alphabet()` from the byte-level card, and count distinct chunks:

```python
SPLIT = re.compile(r"'s|'t|'re|'ve|'m|'ll|'d| ?[^\W\d_]+| ?\d+| ?(?:[^\s\w]|_)+|\s+(?!\S)|\s+")
to_char = byte_alphabet()
counts = Counter(SPLIT.findall(text))
words = {tuple(to_char[b] for b in w.encode("utf-8")): c for w, c in counts.items()}
print(len(text.encode("utf-8")), sum(words.values()), len(words), sum(len(w) for w in words))
```

3. Time `train_naive` and `train_fast` for 100, 300 and 1,000 merges with `time.perf_counter()`, and assert that the merge lists are identical.
4. Time `train_fast` alone for 3,000 and 10,000 merges.
5. Print the first 12 merges and merges 990 to 999 (join each pair into one string).
6. For 0, 100, 300, 1,000 and 3,000 merges, build `ranks` and count the tokens of the whole book with `encode_heap` applied to every distinct chunk times its count. Report bytes per token.
7. Write three sentences: why the naive trainer slows down linearly with the number of merges, what dominates the heap trainer's time, and why compression gains shrink as merges grow.

## What you should see

Measured on the file downloaded on 1 November 2026 (772,386 bytes, SHA-256 starting 3f6bb9d6); Gutenberg occasionally regenerates files, so counts can drift slightly.

- Step 2: 737,950 bytes of book text, 166,681 chunks, 9,694 distinct chunks, 78,072 symbols in the distinct-chunk table.
- Steps 3 and 4 (one core of a shared Linux server; your times will differ, the ratios should not by much):

| Merges | Naive | Heap |
|---|---|---|
| 100 | 9.6 s | 0.31 s |
| 300 | 25.4 s | 0.39 s |
| 1,000 | 78.4 s | 0.49 s |
| 3,000 | | 0.58 s |
| 10,000 | | 1.15 s |

- The merge lists are identical for 100, 300 and 1,000 merges.
- Step 5: the first merges are `he`, `Ġt`, `Ġa`, `in`, `Ġw`, `Ġs`, `re`, `Ġo`, `ha`, `ĠĠ`, `er`, `ou`; by merges 990 to 999 whole words appear: `ĠGeor`, `ĠIf`, `Ġeach`, `Ġgl`, `Ġgiven`, `Ġhon`, `Ġjo`, `Ġmis`, `Ġmarriage`, `Ġpassed`.
- Step 6:

| Merges | Tokens | Bytes per token |
|---|---|---|
| 0 | 737,950 | 1.00 |
| 100 | 422,326 | 1.75 |
| 300 | 326,128 | 2.26 |
| 1,000 | 243,718 | 3.03 |
| 3,000 | 195,433 | 3.78 |

- The naive trainer costs a near-constant 78 ms or so per merge because it rescans all 78,072 symbols every time. The heap trainer spends about 0.3 s building its index, after which each merge touches only that pair's occurrences, and later merges are rarer pairs. Compression has diminishing returns because each new merge covers a rarer pair: the first 100 merges cut the token count by 43%, the next 2,900 by another 54% of what remained.
