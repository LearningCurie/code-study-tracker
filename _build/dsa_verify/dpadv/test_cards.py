"""Exercise the Python printed in every advanced-DP card against independent oracles."""

import itertools
import random
import re
import sys
import unittest
from collections import deque
from pathlib import Path

BUILD = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUILD))
from build_dsa_guide import CARD_HEADINGS, CARD_WORDS, Problems, load_module, parse_cards
import mdlite

SOURCE = BUILD / "dsa" / "26-dpadv.cards.md"
MODULE = BUILD / "dsa" / "26-dpadv.md"
NAMES = {
    "486": "first_player_can_tie", "337": "max_tree_robbery",
    "1986": "min_work_sessions", "1547": "min_cut_cost",
    "312": "max_burst_coins", "2246": "longest_distinct_adjacent_path",
    "834": "tree_distance_sums", "ac:dp_o": "count_matchings",
    "902": "count_allowed_numbers", "ac:dp_s": "count_digit_sum_multiples",
    "943": "shortest_superstring", "2376": "count_distinct_digit_numbers",
}
CARDS = parse_cards(SOURCE)
CODE = {}
for pid, card in CARDS.items():
    blocks = re.findall(r"```python\n(.*?)\n```", card["md"], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"{pid}: expected one Python block, got {len(blocks)}")
    namespace = {}
    exec(compile(blocks[0], f"{SOURCE.name}:{pid}", "exec"), namespace)
    CODE[pid] = namespace[NAMES[pid]]


def game_oracle(values, first=0, second=0, turn=0):
    if not values:
        return first >= second
    results = []
    for index in {0, len(values) - 1}:
        remaining = values[:index] + values[index + 1:]
        if turn == 0:
            results.append(game_oracle(remaining, first + values[index], second, 1))
        else:
            results.append(game_oracle(remaining, first, second + values[index], 0))
    return any(results) if turn == 0 else all(results)


class Node:
    def __init__(self, value):
        self.val = value
        self.left = self.right = None


def robbery_oracle(nodes, edges):
    best = 0
    for mask in range(1 << len(nodes)):
        if all(not (mask & (1 << a) and mask & (1 << b)) for a, b in edges):
            best = max(best, sum(node.val for i, node in enumerate(nodes) if mask & (1 << i)))
    return best


def sessions_oracle(tasks, capacity):
    if not tasks:
        return 0
    best = len(tasks)
    loads = []

    def assign(index):
        nonlocal best
        if len(loads) >= best:
            return
        if index == len(tasks):
            best = len(loads)
            return
        tried = set()
        for i in range(len(loads)):
            if loads[i] in tried or loads[i] + tasks[index] > capacity:
                continue
            tried.add(loads[i])
            loads[i] += tasks[index]
            assign(index + 1)
            loads[i] -= tasks[index]
        loads.append(tasks[index])
        assign(index + 1)
        loads.pop()

    assign(0)
    return best


def cuts_oracle(length, cuts):
    best = float("inf")
    for order in itertools.permutations(cuts):
        boundaries = [0, length]
        cost = 0
        for cut in order:
            cost += min(x for x in boundaries if x > cut) - max(x for x in boundaries if x < cut)
            boundaries.append(cut)
        best = min(best, cost)
    return best


def balloons_oracle(values):
    if not values:
        return 0
    outcomes = []
    for i, value in enumerate(values):
        left = values[i - 1] if i else 1
        right = values[i + 1] if i + 1 < len(values) else 1
        outcomes.append(left * value * right + balloons_oracle(values[:i] + values[i + 1:]))
    return max(outcomes)


def adjacency(n, edges):
    graph = [[] for _ in range(n)]
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    return graph


def distances(graph, start):
    dist = [-1] * len(graph)
    dist[start] = 0
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if dist[neighbor] == -1:
                dist[neighbor] = dist[node] + 1
                queue.append(neighbor)
    return dist


def longest_path_oracle(parent, labels):
    edges = [(node, parent[node]) for node in range(1, len(parent))]
    graph = adjacency(len(parent), edges)
    best = 1
    for start in range(len(parent)):
        queue = deque([(start, -1, 1)])
        while queue:
            node, previous, length = queue.popleft()
            best = max(best, length)
            for neighbor in graph[node]:
                if neighbor != previous and labels[node] != labels[neighbor]:
                    queue.append((neighbor, node, length + 1))
    return best


def arbitrary_parent_tree(n, rng):
    # Relabel an increasing-parent tree without moving the root: parents can exceed children.
    old_parent = [-1] + [rng.randrange(i) for i in range(1, n)]
    labels = list(range(1, n))
    rng.shuffle(labels)
    mapping = [0] + labels
    parent = [-1] * n
    for node in range(1, n):
        parent[mapping[node]] = mapping[old_parent[node]]
    return parent


def matching_oracle(matrix):
    return sum(all(matrix[row][col] for row, col in enumerate(order))
               for order in itertools.permutations(range(len(matrix))))


