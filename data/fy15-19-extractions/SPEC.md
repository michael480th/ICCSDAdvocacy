# FY2015–FY2019 audit extraction spec

Goal: extend the repo's detailed financial schema back to FY2015–FY2019 for one district, by
reading that district's audited ACFR / annual financial report PDFs in `auditreports/`.
We already have FY2020–FY2025 in `data/iowa-district-financials.csv` and
`data/district-extractions/` + `data/notes-extractions/`. Match those formats and conventions.

The backbone GF figures (revenues, expenditures, fund balance classes, cash) for FY2015–FY2023
already exist in `data/audit-financials.csv` — you do NOT need to re-extract those, but DO read
them as a cross-check and to confirm you are on the right statement.

## House rules (critical — same discipline as the rest of the repo)
- Every figure must trace to a specific statement + page in the specific PDF. Put page refs in `notes`.
- Iowa audits report GOVERNMENTAL-ACTIVITIES (government-wide) AND fund statements. Pull each field
  from the correct one (see per-field source below). Use the General Fund column on fund statements.
- A negative number in parentheses `(1,234)` is negative. `-` means 0.
- **Never guess or interpolate.** If a field is not in that year's report, leave it blank and say so
  in `notes`. A blank honest cell beats a wrong number. Set `confidence` = High / Medium / Low.
- Numbers are whole dollars (no `$`, no commas) in the CSV. Percentages as plain numbers (e.g. 7.03).
- Watch for **restatements**: if beginning net position / fund balance was restated, note it.

## Tooling
Use Python + PyMuPDF (`import fitz`). Dump page text with `page.get_text()`. Search for statement
titles ("Statement of Net Position", "Balance Sheet — Governmental Funds", "Statement of Revenues,
Expenditures and Changes in Fund Balances", "Notes to Financial Statements", capital-asset note,
long-term-debt note, pension note, OPEB note, "Schedule of Findings"). Read the General Fund column.
Cross-check totals against `data/audit-financials.csv` for that district-year.

## Output files (create these two, semicolon... no — use the delimiters below)
1. `data/fy15-19-extractions/<DistrictKey>.csv` — pipe `|` delimited, columns EXACTLY:

district|fiscal_year|auditor|report_date|opinion_type|certified_enrollment|gf_revenue|gf_expenditure|gf_total_fund_balance|gf_unassigned|gf_assigned|gf_committed|aea_flowthrough|state_aid_direct|interest_income|salaries_benefits|gf_current_assets|gf_receivables|gf_inventory|gf_prepaid|gf_current_liabilities|gf_deferred_inflows|iscap_restricted_assets|cash_and_investments|go_debt_outstanding|capital_loan_notes|save_rev_bonds|lease_sbita|annual_debt_service|capital_additions|depreciation|construction_in_progress|save_revenue|unrestricted_net_position|ipers_npl|opeb_liability|pension_contribution|opeb_contribution|findings_count|material_weakness|significant_deficiency|repeat_finding|single_audit_findings|gfoa_cert|confidence|notes

2. `data/fy15-19-notes/<DistrictKey>.csv` — pipe `|` delimited, columns EXACTLY:

district|fiscal_year|total_assets|total_deferred_outflows|total_liabilities|total_deferred_inflows|net_invest_capital_assets|restricted_net_position|unrestricted_net_position|total_net_position|gross_capital_assets|accumulated_depreciation|construction_commitments|debt_service_next_fy|total_future_debt_service|notes

Write one row per fiscal year you have a PDF for (FY2015–FY2019). `<DistrictKey>` = the district
name with spaces→underscores, e.g. `Iowa_City_CSD`, `West_Des_Moines_CSD`, `College_CSD`.

