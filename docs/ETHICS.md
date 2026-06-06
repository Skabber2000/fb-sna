# Ethics, ToS & OPSEC

## Scope of consent
This project analyzes **the owner's own audience** on **the owner's own posts**,
from **the owner's own logged-in session**, for the owner's own understanding. The
owner explicitly authorized the browser-automation approach after being shown the
risks (twice). It is not a tool for analyzing third parties' audiences.

## Terms of Service — honest position
- **First-party content reading** (comments/reactions on your own posts) and
  reading **public** profile About pages is what a logged-in user can see manually.
- **Automating** that collection nonetheless **violates Facebook's ToS** (automated
  data collection). This is a ToS matter, not illegality, and carries **account
  risk** (checkpoint / temporary lock / ban). Profile-visiting is the activity FB
  detects most aggressively.
- Mitigations: headless single session, no parallelism, human-paced delays
  (15–55 s), per-run caps, conservative profile-visit gaps, and stall-guards that
  stop on the first sign of a checkpoint.

## What was NOT done
- No third-party scraping beyond the owner's own audience.
- No Graph API abuse (the API genuinely cannot serve this for a personal profile).
- No mass profiling of unrelated people — enrichment was limited to **engaged**
  members with a reliable profile slug.

## Privacy
- **Pseudonymization at the keying layer.** Every person is a salted hash
  (`u_<sha256(salt:name)[:16]>`). Analysis files key on the pseudonym.
- Real names appear in working CSVs (for the owner's own use) but the canonical
  re-identification key is `id_map.csv`, which is **gitignored** and must stay local.
- **No public named scorecards.** Discourse scores (politeness, "insight", civility)
  are sensitive; report them as aggregates / pseudonymous ranks, never as a
  published dossier of named individuals. The owner is defense-adjacent — a
  doxxable map of named people is explicitly out of scope.
- **GDPR sensitivity.** Much of the audience is EU (Ukraine + diaspora). Aggregate
  analysis of engagement on one's own content for personal optimization is the
  defensible use; named individual profiling is the risk zone — stay aggregate.

## Data handling
- All of `data/` is gitignored (raw HTML, CSVs, the browser profile, the salt,
  `id_map.csv`). ~26 GB local only.
- API keys live in `.env` (gitignored), loaded via `python-dotenv`. Never printed to
  logs or chat. If a key leaks, rotate immediately (providers auto-disable on leak).

## Recommended retention
- Keep derived aggregates (`nodes_analyzed.csv`, `community_profiles.csv`, the
  report). Consider deleting the 26 GB of raw HTML and `profile_html/` once analysis
  is final, and the `id_map.csv` if re-identification is not needed.
