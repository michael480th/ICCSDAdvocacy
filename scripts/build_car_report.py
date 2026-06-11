#!/usr/bin/env python3
"""
Build a self-contained report: does each district's CAR (unaudited self-report) match its
audited books? Reads data/car-vs-audited.csv (+ data/car-fund-balances.csv and the audited
financials for the Iowa City detail) and renders car-vs-audited.html — a colored
district x year matrix of the General-Fund ending-balance gap, headlined on Iowa City.

Run:  python3 scripts/build_car_report.py   ->  car-vs-audited.html
"""
import csv, html, datetime, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

rows = list(csv.DictReader(open("data/car-vs-audited.csv")))
YEARS = sorted({int(r["fiscal_year"]) for r in rows})
DISTS = sorted({r["district"] for r in rows})
cell = {(r["district"], int(r["fiscal_year"])): r for r in rows}


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# Iowa City detail for the headline
ic23 = cell[("Iowa City CSD", 2023)]
ic_diff = f(ic23["ending_diff"]); ic_pct = f(ic23["ending_diff_pct"])
ic_car_net = f(ic23["car_net_change"]); ic_aud_net = f(ic23["audited_net_change"])
ic_beg_tie = f(ic23["beginning_vs_prior_audited"])
# unassigned (CAR vs audited)
carfb = {(r["district_code"], r["fiscal_year"]): r for r in csv.DictReader(open("data/car-fund-balances.csv"))
         if r["fund"] == "General"}
ic_car_un = f(carfb[("3141", "2023")]["gf_unassigned"])
ic_aud_un = None
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    if r["district"] == "Iowa City CSD" and r["fiscal_year"] == "2023":
        ic_aud_un = f(r["gf_unassigned"])
un_diff = ic_car_un - ic_aud_un
un_pct = un_diff / ic_aud_un * 100


def color(pct):
    a = abs(pct)
    if a < 0.5: return "#16a34a"      # ties
    if a < 2:   return "#d97706"      # minor
    if a < 5:   return "#ea580c"      # material
    return "#dc2626"                  # large


def matrix_rows():
    out = []
    for d in DISTS:
        me = d == "Iowa City CSD"
        tds = [f'<th class="dname{" me" if me else ""}">{html.escape(d)}</th>']
        for y in YEARS:
            r = cell.get((d, y))
            if not r or f(r["ending_diff_pct"]) is None:
                tds.append('<td class="na">—</td>')
                continue
            pct = f(r["ending_diff_pct"]); diff = f(r["ending_diff"])
            flag = r["flag"] == "Y"
            c = color(pct)
            title = f"{d} FY{y}: CAR {f(r['car_ending']):,.0f} vs audited {f(r['audited_ending']):,.0f} ({diff:+,.0f})"
            style = f"color:{c};font-weight:{'800' if flag else '600'}"
            ring = "box-shadow:inset 0 0 0 2px #dc2626;border-radius:6px" if flag else ""
            tds.append(f'<td style="{style};{ring}" title="{html.escape(title)}">{pct:+.1f}%</td>')
        out.append(f"<tr>{''.join(tds)}</tr>")
    return "\n".join(out)


flagged = [r for r in rows if r["flag"] == "Y"]
flagged.sort(key=lambda r: -abs(f(r["ending_diff_pct"])))
flag_li = "\n".join(
    f"<li><b>{html.escape(r['district'])} FY{r['fiscal_year']}</b>: CAR "
    f"{f(r['car_ending']):,.0f} vs audited {f(r['audited_ending']):,.0f} "
    f"(<b style=\"color:{color(f(r['ending_diff_pct']))}\">{f(r['ending_diff_pct']):+.1f}%</b>, "
    f"{f(r['ending_diff']):+,.0f})</li>"
    for r in flagged)

date = datetime.date(2026, 6, 11).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CAR vs. audited — do districts' self-reports match their books?</title>
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
table{{border-collapse:collapse;width:100%;font-size:14px;margin-top:6px}}
th,td{{padding:7px 10px;text-align:right;border-bottom:1px solid var(--line)}}
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
</style></head><body>{nav("car")}<div class="wrap">

<h1>Self-report vs. audit: do the books reconcile?</h1>
<p class="sub">Each district's <b>Certified Annual Report</b> (CAR — the unaudited figures it files with the state) compared to its <b>audited</b> General Fund results · {date}</p>

