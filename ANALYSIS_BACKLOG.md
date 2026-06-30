# Analysis Backlog / Parking Lot

Opportunities identified after uploading full BEDS, Certified Enrollment, Forecast,
and Financial Health datasets — June 2026.

---

## In progress

- **Neighboring-district enrollment decomposition (Tiffin / Clear Creek Amana, Solon)**
  Same waterfall methodology as the ESA Private Study. Quantify how many students
  are "captured" by neighboring districts because of housing growth just outside ICCSD
  boundaries (especially Tiffin / Clear Creek Amana CSD). Compare CCA and Solon growth
  vs. ICCSD to estimate the geographic drag on ICCSD enrollment.

---

## Queued

### 1. Forecasts vs. Reality page
*Data in hand: `Certified Enrollment/Forecasts/ICCSD_Enrollment_Forecast_vs_Actual.xlsx`*

Chart every demographer forecast vintage (RSP 2010, DeJong-Richter 2013/2015/2016,
Granville 2023, Woolpert 2025) against Iowa DOE certified actuals, with the GO bond
timeline overlaid. Key story: bond-era forecasters overshot by 9–13% (1,256–1,902
students by 2024-25); post-bond forecasters are accurate and project decline. This
page is the connective tissue between enrollment and financial health.

### 2. ESA decomposition page
*Data in hand: `Certified Enrollment/ESA Private Study/FINDINGS.md` + `.xlsx`*

Build a proper HTML page from the completed FINDINGS.md. The central finding —
~78% of ESA users were already private (inframarginal); net public→private movement
is ~120–190 students over 3 years, under 1.5% of the district — resolves the open
question on the forecast page and deserves its own citable analysis.

### 3. Triangulation update to enrollment forecast
*Data in hand: Iowa DOE 2026-31 projections (13,720 certified by 2030-31); Woolpert
2025 (13,609 headcount by 2034-35); our model Baseline (13,475 headcount by 2030)*

Add Iowa DOE and Woolpert 2025 as comparison lines on the fan chart or a new
comparison table. Three independent methods using different data and assumptions
converge within ~300 students of each other — a significant credibility signal.

### 4. Enrollment → revenue bridge
*Derivable from enrollment projections + Iowa per-pupil foundation aid rate (~$9,000)*

Short analysis: Baseline 2030 scenario = ~700 fewer students than 2025 × $9,000
state foundation aid = ~$6M/year revenue headwind. Layer against current thin
cash position (31 days net cash vs. 90-day target). Makes the enrollment decline
financially consequential in concrete terms.

### 5. Ten-Point Test trend (FY2014–2025)
*Data in hand: `ICCSD_FinancialHealth/FY15-FY25 Summary.xlsx`*

Chart the district's own financial health metrics from bond-era peak to now:
- Day's Net Cash: 88 days (2017) → 31 days (2025). Target: 90+.
- Financial Solvency Ratio: 12.3% (2017) → 6.0% (2025). Target: 10%.
- Unspent Balance: 6.6% (2017) → 2.3% (2025). Target: 10%.
All three peaked at bond issuance and have not recovered. Connects the bond-era
over-projection story to observed financial deterioration.

---

## Later / lower priority

- **Building-level enrollment analysis** (`BEDS/BEDS_Public_ByBuilding/`): which ICCSD
  schools are growing (North Liberty-area elementaries) vs. shrinking (west-side Iowa
  City). Relevant to closure/consolidation discussion.

- **Immigrant student trend as enrollment cushion**: Johnson County immigrant students
  grew from ~20 (2009-10) to 1,164 (2020-21). If that flow changes (immigration
  policy, university enrollment), it is a large latent risk to ICCSD headcount.

- **Birth rate update**: Iowa birth data beyond what CDC WONDER currently has. More
  refined county-level projection than the linear extrapolation currently used.
