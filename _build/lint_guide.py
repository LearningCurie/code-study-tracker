"""Editorial checks for guide modules: python3 lint_guide.py [ai/NN-key.md ...] (default: all).

Reports em dashes, American spellings in prose, thin lessons, missing Try it/sections, and, for lessons that
replace an old concept, the old task next to the first Check-yourself question so they can be compared.
"""
import re
import sys
from pathlib import Path

import build_guide as bg

HERE = Path(__file__).parent
US = re.compile(r"\b(optimiz\w*|behavior\w*|tokeniz\w*|analyz\w*|organiz\w*|summariz\w*|prioritiz\w*|normaliz\w*|"
                r"visualiz\w*|minimiz\w*|maximiz\w*|recogniz\w*|utiliz\w*|categoriz\w*|customiz\w*|"
                r"standardiz\w*|generaliz\w*|memoriz\w*|modeling|labeled|labeling|favor\w*|center\b|catalog\b)", re.I)


def old_tasks():
    path = Path("/home/chsa627/.copilot/session-state/f578a5e2-2854-47ae-a71c-551e49f040e2/files/old_ai_track.txt")
    if not path.exists():
        return {}
    out = {}
    for m in re.finditer(r"concept: id=(\S+) \| [^|]+ \| \S+ \| task: (.*)", path.read_text()):
        out[m.group(1)] = m.group(2).strip()
    return out


def prose(md):
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"`[^`]*`", " ", md)
    return re.sub(r"\]\([^)]*\)", "]", md)


def main(paths):
    tasks = old_tasks()
    for path in paths:
        meta, body = bg.front_matter(path.read_text(), path.name)
        problems = []
        items = bg.parse_items(body, meta["key"], path.name, problems)
        print(f"== {path.name}: {len(items)} items, {sum(i['words'] for i in items):,} words")
        for p in problems:
            print("  WARN", p)
        for it in items:
            text = prose(it["md"])
            notes = []
            if "\u2014" in it["md"] or " \u2013 " in it["md"]:
                notes.append("em/en dash")
            us = sorted({m.group(0).lower() for m in US.finditer(text)})
            if us:
                notes.append("US spelling: " + ", ".join(us[:6]))
            if it["k"] == "lesson" and it["words"] < 450:
                notes.append(f"thin ({it['words']} words)")
            if it["k"] == "lesson" and it["words"] > 1400:
                notes.append(f"long ({it['words']} words)")
            if notes:
                print(f"  - {it['t']}: " + "; ".join(notes))
            if it["id"] in tasks:
                q = re.search(r"^Q:\s*(.*)$", it["md"], re.M)
                print(f"    task: {tasks[it['id']]}\n    Q1:   {q.group(1) if q else '(none)'}")


if __name__ == "__main__":
    args = [Path(a) for a in sys.argv[1:]] or sorted((HERE / "ai").glob("[0-9][0-9]-*.md"))
    main(args)
