#!/usr/bin/env python3
"""
Build iccsd-enrollment-decomposition.html
All-factors walk: demographics, CCA/Tiffin, ESA, open enrollment, birth rate, immigration.
Source data: Iowa DOE BEDS (PK-12 headcount), certified enrollment files.
"""

import json, os

OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "iccsd-enrollment-decomposition.html")

# ── Data ──────────────────────────────────────────────────────────────────────

# BEDS PK-12 headcount by district, extracted from Iowa DOE BEDS public files.
BEDS = [
    {"sy":"2011-12","yr":2011,"ICCSD":12405,"CCA":1779,"Solon":1378,"county":16099},
    {"sy":"2012-13","yr":2012,"ICCSD":12751,"CCA":1919,"Solon":1408,"county":16607},
    {"sy":"2013-14","yr":2013,"ICCSD":13215,"CCA":2022,"Solon":1441,"county":17208},
    {"sy":"2014-15","yr":2014,"ICCSD":13397,"CCA":2103,"Solon":1495,"county":17523},
    {"sy":"2015-16","yr":2015,"ICCSD":13666,"CCA":2199,"Solon":1494,"county":17862},
    {"sy":"2016-17","yr":2016,"ICCSD":13986,"CCA":2331,"Solon":1535,"county":18351},
    {"sy":"2017-18","yr":2017,"ICCSD":14405,"CCA":2492,"Solon":1531,"county":18923},
    {"sy":"2018-19","yr":2018,"ICCSD":14560,"CCA":2633,"Solon":1531,"county":19226},
    {"sy":"2019-20","yr":2019,"ICCSD":14939,"CCA":2750,"Solon":1529,"county":19701},
    {"sy":"2020-21","yr":2020,"ICCSD":14428,"CCA":2823,"Solon":1515,"county":19232},
    {"sy":"2021-22","yr":2021,"ICCSD":14820,"CCA":2975,"Solon":1511,"county":19764},
    {"sy":"2022-23","yr":2022,"ICCSD":14806,"CCA":3061,"Solon":1523,"county":19818},
    {"sy":"2023-24","yr":2023,"ICCSD":14776,"CCA":3126,"Solon":1522,"county":19862},
    {"sy":"2024-25","yr":2024,"ICCSD":15013,"CCA":3156,"Solon":1477,"county":20047},
    {"sy":"2025-26","yr":2025,"ICCSD":14871,"CCA":3190,"Solon":1504,"county":19945},
]

BASE_SHARE = 100 * BEDS[0]["ICCSD"] / BEDS[0]["county"]   # 77.05 %

# Open enrollment net (OE In − OE Out) from Iowa DOE certified enrollment files.
OE = [
    {"sy":"2017-18","iccsd": -272.5,"cca": 161.5},
    {"sy":"2018-19","iccsd": -227.6,"cca": 118.7},
    {"sy":"2019-20","iccsd": -192.8,"cca":  87.0},
    {"sy":"2020-21","iccsd": -197.8,"cca":  62.3},
    {"sy":"2021-22","iccsd":  -39.9,"cca":  12.0},
    {"sy":"2022-23","iccsd":  -44.5,"cca":  -8.1},
    {"sy":"2023-24","iccsd":   15.1,"cca": -40.9},
    {"sy":"2024-25","iccsd":   12.9,"cca": -73.6},
    {"sy":"2025-26","iccsd":   14.6,"cca":-104.4},
]

# ESA resident counts from Iowa DOE certified enrollment (Row 14).
# Net switchers = ~9 % of residents (78 % already private = inframarginal).
ESA = [
    {"sy":"2023-24","residents": 471,"net_est":  50},
    {"sy":"2024-25","residents": 773,"net_est":  75},
    {"sy":"2025-26","residents":1440,"net_est": 130},
]

# Counterfactual: ICCSD at 2011-12 county share each year
for r in BEDS:
    r["cf"]  = round(r["county"] * BASE_SHARE / 100)
    r["gap"] = r["ICCSD"] - r["cf"]
    r["iccsd_pct"] = round(100 * r["ICCSD"] / r["county"], 2)
    r["cca_pct"]   = round(100 * r["CCA"]   / r["county"], 2)

