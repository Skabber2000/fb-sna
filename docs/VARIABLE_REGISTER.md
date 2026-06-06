# Variable Register (Phase 0b)

`nodes_analyzed.csv`: 2281 users x 68 columns. Unclassified: 0.

Release decisions: **keep** = publishable per-user; **aggregate-only** = community/stratum level only, never per-user; **drop** = excluded from any release dataset (identity & PII).

| column             | category            | coverage   | release        |
|:-------------------|:--------------------|:-----------|:---------------|
| user               | profile-PII         | 100%       | drop           |
| n_comments         | observed-behavioral | 100%       | keep           |
| reactions_received | observed-behavioral | 100%       | keep           |
| posts_engaged      | observed-behavioral | 100%       | keep           |
| dominant_lang      | observed-behavioral | 100%       | keep           |
| author_name        | profile-PII         | 100%       | drop           |
| is_owner           | flag                | 100%       | keep           |
| reactions_given    | observed-behavioral | 100%       | keep           |
| engaged_via        | observed-behavioral | 100%       | keep           |
| work               | profile-PII         | 17%        | drop           |
| education          | profile-PII         | 28%        | drop           |
| location           | profile-PII         | 39%        | drop           |
| city               | profile-PII         | 39%        | drop           |
| community          | observed-behavioral | 100%       | keep           |
| betweenness        | observed-behavioral | 100%       | keep           |
| wm_zscore          | observed-behavioral | 100%       | keep           |
| participation      | observed-behavioral | 100%       | keep           |
| ga_role            | observed-behavioral | 100%       | keep           |
| behaviour_cluster  | observed-behavioral | 100%       | keep           |
| politeness         | LLM-discourse       | 61%        | keep           |
| constructiveness   | LLM-discourse       | 61%        | keep           |
| insight            | LLM-discourse       | 61%        | keep           |
| civility           | LLM-discourse       | 61%        | keep           |
| stance             | LLM-discourse       | 61%        | keep           |
| n_scored           | observed-behavioral | 61%        | keep           |
| av_ptype           | avatar-inferred     | 53%        | aggregate-only |
| av_unif            | avatar-inferred     | 53%        | aggregate-only |
| av_uasym           | avatar-inferred     | 53%        | aggregate-only |
| av_grp             | avatar-inferred     | 53%        | aggregate-only |
| av_fml             | avatar-inferred     | 53%        | aggregate-only |
| av_age             | avatar-inferred     | 53%        | aggregate-only |
| av_gnd             | avatar-inferred     | 53%        | aggregate-only |
| av_smil            | avatar-inferred     | 53%        | aggregate-only |
| ang                | LLM-expressive      | 61%        | keep           |
| iro                | LLM-expressive      | 61%        | keep           |
| hop                | LLM-expressive      | 61%        | keep           |
| rsg                | LLM-expressive      | 61%        | keep           |
| ent                | LLM-expressive      | 61%        | keep           |
| anx                | LLM-expressive      | 61%        | keep           |
| cnt                | LLM-expressive      | 61%        | keep           |
| aff                | LLM-sensitive       | 61%        | aggregate-only |
| dis                | LLM-sensitive       | 61%        | aggregate-only |
| exh                | LLM-sensitive       | 61%        | aggregate-only |
| rsl                | LLM-sensitive       | 61%        | aggregate-only |
| frm                | LLM-expressive      | 61%        | keep           |
| hum                | LLM-expressive      | 61%        | keep           |
| prf                | LLM-expressive      | 61%        | keep           |
| n_a                | observed-behavioral | 61%        | keep           |
| care               | LLM-sensitive       | 61%        | aggregate-only |
| fair               | LLM-sensitive       | 61%        | aggregate-only |
| loya               | LLM-sensitive       | 61%        | aggregate-only |
| auth               | LLM-sensitive       | 61%        | aggregate-only |
| libe               | LLM-sensitive       | 61%        | aggregate-only |
| trad               | LLM-sensitive       | 61%        | aggregate-only |
| sexp               | LLM-sensitive       | 61%        | aggregate-only |
| indv               | LLM-sensitive       | 61%        | aggregate-only |
| scfr               | LLM-sensitive       | 61%        | aggregate-only |
| evid               | LLM-sensitive       | 61%        | aggregate-only |
| cnsp               | LLM-sensitive       | 61%        | aggregate-only |
| dogm               | LLM-sensitive       | 61%        | aggregate-only |
| itru               | LLM-sensitive       | 61%        | aggregate-only |
| wtru               | LLM-sensitive       | 61%        | aggregate-only |
| hawk               | LLM-sensitive       | 61%        | aggregate-only |
| ogh                | LLM-sensitive       | 61%        | aggregate-only |
| lgbt               | LLM-sensitive       | 61%        | aggregate-only |
| gtrd               | LLM-sensitive       | 61%        | aggregate-only |
| sxm                | LLM-sensitive       | 61%        | aggregate-only |
| n_b                | observed-behavioral | 61%        | keep           |

## Notes
- `user` is a pseudonym but joins to PII inside the private dataset; treated as PII for release.
- LLM-sensitive dims describe EXPRESSED content, not inner attitudes; even so they are aggregate-only.
- Comment-level tables follow the same map; raw text is excluded from release (searchable -> re-identifying).
