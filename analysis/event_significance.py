#!/usr/bin/env python3
"""Placebo-permutation significance for the war-event mood study.

For each event category: observed delta = n-weighted mean emotion in real
7-day post-event windows minus all-period baseline. Null distribution: 1000
draws of the same NUMBER of placebo event dates (uniform over the span),
identical windowing and >=25-comment filter. Two-sided p = share of null
|deltas| >= |observed|.

Outputs data/event_significance.md

    python -m analysis.event_significance
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from analysis.event_mood import MIN_WIN, WIN, load

DATA = Path(__file__).resolve().parent.parent / "data"
DIMS = ["ang", "anx", "hop", "rsg", "aff"]
NPERM = 1000
SEED = 17


def cat_delta(df: pd.DataFrame, dates: list, base: pd.Series) -> dict | None:
    deltas, ns = [], []
    for d in dates:
        w = df[(df["dt"] >= d) & (df["dt"] < d + pd.Timedelta(days=WIN))]
        if len(w) < MIN_WIN:
            continue
        deltas.append(w[DIMS].mean() - base)
        ns.append(len(w))
    if not deltas:
        return None
    arr = pd.DataFrame(deltas)
    wts = np.array(ns)
    return {d: float(np.average(arr[d], weights=wts)) for d in DIMS}


def main() -> None:
    df = load()
    base = df[DIMS].mean()
    ev = pd.read_csv(DATA / "war_events.csv")
    ev["dt"] = pd.to_datetime(ev["date"])
    lo, hi = df["dt"].min(), df["dt"].max() - pd.Timedelta(days=WIN)
    span = (hi - lo).days
    rng = np.random.default_rng(SEED)

    rows = []
    for cat, grp in ev.groupby("category"):
        obs = cat_delta(df, list(grp["dt"]), base)
        if obs is None:
            continue
        k = len(grp)
        null = {d: [] for d in DIMS}
        for _ in range(NPERM):
            dates = [lo + pd.Timedelta(days=int(x))
                     for x in rng.integers(0, span, size=k)]
            nd = cat_delta(df, dates, base)
            if nd is None:
                continue
            for d in DIMS:
                null[d].append(nd[d])
        for d in DIMS:
            arr = np.array(null[d])
            p = float((np.abs(arr) >= abs(obs[d])).mean()) if len(arr) else np.nan
            rows.append({"category": cat, "n_events": k, "dim": d,
                         "delta": round(obs[d], 3), "p_perm": round(p, 3),
                         "sig": "***" if p < .001 else "**" if p < .01
                                else "*" if p < .05 else ""})
    res = pd.DataFrame(rows)
    res.to_csv(DATA / "event_significance.csv", index=False)

    sig = res[res["p_perm"] < 0.05].sort_values("p_perm")
    lines = ["# Event-Study Significance (placebo permutation)", "",
             f"{NPERM} placebo draws per category; two-sided p vs |delta|; "
             f"window {WIN}d, min {MIN_WIN} comments; span {lo.date()}..{hi.date()}.",
             "", "## Significant category x emotion effects (p < .05)", "",
             sig.to_string(index=False), "",
             "## Full table", "", res.to_string(index=False), "",
             "Note: placebo windows inherit the owner-posting selection the "
             "same way real windows do, so this tests 'events move mood more "
             "than arbitrary dates', not pure causality.", ""]
    (DATA / "event_significance.md").write_text("\n".join(lines), encoding="utf-8")
    print(sig.to_string(index=False))
    print(f"\nwrote {DATA / 'event_significance.md'}")


if __name__ == "__main__":
    main()
