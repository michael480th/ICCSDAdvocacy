#!/usr/bin/env python3
"""
Build a self-contained, public-facing report showing the TREND of Iowa City CSD
drawing down its reserves over time, against its size-matched peers (5,000+ students).

Two time-series:
  1. Spending-authority cushion  — Unspent Authorized Budget as a % of the maximum
     authorized budget, FY2017-FY2025. The only reserve measure that exists for every
     district across the whole window (state-computed, exists even where audits are late).
  2. True cash reserves          — the audited general-fund solvency ratio (assigned +
     unassigned fund balance as a % of revenue), FY2020-FY2025 (from the ACFRs).

Each chart draws every peer as a faint line, the peer average as a bold dashed line, and
Iowa City as a bold red line, so the drawdown vs. peers reads at a glance. Self-contained
SVG — no internet, no dependencies. Reads UAB/ workbook + data/iowa-district-financials.csv.

Run:  python3 scripts/build_liquidity_trend.py   ->  iccsd-liquidity-trend.html
"""
import openpyxl, csv, html, datetime, statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

CODE = {"0261":"Ankeny CSD","0882":"Burlington CSD","1053":"Cedar Rapids CSD",
"1337":"College CSD (Prairie)","1611":"Davenport CSD","1737":"Des Moines Independent CSD",
"1863":"Dubuque CSD","3141":"Iowa City CSD","3231":"Johnston CSD","3715":"Linn-Mar CSD",
"4581":"Muscatine CSD","5250":"Pleasant Valley CSD","6795":"Waterloo CSD","6822":"Waukee CSD",
"6957":"West Des Moines CSD"}
IC = "Iowa City CSD"
# Size-matched peers: the 5,000+ student districts (same definition as iccsd-vs-peers.html)
PEERS = ["Ankeny CSD","Cedar Rapids CSD","College CSD (Prairie)","Davenport CSD",
         "Des Moines Independent CSD","Dubuque CSD","Johnston CSD","Linn-Mar CSD",
         "Pleasant Valley CSD","Waterloo CSD","Waukee CSD","West Des Moines CSD"]

# ---------- 1. Spending-authority cushion (UAB %), FY2017-2025 ----------
wb = openpyxl.load_workbook("UAB/Unspent Authorized Budget Report.xlsx", data_only=True, read_only=True)
ws = wb["data_UAB"]
uab = {}                                  # name -> {fy: pct}
for row in ws.iter_rows(min_row=2, values_only=True):
    fy, dist = row[0], row[1]
    if dist in CODE and isinstance(fy, int) and 2017 <= fy <= 2025 and row[37]:
        uab.setdefault(CODE[dist], {})[fy] = round(100 * row[38] / row[37], 2)
UAB_YEARS = list(range(2017, 2026))

# ---------- 2. True cash reserves (audited solvency ratio %), FY2020-2025 ----------
solv = {}
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    d, fy, v = r["district"], int(r["fiscal_year"]), r["solvency_ratio_pct"]
    if (d == IC or d in PEERS) and v not in ("", None):
        solv.setdefault(d, {})[fy] = float(v)
SOLV_YEARS = list(range(2020, 2026))


def peer_avg(series, year):
    vals = [series[p][year] for p in PEERS if year in series.get(p, {})]
    return st.mean(vals) if vals else None


