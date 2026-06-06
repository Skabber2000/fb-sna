#!/usr/bin/env python3
"""Re-parse post body text from saved raw_html into posts.csv `message`.

Scrape-once / parse-many: runs entirely offline on data/raw_html/*.html.
The post body is recovered two ways and cross-checked:
  1. DOM  — first div[data-ad-rendering-role="story_message"] (rendered text,
            may be truncated by "See more")
  2. JSON — "message":{...,"text":"..."} payload candidates (full text; the
            main post is the candidate that prefix-matches the DOM text,
            else the longest / most frequent one)

    python -m analysis.post_text          # fills message column in posts.csv
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw_html"
POSTS = ROOT / "data" / "posts.csv"

DOM_MARK = 'data-ad-rendering-role="story_message"'
JSON_MSG = re.compile(r'"message"\s*:\s*\{[^{]{0,500}?"text"\s*:\s*"((?:[^"\\]|\\.)+)"')
TS = re.compile(r'(?:creation_time|publish_time)\W{1,3}(\d{9,11})')


def _decode(raw: str) -> str:
    try:
        return json.loads(f'"{raw}"')
    except Exception:
        return ""


def dom_text(html: str) -> str:
    i = html.find(DOM_MARK)
    if i < 0:
        return ""
    start = html.rfind("<div", 0, i)
    frag = html[start:start + 300_000]
    soup = BeautifulSoup(frag, "lxml")
    div = soup.find("div")
    return div.get_text(" ", strip=True) if div else ""


def json_candidates(html: str) -> list[str]:
    texts = [_decode(m) for m in JSON_MSG.findall(html)]
    return [t for t in texts if t]


def extract(html: str) -> str:
    dom = dom_text(html)
    cands = json_candidates(html)
    if not cands:
        return dom
    if dom:
        prefix = dom[:60]
        matched = [c for c in cands if c[:40] and prefix.startswith(c[:40])
                   or c.startswith(prefix[:40])]
        if matched:
            return max(matched, key=len)
    # fallback: most frequent candidate (main post repeats in payload), ties -> longest
    freq = Counter(cands)
    best = max(freq.items(), key=lambda kv: (kv[1], len(kv[0])))
    return best[0]


def post_time(html: str) -> str:
    """Earliest embedded timestamp = the post's own publish time (ISO date)."""
    import datetime
    ts = [int(x) for x in TS.findall(html)]
    ts = [t for t in ts if 1199145600 <= t <= 1812000000]      # 2008..2027
    if not ts:
        return ""
    return datetime.datetime.fromtimestamp(min(ts)).strftime("%Y-%m-%d")


def main() -> None:
    posts = pd.read_csv(POSTS)
    files = {f.stem: f for f in RAW.glob("*.html")}
    print(f"{len(posts)} posts, {len(files)} html files")
    msgs, times, missing = [], [], 0
    for pid in posts["post_id"]:
        f = files.get(str(pid))
        if not f:
            msgs.append("")
            times.append("")
            missing += 1
            continue
        html = f.read_text(encoding="utf-8", errors="ignore")
        msgs.append(extract(html))
        times.append(post_time(html))
    posts["message"] = msgs
    posts["post_time"] = times
    posts.to_csv(POSTS, index=False)
    n_ok = int((posts["message"].astype(str).str.len() >= 10).sum())
    print(f"message filled: {n_ok}/{len(posts)}  (no html: {missing})")
    for _, r in posts.head(3).iterrows():
        print(f"  {r['post_id']}: {str(r['message'])[:100]!r}")


if __name__ == "__main__":
    main()
