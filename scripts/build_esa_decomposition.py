#!/usr/bin/env python3
"""Build iccsd-esa-decomposition.html from the ESA Private Study FINDINGS.md.

Self-contained page (inline SVG charts, no CDN dependency) mirroring the
neighboring-districts decomposition page. Central finding: ~78% of ESA users
were already private (inframarginal); defensible net public->private transfer
is ~120-190 students over three years (<1.5% of the district).
"""

OUT = "iccsd-esa-decomposition.html"

# ── Data (from ESA Private Study FINDINGS.md) ────────────────────────────────
# Resident pool, ICCSD boundary (Iowa DE district 3141)
YEARS = ["2022-23", "2023-24", "2024-25", "2025-26"]
PUBLIC = [14440, 14379, 14551, 14370]
PRIVATE = [1192, 1302, 1434, 1523]
ESA = [None, 471, 773, 1440]
# Private share of resident pool (private / (public+private))
SHARE = [round(100 * p / (p + pub), 1) for p, pub in zip(PRIVATE, PUBLIC)]

# Funnel: from headline ESA count to defensible transfer
ESA_TOTAL = 1440          # ICCSD-resident ESA users, 2025-26
INFRAMARGINAL = 1129      # already private (78%); ESA is a subsidy, no enrollment effect
EXCESS_PRIVATE = 311      # constant-share counterfactual upper bound on net movement
NEWLY_ACCRED = 136        # Montessori, Hillside, Tamarack entering certified count via accreditation
NET_TRANSFER = 175        # established-school growth (Regina +130, Faith +39)

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


def funnel_svg():
    """Horizontal funnel: 1,440 ESA users -> 311 excess private -> 175 net transfer."""
    W, rowh, gap, top, left, barmax = 760, 46, 16, 16, 250, 460
    rows = [
        ("All ICCSD-resident ESA users", ESA_TOTAL, "#64748b", "2025-26 headline count"),
        ("Already private (inframarginal)", INFRAMARGINAL, "#94a3b8", "~78% — subsidy, no enrollment effect"),
        ("Upper-bound net move to private", EXCESS_PRIVATE, "#f59e0b", "constant-share counterfactual"),
        ("…minus newly-accredited schools", NEWLY_ACCRED, "#cbd5e1", "already non-public students"),
        ("Defensible public→private transfer", NET_TRANSFER, "#dc2626", "Regina +130, Faith +39"),
    ]
    H = top * 2 + len(rows) * rowh + (len(rows) - 1) * gap
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
             f'aria-label="ESA decomposition funnel" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    for i, (label, val, color, note) in enumerate(rows):
        y = top + i * (rowh + gap)
        bw = max(2, barmax * val / ESA_TOTAL)
        parts.append(f'<text x="{left-10}" y="{y+rowh/2-2}" text-anchor="end" '
                     f'font-size="12.5" font-weight="700" fill="#0f172a">{label}</text>')
        parts.append(f'<text x="{left-10}" y="{y+rowh/2+13}" text-anchor="end" '
                     f'font-size="10.5" fill="#94a3b8">{note}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bw:.1f}" height="{rowh}" rx="4" fill="{color}"/>')
        tx = left + bw + 8
        parts.append(f'<text x="{tx:.1f}" y="{y+rowh/2+5}" font-size="14" font-weight="800" '
                     f'fill="{color}">{val:,}</text>')
    parts.append('</svg>')
    return "".join(parts)


