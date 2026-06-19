#!/usr/bin/env python3
"""
Catalog of every KPI in the three-methodology benchmark, grouped into logical areas.

Single source of truth shared by build_kpi_dataset.py (computes the values) and
build_kpi_report.py (renders them) and the methodology appendix. Each KPI declares:
  key       - column name in data/kpi-three-methodologies.csv
  label     - human label
  group     - logical KPI area (see GROUPS)
  source    - which methodology defines it: Internal | Moody's | S&P | Shared | Context
  formula   - plain-English formula
  unit      - pct | days | ratio_pct | usd | usd_pp | number | x
  good      - 'up' higher-better, 'down' lower-better, 'context' neither
  target    - Iowa / methodology benchmark band (text)
  note      - caveats (e.g. per-capita vs per-pupil, reported vs adjusted)

Methodology factors that CANNOT be derived from audited financials (Moody's Resident
Income & Full-Value-per-Capita; S&P Economy & Management; income/GCP data) are listed in
QUALITATIVE so the report can name them as "external / not scored" rather than guess.
"""

GROUPS = [
    ("cash_liquidity",  "1. Cash & Liquidity",
     "Can the district pay its bills through the year? Cash on hand and short-term solvency."),
    ("reserves",        "2. Reserves & Fund Balance",
     "The financial cushion: available fund balance / reserves relative to the size of operations."),
    ("authority",       "3. Spending Authority (Iowa-specific)",
     "Iowa's binding legal constraint — Unspent Authorized Budget. Not in Moody's or S&P; the #1 ISFIS health indicator."),
    ("operating",       "4. Operating Performance",
     "Does the district live within its means? Margins, operating result, cost structure."),
    ("leverage",        "5. Leverage & Debt",
     "Long-term obligations (debt + pension + OPEB) and the annual fixed-cost burden they create."),
    ("economy_base",    "6. Economy & Tax Base",
     "Revenue-raising capacity: enrollment trend, property wealth, levy effort."),
    ("quality",         "7. Reporting Quality & Framework",
     "Can we trust the numbers, and what state framework do they operate in? Opinions, findings, timeliness."),
]

