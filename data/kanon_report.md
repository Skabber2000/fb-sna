# k-Anonymity Scan (Phase 0a)

Users: 2280. Carrying >=1 sensitive inferred label: 391 (17%).

Sensitive-label prevalence:
- hostile_political: 154
- outgroup_hostile: 66
- distress: 100
- lgbtq_any: 5
- high_conspiracy: 50
- author_hostile: 54
- ru_language: 134

## Re-identification exposure by adversary strength

                   QI set  users_w_QI  k1_unique  k1_AND_sensitive  k_le_5
minimal (city+gender+age)        1203        248                13     382
     typical (+education)        1206        753                60     818
           strong (+work)        1207        828                62     884
     max (+location+lang)        1211        874                70     941

## Reading
- k=1 = unique combination of public profile facts; an adversary
  who knows those facts re-identifies the row with certainty.
- k1_AND_sensitive = unique AND carrying a harmful inferred label
  (hostile-political / outgroup / distress / LGBTQ / conspiracy /
  author-hostile / RU-language). These rows are the publication
  and leak risk. Mitigations: suppress work/education in any
  shared table, coarsen city to oblast, never release row-level
  psychographics joined to profile fields.