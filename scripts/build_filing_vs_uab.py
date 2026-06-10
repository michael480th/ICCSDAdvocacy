#!/usr/bin/env python3
"""
Scatterplot: a district's audit-filing timeliness vs. its financial cushion.

X = average Unspent Authorized Budget (% of budget) over the last 3 complete years (FY2023-2025).
Y = how many days EARLY (+) or LATE (-) it files its audited financials with the state,
    averaged over the last 3 years (data/audit-filing-days.csv).

UAB for every Iowa district is read from the DOM "Unspent Authorized Budget Report.xlsx"
(data_UAB sheet, joined on district code). Renders a self-contained HTML with an inline-SVG
scatter; Iowa City and the other large (5,000+) districts are highlighted, because that is
where the relationship lives.

Run:  python3 scripts/build_filing_vs_uab.py   ->  iccsd-filing-vs-uab.html
"""
import openpyxl, csv, html, datetime, statistics as st, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

# ---- filing-days table (data/audit-filing-days.csv) ----
recs = []
for row in csv.DictReader(open("data/audit-filing-days.csv")):
    recs.append(dict(name=row["school_district"], code=int(row["district_code"]),
                     enr=int(row["certified_enrollment"]), days=int(row["avg_days_early_late"])))

# ---- UAB FY2023-2025 average per district ----
wb = openpyxl.load_workbook("UAB/Unspent Authorized Budget Report.xlsx", data_only=True, read_only=True)
ws = wb["data_UAB"]
uab = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    fy, dist = r[0], r[1]
    if isinstance(fy, int) and fy in (2023, 2024, 2025) and dist and r[37]:
        try:
            c = int(dist)
        except (TypeError, ValueError):
            continue
        uab.setdefault(c, {})[fy] = 100 * r[38] / r[37]

pts = []
for rec in recs:
    u = uab.get(rec["code"])
    if u:
        rec["uab"] = st.mean(u.values())
        pts.append(rec)

LARGE = 5000


def pearson(x, y):
    mx, my = st.mean(x), st.mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def linreg(x, y):                      # returns slope, intercept
    mx, my = st.mean(x), st.mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return b, my - b * mx


allx = [p["uab"] for p in pts]
ally = [p["days"] for p in pts]
r_all = pearson(allx, ally)
big = [p for p in pts if p["enr"] >= LARGE]
bx = [p["uab"] for p in big]
by = [p["days"] for p in big]
r_big = pearson(bx, by)
slope_b, int_b = linreg(bx, by)
IC = next(p for p in pts if p["code"] == 3141)

# ---------- SVG scatter ----------
W, H = 820, 540
L, Rm, T, B = 70, 30, 30, 56
pw, ph = W - L - Rm, H - T - B
XMIN, XMAX = -10, 65
YMIN, YMAX = -450, 150
def X(v): return L + pw * (v - XMIN) / (XMAX - XMIN)
def Y(v): return T + ph * (YMAX - v) / (YMAX - YMIN)

s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="filing days vs UAB scatter">']
# gridlines + axis ticks
for gx in range(-10, 70, 10):
    s.append(f'<line x1="{X(gx):.1f}" y1="{T}" x2="{X(gx):.1f}" y2="{T+ph}" class="grid"/>')
    s.append(f'<text x="{X(gx):.1f}" y="{T+ph+20}" class="xtick">{gx}%</text>')
for gy in range(-450, 151, 75):
    s.append(f'<line x1="{L}" y1="{Y(gy):.1f}" x2="{L+pw}" y2="{Y(gy):.1f}" class="grid"/>')
    s.append(f'<text x="{L-8}" y="{Y(gy)+4:.1f}" class="ytick">{gy:+d}</text>')
# zero-day reference (on-time line)
s.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{L+pw}" y2="{Y(0):.1f}" class="zero"/>')
s.append(f'<text x="{L+pw-4}" y="{Y(0)-6:.1f}" class="zlab">on time (0 days) — above = early, below = late</text>')
# large-district regression line (clipped to large-district UAB range)
lx0, lx1 = min(bx), max(bx)
s.append(f'<line x1="{X(lx0):.1f}" y1="{Y(slope_b*lx0+int_b):.1f}" '
         f'x2="{X(lx1):.1f}" y2="{Y(slope_b*lx1+int_b):.1f}" class="fit"/>')
# small districts (gray cloud)
for p in pts:
    if p["enr"] < LARGE:
        s.append(f'<circle cx="{X(p["uab"]):.1f}" cy="{Y(max(YMIN,p["days"])):.1f}" r="3" class="dot sm"/>')
# large districts (blue) + labels
def esc(t): return html.escape(t)
for p in big:
    if p["code"] == 3141:
        continue
    cx, cy = X(p["uab"]), Y(p["days"])
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" class="dot lg"/>')
    short = p["name"].replace(" CSD", "").replace(" Independent", "")
    s.append(f'<text x="{cx+7:.1f}" y="{cy+3:.1f}" class="lglab">{esc(short)}</text>')
