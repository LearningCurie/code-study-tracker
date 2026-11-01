import itertools
import random
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "20-dsu.cards.md"
CARDS = {
    match.group(1): match.group(2)
    for match in re.finditer(r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)", SOURCE.read_text())
}


def solution(problem, name):
    section = CARDS[problem].split("## Code", 1)[1].split("## Complexity", 1)[0]
    code = re.search(r"```python\n(.*?)\n```", section, re.S).group(1)
    namespace = {}
    exec(compile(code, f"card-{problem}", "exec"), namespace)
    return namespace[name]


def components(n, edges):
    neighbours = [[] for _ in range(n)]
    for u, v in edges:
        neighbours[u].append(v)
        neighbours[v].append(u)
    seen = set()
    sizes = []
    for start in range(n):
        if start in seen:
            continue
        seen.add(start)
        pending = [start]
        size = 0
        while pending:
            u = pending.pop()
            size += 1
            for v in neighbours[u]:
                if v not in seen:
                    seen.add(v)
                    pending.append(v)
        sizes.append(size)
    return sizes


def connected(n, edges, start, end):
    neighbours = [[] for _ in range(n)]
    for u, v in edges:
        neighbours[u].append(v)
        neighbours[v].append(u)
    seen = {start}
    pending = [start]
    while pending:
        for v in neighbours[pending.pop()]:
            if v not in seen:
                seen.add(v)
                pending.append(v)
    return end in seen


