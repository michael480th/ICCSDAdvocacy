# School Districts That Lost Their Bond Rating for Lack of (Timely) Financial Information

**Scope:** U.S. K-12 school districts, 2015–2025. "Lost its rating" = a rating agency
**withdrew/suspended** the rating because it lacked sufficient or timely financial
information (e.g., the district failed to deliver audited financial statements in time).
**Downgrades do not count** — a withdrawal is the more severe action and is the focus here.

**Companion data:** structured spreadsheets live in [`data/`](data/) —
[`confirmed-rating-actions.csv`](data/confirmed-rating-actions.csv) (named district cases),
[`mississippi-delinquent-audits.csv`](data/mississippi-delinquent-audits.csv) (the at-risk
population), and [`data/README.md`](data/README.md) (aggregate anchors + method).

**Research date:** May 2026. Compiled from multi-source web research (Moody's/S&P/Fitch
policy documents, SEC, MSRB/GFOA, Bond Buyer, Bloomberg, GFRC/UIC, and local news).
Primary agency pages (Moody's, S&P, Bond Buyer, Bloomberg) bot-block automated fetching;
figures below were corroborated across multiple independent outlets and, where possible,
a second independent web search. Confidence is noted throughout.

---

## Bottom line

1. **There is no published list — by anyone — of school districts that lost a rating for
   lack of financial information.** Rating agencies report withdrawals issuer-by-issuer,
   not in a registry, and they do **not** break their withdrawal counts out by issuer type
   (school district vs. city vs. county). So a truly *complete* per-district list cannot be
   assembled from public sources. What follows is the best achievable: **confirmed named
   cases + a defensible annualized estimate**, kept strictly separate.

2. **Annualized estimate (all agencies, nationwide):** Roughly **15–40 K-12 districts per
   year** lost a rating this way during the recent peak (2022–2024); the **10-year average
   is lower, on the order of ~10–25/year**, because the phenomenon surged after 2020 from a
   much smaller pre-pandemic baseline. This is an **estimate**, derived below — treat it as
   an order-of-magnitude figure, not a precise count.

3. **The single best hard anchor:** In 2023, **S&P withdrew the ratings of ~70 U.S. public
   finance issuers** for "lack of timely information," after placing **149** on CreditWatch
   (vs. a 2018–2022 average of **95** such warnings, and **<80** actions in 2019). School
   districts are a *subset* of that all-issuer total — the agencies just don't tell us how
   big a subset.

---

## Part 1 — Confirmed named cases (school district was the rated issuer)

These are cases where the **district itself** held the rating and it was **withdrawn**
specifically for missing/late audited financials. Public reporting on individually named
districts is sparse; these are the cleanest confirmed examples.

| District | State | Agency | Year withdrawn | Prior rating | Stated reason | Confidence |
|---|---|---|---|---|---|---|
| **Iowa City Community School District** | IA | Moody's | 2024 (still unrated as of May 2026) | **Aa2** | "Lack of information" — FY2023 (then FY2024/FY2025) audits not completed | High |
| **DeKalb County School District** | GA | Moody's | 2020 | Aa-band (notch unverified) | FY2018 audited financials filed >1 year late (Dec 2019) | High |
| **White Bear Lake Area Schools (ISD No. 624)** | MN | S&P | ~2023 | not stated | Appears in S&P's "Various Ratings Withdrawn On 70 U.S. Public Finance Issuers Due To Lack Of Timely Information" | **Medium — verify via EMMA** |

> **Correction to the earlier draft:** *Jackson County School District (GA)* was previously
> listed here as a confirmed ~2018 withdrawal. A deeper search could **not** confirm it — the
> single entity actually *withdrawn* in Moody's June 2018 "insufficient information" action was
> **Spring Valley, NY (a village)**, not a school district. Jackson County SD is now treated as
> an **unverified lead** (see `data/confirmed-rating-actions.csv`). This is exactly the kind of
> claim that requires a primary EMMA/agency filing before it can be relied upon.

**Iowa City's prior rating (Aa2) is now confirmed.** DeKalb's exact notch and the White Bear
Lake action type still need a primary EMMA/MSRB filing to confirm.

### "On review / CreditWatch" — the precursor step (NOT withdrawals)

These districts were flagged for missing/late financials but did **not** (or not yet) lose the
rating — useful because "under review for lack of information" is the step that precedes a
withdrawal:

- **Talbot County School District (GA)** — Moody's placed it on review (Jun 2018), then
  *confirmed* the rating at **A3** (Aug 2018). Review resolved; rating retained.
- **Milwaukee Public Schools (WI)** — S&P **CreditWatch negative** (Dec 2024, prior **A+**) over
  late FY2022-23 / FY2023-24 audits and ~$81M of withheld state aid; partial resolution Aug 2025.

### Closely related — but NOT clean school-district withdrawals (do not count these)

- **Coventry, RI** — Moody's **withdrew** the rating in 2024 for "lack of sufficient
  information" (no FY2022-23 audit), and the driver was a ~$5M **school** deficit / planned
  $25M school-construction bond — but the **rated issuer was the Town**, not the district.
  (Same caveat for **Woonsocket, RI**.)
- **Fayette County Public Schools (KY)** — May 2026 Moody's **downgrade** (A2→A3) for
  *inaccurate* financial reporting. A downgrade, not a withdrawal.
- **Alum Rock Union ESD (CA)** — S&P **CreditWatch** over audit findings, not a withdrawal.
- **St. Paul Public Schools (MN)** — late FY2023 audit flagged as a rating *risk*; no
  confirmed action.

The pattern is important: most *named* "lost-its-rating-over-a-late-audit" headlines are
**cities and counties** (Jackson MS, Montgomery County AL, Mount Vernon NY, Marion OH,
Coventry/Woonsocket RI), not the school district as the rated entity — even when a school
deficit caused the problem.

---

## Part 2 — The annualized estimate (methodology)

Because no source isolates a school-district-only count, we build the estimate from the
best available anchors and scale down.

### Anchors
- **S&P, 2023:** ~**70 U.S. public finance issuers** had ratings **withdrawn** for lack of
  timely information; **149** placed on CreditWatch; **2018–2022 average = 95** warnings;
  **<80** actions in 2019. Bloomberg: the volume of stale-financials watch/withdrawal
  actions "more than quadrupled since 2018." *(High confidence — corroborated by Bond
  Buyer, Bloomberg, Fortune, and an independent verification search.)*
- **Moody's** does these in periodic **batches** ("withdraws 8 local governments…",
  "places 10 on review and withdraws 1…", "places 5 on review… withdraws Mount Vernon").
  Moody's publishes **no aggregate annual count**, so its volume must be estimated by
  tallying these press releases. Policy: Moody's withdraws "for lack of sufficient
  information" when audited financials aren't received **within ~1 year of fiscal year-end**.
