# War-Event Mood Join

9460 dated scored comments; 25 events with >= 25 comments in a 7-day window. Values are deltas vs the all-period baseline.

## By event category (n-weighted mean delta)

                      ang    anx    hop    rsg    ent    cnt    iro    aff  n_events  n_comments
category                                                                                        
political-negative  0.247  0.101  0.021  0.015 -0.036  0.243 -0.017 -0.045       2.0       249.0
morale-negative     0.187  0.176  0.031  0.103 -0.092  0.175  0.069 -0.049       1.0        71.0
anniversary         0.154  0.288  0.103  0.053 -0.015  0.049 -0.286  0.440       1.0        60.0
political           0.140 -0.006 -0.036  0.002 -0.079  0.163  0.061 -0.077       3.0       374.0
attention-shift     0.068  0.161 -0.047  0.171 -0.041 -0.114  0.065  0.119       2.0       158.0
military-negative   0.062  0.048 -0.069 -0.013 -0.016 -0.102 -0.082 -0.059       2.0       287.0
strike-wave         0.050  0.000  0.003  0.039 -0.019  0.029  0.037 -0.047       5.0       674.0
aid-negative        0.026  0.016 -0.022  0.093 -0.024  0.049 -0.008 -0.033       3.0       498.0
military-positive  -0.071 -0.010 -0.055 -0.088  0.006  0.063  0.155 -0.031       3.0       304.0
escalation         -0.108 -0.104 -0.042 -0.037 -0.045 -0.098  0.004  0.268       1.0        29.0
political-positive -0.374 -0.056  0.609 -0.032  0.444 -0.224 -0.364  1.305       1.0        76.0
aid-positive       -0.462 -0.123 -0.114 -0.259 -0.149 -0.262  0.169 -0.099       1.0        45.0

## Strongest single-event mood responses

      date                                                        event           category   n    ang    anx    hop    rsg    aff
2024-06-26                    EU accession negotiations formally opened political-positive  76 -0.374 -0.056  0.609 -0.032  1.305
2024-04-20                             US House passes $61B aid package       aid-positive  45 -0.462 -0.123 -0.114 -0.259 -0.099
2024-11-21                               Oreshnik IRBM strike on Dnipro        strike-wave  57  0.201  0.391  0.065  0.208 -0.077
2025-11-29 Zelensky chief of staff Yermak dismissed amid corruption pro political-negative  28  0.414 -0.203  0.034 -0.125 -0.148
2026-03-25 ~40% of Russian oil export capacity halted after drone strik  military-positive 160 -0.204 -0.221 -0.087 -0.222  0.036
2026-01-15 Peak winter strike campaign; Kyiv without power ~half of eac        strike-wave  79 -0.261  0.135  0.085  0.172  0.050
2024-02-24                     Two-year full-scale invasion anniversary        anniversary  60  0.154  0.288  0.103  0.053  0.440
2024-11-05                          Trump wins US presidential election    attention-shift 123  0.084  0.240 -0.042  0.181  0.126
2025-03-11         Jeddah talks; 30-day ceasefire proposal; aid resumes          political  81  0.172 -0.123 -0.057 -0.187 -0.484
2023-11-01                 Zaluzhnyi "stalemate" essay in The Economist    morale-negative  71  0.187  0.176  0.031  0.103 -0.049

## Caveats
- Comment dates are post-anchored (day grain); selection runs through what the OWNER posted after events - this measures the audience's response conditional on his coverage.
- Deltas confound event effect with topic effect (events trigger topical posts which attract their own registers).
