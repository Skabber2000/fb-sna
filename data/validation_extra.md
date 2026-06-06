# Additional Validation Analyses (2026-06-06)

## A. Edge-bootstrap 95% CIs, reply-graph assortativity
(1000 edge-bootstrap reps; dims as decile ranks)

| dim | point | 95% CI | excludes 0 |
|---|---|---|---|
| civility | 0.111 | [0.051, 0.168] | YES |
| insight | 0.053 | [-0.016, 0.112] | no |
| iro | 0.094 | [0.032, 0.154] | YES |
| cnt | 0.088 | [0.033, 0.145] | YES |
| ang | 0.081 | [0.017, 0.138] | YES |
| cnsp | 0.070 | [0.009, 0.130] | YES |
| wtru | 0.064 | [-0.001, 0.133] | no |
| hawk | 0.021 | [-0.042, 0.086] | no |
| trad | -0.025 | [-0.088, 0.042] | no |
| indv | 0.024 | [-0.034, 0.081] | no |

## B. Split-half robustness of orthogonality
(random post-half -> co-comment graph -> Louvain -> max psych-layer ARI)

- Half 1: 1052 nodes, 18 communities, max |psych ARI| = 0.027
- Half 2: 967 nodes, 14 communities, max |psych ARI| = 0.014
- Cross-half structural ARI (stability): 0.018 on 465 shared users

## C. Drop-one-event jackknife (categories with >=2 windowed events; anger delta)

| category | full | jackknife range | single-event driven |
|---|---|---|---|
| aid-negative | +0.026 | [-0.035, +0.075] | YES |
| attention-shift | +0.069 | [+0.014, +0.084] | YES |
| military-negative | +0.062 | [+0.010, +0.125] | YES |
| military-positive | -0.071 | [-0.129, +0.077] | YES |
| political | +0.140 | [+0.123, +0.159] | no |
| political-negative | +0.247 | [+0.226, +0.414] | no |
| strike-wave | +0.050 | [-0.012, +0.091] | YES |
