import itertools
import random
import re
import unittest
from fractions import Fraction
from pathlib import Path


BUILD = Path(__file__).resolve().parents[2]
SOURCE = BUILD / "dsa" / "12-mono.cards.md"
MODULE = BUILD / "dsa" / "12-mono.md"
CARDS = dict(re.findall(
    r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)",
    SOURCE.read_text(encoding="utf-8"),
))
NAMES = {
    "496": "next_greater_queries",
    "739": "daily_temperatures",
    "503": "next_greater_circular",
    "901": "StockSpanner",
    "402": "remove_k_digits",
    "853": "car_fleets",
    "907": "sum_subarray_mins",
    "84": "largest_rectangle",
    "239": "sliding_window_max",
    "1438": "longest_bounded_range",
    "862": "shortest_subarray_at_least",
    "85": "maximal_rectangle",
}


def load_solutions():
    solutions = {}
    for problem, name in NAMES.items():
        blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
        if len(blocks) != 1:
            raise AssertionError(f"{problem}: expected exactly one Python block")
        namespace = {}
        exec(compile(blocks[0], f"card-{problem}", "exec"), namespace)
        solutions[problem] = namespace[name]
    return solutions


SOLUTIONS = load_solutions()


def tuples(values, max_length):
    for length in range(max_length + 1):
        yield from itertools.product(values, repeat=length)


def fleet_simulation(target, positions, speeds):
    """Advance exact rational positions to the next collision or arrival."""
    groups = sorted(
        [[Fraction(position), Fraction(speed)] for position, speed in zip(positions, speeds)]
    )
    arrived = 0
    while groups:
        events = [(Fraction(target) - position) / speed for position, speed in groups]
        for rear, front in zip(groups, groups[1:]):
            if rear[1] > front[1]:
                events.append((front[0] - rear[0]) / (rear[1] - front[1]))
        elapsed = min(events)
        for group in groups:
            group[0] += group[1] * elapsed
        merged = []
        for position, speed in groups:
            if merged and merged[-1][0] == position:
                # The leading group controls the speed after a collision.
                merged[-1][1] = speed
            else:
                merged.append([position, speed])
        groups = [group for group in merged if group[0] < target]
        arrived += len(merged) - len(groups)
    return arrived


def rectangle_oracle(matrix):
    if not matrix or not matrix[0]:
        return 0
    rows, cols = len(matrix), len(matrix[0])
    best = 0
    for top in range(rows):
        for bottom in range(top, rows):
            for left in range(cols):
                for right in range(left, cols):
                    if all(matrix[r][c] == "1"
                           for r in range(top, bottom + 1)
                           for c in range(left, right + 1)):
                        best = max(best, (bottom - top + 1) * (right - left + 1))
    return best


