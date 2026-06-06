#!/usr/bin/env python3
"""Decluttered view: only inter-community ('intersected') edges and the nodes
that bridge clusters. Strips intra-cluster density + isolated pendants so the
cross-cluster skeleton is legible.

Inputs (data/): graph_coengage.graphml, nodes_analyzed.csv
Output (data/): figures/network_intersections.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
PALETTE = plt.get_cmap("tab20").colors


def draw_community_graph(P, nodes, min_comm: int, keep_top: float) -> None:
    """Aggregate to one node per community; edge = total cross-engagement weight."""
    comm = dict(zip(nodes["user"], nodes["community"]))
    sizes = nodes["community"].value_counts()
    big = set(sizes[sizes >= min_comm].index)
    # city label per community
    city_lbl = {}
    if "city" in nodes.columns:
        for cm in big:
            sub = nodes[(nodes["community"] == cm) &
                        (nodes["city"].astype(str).str.len() > 0)]
            if len(sub):
                city_lbl[cm] = sub["city"].value_counts().index[0]

    cross: dict[tuple, float] = {}
    for u, v, d in P.edges(data=True):
        cu, cv = comm.get(u), comm.get(v)
        if cu in big and cv in big and cu != cv:
            key = tuple(sorted((cu, cv)))
            cross[key] = cross.get(key, 0.0) + d.get("weight", 1.0)
    if not cross:
        raise SystemExit("no cross-community weight")
    thr = np.quantile(list(cross.values()), 1 - keep_top)

    G = nx.Graph()
    for cm in big:
        G.add_node(cm, size=int(sizes[cm]))
    for (a, b), w in cross.items():
        if w >= thr:
            G.add_edge(a, b, weight=w)
    G.remove_nodes_from([n for n in list(G) if G.degree(n) == 0])

    pos = nx.spring_layout(G, k=1.2, weight="weight", seed=42, iterations=300)
    fig, ax = plt.subplots(figsize=(13, 10), facecolor="white")
    ax.set_facecolor("white")
    ews = [G[u][v]["weight"] for u, v in G.edges()]
    wmax = max(ews) if ews else 1
    nx.draw_networkx_edges(G, pos, width=[0.5 + 6 * w / wmax for w in ews],
                           alpha=0.4, edge_color="#7a8aa0", ax=ax)
    nsz = [300 + 18 * G.nodes[n]["size"] for n in G.nodes()]
    ncol = [PALETTE[n % len(PALETTE)] for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_size=nsz, node_color=ncol,
                           linewidths=1, edgecolors="white", ax=ax)
    labels = {n: f"C{n}\n{G.nodes[n]['size']}p"
              + (f"\n{city_lbl[n]}" if n in city_lbl else "") for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_color="#111", ax=ax)
    ax.set_title("Community intersection graph — node = cluster (size = members), "
                 "edge width = cross-cluster co-engagement", fontsize=12, color="#111")
    ax.axis("off")
    fig.tight_layout()
    out = DATA / "figures" / "community_graph.png"
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"{G.number_of_nodes()} communities, {G.number_of_edges()} intersections -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Inter-community skeleton figure")
    ap.add_argument("--mode", choices=["node", "community"], default="community")
    ap.add_argument("--keep-top", type=float, default=0.5,
                    help="keep this top fraction of cross-edges by weight (declutter)")
    ap.add_argument("--min-comm", type=int, default=10,
                    help="drop communities smaller than this")
    args = ap.parse_args()

    if args.mode == "community":
        P = nx.read_graphml(DATA / "graph_coengage.graphml")
        nodes = pd.read_csv(DATA / "nodes_analyzed.csv").fillna("")
        draw_community_graph(P, nodes, args.min_comm, args.keep_top)
        return

    P = nx.read_graphml(DATA / "graph_coengage.graphml")
    nodes = pd.read_csv(DATA / "nodes_analyzed.csv").fillna("")
    comm = dict(zip(nodes["user"], nodes["community"]))
    btw = dict(zip(nodes["user"], nodes["betweenness"]))

    # communities large enough to matter
    sizes = nodes["community"].value_counts()
    big = set(sizes[sizes >= args.min_comm].index)

    # inter-community edges only ("intersected" edges)
    inter = [(u, v, d.get("weight", 1.0)) for u, v, d in P.edges(data=True)
             if comm.get(u) != comm.get(v)
             and comm.get(u) in big and comm.get(v) in big]
    if not inter:
        raise SystemExit("no inter-community edges found")
    thr = np.quantile([w for *_, w in inter], 1 - args.keep_top)
    kept = [(u, v, w) for u, v, w in inter if w >= thr]

    H = nx.Graph()
    for u, v, w in kept:
        H.add_edge(u, v, weight=w)
    # drop weakly-attached bridge nodes (only 1 cross-link) to declutter further
    H.remove_nodes_from([n for n in list(H) if H.degree(n) < 2])
    if H.number_of_nodes() == 0:
        raise SystemExit("nothing left after filtering; lower --keep-top threshold")

    pos = nx.spring_layout(H, k=0.5, weight="weight", seed=42, iterations=200)
    fig, ax = plt.subplots(figsize=(15, 12), facecolor="white")
    ax.set_facecolor("white")
    nx.draw_networkx_edges(H, pos, alpha=0.25, width=0.7, edge_color="#9aa", ax=ax)
    colors = [PALETTE[comm.get(n, 0) % len(PALETTE)] for n in H.nodes()]
    sizes_n = [120 + 6000 * btw.get(n, 0) for n in H.nodes()]
    nx.draw_networkx_nodes(H, pos, node_color=colors, node_size=sizes_n,
                           linewidths=0.5, edgecolors="white", ax=ax)
    # label the strongest bridges present
    top = nodes[nodes["user"].isin(H.nodes())].sort_values(
        "betweenness", ascending=False)
    top = top[~top["is_owner"].astype(bool)].head(15)
    labels = {r["user"]: str(r["author_name"])[:18] for _, r in top.iterrows()
              if r["user"] in pos}
    nx.draw_networkx_labels(H, pos, labels, font_size=8, font_color="#111", ax=ax)
    ax.set_title(f"Inter-community skeleton — {H.number_of_nodes()} bridge nodes, "
                 f"{H.number_of_edges()} cross-cluster edges "
                 f"(color = community, size = betweenness)", fontsize=12, color="#111")
    ax.axis("off")
    fig.tight_layout()
    out = DATA / "figures" / "network_intersections.png"
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"{H.number_of_nodes()} nodes, {H.number_of_edges()} cross-edges -> {out}")


if __name__ == "__main__":
    main()
