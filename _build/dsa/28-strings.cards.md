=== card | 205
time: 20 min

## The problem

Decide whether each character of one string can be renamed consistently to obtain the other, with distinct source characters assigned distinct targets. Positions are significant: `egg` and `add` qualify, while `ab` and `cc` do not.

## Constraints and what they imply

The strings must have equal lengths; this implementation returns false otherwise. Characters are arbitrary Python code points, so an array indexed only by lowercase letters would unnecessarily restrict the inputs. Empty strings satisfy the condition.

## Brute force

For every pair of positions, compare whether the source characters are equal and whether the corresponding target characters are equal. The two equality results must agree for all pairs. This uses O(n²) time and O(1) auxiliary space but revisits the same character relationships repeatedly.

## The insight

Keep a mapping in each direction while scanning aligned positions. The forward map prevents one source from changing its target; the reverse map prevents two sources from merging. If a pair is compatible, record both directions. After each position, the maps represent a bijection on exactly the characters encountered so far. A conflicting pair cannot occur in any valid renaming, and completing the scan gives a consistent one-to-one mapping.

## Optimal solution, traced

```steps
Compare e with a and g with d
    Record e -> a, a -> e, g -> d, d -> g
---
Compare the final g with d
    Both existing mappings agree, so return {{true}}
```

## Code

```python
def is_isomorphic(source, target):
    if len(source) != len(target):
        return False
    forward, reverse = {}, {}
    for a, b in zip(source, target):
        if a in forward and forward[a] != b:
            return False
        if b in reverse and reverse[b] != a:
            return False
        forward[a] = b
        reverse[b] = a
    return True
```

## Complexity

Expected O(n) time for dictionary operations and O(d) space, where d is the number of distinct characters encountered. The Python hash-table bounds are expected rather than worst-case guarantees.

## Mistakes and edge cases

- One direction alone incorrectly accepts `ab` mapped to `cc`.
- Compare lengths before using `zip`, which otherwise silently truncates.
- A mapping is between code points; normalization and grapheme clusters are separate choices.

## Variations

- Compare the sequence of first-occurrence indices in each string instead.
- Test whether a list of words has the same equality pattern as a pattern string.

=== card | 28
time: 20 min

## The problem

Return the starting index of the first occurrence of a pattern in a text, or -1 if it is absent. Treat the empty pattern as occurring at index 0. For `text = "ababa"` and `pattern = "aba"`, the result is 0.

## Constraints and what they imply

Both strings may be empty and may contain arbitrary code points. Overlapping matches are possible, though only the earliest is requested. Repeated characters make naive restarting expensive; the scan should avoid moving the text index backward.

## Brute force

At each legal starting position, compare the pattern against the corresponding text characters until a mismatch or a full match. With text length n and pattern length m, worst-case time is O(nm), as almost all comparisons can succeed before each mismatch. Comparing characters directly needs O(1) auxiliary space.

## The insight

For each pattern prefix, compute the length of its longest proper prefix that is also a suffix. When a comparison fails after k matched characters, any possible continuation must begin with a border of those k characters. Falling back to the longest such border preserves every viable candidate; further mismatches follow its own border links. The text index never retreats, and total fallback steps are amortized linear because k can increase only once per scanned character.

## Optimal solution, traced

```steps
pattern = aba, prefix lengths = [0, 0, 1]
    Scan a then b: matched length becomes 2
---
Scan a
    matched length becomes 3; return 2 - 3 + 1 = {{0}}
```

## Code

```python
def find_first(text, pattern):
    if not pattern:
        return 0
    pi = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k and pattern[i] != pattern[k]:
            k = pi[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        pi[i] = k
    k = 0
    for i, char in enumerate(text):
        while k and char != pattern[k]:
            k = pi[k - 1]
        if char == pattern[k]:
            k += 1
        if k == len(pattern):
            return i - len(pattern) + 1
    return -1
```

## Complexity

The prefix table costs O(m) time and space. The text scan costs O(n), so total time is O(n + m) and auxiliary space is O(m). In ordinary Python, `text.find(pattern)` is usually simpler.

## Mistakes and edge cases

- Use `pi[k - 1]`, not `pi[k]`, when falling back.
- Handle the empty pattern before indexing it.
- Return as soon as the first full match ends, including when it ends at the final text character.

## Variations

- Report all occurrences by falling back after a full match instead of returning.
- Use a prefix automaton for repeated scans over a fixed small alphabet.

=== card | 459
time: 20 min

## The problem

