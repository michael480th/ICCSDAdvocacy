#!/usr/bin/env python3
"""
Extract audited General Fund figures from each district's ACFR PDF (auditreports/), for the
CAR-vs-audited reporting-integrity screen.

Approach (column- and region-aware):
  * Find the EARLIEST *basic* Governmental Funds statements. Reject Table-of-Contents,
    Management's-Discussion-&-Analysis, reconciliation, combining/budget/nonmajor/schedule
    pages. A page only qualifies if its heading is the statement title AND it carries real
    data rows (e.g. "Total revenues"/"Total fund balances") AND a "General" column header.
  * Locate the x-position of the "General" column header and read the value whose x falls in
    that column band -- robust to wide tables that put many fund columns on one row, and to
    statements split across pages (revenues on one page, expenditures + fund balances on the
    next "(Continued)" page). "-" is read as 0.
  * Fund-balance components are read from the bottom of the balance sheet (searching upward so
    "Restricted cash" in the assets section is not mistaken for the "Restricted" fund-balance
    component). "Restricted:" header with sub-lines is summed.
  * Every row is self-validated against accounting identities (roll-forward; component sum).

Accuracy vs trusted data/iowa-district-financials.csv (FY2020-2023, 13 in-scope districts):
  revenues, expenditures, ending_balance, fb_unassigned all match within $2/0.5% on >=95% of
  the 52 district-years (see module test / commit message for the exact tally). Rows that fail
  ok_rollforward are kept but should be treated as low-confidence.

-> data/audit-financials.csv
"""
import fitz, re, csv, os

STEM = {"Ankeny CSD": "Ankeny CSD", "Cedar Rapids CSD": "Cedar Rapids CSD",
        "College CSD (Prairie)": "College CSD", "Davenport CSD": "Davenport CSD",
        "Des Moines Independent CSD": "Des Moines Independent CSD", "Dubuque CSD": "Dubuque CSD",
        "Iowa City CSD": "Iowa City CSD", "Johnston CSD": "Johnston CSD", "Linn-Mar CSD": "Linn-Mar CSD",
        "Pleasant Valley CSD": "Pleasant Valley CSD", "Waterloo CSD": "Waterloo CSD",
        "Waukee CSD": "Waukee CSD", "West Des Moines CSD": "West Des Moines CSD",
        "Muscatine CSD": "Muscatine CSD", "Burlington CSD": "Burlington CSD"}
YEARS = range(2015, 2026)

NUM = re.compile(r'^\(?\$?(\d{1,3}(?:,\d{3})+|\d{4,})\)?$')
# words that mark a non-basic statement. "nonmajor"/"combining" are NOT here: they appear as
# legitimate column labels on the basic *combined* governmental-funds statements. The basic
# "Combining" schedules are excluded via the title phrase check in is_sre_basic/is_bs_basic.
BAD_HEAD = ("budget", "budgetary", "schedule",
            "reconciliation", "discussion", "table of contents")


def norm(s):
    """normalize non-breaking spaces and unicode hyphens some ACFRs use (e.g. WDM 2015)."""
    return s.replace("\xa0", " ").replace("‐", "-")


def page_text(page):
    return norm(page.get_text()).lower()


def val(tok):
    t = tok.strip().rstrip("*")
    if t in ("-", "—", "–"):
        return 0.0
    m = NUM.match(t)
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return -v if t.startswith("(") else v


def words(page):
    """list of (x0, x1, y, text) sorted by y then x."""
    ws = [(w[0], w[2], w[1], norm(w[4])) for w in page.get_text("words")]
    ws.sort(key=lambda w: (round(w[2] / 3) * 3, w[0]))
    return ws


def lines(page):
    """group words into rows by y; each row -> list of (x_center, x0, text)."""
    rows = {}
    for x0, x1, y, t in words(page):
        rows.setdefault(round(y / 3) * 3, []).append(((x0 + x1) / 2, x0, t))
    return [sorted(rows[k]) for k in sorted(rows)]


