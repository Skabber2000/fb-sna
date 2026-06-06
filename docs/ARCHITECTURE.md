# Architecture

## Design principles

1. **Scrape-once / parse-many.** The browser layer does the minimum — navigate,
   expand, save raw HTML. *All* structured extraction is offline on saved HTML.
   Benefits: minimal account exposure, free re-parsing when selectors are fixed,
   and clean separation of fragile (live) vs. stable (offline) code.
2. **Resumable campaigns.** Long captures run as self-chaining shell loops that
   skip already-done work (by URL-hash slug or a done-list), survive crashes/sleep,
   and stop on a real stall.
3. **Pseudonymous by default.** People are keyed by a salted hash of their display
   name. Real names live only in local, gitignored files.
4. **One report.** Every analysis axis renders into a single self-contained
   `data/report.html`.

## Data flow

```
                        ┌─────────── fb_capture (live browser, headless) ───────────┐
 FB profile ──login──▶  browse --discover ─▶ post_urls.txt
                        browse --capture   ─▶ data/raw_html/*.html        (comments)
                        reactions --capture─▶ data/reactions_html/*.html  (reactors)
                        profiles --capture ─▶ data/profile_html/*.html    (About)
                        browse --friends   ─▶ friends.csv                 (optional)
                        └───────────────────────────────────────────────────────────┘
                                              │ (raw HTML on disk)
                        ┌─────────── offline parse (no network) ───────────┐
 parse_html  ─▶ comments.csv         (aria-label driven: author, parent, text, lang, reactions)
 reactions --parse ─▶ reactions.csv  (reactor identities, 100% reliable slugs)
 profiles --parse  ─▶ profiles.csv   (work / education / location)
                        └───────────────────────────────────────────────────┘
                                              │
                        ┌─────────── analysis ───────────┐
 build_graph ─▶ graph_coengage.graphml (Newman-weighted), graph_reply.graphml, nodes.csv
 analyze     ─▶ nodes_analyzed.csv  (Louvain communities, betweenness, Guimerà-Amaral
                                     roles, behaviour k-means, + profile + discourse merges)
 discourse   ─▶ discourse_comments.csv → discourse_users.csv  (Claude Haiku 4.5)
 characterize─▶ community_profiles.csv (Claude Sonnet 4.6 cluster labels)
 viz_intersections ─▶ figures/community_graph.png
 report      ─▶ report.html + figures/network.png
                        └─────────────────────────────────┘
```

## Modules

### Capture (`fb_capture/`)
| Module | Role |
|---|---|
| `browse.py` | login · discover post URLs (deep-scroll, checkpointed) · capture+expand comments · friends list. Persistent browser profile = reuses login. |
| `parse_html.py` | post HTML → `comments.csv`. **aria-label-driven** extraction (`Comment by X …` / `Reply by X to Y's comment …`) — robust to FB's obfuscated class names. |
| `reactions.py` | open each post's reaction modal, save → parse reactor identities. |
| `profiles.py` | visit a ranked target list's public *About* pages → work/education/location. |

### Analysis (`analysis/`)
| Module | Role |
|---|---|
| `build_graph.py` | bipartite engagement → **co-engagement projection P** (Newman 1/(n−1) weighting) + **reply graph R**; node attribute table. Owner excluded from P. |
| `analyze.py` | Louvain communities + modularity; betweenness (on R); Guimerà-Amaral within-module z × participation → connector-hub roles; behaviour k-means; merges profiles + discourse. |
| `discourse.py` | per-comment LLM scoring (politeness/constructiveness/insight/civility/stance + EN gloss); aggregate to per-user profile. |
| `characterize.py` | per-community LLM synthesis of a label + description from member glosses + occupations. |
| `viz_intersections.py` | decluttered inter-community figure (`--mode community` / `node`). |
| `report.py` | assembles the HTML report + light-theme network figure. |

### Orchestration
`run_capture_campaign.sh`, `run_reactions_campaign.sh`, `run_profiles_campaign.sh`
— self-chaining batch loops (resume, stall-guard).

## Graph model

- **Co-engagement P** (undirected): users linked if they engage the same post;
  edge weight Σ 1/(n_p−1) over shared posts (Newman collaboration weighting stops
  viral posts forming a hairball). Drives community detection.
- **Reply graph R** (directed): edge author→parent_author. Drives betweenness /
  brokerage (truer interaction signal than co-engagement).
- **Node key**: `u_<sha256(salt:displayname)[:16]>`. Consistent across comments and
  reactions so the same person merges into one node.

## Key technical decisions

- **Headless Chromium** for unattended runs (immune to screen-off; only full
  system sleep wedges it). `caffeinate -dimsu` prevents display sleep.
- **Slug reliability**: profile slugs are taken only from reactions (100% reliable)
  and top-level comments (93%); reply-comment DOM embeds the *parent's* profile so
  reply slugs (58%) are discarded. See [PROJECT_LOG.md](PROJECT_LOG.md).
- **Claude model split**: Haiku 4.5 for high-volume per-comment scoring (cheap,
  fast, multilingual); Sonnet 4.6 for the 10 community-synthesis calls (quality).
