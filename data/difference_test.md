# Tone vs Ideology: direct difference tests (audit item 1)

Reply graph; decile ranks; 2000 edge-bootstrap reps.

## A. Pairwise differences (tone - ideology)

| tone dim | ideo dim | diff | 95% CI | excludes 0 |
|---|---|---|---|---|
| civility (0.111) | hawk (0.021) | 0.090 | [0.005, 0.174] | YES |
| civility (0.111) | trad (-0.025) | 0.136 | [0.048, 0.224] | YES |
| civility (0.111) | indv (0.024) | 0.087 | [0.013, 0.159] | YES |
| iro (0.094) | hawk (0.021) | 0.073 | [-0.018, 0.163] | no |
| iro (0.094) | trad (-0.025) | 0.119 | [0.031, 0.208] | YES |
| iro (0.094) | indv (0.024) | 0.070 | [-0.014, 0.152] | no |
| cnt (0.088) | hawk (0.021) | 0.067 | [-0.019, 0.156] | no |
| cnt (0.088) | trad (-0.025) | 0.114 | [0.030, 0.201] | YES |
| cnt (0.088) | indv (0.024) | 0.065 | [-0.007, 0.139] | no |
| ang (0.081) | hawk (0.021) | 0.060 | [-0.022, 0.147] | no |
| ang (0.081) | trad (-0.025) | 0.106 | [0.023, 0.194] | YES |
| ang (0.081) | indv (0.024) | 0.058 | [-0.016, 0.134] | no |
| cnsp (0.070) | hawk (0.021) | 0.049 | [-0.033, 0.134] | no |
| cnsp (0.070) | trad (-0.025) | 0.095 | [0.008, 0.187] | YES |
| cnsp (0.070) | indv (0.024) | 0.046 | [-0.028, 0.126] | no |

**Pooled blocks:** mean tone assortativity 0.089 vs mean ideology 0.006; difference 0.082, 95% CI [0.035, 0.131] -> EXCLUDES zero.
Pairwise: 7/15 tone-ideology pairs exclude zero.

## B. Disattenuation (audit item 2)

corrected = observed / per-comment test-retest r (upper-bound correction; user-mean reliability >= per-comment).

| dim | block | observed | reliability | corrected |
|---|---|---|---|---|
| civility | tone | 0.111 | 0.754 | 0.147 |
| iro | tone | 0.094 | 0.759 | 0.124 |
| cnt | tone | 0.088 | 0.793 | 0.111 |
| ang | tone | 0.081 | 0.775 | 0.105 |
| cnsp | tone | 0.070 | 0.791 | 0.088 |
| hawk | ideology | 0.021 | 0.659 | 0.032 |
| trad | ideology | -0.025 | 0.731 | -0.035 |
| indv | ideology | 0.024 | 0.428 | 0.055 |

Corrected block means: tone 0.115 vs ideology 0.017. The contrast SURVIVES disattenuation; differential reliability does not explain it.

## C. Benjamini-Hochberg FDR across all 52 dim x graph tests (audit item 5)

21 survive FDR 0.05:

   graph               dim    assort          z     p
coengage               aff  0.034913   6.052378 0.000
coengage              dogm  0.034027   5.735116 0.000
coengage              evid  0.024041   4.693275 0.000
coengage           insight  0.020846   4.162560 0.000
coengage               cnt  0.022681   4.009145 0.000
coengage               ang  0.021637   3.738299 0.000
coengage               hum  0.018470   3.355205 0.000
coengage  constructiveness  0.014849   3.124125 0.000
coengage               ogh  0.013861   2.877541 0.000
coengage           ga_role -0.070578 -15.673677 0.000
   reply              cnsp  0.069951   3.150466 0.000
   reply               iro  0.093914   3.052756 0.000
coengage behaviour_cluster -0.058531 -10.354622 0.000
   reply               cnt  0.088224   2.625918 0.005
   reply          civility  0.110885   3.178687 0.005
   reply              wtru  0.064265   2.447476 0.005
   reply               ang  0.081083   2.626649 0.010
   reply               ogh  0.062607   2.402843 0.015
   reply           insight  0.053345   2.115093 0.015
coengage     dominant_lang  0.006357   2.314747 0.020
   reply               hum  0.075305   2.547182 0.020
