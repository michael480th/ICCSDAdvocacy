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
YEARS = list(range(2020, 2027))


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
IC_AUDITED = set()   # Iowa City years backed by a completed audit (solid line)
for r in csv.DictReader(open("data/gf-operating-cash.csv")):
    d, fy, c = r["district"], int(r["fiscal_year"]), num(r["gf_cash_investments"])
    cash.setdefault(d, {})[fy] = c
    e = exp.get((d, fy))
    if c is not None and e:
        days.setdefault(d, {})[fy] = c / (e / 365.0)
    if d == IC and r.get("source") == "audit":
        IC_AUDITED.add(fy)

# Iowa City FY2025 (unaudited internal) + FY2026 (PFM projection) — not yet audited or state-filed
IC_PROJECTED = set()
for r in csv.DictReader(open("data/iccsd-cash-supplemental.csv")):
    fy, c, e = int(r["fiscal_year"]), num(r["gf_cash_investments"]), num(r["gf_expenditures"])
    if c and e:
        days.setdefault(IC, {})[fy] = c / (e / 365.0)
    if r["status"] == "projected":
        IC_PROJECTED.add(fy)


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
# Iowa City, by certainty: solid+filled = audited (≤2023); dotted+hollow = unaudited actuals
# (FY2024 CAR, FY2025 internal); dashed+hollow = projection (FY2026). Hollow = "not yet audited".
def xy(y): return X(YEARS.index(y)), Y(days[IC][y])
aud = sorted(y for y in days[IC] if y in IC_AUDITED)
unaud = sorted(y for y in days[IC] if y not in IC_AUDITED and y not in IC_PROJECTED)
proj = sorted(y for y in days[IC] if y in IC_PROJECTED)
# solid audited line + filled dots
ap = [xy(y) for y in aud]
s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in ap)}" fill="none" stroke="#dc2626" stroke-width="3.4"/>')
s.append("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#dc2626"/>' for x, y in ap))
# dotted connector through the unaudited actuals
if unaud:
    seq = [aud[-1]] + unaud
    pp = [xy(y) for y in seq]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pp)}" fill="none" stroke="#dc2626" stroke-width="3" stroke-dasharray="2 4" opacity="0.9"/>')
    for y in unaud:
        px, py = xy(y)
        s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.6" fill="#fff" stroke="#dc2626" stroke-width="2.4"/>')
# dashed connector to the projection
if proj:
    seq = [(unaud[-1] if unaud else aud[-1])] + proj
    pp = [xy(y) for y in seq]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pp)}" fill="none" stroke="#dc2626" stroke-width="3" stroke-dasharray="6 4" opacity="0.8"/>')
    for y in proj:
        px, py = xy(y)
        s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.6" fill="#fff" stroke="#dc2626" stroke-width="2.4"/>')
        s.append(f'<text x="{px:.1f}" y="{py-13:.1f}" class="endlab2" fill="#dc2626" text-anchor="middle">FY26 projected</text>')
# callouts
if 2024 in days[IC]:
    x24, y24 = xy(2024)
    s.append(f'<text x="{x24:.1f}" y="{y24-13:.1f}" class="endlab2" fill="#b45309" text-anchor="middle">2024 (CAR, unaudited)</text>')
if 2025 in days[IC] and 2023 in days[IC]:
    x25, y25 = xy(2025)
    s.append(f'<text x="{x25:.1f}" y="{y25+24:.1f}" class="endlab2" fill="#b91c1c" text-anchor="middle" style="font-weight:700">same as 2023 low</text>')
s.append(f'<text x="{X(YEARS.index(aud[-1]))-6:.1f}" y="{Y(days[IC][aud[-1]])-12:.1f}" class="endlab" fill="#dc2626" text-anchor="end" style="font-weight:700">Iowa City</text>')
ay = avg[max(avg)]
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+4:.1f}" class="endlab" fill="#2563eb">Peer average</text>')
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+20:.1f}" class="endlab2" fill="#94a3b8">(large districts)</text>')
s.append('</svg>')
svg = "".join(s)

