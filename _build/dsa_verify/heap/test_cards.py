import itertools
import random
import re
import unittest
from collections import Counter
from pathlib import Path


BUILD = Path(__file__).resolve().parents[2]
SOURCE = BUILD / "dsa" / "14-heap.cards.md"
MODULE = BUILD / "dsa" / "14-heap.md"
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


def median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


class TestHeapCards(unittest.TestCase):
    def test_coverage_and_all_python_blocks(self):
        practice = MODULE.read_text().split("=== practice\n", 1)[1]
        ids = re.findall(r"(?m)^- (\S+) (?:core|derive|stretch|mixed)$", practice)
        self.assertEqual(len(ids), len(CARDS))
        self.assertEqual(set(ids), set(CARDS))
        for problem, card in CARDS.items():
            blocks = re.findall(r"```python\n(.*?)\n```", card, re.S)
            self.assertEqual(len(blocks), 1, problem)
            compile(blocks[0], f"card-{problem}", "exec")

    def test_published_examples(self):
        self.assertEqual(solution("1046", "last_stone_weight")([2, 7, 4, 1, 8, 1]), 1)
        stream = solution("703", "KthLargest")(2, [4, 2])
        self.assertEqual([stream.add(5), stream.add(4)], [4, 4])
        self.assertEqual(solution("hr:qheap1", "heap_queries")(
            [(1, 5), (1, 2), (1, 7), (2, 2), (2, 7), (3,)]), [5])
        self.assertEqual({tuple(point) for point in solution("973", "k_closest")(
            [[1, 1], [3, 0], [-1, 0]], 2)}, {(1, 1), (-1, 0)})
        self.assertEqual(solution("215", "kth_largest")([3, 1, 5, 3], 2), 3)
        self.assertEqual(solution("373", "k_smallest_pairs")([1, 3], [2, 4], 3),
                         [[1, 2], [1, 4], [3, 2]])
        self.assertEqual(solution("1834", "cpu_order")(
            [[1, 2], [2, 4], [3, 2], [4, 1]]), [0, 2, 3, 1])
        self.assertEqual(solution("1642", "furthest_building")([1, 5, 6, 10], 4, 1), 2)
        stream = solution("295", "MedianFinder")()
        for value in (5, 1, 3):
            stream.add(value)
        self.assertEqual(stream.median(), 3)
        stream.add(3)
        self.assertEqual(stream.median(), 3)
        self.assertEqual(solution("502", "maximize_capital")(2, 0, [1, 2, 3], [0, 1, 1]), 4)
        self.assertEqual(solution("632", "smallest_range")([[1, 5], [2, 6], [3, 7]]), [1, 3])
        self.assertEqual(solution("480", "median_sliding_window")([1, 3, -1, -3, 5], 3),
                         [1, -1, -1])

    def test_stones_against_sort_simulation(self):
        solve = solution("1046", "last_stone_weight")
        for length in range(7):
            for stones in itertools.product(range(1, 5), repeat=length):
                remaining = list(stones)
                while len(remaining) > 1:
                    remaining.sort()
                    larger = remaining.pop()
                    smaller = remaining.pop()
                    if larger != smaller:
                        remaining.append(larger - smaller)
                self.assertEqual(solve(stones), remaining[0] if remaining else 0)

    def test_stream_rank_against_sort(self):
        cls = solution("703", "KthLargest")
        rng = random.Random(703)
        for k in range(1, 9):
            for _ in range(150):
                initial = [rng.randrange(-5, 6) for _ in range(rng.randrange(k - 1, k + 5))]
                stream = cls(k, initial)
                seen = initial[:]
                for _ in range(20):
                    value = rng.randrange(-5, 6)
                    seen.append(value)
                    self.assertEqual(stream.add(value), sorted(seen, reverse=True)[k - 1])
                    self.assertLessEqual(len(stream.heap), k)
        stream = cls(3, [])
        with self.assertRaises(ValueError):
            stream.add(7)
        with self.assertRaises(ValueError):
            stream.add(9)
        self.assertEqual(stream.add(8), 7)
        with self.assertRaises(ValueError):
            cls(0, [])

    def test_queries_against_multiset(self):
        solve = solution("hr:qheap1", "heap_queries")
        rng = random.Random(141)
        for _ in range(350):
            values, queries, expected = [], [], []
            for _ in range(100):
                kind = rng.choice((1, 1, 2, 3)) if values else 1
                if kind == 1:
                    value = rng.randrange(-5, 6)
                    values.append(value)
                    queries.append((1, value))
                elif kind == 2:
                    value = rng.choice(values)
                    values.remove(value)
                    queries.append((2, value))
                else:
                    queries.append((3,))
                    expected.append(min(values))
            self.assertEqual(solve(queries), expected)
        self.assertEqual(solve([(1, 2), (2, 2), (1, 2), (3,)]), [2])
        with self.assertRaises(ValueError):
            solve([(3,)])

    def test_closest_against_full_sort(self):
        solve = solution("973", "k_closest")
        rng = random.Random(973)
        for n in range(11):
            for _ in range(100):
                points = [[rng.randrange(-3, 4), rng.randrange(-3, 4)] for _ in range(n)]
                available = Counter(map(tuple, points))
                for k in range(n + 1):
                    result = solve(points, k)
                    self.assertEqual(len(result), k)
                    self.assertFalse(Counter(map(tuple, result)) - available)
                    self.assertEqual(
                        sorted(x * x + y * y for x, y in result),
                        sorted(x * x + y * y for x, y in points)[:k],
                    )
        with self.assertRaises(ValueError):
            solve([], 1)

    def test_kth_against_sort(self):
        solve = solution("215", "kth_largest")
        for n in range(1, 7):
            for nums in itertools.product(range(-1, 2), repeat=n):
                for k in range(1, n + 1):
                    self.assertEqual(solve(nums, k), sorted(nums, reverse=True)[k - 1])
        with self.assertRaises(ValueError):
            solve([], 1)
        with self.assertRaises(ValueError):
            solve([1], 0)

    def test_pairs_against_cartesian_product(self):
        solve = solution("373", "k_smallest_pairs")
        rng = random.Random(373)
        for _ in range(1800):
            first = sorted(rng.randrange(-3, 4) for _ in range(rng.randrange(7)))
            second = sorted(rng.randrange(-3, 4) for _ in range(rng.randrange(7)))
            k = rng.randrange(15)
            all_pairs = list(itertools.product(first, second))
            result = solve(first, second, k)
            self.assertEqual(len(result), min(k, len(all_pairs)))
            self.assertFalse(Counter(map(tuple, result)) - Counter(all_pairs))
            self.assertEqual([sum(pair) for pair in result],
                             sorted(map(sum, all_pairs))[:k])

    def test_cpu_against_scanning_simulation(self):
        solve = solution("1834", "cpu_order")
        rng = random.Random(1834)
        for _ in range(2000):
            tasks = [[rng.randrange(12), rng.randrange(1, 8)]
                     for _ in range(rng.randrange(13))]
            todo = set(range(len(tasks)))
            clock = 0
            expected = []
            while todo:
                available = [i for i in todo if tasks[i][0] <= clock]
                if not available:
                    clock = min(tasks[i][0] for i in todo)
                    continue
                chosen = min(available, key=lambda i: (tasks[i][1], i))
                todo.remove(chosen)
                expected.append(chosen)
                clock += tasks[chosen][1]
            self.assertEqual(solve(tasks), expected)

    def test_buildings_against_all_ladder_allocations(self):
        solve = solution("1642", "furthest_building")
        rng = random.Random(1642)
        for _ in range(2200):
            heights = [rng.randrange(8) for _ in range(rng.randrange(1, 9))]
            bricks, ladders = rng.randrange(10), rng.randrange(5)
            expected = 0
            climbs = []
            for i in range(len(heights) - 1):
                climbs.append(max(0, heights[i + 1] - heights[i]))
                possible = any(
                    sum(climb for j, climb in enumerate(climbs) if j not in chosen) <= bricks
                    for count in range(min(ladders, len(climbs)) + 1)
                    for chosen in itertools.combinations(range(len(climbs)), count)
                )
                if not possible:
                    break
                expected = i + 1
            self.assertEqual(solve(heights, bricks, ladders), expected)

    def test_stream_median_against_sort(self):
        cls = solution("295", "MedianFinder")
        rng = random.Random(295)
        for _ in range(400):
            stream = cls()
            with self.assertRaises(ValueError):
                stream.median()
            values = []
            for _ in range(50):
                value = rng.randrange(-10, 11)
                values.append(value)
                stream.add(value)
                self.assertEqual(stream.median(), median(values))

    def test_projects_against_feasible_sequence_enumeration(self):
        solve = solution("502", "maximize_capital")
        rng = random.Random(502)
        for _ in range(1400):
            n = rng.randrange(7)
            profits = [rng.randrange(5) for _ in range(n)]
            requirements = [rng.randrange(8) for _ in range(n)]
            capital, k = rng.randrange(5), rng.randrange(8)

            def search(current, remaining, choices):
                best = current
                if choices:
                    for i in remaining:
                        if requirements[i] <= current:
                            best = max(best, search(current + profits[i],
                                                    remaining - {i}, choices - 1))
                return best

            expected = search(capital, set(range(n)), k)
            self.assertEqual(solve(k, capital, profits, requirements), expected)

    def test_range_against_all_witness_combinations(self):
        solve = solution("632", "smallest_range")
        rng = random.Random(632)
        for _ in range(2200):
            lists = [sorted(rng.randrange(-5, 6) for _ in range(rng.randrange(1, 5)))
                     for _ in range(rng.randrange(1, 6))]
            ranges = [(max(values) - min(values), min(values), max(values))
                      for values in itertools.product(*lists)]
            _, left, right = min(ranges)
            self.assertEqual(solve(lists), [left, right])
        with self.assertRaises(ValueError):
            solve([])
        with self.assertRaises(ValueError):
            solve([[1], []])

    def test_sliding_median_against_window_sort(self):
        solve = solution("480", "median_sliding_window")
        for n in range(1, 8):
            for nums in itertools.product(range(-1, 2), repeat=n):
                for k in range(1, n + 1):
                    expected = [median(nums[i:i + k]) for i in range(n - k + 1)]
                    self.assertEqual(solve(nums, k), expected, (nums, k))
        rng = random.Random(480)
        examples = [list(range(150)), list(range(150, 0, -1)), [5] * 150,
                    [(-1) ** i * i for i in range(150)]]
        examples.extend([[rng.randrange(-20, 21) for _ in range(150)] for _ in range(30)])
        for nums in examples:
            for k in (1, 2, 3, 4, 17, 75, 149, 150):
                self.assertEqual(solve(nums, k),
                                 [median(nums[i:i + k]) for i in range(len(nums) - k + 1)])
        with self.assertRaises(ValueError):
            solve([1], 0)
        with self.assertRaises(ValueError):
            solve([], 1)


if __name__ == "__main__":
    unittest.main()