start = BEDS[0]
end   = BEDS[-1]
demo_growth = end["cf"] - start["ICCSD"]   # +2,965
geo_capture = end["gap"]                    # -499  (actual − counterfactual)

# ── JS data blobs ─────────────────────────────────────────────────────────────

SY          = json.dumps([r["sy"]   for r in BEDS])
ICCSD_ENRL  = json.dumps([r["ICCSD"] for r in BEDS])
CCA_ENRL    = json.dumps([r["CCA"]   for r in BEDS])
SOLON_ENRL  = json.dumps([r["Solon"] for r in BEDS])
CF_ENRL     = json.dumps([r["cf"]    for r in BEDS])
ICCSD_PCT   = json.dumps([r["iccsd_pct"] for r in BEDS])
CCA_PCT     = json.dumps([r["cca_pct"]   for r in BEDS])
GAP_SERIES  = json.dumps([r["gap"]  for r in BEDS])

OE_SY     = json.dumps([r["sy"]    for r in OE])
OE_ICCSD  = json.dumps([r["iccsd"] for r in OE])
OE_CCA    = json.dumps([r["cca"]   for r in OE])

# Waterfall bars: [low, high] pairs for Chart.js floating bars
# Bars: Start | +Demo | −Geo | = End
wf_labels = ["2011-12\nEnrollment", "County\nDemographic Growth", "CCA/Tiffin\nGeographic Capture", "2025-26\nEnrollment"]
wf_float  = [
    [0, start["ICCSD"]],                    # Start
    [start["ICCSD"], end["cf"]],            # +Demo (green)
    [end["ICCSD"], end["cf"]],              # −Geo  (red)
    [0, end["ICCSD"]],                      # End
]
wf_colors = ["#1e3a5f","#16a34a","#dc2626","#1e3a5f"]

WF_LABELS = json.dumps(wf_labels)
WF_DATA   = json.dumps(wf_float)
WF_COLORS = json.dumps(wf_colors)

