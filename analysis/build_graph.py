#!/usr/bin/env python3
"""Stage 2: build the interaction graphs from parsed engagement.

Inputs (data/):  comments.csv  [+ reactions.csv, shares.csv if present]
Outputs (data/): graph_reply.graphml      directed user->user reply network R
                 graph_coengage.graphml    undirected co-engagement projection P
                 nodes.csv                 per-user attributes

Design notes (see SNA_METHODOLOGY.md):
- Co-engagement P uses Newman weighting 1/(n_p-1) so a viral post doesn't make a
  hairball. Built from the union of commenters (+ reactors if available).
- The page owner is flagged and EXCLUDED from P by default (he replies to nearly
  everyone, which would create a star and wash out real community structure).
  He is kept in the reply graph R, where his replies are meaningful.
"""
from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OWNER_NAMES = {"Eugene Nayshtetik", "nayshtetik"}


def _maybe_csv(path: Path) -> pd.DataFrame | None:
    """Read a CSV, returning None if missing or empty (no columns)."""
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path).fillna("")
        return df if len(df) else None
    except pd.errors.EmptyDataError:
        return None


def load() -> tuple[pd.DataFrame, pd.DataFrame | None, pd.DataFrame | None]:
    comments = pd.read_csv(DATA / "comments.csv").fillna("")
    return comments, _maybe_csv(DATA / "reactions.csv"), _maybe_csv(DATA / "shares.csv")


def owner_users(comments: pd.DataFrame) -> set[str]:
    mask = comments["author_name"].isin(OWNER_NAMES)
    return set(comments.loc[mask, "user"])


def build_reply_graph(comments: pd.DataFrame) -> nx.DiGraph:
    g = nx.DiGraph()
    edges = comments[comments["parent_user"].astype(str).str.len() > 3]
    for _, r in edges.iterrows():
        a, b = r["user"], r["parent_user"]
        if a == b:
            continue
        if g.has_edge(a, b):
            g[a][b]["weight"] += 1
        else:
            g.add_edge(a, b, weight=1)
    return g


def build_coengagement(comments, reactions, owners) -> nx.Graph:
    """Newman-weighted co-engagement projection, owner excluded."""
    engage: dict[str, set[str]] = {}   # post_id -> set of users
    for _, r in comments.iterrows():
        if r["user"] in owners:
            continue
        engage.setdefault(r["post_id"], set()).add(r["user"])
    if reactions is not None:
        for _, r in reactions.iterrows():
            if r["user"] in owners:
                continue
            engage.setdefault(r["post_id"], set()).add(r["user"])

    g = nx.Graph()
    for users in engage.values():
        n = len(users)
        if n < 2:
            continue
        w = 1.0 / (n - 1)             # Newman collaboration weighting
        for u, v in combinations(sorted(users), 2):
            if g.has_edge(u, v):
                g[u][v]["weight"] += w
            else:
                g.add_edge(u, v, weight=w)
    return g


def node_table(comments, reactions, shares, owners) -> pd.DataFrame:
    # universe = everyone who commented OR reacted (reactors are real audience)
    users = set(comments["user"])
    if reactions is not None:
        users |= set(reactions["user"])
    nodes = pd.DataFrame({"user": sorted(users)})

    g = comments.groupby("user")
    nodes["n_comments"] = nodes["user"].map(g.size()).fillna(0).astype(int)
    nodes["reactions_received"] = nodes["user"].map(
        g["reactions"].sum()).fillna(0).astype(int)
    # posts engaged = union of commented + reacted posts
    posts = {u: set(s) for u, s in comments.groupby("user")["post_id"]}
    if reactions is not None:
        for u, s in reactions.groupby("user")["post_id"]:
            posts.setdefault(u, set()).update(s)
    nodes["posts_engaged"] = nodes["user"].map(
        lambda u: len(posts.get(u, set()))).astype(int)
    nodes["dominant_lang"] = nodes["user"].map(
        g["lang"].agg(lambda s: s.value_counts().idxmax())).fillna("und")
    # name from comments, else from reactions
    name = dict(zip(comments["user"], comments["author_name"]))
    if reactions is not None:
        for u, nm in zip(reactions["user"], reactions["author_name"]):
            name.setdefault(u, nm)
    nodes["author_name"] = nodes["user"].map(name).fillna("")
    nodes["is_owner"] = nodes["user"].isin(owners)
    nodes["reactions_given"] = (
        nodes["user"].map(reactions.groupby("user").size()).fillna(0).astype(int)
        if reactions is not None else 0)
    nodes["engaged_via"] = nodes.apply(
        lambda r: "comment" if r["n_comments"] > 0 else "reaction_only", axis=1)
    if shares is not None:
        nodes["is_sharer"] = nodes["user"].isin(set(shares["user"]))
    return nodes


def summarize(name: str, g) -> None:
    if g.number_of_nodes() == 0:
        print(f"  {name}: empty"); return
    directed = g.is_directed()
    comp = (nx.number_weakly_connected_components(g) if directed
            else nx.number_connected_components(g))
    dens = nx.density(g)
    print(f"  {name}: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges, "
          f"density={dens:.4f}, components={comp}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build interaction graphs")
    ap.add_argument("--keep-owner", action="store_true",
                    help="include the page owner in co-engagement (default: exclude)")
    args = ap.parse_args()

    comments, reactions, shares = load()
    owners = set() if args.keep_owner else owner_users(comments)

    reply = build_reply_graph(comments)
    coeng = build_coengagement(comments, reactions, owners)
    nodes = node_table(comments, reactions, shares, owners)

    nx.write_graphml(reply, DATA / "graph_reply.graphml")
    nx.write_graphml(coeng, DATA / "graph_coengage.graphml")
    nodes.to_csv(DATA / "nodes.csv", index=False)

    print(f"Graphs built ({'reactions merged' if reactions is not None else 'comments only'}):")
    summarize("reply R     ", reply)
    summarize("coengage P  ", coeng)
    print(f"  nodes.csv: {len(nodes)} users "
          f"({nodes['is_owner'].sum()} owner-flagged, excluded from P)")
    print(f"  -> data/graph_reply.graphml, graph_coengage.graphml, nodes.csv")


if __name__ == "__main__":
    main()
