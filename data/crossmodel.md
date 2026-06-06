# Cross-Model Convergent Validity (audit item 4)

Same 200-comment sample, identical rubrics; instrument A = claude-haiku-4-5 (production scores), instrument B = grok-4.3 (temperature 0). Convergence = Pearson r between instruments.

## Pass A

dim   n  pearson_r   mae  exact  within1
ang 200      0.709 0.430  0.675    0.895
iro 200      0.768 0.375  0.685    0.945
hop 200      0.757 0.140  0.880    0.980
rsg 200      0.669 0.225  0.815    0.965
ent 200      0.806 0.140  0.870    0.990
anx 200      0.706 0.215  0.830    0.960
cnt 200      0.684 0.520  0.595    0.895
aff 200      0.708 0.340  0.750    0.915
dis 200      0.481 0.095  0.920    0.985
exh 200      0.660 0.065  0.940    0.995
rsl 200      0.674 0.160  0.855    0.985
frm 200      0.577 0.665  0.430    0.915
hum 200      0.743 0.270  0.755    0.975
prf 200      0.552 0.080  0.925    0.995

## Pass B

 dim   n  pearson_r   mae  exact  within1
care 200      0.363 0.460  0.720    0.845
fair 200      0.395 0.490  0.650    0.870
loya 200      0.618 0.280  0.770    0.950
auth 200      0.334 0.230  0.815    0.960
libe 200      0.279 0.365  0.720    0.920
trad 200      0.459 0.100  0.915    0.990
sexp 200      0.389 0.255  0.760    0.985
indv 200      0.345 0.340  0.685    0.975
scfr 200      0.195 0.365  0.670    0.970
evid 200      0.643 0.350  0.685    0.965
cnsp 200      0.692 0.150  0.875    0.975
dogm 200      0.532 0.655  0.445    0.905
itru 200      0.525 0.150  0.860    0.990
wtru 200      0.715 0.130  0.880    0.990
hawk 200      0.554 0.155  0.880    0.965
 ogh 200      0.574 0.155  0.875    0.970
lgbt 200      0.709 0.005  0.995    1.000
gtrd 200      0.721 0.030  0.970    1.000
 sxm 200      0.561 0.025  0.980    0.995

## Reading
- r >= 0.6 cross-model: construct robust to model family.
- r 0.4-0.6: model-sensitive; rely on human validation.
- r < 0.4: likely instrument artifact; flag the dimension.

## Pass DISCOURSE (incl. headline civility)

             dim   n  pearson_r   mae  exact  within1
      politeness 199      0.599 0.784  0.352    0.884
constructiveness 199      0.776 0.513  0.518    0.970
         insight 199      0.749 0.497  0.558    0.945
        civility 199      0.631 0.638  0.467    0.905
          stance 198      0.701 0.510  0.545    0.949
