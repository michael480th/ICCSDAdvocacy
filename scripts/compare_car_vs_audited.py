#!/usr/bin/env python3
"""
Compare each district's CAR (unaudited, self-reported) General Fund balances to its audited
ACFR figures, for the 15 benchmarked districts, every overlapping fiscal year. Flags material
divergences — the red flag being a CAR that does not reconcile to the audit.

Inputs : data/car-fund-balances.csv      (from extract_car.py)
         data/iowa-district-financials.csv (audited ACFR data)
Output : data/car-vs-audited.csv          (one row per district-year, with flags)

A row is flagged when the CAR ending General Fund balance differs from the audited ending
balance by >= 1.0% AND >= $250,000 — i.e. a difference too big to be rounding/classification.
"""
import csv

CODE = {261: "Ankeny CSD", 882: "Burlington CSD", 1053: "Cedar Rapids CSD",
        1337: "College CSD (Prairie)", 1611: "Davenport CSD", 1737: "Des Moines Independent CSD",
        1863: "Dubuque CSD", 3141: "Iowa City CSD", 3231: "Johnston CSD", 3715: "Linn-Mar CSD",
        4581: "Muscatine CSD", 5250: "Pleasant Valley CSD", 6795: "Waterloo CSD",
        6822: "Waukee CSD", 6957: "West Des Moines CSD"}
THRESH_PCT, THRESH_ABS = 1.0, 250_000


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# CAR General Fund, keyed (name, fy)
car = {}
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["fund"] != "General":
        continue
    c = int(r["district_code"])
    if c in CODE:
        car[(CODE[c], int(r["fiscal_year"]))] = dict(
            beg=num(r["beginning_balance"]), end=num(r["ending_balance"]),
            rev=num(r["revenues"]), exp=num(r["expenditures"]))

# Audited, keyed (name, fy)
aud = {}
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    aud[(r["district"], int(r["fiscal_year"]))] = dict(
        end=num(r["gf_total_fund_balance"]), rev=num(r["gf_revenue"]), exp=num(r["gf_expenditure"]))

rows = []
for (name, fy) in sorted(car):
    a = aud.get((name, fy))
    c = car[(name, fy)]
    if not a or a["end"] is None or c["end"] is None:
        continue
    diff = c["end"] - a["end"]
    pct = diff / a["end"] * 100 if a["end"] else 0.0
    flag = "Y" if (abs(pct) >= THRESH_PCT and abs(diff) >= THRESH_ABS) else ""
    # beginning balance should equal the prior year's audited ending
    prior = aud.get((name, fy - 1))
    beg_tie = (c["beg"] - prior["end"]) if (prior and prior["end"] is not None and c["beg"] is not None) else None
    # net change reported vs audited net change
    car_net = (c["end"] - c["beg"]) if c["beg"] is not None else None
    aud_net = (a["end"] - prior["end"]) if (prior and prior["end"] is not None) else None
    rows.append([name, fy, c["end"], a["end"], round(diff), round(pct, 2), flag,
                 c["beg"], (prior["end"] if prior else None),
                 (round(beg_tie) if beg_tie is not None else None),
                 (round(car_net) if car_net is not None else None),
                 (round(aud_net) if aud_net is not None else None)])

with open("data/car-vs-audited.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["district", "fiscal_year", "car_ending", "audited_ending",
                "ending_diff", "ending_diff_pct", "flag",
                "car_beginning", "prior_audited_ending", "beginning_vs_prior_audited",
                "car_net_change", "audited_net_change"])
    w.writerows(rows)

flagged = [r for r in rows if r[6] == "Y"]
print(f"wrote data/car-vs-audited.csv: {len(rows)} district-years, {len(flagged)} flagged\n")
print(f"{'District':28s}{'FY':>5}{'CAR end':>14}{'Audited end':>14}{'Diff':>12}{'%':>8}  flag")
for r in rows:
    mark = "  <== FLAG" if r[6] == "Y" else ""
    print(f"{r[0]:28s}{r[1]:>5}{r[2]:>14,.0f}{r[3]:>14,.0f}{r[4]:>+12,.0f}{r[5]:>+7.1f}%{mark}")
