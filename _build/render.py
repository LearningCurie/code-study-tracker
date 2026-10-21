"""Shared rendering: inject tracker data into template.html and list every URL for the link checker."""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
YT = "https://www.youtube.com/watch?v="
PL = "https://www.youtube.com/playlist?list="


def media(ref, label):
    kind, val = ref.split(":", 1)
    if kind == "yt":
        return dict(t=label, h=YT + val)
    if kind == "pl":
        return dict(t=label, h=PL + val)
    if kind == "url":
        return dict(t=label, h=val)
    raise ValueError(ref)


def urls_in(o, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "h" and isinstance(v, str) and v.startswith("http"):
                out.add(v)
            else:
                urls_in(v, out)
    elif isinstance(o, list):
        for v in o:
            urls_in(v, out)
    return out


def render(data, out_path, urls_path):
    tpl = (HERE / "template.html").read_text()
    # "<" is escaped so the JSON can never close its <script> block.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    page = (tpl.replace("/*DATA*/", payload)
            .replace("__TITLE__", html.escape(data["title"]))
            .replace("__DESC__", html.escape(data["subtitle"])))
    out_path.write_text(page)
    write_track(data, out_path)
    urls = urls_in(data, set())
    urls_path.write_text("\n".join(sorted(urls)) + "\n")
    return urls


def write_track(data, out_path):
    """Keep tracks.js (used by the home page) in step with each generated tracker."""
    path = out_path.parent / "tracks.js"
    tracks = {}
    if path.exists():
        body = path.read_text()
        tracks = json.loads(body[body.index("=") + 1:body.rindex(";")])
    items = [i for m in data["modules"] for g in m["groups"] for i in g["items"]]
    tracks[data["storageKey"]] = dict(
        title=data["title"], href="./" + out_path.name, total=len(items),
        topics=len(data["modules"]), unit=data["statuses"][0].lower(), first=data["modules"][0]["name"])
    path.write_text("window.STUDY_TRACKS = " + json.dumps(tracks, indent=1, sort_keys=True) + ";\n")
