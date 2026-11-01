"""Exercise the actual card blocks against independent small-input oracles."""

import itertools
import random
import re
import unittest
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dsa" / "08-twoptr.cards.md"
LESSON = ROOT / "dsa" / "08-twoptr.md"
CARDS = {
    match.group(1): match.group(2)
    for match in re.finditer(r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)", SOURCE.read_text())
}
FUNCTIONS = {
    "283": "move_zeroes",
    "680": "valid_palindrome",
    "88": "merge_sorted",
    "167": "two_sum_sorted",
    "881": "rescue_boats",
    "15": "three_sum",
    "75": "sort_colors",
    "11": "max_container",
    "42": "trapped_water",
    "18": "four_sum",
    "611": "triangle_count",
}


def load_solution(problem):
    blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"card {problem}: expected exactly one Python block, got {len(blocks)}")
    namespace = {}
    exec(compile(blocks[0], f"{SOURCE.name}:{problem}", "exec"), namespace)
    return namespace[FUNCTIONS[problem]]


def arrays(alphabet, maximum):
    for size in range(maximum + 1):
        yield from itertools.product(alphabet, repeat=size)


@lru_cache(maxsize=None)
def boat_oracle(weights, limit):
    if not weights:
        return 0
    first, rest = weights[0], weights[1:]
    best = 1 + boat_oracle(rest, limit)
    for i, partner in enumerate(rest):
        if first + partner <= limit:
            best = min(best, 1 + boat_oracle(rest[:i] + rest[i + 1:], limit))
    return best