Determine whether a nonempty string consists of at least two copies of a shorter nonempty string. For example, `abcabc` qualifies, but `abca` does not. This implementation also returns false for an empty input.

## Constraints and what they imply

The repeating unit must cover the entire input; a repeated prefix with a leftover tail is insufficient. A one-character string cannot be formed from two nonempty copies. Arbitrary code points are supported.

## Brute force

Try each possible unit length from 1 through half the input length. When the length divides n, repeat the corresponding prefix and compare it with the original. Constructing and checking each candidate can cost O(n), for O(n²) worst-case time and O(n) space for a constructed candidate.

## The insight

The prefix function gives the longest proper border length b, where a border is both a prefix and suffix. Consequently p = n - b is the shortest period: the border equality enforces `s[i] == s[i - p]` wherever both indices exist. Conversely any period q gives a border of length n - q, so no shorter period exists. The string is a whole repetition exactly when b is positive and p divides n. Divisibility is essential: a periodic string can stop partway through its next block.

## Optimal solution, traced

```steps
For abcabc, the longest proper border is abc
    n = 6, b = 3, so shortest period p = 3
---
6 is divisible by 3 and b is positive
    return {{true}}
```

## Code

```python
def repeated_substring(s):
    if not s:
        return False
    pi = [0] * len(s)
    k = 0
    for i in range(1, len(s)):
        while k and s[i] != s[k]:
            k = pi[k - 1]
        if s[i] == s[k]:
            k += 1
        pi[i] = k
    border = pi[-1]
    return border > 0 and len(s) % (len(s) - border) == 0
```

## Complexity

Computing the prefix table takes O(n) amortized time and O(n) auxiliary space. Each successful extension raises k by one, and each fallback lowers it, bounding the total number of fallback steps.

## Mistakes and edge cases

- A border alone does not ensure a whole number of repetitions: `ababa` has period 2 but length 5.
- The entire string is not a shorter unit.
- Avoid accessing the last prefix entry for an empty string.

## Variations

- Return the shortest repeating unit rather than a Boolean.
- Find every valid unit length by following the border chain and testing divisibility.

=== card | 5
time: 30 min

## The problem

Return a longest contiguous substring that reads identically from left to right and right to left. If several have maximum length, any one is acceptable. For `babad`, either `bab` or `aba` is valid. An empty input returns an empty string.

## Constraints and what they imply

The substring must be contiguous, not a subsequence obtained by skipping characters. Both odd and even lengths are possible. Python strings are sequences of code points; this algorithm compares those code points directly and does not perform Unicode normalization. An answer must be materialized as a new string, but candidate slices need not be created.

## Brute force

Enumerate each pair of endpoints and check the corresponding substring by comparing inward. There are O(n²) candidates and a check can take O(n), giving O(n³) time in the worst case. Direct index comparisons need O(1) workspace; slicing every candidate would add allocation and copying costs.

## The insight

Every nonempty palindrome has exactly one center, either a character or the gap between adjacent characters. Starting at that center, matching outward endpoints yields all palindromes with that center in increasing size. Once a pair mismatches, every larger candidate with the same center includes that mismatch, so further expansion cannot succeed. Visiting all centers therefore examines every possible palindrome; keep only the best half-open interval. Length-one centers ensure that a nonempty input always has a candidate.

## Optimal solution, traced

```steps
s = cbbd; try the gap between the two b characters
    b equals b, so the interval [1, 3) is a palindrome
---
Expand to c and d
    They differ; keep [1, 3) and return {{bb}}
```

The interval is updated only when it is strictly longer than the current best. This deliberately leaves ties with the earlier discovered candidate; the problem does not require a particular tie choice.

## Code

```python
def longest_palindrome(s):
    best_left = best_right = 0
    for center in range(len(s)):
        for left, right in ((center, center), (center, center + 1)):
            while left >= 0 and right < len(s) and s[left] == s[right]:
                if right - left + 1 > best_right - best_left:
                    best_left, best_right = left, right + 1
                left -= 1
                right += 1
    return s[best_left:best_right]
```

## Complexity

There are O(n) centers and each can expand O(n) times, giving O(n²) worst-case time. Auxiliary workspace is O(1), excluding the returned substring, which can occupy O(n) space. On strings with little symmetry, expansions often stop quickly, but that is not a worst-case guarantee.

## Mistakes and edge cases

- Forgetting gap centers misses `bb` and other even palindromes.
- Do not return the interval after the failed comparison without correcting its boundaries.
- Track indices instead of repeatedly slicing, which can introduce substantial copying.
- A single character, an empty string, and a string of identical characters deserve separate tests.

## Variations

