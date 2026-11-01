import itertools
import random
import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "dsa"
EXPECTED = {
    "28-strings.cards.md": {
        "205", "28", "459", "5", "647", "151", "8", "38",
        "1392", "214", "1044", "2223",
    },
    "35-storage.cards.md": {"1206"},
}


def load_cards():
    cards = {}
    for filename, expected in EXPECTED.items():
        text = (ROOT / filename).read_text(encoding="utf-8")
        chunks = re.split(r"(?m)^=== card \| (\S+)\s*\n", text)
        if chunks[0].strip():
            raise AssertionError(f"Unexpected text before first card in {filename}")
        pairs = list(zip(chunks[1::2], chunks[2::2]))
        if len(pairs) != len(expected) or {pid for pid, _ in pairs} != expected:
            raise AssertionError(f"Incorrect card coverage in {filename}")
        for pid, body in pairs:
            blocks = re.findall(r"```python\n(.*?)\n```", body, re.S)
            if len(blocks) != 1:
                raise AssertionError(f"{pid} must have exactly one tested Python block")
            namespace = {}
            exec(compile(blocks[0], f"{filename}:{pid}", "exec"), namespace)
            cards[pid] = namespace
    return cards


CARDS = load_cards()


def strings(alphabet, maximum):
    for length in range(maximum + 1):
        for chars in itertools.product(alphabet, repeat=length):
            yield "".join(chars)


def palindrome(s):
    return s == s[::-1]


