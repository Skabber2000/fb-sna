#!/usr/bin/env python3
"""Audit item 4: cross-model convergent validity.

Scores the SAME 200-comment consistency sample with a different frontier
model family (Grok via xAI API) using the identical rubrics, then reports
per-dimension convergence (Pearson r, within-1) between the two instruments.
High convergence = the constructs are not artifacts of one model family.

Output: data/crossmodel.md; raw scores data/validation/grok_{a,b}.csv

    python -m analysis.crossmodel
"""
from __future__ import annotations

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from analysis.layers import CHUNK, PASSES, _parse_json
from analysis.phase0_consistency import N, SEED, compare

DATA = Path(__file__).resolve().parent.parent / "data"
VAL = DATA / "validation"
KEY = Path(r"C:\Users\Eugene Nayshtetik\Desktop\Grok_API.txt") \
    .read_text(encoding="utf-8").strip()
MODEL = "grok-4.3"
URL = "https://api.x.ai/v1/chat/completions"


def grok_chunk(rows: list[dict], spec: dict) -> list[dict]:
    numbered = "\n".join(f'{n + 1}. "{(r["text_original"] or "")[:300]}"'
                         for n, r in enumerate(rows))
    body = json.dumps({
        "model": MODEL, "max_tokens": 4000, "temperature": 0,
        "messages": [{"role": "system", "content": spec["rubric"]},
                     {"role": "user",
                      "content": f"Score these comments:\n{numbered}"}],
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        text = json.load(resp)["choices"][0]["message"]["content"]
    parsed = _parse_json(text)
    out = []
    for n, r in enumerate(rows):
        rec = next((p for p in parsed if p.get("i") == n + 1), None) or {}
        row = {"comment_id": r["comment_id"]}
        for k in spec["num"]:
            row[k] = rec.get(k, "")
        for k in spec["str_"]:
            row[k] = str(rec.get(k, ""))[:40]
        out.append(row)
    return out


def main() -> None:
    com = pd.read_csv(DATA / "comments.csv").fillna("")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    scored = set(la["comment_id"]) & set(lb["comment_id"])
    pool = com[com["comment_id"].isin(scored)
               & (com["text_original"].astype(str).str.len() >= 10)]
    sample = pool.sample(n=min(N, len(pool)), random_state=SEED)  # same 200
    print(f"cross-model scoring {len(sample)} comments with {MODEL}")

    lines = ["# Cross-Model Convergent Validity (audit item 4)", "",
             f"Same 200-comment sample, identical rubrics; instrument A = "
             f"claude-haiku-4-5 (production scores), instrument B = {MODEL} "
             "(temperature 0). Convergence = Pearson r between instruments.",
             ""]
    rows = sample.to_dict("records")
    for pname, orig in [("a", la), ("b", lb)]:
        spec = PASSES[pname]
        chunks = [rows[i:i + CHUNK] for i in range(0, len(rows), CHUNK)]
        with ThreadPoolExecutor(max_workers=4) as ex:
            res = list(ex.map(lambda c: grok_chunk(c, spec), chunks))
        new = pd.DataFrame([r for ch in res for r in ch])
        new.to_csv(VAL / f"grok_{pname}.csv", index=False)
        tab = compare(orig, new, spec["num"])
        lines += [f"## Pass {pname.upper()}", "", tab.to_string(index=False),
                  ""]
        print(f"pass {pname}:\n{tab.to_string(index=False)}")
    lines += ["## Reading",
              "- r >= 0.6 cross-model: construct robust to model family.",
              "- r 0.4-0.6: model-sensitive; rely on human validation.",
              "- r < 0.4: likely instrument artifact; flag the dimension.", ""]
    (DATA / "crossmodel.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {DATA / 'crossmodel.md'}")


if __name__ == "__main__":
    main()
