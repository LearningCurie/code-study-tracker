=== card | 208
time: 25 min

## The problem

Design a collection of lowercase words with three operations: add a word, check whether a whole word was added, and check whether any added word begins with a supplied prefix. For instance, after adding `ant`, `an` is a prefix but is not yet a stored word.

## Constraints and what they imply

Operations arrive online, so earlier additions must remain available for later queries. Words consist of lowercase English letters and are nonempty in the original task. Repeated additions should not change the answer. A path alone represents a prefix, not necessarily a complete word: an explicit terminal marker distinguishes the two.

## Brute force

Keep all words in a set. Exact membership is fast on average, but a prefix query can scan every stored word and compare up to its length. For `n` words and prefix length `L`, that query can take O(nL) time. Explicitly storing every prefix instead improves queries but copies many overlapping strings.

## The insight

Share each common beginning as a path from the root. A node has one child per next letter and a flag saying whether a word ends there. After following a query, successful prefix search needs only the path, whereas exact search additionally requires the flag. Insertion creates precisely the missing edges, preserving all earlier paths and terminal flags.

## Optimal solution, traced

```steps
Add ant
    root -> a -> n -> t; mark t terminal
---
Ask for an
    path exists, but n is not terminal
    exact {{False}}, prefix {{True}}
---
Add an
    mark n terminal without removing t
    both exact searches now succeed
```

By induction on characters, the node reached after reading a prefix represents exactly that prefix. No other word can make a nonterminal node an exact match.

## Code

```python
class Trie:
    def __init__(self):
        self.root = {"children": {}, "end": False}

    def insert(self, word):
        node = self.root
        for ch in word:
            children = node["children"]
            if ch not in children:
                children[ch] = {"children": {}, "end": False}
            node = children[ch]
        node["end"] = True

    def _walk(self, text):
        node = self.root
        for ch in text:
            node = node["children"].get(ch)
            if node is None:
                return None
        return node

    def search(self, word):
        node = self._walk(word)
        return node is not None and node["end"]

    def starts_with(self, prefix):
        return self._walk(prefix) is not None
```

## Complexity

With expected constant-time dictionary access, each operation takes O(L) time for its input length. A total of S inserted characters creates at most S nodes, so storage is O(S), including child maps. The temporary traversal uses O(1) auxiliary space.

## Mistakes and edge cases

- Do not mark every traversed node as a complete word.
- Inserting an existing word must retain its descendants and other terminal flags.
- The code treats the empty prefix as present even in an empty trie; empty strings are outside the stated input contract.
- A failed lookup must not create nodes as a side effect.

## Variations

- Add deletion using per-node counts so shared paths are removed only when unused.
- Return all words below a prefix by traversing its descendants.
- Count how many stored words share each prefix.

=== card | 3043
time: 25 min

## The problem

Given two collections of positive integers, choose one number from each and return the greatest number of initial decimal digits they share. If no first digit agrees, return zero. For example, `[451, 82]` and `[4599, 8]` yield 2 from `451` and `4599`.

## Constraints and what they imply

Numbers are positive and represented in ordinary decimal notation, without leading zeroes. A number may be a prefix of another, and duplicates do not change the maximum. If a number has at most `d` digits, traversing its digits is bounded by `d`; comparisons are about the textual representation, not arithmetic distance.

## Brute force

Convert each pair to decimal strings and compare their leading characters until a mismatch. For `n` and `m` numbers this costs O(nmd) time, since each pair may agree for the entire shorter representation. It repeats the same comparisons when many numbers share their first digits.

## The insight

Insert the decimal representation of every first-collection number into a prefix tree. A path of length `k` exists exactly when some inserted number begins with those `k` digits. For each second-collection number, follow its path until the next edge is absent; the length reached is the best match with any first number. Taking the maximum over queries covers every cross-collection pair.

## Optimal solution, traced

```steps
Insert 451 and 82
    root has edges 4 and 8
---
Walk 4599
    4 -> 5 succeeds; edge 9 is missing
    best length {{2}}
---
Walk 8
    its one digit succeeds; maximum stays {{2}}
```

Even when a walk stops at a node with children, it has already found a real prefix of an inserted number. A terminal marker is unnecessary because the task asks only about beginnings.

## Code

```python
def longest_common_prefix(first, second):
    root = {}
    for number in first:
        node = root
        for digit in str(number):
            node = node.setdefault(digit, {})

    best = 0
    for number in second:
        node = root
        length = 0
        for digit in str(number):
            if digit not in node:
                break
            node = node[digit]
            length += 1
        best = max(best, length)
    return best
```

## Complexity

For at most `d` digits per number, expected time is O((n + m)d), including conversion, and the trie uses O(nd) space. Traversing a query needs O(d) for its decimal string. An empty collection, although outside the original constraints, naturally produces zero.

## Mistakes and edge cases

