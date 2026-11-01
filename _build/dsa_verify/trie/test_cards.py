import itertools
import random
import re
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "18-trie.cards.md"
TEXT = SOURCE.read_text(encoding="utf-8")
CARDS = dict(re.findall(r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)", TEXT))
IDS = {"208", "3043", "648", "1268", "677", "211", "421", "2707", "2416", "212", "1707", "336"}


def solution(problem, name):
    blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"expected exactly one Python block for {problem}")
    namespace = {}
    exec(compile(blocks[0], f"card-{problem}", "exec"), namespace)
    return namespace[name]


def strings(alphabet, maximum):
    return ["".join(chars) for size in range(1, maximum + 1)
            for chars in itertools.product(alphabet, repeat=size)]


def common_prefix(a, b):
    count = 0
    for x, y in zip(str(a), str(b)):
        if x != y:
            break
        count += 1
    return count


def word_on_board(board, word):
    rows = len(board)
    cols = len(board[0]) if rows else 0

    def visit(r, c, i, seen):
        if (r, c) in seen or board[r][c] != word[i]:
            return False
        if i + 1 == len(word):
            return True
        seen = seen | {(r, c)}
        return any(visit(nr, nc, i + 1, seen)
                   for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                   if 0 <= nr < rows and 0 <= nc < cols)

    return any(visit(r, c, 0, set()) for r in range(rows) for c in range(cols))


