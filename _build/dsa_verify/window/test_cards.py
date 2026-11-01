import itertools
import math
import random
import re
import unittest
from collections import Counter
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "09-window.cards.md"
MODULE = SOURCE.with_name("09-window.md")
EXPECTED = {"643", "209", "3", "567", "424", "713", "904", "1658",
            "76", "992", "1838", "395"}
FUNCTIONS = {
    "643": "max_average",
    "209": "min_subarray_length",
    "3": "longest_distinct",
    "567": "contains_permutation",
    "424": "longest_replacement",
    "713": "count_product_less_than_k",
    "904": "longest_two_types",
    "1658": "min_end_removals",
    "76": "minimum_cover",
    "992": "exactly_k_distinct",
    "1838": "max_frequency_after_increments",
    "395": "longest_at_least_k",
}


def load_solutions():
    text = SOURCE.read_text(encoding="utf-8")
    practice = MODULE.read_text(encoding="utf-8").split("=== practice\n", 1)[1]
    practice_ids = re.findall(r"(?m)^- (\d+) (?:core|derive|stretch|mixed)\s*$",
                              practice)
    if len(practice_ids) != len(set(practice_ids)) or set(practice_ids) != EXPECTED:
        raise AssertionError(f"Unexpected or duplicate practice IDs: {practice_ids}")
    chunks = list(re.finditer(
        r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)", text
    ))
    ids = [match.group(1) for match in chunks]
    if len(ids) != len(set(ids)) or set(ids) != EXPECTED:
        raise AssertionError(f"Unexpected or duplicate card IDs: {ids}")
    solutions = {}
    for match in chunks:
        pid, card = match.groups()
        blocks = re.findall(r"```python\n(.*?)\n```", card, re.S)
        if len(blocks) != 1 or card.count("```python") != 1:
            raise AssertionError(f"Card {pid} must have exactly one Python block")
        namespace = {}
        exec(compile(blocks[0], f"{SOURCE.name}:{pid}", "exec"), namespace)
        solutions[pid] = namespace[FUNCTIONS[pid]]
    if text.count("```python") != len(chunks):
        raise AssertionError("Python block outside a card")
    return solutions


SOLVE = load_solutions()


def sequences(alphabet, max_length):
    for length in range(max_length + 1):
        yield from itertools.product(alphabet, repeat=length)


def blocks(values):
    for left in range(len(values)):
        for right in range(left + 1, len(values) + 1):
            yield values[left:right]


