#!/usr/bin/env python3
"""Publication-safe SNA figures + descriptives (no names, light theme).

  figures/network_anon.png  - co-engagement graph, community-colored,
                              degree-sized, unlabeled + reply graph inset
  figures/degree_dist.png   - degree distributions (log-log)
  data/sna_descriptives.md  - N, E, density, modularity Q, clustering,
                              community sizes, GA-role counts

    python -m analysis.make_network_figs
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FIG = DATA / "figures"
CMAP = plt.get_cmap("tab20")


def main() -> None:
    g = nx.read_graphml(DATA / "graph_coengage.graphml").to_undirected()
    r = nx.read_graphml(DATA / "graph_reply.graphml").to_undirected()
    na = pd.read_csv(DATA / "nodes_analyzed.csv")
    comm = dict(zip(na["user"].astype(str), na["community"]))
    cids = sorted({c for c in comm.values() if pd.notna(c)})
    cidx = {c: i for i, c in enumerate(cids)}

    # ---- descriptives
    part = [{n for n in g if comm.get(n) == c} for c in cids]
    part = [p for p in part if p]
    extra = set(g) - set().union(*part)
    Q = nx.community.modularity(g, part + [{n} for n in extra], weight="weight")
    deg = dict(g.degree())
    lines = ["# SNA Descriptives (publication)", "",
             f"- Co-engagement: {g.number_of_nodes()} nodes, "
             f"{g.number_of_edges()} edges, density "
             f"{nx.density(g):.4f}, mean degree {np.mean(list(deg.values())):.1f}, "
             f"clustering {nx.average_clustering(g):.3f}, modularity Q={Q:.3f}",
             f"- Reply: {r.number_of_nodes()} nodes, {r.number_of_edges()} edges, "
             f"density {nx.density(r):.4f}",
             "", "## Community sizes", ""]
    sizes = na["community"].value_counts().sort_index()
    lines += [f"- C{c}: {n}" for c, n in sizes.items()]
    lines += ["", "## Guimera-Amaral roles", ""]
    lines += [f"- {k}: {v}" for k, v in na["ga_role"].value_counts().items()]
    (DATA / "sna_descriptives.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:8]))

    # ---- main network figure
    print("layout (this takes a minute)...")
    pos = nx.spring_layout(g, k=0.08, iterations=60, seed=3, weight="weight")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor="white",
                                   gridspec_kw={"width_ratios": [1.7, 1]})
    colors = [CMAP(cidx.get(comm.get(n), 19) % 20) for n in g]
    size = [6 + 2.2 * np.sqrt(deg[n]) for n in g]
    nx.draw_networkx_edges(g, pos, ax=ax1, alpha=0.04, width=0.4,
                           edge_color="#555")
    nx.draw_networkx_nodes(g, pos, ax=ax1, node_color=colors, node_size=size,
                           linewidths=0)
    ax1.set_title(f"Co-engagement network ({g.number_of_nodes()} nodes, "
                  f"{g.number_of_edges()} edges, Q={Q:.2f})\n"
                  "color = community, size = degree; no identities shown",
                  fontsize=11)
    ax1.axis("off")

    pos_r = nx.spring_layout(r, k=0.25, iterations=80, seed=3)
    deg_r = dict(r.degree())
    colors_r = [CMAP(cidx.get(comm.get(n), 19) % 20) for n in r]
    nx.draw_networkx_edges(r, pos_r, ax=ax2, alpha=0.18, width=0.5,
                           edge_color="#555")
    nx.draw_networkx_nodes(r, pos_r, ax=ax2, node_color=colors_r,
                           node_size=[8 + 6 * np.sqrt(deg_r[n]) for n in r],
                           linewidths=0)
    ax2.set_title(f"Reply network ({r.number_of_nodes()} nodes, "
                  f"{r.number_of_edges()} edges)\ncolored by co-engagement "
                  "community", fontsize=11)
    ax2.axis("off")
    fig.tight_layout()
    fig.savefig(FIG / "network_anon.png", dpi=150)
    print("wrote figures/network_anon.png")

    # ---- degree distributions
    fig2, ax = plt.subplots(figsize=(6.5, 4.5), facecolor="white")
    for gg, lab, c in [(g, "co-engagement", "#0057B7"), (r, "reply", "#c8961e")]:
        d = np.array(sorted(dict(gg.degree()).values(), reverse=True))
        vals, counts = np.unique(d, return_counts=True)
        ax.loglog(vals, counts, "o", ms=4, label=lab, color=c, alpha=0.8)
    ax.set_xlabel("degree k")
    ax.set_ylabel("count")
    ax.legend()
    ax.grid(alpha=0.25)
    ax.set_title("Degree distributions", fontsize=11)
    fig2.tight_layout()
    fig2.savefig(FIG / "degree_dist.png", dpi=150)
    print("wrote figures/degree_dist.png")


if __name__ == "__main__":
    main()
