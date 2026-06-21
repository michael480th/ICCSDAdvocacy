# Research note — the SAVE bonds and SEC bond-disclosure exposure

**Status:** INTERNAL research file. Compiled June 2026.
**Owner direction:** do NOT over-emphasize the SEC / fraud angle in the published narrative. It could be
perceived as a threat and would undermine the piece's credibility. This analysis stays in the research notes
for the owner's own understanding (e.g., oversight-committee work). It is **not** featured in the public story,
and the narrative makes no SEC claim. The plain fact that the audits were late is already in the story, stated
factually and without any securities-law framing.

**Question (from project owner):** the 2023 $71M SAVE issue happened while the books were a mess. Could there
be misstatements in that issuance, and could it get the district in trouble (as it did a Texas district)?

**Short answer:** yes, on two distinct fronts, with different levels of certainty.
1. **Continuing-disclosure failures are documented and concrete.** The district's own SEC Rule 15c2-12
   filings show it failed to deliver audited financials on time and broke its own written 90-day commitment.
2. **A primary-offering antifraud question is real but not established.** Whether the June 2023 official
   statement misrepresented or omitted the known deterioration is a question only the offering documents can
   answer. The SEC has charged a school district for exactly this.

---

## 1. The precedent: SEC v. Crosby ISD (press release 2022-43, March 16 2022)
- The SEC charged **Crosby Independent School District (TX), its former CFO (Carla Merka), and its auditor**
  with fraud in a **January 2018 $20M bond sale**.
- The district **failed to report $11.7M in payroll and construction liabilities and falsely reported $5.4M
  in general fund reserves** in its audited FY2017 statements, then **knowingly included those statements in
  the offering documents**.
- **Seven months after the sale**, Crosby disclosed a **negative general fund balance**; ratings were cut the
  next month.
- Settlement: penalty and officer ban for the CFO; the **auditor was barred from practicing before the SEC
  for three years**.
- Why it matters here: it establishes that the SEC will pursue a school district, its finance chief, and its
  auditor for material misstatements about financial condition in bond offering documents.
- Source: https://www.sec.gov/newsroom/press-releases/2022-43

## 2. ICCSD primary offering: the June 2023 $71M SAVE bonds (the open question)
- The district issued **$71,470,000 of Sales Tax Revenue Bonds on June 29 2023** (partly to refund 2015
  bonds). [FY2024 audit, Note 5]
- At that moment, by the **later audit's own account**, the books were unreliable: bank reconciliations not
  done properly for about three years; the FY2023 close not completed until December 2024; the FY2023 audit
  ultimately carried a material weakness for financial statements that "required significant revisions." [FY24
  audit findings; corrective action plan Nov 2023]
- **What we cannot determine from here:** the contents of the June 2023 official statement, and what
  management represented vs. what it knew. That is exactly the comparison the Crosby case turned on, and the
  comparison a forensic audit or the SEC would make. **Do not assert misstatements occurred. Flag the risk.**

## 3. ICCSD continuing disclosure: the documented failures (Rule 15c2-12)
Rule 15c2-12 requires bond issuers to keep providing **annual financial and operating data, audited financial
statements, and notices of certain events (including rating changes) and of any failure to provide required
information**. A new official statement must also disclose any failure, in the prior five years, to comply
with these commitments. The SEC's MCDC initiative specifically targeted inaccurate statements about prior
compliance.

The district's own filings (in the repo at `Annual Financial Report SEC 15c2-12/`) show it, in its own words.
Lean on these documents, not on news characterizations, for anything stated about disclosure.

- **FY2023 report, filed Jan 24 2024 (verbatim):** "The District's Annual Comprehensive Financial Report for
  the Fiscal Year ended June 30, 2023, **has not been finalized as of the date of this submission**. The
  District's June 30, 2023 Unaudited Financial Statements have been filed with the Municipal Securities
  Rulemaking Board and the District **will provide the June 30, 2023 Annual Comprehensive Financial Report
  within 90 days** of the date of this submission as a separate document." The audited FY2023 ACFR did not
  arrive until **August 2025**, more than a year past the district's own written 90-day commitment.
- **FY2024 report, filed Jan 23 2025:** again states the ACFR "has not been finalized"; the FY2024 ACFR did
  not arrive until **June 2026**. (Note the language softened from a "90 day" promise to "as soon as it is
  available" — they stopped committing to a date.)
- **Material event:** Moody's **withdrew the district's rating in October 2024**. A rating change is a
  reportable event under 15c2-12, requiring prompt notice (generally within 10 business days). Whether the
  notice was filed needs an EMMA check (job 7).

**Net:** the late audited financials are a documented breach of the district's continuing-disclosure
undertakings, and the broken 90-day promise is in writing in the district's own filing.

## 4. How to frame it in the narrative
- **Safe to state:** the continuing-disclosure failures (the district's own filings prove the late audits and
  the broken 90-day commitment) and the Crosby precedent (public SEC action).
- **Frame as an open question, not an allegation:** whether the June 2023 official statement misrepresented
  the district's condition. The forensic audit and any regulator can compare the offering documents to what
  management knew.
- The narrative section "An open question worth watching" does this. It is the most legally sensitive content
  in the piece. Flagged in `story-judgment-calls.md` for owner review.

## Sources
- SEC press release 2022-43 (Crosby ISD): https://www.sec.gov/newsroom/press-releases/2022-43
- SEC Rule 15c2-12 overview (continuing disclosure; prior-compliance disclosure requirement): NABL,
  https://www.nabl.org/bond-basics/15c2-12/ ; SEC MCDC initiative,
  https://www.sec.gov/divisions/enforce/municipalities-continuing-disclosure-cooperation-initiative.shtml
- ICCSD continuing-disclosure filings: repo folder `Annual Financial Report SEC 15c2-12/` (FY2021-FY2025).
- ICCSD FY2024 audit, Note 5 (the June 29 2023 $71.47M SAVE issuance) and Schedule of Findings.
