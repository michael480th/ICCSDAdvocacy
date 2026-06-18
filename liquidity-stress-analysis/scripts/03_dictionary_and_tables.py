"""
03_dictionary_and_tables.py
Deliverable 2 (data dictionary) and the four benchmarking tables.

Writes:
  output/data_dictionary.csv, output/data_dictionary.md
  output/tables/table1_recent_screen.csv
  output/tables/table2_five_year_trend.csv
  output/tables/table3_numerator_sensitivity.csv
  output/tables/table4_red_flags.csv
  output/tables/statewide_bottom_quartile_FY2024.csv
"""
import numpy as np
import pandas as pd

import common as C

RECENT = C.COMMON_RECENT_FY  # 2024

# ---------------------------------------------------------------------------
# Data dictionary
# ---------------------------------------------------------------------------
# (field, source, definition, formula, limitations, consistently_available)
DICTIONARY = [
    # identity
    ("district_code", "CAR (state 4-digit Dist)", "State district identifier", "", "", "Yes (all)"),
    ("district_name / district_name_display", "CAR / canonical", "Official district name", "", "", "Yes (all)"),
    ("fiscal_year", "All", "Actual fiscal year of the financial position (year ended June 30)", "", "SBRC levy files are labelled by budget year = actual_year+2; remapped to actual year here", "Yes (all)"),
    ("certified_enrollment", "DOM/DE UAB workbook (x249); audited file for the 15", "Budget/funding certified enrollment", "", "DOM x249 differs ~1-3% from audited certified enrollment (definition/lag)", "Yes (statewide FY2017+)"),
    # GF raw
    ("gf_revenues / gf_revenue", "CAR (statewide); audited (15)", "Annual General Fund revenues", "", "", "Yes (FY2017+)"),
    ("gf_expenditures / gf_expenditure", "CAR (statewide); audited (15)", "Annual General Fund expenditures (primary denominator)", "", "", "Yes (FY2017+)"),
    ("gf_total_fund_balance", "CAR (statewide); audited (15)", "Ending GF fund balance", "", "", "Yes (FY2017+)"),
    ("gf_unassigned", "CAR (statewide FY2023-24 only); audited (15, FY2020-25)", "GF unassigned fund balance", "", "Statewide split available only FY2023-24; otherwise only the assigned+unassigned SUM is available", "Statewide: FY2023-24. 15 districts: FY2020-25"),
    ("gf_assigned", "CAR (statewide FY2023-24); audited (15)", "GF assigned fund balance", "", "Same limitation as gf_unassigned", "Partial"),
    ("gf_assigned_plus_unassigned", "CAR split (FY2023-24) else SBRC combined (FY2020-24)", "Practical operating numerator (assigned + unassigned)", "gf_assigned + gf_unassigned", "Source noted in assigned_unassigned_source; statewide available FY2020-2024", "Statewide FY2020-2024"),
    ("assigned_unassigned_source", "derived", "Which source supplied the practical numerator", "", "", "Yes"),
    ("gf_cash_and_investments / cash_and_investments", "Audited ACFR (15 only)", "GF cash and investments at year end", "", "Not available statewide; year-end snapshot only (not an intra-year low)", "15 districts only"),
    # other funds
    ("management_fund_balance", "CAR", "Management Fund ending balance", "", "May be legally restricted; treat operating-adjacent case as secondary", "Yes (FY2017+, gaps in FY2024)"),
    ("ppel_fund_balance", "CAR", "PPEL Fund ending balance", "", "Capital; NOT operating liquidity", "Yes"),
    ("save_fund_balance", "CAR ('Sales Tax')", "SAVE / statewide penny capital projects balance", "", "Capital; NOT operating liquidity", "Yes"),
    ("other_capital_projects_balance", "CAR", "Other Capital Projects ending balance", "", "Capital; NOT operating liquidity", "Yes"),
    ("debt_service_fund_balance", "CAR", "Debt Service Fund ending balance", "", "Restricted; NOT operating liquidity", "Yes"),
    ("total_governmental_fund_balance", "CAR (sum of governmental funds)", "Total governmental fund balance", "sum of General, Management, PPEL, PERL, Debt Service, Sales Tax, Other Capital Projects, Activity, Emergency/Disaster, Entrepreneurial/Reorg (excludes Enterprise & Nutrition)", "Approximation by summing CAR funds; do NOT use as operating liquidity", "Yes"),
    # levy / SBRC
    ("cash_reserve_levy_amount", "SBRC Final Cash Reserve Levies (Final Cash Reserve Levy)", "Cash reserve levy certified (for budget year actual_year+2)", "", "2-year lag between the actuals year and the levy budget year (see cash_reserve_levy_budget_fy)", "Statewide FY2020-2024"),
    ("max_cash_reserve_levy_capacity", "SBRC (Final Maximum Cash Reserve Levy)", "State-computed maximum cash reserve levy the district could certify", "", "", "Statewide FY2020-2024"),
    ("sbrc_20pct_cap", "SBRC (20% of Expenditures)", "20% of prior-year GF expenditures (statutory reference cap)", "", "", "Statewide FY2020-2024"),
    ("cash_reserve_levy_budget_fy", "derived", "Budget fiscal year the certified levy applies to", "actual_year + 2", "", "Yes (where levy present)"),
    # DOE
    ("unspent_authorized_budget", "DOE/DOM UAB workbook", "Year-end unspent authorized (spending-authority) budget", "", "State-computed, unaudited; exists even when audit is missing", "Statewide FY2017+"),
    ("uab_per_pupil", "DOE/DOM UAB workbook", "UAB per certified pupil", "UAB / enrollment", "", "Statewide FY2017+"),
    # audited extras
    ("solvency_ratio_pct", "Audited (ISFIS definition)", "Solvency ratio", "", "15 districts only", "15 districts"),
    ("operating_margin_pct", "Audited", "GF operating margin", "", "15 districts only", "15 districts"),
    ("findings_count / material_weakness / significant_deficiency / repeat_finding", "Audited ACFR", "Audit finding indicators", "", "15 districts only; ICCSD missing FY2024-25 audits", "15 districts"),
    # derived metrics
    ("conservative_reserve_ratio", "derived (Metric 1)", "Narrowest operating cushion", "gf_unassigned / gf_expenditures", "Needs unassigned split (statewide FY2023-24 only)", "Partial"),
    ("practical_cushion_ratio", "derived (Metric 2, PRIMARY)", "Practically available operating reserve ratio", "(gf_assigned + gf_unassigned) / gf_expenditures", "", "Statewide FY2020-2024"),
    ("broad_cushion_ratio", "derived (Metric 3)", "Total GF balance vs operating scale", "gf_total_fund_balance / gf_expenditures", "May overstate available liquidity", "Yes (FY2017+ where exp present)"),
    ("operating_adjacent_ratio", "derived (Metric 4)", "Operating-adjacent cushion incl. Management Fund", "(gf_assigned + gf_unassigned + management_fund_balance) / gf_expenditures", "Management Fund may be restricted; secondary case", "Statewide FY2020-2024"),
    ("conservative_days_cushion / practical_days_cushion / operating_adjacent_days_cushion", "derived (Metric 5)", "Approximate days of cushion", "ratio * 365", "Year-end proxy; not an intra-year low", "As per underlying ratio"),
    ("gf_cash_days", "derived (Metric 6)", "Approximate raw cash days on hand", "gf_cash_and_investments / (gf_expenditures / 365)", "Cash != usable liquidity; 15 districts only", "15 districts"),
    ("crl_reliance", "derived (Metric 7)", "Cash reserve levy reliance", "cash_reserve_levy_amount / gf_expenditures", "", "Statewide FY2020-2024"),
    ("crl_capacity_used_pct", "derived (Metric 7)", "Share of maximum cash reserve levy used", "cash_reserve_levy_amount / max_cash_reserve_levy_capacity", "Near 1.0 = limited levy headroom", "Statewide FY2020-2024"),
    ("crl_levy_headroom", "derived", "Remaining cash reserve levy capacity ($)", "max_cash_reserve_levy_capacity - cash_reserve_levy_amount", "", "Statewide FY2020-2024"),
    ("uab_cushion", "derived (Metric 8)", "Spending-authority cushion", "unspent_authorized_budget / gf_expenditures", "Spending authority, NOT cash", "Statewide FY2017+"),
    ("operating_result_pct", "derived (Metric 9)", "Current-year structural operating result", "(gf_revenues - gf_expenditures) / gf_revenues", "", "Yes"),
    ("operating_result_3yr_avg", "derived (Metric 9)", "3-year average operating result", "rolling mean of operating_result_pct", "", "Yes (>=2 yrs)"),
    ("enrollment_3yr_trend", "derived (Metric 10)", "3-year certified enrollment change", "(enr - enr_lag3) / enr_lag3", "Needs 3 prior years", "Yes (FY2020+)"),
    ("fb_drawdown_years", "derived", "Consecutive years of GF fund-balance decline", "", "", "Yes"),
    # risk
    ("flag_* (10 flags)", "derived (Risk Scoring)", "Additive risk flags", "see executive summary / README", "Special-ed pressure & short-term borrowing not available statewide (default False); audit concern is 15-districts only", "Mixed"),
    ("risk_flag_count", "derived", "Count of additive risk flags fired", "", "Peer-relative flags use within-year percentiles", "Yes"),
    ("cushion_band", "derived", "Practical-days-cushion risk band", "0-10 VeryHigh / 10-20 High / 20-45 Moderate / 45-75 Low / 75+ VeryLow", "", "Where practical cushion available"),
    ("risk_class", "derived", "Composite liquidity risk classification", "explainable rule: cushion band primary, flags & negative UAB escalate", "Apparent (annual-screen) risk, not confirmed intra-year stress", "Where scored"),
    ("risk_rationale", "derived", "Plain-language explanation of the class", "", "", "Where scored"),
]


