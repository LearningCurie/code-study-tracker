import itertools
import random
import re
import unittest
from collections import Counter, deque
from pathlib import Path


BUILD = Path(__file__).resolve().parents[2]
SOURCE = BUILD / "dsa" / "07-linear.cards.md"
MODULE = BUILD / "dsa" / "07-linear.md"
CARDS = dict(re.findall(
    r"(?ms)^=== card \| (\S+)\n(.*?)(?=^=== card \| |\Z)",
    SOURCE.read_text(),
))


def load_card(problem):
    blocks = re.findall(r"```python\n(.*?)\n```", CARDS[problem], re.S)
    if len(blocks) != 1:
        raise AssertionError(f"{problem}: expected exactly one Python block")
    namespace = {}
    exec(compile(blocks[0], f"card-{problem}", "exec"), namespace)
    return namespace


def make_nodes(cls, values):
    nodes = [cls(value) for value in values]
    for left, right in zip(nodes, nodes[1:]):
        left.next = right
    return nodes


def node_sequence(head, maximum):
    result = []
    while head is not None:
        if len(result) >= maximum:
            raise AssertionError("unexpected cycle or extra node")
        result.append(head)
        head = head.next
    return result


def bracket_oracle(text):
    while True:
        shorter = text.replace("()", "").replace("[]", "").replace("{}", "")
        if shorter == text:
            return not text
        text = shorter


def trunc_div(a, b):
    magnitude, _ = divmod(abs(a), abs(b))
    return -magnitude if a * b < 0 else magnitude


