#!/usr/bin/env python3
"""
Extract each district's *audited* Student Activity fund balance from its ACFR PDF
(auditreports/<stem>-<FY>.pdf), for the 15 benchmarked districts, FY2020-FY2024 -> the
year-end balance of the Student Activity special-revenue fund.

In an Iowa ACFR the figure surfaces in several equivalent places that all tie to the same
dollar amount: the government-wide Statement of Net Position ("Restricted for ... student
activities"), the fund-balance note, and the (Combining) Balance Sheet's Student-Activity
column ("Restricted" / "Total fund balances"). We read every numeric token that sits on a row
labeled "student activit(y/ies)" (or an "Activity" / "Student activity fund" line) across the
whole document, then disambiguate using the CAR Activity balance as an oracle: the CAR
(district self-report) and the audit reconcile to the dollar for this fund, so among the
candidates we keep the one closest to CAR. A candidate within max($2, 0.5%) of CAR is
`confidence=high`; otherwise the nearest value is kept as `low` (review it). District-years
with no Student-Activity line found (or no ACFR on file) are emitted blank.

Reuses the fitz word-geometry helpers from extract_audit_financials.py.

-> data/activity-fund-audited.csv  (district, fiscal_year, audited_activity_balance,
                                    car_activity_balance, diff, source_page, confidence)
"""
import fitz, re, csv, os

# PDF filename stems (auditreports/<stem>-<FY>.pdf). College's ACFRs are filed as "College CSD".
STEM = {"Ankeny CSD": "Ankeny CSD", "Burlington CSD": "Burlington CSD",
        "Cedar Rapids CSD": "Cedar Rapids CSD", "College CSD (Prairie)": "College CSD",
        "Davenport CSD": "Davenport CSD", "Des Moines Independent CSD": "Des Moines Independent CSD",
        "Dubuque CSD": "Dubuque CSD", "Iowa City CSD": "Iowa City CSD", "Johnston CSD": "Johnston CSD",
        "Linn-Mar CSD": "Linn-Mar CSD", "Muscatine CSD": "Muscatine CSD",
        "Pleasant Valley CSD": "Pleasant Valley CSD", "Waterloo CSD": "Waterloo CSD",
        "Waukee CSD": "Waukee CSD", "West Des Moines CSD": "West Des Moines CSD"}
YEARS = range(2020, 2025)  # FY2020-FY2024

# CAR district codes -> benchmark name (to load the CAR oracle)
CODE = {261: "Ankeny CSD", 882: "Burlington CSD", 1053: "Cedar Rapids CSD",
        1337: "College CSD (Prairie)", 1611: "Davenport CSD", 1737: "Des Moines Independent CSD",
        1863: "Dubuque CSD", 3141: "Iowa City CSD", 3231: "Johnston CSD", 3715: "Linn-Mar CSD",
        4581: "Muscatine CSD", 5250: "Pleasant Valley CSD", 6795: "Waterloo CSD",
        6822: "Waukee CSD", 6957: "West Des Moines CSD"}

NUM = re.compile(r'^\(?\$?(\d{1,3}(?:,\d{3})+|\d{4,})\)?$')


def norm(s):
    return s.replace("\xa0", " ").replace("‐", "-")


def val(tok):
    t = tok.strip().rstrip("*")
    if t in ("-", "—", "–"):
        return 0.0
    m = NUM.match(t)
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return -v if t.startswith("(") else v


def rows_of(page):
    """group a page's words into visual rows by y; each row -> list of (x0, text), x-sorted."""
    rows = {}
    for w in page.get_text("words"):
        x0, y, t = w[0], w[1], norm(w[4])
        rows.setdefault(round(y / 3) * 3, []).append((x0, t))
    return [sorted(rows[k]) for k in sorted(rows)]


# a row whose label identifies the student-activity fund / its restricted balance
ACT_LABEL = re.compile(r'student activit|^activity\b|^student activity fund|activity fund')


def candidates(path):
    """all (value, page) on rows that name the student-activity fund, across the document."""
    doc = fitz.open(path)
    out = []
    for pno in range(doc.page_count):
        page = doc[pno]
        if "activit" not in norm(page.get_text()).lower():
            continue
        for row in rows_of(page):
            label = " ".join(t for _, t in row).lower().strip()
            if not ACT_LABEL.search(label):
                continue
            # skip obvious revenue/expenditure-detail contexts? No -- keep all numbers on the
            # line; CAR-guided selection below discards the non-balance ones.
            for _, t in row:
                v = val(t)
                if v is not None and v > 0:
                    out.append((v, pno + 1, label[:70]))
    doc.close()
    return out


def load_car():
    car = {}
    with open("data/car-fund-balances.csv") as fh:
        for r in csv.DictReader(fh):
            if r["fund"] != "Activity":
                continue
            try:
                c = int(r["district_code"])
            except (TypeError, ValueError):
                continue
            if c in CODE and r["ending_balance"]:
                car[(CODE[c], int(r["fiscal_year"]))] = float(r["ending_balance"])
    return car


def pick(cands, car_val):
    """choose the candidate closest to the CAR oracle (the audit ties to CAR for this fund)."""
    if not cands:
        return None, None, None
    if car_val is None:
        # no oracle (e.g. a year CAR lacks Activity): take the most frequent value
        from collections import Counter
        v, _ = Counter(c[0] for c in cands).most_common(1)[0]
        page = next(p for val_, p, _ in cands if val_ == v)
        return v, page, None
    best = min(cands, key=lambda c: abs(c[0] - car_val))
    return best[0], best[1], best[0] - car_val


if __name__ == "__main__":
    car = load_car()
    rows = []
    for name, stem in STEM.items():
        for fy in YEARS:
            p = f"auditreports/{stem}-{fy}.pdf"
            car_val = car.get((name, fy))
            if not os.path.exists(p):
                rows.append([name, fy, "", f"{car_val:.2f}" if car_val is not None else "",
                             "", "", "no_audit"])
                continue
            cands = candidates(p)
            v, page, diff = pick(cands, car_val)
            if v is None:
                conf = "not_found"
            elif car_val is None:
                conf = "no_car_oracle"
            else:
                conf = "high" if abs(diff) <= max(2.0, abs(car_val) * 0.005) else "low"
            rows.append([name, fy,
                         f"{v:.2f}" if v is not None else "",
                         f"{car_val:.2f}" if car_val is not None else "",
                         f"{diff:.2f}" if diff is not None else "",
                         page if page is not None else "", conf])

    os.makedirs("data", exist_ok=True)
    with open("data/activity-fund-audited.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["district", "fiscal_year", "audited_activity_balance",
                    "car_activity_balance", "diff", "source_page", "confidence"])
        w.writerows(rows)

    by_conf = {}
    for r in rows:
        by_conf[r[6]] = by_conf.get(r[6], 0) + 1
    print("wrote data/activity-fund-audited.csv:", len(rows), "district-years")
    print("  by confidence:", dict(sorted(by_conf.items())))
    print("  flagged (low / not_found):")
    for r in rows:
        if r[6] in ("low", "not_found"):
            print(f"    {r[0]} FY{r[1]}: audited={r[2] or '-'} car={r[3] or '-'} diff={r[4] or '-'} p{r[5]} [{r[6]}]")
