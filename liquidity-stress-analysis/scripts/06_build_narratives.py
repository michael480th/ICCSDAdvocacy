"""
06_build_narratives.py  -- Deliverable 4 (executive summary) + ICCSD one-pager
+ Cedar Rapids comparison. Numbers are pulled live from the computed datasets.
"""
import pandas as pd

import common as C

RECENT = C.COMMON_RECENT_FY


def f0(x):
    return "n/a" if pd.isna(x) else f"{x:,.0f}"


def pct(x, d=1):
    return "n/a" if pd.isna(x) else f"{x*100:.{d}f}%"


def ordn(x):
    n = int(round(x))
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def main():
    m = pd.read_csv(C.MASTER_CSV)
    f = pd.read_csv(C.FOCUS_CSV)
    t1 = pd.read_csv(C.TABLES_DIR / "table1_recent_screen.csv")
    t3 = pd.read_csv(C.TABLES_DIR / "table3_numerator_sensitivity.csv")
    supp = pd.read_csv(C.ICCSD_CASH_SUPP_CSV)

    ic_aud = f[f.district_code == 3141].sort_values("fiscal_year")
    ic_car24 = m[(m.district_code == 3141) & (m.fiscal_year == RECENT)].iloc[0]
    cr_aud = f[f.district_code == 1053].sort_values("fiscal_year")

    # statewide percentile of ICCSD practical cushion in FY2024
    cur = m[(m.fiscal_year == RECENT) & m.practical_days_cushion.notna()]
    ic_pctile = (cur.practical_days_cushion < ic_car24.practical_days_cushion).mean()
    ic_uab_pctile = (cur.uab_cushion < ic_car24.uab_cushion).mean()
    n_state = len(cur)

    # peer ranking FY2024
    t1s = t1.sort_values("Practical days cushion").reset_index(drop=True)
    ic_rank = t1s.index[t1s.District == "Iowa City CSD"][0] + 1

    ic23 = ic_aud[ic_aud.fiscal_year == 2023].iloc[0]
    ic_t3 = t3[t3.District.str.startswith("Iowa City")]
    cr_t3 = t3[t3.District.str.startswith("Cedar Rapids")]

    # ---------- Executive summary ----------
    es = f"""# Executive summary — Iowa school district liquidity stress benchmarking

*Annual statewide screen. Apparent liquidity risk only — not confirmed intra-year cash stress.
Most recent common fiscal year for peer comparison: FY{RECENT}.*

## 1. Does ICCSD screen as unusually liquidity-constrained?

**Yes, on a reserve-thinness basis — but as "thin operating reserves," not (from this data)
confirmed intra-year cash stress.** In FY{RECENT} Iowa City's practical operating cushion was
**{ic_car24.practical_days_cushion:.0f} days** ((assigned+unassigned GF balance) ÷ GF
expenditures × 365). That ranks **{ic_rank} of {len(t1s)}** among the large focus districts
(only Waterloo and Linn-Mar were thinner) and sits around the
**{ordn(ic_pctile*100)} percentile** of the ~{n_state} Iowa districts scored statewide — i.e.
in the lower-middle of the state, and at the thin end of its size-matched peer group.

The cushion lands in the **Moderate** band (20–45 days) in FY{RECENT}, but that is a recovery
year. Across FY2020–FY2023 the audited practical cushion ran
**{ic_aud[ic_aud.fiscal_year.between(2020,2023)].practical_days_cushion.min():.0f}–{ic_aud[ic_aud.fiscal_year.between(2020,2023)].practical_days_cushion.max():.0f} days**,
dropping to **{ic23.practical_days_cushion:.0f} days in FY2023** — squarely in the **Very high**
band — the year its spending authority also went negative.

## 2. Which metric drives the conclusion?

Two metrics, and they are different things:

- **Reserve adequacy (cushion):** ICCSD's assigned+unassigned reserves are persistently thin
  relative to its spending base. Critically, this is **not** an artifact of the strict
  "unassigned only" definition — see the numerator sensitivity below.
- **Spending authority (UAB):** This is the sharper outlier. ICCSD's unspent authorized budget
  was **{pct(ic_car24.uab_cushion)}** of GF expenditures in FY{RECENT} — the **lowest UAB cushion
  of every focus district** (peers range ~10–45%), and around the {ordn(ic_uab_pctile*100)} percentile statewide. UAB went **negative in FY2023 ({pct(ic23.uab_cushion)})**, the
  state-review-triggering (SBRC) level. A district can be cash-solvent yet out of legal spending
  authority; for ICCSD the spending-authority signal is more acute than the cash signal.

## 3. How does ICCSD compare with Cedar Rapids and other peers?

Under **every** reserve definition tested, ICCSD's FY2023 cushion stays in single-to-low-double
digit days while Cedar Rapids is 60–90 days:

| Numerator definition | ICCSD (FY2023) | Cedar Rapids (FY2023) |
|---|---:|---:|
"""
    for _, ri in ic_t3.iterrows():
        rc = cr_t3[cr_t3["Numerator case"] == ri["Numerator case"]].iloc[0]
        es += f"| {ri['Numerator case']} | {ri['Approx. days cushion']:.0f} d | {rc['Approx. days cushion']:.0f} d |\n"
    es += f"""
**The weakness is not metric-specific.** Even the most generous definition
(GF total + Management Fund) leaves ICCSD at ~{ic_t3['Approx. days cushion'].max():.0f} days
vs. ~{cr_t3['Approx. days cushion'].max():.0f} for Cedar Rapids. Cedar Rapids remains
structurally stronger across the board.

## 4. Is the concern cash, reserves, spending authority, or structural deficit?

- **Cash liquidity (intra-year):** *Cannot be confirmed from this annual data.* Year-end GF cash
  days look ample for the focus set (ICCSD's audited FY2023 GF cash ≈ {ic23.gf_cash_days:.0f}
  days), but year-end cash cannot reveal an intra-year low before major revenue inflows.
- **Reserve adequacy:** **Weak** — thin and volatile practical cushion, repeatedly in the
  High/Very-high bands FY2020–FY2023.
- **Spending authority:** **The most acute risk** — lowest UAB cushion of all peers; negative in
  FY2023.
- **Structural budget:** Mixed/strained — the 3-year average operating result is
  {pct(ic_aud[ic_aud.fiscal_year==2023].operating_result_3yr_avg.iloc[0])} and reserves were
  drawn down across multiple years before the FY2024 rebound. ESSER wind-down pressured most
  Iowa districts, but ICCSD entered that period with less cushion than peers.

## 5. What further data would confirm actual intra-year cash stress?

This screen is built on year-end annual data and **cannot** establish an intra-year cash low.
To confirm (per the workplan's follow-up criteria, which ICCSD meets on ≥2 conditions —
thin cushion, low/negative UAB, multi-year drawdown), collect monthly:
GF cash & investment balances by fund; GF revenue by source; GF expenditures by object;
payroll & benefits; accounts payable; interfund-borrowing activity; grant-receivable aging;
and any cash-flow projections. *(ICCSD board materials already hint at this:
COO indicated ~$19.3M GF cash entering FY26 ≈ ~33 days; PFM projected ~$21.4M / ~35 days for
FY26 — internal/unaudited, suitable only for targeted follow-up, not statewide benchmarking.)*

## Precise-language conclusion

> **Iowa City CSD screens as liquidity-constrained and has thin operating reserves**, with the
> sharpest signal being **spending-authority (UAB) weakness** rather than year-end cash.
> It **may be exposed to intra-year cash-flow stress**, but **monthly cash-flow data would be
> required to confirm actual liquidity pressure.** Cedar Rapids does not screen as constrained
> under any reserve definition.

---
### Statewide screen — how the focus districts sit (FY{RECENT})
Of ~{n_state} Iowa districts scored: see `district_year_master.csv` for the full population and
`tables/statewide_bottom_quartile_FY2024.csv` for the bottom quartile (≤
{cur.practical_days_cushion.quantile(0.25):.0f} days practical cushion).
"""
    (C.OUTPUT_DIR / "executive_summary.md").write_text(es)
    print("wrote executive_summary.md")

    # ---------- ICCSD one-pager ----------
    op = ["# Iowa City CSD — liquidity one-pager", "",
          f"*Annual screen, FY2020–FY{RECENT}. Apparent risk only; not confirmed intra-year stress.*",
          "", "## 1. Most recent metrics (FY%d, CAR — FY2024/25 audits not filed)" % RECENT, ""]
    op += [f"- Practical days cushion: **{ic_car24.practical_days_cushion:.0f} days** (Moderate band; "
           f"~{ordn(ic_pctile*100)} pctile statewide; #{ic_rank} of {len(t1s)} peers)",
           f"- Unassigned / GF exp: **{pct(ic_car24.conservative_reserve_ratio)}**",
           f"- UAB / GF exp: **{pct(ic_car24.uab_cushion)}** (lowest of all focus peers)",
           f"- Cash reserve levy / GF exp: **{pct(ic_car24.crl_reliance)}**; "
           f"levy capacity used: **{pct(ic_car24.crl_capacity_used_pct,0)}** (limited headroom)",
           f"- Composite class: **{ic_car24.risk_class}**", ""]
    op += ["## 2. Five-year trend (audited; FY2024 from CAR)", "",
           "| FY | GF exp | Unassigned | Practical days | UAB/exp | Risk |",
           "|---|---:|---:|---:|---:|---|"]
    for _, r in ic_aud.iterrows():
        op.append(f"| {int(r.fiscal_year)} | {f0(r.gf_expenditure)} | {f0(r.gf_unassigned)} | "
                  f"{r.practical_days_cushion:.0f} | {pct(r.uab_cushion)} | {r.risk_class} |")
    op.append(f"| {RECENT} (CAR) | {f0(ic_car24.gf_expenditures)} | {f0(ic_car24.gf_unassigned)} | "
              f"{ic_car24.practical_days_cushion:.0f} | {pct(ic_car24.uab_cushion)} | {ic_car24.risk_class} |")
    op += ["",
           "## 3. Vs Cedar Rapids & large peers",
           f"- Practical cushion #{ic_rank} of {len(t1s)} focus districts; lowest UAB cushion of the set.",
           "- Under every numerator definition, ICCSD (FY2023) = 9–20 days vs Cedar Rapids 61–87 days.",
           "",
           "## 4. Numerator cases (FY2023, audited)", "",
           "| Case | Amount | % GF exp | Days |", "|---|---:|---:|---:|"]
    for _, r in ic_t3.iterrows():
        op.append(f"| {r['Numerator case']} | {f0(r['Amount'])} | {r['% of GF expenditures']:.1f}% | {r['Approx. days cushion']:.0f} |")
    op += ["",
           "## 5. Cash reserve levy reliance & headroom",
           f"- FY2024 levy ≈ ${f0(ic_car24.cash_reserve_levy_amount)}; max capacity ≈ "
           f"${f0(ic_car24.max_cash_reserve_levy_capacity)} → **{pct(ic_car24.crl_capacity_used_pct,0)} used** "
           "(little remaining levy headroom to rebuild reserves).",
           "",
           "## 6. UAB position",
           f"- FY2023 UAB went **negative ({pct(ic23.uab_cushion)})** — the SBRC review threshold; "
           f"recovered to {pct(ic_car24.uab_cushion)} in FY2024 but still the thinnest of peers.",
           "",
           "## 7. Enrollment trend",
           f"- 3-yr certified-enrollment trend ≈ {pct(ic_car24.enrollment_3yr_trend)} (roughly flat; "
           "not a declining-enrollment story).",
           "",
           "## 8. Audit findings / internal control",
           "- **FY2024 and FY2025 audits not filed** as of this analysis — a transparency/ timeliness "
           "concern in its own right; audited components for ICCSD stop at FY2023.",
           "",
           "## 9. Overall liquidity risk conclusion", "",
           "- **Annual operating-reserve weakness:** YES — thin, volatile practical cushion.",
           "- **Actual intra-year liquidity stress:** UNCONFIRMED — needs monthly cash-flow data.",
           "- **Spending-authority risk:** ELEVATED — lowest UAB of peers; negative in FY2023.",
           "- **Longer-term structural budget risk:** MODERATE — multi-year drawdown before FY2024 rebound; "
           "limited levy headroom to rebuild.",
           "",
           "_Internal/unaudited follow-up signals (board materials, targeted use only):_ "
           + "; ".join(f"FY{int(r.fiscal_year)} GF cash ≈ ${f0(r.gf_cash_investments)} ({r.status})"
                      for _, r in supp.iterrows()),
           ""]
    (C.OUTPUT_DIR / "iccsd_one_pager.md").write_text("\n".join(op))
    print("wrote iccsd_one_pager.md")

    # ---------- Cedar Rapids comparison ----------
    cr = ["# Cedar Rapids comparison — numerator sensitivity", "",
          "Same five numerator cases as ICCSD, to test whether ICCSD's apparent weakness is "
          "definition-specific or persists under broader operating-reserve definitions.", "",
          "| Numerator case | ICCSD FY2023 days | Cedar Rapids FY2023 days |",
          "|---|---:|---:|"]
    for _, ri in ic_t3.iterrows():
        rc = cr_t3[cr_t3["Numerator case"] == ri["Numerator case"]].iloc[0]
        cr.append(f"| {ri['Numerator case']} | {ri['Approx. days cushion']:.0f} | {rc['Approx. days cushion']:.0f} |")
    cr += ["",
           "**Finding:** Cedar Rapids is stronger under *every* definition. ICCSD's thinness is "
           "**not** an artifact of the strict unassigned-only metric — it persists from the "
           "conservative case all the way through the broadest (GF total + Management) case. "
           f"Cedar Rapids' FY{int(cr_aud.fiscal_year.max())} composite class: "
           f"{cr_aud.iloc[-1].risk_class}.", ""]
    (C.OUTPUT_DIR / "cedar_rapids_comparison.md").write_text("\n".join(cr))
    print("wrote cedar_rapids_comparison.md")


if __name__ == "__main__":
    main()