- Do not compare suffixes or numeric closeness: only aligned leading digits count.
- Stop when either the query ends or an edge is absent; neither number needs to be a complete trie word.
- Repeated values are harmless, and a shared first digit can produce exactly one.
- Negative signs and leading-zero encodings would need a different input contract.

## Variations

- Store all decimal prefixes in a set instead of building nodes.
- Return an example pair by keeping a representative at each node.
- Find the longest shared prefix among three collections.

=== card | 648
time: 25 min

## The problem

You are given a collection of lowercase roots and a sentence of lowercase words separated by single spaces. Replace each sentence word by the shortest root that is its prefix; retain words with no matching root. With roots `["go", "gone"]`, the sentence `gone home` becomes `go home`.

## Constraints and what they imply

Roots and sentence words are nonempty. A root may equal the entire word or be the beginning of another root. Only prefixes count: an occurrence in the middle is irrelevant. Because the input uses single spaces, splitting and joining words preserves its spacing.

The selection is independent for each word, so replacing one word does not affect the choices for its neighbours. Multiple identical roots are harmless: they lead to the same terminal node. The case-sensitive lowercase alphabet also lets us reserve a non-character key for the terminal marker without ambiguity.

## Brute force

For each sentence word, test every root using a prefix comparison and select the shortest match. If there are `r` roots and `w` sentence words, comparisons can require O(wrd) time for maximum compared length `d`. The same root characters are repeatedly examined across different words.

## The insight

Insert roots into a trie and mark their ends. Scan a sentence word from left to right. The first marked node encountered is the shortest possible root because node depth increases by one each step. If an edge is missing before a mark, no longer root can match: every longer matching root would require that missing edge.

## Optimal solution, traced

```steps
Insert go and gone
    mark both o and e as root ends
---
Walk gone
    g -> o reaches the first terminal
    replace with {{go}}
---
Walk home
    no h edge exists at the root
    keep {{home}}
```

The scan stops immediately on the first terminal, so a longer terminal below it cannot override the correct answer.

## Code

```python
def replace_words(roots, sentence):
    root = {}
    for word in roots:
        node = root
        for ch in word:
            node = node.setdefault(ch, {})
        node[None] = True

    result = []
    for word in sentence.split(" "):
        node = root
        replacement = word
        for i, ch in enumerate(word):
            if ch not in node:
                break
            node = node[ch]
            if None in node:
                replacement = word[:i + 1]
                break
        result.append(replacement)
    return " ".join(result)
```

## Complexity

Let `S` be the total number of root characters and `T` the sentence length. Expected time is O(S + T): each input character is processed at most once in its phase. Trie space is O(S); the split words and returned sentence use O(T) additional space.

## Mistakes and edge cases

- A complete word can itself be the shortest matching root.
- Stop at the first terminal, not the deepest terminal.
- A missing first edge leaves the word unchanged.
- The marker `None` cannot collide with a character key. Empty roots and arbitrary whitespace are outside the contract.

## Variations

- Replace using the longest matching root instead.
- Preserve arbitrary original whitespace by tokenizing separators as well as words.
- Store roots in a set and check every prefix of each word.

=== card | 1268
time: 30 min

## The problem

Given distinct lowercase product names and a search word, return a list of suggestions after each successive character is typed. Each list contains at most three matching names, ordered lexicographically. For products `["map", "mat", "moss", "mud"]` and search word `ma`, the answers are `["map", "mat", "moss"]` then `["map", "mat"]`.

## Constraints and what they imply

Products are distinct, and both products and the search word are nonempty lowercase strings. Prefixes are nested as the user types: after a prefix fails to match, every longer prefix also fails. The answer must contain the original full product strings, not just their suffixes.

## Brute force

For each search prefix, filter the entire product list and sort all matches, then keep three. With `L` search characters and `n` products, this repeats up to `L` full scans and sorts; O(L(n d + n log n d)) is a conservative bound when comparing strings of length at most `d`. Shared prefixes do not reduce that repeated work.

## The insight

Sort the products once, then insert them into a trie in that order. At every visited node, append the current product only if fewer than three have been saved. All products visiting a node share its prefix, and sorted insertion ensures the saved first three are the smallest matches. Following the search word then reads the precomputed list for each prefix.

## Optimal solution, traced

```steps
Sort map, mat, moss, mud and insert in order
    node m caches [map, mat, moss]; mud arrives too late
---
Type m
    return {{[map, mat, moss]}}
---
Type a after m
    node ma caches {{[map, mat]}}
```

Once a node contains three names, later names cannot be lexicographically smaller because the input order is sorted. Capping the list therefore loses no answer.

## Code

