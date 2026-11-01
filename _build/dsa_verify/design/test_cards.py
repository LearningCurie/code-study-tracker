import collections
import random
import re
import unittest
from pathlib import Path
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "27-design.cards.md"
TEXT = SOURCE.read_text(encoding="utf-8")
CARDS = dict(re.findall(r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)", TEXT))
IDS = {"705", "933", "622", "1396", "146", "380",
       "284", "2034", "460", "432", "381", "2276"}


def solution(problem, name):
    blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"expected exactly one Python block for {problem}")
    namespace = {}
    exec(compile(blocks[0], f"card-{problem}", "exec"), namespace)
    return namespace[name]


class DesignCardTests(unittest.TestCase):
    def test_inventory_and_code_blocks(self):
        self.assertEqual(set(CARDS), IDS)
        self.assertEqual(len(re.findall(r"```python\n", TEXT)), len(IDS))
        for problem in IDS:
            blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
            self.assertEqual(len(blocks), 1, problem)
            exec(compile(blocks[0], f"card-{problem}", "exec"), {})

    def test_705_against_builtin_set(self):
        store = solution("705", "MyHashSet")()
        model = set()
        rng = random.Random(705)
        keys = [0, 1, 999_999, 1_000_000] + list(range(30))
        for _ in range(2500):
            key = rng.choice(keys)
            operation = rng.choice(("add", "remove", "contains"))
            if operation == "add":
                store.add(key)
                model.add(key)
            elif operation == "remove":
                store.remove(key)
                model.discard(key)
            else:
                self.assertEqual(store.contains(key), key in model)
            for candidate in keys:
                self.assertEqual(store.contains(candidate), candidate in model)

    def test_933_against_history_scan(self):
        cls = solution("933", "RecentCounter")
        for times in ([1, 1000, 3001, 3002, 6002, 10000],
                      list(range(1, 200)),
                      [1, 3001, 6001, 9001]):
            counter = cls()
            history = []
            for t in times:
                history.append(t)
                self.assertEqual(counter.ping(t), sum(t - 3000 <= x <= t for x in history))
        rng = random.Random(933)
        counter = cls()
        history = []
        t = 0
        for _ in range(2000):
            t += rng.randint(1, 1200)
            history.append(t)
            self.assertEqual(counter.ping(t), sum(t - 3000 <= x <= t for x in history))

    def test_622_against_fifo_list(self):
        cls = solution("622", "MyCircularQueue")
        rng = random.Random(622)
        for capacity in range(1, 7):
            queue, model = cls(capacity), []
            for _ in range(2500):
                if rng.randrange(2):
                    value = rng.randrange(6)
                    result = queue.enQueue(value)
                    expected = len(model) < capacity
                    if expected:
                        model.append(value)
                else:
                    result = queue.deQueue()
                    expected = bool(model)
                    if expected:
                        model.pop(0)
                self.assertEqual(result, expected)
                self.assertEqual(queue.Front(), model[0] if model else -1)
                self.assertEqual(queue.Rear(), model[-1] if model else -1)
                self.assertEqual(queue.isEmpty(), not model)
                self.assertEqual(queue.isFull(), len(model) == capacity)

    def test_1396_against_completed_trip_history(self):
        system = solution("1396", "UndergroundSystem")()
        rng = random.Random(1396)
        active, history = {}, []
        stations = ["Oak", "Pine", "Maple"]
        time = 0
        for _ in range(2500):
            time += rng.randrange(1, 5)
            rider = rng.randrange(8)
            station = rng.choice(stations)
            if rider not in active:
                system.checkIn(rider, station, time)
                active[rider] = (station, time)
            else:
                start, entered = active.pop(rider)
                system.checkOut(rider, station, time)
                history.append((start, station, time - entered))
            pairs = {(start, end) for start, end, _ in history}
            for start, end in pairs:
                durations = [duration for a, b, duration in history if (a, b) == (start, end)]
                self.assertAlmostEqual(system.getAverageTime(start, end), sum(durations) / len(durations))

    def test_146_against_clock_model(self):
        cls = solution("146", "LRUCache")
        rng = random.Random(146)
        for capacity in range(5):
            cache, values, last = cls(capacity), {}, {}
            for clock in range(4000):
                key = rng.randrange(7)
                if rng.randrange(2):
                    expected = values.get(key, -1)
                    if key in values:
                        last[key] = clock
                    self.assertEqual(cache.get(key), expected)
                else:
                    value = rng.randrange(20)
                    if capacity:
                        if key not in values and len(values) == capacity:
                            victim = min(values, key=lambda x: last[x])
                            del values[victim]
                            del last[victim]
                        values[key] = value
                        last[key] = clock
                    cache.put(key, value)
                self.assertEqual(dict(cache.items), values)

    def test_380_against_set_and_uniform_slots(self):
        cls = solution("380", "RandomizedSet")
        store, model = cls(), set()
        rng = random.Random(380)
        for _ in range(3000):
            val = rng.randrange(-4, 5)
            if rng.randrange(2):
                expected = val not in model
                self.assertEqual(store.insert(val), expected)
                model.add(val)
            else:
                expected = val in model
                self.assertEqual(store.remove(val), expected)
                model.discard(val)
            self.assertEqual(len(store.values), len(model))
            self.assertEqual(set(store.values), model)
            self.assertEqual(store.index, {value: i for i, value in enumerate(store.values)})
            if model:
                sampled = []
                for i in range(len(model)):
                    with patch("random.choice", side_effect=lambda seq, i=i: seq[i]) as choice:
                        sampled.append(store.getRandom())
                        choice.assert_called_once_with(store.values)
                self.assertEqual(set(sampled), model)

    def test_284_against_list_cursor_and_lazy_source(self):
        cls = solution("284", "PeekingIterator")
        for values in ([], [None], [0, False, None, 4], list(range(15))):
            reads = []

            def source():
                for value in values:
                    reads.append(value)
                    yield value

            iterator = cls(source())
            self.assertEqual(reads, values[:1])
            for i, value in enumerate(values):
                self.assertTrue(iterator.hasNext())
                self.assertTrue(iterator.hasNext())
                self.assertEqual(iterator.peek(), value)
                self.assertEqual(iterator.peek(), value)
                self.assertEqual(reads, values[:i + 1])
                self.assertEqual(iterator.next(), value)
                self.assertEqual(reads, values[:i + 2])
            self.assertFalse(iterator.hasNext())
            with self.assertRaises(StopIteration):
                iterator.peek()
            with self.assertRaises(StopIteration):
                iterator.next()

    def test_2034_against_dictionary_scan(self):
        cls = solution("2034", "StockPrice")
        stock, prices = cls(), {}
        for timestamp, price in [(2, 9), (5, 4), (2, 1), (2, 9), (2, 1), (5, 1)]:
            stock.update(timestamp, price)
            prices[timestamp] = price
            self.assertEqual(stock.current(), prices[max(prices)])
            self.assertEqual(stock.minimum(), min(prices.values()))
            self.assertEqual(stock.maximum(), max(prices.values()))
        rng = random.Random(2034)
        for _ in range(5000):
            timestamp, price = rng.randint(1, 12), rng.randint(1, 15)
            stock.update(timestamp, price)
            prices[timestamp] = price
            self.assertEqual(stock.current(), prices[max(prices)])
            self.assertEqual(stock.minimum(), min(prices.values()))
            self.assertEqual(stock.maximum(), max(prices.values()))

    def test_460_against_frequency_and_clock_model(self):
        cls = solution("460", "LFUCache")
        rng = random.Random(460)
        for capacity in range(5):
            cache, model = cls(capacity), {}
            for clock in range(7000):
                key = rng.randrange(7)
                if rng.randrange(2):
                    expected = model[key][0] if key in model else -1
                    if key in model:
                        value, freq, _ = model[key]
                        model[key] = (value, freq + 1, clock)
                    self.assertEqual(cache.get(key), expected)
                else:
                    value = rng.randrange(20)
                    if capacity:
                        if key in model:
                            _, freq, _ = model[key]
                            model[key] = (value, freq + 1, clock)
                        else:
                            if len(model) == capacity:
                                victim = min(model, key=lambda k: (model[k][1], model[k][2]))
                                del model[victim]
                            model[key] = (value, 1, clock)
                    cache.put(key, value)
                self.assertEqual(cache.entries,
                                 {k: (value, freq) for k, (value, freq, _) in model.items()})
                self.assertEqual(set(cache.buckets), {entry[1] for entry in model.values()})
                for freq, bucket in cache.buckets.items():
                    expected_order = sorted((k for k in model if model[k][1] == freq),
                                            key=lambda k: model[k][2])
                    self.assertEqual(list(bucket), expected_order)
                if model:
                    self.assertEqual(cache.min_freq, min(entry[1] for entry in model.values()))

    def test_432_against_count_scan(self):
        cls = solution("432", "AllOne")
        structure, counts = cls(), {}
        rng = random.Random(432)
        self.assertEqual(structure.getMinKey(), "")
        self.assertEqual(structure.getMaxKey(), "")
        for _ in range(12000):
            key = rng.choice(["red", "blue", "green", "gold", "white"])
            if key not in counts or rng.randrange(2):
                structure.inc(key)
                counts[key] = counts.get(key, 0) + 1
            else:
                structure.dec(key)
                counts[key] -= 1
                if not counts[key]:
                    del counts[key]
            if counts:
                self.assertIn(structure.getMinKey(), {k for k in counts if counts[k] == min(counts.values())})
                self.assertIn(structure.getMaxKey(), {k for k in counts if counts[k] == max(counts.values())})
            else:
                self.assertEqual(structure.getMinKey(), "")
                self.assertEqual(structure.getMaxKey(), "")
            node, previous, seen = structure.head.next, structure.head, {}
            while node is not structure.tail:
                self.assertIs(node.prev, previous)
                self.assertGreater(node.count, previous.count)
                self.assertTrue(node.keys)
                for k in node.keys:
                    self.assertNotIn(k, seen)
                    seen[k] = node.count
                    self.assertIs(structure.where[k], node)
                previous, node = node, node.next
            self.assertIs(structure.tail.prev, previous)
            self.assertEqual(seen, counts)

    def test_381_against_multiset_and_uniform_slots(self):
        cls = solution("381", "RandomizedCollection")
        store, model = cls(), collections.Counter()
        rng = random.Random(381)
        selected = [0]
        with patch("random.choice", side_effect=lambda seq: seq[selected[0]]) as choice:
            for step in range(4500):
                val = rng.randrange(-3, 4)
                if rng.randrange(2):
                    expected = model[val] == 0
                    self.assertEqual(store.insert(val), expected)
                    model[val] += 1
                else:
                    expected = model[val] > 0
                    self.assertEqual(store.remove(val), expected)
                    if expected:
                        model[val] -= 1
                        if not model[val]:
                            del model[val]
                self.assertEqual(collections.Counter(store.values), model)
                indices = {}
                for i, value in enumerate(store.values):
                    indices.setdefault(value, set()).add(i)
                self.assertEqual(store.indices, indices)
                if store.values:
                    positions = range(len(store.values)) if step % 100 == 0 else [rng.randrange(len(store.values))]
                    for i in positions:
                        selected[0] = i
                        self.assertEqual(store.getRandom(), store.values[i])
                        choice.assert_called_with(store.values)

    def test_2276_against_integer_set_and_large_boundaries(self):
        cls = solution("2276", "CountIntervals")
        store, covered = cls(), set()
        self.assertEqual(store.count(), 0)
        rng = random.Random(2276)
        for _ in range(1000):
            left = rng.randint(1, 90)
            right = rng.randint(left, 100)
            store.add(left, right)
            covered.update(range(left, right + 1))
            self.assertEqual(store.count(), len(covered))
        store = cls()
        for left, right, expected in [(1, 1, 1), (1_000_000_000, 1_000_000_000, 2),
                                      (2, 999_999_999, 1_000_000_000),
                                      (50, 100, 1_000_000_000),
                                      (1, 1_000_000_000, 1_000_000_000)]:
            store.add(left, right)
            self.assertEqual(store.count(), expected)
        for _ in range(120):
            store, covered = cls(), set()
            for _ in range(40):
                left = rng.randint(1, 40)
                right = rng.randint(left, 50)
                store.add(left, right)
                covered.update(range(left, right + 1))
                self.assertEqual(store.count(), len(covered))


if __name__ == "__main__":
    unittest.main()
