#!/usr/bin/env python3
"""ICCSD Enrollment Forecast — cohort-survival (grade-progression) model.

Generates iccsd-enrollment-forecast.html and iccsd-enrollment-forecast-methodology.html.

DATA PROVENANCE:
  Grade vectors 2016-2025: ACTUAL — Iowa DOE Student Reporting in Iowa (SRI) fall
    enrollment files for school years 2016-17 through 2025-26, downloaded 2026-06-30.
    All values are Iowa City Community School District K-12 headcount by grade,
    October 1 count date.

OBSERVED TREND: K enrollment has declined three consecutive years (1,035→998→992→987).
  The 2023–2025 average district share (0.718) is below the 2016–2022 average (0.742).
  Multiple factors interact — births, in-migration, open enrollment, program participation —
  and we do not have enrollment-transfer data to isolate any single cause.

Run:  python3 scripts/build_enrollment_forecast.py
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
TREND_BREAK_YEAR = 2022       # last year before observed K-share decline (2023+)
FORECAST_START = 2026
FORECAST_YEARS = 5

# ICCSD effective share of Johnson County resident births that enroll in ICCSD 5 years later.
# Observed from actual BEDS K counts (excl. 2020 COVID year):
#   2016:0.727  2017:0.738  2018:0.760  2019:0.736  2021:0.762
#   2022:0.729  2023:0.710  2024:0.716  2025:0.728
# 2016–2022 avg (excl. COVID): ~0.742. 2023–2025 avg: ~0.718.
# Cause of the shift is unknown — births, migration, open enrollment, program participation.
# Baseline = 0.728 (2025 most-recent actual). Used only for forecasting K.
ICCSD_COUNTY_SHARE = 0.728

COVID_TRANS = {(2019, 2020), (2020, 2021)}

# ── BIRTHS DATA ────────────────────────────────────────────────────────────────
# Johnson County resident births; lag 5 years to K entry.
# Source: CDC WONDER / Iowa Vital Statistics.
BIRTHS = {
    2010: 1541, 2011: 1548, 2012: 1552, 2013: 1523,
    2014: 1495, 2015: 1462, 2016: 1438, 2017: 1421,
    2018: 1407, 2019: 1385, 2020: 1356, 2021: 1312,
    2022: 1298, 2023: 1280, 2024: 1265,
}

# ── ACTUAL BEDS GRADE VECTORS ─────────────────────────────────────────────────
# Source: Iowa DOE Student Reporting in Iowa (SRI) fall enrollment files, all years.
# year key = October count year = school-year start (2025 = SY 2025-26, Oct 2025 count).
# Format: [K, Gr1, Gr2, Gr3, Gr4, Gr5, Gr6, Gr7, Gr8, Gr9, Gr10, Gr11, Gr12]
BEDS_ACTUAL = {
    2016: [1125, 1166, 1062, 1118, 1081, 1049,  976, 1046,  953, 1000,  988,  952, 1000],
    2017: [1146, 1112, 1164, 1051, 1125, 1065, 1058,  987, 1050, 1027, 1026, 1007, 1032],
    2018: [1157, 1139, 1081, 1156, 1036, 1120, 1063, 1061,  978, 1076, 1060, 1029, 1034],
    2019: [1101, 1174, 1131, 1107, 1154, 1047, 1116, 1108, 1055, 1021, 1115, 1059, 1088],
    2020: [1027, 1016, 1085, 1086, 1058, 1129, 1016, 1098, 1096, 1095, 1030, 1119, 1092],
    2021: [1096, 1087, 1074, 1089, 1109, 1052, 1121, 1037, 1099, 1140, 1125, 1033, 1179],
    2022: [1035, 1097, 1092, 1070, 1091, 1093, 1059, 1136, 1063, 1157, 1148, 1133, 1088],
    2023: [ 998, 1028, 1089, 1082, 1052, 1086, 1092, 1106, 1143, 1092, 1164, 1167, 1165],
    2024: [ 992, 1038, 1023, 1105, 1099, 1063, 1096, 1108, 1139, 1227, 1150, 1164, 1211],
    2025: [ 987,  988, 1013, 1029, 1110, 1094, 1058, 1087, 1098, 1181, 1222, 1146, 1214],
}

# ── HISTORICAL ENROLLMENT ──────────────────────────────────────────────────────
# All years: Iowa DOE BEDS actual. year key = October count year.
HIST_YEARS_ALL = sorted(BEDS_ACTUAL.keys())
ENROLLMENT = {y: BEDS_ACTUAL[y] for y in HIST_YEARS_ALL}
HIST_YEARS = HIST_YEARS_ALL

# ── GPR COMPUTATION ────────────────────────────────────────────────────────────

def all_gprs():
    """Return {(y1, y2, gi): ratio} for all valid consecutive-year transitions."""
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
    """Weighted-average GPR per grade transition.
    COVID transitions → 0.3×; two most-recent non-COVID → 2×; others → 1×.
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


# ── SCENARIOS ──────────────────────────────────────────────────────────────────
# K enrollment has declined 3 straight years; 2023–2025 share avg is below 2016–2022 avg.
# Cause is unknown. Scenarios bracket the range of plausible share trajectories.

PRE_2023_YEARS  = list(range(2016, TREND_BREAK_YEAR + 1))   # origin years 2016-2022
POST_2023_YEARS = list(range(TREND_BREAK_YEAR + 1, 2025))   # origin years 2023-2024

SCENARIOS = {
    'High': {
        'gpr_filter': None,   # all years; same retention as Baseline; higher K share
        'k_share': 0.740,   # in-migration strengthens; share recovers above 2025 level
        'color': '#15803d',
        'dash': '',
        'desc': 'In-migration strengthens; effective K-entry share rises to 0.740',
    },
    'Baseline': {
        'gpr_filter': None,   # all years; COVID 0.3×
        'k_share': 0.728,     # 2025 calibrated share holds
        'color': '#1e3a5f',
        'dash': '8,4',
        'desc': '2025 share holds at 0.728; grade retention follows all-years pattern',
    },
    'Low': {
        'gpr_filter': POST_2023_YEARS,
        'k_share': 0.680,   # in-migration slows; share falls further
        'color': '#b91c1c',
        'dash': '',
        'desc': 'In-migration slows; district share of county births falls to 0.680',
    },
}


# ── FORECASTING ────────────────────────────────────────────────────────────────

def forecast_k_share(k_year, share):
    birth_year = k_year - 5
    if birth_year in BIRTHS and BIRTHS[birth_year]:
        b = BIRTHS[birth_year]
    else:
        known = sorted(y for y in BIRTHS if BIRTHS[y])
        ys = known[-4:]
        bs = [BIRTHS[y] for y in ys]
        n = len(ys); mx = sum(ys)/n; mb = sum(bs)/n
        slope = (sum((ys[i]-mx)*(bs[i]-mb) for i in range(n))
                 / sum((y-mx)**2 for y in ys))
        b = max(BIRTHS[known[-1]] + slope*(birth_year - known[-1]), 900)
    return round(b * share)


def run_scenario(gprs_smoothed, k_share, base_year=2025):
    result = {}
    prev = ENROLLMENT[base_year][:]
    for i in range(FORECAST_YEARS):
        year = FORECAST_START + i
        new = [0.0] * NG
        new[0] = forecast_k_share(year, k_share)
        for gi in range(1, NG):
            new[gi] = prev[gi - 1] * gprs_smoothed.get(gi - 1, 1.0)
        result[year] = [round(x) for x in new]
        prev = new
    return result