```python
def suggested_products(products, search_word):
    root = {"children": {}, "best": []}
    for product in sorted(products):
        node = root
        for ch in product:
            children = node["children"]
            if ch not in children:
                children[ch] = {"children": {}, "best": []}
            node = children[ch]
            if len(node["best"]) < 3:
                node["best"].append(product)

    answers = []
    node = root
    for ch in search_word:
        if node is not None:
            node = node["children"].get(ch)
        answers.append([] if node is None else list(node["best"]))
    return answers
```

## Complexity

For `n` products, total product length `S`, search length `L`, and maximum product length `d`, sorting costs O(n log n · d) in the worst case; building and querying take O(S + L), apart from the constant-size output lists. The trie stores O(S) nodes and at most three references per node, so uses O(S) space; the returned lists use O(L).

## Mistakes and edge cases

- Sorting must happen before caching; insertion order otherwise determines the wrong three.
- Include fewer than three names when fewer match.
- Once a prefix has no path, emit an empty list for it and every later prefix.
- Return independent result lists rather than exposing the mutable cache.

## Variations

- Use sorted products and binary search to locate the first match for each prefix.
- Support a configurable suggestion limit instead of three.
- Support product deletion by storing more information at each node.

=== card | 677
time: 30 min

## The problem

Maintain lowercase string keys with integer values. Setting an existing key replaces its value; a prefix query returns the sum of values for all keys beginning with that prefix. For example, set `art` to 4, set `arc` to 2, then reset `art` to 1: the sum for `ar` is 3.

## Constraints and what they imply

Keys and queried prefixes are nonempty in the original task. Multiple updates to the same key are replacements, not additions. Distinct keys can share an arbitrarily long path, and an absent prefix has sum zero. Retaining the old value is essential to remove its previous contribution.

## Brute force

Keep a dictionary of keys and values. On every query, iterate through all `n` keys and add values whose keys begin with the requested prefix. This takes O(nL) time for a prefix of length `L`, even when only a few keys match. Updates themselves take expected O(L) to hash the key.

## The insight

Each trie node stores the sum of all key values passing through that prefix. When changing a key, find the difference between its new and old values, then add that difference to the root and every node on its path. Every affected prefix includes this key and no other prefix does, so the node-sum invariant survives both new keys and overwrites. Querying follows a single path and reads its aggregate.

## Optimal solution, traced

```steps
Set art = 4 and arc = 2
    node ar has total 6
---
Reset art from 4 to 1
    delta = -3; add it along root -> a -> r -> t
---
Query ar
    node total {{3}}
```

Only the key's old contribution is replaced. A zero delta makes no change, and different keys that share nodes retain their own contributions.

## Code

```python
class MapSum:
    def __init__(self):
        self.root = {"children": {}, "total": 0}
        self.values = {}

    def insert(self, key, value):
        delta = value - self.values.get(key, 0)
        self.values[key] = value
        node = self.root
        node["total"] += delta
        for ch in key:
            children = node["children"]
            if ch not in children:
                children[ch] = {"children": {}, "total": 0}
            node = children[ch]
            node["total"] += delta

    def sum(self, prefix):
        node = self.root
        for ch in prefix:
            node = node["children"].get(ch)
            if node is None:
                return 0
        return node["total"]
```

## Complexity

An insertion or query takes expected O(L) time for its key or prefix length, including string hashing. The trie and stored keys use O(S) space for the total length `S` of distinct inserted keys. Only O(1) traversal state is needed per operation.

## Mistakes and edge cases

- Adding the new value instead of the delta double-counts overwritten keys.
- A key may itself be a prefix of another key; both contributions belong in that node.
- An unknown path has sum zero, even when other nearby prefixes exist.
- The root is updated too, so this implementation also supports an empty-prefix total.

## Variations

- Support removal by applying the negative of the old value.
- Maintain both a count and a sum to answer prefix averages.
- Use a dictionary scan when queries are rare and memory is more important.

=== card | 211
time: 30 min

## The problem

Build a word collection supporting additions and pattern searches. In a search, a dot matches exactly one lowercase letter, while every other character must match literally. For stored words `["bad", "bag"]`, `ba.` succeeds and `b..s` fails.

## Constraints and what they imply

Added words are nonempty lowercase strings; patterns have the same alphabet plus the dot wildcard. Matching must consume the whole word, so a shorter stored prefix is not enough. Repeated additions have no effect on membership. Wildcards may branch across many possible letters rather than following one deterministic path.

## Brute force

Keep words in a set and compare a pattern with every word of equal length, allowing a dot to match any character. With `n` candidates and pattern length `L`, a search can take O(nL) time. Length buckets avoid unrelated lengths but still repeat comparisons for shared prefixes.

## The insight

Share stored prefixes in a trie with terminal markers. At pattern index `i`, a state is a node representing exactly the first `i` matched characters. A literal follows its one matching edge; a dot considers all children. After the last pattern character, accept only terminal nodes. The branching search enumerates all and only words consistent with the pattern.

## Optimal solution, traced

