"""Exercise the actual card blocks against independent small-input oracles."""
import ast
from collections import deque
from itertools import product
from pathlib import Path
import random
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
CARDS = ROOT / "dsa" / "10-prefix.cards.md"
MODULE = ROOT / "dsa" / "10-prefix.md"
EXPECTED = {"303", "724", "560", "974", "525", "304", "1109",
            "1749", "1074", "2536", "995", "689"}


def load_blocks():
    cards = {}
    source = CARDS.read_text(encoding="utf-8")
    for chunk in re.split(r"(?m)^=== card \| ", source)[1:]:
        pid, _, body = chunk.partition("\n")
        blocks = re.findall(r"```python\n(.*?)\n```", body, re.S)
        if pid in cards or len(blocks) != 1:
            raise AssertionError(f"card {pid}: duplicate or not exactly one Python block")
        namespace = {}
        exec(compile(ast.parse(blocks[0]), f"card-{pid}", "exec"), namespace)
        cards[pid] = namespace
    return cards


BLOCKS = load_blocks()


def slices(a):
    return [a[i:j] for i in range(len(a)) for j in range(i + 1, len(a) + 1)]


def rectangles(grid):
    m, n = len(grid), len(grid[0])
    for r1 in range(m):
        for r2 in range(r1, m):
            for c1 in range(n):
                for c2 in range(c1, n):
                    yield r1, c1, r2, c2


def rect_sum(grid, rect):
    r1, c1, r2, c2 = rect
    return sum(grid[r][c] for r in range(r1, r2 + 1)
               for c in range(c1, c2 + 1))


