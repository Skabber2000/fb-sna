#!/usr/bin/env python3
"""Inter-community structure: who talks to whom BETWEEN the arenas.

For both graphs (co-engagement, reply):
  - community x community weighted mixing matrix
  - within-community weight share (vs configuration-null expectation)
  - per-pair observed/expected ratios
Outputs:
  data/community_structure.md   - profile table + mixing results
  data/community_mixing.csv     - full obs/exp matrices (long form)
  figures/community_quotient.png- quotient graph + reply mixing heatmap

    python -m analysis.community_structure
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


def mixing(g: nx.Graph, comm: dict) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """Weighted community mixing matrix, obs/exp ratios, within-share."""
    cids = sorted({c for c in comm.values()})
    idx = {c: i for i, c in enumerate(cids)}
    W = np.zeros((len(cids), len(cids)))
    for u, v, d in g.edges(data=True):
        cu, cv = comm.get(u), comm.get(v)
        if cu is None or cv is None:
            continue
        w = d.get("weight", 1.0)
        W[idx[cu], idx[cv]] += w
        if cu != cv:
            W[idx[cv], idx[cu]] += w
    tot = W.sum() - np.trace(W) / 2          # undirected total (diag once)
    strength = W.sum(axis=1)
    exp = np.outer(strength, strength) / (2 * tot) if tot else W * 0
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(exp > 0, W / exp, np.nan)
    within = np.trace(W) / 2 / tot if tot else np.nan
    obs = pd.DataFrame(W, index=cids, columns=cids)
    rat = pd.DataFrame(ratio, index=cids, columns=cids)
    return obs, rat, float(within)


def main() -> None:
    na = pd.read_csv(DATA / "nodes_analyzed.csv")
    # exclude community -1: the author himself + 2 unassigned mega-nodes.
    # every community over-mixes with the author by construction (he replies
    # to everyone), which would swamp genuine inter-community structure.
    comm = {str(u): int(c) for u, c in zip(na["user"], na["community"])
            if pd.notna(c) and int(c) >= 0}
    prof = pd.read_csv(DATA / "community_profiles.csv").set_index("community")
    g_co = nx.read_graphml(DATA / "graph_coengage.graphml").to_undirected()
    g_re = nx.read_graphml(DATA / "graph_reply.graphml").to_undirected()

    results, rows_csv = {}, []
    for name, g in [("coengage", g_co), ("reply", g_re)]:
        obs, rat, within = mixing(g, comm)
        results[name] = (obs, rat, within)
        for a in obs.index:
            for b in obs.columns:
                rows_csv.append({"graph": name, "ca": a, "cb": b,
                                 "obs_w": round(obs.loc[a, b], 1),
                                 "obs_over_exp": round(rat.loc[a, b], 3)
                                 if pd.notna(rat.loc[a, b]) else ""})
    pd.DataFrame(rows_csv).to_csv(DATA / "community_mixing.csv", index=False)

    # ---- profile + partners table
    obs_r, rat_r, win_r = results["reply"]
    obs_c, rat_c, win_c = results["coengage"]
    lines = ["# Community Structure: profiles and inter-community mixing", "",
             f"Within-community weight share: co-engagement {win_c:.1%} "
             f"(null expectation if random: ~community strength shares), "
             f"reply {win_r:.1%}.", "",
             "| C | label | n | reply within-share | top reply partners (obs/exp) |",
             "|---|---|---|---|---|"]
    for c in sorted(prof.index):
        if c not in obs_r.index:
            continue
        row_w = obs_r.loc[c]
        wshare = row_w[c] / row_w.sum() if row_w.sum() else np.nan
        partners = rat_r.loc[c].drop(index=c).dropna()
        partners = partners[obs_r.loc[c].drop(index=c) >= 3]   # >=3 edges
        top = partners.nlargest(2)
        ptxt = ", ".join(f"C{int(p)} ({v:.1f}x)" for p, v in top.items())
        lines.append(f"| C{c} | {prof.loc[c, 'label']} | "
                     f"{int(prof.loc[c, 'size'])} | "
                     f"{wshare:.0%} | {ptxt or '-'} |")
    lines += ["", "Pairs with obs/exp >= 1.5 and >= 5 edges (reply graph):"]
    for a in rat_r.index:
        for b in rat_r.columns:
            if a < b and pd.notna(rat_r.loc[a, b]) and \
               rat_r.loc[a, b] >= 1.5 and obs_r.loc[a, b] >= 5:
                lines.append(f"- C{a} <-> C{b}: {rat_r.loc[a, b]:.1f}x "
                             f"(w={obs_r.loc[a, b]:.0f})")
    (DATA / "community_structure.md").write_text("\n".join(lines),
                                                 encoding="utf-8")
    print("\n".join(lines[:28]))

    # ---- figure: quotient graph (reply) + mixing heatmap (reply)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), facecolor="white")
    q = nx.Graph()
    sizes = prof["size"].to_dict()
    for c in obs_r.index:
        q.add_node(c)
    for a in obs_r.index:
        for b in obs_r.columns:
            if a < b and obs_r.loc[a, b] >= 3:
                q.add_edge(a, b, weight=rat_r.loc[a, b],
                           w_obs=obs_r.loc[a, b])
    pos = nx.spring_layout(q, weight="w_obs", seed=4, k=1.4)
    cmap = plt.get_cmap("tab20")
    nx.draw_networkx_nodes(q, pos, ax=ax1,
                           node_size=[40 + 4 * sizes.get(c, 20) for c in q],
                           node_color=[cmap(int(c) % 20) for c in q],
                           alpha=0.92, linewidths=0)
    for u, v, d in q.edges(data=True):
        lw = 0.6 + 1.6 * np.log1p(d["w_obs"]) / 2
        col = "#c0392b" if d["weight"] >= 1.5 else "#9aa1ab"
        ax1.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                 color=col, lw=lw, alpha=0.6, zorder=0)
    nx.draw_networkx_labels(q, pos, ax=ax1,
                            labels={c: f"C{c}" for c in q}, font_size=9)
    ax1.set_title("Reply quotient graph: node = community (size = members),\n"
                  "red edges = above-expectation mixing (obs/exp >= 1.5)",
                  fontsize=10)
    ax1.axis("off")

    logr = np.log2(rat_r.replace(0, np.nan))
    im = ax2.imshow(logr.values, cmap="RdBu_r", vmin=-2, vmax=2)
    ax2.set_xticks(range(len(logr)))
    ax2.set_xticklabels([f"C{c}" for c in logr.columns], rotation=90,
                        fontsize=8)
    ax2.set_yticks(range(len(logr)))
    ax2.set_yticklabels([f"C{c}" for c in logr.index], fontsize=8)
    ax2.set_title("Reply mixing: log2(observed / expected)", fontsize=10)
    fig.colorbar(im, ax=ax2, shrink=0.8)
    fig.tight_layout()
    fig.savefig(FIG / "community_quotient.png", dpi=150)
    print("\nwrote figures/community_quotient.png + community_mixing.csv")


if __name__ == "__main__":
    main()
