#!/usr/bin/env python3
"""PRE-SPECIFIED confirmatory analysis for the human-validation gate.

Committed BEFORE coder data arrival per docs/PREREGISTRATION.md. When the
two coder sheets land in data/validation/ as coder_sheet_<initials>.csv,
run this once; its outputs are the confirmatory results. Any further
analysis of the coder data is exploratory by definition.

  H1: Krippendorff alpha (ordinal; coder1 x coder2 x LLM) >= 0.667 per dim
  H2: |mean(LLM - human)| difference UK vs RU <= 0.25 scale points (TOST)
  H3: tone-ideology block difference re-estimated with human scores on the
      subsample's users does not flip sign

Requires: pip install krippendorff

    python -m analysis.validate_human coder_sheet_AB.csv coder_sheet_CD.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
VAL = DATA / "validation"
DIMS = ["aff", "ang", "iro", "cnt", "evid", "ogh"]   # akind is categorical
ALPHA_GATE = 0.667
TOST_BOUND = 0.25


def load(c1: str, c2: str) -> pd.DataFrame:
    key = pd.read_csv(VAL / "answer_key.csv")
    a = pd.read_csv(VAL / c1)
    b = pd.read_csv(VAL / c2)
    m = key.merge(a, on="comment_id", suffixes=("", "_c1")) \
           .merge(b, on="comment_id", suffixes=("", "_c2"))
    return m


def h1_alpha(m: pd.DataFrame) -> pd.DataFrame:
    import krippendorff
    rows = []
    for d in DIMS:
        mat = np.vstack([
            pd.to_numeric(m[f"coder_{d}"], errors="coerce"),
            pd.to_numeric(m[f"coder_{d}_c2"], errors="coerce"),
            pd.to_numeric(m[d], errors="coerce"),
        ])
        alpha = krippendorff.alpha(reliability_data=mat,
                                   level_of_measurement="ordinal")
        rows.append({"dim": d, "alpha": round(alpha, 3),
                     "passes": alpha >= ALPHA_GATE})
    return pd.DataFrame(rows)


def h2_language_bias(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for d in ["aff", "ang", "ogh"]:
        llm = pd.to_numeric(m[d], errors="coerce")
        hum = (pd.to_numeric(m[f"coder_{d}"], errors="coerce")
               + pd.to_numeric(m[f"coder_{d}_c2"], errors="coerce")) / 2
        bias = llm - hum
        rec = {"dim": d}
        for lg in ["uk", "ru"]:
            rec[f"bias_{lg}"] = round(bias[m["lang_s"] == lg].mean(), 3)
        diff = bias[m["lang_s"] == "uk"] .mean() - \
            bias[m["lang_s"] == "ru"].mean()
        # TOST via two one-sided t approximations
        from scipy.stats import ttest_ind
        bu = bias[m["lang_s"] == "uk"].dropna()
        br = bias[m["lang_s"] == "ru"].dropna()
        se = np.sqrt(bu.var() / len(bu) + br.var() / len(br))
        from scipy.stats import norm
        p1 = 1 - norm.cdf((diff + TOST_BOUND) / se)     # H0: diff <= -bound
        p2 = norm.cdf((diff - TOST_BOUND) / se)          # H0: diff >= +bound
        rec.update({"uk_minus_ru": round(diff, 3),
                    "tost_p": round(max(p1, p2), 4),
                    "equivalent": max(p1, p2) < 0.05})
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: python -m analysis.validate_human "
                 "coder_sheet_X.csv coder_sheet_Y.csv")
    m = load(sys.argv[1], sys.argv[2])
    print(f"{len(m)} triple-coded comments")
    t1 = h1_alpha(m)
    t2 = h2_language_bias(m)
    out = ["# Confirmatory Human-Validation Results (pre-registered)", "",
           "## H1: Krippendorff alpha (ordinal)", t1.to_string(index=False),
           "", "## H2: per-language LLM bias (TOST, bound 0.25)",
           t2.to_string(index=False), "",
           "## H3: run analysis/difference_test.py variant with human "
           "scores substituted for the subsample's users (manual step; "
           "report sign of pooled block difference).", ""]
    (DATA / "human_validation_results.md").write_text("\n".join(out),
                                                      encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
