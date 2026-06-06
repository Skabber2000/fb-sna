#!/usr/bin/env python3
"""The complete report: a wartime Facebook life and its audience.
Integrates every layer built 2026-06-05/06 into one narrative document.

    python -m analysis.report_war   ->  data/FB_WAR_REPORT.html
"""
from __future__ import annotations

import base64
import html as H
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FIG = DATA / "figures"
EXP = DATA / "insights_html" / "exports"


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
    return (f"<details><summary>{H.escape(title)}</summary>"
            f"<pre>{H.escape(txt)}</pre></details>")


def tbl(df: pd.DataFrame) -> str:
    return df.to_html(border=0, index=False, escape=True)


def main() -> None:
    posts = pd.read_csv(DATA / "posts.csv")
    posts["dt"] = pd.to_datetime(posts["post_time"], errors="coerce")
    war = posts[posts["dt"] >= "2023-09-01"]
    yearly = war.groupby(war["dt"].dt.year).size()
    themes = war["theme"].value_counts().head(11)

    ex = pd.concat([pd.read_csv(f) for f in EXP.glob("*.csv")],
                   ignore_index=True).drop_duplicates("Post ID")
    for c in ["Views", "Interactions", "Reactions"]:
        ex[c] = pd.to_numeric(ex[c], errors="coerce")
    top_posts = (ex.nlargest(6, "Views")[["Publish time", "Title", "Views",
                                          "Interactions"]]
                 .assign(Title=lambda d: d["Title"].astype(str).str[:90]))

    win = pd.read_csv(DATA / "event_windows.csv")
    top_ev = win.reindex(win[["ang", "anx", "hop", "rsg"]].abs()
                         .sum(axis=1).nlargest(8).index)
    top_ev = top_ev[["date", "event", "category", "n", "ang", "anx", "hop", "aff"]]

    css = """
    body{font-family:Georgia,'Times New Roman',serif;max-width:980px;margin:28px auto;
         padding:0 18px;color:#1a1c20;background:#fff;line-height:1.62;font-size:17px}
    h1{font-size:2em;border-bottom:3px solid #0057B7;padding-bottom:8px}
    h2{border-bottom:1px solid #d7dbe0;padding-bottom:4px;margin-top:40px;color:#0b2545}
    .sub{color:#5a6270;font-size:.92em}
    figure{margin:18px 0;text-align:center}img{max-width:100%;border:1px solid #e3e6ea;border-radius:6px}
    figcaption{font-size:.82em;color:#5a6270;margin-top:6px;font-family:Segoe UI,sans-serif}
    table{border-collapse:collapse;font-size:.82em;font-family:Segoe UI,sans-serif;margin:10px 0}
    td,th{padding:4px 10px;border-bottom:1px solid #eceef1;text-align:left}
    pre{background:#f6f7f9;padding:12px;overflow-x:auto;font-size:.74em;border-radius:6px}
    .key{background:#f0f6ff;border-left:4px solid #0057B7;padding:10px 16px;margin:16px 0}
    .warn{background:#fff8ec;border-left:4px solid #D4A843;padding:10px 16px;margin:16px 0}
    details{margin:10px 0;font-family:Segoe UI,sans-serif}summary{cursor:pointer;color:#0057B7;font-weight:600}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 28px}
    .stat{font-size:1.5em;font-weight:700;color:#0b2545}
    """

    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>A Wartime Facebook Life</title>",
        f"<style>{css}</style></head><body>",
        "<h1>A Wartime Facebook Life</h1>",
        "<p class=sub>facebook.com/nayshtetik &middot; October 2023 &ndash; June 2026 "
        "&middot; 483 posts &middot; 11,036 comments &middot; 1.14M reactions &middot; "
        "2,281 engaged people of 21,199 followers &middot; 34 scored dimensions "
        "&middot; generated 2026-06-06</p>",

        "<h2>1 &middot; The life: what you wrote, and who saw it</h2>",
        f"<p>Across the observed war window you published <b>{len(war)} posts</b> "
        f"({' / '.join(f'{y}: {n}' for y, n in yearly.items())}). The mix is the "
        "portrait of a defense-tech founder thinking in public: society &amp; culture "
        f"({themes.get('society-culture', 0)}), geopolitics ({themes.get('geopolitics', 0)}), "
        f"defense technology ({themes.get('defense-tech', 0)}), personal life "
        f"({themes.get('personal', 0)}), war strategy ({themes.get('war-strategy', 0)}), "
        "with AI, Ukrainian politics, economy, nuclear matters and science filling the rest.</p>",
        "<p>The current quarter delivered <b>2.52M views</b> and 1.72M impressions "
        "(861K views/month), a 1.52% engagement rate &mdash; two to three times the "
        "Facebook page norm &mdash; and 441 hours of audience attention. Reach is "
        "viral-skewed: the median post makes ~7.8K views while one post can carry "
        "1.26M.</p>",
        "<h3>Most-seen posts (last 90 days)</h3>", tbl(top_posts),

        "<h2>2 &middot; The audience: who gathered around you</h2>",
        "<div class=grid>"
        "<div><h3>All 21,199 followers</h3><ul>"
        "<li><b>93% are 35+</b> (45&ndash;54: 35.8%) &mdash; inverted vs the UA "
        "Facebook norm where 25&ndash;34 dominates</li>"
        "<li>Ukraine 80.1%, Kyiv 65.2% of located; diaspora ~13% (DE/PL/US/UK)</li>"
        "<li>Education ~2&times; the national tertiary floor</li></ul></div>"
        "<div><h3>The 2,281 who engage</h3><ul>"
        "<li>1,555 commenters + 726 reaction-only</li>"
        "<li>Avatars: 76% real photos, 24% UA symbols, 4.3% in uniform</li>"
        "<li>Languages UK 70% / RU 12% / EN 1% &mdash; the RU&rarr;UK shift "
        "completed before this window</li></ul></div></div>",
        "<div class=key><b>The sociological verdict:</b> not the general public. By "
        "education premium, age inversion, analytical register, sociometric "
        "opinion-leader structure and low expressed prejudice, this is an "
        "<b>opinion-leading, high-cultural-capital professional stratum</b> &mdash; "
        "the people who relay ideas onward. It matches the population in exactly one "
        "trait: institutional distrust.</div>",

        "<h2>3 &middot; The room you built: arenas, not tribes</h2>",
        "<p>The 16 conversational communities are <b>arenas, not worldview tribes</b>: "
        "every psychographic clustering (emotions, moral foundations, values, "
        "epistemics, politics, topics) is orthogonal to them (ARI&nbsp;&asymp;&nbsp;0; "
        "multiplex stress-test max 0.031 across co-engagement, reply and combined "
        "graphs). Exposure mixes everyone &mdash; hubs engage alongside casuals.</p>",
        "<p>But <i>conversation</i> sorts: reply-partner choice follows tone and "
        "epistemic style (civility .111, irony .094, contempt .088, conspiracy .070), "
        "never ideology (hawk/dove, traditionalism: ns). Your comment section "
        "micro-segregates by manners, not beliefs &mdash; a direct counterpoint to "
        "the echo-chamber literature.</p>",
        img("layers_heatmap.png", "Communities x psychographic layers (z-scored means)"),

        "<h2>4 &middot; The emotional weather of three war years</h2>",
        "<p>The baseline register is <b>sardonic vigilance</b>: anger 0.73, irony "
        "0.72, contempt 0.68 (on 0&ndash;4 scales) against hope 0.18 and enthusiasm "
        "0.15. This is not despair &mdash; expressed distress is 1.3% and resilience "
        "outweighs it at 3.0% &mdash; it is emotional self-discipline: "
        "intellectualization as a collective coping style.</p>",
        img("event_mood.png", "Monthly mean expressed emotion; war events in grey"),
        "<p>Joining 35 war events to the mood series shows your audience reacts "
        "most to <b>politics, not to the front line</b>:</p>"
        "<ul><li><b>Political-negative</b> events (Oval Office confrontation, "
        "aid pauses) produce the largest anger spikes (+0.25)</li>"
        "<li>The single <b>political-positive</b> event window shows the largest "
        "hope response in the corpus (+0.61) with anger collapsing (&minus;0.37)</li>"
        "<li><b>Aid-positive</b> news calms everything (&minus;0.46 anger)</li>"
        "<li>Invasion <b>anniversaries</b> read as anxiety (+0.29), not anger</li>"
        "<li><b>Strike waves</b> barely move the needle (+0.05) &mdash; "
        "three years in, missiles are routine; betrayal is not.</li></ul>",
        "<h3>Strongest single-event responses</h3>", tbl(top_ev.round(2)),

        "<h2>5 &middot; How they feel about you</h2>",
        img("layers_affect.png", "Expressed feeling toward the author, -4..+4"),
        "<p>A quarter of comments express a feeling toward you personally: 13.4% "
        "positive vs 11.7% negative. Warmth (568) outweighs hostility (499), with a "
        "thick band of teasing (345) &mdash; the affectionate register of this "
        "audience. Hostility, when it comes, has four signatures: psychologically it "
        "is <b>status-competition</b> (high dogmatism, low evidence, <i>not</i> "
        "conspiracy); topically it concentrates on <b>nuclear</b> takes (8.9%) and "
        "satire at groups' expense; structurally it comes from the periphery, not "
        "the debate cores; individually it is concentrated in a handful of serial "
        "accounts, none of them bridges. Your sharpest substantive critics are the "
        "C15 diaspora intellectuals (&minus;0.22) &mdash; the one hostile segment "
        "worth engaging.</p>",

        "<h2>6 &middot; The dark corners (aggregate)</h2>",
        "<p>5.4% of comments carry outgroup hostility &ge;2 &mdash; dominated by "
        "the wartime enemy (russians 205, west 122); expressed antisemitism is "
        "0.29% of comments against a 29% population attitude baseline (ADL). It "
        "travels with conspiratorial reasoning (r=.39), not low education, and "
        "geopolitics posts are its trigger. Wellbeing: analytical, not confessional "
        "&mdash; your comment section is where this audience thinks, not where it "
        "breaks down.</p>",

        "<h2>7 &middot; The silent majority speaks in reactions</h2>",
        img("reaction_mix.png", "Emotional reaction mix by theme (Like excluded)"),
        "<p>1,142,091 reactions are the only voice of the ~19K who never comment. "
        "Their language: Like 69%, <b>Haha 15.7%</b> (the sardonic culture at "
        "scale), Love 7%, Angry 3.9%. Nuclear posts: 31% Angry + 16% Sad &mdash; "
        "the most negative theme by reactions, affect and hostility alike "
        "(triple-confirmed). Economy posts are the warmest (39% Love); AI posts "
        "are entertainment (72% Haha).</p>",

        "<h2>8 &middot; What it is worth</h2>",
        "<p>As ad inventory: blended CPM &asymp; $2.7 (UA-weighted) &rarr; "
        "<b>$7&ndash;14K/yr</b> media-equivalent, an ~85&ndash;90% discount to the "
        "same metrics US-priced ($110&ndash;158K). As an asset: $30&ndash;100K "
        "replacement cost. Meta pays $26/yr &mdash; noise. But the discount "
        "collapses at the level where this audience actually matters: "
        "<b>decision-maker access</b>. Kyiv-dominant, 93% career-stage, "
        "defense/tech/policy-heavy, with expert-bridges &mdash; one enabled B2B "
        "relationship per year exceeds the entire media valuation.</p>",

        "<h2>9 &middot; How solid is all this</h2>",
        "<p>Test-retest of the scoring instrument (200 comments, identical rubric): "
        "every claim-bearing dimension passes r&ge;0.7 (affect .71, outgroup "
        "hostility .78, conspiracy .79, anger .78, irony .76); within-1-point "
        "agreement &ge;.89 everywhere. Two dims failed and were retired (scfr: "
        "noise; lgbt: unmeasurable &mdash; 99% zeros). The orthogonality headline "
        "survived a multiplex stress-test. A 503-comment stratified human-coding "
        "sample is prepared as the final validation gate.</p>",
        "<div class=warn><b>Standing caveats:</b> LLM scores measure <i>expressed</i> "
        "content, not inner attitudes; comment dates are post-anchored (day grain); "
        "engagement selects 10.8% of followers &mdash; silent-majority claims rest "
        "on reactions and dashboard aggregates; event-window deltas confound the "
        "event with your choice to post about it; sensitive dimensions are reported "
        "aggregate-only and the release dataset strips all PII.</div>",

        "<h2>10 &middot; The portrait</h2>",
        "<div class=key>Over three war years you ran, without planning to, a salon "
        "for the Ukrainian professional class: a mostly-male, mostly-Kyiv, "
        "career-stage audience that is educated well above the national norm, "
        "polyglot but settled into Ukrainian, allergic to enthusiasm, fluent in "
        "irony, and emotionally disciplined to a degree that is itself the finding. "
        "They do not sort into tribes around beliefs &mdash; they sort around "
        "<i>manners</i>. They are angrier at betrayal than at missiles. They laugh "
        "as a defense, argue as a sport, reserve their rare hope for politics done "
        "right, and direct their warmth at you in the form of teasing. It is not a "
        "mass audience and was never going to be: it is an instrument panel for how "
        "Ukraine's opinion-leading stratum metabolizes the war &mdash; and it is "
        "worth more as a network than as a megaphone.</div>",

        "<h3>Appendices</h3>",
        pre(DATA / "event_mood.md", "A. War-event mood join"),
        pre(DATA / "multiplex.md", "B. Multiplex stress-test"),
        pre(DATA / "consistency_report.md", "C. Instrument reliability"),
        pre(DATA / "homophily.md", "D. Homophily tables"),
        pre(DATA / "xenophobia.md", "E. Outgroup hostility tables"),
        "</body></html>",
    ]
    out = DATA / "FB_WAR_REPORT.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
