"""Build the DSA engineering guide (dsa.html) from Markdown modules plus the existing problem bank.

Usage: python3 build_dsa_guide.py [--strict]
       python3 build_dsa_guide.py --check dsa/07-twoptr.md [...]   (validate files only; writes nothing)

Module files live in _build/dsa/NN-key.md and use the AI guide's format (see build_guide.py) with these changes:

    ---
    key: twoptr
    name: Two pointers
    stage: linear
    summary: One sentence shown under the module title.
    why: Why the module matters (one paragraph).
    outcomes:            (2+ items) what you can do afterwards
    cues:                (2+ items) recognition cues: what in a problem signals this module's ideas
    traps:               (2+ items) common mistakes
    systems:             (optional) where it shows up in real software
    further:             (optional) Type · duration | Title | https://url
    bank: twoptr window  (optional) old topic keys from dsa_problems.txt whose remaining problems are listed here
    ---

    === lesson | Title | 12 min
    goal: ...
    link: Label | https://url | What to read there
    practice: 167, 15      (optional) problems from this module's practice block to try right after the lesson

    === practice           (at most one per module, usually last)
    - 167 core             tier: core, derive (core, but the technique is not obvious), stretch, or mixed
      cue: what in the statement signals the technique
      hint: a nudge toward the approach
      insight: the idea that unlocks the optimal solution
      cost: O(n) time, O(1) space
      pattern: the technique, revealed last (required for mixed problems)
      after: module key (mixed problems only): the review set unlocks once that module's lessons are done

Problem ids are LeetCode numbers ("167") or the bank's other judges ("cses:1641", "ac:dp_a", "hr:slug").
Progress lives in the same "dsa-status" tracker the old problem page used, so every old mark is kept: each of the
899 old problems appears exactly once, either in a practice block or in the bank of the module that claims its topic.
"""
import ast
import hashlib
import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

import mdlite
from build_guide import further_parts, link_parts, minutes, slug
from meta import DATA, NC_RENAMED, curated, leetcode, neetcode, neetcode_pages
from render import write_track

HERE = Path(__file__).parent
KINDS = {"primer": "l", "recap": "l", "lab": "lab", "build": "b"}
ALIASES = {"lesson": "primer"}
PRIMER_HEADINGS = ("## Intuition", "## How it works", "## Cost", "## When to use it", "## Worked trace", "## Template",
                   "## Pitfalls", "## Check yourself", "## Lab")
RECAP_HEADINGS = ("## Internals", "## Template", "## Worked example", "## Pitfalls", "## Quick check")
TAG_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,23}")
CARD_HEADINGS = ("## The problem", "## Constraints and what they imply", "## Brute force", "## The insight",
                 "## Optimal solution, traced", "## Code", "## Complexity", "## Mistakes and edge cases", "## Variations")
CARD_WORDS = {"E": 220, "M": 380, "H": 600}
MAX_VIDEO_MIN = 20.5
TIERS = ("core", "derive", "stretch", "mixed")
MODULE_FIELDS = ("key", "name", "stage", "summary", "why")
LIST_FIELDS = ("outcomes", "cues", "traps", "systems", "further")
PROBLEM_FIELDS = ("cue", "hint", "insight", "cost", "pattern", "after")
DIFF = {"Easy": "E", "Medium": "M", "Hard": "H"}


# ---------- problem metadata ----------

def _cses_names():
    h = (DATA / "cses_archive.html").read_text(encoding="utf-8", errors="ignore")
    return {i: html.unescape(t) for i, t in re.findall(r'/problemset/task/(\d+)/?"[^>]*>([^<]+)</a>', h)}


def _atcoder_names():
    h = (DATA / "atcoder_dp.html").read_text()
    return {tid: t for tid, t in re.findall(r'href="/contests/dp/tasks/(dp_[a-z])">([^<]+)</a>', h) if len(t) > 1}