- Count all palindromic substrings by adding one per successful expansion.
- Use Manacher's algorithm to compute maximum radii in O(n) time.
- Return all distinct longest values, taking care to define how duplicates are handled.

=== card | 647
time: 30 min

## The problem

Count the nonempty contiguous substrings that are palindromes. Occurrences at different positions count separately even when their text is the same. For `aaa`, the answer is 6: three length-one occurrences, two length-two occurrences, and one length-three occurrence.

## Constraints and what they imply

Every center may contribute several lengths, and both character centers and gap centers matter. The input may be empty, in which case there are no nonempty substrings. The result can grow quadratically in n, so fixed-width implementations must choose an appropriately wide counter. Python integers grow as necessary.

## Brute force

Enumerate all O(n²) endpoint pairs and check each candidate by comparing the characters from its ends inward. One test can take O(n), yielding O(n³) worst-case time and O(1) auxiliary space if the check uses indices. The repeated checks recompute the inner palindrome for longer candidates.

## The insight

A palindrome is determined by its center and its radius. Begin at each character and each gap, and expand while both endpoints are in range and equal. Every successful comparison creates exactly one palindrome, since the previously tested inner interval is already known to be symmetric. Once a mismatch or boundary stops the expansion, no larger palindrome at that center can exist. Every palindrome has one unique center, so summing successful steps neither misses nor double-counts occurrences.

## Optimal solution, traced

```steps
s = aaa; the three character centers contribute 1, 2, and 1
    Their total is 4
---
The two gaps each contribute one length-two palindrome
    total = 4 + 1 + 1 = {{6}}
```

The two copies of `aa` are counted separately because they have different gap centers. A successful expansion counts an occurrence, not merely a distinct string value.

For an even center, the initial empty interior is symmetric. Matching the two adjacent characters creates the first nonempty palindrome, and each later step adds one character to each side.

## Code

```python
def count_palindromes(s):
    count = 0
    for center in range(len(s)):
        for left, right in ((center, center), (center, center + 1)):
            while left >= 0 and right < len(s) and s[left] == s[right]:
                count += 1
                left -= 1
                right += 1
    return count
```

## Complexity

There are O(n) centers and at most O(n) successful expansions per center, so time is O(n²) in the worst case. The algorithm uses O(1) auxiliary space. The final extra gap after the last character fails immediately and does not affect the count or asymptotic cost.

## Mistakes and edge cases

- Counting only maximal palindromes loses the smaller ones at the same center.
- Counting distinct contents instead of positions changes the requested result.
- Include odd and even centers, and return zero for empty input.
- For n identical characters the expected answer is n(n + 1)/2.

## Variations

- Record the longest interval instead of counting successful expansions.
- Use Manacher radii to sum contributions in O(n) time.
- Count distinct palindrome values with a palindromic tree.

=== card | 151
time: 30 min

## The problem

Given a sentence whose words are separated by spaces, return the words in reverse order, separated by one space, with no leading or trailing space. For `  red   blue `, return `blue red`. All-space input produces an empty string.

## Constraints and what they imply

This version treats the literal ASCII space as the separator and preserves all other characters inside words, including tabs. It accepts an empty string. Python strings are immutable, so the returned text and token references require storage; the implementation does not claim an in-place transformation.

## Brute force

Repeatedly scan the remaining prefix from the beginning to find its final word, append that word to the answer, then shrink the prefix. Repeating a linear scan for each of O(n) short words can take O(n²) time. Building the answer by repeated concatenation can add further copying; at least O(n) space is required for the returned string.

## The insight

Split once on the exact separator, discard empty tokens produced by consecutive or boundary spaces, reverse the remaining sequence, and join with a single separator. Every nonempty token is exactly one maximal run of non-space characters. Reversal changes only token order, while joining inserts exactly one space between neighboring output words. Thus neither the characters within a word nor their order are altered, and no extra separator can remain at either end.

## Optimal solution, traced

```steps
Split "  red   blue " on spaces and discard empty tokens
    words = [red, blue]
---
Reverse the tokens and join with one space
    result = {{blue red}}
```

Using `split(" ")` rather than the no-argument form is intentional: no-argument splitting also treats tabs, newlines and other whitespace as separators. Either convention can be useful, but they are different contracts.

For instance, a tab inside `red` followed by `blue` is part of one word under this contract, rather than a boundary between two words.

## Code

```python
def reverse_words(sentence):
    words = [word for word in sentence.split(" ") if word]
    words.reverse()
    return " ".join(words)
```

## Complexity

