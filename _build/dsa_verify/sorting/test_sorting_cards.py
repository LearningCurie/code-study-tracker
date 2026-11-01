"""Independent small-input checks of the Python blocks displayed in the sorting cards."""

import itertools
import random
import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARDS = ROOT / "dsa" / "13-sorting.cards.md"
MODULE = ROOT / "dsa" / "13-sorting.md"


def load_blocks():
    source = CARDS.read_text(encoding="utf-8")
    cards = re.split(r"(?m)^=== card \| ", source)[1:]
    result = {}
    for card in cards:
        pid, _, body = card.partition("\n")
        blocks = re.findall(r"```python\n(.*?)\n```", body, re.S)
        if pid in result or len(blocks) != 1:
            raise AssertionError(f"expected exactly one Python block for {pid}")
        namespace = {}
        exec(compile(blocks[0], f"{CARDS.name}:{pid}", "exec"), namespace)
        result[pid] = namespace
    return result


BLOCKS = load_blocks()


def lists(domain, maximum_length):
    for size in range(maximum_length + 1):
        for values in itertools.product(domain, repeat=size):
            yield list(values)


def is_wiggle(values):
    return all(
        values[i] < values[i + 1] if i % 2 == 0 else values[i] > values[i + 1]
        for i in range(len(values) - 1)
    )