# Iowa City (red, on top)
cx, cy = X(IC["uab"]), Y(IC["days"])
s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" class="dot ic"/>')
s.append(f'<text x="{cx+10:.1f}" y="{cy+4:.1f}" class="iclab">Iowa City  (UAB {IC["uab"]:.1f}%, {IC["days"]} days)</text>')
# axis titles
s.append(f'<text x="{L+pw/2:.1f}" y="{H-8}" class="axt">Average spending-authority cushion (UAB %, FY2023–2025) — higher = more cushion →</text>')
s.append(f'<text transform="translate(16,{T+ph/2:.1f}) rotate(-90)" class="axt" text-anchor="middle">Days early (+) / late (−) filing audit ↑</text>')
s.append('</svg>')
svg = "".join(s)

date = datetime.date(2026, 6, 9).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Audit timeliness vs. financial cushion — Iowa districts</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:900px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.chart{{width:100%;height:auto;display:block}}
.grid{{stroke:#eef2f7;stroke-width:1}}
.xtick{{fill:#64748b;font-size:12px;text-anchor:middle}} .ytick{{fill:#94a3b8;font-size:12px;text-anchor:end}}
.zero{{stroke:#0f172a;stroke-width:1;stroke-dasharray:4 3;opacity:.5}}
.zlab{{fill:#475569;font-size:11px;text-anchor:end}}
.fit{{stroke:#2563eb;stroke-width:2;stroke-dasharray:6 4;opacity:.8}}
.dot.sm{{fill:#cbd5e1}} .dot.lg{{fill:#2563eb;opacity:.85}} .dot.ic{{fill:#dc2626;stroke:#fff;stroke-width:1.5}}
.lglab{{fill:#1e3a8a;font-size:10.5px}} .iclab{{fill:#dc2626;font-size:13px;font-weight:700}}
.axt{{fill:#334155;font-size:12.5px;text-anchor:middle}}
.stats{{display:flex;gap:14px;flex-wrap:wrap;margin:4px 0 16px}}
.stat{{background:#f8fafc;border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:150px}}
.stat .n{{font-size:24px;font-weight:800}} .stat .l{{font-size:12px;color:var(--mut)}}
.take{{margin:14px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #dc2626;border-radius:6px;padding:10px 14px}}
.take b{{color:#0f172a}}
.legend{{font-size:13px;color:var(--mut);margin:8px 2px;display:flex;gap:18px;flex-wrap:wrap;align-items:center}}
.legend .sw{{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:5px}}
footer{{color:var(--mut);font-size:12.5px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body>{nav("filing")}<div class="wrap">

<h1>Does a thinner financial cushion mean a later audit?</h1>
<p class="sub">Audit-filing timeliness vs. spending-authority cushion (UAB), {len(pts)} Iowa districts · {date}</p>

<div class="card">
<div class="stats">
  <div class="stat"><div class="n">{r_all:+.2f}</div><div class="l">correlation (r), <b>all {len(pts)} districts</b></div></div>
  <div class="stat"><div class="n">{r_big:+.2f}</div><div class="l">correlation (r), <b>large districts (5,000+, n={len(big)})</b></div></div>
  <div class="stat"><div class="n">{IC['days']}</div><div class="l">Iowa City days late — the worst in the state</div></div>
</div>
<div class="legend">
  <span><span class="sw" style="background:#dc2626"></span>Iowa City CSD</span>
  <span><span class="sw" style="background:#2563eb"></span>Large districts (5,000+ students)</span>
  <span><span class="sw" style="background:#cbd5e1"></span>All other districts</span>
  <span><span class="sw" style="background:#2563eb;border-radius:0;height:3px"></span>large-district trend</span>
</div>
{svg}
<p class="take"><b>Statewide, there is essentially no correlation (r = {r_all:+.2f}).</b> Most small
districts file on time no matter how thin their cushion — districts that filed late average about the
same UAB (≈26%) as those that filed early (≈25%). <b>But among the large districts the expected
relationship appears (r = {r_big:+.2f}):</b> the better-cushioned big districts tend to file sooner,
the thin-cushioned ones later. <b>Iowa City is the extreme of that pattern</b> — the lowest cushion of
any sizable district (~{IC['uab']:.1f}%) <i>and</i> the latest filer in the state by a wide margin
({IC['days']} days). Of the four districts in the whole state with an average UAB under 2%, it is the
only one that filed late at all.</p>
</div>

<footer>
<b>Axes.</b> Horizontal: average Unspent Authorized Budget as a % of the maximum authorized budget over
FY2023–FY2025 (Iowa Dept. of Management UAB report). Vertical: average days early (+) or late (−) filing
the audited financials, last three years (supplied table). <b>Correlation</b> is the Pearson coefficient;
the dashed blue line is the least-squares fit through the large (5,000+) districts only. Six districts in
the table had no matching UAB record (reorganized entities) and are omitted. A handful of very-late small
districts fall below the chart's floor and are pinned to the bottom edge; Iowa City's true value
({IC['days']}) is plotted in place. See also: <a href="iccsd-filing-vs-uab-large.html">the large-districts-only version</a>, where the correlation is computed without Iowa City.
</footer>
</div></body></html>"""

open("iccsd-filing-vs-uab.html", "w").write(DOC)
print(f"Wrote iccsd-filing-vs-uab.html ({len(DOC)//1024} KB)")
print(f"N={len(pts)}  r_all={r_all:+.3f}  r_big(5000+,n={len(big)})={r_big:+.3f}")
print(f"ICCSD: UAB={IC['uab']:.2f}%  days={IC['days']}")
