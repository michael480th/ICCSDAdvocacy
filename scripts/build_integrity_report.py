#!/usr/bin/env python3
"""
Build a self-contained report on the CAR-vs-audited reporting-integrity screen.

Reads data/integrity-checks.csv (one row per district-year-check, produced by
scripts/build_integrity_checks.py) and renders integrity-checks.html — a colored
district x year matrix per check, a district scorecard ranked by flag rate, and an
Iowa City headline. Self-contained: inline CSS, no external dependencies.

Run:  python3 scripts/build_integrity_report.py   ->  integrity-checks.html
"""
import csv, html, datetime, sys, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

rows = list(csv.DictReader(open("data/integrity-checks.csv")))
YEARS = sorted({int(r["fiscal_year"]) for r in rows})
DISTS = sorted({r["district"] for r in rows})
# index: (district, year, check) -> row
idx = {(r["district"], int(r["fiscal_year"]), r["check"]): r for r in rows}


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---- scorecard: flags / checks per district, EXCLUDING timeliness ----
flags = defaultdict(int)
checks = defaultdict(int)
for r in rows:
    if r["check"] == "C22_timeliness":
        continue
    checks[r["district"]] += 1
    if r["flag"] == "Y":
        flags[r["district"]] += 1
scorecard = sorted(DISTS, key=lambda d: (-flags[d] / max(checks[d], 1), -flags[d], d))
total_flags = sum(flags.values())
total_checks = sum(checks.values())


def color(pct):
    """Color scale on absolute percent gap (same buckets as build_car_report.py)."""
    if pct is None:
        return "#94a3b8"
    a = abs(pct)
    if a < 0.5: return "#16a34a"   # ties
    if a < 2:   return "#d97706"   # minor
    if a < 5:   return "#ea580c"   # material
    return "#dc2626"               # large


def rate_color(rate):
    if rate <= 0:    return "#16a34a"
    if rate < 0.08:  return "#d97706"
    if rate < 0.18:  return "#ea580c"
    return "#dc2626"


# ---- Iowa City headline figures ----
ic_end = idx.get(("Iowa City CSD", 2023, "C1_ending"))
ic_avail = idx.get(("Iowa City CSD", 2023, "C2_available"))
ic_net = idx.get(("Iowa City CSD", 2023, "C8_net_change"))
ic_cash = idx.get(("Iowa City CSD", 2023, "C14_cash"))
ic_lag = idx.get(("Iowa City CSD", 2023, "C22_timeliness"))


# ---- AUDIT CURRENCY: the latest audited year each district actually has, and its lag ----
import datetime as _dt
CURRENT_FY = 2025  # the most recent fiscal year peers have audited (FY ended June 30, 2025)
audit_curr = {}    # district -> dict(fy, report, lag_months)
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    if r["district"] in DISTS and r["gf_total_fund_balance"] and r["report_date"]:
        fy = int(r["fiscal_year"])
        if r["district"] not in audit_curr or fy > audit_curr[r["district"]]["fy"]:
            rd = r["report_date"].strip()
            lag = None
            for fmt in ("%Y-%m-%d", "%B %d, %Y", "%m/%d/%Y"):
                try:
                    lag = (_dt.datetime.strptime(rd, fmt).date() - _dt.date(fy, 6, 30)).days / 30.44
                    break
                except ValueError:
                    pass
            audit_curr[r["district"]] = dict(fy=fy, report=rd, lag=lag)