<div class="card intro">
<p>Every Iowa district files a <b>Certified Annual Report (CAR)</b> with the Department of Education by
September 15 — its own, <b>unaudited</b> account of the year. Months or years later, an independent
<b>audit</b> reports the same year. <b>The two should match.</b> When a district's self-reported numbers
don't reconcile to what the auditors ultimately find, that's a red flag about the quality of its books.</p>
<p>Below: the gap between CAR and audited <b>ending General Fund balance</b>, by district and year. Green
means they tie (within rounding); warmer colors mean larger gaps; a <b style="color:#dc2626">red outline</b>
flags a gap over 1% and $250K.</p>
</div>

<div class="flag">
<h2>⚠️ Iowa City CSD, FY2023 — the standout</h2>
<div class="big">
  <div class="stat"><div class="n">+{ic_pct:.1f}%</div><div class="l">CAR ending balance vs audited (+${ic_diff/1e3:,.0f}K) — the largest gap in the matrix</div></div>
  <div class="stat"><div class="n">+{un_pct:.0f}%</div><div class="l">CAR <b>unassigned</b> reserves vs audited (+${un_diff/1e6:.2f}M) — the liquid cushion</div></div>
  <div class="stat"><div class="n">${ic_car_net/1e6:.2f}M</div><div class="l">net change ICCSD's CAR reported — the audit found just ${ic_aud_net/1e3:,.0f}K</div></div>
</div>
<p class="take">Iowa City's CAR said the district <b>added ${ic_car_net/1e6:.2f}M</b> to its General Fund in
FY2023; the audit found the true gain was <b>${ic_aud_net/1e3:,.0f}K</b> — an overstatement of
<b>~${(ic_car_net-ic_aud_net)/1e3:,.0f}K</b>. The CAR's ending balance came in <b>${ic_diff/1e3:,.0f}K
({ic_pct:+.1f}%) too high</b>, and its <b>unassigned</b> reserves — the liquid, spendable cushion and the
solvency-ratio numerator — were <b>{un_pct:.0f}% too high</b> (${ic_car_un:,.0f} reported vs ${ic_aud_un:,.0f}
audited). Even the year's <b>beginning</b> balance was off by ${ic_beg_tie:,.0f}. This is the year the
auditor declared a material weakness — "financial statements required significant revisions."</p>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:20px">CAR vs. audited — ending General Fund balance gap</h2>
<table>
<thead><tr><th class="dname">District</th>{''.join(f'<th>FY{y}</th>' for y in YEARS)}</tr></thead>
<tbody>
{matrix_rows()}
</tbody>
</table>
<div class="legend">Gap (CAR − audited):
<span><i style="background:#16a34a"></i>&lt;0.5% (ties)</span>
<span><i style="background:#d97706"></i>0.5–2%</span>
<span><i style="background:#ea580c"></i>2–5%</span>
<span><i style="background:#dc2626"></i>&gt;5%</span>
<span><i style="background:#fff;box-shadow:inset 0 0 0 2px #dc2626"></i>flagged (&gt;1% &amp; &gt;$250K)</span>
</div>
</div>

<div class="card">
<h2 style="margin:0 0 6px;font-size:20px">Flagged district-years ({len(flagged)})</h2>
<ul>
{flag_li}
</ul>
<p class="take"><b>Most CARs reconcile to the penny</b> — the majority of cells tie within rounding, which
is what a clean district looks like. The exceptions cluster in a few districts. <b>Iowa City's FY2023
gap (+{ic_pct:.1f}%) is the largest in the matrix</b> and lands in the exact year its audit was filed 26
months late with a material weakness. <b>Davenport</b> shows a persistent ~2% gap across four straight
years — a chronic reconciliation pattern worth watching. The FY2024 flags sit on the newest audits, which
were only recently finalized.</p>
</div>

<footer>
<b>Sources.</b> CAR: Iowa Department of Education Certified Annual Report — annual workbooks (FY2023,
FY2024) and the multi-year revenue/expenditure files (FY2017–2023). Audited: each district's ACFR
(General Fund total fund balance), as compiled in this project. Comparison is the General Fund ending
balance; a row is flagged when CAR differs from audited by &ge;1% and &ge;$250,000. Iowa City has no
FY2024 audit filed, so its FY2024 cell is blank. Built by <code>scripts/extract_car.py</code> +
<code>scripts/compare_car_vs_audited.py</code> + <code>scripts/build_car_report.py</code>.
</footer>
</div></body></html>"""

open("car-vs-audited.html", "w").write(DOC)
print(f"Wrote car-vs-audited.html ({len(DOC)//1024} KB), {len(rows)} district-years, {len(flagged)} flagged")
