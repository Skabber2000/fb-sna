#!/usr/bin/env python3
"""Audit item 6: ordinal-appropriate reliability statistics.

Spearman rho + quadratic-weighted Cohen's kappa per dimension, from the
existing re-score files. Appends to data/consistency_report.md.

    python -m analysis.consistency_extra
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

DATA = Path(__file__).resolve().parent.parent / "data"
SETS = [("a", DATA / "layers_a.csv", DATA / "validation" / "rescore_a.csv"),
        ("b", DATA / "layers_b.csv", DATA / "validation" / "rescore_b.csv"),
        ("discourse", DATA / "discourse_comments.csv",
         DATA / "validation" / "rescore_discourse.csv")]


def main() -> None:
    out = ["", "## Ordinal reliability (Spearman rho, quadratic-weighted "
           "kappa) — added 2026-06-06", ""]
    for name, orig_p, new_p in SETS:
        orig = pd.read_csv(orig_p).drop_duplicates("comment_id")
        new = pd.read_csv(new_p).drop_duplicates("comment_id")
        dims = [c for c in new.columns
                if c in orig.columns and c not in ("comment_id", "user")]
        m = orig.merge(new, on="comment_id", suffixes=("_1", "_2"))
        rows = []
        for d in dims:
            a = pd.to_numeric(m[f"{d}_1"], errors="coerce")
            b = pd.to_numeric(m[f"{d}_2"], errors="coerce")
            ok = a.notna() & b.notna()
            a, b = a[ok], b[ok]
            if len(a) < 20 or a.nunique() < 2 or b.nunique() < 2:
                continue
            rho = spearmanr(a, b).statistic
            kap = cohen_kappa_score(a.astype(int), b.astype(int),
                                    weights="quadratic")
            rows.append({"dim": d, "n": len(a), "spearman": round(rho, 3),
                         "qw_kappa": round(kap, 3)})
        tab = pd.DataFrame(rows)
        out += [f"### Pass {name.upper()}", "", tab.to_string(index=False), ""]
        print(f"pass {name}:\n{tab.to_string(index=False)}\n")
    p = DATA / "consistency_report.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n".join(out),
                 encoding="utf-8")
    print(f"appended to {p}")


if __name__ == "__main__":
    main()
