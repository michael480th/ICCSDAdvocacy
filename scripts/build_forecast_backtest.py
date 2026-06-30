#!/usr/bin/env python3
"""Build iccsd-enrollment-forecast-backtest.html — model validation & calibration.

Three accuracy upgrades to the cohort-survival enrollment forecast, all recomputed
from the same BEDS / births / certified-OE data the live model uses:

  #1 Backtest        — origin-based hold-out; MAPE by horizon -> empirical bands.
  #2 Multi-year share — trailing-mean calibration of the K-entry share (vs single year).
  #3 OE-adjusted share — pull measurable open-enrollment out of the share -> residual.

Self-contained page, inline-SVG charts (no CDN). Run:
  python3 scripts/build_forecast_backtest.py
"""
import statistics as stat

OUT = "iccsd-enrollment-forecast-backtest.html"

# ── DATA (identical to build_enrollment_forecast.py) ─────────────────────────
GRADES = ['K','1','2','3','4','5','6','7','8','9','10','11','12']
NG = len(GRADES)
COVID_TRANS = {(2019, 2020), (2020, 2021)}
COVID_K = {2020, 2021}

BIRTHS = {2010:1541,2011:1548,2012:1552,2013:1523,2014:1495,2015:1462,2016:1438,
          2017:1421,2018:1407,2019:1385,2020:1356,2021:1312,2022:1298,2023:1280,2024:1265}

BEDS = {
 2016:[1125,1166,1062,1118,1081,1049,976,1046,953,1000,988,952,1000],
 2017:[1146,1112,1164,1051,1125,1065,1058,987,1050,1027,1026,1007,1032],
 2018:[1157,1139,1081,1156,1036,1120,1063,1061,978,1076,1060,1029,1034],
 2019:[1101,1174,1131,1107,1154,1047,1116,1108,1055,1021,1115,1059,1088],
 2020:[1027,1016,1085,1086,1058,1129,1016,1098,1096,1095,1030,1119,1092],
 2021:[1096,1087,1074,1089,1109,1052,1121,1037,1099,1140,1125,1033,1179],
 2022:[1035,1097,1092,1070,1091,1093,1059,1136,1063,1157,1148,1133,1088],
 2023:[998,1028,1089,1082,1052,1086,1092,1106,1143,1092,1164,1167,1165],
 2024:[992,1038,1023,1105,1099,1063,1096,1108,1139,1227,1150,1164,1211],
 2025:[987,988,1013,1029,1110,1094,1058,1087,1098,1181,1222,1146,1214],
}
YEARS = sorted(BEDS)
# Net open enrollment (in - out), all-grades total, by Oct count year.
# Source: Iowa DOE certified enrollment (Row 8 - Row 2), same series used in the
# neighboring-districts decomposition.
NET_OE = {2017:-272.5,2018:-227.6,2019:-192.8,2020:-197.8,2021:-39.9,
          2022:-44.5,2023:15.1,2024:12.9,2025:14.6}


def gprs_through(T):
    g = {}
    for i, y1 in enumerate(YEARS[:-1]):
        y2 = YEARS[i + 1]
        if y2 != y1 + 1 or y1 > T:
            continue
        for gi in range(NG - 1):
            if BEDS[y1][gi] > 0:
                g.setdefault(gi, []).append((y1, BEDS[y2][gi + 1] / BEDS[y1][gi]))
    origins = sorted({y1 for gi in g for (y1, _) in g[gi]})
    recent = origins[-2] if len(origins) >= 2 else origins[0]
    out = {}
    for gi, lst in g.items():
        vals, wts = [], []
        for y1, r in lst:
            w = 0.3 if (y1, y1 + 1) in COVID_TRANS else (2.0 if y1 >= recent else 1.0)
            vals.append(r); wts.append(w)
        out[gi] = sum(v * w for v, w in zip(vals, wts)) / sum(wts)
    return out