# ---------- SVG line-chart renderer ----------
def chart(series, years, ymin, ymax, refs, title, ylab, healthy=None):
    """refs = list of (yvalue, label, css-class). healthy=(lo,hi) shades a green band."""
    W, H = 860, 420
    L, R, T, B = 64, 150, 28, 46          # margins (R wide for the inline labels)
    pw, ph = W - L - R, H - T - B

    def X(i): return L + pw * i / (len(years) - 1)
    def Y(v): return T + ph * (ymax - v) / (ymax - ymin)

    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="{html.escape(title)}">']
    # healthy band
    if healthy:
        lo, hi = healthy
        s.append(f'<rect x="{L}" y="{Y(hi):.1f}" width="{pw}" height="{Y(lo)-Y(hi):.1f}" '
                 f'fill="#16a34a" opacity="0.07"/>')
        s.append(f'<text x="{L+6}" y="{Y(hi)+13:.1f}" class="bandlab">healthy range {lo}–{hi}%</text>')
    # horizontal gridlines + y labels
    step = 5
    g = ymin - (ymin % step)
    while g <= ymax:
        yy = Y(g)
        s.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L+pw}" y2="{yy:.1f}" class="grid"/>')
        s.append(f'<text x="{L-8}" y="{yy+4:.1f}" class="ytick">{g:g}%</text>')
        g += step
    # reference lines (e.g. 0% danger)
    for val, lab, cls in refs:
        yy = Y(val)
        s.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L+pw}" y2="{yy:.1f}" class="ref {cls}"/>')
        s.append(f'<text x="{L+pw-4}" y="{yy-5:.1f}" class="reflab {cls}">{html.escape(lab)}</text>')
    # x labels
    for i, y in enumerate(years):
        s.append(f'<text x="{X(i):.1f}" y="{T+ph+22}" class="xtick">{y}</text>')

    def poly(name, cls, width, dash=""):
        pts = [(X(i), Y(series[name][y])) for i, y in enumerate(years) if y in series.get(name, {})]
        if not pts: return ""
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        out = f'<polyline points="{d}" fill="none" stroke="{cls}" stroke-width="{width}" {dash}/>'
        dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{2.6 if width<3 else 3.4}" fill="{cls}"/>' for x, y in pts)
        return out + dots

    # faint peer spaghetti
    for p in PEERS:
        s.append(poly(p, "#cbd5e1", 1.4))
    # peer-average (dashed blue)
    avg_series = {"avg": {y: peer_avg(series, y) for y in years if peer_avg(series, y) is not None}}
    pts = [(X(i), Y(avg_series["avg"][y])) for i, y in enumerate(years) if y in avg_series["avg"]]
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    s.append(f'<polyline points="{d}" fill="none" stroke="#2563eb" stroke-width="2.6" stroke-dasharray="7 4"/>')
    # Iowa City (bold red) on top
    s.append(poly(IC, "#dc2626", 3.4))
    # end-of-line inline labels
    def endlabel(name, color, text, weight="700"):
        ys = [y for y in years if y in series.get(name, {})]
        if not ys: return
        ly, lx = series[name][ys[-1]], X(years.index(ys[-1]))
        s.append(f'<text x="{lx+8:.1f}" y="{Y(ly)+4:.1f}" class="endlab" fill="{color}" '
                 f'style="font-weight:{weight}">{html.escape(text)}</text>')
    endlabel(IC, "#dc2626", "Iowa City")
    # place avg label at last avg point
    la_y = avg_series["avg"][max(avg_series["avg"])]
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(la_y)+4:.1f}" class="endlab" fill="#2563eb">Peer average</text>')
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(la_y)+20:.1f}" class="endlab2" fill="#94a3b8">(other large districts)</text>')
    s.append('</svg>')
    return f'<figure><figcaption><b>{html.escape(title)}</b><span>{html.escape(ylab)}</span></figcaption>{"".join(s)}</figure>'


# numbers for the prose
ic17, ic25 = uab[IC][2017], uab[IC][2025]
pa17, pa25 = peer_avg(uab, 2017), peer_avg(uab, 2025)
ic_solv20, ic_solv23 = solv[IC][2020], solv[IC][2023]
pa_solv23 = peer_avg(solv, 2023)

chart1 = chart(uab, UAB_YEARS, -8, 35,
               [(0, "0% — negative triggers a state-supervised recovery plan", "danger")],
               "Spending-authority cushion, FY2017–FY2025",
               "Unspent Authorized Budget, as a % of the district's budget — higher is more cushion")
chart2 = chart(solv, SOLV_YEARS, -8, 36, [(0, "0%", "danger")],
               "True cash reserves (audited), FY2020–FY2025",
               "General-fund solvency ratio — reserves as a % of one year's revenue — higher is more cushion",
               healthy=(5, 15))

