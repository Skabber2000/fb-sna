# Event-Study Significance (placebo permutation)

1000 placebo draws per category; two-sided p vs |delta|; window 7d, min 25 comments; span 2023-10-12..2026-05-20.

## Significant category x emotion effects (p < .05)

          category  n_events dim  delta  p_perm sig
political-positive         1 aff  1.305   0.000 ***
political-positive         1 hop  0.609   0.011   *

## Full table

          category  n_events dim  delta  p_perm sig
      aid-negative         3 ang  0.026   0.862    
      aid-negative         3 anx  0.016   0.895    
      aid-negative         3 hop -0.022   0.704    
      aid-negative         3 rsg  0.093   0.371    
      aid-negative         3 aff -0.033   0.783    
      aid-positive         1 ang -0.462   0.080    
      aid-positive         1 anx -0.123   0.464    
      aid-positive         1 hop -0.114   0.243    
      aid-positive         1 rsg -0.259   0.100    
      aid-positive         1 aff -0.099   0.615    
       anniversary         1 ang  0.154   0.565    
       anniversary         1 anx  0.288   0.072    
       anniversary         1 hop  0.103   0.269    
       anniversary         1 rsg  0.053   0.688    
       anniversary         1 aff  0.440   0.050    
   attention-shift         2 ang  0.069   0.744    
   attention-shift         2 anx  0.161   0.228    
   attention-shift         2 hop -0.047   0.520    
   attention-shift         2 rsg  0.172   0.158    
   attention-shift         2 aff  0.119   0.452    
        escalation         1 ang -0.108   0.689    
        escalation         1 anx -0.104   0.520    
        escalation         1 hop -0.042   0.688    
        escalation         1 rsg -0.037   0.764    
        escalation         1 aff  0.268   0.221    
 military-negative         3 ang  0.062   0.696    
 military-negative         3 anx  0.048   0.651    
 military-negative         3 hop -0.069   0.262    
 military-negative         3 rsg -0.013   0.896    
 military-negative         3 aff -0.060   0.647    
 military-positive         7 ang -0.071   0.484    
 military-positive         7 anx -0.010   0.891    
 military-positive         7 hop -0.055   0.194    
 military-positive         7 rsg -0.089   0.164    
 military-positive         7 aff -0.031   0.697    
   morale-negative         1 ang  0.187   0.470    
   morale-negative         1 anx  0.176   0.284    
   morale-negative         1 hop  0.031   0.740    
   morale-negative         1 rsg  0.103   0.493    
   morale-negative         1 aff -0.049   0.810    
         political         6 ang  0.140   0.211    
         political         6 anx -0.006   0.936    
         political         6 hop -0.036   0.430    
         political         6 rsg  0.002   0.979    
         political         6 aff -0.077   0.434    
political-negative         2 ang  0.247   0.222    
political-negative         2 anx  0.100   0.446    
political-negative         2 hop  0.020   0.794    
political-negative         2 rsg  0.015   0.898    
political-negative         2 aff -0.045   0.744    
political-positive         1 ang -0.374   0.133    
political-positive         1 anx -0.056   0.720    
political-positive         1 hop  0.609   0.011   *
political-positive         1 rsg -0.032   0.820    
political-positive         1 aff  1.305   0.000 ***
       strike-wave         6 ang  0.050   0.665    
       strike-wave         6 anx  0.000   1.000    
       strike-wave         6 hop  0.004   0.939    
       strike-wave         6 rsg  0.039   0.575    
       strike-wave         6 aff -0.047   0.637    

Note: placebo windows inherit the owner-posting selection the same way real windows do, so this tests 'events move mood more than arbitrary dates', not pure causality.
