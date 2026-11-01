"""Editorial and code checks for DSA guide modules: python3 lint_dsa.py [dsa/NN-key.md ...] (default: all).

Reports em dashes, American spellings in prose, thin or very long lessons, Python code blocks that do not
compile, missing Practise-it-now links on lessons, and practice blocks with weak annotations.
"""
import ast
import re
import sys
import urllib.parse
from pathlib import Path

import build_dsa_guide as bd
from lint_guide import US, prose

GENERIC = [
    (re.compile(r"^https://[^/]+/?$"), "homepage"),
    (re.compile(r"^https://github\.com/[^/]+/[^/]+/?$"), "repository root"),
    (re.compile(r"youtube\.com/(playlist|results)|youtube\.com/@"), "playlist, search or channel"),
    (re.compile(r"neetcode\.io/(roadmap|practice)/?$|leetcode\.com/(problemset|studyplan)|techinterviewhandbook\.org/grind75"), "roadmap or problem list"),
    (re.compile(r"^https://[a-z]+\.wikipedia\.org/wiki/[^#]+$"), "whole Wikipedia article (add a #section)"),
]


def link_notes(url, note):
    out = [why for rx, why in GENERIC if rx.search(url)]
    if re.search(r"youtube\.com/watch|youtu\.be/", url):
        parsed = urllib.parse.urlsplit(url)
        params = urllib.parse.parse_qs(parsed.query)
        fragment = urllib.parse.parse_qs(parsed.fragment)
        duration = re.search(r"\b(\d+(?:\.\d+)?)\s*min\b", note)
        timestamped = bool(params.get("t") or fragment.get("t"))
        if not timestamped and (not duration or float(duration.group(1)) > bd.MAX_VIDEO_MIN):
            out.append("video without a length under about 20 min or a timestamp")
    if not note:
        out.append("no note saying what to read")
    return out

HERE = Path(__file__).parent


def code_blocks(md, lang):
    return re.findall(r"```" + lang + r"\n(.*?)\n```", md, flags=re.S)


def main(paths):
    total = 0
    for path in paths:
        problems = []
        try:
            m = bd.load_module(path, problems)
        except ValueError as e:
            print(f"== {path.name}: ERROR {e}")
            total += 1
            continue
        words = sum(i["words"] for i in m["items"])
        print(f"== {path.name}: {len(m['items'])} items, {len(m['practice'])} practice problems, {words:,} words")
        for p in problems:
            print("  WARN", p)
        total += len(problems)
        for it in m["items"]:
            notes = []
            text = prose(it["md"])
            if "\u2014" in it["md"] or " \u2013 " in it["md"]:
                notes.append("em/en dash")
            us = sorted({x.group(0).lower() for x in US.finditer(text)})
            if us:
                notes.append("US spelling: " + ", ".join(us[:6]))
            if it["k"] == "primer" and it["words"] > 1900:
                notes.append(f"long ({it['words']} words): split it")
            if it["k"] == "primer" and not it["src"]:
                notes.append("no Go deeper link")
            for s in it["src"]:
                for why in link_notes(s["h"], s["n"]):
                    notes.append(f"link {s['h']}: {why}")
            for i, code in enumerate(code_blocks(it["md"], "python")):
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    notes.append(f"python block {i + 1} does not parse: line {e.lineno}: {e.msg}")
            if notes:
                print(f"  - {it['t']}: " + "; ".join(notes))
                total += len(notes)
        for f in m["further"]:
            for why in link_notes(f["h"], f["k"]):
                print(f"  - further {f['h']}: {why}")
                total += 1
        tags = {it["tag"][0] for it in m["items"] if it.get("tag")}
        for p in m["practice"]:
            if p["tier"] != "mixed" and p.get("pattern") not in tags:
                print(f"  - problem {p['id']}: pattern {p.get('pattern')!r} is not a tag declared in this module")
                total += 1
            text = " ".join(p.get(f, "") for f in bd.PROBLEM_FIELDS)
            if "\u2014" in text:
                print(f"  - problem {p['id']}: em dash")
                total += 1
            if len(p.get("insight", "")) < 40:
                print(f"  - problem {p['id']}: insight is very short")
                total += 1
    return total


if __name__ == "__main__":
    args = [Path(a) for a in sys.argv[1:]] or sorted((HERE / "dsa").glob("[0-9][0-9]-*.md"))
    sys.exit(1 if main(args) else 0)
