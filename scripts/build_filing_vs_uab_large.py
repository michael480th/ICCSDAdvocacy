#!/usr/bin/env python3
"""
Scatterplot (LARGE districts only, 5,000+ students): audit-filing timeliness vs. UAB cushion.

X = average Unspent Authorized Budget (% of budget), FY2023-2025 (DOM UAB workbook).
Y = average days early (+) / late (-) filing audited financials (supplied table, /tmp/filing.tsv).

The Pearson correlation / regression line are computed on the large districts EXCLUDING Iowa City,
because Iowa City is an extreme outlier (lowest cushion + latest filing in the state) that single-
handedly drives the slope. Iowa City is still plotted, marked as the excluded outlier.

Run:  python3 scripts/build_filing_vs_uab_large.py  ->  iccsd-filing-vs-uab-large.html
"""
import openpyxl, re, html, datetime, statistics as st, math

# ---- filing table ----
recs = []
for ln in open("/tmp/filing.tsv"):
    p = ln.rstrip("\n").split("\t")
    if len(p) < 4:
        continue
    recs.append(dict(name=p[0].strip(), code=int(p[1]),
                     enr=int(re.sub(r"[, ]", "", p[2])),
                     days=(-1 if p[-1].strip().startswith("(") else 1) * int(re.sub(r"[(),]", "", p[-1]))))

# ---- UAB FY2023-2025 average ----
ws = openpyxl.load_workbook("UAB/Unspent Authorized Budget Report.xlsx", data_only=True, read_only=True)["data_UAB"]
uab = {}
for r in ws.iter_rows(min_row=2, values_only=True):
    if isinstance(r[0], int) and r[0] in (2023, 2024, 2025) and r[1] and r[37]:
        try:
            c = int(r[1])
        except (TypeError, ValueError):
            continue
        uab.setdefault(c, {})[r[0]] = 100 * r[38] / r[37]

big = []
for rec in recs:
    if rec["enr"] >= 5000 and rec["code"] in uab:
        rec["uab"] = st.mean(uab[rec["code"]].values())
        big.append(rec)
IC = next(p for p in big if p["code"] == 3141)
others = [p for p in big if p["code"] != 3141]          # excludes Iowa City


def pearson(x, y):
    mx, my = st.mean(x), st.mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def linreg(x, y):
    mx, my = st.mean(x), st.mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return b, my - b * mx


ox, oy = [p["uab"] for p in others], [p["days"] for p in others]
r_excl = pearson(ox, oy)
r_incl = pearson([p["uab"] for p in big], [p["days"] for p in big])
slope, intc = linreg(ox, oy)

# ---------- SVG ----------
W, H = 820, 560
L, Rm, T, B = 72, 130, 28, 58
pw, ph = W - L - Rm, H - T - B
XMIN, XMAX, YMIN, YMAX = 0, 34, -450, 150
def X(v): return L + pw * (v - XMIN) / (XMAX - XMIN)
def Y(v): return T + ph * (YMAX - v) / (YMAX - YMIN)

s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="large district scatter">']
for gx in range(0, 35, 5):
    s.append(f'<line x1="{X(gx):.1f}" y1="{T}" x2="{X(gx):.1f}" y2="{T+ph}" class="grid"/>')
    s.append(f'<text x="{X(gx):.1f}" y="{T+ph+20}" class="xtick">{gx}%</text>')
for gy in range(-450, 151, 75):
    s.append(f'<line x1="{L}" y1="{Y(gy):.1f}" x2="{L+pw}" y2="{Y(gy):.1f}" class="grid"/>')
    s.append(f'<text x="{L-8}" y="{Y(gy)+4:.1f}" class="ytick">{gy:+d}</text>')
s.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{L+pw}" y2="{Y(0):.1f}" class="zero"/>')
s.append(f'<text x="{L+8}" y="{Y(0)-6:.1f}" class="zlab">on time — above = early, below = late</text>')
# regression line (fit on the 17, excl. Iowa City) across full UAB range
s.append(f'<line x1="{X(XMIN):.1f}" y1="{Y(slope*XMIN+intc):.1f}" x2="{X(XMAX):.1f}" y2="{Y(slope*XMAX+intc):.1f}" class="fit"/>')
s.append(f'<text x="{X(XMAX)-4:.1f}" y="{Y(slope*XMAX+intc)-7:.1f}" class="fitlab">best fit (excl. Iowa City) — essentially flat</text>')

# greedy label placement to reduce overlap
placed = []
def put_label(px, py, text, cls):
    lx, ly = px + 8, py + 4
    while any(abs(ly - q) < 13 and abs(lx - qx) < 95 for qx, q in placed):
        ly += 13
    placed.append((lx, ly))
    s.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="{cls}">{html.escape(text)}</text>')

