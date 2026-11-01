"""Execute the Markdown's actual Python blocks against independent small-input models."""

import itertools
import math
import random
import re
import unittest
from pathlib import Path


BUILD = Path(__file__).resolve().parents[2]
CARD_FILE = BUILD / "dsa" / "05-arrays.cards.md"
MODULE_FILE = BUILD / "dsa" / "05-arrays.md"
NAMES = {
    "566": "reshape",
    "448": "missing_numbers",
    "645": "set_mismatch",
    "31": "next_permutation",
    "54": "spiral_order",
    "498": "diagonal_order",
    "48": "rotate_clockwise",
    "289": "life_step",
    "73": "set_zeroes",
    "41": "first_missing_positive",
    "238": "product_except_self",
    "1980": "missing_binary_string",
}


def load_cards():
    text = CARD_FILE.read_text(encoding="utf-8")
    chunks = re.split(r"(?m)^=== card \| ([^\n]+)\n", text)
    if chunks[0].strip() or len(chunks) % 2 != 1:
        raise AssertionError("unexpected card file framing")
    cards = {}
    for pid, body in zip(chunks[1::2], chunks[2::2]):
        if pid in cards:
            raise AssertionError(f"duplicate card {pid}")
        blocks = re.findall(r"```python\n(.*?)\n```", body, re.DOTALL)
        if len(blocks) != 1:
            raise AssertionError(f"card {pid}: expected one Python block, got {len(blocks)}")
        namespace = {}
        exec(compile(blocks[0], f"{CARD_FILE.name}:{pid}", "exec"), namespace)
        cards[pid] = namespace[NAMES[pid]]
    practice = MODULE_FILE.read_text(encoding="utf-8").split("=== practice\n", 1)[1]
    ids = re.findall(r"(?m)^- (\d+) (?:core|derive|stretch|mixed)$", practice)
    if len(ids) != len(set(ids)) or set(ids) != set(cards) or set(cards) != set(NAMES):
        raise AssertionError(f"practice/code coverage mismatch: {ids}, {list(cards)}, {list(NAMES)}")
    return cards


CARDS = load_cards()
COUNTS = {}


def report(pid, count):
    COUNTS[pid] = count
    print(f"card {pid}: {count:,} oracle cases", flush=True)


