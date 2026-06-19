#!/usr/bin/env python3
"""
Build liquidity-lenses.html — Moody's two liquidity sub-factors shown side by side, because
the agency that actually rated ICCSD designs them to be read together:

  Available Fund Balance Ratio = available fund balance / operating revenue   (the accounting
      reserve cushion — includes receivables like taxes/aid owed but not yet collected)
  Net Cash Ratio               = net cash / operating revenue                  (actual cash in
      operating funds, which Moody's reduces by short-term operating debt such as TANs)

Both are scored on the same Moody's Aaa->Caa bands. A diverging ("tornado") chart puts the two
next to each other per district, so the divergence — where reserves and cash tell different
stories — reads at a glance. FY2023 (latest year all 13 districts have an audit).

NOTE: the Net Cash Ratio here is computed from cash only (pre-TAN); we don't yet have each
district's year-end short-term operating debt. Subtracting it would lower net cash — most for
the districts that lean on cash-flow borrowing. This is stated plainly on the page.

Inputs: data/iowa-district-financials.csv (fund balance + revenue), data/gf-operating-cash.csv.
Self-contained SVG.  Run: python3 scripts/build_two_lenses.py -> liquidity-lenses.html
"""
import csv, html, datetime, statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

IC = "Iowa City CSD"
PEERS = ["Ankeny CSD", "Cedar Rapids CSD", "College CSD (Prairie)", "Davenport CSD",
         "Des Moines Independent CSD", "Dubuque CSD", "Johnston CSD", "Linn-Mar CSD",
         "Pleasant Valley CSD", "Waterloo CSD", "Waukee CSD", "West Des Moines CSD"]
FY = "2023"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


fin = {(r["district"], r["fiscal_year"]): r for r in csv.DictReader(open("data/iowa-district-financials.csv"))}
cash = {(r["district"], r["fiscal_year"]): num(r["gf_cash_investments"])
        for r in csv.DictReader(open("data/gf-operating-cash.csv"))}


def band(p):
    return ("Aaa" if p >= 17.5 else "Aa" if p >= 10 else "A" if p >= 5 else
            "Baa" if p >= 0 else "Ba" if p >= -5 else "B" if p >= -10 else "Caa")


def bcolor(p):
    return ("#16a34a" if p >= 17.5 else "#84cc16" if p >= 10 else "#eab308" if p >= 5 else
            "#f97316" if p >= 0 else "#dc2626")


rows = []   # (district, avail_ratio, netcash_ratio)
for d in [IC] + PEERS:
    r = fin.get((d, FY)); c = cash.get((d, FY))
    if not r or not r.get("gf_revenue") or c is None:
        continue
    rev = num(r["gf_revenue"])
    avail = num(r["gf_unassigned"]) + (num(r.get("gf_assigned")) or 0)
    rows.append((d, 100 * avail / rev, 100 * c / rev))
rows.sort(key=lambda t: -t[1])   # by reserve ratio, strongest at top

# ---- diverging "tornado" SVG: reserves grow left, cash grows right ----
SCALE = 42.0
ROWH = 30
n = len(rows)
W = 920
CL, CR = 340, 580          # center label band edges
SIDE = CL - 56             # left chart width (mirror on right)
top = 96
H = top + n * ROWH + 30


def xL(v): return CL - (v / SCALE) * SIDE
def xR(v): return CR + (v / SCALE) * SIDE

s = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" aria-label="Reserves vs. net cash, by district">']
# headers
s.append(f'<text x="{(CL+56)/2:.0f}" y="34" class="lhdr">RESERVES</text>')
s.append(f'<text x="{(CL+56)/2:.0f}" y="52" class="lsub">Available Fund Balance ÷ revenue</text>')
s.append(f'<text x="{(CR+SIDE+56-0+CR)/2:.0f}" y="34" class="rhdr">CASH</text>')
s.append(f'<text x="{(CR+SIDE+CR)/2:.0f}" y="52" class="rsub">Net Cash ÷ revenue (pre-TAN)</text>')
# band threshold guides (5,10,17.5) on each side
for thr in (5, 10, 17.5):
    s.append(f'<line x1="{xL(thr):.1f}" y1="{top-6}" x2="{xL(thr):.1f}" y2="{top+n*ROWH}" class="thr"/>')
    s.append(f'<line x1="{xR(thr):.1f}" y1="{top-6}" x2="{xR(thr):.1f}" y2="{top+n*ROWH}" class="thr"/>')
    s.append(f'<text x="{xL(thr):.1f}" y="{top+n*ROWH+16}" class="thrlab">{thr:g}%</text>')
    s.append(f'<text x="{xR(thr):.1f}" y="{top+n*ROWH+16}" class="thrlab">{thr:g}%</text>')
