# Data files

Structured companions to `../school-district-rating-withdrawals.md`. Every row is
backed by a cited source. Where a source returned HTTP 403 to automated fetching,
the value was taken from corroborating web-search snippets and the confidence column
reflects that. **No district name in these files was invented** — anything that could
not be confirmed is marked `Low` confidence or omitted.

## `confirmed-rating-actions.csv`
Named K-12 districts where a rating agency took an action tied to insufficient/untimely
financial information. Read the `action_type` column carefully — only **Withdrawn** rows
are "lost its rating." `On review` and `CreditWatch` rows are the *precursor* step and are
included for context, not as withdrawals.

- **Confirmed withdrawals (High confidence):** Iowa City CSD (IA), DeKalb County SD (GA).
- **Probable withdrawal (needs EMMA confirmation):** White Bear Lake Area Schools / ISD 624 (MN).
- **On review / CreditWatch only (NOT withdrawn):** Talbot County SD (GA), Milwaukee Public Schools (WI).
- **Unverified leads (do not rely on):** Terrell County SD (GA), Jackson County SD (GA).

### Cases deliberately EXCLUDED (rated issuer was a city/town/county, not the district)
Spring Valley NY (village), Mount Vernon NY (city), Coventry RI (town), Woonsocket RI (city),
Montgomery County AL (county), Jackson MS (city), Marion OH (city). Several of these had a
*school* deficit as the root cause, but the school district was not the rated issuer.

## `mississippi-delinquent-audits.csv`
The richest *public, named* at-risk population: Mississippi K-12 districts missing/late on
audits. **Important:** in Mississippi the consequence is **accreditation** (probation, state
takeover), **not** a bond-rating withdrawal — this is the upstream pool that, in rating-agency
terms, would be withdrawal candidates. Rows are tiered by category and confidence.

## Aggregate anchors (the basis for the annualized estimate)

| Metric | Value | Year | Source |
|---|---|---|---|
| S&P USPF ratings placed on CreditWatch (missing financials) | 149 | 2023 | Bond Buyer / Bloomberg / S&P |
| S&P 5-year average of such CreditWatch actions | 95 | 2018–2022 | S&P |
| Same actions in 2019 (pre-surge) | <80 | 2019 | S&P |
| **S&P USPF issuers actually WITHDRAWN for lack of timely info** | **~70** | **2023** | S&P "Various Ratings Withdrawn On 70…" |
| Same, earlier-2023 sweep | ~64 | Apr 2023 | Bloomberg / Fortune |
| K-12 school districts rated by Moody's (denominator) | ~3,400 | 2021 | Bond Buyer |
| Local-government issuers rated by Moody's (all types) | ~8,600 | — | NJ League of Munis / Moody's |
| School-district issuers "under review" (GFRC/UIC) | ~34 (~2%) | Oct 2024 | GFRC/UIC |

**Mississippi audit-delinquency counts (as-of dates):**
- Dec 2025: 47 of 138 districts missing one or more financial audits
- Mar 2026: 32 districts missing FY2023 and/or FY2024
- May 2026: 61 missing FY2025; of those 29 also missing FY2024; 13 also missing FY2023
- 14 districts downgraded to probation (8 in the Delta)

## Derived annualized estimate (see main report Part 2 for the full method)
- Recent peak (2022–2024): **~15–40 K-12 districts/year** lose a rating this way (all agencies).
- 10-year average: **~10–25/year** (lower; the phenomenon surged post-2020).
- These are estimates scaled from the all-issuer anchors by the ~40% school-district share of
  the local-government universe and the GFRC under-review signal — **not** a measured count.

## To get a precise count (next step, requires non-free access)
Query EMMA (emma.msrb.org) rating-change filings, or Moody's/S&P rating-action feeds, for
actions coded "insufficient/inadequate information," filtered to issuer type = school
district / ISD / USD. Priority issuers to confirm first: White Bear Lake ISD 624 (MN),
and the full issuer lists behind S&P's "70 issuers" release and Moody's batch withdrawal
press releases (PR_331515, PR_907956418, PR_907260492).
