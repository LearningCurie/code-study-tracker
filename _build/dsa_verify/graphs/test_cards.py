"""Exercise the actual graph-card snippets against independent small-input oracles."""

import copy
import itertools
import heapq
from pathlib import Path
import random
import re
import sys
import unittest

BUILD = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUILD))
from build_dsa_guide import CARD_HEADINGS, CARD_WORDS, Problems, card_parts, parse_cards

CARDS_PATH = BUILD / "dsa" / "19-graphs.cards.md"
MODULE_PATH = BUILD / "dsa" / "19-graphs.md"
CARDS = parse_cards(CARDS_PATH)
CODE = {}
for pid, card in CARDS.items():
    blocks = re.findall(r"```python\n(.*?)\n```", card["md"], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"card {pid}: expected exactly one Python block")
    CODE[pid] = {}
    exec(compile(blocks[0], f"card-{pid}", "exec"), CODE[pid])


def clone(grid):
    return [row[:] for row in grid]


def neighbors(r, c, rows, cols, diagonal=False):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    yield nr, nc


def closure(n, edges, directed=False):
    reach = [[i == j for j in range(n)] for i in range(n)]
    for u, v in edges:
        reach[u][v] = True
        if not directed:
            reach[v][u] = True
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] |= reach[i][k] and reach[k][j]
    return reach


def component(grid, sr, sc):
    rows, cols = len(grid), len(grid[0])
    found = {(sr, sc)}
    while True:
        expanded = found | {
            (nr, nc) for r, c in found
            for nr, nc in neighbors(r, c, rows, cols)
            if grid[nr][nc] == grid[sr][sc]
        }
        if expanded == found:
            return found
        found = expanded