class CardOracleTests(unittest.TestCase):
    def test_traced_examples(self):
        self.assertEqual(CARDS["566"]([[1, 2, 3], [4, 5, 6]], 3, 2), [[1, 2], [3, 4], [5, 6]])
        self.assertEqual(CARDS["448"]([2, 2, 4, 1]), [3])
        self.assertEqual(CARDS["645"]([1, 3, 3, 4]), [3, 2])
        a = [1, 3, 5, 4, 2]
        CARDS["31"](a)
        self.assertEqual(a, [1, 4, 2, 3, 5])
        self.assertEqual(CARDS["54"]([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                         [1, 2, 3, 6, 9, 8, 7, 4, 5])
        self.assertEqual(CARDS["498"]([[1, 2, 3], [4, 5, 6]]), [1, 2, 4, 5, 3, 6])
        matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        CARDS["48"](matrix)
        self.assertEqual(matrix, [[7, 4, 1], [8, 5, 2], [9, 6, 3]])
        board = [[0, 0, 0], [1, 1, 1], [0, 0, 0]]
        CARDS["289"](board)
        self.assertEqual(board, [[0, 1, 0], [0, 1, 0], [0, 1, 0]])
        matrix = [[1, 2, 3], [4, 0, 6], [0, 8, 9]]
        CARDS["73"](matrix)
        self.assertEqual(matrix, [[0, 0, 3], [0, 0, 0], [0, 0, 0]])
        self.assertEqual(CARDS["41"]([3, 4, -1, 1]), 2)
        self.assertEqual(CARDS["238"]([2, 0, 4]), [0, 8, 0])
        self.assertEqual(CARDS["1980"](["010", "111", "001"]), "100")

    def test_566_reshape(self):
        f = CARDS["566"]
        count = 0
        for m in range(1, 6):
            for n in range(1, 6):
                grid = [[r * n + c for c in range(n)] for r in range(m)]
                flat = [value for row in grid for value in row]
                for rows in range(1, 7):
                    for cols in range(1, 7):
                        before = [row[:] for row in grid]
                        got = f(grid, rows, cols)
                        if rows * cols == m * n:
                            expected = [flat[i:i + cols] for i in range(0, len(flat), cols)]
                            self.assertEqual(got, expected, (m, n, rows, cols))
                            self.assertIsNot(got, grid)
                            self.assertEqual(len({id(row) for row in got}), rows)
                        else:
                            self.assertIs(got, grid)
                        self.assertEqual(grid, before)
                        count += 1
        report("566", count)

    def test_448_missing(self):
        f = CARDS["448"]
        count = 0
        for n in range(6):
            for values in itertools.product(range(1, n + 1), repeat=n):
                a = list(values)
                expected = sorted(set(range(1, n + 1)) - set(values))
                self.assertEqual(f(a), expected, values)
                self.assertEqual(a, list(values))
                count += 1
        report("448", count)

    def test_645_mismatch(self):
        f = CARDS["645"]
        count = 0
        rng = random.Random(645)
        for n in range(2, 11):
            for missing in range(1, n + 1):
                for duplicate in range(1, n + 1):
                    if duplicate == missing:
                        continue
                    for _ in range(5):
                        a = list(range(1, n + 1))
                        a[missing - 1] = duplicate
                        rng.shuffle(a)
                        before = a[:]
                        self.assertEqual(f(a), [duplicate, missing], before)
                        self.assertEqual(a, before)
                        count += 1
        report("645", count)

    def test_31_next_permutation(self):
        f = CARDS["31"]
        count = 0
        ordering_cache = {}
        for n in range(7):
            for values in itertools.product(range(3), repeat=n):
                key = tuple(sorted(values))
                if key not in ordering_cache:
                    ordering_cache[key] = sorted(set(itertools.permutations(key)))
                order = ordering_cache[key]
                expected = order[(order.index(values) + 1) % len(order)]
                a = list(values)
                self.assertIsNone(f(a))
                self.assertEqual(tuple(a), expected, values)
                count += 1
        report("31", count)

    def test_54_spiral(self):
        f = CARDS["54"]
        count = 0
        for m in range(9):
            for n in range(9):
                grid = [[r * n + c for c in range(n)] for r in range(m)]
                before = [row[:] for row in grid]
                visited = set()
                expected = []
                r = c = direction = 0
                dirs = ((0, 1), (1, 0), (0, -1), (-1, 0))
                for _ in range(m * n):
                    expected.append(grid[r][c])
                    visited.add((r, c))
                    dr, dc = dirs[direction]
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < m and 0 <= nc < n) or (nr, nc) in visited:
                        direction = (direction + 1) % 4
                        dr, dc = dirs[direction]
                        nr, nc = r + dr, c + dc
                    r, c = nr, nc
                self.assertEqual(f(grid), expected, (m, n))
                self.assertEqual(grid, before)
                count += 1
        report("54", count)

    def test_498_diagonals(self):
        f = CARDS["498"]
        count = 0
        for m in range(10):
            for n in range(10):
                grid = [[r * n + c for c in range(n)] for r in range(m)]
                coords = [(r, c) for r in range(m) for c in range(n)]
                coords.sort(key=lambda pos: (sum(pos), pos[0] if sum(pos) % 2 else -pos[0]))
                expected = [grid[r][c] for r, c in coords]
                before = [row[:] for row in grid]
                self.assertEqual(f(grid), expected, (m, n))
                self.assertEqual(grid, before)
                count += 1
        report("498", count)

    def test_48_rotate(self):
        f = CARDS["48"]
        count = 0
        rng = random.Random(48)
        for n in range(10):
            for _ in range(20):
                grid = [[rng.randrange(-5, 6) for _ in range(n)] for _ in range(n)]
                old = [row[:] for row in grid]
                row_ids = [id(row) for row in grid]
                expected = [[old[n - 1 - c][r] for c in range(n)] for r in range(n)]
                self.assertIsNone(f(grid))
                self.assertEqual(grid, expected, old)
                self.assertEqual([id(row) for row in grid], row_ids)
                count += 1
        report("48", count)

    def test_289_life(self):
        f = CARDS["289"]
        count = 0
        rng = random.Random(289)

        def check(board):
            old = [row[:] for row in board]
            m = len(old)
            n = len(old[0]) if m else 0
            expected = []
            for r in range(m):
                row = []
                for c in range(n):
                    neighbours = sum(
                        old[rr][cc]
                        for rr in range(m)
                        for cc in range(n)
                        if (rr != r or cc != c) and abs(rr - r) <= 1 and abs(cc - c) <= 1
                    )
                    row.append(int(neighbours == 3 or (old[r][c] == 1 and neighbours == 2)))
                expected.append(row)
            self.assertIsNone(f(board))
            self.assertEqual(board, expected, old)

        for m in range(4):
            for n in range(4):
                for bits in itertools.product((0, 1), repeat=m * n):
                    check([list(bits[r * n:(r + 1) * n]) for r in range(m)])
                    count += 1
        for _ in range(500):
            m, n = rng.randrange(1, 9), rng.randrange(1, 9)
            check([[rng.randrange(2) for _ in range(n)] for _ in range(m)])
            count += 1
        report("289", count)

    def test_73_zeroes(self):
        f = CARDS["73"]
        count = 0
        rng = random.Random(73)

        def check(matrix):
            old = [row[:] for row in matrix]
            m = len(old)
            n = len(old[0]) if m else 0
            zeros = [(r, c) for r in range(m) for c in range(n) if old[r][c] == 0]
            expected = [
                [0 if any(zr == r or zc == c for zr, zc in zeros) else old[r][c]
                 for c in range(n)]
                for r in range(m)
            ]
            self.assertIsNone(f(matrix))
            self.assertEqual(matrix, expected, old)

        for m in range(4):
            for n in range(4):
                for bits in itertools.product((0, 1), repeat=m * n):
                    check([list(bits[r * n:(r + 1) * n]) for r in range(m)])
                    count += 1
        for _ in range(500):
            m, n = rng.randrange(1, 9), rng.randrange(1, 9)
            check([[rng.randrange(-2, 3) for _ in range(n)] for _ in range(m)])
            count += 1
        report("73", count)

    def test_41_missing_positive(self):
        f = CARDS["41"]
        count = 0
        rng = random.Random(41)

        def check(values):
            a = list(values)
            expected = 1
            while expected in values:
                expected += 1
            self.assertEqual(f(a), expected, values)
            self.assertEqual(sorted(a), sorted(values))

        for n in range(6):
            for values in itertools.product(range(-1, n + 2), repeat=n):
                check(values)
                count += 1
        for _ in range(5000):
            values = [rng.randrange(-30, 31) for _ in range(rng.randrange(20))]
            check(values)
            count += 1
        report("41", count)

    def test_238_product(self):
        f = CARDS["238"]
        count = 0
        for n in range(7):
            for values in itertools.product(range(-2, 3), repeat=n):
                a = list(values)
                expected = [math.prod(values[:i] + values[i + 1:]) for i in range(n)]
                self.assertEqual(f(a), expected, values)
                self.assertEqual(a, list(values))
                count += 1
        report("238", count)

    def test_1980_binary(self):
        f = CARDS["1980"]
        count = 0
        rng = random.Random(1980)

        def check(strings):
            answer = f(strings)
            self.assertEqual(len(answer), len(strings), strings)
            self.assertTrue(set(answer) <= {"0", "1"}, strings)
            self.assertNotIn(answer, strings)

        check([])
        count += 1
        for n in range(1, 4):
            universe = ["".join(bits) for bits in itertools.product("01", repeat=n)]
            for strings in itertools.permutations(universe, n):
                check(strings)
                count += 1
        for _ in range(2000):
            n = rng.randrange(1, 9)
            universe = [f"{i:0{n}b}" for i in range(2**n)]
            check(rng.sample(universe, n))
            count += 1
        report("1980", count)


if __name__ == "__main__":
    unittest.main(verbosity=2)