- **Universe (denominator):** Moody's rates **~3,400 K-12 school districts** (and ~8,600
  local governments total — so districts are roughly **40%** of the local-gov universe).
  *(Medium-high confidence — recurs across Bond Buyer and law-firm sources.)*
- **School-district-specific signal:** Per GFRC/UIC (Oct 2024), of ~3,300 tracked
  school-district issuers, only ~**34 were under review** and ~36 on negative outlook
  (~2%). "Under review for lack of information" is the step that precedes withdrawal, so
  this caps the plausible annual school-district withdrawal count in the **low tens**.

### The math (transparent and rough)
- School districts are ~40% of the local-government issuer universe. If withdrawals track
  issuer counts, then of S&P's ~70 USPF withdrawals (2023), the local-government share that
  is school districts implies **roughly 15–30 districts withdrawn by S&P in the 2023 peak**.
- **Moody's** runs a parallel program of comparable order; **Fitch/KBRA** add smaller
  numbers. Summing across agencies (and netting out districts hit by two agencies) puts the
  recent-peak total around **~15–40 districts/year**.
- The **10-year average is lower**. The surge is a post-2020 phenomenon (auditor shortages,
  pandemic Single-Audit backlog, GASB 87/96 complexity). In 2019 there were **<80** total
  USPF actions; pre-2020 the school-district share was plausibly in the **single digits to
  ~15/year**. Blending the low pre-2020 years with the 2021–2024 spike yields a 10-year
  average of **~10–25 districts/year**.

