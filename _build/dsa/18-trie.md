---
key: trie
name: Tries
stage: hier
summary: Prefix trees for prefix queries, autocomplete, searching many words at once, wildcards, maximum XOR and longest-prefix match, and the honest comparison with a hash set or a sorted list.
why: A trie turns "which stored keys start with this?" into a walk of one step per character, no matter how many keys you store. That single property powers search-box completion, dictionary scans of grids and strings, wildcard lookups, bitwise maximum-XOR tricks and the longest-prefix match that every IP router performs per packet. It is also a lesson in engineering trade-offs: a naive Python trie is several times larger than a set or a sorted list of the same words, so production systems compress it (radix trees, LC-tries, FSTs) or pick a different structure. After this module you can build one from a blank file, bend it to new problems, and say when not to.
outcomes:
- Implement a trie with insert, search, starts-with and delete from memory, and explain why each costs O(length of the key)
- Keep counts, sums or best-k lists on nodes to answer prefix aggregates and top-k completions without scanning
- Choose between a trie, a set of prefixes, a sorted list with bisect and a radix tree from the operation mix and a memory budget, using measured numbers
- Search a whole dictionary inside a letter grid or a string in one pass by walking the trie, pruning finished branches
- Handle '.' wildcards, shortest-root replacement and maximum XOR with trie walks
- Explain longest-prefix match in IP routing and where Linux, Redis and HTTP routers use compressed tries
cues:
- Many stored words or keys share prefixes, and the questions are about prefixes: "starts with", "autocomplete", "shortest root", "longest common prefix"
- You must find many dictionary words inside one grid or one string, and searching for each word separately would repeat the same work
- A query character such as '.' matches any letter at one position
- Maximise XOR, or compare numbers bit by bit from the highest bit down
- "The most specific matching rule wins": routing tables, path routers, configuration overrides
traps:
- Forgetting the end-of-word flag, so search("app") returns True after inserting only "apple"
- Building a dict-of-dicts trie for hundreds of thousands of keys in Python when a set of prefixes or a sorted list would use a third of the memory
- In grid word search, not restoring a cell after the DFS, or reporting the same word twice when two paths spell it
- Iterating bits from low to high in a binary trie, or using fewer bits than the largest value needs
- Relying on dict order for "lexicographic" output: children come out in insertion order unless you sort them
systems:
- Linux IPv4 routing (fib_trie) stores the forwarding table as a level- and path-compressed (LC) trie and backtracks through it to find the longest matching prefix for each packet
- Redis ships its own radix tree, rax: a stream is a radix tree of listpacks keyed by entry ID, and the client-side caching tracking table maps keys and broadcast prefixes to clients with rax trees
- Redis Search keeps autocomplete suggestions (FT.SUGADD, FT.SUGGET) in a trie-based structure with scores and an optional fuzzy prefix match
- Go's httprouter matches URL paths with a compact radix tree, and Ethereum stores its world state in a Merkle Patricia trie
further:
- Article · 10 min | Wikipedia: Trie, bitwise and compressed tries | https://en.wikipedia.org/wiki/Trie#Bitwise_tries
- Docs · 10 min | Linux kernel: LC-trie implementation notes, main lookup mechanism | https://docs.kernel.org/networking/fib_trie.html#main-lookup-mechanism
- Article · 30 min | Andrew Gallant: Index 1,600,000,000 keys with automata and Rust, from 'Trie construction' through the FST sections (sharing suffixes as well as prefixes) | https://burntsushi.net/transducers/#trie-construction
- Docs · 10 min | Ethereum: Merkle Patricia trie | https://ethereum.org/developers/docs/data-structures-and-encoding/patricia-merkle-trie/
bank: trie
---

=== primer | How does a trie look up a word or a prefix in time proportional to its length? | 15 min
goal: Build a trie with insert, search, starts-with and delete from a blank file, and explain why each costs O(L) whatever the number of stored words
tag: trie-walk | Trie insert and prefix walk
link: Wikipedia: Trie, Operations | https://en.wikipedia.org/wiki/Trie#Operations | 10 min: the 'Searching', 'Insertion' and 'Deletion' subsections, a second description of the same three walks with the dead-node clean-up on delete
practice: 208, 3043

> [!key]
> A **trie** (prefix tree) stores strings as paths from a root, one character per edge, so words with a common prefix share the nodes of that prefix. Every operation is a **walk**: follow one child per character, and a flag on the last node says whether a whole word ends there. Lookup costs O(L) for a key of length L, independent of how many words are stored, and "does any word start with p?" is the same walk without checking the flag.

## Intuition

Think of a paper dictionary's thumb tabs taken to the extreme. To find "cart" you open the C section, then the CA pages, then CAR, then CART. Each letter narrows the search to a smaller section, and all the words in a section share the letters you have followed so far. A trie makes each section a node. The section for "ca" is a single node, and "car", "cart" and "cat" all hang below it.

That sharing is why prefix questions are cheap. "Is there any word starting with ca?" is answered the moment you reach the node for "ca"; you never look at the words themselves.

## How it works

Each node holds a map from character to child and a boolean **is_word** that is True when a stored word ends exactly at this node. The root represents the empty prefix.

- **Insert**: walk from the root, creating any missing child, and set is_word on the last node.
- **Search**: walk; if a child is missing, the word is absent; at the end, return is_word.
- **Starts with**: walk; if the walk survives the whole prefix, some word has that prefix (every node lies on the path of at least one stored word).
- **Delete**: walk to the word's node and clear is_word, then walk back up removing nodes that now have no children and are not word ends, so the invariant "every node leads to a word" survives.

```text
words: car, cart, cat, do, dog          (* = a word ends here)

root
 +- c
 |   +- a
 |       +- r*
 |       |   +- t*
 |       +- t*
 +- d
     +- o*
         +- g*
```

Fifteen characters are stored in eight nodes plus the root, because "car" and "cart" share three nodes and "ca" is shared by three words.

**The invariant**: for every non-empty string s, the node reached by walking s from the root exists if and only if s is a prefix of some stored word, and its is_word flag is True if and only if s itself is stored. Insert creates exactly the nodes for the new prefixes; delete removes exactly the nodes that stop being prefixes of anything.

## Cost

Count the work in one operation on a key of length L:

- The walk takes at most L steps, one per character.
- Each step is one lookup in a child map. With a Python dict that is expected O(1); with a fixed array of 26 slots it is O(1) worst case.
- Delete adds a walk back up of at most L steps.

So insert, search, starts-with and delete are **O(L) time**, and n, the number of stored words, appears nowhere. Building the trie for words with total length S costs O(S).

Space is at most one node per inserted character, so **O(S) nodes**, and fewer when prefixes are shared. The constant is what bites in Python: each node is an object plus a dict, roughly 200 bytes. Measured on the 100,000 most common English words (711,708 characters): 233,569 nodes and about 46 MB, against about 4 MB for a set of the same words (plus the 4.8 MB of strings both need). The card "When should you use a trie rather than a hash set or a sorted list?" weighs that trade-off properly.

## When to use it

Reach for a trie when the questions are about **prefixes** or when you consume input **one character at a time** and want to know, after each character, whether you are still on the path of some word: typing in a search box, scanning a string or a grid against a dictionary, routing tables.

| Need | Best tool | Why |
|---|---|---|
| Exact membership only | `set` | O(L) expected, smaller, built in |
| Prefix queries on mostly static data | sorted list + `bisect` | Compact; prefix range in O(L log n) |
| Prefix queries with frequent inserts, or char-by-char walks | trie | O(L) per step and per insert |
| Many keys with long shared prefixes, tight memory | radix tree | Collapses one-child chains |

If you only ever ask "is this exact word stored?", a trie is slower and bigger than a set. If you ask "what starts with this?" thousands of times while words keep arriving, it shines.

## Worked trace

Insert "cat" into a trie that already holds car, cart, do and dog, then run three queries. The highlighted nodes are the path being walked.

```steps
Insert "cat": start at the root and follow "c", which already exists
    root
     +- {{c}}
     |   +- a
     |       +- r*
     |           +- t*
     +- d
         +- o*
             +- g*
---
Follow "a": it exists too, so "ca" costs no new memory
    root
     +- {{c}}
     |   +- {{a}}
     |       +- r*
     |           +- t*
     +- d
         +- o*
             +- g*
---
No child "t" under "ca": create it and mark it as a word end
    root
     +- {{c}}
     |   +- {{a}}
     |       +- r*
     |       |   +- t*
     |       +- {{t*}}
     +- d
         +- o*
             +- g*
---
search("cart"): c, a, r, t all exist and the last node is marked, so True
    root
     +- {{c}}
     |   +- {{a}}
     |       +- {{r*}}
     |       |   +- {{t*}}
     |       +- t*
     +- d
---
search("ca"): the path exists but "a" is not marked, so False; starts_with("ca") is True
    root
     +- {{c}}
     |   +- {{a}}
     |       +- r*
     |       +- t*
     +- d
---
search("cab"): after c and a there is no child "b", so stop: False after three steps
    root
     +- {{c}}
     |   +- {{a}}  (children: r, t; no b)
     +- d
```

## Template

```python
class TrieNode:
    __slots__ = ("children", "is_word")

    def __init__(self):
        self.children = {}        # character -> TrieNode
        self.is_word = False      # a stored word ends exactly here


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            nxt = node.children.get(ch)
            if nxt is None:
                nxt = node.children[ch] = TrieNode()
            node = nxt
        node.is_word = True

    def _walk(self, s):
        """The node reached by following s from the root, or None if the path breaks."""
        node = self.root
        for ch in s:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def search(self, word):
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix):
        return self._walk(prefix) is not None

    def delete(self, word):
        """Remove word if stored; prune nodes that no longer lead to any word."""
        path = [self.root]
        for ch in word:
            node = path[-1].children.get(ch)
            if node is None:
                return False
            path.append(node)
        if not path[-1].is_word:
            return False
        path[-1].is_word = False
        for i in range(len(word), 0, -1):          # climb while the node is dead
            if path[i].is_word or path[i].children:
                break
            del path[i - 1].children[word[i - 1]]
        return True
```

Everything is iterative, so a 100,000-character key cannot hit Python's recursion limit. `__slots__` saves the per-object `__dict__`, which matters when you have hundreds of thousands of nodes. In C++ or Java the usual node is `Node* child[26]` plus a bool: worst-case O(1) steps but 26 pointers (208 bytes on 64-bit) per node even when most are empty.