```steps
Store bad and bag; search ba.
    b then a selects the shared node
---
The dot tries both outgoing letters
    d and g each lead to a terminal
    result {{True}}
---
Search b..s
    no fourth edge exists below either word
    result {{False}}
```

Each search state consumes one character, so the traversal cannot accept a word of the wrong length. An explicit stack avoids recursive depth limits.

## Code

```python
class WordDictionary:
    def __init__(self):
        self.root = {"children": {}, "end": False}

    def add_word(self, word):
        node = self.root
        for ch in word:
            children = node["children"]
            if ch not in children:
                children[ch] = {"children": {}, "end": False}
            node = children[ch]
        node["end"] = True

    def search(self, pattern):
        stack = [(self.root, 0)]
        while stack:
            node, i = stack.pop()
            if i == len(pattern):
                if node["end"]:
                    return True
            elif pattern[i] == ".":
                stack.extend((child, i + 1) for child in node["children"].values())
            else:
                child = node["children"].get(pattern[i])
                if child is not None:
                    stack.append((child, i + 1))
        return False
```

## Complexity

Insertion takes expected O(L) time for word length `L` and total trie storage is O(S) for S inserted characters. A search visits at most the nodes through depth `L`; without dots it takes O(L), but with dots it may take O(S) time and O(S) stack space in the worst case. The number of branches is bounded by actual trie nodes, not just the alphabet's theoretical expansion.

## Mistakes and edge cases

- A dot consumes exactly one character, not zero or an arbitrary-length suffix.
- Test the end flag only after the entire pattern is consumed.
- Missing literal edges terminate that branch without creating nodes.
- An empty dictionary rejects every nonempty pattern.

## Variations

- Bucket words by length and compare each candidate directly.
- Return all matching words rather than stopping at the first match.
- Extend the pattern language to support zero-or-more characters, with a different state transition.

=== card | 421
time: 30 min

## The problem

For an array of nonnegative integers, find the largest XOR obtainable by choosing two entries. For `[2, 5, 7]`, the best value is `2 XOR 5 = 7`. The returned value is the XOR, not the indices or the chosen pair.

## Constraints and what they imply

Values fit in 31 nonnegative binary digits, and the original array has at least two entries. Duplicate values are allowed. The implementation also returns zero for an empty array as a defensive extension. Binary comparison is dominated by the highest differing bit: one high set bit outweighs every lower bit combined.

## Brute force

Try each pair and keep its XOR if larger than the current maximum. This takes O(n²) time and O(1) extra space, which is costly for a large array. It ignores that many candidates share the same high-order bits and can be eliminated together.

## The insight

Insert every number into a binary trie, reading from bit 30 down to bit 0. For a fixed number, at each node prefer the child with the opposite bit, giving a 1 in the XOR at that position. If that child is missing, take the same-bit child. The preferred branch, whenever available, beats every possible completion from the other branch because `2^b` exceeds the sum of all lower powers of two.

## Optimal solution, traced

```steps
Insert 2, 5 and 7 using three illustrative bits
    2 = 010; 5 = 101; 7 = 111
---
Query 2 = 010
    choose 1, then 0, then 1: the candidate is 5
    XOR bits {{111}}
---
Other queries cannot exceed binary 111
    maximum {{7}}
```

The path always corresponds to an inserted number, and the greedy argument applies again within the chosen subtree. With at least two inputs, permitting an entry to pair with itself cannot increase the optimum: self-XOR is zero, while every XOR is nonnegative.

## Code

```python
def maximum_xor(nums):
    root = {}
    for number in nums:
        node = root
        for bit in range(30, -1, -1):
            node = node.setdefault((number >> bit) & 1, {})

    best = 0
    for number in nums:
        node = root
        value = 0
        for bit in range(30, -1, -1):
            digit = (number >> bit) & 1
            opposite = digit ^ 1
            if opposite in node:
                value |= 1 << bit
                node = node[opposite]
            else:
                node = node[digit]
        best = max(best, value)
    return best
```

## Complexity

For `B = 31` bits, inserting and querying all entries costs O(nB) expected time, and the trie uses O(nB) space. A walk needs O(1) auxiliary space. For another numeric domain, choose enough bits for every possible input.

## Mistakes and edge cases

- Decide bits from most significant to least significant, not the reverse.
- Choosing the opposite bit is conditional on that child actually existing.
- All equal entries have answer zero; zero itself is a valid entry.
- Negative integers require an explicitly defined fixed-width representation.

## Variations

- Insert only earlier elements as you scan to produce a pair of distinct indices explicitly.
- Store a representative index at each leaf to return the maximizing pair.
- Build sets of masked prefixes to determine the answer bit by bit without a trie.

=== card | 2707
time: 30 min

## The problem

Cover parts of a lowercase string with nonoverlapping words from a dictionary, minimizing how many characters are left uncovered. Dictionary words may be used repeatedly. For `s = "abxc"` and dictionary `["ab", "c"]`, cover `ab` and `c`, leaving only `x`, so the answer is 1.

