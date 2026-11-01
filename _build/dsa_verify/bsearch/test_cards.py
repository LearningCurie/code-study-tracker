"""Exercise every displayed binary-search card block against independent small oracles."""

import itertools
import random
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARD_PATH = ROOT / "dsa" / "11-bsearch.cards.md"
MODULE_PATH = ROOT / "dsa" / "11-bsearch.md"
EXPECTED = {
    "35": "search_insert", "34": "search_range", "153": "find_min_distinct",
    "33": "search_rotated", "162": "find_peak", "875": "min_eating_speed",
    "1011": "ship_within_days", "1552": "max_min_distance", "410": "split_array",
    "719": "kth_pair_distance", "4": "median_two_sorted", "154": "find_min_with_duplicates",
}
COUNTS = {pid: 0 for pid in EXPECTED}


def load_solutions():
    text = CARD_PATH.read_text(encoding="utf-8")
    chunks = re.split(r"(?m)^=== card \| (\S+)\s*$", text)
    if chunks[0].strip():
        raise AssertionError("unexpected text before first card")
    cards = dict(zip(chunks[1::2], chunks[2::2]))
    if len(cards) != (len(chunks) - 1) // 2:
        raise AssertionError("duplicate card ID")
    practice = set(re.findall(r"(?m)^- (\d+) (?:core|derive|stretch|mixed)\s*$",
                              MODULE_PATH.read_text(encoding="utf-8")))
    if set(cards) != practice or set(cards) != set(EXPECTED):
        raise AssertionError(f"card/practice/test mismatch: {set(cards)}, {practice}, {set(EXPECTED)}")
    solutions = {}
    for pid, card in cards.items():
        blocks = re.findall(r"```python\n(.*?)\n```", card, re.S)
        if len(blocks) != 1:
            raise AssertionError(f"card {pid}: expected exactly one displayed Python block")
        if blocks[0] not in card.split("## Code", 1)[1].split("## Complexity", 1)[0]:
            raise AssertionError(f"card {pid}: code outside the Code section")
        namespace = {}
        exec(compile(blocks[0], f"{CARD_PATH.name}:{pid}", "exec"), namespace)
        solutions[pid] = namespace[EXPECTED[pid]]
    return solutions


SOLVE = load_solutions()


def partition_largest_sums(values):
    """List (number of groups, largest sum) for every nonempty contiguous partition."""
    n = len(values)
    for cuts in itertools.product((False, True), repeat=n - 1):
        groups, running, largest = 1, values[0], 0
        for cut, value in zip(cuts, values[1:]):
            if cut:
                largest = max(largest, running)
                running = value
                groups += 1
            else:
                running += value
        yield groups, max(largest, running)


