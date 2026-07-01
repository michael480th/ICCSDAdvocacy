#!/usr/bin/env python3
"""Build iccsd-enrollment-permits.html.

Brings the corridor building-permit data into the enrollment forecast as a leading
indicator, now with the address-level ICCSD-vs-CCA split from the Tier 2 (TierA)
geocoded pull.

Data:
  Building Permits/Building Permits (Tier 1)/fact_units_ts.csv   (city-level annual, BPS)
  Building Permits/Building Permits (Tier 1)/fact_permit.csv     (address-level, geocoded,
      school-district-assigned; unincorporated Johnson County 2021-2025)

Two findings:
  1. Corridor single-family permits lead the kindergarten share by about five years.
  2. The geocoded split shows unincorporated-county building is mostly NOT ICCSD
     (about a quarter), so ICCSD's family-housing base is the incorporated core.

Run: python3 scripts/build_permit_indicator.py
"""
import csv, statistics as stat

OUT = "iccsd-enrollment-permits.html"
BASE = "Building Permits/Building Permits (Tier 1)"

# ── City single-family (1-unit) permits, 2010-2025 (BPS) ─────────────────────
ts = list(csv.DictReader(open(f"{BASE}/fact_units_ts.csv")))
YEARS = list(range(2010, 2026))


def sf(j, y):
    return sum(int(r['units']) for r in ts if r['jurisdiction'] == j
               and r['structure_bucket'] == '1-unit' and int(r['period']) == y)


SF = {j: {y: sf(j, y) for y in YEARS}
      for j in ['Iowa City', 'Coralville', 'North Liberty', 'Tiffin', 'Johnson Co. (uninc.)']}
# ICCSD core = the incorporated cities that are entirely or predominantly ICCSD.
# Iowa City is 100% ICCSD (confirmed); Coralville and North Liberty are predominantly ICCSD.
# Unincorporated is dropped from the ICCSD series: geocoding shows it is only ~24% ICCSD.
CORE = {y: SF['Iowa City'][y] + SF['Coralville'][y] + SF['North Liberty'][y] for y in YEARS}
TIFFIN = {y: SF['Tiffin'][y] for y in YEARS}

# ── Geocoded unincorporated-county split, site-built, 2021-2025 ──────────────
fp = list(csv.DictReader(open(f"{BASE}/fact_permit.csv")))


def grp(d):
    if 'Iowa City' in d:
        return 'ICCSD'
    if 'Clear Creek' in d:
        return 'CCA'
    return 'Other'


CO = {y: {'ICCSD': 0, 'CCA': 0, 'Other': 0} for y in range(2021, 2026)}
for r in fp:
    if r['structure_type'] == 'manufactured':
        continue
    y = int(r['issue_date'][:4])
    if y in CO:
        CO[y][grp(r['school_district'])] += int(r['net_units'])
CO_TOT = {k: sum(CO[y][k] for y in CO) for k in ('ICCSD', 'CCA', 'Other')}
CO_ALL = sum(CO_TOT.values())
CO_ICCSD_PCT = 100 * CO_TOT['ICCSD'] / CO_ALL

# ── K-entry share and lead correlation ───────────────────────────────────────
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


def lag_corr(L):
    pr = [(CORE[y - L], KSHARE[y]) for y in sorted(KSHARE) if (y - L) in CORE and y not in COVID_K]
    return corr([p[0] for p in pr], [p[1] for p in pr])


CORR4, CORR5 = lag_corr(4), lag_corr(5)
LAG = 5
RECENT = [CORE[y] for y in range(2020, 2026)]
FONT = '-apple-system,Segoe UI,Roboto,sans-serif'


def cities_chart():
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
        p.append(f'<text x="{W-pr+6}" y="{Y(SF[name][YEARS[-1]])+4:.1f}" font-size="10.5" font-weight="700" fill="{col}">{name}</text>')
    p.append('</svg>')
    return "".join(p)