## Constraints and what they imply

The dictionary contains nonempty lowercase words, and a match must occupy consecutive characters. Not every character needs to be covered. Overlapping matches cannot both be selected, but a word may be reused at different positions. Local longest-match choices can block a better later arrangement, so a global optimization is needed.

## Brute force

At each position, branch between leaving the next character uncovered and choosing each dictionary word that starts there. The recursion may revisit the same suffix through many different choices and has exponential worst-case time. Memoizing suffix answers removes this repeated optimization, but naively testing every dictionary word at every position still repeats prefix comparisons.

## The insight

Let `dp[i]` be the minimum uncovered count in the suffix beginning at `i`, with `dp[n] = 0`. Either leave `s[i]` uncovered, costing `1 + dp[i+1]`, or take a dictionary word ending at `j`, costing `dp[j]`. A trie lists all such word ends by walking forward from `i` until an edge is absent. Fill positions right to left so every needed suffix is already solved.

## Optimal solution, traced

```steps
s = abxc; dictionary = [ab, c]
    dp[4] = 0; c matches at index 3, so dp[3] = 0
---
At index 2, x has no trie edge
    leave x uncovered: dp[2] = 1
---
At index 0, ab ends at 2
    choose dp[2] = {{1}}
```

Every valid covering begins with exactly one of the considered alternatives. The recurrence takes the best of them, so induction from the empty suffix proves the result.

## Code

```python
def min_extra_char(s, dictionary):
    root = {}
    for word in dictionary:
        node = root
        for ch in word:
            node = node.setdefault(ch, {})
        node[None] = True

    n = len(s)
    dp = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        dp[i] = 1 + dp[i + 1]
        node = root
        for j in range(i, n):
            if s[j] not in node:
                break
            node = node[s[j]]
            if None in node:
                dp[i] = min(dp[i], dp[j + 1])
    return dp[0]
```

## Complexity

Let `S` be the dictionary's total length, `n` the string length, and `K` the longest dictionary word. Building costs O(S), and each start walks at most `min(n, K)` trie edges plus a possible failed edge. Expected time is O(S + n · min(n, K + 1)), and space is O(S + n) for the trie and DP.

## Mistakes and edge cases

- A terminal word end is an option, not a reason to stop: a longer match may be better.
- Use `dp[j + 1]`, since the matched character at `j` is covered.
- Empty input has answer zero; with no matches every character is uncovered.
- Empty dictionary words are excluded because they do not advance the position.

## Variations

- Record the chosen transition to reconstruct the covered words and leftovers.
- Give uncovered characters different penalties.
- Replace trie walks with testing a set of dictionary strings at each position.

=== card | 2416
time: 40 min

## The problem

For each word in a list, calculate a score as follows: examine every nonempty prefix of that word, count how many list entries begin with that prefix, and add those counts. Return scores in the original order. For `["ab", "ac", "ab"]`, both `ab` entries score 5 and `ac` scores 4: all three words begin with `a`, while two begin with `ab` and one with `ac`.

## Constraints and what they imply

The inputs are nonempty lowercase words, and the total length can be large enough that repeatedly comparing all pairs is undesirable. Duplicate strings count as separate list entries; a set of unique words would discard necessary multiplicity. A shorter word counts toward another word's prefix only when it actually contains that entire prefix. The empty prefix is not included in the score.

This is a batch problem: all words are known before any scores are returned. Thus there is no need to update prior answers when a new word is added. Instead, first build aggregate counts and then read the finished counts for each original entry.

## Brute force

For every word and every prefix, scan all list entries and test whether each begins with that prefix. If there are `n` words of length at most `K`, this can take O(n²K²) time when creating and comparing prefixes, and it repeats the same prefix count for words sharing a beginning. A somewhat better pairwise common-prefix scan still takes O(n²K) time.

As an alternative, count every explicit prefix in a hash map. In Python, constructing and hashing every sliced prefix can copy and inspect O(K²) characters per word. This matters even though the number of prefixes is only linear in the word length.

## The insight

Represent every distinct nonempty prefix by its trie node. During insertion, increment the count of each node reached by one word. Consequently a node's count is exactly the number of input entries with that prefix, including duplicates. A second walk for a word adds the count at each successive node, which is exactly the sum requested.

Shared paths are what make the savings possible. Two words beginning with the same letters update the same nodes, not separate copies of the prefix. A word ending at a node needs no terminal flag here: counts are associated with all prefixes, not just complete words.

## Optimal solution, traced

```steps
Insert ab, ac, ab
    counts: a = 3, ab = 2, ac = 1
---
Score the first ab
    add a: 3; add ab: 2
    total {{5}}
---
Score ac and the second ab
    totals {{4}} and {{5}}
```