def write_dictionary():
    dd = pd.DataFrame(DICTIONARY, columns=[
        "field", "source", "definition", "formula", "limitations", "consistently_available"])
    dd.to_csv(C.OUTPUT_DIR / "data_dictionary.csv", index=False)
    lines = ["# Data dictionary — Iowa liquidity stress benchmarking", "",
             "One row per district per fiscal year. Two datasets share these fields:",
             "`district_year_master.csv` (statewide screen, FY2017-2024) and "
             "`focus_peer_detail.csv` (15 audited districts, FY2020-2025).", ""]
    lines.append("| Field | Source | Definition | Formula | Limitations | Consistently available |")
    lines.append("|---|---|---|---|---|---|")
    for row in DICTIONARY:
        lines.append("| " + " | ".join(str(x).replace("|", "/") for x in row) + " |")
    (C.OUTPUT_DIR / "data_dictionary.md").write_text("\n".join(lines))
    print("wrote data_dictionary.csv / .md")


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def focus_recent_frame():
    """FY2024 screen for all focus districts, sourced consistently from the
    statewide master (CAR/SBRC/UAB), augmented with audited cash days."""
    m = pd.read_csv(C.MASTER_CSV)
    f = pd.read_csv(C.FOCUS_CSV)
    codes = sorted(set(C.FOCUS15) | C.NAMED_FOCUS)
    cur = m[(m.fiscal_year == RECENT) & (m.district_code.isin(codes))].copy()
    cashdays = f[f.fiscal_year == RECENT][["district_code", "gf_cash_days"]]
    cur = cur.merge(cashdays, on="district_code", how="left")
    return cur