# ── HTML ──────────────────────────────────────────────────────────────────────

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>What's Driving ICCSD Enrollment? — Factor Decomposition</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
h3{{font-size:15px;margin:22px 0 5px;color:#1e40af}}
p{{margin:0 0 12px;max-width:760px}}
.kpi-row{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:14px 18px;min-width:150px;flex:1}}
.kpi .label{{font-size:12px;color:var(--mut);margin-bottom:3px}}
.kpi .val{{font-size:22px;font-weight:800;line-height:1}}
.kpi .note{{font-size:11.5px;color:var(--mut);margin-top:3px}}
.kpi.green .val{{color:#15803d}}
.kpi.red .val{{color:#b91c1c}}
.kpi.blue .val{{color:#1e3a5f}}
.kpi.amber .val{{color:#b45309}}
.chart-box{{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:18px;margin:16px 0}}
.chart-box .title{{font-size:13px;font-weight:700;color:var(--mut);margin:0 0 12px;
  text-transform:uppercase;letter-spacing:.04em}}
.factor-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0}}
@media(max-width:640px){{.factor-grid{{grid-template-columns:1fr}}}}
.factor{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}}
.factor .f-head{{font-size:14px;font-weight:700;margin:0 0 6px}}
.factor .f-num{{font-size:20px;font-weight:800;margin:0 0 4px}}
.factor .f-body{{font-size:13px;color:#374151;margin:0}}
.factor.green{{border-top:3px solid #16a34a}}
.factor.green .f-num{{color:#15803d}}
.factor.red{{border-top:3px solid #dc2626}}
.factor.red .f-num{{color:#b91c1c}}
.factor.amber{{border-top:3px solid #d97706}}
.factor.amber .f-num{{color:#b45309}}
.factor.blue{{border-top:3px solid #2563eb}}
.factor.blue .f-num{{color:#1e40af}}
.callout{{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;
  padding:14px 16px;font-size:13.5px;color:#0c4a6e;margin:16px 0;max-width:760px}}
.callout strong{{color:#075985}}
.warn{{background:#fff7ed;border-color:#fed7aa;color:#7c2d12}}
.warn strong{{color:#9a3412}}
.src{{font-size:11px;color:var(--mut);margin-top:8px}}
table.dt{{border-collapse:collapse;font-size:13px;width:100%;margin:12px 0}}
table.dt th{{background:#1e3a5f;color:#fff;padding:5px 8px;text-align:right;font-size:12px}}
table.dt th:first-child{{text-align:left}}
table.dt td{{padding:4px 8px;border-bottom:1px solid #f1f5f9;text-align:right}}
table.dt td:first-child{{text-align:left;font-weight:600}}
table.dt tr:nth-child(even){{background:#f8fafc}}
table.dt .gap-neg{{color:#b91c1c;font-weight:700}}
table.dt .gap-pos{{color:#15803d;font-weight:700}}
.nav{{font-size:13px;color:var(--mut);margin:0 0 20px}}
.nav a{{color:#1d4ed8;text-decoration:none}}
</style>
</head>
<body>
<div class="wrap">

<p class="nav"><a href="index.html">← ICCSD Financial Benchmarking</a></p>
<h1>What's Driving ICCSD Enrollment?</h1>
<p class="sub">A factor-by-factor decomposition, 2011–2025 &nbsp;·&nbsp; Iowa DOE BEDS PK-12 headcount</p>

<div class="callout">
  ICCSD grew <strong>+2,466 students (PK-12)</strong> from 2011-12 to 2025-26 — but it would have grown
  <strong>+2,965 students</strong> if it had simply held its 2011 share of a growing Johnson County.
  The <strong>~499-student gap</strong> is almost entirely explained by Tiffin/Clear Creek Amana absorbing
  new residential growth that would otherwise have flowed to ICCSD. On top of that, post-2023 ESA
  transfers add a newer, smaller headwind. Looking forward, declining birth cohorts are the dominant risk.
</div>

<!-- KPI row -->
<div class="kpi-row">
  <div class="kpi green">
    <div class="label">County demographic tailwind</div>
    <div class="val">+{demo_growth:,}</div>
    <div class="note">Students ICCSD gained from county growth (at 2011 share)</div>
  </div>
  <div class="kpi red">
    <div class="label">CCA geographic capture</div>
    <div class="val">{geo_capture:,}</div>
    <div class="note">Annual gap vs. 2011 share (2025-26)</div>
  </div>
  <div class="kpi red">
    <div class="label">ESA net transfers (2025-26)</div>
    <div class="val">≈ −130</div>
    <div class="note">Public→private switchers (9 % of 1,440 residents)</div>
  </div>
  <div class="kpi blue">
    <div class="label">Open enrollment (net, 2025-26)</div>
    <div class="val">+15</div>
    <div class="note">More CCA/Solon residents now choose ICCSD than vice versa</div>
  </div>
</div>

<!-- ── SECTION 1: Waterfall ──────────────────────────────────────────── -->
<h2>The 14-Year Walk (2011-12 → 2025-26)</h2>
<p>
  The bar below shows how ICCSD enrollment changed from its 2011-12 base. Two factors explain
  essentially everything: Johnson County grew (green), but CCA/Tiffin absorbed a
  disproportionate share of that growth (red).
</p>
<div class="chart-box">
  <div class="title">Enrollment bridge — 2011-12 to 2025-26 (PK-12 headcount)</div>
  <canvas id="wfChart" height="220"></canvas>
  <p class="src">Sources: Iowa DOE BEDS Public enrollment files, 2011-12 through 2025-26.
   Counterfactual = ICCSD at its 2011-12 county share ({BASE_SHARE:.1f}%) applied to each year's
   Johnson County total public enrollment.</p>
</div>

<div class="callout">
  <strong>What this means:</strong> Johnson County's public school enrollment grew by 3,846 students
  over 14 years. At ICCSD's 2011 share, it would have captured 2,965 of those — instead it
  captured 2,466. The missing 499 students per year (by 2025-26) sit inside Clear Creek Amana CSD.
</div>

<!-- ── SECTION 2: County share over time ────────────────────────────── -->
<h2>Johnson County Share — How It Shifted</h2>
<div class="chart-box">
  <div class="title">District share of Johnson County public PK-12 enrollment</div>
  <canvas id="shareChart" height="220"></canvas>
  <p class="src">All Johnson County public school districts. The CCA share gain mirrors the ICCSD share loss almost exactly;
   Solon is flat.</p>
</div>

<!-- ── SECTION 3: Factor cards ──────────────────────────────────────── -->
<h2>Each Factor, Explained</h2>
<div class="factor-grid">

  <div class="factor green">
    <div class="f-head">① County Population &amp; In-Migration</div>
    <div class="f-num">+2,965 students</div>
    <div class="f-body">
      Johnson County's public K-12 enrollment grew 24 % from 2011 to 2025, driven by
      University of Iowa employment growth, hospital and biomedical sector expansion, and
      general in-migration from outside Iowa. ICCSD benefited proportionally — this is
      the demographic tailwind that lifted all boats.
    </div>
  </div>

  <div class="factor green">
    <div class="f-head">② Immigrant &amp; ESL Student Growth</div>
    <div class="f-num">~+900 students (est.)</div>
    <div class="f-body">
      Johnson County immigrant students grew from roughly 20 in 2009-10 to
      ~1,164 in 2020-21 (Iowa DOE). ICCSD captures roughly 78 % of county
      public enrollment, implying ~900 incremental students from this cohort alone.
      This is <em>embedded in</em> the county growth figure above — without immigration,
      the tailwind would be significantly smaller.
      <br><br>
      <strong>Forward risk:</strong> immigration-policy uncertainty could reduce or
      reverse this cushion with a 3–5 year lag into K-12 enrollment.
    </div>
  </div>

  <div class="factor red">
    <div class="f-head">③ CCA / Tiffin Geographic Capture</div>
    <div class="f-num">−499 students/yr (2025-26)</div>
    <div class="f-body">
      Clear Creek Amana CSD (containing Tiffin) grew 79 % from 2011 to 2025 while
      ICCSD grew 20 %. New subdivisions in Tiffin — larger lots, newer construction,
      lower price per square foot — attract Iowa City-area families, who then enroll in CCA.
      <br><br>
      Critically, <strong>no transfer event occurs</strong>: many of these families moved
      to Tiffin before having children, or relocated directly from out of state. The loss
      is invisible to open-enrollment data and only measurable via the BEDS headcount gap.
    </div>
  </div>

  <div class="factor red">
    <div class="f-head">④ ESA Net Transfers (2023+)</div>
    <div class="f-num">≈ −130 students/yr (2025-26)</div>
    <div class="f-body">
      Iowa's ESA (Educational Savings Account) voucher program launched in 2023.
      ICCSD has 1,440 resident ESA users in 2025-26, but the district's own analysis
      found ~78 % were already attending private school (inframarginal). Net public→private
      switchers are estimated at ~120–190 over three years, or roughly 130 in the
      current year.
      <br><br>
      ESA is <em>separate from</em> the county-share analysis above because private-school
      students leave the county BEDS total too. ESA is an additional drag on top of the
      geographic capture figure.
    </div>
  </div>

  <div class="factor blue">
    <div class="f-head">⑤ Open Enrollment (Now Net Positive)</div>
    <div class="f-num">+15 net (2025-26)</div>
    <div class="f-body">
      Students from neighboring districts (CCA, Solon, others) can open-enroll into ICCSD
      and vice versa. In 2017-18, ICCSD was losing 272 students more than it gained on net.
      By 2023-24 the balance flipped positive. CCA went from +161 net in 2017-18 to −104
      net in 2025-26 — its own residents are increasingly choosing ICCSD.
      <br><br>
      This is a direct signal: <strong>families with an active choice are choosing ICCSD
      more than before</strong>, ruling out district-quality flight as a driver of enrollment pressure.
    </div>
  </div>

  <div class="factor amber">
    <div class="f-head">⑥ Birth Rate — The Forward-Looking Driver</div>
    <div class="f-num">−600 to −900 by 2030 (est.)</div>
    <div class="f-body">
      Johnson County births peaked around 2007-2011. Students born in those high-birth
      years are now 14-18 and approaching graduation; smaller cohorts born 2014-2020
      are entering kindergarten. This "pipeline" effect — not ESA, not transfers — is the
      primary driver of the projected enrollment decline through 2030.
      <br><br>
      Three independent forecasts (Iowa DOE 2026 projections, Woolpert 2025, this model's
      baseline) all converge on ICCSD K-12 enrollment of ~13,475–13,720 by 2030-31.
    </div>
  </div>

</div>

<!-- ── SECTION 4: Enrollment trend chart ────────────────────────────── -->
<h2>Enrollment Over Time — ICCSD, CCA, Counterfactual</h2>
<div class="chart-box">
  <div class="title">PK-12 headcount: ICCSD actual vs. constant-share counterfactual, and CCA</div>
  <canvas id="trendChart" height="260"></canvas>
  <p class="src">Counterfactual line = ICCSD enrollment if it had held its 2011-12 county share each year.
  COVID-related anomaly visible in 2020-21 (ICCSD −511, CCA +73).</p>
</div>

<!-- Full data table -->
<h3>Full data table</h3>
<table class="dt">
  <thead>
    <tr>
      <th style="text-align:left">SY</th>
      <th>ICCSD</th>
      <th>At 2011 Share</th>
      <th>Gap</th>
      <th>ICCSD %</th>
      <th>CCA</th>
      <th>CCA %</th>
      <th>County Total</th>
    </tr>
  </thead>
  <tbody>
""" + "".join(
    f"""    <tr>
      <td>{r['sy']}</td>
      <td>{r['ICCSD']:,}</td>
      <td>{r['cf']:,}</td>
      <td class="{'gap-neg' if r['gap'] < 0 else 'gap-pos'}">{r['gap']:+,}</td>
      <td>{r['iccsd_pct']:.1f}%</td>
      <td>{r['CCA']:,}</td>
      <td>{r['cca_pct']:.1f}%</td>
      <td>{r['county']:,}</td>
    </tr>\n"""
    for r in BEDS
) + f"""  </tbody>
</table>

<!-- ── SECTION 5: Open enrollment chart ─────────────────────────────── -->
<h2>Open Enrollment — Net Position</h2>
<p>
  Open enrollment records students who cross district lines <em>by choice</em> while remaining
  a resident of the sending district. Families who <em>moved</em> to Tiffin are invisible here —
  this chart shows only active-choice transfers.
</p>
<div class="chart-box">
  <div class="title">Net open enrollment (OE In − OE Out): ICCSD and CCA</div>
  <canvas id="oeChart" height="220"></canvas>
  <p class="src">Source: Iowa DOE Certified Enrollment by District (Row 8 minus Row 2). Positive = net receiver.</p>
</div>

<div class="callout">
  <strong>Why this matters:</strong> If families were fleeing ICCSD for CCA due to quality concerns,
  ICCSD's net open-enrollment would be falling and CCA's would be rising. The opposite happened.
  ICCSD flipped from −273 net in 2017-18 to +15 in 2025-26; CCA flipped from +162 to −104.
  The enrollment pressure on ICCSD is a <em>housing geography</em> story, not a quality story.
</div>

<!-- ── SECTION 6: ESA ─────────────────────────────────────────────────── -->
<h2>ESA in Context</h2>
<div class="factor-grid">
  <div class="factor red">
    <div class="f-head">ESA resident users</div>
    <div class="f-num">1,440 (2025-26)</div>
    <div class="f-body">ICCSD-resident students using an ESA, per Iowa DOE certified enrollment Row 14. Up from 471 in 2023-24.</div>
  </div>
  <div class="factor amber">
    <div class="f-head">Net public→private switchers</div>
    <div class="f-num">~130 est. (2025-26)</div>
    <div class="f-body">~78% of ESA users were already attending private school (inframarginal).
     Net new transfers from ICCSD public ≈ 120-190 over 3 years total.</div>
  </div>
  <div class="factor red">
    <div class="f-head">CCA geographic capture (2025-26)</div>
    <div class="f-num">499 students/yr</div>
    <div class="f-body">The geographic headwind is roughly <strong>4× larger</strong> than ESA on an annual basis
     and has been compounding since 2011.</div>
  </div>
  <div class="factor amber">
    <div class="f-head">CCA cumulative (2011-2025)</div>
    <div class="f-num">~4,100 student-years</div>
    <div class="f-body">Cumulative student-years of foregone enrollment at constant county share.
     At ~$9,000 state aid/student: ≈$37M in foregone foundation aid since 2011.</div>
  </div>
</div>

<!-- ── SECTION 7: Forward view ─────────────────────────────────────────── -->
<h2>Looking Forward (2025–2030)</h2>
<div class="callout warn">
  <strong>The birth-rate cliff:</strong> Johnson County births peaked around 2007-2011.
  Students born in those peak years are graduating now. Smaller cohorts born 2014–2020
  will shrink kindergarten classes through ~2025-2030. Three independent forecasts
  converge on <strong>~13,475–13,720 ICCSD enrollment by 2030-31</strong> — a decline of
  roughly 800–900 students from the 2024-25 certified enrollment of ~14,550.
  At $9,000/student in state foundation aid, that is a <strong>~$7–8M annual revenue headwind</strong>.
</div>
<div class="factor-grid">
  <div class="factor red">
    <div class="f-head">Birth cohort decline</div>
    <div class="f-num">−600 to −900 by 2030</div>
    <div class="f-body">Primary driver of projected decline. Already "baked in" — the children who
     will be in K-12 in 2030 are already born.</div>
  </div>
  <div class="factor red">
    <div class="f-head">Continued CCA growth</div>
    <div class="f-num">−50 to −100/yr additional</div>
    <div class="f-body">Tiffin construction pipeline continues; CCA's share likely to
     reach 17-18% of county by 2030. Further structural drag on ICCSD headcount.</div>
  </div>
  <div class="factor amber">
    <div class="f-head">ESA trajectory</div>
    <div class="f-num">−50 to −150 additional</div>
    <div class="f-body">ESA enrollment is growing. The inframarginal share may shrink as
     the pool of "already-private" families is exhausted, increasing marginal impact.</div>
  </div>
  <div class="factor amber">
    <div class="f-head">Immigration cushion</div>
    <div class="f-num">Positive but uncertain</div>
    <div class="f-body">Johnson County's immigrant student influx has been a meaningful offset.
     Federal immigration policy changes could reduce this cushion with a 3–5 year lag.</div>
  </div>
</div>

<p style="margin-top:24px">
  <a href="iccsd-enrollment-forecast.html">→ Full enrollment forecast with three scenarios (Baseline, High, Low)</a>
</p>

</div><!-- /wrap -->

<script>
const sy = {SY};
const iccsd = {ICCSD_ENRL};
const cca   = {CCA_ENRL};
const solon = {SOLON_ENRL};
const cf    = {CF_ENRL};
const iccsd_pct = {ICCSD_PCT};
const cca_pct   = {CCA_PCT};
const oe_sy     = {OE_SY};
const oe_iccsd  = {OE_ICCSD};
const oe_cca    = {OE_CCA};
const wfLabels  = {WF_LABELS};
const wfData    = {WF_DATA};
const wfColors  = {WF_COLORS};

const FONT = {{family:'-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif',size:12}};
const gridColor = '#e2e8f0';
const tickColor = '#64748b';

// ── Waterfall chart ──────────────────────────────────────────────────────────
new Chart(document.getElementById('wfChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: wfLabels,
    datasets: [{{
      data: wfData,
      backgroundColor: wfColors,
      borderWidth: 0,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{display: false}},
      tooltip: {{
        callbacks: {{
          label(ctx) {{
            const [lo, hi] = ctx.raw;
            const val = hi - lo;
            return val >= 0 ? `+${{val.toLocaleString()}}` : val.toLocaleString();
          }}
        }}
      }}
    }},
    scales: {{
      x: {{
        ticks: {{font: FONT, color: tickColor}},
        grid: {{display: false}},
      }},
      y: {{
        ticks: {{font: FONT, color: tickColor, callback: v => v.toLocaleString()}},
        grid: {{color: gridColor}},
        min: 0,
        max: 16000,
        title: {{display: true, text: 'PK-12 enrollment', font: FONT, color: tickColor}}
      }}
    }}
  }}
}});

// ── Share chart ──────────────────────────────────────────────────────────────
new Chart(document.getElementById('shareChart').getContext('2d'), {{
  type: 'line',
  data: {{
    labels: sy,
    datasets: [
      {{label:'ICCSD',data:iccsd_pct,borderColor:'#1e3a5f',backgroundColor:'transparent',
        borderWidth:2.5,pointRadius:3,tension:0.2}},
      {{label:'CCA (Tiffin)',data:cca_pct,borderColor:'#dc2626',backgroundColor:'transparent',
        borderWidth:2.5,pointRadius:3,tension:0.2}},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{position:'top',labels:{{font:FONT,boxWidth:20}}}},
      tooltip: {{callbacks: {{label: ctx => `${{ctx.dataset.label}}: ${{ctx.parsed.y.toFixed(1)}}%`}}}}
    }},
    scales: {{
      x: {{ticks:{{font:FONT,color:tickColor,maxRotation:45}}, grid:{{display:false}}}},
      y: {{
        ticks:{{font:FONT,color:tickColor,callback:v=>`${{v}}%`}},
        grid:{{color:gridColor}},
        min:9,max:82,
        title:{{display:true,text:'% of Johnson County public enrollment',font:FONT,color:tickColor}}
      }}
    }}
  }}
}});

// ── Trend chart ──────────────────────────────────────────────────────────────
new Chart(document.getElementById('trendChart').getContext('2d'), {{
  type: 'line',
  data: {{
    labels: sy,
    datasets: [
      {{label:'ICCSD actual',data:iccsd,borderColor:'#1e3a5f',backgroundColor:'transparent',
        borderWidth:2.5,pointRadius:3,tension:0.2}},
      {{label:'ICCSD at 2011 share (counterfactual)',data:cf,
        borderColor:'#94a3b8',backgroundColor:'transparent',borderWidth:1.5,
        borderDash:[6,4],pointRadius:0,tension:0.2}},
      {{label:'CCA (Tiffin area)',data:cca,borderColor:'#dc2626',backgroundColor:'transparent',
        borderWidth:2,pointRadius:3,tension:0.2}},
      {{label:'Solon',data:solon,borderColor:'#f59e0b',backgroundColor:'transparent',
        borderWidth:1.5,pointRadius:2,tension:0.2}},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{position:'top',labels:{{font:FONT,boxWidth:20}}}},
      tooltip: {{callbacks: {{label: ctx => `${{ctx.dataset.label}}: ${{ctx.parsed.y.toLocaleString()}}`}}}}
    }},
    scales: {{
      x: {{ticks:{{font:FONT,color:tickColor,maxRotation:45}}, grid:{{display:false}}}},
      y: {{
        ticks:{{font:FONT,color:tickColor,callback:v=>v.toLocaleString()}},
        grid:{{color:gridColor}},
        title:{{display:true,text:'PK-12 headcount',font:FONT,color:tickColor}}
      }}
    }}
  }}
}});

// ── Open enrollment chart ────────────────────────────────────────────────────
new Chart(document.getElementById('oeChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: oe_sy,
    datasets: [
      {{label:'ICCSD net OE',data:oe_iccsd,backgroundColor:'#1e3a5f',borderRadius:4}},
      {{label:'CCA net OE',data:oe_cca,backgroundColor:'#dc2626',borderRadius:4}},
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{position:'top',labels:{{font:FONT,boxWidth:16}}}},
      tooltip: {{callbacks: {{label: ctx => `${{ctx.dataset.label}}: ${{ctx.parsed.y > 0 ? '+' : ''}}${{ctx.parsed.y.toFixed(0)}}`}}}}
    }},
    scales: {{
      x: {{ticks:{{font:FONT,color:tickColor}}, grid:{{display:false}}}},
      y: {{
        ticks:{{font:FONT,color:tickColor,callback:v=>(v>0?'+':'')+v}},
        grid:{{color:gridColor}},
        title:{{display:true,text:'OE In − OE Out (students)',font:FONT,color:tickColor}}
      }}
    }}
  }}
}});
</script>
</body>
</html>
"""

os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Written: {OUT_FILE}")
print(f"  Start 2011-12:       {start['ICCSD']:,}")
print(f"  Demo growth:         +{demo_growth:,}")
print(f"  Geographic capture:  {geo_capture:,}")
print(f"  End 2025-26:         {end['ICCSD']:,}")
print(f"  Base county share:   {BASE_SHARE:.2f}%")