class Problems:
    """Looks up any problem id and returns its compact page record and its full URLs (for the link checker)."""

    def __init__(self):
        required = ("lc_all.json", "neetcode.json", "nc_slugs.txt", "cses_archive.html",
                    "atcoder_dp.html", "hackerrank.json", "yt_durations.json")
        self.catalog = None
        if not all((DATA / name).is_file() for name in required):
            catalog = HERE / "dsa_catalog.json"
            if not catalog.is_file():
                raise FileNotFoundError("DSA metadata caches and the offline dsa_catalog.json are unavailable")
            self.catalog = json.loads(catalog.read_text(encoding="utf-8"))
            if not isinstance(self.catalog, dict):
                raise ValueError(f"{catalog}: expected an object mapping problem ids to records")
            for pid, record in self.catalog.items():
                if not isinstance(pid, str) or not isinstance(record, list):
                    raise ValueError(f"{catalog}: invalid record for {pid!r}")
                if pid.isdigit():
                    valid = (len(record) == 6 and all(isinstance(value, str) for value in record[:5])
                             and record[1] in DIFF.values() and isinstance(record[5], int))
                else:
                    valid = len(record) == 3 and all(isinstance(value, str) for value in record)
                if not valid:
                    raise ValueError(f"{catalog}: invalid record for {pid!r}")
            return
        self.lc = leetcode()
        self.nc = neetcode()
        self.ncp = neetcode_pages()
        self.cses = _cses_names()
        self.atc = _atcoder_names()
        self.hr = json.loads((DATA / "hackerrank.json").read_text())
        yt = DATA / "yt_durations.json"
        self.yt = json.loads(yt.read_text()) if yt.exists() else {}

    def known(self, pid):
        try:
            self.record(pid)
            return True
        except (KeyError, ValueError):
            return False

    def record(self, pid):
        """Compact record for the page: LeetCode [title, E/M/H, slug, neetcode slug or "", video id or ""];
        other judges [title, judge, url]."""
        if self.catalog is not None:
            return self.catalog[pid]
        if pid.isdigit():
            p = self.lc[int(pid)]
            if p["paid"]:
                raise ValueError(f"LeetCode {pid} is paid-only")
            ncs = NC_RENAMED.get(p["slug"], p["slug"])
            v = self.nc.get(p["slug"], {}).get("video") or ""
            # Videos are linked only when their length is known and under about 20 minutes (link policy).
            secs = self.yt.get(v, 0)
            mins = round(secs / 60) if v and 0 < secs <= MAX_VIDEO_MIN * 60 else 0
            return [p["title"].strip(), DIFF[p["diff"]], p["slug"], ncs if ncs in self.ncp else "", v if mins else "", mins]
        kind, _, val = pid.partition(":")
        if kind == "cses":
            return [self.cses[val], "CSES", f"https://cses.fi/problemset/task/{val}"]
        if kind == "ac":
            return [f"{val[-1].upper()}. {self.atc[val]}", "AtCoder", f"https://atcoder.jp/contests/dp/tasks/{val}"]
        if kind == "hr":
            return [self.hr[val].strip(), "HackerRank", f"https://www.hackerrank.com/challenges/{val}/problem"]
        raise ValueError(f"unknown problem id {pid!r}")

    def urls(self, pid):
        r = self.record(pid)
        if len(r) == 3:
            return [r[2]]
        out = [f"https://leetcode.com/problems/{r[2]}/", f"https://leetcode.doocs.org/en/lc/{int(pid)}/"]
        if r[3]:
            out.append(f"https://neetcode.io/problems/{r[3]}/question")
        if r[4]:
            out.append(f"https://www.youtube.com/watch?v={r[4]}")
        return out


def old_bank():
    """Old topic key -> ordered list of problem ids (LeetCode first, then other judges), as on the old page."""
    from dsa_topics import TOPICS
    out = {}
    for key, _, probs in curated():
        out[key] = [str(n) for n, _ in probs] + list(TOPICS[key]["extra"])
    return out


# ---------- module parsing ----------