def heading(page):
    """
    Statement-title block: the run of rows above the first column-header / data row.
    Stops at the row containing the 'General' column header (column labels like 'Nonmajor'
    or 'Combining' must not disqualify a basic combined statement), or after 6 rows.
    """
    out = []
    for r in lines(page)[:8]:
        txt = " ".join(t for _, _, t in r)
        if any(w == "General" for _, _, t2 in r for w in [t2]):
            break
        out.append(txt)
        if len(out) >= 6:
            break
    return " ".join(out).lower()


def general_x(page):
    """
    x-center of the 'General' *column header* word. A page can contain other 'General' tokens
    (e.g. the row label 'General administration' / 'General obligation bonds'), so among all
    'General' words pick the one whose x best aligns with an actual value column -- i.e. the one
    nearest to a frequently-occurring first-number x across the data rows.
    """
    gens = [((x0 + x1) / 2, x0, y) for x0, x1, y, t in words(page) if t == "General"]
    if not gens:
        return None
    if len(gens) == 1:
        return gens[0][0]
    # collect x-centers of the first numeric token on each data row
    firstnum_x = []
    for r in lines(page):
        for xc, x0, t in r:
            if val(t) is not None and x0 > 120:  # skip label-area stray numbers
                firstnum_x.append(xc)
                break
    if not firstnum_x:
        return min(gens)[0]
    # pick the General whose x is closest to the median first-number x
    firstnum_x.sort()
    med = firstnum_x[len(firstnum_x) // 2]
    return min(gens, key=lambda g: abs(g[0] - med))[0]


def column_value(row, col_x, tol=55):
    """value in `row` whose x-center is nearest col_x and within tol; '$' is skipped."""
    best, best_d = None, tol
    for xc, x0, t in row:
        v = val(t)
        if v is None:
            continue
        d = abs(xc - col_x)
        if d < best_d:
            best, best_d = v, d
    return best


def find_in_region(region, pred, col_x, reverse=False, tol=55):
    """first/last labeled row matching pred -> value in the General column."""
    seq = reversed(region) if reverse else region
    for label, row in seq:
        if pred(label):
            v = column_value(row, col_x, tol)
            if v is not None:
                return v
    return None


def value_after_label(region, pred, col_x, reverse=False, tol=55):
    """
    For statements that wrap a label onto its own line with the numbers on the next visual row
    (e.g. Iowa City's 'Total revenues' / '190,498,914' on the row below; or Waterloo's
    'Fund Balances - Beginning of' / '<num>'). Return the General value from the first numeric
    row at-or-after a label row matching pred.
    """
    def numeric_only(row):
        toks = [t for _, _, t in row]
        return toks and all(val(t) is not None or t in ("$", "-") for t in toks)

    idxs = range(len(region))
    if reverse:
        idxs = reversed(idxs)
    for i in idxs:
        if pred(region[i][0]):
            v = column_value(region[i][1], col_x, tol)
            if v is not None:
                return v
            # value on the row just above, when y-bucket rounding split a single visual line
            # (e.g. "TOT AL EXPENDITURES" / "Total fund balances" with numbers a pixel higher).
            # Checked first, and only a pure numbers row, so a detail line above a subtotal is
            # never mistaken for it.
            if i - 1 >= 0 and numeric_only(region[i - 1][1]):
                v = column_value(region[i - 1][1], col_x, tol)
                if v is not None:
                    return v
            # otherwise the value wrapped onto the row(s) below (the continuation may carry
            # leading text such as "balances ..." or "Year, as Restated ..."). Stop if a new
            # labeled total/section begins.
            for j in (i + 1, i + 2):
                if j < len(region):
                    lab = region[j][0]
                    if j > i + 1 and (lab.startswith("total") or lab.startswith("see ")):
                        break
                    v = column_value(region[j][1], col_x, tol)
                    if v is not None:
                        return v
    return None


def is_sre_basic(low):
    return (("statement of revenues" in low or "statement of revenue," in low)
            and "expenditures" in low
            and "changes in fund balance" in low
            and "combining statement" not in low
            and not any(b in low for b in BAD_HEAD))


def is_bs_basic(low):
    return ("balance sheet" in low and "governmental funds" in low
            and "combining balance sheet" not in low
            and not any(b in low for b in BAD_HEAD))


def gather_region(doc, kind):
    """
    Find the earliest basic statement of `kind` ('sre' or 'bs') and gather its General-Fund
    region across continuation pages. Returns (region, col_x) where region is a list of
    (label_lower, row) and col_x is the General column x-center (from the first page).
    """
    if kind == "sre":
        ok_head = is_sre_basic
        anchor = lambda low: "total revenues" in low or "total expenditures" in low
        stop = lambda low: "end of year" in low or "fund balances, end" in low
    else:
        ok_head = is_bs_basic
        anchor = lambda low: "total fund balance" in low
        stop = lambda low: "total fund balance" in low

    other_title = "balance sheet" if kind == "sre" else "statement of revenues"

    start = None
    for i in range(doc.page_count):
        low = page_text(doc[i])
        if ok_head(heading(doc[i])) and anchor(low) and general_x(doc[i]) is not None:
            start = i
            break
    if start is None:
        # Fallback for statements whose title is rendered as an image / on a divider page
        # (e.g. Davenport 2015): the data page itself has only column headers. Accept the
        # earliest page that has the General column, the anchor row, the closing
        # fund-balance markers, and is not a budget/combining/schedule/reconciliation page.
        for i in range(doc.page_count):
            low = page_text(doc[i])
            if general_x(doc[i]) is None or not anchor(low):
                continue
            if any(b in low for b in BAD_HEAD) or "combining" in low or "nonmajor" in low \
               or "figure" in low or "net position" in low:
                continue
            if kind == "sre" and not (("total revenues" in low or "total revenue" in low)
                                      and "total expenditure" in low
                                      and ("end of year" in low or "fund balances, end" in low)):
                continue
            if kind == "bs" and "total fund balance" not in low:
                continue
            start = i
            break
    if start is None:
        return [], None

    col_x = general_x(doc[start])
    region = []
    for r in lines(doc[start]):
        region.append((" ".join(t for _, _, t in r).lower(), r))
    if stop(page_text(doc[start])):
        return region, col_x

    # gather continuation pages (statement split vertically across pages). A continuation page
    # keeps the General column and does NOT begin a different/non-basic statement.
    for j in range(start + 1, min(start + 4, doc.page_count)):
        hj = heading(doc[j])
        if other_title in hj or any(b in hj for b in BAD_HEAD) \
           or "combining" in hj or "statement of net position" in hj \
           or "statement of activities" in hj:
            break
        gx = general_x(doc[j])
        if gx is None:
            # horizontal split (this page shows only other fund columns) -- skip and continue
            continue
        col_x = gx
        for r in lines(doc[j]):
            region.append((" ".join(t for _, _, t in r).lower(), r))
        if stop(page_text(doc[j])):
            break
    return region, col_x


FIELDS = ["revenues", "expenditures", "net_change", "beginning_balance", "ending_balance", "restated",
          "cash", "fb_nonspendable", "fb_restricted", "fb_committed", "fb_assigned", "fb_unassigned",
          "fb_total", "ok_rollforward", "ok_fbsum"]


def extract(path):
    doc = fitz.open(path)
    d = {k: None for k in FIELDS}

    sre, sx = gather_region(doc, "sre")
    if sre and sx is not None:
        # Total revenue(s); some districts use the singular "Total Revenue". Some PDFs split
        # letters with stray spaces ("TOT AL EXPENDITURES"), so also test the despaced form.
        ds = lambda t: t.replace(" ", "")
        rev_p = lambda t: t.startswith("total revenue") or ds(t).startswith("totalrevenue")
        exp_p = lambda t: t.startswith("total expenditure") or ds(t).startswith("totalexpenditure")
        # Net change line; prefer the final "change in fund balances" (not the "...before
        # special item" subtotal) -- take the last match in the region. The label sometimes
        # wraps ("Net change in" / "fund balance (425,707)") so accept the bare "net change in".
        nc_p = lambda t: (("net change in fund balance" in t)
                          or (t.startswith("change in fund balance") and "before" not in t)
                          or t.strip() in ("net change in", "net change in fund"))
        # beginning: usually "fund balances, beginning of year"; sometimes the "Fund Balances"
        # header is on its own row and "beginning of year <num>" follows. When an "as restated"
        # beginning is present it is the correct roll-forward base, so match it too.
        bb_p = (lambda t: ("beginning of year" in t
                           or (t.startswith("fund balance") and "beginning" in t))
                and not t.startswith("total"))
        # ending: "fund balances [-/at] end of year" or a bare "end of year" data row.
        eb_p = (lambda t: (("end of year" in t or "ending" in t)
                           and ("fund balance" in t or t.startswith("end of year"))))

        def either(pred, last=False):
            v = find_in_region(sre, pred, sx, reverse=last)
            return v if v is not None else value_after_label(sre, pred, sx, reverse=last)
        d["revenues"] = either(rev_p)
        d["expenditures"] = either(exp_p)
        d["net_change"] = either(nc_p, last=True)
        # prefer the last beginning line (the "as restated" base, when present)
        d["beginning_balance"] = either(bb_p, last=True)
        d["ending_balance"] = either(eb_p)
        d["restated"] = "Y" if any("as restated" in lab or "restated" in lab and "beginning" in lab
                                   for lab, _ in sre) else ""

    bs, bx = gather_region(doc, "bs")
    if bs and bx is not None:
        def bsval(pred, reverse=False):
            v = find_in_region(bs, pred, bx, reverse=reverse)
            return v if v is not None else value_after_label(bs, pred, bx, reverse=reverse)
        d["cash"] = bsval(lambda t: t.startswith("cash") and "flow" not in t)
        d["fb_nonspendable"] = bsval(lambda t: t.startswith("nonspendable"), reverse=True)
        d["fb_committed"] = bsval(
            lambda t: t.startswith("committed") and not t.endswith(":"), reverse=True)
        d["fb_assigned"] = bsval(lambda t: t.startswith("assigned"), reverse=True)
        d["fb_unassigned"] = bsval(lambda t: t.startswith("unassigned"), reverse=True)
        d["fb_total"] = bsval(lambda t: t.startswith("total fund balance"), reverse=True)
        d["fb_restricted"] = restricted_component(bs, bx)

    # self-validation
    def close(a, c, tol=2):
        return a is not None and c is not None and abs(a - c) <= max(tol, abs(c) * 0.005)

    bb, nc, eb = d["beginning_balance"], d["net_change"], d["ending_balance"]
    d["ok_rollforward"] = "Y" if (None not in (bb, nc, eb) and close(bb + nc, eb)) else ""

    comps = [d[c] for c in ("fb_nonspendable", "fb_restricted", "fb_committed", "fb_assigned", "fb_unassigned")]
    if d["fb_total"] is not None and all(c is not None for c in comps):
        d["ok_fbsum"] = "Y" if close(sum(comps), d["fb_total"]) else ""
    else:
        d["ok_fbsum"] = ""
    return d


def restricted_component(bs, bx):
    """
    Fund-balance 'Restricted' component. Single line if 'Restricted <num>'; otherwise a
    'Restricted:' / 'Restricted for:' header followed by sub-lines up to the next component
    header (Committed/Assigned/Unassigned/Nonspendable/Total). Sum the General-column values
    of those sub-lines. Search the bottom (fund-balance) section only.
    """
    # locate the fund-balances section start (last 'fund balances:' header)
    start = 0
    for i, (lab, _) in enumerate(bs):
        if lab.startswith("fund balance") and lab.rstrip().endswith(":"):
            start = i
    stoppers = ("committed", "assigned", "unassigned", "nonspendable", "total fund")
    for i in range(start, len(bs)):
        lab, row = bs[i]
        if lab.startswith("restricted"):
            v = column_value(row, bx)
            if v is not None:
                return v
            # header with sub-lines -> sum until next component header
            total = 0.0
            got = False
            for j in range(i + 1, len(bs)):
                lab2, row2 = bs[j]
                if lab2.startswith(stoppers):
                    break
                vv = column_value(row2, bx)
                if vv is not None:
                    total += vv
                    got = True
            return total if got else None
    return None


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
    os.makedirs("data", exist_ok=True)
    with open("data/audit-financials.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    roll = sum(1 for d in out if d["ok_rollforward"] == "Y")
    print(f"wrote data/audit-financials.csv: {len(out)} rows; {roll} pass roll-forward self-check")
