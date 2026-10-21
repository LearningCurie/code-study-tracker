"""Shared rendering: inject tracker data into template.html and list every URL for the link checker."""
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
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out_path.write_text(tpl.replace("/*DATA*/null", payload).replace("__TITLE__", data["title"]))
    urls = urls_in(data, set())
    urls_path.write_text("\n".join(sorted(urls)) + "\n")
    return urls