class SortingCardTests(unittest.TestCase):
    def setUp(self):
        self.random = random.Random(19053)

    def test_exact_practice_and_block_coverage(self):
        practice = MODULE.read_text(encoding="utf-8").split("=== practice\n", 1)[1]
        ids = re.findall(r"(?m)^- ([\w:-]+) (?:core|derive|stretch|mixed)$", practice)
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(set(ids), set(BLOCKS))

    def test_relative_sort(self):
        solve = BLOCKS["1122"]["relative_sort"]
        for values in lists(range(3), 5):
            present = sorted(set(values))
            for size in range(len(present) + 1):
                for priority in itertools.permutations(present, size):
                    rank = {value: index for index, value in enumerate(priority)}
                    expected = sorted(values, key=lambda x: (0, rank[x]) if x in rank else (1, x))
                    original = values[:]
                    self.assertEqual(solve(values, priority), expected)
                    self.assertEqual(values, original)
        self.assertEqual(solve([1000, 0, 1000], [1000]), [1000, 1000, 0])
        self.assertEqual(solve([2, 1, 2, 3, 1], [2, 1]), [2, 2, 1, 1, 3])

    def test_frequency_sort_numbers(self):
        solve = BLOCKS["1636"]["frequency_sort_numbers"]
        for values in lists(range(-2, 3), 6):
            expected = sorted(values, key=lambda x: (values.count(x), -x))
            self.assertEqual(solve(values), expected)
        self.assertEqual(solve([4, 4, -1, -1, 2]), [2, 4, 4, -1, -1])

    def test_largest_perimeter(self):
        solve = BLOCKS["976"]["largest_perimeter"]
        for values in lists(range(1, 5), 6):
            best = 0
            for triple in itertools.combinations(values, 3):
                if sum(triple) - max(triple) > max(triple):
                    best = max(best, sum(triple))
            self.assertEqual(solve(values), best)
        self.assertEqual(solve([2, 1, 2, 4]), 5)

    def test_merge_sort(self):
        solve = BLOCKS["912"]["merge_sort"]
        for values in lists(range(-2, 3), 6):
            original = values[:]
            result = solve(values)
            self.assertEqual(result, sorted(values))
            self.assertEqual(values, original)
            self.assertIsNot(result, values)

        class Record:
            def __init__(self, key, tag):
                self.key, self.tag = key, tag

            def __le__(self, other):
                return self.key <= other.key

        records = [Record(1, "a"), Record(0, "x"), Record(1, "b"), Record(0, "y")]
        self.assertEqual([x.tag for x in solve(records)], ["x", "y", "a", "b"])
        self.assertEqual(solve([3, -1, 3, 2]), [-1, 2, 3, 3])

    def test_largest_number(self):
        solve = BLOCKS["179"]["largest_number"]
        for _ in range(1200):
            values = [self.random.randrange(0, 1000) for _ in range(self.random.randrange(1, 8))]
            choices = ("".join(map(str, ordering)) for ordering in itertools.permutations(values))
            best = max(choices)
            expected = best.lstrip("0") or "0"
            self.assertEqual(solve(values), expected, values)
        for values in ([0, 0], [12, 1212], [3, 30, 34], [], [10, 2]):
            expected = max(("".join(map(str, p)) for p in itertools.permutations(values)), default="")
            self.assertEqual(solve(values), expected.lstrip("0") or "0")

    def test_frequency_sort_characters(self):
        solve = BLOCKS["451"]["frequency_sort_characters"]
        for chars in lists("abA", 7):
            text = "".join(chars)
            result = solve(text)
            counts = Counter(text)
            self.assertEqual(Counter(result), counts)
            groups = [(char, len(list(group))) for char, group in itertools.groupby(result)]
            self.assertEqual(len(groups), len(counts))
            self.assertTrue(all(length == counts[char] for char, length in groups))
            self.assertTrue(all(groups[i][1] >= groups[i + 1][1] for i in range(len(groups) - 1)))
        self.assertEqual(solve("tree"), "eetr")
        self.assertEqual(Counter(solve("éAé🙂A🙂🙂")), Counter("éAé🙂A🙂🙂"))

    def test_h_index(self):
        solve = BLOCKS["274"]["h_index"]
        for values in lists(range(5), 6):
            expected = max(h for h in range(len(values) + 1) if sum(x >= h for x in values) >= h)
            self.assertEqual(solve(values), expected)
        self.assertEqual(solve([3, 0, 6, 1, 5]), 3)
        self.assertEqual(solve([10**20, 0, 10**30]), 2)

    def test_kth_largest_string(self):
        solve = BLOCKS["1985"]["kth_largest_string"]
        for _ in range(4000):
            values = [str(self.random.randrange(100000)) for _ in range(self.random.randrange(1, 16))]
            if self.random.randrange(3) == 0:
                values.append("9" * self.random.randrange(50, 101))
            expected = sorted(map(int, values), reverse=True)
            for k, number in enumerate(expected, 1):
                self.assertEqual(solve(values, k), str(number))
        self.assertEqual(solve(["3", "21", "100", "21"], 2), "21")
        for values, k in [([], 1), (["3"], 0), (["3"], 2)]:
            with self.assertRaises(ValueError):
                solve(values, k)

    def test_maximum_gap(self):
        solve = BLOCKS["164"]["maximum_gap"]
        for values in lists(range(-2, 3), 6):
            ordered = sorted(values)
            expected = max((b - a for a, b in zip(ordered, ordered[1:])), default=0)
            self.assertEqual(solve(values), expected)
        self.assertEqual(solve([3, 6, 9, 1]), 3)
        self.assertEqual(solve([-10**30, 0, 10**30]), 10**30)

    def test_reverse_pairs(self):
        solve = BLOCKS["493"]["reverse_pairs"]
        for values in lists(range(-2, 3), 7):
            expected = sum(values[i] > 2 * values[j]
                           for i in range(len(values)) for j in range(i + 1, len(values)))
            original = values[:]
            self.assertEqual(solve(values), expected, values)
            self.assertEqual(values, original)
        self.assertEqual(solve([1, 3, 2, 3, 1]), 2)
        self.assertEqual(solve([2**31 - 1, -(2**31)]), 1)

    def test_wiggle_sort(self):
        solve = BLOCKS["324"]["wiggle_sort"]
        # A brute-force permutation oracle determines feasibility independently.
        for n in range(9):
            for combination in itertools.combinations_with_replacement(range(4), n):
                feasible = any(is_wiggle(candidate) for candidate in set(itertools.permutations(combination)))
                if not feasible:
                    continue
                for start in (list(combination), list(reversed(combination))):
                    self.assertIsNone(solve(start))
                    self.assertEqual(Counter(start), Counter(combination))
                    self.assertTrue(is_wiggle(start), (combination, start))
        example = [1, 5, 1, 1, 6, 4]
        solve(example)
        self.assertEqual(example, [1, 6, 1, 5, 1, 4])

    def test_insertion_swap_count(self):
        solve = BLOCKS["hr:ctci-merge-sort"]["insertion_swap_count"]
        for values in lists(range(-2, 3), 7):
            work = values[:]
            swaps = 0
            for i in range(1, len(work)):
                j = i
                while j and work[j - 1] > work[j]:
                    work[j - 1], work[j] = work[j], work[j - 1]
                    swaps += 1
                    j -= 1
            self.assertEqual(solve(values), swaps, values)
        self.assertEqual(solve([2, 1, 3, 1]), 3)
        self.assertEqual(solve(list(range(1000, 0, -1))), 1000 * 999 // 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
