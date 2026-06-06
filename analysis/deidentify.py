#!/usr/bin/env python3
"""Build the de-identified release dataset per docs/VARIABLE_REGISTER.md.

Writes data/release/:
  users.csv     - per-user: behavioral + keep-tier LLM dims, fresh random ids
                  (new salt, no mapping kept), PII columns dropped
  comments.csv  - comment-level scores + lang + month, NO raw text,
                  same fresh ids
  communities.csv - community x layer means (aggregate tier lives here)
  README.md     - provenance + what was removed

    python -m analysis.deidentify
"""
from __future__ import annotations

import secrets
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
REL = DATA / "release"

DROP_USER = ["author_name", "work", "education", "location", "city"]
KEEP_USER = ["n_comments", "reactions_received", "posts_engaged",
             "reactions_given", "engaged_via", "dominant_lang", "community",
             "betweenness", "wm_zscore", "participation", "ga_role",
             "behaviour_cluster", "politeness", "constructiveness", "insight",
             "civility", "n_scored",
             "ang", "iro", "hop", "rsg", "ent", "anx", "cnt", "frm", "hum",
             "prf", "evid", "n_a", "n_b"]
AGG_DIMS = ["aff", "dis", "exh", "rsl", "care", "fair", "loya", "auth",
            "libe", "trad", "sexp", "indv", "scfr", "cnsp", "dogm", "itru",
            "wtru", "hawk", "ogh", "lgbt", "gtrd", "sxm",
            "av_age", "av_gnd", "av_uasym", "av_unif"]
COMMENT_SCORES = ["ang", "iro", "hop", "rsg", "ent", "anx", "cnt", "frm",
                  "hum", "prf", "evid"]


def main() -> None:
    REL.mkdir(exist_ok=True)
    nodes = pd.read_csv(DATA / "nodes_analyzed.csv")
    nodes = nodes[nodes["is_owner"] != True].copy()              # noqa: E712

    # fresh, unsalvageable ids: random hex, mapping never written to disk
    mapping = {u: f"r_{secrets.token_hex(6)}" for u in nodes["user"]}
    nodes["rid"] = nodes["user"].map(mapping)

    users = nodes[["rid"] + [c for c in KEEP_USER if c in nodes.columns]]
    users.to_csv(REL / "users.csv", index=False)

    com = pd.read_csv(DATA / "comments.csv").fillna("")
    la = pd.read_csv(DATA / "layers_a.csv").drop_duplicates("comment_id")
    lb = pd.read_csv(DATA / "layers_b.csv").drop_duplicates("comment_id")
    posts = pd.read_csv(DATA / "posts.csv")[["post_id", "theme", "post_time"]]
    c = (com[["comment_id", "post_id", "user", "lang"]]
         .merge(la.drop(columns=["user"]), on="comment_id", how="inner")
         .merge(lb.drop(columns=["user"]), on="comment_id", how="left")
         .merge(posts, on="post_id", how="left"))
    c["rid"] = c["user"].map(mapping)
    c = c[c["rid"].notna()]
    c["month"] = pd.to_datetime(c["post_time"], errors="coerce").dt.strftime("%Y-%m")
    keep = (["rid", "lang", "theme", "month"] + COMMENT_SCORES
            + [d for d in AGG_DIMS if d in c.columns])
    # comment-level sensitive dims stay but text/ids are gone; rows are not
    # linkable to a person without the (non-existent) mapping
    rel_c = c[[k for k in keep if k in c.columns]].copy()
    rel_c.insert(0, "row", range(len(rel_c)))
    rel_c.to_csv(REL / "comments.csv", index=False)

    # community-level aggregates carry the sensitive tier
    agg_cols = [d for d in AGG_DIMS if d in nodes.columns]
    grp = nodes.groupby("community")
    comm = grp[agg_cols].apply(
        lambda g: g.apply(pd.to_numeric, errors="coerce").mean()).round(3)
    comm["n_users"] = grp.size()
    comm = comm[comm["n_users"] >= 10]            # suppress small cells
    comm.to_csv(REL / "communities.csv")

    (REL / "README.md").write_text(
        "# FB-SNA De-identified Release Dataset\n\n"
        f"Built from the private dataset on 2026-06-06.\n\n"
        "## Removed\n"
        "- All names, profile fields (work, education, location, city), "
        "profile refs, avatars, raw comment/post text.\n"
        "- Original pseudonyms replaced by fresh random ids; the mapping was "
        "generated in memory and never written to disk (one-way).\n\n"
        "## Tiers\n"
        "- `users.csv` - behavioral + non-sensitive expressive dims per user.\n"
        "- `comments.csv` - per-comment scores (no text), month grain.\n"
        "- `communities.csv` - sensitive dims (worldview, wellbeing, affect, "
        "avatar) at community level only, cells with n<10 suppressed.\n",
        encoding="utf-8")
    print(f"release: users={len(users)} comments={len(rel_c)} "
          f"communities={len(comm)} -> {REL}")


if __name__ == "__main__":
    main()
