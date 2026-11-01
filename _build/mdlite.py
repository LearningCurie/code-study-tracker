"""A small, safe Markdown subset renderer for guide lessons.

All text is HTML-escaped; only the tags below are produced and links must be https.

Blocks: paragraphs, ## / ### headings, - and 1. lists (nested by indent), | tables |,
```lang code fences, ```flow diagrams (one row per line, nodes split by ->, "Title: note"),
```steps dry runs (steps split by --- lines; first line is the caption, the rest is a monospace state
in which {{text}} is highlighted; the page shows one step at a time with Prev/Next),
> quotes and > [!key|tip|warn|note|example|know] callouts, Q:/A: self-check pairs (answer hidden).
Inline: `code`, **bold**, *italic*, [text](https://url).
"""
import html
import re

CALLOUTS = {"key": "Key idea", "tip": "Tip", "warn": "Watch out", "note": "Note", "example": "Example", "know": "You now know"}
LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


class MdError(ValueError):
    pass


def inline(text):
    codes = []

    def keep(m):
        codes.append(f"<code>{html.escape(m.group(1), quote=False)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`\n]+)`", keep, text)
    links = []

    def link(m):
        label, url = m.group(1), m.group(2)
        if not url.startswith("https://"):
            raise MdError(f"only https links are allowed: {url}")
        links.append((label, url))
        return f"\x01{len(links) - 1}\x01"

    text = re.sub(r"\[([^\]\n]+)\]\((\S+?)\)", link, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*(?![\w*])", r"<i>\1</i>", text)

    def unlink(m):
        label, url = links[int(m.group(1))]
        inner = re.sub(r"\x00(\d+)\x00", lambda c: codes[int(c.group(1))], html.escape(label, quote=False))
        return f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{inner}</a>'

    text = re.sub(r"\x01(\d+)\x01", unlink, text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def flow(lines):
    rows = []
    for line in lines:
        if not line.strip():
            continue
        nodes = []
        for part in [p.strip() for p in line.split("->")]:
            if not part:
                raise MdError(f"empty flow node in: {line}")
            title, _, note = part.partition(":")
            body = f"<b>{inline(title.strip())}</b>" + (f"<small>{inline(note.strip())}</small>" if note.strip() else "")
            nodes.append(f'<span class="fn">{body}</span>')
        rows.append('<div class="fr">' + '<span class="fa" aria-hidden="true">&rarr;</span>'.join(nodes) + "</div>")
    return '<div class="flow" role="img" aria-label="Diagram">' + "".join(rows) + "</div>"


def steps(lines):
    chunks, cur = [], []
    for line in lines:
        if line.strip() == "---":
            chunks.append(cur)
            cur = []
        else:
            cur.append(line)
    chunks.append(cur)
    out = []
    for chunk in chunks:
        while chunk and not chunk[0].strip():
            chunk.pop(0)
        while chunk and not chunk[-1].strip():
            chunk.pop()
        if not chunk:
            raise MdError("empty step in a steps block")
        caption, state = chunk[0].strip(), [l.rstrip() for l in chunk[1:]]
        pad = min((len(l) - len(l.lstrip()) for l in state if l.strip()), default=0)
        text = html.escape("\n".join(l[pad:] for l in state), quote=False)
        text = re.sub(r"\{\{(.+?)\}\}", r"<mark>\1</mark>", text)
        out.append(f'<li><p class="sc">{inline(caption)}</p>' + (f"<pre>{text}</pre>" if text else "") + "</li>")
    if len(out) < 2:
        raise MdError("a steps block needs at least two steps")
    return f'<div class="trace"><ol>{"".join(out)}</ol></div>'


def table(rows):
    def cells(r):
        r = r.strip()
        if r.startswith("|"):
            r = r[1:]
        if r.endswith("|"):
            r = r[:-1]
        return [c.strip() for c in re.split(r"(?<!\\)\|", r)]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    for b in body:
        if len(b) != len(head):
            raise MdError(f"table row has {len(b)} cells, header has {len(head)}: {b}")
    out = ['<div class="tw"><table><thead><tr>']
    out += [f"<th>{inline(c.replace(chr(92) + '|', '|'))}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for b in body:
        out.append("<tr>" + "".join(f"<td>{inline(c.replace(chr(92) + '|', '|'))}</td>" for c in b) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def lists(lines):
    """Render a list block; nesting follows indentation. An ordered list keeps its first number (start=)."""
    items = []
    for line in lines:
        m = LIST_RE.match(line)
        if m:
            num = int(m.group(2)[:-1]) if m.group(2)[0].isdigit() else None
            items.append([len(m.group(1).expandtabs(4)), "ol" if num is not None else "ul", m.group(3), num])
        elif items:
            items[-1][2] += " " + line.strip()

    def open_tag(kind, num):
        return f'<ol start="{num}">' if kind == "ol" and num not in (None, 1) else f"<{kind}>"

    out, stack = [], []
    for ind, kind, text, num in items:
        while stack and ind < stack[-1][0]:
            out.append(f"</li></{stack.pop()[1]}>")
        if stack and ind > stack[-1][0]:
            out.append(open_tag(kind, num))
            stack.append((ind, kind))
        elif stack:
            out.append("</li>")
        else:
            out.append(open_tag(kind, num))
            stack.append((ind, kind))
        out.append(f"<li>{inline(text)}")
    while stack:
        out.append(f"</li></{stack.pop()[1]}>")
    return "".join(out)


def render(src):
    lines = src.replace("\r\n", "\n").split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(s.strip() for s in para))}</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```"):
            flush()
            lang = s[3:].strip().lower()
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            if j == len(lines):
                raise MdError("unclosed code fence")
            body = lines[i + 1:j]
            if lang == "flow":
                out.append(flow(body))
            elif lang == "steps":
                out.append(steps(body))
            else:
                label = f'<span class="cl">{html.escape(lang)}</span>' if lang and lang != "text" else ""
                code = html.escape("\n".join(body), quote=False)
                out.append(f'<div class="code">{label}<pre><code>{code}</code></pre></div>')
            i = j + 1
            continue
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("#### ") or s.startswith("# "):
            raise MdError(f"use ## or ### headings inside items: {s}")
        if s.startswith("## ") or s.startswith("### "):
            flush()
            level = 4 if s.startswith("## ") else 5
            out.append(f"<h{level}>{inline(s.lstrip('#').strip())}</h{level}>")
            i += 1
            continue
        if s.startswith(">"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(re.sub(r"^\s*> ?", "", lines[i]))
                i += 1
            m = re.match(r"^\[!(\w+)\]\s*(.*)$", block[0].strip())
            if m:
                kind = m.group(1).lower()
                if kind not in CALLOUTS:
                    raise MdError(f"unknown callout [!{kind}]")
                rest = ([m.group(2)] if m.group(2) else []) + block[1:]
                out.append(f'<div class="co co-{kind}"><p class="ct">{CALLOUTS[kind]}</p>{render(chr(10).join(rest))}</div>')
            else:
                out.append(f"<blockquote>{render(chr(10).join(block))}</blockquote>")
            continue
        if s.startswith("|") and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(table(rows))
            continue
        if LIST_RE.match(line) and not para:
            block = []
            while i < len(lines) and lines[i].strip() and (LIST_RE.match(lines[i]) or lines[i].startswith((" ", "\t"))):
                block.append(lines[i])
                i += 1
            out.append(lists(block))
            continue
        if s.startswith("Q:"):
            flush()
            q, a = [s[2:].strip()], []
            i += 1
            cur = q
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("Q:"):
                t = lines[i].strip()
                if t.startswith("A:"):
                    cur = a
                    t = t[2:].strip()
                cur.append(t)
                i += 1
            if not "".join(a).strip():
                raise MdError(f"question without answer: {q[0]}")
            out.append(f'<div class="qa"><p class="q">{inline(" ".join(q))}</p><details><summary>Show answer</summary>'
                       f'<p>{inline(" ".join(x for x in a if x))}</p></details></div>')
            continue
        para.append(line)
        i += 1
    flush()
    return "".join(out)


def plain(src):
    """Rough word count of the Markdown source, ignoring code."""
    text = re.sub(r"```.*?```", " ", src, flags=re.S)
    return len(re.findall(r"[A-Za-z0-9][\w'-]*", text))
