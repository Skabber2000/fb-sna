#!/usr/bin/env python3
"""Phase 0b: variable-level register of nodes_analyzed.csv.

For every column: provenance category, coverage, and release decision
(keep / aggregate-only / drop). Output: docs/VARIABLE_REGISTER.md

    python -m analysis.phase0_register
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# provenance -> (category, release decision)
CATS = {
    # observed behavior (public actions on public posts)
    **{c: ("observed-behavioral", "keep") for c in [
        "n_comments", "reactions_received", "posts_engaged", "reactions_given",
        "engaged_via", "community", "betweenness", "wm_zscore",
        "participation", "ga_role", "behaviour_cluster", "dominant_lang",
        "n_scored", "n_a", "n_b"]},
    # identity / public-profile strings (PII)
    **{c: ("profile-PII", "drop") for c in [
        "user", "author_name", "work", "education", "location", "city"]},
    # avatar vision inferences
    **{c: ("avatar-inferred", "aggregate-only") for c in [
        "av_ptype", "av_unif", "av_uasym", "av_grp", "av_fml", "av_age",
        "av_gnd", "av_smil"]},
    # LLM discourse (v1)
    **{c: ("LLM-discourse", "keep") for c in [
        "politeness", "constructiveness", "insight", "civility", "stance"]},
    # LLM expressive (pass A)
    **{c: ("LLM-expressive", "keep") for c in [
        "ang", "iro", "hop", "rsg", "ent", "anx", "cnt", "frm", "hum", "prf"]},
    # sensitive-tier inferences: author-affect, wellbeing, worldview
    **{c: ("LLM-sensitive", "aggregate-only") for c in [
        "aff", "dis", "exh", "rsl", "care", "fair", "loya", "auth", "libe",
        "trad", "sexp", "indv", "scfr", "evid", "cnsp", "dogm", "itru",
        "wtru", "hawk", "ogh", "lgbt", "gtrd", "sxm"]},
    "is_owner": ("flag", "keep"),
}


def main() -> None:
    df = pd.read_csv(DATA / "nodes_analyzed.csv")
    rows = []
    for c in df.columns:
        cat, rel = CATS.get(c, ("UNCLASSIFIED", "review"))
        cov = df[c].notna().mean()
        rows.append({"column": c, "category": cat, "coverage": f"{cov:.0%}",
                     "release": rel})
    reg = pd.DataFrame(rows)
    n_uncl = int((reg["category"] == "UNCLASSIFIED").sum())

    lines = ["# Variable Register (Phase 0b)", "",
             f"`nodes_analyzed.csv`: {len(df)} users x {len(df.columns)} columns. "
             f"Unclassified: {n_uncl}.", "",
             "Release decisions: **keep** = publishable per-user; "
             "**aggregate-only** = community/stratum level only, never "
             "per-user; **drop** = excluded from any release dataset "
             "(identity & PII).", "",
             reg.to_markdown(index=False), "",
             "## Notes",
             "- `user` is a pseudonym but joins to PII inside the private "
             "dataset; treated as PII for release.",
             "- LLM-sensitive dims describe EXPRESSED content, not inner "
             "attitudes; even so they are aggregate-only.",
             "- Comment-level tables follow the same map; raw text is "
             "excluded from release (searchable -> re-identifying).", ""]
    out = ROOT / "docs" / "VARIABLE_REGISTER.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}; categories:\n{reg['category'].value_counts().to_string()}")


if __name__ == "__main__":
    main()