def island_oracle(grid):
    land = {(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == "1"}
    count = 0
    while land:
        r, c = next(iter(land))
        land -= component(grid, r, c)
        count += 1
    return count


def shortest_grid_oracle(grid):
    n = len(grid)
    if grid[0][0] or grid[-1][-1]:
        return -1
    distances = {(0, 0): 1}
    for _ in range(n * n):
        previous = distances.copy()
        for (r, c), distance in previous.items():
            for nr, nc in neighbors(r, c, n, n, diagonal=True):
                if not grid[nr][nc]:
                    distances[(nr, nc)] = min(distances.get((nr, nc), n * n + 1), distance + 1)
        if distances == previous:
            break
    return distances.get((n - 1, n - 1), -1)


def rot_oracle(grid):
    grid = clone(grid)
    rows, cols = len(grid), len(grid[0])
    minutes = 0
    while True:
        affected = {(nr, nc) for r in range(rows) for c in range(cols)
                    if grid[r][c] == 2
                    for nr, nc in neighbors(r, c, rows, cols)
                    if grid[nr][nc] == 1}
        if not affected:
            return (-1 if any(1 in row for row in grid) else minutes), grid
        for r, c in affected:
            grid[r][c] = 2
        minutes += 1


def water_oracle(grid):
    rows, cols = len(grid), len(grid[0])
    answer = []
    for sr in range(rows):
        for sc in range(cols):
            found = {(sr, sc)}
            while True:
                expanded = found | {
                    (nr, nc) for r, c in found
                    for nr, nc in neighbors(r, c, rows, cols)
                    if grid[nr][nc] <= grid[r][c]
                }
                if expanded == found:
                    break
                found = expanded
            if (any(r == 0 or c == 0 for r, c in found)
                    and any(r == rows - 1 or c == cols - 1 for r, c in found)):
                answer.append((sr, sc))
    return answer


def lock_oracle(deadends, target):
    blocked = {tuple(map(int, state)) for state in deadends}
    start = (0, 0, 0, 0)
    goal = tuple(map(int, target))
    if start in blocked or goal in blocked:
        return -1
    # A* uses cyclic Manhattan distance, an admissible and consistent lower bound.
    def estimate(state):
        return sum(min(abs(a - b), 10 - abs(a - b)) for a, b in zip(state, goal))

    distances = {start: 0}
    heap = [(estimate(start), 0, start)]
    while heap:
        _, distance, state = heapq.heappop(heap)
        if distance != distances[state]:
            continue
        if state == goal:
            return distance
        for i in range(4):
            for step in (-1, 1):
                digits = list(state)
                digits[i] = (digits[i] + step) % 10
                nxt = tuple(digits)
                if nxt not in blocked and distance + 1 < distances.get(nxt, 10001):
                    distances[nxt] = distance + 1
                    heapq.heappush(heap, (distance + 1 + estimate(nxt), distance + 1, nxt))
    return -1


def bipartite_oracle(graph):
    n = len(graph)
    return any(all(((mask >> u) & 1) != ((mask >> v) & 1)
                   for u, row in enumerate(graph) for v in row)
               for mask in range(1 << n))


def valid_order(order, n, relations):
    if sorted(order) != list(range(n)):
        return False
    positions = {v: i for i, v in enumerate(order)}
    return all(positions[pre] < positions[course] for course, pre in relations)


def order_oracle(n, relations):
    return any(valid_order(order, n, relations)
               for order in itertools.permutations(range(n)))


def safe_oracle(graph):
    n = len(graph)
    edges = [(u, v) for u, row in enumerate(graph) for v in row]
    reach = closure(n, edges, directed=True)
    cyclic = {u for u, v in edges if reach[v][u]}
    return [u for u in range(n) if not any(reach[u][v] for v in cyclic)]


def ladder_oracle(begin, end, word_list):
    if end not in word_list:
        return 0
    words = sorted(set(word_list) | {begin})
    n = len(words)
    inf = n + 1
    dist = [[0 if i == j else inf for j in range(n)] for i in range(n)]
    for i, a in enumerate(words):
        for j, b in enumerate(words):
            if sum(x != y for x, y in zip(a, b)) == 1:
                dist[i][j] = 1
    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    d = dist[words.index(begin)][words.index(end)]
    return d + 1 if d < inf else 0


def course_time_oracle(n, relations, durations):
    outgoing = [[] for _ in range(n)]
    for a, b in relations:
        outgoing[a - 1].append(b - 1)

    def paths(u, total):
        total += durations[u]
        return max([total] + [paths(v, total) for v in outgoing[u]])

    return max(paths(u, 0) for u in range(n))


def run_with_snapshots(pid, function, args):
    keys = {"queue", "seen", "stack", "image", "grid", "islands", "fresh",
            "elapsed", "colors", "indegree", "order", "remaining", "safe",
            "word", "distance", "ready", "finish", "answer", "state"}
    snapshots = []

    def trace(frame, event, arg):
        if frame.f_code.co_filename == f"card-{pid}" and event in ("line", "return"):
            snapshots.append(copy.deepcopy({k: v for k, v in frame.f_locals.items() if k in keys}))
        return trace

    previous_trace = sys.gettrace()
    try:
        sys.settrace(trace)
        result = function(*copy.deepcopy(args))
    finally:
        sys.settrace(previous_trace)
    return result, snapshots


class GraphCardsTests(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(15927)

    def test_coverage_and_structure(self):
        practice = MODULE_PATH.read_text().split("=== practice\n", 1)[1]
        ids = re.findall(r"(?m)^- (\d+) (?:core|derive|stretch|mixed)\s*$", practice)
        self.assertEqual(len(ids), 12)
        self.assertEqual(set(ids), set(CARDS))
        problems = Problems()
        warnings = []
        for pid, card in CARDS.items():
            headings = re.findall(r"(?m)^## .+$", card["md"])
            self.assertEqual(headings, list(CARD_HEADINGS))
            self.assertEqual(len(re.findall(r"```steps\n.*?\n```", card["md"], re.S)), 1)
            diff = problems.record(pid)[1]
            _, _, words = card_parts(pid, card, diff, CARDS_PATH.name, warnings)
            self.assertGreaterEqual(words, CARD_WORDS[diff])
        self.assertEqual(warnings, [])

    def test_all_displayed_traces(self):
        # Each example is taken from its steps block; the independent oracles
        # also validate the quoted output rather than merely copying it.
        cases = [
            ("1971", "valid_path", (3, [[0, 1], [1, 2]], 0, 2), True),
            ("733", "flood_fill", ([[1, 1], [1, 0]], 0, 0, 2), [[2, 2], [2, 0]]),
            ("200", "num_islands", ([["1", "1", "0"], ["0", "1", "1"], ["1", "0", "0"]],), 2),
            ("1091", "shortest_path_binary_matrix", ([[0, 1, 0], [1, 0, 0], [1, 1, 0]],), 3),
            ("994", "oranges_rotting", ([[2, 1, 1], [1, 1, 0]],), 2),
            ("417", "pacific_atlantic", ([[1, 2], [4, 3]],), [(0, 1), (1, 0), (1, 1)]),
            ("752", "open_lock", ([], "0009"), 1),
            ("785", "is_bipartite", ([[1, 2], [0, 2], [0, 1]],), False),
            ("210", "find_order", (3, [[1, 0], [2, 0]]), [0, 1, 2]),
            ("802", "eventual_safe_nodes", ([[1], [2], [], [3]],), [0, 1, 2]),
            ("127", "ladder_length", ("hit", "cog", ["hot", "dot", "dog", "cog"]), 5),
            ("2050", "minimum_time", (3, [[1, 3], [2, 3]], [3, 2, 5]), 8),
        ]
        states = {}
        for pid, name, args, expected in cases:
            with self.subTest(card=pid):
                result, states[pid] = run_with_snapshots(pid, CODE[pid][name], args)
                self.assertEqual(result, expected)
        # Check the displayed intermediate states, not just final answers.
        self.assertTrue(any(s.get("seen") == {0, 1, 2} and list(s.get("queue", ())) == [2]
                            for s in states["1971"]))
        self.assertTrue(any(s.get("image") == [[2, 2], [2, 0]] for s in states["733"]))
        self.assertTrue(any(s.get("islands") == 1 and
                            s.get("grid") == [["0", "0", "0"], ["0", "0", "0"], ["1", "0", "0"]]
                            for s in states["200"]))
        self.assertTrue(any(list(s.get("queue", ())) == [(1, 1, 2)] for s in states["1091"]))
        self.assertTrue(any((2, 2, 3) in s.get("queue", ()) for s in states["1091"]))
        self.assertTrue(any(s.get("fresh") == 2 for s in states["994"]))
        self.assertTrue(any(s.get("fresh") == 0 and s.get("elapsed") == 2 for s in states["994"]))
        self.assertTrue(any(s.get("seen") == {(0, 0), (0, 1), (1, 0), (1, 1)} for s in states["417"]))
        self.assertTrue(any(s.get("seen") == {(0, 1), (1, 0), (1, 1)} for s in states["417"]))
        self.assertTrue(any(s.get("state") == "0009" and s.get("distance") == 1 for s in states["752"]))
        self.assertTrue(any(s.get("colors") == [0, 1, 1] for s in states["785"]))
        self.assertTrue(any(s.get("indegree") == [0, 0, 0] and s.get("order") == [0]
                            and list(s.get("queue", ())) == [1, 2] for s in states["210"]))
        self.assertTrue(any(s.get("safe") == [True, True, True, False] for s in states["802"]))
        for word, distance in [("hit", 1), ("hot", 2), ("dot", 3), ("dog", 4), ("cog", 5)]:
            self.assertTrue(any(s.get("word") == word and s.get("distance") == distance
                                for s in states["127"]))
        self.assertTrue(any(s.get("ready") == [0, 0, 3] and s.get("indegree") == [0, 0, 0]
                            and list(s.get("queue", ())) == [2] for s in states["2050"]))
        self.assertTrue(any(s.get("finish") == 8 and s.get("answer") == 8 for s in states["2050"]))
        self.assertTrue(closure(3, [(0, 1), (1, 2)])[0][2])
        self.assertEqual(component([[1, 1], [1, 0]], 0, 0), {(0, 0), (0, 1), (1, 0)})
        self.assertEqual(island_oracle([["1", "1", "0"], ["0", "1", "1"], ["1", "0", "0"]]), 2)
        self.assertEqual(shortest_grid_oracle([[0, 1, 0], [1, 0, 0], [1, 1, 0]]), 3)
        self.assertEqual(rot_oracle([[2, 1, 1], [1, 1, 0]])[0], 2)
        self.assertEqual(water_oracle([[1, 2], [4, 3]]), [(0, 1), (1, 0), (1, 1)])
        self.assertEqual(lock_oracle([], "0009"), 1)
        self.assertFalse(bipartite_oracle([[1, 2], [0, 2], [0, 1]]))
        self.assertTrue(valid_order([0, 1, 2], 3, [[1, 0], [2, 0]]))
        self.assertEqual(safe_oracle([[1], [2], [], [3]]), [0, 1, 2])
        self.assertEqual(ladder_oracle("hit", "cog", ["hot", "dot", "dog", "cog"]), 5)
        self.assertEqual(course_time_oracle(3, [[1, 3], [2, 3]], [3, 2, 5]), 8)

    def test_path_random_and_edges(self):
        f, rng = CODE["1971"]["valid_path"], self.rng
        self.assertTrue(f(1, [], 0, 0))
        self.assertFalse(f(2, [], 0, 1))
        for _ in range(200):
            n = rng.randrange(1, 9)
            edges = [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < .3]
            a, b = rng.randrange(n), rng.randrange(n)
            self.assertEqual(f(n, edges, a, b), closure(n, edges)[a][b])

    def test_fill_random_and_edges(self):
        f, rng = CODE["733"]["flood_fill"], self.rng
        self.assertEqual(f([[3]], 0, 0, 3), [[3]])
        self.assertEqual(f([[1, 0], [0, 1]], 0, 0, 2), [[2, 0], [0, 1]])
        for _ in range(200):
            rows, cols = rng.randrange(1, 6), rng.randrange(1, 6)
            grid = [[rng.randrange(3) for _ in range(cols)] for _ in range(rows)]
            r, c, color = rng.randrange(rows), rng.randrange(cols), rng.randrange(3)
            expected = clone(grid)
            for x, y in component(grid, r, c):
                expected[x][y] = color
            actual = clone(grid)
            self.assertIs(f(actual, r, c, color), actual)
            self.assertEqual(actual, expected)

    def test_islands_random_and_edges(self):
        f, rng = CODE["200"]["num_islands"], self.rng
        self.assertEqual(f([["0"]]), 0)
        self.assertEqual(f([["1"]]), 1)
        self.assertEqual(f([["1", "0"], ["0", "1"]]), 2)
        for _ in range(200):
            rows, cols = rng.randrange(1, 6), rng.randrange(1, 6)
            grid = [[rng.choice("01") for _ in range(cols)] for _ in range(rows)]
            self.assertEqual(f(clone(grid)), island_oracle(grid))

    def test_shortest_grid_random_and_edges(self):
        f, rng = CODE["1091"]["shortest_path_binary_matrix"], self.rng
        for grid, expected in [([[0]], 1), ([[1]], -1), ([[0, 1], [1, 0]], 2),
                               ([[0, 1], [1, 1]], -1)]:
            self.assertEqual(f(grid), expected)
        for _ in range(200):
            n = rng.randrange(1, 7)
            grid = [[rng.randrange(2) for _ in range(n)] for _ in range(n)]
            self.assertEqual(f(grid), shortest_grid_oracle(grid))

    def test_rot_random_and_edges(self):
        f, rng = CODE["994"]["oranges_rotting"], self.rng
        for grid, expected in [([[0]], 0), ([[2]], 0), ([[1]], -1),
                               ([[2, 0, 1]], -1), ([[2, 1, 1, 1, 2]], 2)]:
            self.assertEqual(f(clone(grid)), expected)
        for _ in range(200):
            rows, cols = rng.randrange(1, 6), rng.randrange(1, 6)
            grid = [[rng.randrange(3) for _ in range(cols)] for _ in range(rows)]
            expected, final = rot_oracle(grid)
            actual = clone(grid)
            self.assertEqual(f(actual), expected)
            self.assertEqual(actual, final)

    def test_water_random_and_edges(self):
        f, rng = CODE["417"]["pacific_atlantic"], self.rng
        self.assertEqual(f([[4]]), [(0, 0)])
        self.assertEqual(f([[1, 2, 1]]), [(0, 0), (0, 1), (0, 2)])
        for _ in range(200):
            rows, cols = rng.randrange(1, 6), rng.randrange(1, 6)
            grid = [[rng.randrange(5) for _ in range(cols)] for _ in range(rows)]
            result = f(grid)
            self.assertEqual(result, water_oracle(grid))

    def test_lock_random_and_edges(self):
        f, rng = CODE["752"]["open_lock"], self.rng
        self.assertEqual(f(["0000"], "0000"), -1)
        self.assertEqual(f([], "0000"), 0)
        self.assertEqual(f(["0009"], "0009"), -1)
        blocked_neighbors = ["1000", "9000", "0100", "0900", "0010", "0090", "0001", "0009"]
        self.assertEqual(f(blocked_neighbors, "8888"), -1)
        self.assertEqual(f(["0001"], "0002"), 4)
        for _ in range(80):
            target = "".join(str(rng.randrange(10)) for _ in range(4))
            dead = {f"{rng.randrange(10000):04d}" for _ in range(rng.randrange(0, 100))}
            self.assertEqual(f(dead, target), lock_oracle(dead, target))

    def test_bipartite_random_and_edges(self):
        f, rng = CODE["785"]["is_bipartite"], self.rng
        self.assertTrue(f([]))
        self.assertFalse(f([[0]]))
        self.assertFalse(f([[], [2, 3], [1, 3], [1, 2]]))
        for _ in range(200):
            n = rng.randrange(0, 8)
            graph = [[] for _ in range(n)]
            for u in range(n):
                for v in range(u, n):
                    if rng.random() < .22:
                        graph[u].append(v)
                        if u != v:
                            graph[v].append(u)
            self.assertEqual(f(graph), bipartite_oracle(graph))

    def test_course_order_random_and_edges(self):
        f, rng = CODE["210"]["find_order"], self.rng
        self.assertEqual(f(1, [[0, 0]]), [])
        self.assertEqual(f(2, [[1, 0], [0, 1]]), [])
        self.assertTrue(valid_order(f(3, [[1, 0], [1, 0]]), 3, [[1, 0], [1, 0]]))
        for _ in range(160):
            n = rng.randrange(1, 7)
            relations = [[u, v] for u in range(n) for v in range(n) if rng.random() < .14]
            result = f(n, relations)
            self.assertEqual(bool(result), order_oracle(n, relations))
            if result:
                self.assertTrue(valid_order(result, n, relations))

    def test_safe_random_and_edges(self):
        f, rng = CODE["802"]["eventual_safe_nodes"], self.rng
        self.assertEqual(f([]), [])
        self.assertEqual(f([[0], []]), [1])
        self.assertEqual(f([[1, 2], [1], []]), [2])
        self.assertEqual(f([[1, 1], []]), [0, 1])
        for _ in range(200):
            n = rng.randrange(0, 9)
            graph = [[v for v in range(n) if rng.random() < .2] for _ in range(n)]
            self.assertEqual(f(graph), safe_oracle(graph))

    def test_ladder_random_and_edges(self):
        f, rng = CODE["127"]["ladder_length"], self.rng
        self.assertEqual(f("hit", "cog", ["hot", "dot", "dog"]), 0)
        self.assertEqual(f("a", "c", ["c"]), 2)
        self.assertEqual(f("abc", "xyz", ["xyz"]), 0)
        all_words = ["".join(w) for w in itertools.product("abc", repeat=3)]
        for _ in range(160):
            begin, end = rng.sample(all_words, 2)
            words = rng.sample(all_words, rng.randrange(len(all_words) + 1))
            self.assertEqual(f(begin, end, words), ladder_oracle(begin, end, words))

    def test_course_time_random_and_edges(self):
        f, rng = CODE["2050"]["minimum_time"], self.rng
        self.assertEqual(f(1, [], [7]), 7)
        self.assertEqual(f(3, [], [3, 9, 2]), 9)
        self.assertEqual(f(3, [[1, 2], [2, 3]], [3, 2, 5]), 10)
        self.assertEqual(f(4, [[1, 3], [2, 3]], [1, 8, 2, 20]), 20)
        for _ in range(200):
            n = rng.randrange(1, 8)
            order = list(range(1, n + 1))
            rng.shuffle(order)
            relations = [[order[i], order[j]] for i in range(n)
                         for j in range(i + 1, n) if rng.random() < .35]
            durations = [rng.randrange(1, 10) for _ in range(n)]
            self.assertEqual(f(n, relations, durations), course_time_oracle(n, relations, durations))


if __name__ == "__main__":
    unittest.main()
