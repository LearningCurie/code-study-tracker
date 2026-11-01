import itertools
import math
import random
import re
import unittest
from collections import Counter, deque
from pathlib import Path


BUILD = Path(__file__).resolve().parents[2]
EXPECTED = {
    "01-method": {"1929", "1480", "1512", "1365", "1913", "169"},
    "02-cost": {"1732", "2073", "2215", "557", "119", "1656", "1351", "1588", "1381"},
}


def extract_cards():
    cards = {}
    for module, expected in EXPECTED.items():
        text = (BUILD / "dsa" / f"{module}.cards.md").read_text(encoding="utf-8")
        chunks = re.split(r"(?m)^=== card \| (\S+)\s*\n", text)
        if chunks[0].strip():
            raise AssertionError(f"unexpected text before {module} cards")
        found = set()
        for problem, body in zip(chunks[1::2], chunks[2::2]):
            if problem in found or problem in cards:
                raise AssertionError(f"duplicate card {problem}")
            found.add(problem)
            blocks = re.findall(r"```python\n(.*?)\n```", body, re.S)
            if len(blocks) != 1:
                raise AssertionError(f"{problem} must have exactly one tested Python block")
            code_section = body.split("## Code\n", 1)[1].split("## Complexity\n", 1)[0]
            if blocks[0] not in code_section:
                raise AssertionError(f"{problem} block is not in its Code section")
            namespace = {}
            exec(compile(blocks[0], f"{module}-card-{problem}", "exec"), namespace)
            cards[problem] = namespace
        if found != expected:
            raise AssertionError(f"{module} card coverage: {found ^ expected}")
    return cards


CARDS = extract_cards()


def lists(values, maximum):
    for n in range(maximum + 1):
        for items in itertools.product(values, repeat=n):
            yield list(items)


