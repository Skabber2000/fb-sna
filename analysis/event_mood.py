#!/usr/bin/env python3
"""War-event mood join: does audience emotion shift around major war events?

Comments are dated at post-day grain (post_time anchor). For each event in
data/war_events.csv: compare emotion means in [event, event+7d] windows vs
the all-period baseline, aggregated by event category. Plus a monthly mood
series with event markers.

Outputs: data/event_mood.md, figures/event_mood.png (light theme)

    python -m analysis.event_mood
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FIG = DATA / "figures"
DIMS = ["ang", "anx", "hop", "rsg", "ent", "cnt", "iro", "aff"]
WIN = 7          # days after event
MIN_WIN = 25     # min comments in a window to count it


def load() -> pd.DataFrame:
    com = pd.read_csv(DATA / "comments.csv").fillna("")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    posts = pd.read_csv(DATA / "posts.csv")[["post_id", "post_time"]]
    df = (com[["comment_id", "post_id"]]
          .merge(la, on="comment_id")
          .merge(posts, on="post_id", how="left"))
    df["dt"] = pd.to_datetime(df["post_time"], errors="coerce")
    df = df[df["dt"].notna() & (df["dt"] >= "2023-09-01")]
    for d in DIMS:
        df[d] = pd.to_numeric(df[d], errors="coerce")
    return df


def main() -> None:
    df = load()
    ev = pd.read_csv(DATA / "war_events.csv")
    ev["dt"] = pd.to_datetime(ev["date"])
    base = df[DIMS].mean()
    print(f"{len(df)} dated scored comments; baseline:\n{base.round(3).to_string()}")

    # per-event windows
    rows = []
    for _, e in ev.iterrows():
        w = df[(df["dt"] >= e["dt"]) & (df["dt"] < e["dt"] + pd.Timedelta(days=WIN))]
        if len(w) < MIN_WIN:
            continue
        r = {"event": e["event"][:60], "date": e["date"],
             "category": e["category"], "n": len(w)}
        for d in DIMS:
            r[d] = round(w[d].mean() - base[d], 3)      # delta vs baseline
        rows.append(r)
    win = pd.DataFrame(rows)
    win.to_csv(DATA / "event_windows.csv", index=False)

    # category aggregate (weighted by n)
    cat = (win.groupby("category")
           .apply(lambda g: pd.Series(
               {**{d: np.average(g[d], weights=g["n"]) for d in DIMS},
                "n_events": len(g), "n_comments": g["n"].sum()}),
               include_groups=False)
           .round(3)
           .sort_values("ang", ascending=False))

    # monthly series + markers
    df["month"] = df["dt"].dt.to_period("M").dt.to_timestamp()
    mon = df.groupby("month")[DIMS].mean()
    fig, ax = plt.subplots(figsize=(13, 6), facecolor="white")
    for d, c in [("ang", "#c0392b"), ("anx", "#e67e22"), ("hop", "#27ae60"),
                 ("rsg", "#7f8c8d"), ("iro", "#8e44ad")]:
        ax.plot(mon.index, mon[d], label=d, color=c, lw=2)
    for _, e in ev.iterrows():
        if e["dt"] >= mon.index.min():
            ax.axvline(e["dt"], color="#bbb", lw=0.7, zorder=0)
    ax.set_facecolor("white")
    ax.set_title("Monthly mean expressed emotion, war events marked (grey)")
    ax.legend(loc="upper left", ncol=5)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "event_mood.png", dpi=130)

    # strongest single-event responses
    win["mag"] = win[["ang", "anx", "hop", "rsg"]].abs().sum(axis=1)
    top = win.nlargest(10, "mag")

    lines = ["# War-Event Mood Join", "",
             f"{len(df)} dated scored comments; {len(win)} events with >= "
             f"{MIN_WIN} comments in a {WIN}-day window. Values are deltas "
             "vs the all-period baseline.", "",
             "## By event category (n-weighted mean delta)", "",
             cat.to_string(), "",
             "## Strongest single-event mood responses", "",
             top[["date", "event", "category", "n", "ang", "anx", "hop",
                  "rsg", "aff"]].to_string(index=False), "",
             "## Caveats",
             "- Comment dates are post-anchored (day grain); selection runs "
             "through what the OWNER posted after events - this measures the "
             "audience's response conditional on his coverage.",
             "- Deltas confound event effect with topic effect (events trigger "
             "topical posts which attract their own registers).", ""]
    (DATA / "event_mood.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nby category:\n{cat[['ang', 'anx', 'hop', 'rsg', 'n_events']].to_string()}")
    print(f"\nwrote {DATA / 'event_mood.md'} + figures/event_mood.png")


if __name__ == "__main__":
    main()
