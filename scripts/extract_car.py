#!/usr/bin/env python3
"""
Extract per-fund Beginning / Revenue / Expenditure / Ending fund balances from the Iowa
Department of Education Certified Annual Report (CAR) — the district's own *unaudited*
financial self-report — into one tidy table: data/car-fund-balances.csv.

Sources (staged in CAR/; the large raw files are .gitignored — they live on the repo's
main branch and can be fetched on demand):
  - CAR/iowa_school_district_revenues_by_fiscal_year_*.csv      FY2017-2023, all funds.
      Long format; each "Beginning Fund Balance" source line gives the fund's opening balance.
  - CAR/iowa_school_district_expenditures_by_fiscal_year_*.csv  FY2017-2023, all funds.
      Each "Ending Fund Balance" source line gives the fund's closing balance.
  - CAR/2022_2023 CAR data-for website.xlsx                     FY2023 annual workbook (authoritative).
  - CAR/2023_2024 CAR data-for website*.xlsx                    FY2024 annual workbook (authoritative).

The Iowa CAR identity holds per fund/year:  beginning + revenues = expenditures + ending.

The two annual workbooks are the authoritative published CAR; for the General Fund in FY2023
and FY2024 we take ending/revenue/expenditure (and the unassigned/assigned split) from them.
They reconcile to the long CSVs for every benchmarked district except one cell (Cedar Rapids
FY2023, off by a round $1.05M in the long CSV) — so the workbook is preferred for those years.
The long CSVs supply the FY2017-2022 history and every fund's beginning balance.
"""
import csv, glob, os, openpyxl
from collections import defaultdict

OUT = "data/car-fund-balances.csv"
REV = glob.glob("CAR/iowa_school_district_revenues_by_fiscal_year_*.csv")[0]
EXP = glob.glob("CAR/iowa_school_district_expenditures_by_fiscal_year_*.csv")[0]
XLS = {2023: glob.glob("CAR/2022_2023 CAR data*.xlsx")[0],
       2024: glob.glob("CAR/2023_2024 CAR data*.xlsx")[0]}

names = {}
# rec[(code, fy, fund)] = dict(beg, rev, exp, end, unass, ass, xfer)
# xfer = interfund "Transfers In" (General Fund -> the fund), which the CAR counts as revenue.
rec = defaultdict(lambda: dict(beg=None, rev=0.0, exp=0.0, end=None, unass=None, ass=None, xfer=0.0))


def code_of(s):
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return None


# ---- long CSVs: FY2017-2023, every fund ----
with open(REV, newline="") as fh:
    for r in csv.DictReader(fh):
        c = code_of(r["dist"])
        if c is None:
            continue
        names[c] = r["district_name"]
        k = (c, int(r["fiscal_year"]), r["fund"])
        amt = float(r["amount"] or 0)
        if r["source"].strip() == "Beginning Fund Balance":
            rec[k]["beg"] = amt
        else:
            rec[k]["rev"] += amt
            if "Transfers In" in r["source"]:
                rec[k]["xfer"] += amt

with open(EXP, newline="") as fh:
    for r in csv.DictReader(fh):
        c = code_of(r["dist"])
        if c is None:
            continue
        k = (c, int(r["fiscal_year"]), r["fund"])
        amt = float(r["amount"] or 0)
        if r["source"].strip() == "Ending Fund Balance":
            rec[k]["end"] = amt
        else:
            rec[k]["exp"] += amt

# ---- authoritative annual workbooks: override General Fund FY2023 & FY2024 ----
EXPOBJ = ["TotSal", "TotBen", "TotPurchServ", "TotSupplies", "TotEquip", "TotMisc", "TotOther"]


def hidx(ws):
    h = list(ws.iter_rows(min_row=3, max_row=3, values_only=True))[0]
    return {n: i for i, n in enumerate(h) if n}


def by_code(ws):
    d = {}
    for row in ws.iter_rows(min_row=4, values_only=True):
        if isinstance(row[1], int):
            d[row[1]] = row
    return d


for fy, path in XLS.items():
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    bs, rv, ex = wb["BalSheetData1"], wb["RevData1"], wb["GenExpData1"]
    bi, ri, ei = hidx(bs), hidx(rv), hidx(ex)
    B, R, E = by_code(bs), by_code(rv), by_code(ex)
    for c in B:
        if c not in R or c not in E:
            continue
        k = (c, fy, "General")
        rec[k]["end"] = B[c][bi["gentotalfundequity"]]
        rec[k]["unass"] = B[c][bi["genunassfundbal"]]
        rec[k]["ass"] = B[c][bi["genassfundbal"]]
        rec[k]["rev"] = R[c][ri["gentotalrevandother"]] or 0
        rec[k]["exp"] = sum((E[c][ei[o]] or 0) for o in EXPOBJ)
        # beginning of FY = prior year's General-Fund ending
        prior = rec.get((c, fy - 1, "General"))
        if prior and prior["end"] is not None:
            rec[k]["beg"] = prior["end"]

    # ---- Activity (student activities) fund: FY2024 only (long CSVs end at FY2023) ----
    # The workbook carries every fund's balance; we add the Activity special-revenue fund so the
    # CAR series reaches FY2024. Ending = acttotalfundequity; rev/exp from the Activity sheets;
    # beginning = prior-year Activity ending (FY2023, from the long CSVs above).
    if fy == 2024:
        ax = wb["ActExpData1"]
        ai, A = hidx(ax), by_code(ax)
        for c in B:
            if c not in R:
                continue
            k = (c, fy, "Activity")
            rec[k]["end"] = B[c][bi["acttotalfundequity"]]
            rec[k]["rev"] = R[c][ri["acttotalrevandother"]] or 0
            rec[k]["xfer"] = R[c][ri["acttotalotherfinansource"]] or 0  # transfers in (other financing sources)
            if c in A:
                rec[k]["exp"] = sum((A[c][ai[o]] or 0) for o in EXPOBJ)
            prior = rec.get((c, fy - 1, "Activity"))
            if prior and prior["end"] is not None:
                rec[k]["beg"] = prior["end"]

rows = []
for (c, fy, fund) in sorted(rec):
    d = rec[(c, fy, fund)]
    rows.append([c, names.get(c, ""), fy, fund,
                 d["beg"], round(d["rev"], 2), round(d["exp"], 2), d["end"],
                 d["unass"], d["ass"]])

os.makedirs("data", exist_ok=True)
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["district_code", "district_name", "fiscal_year", "fund",
                "beginning_balance", "revenues", "expenditures", "ending_balance",
                "gf_unassigned", "gf_assigned"])
    w.writerows(rows)
print(f"wrote {OUT}: {len(rows)} rows, FY{min(r[2] for r in rows)}-{max(r[2] for r in rows)}, "
      f"{len({r[0] for r in rows})} districts")

# Companion table: the Activity fund's interfund "Transfers In" (General Fund -> Activity), which the
# CAR records as revenue. Lets a report show activity results before vs. after the transfer subsidy.
XOUT = "data/activity-transfers.csv"
with open(XOUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["district_code", "district_name", "fiscal_year", "transfers_in"])
    for (c, fy, fund) in sorted(rec):
        if fund == "Activity":
            w.writerow([c, names.get(c, ""), fy, round(rec[(c, fy, fund)]["xfer"], 2)])
print(f"wrote {XOUT}")
