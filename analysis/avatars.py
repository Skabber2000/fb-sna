#!/usr/bin/env python3
"""Avatar layer: extract page-owner profile pictures from saved profile HTML,
download from fbcdn (signed URLs still live), vision-score with Claude.

Owner-avatar heuristic (validated on samples): svg <image> tags carry avatars;
image-IDs that recur across many different profiles are UI chrome (own navbar
avatar, sidebar shortcuts) — the first NON-constant svg image is the owner's
profile photo. Joins to graph users via enrich_manifest.tsv (safeslug -> name)
+ nodes.csv (author_name -> user pseudonym). No salt needed.

Vision dims (aggregate demography + presentation; pseudonymized):
  ptype: photo type; unif: military uniform; uasym: UA symbols; grp: group photo;
  fml: formality 0-4; age: age band; gnd: gender presentation; smil: smiling.

    python -m analysis.avatars --extract     # urls -> avatar_urls.csv
    python -m analysis.avatars --download    # -> data/avatars/*.jpg
    python -m analysis.avatars --score       # -> avatar_scores.csv
    python -m analysis.avatars --aggregate   # merge into nodes_analyzed.csv
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PROF = DATA / "profile_html"
AVA = DATA / "avatars"
load_dotenv(ROOT / ".env")
MODEL = "claude-haiku-4-5-20251001"

SVG_IMG = re.compile(r'<image[^>]+xlink:href="([^"]+)"')
IMG_ID = re.compile(r"/(\d+_\d+_\d+)_n\.jpg")
PTYPES = ["solo-photo", "group-photo", "family-child", "military-uniform",
          "professional-headshot", "wedding-formal", "symbol-flag", "cartoon-art",
          "pet-animal", "landscape-object", "logo-text", "default-silhouette",
          "unclear"]

RUBRIC = f"""You classify Facebook profile pictures (avatars). For EACH numbered
image return a JSON object:
{{"i":<n>,
 "ptype": one of {json.dumps(PTYPES)},
 "unif": 0/1 military uniform or tactical gear visible,
 "uasym": 0/1 Ukrainian symbols (flag, trident/tryzub, vyshyvanka, blue-yellow),
 "grp": 0/1 more than one person,
 "fml": 0-4 presentation formality (0 casual/fun, 4 formal/professional),
 "age": "18-29|30-44|45-59|60+|unknown" apparent age band of main person,
 "gnd": "m|f|unknown" gender presentation of main person,
 "smil": 0/1 smiling}}