def share_svg():
    """Line chart: private share of resident pool, 2022-23 -> 2025-26."""
    W, H, padl, padr, padt, padb = 760, 260, 48, 16, 20, 40
    plot_w, plot_h = W - padl - padr, H - padt - padb
    ymin, ymax = 6.0, 10.0
    n = len(YEARS)

    def X(i): return padl + plot_w * i / (n - 1)
    def Y(v): return padt + plot_h * (ymax - v) / (ymax - ymin)

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
             f'aria-label="Private share trend" font-family="-apple-system,Segoe UI,Roboto,sans-serif">']
    for gv in range(6, 11):
        gy = Y(gv)
        parts.append(f'<line x1="{padl}" y1="{gy:.1f}" x2="{W-padr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        parts.append(f'<text x="{padl-8}" y="{gy+4:.1f}" text-anchor="end" font-size="11" '
                     f'fill="#94a3b8">{gv}%</text>')
    for i, yr in enumerate(YEARS):
        parts.append(f'<text x="{X(i):.1f}" y="{H-padb+18}" text-anchor="middle" font-size="11.5" '
                     f'fill="#64748b">{yr}</text>')
    pts = " ".join(f"{X(i):.1f},{Y(SHARE[i]):.1f}" for i in range(n))
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#dc2626" stroke-width="3"/>')
    for i in range(n):
        parts.append(f'<circle cx="{X(i):.1f}" cy="{Y(SHARE[i]):.1f}" r="4" fill="#dc2626"/>')
        parts.append(f'<text x="{X(i):.1f}" y="{Y(SHARE[i])-10:.1f}" text-anchor="middle" '
                     f'font-size="11.5" font-weight="700" fill="#b91c1c">{SHARE[i]}%</text>')
    parts.append('</svg>')
    return "".join(parts)


def table_html():
    def row(label, vals, fmt="{:,}"):
        cells = "".join(f"<td>{fmt.format(v) if v is not None else '—'}</td>" for v in vals)
        return f"<tr><td>{label}</td>{cells}</tr>"
    head = "".join(f"<th>{y}</th>" for y in YEARS)
    return (f'<table class="dt"><tr><th>ICCSD-resident pool (dist 3141)</th>{head}</tr>'
            + row("Public certified", PUBLIC)
            + row("Private enrollment", PRIVATE)
            + row("Private share of pool", SHARE, "{}%")
            + row("ESA residents", ESA)
            + "</table>")


HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Is ESA Draining ICCSD Enrollment? — Decomposition</title>
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
ul{{max-width:760px}}
li{{margin:4px 0}}
{NAVCSS}
</style>
</head>
<body>
{NAV}
<div class="wrap">

<h1>Is ESA Draining ICCSD Enrollment?</h1>
<p class="sub">A decomposition of Education Savings Account use vs. actual public→private movement ·
ICCSD boundary (Iowa DE district 3141), 2022-23 → 2025-26</p>

<div class="callout">
  <strong>The question.</strong> ICCSD has 1,440 resident students using an Iowa Education Savings
  Account (ESA) voucher in 2025-26. A high ESA count is often read as proof that vouchers are
  pulling students out of public schools. But that only holds if those students <em>would have
  enrolled in ICCSD</em> without the program. How many actually would have?
</div>

<div class="kpi-row">
  <div class="kpi"><div class="label">ICCSD-resident ESA users (2025-26)</div>
    <div class="val">1,440</div><div class="note">headline voucher count</div></div>
  <div class="kpi green"><div class="label">Already private (inframarginal)</div>
    <div class="val">~78%</div><div class="note">≈1,130 students — no enrollment effect</div></div>
  <div class="kpi red"><div class="label">Defensible public→private transfer</div>
    <div class="val">~120–190</div><div class="note">over 3 years — &lt;1.5% of the district</div></div>
</div>

<h2>The funnel — from 1,440 vouchers to ~175 transfers</h2>
<p>The headline ESA count cannot, by itself, show a transfer. Most of it is the eligibility
phase-in (income-capped in 2023, universal by 2025) reaching families who were <strong>already in
private school</strong>. Stripping out the students who were never going to be in ICCSD leaves a
much smaller figure for genuine public→private movement.</p>
<div class="chart-box">
  <div class="title">ESA users → defensible transfers (2025-26)</div>
  {funnel_svg()}
</div>
<p class="src">Funnel logic from ESA_ICCSD_Decomposition.xlsx. "Upper-bound net move" = excess private
enrollment above what the pre-ESA private <em>share</em> would predict. "Newly-accredited schools"
= Montessori, Hillside, and the Tamarack microschool entering the certified count by getting
accredited for ESA — students already non-public.</p>

