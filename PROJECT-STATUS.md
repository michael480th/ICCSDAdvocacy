# Project status — Iowa school-district financial benchmark

_Last updated: June 2026. This file is a hand-off so a new chat (or a new reader) can pick up fast._

## What this project is
A benchmark of **15 of Iowa's largest school districts** (FY2020–FY2025) on financial **health**,
**quality of financial management**, and **how they pay for buildings**, with a public-facing focus on
**Iowa City CSD (ICCSD)**. Every figure traces to an audited financial report or an official Iowa state
filing.

## Deliverables (all in this repo)
| File | What it is |
|---|---|
| `iowa-district-financial-benchmark.html` | Full interactive report (table, map, per-district deep-dive, "how the score is built") |
| `iccsd-vs-peers.html` | Public Iowa City report — 13 KPI cards vs. size-matched peers (5,000+ students) |
| `iccsd-filing-vs-control.html` | Scatterplot: audit filing speed vs. financial-control metrics |
| `iccsd-fmp-board-commentary.md` | Benchmark vs. the FMP board dissent + the April-2026 cash-flow memo |
| `iowa-district-financial-analysis-framework.md` | Methodology / scoring framework |
| `data/iowa-district-benchmark.xlsx` | Shareable Excel (scorecard + time series + raw data) |
| `iowa-district-financial-benchmark.md` | Markdown version of the report |

## Regenerate everything (from committed data)
```bash
python3 scripts/build_analysis.py       # data/ -> scorecards + /tmp/audit/cards.json
python3 scripts/build_report.py         # -> iowa-district-financial-benchmark.html
python3 scripts/build_iccsd_report.py   # -> iccsd-vs-peers.html
python3 scripts/build_scatter.py        # -> iccsd-filing-vs-control.html
python3 scripts/build_workbook.py       # -> data/iowa-district-benchmark.xlsx
# scripts/extract_dom.py rebuilds data/dom/* from the state spreadsheets in the source-doc folders
```
Requires Python 3 + `openpyxl`. (The build_* scripts read `/tmp/audit/cards.json`, written by
`build_analysis.py`, so run that first.)

## Data layers
- **Audited ACFRs** (FY2020–FY2025) → `data/iowa-district-financials.csv`, `data/district-extractions/`
- **Audit notes** (balance sheet, commitments, debt schedule) → `data/iowa-district-notes.csv`, `data/notes-extractions/`
- **Iowa state (DOM/DE)**, unaudited → `data/dom/*` (UAB, enrollment, levies, valuations, at-risk)
- Source documents (audit PDFs, state spreadsheets, board emails) → the upper-case folders + `emails/`

## Scoring (1–5)
- **Health** = 0.50·UAB(spending authority) + 0.30·solvency + 0.20·operating-margin trend
- **Operational Quality** = audit opinions, findings, repeat findings, timeliness, GFOA/ASBO
- **Capital Sustainability** = 0.35·Health + 0.20·enrollment + 0.15·margin + 0.20·forward-debt burden + 0.10·GO-debt headroom
- **Composite** = 0.40·Health + 0.35·Quality + 0.25·Capital Sustainability. "Building vs. maintaining" is a label, not scored.

## Headline findings
- **Iowa City ranks last of the 15** (composite 2.2) and is the **only large district missing its FY2024/FY2025 audits**.
- Its **spending authority (UAB) went negative in 2023** (−1.2%) — the unlawful, state-review-triggering level.
- **~9 days of operating reserves** vs. ~44 (large-district avg) / ~60 (GFOA guideline).
- **2nd-most SAVE-leveraged** large district (~8.4 yrs pledged); carries **both** GO and SAVE debt (~$322M outstanding, FY2023).
- The broad pattern across all 15: a post-ESSER operating squeeze, but most districts kept clean, timely books.

## Open ideas / not yet built
- **Capacity-utilization KPI** (enrollment ÷ building capacity) — would directly test the "over-building" concern; needs facility design-capacity data not in the audits/state files.
- **Forward debt-payoff-horizon KPI** (final payoff year; ~2036–37 now, 2047 as proposed) — feasible from the debt-maturity schedule.

## ⚠️ Repo / git note
The repo was **renamed to `ICCSD_Financial_Benchmarking`**. A clone that still points at the old name
(`ICCSDAdvocacy`) can read but **cannot push** (proxy rejects the renamed target). Fix by repointing the
git remote to the new name, or renaming the repo back. Files committed during the outage went in via the
GitHub API.
