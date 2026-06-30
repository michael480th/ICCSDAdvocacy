#!/usr/bin/env python3
"""Build iccsd-enrollment-permits.html.

Brings the corridor building-permit time series into the enrollment forecast as a
leading indicator. Single-family permits lead the kindergarten share by about five
years. The data confirms the Tiffin geographic-capture story and signals that the
share is stabilizing, which supports the Baseline over the Low scenario.

Data: Building Permits/Building Permits (Tier 1)/fact_units_ts.csv
  (Census Building Permits Survey, place-level, plus Johnson County unincorporated).

Honest limit: these are whole-city totals. North Liberty and Coralville straddle the
ICCSD/CCA line and Tiffin is mostly CCA, so this is a corridor-level signal, not an
ICCSD-precise input. The Tier 2 address-level spatial join was not done.

Run: python3 scripts/build_permit_indicator.py
"""
import csv, os, statistics as stat

OUT = "iccsd-enrollment-permits.html"
CSV = "Building Permits/Building Permits (Tier 1)/fact_units_ts.csv"

# ── Load single-family (1-unit) permits by jurisdiction and year ─────────────
rows = list(csv.DictReader(open(CSV)))
YEARS = list(range(2010, 2026))
JUR = ['Iowa City', 'Coralville', 'North Liberty', 'Tiffin', 'Johnson Co. (uninc.)']


def sf(juris, yr):
    return sum(int(r['units']) for r in rows
               if r['jurisdiction'] == juris and r['structure_bucket'] == '1-unit'
               and int(r['period']) == yr)


SF = {j: {y: sf(j, y) for y in YEARS} for j in JUR}
# ICCSD-leaning corridor = everything except Tiffin (Tiffin is mostly CCA)
ICCSD_SF = {y: SF['Iowa City'][y] + SF['Coralville'][y] + SF['North Liberty'][y]
            + SF['Johnson Co. (uninc.)'][y] for y in YEARS}
TIFFIN_SF = {y: SF['Tiffin'][y] for y in YEARS}
# ICCSD share of corridor single-family building
ICCSD_SHARE_SF = {y: 100 * ICCSD_SF[y] / (ICCSD_SF[y] + TIFFIN_SF[y]) for y in YEARS}

# ── K-entry share (from the forecast model) ──────────────────────────────────
BIRTHS = {2011: 1548, 2012: 1552, 2013: 1523, 2014: 1495, 2015: 1462, 2016: 1438,
          2017: 1421, 2018: 1407, 2019: 1385, 2020: 1356}
KENR = {2016: 1125, 2017: 1146, 2018: 1157, 2019: 1101, 2020: 1027, 2021: 1096,
        2022: 1035, 2023: 998, 2024: 992, 2025: 987}
COVID_K = {2020, 2021}
KSHARE = {y: KENR[y] / BIRTHS[y - 5] for y in KENR}