class TestLinearCards(unittest.TestCase):
    def test_exact_coverage_and_executable_blocks(self):
        practice = MODULE.read_text().split("=== practice\n", 1)[1]
        ids = re.findall(r"(?m)^- (\S+) (?:core|derive|stretch|mixed)$", practice)
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(ids), len(CARDS))
        self.assertEqual(set(ids), set(CARDS))
        for problem in ids:
            with self.subTest(problem=problem):
                load_card(problem)

    def test_reverse_against_list_reversal_and_identity(self):
        card = load_card("206")
        cls, solve = card["ListNode"], card["reverse_list"]
        for n in range(9):
            for values in itertools.product(range(2), repeat=n):
                nodes = make_nodes(cls, values)
                result = solve(nodes[0] if nodes else None)
                self.assertEqual(node_sequence(result, n), nodes[::-1])

    def test_merge_against_stable_sort_and_identity(self):
        card = load_card("21")
        cls, solve = card["ListNode"], card["merge_lists"]
        options = [values for n in range(5)
                   for values in itertools.combinations_with_replacement(range(3), n)]
        for left in options:
            for right in options:
                a, b = make_nodes(cls, left), make_nodes(cls, right)
                result = solve(a[0] if a else None, b[0] if b else None)
                expected = sorted(a + b, key=lambda node: node.val)
                self.assertEqual(node_sequence(result, len(expected)), expected)

    def test_cycle_detection_and_entry_against_visited_identities(self):
        for problem, name in (("141", "has_cycle"), ("142", "cycle_entry")):
            card = load_card(problem)
            cls, solve = card["ListNode"], card[name]
            self.assertEqual(solve(None), False if problem == "141" else None)
            for n in range(1, 25):
                for entry in range(-1, n):
                    nodes = make_nodes(cls, [1] * n)
                    if entry >= 0:
                        nodes[-1].next = nodes[entry]
                    before = [node.next for node in nodes]
                    seen = set()
                    cursor = nodes[0]
                    while cursor is not None and cursor not in seen:
                        seen.add(cursor)
                        cursor = cursor.next
                    result = solve(nodes[0])
                    if problem == "141":
                        self.assertIs(result, cursor is not None)
                    else:
                        self.assertIs(result, cursor)
                    self.assertEqual([node.next for node in nodes], before)

    def test_brackets_against_reduction_oracle(self):
        solve = load_card("20")["valid_brackets"]
        for n in range(7):
            for chars in itertools.product("()[]{}", repeat=n):
                text = "".join(chars)
                self.assertEqual(solve(text), bracket_oracle(text), text)
        self.assertTrue(solve("{[()]}"))
        self.assertFalse(solve("([)]"))

    def test_queue_against_deque(self):
        cls = load_card("232")["TwoStackQueue"]
        rng = random.Random(232)
        for _ in range(150):
            queue, oracle = cls(), deque()
            for _ in range(300):
                action = rng.randrange(4)
                if action == 0:
                    value = rng.randrange(-4, 5)
                    queue.push(value)
                    oracle.append(value)
                elif action == 1:
                    if oracle:
                        self.assertEqual(queue.pop(), oracle.popleft())
                    else:
                        with self.assertRaises(IndexError):
                            queue.pop()
                elif action == 2:
                    if oracle:
                        self.assertEqual(queue.peek(), oracle[0])
                    else:
                        with self.assertRaises(IndexError):
                            queue.peek()
                else:
                    self.assertEqual(queue.empty(), not oracle)
            self.assertEqual([queue.pop() for _ in range(len(oracle))], list(oracle))

    def test_remove_nth_against_array_deletion(self):
        card = load_card("19")
        cls, solve = card["ListNode"], card["remove_nth_from_end"]
        for length in range(1, 30):
            for n in range(1, length + 1):
                nodes = make_nodes(cls, [i % 3 for i in range(length)])
                expected = nodes[:length - n] + nodes[length - n + 1:]
                self.assertEqual(node_sequence(solve(nodes[0], n), length), expected)

    def test_decoder_generated_trees(self):
        solve = load_card("394")["decode_string"]
        rng = random.Random(394)

        def generate(depth):
            encoded, decoded = [], []
            for _ in range(rng.randrange(1, 4)):
                if depth and rng.random() < 0.55:
                    count = rng.choice((1, 2, 3, 10, 12))
                    inner, expanded = generate(depth - 1)
                    encoded.append(f"{count}[{inner}]")
                    decoded.append(expanded * count)
                else:
                    text = "".join(rng.choice("abc") for _ in range(rng.randrange(1, 4)))
                    encoded.append(text)
                    decoded.append(text)
            return "".join(encoded), "".join(decoded)

        self.assertEqual(solve("2[a3[b]]"), "abbbabbb")
        for _ in range(2500):
            encoded, expected = generate(3)
            self.assertEqual(solve(encoded), expected, encoded)
        self.assertEqual(solve("1[" * 1500 + "a" + "]" * 1500), "a")

    def test_postfix_against_generated_expression_tree(self):
        solve = load_card("150")["evaluate_postfix"]
        rng = random.Random(150)

        def generate(depth):
            if not depth or rng.random() < 0.3:
                value = rng.randrange(-20, 21)
                return [str(value)], value
            left, a = generate(depth - 1)
            right, b = generate(depth - 1)
            op = rng.choice("+-*/")
            if op == "/" and b == 0:
                right, b = ["1"], 1
            value = {"+": lambda: a + b, "-": lambda: a - b,
                     "*": lambda: a * b, "/": lambda: trunc_div(a, b)}[op]()
            return left + right + [op], value

        self.assertEqual(solve(["7", "3", "-", "2", "*"]), 8)
        for _ in range(5000):
            tokens, expected = generate(5)
            self.assertEqual(solve(tokens), expected, tokens)
        huge = 10 ** 400 + 17
        self.assertEqual(solve([str(-huge), "3", "/"]), trunc_div(-huge, 3))

    def test_duplicate_against_counts(self):
        solve = load_card("287")["find_duplicate"]
        for n in range(1, 6):
            for nums in itertools.product(range(1, n + 1), repeat=n + 1):
                counts = Counter(nums)
                duplicates = [value for value, count in counts.items() if count > 1]
                if len(duplicates) == 1:
                    before = list(nums)
                    argument = list(nums)
                    self.assertEqual(solve(argument), duplicates[0], nums)
                    self.assertEqual(argument, before)

    def test_calculator_against_generated_ast(self):
        solve = load_card("224")["calculate"]
        rng = random.Random(224)

        def generate(depth):
            if depth == 0 or rng.random() < 0.25:
                value = rng.randrange(100)
                return str(value), value
            mode = rng.randrange(3)
            if mode == 0:
                inner, value = generate(depth - 1)
                signs = "".join(rng.choice("+-") for _ in range(rng.randrange(1, 5)))
                return signs + "(" + inner + ")", value * (-1 if signs.count("-") % 2 else 1)
            left, a = generate(depth - 1)
            right, b = generate(depth - 1)
            op = rng.choice("+-")
            return "(" + left + " " + op + " " + right + ")", a + b if op == "+" else a - b

        for text, value in [("8-(3-(2+1))", 8), ("-(4-7)+2", 5),
                            ("5--2", 7), ("1-+-+2", 3), ("0", 0)]:
            self.assertEqual(solve(text), value)
        for _ in range(5000):
            text, expected = generate(5)
            self.assertEqual(solve(text), expected, text)
        self.assertEqual(solve("(" * 2000 + "-42" + ")" * 2000), -42)

    def test_group_reversal_against_array_slices_and_identity(self):
        card = load_card("25")
        cls, solve = card["ListNode"], card["reverse_k_group"]
        for length in range(21):
            for k in range(1, 26):
                nodes = make_nodes(cls, [i % 3 for i in range(length)])
                expected = []
                for start in range(0, length, k):
                    group = nodes[start:start + k]
                    expected.extend(group[::-1] if len(group) == k else group)
                result = solve(nodes[0] if nodes else None, k)
                self.assertEqual(node_sequence(result, length), expected)
        for k in (0, -1):
            with self.assertRaises(ValueError):
                solve(None, k)


if __name__ == "__main__":
    unittest.main()