Splitting, filtering, reversing and joining together take O(n) time. The tokens, list, and returned string use O(n) space. Empty tokens from repeated spaces are also bounded by input length.

## Mistakes and edge cases

- Reversing the entire character string alone reverses each word as well.
- Joining unfiltered tokens preserves unwanted repeated spaces.
- Decide explicitly whether tabs and other whitespace are separators.
- One word should be returned unchanged except for surrounding spaces.

## Variations

- Treat all Unicode whitespace as separators with `split()` instead.
- Given a mutable character buffer, compact spaces and reverse individual words after reversing the whole buffer.
- Preserve the original spacing and reverse only the word sequence; specify how separators are assigned.

=== card | 8
time: 30 min

## The problem

Read an optional sign followed by consecutive ASCII decimal digits after skipping leading ASCII spaces. Stop at the first other character, return zero if there are no digits, and clamp the value to the signed 32-bit interval. For `  -42rest`, return -42.

## Constraints and what they imply

The parser consumes only a prefix, not every number embedded in the string. A sign is allowed once and only before digits; a space after the sign ends the digit run. Limits are -2³¹ and 2³¹ - 1, which differ by one in magnitude. Very long inputs should not require constructing an enormous Python integer.

## Brute force

One could identify the digit substring, convert it to an arbitrary-precision integer, apply the sign, then clamp. This takes at least O(n) scanning time and O(n) substring space; very long integers also have conversion and arithmetic costs, and Python may reject conversions past its configured digit limit. An incremental bounded accumulator avoids those problems.

## The insight

The parser has three ordered phases: skip spaces, consume at most one sign, then consume digits. Accumulate a nonnegative magnitude with limit 2³¹ for negative numbers and 2³¹ - 1 otherwise. Before the next multiply and add, compare the existing magnitude with the largest safe predecessor. If that digit would cross the limit, the final clamped result is already determined, because remaining digits can only increase the magnitude. If no overflow happens, the accumulated magnitude is exactly the value of the consumed prefix by the usual base-ten recurrence.

## Optimal solution, traced

```steps
Input "  -42rest": skip two spaces and read the minus sign
    limit = 2147483648, magnitude = 0
---
Read 4 then 2; r stops the digit phase
    signed magnitude is {{-42}}
```

The comparison against the limit happens before multiplication, so the same logic works in a fixed-width language when the limits and intermediate operations are represented safely.

## Code

```python
def parse_int32(text):
    i = 0
    while i < len(text) and text[i] == " ":
        i += 1
    sign = 1
    if i < len(text) and text[i] in "+-":
        if text[i] == "-":
            sign = -1
        i += 1
    limit = (1 << 31) if sign < 0 else (1 << 31) - 1
    value = 0
    while i < len(text) and "0" <= text[i] <= "9":
        digit = ord(text[i]) - ord("0")
        if value > (limit - digit) // 10:
            return -limit if sign < 0 else limit
        value = value * 10 + digit
        i += 1
    return sign * value
```

## Complexity

The scan visits at most n characters and maintains a bounded accumulator: O(n) time and O(1) auxiliary space. It may return early as soon as overflow is unavoidable.

## Mistakes and edge cases

- `isdigit()` recognizes non-ASCII digits that are outside this contract.
- `+-2`, `- 2`, an empty input, and a sign with no digits all yield zero.
- Clamp the negative endpoint separately; its magnitude is one larger.
- A leading tab is not an ASCII space in this contract.

## Variations

- Return both the value and the index where parsing stopped.
- Reject overflow instead of saturating, or support a different base.
- Recognize a broader whitespace set only if the input contract calls for it.

=== card | 38
time: 30 min

## The problem

Start with the string `1`. Each subsequent term describes the preceding term as consecutive runs: write the decimal run length followed by the run's character, for each run in order. Return the nth term for a positive integer n. The first four terms are `1`, `11`, `21`, and `1211`.

## Constraints and what they imply

The operation describes runs, not the total frequency of each character. Runs with the same character separated by another character remain separate. The number of terms is positive; this implementation rejects nonpositive n. Intermediate terms can grow, so avoid repeated string concatenation inside the run loop.

## Brute force

One inefficient method finds a run by comparing each position against all earlier positions in that run, then constructs the next term by appending fragments one at a time to an immutable string. Repeated comparisons or copies can make one transformation quadratic in its input and output lengths. It also obscures the exact boundary between adjacent groups.

## The insight

Scan a term from left to right. At index i, advance j until it reaches the first different character or the end. The interval [i, j) is a maximal run, and its description is `str(j - i)` followed by `term[i]`. Append these pieces to a list and continue from j; a single join builds the new term. The intervals are nonempty, disjoint, and cover the preceding term in order, so each run is described exactly once. Repeating this transformation n - 1 times establishes the requested term by induction.

