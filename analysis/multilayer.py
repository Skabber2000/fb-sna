#!/usr/bin/env python3
"""Multi-layer re-clustering + cross-layer analysis.

Inputs: nodes_analyzed.csv (all layer means per user), user_topics.csv,
        avatar_users.csv, layers_a/b.csv (comment level), posts.csv (themes).
Outputs (data/):
  layer_profiles.csv   — community × every-layer mean table
  ari_matrix.csv       — agreement (ARI) between per-layer clusterings
  layer_clusters.csv   — per-user cluster id per layer
  xenophobia.md        — outgroup-hostility deep dive (aggregate)
  affect.md            — author-affect (hate..love) analysis
  wellbeing.md         — cluster-level wellbeing signals (aggregate-only)
  figures/layers_*.png — light-theme figures

    python -m analysis.multilayer
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = DATA / "figures"
FIG.mkdir(exist_ok=True)
plt.style.use("default")                      # light theme, white background

MIN_N = 3            # min scored comments for a user to enter layer clustering

LAYERS: dict[str, list[str]] = {
    "emotional":  ["ang", "iro", "hop", "rsg", "ent", "anx", "cnt"],
    "affect":     ["aff"],
    "wellbeing":  ["dis", "exh", "rsl"],
    "register":   ["frm", "hum", "prf"],
    "moral":      ["care", "fair", "loya", "auth", "libe"],
    "values":     ["trad", "sexp", "indv", "scfr"],
    "epistemic":  ["evid", "cnsp", "dogm"],
    "political":  ["itru", "wtru", "hawk"],
    "outgroup":   ["ogh", "sxm"],
    "discourse":  ["politeness", "constructiveness", "insight", "civility"],
}


def kmeans_layer(df: pd.DataFrame, cols: list[str], kmax: int = 8):
    X = df[cols].dropna()
    if len(X) < 50 or X.std().sum() == 0:
        return None, None
    Xs = StandardScaler().fit_transform(X)
    best = (None, -1, None)
    for k in range(2, min(kmax, len(X) // 50) + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Xs)
        s = silhouette_score(Xs, km.labels_, sample_size=min(2000, len(X)),
                             random_state=0)
        if s > best[1]:
            best = (km.labels_, s, k)
    return pd.Series(best[0], index=X.index), best[2]


def main() -> None:
    na = pd.read_csv(DATA / "nodes_analyzed.csv")
    na = na[na["is_owner"] != True]                          # noqa: E712
    print(f"{len(na)} users, {na.shape[1]} columns")

    topics = pd.read_csv(DATA / "user_topics.csv")
    theme_cols = [c for c in topics.columns if c not in ("user", "n_eng")]
    na = na.merge(topics, on="user", how="left")

    # ---- per-layer clustering + ARI vs structural communities -------------
    scored = na[(na.get("n_a", 0).fillna(0) >= MIN_N)
                | (na.get("n_scored", 0).fillna(0) >= MIN_N)].copy()
    print(f"{len(scored)} users with >= {MIN_N} scored comments")

    clusterings: dict[str, pd.Series] = {}
    rows = []
    for name, cols in LAYERS.items():
        cols_ok = [c for c in cols if c in scored.columns]
        if not cols_ok:
            continue
        labels, k = kmeans_layer(scored, cols_ok)
        if labels is None:
            continue
        clusterings[name] = labels
        scored.loc[labels.index, f"cl_{name}"] = labels.values
        rows.append({"layer": name, "k": k, "n": len(labels)})
    # topic layer
    tl, tk = kmeans_layer(scored, [c for c in theme_cols if c in scored.columns])
    if tl is not None:
        clusterings["topical"] = tl
        scored.loc[tl.index, "cl_topical"] = tl.values
        rows.append({"layer": "topical", "k": tk, "n": len(tl)})
    print(pd.DataFrame(rows).to_string(index=False))

    names = ["structural"] + list(clusterings)
    ari = pd.DataFrame(np.eye(len(names)), index=names, columns=names)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sa = (scored.loc[clusterings[a].index, "community"] if a == "structural"
                  else clusterings[a]) if a != "structural" else None
            ia = clusterings[a] if a != "structural" else scored["community"]
            ib = clusterings[b] if b != "structural" else scored["community"]
            common = ia.dropna().index.intersection(ib.dropna().index)
            if len(common) < 50:
                continue
            v = adjusted_rand_score(ia.loc[common], ib.loc[common])
            ari.loc[a, b] = ari.loc[b, a] = round(v, 3)
    ari.to_csv(DATA / "ari_matrix.csv")
    print("\nARI vs structural:",
          {n: float(ari.loc["structural", n]) for n in names[1:]})

    cl_cols = ["user"] + [c for c in scored.columns if c.startswith("cl_")]
    scored[cl_cols].to_csv(DATA / "layer_clusters.csv", index=False)

    # ---- community × layer profile table ----------------------------------
    num_cols = [c for cols in LAYERS.values() for c in cols if c in na.columns]
    prof = na.groupby("community")[num_cols].mean().round(2)
    sizes = na.groupby("community").size().rename("size")
    prof = pd.concat([sizes, prof], axis=1)
    labels = pd.read_csv(DATA / "community_profiles.csv")[["community", "label"]]
    prof = prof.merge(labels, left_index=True, right_on="community", how="left")
    prof.to_csv(DATA / "layer_profiles.csv", index=False)
    print(f"layer_profiles.csv: {len(prof)} communities x {len(num_cols)} dims")

    # ---- heatmap figure ----------------------------------------------------
    big = prof[prof["size"] >= 60].set_index("community")
    hm = big[[c for c in num_cols if c in big.columns]]
    hm_z = (hm - hm.mean()) / hm.std().replace(0, 1)
    fig, ax = plt.subplots(figsize=(16, 7))
    im = ax.imshow(hm_z.values, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
    ax.set_xticks(range(len(hm.columns)), hm.columns, rotation=80, fontsize=8)
    ylabels = [f"C{int(i)} ({int(big.loc[i,'size'])})" for i in hm_z.index]
    ax.set_yticks(range(len(hm_z)), ylabels, fontsize=9)
    ax.set_title("Communities × psychographic layers (z-scored means)")
    fig.colorbar(im, shrink=0.7)
    fig.tight_layout()
    fig.savefig(FIG / "layers_heatmap.png", dpi=150, facecolor="white")
    plt.close(fig)

    # ---- author-affect report ----------------------------------------------
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    la["aff"] = pd.to_numeric(la["aff"], errors="coerce")
    com = pd.read_csv(DATA / "comments.csv")[["comment_id", "post_id"]]
    posts = pd.read_csv(DATA / "posts.csv")[["post_id", "theme"]]
    la = la.merge(com, on="comment_id").merge(posts, on="post_id", how="left")
    nz = la[la["aff"].notna()]
    pos = nz[nz["aff"] > 0]
    neg = nz[nz["aff"] < 0]
    kind_counts = la[la["akind"].ne("none") & la["akind"].notna()][
        "akind"].value_counts()
    aff_user = nz.groupby("user")["aff"].agg(["mean", "count"])
    aff_comm = (aff_user.merge(na[["user", "community"]], on="user")
                .groupby("community")["mean"].agg(["mean", "count"]).round(3))
    lines = ["# Author-affect layer (hate .. love)", "",
             f"Scored comments: {len(nz)}; expressed affect in "
             f"{len(pos) + len(neg)} ({(len(pos)+len(neg))/len(nz):.1%})",
             f"Positive: {len(pos)} ({len(pos)/len(nz):.1%})  "
             f"Negative: {len(neg)} ({len(neg)/len(nz):.1%})  "
             f"ratio {len(pos)/max(len(neg),1):.1f}:1", "",
             "Affect kinds: " + ", ".join(f"{k} {v}" for k, v in
                                          kind_counts.head(10).items()), "",
             "Mean affect by community:", aff_comm.to_string(), "",
             "Mean affect by post theme:",
             nz.groupby("theme")["aff"].agg(["mean", "count"]).round(3).to_string()]
    (DATA / "affect.md").write_text("\n".join(lines), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    nz["aff"].hist(bins=np.arange(-4.5, 5.5, 1), ax=ax, color="#4878CF",
                   edgecolor="white")
    ax.set_yscale("log")
    ax.set_xlabel("expressed feeling toward author  (-4 hate .. +4 love)")
    ax.set_title("Author-affect distribution (log scale)")
    fig.tight_layout()
    fig.savefig(FIG / "layers_affect.png", dpi=150, facecolor="white")
    plt.close(fig)

    # ---- xenophobia / antisemitism report (aggregate) ----------------------
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    for c in ["ogh", "cnsp", "evid", "dogm"]:
        lb[c] = pd.to_numeric(lb[c], errors="coerce")
    lb = lb.merge(com, on="comment_id").merge(posts, on="post_id", how="left")
    hot = lb[lb["ogh"] >= 2]
    lines = ["# Outgroup hostility / xenophobia / antisemitism (aggregate)", "",
             f"Comments scored: {len(lb)}; ogh>=2: {len(hot)} "
             f"({len(hot)/len(lb):.2%}); ogh>=3: {(lb['ogh']>=3).sum()}", "",
             "Targets (ogh>=2): " + ", ".join(
                 f"{k} {v}" for k, v in hot["ogt"].value_counts().head(10).items()),
             "Kinds   (ogh>=2): " + ", ".join(
                 f"{k} {v}" for k, v in hot["ogk"].value_counts().head(10).items()),
             "", "Trigger themes (share of theme's comments with ogh>=2):"]
    trig = (lb.assign(hot=lb["ogh"] >= 2).groupby("theme")["hot"]
              .agg(["mean", "sum", "count"]).round(4)
              .sort_values("mean", ascending=False))
    lines.append(trig.to_string())
    og_user = lb.groupby("user").agg(ogh_mean=("ogh", "mean"),
                                     cnsp_mean=("cnsp", "mean"),
                                     n=("ogh", "size"))
    og_user = og_user[og_user["n"] >= MIN_N].merge(
        na[["user", "community", "education", "insight"]], on="user", how="left")
    lines += ["", "Correlations (user level, n>=3):",
              f"  ogh x conspiratorial: "
              f"{og_user['ogh_mean'].corr(og_user['cnsp_mean']):.3f}",
              f"  ogh x insight:        "
              f"{og_user['ogh_mean'].corr(pd.to_numeric(og_user['insight'], errors='coerce')):.3f}",
              "", "Mean ogh by community:",
              og_user.groupby("community")["ogh_mean"].agg(["mean", "count"])
              .round(3).sort_values("mean", ascending=False).to_string()]
    (DATA / "xenophobia.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- wellbeing (aggregate-only) ----------------------------------------
    wb_cols = [c for c in ["dis", "exh", "rsl"] if c in na.columns]
    wb = na.groupby("community")[wb_cols].mean().round(3)
    wb["size"] = na.groupby("community").size()
    lines = ["# Wellbeing signals — AGGREGATE ONLY (not clinical, expressed only)",
             "", wb.to_string(), "",
             "Overall comment-level rates:",
             f"  distress>=2:   {(pd.to_numeric(la['dis'], errors='coerce')>=2).mean():.2%}",
             f"  exhaustion>=2: {(pd.to_numeric(la['exh'], errors='coerce')>=2).mean():.2%}",
             f"  resilience>=2: {(pd.to_numeric(la['rsl'], errors='coerce')>=2).mean():.2%}"]
    (DATA / "wellbeing.md").write_text("\n".join(lines), encoding="utf-8")

    print("\nWrote: layer_profiles, ari_matrix, layer_clusters, affect.md, "
          "xenophobia.md, wellbeing.md, figures/layers_*.png")


if __name__ == "__main__":
    main()