date = datetime.date(2026, 6, 9).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Drawing Down Reserves, 2017–2025</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:30px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px;font-size:16px}}
.intro{{background:#fff;border:1px solid var(--line);border-left:4px solid #2563eb;border-radius:10px;padding:16px 20px;margin-bottom:18px}}
.intro p{{margin:6px 0}} .intro b{{color:var(--ink)}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.card h3{{margin:0 0 2px;font-size:21px}}
.what,.why{{margin:6px 0;font-size:15px;color:#334155}} .what b,.why b{{color:#0f172a}}
figure{{margin:14px 0 6px}}
figcaption{{font-size:13px;color:var(--mut);margin-bottom:4px}} figcaption b{{color:var(--ink);font-size:15px;display:block}} figcaption span{{font-size:13px}}
.chart{{width:100%;height:auto;display:block}}
.grid{{stroke:#eef2f7;stroke-width:1}}
.ytick{{fill:#94a3b8;font-size:12px;text-anchor:end}} .xtick{{fill:#64748b;font-size:13px;text-anchor:middle}}
.ref.danger{{stroke:#dc2626;stroke-width:1.4;stroke-dasharray:3 3;opacity:.7}}
.reflab.danger{{fill:#dc2626;font-size:11px;text-anchor:end;opacity:.85}}
.bandlab{{fill:#16a34a;font-size:11px;opacity:.85}}
.endlab{{font-size:13px}} .endlab2{{font-size:11px}}
.take{{margin:12px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #dc2626;border-radius:6px;padding:10px 14px;color:#1f2937}}
.take b{{color:#0f172a}}
.legend{{font-size:13px;color:var(--mut);margin:6px 2px 0;display:flex;gap:18px;flex-wrap:wrap;align-items:center}}
.legend i{{display:inline-block;width:22px;height:0;border-top-width:3px;border-top-style:solid;vertical-align:middle;margin-right:6px}}
footer{{color:var(--mut);font-size:12.5px;margin-top:30px;border-top:1px solid var(--line);padding-top:14px}}
footer a{{color:#2563eb}}
</style></head><body>{nav("more")}<div class="wrap">

<h1>Iowa City Schools: Drawing Down Its Reserves</h1>
<p class="sub">How Iowa City Community School District's financial cushion has fallen over time, against size-matched peer districts · {date}</p>

<div class="intro">
<p><b>The question:</b> is Iowa City CSD spending down its safety cushion, and how does that trend
compare with similar districts? <b>The answer is yes</b> — and the gap to its peers has widened steadily.</p>
<p>Iowa schools keep two kinds of cushion. One is <b>spending authority</b> (how much the state lets a
district spend), the other is <b>cash reserves</b> (money actually in the bank). Running either toward
zero is the warning sign. We track both below. Each line is a district; <b style="color:#dc2626">Iowa City is red</b>,
the <b style="color:#2563eb">dashed blue line is the peer average</b>, and the faint gray lines are the
other large districts (5,000+ students).</p>
</div>

<div class="legend">
<span><i style="border-color:#dc2626;border-top-width:4px"></i>Iowa City CSD</span>
<span><i style="border-color:#2563eb;border-top-style:dashed"></i>Peer average (large districts)</span>
<span><i style="border-color:#cbd5e1"></i>Individual peer districts</span>
</div>

<div class="card">
<h3>1. Spending-authority cushion — the long view (2017–2025)</h3>
<p class="what"><b>What it is:</b> Iowa caps how much a district may spend each year. This shows the unused
"room" left over (its Unspent Authorized Budget) as a share of its budget. It is the single most-watched
measure of an Iowa district's financial health, and it exists for every district every year — even years
where the audit is late — so it gives the full nine-year trend.</p>
<p class="why"><b>Why it matters:</b> when it hits zero or goes negative, the district has overspent its
legal authority — which is unlawful and forces a state-supervised recovery plan.</p>
{chart1}
<p class="take">Iowa City started the period already thin (<b>{ic17:.1f}%</b> in 2017, about half the
peer average of <b>{pa17:.1f}%</b>) and kept drawing it down — touching <b>0.1% in 2022</b> and going
<b>negative (−1.2%) in 2023</b>, the level that triggers state review. Over the same nine years the
peer average <b>rose</b>, from <b>{pa17:.1f}% to {pa25:.1f}%</b>. The two large districts that were also
low early on (Davenport and Des Moines) rebuilt their cushions to 15–19%; Iowa City is the one that never
recovered. By 2025 its cushion (<b>{ic25:.1f}%</b>) was roughly a <b>seventh</b> of the peer average.</p>
</div>

<div class="card">
<h3>2. True cash reserves — the audited view (2020–2025)</h3>
<p class="what"><b>What it is:</b> the actual rainy-day cash cushion — the district's general-fund reserves
measured against one year of revenue (the "solvency ratio"), straight from the audited financial reports.
In Iowa, <b>5–15% is considered healthy</b>. This is the truest <i>liquidity</i> measure, but it only exists
for years a district has finished its audit — which is why Iowa City's line stops at 2023.</p>
<p class="why"><b>Why it matters:</b> reserves are what absorb a bad budget year, a late state payment, or an
emergency repair. A thin cushion means little margin for error.</p>
{chart2}
<p class="take">The audited cash reserves tell the same story as the spending-authority cushion: Iowa City
sat at <b>{ic_solv20:.1f}% in 2020</b> and slipped to <b>{ic_solv23:.1f}% by 2023</b> — the thinnest of any
large district that has filed, and far below both the 5–15% healthy range and the peer average
(~<b>{pa_solv23:.0f}%</b> in 2023). And the line stops there for a reason: <b>Iowa City's 2024 and 2025
audits still are not filed</b>, so the most recent verified cash position is three years old.</p>
</div>

<footer>
<b>Sources.</b> Spending-authority cushion: Iowa Department of Management <i>Unspent Authorized Budget
Report</i> (state-computed, FY2017–FY2025). True cash reserves: each district's audited Annual
Comprehensive Financial Report (FY2020–FY2025); the solvency ratio is assigned + unassigned general-fund
balance as a percent of general-fund revenue. <b>Peers</b> are the 12 districts in this study with 5,000+
students (Iowa City is ~14,400), the same size-matched group used in the companion
<i>Iowa City Schools: How They Compare</i> report. FY2026 is omitted because that year has not closed —
spending-authority figures only become meaningful once a year's actual spending is in. Figures trace to
official filings; nothing is estimated to fill gaps.
</footer>
</div></body></html>"""

open("iccsd-liquidity-trend.html", "w").write(DOC)
print(f"Wrote iccsd-liquidity-trend.html ({len(DOC)//1024} KB)")
print(f"UAB: ICCSD {ic17:.1f}%(2017) -> {ic25:.1f}%(2025);  peer avg {pa17:.1f}% -> {pa25:.1f}%")
print(f"Solvency: ICCSD {ic_solv20:.1f}%(2020) -> {ic_solv23:.1f}%(2023);  peer avg 2023 {pa_solv23:.1f}%")