def currency_rows():
    out = []
    for d in sorted(DISTS, key=lambda d: (audit_curr.get(d, {}).get("fy", 0), -(audit_curr.get(d, {}).get("lag") or 0))):
        a = audit_curr.get(d)
        if not a:
            continue
        me = d == "Iowa City CSD"
        behind = CURRENT_FY - a["fy"]
        lag = a["lag"]
        late = lag is not None and lag > 15
        c = "#dc2626" if (behind >= 1 or late) else "#16a34a"
        badge = (f'<span style="color:#dc2626;font-weight:800">{behind} yr behind</span>' if behind >= 1
                 else '<span style="color:#16a34a;font-weight:700">current</span>')
        lagtxt = (f'{lag:.0f} mo' if lag is not None else '—')
        out.append(f'<tr><th class="dname{" me" if me else ""}">{html.escape(d)}</th>'
                   f'<td style="color:{c};font-weight:{"800" if behind>=1 else "600"}">FY{a["fy"]}</td>'
                   f'<td style="color:{"#dc2626" if late else "#334155"};font-weight:{"800" if late else "600"}">{lagtxt}</td>'
                   f'<td>{badge}</td></tr>')
    return "\n".join(out)


# ---- ALL CHECKS at a glance: one row per check, with Iowa City's FY2023 result ----
GROUPS = [
    ("Bottom-line reconciliation (these should tie regardless of presentation)", [
        ("C1_ending", "Ending fund balance"), ("C2_available", "Available (spendable) reserves"),
        ("C3_unassigned", "Unassigned balance"), ("C8_net_change", "Net change in fund balance"),
        ("C10_revenue", "Revenue"), ("C14_cash", "Operating cash"), ("C15_days_cash", "Days cash on hand"),
        ("C17_solvency", "Solvency ratio"), ("C6_rollforward", "CAR internal roll-forward"),
        ("C7_begin_vs_audit", "Beginning vs prior audited end")]),
    ("Classification-sensitive (shown for context, not flagged)", [
        ("C11_expenditure", "Expenditure"), ("C12_transfers", "Transfers / other financing"),
        ("C13_margin", "Operating margin"), ("C18_fb_pct_exp", "Fund balance % of expenditure")]),
    ("Audit quality (meta)", [
        ("C9_restatement", "Beginning-balance restatement"), ("C22_timeliness", "Audit timeliness")]),
]


def ic_cell(check):
    """Iowa City's most-recent comparable result for a check (FY2023, the last audited year)."""
    r = idx.get(("Iowa City CSD", 2023, check))
    if not r:
        return '<span style="color:#cbd5e1">no data</span>'
    flag = r["flag"] == "Y"
    style = 'color:#dc2626;font-weight:800' if flag else 'color:#334155'
    if check == "C22_timeliness":
        return f'<span style="{style}">{f(r["audited"]):.0f} mo late</span>'
    if check == "C9_restatement":
        return f'<span style="{style}">{"restated" if r["audited"]=="Y" else "no"}</span>'
    gp = f(r["gap_pct"])
    if check in ("C8_net_change", "C14_cash", "C1_ending", "C2_available", "C3_unassigned", "C10_revenue", "C12_transfers"):
        g = f(r["gap"]); dollar = (f'{("+" if g>=0 else "-")}${abs(g)/1e6:.1f}M' if abs(g) >= 1e6 else f'{("+" if g>=0 else "-")}${abs(g)/1e3:.0f}K')
        # show the % only when it's meaningful (not transfers, whose base is near zero)
        extra = f' ({gp:+.0f}%)' if (gp is not None and abs(gp) < 500 and check != "C12_transfers") else ''
        return f'<span style="{style}">{dollar}{extra}</span>'
    if gp is not None:
        return f'<span style="{style}">{gp:+.1f}%</span>'
    cv, av = f(r["car"]), f(r["audited"])   # point checks (days cash, solvency, margin, fb%exp)
    if cv is not None and av is not None:
        return f'<span style="{style}">{cv-av:+.1f} pts</span>'
    return '<span style="color:#cbd5e1">&mdash;</span>'