> **Confidence: Moderate.** The all-issuer anchors are solid; the step from "all USPF
> issuers" to "K-12 districts only" is an estimate based on the ~40% issuer share and the
> GFRC ~34-under-review signal. The true figure could be somewhat higher (district finance
> offices are especially thinly staffed) or lower.

---

## Part 3 — Why this happens, and the withdrawal mechanism

- **The trigger:** an audited Annual Comprehensive Financial Report (ACFR) not delivered in
  time. GFOA's standard is **180 days** after fiscal year-end; MSRB suggests **120 days**.
  Moody's practice is to withdraw if it hasn't received the audit within **~1 year** of FYE.
- **Agency policies (all permit, Moody's effectively *requires*, withdrawal for bad info):**
  - **Moody's** ("WR" = Withdrawn Rating): "*shall* withdraw any Credit Rating if the
    information available… is insufficient to effectively assess the creditworthiness… and
    such information is unlikely to be available… in the near future." Standard wording in
    its actions: "we believe we have insufficient or otherwise inadequate information to
    support the maintenance of the rating(s)."
  - **S&P** ("NR"): may withdraw "because of a lack of information," at its sole discretion;
    usual path is CreditWatch → 30-day cure window → withdrawal.
  - **Fitch** ("WD"): withdraws when "limited availability of operational and financial
    information… does not provide sufficient transparency to maintain the ratings."
- **Root causes of the post-2020 surge:** national accountant/auditor shortage (~300k left
  the profession 2020–2022); a wave of federally-required **Single Audits** from pandemic
  aid; new **GASB 87 (leases)** and **GASB 96 (subscriptions)** standards adding audit work;
  and chronic understaffing/turnover in district finance offices.

---

## Part 4 — How to close the gap to a *precise* annualized number

A defensible exact count is obtainable, but not from free web sources. The paths:

1. **Rating-action datasets (best):** Query Moody's / S&P rating-action feeds (or EMMA's
   rating-change data) for actions coded **"insufficient/inadequate information"** and
   **filter by issuer type = school district / ISD / USD**. This yields the true count.
2. **S&P & Moody's annual transition studies** (subscription): S&P "Default, Transition, and
   Recovery: Annual U.S. Public Finance" study and Moody's "US Municipal Bond Defaults and
   Recoveries" contain withdrawal ("WR") columns and reason splits.
3. **GFRC/UIC audit-timeliness report** (the ~3,300-district dataset) — the authoritative
   source for school-district audit lateness and under-review counts.
4. **State delinquent-audit lists** (free, mineable for the *upstream* population that feeds
   withdrawals):
   - **Mississippi** — strongest dataset: as of May 2026, **61 districts** missing FY2025
     audits; **29** also missing FY2024; **13** also missing FY2023 (consequence there is
     accreditation, not bond rating — a different lever).
   - **Louisiana** Legislative Auditor "Non-Compliance Report" (lists school boards).
   - **South Carolina** Treasurer "Municipal Delinquent Audits."
   - Audit-status portals in **Ohio, Arizona, New York, Missouri, Florida**.

---

## Sources

**Rating-agency policy**
- Moody's Policy for Withdrawal of Credit Ratings — https://ratings.moodys.com/api/rmc-documents/361187 ; https://www.moodys.com/nrsro_sp13418
- S&P withdrawal policy (Form NRSRO Ex.2) — https://www.sec.gov/Archives/edgar/data/1650548/000165054824000007/SPGR_Ex2.Dec2024.pdf
- Fitch withdrawal policy (Form NRSRO Ex.2) — https://www.sec.gov/Archives/edgar/data/1652282/000114420416112378/v443948_exhibit2.pdf

