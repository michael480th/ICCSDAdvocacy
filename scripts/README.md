# scripts/

## iowa_audit_scraper.py

Builds a by-year table of Iowa school-district audits — **how many completed**
(filed a report) and how many **passed** (unmodified opinion / zero findings) —
from the Auditor of State's public audit reports. See the full write-up in
[`../iowa-school-district-audit-completion.md`](../iowa-school-district-audit-completion.md).

```bash
pip install requests beautifulsoup4 pdfplumber

# Completion + timeliness from the AOS results table (no PDFs needed):
python iowa_audit_scraper.py scrape --years 2015-2025 --out ./out

# Same, plus opinion/findings by opening every PDF (slow):
python iowa_audit_scraper.py scrape --years 2015-2025 --with-pdfs --out ./out

# If results are JavaScript-rendered, save the results page from the browser, then:
python iowa_audit_scraper.py parse-html --html-file results.html --out ./out

# Opinion/findings from a folder of downloaded report PDFs:
python iowa_audit_scraper.py parse --pdf-dir ./audit_pdfs --out ./out
```

Outputs to `--out`:

- `iowa_audit_reports.csv` — one row per district per fiscal year (period ending,
  release date, months-to-release, late flag, firm, and — if PDFs parsed — opinion/findings)
- `iowa_audit_summary_by_year.csv` — the aggregate answer by fiscal year
  (districts filed, late filings, clean opinions, zero-findings, material weaknesses)

The search uses the confirmed AOS recipe: `EntityTypeID=40` (School) over a
`ReportPeriodEnding` date range; *Period Ending 06/30/YYYY = FY YYYY*. **Completion
and timeliness come straight from the results table** — only opinion/findings needs
the PDFs.

A district with **no row** for a fiscal year is behind/delinquent — Iowa Code
§11.6(1)(a) requires an annual audit of every district. "Passed" is reported two
ways (clean opinion vs. zero findings) because governmental audits have no
pass/fail; see the write-up for why both matter.

> Note: authored in a sandbox with no access to `iowa.gov` hosts, so the live HTTP
> behavior (e.g. whether the table needs JavaScript) wasn't run end-to-end. If
> `scrape` returns no rows, use `parse-html` on a saved results page — the table
> parsing is identical and needs no network.
