# Analysis Backlog / Parking Lot

Opportunities identified after uploading full BEDS, Certified Enrollment, Forecast,
and Financial Health datasets — June 2026.

---

## Done

- **✅ Forecasts vs. Reality page** *(was item #1)* — `Certified Enrollment/Forecasts/ICCSD_Enrollment_Story.html`
  8-chapter narrative charting every demographer vintage (DeJong-Richter 2013/2015/2016,
  Granville 2023, Woolpert 2025) vs. Iowa DOE certified actuals, with the GO bond timeline
  and investor-disclosure figures. Plus `Certified Enrollment/Forecasts/README.md`.

- **✅ Neighboring-district enrollment decomposition (Tiffin / Clear Creek Amana, Solon)**
  `Certified Enrollment/Neighboring Districts Study/FINDINGS.md` +
  `iccsd-enrollment-decomposition.html` (factor decomposition page with waterfall bridge,
  county-share, and open-enrollment cross-check charts). Linked from the forecast page.

- **✅ Triangulation update to enrollment forecast** *(was item #3)* — added to
  `iccsd-enrollment-forecast.html` ("How this forecast compares with other projections").
  SVG chart + table comparing Iowa DOE 2025, Woolpert Feb 2025, and our Baseline. All three
  converge on the mid-13,000s by 2030; Iowa DOE and our model land within 245 students.

- **✅ ESA decomposition page** *(was item #2)* — `iccsd-esa-decomposition.html`
  (built by `scripts/build_esa_decomposition.py`). Funnel from 1,440 ICCSD-resident ESA
  vouchers → ~311 upper-bound → ~175 defensible public→private transfers (~78% inframarginal).
  Inline-SVG funnel + private-share trend. Linked from the forecast and decomposition pages
  and the Other-analyses hub.

- **✅ Enrollment → revenue bridge** *(was item #4)* — `iccsd-enrollment-revenue-bridge.html`
  (built by `scripts/build_revenue_bridge.py`). ~752-student Baseline decline by 2030 →
  ~$6.8M/yr recurring headwind at $9,000/student (~$18M cumulative 2026–2030), laid against
  the ~31-day / ~$18M GF cash cushion vs. a 90-day / ~$52M target.

---

## Queued

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