# good: up=higher better, down=lower better, context=neither
KPIS = [
 # ---- 1. Cash & Liquidity ----
 dict(key="days_net_cash", label="Day's Net Cash Ratio", group="cash_liquidity",
      source="Internal", unit="days", good="up", target="90–120 days (internal target 90)",
      formula="(GF cash + investments) / (total GF expenditures / 365)"),
 dict(key="moodys_net_cash_ratio", label="Net Cash Ratio", group="cash_liquidity",
      source="Moody's", unit="ratio_pct", good="up", target="Aaa ≥17.5% · A 5–10% · Ba 0–5% (Aaa endpoint 50%)",
      formula="GF net cash (cash+investments − short-term operating debt) / operating revenue"),
 dict(key="current_ratio", label="Current Ratio", group="cash_liquidity",
      source="Internal", unit="ratio_pct", good="up", target="≥100%",
      formula="GF current assets / (GF current liabilities + deferred inflows)"),
 dict(key="receivables_inventory_ratio", label="Receivables & Inventory Ratio", group="cash_liquidity",
      source="Internal", unit="ratio_pct", good="down", target="as low as possible",
      formula="(GF receivables + inventory) / GF current assets"),
 dict(key="creditor_equity_ratio", label="Creditor's Equity Ratio", group="cash_liquidity",
      source="Internal", unit="ratio_pct", good="down", target="0% (no short-term borrowing)",
      formula="ISCAP (cash-mgmt-program) restricted assets / GF current assets"),

 # ---- 2. Reserves & Fund Balance ----
 dict(key="solvency_ratio", label="Financial Solvency Ratio", group="reserves",
      source="Internal", unit="ratio_pct", good="up", target="5–10% target · ≤25% · <0% alert (Ehlers/ISCAP)",
      formula="(GF unassigned + assigned fund balance) / (GF revenue − AEA flow-through)"),
 dict(key="moodys_avail_fb_ratio", label="Available Fund Balance Ratio", group="reserves",
      source="Moody's", unit="ratio_pct", good="up", target="Aaa ≥17.5% · Aa 10–17.5% · A 5–10% · Baa 0–5%",
      formula="GF available fund balance (committed+assigned+unassigned) / operating revenue"),
 dict(key="sp_available_reserves_pct", label="Available Reserves % of Revenue", group="reserves",
      source="S&P", unit="ratio_pct", good="up", target="'1' >15% · '2' 8–15% · '3' 4–8% · '4' 1–4% · '5' <1%",
      formula="Available GF reserves (fund balance) / GF revenue"),
 dict(key="unrestricted_np_pp", label="Unrestricted Net Position / pupil", group="reserves",
      source="Shared", unit="usd_pp", good="up", target="negative is normal in Iowa (pension/OPEB driven)",
      formula="Government-wide governmental-activities unrestricted net position / certified enrollment"),

 # ---- 3. Spending Authority ----
 dict(key="uab_pct_of_max", label="Unspent Authorized Budget % of Max", group="authority",
      source="Internal", unit="ratio_pct", good="up", target="10–15% total · negative = unlawful → SBRC",
      formula="Unspent authorized budget / maximum authorized budget (Iowa DOM)"),
 dict(key="ubr_unrestricted_pct", label="Unrestricted Unspent Balance Ratio", group="authority",
      source="Internal", unit="ratio_pct", good="up", target=">5% (ISFIS)",
      formula="Unrestricted unspent spending authority / maximum budget authority (ICCSD report / DOM)"),

 # ---- 4. Operating Performance ----
 dict(key="operating_margin", label="Operating Margin (1-yr)", group="operating",
      source="Shared", unit="pct", good="context", target="persistent negative = spending above means",
      formula="(GF revenue − GF expenditure) / GF revenue"),
 dict(key="sp_oper_result_3yr", label="3-yr Avg Operating Result", group="operating",
      source="S&P", unit="pct", good="up", target="'1' >3% · '2' 0–3% · '3' −3–0% · '4' <−3%",
      formula="3-year average of (GF revenue − GF expenditure, net transfers) / GF revenue"),
 dict(key="employee_cost_ratio", label="Employee Cost Ratio", group="operating",
      source="Internal", unit="ratio_pct", good="context", target="75–85% (internal target <80%)",
      formula="(GF salaries + benefits) / total GF expenditures"),
 dict(key="foundation_aid_ratio", label="Foundation Aid Ratio", group="operating",
      source="Internal", unit="ratio_pct", good="context", target="no fixed target (falls as property wealth grows)",
      formula="Direct state foundation aid / total GF revenue"),
 dict(key="transportation_ratio", label="Student Transportation Ratio", group="operating",
      source="Internal", unit="ratio_pct", good="down", target="no fixed target",
      formula="Student transportation expenditure / total GF expenditures (CAR)"),
 dict(key="investment_income_ratio", label="Investment Income Ratio", group="operating",
      source="Internal", unit="ratio_pct", good="up", target="higher better",
      formula="GF interest/investment income / total GF revenue"),
 dict(key="gf_per_pupil", label="GF Expenditure per Pupil", group="operating",
      source="Internal", unit="usd_pp", good="context", target="efficiency context vs state avg",
      formula="Total GF expenditures / certified enrollment"),
 dict(key="local_share_pct", label="Local Revenue Share (Contribution)", group="operating",
      source="Internal", unit="ratio_pct", good="context", target="local taxation effort",
      formula="GF local-source revenue / total GF revenue"),

 # ---- 5. Leverage & Debt ----
 dict(key="moodys_ltl_ratio", label="Long-term Liabilities Ratio", group="leverage",
      source="Moody's", unit="ratio_pct", good="down", target="Aaa 125–250% · Aa 250–400% · A 400–550%",
      formula="(direct debt + net pension liab + net OPEB liab) / operating revenue",
      note="Uses REPORTED GASB NPL/OPEB, not Moody's discount-rate-adjusted ANPL/ANOPEB; operating revenue proxied by GF revenue."),
 dict(key="moodys_fixed_costs_ratio", label="Fixed-Costs Ratio", group="leverage",
      source="Moody's", unit="ratio_pct", good="down", target="Aaa 15–20% · Aa 20–25% · A 25–30%",
      formula="(implied 20-yr debt service + pension cost + OPEB contribution) / operating revenue",
      note="Implied debt service = prior-yr debt / 20-yr level annuity at the implied muni rate; pension cost uses actual contribution where tread-water not computable."),
 dict(key="sp_current_cost_pct", label="Current Cost % of Revenue", group="leverage",
      source="S&P", unit="ratio_pct", good="down", target="local govt '1' <8% · '2' 8–14% · '3' 14–20%",
      formula="(actual debt service P&I + pension contribution + OPEB contribution) / total governmental revenue",
      note="Uses ACTUAL debt service, so bond-refunding years spike (S&P removes such distortions). The Moody's Fixed-Costs Ratio above, built on implied 20-yr debt service, is the refunding-robust comparator."),
 dict(key="net_direct_debt_pp", label="Net Direct Debt / pupil", group="leverage",
      source="S&P", unit="usd_pp", good="down", target="S&P bands are per-CAPITA; shown per-pupil as proxy",
      formula="(GO bonds + sales-tax/SAVE revenue bonds + capital loan notes + leases) / certified enrollment",
      note="S&P scores net direct debt PER CAPITA (population). Population not in audits — per-pupil proxy shown, not mapped to the S&P band."),
 dict(key="npl_pp", label="Net Pension Liability / pupil", group="leverage",
      source="S&P", unit="usd_pp", good="down", target="S&P bands are per-CAPITA; shown per-pupil as proxy",
      formula="IPERS net pension liability (governmental activities) / certified enrollment",
      note="Per-capita in S&P; per-pupil proxy here."),
 dict(key="debt_per_pupil", label="Total Debt / pupil", group="leverage",
      source="Shared", unit="usd_pp", good="down", target="context",
      formula="(GO + SAVE/sales-tax revenue bonds + capital loan notes + leases) / certified enrollment"),

 # ---- 6. Economy & Tax Base ----
 dict(key="enrollment_cagr_3yr", label="Enrollment Trend (3-yr CAGR)", group="economy_base",
      source="Moody's", unit="pct", good="context", target="Aaa 2–4% · Aa 0–2% or >4% · A −2–0% (V-shaped: ~3% ideal)",
      formula="3-year compound annual growth rate of certified enrollment"),
 dict(key="valuation_per_pupil", label="Taxable Valuation per Pupil", group="economy_base",
      source="Context", unit="usd_pp", good="up", target="local revenue-raising capacity (PPEL/debt headroom)",
      formula="District taxable valuation / certified enrollment (Iowa DOM)"),
 dict(key="grand_total_levy_rate", label="Total Property Tax Rate", group="economy_base",
      source="Internal", unit="x", good="context", target="local taxation effort (per $1,000 valuation)",
      formula="Grand total district levy rate per $1,000 taxable valuation (Iowa DOM)"),

 # ---- 7. Reporting Quality & Framework ----
 dict(key="opinion_type", label="Audit Opinion", group="quality",
      source="Shared", unit="text", good="context", target="unmodified = clean",
      formula="Independent auditor's opinion type"),
 dict(key="findings_count", label="Audit Findings (count)", group="quality",
      source="Shared", unit="number", good="down", target="0 best; repeat findings weighted worse",
      formula="Count of internal-control / compliance findings in Schedule of Findings"),
 dict(key="repeat_finding", label="Repeat Finding", group="quality",
      source="Shared", unit="yn", good="down", target="N",
      formula="Any finding repeated from the prior year (not remediated)"),
 dict(key="report_lag_months", label="Audit Filing Lag", group="quality",
      source="Shared", unit="months", good="down", target="filed within statutory window (~3–6 mo)",
      formula="Months from fiscal year-end (June 30) to audit report date"),
 dict(key="data_basis", label="Data Basis", group="quality",
      source="Context", unit="text", good="context", target="audited > management/unaudited",
      formula="audited ACFR vs management/unaudited actual vs projected"),
]