## Optimal solution, traced

```steps
term = 21: the first maximal run contains one 2
    emit 12
---
The next maximal run contains one 1
    emit 11; join to obtain {{1211}}
```

A run count is written in decimal and may require multiple digits for a general input to this encoding operation, even though the generated sequence starts from `1`.

## Code

```python
def count_and_say(n):
    if n < 1:
        raise ValueError("n must be positive")
    term = "1"
    for _ in range(n - 1):
        pieces = []
        i = 0
        while i < len(term):
            j = i + 1
            while j < len(term) and term[j] == term[i]:
                j += 1
            pieces.extend((str(j - i), term[i]))
            i = j
        term = "".join(pieces)
    return term
```

## Complexity

Let L be the sum of the lengths of all generated terms including the answer. Scanning and emitting each run costs O(L) overall, with O(maximum term length) working space for the current term and the next term's pieces. This output-sensitive bound avoids assuming a particular growth rate.

## Mistakes and edge cases

- Start with `1` at n = 1; do not apply the transformation n times.
- Adjacent equal characters are one run, but separated equal characters are not.
- Flush the final run even when it reaches the end of the string.
- Joining fragments once avoids repeated whole-prefix copying.

## Variations

- Implement a generic run-length encoder for an arbitrary string.
- Stream each term's pieces to a consumer rather than returning a single string.
- Specify a delimiter or escaping scheme if encoded counts and symbols must later be decoded unambiguously.

=== card | 1392
time: 40 min

## The problem

Return the longest nonempty proper prefix of a string that is also a suffix. Proper means the prefix cannot be the whole input, although the prefix and suffix are allowed to overlap. Return the empty string if no such border exists. For `level`, the answer is `l`; for `aaaa`, it is `aaa`.

## Constraints and what they imply

The answer is a contiguous prefix and a contiguous suffix, not an arbitrary matching subsequence. An input may be empty or contain arbitrary Python code points. Overlap is permitted, so an algorithm that caps the border length at half the string is incorrect. A long run of the same character creates many candidate borders and exposes repeated comparison costs. The result is a slice, so its allocation must be counted separately from the table used to find it.

## Brute force

Test candidate lengths from n - 1 down to 1, comparing the prefix and suffix character by character. The first successful candidate is the longest because candidates are considered in decreasing order. Each comparison can take O(n), and there are O(n) candidates, giving O(n²) worst-case time. Index-based comparisons use O(1) auxiliary space, apart from the returned slice; making slices at every step allocates extra intermediate strings.

## The insight

Build the prefix function pi, where pi[i] is the length of the longest proper border of the prefix ending at i. Suppose a prefix ending just before i has a border of length k. To extend that border, compare the next character with the character at position k. If they differ, a shorter candidate must itself be a border of the length-k prefix: any suffix that could extend to a border also ends that prefix. The next candidate is therefore pi[k - 1]. Repeating this fallback tries all relevant candidates in decreasing order without revisiting arbitrary positions.

When the characters match, adding one gives the longest extendable candidate; if none match, the answer for this position is zero. This maintains the definition of pi by induction. At the final position, pi[-1] is exactly the longest proper border requested. Its length is less than n because pi only represents proper borders. The algorithm does not forbid the two occurrences from overlapping.

## Optimal solution, traced

```steps
s = aaaa: process the second and third characters
    pi becomes [0, 1, 2, 0] so far
---
The final a extends the border of length 2
    pi[3] = 3; return s[:3] = {{aaa}}
```

In the fallback case, the invariant is that k is a border length of the already processed prefix. Reducing it through the table preserves this invariant, while discarding lengths that cannot possibly match the current character. Over a complete scan, increases of k total at most n and each fallback strictly decreases k; hence all fallback iterations together are linear.

The answer may be empty even when characters recur internally: both ends must match in the same order. For `abcabx`, a repeated internal prefix is not a suffix, so the final border length is zero.

## Code

```python
def longest_border(s):
    if not s:
        return ""
    pi = [0] * len(s)
    k = 0
    for i in range(1, len(s)):
        while k and s[i] != s[k]:
            k = pi[k - 1]
        if s[i] == s[k]:
            k += 1
        pi[i] = k
    return s[:pi[-1]]
```

## Complexity

The prefix table takes O(n) time and O(n) auxiliary space. A returned border can contain O(n) characters, so the output itself can also occupy O(n) space. Each comparison and indexing operation is constant time under the normal Python string cost model.