**Aggregate / annualized data**
- S&P, "Lack Of Timely Information Leads To Increase In Negative Rating Actions…2023" — https://www.spglobal.com/ratings/en/research/articles/230314-lack-of-timely-information-leads-to-increase-in-negative-rating-actions-across-u-s-public-finance-so-far-in-2-12665457
- Bond Buyer, "S&P tells 149 issuers: provide timely financials or risk withdrawn ratings" — https://www.bondbuyer.com/news/s-p-tells-149-issuers-provide-timely-financials-or-risk-withdrawn-ratings
- Bloomberg, "Muni Credit Ratings Are at Risk Because of Missing Accountants" — https://www.bloomberg.com/news/articles/2023-03-14/muni-credit-ratings-are-at-risk-because-of-missing-accountants
- Fortune / Bloomberg, "Accountant shortage leaves some US cities without credit ratings" (~64 withdrawn, Apr 2023) — https://www.bloomberg.com/news/articles/2023-04-21/accountant-shortage-leaves-some-us-cities-without-credit-ratings
- Route Fifty, "How an auditor shortage could hurt local governments" — https://www.route-fifty.com/workforce/2023/04/how-auditor-shortage-could-hurt-local-governments/385337/
- GFRC/UIC + Merritt audit-time report — https://gfrc.uic.edu/ ; https://www.bondbuyer.com/news/municipal-audit-times-improve-long-term-trends-remain-slow
- Moody's K-12 universe (~3,400 districts) — https://www.bondbuyer.com/news/moodys-new-school-rating-methodology-may-impact-65-billion-of-debt

**Named cases**
- Iowa City CSD — https://www.kcrg.com/2026/05/01/iowa-city-community-school-district-could-face-long-road-restore-credit-rating/ ; https://www.thegazette.com/news/education/iowa-city-school-district-is-years-behind-in-audits-here-s-why-it-matters/
- DeKalb County SD (GA) — https://www.ajc.com/news/local-education/credit-service-withdraws-its-rating-for-dekalb-schools/yaHT603lNPKBE4qsvq6gEI/
- Milwaukee Public Schools — https://www.maciverinstitute.com/news/milwaukee-public-schools%E2%80%99-credit-takes-hit-over-missing-financial-report
- Coventry, RI — https://www.wpri.com/target-12/sins-of-our-past-coventry-faces-5m-school-deficit-loses-moodys-rating/
- Montgomery County, AL — https://1819news.com/news/item/moodys-withdraws-montgomery-countys-bond-ratings-due-to-missing-audit
- Jackson, MS (city) — https://www.wlbt.com/2025/03/20/moodys-deals-blow-jacksons-credit-rating-cites-lack-sufficient-information/

**SEC / continuing disclosure (related but distinct mechanism)**
- SEC MCDC issuer actions (71 issuers, Aug 2016) — https://www.sec.gov/newsroom/press-releases/2016-166
- SEC v. West Clark Community Schools (2013, foundational) — https://www.sec.gov/newsroom/press-releases/2013-136

**State delinquent-audit lists**
- Mississippi — https://mississippitoday.org/2026/05/21/school-district-financial-audit/
- Louisiana LLA Non-Compliance Reports — https://lla.la.gov/reports/non-compliance-reports
- South Carolina Treasurer Municipal Delinquent Audits — https://treasurer.sc.gov/what-we-do/for-governments/audit-information/municipal-delinquent-audits/

---

## Confidence & caveats

- **High confidence:** the mechanism, the agency policies, the S&P 2023 anchors (149
  watch / ~70 withdrawn / 95 five-year average / <80 in 2019), Moody's ~1-year trigger,
  the ~3,400 rated-district universe, and the two flagship named cases (Iowa City, DeKalb).
- **Moderate confidence:** the **annualized school-district-only estimate (15–40/yr peak;
  ~10–25/yr over 10 years)** — derived by scaling all-issuer figures by the ~40% district
  share and the GFRC under-review signal, not measured directly.
- **Not establishable from public sources:** a complete, exhaustive per-district list, and
  the exact prior rating notches for individual districts. Both require subscription
  rating-action datasets and/or EMMA filings (see Part 4).
- All primary agency/press pages (Moody's, S&P, Bond Buyer, Bloomberg) bot-block automated
  retrieval; every figure here was taken from multi-outlet corroboration rather than a
  single fetched document.
