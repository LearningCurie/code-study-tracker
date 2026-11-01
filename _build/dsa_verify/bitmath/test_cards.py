import ast
import itertools
import math
import random
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "29-bitmath.cards.md"
CARDS = {
    match.group(1): match.group(2)
    for match in re.finditer(r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)", SOURCE.read_text())
}


def code_for(problem):
    section = CARDS[problem].split("## Code", 1)[1].split("## Complexity", 1)[0]
    return re.search(r"```python\n(.*?)\n```", section, re.S).group(1)


def solution(problem, name):
    namespace = {}
    exec(compile(code_for(problem), f"card-{problem}", "exec"), namespace)
    return namespace[name]


class TestBitMathCards(unittest.TestCase):
    def test_single_number_against_known_single(self):
        solve = solution("136", "single_number")
        rng = random.Random(136)
        for n in range(20):
            for _ in range(50):
                values = rng.sample(range(-100, 100), n + 1)
                nums = [values[0]] + values[1:] * 2
                rng.shuffle(nums)
                self.assertEqual(solve(nums), values[0])

    def test_count_bits_against_builtin(self):
        solve = solution("338", "count_bits")
        for n in range(400):
            self.assertEqual(solve(n), [i.bit_count() for i in range(n + 1)])
        with self.assertRaises(ValueError):
            solve(-1)

    def test_string_gcd_against_prefix_enumeration(self):
        solve = solution("1071", "gcd_of_strings")
        strings = ["".join(chars) for n in range(1, 6) for chars in itertools.product("ab", repeat=n)]
        for first in strings:
            for second in strings:
                options = [
                    first[:length] for length in range(1, min(len(first), len(second)) + 1)
                    if len(first) % length == 0 and len(second) % length == 0
                    and first[:length] * (len(first) // length) == first
                    and first[:length] * (len(second) // length) == second
                ]
                self.assertEqual(solve(first, second), max(options, key=len, default=""))

    def test_bitwise_sum_against_signed_32bit_addition(self):
        solve = solution("371", "bitwise_sum")
        tree = ast.parse(code_for("371"))
        self.assertFalse(any(isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub))
                             for node in ast.walk(tree)))
        rng = random.Random(371)
        cases = [(rng.randrange(-(1 << 31), 1 << 31), rng.randrange(-(1 << 31), 1 << 31))
                 for _ in range(5000)]
        cases.extend([(-(1 << 31), -1), ((1 << 31) - 1, 1), (-1, 1), (0, 0)])
        for a, b in cases:
            expected = (a + b + (1 << 31)) % (1 << 32) - (1 << 31)
            self.assertEqual(solve(a, b), expected)

    def test_two_singles_against_known_values(self):
        solve = solution("260", "two_single_numbers")
        rng = random.Random(260)
        for n in range(20):
            for _ in range(50):
                values = rng.sample(range(-100, 100), n + 2)
                nums = values[:2] + values[2:] * 2
                rng.shuffle(nums)
                self.assertEqual(set(solve(nums)), set(values[:2]))

    def test_thrice_single_against_known_values(self):
        solve = solution("137", "single_number_thrice")
        rng = random.Random(137)
        for n in range(20):
            for _ in range(50):
                values = rng.sample(range(-100, 100), n + 1)
                nums = [values[0]] + values[1:] * 3
                rng.shuffle(nums)
                self.assertEqual(solve(nums), values[0])
        self.assertEqual(solve([-(1 << 31)]), -(1 << 31))
        self.assertEqual(solve([(1 << 31) - 1]), (1 << 31) - 1)

    def test_maximum_or_subsets_against_combinations(self):
        solve = solution("2044", "count_max_or_subsets")
        rng = random.Random(2044)
        for n in range(10):
            for _ in range(40):
                nums = [rng.randrange(16) for _ in range(n)]
                target = 0
                for value in nums:
                    target |= value
                expected = 0
                for count in range(1, n + 1):
                    for subset in itertools.combinations(nums, count):
                        value = 0
                        for item in subset:
                            value |= item
                        expected += value == target
                self.assertEqual(solve(nums), expected)

    def test_sieve_against_trial_division(self):
        solve = solution("204", "count_primes")
        for n in range(500):
            expected = sum(all(number % divisor for divisor in range(2, math.isqrt(number) + 1))
                           for number in range(2, n))
            self.assertEqual(solve(n), expected)

    def test_power_against_builtin(self):
        solve = solution("50", "fast_power")
        rng = random.Random(50)
        for _ in range(3000):
            base = rng.uniform(-5, 5)
            exponent = rng.randrange(-30, 31)
            self.assertTrue(math.isclose(solve(base, exponent), base ** exponent, rel_tol=1e-12, abs_tol=1e-12))
        self.assertEqual(solve(1.0, -(1 << 31)), 1.0)
        self.assertEqual(solve(-1.0, (1 << 31) - 1), -1.0)

    def test_collinear_points_against_cross_products(self):
        solve = solution("149", "max_collinear_points")
        rng = random.Random(149)
        grid = list(itertools.product(range(-3, 4), repeat=2))
        for n in range(10):
            for _ in range(100):
                points = rng.sample(grid, n)
                expected = n if n < 2 else max(
                    sum((b[0] - a[0]) * (c[1] - a[1]) == (b[1] - a[1]) * (c[0] - a[0]) for c in points)
                    for a, b in itertools.combinations(points, 2)
                )
                self.assertEqual(solve(points), expected)

    def test_binomial_queries_against_math_comb(self):
        solve = solution("cses:1079", "binomial_queries")
        rng = random.Random(1079)
        queries = [(a, rng.randrange(a + 1)) for a in range(101)]
        self.assertEqual(solve(queries), [math.comb(a, b) % 1_000_000_007 for a, b in queries])
        self.assertEqual(solve([]), [])
        with self.assertRaises(ValueError):
            solve([(2, 3)])

    def test_puzzle_masks_against_set_membership(self):
        solve = solution("1178", "valid_word_counts")
        rng = random.Random(1178)
        alphabet = "abcdefghij"
        for _ in range(500):
            words = ["".join(rng.choices(alphabet, k=rng.randrange(1, 10))) for _ in range(rng.randrange(30))]
            puzzles = ["".join(rng.sample(alphabet, 7)) for _ in range(rng.randrange(10))]
            expected = [sum(puzzle[0] in word and set(word) <= set(puzzle) for word in words) for puzzle in puzzles]
            self.assertEqual(solve(words, puzzles), expected)


if __name__ == "__main__":
    unittest.main()