## Mistakes and edge cases

- Returning the whole string violates the proper-prefix requirement.
- Restricting the two occurrences to disjoint intervals incorrectly rejects overlapping borders.
- A mismatch needs `pi[k - 1]`, not a reset to zero or an access to `pi[k]`.
- The empty string needs special treatment before accessing the last table entry.
- Slicing a zero-length prefix correctly gives the empty result.

## Variations

- Follow the border chain from pi[-1] to enumerate all proper border lengths.
- Test if the smallest period tiles the whole string by checking divisibility.
- Search for a pattern in a text using the same fallback table.

=== card | 214
time: 45 min

## The problem

Add characters only to the front of a string so that the result is a palindrome, using as few added characters as possible. Return the resulting string. For `aacecaaa`, one optimal result is `aaacecaaa`; an empty string needs no additions.

## Constraints and what they imply

The existing string must remain intact as a suffix of the result. A palindrome that could be formed by inserting characters elsewhere does not satisfy this operation. The input may contain any Python code point, including punctuation ordinarily used as a separator in string algorithms. The answer can be nearly twice the input length, so the output itself may require O(n) space.

## Brute force

Check prefixes from longest to shortest, testing each by comparing from its ends toward the middle. Once a palindromic prefix is found, reverse the remaining suffix and prepend it. Up to O(n) prefix checks each cost O(n), yielding O(n²) worst-case time and O(1) workspace for index comparisons, excluding the result. Testing only prefixes is sufficient because the part that remains unpaired with the newly prepended characters must be a palindromic prefix.

## The insight

Let L be the length of the longest palindromic prefix. The suffix after that prefix must be mirrored in front, giving `reverse(s[L:]) + s`. This construction is a palindrome because its outside pieces mirror each other and its middle is a palindrome. It adds n - L characters.

For optimality, suppose k characters are added. If k is less than n, the original prefix of length n - k lies in the central region of the finished palindrome, so it must itself be palindromic. Hence n - k cannot exceed L, and k is at least n - L. If k is at least n, it is certainly no smaller than n - L. Our construction reaches the lower bound.

To find L, compute the prefix function on the sequence `s`, a unique sentinel, and `reverse(s)`. A proper border cannot include the sentinel: there is only one, and it would have to occur at two distinct aligned positions. Therefore the final border lies completely inside the two string portions. A prefix of s equal to a suffix of its reverse is exactly a palindromic prefix. The longest border thus gives L. A fresh object supplies a sentinel unequal to every string character, rather than assuming an unused character exists.

## Optimal solution, traced

```steps
s = abcd; compare prefixes of abcd with suffixes of dcba
    the longest matching border has length 1, representing a
---
Reverse the remaining suffix bcd and prepend it
    dcb + abcd = {{dcbabcd}}
```

The sentinel is part of the prefix-function sequence, not part of the answer. The combined sequence is a list of characters and one object, so it remains safe even when the input contains `#`, a zero byte, or every ordinary punctuation character.

When the original string is already a palindrome, the border spans all n original characters without including the sentinel. The unmatched suffix is then empty, so the construction returns the original unchanged.

## Code

```python
def shortest_front_palindrome(s):
    marker = object()
    seq = list(s) + [marker] + list(reversed(s))
    pi = [0] * len(seq)
    k = 0
    for i in range(1, len(seq)):
        while k and seq[i] != seq[k]:
            k = pi[k - 1]
        if seq[i] == seq[k]:
            k += 1
        pi[i] = k
    prefix_len = pi[-1]
    return s[prefix_len:][::-1] + s
```

## Complexity

The combined sequence has 2n + 1 entries. Prefix preprocessing takes O(n) time by amortized fallback, and building the reversed suffix and result also takes O(n) time. Lists, table, and result require O(n) space. The empty input produces a one-element sentinel sequence and returns the empty string.

## Mistakes and edge cases

- A literal separator can occur in the input and make the border cross the intended boundary.
- The longest palindromic substring is not necessarily a prefix and cannot replace L.
- Mirror the suffix after the prefix, not the prefix itself.
- Already-palindromic inputs need zero added characters.
- Test repeated characters, one-character inputs, empty input, and punctuation.

## Variations

- Append only at the end by applying the same idea to the reversed string.
- Return the number of characters needed rather than the resulting string.
- Find all palindromic prefix lengths by following the final border chain.

=== card | 1044
time: 50 min

## The problem

