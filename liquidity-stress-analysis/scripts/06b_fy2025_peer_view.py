"""
06b_fy2025_peer_view.py
FY2025 is an AUDITED-PEER view only -- there is no statewide CAR or SBRC
cash-reserve-levy data for FY2025, so it cannot be a statewide screen.
This step adds:
  - output/tables/table5_fy2025_audited_peers.csv   (14 audited large districts)
  - output/iccsd_recent_cash.csv                    (ICCSD board/projected cash days)
  - output/charts/6_bar_fy2025_practical_days.png
Iowa City has no FY2025 audited row (its FY2024/FY2025 audits are not filed);
its own board figures are carried separately as cash days, NOT as a cushion.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import common as C

RISK_COLORS = {
    "Very high risk": "#b2182b", "High risk": "#ef8a62",
    "Moderate risk": "#fddbc7", "Low risk": "#67a9cf",
}


def short(n):
    return (n.replace(" CSD", "").replace(" Community", "").replace(" Independent", "")
            .replace(" (Prairie)", ""))


def dom_uab_fy2025():
    """State-computed (unaudited) UAB for FY2025 -- covers all 15 incl. Iowa City,
    so it works even where an audit is not filed. Returns {district: (uab, exp)}."""
    u = pd.read_csv(C.DOM_DIR / "unspent-authorized-budget.csv")
    u = u[u.fiscal_year == 2025]
    return {r.district: (r.unspent_authorized_budget, r.expenditures) for _, r in u.iterrows()}


def iccsd_board_cash(uab):
    supp = pd.read_csv(C.ICCSD_CASH_SUPP_CSV)
    supp["gf_cash_days"] = supp["gf_cash_investments"] / (supp["gf_expenditures"] / 365.0)
    supp["timing_note"] = [
        "start-of-FY26 cash (≈ intra-year low point), not a June-30 year-end figure",
        "FY26 projection (PFM Option 1)",
    ][: len(supp)]
    # attach the state's FY2025 UAB cushion for Iowa City (FY2026 UAB not yet computed)
    ic_uab, ic_exp = uab.get("Iowa City CSD", (None, None))
    supp["uab_cushion"] = [
        (ic_uab / ic_exp) if (ic_uab and ic_exp) else None,
        None,
    ][: len(supp)]
    out = supp[["district", "fiscal_year", "status", "gf_cash_investments",
                "gf_expenditures", "gf_cash_days", "uab_cushion", "timing_note", "source"]]
    out.to_csv(C.OUTPUT_DIR / "iccsd_recent_cash.csv", index=False)
    print("wrote iccsd_recent_cash.csv")
    return out


def fy2025_table(uab):
    f = pd.read_csv(C.FOCUS_CSV)
    s = f[f.fiscal_year == 2025].copy()
    # populate FY2025 UAB cushion from the DOM file (state-computed)
    s["uab_cushion"] = s.apply(
        lambda r: (uab[r["district"]][0] / uab[r["district"]][1])
        if r["district"] in uab and uab[r["district"]][1] else float("nan"), axis=1)
    t = s[[
        "district", "gf_expenditure", "conservative_reserve_ratio",
        "practical_days_cushion", "gf_cash_days", "operating_result_pct",
        "uab_cushion", "risk_class",
    ]].copy()
    t.columns = [
        "District", "GF expenditures", "GF unassigned / GF exp.",
        "Practical days cushion", "GF cash days", "Operating result",
        "UAB / GF exp.", "Risk class"]
    t = t.sort_values("Practical days cushion")

    # Iowa City FY2025 -- no filed audit, so cushion is unavailable, but the state's
    # UAB figure and the district's own board cash ARE available.
    ic_uab, ic_exp = uab.get("Iowa City CSD", (None, None))
    supp = pd.read_csv(C.ICCSD_CASH_SUPP_CSV)
    ic_cashdays = float("nan")
    s25 = supp[supp.fiscal_year == 2025]
    if not s25.empty:
        rr = s25.iloc[0]
        ic_cashdays = rr.gf_cash_investments / (rr.gf_expenditures / 365.0)
    ic_row = {
        "District": "Iowa City CSD", "GF expenditures": ic_exp,
        "GF unassigned / GF exp.": float("nan"), "Practical days cushion": float("nan"),
        "GF cash days": ic_cashdays, "Operating result": float("nan"),
        "UAB / GF exp.": (ic_uab / ic_exp) if (ic_uab and ic_exp) else float("nan"),
        "Risk class": "Audit not filed (UAB & board cash only)",
    }
    t = pd.concat([t, pd.DataFrame([ic_row])], ignore_index=True)
    t.to_csv(C.TABLES_DIR / "table5_fy2025_audited_peers.csv", index=False)
    print("wrote table5_fy2025_audited_peers.csv (incl. Iowa City UAB/cash row)")
    return s


def fy2025_chart(s):
    s = s.sort_values("practical_days_cushion")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [RISK_COLORS.get(c, "#999") for c in s.risk_class]
    bars = ax.barh([short(n) for n in s.district], s.practical_days_cushion,
                   color=colors, edgecolor="black", linewidth=0.5)
    for x, lbl in [(10, "10d"), (20, "20d"), (45, "45d"), (75, "75d")]:
        ax.axvline(x, color="#888", ls="--", lw=0.7)
        ax.text(x, -0.7, lbl, fontsize=7, color="#666", ha="center")
    ax.axvline(0, color="#000", lw=0.9)
    for i, v in enumerate(s.practical_days_cushion):
        ax.text(v + (1 if v >= 0 else -1), i, f"{v:.0f}",
                va="center", ha="left" if v >= 0 else "right", fontsize=8)
    ax.set_xlabel("Practical days cushion")
    ax.set_title("Practical operating days cushion — FY2025 (audited large peers)\n"
                 "No statewide data exists for FY2025; Iowa City's FY2025 audit is not filed")
    fig.tight_layout()
    fig.savefig(C.CHARTS_DIR / "6_bar_fy2025_practical_days.png", dpi=140)
    plt.close(fig)
    print("chart 6 fy2025 bar")


def main():
    uab = dom_uab_fy2025()
    iccsd_board_cash(uab)
    s = fy2025_table(uab)
    fy2025_chart(s)


if __name__ == "__main__":
    main()
