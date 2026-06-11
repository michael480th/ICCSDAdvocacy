#!/usr/bin/env python3
"""
Build a one-page, social-media infographic (portrait, ~1080x1350) on Iowa City CSD's operating
cash vs. peers vs. the GFOA safety guideline — plain-language, for a non-technical audience.
Renders iccsd-operating-cash-infographic.html (screenshot it to a PNG for Facebook).
"""
import csv, statistics as st, datetime

IC = "Iowa City CSD"
PEERS = ["Ankeny CSD", "Cedar Rapids CSD", "College CSD (Prairie)", "Davenport CSD",
         "Des Moines Independent CSD", "Dubuque CSD", "Johnston CSD", "Linn-Mar CSD",
         "Pleasant Valley CSD", "Waterloo CSD", "Waukee CSD", "West Des Moines CSD"]
YEARS = list(range(2020, 2025))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


exp = {}
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    e = num(r["gf_expenditure"])
    if e:
        exp[(r["district"], int(r["fiscal_year"]))] = e
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["district_code"] == "3141" and r["fiscal_year"] == "2024" and r["fund"] == "General":
        exp[(IC, 2024)] = num(r["expenditures"])

days = {}
for r in csv.DictReader(open("data/gf-operating-cash.csv")):
    d, fy, c = r["district"], int(r["fiscal_year"]), num(r["gf_cash_investments"])
    e = exp.get((d, fy))
    if c is not None and e:
        days.setdefault(d, {})[fy] = c / (e / 365.0)


def pavg(y):
    v = [days[p][y] for p in PEERS if y in days.get(p, {})]
    return st.mean(v) if v else None


ic = {y: days[IC][y] for y in YEARS if y in days[IC]}
pa = {y: pavg(y) for y in YEARS if pavg(y) is not None}

# ---- chart ----
W, H = 1000, 470
L, Rm, T, B = 56, 120, 30, 50
pw, ph = W - L - Rm, H - T - B
YMAX = 110
def X(i): return L + pw * i / (len(YEARS) - 1)
def Y(v): return T + ph * (YMAX - v) / YMAX

s = [f'<svg viewBox="0 0 {W} {H}" width="100%">']
# zones: safe (>=60) green tint, thin (<60) red tint
s.append(f'<rect x="{L}" y="{T}" width="{pw}" height="{Y(60)-T:.1f}" fill="#16a34a" opacity="0.08"/>')
s.append(f'<rect x="{L}" y="{Y(60):.1f}" width="{pw}" height="{T+ph-Y(60):.1f}" fill="#dc2626" opacity="0.07"/>')
s.append(f'<text x="{L+10}" y="{T+22}" font-size="15" fill="#15803d" font-weight="700">SAFE ZONE — healthy cushion</text>')
s.append(f'<text x="{L+10}" y="{T+ph-12}" font-size="15" fill="#b91c1c" font-weight="700">THIN — little margin for error</text>')
for g in range(0, 111, 20):
    s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+pw}" y2="{Y(g):.1f}" stroke="#e8edf3"/>')
    s.append(f'<text x="{L-10}" y="{Y(g)+5:.1f}" font-size="13" fill="#94a3b8" text-anchor="end">{g}</text>')
# GFOA 60 line
s.append(f'<line x1="{L}" y1="{Y(60):.1f}" x2="{L+pw}" y2="{Y(60):.1f}" stroke="#16a34a" stroke-width="2.5" stroke-dasharray="8 5"/>')
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(60)+5:.1f}" font-size="15" fill="#15803d" font-weight="800">60 days</text>')
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(60)+23:.1f}" font-size="12" fill="#16a34a">recommended</text>')
for i, y in enumerate(YEARS):
    s.append(f'<text x="{X(i):.1f}" y="{T+ph+28}" font-size="15" fill="#475569" text-anchor="middle" font-weight="600">{y}</text>')


def line(series, color, w, dash=""):
    pts = [(X(i), Y(series[y])) for i, y in enumerate(YEARS) if y in series]
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    out = f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{w}" {("stroke-dasharray="+chr(34)+dash+chr(34)) if dash else ""} stroke-linejoin="round"/>'
    out += "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6 if w>4 else 4}" fill="{color}"/>' for x, y in pts)
    return out


