#!/usr/bin/env python3
"""Temporal dynamics + language-shift layers (offline, comments.csv).

Comment times come from FB relative labels parsed at capture (e.g. '3d', '2w',
'5 March') — precision varies; monthly resolution is the honest grain.

Outputs:
  data/temporal.md, data/language_shift.md, figures/temporal_*.png

    python -m analysis.temporal
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = DATA / "figures"
CAPTURE_DATE = datetime(2026, 6, 4)          # capture campaign date

REL = re.compile(r"^(?:(a|an|\d+)\s+)?(minute|hour|day|week|month|year)s?\s+ago",
                 re.I)


def parse_rel(s: str) -> datetime | None:
    """Parse FB relative labels: '3 weeks ago', 'a year ago', 'yesterday'."""
    s = str(s).strip().lower()
    if s.startswith("just now"):
        return CAPTURE_DATE
    if s.startswith("yesterday"):
        return CAPTURE_DATE - timedelta(days=1)
    m = REL.match(s)
    if not m:
        return None
    n = 1 if m.group(1) in (None, "a", "an") else int(m.group(1))
    days = {"minute": n / 1440, "hour": n / 24, "day": n,
            "week": n * 7, "month": n * 30.4, "year": n * 365}[m.group(2)]
    return CAPTURE_DATE - timedelta(days=days)


def main() -> None:
    com = pd.read_csv(DATA / "comments.csv").fillna("")
    posts = pd.read_csv(DATA / "posts.csv")[["post_id", "post_time"]]
    posts["post_dt"] = pd.to_datetime(posts["post_time"], errors="coerce")
    com = com.merge(posts, on="post_id", how="left")

    # anchor: post date (comments land within days of the post); refine with
    # the relative label when it parses to a plausible date >= post date.
    rel = com["created_time"].map(parse_rel)
    com["dt"] = com["post_dt"]
    fine = rel.notna() & com["post_dt"].notna() & \
        (rel >= com["post_dt"] - pd.Timedelta(days=2)) & \
        (rel - com["post_dt"] <= pd.Timedelta(days=365))
    com.loc[fine, "dt"] = rel[fine]
    com.loc[com["dt"].isna(), "dt"] = rel[com["dt"].isna()]
    ok = com[com["dt"].notna()].copy()
    print(f"{len(com)} comments, datable: {len(ok)} ({len(ok)/len(com):.0%}; "
          f"label-refined: {int(fine.sum())})")
    ok["month"] = ok["dt"].dt.to_period("M")

    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    for c in ["ang", "rsg", "hop", "exh", "iro"]:
        la[c] = pd.to_numeric(la[c], errors="coerce")
    ok = ok.merge(la[["comment_id", "ang", "rsg", "hop", "exh", "iro"]],
                  on="comment_id", how="left")

    # ---- monthly volume + mood trajectory ---------------------------------
    mm = ok.groupby("month").agg(n=("comment_id", "size"), ang=("ang", "mean"),
                                 rsg=("rsg", "mean"), hop=("hop", "mean"),
                                 iro=("iro", "mean"))
    mm = mm[mm["n"] >= 30]
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    x = mm.index.astype(str)
    axes[0].bar(x, mm["n"], color="#A8C4E0")
    axes[0].set_ylabel("comments / month")
    axes[0].set_title("Engagement volume and mood trajectory")
    for c, col in [("ang", "#C44E52"), ("rsg", "#8172B2"),
                   ("hop", "#55A868"), ("iro", "#CCB974")]:
        axes[1].plot(x, mm[c], label=c, color=col, lw=2)
    axes[1].legend()
    axes[1].set_ylabel("mean score")
    plt.setp(axes[1].get_xticklabels(), rotation=60, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "temporal_mood.png", dpi=150, facecolor="white")
    plt.close(fig)

    # ---- cohorts & churn ----------------------------------------------------
    first = ok.groupby("user")["dt"].min().dt.to_period("Q").rename("cohort")
    last = ok.groupby("user")["dt"].max().rename("last_seen")
    nact = ok.groupby("user").size().rename("n")
    coh = pd.concat([first, last, nact], axis=1)
    recent_cut = CAPTURE_DATE - timedelta(days=90)
    coh["active_recent"] = coh["last_seen"] >= recent_cut
    ctab = coh.groupby("cohort").agg(joined=("n", "size"),
                                     still_active=("active_recent", "mean"),
                                     mean_comments=("n", "mean")).round(2)
    lines = ["# Temporal dynamics", "",
             f"Datable comments: {len(ok)}/{len(com)} "
             f"({len(ok)/len(com):.0%}; relative timestamps -> monthly grain)",
             "", "## Cohorts (first-seen quarter)", ctab.to_string(), "",
             "## Monthly mood (n>=30)", mm.round(2).to_string()]
    (DATA / "temporal.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- language shift -----------------------------------------------------
    ok["lang3"] = ok["lang"].map(lambda s: s if s in ("uk", "ru", "en") else "other")
    lm = (ok.groupby(["month", "lang3"]).size().unstack(fill_value=0))
    lm = lm[lm.sum(axis=1) >= 30]
    sh = lm.div(lm.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for c, col in [("uk", "#0057B7"), ("ru", "#C44E52"), ("en", "#55A868")]:
        if c in sh.columns:
            ax.plot(sh.index.astype(str), sh[c], label=c, color=col, lw=2)
    ax.set_ylabel("share of comments")
    ax.set_title("Comment language share over time")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=60, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "temporal_language.png", dpi=150, facecolor="white")
    plt.close(fig)

    # per-user switchers: dominant lang in first vs second half of their span
    u = ok[ok["lang3"].isin(["uk", "ru"])].copy()
    switch_rows = []
    for user, g in u.groupby("user"):
        if len(g) < 6 or g["dt"].nunique() < 4:
            continue
        g = g.sort_values("dt")
        half = len(g) // 2
        a = g.head(half)["lang3"].mode().iat[0]
        b = g.tail(half)["lang3"].mode().iat[0]
        if a != b:
            switch_rows.append({"user": user, "from": a, "to": b, "n": len(g)})
    sw = pd.DataFrame(switch_rows)
    ru_uk = len(sw[(sw["from"] == "ru") & (sw["to"] == "uk")]) if len(sw) else 0
    uk_ru = len(sw[(sw["from"] == "uk") & (sw["to"] == "ru")]) if len(sw) else 0
    eligible = sum(1 for _, g in u.groupby("user") if len(g) >= 6)
    lines = ["# Language shift (UK / RU / EN)", "",
             f"Overall shares: {ok['lang3'].value_counts(normalize=True).round(3).to_dict()}",
             "", f"Eligible bilingual-history users (>=6 dated UK/RU comments): {eligible}",
             f"Switchers RU->UK: {ru_uk}   UK->RU: {uk_ru}", "",
             "Monthly shares (n>=30):", sh.round(3).to_string()]
    (DATA / "language_shift.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote temporal.md, language_shift.md, figures")
    print(f"switchers RU->UK {ru_uk}, UK->RU {uk_ru}, eligible {eligible}")


if __name__ == "__main__":
    main()
