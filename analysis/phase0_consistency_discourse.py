#!/usr/bin/env python3
"""Phase 0d addendum: test-retest reliability of the v1 discourse dims
(politeness, constructiveness, insight, civility, stance) — the dims behind
the P2 reply-homophily headline that were absent from the first re-test.

Re-scores the SAME 200 comments used in phase0_consistency (seed 7) with the
identical v1 rubric; appends results to data/consistency_report.md.

    python -m analysis.phase0_consistency_discourse
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from analysis.discourse import CHUNK, client, score_chunk
from analysis.phase0_consistency import N, SEED, compare

DATA = Path(__file__).resolve().parent.parent / "data"
DIMS = ["politeness", "constructiveness", "insight", "civility", "stance"]


def main() -> None:
    com = pd.read_csv(DATA / "comments.csv").fillna("")
    orig = pd.read_csv(DATA / "discourse_comments.csv").drop_duplicates("comment_id")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    scored = set(la["comment_id"]) & set(lb["comment_id"])
    pool = com[com["comment_id"].isin(scored)
               & (com["text_original"].astype(str).str.len() >= 10)]
    sample = pool.sample(n=min(N, len(pool)), random_state=SEED)   # same 200
    sample = sample[sample["comment_id"].isin(set(orig["comment_id"]))]
    print(f"re-scoring {len(sample)} comments on v1 discourse rubric")

    rows = sample.to_dict("records")
    chunks = [rows[i:i + CHUNK] for i in range(0, len(rows), CHUNK)]
    cl = client()
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(lambda c: score_chunk(cl, c), chunks))
    new = pd.DataFrame([r for chunk in results for r in chunk])
    new.to_csv(DATA / "validation" / "rescore_discourse.csv", index=False)

    tab = compare(orig, new, DIMS)
    print(tab.to_string(index=False))

    add = ["", "## Pass DISCOURSE (v1 dims, re-tested 2026-06-06)", "",
           tab.to_string(index=False), "",
           "These are the dims behind the reply-homophily headline (P2); "
           "re-tested on the same 200-comment sample with the identical v1 "
           "rubric.", ""]
    p = DATA / "consistency_report.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n".join(add),
                 encoding="utf-8")
    print(f"appended to {p}")


if __name__ == "__main__":
    main()