class FoundationCards(unittest.TestCase):
    def test_1929_concatenation(self):
        solve = CARDS["1929"]["concatenate"]
        for nums in lists([-1, 0, 1], 6):
            before = nums[:]
            result = solve(nums)
            self.assertEqual(result, [nums[i % len(nums)] for i in range(2 * len(nums))])
            self.assertEqual(nums, before)
            self.assertIsNot(result, nums)

    def test_1480_running_sums(self):
        solve = CARDS["1480"]["running_sum"]
        for nums in lists([-2, 0, 3], 6):
            before = nums[:]
            self.assertEqual(solve(nums), [sum(nums[:i + 1]) for i in range(len(nums))])
            self.assertEqual(nums, before)

    def test_1512_equal_pairs(self):
        solve = CARDS["1512"]["count_equal_pairs"]
        for nums in lists([-1, 0, 1], 7):
            oracle = sum(nums[i] == nums[j] for i in range(len(nums)) for j in range(i + 1, len(nums)))
            self.assertEqual(solve(nums), oracle)

    def test_1365_strictly_smaller(self):
        solve = CARDS["1365"]["count_smaller"]
        for nums in lists([0, 1, 42, 100], 5):
            self.assertEqual(solve(nums), [sum(other < value for other in nums) for value in nums])

    def test_1913_four_distinct_positions(self):
        solve = CARDS["1913"]["max_product_difference"]
        for n in range(4, 7):
            for nums in itertools.product([1, 2, 3], repeat=n):
                oracle = max(nums[a] * nums[b] - nums[c] * nums[d]
                             for a, b, c, d in itertools.permutations(range(n), 4))
                self.assertEqual(solve(nums), oracle, nums)

    def test_169_majority(self):
        solve = CARDS["169"]["majority_element"]
        for nums in lists([-1, 0, 1], 7):
            counts = Counter(nums)
            majority = [value for value, count in counts.items() if count > len(nums) // 2]
            if majority:
                self.assertEqual(solve(nums), majority[0], nums)

    def test_1732_highest_altitude(self):
        solve = CARDS["1732"]["highest_altitude"]
        for gain in lists([-2, 0, 3], 7):
            self.assertEqual(solve(gain), max(sum(gain[:i]) for i in range(len(gain) + 1)))

    def test_2073_queue_simulation(self):
        solve = CARDS["2073"]["ticket_time"]
        for n in range(1, 6):
            for tickets in itertools.product(range(1, 4), repeat=n):
                for k in range(n):
                    remaining = list(tickets)
                    queue = deque(range(n))
                    elapsed = 0
                    while True:
                        person = queue.popleft()
                        remaining[person] -= 1
                        elapsed += 1
                        if remaining[person]:
                            queue.append(person)
                        elif person == k:
                            break
                    self.assertEqual(solve(tickets, k), elapsed, (tickets, k))

    def test_2215_list_membership_oracle(self):
        solve = CARDS["2215"]["distinct_differences"]
        inputs = list(lists([-1, 0, 1], 4))
        for first in inputs:
            for second in inputs:
                answer = solve(first, second)
                expected = ([x for x in first if x not in second], [x for x in second if x not in first])
                self.assertEqual(len(answer), 2)
                for actual, wanted in zip(answer, expected):
                    self.assertEqual(set(actual), set(wanted))
                    self.assertEqual(len(actual), len(set(actual)))

    def test_557_character_scan(self):
        solve = CARDS["557"]["reverse_words"]
        for chars in lists(["a", "b", " "], 7):
            text = "".join(chars)
            out = []
            word = []
            for char in text + " ":
                if char == " ":
                    out.extend(reversed(word))
                    out.append(" ")
                    word.clear()
                else:
                    word.append(char)
            out.pop()
            self.assertEqual(solve(text), "".join(out), repr(text))
        self.assertEqual(solve("αβ  中文"), "βα  文中")

    def test_119_binomial_coefficients(self):
        solve = CARDS["119"]["pascal_row"]
        for k in range(101):
            self.assertEqual(solve(k), [math.comb(k, j) for j in range(k + 1)])

    def test_1656_every_small_arrival_order(self):
        stream_type = CARDS["1656"]["OrderedStream"]
        for n in range(1, 7):
            values = [None] + ["" if i == 2 else f"value-{i}" for i in range(1, n + 1)]
            for order in itertools.permutations(range(1, n + 1)):
                stream = stream_type(n)
                arrived = set()
                emitted = set()
                for position in order:
                    arrived.add(position)
                    expected = []
                    while len(emitted) + 1 in arrived:
                        next_position = len(emitted) + 1
                        emitted.add(next_position)
                        expected.append(values[next_position])
                    self.assertEqual(stream.insert(position, values[position]), expected, (n, order, position))

    def test_1351_sorted_matrices(self):
        solve = CARDS["1351"]["count_negatives"]
        self.assertEqual(solve([]), 0)
        self.assertEqual(solve([[], []]), 0)
        for rows in range(1, 4):
            for columns in range(1, 4):
                for values in itertools.product([-1, 0, 1], repeat=rows * columns):
                    grid = [values[i * columns:(i + 1) * columns] for i in range(rows)]
                    if any(grid[r][c] < grid[r][c + 1] for r in range(rows) for c in range(columns - 1)):
                        continue
                    if any(grid[r][c] < grid[r + 1][c] for r in range(rows - 1) for c in range(columns)):
                        continue
                    expected = sum(value < 0 for value in values)
                    self.assertEqual(solve(grid), expected, grid)

    def test_1588_odd_ranges(self):
        solve = CARDS["1588"]["odd_subarray_sum"]
        for nums in lists([-2, 0, 3], 7):
            expected = sum(sum(nums[start:end]) for start in range(len(nums))
                           for end in range(start + 1, len(nums) + 1) if (end - start) % 2)
            self.assertEqual(solve(nums), expected)

    def test_1381_stack_against_eager_simulation(self):
        stack_type = CARDS["1381"]["CustomStack"]
        rng = random.Random(1381)
        for capacity in range(7):
            for _ in range(100):
                stack = stack_type(capacity)
                reference = []
                for _ in range(200):
                    operation = rng.choice(("push", "pop", "increment"))
                    if operation == "push":
                        value = rng.randrange(-8, 9)
                        stack.push(value)
                        if len(reference) < capacity:
                            reference.append(value)
                    elif operation == "pop":
                        expected = reference.pop() if reference else -1
                        self.assertEqual(stack.pop(), expected)
                    else:
                        k = rng.randrange(capacity + 4)
                        value = rng.randrange(-8, 9)
                        stack.increment(k, value)
                        for i in range(min(k, len(reference))):
                            reference[i] += value
                while reference:
                    self.assertEqual(stack.pop(), reference.pop())
                self.assertEqual(stack.pop(), -1)


if __name__ == "__main__":
    unittest.main()
