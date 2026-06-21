# research/ — the ICCSD story bundle (self-contained, isolated)

Everything for the long-form narrative **"How Iowa City ran out of room"** lives here, kept separate from the
main benchmarking site (which lives in `scripts/`, `data/`, and the published `*.html` pages at the repo root).

Nothing in this folder is linked from the live site. The narrative page itself (`how-it-happened.html` at the
repo root, built by `scripts/build_story.py`) is **not** wired into navigation and stays unpublished until
reviewed and approved.

## What is here
- `MANIFEST.md` — index of every file in this bundle, with provenance.
- `story-build-status.md` — build progress / resume tracker for the narrative.
- `story-judgment-calls.md` — every editorial and sourcing judgment call, for review.
- `board-financial-oversight.md` — research on board financial fluency and the Financial Oversight Committee.
- `subplots-act-contract-warnings.md` — research on the ACT building, the superintendent contract, and the
  community warning letters.
- `jobs/` — six research-job briefs for gaps that need full-access or paywalled sourcing.
- `sources/` — the source material provided in chat (news summaries, community emails, public documents).

## Reproduce the narrative page
```
python3 scripts/build_story.py   # -> how-it-happened.html (repo root)
```
