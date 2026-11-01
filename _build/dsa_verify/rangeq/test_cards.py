import itertools
import random
import re
import unittest
from pathlib import Path


BUILD = Path(__file__).resolve().parents[2]
SOURCE = BUILD / "dsa" / "30-rangeq.cards.md"
MODULE = BUILD / "dsa" / "30-rangeq.md"
CARDS = {
    match.group(1): match.group(2)
    for match in re.finditer(
        r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)",
        SOURCE.read_text(),
    )
}


def solution(problem, name):
    blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"expected exactly one Python block in {problem}")
    namespace = {}
    exec(compile(blocks[0], f"card-{problem}", "exec"), namespace)
    return namespace[name]


class RangeQueryCards(unittest.TestCase):
    def test_coverage_and_blocks(self):
        practice = MODULE.read_text().split("=== practice\n", 1)[1]
        ids = re.findall(r"(?m)^- (\S+) (?:core|derive|stretch|mixed)$", practice)
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(ids), len(CARDS))
        self.assertEqual(set(ids), set(CARDS))
        for problem, card in CARDS.items():
            blocks = re.findall(r"```python\n(.*?)\n```", card, re.S)
            self.assertEqual(len(blocks), 1, problem)
            compile(blocks[0], f"card-{problem}", "exec")

    def test_mutable_sum(self):
        cls = solution("307", "MutableSum")
        demo = cls([2, -1, 4])
        self.assertEqual(demo.sum_range(0, 2), 5)
        demo.update(1, 3)
        self.assertEqual(demo.sum_range(0, 2), 9)
        rng = random.Random(307)
        for n in range(1, 26):
            values = [rng.randrange(-20, 21) for _ in range(n)]
            obj = cls(values)
            for _ in range(180):
                if rng.randrange(2):
                    i = rng.randrange(n)
                    value = rng.randrange(-20, 21)
                    obj.update(i, value)
                    values[i] = value
                else:
                    left = rng.randrange(n)
                    right = rng.randrange(left, n)
                    self.assertEqual(obj.sum_range(left, right), sum(values[left:right + 1]))
            obj.update(n - 1, values[-1])
            self.assertEqual(obj.sum_range(0, n - 1), sum(values))

    def test_static_minimum(self):
        cls = solution("cses:1647", "StaticMinimum")
        self.assertEqual(cls([7, 2, 5, 1]).query(1, 3), 1)
        rng = random.Random(1647)
        for n in range(1, 65):
            values = [rng.randrange(-10, 11) for _ in range(n)]
            obj = cls(values)
            for left in range(n):
                for right in range(left, n):
                    self.assertEqual(obj.query(left, right), min(values[left:right + 1]))

    def test_dynamic_minimum(self):
        cls = solution("cses:1649", "DynamicMinimum")
        demo = cls([6, 3, 8])
        demo.update(1, 9)
        self.assertEqual(demo.query(0, 1), 6)
        rng = random.Random(16490)
        for n in range(1, 40):
            values = [rng.randrange(-20, 21) for _ in range(n)]
            obj = cls(values)
            for _ in range(150):
                if rng.randrange(2):
                    i, value = rng.randrange(n), rng.randrange(-20, 21)
                    values[i] = value
                    obj.update(i, value)
                else:
                    left = rng.randrange(n)
                    right = rng.randrange(left, n)
                    self.assertEqual(obj.query(left, right), min(values[left:right + 1]))

    def test_range_add_point(self):
        cls = solution("cses:1651", "RangeAddPoint")
        demo = cls([4, 1, 3])
        demo.add_range(0, 1, 2)
        self.assertEqual(demo.get(1), 3)
        rng = random.Random(1651)
        for n in range(1, 32):
            values = [rng.randrange(-9, 10) for _ in range(n)]
            obj = cls(values)
            for _ in range(120):
                left = rng.randrange(n)
                right = rng.randrange(left, n)
                delta = rng.randrange(-9, 10)
                obj.add_range(left, right, delta)
                for i in range(left, right + 1):
                    values[i] += delta
                for i in range(n):
                    self.assertEqual(obj.get(i), values[i])

    def test_teams(self):
        solve = solution("1395", "count_teams")
        self.assertEqual(solve([2, 5, 3, 4]), 1)
        for n in range(7):
            for nums in itertools.product(range(3), repeat=n):
                expected = sum(
                    (nums[i] < nums[j] < nums[k]) or (nums[i] > nums[j] > nums[k])
                    for i, j, k in itertools.combinations(range(n), 3)
                )
                self.assertEqual(solve(nums), expected, nums)

    def test_smaller_after(self):
        solve = solution("315", "smaller_after")
        self.assertEqual(solve([4, 1, 4, 2]), [2, 0, 1, 0])
        for n in range(8):
            for nums in itertools.product((-2, 0, 3), repeat=n):
                expected = [sum(x < nums[i] for x in nums[i + 1:]) for i in range(n)]
                self.assertEqual(solve(nums), expected, nums)

    def test_insertion_cost(self):
        solve = solution("1649", "insertion_cost")
        self.assertEqual(solve([1, 5, 6, 2]), 1)
        for n in range(8):
            for nums in itertools.product((-1, 0, 2), repeat=n):
                expected = sum(
                    min(sum(x < v for x in nums[:i]), sum(x > v for x in nums[:i]))
                    for i, v in enumerate(nums)
                )
                self.assertEqual(solve(nums), expected % 1_000_000_007, nums)
        # A long repeating pattern crosses the modulus while keeping the oracle linear.
        n = 150_001
        pattern = [0, 2, 1] * (n // 3) + [0]
        cycles = n // 3
        expected = cycles * (cycles + 1) // 2
        self.assertEqual(solve(pattern), expected % 1_000_000_007)

    def test_range_sum_count(self):
        solve = solution("327", "count_range_sum")
        self.assertEqual(solve([-2, 5, -1], -2, 2), 3)
        for n in range(6):
            for nums in itertools.product((-2, 0, 3), repeat=n):
                sums = [sum(nums[i:j]) for i in range(n) for j in range(i + 1, n + 1)]
                for lower, upper in ((-3, -1), (0, 0), (-2, 2), (1, 5), (-20, 20)):
                    self.assertEqual(solve(nums, lower, upper),
                                     sum(lower <= x <= upper for x in sums))
        self.assertEqual(solve([0] * 100, 0, 0), 5050)

    def test_constrained_lis(self):
        solve = solution("2407", "constrained_lis")
        self.assertEqual(solve([1, 5, 3, 4], 2), 3)
        for n in range(7):
            for nums in itertools.product((-2, 0, 2), repeat=n):
                for k in (0, 1, 2, 5):
                    lengths = []
                    for i, value in enumerate(nums):
                        best = max((lengths[j] for j in range(i)
                                    if 0 < value - nums[j] <= k), default=0)
                        lengths.append(best + 1)
                    self.assertEqual(solve(nums, k), max(lengths, default=0), (nums, k))

    def test_falling_squares(self):
        solve = solution("699", "falling_squares")
        self.assertEqual(solve([(1, 2), (2, 3), (6, 1)]), [2, 5, 5])
        self.assertEqual(solve([]), [])
        self.assertEqual(solve([(0, 2), (2, 2), (0, 2)]), [2, 2, 4])
        rng = random.Random(699)
        for _ in range(1500):
            positions = [(rng.randrange(-5, 10), rng.randrange(1, 6))
                         for _ in range(rng.randrange(1, 11))]
            previous, expected, high = [], [], 0
            for left, side in positions:
                right = left + side
                base = max((height for a, b, height in previous
                            if left < b and a < right), default=0)
                top = base + side
                previous.append((left, right, top))
                high = max(high, top)
                expected.append(high)
            self.assertEqual(solve(positions), expected, positions)

    def test_good_triplets(self):
        solve = solution("2179", "good_triplets")
        self.assertEqual(solve([0, 1, 2, 3], [0, 2, 1, 3]), 2)
        for n in range(7):
            first = list(range(n))
            for second in itertools.permutations(first):
                positions = {v: i for i, v in enumerate(second)}
                expected = sum(positions[first[i]] < positions[first[j]] < positions[first[k]]
                               for i, j, k in itertools.combinations(range(n), 3))
                self.assertEqual(solve(first, second), expected, second)
        rng = random.Random(2179)
        for _ in range(300):
            n = rng.randrange(3, 12)
            first, second = list(range(n)), list(range(n))
            rng.shuffle(first)
            rng.shuffle(second)
            positions = {v: i for i, v in enumerate(second)}
            expected = sum(positions[first[i]] < positions[first[j]] < positions[first[k]]
                           for i, j, k in itertools.combinations(range(n), 3))
            self.assertEqual(solve(first, second), expected)

    def test_rectangle_union(self):
        solve = solution("850", "rectangle_union_area")
        self.assertEqual(solve([[0, 0, 2, 2], [1, 1, 3, 3]]), 7)
        self.assertEqual(solve([]), 0)
        self.assertEqual(solve([[0, 0, 10**9, 10**9]]),
                         (10**18) % 1_000_000_007)
        rng = random.Random(850)
        cases = [
            [[0, 0, 2, 2], [0, 0, 2, 2]],
            [[0, 0, 4, 4], [1, 1, 2, 2]],
            [[0, 0, 1, 1], [1, 0, 2, 1]],
            [[0, 0, 3, 1], [0, 1, 3, 2], [1, 0, 2, 2]],
        ]
        for _ in range(1500):
            rects = []
            for _ in range(rng.randrange(1, 9)):
                x1, x2 = sorted(rng.sample(range(-4, 6), 2))
                y1, y2 = sorted(rng.sample(range(-4, 6), 2))
                rects.append([x1, y1, x2, y2])
            cases.append(rects)
        for rects in cases:
            cells = set()
            for x1, y1, x2, y2 in rects:
                cells.update((x, y) for x in range(x1, x2) for y in range(y1, y2))
            self.assertEqual(solve(rects), len(cells), rects)


if __name__ == "__main__":
    unittest.main()
