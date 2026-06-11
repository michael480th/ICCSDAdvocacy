#!/usr/bin/env python3
"""
Build a self-contained operating-cash trend: General Fund days-cash-on-hand for Iowa City CSD
vs. its size-matched peers (5,000+ students), FY2020-FY2025. Operating cash = audited General
Fund cash & investments (data/gf-operating-cash.csv, from the ACFRs; Iowa City FY2024 from the
CAR since no FY2024 audit is filed). Days-cash = cash / (General Fund expenditures / 365), the
standard size-neutral liquidity yardstick; GFOA recommends >= ~60 days.

Run:  python3 scripts/build_operating_cash.py  ->  iccsd-operating-cash.html
"""
import csv, html, datetime, statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

IC = "Iowa City CSD"
PEERS = ["Ankeny CSD", "Cedar Rapids CSD", "College CSD (Prairie)", "Davenport CSD",
         "Des Moines Independent CSD", "Dubuque CSD", "Johnston CSD", "Linn-Mar CSD",
         "Pleasant Valley CSD", "Waterloo CSD", "Waukee CSD", "West Des Moines CSD"]
YEARS = list(range(2020, 2026))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# audited GF expenditures (denominator)
exp = {}
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    e = num(r["gf_expenditure"])
    if e:
        exp[(r["district"], int(r["fiscal_year"]))] = e
# Iowa City FY2024 expenditures from CAR (no audit)
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["district_code"] == "3141" and r["fiscal_year"] == "2024" and r["fund"] == "General":
        exp[(IC, 2024)] = num(r["expenditures"])

# operating cash -> days-cash
days = {}   # district -> {fy: days}
cash = {}
for r in csv.DictReader(open("data/gf-operating-cash.csv")):
    d, fy, c = r["district"], int(r["fiscal_year"]), num(r["gf_cash_investments"])
    cash.setdefault(d, {})[fy] = c
    e = exp.get((d, fy))
    if c is not None and e:
        days.setdefault(d, {})[fy] = c / (e / 365.0)


def peer_avg(y):
    vals = [days[p][y] for p in PEERS if y in days.get(p, {})]
    return st.mean(vals) if vals else None


# ---- SVG line chart ----
W, H = 860, 430
L, R, T, B = 60, 150, 28, 46
pw, ph = W - L - R, H - T - B
YMIN, YMAX = 0, 160
def X(i): return L + pw * i / (len(YEARS) - 1)
def Y(v): return T + ph * (YMAX - v) / (YMAX - YMIN)

s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="operating cash trend">']
for g in range(0, 161, 20):
    s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+pw}" y2="{Y(g):.1f}" class="grid"/>')
    s.append(f'<text x="{L-8}" y="{Y(g)+4:.1f}" class="ytick">{g}</text>')
# GFOA 60-day reference
s.append(f'<line x1="{L}" y1="{Y(60):.1f}" x2="{L+pw}" y2="{Y(60):.1f}" class="ref"/>')
s.append(f'<text x="{L+pw-4}" y="{Y(60)-6:.1f}" class="reflab">GFOA guideline ≈ 60 days</text>')
for i, y in enumerate(YEARS):
    s.append(f'<text x="{X(i):.1f}" y="{T+ph+22}" class="xtick">{y}</text>')


def poly(d, color, width):
    pts = [(X(i), Y(days[d][y])) for i, y in enumerate(YEARS) if y in days.get(d, {})]
    if not pts:
        return ""
    line = f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{color}" stroke-width="{width}"/>'
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3.4 if width>2.5 else 2.4}" fill="{color}"/>' for x, y in pts)
    return line + dots


for p in PEERS:
    s.append(poly(p, "#cbd5e1", 1.4))
avg = {y: peer_avg(y) for y in YEARS if peer_avg(y) is not None}
apts = [(X(i), Y(avg[y])) for i, y in enumerate(YEARS) if y in avg]
s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in apts)}" fill="none" stroke="#2563eb" stroke-width="2.6" stroke-dasharray="7 4"/>')
s.append(poly(IC, "#dc2626", 3.4))
# end labels
icy = [y for y in YEARS if y in days[IC]]
lx, ly = X(YEARS.index(icy[-1])), Y(days[IC][icy[-1]])
s.append(f'<text x="{lx+8:.1f}" y="{ly+4:.1f}" class="endlab" fill="#dc2626" style="font-weight:700">Iowa City</text>')
ay = avg[max(avg)]
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+4:.1f}" class="endlab" fill="#2563eb">Peer average</text>')
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+20:.1f}" class="endlab2" fill="#94a3b8">(large districts)</text>')
s.append('</svg>')
svg = "".join(s)

