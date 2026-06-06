#!/usr/bin/env python3
"""Multi-layer psychographic scoring of comments via Claude (Haiku 4.5).

Two rubric passes over the same comments (quality > one mega-rubric):
  PASS A (expressive): emotions, author-affect (hate..love), wellbeing
                       signals, register.            -> layers_a.csv
  PASS B (worldview):  moral foundations, social values, epistemic style,
                       political stance, outgroup hostility, gender/
                       sexuality attitudes.          -> layers_b.csv

Scores native-language text (UK/RU/EN). Resumable: appends per chunk,
reruns skip scored comment_ids. Wellbeing + outgroup dimensions are
reported AGGREGATE-ONLY downstream (see docs/ETHICS.md).

    python -m analysis.layers --pass a --limit 0
    python -m analysis.layers --pass b --limit 0
    python -m analysis.layers --aggregate
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
CHUNK = 12
WORKERS = 6

CTX = """Comments are from the public Facebook of a Ukrainian public intellectual
("the author") who posts on defense, technology, economy, politics, society.
Comments may be Ukrainian, Russian, English or mixed — score the ORIGINAL text.
The audience is heavily ironic: distinguish irony/sarcasm from literal hostility.
Score ONLY what is actually expressed in the text. When a dimension is not
expressed, use 0. Return ONLY a JSON array, one object per numbered comment,
in input order. No prose, no code fences."""

RUBRIC_A = CTX + """

For EACH numbered comment return:
{"i":<n>,
 "ang":0-4 anger/outrage, "iro":0-4 irony/sarcasm, "hop":0-4 hope/optimism,
 "rsg":0-4 resignation/fatalism, "ent":0-4 enthusiasm/excitement,
 "anx":0-4 anxiety/fear, "cnt":0-4 contempt/disdain,
 "aff":-4..4 feeling expressed toward THE AUTHOR HIMSELF — only when directed
        at the author (addressing him, praising/attacking HIM or his work).
        Anger/criticism aimed at third parties (governments, the West, groups,
        situations) is NOT author-directed -> aff=0.
        (-4 hate, -2 hostility, 0 none/neutral, 2 warmth, 4 love/admiration),
 "akind":"none|admiration|gratitude|warmth|respect|teasing|condescension|mockery|hostility",
 "dis":0-4 expressed personal distress/suffering,
 "exh":0-4 expressed exhaustion/burnout/war-fatigue,
 "rsl":0-4 expressed resilience/coping/constructive determination,
 "frm":0-4 register formality (0 slang/profane, 4 formal/academic),
 "hum":0-4 humor presence, "prf":0-4 profanity}"""

RUBRIC_B = CTX + """

