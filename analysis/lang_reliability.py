#!/usr/bin/env python3
"""Audit item 3: per-language instrument reliability.

Stratifies the existing 200-comment re-test by comment language, then tops
up the RU stratum (re-scoring additional already-scored RU comments on both
passes) so the RU estimate has usable n. Key claim-bearing dims only.

Output: data/lang_reliability.md (+ appended to consistency_report.md)

    python -m analysis.lang_reliability
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from analysis.layers import CHUNK, PASSES, client, score_chunk
from analysis.phase0_consistency import compare

DATA = Path(__file__).resolve().parent.parent / "data"
VAL = DATA / "validation"
RU_TARGET = 150
SEED = 41
KEY_A = ["ang", "iro", "cnt", "aff", "hop", "rsg"]
KEY_B = ["cnsp", "ogh", "evid", "wtru", "hawk", "trad"]


def rescore(df: pd.DataFrame, pass_name: str) -> pd.DataFrame:
    spec = PASSES[pass_name]
    rows = df.to_dict("records")
    chunks = [rows[i:i + CHUNK] for i in range(0, len(rows), CHUNK)]
    cl = client()
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda c: score_chunk(cl, c, spec), chunks))
    return pd.DataFrame([r for ch in res for r in ch])


def main() -> None:
    com = pd.read_csv(DATA / "comments.csv").fillna("")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    ra = pd.read_csv(VAL / "rescore_a.csv").drop_duplicates("comment_id")
    rb = pd.read_csv(VAL / "rescore_b.csv").drop_duplicates("comment_id")
    lang = com.set_index("comment_id")["lang"]

    # top up RU: already-rescored RU ids + fresh RU sample
    done_ru = set(ra["comment_id"]) & set(
        lang[lang == "ru"].index)
    scored = set(la["comment_id"]) & set(lb["comment_id"])
    pool = com[(com["lang"] == "ru") & com["comment_id"].isin(scored)
               & ~com["comment_id"].isin(set(ra["comment_id"]))
               & (com["text_original"].astype(str).str.len() >= 10)]
    need = max(0, RU_TARGET - len(done_ru))
    extra = pool.sample(n=min(need, len(pool)), random_state=SEED)
    print(f"RU already re-scored: {len(done_ru)}; topping up {len(extra)}")
    if len(extra):
        ra2 = rescore(extra, "a")
        rb2 = rescore(extra, "b")
        ra = pd.concat([ra, ra2], ignore_index=True)
        rb = pd.concat([rb, rb2], ignore_index=True)
        ra.to_csv(VAL / "rescore_a.csv", index=False)
        rb.to_csv(VAL / "rescore_b.csv", index=False)

    lines = ["# Per-Language Instrument Reliability (audit item 3)", "",
             "Test-retest Pearson r stratified by comment language; RU "
             f"stratum topped up to ~{RU_TARGET}.", ""]
    for lg in ["uk", "ru", "en"]:
        ids = set(lang[lang == lg].index)
        for pname, orig, new, dims in [("A", la, ra, KEY_A),
                                       ("B", lb, rb, KEY_B)]:
            o = orig[orig["comment_id"].isin(ids)]
            n = new[new["comment_id"].isin(ids)]
            tab = compare(o, n, dims)
            if tab.empty:
                continue
            lines += [f"## {lg.upper()} — pass {pname} "
                      f"(n={len(set(o['comment_id']) & set(n['comment_id']))})",
                      "", tab.to_string(index=False), ""]
    (DATA / "lang_reliability.md").write_text("\n".join(lines),
                                              encoding="utf-8")
    p = DATA / "consistency_report.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n\n"
                 + "\n".join(lines[2:]), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
