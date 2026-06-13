# ICCSD Advocacy — Iowa School District Financial Analysis

Tools and analysis for understanding the financial health of Iowa's public school districts,
built from **audited financial reports** and **Iowa state financial filings**.

The centerpiece is a benchmark comparing **15 of Iowa's largest districts** across six years
(FY2020–FY2025) on three things: day-to-day **financial health**, the **quality of financial
management**, and **how they are paying for buildings**.

> New to Iowa school finance? The report opens with a plain-English "Key terms" box. The one idea
> to know up front: Iowa caps how much a district may *spend* each year (its **spending authority**),
> separately from how much *cash* it has — so a district can have money in the bank and still be in
> trouble. That distinction drives much of the analysis.

---

## 📊 The report

| File | What it is |
|---|---|
| **[`iowa-district-financial-benchmark.html`](iowa-district-financial-benchmark.html)** | **The interactive report.** Open in any web browser. Sortable comparison table, a financial-health-vs-management map, per-district scorecards, and an "analyze one district" tool with ~20 charts and a "how this score is built" breakdown. A single self-contained file — no internet or install required. |
| **[`iccsd-vs-peers.html`](iccsd-vs-peers.html)** | **Public-facing Iowa City focus.** One measure at a time, comparing Iowa City CSD to **size-matched peers** (large districts of 5,000+ students, and the best-run of those), each with a plain-English explanation of what it is and why it matters. Self-contained. |
| **[`activity-fund.html`](activity-fund.html)** | **Student Activity Fund comparison.** Year-end balance of each district's student-activity fund — self-reported (CAR), audited (ACFR), and **per student** — Iowa City vs. 14 peers, FY2020–FY2024. Shows ICCSD carrying the thinnest cushion of the 15 (~$2/student at the FY2023 trough vs. a ~$100 peer average). Self-contained. |
| **[`FY24-UAB-cushion.html`](FY24-UAB-cushion.html)** | **FY24 unspent-budget-authority watch.** Why ICCSD's FY24 UAB cushion is roughly $3.3 million wide and what it means for the district's spending authority. Self-contained. |
| **[`FY24-audit-watchlist.html`](FY24-audit-watchlist.html)** | **FY24 audit watchlist.** A plain-English guide to what to check first when ICCSD's overdue FY24 audit is finally released. Self-contained. |
| **[`making-the-foc-work.html`](making-the-foc-work.html)** | **Making the Financial Oversight Committee work** (district-leadership perspective). How to stand up the FOC — light-touch oversight, board-adopted financial limits with red/yellow/green zones, a phased path out of crisis, and independence provisions — plus a linked index of all seven illustrative example reports (the monthly dashboard, claims-exception review, 13-week cash forecast, corrective-action tracker, quarterly scorecard, phase-change certification, and auditor-independence confirmation). |
| [`iccsd-fmp-board-commentary.md`](iccsd-fmp-board-commentary.md) | Brief reconciling the benchmark with an ICCSD board member's "no" vote on the Facilities Master Plan — where the data agrees, what the dissent adds, and which KPIs are still missing. Includes the full statement. |
| **[`data/iowa-district-benchmark.xlsx`](data/iowa-district-benchmark.xlsx)** | **The benchmark as a spreadsheet.** Scorecard + year-by-year tabs (UAB, solvency, operating margin, enrollment, total debt, cash-reserve levy) + the underlying audited/state/balance-sheet data + a sources-and-definitions sheet. The "share the Excel file" deliverable. |
| [`iowa-district-financial-benchmark.md`](iowa-district-financial-benchmark.md) | The same findings in plain Markdown (readable directly on GitHub). |
| [`iowa-district-financial-analysis-framework.md`](iowa-district-financial-analysis-framework.md) | The **methodology** — how districts are assessed and scored, and why (the Iowa-specific reasoning behind every metric). |

