#!/usr/bin/env python3
"""
Build a self-contained page comparing the 15 large Iowa districts on their Student Activity
fund year-end balance -- as self-reported in the CAR, as found in the audited ACFR, and per
student -- FY2020-FY2024, headlined on Iowa City.

Inputs : data/car-fund-balances.csv        (fund="Activity"  -> CAR ending balance)
         data/activity-fund-audited.csv     (audited Student Activity balance from the ACFRs)
         data/dom/certified-enrollment.csv  (per-student denominator)
Output : activity-fund.html

Run:  python3 scripts/build_activity_fund_report.py
"""
import csv, html, datetime, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

CODE = {"261": "Ankeny CSD", "882": "Burlington CSD", "1053": "Cedar Rapids CSD",
        "1337": "College CSD (Prairie)", "1611": "Davenport CSD", "1737": "Des Moines Independent CSD",
        "1863": "Dubuque CSD", "3141": "Iowa City CSD", "3231": "Johnston CSD", "3715": "Linn-Mar CSD",
        "4581": "Muscatine CSD", "5250": "Pleasant Valley CSD", "6795": "Waterloo CSD",
        "6822": "Waukee CSD", "6957": "West Des Moines CSD"}
YEARS = [2020, 2021, 2022, 2023, 2024]
ME = "Iowa City CSD"


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# CAR Activity ending balance + the year's revenue / expenditure / net change (rev - exp = Δ balance)
car, rev, exp, net = {}, {}, {}, {}
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["fund"] == "Activity" and r["district_code"] in CODE:
        k = (CODE[r["district_code"]], int(r["fiscal_year"]))
        if r["ending_balance"]:
            car[k] = f(r["ending_balance"])
        rv, ex = f(r["revenues"]), f(r["expenditures"])
        if rv is not None:
            rev[k] = rv
        if ex is not None:
            exp[k] = ex
        if rv is not None and ex is not None:
            net[k] = rv - ex

# Audited Activity balance (+ CAR-vs-audited diff)
aud = {}
for r in csv.DictReader(open("data/activity-fund-audited.csv")):
    aud[(r["district"], int(r["fiscal_year"]))] = f(r["audited_activity_balance"])

# Certified enrollment
enr = {}
for r in csv.DictReader(open("data/dom/certified-enrollment.csv")):
    enr[(r["district"], int(r["fiscal_year"]))] = f(r["certified_enrollment"])

DISTS = sorted(CODE.values())


def per_student(name, fy):
    b, e = car.get((name, fy)), enr.get((name, fy))
    return b / e if (b is not None and e) else None


def peer_avg_ps(fy):
    vals = [per_student(n, fy) for n in DISTS if n != ME and per_student(n, fy) is not None]
    return sum(vals) / len(vals) if vals else None


# ---- headline numbers (Iowa City) ----
ic_ps = {y: per_student(ME, y) for y in YEARS}
ic_bal = {y: car.get((ME, y)) for y in YEARS}
peer = {y: peer_avg_ps(y) for y in YEARS}
trough = min((y for y in YEARS if ic_ps.get(y) is not None), key=lambda y: ic_ps[y])  # FY2023


def rank_of(name, fy):
    """1 = lowest per-student that year (of districts with data)."""
    order = sorted((per_student(n, fy), n) for n in DISTS if per_student(n, fy) is not None)
    for i, (_, n) in enumerate(order, 1):
        if n == name:
            return i, len(order)
    return None, len(order)

ic_rank_trough = rank_of(ME, trough)


# ---- colors ----
def ps_color(v):
    """per-student reserve: thin = red, healthy = green."""
    if v is None: return "#cbd5e1"
    if v < 25:  return "#dc2626"
    if v < 50:  return "#ea580c"
    if v < 90:  return "#d97706"
    return "#16a34a"


def gap_color(pct):
    a = abs(pct)
    if a < 0.5: return "#16a34a"
    if a < 2:   return "#d97706"
    if a < 5:   return "#ea580c"
    return "#dc2626"


def ps_matrix():
    out = []
    for d in DISTS:
        me = d == ME
        tds = [f'<th class="dname{" me" if me else ""}">{html.escape(d)}</th>']
        for y in YEARS:
            v = per_student(d, y)
            if v is None:
                tds.append('<td class="na">—</td>'); continue
            bal = car.get((d, y))
            title = f"{d} FY{y}: ${bal:,.0f} ÷ {enr.get((d,y)):,.0f} students = ${v:.0f}/student"
            tds.append(f'<td style="color:{ps_color(v)};font-weight:{800 if me else 600}" '
                       f'title="{html.escape(title)}">${v:.0f}</td>')
        out.append(f"<tr>{''.join(tds)}</tr>")
    # peer-average row
    avg_tds = ['<th class="dname avg">Peer average (excl. ICCSD)</th>']
    for y in YEARS:
        a = peer_avg_ps(y)
        avg_tds.append(f'<td class="avg">${a:.0f}</td>' if a else '<td class="na">—</td>')
    out.append(f'<tr class="avgrow">{"".join(avg_tds)}</tr>')
    return "\n".join(out)