ic20, ic23 = days[IC][2020], days[IC][2023]
ic24 = days[IC].get(2024)
ic25 = days[IC].get(2025)
ic26 = days[IC].get(2026)
pa23 = peer_avg(2023)
pa25 = peer_avg(2025)
date = datetime.date(2026, 6, 11).strftime("%B %Y")
SITE = "https://michael480th.github.io/ICCSD_Financial_Benchmarking"
PAGE_URL = f"{SITE}/iccsd-operating-cash.html"
IMG_URL = f"{SITE}/iccsd-operating-cash-infographic.png"
SHARE = f"https://www.facebook.com/sharer/sharer.php?u={PAGE_URL}"
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Operating cash trend vs. peers</title>
<meta property="og:type" content="article">
<meta property="og:title" content="Iowa City Schools: about one month of cash on hand">
<meta property="og:description" content="General Fund days-cash-on-hand fell to ~33 days in 2023 — the thinnest of any large Iowa district, vs. ~98 for peers and a 60-day recommended level.">
<meta property="og:image" content="{IMG_URL}">
<meta property="og:url" content="{PAGE_URL}">
<meta name="twitter:card" content="summary_large_image">
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.intro{{border-left:4px solid #2563eb}} .intro p{{margin:7px 0}}
.hero{{margin:0 0 18px}}
.hero img{{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.hero figcaption{{font-size:13.5px;color:var(--mut);margin-top:10px;text-align:center;display:flex;gap:14px;justify-content:center;align-items:center;flex-wrap:wrap}}
.hero a{{color:#2563eb;font-weight:600;text-decoration:none}}
.fb{{display:inline-flex;align-items:center;gap:7px;background:#1877f2;color:#fff;padding:8px 16px;border-radius:8px;font-weight:700;font-size:14px}}
.fb:hover{{background:#0f63d6}} .fb svg{{width:16px;height:16px;fill:#fff}}
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

<figure class="hero">
  <img src="iccsd-operating-cash-infographic.png" alt="Infographic: Iowa City schools have about one month of cash on hand (~33 days in 2023) versus ~98 days at similar districts and a 60-day recommended level.">
  <figcaption>
    <a class="fb" href="{SHARE}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24"><path d="M22 12a10 10 0 10-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.4v7A10 10 0 0022 12z"/></svg>Share on Facebook</a>
    <a href="iccsd-operating-cash-infographic.png" download>⬇ Download image</a>
  </figcaption>
</figure>

<h1>Iowa City Schools: Operating Cash on Hand</h1>
<p class="sub">General Fund <b>days-cash-on-hand</b> — how many days the district could run on its operating cash — vs. size-matched peers, FY2020–FY2026 · {date}</p>

<div class="card intro">
<p><b>What it is:</b> the most direct measure of liquidity — the district's General Fund cash &amp;
investments divided by its average daily spending. It answers "if the money stopped coming in, how many
days could the lights stay on?" Unlike reserves or spending authority, this is <b>actual cash</b>.</p>
<p><b>Why days, not dollars:</b> a big district needs more cash than a small one, so raw dollars aren't
comparable — days-cash normalizes for size. <b>GFOA recommends keeping at least ~60 days.</b></p>
<p><b>About the last three points:</b> FY2024 is the district's <i>unaudited</i> state-filed figure; FY2025
(~{ic25:.0f} days) is an <i>unaudited internal</i> number the COO gave the board in April 2026; and FY2026
(~{ic26:.0f} days, the hollow marker) is a <i>forward projection</i> from PFM's April 28, 2026 update — not a
close. None of FY2024–FY2026 has been audited yet.</p>
</div>

<div class="card">
<div class="legend">
  <span><i style="border-color:#dc2626;border-top-width:4px"></i>Iowa City CSD</span>
  <span><i style="border-color:#2563eb;border-top-style:dashed"></i>Peer average</span>
  <span><i style="border-color:#cbd5e1"></i>Individual peers</span>
  <span><i style="border-color:#16a34a;border-top-style:dashed"></i>GFOA ≈ 60 days</span>
  <span><span style="display:inline-block;width:11px;height:11px;border:2px solid #dc2626;border-radius:50%;background:#fff;vertical-align:middle;margin-right:5px"></span>open marker = not yet audited (FY2024 CAR, FY2025 internal, FY2026 projected)</span>
</div>
{svg}
<p class="take">Iowa City has run <b>below the ~60-day GFOA guideline every year</b>. Its operating cash
fell from ~<b>{ic20:.0f} days in 2020</b> to ~<b>{ic23:.0f} in 2023</b> — the thinnest of any large district,
vs. a peer average near <b>{pa23:.0f}</b>. The state-filed FY2024 figure looked like a rebound (~{ic24:.0f}),
but <b>it didn't stick: the unaudited FY2025 number is back to ~{ic25:.0f} days — the same as the 2023 low</b>,
and FY2026 is projected at just ~{ic26:.0f}. By any honest read, the district has sat <b>near 33 days of cash for
most of the last three years</b>, with one bounce that may be partly an artifact of the very allocation issues
the late audits are now untangling. Peers, meanwhile, held ~<b>{pa25:.0f} days</b>. This is the cash behind the
district's tax-anticipation-warrant and interfund-loan discussions.</p>
</div>

<footer>
<b>Sources.</b> Operating cash = General Fund "cash &amp; investments" from the first fund column of each
district's audited <i>Balance Sheet — Governmental Funds</i> (ACFRs in <code>auditreports/</code>,
FY2020–FY2025). <b>Iowa City</b>: FY2024 from the Certified Annual Report (state-filed, unaudited); <b>FY2025</b>
(~$19.3M / {ic25:.0f} days) from the COO's April 1, 2026 board work-session figure; <b>FY2026</b>
(~$21.4M / {ic26:.0f} days, hollow marker) a projection from PFM's April 28, 2026 update (Option 1). Iowa City's
FY2024–FY2026 audits are all still outstanding (committed complete by May 2027). Days-cash = cash &divide;
(General Fund expenditures / 365). College (Prairie)'s FY2020 balance sheet used an older layout and is omitted.
"Peers" are the 12 districts with 5,000+ students. Built by <code>scripts/extract_audit_cash.py</code> +
<code>scripts/build_operating_cash.py</code> (Iowa City FY2025–26 from <code>data/iccsd-cash-supplemental.csv</code>).
</footer>
</div></body></html>"""

open("iccsd-operating-cash.html", "w").write(DOC)
print(f"Wrote iccsd-operating-cash.html ({len(DOC)//1024} KB)")
print("ICCSD days-cash:", {y: round(days[IC][y]) for y in sorted(days[IC])})
print("Peer avg by year:", {y: round(peer_avg(y)) for y in YEARS if peer_avg(y)})
