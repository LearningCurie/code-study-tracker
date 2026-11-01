"""Randomized checks execute the actual Python blocks from the tree cards."""

import ast
from collections import deque
from pathlib import Path
import random
import re
import sys
import unittest


BUILD = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BUILD))
import mdlite

SOURCE = BUILD / "dsa" / "16-trees.cards.md"
IDS = {"104", "110", "543", "94", "102", "1448", "437", "236",
       "105", "124", "297", "863"}
HEADINGS = (
    "## The problem", "## Constraints and what they imply", "## Brute force",
    "## The insight", "## Optimal solution, traced", "## Code", "## Complexity",
    "## Mistakes and edge cases", "## Variations",
)
MINIMUM = {"104": 220, "110": 220, "543": 220, "94": 220, "102": 380,
           "1448": 380, "437": 380, "236": 380, "105": 380, "124": 600,
           "297": 600, "863": 380}


def load_cards():
    source = SOURCE.read_text(encoding="utf-8")
    chunks = re.split(r"(?m)^=== card \| (\d+)\n", source)
    if chunks[0].strip():
        raise AssertionError("Unexpected content before cards")
    cards = {}
    for pid, text in zip(chunks[1::2], chunks[2::2]):
        if pid in cards:
            raise AssertionError(f"Duplicate card {pid}")
        cards[pid] = text
    return cards


CARDS = load_cards()
CODE = {}
for card_id, card in CARDS.items():
    blocks = re.findall(r"```python\n(.*?)\n```", card, re.S)
    if len(blocks) != 1:
        raise AssertionError(f"{card_id}: expected one Python block")
    namespace = {}
    exec(compile(blocks[0], f"card-{card_id}", "exec"), namespace)
    CODE[card_id] = namespace


class Node:
    def __init__(self, value):
        self.val = value
        self.left = None
        self.right = None


def make_tree(rng, size, unique=False):
    if not size:
        return None, []
    values = list(range(size)) if unique else [rng.randint(-5, 5) for _ in range(size)]
    rng.shuffle(values)
    nodes = [Node(value) for value in values]
    open_slots = [(nodes[0], "left"), (nodes[0], "right")]
    for node in nodes[1:]:
        i = rng.randrange(len(open_slots))
        parent, side = open_slots.pop(i)
        setattr(parent, side, node)
        open_slots.extend(((node, "left"), (node, "right")))
    return nodes[0], nodes


def parents_and_depths(root):
    if root is None:
        return {}, {}
    parent = {root: None}
    depth = {root: 1}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for child in (node.left, node.right):
            if child is not None:
                parent[child] = node
                depth[child] = depth[node] + 1
                queue.append(child)
    return parent, depth


def height(node):
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))


def recursive_inorder(node):
    if node is None:
        return []
    return recursive_inorder(node.left) + [node.val] + recursive_inorder(node.right)


def recursive_preorder(node):
    if node is None:
        return []
    return [node.val] + recursive_preorder(node.left) + recursive_preorder(node.right)


def tree_signature(node):
    if node is None:
        return None
    return (node.val, tree_signature(node.left), tree_signature(node.right))


def distances(start, parent):
    result = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in (node.left, node.right, parent[node]):
            if neighbor is not None and neighbor not in result:
                result[neighbor] = result[node] + 1
                queue.append(neighbor)
    return result


def brute_max_path(nodes, parent):
    best = None
    for start in nodes:
        stack = [(start, None, 0)]
        while stack:
            node, previous, total = stack.pop()
            total += node.val
            best = total if best is None else max(best, total)
            for neighbor in (node.left, node.right, parent[node]):
                if neighbor is not None and neighbor is not previous:
                    stack.append((neighbor, node, total))
    return best


def brute_path_count(nodes, target):
    count = 0
    for start in nodes:
        stack = [(start, 0)]
        while stack:
            node, total = stack.pop()
            total += node.val
            count += total == target
            for child in (node.left, node.right):
                if child is not None:
                    stack.append((child, total))
    return count


def ancestors(node, parent):
    result = []
    while node is not None:
        result.append(node)
        node = parent[node]
    return result


