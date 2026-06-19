# FY2020–FY2025 General-Fund balance-sheet detail extraction

Quick, focused back-fill: we already have FY2015–2019 detail; this fills the GF balance-sheet line
items for FY2020–FY2025 so the internal liquidity ratios (current ratio, receivables & inventory,
creditor's equity) populate for the recent years too.

For ONE district, read its FY2020–FY2025 ACFR PDFs in `auditreports/` (e.g. `Ankeny CSD-2020.pdf` …
`Ankeny CSD-2025.pdf`). (Iowa City has NO FY2024/FY2025 audit — do FY2020–FY2023 only.)

Use Python + PyMuPDF (`import fitz`). From the **Balance Sheet — Governmental Funds**, read the
**General Fund column** for each year. From the **Statement of Revenues, Expenditures and Changes in
Fund Balances (General Fund column)** read the interest/investment-earnings revenue line.

Write `data/fy20-25-bsheet/<DistrictKey>.csv`, pipe `|` delimited, columns EXACTLY:

district|fiscal_year|gf_current_assets|gf_receivables|gf_inventory|gf_prepaid|gf_current_liabilities|gf_deferred_inflows|iscap_restricted_assets|interest_income|confidence|notes

Rules (same house discipline):
- One row per fiscal year you have a PDF for (2020–2025; 2020–2023 for Iowa City).
- `gf_current_assets` = total GF assets (these funds hold only current assets).
- `gf_receivables` = sum of all GF receivable lines (property tax, accounts, due-from, accrued, etc.).
- `gf_current_liabilities` = total GF liabilities. `gf_deferred_inflows` = total GF deferred inflows of resources.
- `iscap_restricted_assets` = Iowa Schools Cash Anticipation Program / cash-management restricted asset (almost always 0 — put 0 if none).
- `interest_income` = GF interest / investment earnings revenue line (blank if folded into "Other" and not separable).
- Whole-dollar integers. Parentheses = negative. `-` = 0. Blank (not 0) when a field truly isn't on the statement; explain in `notes`.
- Never guess. Page refs + confidence (High/Medium/Low) in `notes`. Cross-check total assets = total liabilities + deferred inflows + total fund balance.

District name string to put in the `district` column must match exactly the name given in the task.
Print a one-line confidence-by-year summary when done.
