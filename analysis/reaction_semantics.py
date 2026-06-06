#!/usr/bin/env python3
"""Reaction-type semantics: per-post Like/Love/Haha/Wow/Sad/Angry/Care counts
parsed from saved reaction dialogs, crossed with post themes.

Per-PERSON reaction types are not recoverable from the captured dialogs
(badges render only for visible rows) — this layer is post-level. The 216
reaction-only people stay attributable only by presence, not emotion type;
noted honestly in the report.

    python -m analysis.reaction_semantics
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RX = DATA / "reactions_html"
FIG = DATA / "figures"

PAIR = re.compile(r'"localized_name"\s*:\s*"([A-Za-z]+)"\}\s*,\s*'
                  r'"i18n_reaction_count"\s*:\s*"[^"]*"\s*,\s*'
                  r'"reaction_count"\s*:\s*(\d+)')
TYPES = ["Like", "Love", "Care", "Haha", "Wow", "Sad", "Angry"]


def main() -> None:
    rows = []
    for f in sorted(RX.glob("*.html")):
        html = f.read_text(encoding="utf-8", errors="ignore")
        counts: dict[str, int] = {}
        for name, n in PAIR.findall(html):
            if name in TYPES:
                counts[name] = max(counts.get(name, 0), int(n))
        if counts:
            rows.append({"post_id": f.stem, **{t: counts.get(t, 0) for t in TYPES}})
    df = pd.DataFrame(rows)
    print(f"{len(df)} posts with type counts (of {len(list(RX.glob('*.html')))} dialogs)")
    posts = pd.read_csv(DATA / "posts.csv")[["post_id", "theme", "post_time"]]
    df = df.merge(posts, on="post_id", how="left")
    df.to_csv(DATA / "post_reaction_types.csv", index=False)

    tot = df[TYPES].sum()
    print("\nOverall reaction mix:")
    print((tot / tot.sum()).round(4).to_string())

    # per-theme mix (share of non-Like emotional reactions)
    by_theme = df.groupby("theme")[TYPES].sum()
    by_theme = by_theme[by_theme.sum(axis=1) >= 200]
    mix = by_theme.div(by_theme.sum(axis=1), axis=0)
    emo = by_theme[["Love", "Care", "Haha", "Wow", "Sad", "Angry"]]
    emo_mix = emo.div(emo.sum(axis=1), axis=0)
    out = ["# Reaction-type semantics (post-level)", "",
           f"Posts with reaction-type data: {len(df)}",
           f"Total reactions: {int(tot.sum()):,}", "",
           "## Overall mix", (tot / tot.sum()).round(4).to_string(), "",
           "## Per-theme full mix (incl. Like)", mix.round(3).to_string(), "",
           "## Per-theme EMOTIONAL mix (Like excluded)", emo_mix.round(3).to_string(),
           "", "Note: per-person reaction types not recoverable from captured "
           "dialogs; reaction-only members remain emotion-untyped."]
    (DATA / "reaction_semantics.md").write_text("\n".join(out), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(11, 5))
    bottom = np.zeros(len(emo_mix))
    colors = {"Love": "#E0245E", "Care": "#F7B125", "Haha": "#55A868",
              "Wow": "#4878CF", "Sad": "#8172B2", "Angry": "#C44E52"}
    for t in ["Love", "Care", "Haha", "Wow", "Sad", "Angry"]:
        ax.bar(emo_mix.index, emo_mix[t], bottom=bottom, label=t, color=colors[t])
        bottom += emo_mix[t].values
    ax.set_ylabel("share of emotional reactions")
    ax.set_title("Emotional reaction mix by post theme (Like excluded)")
    ax.legend(ncol=6, fontsize=9)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "reaction_mix.png", dpi=150, facecolor="white")
    plt.close(fig)
    print("wrote reaction_semantics.md, post_reaction_types.csv, figure")


if __name__ == "__main__":
    main()