<h2>Why the count overstates the effect</h2>
<div class="chart-box">
  <div class="title">Private share of the resident school-age pool</div>
  {share_svg()}
</div>
<p>The private <em>share</em> of the ICCSD-resident pool rose from 7.6% to 9.6% over the ESA
period — real, but modest. Holding the pre-ESA share constant and applying it to each year's
resident pool, the "excess" private enrollment (the part not explained by population size) is
about <strong>+311 by 2025-26</strong>. That is the <em>upper bound</em> on would-be-public
families moving to private. Most of the 1,440 ESA users sit below this line — they were private
already.</p>

{table_html()}

<h2>Five reasons the hypothesis holds</h2>
<ul>
  <li><strong>ESA counts can't show transfer.</strong> The 471→1,440 ramp tracks the eligibility
  phase-in (income-capped → universal), not students moving.</li>
  <li><strong>Private enrollment grew only modestly.</strong> +331 over three years; the
  share-adjusted "excess" is +311, and ~136 of that is schools that simply got accredited.</li>
  <li><strong>The public side didn't crater.</strong> ICCSD public was roughly flat (−70) across
  the period; in 2024-25 it actually <em>rose</em> while ESA grew. No co-movement of
  public-down with ESA-up.</li>
  <li><strong>No new private capacity.</strong> No new K-12 private school opened in the ESA era;
  the only physical expansions (Regina's 2020 wing, 2021 early-childhood center) predate ESA.</li>
  <li><strong>The plateau predates ESA.</strong> Pre-ESA 2015-16 forecasts over-projected 2024-25
  by 1,100–1,800 students; the Nov-2023 forecast (just after ESA launched) was within ~200.
  Johnson County births peaked in 2016, feeding smaller kindergarten classes from ~2022 on.</li>
</ul>

<div class="callout warn">
  <strong>Bottom line.</strong> "ESA use is high, therefore it is lowering ICCSD enrollment" does
  not hold for Iowa City. ESA use is high mainly because families <em>already</em> in private
  school became eligible for a subsidy. The defensible public→private transfer attributable to
  ESA is on the order of <strong>120–190 students over three years (&lt;1.5% of the district)</strong> —
  small, concentrated at Regina, and not the driver of ICCSD's enrollment plateau. The plateau is
  demographic.
</div>

<h2>What would have changed the conclusion</h2>
<p>If private schools had grown sharply (new buildings, new K-12 schools, waitlists) <em>and</em>
ICCSD had fallen below its post-ESA demographic forecast at the same time, that would signal a real
mix shift. We don't see it: the private growth that occurred is modest and demographically
plausible, and the public count held.</p>

<h2>Caveats</h2>
<ul>
  <li>District-3141 private enrollment is a close proxy for, but not identical to, the ICCSD-resident
  ESA population (some residents attend out-of-area private; some boundary-private students are
  non-residents). Directional, not a census.</li>
  <li>The constant-share counterfactual is a simplification — we report a range, not a point.</li>
  <li>ESA-by-school-of-attendance and open-enrollment-by-receiving-district were not obtainable
  from public sources and would tighten the estimate.</li>
  <li>A cross-check supports the pool measurement: public + private (dist 3141) ≈ ACS school-age
  population each year, so homeschool/other is small.</li>
</ul>

<p style="margin-top:24px">
  <a href="iccsd-enrollment-decomposition.html">→ What's driving ICCSD enrollment? Full factor decomposition</a><br>
  <a href="iccsd-enrollment-forecast.html">→ ICCSD enrollment forecast (three scenarios)</a>
</p>

<p class="src">Source: Iowa DOE Certified Enrollment by District (public &amp; non-public, dist 3141),
2022-23 through 2025-26; Iowa Dept. of Education ESA program counts; ICCSD ESA Private Study
(ESA_ICCSD_Decomposition.xlsx, FINDINGS.md). Built {OUT} via scripts/build_esa_decomposition.py.</p>

</div>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT} ({len(HTML):,} bytes)")