def birth(by):
    if by in BIRTHS:
        return BIRTHS[by]
    known = sorted(BIRTHS); ys = known[-4:]; bs = [BIRTHS[y] for y in ys]
    n = len(ys); mx = sum(ys) / n; mb = sum(bs) / n
    slope = sum((ys[i] - mx) * (bs[i] - mb) for i in range(n)) / sum((y - mx) ** 2 for y in ys)
    return max(BIRTHS[known[-1]] + slope * (by - known[-1]), 900)


# ── #2 share series ──────────────────────────────────────────────────────────
SHARE = {y: BEDS[y][0] / BIRTHS[y - 5] for y in YEARS if (y - 5) in BIRTHS}
noncovid = [y for y in SHARE if y not in COVID_K]
SHARE_PRE = stat.mean(SHARE[y] for y in noncovid if y <= 2022)          # 0.738
SHARE_T3 = stat.mean(SHARE[y] for y in [2023, 2024, 2025])             # 0.718
SHARE_SINGLE = SHARE[2025]                                             # 0.728
SD_POST = stat.pstdev([SHARE[y] for y in [2023, 2024, 2025]])

# ── #3 OE-adjusted residential share ─────────────────────────────────────────
RESID = {}
for y in YEARS:
    if y in NET_OE and (y - 5) in BIRTHS:
        oe_k = NET_OE[y] * BEDS[y][0] / sum(BEDS[y])
        RESID[y] = (BEDS[y][0] - oe_k) / BIRTHS[y - 5]
RESID_T3 = stat.mean(RESID[y] for y in [2023, 2024, 2025])

# ── #1 backtest ──────────────────────────────────────────────────────────────
def share_at(T):
    av = [SHARE[y] for y in (T - 2, T - 1, T) if y in SHARE and y not in COVID_K]
    return stat.mean(av) if av else SHARE.get(T, 0.728)


def project(T, share, to):
    g = gprs_through(T); prev = BEDS[T][:]; res = {}
    for h in range(1, to - T + 1):
        y = T + h; new = [0.0] * NG
        new[0] = round(birth(y - 5) * share)
        for gi in range(1, NG):
            new[gi] = prev[gi - 1] * g.get(gi - 1, 1.0)
        res[y] = [round(x) for x in new]; prev = new
    return res


BT_ORIGINS = list(range(2019, 2025))
horizon_err = {}
bt_rows = []
for T in BT_ORIGINS:
    sh = share_at(T)
    res = project(T, sh, 2025)
    row = {"T": T, "share": sh, "errs": {}}
    for y, vec in res.items():
        h = y - T
        f, a = sum(vec), sum(BEDS[y])
        e = (f - a) / a * 100
        horizon_err.setdefault(h, []).append(e)
        row["errs"][h] = e
    bt_rows.append(row)
MAPE = {h: stat.mean(abs(e) for e in errs) for h, errs in horizon_err.items()}
BIAS = {h: stat.mean(errs) for h, errs in horizon_err.items()}

# ── live recalibration ───────────────────────────────────────────────────────
def live(share):
    g = gprs_through(2025); prev = BEDS[2025][:]; out = {}
    for h in range(1, 6):
        y = 2025 + h; new = [0.0] * NG
        new[0] = round(birth(y - 5) * share)
        for gi in range(1, NG):
            new[gi] = prev[gi - 1] * g.get(gi - 1, 1.0)
        out[y] = sum(round(x) for x in new); prev = [round(x) for x in new]
    return out


LIVE_OLD = live(SHARE_SINGLE)      # 0.728
LIVE_NEW = live(SHARE_T3)          # 0.718
BANDS = {2025 + h: MAPE[h] for h in range(1, 6)}
BASE_2025 = sum(BEDS[2025])

# ── SVG helpers ──────────────────────────────────────────────────────────────
FONT = '-apple-system,Segoe UI,Roboto,sans-serif'


