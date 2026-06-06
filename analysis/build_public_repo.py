#!/usr/bin/env python3
"""Assemble the public release repo at C:\\Projects\\fb-sna-public.

Safety gates, applied to EVERY text file before copy:
  1. name scan  - no author display-name (or unique name token) from
                  nodes.csv / enrich_manifest.tsv may appear
  2. secret scan- no sk-ant / xai- / sk-proj / token-like strings
Files failing a gate are excluded and reported, never copied.

Collection tooling (fb_capture/) is deliberately NOT released (dual-use:
think-tank ethics panel recommendation). Analysis code is released.

    python -m analysis.build_public_repo
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parent.parent
DST = Path(r"C:\Projects\fb-sna-public")

DATA_FILES = [
    "release/users.csv", "release/comments.csv", "release/communities.csv",
    "release/README.md", "war_events.csv", "ari_matrix.csv",
    "layer_profiles.csv", "theme_affinity.csv", "homophily.csv",
    "homophily.md", "multiplex.md", "event_mood.md", "event_windows.csv",
    "consistency_report.md", "kanon_report.md", "post_reaction_types.csv",
    "sna_descriptives.md", "event_significance.md", "event_significance.csv",
    "community_structure.md", "community_mixing.csv", "validation_extra.md",
    "community_profiles.csv", "difference_test.md", "lang_reliability.md",
    "crossmodel.md",
]
DOC_FILES = ["ETHICS.md", "CODING_MANUAL.md", "VARIABLE_REGISTER.md",
             "SOCIOLOGY_BASELINES.md", "PIPELINE.md", "ARCHITECTURE.md",
             "DATA_DICTIONARY.md", "PREREGISTRATION.md"]
FIG_FILES = ["layers_heatmap.png", "event_mood.png", "homophily.png",
             "reaction_mix.png", "temporal_mood.png", "temporal_language.png",
             "layers_affect.png", "reliability.png", "network_anon.png",
             "degree_dist.png", "community_quotient.png"]
CODE_FILES = sorted(p.name for p in (SRC / "analysis").glob("*.py")
                    if not p.name.startswith("_"))

SECRET = re.compile(r"sk-ant-\w|xai-\w|sk-proj-\w|ghp_\w|AKIA[A-Z0-9]")
# the study owner is the named author of the release - his name is not PII here
OWNER = {"nayshtetik", "eugene nayshtetik", "євген найштетік"}


def name_tokens() -> set[str]:
    nodes = pd.read_csv(SRC / "data" / "nodes.csv")
    names = set(nodes["author_name"].dropna().astype(str))
    toks = set()
    for n in names:
        n = n.strip()
        if len(n) >= 7:                     # full display names
            toks.add(n.lower())
    man = SRC / "data" / "enrich_manifest.tsv"
    if man.exists():
        for line in man.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.split("\t")
            for p in parts[:2]:             # slugs + refs
                if len(p.strip()) >= 8:
                    toks.add(p.strip().lower())
    return {t for t in toks if not any(o in t for o in OWNER)}


def scan(path: Path, toks: set[str]) -> list[str]:
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return ["unreadable"]
    hits = []
    if SECRET.search(txt):
        hits.append("SECRET-PATTERN")
    for t in toks:
        if t in txt:
            hits.append(f"name:{t[:24]}")
            if len(hits) > 4:
                break
    return hits


def main() -> None:
    # refresh content dirs only; preserve .git and README.md
    for sub in ["data", "docs", "figures", "analysis"]:
        if (DST / sub).exists():
            shutil.rmtree(DST / sub)
        (DST / sub).mkdir(parents=True)
    toks = name_tokens()
    print(f"PII token list: {len(toks)} entries")

    copied, excluded = [], []
    jobs = ([(SRC / "data" / f, DST / "data" / Path(f).name) for f in DATA_FILES]
            + [(SRC / "docs" / f, DST / "docs" / f) for f in DOC_FILES]
            + [(SRC / "analysis" / f, DST / "analysis" / f) for f in CODE_FILES])
    for src, dst in jobs:
        if not src.exists():
            excluded.append((src.name, "missing"))
            continue
        hits = scan(src, toks)
        if hits:
            excluded.append((src.name, "; ".join(hits[:3])))
            continue
        shutil.copy2(src, dst)
        copied.append(src.name)
    for f in FIG_FILES:                      # rasters: manually vetted list
        p = SRC / "data" / "figures" / f
        if p.exists():
            shutil.copy2(p, DST / "figures" / f)
            copied.append(f)

    print(f"copied {len(copied)}, excluded {len(excluded)}:")
    for n, why in excluded:
        print(f"  EXCLUDED {n}: {why}")


if __name__ == "__main__":
    main()
