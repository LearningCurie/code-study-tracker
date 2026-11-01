import itertools
import random
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "15-intervals.cards.md"
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


def make_intervals(rng, count):
    return [sorted((rng.randrange(-10, 11), rng.randrange(-10, 11))) for _ in range(count)]


def pairwise_merge(intervals):
    blocks = [interval[:] for interval in intervals]
    while True:
        pair = next(((i, j) for i in range(len(blocks)) for j in range(i + 1, len(blocks))
                     if max(blocks[i][0], blocks[j][0]) <= min(blocks[i][1], blocks[j][1])), None)
        if pair is None:
            return sorted(blocks)
        i, j = pair
        blocks[i] = [min(blocks[i][0], blocks[j][0]), max(blocks[i][1], blocks[j][1])]
        blocks.pop(j)


def disjoint_intervals(rng, count):
    result = []
    start = rng.randrange(-20, -10)
    for _ in range(count):
        end = start + rng.randrange(4)
        result.append([start, end])
        start = end + rng.randrange(1, 5)
    return result


class TestIntervalCards(unittest.TestCase):
    def test_covered_points_against_set(self):
        solve = solution("2848", "covered_points")
        rng = random.Random(2848)
        for n in range(20):
            for _ in range(50):
                intervals = make_intervals(rng, n)
                expected = len({point for left, right in intervals for point in range(left, right + 1)})
                self.assertEqual(solve(intervals), expected)

    def test_population_against_year_scan(self):
        solve = solution("1854", "maximum_population_year")
        rng = random.Random(1854)
        for _ in range(500):
            logs = []
            for _ in range(rng.randrange(1, 25)):
                birth = rng.randrange(1950, 2050)
                logs.append((birth, rng.randrange(birth + 1, 2051)))
            population = [sum(birth <= year < death for birth, death in logs)
                          for year in range(1950, 2050)]
            expected = 1950 + population.index(max(population))
            self.assertEqual(solve(logs), expected)

    def test_merge_against_pairwise_union(self):
        solve = solution("56", "merge_intervals")
        rng = random.Random(56)
        for n in range(20):
            for _ in range(70):
                intervals = make_intervals(rng, n)
                self.assertEqual(solve(intervals), pairwise_merge(intervals))

    def test_intersections_against_pairwise_comparison(self):
        solve = solution("986", "interval_intersections")
        rng = random.Random(986)
        for _ in range(1000):
            first = disjoint_intervals(rng, rng.randrange(10))
            second = disjoint_intervals(rng, rng.randrange(10))
            expected = sorted([max(a, c), min(b, d)] for a, b in first for c, d in second
                              if max(a, c) <= min(b, d))
            self.assertEqual(solve(first, second), expected)

    def test_insert_against_pairwise_union(self):
        solve = solution("57", "insert_interval")
        rng = random.Random(57)
        for _ in range(1000):
            intervals = disjoint_intervals(rng, rng.randrange(10))
            new = sorted((rng.randrange(-25, 30), rng.randrange(-25, 30)))
            original = [row[:] for row in intervals]
            original_new = new[:]
            self.assertEqual(solve(intervals, new), pairwise_merge(intervals + [new]))
            self.assertEqual(intervals, original)
            self.assertEqual(new, original_new)

    def test_calendar_against_linear_overlap_scan(self):
        calendar = solution("729", "MyCalendar")
        rng = random.Random(729)
        for _ in range(100):
            instance = calendar()
            accepted = []
            for _ in range(100):
                start = rng.randrange(100)
                end = start + rng.randrange(1, 15)
                expected = all(not (start < old_end and old_start < end) for old_start, old_end in accepted)
                self.assertEqual(instance.book(start, end), expected)
                if expected:
                    accepted.append((start, end))

    def test_group_count_against_maximum_overlap(self):
        solve = solution("2406", "minimum_interval_groups")
        rng = random.Random(2406)
        for n in range(20):
            for _ in range(70):
                intervals = make_intervals(rng, n)
                expected = max([0] + [sum(start <= x <= end for start, end in intervals)
                                      for x in range(-10, 11)])
                self.assertEqual(solve(intervals), expected)

    def test_arrows_against_endpoint_subsets(self):
        solve = solution("452", "minimum_arrows")
        rng = random.Random(452)
        for n in range(8):
            for _ in range(100):
                intervals = make_intervals(rng, n)
                endpoints = sorted({end for _, end in intervals})
                expected = next(
                    count for count in range(len(endpoints) + 1)
                    if any(all(any(start <= point <= end for point in choice) for start, end in intervals)
                           for choice in itertools.combinations(endpoints, count))
                )
                self.assertEqual(solve(intervals), expected)

    def test_removals_against_subsets(self):
        solve = solution("435", "minimum_interval_removals")
        rng = random.Random(435)
        for n in range(9):
            for _ in range(100):
                intervals = []
                for _ in range(n):
                    start = rng.randrange(-10, 10)
                    intervals.append([start, start + rng.randrange(1, 8)])
                best = 0
                for count in range(n + 1):
                    for subset in itertools.combinations(intervals, count):
                        ordered = sorted(subset)
                        if all(ordered[i][1] <= ordered[i + 1][0] for i in range(len(ordered) - 1)):
                            best = max(best, count)
                self.assertEqual(solve(intervals), n - best)

    def test_room_allocation_against_overlap_lower_bound(self):
        solve = solution("cses:1164", "allocate_rooms")
        rng = random.Random(1164)
        for n in range(20):
            for _ in range(70):
                stays = make_intervals(rng, n)
                rooms, assignments = solve(stays)
                self.assertEqual(len(assignments), n)
                expected = max([0] + [sum(start <= day <= end for start, end in stays)
                                      for day in range(-10, 11)])
                self.assertEqual(rooms, expected)
                self.assertTrue(all(1 <= room <= rooms for room in assignments))
                for i, j in itertools.combinations(range(n), 2):
                    if max(stays[i][0], stays[j][0]) <= min(stays[i][1], stays[j][1]):
                        self.assertNotEqual(assignments[i], assignments[j])

    def test_minimum_cover_against_full_scan(self):
        solve = solution("1851", "minimum_covering_intervals")
        rng = random.Random(1851)
        for n in range(20):
            for _ in range(80):
                intervals = make_intervals(rng, n)
                queries = [rng.randrange(-15, 16) for _ in range(rng.randrange(20))]
                expected = [
                    min([end - start + 1 for start, end in intervals if start <= query <= end], default=-1)
                    for query in queries
                ]
                self.assertEqual(solve(intervals, queries), expected)

    def test_skyline_against_endpoint_scan(self):
        solve = solution("218", "skyline")
        rng = random.Random(218)
        for n in range(20):
            for _ in range(80):
                buildings = []
                for _ in range(n):
                    left = rng.randrange(-10, 11)
                    buildings.append([left, left + rng.randrange(1, 10), rng.randrange(1, 11)])
                points = sorted({x for left, right, _ in buildings for x in (left, right)})
                expected = []
                previous = 0
                for x in points:
                    height = max([0] + [height for left, right, height in buildings if left <= x < right])
                    if height != previous:
                        expected.append([x, height])
                        previous = height
                self.assertEqual(solve(buildings), expected)


if __name__ == "__main__":
    unittest.main()
