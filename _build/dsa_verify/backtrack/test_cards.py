import itertools
import random
import re
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "22-backtrack.cards.md"
NAMES = {
    "1863": "subset_xor_sum",
    "78": "subsets",
    "46": "permutations",
    "90": "subsets_with_duplicates",
    "39": "combination_sum",
    "22": "generate_parentheses",
    "131": "palindrome_partitions",
    "79": "word_exists",
    "698": "partition_equal_groups",
    "51": "n_queens",
    "2305": "distribute_cookies",
    "37": "solve_sudoku",
}


def load_solutions():
    text = SOURCE.read_text()
    chunks = re.split(r"(?m)^=== card \| (\S+)\s*\n", text)
    if chunks[0].strip():
        raise AssertionError("unexpected content before cards")
    solutions = {}
    for pid, card in zip(chunks[1::2], chunks[2::2]):
        if pid in solutions or pid not in NAMES:
            raise AssertionError(f"duplicate or unexpected card {pid}")
        blocks = re.findall(r"```python\n(.*?)\n```", card, re.S)
        if len(blocks) != 1 or "## Code\n" not in card:
            raise AssertionError(f"card {pid} must contain exactly one displayed Python block")
        namespace = {}
        exec(compile(blocks[0], f"card-{pid}", "exec"), namespace)
        solutions[pid] = namespace[NAMES[pid]]
    if solutions.keys() != NAMES.keys():
        raise AssertionError(f"missing cards: {NAMES.keys() - solutions.keys()}")
    return solutions


SOLVE = load_solutions()


def masks(values):
    return [tuple(values[i] for i in range(len(values)) if mask & (1 << i))
            for mask in range(1 << len(values))]


def assignment_totals(values, k):
    for assignment in itertools.product(range(k), repeat=len(values)):
        sums = [0] * k
        for value, group in zip(values, assignment):
            sums[group] += value
        yield sums


def word_oracle(board, word):
    if not word:
        return True
    cells = list(itertools.product(range(len(board)), range(len(board[0])))) if board else []
    for path in itertools.product(cells, repeat=len(word)):
        if len(set(path)) != len(path):
            continue
        if any(abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1
               for a, b in zip(path, path[1:])):
            continue
        if "".join(board[r][c] for r, c in path) == word:
            return True
    return False


