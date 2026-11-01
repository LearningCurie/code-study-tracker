"""Test the actual mixed-card code. Set DSA_MIXED_CARDS while authoring."""

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

IDS = "572 692 1288 103 1029 1233 1382 1353 695 2316 1466 851 542 1786 909 2492 1882 2092 279 40".split()
CARD_PATH = Path(os.environ.get("DSA_MIXED_CARDS", BUILD / "dsa" / "32-mixed.cards.md"))
CARDS = guide.parse_cards(CARD_PATH)


def load(pid, name):
    blocks = re.findall(r"```python\n(.*?)\n```", CARDS[pid]["md"], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"{pid}: expected one displayed Python block")
    namespace = {}
    exec(compile(blocks[0], f"{CARD_PATH} card {pid}", "exec"), namespace)
    return namespace[name]


class Node:
    def __init__(self, val, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def random_tree(rng, n):
    if not n:
        return None
    left = rng.randrange(n)
    return Node(rng.randrange(3), random_tree(rng, left), random_tree(rng, n - 1 - left))


def all_nodes(root):
    if root is None:
        return []
    return [root] + all_nodes(root.left) + all_nodes(root.right)


def insert_bst(root, value):
    if root is None:
        return Node(value)
    if value < root.val:
        root.left = insert_bst(root.left, value)
    else:
        root.right = insert_bst(root.right, value)
    return root


def graph_reach(n, edges):
    reach = [[i == j for j in range(n)] for i in range(n)]
    for u, v in edges:
        reach[u][v] = reach[v][u] = True
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] |= reach[i][k] and reach[k][j]
    return reach


