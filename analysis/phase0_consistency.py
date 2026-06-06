#!/usr/bin/env python3
"""Phase 0d: LLM self-consistency check.

Re-scores 200 already-scored comments with the identical rubric (both
passes) and compares against the original scores: Pearson r, MAE, and
exact-agreement per dimension. Output: data/consistency_report.md

    python -m analysis.phase0_consistency
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from analysis.layers import CHUNK, PASSES, client, score_chunk

DATA = Path(__file__).resolve().parent.parent / "data"
N = 200
SEED = 7


def rescore(df: pd.DataFrame, pass_name: str) -> pd.DataFrame:
    spec = PASSES[pass_name]
    rows = df.to_dict("records")
    chunks = [rows[i:i + CHUNK] for i in range(0, len(rows), CHUNK)]
    cl = client()
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda c: score_chunk(cl, c, spec), chunks))
    return pd.DataFrame([r for chunk in results for r in chunk])


def compare(orig: pd.DataFrame, new: pd.DataFrame, dims: list[str]) -> pd.DataFrame:
    m = orig.merge(new, on="comment_id", suffixes=("_1", "_2"))
    out = []
    for d in dims:
        a = pd.to_numeric(m[f"{d}_1"], errors="coerce")
        b = pd.to_numeric(m[f"{d}_2"], errors="coerce")
        ok = a.notna() & b.notna()
        a, b = a[ok], b[ok]
        if len(a) < 10:
            continue
        out.append({"dim": d, "n": len(a),
                    "pearson_r": round(a.corr(b), 3),
                    "mae": round((a - b).abs().mean(), 3),
                    "exact": round((a == b).mean(), 3),
                    "within1": round(((a - b).abs() <= 1).mean(), 3)})
    return pd.DataFrame(out)


def main() -> None:
    com = pd.read_csv(DATA / "comments.csv").fillna("")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    scored = set(la["comment_id"]) & set(lb["comment_id"])
    pool = com[com["comment_id"].isin(scored)
               & (com["text_original"].astype(str).str.len() >= 10)]
    sample = pool.sample(n=min(N, len(pool)), random_state=SEED)
    print(f"re-scoring {len(sample)} comments, both passes")

    lines = ["# LLM Self-Consistency Report (Phase 0d)", "",
             f"n = {len(sample)} comments re-scored with identical rubric/model.",
             "Test-retest reliability of the scoring instrument itself.", ""]
    for pass_name, orig in [("a", la), ("b", lb)]:
        new = rescore(sample, pass_name)
        dims = PASSES[pass_name]["num"]
        tab = compare(orig, new, dims)
        lines += [f"## Pass {pass_name.upper()}", "", tab.to_string(index=False), ""]
        print(f"pass {pass_name}:\n{tab.to_string(index=False)}")
        new.to_csv(DATA / "validation" / f"rescore_{pass_name}.csv", index=False)

    lines += ["## Interpretation",
              "- r >= 0.7 and within1 >= 0.9: dimension is reliable as scored.",
              "- r 0.4-0.7: usable with shrinkage/aggregation, flag in methods.",
              "- r < 0.4: do not base claims on this dimension without human",
              "  validation (Phase 0c) or rubric revision.", ""]
    (DATA / "consistency_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {DATA / 'consistency_report.md'}")


if __name__ == "__main__":
    main()
