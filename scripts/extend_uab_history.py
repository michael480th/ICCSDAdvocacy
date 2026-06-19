#!/usr/bin/env python3
"""
Extend data/dom/unspent-authorized-budget.csv and data/dom/aea-flowthrough.csv back to FY2015.

The main DOM extractor (extract_dom.py) runs off a staged source tree and was year-limited to
FY2020+. The Unspent Authorized Budget workbook in this repo (UAB/) actually carries every Iowa
district from FY2008, so this script reads it directly and merges the FY2015–FY2019 rows for our
15 benchmarked districts into the committed DOM CSVs (idempotent — existing rows are kept).

UAB is Iowa's single most important financial-health measure, so having it for the full FY2015–FY2025
window (all districts) matters for the benchmark. Verified against ICCSD's published Annual Financial
Health Report: FY2017 UAB = 6.64% ($10.93M / $164.7M), matching this workbook.

-> data/dom/unspent-authorized-budget.csv, data/dom/aea-flowthrough.csv
"""
import openpyxl, csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WB = os.path.join(ROOT, "UAB", "Unspent Authorized Budget Report.xlsx")
CODE = {"0261":"Ankeny CSD","0882":"Burlington CSD","1053":"Cedar Rapids CSD",
 "1337":"College CSD (Prairie)","1611":"Davenport CSD","1737":"Des Moines Independent CSD",
 "1863":"Dubuque CSD","3141":"Iowa City CSD","3231":"Johnston CSD","3715":"Linn-Mar CSD",
 "4581":"Muscatine CSD","5250":"Pleasant Valley CSD","6795":"Waterloo CSD","6822":"Waukee CSD",
 "6957":"West Des Moines CSD"}
YEARS = range(2015, 2020)   # the gap to backfill (FY2020+ already present from extract_dom.py)

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def main():
    wb = openpyxl.load_workbook(WB, data_only=True, read_only=True)
    ws = wb["data_UAB"]   # cols: 0=FiscalYear 1=Dist# 35=Expenditures 37=MaxAuthBudget 38=UnspentAuthBudget, 12..18=AEA
    uab, aea = {}, {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        fy, dist = row[0], row[1]
        if dist in CODE and isinstance(fy, (int, float)) and int(fy) in YEARS:
            k = (CODE[dist], int(fy))
            if k in uab: continue
            mx, ub, exp = num(row[37]), num(row[38]), num(row[35])
            pct = round(100*ub/mx, 2) if (ub is not None and mx) else ""
            uab[k] = [CODE[dist], int(fy), mx, ub, exp, pct]
            aea[k] = [CODE[dist], int(fy), round(sum(num(row[i]) or 0 for i in range(12, 19)))]

    def merge(path, header, new):
        existing = list(csv.reader(open(path)))[1:]
        seen = {(r[0], r[1]) for r in existing}
        rows = existing + [[str(c) for c in r] for k, r in new.items() if (r[0], str(r[1])) not in seen]
        rows.sort(key=lambda r: (r[0], int(r[1])))
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(header); csv.writer(f).writerows(rows)
        return len(rows)

    n1 = merge(os.path.join(ROOT, "data/dom/unspent-authorized-budget.csv"),
               ["district","fiscal_year","max_authorized_budget","unspent_authorized_budget","expenditures","uab_pct_of_max"], uab)
    n2 = merge(os.path.join(ROOT, "data/dom/aea-flowthrough.csv"),
               ["district","fiscal_year","aea_flowthrough"], aea)
    print(f"UAB rows: {n1}, AEA rows: {n2} (added {len(uab)} FY2015-2019 rows)")

if __name__ == "__main__":
    main()
