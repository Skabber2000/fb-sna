# FB-SNA: A Wartime Facebook Audience, Measured

De-identified data and analysis code from a multilayer psychographic study of
the engaged audience of one Ukrainian public figure's personal Facebook
profile (the author's own), October 2023 – June 2026: 483 posts, 11,036
comments scored on 34 LLM dimensions, 1.14M reactions, 2,281 engaged people
of a 21,199-follower base.

**Author:** Eugene Nayshtetik ([ORCID 0000-0001-9166-3288](https://orcid.org/0000-0001-9166-3288)) · **Preprints (SocArXiv):** [Methods & reliability](https://osf.io/preprints/socarxiv/yu9kz) · [Tone-not-ideology homophily](https://osf.io/preprints/socarxiv/kvpqn) · [Wartime emotion](https://osf.io/preprints/socarxiv/4vfrb)

## Headline findings

1. **Arenas, not tribes.** Every psychographic clustering (emotions, moral
   foundations, values, epistemics, politics, topics) is orthogonal to the
   interaction communities (ARI ≈ 0; multiplex-robust, max 0.031).
2. **Exposure mixes, conversation sorts — by tone, not ideology.**
   Reply-graph homophily: civility .111, irony .094, contempt .088,
   conspiracy-mindedness .070; ideological dimensions non-significant.
3. **Sardonic vigilance.** Baseline register anger .73 / irony .72 vs hope
   .18; expressed distress 1.3% in year 3+ of war — emotional self-discipline
   as the substantive finding.
4. **Politics over missiles.** Strike waves barely move audience mood
   (+0.05 anger); political-negative events spike it (+0.25); the one
   political-positive window produced the largest hope response (+0.61).
5. **Instrument reliability is published, not assumed:** test-retest r per
   dimension in `data/consistency_report.md`; two dimensions failed and were
   retired. Human-coder validation (503-comment stratified sample, manual in
   `docs/CODING_MANUAL.md`) is in progress — treat findings as preliminary.

## Repository layout

| Path | Contents |
|---|---|
| `data/users.csv` | 2,280 engaged users: behavioral + reliability-passing dims, one-way random IDs |
| `data/comments.csv` | 8,503 scored comments (no text, month grain) |
| `data/communities.csv` | community-level aggregates (sensitive tier lives only here; n<10 suppressed) |
| `data/*.md`, `data/*.csv` | aggregate results: homophily, multiplex, event study, reliability, reaction mix |
| `data/war_events.csv` | 35-event war calendar Oct 2023 – May 2026 used in the event study |
| `docs/` | methodology, ethics, variable register, coding manual, population baselines |
| `figures/` | publication figures |
| `analysis/` | the full analysis pipeline (Python) |

## De-identification

All names, profile fields, avatars, raw text, and original pseudonyms are
excluded. Release IDs are fresh random tokens whose mapping was generated in
memory and never persisted (one-way). Sensitive inferred dimensions
(worldview, wellbeing, author-affect, avatar attributes) appear only as
community-level aggregates. Every file in this repository passed an
automated scan against the complete participant name list before inclusion.
See `docs/VARIABLE_REGISTER.md` and `data/kanon_report.md`.

## What is deliberately not here

- **Raw comment/post text** — searchable text is re-identifying.
- **Collection tooling** — the browser-automation capture code is withheld
  as a dual-use precaution (independent ethics-panel recommendation).
  The analysis pipeline (this repo) runs on the released tables.

## Ethics

Owner-authorized collection of public comments on the owner's own public
posts; pseudonymized at ingest; sensitive dimensions aggregate-only;
expression ≠ inner attitude throughout. Full statement: `docs/ETHICS.md`.

## License

Data: CC BY 4.0 · Code: MIT
