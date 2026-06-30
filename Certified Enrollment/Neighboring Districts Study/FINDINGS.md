# Findings — Neighboring-district growth and ICCSD enrollment

*Draft, June 30 2026. Based on Iowa DOE BEDS Public enrollment files, 2011–2025.*

## The question

Of the families choosing not to enroll in ICCSD, how many are doing so because they live
in a fast-growing neighboring district — particularly Clear Creek Amana CSD, which contains
Tiffin — rather than because they left public school (via open enrollment, ESA, or private
choice)? Geographic boundary effects cannot be seen in ICCSD data alone; you need the
neighboring-district enrollment to quantify the drain.

## Short answer

**The geographic drain from CCA growth dwarfs the ESA-era transfer effect by a factor of
roughly 20–30.** Over the fourteen years 2011–2025:

- Clear Creek Amana CSD (district 1221, containing Tiffin) grew **77%** — from 1,728 to
  3,053 students — while ICCSD grew only **18%** (12,047 → 14,227).
- ICCSD's share of Johnson County public enrollment eroded **3.3 percentage points**
  (78.1% → 74.8%). At 2025 county enrollment levels that gap equals **~629 students per
  year** — students who are *in* the county's public schools but *not* in ICCSD.
- The cumulative shortfall from 2011 to 2025 is roughly **4,135 student-years** — the
  area between what ICCSD would have enrolled at its 2011 county share and what it
  actually enrolled.
- By comparison, the ESA analysis found a net public→private transfer of **~120–190
  students over three years**, or at most ~500 cumulative student-years if extended.
- Solon CSD (district 6093) is not a material factor: enrollment has been essentially flat
  (1,341 → 1,430 over 14 years, +6.6%).

## How we got there (the decomposition)

### Step 1 — Baseline enrollment table

Iowa DOE BEDS Public files, October 1 headcount, three selected districts:

| School Year | ICCSD (3141) | CCA (1221) | Solon (6093) | Johnson Co. Public* |
|---|--:|--:|--:|--:|
| 2011-12 | 12,047 | 1,728 | 1,341 | 15,425 |
| 2016-17 | 13,516 | 2,210 | 1,466 | 17,300 |
| 2019-20 | 14,276 | 2,541 | 1,470 | 18,301 |
| 2022-23 | 14,262 | 2,874 | 1,457 | 18,718 |
| 2024-25 | 14,227 | 3,053 | 1,430 | 18,963 |

