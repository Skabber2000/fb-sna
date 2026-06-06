#!/usr/bin/env python3
"""v2 report: multi-layer psychographic re-investigation -> data/report_v2.html
Self-contained (figures base64-embedded), light theme.

    python -m analysis.report_v2
"""
from __future__ import annotations

import base64
import html as H
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FIG = DATA / "figures"


def img(name: str, cap: str) -> str:
    p = FIG / name
    if not p.exists():
        return f"<p><em>figure missing: {name}</em></p>"
    b = base64.b64encode(p.read_bytes()).decode()
    return (f'<figure><img src="data:image/png;base64,{b}" alt="{H.escape(cap)}">'
            f"<figcaption>{H.escape(cap)}</figcaption></figure>")


def pre(path: Path, title: str) -> str:
    if not path.exists():
        return ""
    txt = path.read_text(encoding="utf-8")
    return f"<details><summary>{H.escape(title)}</summary><pre>{H.escape(txt)}</pre></details>"


def main() -> None:
    ari = pd.read_csv(DATA / "ari_matrix.csv", index_col=0)
    ari_row = ari.loc["structural"].drop("structural").round(3)
    ari_html = ari_row.to_frame("ARI vs structural").to_html(border=0)

    css = """
    body{font-family:Segoe UI,system-ui,sans-serif;max-width:1080px;margin:24px auto;
         padding:0 16px;color:#16181d;background:#fff;line-height:1.55}
    h1{border-bottom:3px solid #0057B7}h2{border-bottom:1px solid #d7dbe0;padding-bottom:4px;margin-top:34px}
    figure{margin:18px 0;text-align:center}img{max-width:100%;border:1px solid #e3e6ea;border-radius:6px}
    figcaption{font-size:.85em;color:#5a6270;margin-top:6px}
    table{border-collapse:collapse;font-size:.9em}td,th{padding:4px 10px;border-bottom:1px solid #eceef1}
    pre{background:#f6f7f9;padding:12px;overflow-x:auto;font-size:.8em;border-radius:6px}
    .key{background:#f0f6ff;border-left:4px solid #0057B7;padding:10px 14px;margin:14px 0}
    details{margin:10px 0}summary{cursor:pointer;color:#0057B7;font-weight:600}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 24px}
    """

    key_findings = """
    <div class=key><b>1. Psychology is orthogonal to community structure.</b> Every
    psychographic clustering (emotions, values, moral foundations, epistemic style,
    politics, topics) has ARI &approx; 0 against the co-engagement communities. The 16
    communities are conversational arenas, not worldview tribes.</div>
    <div class=key><b>2. Conversations sort by tone, not ideology.</b> Reply-graph
    homophily: civility .111, irony .094, contempt .088, anger .081, conspiracy-mindedness
    .070 — all significant; hawk/dove, traditionalism, individualism — none. Exposure
    mixes everyone; dialogue micro-segregates by manners and epistemics.</div>
    <div class=key><b>3. The audience is an opinion-leading professional stratum, not
    the general public.</b> 93% of 21,199 followers are 35+ (UA Facebook norm: 25-34
    largest); listed higher education ~2&times; the national rate; 76% present with real
    photos; discourse register analytical. By Katz-Lazarsfeld and Bourdieu criteria the
    composite claim "opinion-leading, high-cultural-capital audience" is defensible.</div>
    <div class=key><b>4. Author-affect is mildly net-positive and polarized</b> (13.4%
    positive vs 11.7% negative). Hostility is status-competitive, peripheral,
    topic-predictable (nuclear), and individually concentrated.</div>
    <div class=key><b>5. Expressed antisemitism is rare (0.29% of comments)</b>; outgroup
    hostility travels with conspiratorial reasoning (r=.39), not low education; trigger
    topic is geopolitics; hottest community is C0, not the originally-flagged C6.</div>
    """

    audience = """
    <div class=grid>
    <div><h3>Full follower base (dashboard)</h3><ul>
    <li>21,199 followers; +215/-58 per 28d</li>
    <li><b>Age: 45-54 35.8% · 35-44 29.3% · 55-64 18.1% · 65+ 9.8% · &lt;35 7.0%</b></li>
    <li>Ukraine 80.1%; Kyiv 65.2% of located; diaspora ~13% (DE/PL/US/UK)</li>
    <li>Views from followers: 76.8%</li></ul></div>
    <div><h3>Engaged audience (2,281)</h3><ul>
    <li>2,065 commenters + 216 reaction-only</li>
    <li>11,036 comments · 1.14M reactions on 448 posts</li>
    <li>Avatars: 76% real photo; 24% UA symbols; 4.3% in uniform; 43%m/38%f</li>
    <li>Languages: UK 70% · RU 12% · EN 1%</li></ul></div></div>
    """

    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>FB-SNA v2 — Multi-layer Psychographic Re-investigation</title>",
        f"<style>{css}</style></head><body>",
        "<h1>FB-SNA v2 — Multi-layer Psychographic Re-investigation</h1>",
        "<p>facebook.com/nayshtetik audience · 493 posts · 9,651 comments scored on "
        "34 dimensions · 1,204 avatars vision-scored · full-follower dashboard data · "
        "generated 2026-06-06</p>",
        "<h2>Key findings</h2>", key_findings,
        "<h2>Who is the audience</h2>", audience,
        "<h2>Layers × communities</h2>",
        "<p>Mean layer scores differ across communities (heatmap), but cluster "
        "<i>boundaries</i> do not align with any psychological axis (ARI table).</p>",
        img("layers_heatmap.png", "Communities × psychographic layers (z-scored means)"),
        ari_html,
        "<h2>Author-affect: hate ↔ love</h2>",
        img("layers_affect.png", "Expressed feeling toward the author, -4..+4 (log scale)"),
        "<p>25.1% of comments express affect toward the author: 13.4% positive, 11.7% "
        "negative (1.1:1). Warmth 568 · hostility 499 · teasing 345 · mockery 299 · "
        "respect 288 · admiration 172 · gratitude 121. Most affectionate: C4 (+0.71), "
        "C11 (+0.61); most hostile: C15 diaspora intellectuals (-0.22), C13 (-0.16). "
        "Nuclear posts draw the most personal negativity (-0.21); science-medicine the "
        "most warmth (+0.30).</p>",
        pre(DATA / "affect.md", "affect.md — full tables"),
        "<h2>Hostility vectors</h2>",
        "<ol><li><b>Psychological:</b> anger 2.1 / contempt 2.0 / dogmatism 1.6 vs rest "
        "0.7/0.6/1.0; <i>not</i> more conspiratorial; less evidence-based. "
        "Status-competition, not ideology.</li>"
        "<li><b>Topical:</b> nuclear 8.9% hostile-rate, personal-satire 6.8%, economy 6.5%.</li>"
        "<li><b>Structural:</b> periphery (C1 8.2%, C13 7.4%) — heavy debater clusters are "
        "below average; C2 lowest (2.0%).</li>"
        "<li><b>Individual:</b> concentrated in a handful of serial accounts; none are "
        "bridges or experts.</li></ol>",
        "<h2>Xenophobia / antisemitism (aggregate)</h2>",
        "<p>5.44% of comments carry outgroup hostility ≥2; targets: russians 205, west "
        "122, jews 28 (0.29% of all comments), migrants 26, muslims 24. Forms: stereotype "
        "261 &gt; dehumanization 81 &gt; conspiracy-trope 76 &gt; slur 53. Root-cause: "
        "correlation with conspiratorial reasoning r=.39 (insight r=-.10). Trigger theme: "
        "geopolitics (7.3%). Population anchor: ADL Global-100 Ukraine 29% (2023, lowest "
        "in E. Europe).</p>",
        pre(DATA / "xenophobia.md", "xenophobia.md — full tables"),
        "<h2>Wellbeing signals (aggregate-only)</h2>",
        "<p>Expressed distress 1.3% · exhaustion 1.0% · resilience 3.0% of comments — "
        "analytical, not confessional discourse (population surveys: 65% moderate "
        "stress). Pockets: C14, C13. Not clinical measures.</p>",
        pre(DATA / "wellbeing.md", "wellbeing.md — cluster table"),
        "<h2>Topics × reactions: 1.14M-reaction emotional map</h2>",
        img("reaction_mix.png", "Emotional reaction mix by theme (Like excluded)"),
        "<p>Nuclear: 31% Angry + 16% Sad (most negative by reactions, affect AND "
        "hostility — triple-confirmed). Economy: 39% Love + 17% Care (warmest). "
        "AI-tech: 72% Haha. Overall Haha share 15.7% — sardonic humor culture at scale.</p>",
        "<h2>Temporal & language</h2>",
        img("temporal_mood.png", "Engagement volume and mood trajectory"),
        img("temporal_language.png", "Comment language share over time"),
        "<p>UK 70% / RU 12% / EN 1%; the RU→UK transition pre-dates the observation "
        "window (stable since Oct 2023; 1 RU→UK vs 3 UK→RU switchers among 299 "
        "bilingual-history users).</p>",
        "<h2>Homophily: exposure mixes, conversation sorts</h2>",
        img("homophily.png", "Assortativity z-scores vs permutation null (co-engagement)"),
        "<p>Co-engagement assortativity is negligible (|r|≤.02) and role-DISassortative "
        "(hubs mix with casuals). Reply-graph homophily is 3-5&times; stronger and "
        "tone-dominated: civility .111, irony .094, contempt .088, anger .081, "
        "conspiracy .070, west-trust .064. Ideology dims not significant.</p>",
        pre(DATA / "homophily.md", "homophily.md — all dimensions"),
        "<h2>Sociological verdict: elite or general public?</h2>",
        "<p>Composite answer: <b>an opinion-leading professional stratum</b> — education "
        "~2&times; national tertiary floor (53% listed vs 26.3% pop. ≥15), age structure "
        "inverted vs UA Facebook (93% are 35+), analytical register, low expressed "
        "prejudice vs ADL baseline, and sociometric opinion-leader structure "
        "(connector-hubs, expert-bridges). Where the audience matches the population: "
        "institutional distrust (Rada trust balance −58.9% nationally). 'Intellectual "
        "elite' is defensible only as this composite claim — see "
        "docs/SOCIOLOGY_BASELINES.md for sources and caveats.</p>",
        "<h2>Method & caveats</h2>",
        "<ul><li>LLM rubric scoring (Haiku 4.5) on native-language text; two passes, "
        "34 dims; irony explicitly modeled.</li>"
        "<li>Author-affect scored only when directed at the author.</li>"
        "<li>Wellbeing/outgroup reported aggregate-only (ETHICS.md).</li>"
        "<li>Comment dates anchored to post dates (monthly grain).</li>"
        "<li>Per-person reaction types unrecoverable; reaction layer is post-level.</li>"
        "<li>ARI &approx; 0 partly reflects soft community structure (Q≈0.26).</li>"
        "<li>Engaged audience = 10.8% of followers; silent-majority inferences rely on "
        "dashboard aggregates only.</li></ul>",
        "</body></html>",
    ]
    out = DATA / "report_v2.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