# Methodology factors that cannot be computed from audited financials (named, not scored)
QUALITATIVE = [
 dict(methodology="Moody's", factor="Resident Income (MHI adj for RPP / US MHI)", weight="10%",
      reason="Needs Census ACS median household income + BEA regional price parity — external, not in audits."),
 dict(methodology="Moody's", factor="Full Value per Capita", weight="10%",
      reason="Needs district POPULATION (not enrollment). Valuation-per-pupil is shown instead as an Iowa-appropriate proxy."),
 dict(methodology="Moody's", factor="Institutional Framework", weight="10%",
      reason="Qualitative & identical statewide: Iowa is a STATE-DETERMINED revenue framework (foundation formula caps spending authority) with limited voter-approved local supplements (ISL, PPEL, SAVE). Analyst-assigned, same for all Iowa districts."),
 dict(methodology="S&P", factor="Economy (county GCP per capita, PCPI)", weight="20%",
      reason="Needs county gross product & per-capita personal income vs US — external macro data, not in audits."),
 dict(methodology="S&P", factor="Management", weight="20%",
      reason="Qualitative assessment of budgeting, long-term planning, policies — read from governance, not a single ratio."),
 dict(methodology="S&P", factor="Institutional Framework", weight="anchor",
      reason="S&P assigns an IF by state/government type; same for all Iowa school districts."),
]
