"""Build a lesson-based field guide page (ai.html) from Markdown module files.

Usage: python3 build_guide.py [--strict]
       python3 build_guide.py --check ai/07-billing.md [...]   (validate files only; writes nothing)

Module files live in _build/ai/NN-key.md:

    ---
    key: billing
    name: Tokens, billing and prompt caching
    stage: build
    summary: One sentence shown under the module title.
    why: Why the module matters (one paragraph).
    outcomes:
    - What you can do after the module
    habits:
    - What professionals do
    traps:
    - Common mistakes
    further:
    - Video · 18 min | Title | https://...
    ---

    === lesson | Title | 12 min
    id: c:legacy-id            (optional; keeps progress from older versions)
    goal: What you will be able to do or explain
    link: Label | https://url | What to read there

    Markdown body (see mdlite.py)

Item kinds are lesson, lab and build. Lessons start with a > [!key] callout and end with
## Check yourself Q:/A: pairs; builds contain ## Milestones and ## Done when.
"""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import mdlite
from render import write_track

HERE = Path(__file__).parent
KINDS = {"lesson": "l", "lab": "lab", "build": "b"}
MODULE_FIELDS = ("key", "name", "stage", "summary", "why")
LIST_FIELDS = ("outcomes", "habits", "traps", "further")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def minutes(t):
    m = re.fullmatch(r"(\d+)\s*min", t)
    if m:
        return int(m.group(1))
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?\s*h", t)
    if m:
        lo = float(m.group(1))
        hi = float(m.group(2) or lo)
        return round((lo + hi) / 2 * 60)
    raise ValueError(f"bad time {t!r}; use '12 min', '2 h' or '6-10 h'")


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


def link_parts(raw, where):
    parts = [p.strip() for p in raw.split(" | ")]
    if len(parts) not in (2, 3) or not parts[1].startswith("https://"):
        raise ValueError(f"{where}: link must be 'Label | https://url | note': {raw!r}")
    return dict(t=parts[0], h=parts[1], n=parts[2] if len(parts) == 3 else "")


def further_parts(raw, where):
    parts = [p.strip() for p in raw.split(" | ")]
    if len(parts) != 3 or not parts[2].startswith("https://"):
        raise ValueError(f"{where}: further must be 'Type · duration | Title | https://url': {raw!r}")
    return dict(k=parts[0], t=parts[1], h=parts[2])


def parse_items(body, mod, where, problems):
    items = []
    chunks = re.split(r"(?m)^=== ", body)
    if chunks[0].strip():
        raise ValueError(f"{where}: text before the first item")
    for chunk in chunks[1:]:
        head, _, rest = chunk.partition("\n")
        parts = [p.strip() for p in head.split("|")]
        if len(parts) != 3 or parts[0] not in KINDS:
            raise ValueError(f"{where}: bad item header {head!r}")
        kind, title, time = parts
        w = f"{where} [{title}]"
        fields = {"link": []}
        lines = rest.split("\n")
        i = 0
        while i < len(lines) and lines[i].strip():
            k, sep, v = lines[i].partition(":")
            if not sep or k not in ("id", "goal", "link"):
                raise ValueError(f"{w}: expected id/goal/link field lines then a blank line, got {lines[i]!r}")
            if k == "link":
                fields["link"].append(link_parts(v.strip(), w))
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
        if kind == "lesson":
            if not fields["link"]:
                problems.append(f"{w}: lesson has no link")
            if not src.startswith("> [!key]"):
                problems.append(f"{w}: lesson should open with a > [!key] callout")
            if "## Check yourself" not in src or src.count("\nQ:") < 2:
                problems.append(f"{w}: lesson needs ## Check yourself with at least two Q:/A: pairs")
            if words < 300:
                problems.append(f"{w}: lesson is short ({words} words)")
        if kind == "build":
            for h in ("## Milestones", "## Done when"):
                if h not in src:
                    problems.append(f"{w}: build needs {h}")
        if kind == "lab" and "## Steps" not in src:
            problems.append(f"{w}: lab needs ## Steps")
        items.append(dict(
            id=fields.get("id") or f"{KINDS[kind]}:{mod}/{slug(title)}",
            k=kind, t=title, tm=time, m=minutes(time), g=fields["goal"],
            src=fields["link"], html=body_html, words=words, md=src))
    return items


def load(folder):
    problems, modules = [], []
    for path in sorted(folder.glob("[0-9][0-9]-*.md")):
        meta, body = front_matter(path.read_text(), path.name)
        for f in MODULE_FIELDS:
            if not meta.get(f):
                raise ValueError(f"{path.name}: missing {f}")
        for f in ("outcomes", "habits", "traps"):
            if len(meta.get(f, [])) < 2:
                problems.append(f"{path.name}: needs at least two {f}")
        items = parse_items(body, meta["key"], path.name, problems)
        modules.append(dict(
            key=meta["key"], name=meta["name"], stage=meta["stage"], summary=meta["summary"], why=meta["why"],
            outcomes=meta.get("outcomes", []), habits=meta.get("habits", []), traps=meta.get("traps", []),
            further=[further_parts(f, path.name) for f in meta.get("further", [])], items=items))
    return modules, problems


