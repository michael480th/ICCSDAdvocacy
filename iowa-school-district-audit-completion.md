# Iowa School District Audits: Can You Count Completed / "Passed" Audits by Year?

**Question:** Within Iowa, can we see how many school districts *completed* audits by year —
not merely submitted financials to the state, but actually got through the audit — and how
many "passed" (clean result)?

**Short answer:** There is **no published, ready-made statistic** that says "N Iowa districts
passed their audits in year Y." But Iowa's system makes the number **reconstructable**, because
(a) every district is required to be audited every year, and (b) every audit report is a public
record filed in one central place. This document defines the terms precisely, states exactly
what is and isn't available, and ships an automated method (`scripts/iowa_audit_scraper.py`) to
build the by-year table from the primary source.

**Research date:** May 2026. Statutory and structural facts corroborated via Iowa Code §11.6,
the Iowa Dept. of Education audit guidance (Chapter 8), and the Auditor of State. Note: the
empirical by-year counts are **not** filled in here — they require running the scraper against
the live Auditor of State database (see "Why this file has no numbers yet" below).

---

## 1. "Passed" needs a definition — governmental audits have no pass/fail

A school-district audit does not produce a pass/fail grade. It produces two distinct outputs,
and "passed" can map to either — they give very different counts:

| Output | Categories | What "passed" would mean | Typical Iowa reality |
|---|---|---|---|
| **Opinion on the financial statements** | *Unmodified* (clean) · *Qualified* · *Adverse* · *Disclaimer* | An **unmodified** opinion | The **vast majority** of districts get an unmodified opinion every year — so this count is near-100% and not very discriminating |
| **Schedule of Findings** | Material weakness · Significant deficiency · Noncompliance · Iowa statutory findings | **Zero** significant findings | Far more variation here — this is the more informative "passed" metric |

> **Recommendation:** Track **both**. Report "districts with an unmodified opinion" (the formal
> "clean audit") *and* "districts with no material weaknesses / no significant findings" (the
> substantive "clean audit"). The scraper captures both.

A district can receive a clean (unmodified) **opinion** and still have **findings** — these are
independent. Conversely, the most severe outcome short of fraud is not a "fail" but a **late or
missing** audit (a "completion" failure), which is exactly what cost the Iowa City Community
School District its bond rating (see the companion file
`school-district-rating-withdrawals.md`).

---

## 2. "Completed" vs. "submitted financials" — you are right that these are different filings

Iowa districts make **two separate** financial filings, and conflating them is the core of the
confusion this question raises:

| Filing | Goes to | What it is | Maps to |
|---|---|---|---|
| **Certified Annual Report (CAR)** | Iowa **Dept. of Education** | The district reporting **its own** financial data | "submitted financials to the state" |
| **Annual audit** | **Auditor of State** (also copied to Dept. of Ed) | An **independent** CPA's / State Auditor's examination, with opinion + findings | "completed an audit" |

A district can keep filing CARs on time while falling **years behind on audits** — which is
precisely the ICCSD situation. So "completed an audit" = **an audit report actually on file with
the Auditor of State for that fiscal year**. The CAR (and the open-data expenditure dataset
derived from it on data.iowa.gov) tells you nothing about whether the audit was done.

---

## 3. The statutory backbone (why the count is even possible)

- **Iowa Code §11.6(1)(a):** *every* school district must be examined/audited **at least once each
  year.* Unlike cities (which below a size threshold may get periodic exams instead of annual
  audits), **school districts have no small-district exemption** — so the expected denominator is
  effectively **all ~325 districts, every year.**
- The audit must cover school funds, **the Certified Annual Report**, certified enrollment
  (§257.6), supplementary weighting (§257.11), categorical-funding compliance, and statutory
  compliance items.
- **Deadline:** the audit report is due to the Auditor of State within **nine months of fiscal
  year-end** (FYE June 30) — i.e., **by March 31** — or within 30 days of issuance to the
  district, whichever is first. **Extensions** require a written, good-cause request under
  §11.6(6).
- Audits may be performed **by the Auditor of State or by an approved private CPA firm** (most
  districts use private firms); either way the report is filed with, and re-reviewed by, the
  Auditor of State, and is a **public record**.

This means the *ideal* dataset is: 325 districts × each fiscal year, each row either
**(a) has a filed report** (completed) with an **opinion** and a **findings count**, or
**(b) has no report on file** (behind / delinquent — e.g., ICCSD).

---

## 4. What is and isn't centrally available

| You want | Available as a stat? | Source / how |
|---|---|---|
| Count of districts with a **filed/completed** audit, by year | **Not pre-tabulated** — but reconstructable | Auditor of State audit-reports database: every filed PDF, back to ~2000; enumerate school-district reports per fiscal year |
| Count with a **clean (unmodified) opinion**, by year | **No aggregate** — read each PDF | Same database; opinion is in the Independent Auditor's Report |
| Count with **no significant/material findings**, by year | **No aggregate** — read each PDF | Same database; Schedule of Findings |
| List of **delinquent / late / not-filed** districts | **Not a standing public list** | Records request to the Auditor of State (tracks deadlines/extensions); or infer from "missing FY rows" in the scrape |
| "Submitted financials" (CAR) by year | **Yes**, machine-readable | data.iowa.gov (CAR-derived expenditure datasets) — but this is *not* audit status |

