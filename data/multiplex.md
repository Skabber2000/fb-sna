# Multiplex Community Stress-Test

Layers: co-engagement (53786 edges), reply (1157 edges), normalized-union multiplex.

## Structural partitions vs each other (ARI)

                a                 b   ari    n
       co_louvain     reply_louvain 0.011  753
       co_louvain multiplex_louvain 0.199 2278
       co_louvain          original 0.229 2278
    reply_louvain multiplex_louvain 0.014  758
    reply_louvain          original 0.015  755
multiplex_louvain          original 0.247 2280

## Psychographic clusterings vs every structural partition (ARI)

       layer  co_louvain  reply_louvain  multiplex_louvain  original
cl_emotional      -0.000          0.017             -0.001    -0.001
   cl_affect       0.004         -0.002              0.018     0.010
cl_wellbeing      -0.007          0.007             -0.000    -0.000
 cl_register      -0.002          0.025              0.001    -0.001
    cl_moral      -0.012         -0.008             -0.002    -0.004
   cl_values      -0.003          0.003             -0.009    -0.004
cl_epistemic      -0.004          0.004             -0.004    -0.000
cl_political      -0.012          0.021             -0.009    -0.009
 cl_outgroup      -0.002         -0.001              0.001     0.001
cl_discourse      -0.001          0.008              0.001    -0.000
  cl_topical       0.021         -0.007              0.031     0.028

## Verdict
Max |ARI| of any psych layer against any structural partition: **0.031**.
If this stays ~0, the orthogonality result is robust to graph choice (co-engagement vs reply vs multiplex) and is not an artifact of soft co-engagement structure.