def front_matter(text, where):
    if not text.startswith("---\n"):
        raise ValueError(f"{where}: missing front matter")
    end = text.index("\n---\n", 4)
    meta, cur = {}, None
    for line in text[4:end].split("\n"):
        if not line.strip():
            continue
        if line.startswith("- ") and cur in LIST_FIELDS:
            meta[cur].append(line[2:].strip())
        elif line.startswith("  ") and cur and isinstance(meta.get(cur), str):
            meta[cur] += " " + line.strip()
        else:
            k, sep, v = line.partition(":")
            k = k.strip()
            if not sep or not re.fullmatch(r"[a-z]+", k):
                raise ValueError(f"{where}: bad front-matter line {line!r}")
            cur = k
            meta[k] = [] if k in LIST_FIELDS else v.strip()
            if k in LIST_FIELDS and v.strip():
                raise ValueError(f"{where}: {k} must be a list of '- ' lines")
    return meta, text[end + 5:]


def parse_practice(src, where, problems):
    """The === practice block: '- <id> <tier>' lines, each followed by indented 'field: text' lines."""
    out, cur = [], None
    for raw in src.split("\n"):
        if not raw.strip():
            continue
        m = re.fullmatch(r"- (\S+) (\w+)\s*", raw)
        if m:
            pid, tier = m.groups()
            if tier not in TIERS:
                raise ValueError(f"{where}: problem {pid}: tier must be one of {', '.join(TIERS)}")
            cur = dict(id=pid, tier=tier)
            out.append(cur)
            continue
        m = re.fullmatch(r"\s+(\w+):\s*(.*)", raw)
        if m and cur is not None and m.group(1) in PROBLEM_FIELDS:
            cur[m.group(1)] = m.group(2).strip()
        elif raw.startswith("    ") and cur is not None and len(cur) > 2:
            last = list(cur)[-1]
            cur[last] += " " + raw.strip()
        else:
            raise ValueError(f"{where}: bad practice line {raw!r}")
    for p in out:
        w = f"{where} [problem {p['id']}]"
        for f in ("cue", "hint", "insight", "cost"):
            if not p.get(f):
                problems.append(f"{w}: missing {f}")
        if p["tier"] == "mixed" and not (p.get("pattern") and p.get("after")):
            problems.append(f"{w}: mixed problems need a pattern and an after module")
        if p["tier"] != "mixed" and p.get("after"):
            problems.append(f"{w}: only mixed problems take after")
    return out


def ladder_html(p, pattern_name=""):
    """The three-level hint ladder: what to notice, a nudge, the key insight (which also reveals the pattern)."""
    parts = []
    for label, f in (("Hint 1: what to notice", "cue"), ("Hint 2: a nudge", "hint")):
        if p.get(f):
            parts.append(f'<details class="hs"><summary>{label}</summary><p>{mdlite.inline(p[f])}</p></details>')
    tail = ""
    if pattern_name:
        tail += f'<p><b>Pattern:</b> {mdlite.inline(pattern_name)}</p>'
    tail += f'<p>{mdlite.inline(p.get("insight", ""))}</p>'
    if p.get("cost"):
        tail += f'<p class="cx"><b>Target:</b> {mdlite.inline(p["cost"])}</p>'
    parts.append(f'<details class="hs"><summary>Hint 3: the key insight</summary>{tail}</details>')
    return '<div class="hn"><p class="hl">Stuck? Open the hints one at a time:</p>' + "".join(parts) + "</div>"


def parse_cards(path):
    """NN-key.cards.md holds full problem cards: '=== card | <problem id>', optional 'time: 25 min', a blank line,
    then Markdown with CARD_HEADINGS in order."""
    out = {}
    chunks = re.split(r"(?m)^=== ", path.read_text())
    if chunks[0].strip():
        raise ValueError(f"{path.name}: text before the first card")
    for chunk in chunks[1:]:
        head, _, rest = chunk.partition("\n")
        parts = [x.strip() for x in head.split("|")]
        if len(parts) != 2 or parts[0] != "card" or not parts[1]:
            raise ValueError(f"{path.name}: bad card header {head!r}")
        pid = parts[1]
        if pid in out:
            raise ValueError(f"{path.name}: card {pid} appears twice")
        lines, fields, i = rest.split("\n"), {}, 0
        while i < len(lines) and lines[i].strip():
            k, sep, v = lines[i].partition(":")
            if not sep or k.strip() != "time":
                raise ValueError(f"{path.name} [card {pid}]: expected an optional 'time:' line then a blank line, got {lines[i]!r}")
            fields["time"] = v.strip()
            i += 1
        out[pid] = dict(md="\n".join(lines[i:]).strip(), time=fields.get("time"))
    return out