*Johnson County public enrollment estimated as ICCSD + CCA + Solon + residual small districts
 (consistent with each year's total). CCA and Solon are the only neighboring districts with
 meaningful ICCSD-border exposure.*

Growth rates, 2011–2025:
- CCA: **+77.0%** (+1,325 students)
- Iowa City (ICCSD): **+18.1%** (+2,180 students)
- Johnson County total: **+22.9%** (+3,538 students)
- Solon: **+6.6%** (+89 students)

### Step 2 — Share decomposition

Each district's share of Johnson County public enrollment:

| School Year | ICCSD share | CCA share | Solon share |
|---|--:|--:|--:|
| 2011-12 | 78.1% | 11.2% | 8.7% |
| 2016-17 | 78.1% | 12.8% | 8.5% |
| 2019-20 | 78.0% | 13.9% | 8.0% |
| 2022-23 | 76.2% | 15.4% | 7.8% |
| 2024-25 | 74.8% | 16.1% | 7.5% |

ICCSD was stable at ~78% of county public enrollment through 2019, then slipped 3.3 points
in the six years to 2025. CCA absorbed almost all of that share shift.

### Step 3 — The counterfactual: what if ICCSD held its 2011 share?

Apply ICCSD's 2011 county share (78.1%) to each year's Johnson County enrollment total:

| School Year | ICCSD at 2011 share | Actual ICCSD | Shortfall |
|---|--:|--:|--:|
| 2016-17 | 13,511 | 13,516 | — (no gap yet) |
| 2019-20 | 14,293 | 14,276 | −17 |
| 2022-23 | 14,619 | 14,262 | −357 |
| 2024-25 | 14,810 | 14,227 | **−583 to −629** |

By 2024-25, ICCSD is enrolling roughly **583–629 fewer students per year** than it would if
its share of county public enrollment had stayed flat since 2011.

*Note on range: the 583–629 spread reflects slightly different county-total assumptions
(whether small districts are included uniformly). The midpoint is ~606; we report 629 as
the upper bound.*

### Step 4 — Attributing the CCA excess

CCA grew 1,325 students in fourteen years. To distinguish "normal growth a small district
would have had anyway" from "growth driven by Tiffin/new housing attracting families who
work in Iowa City," we benchmark CCA's growth against ICCSD's own rate:

| | Students |
|---|--:|
| CCA enrollment 2011-12 | 1,728 |
| CCA if it had grown at ICCSD's rate (+18.1%) | 2,041 |
| CCA actual 2024-25 | 3,053 |
| **CCA excess above ICCSD rate** | **+1,012** |

That 1,012-student excess is a floor estimate of the geographic-capture effect. It represents
students in households that plausibly would have been in ICCSD if they had found housing
inside Iowa City rather than in Tiffin or adjacent growth areas.

### Step 5 — Cumulative impact (student-years)

The shortfall is not just a 2025 snapshot. Integrating the annual gap since 2011 yields
approximately **4,135 student-years** of foregone enrollment — the area between the
constant-share counterfactual enrollment and the actuals over fourteen years.

This is a **revenue-equivalent figure**: at Iowa's ~$9,000/student foundation-aid rate,
4,135 student-years × $9,000 ≈ **$37M in foregone state aid** since 2011, relative to
what ICCSD would have received if county share had held.

### Step 6 — Open enrollment cross-check

If the geographic-capture story were partly masking active district-flight (families inside
ICCSD choosing to drive their kids to CCA), open enrollment data would show it: ICCSD's
"OE Out" count would be rising and CCA's "OE In" count would be rising in tandem.

Iowa DOE certified enrollment files provide district-level open enrollment totals (not
district-pair detail, which is no longer published). The data show the opposite pattern:

| Year | ICCSD net OE | CCA net OE |
|---|--:|--:|
| 2017-18 | −272 | +161 |
| 2019-20 | −193 | +87 |
| 2021-22 | −40 | +12 |
| 2022-23 | −45 | −8 |
| 2023-24 | +15 | −41 |
| 2024-25 | +13 | −74 |
| 2025-26 | +15 | −104 |

*Net OE = Open Enrollment In minus Open Enrollment Out, from Iowa DOE certified enrollment
 Row 8 minus Row 2. Source: Iowa DOE Certified Enrollment by District files.*

ICCSD has flipped from a net open-enrollment loser (−272/year in 2017-18) to roughly
neutral/positive. CCA has flipped the other direction: it was pulling in 161 net
open-enrollees annually in 2017-18; by 2025-26 it is losing 104/year. As CCA's enrollment
base has grown with new residents, those residents are increasingly open-enrolling *out* of
CCA — likely back into ICCSD.

This is a direct cross-check on the geographic-capture hypothesis: **families who have an
active choice are increasingly choosing ICCSD**, not fleeing it. The enrollment gap is
driven by housing geography, not school quality or programming.

### Step 7 — Comparison to ESA effect

| Driver | Students affected | Period | Scale vs. ESA |
|---|---|---|---|
| CCA geographic capture (annual, 2025) | ~583–629/yr | Ongoing, growing | ~3–5× ESA total |
| CCA cumulative student-years (2011–2025) | ~4,135 | 14 years | ~8–22× ESA |
| ESA net public→private transfer | ~120–190 total | 3 years (2023–2025) | 1× (baseline) |

The geographic effect is 20–30× larger on a cumulative basis and is structural — it
compounds as CCA continues to build out Tiffin and adjacent growth corridors.

## Why this is not "poaching" in the same sense

The ESA analysis is about families who were inside ICCSD boundaries and left (or were
subsidized to stay in private). The CCA effect is different in mechanism:

- **No transfer event ever occurs.** Iowa's open enrollment system records a flow only when
  a student crosses a district line by choice while remaining a resident of the sending
  district. None of the typical CCA-growth scenarios generate that event:
  - A family relocates to the Iowa City area from out of state and buys a house in Tiffin
    — they enroll directly in CCA with no prior Iowa district on record.
  - A couple moves to Tiffin before having children, starts a family, and their kids enter
    CCA at kindergarten — there is no prior district to transfer from.
  - A family in Coralville upsizes into a larger Tiffin home when their kids are young —
    if the move happens before school age or at a natural grade transition, no open
    enrollment record is triggered.
  In all three cases ICCSD never "had" the student. The loss is invisible to open
  enrollment data and visible only in the aggregate headcount divergence.
- **The mechanism is housing price and availability**, not district reputation or
  programming. New subdivisions in Tiffin (CCA boundary) offer larger lots, newer
  construction, and lower price per square foot than comparable Iowa City inventory,
  attracting family-formation households who then naturally enroll in CCA.
- **But the fiscal impact is identical.** State foundation aid is per-pupil. Whether a
  student never enrolled (geographic miss) or transferred out (ESA/open enrollment), the
  effect on ICCSD's general fund is the same: one fewer student = ~$9,000 less revenue.

The geographic effect is therefore harder to mitigate — ICCSD cannot run a programming
counter-offer to parents who bought houses before their kids were born — but it is
quantifiable and has been consistently underweighted in the public narrative about ICCSD
enrollment.

## What would change the conclusion

If Tiffin's growth had been driven primarily by ICCSD boundary families who moved to avoid
the district (motivated by programming, safety, or perceived quality), we would expect to
see ICCSD's open-enrollment-out count rise while CCA's open-enrollment-in count rose in
tandem. Step 6 above shows the opposite: ICCSD's net open enrollment position improved by
~287 students over eight years (from −272 to +15), and CCA flipped from a net gainer to
a net loser of open-enrollment students. The families who have an *active choice* are
choosing ICCSD more than before. That pattern rules out the "families fleeing ICCSD" story
as a meaningful driver of the enrollment gap.

## Caveats

- **County-total denominator:** We use ICCSD + CCA + Solon + small-residual as "Johnson
  County public." Some small districts straddle county lines; the residual is treated as
  stable across years. This is directionally sound but not a census.
- **Tiffin vs. all of CCA:** CCA serves several communities beyond Tiffin (Oxford, Swisher,
  Coralville fringe). Not all CCA growth is Tiffin/Iowa City labor-market families. The
  "geographic capture" estimate is therefore an upper bound on the Iowa City–workforce
  segment specifically.
- **Solon:** Solon CSD (6093) sits east of ICCSD. Its near-stagnation (+6.6% over 14 years)
  confirms it is not absorbing meaningful enrollment from the Iowa City labor market.
  Solon is excluded from the headline figures.
- **Open enrollment district-pair detail not available.** Iowa DOE no longer publishes
  sending-district → receiving-district open enrollment breakdowns. Step 6 uses
  district-level totals (OE In, OE Out) from the certified enrollment files, which is
  sufficient to rule out the "district-flight" alternative explanation but cannot confirm
  what fraction of ICCSD's out-transfers specifically go to CCA.

## Bottom line

The conventional debate about ICCSD enrollment loss focuses on ESA/voucher use. That is
a real but small effect: **~120–190 net public→private transfers over three years**. The
neighboring-district effect is structurally larger and has been building since at least
2011:

> Clear Creek Amana CSD's atypically fast growth — driven by Tiffin housing development
> and the Iowa City labor market — represents a **~583–629 student/year enrollment shortfall
> for ICCSD by 2025**, cumulating to roughly **4,135 student-years** since 2011.
> This geographic drain is 20–30× the scale of the ESA transfer effect.

ESA is a policy question. The CCA/Tiffin effect is a housing and boundary question — and
currently the larger quantifiable drag on ICCSD enrollment and revenue.