class TestMonoCards(unittest.TestCase):
    def test_coverage_and_examples(self):
        practice = MODULE.read_text(encoding="utf-8").split("=== practice\n", 1)[1]
        ids = re.findall(r"(?m)^- (\S+) (?:core|derive|stretch|mixed)$", practice)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(CARDS), len(ids))
        self.assertEqual(set(CARDS), set(ids))
        self.assertEqual(set(CARDS), set(NAMES))
        self.assertEqual(SOLUTIONS["496"]([1, 4], [4, 1, 3, 2]), [3, -1])
        self.assertEqual(SOLUTIONS["739"]([70, 72, 71, 73]), [1, 2, 1, 0])
        self.assertEqual(SOLUTIONS["503"]([2, 1, 2, 4]), [4, 2, 4, -1])
        stream = SOLUTIONS["901"]()
        self.assertEqual([stream.next(x) for x in [3, 1, 2, 2]], [1, 1, 2, 3])
        self.assertEqual(SOLUTIONS["402"]("1432", 2), "12")
        self.assertEqual(SOLUTIONS["853"](12, [10, 8, 0], [2, 4, 1]), 2)
        self.assertEqual(SOLUTIONS["907"]([3, 1, 2]), 9)
        self.assertEqual(SOLUTIONS["84"]([2, 1, 2]), 3)
        self.assertEqual(SOLUTIONS["239"]([1, 3, 2, 5], 2), [3, 3, 5])
        self.assertEqual(SOLUTIONS["1438"]([8, 2, 4, 7], 4), 2)
        self.assertEqual(SOLUTIONS["862"]([2, -1, 2], 3), 3)
        self.assertEqual(SOLUTIONS["85"]([["1", "0", "1"], ["1", "1", "1"]]), 3)

    def test_next_greater_queries(self):
        solve = SOLUTIONS["496"]
        for n in range(6):
            for nums in itertools.permutations(range(5), n):
                queries = list(reversed(nums))
                expected = []
                for value in queries:
                    suffix = nums[nums.index(value) + 1:]
                    expected.append(next((x for x in suffix if x > value), -1))
                self.assertEqual(solve(queries, nums), expected, nums)

    def test_temperatures(self):
        solve = SOLUTIONS["739"]
        for nums in tuples(range(3), 7):
            expected = []
            for i, value in enumerate(nums):
                expected.append(next((j - i for j in range(i + 1, len(nums))
                                      if nums[j] > value), 0))
            self.assertEqual(solve(nums), expected, nums)

    def test_circular_greater(self):
        solve = SOLUTIONS["503"]
        for nums in tuples(range(-1, 2), 7):
            n = len(nums)
            expected = []
            for i, value in enumerate(nums):
                expected.append(next((nums[(i + offset) % n] for offset in range(1, n)
                                      if nums[(i + offset) % n] > value), -1))
            self.assertEqual(solve(nums), expected, nums)

    def test_stock_spans(self):
        for prices in tuples(range(3), 7):
            stream = SOLUTIONS["901"]()
            for i, price in enumerate(prices):
                start = i
                while start > 0 and prices[start - 1] <= price:
                    start -= 1
                self.assertEqual(stream.next(price), i - start + 1, prices)

    def test_digit_removal(self):
        solve = SOLUTIONS["402"]
        for n in range(1, 7):
            for digits in itertools.product("012", repeat=n):
                num = "".join(digits)
                for k in range(n + 1):
                    candidates = [
                        "".join(num[i] for i in kept)
                        for kept in itertools.combinations(range(n), n - k)
                    ]
                    expected = min(candidates).lstrip("0") or "0"
                    self.assertEqual(solve(num, k), expected, (num, k))

    def test_fleets_event_simulation(self):
        solve = SOLUTIONS["853"]
        rng = random.Random(853)
        for _ in range(1500):
            target = rng.randint(1, 12)
            positions = rng.sample(range(target), rng.randint(0, min(6, target)))
            speeds = [rng.randint(1, 7) for _ in positions]
            self.assertEqual(solve(target, positions, speeds),
                             fleet_simulation(target, positions, speeds),
                             (target, positions, speeds))
        # Distinct exact ratios that are indistinguishable as binary floats.
        big = 10**20
        self.assertEqual(solve(big + 1, [1, 0], [big, big]), 2)
        self.assertEqual(solve(12, [10, 8], [2, 4]), 1)

    def test_subarray_minimum_sum(self):
        solve = SOLUTIONS["907"]
        for nums in tuples(range(4), 6):
            expected = sum(min(nums[i:j]) for i in range(len(nums))
                           for j in range(i + 1, len(nums) + 1))
            self.assertEqual(solve(nums), expected % 1_000_000_007, nums)
        self.assertEqual(solve([10**9] * 100), (5050 * 10**9) % 1_000_000_007)

    def test_histogram(self):
        solve = SOLUTIONS["84"]
        for heights in tuples(range(4), 7):
            expected = max((min(heights[i:j]) * (j - i)
                            for i in range(len(heights))
                            for j in range(i + 1, len(heights) + 1)), default=0)
            self.assertEqual(solve(heights), expected, heights)

    def test_sliding_maximum(self):
        solve = SOLUTIONS["239"]
        for nums in tuples(range(-1, 2), 7):
            for k in range(1, len(nums) + 1):
                expected = [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]
                self.assertEqual(solve(nums, k), expected, (nums, k))
        for nums, k in [([], 1), ([1], 0), ([1], 2)]:
            with self.assertRaises(ValueError):
                solve(nums, k)

    def test_bounded_range(self):
        solve = SOLUTIONS["1438"]
        for nums in tuples(range(-1, 2), 7):
            for limit in range(3):
                expected = max((j - i for i in range(len(nums))
                                for j in range(i + 1, len(nums) + 1)
                                if max(nums[i:j]) - min(nums[i:j]) <= limit), default=0)
                self.assertEqual(solve(nums, limit), expected, (nums, limit))
        with self.assertRaises(ValueError):
            solve([1], -1)

    def test_shortest_subarray(self):
        solve = SOLUTIONS["862"]
        for nums in tuples(range(-2, 3), 6):
            for k in range(1, 5):
                expected = min((j - i for i in range(len(nums))
                                for j in range(i + 1, len(nums) + 1)
                                if sum(nums[i:j]) >= k), default=-1)
                self.assertEqual(solve(nums, k), expected, (nums, k))
        # Even outside the usual positive-target domain the interval is nonempty.
        self.assertEqual(solve([0], 0), 1)
        self.assertEqual(solve([], 0), -1)

    def test_binary_rectangles(self):
        solve = SOLUTIONS["85"]
        self.assertEqual(solve([]), 0)
        self.assertEqual(solve([[]]), 0)
        for rows, cols in [(1, 5), (2, 4), (3, 4), (4, 3)]:
            for cells in itertools.product("01", repeat=rows * cols):
                matrix = [list(cells[i * cols:(i + 1) * cols]) for i in range(rows)]
                original = [row[:] for row in matrix]
                self.assertEqual(solve(matrix), rectangle_oracle(matrix), matrix)
                self.assertEqual(matrix, original)


if __name__ == "__main__":
    unittest.main()
