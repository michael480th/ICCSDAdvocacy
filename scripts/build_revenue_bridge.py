#!/usr/bin/env python3
"""Build iccsd-enrollment-revenue-bridge.html.

Translates the cohort-survival enrollment forecast into a recurring-revenue
headwind and lays it against the district's thin cash cushion. Connects the
enrollment work to the financial-health work in concrete dollar terms.
"""

OUT = "iccsd-enrollment-revenue-bridge.html"

# ── Enrollment (K-12, from iccsd-enrollment-forecast.html) ───────────────────
BASE_YEAR, BASE_ENROLL = 2025, 14227
# Baseline scenario trajectory 2025 -> 2030
BASELINE = {2025: 14227, 2026: 14124, 2027: 14028, 2028: 13836, 2029: 13645, 2030: 13475}
SCEN_2030 = {"High": 13551, "Baseline": 13475, "Low": 13306}

# ── Funding assumptions ──────────────────────────────────────────────────────
PER_PUPIL = 9000          # site-standard all-in state foundation aid per student
PER_PUPIL_LOW = 7800      # regular-program district cost per pupil (conservative)

# ── Cash cushion (ICCSD General Fund, from Healthy Cash Levels.xlsx) ──────────
# days -> $M GF balance
CASH_DAYS = {15: 9, 30: 17, 45: 26, 60: 35, 90: 52}
CURRENT_DAYS = 31         # FY2025 Day's Net Cash (all funds), adjusted
CURRENT_CASH_M = 18       # ~31 days GF cash ≈ $18M (interpolated from table)

drop_2030 = BASE_ENROLL - SCEN_2030["Baseline"]            # 752
headwind_2030 = drop_2030 * PER_PUPIL                       # ~$6.8M
headwind_low = (BASE_ENROLL - SCEN_2030["High"]) * PER_PUPIL
headwind_high = (BASE_ENROLL - SCEN_2030["Low"]) * PER_PUPIL
# cumulative student-years 2026-2030 (baseline gap vs 2025)
cum_student_years = sum(BASE_ENROLL - BASELINE[y] for y in range(2026, 2031))
cum_dollars = cum_student_years * PER_PUPIL

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


