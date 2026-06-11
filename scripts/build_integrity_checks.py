#!/usr/bin/env python3
"""
CAR-vs-audited reporting-integrity screen for the benchmarked districts.

Runs the reconciliation checks a rating analyst would use, comparing each district's UNAUDITED
Certified Annual Report to its AUDITED ACFR (General Fund), per district per year, and scores how
reliably each district's self-reported numbers tie out.

Inputs (the reliable layers):
  data/car-fund-balances.csv          CAR beginning/revenue/expenditure/ending by fund (FY2017-2024);
                                      unassigned/assigned + the workbooks' cash for FY2023-2024
  data/iowa-district-financials.csv   curated AUDITED ACFR figures (FY2020-2023, + 2024-25 where filed)
  data/gf-operating-cash.csv          audited General Fund cash (FY2020-2023; CAR for IC FY2024)
  CAR/2022_2023 / 2023_2024 workbooks CAR General Fund cash (gencashinvest) for FY2023 / FY2024

Output: data/integrity-checks.csv (one row per district-year-check) + a printed scorecard.

Coverage note: checks that need FY2015-2019 audited figures, per-fund audited detail, transfers, or
restatement notes are listed as PENDING until those audited layers are curated (the FY2015-2019
audit PDFs are in the repo but not yet reliably machine-extractable).
"""
import csv, openpyxl, datetime, glob, statistics as st
from collections import defaultdict

CODE = {261: "Ankeny CSD", 882: "Burlington CSD", 1053: "Cedar Rapids CSD", 1337: "College CSD (Prairie)",
        1611: "Davenport CSD", 1737: "Des Moines Independent CSD", 1863: "Dubuque CSD", 3141: "Iowa City CSD",
        3231: "Johnston CSD", 3715: "Linn-Mar CSD", 4581: "Muscatine CSD", 5250: "Pleasant Valley CSD",
        6795: "Waterloo CSD", 6822: "Waukee CSD", 6957: "West Des Moines CSD"}