## Pitfalls

- **No end flag.** Without is_word, inserting "apple" makes search("app") True. The walk proves a prefix exists, not a word.
- **Creating nodes on search.** `node.children.setdefault(ch, TrieNode())` inside search adds junk nodes for every miss (and builds a throwaway node on every step even in insert). Use `get` in walks.
- **Delete without pruning** leaves dead branches, so starts_with("appl") stays True after deleting "apple". Prune bottom-up, and stop at a node that is a word end or still has children.
- **The empty string.** Inserting "" marks the root, and starts_with("") is True even for an empty trie because the root always exists. Decide what both should mean before a test does it for you.
- **Case and alphabet.** "Apple" and "apple" are different paths. Normalise first (`casefold()`), and do not assume 26 letters unless the problem promises it.

## Check yourself

Q: You insert "to", "tea", "ten" and "inn" into an empty trie. How many nodes does it have, counting the root? What do search("te") and starts_with("in") return?
A: Nine: the root, then t, o, e, a, n under "te", and i, n, n. "to", "tea" and "ten" share the t node and "tea" and "ten" share "te". search("te") is False because no word ends at the "te" node; starts_with("in") is True because the walk survives both letters.

Q: Why is search O(L) rather than O(L log n) or O(n), when a balanced search tree of the same n words needs O(L log n)?
A: The walk visits exactly one node per character and never compares the key with whole stored words. A search tree compares the key with about log n stored words, each comparison costing up to O(L). In the trie, n only affects how many nodes exist, not how many are visited.

Q: A colleague's search is `return self._walk(word) is not None`. Which test exposes the bug, and what is the fix?
A: Insert "apple" and search "app": the walk survives, so it wrongly returns True. The walk only proves "app" is a prefix. Return `node is not None and node.is_word`.

Q: You need only exact membership for a million words, loaded once. Trie or set?
A: A set. Lookup is O(L) expected for both (hashing reads the whole key), but the set is several times smaller and its lookup runs in C. The trie pays for prefix operations you do not need.

## Lab

- **208 Implement Trie (Prefix Tree)**: write the class from a blank file, without looking at the template. Expected: every operation O(L), O(total characters) space. Your own test: insert("tree"); search("tre") is False; starts_with("tre") is True; insert("tre"); search("tre") is True; search("trees") is False.
- **3043 Find the Length of the Longest Common Prefix**: insert every number of the first array as a digit string, then walk each number of the second array, counting how far the walk survives. Expected: O((n + m) * d) for d at most 9 digits; for arr1 = [5655359, 128] and arr2 = [56554, 1290, 7] the answer is 4 ("5655").

> [!know]
> You now know how to build a trie, walk it for words and prefixes in O(L), delete with pruning, and why n never appears in the cost.

=== primer | How do you count, rank and list the completions of a prefix? | 15 min
goal: Store counts and best-k lists on trie nodes so prefix counts and top-k completions cost O(prefix length + k), and enumerate completions in lexicographic order
tag: trie-agg | Aggregates on trie nodes
link: Redis docs: Autocomplete with Redis, Retrieve suggestions | https://redis.io/docs/latest/develop/ai/search-and-query/advanced-concepts/autocomplete/#retrieve-suggestions | 5 min: 'Add autocomplete suggestions' and 'Retrieve suggestions', a production trie-based API with scores, INCR updates and an optional fuzzy match, the same operations as this card
practice: 1268, 677, 2416

> [!key]
> Any question of the form "something about all words below this prefix" can be answered at the prefix node if every node keeps a summary of its subtree: a **count** of words passing through, a **sum** of their values, or the **best k** words. Update the summaries along the path on every insert (O(L) nodes), and a query becomes a walk to the prefix plus a read: O(P + k) instead of a scan of every completion.

## Intuition

A library shelf labelled "CA" could carry a sticky note: "312 books here; the three most borrowed are...". Whoever adds a book to the shelf updates the note, and a visitor reads it without touching a single book. A trie node is that shelf: everything below it shares its prefix, and the note is a field on the node.

## How it works

### Prefix counts and sums

Give each node a `count`. On insert, add one to every node on the path, root included. Then `count_prefix(p)` is the count at the node for p, or 0 if the walk breaks. A sum of values works the same way, and an overwrite becomes "add the difference (new value minus old value) along the path".

### Best-k completions, cached

Give each node a list `top` of at most K `(-freq, word)` pairs, best first. On insert of (word, freq), every node on the path gains a candidate: append, sort the K + 1 items, drop the worst. A query walks to the prefix node and returns its list. Sorting by `(-freq, word)` gives a deterministic order for ties.

This only works as written for **new** words or **increasing** frequencies. If a frequency goes down, a word may fall out of a node's list and the next best word was never kept there, so the node must be rebuilt from its children's lists (each child still holds its own best K). This stage's project goes further, with best-first search over subtree maxima.

### Listing every completion in order

Walk to the prefix node, then run a depth-first traversal of its subtree, visiting children in sorted order. Pre-order visits a word before its extensions ("car" before "cart"), which is exactly lexicographic order. With an explicit stack, push children in **reverse** sorted order so the smallest pops first.

## Cost

- Insert with counts: the walk is L steps and each node gets one increment, O(L).
- Insert with cached best-k: L + 1 nodes, each sorting K + 1 items, O(L * K log K); with K = 5 that is a small constant per character.
- count_prefix and cached top-k: walk P characters, then read: O(P), and O(P + K) to copy the answer.
- Listing all completions: O(P) to walk, then every node in the subtree once, plus sorting each node's children (at most the alphabet size) and building strings: proportional to the total length of the completions.
- Memory: counts add one int per node; cached lists add up to K tuples per node. In this module's lab, caching the top 5 on 233,569 nodes raised memory from about 48 MB to about 78 MB and turned 12 ms one-letter queries into microseconds.

## When to use it