class TestTwoPointerCards(unittest.TestCase):
    def test_exact_card_and_block_coverage(self):
        practice = LESSON.read_text().split("=== practice\n", 1)[1]
        ids = re.findall(r"(?m)^- (\d+) (?:core|derive|stretch|mixed)\s*$", practice)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(FUNCTIONS))
        self.assertEqual(set(CARDS), set(FUNCTIONS))
        self.assertEqual(len(re.findall(r"(?m)^=== card \| ", SOURCE.read_text())), len(FUNCTIONS))
        for problem in ids:
            self.assertTrue(callable(load_solution(problem)))

    def test_move_zeroes(self):
        solve = load_solution("283")
        for original in arrays((-1, 0, 1), 7):
            data = list(original)
            result = solve(data)
            expected = [x for x in original if x != 0] + [0] * original.count(0)
            self.assertIsNone(result)
            self.assertEqual(data, expected, original)

    def test_valid_palindrome(self):
        solve = load_solution("680")
        for letters in arrays("abc", 7):
            text = "".join(letters)
            candidates = [text] + [text[:i] + text[i + 1:] for i in range(len(text))]
            expected = any(item == item[::-1] for item in candidates)
            self.assertEqual(solve(text), expected, text)

    def test_merge_sorted(self):
        solve = load_solution("88")
        choices = [tuple(x) for x in arrays((-2, 0, 1), 4) if list(x) == sorted(x)]
        for first in choices:
            for second in choices:
                # Spare cells are arbitrary: they must never be treated as data.
                data = list(first) + [999] * len(second)
                other = list(second)
                self.assertIsNone(solve(data, len(first), other, len(second)))
                self.assertEqual(data, sorted(first + second), (first, second))
                self.assertEqual(other, list(second))

    def test_two_sum_sorted(self):
        solve = load_solution("167")
        choices = [x for x in arrays((-2, -1, 0, 1, 2), 5) if list(x) == sorted(x)]
        for data in choices:
            for target in range(-5, 6):
                pairs = [(i + 1, j + 1) for i in range(len(data))
                         for j in range(i + 1, len(data)) if data[i] + data[j] == target]
                result = solve(data, target)
                if pairs:
                    self.assertIn(tuple(result), pairs, (data, target))
                else:
                    self.assertEqual(result, [], (data, target))

    def test_rescue_boats(self):
        solve = load_solution("881")
        for limit in range(1, 6):
            for weights in arrays(range(1, limit + 1), 5):
                data = list(weights)
                self.assertEqual(solve(data, limit), boat_oracle(weights, limit), (weights, limit))
                self.assertEqual(data, list(weights))

    def test_three_sum(self):
        solve = load_solution("15")
        for original in arrays((-2, -1, 0, 1, 2), 6):
            expected = {tuple(sorted(combo)) for combo in itertools.combinations(original, 3)
                        if sum(combo) == 0}
            actual = solve(list(original))
            self.assertEqual(len(actual), len({tuple(x) for x in actual}), original)
            self.assertTrue(all(x == sorted(x) for x in actual), original)
            self.assertEqual({tuple(x) for x in actual}, expected, original)

    def test_sort_colors(self):
        solve = load_solution("75")
        for original in arrays((0, 1, 2), 8):
            data = list(original)
            self.assertIsNone(solve(data))
            self.assertEqual(data, sorted(original), original)

    def test_max_container(self):
        solve = load_solution("11")
        for data in arrays(range(4), 7):
            expected = max(((j - i) * min(data[i], data[j])
                            for i in range(len(data)) for j in range(i + 1, len(data))),
                           default=0)
            self.assertEqual(solve(data), expected, data)

    def test_trapped_water(self):
        solve = load_solution("42")
        for data in arrays(range(4), 7):
            expected = sum(min(max(data[:i + 1]), max(data[i:])) - data[i]
                           for i in range(len(data)))
            self.assertEqual(solve(data), expected, data)

    def test_four_sum(self):
        solve = load_solution("18")
        rng = random.Random(18)
        cases = list(arrays((-1, 0, 1), 6))
        cases += [tuple(rng.randint(-5, 5) for _ in range(rng.randrange(10)))
                  for _ in range(3000)]
        for original in cases:
            for target in (-4, -1, 0, 2, 5):
                expected = {tuple(sorted(combo)) for combo in itertools.combinations(original, 4)
                            if sum(combo) == target}
                actual = solve(list(original), target)
                self.assertEqual(len(actual), len({tuple(x) for x in actual}), (original, target))
                self.assertTrue(all(x == sorted(x) for x in actual), (original, target))
                self.assertEqual({tuple(x) for x in actual}, expected, (original, target))

    def test_triangle_count(self):
        solve = load_solution("611")
        for data in arrays(range(4), 7):
            expected = sum(a + b > c and a + c > b and b + c > a
                           for a, b, c in itertools.combinations(data, 3))
            self.assertEqual(solve(data), expected, data)

    def test_published_trace_examples(self):
        data = [0, 4, 0, -2]
        load_solution("283")(data)
        self.assertEqual(data, [4, -2, 0, 0])
        self.assertTrue(load_solution("680")("abca"))
        data = [1, 4, 0, 0]
        load_solution("88")(data, 2, [2, 3], 2)
        self.assertEqual(data, [1, 2, 3, 4])
        self.assertEqual(load_solution("167")([1, 3, 4, 8], 7), [2, 3])
        self.assertEqual(load_solution("881")([1, 2, 2, 3], 3), 3)
        self.assertEqual(load_solution("15")([-2, 0, 1, 1, 2]), [[-2, 0, 2], [-2, 1, 1]])
        data = [2, 0, 2, 1, 0]
        load_solution("75")(data)
        self.assertEqual(data, [0, 0, 1, 2, 2])
        self.assertEqual(load_solution("11")([1, 4, 2, 3]), 6)
        self.assertEqual(load_solution("42")([2, 0, 1, 0, 2]), 5)
        self.assertEqual(load_solution("18")([1, 0, -1, 0, -2, 2], 0),
                         [[-2, -1, 1, 2], [-2, 0, 0, 2], [-1, 0, 0, 1]])
        self.assertEqual(load_solution("611")([2, 2, 3, 4]), 3)


if __name__ == "__main__":
    unittest.main()
