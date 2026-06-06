#!/usr/bin/env python3
"""Phase 0a: k-anonymity scan -> data/kanon_report.md"""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
QI_SETS = {
    "minimal (city+gender+age)": ["city", "av_gnd", "av_age"],
    "typical (+education)": ["city", "av_gnd", "av_age", "education"],
    "strong (+work)": ["city", "av_gnd", "av_age", "education", "work"],
    "max (+location+lang)": ["city", "location", "av_gnd", "av_age",
                             "education", "work", "dominant_lang"],
}

def main():
    df = pd.read_csv(DATA / "nodes_analyzed.csv")
    df = df[df["is_owner"] != True]
    num = lambda c: pd.to_numeric(df.get(c), errors="coerce")
    flags = pd.DataFrame(index=df.index)
    flags["hostile_political"] = (num("itru") <= -1) | (num("wtru") <= -1.5)
    flags["outgroup_hostile"] = num("ogh") >= 1.5
    flags["distress"] = (num("dis") >= 1) | (num("exh") >= 1)
    flags["lgbtq_any"] = num("lgbt").abs() >= 1
    flags["high_conspiracy"] = num("cnsp") >= 1.5
    flags["author_hostile"] = num("aff") <= -1.5
    flags["ru_language"] = df.get("dominant_lang", "").astype(str).eq("ru")
    any_sens = flags.any(axis=1)

    lines = ["# k-Anonymity Scan (Phase 0a)", "",
             f"Users: {len(df)}. Carrying >=1 sensitive inferred label: "
             f"{int(any_sens.sum())} ({any_sens.mean():.0%}).", "",
             "Sensitive-label prevalence:"]
    for c in flags.columns:
        lines.append(f"- {c}: {int(flags[c].sum())}")
    lines.append("")

    rows = []
    for name, qis in QI_SETS.items():
        cols = [c for c in qis if c in df.columns]
        sub = df[cols].fillna("(missing)").astype(str)
        informative = (sub != "(missing)").sum(axis=1) >= 2
        si = sub[informative]
        k = si.groupby(cols)[cols[0]].transform("size")
        k1 = int((k == 1).sum())
        k1s = int(((k == 1) & any_sens[informative]).sum())
        rows.append({"QI set": name, "users_w_QI": int(informative.sum()),
                     "k1_unique": k1, "k1_AND_sensitive": k1s,
                     "k_le_5": int((k <= 5).sum())})
    summ = pd.DataFrame(rows)
    lines += ["## Re-identification exposure by adversary strength", "",
              summ.to_string(index=False), "",
              "## Reading",
              "- k=1 = unique combination of public profile facts; an adversary",
              "  who knows those facts re-identifies the row with certainty.",
              "- k1_AND_sensitive = unique AND carrying a harmful inferred label",
              "  (hostile-political / outgroup / distress / LGBTQ / conspiracy /",
              "  author-hostile / RU-language). These rows are the publication",
              "  and leak risk. Mitigations: suppress work/education in any",
              "  shared table, coarsen city to oblast, never release row-level",
              "  psychographics joined to profile fields."]
    out = DATA / "kanon_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    print(summ.to_string(index=False))

if __name__ == "__main__":
    main()
