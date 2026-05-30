# scripts/

## iowa_audit_scraper.py

Builds a by-year table of Iowa school-district audits — **how many completed**
(filed a report) and how many **passed** (unmodified opinion / zero findings) —
from the Auditor of State's public audit reports. See the full write-up in
[`../iowa-school-district-audit-completion.md`](../iowa-school-district-audit-completion.md).

```bash
pip install requests beautifulsoup4 pdfplumber

# Reliable path — parse PDFs you already have on disk:
python iowa_audit_scraper.py parse --pdf-dir ./audit_pdfs --out ./out

# Or attempt to scrape the AOS index first (confirm the endpoint against the
# live site; it may be JavaScript-rendered):
python iowa_audit_scraper.py scrape --years 2015-2025 --out ./out
```

Outputs to `--out`:

- `iowa_audit_reports.csv` — one row per district per fiscal year (opinion, findings, etc.)
- `iowa_audit_summary_by_year.csv` — the aggregate answer by fiscal year

A district with **no row** for a fiscal year is behind/delinquent — Iowa Code
§11.6(1)(a) requires an annual audit of every district. "Passed" is reported two
ways (clean opinion vs. zero findings) because governmental audits have no
pass/fail; see the write-up for why both matter.

> Note: this was authored in a sandbox with no access to `iowa.gov` hosts, so the
> scraper's HTTP layer (`scrape` mode constants at the top of the file) should be
> confirmed against the live Auditor of State page. The `parse` mode needs no
> network knowledge and is the dependable route.