def allchecks_rows():
    out = []
    for gtitle, items in GROUPS:
        out.append(f'<tr><td colspan="4" style="background:#f8fafc;font-weight:700;color:#475569;'
                   f'font-size:12.5px;padding:8px 10px">{gtitle}</td></tr>')
        for cid, label in items:
            cr = [r for r in rows if r["check"] == cid]
            nflag = sum(1 for r in cr if r["flag"] == "Y")
            nrun = len(cr)
            fcol = "#dc2626" if nflag else "#16a34a"
            out.append(f'<tr><th class="dname">{label}</th>'
                       f'<td style="text-align:left;color:#64748b;font-size:12.5px">{html.escape(cr[0]["name"]) if cr else ""}</td>'
                       f'<td style="color:{fcol};font-weight:{"800" if nflag else "600"}">{nflag} / {nrun}</td>'
                       f'<td style="text-align:right">{ic_cell(cid)}</td></tr>')
    return "\n".join(out)



def scorecard_rows():
    out = []
    for d in scorecard:
        me = d == "Iowa City CSD"
        c, fl = checks[d], flags[d]
        rate = fl / max(c, 1)
        col = rate_color(rate)
        tds = [
            f'<th class="dname{" me" if me else ""}">{html.escape(d)}</th>',
            f'<td>{c}</td>',
            f'<td style="color:{col};font-weight:{"800" if fl else "600"}">{fl}</td>',
            f'<td style="color:{col};font-weight:800">{rate*100:.0f}%</td>',
        ]
        out.append(f"<tr>{''.join(tds)}</tr>")
    return "\n".join(out)


def matrix(check, kind="$"):
    """Render a district x year colored matrix for one check.

    kind="$"   -> show signed percent gap (CAR vs audited)
    kind="pts" -> show signed point gap (ratios/days), color on its magnitude
    kind="lag" -> show the audit lag in months (timeliness; audited only)
    """
    out = []
    for d in DISTS:
        me = d == "Iowa City CSD"
        tds = [f'<th class="dname{" me" if me else ""}">{html.escape(d)}</th>']
        for y in YEARS:
            r = idx.get((d, y, check))
            if not r:
                tds.append('<td class="na">&mdash;</td>')
                continue
            flag = r["flag"] == "Y"
            ring = "box-shadow:inset 0 0 0 2px #dc2626;border-radius:6px" if flag else ""
            if kind == "lag":
                months = f(r["audited"])
                if months is None:
                    tds.append('<td class="na">&mdash;</td>')
                    continue
                c = "#dc2626" if months > 15 else ("#ea580c" if months > 12 else "#16a34a")
                title = f"{d} FY{y}: audit filed {months:.1f} months after fiscal year-end"
                tds.append(f'<td style="color:{c};font-weight:{"800" if flag else "600"};{ring}" '
                           f'title="{html.escape(title)}">{months:.0f}mo</td>')
                continue
            cv, av = f(r["car"]), f(r["audited"])
            if cv is None or av is None:
                tds.append('<td class="na">&mdash;</td>')
                continue
            if kind == "dollar":
                gap = cv - av
                gp = f(r["gap_pct"])
                c = color(gp)
                a = abs(gap); sgn = "+" if gap >= 0 else "-"
                lbl = f"{sgn}${a/1e6:.1f}M" if a >= 1e6 else (f"{sgn}${a/1e3:.0f}K" if a >= 1e3 else f"{gap:+.0f}")
                title = f"{d} FY{y}: CAR net {cv:+,.0f} vs audited net {av:+,.0f} (gap {gap:+,.0f}; {gp:+.1f}% of fund balance)"
                tds.append(f'<td style="color:{c};font-weight:{"800" if flag else "600"};{ring}" '
                           f'title="{html.escape(title)}">{lbl}</td>')
                continue
            if kind == "pts":
                gap = cv - av
                c = "#16a34a" if abs(gap) < 1 else ("#d97706" if abs(gap) < 3 else "#dc2626")
                title = f"{d} FY{y}: CAR {cv:,.1f} vs audited {av:,.1f} ({gap:+.1f} pts)"
                tds.append(f'<td style="color:{c};font-weight:{"800" if flag else "600"};{ring}" '
                           f'title="{html.escape(title)}">{gap:+.1f}</td>')
                continue
            gp = f(r["gap_pct"])
            c = color(gp)
            title = f"{d} FY{y}: CAR {cv:,.0f} vs audited {av:,.0f} ({cv-av:+,.0f})"
            label = f"{gp:+.1f}%" if gp is not None else f"{cv-av:+,.0f}"
            tds.append(f'<td style="color:{c};font-weight:{"800" if flag else "600"};{ring}" '
                       f'title="{html.escape(title)}">{label}</td>')
        out.append(f"<tr>{''.join(tds)}</tr>")
    return "\n".join(out)


