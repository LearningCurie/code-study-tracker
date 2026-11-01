"""Verify the actual card code against independent small-input enumerations."""

import itertools
from collections import deque
from pathlib import Path
import random
import re
import sys
import unittest


BUILD = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUILD))
from build_dsa_guide import CARD_HEADINGS, CARD_WORDS, Problems, load_module, parse_cards
import mdlite


MODULE = BUILD / "dsa" / "24-dpseq.md"
SOURCE = BUILD / "dsa" / "24-dpseq.cards.md"
NAMES = {
    "64": "min_path_sum", "221": "maximal_square", "1143": "lcs_length",
    "72": "edit_distance", "97": "is_interleave",
    "516": "longest_palindromic_subsequence", "416": "can_partition",
    "494": "target_sum_ways", "322": "min_coins",
    "518": "coin_combinations", "10": "regex_match",
    "132": "min_palindrome_cuts",
}
CARDS = parse_cards(SOURCE)
CODE = {}
for pid, card in CARDS.items():
    blocks = re.findall(r"```python\n(.*?)\n```", card["md"], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"Card {pid}: expected exactly one Python block, got {len(blocks)}")
    namespace = {}
    exec(compile(blocks[0], f"{SOURCE.name}:{pid}", "exec"), namespace)
    CODE[pid] = namespace[NAMES[pid]]


def words(max_length, alphabet="ab"):
    return ["".join(t) for length in range(max_length + 1)
            for t in itertools.product(alphabet, repeat=length)]


def subsequences(s):
    return {"".join(s[i] for i in range(len(s)) if mask & (1 << i))
            for mask in range(1 << len(s))}


def path_costs(grid, row=0, col=0):
    if row == len(grid) - 1 and col == len(grid[0]) - 1:
        return [grid[row][col]]
    costs = []
    if row + 1 < len(grid):
        costs.extend(path_costs(grid, row + 1, col))
    if col + 1 < len(grid[0]):
        costs.extend(path_costs(grid, row, col + 1))
    return [grid[row][col] + x for x in costs]


def largest_square(matrix):
    best = 0
    for r in range(len(matrix)):
        for c in range(len(matrix[0])):
            for side in range(1, min(len(matrix) - r, len(matrix[0]) - c) + 1):
                if all(matrix[i][j] == "1"
                       for i in range(r, r + side) for j in range(c, c + side)):
                    best = max(best, side * side)
    return best


def edit_bfs(source, target):
    # A shortest script never needs a string longer than the larger endpoint:
    # delete surplus characters first, then replace and insert as necessary.
    max_length = max(len(source), len(target))
    queue = deque([(source, 0)])
    seen = {source}
    while queue:
        current, distance = queue.popleft()
        if current == target:
            return distance
        neighbors = set()
        for i in range(len(current)):
            neighbors.add(current[:i] + current[i + 1:])
            for ch in "ab":
                neighbors.add(current[:i] + ch + current[i + 1:])
        if len(current) < max_length:
            for i in range(len(current) + 1):
                for ch in "ab":
                    neighbors.add(current[:i] + ch + current[i:])
        for nxt in neighbors - seen:
            seen.add(nxt)
            queue.append((nxt, distance + 1))
    raise AssertionError("target must be reachable")


def interleave_brute(a, b, merged):
    if len(a) + len(b) != len(merged):
        return False

    def visit(i, j):
        if i == len(a) and j == len(b):
            return True
        k = i + j
        return ((i < len(a) and a[i] == merged[k] and visit(i + 1, j))
                or (j < len(b) and b[j] == merged[k] and visit(i, j + 1)))

    return visit(0, 0)


def subset_sums(nums):
    return [sum(x for i, x in enumerate(nums) if mask & (1 << i))
            for mask in range(1 << len(nums))]


def signs_brute(nums, target):
    return sum(sum(sign * x for sign, x in zip(signs, nums)) == target
               for signs in itertools.product((-1, 1), repeat=len(nums)))


def coins_bfs(coins, amount):
    queue = deque([(0, 0)])
    seen = {0}
    while queue:
        value, count = queue.popleft()
        if value == amount:
            return count
        for coin in coins:
            nxt = value + coin
            if nxt <= amount and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, count + 1))
    return -1


