# Findings — ESA use vs. ICCSD enrollment

*Draft, June 29 2026. Companion to ESA_ICCSD_Decomposition.xlsx and IDENTIFICATION.md.*

## The question

Of the ICCSD-resident students using an Education Savings Account, how many would
have attended ICCSD public schools if ESA did not exist? High ESA uptake is not, by
itself, evidence that ESA is lowering public enrollment.

## Short answer

**The large majority of ESA users in Iowa City were already going to be in private
school. The hypothesis holds.** Of 1,440 ICCSD-resident ESA users in 2025-26:

- **At least ~78%** (≈1,130 students) are *inframarginal* — already private; ESA is a
  subsidy with no effect on public enrollment.
- The **upper bound** on ESA-induced public→private movement is **~310 students** over
  three years (22% of ESA users) — and that drops to **~175 (12%)** once you remove the
  small schools that simply got accredited to access ESA (their students were already
  non-public). The realistic figure is lower still, because even that ~175 includes
  families who moved into the district or would have chosen private regardless.
- For scale: ~175 students is **~1.2% of ICCSD's ~14,400 enrollment**, spread over three
  years.

## How we got there (the decomposition)

ICCSD-boundary (Iowa DE district 3141) resident enrollment, 2022-23 (last pre-ESA) → 2025-26:

| | 2022-23 | 2023-24 | 2024-25 | 2025-26 |
|---|--:|--:|--:|--:|
| Public certified | 14,440 | 14,379 | 14,551 | 14,370 |
| Private (dist 3141) | 1,192 | 1,302 | 1,434 | 1,523 |
| Private share of resident pool | 7.6% | 8.3% | 9.0% | 9.6% |
| ESA residents | — | 471 | 773 | 1,440 |

The logic, following the identification rule:

1. **ESA counts can't show transfer.** The 471→1,440 ramp is mostly the eligibility
   phase-in (income-capped → universal), not students moving. So we ignore it as proof.
2. **Look at private enrollment instead.** It grew +331. Hold the pre-ESA private *share*
   constant and apply it to each year's resident pool: the "excess" private enrollment —
   the part not explained by the size of the school-age population — is **+311** by 2025-26.
   That is the upper bound on net movement into private (would-be public avoiders).
3. **Strip out non-transfers.** ~136 of that is Montessori, Hillside, and the Tamarack
   microschool entering the certified count by getting accredited for ESA — students who
   were already non-public. Net: **~175**, concentrated in growth at established schools
   (Regina +130, Faith +39).
4. **The public side didn't crater.** ICCSD public was ~flat (−70) across the period; in
   2024-25 it actually rose while ESA grew. No co-movement of public-down with ESA-up.
5. **The enrollment plateau is demographic and predates ESA.** Forecasts made in 2015-16
   (before ESA) over-projected 2024-25 by 1,100–1,800 students; the forecast made just
   after ESA launched (Nov 2023) was within ~200. Johnson County births peaked in 2016,
   feeding smaller kindergarten classes from ~2022 on. Immigration cushioned the decline.

So ESA isn't what's holding ICCSD flat — demography is.

## What would have changed the conclusion

If the private schools had grown sharply (new buildings, new K-12 schools, waitlists) and
ICCSD had fallen below its *post-ESA* demographic forecast at the same time, that would
signal a real mix shift. We don't see it: no new K-12 private school opened in the ESA era,
the only physical expansions (Regina's 2020 wing, 2021 early-childhood center) predate ESA,
and the private growth that did occur is modest and demographically plausible.

## Caveats (honest bounds, not a census)

- District-3141 private ≠ the exact ICCSD-resident ESA population (some residents attend
  metro/out-of-area private; some boundary-private students are non-residents). Directional.
- The constant-share counterfactual is a simplification; we report a *range*, not a point.
- ESA-by-school-of-attendance and open-enrollment-by-receiving-district were not obtainable
  from public sources (binary files / no public dashboard) and would tighten the estimate.
- A cross-check supports the pool measurement: public + private (dist 3141) ≈ ACS school-age
  population each year, so homeschool/other is small.

## Bottom line for the original hypothesis

"ESA use is high, therefore it's lowering ICCSD enrollment" does **not** hold for Iowa City.
ESA use is high mainly because families already in private school became eligible. The
defensible public→private transfer attributable to ESA is on the order of **~120–190
students over three years (<1.5% of the district)** — small, concentrated at Regina, and
not the driver of ICCSD's demographically-driven enrollment plateau.
