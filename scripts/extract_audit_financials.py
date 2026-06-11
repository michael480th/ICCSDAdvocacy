#!/usr/bin/env python3
"""
Extract audited General Fund figures from each district's ACFR PDF (auditreports/), for the
CAR-vs-audited reporting-integrity screen. Position-aware and region-aware:
  * picks the EARLIEST basic Governmental Funds statements (combining/budget schedules come later),
  * gathers the statement across its 1-3 pages,
  * reads the General Fund column (first value column; "-" zeros handled),
  * self-validates every row against accounting identities and writes pass/fail flags.

Scope: the 13 large in-scope districts (5,000+ students). Fields (General Fund):
  revenues, expenditures, net_change, beginning_balance, ending_balance, restated,
  cash, fb_nonspendable, fb_restricted, fb_committed, fb_assigned, fb_unassigned, fb_total
  + checks: ok_rollforward (begin+net==end), ok_fbsum (components==total)

-> data/audit-financials.csv   (validated against data/iowa-district-financials.csv for FY2020-2023)
"""
import fitz, re, csv, os

STEM = {"Ankeny CSD": "Ankeny CSD", "Cedar Rapids CSD": "Cedar Rapids CSD",
        "College CSD (Prairie)": "College CSD", "Davenport CSD": "Davenport CSD",
        "Des Moines Independent CSD": "Des Moines Independent CSD", "Dubuque CSD": "Dubuque CSD",
        "Iowa City CSD": "Iowa City CSD", "Johnston CSD": "Johnston CSD", "Linn-Mar CSD": "Linn-Mar CSD",
        "Pleasant Valley CSD": "Pleasant Valley CSD", "Waterloo CSD": "Waterloo CSD",
        "Waukee CSD": "Waukee CSD", "West Des Moines CSD": "West Des Moines CSD"}
YEARS = range(2015, 2024)
NUM = re.compile(r'^\(?\$?(\d{1,3}(?:,\d{3})+|\d{4,})\)?$')
BAD = ("combining", "budget", "nonmajor", "schedule", "budgetary")


def val(tok):
    t = tok.strip()
    if t in ("-", "—", "–"):
        return 0.0
    m = NUM.match(t)
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return -v if t.startswith("(") else v


def rows_of(page):
    rows = {}
    for w in page.get_text("words"):
        rows.setdefault(round(w[1] / 3) * 3, []).append((w[0], w[4]))
    return [[t for _, t in sorted(r)] for _, r in sorted(rows.items())]


def first_value(row):
    for t in row:
        v = val(t)
        if v is not None:
            return v
    return None


def find(rows, pred, reverse=False):
    for r in (reversed(rows) if reverse else rows):
        if pred(" ".join(r).lower()):
            v = first_value(r)
            if v is not None:
                return v
    return None


def region(doc, is_stmt):
    """rows of the earliest basic GF statement (1-3 pages)."""
    for i in range(doc.page_count):
        low = doc[i].get_text().lower()
        ok = (("statement of revenues, expenditures" in low) if is_stmt
              else ("balance sheet" in low and "governmental funds" in low))
        if ok and "general" in low and not any(b in low for b in BAD):
            rows = []
            for j in range(i, min(i + 3, doc.page_count)):
                lj = doc[j].get_text().lower()
                if j > i and ("statement of revenues" in lj or "balance sheet" in lj) and j != i:
                    break  # next statement started
                rows += rows_of(doc[j])
                if is_stmt and "end of year" in lj:
                    break
                if not is_stmt and "total fund balance" in lj:
                    break
            return rows
    return []


def extract(path):
    doc = fitz.open(path)
    d = {k: None for k in FIELDS}
    r = region(doc, True)
    if r:
        d["revenues"] = find(r, lambda t: t.startswith("total revenues"))
        d["expenditures"] = find(r, lambda t: t.startswith("total expenditures"))
        d["net_change"] = find(r, lambda t: "change in fund balance" in t)
        d["beginning_balance"] = find(r, lambda t: t.startswith("fund balance") and "beginning" in t and "restat" not in t)
        d["ending_balance"] = find(r, lambda t: t.startswith("fund balance") and ("end of year" in t or "ending" in t))
        d["restated"] = "Y" if any("as restated" in " ".join(x).lower() for x in r) else ""
    b = region(doc, False)
    if b:
        d["cash"] = find(b, lambda t: t.startswith("cash") and "flow" not in t)
        d["fb_nonspendable"] = find(b, lambda t: t.startswith("nonspendable"), reverse=True)
        d["fb_restricted"] = find(b, lambda t: t.startswith("restricted") and "cash" not in t, reverse=True)
        d["fb_committed"] = find(b, lambda t: t.startswith("committed"), reverse=True)
        d["fb_assigned"] = find(b, lambda t: t.startswith("assigned"), reverse=True)
        d["fb_unassigned"] = find(b, lambda t: t.startswith("unassigned"), reverse=True)
        d["fb_total"] = find(b, lambda t: t.startswith("total fund balance"), reverse=True)
    # self-validation
    def close(a, c, tol=2):
        return a is not None and c is not None and abs(a - c) <= max(tol, abs(c) * 0.001)
    bb, nc, eb = d["beginning_balance"], d["net_change"], d["ending_balance"]
    d["ok_rollforward"] = "Y" if (bb is not None and nc is not None and eb is not None and close(bb + nc, eb)) else ""
    comps = [d[c] for c in ("fb_nonspendable", "fb_restricted", "fb_committed", "fb_assigned", "fb_unassigned")]
    if d["fb_total"] is not None and all(c is not None for c in comps):
        d["ok_fbsum"] = "Y" if close(sum(comps), d["fb_total"]) else ""
    else:
        d["ok_fbsum"] = ""
    return d


FIELDS = ["revenues", "expenditures", "net_change", "beginning_balance", "ending_balance", "restated",
          "cash", "fb_nonspendable", "fb_restricted", "fb_committed", "fb_assigned", "fb_unassigned",
          "fb_total", "ok_rollforward", "ok_fbsum"]
COLS = ["district", "fiscal_year"] + FIELDS

if __name__ == "__main__":
    out = []
    for name, stem in STEM.items():
        for fy in YEARS:
            p = f"auditreports/{stem}-{fy}.pdf"
            if not os.path.exists(p):
                continue
            d = extract(p)
            d["district"], d["fiscal_year"] = name, fy
            out.append(d)
    with open("data/audit-financials.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    roll = sum(1 for d in out if d["ok_rollforward"] == "Y")
    print(f"wrote data/audit-financials.csv: {len(out)} rows; {roll} pass roll-forward self-check")
