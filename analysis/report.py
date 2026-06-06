#!/usr/bin/env python3
"""Stage 5: light-theme network figure + self-contained HTML report.

Inputs (data/): graph_coengage.graphml, nodes_analyzed.csv
Outputs (data/): figures/network.png, report.html

Pseudonymous by default: shows community structure, bridge ranks and behaviour
segments. Real names are shown ONLY for the top bridges (already public commenters
on your posts) to make the report actionable; flip --anonymize to hide them.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
# light, distinct categorical palette (white background per house style)
PALETTE = plt.get_cmap("tab20").colors


def draw_network(P, nodes, out: Path) -> None:
    sub = P.subgraph(max(nx.connected_components(P), key=len)).copy()
    comm = dict(zip(nodes["user"], nodes["community"]))
    btw = dict(zip(nodes["user"], nodes["betweenness"]))
    pos = nx.spring_layout(sub, k=0.35, weight="weight", seed=42, iterations=120)
    fig, ax = plt.subplots(figsize=(14, 11), facecolor="white")
    ax.set_facecolor("white")
    nx.draw_networkx_edges(sub, pos, alpha=0.12, width=0.6, edge_color="#888", ax=ax)
    colors = [PALETTE[comm.get(n, 0) % len(PALETTE)] for n in sub.nodes()]
    sizes = [80 + 5000 * btw.get(n, 0) for n in sub.nodes()]
    nx.draw_networkx_nodes(sub, pos, node_color=colors, node_size=sizes,
                           linewidths=0.4, edgecolors="white", ax=ax)
    # label the strongest bridges only
    top = nodes.sort_values("betweenness", ascending=False)
    top = top[~top["is_owner"].astype(bool)].head(10)
    labels = {r["user"]: str(r["author_name"])[:18] for _, r in top.iterrows()
              if r["user"] in pos}
    nx.draw_networkx_labels(sub, pos, labels, font_size=8, font_color="#111", ax=ax)
    ax.set_title("FB audience — co-engagement network (color = community, "
                 "size = bridge centrality)", fontsize=13, color="#111")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)


def html_report(nodes, posts, q_note, anonymize, out: Path) -> None:
    def nm(r):
        return "(hidden)" if anonymize else html.escape(str(r["author_name"])[:28])
    comm_sizes = nodes["community"].value_counts().sort_index()
    cprof = {}
    cpath = DATA / "community_profiles.csv"
    if cpath.exists():
        cp = pd.read_csv(cpath).fillna("")
        cprof = {int(r["community"]): (r["label"], r["description"])
                 for _, r in cp.iterrows()}
    bridges = nodes[~nodes["is_owner"].astype(bool)].sort_values(
        "betweenness", ascending=False).head(12)
    beh = nodes["behaviour_cluster"].value_counts().sort_index()

    rows_comm = "".join(
        f"<tr><td>C{c}</td><td>{s}</td>"
        f"<td><b>{html.escape(cprof.get(c, ('',''))[0])}</b>"
        f"{('<br><span class=\"note\">'+html.escape(cprof[c][1])+'</span>') if c in cprof else ''}</td></tr>"
        for c, s in comm_sizes.sort_values(ascending=False).items())
    rows_bridge = "".join(
        f"<tr><td>{nm(r)}</td><td>{r['community']}</td>"
        f"<td>{r['betweenness']:.3f}</td><td>{r['participation']:.2f}</td>"
        f"<td>{html.escape(str(r['ga_role']))}</td></tr>"
        for _, r in bridges.iterrows())
    rows_beh = "".join(
        f"<tr><td>cluster {c}</td><td>{s}</td></tr>" for c, s in beh.items())

    # discourse layer (Axis C), if present
    disc_section = ""
    dmetrics = ["politeness", "constructiveness", "insight", "civility", "stance"]
    if "insight" in nodes.columns and pd.to_numeric(
            nodes["insight"], errors="coerce").notna().any():
        for m in dmetrics:
            nodes[m] = pd.to_numeric(nodes[m], errors="coerce")
        scored = nodes[nodes["insight"].notna()]
        avg = {m: scored[m].mean() for m in dmetrics}
        # expert voices: high insight (>=2 comments scored)
        ev = scored[scored.get("n_scored", 0) >= 2].sort_values(
            "insight", ascending=False).head(12)
        rows_ev = "".join(
            f"<tr><td>{nm(r)}</td><td>{r['insight']:.1f}</td>"
            f"<td>{r['constructiveness']:.1f}</td><td>{r['politeness']:.1f}</td>"
            f"<td>{r['civility']:.1f}</td></tr>" for _, r in ev.iterrows())
        # expert-bridges: connector hubs who ALSO bring insight
        eb = scored[(scored["betweenness"] > 0) & (~scored["is_owner"].astype(bool))]
        eb = eb.assign(power=eb["betweenness"] * eb["insight"].fillna(0)) \
               .sort_values("power", ascending=False).head(10)
        rows_eb = "".join(
            f"<tr><td>{nm(r)}</td><td>{r['community']}</td>"
            f"<td>{r['betweenness']:.3f}</td><td>{r['insight']:.1f}</td></tr>"
            for _, r in eb.iterrows())
        disc_section = f"""
