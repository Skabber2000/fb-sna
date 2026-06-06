#!/usr/bin/env python3
"""Reliability dot plot for paper 1: test-retest r per dimension.
Light theme. -> data/figures/reliability.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = Path(__file__).resolve().parent.parent / "data"

A = {"ent": .858, "anx": .817, "cnt": .793, "rsl": .791, "ang": .775,
     "iro": .759, "hop": .759, "rsg": .759, "dis": .756, "hum": .753,
     "aff": .709, "exh": .654, "frm": .652, "prf": .646}
B = {"cnsp": .791, "ogh": .776, "wtru": .770, "loya": .748, "care": .731,
     "trad": .731, "dogm": .730, "evid": .713, "hawk": .659, "sxm": .663,
     "fair": .625, "itru": .598, "sexp": .592, "auth": .522, "gtrd": .521,
     "libe": .431, "indv": .428, "scfr": .045, "lgbt": .000}

items = ([(k, v, "A") for k, v in A.items()] + [(k, v, "B") for k, v in B.items()])
items.sort(key=lambda x: x[1])

fig, ax = plt.subplots(figsize=(7.5, 9), facecolor="white")
y = range(len(items))
for yi, (k, v, p) in zip(y, items):
    c = "#0057B7" if p == "A" else "#c8961e"
    ax.plot([0, v], [yi, yi], color="#e3e6ea", lw=1.4, zorder=1)
    ax.scatter([v], [yi], color=c, s=46, zorder=2)
ax.axvline(0.7, color="#c0392b", lw=1.2, ls="--")
ax.text(0.705, len(items) - 0.5, "publication gate r = 0.7",
        color="#c0392b", fontsize=9, va="top")
ax.set_yticks(list(y))
ax.set_yticklabels([k for k, _, _ in items], fontsize=9)
ax.set_xlim(0, 1)
ax.set_xlabel("test-retest Pearson r (n = 200 re-scored comments)")
ax.set_title("Instrument reliability by dimension\n"
             "blue = expressive pass A, gold = worldview pass B", fontsize=11)
ax.set_facecolor("white")
ax.grid(axis="x", alpha=0.25)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(DATA / "figures" / "reliability.png", dpi=150)
print("wrote figures/reliability.png")