def n(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---- CAR (General Fund) ----
car = {}
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["fund"] == "General" and int(r["district_code"]) in CODE:
        car[(CODE[int(r["district_code"])], int(r["fiscal_year"]))] = dict(
            beg=n(r["beginning_balance"]), rev=n(r["revenues"]), exp=n(r["expenditures"]),
            end=n(r["ending_balance"]), un=n(r["gf_unassigned"]), asg=n(r["gf_assigned"]))
# CAR General Fund cash from the annual workbooks
for fy, pat in [(2023, "CAR/2022_2023 CAR data*.xlsx"), (2024, "CAR/2023_2024 CAR data*.xlsx")]:
    ws = openpyxl.load_workbook(glob.glob(pat)[0], data_only=True, read_only=True)["BalSheetData1"]
    h = {v: i for i, v in enumerate(list(ws.iter_rows(min_row=3, max_row=3, values_only=True))[0]) if v}
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[1] in CODE and (CODE[row[1]], fy) in car:
            car[(CODE[row[1]], fy)]["cash"] = row[h["gencashinvest"]]

# ---- Audited ----
aud = {}
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    aud[(r["district"], int(r["fiscal_year"]))] = dict(
        rev=n(r["gf_revenue"]), exp=n(r["gf_expenditure"]), end=n(r["gf_total_fund_balance"]),
        un=n(r["gf_unassigned"]), asg=n(r["gf_assigned"]), solv=n(r["solvency_ratio_pct"]),
        marg=n(r["operating_margin_pct"]), report=r["report_date"])
audcash = {}
for r in csv.DictReader(open("data/gf-operating-cash.csv")):
    if r["source"] == "audit":
        audcash[(r["district"], int(r["fiscal_year"]))] = n(r["gf_cash_investments"])


def pct(c, a):
    return (c - a) / a * 100 if (c is not None and a not in (None, 0)) else None


def avail(d):
    if d is None:
        return None
    u, a = d.get("un"), d.get("asg")
    return None if u is None else u + (a or 0)


# ---- checks: each yields (car_value, aud_value) or None ----
ROWS = []
DISTS = sorted(set(CODE.values()))
YEARS = range(2017, 2024)
ABS, PCTT = 250_000, 1.0   # flag thresholds for dollar checks


def emit(dist, fy, cid, name, cv, av, kind="$"):
    if cv is None or av is None:
        return
    if kind == "$":
        gap = cv - av
        gp = pct(cv, av)
        flag = "Y" if (gp is not None and abs(gp) >= PCTT and abs(gap) >= ABS) else ""
    else:  # ratio / pts (days, %): flag on absolute-point gap >= 3
        gap = cv - av
        gp = None
        flag = "Y" if abs(gap) >= 3 else ""
    ROWS.append(dict(district=dist, fiscal_year=fy, check=cid, name=name,
                     car=round(cv, 2), audited=round(av, 2), gap=round(gap, 2),
                     gap_pct=(round(gp, 2) if gp is not None else ""), flag=flag))


for d in DISTS:
    for y in YEARS:
        c, a = car.get((d, y)), aud.get((d, y))
        cprev, aprev = car.get((d, y - 1)), aud.get((d, y - 1))
        if c and a:
            emit(d, y, "C1_ending", "Ending GF fund balance", c["end"], a["end"])
            emit(d, y, "C2_available", "Available (unassigned+assigned)", avail(c), avail(a))
            emit(d, y, "C10_revenue", "GF revenue", c["rev"], a["rev"])
            emit(d, y, "C11_expenditure", "GF expenditure", c["exp"], a["exp"])
            if c["rev"]:
                emit(d, y, "C13_margin", "Operating margin %", (c["rev"] - c["exp"]) / c["rev"] * 100, a["marg"], "pts")
            if c.get("end") and c.get("exp"):
                emit(d, y, "C18_fb_pct_exp", "Fund balance % of expenditure", c["end"] / c["exp"] * 100,
                     (a["end"] / a["exp"] * 100 if a["exp"] else None), "pts")
            if avail(c) is not None and c["rev"] and a["solv"] is not None:
                emit(d, y, "C17_solvency", "Solvency ratio %", avail(c) / c["rev"] * 100, a["solv"], "pts")
            if c.get("cash") is not None and (d, y) in audcash:
                emit(d, y, "C14_cash", "GF operating cash", c["cash"], audcash[(d, y)])
                emit(d, y, "C15_days_cash", "Days cash on hand",
                     c["cash"] / (c["exp"] / 365), audcash[(d, y)] / (a["exp"] / 365), "pts")
        # CAR internal roll-forward (CAR-only, 2018-2023)
        if c and cprev and c["beg"] is not None and cprev["end"] is not None:
            emit(d, y, "C6_rollforward", "CAR begin = prior CAR end", c["beg"], cprev["end"])
        # CAR beginning vs PRIOR-year audited ending
        if c and aprev and c["beg"] is not None and aprev["end"] is not None:
            emit(d, y, "C7_begin_vs_audit", "CAR begin vs prior audited end", c["beg"], aprev["end"])
        # net change: CAR vs audited
        if c and a and aprev and c["beg"] is not None and aprev["end"] is not None:
            emit(d, y, "C8_net_change", "Net change in fund balance",
                 c["end"] - c["beg"], a["end"] - aprev["end"])

# ---- audit timeliness (meta; audited only) ----
for (d, y), a in aud.items():
    if d in DISTS and 2017 <= y <= 2023 and a["report"]:
        try:
            rd = datetime.date.fromisoformat(a["report"])
            months = (rd - datetime.date(y, 6, 30)).days / 30.44
            ROWS.append(dict(district=d, fiscal_year=y, check="C22_timeliness",
                             name="Audit lag (months after FYE)", car="", audited=round(months, 1),
                             gap="", gap_pct="", flag=("Y" if months > 15 else "")))
        except ValueError:
            pass

with open("data/integrity-checks.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["district", "fiscal_year", "check", "name", "car", "audited", "gap", "gap_pct", "flag"])
    w.writeheader()
    w.writerows(ROWS)

# ---- reconciliation scorecard per district ----
flags = defaultdict(int); checks = defaultdict(int)
for r in ROWS:
    if r["check"] in ("C22_timeliness",):
        continue
    checks[r["district"]] += 1
    flags[r["district"]] += 1 if r["flag"] == "Y" else 0
print(f"wrote data/integrity-checks.csv: {len(ROWS)} check-results, "
      f"{sum(1 for r in ROWS if r['flag']=='Y')} flagged\n")
print(f"{'District':28}{'checks':>8}{'flags':>7}{'flag rate':>11}")
for d in sorted(DISTS, key=lambda d: -flags[d] / max(checks[d], 1)):
    print(f"{d:28}{checks[d]:>8}{flags[d]:>7}{(flags[d]/max(checks[d],1)*100):>10.0f}%")