for p in sorted(others, key=lambda d: (-d["days"], d["uab"])):
    cx, cy = X(p["uab"]), Y(p["days"])
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" class="dot lg"/>')
    put_label(cx, cy, p["name"].replace(" CSD", "").replace(" Independent", ""), "lglab")
# Iowa City outlier
cx, cy = X(IC["uab"]), Y(IC["days"])
s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7.5" class="dot ic"/>')
s.append(f'<text x="{cx+11:.1f}" y="{cy+4:.1f}" class="iclab">Iowa City — {IC["uab"]:.1f}% UAB, {IC["days"]} days (excluded from r)</text>')
s.append(f'<text x="{L+pw/2:.1f}" y="{H-8}" class="axt">Average spending-authority cushion (UAB %, FY2023–2025) — higher = more cushion →</text>')
s.append(f'<text transform="translate(16,{T+ph/2:.1f}) rotate(-90)" class="axt" text-anchor="middle">Days early (+) / late (−) filing audit ↑</text>')
s.append('</svg>')
svg = "".join(s)

date = datetime.date(2026, 6, 9).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Audit timeliness vs. cushion — large Iowa districts</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:900px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:27px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.chart{{width:100%;height:auto;display:block}}
.grid{{stroke:#eef2f7;stroke-width:1}}
.xtick{{fill:#64748b;font-size:12px;text-anchor:middle}} .ytick{{fill:#94a3b8;font-size:12px;text-anchor:end}}
.zero{{stroke:#0f172a;stroke-width:1;stroke-dasharray:4 3;opacity:.5}} .zlab{{fill:#475569;font-size:11px}}
.fit{{stroke:#2563eb;stroke-width:2;stroke-dasharray:6 4;opacity:.85}} .fitlab{{fill:#1d4ed8;font-size:11px;text-anchor:end}}
.dot.lg{{fill:#2563eb;opacity:.88}} .dot.ic{{fill:#dc2626;stroke:#fff;stroke-width:1.5}}
.lglab{{fill:#1e3a8a;font-size:11px}} .iclab{{fill:#dc2626;font-size:12.5px;font-weight:700}}
.axt{{fill:#334155;font-size:12.5px;text-anchor:middle}}
.stats{{display:flex;gap:14px;flex-wrap:wrap;margin:4px 0 14px}}
.stat{{background:#f8fafc;border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:160px}}
.stat .n{{font-size:24px;font-weight:800}} .stat .l{{font-size:12px;color:var(--mut)}}
.take{{margin:14px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #dc2626;border-radius:6px;padding:10px 14px}}
.take b{{color:#0f172a}}
footer{{color:var(--mut);font-size:12.5px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body><div class="wrap">

<h1>Audit timeliness vs. financial cushion — large districts only</h1>
<p class="sub">Iowa districts with 5,000+ students (n={len(big)}); correlation computed without Iowa City · {date}</p>

<div class="card">
<div class="stats">
  <div class="stat"><div class="n">{r_excl:+.2f}</div><div class="l">correlation (r), <b>17 large districts, Iowa City excluded</b></div></div>
  <div class="stat"><div class="n">{r_incl:+.2f}</div><div class="l">correlation (r) <b>if Iowa City is included</b> (one point drives it)</div></div>
  <div class="stat"><div class="n">{IC['days']}</div><div class="l">Iowa City days late — the extreme outlier</div></div>
</div>
{svg}
<p class="take"><b>Among large districts, there is no real correlation (r = {r_excl:+.2f}) once Iowa City is
set aside.</b> The other 17 big districts are scattered — Waukee and Marshalltown both carry ~30% cushions
yet file 108 and 9 days early respectively; Linn-Mar and Pleasant Valley sit at very different cushions but
both file ~3–4 months early. Cushion size simply doesn't predict how fast a large district files.
<b>The +0.40 correlation from the earlier all-large-districts chart was Iowa City alone</b> — a single
point in the low-cushion / very-late corner that pulls a slope out of an otherwise flat cloud. Iowa City
isn't the end of a trend; it's a category of its own: the thinnest cushion <i>and</i> the latest audit in
the state, by a wide margin.</p>
</div>

<footer>
<b>Axes.</b> Horizontal: average Unspent Authorized Budget as a % of the maximum authorized budget,
FY2023–FY2025 (Iowa Dept. of Management). Vertical: average days early (+) / late (−) filing audited
financials, last three years (supplied table). <b>r</b> and the dashed best-fit line are computed on the
17 large districts excluding Iowa City; Iowa City ({IC['days']} days) is plotted but held out of the math
as an extreme outlier. "Large" = 5,000+ certified students.
</footer>
</div></body></html>"""

open("iccsd-filing-vs-uab-large.html", "w").write(DOC)
print(f"Wrote iccsd-filing-vs-uab-large.html ({len(DOC)//1024} KB)")
print(f"n_large={len(big)}  r_excl_ICCSD={r_excl:+.3f}  r_incl_ICCSD={r_incl:+.3f}  slope={slope:.2f}")
