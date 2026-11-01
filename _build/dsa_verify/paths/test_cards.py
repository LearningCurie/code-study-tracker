"""Exercise the snippets embedded in the path cards against small independent oracles."""

import itertools
import math
from pathlib import Path
import random
import re
import sys
import unittest

BUILD = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUILD))
from build_dsa_guide import Problems, card_parts, load_module, parse_cards

CARDS = parse_cards(BUILD / 'dsa' / '21-paths.cards.md')
CODE = {}
for pid, card in CARDS.items():
    blocks = re.findall(r'```python\n(.*?)\n```', card['md'], re.S)
    if len(blocks) != 1:
        raise AssertionError(f'{pid}: expected exactly one Python block, got {len(blocks)}')
    CODE[pid] = {}
    exec(compile(blocks[0], f'card-{pid}', 'exec'), CODE[pid])


def neighbours(r, c, rows, cols):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc


def simple_paths(n, edges, start, end, directed=True):
    graph = [[] for _ in range(n)]
    for u, v, weight in edges:
        graph[u].append((v, weight))
        if not directed:
            graph[v].append((u, weight))
    def visit(u, seen, weights):
        if u == end:
            yield weights
            return
        for v, weight in graph[u]:
            if v not in seen:
                yield from visit(v, seen | {v}, weights + [weight])
    return visit(start, {start}, [])


def distances(n, edges, start):
    result = [math.inf] * n
    result[start] = 0
    for _ in range(n - 1):
        updated = result[:]
        for u, v, weight in edges:
            updated[v] = min(updated[v], result[u] + weight)
        result = updated
    return result


def grid_paths(grid):
    rows, cols = len(grid), len(grid[0])
    def visit(r, c, seen, path):
        if (r, c) == (rows - 1, cols - 1):
            yield path
            return
        for nr, nc in neighbours(r, c, rows, cols):
            if (nr, nc) not in seen:
                yield from visit(nr, nc, seen | {(nr, nc)}, path + [(nr, nc)])
    return visit(0, 0, {(0, 0)}, [(0, 0)])


def component_count(n, edges):
    components = [{i} for i in range(n)]
    for u, v in edges:
        a = next(group for group in components if u in group)
        b = next(group for group in components if v in group)
        if a is not b:
            a.update(b)
            components.remove(b)
    return len(components)


def shared_oracle(n, edges, a, b, dest):
    best = math.inf
    for mask in range(1 << len(edges)):
        selected = [edge for i, edge in enumerate(edges) if mask & (1 << i)]
        cost = sum(w for _, _, w in selected)
        if cost >= best:
            continue
        reachable = []
        for start in (a, b):
            seen = {start}
            while True:
                expanded = seen | {v for u, v, _ in selected if u in seen}
                if expanded == seen:
                    break
                seen = expanded
            reachable.append(dest in seen)
        if all(reachable):
            best = cost
    return -1 if best == math.inf else best


def keys_oracle(grid):
    rows, cols = len(grid), len(grid[0])
    target = frozenset(ch for row in grid for ch in row if ch.islower())
    start = next((r, c) for r, row in enumerate(grid)
                 for c, ch in enumerate(row) if ch == '@')
    # Synchronous reachability expansion, independently using sets of letters, not bit masks.
    reached = {(start[0], start[1], frozenset())}
    for moves in range(rows * cols * (2 ** len(target)) + 1):
        if any(held == target for _, _, held in reached):
            return moves
        updated = set(reached)
        for r, c, held in reached:
            for nr, nc in neighbours(r, c, rows, cols):
                cell = grid[nr][nc]
                if cell == '#' or (cell.isupper() and cell.lower() not in held):
                    continue
                updated.add((nr, nc, held | {cell} if cell.islower() else held))
        if updated == reached:
            return -1
        reached = updated
    raise AssertionError('state bound exceeded')


