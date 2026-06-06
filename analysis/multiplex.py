#!/usr/bin/env python3
"""Multiplex community stress-test of the ARI~0 orthogonality result.

Layers: co-engagement graph + reply graph. Runs Louvain on each layer,
on a weight-normalized union (multiplex consensus), and compares all
partitions (ARI) against the original communities and the psychographic
clusterings. If psych ARI stays ~0 against every structural partition,
the orthogonality headline survives the "wrong-graph" objection.

Outputs: data/multiplex.md

    python -m analysis.multiplex
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

DATA = Path(__file__).resolve().parent.parent / "data"
SEED = 11


def louvain(g: nx.Graph) -> dict:
    comms = nx.community.louvain_communities(g, weight="weight", seed=SEED)
    return {n: i for i, c in enumerate(comms) for n in c}


def normalize(g: nx.Graph) -> nx.Graph:
    w = [d.get("weight", 1.0) for _, _, d in g.edges(data=True)]
    s = float(np.mean(w)) or 1.0
    h = nx.Graph()
    for u, v, d in g.edges(data=True):
        h.add_edge(u, v, weight=d.get("weight", 1.0) / s)
    return h


def ari(a: dict, b: dict) -> tuple[float, int]:
    common = [n for n in a if n in b]
    if len(common) < 50:
        return np.nan, len(common)
    return adjusted_rand_score([a[n] for n in common],
                               [b[n] for n in common]), len(common)


def main() -> None:
    g_co = nx.read_graphml(DATA / "graph_coengage.graphml").to_undirected()
    g_re = nx.read_graphml(DATA / "graph_reply.graphml").to_undirected()
    print(f"coengage: {g_co.number_of_nodes()}n/{g_co.number_of_edges()}e; "
          f"reply: {g_re.number_of_nodes()}n/{g_re.number_of_edges()}e")

    # multiplex consensus: normalized-weight union
    g_mx = normalize(g_co).copy()
    for u, v, d in normalize(g_re).edges(data=True):
        w = d["weight"] + (g_mx[u][v]["weight"] if g_mx.has_edge(u, v) else 0)
        g_mx.add_edge(u, v, weight=w)

    parts = {"co_louvain": louvain(g_co), "reply_louvain": louvain(g_re),
             "multiplex_louvain": louvain(g_mx)}
    for name, p in parts.items():
        print(f"{name}: {len(set(p.values()))} communities")

    na = pd.read_csv(DATA / "nodes_analyzed.csv")
    parts["original"] = dict(zip(na["user"].astype(str),
                                 na["community"].astype(str)))
    lc = pd.read_csv(DATA / "layer_clusters.csv").set_index("user")
    psych = {c: lc[c].dropna().astype(str).to_dict() for c in lc.columns}

    # structural x structural
    snames = list(parts)
    rows = []
    for i, a in enumerate(snames):
        for b in snames[i + 1:]:
            v, n = ari(parts[a], parts[b])
            rows.append({"a": a, "b": b, "ari": round(v, 3), "n": n})
    ss = pd.DataFrame(rows)

    # psych x structural
    rows = []
    for pname, pv in psych.items():
        r = {"layer": pname}
        for sname in snames:
            v, _ = ari(pv, parts[sname])
            r[sname] = round(v, 3)
        rows.append(r)
    ps = pd.DataFrame(rows)
    mx = ps[snames].abs().max().max()

    lines = ["# Multiplex Community Stress-Test", "",
             f"Layers: co-engagement ({g_co.number_of_edges()} edges), reply "
             f"({g_re.number_of_edges()} edges), normalized-union multiplex.", "",
             "## Structural partitions vs each other (ARI)", "",
             ss.to_string(index=False), "",
             "## Psychographic clusterings vs every structural partition (ARI)",
             "", ps.to_string(index=False), "",
             "## Verdict",
             f"Max |ARI| of any psych layer against any structural partition: "
             f"**{mx:.3f}**.",
             "If this stays ~0, the orthogonality result is robust to graph "
             "choice (co-engagement vs reply vs multiplex) and is not an "
             "artifact of soft co-engagement structure.", ""]
    (DATA / "multiplex.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nstructural x structural:\n{ss.to_string(index=False)}")
    print(f"\npsych max |ARI| vs any structural partition: {mx:.3f}")
    print(f"wrote {DATA / 'multiplex.md'}")


if __name__ == "__main__":
    main()
