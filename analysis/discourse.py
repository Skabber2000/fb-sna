#!/usr/bin/env python3
"""Axis C — discourse-quality scoring of comments via Claude (Haiku 4.5).

Scores each comment in its ORIGINAL language (Claude is multilingual) on:
  politeness, constructiveness, professional_insight, civility (0-4) and
  stance (-2..+2), plus a short English gloss. Aggregates to a per-user
  discourse profile and merges into the node table.

Cost control: Haiku 4.5 + prompt-cached rubric + comment batching.
Resumable: appends per-chunk to discourse_comments.csv; reruns skip done ids.

    python -m analysis.discourse --limit 0        # score all (0 = no limit)
    python -m analysis.discourse --aggregate      # build per-user + merge nodes
"""
from __future__ import annotations

import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
load_dotenv(ROOT / ".env")
MODEL = "claude-haiku-4-5-20251001"
CHUNK = 20
WORKERS = 6
OUT = DATA / "discourse_comments.csv"
METRICS = ["politeness", "constructiveness", "insight", "civility", "stance"]

RUBRIC = """You score Facebook comments for discourse quality. Comments may be in \
Ukrainian, Russian, English or other languages — score them in their original \
language (do not require translation).

For EACH numbered comment return integer scores:
- politeness 0-4 (0 rude/hostile, 4 very polite/respectful)
- constructiveness 0-4 (0 noise/dismissive, 4 adds substantive info or argument)
- insight 0-4 (professional/domain insight: 0 none, 4 clear expertise/specifics)
- civility 0-4 (0 toxic/abusive, 4 fully civil)
- stance -2..2 (toward the author/post: -2 strongly critical, 0 neutral, 2 strongly supportive)
- gloss: <=10 word English summary

Return ONLY a JSON array, one object per comment, in input order:
[{"i":1,"politeness":3,"constructiveness":2,"insight":1,"civility":4,"stance":1,"gloss":"..."}]
No prose, no code fences."""


def client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("["), text.rfind("]")
    return json.loads(text[start:end + 1]) if start >= 0 else []


def score_chunk(cl, rows: list[dict]) -> list[dict]:
    numbered = "\n".join(f'{n+1}. "{(r["text_original"] or "")[:300]}"'
                         for n, r in enumerate(rows))
    msg = cl.messages.create(
        model=MODEL, max_tokens=2000,
        system=[{"type": "text", "text": RUBRIC,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Score these comments:\n{numbered}"}],
    )
    parsed = _parse_json(msg.content[0].text)
    out = []
    for n, r in enumerate(rows):
        rec = next((p for p in parsed if p.get("i") == n + 1), None) or {}
        out.append({
            "comment_id": r["comment_id"], "user": r["user"],
            "politeness": rec.get("politeness", ""), "constructiveness": rec.get("constructiveness", ""),
            "insight": rec.get("insight", ""), "civility": rec.get("civility", ""),
            "stance": rec.get("stance", ""), "gloss": str(rec.get("gloss", ""))[:80],
        })
    return out


def run(limit: int) -> None:
    df = pd.read_csv(DATA / "comments.csv").fillna("")
    df = df[df["text_original"].astype(str).str.len() >= 3]
    done = set()
    if OUT.exists():
        done = set(pd.read_csv(OUT)["comment_id"])
    todo = df[~df["comment_id"].isin(done)]
    if limit:
        todo = todo.head(limit)
    chunks = [todo.iloc[i:i + CHUNK].to_dict("records")
              for i in range(0, len(todo), CHUNK)]
    print(f"{len(df)} comments, {len(done)} done, scoring {len(todo)} in {len(chunks)} chunks")
    if not chunks:
        return
    cl = client()
    header_written = OUT.exists()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(score_chunk, cl, ch): i for i, ch in enumerate(chunks)}
        for k, fut in enumerate(as_completed(futs), 1):
            try:
                recs = fut.result()
            except Exception as e:                       # noqa: BLE001
                print(f"  chunk failed: {e}"); continue
            pd.DataFrame(recs).to_csv(OUT, mode="a", header=not header_written, index=False)
            header_written = True
            if k % 10 == 0:
                print(f"  {k}/{len(chunks)} chunks scored")
    print(f"Done -> {OUT}")


def aggregate() -> None:
    d = pd.read_csv(OUT)
    for m in METRICS:
        d[m] = pd.to_numeric(d[m], errors="coerce")
    g = d.groupby("user")
    prof = g[METRICS].mean().round(2)
    prof["n_scored"] = g.size()
    prof = prof.reset_index()
    prof.to_csv(DATA / "discourse_users.csv", index=False)

    # merge into nodes_analyzed
    na_path = DATA / "nodes_analyzed.csv"
    if na_path.exists():
        na = pd.read_csv(na_path)
        na = na.drop(columns=[c for c in METRICS + ["n_scored"] if c in na.columns],
                     errors="ignore")
        na = na.merge(prof, on="user", how="left")
        na.to_csv(na_path, index=False)
    print(f"discourse_users.csv: {len(prof)} people")
    print("Top professional-insight voices:")
    top = prof[prof["n_scored"] >= 2].sort_values("insight", ascending=False).head(10)
    nm = pd.read_csv(DATA / "nodes.csv")[["user", "author_name"]]
    top = top.merge(nm, on="user", how="left")
    for _, r in top.iterrows():
        print(f"  {str(r['author_name'])[:24]:<24} insight={r['insight']} "
              f"polite={r['politeness']} constr={r['constructiveness']} (n={int(r['n_scored'])})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Discourse-quality scoring (Claude)")
    ap.add_argument("--limit", type=int, default=0, help="max comments (0=all)")
    ap.add_argument("--aggregate", action="store_true")
    args = ap.parse_args()
    if args.aggregate:
        aggregate()
    else:
        run(args.limit)


if __name__ == "__main__":
    main()