def shortest_length_oracle(words, alphabet):
    if not words:
        return 0
    for length in range(max(map(len, words)), sum(map(len, words)) + 1):
        for letters in itertools.product(alphabet, repeat=length):
            candidate = "".join(letters)
            if all(word in candidate for word in words):
                return length
    raise AssertionError("concatenation must be a superstring")


def unique_count_formula(bound):
    # Count by representation length and lexicographic first differing digit.
    text = str(bound)
    total = 0
    for length in range(1, len(text)):
        choices = 9
        for remaining in range(length - 1):
            choices *= 9 - remaining
        total += choices
    used = set()
    for i, ch in enumerate(text):
        for digit in range(1 if i == 0 else 0, int(ch)):
            if digit in used:
                continue
            available = 9 - i
            ways = 1
            for j in range(len(text) - i - 1):
                ways *= max(available - j, 0)
            total += ways
        digit = int(ch)
        if digit in used:
            return total
        used.add(digit)
    return total + 1


class TestCards(unittest.TestCase):
    def test_inventory_and_format(self):
        errors = []
        module = load_module(MODULE, errors)
        self.assertFalse(errors, errors)
        ids = {entry["id"] for entry in module["practice"]}
        self.assertEqual(ids, set(NAMES))
        self.assertEqual(ids, set(CARDS))
        problems = Problems()
        for pid, card in CARDS.items():
            with self.subTest(pid=pid):
                text = card["md"]
                headings = re.findall(r"(?m)^## .+$", text)
                self.assertEqual(headings, list(CARD_HEADINGS))
                self.assertIn("```steps\n", text)
                diff = problems.record(pid)[1] if pid.isdigit() else "M"
                self.assertGreaterEqual(mdlite.plain(text), CARD_WORDS[diff])

    def test_game_exhaustive(self):
        solve = CODE["486"]
        for n in range(1, 8):
            for values in itertools.product(range(3), repeat=n):
                self.assertEqual(solve(list(values)), game_oracle(values), values)
        self.assertFalse(solve([1, 5, 2]))
        self.assertTrue(solve([0, 0]))
        self.assertTrue(solve([10_000_000]))

    def test_robbery_subsets_and_depth(self):
        solve = CODE["337"]
        self.assertEqual(solve(None), 0)
        rng = random.Random(337)
        for n in range(1, 11):
            for _ in range(50):
                nodes = [Node(rng.randrange(8)) for _ in range(n)]
                edges = []
                slots = [(0, "left"), (0, "right")]
                for i in range(1, n):
                    p, side = slots.pop(rng.randrange(len(slots)))
                    setattr(nodes[p], side, nodes[i])
                    edges.append((p, i))
                    slots.extend([(i, "left"), (i, "right")])
                self.assertEqual(solve(nodes[0]), robbery_oracle(nodes, edges))
        root = Node(1)
        current = root
        for _ in range(10_999):
            current.left = Node(1)
            current = current.left
        self.assertEqual(solve(root), 5500)

    def test_sessions_against_bin_assignments(self):
        solve = CODE["1986"]
        rng = random.Random(1986)
        self.assertEqual(solve([], 3), 0)
        self.assertEqual(solve([1, 2, 3], 3), 2)
        self.assertEqual(solve([2, 2, 2], 3), 3)
        for n in range(1, 10):
            for _ in range(100):
                capacity = rng.randrange(1, 9)
                tasks = [rng.randrange(1, capacity + 1) for _ in range(n)]
                self.assertEqual(solve(tasks, capacity), sessions_oracle(tasks, capacity), (tasks, capacity))
        self.assertEqual(solve([1] * 14, 3), 5)

    def test_cuts_permutations(self):
        solve = CODE["1547"]
        for length in range(2, 9):
            for count in range(min(5, length - 1) + 1):
                for cuts in itertools.combinations(range(1, length), count):
                    supplied = list(reversed(cuts))
                    self.assertEqual(solve(length, supplied), cuts_oracle(length, cuts), (length, cuts))
                    self.assertEqual(supplied, list(reversed(cuts)))
        self.assertEqual(solve(7, [1, 3]), 10)
        self.assertEqual(solve(7, [1, 3, 4, 5]), 16)

    def test_balloons_simulation(self):
        solve = CODE["312"]
        for n in range(7):
            for values in itertools.product(range(3), repeat=n):
                self.assertEqual(solve(values), balloons_oracle(values), values)
        self.assertEqual(solve([2, 3]), 9)
        self.assertEqual(solve([3, 1, 5, 8]), 167)

    def test_longest_path_against_bfs(self):
        solve = CODE["2246"]
        rng = random.Random(2246)
        self.assertEqual(solve([-1], "a"), 1)
        self.assertEqual(solve([-1, 0, 0, 1], "abca"), 4)
        self.assertEqual(solve([-1, 2, 0], "aba"), 2)
        for n in range(1, 30):
            for _ in range(40):
                parent = arbitrary_parent_tree(n, rng)
                labels = "".join(rng.choice("abc") for _ in range(n))
                self.assertEqual(solve(parent, labels), longest_path_oracle(parent, labels), (parent, labels))
        n = 100_000
        self.assertEqual(solve([-1] + list(range(n - 1)), "ab" * (n // 2)), n)
        self.assertEqual(solve([-1] + [0] * (n - 1), "a" * n), 1)

    def test_distance_sums_against_bfs(self):
        solve = CODE["834"]
        rng = random.Random(834)
        self.assertEqual(solve(1, []), [0])
        self.assertEqual(solve(3, [(0, 1), (1, 2)]), [3, 2, 3])
        for n in range(1, 40):
            for _ in range(30):
                parent = arbitrary_parent_tree(n, rng)
                edges = [(i, parent[i]) for i in range(1, n)]
                rng.shuffle(edges)
                graph = adjacency(n, edges)
                expected = [sum(distances(graph, i)) for i in range(n)]
                self.assertEqual(solve(n, edges), expected, edges)
        n = 30_000
        result = solve(n, [(i, i + 1) for i in range(n - 1)])
        self.assertEqual(result[0], n * (n - 1) // 2)
        self.assertEqual(result[-1], result[0])
        self.assertEqual(result[n // 2], (n // 2) * (n // 2 + 1) // 2 + (n - 1 - n // 2) * (n - n // 2) // 2)

    def test_matching_permutations(self):
        solve = CODE["ac:dp_o"]
        self.assertEqual(solve([]), 1)
        self.assertEqual(solve([[1, 1], [1, 1]]), 2)
        for bits in range(1 << 9):
            matrix = [[(bits >> (r * 3 + c)) & 1 for c in range(3)] for r in range(3)]
            self.assertEqual(solve(matrix), matching_oracle(matrix), matrix)
        rng = random.Random(42)
        for n in range(1, 8):
            for _ in range(40):
                matrix = [[rng.randrange(2) for _ in range(n)] for _ in range(n)]
                self.assertEqual(solve(matrix), matching_oracle(matrix), matrix)
        self.assertEqual(solve([[1] * 13 for _ in range(13)]), 6227020800 % 1_000_000_007)

    def test_allowed_digits_scan(self):
        solve = CODE["902"]
        self.assertEqual(solve(["1", "3"], 31), 5)
        self.assertEqual(solve([], 100), 0)
        self.assertEqual(solve(["1"], 0), 0)
        digits = "123456789"
        for mask in range(1, 1 << 9):
            allowed = [digits[i] for i in range(9) if mask & (1 << i)]
            running = 0
            for bound in range(1, 201):
                running += all(ch in allowed for ch in str(bound))
                self.assertEqual(solve(allowed, bound), running, (allowed, bound))
        self.assertEqual(solve(list("123456789"), 1_000_000_000), sum(9 ** i for i in range(1, 10)))

    def test_digit_sum_scan_and_long_bound(self):
        solve = CODE["ac:dp_s"]
        self.assertEqual(solve("12", 3), 4)
        self.assertEqual(solve("20", 2), 10)
        for divisor in range(1, 21):
            running = 0
            for bound in range(1, 501):
                running += sum(map(int, str(bound))) % divisor == 0
                self.assertEqual(solve(str(bound), divisor), running, (bound, divisor))
        long_bound = "9" * 10_000
        self.assertEqual(solve(long_bound, 1), (pow(10, 10_000, 1_000_000_007) - 1) % 1_000_000_007)
        self.assertEqual(solve("0", 7), 0)

    def test_superstring_exhaustive_strings(self):
        solve = CODE["943"]
        pool = ["a", "b", "aa", "ab", "ba", "bb", "aba", "bab"]
        for count in range(1, 5):
            for words in itertools.combinations_with_replacement(pool, count):
                answer = solve(words)
                self.assertTrue(all(word in answer for word in words), (words, answer))
                self.assertEqual(len(answer), shortest_length_oracle(words, "ab"), (words, answer))
        self.assertEqual(solve([]), "")
        self.assertEqual(solve(["ab", "ab", "b"]), "ab")
        result = solve(["ab", "bc", "ca"])
        self.assertEqual(len(result), 4)
        self.assertTrue(all(word in result for word in ["ab", "bc", "ca"]))
        no_overlap = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
        answer = solve(no_overlap)
        self.assertEqual(len(answer), 12)
        self.assertTrue(all(word in answer for word in no_overlap))

    def test_unique_digits_scan_and_combinatorics(self):
        solve = CODE["2376"]
        self.assertEqual(solve(0), 0)
        self.assertEqual(solve(20), 19)
        count = 0
        for bound in range(1, 5001):
            text = str(bound)
            count += len(set(text)) == len(text)
            self.assertEqual(solve(bound), count, bound)
        for bound in [9, 10, 99, 100, 101, 1000, 987654321, 1_000_000_000, 2_000_000_000, 9_876_543_210]:
            self.assertEqual(solve(bound), unique_count_formula(bound), bound)


if __name__ == "__main__":
    unittest.main()