class CardsTest(unittest.TestCase):
    def test_coverage(self):
        practice = MODULE.read_text(encoding="utf-8").split("=== practice\n", 1)[1]
        ids = set(re.findall(r"(?m)^- ([0-9]+) (?:core|derive|stretch|mixed)\s*$", practice))
        self.assertEqual(ids, EXPECTED)
        self.assertEqual(set(BLOCKS), ids)

    def test_303(self):
        cls = BLOCKS["303"]["NumArray"]
        for n in range(1, 7):
            for a in product((-2, 0, 3), repeat=n):
                obj = cls(list(a))
                for left in range(n):
                    for right in range(left, n):
                        self.assertEqual(obj.sumRange(left, right), sum(a[left:right + 1]))
        self.assertEqual(cls([3, -2, 5]).sumRange(1, 2), 3)

    def test_724(self):
        solve = BLOCKS["724"]["Solution"]().pivotIndex
        for n in range(1, 8):
            for a in product((-1, 0, 1), repeat=n):
                expected = next((i for i in range(n) if sum(a[:i]) == sum(a[i + 1:])), -1)
                self.assertEqual(solve(list(a)), expected, a)
        self.assertEqual(solve([1, 7, 3, 6, 5, 6]), 3)

    def test_560(self):
        solve = BLOCKS["560"]["Solution"]().subarraySum
        for n in range(1, 7):
            for a in product((-1, 0, 1), repeat=n):
                sums = [sum(part) for part in slices(a)]
                for k in range(-3, 4):
                    self.assertEqual(solve(list(a), k), sums.count(k), (a, k))
        self.assertEqual(solve([1, -1, 1], 1), 3)

    def test_974(self):
        solve = BLOCKS["974"]["Solution"]().subarraysDivByK
        for n in range(1, 7):
            for a in product((-2, 0, 1), repeat=n):
                sums = [sum(part) for part in slices(a)]
                for k in range(1, 6):
                    self.assertEqual(solve(list(a), k), sum(s % k == 0 for s in sums), (a, k))
        self.assertEqual(solve([4, -1, 2], 3), 1)

    def test_525(self):
        solve = BLOCKS["525"]["Solution"]().findMaxLength
        for n in range(1, 11):
            for a in product((0, 1), repeat=n):
                expected = max((len(part) for part in slices(a)
                                if part.count(0) == part.count(1)), default=0)
                self.assertEqual(solve(list(a)), expected, a)
        self.assertEqual(solve([0, 1, 0, 0, 1, 1]), 6)

    def test_304(self):
        cls = BLOCKS["304"]["NumMatrix"]
        rng = random.Random(304)
        for m in range(1, 5):
            for n in range(1, 5):
                for _ in range(40):
                    grid = [[rng.randrange(-5, 6) for _ in range(n)] for _ in range(m)]
                    obj = cls(grid)
                    for rect in rectangles(grid):
                        self.assertEqual(obj.sumRegion(*rect), rect_sum(grid, rect), (grid, rect))
        self.assertEqual(cls([[1, 2], [3, 4]]).sumRegion(0, 1, 1, 1), 6)

    def test_1109(self):
        solve = BLOCKS["1109"]["Solution"]().corpFlightBookings
        rng = random.Random(1109)
        for n in range(1, 9):
            for _ in range(400):
                bookings = []
                expected = [0] * n
                for _ in range(rng.randrange(9)):
                    first = rng.randint(1, n)
                    last = rng.randint(first, n)
                    seats = rng.randint(1, 8)
                    bookings.append([first, last, seats])
                    for i in range(first - 1, last):
                        expected[i] += seats
                self.assertEqual(solve(bookings, n), expected, (bookings, n))
        self.assertEqual(solve([[1, 2, 5], [2, 4, 3]], 4), [5, 8, 3, 3])

    def test_1749(self):
        solve = BLOCKS["1749"]["Solution"]().maxAbsoluteSum
        for n in range(1, 8):
            for a in product((-2, 0, 3), repeat=n):
                expected = max([0] + [abs(sum(part)) for part in slices(a)])
                self.assertEqual(solve(list(a)), expected, a)
        self.assertEqual(solve([2, -5, 1]), 5)

    def test_1074(self):
        solve = BLOCKS["1074"]["Solution"]().numSubmatrixSumTarget
        rng = random.Random(1074)
        for m in range(1, 5):
            for n in range(1, 5):
                for _ in range(100):
                    grid = [[rng.randrange(-2, 3) for _ in range(n)] for _ in range(m)]
                    all_sums = [rect_sum(grid, rect) for rect in rectangles(grid)]
                    before = [row[:] for row in grid]
                    for target in range(-3, 4):
                        self.assertEqual(solve(grid, target), all_sums.count(target), (grid, target))
                    self.assertEqual(grid, before)
        self.assertEqual(solve([[1, -1], [0, 1]], 0), 3)

    def test_2536(self):
        solve = BLOCKS["2536"]["Solution"]().rangeAddQueries
        rng = random.Random(2536)
        for n in range(1, 7):
            for _ in range(400):
                queries = []
                expected = [[0] * n for _ in range(n)]
                for _ in range(rng.randrange(10)):
                    r1, c1 = rng.randrange(n), rng.randrange(n)
                    r2, c2 = rng.randrange(r1, n), rng.randrange(c1, n)
                    queries.append([r1, c1, r2, c2])
                    for r in range(r1, r2 + 1):
                        for c in range(c1, c2 + 1):
                            expected[r][c] += 1
                self.assertEqual(solve(n, queries), expected, (n, queries))
        self.assertEqual(solve(3, [[0, 1, 1, 2]]),
                         [[0, 1, 1], [0, 1, 1], [0, 0, 0]])

    def test_995(self):
        solve = BLOCKS["995"]["Solution"]().minKBitFlips
        for n in range(1, 10):
            for k in range(1, n + 1):
                # Reverse BFS gives the shortest distance to all ones for every reachable bit state.
                goal = (1 << n) - 1
                distance = {goal: 0}
                queue = deque([goal])
                masks = [((1 << k) - 1) << start for start in range(n - k + 1)]
                while queue:
                    state = queue.popleft()
                    for mask in masks:
                        neighbor = state ^ mask
                        if neighbor not in distance:
                            distance[neighbor] = distance[state] + 1
                            queue.append(neighbor)
                for state in range(1 << n):
                    nums = [(state >> i) & 1 for i in range(n)]
                    before = nums[:]
                    self.assertEqual(solve(nums, k), distance.get(state, -1), (nums, k))
                    self.assertEqual(nums, before)
        self.assertEqual(solve([0, 0, 0, 1, 0, 1, 1, 0], 3), 3)

    def test_689(self):
        solve = BLOCKS["689"]["Solution"]().maxSumOfThreeSubarrays
        rng = random.Random(689)
        for n in range(3, 13):
            for k in range(1, n // 3 + 1):
                for _ in range(300):
                    nums = [rng.randrange(-3, 4) for _ in range(n)]
                    candidates = []
                    for a in range(n - k + 1):
                        for b in range(a + k, n - k + 1):
                            for c in range(b + k, n - k + 1):
                                score = sum(nums[a:a + k] + nums[b:b + k] + nums[c:c + k])
                                candidates.append((-score, [a, b, c]))
                    expected = min(candidates)[1]
                    self.assertEqual(solve(nums, k), expected, (nums, k))
        self.assertEqual(solve([1, 2, 1, 2, 1, 2], 2), [0, 2, 4])


if __name__ == "__main__":
    unittest.main(verbosity=2)