## Field-by-field source guide
- auditor / report_date (YYYY-MM-DD) / opinion_type (unmodified/qualified/adverse/disclaimer): Independent Auditor's Report.
- certified_enrollment: MD&A or statistical/operating section (official Oct count). Number like 14285.1.
- gf_revenue, gf_expenditure, gf_total_fund_balance, gf_unassigned, gf_assigned, gf_committed: GF column of the Statement of Revenues, Expenditures & Changes in Fund Balances + Balance Sheet — Governmental Funds. (Cross-check vs audit-financials.csv.)
- aea_flowthrough: AEA flow-through / "Area Education Agency flow through" expenditure (GF) — used in solvency denominator; often a single expenditure line. If not separable, blank + note.
- state_aid_direct: GF "State sources" → foundation/state aid revenue line (the direct state aid). For foundation-aid ratio.
- interest_income: GF "interest"/"investment earnings" revenue line.
- salaries_benefits: only if the GF statement (or a schedule) breaks out salaries+benefits at the object level. Most Iowa ACFRs report by FUNCTION, not object — if so, leave blank + note "not object-level in GF".
- gf_current_assets / gf_receivables / gf_inventory / gf_prepaid / gf_current_liabilities / gf_deferred_inflows: GF column, Balance Sheet — Governmental Funds. current_liabilities = total liabilities of GF (these funds have no LT liab). deferred_inflows = "Deferred inflows of resources" total (mostly unavailable property tax).
- iscap_restricted_assets: any "Iowa Schools Cash Anticipation Program" / cash-management-program restricted asset (short-term borrowing). Almost always 0 for large districts — put 0 if balance sheet shows none.
- cash_and_investments: GF cash + pooled investments (Balance Sheet). Cross-check audit-financials.csv `cash`.
- go_debt_outstanding: total General Obligation bonds outstanding at year-end (long-term debt note / Statement of Net Position long-term liabilities). District-wide.
- capital_loan_notes: PPEL/other capital loan notes outstanding (if separately stated).
- save_rev_bonds: sales-tax (SAVE / "Sales Tax Revenue Bonds" / "Statewide Penny") revenue bonds outstanding.
- lease_sbita: capital lease / SBITA obligations (pre-GASB87 capital leases if any; usually small or 0 in FY15-19).
- annual_debt_service: total principal + interest PAID during the fiscal year on all long-term debt (from Debt Service fund statement or debt note "current year" — needed for fixed-cost ratios). If only principal maturities table, use the row for the current/next year and note it.
- capital_additions / depreciation / construction_in_progress: governmental capital-asset note (additions during year; depreciation expense; CIP balance at year-end).
- save_revenue: SAVE / Local Option Sales Tax / Statewide Penny revenue received in year (Capital Projects/Sales Tax fund).
- unrestricted_net_position: government-wide Statement of Net Position, governmental activities "Unrestricted" (often negative due to pensions — that's normal).
- ipers_npl: district's share of IPERS Net Pension Liability (governmental activities; pension note / Statement of Net Position). Sum govt + business-type if both, note the split.
- opeb_liability: net OPEB liability (governmental activities). NOTE: GASB 75 OPEB liability begins FY2018; before that it may be "OPEB obligation" (GASB 45) — extract what's reported, note the standard.
- pension_contribution: employer IPERS contribution for the year (pension note "contributions" / RSI schedule of contributions). For fixed-cost ratio.
- opeb_contribution: employer OPEB contribution/pay-go for the year (OPEB note). For fixed-cost ratio.
- findings_count / material_weakness (Y/N) / significant_deficiency (Y/N) / repeat_finding (Y/N) / single_audit_findings (text or "None") / gfoa_cert (Y/N): Schedule of Findings & Questioned Costs; GFOA from intro/transmittal letter.
- notes csv: government-wide governmental-activities Statement of Net Position totals + the capital-asset gross/accumulated-depreciation (for Moody's capital-asset depreciation notch) + debt-service schedule (next-FY and total future P&I from the debt note summary table) + construction commitments (commitments note).

## Reference template
Read your district's existing FY2020–FY2023 rows in `data/district-extractions/<DistrictKey>.csv`
and `data/notes-extractions/<DistrictKey>.csv` (pipe-delimited) — same auditor usually, same layout.
Mirror their style in the `notes` column (page refs, the SAVE-bond tranche breakdown, NPL govt+business
split, etc.). Keep going back one year at a time; FY2015 will be the earliest.

When done, print a short summary: which years/fields you got at High vs Low confidence, and any field
you could not find in any year.