For correctness, fix any prefix `p`. Each list entry contributes one increment at its node if and only if that entry begins with `p`; insertions contribute nothing otherwise. Thus the stored count is exactly the mathematical count for `p`. The second pass visits each nonempty prefix of a word exactly once, so its sum is the desired score.

## Code

```python
def sum_prefix_scores(words):
    root = {"children": {}, "count": 0}
    for word in words:
        node = root
        for ch in word:
            children = node["children"]
            if ch not in children:
                children[ch] = {"children": {}, "count": 0}
            node = children[ch]
            node["count"] += 1

    scores = []
    for word in words:
        node = root
        score = 0
        for ch in word:
            node = node["children"][ch]
            score += node["count"]
        scores.append(score)
    return scores
```

## Complexity

Let `S` be the sum of all word lengths and `n` the number of entries. Both passes process exactly S characters, so time is expected O(S) with dictionary child lookup. There are at most S non-root nodes and O(n) output integers, for O(S + n) space including output. The walk itself holds only a node and a running score.

## Mistakes and edge cases

- Count each occurrence, even if the same string appears more than once.
- Do not add a root count: the empty prefix is excluded.
- The word `a` contributes to prefix `a`, but not to `ab`.
- Preserve input order in the result; trie traversal order would not guarantee it.
- If an empty list is supplied as an extension, the result is an empty list.

## Variations

- Support insertions and deletions by incrementing or decrementing all path counts.
- Ask for the number of words with a particular prefix rather than a sum of counts.
- Return the highest scoring word, specifying how ties should be resolved.

=== card | 212
time: 45 min

## The problem

Given a rectangular grid of lowercase letters and a list of distinct lowercase words, return the words that can be formed by a path through horizontally or vertically adjacent cells. A path may not reuse a cell within the same word. Report each found word once, in any order. On the grid `[["a", "b"], ["c", "d"]]`, `ab` and `ac` are present, but `aba` is not because the path would revisit the first cell.

## Constraints and what they imply

The original task supplies a nonempty board and distinct nonempty words; the grid can contain the same letter in many different cells. Movement is not diagonal, and visited cells are local to the current path, not permanently unavailable to other searches. A shared word prefix may correspond to many possible grid paths, all of which can matter.

The maximum word length is bounded in the original problem, so recursion depth is limited by that length. The board may still admit exponentially many candidate paths of that length. Output order is not specified; the search may therefore emit a word immediately when it first finds a terminal.

## Brute force

For each dictionary word independently, start a backtracking search from each board cell, advancing only if the next letter matches and marking cells for the current path. With `N` cells, `W` words and maximum length `L`, a loose bound is O(W · N · 4 · 3^(L-1)) time. The first step has up to four directions and later steps have at most three because the immediately previous cell is occupied.

This approach is correct but repeats the same grid exploration for different words with common prefixes. Merely marking a letter as globally visited would be wrong: the same cell can participate in another path or a different answer.

## The insight

Build a trie over all words and search the board while carrying the current trie node. If the next board letter is not an outgoing edge, no dictionary word can extend that path, so stop immediately. If the reached node is terminal, report its word and clear that terminal marker. Continue exploring because another word can extend it.

Mark the current cell while exploring neighbours and restore it during backtracking. Once a trie node has no remaining children or terminal word, remove its edge from its parent: no unreported word can use that branch. Clearing a terminal avoids duplicate output even when many grid paths spell the same word.

## Optimal solution, traced

```steps
Board [[a, b], [c, d]]; words [a, ab, ac, aba]
    insert all four words and start at a
---
Node a is terminal
    report {{a}}, clear its terminal, and keep exploring
---
Visit b then try a
    original a is marked, so aba cannot reuse it
    report ab and backtrack
---
Visit c from restored a
    report ac; final set {{a, ab, ac}}
```

For soundness, the DFS reaches a terminal only after following matching adjacent, distinct cells; hence every reported word exists. For completeness, consider a valid path to an unreported word. Its trie edges cannot have been pruned, since each still leads to that terminal. The search starts at its first cell and explores every valid continuation, so it eventually reaches the terminal. Removing a terminal after reporting prevents repetitions without hiding longer words.

## Code

```python
def find_words(board, words):
    root = {}
    for word in words:
        node = root
        for ch in word:
            node = node.setdefault(ch, {})
        node[None] = word

    if not board or not board[0]:
        return []
    rows, cols = len(board), len(board[0])
    found = []

    def visit(r, c, parent):
        ch = board[r][c]
        if ch not in parent:
            return
        node = parent[ch]
        word = node.pop(None, None)
        if word is not None:
            found.append(word)

        board[r][c] = "#"
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                visit(nr, nc, node)
        board[r][c] = ch

        if not node:
            del parent[ch]

    for r in range(rows):
        for c in range(cols):
            visit(r, c, root)
    return found
```

## Complexity