class WindowCardTests(unittest.TestCase):
    def test_fixed_average(self):
        solve = SOLVE["643"]
        for values in sequences((-2, 0, 3), 6):
            for k in range(1, len(values) + 1):
                expected = max(sum(values[i:i + k]) / k
                               for i in range(len(values) - k + 1))
                self.assertAlmostEqual(solve(values, k), expected)

    def test_minimum_positive_sum(self):
        solve = SOLVE["209"]
        for values in sequences((1, 2, 4), 6):
            for target in range(1, 13):
                expected = min((len(part) for part in blocks(values)
                                if sum(part) >= target), default=0)
                self.assertEqual(solve(target, values), expected, (values, target))

    def test_longest_distinct(self):
        solve = SOLVE["3"]
        for values in sequences("ab ", 7):
            s = "".join(values)
            expected = max((len(part) for part in blocks(s)
                            if len(set(part)) == len(part)), default=0)
            self.assertEqual(solve(s), expected, s)
        self.assertEqual(solve("🙂a🙂b"), 3)

    def test_permutation(self):
        solve = SOLVE["567"]
        patterns = ["".join(chars) for chars in sequences("abc", 3)]
        texts = ["".join(chars) for chars in sequences("abc", 5)]
        for pattern in patterns:
            for text in texts:
                m = len(pattern)
                expected = any(Counter(text[i:i + m]) == Counter(pattern)
                               for i in range(len(text) - m + 1))
                self.assertEqual(solve(pattern, text), expected, (pattern, text))

    def test_replacement(self):
        solve = SOLVE["424"]
        for values in sequences("ABC", 7):
            s = "".join(values)
            for k in range(4):
                expected = max((len(part) for part in blocks(s)
                                if len(part) - max(Counter(part).values()) <= k),
                               default=0)
                self.assertEqual(solve(s, k), expected, (s, k))

    def test_product(self):
        solve = SOLVE["713"]
        for values in sequences((1, 2, 3), 6):
            for k in range(0, 12):
                expected = sum(math.prod(part) < k for part in blocks(values))
                self.assertEqual(solve(values, k), expected, (values, k))
        self.assertEqual(solve([10, 5, 2, 6], 100), 8)

    def test_two_types(self):
        solve = SOLVE["904"]
        for values in sequences((0, 1, 2), 7):
            expected = max((len(part) for part in blocks(values)
                            if len(set(part)) <= 2), default=0)
            self.assertEqual(solve(values), expected, values)

    def test_end_removals(self):
        solve = SOLVE["1658"]
        for values in sequences((1, 2, 3), 6):
            for x in range(0, sum(values) + 2):
                candidates = [
                    left + right
                    for left in range(len(values) + 1)
                    for right in range(len(values) - left + 1)
                    if sum(values[:left]) + sum(values[len(values) - right:]) == x
                ]
                expected = min(candidates, default=-1)
                self.assertEqual(solve(values, x), expected, (values, x))

    def test_minimum_cover(self):
        solve = SOLVE["76"]
        targets = ["".join(chars) for chars in sequences("abc", 3)]
        sources = ["".join(chars) for chars in sequences("abc", 5)]
        for source in sources:
            for target in targets:
                need = Counter(target)
                candidates = [
                    (right - left, left, source[left:right])
                    for left in range(len(source) + 1)
                    for right in range(left, len(source) + 1)
                    if all(Counter(source[left:right])[c] >= count
                           for c, count in need.items())
                ]
                expected = min(candidates)[2] if candidates else ""
                self.assertEqual(solve(source, target), expected, (source, target))
        self.assertEqual(solve("ADOBECODEBANC", "ABC"), "BANC")

    def test_exactly_k(self):
        solve = SOLVE["992"]
        for values in sequences((1, 2, 3), 7):
            for k in range(-1, 5):
                expected = sum(len(set(part)) == k for part in blocks(values))
                self.assertEqual(solve(values, k), expected, (values, k))
        self.assertEqual(solve([1, 2, 1, 2, 3], 2), 7)

    def test_increment_frequency(self):
        solve = SOLVE["1838"]
        for values in sequences((1, 2, 4), 6):
            for k in range(6):
                # Enumerate subsets and their cheapest possible target: their maximum.
                expected = 0
                for mask in range(1, 1 << len(values)):
                    subset = [values[i] for i in range(len(values)) if mask & (1 << i)]
                    if sum(max(subset) - value for value in subset) <= k:
                        expected = max(expected, len(subset))
                original = list(values)
                self.assertEqual(solve(original, k), expected, (values, k))
                self.assertEqual(original, list(values))

    def test_minimum_frequencies(self):
        solve = SOLVE["395"]
        for values in sequences("abc", 6):
            s = "".join(values)
            for k in range(1, 5):
                expected = max((len(part) for part in blocks(s)
                                if min(Counter(part).values()) >= k), default=0)
                self.assertEqual(solve(s, k), expected, (s, k))
        rng = random.Random(395)
        for _ in range(300):
            s = "".join(rng.choice("abcde") for _ in range(rng.randrange(15)))
            k = rng.randrange(1, 6)
            expected = max((len(part) for part in blocks(s)
                            if min(Counter(part).values()) >= k), default=0)
            self.assertEqual(solve(s, k), expected, (s, k))


if __name__ == "__main__":
    unittest.main()
