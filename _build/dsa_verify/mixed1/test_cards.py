import functools
import itertools
import os
import random
import re
import sys
import unittest
from collections import Counter, deque
from pathlib import Path

BUILD = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUILD))
import build_dsa_guide as guide

SOURCE = Path(os.environ.get('DSA_MIXED_CARDS', BUILD / 'dsa' / '32-mixed.cards.md'))
IDS = '219 1679 930 438 189 1657 1004 523 16 2125 946 240 1944 328 2300 1019 1248 1283 2966 1209'.split()
NAMES = 'contains_nearby_duplicate max_operations num_subarrays_with_sum find_anagrams rotate close_strings longest_ones check_subarray_sum three_sum_closest number_of_beams validate_stack_sequences search_matrix can_see_persons_count odd_even_list successful_pairs next_larger_nodes number_of_nice_subarrays smallest_divisor divide_array remove_duplicates'.split()
CARDS = guide.parse_cards(SOURCE)


def solution(pid):
    section = CARDS[pid]['md'].split('## Code', 1)[1].split('## Complexity', 1)[0]
    blocks = re.findall(r'```python\n(.*?)\n```', section, re.S)
    if len(blocks) != 1:
        raise AssertionError(f'{pid}: expected exactly one displayed solution block')
    scope = {}
    exec(compile(blocks[0], f'card-{pid}', 'exec'), scope)
    return scope[NAMES[IDS.index(pid)]]


def arrays(alphabet, max_length):
    for n in range(max_length + 1):
        yield from itertools.product(alphabet, repeat=n)


class Node:
    def __init__(self, value, next=None):
        self.val, self.next = value, next


def linked(values):
    nodes = [Node(x) for x in values]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    return (nodes[0] if nodes else None), nodes