def sudoku_oracle(board):
    grid = [row[:] for row in board]
    digits = "123456789"

    def valid(r, c, value):
        return (value not in grid[r] and
                all(grid[i][c] != value for i in range(9)) and
                all(grid[i][j] != value
                    for i in range(r // 3 * 3, r // 3 * 3 + 3)
                    for j in range(c // 3 * 3, c // 3 * 3 + 3)))

    def visit():
        for r in range(9):
            for c in range(9):
                if grid[r][c] == ".":
                    for value in digits:
                        if valid(r, c, value):
                            grid[r][c] = value
                            if visit():
                                return True
                            grid[r][c] = "."
                    return False
        return True

    return visit()


def valid_solution(board, initial):
    digits = set("123456789")
    if any(initial[r][c] != "." and initial[r][c] != board[r][c]
           for r in range(9) for c in range(9)):
        return False
    units = list(board) + [[board[r][c] for r in range(9)] for c in range(9)]
    units += [[board[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)]
              for br in (0, 3, 6) for bc in (0, 3, 6)]
    return all(set(unit) == digits for unit in units)


class BacktrackCards(unittest.TestCase):
    def test_subset_xor_against_masks(self):
        for n in range(6):
            for values in itertools.product(range(4), repeat=n):
                expected = 0
                for subset in masks(values):
                    xor = 0
                    for x in subset:
                        xor ^= x
                    expected += xor
                self.assertEqual(SOLVE["1863"](values), expected)
        values = list(range(12))
        expected = 0
        for subset in masks(values):
            xor = 0
            for value in subset:
                xor ^= value
            expected += xor
        self.assertEqual(SOLVE["1863"](values), expected)

    def test_subsets_against_masks(self):
        for n in range(8):
            values = list(range(n))
            result = SOLVE["78"](values)
            self.assertEqual(len(result), 2 ** n)
            self.assertEqual(set(map(tuple, result)), set(masks(values)))
            self.assertEqual(values, list(range(n)))

    def test_permutations_against_library_enumeration(self):
        for n in range(8):
            result = SOLVE["46"](list(range(n)))
            expected = set(itertools.permutations(range(n)))
            self.assertEqual(len(result), len(expected))
            self.assertEqual(set(map(tuple, result)), expected)

    def test_duplicate_subsets_against_masks(self):
        for n in range(7):
            for values in itertools.product(range(3), repeat=n):
                expected = {tuple(sorted(s)) for s in masks(values)}
                result = SOLVE["90"](values)
                self.assertEqual(len(result), len(expected))
                self.assertEqual(set(map(tuple, result)), expected)

    def test_combination_sum_against_count_vectors(self):
        for candidates in ([], [1], [2], [2, 3], [2, 3, 5], [4, 2, 7]):
            for target in range(13):
                expected = set()
                for counts in itertools.product(*(range(target // x + 1) for x in candidates)):
                    if sum(x * count for x, count in zip(candidates, counts)) == target:
                        expected.add(tuple(sorted(x for x, count in zip(candidates, counts)
                                                  for _ in range(count))))
                result = SOLVE["39"](candidates, target)
                self.assertEqual(len(result), len(expected))
                self.assertEqual(set(map(tuple, result)), expected)

    def test_parentheses_against_all_strings(self):
        for n in range(7):
            expected = set()
            for chars in itertools.product("()", repeat=2 * n):
                balance = 0
                for char in chars:
                    balance += 1 if char == "(" else -1
                    if balance < 0:
                        break
                else:
                    if balance == 0:
                        expected.add("".join(chars))
            result = SOLVE["22"](n)
            self.assertEqual(len(result), len(expected))
            self.assertEqual(set(result), expected)

    def test_palindrome_partitions_against_cut_masks(self):
        for n in range(8):
            for chars in itertools.product("ab", repeat=n):
                s = "".join(chars)
                expected = set()
                if not n:
                    expected.add(())
                else:
                    for mask in range(1 << (n - 1)):
                        ends = [i + 1 for i in range(n - 1) if mask & (1 << i)] + [n]
                        starts = [0] + ends[:-1]
                        parts = tuple(s[a:b] for a, b in zip(starts, ends))
                        if all(piece == piece[::-1] for piece in parts):
                            expected.add(parts)
                result = SOLVE["131"](s)
                self.assertEqual(len(result), len(expected))
                self.assertEqual(set(map(tuple, result)), expected)

    def test_word_search_against_coordinate_sequences(self):
        self.assertTrue(SOLVE["79"]([], ""))
        self.assertFalse(SOLVE["79"]([], "A"))
        for cells in itertools.product("AB", repeat=4):
            board = [list(cells[:2]), list(cells[2:])]
            for n in range(6):
                for chars in itertools.product("AB", repeat=n):
                    word = "".join(chars)
                    before = [row[:] for row in board]
                    self.assertEqual(SOLVE["79"](board, word), word_oracle(board, word))
                    self.assertEqual(board, before)

    def test_equal_groups_against_assignments(self):
        solve = SOLVE["698"]
        self.assertFalse(solve([], 1))
        self.assertFalse(solve([1], 0))
        self.assertFalse(solve([1], 2))
        rng = random.Random(698)
        for n in range(1, 8):
            for _ in range(90):
                values = [rng.randrange(1, 8) for _ in range(n)]
                k = rng.randrange(1, min(n, 4) + 1)
                expected = any(len(set(totals)) == 1 for totals in assignment_totals(values, k))
                self.assertEqual(solve(values, k), expected, (values, k))

    def test_queens_against_permutations(self):
        for n in range(10):
            expected = {p for p in itertools.permutations(range(n))
                        if len({r - c for r, c in enumerate(p)}) == n
                        and len({r + c for r, c in enumerate(p)}) == n}
            boards = SOLVE["51"](n)
            actual = set()
            for board in boards:
                self.assertEqual(len(board), n)
                for row in board:
                    self.assertEqual(len(row), n)
                    self.assertEqual(row.count("Q"), 1)
                    self.assertEqual(set(row) - {".", "Q"}, set())
                actual.add(tuple(row.index("Q") for row in board))
            self.assertEqual(len(boards), len(expected))
            self.assertEqual(actual, expected)

    def test_cookies_against_assignments(self):
        solve = SOLVE["2305"]
        self.assertEqual(solve([], 2), 0)
        rng = random.Random(2305)
        for n in range(1, 8):
            for _ in range(80):
                values = [rng.randrange(1, 10) for _ in range(n)]
                k = rng.randrange(1, min(n, 4) + 1)
                expected = min(max(totals) for totals in assignment_totals(values, k))
                self.assertEqual(solve(values, k), expected, (values, k))

    def test_sudoku_against_fixed_order_search(self):
        solve = SOLVE["37"]
        solution = [list(row) for row in (
            "123456789", "456789123", "789123456", "234567891", "567891234",
            "891234567", "345678912", "678912345", "912345678",
        )]
        rng = random.Random(37)
        for holes in range(16):
            for _ in range(10):
                board = [row[:] for row in solution]
                for pos in rng.sample(range(81), holes):
                    board[pos // 9][pos % 9] = "."
                before = [row[:] for row in board]
                expected = sudoku_oracle(before)
                self.assertEqual(solve(board), expected)
                self.assertTrue(valid_solution(board, before))

        for holes in (40, 50, 60):
            board = [row[:] for row in solution]
            for pos in rng.sample(range(81), holes):
                board[pos // 9][pos % 9] = "."
            before = [row[:] for row in board]
            self.assertTrue(sudoku_oracle(before))
            self.assertTrue(solve(board))
            self.assertTrue(valid_solution(board, before))

        # Valid givens with no possible value for (0, 0).
        board = [row[:] for row in solution]
        board[0][0] = "."
        board[1][0] = "1"
        board[1][6] = "."
        before = [row[:] for row in board]
        self.assertFalse(sudoku_oracle(before))
        self.assertFalse(solve(board))
        self.assertEqual(board, before)

        # This conflict-free puzzle has no immediately empty candidate set,
        # so both solvers must explore beyond their initial state.
        board = [list(row) for row in (
            "..34.67..", "456.89123", ".8912.456", "23456..81", ".6789.23.",
            "89.23..67", ".45.....2", "6789..3..", "9.2.4567.",
        )]
        before = [row[:] for row in board]
        self.assertFalse(sudoku_oracle(before))
        self.assertFalse(solve(board))
        self.assertEqual(board, before)

        invalid = [row[:] for row in solution]
        invalid[0][0] = invalid[0][1]
        before = [row[:] for row in invalid]
        self.assertFalse(solve(invalid))
        self.assertEqual(invalid, before)


if __name__ == "__main__":
    unittest.main()