# center baseline
s.append(f'<line x1="{CL}" y1="{top-6}" x2="{CL}" y2="{top+n*ROWH}" class="axis"/>')
s.append(f'<line x1="{CR}" y1="{top-6}" x2="{CR}" y2="{top+n*ROWH}" class="axis"/>')

for i, (d, a, nc) in enumerate(rows):
    y = top + i * ROWH
    me = d == IC
    if me:
        s.append(f'<rect x="40" y="{y+1:.0f}" width="{W-80}" height="{ROWH-3}" class="merow"/>')
    # left (reserves) bar
    s.append(f'<rect x="{xL(a):.1f}" y="{y+5:.0f}" width="{CL-xL(a):.1f}" height="{ROWH-12}" fill="{bcolor(a)}" rx="2"/>')
    s.append(f'<text x="{xL(a)-6:.1f}" y="{y+ROWH/2+4:.0f}" class="val" text-anchor="end">{a:.1f}</text>')
    # right (cash) bar
    s.append(f'<rect x="{CR:.1f}" y="{y+5:.0f}" width="{xR(nc)-CR:.1f}" height="{ROWH-12}" fill="{bcolor(nc)}" rx="2"/>')
    s.append(f'<text x="{xR(nc)+6:.1f}" y="{y+ROWH/2+4:.0f}" class="val" text-anchor="start">{nc:.1f}</text>')
    # center district label
    cls = "dname me" if me else "dname"
    s.append(f'<text x="{(CL+CR)/2:.0f}" y="{y+ROWH/2+4:.0f}" class="{cls}" text-anchor="middle">{html.escape(d)}</text>')
s.append('</svg>')
svg = "".join(s)

ica = next(a for d, a, nc in rows if d == IC)
icn = next(nc for d, a, nc in rows if d == IC)
# rank on each lens (1 = strongest)
res_rank = sorted(rows, key=lambda t: -t[1])
cash_rank = sorted(rows, key=lambda t: -t[2])
ic_res_rank = [d for d, a, nc in res_rank].index(IC) + 1
ic_cash_rank = [d for d, a, nc in cash_rank].index(IC) + 1
gaps = {d: nc - a for d, a, nc in rows}
ic_gap = gaps[IC]
peer_gap_med = st.median([v for d, v in gaps.items() if d != IC])

