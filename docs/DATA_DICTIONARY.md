# Data dictionary

All under `data/` (gitignored; ~26 GB, mostly raw HTML). Counts as of 2026-06-05.

## Raw capture (saved HTML)
| Path | Count | Contents |
|---|---|---|
| `raw_html/<slug>.html` (+`.url`) | 493 | full post page with comments expanded |
| `reactions_html/<slug>.html` | 448 | post reaction modal (reactor list) |
| `profile_html/<safeslug>__<section>.html` | 3,669 | public About pages (3 sections × ~1,224 people) |

## Inputs / bookkeeping
| File | Contents |
|---|---|
| `post_urls.txt` / `post_urls_full_inventory.txt` | discovered post permalinks (475 own) |
| `reactions_done.txt`, `enrich_done.txt` | processed-post / processed-profile logs (resume) |
| `enrich_manifest.tsv` | `safeslug ⟶ slug ⟶ display name` (joins enrichment to graph) |
| `enrich_targets.txt` | engagement-ranked profile slugs to enrich |
| `id_map.csv` | pseudonym ⟶ raw id/name (de-pseudonymization key; **guard**) |

## Tables (CSV)

### `comments.csv` — 11,036 rows
`comment_id, post_id, user, author_name, user_ref, ctype, parent_user,
parent_comment_id, created_time, text_original, lang, reactions`
- `user` = display-name pseudonym (node key) · `user_ref` = profile slug (reliable
  only for top-level comments) · `ctype` = comment|reply · `parent_user` = pseudonym
  replied-to · `reactions` = reaction count on that comment · `created_time` =
  relative ("3 d ago").

### `posts.csv` — 493 rows
`post_id, permalink_url, n_comments, n_reactions, message, theme`
(`theme` blank — reserved for topic-labeling step.)

### `reactions.csv` — 2,588 rows
`post_id, user, author_name, user_ref, reaction_type` — one row per (post, reactor).
`user_ref` here is **100% reliable** (modal rows are the reactor's own profile).

### `shares.csv` — 0 rows
No public reshares surfaced (FB exposes few).

### `profiles.csv` — 1,212 rows
`user, user_ref, author_name, work, education, location, bio` — public About fields.

### `nodes.csv` — 2,281 rows
`user, n_comments, reactions_received, posts_engaged, dominant_lang, author_name,
is_owner, reactions_given, engaged_via` (`engaged_via` = comment|reaction_only).

### `nodes_analyzed.csv` — 2,281 rows (the master node table)
nodes.csv + `work, education, location, city` (profile merge) +
`community, betweenness, wm_zscore, participation, ga_role, behaviour_cluster`
(graph analysis) + `politeness, constructiveness, insight, civility, stance,
n_scored` (discourse merge). `ga_role` ∈ connector_hub | provincial_hub | connector
| peripheral.

### `discourse_comments.csv` — 9,611 rows
`comment_id, user, politeness, constructiveness, insight, civility (0-4),
stance (-2..2), gloss` (≤10-word English summary).

### `discourse_users.csv` — 1,398 rows
`user, politeness, constructiveness, insight, civility, stance, n_scored`
(per-user means).

### `community_profiles.csv` — 10 rows
`community, size, label, description` (LLM-synthesized cluster characterizations).

## Graphs
| File | Contents |
|---|---|
| `graph_coengage.graphml` | undirected co-engagement P (2,278 nodes / 53,786 edges) |
| `graph_reply.graphml` | directed reply graph R (758 nodes / 1,612 edges) |

## Outputs
| File | Contents |
|---|---|
| `report.html` | the full self-contained report |
| `figures/network.png` | full co-engagement network (light theme) |
| `figures/community_graph.png` | decluttered community-intersection map |
