"""Load cached LeetCode / doocs / NeetCode metadata and the curated problem list."""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
DIFF = {1: "Easy", 2: "Medium", 3: "Hard"}

# NeetCode renamed these practice pages; everything else uses the LeetCode slug.
NC_RENAMED = {
    "group-anagrams": "anagram-groups",
    "diameter-of-binary-tree": "binary-tree-diameter",
    "construct-binary-tree-from-preorder-and-inorder-traversal": "binary-tree-from-preorder-and-inorder-traversal",
    "best-time-to-buy-and-sell-stock": "buy-and-sell-crypto",
    "best-time-to-buy-and-sell-stock-with-cooldown": "buy-and-sell-crypto-with-cooldown",
    "cheapest-flights-within-k-stops": "cheapest-flight-path",
    "letter-combinations-of-a-phone-number": "combinations-of-a-phone-number",
    "combination-sum": "combination-target-sum",
    "combination-sum-ii": "combination-target-sum-ii",
    "copy-list-with-random-pointer": "copy-linked-list-with-random-pointer",
    "number-of-islands": "count-number-of-islands",
    "unique-paths": "count-paths",
    "palindromic-substrings": "count-squares",
    "distinct-subsequences": "count-subsequences",
    "maximum-depth-of-binary-tree": "depth-of-binary-tree",
    "design-twitter": "design-twitter-feed",
    "design-add-and-search-words-data-structure": "design-word-search-data-structure",
    "contains-duplicate": "duplicate-integer",
    "koko-eating-bananas": "eating-bananas",
    "find-the-duplicate-number": "find-duplicate-integer",
    "find-median-from-data-stream": "find-median-in-a-data-stream",
    "search-in-rotated-sorted-array": "find-target-in-rotated-sorted-array",
    "implement-trie-prefix-tree": "implement-prefix-tree",
    "insert-interval": "insert-new-interval",
    "invert-binary-tree": "invert-a-binary-tree",
    "valid-anagram": "is-anagram",
    "valid-palindrome": "is-palindrome",
    "kth-largest-element-in-a-stream": "kth-largest-integer-in-a-stream",
    "kth-smallest-element-in-a-bst": "kth-smallest-integer-in-bst",
    "binary-tree-level-order-traversal": "level-order-traversal-of-binary-tree",
    "linked-list-cycle": "linked-list-cycle-detection",
    "longest-increasing-path-in-a-matrix": "longest-increasing-path-in-matrix",
    "longest-repeating-character-replacement": "longest-repeating-substring-with-replacement",
    "longest-substring-without-repeating-characters": "longest-substring-without-duplicates",
    "lowest-common-ancestor-of-a-binary-search-tree": "lowest-common-ancestor-in-binary-search-tree",
    "container-with-most-water": "max-water-container",
    "merge-k-sorted-lists": "merge-k-sorted-linked-lists",
    "merge-triplets-to-form-target-triplet": "merge-triplets-to-form-target",
    "merge-two-sorted-lists": "merge-two-sorted-linked-lists",
    "min-cost-to-connect-all-points": "min-cost-to-connect-points",
    "minimum-interval-to-include-each-query": "minimum-interval-including-query",
    "min-stack": "minimum-stack",
    "minimum-window-substring": "minimum-window-with-characters",
    "happy-number": "non-cyclical-number",
    "number-of-1-bits": "number-of-one-bits",
    "permutation-in-string": "permutation-string",
    "powx-n": "pow-x-n",
    "product-of-array-except-self": "products-of-array-discluding-self",
    "reconstruct-itinerary": "reconstruct-flight-path",
    "remove-nth-node-from-end-of-list": "remove-node-from-end-of-linked-list",
    "reorder-list": "reorder-linked-list",
    "reverse-linked-list": "reverse-a-linked-list",
    "rotate-image": "rotate-matrix",
    "rotting-oranges": "rotting-fruit",
    "same-tree": "same-binary-tree",
    "search-a-2d-matrix": "search-2d-matrix",
    "word-search": "search-for-word",
    "word-search-ii": "search-for-word-ii",
    "set-matrix-zeroes": "set-zeroes-in-matrix",
    "subtree-of-another-tree": "subtree-of-a-binary-tree",
    "task-scheduler": "task-scheduling",
    "3sum": "three-integer-sum",
    "top-k-frequent-elements": "top-k-elements-in-list",
    "two-sum": "two-integer-sum",
    "two-sum-ii-input-array-is-sorted": "two-integer-sum-ii",
    "valid-parentheses": "validate-parentheses",
    "validate-binary-search-tree": "valid-binary-search-tree",
}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def leetcode():
    """number -> dict(title, slug, diff, paid, acs)"""
    pairs = json.loads((DATA / "lc_all.json").read_text())["stat_status_pairs"]
    out = {}
    for p in pairs:
        s = p["stat"]
        out[s["frontend_question_id"]] = dict(
            title=s["question__title"], slug=s["question__title_slug"],
            diff=DIFF[p["difficulty"]["level"]], paid=p["paid_only"], acs=s["total_acs"])
    return out


def doocs():
    """number -> GitHub path of the doocs solution README"""
    out = {}
    for m in re.finditer(r"\|\s*(\d{4})\s*\|\s*\[[^\]]*\]\((/solution/[^)]+/README_EN\.md)\)",
                         (DATA / "doocs_index.md").read_text()):
        out[int(m.group(1))] = m.group(2)
    return out


def neetcode():
    """leetcode slug -> dict(video, code, python)"""
    out = {}
    for x in json.loads((DATA / "neetcode.json").read_text()):
        slug = x["link"].strip("/")
        out[slug] = dict(video=x.get("video"), code=x.get("code"), python=x.get("python", False))
    return out


def neetcode_pages():
    return {l.strip() for l in (DATA / "nc_slugs.txt").read_text().split() if l.strip()}


def curated():
    """[(key, name, [(num, title)])] in file order."""
    topics = []
    for line in (HERE / "dsa_problems.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("# "):
            continue
        if line.startswith("## "):
            key, name = [x.strip() for x in line[3:].split("|", 1)]
            topics.append((key, name, []))
            continue
        num, title = line.split(" ", 1)
        topics[-1][2].append((int(num), title))
    return topics