For EACH numbered comment return (0 = not expressed / neutral):
{"i":<n>,
 "care":0-4,"fair":0-4,"loya":0-4,"auth":0-4,"libe":0-4
   (moral foundations the comment APPEALS TO: care/harm, fairness/cheating,
    ingroup loyalty, authority/order, liberty/autonomy),
 "trad":-2..2 (-2 secular-rational/progressive, +2 traditional/religious),
 "sexp":-2..2 (-2 survival/material-security values, +2 self-expression/post-material),
 "indv":-2..2 (-2 collectivist framing, +2 individualist framing),
 "scfr":-2..2 (-2 prioritizes security/order, +2 prioritizes freedom/rights),
 "evid":0-4 evidence-based reasoning (facts, sources, specifics),
 "cnsp":0-4 conspiratorial reasoning (hidden actors, secret plans, "them"),
 "dogm":0-4 dogmatism/certainty (0 open/hedged, 4 absolute certainty),
 "itru":-2..2 trust in Ukrainian institutions expressed (-2 deep distrust, +2 trust),
 "wtru":-2..2 trust/attitude toward West/EU/US (-2 hostile, +2 trusting),
 "hawk":-2..2 war stance (-2 dove/negotiate, +2 hawk/fight on),
 "ogh":0-4 hostility toward an ethnic/national/religious outgroup,
 "ogt":"none|russians|jews|west|roma|migrants|muslims|poles|other" (target if ogh>0),
 "ogk":"none|slur|conspiracy|stereotype|dogwhistle|dehumanization" (kind if ogh>0),
 "lgbt":-2..2 attitude toward LGBTQ/gender diversity if expressed,
 "gtrd":-2..2 gender-role view (-2 egalitarian, +2 traditionalist),
 "sxm":0-4 sexism/misogyny markers}"""

PASSES = {
    "a": {"rubric": RUBRIC_A, "out": DATA / "layers_a.csv",
          "num": ["ang", "iro", "hop", "rsg", "ent", "anx", "cnt", "aff",
                  "dis", "exh", "rsl", "frm", "hum", "prf"],
          "str_": ["akind"]},
    "b": {"rubric": RUBRIC_B, "out": DATA / "layers_b.csv",
          "num": ["care", "fair", "loya", "auth", "libe", "trad", "sexp",
                  "indv", "scfr", "evid", "cnsp", "dogm", "itru", "wtru",
                  "hawk", "ogh", "lgbt", "gtrd", "sxm"],
          "str_": ["ogt", "ogk"]},
}


def client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("["), text.rfind("]")
    return json.loads(text[start:end + 1]) if start >= 0 else []


def score_chunk(cl, rows: list[dict], spec: dict) -> list[dict]:
    numbered = "\n".join(f'{n+1}. "{(r["text_original"] or "")[:300]}"'
                         for n, r in enumerate(rows))
    msg = cl.messages.create(
        model=MODEL, max_tokens=4000,
        system=[{"type": "text", "text": spec["rubric"],
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Score these comments:\n{numbered}"}],
    )
    parsed = _parse_json(msg.content[0].text)
    out = []
    for n, r in enumerate(rows):
        rec = next((p for p in parsed if p.get("i") == n + 1), None) or {}
        row = {"comment_id": r["comment_id"], "user": r["user"]}
        for k in spec["num"]:
            row[k] = rec.get(k, "")
        for k in spec["str_"]:
            row[k] = str(rec.get(k, ""))[:40]
        out.append(row)
    return out


def run(pass_name: str, limit: int) -> None:
    spec = PASSES[pass_name]
    df = pd.read_csv(DATA / "comments.csv").fillna("")
    df = df[df["text_original"].astype(str).str.len() >= 3]
    done = set()
    if spec["out"].exists():
        done = set(pd.read_csv(spec["out"])["comment_id"])
    todo = df[~df["comment_id"].isin(done)]
    if limit:
        todo = todo.head(limit)
    chunks = [todo.iloc[i:i + CHUNK].to_dict("records")
              for i in range(0, len(todo), CHUNK)]
    print(f"pass {pass_name}: {len(df)} comments, {len(done)} done, "
          f"scoring {len(todo)} in {len(chunks)} chunks")
    if not chunks:
        return
    cl = client()
    header_written = spec["out"].exists()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(score_chunk, cl, ch, spec): i for i, ch in enumerate(chunks)}
        for k, fut in enumerate(as_completed(futs), 1):
            try:
                recs = fut.result()
            except Exception as e:                       # noqa: BLE001
                print(f"  chunk failed: {e}")
                continue
            pd.DataFrame(recs).to_csv(spec["out"], mode="a",
                                      header=not header_written, index=False)
            header_written = True
            if k % 25 == 0:
                print(f"  {k}/{len(chunks)} chunks")
    print(f"Done -> {spec['out']}")


def aggregate() -> None:
    """Per-user means for every numeric dim of both passes -> layers_users.csv,
    merged into nodes_analyzed.csv. String tags aggregated as top non-none value
    counts at comment level only (used by multilayer.py at cluster level)."""
    frames = []
    for name, spec in PASSES.items():
        if not spec["out"].exists():
            print(f"pass {name} output missing, skipping")
            continue
        d = pd.read_csv(spec["out"])
        d = d.drop_duplicates(subset="comment_id", keep="first")
        for m in spec["num"]:
            d[m] = pd.to_numeric(d[m], errors="coerce")
        g = d.groupby("user")
        prof = g[spec["num"]].mean().round(3)
        prof[f"n_{name}"] = g.size()
        frames.append(prof)
    if not frames:
        return
    users = pd.concat(frames, axis=1).reset_index()
    users.to_csv(DATA / "layers_users.csv", index=False)
    print(f"layers_users.csv: {len(users)} people, {users.shape[1]-1} columns")

    na_path = DATA / "nodes_analyzed.csv"
    if na_path.exists():
        na = pd.read_csv(na_path)
        drop = [c for c in users.columns if c != "user" and c in na.columns]
        na = na.drop(columns=drop, errors="ignore").merge(users, on="user", how="left")
        na.to_csv(na_path, index=False)
        print(f"merged into nodes_analyzed.csv ({na.shape[1]} cols)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Multi-layer comment scoring")
    ap.add_argument("--pass", dest="pass_name", choices=["a", "b"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--aggregate", action="store_true")
    args = ap.parse_args()
    if args.aggregate:
        aggregate()
    elif args.pass_name:
        run(args.pass_name, args.limit)
    else:
        print("specify --pass a|b or --aggregate")


if __name__ == "__main__":
    main()