def urls_of(modules):
    urls = set()
    for m in modules:
        urls.update(f["h"] for f in m["further"])
        for it in m["items"]:
            urls.update(s["h"] for s in it["src"])
            # Only real Markdown links count; example URLs inside code are not rendered as links.
            prose = re.sub(r"`[^`\n]*`", " ", re.sub(r"```.*?```", " ", it["md"], flags=re.S))
            urls.update(re.findall(r"\]\((https://[^)\s]+)\)", prose))
    return urls


def build(name="ai", strict=False):
    guide = __import__(f"{name}_guide")
    T, STAGES = guide.TRACK, guide.STAGES
    modules, problems = load(HERE / name)
    stage_keys = [s["key"] for s in STAGES]
    keys, ids = set(), set()
    for m in modules:
        if m["key"] in keys:
            raise ValueError(f"duplicate module key {m['key']}")
        keys.add(m["key"])
        if m["stage"] not in stage_keys:
            raise ValueError(f"{m['key']}: unknown stage {m['stage']}")
        for it in m["items"]:
            if it["id"] in ids:
                raise ValueError(f"duplicate item id {it['id']}")
            if len(it["id"]) > 120:
                raise ValueError(f"item id too long {it['id']}")
            ids.add(it["id"])
    order = {k: i for i, k in enumerate(stage_keys)}
    if [order[m["stage"]] for m in modules] != sorted(order[m["stage"]] for m in modules):
        raise ValueError("module files must be numbered in stage order")
    for p in problems:
        print("WARN", p)
    if strict and problems:
        sys.exit(1)

    # Lesson bodies go in one small script per module (loaded when the module is opened), so the page itself
    # only carries the outline and stays fast however much content the guide grows.
    content_dir = HERE.parent / T["contentDir"]
    content_dir.mkdir(exist_ok=True)
    for old in content_dir.glob("*.js"):
        old.unlink()
    for m in modules:
        body = {it["id"]: it["html"] for it in m["items"]}
        js = ("(window.guideContent=window.guideContent||[]).push(" +
              json.dumps([m["key"], body], ensure_ascii=False, separators=(",", ":"))
              .replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + ");\n")
        m["v"] = hashlib.sha256(js.encode()).hexdigest()[:10]
        (content_dir / f"{m['key']}.js").write_text(js)

    data = dict(
        title=T["title"], subtitle=T["subtitle"], storageKey=T["storageKey"], routine=T["routine"], atlas=T.get("atlas", ""),
        statuses=["Done", "Needs practice", "Revisit"], searchHint=T["searchHint"], contentDir=T["contentDir"],
        stages=[dict(s, modules=[i for i, m in enumerate(modules) if m["stage"] == s["key"]]) for s in STAGES],
        modules=[dict({k: v for k, v in m.items() if k != "items"},
                      items=[{k: v for k, v in it.items() if k not in ("md", "words", "html")} for it in m["items"]])
                 for m in modules])
    tpl = (HERE / "guide_template.html").read_text()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    out = HERE.parent / T["file"]
    ver = lambda f: hashlib.sha256((HERE.parent / f).read_bytes()).hexdigest()[:10]
    out.write_text(tpl.replace("/*DATA*/", payload)
                   .replace("__TITLE__", html.escape(T["title"]))
                   .replace("__DESC__", html.escape(T["subtitle"]))
                   .replace("__CSSV__", ver("guide.css")).replace("__JSV__", ver("guide.js")))
    # write_track expects the tracker shape: modules -> groups -> items.
    write_track(dict(title=T["title"], storageKey=T["storageKey"], statuses=data["statuses"],
                     modules=[dict(name=m["name"], groups=[dict(items=m["items"])]) for m in modules]), out)
    urls = urls_of(modules)
    (HERE / "data" / f"urls_{name}.txt").write_text("\n".join(sorted(urls)) + "\n")

    count = {k: sum(1 for m in modules for it in m["items"] if it["k"] == k) for k in KINDS}
    words = sum(it["words"] for m in modules for it in m["items"])
    mins = sum(it["m"] for m in modules for it in m["items"] if it["k"] != "build")
    print(f"wrote {out.name}: {len(STAGES)} stages, {len(modules)} modules, {count}, {words:,} words, "
          f"~{mins / 60:.0f} h of lessons and labs, {len(urls)} unique URLs, page {out.stat().st_size / 1e3:.0f} kB, "
          f"lessons {sum(p.stat().st_size for p in content_dir.glob('*.js')) / 1e6:.2f} MB in {T['contentDir']}/")
    return modules


def check(paths):
    """Validate single module files without writing anything (safe while others edit other files)."""
    bad = 0
    for p in paths:
        path = Path(p)
        problems = []
        try:
            meta, body = front_matter(path.read_text(), path.name)
            for f in MODULE_FIELDS:
                if not meta.get(f):
                    problems.append(f"missing front-matter field {f}")
            for f in meta.get("further", []):
                further_parts(f, path.name)
            items = parse_items(body, meta.get("key", "?"), path.name, problems)
            ids = [it["id"] for it in items]
            if len(ids) != len(set(ids)):
                problems.append("duplicate item ids")
            kinds = {k: sum(1 for it in items if it["k"] == k) for k in KINDS}
            words = sum(it["words"] for it in items)
            print(f"{path.name}: {kinds}, {words:,} words")
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
