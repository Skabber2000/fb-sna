#!/usr/bin/env python3
"""Explain communities: synthesize a label + description for each cluster from
its members' comment glosses (English summaries), occupations and discourse.

Inputs (data/): nodes_analyzed.csv, discourse_comments.csv, profiles.csv
Output (data/): community_profiles.csv  (+ console)
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
load_dotenv(ROOT / ".env")
MODEL = "claude-sonnet-4-6"
GLOSS_SAMPLE = 45


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    s, e = text.find("{"), text.rfind("}")
    return json.loads(text[s:e + 1]) if s >= 0 else {}


def describe(cl, cid, members, glosses, occ, disc) -> dict:
    prompt = f"""This is one cluster of a Ukrainian public figure's Facebook audience
(the page owner posts on defense, technology, economy, politics and society).

Cluster {cid}: {len(members)} people. Lead members: {', '.join(members[:6])}.
Member occupations (sample): {', '.join(occ[:15]) or 'unknown'}.
Discourse: insight {disc['insight']:.2f}/4, civility {disc['civility']:.2f}/4,
politeness {disc['politeness']:.2f}/4, stance {disc['stance']:+.2f}.

English summaries of their comments (sample):
- """ + "\n- ".join(glosses[:GLOSS_SAMPLE]) + """

Return JSON only: {"label":"3-5 word name","description":"2 sentences on what
defines this cluster — topics they engage, tone, who they are"}"""
    m = cl.messages.create(model=MODEL, max_tokens=350,
                           messages=[{"role": "user", "content": prompt}])
    return _parse(m.content[0].text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    n = pd.read_csv(DATA / "nodes_analyzed.csv").fillna("")
    d = pd.read_csv(DATA / "discourse_comments.csv").fillna("")
    prof = (pd.read_csv(DATA / "profiles.csv").fillna("")
            if (DATA / "profiles.csv").exists() else pd.DataFrame())
    u2c = dict(zip(n["user"], n["community"]))
    d["community"] = d["user"].map(u2c)
    for m in ["insight", "civility", "politeness", "stance"]:
        n[m] = pd.to_numeric(n[m], errors="coerce")

    cl = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    rows = []
    for cid, sz in n["community"].value_counts().head(args.top).items():
        sub = n[n["community"] == cid]
        members = sub[~sub["is_owner"].astype(bool)].sort_values(
            "betweenness", ascending=False)["author_name"].tolist()
        glosses = [g for g in d[d["community"] == cid]["gloss"].tolist() if g][:200]
        occ = []
        if len(prof):
            pm = prof[prof["user"].isin(sub["user"])]
            occ = [w for w in pm["work"].tolist() if w][:20]
        disc = {m: sub[m].mean() for m in ["insight", "civility", "politeness", "stance"]}
        info = describe(cl, cid, members, glosses, occ, disc)
        rows.append({"community": cid, "size": int(sz),
                     "label": info.get("label", ""),
                     "description": info.get("description", "")})
        print(f"\nC{cid} ({sz}) — {info.get('label','?')}")
        print(f"  {info.get('description','')}")
    pd.DataFrame(rows).to_csv(DATA / "community_profiles.csv", index=False)
    print(f"\n-> data/community_profiles.csv")


if __name__ == "__main__":
    main()