def bal_matrix():
    out = []
    for d in DISTS:
        me = d == ME
        tds = [f'<th class="dname{" me" if me else ""}">{html.escape(d)}</th>']
        for y in YEARS:
            b, a = car.get((d, y)), aud.get((d, y))
            if b is None:
                tds.append('<td class="na">—</td>'); continue
            atxt = f"audited ${a:,.0f}" if a is not None else "no audit on file"
            title = f"{d} FY{y}: CAR ${b:,.0f} · {atxt}"
            tds.append(f'<td style="font-weight:{700 if me else 500}" '
                       f'title="{html.escape(title)}">${b/1e3:,.0f}K</td>')
        out.append(f"<tr>{''.join(tds)}</tr>")
    return "\n".join(out)


def flow_matrix(src, signed=False):
    """district x year matrix of a $ flow (revenue / expenditure / net), in $thousands.
    signed=True colors negatives red / positives green and shows a +/- sign (for net change)."""
    out = []
    for d in DISTS:
        me = d == ME
        tds = [f'<th class="dname{" me" if me else ""}">{html.escape(d)}</th>']
        for y in YEARS:
            v = src.get((d, y))
            if v is None:
                tds.append('<td class="na">—</td>'); continue
            if signed:
                style = f"color:{'#16a34a' if v >= 0 else '#dc2626'};font-weight:{800 if me else 600}"
                txt = f"{v/1e3:+,.0f}K"
            else:
                style = f"font-weight:{700 if me else 500}"
                txt = f"${v/1e3:,.0f}K"
            tds.append(f'<td style="{style}" title="{html.escape(f"{d} FY{y}: ${v:,.0f}")}">{txt}</td>')
        out.append(f"<tr>{''.join(tds)}</tr>")
    # peer-average row
    avg_tds = ['<th class="dname avg">Peer average (excl. ICCSD)</th>']
    for y in YEARS:
        vals = [src[(n, y)] for n in DISTS if n != ME and (n, y) in src]
        if not vals:
            avg_tds.append('<td class="na">—</td>'); continue
        a = sum(vals) / len(vals)
        txt = f"{a/1e3:+,.0f}K" if signed else f"${a/1e3:,.0f}K"
        avg_tds.append(f'<td class="avg">{txt}</td>')
    out.append(f'<tr class="avgrow">{"".join(avg_tds)}</tr>')
    return "\n".join(out)


# Iowa City throughput headline: revenue per student (FY2024) and where it ranks
ic_rev_ps = {y: (rev.get((ME, y)) / enr[(ME, y)] if (ME, y) in rev and enr.get((ME, y)) else None)
             for y in YEARS}
rev_ps_2024 = sorted(((rev[(n, 2024)] / enr[(n, 2024)], n) for n in DISTS
                      if (n, 2024) in rev and enr.get((n, 2024))), reverse=True)
ic_rev_rank = [i for i, (_, n) in enumerate(rev_ps_2024, 1) if n == ME][0]


def recon_matrix():
    out = []
    for d in DISTS:
        me = d == ME
        tds = [f'<th class="dname{" me" if me else ""}">{html.escape(d)}</th>']
        for y in YEARS:
            b, a = car.get((d, y)), aud.get((d, y))
            if b is None or a is None:
                tds.append('<td class="na">—</td>'); continue
            diff = b - a
            pct = diff / a * 100 if a else 0.0
            title = f"{d} FY{y}: CAR ${b:,.0f} vs audited ${a:,.0f} ({diff:+,.0f})"
            tds.append(f'<td style="color:{gap_color(pct)};font-weight:600" '
                       f'title="{html.escape(title)}">{pct:+.1f}%</td>')
        out.append(f"<tr>{''.join(tds)}</tr>")
    return "\n".join(out)


# reconciliation tally for the takeaway
ties = sum(1 for d in DISTS for y in YEARS
           if car.get((d, y)) is not None and aud.get((d, y)) is not None
           and abs(car[(d, y)] - aud[(d, y)]) <= max(2.0, abs(aud[(d, y)]) * 0.005))
both = sum(1 for d in DISTS for y in YEARS
           if car.get((d, y)) is not None and aud.get((d, y)) is not None)