class BinarySearchCards(unittest.TestCase):
    def check(self, pid, actual, expected):
        COUNTS[pid] += 1
        self.assertEqual(actual, expected, f"card {pid}, case {COUNTS[pid]}")

    def test_lower_bound_and_range(self):
        for n in range(7):
            for values in itertools.combinations_with_replacement(range(-2, 3), n):
                nums = list(values)
                for target in range(-3, 4):
                    indices = [i for i, x in enumerate(nums) if x == target]
                    insertion = next((i for i, x in enumerate(nums) if x >= target), n)
                    span = [indices[0], indices[-1]] if indices else [-1, -1]
                    self.check("35", SOLVE["35"](nums, target), insertion)
                    self.check("34", SOLVE["34"](nums, target), span)
                    self.assertEqual(nums, list(values))

    def test_rotated_distinct(self):
        self.check("33", SOLVE["33"]([], 0), -1)
        for n in range(1, 8):
            for values in itertools.combinations(range(-4, 5), n):
                for cut in range(n):
                    nums = list(values[cut:] + values[:cut])
                    before = nums[:]
                    self.check("153", SOLVE["153"](nums), min(nums))
                    for target in range(-5, 6):
                        expected = nums.index(target) if target in nums else -1
                        self.check("33", SOLVE["33"](nums, target), expected)
                    self.assertEqual(nums, before)

    def test_peak_against_neighbor_definition(self):
        for n in range(1, 8):
            for values in itertools.product(range(4), repeat=n):
                if any(a == b for a, b in zip(values, values[1:])):
                    continue
                peak = SOLVE["162"](values)
                valid = [i for i, x in enumerate(values)
                         if (i == 0 or x > values[i - 1])
                         and (i == n - 1 or x > values[i + 1])]
                self.check("162", peak in valid, True)

    def test_rate_against_enumeration(self):
        for n in range(1, 5):
            for piles in itertools.product(range(1, 6), repeat=n):
                for hours in range(n, n + 7):
                    expected = next(rate for rate in range(1, max(piles) + 1)
                                    if sum(len(range(0, p, rate)) for p in piles) <= hours)
                    self.check("875", SOLVE["875"](piles, hours), expected)

    def test_shipping_against_all_cut_patterns(self):
        for n in range(1, 6):
            for weights in itertools.product(range(1, 5), repeat=n):
                options = list(partition_largest_sums(weights))
                for days in range(1, n + 3):
                    expected = min(largest for groups, largest in options if groups <= days)
                    self.check("1011", SOLVE["1011"](weights, days), expected)

    def test_maximum_spacing_against_combinations(self):
        for n in range(2, 8):
            for positions in itertools.combinations(range(-4, 5), n):
                for m in range(2, n + 1):
                    expected = max(min(abs(x - y) for x, y in itertools.combinations(choice, 2))
                                   for choice in itertools.combinations(positions, m))
                    shuffled = list(reversed(positions))
                    self.check("1552", SOLVE["1552"](shuffled, m), expected)
                    self.assertEqual(shuffled, list(reversed(positions)))

    def test_split_against_all_exact_partitions(self):
        for n in range(1, 7):
            for nums in itertools.product(range(4), repeat=n):
                options = list(partition_largest_sums(nums))
                for k in range(1, n + 1):
                    expected = min(largest for groups, largest in options if groups == k)
                    self.check("410", SOLVE["410"](nums, k), expected)

    def test_pair_distance_against_sorted_pairs(self):
        rng = random.Random(719)
        cases = [nums for n in range(2, 7) for nums in itertools.product(range(3), repeat=n)]
        cases += [tuple(rng.randint(-30, 30) for _ in range(rng.randint(2, 10)))
                  for _ in range(500)]
        for nums in cases:
            ordered = sorted(abs(x - y) for x, y in itertools.combinations(nums, 2))
            for k, expected in enumerate(ordered, 1):
                self.check("719", SOLVE["719"](nums, k), expected)

    def test_median_against_merge(self):
        arrays = [values for n in range(5)
                  for values in itertools.combinations_with_replacement(range(-2, 3), n)]
        for a in arrays:
            for b in arrays:
                if not a and not b:
                    continue
                merged = sorted(a + b)
                middle = len(merged) // 2
                expected = (merged[middle] if len(merged) % 2
                            else (merged[middle - 1] + merged[middle]) / 2)
                self.check("4", SOLVE["4"](a, b), expected)
        with self.assertRaises(ValueError):
            SOLVE["4"]([], [])

    def test_duplicate_rotation_against_min(self):
        for n in range(1, 9):
            for values in itertools.combinations_with_replacement(range(-2, 3), n):
                for cut in range(n):
                    nums = list(values[cut:] + values[:cut])
                    before = nums[:]
                    self.check("154", SOLVE["154"](nums), min(nums))
                    self.assertEqual(nums, before)

    @classmethod
    def tearDownClass(cls):
        print("\nOracle cases per card: " + ", ".join(f"{pid}={COUNTS[pid]}" for pid in EXPECTED))
        print(f"Total oracle cases: {sum(COUNTS.values())}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