def card_parts(pid, card, diff, where, problems):
    """Validate one problem card and render it as (visible html, hidden solution html, words)."""
    src, w = card["md"], f"{where} [card {pid}]"
    found = [h for h in re.findall(r"(?m)^## .+$", src) if h in CARD_HEADINGS]
    missing = [h for h in CARD_HEADINGS if h not in found]
    if missing:
        problems.append(f"{w}: missing " + ", ".join(missing))
    elif found != list(CARD_HEADINGS):
        problems.append(f"{w}: headings out of order or repeated")
    if "```steps" not in src:
        problems.append(f"{w}: the optimal solution needs a ```steps trace")
    if "```python" not in src.split("## Code", 1)[-1]:
        problems.append(f"{w}: ## Code needs a python block")
    for code in re.findall(r"```python\n(.*?)\n```", src, flags=re.S):
        try:
            ast.parse(code)
        except SyntaxError as e:
            problems.append(f"{w}: python block does not parse: line {e.lineno}: {e.msg}")
    var = src.split("## Variations", 1)[-1]
    if not 2 <= len(re.findall(r"(?m)^- ", var)) <= 4:
        problems.append(f"{w}: ## Variations needs 2-3 bullet points")
    words = mdlite.plain(src)
    if words < CARD_WORDS.get(diff, 300):
        problems.append(f"{w}: thin for its difficulty ({words} words)")
    if card.get("time"):
        minutes(card["time"])
    visible, _, hidden = src.partition("## Brute force")
    try:
        return mdlite.render(visible), mdlite.render("## Brute force" + hidden), words
    except mdlite.MdError as e:
        raise ValueError(f"{w}: {e}") from None


def problem_html(p, card=None, pattern_name=""):
    """A problem's in-page content: the card's visible part, the hint ladder, then the hidden solution."""
    if not card:
        return ladder_html(p, pattern_name)
    vis, hid = card
    return (f'<div class="pc">{vis}</div>' + ladder_html(p, pattern_name) +
            f'<details class="sol"><summary>Show the solution: brute force, insight, traced optimal, code</summary>'
            f'<div class="pc">{hid}</div></details>')


