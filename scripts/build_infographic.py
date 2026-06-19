#!/usr/bin/env python3
"""
Build one-page, social-media infographics on Iowa City CSD's operating cash vs. peers vs. the
GFOA safety guideline — plain-language, for a non-technical audience. Produces two layouts:
  - portrait 1080x1350  -> iccsd-operating-cash-infographic.html / .png
  - square   1080x1080  -> iccsd-operating-cash-infographic-square.html / .png
(Screenshot the HTML to the PNG; the .png files are what you post.)
"""
import csv, statistics as st, datetime

IC = "Iowa City CSD"
PEERS = ["Ankeny CSD", "Cedar Rapids CSD", "College CSD (Prairie)", "Davenport CSD",
         "Des Moines Independent CSD", "Dubuque CSD", "Johnston CSD", "Linn-Mar CSD",
         "Pleasant Valley CSD", "Waterloo CSD", "Waukee CSD", "West Des Moines CSD"]
YEARS = list(range(2020, 2026))   # end at FY2025; FY2026 projection omitted (too uncertain)


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
IC_AUDITED = set()
for r in csv.DictReader(open("data/gf-operating-cash.csv")):
    d, fy, c = r["district"], int(r["fiscal_year"]), num(r["gf_cash_investments"])
    e = exp.get((d, fy))
    if c is not None and e:
        days.setdefault(d, {})[fy] = c / (e / 365.0)
    if d == IC and r.get("source") == "audit":
        IC_AUDITED.add(fy)

IC_PROJECTED = set()
for r in csv.DictReader(open("data/iccsd-cash-supplemental.csv")):
    fy, c, e = int(r["fiscal_year"]), num(r["gf_cash_investments"]), num(r["gf_expenditures"])
    if fy > 2025: continue   # FY2026 projection omitted
    if c and e:
        days.setdefault(IC, {})[fy] = c / (e / 365.0)
    if r["status"] == "projected":
        IC_PROJECTED.add(fy)


def pavg(y):
    v = [days[p][y] for p in PEERS if y in days.get(p, {})]
    return st.mean(v) if v else None


ic = {y: days[IC][y] for y in YEARS if y in days[IC]}
pa = {y: pavg(y) for y in YEARS if pavg(y) is not None}
ic20, ic23 = ic[2020], ic[2023]
ic24, ic25 = ic.get(2024), ic.get(2025)
pa23 = pa[2023]
date = datetime.date(2026, 6, 11).strftime("%B %Y")