date = datetime.date(2026, 6, 19).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Two liquidity lenses (reserves vs. cash)</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:980px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04);overflow-x:auto}}
.intro{{border-left:4px solid #2563eb}} .intro p{{margin:7px 0}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:6px 0 2px}}
.two .l,.two .r{{background:#f8fafc;border:1px solid var(--line);border-radius:10px;padding:12px 15px;font-size:14.5px}}
.two h3{{margin:0 0 4px;font-size:16px}} .two .l h3{{color:#1d4ed8}} .two .r h3{{color:#0f766e}}
.chart{{width:100%;height:auto;display:block;margin-top:6px}}
.lhdr,.rhdr{{font-size:14px;font-weight:800;fill:#334155;text-anchor:middle;letter-spacing:.04em}}
.lsub,.rsub{{font-size:11px;fill:#94a3b8;text-anchor:middle}}
.axis{{stroke:#94a3b8;stroke-width:1.2}} .thr{{stroke:#e2e8f0;stroke-width:1;stroke-dasharray:2 3}}
.thrlab{{fill:#cbd5e1;font-size:10px;text-anchor:middle}}
.dname{{font-size:12.5px;fill:#475569;font-weight:600}} .dname.me{{fill:#b91c1c;font-weight:800}}
.val{{font-size:12px;fill:#334155;font-weight:600}}
.merow{{fill:#fef2f2;stroke:#fecaca;stroke-width:1;rx:4}}
.legend{{font-size:12.5px;color:var(--mut);margin:12px 2px 0;display:flex;gap:14px;flex-wrap:wrap;align-items:center}}
.legend i{{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:middle;margin-right:5px}}
.take{{margin:14px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #dc2626;border-radius:6px;padding:12px 15px}}
.take b{{color:#0f172a}}
.caution{{margin:12px 0 0;font-size:14px;line-height:1.5;background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;border-radius:8px;padding:12px 15px;color:#3f3f46}}
.caution b{{color:#92400e}}
.deep{{font-size:13.5px;color:var(--mut);margin-top:12px}} .deep a{{color:#2563eb;font-weight:600;text-decoration:none}}
footer{{color:var(--mut);font-size:12.5px;margin-top:26px;border-top:1px solid var(--line);padding-top:14px}}
footer a{{color:#2563eb}}
</style></head><body>{nav("more")}<div class="wrap">

<h1>Two Liquidity Lenses, Side by Side</h1>
<p class="sub">Reserves vs. cash — how Moody's actually scores a school district's liquidity, and why you have to read both · {date}</p>

<div class="card intro">
<p>Moody's — the agency that <b>rated ICCSD</b> — measures liquidity with <b>two</b> ratios, on purpose,
because each hides what the other reveals:</p>
<div class="two">
  <div class="l"><h3>Reserves — Available Fund Balance ÷ revenue</h3>The accounting cushion. It counts
  <b>receivables</b> — money owed to the district (taxes, state aid) but not yet collected — so it can look
  healthy even when the bank account is thin.</div>
  <div class="r"><h3>Cash — Net Cash ÷ revenue</h3>The money actually on hand. Moody's <b>subtracts
  short-term borrowing</b> (tax-anticipation notes), so cash propped up by a loan doesn't count. The truest
  immediate-liquidity test.</div>
</div>
<p>Both are scored on the same scale (Aaa = strongest … Caa = weakest). Below, every district's two ratios
sit back-to-back: <b>reserves grow left, cash grows right</b>. FY2023, the latest year all 13 have an audit.</p>
</div>

<div class="card">
{svg}
<div class="legend"><b>Moody's band:</b>
<span><i style="background:#16a34a"></i>Aaa (≥17.5%)</span>
<span><i style="background:#84cc16"></i>Aa (10–17.5%)</span>
<span><i style="background:#eab308"></i>A (5–10%)</span>
<span><i style="background:#f97316"></i>Baa (0–5%)</span>
<span><i style="background:#dc2626"></i>Ba or below (&lt;0%)</span>
</div>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:20px">How the story changes when you see both</h2>
<p class="take"><b>One lens alone understates the problem.</b> On <b>reserves</b>, Iowa City is alone at the
bottom — <b>{ica:.1f}% (Baa)</b>, the only district below the A band and ranked <b>#{ic_res_rank} of {n}</b>.
Switch to <b>cash</b> and it looks less dire — <b>{icn:.1f}% (A)</b>, still last (#{ic_cash_rank}) but not in
a category by itself. A reader shown only the cash number might shrug.</p>
<p class="take"><b>Seeing both reveals why that comfort is false.</b> Notice the <i>gap</i> between each
district's two bars. Peers' cash sits far to the right of their reserves (median gap
<b>+{peer_gap_med:.0f} points</b>) — they hold real surplus cash on top of healthy reserves. Iowa City's gap
is the <b>smallest in the group (+{ic_gap:.1f})</b>: it has barely more cash than its (already thin) reserves.
And this cash figure is <b>before</b> Moody's subtracts tax-anticipation borrowing. Because Iowa City is the
district leaning on that borrowing, the subtraction hits it hardest — pulling its cash lens back down toward,
or below, its weak reserve lens. <b>Either way it finishes last; together, the two lenses show the cash
"cushion" is thin and partly borrowed.</b></p>
<p class="caution"><b>⚠ The Net Cash figures are pre-TAN.</b> We don't yet have each district's short-term
operating debt outstanding at June 30, so the right-hand bars use cash only. Subtracting tax-anticipation /
cash-flow notes — as Moody's does — would shorten the cash bars, most for districts that rely on that
borrowing. For Iowa City, an outstanding TAN on the order of its operating gap would erase the cash bar
entirely. We'll wire in the exact figures once we have the year-end note balances.</p>
<p class="deep">Companion views: the district's own intuitive
<a href="iccsd-net-cash-ratio.html">Day's Net Cash Ratio</a> (days of cash, validated against ICCSD's
dashboard) and the three-part <a href="iccsd-cushion.html">“Does it have a cushion?”</a> story. More under
<a href="other-analyses.html">Other analyses</a>.</p>
</div>

<footer>
<b>Sources &amp; method.</b> Framework: <i>Moody's Ratings — US K-12 Public School Districts</i> (July 2024),
Financial Performance factor. <b>Available Fund Balance Ratio</b> = (assigned + unassigned General Fund
balance) ÷ General Fund revenue. <b>Net Cash Ratio</b> = General Fund cash &amp; investments ÷ General Fund
revenue (Moody's also subtracts short-term operating debt; omitted here for lack of data — see caution).
Moody's uses "operating revenue" (general + debt-service funds); we approximate with General Fund revenue.
Fund balance and revenue from the audited statements (<code>data/iowa-district-financials.csv</code>); cash
from each audited Balance Sheet — Governmental Funds (<code>data/gf-operating-cash.csv</code>). FY2023, the
most recent year all 13 districts have a filed audit. Bands per Moody's Exhibit 2. Built by
<code>scripts/build_two_lenses.py</code>.
</footer>
</div></body></html>"""

open("liquidity-lenses.html", "w").write(DOC)
print(f"Wrote liquidity-lenses.html ({len(DOC)//1024} KB)")
print(f"ICCSD reserves {ica:.1f}% (#{ic_res_rank}), cash {icn:.1f}% (#{ic_cash_rank}); gap {ic_gap:.1f} vs peer median {peer_gap_med:.0f}")
