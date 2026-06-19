#!/usr/bin/env python3
"""
Build iccsd-net-cash-ratio.html — the district's own "Day's Net Cash Ratio" KPI, computed
the same way ICCSD computes it on its internal dashboard, but extended across the size-matched
peer districts and back to FY2015.

  Day's Net Cash Ratio = (General Fund) Cash & Investments / (Total Expenditures / 365)
                       = number of days the district could carry expenditures without new cash.

This is the district's own formula (CAR refs BalSheet C1L1 / ExpGF C8L42). Our independent
extraction of Cash & Investments from the audited balance sheets reproduces ICCSD's published
dashboard figures to within ~$2 (rounding), and the resulting day counts match exactly
(FY2015 = 67 ... FY2019 = 63). The district's own target is 90 days; we shade 90-120 as the
recommended range (an Iowa-seasonally-appropriate buffer, above GFOA's ~60-day general floor).

Inputs: data/gf-operating-cash.csv (cash, FY2015-2025), data/iowa-district-financials.csv and
data/audit-financials.csv (General Fund expenditures). Self-contained SVG.

Run:  python3 scripts/build_net_cash_ratio.py   ->  iccsd-net-cash-ratio.html
"""
import csv, html, datetime, statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

IC = "Iowa City CSD"
PEERS = ["Ankeny CSD", "Cedar Rapids CSD", "College CSD (Prairie)", "Davenport CSD",
         "Des Moines Independent CSD", "Dubuque CSD", "Johnston CSD", "Linn-Mar CSD",
         "Pleasant Valley CSD", "Waterloo CSD", "Waukee CSD", "West Des Moines CSD"]
YEARS = list(range(2015, 2026))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# General Fund expenditures: prefer the audited series (FY2015-2023), fall back to the
# master file (FY2020-2025) so the denominator spans the whole window.
exp = {}
for r in csv.DictReader(open("data/audit-financials.csv")):
    e = num(r["expenditures"])
    if e:
        exp[(r["district"], int(r["fiscal_year"]))] = e
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    e = num(r["gf_expenditure"])
    if e:
        exp.setdefault((r["district"], int(r["fiscal_year"])), e)
# Iowa City FY2024 expenditures from CAR (no audit filed)
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["district_code"] == "3141" and r["fiscal_year"] == "2024" and r["fund"] == "General":
        exp[(IC, 2024)] = num(r["expenditures"])

# Cash & investments -> Day's Net Cash Ratio
days = {}
IC_UNAUDITED = set()
for r in csv.DictReader(open("data/gf-operating-cash.csv")):
    d, fy, c = r["district"], int(r["fiscal_year"]), num(r["gf_cash_investments"])
    e = exp.get((d, fy))
    if c is not None and e:
        days.setdefault(d, {})[fy] = c / (e / 365.0)
    if d == IC and r.get("source") != "audit":
        IC_UNAUDITED.add(fy)


def peer_avg(y):
    vals = [days[p][y] for p in PEERS if y in days.get(p, {})]
    return st.mean(vals) if vals else None


# ---- SVG chart ----
W, H = 880, 460
L, R, T, B = 56, 150, 24, 46
pw, ph = W - L - R, H - T - B
YMIN, YMAX = 0, 200
def X(i): return L + pw * i / (len(YEARS) - 1)
def Y(v): return T + ph * (YMAX - v) / (YMAX - YMIN)

s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Day\'s Net Cash Ratio by district, 2015-2025">']
# recommended band 90-120
s.append(f'<rect x="{L}" y="{Y(120):.1f}" width="{pw}" height="{Y(90)-Y(120):.1f}" fill="#16a34a" opacity="0.10"/>')
s.append(f'<text x="{L+6}" y="{Y(120)+14:.1f}" class="bandlab">recommended range 90–120 days</text>')
for g in range(0, 201, 20):
    s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+pw}" y2="{Y(g):.1f}" class="grid"/>')
    s.append(f'<text x="{L-8}" y="{Y(g)+4:.1f}" class="ytick">{g}</text>')
