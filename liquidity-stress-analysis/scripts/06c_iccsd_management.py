"""
06c_iccsd_management.py
Iowa City management/board disclosures (UNAUDITED) that corroborate intra-year
liquidity stress -- from the COO's FY26-FY28 Cash Flow Narrative (board packet
B.01.01, Apr 1 2026), as summarized in ../../iccsd-fmp-board-commentary.md.

Builds chart 7 (management's days-cash-on-hand projection). The borrowing table
and projection are consumed by 07_build_report.py from inputs/.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import common as C


def chart_cash_projection():
    p = pd.read_csv(C.INPUTS_DIR / "iccsd_management_cash_projection.csv")
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(p.fiscal_year, p.days_cash_on_hand, marker="o", lw=2.6, color="#b2182b")
    for _, r in p.iterrows():
        ax.annotate(f"{r.days_cash_on_hand:.1f}", (r.fiscal_year, r.days_cash_on_hand),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=10, fontweight="bold")
    ax.axhline(30, color="#d97706", ls="--", lw=1)
    ax.text(p.fiscal_year.max(), 30, " ~30d: tight", color="#d97706", va="bottom", ha="right", fontsize=9)
    ax.axhline(17, color="#b91c1c", ls="--", lw=1)
    ax.text(p.fiscal_year.max(), 17, " ~17d: alarming", color="#b91c1c", va="bottom", ha="right", fontsize=9)
    ax.set_ylim(0, max(40, p.days_cash_on_hand.max() + 6))
    ax.set_xticks(p.fiscal_year)
    ax.set_xticklabels([f"FY{int(y)}" for y in p.fiscal_year])
    ax.set_ylabel("Projected days of cash on hand")
    ax.set_title("Iowa City — management's own days-cash-on-hand projection\n"
                 "(COO FY26–FY28 Cash Flow Narrative, Apr 2026 — district projection, unaudited)")
    fig.tight_layout()
    fig.savefig(C.CHARTS_DIR / "7_iccsd_management_cash_projection.png", dpi=140)
    plt.close(fig)
    print("chart 7 iccsd management cash projection")


def main():
    chart_cash_projection()


if __name__ == "__main__":
    main()