def headwind_svg():
    """Bar chart: annual revenue headwind vs 2025 base, 2026-2030 (baseline)."""
    W, H, padl, padr, padt, padb = 760, 280, 56, 16, 24, 42
    plot_w, plot_h = W - padl - padr, H - padt - padb
    yrs = list(range(2026, 2031))
    vals = [(BASE_ENROLL - BASELINE[y]) * PER_PUPIL / 1e6 for y in yrs]
    ymax = 8.0
    n = len(yrs)
    slot = plot_w / n
    bw = slot * 0.55

    def Y(v): return padt + plot_h * (ymax - v) / ymax

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
             f'aria-label="Annual revenue headwind" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    for gv in range(0, 9, 2):
        gy = Y(gv)
        parts.append(f'<line x1="{padl}" y1="{gy:.1f}" x2="{W-padr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        parts.append(f'<text x="{padl-8}" y="{gy+4:.1f}" text-anchor="end" font-size="11" '
                     f'fill="#94a3b8">${gv}M</text>')
    for i, yr in enumerate(yrs):
        cx = padl + slot * i + slot / 2
        bh = plot_h * vals[i] / ymax
        by = Y(vals[i])
        parts.append(f'<rect x="{cx-bw/2:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                     f'rx="3" fill="#b91c1c"/>')
        parts.append(f'<text x="{cx:.1f}" y="{by-6:.1f}" text-anchor="middle" font-size="12" '
                     f'font-weight="800" fill="#b91c1c">−${vals[i]:.1f}M</text>')
        parts.append(f'<text x="{cx:.1f}" y="{H-padb+18}" text-anchor="middle" font-size="11.5" '
                     f'fill="#64748b">{yr}-{str(yr+1)[2:]}</text>')
    parts.append('</svg>')
    return "".join(parts)


def cushion_svg():
    """Horizontal comparison: current cash, 90-day target, and the recurring headwind."""
    W, rowh, gap, top, left, barmax, scale_max = 760, 44, 18, 16, 210, 470, 55
    rows = [
        ("90-day target (GFOA-ish)", CASH_DAYS[90], "#16a34a", "90 days net cash", "$52M"),
        ("What most districts hold", CASH_DAYS[90], "#86efac", "≈90 days", "$52M"),
        ("ICCSD today", CURRENT_CASH_M, "#dc2626", f"{CURRENT_DAYS} days net cash (FY2025)", "$18M"),
        ("Annual revenue headwind by 2030", headwind_2030 / 1e6, "#b45309",
         "recurring, every year", f"${headwind_2030/1e6:.1f}M"),
    ]
    H = top * 2 + len(rows) * rowh + (len(rows) - 1) * gap
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
             f'aria-label="Cushion vs headwind" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    for i, (label, val, color, note, vlabel) in enumerate(rows):
        y = top + i * (rowh + gap)
        bw = max(2, barmax * val / scale_max)
        parts.append(f'<text x="{left-10}" y="{y+rowh/2-2}" text-anchor="end" font-size="12.5" '
                     f'font-weight="700" fill="#0f172a">{label}</text>')
        parts.append(f'<text x="{left-10}" y="{y+rowh/2+13}" text-anchor="end" font-size="10.5" '
                     f'fill="#94a3b8">{note}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bw:.1f}" height="{rowh}" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{left+bw+8:.1f}" y="{y+rowh/2+5}" font-size="14" font-weight="800" '
                     f'fill="{color}">{vlabel}</text>')
    parts.append('</svg>')
    return "".join(parts)


def scenario_table():
    rows = ""
    for name in ["High", "Baseline", "Low"]:
        e2030 = SCEN_2030[name]
        drop = BASE_ENROLL - e2030
        hw = drop * PER_PUPIL / 1e6
        cls = ' style="background:#fef2f2"' if name == "Baseline" else ""
        rows += (f"<tr{cls}><td>{name}</td><td>{e2030:,}</td><td>−{drop:,}</td>"
                 f"<td>−${hw:.1f}M</td></tr>")
    return (f'<table class="dt"><tr><th>2030 scenario</th><th>K-12 enrollment</th>'
            f'<th>vs. 2025 ({BASE_ENROLL:,})</th><th>Annual revenue at ${PER_PUPIL:,}/student</th></tr>'
            f'{rows}</table>')


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Enrollment → Revenue Bridge — ICCSD</title>
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
.kpi.red .val{{color:#b91c1c}}
.kpi.blue .val{{color:#1e3a5f}}
.kpi.amber .val{{color:#b45309}}
.chart-box{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin:16px 0}}
.chart-box .title{{font-size:13px;font-weight:700;color:var(--mut);margin:0 0 12px;text-transform:uppercase;letter-spacing:.04em}}
.callout{{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:14px 16px;font-size:13.5px;color:#0c4a6e;margin:16px 0;max-width:760px}}
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
.steps{{counter-reset:step;max-width:760px;margin:14px 0}}
.step{{position:relative;padding:10px 0 10px 44px;border-bottom:1px solid #eef2f7}}
.step:before{{counter-increment:step;content:counter(step);position:absolute;left:0;top:10px;
  width:30px;height:30px;border-radius:50%;background:#1e3a5f;color:#fff;font-weight:800;
  font-size:14px;display:flex;align-items:center;justify-content:center}}
.step b{{color:#1e3a5f}}
{NAVCSS}
</style>
</head>
<body>
{NAV}
<div class="wrap">

<h1>From Fewer Students to Fewer Dollars</h1>
<p class="sub">Translating the K-12 enrollment forecast into a recurring revenue headwind —
and laying it against the district's cash cushion</p>

<div class="callout">
  <strong>Why this matters.</strong> Iowa funds districts on a per-pupil basis. ICCSD's own
  cohort-survival forecast projects roughly <strong>750 fewer students by 2030</strong> (Baseline).
  At the state foundation rate that is a <strong>recurring ~${headwind_2030/1e6:.1f}M/year</strong>
  hole in the operating budget — arriving while the district already runs one of the thinnest cash
  cushions of any large Iowa district.
</div>

<div class="kpi-row">
  <div class="kpi red"><div class="label">Projected enrollment decline by 2030</div>
    <div class="val">−{drop_2030:,}</div><div class="note">Baseline: {BASE_ENROLL:,} → {SCEN_2030['Baseline']:,} K-12</div></div>
  <div class="kpi amber"><div class="label">Recurring revenue headwind by 2030</div>
    <div class="val">~${headwind_2030/1e6:.1f}M/yr</div><div class="note">at ${PER_PUPIL:,}/student</div></div>
  <div class="kpi red"><div class="label">Current cash cushion</div>
    <div class="val">{CURRENT_DAYS} days</div><div class="note">≈${CURRENT_CASH_M}M GF · target 90+ days</div></div>
</div>

<h2>The bridge, in four steps</h2>
<div class="steps">
  <div class="step"><b>Enrollment falls ~{drop_2030:,} students</b> by 2030 under the Baseline
  scenario ({BASE_ENROLL:,} K-12 in 2025 → {SCEN_2030['Baseline']:,} in 2030). The decline is
  demographic — Johnson County births peaked in 2016 and feed smaller kindergarten classes.</div>
  <div class="step"><b>Each lost student removes ~${PER_PUPIL:,} of revenue.</b> Iowa's
  funding formula pays districts per pupil; fewer students means a smaller combined state-aid +
  property-tax foundation entitlement the following year.</div>
  <div class="step"><b>That compounds to a recurring ~${headwind_2030/1e6:.1f}M/year</b> shortfall
  by 2030 versus the 2025 revenue base — and roughly <b>${cum_dollars/1e6:.0f}M cumulative</b>
  ({cum_student_years:,} student-years) of foregone state aid over 2026–2030 as the decline phases in.</div>
  <div class="step"><b>It lands on a thin cushion.</b> ICCSD holds about {CURRENT_DAYS} days of net
  cash (≈${CURRENT_CASH_M}M in the General Fund) versus a 90-day target (≈${CASH_DAYS[90]}M). A
  recurring ${headwind_2030/1e6:.1f}M/year drain is roughly <b>a third of the district's entire
  current cash balance — every year.</b></div>
</div>

<h2>Annual revenue headwind vs. 2025 (Baseline)</h2>
<div class="chart-box">
  <div class="title">Foregone operating revenue, ${PER_PUPIL:,}/student · 2026–2030</div>
  {headwind_svg()}
</div>

<h2>It depends on the scenario — but every path is negative</h2>
{scenario_table()}
<p class="src">Enrollment from the ICCSD cohort-survival forecast (iccsd-enrollment-forecast.html),
K-12 BEDS basis. Per-pupil revenue uses the site-standard ${PER_PUPIL:,} all-in state foundation
figure; at the narrower regular-program district cost per pupil (~${PER_PUPIL_LOW:,}) the Baseline
headwind is about ${drop_2030*PER_PUPIL_LOW/1e6:.1f}M/year — still a structural drag.</p>

<h2>Against the cushion</h2>
<div class="chart-box">
  <div class="title">General-fund cash cushion vs. the recurring headwind ($M)</div>
  {cushion_svg()}
</div>
<p>The district is already ~${CASH_DAYS[90]-CURRENT_CASH_M}M below a 90-day cushion. A recurring
revenue decline doesn't just block rebuilding that cushion — left unmatched by spending reductions,
it <em>erodes</em> what little remains. This is why the enrollment forecast is a financial document,
not just a demographic one.</p>

<div class="callout warn">
  <strong>Bottom line.</strong> The ~{drop_2030:,}-student Baseline decline translates to a
  <strong>recurring ~${headwind_2030/1e6:.1f}M/year</strong> revenue headwind by 2030
  (range ~${headwind_low/1e6:.1f}M–${headwind_high/1e6:.1f}M across scenarios), against a General
  Fund holding only ~{CURRENT_DAYS} days of cash. Closing the gap requires either reversing the
  enrollment trend (largely demographic, hard to move) or cutting recurring operating costs by a
  comparable amount. Doing neither spends down a cushion that is already the thinnest among large
  Iowa districts.
</div>

<h2>Caveats</h2>
<ul style="max-width:760px">
  <li>Iowa's formula uses prior-year certified enrollment with a budget guarantee and a declining-
  enrollment supplement that soften single-year swings; the figures here are the gross per-pupil
  impact, not a line-item budget projection.</li>
  <li>Per-pupil revenue is an all-in approximation; categorical funding that scales with enrollment
  is included in the ${PER_PUPIL:,} figure, and a conservative ${PER_PUPIL_LOW:,} alternative is shown.</li>
  <li>The cushion translation (days → $M) uses the district's own General Fund benchmark table;
  the {CURRENT_DAYS}-day figure is the FY2025 all-funds Day's Net Cash ratio (adjusted).</li>
</ul>

<p style="margin-top:24px">
  <a href="iccsd-enrollment-forecast.html">→ The enrollment forecast behind these numbers</a><br>
  <a href="iccsd-cushion.html">→ Does ICCSD have a cushion? (the cash side)</a>
</p>

<p class="src">Sources: ICCSD cohort-survival enrollment forecast; Iowa DOE BEDS; Iowa school
foundation formula (state cost per pupil); ICCSD_FinancialHealth/Healthy Cash Levels.xlsx and
FY15-FY25 Summary.xlsx (Day's Net Cash). Built {OUT} via scripts/build_revenue_bridge.py.</p>

</div>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT} ({len(HTML):,} bytes)")
print(f"  drop_2030={drop_2030}, headwind={headwind_2030:,}, cum_sy={cum_student_years}, cum=${cum_dollars:,}")
