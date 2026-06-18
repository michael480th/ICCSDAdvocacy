"""
04_build_charts.py  -- the five required visuals (PNG, in output/charts/).
  1 scatter : practical days cushion vs UAB/GF exp, bubble=enrollment, color=risk
  2 bar     : practical days cushion by district, most-recent common FY (2024)
  3 trend   : practical days cushion by year, ICCSD vs Cedar Rapids + peers
  4 waterfall: ICCSD numerator sensitivity (FY2023)
  5 heatmap : districts x liquidity metric / risk flag
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import common as C

RECENT = C.COMMON_RECENT_FY
RISK_COLORS = {
    "Very high risk": "#b2182b", "High risk": "#ef8a62",
    "Moderate risk": "#fddbc7", "Low risk": "#67a9cf",
    "Unscored (insufficient component data)": "#cccccc",
}
BAND_LINES = [(10, "10d"), (20, "20d"), (45, "45d"), (75, "75d")]


def recent_focus():
    m = pd.read_csv(C.MASTER_CSV)
    codes = sorted(set(C.FOCUS15) | C.NAMED_FOCUS)
    return m[(m.fiscal_year == RECENT) & (m.district_code.isin(codes))].copy()


def short_name(n):
    return n.replace(" CSD", "").replace(" Community", "").replace(" Independent", "").replace(" (Prairie)", "")


# ---------------------------------------------------------------------------
def chart_scatter():
    m = pd.read_csv(C.MASTER_CSV)
    cur = m[(m.fiscal_year == RECENT) & m.practical_days_cushion.notna() & m.uab_cushion.notna()]
    foc = recent_focus()
    fig, ax = plt.subplots(figsize=(11, 7))
    # statewide backdrop
    ax.scatter(cur.practical_days_cushion, cur.uab_cushion * 100, s=12,
               color="#e0e0e0", alpha=0.6, label="All Iowa districts (FY2024)", zorder=1)
    # focus districts colored by risk
    for cls, g in foc.groupby("risk_class"):
        ax.scatter(g.practical_days_cushion, g.uab_cushion * 100,
                   s=(g.certified_enrollment.fillna(2000) / 25).clip(40, 800),
                   color=RISK_COLORS.get(cls, "#999"), edgecolor="black", linewidth=0.6,
                   alpha=0.9, label=cls, zorder=3)
    for _, r in foc.iterrows():
        ax.annotate(short_name(r.district_name_display),
                    (r.practical_days_cushion, r.uab_cushion * 100),
                    fontsize=7, xytext=(4, 4), textcoords="offset points")
    for x, lbl in BAND_LINES:
        ax.axvline(x, color="#bbbbbb", ls="--", lw=0.7)
    ax.set_xlabel("Practical days cushion ((assigned+unassigned) / GF exp. × 365)")
    ax.set_ylabel("UAB / GF expenditures (%)")
    ax.set_title("FY2024 liquidity screen: operating cushion vs. spending authority\n"
                 "(bubble size = enrollment; grey = all Iowa districts)")
    ax.axhline(0, color="#b2182b", lw=0.8)
    ax.legend(fontsize=7, loc="upper right")
    ax.set_xlim(left=0)
    fig.tight_layout()
    fig.savefig(C.CHARTS_DIR / "1_scatter_cushion_vs_uab.png", dpi=140)
    plt.close(fig)
    print("chart 1 scatter")


def chart_bar():
    foc = recent_focus().sort_values("practical_days_cushion")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [RISK_COLORS.get(c, "#999") for c in foc.risk_class]
    ax.barh([short_name(n) for n in foc.district_name_display],
            foc.practical_days_cushion, color=colors, edgecolor="black", linewidth=0.5)
    for x, lbl in BAND_LINES:
        ax.axvline(x, color="#888", ls="--", lw=0.7)
        ax.text(x, -0.7, lbl, fontsize=7, color="#666", ha="center")
    ax.set_xlabel("Practical days cushion")
    ax.set_title(f"Practical operating days cushion by district — FY{RECENT}\n"
                 "(assigned+unassigned GF balance ÷ GF expenditures × 365)")
    for i, v in enumerate(foc.practical_days_cushion):
        ax.text(v + 1, i, f"{v:.0f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(C.CHARTS_DIR / "2_bar_practical_days.png", dpi=140)
    plt.close(fig)
    print("chart 2 bar")


def chart_trend():
    f = pd.read_csv(C.FOCUS_CSV)
    m = pd.read_csv(C.MASTER_CSV)
    series = {
        "Iowa City CSD": 3141, "Cedar Rapids CSD": 1053,
        "Linn-Mar CSD": 3715, "Johnston CSD": 3231, "Davenport CSD": 1611,
    }
    fig, ax = plt.subplots(figsize=(10, 6))
    for name, code in series.items():
        g = f[f.district_code == code][["fiscal_year", "practical_days_cushion"]].dropna()
        if code == 3141:  # extend ICCSD with CAR FY2024 (audit missing)
            car = m[(m.district_code == 3141) & (m.fiscal_year == 2024)][["fiscal_year", "practical_days_cushion"]]
            g = pd.concat([g, car]).drop_duplicates("fiscal_year").sort_values("fiscal_year")
        lw = 3 if code == 3141 else 1.6
        ax.plot(g.fiscal_year, g.practical_days_cushion, marker="o",
                lw=lw, label=short_name(name))
    for y, lbl in BAND_LINES:
        ax.axhline(y, color="#ddd", ls="--", lw=0.7)
        ax.text(ax.get_xlim()[1], y, " " + lbl, fontsize=7, color="#888", va="center")
    ax.set_ylabel("Practical days cushion")
    ax.set_xlabel("Fiscal year")
    ax.set_title("Practical operating days cushion, FY2020–FY2024\n"
                 "(ICCSD bold; FY2024 ICCSD from CAR — audit not filed)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(C.CHARTS_DIR / "3_trend_practical_days.png", dpi=140)
    plt.close(fig)
    print("chart 3 trend")


def chart_waterfall():
    t3 = pd.read_csv(C.TABLES_DIR / "table3_numerator_sensitivity.csv")
    ic = t3[t3.District.str.startswith("Iowa City")]
    labels = ["GF\nunassigned", "+ assigned", "GF total\nfund bal.", "+ Management\n(on a+u)", "GF total\n+ Mgmt"]
    days = ic["Approx. days cushion"].tolist()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, days, color="#ef8a62", edgecolor="black", linewidth=0.5)
    for b, d in zip(bars, days):
        ax.text(b.get_x() + b.get_width() / 2, d + 0.4, f"{d:.1f}d", ha="center", fontsize=9)
    for y, lbl in BAND_LINES:
        ax.axhline(y, color="#bbb", ls="--", lw=0.7)
        ax.text(len(labels) - 0.4, y, " " + lbl, fontsize=7, color="#888", va="center")
    ax.set_ylabel("Approximate days cushion")
    ax.set_title("ICCSD numerator sensitivity (FY2023): cushion under each reserve definition\n"
                 "Even the broadest definition stays under ~20 days")
    fig.tight_layout()
    fig.savefig(C.CHARTS_DIR / "4_waterfall_iccsd_numerators.png", dpi=140)
    plt.close(fig)
    print("chart 4 waterfall")


def chart_heatmap():
    foc = recent_focus().sort_values("practical_days_cushion")
    metrics = {
        "Practical days\ncushion": "practical_days_cushion",
        "Unassigned /\nGF exp (%)": "conservative_reserve_ratio",
        "UAB /\nGF exp (%)": "uab_cushion",
        "CRL capacity\nused (%)": "crl_capacity_used_pct",
        "Operating\nresult (%)": "operating_result_pct",
        "Enrollment\n3yr trend (%)": "enrollment_3yr_trend",
        "Risk flag\ncount": "risk_flag_count",
    }
    names = [short_name(n) for n in foc.district_name_display]
    data = []
    for label, col in metrics.items():
        vals = foc[col].astype(float).values
        # normalize each metric 0..1 where 1 = worse; invert for "more is better" metrics
        v = vals.copy()
        if col in ("practical_days_cushion", "conservative_reserve_ratio", "uab_cushion",
                   "operating_result_pct", "enrollment_3yr_trend"):
            v = -v  # lower = worse -> higher score
        rng = np.nanmax(v) - np.nanmin(v)
        norm = (v - np.nanmin(v)) / rng if rng else np.zeros_like(v)
        data.append(norm)
    arr = np.array(data)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    im = ax.imshow(arr, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(list(metrics.keys()), fontsize=8)
    # annotate raw values
    for i, (label, col) in enumerate(metrics.items()):
        for j, (_, r) in enumerate(foc.iterrows()):
            val = r[col]
            if pd.isna(val):
                txt = "—"
            elif col in ("conservative_reserve_ratio", "uab_cushion", "crl_capacity_used_pct",
                         "operating_result_pct", "enrollment_3yr_trend"):
                txt = f"{val*100:.0f}"
            else:
                txt = f"{val:.0f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=7)
    ax.set_title(f"Liquidity metric heatmap — focus districts, FY{RECENT} "
                 "(red = relatively worse within this peer set)")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01, label="worse →")
    fig.tight_layout()
    fig.savefig(C.CHARTS_DIR / "5_heatmap_metrics.png", dpi=140)
    plt.close(fig)
    print("chart 5 heatmap")


def main():
    chart_scatter()
    chart_bar()
    chart_trend()
    chart_waterfall()
    chart_heatmap()


if __name__ == "__main__":
    main()
