# Human Coding Manual — Validation Subsample (Phase 0c)

**Purpose:** Two bilingual (UK/RU) coders independently score the same 450
comments the LLM scored, on 7 key dimensions. Agreement between coders and
LLM determines which automated dimensions are publishable.

**Materials:** `data/validation/coder_sheet.csv` — one row per comment,
randomized order. Coders see ONLY the comment text (stay blind to LLM scores
and to each other). Fill the `coder_*` columns.

**Context:** All comments were posted publicly under one author's Facebook
posts (Ukrainian public figure; defense/politics/society topics; wartime).
Score what the TEXT EXPRESSES, not what you infer the person privately thinks.

---

## Dimensions

### coder_aff — feeling toward the author (-4 .. +4)
Only when directed at the author himself: addressing him, praising or
attacking HIM or his work. Anger at third parties (governments, groups,
situations) is NOT author-directed → 0.
- -4 hate · -2 hostility/derision · 0 none/neutral · +2 warmth/approval · +4 love/admiration

### coder_akind — kind of author-directed feeling (pick one)
`none | admiration | gratitude | warmth | respect | teasing | condescension | mockery | hostility`

### coder_ang — anger/outrage (0–4)
Expressed anger at anyone/anything. 0 none · 2 clear irritation · 4 fury.

### coder_iro — irony/sarcasm (0–4)
0 literal · 2 noticeably ironic · 4 fully sarcastic (surface meaning inverted).

### coder_cnt — contempt/disdain (0–4)
Looking down on a person or group; dismissiveness, sneering. Distinct from
anger (heat) — contempt is cold superiority.

### coder_evid — evidence-based reasoning (0–2)
0 assertion/opinion only · 1 some reasoning or reference · 2 explicit
evidence: links, data, verifiable specifics.

### coder_ogh — outgroup hostility (0–4)
Hostility toward an ethnic/national/religious/social GROUP as a group
(not individuals, not governments-as-actors). 0 none · 2 clear negative
generalization · 4 dehumanization/slur.

---

## Rules

1. Score the comment in its original language; do not translate first.
2. Irony does not cancel scoring: a sarcastic insult still scores aff/cnt.
3. Quoting someone else's hostile words to criticize them ≠ the coder's own
   hostility (score the commenter's stance, not the quote).
4. Emoji count as expression (e.g. 🤡 directed at author → mockery).
5. If text is too short/ambiguous to judge a dimension, leave the cell empty
   (do not guess 0).
6. Do not discuss items with the other coder until both sheets are complete.

## Deliverable

Each coder returns their completed `coder_sheet.csv` (rename with initials).
Analysis: Krippendorff's alpha (coder1 × coder2 × LLM) per dimension;
dimensions with alpha ≥ 0.667 pass for publication use.