👉 **To view the report:** download `iowa-district-financial-benchmark.html` and open it in a browser,
or publish it online using the steps in **[Putting the report online](#-putting-the-report-online)** below.

---

## How the scores work

Each district gets three 1–5 scores plus a blended composite:

- **Financial Health** — is it living within its means and keeping a cushion?
  *(spending authority 50% + reserves/solvency 30% + recent operating margin 20%)*
- **Operational Quality** — are the books clean, on time, and well-run?
  *(audit opinions, internal-control findings, repeat problems, timeliness, GFOA/ASBO recognition)*
- **Capital Sustainability** — can it afford what it's building?
  *(health + enrollment trend + margin + how heavy its locked-in building cost is + debt-limit room)*
- **Composite** = 40% Health + 35% Quality + 25% Capital Sustainability.

"Building vs. maintaining" is reported as a neutral **label**, not scored.

---

## Repository contents

```
iowa-district-financial-benchmark.html      The interactive report (open this)
iowa-district-financial-benchmark.md         Markdown version of the report
iowa-district-financial-analysis-framework.md  Methodology / scoring framework
iccsd-vs-peers.html                          Public-facing Iowa City KPI comparison
activity-fund.html                           Student Activity Fund: CAR vs. audited vs. per student
iccsd-fmp-board-commentary.md                Benchmark vs. the FMP board dissent
school-district-rating-withdrawals.md        Companion research: districts that lost bond
                                             ratings over late/missing audits

data/
  iowa-district-benchmark.xlsx               Shareable Excel workbook (snapshot + time series + raw)
  iowa-district-financials.csv               Master dataset from the audits (one row per district-year)
  iowa-district-notes.csv                    Balance-sheet & forward-commitment data from audit notes
  iowa-district-scorecards.csv               Final scores + flags, one row per district
  car-fund-balances.csv                      Per-fund CAR balances incl. the Activity fund (FY2017-2024)
  activity-fund-audited.csv                  Audited Student Activity fund balance from the ACFRs (FY2020-2024)
  district-extractions/                      Raw per-district extractions from the audits (provenance)
  notes-extractions/                         Raw per-district extractions from the notes (provenance)
  dom/                                        Iowa Dept. of Management/Education state data
    unspent-authorized-budget.csv              Spending authority (the #1 health metric)
    cash-reserve-levy.csv, levy-rates-and-valuation.csv, certified-enrollment.csv,
    aea-flowthrough.csv, at-risk.csv, assessed-valuation-latest.csv, aid-levy-summary.csv

scripts/
  extract_dom.py        Reads the Iowa state workbooks -> data/dom/*.csv
  build_analysis.py     Merges audited + state + notes data, scores every district -> scorecards + cards.json
  build_report.py       Renders cards.json into the main HTML report
  build_iccsd_report.py Renders the public-facing Iowa City KPI comparison
  build_workbook.py     Renders the shareable Excel workbook
  extract_car.py        Reads the Iowa DE CAR workbooks/CSVs -> data/car-fund-balances.csv
  extract_activity_fund.py        Reads each ACFR -> data/activity-fund-audited.csv (audited activity balance)
  build_activity_fund_report.py   Renders the Student Activity Fund comparison -> activity-fund.html
```

Each `data/` folder has its own README describing the columns and sources.

---

## Where the numbers come from

- **Audited Annual Comprehensive Financial Reports (ACFRs)** for each district, FY2020–FY2025.
- **Iowa Department of Management / Department of Education** filings: the Unspent Authorized Budget
  report, cash-reserve levies, tax rates, property valuations, certified enrollment, and at-risk funding.
- **Notes to the audited statements** for net worth, construction commitments, and future debt payments.

State figures are *unaudited* but exist even when a district hasn't filed its audit (which is why
Iowa City still has spending-authority data for 2024–2025 even though those audits are missing — and is
marked down for the gap).

## Reproducing the analysis

The scoring and reports are regenerated from the committed data with:

```bash
python3 scripts/build_analysis.py     # data/ -> data/iowa-district-scorecards.csv (+ cards.json)
python3 scripts/build_report.py       # -> iowa-district-financial-benchmark.html
python3 scripts/build_iccsd_report.py # -> iccsd-vs-peers.html (+ index.html, the Pages landing page)
python3 scripts/build_workbook.py     # -> data/iowa-district-benchmark.xlsx
```

(`scripts/extract_dom.py` rebuilds `data/dom/` from the original Iowa state spreadsheets; those source
workbooks and the audit PDFs are kept in the project's data-source folders.) Requires Python 3 with
`openpyxl` for the spreadsheet steps.

---

## 🌐 Putting the report online

`iowa-district-financial-benchmark.html` is a **single self-contained file** (all charts and styling are
inside it, no external dependencies), so it's easy to host. Easiest options, simplest first:

### Option 1 — Netlify Drop (fastest, no account setup)
1. Go to **[app.netlify.com/drop](https://app.netlify.com/drop)**.
2. Drag `iowa-district-financial-benchmark.html` onto the page.
3. You instantly get a public link you can share. (Rename the file to `index.html` first if you want a
   cleaner URL.) Cloudflare Pages and Vercel offer similar drag-and-drop.

### Option 2 — GitHub Pages (free, lives with this repo)
GitHub serves the site directly from this repository. **`index.html` is already the landing
page** — it is the public-facing Iowa-City-vs-peers report, written automatically by
`scripts/build_iccsd_report.py` (no copy/rename step). Every published page carries a shared
nav bar linking the others, so the whole site shares one URL.
1. In GitHub: **Settings → Pages → Build and deployment → Source: "Deploy from a branch."**
2. Choose the branch to publish (e.g. `main`) and folder **`/ (root)`**, then **Save**.
3. After ~1 minute the site is live at a `github.io` URL, opening on `index.html`.

### Option 3 — Quick preview link (no setup at all)
Paste the file's GitHub URL into the htmlpreview proxy:
`https://htmlpreview.github.io/?<the file's GitHub URL>`
Good for a quick look; for anything you'll share widely, prefer Option 1 or 2.

### Option 4 — Just email it / open locally
Because it's one self-contained file, you can email it or open it by double-clicking — it works offline.

---

## Notes & caveats

- All figures trace to a district's audited report or an official Iowa state filing; nothing is estimated
  to fill gaps. Anything that couldn't be confirmed is flagged or left blank.
- A negative "unrestricted net position" in the charts is **normal** for Iowa schools — it reflects
  long-term pension obligations (IPERS), not day-to-day insolvency.
- One common measure — staff salaries/benefits as a share of the budget — isn't broken out in these
  audits, so it's noted rather than scored.