def parse_items(body, mod, where, problems):
    items, practice = [], []
    chunks = re.split(r"(?m)^=== ", body)
    if chunks[0].strip():
        raise ValueError(f"{where}: text before the first item")
    for chunk in chunks[1:]:
        head, _, rest = chunk.partition("\n")
        if head.strip() == "practice":
            if practice:
                raise ValueError(f"{where}: more than one === practice block")
            practice = parse_practice(rest, where, problems)
            continue
        parts = [p.strip() for p in head.split("|")]
        if parts and parts[0] in ALIASES:
            parts[0] = ALIASES[parts[0]]
        if len(parts) != 3 or parts[0] not in KINDS:
            raise ValueError(f"{where}: bad item header {head!r}")
        kind, title, time = parts
        w = f"{where} [{title}]"
        fields = {"link": [], "practice": []}
        lines = rest.split("\n")
        i = 0
        while i < len(lines) and lines[i].strip():
            k, sep, v = lines[i].partition(":")
            if not sep or k not in ("id", "goal", "link", "practice", "tag"):
                raise ValueError(f"{w}: expected id/goal/link/practice/tag field lines then a blank line, got {lines[i]!r}")
            if k == "tag":
                tk, _, tn = [x.strip() for x in v.partition("|")]
                if not TAG_RE.fullmatch(tk) or not tn:
                    raise ValueError(f"{w}: tag must be 'key | Display name' with a short lowercase key, got {v.strip()!r}")
                fields["tag"] = [tk, tn]
            elif k == "link":
                fields["link"].append(link_parts(v.strip(), w))
            elif k == "practice":
                fields["practice"] += [x for x in re.split(r"[,\s]+", v.strip()) if x]
            else:
                fields[k] = v.strip()
            i += 1
        src = "\n".join(lines[i:]).strip()
        if not fields.get("goal"):
            raise ValueError(f"{w}: missing goal")
        try:
            body_html = mdlite.render(src)
        except mdlite.MdError as e:
            raise ValueError(f"{w}: {e}") from None
        words = mdlite.plain(src)
        if kind in ("primer", "recap"):
            if not src.startswith("> [!key]"):
                problems.append(f"{w}: {kind} should open with a > [!key] callout")
            heads = PRIMER_HEADINGS if kind == "primer" else RECAP_HEADINGS
            found = [h for h in re.findall(r"(?m)^## .+$", src) if h in heads]
            missing = [h for h in heads if h not in found]
            if missing:
                problems.append(f"{w}: {kind} is missing " + ", ".join(missing))
            elif found != [h for h in heads if h in found]:
                problems.append(f"{w}: {kind} headings are out of order")
            qs = src.count("\nQ:")
            if kind == "primer" and not 2 <= qs <= 4:
                problems.append(f"{w}: primer needs 2-4 Q:/A: pairs (has {qs})")
            if kind == "recap" and not 1 <= qs <= 2:
                problems.append(f"{w}: recap needs 1-2 Q:/A: pairs (has {qs})")
            if "```steps" not in src and kind == "primer":
                problems.append(f"{w}: primer needs a ```steps worked trace")
            if not re.search(r"(?m)^> \[!know\]", src):
                problems.append(f"{w}: {kind} must end with a > [!know] 'You now know' line")
            if kind == "primer" and words < 600:
                problems.append(f"{w}: primer is short ({words} words)")
            if kind == "recap" and not 250 <= words <= 900:
                problems.append(f"{w}: recap should be 300-700 words ({words})")
        if kind == "build":
            for h in ("## The brief", "## Spec", "## Milestones", "## Done when", "## Stretch goals", "## Hints"):
                if h not in src:
                    problems.append(f"{w}: build needs {h}")
        if kind == "lab" and "## Steps" not in src:
            problems.append(f"{w}: lab needs ## Steps")
        ms = 0
        if kind == "build":
            mm = re.search(r"(?ms)^## Milestones\n(.*?)(?=^## |\Z)", src)
            ms = len(re.findall(r"(?m)^\d+\. ", mm.group(1))) if mm else 0
            if not 3 <= ms <= 15:
                problems.append(f"{w}: build needs 3-15 numbered milestones under ## Milestones (found {ms})")
        items.append(dict(
            id=fields.get("id") or f"{KINDS[kind]}:{mod}/{slug(title)}",
            k=kind, t=title, tm=time, m=minutes(time), g=fields["goal"], src=fields["link"],
            p=fields["practice"], tag=fields.get("tag"), ms=ms, html=body_html, words=words, md=src))
    return items, practice


STUB = "---\nkey: {key}\nname: Builds\nstage: found\nsummary: x\nwhy: x\noutcomes:\n- x\n- x\ncues:\n- x\n- x\ntraps:\n- x\n- x\n---\n\n"


def load_module(path, problems):
    text = path.read_text()
    if not text.startswith("---\n") and text.startswith("=== build"):
        # A builds-only file (written separately and appended to its module later): validate it on its own.
        text = STUB.format(key=re.sub(r"[^a-z0-9]", "", path.stem.lower())[:20] or "b") + text
    meta, body = front_matter(text, path.name)
    for f in MODULE_FIELDS:
        if not meta.get(f):
            raise ValueError(f"{path.name}: missing {f}")
    for f in ("outcomes", "cues", "traps"):
        if len(meta.get(f, [])) < 2:
            problems.append(f"{path.name}: needs at least two {f}")
    items, practice = parse_items(body, meta["key"], path.name, problems)
    ids = [p["id"] for p in practice]
    if len(ids) != len(set(ids)):
        problems.append(f"{path.name}: a problem is listed twice in the practice block")
    cards_path = path.with_name(path.stem + ".cards.md")
    cards = parse_cards(cards_path) if cards_path.exists() else {}
    for pid in cards:
        if pid not in ids:
            problems.append(f"{cards_path.name}: card {pid} is not in the module's practice block")
    return dict(cards=cards, cards_name=cards_path.name,
        key=meta["key"], name=meta["name"], stage=meta["stage"], summary=meta["summary"], why=meta["why"],
        outcomes=meta.get("outcomes", []), cues=meta.get("cues", []), traps=meta.get("traps", []),
        systems=meta.get("systems", []), further=[further_parts(f, path.name) for f in meta.get("further", [])],
        bank=meta.get("bank", "").split(), items=items, practice=practice)


