#!/usr/bin/env python3
"""
Build the "Does it have a cushion?" page (iccsd-cushion.html) — the merged liquidity story
for Iowa City CSD vs. its size-matched peers (5,000+ students). One page, three complementary
views of the same question ("does the district have a financial safety margin, and is it
eroding?"):

  1. Spending-authority cushion — Unspent Authorized Budget as a % of the maximum authorized
     budget, FY2017-FY2025 (state-computed; exists even where audits are late).
  2. True cash reserves — audited General-Fund solvency ratio (assigned + unassigned fund
     balance as a % of revenue), FY2020-FY2025.
  3. Operating cash — General-Fund days-cash-on-hand, FY2020-FY2026 (the most direct
     liquidity measure; GFOA recommends >= ~60 days).

This supersedes the two standalone pages (iccsd-liquidity-trend.html, iccsd-operating-cash.html),
which remain published as detailed deep-dives under "Other analyses." Self-contained SVG.

Run:  python3 scripts/build_cushion.py   ->  iccsd-cushion.html
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
PEERS = ["Ankeny CSD","Cedar Rapids CSD","College CSD (Prairie)","Davenport CSD",
         "Des Moines Independent CSD","Dubuque CSD","Johnston CSD","Linn-Mar CSD",
         "Pleasant Valley CSD","Waterloo CSD","Waukee CSD","West Des Moines CSD"]


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------- 1. Spending-authority cushion (UAB %), FY2017-2025 ----------
wb = openpyxl.load_workbook("UAB/Unspent Authorized Budget Report.xlsx", data_only=True, read_only=True)
ws = wb["data_UAB"]
uab = {}
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

# ---------- 3. Operating cash -> days-cash, FY2020-2025 ----------
DAYS_YEARS = list(range(2020, 2026))   # end at FY2025 (last actual); FY2026 projection omitted — too uncertain
exp = {}
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    e = num(r["gf_expenditure"])
    if e:
        exp[(r["district"], int(r["fiscal_year"]))] = e
for r in csv.DictReader(open("data/car-fund-balances.csv")):
    if r["district_code"] == "3141" and r["fiscal_year"] == "2024" and r["fund"] == "General":
        exp[(IC, 2024)] = num(r["expenditures"])

days, cash, IC_AUDITED = {}, {}, set()
for r in csv.DictReader(open("data/gf-operating-cash.csv")):
    d, fy, c = r["district"], int(r["fiscal_year"]), num(r["gf_cash_investments"])
    cash.setdefault(d, {})[fy] = c
    e = exp.get((d, fy))
    if c is not None and e:
        days.setdefault(d, {})[fy] = c / (e / 365.0)
    if d == IC and r.get("source") == "audit":
        IC_AUDITED.add(fy)

# Iowa City FY2024-FY2026: the district's own stated General Fund figures (PFM Exhibit 1 /
# COO cash-flow narrative), overriding the CAR-based FY2024. Use the district's published
# days-cash (days_cash) where given, else compute from cash and expenditures.
IC_PROJECTED = set()
for r in csv.DictReader(open("data/iccsd-cash-supplemental.csv")):
    fy = int(r["fiscal_year"])
    if fy > 2025: continue   # FY2026 projection omitted (too uncertain; see note in prose)
    dc = num(r.get("days_cash"))
    if dc is None:
        c, e = num(r["gf_cash_investments"]), num(r["gf_expenditures"])
        dc = c / (e / 365.0) if (c and e) else None
    if dc is not None:
        days.setdefault(IC, {})[fy] = dc
    if r["status"] == "projected":
        IC_PROJECTED.add(fy)


def peer_avg(series, year):
    vals = [series[p][year] for p in PEERS if year in series.get(p, {})]
    return st.mean(vals) if vals else None


# ---------- generic line-chart renderer (UAB + solvency) ----------
def chart(series, years, ymin, ymax, refs, title, ylab, healthy=None):
    W, H = 860, 420
    L, R, T, B = 64, 150, 28, 46
    pw, ph = W - L - R, H - T - B

    def X(i): return L + pw * i / (len(years) - 1)
    def Y(v): return T + ph * (ymax - v) / (ymax - ymin)

    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="{html.escape(title)}">']
    if healthy:
        lo, hi = healthy
        s.append(f'<rect x="{L}" y="{Y(hi):.1f}" width="{pw}" height="{Y(lo)-Y(hi):.1f}" '
                 f'fill="#16a34a" opacity="0.07"/>')
        s.append(f'<text x="{L+6}" y="{Y(hi)+13:.1f}" class="bandlab">healthy range {lo}–{hi}%</text>')
    step = 5
    g = ymin - (ymin % step)
    while g <= ymax:
        yy = Y(g)
        s.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L+pw}" y2="{yy:.1f}" class="grid"/>')
        s.append(f'<text x="{L-8}" y="{yy+4:.1f}" class="ytick">{g:g}%</text>')
        g += step
    for val, lab, cls in refs:
        yy = Y(val)
        s.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L+pw}" y2="{yy:.1f}" class="ref {cls}"/>')
        s.append(f'<text x="{L+pw-4}" y="{yy-5:.1f}" class="reflab {cls}">{html.escape(lab)}</text>')
    for i, y in enumerate(years):
        s.append(f'<text x="{X(i):.1f}" y="{T+ph+22}" class="xtick">{y}</text>')

    def poly(name, cls, width):
        pts = [(X(i), Y(series[name][y])) for i, y in enumerate(years) if y in series.get(name, {})]
        if not pts: return ""
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        out = f'<polyline points="{d}" fill="none" stroke="{cls}" stroke-width="{width}"/>'
        dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{2.6 if width<3 else 3.4}" fill="{cls}"/>' for x, y in pts)
        return out + dots

    for p in PEERS:
        s.append(poly(p, "#cbd5e1", 1.4))
    avg = {y: peer_avg(series, y) for y in years if peer_avg(series, y) is not None}
    pts = [(X(i), Y(avg[y])) for i, y in enumerate(years) if y in avg]
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    s.append(f'<polyline points="{d}" fill="none" stroke="#2563eb" stroke-width="2.6" stroke-dasharray="7 4"/>')
    s.append(poly(IC, "#dc2626", 3.4))
    ys = [y for y in years if y in series.get(IC, {})]
    if ys:
        ly, lx = series[IC][ys[-1]], X(years.index(ys[-1]))
        s.append(f'<text x="{lx+8:.1f}" y="{Y(ly)+4:.1f}" class="endlab" fill="#dc2626" '
                 f'style="font-weight:700">Iowa City</text>')
    la_y = avg[max(avg)]
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(la_y)+4:.1f}" class="endlab" fill="#2563eb">Peer average</text>')
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(la_y)+20:.1f}" class="endlab2" fill="#94a3b8">(other large districts)</text>')
    s.append('</svg>')
    return f'<figure><figcaption><b>{html.escape(title)}</b><span>{html.escape(ylab)}</span></figcaption>{"".join(s)}</figure>'


# ---------- days-cash chart (custom: certainty-coded Iowa City line) ----------
def days_chart():
    W, H = 860, 430
    L, R, T, B = 60, 150, 28, 46
    pw, ph = W - L - R, H - T - B
    YMIN, YMAX = 0, 160
    def X(i): return L + pw * i / (len(DAYS_YEARS) - 1)
    def Y(v): return T + ph * (YMAX - v) / (YMAX - YMIN)
    s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="operating cash trend">']
    for g in range(0, 161, 20):
        s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+pw}" y2="{Y(g):.1f}" class="grid"/>')
        s.append(f'<text x="{L-8}" y="{Y(g)+4:.1f}" class="ytick">{g}</text>')
    s.append(f'<line x1="{L}" y1="{Y(60):.1f}" x2="{L+pw}" y2="{Y(60):.1f}" class="ref60"/>')
    s.append(f'<text x="{L+pw-4}" y="{Y(60)-6:.1f}" class="reflab60">GFOA guideline ≈ 60 days</text>')
    for i, y in enumerate(DAYS_YEARS):
        s.append(f'<text x="{X(i):.1f}" y="{T+ph+22}" class="xtick">{y}</text>')

    def poly(d, color, width):
        pts = [(X(i), Y(days[d][y])) for i, y in enumerate(DAYS_YEARS) if y in days.get(d, {})]
        if not pts: return ""
        line = f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{color}" stroke-width="{width}"/>'
        dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{3.4 if width>2.5 else 2.4}" fill="{color}"/>' for x, y in pts)
        return line + dots

    for p in PEERS:
        s.append(poly(p, "#cbd5e1", 1.4))
    avg = {y: peer_avg(days, y) for y in DAYS_YEARS if peer_avg(days, y) is not None}
    apts = [(X(i), Y(avg[y])) for i, y in enumerate(DAYS_YEARS) if y in avg]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in apts)}" fill="none" stroke="#2563eb" stroke-width="2.6" stroke-dasharray="7 4"/>')
    def xy(y): return X(DAYS_YEARS.index(y)), Y(days[IC][y])
    aud = sorted(y for y in days[IC] if y in IC_AUDITED)
    unaud = sorted(y for y in days[IC] if y not in IC_AUDITED and y not in IC_PROJECTED)
    proj = sorted(y for y in days[IC] if y in IC_PROJECTED)
    ap = [xy(y) for y in aud]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in ap)}" fill="none" stroke="#dc2626" stroke-width="3.4"/>')
    s.append("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#dc2626"/>' for x, y in ap))
    if unaud:
        pp = [xy(y) for y in [aud[-1]] + unaud]
        s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pp)}" fill="none" stroke="#dc2626" stroke-width="3" stroke-dasharray="2 4" opacity="0.9"/>')
        for y in unaud:
            px, py = xy(y)
            s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.6" fill="#fff" stroke="#dc2626" stroke-width="2.4"/>')
    if proj:
        pp = [xy(y) for y in [(unaud[-1] if unaud else aud[-1])] + proj]
        s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pp)}" fill="none" stroke="#dc2626" stroke-width="3" stroke-dasharray="6 4" opacity="0.8"/>')
        for y in proj:
            px, py = xy(y)
            s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.6" fill="#fff" stroke="#dc2626" stroke-width="2.4"/>')
            s.append(f'<text x="{px:.1f}" y="{py-13:.1f}" class="endlab2" fill="#dc2626" text-anchor="middle">FY26 projected</text>')
    if 2024 in days[IC]:
        x24, y24 = xy(2024)
        s.append(f'<text x="{x24:.1f}" y="{y24-13:.1f}" class="endlab2" fill="#b45309" text-anchor="middle">2024 (CAR, unaudited)</text>')
    if 2025 in days[IC] and 2023 in days[IC]:
        x25, y25 = xy(2025)
        s.append(f'<text x="{x25:.1f}" y="{y25+24:.1f}" class="endlab2" fill="#b91c1c" text-anchor="middle" style="font-weight:700">same as 2023 low</text>')
    s.append(f'<text x="{X(DAYS_YEARS.index(aud[-1]))-6:.1f}" y="{Y(days[IC][aud[-1]])-12:.1f}" class="endlab" fill="#dc2626" text-anchor="end" style="font-weight:700">Iowa City</text>')
    ay = avg[max(avg)]
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+4:.1f}" class="endlab" fill="#2563eb">Peer average</text>')
    s.append(f'<text x="{L+pw+8:.1f}" y="{Y(ay)+20:.1f}" class="endlab2" fill="#94a3b8">(large districts)</text>')
    s.append('</svg>')
    return f'<figure><figcaption><b>Operating cash — days-cash-on-hand, FY2020–FY2025</b><span>General Fund cash ÷ average daily spending — higher is more cushion</span></figcaption>{"".join(s)}</figure>'


# ---- numbers for prose ----
ic17, ic_uab25 = uab[IC][2017], uab[IC][2025]
pa17, pa_uab25 = peer_avg(uab, 2017), peer_avg(uab, 2025)
ic_solv20, ic_solv23 = solv[IC][2020], solv[IC][2023]
pa_solv23 = peer_avg(solv, 2023)
icd20, icd23 = days[IC][2020], days[IC][2023]
icd24, icd25 = days[IC].get(2024), days[IC].get(2025)
pad23, pad25 = peer_avg(days, 2023), peer_avg(days, 2025)

chart1 = chart(uab, UAB_YEARS, -8, 35,
               [(0, "0% — negative triggers a state-supervised recovery plan", "danger")],
               "Spending-authority cushion, FY2017–FY2025",
               "Unspent Authorized Budget, as a % of the district's budget — higher is more cushion")
chart2 = chart(solv, SOLV_YEARS, -8, 36, [(0, "0%", "danger")],
               "True cash reserves (audited), FY2020–FY2025",
               "General-fund solvency ratio — reserves as a % of one year's revenue — higher is more cushion",
               healthy=(5, 15))
chart3 = days_chart()

date = datetime.date(2026, 6, 18).strftime("%B %Y")
SITE = "https://michael480th.github.io/ICCSD_Financial_Benchmarking"
PAGE_URL = f"{SITE}/iccsd-cushion.html"
IMG_URL = f"{SITE}/iccsd-operating-cash-infographic.png"
SHARE = f"https://www.facebook.com/sharer/sharer.php?u={PAGE_URL}"

DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Does it have a financial cushion?</title>
<meta property="og:type" content="article">
<meta property="og:title" content="Iowa City Schools: does the district have a financial cushion?">
<meta property="og:description" content="Three ways to measure it — spending room, reserves, and days of cash — all point the same way: Iowa City keeps the thinnest cushion of any large Iowa district, and it has been shrinking.">
<meta property="og:image" content="{IMG_URL}">
<meta property="og:url" content="{PAGE_URL}">
<meta name="twitter:card" content="summary_large_image">
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:30px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px;font-size:16px}}
.hero{{margin:0 0 20px;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.herobar{{background:#0f172a;color:#fff;padding:20px 24px}}
.herobar .kick{{color:#93c5fd;font-weight:700;font-size:12px;letter-spacing:.08em;margin-bottom:6px}}
.herobar h2{{margin:0 0 8px;font-size:25px;line-height:1.15}}
.herobar p{{margin:0;color:#cbd5e1;font-size:14.5px}}
.herostats{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;padding:16px 24px 4px}}
@media(max-width:640px){{.herostats{{grid-template-columns:1fr}}}}
.hs{{border-radius:10px;padding:12px 14px;border:1px solid}}
.hs .hn{{font-size:25px;font-weight:800;line-height:1.1}} .hs .hl{{font-size:12.5px;color:#475569;margin-top:4px}}
.hs.red{{background:#fef2f2;border-color:#fecaca}} .hs.red .hn{{color:#dc2626}}
.hs.blue{{background:#eff6ff;border-color:#bfdbfe}} .hs.blue .hn{{color:#2563eb}}
.hs.green{{background:#f0fdf4;border-color:#bbf7d0}} .hs.green .hn{{color:#16a34a}}
.hero figure{{margin:6px 24px 8px}}
.herofoot{{padding:6px 24px 18px;font-size:13.5px}} .herofoot a{{color:#2563eb;font-weight:600;text-decoration:none}}
.fb{{display:inline-flex;align-items:center;gap:7px;background:#1877f2;color:#fff;padding:8px 16px;border-radius:8px;font-weight:700;font-size:14px}}
.fb:hover{{background:#0f63d6}} .fb svg{{width:16px;height:16px;fill:#fff}}
.intro{{background:#fff;border:1px solid var(--line);border-left:4px solid #2563eb;border-radius:10px;padding:16px 20px;margin-bottom:18px}}
.intro p{{margin:6px 0}} .intro b{{color:var(--ink)}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04);overflow-x:auto}}
.card h3{{margin:0 0 2px;font-size:21px}}
.what,.why{{margin:6px 0;font-size:15px;color:#334155}} .what b,.why b{{color:#0f172a}}
figure{{margin:14px 0 6px}}
figcaption{{font-size:13px;color:var(--mut);margin-bottom:4px}} figcaption b{{color:var(--ink);font-size:15px;display:block}} figcaption span{{font-size:13px}}
.chart{{width:100%;height:auto;display:block}}
.grid{{stroke:#eef2f7;stroke-width:1}}
.ytick{{fill:#94a3b8;font-size:12px;text-anchor:end}} .xtick{{fill:#64748b;font-size:13px;text-anchor:middle}}
.ref.danger{{stroke:#dc2626;stroke-width:1.4;stroke-dasharray:3 3;opacity:.7}}
.reflab.danger{{fill:#dc2626;font-size:11px;text-anchor:end;opacity:.85}}
.ref60{{stroke:#16a34a;stroke-width:1.4;stroke-dasharray:5 4;opacity:.8}} .reflab60{{fill:#16a34a;font-size:11px;text-anchor:end}}
.bandlab{{fill:#16a34a;font-size:11px;opacity:.85}}
.endlab{{font-size:13px}} .endlab2{{font-size:11px}}
.take{{margin:12px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #dc2626;border-radius:6px;padding:10px 14px;color:#1f2937}}
.take b{{color:#0f172a}}
.caution{{margin:12px 0 0;font-size:14.5px;line-height:1.5;background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;border-radius:8px;padding:12px 16px;color:#3f3f46}}
.caution b{{color:#92400e}}
.legend{{font-size:13px;color:var(--mut);margin:6px 2px 0;display:flex;gap:18px;flex-wrap:wrap;align-items:center}}
.legend i{{display:inline-block;width:22px;height:0;border-top-width:3px;border-top-style:solid;vertical-align:middle;margin-right:6px}}
.deep{{font-size:13.5px;color:var(--mut);margin-top:10px}} .deep a{{color:#2563eb;font-weight:600;text-decoration:none}}
footer{{color:var(--mut);font-size:12.5px;margin-top:30px;border-top:1px solid var(--line);padding-top:14px}}
footer a{{color:#2563eb}}
</style></head><body>{nav("cushion")}<div class="wrap">

<section class="hero">
  <div class="herobar">
    <div class="kick">IOWA CITY SCHOOLS · CASH WATCH</div>
    <h2>Our schools have about one month of cash in the bank</h2>
    <p>"Days of cash" is how long a district could keep paying its bills — payroll, heat, buses — if the
    money stopped coming in. It's the school version of a family's emergency savings.</p>
  </div>
  <div class="herostats">
    <div class="hs red"><div class="hn">~{icd25:.0f} days</div><div class="hl">Iowa City in 2025 — back at its 2023 low</div></div>
    <div class="hs blue"><div class="hn">~{pad25:.0f} days</div><div class="hl">Similar-size districts, recent average</div></div>
    <div class="hs green"><div class="hn">60+ days</div><div class="hl">Recommended safety level (about 2 months)</div></div>
  </div>
  {chart3}
  <div class="herofoot"><a class="fb" href="{SHARE}" target="_blank" rel="noopener">↗ Share on Facebook</a></div>
</section>

<h1>Does Iowa City Have a Financial Cushion?</h1>
<p class="sub">Three ways to measure the district's safety margin — spending room, reserves, and days of cash — vs. size-matched peers · {date}</p>

<div class="intro">
<p><b>The question:</b> does Iowa City CSD keep a financial safety margin — and is it shrinking? A district
can run short of cushion in three different ways, so we check all three. <b>All three point the same
direction:</b> Iowa City keeps the thinnest cushion of any large Iowa district, and the gap to its peers
has widened over time.</p>
<p>In each chart, every line is a district. <b style="color:#dc2626">Iowa City is red</b>, the
<b style="color:#2563eb">dashed blue line is the peer average</b>, and the faint gray lines are the other
large districts (5,000+ students).</p>
</div>

<div class="legend">
<span><i style="border-color:#dc2626;border-top-width:4px"></i>Iowa City CSD</span>
<span><i style="border-color:#2563eb;border-top-style:dashed"></i>Peer average (large districts)</span>
<span><i style="border-color:#cbd5e1"></i>Individual peer districts</span>
</div>

<div class="card">
<h3>1. Spending room — the long view (2017–2025)</h3>
<p class="what"><b>What it is:</b> Iowa caps how much a district may spend each year. This shows the unused
"room" left over (its Unspent Authorized Budget) as a share of its budget. It's the single most-watched
measure of an Iowa district's financial health, and it exists for every district every year — even years
where the audit is late — so it gives the full nine-year trend.</p>
<p class="why"><b>Why it matters:</b> when it hits zero or goes negative, the district has overspent its
legal authority — which is unlawful and forces a state-supervised recovery plan.</p>
{chart1}
<p class="take">Iowa City started already thin (<b>{ic17:.1f}%</b> in 2017, about half the peer average of
<b>{pa17:.1f}%</b>) and kept drawing it down — touching <b>0.1% in 2022</b> and going <b>negative
(−1.2%) in 2023</b>, the level that triggers state review. Over the same nine years the peer average
<b>rose</b>, from <b>{pa17:.1f}% to {pa_uab25:.1f}%</b>. By 2025 Iowa City's cushion (<b>{ic_uab25:.1f}%</b>)
was roughly a <b>seventh</b> of the peer average.</p>
</div>

<div class="card">
<h3>2. Reserves in the bank — the audited view (2020–2025)</h3>
<p class="what"><b>What it is:</b> the actual rainy-day cushion — the district's general-fund reserves
measured against one year of revenue (the "solvency ratio"), straight from the audited financial reports.
In Iowa, <b>5–15% is considered healthy</b>. It only exists for years a district has finished its audit —
which is why Iowa City's line stops at 2023.</p>
<p class="why"><b>Why it matters:</b> reserves are what absorb a bad budget year, a late state payment, or
an emergency repair. A thin cushion means little margin for error.</p>
{chart2}
<p class="take">Same story: Iowa City sat at <b>{ic_solv20:.1f}% in 2020</b> and slipped to
<b>{ic_solv23:.1f}% by 2023</b> — the thinnest of any large district that has filed, below both the 5–15%
healthy range and the peer average (~<b>{pa_solv23:.0f}%</b> in 2023). The line stops there for a reason:
<b>Iowa City's 2024 and 2025 audits still aren't filed</b>, so the most recent verified reserve position is
three years old.</p>
</div>

<div class="card">
<h3>3. Cash on hand — the most direct test (2020–2025)</h3>
<p class="what"><b>What it is:</b> the district's General Fund cash &amp; investments divided by its average
daily spending — "if the money stopped coming in, how many days could the lights stay on?" Unlike the first
two, this is <b>actual cash</b>. <b>GFOA recommends keeping at least ~60 days.</b></p>
<p class="why"><b>Why it matters:</b> it's the cash behind the district's tax-anticipation-warrant and
interfund-loan discussions — the most concrete sign of how tight things are. <i>(The days-cash chart is at
the top of this page.)</i></p>
<p class="take">Iowa City has run <b>below the ~60-day guideline every year</b>, falling from ~<b>{icd20:.0f}
days in 2020</b> to ~<b>{icd23:.0f} in 2023</b> — the thinnest of any large district, vs. a peer average near
<b>{pad23:.0f}</b>. FY2024's unaudited actual ticked up to ~{icd24:.0f}, but it didn't hold: <b>FY2025 is back
to ~{icd25:.0f} days — the same as the 2023 low</b>, while peers held ~<b>{pad25:.0f}</b>. FY2024 and FY2025 are
the district's own unaudited figures (open markers).</p>
<p class="caution">Looking ahead, the district's <b>FY2026</b> cash position is still uncertain and depends on planned
short-term borrowing (a revenue-anticipation warrant and an interfund loan), so it isn't charted here. The district's
own projections for it range widely — roughly 7 days of operating cash before that borrowing, versus ~37 days counting
it — which is why we show actuals only, through FY2025.</p>
<p class="deep">Want the credit-rating view? See <a href="liquidity-lenses.html">Three liquidity lenses</a>
(reserves, net cash, and days side by side — how the rating agencies score it), and the district's own intuitive
<a href="iccsd-net-cash-ratio.html">Day's Net Cash Ratio</a> (its internal KPI, computed across all peers
back to 2015 against a 90–120 day target), plus the deep-dive
<a href="iccsd-liquidity-trend.html">reserves trend</a> and
<a href="iccsd-operating-cash.html">operating-cash</a> pages under
<a href="other-analyses.html">Other analyses</a>.</p>
</div>

<footer>
<b>Sources.</b> <b>Spending room:</b> Iowa Department of Management <i>Unspent Authorized Budget Report</i>
(state-computed, FY2017–FY2025). <b>Reserves:</b> each district's audited ACFR (FY2020–FY2025); solvency
ratio = assigned + unassigned general-fund balance ÷ general-fund revenue. <b>Cash:</b> General Fund "cash
&amp; investments" from each district's audited Balance Sheet — Governmental Funds (FY2020–FY2025). Iowa
City FY2024 and FY2025 are the district's own stated General Fund figures (no audit filed): FY2024 (~$25.9M) and
FY2025 (~$19.4M) from PFM's Exhibit 1 (unaudited actual). FY2026 is omitted as too uncertain (it depends on planned
short-term borrowing — see the note above). Days-cash = cash ÷ (general-fund expenditures / 365). Iowa City's FY2024
and FY2025 audits are both still outstanding. <b>Peers</b> are the 12 districts with 5,000+ students. Figures trace to official
filings; nothing is estimated to fill gaps. Built by <code>scripts/build_cushion.py</code>.
</footer>
</div></body></html>"""

open("iccsd-cushion.html", "w").write(DOC)
print(f"Wrote iccsd-cushion.html ({len(DOC)//1024} KB)")
print(f"UAB: ICCSD {ic17:.1f}->{ic_uab25:.1f}; peer {pa17:.1f}->{pa_uab25:.1f}")
print(f"Solv: ICCSD {ic_solv20:.1f}->{ic_solv23:.1f}; peer23 {pa_solv23:.1f}")
print(f"Days: ICCSD {icd20:.0f}->{icd23:.0f} (24={icd24:.0f},25={icd25:.0f}); peer23 {pad23:.0f}")
