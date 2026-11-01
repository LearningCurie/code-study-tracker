---
key: strings
name: String algorithms
stage: engineer
summary: Compact recaps of the string toolkit: what Python strings really cost, palindromes by centre expansion, rolling hashes, KMP, the Z-function and small parsers and encodings, with the real tools that use them.
why: String problems hide familiar techniques behind text: counting, windows, two pointers, DP. The few ideas that are genuinely about strings are worth knowing cold: expanding around centres, comparing substrings in O(1) with a rolling hash, and the prefix and Z functions, which find patterns, borders and periods in linear time. They are also the ideas behind real tools: grep skips through text with Boyer-Moore, rsync finds moved blocks with a rolling checksum, backup tools cut files at content-defined boundaries with a Rabin fingerprint, and intrusion detectors match thousands of signatures at once with Aho-Corasick. These cards are recaps: the mechanics, the invariant, a template to reproduce and the traps.
outcomes:
- Predict the real cost of Python string operations (slicing, concatenation, `in`, hashing) and pick counts, a canonical shape or join accordingly
- Find the longest palindromic substring and count all of them by expanding around the 2n - 1 centres, and outline Manacher's linear-time improvement
- Compare substrings in O(1) with prefix hashes, choose a modulus and base that make collisions negligible, and always verify on a hit
- Build the prefix function and use it for O(n + m) matching, borders and periods
- Compute the Z-function with its Z-box and use either function on pattern + separator + text
- Write small tokenisers and length-prefixed encodings that survive any input characters
cues:
- "Find a pattern in a long text", "first occurrence", "how many times does p occur", with n large enough that O(nm) is too slow
- Repeated, periodic or rotated strings; "longest prefix that is also a suffix"
- Palindromic substrings or prefixes
- Many substring comparisons, or "longest substring that appears twice"
- Parsing or producing a format: numbers, versions, words, encoded lists
traps:
- Building strings with += in a loop, or slicing inside a loop, and getting O(n^2) without noticing
- Trusting a hash match without comparing the actual text, or using a small modulus such as 10^9 + 7 with millions of substrings
- In KMP, falling back with k = pi[k] instead of pi[k - 1], or forgetting to fall back after a full match
- Using a separator in pattern + separator + text that can occur in the input
- Forgetting even-length centres when expanding palindromes
systems:
- GNU grep searches for literal strings with Boyer-Moore, skipping input bytes, and looks for line boundaries only around a match (Mike Haertel's 2010 note on why GNU grep is fast)
- CPython's str.find and `in` use a Boyer-Moore-Horspool hybrid, switching to the Crochemore-Perrin Two-Way algorithm for long needles to guarantee linear time
- rsync finds blocks of the old file at any offset of the new one with a weak rolling checksum updated in O(1) per byte, confirming candidates with a strong hash
- restic cuts files into content-defined chunks with a Rabin fingerprint over a 64-byte window, so an insertion changes only nearby chunks; Suricata matches many signatures at once with Aho-Corasick or Hyperscan
further:
- Notes · 40 min | Jeff Erickson: String matching notes, PDF pages 2-10 (Karp-Rabin fingerprinting, then KMP as an automaton and its failure function) | https://jeffe.cs.illinois.edu/teaching/algorithms/notes/07-strings.pdf
- Article · 10 min | Mike Haertel: why GNU grep is fast | https://lists.freebsd.org/pipermail/freebsd-current/2010-August/019310.html
- Article · 10 min | rsync technical report: checksum searching | https://rsync.samba.org/tech_report/node4.html
- Article · 15 min | cp-algorithms: Aho-Corasick, construction of the automaton | https://cp-algorithms.com/string/aho_corasick.html#construction-of-an-automaton
bank: strings
---

=== recap | Python strings: real costs, counts and canonical shapes | 10 min
goal: Predict what Python string operations cost, recognise which technique a string problem needs, and use counts or a first-occurrence shape for equivalence questions
tag: str-count | Counts and canonical shapes
link: Python FAQ: concatenating many strings | https://docs.python.org/3/faq/programming.html#what-is-the-most-efficient-way-to-concatenate-many-strings-together | 2 min: why repeated += is quadratic in general and why join or io.StringIO is linear
practice: 205

> [!key]
> A Python `str` is an immutable array of code points, so indexing and `len` are O(1) but every slice, `+` and `replace` builds a new string. Most "string problems" are really counting, window, two-pointer, DP or parsing problems; the genuinely string-specific tools are in the next cards. For "are these the same up to rearrangement or relabelling?" compare **counts** or a **canonical shape**.

## Internals

- **Storage** (PEP 393): each string stores every code point in 1, 2 or 4 bytes, chosen by its widest character. `s[i]` and `len(s)` are O(1); `len` counts code points, not bytes or visible characters.
- **Immutability**: `s[i:j]` copies j - i characters. `res += piece` in a loop is O(total^2) in general (CPython sometimes extends in place when nothing else references the string; do not rely on it). Collect pieces in a list and `"".join` them once.
- **Hashing**: a string's hash is computed once and cached in the object, so repeated dict lookups with the same key object are cheap; equality is O(L) at worst.
- **Searching**: `in`, `find`, `count` and `replace` use CPython's fastsearch, a Boyer-Moore-Horspool hybrid that skips ahead on mismatches, switching to the Two-Way algorithm for long needles so the worst case stays linear. For one search, `pat in text` beats any hand-written loop.
- **Counting**: `collections.Counter(s)` counts in C; for lowercase ASCII a 26-slot list indexed by `ord(ch) - 97` is smaller and lets you compare counts in O(26).

| The statement says | Usually means |
|---|---|
| anagram, same letters, rearrange | counts |
| longest or shortest substring with a condition | sliding window |
| two strings, subsequence, edits | DP on prefixes |
| nested brackets, encoded repeats, expressions | stack or parser |
| palindromic substring | expand around centres |
| find, occurrences, period, prefix equals suffix | prefix function, Z-function or rolling hash |

## Template

```python
from collections import Counter


def counts26(s):
    """Letter counts for lowercase ASCII; compare two of these in O(26)."""
    c = [0] * 26
    for ch in s:
        c[ord(ch) - 97] += 1
    return c


def shape(s):
    """First-occurrence pattern: equal shapes mean a one-to-one letter mapping exists."""
    first = {}
    return tuple(first.setdefault(ch, len(first)) for ch in s)


def same_letters(a, b):
    return Counter(a) == Counter(b)


def build(pieces):
    return "".join(pieces)             # one O(total) copy, never += in a loop
```

## Worked example

Is there a one-to-one letter mapping from "noon" to "deed", and from "noon" to "dead"?

```steps
shape("noon"): n is new (0), o is new (1), o seen (1), n seen (0)
    noon  ->  ({{0}}, {{1}}, 1, 0)
---
shape("deed"): d is 0, e is 1, e again 1, d again 0. Same shape, so n->d, o->e works both ways
    deed  ->  (0, 1, 1, 0)      equal to noon's shape
---
shape("dead"): d 0, e 1, a is new (2), d 0. The shapes differ at position 2
    dead  ->  (0, 1, {{2}}, 0)      noon has 1 here: o would map to e and a
```

## Pitfalls

- **Quadratic building**: `+=` or `s = s[:i] + c + s[i+1:]` inside a loop. Use a list of characters, then join.
- **One-way mappings**: checking only s to t lets "ab" map to "cc". Shapes, or two dicts, check both directions.
- **ASCII assumptions**: `ord(ch) - 97` breaks on capitals, digits and accents. Normalise with `casefold()`, and use `unicodedata.normalize("NFC", s)` when "é" may arrive as one code point or two.
- **Identity**: compare strings with `==`, never `is`.

## Quick check

Q: What is shape("abca"), and is there a one-to-one mapping from "abca" to "zyxz"?
A: (0, 1, 2, 0). "zyxz" also has shape (0, 1, 2, 0), so yes: a to z, b to y, c to x.

> [!know]
> You now know what Python string operations really cost and how counts and canonical shapes answer equivalence questions in O(n).

=== recap | Palindromes: expanding around 2n - 1 centres | 10 min
goal: Find the longest palindromic substring and count all of them in O(n^2) time and O(1) space by expanding around every centre, and describe how Manacher's algorithm reaches O(n)
tag: str-palin | Expand around centres
link: cp-algorithms: Manacher's algorithm | https://cp-algorithms.com/string/manacher.html#manachers-algorithm | 10 min: 'Manacher's algorithm' (reusing the mirror inside the rightmost palindrome) and 'Working with parities' (one pass for odd and even lengths)
practice: 5, 647

> [!key]
> Every palindrome is symmetric around a **centre**: a character (odd length) or the gap between two characters (even length), so a string of length n has **2n - 1 centres**. From each centre, grow outwards while the two ends match. The maximal palindrome at each centre gives the longest one, and every successful growth step is one more palindrome, so the same loop also counts them.

## Internals

**Why expanding is enough**: if s[lo..hi] is a palindrome, so is s[lo+1..hi-1], with the same centre. The palindromes around one centre are therefore nested, and growing until the first mismatch finds all of them: a maximal span of length L contains (L + 1) // 2 palindromes centred there.

**Cost**: each centre costs O(1 + radius). The total is O(n^2) in the worst case (a string of one repeated letter, where every centre grows to the nearest edge) and close to O(n) on typical text, with O(1) extra space. Compare: checking all O(n^2) substrings with `t == t[::-1]` costs O(n^3); a DP table of "is s[i..j] a palindrome" costs O(n^2) time **and** O(n^2) memory.

**Manacher in outline**: keep the palindrome that reaches furthest right, [l, r]. For a new centre i inside it, the mirror centre j = l + r - i has already been expanded, and inside [l, r] the text around i mirrors the text around j, so i's radius is at least min(radius[j], r - i). Start expanding from there; every comparison that succeeds pushes r to the right, and r never moves left, so the total work is O(n). Interleaving a separator (`#a#b#a#`) turns every centre into a character so one loop handles both parities.

For a whole string, `s == s[::-1]` is the fastest check in Python (C speed). Use two pointers when characters must be skipped or one deletion is allowed.

## Template

```python
def expand(s, lo, hi):
    """Grow around the centre (lo, hi) while the ends match; return the widest palindrome as (lo, hi)."""
    while lo >= 0 and hi < len(s) and s[lo] == s[hi]:
        lo -= 1
        hi += 1
    return lo + 1, hi - 1                 # an empty span (hi < lo) when even and s[lo] != s[hi]


def centre_spans(s):
    """The maximal palindrome around each of the 2n - 1 centres."""
    for c in range(len(s)):
        yield expand(s, c, c)             # odd length: centred on s[c]
        if c + 1 < len(s):
            yield expand(s, c, c + 1)     # even length: centred on the gap after s[c]


spans = list(centre_spans("cbbcabac"))
lo, hi = max(spans, key=lambda span: span[1] - span[0])    # longest: s[3:8] == "cabac"
count = sum((hi - lo + 2) // 2 for lo, hi in spans)        # all palindromic substrings: 12
```

## Worked example

s = "cbbcabac" (indices 0 to 7). Five of the fifteen centres, including the two that matter.

```steps
Centre on s[0] = "c": s[-1] does not exist, so the span is just "c": 1 palindrome
    index   0 1 2 3 4 5 6 7
    s      {{c}} b b c a b a c
---
Gap between s[1] and s[2]: b == b gives "bb"; then s[0] == s[3] (c == c) gives "cbbc"; then the left end runs out
    index   0 1 2 3 4 5 6 7
    s      {{c b b c}} a b a c      2 palindromes: bb, cbbc
---
Gap between s[2] and s[3]: b != c, so nothing: 0 palindromes
    index   0 1 2 3 4 5 6 7
    s       c b {{b c}} a b a c
---
Centre on s[5] = "b": a == a gives "aba", c == c gives "cabac", then s[2] = b vs s[8]: out of range
    index   0 1 2 3 4 5 6 7
    s       c b b {{c a b a c}}      3 palindromes: b, aba, cabac
---
After all 15 centres: longest is "cabac" (3..7); count = 8 single letters + bb + cbbc + aba + cabac = 12
    index   0 1 2 3 4 5 6 7
    s       c b b {{c a b a c}}
```

## Pitfalls

- **Odd centres only**: misses "bb" and "cbbc". Every problem needs both parities (or Manacher's separator trick).
- **Off by one on return**: the loop exits one step past the last match, so return (lo + 1, hi - 1).
- **Slicing inside the loop**: building s[lo:hi+1] at every step turns O(n^2) into O(n^3); keep indices and slice once at the end.
- **Palindromic subsequence is different**: characters need not be adjacent, which is an interval DP, not centre expansion.

## Quick check

Q: How many palindromic substrings does "aaa" have, and which centres produce them?
A: Six. Odd centres give a, a, a and "aaa" (the middle centre expands twice); the two gaps give "aa" each.

> [!know]
> You now know how to find and count palindromic substrings by expanding around 2n - 1 centres, and why Manacher's mirror trick makes it linear.

=== recap | Rolling hash and Rabin-Karp | 12 min
goal: Hash every window or substring in O(1) with polynomial prefix hashes, choose a modulus and base that make collisions negligible, and verify every hit
tag: str-hash | Rolling hash
link: cp-algorithms: String hashing | https://cp-algorithms.com/string/string-hashing.html#fast-hash-calculation-of-substrings-of-given-string | 10 min: 'Calculation of the hash of a string', 'Fast hash calculation of substrings of given string' (prefix hashes) and 'Improve no-collision probability' (why 10^9-sized moduli fail and how two hashes help)
link: rsync technical report: the rolling checksum | https://rsync.samba.org/tech_report/node3.html | 3 min: rsync's weak checksum and the two recurrences that slide it one byte in O(1)
practice: 1044

> [!key]
> Treat a string as a number in base B: hash(c0 c1 ... c(L-1)) = c0 * B^(L-1) + ... + c(L-1), modulo a large prime M. Sliding the window one character costs O(1): remove the leading character's term, multiply by B, add the new character. With **prefix hashes** any substring's hash is O(1) after O(n) preprocessing. Equal strings always have equal hashes; unequal strings collide only rarely if M is large and B is **random**, so compare the actual text on every hit and the answer is exact.

## Internals

**Sliding**: if h is the hash of s[i:i+L], then the hash of s[i+1:i+L+1] is ((h - s[i] * B^(L-1)) * B + s[i+L]) mod M. **Prefix hashes**: with H[0] = 0 and H[i+1] = H[i] * B + s[i], the hash of s[i:j] is H[j] - H[i] * B^(j-i) (mod M).

**Collisions**: for two different strings of length L and a base chosen uniformly at random, a collision means B is a root of a nonzero polynomial of degree below L, which has fewer than L roots, so the probability is below L / M. With M = 2^61 - 1 (a Mersenne prime) and L = 10^5 that is under 10^-13 per comparison. Storing N hashes in a set is a birthday problem: expect about N^2 / (2M) colliding pairs, which is about 500 for N = 10^6 and M near 10^9. Hence: a 61-bit prime (Python's big integers make this easy), or **double hashing** (two independent moduli and bases, standard in C++ and Java where 64-bit products overflow); a base drawn at run time, so nobody can craft colliding inputs (with the "free" modulus 2^64, a known family of strings built from the Thue-Morse sequence collides for every base); and a real comparison before reporting a match.

**Cost**: O(n + m) expected for Rabin-Karp, but every true match is verified in O(m), so "aaa" in "aaaa..." costs O(nm); KMP and Z guarantee O(n + m). Hashing wins when you compare **many** substrings: duplicates of length L, longest repeated substring (binary search on L), equality of arbitrary ranges.

**In real tools**: rsync's receiver sends a weak 32-bit rolling checksum (two running sums modulo 2^16, inspired by Adler-32) and a strong checksum per block; the sender slides the weak one over **every byte offset** of its file and computes the strong one only for candidates. restic cuts chunks where a Rabin fingerprint of the last 64 bytes matches a pattern, so an insertion moves only nearby boundaries.

## Template

```python
import random

MOD = (1 << 61) - 1                       # Mersenne prime
BASE = random.randrange(256, MOD - 1)     # random per run: no input can be crafted against it


class PrefixHash:
    """Hash of any substring s[i:j] in O(1) after O(n) preprocessing."""

    def __init__(self, s):
        self.h = [0] * (len(s) + 1)       # h[i] = hash of s[:i]
        self.p = [1] * (len(s) + 1)       # p[i] = BASE**i % MOD
        for i, ch in enumerate(s):
            self.h[i + 1] = (self.h[i] * BASE + ord(ch)) % MOD
            self.p[i + 1] = self.p[i] * BASE % MOD

    def get(self, i, j):
        return (self.h[j] - self.h[i] * self.p[j - i]) % MOD


def rabin_karp(text, pat):
    """All start indices of pat in text. Every hash hit is checked, so the answer is exact."""
    n, m = len(text), len(pat)
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []
    target = h = 0
    for k in range(m):
        target = (target * BASE + ord(pat[k])) % MOD
        h = (h * BASE + ord(text[k])) % MOD
    top = pow(BASE, m - 1, MOD)           # weight of the character that leaves the window
    out = []
    for i in range(n - m + 1):
        if h == target and text[i:i + m] == pat:
            out.append(i)
        if i + m < n:
            h = ((h - ord(text[i]) * top) * BASE + ord(text[i + m])) % MOD
    return out
```

## Worked example

Find "159" in "31415926" with a deliberately tiny modulus: B = 10, M = 13, digits as values. hash("159") = 159 mod 13 = 3, and B^2 mod 13 = 9.

```steps
Window 314: 314 mod 13 = 2, not the target 3
    text    {{3 1 4}} 1 5 9 2 6        h = 2
---
Slide: drop 3, add 1: (2 - 3 * 9) * 10 + 1 = -249, and -249 mod 13 = 11 (= 141 mod 13)
    text    3 {{1 4 1}} 5 9 2 6        h = 11
---
Slide: (11 - 1 * 9) * 10 + 5 = 25, mod 13 = 12 (= 415 mod 13)
    text    3 1 {{4 1 5}} 9 2 6        h = 12
---
Slide: (12 - 4 * 9) * 10 + 9 = -231, mod 13 = 3: a hit. Compare the text: "159" == "159", match at 3
    text    3 1 4 {{1 5 9}} 2 6        h = {{3}}
---
Slide twice more: 592 gives 7, then 926 gives 3: another hit, but "926" != "159". A collision, caught by the comparison
    text    3 1 4 1 5 {{9 2 6}}        h = {{3}}   rejected
```

With M = 2^61 - 1 and a random base, that second hit would essentially never happen; the comparison makes the answer exact either way.

## Pitfalls

- **Negative remainders** in C++, Java or Go: `(a - b) % M` can be negative; add M before taking the remainder. Python's `%` is already non-negative.
- **Overflow**: in 64-bit languages the product of two values below 2^61 overflows; use 128-bit multiplication or two 31-bit moduli.
- **Skipping verification**, or using a small or famous modulus with a fixed base on adversarial input.
- **Comparing hashes of different lengths**: with prefix hashes, "a" and "\x00a" can collide; only compare equal-length substrings, or include the length in the key.
- **Python's `hash()`** of a slice still costs O(L), and it is randomised per process: fine within one run, never for values you store.

## Quick check

Q: Why must the base be random, and what does verifying each hit cost in the worst case?
A: With a fixed base (and modulus), someone can compute two different strings with equal hashes in advance; a base chosen at run time makes any fixed pair collide with probability below L / M. Verification costs O(m) per hit, so a text full of true matches costs O(nm) in total.

> [!know]
> You now know how to slide and query polynomial hashes in O(1), why a 61-bit prime with a random base is safe, and why every hit is verified.

=== recap | KMP and the prefix function | 12 min
goal: Build the prefix function in O(m) with its fallback chain, match a pattern in O(n + m) without moving backwards in the text, and read borders and periods from it
tag: str-kmp | Prefix function (KMP)
link: cp-algorithms: Prefix function, Knuth-Morris-Pratt | https://cp-algorithms.com/string/prefix-function.html#efficient-algorithm | 12 min: 'Efficient Algorithm' (the two optimisations that give O(n)) and 'Search for a substring in a string' (the pattern + separator + text form)
practice: 28, 459, 1392, 214

> [!key]
> pi[i] is the length of the longest **border** of s[:i+1]: a proper prefix that is also a suffix. When a match of k characters fails, the pattern can resume at pi[k-1] characters instead of starting over, because that much of what you just matched is already a prefix of the pattern. The text pointer never moves backwards, so matching costs O(n + m), and pi itself is built by the same loop in O(m).

## Internals

**Building pi**: keep k = pi[i-1], the border you are trying to extend. If s[i] == s[k], the border grows to k + 1. If not, fall back to the next shorter border of the same prefix, which is pi[k-1], and try again; stop at k = 0. The borders of a string form a chain k, pi[k-1], pi[pi[k-1]-1], ..., so the fallback visits every candidate in decreasing order and the first that extends is the longest.

**Why O(m)**: k rises by at most 1 per index and every fallback lowers it by at least 1, so the total number of fallbacks is at most the total number of rises: at most m. The same argument bounds matching by O(n + m).

**Matching**: run the identical loop with the text as input and the pattern as the thing being extended; when k reaches m, report a match at i - m + 1 and fall back to pi[m-1] so overlapping matches are found. Equivalently, compute pi of pattern + "\x00" + text and report every position where pi equals m (the separator must not occur in either string).

**What else pi tells you**: s[:pi[n-1]] is the longest prefix that is also a suffix. p = n - pi[n-1] is the smallest period, and s is a whole repetition of a block exactly when pi[n-1] > 0 and n % p == 0. The longest palindromic prefix of s is pi's last value for s + "#" + reversed(s).

**In real tools**: KMP is a worst-case guarantee and a source of structure, not what fast searchers run. CPython's `str.find` and GNU grep skip ahead with Boyer-Moore-style shift tables (CPython switches to Two-Way for long needles). Aho-Corasick is KMP generalised to a trie of many patterns, with failure links playing the role of pi; Suricata offers it as a multi-pattern matcher.

## Template

```python
def prefix_function(s):
    """pi[i] = length of the longest proper prefix of s[:i + 1] that is also its suffix."""
    pi = [0] * len(s)
    k = 0                                  # the border being extended
    for i in range(1, len(s)):
        while k > 0 and s[i] != s[k]:
            k = pi[k - 1]                  # next shorter border
        if s[i] == s[k]:
            k += 1
        pi[i] = k
    return pi


def kmp_search(text, pat):
    """All start indices of pat in text in O(n + m)."""
    if not pat:
        return list(range(len(text) + 1))
    pi = prefix_function(pat)
    out, k = [], 0                         # k = characters of pat matched so far
    for i, ch in enumerate(text):
        while k > 0 and ch != pat[k]:
            k = pi[k - 1]
        if ch == pat[k]:
            k += 1
        if k == len(pat):
            out.append(i - k + 1)
            k = pi[k - 1]                  # keep going: matches may overlap
    return out
```

## Worked example

Build pi for the pattern "abacabab", then match it in "abacabacabab".

```steps
i = 1, 2: "b" cannot extend the empty border (pi 0); "a" matches s[0] (pi 1)
    s    a b a c a b a b
    pi   0 0 {{1}}
---
i = 3: "c" != s[1] = "b", fall back to k = pi[0] = 0; "c" != s[0]: pi 0
    s    a b a {{c}} a b a b
    pi   0 0 1 {{0}}
---
i = 4, 5, 6: a, b, a each extend the border: "a", "ab", "aba"
    s    a b a c {{a b a}} b
    pi   0 0 1 0 {{1 2 3}}
---
i = 7: "b" != s[3] = "c", so fall back to k = pi[2] = 1; "b" == s[1]: k = 2. The border is "ab"
    s    a b a c a b a {{b}}
    pi   0 0 1 0 1 2 3 {{2}}
```

```steps
Matching: text[0..6] = "abacaba" equals the pattern's first 7 characters: k = 7
    text  {{a b a c a b a}} c a b a b
    pat   {{a b a c a b a}} b
---
text[7] = "c" but pat[7] = "b": mismatch. Fall back to k = pi[6] = 3, since "aba" is both a suffix of what matched and a prefix of pat
    text  a b a c {{a b a}} c a b a b
    pat           {{a b a}} c a b a b
---
Compare the same text character again: text[7] = "c" == pat[3]: k = 4. The text pointer never went back
    text  a b a c a b a {{c}} a b a b
    pat           a b a {{c}} a b a b
---
text[8..11] = "abab" extend k to 8 = m: match at 11 - 8 + 1 = 4, then k = pi[7] = 2 for overlapping matches
    text  a b a c {{a b a c a b a b}}
    pat           {{a b a c a b a b}}
```

## Pitfalls

- **k = pi[k] instead of pi[k - 1]**: pi is indexed by the last position of the matched prefix, which is k - 1.
- **`if` instead of `while`** for the fallback: one step back is not always enough.
- **No fallback after a full match**: the next comparison reads pat[m] and raises IndexError, or overlapping matches are lost.
- **A separator that occurs in the data** when using pattern + separator + text; pick a character outside the alphabet, or run the two-phase version above.

## Quick check

Q: What is the prefix function of "aabaaab", and what are its smallest period and longest border?
A: [0, 1, 0, 1, 2, 2, 3]. The longest border is "aab" (length 3), so the smallest period is 7 - 3 = 4; since 7 % 4 != 0, the string is not a whole repetition of a block.

> [!know]
> You now know how to build the prefix function with its fallback chain, match in O(n + m), and read borders and periods from it.

=== recap | The Z-function and its Z-box | 10 min
goal: Compute z[i], the longest common prefix of s and s[i:], in O(n) by reusing the rightmost matched segment, and use it for matching and prefix-comparison sums
tag: str-z | Z-function
link: cp-algorithms: Z-function | https://cp-algorithms.com/string/z-function.html#efficient-algorithm-to-compute-the-z-function | 10 min: 'Efficient algorithm to compute the Z-function' (the [l, r) segment), its O(n) argument, and 'Search the substring' on pattern + separator + text
practice: 2223

> [!key]
> z[i] is the length of the longest common prefix of s and the suffix starting at i. The algorithm keeps the **Z-box** [l, r): the rightmost segment known to equal a prefix of s. For an i inside the box, s[i:r] is a copy of s[i-l:r-l], so z[i] starts at min(r - i, z[i - l]) for free; only characters beyond r are compared, and r never moves left, so the whole array costs O(n).

## Internals

**Three cases** for each i from 1 to n - 1:

- **i is outside the box** (i >= r): compare from scratch, s[0] with s[i], s[1] with s[i+1], ...
- **Inside, and the copied value fits** (z[i - l] < r - i): the answer is exactly z[i - l]; the mismatch that stopped it is also inside the box. No comparisons succeed.
- **Inside, and the copy reaches the box edge** (z[i - l] >= r - i): start at r - i and keep comparing past r.

Whenever the match for i ends beyond r, the box becomes [i, i + z[i]).

**Why O(n)**: every successful comparison moves r one step to the right (it compares s at a position at or beyond r), r only grows, and it stops at n. Each i adds at most one failed comparison. Total: O(n).

**Uses**: matching (compute z of pattern + separator + text; a position with z equal to m is a match); the sum of all z values plus n is the total length of all prefix-suffix matches (LeetCode 2223); a period p of s exists where p + z[p] == n. The prefix function and the Z-function carry the same information and can be converted into each other in O(n); many people find the Z-box easier to reason about, while KMP's form streams naturally (it never needs the text in advance).

## Template

```python
def z_function(s):
    """z[i] = length of the longest common prefix of s and s[i:]; z[0] is left as 0."""
    n = len(s)
    z = [0] * n
    l = r = 0                                  # Z-box: s[l:r] == s[0:r - l]
    for i in range(1, n):
        if i < r:
            z[i] = min(r - i, z[i - l])        # copy from inside the box
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1                          # compare only past what is known
        if i + z[i] > r:
            l, r = i, i + z[i]
    return z


def z_search(text, pat, sep="\x00"):
    """Start indices of pat in text; sep must occur in neither string."""
    z = z_function(pat + sep + text)
    m = len(pat)
    return [i - m - 1 for i in range(m + 1, len(z)) if z[i] >= m]
```

## Worked example

s = "abaababc". Box [l, r) shown with brackets below the string.

```steps
i = 1, 2 are outside any box: "b" vs "a" fails (z 0); "a" matches s[0], then "a" vs "b" fails (z 1). Box [2, 3)
    i     0 1 2 3 4 5 6 7
    s     a b a a b a b c
    z     0 0 {{1}}
---
i = 3: outside the box. "aba" matches s[0:3], then s[6] = "b" vs s[3] = "a" fails: z = 3, box [3, 6)
    s     a b a {{a b a}} b c
    box         [3     6)
    z     0 0 1 {{3}}
---
i = 4: inside. Copy z[4 - 3] = z[1] = 0, which is less than r - i = 2: z = 0 with no comparisons
    s     a b a a {{b}} a b c
    box         [3     6)
    z     0 0 1 3 {{0}}
---
i = 5: inside. z[5 - 3] = z[2] = 1 reaches the box edge (r - i = 1), so start at 1 and compare past r: s[1] = "b" == s[6], then "a" vs "c" fails. z = 2, box [5, 7)
    s     a b a a b {{a b}} c
    box               [5  7)
    z     0 0 1 3 0 {{2}}
---
i = 6: inside. z[1] = 0 < r - i = 1, so z = 0. i = 7: outside, "c" vs "a" fails, z = 0
    s     a b a a b a {{b c}}
    z     0 0 1 3 0 2 {{0 0}}
```

## Pitfalls

- **Forgetting the min with r - i**: copying z[i - l] blindly claims matches beyond the box that were never checked.
- **Updating the box unconditionally**: when i + z[i] does not pass r, replacing the box moves r to the left, forgets matched text and breaks the O(n) argument. Update only when i + z[i] > r.
- **z[0]**: the template leaves it 0; some problems want n there (2223 counts the whole string), so add it explicitly.
- **The separator**: as with KMP, it must not occur in the pattern or text, and searching with `z[i] >= m` relies on it to stop matches at length m.

## Quick check

Q: For s = "aaaa", what is the Z-array, and how many character comparisons succeed in total?
A: [0, 3, 2, 1]. Only i = 1 compares from scratch (3 successes, then the end of the string); i = 2 and i = 3 lie inside the box [1, 4) and copy min(r - i, z[i - l]) = 2 and 1 without any successful comparison. Three successes in total.

> [!know]
> You now know how the Z-box lets you compute every prefix-match length in O(n), and how to use it for matching.

=== recap | Parsing, tokenising and length-prefixed encodings | 10 min
goal: Split input into tokens before interpreting it, write small state-machine parsers, run-length encode, and encode lists of arbitrary strings so that decoding is unambiguous
tag: str-parse | Tokenisers, state machines and encodings
link: Python docs: re, Writing a Tokenizer | https://docs.python.org/3/library/re.html#writing-a-tokenizer | 5 min: the whole example: one regular expression of named alternatives, re.finditer, and a loop that turns matches into typed tokens with line and column numbers
link: Redis protocol spec: Bulk strings | https://redis.io/docs/latest/develop/reference/protocol-spec/#bulk-strings | 3 min: a production length-prefixed encoding ($5\r\nhello\r\n) and why it can carry any bytes
practice: 151, 8, 38

> [!key]
> Parse in two layers: a **tokeniser** turns characters into tokens (numbers, words, symbols), and a parser or **state machine** consumes tokens with an explicit state such as "before sign, in digits, done". To store a list of strings in one string, a delimiter alone fails as soon as a value contains the delimiter; prefix each value with its **length** (or escape the delimiter) and decoding becomes unambiguous.

## Internals

**Tokenise first.** `s.split()` (no argument) splits on runs of whitespace and drops empty strings, which is exactly "words" for most problems. For richer input, one regular expression with named alternatives, scanned with `re.finditer`, yields typed tokens in one pass; a hand-written index loop does the same with full control. Each character is examined a constant number of times, so tokenising is O(n).

**State machines.** Write the states down before coding: for a signed integer they are leading spaces, optional sign, digits, stop. Each character either moves to the next state or ends the parse. Clamping, overflow and "stop at the first non-digit" then become explicit transitions instead of scattered ifs. Nested formats (brackets, `3[ab]`-style repeats) add a stack of partial results.

**Run-length encoding** replaces each maximal run of a character by (character, count): "aaabcc" becomes a3 b1 c2. One pass, O(n). The look-and-say sequence is RLE applied to the previous term, read aloud.

**Why delimiters fail.** Join ["a,b", "c"] with "," and you get "a,b,c", which decodes to three values. Either escape the delimiter inside values (CSV doubles quotes; JSON escapes backslashes and quotes), or write each value's **length** first. Real formats do the second: HTTP bodies carry Content-Length, Redis's protocol sends bulk strings as `$<length>\r\n<data>\r\n`, and Protocol Buffers prefix strings and nested messages with a varint length. A length prefix needs no scanning of the data, so it handles binary content.

## Template

```python
import re

TOKEN = re.compile(r"\s*(?:(?P<num>\d+)|(?P<name>[A-Za-z_]\w*)|(?P<op>\S))")


def tokens(text):
    """[(kind, value), ...] for numbers, names and single-character operators."""
    out = []
    for m in TOKEN.finditer(text):
        kind = m.lastgroup
        if kind:                               # None only for trailing whitespace
            out.append((kind, m.group(kind)))
    return out


def rle(s):
    """'aaabcc' -> [('a', 3), ('b', 1), ('c', 2)]"""
    runs = []
    for ch in s:
        if runs and runs[-1][0] == ch:
            runs[-1][1] += 1
        else:
            runs.append([ch, 1])
    return [(ch, n) for ch, n in runs]


def encode(strings):
    """Length-prefixed: any characters, including ':' and digits, survive a round trip."""
    return "".join(f"{len(s)}:{s}" for s in strings)


def decode(data):
    out, i = [], 0
    while i < len(data):
        j = data.index(":", i)                 # the length field itself never contains ':'
        n = int(data[i:j])
        out.append(data[j + 1:j + 1 + n])
        i = j + 1 + n
    return out
```

## Worked example

`encode(["a:b", "", "5:x"])` is "3:a:b0:3:5:x". Decoding never looks inside a value, so the colons and digits in the data are harmless.

```steps
i = 0: the first ":" after i is at 1, so the length is "3"; take the 3 characters after it: "a:b"
    data  {{3:}}{{a:b}}0:3:5:x
    out   ["a:b"]
---
i = 5: ":" at 6, length "0": an empty string, and the next field starts at 7
    data  3:a:b{{0:}}3:5:x
    out   ["a:b", ""]
---
i = 7: ":" at 8, length "3": take "5:x". i = 12 = len(data): done
    data  3:a:b0:{{3:}}{{5:x}}
    out   ["a:b", "", "5:x"]
```

## Pitfalls

- **`split(" ")` versus `split()`**: the first keeps empty strings between repeated spaces; the second collapses whitespace.
- **Unclear states**: "  +-12" and "-" are where ad hoc parsers break. List the states and test every transition, including empty input and a lone sign.
- **Overflow in other languages**: accumulate with a check before multiplying by 10 (Python's ints never overflow, so clamp explicitly when the problem asks for 32-bit results).
- **Trusting a length field** from untrusted input: check it against the remaining data before slicing, or a corrupted prefix silently swallows the next value.

## Quick check

Q: Why does decoding "3:a:b0:3:5:x" never misread the ":" inside "a:b" or "5:x"?
A: The decoder searches for ":" only at the start of a field, to end the length; it then jumps over exactly n characters without inspecting them. Characters inside a value are never treated as structure.

> [!know]
> You now know how to tokenise before parsing, model a parser as states, run-length encode, and encode lists so that any content round-trips.

=== lab | Find the duplicates: repeated passages across documents | 45 min
goal: Detect passages of L characters shared by two documents with exact slices, hashed slices and a rolling hash, verify every hit, and measure where the rolling hash pays off in CPython
link: rsync technical report: checksum searching | https://rsync.samba.org/tech_report/node4.html | 4 min: how rsync looks up a rolling checksum at every byte offset with a 16-bit hash table, then confirms with the 32-bit sum and a strong checksum, the same hit-then-verify pattern as this lab

Plagiarism checkers, deduplicating backup tools and near-duplicate detectors all ask the same question: which passages of length L appear in more than one document? You will answer it three ways on about 420,000 characters of synthetic documents with planted copies, check that all three agree exactly, then measure time and memory for L = 50, 500 and 2,000. The point is not only "O(n) beats O(nL)", but where that crossover really is in CPython, and what collisions cost.

## Setup

- Python 3.10 or newer; no packages needed. The run takes about two minutes, most of it the memory measurements (tracemalloc slows allocation down).

## Steps

1. Save this as `dup_lab.py`. `by_slices` is the exact baseline (every window as a dict key). The two hash-based methods store one integer per window and **verify** every hit against the real text, so a collision can cost time but never a wrong answer.

```python
"""Find passages of L characters that appear in two different documents: exact slices, hashed slices, rolling hash."""
import random
import time
import tracemalloc

MOD = (1 << 61) - 1                      # Mersenne prime modulus
BASE = random.randrange(256, MOD - 1)    # random base, chosen once per run


def make_docs(n_docs=30, words=2_000, plants=30, seed=7):
    """Random-word documents plus planted copies of 60-3000 character passages."""
    rng = random.Random(seed)
    vocab = ["".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=rng.randint(2, 9))) for _ in range(5_000)]
    docs = [" ".join(rng.choices(vocab, k=words)) for _ in range(n_docs)]
    for _ in range(plants):
        a, b = rng.sample(range(n_docs), 2)
        size = rng.choice((60, 300, 3_000))
        start = rng.randrange(len(docs[a]) - size)
        pos = rng.randrange(len(docs[b]))
        docs[b] = docs[b][:pos] + docs[a][start:start + size] + docs[b][pos:]
    return docs


def by_slices(docs, L):
    """Exact baseline: every window is a dict key. Returns the set of (first doc, later doc) pairs."""
    first, pairs = {}, set()
    for d, text in enumerate(docs):
        for i in range(len(text) - L + 1):
            owner = first.setdefault(text[i:i + L], d)
            if owner != d:
                pairs.add((owner, d))
    return pairs


def _check(buckets, docs, L, key, d, i, pairs):
    """A hash hit. buckets[key] holds the first (doc << 32 | start) of each distinct window with this hash.
    Compare the real text, so a collision costs time but never a wrong answer. Returns 1 for a collision."""
    window = docs[d][i:i + L]
    entry = buckets[key]
    entries = entry if isinstance(entry, list) else [entry]
    for packed in entries:
        od, oi = packed >> 32, packed & 0xFFFFFFFF
        if docs[od][oi:oi + L] == window:
            if od != d:
                pairs.add((od, d))
            return 0
    buckets[key] = entries + [d << 32 | i]          # same hash, different text
    return 1


def by_slice_hash(docs, L):
    buckets, pairs, collisions = {}, set(), 0
    for d, text in enumerate(docs):
        for i in range(len(text) - L + 1):
            key = hash(text[i:i + L])                   # O(L): slice, then hash, both in C
            if key in buckets:
                collisions += _check(buckets, docs, L, key, d, i, pairs)
            else:
                buckets[key] = d << 32 | i
    return pairs, collisions


def by_rolling(docs, L, mod=MOD):
    buckets, pairs, collisions = {}, set(), 0
    top = pow(BASE, L - 1, mod)
    for d, text in enumerate(docs):
        if len(text) < L:
            continue
        codes = [ord(ch) for ch in text]
        h = 0
        for c in codes[:L]:
            h = (h * BASE + c) % mod
        for i in range(len(text) - L + 1):
            if h in buckets:
                collisions += _check(buckets, docs, L, h, d, i, pairs)
            else:
                buckets[h] = d << 32 | i
            if i + L < len(text):
                h = ((h - codes[i] * top) * BASE + codes[i + L]) % mod   # O(1) slide
    return pairs, collisions


def timed(fn, *args):
    t = time.perf_counter()
    out = fn(*args)
    return out, time.perf_counter() - t


def peak_mb(fn, *args):
    tracemalloc.start()
    fn(*args)
    peak = tracemalloc.get_traced_memory()[1] / 1e6
    tracemalloc.stop()
    return peak


def main():
    docs = make_docs()
    print(f"{len(docs)} documents, {sum(map(len, docs)):,} characters")
    for L in (50, 500, 2_000):
        print(f"L = {L}")
        results = {}
        methods = [("hash(slice)", by_slice_hash, ()), ("rolling hash", by_rolling, ()),
                   ("rolling, mod 1000003", by_rolling, (1_000_003,))]
        if L <= 500:
            methods.insert(0, ("dict of slices", by_slices, ()))
        for name, fn, extra in methods:
            out, secs = timed(fn, docs, L, *extra)
            results[name] = out if isinstance(out, set) else out[0]
            note = "" if isinstance(out, set) else f"  collisions {out[1]}"
            print(f"  {name:21} {secs:6.2f} s  peak {peak_mb(fn, docs, L, *extra):6.1f} MB{note}")
        answers = list(results.values())
        assert all(a == answers[0] for a in answers), "methods disagree"
        print(f"  all methods agree: {len(answers[0])} document pairs share a passage")


if __name__ == "__main__":
    main()
```

2. Predict before running: which method is fastest at L = 50, and at L = 2,000? Which uses the most memory at L = 500? Roughly how many collisions will the modulus 1,000,003 cause on about 420,000 windows?
3. Run `python3 dup_lab.py` and copy the output into a table: method by L, with time and peak memory.
4. Explain the L = 50 row. Slicing and hashing 50 characters runs in C and costs about as much as the handful of Python operations the rolling update needs per window, so O(nL) in C competes with O(n) in bytecode.
5. Explain the memory column: `by_slices` keeps every window as a string of about 49 + L bytes, while the hash methods keep one integer per window whatever L is.
6. Explain the collision count with the birthday effect: with N windows and M buckets you expect about N^2 / (2M) colliding pairs while N is much smaller than M, and when N approaches M a large fraction of new windows land in an occupied bucket. Then confirm the answers still agree: verification removed every false hit.
7. Stretch: winnowing, the fingerprinting idea used by plagiarism detectors. Instead of storing every window hash, store only the smallest hash in each run of w consecutive window hashes. Implement it for w = 20 and check that every planted passage of at least L + w - 1 characters is still found while far fewer fingerprints are stored.

## What you should see

Times on a recent machine (a shared one can be twice as slow); memory is stable:

| L | dict of slices | hash(slice) | rolling hash |
|---|---|---|---|
| 50 | about 0.4 s, 55 MB | about 0.5 s, 55 MB | about 0.8-1.3 s, 55 MB |
| 500 | about 0.7 s, 220 MB | about 0.5-0.7 s, 55 MB | about 0.8-1 s, 55 MB |
| 2,000 | (skipped: about 0.9 GB) | about 1-1.1 s, 55 MB | about 0.7-0.9 s, 55 MB |

- All methods agree: about 32 document pairs share a 50-character passage and about 10 share a 500- or 2,000-character one (only the long planted copies are that long).
- At L = 50 the C-level slicing methods win; the rolling hash's cost is flat in L while slicing grows with it, so the rolling hash catches up somewhere between 500 and 2,000 characters and is ahead at 2,000. In a compiled language the crossover comes far earlier.
- Exact slices are fine for short L and hopeless for long L: memory grows with L, about four times larger at 500 than at 50.
- With the modulus 1,000,003, expect tens of thousands of collisions, a little extra time for verification, and exactly the same answer. With 2^61 - 1, zero.

## Check yourself

Q: A service must find repeated 4 KB blocks across terabytes of backups. Which approach from this lab scales, and what would you change about it?
A: The rolling hash: its cost per byte does not depend on the block size, and it stores one small integer per candidate instead of a 4 KB key. In production you would write it in a compiled language, store only some fingerprints (content-defined boundaries as restic does, or winnowing), keep the hash index on disk, and confirm candidates with a strong hash or a byte comparison, as rsync does.

=== practice
- 205 core
  cue: Decide whether the letters of one string can be renamed, consistently and one-to-one, to produce another string of the same length
  hint: A renaming must send every copy of a letter to the same letter, and two different letters may not share a target. What pattern do both strings have to share?
  insight: Map each character to the index of its first occurrence; two strings are related by a one-to-one renaming exactly when these first-occurrence patterns are equal. Two dicts (s to t and t to s) checked position by position work too; checking only one direction is the classic bug.
  cost: O(n) time, O(alphabet) space
  pattern: str-count
- 28 core
  cue: Return where a pattern first occurs inside a text, or -1
  hint: After a partial match fails, the naive method restarts from the next text position. Could the part you already matched tell you where the pattern can resume?
  insight: Build the prefix function of the pattern; scan the text once, and on a mismatch fall back to pi[k - 1] characters matched instead of zero, so the text pointer never moves backwards. The first time k reaches m, the answer is i - m + 1. (In everyday Python, text.find(pattern) is the right tool.)
  cost: O(n + m) time, O(m) space
  pattern: str-kmp
- 459 derive
  cue: Can the whole string be produced by writing some shorter substring several times in a row?
  hint: If the string is a repetition of a block, what is true of its longest proper prefix that is also a suffix?
  insight: Let b = pi[n - 1] be the longest border; then p = n - b is the smallest period, and the string is a whole repetition exactly when b > 0 and n % p == 0. Equivalently, s occurs in (s + s)[1:-1]: rotating a repetition by one period gives the string back.
  cost: O(n) time, O(n) space
  pattern: str-kmp
- 5 core
  cue: Return the longest contiguous piece of the string that reads the same in both directions
  hint: Every such piece is symmetric about a middle point. How many possible middles are there, and what can you do from each?
  insight: Expand from each of the 2n - 1 centres (each character and each gap) while the two ends match; the widest span found wins. Each centre costs its radius, so O(n^2) in the worst case with O(1) extra space (Manacher brings it to O(n)).
  cost: O(n^2) time, O(1) extra space
  pattern: str-palin
- 647 core
  cue: Count how many contiguous substrings read the same in both directions, counting equal substrings at different positions separately
  hint: Use the same middles as for the longest one. How many palindromes does one successful expansion step add?
  insight: Expand around all 2n - 1 centres; every step where the ends still match is exactly one more palindrome centred there, so the answer is the total number of successful steps (a maximal span of length L contributes (L + 1) // 2).
  cost: O(n^2) time, O(1) extra space
  pattern: str-palin
- 151 core
  cue: Reverse the order of the words in a sentence, removing leading, trailing and repeated spaces
  hint: Treat the sentence as a list of tokens rather than characters. Which split collapses runs of spaces for you?
  insight: Tokenise with split() (no argument), which drops empty strings, then join the reversed list with single spaces. Without a split, reverse the whole character buffer, then reverse each word and compact spaces with a write index.
  cost: O(n) time, O(n) space (O(1) extra for the in-place buffer version)
  pattern: str-parse
- 8 core
  cue: Read a signed integer from the front of a messy string and clamp it to the 32-bit range
  hint: Write down the stages the input goes through (spaces, an optional sign, digits) and what ends each one.
  insight: A small state machine: skip leading spaces, read at most one sign, then accumulate digits until the first non-digit; clamp the result to [-2^31, 2^31 - 1]. In languages with fixed-width ints, check before multiplying by 10.
  cost: O(n) time, O(1) space
  pattern: str-parse
- 38 core
  cue: Each term of a sequence describes the previous term by reading out its groups of equal digits
  hint: How do you describe "111221" in one left-to-right pass? What counts as one group?
  insight: Each term is the run-length encoding of the previous one, written as count then digit. Scan maximal runs, append str(count) and the digit to a list, join once, and repeat n - 1 times; the terms grow by roughly 30% each step, so build with join.
  cost: O(total length of all terms generated) time
  pattern: str-parse
- 1392 core
  cue: Return the longest non-empty prefix of a string that is also a suffix, without being the whole string
  hint: This is precisely one value that the KMP preprocessing computes. Which one?
  insight: The answer is s[:pi[n - 1]], the longest border. Alternatively compare prefix and suffix hashes for every length from longest to shortest and verify the first equal pair.
  cost: O(n) time, O(n) space
  pattern: str-kmp
- 214 derive
  cue: Make the string a palindrome by adding as few characters as possible, only at the front
  hint: Whatever you add in front mirrors part of the end. Which part of the original string can stay unmatched in the middle?
  insight: Find the longest palindromic prefix of s: it is the last prefix-function value of s + "#" + reversed(s), since a border there is a prefix of s equal to a suffix of its reverse. Answer: reversed(s[L:]) + s.
  cost: O(n) time, O(n) space
  pattern: str-kmp
- 1044 stretch
  cue: Find the longest substring that occurs at least twice (occurrences may overlap), for a string of up to 3 * 10^4 characters
  hint: If some length works, every shorter length works too. How fast can you test one length?
  insight: Binary search on the length L; test a length by sliding a polynomial hash over every window and checking for a repeat in a set, verifying candidates against the real text (or using a 61-bit modulus with a random base). Each test is O(n), so O(n log n) overall.
  cost: O(n log n) expected time, O(n) space
  pattern: str-hash
- 2223 stretch
  cue: Sum, over every suffix, the length of its longest common prefix with the whole string
  hint: Each term compares the string with itself shifted by i. Which array stores exactly those lengths?
  insight: Those terms are the Z-function: z[i] is the longest common prefix of s and s[i:]. Compute it in O(n) with the Z-box; the answer is n (for the whole string) plus the sum of z[i] for i >= 1.
  cost: O(n) time, O(n) space
  pattern: str-z
