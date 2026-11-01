"""Verify the DSA guide: python3 verify_dsa.py [--run-tests] [--exec]

1. Structure: every card, problem card, lab and project has its required parts in order (the build's own checks).
2. Link policy: every link is https, specific (no homepages, roadmaps, problem lists, repository roots, playlists,
   search pages or whole Wikipedia articles), and every video states a length under 20 minutes or a timestamp.
3. Code: every ```python block compiles; with --exec each block also runs on its own in a subprocess (blocks that
   only fail because they use names defined in an earlier block of the same card are retried after those blocks).
4. Tests: with --run-tests, every script in dsa_verify/ runs (each problem card has one that compares the brute force
   and the optimal solution on random small inputs) and must exit 0 within 60 seconds.
Exit status is non-zero if anything fails.
"""
import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import build_dsa_guide as bd
import lint_dsa

HERE = Path(__file__).parent
TESTS = HERE / "dsa_verify"


def blocks(md):
    return re.findall(r"```python\n(.*?)\n```", md, flags=re.S)


def run(code, timeout=30):
    with tempfile.TemporaryDirectory(prefix="dsa-example-") as directory:
        script = Path(directory) / "example.py"
        script.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(script)], cwd=directory, capture_output=True, text=True, timeout=timeout)
            return r.returncode, (r.stderr.strip().splitlines() or [""])[-1]
        except subprocess.TimeoutExpired:
            return 1, "timed out"


def main():
    args = set(sys.argv[1:])
    problems = []
    modules, warn = bd.load(HERE / "dsa")
    problems += warn
    tags = {it["tag"][0] for m in modules for it in m["items"] if it.get("tag")}
    P = bd.Problems()
    counts = dict(cards=0, problem_cards=0, links=0, python=0, executed=0, needs_context=0, tests=0)
    for m in modules:
        for p in m["practice"]:
            if p["tier"] != "mixed" and p.get("pattern") not in tags:
                problems.append(f"{m['key']}: problem {p['id']} has no primer for pattern {p.get('pattern')!r}")
            if p["id"] in m["cards"]:
                counts["problem_cards"] += 1
                diff = P.record(p["id"])[1] if p["id"].isdigit() else "M"
                bd.card_parts(p["id"], m["cards"][p["id"]], diff, m["cards_name"], problems)
            elif p["tier"] != "bank":
                problems.append(f"{m['key']}: problem {p['id']} has no card")
        links = [(f["h"], f["k"]) for f in m["further"]]
        texts = []
        for it in m["items"]:
            counts["cards"] += it["k"] in ("primer", "recap")
            links += [(s["h"], s["n"]) for s in it["src"]]
            texts.append((f"{m['key']} [{it['t']}]", it["md"]))
        texts += [(f"{m['key']} [card {pid}]", c["md"]) for pid, c in m["cards"].items()]
        for where, md in texts:
            prose = re.sub(r"`[^`\n]*`", " ", re.sub(r"```.*?```", " ", md, flags=re.S))
            links += [(u, "inline") for u in re.findall(r"\]\((https://[^)\s]+)\)", prose)]
            if "\u2014" in md:
                problems.append(f"{where}: em dash")
            done = []
            for code in blocks(md):
                counts["python"] += 1
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    problems.append(f"{where}: python block does not compile: line {e.lineno}: {e.msg}")
                    continue
                if "--exec" in args and "input(" not in code and "sys.stdin" not in code:
                    rc, err = run(code)
                    if rc and ("NameError" in err or "ModuleNotFoundError" in err) and done:
                        rc, err = run("\n\n".join(done + [code]))
                    if rc and ("NameError" in err or "ModuleNotFoundError" in err):
                        counts["needs_context"] += 1
                        problems.append(f"{where}: python block needs context or a dependency: {err}")
                    elif rc:
                        problems.append(f"{where}: python block fails: {err}")
                    else:
                        counts["executed"] += 1
                    done.append(code)
        for url, note in links:
            counts["links"] += 1
            if not url.startswith("https://"):
                problems.append(f"{m['key']}: link is not https: {url}")
            for why in lint_dsa.link_notes(url, note if note != "inline" else "inline 5 min"):
                if note == "inline" and why == "no note saying what to read":
                    continue
                problems.append(f"{m['key']}: {url}: {why}")
    if "--run-tests" in args:
        scripts = [script for script in sorted(TESTS.rglob("*.py")) if not script.name.startswith("_")]
        if not scripts:
            problems.append(f"no test scripts found in {TESTS}")
        for script in scripts:
            counts["tests"] += 1
            try:
                r = subprocess.run([sys.executable, script.name], cwd=script.parent, capture_output=True, text=True, timeout=60)
                if r.returncode:
                    output = r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or ["no output"]
                    problems.append(f"test {script.relative_to(HERE)} failed: {output[-1]}")
            except subprocess.TimeoutExpired:
                problems.append(f"test {script.relative_to(HERE)} timed out")
    for p in problems:
        print("FAIL", p)
    print(f"verify_dsa: {len(modules)} modules, {counts['cards']} primer and recap cards, {counts['problem_cards']} problem "
          f"cards, {counts['links']} links, {counts['python']} python blocks"
          + (f" ({counts['executed']} ran alone, {counts['needs_context']} are fragments that need earlier context)" if "--exec" in args else "")
          + (f", {counts['tests']} test scripts" if "--run-tests" in args else "") + f": {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
