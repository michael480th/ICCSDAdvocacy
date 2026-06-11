#!/usr/bin/env python3
"""
CAR-vs-audited reporting-integrity screen for the benchmarked districts.

Compares each district's UNAUDITED Certified Annual Report to its AUDITED ACFR (General Fund),
per district per year, and scores how reliably its self-reported numbers tie out.

Inputs:
  data/car-fund-balances.csv          CAR beginning/revenue/expenditure/ending by fund (FY2017-2024);
                                      unassigned/assigned + workbook cash for FY2023-2024
  data/audit-financials.csv           AUDITED ACFR General Fund figures, FY2015-2023, 13 large
                                      districts (revenue, expenditure, net change, beginning/ending,
                                      cash, fund-balance components, restatement flag) -- the
                                      machine-extracted, self-validated layer
  data/iowa-district-financials.csv   curated audited figures: supplies report_date (audit lag) and
                                      Burlington/Muscatine (the two non-large districts), FY2020-2023

Comparison checks run FY2017-2023 (the CAR window); audited-only checks (restatement, audit lag) use
whatever audited years exist. Output: data/integrity-checks.csv + a printed scorecard.
"""
import csv, openpyxl, datetime, glob
from collections import defaultdict

CODE = {261: "Ankeny CSD", 882: "Burlington CSD", 1053: "Cedar Rapids CSD", 1337: "College CSD (Prairie)",
        1611: "Davenport CSD", 1737: "Des Moines Independent CSD", 1863: "Dubuque CSD", 3141: "Iowa City CSD",
        3231: "Johnston CSD", 3715: "Linn-Mar CSD", 4581: "Muscatine CSD", 5250: "Pleasant Valley CSD",
        6795: "Waterloo CSD", 6822: "Waukee CSD", 6957: "West Des Moines CSD"}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---- CAR (General Fund) ----
car = {}
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["fund"] == "General" and int(r["district_code"]) in CODE:
        car[(CODE[int(r["district_code"])], int(r["fiscal_year"]))] = dict(
            beg=num(r["beginning_balance"]), rev=num(r["revenues"]), exp=num(r["expenditures"]),
            end=num(r["ending_balance"]), un=num(r["gf_unassigned"]), asg=num(r["gf_assigned"]))
for fy, pat in [(2023, "CAR/2022_2023 CAR data*.xlsx"), (2024, "CAR/2023_2024 CAR data*.xlsx")]:
    ws = openpyxl.load_workbook(glob.glob(pat)[0], data_only=True, read_only=True)["BalSheetData1"]
    h = {v: i for i, v in enumerate(list(ws.iter_rows(min_row=3, max_row=3, values_only=True))[0]) if v}
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[1] in CODE and (CODE[row[1]], fy) in car:
            car[(CODE[row[1]], fy)]["cash"] = row[h["gencashinvest"]]

# ---- Audited: primary = machine-extracted FY2015-2023 (13 districts) ----
aud = {}
for r in csv.DictReader(open("data/audit-financials.csv")):
    aud[(r["district"], int(r["fiscal_year"]))] = dict(
        rev=num(r["revenues"]), exp=num(r["expenditures"]), net=num(r["net_change"]),
        beg=num(r["beginning_balance"]), end=num(r["ending_balance"]), cash=num(r["cash"]),
        un=num(r["fb_unassigned"]), asg=num(r["fb_assigned"]), restated=(r["restated"] == "Y"),
        report=None)
# supplement: report_date (for audit-lag) + the 2 non-large districts, from the curated set
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    k = (r["district"], int(r["fiscal_year"]))
    if k in aud:
        aud[k]["report"] = r["report_date"]
    elif r["district"] in CODE.values():
        aud[k] = dict(rev=num(r["gf_revenue"]), exp=num(r["gf_expenditure"]), net=None,
                      beg=None, end=num(r["gf_total_fund_balance"]), cash=None,
                      un=num(r["gf_unassigned"]), asg=num(r["gf_assigned"]), restated=False,
                      report=r["report_date"])


def avail(d):
    return None if (d is None or d.get("un") is None) else d["un"] + (d.get("asg") or 0)


ROWS = []
DISTS = sorted(CODE.values())
ABS, PCTT = 250_000, 1.0
# Checks distorted by a known presentation convention (the CAR folds "other financing uses"/
# transfers into General Fund expenditures, the audit separates them). Shown for context but
# NOT flagged, so the reliability scorecard only reflects bottom-line figures that must tie.
INFORMATIONAL = {"C11_expenditure", "C12_transfers", "C13_margin", "C18_fb_pct_exp"}


def emit(dist, fy, cid, name, cv, av, kind="$"):
    if cv is None or av is None:
        return
    gap = cv - av
    if kind == "$":
        gp = (gap / av * 100) if av else None
        flag = "Y" if (gp is not None and abs(gp) >= PCTT and abs(gap) >= ABS) else ""
    else:  # ratio/points (%, days): flag on >= 3-point gap
        gp = None
        flag = "Y" if abs(gap) >= 3 else ""
    if cid in INFORMATIONAL:
        flag = ""
    ROWS.append(dict(district=dist, fiscal_year=fy, check=cid, name=name,
                     car=round(cv, 2), audited=round(av, 2), gap=round(gap, 2),
                     gap_pct=(round(gp, 2) if gp is not None else ""), flag=flag))