Return a longest substring that occurs at least twice in a string. The occurrences may overlap; if several answers have the same maximum length, any is acceptable. Return the empty string if there is no repeated nonempty substring. For `banana`, `ana` occurs at positions 1 and 3.

## Constraints and what they imply

Inputs can be long, around 30,000 characters, so enumerating every substring and comparing every pair is impractical. Overlaps must not be excluded. Exact answers are required: a hash collision cannot be accepted as evidence that two windows match. This implementation uses Unicode code-point ordering and a deterministic suffix-array construction; it does not depend on a small alphabet or a probabilistic hash.

## Brute force

For every pair of starting positions, compare characters until they differ or one suffix ends, retaining the longest common prefix. There are O(n²) pairs and each comparison may inspect O(n) characters, for O(n³) worst-case time with O(1) auxiliary workspace apart from the output. For example, a string of identical characters makes many comparisons very long.

## The insight

Sort all suffixes lexicographically. If two suffixes share a prefix x, every suffix between them in sorted order also begins with x: strings beginning with x form one contiguous lexicographic interval. Consequently the maximum common prefix of any pair is attained by some adjacent pair. The desired repeated substring is precisely such a common prefix, because every repeated substring begins two suffixes.

Construct the suffix order by doubling. Initially rank each suffix by its first character. If ranks distinguish prefixes of length k, sort suffix starts by the pair of ranks for the first k characters and the next k characters. An out-of-range second half receives rank zero, smaller than any real rank. Equal pairs receive equal new ranks, and unequal pairs are ranked in sorted order; therefore the new ranks describe prefixes of length 2k. Once all ranks differ, the sorted order is the complete suffix order.

The ranks are consecutive integers, so each round can sort pairs in linear time with two stable counting sorts: first by the second rank, then by the first. Stability preserves the second-key order among entries with the same first key. This avoids an additional comparison-sort logarithm in every doubling round.

Next compute adjacent common-prefix lengths in linear time. Scan starts in text order, comparing each suffix to the preceding suffix in sorted order. If the preceding comparison matched h characters, dropping the first character leaves at least h - 1 matching characters with some earlier suffix. The immediate lexicographic predecessor shares at least that much, so reuse h - 1 before comparing further. The height falls by at most one per iteration and grows only when characters are actually compared, making the total growth linear.

## Optimal solution, traced

```steps
Sort the suffixes of banana
    a, ana, anana, banana, na, nana
---
Adjacent ana and anana share three leading characters
    the maximum adjacent common prefix is {{ana}}
```

The two `ana` occurrences overlap, which is allowed. The algorithm stores their starting positions rather than requiring disjoint windows. The sentinel rank is numeric and is used only for absent suffix halves; no input character is reserved as a separator.

## Code

```python
def longest_duplicate(s):
    n = len(s)
    if n < 2:
        return ""
    suffixes = sorted(range(n), key=s.__getitem__)
    rank = [0] * n
    classes = 0
    for j, start in enumerate(suffixes):
        if j == 0 or s[start] != s[suffixes[j - 1]]:
            classes += 1
        rank[start] = classes

    def counting_sort(indices, keys, maximum):
        counts = [0] * (maximum + 1)
        for i in indices:
            counts[keys[i]] += 1
        total = 0
        for key in range(len(counts)):
            count = counts[key]
            counts[key] = total
            total += count
        output = [0] * len(indices)
        for i in indices:
            key = keys[i]
            output[counts[key]] = i
            counts[key] += 1
        return output

    width = 1
    while width < n:
        second = [rank[i + width] if i + width < n else 0 for i in range(n)]
        suffixes = counting_sort(suffixes, second, classes)
        suffixes = counting_sort(suffixes, rank, classes)
        new_rank = [0] * n
        new_rank[suffixes[0]] = 1
        for j in range(1, n):
            a, b = suffixes[j - 1], suffixes[j]
            a_key = (rank[a], second[a])
            b_key = (rank[b], second[b])
            new_rank[b] = new_rank[a] + (a_key != b_key)
        rank = new_rank
        classes = rank[suffixes[-1]]
        if classes == n:
            break
        width *= 2
    position = [0] * n
    for j, start in enumerate(suffixes):
        position[start] = j
    height = best = best_start = 0
    for start in range(n):
        j = position[start]
        if j == 0:
            height = 0
            continue
        other = suffixes[j - 1]
        while start + height < n and other + height < n and s[start + height] == s[other + height]:
            height += 1
        if height > best:
            best, best_start = height, start
        if height:
            height -= 1
    return s[best_start:best_start + best]
```

## Complexity