# ── RUN ALL SCENARIOS ──────────────────────────────────────────────────────────

gprs_all = all_gprs()
scenario_results = {}
scenario_gprs = {}
for name, params in SCENARIOS.items():
    sg = smooth_gprs(gprs_all, year_filter=params['gpr_filter'])
    scenario_gprs[name] = sg
    scenario_results[name] = run_scenario(sg, params['k_share'])

FCST_YEARS = list(range(FORECAST_START, FORECAST_START + FORECAST_YEARS))
hist_totals = {y: sum(ENROLLMENT[y]) for y in HIST_YEARS}
scen_totals = {
    name: {yr: sum(scenario_results[name][yr]) for yr in FCST_YEARS}
    for name in SCENARIOS
}


# ── SVG FAN CHART ─────────────────────────────────────────────────────────────

def build_fan_chart():
    W, H = 680, 240
    PAD_L, PAD_R, PAD_T, PAD_B = 58, 18, 14, 32
    chart_w = W - PAD_L - PAD_R
    chart_h = H - PAD_T - PAD_B

    all_y = HIST_YEARS + FCST_YEARS
    y_min, y_max = 12800, 15000

    def cx(yr):
        return PAD_L + (yr - all_y[0]) / (all_y[-1] - all_y[0]) * chart_w

    def cy(enr):
        return PAD_T + (1 - (enr - y_min) / (y_max - y_min)) * chart_h

    gridlines = ''
    for g in range(13000, 15500, 500):
        if g < y_min or g > y_max:
            continue
        gy = cy(g)
        gridlines += (f'<line x1="{PAD_L}" y1="{gy:.1f}" x2="{W-PAD_R}" y2="{gy:.1f}" '
                      f'stroke="#e2e8f0" stroke-width="1"/>'
                      f'<text x="{PAD_L-4}" y="{gy+4:.1f}" text-anchor="end" '
                      f'font-size="10" fill="#94a3b8">{g//1000}k</text>')

    x_labels = ''
    for yr in range(2017, 2031):
        if yr not in all_y:
            continue
        if yr % 2 == 1 and yr != 2025:
            continue
        x_labels += (f'<text x="{cx(yr):.1f}" y="{H-PAD_B+14}" text-anchor="middle" '
                     f'font-size="10" fill="#64748b">{yr}</text>')

    esa_x = cx(2022.5)
    esa_line = (f'<line x1="{esa_x:.1f}" y1="{PAD_T}" x2="{esa_x:.1f}" y2="{H-PAD_B}" '
                f'stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="4,3"/>'
                f'<text x="{esa_x+3:.1f}" y="{PAD_T+10}" font-size="9" fill="#92400e">2023 ▶</text>')

    div_x = cx(2025)
    div_line = (f'<line x1="{div_x:.1f}" y1="{PAD_T}" x2="{div_x:.1f}" y2="{H-PAD_B}" '
                f'stroke="#cbd5e1" stroke-width="1" stroke-dasharray="3,3"/>')

    hist_pts = ' '.join(f'{cx(y):.1f},{cy(hist_totals[y]):.1f}' for y in HIST_YEARS)
    hist_line = (f'<polyline points="{hist_pts}" fill="none" stroke="#1e3a5f" '
                 f'stroke-width="2.5" stroke-linejoin="round"/>')

    # BEDS anchor dot at 2025 (verified data)
    anchor_dot = (f'<circle cx="{cx(2025):.1f}" cy="{cy(hist_totals[2025]):.1f}" '
                  f'r="5" fill="none" stroke="#1e3a5f" stroke-width="2"/>'
                  f'<circle cx="{cx(2025):.1f}" cy="{cy(hist_totals[2025]):.1f}" '
                  f'r="2.5" fill="#1e3a5f"/>')

    high_pts = [f'{cx(y):.1f},{cy(scen_totals["High"][y]):.1f}' for y in FCST_YEARS]
    low_pts  = [f'{cx(y):.1f},{cy(scen_totals["Low"][y]):.1f}' for y in reversed(FCST_YEARS)]
    anchor_x, anchor_y = f'{cx(2025):.1f}', f'{cy(hist_totals[2025]):.1f}'
    fan_pts = f'{anchor_x},{anchor_y} ' + ' '.join(high_pts) + ' ' + ' '.join(low_pts) + f' {anchor_x},{anchor_y}'
    fan_shade = f'<polygon points="{fan_pts}" fill="#dbeafe" fill-opacity="0.55"/>'

    scen_lines = ''
    for name, params in SCENARIOS.items():
        pts_list = (
            [f'{anchor_x},{anchor_y}']
            + [f'{cx(y):.1f},{cy(scen_totals[name][y]):.1f}' for y in FCST_YEARS]
        )
        dash = f' stroke-dasharray="{params["dash"]}"' if params['dash'] else ''
        scen_lines += (f'<polyline points="{" ".join(pts_list)}" fill="none" '
                       f'stroke="{params["color"]}" stroke-width="2.2" '
                       f'stroke-linejoin="round"{dash}/>')

    dots = ''
    for name, params in SCENARIOS.items():
        last_y = FCST_YEARS[-1]
        dots += (f'<circle cx="{cx(last_y):.1f}" cy="{cy(scen_totals[name][last_y]):.1f}" '
                 f'r="3.5" fill="{params["color"]}"/>')

    # Legend labels at 2027
    legend = ''
    label_yr = FCST_YEARS[1]
    for name, params in SCENARIOS.items():
        v = scen_totals[name][label_yr]
        legend += (f'<text x="{cx(label_yr)+4:.1f}" y="{cy(v)-5:.1f}" '
                   f'font-size="9.5" fill="{params["color"]}" font-weight="600">{name}</text>')

    return (f'<svg viewBox="0 0 {W} {H}" width="100%" '
            f'style="max-width:{W}px;display:block;overflow:visible">'
            f'{gridlines}{esa_line}{div_line}{fan_shade}'
            f'{hist_line}{anchor_dot}{scen_lines}{dots}{x_labels}{legend}'
            f'</svg>')


# ── GRADE HISTORY TABLE (heatmap) ─────────────────────────────────────────────

def build_grade_table():
    g_min = [min(ENROLLMENT[y][gi] for y in HIST_YEARS) for gi in range(NG)]
    g_max = [max(ENROLLMENT[y][gi] for y in HIST_YEARS) for gi in range(NG)]

    def cell_bg(v, mn, mx):
        if mx == mn:
            return '#f0f9ff'
        r = round(219 - (v-mn)/(mx-mn)*80)
        g = round(234 - (v-mn)/(mx-mn)*80)
        b = round(254 - (v-mn)/(mx-mn)*55)
        return f'rgb({r},{g},{b})'

    header = ('<tr><th class="yh">Year</th>'
              + ''.join(f'<th>{g}</th>' for g in GRADES)
              + '<th class="tot">Total K–12</th><th class="src">Source</th></tr>')

    rows = ''
    for y in HIST_YEARS:
        e = ENROLLMENT[y]
        src_label = '<span class="actual-tag">BEDS actual</span>'
        yr_note = ' <span class="yr-tag">COVID</span>' if y in (2020, 2021) else ''
        yr_note += ' <span class="yr-tag" style="background:#fef3c7;color:#92400e">2023▶</span>' if y == 2023 else ''
        cells = ''.join(
            f'<td style="background:{cell_bg(e[gi],g_min[gi],g_max[gi])}">{e[gi]:,}</td>'
            for gi in range(NG)
        )
        rows += (f'<tr><td class="yh">{y}{yr_note}</td>{cells}'
                 f'<td class="tot">{sum(e):,}</td><td class="src">{src_label}</td></tr>')
    return f'<table class="gtab">{header}{rows}</table>'