class TestTrieCards(unittest.TestCase):
    def test_inventory_and_all_displayed_code(self):
        self.assertEqual(set(CARDS), IDS)
        self.assertEqual(len(re.findall(r"```python\n", TEXT)), len(IDS))
        for problem in IDS:
            blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
            self.assertEqual(len(blocks), 1, problem)
            exec(compile(blocks[0], f"card-{problem}", "exec"), {})

    def test_208_membership_and_prefix_simulation(self):
        trie = solution("208", "Trie")()
        stored = set()
        pool = strings("abc", 3)
        self.assertFalse(trie.search("a"))
        self.assertTrue(trie.starts_with(""))
        for word in ["ant", "an", "ant"] + pool:
            trie.insert(word)
            stored.add(word)
            for candidate in ["an", "ant", "z"] + pool:
                self.assertEqual(trie.search(candidate), candidate in stored)
                self.assertEqual(trie.starts_with(candidate),
                                 any(s.startswith(candidate) for s in stored))

    def test_3043_pairwise_digit_oracle(self):
        solve = solution("3043", "longest_common_prefix")
        self.assertEqual(solve([451, 82], [4599, 8]), 2)
        self.assertEqual(solve([], [12]), 0)
        rng = random.Random(3043)
        for _ in range(600):
            first = [rng.randrange(1, 100000) for _ in range(rng.randrange(9))]
            second = [rng.randrange(1, 100000) for _ in range(rng.randrange(9))]
            expected = max((common_prefix(a, b) for a in first for b in second), default=0)
            self.assertEqual(solve(first, second), expected)

    def test_648_root_scan_oracle(self):
        solve = solution("648", "replace_words")
        self.assertEqual(solve(["go", "gone"], "gone home"), "go home")
        rng = random.Random(648)
        pool = strings("abc", 4)
        for _ in range(500):
            roots = rng.sample(pool, rng.randrange(15))
            words = rng.choices(pool, k=rng.randrange(1, 12))
            expected = [min((root for root in roots if word.startswith(root)),
                            key=len, default=word) for word in words]
            self.assertEqual(solve(roots, " ".join(words)), " ".join(expected))

    def test_1268_filter_sort_oracle(self):
        solve = solution("1268", "suggested_products")
        self.assertEqual(solve(["map", "mat", "moss", "mud"], "ma"),
                         [["map", "mat", "moss"], ["map", "mat"]])
        rng = random.Random(1268)
        pool = strings("abc", 4)
        for _ in range(500):
            products = rng.sample(pool, rng.randrange(20))
            original = products[:]
            search = rng.choice(pool) + rng.choice(["", "z"])
            expected = [sorted(word for word in products if word.startswith(search[:i]))[:3]
                        for i in range(1, len(search) + 1)]
            actual = solve(products, search)
            self.assertEqual(actual, expected)
            self.assertEqual(products, original)
            if len(actual) > 1:
                actual[0].append("mutation")
                self.assertEqual(actual[1:], expected[1:])

    def test_677_updates_against_dictionary(self):
        cls = solution("677", "MapSum")
        store = cls()
        values = {}
        self.assertEqual(store.sum("a"), 0)
        for key, value in [("art", 4), ("arc", 2), ("art", 1)]:
            store.insert(key, value)
            values[key] = value
        self.assertEqual(store.sum("ar"), 3)
        rng = random.Random(677)
        pool = strings("abc", 3)
        for _ in range(1000):
            key = rng.choice(pool)
            value = rng.randrange(0, 20)
            store.insert(key, value)
            values[key] = value
            for prefix in [rng.choice(pool), "", "z", key]:
                self.assertEqual(store.sum(prefix),
                                 sum(v for k, v in values.items() if k.startswith(prefix)))

    def test_211_patterns_against_word_scan(self):
        cls = solution("211", "WordDictionary")
        store = cls()
        self.assertFalse(store.search("."))
        words = strings("ab", 4)
        for word in words + ["bad", "bag", "bad"]:
            store.add_word(word)
        patterns = strings("ab.", 5) + ["ba.", "b..s", "....", "z"]
        for pattern in patterns:
            expected = any(len(word) == len(pattern) and
                           all(p == "." or p == c for p, c in zip(pattern, word))
                           for word in words + ["bad", "bag"])
            self.assertEqual(store.search(pattern), expected, pattern)

    def test_421_all_pairs(self):
        solve = solution("421", "maximum_xor")
        self.assertEqual(solve([2, 5, 7]), 7)
        self.assertEqual(solve([]), 0)
        rng = random.Random(421)
        for _ in range(600):
            nums = [rng.randrange(256) for _ in range(rng.randrange(2, 15))]
            self.assertEqual(solve(nums), max(a ^ b for a, b in itertools.combinations(nums, 2)))
        self.assertEqual(solve([0, (1 << 31) - 1]), (1 << 31) - 1)
        self.assertEqual(solve([9, 9]), 0)

    def test_2707_exhaustive_covering_oracle(self):
        solve = solution("2707", "min_extra_char")
        self.assertEqual(solve("abxc", ["ab", "c"]), 1)
        rng = random.Random(2707)
        pool = strings("ab", 3)

        def oracle(s, dictionary, i=0):
            if i == len(s):
                return 0
            choices = [1 + oracle(s, dictionary, i + 1)]
            for word in dictionary:
                if s.startswith(word, i):
                    choices.append(oracle(s, dictionary, i + len(word)))
            return min(choices)

        for _ in range(400):
            s = "".join(rng.choices("abx", k=rng.randrange(9)))
            dictionary = rng.sample(pool, rng.randrange(9))
            self.assertEqual(solve(s, dictionary), oracle(s, dictionary), (s, dictionary))

    def test_2416_direct_prefix_count(self):
        solve = solution("2416", "sum_prefix_scores")
        self.assertEqual(solve(["ab", "ac", "ab"]), [5, 4, 5])
        self.assertEqual(solve([]), [])
        rng = random.Random(2416)
        pool = strings("abc", 4)
        for _ in range(600):
            words = rng.choices(pool, k=rng.randrange(15))
            expected = [sum(sum(other.startswith(word[:i]) for other in words)
                            for i in range(1, len(word) + 1)) for word in words]
            self.assertEqual(solve(words), expected)

    def test_212_separate_board_search(self):
        solve = solution("212", "find_words")
        board = [["a", "b"], ["c", "d"]]
        self.assertEqual(set(solve(board, ["a", "ab", "ac", "aba"])), {"a", "ab", "ac"})
        self.assertEqual(board, [["a", "b"], ["c", "d"]])
        self.assertEqual(solve([], ["a"]), [])
        rng = random.Random(212)
        pool = strings("ab", 4)
        for _ in range(500):
            board = [[rng.choice("ab") for _ in range(rng.randrange(1, 4))]
                     for _ in range(1)]
            board.extend([[rng.choice("ab") for _ in range(len(board[0]))]
                          for _ in range(rng.randrange(3))])
            before = [row[:] for row in board]
            words = rng.sample(pool, rng.randrange(len(pool) + 1))
            expected = {word for word in words if word_on_board(board, word)}
            actual = solve(board, words)
            self.assertEqual(len(actual), len(set(actual)))
            self.assertEqual(set(actual), expected, (before, words))
            self.assertEqual(board, before)

    def test_1707_filter_and_scan(self):
        solve = solution("1707", "maximize_xor")
        self.assertEqual(solve([1, 4, 6], [(2, 4), (3, 0)]), [6, -1])
        self.assertEqual(solve([], [(0, 0)]), [-1])
        rng = random.Random(1707)
        for _ in range(600):
            nums = [rng.randrange(128) for _ in range(rng.randrange(12))]
            queries = [(rng.randrange(128), rng.randrange(128)) for _ in range(rng.randrange(12))]
            expected = [max((x ^ n for n in nums if n <= limit), default=-1)
                        for x, limit in queries]
            before = nums[:], queries[:]
            self.assertEqual(solve(nums, queries), expected)
            self.assertEqual((nums, queries), before)
        self.assertEqual(solve([0, (1 << 31) - 1], [(1 << 30, (1 << 31) - 1)]),
                         [1 << 30])

    def test_336_all_ordered_pairs(self):
        solve = solution("336", "palindrome_pairs")
        words = ["ab", "ba", "a", ""]
        expected = {(i, j) for i, a in enumerate(words) for j, b in enumerate(words)
                    if i != j and a + b == (a + b)[::-1]}
        self.assertEqual(set(solve(words)), expected)
        pool = [""] + strings("ab", 3)
        for size in range(6):
            for group in itertools.combinations(pool, size):
                actual = solve(group)
                expected = {(i, j) for i, a in enumerate(group) for j, b in enumerate(group)
                            if i != j and a + b == (a + b)[::-1]}
                self.assertEqual(len(actual), len(set(actual)), group)
                self.assertEqual(set(actual), expected, group)


if __name__ == "__main__":
    unittest.main()