def corr(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    sx = (sum((x - mx) ** 2 for x in xs)) ** .5
    sy = (sum((y - my) ** 2 for y in ys)) ** .5
    return cov / (sx * sy) if sx and sy else 0


LAG = 5
pairs = [(ICCSD_SF[y - LAG], KSHARE[y]) for y in sorted(KSHARE)
         if (y - LAG) in ICCSD_SF and y not in COVID_K]
CORR5 = corr([p[0] for p in pairs], [p[1] for p in pairs])
pairs4 = [(ICCSD_SF[y - 4], KSHARE[y]) for y in sorted(KSHARE)
          if (y - 4) in ICCSD_SF and y not in COVID_K]
CORR4 = corr([p[0] for p in pairs4], [p[1] for p in pairs4])

# Recent permit signal feeding the 2026-2030 K window (permits 2020-2025)
RECENT = [ICCSD_SF[y] for y in range(2020, 2026)]
TROUGH = [ICCSD_SF[y] for y in range(2018, 2021)]
FONT = '-apple-system,Segoe UI,Roboto,sans-serif'


def line_chart_cities():
    W, H, pl, pr, pt, pb = 760, 280, 44, 110, 18, 36
    pw, ph = W - pl - pr, H - pt - pb
    ymax = 300
    series = [('Iowa City', '#1e3a5f'), ('North Liberty', '#2563eb'),
              ('Coralville', '#0891b2'), ('Tiffin', '#dc2626')]

    def X(y): return pl + pw * (y - YEARS[0]) / (YEARS[-1] - YEARS[0])
    def Y(v): return pt + ph * (ymax - v) / ymax
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in range(0, 301, 100):
        gy = Y(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="10.5" fill="#94a3b8">{gv}</text>')
    for y in YEARS:
        if y % 2 == 0:
            p.append(f'<text x="{X(y):.1f}" y="{H-pb+16}" text-anchor="middle" font-size="10" fill="#64748b">{str(y)[2:]}</text>')
    for name, col in series:
        pts = " ".join(f"{X(y):.1f},{Y(SF[name][y]):.1f}" for y in YEARS)
        dash = ' stroke-dasharray="5 3"' if name == 'Tiffin' else ''
        p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.5"{dash}/>')
        ly = Y(SF[name][YEARS[-1]])
        p.append(f'<text x="{W-pr+6}" y="{ly+4:.1f}" font-size="10.5" font-weight="700" fill="{col}">{name}</text>')
    p.append('</svg>')
    return "".join(p)


def share_sf_chart():
    W, H, pl, pr, pt, pb = 760, 260, 44, 20, 18, 36
    pw, ph = W - pl - pr, H - pt - pb
    ymin, ymax = 55, 100

    def X(y): return pl + pw * (y - YEARS[0]) / (YEARS[-1] - YEARS[0])
    def Y(v): return pt + ph * (ymax - v) / (ymax - ymin)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in range(60, 101, 10):
        gy = Y(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="10.5" fill="#94a3b8">{gv}%</text>')
    for y in YEARS:
        if y % 2 == 0:
            p.append(f'<text x="{X(y):.1f}" y="{H-pb+16}" text-anchor="middle" font-size="10" fill="#64748b">{str(y)[2:]}</text>')
    # shade the capture trough 2017-2021
    p.append(f'<rect x="{X(2017):.1f}" y="{pt}" width="{X(2021)-X(2017):.1f}" height="{ph}" fill="#fee2e2" fill-opacity="0.5"/>')
    p.append(f'<text x="{(X(2017)+X(2021))/2:.1f}" y="{pt+12}" text-anchor="middle" font-size="9.5" fill="#b91c1c">Tiffin capture surge</text>')
    pts = " ".join(f"{X(y):.1f},{Y(ICCSD_SHARE_SF[y]):.1f}" for y in YEARS)
    p.append(f'<polyline points="{pts}" fill="none" stroke="#1e3a5f" stroke-width="2.8"/>')
    for y in YEARS:
        p.append(f'<circle cx="{X(y):.1f}" cy="{Y(ICCSD_SHARE_SF[y]):.1f}" r="3" fill="#1e3a5f"/>')
    for y in (2010, 2019, 2025):
        p.append(f'<text x="{X(y):.1f}" y="{Y(ICCSD_SHARE_SF[y])-9:.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#1e3a5f">{ICCSD_SHARE_SF[y]:.0f}%</text>')
    p.append('</svg>')
    return "".join(p)


def lead_chart():
    """ICCSD-corridor SF permits (shifted forward 5 yrs) vs observed K share."""
    W, H, pl, pr, pt, pb = 760, 270, 48, 52, 18, 38
    pw, ph = W - pl - pr, H - pt - pb
    kyears = [y for y in sorted(KSHARE) if y not in COVID_K]
    x0, x1 = min(kyears), max(kyears)

    def X(y): return pl + pw * (y - x0) / (x1 - x0)
    def Yk(v): return pt + ph * (0.78 - v) / (0.78 - 0.68)      # share axis
    def Yp(v): return pt + ph * (560 - v) / (560 - 200)          # permits axis
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in [0.70, 0.72, 0.74, 0.76]:
        gy = Yk(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="10" fill="#1e3a5f">{gv:.2f}</text>')
    for y in kyears:
        p.append(f'<text x="{X(y):.1f}" y="{H-pb+15}" text-anchor="middle" font-size="9.5" fill="#64748b">{str(y)[2:]}</text>')
    # permits shifted forward 5 yrs: plotted at K-year = permit-year + 5
    ppts = " ".join(f"{X(py+LAG):.1f},{Yp(ICCSD_SF[py]):.1f}" for py in range(x0-LAG, x1-LAG+1) if (py+LAG) in range(x0, x1+1))
    p.append(f'<polyline points="{ppts}" fill="none" stroke="#16a34a" stroke-width="2.5" stroke-dasharray="5 3"/>')
    # K share line
    kpts = " ".join(f"{X(y):.1f},{Yk(KSHARE[y]):.1f}" for y in kyears)
    p.append(f'<polyline points="{kpts}" fill="none" stroke="#1e3a5f" stroke-width="2.8"/>')
    for y in kyears:
        p.append(f'<circle cx="{X(y):.1f}" cy="{Yk(KSHARE[y]):.1f}" r="3" fill="#1e3a5f"/>')
    p.append(f'<text x="{W-pr+4}" y="{pt+12}" font-size="10" font-weight="700" fill="#1e3a5f">K share</text>')
    p.append(f'<text x="{W-pr+4}" y="{pt+28}" font-size="10" font-weight="700" fill="#16a34a">SF permits</text>')
    p.append(f'<text x="{W-pr+4}" y="{pt+40}" font-size="8.5" fill="#94a3b8">(lagged 5 yr)</text>')
    p.append('</svg>')
    return "".join(p)


def sf_table():
    head = "".join(f"<th>{str(y)[2:]}</th>" for y in YEARS)
    def row(label, d):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{d[y]}</td>" for y in YEARS) + "</tr>"
    return (f'<table class="dt"><tr><th>Single-family permits</th>{head}</tr>'
            + row("Iowa City", SF['Iowa City'])
            + row("North Liberty", SF['North Liberty'])
            + row("Coralville", SF['Coralville'])
            + row("Johnson Co. uninc.", SF['Johnson Co. (uninc.)'])
            + f'<tr style="border-top:2px solid #1e3a5f"><td><b>ICCSD-corridor total</b></td>'
            + "".join(f"<td><b>{ICCSD_SF[y]}</b></td>" for y in YEARS) + "</tr>"
            + row("Tiffin (CCA)", TIFFIN_SF)
            + "</table>")


NAV = ('<nav class="sitenav"><span class="brand">Iowa City CSD finances</span>'
       '<a href="index.html">How ICCSD compares</a>'
       '<a href="iccsd-cushion.html">Does it have a cushion?</a>'
       '<a href="iowa-district-financial-benchmark.html">Dig into the data</a>'
       '<span class="sep"></span>'
       '<a class="more cur" href="other-analyses.html">Other analyses</a>'
       '<a class="more" href="making-the-foc-work.html">Oversight committee</a></nav>')
NAVCSS = ('.sitenav{max-width:900px;margin:0 auto;padding:14px 18px 0;display:flex;gap:8px;'
          'flex-wrap:wrap;align-items:center;font:600 13.5px/1.4 -apple-system,BlinkMacSystemFont,'
          '"Segoe UI",Roboto,Helvetica,Arial,sans-serif}.sitenav .brand{color:#0f172a;'
          'margin-right:4px;font-weight:800}.sitenav a,.sitenav .cur{display:inline-block;'
          'padding:6px 13px;border-radius:999px;text-decoration:none;border:1px solid #e2e8f0}'
          '.sitenav a{color:#2563eb;background:#fff}.sitenav a:hover{background:#eff6ff;'
          'border-color:#bfdbfe}.sitenav .cur{color:#0f172a;background:#f1f5f9;border-color:#cbd5e1}'
          '.sitenav .sep{flex-basis:100%;height:0;margin:0}.sitenav .more{color:#64748b;'
          'border-color:#eef2f7;background:#fff;font-weight:600}.sitenav .more:hover{'
          'background:#f8fafc;border-color:#e2e8f0}.sitenav .more.cur{color:#0f172a;'
          'background:#f1f5f9;border-color:#cbd5e1}')

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Building Permits as an Early Signal for ICCSD Enrollment</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--bg:#f1f5f9;--card:#fff}}
*{{box-sizing:border-box}}
body{{font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--ink);margin:0;background:var(--bg)}}
a{{color:#1d4ed8}}
.wrap{{max-width:900px;margin:0 auto;padding:24px 18px 60px}}
h1{{font-size:24px;margin:0 0 4px;color:#1e3a5f}}
.sub{{color:var(--mut);font-size:14px;margin:0 0 24px}}
h2{{font-size:17px;margin:36px 0 6px;color:#1e3a5f;border-bottom:2px solid #e2e8f0;padding-bottom:4px}}
p{{margin:0 0 12px;max-width:760px}}
.kpi-row{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;min-width:150px;flex:1}}
.kpi .label{{font-size:12px;color:var(--mut);margin-bottom:3px}}
.kpi .val{{font-size:22px;font-weight:800;line-height:1}}
.kpi .note{{font-size:11.5px;color:var(--mut);margin-top:3px}}
.kpi.green .val{{color:#15803d}}
.kpi.blue .val{{color:#1e3a5f}}
.kpi.red .val{{color:#b91c1c}}
.chart-box{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin:16px 0}}
.chart-box .title{{font-size:13px;font-weight:700;color:var(--mut);margin:0 0 12px;text-transform:uppercase;letter-spacing:.04em}}
.callout{{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:14px 16px;font-size:13.5px;color:#0c4a6e;margin:16px 0;max-width:760px}}
.callout strong{{color:#075985}}
.warn{{background:#fff7ed;border-color:#fed7aa;color:#7c2d12}}
.warn strong{{color:#9a3412}}
.good{{background:#f0fdf4;border-color:#bbf7d0;color:#14532d}}
.good strong{{color:#15803d}}
.src{{font-size:11px;color:var(--mut);margin-top:8px}}
table.dt{{border-collapse:collapse;font-size:11.5px;width:100%;margin:12px 0}}
table.dt th{{background:#1e3a5f;color:#fff;padding:4px 5px;text-align:right;font-size:11px}}
table.dt th:first-child{{text-align:left}}
table.dt td{{padding:3px 5px;border-bottom:1px solid #f1f5f9;text-align:right}}
table.dt td:first-child{{text-align:left;font-weight:600}}
table.dt tr:nth-child(even){{background:#f8fafc}}
ul{{max-width:760px}} li{{margin:4px 0}}
{NAVCSS}
</style>
</head>
<body>
{NAV}
<div class="wrap">

<h1>Building permits as an early signal for ICCSD enrollment</h1>
<p class="sub">Corridor housing permits, 2010 to 2025, as a leading indicator for the kindergarten
share that drives the enrollment forecast</p>

<div class="callout">
  <strong>New single-family homes today become kindergarteners in about five years.</strong> The
  enrollment forecast turns on one number, the share of county births that enrolls in ICCSD
  kindergarten. That share moves with where families build and buy. Building permits give an early
  read on it. In the ICCSD corridor, single-family permits lead the kindergarten share by about five
  years, with a correlation of <strong>{CORR5:+.2f}</strong> (and {CORR4:+.2f} at a four-year lag).
</div>

<div class="kpi-row">
  <div class="kpi blue"><div class="label">Lead correlation</div>
    <div class="val">{CORR5:+.2f}</div><div class="note">corridor single-family permits to K share, 5-yr lag</div></div>
  <div class="kpi red"><div class="label">ICCSD share of corridor single-family</div>
    <div class="val">{ICCSD_SHARE_SF[2019]:.0f}%</div><div class="note">2019 trough, down from {ICCSD_SHARE_SF[2010]:.0f}% in 2010</div></div>
  <div class="kpi green"><div class="label">Recovered to</div>
    <div class="val">{ICCSD_SHARE_SF[2025]:.0f}%</div><div class="note">2025, as Tiffin cooled</div></div>
</div>

<h2>Where the family housing is getting built</h2>
<p>Single-family detached homes are the housing that brings school-age children. Multifamily, mostly
student and young-professional rentals near the university, brings very few. So the single-family
permit trend is the part that matters for enrollment.</p>
<div class="chart-box">
  <div class="title">Single-family permits by city, 2010 to 2025</div>
  {line_chart_cities()}
</div>
<p>Three things show up. Iowa City proper is largely built out, and its single-family permits have
drifted down. North Liberty is the ICCSD growth engine and keeps building at a steady pace. And
Tiffin, which sits in Clear Creek Amana, surged from about 36 single-family permits in 2016 to
120 to 163 a year from 2017 through 2021, then cooled back to about 110.</p>

<h2>The Tiffin capture, visible in permits</h2>
<p>The decomposition analysis argued that ICCSD's lost ground is geographic, families forming in
Tiffin rather than leaving the district. The permits show it directly. ICCSD's share of all corridor
single-family building held above 90% through 2016, then fell to a trough near
{ICCSD_SHARE_SF[2019]:.0f}% from 2018 to 2020 as Tiffin surged. As Tiffin cooled, it recovered to
about {ICCSD_SHARE_SF[2025]:.0f}%.</p>
<div class="chart-box">
  <div class="title">ICCSD-corridor share of single-family permits (rest is Tiffin / CCA)</div>
  {share_sf_chart()}
</div>
<p>Lag that five years and the timing lines up with the kindergarten share. The Tiffin surge of
2017 to 2021 is what fed the K-share decline of 2023 to 2025. That is the same mechanism the
headcount decomposition found, now confirmed by an independent dataset.</p>

<h2>The permits lead the kindergarten share</h2>
<div class="chart-box">
  <div class="title">ICCSD-corridor single-family permits (lagged 5 yr) vs the K-entry share</div>
  {lead_chart()}
</div>
<p>The two lines move together. When corridor single-family building is strong, the kindergarten
share five years later is high. When it dips, the share dips. That is what makes permits a usable
early signal, and the relationship is strong enough ({CORR5:+.2f} at five years) to lean on for
direction even with a short history.</p>

<h2>What it says about the forecast</h2>
<div class="callout good">
  <strong>The permits point to stabilization, not further decline.</strong> The kindergarten classes
  of 2026 to 2030 draw on permits from about 2020 to 2025. Over those years ICCSD-corridor
  single-family permits held steady (around {min(RECENT)} to {max(RECENT)} a year, no further drop),
  and ICCSD's share of corridor single-family building recovered from its {ICCSD_SHARE_SF[2019]:.0f}%
  trough back to about {ICCSD_SHARE_SF[2025]:.0f}%. The thing that pulled the share down, the Tiffin
  surge, has passed its peak. This supports the <strong>Baseline (a flat share near 0.718)</strong>
  and argues against the <strong>Low scenario</strong>, which assumes the share keeps falling toward
  0.680. The leading indicator says the decline is leveling off, not accelerating.
</div>

{sf_table()}

<h2>The honest limit</h2>
<div class="callout warn">
  <strong>These are whole-city totals, not an ICCSD count.</strong> North Liberty and Coralville
  straddle the ICCSD and Clear Creek Amana line, and Tiffin is mostly CCA. Splitting each city's
  permits into ICCSD vs CCA needs an address-level pull and a spatial join against the district
  boundary, which was not done this round. So this is a corridor-level signal that points to a
  direction, not a precise input to the share. Done properly, the address-level join would let the
  permits feed the kindergarten module directly instead of confirming it after the fact.
</div>
<ul>
  <li>Multifamily permits are excluded on purpose. They bring few school-age children.</li>
  <li>Census Building Permits Survey figures for thin-reporting places (Tiffin 2024 to 2025) are
  partly imputed and should be read as preliminary.</li>
  <li>The lead correlation rests on eight non-COVID kindergarten years, so it is directional, not a
  fitted model.</li>
</ul>

<p style="margin-top:24px">
  <a href="iccsd-enrollment-forecast.html">The enrollment forecast &rarr;</a><br>
  <a href="iccsd-enrollment-forecast-backtest.html">Forecast validation and calibration &rarr;</a><br>
  <a href="iccsd-enrollment-decomposition.html">What's driving ICCSD enrollment? &rarr;</a>
</p>

<p class="src">Source: Building Permits/Building Permits (Tier 1)/fact_units_ts.csv. U.S. Census
Bureau Building Permits Survey, place-level annual files (Iowa City, Coralville, North Liberty,
Tiffin), plus Johnson County CitizenServe issued-permits report for the unincorporated balance.
Single-family is the BPS 1-unit bucket. Pulled 2026-06-30. Built {OUT} via
scripts/build_permit_indicator.py.</p>

</div>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT} ({len(HTML):,} bytes)")
print(f"  corr lag5={CORR5:+.3f} lag4={CORR4:+.3f}")
print(f"  ICCSD share SF: 2010={ICCSD_SHARE_SF[2010]:.0f}% 2019={ICCSD_SHARE_SF[2019]:.0f}% 2025={ICCSD_SHARE_SF[2025]:.0f}%")
print(f"  ICCSD SF recent (2020-25): {RECENT}")
