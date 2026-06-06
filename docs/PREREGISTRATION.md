# Pre-Registration: Confirmatory Re-Analysis After Human Validation

**Study:** FB-SNA — multilayer psychographic analysis of a wartime Facebook
audience (papers P1/P2/P3, preprints June 2026)
**Author:** Eugene Nayshtetik (independent researcher)
**Status:** DRAFT for OSF registration. To be registered BEFORE the human
coders return their sheets. Date drafted: 2026-06-06.

## 1. What is already known (and is NOT being re-tested exploratorily)

All results in the three preprints were produced before this registration
and are labeled preliminary. This document pre-specifies the CONFIRMATORY
analysis that will run once, after human validation data arrives, with no
analyst degrees of freedom.

## 2. Pending data

Two bilingual (UK/RU) coders independently code the same 503-comment
stratified sample (language x irony x author-affect strata; floor 4/stratum;
drawn with seed 42) on 7 dimensions: aff, akind, ang, iro, cnt, evid, ogh
per `docs/CODING_MANUAL.md`. Coders are blind to LLM scores and to each
other.

## 3. Pre-specified hypotheses

- H1 (instrument validity): for each of the 7 dimensions, Krippendorff's
  alpha over (coder1, coder2, LLM) >= 0.667.
- H2 (no language bias): for aff, ang, ogh — the LLM-minus-human-mean
  difference does not differ between UK and RU comments by more than 0.25
  scale points (TOST equivalence, alpha = .05).
- H3 (headline robustness): re-estimating reply-graph assortativity for
  civility-adjacent dims using HUMAN scores on the subsample's users does
  not flip the sign of the tone-ideology block difference.

## 4. Pre-specified decision rules

| Outcome | Action |
|---|---|
| H1 holds for a dimension | Remove "preliminary" qualifier for claims resting on it |
| H1 fails (alpha < 0.667) | Claims resting on that dimension are withdrawn or re-stated as unvalidated in a revision; no rubric re-tuning on this sample |
| H2 fails for a dimension | Per-language correction published; affected RU-stratum results flagged in all three papers |
| H3 sign flips | P2's central claim is retracted from the preprint |

## 5. Pre-specified analysis code

`analysis/validate_human.py` (to be committed BEFORE data arrival) computes:
Krippendorff alpha (ordinal) per dimension; per-language LLM-human bias with
TOST; the H3 re-estimate. No other analyses of the coder data will be
reported as confirmatory. Anything else is labeled exploratory.

## 6. Blinding & integrity

- The coder sample and answer key were frozen 2026-06-06
  (`data/validation/`), before this registration.
- The author does not code; coders do not see LLM scores.
- Raw coder sheets will be released (de-identified) with the revision.
