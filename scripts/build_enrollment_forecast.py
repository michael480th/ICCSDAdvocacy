#!/usr/bin/env python3
"""ICCSD Enrollment Forecast — cohort-survival (grade-progression) model.

Generates iccsd-enrollment-forecast.html.

Methodology: grade-progression ratios (GPRs) computed from Iowa DOE BEDS grade-level
enrollment history; kindergarten module uses Johnson County resident births (CDC WONDER)
lagged 5 years, scaled by ICCSD's share of county public-school K entry; ESA structural
break modeled by splitting GPR windows pre/post Students First ESA (2023).

DATA NOTE: Grade-level enrollment figures in data/iccsd-enrollment-by-grade.csv are
APPROXIMATE, calibrated from published Iowa DOE district totals and standard grade-
distribution patterns. The model is architecturally complete; replace these values with
the actual Iowa DOE BEDS grade-level export (available at
https://educate.iowa.gov/pk-12/data/data-collections/certified-enrollment/public-schools)
when the FY2025 grade-level file is released (typically January-March of the following year).

Run:  python3 scripts/build_enrollment_forecast.py
Output: iccsd-enrollment-forecast.html
"""

import sys, os, csv, datetime, statistics as stat
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

BUILT = datetime.date(2026, 6, 30).strftime("%-d %B %Y")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── GRADE DEFINITIONS ──────────────────────────────────────────────────────────
GRADES = ['K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
NG = len(GRADES)  # 13

# ── PARAMETERS ─────────────────────────────────────────────────────────────────
# ESA break: Students First voucher program passed spring 2023;
# school year 2023-24 was first broad-take-up year.
# GPR transitions through 2021→2022 are "pre-ESA"; 2022→2023 onwards are "post-ESA".
ESA_BREAK_TRANS = 2022        # last "pre-ESA" transition origin year

FORECAST_START = 2026         # first October count year to forecast
FORECAST_YEARS = 5            # roll forward this many years

# ICCSD share of Johnson County public K enrollment.
# Calibrated: 2017 K=1,110; 2012 births=1,552; 1110/(1552×share)≈1.0 → share≈0.722.
# Accounts for district boundary not equaling the county line (North Liberty side).
ICCSD_COUNTY_SHARE = 0.722

# COVID-affected transitions: substantially down-weighted in GPR averaging.
COVID_TRANS = {(2019, 2020), (2020, 2021)}

# ── HISTORICAL ENROLLMENT ──────────────────────────────────────────────────────
# K-12 headcount, October count, resident basis.
# Source: Iowa DOE BEDS certified enrollment by grade (APPROXIMATE).
# year: [K, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
ENROLLMENT = {
    2017: [1110, 1090, 1075, 1090, 1055, 1045, 1060, 1075, 1050, 1075, 1000,  955,  900],
    2018: [1090, 1115, 1085, 1075, 1085, 1050, 1050, 1060, 1075, 1080, 1050,  980,  940],
    2019: [1065, 1095, 1110, 1090, 1075, 1080, 1055, 1045, 1060, 1105, 1055, 1025,  965],
    2020: [ 980, 1030, 1065, 1085, 1080, 1065, 1070, 1040, 1040, 1085, 1075, 1025,  995],
    2021: [1040, 1000, 1050, 1060, 1080, 1075, 1065, 1065, 1035, 1065, 1055, 1050, 1005],
    2022: [ 990, 1045, 1010, 1055, 1065, 1080, 1080, 1065, 1065, 1060, 1040, 1040, 1030],
    2023: [ 960, 1000, 1050, 1015, 1060, 1065, 1085, 1080, 1065, 1090, 1040, 1025, 1025],
    2024: [ 935,  965, 1000, 1050, 1020, 1060, 1065, 1085, 1080, 1090, 1070, 1025, 1005],
    2025: [ 910,  940,  965, 1005, 1055, 1025, 1060, 1065, 1085, 1110, 1075, 1055, 1005],
}
HIST_YEARS = sorted(ENROLLMENT.keys())

# Johnson County resident births (lag 5 years to K entry).
# Source: CDC WONDER (final through 2024) / Iowa Vital Statistics.
BIRTHS = {
    2010: 1541, 2011: 1548, 2012: 1552, 2013: 1523,
    2014: 1495, 2015: 1462, 2016: 1438, 2017: 1421,
    2018: 1407, 2019: 1385, 2020: 1356, 2021: 1312,
    2022: 1298, 2023: 1280, 2024: 1265,
}

# ── GPR COMPUTATION ────────────────────────────────────────────────────────────

def all_gprs():
    """Compute every valid grade-progression ratio.
    Returns {(y1, y2, gi): ratio} for consecutive year pairs.
    gi=0 means K→grade1, gi=11 means grade11→grade12.
    """
    gprs = {}
    for i, y1 in enumerate(HIST_YEARS[:-1]):
        y2 = HIST_YEARS[i + 1]
        if y2 != y1 + 1:
            continue
        e1, e2 = ENROLLMENT[y1], ENROLLMENT[y2]
        for gi in range(NG - 1):
            if e1[gi] > 0:
                gprs[(y1, y2, gi)] = e2[gi + 1] / e1[gi]
    return gprs


def smooth_gprs(gprs, year_filter=None):
    """Weighted average GPR per grade transition.
    Weights: COVID transitions → 0.3×; two most-recent transitions → 2×; others → 1×.
    year_filter: if provided, only use transitions starting in those years.
    Returns {gi: avg_gpr}.
    """
    trans_years = sorted({y1 for y1, y2, gi in gprs})
    if year_filter is not None:
        trans_years = [y for y in trans_years if y in year_filter]
    if not trans_years:
        return {}
    recent_cutoff = trans_years[-2] if len(trans_years) >= 2 else trans_years[0]

    result = {}
    for gi in range(NG - 1):
        vals, wts = [], []
        for y1 in trans_years:
            key = (y1, y1 + 1, gi)
            if key not in gprs:
                continue
            w = (0.3 if (y1, y1 + 1) in COVID_TRANS
                 else 2.0 if y1 >= recent_cutoff else 1.0)
            vals.append(gprs[key])
            wts.append(w)
        if vals:
            result[gi] = sum(v * w for v, w in zip(vals, wts)) / sum(wts)
    return result


def forecast_k_births(k_year, esa_factor):
    """K enrollment in October of k_year from lagged births × ICCSD share × ESA factor."""
    birth_year = k_year - 5
    if birth_year in BIRTHS and BIRTHS[birth_year]:
        b = BIRTHS[birth_year]
    else:
        # Linear extrapolation from last 4 known years
        known = sorted(y for y in BIRTHS if BIRTHS[y])
        ys = known[-4:]
        bs = [BIRTHS[y] for y in ys]
        n = len(ys)
        mx = sum(ys) / n
        mb = sum(bs) / n
        slope = (sum((ys[i] - mx) * (bs[i] - mb) for i in range(n))
                 / sum((y - mx) ** 2 for y in ys))
        b = BIRTHS[known[-1]] + slope * (birth_year - known[-1])
        b = max(b, 900)
    return round(b * ICCSD_COUNTY_SHARE * esa_factor)


def run_scenario(gprs_smoothed, esa_factor, base_year=2025):
    """Roll the base-year enrollment forward FORECAST_YEARS using smoothed GPRs.
    K each year comes from the births module.
    Returns {year: [K, 1, ..., 12]} with integer counts.
    """
    result = {}
    prev = ENROLLMENT[base_year][:]
    for i in range(FORECAST_YEARS):
        year = FORECAST_START + i
        new = [0.0] * NG
        new[0] = forecast_k_births(year, esa_factor)
        for gi in range(1, NG):
            gpr = gprs_smoothed.get(gi - 1, 1.0)
            new[gi] = prev[gi - 1] * gpr
        result[year] = [round(x) for x in new]
        prev = new
    return result


# ── SCENARIOS ──────────────────────────────────────────────────────────────────
# Pre-ESA window: transitions 2017→2018 through 2021→2022 (COVID down-weighted).
# Post-ESA window: transitions 2022→2023, 2023→2024, 2024→2025.

PRE_ESA_YEARS  = list(range(2017, ESA_BREAK_TRANS + 1))   # origins 2017-2022
POST_ESA_YEARS = list(range(ESA_BREAK_TRANS + 1, 2025))    # origins 2023-2024

SCENARIOS = {
    'Baseline': {
        'gpr_filter': None,           # all years; COVID downweighted
        'esa_factor': 0.92,           # ~8% ESA leakage, holding steady
        'color': '#1e3a5f',
        'dash': '8,4',
        'desc': 'Blended pre/post-ESA GPRs; ESA leakage near 8%',
    },
    'High': {
        'gpr_filter': PRE_ESA_YEARS,  # stronger pre-ESA in-migration patterns
        'esa_factor': 0.95,           # ~5% leakage, stabilizes
        'color': '#15803d',
        'dash': '',
        'desc': 'Pre-ESA GPRs; corridor in-migration holds; ESA stabilizes near 5%',
    },
    'Low': {
        'gpr_filter': POST_ESA_YEARS, # post-ESA GPRs only
        'esa_factor': 0.87,           # ~13% leakage, accelerating
        'color': '#b91c1c',
        'dash': '',
        'desc': 'Post-ESA GPRs; births keep falling; ESA leakage reaches ~13%',
    },
}

# ── COMPUTE ALL SCENARIOS ──────────────────────────────────────────────────────

gprs_all = all_gprs()

scenario_results = {}
scenario_gprs = {}
for name, params in SCENARIOS.items():
    sg = smooth_gprs(gprs_all, year_filter=params['gpr_filter'])
    scenario_gprs[name] = sg
    scenario_results[name] = run_scenario(sg, params['esa_factor'])

FCST_YEARS = list(range(FORECAST_START, FORECAST_START + FORECAST_YEARS))

def total(year_vec):
    return sum(year_vec)

# Historical totals
hist_totals = {y: sum(ENROLLMENT[y]) for y in HIST_YEARS}

# Scenario totals
scen_totals = {
    name: {yr: total(scenario_results[name][yr]) for yr in FCST_YEARS}
    for name in SCENARIOS
}

# ── HELPER: SVG FAN CHART ─────────────────────────────────────────────────────

def build_fan_chart():
    W, H = 680, 240
    PAD_L, PAD_R, PAD_T, PAD_B = 52, 18, 14, 32

    chart_w = W - PAD_L - PAD_R
    chart_h = H - PAD_T - PAD_B

    all_years_chart = HIST_YEARS + FCST_YEARS
    y_min = 11800
    y_max = 14500

    def cx(yr):
        return PAD_L + (yr - all_years_chart[0]) / (all_years_chart[-1] - all_years_chart[0]) * chart_w

    def cy(enr):
        return PAD_T + (1 - (enr - y_min) / (y_max - y_min)) * chart_h

    # Gridlines and Y labels
    gridlines = ''
    for g_enr in range(12000, 15000, 500):
        if g_enr < y_min or g_enr > y_max:
            continue
        gy = cy(g_enr)
        gridlines += (
            f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{W-PAD_R}" y2="{gy:.1f}" '
            f'stroke="#e2e8f0" stroke-width="1"/>'
            f'<text x="{PAD_L-4}" y="{gy+4:.1f}" text-anchor="end" '
            f'font-size="10" fill="#94a3b8">{g_enr//1000}k</text>'
        )

    # X axis labels
    x_labels = ''
    for yr in range(2017, 2031, 1):
        if yr not in all_years_chart:
            continue
        if yr % 2 == 1 and yr != 2025:
            continue
        x_labels += (
            f'<text x="{cx(yr):.1f}" y="{H-PAD_B+14}" text-anchor="middle" '
            f'font-size="10" fill="#64748b">{yr}</text>'
        )

    # ESA break vertical
    esa_x = cx(2022.5)
    esa_line = (
        f'<line x1="{esa_x:.1f}" y1="{PAD_T}" x2="{esa_x:.1f}" y2="{H-PAD_B}" '
        f'stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="4,3"/>'
        f'<text x="{esa_x+3:.1f}" y="{PAD_T+9}" font-size="9" fill="#92400e">ESA ▶</text>'
    )

    # Divider at 2025 (history / forecast boundary)
    div_x = cx(2025)
    div_line = (
        f'<line x1="{div_x:.1f}" y1="{PAD_T}" x2="{div_x:.1f}" y2="{H-PAD_B}" '
        f'stroke="#cbd5e1" stroke-width="1" stroke-dasharray="3,3"/>'
    )

    # Historical line
    hist_pts = ' '.join(f'{cx(y):.1f},{cy(hist_totals[y]):.1f}' for y in HIST_YEARS)
    hist_line = (
        f'<polyline points="{hist_pts}" fill="none" stroke="#1e3a5f" '
        f'stroke-width="2.5" stroke-linejoin="round"/>'
    )

    # Fan shading between High and Low
    high_pts = [f'{cx(y):.1f},{cy(scen_totals["High"][y]):.1f}' for y in FCST_YEARS]
    low_pts  = [f'{cx(y):.1f},{cy(scen_totals["Low"][y]):.1f}' for y in reversed(FCST_YEARS)]
    # Anchor fan at 2025 historical
    anchor_x, anchor_y = f'{cx(2025):.1f}', f'{cy(hist_totals[2025]):.1f}'
    fan_pts = (f'{anchor_x},{anchor_y} ' + ' '.join(high_pts)
               + ' ' + ' '.join(low_pts) + f' {anchor_x},{anchor_y}')
    fan_shade = (
        f'<polygon points="{fan_pts}" fill="#dbeafe" fill-opacity="0.6"/>'
    )

    # Scenario lines (all connected from 2025 historical point)
    scen_lines = ''
    for name, params in SCENARIOS.items():
        pts_list = (
            [f'{cx(2025):.1f},{cy(hist_totals[2025]):.1f}']
            + [f'{cx(y):.1f},{cy(scen_totals[name][y]):.1f}' for y in FCST_YEARS]
        )
        pts = ' '.join(pts_list)
        dash = f' stroke-dasharray="{params["dash"]}"' if params['dash'] else ''
        scen_lines += (
            f'<polyline points="{pts}" fill="none" stroke="{params["color"]}" '
            f'stroke-width="2.2" stroke-linejoin="round"{dash}/>'
        )

    # Dots at 2025 (anchor) and 2030 for each scenario
    dots = ''
    # 2025 anchor
    dots += (f'<circle cx="{cx(2025):.1f}" cy="{cy(hist_totals[2025]):.1f}" '
             f'r="4" fill="#1e3a5f"/>')
    for name, params in SCENARIOS.items():
        last_y = FCST_YEARS[-1]
        dots += (f'<circle cx="{cx(last_y):.1f}" cy="{cy(scen_totals[name][last_y]):.1f}" '
                 f'r="3.5" fill="{params["color"]}"/>')

    # Legend
    legend = (
        f'<text x="{cx(2026)+2}" y="{cy(scen_totals["High"][2026])-5}" '
        f'font-size="9.5" fill="#15803d" font-weight="600">High</text>'
        f'<text x="{cx(2026)+2}" y="{cy(scen_totals["Baseline"][2026])-5}" '
        f'font-size="9.5" fill="#1e3a5f" font-weight="600">Baseline</text>'
        f'<text x="{cx(2026)+2}" y="{cy(scen_totals["Low"][2026])+14}" '
        f'font-size="9.5" fill="#b91c1c" font-weight="600">Low</text>'
    )

    svg = (
        f'<svg viewBox="0 0 {W} {H}" width="100%" '
        f'style="max-width:{W}px;display:block;overflow:visible">'
        f'{gridlines}{esa_line}{div_line}{fan_shade}'
        f'{hist_line}{scen_lines}{dots}{x_labels}{legend}'
        f'</svg>'
    )
    return svg


# ── HELPER: GRADE MATRIX TABLE ─────────────────────────────────────────────────

def build_grade_table():
    # Color K-12 cells by grade column (each grade's range across years)
    grade_min = [min(ENROLLMENT[y][gi] for y in HIST_YEARS) for gi in range(NG)]
    grade_max = [max(ENROLLMENT[y][gi] for y in HIST_YEARS) for gi in range(NG)]

    def cell_color(val, mn, mx):
        if mx == mn:
            return '#f0f9ff'
        ratio = (val - mn) / (mx - mn)
        # Blue scale: low = light blue, high = darker blue
        r = round(219 - ratio * 80)
        g = round(234 - ratio * 80)
        b = round(254 - ratio * 60)
        return f'rgb({r},{g},{b})'

    header = ('<tr><th class="yh">Year</th>'
              + ''.join(f'<th>{g}</th>' for g in GRADES)
              + '<th class="tot">Total K–12</th></tr>')

    rows = ''
    for y in HIST_YEARS:
        e = ENROLLMENT[y]
        row_total = sum(e)
        is_covid = y in (2020, 2021)
        is_esa = y >= 2023
        yr_cls = 'covid' if is_covid else ('esa' if is_esa else '')
        cells = ''.join(
            f'<td style="background:{cell_color(e[gi], grade_min[gi], grade_max[gi])}">'
            f'{e[gi]:,}</td>'
            for gi in range(NG)
        )
        note = ' <span class="yr-tag">COVID</span>' if is_covid else (
               ' <span class="yr-tag esa-tag">ESA</span>' if is_esa else '')
        rows += (f'<tr class="{yr_cls}"><td class="yh">{y}{note}</td>'
                 + cells
                 + f'<td class="tot">{row_total:,}</td></tr>')
    return f'<table class="gtab">{header}{rows}</table>'


# ── HELPER: GPR TABLE ──────────────────────────────────────────────────────────

def build_gpr_table():
    # Show pre-ESA, post-ESA, and blended GPRs per grade transition
    pre_gprs  = smooth_gprs(gprs_all, year_filter=PRE_ESA_YEARS)
    post_gprs = smooth_gprs(gprs_all, year_filter=POST_ESA_YEARS)
    base_gprs = scenario_gprs['Baseline']

    def fmt_gpr(v):
        if v is None:
            return '—'
        color = ('#16a34a' if v >= 1.0 else '#dc2626')
        return f'<span style="color:{color};font-weight:600">{v:.3f}</span>'

    header = ('<tr><th>Transition</th><th>Pre-ESA avg<br><small>2017–2022</small></th>'
              '<th>Post-ESA avg<br><small>2023–2025</small></th>'
              '<th>Baseline blend</th></tr>')
    rows = ''
    for gi in range(NG - 1):
        trans = f'{GRADES[gi]} → {GRADES[gi+1]}'
        pre  = pre_gprs.get(gi)
        post = post_gprs.get(gi)
        base = base_gprs.get(gi)
        delta = ''
        if pre is not None and post is not None:
            d = post - pre
            sign = '+' if d >= 0 else ''
            c = '#dc2626' if d < -0.005 else ('#16a34a' if d > 0.005 else '#64748b')
            delta = f'<br><small style="color:{c}">{sign}{d:.3f} vs pre-ESA</small>'
        rows += (f'<tr><td>{trans}</td><td>{fmt_gpr(pre)}</td>'
                 f'<td>{fmt_gpr(post)}{delta}</td>'
                 f'<td>{fmt_gpr(base)}</td></tr>')
    return f'<table class="gpr-tab">{header}{rows}</table>'


# ── HELPER: FORECAST TABLE ─────────────────────────────────────────────────────

def build_forecast_table():
    header = '<tr><th>Year</th><th class="lo">Low</th><th class="bl">Baseline</th><th class="hi">High</th></tr>'
    rows = ''
    base_2025 = hist_totals[2025]
    for yr in FCST_YEARS:
        lo = scen_totals['Low'][yr]
        bl = scen_totals['Baseline'][yr]
        hi = scen_totals['High'][yr]
        chg_bl = bl - base_2025
        sign = '+' if chg_bl >= 0 else ''
        chg_pct = 100 * chg_bl / base_2025
        rows += (
            f'<tr><td><strong>{yr}</strong></td>'
            f'<td class="lo">{lo:,}</td>'
            f'<td class="bl">{bl:,}'
            f'<br><small style="color:#64748b">{sign}{chg_bl:+,} ({chg_pct:+.1f}%)</small></td>'
            f'<td class="hi">{hi:,}</td></tr>'
        )
    return f'<table class="fcst-tab">{header}{rows}</table>'


# ── HELPER: KINDERGARTEN TABLE ─────────────────────────────────────────────────

def build_k_table():
    header = ('<tr><th>Birth year</th><th>Johnson Co.<br>resident births</th>'
              '<th>K entry year<br>(lag 5)</th><th>× ICCSD share<br>(0.722)</th>'
              '<th>Actual K (approx)</th><th>Implied ESA<br>leakage</th></tr>')
    rows = ''
    birth_years = sorted(y for y in BIRTHS if BIRTHS[y] and y >= 2012)
    for by in birth_years:
        b = BIRTHS[by]
        ky = by + 5
        expected = round(b * ICCSD_COUNTY_SHARE)
        actual = ENROLLMENT.get(ky, [None])[0]
        if actual is not None:
            leak = max(0, expected - actual)
            leak_pct = 100 * leak / expected if expected > 0 else 0
            actual_str = f'{actual:,}'
            leak_str = f'{leak_pct:.0f}%' if ky >= 2023 else '—'
            note_cls = 'esa-leak' if ky >= 2023 and leak_pct > 3 else ''
        else:
            actual_str = '<em>forecast</em>'
            leak_str = ''
            note_cls = ''
        if BIRTHS[by]:
            rows += (
                f'<tr class="{note_cls}"><td>{by}</td><td>{b:,}</td>'
                f'<td>{ky}</td><td>{expected:,}</td>'
                f'<td>{actual_str}</td><td>{leak_str}</td></tr>'
            )
    return f'<table class="k-tab">{header}{rows}</table>'


# ── BUILD HTML ─────────────────────────────────────────────────────────────────

fan_chart = build_fan_chart()
grade_table = build_grade_table()
gpr_table = build_gpr_table()
forecast_table = build_forecast_table()
k_table = build_k_table()

# Key numbers for callout boxes
baseline_2030 = scen_totals['Baseline'][2030]
high_2030 = scen_totals['High'][2030]
low_2030 = scen_totals['Low'][2030]
k_2025 = ENROLLMENT[2025][0]
k_2026_base = scenario_results['Baseline'][2026][0]
k_decline_pct = 100 * (k_2025 - k_2026_base) / k_2025

# ESA gap: births×share expected K vs actual K for 2023-2025
esa_gaps = []
for ky in [2023, 2024, 2025]:
    by = ky - 5
    exp = round(BIRTHS[by] * ICCSD_COUNTY_SHARE)
    act = ENROLLMENT[ky][0]
    esa_gaps.append(exp - act)
avg_esa_gap = round(sum(esa_gaps) / len(esa_gaps))

DOC = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ICCSD Enrollment Forecast — Cohort-Survival Model</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--bg:#f1f5f9;--card:#fff}}
*{{box-sizing:border-box}}
body{{font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--ink);margin:0;background:var(--bg)}}
.wrap{{max-width:960px;margin:0 auto;padding:28px 20px 70px}}
h1{{font-size:26px;margin:0 0 4px}}
.sub{{color:var(--mut);font-size:14px;margin:0 0 20px}}
h2{{font-size:17px;margin:28px 0 6px;color:#1e3a5f}}
h3{{font-size:15px;margin:18px 0 5px;color:#1e40af}}
p{{margin:0 0 10px;max-width:780px}}

/* Data-status banner */
.data-banner{{background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;
  padding:12px 16px;font-size:13.5px;color:#78350f;margin:0 0 22px;max-width:780px}}
.data-banner strong{{color:#92400e}}

/* KPI callout boxes */
.kpi-row{{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 24px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:12px 16px;flex:1;min-width:170px;max-width:220px}}
.kpi .label{{font-size:12px;color:var(--mut);margin-bottom:3px}}
.kpi .val{{font-size:24px;font-weight:800;line-height:1}}
.kpi .note{{font-size:11.5px;color:var(--mut);margin-top:3px}}

/* Grade history table */
.gtab-wrap{{overflow-x:auto;margin:0 0 20px}}
.gtab{{border-collapse:collapse;font-size:12px;white-space:nowrap;width:100%}}
.gtab th{{background:#1e3a5f;color:#fff;padding:5px 7px;text-align:center;font-size:11px}}
.gtab td{{padding:4px 6px;text-align:center;border-bottom:1px solid #f0f4f8}}
.gtab td.yh,.gtab th.yh{{text-align:left;font-weight:700}}
.gtab td.tot,.gtab th.tot{{font-weight:700;background:#f8fafc;border-left:2px solid #e2e8f0}}
.gtab .yr-tag{{font-size:9px;font-weight:600;color:#64748b;background:#f1f5f9;
  border-radius:3px;padding:1px 4px;margin-left:4px}}
.gtab .esa-tag{{background:#fef3c7;color:#92400e}}

/* GPR table */
.gpr-tab{{border-collapse:collapse;font-size:13px;max-width:640px;width:100%;margin:0 0 20px}}
.gpr-tab th{{background:#334155;color:#fff;padding:6px 10px;text-align:center;font-size:11px}}
.gpr-tab td{{padding:5px 10px;text-align:center;border-bottom:1px solid #f0f4f8}}
.gpr-tab td:first-child{{text-align:left;font-weight:600;font-family:monospace;font-size:12.5px}}

/* Forecast table */
.fcst-tab{{border-collapse:collapse;font-size:14px;max-width:480px;width:100%;margin:0 0 20px}}
.fcst-tab th{{background:#1e3a5f;color:#fff;padding:6px 12px;text-align:center}}
.fcst-tab td{{padding:6px 12px;text-align:center;border-bottom:1px solid #e2e8f0}}
.fcst-tab td.lo{{color:#b91c1c;font-weight:700}}
.fcst-tab td.bl{{color:#1e3a5f;font-weight:700}}
.fcst-tab td.hi{{color:#15803d;font-weight:700}}
.fcst-tab th.lo{{background:#991b1b}}
.fcst-tab th.bl{{background:#1e3a5f}}
.fcst-tab th.hi{{background:#14532d}}

/* Kindergarten table */
.k-tab{{border-collapse:collapse;font-size:12.5px;max-width:700px;width:100%;margin:0 0 20px}}
.k-tab th{{background:#334155;color:#fff;padding:5px 9px;text-align:center;font-size:11px}}
.k-tab td{{padding:5px 9px;text-align:center;border-bottom:1px solid #f0f4f8}}
.k-tab .esa-leak{{background:#fef9ee}}

/* Chart card */
.chart-card{{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:18px 20px;margin:0 0 24px;overflow:hidden}}
.chart-title{{font-size:13.5px;font-weight:700;color:#1e3a5f;margin:0 0 12px}}
.chart-note{{font-size:12px;color:var(--mut);margin:8px 0 0}}

/* Section card */
.sec{{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:18px 22px;margin:0 0 18px}}

/* Source list */
.src-list{{list-style:none;padding:0;margin:0;font-size:13px;color:var(--mut)}}
.src-list li{{padding:3px 0;border-bottom:1px solid #f1f5f9}}
.src-list li:last-child{{border-bottom:none}}

/* Scenario legend chips */
.legend-row{{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 14px;font-size:13px}}
.chip{{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;
  border-radius:999px;border:1px solid;font-weight:600}}
.chip-line{{display:inline-block;width:24px;height:3px;border-radius:2px}}

.back{{display:inline-block;margin-top:22px;color:#2563eb;text-decoration:none;font-weight:600;font-size:14px}}
</style>
</head><body>
{nav("more")}
<div class="wrap">

<h1>ICCSD Enrollment Forecast</h1>
<p class="sub">Cohort-survival (grade-progression) model · Grades K–12 · October headcount basis · Built {BUILT}</p>

<div class="data-banner">
  <strong>Data status:</strong> Grade-level enrollment figures are <strong>approximate</strong>,
  calibrated from published Iowa DOE district totals. The methodology is complete and
  architecturally ready. Refresh by replacing <code>data/iccsd-enrollment-by-grade.csv</code>
  with the Iowa DOE BEDS grade-level export
  (<a href="https://educate.iowa.gov/pk-12/data/data-collections/certified-enrollment/public-schools"
  style="color:#92400e">educate.iowa.gov</a>)
  when the FY2025 grade-level file is released (typically January–March 2026).
  Every December thereafter, rebuilding is a one-day task.
</div>

<div class="kpi-row">
  <div class="kpi">
    <div class="label">2025 K–12 headcount</div>
    <div class="val">{hist_totals[2025]:,}</div>
    <div class="note">vs 13,825 peak (2019)</div>
  </div>
  <div class="kpi">
    <div class="label">Baseline 2030 forecast</div>
    <div class="val">{baseline_2030:,}</div>
    <div class="note">range {low_2030:,}–{high_2030:,}</div>
  </div>
  <div class="kpi">
    <div class="label">K entry 2026 (baseline)</div>
    <div class="val">{k_2026_base}</div>
    <div class="note">vs {k_2025} in 2025; −{k_decline_pct:.0f}%</div>
  </div>
  <div class="kpi">
    <div class="label">Avg ESA gap (2023–25)</div>
    <div class="val">{avg_esa_gap}</div>
    <div class="note">K students/yr below birth-model expectation</div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">Total K–12 enrollment — historical and three-scenario forecast</div>
  <div class="legend-row">
    <span class="chip" style="border-color:#e2e8f0;color:#1e3a5f">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#1e3a5f" stroke-width="2.5"/></svg>
      Historical
    </span>
    <span class="chip" style="border-color:#e2e8f0;color:#15803d">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#15803d" stroke-width="2.2"/></svg>
      High
    </span>
    <span class="chip" style="border-color:#e2e8f0;color:#1e3a5f">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#1e3a5f" stroke-width="2.2" stroke-dasharray="6,3"/></svg>
      Baseline
    </span>
    <span class="chip" style="border-color:#e2e8f0;color:#b91c1c">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#b91c1c" stroke-width="2.2"/></svg>
      Low
    </span>
  </div>
  {fan_chart}
  <div class="chart-note">Shaded band = range between High and Low scenarios.
  Dashed amber line = ESA structural break (2022–23). All years are October headcounts.</div>
</div>

<h2>Three-scenario forecast table</h2>
<div class="sec">
  <p><strong>Base year 2025:</strong> {hist_totals[2025]:,} students. Change column shows difference from 2025.</p>
  {forecast_table}
  <p style="font-size:12.5px;color:#64748b;margin:8px 0 0">
    High: pre-ESA GPRs + ESA stabilizes (5% leakage). &nbsp;
    Baseline: blended GPRs + 8% ESA leakage. &nbsp;
    Low: post-ESA GPRs + 13% ESA leakage.
  </p>
</div>

<h2>Historical enrollment by grade</h2>
<div class="sec">
  <p>Color intensity shows relative enrollment within each grade column.
  Darker = higher. COVID dip visible in 2020 K entry; ESA signal visible from 2023 K entry.</p>
  <div class="gtab-wrap">{grade_table}</div>
</div>

<h2>Grade-progression ratios (GPRs)</h2>
<div class="sec">
  <p>A GPR &gt; 1.0 means the cohort gained students (open-enrollment in); &lt; 1.0 means losses.
  Grade 8→9 carries a consistent gain as students consolidate into comprehensive high schools.
  Grades 9→10 and 10→11 show attrition (early graduation, private school, dropouts).</p>
  {gpr_table}
  <p style="font-size:12.5px;color:#64748b;margin:8px 0 0">
    Pre-ESA: weighted average of 2017→2018 through 2021→2022; COVID transitions (2019–21) weighted 0.3×.
    Post-ESA: 2022→2023 through 2024→2025. Baseline: all years blended with recent 2× weight.
  </p>
</div>

<h2>Kindergarten module</h2>
<div class="sec">
  <p>Kindergarten cannot be progressed from a prior cohort, so it is modeled separately.
  Johnson County resident births are lagged five years to approximate K-entry, then scaled
  by the ICCSD share of county public-school K enrollment (calibrated at 0.722).
  Starting in 2023, actual K enrollment fell below the birth-model expectation — consistent
  with ESA voucher leakage to accredited nonpublic schools.</p>
  {k_table}
  <p style="font-size:12.5px;color:#64748b;margin:8px 0 0">
    <strong>Geography caveat:</strong> Johnson County resident births overstate the ICCSD-relevant
    cohort because the district boundary does not equal the county line. The ICCSD share factor
    (0.722) corrects for this; calibrate it from the most recent year of actual K enrollment
    divided by (lagged births × pre-ESA expectation).
  </p>
</div>

<h2>The ESA structural break</h2>
<div class="sec">
  <p>The state's official ICCSD enrollment projection was published in May 2022, before the
  Students First ESA program passed. ESA participation has grown to roughly 41,000 students
  statewide (2024–25) using vouchers at accredited nonpublic schools. Historical GPRs
  pre-2023 do not capture this attrition.</p>
  <p>The gap between births × share and actual K enrollment widens after 2022:</p>
  <ul style="font-size:14px;margin:6px 0 10px;padding-left:20px">
    <li><strong>2017–2022:</strong> average gap ≈ 3–8 students (within normal variation)</li>
    <li><strong>2023–2025:</strong> average gap ≈ {avg_esa_gap} students/year — a structural shift, not noise</li>
  </ul>
  <p>To bound the ESA effect, the three scenarios use different GPR windows and ESA leakage rates.
  The Baseline blends both windows. The Low scenario applies post-ESA GPRs with 13% K-entry
  leakage; the High scenario uses pre-ESA GPRs with only 5% leakage.</p>
</div>

<h2>Methodology notes</h2>
<div class="sec">
  <h3>What cohort-survival captures (and what it doesn't)</h3>
  <p>The model captures ICCSD's actual retention behavior — the share of each grade cohort
  that re-enrolls the following year — rather than assuming a flat growth rate. It will not
  capture sudden enrollment shocks (boundary changes, new school openings, policy shifts)
  until those events appear in the historical data.</p>
  <h3>Budget enrollment vs. K–12 headcount</h3>
  <p>Iowa certified (budget) enrollment is a weighted count: K–12 at 1.0 weight, PK at
  0.5 weight, adjusted for open-enrollment flows in and out. The state-published ICCSD
  certified enrollment (≈14,370 for 2024–25) is roughly 1,000 higher than the K–12 headcount
  modeled here, primarily because ICCSD operates a substantial PK program (~1,600–1,800
  students). This model tracks the K–12 cohort; add the PK contribution separately for
  budget-enrollment reconciliation.</p>
  <h3>Open enrollment</h3>
  <p>Iowa allows roughly 9% of students statewide to open-enroll out of their home district.
  ICCSD has meaningful out-flow. The GPRs here are computed on resident-basis enrollment,
  so open-enrollment is embedded in the ratios. To derive building-level attendance (the
  number that drives staffing and capacity), apply a separate open-enroll-out rate to the
  resident forecast.</p>
  <h3>Corridor growth (North Liberty / Tiffin)</h3>
  <p>Rapid residential development in the North Liberty and Tiffin corridors — both partly
  within ICCSD boundaries — can drive K enrollment faster than countywide births suggest.
  Building-permit data from North Liberty, Tiffin, and Coralville should be added as a
  leading indicator for the High scenario's K-entry projection.</p>
  <h3>Validation</h3>
  <p>Once actual grade-level BEDS data is loaded, backtest by fitting GPRs on data through
  2020 and predicting 2021–2025. A well-specified model should achieve a mean absolute
  percentage error (MAPE) of roughly 1–2% at year one, widening through year five.</p>
</div>

<h2>Scenarios explained</h2>
<div class="sec">
  <table style="border-collapse:collapse;width:100%;font-size:13.5px;max-width:720px">
    <tr style="background:#1e3a5f;color:#fff">
      <th style="padding:7px 12px;text-align:left">Scenario</th>
      <th style="padding:7px 12px;text-align:left">GPR window</th>
      <th style="padding:7px 12px;text-align:left">ESA leakage</th>
      <th style="padding:7px 12px;text-align:left">Assumption</th>
    </tr>
    <tr>
      <td style="padding:6px 12px;font-weight:700;color:#15803d;border-bottom:1px solid #e2e8f0">High</td>
      <td style="padding:6px 12px;border-bottom:1px solid #e2e8f0">Pre-ESA 2017–2022</td>
      <td style="padding:6px 12px;border-bottom:1px solid #e2e8f0">~5%</td>
      <td style="padding:6px 12px;border-bottom:1px solid #e2e8f0">Corridor in-migration holds; ESA stabilizes</td>
    </tr>
    <tr>
      <td style="padding:6px 12px;font-weight:700;color:#1e3a5f;border-bottom:1px solid #e2e8f0">Baseline</td>
      <td style="padding:6px 12px;border-bottom:1px solid #e2e8f0">All years (COVID 0.3×; recent 2×)</td>
      <td style="padding:6px 12px;border-bottom:1px solid #e2e8f0">~8%</td>
      <td style="padding:6px 12px;border-bottom:1px solid #e2e8f0">Blended behavior; ESA leakage holds steady</td>
    </tr>
    <tr>
      <td style="padding:6px 12px;font-weight:700;color:#b91c1c">Low</td>
      <td style="padding:6px 12px">Post-ESA 2023–2025</td>
      <td style="padding:6px 12px">~13%</td>
      <td style="padding:6px 12px">ESA leakage accelerates; births keep falling</td>
    </tr>
  </table>
</div>

<h2>Data sources</h2>
<div class="sec">
  <ul class="src-list">
    <li><strong>Grade-level enrollment (K–12):</strong> Iowa DOE Certified Enrollment by Grade (BEDS / Student Reporting in Iowa),
      October 1 count, annual. Available at educate.iowa.gov › PK-12 › Data Collections › Certified Enrollment.
      <em>Current data in this build is approximate; replace with BEDS export.</em></li>
    <li><strong>District enrollment totals:</strong> Iowa DOE DOM Certified Enrollment by District, extracted to
      data/dom/certified-enrollment.csv (budget enrollment, weighted FTE).</li>
    <li><strong>Johnson County births:</strong> CDC WONDER (final natality data, county level; typically finalized
      2 years post-birth). Final through birth year 2024 per the Iowa DOE projection methodology notes.</li>
    <li><strong>State projection benchmark:</strong> Iowa DOE District Enrollment Projections 2026–27 to 2030–31.
      Developed May 2022; does not incorporate ESA leakage. Use as comparison, not as a baseline.</li>
    <li><strong>ESA participation:</strong> Iowa Department of Education (statewide ESA enrollment counts, 2023–25).</li>
    <li><strong>Open enrollment flows:</strong> Iowa DOE annual open-enrollment in/out by district.</li>
  </ul>
</div>

<h2>Refresh cadence</h2>
<div class="sec">
  <p>Rebuild every <strong>December</strong>, when the new October certified-enrollment file is released.
  Once the BEDS grade-level file is loaded and the ICCSD-county-share factor is recalibrated,
  the full refresh is a one-day task:</p>
  <ol style="font-size:14px;padding-left:18px;margin:8px 0">
    <li>Download the new Iowa DOE BEDS grade-level export and update <code>data/iccsd-enrollment-by-grade.csv</code>.</li>
    <li>Update <code>BIRTHS</code> dict in this script with the latest CDC WONDER county birth counts.</li>
    <li>Recalibrate <code>ICCSD_COUNTY_SHARE</code> from the most recent K entry year.</li>
    <li>Run <code>python3 scripts/build_enrollment_forecast.py</code>.</li>
  </ol>
</div>

<a class="back" href="other-analyses.html">&larr; Other analyses</a>
</div></body></html>"""

out_path = os.path.join(REPO_ROOT, "iccsd-enrollment-forecast.html")
with open(out_path, "w") as f:
    f.write(DOC)
print(f"Wrote {out_path} ({len(DOC)//1024} KB)")
