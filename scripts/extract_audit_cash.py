#!/usr/bin/env python3
"""
Extract each district's audited General Fund cash & investments from the Governmental Funds
balance sheet in its ACFR PDF (auditreports/), to build a longer operating-cash trend than the
two CAR balance-sheet workbooks allow. -> data/gf-operating-cash.csv

The General Fund is the first fund column on the Balance Sheet - Governmental Funds, so the
first dollar figure on the "Cash ..." asset line is the General Fund's cash. Validated against
the CAR's gencashinvest for FY2023 (matches within rounding for the clean districts; Iowa City
and Des Moines differ for real). Iowa City's FY2024 cash comes from the CAR (no FY2024 audit).
"""
import fitz, re, csv, os, openpyxl

# 5,000+ peers + Iowa City (same size-matched group as the other reports); name -> audit PDF stem
DISTRICTS = {
    "Ankeny CSD": "Ankeny CSD", "Cedar Rapids CSD": "Cedar Rapids CSD",
    "College CSD (Prairie)": "College CSD", "Davenport CSD": "Davenport CSD",
    "Des Moines Independent CSD": "Des Moines Independent CSD", "Dubuque CSD": "Dubuque CSD",
    "Iowa City CSD": "Iowa City CSD", "Johnston CSD": "Johnston CSD", "Linn-Mar CSD": "Linn-Mar CSD",
    "Pleasant Valley CSD": "Pleasant Valley CSD", "Waterloo CSD": "Waterloo CSD",
    "Waukee CSD": "Waukee CSD", "West Des Moines CSD": "West Des Moines CSD",
}
NUM = re.compile(r'-?[\d,]{5,}')


def first_cash_number(lines):
    for j, l in enumerate(lines):
        if l.lower().startswith("cash") and "flow" not in l.lower():
            for k in range(j + 1, min(j + 8, len(lines))):
                m = NUM.search(lines[k])
                if m:
                    v = float(m.group().replace(",", ""))
                    if v > 10000:
                        return v
    return None


def gf_cash(path):
    doc = fitz.open(path)
    # primary: page titled Balance Sheet - Governmental Funds
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "Balance Sheet" in t and "Governmental Funds" in t:
            v = first_cash_number([l.strip() for l in t.split("\n")])
            if v:
                return v
    # fallback: a balance-sheet page with a General column and Total assets (older formats)
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "Balance Sheet" in t and "General" in t and "Total assets" in t:
            v = first_cash_number([l.strip() for l in t.split("\n")])
            if v:
                return v
    return None


rows = []
for name, stem in DISTRICTS.items():
    for fy in range(2015, 2026):
        p = f"auditreports/{stem}-{fy}.pdf"
        if not os.path.exists(p):
            continue
        v = gf_cash(p)
        if v is not None:
            rows.append([name, fy, round(v), "audit"])

# Iowa City FY2024: no audit filed -> use CAR balance sheet
wb = openpyxl.load_workbook("CAR/2023_2024 CAR data-for website (1).xlsx", data_only=True, read_only=True)
bs = wb["BalSheetData1"]
bh = {n: i for i, n in enumerate(list(bs.iter_rows(min_row=3, max_row=3, values_only=True))[0]) if n}
for r in bs.iter_rows(min_row=4, values_only=True):
    if r[1] == 3141:
        rows.append(["Iowa City CSD", 2024, round(r[bh["gencashinvest"]]), "CAR"])
        break

rows.sort(key=lambda r: (r[0], r[1]))
with open("data/gf-operating-cash.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["district", "fiscal_year", "gf_cash_investments", "source"])
    w.writerows(rows)
miss = [(n, fy) for n in DISTRICTS for fy in range(2015, 2026)
        if os.path.exists(f"auditreports/{DISTRICTS[n]}-{fy}.pdf")
        and not any(r[0] == n and r[1] == fy for r in rows)]
print(f"wrote data/gf-operating-cash.csv: {len(rows)} rows")
if miss:
    print("MISSING:", miss)
