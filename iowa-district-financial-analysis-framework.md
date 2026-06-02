# Iowa School District Financial Analysis & Benchmarking Framework

**Purpose.** This document defines *how* we will read audited financial PDFs (ACFRs / annual
financial reports and the State Auditor's reports) from Iowa's largest school districts and
turn them into a consistent, comparable assessment. It is the **method**, not the analysis.
When we run the analysis later, every district gets scored the same way, against the same
peer set, using the metrics defined here.

**What we are trying to answer for each district (the three questions the user asked):**

1. **Financial health** — Is the district solvent, liquid, and operating within its means?
   Are reserves adequate and stable?
2. **Strategic position** — Is the district in **building/growth mode** (enrollment up,
   capital program active, debt being issued, facilities expanding) or **maintain mode**
   (flat/declining enrollment, capital limited to upkeep, deleveraging)? Neither is "good" or
   "bad" on its own — the point is to read the posture correctly.
3. **Operational quality** — Are the financials **robust, accurate, diligent, and detailed**?
   Clean opinions, no repeat findings, on-time filing, strong disclosure, recognized reporting.

**Why Iowa needs its own framework.** Generic municipal-finance ratios miss the two facts that
dominate Iowa school finance:

- **The binding constraint is *spending authority*, not cash.** A district can be cash-rich and
  still be in trouble if it exhausts its **Unspent Authorized Budget (UAB / "unspent balance")**.
  Going negative on spending authority is an unlawful act by the board and triggers a **School
  Budget Review Committee (SBRC)** workout plan. Any Iowa health score that ignores spending
  authority is wrong. ([Iowa DOE — SBRC](https://educate.iowa.gov/pk-12/operation-support/business-finance/financial-management/budget-review),
  [ISFIS — School Finance Basics](https://www.iowaschoolfinance.com/schoolfinancebasics))
- **Capital is funded through dedicated, restricted streams** — **SAVE** (the statewide penny
  sales tax for infrastructure) and **PPEL** (the Physical Plant & Equipment Levy) — that are
  *walled off* from the General Fund. Building-vs-maintain mode is read from these funds, not
  from the operating budget. ([Iowa DOE — Levies & Funds](https://educate.iowa.gov/pk-12/operation-support/business-finance/levies-funds),
  [Iowa DOE — Facilities Funding](https://educate.iowa.gov/pk-12/operation-support/school-facilities/funding))

---

## 1. Scope, peer set, and the comparability problem

**Population.** Iowa's largest districts by certified enrollment (the exact roster is set when
we receive the archive). A working "biggest districts" list includes Des Moines, Cedar Rapids,
Davenport, Iowa City, Waukee, Ankeny, Sioux City, West Des Moines, Dubuque, Council Bluffs,
Cedar Falls, Johnston, Linn-Mar, Bettendorf, Pleasant Valley, Marion, Dallas Center–Grimes,
Waterloo, etc. Confirm against the current Iowa DOE certified enrollment file.

**Peers must be grouped before they are compared.** A growing 18,000-student suburb and a
declining 4,000-student urban district are not the same animal. Before scoring, bucket each
district on three axes and only benchmark *within or adjacent to* a bucket:

| Axis | Buckets | Why it matters |
|---|---|---|
| **Size** | <2,500 / 2,500–7,500 / 7,500–15,000 / >15,000 certified enrollment | Fixed-cost spreading, reserve volatility, debt capacity |
| **Enrollment trajectory** | Growing (>1%/yr) / Stable (±1%) / Declining (<−1%) | Funding direction, capital pressure, budget-guarantee reliance |
| **Property wealth** | Taxable valuation **per pupil** (low/mid/high tertile) | Local revenue-raising ability; PPEL/debt headroom |

**Normalization (mandatory for every dollar figure).** Raw dollars are not comparable across
districts. Convert every metric to **at least one** comparable basis:
- **Per pupil** (÷ certified enrollment) — the default for almost everything.
- **As a % of total General Fund revenue / expenditure** — for ratios and shares.
- **Per $1,000 of taxable valuation** — for levy rates and debt.
- **Year-over-year % change** and **3–5 year CAGR** — for trend/direction.

> **Confidence discipline (inherited from this repo's house style).** Every extracted figure
> carries a source (district + fiscal year + statement + page) and a confidence flag. Anything
> we cannot tie to a specific page in a specific audited statement is marked **Low** and is not
> used to rank. We do not invent or interpolate figures to fill a cell.

---

## 2. Source documents — what each Iowa audit contains and where the numbers live

Iowa districts file under GASB. Larger districts publish a full **ACFR** (Annual Comprehensive
Financial Report); all are audited either by the **Iowa Auditor of State** or a private CPA
firm. Know which statement holds which number:

| Section of the report | What we pull from it |
|---|---|
| **Independent Auditor's Report** | Opinion type (unmodified / qualified / adverse / disclaimer); auditor identity; report date (→ timeliness) |
| **Management's Discussion & Analysis (MD&A)** | Management's own narrative on enrollment, finances, capital, debt — and a *quality* signal (depth vs. boilerplate) |
| **Government-wide statements** (Net Position; Activities) | Total/net position, unrestricted net position, change in net position, long-term liabilities |
| **Fund statements** (Balance Sheet & Rev/Exp/Changes — Governmental Funds) | General Fund balance by classification (nonspendable/restricted/committed/assigned/**unassigned**), fund-level revenue & expenditure detail |
| **Budgetary Comparison Schedule (RSI)** | Budget vs. actual — Iowa budgets at the **function** level on a **whole-of-funds certified budget**; over-expenditure of certified budget is the legal red line |
| **Notes to the financial statements** | Debt schedules & maturities, lease/SBITA obligations (GASB 87/96), **IPERS net pension liability** & OPEB, interfund transfers, contingencies, subsequent events |
| **Schedule of Findings & Questioned Costs / Single Audit** | Internal-control material weaknesses & significant deficiencies; federal compliance findings; **repeat** findings; corrective action plans |
| **Statistical/Supplementary section** (ACFR) | 10-year trends: enrollment, valuations, levy rates, debt ratios, demographics |

**Iowa-specific funds to identify and track separately** (do not net them into one number):

- **General Fund (10)** — operations; governed by **spending authority**, not cash.
- **Management Fund (22)** — levy-funded; pays property/liability insurance, early retirement,
  unemployment, legal judgments. A swelling Management levy can mask General Fund stress.
- **PPEL (36)** — regular ($0.33/$1,000) + voter-approved (up to $1.34, total cap $1.67) — buildings,
  grounds, technology hardware, buses, asbestos. ([ITR](https://itrreportcard.org/what-is-the-physical-plant-and-equipment-levy-ppel/))
- **SAVE / Statewide Penny (33)** — sales-tax infrastructure money, equal **per-pupil** statewide;
  funds construction and can also service SAVE revenue bonds or buy down PPEL/PERL/debt levies. ([NW Iowa](https://www.nwestiowa.com/sentinel/iowa-secure-an-advanced-vision-for-education-save-revenue-purpose-statement-q-and-a/article_edb33fa2-7436-11ee-b21e-331dd550d67d.html))
- **Debt Service (40)** — repays GO bonds; funded by the debt-service levy.
- **Capital Projects (36/39)** — active construction.
- **Student Activity (21), Nutrition (61), Internal Service** — secondary, but Nutrition deficits
  and Activity-fund control are operational-quality tells.

---

## 3. The four analytical pillars and their metrics

Each pillar has a small set of metrics with: a **formula**, **where to find it**, a **direction**
(↑ higher is better / ↓ lower is better / ◦ context-dependent), and an **Iowa benchmark band**.
Bands are starting points calibrated to Iowa norms; we re-center them on the *actual peer set's*
distribution (quartiles) once data is loaded, rather than treating any single number as a hard
pass/fail.

### Pillar A — Financial Health (solvency, liquidity, budget discipline)

| # | Metric | Formula | Source | Dir | Iowa benchmark band |
|---|---|---|---|---|---|
| A1 | **Solvency ratio** | (Unassigned + Assigned GF balance) ÷ (Total GF revenue − AEA flow-through) | Fund stmts | ↑ | **<5% weak · 5–15% target/good · 15–25% strong · >25% possibly over-reserved** ([ISFIS](https://www.iowaschoolfinance.com/schoolfinancebasics)) |
| A2 | **Unspent Authorized Budget (UAB) as % of budget** | Unspent spending authority ÷ total GF certified budget | DOM UAB report / notes / MD&A | ↑ | Positive & stable. Falling 3-yr trend toward zero = warning; **negative = SBRC review / unlawful** |
| A3 | **General Fund balance trend** | 3–5 yr change in unassigned GF balance (per pupil) | Fund stmts (multi-yr) | ◦ | Stable/rising healthy; sustained drawdown = structural deficit |
| A4 | **Operating margin** | (GF revenue − GF expenditure) ÷ GF revenue, multi-year | Fund stmts | ◦ | Persistent negative = spending above means |
| A5 | **Days cash / liquidity** | (Cash + investments) ÷ (daily operating expenditure) | Net Position / notes | ↑ | Context; pair with A2 — cash ≠ authority in Iowa |
| A6 | **Budget-guarantee / one-time reliance** | Budget guarantee, SBRC modified allowable growth, one-time ESSER/federal $ as % of GF | MD&A, RSI, notes | ↓ | High reliance on one-time money = fragility (post-ESSER cliff) |
| A7 | **Unrestricted net position** | Unrestricted net position (government-wide), per pupil & trend | Stmt of Net Position | ↑ | Deeply negative driven by pension/OPEB is common in IA — read in context |

**Health read:** strong = positive UAB trend + solvency in target band + flat/positive operating
margin + low one-time reliance. Distress = solvency <5% **and** UAB trending to/through zero
**and** multi-year deficits **and** ESSER dependence.

### Pillar B — Strategic Position (building/growth vs. maintain)

The tell is **enrollment direction × capital intensity × debt trajectory**. Read these together.

| # | Metric | Formula | Source | Reads as… |
|---|---|---|---|---|
| B1 | **Certified enrollment CAGR** | 5-yr CAGR of certified enrollment | Stat. section / DOE | Growth engine; >1%/yr = growing, <−1% = declining |
| B2 | **Capital outlay intensity** | (SAVE + PPEL + Capital Projects spend) ÷ enrollment, 5-yr | Fund stmts | High & rising → **building**; low/upkeep-only → **maintain** |
| B3 | **Construction-in-progress / capital additions** | Δ capital assets; CIP balance; additions vs. depreciation | Capital-asset note | Additions ≫ depreciation → expanding plant; additions ≈ depreciation → holding steady; < depreciation → aging plant |
| B4 | **Debt trajectory** | GO + SAVE-revenue + lease debt, per pupil & YoY; new issuance | Debt note / Debt Service | Rising new issuance → building; net amortization → deleveraging/maintain |
| B5 | **Debt capacity headroom** | Outstanding GO debt vs. **5%-of-assessed-value** constitutional limit; SAVE-bond capacity vs. per-pupil SAVE revenue | Debt note / stat. section | How much building room is left |
| B6 | **Voter-approved capacity in use** | Voted-PPEL active? PPEL near $1.67 cap? Instructional Support Levy (ISL) in use? Bond referendum history | Levy detail / MD&A | Tapped vs. untapped local capacity |
| B7 | **Facilities posture (qualitative)** | Master-plan / new-school / renovation language | MD&A, subsequent events | Confirms the quantitative read |

**Strategic read (the headline classification we assign each district):**
- **Building/Growth** — enrollment ↑, capital intensity high & rising, additions > depreciation,
  new debt being issued, capacity being deployed.
- **Steady-state/Maintain** — flat enrollment, capital ≈ depreciation, debt amortizing, reserves
  prioritized over expansion.
- **Contracting/Right-sizing** — enrollment ↓, capital limited to consolidation/closure, possible
  facility disposal — a distinct posture worth flagging separately from "maintain."

### Pillar C — Operational & Reporting Quality (robust, accurate, diligent, detailed)

This pillar answers "can we *trust* the numbers and does the district run a tight shop?" It is
graded largely from the auditor's product, not the dollars.

| # | Signal | Strong (good) | Weak (concern) | Source |
|---|---|---|---|---|
| C1 | **Audit opinion** | Unmodified ("clean") | Qualified / adverse / disclaimer | Auditor's report |
| C2 | **Internal-control findings** | None | Material weakness / significant deficiency, esp. segregation-of-duties | Schedule of Findings |
| C3 | **Repeat findings** | None | Same finding recurring year over year = not remediating | Findings (multi-yr) |
| C4 | **Single Audit / federal compliance** | Clean | Questioned costs, noncompliance | Single Audit section |
| C5 | **Timeliness** | Filed within statutory window; report date close to FYE | Late / multi-year backlog (the Iowa City cautionary case) | Report date vs. FYE |
| C5b | **Most-recent-year present?** | FY2025 (and FY2024) audit present in the archive | **Most recent year(s) missing/unfiled** = late or non-filing — strongest negative tell, withdrawal territory | Archive inventory vs. Auditor of State |
| C6 | **Disclosure depth & detail** | Rich MD&A, full debt/pension/lease notes, GASB 87/96 adopted, complete statistical section | Boilerplate MD&A, thin notes, missing schedules | Whole report |
| C7 | **Recognition / external validation** | GFOA Certificate of Achievement; ASBO Certificate of Excellence | None | Intro section |
| C8 | **Restatements / prior-period adjustments** | None / explained routine | Unexplained restatements, beginning-balance corrections = control weakness | Notes |
| C9 | **Budget accuracy** | Actuals track certified budget; no function over-expenditure | Large variances, certified-budget overruns (legal issue) | Budgetary RSI |
| C10 | **Estimate quality** | Reasonable IPERS/OPEB, allowances, accruals consistent year-to-year | Volatile, unexplained estimate swings | Notes / RSI |

**Quality read:** "robust/accurate/diligent/detailed" = clean opinion + zero (or zero repeat)
findings + on-time + deep disclosure + GFOA/ASBO recognition + budget actuals that track the
certified budget. The strongest negative single signal is **late/missing audits** (rating-withdrawal
territory — see companion report `school-district-rating-withdrawals.md`); the strongest positive is
**no repeat findings + GFOA certificate + early filing**.

> **The "missing recent year" rule (critical for this dataset).** The archive covers FY2020–FY2025,
> but a district that did not file its FY2024 or FY2025 audit will simply be *absent* for that year.
> **Treat a missing recent year as a finding, not a blank.** A large district whose most recent
> available audit is FY2023 in a FY2025 world is exhibiting the exact late/non-filing pattern that
> precedes a rating withdrawal (the Iowa City case, documented in this repo). So:
> 1. **Confirm it's a true non-filing, not an upload gap** — cross-check the Auditor of State's
>    published report list. "Not in our folder" ≠ "not filed"; only the former is a district problem,
>    but a confirmed non-filing is a serious Pillar C penalty.
> 2. **Score from the most-recent-*available* year, but penalize the staleness** — do not let a clean
>    but two-years-stale FY2023 report earn the same Pillar C standing as a current FY2025 clean filing.
> 3. **Flag every district by its data currency** so a stale-but-clean record can never silently
>    outrank a current one, and so trend metrics (UAB direction, reserve drawdown) are read against the
>    *right* end year.

---

## 4. Scoring & benchmarking model

We produce **both** a transparent profile and a comparable score. The score never replaces the
profile — it orders districts and flags outliers for human reading.

1. **Extract** every metric in §3 into the data schema (§5), with source + confidence.
2. **Normalize** to per-pupil / %, then **percentile-rank within peer bucket** (§1). Ranking
   within peer set avoids penalizing a district for being small or property-poor.
3. **Score each pillar 1–5** from the percentile ranks and the qualitative tells:
   - Pillar A (Health), Pillar C (Operational Quality) → higher is better.
   - **Pillar B (Strategic) is *classified, not scored* good/bad** — output the label
     (Building / Maintain / Contracting) plus a 1–5 *capital-sustainability* sub-score (is the
     building or the maintaining financially supportable?).
4. **Composite** = weighted blend, weights stated explicitly and adjustable. Default starting
   weights: **Health 40% · Operational Quality 35% · Capital-Sustainability 25%.** (Strategic
   *label* is reported alongside, not folded into the number.)
5. **Flag, don't just rank.** Auto-flag any: negative/declining UAB, solvency <5%, repeat audit
   findings, late filing, **most-recent-year (FY2024/FY2025) audit missing/unfiled**, stale data
   currency, ESSER-cliff exposure, debt near the 5% constitutional limit.
6. **Sensitivity / honesty check.** Re-run with alternate weights; if a district's standing
   swings hard, say so. Note every metric that was missing or Low-confidence for that district.

**Output per district:** a one-page scorecard — three pillar scores, the strategic label, the
composite, the flags, and a short narrative tying them to specific statements. Plus a master
benchmark table across all districts.

---

## 5. Data schema (the spreadsheet we will fill in the analysis phase)

One row per **district × fiscal year** (carry 5 years so trends are real, not snapshots).
Mirrors the `data/` CSV convention already in this repo (every cell sourced + confidence-flagged).

```
district, county, fiscal_year, auditor (State/firm), report_date, opinion_type,
certified_enrollment, enrollment_cagr_5yr, taxable_valuation, valuation_per_pupil,
gf_revenue, gf_expenditure, gf_unassigned_balance, gf_assigned_balance, aea_flowthrough,
solvency_ratio, unspent_authorized_budget, uab_pct_of_budget, operating_margin,
days_cash, unrestricted_net_position_pp, one_time_federal_pct,
save_revenue_pp, ppel_levy_rate, capital_outlay_pp, construction_in_progress,
capital_additions, depreciation, go_debt_outstanding, save_rev_debt, lease_sbita_obligations,
debt_per_pupil, debt_vs_5pct_limit, voted_ppel_flag, isl_flag,
ipers_net_pension_liability, opers_oepb_liability,
audit_findings_count, material_weakness_flag, repeat_finding_flag, single_audit_findings,
restatement_flag, gfoa_cert_flag, asbo_cert_flag, certified_budget_overrun_flag,
source_page_refs, confidence
```

Derived/scored columns (computed, not transcribed): `peer_bucket`, `latest_year_available`,
`years_covered`, `recent_year_missing_flag`, `data_currency` (current / 1-yr-stale / 2+-yr-stale),
`pillarA_health_score`, `pillarB_strategic_label`, `pillarB_capital_sustainability`,
`pillarC_quality_score`, `composite_score`, `flags`. `latest_year_available` and
`recent_year_missing_flag` are set at the **district** level during inventory (§6, step 1), before
any per-year extraction.

---

## 6. Extraction workflow (analysis phase, later)

1. **Inventory** the archive first: build the district × fiscal-year coverage grid across the
   FY2020–FY2025 window. For each district record `latest_year_available`, `years_covered`, and
   whether FY2024/FY2025 is absent. A **missing recent year is a finding (C5b), not just a gap** —
   confirm it against the Auditor of State's published report list to separate a true non-filing
   (a real Pillar C penalty) from a mere upload omission, then set `recent_year_missing_flag` and
   `data_currency` before any number is extracted.
2. **Cross-reference Iowa public data** to validate PDF figures — DOE certified enrollment, DOM
   Aid & Levy and the **Unspent Authorized Budget report**, and State Auditor report dates. These
   are authoritative independent checks on what the PDF says.
3. **Extract** per the schema, working statement-by-statement; record page references.
4. **Two-pass accuracy check:** key figures (solvency, UAB, debt, opinion) re-read independently;
   tie government-wide to fund statements where they should reconcile.
5. **Normalize, bucket, rank, score, flag** per §4.
6. **Write** per-district scorecards + the master benchmark table; document every assumption,
   weight, and Low-confidence cell.

**Authoritative cross-check sources:**
[Iowa DOE — School Finance Resources](https://educate.iowa.gov/pk-12/operation-support/business-finance/financial-management/school-finance-resources) ·
[DOM — Unspent Authorized Budget report](https://dom.iowa.gov/resource/school-budget-reference-files/unspent-authorized-budget-report) ·
[Iowa Auditor of State — reports](https://www.auditor.iowa.gov/) ·
[IASB Financial Glossary](https://www.ia-sb.org/docs/default-source/toolbox/financial-tools/school-finance-basics/sept.-2023-financial-glossary-of-terms-(revised)c4452a84-d477-4d19-adbf-098d228c06bc.pdf)

---

## 7. Iowa-specific pitfalls & interpretation guardrails

- **Cash ≠ spending authority.** Always read UAB (A2) alongside cash (A5). The Iowa-distinctive
  failure mode is exhausting authority while holding cash.
- **Restricted money is not flexible.** SAVE, PPEL, Debt Service, Management, Nutrition balances
  are walled off — never count them toward operating solvency. A fat SAVE balance does not rescue
  a thin General Fund.
- **Negative unrestricted net position is normal in Iowa** because IPERS net pension liability and
  OPEB sit on the government-wide statement. Don't score a district down for a pension-driven
  negative UNP — isolate the pension component.
- **The budget guarantee & SBRC modified allowable growth** can prop up a declining-enrollment
  district's revenue temporarily — read them as fragility signals (A6), not strength.
- **The ESSER/federal cliff:** FY2022–FY2024 figures may be inflated by one-time pandemic money.
  Normalize it out (A6) before judging operating health or trend.
- **Auditor identity is context, not a grade.** State Auditor vs. private firm both produce valid
  audits; what matters is the opinion and findings, not who signed.
- **Per-pupil denominators differ** (certified vs. enrolled vs. weighted enrollment). Pick ONE
  denominator and use it consistently; document which.
- **Don't over-interpret a single year.** Reserves and margins are volatile; the 3–5 year trend is
  the signal. One bad year with a clear cause is not distress.
- **Confidence over completeness.** A blank, honestly-flagged cell beats a guessed number. Mirror
  the repo's existing discipline: nothing ranked that isn't sourced.

---

## 8. Deliverables (analysis phase)

1. **`data/iowa-district-financials.csv`** — the filled schema (§5), one row per district-year,
   every cell sourced + confidence-flagged.
2. **Per-district scorecards** — three pillar scores, strategic label, composite, flags, narrative.
3. **Master benchmark table** — all districts ranked within peer buckets, with the flag column.
4. **Methodology appendix** — final weights, peer-bucket cutoffs, and a list of every
   Low-confidence / missing figure, so the ranking's limits are explicit.

---

### Sources

- [Iowa DOE — School Budget Review Committee](https://educate.iowa.gov/pk-12/operation-support/business-finance/financial-management/budget-review)
- [Iowa DOE — Levies & Funds](https://educate.iowa.gov/pk-12/operation-support/business-finance/levies-funds)
- [Iowa DOE — School Facilities Funding & Bonds](https://educate.iowa.gov/pk-12/operation-support/school-facilities/funding)
- [Iowa DOE — School Finance Resources](https://educate.iowa.gov/pk-12/operation-support/business-finance/financial-management/school-finance-resources)
- [Iowa DOM — Unspent Authorized Budget report](https://dom.iowa.gov/resource/school-budget-reference-files/unspent-authorized-budget-report)
- [ISFIS — School Finance Basics (solvency ratio, UAB)](https://www.iowaschoolfinance.com/schoolfinancebasics)
- [IASB — Iowa School Finance Formula: A Summary](https://www.ia-sb.org/docs/default-source/toolbox/financial-tools/school-finance-basics/iowachapter_schoolfinance_final562dd9c6-c4ec-42d6-9a1e-89577356178c.pdf)
- [IASB — Financial Glossary of Terms (2023)](https://www.ia-sb.org/docs/default-source/toolbox/financial-tools/school-finance-basics/sept.-2023-financial-glossary-of-terms-(revised)c4452a84-d477-4d19-adbf-098d228c06bc.pdf)
- [ITR — What is the PPEL?](https://itrreportcard.org/what-is-the-physical-plant-and-equipment-levy-ppel/)
- [SAVE Revenue Purpose Statement Q&A](https://www.nwestiowa.com/sentinel/iowa-secure-an-advanced-vision-for-education-save-revenue-purpose-statement-q-and-a/article_edb33fa2-7436-11ee-b21e-331dd550d67d.html)
- [Iowa Auditor of State — audited reports](https://www.auditor.iowa.gov/)
- Companion in this repo: [`school-district-rating-withdrawals.md`](school-district-rating-withdrawals.md) — what happens when audits go missing/late
</content>
</invoke>