def table1():
    cur = focus_recent_frame()
    t = cur[[
        "district_name_display", "conservative_reserve_ratio", "practical_cushion_ratio",
        "practical_days_cushion", "gf_cash_days", "crl_reliance", "uab_cushion", "risk_class",
    ]].copy()
    t.columns = [
        "District", "GF unassigned / GF exp.", "GF (assigned+unassigned) / GF exp.",
        "Practical days cushion", "GF cash days", "Cash reserve levy / GF exp.",
        "UAB / GF exp.", "Risk class"]
    t = t.sort_values("Practical days cushion")
    t.to_csv(C.TABLES_DIR / "table1_recent_screen.csv", index=False)
    print("wrote table1_recent_screen.csv")
    return t


def table2():
    f = pd.read_csv(C.FOCUS_CSV)
    m = pd.read_csv(C.MASTER_CSV)
    rows = f[[
        "district", "fiscal_year", "gf_expenditure", "gf_unassigned",
        "gf_assigned_plus_unassigned_aud", "practical_days_cushion",
        "uab_cushion", "certified_enrollment", "risk_class",
    ]].rename(columns={
        "gf_expenditure": "gf_expenditures",
        "gf_assigned_plus_unassigned_aud": "gf_assigned_plus_unassigned"})
    # ICCSD: append CAR-sourced FY2024 (audit missing) for trend completeness.
    ic = m[(m.district_code == 3141) & (m.fiscal_year.isin([2024]))][[
        "fiscal_year", "gf_expenditures", "gf_unassigned",
        "gf_assigned_plus_unassigned", "practical_days_cushion",
        "uab_cushion", "certified_enrollment", "risk_class"]].copy()
    ic.insert(0, "district", "Iowa City CSD")
    ic["_src"] = "CAR (audit missing)"
    rows["_src"] = "Audited"
    out = pd.concat([rows, ic], ignore_index=True).sort_values(["district", "fiscal_year"])
    out.to_csv(C.TABLES_DIR / "table2_five_year_trend.csv", index=False)
    print("wrote table2_five_year_trend.csv")
    return out


