# Iowa School District Liquidity Stress Benchmarking

A **self-contained** analysis of Iowa school-district intra-year liquidity resilience.

> **This folder is deliberately separate from the rest of the repo.** It only *reads* the
> shared raw / cleansed data (`../data`, `../CAR`, `../FinalCashReserveLevies`, `../UAB`) and
> writes everything under `output/`. **Nothing here is wired into the public GitHub Pages site**
> (`../index.html` and friends) and nothing in the existing site was changed.

## The question

> For each Iowa district: does it have enough usable operating cushion to manage intra-year
> cash-flow volatility (payroll, benefits, vendors) before major revenue inflows arrive?

Because monthly cash data isn't consistently available statewide, this is an **annual proxy
screen**. It classifies *apparent* liquidity risk; it does **not** assert confirmed intra-year
cash stress (which needs monthly cash-flow data — see the executive summary).

## Two populations

| Dataset | Coverage | Source | What it powers |
|---|---|---|---|
| `output/district_year_master.csv` | ~330 districts/yr, **FY2017–2024** | CAR fund balances + SBRC Final Cash Reserve Levy files + DOE/DOM UAB workbook | The scalable statewide screen, percentiles, bottom-quartile flagging |
| `output/focus_peer_detail.csv` | 15 large audited districts, **FY2020–2025** | Audited ACFRs (`../data/iowa-district-financials.csv`) + DOM | Full derived metrics, cash days, audit findings, ICCSD & Cedar Rapids deep dives |

**Key data reality:** the assigned/unassigned *split* is only in CAR for FY2023–2024, but the SBRC
cash-reserve-levy files provide the **assigned+unassigned sum statewide for FY2020–FY2024**, which
is exactly the "practical" numerator. GF cash & investments and audit findings exist only for the
15 audited districts. ICCSD's FY2024–FY2025 audits are not filed, so its recent components come
from CAR. All of this is documented per-field in `output/data_dictionary.md`.

## Metrics (per the workplan)

Primary: **Practical days cushion** = (GF assigned + unassigned) ÷ GF expenditures × 365.
Also computed: conservative (unassigned-only) and operating-adjacent (+Management) cushions and
their day-equivalents; GF cash days; cash-reserve-levy reliance & headroom; UAB (spending-
authority) cushion; current & 3-yr operating result; 3-yr enrollment trend.

**Risk bands** (practical days cushion): 0–10 Very high · 10–20 High · 20–45 Moderate ·
45–75 Low · 75+ Very low. Ten additive flags (some peer-relative) escalate the band; negative
UAB is a High-risk floor. The composite class is explainable, not purely mechanical — every row
carries a `risk_rationale`. Logic lives in `scripts/02_compute_metrics.py`.

Capital balances (SAVE/Sales Tax, PPEL, Other Capital Projects, Debt Service) and total
governmental fund balance are **carried for context only** and never used as operating liquidity.

## Deliverables (`output/`)

- `district_year_master.csv`, `focus_peer_detail.csv` — the datasets (Deliverable 1)
- `data_dictionary.csv` / `.md` — Deliverable 2
- `liquidity_benchmark_workbook.xlsx` — Deliverable 3 (raw, derived, comparison, ICCSD, Cedar
  Rapids, risk scoring, charts tabs)
- `executive_summary.md`, `iccsd_one_pager.md`, `cedar_rapids_comparison.md` — Deliverable 4
- `liquidity-stress-report.html` — a single self-contained, general-audience report (plain
  language + real terminology; charts embedded). **Standalone — not linked into the public site.**
- `tables/table1..4_*.csv` + `statewide_bottom_quartile_FY2024.csv`
- `tables/table5_fy2025_audited_peers.csv` + `iccsd_recent_cash.csv` — the **FY2025** audited
  large-peer view (no statewide data exists for FY2025) and Iowa City's own FY25/FY26 board cash
- `charts/1..6_*.png` — scatter, peer bar, trend, ICCSD numerator waterfall, heatmap, FY2025 bar

### Iowa City management disclosures (the one place we move past "apparent")
`inputs/iccsd_short_term_borrowing.csv` and `inputs/iccsd_management_cash_projection.csv` capture the
COO's FY26–FY28 Cash Flow Narrative (board packet B.01.01, Apr 1 2026, **unaudited district
projections**), as summarized in `../iccsd-fmp-board-commentary.md`: a $10M interfund loan (Aug 2025,
GF cash < $6M / ~10 days), a $3M revenue anticipation warrant for the Mar 15 2026 payroll, a proposed
$25M warrant (May 2026), and a days-cash projection of 36.6 → 23.2 → 16.9 (FY26→FY28). Per the
workplan's Final Interpretation Standard (short-term borrowing **or** management disclosure), this is
enough to call Iowa City's intra-year stress **documented** — for Iowa City only, on unaudited figures,
used strictly as targeted follow-up. It does not change any other district's classification or the
statewide screen.

### A note on FY2025 / FY2026
The statewide files (CAR, SBRC cash-reserve-levy) only run through **FY2024**, so FY2025 cannot be a
statewide screen. The 15 large districts' **audited** FY2025 reports are in, so FY2025 is presented as
an audited large-peer view. **Iowa City's FY2024 and FY2025 audits are not filed**, so it has no FY2025
reserve cushion — but the state's audit-independent **UAB** (FY2025 ≈ 2.4%, still lowest of the 15) and
the district's own board **cash** figures (~33 days at the start of FY2026, ~35 projected) are carried
separately and clearly labeled as unaudited. New FY2025 signal: **Waterloo's** unassigned balance went
**negative** (−17 days).

## Regenerate

```bash
pip install pandas openpyxl matplotlib
python3 scripts/run_all.py          # runs steps 01–06 in order
```

## Headline finding

Iowa City CSD screens as **liquidity-constrained / thin on operating reserves** — ~27 practical
days in FY2024 (3rd-thinnest of the large peers; ~11th percentile statewide), and 9–23 days
FY2020–FY2023. The sharper signal is **spending authority (UAB)**: the lowest of any focus peer
and **negative in FY2023**. The weakness is **not** an artifact of the strict unassigned metric —
it persists under every broader reserve definition, whereas Cedar Rapids stays at 60–90 days
under all of them. Confirming *actual* intra-year cash stress would require monthly cash-flow data.