| Workload | Approach |
|---|---|
| Prefix counts, sums, "how many words start with p" | Counter or sum on each node |
| Top-k for hot short prefixes, data changes rarely | Cached best-k per node |
| Top-k with constantly changing scores | Subtree maximum per node plus best-first search (this stage's project), or recompute lazily |
| Occasional queries, long prefixes, static data | Sorted list + `bisect` range, then `heapq.nsmallest` |
| All completions in order | Sorted DFS from the prefix node |

Do not cache when memory is tight and queries are rare: the lists cost K entries on every node, most of which are never asked.

## Worked trace

K = 2. Insert car:5, cat:9, cart:2 (word:frequency), then query. Each row is one node; changed cells are highlighted.

```steps
Insert car:5. Every node on the path c, ca, car gets count 1 and the candidate car:5
    node   count  top-2
    c      {{1}}      {{car:5}}
    ca     {{1}}      {{car:5}}
    car    {{1}}      {{car:5}}
---
Insert cat:9. c and ca now see two words; cat:9 sorts ahead of car:5. New node cat
    node   count  top-2
    c      {{2}}      {{cat:9 car:5}}
    ca     {{2}}      {{cat:9 car:5}}
    car    1      car:5
    cat    {{1}}      {{cat:9}}
---
Insert cart:2. Counts rise along c, ca, car; cart:2 loses to both entries at c and ca, so their lists stay
    node   count  top-2
    c      {{3}}      cat:9 car:5
    ca     {{3}}      cat:9 car:5
    car    {{2}}      {{car:5 cart:2}}
    cat    1      cat:9
    cart   {{1}}      {{cart:2}}
---
Query top("ca"): walk c, a and read the list: [cat, car]. count_prefix("ca") = 3. No subtree scan
    node   count  top-2
    c      3      cat:9 car:5
    {{ca}}     {{3}}      {{cat:9 car:5}}
---
List completions("ca") in order: DFS from ca with children sorted r < t gives car, cart, cat
    ca
     +- {{r}}*   -> car
     |   +- {{t}}*   -> cart
     +- {{t}}*   -> cat
```

## Template

```python
class Node:
    __slots__ = ("children", "count", "freq", "top")

    def __init__(self):
        self.children = {}
        self.count = 0         # stored words that pass through this node
        self.freq = None       # frequency if a word ends here
        self.top = []          # best K (-freq, word) pairs in this subtree, best first


class PrefixIndex:
    def __init__(self, k=5):
        self.k = k
        self.root = Node()

    def add(self, word, freq):
        """Insert a new word. (Re-adding a word would double-count: update with a delta instead.)"""
        node = self.root
        path = [node]
        for ch in word:
            nxt = node.children.get(ch)
            if nxt is None:
                nxt = node.children[ch] = Node()
            node = nxt
            path.append(node)
        node.freq = freq
        for n in path:
            n.count += 1
            n.top.append((-freq, word))
            n.top.sort()
            del n.top[self.k:]

    def _walk(self, prefix):
        node = self.root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def count_prefix(self, prefix):
        node = self._walk(prefix)
        return node.count if node else 0

    def top(self, prefix):
        node = self._walk(prefix)
        return [w for _, w in node.top] if node else []

    def completions(self, prefix):
        """Every stored word that starts with prefix, in lexicographic order."""
        start = self._walk(prefix)
        if start is None:
            return []
        out, stack = [], [(start, prefix)]
        while stack:
            node, text = stack.pop()
            if node.freq is not None:
                out.append(text)
            for ch in sorted(node.children, reverse=True):    # smallest child is popped first
                stack.append((node.children[ch], text + ch))
        return out
```

## Pitfalls

- **Re-inserting a word** with this template adds it twice to every count and list. For overwrites (Map Sum Pairs), look up the old value first and add the delta along the path.
- **Dict order is insertion order**, not alphabetical. Lexicographic output needs `sorted(node.children)`, or insert the words in sorted order and rely on that.
- **Ties.** Rank by `(-freq, word)`, not by `-freq` alone, or equal scores come back in an arbitrary order and tests become flaky.
- **Decreasing a score** silently corrupts cached lists; rebuild the affected nodes bottom-up from their children's lists.
- **Building strings** with `text + ch` copies the prefix each time: fine for words, wasteful for very long keys, where you can carry a list of characters and join only for output.

## Check yourself

Q: Continue the trace: insert dog:7. What are the root's count and top-2 list, and what does top("d") return?
A: The root has count 4 and top-2 [cat:9, dog:7], since dog:7 beats car:5. top("d") walks to the d node, whose list is [dog].

Q: Why can each node's best-k list be maintained by merging in only the inserted word, while a frequency decrease needs more work?
A: A node's list only ever contains words from its subtree. A new or improved word can only move up, so comparing it with the current K is enough: anything it pushes out was already worse than K others. When a score falls, the word may drop below the K + 1-th best word of the subtree, which the node discarded, so the node must recompute from its children's lists and its own word.

Q: Products change once a night; users type one or two letters and expect suggestions within a millisecond. Cache best-k per node, or collect and sort per query?
A: Cache. Updates are rare, so the extra build time and memory are paid once, and short prefixes are exactly where collecting is slowest (a one-letter prefix can cover tens of thousands of words, about 12 ms per query in this module's lab, against microseconds from the cache).

## Lab

- **1268 Search Suggestions System**: insert the products in sorted order and keep at most three words per node (or sort, then use bisect on the prefix range). Expected: O(S) build for S product characters plus O(1) per typed character after the walk; products ["bat", "bath", "batch", "bad", "cab"] with search word "bat" give [["bad", "bat", "batch"], ["bad", "bat", "batch"], ["bat", "batch", "bath"]].
- **677 Map Sum Pairs**: keep a running sum on every node and add the delta (new value minus old) along the path. Expected: O(L) per call; insert("ape", 3), sum("ap") = 3, insert("app", 2), sum("ap") = 5, insert("ape", 1), sum("ap") = 3.
- **2416 Sum of Prefix Scores of Strings**: count words through every node, then sum the counts along each word's path. Expected: O(total characters); words ["ab", "abc", "b"] give [4, 5, 1].

> [!know]
> You now know how to keep counts, sums and cached best-k lists on trie nodes, list completions in lexicographic order, and when caching pays for its memory.

=== primer | When should you use a trie rather than a hash set or a sorted list? | 14 min
goal: Choose between a set, a set of prefixes, a sorted list with bisect, a trie and a radix tree from the operations and memory budget, and build a radix tree that splits edges on insert
link: Wikipedia: Radix tree, Comparison to other data structures | https://en.wikipedia.org/wiki/Radix_tree#Comparison_to_other_data_structures | 5 min: radix trees against balanced trees (O(k) instead of O(log n) string comparisons) and hash tables (hashing is also O(k), and hash tables have no successor or predecessor queries)
practice: 3043

> [!key]
> A trie wins when you need **prefix operations or character-by-character walks with frequent inserts**. For exact membership a **set** is smaller and faster; for prefix queries over mostly static data a **sorted list with bisect** is compact and fast, because all words with a prefix form one contiguous range. A naive Python trie costs about 200 bytes per node; a **radix tree** collapses chains of single-child nodes into one edge labelled with a string, cutting the node count to at most twice the number of words.

## Intuition

Three ways to find every word beginning with "comp" in a dictionary: a pile of index cards in a shoebox (a set: great if you know the exact word, useless for "starts with"), a printed dictionary (a sorted list: open it at "comp", read until the words stop starting with "comp"), or a tree of tabbed folders (a trie). The printed dictionary is the most compact, and for a book that never changes it is hard to beat.

## How it works

### The sorted-list baseline

In sorted order, all words with prefix p sit in one block. `bisect_left(words, p)` finds its start. Its end is the first position whose word does not start with p, which is `bisect_left(words, p + "\U0010ffff")`: appending the largest code point makes a string that sorts after every word of the form p + something. Two binary searches, O(L log n), then slice or scan the block.

### The set-of-prefixes trick

If the only question is "is p a prefix of some word?" (or "what is the longest common prefix with anything stored?"), put **every prefix** of every word in a set. Lookups are O(L) expected and the code is one line. The set holds one string per distinct prefix, so memory grows with the number of trie nodes, but each entry is a compact string rather than a node object plus a dict.

### Radix trees

Most trie nodes for real words have exactly one child: "q", "qu", "qua", "quar"... A **radix tree** (compressed trie, Patricia tree) stores such a chain as one edge with a string label. Every node is then either a word end or a branch point with two or more children, which bounds the number of nodes by 2n - 1 (excluding the root) for n words. Insert walks edges; when the new word diverges in the **middle** of an edge, split that edge at the divergence point.

### Measured on 100,000 real words (CPython 3.12, tracemalloc)

| Structure | Extra memory | Notes |
|---|---|---|
| sorted list | 0.8 MB | references to the 4.8 MB of word strings |
| set of words | 4.2 MB | hash table only; no prefix queries |
| set of all prefixes | 15.4 MB | 233,568 prefix strings |
| radix tree | 27.6 MB | 115,733 nodes |
| dict-of-children trie | 46.1 MB | 233,569 nodes |

| Operation | set | sorted list + bisect | trie / radix tree |
|---|---|---|---|
| exact lookup | O(L) expected | O(L log n) | O(L) |
| any word with prefix p? | no (yes with a prefix set) | O(L log n) | O(L) |
| count or list words with prefix p | O(n L) scan | O(L log n) + output | O(L) + output, O(L) for counts |
| insert one word | O(L) amortised | O(n) (list shift) | O(L) |
| ordered iteration | sort first | free | sorted DFS |

## Cost

For the radix tree, a lookup still compares each character of the key once, so it is O(L), but it visits far fewer nodes and allocates far fewer objects. Insert is O(L) plus at most one edge split, which creates two nodes. Why at most 2n - 1 nodes: leaves are word ends, so there are at most n of them; every non-word internal node has at least two children, and a tree where every internal node branches has fewer internal nodes than leaves. Words that end at internal nodes are counted once each. On the measured list, compression halved the node count and cut memory by 40%.

In C, C++ or Rust the constants change completely: nodes can be packed arrays, and production radix trees (Redis rax, Linux's LC-trie) work hard on memory layout. In Python, object overhead dominates, which is why the sorted list and the prefix set do so well.

## When to use it

- **Static word list, prefix ranges, tight memory**: sorted list + bisect.
- **Only "is this a prefix?"**: set of prefixes, if memory allows.
- **Many inserts mixed with prefix queries, or walking input one character at a time** (grids, streams, typing): trie.
- **Long keys with long shared runs** (URLs, file paths, IP prefixes, IDs): radix tree.
- **Only exact lookups**: plain set or dict, always.

## Worked trace

Insert test, team, toast and to into an empty radix tree. Labels are strings; * marks a word end.

```steps
Insert "test": the root has no edge starting with t, so the whole word becomes one edge
    root
     +- {{"test"*}}
---
Insert "team": it shares "te" with the edge "test" and diverges inside it, so split the edge at "te"
    root
     +- {{"te"}}
         +- {{"st"*}}
         +- {{"am"*}}
---
Insert "toast": it shares only "t" with "te", so split again; the rest "oast" hangs off the new node
    root
     +- {{"t"}}
         +- {{"e"}}
         |   +- "st"*
         |   +- "am"*
         +- {{"oast"*}}
---
Insert "to": it ends inside the edge "oast", so split at "o" and mark the new node as a word end
    root
     +- "t"
         +- "e"
         |   +- "st"*
         |   +- "am"*
         +- {{"o"*}}
             +- {{"ast"*}}
---
Six nodes below the root, against ten in a plain trie (t, e, s, t, a, m, o, a, s, t)
    root
     +- t
         +- e
         |   +- st*
         |   +- am*
         +- o*
             +- ast*
```

## Template

```python
from bisect import bisect_left


def prefix_range(words, prefix):
    """words is sorted: words[lo:hi] are exactly the words that start with prefix."""
    lo = bisect_left(words, prefix)
    hi = bisect_left(words, prefix + "\U0010ffff")
    return lo, hi


class RadixNode:
    __slots__ = ("edges", "is_word")

    def __init__(self):
        self.edges = {}        # first character -> (label, child)
        self.is_word = False


class RadixTree:
    def __init__(self):
        self.root = RadixNode()

    def insert(self, word):
        node, i = self.root, 0
        while i < len(word):
            edge = node.edges.get(word[i])
            if edge is None:                          # nothing shares this letter: one new edge
                leaf = RadixNode()
                leaf.is_word = True
                node.edges[word[i]] = (word[i:], leaf)
                return
            label, child = edge
            k = 0                                     # common prefix of the label and the rest of word
            while k < len(label) and i + k < len(word) and label[k] == word[i + k]:
                k += 1
            if k < len(label):                        # diverges inside the edge: split it at k
                mid = RadixNode()
                mid.edges[label[k]] = (label[k:], child)
                node.edges[word[i]] = (label[:k], mid)
                child = mid
            node, i = child, i + k
        node.is_word = True

    def contains(self, word):
        node, i = self.root, 0
        while i < len(word):
            edge = node.edges.get(word[i])
            if edge is None or not word.startswith(edge[0], i):
                return False
            i += len(edge[0])
            node = edge[1]
        return node.is_word
```

## Pitfalls

- **Judging by Big-O alone.** All three structures answer prefix queries fast; in Python the deciding factor is often memory and constant factors. Measure with `tracemalloc` before choosing.
- **The bisect upper bound.** `p + "\U0010ffff"` is correct unless a word contains U+10FFFF right after the prefix (a non-character that real text does not use). An alternative is to increment the last character of p.
- **Inserting into a sorted list** is O(n) per insert because the list shifts; with many inserts, rebuild in batches or switch structure.
- **Radix splits.** The two classic bugs are forgetting to re-key the parent's edge to the shortened label, and forgetting that the word may end exactly at the split point (mark the middle node).
- **A prefix set duplicates memory per prefix**: a million 30-character keys produce up to 30 million prefixes. It suits short keys such as the digit strings of 3043.

## Check yourself

Q: Words are ["app", "apple", "apply", "bat"], sorted. What does `prefix_range(words, "app")` return, and which words does it cover?
A: (0, 3): bisect_left finds "app" at 0, and "app" + U+10FFFF sorts after "apply" but before "bat", so hi is 3. The block covers app, apple and apply.

Q: Why can a radix tree never have more than 2n - 1 nodes below the root for n words, while a plain trie can have as many nodes as there are characters?
A: Every radix node either ends a word (at most n such nodes) or branches into two or more children. A tree in which every non-word internal node branches has fewer such nodes than it has leaves, and leaves are word ends, so the total stays below 2n. A plain trie keeps one node per character of every unshared suffix, so a single 1,000-character word costs 1,000 nodes.

Q: An autocomplete box serves 2 million product names that change once a day, from a Python service with a 1 GB memory limit. Which structure?
A: A sorted list with bisect (or a sorted list plus a small cache for the hottest one- and two-letter prefixes). At about 200 bytes per node, a dict trie of 2 million names would need several gigabytes, while the sorted list costs 8 bytes per name on top of the strings, and daily rebuilds are cheap.

## Lab

- **3043 Find the Length of the Longest Common Prefix**, a second time: replace your trie with a set of every prefix of every number in the first array, then for each number in the second array try its prefixes from longest to shortest. Expected: the same answers as your trie (4 for arr1 = [5655359, 128], arr2 = [56554, 1290, 7]), O((n + m) * d) time, simpler code; the set holds at most 9 strings per number.
- Exercise: insert ["slow", "slower", "slowly", "snow", "snowy"] into the template's RadixTree and count its nodes below the root. Expected: 6 (s, then low* and now*, then er*, ly* and y*), against 12 nodes in a plain trie; "slow" and "snow" end at internal nodes.

> [!know]
> You now know how to pick between a set, a prefix set, a sorted list, a trie and a radix tree from the operations and a memory budget, and how a radix tree splits edges.

=== lab | Autocomplete: trie or sorted list? | 45 min
goal: Build three top-5 autocomplete indexes over 100,000 real words, prove they agree with a brute-force oracle, and measure memory and latency by prefix length
link: Python docs: tracemalloc | https://docs.python.org/3/library/tracemalloc.html#display-the-top-10 | 5 min: 'Display the top 10' and the get_traced_memory() reference, which is how the lab measures each index's memory

You will index the 100,000 most frequent English words with their counts in three ways and answer "the five most frequent words starting with this prefix": a sorted list with bisect, a trie that collects the whole subtree per query, and a trie that caches the best five at every node. Then you will measure what each costs. Keep it focused on these three: this stage's project builds the full service (radix tree, best-first ranking, HTTP endpoint).

## Setup

- Python 3.10 or newer; no packages needed.
- Download Peter Norvig's word counts, [count_1w.txt](https://norvig.com/ngrams/count_1w.txt) (333,333 lines of `word<TAB>count`, about 5 MB), into the folder where you run the script.

## Steps

1. Save this as `autocomplete_lab.py`. The oracle is the brute force from the foundations stage: it scans every word, so it is slow but obviously right, and every design must match it exactly (ties broken by the word).

```python
"""Autocomplete lab: top-5 completions by frequency from a sorted list, a trie, and a trie with cached answers."""
import bisect
import heapq
import random
import statistics
import sys
import time
import tracemalloc

K = 5


def load(path="count_1w.txt", n=100_000):
    """The n most frequent words as (word, count) pairs."""
    pairs = []
    with open(path) as f:
        for line in f:
            word, count = line.split("\t")
            pairs.append((word, int(count)))
            if len(pairs) == n:
                break
    return pairs


def oracle(pairs, prefix, k=K):
    """Brute force: scan everything. Ties broken by the word, so every design must agree exactly."""
    return [w for _, w in sorted((-c, w) for w, c in pairs if w.startswith(prefix))[:k]]


class SortedIndex:
    def __init__(self, pairs):
        pairs = sorted(pairs)
        self.words = [w for w, _ in pairs]
        self.counts = [c for _, c in pairs]

    def top(self, prefix, k=K):
        lo = bisect.bisect_left(self.words, prefix)
        hi = bisect.bisect_left(self.words, prefix + "\U0010ffff")   # just past the last word with this prefix
        best = heapq.nsmallest(k, ((-self.counts[i], self.words[i]) for i in range(lo, hi)))
        return [w for _, w in best]


class Node:
    __slots__ = ("children", "count", "top")

    def __init__(self):
        self.children = {}
        self.count = 0          # frequency if a word ends here, else 0
        self.top = None         # cached best k (only in CachedTrie)


class TrieIndex:
    """Walk to the prefix node, collect its whole subtree, keep the best k."""

    def __init__(self, pairs):
        self.root = Node()
        for word, count in pairs:
            node = self.root
            for ch in word:
                nxt = node.children.get(ch)
                if nxt is None:
                    nxt = node.children[ch] = Node()
                node = nxt
            node.count = count

    def walk(self, prefix):
        node = self.root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def top(self, prefix, k=K):
        start = self.walk(prefix)
        if start is None:
            return []
        hits, stack = [], [(start, prefix)]
        while stack:
            node, text = stack.pop()
            if node.count:
                hits.append((-node.count, text))
            for ch, child in node.children.items():
                stack.append((child, text + ch))
        return [w for _, w in heapq.nsmallest(k, hits)]


class CachedTrie(TrieIndex):
    """Every node stores its subtree's best k, so a query is a walk plus a copy."""

    def __init__(self, pairs):
        super().__init__(pairs)
        order, stack = [], [(self.root, "")]
        while stack:                                  # pre-order; reversed, children come before parents
            node, text = stack.pop()
            order.append((node, text))
            for ch, child in node.children.items():
                stack.append((child, text + ch))
        for node, text in reversed(order):
            cands = [(-node.count, text)] if node.count else []
            for child in node.children.values():
                cands.extend(child.top)
            node.top = heapq.nsmallest(K, cands)

    def top(self, prefix, k=K):
        node = self.walk(prefix)
        return [] if node is None else [w for _, w in node.top[:k]]


def make_queries(pairs, n, seed=1):
    """Prefixes of words drawn in proportion to frequency, cut at random lengths, like real typing."""
    rng = random.Random(seed)
    words = rng.choices([w for w, _ in pairs], weights=[c for _, c in pairs], k=n)
    return [w[:rng.randint(1, len(w))] for w in words]


def built(cls, pairs):
    t = time.perf_counter()
    index = cls(pairs)
    secs = time.perf_counter() - t
    tracemalloc.start()                      # build again under tracemalloc (it slows allocation down)
    again = cls(pairs)
    mb = tracemalloc.get_traced_memory()[0] / 1e6
    del again
    tracemalloc.stop()
    return index, secs, mb


def main():
    pairs = load()
    print(f"the word strings themselves: {sum(sys.getsizeof(w) for w, _ in pairs) / 1e6:.1f} MB")
    designs = {}
    for cls in (SortedIndex, TrieIndex, CachedTrie):
        designs[cls.__name__], secs, mb = built(cls, pairs)
        print(f"{cls.__name__:12} build {secs:5.2f} s   memory {mb:6.1f} MB")

    queries = make_queries(pairs, 2_000)
    for q in queries[:300] + ["zzzzq", "", "the"]:          # correctness first: all agree with the oracle
        want = oracle(pairs, q)
        for name, index in designs.items():
            assert index.top(q) == want, (name, q)
    print("all designs agree with the oracle")

    by_len = {}
    for q in queries:
        by_len.setdefault(min(len(q), 4), []).append(q)
    for length in sorted(by_len):
        qs = by_len[length][:300]
        row = []
        for name, index in designs.items():
            times = []
            for q in qs:
                t = time.perf_counter()
                index.top(q)
                times.append((time.perf_counter() - t) * 1000)
            times.sort()
            row.append(f"{name} p50 {statistics.median(times):7.3f} p99 {times[int(0.99 * len(times))]:7.3f}")
        print(f"prefix length {length}{'+' if length == 4 else ' '} ({len(qs)} queries, ms): " + " | ".join(row))
    trie = designs["TrieIndex"]
    nodes, stack = 0, [trie.root]
    while stack:
        node = stack.pop()
        nodes += 1
        stack.extend(node.children.values())
    print(f"trie nodes: {nodes:,} for {len(pairs):,} words ({sum(len(w) for w, _ in pairs):,} characters)")


if __name__ == "__main__":
    main()
```

2. Before running it, write down your predictions: which index uses the least memory, which is fastest for one-letter prefixes, and which is fastest for prefixes of four or more letters.
3. Run `python3 autocomplete_lab.py`. It takes about half a minute; the oracle checks and the second, traced build of each index take most of it.
4. Copy the output into a table: build time, memory, and p50 and p99 latency for prefix lengths 1, 2, 3 and 4+.
5. Explain the one-letter row. In the Python shell, count how many of the 100,000 words start with "s" and with "comp". The collecting trie visits all of those nodes per query; the sorted list scans the same block of the list but in C-level loops; the cached trie reads five tuples.
6. Change `K` to 10 and rerun: which numbers move, and by roughly how much?
7. Stretch: load all 333,333 words (`load(n=333_333)`). Does memory scale linearly with the number of words? Does the one-letter p99 of the collecting trie stay under 100 ms?

## What you should see

On a recent laptop or server, single-threaded (expect noise of a factor of two on a shared machine):

- **Memory**: the sorted list adds under 2 MB on top of the 4.8 MB of word strings it shares; the collecting trie uses about 48 MB for 233,569 nodes (about 200 bytes per node); the cached trie about 78 MB.
- **Build**: about 0.3 s for the sorted list, about 1 s for the trie, about 3 s for the cached trie.
- **One-letter prefixes**: sorted list p50 around 2 ms (p99 around 10 ms), collecting trie p50 around 12 ms (p99 around 50 ms), cached trie a few microseconds. 10,014 of the words start with "s", 275 with "comp".
- **Four or more letters**: everything is fast, from a few microseconds (cached trie) to about 0.02 ms (sorted list) and 0.03 ms (collecting trie) at p50.
- The naive trie is the **worst** design here: bigger than the sorted list and slower for short prefixes, because it does the same O(matches) work in Python bytecode instead of C. Caching per node buys roughly a thousandfold speed-up on short prefixes for about 60% more memory.
- With K = 10 the cached trie's memory grows (longer lists on every node) while its latency stays tiny; the other two barely change.

## Check yourself

Q: Your product owner wants under 1 ms at p99 for every prefix, and memory is not a concern. Which design meets that here, and what is its real cost?
A: Only the cached trie: at p99, one-letter prefixes take around 10 ms with the sorted list and around 50 ms with the collecting trie. Its cost is memory (about 60% more than the plain trie, and K entries on every node) and update complexity: if counts change, every node on a word's path must refresh its list, and a decrease forces rebuilding lists from the children.

=== primer | How do you find every dictionary word hidden in a letter grid without searching for each word separately? | 16 min
goal: Run one backtracking search over a grid guided by a trie of all the words, pruning dead prefixes and found words, and bound its cost
tag: trie-grid | Trie-guided grid search
link: cp-algorithms: Aho-Corasick, construction of the automaton | https://cp-algorithms.com/string/aho_corasick.html#construction-of-an-automaton | 15 min: 'Construction of the trie' and 'Construction of an automaton'; the same idea (walk one trie for all patterns at once) for a text instead of a grid, with suffix links that avoid restarting
practice: 212

> [!key]
> Searching the grid once per word repeats the same exploration for every shared prefix. Instead, build a trie of all the words and run **one** depth-first search from each cell that walks the grid and the trie **in lockstep**: a step is allowed only if the next letter is a child of the current trie node, so the search dies the moment the path stops being a prefix of any word. Record a word when you reach its end node, then **prune** trie branches that have nothing left to find.

## Intuition

Imagine twenty friends each searching the same word-search puzzle for their own word. Most of them start at the same letters and trace the same paths ("ca..." for car, cat, cats, cave). A trie lets one person carry all twenty words at once: standing on a C next to an A, they continue only if some word starts with "ca", and they notice every word that ends along the way.

## How it works

1. **Build** a trie of the words. Store the whole word at its end node (instead of a flag), so you can record it without rebuilding the string from the path.
2. **Start** a DFS from every cell whose letter is a child of the root.
3. **Step**: at cell (r, c) with trie node `node`, if `node` holds a word, record it and **remove** it from the node, so a second path spelling the same word cannot report it again.
4. **Mark** the cell as used (overwrite it with `#`), recurse into the four neighbours whose letters are children of `node`, then **restore** the cell. This is the choose, explore, unchoose pattern of backtracking.
5. **Prune** on the way back: if `node` now has no children and holds no word, delete it from its parent. Later searches will not even enter that branch, and when the whole trie is empty every remaining start cell is skipped instantly.

The two pruning effects are different: walking the trie stops paths that are **not prefixes** of any word; deleting exhausted branches stops paths that only lead to words **already found**.

## Cost

Let the grid have R x C cells and the longest word have length L.

- **Build**: O(S) for S total characters in the word list.
- **Search, worst case**: from each start cell the first step has at most 4 neighbours and every later step at most 3 (you cannot step back onto the cell you came from), and a path never goes deeper than L because it must stay inside the trie. That gives O(R * C * 4 * 3^(L-1)) steps, each O(1).
- **Compared with one search per word**: W words would cost up to W times as much, because the shared prefixes are re-explored for each word.
- **Space**: the trie, O(S), plus the recursion depth, at most L frames.

The worst case needs an adversarial grid (all 'a') and words like "aaaaaaaaab". On real grids the trie walk cuts almost every path within one or two steps, and pruning removes whole branches as words are found.

## When to use it

- **Cues**: one board or text, many query words, "return all words that appear", paths of adjacent cells with no reuse.
- **One word only**: plain backtracking (word search I); a trie adds nothing.
- **Many patterns in a linear text** (no grid): Aho-Corasick, which adds failure links to the trie so the text is scanned once in O(text + patterns + matches).
- **Huge dictionaries and tiny boards**: the opposite direction can win: enumerate the board's paths up to length L and look each one up in a set of the words and a set of their prefixes.

## Worked trace

Board rows "cat", "ors", "doc"; words car, cat, cats, rod. Neighbours are tried in the order up, down, left, right. Used cells show as #.

```steps
Trie of the words. Start at (0,0): "c" is a child of the root, so the search begins
    {{c}} a t      trie: c-a-r*  c-a-t*-s*  r-o-d*
    o r s
    d o c
---
Mark (0,0). Up and left are off the board, down is "o" (not a child of c), right is "a": go to (0,1), node "ca"
    # {{a}} t      trie: c-a-r*  c-a-t*-s*  r-o-d*
    o r s
    d o c
---
From (0,1), down is "r" and "car" is a word: record car, then prune its leaf
    # # t      found: car
    o {{r}} s      trie: c-a-t*-s*  r-o-d*
    d o c
---
Back at "ca", right is "t": record cat. From (0,2), down is "s": record cats
    # # #      found: car cat cats
    o r {{s}}      trie: c-a-t-s  r-o-d*   (words removed)
    d o c
---
Unwinding prunes s, t, a and c, since each is now empty. All cells are restored
    c a t      found: car cat cats
    o r s      trie: {{r-o-d*}}
    d o c
---
(0,1) "a", (0,2) "t" and (1,0) "o" are not children of the root: skipped with no search at all
    c {{a}} {{t}}      trie: r-o-d*
    {{o}} r s
    d o c
---
(1,1) "r": down to "o" at (2,1), then left to "d": record rod and prune d, o, r
    c a t      found: car cat cats rod
    o # s      trie: (empty)
    {{d}} # c
---
The second path to "rod", via (1,0), is never tried: "r" has no children left. The other "c" at (2,2) is skipped too
    c a t      found: car cat cats rod
    o r s      trie: (empty)
    d o {{c}}
```

## Template

```python
def find_words(board, words):
    """Every word from words that can be traced through adjacent cells, each cell used at most once per word."""
    root = {}
    for w in words:
        node = root
        for ch in w:
            node = node.setdefault(ch, {})
        node["$"] = w                          # the word ends here; store it whole
    rows, cols = len(board), len(board[0])
    found = []

    def dfs(r, c, parent):
        ch = board[r][c]
        node = parent[ch]
        word = node.pop("$", None)             # report each word once
        if word is not None:
            found.append(word)
        board[r][c] = "#"                      # choose: mark the cell as used
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] in node:
                dfs(nr, nc, node)              # explore only prefixes of some word
        board[r][c] = ch                       # unchoose: restore the cell
        if not node:                           # nothing left below: prune this branch
            del parent[ch]

    for r in range(rows):
        for c in range(cols):
            if board[r][c] in root:
                dfs(r, c, root)
    return found
```

The trie here is plain nested dicts with the key `"$"` holding the word: compact to write, and safe because neither `"$"` nor `"#"` is a board letter. Recursion depth is at most the longest word, so Python's limit is not a concern for word lengths of 10 or so.

## Pitfalls

- **Forgetting to restore the cell** corrupts the board for every later start, and you miss words.
- **Reporting duplicates**: two paths can spell the same word. Removing the word from its node (or using a set) fixes it; the pop also feeds pruning.
- **Pruning while iterating** a dict raises "dictionary changed size during iteration". The template deletes the child from its parent only after finishing its own loop, and the parent's loop iterates over directions, not over the dict.
- **Checking the neighbour's letter against the wrong node**: the test must be `board[nr][nc] in node` (children of the current node), not `in root`.
- **Mutating the caller's board** is fine only because every change is undone; if the board is shared between threads or reused, copy it first.

## Check yourself

Q: In the trace, why does the search from (1,1) never try the path r, o (1,0), d (2,0), even though it also spells "rod"?
A: The first path recorded "rod" and pruned d, o and r from the trie. By the time the loop at r reaches the left neighbour (1,0), the r node has no children, so the condition `board[nr][nc] in node` fails immediately.

Q: Why is the branching factor 3, not 4, after the first step, and why does the depth never exceed the longest word?
A: The cell you came from is marked as used, so at most three neighbours remain. The DFS only moves into a neighbour whose letter is a child of the current trie node, and the trie has no path longer than the longest word, so the recursion cannot go deeper than L.

Q: Without the pruning lines, what still works and what gets slower?
A: The answer stays correct, because the popped words cannot be reported twice. But exhausted branches remain in the trie, so later searches keep walking prefixes that lead only to words already found: on a large board where most words are found early, that is most of the remaining work.

## Lab

- **212 Word Search II**: implement the template from memory, then test it on the trace's board and on an all-"a" 12 x 12 board with words "a" through "aaaaaaaaaa" plus "aaaaaaaaab". Expected: the trace's board returns car, cat, cats and rod (in any order); the all-"a" board returns the ten words made only of "a" and never "aaaaaaaaab"; worst case O(R * C * 4 * 3^(L-1)), which is why the all-"a" case is far slower than the real board.

> [!know]
> You now know how to search a whole dictionary in one backtracking pass by walking a trie in lockstep with the grid, and how pruning finished branches keeps it fast.

=== primer | How do you search a trie with wildcards, or find every dictionary word that starts at a given position? | 14 min
goal: Branch over all children for a '.' wildcard, walk the trie along a string to list every dictionary word starting at each index, and bound both costs
tag: trie-scan | Trie walks with wildcards and from each start
link: USACO Guide: Advanced string searching, Tries | https://usaco.guide/adv/string-search#tries | 5 min: the short 'Tries' subsection: an array-based C++ trie (trie[node][26] plus an end flag) written for CSES Word Combinations, which counts segmentations with exactly the walk-from-each-start loop of this card
practice: 211, 2707, 336

> [!key]
> Two small changes to the plain walk cover a family of problems. A **wildcard** position cannot follow one child, so it tries every child and succeeds if any branch does: a depth-first search over the trie. A **scan from position i** keeps following s[i], s[i+1], ... down the trie and reports every word-end it passes, so one walk lists **all** dictionary words that start at i, stopping as soon as the path leaves the trie. Both cost no more than the part of the trie they touch.

## Intuition

A crossword solver with "b?e" in front of them runs a finger down the B page, then fans out over every second letter, keeping only the branches that can still end in E. And a reader scanning "theremin" from the first letter notices "the", "there" and "theremin" in one left-to-right pass: every word that starts there is a prefix of the same walk.

## How it works

### Wildcard search

`match(node, pattern, i)` asks whether some stored word below `node` matches `pattern[i:]`.

- If `i == len(pattern)`, succeed exactly when `node` is a word end.
- If `pattern[i]` is a letter, follow that one child (fail if it is missing).
- If it is `.`, try each child in turn and succeed on the first branch that matches the rest.

Each node is visited at most once per search: a node at depth d can only be reached while matching pattern position d.

### Every word that starts at i

Walk from the root along s[i], s[i+1], ...; whenever the node you reach is a word end, s[i:j] is a dictionary word, where j is one past the last character read. Stop when a child is missing. This turns "which dictionary words start here?" into one walk instead of one lookup per possible length, and it is the inner loop of segmentation DPs such as Extra Characters in a String or Word Break:

```text
best[i] = fewest leftover characters in s[i:]
best[i] = min(best[i + 1] + 1,                           leave s[i] over
              best[j] for every word s[i:j] found by the walk from i)
```

The same walk, stopped at the **first** word end, gives the shortest dictionary root of a word (Replace Words, in the longest-prefix-match card).

## Cost

- **Wildcard search without dots**: O(L), the plain walk.
- **With dots**: every visited node sits at the depth of the pattern position being matched, so the search visits at most the trie nodes at depths 0 to L. Worst case it is a scan of that part of the trie: O(min(total nodes, alphabet^d * L)) for d dots. Patterns with dots near the end are cheap; a leading dot fans out across the whole first level.
- **Scan from one start**: O(min(n - i, maxlen)), where maxlen is the longest dictionary word, because the walk cannot go deeper than the trie.
- **Scan from every start** (the DP above): O(n * maxlen) for the walks plus O(S) to build the trie, compared with O(n * maxlen^2) for slicing every candidate s[i:j] and looking it up in a set (each slice costs up to maxlen).

## When to use it

- **Single-position wildcards** over a dictionary that also receives inserts: trie with branching search. For a fixed dictionary and fixed wildcard positions, precomputing keys such as "b.e" into a dict can be faster.
- **Segmentation and "words inside a string"** with a large dictionary and long words: trie scans. With short words (maxlen around 10), a set of words with slicing is often just as fast in Python and simpler.
- **Many patterns in a long text**, reported in one pass: Aho-Corasick, which is this scan plus failure links so you never restart from the root.
- **General regular expressions**: use `re`, not a trie.

## Worked trace

Trie of bad, bed, bee and dad; search "b.e". Highlighted nodes are the ones being tried.

```steps
match(root, "b.e", 0): "b" is a letter, so follow the single child b
    root
     +- {{b}}
     |   +- a
     |   |   +- d*
     |   +- e
     |       +- d*
     |       +- e*
     +- d
         +- a
             +- d*
---
Position 1 is ".", so try every child of b in turn. First child: a
    root
     +- {{b}}
     |   +- {{a}}
     |   |   +- d*
     |   +- e
     |       +- d*
     |       +- e*
---
Position 2 needs "e" under ba, but ba has only d: this branch fails, back up
    root
     +- {{b}}
     |   +- {{a}}
     |   |   +- d*    (no e)
     |   +- e
---
Next child of b: e. Position 2 needs "e" under be: it exists
    root
     +- {{b}}
     |   +- a
     |   +- {{e}}
     |       +- d*
     |       +- {{e*}}
---
i = 3 = len(pattern) and bee is a word end: True. The d subtree was never visited
    root
     +- {{b}}
     |   +- {{e}}
     |       +- {{e*}}   -> "bee" matches
     +- d   (untouched)
```

## Template

```python
END = "$"


def build(words):
    root = {}
    for w in words:
        node = root
        for ch in w:
            node = node.setdefault(ch, {})
        node[END] = True
    return root


def match(node, pattern, i=0):
    """Does some stored word below node match pattern[i:], where '.' matches any one character?"""
    if i == len(pattern):
        return END in node
    ch = pattern[i]
    if ch == ".":
        return any(match(child, pattern, i + 1) for key, child in node.items() if key != END)
    child = node.get(ch)
    return child is not None and match(child, pattern, i + 1)


def words_starting_at(root, s, i):
    """Every j such that s[i:j] is a stored word, in increasing order, found in one walk."""
    node, ends = root, []
    for j in range(i, len(s)):
        node = node.get(s[j])
        if node is None:
            break
        if END in node:
            ends.append(j + 1)
    return ends
```

`any` stops at the first successful branch, so a match found early ends the search. The recursion depth of `match` is the pattern length, which is safe for word-length patterns.

## Pitfalls

- **Treating the end marker as a child.** With a nested-dict trie, the `.` branch must skip the `"$"` key, or a pattern like "ba." could step into True instead of a node.
- **Forgetting the length check.** "b." must not match "bad": success requires both the pattern to be exhausted and the node to be a word end.
- **Slicing inside the scan.** Building `s[i:j]` at every step makes the walk O(maxlen^2) per start; carry the node, and slice only for words you actually report.
- **Stopping the scan at the first word** when you need all of them (segmentation), or continuing past it when you need the shortest root (Replace Words). Decide which the problem asks for.

## Check yourself

Q: With the trace's trie (bad, bed, bee, dad), what do `match(root, ".a.")`, `match(root, "b..")`, `match(root, "d.e")` and `match(root, "be")` return?
A: True (bad or dad), True (bad), False (only dad starts with d, and it ends in d), and False ("be" is a prefix but not a word end).

Q: Why can a wildcard search never visit more nodes than the trie has at depths 0 to L, even with every position a dot?
A: When matching position i, the search is always at a node of depth i, and from each node it enters each child at most once for position i + 1. So each node is entered at most once, and only nodes at depth up to L can be reached. The worst case is a full scan of those levels, never more.

Q: For s = "catsanddog" and the dictionary {cat, cats, and, sand, dog}, what does `words_starting_at(root, s, 0)` return, and what does it tell a segmentation DP?
A: [3, 4]: "cat" ends before index 3 and "cats" before index 4. The DP for position 0 can therefore continue from best[3] or best[4] (plus the option of leaving s[0] over), without trying any other split point.

## Lab

- **211 Design Add and Search Words Data Structure**: a trie whose search treats "." as any letter. Expected: O(L) without dots and at most the trie levels touched with dots; after adding bad, bed, bee and dad, search("b..") is True, search(".e.") is True, search("d.e") is False and search("b.") is False.
- **2707 Extra Characters in a String**: the DP above, with the trie scan as the inner loop. Expected: O(n * maxlen + S) time; s = "xsayhelloqworld" with dictionary ["say", "hello", "hell", "world", "low"] gives 2 (x and q are left over).
- **336 Palindrome Pairs** (stretch): for each word, split it into a part that must itself be a palindrome and a part whose reverse must be another word; look reverses up in a dict (or walk a trie of reversed words). Expected: O(n * k^2) for n words of length up to k; ["ab", "ba", "abc", "cba", "a", ""] has 10 ordered pairs, including both orders of each reversed couple and every pairing of "" with a palindrome.

> [!know]
> You now know how to branch a trie walk over wildcards and how one walk from each position lists every dictionary word starting there, the engine of segmentation DPs.

=== primer | How does a binary trie find the maximum XOR of two numbers? | 14 min
goal: Store numbers as bit paths from the highest bit, answer "which stored number maximises x XOR y?" greedily in O(bits), and know the set-based alternative
tag: trie-xor | Binary trie for maximum XOR
link: Wikipedia: Trie, Bitwise tries | https://en.wikipedia.org/wiki/Trie#Bitwise_tries | 3 min: the short 'Bitwise tries' subsection: keys walked one bit at a time, the representation this card uses (its notes on CPU bit instructions are optional)
practice: 421, 1707

> [!key]
> Write every number as a fixed-width string of bits, highest bit first, and store those strings in a trie with two children per node. To maximise x XOR y, walk down choosing the child whose bit is the **opposite** of x's bit whenever it exists. Taking a 1 at a higher bit always beats anything the lower bits can add, because 2^b is larger than 2^b - 1 (all lower bits set). Each insert and query costs O(B) for B bits, so the best pair among n numbers costs O(nB) instead of O(n^2).

## Intuition

XOR gives 1 exactly where two numbers differ. To make x XOR y large you want y to differ from x in the **highest** possible positions, and you want that greedily: a single 1 in bit 4 (16) beats 1s in all of bits 0 to 3 together (15). So ask, from the top bit down: "is there a stored number that differs from x here, among those that matched my choices so far?" A trie keyed by bits answers exactly that, one level per bit.

## How it works

Insert a number by walking bits B-1 down to 0, creating the 0-child or 1-child as needed. The node reached after k bits represents every stored number that shares those k leading bits.

```text
3-bit numbers 1 (001), 4 (100), 6 (110)

        root
      0/    \1
      0      1
      |0    0/ \1
      0     0   1
      |1    |0  |0
     001   100  110
```

Query x: at each level, let bit be x's bit. If the child for `1 - bit` exists, go there and set that bit of the answer; otherwise take the child for `bit` (it must exist, since every node lies on some stored number's path) and leave the answer bit 0.

**Why greedy is safe**: suppose at bit b the opposite child exists but you took the same child. Every number in the same-child subtree gives an XOR whose bit b is 0 and whose higher bits equal the ones you already fixed, so it is at most (fixed part) + 2^b - 1, while any number in the opposite subtree gives at least (fixed part) + 2^b. So the opposite child always contains the best answer.

For the maximum over all pairs, insert every number, then query every number and keep the largest result. (Inserting each number before querying it also works and pairs a number with itself, which contributes XOR 0 and never wins unless there is only one number.)

## Cost

- Insert: B steps, at most B new nodes. Query: B steps.
- All pairs: n inserts plus n queries, O(nB), with B = 31 for values below 2^31. Brute force is n(n-1)/2 XORs: for n = 200,000 that is 2 * 10^10, against about 1.2 * 10^7 trie steps.
- Memory: up to nB nodes; shared high bits make it fewer. In Python, 200,000 random 31-bit numbers produced about 2.9 million nodes and took about 8 s with the flat-list template below.
- The same greedy without a trie: for each bit from the top, put every number's prefix `x >> b` into a set and check whether the next candidate answer is achievable (`want ^ p in prefixes`). Also O(nB), but each step is a C-level set operation, and on the same 200,000 numbers it ran in about 2 s in Python. The trie earns its keep when the set of numbers **changes between queries**, as in offline queries sorted by a limit.

## When to use it

- **Cues**: "maximum XOR", "XOR with any element", queries that each pick the best partner for x from a set that grows.
- **Offline constraints**: if each query only allows elements up to some limit m, sort the queries by m and the numbers by value, insert numbers as the limit grows, then answer: the trie supports inserts between queries.
- **Minimum XOR**: walk preferring the **same** bit instead.
- **XOR of a subset** (not a pair) is a different problem: that needs a linear basis over GF(2), not a trie.
- **Negative numbers**: Python's ints have no fixed width; add an offset (or mask to 32 bits) so every key has the same number of bits.

## Worked trace

The trie holds 9 (1001), 12 (1100) and 6 (0110), with B = 4. Query x = 2 (0010). A node is shown as the set of numbers still reachable below it.

```steps
x = 2 = 0010, best = 0000. At the root every stored number is reachable
    bit:        3 2 1 0
    x           0 0 1 0
    reachable   1001 (9)   1100 (12)   0110 (6)
    best        0 0 0 0
---
Bit 3: x has 0, so prefer 1. The 1-child exists (9 and 12): take it, best gets bit 3
    x           {{0}} 0 1 0
    reachable   {{1001 (9)   1100 (12)}}
    best        {{1}} 0 0 0
---
Bit 2: x has 0, prefer 1. Only 12 has a 1 here, so the 1-child exists: take it
    x           0 {{0}} 1 0
    reachable   {{1100 (12)}}
    best        1 {{1}} 0 0
---
Bit 1: x has 1, prefer 0. 12 has 0 here: the 0-child exists, take it
    x           0 0 {{1}} 0
    reachable   1100 (12)
    best        1 1 {{1}} 0
---
Bit 0: x has 0, prefer 1, but 12 has only a 0-child. Forced: best keeps 0 here
    x           0 0 1 {{0}}
    reachable   1100 (12)
    best        1 1 1 {{0}}   = 14 = 2 XOR 12
---
For the best pair, insert all four numbers (9, 12, 6, 2) and query each one. Maximum pair XOR = 15
    9  = 1001   best partner 0110 (6)    -> {{1111 = 15}}
    12 = 1100   best partner 0010 (2)    -> 1110 = 14
    6  = 0110   best partner 1001 (9)    -> {{1111 = 15}}
    2  = 0010   best partner 1100 (12)   -> 1110 = 14
```

## Template

```python
class XorTrie:
    """Binary trie over non-negative ints below 2**bits, for maximum-XOR queries."""

    def __init__(self, bits=31):
        self.bits = bits
        self.child = [0, 0]        # node k's children: child[2k] (bit 0), child[2k + 1] (bit 1); 0 = none

    def insert(self, x):
        node = 0
        for b in range(self.bits - 1, -1, -1):
            slot = 2 * node + ((x >> b) & 1)
            if not self.child[slot]:
                self.child[slot] = len(self.child) // 2     # number of the new node
                self.child += [0, 0]
            node = self.child[slot]

    def max_xor(self, x):
        """Largest x ^ y over all inserted y. The trie must not be empty."""
        node, best = 0, 0
        for b in range(self.bits - 1, -1, -1):
            bit = (x >> b) & 1
            other = self.child[2 * node + (bit ^ 1)]
            if other:                                       # a number differs from x here: take it
                best |= 1 << b
                node = other
            else:
                node = self.child[2 * node + bit]
        return best


def max_xor_pair(nums, bits=31):
    """The same greedy with sets of prefixes instead of a trie (faster in Python for a fixed list)."""
    ans = 0
    for b in range(bits - 1, -1, -1):
        prefixes = {x >> b for x in nums}
        want = (ans << 1) | 1                               # can this bit of the answer be 1?
        ans = want if any(want ^ p in prefixes for p in prefixes) else ans << 1
    return ans
```

Node 0 is the root and is never anyone's child, so 0 safely means "no child". One flat list of ints is far lighter in Python than one object per node.

## Pitfalls

- **Bit order.** Walk from the highest bit down; walking from bit 0 up optimises the least important bits first and gives wrong answers.
- **Too few bits.** With `bits=31` a value of 2^31 or more silently loses its top bit. Use `max(nums).bit_length()` (at least 1) when the range is unknown.
- **Querying an empty trie** quietly returns 0, as if a partner existed (every missing child reads as node 0, the root); offline problems must answer -1 when nothing is inserted yet.
- **Self-pairing.** If you query x after inserting it, the result can be x XOR x = 0 only when nothing better exists; for "two different indices" with a single element, handle n = 1 separately.
- **Memory.** Up to n * bits nodes: 6.2 million for n = 200,000 and 31 bits. Prefer the set version when the list is fixed.

## Check yourself

Q: Insert 5 (101), 2 (010) and 7 (111) into a 3-bit trie. Trace the query for x = 5: which child is chosen at each bit, and what is the answer?
A: Bit 2: x has 1, prefer 0: 2 has 0, take it (best 100). Bit 1: x has 0, prefer 1: 2 has 1, take it (best 110). Bit 0: x has 1, prefer 0: 2 has 0, take it (best 111). The answer is 7 = 5 XOR 2.

Q: Prove that choosing the opposite bit whenever possible can never lose to a choice that keeps the same bit.
A: After fixing the higher bits, any number in the opposite subtree gives an XOR of at least prefix + 2^b, and any number in the same-bit subtree gives at most prefix + (2^b - 1), since its bit b of the XOR is 0 and the lower bits add at most 2^b - 1. So the best answer is always in the opposite subtree when it exists.

Q: Each query asks for the maximum of x XOR y over array elements y not exceeding m, with many (x, m) queries. Why does sorting help, and what does each query cost?
A: Sort the array and the queries by m; before answering a query, insert every element up to its m, so the trie always holds exactly the allowed elements (it only grows). Each query then costs O(B), for O((n + q) * B + n log n + q log q) overall.

## Lab

- **421 Maximum XOR of Two Numbers in an Array** (derive): solve it with the trie, then with the set version, and compare times on 200,000 random numbers. Expected: O(31 n) for both; [9, 12, 6, 2] gives 15; in Python the set version is several times faster.
- **1707 Maximum XOR With an Element From Array** (stretch): offline, as in the third question. Expected: O((n + q) * 31 + n log n + q log q); nums = [9, 12, 6, 2] with queries (x=2, m=7) and (x=5, m=1) gives [4, -1] (2 XOR 6, and nothing is at most 1).

> [!know]
> You now know how a binary trie answers maximum-XOR queries greedily from the highest bit, why the greedy is safe, and when a set of prefixes does the same job faster.

=== primer | How does a router find the longest matching prefix, and why are production tries compressed? | 15 min
goal: Implement longest-prefix match with a binary trie over address bits, relate it to shortest-root replacement, and explain how Linux, Redis and HTTP routers compress tries
tag: trie-lpm | Longest and shortest prefix match
link: Linux kernel: LC-trie implementation notes | https://docs.kernel.org/networking/fib_trie.html#main-lookup-mechanism | 10 min: 'Main lookup mechanism', plus 'Path Compression' and 'Level Compression' just above it: how the kernel's IPv4 routing trie skips single-path bits, widens dense nodes and backtracks to the longest matching prefix
practice: 648

> [!key]
> A routing table maps **prefixes** (10.0.0.0/8, 10.20.0.0/16, the default 0.0.0.0/0) to next hops, and a packet must follow the **most specific** prefix that contains its address. Store each prefix as a path of bits in a binary trie and walk the address's bits from the top, **remembering the last node that carries a route**; when the path breaks, the remembered route is the longest match. That is at most 32 steps for IPv4 whatever the table size. Stop at the **first** marked node instead and you get the shortest match, the move behind Replace Words.

## Intuition

Mail sorting works the same way. A sorter holds rules like "anything for the UK goes to bin 1", "London goes to bin 7", "London EC1 goes to bin 12". For a letter to London EC1A, all three rules match, and the most specific one wins. Reading the address one part at a time and remembering the last rule you passed is exactly the trie walk.

## How it works

A prefix of length p is the top p bits of an address. Insert it by walking those p bits from the root and storing the next hop on the node you reach; the default route (/0) lives on the root.

To look up an address:

1. Start at the root with `best` = the root's route (the default, if any).
2. For each bit of the address from the most significant down, move to that child. If it is missing, stop.
3. If the node you reached carries a route, overwrite `best`: it is more specific than anything seen so far.
4. Return `best`.

**Invariant**: after reading k bits, `best` is the route of the longest stored prefix among the first k bits of the address. Every longer stored prefix of the address would lie further down the same path, so when the path breaks, no longer match exists.

### Shortest match: Replace Words

Replace each word in a sentence by its shortest dictionary root ("re" for "replay"): walk the word's letters and return at the **first** node marked as a root. Same structure, opposite stopping rule.

### Real tries are compressed

A plain binary trie for a full Internet table (hundreds of thousands of IPv4 prefixes) would have millions of nodes, and each lookup would chase up to 32 pointers through memory that does not fit in cache. Production systems compress:

- **Linux fib_trie** (the IPv4 forwarding table) is an **LC-trie**: path compression skips runs of bits where there is no branching (the leaf keeps its full key, so a skipped bit is verified at the end), and level compression replaces a dense subtree with one node indexed by several bits at once. When the first leaf does not match, the lookup backtracks, shortening the prefix, until it finds the longest match.
- **Redis rax** is a radix tree over bytes. A stream is "a radix tree of listpacks" keyed by entry IDs, and the client-side caching code tracks which clients cached which keys (and, in broadcast mode, which prefixes) in rax trees.
- **Go's httprouter** matches URL paths with a compact prefix tree, and **Ethereum** stores account state in a Merkle Patricia trie, a radix tree whose nodes are also hashed.

## Cost

- Lookup: one step per address bit, so at most 32 steps for IPv4 and 128 for IPv6, independent of the number of routes n. Each step is O(1).
- Insert: O(p) for a prefix of length p.
- Memory: up to n * 32 nodes uncompressed; path compression bounds it by O(n) nodes, like any radix tree.
- Alternatives: a linear scan of all routes is O(n) per packet; one hash table per prefix length, probed from /32 down to /0, needs up to 33 hash lookups per packet.

## When to use it

- **Cues**: "most specific rule wins", CIDR blocks, path or URL routing with nested prefixes, configuration overrides by key prefix, "longest prefix of the input that is in the table".
- **Shortest match**: "replace by its root", "stop at the first keyword".
- **Few rules** (a dozen ACL entries): a sorted list scanned from the longest prefix is simpler.
- **Exact keys only**: a hash table.
- **Production networking**: use the OS or a library (`ipaddress` gives you `subnet_of` and `in` tests; a radix-tree package for many routes), and treat this template as the model of what they do.

## Worked trace

Toy 8-bit addresses. Routes: default (empty prefix) to A, 1 to B, 101 to C, 10110 to D. Look up 10111010.

```steps
Start at the root: best = A (the default route)
    routes:  (root)=A  1=B  101=C  10110=D
    address  1 0 1 1 1 0 1 0
    path     (root)              best = {{A}}
---
Bit 1: move to node "1", which carries route B: best = B
    address  {{1}} 0 1 1 1 0 1 0
    path     1                   best = {{B}}
---
Bit 0: node "10" exists (it leads to C and D) but carries no route: best stays B
    address  1 {{0}} 1 1 1 0 1 0
    path     10                  best = B
---
Bit 1: node "101" carries route C: best = C
    address  1 0 {{1}} 1 1 0 1 0
    path     101                 best = {{C}}
---
Bit 1: node "1011" exists on the way to D, no route: best stays C
    address  1 0 1 {{1}} 1 0 1 0
    path     1011                best = C
---
Bit 1: there is no node "10111" (D is 10110), so the walk stops. Longest match: 101, next hop C
    address  1 0 1 1 {{1}} 0 1 0
    path     1011 -> (no child 1)  best = {{C}}
```

## Template

```python
import ipaddress


class RouteTable:
    """Longest-prefix match for IPv4 routes, one trie level per address bit."""

    def __init__(self):
        self.root = {}                         # node: {0: child, 1: child, "hop": next hop}

    def add(self, cidr, hop):
        net = ipaddress.IPv4Network(cidr)
        bits = int(net.network_address)
        node = self.root
        for i in range(net.prefixlen):
            node = node.setdefault((bits >> (31 - i)) & 1, {})
        node["hop"] = hop

    def lookup(self, address):
        x = int(ipaddress.IPv4Address(address))
        node, best = self.root, self.root.get("hop")
        for i in range(32):
            node = node.get((x >> (31 - i)) & 1)
            if node is None:
                break
            best = node.get("hop", best)       # a longer matching prefix overrides the shorter one
        return best


def shortest_root(root, word, end="$"):
    """Replace-words walk: the shortest stored prefix of word, or word itself if none."""
    node = root
    for i, ch in enumerate(word):
        node = node.get(ch)
        if node is None:
            break
        if end in node:
            return word[:i + 1]
    return word
```

`shortest_root` expects the nested-dict trie built by `build` in the wildcard card. `ipaddress.IPv4Network` rejects a CIDR with host bits set (such as 10.1.2.3/8) unless you pass `strict=False`, which is a useful guard against typos in route tables.

## Pitfalls

- **Returning the deepest node reached** rather than the deepest node **with a route**: the walk often continues past the last real match (node 1011 in the trace).
- **Forgetting the default route**: initialise `best` from the root, or addresses that match nothing but 0.0.0.0/0 return None.
- **Bit order**: prefixes are the **high** bits; index with `31 - i`.
- **Shortest versus longest**: Replace Words wants the first marked node, routing the last. Swapping the stopping rule passes small tests and fails real ones.
- **Assuming host bits are zero**: normalise each route to its network address before inserting.

## Check yourself

Q: Add the route 10111 to E in the trace. Which next hop does 10111010 get now, and how many nodes does the walk visit?
A: E. The walk now finds node 10111, which carries a route, then tries bit 0 of "101110", finds no child, and stops: it visits the root plus five nodes, and E is the longest match.

Q: Why is it safe to stop at the first missing child, without exploring other branches?
A: Every stored prefix that matches the address is a prefix of the address's own bit string, so it lies on the single path the walk follows. Once that path breaks, no deeper node on it exists, so no longer matching prefix exists anywhere else in the trie.

Q: A firewall has 20 rules, edited by hand each week. Would you build a trie?
A: Probably not: a list of 20 networks sorted by prefix length, checked from the longest, costs at most 20 cheap tests per packet in a few lines of code. The trie pays off for thousands of routes, frequent lookups, or when lookup cost must not grow with the table.

## Lab

- **648 Replace Words**: insert the roots, then replace each word by `shortest_root`. Expected: O(total characters) time; roots ["re", "rep", "un"] and the sentence "replay unhappy rested ox" give "re un re ox".
- Exercise: load the template's RouteTable with 0.0.0.0/0 to isp, 10.0.0.0/8 to corp, 10.20.0.0/16 to lab and 10.20.30.0/24 to rack, then look up 10.20.30.40, 10.20.99.1, 10.99.0.1 and 8.8.8.8. Expected: rack, lab, corp, isp. Then check every answer against a brute force that tests `ipaddress.IPv4Address(a) in network` for every route and keeps the longest prefix.

> [!know]
> You now know how a binary trie gives the longest (or shortest) matching prefix in one walk, and why kernels, Redis and HTTP routers compress their tries.

=== practice
- 208 core
  cue: A class must store words and answer both "is this exact word stored?" and "does any stored word begin with this?"
  hint: Words that begin the same way could share storage. What would you need to remember at the point where a word ends?
  insight: A trie: each node maps a character to a child and has an end-of-word flag. All three operations walk one node per character, so each costs O(L); search checks the flag at the end, starts-with only needs the walk to survive.
  cost: O(L) per operation, O(total characters) space
  pattern: trie-walk
- 3043 core
  cue: Two lists of integers; you want the longest run of leading digits shared by a number from the first list and a number from the second
  hint: Treat each number as a string of digits. Which structure lets you test "is this a prefix of something in list one?" digit by digit?
  insight: Insert every number of the first list as a digit string into a trie (or put all its prefixes in a set); walk each number of the second list as far as it survives and keep the longest depth. Numbers have at most 9 digits, so each walk is tiny.
  cost: O((n + m) * d) time for d at most 9 digits, O(n * d) space
  pattern: trie-walk
- 648 core
  cue: Every word in a sentence should be replaced by the shortest dictionary root it starts with, if any
  hint: For one word, you need the first dictionary entry you meet while reading its letters from the left.
  insight: Insert the roots into a trie; walk each word letter by letter and stop at the first node marked as a root (replace) or at a missing child (keep the word). The shortest root is found first, so no comparison of lengths is needed.
  cost: O(total characters of roots and sentence) time and space
  pattern: trie-lpm
- 1268 core
  cue: After each typed character, show up to three alphabetically smallest products that start with what has been typed
  hint: Every keystroke extends the previous prefix, so the candidate set only shrinks. Could each prefix's answer be stored ahead of time?
  insight: Sort the products and insert them in order into a trie, appending a product to a node's list only while it holds fewer than three; the first three that reach a node are its three smallest. Each keystroke then moves one node and reads its list. Sorting plus bisect on the prefix range also works.
  cost: O(S log n) for sorting plus O(S) to build for S product characters, O(1) per keystroke after that
  pattern: trie-agg
- 677 core
  cue: Store key-value pairs where a key can be set again, and report the total value of all keys starting with a prefix
  hint: The answer for a prefix is a sum over its subtree. Can every node keep that sum up to date as keys arrive and change?
  insight: Keep a running sum on every trie node and a dict of each key's current value. On insert, compute delta = new value minus old value (0 if new) and add delta to every node on the key's path; a query walks to the prefix and reads its sum.
  cost: O(L) per insert and per query, O(total characters) space
  pattern: trie-agg
- 211 core
  cue: Add words, then search with patterns where a dot can stand for any single letter
  hint: A letter follows one branch of a prefix tree. What should a dot do, and when does the search succeed?
  insight: Store the words in a trie. Search recursively: a letter follows its child, a dot tries every child and succeeds if any branch matches the rest; at the end of the pattern the node must be a word end. A node at depth i is only reached for pattern position i, so the search never visits more than the trie's first L levels.
  cost: O(L) without dots; at most the nodes in the first L levels with dots
  pattern: trie-scan
- 421 derive
  cue: Among all pairs of numbers in an array, find the largest bitwise XOR, with up to 2 * 10^5 numbers
  hint: A 1 in a high bit outweighs every lower bit combined. Decide the answer one bit at a time, from the top.
  insight: Store the numbers as 31-bit strings in a binary trie; for each number walk down preferring the child with the opposite bit, setting that answer bit when it exists. Greedy is safe because 2^b exceeds 2^b - 1. The same greedy works with a set of prefixes x >> b per bit.
  cost: O(31 n) time, O(31 n) trie nodes (O(n) with the set version)
  pattern: trie-xor
- 2707 derive
  cue: Split a string into dictionary words and leftover characters so that as few characters as possible are left over
  hint: Decide position by position from the right: either s[i] is left over, or some dictionary word starts at i. How do you list those words quickly?
  insight: Let best[i] be the fewest leftovers in s[i:]: best[i] = min(best[i + 1] + 1, best[j] for every word s[i:j]). Find all such j with one walk down a trie of the dictionary starting at s[i], stopping when a child is missing.
  cost: O(n * maxlen + S) time with a trie (S dictionary characters), O(n + S) space
  pattern: trie-scan
- 2416 core
  cue: For each word, add up, over all of its prefixes, how many words in the list start with that prefix
  hint: The count for one prefix is the number of words passing through one node of a prefix tree.
  insight: Insert every word, adding 1 to a counter on each node it passes. A word's score is the sum of the counters along its own path, so a second pass walks each word once more and adds them up.
  cost: O(total characters) time and space
  pattern: trie-agg
- 212 core
  cue: Find which of many words can be traced on a letter grid through adjacent cells, using each cell at most once per word
  hint: Searching the grid once per word repeats the same paths for words with the same start. Carry all the words in one search.
  insight: Build a trie of the words and run one backtracking DFS from each cell that only moves to a neighbour whose letter is a child of the current trie node. Record a word at its end node and remove it; delete trie branches that become empty so later searches skip them.
  cost: O(R * C * 4 * 3^(L-1)) worst case plus O(S) to build, O(S) space
  pattern: trie-grid
- 1707 stretch
  cue: Many queries, each asking for the largest XOR of x with an array element that does not exceed m
  hint: If the queries arrive in increasing order of m, the set of allowed elements only grows. Can you choose that order yourself?
  insight: Sort the array and the queries by m (remember each query's index). Before answering a query, insert every remaining element at most m into a binary trie, then walk greedily for the opposite bit; answer -1 if nothing has been inserted.
  cost: O((n + q) * 31 + n log n + q log q) time, O(31 n) space
  pattern: trie-xor
- 336 stretch
  cue: Find every ordered pair of distinct words whose concatenation reads the same backwards
  hint: If a + b is a palindrome and a is the longer word, then a starts with the reverse of b and the rest of a is itself a palindrome.
  insight: Map each reversed word to its index. For every word and every split into prefix and suffix: if the prefix is a palindrome and reverse(suffix) is another word, that word goes in front; if the suffix is a palindrome and reverse(prefix) is another word, it goes behind. Skip one of the two empty splits to avoid counting a pair twice, and handle the empty word.
  cost: O(n * k^2) time for n words of length up to k, O(n * k) space
  pattern: trie-scan