def numerator_sensitivity(code, label, fy):
    """Table 3: numerator cases for a district at a given fiscal year."""
    f = pd.read_csv(C.FOCUS_CSV)
    row = f[(f.district_code == code) & (f.fiscal_year == fy)]
    if row.empty:
        return None
    r = row.iloc[0]
    exp = r["gf_expenditure"]
    una = r["gf_unassigned"]
    asn = r.get("gf_assigned", 0) or 0
    au = (una or 0) + (asn or 0)
    tot = r["gf_total_fund_balance"]
    mgmt = r.get("management_fund_balance") or 0
    totgov = r.get("total_governmental_fund_balance") or 0
    cases = [
        ("GF unassigned only", una),
        ("GF assigned + unassigned", au),
        ("GF total fund balance", tot),
        ("GF assigned + unassigned + Management", au + mgmt),
        ("GF total + Management", tot + mgmt),
    ]
    out = []
    for name, amt in cases:
        pct = (amt / exp) if (pd.notna(amt) and exp) else np.nan
        out.append({
            "District": label, "Fiscal year": fy, "Numerator case": name,
            "Amount": amt, "% of GF expenditures": round(pct * 100, 2) if pd.notna(pct) else np.nan,
            "Approx. days cushion": round(pct * 365, 1) if pd.notna(pct) else np.nan,
        })
    return pd.DataFrame(out)


def table3():
    # most recent audited year for each
    f = pd.read_csv(C.FOCUS_CSV)
    parts = []
    for code, label in [(3141, "Iowa City CSD"), (1053, "Cedar Rapids CSD")]:
        elig = f[(f.district_code == code) & f["gf_unassigned"].notna()
                 & f["management_fund_balance"].notna()]
        fy = int(elig.fiscal_year.max())
        parts.append(numerator_sensitivity(code, f"{label} (FY{fy}, audited)", fy))
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(C.TABLES_DIR / "table3_numerator_sensitivity.csv", index=False)
    print("wrote table3_numerator_sensitivity.csv")
    return out


def table4():
    cur = focus_recent_frame()
    t = cur[[
        "district_name_display", "flag_low_unrestricted", "flag_negative_operating",
        "flag_declining_enrollment", "flag_weak_uab", "flag_high_crl_reliance",
        "flag_short_term_borrowing", "risk_class",
    ]].copy()
    t.columns = [
        "District", "Reserve thinness", "Operating deficit", "Enrollment decline",
        "UAB weakness", "Cash reserve reliance", "Short-term borrowing", "Overall concern"]
    t = t.sort_values("District")
    t.to_csv(C.TABLES_DIR / "table4_red_flags.csv", index=False)
    print("wrote table4_red_flags.csv")
    return t


def statewide_bottom_quartile():
    m = pd.read_csv(C.MASTER_CSV)
    cur = m[(m.fiscal_year == RECENT) & m.practical_days_cushion.notna()].copy()
    q = cur.practical_days_cushion.quantile(0.25)
    bq = cur[cur.practical_days_cushion <= q].sort_values("practical_days_cushion")
    bq = bq[[
        "district_name_display", "practical_days_cushion", "conservative_reserve_ratio",
        "uab_cushion", "crl_capacity_used_pct", "risk_flag_count", "risk_class",
        "is_named_focus", "is_focus15"]]
    bq.to_csv(C.TABLES_DIR / "statewide_bottom_quartile_FY2024.csv", index=False)
    print(f"wrote statewide_bottom_quartile_FY2024.csv (25th pctile = {q:.1f} days, n={len(bq)})")
    return bq


def main():
    write_dictionary()
    table1()
    table2()
    table3()
    table4()
    statewide_bottom_quartile()


if __name__ == "__main__":
    main()
