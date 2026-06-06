# Pipeline — run sequence

All commands from the project root with the venv Python
(`~/.venvs/dev/bin/python`). Everything is **resumable**.

## 0. Setup (once)

```bash
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
#   FB_PAGE_ID         = numeric id (informational)
#   FB_PSEUDONYM_SALT  = python -c "import secrets;print(secrets.token_hex(16))"
#   ANTHROPIC_API_KEY  = for discourse + characterize
python -m fb_capture.browse --login          # manual login: email+password (NOT passkey)
```
> Keep the lid **open** during unattended runs. Headless survives screen-off;
> a full lid-close system sleep wedges the browser (just relaunch the runner —
> nothing is lost; clear `data/.browser_profile/SingletonLock` if locked).

## 1. Discover posts

```bash
python -m fb_capture.browse --discover --max-posts 2000
```
Deep-scrolls the timeline → `data/post_urls.txt` (checkpointed every 3 scrolls).
Filter to own posts if needed (drops tagged/shared):
```bash
python - <<'PY'
from pathlib import Path
p=Path("data/post_urls.txt"); u=[x for x in p.read_text().splitlines() if x.strip()]
p.write_text("\n".join(x for x in u if "/nayshtetik/" in x)+"\n")
PY
```

## 2. Capture comments  →  3. reactions  →  4. profiles

Use the self-chaining runners (loop batches until done):

```bash
./run_capture_campaign.sh     # comments  (~6-7h for ~475 posts)
./run_reactions_campaign.sh   # reactor identities (run after comments parsed once)
python -m fb_capture.profiles --build-targets --top 100000   # rank reliable-slug targets
./run_profiles_campaign.sh    # public About enrichment (HIGH ban-risk; ~17-30h)
```
Single batches (manual / calibration):
```bash
python -m fb_capture.browse    --capture --max-posts 35 --headless
python -m fb_capture.reactions --capture --max 25
python -m fb_capture.profiles  --capture --max 20
```

## 5. Parse (offline, no network)

```bash
python -m fb_capture.parse_html         # → comments.csv, posts.csv
python -m fb_capture.reactions --parse  # → reactions.csv
python -m fb_capture.profiles  --parse  # → profiles.csv
```

## 6. Build graph + analyze

```bash
python -m analysis.build_graph          # → graph_*.graphml, nodes.csv
python -m analysis.analyze              # → nodes_analyzed.csv (communities, bridges, behaviour)
```

## 7. Discourse layer (Claude)

```bash
python -m analysis.discourse            # score all comments → discourse_comments.csv
python -m analysis.discourse --aggregate# → discourse_users.csv + merge into nodes_analyzed
```

## 8. Characterize + report

```bash
python -m analysis.characterize --top 10           # → community_profiles.csv (LLM labels)
python -m analysis.viz_intersections --mode community --min-comm 15 --keep-top 0.7
python -m analysis.report                          # → report.html + figures/network.png
open data/report.html
```

## Re-run after a parser fix

Because raw HTML is saved, fixing a parser never needs re-scraping:
```bash
python -m fb_capture.parse_html && python -m analysis.build_graph \
  && python -m analysis.analyze && python -m analysis.report
```

## Recovery cheatsheet

| Symptom | Fix |
|---|---|
| browser wedged after sleep | `pkill -f fb_capture; rm -f data/.browser_profile/SingletonLock`; relaunch runner |
| campaign "STALLED" | check for FB checkpoint/login in a headed `--login`; then rerun runner |
| display sleeping | `caffeinate -dimsu &` (lid must stay open) |
| profile lock busy | ensure only one capture touches `data/.browser_profile` at a time |