def chart(W, H, fs=1.0):
    L, Rm, T, B = 56, 124, 30, 50
    pw, ph = W - L - Rm, H - T - B
    YMAX = 110
    def X(i): return L + pw * i / (len(YEARS) - 1)
    def Y(v): return T + ph * (YMAX - v) / YMAX
    z = lambda px: round(px * fs, 1)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%">']
    s.append(f'<rect x="{L}" y="{T}" width="{pw}" height="{Y(60)-T:.1f}" fill="#16a34a" opacity="0.08"/>')
    s.append(f'<rect x="{L}" y="{Y(60):.1f}" width="{pw}" height="{T+ph-Y(60):.1f}" fill="#dc2626" opacity="0.07"/>')
    s.append(f'<text x="{L+10}" y="{T+22}" font-size="{z(15)}" fill="#15803d" font-weight="700">SAFE ZONE — healthy cushion</text>')
    s.append(f'<text x="{L+10}" y="{T+ph-12}" font-size="{z(15)}" fill="#b91c1c" font-weight="700">THIN — little margin for error</text>')
    for g in range(0, 111, 20):
        s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+pw}" y2="{Y(g):.1f}" stroke="#e8edf3"/>')
        s.append(f'<text x="{L-10}" y="{Y(g)+5:.1f}" font-size="{z(13)}" fill="#94a3b8" text-anchor="end">{g}</text>')
    s.append(f'<line x1="{L}" y1="{Y(60):.1f}" x2="{L+pw}" y2="{Y(60):.1f}" stroke="#16a34a" stroke-width="2.5" stroke-dasharray="8 5"/>')
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(60)+5:.1f}" font-size="{z(15)}" fill="#15803d" font-weight="800">60 days</text>')
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(60)+22:.1f}" font-size="{z(12)}" fill="#16a34a">recommended</text>')
    for i, y in enumerate(YEARS):
        s.append(f'<text x="{X(i):.1f}" y="{T+ph+28}" font-size="{z(15)}" fill="#475569" text-anchor="middle" font-weight="600">{y}</text>')

    def linef(series, color, w):
        pts = [(X(i), Y(series[y])) for i, y in enumerate(YEARS) if y in series]
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        out = f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round"/>'
        out += "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6 if w>4 else 4}" fill="{color}"/>' for x, y in pts)
        return out
    s.append(linef(pa, "#2563eb", 4))
    # Iowa City by certainty: solid+filled = audited (<=2023); dotted+hollow = unaudited
    # actuals (FY24 CAR, FY25 internal); dashed+hollow = projection (FY26).
    def xy(y): return X(YEARS.index(y)), Y(ic[y])
    aud = sorted(y for y in ic if y in IC_AUDITED)
    unaud = sorted(y for y in ic if y not in IC_AUDITED and y not in IC_PROJECTED)
    prj = sorted(y for y in ic if y in IC_PROJECTED)
    ap = [xy(y) for y in aud]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in ap)}" fill="none" stroke="#dc2626" stroke-width="6" stroke-linejoin="round"/>')
    s.append("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#dc2626"/>' for x, y in ap))
    if unaud:
        pp = [xy(y) for y in [aud[-1]] + unaud]
        s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pp)}" fill="none" stroke="#dc2626" stroke-width="5" stroke-dasharray="2 5" opacity="0.9"/>')
        s.append("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#fff" stroke="#dc2626" stroke-width="3"/>' for x, y in [xy(y) for y in unaud]))
    if prj:
        pp = [xy(y) for y in [(unaud[-1] if unaud else aud[-1])] + prj]
        s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pp)}" fill="none" stroke="#dc2626" stroke-width="5" stroke-dasharray="7 5" opacity="0.85"/>')
        for y in prj:
            px, py2 = xy(y)
            s.append(f'<circle cx="{px:.1f}" cy="{py2:.1f}" r="7" fill="#fff" stroke="#dc2626" stroke-width="3"/>')
            s.append(f'<text x="{px:.1f}" y="{py2-16:.1f}" font-size="{z(13)}" fill="#dc2626" font-weight="700" text-anchor="middle">FY26 proj.</text>')
    py = pa[max(pa)]
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(py)+1:.1f}" font-size="{z(16)}" fill="#2563eb" font-weight="800">Similar</text>')
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(py)+19:.1f}" font-size="{z(16)}" fill="#2563eb" font-weight="800">districts</text>')
    s.append(f'<text x="{X(YEARS.index(aud[-1]))-10:.1f}" y="{Y(ic[aud[-1]])-16:.1f}" font-size="{z(16)}" fill="#dc2626" font-weight="800" text-anchor="end">Iowa City</text>')
    tx, ty = xy(2025)
    s.append(f'<text x="{tx:.1f}" y="{ty+30:.1f}" font-size="{z(15)}" fill="#dc2626" font-weight="800" text-anchor="middle">still ~{ic[2025]:.0f} days</text>')
    s.append(f'<text x="{L+pw/2:.1f}" y="{T+ph+46}" font-size="{z(13)}" fill="#94a3b8" text-anchor="middle">○ open marker = not yet audited (2024 CAR · 2025 internal)</text>')
    s.append('</svg>')
    return "".join(s)


COMMON = """
*{box-sizing:border-box;margin:0;padding:0}
body{font:18px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#fff}
.eyebrow{color:#7dd3fc;font-weight:800;letter-spacing:.12em;text-transform:uppercase}
.hd{background:#0f172a;color:#fff}
.stat{flex:1;border-radius:16px;border:2px solid}
.stat .n{font-weight:850;line-height:1} .stat .l{font-weight:600;color:#334155}
.s-red{background:#fef2f2;border-color:#fecaca}.s-red .n{color:#dc2626}
.s-blue{background:#eff6ff;border-color:#bfdbfe}.s-blue .n{color:#2563eb}
.s-green{background:#f0fdf4;border-color:#bbf7d0}.s-green .n{color:#16a34a}
.explain{background:#f8fafc;border:1px solid #e2e8f0;border-left:6px solid #dc2626;border-radius:14px}
.explain b{color:#0f172a}
.foot{display:flex;justify-content:space-between;align-items:flex-end;color:#64748b}
.foot b{color:#334155}
"""