def matrix_card(title, blurb, check, kind="$", legend="gap"):
    leg = {
        "gap": ('<div class="legend">Gap (CAR &minus; audited):'
                '<span><i style="background:#16a34a"></i>&lt;0.5% (ties)</span>'
                '<span><i style="background:#d97706"></i>0.5&ndash;2%</span>'
                '<span><i style="background:#ea580c"></i>2&ndash;5%</span>'
                '<span><i style="background:#dc2626"></i>&gt;5%</span>'
                '<span><i style="background:#fff;box-shadow:inset 0 0 0 2px #dc2626"></i>flagged</span></div>'),
        "pts": ('<div class="legend">Gap (CAR &minus; audited), percentage points:'
                '<span><i style="background:#16a34a"></i>&lt;1 pt</span>'
                '<span><i style="background:#d97706"></i>1&ndash;3 pts</span>'
                '<span><i style="background:#dc2626"></i>&ge;3 pts (flagged)</span></div>'),
        "lag": ('<div class="legend">Months from fiscal year-end to audit filing:'
                '<span><i style="background:#16a34a"></i>&le;12 mo</span>'
                '<span><i style="background:#ea580c"></i>12&ndash;15 mo</span>'
                '<span><i style="background:#dc2626"></i>&gt;15 mo (flagged)</span></div>'),
    }[legend]
    return f"""<div class="card">
<h2 style="margin:0 0 4px;font-size:19px">{title}</h2>
<p style="font-size:14px;color:#475569;margin:2px 0 6px">{blurb}</p>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{matrix(check, kind)}
</tbody>
</table>
{leg}
</div>"""


date = datetime.date(2026, 6, 11).strftime("%B %Y")

DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporting-integrity screen — how reliably do district CARs reconcile to their audits?</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04);overflow-x:auto}}
.intro{{border-left:4px solid #2563eb}} .intro p{{margin:7px 0}}
.flag{{background:#fef2f2;border:1px solid #fecaca;border-left:4px solid #dc2626;border-radius:10px;padding:16px 20px;margin-bottom:18px}}
.flag h2{{margin:0 0 8px;font-size:20px;color:#991b1b}}
.big{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px}}
.big .stat{{background:#fff;border:1px solid #fecaca;border-radius:10px;padding:10px 14px;min-width:150px;flex:1}}
.big .n{{font-size:25px;font-weight:800;color:#dc2626}} .big .l{{font-size:12px;color:var(--mut)}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin-top:6px}}
th,td{{padding:7px 10px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}}
thead th{{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.03em}}
.dname{{text-align:left;font-weight:600}} .dname.me{{color:#1d4ed8}}
tr:has(.me){{background:#eff6ff}}
td.na{{color:#cbd5e1}}
.legend{{font-size:12.5px;color:var(--mut);margin:10px 2px 0;display:flex;gap:16px;flex-wrap:wrap;align-items:center}}
.legend i{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:middle;margin-right:5px}}
ul{{margin:8px 0}} li{{margin:4px 0}}
.take{{margin:12px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #94a3b8;border-radius:6px;padding:10px 14px}}
.take b{{color:#0f172a}}
footer{{color:var(--mut);font-size:12.5px;margin-top:28px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body>{nav("integrity")}<div class="wrap">

<h1>Reporting-integrity screen: do the CARs reconcile to the audits?</h1>
<p class="sub">A reconciliation screen comparing each district's <b>Certified Annual Report</b> (its unaudited self-report) against its <b>independently audited</b> General Fund results, FY2017&ndash;FY2023 &middot; {date}</p>

<div class="card intro">
<p>Every Iowa district files a <b>Certified Annual Report (CAR)</b> with the state by September 15 &mdash;
its own <b>unaudited</b> account of the year. Months or years later, an independent <b>audit</b> reports the
same year. <b>The two should match.</b> This screen runs the reconciliation checks a rating analyst would
use &mdash; ending balance, available reserves, net change, revenue, expenditure, operating cash, beginning
balance versus the prior year's audit, and audit timeliness &mdash; and scores how reliably each district's
self-reported numbers tie out to what the auditors ultimately found.</p>
<p>Two things make a district's self-reporting trustworthy: an audit has to <b>exist</b> for the year (so the
numbers can be checked at all), and when it does, the CAR has to <b>match</b> it. Across {len(DISTS)} districts
and {len(YEARS)} years, <b>{total_flags} of {total_checks}</b> reconciliation checks are flagged &mdash; but the
first test is the one that most cleanly separates the pack, and it is where Iowa City stands alone.</p>
</div>

<div class="card" style="border-left:4px solid #dc2626">
<h2 style="margin:0 0 4px;font-size:20px">First question: can the numbers even be checked yet?</h2>
<p style="font-size:14.5px;color:#334155;margin:2px 0 10px">The most basic integrity test isn't whether the CAR
matches the audit &mdash; it's whether an <b>audit exists yet at all</b>. As of {date}, every peer district has a
completed audit through <b>FY2025</b>. <b>Iowa City's most recent audit is FY2023</b> &mdash; the only district
two years behind &mdash; and that one arrived <b>26 months late</b> with a declared material weakness. Its FY2024
and FY2025 self-reported numbers <b>cannot be verified by anyone.</b></p>
<table>
<thead><tr><th class="dname">District</th><th>Audited through</th><th>Filing lag</th><th>Status</th></tr></thead>
<tbody>
{currency_rows()}
</tbody>
</table>
<div class="legend">Filing lag = months from the June&nbsp;30 fiscal year-end to the audit's report date.
<span style="color:#dc2626;font-weight:700">Red</span> = behind the FY2025 cycle, or filed more than 15 months late.</div>
</div>

<div class="flag">
<h2>&#9888;&#65039; Iowa City CSD, FY2023 &mdash; the standout</h2>
<div class="big">
  <div class="stat"><div class="n">+{f(ic_net['gap']):,.0f}</div><div class="l">net change: CAR reported +${f(ic_net['car'])/1e6:.2f}M added to the General Fund; the audit found just +${f(ic_net['audited'])/1e3:,.0f}K</div></div>
  <div class="stat"><div class="n">+{f(ic_avail['gap_pct']):.0f}%</div><div class="l">CAR <b>available</b> (spendable) reserves vs audited (+${f(ic_avail['gap'])/1e6:.2f}M) &mdash; the liquid cushion</div></div>
  <div class="stat"><div class="n">{f(ic_lag['audited']):.0f} mo</div><div class="l">audit filed {f(ic_lag['audited']):.0f} months after fiscal year-end &mdash; more than two years late</div></div>
</div>
<p class="take">Iowa City's CAR said the district <b>added ${f(ic_net['car'])/1e6:.2f}M</b> to its General Fund in
FY2023; the audit found the true gain was just <b>${f(ic_net['audited'])/1e3:,.0f}K</b> &mdash; an overstatement
of <b>~${f(ic_net['gap'])/1e3:,.0f}K</b>. The CAR's ending balance came in <b>${f(ic_end['gap'])/1e3:,.0f}K
({f(ic_end['gap_pct']):+.1f}%) too high</b>, and its <b>available</b> (spendable) reserves &mdash; the liquid
cushion and the solvency-ratio numerator &mdash; were <b>{f(ic_avail['gap_pct']):+.0f}% too high</b>
(${f(ic_avail['car']):,.0f} reported vs ${f(ic_avail['audited']):,.0f} audited). The one figure the CAR
<i>under</i>stated was operating cash, off <b>{f(ic_cash['gap_pct']):+.1f}%</b>. This is the year the audit was
filed <b>{f(ic_lag['audited']):.0f} months late</b> and the auditor declared a material weakness &mdash;
"financial statements required significant revisions."</p>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:19px">District scorecard &mdash; reconciliation flag rate</h2>
<p style="font-size:14px;color:#475569;margin:2px 0 6px">Share of each district's dollar/ratio checks that fail to reconcile, ranked worst first.
<b>Audit timeliness is excluded here</b> (it is a meta check, not a CAR-vs-audited number). A clean district shows 0%.</p>
<p style="font-size:13.5px;color:#64748b;margin:2px 0 6px;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:8px 12px">
<b>Read this with the audit-currency table above.</b> A low rate can mean genuinely clean books (Pleasant Valley, Linn-Mar) &mdash;
or, as with <b>Iowa City</b>, that the CAR reconciled fine for years (zero flags FY2017&ndash;2022) and then <b>broke
catastrophically in one recent year (FY2023)</b> before going dark. Flag <i>rate</i> averages that single failure across the
clean years, so Davenport's <i>chronic</i> ~2% drift ranks higher than Iowa City's <i>acute</i> breakdown. Reconciliation
alone does not capture Iowa City's real problem &mdash; that there is no recent audit to reconcile against.</p>
<table>
<thead><tr><th class="dname">District</th><th>Checks run</th><th>Flagged</th><th>Flag rate</th></tr></thead>
<tbody>
{scorecard_rows()}
</tbody>
</table>
<p class="take"><b>Most districts reconcile cleanly</b> &mdash; six show a 0% flag rate. <b>Davenport</b> has the
<b>highest flag rate ({flags['Davenport CSD']/checks['Davenport CSD']*100:.0f}%)</b>, a chronic, broad-based
pattern of small gaps year after year. <b>Iowa City's</b> rate is lower
({flags['Iowa City CSD']/checks['Iowa City CSD']*100:.0f}%) but its flags are <b>concentrated and severe</b>
&mdash; they all land in FY2023, on the headline balances and the net change, in the exact year its audit was
filed {f(ic_lag['audited']):.0f} months late with a material weakness. Davenport's problem is breadth;
Iowa City's is depth.</p>
</div>

{matrix_card("Net change in fund balance &mdash; CAR vs audited",
  "The single most telling check: did the change the CAR reported actually happen? Cells show the <b>dollar gap</b> (CAR minus audited net change); color is its size relative to the fund balance. Iowa City's FY2023 stands out &mdash; the CAR reported a +$1.04M gain, the audit found +$88K (a ~$951K overstatement). (We size this against the fund balance, not against the audited net change, because that base is often near zero.)",
  "C8_net_change", "dollar", "gap")}

{matrix_card("Ending General Fund balance &mdash; CAR vs audited",
  "The bottom line: does the year-end balance the CAR reports match the audited books? A red outline flags a gap over 1% and $250K.",
  "C1_ending", "$", "gap")}

{matrix_card("Available (spendable) reserves &mdash; CAR vs audited",
  "The unassigned + assigned cushion a district can actually use, and the numerator of the solvency ratio. The CAR workbooks only carry this split for FY2023.",
  "C2_available", "$", "gap")}

{matrix_card("Operating cash &mdash; CAR vs audited",
  "General Fund cash and investments &mdash; the literal money on hand. Carried in the CAR workbooks for FY2023.",
  "C14_cash", "$", "gap")}

{matrix_card("Beginning balance vs prior year's audited ending &mdash; CAR vs audited",
  "Does the CAR open the year where the previous year's audit closed it? A clean roll-forward should tie exactly.",
  "C7_begin_vs_audit", "$", "gap")}

{matrix_card("Audit timeliness &mdash; months from year-end to filing",
  "Not a CAR-vs-audited number, but a direct signal of reporting reliability: how long after the June 30 fiscal year-end the independent audit was actually filed. Flagged over 15 months.",
  "C22_timeliness", "lag", "lag")}

<div class="card">
<h2 style="margin:0 0 6px;font-size:19px">Davenport &mdash; the breadth case</h2>
<p style="font-size:14px;color:#475569;margin:2px 0 6px">Where Iowa City's flags are a single severe year, Davenport's are a steady drumbeat &mdash; small CAR-vs-audited
gaps that recur across revenue, expenditure, ending balance and net change, year after year. No single year is
dramatic, but the books rarely tie out, which is its own kind of reporting-quality signal.</p>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:19px">All 16 checks &mdash; at a glance</h2>
<p style="font-size:14px;color:#475569;margin:2px 0 6px">Every check the screen runs, how many district-years it flags,
and Iowa City's most recent comparable result (FY2023, its last audited year). The <b>bottom-line</b> checks must reconcile
regardless of accounting presentation; the <b>classification-sensitive</b> ones differ systematically (the CAR folds
transfers into expenditures) and are shown but not flagged; the <b>meta</b> checks are about audit quality, not the CAR.</p>
<table>
<thead><tr><th class="dname">Check</th><th style="text-align:left">Compares</th><th>Flagged</th><th>Iowa City FY2023</th></tr></thead>
<tbody>
{allchecks_rows()}
</tbody>
</table>
</div>

<footer>
<b>Method.</b> The audited General Fund figures are now machine-extracted from every district's ACFR for
<b>FY2015&ndash;FY2023</b> (column- and region-aware, self-validated against accounting identities, and 100%
matched to the curated FY2020&ndash;FY2023 data). The CAR-vs-audited comparison therefore runs across the full
CAR window, <b>FY2017&ndash;FY2023</b>; audited-only checks (restatement, audit lag) reach back to FY2015.
Dollar checks are flagged when the CAR differs from audited by &ge;1% and &ge;$250,000; ratio/point checks
(solvency, days cash) when they differ by &ge;3 points; audit timeliness when filing runs more than 15 months
past fiscal year-end. <b>Expenditure, transfers, operating margin and fund-balance-%-of-expenditure are shown
for context but NOT flagged</b> &mdash; they differ systematically because the CAR folds "other financing
uses"/transfers into General Fund expenditures while the audit separates them, so the scorecard reflects only
the bottom-line figures that must reconcile regardless of presentation. Still pending: <b>per-fund</b> and
<b>all-funds</b> reconciliation, and the full fund-balance <b>classification mix</b> for years before FY2023
(the CAR carries the unassigned/assigned split only in its FY2023&ndash;FY2024 workbooks).
<b>Sources.</b> CAR: Iowa Department of Education Certified Annual Report workbooks + multi-year files.
Audited: each district's ACFR (<code>scripts/extract_audit_financials.py</code> &rarr;
<code>data/audit-financials.csv</code>). Built by <code>scripts/build_integrity_checks.py</code> +
<code>scripts/build_integrity_report.py</code>.
</footer>
</div></body></html>"""

open("integrity-checks.html", "w").write(DOC)
print(f"Wrote integrity-checks.html ({len(DOC)//1024} KB), {len(DISTS)} districts, "
      f"{total_flags}/{total_checks} flagged (excl. timeliness)")