class Cards(unittest.TestCase):
    def setUp(self):
        self.r = random.Random(20261101)

    def test_structure(self):
        p = guide.Problems()
        issues = []
        for pid in IDS:
            self.assertIn(pid, CARDS)
            visible, hidden, _ = guide.card_parts(pid, CARDS[pid], p.record(pid)[1], CARD_PATH.name, issues)
            self.assertNotIn("Brute force", visible)
            self.assertIn("Brute force", hidden)
        self.assertEqual(issues, [])

    def test_572(self):
        f = load("572", "is_subtree")

        def equal(a, b):
            if a is None or b is None:
                return a is b
            return a.val == b.val and equal(a.left, b.left) and equal(a.right, b.right)

        for _ in range(250):
            root = random_tree(self.r, self.r.randrange(12))
            nodes = all_nodes(root)
            sub = self.r.choice(nodes) if nodes and self.r.randrange(2) else random_tree(self.r, self.r.randrange(6))
            self.assertEqual(f(root, sub), sub is None or any(equal(node, sub) for node in nodes))
        self.assertFalse(f(Node(4, Node(4)), Node(4, None, Node(4))))
        self.assertFalse(f(Node(12), Node(2)))
        self.assertTrue(f(Node(-10000, Node(10000)), Node(10000)))
        root = Node(0)
        for _ in range(2500):
            root = Node(0, root)
        self.assertTrue(f(root, Node(0)))

    def test_692(self):
        f = load("692", "top_k_frequent")
        for _ in range(250):
            words = [self.r.choice(["a", "ab", "b", "ba", "cat", "dog"]) for _ in range(self.r.randrange(1, 25))]
            counts = Counter(words)
            k = self.r.randint(1, len(counts))
            self.assertEqual(f(words, k), sorted(counts, key=lambda w: (-counts[w], w))[:k])
        self.assertEqual(f(["z", "a", "z", "a"], 1), ["a"])

    def test_1288(self):
        f = load("1288", "remove_covered_intervals")
        universe = list(itertools.combinations(range(9), 2))
        for _ in range(250):
            intervals = self.r.sample(universe, self.r.randrange(1, 12))
            expected = sum(not any(c <= a and b <= d for c, d in intervals if (a, b) != (c, d))
                           for a, b in intervals)
            self.assertEqual(f(intervals), expected)
        self.assertEqual(f([(1, 2), (1, 3), (2, 3)]), 1)

    def test_103(self):
        f = load("103", "zigzag_level_order")
        for _ in range(200):
            root = random_tree(self.r, self.r.randrange(25))
            levels = []

            def dfs(node, depth):
                if node is None:
                    return
                if depth == len(levels):
                    levels.append([])
                levels[depth].append(node.val)
                dfs(node.left, depth + 1)
                dfs(node.right, depth + 1)

            dfs(root, 0)
            expected = [level[::-1] if i % 2 else level for i, level in enumerate(levels)]
            self.assertEqual(f(root), expected)
        self.assertEqual(f(None), [])

    def test_1029(self):
        f = load("1029", "two_city_cost")
        for _ in range(200):
            n = self.r.randint(1, 5)
            costs = [[self.r.randint(1, 20), self.r.randint(1, 20)] for _ in range(2 * n)]
            expected = min(sum(pair[0 if i in chosen else 1] for i, pair in enumerate(costs))
                           for chosen in map(set, itertools.combinations(range(2 * n), n)))
            self.assertEqual(f(costs), expected)

    def test_1233(self):
        f = load("1233", "remove_subfolders")
        universe = ["/" + "/".join(parts) for k in range(1, 4)
                    for parts in itertools.product(("a", "ab", "b"), repeat=k)]
        for _ in range(250):
            folders = self.r.sample(universe, self.r.randint(1, len(universe)))
            expected = {p for p in folders if not any(p.startswith(q + "/") for q in folders if p != q)}
            self.assertEqual(set(f(folders)), expected)
            self.assertEqual(len(f(folders)), len(expected))
        self.assertEqual(set(f(["/a", "/ab", "/a/b"])), {"/a", "/ab"})

    def test_1382(self):
        f = load("1382", "balance_bst")

        def examine(node):
            if node is None:
                return [], 0
            left, lh = examine(node.left)
            right, rh = examine(node.right)
            self.assertLessEqual(abs(lh - rh), 1)
            return left + [node.val] + right, 1 + max(lh, rh)

        for _ in range(150):
            values = self.r.sample(range(1000), self.r.randint(0, 40))
            root = None
            for value in values:
                root = insert_bst(root, value)
            self.assertEqual(examine(f(root))[0], sorted(values))
        root = Node(0)
        node = root
        for i in range(1, 2500):
            node.right = Node(i)
            node = node.right
        self.assertEqual(examine(f(root))[0], list(range(2500)))

    def test_1353(self):
        f = load("1353", "max_events")

        def brute(events, day, used):
            if day > 6:
                return 0
            best = brute(events, day + 1, used)
            for i, (start, end) in enumerate(events):
                if not used & (1 << i) and start <= day <= end:
                    best = max(best, 1 + brute(events, day + 1, used | (1 << i)))
            return best

        for _ in range(150):
            events = []
            for _ in range(self.r.randrange(8)):
                a = self.r.randint(1, 6)
                events.append([a, self.r.randint(a, 6)])
            self.assertEqual(f(events), brute(events, 1, 0))
        self.assertEqual(f([[1, 1], [1, 1], [100000, 100000]]), 2)
        self.assertEqual(f([[1, 100000]] * 10000), 10000)

    def test_695(self):
        f = load("695", "max_area_of_island")
        for _ in range(200):
            rows, cols = self.r.randint(1, 5), self.r.randint(1, 5)
            grid = [[self.r.randrange(2) for _ in range(cols)] for _ in range(rows)]
            land = {(r, c) for r in range(rows) for c in range(cols) if grid[r][c]}
            best = 0
            while land:
                group = {land.pop()}
                while True:
                    neighbours = {(r + dr, c + dc) for r, c in group for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))}
                    new = neighbours & land
                    if not new:
                        break
                    group |= new
                    land -= new
                best = max(best, len(group))
            original = [row[:] for row in grid]
            self.assertEqual(f(grid), best)
            self.assertEqual(grid, original)
        self.assertEqual(f([[1, 0], [0, 1]]), 1)

    def test_2316(self):
        f = load("2316", "count_unreachable_pairs")
        for _ in range(200):
            n = self.r.randint(1, 9)
            edges = [e for e in itertools.combinations(range(n), 2) if self.r.randrange(3) == 0]
            reach = graph_reach(n, edges)
            self.assertEqual(f(n, edges), sum(not reach[i][j] for i in range(n) for j in range(i + 1, n)))
        self.assertEqual(f(100000, []), 100000 * 99999 // 2)

    def test_1466(self):
        f = load("1466", "min_reorder")
        for _ in range(120):
            n = self.r.randint(2, 7)
            roads = []
            for v in range(1, n):
                u = self.r.randrange(v)
                roads.append((u, v) if self.r.randrange(2) else (v, u))
            expected = n
            for mask in range(1 << (n - 1)):
                directed = [(v, u) if mask & (1 << i) else (u, v) for i, (u, v) in enumerate(roads)]
                reach = {0}
                for _ in range(n):
                    reach |= {u for u, v in directed if v in reach}
                if len(reach) == n:
                    expected = min(expected, mask.bit_count())
            self.assertEqual(f(n, roads), expected)
        self.assertEqual(f(10000, [(i, i + 1) for i in range(9999)]), 9999)

    def test_851(self):
        f = load("851", "loud_and_rich")
        for _ in range(200):
            n = self.r.randint(1, 9)
            ranking = self.r.sample(range(n), n)
            quiet = self.r.sample(range(n), n)
            edges = [(ranking[i], ranking[j]) for i in range(n) for j in range(i + 1, n)
                     if self.r.randrange(3) == 0]
            reach = [[i == j for j in range(n)] for i in range(n)]
            for rich, poor in edges:
                reach[rich][poor] = True
            for k in range(n):
                for i in range(n):
                    for j in range(n):
                        reach[i][j] |= reach[i][k] and reach[k][j]
            expected = [min((i for i in range(n) if reach[i][j]), key=lambda i: quiet[i]) for j in range(n)]
            self.assertEqual(f(edges, quiet), expected)

    def test_542(self):
        f = load("542", "update_matrix")
        for _ in range(200):
            rows, cols = self.r.randint(1, 6), self.r.randint(1, 6)
            mat = [[self.r.randrange(2) for _ in range(cols)] for _ in range(rows)]
            mat[0][0] = 0
            zeros = [(r, c) for r in range(rows) for c in range(cols) if mat[r][c] == 0]
            expected = [[min(abs(r - x) + abs(c - y) for x, y in zeros) for c in range(cols)] for r in range(rows)]
            self.assertEqual(f(mat), expected)

    def test_1786(self):
        f = load("1786", "count_restricted_paths")
        for _ in range(150):
            n = self.r.randint(2, 8)
            pairs = {(v, self.r.randrange(1, v)) for v in range(2, n + 1)}
            pairs |= {(v, u) for v in range(2, n + 1) for u in range(1, v) if self.r.randrange(4) == 0}
            edges = [(u, v, self.r.randint(1, 8)) for u, v in pairs]
            dist = [[float("inf")] * (n + 1) for _ in range(n + 1)]
            for i in range(1, n + 1):
                dist[i][i] = 0
            for u, v, w in edges:
                dist[u][v] = dist[v][u] = w
            for k in range(1, n + 1):
                for i in range(1, n + 1):
                    for j in range(1, n + 1):
                        dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

            def enumerate_paths(u):
                if u == n:
                    return 1
                neighbours = [v if a == u else a for a, v, _ in edges if a == u or v == u]
                return sum(enumerate_paths(v) for v in neighbours if dist[v][n] < dist[u][n])

            self.assertEqual(f(n, edges), enumerate_paths(1))
        self.assertEqual(f(3, [(1, 2, 1), (2, 3, 1), (1, 3, 4)]), 2)
        layers = 35
        groups = [[1]] + [[2 + 2 * i, 3 + 2 * i] for i in range(layers)] + [[2 * layers + 2]]
        edges = [(u, v, 1) for group, following in zip(groups, groups[1:])
                 for u in group for v in following]
        self.assertEqual(f(2 * layers + 2, edges), pow(2, layers, 1_000_000_007))

    def test_909(self):
        f = load("909", "snakes_and_ladders")
        for _ in range(200):
            n = self.r.randint(2, 5)
            size = n * n
            cells = [-1] * (size + 1)
            for s in range(2, size):
                if self.r.randrange(3) == 0:
                    cells[s] = self.r.randint(1, size)
            rows = []
            for offset in range(0, size, n):
                row = cells[offset + 1:offset + n + 1]
                rows.append(row if len(rows) % 2 == 0 else row[::-1])
            board = rows[::-1]
            distance = [float("inf")] * (size + 1)
            distance[1] = 0
            for _ in range(size):
                for start in range(1, size + 1):
                    for landing in range(start + 1, min(start + 6, size) + 1):
                        end = cells[landing] if cells[landing] != -1 else landing
                        distance[end] = min(distance[end], distance[start] + 1)
            expected = -1 if distance[size] == float("inf") else distance[size]
            self.assertEqual(f(board), expected)
        self.assertEqual(f([[-1] * 3 for _ in range(3)]), 2)
        self.assertEqual(f([[1, 1, -1], [1, 1, 1], [-1, 1, 1]]), -1)

    def test_2492(self):
        f = load("2492", "min_score")
        for _ in range(180):
            n = self.r.randint(2, 7)
            pairs = {(v, self.r.randrange(1, v)) for v in range(2, n + 1)}
            pairs |= {(v, u) for v in range(2, n + 1) for u in range(1, v) if self.r.randrange(4) == 0}
            roads = [(u, v, self.r.randint(1, 12)) for u, v in pairs]
            queue = deque([(1, float("inf"))])
            states = {(1, float("inf"))}
            while queue:
                u, score = queue.popleft()
                for a, b, weight in roads:
                    if a == u or b == u:
                        v = b if a == u else a
                        state = (v, min(score, weight))
                        if state not in states:
                            states.add(state)
                            queue.append(state)
            expected = min(score for city, score in states if city == n)
            self.assertEqual(f(n, roads), expected)
        self.assertEqual(f(4, [(1, 2, 7), (2, 3, 1), (2, 4, 5)]), 1)

    def test_1882(self):
        f = load("1882", "assign_tasks")

        def simulate(servers, tasks):
            free_at = [0] * len(servers)
            answer = []
            waiting = deque()
            time = 0
            while len(answer) < len(tasks):
                if time < len(tasks):
                    waiting.append(time)
                while waiting:
                    available = [i for i in range(len(servers)) if free_at[i] <= time]
                    if not available:
                        break
                    i = min(available, key=lambda x: (servers[x], x))
                    task = waiting.popleft()
                    free_at[i] = time + tasks[task]
                    answer.append(i)
                time += 1
            return answer

        for _ in range(250):
            servers = [self.r.randint(1, 4) for _ in range(self.r.randint(1, 5))]
            tasks = [self.r.randint(1, 8) for _ in range(self.r.randint(1, 14))]
            self.assertEqual(f(servers, tasks), simulate(servers, tasks))
        self.assertEqual(f([3, 1], [2, 1, 2]), [1, 0, 1])
        self.assertEqual(f([5, 1], [2, 1, 3]), [1, 0, 1])

    def test_2092(self):
        f = load("2092", "find_all_people")

        def simulate(n, meetings, first):
            known = {0, first}
            for time in sorted({meeting[2] for meeting in meetings}):
                batch = [(a, b) for a, b, t in meetings if t == time]
                while True:
                    before = len(known)
                    for a, b in batch:
                        if a in known or b in known:
                            known.update((a, b))
                    if len(known) == before:
                        break
            return sorted(known)

        for _ in range(300):
            n = self.r.randint(2, 9)
            meetings = []
            for _ in range(self.r.randint(0, 20)):
                a, b = self.r.sample(range(n), 2)
                meetings.append((a, b, self.r.randint(1, 5)))
            first = self.r.randrange(1, n)
            self.assertEqual(f(n, meetings, first), simulate(n, meetings, first))
            self.r.shuffle(meetings)
            self.assertEqual(f(n, meetings, first), simulate(n, meetings, first))
        self.assertEqual(f(5, [[3, 4, 3], [2, 3, 3], [1, 2, 3]], 1), [0, 1, 2, 3, 4])
        self.assertEqual(f(5, [[3, 4, 1], [1, 3, 2]], 1), [0, 1, 3])
        self.assertEqual(f(3, [], 1), [0, 1])
        self.assertEqual(len(f(10000, [(i, i + 1, 1) for i in range(1, 9999)], 1)), 10000)

    def test_279(self):
        f = load("279", "num_squares")
        for n in range(201):
            squares = [i * i for i in range(1, n + 1) if i * i <= n]
            frontier = {0}
            seen = {0}
            depth = 0
            while n not in frontier:
                frontier = {x + s for x in frontier for s in squares if x + s <= n} - seen
                seen |= frontier
                depth += 1
            self.assertEqual(f(n), depth)
        self.assertEqual(f(12), 3)
        self.assertEqual(f(10000), 1)

    def test_40(self):
        f = load("40", "combination_sum2")
        for _ in range(300):
            candidates = [self.r.randint(1, 8) for _ in range(self.r.randint(0, 10))]
            target = self.r.randint(1, 20)
            expected = {tuple(sorted(candidates[i] for i in range(len(candidates)) if mask & (1 << i)))
                        for mask in range(1 << len(candidates))
                        if sum(candidates[i] for i in range(len(candidates)) if mask & (1 << i)) == target}
            result = f(candidates, target)
            self.assertEqual({tuple(row) for row in result}, expected)
            self.assertEqual(len(result), len(expected))
        self.assertEqual(f([1, 1, 2, 5], 3), [[1, 2]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