class TestCards(unittest.TestCase):
    def test_provinces_against_graph_search(self):
        solve = solution("547", "count_provinces")
        rng = random.Random(547)
        for n in range(1, 13):
            for _ in range(50):
                matrix = [[int(i == j) for j in range(n)] for i in range(n)]
                edges = []
                for i, j in itertools.combinations(range(n), 2):
                    if rng.randrange(3) == 0:
                        matrix[i][j] = matrix[j][i] = 1
                        edges.append((i, j))
                self.assertEqual(solve(matrix), len(components(n, edges)))

    def test_redundant_edge_against_removal(self):
        solve = solution("684", "redundant_connection")
        rng = random.Random(684)
        for n in range(3, 10):
            for _ in range(80):
                edges = [(i, rng.randrange(i)) for i in range(1, n)]
                existing = {tuple(sorted(edge)) for edge in edges}
                extra = rng.choice([e for e in itertools.combinations(range(n), 2) if e not in existing])
                edges.append(extra)
                rng.shuffle(edges)
                expected = next(
                    edges[i]
                    for i in reversed(range(n))
                    if len(components(n, edges[:i] + edges[i + 1:])) == 1
                )
                labelled = [[u + 1, v + 1] for u, v in edges]
                self.assertEqual(solve(labelled), [expected[0] + 1, expected[1] + 1])

    def test_equations_against_equality_graph(self):
        solve = solution("990", "equations_possible")
        rng = random.Random(990)
        for _ in range(600):
            equations = [
                rng.choice("abcdef") + rng.choice(("==", "!=")) + rng.choice("abcdef")
                for _ in range(rng.randrange(20))
            ]
            eq_edges = [(ord(e[0]) - 97, ord(e[3]) - 97) for e in equations if e[1:3] == "=="]
            inequalities = [(ord(e[0]) - 97, ord(e[3]) - 97) for e in equations if e[1:3] == "!="]
            expected = all(len(components(6, eq_edges + [(u, v)])) < len(components(6, eq_edges))
                           for u, v in inequalities)
            self.assertEqual(solve(equations), expected)

    def test_prim_against_spanning_tree_enumeration(self):
        solve = solution("1584", "min_connect_cost")
        rng = random.Random(1584)
        self.assertEqual(solve([]), 0)
        for n in range(1, 6):
            for _ in range(40):
                points = rng.sample(list(itertools.product(range(-3, 4), repeat=2)), n)
                edges = list(itertools.combinations(range(n), 2))
                costs = {
                    (u, v): abs(points[u][0] - points[v][0]) + abs(points[u][1] - points[v][1])
                    for u, v in edges
                }
                expected = min(
                    sum(costs[edge] for edge in choice)
                    for choice in itertools.combinations(edges, n - 1)
                    if len(components(n, choice)) == 1
                )
                self.assertEqual(solve(points), expected)

    def test_roads_against_repeated_graph_search(self):
        solve = solution("cses:1676", "road_status")
        rng = random.Random(1676)
        for n in range(1, 13):
            for _ in range(40):
                roads = [(rng.randrange(n), rng.randrange(n)) for _ in range(25)]
                expected = []
                for i in range(len(roads)):
                    sizes = components(n, roads[:i + 1])
                    expected.append((len(sizes), max(sizes)))
                self.assertEqual(solve(n, [(u + 1, v + 1) for u, v in roads]), expected)

    def test_accounts_against_pairwise_graph(self):
        solve = solution("721", "merge_accounts")
        rng = random.Random(721)
        for _ in range(500):
            accounts = []
            for _ in range(rng.randrange(1, 12)):
                person = rng.randrange(4)
                name = "same" if person < 2 else str(person)
                emails = [f"{person}-{rng.randrange(4)}@example.test" for _ in range(rng.randrange(1, 5))]
                accounts.append([name, *emails])
            email_sets = [set(account[1:]) for account in accounts]
            edges = [(i, j) for i, j in itertools.combinations(range(len(accounts)), 2)
                     if email_sets[i] & email_sets[j]]
            adjacency = [set() for _ in accounts]
            for i, j in edges:
                adjacency[i].add(j)
                adjacency[j].add(i)
            expected = []
            seen = set()
            for i in range(len(accounts)):
                if i in seen:
                    continue
                seen.add(i)
                pending = [i]
                emails = set()
                while pending:
                    u = pending.pop()
                    emails.update(email_sets[u])
                    for v in adjacency[u] - seen:
                        seen.add(v)
                        pending.append(v)
                expected.append((accounts[i][0], *sorted(emails)))
            self.assertEqual(sorted(map(tuple, solve(accounts))), sorted(expected))

    def test_stones_against_pairwise_graph(self):
        solve = solution("947", "removable_stones")
        rng = random.Random(947)
        grid = list(itertools.product(range(-3, 4), repeat=2))
        for n in range(0, 15):
            for _ in range(50):
                stones = rng.sample(grid, n)
                edges = [(i, j) for i, j in itertools.combinations(range(n), 2)
                         if stones[i][0] == stones[j][0] or stones[i][1] == stones[j][1]]
                self.assertEqual(solve(stones), n - len(components(n, edges)))

    def test_road_mst_against_enumeration(self):
        solve = solution("cses:1675", "min_road_cost")
        rng = random.Random(1675)
        for n in range(1, 7):
            possible = list(itertools.combinations(range(n), 2))
            for _ in range(80):
                edges = rng.sample(possible, rng.randrange(min(len(possible), 10) + 1))
                roads = [(u, v, rng.randrange(1, 15)) for u, v in edges]
                candidates = [
                    sum(cost for _, _, cost in subset)
                    for subset in itertools.combinations(roads, n - 1)
                    if len(components(n, [(u, v) for u, v, _ in subset])) == 1
                ]
                expected = min(candidates) if candidates else None
                self.assertEqual(solve(n, [(u + 1, v + 1, c) for u, v, c in roads]), expected)

    def test_weighted_union_against_graph_search(self):
        solve = solution("399", "evaluate_ratios")
        rng = random.Random(399)
        names = [f"v{i}" for i in range(8)]
        for _ in range(300):
            underlying = {name: rng.randrange(1, 30) for name in names}
            pairs = rng.sample(list(itertools.combinations(names, 2)), rng.randrange(20))
            values = [underlying[a] / underlying[b] for a, b in pairs]
            graph = {}
            for (a, b), value in zip(pairs, values):
                graph.setdefault(a, []).append((b, value))
                graph.setdefault(b, []).append((a, 1 / value))
            queries = [(rng.choice(names + ["missing"]), rng.choice(names + ["missing"])) for _ in range(25)]
            expected = []
            for start, end in queries:
                if start not in graph or end not in graph:
                    expected.append(-1.0)
                    continue
                seen = {start}
                pending = [(start, 1.0)]
                found = -1.0
                while pending:
                    node, value = pending.pop()
                    if node == end:
                        found = value
                        break
                    for neighbour, ratio in graph[node]:
                        if neighbour not in seen:
                            seen.add(neighbour)
                            pending.append((neighbour, value * ratio))
                expected.append(found)
            for actual, wanted in zip(solve(pairs, values, queries), expected):
                self.assertAlmostEqual(actual, wanted)

    def test_offline_limits_against_search(self):
        solve = solution("1697", "limited_paths")
        rng = random.Random(1697)
        for n in range(1, 11):
            for _ in range(80):
                edges = [(rng.randrange(n), rng.randrange(n), rng.randrange(1, 8))
                         for _ in range(rng.randrange(20))]
                queries = [(rng.randrange(n), rng.randrange(n), rng.randrange(1, 9))
                           for _ in range(20)]
                expected = [
                    connected(n, [(a, b) for a, b, weight in edges if weight < limit], u, v)
                    for u, v, limit in queries
                ]
                self.assertEqual(solve(n, edges, queries), expected)

    def test_classification_against_all_spanning_trees(self):
        solve = solution("1489", "classify_mst_edges")
        rng = random.Random(1489)
        for n in range(2, 7):
            possible = list(itertools.combinations(range(n), 2))
            for _ in range(80):
                initial = {(rng.randrange(i), i) for i in range(1, n)}
                extra = [edge for edge in possible if edge not in initial]
                chosen = list(initial) + rng.sample(extra, rng.randrange(min(len(extra), 4) + 1))
                edges = [(u, v, rng.randrange(1, 5)) for u, v in chosen]
                trees = []
                for indices in itertools.combinations(range(len(edges)), n - 1):
                    if len(components(n, [(edges[i][0], edges[i][1]) for i in indices])) == 1:
                        trees.append((sum(edges[i][2] for i in indices), set(indices)))
                best = min(weight for weight, _ in trees)
                winners = [indices for weight, indices in trees if weight == best]
                critical = {i for i in range(len(edges)) if all(i in tree for tree in winners)}
                pseudo = {i for i in range(len(edges)) if any(i in tree for tree in winners)} - critical
                actual = solve(n, edges)
                self.assertEqual(set(actual[0]), critical)
                self.assertEqual(set(actual[1]), pseudo)

    def test_good_paths_against_unique_path_search(self):
        solve = solution("2421", "count_good_paths")
        rng = random.Random(2421)
        for n in range(1, 14):
            for _ in range(100):
                edges = [(rng.randrange(i), i) for i in range(1, n)]
                values = [rng.randrange(1, 5) for _ in range(n)]
                adjacency = [[] for _ in range(n)]
                for u, v in edges:
                    adjacency[u].append(v)
                    adjacency[v].append(u)
                expected = n
                for start in range(n):
                    pending = [(start, -1, values[start])]
                    while pending:
                        u, previous, maximum = pending.pop()
                        if u > start and values[u] == values[start] and maximum <= values[start]:
                            expected += 1
                        for v in adjacency[u]:
                            if v != previous:
                                pending.append((v, u, max(maximum, values[v])))
                self.assertEqual(solve(values, edges), expected)


if __name__ == "__main__":
    unittest.main()
