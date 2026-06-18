"""
02_compute_metrics.py
Add derived liquidity metrics and the preliminary risk score to:
  - district_year_master.csv  (statewide screen)
  - focus_peer_detail.csv     (15 audited districts; uses audited components & cash)

Overwrites those CSVs in place with the metric/risk columns appended.
Also writes statewide within-year percentile context used by peer-relative flags.
"""
import numpy as np
import pandas as pd

import common as C

DAYS = 365.0


def safe_div(a, b):
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    return a / b.where(b != 0)


# ---------------------------------------------------------------------------
# Derived metrics (shared formula set, applied to whichever frame is passed)
# ---------------------------------------------------------------------------
def add_core_metrics(df, *, unassigned, assigned_plus_unassigned, total_fb,
                     expenditures, management, cash=None, crl=None,
                     crl_max=None, uab=None, revenues=None, enrollment=None):
    g = df
    g["conservative_reserve_ratio"] = safe_div(g[unassigned], g[expenditures])
    g["practical_cushion_ratio"] = safe_div(g[assigned_plus_unassigned], g[expenditures])
    g["broad_cushion_ratio"] = safe_div(g[total_fb], g[expenditures])
    op_adj_num = pd.to_numeric(g[assigned_plus_unassigned], errors="coerce") + \
        pd.to_numeric(g[management], errors="coerce")
    g["operating_adjacent_ratio"] = safe_div(op_adj_num, g[expenditures])

    g["conservative_days_cushion"] = g["conservative_reserve_ratio"] * DAYS
    g["practical_days_cushion"] = g["practical_cushion_ratio"] * DAYS
    g["operating_adjacent_days_cushion"] = g["operating_adjacent_ratio"] * DAYS

    if cash is not None:
        g["gf_cash_days"] = safe_div(g[cash], pd.to_numeric(g[expenditures], errors="coerce") / DAYS)
    if crl is not None:
        g["crl_reliance"] = safe_div(g[crl], g[expenditures])
    if crl is not None and crl_max is not None:
        g["crl_capacity_used_pct"] = safe_div(g[crl], g[crl_max])
        g["crl_levy_headroom"] = pd.to_numeric(g[crl_max], errors="coerce") - \
            pd.to_numeric(g[crl], errors="coerce")
    if uab is not None:
        g["uab_cushion"] = safe_div(g[uab], g[expenditures])
    if revenues is not None:
        g["operating_result_pct"] = safe_div(
            pd.to_numeric(g[revenues], errors="coerce") - pd.to_numeric(g[expenditures], errors="coerce"),
            g[revenues])
    return g


def add_trend_metrics(df, code_col, fy_col, total_fb, revenues, expenditures, enrollment):
    """Per-district time-series metrics (3yr operating avg, drawdown streak, enrollment trend)."""
    df = df.sort_values([code_col, fy_col]).copy()
    out = []
    for code, g in df.groupby(code_col):
        g = g.sort_values(fy_col).copy()
        # 3-year average operating result
        g["operating_result_3yr_avg"] = g["operating_result_pct"].rolling(3, min_periods=2).mean()
        # consecutive-year fund-balance drawdown streak (years of decline up to & incl this row)
        fb = pd.to_numeric(g[total_fb], errors="coerce").values
        streak = [0] * len(fb)
        for i in range(1, len(fb)):
            if pd.notna(fb[i]) and pd.notna(fb[i - 1]) and fb[i] < fb[i - 1]:
                streak[i] = streak[i - 1] + 1
        g["fb_drawdown_years"] = streak
        # 3-year enrollment trend
        enr = pd.to_numeric(g[enrollment], errors="coerce")
        g["enrollment_3yr_trend"] = (enr - enr.shift(3)) / enr.shift(3)
        out.append(g)
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------
# Within-fiscal-year statewide percentiles (for peer-relative flags)
# ---------------------------------------------------------------------------
def add_year_percentiles(df, fy_col, cols):
    for col in cols:
        pct = (df.groupby(fy_col)[col]
               .rank(pct=True))
        df[col + "_pctile"] = pct
    return df


# ---------------------------------------------------------------------------
# Risk flags + composite classification
# ---------------------------------------------------------------------------
def cushion_band(days):
    if pd.isna(days):
        return None
    if days < 10:
        return "Very high"
    if days < 20:
        return "High"
    if days < 45:
        return "Moderate"
    if days < 75:
        return "Low"
    return "Very low"


