# FY2020–FY2025 fixed-cost inputs (pension/OPEB contributions + annual debt service)

Fills the Moody's Fixed-Costs Ratio and S&P Current-Cost Ratio for recent years. For ONE district,
read its FY2020–FY2025 ACFR PDFs in `auditreports/` (Iowa City: FY2020–FY2023 only — no FY24/25 audit).

Extract three figures per fiscal year, from these locations:
- `pension_contribution` — the employer's IPERS contribution for the year. Best source: the RSI
  "Schedule of District Contributions" (IPERS) → "Contractually required contribution" / "Contributions
  in relation to the contractually required contribution" for that fiscal year. If a district has more
  than one plan (e.g. a municipal/teacher plan), sum the employer contributions and note it.
- `opeb_contribution` — the employer's OPEB contribution / benefit payments (pay-go) for the year, from
  the OPEB note ("Contributions" or "benefit payments") or OPEB RSI. Blank if the district reports no OPEB plan.
- `annual_debt_service` — total principal + interest PAID on long-term debt during the fiscal year.
  Best source: the Debt Service fund column of the Statement of Revenues, Expenditures and Changes in
  Fund Balances (principal + interest + fiscal charges), or the governmental-funds total debt-service line.
  If a year includes a bond refunding/defeasance that inflates principal, record the figure AND note it.

Write `data/fy20-25-flows/<DistrictKey>.csv`, pipe `|` delimited, columns EXACTLY:

district|fiscal_year|pension_contribution|opeb_contribution|annual_debt_service|confidence|notes

Rules: one row per fiscal year with a PDF (2020–2025; 2020–2023 for Iowa City). Whole-dollar integers.
Parentheses = negative. Blank (not 0) when truly absent; explain in `notes`. Never guess. Page refs +
confidence (High/Medium/Low) in `notes`. The `district` column value must match the name in the task exactly.
Print a one-line confidence-by-year summary when done.