There are O(log n) doubling rounds. Each pair of counting sorts and rank assignment takes O(n) time because there are at most n ranks. Sorting the starting positions by their first characters initially takes O(n log n) comparison time, and the adjacent-prefix pass is O(n), for O(n log n) total time. Arrays and counting buckets occupy O(n) auxiliary space, plus O(n) for the returned slice. This deterministic bound avoids collision-based correctness qualifications.

## Mistakes and edge cases

- Do not require occurrences to be disjoint; `aaaa` has answer `aaa`.
- Sorting suffix strings directly creates O(n²) total copied characters in Python.
- Give a missing second half a rank below every real rank.
- Reset the reused prefix height when there is no predecessor.
- Check empty, one-character, all-distinct, and all-equal inputs.

## Variations

- Use binary search and rolling hashes, verifying every hash collision against the original characters.
- Build a suffix automaton and track occurrence counts to locate a longest repeated substring.
- Restrict matches to nonoverlapping positions, which changes the feasibility condition.

=== card | 2223
time: 45 min

## The problem

For each suffix of a string, measure how many leading characters it shares with the whole string. Return the sum of those lengths, including the whole string's contribution. For `ababa`, the contributions are 5, 0, 3, 0, and 1, totaling 9.

## Constraints and what they imply

Suffixes are identified by starting positions, so repeated suffix-prefix matches contribute separately. The empty input has sum zero. A string of n identical characters has sum n(n + 1)/2; fixed-width implementations should therefore use a sufficiently wide result. Each character is compared as a Python code point, with no case folding or normalization.

## Brute force

For every start i, compare `s[0]` with `s[i]`, then advance both positions until a mismatch or the end. On a run of identical characters this performs n + (n - 1) + ... + 1 comparisons, so time is O(n²). It needs O(1) auxiliary space if it uses indices rather than materializing suffixes.

## The insight

The Z-array stores exactly the needed values for positions i > 0: z[i] is the length of the common prefix of s and s[i:]. The contribution at i = 0 is n. Maintain a half-open interval [left, right) that matches the prefix and has the furthest right endpoint found so far. If i lies inside this interval, the earlier Z-value at i - left supplies a known match, clipped to right - i. Beyond right, or when i is outside the box, compare explicitly.

The clipped reuse is safe because each position in the box equals the corresponding prefix position. When the mirrored Z-value ends strictly before the box boundary, its next mismatch is also a mismatch at i. When it reaches the boundary, the next characters have not yet been certified, so explicit comparisons extend the match. Update the box if the new match ends later. This yields the exact z[i] for each position by induction.

All successful comparisons beyond a current box extend the rightmost boundary, which never moves backward. At most one failed comparison ends each position's expansion. Along with constant work per position, this proves linear total time even on highly repetitive strings.

## Optimal solution, traced

```steps
s = ababa: the whole suffix contributes 5
    z[1] = 0, z[2] = 3 for aba
---
The remaining Z values are 0 and 1
    5 + 0 + 3 + 0 + 1 = {{9}}
```

At position 4, the known box from position 2 covers the final character, allowing the algorithm to reuse a length-one match. The half-open boundary makes the available reuse length `right - i`, not `right - i + 1`.

Consider a different box where the mirrored value is shorter than the remaining box: its mismatch is already inside the region known to equal the prefix. That mismatch proves the current value cannot extend, so reuse does not silently skip a better match. If the mirrored match fills the remainder, however, the character after the boundary has not been compared yet. The explicit loop tests it and may grow the box. This distinction prevents a common error: copying a mirrored Z-value without considering how much of it is certified by the current box.

## Code

```python
def sum_suffix_scores(s):
    n = len(s)
    z = [0] * n
    left = right = 0
    for i in range(1, n):
        if i < right:
            z[i] = min(right - i, z[i - left])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] > right:
            left, right = i, i + z[i]
    return n + sum(z)
```

## Complexity

The Z-array is built in O(n) time and stored in O(n) auxiliary space. Summing it is another O(n) pass. For n = 0, the loop and sum are empty and the result is zero.

## Mistakes and edge cases

- Do not forget the whole string's contribution n; z[0] here is deliberately zero.
- Clip a reused value at the right boundary of the current box.
- Do not count only distinct suffixes or distinct matching prefix strings.
- Use a wide enough integer in fixed-width languages for a quadratic-size sum.
- Test empty, one-character, all-identical and no-repetition inputs.

## Variations

- Return the Z-array itself to expose the individual suffix scores.
- Match a pattern against text with a Z-array and a separator guaranteed not to occur in either.
- Find all prefix lengths that also occur at selected positions by inspecting Z-values.
