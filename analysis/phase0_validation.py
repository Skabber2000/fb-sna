#!/usr/bin/env python3
"""Phase 0c: stratified human-validation sample.

Draws ~450 comments stratified by language x irony band x affect band
(oversampling rare strata: RU, ironic, author-directed affect), and writes:
  data/validation/coder_sheet.csv  - randomized order, text only, empty
                                     scoring columns (coders stay blind)
  data/validation/answer_key.csv   - LLM scores for the sampled ids
  docs/CODING_MANUAL.md is written separately (static).

    python -m analysis.phase0_validation
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "validation"
TARGET = 450
SEED = 42
CODER_DIMS = ["aff", "akind", "ang", "iro", "cnt", "evid", "ogh"]


def band(s: pd.Series, edges: list[float], labels: list[str]) -> pd.Series:
    return pd.cut(pd.to_numeric(s, errors="coerce"), edges, labels=labels,
                  include_lowest=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)

    com = pd.read_csv(DATA / "comments.csv").fillna("")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    df = (com[["comment_id", "text_original", "lang"]]
          .merge(la, on="comment_id")
          .merge(lb[["comment_id", "evid", "ogh"]], on="comment_id"))
    df = df[df["text_original"].astype(str).str.len() >= 10]

    df["lang_s"] = df["lang"].where(df["lang"].isin(["uk", "ru", "en"]), "other")
    df["iro_b"] = band(df["iro"], [-0.1, 0.5, 2.5, 4.1], ["none", "mid", "high"])
    df["aff_b"] = band(df["aff"], [-4.1, -0.5, 0.5, 4.1], ["neg", "zero", "pos"])
    df["stratum"] = (df["lang_s"].astype(str) + "|" + df["iro_b"].astype(str)
                     + "|" + df["aff_b"].astype(str))

    # proportional allocation with a floor so rare strata are represented
    sizes = df.groupby("stratum").size()
    alloc = (sizes / sizes.sum() * TARGET).round().astype(int).clip(lower=4)
    alloc = alloc.clip(upper=sizes)            # can't take more than exists
    picks = []
    for stratum, n in alloc.items():
        pool = df[df["stratum"] == stratum]
        picks.append(pool.sample(n=int(n), random_state=rng.integers(1 << 30)))
    sample = pd.concat(picks).sample(frac=1, random_state=SEED)  # shuffle order
    print(f"sample: {len(sample)} comments across {len(alloc)} strata")
    print(sample.groupby(["lang_s", "iro_b"], observed=True).size().to_string())

    key_cols = ["comment_id", "lang_s", "stratum"] + CODER_DIMS
    sample[key_cols].to_csv(OUT / "answer_key.csv", index=False)

    sheet = sample[["comment_id", "text_original"]].copy()
    for d in CODER_DIMS:                       # blind: empty columns to fill
        sheet[f"coder_{d}"] = ""
    sheet.to_csv(OUT / "coder_sheet.csv", index=False, encoding="utf-8-sig")
    print(f"wrote {OUT / 'coder_sheet.csv'} (blind) and answer_key.csv")


if __name__ == "__main__":
    main()