If no person visible: age/gnd "unknown", smil 0.
Return ONLY a JSON array, in input order. No prose."""


def _norm(u: str) -> str:
    return u.replace("\\u0026", "&").replace("&amp;", "&")


def client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("["), text.rfind("]")
    return json.loads(text[start:end + 1]) if start >= 0 else []


def extract() -> None:
    files = sorted(PROF.glob("*__about_overview.html"))
    print(f"{len(files)} profile pages")
    per_file: list[tuple[str, list[tuple[str, str]]]] = []
    id_freq: Counter = Counter()
    for f in files:
        html = f.read_text(encoding="utf-8", errors="ignore")
        seq = []
        for u in SVG_IMG.findall(html):
            u = _norm(u)
            m = IMG_ID.search(u)
            if m:
                seq.append((m.group(1), u))
        per_file.append((f.stem.replace("__about_overview", ""), seq))
        for iid in {iid for iid, _ in seq}:
            id_freq[iid] += 1
    chrome = {iid for iid, n in id_freq.items() if n > len(files) * 0.05}
    print(f"chrome image-ids excluded: {len(chrome)}")
    rows = []
    for safeslug, seq in per_file:
        own = [(iid, u) for iid, u in seq if iid not in chrome]
        if not own:
            rows.append({"safeslug": safeslug, "img_id": "", "url": ""})
            continue
        first_id = own[0][0]
        # prefer the largest variant of that id (longest stp size / no crop)
        variants = [u for iid, u in own if iid == first_id]
        best = max(variants, key=lambda u: int(
            (re.search(r"_s(\d+)x\d+", u) or re.search(r"(\d+)", "0")).group(1)))
        rows.append({"safeslug": safeslug, "img_id": first_id, "url": best})
    pd.DataFrame(rows).to_csv(DATA / "avatar_urls.csv", index=False)
    n = sum(1 for r in rows if r["url"])
    print(f"avatar_urls.csv: {n}/{len(rows)} with owner avatar")


def download() -> None:
    import urllib.request
    AVA.mkdir(exist_ok=True)
    df = pd.read_csv(DATA / "avatar_urls.csv").fillna("")
    todo = [(r["safeslug"], r["url"]) for _, r in df.iterrows()
            if r["url"] and not (AVA / f"{r['safeslug']}.jpg").exists()]
    print(f"downloading {len(todo)} avatars")

    def get(item):
        slug, url = item
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            data = urllib.request.urlopen(req, timeout=20).read()
            if len(data) > 500:
                (AVA / f"{slug}.jpg").write_bytes(data)
                return 1
        except Exception:
            pass
        return 0

    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(get, todo):
            ok += r
    have = len(list(AVA.glob("*.jpg")))
    print(f"downloaded {ok} new; total on disk {have}")


def score() -> None:
    out = DATA / "avatar_scores.csv"
    done = set()
    if out.exists():
        done = set(pd.read_csv(out)["safeslug"])
    imgs = [p for p in sorted(AVA.glob("*.jpg")) if p.stem not in done]
    print(f"scoring {len(imgs)} avatars ({len(done)} done)")
    if not imgs:
        return
    cl = client()
    BATCH = 4
    batches = [imgs[i:i + BATCH] for i in range(0, len(imgs), BATCH)]
    header_written = out.exists()

    def score_batch(batch):
        content = []
        for n, p in enumerate(batch, 1):
            content.append({"type": "text", "text": f"Image {n}:"})
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg",
                "data": base64.b64encode(p.read_bytes()).decode()}})
        content.append({"type": "text", "text": "Classify all images."})
        msg = cl.messages.create(
            model=MODEL, max_tokens=1200,
            system=[{"type": "text", "text": RUBRIC,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": content}],
        )
        parsed = _parse_json(msg.content[0].text)
        recs = []
        for n, p in enumerate(batch, 1):
            rec = next((x for x in parsed if x.get("i") == n), None) or {}
            recs.append({"safeslug": p.stem,
                         "ptype": str(rec.get("ptype", "")),
                         "unif": rec.get("unif", ""), "uasym": rec.get("uasym", ""),
                         "grp": rec.get("grp", ""), "fml": rec.get("fml", ""),
                         "age": str(rec.get("age", "")), "gnd": str(rec.get("gnd", "")),
                         "smil": rec.get("smil", "")})
        return recs

    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(score_batch, b) for b in batches]
        for k, fut in enumerate(as_completed(futs), 1):
            try:
                recs = fut.result()
            except Exception as e:                       # noqa: BLE001
                print(f"  batch failed: {e}")
                continue
            pd.DataFrame(recs).to_csv(out, mode="a",
                                      header=not header_written, index=False)
            header_written = True
            if k % 25 == 0:
                print(f"  {k}/{len(batches)} batches")
    print(f"Done -> {out}")


def aggregate() -> None:
    """Join avatar scores to graph users via manifest (safeslug->name) +
    nodes (author_name->user)."""
    man = pd.read_csv(DATA / "enrich_manifest.tsv", sep="\t",
                      names=["safeslug", "slug", "name"])
    sc = pd.read_csv(DATA / "avatar_scores.csv")
    nodes = pd.read_csv(DATA / "nodes.csv")[["user", "author_name"]].drop_duplicates("author_name")
    j = (sc.merge(man, on="safeslug", how="left")
           .merge(nodes, left_on="name", right_on="author_name", how="left"))
    j = j[j["user"].notna()]
    cols = ["user", "ptype", "unif", "uasym", "grp", "fml", "age", "gnd", "smil"]
    j[cols].drop_duplicates("user").to_csv(DATA / "avatar_users.csv", index=False)
    print(f"avatar_users.csv: {j['user'].nunique()} users joined "
          f"(of {len(sc)} scored)")
    na = pd.read_csv(DATA / "nodes_analyzed.csv")
    av = j[cols].drop_duplicates("user").add_prefix("av_").rename(
        columns={"av_user": "user"})
    na = na.drop(columns=[c for c in av.columns if c != "user" and c in na.columns],
                 errors="ignore").merge(av, on="user", how="left")
    na.to_csv(DATA / "nodes_analyzed.csv", index=False)
    print(f"merged into nodes_analyzed.csv ({na.shape[1]} cols)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Avatar extraction + vision layer")
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    args = ap.parse_args()
    if args.extract:
        extract()
    if args.download:
        download()
    if args.score:
        score()
    if args.aggregate:
        aggregate()


if __name__ == "__main__":
    main()