def add_risk(df, *, has_audit_flags=False):
    # individual additive flags ------------------------------------------------
    df["flag_low_unrestricted"] = (
        df["conservative_reserve_ratio"] < 0.02).where(df["conservative_reserve_ratio"].notna(), other=pd.NA)
    df["flag_negative_operating"] = df["operating_result_pct"] < 0
    df["flag_multiyear_drawdown"] = df["fb_drawdown_years"] >= 2
    # weak spending authority: negative UAB, or bottom-quartile UAB cushion within year
    df["flag_weak_uab"] = (df["uab_cushion"] < 0) | (df.get("uab_cushion_pctile", pd.Series(np.nan, index=df.index)) <= 0.25)
    df["flag_declining_enrollment"] = df["enrollment_3yr_trend"] < -0.03
    df["flag_high_crl_reliance"] = df.get("crl_reliance_pctile", pd.Series(np.nan, index=df.index)) >= 0.75
    df["flag_limited_levy_headroom"] = df["crl_capacity_used_pct"] >= 0.90
    # not available statewide -> default False (documented as data gap)
    if "flag_special_ed_pressure" not in df:
        df["flag_special_ed_pressure"] = False
    if "flag_short_term_borrowing" not in df:
        df["flag_short_term_borrowing"] = False
    if not has_audit_flags:
        df["flag_audit_concern"] = False

    flag_cols = [
        "flag_low_unrestricted", "flag_negative_operating", "flag_multiyear_drawdown",
        "flag_weak_uab", "flag_declining_enrollment", "flag_high_crl_reliance",
        "flag_limited_levy_headroom", "flag_special_ed_pressure",
        "flag_short_term_borrowing", "flag_audit_concern",
    ]
    def is_flagged(v):
        if v is True:
            return True
        if v is False or v is None:
            return False
        try:
            if pd.isna(v):
                return False
        except (TypeError, ValueError):
            return False
        return v == 1

    df["risk_flag_count"] = df[flag_cols].map(is_flagged).sum(axis=1)

    df["cushion_band"] = df["practical_days_cushion"].apply(cushion_band)

    df["risk_class"], df["risk_rationale"] = zip(*df.apply(classify, axis=1))
    return df


def classify(r):
    band = r["cushion_band"]
    flags = r["risk_flag_count"]
    days = r["practical_days_cushion"]
    neg_uab = (r.get("uab_cushion") is not None) and pd.notna(r.get("uab_cushion")) and r["uab_cushion"] < 0
    bits = []
    if pd.notna(days):
        bits.append(f"{days:.0f}-day practical cushion")
    bits.append(f"{int(flags)} risk flag(s)")
    if neg_uab:
        bits.append("negative spending authority (UAB)")

    # Cushion band is the primary driver; flags escalate mainly when the
    # cushion is already thin. Negative spending authority (UAB) is treated as
    # an automatic High-risk floor regardless of cushion.
    if not isinstance(band, str):   # None or NaN -> no practical cushion available
        cls = "Unscored (insufficient component data)"
    elif band == "Very high" or (band == "High" and (neg_uab or flags >= 3)):
        cls = "Very high risk"
    elif band == "High" or neg_uab or (band == "Moderate" and flags >= 4):
        cls = "High risk"
    elif band == "Moderate" or (band == "Low" and flags >= 4):
        cls = "Moderate risk"
    else:
        cls = "Low risk"
    return cls, "; ".join(bits)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # ---- Statewide master --------------------------------------------------
    m = pd.read_csv(C.MASTER_CSV)
    m = add_core_metrics(
        m,
        unassigned="gf_unassigned",
        assigned_plus_unassigned="gf_assigned_plus_unassigned",
        total_fb="gf_total_fund_balance",
        expenditures="gf_expenditures",
        management="management_fund_balance",
        crl="cash_reserve_levy_amount",
        crl_max="max_cash_reserve_levy_capacity",
        uab="unspent_authorized_budget",
        revenues="gf_revenues",
    )
    m = add_trend_metrics(m, "district_code", "fiscal_year",
                          "gf_total_fund_balance", "gf_revenues", "gf_expenditures",
                          "certified_enrollment")
    m = add_year_percentiles(m, "fiscal_year",
                             ["practical_days_cushion", "uab_cushion", "crl_reliance"])
    m = add_risk(m, has_audit_flags=False)
    m = m.sort_values(["district_name_display", "fiscal_year"])
    m.to_csv(C.MASTER_CSV, index=False)
    print(f"master: {len(m)} rows; metrics+risk added")

    # ---- Focus 15 (audited components & cash) ------------------------------
    f = pd.read_csv(C.FOCUS_CSV)
    f["gf_assigned_plus_unassigned_aud"] = (
        pd.to_numeric(f["gf_unassigned"], errors="coerce").fillna(0)
        + pd.to_numeric(f["gf_assigned"], errors="coerce").fillna(0))
    # audit-derived flag
    f["flag_audit_concern"] = (
        (pd.to_numeric(f.get("material_weakness"), errors="coerce") > 0)
        | (pd.to_numeric(f.get("significant_deficiency"), errors="coerce") > 0)
        | (pd.to_numeric(f.get("repeat_finding"), errors="coerce") > 0))
    f = add_core_metrics(
        f,
        unassigned="gf_unassigned",
        assigned_plus_unassigned="gf_assigned_plus_unassigned_aud",
        total_fb="gf_total_fund_balance",
        expenditures="gf_expenditure",
        management="management_fund_balance",
        cash="cash_and_investments",
        crl="cash_reserve_levy_amount",
        crl_max="max_cash_reserve_levy_capacity",
        uab="unspent_authorized_budget",
        revenues="gf_revenue",
    )
    f = add_trend_metrics(f, "district_code", "fiscal_year",
                          "gf_total_fund_balance", "gf_revenue", "gf_expenditure",
                          "certified_enrollment")
    # peer-relative percentiles WITHIN the 15-district peer group
    f = add_year_percentiles(f, "fiscal_year",
                             ["practical_days_cushion", "uab_cushion", "crl_reliance"])
    f = add_risk(f, has_audit_flags=True)
    f = f.sort_values(["district", "fiscal_year"])
    f.to_csv(C.FOCUS_CSV, index=False)
    print(f"focus:  {len(f)} rows; metrics+risk added")


if __name__ == "__main__":
    main()