class CardTests(unittest.TestCase):
    def test_format_and_word_minimum(self):
        self.assertEqual(set(CARDS), IDS)
        for pid, card in CARDS.items():
            with self.subTest(card=pid):
                actual = re.findall(r"(?m)^## .+$", card)
                self.assertEqual(actual, list(HEADINGS))
                steps = re.findall(r"```steps\n(.*?)\n```", card, re.S)
                self.assertEqual(len(steps), 1)
                self.assertGreaterEqual(len(re.split(r"(?m)^---$", steps[0])), 2)
                code = re.search(r"```python\n(.*?)\n```", card, re.S).group(1)
                ast.parse(code)
                variations = card.split("## Variations", 1)[1]
                self.assertIn(len(re.findall(r"(?m)^- ", variations)), (2, 3, 4))
                prose = re.sub(r"```.*?```", " ", card, flags=re.S)
                words = len(re.findall(r"[A-Za-z0-9][\w'-]*", prose))
                self.assertGreaterEqual(words, MINIMUM[pid], f"{pid}: {words}")
                self.assertEqual(words, mdlite.plain(card))
                mdlite.render(card)

    def test_randomized_brute_force_comparisons(self):
        rng = random.Random(1601)
        for iteration in range(600):
            root, nodes = make_tree(rng, rng.randrange(15))
            parent, depths = parents_and_depths(root)
            with self.subTest(iteration=iteration, size=len(nodes)):
                self.assertEqual(CODE["104"]["max_depth"](root), max(depths.values(), default=0))
                balanced = all(abs(height(n.left) - height(n.right)) <= 1 for n in nodes)
                self.assertEqual(CODE["110"]["is_balanced"](root), balanced)
                diameter = max((max(distances(n, parent).values()) for n in nodes), default=0)
                self.assertEqual(CODE["543"]["diameter"](root), diameter)
                self.assertEqual(CODE["94"]["inorder"](root), recursive_inorder(root))
                # Node insertion order is not necessarily left-to-right.
                levels = [[n.val for n in parent if depths[n] == d]
                          for d in range(1, max(depths.values(), default=0) + 1)]
                self.assertEqual(CODE["102"]["level_order"](root), levels)
                good = sum(n.val >= max(a.val for a in ancestors(n, parent)) for n in nodes)
                self.assertEqual(CODE["1448"]["good_nodes"](root), good)
                target_sum = rng.randint(-10, 10)
                self.assertEqual(CODE["437"]["path_sum_count"](root, target_sum),
                                 brute_path_count(nodes, target_sum))
                if nodes:
                    self.assertEqual(CODE["124"]["max_path_sum"](root),
                                     brute_max_path(nodes, parent))
                    target = rng.choice(nodes)
                    k = rng.randrange(18)
                    expected = sorted(n.val for n, dist in distances(target, parent).items() if dist == k)
                    self.assertEqual(sorted(CODE["863"]["distance_k"](root, target, k)), expected)
                if len(nodes) >= 2:
                    p, q = rng.sample(nodes, 2)
                    p_ancestors = set(ancestors(p, parent))
                    expected = next(n for n in ancestors(q, parent) if n in p_ancestors)
                    self.assertIs(CODE["236"]["lowest_common_ancestor"](root, p, q), expected)

                codec = CODE["297"]["Codec"]()
                encoded = codec.serialize(root)
                self.assertEqual(tree_signature(codec.deserialize(encoded)), tree_signature(root))
                # Verify each direction against an independent recursive encoder.
                def reference_encode(node):
                    if node is None:
                        return ["#"]
                    return [str(node.val)] + reference_encode(node.left) + reference_encode(node.right)

                expected_encoding = ",".join(reference_encode(root))
                self.assertEqual(encoded, expected_encoding)
                self.assertEqual(tree_signature(codec.deserialize(expected_encoding)), tree_signature(root))

                unique_root, _ = make_tree(rng, len(nodes), unique=True)
                pre = recursive_preorder(unique_root)
                ino = recursive_inorder(unique_root)
                rebuilt = CODE["105"]["build_tree"](pre, ino)
                self.assertEqual(tree_signature(rebuilt), tree_signature(unique_root))

    def test_deep_chains_without_recursion(self):
        root, nodes = None, []
        for i in range(30000):
            node = Node(-1)
            node.left = root
            root = node
            nodes.append(node)
        self.assertEqual(CODE["104"]["max_depth"](root), 30000)
        self.assertFalse(CODE["110"]["is_balanced"](root))
        self.assertEqual(CODE["543"]["diameter"](root), 29999)
        self.assertEqual(len(CODE["94"]["inorder"](root)), 30000)
        self.assertEqual(len(CODE["102"]["level_order"](root)), 30000)
        self.assertEqual(CODE["1448"]["good_nodes"](root), 30000)
        self.assertEqual(CODE["437"]["path_sum_count"](root, -1), 30000)
        self.assertIs(CODE["236"]["lowest_common_ancestor"](root, nodes[0], nodes[15000]),
                      nodes[15000])
        self.assertEqual(CODE["124"]["max_path_sum"](root), -1)
        codec = CODE["297"]["Codec"]()
        self.assertEqual(CODE["104"]["max_depth"](codec.deserialize(codec.serialize(root))), 30000)
        pre = list(range(30000))
        built = CODE["105"]["build_tree"](pre, pre[::-1])
        self.assertEqual(CODE["104"]["max_depth"](built), 30000)
        self.assertEqual(CODE["863"]["distance_k"](root, nodes[0], 30000), [])

    def test_zero_and_negative_cases(self):
        root = Node(0)
        root.left = Node(0)
        root.right = Node(0)
        self.assertEqual(CODE["437"]["path_sum_count"](root, 0), 5)
        root.val, root.left.val, root.right.val = -5, -2, -3
        self.assertEqual(CODE["124"]["max_path_sum"](root), -2)
        self.assertEqual(CODE["1448"]["good_nodes"](root), 3)
        self.assertEqual(CODE["863"]["distance_k"](root, root, 0), [-5])


if __name__ == "__main__":
    unittest.main()