for d in DISTS:
    for y in range(2017, 2024):
        c, a = car.get((d, y)), aud.get((d, y))
        cprev, aprev = car.get((d, y - 1)), aud.get((d, y - 1))
        if c and a:
            emit(d, y, "C1_ending", "Ending GF fund balance", c["end"], a["end"])
            emit(d, y, "C2_available", "Available (unassigned+assigned)", avail(c), avail(a))
            emit(d, y, "C3_unassigned", "Unassigned (spendable) balance", c["un"], a["un"])
            emit(d, y, "C10_revenue", "GF revenue", c["rev"], a["rev"])
            emit(d, y, "C11_expenditure", "GF expenditure", c["exp"], a["exp"])
            if c["rev"]:
                emit(d, y, "C13_margin", "Operating margin %", (c["rev"] - c["exp"]) / c["rev"] * 100,
                     ((a["rev"] - a["exp"]) / a["rev"] * 100 if a["rev"] else None), "pts")
            if c.get("end") and c.get("exp"):
                emit(d, y, "C18_fb_pct_exp", "Fund balance % of expenditure", c["end"] / c["exp"] * 100,
                     (a["end"] / a["exp"] * 100 if a["exp"] else None), "pts")
            if avail(c) is not None and c["rev"]:
                emit(d, y, "C17_solvency", "Solvency ratio %", avail(c) / c["rev"] * 100,
                     (avail(a) / a["rev"] * 100 if (avail(a) is not None and a["rev"]) else None), "pts")
            if c.get("cash") is not None and a.get("cash") is not None:
                emit(d, y, "C14_cash", "GF operating cash", c["cash"], a["cash"])
                if c["exp"] and a["exp"]:
                    emit(d, y, "C15_days_cash", "Days cash on hand",
                         c["cash"] / (c["exp"] / 365), a["cash"] / (a["exp"] / 365), "pts")
            # transfers / other financing (net change not explained by rev-exp)
            if c["beg"] is not None and a.get("net") is not None:
                emit(d, y, "C12_transfers", "Other financing / transfers",
                     (c["end"] - c["beg"]) - (c["rev"] - c["exp"]), a["net"] - (a["rev"] - a["exp"]))
        # CAR internal roll-forward
        if c and cprev and c["beg"] is not None and cprev["end"] is not None:
            emit(d, y, "C6_rollforward", "CAR begin = prior CAR end", c["beg"], cprev["end"])
        # CAR beginning vs PRIOR-year audited ending
        if c and aprev and c["beg"] is not None and aprev["end"] is not None:
            emit(d, y, "C7_begin_vs_audit", "CAR begin vs prior audited end", c["beg"], aprev["end"])
        # net change: CAR vs audited (uses audited net_change directly when available)
        if c and a and c["beg"] is not None:
            an = a["net"] if a.get("net") is not None else (a["end"] - aprev["end"] if (aprev and aprev["end"] is not None) else None)
            if an is not None:
                emit(d, y, "C8_net_change", "Net change in fund balance", c["end"] - c["beg"], an)

# ---- audited-only meta checks ----
for (d, y), a in aud.items():
    if d not in DISTS or not (2015 <= y <= 2023):
        continue
    # restatement (a prior-period adjustment is itself a reliability flag)
    ROWS.append(dict(district=d, fiscal_year=y, check="C9_restatement", name="Beginning balance restated",
                     car="", audited=("Y" if a.get("restated") else "—"), gap="", gap_pct="",
                     flag=("Y" if a.get("restated") else "")))
    # audit lag in months after FYE (June 30)
    if a.get("report"):
        try:
            months = (datetime.date.fromisoformat(a["report"]) - datetime.date(y, 6, 30)).days / 30.44
            ROWS.append(dict(district=d, fiscal_year=y, check="C22_timeliness", name="Audit lag (months after FYE)",
                             car="", audited=round(months, 1), gap="", gap_pct="", flag=("Y" if months > 15 else "")))
        except ValueError:
            pass

with open("data/integrity-checks.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["district", "fiscal_year", "check", "name", "car", "audited", "gap", "gap_pct", "flag"])
    w.writeheader()
    w.writerows(ROWS)

flags = defaultdict(int); checks = defaultdict(int)
META = ("C22_timeliness", "C9_restatement")
for r in ROWS:
    if r["check"] in META:
        continue
    checks[r["district"]] += 1
    flags[r["district"]] += 1 if r["flag"] == "Y" else 0
yrs = sorted({r["fiscal_year"] for r in ROWS})
print(f"wrote data/integrity-checks.csv: {len(ROWS)} results, FY{min(yrs)}-{max(yrs)}, "
      f"{len({r['check'] for r in ROWS})} distinct checks, {sum(1 for r in ROWS if r['flag']=='Y')} flagged\n")
print(f"{'District':28}{'checks':>8}{'flags':>7}{'rate':>7}")
for d in sorted(DISTS, key=lambda d: -flags[d] / max(checks[d], 1)):
    print(f"{d:28}{checks[d]:>8}{flags[d]:>7}{flags[d]/max(checks[d],1)*100:>6.0f}%")
