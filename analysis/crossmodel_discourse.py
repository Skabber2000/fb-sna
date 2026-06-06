#!/usr/bin/env python3
"""Cross-model convergence for the DISCOURSE dims (incl. the headline
civility) — same 200-comment sample, Grok vs production Haiku scores.
Appends to data/crossmodel.md.

    python -m analysis.crossmodel_discourse
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from analysis.crossmodel import grok_chunk
from analysis.discourse import METRICS, RUBRIC
from analysis.layers import CHUNK
from analysis.phase0_consistency import N, SEED, compare

DATA = Path(__file__).resolve().parent.parent / "data"
VAL = DATA / "validation"
SPEC = {"rubric": RUBRIC, "num": METRICS, "str_": ["gloss"]}


def main() -> None:
    com = pd.read_csv(DATA / "comments.csv").fillna("")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    orig = pd.read_csv(DATA / "discourse_comments.csv") \
        .drop_duplicates("comment_id")
    scored = set(la["comment_id"]) & set(lb["comment_id"])
    pool = com[com["comment_id"].isin(scored)
               & (com["text_original"].astype(str).str.len() >= 10)]
    sample = pool.sample(n=min(N, len(pool)), random_state=SEED)  # same 200
    sample = sample[sample["comment_id"].isin(set(orig["comment_id"]))]
    print(f"cross-model discourse scoring {len(sample)} comments")

    rows = sample.to_dict("records")
    chunks = [rows[i:i + CHUNK] for i in range(0, len(rows), CHUNK)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda c: grok_chunk(c, SPEC), chunks))
    new = pd.DataFrame([r for ch in res for r in ch])
    new.to_csv(VAL / "grok_discourse.csv", index=False)
    tab = compare(orig, new, METRICS)
    print(tab.to_string(index=False))

    p = DATA / "crossmodel.md"
    p.write_text(p.read_text(encoding="utf-8")
                 + "\n## Pass DISCOURSE (incl. headline civility)\n\n"
                 + tab.to_string(index=False) + "\n", encoding="utf-8")
    print(f"appended to {p}")


if __name__ == "__main__":
    main()