s.append(line(pa, "#2563eb", 4))
s.append(line(ic, "#dc2626", 6))
# peer label
py = pa[max(pa)]
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(py)+5:.1f}" font-size="16" fill="#2563eb" font-weight="800">Similar</text>')
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(py)+24:.1f}" font-size="16" fill="#2563eb" font-weight="800">districts</text>')
# ICCSD label + trough annotation
iy = ic[max(ic)]
s.append(f'<text x="{L+pw+8:.1f}" y="{Y(iy)+5:.1f}" font-size="16" fill="#dc2626" font-weight="800">Iowa City</text>')
tx, ty = X(YEARS.index(2023)), Y(ic[2023])
s.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="9" fill="none" stroke="#dc2626" stroke-width="2.5"/>')
s.append(f'<text x="{tx:.1f}" y="{ty+34:.1f}" font-size="17" fill="#dc2626" font-weight="800" text-anchor="middle">just {ic[2023]:.0f} days</text>')
s.append('</svg>')
svg = "".join(s)

ic20, ic23 = ic[2020], ic[2023]
pa23 = pa[2023]
date = datetime.date(2026, 6, 11).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font:18px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#fff}}
.card{{width:1080px;background:#fff}}
.hd{{background:#0f172a;color:#fff;padding:34px 44px 30px}}
.eyebrow{{color:#7dd3fc;font-size:16px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px}}
h1{{font-size:46px;line-height:1.12;font-weight:850;letter-spacing:-.5px}}
.hd p{{margin-top:14px;font-size:21px;color:#cbd5e1;max-width:880px}}
.stats{{display:flex;gap:18px;padding:30px 44px 6px}}
.stat{{flex:1;border-radius:16px;padding:20px 22px;border:2px solid}}
.stat .n{{font-size:44px;font-weight:850;line-height:1}}
.stat .l{{font-size:16px;margin-top:8px;font-weight:600;color:#334155}}
.s-red{{background:#fef2f2;border-color:#fecaca}} .s-red .n{{color:#dc2626}}
.s-blue{{background:#eff6ff;border-color:#bfdbfe}} .s-blue .n{{color:#2563eb}}
.s-green{{background:#f0fdf4;border-color:#bbf7d0}} .s-green .n{{color:#16a34a}}
.chartwrap{{padding:18px 40px 6px}}
.chartwrap h2{{font-size:23px;padding:0 4px 6px;color:#0f172a}}
.explain{{margin:14px 44px 0;background:#f8fafc;border:1px solid #e2e8f0;border-left:6px solid #dc2626;border-radius:14px;padding:22px 26px}}
.explain h3{{font-size:24px;color:#0f172a;margin-bottom:8px}}
.explain p{{font-size:20px;color:#1f2937}}
.explain b{{color:#0f172a}}
.foot{{display:flex;justify-content:space-between;align-items:flex-end;padding:24px 44px 34px;color:#64748b;font-size:14px}}
.foot b{{color:#334155}}
</style></head><body>
<div class="card">
  <div class="hd">
    <div class="eyebrow">Iowa City Schools · Cash Watch</div>
    <h1>Our schools have about<br>one month of cash in the bank</h1>
    <p>"Days of cash" is how long a district could keep paying its bills — payroll, heat, buses — if the money stopped coming in. It's the school version of a family's emergency savings.</p>
  </div>

  <div class="stats">
    <div class="stat s-red"><div class="n">~{ic23:.0f} days</div><div class="l">Iowa City CSD (2023) — the thinnest of any large Iowa district</div></div>
    <div class="stat s-blue"><div class="n">~{pa23:.0f} days</div><div class="l">Similar-size districts, on average</div></div>
    <div class="stat s-green"><div class="n">60+ days</div><div class="l">Recommended safety level (about 2 months)</div></div>
  </div>

  <div class="chartwrap">
    <h2>Days of cash on hand — Iowa City vs. peers, 2020–2024</h2>
    {svg}
  </div>

  <div class="explain">
    <h3>What's happening</h3>
    <p>Iowa City's cash cushion <b>shrank from about {ic20:.0f} days in 2020 to just {ic23:.0f} days in 2023</b> — while
    comparable districts kept roughly <b>{pa23:.0f} days</b> and the recommended level is <b>60+</b>. A cushion this thin
    means a single bad month, a late state payment, or a surprise repair can become a real cash crunch.</p>
  </div>

  <div class="foot">
    <div>Source: audited district financial reports (General Fund cash &divide; daily spending),<br>FY2020–FY2024. 2024 from the state-filed report; Iowa City's 2024 audit isn't finished.</div>
    <div style="text-align:right"><b>Unofficial community analysis</b><br>Not official district data · {date}</div>
  </div>
</div>
</body></html>"""

open("iccsd-operating-cash-infographic.html", "w").write(DOC)
print("Wrote iccsd-operating-cash-infographic.html")
print("ICCSD:", {y: round(v) for y, v in ic.items()}, "PeerAvg:", {y: round(v) for y, v in pa.items()})
