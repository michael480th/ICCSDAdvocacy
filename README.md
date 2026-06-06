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
| **[`iccsd-vs-peers.html`](iccsd-vs-peers.html)** | **Public-facing Iowa City focus.** One measure at a time, comparing Iowa City CSD to the top-10 and top-5 districts, each with a plain-English explanation of what it is and why it matters. Self-contained. |
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
school-district-rating-withdrawals.md        Companion research: districts that lost bond
                                             ratings over late/missing audits

data/
  iowa-district-financials.csv               Master dataset from the audits (one row per district-year)
  iowa-district-notes.csv                    Balance-sheet & forward-commitment data from audit notes
  iowa-district-scorecards.csv               Final scores + flags, one row per district
  district-extractions/                      Raw per-district extractions from the audits (provenance)
  notes-extractions/                         Raw per-district extractions from the notes (provenance)
  dom/                                        Iowa Dept. of Management/Education state data
    unspent-authorized-budget.csv              Spending authority (the #1 health metric)
    cash-reserve-levy.csv, levy-rates-and-valuation.csv, certified-enrollment.csv,
    aea-flowthrough.csv, at-risk.csv, assessed-valuation-latest.csv, aid-levy-summary.csv

scripts/
  extract_dom.py        Reads the Iowa state workbooks -> data/dom/*.csv
  build_analysis.py     Merges audited + state + notes data, scores every district -> scorecards + cards.json
  build_report.py       Renders cards.json into the HTML report
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

The scoring and report are regenerated from the committed data with:

```bash
python3 scripts/build_analysis.py   # data/ -> data/iowa-district-scorecards.csv (+ cards.json)
python3 scripts/build_report.py     # -> iowa-district-financial-benchmark.html
```

(`scripts/extract_dom.py` rebuilds `data/dom/` from the original Iowa state spreadsheets; those source
workbooks and the audit PDFs are kept in the project's data-source folders.) Requires Python 3 with
`openpyxl` for the spreadsheet step.

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
GitHub can serve the file directly from this repository:
1. Make a copy named **`index.html`** at the repo root (so it becomes the landing page):
   `cp iowa-district-financial-benchmark.html index.html` and commit it.
2. In GitHub: **Settings → Pages → Build and deployment → Source: "Deploy from a branch."**
3. Choose the branch to publish (e.g. `main`) and folder **`/ (root)`**, then **Save**.
4. After ~1 minute the report is live at:
   `https://michael480th.github.io/iccsdadvocacy/`
   (or `…/iowa-district-financial-benchmark.html` if you skip the `index.html` copy).

> Pages publishes from one branch. If the report is on a feature branch, either merge it to `main`
> first, or point Pages at that branch in step 3.

### Option 3 — Quick preview link (no setup at all)
Paste the file's GitHub URL into the htmlpreview proxy:
`https://htmlpreview.github.io/?https://github.com/michael480th/iccsdadvocacy/blob/main/iowa-district-financial-benchmark.html`
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