class TestPathCards(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(2111195)

    def test_structure_and_coverage(self):
        problems = []
        module = load_module(BUILD / 'dsa' / '21-paths.md', problems)
        expected = {p['id'] for p in module['practice']}
        self.assertEqual(expected, set(CARDS))
        self.assertEqual(expected, {'743', '1514', '1631', '787', '1334', '1976',
                                    'cses:1195', '2290', '1368', '2203', '864', '1192'})
        metadata = Problems()
        for pid, card in CARDS.items():
            diff = metadata.record(pid)[1] if pid.isdigit() else 'M'
            errors = []
            card_parts(pid, card, diff, 'cards', errors)
            self.assertEqual(errors, [], pid)

    def test_network_delay(self):
        f = CODE['743']['network_delay']
        self.assertEqual(f([], 1, 1), 0)
        self.assertEqual(f([[1, 2, 0]], 3, 1), -1)
        self.assertEqual(f([[1, 2, 2], [1, 3, 8], [2, 3, 1]], 3, 1), 3)
        for _ in range(240):
            n = self.rng.randint(1, 6)
            edges = [(u, v, self.rng.randrange(7)) for u in range(n) for v in range(n)
                     if u != v and self.rng.random() < .3]
            source = self.rng.randrange(n)
            answer = max(distances(n, edges, source))
            expected = -1 if answer == math.inf else answer
            self.assertEqual(f([(u + 1, v + 1, w) for u, v, w in edges], n, source + 1), expected)

    def test_probability(self):
        f = CODE['1514']['max_probability']
        self.assertEqual(f(1, [], [], 0, 0), 1)
        self.assertEqual(f(2, [(0, 1)], [0], 0, 1), 0)
        self.assertAlmostEqual(f(3, [(0, 1), (1, 2), (0, 2)], [.8, .5, .3], 0, 2), .4)
        for _ in range(200):
            n = self.rng.randint(1, 6)
            edges = [(u, v, self.rng.choice([0, .25, .5, .75, 1]))
                     for u in range(n) for v in range(u + 1, n) if self.rng.random() < .5]
            a, b = self.rng.randrange(n), self.rng.randrange(n)
            expected = max((math.prod(p) for p in simple_paths(n, edges, a, b, False)), default=0)
            self.assertAlmostEqual(f(n, [(u, v) for u, v, _ in edges], [p for _, _, p in edges], a, b), expected)

    def test_effort(self):
        f = CODE['1631']['minimum_effort']
        self.assertEqual(f([[5]]), 0)
        self.assertEqual(f([[1, 4], [2, 3]]), 1)
        for rows, cols in [(1, 4), (2, 2), (2, 3), (3, 3)]:
            for _ in range(45):
                grid = [[self.rng.randrange(7) for _ in range(cols)] for _ in range(rows)]
                expected = min(max((abs(grid[r][c] - grid[rr][cc])
                                    for (r, c), (rr, cc) in zip(path, path[1:])), default=0)
                               for path in grid_paths(grid))
                self.assertEqual(f(grid), expected)

    def test_cheapest_flights(self):
        f = CODE['787']['cheapest_flight']
        self.assertEqual(f(3, [(0, 1, 2), (1, 2, 2), (0, 2, 7)], 0, 2, 0), 7)
        self.assertEqual(f(3, [(0, 1, 2), (1, 2, 2), (0, 2, 7)], 0, 2, 1), 4)
        self.assertEqual(f(1, [], 0, 0, 0), 0)
        for _ in range(250):
            n = self.rng.randint(1, 5)
            edges = [(u, v, self.rng.randrange(8)) for u in range(n) for v in range(n)
                     if u != v and self.rng.random() < .35]
            src, dst, k = self.rng.randrange(n), self.rng.randrange(n), self.rng.randrange(4)
            options = []
            def enumerate_walks(u, cost, remaining):
                if u == dst:
                    options.append(cost)
                if remaining:
                    for a, b, w in edges:
                        if a == u:
                            enumerate_walks(b, cost + w, remaining - 1)
            enumerate_walks(src, 0, k + 1)
            self.assertEqual(f(n, edges, src, dst, k), min(options, default=-1))

    def test_city(self):
        f = CODE['1334']['city_with_fewest']
        self.assertEqual(f(3, [(0, 1, 2), (1, 2, 2)], 2), 2)
        self.assertEqual(f(3, [], 0), 2)
        for _ in range(200):
            n = self.rng.randint(1, 6)
            edges = [(u, v, self.rng.randrange(8)) for u in range(n) for v in range(u + 1, n)
                     if self.rng.random() < .45]
            if edges and self.rng.random() < .3:
                u, v, _ = self.rng.choice(edges)
                edges.append((u, v, self.rng.randrange(8)))
            threshold = self.rng.randrange(10)
            directed = edges + [(v, u, w) for u, v, w in edges]
            counts = [sum(i != j and d <= threshold for j, d in enumerate(distances(n, directed, i)))
                      for i in range(n)]
            expected = max(i for i, count in enumerate(counts) if count == min(counts))
            self.assertEqual(f(n, edges, threshold), expected)

    def test_count_routes(self):
        f = CODE['1976']['count_shortest_routes']
        self.assertEqual(f(1, []), 1)
        self.assertEqual(f(2, []), 0)
        self.assertEqual(f(3, [(0, 2, 3), (0, 1, 1), (1, 2, 2)]), 2)
        for _ in range(220):
            n = self.rng.randint(1, 7)
            edges = [(u, v, self.rng.randint(1, 5)) for u in range(n) for v in range(u + 1, n)
                     if self.rng.random() < .45]
            totals = [sum(path) for path in simple_paths(n, edges, 0, n - 1, False)]
            expected = sum(total == min(totals) for total in totals) if totals else 0
            self.assertEqual(f(n, edges), expected)
        # Two parallel choices on each of 31 layers force modular reduction.
        edges = [(i, i + 1, 1) for i in range(31) for _ in range(2)]
        self.assertEqual(f(32, edges), pow(2, 31, 1_000_000_007))

    def test_coupon(self):
        f = CODE['cses:1195']['discount_flight']
        self.assertEqual(f(1, []), -1)
        self.assertEqual(f(1, [(1, 1, 7)]), 3)
        self.assertEqual(f(2, []), -1)
        self.assertEqual(f(3, [(1, 2, 9), (2, 3, 5)]), 9)
        for _ in range(250):
            n = self.rng.randint(2, 6)
            edges = [(u, v, self.rng.randrange(9)) for u in range(n) for v in range(n)
                     if u != v and self.rng.random() < .35]
            candidates = []
            for weights in simple_paths(n, edges, 0, n - 1):
                total = sum(weights)
                candidates.extend(total - w + w // 2 for w in weights)
            expected = min(candidates, default=-1)
            self.assertEqual(f(n, [(u + 1, v + 1, w) for u, v, w in edges]), expected)

    def test_obstacles(self):
        f = CODE['2290']['minimum_obstacles']
        self.assertEqual(f([[0]]), 0)
        self.assertEqual(f([[0, 1, 0], [0, 1, 0]]), 1)
        for rows, cols in [(1, 4), (2, 3), (3, 3)]:
            cells = [(r, c) for r in range(rows) for c in range(cols)
                     if (r, c) not in ((0, 0), (rows - 1, cols - 1))]
            for values in itertools.product((0, 1), repeat=len(cells)):
                grid = [[0] * cols for _ in range(rows)]
                obstacles = []
                for (r, c), value in zip(cells, values):
                    grid[r][c] = value
                    if value:
                        obstacles.append((r, c))
                expected = None
                for count in range(len(obstacles) + 1):
                    for removed in itertools.combinations(obstacles, count):
                        seen = {(0, 0)}
                        while True:
                            expanded = seen | {(nr, nc) for r, c in seen
                                               for nr, nc in neighbours(r, c, rows, cols)
                                               if not grid[nr][nc] or (nr, nc) in removed}
                            if expanded == seen:
                                break
                            seen = expanded
                        if (rows - 1, cols - 1) in seen:
                            expected = count
                            break
                    if expected is not None:
                        break
                original = [row[:] for row in grid]
                self.assertEqual(f(grid), expected, grid)
                self.assertEqual(grid, original)

    def test_arrows(self):
        f = CODE['1368']['minimum_arrow_changes']
        self.assertEqual(f([[4]]), 0)
        self.assertEqual(f([[1, 1], [4, 3]]), 1)
        directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
        # Exhaustively assign the final arrows and simulate their actual fixed behaviour.
        for values in itertools.product(range(1, 5), repeat=4):
            grid = [list(values[:2]), list(values[2:])]
            expected = 4
            for assignment in itertools.product(range(1, 5), repeat=4):
                cost = sum(a != b for a, b in zip(values, assignment))
                if cost >= expected:
                    continue
                r = c = 0
                seen = set()
                while 0 <= r < 2 and 0 <= c < 2 and (r, c) not in seen:
                    if (r, c) == (1, 1):
                        expected = cost
                        break
                    seen.add((r, c))
                    dr, dc = directions[assignment[2 * r + c] - 1]
                    r, c = r + dr, c + dc
            self.assertEqual(f(grid), expected, grid)
        for _ in range(120):
            rows, cols = 2, 3
            grid = [[self.rng.randint(1, 4) for _ in range(cols)] for _ in range(rows)]
            expected = min(sum(directions[grid[r][c] - 1] != (nr - r, nc - c)
                               for (r, c), (nr, nc) in zip(path, path[1:]))
                           for path in grid_paths(grid))
            self.assertEqual(f(grid), expected)

    def test_shared_weight(self):
        f = CODE['2203']['minimum_shared_weight']
        self.assertEqual(f(1, [], 0, 0, 0), 0)
        self.assertEqual(f(3, [(0, 2, 1)], 0, 1, 2), -1)
        self.assertEqual(f(4, [(0, 2, 2), (1, 2, 3), (2, 3, 4)], 0, 1, 3), 9)
        # Independent subset enumeration counts each selected edge once.
        for _ in range(260):
            n = self.rng.randint(1, 5)
            edges = [(u, v, self.rng.randrange(6)) for u in range(n) for v in range(n)
                     if u != v and self.rng.random() < .32]
            if len(edges) > 10:
                edges = edges[:10]
            if edges and self.rng.random() < .15:
                edges.append(self.rng.choice(edges))
            src1, src2, dest = (self.rng.randrange(n) for _ in range(3))
            self.assertEqual(f(n, edges, src1, src2, dest),
                             shared_oracle(n, edges, src1, src2, dest), (n, edges, src1, src2, dest))

    def test_keys(self):
        f = CODE['864']['shortest_collect_keys']
        cases = [(['@'], 0), (['@.aA.b'], 5), (['@Aa'], -1),
                 (['@Z.a'], -1), (['@.fF.a'], 5), (['@..a', '##A.', 'b...'], 8),
                 (['@#a'], -1), (['@a..'], 1)]
        for grid, expected in cases:
            self.assertEqual(keys_oracle(grid), expected, grid)
            self.assertEqual(f(grid), expected, grid)
        for _ in range(250):
            rows, cols = 2, 3
            cells = ['a', 'f', 'A', 'F', '#', '#', '.', '.', 'Z']
            grid = [['.' for _ in range(cols)] for _ in range(rows)]
            grid[0][0] = '@'
            selected = iter(self.rng.sample(cells, rows * cols - 1))
            for r in range(rows):
                for c in range(cols):
                    if (r, c) != (0, 0):
                        grid[r][c] = next(selected)
            grid = [''.join(row) for row in grid]
            self.assertEqual(f(grid), keys_oracle(grid), grid)

    def test_bridges(self):
        f = CODE['1192']['critical_connections']
        def normalise(edges):
            return {tuple(sorted(edge)) for edge in edges}
        self.assertEqual(f(0, []), [])
        self.assertEqual(normalise(f(4, [(0, 1), (1, 2), (2, 0), (1, 3)])), {(1, 3)})
        self.assertEqual(f(2, [(0, 1), (0, 1)]), [])
        for _ in range(450):
            n = self.rng.randint(1, 7)
            edges = [(self.rng.randrange(n), self.rng.randrange(n))
                     for _ in range(self.rng.randrange(12))]
            original = component_count(n, edges)
            expected = {tuple(sorted(edge)) for i, edge in enumerate(edges)
                        if component_count(n, edges[:i] + edges[i + 1:]) > original}
            actual = f(n, edges)
            self.assertEqual(normalise(actual), expected, (n, edges))
            self.assertEqual(len(actual), len(expected))
        n = 100_000
        chain = [(i, i + 1) for i in range(n - 1)]
        self.assertEqual(len(f(n, chain)), n - 1)


if __name__ == '__main__':
    unittest.main()
