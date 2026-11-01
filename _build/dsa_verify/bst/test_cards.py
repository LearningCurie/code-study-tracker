import random
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "dsa" / "17-bst.cards.md"
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


class Node:
    def __init__(self, value):
        self.val = value
        self.left = None
        self.right = None


def make_tree(values):
    root = None
    nodes = {}
    for value in values:
        new = nodes[value] = Node(value)
        if root is None:
            root = new
            continue
        node = root
        while True:
            side = "left" if value < node.val else "right"
            child = getattr(node, side)
            if child is None:
                setattr(node, side, new)
                break
            node = child
    return root, nodes


def all_nodes(root):
    result = []
    todo = [root] if root else []
    while todo:
        node = todo.pop()
        result.append(node)
        if node.left:
            todo.append(node.left)
        if node.right:
            todo.append(node.right)
    return result


class TestBSTCards(unittest.TestCase):
    def test_search_against_full_traversal(self):
        search = solution("700", "search_bst")
        rng = random.Random(700)
        self.assertIsNone(search(None, 1))
        for n in range(1, 45):
            root, _ = make_tree(rng.sample(range(-100, 100), n))
            for key in rng.sample(range(-100, 100), 20):
                expected = next((node for node in all_nodes(root) if node.val == key), None)
                self.assertIs(search(root, key), expected)

    def test_range_sum_against_full_traversal(self):
        solve = solution("938", "range_sum_bst")
        rng = random.Random(938)
        self.assertEqual(solve(None, 0, 5), 0)
        for n in range(1, 45):
            root, _ = make_tree(rng.sample(range(-100, 100), n))
            for _ in range(20):
                low, high = sorted(rng.sample(range(-100, 100), 2))
                expected = sum(node.val for node in all_nodes(root) if low <= node.val <= high)
                self.assertEqual(solve(root, low, high), expected)

    def test_sorted_array_builds_balanced_bst(self):
        build = solution("108", "sorted_array_to_bst")
        rng = random.Random(108)
        for n in range(100):
            values = sorted(rng.sample(range(-1000, 1000), n))
            root = build(values)

            def walk(node):
                if node is None:
                    return [], 0
                left, left_height = walk(node.left)
                right, right_height = walk(node.right)
                self.assertLessEqual(abs(left_height - right_height), 1)
                return left + [node.val] + right, 1 + max(left_height, right_height)

            actual, _ = walk(root)
            self.assertEqual(actual, values)

    def test_lca_against_parent_paths(self):
        solve = solution("235", "bst_lowest_common_ancestor")
        rng = random.Random(235)
        for n in range(2, 60):
            values = rng.sample(range(-1000, 1000), n)
            root, nodes = make_tree(values)
            parents = {root: None}
            for node in all_nodes(root):
                if node.left:
                    parents[node.left] = node
                if node.right:
                    parents[node.right] = node
            for _ in range(20):
                a, b = [nodes[value] for value in rng.sample(values, 2)]
                ancestors = set()
                current = a
                while current:
                    ancestors.add(current)
                    current = parents[current]
                current = b
                while current not in ancestors:
                    current = parents[current]
                self.assertIs(solve(root, a, b), current)

    def test_validate_against_full_subtree_checks(self):
        solve = solution("98", "is_valid_bst")
        rng = random.Random(98)
        self.assertTrue(solve(None))
        for n in range(1, 25):
            for _ in range(50):
                root = Node(rng.randrange(-10, 11))
                slots = [(root, "left"), (root, "right")]
                for _ in range(n - 1):
                    index = rng.randrange(len(slots))
                    parent, side = slots.pop(index)
                    node = Node(rng.randrange(-10, 11))
                    setattr(parent, side, node)
                    slots.extend([(node, "left"), (node, "right")])
                expected = all(
                    all(child.val < node.val for child in all_nodes(node.left))
                    and all(child.val > node.val for child in all_nodes(node.right))
                    for node in all_nodes(root)
                )
                self.assertEqual(solve(root), expected)

    def test_delete_preserves_order_and_all_other_nodes(self):
        solve = solution("450", "delete_bst")
        rng = random.Random(450)
        for n in range(1, 50):
            values = rng.sample(range(-100, 100), n)
            root, _ = make_tree(values)
            remaining = set(values)
            for key in rng.sample(range(-100, 100), 30):
                root = solve(root, key)
                remaining.discard(key)
                actual = [node.val for node in all_nodes(root)]
                self.assertEqual(sorted(actual), sorted(remaining))
                self.assertTrue(solution("98", "is_valid_bst")(root))

    def test_kth_against_sorted_values(self):
        solve = solution("230", "kth_smallest")
        rng = random.Random(230)
        for n in range(1, 50):
            values = rng.sample(range(-100, 100), n)
            root, _ = make_tree(values)
            for k, expected in enumerate(sorted(values), 1):
                self.assertEqual(solve(root, k), expected)
            with self.assertRaises(ValueError):
                solve(root, n + 1)

    def test_iterator_against_sorted_values(self):
        iterator = solution("173", "BSTIterator")
        rng = random.Random(173)
        for n in range(60):
            values = rng.sample(range(-100, 100), n)
            root, _ = make_tree(values)
            current = iterator(root)
            actual = []
            while current.has_next():
                actual.append(current.next())
            self.assertEqual(actual, sorted(values))
            with self.assertRaises(StopIteration):
                current.next()

    def test_recover_swapped_values_without_changing_shape(self):
        solve = solution("99", "recover_bst")
        rng = random.Random(99)
        for n in range(2, 60):
            for _ in range(20):
                values = rng.sample(range(-1000, 1000), n)
                root, nodes = make_tree(values)
                links = {node: (node.left, node.right) for node in all_nodes(root)}
                a, b = [nodes[value] for value in rng.sample(values, 2)]
                a.val, b.val = b.val, a.val
                solve(root)
                self.assertEqual(sorted(node.val for node in all_nodes(root)), sorted(values))
                self.assertTrue(solution("98", "is_valid_bst")(root))
                self.assertEqual({node: (node.left, node.right) for node in all_nodes(root)}, links)

    def test_trim_against_filtered_values(self):
        solve = solution("669", "trim_bst")
        rng = random.Random(669)
        for n in range(0, 60):
            for _ in range(20):
                values = rng.sample(range(-100, 100), n)
                root, _ = make_tree(values)
                low, high = sorted(rng.sample(range(-100, 100), 2))
                trimmed = solve(root, low, high)
                self.assertEqual(sorted(node.val for node in all_nodes(trimmed)),
                                 sorted(value for value in values if low <= value <= high))
                self.assertTrue(solution("98", "is_valid_bst")(trimmed))

    def test_maximum_bst_sum_against_subtree_enumeration(self):
        solve = solution("1373", "maximum_sum_bst")
        valid = solution("98", "is_valid_bst")
        rng = random.Random(1373)
        self.assertEqual(solve(None), 0)
        for n in range(1, 25):
            for _ in range(50):
                root = Node(rng.randrange(-10, 11))
                slots = [(root, "left"), (root, "right")]
                for _ in range(n - 1):
                    parent, side = slots.pop(rng.randrange(len(slots)))
                    node = Node(rng.randrange(-10, 11))
                    setattr(parent, side, node)
                    slots.extend([(node, "left"), (node, "right")])
                expected = max([0] + [sum(child.val for child in all_nodes(node))
                                      for node in all_nodes(root) if valid(node)])
                self.assertEqual(solve(root), expected)
        root, _ = make_tree(range(2000))
        self.assertEqual(solve(root), sum(range(2000)))

    def test_nearby_duplicate_against_all_pairs(self):
        solve = solution("220", "contains_nearby_almost_duplicate")
        rng = random.Random(220)
        for n in range(20):
            for _ in range(200):
                values = [rng.randrange(-30, 31) for _ in range(n)]
                index_diff = rng.randrange(10)
                value_diff = rng.randrange(10)
                expected = any(j - i <= index_diff and abs(values[i] - values[j]) <= value_diff
                               for i in range(n) for j in range(i + 1, n))
                self.assertEqual(solve(values, index_diff, value_diff), expected)
        self.assertTrue(solve([-10**100, -10**100 + 1], 1, 1))
        self.assertFalse(solve([1, 1], 0, 0))


if __name__ == "__main__":
    unittest.main()