ic20, ic23 = days[IC][2020], days[IC][2023]
ic24 = days[IC].get(2024)
pa23 = peer_avg(2023)
date = datetime.date(2026, 6, 11).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Operating cash trend vs. peers</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.intro{{border-left:4px solid #2563eb}} .intro p{{margin:7px 0}}
.chart{{width:100%;height:auto;display:block}}
.grid{{stroke:#eef2f7;stroke-width:1}} .ytick{{fill:#94a3b8;font-size:12px;text-anchor:end}} .xtick{{fill:#64748b;font-size:13px;text-anchor:middle}}
.ref{{stroke:#16a34a;stroke-width:1.4;stroke-dasharray:5 4;opacity:.8}} .reflab{{fill:#16a34a;font-size:11px;text-anchor:end}}
.endlab{{font-size:13px}} .endlab2{{font-size:11px}}
.legend{{font-size:13px;color:var(--mut);margin:8px 2px 0;display:flex;gap:18px;flex-wrap:wrap;align-items:center}}
.legend i{{display:inline-block;width:22px;height:0;border-top-width:3px;border-top-style:solid;vertical-align:middle;margin-right:6px}}
.take{{margin:14px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #dc2626;border-radius:6px;padding:10px 14px}}
.take b{{color:#0f172a}}
footer{{color:var(--mut);font-size:12.5px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body>{nav("cash")}<div class="wrap">

<h1>Iowa City Schools: Operating Cash on Hand</h1>
<p class="sub">General Fund <b>days-cash-on-hand</b> — how many days the district could run on its operating cash — vs. size-matched peers, FY2020–FY2025 · {date}</p>

<div class="card intro">
<p><b>What it is:</b> the most direct measure of liquidity — the district's General Fund cash &amp;
investments divided by its average daily spending. It answers "if the money stopped coming in, how many
days could the lights stay on?" Unlike reserves or spending authority, this is <b>actual cash</b>.</p>
<p><b>Why days, not dollars:</b> a big district needs more cash than a small one, so raw dollars aren't
comparable — days-cash normalizes for size. <b>GFOA recommends keeping at least ~60 days.</b></p>
</div>

<div class="card">
<div class="legend">
  <span><i style="border-color:#dc2626;border-top-width:4px"></i>Iowa City CSD</span>
  <span><i style="border-color:#2563eb;border-top-style:dashed"></i>Peer average</span>
  <span><i style="border-color:#cbd5e1"></i>Individual peers</span>
  <span><i style="border-color:#16a34a;border-top-style:dashed"></i>GFOA ≈ 60 days</span>
</div>
{svg}
<p class="take">Iowa City has run <b>below the ~60-day GFOA guideline every year</b>, and its operating
cash <b>fell steadily from ~{ic20:.0f} days in 2020 to ~{ic23:.0f} days in 2023</b> — the thinnest of any
large district — while the peer average sat near <b>{pa23:.0f} days</b>. {"Its FY2024 figure recovers to ~" + f"{ic24:.0f}" + " days (from the CAR, since the FY2024 audit isn't filed) — still under 60." if ic24 else ""}
This is the cash-in-the-bank view behind the district's tax-anticipation-warrant and interfund-loan
discussions: the cushion got thin enough that a bad month or a late state payment was a real problem.</p>
</div>

<footer>
<b>Sources.</b> Operating cash = General Fund "cash &amp; investments" from the first fund column of each
district's audited <i>Balance Sheet — Governmental Funds</i> (ACFRs in <code>auditreports/</code>,
FY2020–FY2025). Iowa City's FY2024 point is from the Certified Annual Report (no FY2024 audit is filed),
and its FY2024/FY2025 audits remain outstanding. Days-cash = cash &divide; (General Fund expenditures /
365), using audited expenditures. College (Prairie)'s FY2020 balance sheet used an older layout and is
omitted. "Peers" are the 12 districts with 5,000+ students. Built by
<code>scripts/extract_audit_cash.py</code> + <code>scripts/build_operating_cash.py</code>.
</footer>
</div></body></html>"""

open("iccsd-operating-cash.html", "w").write(DOC)
print(f"Wrote iccsd-operating-cash.html ({len(DOC)//1024} KB)")
print("ICCSD days-cash:", {y: round(days[IC][y]) for y in sorted(days[IC])})
print("Peer avg by year:", {y: round(peer_avg(y)) for y in YEARS if peer_avg(y)})
