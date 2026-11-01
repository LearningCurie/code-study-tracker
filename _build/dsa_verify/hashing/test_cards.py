import itertools
import random
import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dsa" / "06-hashing.cards.md"
MODULE = ROOT / "dsa" / "06-hashing.md"
EXPECTED = {"217", "1", "242", "49", "347", "36", "2001", "128", "454", "2131", "554", "229"}
CARDS = {
    match.group(1): match.group(2)
    for match in re.finditer(r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)", SOURCE.read_text())
}


def solution(problem, name):
    blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"card {problem}: expected exactly one tested Python block")
    namespace = {}
    exec(compile(blocks[0], f"card-{problem}", "exec"), namespace)
    return namespace[name]


class TestHashingCards(unittest.TestCase):
    def test_inventory_and_all_python_blocks(self):
        practice = MODULE.read_text().split("=== practice\n", 1)[1]
        self.assertEqual(set(re.findall(r"(?m)^- (\d+) (?:core|derive|stretch|mixed)$", practice)), EXPECTED)
        self.assertEqual(set(CARDS), EXPECTED)
        for card in CARDS.values():
            self.assertEqual(len(re.findall(r"```python\n(.*?)\n```", card, re.S)), 1)

    def test_contains_duplicate_exhaustive(self):
        solve = solution("217", "contains_duplicate")
        for length in range(8):
            for nums in itertools.product(range(-1, 2), repeat=length):
                expected = any(nums[i] == nums[j] for i in range(length) for j in range(i))
                self.assertEqual(solve(nums), expected, nums)

    def test_two_sum_exhaustive(self):
        solve = solution("1", "two_sum")
        for length in range(7):
            for nums in itertools.product(range(-2, 3), repeat=length):
                for target in range(-4, 5):
                    pairs = [(i, j) for i in range(length) for j in range(i + 1, length)
                             if nums[i] + nums[j] == target]
                    actual = solve(nums, target)
                    if pairs:
                        self.assertEqual(len(actual), 2)
                        self.assertIn(tuple(sorted(actual)), pairs)
                    else:
                        self.assertEqual(actual, [])

    def test_anagram_exhaustive(self):
        solve = solution("242", "valid_anagram")
        strings = ["".join(chars) for n in range(5) for chars in itertools.product("abc", repeat=n)]
        for a in strings:
            for b in strings:
                self.assertEqual(solve(a, b), sorted(a) == sorted(b), (a, b))
        self.assertTrue(solve("éa", "aé"))
        self.assertFalse(solve("A", "a"))

    def test_groups_against_sorted_word_keys(self):
        solve = solution("49", "group_anagrams")
        rng = random.Random(49)
        for _ in range(1000):
            words = ["".join(rng.choices("abc", k=rng.randrange(6))) for _ in range(rng.randrange(20))]
            actual = solve(words)
            self.assertEqual(Counter(word for group in actual for word in group), Counter(words))
            expected_groups = {}
            for word in words:
                expected_groups.setdefault("".join(sorted(word)), []).append(word)
            self.assertEqual(
                sorted(sorted(group) for group in actual),
                sorted(sorted(group) for group in expected_groups.values()),
            )

    def test_top_k_against_sorted_frequency_cutoff(self):
        solve = solution("347", "top_k_frequent")
        rng = random.Random(347)
        for _ in range(2000):
            nums = [rng.randrange(-5, 6) for _ in range(rng.randrange(30))]
            distinct = set(nums)
            k = rng.randrange(len(distinct) + 1)
            actual = solve(nums, k)
            self.assertEqual(len(actual), k)
            self.assertEqual(len(set(actual)), k)
            self.assertTrue(set(actual) <= distinct)
            if k:
                counts = {value: nums.count(value) for value in distinct}
                self.assertEqual(sorted((counts[value] for value in actual), reverse=True),
                                 sorted(counts.values(), reverse=True)[:k])

    def test_sudoku_against_pairwise_conflicts(self):
        solve = solution("36", "valid_sudoku")

        def oracle(board):
            cells = [(r, c, board[r][c]) for r in range(9) for c in range(9) if board[r][c] != "."]
            return not any(
                a == b and (r1 == r2 or c1 == c2 or (r1 // 3, c1 // 3) == (r2 // 3, c2 // 3))
                for (r1, c1, a), (r2, c2, b) in itertools.combinations(cells, 2)
            )

        rng = random.Random(36)
        board = [["."] * 9 for _ in range(9)]
        self.assertTrue(solve(board))
        for _ in range(2500):
            board = [["."] * 9 for _ in range(9)]
            for _ in range(rng.randrange(30)):
                board[rng.randrange(9)][rng.randrange(9)] = str(rng.randrange(1, 10))
            self.assertEqual(solve(board), oracle(board), board)
        for r in range(9):
            for c in range(9):
                board = [["."] * 9 for _ in range(9)]
                board[r][c] = "7"
                for rr, cc in ((r, (c + 1) % 9), ((r + 1) % 9, c),
                               (r // 3 * 3 + (r + 1) % 3, c // 3 * 3 + (c + 1) % 3)):
                    board[rr][cc] = "7"
                    self.assertFalse(solve(board))
                    board[rr][cc] = "."

    def test_rectangle_ratios_against_cross_products(self):
        solve = solution("2001", "interchangeable_rectangles")
        rng = random.Random(2001)
        for _ in range(3000):
            rectangles = [(rng.randrange(1, 21), rng.randrange(1, 21)) for _ in range(rng.randrange(25))]
            expected = sum(a * d == c * b for (a, b), (c, d) in itertools.combinations(rectangles, 2))
            self.assertEqual(solve(rectangles), expected)
        self.assertEqual(solve([(10**12, 10**12 - 1), (10**12 + 1, 10**12)]), 0)
        self.assertEqual(solve([(1, 1)] * 1000), 499500)

    def test_consecutive_against_sorted_distinct(self):
        solve = solution("128", "longest_consecutive")
        rng = random.Random(128)
        for _ in range(5000):
            nums = [rng.randrange(-10, 11) for _ in range(rng.randrange(30))]
            ordered = sorted(set(nums))
            best = current = 0
            previous = None
            for value in ordered:
                current = current + 1 if previous is not None and value == previous + 1 else 1
                best = max(best, current)
                previous = value
            self.assertEqual(solve(nums), best)
        self.assertEqual(solve([1] * 1000 + list(range(2, 1002))), 1001)

    def test_four_sum_against_index_enumeration(self):
        solve = solution("454", "four_sum_count")
        rng = random.Random(454)
        for _ in range(3000):
            arrays = [[rng.randrange(-3, 4) for _ in range(rng.randrange(5))] for _ in range(4)]
            expected = sum(sum(quadruple) == 0 for quadruple in itertools.product(*arrays))
            self.assertEqual(solve(*arrays), expected, arrays)
        self.assertEqual(solve([0] * 10, [0] * 9, [0] * 8, [0] * 7), 5040)

    def test_palindrome_against_ordered_occurrence_search(self):
        solve = solution("2131", "longest_palindrome_words")

        def oracle(words):
            best = 0
            for count in range(1, len(words) + 1):
                for indices in itertools.permutations(range(len(words)), count):
                    joined = "".join(words[i] for i in indices)
                    if joined == joined[::-1]:
                        best = max(best, len(joined))
            return best

        rng = random.Random(2131)
        for _ in range(350):
            words = [rng.choice(("aa", "ab", "ba", "bb", "ac", "ca", "cc"))
                     for _ in range(rng.randrange(7))]
            self.assertEqual(solve(words), oracle(words), words)
        self.assertEqual(solve(["aa"] * 7 + ["bb"] * 3), 18)

    def test_wall_against_all_half_step_positions(self):
        solve = solution("554", "least_bricks")
        rng = random.Random(554)
        self.assertEqual(solve([]), 0)
        for _ in range(2500):
            width = rng.randrange(1, 12)
            wall = []
            for _ in range(rng.randrange(1, 10)):
                cuts = [0] + [i for i in range(1, width) if rng.randrange(2)] + [width]
                wall.append([b - a for a, b in zip(cuts, cuts[1:])])
            expected = min(
                sum(all(2 * sum(row[:i]) != x for i in range(1, len(row))) for row in wall)
                for x in range(1, 2 * width)
            )
            self.assertEqual(solve(wall), expected, wall)

    def test_majority_against_direct_counts_exhaustive(self):
        solve = solution("229", "majority_thirds")
        for length in range(10):
            for nums in itertools.product(range(-1, 2), repeat=length):
                expected = {value for value in set(nums) if nums.count(value) * 3 > length}
                actual = solve(nums)
                self.assertEqual(len(actual), len(set(actual)))
                self.assertEqual(set(actual), expected, nums)
        rng = random.Random(229)
        for _ in range(1000):
            nums = [rng.randrange(8) for _ in range(rng.randrange(50))]
            expected = {value for value in set(nums) if nums.count(value) * 3 > len(nums)}
            self.assertEqual(set(solve(nums)), expected)


if __name__ == "__main__":
    unittest.main()