class StringCards(unittest.TestCase):
    def test_isomorphic_against_all_position_pairs(self):
        solve = CARDS["205"]["is_isomorphic"]
        choices = list(strings("ab", 4))
        for source in choices:
            for target in choices:
                expected = len(source) == len(target) and all(
                    (source[i] == source[j]) == (target[i] == target[j])
                    for i in range(len(source)) for j in range(len(source))
                )
                self.assertEqual(solve(source, target), expected, (source, target))
        self.assertTrue(solve("😀é😀", "x#x"))

    def test_find_against_builtin(self):
        solve = CARDS["28"]["find_first"]
        patterns = list(strings("ab", 4))
        for text in strings("ab", 7):
            for pattern in patterns:
                self.assertEqual(solve(text, pattern), text.find(pattern), (text, pattern))
        self.assertEqual(solve("😀#😀#", "#😀"), 1)

    def test_repetition_against_candidate_enumeration(self):
        solve = CARDS["459"]["repeated_substring"]
        for s in strings("ab", 10):
            expected = any(
                len(s) % length == 0 and s[:length] * (len(s) // length) == s
                for length in range(1, len(s))
            )
            self.assertEqual(solve(s), expected, s)

    def test_longest_palindrome_against_all_substrings(self):
        solve = CARDS["5"]["longest_palindrome"]
        for s in strings("abc", 7):
            candidates = [s[i:j] for i in range(len(s) + 1)
                          for j in range(i, len(s) + 1) if palindrome(s[i:j])]
            result = solve(s)
            self.assertIn(result, candidates, s)
            self.assertEqual(len(result), max(map(len, candidates)), s)

    def test_palindrome_count_against_all_substrings(self):
        solve = CARDS["647"]["count_palindromes"]
        for s in strings("abc", 7):
            expected = sum(palindrome(s[i:j]) for i in range(len(s))
                           for j in range(i + 1, len(s) + 1))
            self.assertEqual(solve(s), expected, s)
        self.assertEqual(solve("a" * 100), 5050)

    def test_reverse_words_against_regex_tokenization(self):
        solve = CARDS["151"]["reverse_words"]
        for s in strings("ab \t", 6):
            expected = " ".join(reversed(re.findall(r"[^ ]+", s)))
            self.assertEqual(solve(s), expected, repr(s))

    def test_atoi_against_regex_and_integer_clamp(self):
        solve = CARDS["8"]["parse_int32"]
        for s in itertools.chain(strings(" +-019x\t", 5), [
            "2147483647", "2147483648", "-2147483648", "-2147483649",
            "9" * 300, "-" + "9" * 300, "٠12", "0000000002147483648",
        ]):
            match = re.match(r" *([+-]?)([0-9]+)", s)
            value = int((match.group(1) or "") + match.group(2)) if match else 0
            expected = min((1 << 31) - 1, max(-(1 << 31), value))
            self.assertEqual(solve(s), expected, repr(s))
        self.assertEqual(solve("9" * 10000), (1 << 31) - 1)

    def test_count_and_say_against_groupby(self):
        solve = CARDS["38"]["count_and_say"]
        term = "1"
        for n in range(1, 21):
            self.assertEqual(solve(n), term, n)
            term = "".join(str(len(list(group))) + char
                           for char, group in itertools.groupby(term))
        for n in [0, -1]:
            with self.assertRaises(ValueError):
                solve(n)

    def test_border_against_direct_prefix_suffix_comparison(self):
        solve = CARDS["1392"]["longest_border"]
        for s in strings("abc", 8):
            options = [s[:length] for length in range(1, len(s))
                       if s[:length] == s[-length:]]
            self.assertEqual(solve(s), max(options, key=len, default=""), s)

    def test_shortest_palindrome_against_all_added_strings(self):
        solve = CARDS["214"]["shortest_front_palindrome"]
        for s in strings("ab#", 5):
            result = solve(s)
            self.assertTrue(result.endswith(s), s)
            self.assertTrue(palindrome(result), (s, result))
            possible = [prefix + s
                        for length in range(len(s) + 1)
                        for chars in itertools.product("ab#", repeat=length)
                        if palindrome((prefix := "".join(chars)) + s)]
            self.assertEqual(len(result), min(map(len, possible)), s)
        for s in ["a#b", "\0😀\0x", "aaaa", "😀"]:
            result = solve(s)
            self.assertTrue(result.endswith(s) and palindrome(result))
            best_prefix = max(i for i in range(len(s) + 1) if palindrome(s[:i]))
            self.assertEqual(len(result), 2 * len(s) - best_prefix)

    def test_longest_duplicate_against_all_start_pairs(self):
        solve = CARDS["1044"]["longest_duplicate"]
        for s in strings("abc", 7):
            best = 0
            for i in range(len(s)):
                for j in range(i + 1, len(s)):
                    length = 0
                    while j + length < len(s) and s[i + length] == s[j + length]:
                        length += 1
                    best = max(best, length)
            result = solve(s)
            self.assertEqual(len(result), best, s)
            if result:
                first = s.find(result)
                self.assertNotEqual(s.find(result, first + 1), -1, (s, result))
        self.assertEqual(solve("a" * 30000), "a" * 29999)

    def test_suffix_score_against_direct_comparisons(self):
        solve = CARDS["2223"]["sum_suffix_scores"]
        for s in strings("abc", 8):
            total = 0
            for start in range(len(s)):
                for offset in range(len(s) - start):
                    if s[offset] != s[start + offset]:
                        break
                    total += 1
            self.assertEqual(solve(s), total, s)
        self.assertEqual(solve("a" * 10000), 10000 * 10001 // 2)


class SkipListCards(unittest.TestCase):
    def assert_structure(self, skip, counts):
        head = skip.head
        self.assertGreaterEqual(len(head.next), 1)
        if len(head.next) > 1:
            self.assertIsNotNone(head.next[-1])
        levels = []
        for level in range(len(head.next)):
            nodes = []
            seen = set()
            node = head.next[level]
            while node is not None:
                self.assertNotIn(id(node), seen, "cycle")
                seen.add(id(node))
                self.assertGreater(len(node.next), level)
                nodes.append(node)
                node = node.next[level]
            self.assertEqual([node.value for node in nodes],
                             sorted(node.value for node in nodes))
            levels.append(nodes)
        self.assertEqual(Counter(node.value for node in levels[0]), counts)
        for level in range(1, len(levels)):
            self.assertEqual(levels[level],
                             [node for node in levels[0] if len(node.next) > level])

    def test_random_operations_against_counter_and_tower_invariants(self):
        cls = CARDS["1206"]["SkipList"]
        for seed in range(30):
            operations = random.Random(seed)
            skip = cls(random.Random(seed + 500))
            counts = Counter()
            for step in range(500):
                value = operations.randrange(-8, 9)
                op = operations.choice(("add", "add", "erase", "search"))
                if op == "add":
                    skip.add(value)
                    counts[value] += 1
                elif op == "erase":
                    present = counts[value] > 0
                    self.assertEqual(skip.erase(value), present, (seed, step, value))
                    if present:
                        counts[value] -= 1
                        if counts[value] == 0:
                            del counts[value]
                else:
                    self.assertEqual(skip.search(value), counts[value] > 0)
                self.assert_structure(skip, counts)
            for value in list(counts):
                while counts[value]:
                    self.assertTrue(skip.erase(value))
                    counts[value] -= 1
                del counts[value]
            self.assert_structure(skip, counts)
            self.assertFalse(skip.erase(99))

    def test_duplicate_node_with_different_towers(self):
        cls = CARDS["1206"]["SkipList"]

        class Promotions:
            def __init__(self):
                self.coins = iter([0, 0, 1, 1])

            def randrange(self, stop):
                return next(self.coins)

        skip = cls(Promotions())
        skip.add(4)  # Older copy has height three.
        skip.add(4)  # Newer copy has height one.
        self.assertTrue(skip.erase(4))
        self.assertTrue(skip.search(4))
        self.assertEqual(len(skip.head.next), 3)
        self.assertTrue(skip.erase(4))
        self.assertFalse(skip.search(4))
        self.assertEqual(len(skip.head.next), 1)


if __name__ == "__main__":
    unittest.main()