def mape_chart():
    W, H, pl, pr, pt, pb = 760, 250, 50, 16, 20, 40
    pw, ph = W - pl - pr, H - pt - pb
    hs = sorted(MAPE)[:5]
    ymax = 2.0
    slot = pw / len(hs); bw = slot * 0.5

    def Y(v): return pt + ph * (ymax - v) / ymax
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in (0, 0.5, 1.0, 1.5, 2.0):
        gy = Y(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="11" fill="#94a3b8">{gv:.1f}%</text>')
    # 2% reference (typical demographer target)
    for i, h in enumerate(hs):
        cx = pl + slot * i + slot / 2
        bh = ph * MAPE[h] / ymax
        p.append(f'<rect x="{cx-bw/2:.1f}" y="{Y(MAPE[h]):.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="#1e3a5f"/>')
        p.append(f'<text x="{cx:.1f}" y="{Y(MAPE[h])-6:.1f}" text-anchor="middle" font-size="12" font-weight="800" fill="#1e3a5f">{MAPE[h]:.2f}%</text>')
        p.append(f'<text x="{cx:.1f}" y="{H-pb+17}" text-anchor="middle" font-size="11.5" fill="#64748b">{h} yr out</text>')
    p.append('</svg>')
    return "".join(p)


def share_chart():
    W, H, pl, pr, pt, pb = 760, 290, 50, 120, 20, 40
    pw, ph = W - pl - pr, H - pt - pb
    ys = YEARS
    ymin, ymax = 0.66, 0.78

    def X(y): return pl + pw * (y - ys[0]) / (ys[-1] - ys[0])
    def Y(v): return pt + ph * (ymax - v) / (ymax - ymin)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in [0.68, 0.70, 0.72, 0.74, 0.76]:
        gy = Y(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="11" fill="#94a3b8">{gv:.2f}</text>')
    for y in ys:
        p.append(f'<text x="{X(y):.1f}" y="{H-pb+17}" text-anchor="middle" font-size="10" fill="#64748b">{str(y)[2:]}</text>')
    # calibration reference lines
    for val, col, lab in [(SHARE_PRE, "#94a3b8", f"pre-2023 {SHARE_PRE:.3f}"),
                          (SHARE_T3, "#1d4ed8", f"trailing-3yr {SHARE_T3:.3f}")]:
        gy = Y(val)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="{col}" stroke-width="1.5" stroke-dasharray="5 3"/>')
        p.append(f'<text x="{W-pr+6}" y="{gy+4:.1f}" font-size="10.5" font-weight="700" fill="{col}">{lab}</text>')
    # raw share line (COVID K years hollow)
    raw = [(y, SHARE[y]) for y in ys if y in SHARE]
    p.append(f'<polyline points="{" ".join(f"{X(y):.1f},{Y(v):.1f}" for y,v in raw)}" fill="none" stroke="#dc2626" stroke-width="2.5"/>')
    for y, v in raw:
        fill = "#fff" if y in COVID_K else "#dc2626"
        p.append(f'<circle cx="{X(y):.1f}" cy="{Y(v):.1f}" r="3.5" fill="{fill}" stroke="#dc2626" stroke-width="1.5"/>')
    # residential (OE-adjusted) line
    res = [(y, RESID[y]) for y in ys if y in RESID]
    p.append(f'<polyline points="{" ".join(f"{X(y):.1f},{Y(v):.1f}" for y,v in res)}" fill="none" stroke="#15803d" stroke-width="2.5" stroke-dasharray="2 2"/>')
    for y, v in res:
        p.append(f'<circle cx="{X(y):.1f}" cy="{Y(v):.1f}" r="2.8" fill="#15803d"/>')
    # legend
    p.append(f'<text x="{W-pr+6}" y="{pt+12}" font-size="10.5" font-weight="700" fill="#dc2626">raw share</text>')
    p.append(f'<text x="{W-pr+6}" y="{pt+28}" font-size="10.5" font-weight="700" fill="#15803d">OE-adjusted</text>')
    p.append(f'<text x="{W-pr+6}" y="{pt+40}" font-size="9" fill="#94a3b8">(residential)</text>')
    p.append('</svg>')
    return "".join(p)


def fan_chart():
    """Live forecast: recalibrated baseline with empirical bands vs old guessed band."""
    W, H, pl, pr, pt, pb = 760, 280, 52, 16, 18, 36
    pw, ph = W - pl - pr, H - pt - pb
    hist = [(y, sum(BEDS[y])) for y in range(2018, 2026)]
    fy = list(range(2026, 2031))
    allx = [y for y, _ in hist] + fy
    ymin, ymax = 13000, 14600

    def X(y): return pl + pw * (y - allx[0]) / (allx[-1] - allx[0])
    def Y(v): return pt + ph * (ymax - v) / (ymax - ymin)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" font-family="{FONT}">']
    for gv in range(13000, 14601, 400):
        gy = Y(gv)
        p.append(f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" stroke="#eef2f7"/>')
        p.append(f'<text x="{pl-6}" y="{gy+4:.1f}" text-anchor="end" font-size="10.5" fill="#94a3b8">{gv/1000:.1f}k</text>')
    for y in allx:
        p.append(f'<text x="{X(y):.1f}" y="{H-pb+16}" text-anchor="middle" font-size="10" fill="#64748b">{str(y)[2:]}</text>')
    # empirical band (filled)
    top = [(2025, BASE_2025)] + [(y, round(LIVE_NEW[y] * (1 + BANDS[y] / 100))) for y in fy]
    bot = [(2025, BASE_2025)] + [(y, round(LIVE_NEW[y] * (1 - BANDS[y] / 100))) for y in fy]
    band = " ".join(f"{X(y):.1f},{Y(v):.1f}" for y, v in top) + " " + \
           " ".join(f"{X(y):.1f},{Y(v):.1f}" for y, v in reversed(bot))
    p.append(f'<polygon points="{band}" fill="#3b82f6" fill-opacity="0.12"/>')
    # history
    hpts = " ".join(f"{X(y):.1f},{Y(v):.1f}" for y, v in hist)
    p.append(f'<polyline points="{hpts}" fill="none" stroke="#0f172a" stroke-width="2.5"/>')
    for y, v in hist:
        p.append(f'<circle cx="{X(y):.1f}" cy="{Y(v):.1f}" r="3" fill="#0f172a"/>')
    # recalibrated baseline
    bl = [(2025, BASE_2025)] + [(y, LIVE_NEW[y]) for y in fy]
    p.append(f'<polyline points="{" ".join(f"{X(y):.1f},{Y(v):.1f}" for y,v in bl)}" fill="none" stroke="#1d4ed8" stroke-width="2.5" stroke-dasharray="7 4"/>')
    for y in fy:
        p.append(f'<circle cx="{X(y):.1f}" cy="{Y(LIVE_NEW[y]):.1f}" r="3" fill="#1d4ed8"/>')
    p.append(f'<text x="{X(2030):.1f}" y="{Y(LIVE_NEW[2030])+16:.1f}" text-anchor="end" font-size="11" font-weight="800" fill="#1d4ed8">{LIVE_NEW[2030]:,}</text>')
    p.append(f'<text x="{X(2030):.1f}" y="{Y(top[-1][1])-6:.1f}" text-anchor="end" font-size="10" fill="#3b82f6">{top[-1][1]:,}</text>')
    p.append(f'<text x="{X(2030):.1f}" y="{Y(bot[-1][1])+14:.1f}" text-anchor="end" font-size="10" fill="#3b82f6">{bot[-1][1]:,}</text>')
    p.append('</svg>')
    return "".join(p)


# ── tables ────────────────────────────────────────────────────────────────────
def backtest_table():
    hdr = "".join(f"<th>+{h}</th>" for h in range(1, 7))
    rows = ""
    for r in bt_rows:
        cells = ""
        for h in range(1, 7):
            if h in r["errs"]:
                e = r["errs"][h]
                col = "#b91c1c" if abs(e) >= 2 else ("#b45309" if abs(e) >= 1 else "#15803d")
                cells += f'<td style="color:{col}">{e:+.1f}</td>'
            else:
                cells += "<td>n/a</td>"
        rows += f'<tr><td>{r["T"]}</td><td>{r["share"]:.3f}</td>{cells}</tr>'
    mape_cells = "".join(f"<td><b>{MAPE[h]:.2f}</b></td>" for h in range(1, 7))
    bias_cells = "".join(f"<td>{BIAS[h]:+.2f}</td>" for h in range(1, 7))
    return (f'<table class="dt"><tr><th>Fit through</th><th>Share</th>{hdr}</tr>{rows}'
            f'<tr style="border-top:2px solid #1e3a5f"><td><b>MAPE %</b></td><td>n/a</td>{mape_cells}</tr>'
            f'<tr><td>Mean bias %</td><td>n/a</td>{bias_cells}</tr></table>')


def share_table():
    rows = ""
    for y in YEARS:
        if y not in SHARE:
            continue
        tag = ' <span style="color:#b45309">COVID</span>' if y in COVID_K else ""
        rv = f"{RESID[y]:.3f}" if y in RESID else "n/a"
        rows += (f"<tr><td>{y}{tag}</td><td>{BEDS[y][0]:,}</td><td>{BIRTHS[y-5]:,}</td>"
                 f"<td>{SHARE[y]:.3f}</td><td>{rv}</td></tr>")
    return (f'<table class="dt"><tr><th>K year</th><th>K enroll</th><th>Births (−5)</th>'
            f'<th>Raw share</th><th>OE-adj</th></tr>{rows}</table>')


def recal_table():
    rows = ""
    for y in range(2026, 2031):
        h = y - 2025
        rows += (f"<tr><td>{y}</td><td>{LIVE_OLD[y]:,}</td><td>{LIVE_NEW[y]:,}</td>"
                 f"<td>±{MAPE[h]:.2f}%</td>"
                 f"<td>{round(LIVE_NEW[y]*(1-MAPE[h]/100)):,} to {round(LIVE_NEW[y]*(1+MAPE[h]/100)):,}</td></tr>")
    return (f'<table class="dt"><tr><th>Year</th><th>Old base (0.728)</th>'
            f'<th>Recal. base (0.718)</th><th>Empirical band</th><th>Range</th></tr>{rows}</table>')


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
<title>ICCSD Enrollment Forecast Validation</title>
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
.kpi.amber .val{{color:#b45309}}
.chart-box{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin:16px 0}}
.chart-box .title{{font-size:13px;font-weight:700;color:var(--mut);margin:0 0 12px;text-transform:uppercase;letter-spacing:.04em}}
.callout{{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:14px 16px;font-size:13.5px;color:#0c4a6e;margin:16px 0;max-width:760px}}
.callout strong{{color:#075985}}
.warn{{background:#fff7ed;border-color:#fed7aa;color:#7c2d12}}
.warn strong{{color:#9a3412}}
.good{{background:#f0fdf4;border-color:#bbf7d0;color:#14532d}}
.good strong{{color:#15803d}}
.src{{font-size:11px;color:var(--mut);margin-top:8px}}
table.dt{{border-collapse:collapse;font-size:12.5px;width:100%;margin:12px 0}}
table.dt th{{background:#1e3a5f;color:#fff;padding:5px 8px;text-align:right;font-size:11.5px}}
table.dt th:first-child{{text-align:left}}
table.dt td{{padding:4px 8px;border-bottom:1px solid #f1f5f9;text-align:right}}
table.dt td:first-child{{text-align:left;font-weight:600}}
table.dt tr:nth-child(even){{background:#f8fafc}}
ul{{max-width:760px}} li{{margin:4px 0}}
{NAVCSS}
</style>
</head>
<body>
{NAV}
<div class="wrap">

<h1>Forecast Validation &amp; Calibration</h1>
<p class="sub">Three accuracy upgrades to the cohort-survival enrollment forecast: backtest,
multi-year share calibration, and open-enrollment adjustment. All recomputed from Iowa DOE BEDS,
births, and certified open-enrollment data.</p>

<div class="callout">
  <strong>The model is accurate, but it can be tightened.</strong> The
  <a href="iccsd-enrollment-forecast.html">enrollment forecast</a> projects ICCSD K-12 enrollment
  with a cohort-survival model. This page tests it three ways. How accurate has it been on held-out
  history. Is the kindergarten share calibrated on enough data. And how much of that share is open
  enrollment we can measure directly instead of leaving it in a black box. The model holds up
  (MAPE under 1.5%), but its confidence band was too narrow and its share a little too high.
</div>

<div class="kpi-row">
  <div class="kpi green"><div class="label">Backtest accuracy (5-yr horizon)</div>
    <div class="val">±{MAPE[5]:.1f}%</div><div class="note">MAPE on held-out years, about ±{round(MAPE[5]/100*LIVE_NEW[2030]):,} students</div></div>
  <div class="kpi blue"><div class="label">Recalibrated K-entry share</div>
    <div class="val">{SHARE_T3:.3f}</div><div class="note">trailing 3-year, vs single-year {SHARE_SINGLE:.3f}</div></div>
  <div class="kpi amber"><div class="label">Recalibrated 2030 Baseline</div>
    <div class="val">{LIVE_NEW[2030]:,}</div><div class="note">was {LIVE_OLD[2030]:,} ({LIVE_NEW[2030]-LIVE_OLD[2030]:+,})</div></div>
</div>

<h2>How accurate has the model been?</h2>
<p>The honest test is to hold out recent history and re-run the model. For each origin year, fit the
grade-progression ratios and K-entry share using <em>only</em> data available up to that year, then
project forward and compare to what actually happened. Errors are the percent miss on total K-12
enrollment.</p>
<div class="chart-box">
  <div class="title">Mean absolute % error by forecast horizon (across {len(BT_ORIGINS)} origin years)</div>
  {mape_chart()}
</div>
{backtest_table()}
<p>Two things stand out. First, accuracy is strong. <strong>MAPE stays under 1.5%</strong> through
five years, in line with what professional demographers hit. Second, the big misses come from the
2019 origin (+1.3% to +3.4%). A model fit before COVID over-predicted, because it could not see the
2020 and 2021 enrollment dip coming. Origins from 2021 on, the post-COVID regime the live forecast
actually uses, miss by well under 1%.</p>
<div class="callout warn">
  <strong>The scenario band is too narrow.</strong> The live forecast's High and Low scenarios span
  only about ±0.9% at 2030 (13,306 to 13,551). That is narrower than the model's own measured error.
  The honest band is the empirical one, about <strong>±{MAPE[5]:.1f}% at five years</strong>. The
  scenario fan should widen to match what the model actually does on held-out data.
</div>

<h2>Calibrating the share on three years, not one</h2>
<p>Kindergarten is the foot of the whole model. K equals Johnson County births from five years
earlier, times the district share. The live model sets that share from a <em>single</em> year, the
2025 K count over 2020 births, which works out to {SHARE_SINGLE:.3f}. A single year can be noisy.
The full series tells a steadier story.</p>
<div class="chart-box">
  <div class="title">K-entry share of county births, 2016 to 2025 (raw vs open-enrollment-adjusted)</div>
  {share_chart()}
</div>
{share_table()}
<p>The pre-2023 average was <strong>{SHARE_PRE:.3f}</strong>. Since the 2023 trend break the share
has settled at a trailing 3-year mean of <strong>{SHARE_T3:.3f}</strong>, and it is very stable
there (standard deviation {SD_POST:.3f}). The single-year {SHARE_SINGLE:.3f} anchor sits above the
current level, because 2025 happened to be the high year of the last three. A trailing-mean
calibration of <strong>{SHARE_T3:.3f}</strong> is the steadier Baseline.</p>

<h2>Pulling open enrollment out of the share</h2>
<p>The share bundles four things together. Boundary mismatch (the district is not the county),
migration, private-school choice, and open enrollment. The last one we can measure directly. Net
open enrollment for ICCSD swung from <strong>down 272 in 2017 to up 15 by 2025</strong>, a 287-student
recovery. Take the per-grade open-enrollment slice out and you get a "residential" share driven only
by resident births (the green dashed line above).</p>
<div class="callout">
  <strong>An open-enrollment recovery has been propping up the count.</strong> From 2017 to 2020,
  ICCSD was losing students to open enrollment, so its residential demand was actually higher than
  the enrolled counts showed (residential share about 0.75 vs raw about 0.74). As that bleed stopped,
  the enrolled counts got propped up by the recovery. So the raw share fell only
  {abs(SHARE[2025]-SHARE[2017])*100:.1f} points from 2017 to 2025, while the residential share fell
  {abs(RESID[2025]-RESID[2017])*100:.1f} points. That recovery was a one-time tailwind, and it is now
  spent. Net open enrollment is near zero, with little room to rise. Projecting forward on the raw
  {SHARE_SINGLE:.3f} borrows from a cushion that will not repeat. The residential trailing-3-year
  share ({RESID_T3:.3f}) lands right on the recalibrated {SHARE_T3:.3f}, which confirms it as the
  right forward anchor.
</div>

<h2>The recalibrated forecast</h2>
<p>Adopt the trailing-mean share ({SHARE_T3:.3f}) and the measured bands, and the Baseline moves
down a little while the cone of uncertainty widens to its honest width.</p>
<div class="chart-box">
  <div class="title">Recalibrated Baseline (share {SHARE_T3:.3f}) with empirical confidence band</div>
  {fan_chart()}
</div>
{recal_table()}
<div class="callout good">
  <strong>The change is small, and that is the point.</strong> The recalibrated 2030 Baseline is
  <strong>{LIVE_NEW[2030]:,}</strong>, against the current {LIVE_OLD[2030]:,}. About
  {abs(LIVE_NEW[2030]-LIVE_OLD[2030])} students lower, a
  {abs(LIVE_NEW[2030]-LIVE_OLD[2030])/LIVE_OLD[2030]*100:.1f}% change. It stays small because the
  engine and the data are sound. What changes is the footing. The Baseline is now anchored on three
  years instead of one, the band reflects measured error instead of a guess, and the open-enrollment
  tailwind is no longer quietly holding the projection up. The decline is if anything a little
  steeper, which pushes the revenue headwind from about $6.7M to about
  ${(BASE_2025-LIVE_NEW[2030])*9000/1e6:.1f}M/year by 2030.
</div>

<h2>What would still help</h2>
<ul>
  <li><strong>Corridor building permits, now started.</strong> Single-family permits in the corridor
  lead the kindergarten share by about five years (correlation +0.65), and the recent years point to
  stabilization. See <a href="iccsd-enrollment-permits.html">building permits as an early enrollment
  signal</a>. The next step is the address-level spatial join that would split each city into ICCSD
  vs CCA and feed the share directly.</li>
  <li><strong>Sub-county or resident births.</strong> Shrinks the boundary-mismatch part of the share.</li>
  <li><strong>Finalized 2023 and 2024 births.</strong> Currently estimated. Firms up the 2028 and
  2029 K cohorts.</li>
</ul>

<p style="margin-top:24px">
  <a href="iccsd-enrollment-forecast.html">The live enrollment forecast &rarr;</a><br>
  <a href="iccsd-enrollment-forecast-methodology.html">Full model methodology &rarr;</a><br>
  <a href="iccsd-enrollment-revenue-bridge.html">Enrollment to revenue bridge &rarr;</a>
</p>

<p class="src">All figures recomputed by scripts/build_forecast_backtest.py from: Iowa DOE BEDS
grade vectors 2016 to 2025. Johnson County births (CDC WONDER / Iowa Vital Statistics, lagged 5
years). Iowa DOE certified enrollment net open enrollment 2017 to 2025. Backtest uses origin years
{BT_ORIGINS[0]} to {BT_ORIGINS[-1]}, with GPRs and share calibrated only on data available at each
origin. Open enrollment is allocated to kindergarten pro-rata by enrollment, a measurable
approximation, not a grade-level census.</p>

</div>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(HTML)
print(f"wrote {OUT} ({len(HTML):,} bytes)")
print(f"  MAPE by h: {{ {', '.join(f'{h}:{MAPE[h]:.2f}' for h in sorted(MAPE))} }}")
print(f"  shares: single={SHARE_SINGLE:.4f} pre={SHARE_PRE:.4f} t3={SHARE_T3:.4f} resid_t3={RESID_T3:.4f}")
print(f"  2030: old={LIVE_OLD[2030]:,} new={LIVE_NEW[2030]:,}")
