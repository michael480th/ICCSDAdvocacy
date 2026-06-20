# Story judgment calls and things to refine

A record of every meaningful decision I made building the narrative, plus places I would tighten with you.
Read this first when we review. Compiled overnight, June 2026.

## 0. Follow-up revisions (your live feedback)
- **Removed the voucher / "statewide squeeze" framing from section 11.** You were right that it hands the
  district an excuse the math does not support. The research backs it: Iowa's ESA is enrollment-driven and the
  district actually keeps about $1,205 per resident private-school student it no longer educates, so the net
  voucher cost is small. Against that, the self-inflicted costs are documented and larger ($525K in late-filing
  penalties, unpaid interest on $38M of interfund loans, a $13.5M payroll overrun). Section 11 now makes the
  controllable-cost case and rests it on our own 15-district peer benchmark.
- **Added the "killer" combo chart** (section 2): debt bars with days-of-cash overlaid. Per your IOU point, the
  liquidity line is days of cash, which uses the actual cash line, not the interfund receivables that pad fund
  balance. So it cannot be inflated by the district borrowing from itself.
- **Added a peer chart** (section 11): all 15 large districts on FY2024 spending authority, Iowa City the lone
  low outlier at 1.6% while 14 sit between 9% and 31%. This is the empirical answer to "blame the state."
- **Preempted the "funds are separate" defense** with a callout in section 3: the funds are separate by law, and
  the district mixed them $38M worth without the votes the law requires, so it cannot hide behind the rule it
  broke.
- **Generalized the community-correspondence section (9) to protect the writers.** No dated letters tied to a
  person; it now says qualified community members raised the exact issues at the key moments and were ignored.
  The tax lien is sourced to public reporting, not a private letter.
- **SEC / bond-disclosure exposure: kept INTERNAL, not in the narrative.** Per your direction (it could read as
  a threat), the analysis lives only in `save-bond-sec-disclosure.md`. If it is ever used, it must lean on the
  district's own SEC Rule 15c2-12 filings (e.g., its own written "within 90 days" promise) and cite carefully.
  The narrative states only the plain fact that the audits were late, with no securities-law framing.
- **Extended the debt chart back to 2015** using the audited FY2015-2019 debt already in the project.

## 1. Privacy and exclusion decisions (please confirm)
- **Held the voice profile OUT of the repo.** You said put all the files you gave me in the repo. I did not
  commit `mike_voice_profile_long.md`, because this repo is likely public (it serves a live GitHub Pages site)
  and that document is personal. If the repo is private, or you want it in anyway, say so and I will add it.
- **Held the Moody's and S&P methodology PDFs out.** Third-party copyrighted documents. Not appropriate to
  publish. They are still in the project workspace, just not committed.
- **Did not duplicate the 8.7MB FY2025 CAR PDF** into `research/sources/`; it already lives at
  `CAR/FY2025 Iowa City.pdf`. The manifest points to it.

## 2. Framing decisions where I made a call
- **"Can't be fired" reframed to "no accountability built in, and none used."** The literal claim would fail
  a fact-check: Iowa law and the contract both give the board a May non-renewal window. The defensible version
  is the 2022 community critique (no performance measures, not tied to goals) plus the board renewing him in
  July 2025 and keeping him after the crisis. Section 8 uses that version. **Refine:** if job 6 shows the
  contract is genuinely unusual vs peers, we can sharpen this.
- **ACT conflict-of-interest is NOT in the page yet.** The $8.7M purchase, above the $5.4M assessed value, is
  in (section 2), attributed and sourced. The "seller's CEO was a former board member" claim is held until job
  5 confirms a name and dates. I will not print an unverified conflict allegation about a named person.
- **FOC: corrected mid-build.** An earlier research draft wrongly said no oversight committee existed before
  2026. You corrected it. The page (section 5) now says the committee was formed Nov 2023 and went dark for ~2
  years. The off-record detail (who chaired; Eastham cancelling) is kept OUT of the public page. The citable
  spine is the meeting-video record plus the director's on-camera "couple years" line.
- **Board financial-fluency thread kept light, per your instruction.** The page does not litigate board members'
  resumes. It makes the structural point (staff, committee, and board all failed to catch it) through documented
  facts. The fuller board research sits in `board-financial-oversight.md` for us to decide how far to push.
- **Tone.** Calm and factual, not a hit piece. Section 11 gives the district the fair context (statewide
  special-ed deficits, the voucher squeeze) and states plainly that intent is unresolved pending the forensic
  audit. Your Q10 conviction (a management problem, not a money problem) is present but carried by the facts,
  not by editorializing. **Refine:** tell me if you want it sharper.

## 3. Sourcing decisions
- **"Largest school bond in Iowa history"** is confirmed (the Gazette headline and reporting). Stated as fact.
- **Community emails** are quoted by substance only; senders are redacted in the source files and stay redacted.
- **FY2025 and FY2026 figures are labeled unaudited/projected** everywhere they appear, including a standing
  note near the top of the page.
- **Several citations point to the curated news index, not the original article.** For a finished public piece
  I would upgrade the load-bearing ones to the original outlet URLs (the news files carry those links). Flagged
  as a refinement, not a blocker.

## 4. Data decisions (chart inputs)
- **Chart series are hardcoded in `build_story.py` with provenance comments**, rather than parsed live from the
  CSVs. This is deliberate for a narrative page (robust, self-contained, framing-specific). All values trace to
  the project's audited data, the FY2024 audit, or the FY2025 CAR. If you prefer live CSV reads, I can switch it.
- **Pooled cash falling "~42%, from ~$108M to ~$62M" in FY2025** is computed by summing the FY2025 CAR
  Treasurer's Report by Fund (begin vs end). Unaudited.
- **Interfund chart** shows the General Fund's "due from other funds" (a rounding error, then $29M in FY2024).
  The $38.2M figure in the caption is the district-wide total the audit flagged (Finding 2024-008). I used the
  GF series for the bars because I have it back to 2020; the district-wide total I only have for FY2024.
- **Precision.** Rounded to match the audience and the margin (days to whole numbers, dollars to $0.1M on charts,
  percentages to one decimal). No false precision.
- **The $377,628.90 tax lien** (section 9) comes from the June 2025 community email and corroborates the news
  thread of $525,110 in IRS penalties for late filings. Job 6 will confirm the lien independently.

## 5. Things I would refine with you (not done)
- **Section 6 transition.** The "$108M to $62M" pool figure is strong but appears only in prose. We could add a
  small total-pool sparkline so the 42% drop is visible, not just stated.
- **A 2026 events ribbon** for section 10 (the cascade) would help the reader hold the sequence. I left it as
  prose to avoid overbuilding overnight. Easy to add.
- **The ACT "then sold the old HQ for $3.2M" irony** (bought a bigger admin building for $8.7M going in, sold
  the old one for a fraction coming out) is in the research notes but only lightly in the page. Could be sharper
  if you want it.
- **Headline and dek.** "How Iowa City ran out of room" plays on spending authority (running out of room to
  spend) and the building program. If you want a different title, it is a one-line change.
- **Length.** The piece is ~13 sections. If it reads long, sections 3 (the decoder) and 4 (the slow bleed) could
  merge. I kept them split because the decoder earns its keep for a general reader.

## 6. Open verification (the six job briefs)
None of these block a draft, and each is scoped in `jobs/`. The two that would change wording if they come back
differently: **job 5** (ACT conflict) and **job 6** (contract-is-unusual). The rest firm up dates and add color.