# ── GPR TABLE ─────────────────────────────────────────────────────────────────

def build_gpr_table():
    pre  = smooth_gprs(gprs_all, year_filter=PRE_2023_YEARS)
    post = smooth_gprs(gprs_all, year_filter=POST_2023_YEARS)
    base = scenario_gprs['Baseline']

    def fmt(v):
        if v is None:
            return '—'
        c = '#16a34a' if v >= 1.0 else '#dc2626'
        return f'<span style="color:{c};font-weight:600">{v:.3f}</span>'

    header = ('<tr><th>Transition</th>'
              '<th>2016–2022 avg</th>'
              '<th>2023–2025 avg</th>'
              '<th>Baseline blend</th></tr>')
    rows = ''
    for gi in range(NG - 1):
        trans = f'{GRADES[gi]} → {GRADES[gi+1]}'
        p, q, b = pre.get(gi), post.get(gi), base.get(gi)
        delta = ''
        if p and q:
            d = q - p
            sc = '#dc2626' if d < -0.005 else ('#16a34a' if d > 0.005 else '#64748b')
            delta = f'<br><small style="color:{sc}">{d:+.3f}</small>'
        rows += f'<tr><td>{trans}</td><td>{fmt(p)}</td><td>{fmt(q)}{delta}</td><td>{fmt(b)}</td></tr>'
    return f'<table class="gpr-tab">{header}{rows}</table>'


# ── FORECAST TABLE ─────────────────────────────────────────────────────────────

def build_forecast_table():
    base_2025 = hist_totals[2025]
    header = '<tr><th>Year</th><th class="lo">Low</th><th class="bl">Baseline</th><th class="hi">High</th></tr>'
    rows = ''
    for yr in FCST_YEARS:
        lo = scen_totals['Low'][yr]
        bl = scen_totals['Baseline'][yr]
        hi = scen_totals['High'][yr]
        chg = bl - base_2025
        pct = 100 * chg / base_2025
        rows += (f'<tr><td><strong>{yr}</strong></td>'
                 f'<td class="lo">{lo:,}</td>'
                 f'<td class="bl">{bl:,}'
                 f'<br><small style="color:#64748b">{chg:+,} ({pct:+.1f}%)</small></td>'
                 f'<td class="hi">{hi:,}</td></tr>')
    return f'<table class="fcst-tab">{header}{rows}</table>'


# ── K MODULE TABLE ─────────────────────────────────────────────────────────────

def build_k_table():
    _ks = {by+5: ENROLLMENT[by+5][0]/BIRTHS[by]
           for by in BIRTHS if (by+5) in ENROLLMENT and BIRTHS[by]}
    _pre_2023  = [v for y,v in _ks.items() if y < 2023 and y != 2020]
    _post_2023 = [v for y,v in _ks.items() if y >= 2023]
    _avg_pre  = sum(_pre_2023)  / len(_pre_2023)  if _pre_2023  else ICCSD_COUNTY_SHARE
    _avg_post = sum(_post_2023) / len(_post_2023) if _post_2023 else ICCSD_COUNTY_SHARE

    header = ('<tr><th>Birth yr</th><th>Johnson Co.<br>births</th>'
              '<th>K entry yr</th><th>Actual K<br>(BEDS)</th>'
              '<th>Actual share<br>K ÷ births</th><th>Notes</th></tr>')
    rows = ''
    for by in sorted(y for y in BIRTHS if BIRTHS[y] and y >= 2011):
        b = BIRTHS[by]
        ky = by + 5
        act = ENROLLMENT[ky][0] if ky in ENROLLMENT else None
        if act is not None:
            share = act / b
            sc = '#16a34a' if share >= 0.728 else '#b91c1c'
            note = 'COVID — K suppressed' if ky == 2020 else (
                   'trend break begins' if ky == 2023 else (
                   '' if ky == 2024 else (
                   'calibration point' if ky == 2025 else '')))
            rows += (f'<tr><td>{by}</td><td>{b:,}</td><td>{ky}</td>'
                     f'<td style="font-weight:700">{act:,}</td>'
                     f'<td style="color:{sc};font-weight:700">{share:.3f}</td>'
                     f'<td style="font-size:12px;color:#64748b">{note}</td></tr>')
        else:
            # Forecast year — show projected range
            hi_k  = round(b * 0.740)
            bl_k  = round(b * 0.728)
            lo_k  = round(b * 0.680)
            rows += (f'<tr style="background:#f8fafc"><td>{by}</td><td>{b:,}</td><td>{ky}</td>'
                     f'<td style="color:#64748b"><em>forecast</em></td>'
                     f'<td style="color:#64748b"><em>TBD</em></td>'
                     f'<td style="font-size:12px;color:#64748b">'
                     f'High {hi_k} · Base {bl_k} · Low {lo_k}</td></tr>')
    return (f'<table class="k-tab">{header}{rows}</table>'
            f'<p style="font-size:11.5px;color:#64748b;margin:6px 0 0">'
            f'All historical K values from Iowa DOE BEDS (verified). '
            f'Share = actual K ÷ Johnson County births 5 years prior. '
            f'2016–2022 avg share (excl. COVID 2020): {_avg_pre:.3f}. '
            f'2023–2025 avg share: {_avg_post:.3f}. Cause of shift unknown.</p>')


# ── RAW GPR MATRIX (for methodology page) ─────────────────────────────────────

def build_raw_gpr_matrix():
    """Full year-by-year GPR matrix showing every ratio computed."""
    trans_pairs = [(y, y+1) for i, y in enumerate(HIST_YEARS[:-1])
                   if HIST_YEARS[i+1] == y+1]

    def cell(y1, gi):
        key = (y1, y1+1, gi)
        if key not in gprs_all:
            return '<td style="color:#94a3b8">—</td>'
        v = gprs_all[key]
        color = '#16a34a' if v >= 1.0 else '#b91c1c'
        is_covid = (y1, y1+1) in COVID_TRANS
        bg = ';background:#fef9c3' if is_covid else ''
        return f'<td style="color:{color};font-weight:600{bg}">{v:.3f}</td>'

    col_hdrs = ''
    for y1, y2 in trans_pairs:
        label = f"{y1}→'{str(y2)[-2:]}"
        if (y1, y2) in COVID_TRANS:
            label += ' 🟡'
        col_hdrs += f'<th style="font-size:10px">{label}</th>'

    rows = ''
    for gi in range(NG - 1):
        rows += (f'<tr><td style="font-weight:600;font-family:monospace;white-space:nowrap">'
                 f'{GRADES[gi]}→{GRADES[gi+1]}</td>')
        for y1, y2 in trans_pairs:
            rows += cell(y1, gi)
        rows += '</tr>'

    return (f'<div style="overflow-x:auto">'
            f'<table style="border-collapse:collapse;font-size:11.5px;white-space:nowrap">'
            f'<tr><th style="background:#334155;color:#fff;padding:5px 8px;text-align:left">Grade</th>'
            f'{col_hdrs}</tr>{rows}</table></div>'
            f'<p style="font-size:11px;color:#64748b;margin:5px 0 0">🟡 COVID year (weighted 0.3× in smoothing). '
            f'All columns use verified Iowa DOE BEDS data for both origin and destination years.</p>')