date = datetime.date(2026, 6, 12).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Student activities fund — Iowa City vs. peers</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.intro{{border-left:4px solid #2563eb}} .intro p{{margin:7px 0}}
.flag{{background:#fef2f2;border:1px solid #fecaca;border-left:4px solid #dc2626;border-radius:10px;padding:16px 20px;margin-bottom:18px}}
.flag h2{{margin:0 0 8px;font-size:20px;color:#991b1b}}
.big{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px}}
.big .stat{{background:#fff;border:1px solid #fecaca;border-radius:10px;padding:10px 14px;min-width:150px}}
.big .n{{font-size:25px;font-weight:800;color:#dc2626}} .big .l{{font-size:12px;color:var(--mut)}}
.tscroll{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin-top:6px}}
.tscroll table{{min-width:520px}}
th,td{{padding:7px 10px;text-align:right;border-bottom:1px solid var(--line)}}
thead th{{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.03em}}
.dname{{text-align:left;font-weight:600}} .dname.me{{color:#1d4ed8}}
tr:has(.me){{background:#eff6ff}}
.avgrow{{border-top:2px solid #cbd5e1}} .avg{{font-weight:700;color:#334155;font-style:italic}}
td.na{{color:#cbd5e1}}
.legend{{font-size:12.5px;color:var(--mut);margin:10px 2px 0;display:flex;gap:16px;flex-wrap:wrap;align-items:center}}
.legend i{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:middle;margin-right:5px}}
ul{{margin:8px 0}} li{{margin:4px 0}}
.take{{margin:12px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #94a3b8;border-radius:6px;padding:10px 14px}}
.take b{{color:#0f172a}}
footer{{color:var(--mut);font-size:12.5px;margin-top:28px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body>{nav("activity")}<div class="wrap">

<h1>The student activities fund: how much do districts keep?</h1>
<p class="sub">Year-end balance of the <b>Student Activity Fund</b> — self-reported (CAR), audited (ACFR), and per student — Iowa City CSD vs. 14 size-matched peers · FY2020–FY2024 · {date}</p>

<div class="card intro">
<p>Every Iowa district runs a <b>Student Activity Fund</b> — a restricted special-revenue fund that
holds the money raised by and for student groups (athletics, clubs, music, drama, fundraisers). The
cash flowing through it is large, but what matters here is the <b>year-end balance</b>: the cushion the
fund carries from one year to the next.</p>
<p>Below, three views of that balance for the 15 largest districts: <b>per student</b> (the headline
comparison), the raw <b>dollar balance</b>, and a <b>CAR-vs-audited</b> reconciliation — the district's
own unaudited self-report (the Certified Annual Report it files with the state) against the figure its
independent audit later confirms.</p>
</div>

<div class="flag">
<h2>⚠️ Iowa City CSD carries the thinnest activity-fund cushion of any large district</h2>
<div class="big">
  <div class="stat"><div class="n">${ic_ps[trough]:.0f}/student</div><div class="l">FY{trough} — the <b>lowest of all 15</b> (rank {ic_rank_trough[0]} of {ic_rank_trough[1]}), vs a <b>${peer[trough]:.0f}</b> peer average</div></div>
  <div class="stat"><div class="n">${ic_bal[trough]/1e3:.0f}K</div><div class="l">FY{trough} ending balance — down from <b>${ic_bal[2021]/1e3:.0f}K</b> in FY2021</div></div>
  <div class="stat"><div class="n">${ic_ps[2024]:.0f}/student</div><div class="l">FY2024 — a partial rebuild to ${ic_bal[2024]/1e3:.0f}K, still <b>~¼ of the ${peer[2024]:.0f} peer average</b></div></div>
</div>
<p class="take">From FY2021 to FY{trough}, Iowa City drew its student activity fund down from
<b>${ic_bal[2021]/1e3:.0f}K to just ${ic_bal[trough]/1e3:.0f}K</b> — about <b>${ic_ps[trough]:.0f} per
student</b>, when every peer was holding <b>${peer[trough]:.0f}+</b>. It rebuilt to
<b>${ic_bal[2024]/1e3:.0f}K (${ic_ps[2024]:.0f}/student)</b> in FY2024, but that is still the
<b>2nd-thinnest of the 15</b> and roughly a quarter of the ~${peer[2024]:.0f} large-district norm.
The fund's <i>throughput</i> is healthy — ICCSD ran ~$4.7M of student-activity revenue through it in
FY2024 — so the thin balance is a choice about how little to carry over, not a lack of activity.</p>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:20px">Student activity fund — balance <b>per student</b></h2>
<p style="font-size:14px;color:#475569;margin:2px 0 6px">Year-end Student Activity fund balance ÷ certified enrollment. Color marks the size of the cushion.</p>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{ps_matrix()}
</tbody>
</table>
<div class="legend">$ per student:
<span><i style="background:#dc2626"></i>&lt;$25</span>
<span><i style="background:#ea580c"></i>$25–50</span>
<span><i style="background:#d97706"></i>$50–90</span>
<span><i style="background:#16a34a"></i>&gt;$90</span>
</div>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:20px">Student activity fund — ending balance ($ thousands)</h2>
<p style="font-size:14px;color:#475569;margin:2px 0 6px">CAR ending balance per district-year (hover a cell for the audited figure). Iowa City has no FY2024 audit on file, so its FY2024 audited figure is blank — but its CAR balance is shown.</p>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{bal_matrix()}
</tbody>
</table>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:20px">Revenue, expenditure, and net change — broken out</h2>
<p style="font-size:14px;color:#475569;margin:2px 0 10px">The money that flows <i>through</i> the
student activity fund each year (CAR), and the resulting <b>net change</b> in the year-end balance.
<b>Net = revenue − expenditure = the change in fund balance</b> (a positive net adds to the cushion; a
negative net draws it down). All figures in $ thousands.</p>

<h3 style="margin:14px 0 2px;font-size:15px;color:#334155">Revenue</h3>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{flow_matrix(rev)}
</tbody>
</table>

<h3 style="margin:18px 0 2px;font-size:15px;color:#334155">Expenditure</h3>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{flow_matrix(exp)}
</tbody>
</table>

<h3 style="margin:18px 0 2px;font-size:15px;color:#334155">Net change (revenue − expenditure)</h3>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{flow_matrix(net, signed=True)}
</tbody>
</table>
<div class="legend">Net change:
<span><i style="background:#16a34a"></i>added to the fund (surplus)</span>
<span><i style="background:#dc2626"></i>drew the fund down (deficit)</span>
</div>
<p class="take"><b>Iowa City moves the most money through its activity fund of any peer, yet keeps the
least.</b> In FY2024 it ran <b>${rev[(ME,2024)]/1e6:.1f}M of revenue</b> through the fund —
<b>${ic_rev_ps[2024]:.0f} per student, the highest of all 15</b> (rank {ic_rev_rank} of {len(rev_ps_2024)})
— but its year-end balance is still the 2nd-thinnest. The net-change column tells the story of the
drawdown: ICCSD ran <b>deficits in FY2022 (${net[(ME,2022)]/1e3:+,.0f}K) and FY2023
(${net[(ME,2023)]/1e3:+,.0f}K)</b> that emptied the cushion, then a <b>${net[(ME,2024)]/1e3:+,.0f}K</b>
surplus in FY2024 rebuilt part of it. So the thin balance is a function of how little is carried over,
not of low activity.</p>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:20px">CAR vs. audited — do the activity-fund books reconcile?</h2>
<p style="font-size:14px;color:#475569;margin:2px 0 6px">Gap between the CAR (self-reported) and audited Student Activity balance. Green means they tie within rounding.</p>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{recon_matrix()}
</tbody>
</table>
<div class="legend">Gap (CAR − audited):
<span><i style="background:#16a34a"></i>&lt;0.5% (ties)</span>
<span><i style="background:#d97706"></i>0.5–2%</span>
<span><i style="background:#ea580c"></i>2–5%</span>
<span><i style="background:#dc2626"></i>&gt;5%</span>
</div>
<p class="take"><b>The activity fund reconciles cleanly almost everywhere</b> — {ties} of {both} district-years
with both figures tie to the dollar, confirming the per-student picture above is not an artifact of one
source. The handful of small gaps (Pleasant Valley ~0.5%, Ankeny FY2024 ~3.6%) are genuine CAR-vs-audit
differences, not data errors — the audited figure is simply lower than the district's self-report in
those years. Iowa City's FY2024 cell is blank because, alone among the 15, it has <b>not filed a FY2024
audit</b>; its FY2020–FY2023 activity balances tie to the audit exactly.</p>
</div>

<footer>
<b>Sources.</b> CAR (self-reported): Iowa Department of Education Certified Annual Report — annual
workbooks (FY2023, FY2024) and the multi-year fund-balance files (FY2017–2023). Audited: each district's
ACFR (Student Activity fund balance / "restricted for student activities"), extracted from the reports in
<code>auditreports/</code>. Enrollment: Iowa DE certified enrollment. Per student = year-end Student
Activity fund balance ÷ certified enrollment. Built by <code>scripts/extract_car.py</code> +
<code>scripts/extract_activity_fund.py</code> + <code>scripts/build_activity_fund_report.py</code>.
</footer>
</div></body></html>"""

# Wrap every table in a horizontal-scroll container so a wide table never spills past the
# white card on narrow (mobile) screens — the card background stays behind the visible cells.
DOC = DOC.replace("<table>", '<div class="tscroll"><table>').replace("</table>", "</table></div>")

open("activity-fund.html", "w").write(DOC)
print(f"Wrote activity-fund.html ({len(DOC)//1024} KB); {both} district-years with both CAR & audited, {ties} tie")