def load(folder):
    problems = []
    modules = [load_module(p, problems) for p in sorted(folder.glob("[0-9][0-9]-*.md")) if not p.name.endswith(".cards.md")]
    return modules, problems


# ---------- page ----------

def urls_of(modules, P, pids):
    urls = set()
    for m in modules:
        urls.update(f["h"] for f in m["further"])
        for it in m["items"]:
            urls.update(s["h"] for s in it["src"])
            prose = re.sub(r"`[^`\n]*`", " ", re.sub(r"```.*?```", " ", it["md"], flags=re.S))
            urls.update(re.findall(r"\]\((https://[^)\s]+)\)", prose))
        for card in m["cards"].values():
            prose = re.sub(r"`[^`\n]*`", " ", re.sub(r"```.*?```", " ", card["md"], flags=re.S))
            urls.update(re.findall(r"\]\((https://[^)\s]+)\)", prose))
        for p in m["practice"]:
            urls.update(re.findall(r"\]\((https://[^)\s]+)\)", " ".join(p.get(f, "") for f in PROBLEM_FIELDS)))
    for pid in pids:
        urls.update(P.urls(pid))
    return urls


def build(strict=False):
    import dsa_guide as guide
    T, STAGES = guide.TRACK, guide.STAGES
    P = Problems()
    modules, problems = load(HERE / "dsa")
    stage_keys = [s["key"] for s in STAGES]
    order = {k: i for i, k in enumerate(stage_keys)}
    for m in modules:
        if m["stage"] not in order:
            raise ValueError(f"{m['key']}: unknown stage {m['stage']}")
    modules.sort(key=lambda m: order[m["stage"]])
    bank = old_bank()
    keys, ids, placed, claimed = set(), set(), {}, {}
    for m in modules:
        if m["key"] in keys:
            raise ValueError(f"duplicate module key {m['key']}")
        keys.add(m["key"])
        if m["stage"] not in stage_keys:
            raise ValueError(f"{m['key']}: unknown stage {m['stage']}")
        for it in m["items"]:
            if it["id"] in ids or it["id"].isdigit():
                raise ValueError(f"duplicate or numeric item id {it['id']}")
            if len(it["id"]) > 120:
                raise ValueError(f"item id too long {it['id']}")
            ids.add(it["id"])
        for p in m["practice"]:
            if p.get("after") and p["after"] not in {x["key"] for x in modules}:
                raise ValueError(f"{m['key']}: problem {p['id']}: unknown after module {p['after']}")
            if not P.known(p["id"]):
                raise ValueError(f"{m['key']}: unknown or paid problem {p['id']}")
            if p["id"] in placed:
                raise ValueError(f"problem {p['id']} is in the practice blocks of {placed[p['id']]} and {m['key']}")
            placed[p["id"]] = m["key"]
        for t in m["bank"]:
            if t not in bank:
                raise ValueError(f"{m['key']}: unknown bank topic {t}")
            if t in claimed:
                raise ValueError(f"bank topic {t} is claimed by {claimed[t]} and {m['key']}")
            claimed[t] = m["key"]
    unclaimed = sorted(set(bank) - set(claimed))
    if unclaimed:
        problems.append("bank topics not claimed by any module (their problems would vanish): " + ", ".join(unclaimed))
    for m in modules:
        m["bankIds"] = [pid for t in m["bank"] for pid in bank[t] if pid not in placed]
    tags = {}
    for m in modules:
        for it in m["items"]:
            if it.get("tag"):
                if it["tag"][0] in tags:
                    raise ValueError(f"tag {it['tag'][0]} is declared twice")
                tags[it["tag"][0]] = [it["tag"][1], it["id"]]
    for m in modules:
        for p in m["practice"]:
            pat = p.get("pattern", "")
            if pat not in tags and p["tier"] != "mixed":
                problems.append(f"{m['key']}: problem {p['id']}: pattern {pat!r} is not a declared tag")
    every_old = {pid for t in bank for pid in bank[t]}
    shown = set(placed) | {pid for m in modules for pid in m["bankIds"]}
    for m in modules:
        for it in m["items"]:
            for pid in it["p"]:
                if pid not in shown:
                    problems.append(f"{m['key']} [{it['t']}]: practice {pid} is not on the page")
    lost = every_old - shown
    if lost:
        problems.append(f"{len(lost)} old problems are not on the page: " + ", ".join(sorted(lost)[:20]))
    for m in modules:
        m["rendered_cards"] = {}
        for p in m["practice"]:
            card = m["cards"].get(p["id"])
            if card:
                diff = P.record(p["id"])[1] if p["id"].isdigit() else "M"
                visible, hidden, _ = card_parts(p["id"], card, diff, m["cards_name"], problems)
                m["rendered_cards"][p["id"]] = (visible, hidden)
            else:
                problems.append(f"{m['key']}: problem {p['id']} has no full solution card")
    for p in problems:
        print("WARN", p)
    if strict and problems:
        sys.exit(1)

    content_dir = HERE.parent / T["contentDir"]
    content_dir.mkdir(exist_ok=True)
    for m in modules:
        body = {it["id"]: it["html"] for it in m["items"]}
        for p in m["practice"]:
            parts = m["rendered_cards"].get(p["id"])
            pat = p.get("pattern", "")
            body["p:" + p["id"]] = problem_html(p, parts, tags[pat][0] if pat in tags else pat)
        js = ("(window.guideContent=window.guideContent||[]).push(" +
              json.dumps([m["key"], body], ensure_ascii=False, separators=(",", ":"))
              .replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + ");\n")
        m["v"] = hashlib.sha256(js.encode()).hexdigest()[:10]
        (content_dir / f"{m['key']}.js").write_text(js)

    keyidx = {m["key"]: i for i, m in enumerate(modules)}
    pids = sorted(shown, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x))
    data = dict(
        title=T["title"], subtitle=T["subtitle"], storageKey=T["storageKey"], routine=T["routine"],
        projects=T["projects"], searchHint=T["searchHint"], contentDir=T["contentDir"],
        statuses=["Done", "Needs practice", "Revisit"], pstatuses=["Solved", "Brute only", "Stuck"], tags=tags,
        stages=[dict(s, modules=[i for i, m in enumerate(modules) if m["stage"] == s["key"]]) for s in STAGES],
        problems={pid: P.record(pid) for pid in pids},
        modules=[dict(
            key=m["key"], name=m["name"], summary=m["summary"], why=m["why"], outcomes=m["outcomes"], cues=m["cues"],
            traps=m["traps"], systems=m["systems"], further=m["further"], v=m["v"],
            items=[dict({k: it[k] for k in ("id", "k", "t", "tm", "m", "g", "src", "p")},
                        **({"tag": it["tag"][0]} if it.get("tag") else {}), **({"ms": it["ms"]} if it["ms"] else {}))
                   for it in m["items"]],
            practice=[dict(id=p["id"], t=p["tier"], pat=p.get("pattern", ""),
                           **({"after": keyidx[p["after"]]} if p.get("after") else {}),
                           **({"card": 1, "tm": minutes(m["cards"][p["id"]]["time"]) if m["cards"][p["id"]].get("time") else 0}
                              if p["id"] in m["cards"] else {}))
                      for p in m["practice"]],
            bank=m["bankIds"]) for m in modules])
    tpl = (HERE / "dsa_template.html").read_text()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    out = HERE.parent / T["file"]
    ver = lambda f: hashlib.sha256((HERE.parent / f).read_bytes()).hexdigest()[:10]
    out.write_text(tpl.replace("/*DATA*/", payload)
                   .replace("__TITLE__", html.escape(T["title"]))
                   .replace("__DESC__", html.escape(T["subtitle"]))
                   .replace("__GCSSV__", ver("guide.css")).replace("__CSSV__", ver("dsa.css"))
                   .replace("__JSV__", ver("dsa.js")))
    # write_track expects the tracker shape (modules -> groups -> items) and only counts the items.
    write_track(dict(title=T["title"], storageKey=T["storageKey"], statuses=["done"],
                     modules=[dict(name=m["name"], groups=[dict(items=m["items"] + m["practice"] + m["bankIds"])])
                              for m in modules]), out)
    urls = urls_of(modules, P, pids)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "urls_dsa.txt").write_text("\n".join(sorted(urls)) + "\n")
    if P.catalog is None:
        (HERE / "dsa_catalog.json").write_text(
            json.dumps(data["problems"], ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")

    count = {k: sum(1 for m in modules for it in m["items"] if it["k"] == k) for k in KINDS}
    tiers = {t: sum(1 for m in modules for p in m["practice"] if p["tier"] == t) for t in TIERS}
    words = sum(it["words"] for m in modules for it in m["items"])
    mins = sum(it["m"] for m in modules for it in m["items"] if it["k"] != "build")
    print(f"wrote {out.name}: {len(STAGES)} stages, {len(modules)} modules, {count}, practice {tiers}, "
          f"bank {sum(len(m['bankIds']) for m in modules)}, {len(pids)} problems in all, {words:,} words, "
          f"~{mins / 60:.0f} h of lessons and labs, {len(urls)} unique URLs, page {out.stat().st_size / 1e3:.0f} kB, "
          f"lessons {sum(p.stat().st_size for p in content_dir.glob('*.js')) / 1e6:.2f} MB in {T['contentDir']}/")
    return modules


def check(paths):
    """Validate single module files without writing anything (safe while others edit other files)."""
    P = Problems()
    bad = 0
    for p in paths:
        path = Path(p)
        problems = []
        cards_only = path.name.endswith(".cards.md")
        if cards_only:
            path = path.with_name(path.name[:-len(".cards.md")] + ".md")
        try:
            m = load_module(path, problems)
            if cards_only:
                problems = []  # a card author checks the cards, not the module author's work
                missing = [q["id"] for q in m["practice"] if q["id"] not in m["cards"]]
                if missing:
                    problems.append("practice problems without a card: " + ", ".join(missing))
            tags = {it["tag"][0] for it in m["items"] if it.get("tag")}
            for q in m["practice"]:
                if q["id"] in m["cards"]:
                    diff = P.record(q["id"])[1] if q["id"].isdigit() and P.known(q["id"]) else "M"
                    card_parts(q["id"], m["cards"][q["id"]], diff, m["cards_name"], problems)
                if not cards_only and q["tier"] != "mixed" and q.get("pattern") not in tags:
                    problems.append(f"problem {q['id']}: pattern {q.get('pattern')!r} is not a tag declared in this module")
            for q in m["practice"]:
                if not P.known(q["id"]):
                    problems.append(f"unknown or paid-only problem {q['id']}")
            for it in m["items"]:
                for pid in it["p"]:
                    if not P.known(pid):
                        problems.append(f"{it['t']}: unknown or paid-only practice problem {pid}")
            ids = [it["id"] for it in m["items"]]
            if len(ids) != len(set(ids)):
                problems.append("duplicate item ids")
            bank = old_bank()
            for t in m["bank"]:
                if t not in bank:
                    problems.append(f"unknown bank topic {t}")
            kinds = {k: sum(1 for it in m["items"] if it["k"] == k) for k in KINDS}
            tiers = {t: sum(1 for q in m["practice"] if q["tier"] == t) for t in TIERS}
            words = sum(it["words"] for it in m["items"])
            cw = sum(mdlite.plain(c["md"]) for c in m["cards"].values())
            print(f"{path.name}: {kinds}, practice {tiers}, {words:,} words" +
                  (f"; {len(m['cards'])} problem cards, {cw:,} words" if m["cards"] else ""))
        except ValueError as e:
            problems.append(f"ERROR {e}")
        for x in problems:
            print("  WARN", x)
        bad += len(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    if "--check" in sys.argv:
        check([a for a in sys.argv[1:] if a != "--check"])
    else:
        build(strict="--strict" in sys.argv)