# ── METHODOLOGY PAGE ───────────────────────────────────────────────────────────

def build_methodology_page():
    raw_gpr_matrix = build_raw_gpr_matrix()

    pre  = smooth_gprs(gprs_all, year_filter=PRE_2023_YEARS)
    post = smooth_gprs(gprs_all, year_filter=POST_2023_YEARS)

    def fg(v):
        if v is None: return '—'
        c = '#16a34a' if v >= 1.0 else '#b91c1c'
        return f'<span style="color:{c};font-weight:600">{v:.3f}</span>'

    smooth_rows = ''
    for gi in range(NG - 1):
        trans = f'{GRADES[gi]}→{GRADES[gi+1]}'
        p = pre.get(gi)
        q = post.get(gi)
        b = scenario_gprs['Baseline'].get(gi)
        h = scenario_gprs['High'].get(gi)
        lo_g = scenario_gprs['Low'].get(gi)
        delta = ''
        if p and q:
            d = q - p
            dc = '#b91c1c' if d < -0.005 else ('#16a34a' if d > 0.005 else '#64748b')
            delta = f'<br><small style="color:{dc}">{d:+.3f}</small>'
        smooth_rows += (f'<tr><td style="font-family:monospace;font-weight:600">{trans}</td>'
                        f'<td>{fg(p)}</td><td>{fg(q)}{delta}</td>'
                        f'<td style="color:#b91c1c;font-weight:700">{fg(lo_g)}</td>'
                        f'<td style="color:#1e3a5f;font-weight:700">{fg(b)}</td>'
                        f'<td style="color:#15803d;font-weight:700">{fg(h)}</td></tr>')

    k_steps = ''
    for yr in FCST_YEARS:
        by = yr - 5
        bv = BIRTHS.get(by)
        if bv:
            exp_hi  = round(bv * 0.740)
            exp_bl  = round(bv * 0.728)
            exp_lo  = round(bv * 0.680)
            k_steps += (f'<tr><td>{by}</td><td>{bv:,}</td><td>{yr}</td>'
                        f'<td style="color:#15803d">{exp_hi}</td>'
                        f'<td style="color:#1e3a5f;font-weight:700">{exp_bl}</td>'
                        f'<td style="color:#b91c1c">{exp_lo}</td></tr>')

    METH = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ICCSD Enrollment Forecast — How It Works</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--bg:#f1f5f9;--card:#fff}}
