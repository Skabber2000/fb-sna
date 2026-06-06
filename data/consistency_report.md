# LLM Self-Consistency Report (Phase 0d)

n = 200 comments re-scored with identical rubric/model.
Test-retest reliability of the scoring instrument itself.

## Pass A

dim   n  pearson_r   mae  exact  within1
ang 200      0.775 0.330  0.720    0.950
iro 200      0.759 0.380  0.665    0.955
hop 200      0.759 0.145  0.870    0.985
rsg 199      0.759 0.201  0.814    0.985
ent 200      0.858 0.095  0.910    0.995
anx 200      0.817 0.170  0.845    0.985
cnt 200      0.793 0.320  0.720    0.965
aff 200      0.709 0.375  0.710    0.915
dis 200      0.756 0.075  0.925    1.000
exh 200      0.654 0.080  0.920    1.000
rsl 200      0.791 0.125  0.875    1.000
frm 200      0.652 0.400  0.625    0.975
hum 200      0.753 0.295  0.725    0.980
prf 200      0.646 0.065  0.935    1.000

## Pass B

 dim   n  pearson_r   mae  exact  within1
care 200      0.731 0.285  0.770    0.950
fair 200      0.625 0.360  0.705    0.945
loya 200      0.748 0.230  0.795    0.975
auth 200      0.522 0.240  0.790    0.970
libe 200      0.431 0.355  0.725    0.945
trad 200      0.731 0.100  0.910    0.990
sexp 200      0.592 0.250  0.765    0.985
indv 200      0.428 0.320  0.705    0.980
scfr 200      0.045 0.505  0.640    0.885
evid 200      0.713 0.275  0.740    0.990
cnsp 200      0.791 0.130  0.875    0.995
dogm 200      0.730 0.415  0.610    0.975
itru 200      0.598 0.205  0.800    0.995
wtru 200      0.770 0.135  0.865    1.000
hawk 200      0.659 0.160  0.860    0.980
 ogh 200      0.776 0.125  0.880    0.995
lgbt 200      0.000 0.015  0.990    0.995
gtrd 200      0.521 0.045  0.960    0.995
 sxm 200      0.663 0.015  0.985    1.000

## Interpretation
- r >= 0.7 and within1 >= 0.9: dimension is reliable as scored.
- r 0.4-0.7: usable with shrinkage/aggregation, flag in methods.
- r < 0.4: do not base claims on this dimension without human
  validation (Phase 0c) or rubric revision.

## Verdict (2026-06-06)

**Pass the r>=0.7 gate (claim-bearing, publishable):** ang .775, iro .759,
hop .759, rsg .759, ent .858, anx .817, cnt .793, aff .709, dis .756,
rsl .791, hum .753, care .731, loya .748, trad .731, evid .713, cnsp .791,
wtru .770, ogh .776. Every dimension behind the headline findings
(author-affect, hostility vectors, xenophobia/conspiracy link, epistemic
style, emotional registers) is reliable.

**Usable with aggregation/shrinkage only (r .4-.7):** exh, frm, prf, fair,
auth, sexp, itru, hawk, gtrd, sxm, libe .431, indv .428.

**FAILED -- do not use:** scfr (r=.045, pure noise; drop from all analyses).
lgbt (r=0 from extreme sparsity, 99% zeros): not noise but unmeasurable at
comment level; retire as a layer, keep only as a rare-event flag.

Within-1-point agreement >= .89 everywhere: the instrument never swings
wildly; unreliability is granularity, not direction.
