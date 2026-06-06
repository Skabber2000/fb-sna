#!/usr/bin/env python3
"""Psychological homophily: do co-engagement / reply edges connect similar
people? Numeric assortativity per layer dimension + label-permutation null.

Outputs data/homophily.md + figures/homophily.png

    python -m analysis.homophily
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = DATA / "figures"
NPERM = 200
MIN_N = 3

NUMERIC = ["insight", "politeness", "constructiveness", "civility",
           "ang", "iro", "rsg", "hop", "cnt", "aff", "frm", "hum",
           "evid", "cnsp", "dogm", "itru", "wtru", "hawk",
           "trad", "indv", "scfr", "ogh"]
CATEG = ["dominant_lang", "behaviour_cluster", "ga_role", "av_gnd"]


def perm_test(g: nx.Graph, vals: dict, numeric: bool) -> tuple[float, float, float]:
    nodes = [n for n in g.nodes if n in vals and pd.notna(vals[n])]
    sg = g.subgraph(nodes)
    if sg.number_of_edges() < 100:
        return np.nan, np.nan, np.nan
    nx.set_node_attributes(sg, {n: vals[n] for n in nodes}, "x")
    f = (nx.numeric_assortativity_coefficient if numeric
         else nx.attribute_assortativity_coefficient)
    try:
        obs = f(sg, "x")
    except Exception:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(0)
    arr = [vals[n] for n in nodes]
    null = []
    for _ in range(NPERM):
        shuf = dict(zip(nodes, rng.permutation(arr)))
        nx.set_node_attributes(sg, shuf, "x")
        try:
            null.append(f(sg, "x"))
        except Exception:
            continue
    null = np.array(null)
    z = (obs - null.mean()) / (null.std() + 1e-12)
    p = float((np.abs(null - null.mean()) >= abs(obs - null.mean())).mean())
    return float(obs), float(z), p


def main() -> None:
    na = pd.read_csv(DATA / "nodes_analyzed.csv")
    na = na[pd.to_numeric(na.get("n_a"), errors="coerce").fillna(0) >= MIN_N]
    na = na.set_index("user")
    print(f"{len(na)} users with >= {MIN_N} scored comments")

    results = []
    for gname, fname in [("coengage", "graph_coengage.graphml"),
                         ("reply", "graph_reply.graphml")]:
        g = nx.read_graphml(DATA / fname)
        g = g.to_undirected()
        print(f"{gname}: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
        for col in NUMERIC:
            if col not in na.columns:
                continue
            # discretize to int deciles for numeric assortativity stability
            v = pd.to_numeric(na[col], errors="coerce").dropna()
            ranks = (v.rank(pct=True) * 10).astype(int).to_dict()
            obs, z, p = perm_test(g, ranks, numeric=True)
            results.append({"graph": gname, "dim": col, "assort": obs,
                            "z": z, "p": p})
        for col in CATEG:
            if col not in na.columns:
                continue
            v = na[col].dropna().astype(str).to_dict()
            obs, z, p = perm_test(g, v, numeric=False)
            results.append({"graph": gname, "dim": col, "assort": obs,
                            "z": z, "p": p})
    df = pd.DataFrame(results).dropna()
    df = df.sort_values(["graph", "z"], ascending=[True, False])
    df.to_csv(DATA / "homophily.csv", index=False)

    sig = df[(df["p"] < 0.05)]
    lines = ["# Psychological homophily (assortativity + permutation null)", "",
             f"Users: {len(na)} (>= {MIN_N} scored comments); "
             f"permutations: {NPERM}", "",
             "## Significant dimensions (p<0.05)",
             sig.round(4).to_string(index=False) if len(sig) else "(none)",
             "", "## All results", df.round(4).to_string(index=False)]
    (DATA / "homophily.md").write_text("\n".join(lines), encoding="utf-8")

    co = df[df["graph"] == "coengage"].set_index("dim")
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = ["#C44E52" if p < 0.05 else "#A8C4E0" for p in co["p"]]
    ax.bar(co.index, co["z"], color=colors)
    ax.axhline(2, ls="--", c="gray", lw=1)
    ax.axhline(-2, ls="--", c="gray", lw=1)
    ax.set_ylabel("assortativity z-score vs permutation null")
    ax.set_title("Homophily by layer dimension — co-engagement graph "
                 "(red = p<0.05)")
    plt.setp(ax.get_xticklabels(), rotation=70, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "homophily.png", dpi=150, facecolor="white")
    plt.close(fig)
    print("wrote homophily.md/.csv + figure")
    print(sig.round(3).to_string(index=False) if len(sig) else "no significant dims")


if __name__ == "__main__":
    main()
