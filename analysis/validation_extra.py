#!/usr/bin/env python3
"""Additional result-validation analyses for the three papers.

A. Edge-bootstrap CIs for reply-graph assortativity (headline P2 dims):
   resample edges with replacement, 1000 reps -> 95% CI per dimension.
B. Split-half robustness of the orthogonality result: random half-split of
   posts, rebuild co-comment graphs per half, Louvain, max psych-layer ARI
   per half + cross-half structural stability.
C. Drop-one-event jackknife for event-category mood deltas (categories with
   >=2 windowed events): range of category delta when any one event is
   dropped -> is the mean driven by a single event?

Outputs: data/validation_extra.md

    python -m analysis.validation_extra
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from analysis.event_mood import MIN_WIN, WIN, load as load_mood

DATA = Path(__file__).resolve().parent.parent / "data"
RNG = np.random.default_rng(23)
DIMS_A = ["civility", "insight", "iro", "cnt", "ang", "cnsp", "wtru",
          "hawk", "trad", "indv"]
NBOOT = 1000


def rank10(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce").dropna()
    return (v.rank(pct=True) * 10).astype(int)


def edge_assort(pairs: np.ndarray) -> float:
    """Numeric assortativity = Pearson r over symmetrized endpoint values."""
    x = np.concatenate([pairs[:, 0], pairs[:, 1]])
    y = np.concatenate([pairs[:, 1], pairs[:, 0]])
    return float(np.corrcoef(x, y)[0, 1])


def part_a() -> list[str]:
    g = nx.read_graphml(DATA / "graph_reply.graphml").to_undirected()
    na = pd.read_csv(DATA / "nodes_analyzed.csv")
    na = na[pd.to_numeric(na.get("n_a"), errors="coerce").fillna(0) >= 3]
    na = na.set_index("user")
    out = ["## A. Edge-bootstrap 95% CIs, reply-graph assortativity",
           f"(1000 edge-bootstrap reps; dims as decile ranks)", "",
           "| dim | point | 95% CI | excludes 0 |", "|---|---|---|---|"]
    for d in DIMS_A:
        if d not in na.columns:
            continue
        vals = rank10(na[d]).to_dict()
        pairs = np.array([[vals[u], vals[v]] for u, v in g.edges()
                          if u in vals and v in vals], dtype=float)
        if len(pairs) < 100:
            continue
        point = edge_assort(pairs)
        boots = [edge_assort(pairs[RNG.integers(0, len(pairs), len(pairs))])
                 for _ in range(NBOOT)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        out.append(f"| {d} | {point:.3f} | [{lo:.3f}, {hi:.3f}] | "
                   f"{'YES' if lo > 0 or hi < 0 else 'no'} |")
    return out


def part_b() -> list[str]:
    com = pd.read_csv(DATA / "comments.csv")[["post_id", "user"]].dropna()
    posts = com["post_id"].unique()
    half_parts = []
    perm = RNG.permutation(len(posts))
    halves = [set(posts[perm[: len(posts) // 2]]),
              set(posts[perm[len(posts) // 2:]])]
    lc = pd.read_csv(DATA / "layer_clusters.csv").set_index("user")
    rows = ["## B. Split-half robustness of orthogonality",
            "(random post-half -> co-comment graph -> Louvain -> "
            "max psych-layer ARI)", ""]
    for hi_, half in enumerate(halves):
        sub = com[com["post_id"].isin(half)]
        g = nx.Graph()
        for _, grp in sub.groupby("post_id"):
            us = grp["user"].unique()
            if len(us) > 60:                      # cap mega-posts like v1
                us = RNG.choice(us, 60, replace=False)
            for i in range(len(us)):
                for j in range(i + 1, len(us)):
                    w = g[us[i]][us[j]]["weight"] + 1 \
                        if g.has_edge(us[i], us[j]) else 1
                    g.add_edge(us[i], us[j], weight=w)
        part = {n: i for i, c in enumerate(
            nx.community.louvain_communities(g, weight="weight", seed=5))
            for n in c}
        half_parts.append(part)
        aris = {}
        for col in lc.columns:
            pv = lc[col].dropna().astype(str).to_dict()
            common = [u for u in pv if u in part]
            if len(common) >= 50:
                aris[col] = adjusted_rand_score(
                    [pv[u] for u in common], [part[u] for u in common])
        mx = max(abs(v) for v in aris.values())
        rows.append(f"- Half {hi_ + 1}: {g.number_of_nodes()} nodes, "
                    f"{len(set(part.values()))} communities, "
                    f"max |psych ARI| = {mx:.3f}")
    common = [u for u in half_parts[0] if u in half_parts[1]]
    cross = adjusted_rand_score([half_parts[0][u] for u in common],
                                [half_parts[1][u] for u in common])
    rows.append(f"- Cross-half structural ARI (stability): {cross:.3f} "
                f"on {len(common)} shared users")
    return rows


def part_c() -> list[str]:
    df = load_mood()
    base = df[["ang", "anx", "hop", "rsg"]].mean()
    ev = pd.read_csv(DATA / "war_events.csv")
    ev["dt"] = pd.to_datetime(ev["date"])
    rows = ["## C. Drop-one-event jackknife (categories with >=2 windowed "
            "events; anger delta)", "",
            "| category | full | jackknife range | single-event driven |",
            "|---|---|---|---|"]
    for cat, grp in ev.groupby("category"):
        deltas, ns = [], []
        for _, e in grp.iterrows():
            w = df[(df["dt"] >= e["dt"])
                   & (df["dt"] < e["dt"] + pd.Timedelta(days=WIN))]
            if len(w) >= MIN_WIN:
                deltas.append(float(w["ang"].mean() - base["ang"]))
                ns.append(len(w))
        if len(deltas) < 2:
            continue
        full = float(np.average(deltas, weights=ns))
        jk = []
        for i in range(len(deltas)):
            d2 = deltas[:i] + deltas[i + 1:]
            n2 = ns[:i] + ns[i + 1:]
            jk.append(float(np.average(d2, weights=n2)))
        lo, hi = min(jk), max(jk)
        driven = "YES" if (hi - lo) > abs(full) else "no"
        rows.append(f"| {cat} | {full:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {driven} |")
    return rows


def main() -> None:
    parts = (["# Additional Validation Analyses (2026-06-06)", ""]
             + part_a() + [""] + part_b() + [""] + part_c() + [""])
    (DATA / "validation_extra.md").write_text("\n".join(parts), encoding="utf-8")
    print("\n".join(parts))


if __name__ == "__main__":
    main()