Let `S` be the total dictionary length, `N = rows · cols`, and `L` the maximum word length. Trie construction takes O(S); worst-case search takes O(N · 4 · 3^(L-1)) for `L >= 1`, despite pruning. The trie uses O(S) space, the recursion uses O(min(L, N)) stack space, and the output uses O(W) references to input words. The board is modified temporarily and restored.

## Mistakes and edge cases

- Restore each cell after exploring so other starting paths can use it.
- Clear only the terminal marker, not a node that still leads to longer words.
- Do not allow diagonal movement or reuse within the same path.
- Prune a branch only when its node has no remaining terminal or children.
- The sentinel `#` must not occur in the lowercase board.

## Variations

- Return a coordinate path for each found word as well as the word.
- Search each word separately when the dictionary is very small.
- Count distinct grid paths per word; in that version do not clear a terminal after the first path.

=== card | 1707
time: 45 min

## The problem

You have a list of nonnegative integers and independent queries `(x, limit)`. For each query, choose an array value no greater than `limit` and maximize its XOR with `x`; return `-1` if no value qualifies. Answers must follow the original query order. For numbers `[1, 4, 6]`, queries `(2, 4)` and `(3, 0)` give 6 and -1.

## Constraints and what they imply

Array values, query values, and limits are nonnegative and fit within 31 bits. There may be many queries, and the limit differs between them. The original task has a nonempty array, although the implementation also handles an empty one. Equal array values or equal limits are allowed. A value equal to the limit is eligible.

The queries are independent: reordering them for processing is safe as long as each answer is restored to its input position. Eligibility is monotone in the limit, which is the key property allowing data to be shared between queries rather than rebuilt each time.

An XOR result is compared as an integer, not as a count of differing bits. For example, setting a high bit can outweigh several lower set bits. The trie therefore needs the full fixed-width bit representation, including leading zeroes, so values of different magnitudes remain aligned during every query.

## Brute force

For each query, scan every array value. Discard values greater than the limit, compute XOR for the rest, and keep the maximum or -1. This is straightforward and takes O(nq) time with O(q) output space for `n` values and `q` queries. Large inputs make repeating the eligibility scan the bottleneck.

One could build a separate binary trie for every query's eligible set, but the repeated construction still costs O(nqB) in the worst case for `B` bits. It does not exploit the fact that increasing a limit only adds eligible numbers.

## The insight

Sort the numbers and process queries in increasing limit order, remembering each original index. Before each query, insert every not-yet-inserted number at most that limit into a binary trie. The trie then contains exactly the eligible numbers. If it is empty, the answer is -1.

Otherwise, walk from the highest bit down, preferring an edge opposite the corresponding bit of `x`. That gives a 1 at the most significant undecided XOR position whenever possible. A 1 at bit `b` is worth more than all lower bits together, so no opposite choice at lower positions can compensate for rejecting a feasible opposite edge now.

## Optimal solution, traced

```steps
Numbers [1, 4, 6]; sort queries (3, 0), (2, 4) by limit
    first query has no eligible number
    answer at its original index {{-1}}
---
For limit 4, insert 1 and 4
    6 remains outside the trie
---
Walk x = 2 against eligible numbers
    best partner is 4; 2 XOR 4 = {{6}}
    restore original order: {{[6, -1]}}
```

The sorted insertion pointer establishes the eligibility invariant before every query: all inserted values meet the current limit, and all not yet inserted values exceed it. For the XOR choice, induct on bit positions. The greedy edge fixes the largest possible current XOR bit among remaining candidates; subsequent choices cannot change that bit. Therefore the resulting path yields the maximum among precisely the eligible values.

## Code

```python
def maximize_xor(nums, queries):
    ordered = sorted(nums)
    ranked_queries = sorted((limit, x, i) for i, (x, limit) in enumerate(queries))
    answers = [-1] * len(queries)
    root = {}
    inserted = 0

    for limit, x, index in ranked_queries:
        while inserted < len(ordered) and ordered[inserted] <= limit:
            node = root
            number = ordered[inserted]
            for bit in range(30, -1, -1):
                node = node.setdefault((number >> bit) & 1, {})
            inserted += 1

        if inserted == 0:
            continue
        node = root
        value = 0
        for bit in range(30, -1, -1):
            digit = (x >> bit) & 1
            opposite = digit ^ 1
            if opposite in node:
                value |= 1 << bit
                node = node[opposite]
            else:
                node = node[digit]
        answers[index] = value
    return answers
```

## Complexity

For `B = 31`, sorting takes O(n log n + q log q), while insertions and walks take O((n + q)B) expected time. The trie uses O(nB) space; sorted copies, indexed queries, and answers add O(n + q). The implementation does not mutate the caller's input lists.

## Mistakes and edge cases