# GFOA 60-day reference floor
s.append(f'<line x1="{L}" y1="{Y(60):.1f}" x2="{L+pw}" y2="{Y(60):.1f}" class="ref60"/>')
s.append(f'<text x="{L+pw-4}" y="{Y(60)-5:.1f}" class="reflab60">GFOA ≈ 60-day floor</text>')
for i, y in enumerate(YEARS):
    s.append(f'<text x="{X(i):.1f}" y="{T+ph+22}" class="xtick">{y}</text>')


def poly(d, color, width):
    pts = [(X(i), Y(days[d][y])) for i, y in enumerate(YEARS) if y in days.get(d, {})]
    if not pts:
        return ""
    line = f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{color}" stroke-width="{width}"/>'
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3.2 if width>2.5 else 2.2}" fill="{color}"/>' for x, y in pts)
    return line + dots


for p in PEERS:
    s.append(poly(p, "#cbd5e1", 1.4))
avg = {y: peer_avg(y) for y in YEARS if peer_avg(y) is not None}
apts = [(X(i), Y(avg[y])) for i, y in enumerate(YEARS) if y in avg]
s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in apts)}" fill="none" stroke="#2563eb" stroke-width="2.6" stroke-dasharray="7 4"/>')
# Iowa City (bold red); hollow markers for unaudited years (FY2024 CAR)
icpts = [(i, y) for i, y in enumerate(YEARS) if y in days.get(IC, {})]
s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(days[IC][y]):.1f}" for i, y in icpts)}" fill="none" stroke="#dc2626" stroke-width="3.4"/>')
for i, y in icpts:
    if y in IC_UNAUDITED:
        s.append(f'<circle cx="{X(i):.1f}" cy="{Y(days[IC][y]):.1f}" r="4.4" fill="#fff" stroke="#dc2626" stroke-width="2.4"/>')
        s.append(f'<text x="{X(i):.1f}" y="{Y(days[IC][y])-12:.1f}" class="endlab2" fill="#b45309" text-anchor="middle">{y} (unaudited)</text>')
    else:
        s.append(f'<circle cx="{X(i):.1f}" cy="{Y(days[IC][y]):.1f}" r="3.8" fill="#dc2626"/>')
# end labels
li, ly = icpts[-1]
s.append(f'<text x="{X(li)+8:.1f}" y="{Y(days[IC][ly])+4:.1f}" class="endlab" fill="#dc2626" style="font-weight:700">Iowa City</text>')
ay = avg[max(avg)]
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+4:.1f}" class="endlab" fill="#2563eb">Peer average</text>')
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+20:.1f}" class="endlab2" fill="#94a3b8">(large districts)</text>')
s.append('</svg>')
svg = "".join(s)

# prose numbers
ic_first = days[IC][min(days[IC])]
ic_peak = max(days[IC].values())
ic_peak_y = max(days[IC], key=days[IC].get)
ic_last_y = max(days[IC])
ic_last = days[IC][ic_last_y]
pa_last = peer_avg(ic_last_y) or peer_avg(max(avg))
n_in_band = sum(1 for p in PEERS if max(days[p]) in days[p] and 90 <= days[p][max(days[p])] <= 120)

# per-district latest table
def latest(d):
    if d not in days: return (None, None)
    y = max(days[d]); return (y, days[d][y])
tbl = []
for d in [IC] + PEERS:
    y, v = latest(d)
    if v is None: continue
    band = "#16a34a" if v >= 90 else ("#d97706" if v >= 60 else "#dc2626")
    tbl.append((d, y, v, band))
tbl.sort(key=lambda r: -r[2])
trows = "\n".join(
    f'<tr{" class=me" if d==IC else ""}><td class="dn">{html.escape(d)}</td>'
    f'<td>FY{y}</td><td style="color:{c};font-weight:{800 if d==IC else 600}">{v:.0f}</td></tr>'
    for d, y, v, c in tbl)