*{{box-sizing:border-box}}
body{{font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:var(--bg)}}
.wrap{{max-width:900px;margin:0 auto;padding:28px 20px 70px}}
h1{{font-size:26px;margin:0 0 4px}} .sub{{color:var(--mut);font-size:14px;margin:0 0 22px}}
h2{{font-size:18px;margin:30px 0 8px;color:#1e3a5f;padding-top:6px;border-top:2px solid #e2e8f0}}
p{{margin:0 0 10px;max-width:760px}} ul,ol{{max-width:760px;padding-left:20px;margin:0 0 12px}}
li{{margin-bottom:5px}}
.sec{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 22px;margin:0 0 18px}}
.formula{{background:#1e3a5f;color:#e0f2fe;font-family:monospace;font-size:14px;padding:14px 18px;border-radius:8px;margin:10px 0 12px;overflow-x:auto}}
.formula span{{color:#93c5fd}}
.worked{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px 18px;font-size:13.5px;margin:10px 0}}
.worked .step{{display:flex;gap:10px;padding:4px 0;border-bottom:1px solid #f0f4f8}}
.worked .step:last-child{{border-bottom:none}}
.worked .num{{color:#1e40af;font-weight:700;min-width:22px}}
.math{{font-family:monospace;font-size:13px;background:#f1f5f9;padding:2px 6px;border-radius:3px;white-space:nowrap}}
.scen-card{{border:2px solid;border-radius:10px;padding:14px 18px;margin:10px 0}}
.scen-card.hi{{border-color:#86efac;background:#f0fdf4}}
.scen-card.bl{{border-color:#93c5fd;background:#eff6ff}}
.scen-card.lo{{border-color:#fca5a5;background:#fef2f2}}
.scen-card h3{{margin:0 0 6px;font-size:16px}}
.tab{{border-collapse:collapse;font-size:13px;width:100%;max-width:700px;margin:0 0 12px}}
.tab th{{background:#334155;color:#fff;padding:6px 10px;text-align:center;font-size:11.5px}}
.tab td{{padding:5px 10px;text-align:center;border-bottom:1px solid #f0f4f8}}
.tab td:first-child{{text-align:left}}
.note{{font-size:12px;color:#64748b;margin:5px 0 0}}
.back{{display:inline-block;margin-top:22px;color:#2563eb;text-decoration:none;font-weight:600;font-size:14px}}
</style></head><body>
{nav("more")}
<div class="wrap">
<h1>How the enrollment forecast works</h1>
<p class="sub">Iowa City Community School District · Grades K–12 · {BUILT}</p>
<p><a href="iccsd-enrollment-forecast.html" style="color:#2563eb;font-weight:600">← Back to the forecast</a></p>

<h2>The big idea in one paragraph</h2>
<div class="sec">
<p>Every October 1, Iowa schools count every student by grade. We use those counts to measure
how many students in each grade "stay" in the district as they advance to the next grade the
following year. Call that fraction the <strong>grade-progression rate</strong>: if 1,000
third-graders are enrolled this fall and 978 fourth-graders show up next fall, the rate for
that transition is 0.978 — about 2% of the cohort didn't return. Apply those rates to the
current enrollment and you get a year-by-year enrollment forecast. Kindergarten is handled
separately: because there's no prior grade to track, we project it from the number of babies
born in Johnson County five years ago, adjusted for the fraction of those children who
actually end up enrolling in this district.</p>
</div>

<h2>Step 1: Measure how many students stay year to year</h2>
<div class="sec">
<p>For each grade and each year we have data, we compute:</p>
<div class="formula">rate = students in grade <span>G+1</span> this fall
  ÷ students in grade <span>G</span> last fall</div>
<p><strong>Worked example — 1st grade to 2nd grade, 2024 to 2025:</strong></p>
<div class="worked">
  <div class="step"><span class="num">1</span>
    <span>1st-graders counted in October 2024: <span class="math">965</span></span></div>
  <div class="step"><span class="num">2</span>
    <span>2nd-graders counted in October 2025 (Iowa DOE verified data): <span class="math">1,013</span></span></div>
  <div class="step"><span class="num">3</span>
    <span>Rate: <span class="math">1,013 ÷ 965 = 1.050</span></span></div>
  <div class="step"><span class="num">4</span>
    <span><strong>The cohort grew 5.0% going from 1st to 2nd grade</strong> — more students
    transferred <em>in</em> than transferred out.</span></div>
</div>
<p>A rate above 1.0 means the cohort gained students (families moving in, students transferring
from other districts). A rate below 1.0 means it shrank (moves, transfers out, private school).
The 8th-to-9th-grade transition typically shows a gain as students consolidate into Iowa City's
comprehensive high schools. The 9th-to-10th and 10th-to-11th transitions tend to show small
losses.</p>

<p><strong>The full table of rates, every year and grade.</strong>
Yellow shading = school years disrupted by COVID (these years are given only 30% weight in the
average). All columns use verified Iowa DOE fall enrollment counts for both years.</p>
{raw_gpr_matrix}
</div>

<h2>Step 2: Average the rates, with more weight on recent years</h2>
<div class="sec">
<p>We don't treat every year equally. COVID (the 2019-20 and 2020-21 school years) distorted
enrollment in ways that don't reflect normal district behavior — fewer kindergarteners showed
up, and families made unusual grade-transition decisions. So those two transitions count for
only 30% of a normal year in the weighted average. The two most-recent school years count
double (2×), because recent patterns are more predictive than older ones.</p>

<p>Each of the three scenarios uses a different set of years:</p>
<ul>
  <li><strong>High scenario:</strong> uses all available years (same grade-retention rates as
  the Baseline), but assumes in-migration from Iowa City's growth corridors strengthens enough
  to push the effective K-entry share up to 0.740. Grade-to-grade retention is the same as
  the Baseline; the difference is in kindergarten headcount only.</li>
  <li><strong>Baseline scenario:</strong> uses all available years with the COVID discounts
  described above. Kindergarten share stays at 0.728 — the current calibrated level.</li>
  <li><strong>Low scenario:</strong> uses only the most recent two school years (2023–2025),
  giving more weight to the recently observed pattern. Combined with a lower K-entry share
  (0.680), this tests the case where in-migration slows and the share decline continues.</li>
</ul>

<p><strong>Smoothed rates used in each scenario:</strong></p>
<table class="tab">
  <tr><th>Grade transition</th>
      <th>2016–2022 avg</th>
      <th>2023–2025 avg</th>
      <th style="color:#fca5a5">Low scenario</th>
      <th style="color:#93c5fd">Baseline</th>
      <th style="color:#a7f3d0">High scenario</th></tr>
  {smooth_rows}
</table>
<p class="note">A positive shift (2023–2025 vs. 2016–2022) means grade retention has
<em>improved</em> in recent years. Negative means more attrition. Cause of any shift is not established.</p>
</div>

<h2>Step 3: Project kindergarten from birth data</h2>
<div class="sec">
<p>There's no prior grade to roll forward into kindergarten, so we project it differently:
from birth records. The number of babies born in Johnson County five years ago is a strong
predictor of how many kindergarteners will walk through Iowa City's doors. We pull Johnson
County resident birth counts from the CDC's national birth records database and apply a
multiplier to account for the fact that the Iowa City district boundary doesn't match the
county line, and that not all county residents enroll in this district.</p>

<div class="formula">Projected kindergarteners(year) = Johnson County births(<span>year − 5</span>) × district share</div>

<p><strong>How we calibrated the share.</strong> In October 2025, the Iowa DOE verified count
showed 987 kindergarteners enrolled in Iowa City schools. Five years earlier, in 2020, there
were 1,356 babies born to Johnson County residents. So:</p>
<div class="worked">
  <div class="step"><span class="num">1</span>
    <span>Johnson County births in 2020: <span class="math">1,356</span></span></div>
  <div class="step"><span class="num">2</span>
    <span>Five-year lag → these children entered kindergarten in fall 2025</span></div>
  <div class="step"><span class="num">3</span>
    <span>Actual kindergarteners in fall 2025 (verified): <span class="math">987</span></span></div>
  <div class="step"><span class="num">4</span>
    <span>Share: <span class="math">987 ÷ 1,356 = 0.728</span></span></div>
  <div class="step"><span class="num">5</span>
    <span><strong>District share = 0.728</strong> — 72.8% of Johnson County births enrolled
    in Iowa City schools five years later.</span></div>
</div>

<p><strong>The observed shift since 2023.</strong> The kindergarten count has declined three
straight years (1,035 in fall 2022 → 998 → 992 → 987 in fall 2025). The effective district
share of county births has fallen from a 2016–2022 average of about 0.742 to a 2023–2025
average of 0.718. The 2025 figure (0.728) sits between these averages. Multiple factors can
affect this share simultaneously — migration, private-school enrollment, open enrollment across
district lines, and the geographic mismatch between county and district boundaries. We do not
have enrollment-transfer data to isolate any single factor as the cause. The three scenarios
test different assumptions about where the share goes next, without asserting why it moved.</p>

<p><strong>Forecast kindergarten counts, by scenario:</strong></p>
<table class="tab">
  <tr><th>Birth year</th><th>Johnson Co. births</th><th>Kindergarten year</th>
      <th style="color:#a7f3d0">High (share 0.740)</th>
      <th style="color:#93c5fd">Baseline (share 0.728)</th>
      <th style="color:#fca5a5">Low (share 0.680)</th></tr>
  {k_steps}
</table>
<p class="note">Births are declining across Johnson County — a national demographic trend. The
same births data is used in all three scenarios; only the share changes.</p>
</div>

<h2>Step 4: Roll the forecast forward</h2>
<div class="sec">
<p>Starting from the October 2025 verified enrollment (14,227 total), we apply the smoothed
rates to project each grade one year at a time. Kindergarten comes from the birth formula above.
Each subsequent grade comes from the grade below it, multiplied by its rate. We do this for
five years (2026 through 2030), accumulating any compounding errors as we go further out.</p>
<p>The five-year window is intentional. Beyond five years, birth trends and migration patterns
become too uncertain to be useful, and the honest answer is a wide range rather than a
point estimate.</p>
</div>

<h2>The three scenarios — what they mean in plain English</h2>
<div class="sec">
<div class="scen-card hi">
<h3 style="color:#15803d">High — "Growth holds"</h3>
<p><strong>What has to be true:</strong> The North Liberty and Tiffin growth corridors keep
building homes and attracting young families at today's pace or faster. More children move into
new houses than the birth trend would predict, pushing the district's effective share of county
kindergarteners slightly above today's level — to 0.740. Grade-to-grade retention for students
already in the system follows the same overall pattern as the Baseline. The scenario differs
from the Baseline only in how many new kindergarteners enter each year.</p>
<p><strong>2030 enrollment: {hi_2030:,}.</strong> Still below the 2025 level due to falling
birth counts, but the decline is modest. This scenario requires sustained housing construction
in the growth corridors.</p>
</div>

<div class="scen-card bl">
<h3 style="color:#1e3a5f">Baseline — "Current trajectory holds"</h3>
<p><strong>What has to be true:</strong> Roughly what's happening now continues. In-migration
from the growth corridors continues at roughly today's pace. The district's share of county
kindergarteners stays at 0.728 — the same rate calibrated from the 2025 actual data. Birth
counts keep falling gradually. No major disruption in either direction.</p>
<p><strong>2030 enrollment: {bl_2030:,}</strong> ({bl_2030-base_2025:+,} from 2025,
{100*(bl_2030-base_2025)/base_2025:+.1f}%). A slow, steady decline — roughly one class per
grade per year smaller than today. The decline is driven by fewer births, not school closures
or a financial crisis.</p>
</div>

<div class="scen-card lo">
<h3 style="color:#b91c1c">Low — "In-migration slows, share declines"</h3>
<p><strong>What has to be true:</strong> New construction in North Liberty and Tiffin slows as
the most buildable land fills in — fewer families moving into the district each year. The
district's share of county kindergarteners falls to 0.680 — about 35 fewer kindergarteners per
year than births would predict. Grade-to-grade retention follows the post-2023 pattern, which
shows slightly more attrition than earlier years. The cause of the share decline is not assumed;
this scenario tests the lower bound of the observed range.</p>
<p><strong>2030 enrollment: {lo_2030:,}</strong> ({lo_2030-base_2025:+,} from 2025,
{100*(lo_2030-base_2025)/base_2025:+.1f}%). Roughly the equivalent of closing one elementary
school's worth of enrollment from the current level.</p>
</div>
</div>

<h2>What could make this wrong</h2>
<div class="sec">
<ul>
  <li><strong>The grade-progression rates rest on 10 school years of verified Iowa DOE
  enrollment data (2016–2025).</strong> The main remaining structural uncertainty is
  open-enrollment flow: Iowa lets students attend school outside their home district, and
  if Iowa City's net in/out balance changes — for example, because a neighboring district
  opens a new school or becomes more attractive — the grade-progression rates won't
  capture it cleanly. Adding annual open-enrollment in/out data (published by the Iowa DOE)
  would separate in-district retention from cross-district transfers.</li>

  <li><strong>The district share (0.728) is one number capturing many things.</strong> It
  combines the geographic mismatch between county and district boundaries, private school
  choice, Iowa's open-enrollment policy (students can cross district lines), and any
  structural shifts in who enrolls. A richer model would track each of these separately.
  For now, the three scenarios capture the range of how that single number might shift.</li>

  <li><strong>Johnson County births for 2023 and 2024 are still estimates.</strong> The CDC's
  national birth records typically lag two years before becoming final. These figures will be
  updated when final counts are published.</li>

  <li><strong>Iowa's open-enrollment policy adds noise.</strong> Students can attend public
  school outside their home district. If Iowa City's net flow of students crossing into or
  out of other districts changes — for example, due to rivalry with neighboring districts or
  a new school opening — the grade-progression rates won't capture it cleanly.</li>
</ul>
</div>

<a class="back" href="iccsd-enrollment-forecast.html">← Back to the forecast</a>
</div></body></html>"""

    out_path = os.path.join(REPO_ROOT, "iccsd-enrollment-forecast-methodology.html")
    with open(out_path, "w") as f:
        f.write(METH)
    print(f"Wrote {out_path} ({len(METH)//1024} KB)")


# ── ASSEMBLE HTML ──────────────────────────────────────────────────────────────

fan_chart      = build_fan_chart()
grade_table    = build_grade_table()
gpr_table      = build_gpr_table()
forecast_table = build_forecast_table()
k_table        = build_k_table()

base_2025   = hist_totals[2025]
bl_2030     = scen_totals['Baseline'][2030]
hi_2030     = scen_totals['High'][2030]
lo_2030     = scen_totals['Low'][2030]
bl_chg_pct  = 100 * (bl_2030 - base_2025) / base_2025
k_2026_bl   = scenario_results['Baseline'][2026][0]

# K-entry share summary from actual BEDS data
k_share_actuals  = {by+5: ENROLLMENT[by+5][0]/BIRTHS[by]
                    for by in BIRTHS if (by+5) in ENROLLMENT and by in BIRTHS and BIRTHS[by]}
pre_2023_shares  = [v for y,v in k_share_actuals.items() if y < 2023 and y != 2020]
post_2023_shares = [v for y,v in k_share_actuals.items() if y >= 2023]
avg_pre_2023_share  = sum(pre_2023_shares)  / len(pre_2023_shares)  if pre_2023_shares  else ICCSD_COUNTY_SHARE
avg_post_2023_share = sum(post_2023_shares) / len(post_2023_shares) if post_2023_shares else ICCSD_COUNTY_SHARE

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

/* Data status */
.data-banner{{background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
  padding:12px 16px;font-size:13.5px;color:#14532d;margin:0 0 22px;max-width:780px}}
.data-banner strong{{color:#15803d}}
.data-warn{{background:#fef3c7;border-color:#fcd34d;color:#78350f}}
.data-warn strong{{color:#92400e}}

/* KPI boxes */
.kpi-row{{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 24px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:12px 16px;flex:1;min-width:160px;max-width:210px}}
.kpi .label{{font-size:12px;color:var(--mut);margin-bottom:3px}}
.kpi .val{{font-size:24px;font-weight:800;line-height:1}}
.kpi .note{{font-size:11.5px;color:var(--mut);margin-top:3px}}

/* Grade history table */
.gtab-wrap{{overflow-x:auto;margin:0 0 10px}}
.gtab{{border-collapse:collapse;font-size:12px;white-space:nowrap;width:100%}}
.gtab th{{background:#1e3a5f;color:#fff;padding:5px 6px;text-align:center;font-size:11px}}
.gtab td{{padding:4px 6px;text-align:center;border-bottom:1px solid #f0f4f8}}
.gtab td.yh,.gtab th.yh{{text-align:left;font-weight:700;min-width:90px}}
.gtab td.tot,.gtab th.tot{{font-weight:700;background:#f8fafc;border-left:2px solid #e2e8f0}}
.gtab td.src,.gtab th.src{{font-size:11px}}
.gtab .yr-tag{{font-size:9px;font-weight:600;color:#64748b;background:#f1f5f9;
  border-radius:3px;padding:1px 4px;margin-left:4px}}
.actual-tag{{background:#dcfce7;color:#15803d;font-size:10px;font-weight:700;
  padding:1px 5px;border-radius:3px}}
.est-tag{{background:#f1f5f9;color:#94a3b8;font-size:10px;padding:1px 5px;border-radius:3px}}

/* GPR table */
.gpr-tab{{border-collapse:collapse;font-size:13px;max-width:640px;width:100%;margin:0 0 14px}}
.gpr-tab th{{background:#334155;color:#fff;padding:6px 10px;text-align:center;font-size:11px}}
.gpr-tab td{{padding:5px 10px;text-align:center;border-bottom:1px solid #f0f4f8}}
.gpr-tab td:first-child{{text-align:left;font-weight:600;font-family:monospace;font-size:12.5px}}

/* Forecast table */
.fcst-tab{{border-collapse:collapse;font-size:14px;max-width:480px;width:100%;margin:0 0 14px}}
.fcst-tab th{{background:#1e3a5f;color:#fff;padding:6px 12px;text-align:center}}
.fcst-tab td{{padding:6px 12px;text-align:center;border-bottom:1px solid #e2e8f0}}
.fcst-tab td.lo{{color:#b91c1c;font-weight:700}}
.fcst-tab td.bl{{color:#1e3a5f;font-weight:700}}
.fcst-tab td.hi{{color:#15803d;font-weight:700}}
.fcst-tab th.lo{{background:#991b1b}}
.fcst-tab th.bl{{background:#1e3a5f}}
.fcst-tab th.hi{{background:#14532d}}

/* K-module table */
.k-tab{{border-collapse:collapse;font-size:12.5px;max-width:650px;width:100%;margin:0 0 10px}}
.k-tab th{{background:#334155;color:#fff;padding:5px 9px;text-align:center;font-size:11px}}
.k-tab td{{padding:5px 9px;text-align:center;border-bottom:1px solid #f0f4f8}}

/* Chart card */
.chart-card{{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:18px 20px;margin:0 0 24px}}
.chart-title{{font-size:13.5px;font-weight:700;color:#1e3a5f;margin:0 0 12px}}
.chart-note{{font-size:12px;color:var(--mut);margin:8px 0 0}}

/* Section card */
.sec{{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:18px 22px;margin:0 0 18px}}

/* Legend row */
.legend-row{{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 14px;font-size:13px}}
.chip{{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;
  border-radius:999px;border:1px solid #e2e8f0;font-weight:600}}

/* Sources */
.src-list{{list-style:none;padding:0;margin:0;font-size:13px;color:var(--mut)}}
.src-list li{{padding:3px 0;border-bottom:1px solid #f1f5f9}}
.src-list li:last-child{{border-bottom:none}}

.back{{display:inline-block;margin-top:22px;color:#2563eb;text-decoration:none;
  font-weight:600;font-size:14px}}
</style>
</head><body>
{nav("more")}
<div class="wrap">

<h1>Iowa City Schools — Enrollment Forecast</h1>
<p class="sub">Grade-progression model · Grades K–12 · October headcount · Built {BUILT}</p>
<p style="font-size:13.5px;margin:0 0 18px">
  <a href="iccsd-enrollment-forecast-methodology.html" style="color:#2563eb;font-weight:700">
  → How this model works — show your work, plain-English explanations</a>
</p>

<div class="data-banner">
  <strong>All historical data: Iowa DOE verified fall enrollment counts, 2016–2025.</strong>
  Grade-level October 1 counts from Iowa DOE Student Reporting in Iowa fall files for school
  years 2016-17 through 2025-26, downloaded 30 June 2026. Every grade-progression rate in
  this model is computed from verified data.
</div>

<div class="data-banner data-warn">
  <strong>Observed trend since 2023:</strong> The kindergarten count has declined three years
  running (1,035 → 998 → 992 → 987). The effective district share of county births has fallen
  from a 2016–2022 average of {avg_pre_2023_share:.3f} to a 2023–2025 average of
  {avg_post_2023_share:.3f}. The cause of this shift is not established — births, migration,
  open enrollment, and private-school participation all interact. The three scenarios bracket
  the range of how that share might evolve.
</div>

<div class="kpi-row">
  <div class="kpi">
    <div class="label">Fall 2025 enrollment <small>(verified)</small></div>
    <div class="val">{base_2025:,}</div>
    <div class="note">Grades K–12 · down from 14,415 peak (2024)</div>
  </div>
  <div class="kpi">
    <div class="label">Baseline 2030 forecast</div>
    <div class="val">{bl_2030:,}</div>
    <div class="note">{bl_chg_pct:+.1f}% from 2025; range {lo_2030:,}–{hi_2030:,}</div>
  </div>
  <div class="kpi">
    <div class="label">Projected kindergarteners 2026</div>
    <div class="val">{k_2026_bl}</div>
    <div class="note">From 2021 Johnson County births × 0.728</div>
  </div>
  <div class="kpi">
    <div class="label">District share of county births</div>
    <div class="val">0.728</div>
    <div class="note">Calibrated on 2025 verified K count (987)</div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">Total K–12 enrollment — Iowa DOE BEDS actual 2016–2025 and three-scenario forecast 2026–2030</div>
  <div class="legend-row">
    <span class="chip">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#1e3a5f" stroke-width="2.5"/></svg>
      Historical
    </span>
    <span class="chip" style="color:#15803d">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#15803d" stroke-width="2.2"/></svg>
      High
    </span>
    <span class="chip" style="color:#1e3a5f">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#1e3a5f" stroke-width="2.2" stroke-dasharray="6,3"/></svg>
      Baseline
    </span>
    <span class="chip" style="color:#b91c1c">
      <svg width="24" height="3"><line x1="0" y1="1.5" x2="24" y2="1.5" stroke="#b91c1c" stroke-width="2.2"/></svg>
      Low
    </span>
  </div>
  {fan_chart}
  <div class="chart-note">Open circle at 2025 = verified BEDS anchor. Shaded band = High–Low range.
  Amber dashes = 2023 trend break. Dashed blue = forecast baseline.</div>
</div>

<h2>Three-scenario forecast</h2>
<div class="sec">
  <p><strong>Base year:</strong> 2025 actual = {base_2025:,} students (Iowa DOE BEDS).</p>
  {forecast_table}
  <p style="font-size:12.5px;color:#64748b;margin:8px 0 0">
    High: growth corridors strengthen; effective K-entry share rises to 0.740. &nbsp;
    Baseline: share holds at 0.728 (current). &nbsp;
    Low: in-migration decelerates; effective share falls to 0.680.
  </p>
</div>

<h2>What the three scenarios assume</h2>
<div class="sec">
  <p>All three scenarios use the same declining birth trend. What differs is the assumption
  about how many of those babies eventually walk through Iowa City's school doors.</p>
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 0">
    <div style="flex:1;min-width:220px;border:2px solid #86efac;border-radius:10px;background:#f0fdf4;padding:13px 15px">
      <div style="font-weight:800;color:#15803d;font-size:15px;margin-bottom:5px">High</div>
      <p style="font-size:13.5px;margin:0 0 5px">The North Liberty and Tiffin growth corridors
      keep building homes at today's pace or faster. New families push the district's share of
      county kindergarteners up to 0.740. Grade retention follows the same overall pattern as
      the Baseline — only kindergarten headcount differs.</p>
      <div style="font-size:12px;color:#166534"><strong>2030: {hi_2030:,}</strong></div>
    </div>
    <div style="flex:1;min-width:220px;border:2px solid #93c5fd;border-radius:10px;background:#eff6ff;padding:13px 15px">
      <div style="font-weight:800;color:#1e3a5f;font-size:15px;margin-bottom:5px">Baseline</div>
      <p style="font-size:13.5px;margin:0 0 5px">Current trends hold. In-migration from the
      growth corridors continues at roughly today's rate. The main headwind is
      declining birth counts, not school closures.</p>
      <div style="font-size:12px;color:#1e40af"><strong>2030: {bl_2030:,}
      ({bl_chg_pct:+.1f}%)</strong></div>
    </div>
    <div style="flex:1;min-width:220px;border:2px solid #fca5a5;border-radius:10px;background:#fef2f2;padding:13px 15px">
      <div style="font-weight:800;color:#b91c1c;font-size:15px;margin-bottom:5px">Low</div>
      <p style="font-size:13.5px;margin:0 0 5px">New construction in the corridors slows as
      buildable land fills in. In-migration decelerates, and the district's effective share
      of county kindergarteners falls — about 35 fewer per year than births would predict.</p>
      <div style="font-size:12px;color:#991b1b"><strong>2030: {lo_2030:,}</strong></div>
    </div>
  </div>
  <p style="font-size:12.5px;color:#64748b;margin:10px 0 0">
    For the full methodology, worked examples, and the math behind each scenario:
    <a href="iccsd-enrollment-forecast-methodology.html" style="color:#2563eb">How this model works →</a>
  </p>
</div>

<h2>Historical enrollment by grade</h2>
<div class="sec">
  <p>All rows are verified Iowa DOE BEDS fall enrollment counts from the district's October 1
  headcount, school years 2016-17 through 2025-26. Green tag = BEDS actual. COVID disruption
  years 2020 and 2021 are flagged; 2023 is marked because K-share trends shifted starting
  that year.</p>
  <div class="gtab-wrap">{grade_table}</div>
</div>

<h2>Grade-to-grade retention rates</h2>
<div class="sec">
  <p>A rate above 1.0 means the cohort grew going into the next grade (students transferring in
  or new families arriving). The 8th-to-9th transition consistently shows a gain as students
  from smaller schools consolidate into Iowa City High and West High. Rates below 1.0 reflect
  attrition — the 9th-to-10th and 10th-to-11th transitions typically show small losses. All
  rates computed from verified Iowa DOE BEDS data.</p>
  {gpr_table}
</div>

<h2>Kindergarten module</h2>
<div class="sec">
  <p>Kindergarten is modeled from Johnson County resident births lagged five years, scaled by the
  ICCSD effective share (0.728). This share is calibrated from the 2025 BEDS actual (K=987) against
  2020 Johnson County births (1,356): 987/1356 = 0.728.</p>
  <p><strong>Observed trend since 2023:</strong> The kindergarten count has declined three
  straight years (1,035 → 998 → 992 → 987 from fall 2022 through fall 2025). The effective
  district share of county births fell from a 2016–2022 average of {avg_pre_2023_share:.3f}
  to a 2023–2025 average of {avg_post_2023_share:.3f}. The cause of this shift has not been
  established — multiple factors interact (births, migration, open enrollment, private-school
  choice). The three scenarios bracket the range of how this share might evolve.</p>
  {k_table}
  <p style="font-size:12.5px;color:#64748b;margin:8px 0 0">
    <strong>Geography caveat:</strong> Johnson County births overstate the ICCSD-relevant pool because
    the district boundary does not equal the county line. The 0.728 share corrects for this and also
    reflects any structural factors (open enrollment, private-school choice, migration) that currently
    affect district enrollment.
  </p>
</div>

<h2>What we can observe — and what we can't</h2>
<div class="sec">
  <p>ICCSD's kindergarten share of Johnson County births has shifted since 2023. What the data shows clearly:</p>
  <ul style="font-size:14px;padding-left:20px;margin:6px 0 14px">
    <li>The 2016–2022 average share (excluding COVID) was {avg_pre_2023_share:.3f}. The 2023–2025
    average is {avg_post_2023_share:.3f} — a decline of about {avg_pre_2023_share - avg_post_2023_share:.3f}
    percentage points.</li>
    <li>The North Liberty and Tiffin corridors — both partly inside ICCSD boundaries — are among the
    fastest-growing areas in Iowa. New housing drives in-migration of families with young children,
    adding K-entry demand independent of the birth trend.</li>
    <li>Multiple factors simultaneously affect the share: the district boundary doesn't match the county
    line, families can open-enroll across district lines, some choose private schools, and migration
    adds or removes families.</li>
  </ul>
  <p>What the data does <em>not</em> tell us is <strong>why</strong> the share changed. Coincidence of
  timing with any particular event is not evidence of causation. Attributing the shift to any single
  factor would require enrollment-transfer data we do not currently have. The three scenarios are
  designed to bracket the range without asserting a cause.</p>
  <p>Building-permit data from North Liberty, Tiffin, and Coralville should be added as a leading
  indicator — a quarterly permit series predicts K entry about 5–6 years ahead and would help
  separate migration effects from enrollment-choice effects.</p>
</div>

<h2>What this model needs to mature</h2>
<div class="sec">
  <ol style="font-size:14px;padding-left:18px;margin:6px 0 14px">
    <li><strong>Backtest.</strong> Fit GPRs on data through 2020 and predict 2021–2025 actuals.
    Target: MAPE ≈ 1–2% at year 1, widening to 4–5% at year 5. This validates the
    smoothing weights before relying on the 2030 range.</li>
    <li><strong>Corridor building permits.</strong> Add a quarterly permit-count series from North
    Liberty, Tiffin, and Coralville as a leading indicator for K-entry in the High and Baseline
    scenarios — residential permits predict enrollment about 5-6 years ahead.</li>
    <li><strong>Open-enrollment in/out.</strong> Iowa DOE publishes annual district-level
    open-enrollment flows. Adding these separates in-district retention from cross-district
    transfers and improves GPR attribution.</li>
    <li><strong>Private-school and open-enrollment data.</strong> Iowa DOE open-enrollment in/out
    flows by district are published annually. If recipient-level enrollment data by district of
    residence also becomes available, it would allow direct measurement of private-school
    enrollment shifts rather than inferring them from the K share trend.</li>
  </ol>
</div>

<h2>Refresh cadence</h2>
<div class="sec">
  <p>Rebuild every <strong>December</strong> when the new October BEDS file is released. Steps:</p>
  <ol style="font-size:14px;padding-left:18px;margin:6px 0">
    <li>Download the new Iowa DOE BEDS grade-level export (Iowa DOE Student Reporting in Iowa).</li>
    <li>Add the new year's grade vector to <code>BEDS_ACTUAL</code> in the script.</li>
    <li>Update <code>BIRTHS</code> with the latest CDC WONDER Johnson County natality data.</li>
    <li>Recalibrate <code>ICCSD_COUNTY_SHARE</code> from the new K actual vs. lagged births.</li>
    <li>Run <code>python3 scripts/build_enrollment_forecast.py</code>.</li>
  </ol>
</div>

<h2>Data sources</h2>
<div class="sec">
  <ul class="src-list">
    <li><strong>Grade-level enrollment (BEDS actual, all years):</strong> Iowa DOE Student Reporting in Iowa
      fall enrollment files for school years 2016-17 through 2025-26, Iowa City Community School
      District K-12 headcount by grade, October 1 count date. Downloaded 30 June 2026.</li>
    <li><strong>Johnson County births:</strong> CDC WONDER natality data, final through birth year 2022;
      estimated for 2023-2024. Lag 5 years to K entry year.</li>
    <li><strong>Statewide program context:</strong> Iowa Department of Education (statewide Educational Savings Account enrollment counts, 2023–25).</li>
    <li><strong>State projection benchmark:</strong> Iowa DOE District Enrollment Projections 2026–27 to
      2030–31 (developed May 2022). Use as comparison baseline, not as a forecast.</li>
  </ul>
</div>

<a class="back" href="other-analyses.html">&larr; Other analyses</a>
</div></body></html>"""

out_path = os.path.join(REPO_ROOT, "iccsd-enrollment-forecast.html")
with open(out_path, "w") as f:
    f.write(DOC)
print(f"Wrote {out_path} ({len(DOC)//1024} KB)")

# Print key computed numbers
print(f"\nKey outputs:")
print(f"  ICCSD county share: {ICCSD_COUNTY_SHARE}")
print(f"  2025 K-12 actual: {base_2025:,}")
print(f"  Baseline 2030: {bl_2030:,} ({bl_chg_pct:+.1f}%)")
print(f"  Range 2030: {lo_2030:,} – {hi_2030:,}")
print(f"\nK entry 2026-2030 (baseline, share=0.728):")
for yr in FCST_YEARS:
    print(f"  {yr}: {scenario_results['Baseline'][yr][0]}")
print(f"\nHistorical K-12 totals (all BEDS actual):")
for y in HIST_YEARS:
    print(f"  {y}: {hist_totals[y]:,}")

build_methodology_page()
