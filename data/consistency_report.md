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

## Pass DISCOURSE (v1 dims, re-tested 2026-06-06)

             dim   n  pearson_r   mae  exact  within1
      politeness 199      0.740 0.442  0.588     0.97
constructiveness 199      0.842 0.357  0.653     0.99
         insight 199      0.824 0.271  0.729     1.00
        civility 199      0.754 0.402  0.628     0.97
          stance 198      0.796 0.374  0.657     0.97

These are the dims behind the reply-homophily headline (P2); re-tested on the same 200-comment sample with the identical v1 rubric.

## Ordinal reliability (Spearman rho, quadratic-weighted kappa) — added 2026-06-06

### Pass A

dim   n  spearman  qw_kappa
ang 200     0.708     0.775
iro 200     0.692     0.758
hop 200     0.671     0.758
rsg 199     0.701     0.757
ent 200     0.817     0.855
anx 200     0.759     0.816
cnt 200     0.760     0.793
aff 200     0.607     0.709
dis 200     0.721     0.756
exh 200     0.370     0.530
rsl 200     0.710     0.790
frm 200     0.652     0.652
hum 200     0.734     0.747
prf 200     0.661     0.645

### Pass B

 dim   n  spearman  qw_kappa
care 200     0.755     0.730
fair 200     0.631     0.637
loya 200     0.708     0.748
auth 200     0.391     0.520
libe 200     0.485     0.429
trad 200     0.646     0.710
sexp 200     0.594     0.589
indv 200     0.407     0.427
scfr 200     0.054     0.045
evid 200     0.718     0.713
cnsp 200     0.815     0.789
dogm 200     0.712     0.723
itru 200     0.558     0.589
wtru 200     0.746     0.767
hawk 200     0.661     0.657
 ogh 200     0.710     0.775
lgbt 200     0.000     0.000
gtrd 200     0.490     0.520
 sxm 200     0.663     0.659

### Pass DISCOURSE

             dim   n  spearman  qw_kappa
      politeness 199     0.722     0.729
constructiveness 199     0.842     0.838
         insight 199     0.808     0.824
        civility 199     0.733     0.744
          stance 198     0.760     0.791


Test-retest Pearson r stratified by comment language; RU stratum topped up to ~150.

## UK — pass A (n=169)

dim   n  pearson_r   mae  exact  within1
ang 169      0.757 0.343  0.704    0.953
iro 169      0.764 0.391  0.657    0.953
cnt 169      0.783 0.337  0.698    0.964
aff 169      0.674 0.367  0.728    0.905
hop 169      0.773 0.154  0.864    0.982
rsg 168      0.774 0.196  0.815    0.988

## UK — pass B (n=169)

 dim   n  pearson_r   mae  exact  within1
cnsp 169      0.738 0.148  0.858    0.994
 ogh 169      0.780 0.124  0.882    0.994
evid 169      0.717 0.284  0.728    0.994
wtru 169      0.782 0.136  0.864    1.000
hawk 169      0.667 0.178  0.840    0.982
trad 169      0.725 0.118  0.893    0.988

## RU — pass A (n=150)

dim   n  pearson_r   mae  exact  within1
ang 150      0.843 0.273  0.767    0.960
iro 150      0.797 0.427  0.647    0.933
cnt 150      0.737 0.373  0.707    0.927
aff 150      0.783 0.293  0.773    0.933
hop 150      0.655 0.107  0.893    1.000
rsg 148      0.746 0.209  0.818    0.980

## RU — pass B (n=150)

 dim   n  pearson_r   mae  exact  within1
cnsp 150      0.859 0.073  0.933    0.993
 ogh 150      0.653 0.200  0.840    0.960
evid 150      0.724 0.240  0.773    0.987
wtru 150      0.677 0.140  0.880    0.980
hawk 150      0.576 0.207  0.833    0.960
trad 150      0.688 0.080  0.920    1.000
