# FB-SNA De-identified Release Dataset

Built from the private dataset on 2026-06-06.

## Removed
- All names, profile fields (work, education, location, city), profile refs, avatars, raw comment/post text.
- Original pseudonyms replaced by fresh random ids; the mapping was generated in memory and never written to disk (one-way).

## Tiers
- `users.csv` - behavioral + non-sensitive expressive dims per user.
- `comments.csv` - per-comment scores (no text), month grain.
- `communities.csv` - sensitive dims (worldview, wellbeing, affect, avatar) at community level only, cells with n<10 suppressed.
