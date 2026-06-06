#!/usr/bin/env python3
"""Topic-label posts (Sonnet) + per-user topic-mix vectors + community×theme affinity.

Fills posts.csv `theme`, writes:
  data/user_topics.csv      — per-user L1-normalized topic-mix vector
  data/theme_affinity.csv   — community × theme engagement-share matrix

    python -m analysis.topics --label       # LLM-label all posts with text
    python -m analysis.topics --vectors     # build user vectors + affinity
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
MODEL = "claude-sonnet-4-6"          # 475 posts only — use the better model
CHUNK = 10
WORKERS = 4

THEMES = ["defense-tech", "war-strategy", "geopolitics", "nuclear",
          "ukraine-politics", "economy", "ai-tech", "science-medicine",
          "society-culture", "personal", "other"]

RUBRIC = f"""You label Facebook posts by a Ukrainian public intellectual
(defense/tech/economy/politics commentator). Posts are in Ukrainian, Russian or
English. Assign each numbered post ONE primary theme and optionally one
secondary theme from EXACTLY this list:
{json.dumps(THEMES)}

defense-tech: weapons, drones, missiles, defense industry, milspec engineering
war-strategy: front-line analysis, operations, mobilization, doctrine
geopolitics: international relations, EU/US/NATO/China/Russia politics, sanctions
nuclear: nuclear weapons, energy, safety, deterrence
ukraine-politics: domestic politics, government, reforms, corruption
economy: macro, budgets, markets, business, industry (non-defense)
ai-tech: AI, software, computing, consumer tech, science of computing
science-medicine: biotech, pharma, medicine, fundamental science
society-culture: social issues, culture, history, education, media, religion
personal: personal life, humor without policy point, meta posts
other: anything else

Return ONLY a JSON array in input order:
[{{"i":1,"theme":"...","theme2":"...or empty"}}]"""


def client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("["), text.rfind("]")
    return json.loads(text[start:end + 1]) if start >= 0 else []


def label_chunk(cl, rows: list[dict]) -> dict[str, tuple[str, str]]:
    numbered = "\n".join(f'{n+1}. "{str(r["message"])[:600]}"'
                         for n, r in enumerate(rows))
    msg = cl.messages.create(
        model=MODEL, max_tokens=1500,
        system=[{"type": "text", "text": RUBRIC,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Label these posts:\n{numbered}"}],
    )
    parsed = _parse_json(msg.content[0].text)
    out = {}
    for n, r in enumerate(rows):
        rec = next((p for p in parsed if p.get("i") == n + 1), None) or {}
        t = rec.get("theme", "")
        out[r["post_id"]] = (t if t in THEMES else "other",
                             rec.get("theme2", "") if rec.get("theme2", "") in THEMES else "")
    return out


def label() -> None:
    posts = pd.read_csv(DATA / "posts.csv").fillna("")
    todo = posts[(posts["message"].astype(str).str.len() >= 10)
                 & (posts["theme"].astype(str) == "")]
    chunks = [todo.iloc[i:i + CHUNK].to_dict("records")
              for i in range(0, len(todo), CHUNK)]
    print(f"{len(posts)} posts, labeling {len(todo)} in {len(chunks)} chunks")
    if not chunks:
        return
    cl = client()
    labels: dict[str, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(label_chunk, cl, ch) for ch in chunks]
        for fut in as_completed(futs):
            try:
                labels.update(fut.result())
            except Exception as e:                       # noqa: BLE001
                print(f"  chunk failed: {e}")
    posts["theme"] = posts.apply(
        lambda r: labels.get(r["post_id"], (r["theme"], ""))[0], axis=1)
    posts["theme2"] = posts["post_id"].map(lambda p: labels.get(p, ("", ""))[1])
    posts.to_csv(DATA / "posts.csv", index=False)
    print(posts["theme"].value_counts().to_string())


def vectors() -> None:
    posts = pd.read_csv(DATA / "posts.csv").fillna("")
    comments = pd.read_csv(DATA / "comments.csv")
    reactions_p = DATA / "reactions.csv"
    eng = comments[["post_id", "user"]]
    if reactions_p.exists():
        rx = pd.read_csv(reactions_p)
        if {"post_id", "user"} <= set(rx.columns):
            eng = pd.concat([eng, rx[["post_id", "user"]]])
    eng = eng.merge(posts[["post_id", "theme"]], on="post_id")
    eng = eng[eng["theme"].isin(THEMES)]

    # per-user topic mix (L1-normalized engagement counts)
    mix = (eng.groupby(["user", "theme"]).size().unstack(fill_value=0)
              .reindex(columns=THEMES, fill_value=0))
    mix_n = mix.div(mix.sum(axis=1), axis=0).round(4)
    mix_n["n_eng"] = mix.sum(axis=1)
    mix_n.reset_index().to_csv(DATA / "user_topics.csv", index=False)
    print(f"user_topics.csv: {len(mix_n)} users")

    # community × theme affinity (share of community engagement per theme)
    na = pd.read_csv(DATA / "nodes_analyzed.csv")[["user", "community"]]
    ct = (eng.merge(na, on="user")
             .groupby(["community", "theme"]).size().unstack(fill_value=0)
             .reindex(columns=THEMES, fill_value=0))
    aff = ct.div(ct.sum(axis=1), axis=0).round(4)
    aff.to_csv(DATA / "theme_affinity.csv")
    print(f"theme_affinity.csv: {len(aff)} communities x {len(THEMES)} themes")


def main() -> None:
    ap = argparse.ArgumentParser(description="Post topic labeling + vectors")
    ap.add_argument("--label", action="store_true")
    ap.add_argument("--vectors", action="store_true")
    args = ap.parse_args()
    if args.label:
        label()
    if args.vectors:
        vectors()
    if not (args.label or args.vectors):
        print("specify --label and/or --vectors")


if __name__ == "__main__":
    main()
