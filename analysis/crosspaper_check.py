#!/usr/bin/env python3
"""Cross-paper consistency check: shared facts must agree across P1/P2/P3.

For each canonical token (number/value), report which papers contain it,
and flag known-wrong variants if any paper still carries them.

    python -m analysis.crosspaper_check
"""
from __future__ import annotations

import re
from pathlib import Path

PAPERS = {p: (Path(r"C:\Projects\fb-sna\paper") / p / "main.tex")
          .read_text(encoding="utf-8")
          for p in ["p1_methods", "p2_homophily", "p3_emotion"]}


def norm(s: str) -> str:
    # collapse LaTeX thousands separators and whitespace for matching
    return re.sub(r"\s+", " ", s.replace("{,}", ",").replace("~", " "))


TEX = {k: norm(v) for k, v in PAPERS.items()}

# canonical facts -> (regex on normalized text, wrong variants regex or None)
FACTS = {
    "followers 21,199":        (r"21,199", None),
    "engaged 2,281":           (r"2,281", None),
    "commenters 1,555":        (r"1,555", r"2,065"),
    "reaction-only 726":       (r"\b726\b", r"\b216 reaction|216 reaction"),
    "comments 11,036":         (r"11,036", None),
    "scored 9,651":            (r"9,651", None),
    "reactions 1,142,091":     (r"1,142,091", None),
    "posts captured 493":      (r"\b493\b", None),
    "posts in window 483":     (r"\b483\b", None),
    "co-engage nodes 2,278":   (r"2,278", None),
    "co-engage edges 53,786":  (r"53,786", None),
    "reply nodes 758":         (r"\b758\b", None),
    "reply edges 1,157":       (r"1,157", None),
    "communities 16":          (r"\b16 (communities|interaction)", None),
    "modularity .259/.26":     (r"0\.259|Q\s*=\s*0\.26|Q\\approx0\.26|Q \\approx 0\.26", None),
    "max ARI 0.031":           (r"0\.031", None),
    "civility homophily .111": (r"0?\.111", None),
    "civility retest .754":    (r"0?\.754", None),
    "age 93% 35+":             (r"93\\?%|93\\%", None),
    "Kyiv 65.2%":              (r"65\.2", None),
    "Ukraine 80.1%":           (r"80\.1", None),
    "events 34":               (r"\b34\b", r"\b35 (war )?events|35 events"),
    "reactors-never-comment 59.6%": (r"59\.6", r"69\\?% of reactors"),
    "pol-positive hope +.609": (r"0?\.609", None),
    "pol-positive aff +1.305": (r"1\.305", None),
}

print(f"{'fact':36} {'p1':>4} {'p2':>4} {'p3':>4}  wrong-variant hits")
problems = []
for name, (pat, wrong) in FACTS.items():
    row = []
    for p in ["p1_methods", "p2_homophily", "p3_emotion"]:
        row.append("X" if re.search(pat, TEX[p]) else "-")
    whits = []
    if wrong:
        for p in ["p1_methods", "p2_homophily", "p3_emotion"]:
            if re.search(wrong, TEX[p]):
                whits.append(p)
                problems.append((name, p))
    print(f"{name:36} {row[0]:>4} {row[1]:>4} {row[2]:>4}  "
          f"{('!! ' + ', '.join(whits)) if whits else ''}")

print()
if problems:
    print("PROBLEMS (stale variants present):")
    for name, p in problems:
        print(f"  - {p}: {name}")
else:
    print("No stale variants found in any paper.")