date = datetime.date(2026, 6, 19).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Day's Net Cash Ratio vs. peers</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04);overflow-x:auto}}
.intro{{border-left:4px solid #2563eb}} .intro p{{margin:7px 0}}
.formula{{background:#f8fafc;border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:10px 0;font-size:15px;text-align:center}}
.formula .frac{{display:inline-block;text-align:center;margin:0 4px;vertical-align:middle}}
.formula .frac .n{{display:block;border-bottom:2px solid #334155;padding:0 8px}}
.formula .frac .d{{display:block;padding:0 8px}}
.valid{{background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #16a34a;border-radius:10px;padding:14px 18px;margin-bottom:18px;font-size:14.5px}}
.valid b{{color:#166534}}
.valid table{{border-collapse:collapse;margin-top:8px;font-size:13.5px}}
.valid td,.valid th{{padding:3px 12px 3px 0;text-align:right}} .valid th{{color:var(--mut);font-weight:600}}
.valid td:first-child,.valid th:first-child{{text-align:left}}
.chart{{width:100%;height:auto;display:block}}
.grid{{stroke:#eef2f7;stroke-width:1}} .ytick{{fill:#94a3b8;font-size:12px;text-anchor:end}} .xtick{{fill:#64748b;font-size:13px;text-anchor:middle}}
.ref60{{stroke:#94a3b8;stroke-width:1.3;stroke-dasharray:4 4;opacity:.8}} .reflab60{{fill:#94a3b8;font-size:11px;text-anchor:end}}
.bandlab{{fill:#16a34a;font-size:11px;opacity:.9}}
.endlab{{font-size:13px}} .endlab2{{font-size:11px}}
.legend{{font-size:13px;color:var(--mut);margin:8px 2px 0;display:flex;gap:16px;flex-wrap:wrap;align-items:center}}
.legend i{{display:inline-block;width:22px;height:0;border-top-width:3px;border-top-style:solid;vertical-align:middle;margin-right:6px}}
.take{{margin:14px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #dc2626;border-radius:6px;padding:10px 14px}}
.take b{{color:#0f172a}}
table.rank{{border-collapse:collapse;width:100%;font-size:14px;margin-top:4px}}
table.rank td,table.rank th{{padding:6px 10px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}}
table.rank th{{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.03em}}
table.rank td.dn{{text-align:left;font-weight:600}} table.rank tr.me{{background:#eff6ff}} table.rank tr.me td.dn{{color:#1d4ed8}}
footer{{color:var(--mut);font-size:12.5px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}}
footer a{{color:#2563eb}}
</style></head><body>{nav("more")}<div class="wrap">

<h1>Day's Net Cash Ratio — Iowa City vs. peers</h1>
<p class="sub">The district's own liquidity KPI — how many days it could keep paying the bills on cash on hand — computed across the large Iowa districts, FY2015–FY2025 · {date}</p>

<div class="card intro">
<p><b>What it is:</b> Iowa City tracks a "Day's Net Cash Ratio" on its own financial dashboard. It answers
the most concrete liquidity question — <b>how many days the district could carry expenditures without any
new cash coming in.</b></p>
<div class="formula">
Day's Net Cash Ratio =
<span class="frac"><span class="n">Cash &amp; Investments</span><span class="d">Total Expenditures ÷ 365</span></span>
</div>
<p><b>The recommended range is 90–120 days</b> (shaded green). That is the district's own target (90 days)
and reflects Iowa's seasonal property-tax timing — districts receive tax money in big lumps in fall and
spring, so they need a larger buffer than GFOA's general ~60-day floor (gray line) to bridge the gap.</p>
</div>

<div class="valid">
<b>✓ Validated against the district's own numbers.</b> We extracted Cash &amp; Investments independently from
each audited balance sheet. For the five years ICCSD published this KPI itself, our figures match the
district's dashboard to within about $2 (rounding), and the day counts match exactly:
<table>
<tr><th>Fiscal year</th><th>2015</th><th>2016</th><th>2017</th><th>2018</th><th>2019</th></tr>
<tr><td>District dashboard</td><td>67</td><td>84</td><td>88</td><td>79</td><td>63</td></tr>
<tr><td>Our calculation</td>
<td>{days[IC][2015]:.0f}</td><td>{days[IC][2016]:.0f}</td><td>{days[IC][2017]:.0f}</td><td>{days[IC][2018]:.0f}</td><td>{days[IC][2019]:.0f}</td></tr>
</table>
</div>

<div class="card">
<div class="legend">
  <span><i style="border-color:#dc2626;border-top-width:4px"></i>Iowa City CSD</span>
  <span><i style="border-color:#2563eb;border-top-style:dashed"></i>Peer average</span>
  <span><i style="border-color:#cbd5e1"></i>Individual peers</span>
  <span><span style="display:inline-block;width:14px;height:10px;background:#16a34a;opacity:.2;vertical-align:middle;margin-right:5px"></span>recommended 90–120</span>
  <span><span style="display:inline-block;width:11px;height:11px;border:2px solid #dc2626;border-radius:50%;background:#fff;vertical-align:middle;margin-right:5px"></span>unaudited (FY2024 CAR)</span>
</div>
{svg}
<p class="take">Iowa City sat <b>inside or near the 90–120 recommended band a decade ago</b> (peaking at
~<b>{ic_peak:.0f} days in {ic_peak_y}</b>), then fell steadily out of it. By <b>FY{ic_last_y} it was at
~{ic_last:.0f} days</b> — roughly a third of the recommended minimum, and well under even the 60-day GFOA
floor. Its large-district peers have generally stayed at or above the band (peer average ~<b>{pa_last:.0f}
days</b>). Iowa City has gone from a typical Iowa cushion to the thinnest in the group.</p>
</div>

<div class="card">
<h2 style="margin:0 0 6px;font-size:19px">Most recent year, ranked</h2>
<table class="rank">
<thead><tr><th class="dn">District</th><th>Year</th><th>Day's Net Cash Ratio</th></tr></thead>
<tbody>
{trows}
</tbody>
</table>
<p style="font-size:13px;color:#64748b;margin:8px 2px 0">Green ≥ 90 (in range) · amber 60–90 · red &lt; 60. Latest audited year shown per district; Iowa City's FY2024 is its unaudited self-report.</p>
<p style="font-size:13.5px;color:#64748b;margin:12px 2px 0">This is the intuitive "days" view. For how the <b>credit-rating agencies</b> score the same liquidity — reserves vs. net cash, as a percent of revenue — see <a href="liquidity-lenses.html" style="color:#2563eb;font-weight:600;text-decoration:none">Two liquidity lenses</a>.</p>
</div>

<footer>
<b>Sources.</b> Day's Net Cash Ratio = General Fund Cash &amp; Investments ÷ (General Fund expenditures / 365),
the district's own dashboard formula (CAR refs BalSheet C1L1 / ExpGF C8L42). Cash &amp; Investments extracted
from the first General-Fund column of each district's audited <i>Balance Sheet — Governmental Funds</i>
(<code>auditreports/</code>, FY2015–FY2023; later years where filed); Iowa City FY2024 from its unaudited
Certified Annual Report. Expenditures from the audited statements (<code>data/audit-financials.csv</code>,
FY2015–FY2023) and the master file (<code>data/iowa-district-financials.csv</code>, FY2020–FY2025). "Peers"
are the 12 districts with 5,000+ students; a few district-years are blank where an older balance-sheet
layout couldn't be read cleanly. Built by <code>scripts/extract_audit_cash.py</code> +
<code>scripts/build_net_cash_ratio.py</code>.
</footer>
</div></body></html>"""

open("iccsd-net-cash-ratio.html", "w").write(DOC)
print(f"Wrote iccsd-net-cash-ratio.html ({len(DOC)//1024} KB)")
print("ICCSD:", {y: round(days[IC][y]) for y in sorted(days[IC])})
print("Peer avg:", {y: round(peer_avg(y)) for y in YEARS if peer_avg(y)})
