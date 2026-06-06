#!/usr/bin/env python3
"""Stage 3: communities, bridges, and behaviour clusters.

Inputs (data/):  graph_coengage.graphml, graph_reply.graphml, nodes.csv
Output (data/):  nodes_analyzed.csv  (+ console summary)

Covers SNA_METHODOLOGY.md:
- Communities: Louvain on co-engagement P (modularity Q reported).
- Bridges: betweenness on reply R + Guimera-Amaral connector-hub roles on P
  (within-module degree z-score x participation coefficient).
- Behaviour (Axis B2): k-means on engagement-style features in nodes.csv.

Topic (B1) and discourse (Axis C) layers need post-theme labels / LLM and are
handled in later stages.
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.community import louvain_communities, modularity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parent.parent / "data"


def detect_communities(P: nx.Graph) -> tuple[dict, float]:
    comms = louvain_communities(P, weight="weight", seed=42)
    q = modularity(P, comms, weight="weight")
    node2c = {n: i for i, c in enumerate(comms) for n in c}
    return node2c, q


def guimera_amaral(P: nx.Graph, node2c: dict) -> pd.DataFrame:
    """Within-module degree z-score and participation coefficient (weighted)."""
    rows = []
    # weighted degree within each module
    modules: dict[int, list] = {}
    for n, c in node2c.items():
        modules.setdefault(c, []).append(n)
    kin_by_mod = {}
    for c, members in modules.items():
        ks = {}
        for n in members:
            ks[n] = sum(P[n][m]["weight"] for m in P[n] if node2c.get(m) == c)
        arr = np.array(list(ks.values()))
        mu, sd = arr.mean(), arr.std() or 1.0
        kin_by_mod[c] = (ks, mu, sd)
    for n in P.nodes():
        c = node2c.get(n)
        ks, mu, sd = kin_by_mod[c]
        z = (ks[n] - mu) / sd
        ktot = sum(P[n][m]["weight"] for m in P[n])
        if ktot > 0:
            per_mod = {}
            for m in P[n]:
                cm = node2c.get(m)
                per_mod[cm] = per_mod.get(cm, 0) + P[n][m]["weight"]
            part = 1 - sum((v / ktot) ** 2 for v in per_mod.values())
        else:
            part = 0.0
        role = ("connector_hub" if z >= 2.5 and part > 0.62 else
                "provincial_hub" if z >= 2.5 else
                "connector" if part > 0.62 else "peripheral")
        rows.append({"user": n, "wm_zscore": round(z, 2),
                     "participation": round(part, 3), "ga_role": role})
    return pd.DataFrame(rows)


def behaviour_clusters(nodes: pd.DataFrame, k: int = 4) -> pd.Series:
    feats = ["n_comments", "reactions_received", "posts_engaged"]
    feats += [c for c in ("reactions_given",) if c in nodes.columns]
    X = StandardScaler().fit_transform(nodes[feats].fillna(0))
    k = min(k, max(2, len(nodes) // 10))
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    return pd.Series(km.labels_, index=nodes.index)


def main() -> None:
    P = nx.read_graphml(DATA / "graph_coengage.graphml")
    R = nx.read_graphml(DATA / "graph_reply.graphml")
    nodes = pd.read_csv(DATA / "nodes.csv").fillna("")

    node2c, q = detect_communities(P)
    sizes = pd.Series(list(node2c.values())).value_counts().sort_index()

    # merge profile enrichment (occupation / education / region) if present
    prof_path = DATA / "profiles.csv"
    prof = pd.read_csv(prof_path).fillna("") if prof_path.exists() else None
    if prof is not None:
        for col in ("work", "education", "location"):
            nodes[col] = nodes["user"].map(dict(zip(prof["user"], prof[col]))).fillna("")
        # normalized city from 'Lives in X' / 'From X'
        nodes["city"] = (nodes["location"].str.replace(
            r"^(Lives in|From|Based in)\s*", "", regex=True, case=False).str.strip())

    # betweenness on reply graph (bridge brokers); distance = 1/weight
    Rd = R.copy()
    for u, v, d in Rd.edges(data=True):
        d["dist"] = 1.0 / max(d.get("weight", 1), 1e-9)
    btw = nx.betweenness_centrality(Rd, weight="dist") if Rd.number_of_nodes() else {}

    ga = guimera_amaral(P, node2c)
    nodes["community"] = nodes["user"].map(node2c).fillna(-1).astype(int)
    nodes["betweenness"] = nodes["user"].map(btw).fillna(0).round(4)
    nodes = nodes.merge(ga, on="user", how="left")
    nodes["behaviour_cluster"] = behaviour_clusters(nodes)
    nodes.to_csv(DATA / "nodes_analyzed.csv", index=False)

    print(f"COMMUNITIES (Louvain on P):  {len(sizes)} communities, modularity Q={q:.3f}")
    for c, sz in sizes.items():
        print(f"   community {c}: {sz} members")
    print(f"\nBRIDGES — top connector hubs / brokers:")
    bridges = nodes.sort_values(["betweenness", "participation"], ascending=False)
    show = bridges[~bridges["is_owner"].astype(bool)].head(8)
    for _, r in show.iterrows():
        print(f"   {str(r['author_name'])[:22]:<22} comm={r['community']} "
              f"btw={r['betweenness']:.3f} P={r['participation']:.2f} "
              f"role={r['ga_role']}")
    print(f"\nBEHAVIOUR clusters: {nodes['behaviour_cluster'].value_counts().to_dict()}")
    print(f"  -> data/nodes_analyzed.csv")


if __name__ == "__main__":
    main()
