# Story build status (resume tracker)

**What this is.** A long-form scrollable narrative, "How Iowa City ran out of room," built by
`scripts/build_story.py` into `how-it-happened.html`, wired as a new top-nav door. Written in Mike's voice
(see `mike_voice_profile_long.md`): no em dashes, front-end bolding, lead with the so-what, 12-20 word
sentences, calm and factual, the district at the center, numbered footnotes. Charts not photos.

**How to resume.** Run `python3 scripts/build_story.py` to regenerate the page from current content. Each
section lives in its own function in the script. Add/finish sections, commit, update the checklist below.
All content and citations live in the script, so nothing is lost between sessions as long as it is committed.

## Section checklist
- [x] Build harness: data, CSS, scroll JS, citation system, chart helpers, assembly
- [x] Chart: hero days-of-cash (2015-2026)
- [x] Chart: cushions small-multiples (UAB / solvency / days)
- [x] Chart: debt build-up (GO + SAVE, FY20-24)
- [x] 0. The loan nobody voted for (Jan 2026 lede)
- [x] 1. A district in good shape (2015-17 + Finger 2019 health report)
- [x] 2. The biggest bet in the state (2017 bond + ACT building + capital kept growing)
- [x] 3. How Iowa school money actually works (decoder)
- [x] 4. The slow bleed (2018-22 operating squeeze)
- [x] 5. The warnings, and the committee built to catch them (FOC formed Nov 2023, went dark)
- [x] 6. Empty at the same time (FY25 fund-drawdown dumbbell)
- [x] 7. Borrowing from itself (FY24 interfund $38.2M, Finding 2024-008; interfund chart)
- [x] 8. Who was watching (staff collapse + toothless contract + FOC dark)
- [x] 9. They were told (community warnings 2022-2025)
- [x] 10. The reckoning (2026 cascade)
- [x] 11. Why it happened, what is unresolved
- [x] 12. What to watch next + full sources
- [ ] HOLD (owner must approve first): wire into `_nav.py` as a primary door and run `scripts/resync_nav.py`.
      Until then the page exists in the repo but is NOT linked from any nav, so it is unpublished/unlisted.
- [x] Voice/em-dash check passed (0 em dashes in rendered prose; all 27 footnotes resolve)

## Build complete (first full draft)
All 13 sections and 5 chart types render. 27 sourced footnotes. See `story-judgment-calls.md` for decisions
and refinements to review together. Optional additions noted there (total-pool sparkline for section 6, a 2026
events ribbon for section 10).

## Sourcing notes
- Two beats stay attributed/hedged until research jobs return: ACT conflict-of-interest (job 5) and
  "contract is unusual vs peers" (job 6). Do not assert either as fact yet.
- Off-record FOC chairing detail stays out of the public page; cite the video record + Lingo's quote.
- FY25 (CAR) and FY26 (PFM/news) are unaudited and must be labeled as such.