**The key limitation** mirrors what the companion bond-rating report found about the rating
agencies: the Auditor of State publishes reports **issuer-by-issuer as PDFs**, not as a queryable
dataset broken out by opinion/findings. There is no dashboard that tallies "X districts clean in
FY2023." You assemble it yourself.

---

## 5. The method (automated): `scripts/iowa_audit_scraper.py`

The scraper produces two CSVs from the primary source:

1. **`iowa_audit_reports.csv`** — one row per district per fiscal year found:
   `entity_name, fiscal_year, report_date, audited_by, opinion,
   num_financial_findings, num_statutory_findings, material_weakness,
   significant_deficiency, going_concern, report_url`
2. **`iowa_audit_summary_by_year.csv`** — the answer to your question, aggregated:
   `fiscal_year, districts_with_filed_audit, unmodified_opinions,
   modified_opinions, zero_findings, with_material_weakness,
   completion_rate_vs_325`

It works in two modes so it's useful regardless of how the site serves files:

- **`scrape`** — walk the Auditor of State audit-reports index, filter to school districts,
  download each PDF.
- **`parse`** — read a folder of already-downloaded PDFs and emit the CSVs. (Use this if the
  index is JavaScript-rendered and you download PDFs by hand or via the site's export.)

Opinion and findings are detected from the **standardized Iowa CSD report wording** (the Auditor
of State publishes a CSD report template, so the language is consistent across firms):

- **Unmodified:** *"present fairly, in all material respects"* in the opinion paragraph.
- **Qualified:** *"except for"* qualifier in the opinion.
- **Adverse:** *"do not present fairly."*
- **Disclaimer:** *"we do not express an opinion."*
- **Findings:** the *Schedule of Findings* section, split into financial-statement findings and
  *Other Findings Related to Required Statutory Reporting*; plus material-weakness /
  significant-deficiency / going-concern flags.

> The Auditor of State site is a CMS whose exact search endpoint/selectors must be confirmed
> against the live page; the script centralizes those in clearly-marked constants at the top so
> `scrape` mode can be pointed at the right URL without touching parsing logic. The `parse` mode
> needs no network knowledge at all and is the reliable path.

### Running it

```bash
pip install requests beautifulsoup4 pdfplumber
# Option A — you have a folder of downloaded district audit PDFs:
python scripts/iowa_audit_scraper.py parse --pdf-dir ./audit_pdfs --out ./out
# Option B — attempt to scrape the index, then parse:
python scripts/iowa_audit_scraper.py scrape --years 2015-2025 --out ./out
```

---

## 6. Why this file has no numbers yet

This report was compiled in a sandboxed environment whose **network egress is restricted to an
allowlist that excludes all `iowa.gov` domains**, and the Auditor of State / Dept. of Education
sites additionally **bot-block automated fetching**. The empirical by-year counts therefore have
to be produced by running the scraper from a normal internet connection. Everything structural
above (the requirement, the deadline, the two-filing distinction, the source of truth) is
confirmed; the counts are one scraper run away.

---

## 7. Sources

- Iowa Code §11.6 — Audits of governmental subdivisions — https://www.legis.iowa.gov/docs/code/11.6.pdf
- Iowa Dept. of Education — Chapter 8: Auditing / Annual Audit — https://educate.iowa.gov/media/3268/download
- Iowa Dept. of Education — Audits / School Finance — https://educate.iowa.gov/pk-12/operation-support/business-finance/financial-management/audits
- Iowa State Auditor — Audit Reports database — https://www.auditor.iowa.gov/reports/audit-reports
- Iowa State Auditor — CSD report template (sample) — https://www.auditor.iowa.gov/moduledocuments/embed/4405/25_CSD_Sample_Report_PDF_55BD27EEC8000.pdf
- Iowa Legislature — Audit Reports listing — https://www.legis.iowa.gov/publications/auditReports?department=19206&ga=all
- data.iowa.gov — School District Expenditures Per Pupil by FY (CAR-derived; "submitted financials", not audit) — https://data.iowa.gov/School-Finance/School-District-Expenditures-Per-Pupil-By-Fiscal-Y/y68w-es55
- Iowa Dept. of Education — district count (~325, 2024–25) — https://educate.iowa.gov/pk-12/district-maps
- Companion: `school-district-rating-withdrawals.md` (ICCSD bond-rating loss for late audits)

---

## 8. Confidence & caveats

- **High confidence:** the completed-vs-submitted distinction; the §11.6 annual-audit
  requirement for all districts; the March 31 / 9-month deadline; the ~325 denominator; and that
  the Auditor of State database is the authoritative, public source of every filed report.
- **Moderate confidence:** that nearly all districts receive unmodified opinions in a typical
  year (true of governmental auditing generally and Iowa specifically, but not independently
  re-counted here).
- **Not establishable without running the scraper / a records request:** the actual by-year
  counts, and a definitive list of delinquent districts. The Auditor of State does not publish
  an opinion/findings dataset or a standing delinquency list.
