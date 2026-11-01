"""Exercise the displayed mixed-review implementations, not copied solutions."""
import itertools
import math
import os
import random
import re
import sys
import unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

BUILD = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('DSA_MIXED_CARDS', BUILD / 'dsa' / '32-mixed.cards.md'))
sys.path.insert(0, str(BUILD))
import build_dsa_guide as guide

IDS = '1035 1594 93 2140 375 646 712 1653 1140 688 1442 1823 1352 2101 382 1856 2349 2402 1964 1146'.split()
CARDS = guide.parse_cards(SOURCE)


def implementation(pid, name):
    section = CARDS[pid]['md'].split('## Code', 1)[1].split('## Complexity', 1)[0]
    blocks = re.findall(r'```python\n(.*?)\n```', section, re.S)
    if len(blocks) != 1:
        raise AssertionError(f'{pid}: expected exactly one displayed Python block')
    namespace = {}
    exec(compile(blocks[0], f'card-{pid}', 'exec'), namespace)
    return namespace[name]


def subsequences(items):
    return [tuple(items[i] for i in range(len(items)) if mask >> i & 1)
            for mask in range(1 << len(items))]


class MixedCards(unittest.TestCase):
    def test_format_and_metadata(self):
        catalog = guide.Problems()
        errors = []
        for pid in IDS:
            record = catalog.record(pid)
            visible, hidden, _ = guide.card_parts(pid, CARDS[pid], record[1], str(SOURCE), errors)
            self.assertTrue(visible and hidden, pid)
        self.assertEqual(errors, [])

    def test_1035(self):
        f = implementation('1035', 'uncrossed_lines')
        rng = random.Random(1035)
        for _ in range(300):
            a = [rng.randrange(4) for _ in range(rng.randrange(8))]
            b = [rng.randrange(4) for _ in range(rng.randrange(8))]
            common = set(subsequences(a)) & set(subsequences(b))
            self.assertEqual(f(a, b), max(map(len, common)))
        self.assertEqual(f([7] * 500, [7] * 500), 500)

    def test_1594(self):
        f = implementation('1594', 'max_product_path')
        rng = random.Random(1594)
        for _ in range(250):
            rows, cols = rng.randint(1, 4), rng.randint(1, 4)
            grid = [[rng.randint(-4, 4) for _ in range(cols)] for _ in range(rows)]
            def paths(r, c, product):
                product *= grid[r][c]
                if r == rows - 1 and c == cols - 1:
                    return [product]
                result = []
                if r + 1 < rows: result += paths(r + 1, c, product)
                if c + 1 < cols: result += paths(r, c + 1, product)
                return result
            best = max(paths(0, 0, 1))
            self.assertEqual(f(grid), best % 1_000_000_007 if best >= 0 else -1)
        self.assertEqual(f([[-4] * 15 for _ in range(15)]), -1)
        self.assertEqual(f([[0]]), 0)
        self.assertEqual(f([[4] * 15 for _ in range(15)]), pow(4, 29, 1_000_000_007))

    def test_93(self):
        f = implementation('93', 'restore_ip_addresses')
        rng = random.Random(93)
        cases = ['0000', '25525511135', '1111', '123', '1' * 13, '101023']
        cases += [''.join(str(rng.randrange(10)) for _ in range(rng.randrange(1, 15))) for _ in range(500)]
        for s in cases:
            expected = []
            for cuts in itertools.combinations(range(1, len(s)), 3):
                positions = (0,) + cuts + (len(s),)
                parts = [s[positions[i]:positions[i + 1]] for i in range(4)]
                if all(len(p) <= 3 and (len(p) == 1 or p[0] != '0') and int(p) <= 255 for p in parts):
                    expected.append('.'.join(parts))
            actual = f(s)
            self.assertEqual(sorted(actual), sorted(expected), s)
            self.assertEqual(len(actual), len(set(actual)))

    def test_2140(self):
        f = implementation('2140', 'most_points')
        rng = random.Random(2140)
        for _ in range(500):
            questions = [[rng.randint(1, 20), rng.randint(1, 7)] for _ in range(rng.randint(1, 10))]
            def search(i):
                if i >= len(questions): return 0
                return max(search(i + 1), questions[i][0] + search(i + questions[i][1] + 1))
            self.assertEqual(f(questions), search(0))
        self.assertEqual(f([[1, 1]] * 100000), 50000)

    def test_375(self):
        f = implementation('375', 'guaranteed_guess_cost')
        # Enumerate strategies as sets of cost vectors, one coordinate per hidden number.
        def strategies(lo, hi):
            if lo > hi: return [()]
            if lo == hi: return [(0,)]
            vectors = []
            for guess in range(lo, hi + 1):
                for left in strategies(lo, guess - 1):
                    for right in strategies(guess + 1, hi):
                        vectors.append(tuple(x + guess for x in left) + (0,) + tuple(x + guess for x in right))
            return vectors
        for n in range(1, 8):
            self.assertEqual(f(n), min(max(v) for v in strategies(1, n)))
        self.assertEqual(f(10), 16)

    def test_646(self):
        f = implementation('646', 'longest_pair_chain')
        rng = random.Random(646)
        for _ in range(350):
            pairs = []
            for _ in range(rng.randrange(9)):
                x, y = sorted(rng.sample(range(-6, 8), 2))
                pairs.append((x, y))
            # Every valid chain has increasing starts, so sorted subsets suffice.
            expected = 0
            for subset in subsequences(sorted(pairs)):
                if all(a[1] < b[0] for a, b in zip(subset, subset[1:])):
                    expected = max(expected, len(subset))
            self.assertEqual(f(pairs), expected)
        self.assertEqual(f([[1, 2], [2, 3], [3, 4]]), 2)

    def test_712(self):
        f = implementation('712', 'minimum_delete_sum')
        rng = random.Random(712)
        for _ in range(400):
            a = ''.join(rng.choice('abc') for _ in range(rng.randrange(8)))
            b = ''.join(rng.choice('abc') for _ in range(rng.randrange(8)))
            common = set(subsequences(a)) & set(subsequences(b))
            expected = sum(map(ord, a + b)) - 2 * max(sum(map(ord, s)) for s in common)
            self.assertEqual(f(a, b), expected)
        self.assertEqual(f('sea', 'eat'), 231)

    def test_1653(self):
        f = implementation('1653', 'minimum_balanced_deletions')
        for n in range(11):
            for chars in itertools.product('ab', repeat=n):
                s = ''.join(chars)
                expected = min(s[:i].count('b') + s[i:].count('a') for i in range(n + 1))
                self.assertEqual(f(s), expected)
        self.assertEqual(f('ba' * 50000), 50000)

    def test_1140(self):
        f = implementation('1140', 'stone_game_ii')
        rng = random.Random(1140)
        for _ in range(250):
            piles = [rng.randint(1, 9) for _ in range(rng.randint(1, 9))]
            def game(i, m, turn):
                if i == len(piles): return 0
                choices = []
                for x in range(1, min(2*m, len(piles)-i) + 1):
                    choices.append((sum(piles[i:i+x]) if turn == 0 else 0) + game(i+x, max(m,x), 1-turn))
                return (max if turn == 0 else min)(choices)
            self.assertEqual(f(piles), game(0, 1, 0))
        self.assertEqual(f([2, 7, 9, 4, 4]), 10)
        self.assertGreater(f([1] * 100), 0)

    def test_688(self):
        f = implementation('688', 'knight_probability')
        moves = [(a, b) for a in (-2, -1, 1, 2) for b in (-2, -1, 1, 2) if abs(a) != abs(b)]
        for n in range(1, 5):
            for row in range(n):
                for col in range(n):
                    for k in range(4):
                        survivors = 0
                        for seq in itertools.product(moves, repeat=k):
                            r, c = row, col
                            for dr, dc in seq:
                                r, c = r + dr, c + dc
                                if not (0 <= r < n and 0 <= c < n): break
                            else: survivors += 1
                        self.assertAlmostEqual(f(n, k, row, col), survivors / 8**k)
        self.assertEqual(f(1, 0, 0, 0), 1.0)

    def test_1442(self):
        f = implementation('1442', 'count_xor_triplets')
        rng = random.Random(1442)
        for _ in range(500):
            arr = [rng.randrange(8) for _ in range(rng.randint(1, 10))]
            expected = 0
            for i in range(len(arr)):
                for j in range(i + 1, len(arr)):
                    for k in range(j, len(arr)):
                        a = b = 0
                        for x in arr[i:j]: a ^= x
                        for x in arr[j:k+1]: b ^= x
                        expected += a == b
            self.assertEqual(f(arr), expected)
        self.assertEqual(f([2, 2, 2]), 2)

    def test_1823(self):
        f = implementation('1823', 'circular_winner')
        for n in range(1, 60):
            for k in range(1, 70):
                circle = list(range(1, n + 1))
                pos = 0
                while len(circle) > 1:
                    pos = (pos + k - 1) % len(circle)
                    circle.pop(pos)
                self.assertEqual(f(n, k), circle[0])
        self.assertEqual(f(500, 1), 500)

    def test_1352(self):
        cls = implementation('1352', 'ProductOfNumbers')
        rng = random.Random(1352)
        for _ in range(100):
            obj, values = cls(), []
            for _ in range(150):
                if not values or rng.random() < 0.65:
                    value = rng.randrange(6)
                    values.append(value)
                    obj.add(value)
                else:
                    k = rng.randint(1, len(values))
                    self.assertEqual(obj.getProduct(k), math.prod(values[-k:]))
        obj = cls()
        for x in [3, 0, 0, 2, 5]: obj.add(x)
        self.assertEqual([obj.getProduct(k) for k in range(1, 6)], [5, 10, 0, 0, 0])

    def test_2101(self):
        f = implementation('2101', 'maximum_detonation')
        rng = random.Random(2101)
        for _ in range(300):
            bombs = [(rng.randint(-5, 5), rng.randint(-5, 5), rng.randint(1, 6))
                     for _ in range(rng.randint(1, 9))]
            maximum = 0
            for start in range(len(bombs)):
                exploded = {start}
                while True:
                    new = {j for i in exploded for j, (x, y, _) in enumerate(bombs)
                           if (x-bombs[i][0])**2 + (y-bombs[i][1])**2 <= bombs[i][2]**2}
                    if new <= exploded: break
                    exploded |= new
                maximum = max(maximum, len(exploded))
            self.assertEqual(f(bombs), maximum)
        self.assertEqual(f([[0, 0, 3], [3, 0, 1], [4, 0, 1]]), 3)

    def test_382(self):
        cls = implementation('382', 'RandomNode')
        class Node:
            def __init__(self, value, next=None): self.val, self.next = value, next
        head = None
        for x in reversed(range(4)): head = Node(x, head)
        counts = [0] * 4
        # All equally likely random integer sequences: 1 * 2 * 3 * 4 outcomes.
        for draws in itertools.product(range(1), range(2), range(3), range(4)):
            with patch('random.randrange', side_effect=draws) as rand:
                result = cls(head).getRandom()
                counts[result] += 1
                self.assertEqual([call.args[0] for call in rand.call_args_list], [1, 2, 3, 4])
        self.assertEqual(counts, [6] * 4)
        self.assertEqual(cls(Node(42)).getRandom(), 42)
        head = Node(5, Node(5, Node(8)))
        results = []
        for draws in itertools.product(range(1), range(2), range(3)):
            with patch('random.randrange', side_effect=draws): results.append(cls(head).getRandom())
        self.assertEqual(results.count(5), 4)
        self.assertEqual(results.count(8), 2)

    def test_1856(self):
        f = implementation('1856', 'max_sum_min_product')
        rng = random.Random(1856)
        for _ in range(600):
            arr = [rng.randint(1, 9) for _ in range(rng.randint(1, 12))]
            expected = max(min(arr[i:j]) * sum(arr[i:j]) for i in range(len(arr)) for j in range(i+1, len(arr)+1))
            self.assertEqual(f(arr), expected % 1_000_000_007)
        self.assertEqual(f([9000000] * 100000), (9000000**2 * 100000) % 1_000_000_007)
        self.assertEqual(f([2, 2, 2]), 12)

    def test_2349(self):
        cls = implementation('2349', 'NumberContainers')
        rng = random.Random(2349)
        for _ in range(100):
            obj = cls()
            reference = {}
            for _ in range(250):
                if rng.random() < .7:
                    index, number = rng.randrange(1, 20), rng.randrange(1, 7)
                    reference[index] = number
                    obj.change(index, number)
                else:
                    number = rng.randrange(1, 9)
                    expected = min((i for i, val in reference.items() if val == number), default=-1)
                    self.assertEqual(obj.find(number), expected)
        obj = cls()
        for value in [10, 20, 10, 20]: obj.change(1, value)
        self.assertEqual(obj.find(10), -1)
        self.assertEqual(obj.find(20), 1)

    def test_2402(self):
        f = implementation('2402', 'most_booked')
        rng = random.Random(2402)
        for _ in range(1000):
            rooms = rng.randint(1, 6)
            starts = rng.sample(range(30), rng.randint(1, 15))
            meetings = [[s, s + rng.randint(1, 15)] for s in starts]
            available, counts = [0] * rooms, [0] * rooms
            for start, end in sorted(meetings):
                free = [r for r in range(rooms) if available[r] <= start]
                room = min(free) if free else min(range(rooms), key=lambda r: (available[r], r))
                available[room] = max(start, available[room]) + end - start
                counts[room] += 1
            expected = min(range(rooms), key=lambda r: (-counts[r], r))
            self.assertEqual(f(rooms, meetings), expected, (rooms, meetings))
        self.assertEqual(f(2, [[0, 10], [1, 5], [2, 7], [3, 4]]), 0)
        self.assertEqual(f(2, [[0, 2], [1, 2], [2, 3]]), 0)
        self.assertEqual(f(1, [[i, i+500000] for i in range(1000)]), 0)

    def test_1964(self):
        f = implementation('1964', 'longest_obstacle_course')
        rng = random.Random(1964)
        for _ in range(800):
            arr = [rng.randint(1, 8) for _ in range(rng.randrange(35))]
            dp = []
            for i, value in enumerate(arr):
                dp.append(1 + max((dp[j] for j in range(i) if arr[j] <= value), default=0))
            self.assertEqual(f(arr), dp)
        self.assertEqual(f([7] * 100000), list(range(1, 100001)))
        self.assertEqual(f([3, 2, 1]), [1, 1, 1])

    def test_1146(self):
        cls = implementation('1146', 'SnapshotArray')
        rng = random.Random(1146)
        for _ in range(100):
            length = rng.randint(1, 12)
            obj, current, snapshots = cls(length), [0] * length, []
            for _ in range(250):
                action = rng.randrange(3)
                if action == 0:
                    index, value = rng.randrange(length), rng.randrange(100)
                    obj.set(index, value)
                    current[index] = value
                elif action == 1 or not snapshots:
                    self.assertEqual(obj.snap(), len(snapshots))
                    snapshots.append(current[:])
                else:
                    index, version = rng.randrange(length), rng.randrange(len(snapshots))
                    self.assertEqual(obj.get(index, version), snapshots[version][index])
        obj = cls(1)
        obj.set(0, 5); obj.set(0, 6)
        self.assertEqual(obj.snap(), 0)
        self.assertEqual(obj.snap(), 1)
        obj.set(0, 7)
        self.assertEqual(obj.get(0, 0), 6)
        self.assertEqual(obj.get(0, 1), 6)


if __name__ == '__main__':
    unittest.main(verbosity=2)