<h2>Discourse quality (who brings substance)</h2>
<p class="note">Each comment scored 0-4 for politeness / constructiveness /
professional insight / civility (stance -2..+2) by an LLM in its original language.
Audience means — insight {avg['insight']:.2f}, constructiveness
{avg['constructiveness']:.2f}, politeness {avg['politeness']:.2f},
civility {avg['civility']:.2f}.</p>
<h3 style="font-size:15px">Expert voices — highest professional insight</h3>
<table><tr><th>person</th><th>insight</th><th>constructiveness</th>
<th>politeness</th><th>civility</th></tr>{rows_ev}</table>
<h3 style="font-size:15px;margin-top:18px">Expert-bridges — connectors who also bring substance</h3>
<p class="note">Highest-leverage relationships: spread content across clusters AND
carry domain expertise (betweenness × insight).</p>
<table><tr><th>person</th><th>community</th><th>betweenness</th>
<th>insight</th></tr>{rows_eb}</table>
"""

    # geography (from profile enrichment, if present)
    geo_section = ""
    if "city" in nodes.columns and (nodes["city"].astype(str).str.len() > 0).any():
        cities = nodes.loc[nodes["city"].astype(str).str.len() > 0, "city"]
        top_cities = cities.value_counts().head(15)
        rows_city = "".join(f"<tr><td>{html.escape(str(c))}</td><td>{n}</td></tr>"
                            for c, n in top_cities.items())
        cov = (nodes["city"].astype(str).str.len() > 0).sum()
        # dominant city per community (top 8 communities)
        big = nodes["community"].value_counts().head(8).index
        rows_cc = ""
        for cm in big:
            sub = nodes[(nodes["community"] == cm) &
                        (nodes["city"].astype(str).str.len() > 0)]
            if len(sub):
                top = sub["city"].value_counts().head(3)
                desc = ", ".join(f"{html.escape(str(c))} ({n})" for c, n in top.items())
                rows_cc += f"<tr><td>{cm}</td><td>{len(sub)}</td><td>{desc}</td></tr>"
        occ = nodes.get("work")
        occ_cov = int((occ.astype(str).str.len() > 0).sum()) if occ is not None else 0
        geo_section = f"""
<h2>Geography &amp; profile enrichment</h2>
<p class="note">Resolved from public profiles for {cov} of {len(nodes)} people
(occupation for {occ_cov}). Region clusters reveal the audience's real-world footprint.</p>
<table><tr><th>top city</th><th>people</th></tr>{rows_city}</table>
<h3 style="font-size:15px;margin-top:18px">Dominant city per community</h3>
<table><tr><th>community</th><th>located</th><th>top cities</th></tr>{rows_cc}</table>
"""

    doc = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>FB Audience SNA</title>
<style>
  :root{{--ink:#1a1a2e;--muted:#555;--line:#e4e4ea;--accent:#2a6df4;}}
  body{{font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);
       background:#fff;max-width:920px;margin:40px auto;padding:0 24px;}}
  h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:18px;margin:30px 0 10px;
       border-bottom:2px solid var(--accent);display:inline-block;padding-bottom:3px}}
  .sub{{color:var(--muted);margin:0 0 8px}}
  table{{border-collapse:collapse;width:100%;margin:8px 0 16px;font-size:14px}}
  th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}}
  th{{background:#f6f7fb}} .cards{{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0}}
  .card{{flex:1;min-width:150px;background:#f6f7fb;border-radius:10px;padding:14px 16px}}
  .card b{{font-size:24px;display:block;color:var(--accent)}}
  img{{width:100%;border:1px solid var(--line);border-radius:10px;margin:10px 0}}
  .note{{color:var(--muted);font-size:13px}}
</style>
<h1>Facebook Audience — Social Network Analysis</h1>
<p class="sub">Co-engagement + reply network reconstructed from comments on your own posts.
Pseudonymous interaction graph; bridge names shown for actionability.</p>
<div class="cards">
  <div class="card"><b>{len(nodes)}</b>engaged people</div>
  <div class="card"><b>{len(posts)}</b>posts analyzed</div>
  <div class="card"><b>{len(comm_sizes)}</b>communities</div>
  <div class="card"><b>{q_note}</b>modularity Q</div>
</div>
<h2>Community intersection map</h2>
<p class="note">Each node is a community (size = members); edge thickness = cross-cluster
co-engagement. The decluttered view of how your clusters interconnect.</p>
<img src="figures/community_graph.png" alt="community intersection graph">
<h2>Full co-engagement network</h2>
<img src="figures/network.png" alt="co-engagement network">
<h2>Communities</h2>
<table><tr><th>cluster</th><th>members</th><th>character</th></tr>{rows_comm}</table>
<h2>Bridges — connector hubs &amp; brokers</h2>
<p class="note">Highest-leverage relationships: they spread content across clusters.</p>
<table><tr><th>person</th><th>community</th><th>betweenness</th>
<th>participation</th><th>role</th></tr>{rows_bridge}</table>
<h2>Behaviour segments</h2>
<table><tr><th>segment</th><th>people</th></tr>{rows_beh}</table>
{disc_section}
{geo_section}
<p class="note">Topic affinity and discourse-quality (politeness / constructiveness /
professional insight) layers are added once the discourse stage runs.</p>
</html>"""
    out.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Render SNA figure + HTML report")
    ap.add_argument("--anonymize", action="store_true", help="hide all names")
    args = ap.parse_args()

    P = nx.read_graphml(DATA / "graph_coengage.graphml")
    nodes = pd.read_csv(DATA / "nodes_analyzed.csv").fillna("")
    posts = pd.read_csv(DATA / "posts.csv")
    from networkx.algorithms.community import louvain_communities, modularity
    q = modularity(P, louvain_communities(P, weight="weight", seed=42),
                   weight="weight")

    draw_network(P, nodes, DATA / "figures" / "network.png")
    html_report(nodes, posts, f"{q:.3f}", args.anonymize, DATA / "report.html")
    print(f"Report -> data/report.html  +  data/figures/network.png")


if __name__ == "__main__":
    main()