def portrait():
    css = COMMON + """
    .card{width:1080px}
    .hd{padding:34px 44px 30px}
    .eyebrow{font-size:16px;margin-bottom:10px}
    h1{font-size:46px;line-height:1.12;font-weight:850;letter-spacing:-.5px}
    .hd .sub{margin-top:14px;font-size:21px;color:#cbd5e1;max-width:880px}
    .stats{display:flex;gap:18px;padding:30px 44px 6px}
    .stat{padding:20px 22px} .stat .n{font-size:44px} .stat .l{font-size:16px;margin-top:8px}
    .chartwrap{padding:18px 40px 6px} .chartwrap h2{font-size:23px;padding:0 4px 6px;color:#0f172a}
    .explain{margin:14px 44px 0;padding:22px 26px} .explain h3{font-size:24px;color:#0f172a;margin-bottom:8px} .explain p{font-size:20px;color:#1f2937}
    .foot{padding:24px 44px 34px;font-size:14px}
    """
    body = f"""<div class="card">
  <div class="hd"><div class="eyebrow">Iowa City Schools · Cash Watch</div>
    <h1>Our schools have about<br>one month of cash in the bank</h1>
    <p class="sub">"Days of cash" is how long a district could keep paying its bills — payroll, heat, buses — if the money stopped coming in. It's the school version of a family's emergency savings.</p></div>
  <div class="stats">
    <div class="stat s-red"><div class="n">~{ic25:.0f} days</div><div class="l">Iowa City in 2025 — right back at its 2023 low</div></div>
    <div class="stat s-blue"><div class="n">~{pa23:.0f} days</div><div class="l">Similar-size districts, on average</div></div>
    <div class="stat s-green"><div class="n">60+ days</div><div class="l">Recommended safety level (about 2 months)</div></div></div>
  <div class="chartwrap"><h2>Days of cash on hand — Iowa City vs. peers, 2020–2025</h2>{chart(1000,470)}</div>
  <div class="explain"><h3>What's happening</h3>
    <p>Iowa City's cash cushion <b>fell from about {ic20:.0f} days in 2020 to ~{ic23:.0f} in 2023</b>. The state-filed 2024 number looked like a rebound — but <b>it didn't stick: 2025 is back to ~{ic25:.0f} days</b>, the same low. The district has sat near a month of cash for three straight years, while peers held ~<b>{pa23:.0f}</b>. A cushion this thin means a bad month or a late state payment can become a real cash crunch.</p></div>
  <div class="foot"><div>Source: audited reports (General Fund cash &divide; daily spending), FY2020–FY2023. Iowa City 2024 state-filed,<br>2025 unaudited (COO, Apr 2026); those audits aren't finished.</div>
    <div style="text-align:right"><b>Unofficial community analysis</b><br>Not official district data · {date}</div></div>
</div>"""
    return css, body


def square():
    css = COMMON + """
    .card{width:1080px;height:1080px;display:flex;flex-direction:column}
    .hd{padding:26px 40px 22px}
    .eyebrow{font-size:15px;margin-bottom:8px}
    h1{font-size:40px;line-height:1.1;font-weight:850;letter-spacing:-.5px}
    .hd .sub{margin-top:10px;font-size:18px;color:#cbd5e1}
    .stats{display:flex;gap:14px;padding:18px 40px 2px}
    .stat{padding:14px 16px} .stat .n{font-size:34px} .stat .l{font-size:13.5px;margin-top:6px}
    .chartwrap{padding:8px 36px 0;flex:1} .chartwrap h2{font-size:20px;padding:6px 4px 2px;color:#0f172a}
    .explain{margin:8px 40px 0;padding:16px 22px} .explain p{font-size:18px;color:#1f2937}
    .foot{padding:14px 40px 22px;font-size:12.5px;margin-top:auto}
    """
    body = f"""<div class="card">
  <div class="hd"><div class="eyebrow">Iowa City Schools · Cash Watch</div>
    <h1>About one month of cash in the bank</h1>
    <p class="sub">"Days of cash" = how long the district could keep paying its bills if the money stopped — its emergency savings.</p></div>
  <div class="stats">
    <div class="stat s-red"><div class="n">~{ic25:.0f} days</div><div class="l">Iowa City (2025) — back at its 2023 low</div></div>
    <div class="stat s-blue"><div class="n">~{pa23:.0f} days</div><div class="l">Similar districts, on average</div></div>
    <div class="stat s-green"><div class="n">60+ days</div><div class="l">Recommended (about 2 months)</div></div></div>
  <div class="chartwrap"><h2>Days of cash on hand — Iowa City vs. peers, 2020–2025</h2>{chart(1000,400)}</div>
  <div class="explain"><p>Iowa City's cash cushion <b>fell from ~{ic20:.0f} days (2020) to ~{ic23:.0f} (2023)</b>. The 2024 rebound <b>didn't stick — 2025 is back to ~{ic25:.0f} days</b>, while peers kept ~<b>{pa23:.0f}</b>. A cushion this thin means a bad month or a late state payment can become a real cash crunch.</p></div>
  <div class="foot"><div>Source: audited reports, FY2020–23 (GF cash &divide; daily spend). IC 2024 state-filed,<br>2025 unaudited — audits not yet final.</div>
    <div style="text-align:right"><b>Unofficial community analysis</b><br>{date}</div></div>
</div>"""
    return css, body


for name, builder in [("iccsd-operating-cash-infographic", portrait),
                      ("iccsd-operating-cash-infographic-square", square)]:
    css, body = builder()
    doc = f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<style>{css}</style></head><body>\n{body}\n</body></html>'
    open(name + ".html", "w").write(doc)
    print("Wrote", name + ".html")