def county_split_chart():
    """Stacked bars: unincorporated site-built by district group, 2021-2025."""
    W, H, pl, pr, pt, pb = 760, 260, 44, 100, 18, 36
    pw, ph = W - pl - pr, H - pt - pb
    yrs = list(range(2021, 2026))
    ymax = 60
    slot = pw / len(yrs); bw = slot * 0.5
    colors = {'ICCSD': '#1e3a5f', 'CCA': '#dc2626', 'Other': '#cbd5e1'}

    def Y(v): return pt + ph * (ymax - v) / ymax
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in range(0, 61, 20):
        gy = Y(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="10.5" fill="#94a3b8">{gv}</text>')
    for i, y in enumerate(yrs):
        cx = pl + slot * i + slot / 2
        base = 0
        for grpname in ('Other', 'CCA', 'ICCSD'):
            v = CO[y][grpname]
            p.append(f'<rect x="{cx-bw/2:.1f}" y="{Y(base+v):.1f}" width="{bw:.1f}" height="{ph*v/ymax:.1f}" fill="{colors[grpname]}"/>')
            base += v
        p.append(f'<text x="{cx:.1f}" y="{H-pb+16}" text-anchor="middle" font-size="10.5" fill="#64748b">{y}</text>')
    ly = pt + 6
    for grpname in ('ICCSD', 'CCA', 'Other'):
        p.append(f'<rect x="{W-pr+8}" y="{ly-9:.1f}" width="10" height="10" fill="{colors[grpname]}"/>')
        p.append(f'<text x="{W-pr+22}" y="{ly:.1f}" font-size="10.5" font-weight="700" fill="{colors[grpname]}">{grpname}</text>')
        ly += 16
    p.append('</svg>')
    return "".join(p)


def lead_chart():
    W, H, pl, pr, pt, pb = 760, 270, 48, 52, 18, 38
    pw, ph = W - pl - pr, H - pt - pb
    kyears = [y for y in sorted(KSHARE) if y not in COVID_K]
    x0, x1 = min(kyears), max(kyears)

    def X(y): return pl + pw * (y - x0) / (x1 - x0)
    def Yk(v): return pt + ph * (0.78 - v) / (0.78 - 0.68)
    def Yp(v): return pt + ph * (500 - v) / (500 - 150)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in [0.70, 0.72, 0.74, 0.76]:
        gy = Yk(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="10" fill="#1e3a5f">{gv:.2f}</text>')
    for y in kyears:
        p.append(f'<text x="{X(y):.1f}" y="{H-pb+15}" text-anchor="middle" font-size="9.5" fill="#64748b">{str(y)[2:]}</text>')
    ppts = " ".join(f"{X(py+LAG):.1f},{Yp(CORE[py]):.1f}" for py in range(x0-LAG, x1-LAG+1) if x0 <= py+LAG <= x1)
    p.append(f'<polyline points="{ppts}" fill="none" stroke="#16a34a" stroke-width="2.5" stroke-dasharray="5 3"/>')
    kpts = " ".join(f"{X(y):.1f},{Yk(KSHARE[y]):.1f}" for y in kyears)
    p.append(f'<polyline points="{kpts}" fill="none" stroke="#1e3a5f" stroke-width="2.8"/>')
    for y in kyears:
        p.append(f'<circle cx="{X(y):.1f}" cy="{Yk(KSHARE[y]):.1f}" r="3" fill="#1e3a5f"/>')
    p.append(f'<text x="{W-pr+4}" y="{pt+12}" font-size="10" font-weight="700" fill="#1e3a5f">K share</text>')
    p.append(f'<text x="{W-pr+4}" y="{pt+28}" font-size="10" font-weight="700" fill="#16a34a">Core SF</text>')
    p.append(f'<text x="{W-pr+4}" y="{pt+40}" font-size="8.5" fill="#94a3b8">(lagged 5 yr)</text>')
    p.append('</svg>')
    return "".join(p)


def attribution_table():
    # All-structure BPS city totals (sum buckets excl manufactured), 2021-2025.
    def allunits(j, y):
        return sum(int(r['units']) for r in ts if r['jurisdiction'] == j
                   and r['structure_bucket'] != 'manufactured' and int(r['period']) == y)
    yrs = list(range(2021, 2026))
    def row(label, get5, attr, status):
        cells = "".join(f"<td>{v}</td>" for v in get5) + f"<td><b>{sum(get5)}</b></td>"
        return f"<tr><td>{label}</td>{cells}<td>{attr}</td><td>{status}</td></tr>"
    head = "".join(f"<th>{y}</th>" for y in yrs)
    co_site = [CO[y]['ICCSD'] + CO[y]['CCA'] + CO[y]['Other'] for y in yrs]
    return (f'<table class="dt"><tr><th>Jurisdiction (all new units)</th>{head}<th>5-yr</th>'
            f'<th>ICCSD attribution</th><th>Split status</th></tr>'
            + row("Iowa City", [allunits('Iowa City', y) for y in yrs], "100% ICCSD", "confirmed")
            + row("Coralville", [allunits('Coralville', y) for y in yrs], "most ICCSD", "city pending")
            + row("North Liberty", [allunits('North Liberty', y) for y in yrs], "most ICCSD", "city pending")
            + row("Tiffin", [allunits('Tiffin', y) for y in yrs], "mostly CCA", "city pending")
            + row("Johnson Co. uninc. (site-built)", co_site, f"{CO_TOT['ICCSD']} of {CO_ALL} ICCSD ({CO_ICCSD_PCT:.0f}%)", "geocoded")
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
table.dt td:last-child,table.dt td:nth-last-child(2){{text-align:left;font-weight:400}}
table.dt tr:nth-child(even){{background:#f8fafc}}
ul{{max-width:760px}} li{{margin:4px 0}}
{NAVCSS}
</style>
</head>
<body>
{NAV}
<div class="wrap">

<h1>Building permits as an early signal for ICCSD enrollment</h1>
<p class="sub">Corridor housing permits, 2010 to 2025, with the address-level ICCSD vs Clear Creek-Amana
split from the geocoded pull</p>

<div class="callout">
  <strong>New single-family homes today become kindergarteners in about five years.</strong> The
  enrollment forecast turns on one number, the share of county births that enrolls in ICCSD
  kindergarten. That share moves with where families build and buy. In the ICCSD corridor,
  single-family permits lead the kindergarten share by about five years, with a correlation of
  <strong>{CORR4:+.2f}</strong> at a four-year lag ({CORR5:+.2f} at five). The new address-level data
  sharpens the picture by separating ICCSD building from Clear Creek-Amana.
</div>

<div class="kpi-row">
  <div class="kpi blue"><div class="label">Lead correlation</div>
    <div class="val">{CORR4:+.2f}</div><div class="note">ICCSD-core single-family permits to K share, 4-yr lag</div></div>
  <div class="kpi red"><div class="label">Unincorporated county that is ICCSD</div>
    <div class="val">{CO_ICCSD_PCT:.0f}%</div><div class="note">geocoded, 2021-2025 ({CO_TOT['ICCSD']} of {CO_ALL} units)</div></div>
  <div class="kpi green"><div class="label">ICCSD-core single-family permits</div>
    <div class="val">stable</div><div class="note">{min(RECENT)} to {max(RECENT)} a year, 2020-2025</div></div>
</div>

<h2>Where the family housing is getting built</h2>
<p>Single-family detached homes are the housing that brings school-age children. Multifamily, mostly
student and young-professional rentals near the university, brings very few. So the single-family
permit trend is the part that matters for enrollment.</p>
<div class="chart-box">
  <div class="title">Single-family permits by city, 2010 to 2025</div>
  {cities_chart()}
</div>
<p>Iowa City proper is largely built out, and its single-family permits have drifted down. North
Liberty is the ICCSD growth engine and keeps building at a steady pace. Tiffin, which sits in Clear
Creek-Amana, surged from about 36 single-family permits in 2016 to 120 to 163 a year from 2017
through 2021, then cooled back to about 110.</p>

<h2>The ICCSD vs CCA split, from geocoding</h2>
<p>The earlier version of this analysis had to treat whole cities and the whole unincorporated county
as ICCSD. The address-level pull fixes that. Every unincorporated-county permit from 2021 to 2025 was
geocoded and assigned to a school district by point-in-polygon against the Census district boundary.
The result is a clean read on who is actually capturing rural growth.</p>
<div class="chart-box">
  <div class="title">Unincorporated Johnson County new homes by school district (geocoded, site-built)</div>
  {county_split_chart()}
</div>
<div class="callout">
  <strong>Most rural building is not ICCSD.</strong> Of {CO_ALL} site-built homes permitted in
  unincorporated Johnson County over 2021 to 2025, only <strong>{CO_TOT['ICCSD']} ({CO_ICCSD_PCT:.0f}%)
  fall in ICCSD</strong>. Clear Creek-Amana took {CO_TOT['CCA']}, and {CO_TOT['Other']} went to other
  districts entirely, mostly College Community (Prairie), Solon, and Lone Tree. This corrects the
  earlier assumption that unincorporated growth was ICCSD. It is not. ICCSD's family-housing base is
  the incorporated core, not the rural fringe.
</div>

<h2>The corridor, attributed</h2>
{attribution_table()}
<p>Iowa City sits entirely inside ICCSD, so its new units are all ICCSD. The unincorporated county is
now geocoded. Coralville and North Liberty are predominantly ICCSD but have Clear Creek-Amana slices
on their western edges, and their city permit portals blocked a clean address-level pull this round.
Tiffin is primarily Clear Creek-Amana.</p>

<h2>The permits lead the kindergarten share</h2>
<div class="chart-box">
  <div class="title">ICCSD-core single-family permits (lagged 5 yr) vs the K-entry share</div>
  {lead_chart()}
</div>
<p>ICCSD-core here means Iowa City plus Coralville plus North Liberty, the incorporated cities that
are entirely or predominantly ICCSD. The unincorporated county is left out, because the geocoding
shows it is mostly other districts. The two lines still move together, and the relationship holds
({CORR4:+.2f} at four years), so the corrected series works as an early signal.</p>

<h2>What it says about the forecast</h2>
<div class="callout good">
  <strong>The permits point to stabilization, not further decline.</strong> The kindergarten classes
  of 2026 to 2030 draw on permits from about 2020 to 2025. Over those years ICCSD-core single-family
  permits held steady, between {min(RECENT)} and {max(RECENT)} a year, with no further drop. The Tiffin
  surge that pulled the share down has passed its peak, and the incorporated core that actually feeds
  ICCSD kept building. This supports the <strong>Baseline (a flat share near 0.718)</strong> and
  argues against the <strong>Low scenario</strong>, which assumes the share keeps falling toward
  0.680. It also reframes the geographic drain. It is not only Tiffin. The whole rural fringe of the
  county builds mostly for other districts, and ICCSD captures its incorporated core.
</div>

<h2>The honest limit</h2>
<div class="callout warn">
  <strong>Two of the suburbs are still whole-city totals.</strong> The geocoding is complete for
  Iowa City (all ICCSD) and the unincorporated county. Coralville and North Liberty still come in as
  whole-city BPS totals, because their permit portals blocked a clean address-level pull. Both are
  predominantly ICCSD with small Clear Creek-Amana slices, so the ICCSD-core series is close but not
  exact. A records request to those two cities would finish the split and let the permits feed the
  kindergarten module directly.
</div>
<ul>
  <li>Multifamily permits are excluded on purpose. They bring few school-age children.</li>
  <li>Manufactured-home placements are excluded. They are mostly replacements, not net-new.</li>
  <li>The lead correlation rests on eight non-COVID kindergarten years, so it is directional, not a
  fitted model.</li>
</ul>

<p style="margin-top:24px">
  <a href="iccsd-enrollment-forecast.html">The enrollment forecast &rarr;</a><br>
  <a href="iccsd-enrollment-forecast-backtest.html">Forecast validation and calibration &rarr;</a><br>
  <a href="iccsd-enrollment-decomposition.html">What's driving ICCSD enrollment? &rarr;</a>
</p>

<p class="src">Source: Building Permits (Tier 1) fact_units_ts.csv (U.S. Census Building Permits
Survey, place-level, single-family = 1-unit bucket) and fact_permit.csv (address-level, geocoded with
the Esri World Geocoder and assigned to school districts by point-in-polygon against Census TIGERweb
Unified School Districts, 2024 vintage). Unincorporated permits from the Johnson County CitizenServe
issued-permits report, 2021 to 2025. Pulled 2026-06-30. Built {OUT} via
scripts/build_permit_indicator.py.</p>

</div>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT} ({len(HTML):,} bytes)")
print(f"  corr lag4={CORR4:+.3f} lag5={CORR5:+.3f}")
print(f"  county split 5yr: ICCSD={CO_TOT['ICCSD']} CCA={CO_TOT['CCA']} Other={CO_TOT['Other']} ({CO_ICCSD_PCT:.0f}% ICCSD)")
print(f"  core SF 2020-2025: {RECENT}")