- Use `<= limit`, not a strict inequality.
- An empty eligible set returns -1, not zero; a real maximum may be zero.
- Store query indices before sorting, or the result order will be wrong.
- Insert each number only once as the limit advances; never remove earlier eligible numbers.
- Choose a bit width covering both array numbers and query `x` values.

## Variations

- Return the maximizing array value by recording a representative at each leaf.
- Support online queries using trie nodes that record subtree minimum values.
- Apply the same offline sorting idea to other queries with a monotone eligibility threshold.

=== card | 336
time: 45 min

## The problem

Given a list of distinct strings, return every ordered pair of different indices `(i, j)` for which `words[i] + words[j]` reads identically left to right and right to left. The output order is irrelevant, but the direction of each pair matters. For `["ab", "ba", "a", ""]`, valid pairs include `(0, 1)`, `(1, 0)`, `(2, 3)`, and `(3, 2)`.

## Constraints and what they imply

Each word consists of lowercase letters, except that an empty string may also appear. Words are distinct, so a word-to-index dictionary has at most one index for each spelling. Indices in a pair must differ. An empty string pairs in both directions with every other word that is itself a palindrome.

The output can contain many pairs, and they must not be repeated. The algorithm should find pairs when either word is longer, when the two lengths are equal, and when one is empty. A simple word lookup is useful, but a full reversal lookup alone misses cases where the extra letters form a palindrome.

## Brute force

Try all `n(n-1)` ordered index pairs, form each concatenation and compare it with its reverse. With maximum word length `K`, this takes O(n²K) time and O(K) temporary space per test, excluding the output. This can spend substantial time inspecting pairs whose characters make a match impossible from the outset.

Instead, examine where one word must align against the reverse of the other. The unpaired remainder, if any, must itself be a palindrome. This turns the partner search at each split into a dictionary lookup.

## The insight

Map every whole word to its index. Split a current word into `left` and `right` at every position. If `left` is a palindrome, then `reverse(right)` can be placed before the current word. If `right` is a palindrome, then `reverse(left)` can be placed after it. In either case, accept only an existing partner with a different index.

For the second rule, skip the split with an empty `right`. The first rule already produces every pair of exact reversed words at its empty-`left` split. Skipping that one case prevents duplicates while retaining empty-string pairs through the other applicable split. Uniqueness of the input words makes each dictionary lookup unambiguous.

## Optimal solution, traced

```steps
words = [ab, ba, a, empty]
    build a lookup from each word to its index
---
Split ab as empty | ab
    empty is palindromic; reverse(ab) = ba
    emit {{(1, 0)}}
---
Split a as a | empty
    a is palindromic; reverse(empty) is present
    emit {{(3, 2)}}
---
Split a as empty | a using the second rule
    a is palindromic and reverse(empty) is present
    emit {{(2, 3)}}
```

Why are these rules complete? For any palindromic concatenation `A + B`, compare the two ends. If `A` is longer than `B`, its first `len(B)` characters must be `reverse(B)` and its remaining suffix must be palindromic; the second rule discovers `(A, B)` while scanning `A`. If `B` is at least as long, its last `len(A)` characters must be `reverse(A)` and its remaining prefix must be palindromic; the first rule discovers the pair while scanning `B`.

Conversely, either rule constructs a concatenation with mirrored outer pieces and a palindromic middle, so every emitted pair is valid. Equal-length reverse pairs belong to both descriptions, hence the explicit skipped split; unequal lengths belong to only one. Checking indices rejects self-pairs, including a palindrome paired with itself.

## Code

```python
def palindrome_pairs(words):
    index = {word: i for i, word in enumerate(words)}
    result = []
    for i, word in enumerate(words):
        for cut in range(len(word) + 1):
            left, right = word[:cut], word[cut:]
            if left == left[::-1]:
                partner = index.get(right[::-1])
                if partner is not None and partner != i:
                    result.append((partner, i))
            if right and right == right[::-1]:
                partner = index.get(left[::-1])
                if partner is not None and partner != i:
                    result.append((i, partner))
    return result
```

## Complexity

With total word length `S`, maximum length `K`, and `P` returned pairs, each split can copy, reverse, compare, and hash O(K) characters. There are O(S + n) splits, giving expected O(n(K + 1)² + P) time as a simple bound. The index and its referenced words use O(S + n), temporary slices use O(K), and output uses O(P) space.

## Mistakes and edge cases

- The pair is ordered: `(i, j)` and `(j, i)` are different answers.
- Never pair an index with itself, even if its word is a palindrome.
- Do not omit the empty string: it pairs with every other palindrome in both directions.
- Skip exactly the empty-right second-rule case to avoid duplicate reverse-word pairs.
- The single-index lookup relies on distinct input words; duplicates would require storing all indices.

## Variations

- Store reversed words in a trie with lists of palindromic remainders.
- Count valid ordered pairs without materializing the full result.
- Allow duplicate words by mapping each spelling to a list of indices and excluding only identical indices.