class TestMixedCards(unittest.TestCase):
    def test_metadata_and_rendering(self):
        catalog = guide.Problems()
        for pid in IDS:
            with self.subTest(pid=pid):
                self.assertIn(pid, CARDS)
                problems = []
                visible, hidden, words = guide.card_parts(pid, CARDS[pid], catalog.record(pid)[1], str(SOURCE), problems)
                self.assertFalse(problems, problems)
                self.assertGreaterEqual(words, guide.CARD_WORDS[catalog.record(pid)[1]])
                self.assertIn('The problem', visible)
                self.assertNotIn('Brute force', visible)
                self.assertNotIn('<code class="language-python"', visible)
                self.assertIn('Brute force', hidden)
                solution(pid)

    def test_219(self):
        f = solution('219')
        for a in arrays(range(3), 6):
            for k in range(8):
                expected = any(a[i] == a[j] and j-i <= k for i in range(len(a)) for j in range(i+1, len(a)))
                self.assertEqual(f(a, k), expected, (a, k))

    def test_1679(self):
        f = solution('1679')
        @functools.lru_cache(None)
        def brute(a, k):
            return max((1 + brute(a[:i] + a[i+1:j] + a[j+1:], k)
                        for i in range(len(a)) for j in range(i+1, len(a)) if a[i] + a[j] == k), default=0)
        for a in arrays(range(4), 6):
            for k in range(7):
                self.assertEqual(f(a, k), brute(a, k), (a, k))

    def test_930(self):
        f = solution('930')
        for a in arrays(range(2), 8):
            for goal in range(5):
                expected = sum(sum(a[i:j]) == goal for i in range(len(a)) for j in range(i+1, len(a)+1))
                self.assertEqual(f(a, goal), expected, (a, goal))

    def test_438(self):
        f = solution('438')
        for a in arrays('ab', 7):
            s = ''.join(a)
            for p in (''.join(t) for t in arrays('ab', 4) if t):
                expected = [i for i in range(len(s)-len(p)+1) if sorted(s[i:i+len(p)]) == sorted(p)]
                self.assertEqual(f(s, p), expected, (s, p))

    def test_189(self):
        f = solution('189')
        for a in arrays(range(3), 5):
            for k in range(12):
                value = list(a)
                shifted = k % len(a) if a else 0
                expected = list(a[-shifted:] + a[:-shifted]) if shifted else list(a)
                self.assertIsNone(f(value, k))
                self.assertEqual(value, expected, (a, k))

    def test_1657(self):
        f = solution('1657')
        for n in range(1, 5):
            words = [''.join(t) for t in itertools.product('abc', repeat=n)]
            for start in words:
                seen, q = {start}, deque([start])
                while q:
                    word = q.popleft()
                    neighbours = []
                    for i in range(n):
                        for j in range(i+1, n):
                            chars = list(word)
                            chars[i], chars[j] = chars[j], chars[i]
                            neighbours.append(''.join(chars))
                    for x, y in itertools.combinations(set(word), 2):
                        neighbours.append(''.join(y if ch == x else x if ch == y else ch for ch in word))
                    for neighbour in neighbours:
                        if neighbour not in seen:
                            seen.add(neighbour)
                            q.append(neighbour)
                for target in words:
                    self.assertEqual(f(start, target), target in seen, (start, target))
        self.assertFalse(f('a', 'aa'))
        self.assertTrue(f('', ''))

    def test_1004(self):
        f = solution('1004')
        for a in arrays(range(2), 8):
            for k in range(4):
                expected = max((j-i for i in range(len(a)+1) for j in range(i, len(a)+1) if a[i:j].count(0) <= k), default=0)
                self.assertEqual(f(a, k), expected, (a, k))

    def test_523(self):
        f = solution('523')
        for a in arrays(range(3), 6):
            for k in range(1, 7):
                expected = any(sum(a[i:j]) % k == 0 for i in range(len(a)) for j in range(i+2, len(a)+1))
                self.assertEqual(f(a, k), expected, (a, k))
        self.assertFalse(f([6], 6))
        self.assertTrue(f([0, 0], 10**9))

    def test_16(self):
        f = solution('16')
        for a in arrays(range(-2, 3), 5):
            if len(a) < 3:
                continue
            for target in (-4, -1, 0, 3, 5):
                sums = [sum(t) for t in itertools.combinations(a, 3)]
                answer = f(a, target)
                self.assertIn(answer, sums)
                self.assertEqual(abs(answer-target), min(abs(x-target) for x in sums), (a, target))

    def test_2125(self):
        f = solution('2125')
        rows = [''.join(x) for x in itertools.product('01', repeat=3)]
        for bank in arrays(rows, 4):
            devices = [(i, j) for i, row in enumerate(bank) for j, ch in enumerate(row) if ch == '1']
            expected = sum(all('1' not in bank[r] for r in range(a[0]+1, b[0]))
                           for a, b in itertools.combinations(devices, 2) if a[0] < b[0])
            self.assertEqual(f(bank), expected, bank)

    def test_946(self):
        f = solution('946')
        for n in range(7):
            pushed = tuple(range(n))
            @functools.lru_cache(None)
            def possible(i, j, stack, popped):
                if j == n:
                    return i == n
                return ((i < n and possible(i+1, j, stack + (pushed[i],), popped)) or
                        (bool(stack) and stack[-1] == popped[j] and possible(i, j+1, stack[:-1], popped)))
            for popped in itertools.permutations(pushed):
                self.assertEqual(f(pushed, popped), bool(possible(0, 0, (), popped)), popped)
        self.assertFalse(f([1], []))
        self.assertFalse(f([1, 2], [1, 1]))

    def test_240(self):
        f = solution('240')
        rng = random.Random(240)
        for r in range(1, 8):
            for c in range(1, 8):
                for _ in range(30):
                    matrix = [[0]*c for _ in range(r)]
                    for i in range(r):
                        for j in range(c):
                            matrix[i][j] = max(matrix[i-1][j] if i else -5, matrix[i][j-1] if j else -5) + rng.randrange(3)
                    for target in range(-6, 12):
                        self.assertEqual(f(matrix, target), any(target in row for row in matrix))
        self.assertFalse(f([], 0))
        self.assertFalse(f([[]], 0))

    def test_1944(self):
        f = solution('1944')
        for n in range(8):
            for a in itertools.permutations(range(1, n+1)):
                expected = [sum(all(a[t] < min(a[i], a[j]) for t in range(i+1, j))
                                for j in range(i+1, n)) for i in range(n)]
                self.assertEqual(f(a), expected, a)

    def test_328(self):
        f = solution('328')
        for n in range(30):
            head, nodes = linked([i % 3 for i in range(n)])
            current = f(head)
            seen = []
            while current is not None and len(seen) <= n:
                seen.append(current)
                current = current.next
            self.assertIsNone(current, 'cycle or extra nodes')
            self.assertEqual(seen, nodes[::2] + nodes[1::2])

    def test_2300(self):
        f = solution('2300')
        rng = random.Random(2300)
        for _ in range(3000):
            spells = [rng.randrange(1, 20) for _ in range(rng.randrange(9))]
            potions = [rng.randrange(1, 20) for _ in range(rng.randrange(9))]
            success = rng.randrange(1, 400)
            before = potions[:]
            self.assertEqual(f(spells, potions, success), [sum(s*p >= success for p in potions) for s in spells])
            self.assertEqual(potions, before)
        self.assertEqual(f([10**18], [10**18-1, 10**18], 10**36), [1])

    def test_1019(self):
        f = solution('1019')
        for a in arrays(range(1, 4), 7):
            head, nodes = linked(a)
            expected = [next((x for x in a[i+1:] if x > value), 0) for i, value in enumerate(a)]
            self.assertEqual(f(head), expected, a)
            self.assertEqual([node.next for node in nodes], nodes[1:] + ([None] if nodes else []))

    def test_1248(self):
        f = solution('1248')
        for a in arrays((-2, -1, 0, 1), 6):
            for k in range(4):
                expected = sum(sum(x % 2 for x in a[i:j]) == k for i in range(len(a)) for j in range(i+1, len(a)+1))
                self.assertEqual(f(a, k), expected, (a, k))

    def test_1283(self):
        f = solution('1283')
        for a in arrays(range(1, 6), 5):
            if not a:
                continue
            for threshold in range(len(a), sum(a)+2):
                expected = next(d for d in range(1, max(a)+1)
                                if sum(q + bool(r) for q, r in (divmod(x, d) for x in a)) <= threshold)
                self.assertEqual(f(a, threshold), expected, (a, threshold))
        self.assertEqual(f([10**18], 1), 10**18)

    def test_2966(self):
        f = solution('2966')
        @functools.lru_cache(None)
        def possible(a, k):
            if not a:
                return True
            return any(max(group)-min(group) <= k and possible(tuple(a[t] for t in range(len(a)) if t not in indices), k)
                       for i, j in itertools.combinations(range(1, len(a)), 2)
                       for indices in [(0, i, j)] for group in [[a[t] for t in indices]])
        rng = random.Random(2966)
        inputs = list(arrays(range(4), 3))
        inputs += [tuple(rng.randrange(8) for _ in range(n)) for n in (6, 9, 12) for _ in range(500)]
        for a in inputs:
            if len(a) % 3 or not a:
                continue
            for k in range(4):
                result = f(a, k)
                self.assertEqual(bool(result), possible(tuple(sorted(a)), k), (a, k, result))
                if result:
                    self.assertEqual(Counter(itertools.chain.from_iterable(result)), Counter(a))
                    self.assertTrue(all(len(g) == 3 and max(g)-min(g) <= k for g in result))

    def test_1209(self):
        f = solution('1209')
        def brute(s, k):
            while True:
                for i in range(len(s)-k+1):
                    if len(set(s[i:i+k])) == 1:
                        s = s[:i] + s[i+k:]
                        break
                else:
                    return s
        for a in arrays('abc', 8):
            s = ''.join(a)
            for k in range(2, 5):
                self.assertEqual(f(s, k), brute(s, k), (s, k))
        self.assertEqual(f('deeedbbcccbdaa', 3), 'aa')


if __name__ == '__main__':
    unittest.main()