def coin_vectors(coins, amount, i=0):
    if i == len(coins):
        return int(amount == 0)
    coin = coins[i]
    return sum(coin_vectors(coins, amount - count * coin, i + 1)
               for count in range(amount // coin + 1))


def regex_brute(text, units):
    def visit(pos, unit):
        if unit == len(units):
            return pos == len(text)
        atom, starred = units[unit]
        if not starred:
            return (pos < len(text) and (atom == "." or text[pos] == atom)
                    and visit(pos + 1, unit + 1))
        end = pos
        while True:
            if visit(end, unit + 1):
                return True
            if end == len(text) or (atom != "." and text[end] != atom):
                return False
            end += 1

    return visit(0, 0)


def cuts_brute(s):
    if not s:
        return 0
    best = len(s) - 1
    for mask in range(1 << (len(s) - 1)):
        starts = [0] + [i for i in range(1, len(s)) if mask & (1 << (i - 1))]
        ends = starts[1:] + [len(s)]
        if all(s[a:b] == s[a:b][::-1] for a, b in zip(starts, ends)):
            best = min(best, len(starts) - 1)
    return best


class CardTests(unittest.TestCase):
    def test_structure_and_coverage(self):
        issues = []
        module = load_module(MODULE, issues)
        self.assertEqual(issues, [])
        self.assertEqual(set(CARDS), {p["id"] for p in module["practice"]})
        self.assertEqual(set(CARDS), set(NAMES))
        problems = Problems()
        for pid, card in CARDS.items():
            with self.subTest(card=pid):
                text = card["md"]
                self.assertEqual(re.findall(r"(?m)^## .+$", text), list(CARD_HEADINGS))
                self.assertGreaterEqual(mdlite.plain(text),
                                        CARD_WORDS[problems.record(pid)[1]])
                steps = re.findall(r"```steps\n(.*?)\n```", text, re.S)
                self.assertEqual(len(steps), 1)
                self.assertGreaterEqual(len(re.split(r"(?m)^---$", steps[0])), 2)
                variations = text.split("## Variations", 1)[1]
                self.assertIn(len(re.findall(r"(?m)^- ", variations)), (2, 3, 4))
                mdlite.render(text)

    def test_traced_examples(self):
        examples = [
            ("64", ([[1, 3], [2, 1]],), 4),
            ("221", ([["1", "1"], ["1", "1"]],), 4),
            ("1143", ("ab", "ac"), 1),
            ("72", ("ab", "ac"), 1),
            ("97", ("ab", "cd", "acbd"), True),
            ("516", ("aba",), 3),
            ("416", ([1, 2, 3],), True),
            ("494", ([0, 1], 1), 2),
            ("322", ([1, 3, 4], 6), 2),
            ("518", (4, [1, 2]), 3),
            ("10", ("aab", "c*a*b"), True),
            ("132", ("aab",), 1),
        ]
        for pid, args, expected in examples:
            with self.subTest(card=pid):
                self.assertEqual(CODE[pid](*args), expected)

    def test_grids(self):
        rng = random.Random(2401)
        for rows, cols in ((1, 1), (1, 5), (5, 1), (2, 3), (3, 3), (4, 4)):
            for _ in range(80):
                grid = [[rng.randrange(5) for _ in range(cols)] for _ in range(rows)]
                original = [row[:] for row in grid]
                self.assertEqual(CODE["64"](grid), min(path_costs(grid)))
                self.assertEqual(grid, original)
        for rows, cols in ((1, 1), (1, 4), (2, 3), (3, 3)):
            for values in itertools.product("01", repeat=rows * cols):
                matrix = [list(values[r * cols:(r + 1) * cols]) for r in range(rows)]
                original = [row[:] for row in matrix]
                self.assertEqual(CODE["221"](matrix), largest_square(matrix))
                self.assertEqual(matrix, original)
        self.assertEqual(CODE["64"]([[200] * 200 for _ in range(200)]), 79800)
        self.assertEqual(CODE["221"]([["1"] * 300 for _ in range(300)]), 90000)

    def test_lcs_and_palindromic_subsequence(self):
        samples = words(5)
        for a in samples:
            subs_a = subsequences(a)
            for b in samples:
                expected = max(map(len, subs_a & subsequences(b)))
                self.assertEqual(CODE["1143"](a, b), expected, (a, b))
            expected_pal = max(len(x) for x in subs_a if x == x[::-1])
            self.assertEqual(CODE["516"](a), expected_pal, a)
        self.assertEqual(CODE["1143"]("a" * 1000, "a" * 1000), 1000)
        self.assertEqual(CODE["516"]("a" * 1000), 1000)

    def test_edit_distance(self):
        for a in words(3):
            for b in words(3):
                self.assertEqual(CODE["72"](a, b), edit_bfs(a, b), (a, b))
        self.assertEqual(CODE["72"]("", "a" * 500), 500)
        self.assertEqual(CODE["72"]("a" * 500, "b" * 500), 500)

    def test_interleaving(self):
        sources = words(3)
        for a in sources:
            for b in sources:
                for merged in itertools.product("ab", repeat=len(a) + len(b)):
                    text = "".join(merged)
                    self.assertEqual(CODE["97"](a, b, text),
                                     interleave_brute(a, b, text), (a, b, text))
                self.assertFalse(CODE["97"](a, b, "x" * (len(a) + len(b) + 1)))
        self.assertTrue(CODE["97"]("a" * 100, "b" * 100, "ab" * 100))
        self.assertTrue(CODE["97"]("aabcc", "dbbca", "aadbbcbcac"))
        self.assertFalse(CODE["97"]("aabcc", "dbbca", "aadbbbaccc"))

    def test_partition_and_target_sum(self):
        for n in range(7):
            for nums in itertools.product((1, 2, 3), repeat=n):
                sums = subset_sums(nums)
                total = sum(nums)
                self.assertEqual(CODE["416"](nums),
                                 total % 2 == 0 and total // 2 in sums, nums)
        for n in range(6):
            for nums in itertools.product((0, 1, 2), repeat=n):
                for target in range(-sum(nums) - 1, sum(nums) + 2):
                    self.assertEqual(CODE["494"](nums, target),
                                     signs_brute(nums, target), (nums, target))
        self.assertTrue(CODE["416"]([100] * 200))
        self.assertEqual(CODE["494"]([0] * 20, 0), 2 ** 20)
        self.assertFalse(CODE["416"]([1, 2, 5]))

    def test_coin_problems(self):
        for mask in range(1, 1 << 6):
            coins = [i + 1 for i in range(6) if mask & (1 << i)]
            for amount in range(21):
                self.assertEqual(CODE["322"](coins, amount),
                                 coins_bfs(coins, amount), (coins, amount))
                self.assertEqual(CODE["518"](amount, coins),
                                 coin_vectors(coins, amount), (coins, amount))
        self.assertEqual(CODE["322"]([2], 3), -1)
        self.assertEqual(CODE["322"]([1], 10000), 10000)
        self.assertEqual(CODE["518"](0, [3, 5]), 1)
        self.assertEqual(CODE["518"](5000, [1]), 1)

    def test_regex(self):
        options = list(itertools.product("ab.", (False, True)))
        texts = words(4)
        for count in range(4):
            for units in itertools.product(options, repeat=count):
                pattern = "".join(atom + ("*" if star else "") for atom, star in units)
                for text in texts:
                    self.assertEqual(CODE["10"](text, pattern),
                                     regex_brute(text, units), (text, pattern))
        self.assertTrue(CODE["10"]("aab", "c*a*b"))
        self.assertFalse(CODE["10"]("ab", ".*c"))
        self.assertTrue(CODE["10"]("", "a*b*"))
        self.assertFalse(CODE["10"]("", "."))
        self.assertTrue(CODE["10"]("a" * 20, "a*" * 10))

    def test_palindrome_cuts(self):
        for s in words(9):
            self.assertEqual(CODE["132"](s), cuts_brute(s), s)
        self.assertEqual(CODE["132"]("aab"), 1)
        self.assertEqual(CODE["132"]("a" * 2000), 0)
        self.assertEqual(CODE["132"]("ab" * 1000), 1)


if __name__ == "__main__":
    unittest.main()
