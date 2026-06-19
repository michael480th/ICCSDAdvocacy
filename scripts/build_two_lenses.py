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
FY = "2025"


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


fin = {(r["district"], r["fiscal_year"]): r for r in csv.DictReader(open("data/iowa-district-financials.csv"))}
cash = {(r["district"], r["fiscal_year"]): num(r["gf_cash_investments"])
        for r in csv.DictReader(open("data/gf-operating-cash.csv"))}

# General Fund expenditures (for the district's days-based KPI denominator)
exp = {}
for r in csv.DictReader(open("data/audit-financials.csv")):
    if r["expenditures"]:
        exp[(r["district"], r["fiscal_year"])] = num(r["expenditures"])
for r in csv.DictReader(open("data/iowa-district-financials.csv")):
    if r.get("gf_expenditure"):
        exp.setdefault((r["district"], r["fiscal_year"]), num(r["gf_expenditure"]))


def band(p):
    return ("Aaa" if p >= 17.5 else "Aa" if p >= 10 else "A" if p >= 5 else
            "Baa" if p >= 0 else "Ba" if p >= -5 else "B" if p >= -10 else "Caa")


def bcolor(p):
    return ("#16a34a" if p >= 17.5 else "#84cc16" if p >= 10 else "#eab308" if p >= 5 else
            "#f97316" if p >= 0 else "#dc2626")


# Iowa City has no FY2025 audit, so no audited available fund balance (the reserves lens). Use
# the district's own internal General Fund figures (PFM Exhibit 1) for the cash and days lenses.
IC_CASH = IC_REV = IC_DAYS = None
for r in csv.DictReader(open("data/iccsd-cash-supplemental.csv")):
    if r["fiscal_year"] == FY:
        IC_CASH, IC_REV, IC_DAYS = num(r["gf_cash_investments"]), num(r.get("gf_revenue")), num(r.get("days_cash"))

rows = []   # (district, avail_ratio_or_None, netcash_ratio); None reserves = no audit
for d in PEERS:
    r = fin.get((d, FY)); c = cash.get((d, FY))
    if not r or not r.get("gf_revenue") or c is None:
        continue
    rev = num(r["gf_revenue"])
    avail = num(r["gf_unassigned"]) + (num(r.get("gf_assigned")) or 0)
    rows.append((d, 100 * avail / rev, 100 * c / rev))
if IC_CASH and IC_REV:
    rows.append((IC, None, 100 * IC_CASH / IC_REV))   # reserves unavailable (no FY25 audit)
rows.sort(key=lambda t: -(t[1] if t[1] is not None else -1e9))   # ICCSD (None) sorts to the bottom

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
    # left (reserves) bar — or a "no audit" gap marker (Iowa City FY2025)
    if a is None:
        s.append(f'<text x="{CL-8:.1f}" y="{y+ROWH/2+4:.0f}" class="nodata" text-anchor="end">no FY25 audit — reserves can\'t be measured</text>')
    else:
        s.append(f'<rect x="{xL(a):.1f}" y="{y+5:.0f}" width="{CL-xL(a):.1f}" height="{ROWH-12}" fill="{bcolor(a)}" rx="2"/>')
        s.append(f'<text x="{xL(a)-6:.1f}" y="{y+ROWH/2+4:.0f}" class="val" text-anchor="end">{a:.1f}</text>')
    # right (cash) bar (Iowa City unaudited: dashed outline + asterisk)
    flag = ' stroke="#b91c1c" stroke-width="1.4" stroke-dasharray="4 2" opacity="0.85"' if me else ''
    s.append(f'<rect x="{CR:.1f}" y="{y+5:.0f}" width="{xR(nc)-CR:.1f}" height="{ROWH-12}" fill="{bcolor(nc)}" rx="2"{flag}/>')
    s.append(f'<text x="{xR(nc)+6:.1f}" y="{y+ROWH/2+4:.0f}" class="val" text-anchor="start">{nc:.1f}{"*" if me else ""}</text>')
    # center district label
    cls = "dname me" if me else "dname"
    s.append(f'<text x="{(CL+CR)/2:.0f}" y="{y+ROWH/2+4:.0f}" class="{cls}" text-anchor="middle">{html.escape(d)}</text>')
s.append('</svg>')
svg = "".join(s)

# ---- third lens: the district's own Day's Net Cash Ratio (days) ----
def dcolor(v): return "#16a34a" if v >= 90 else "#eab308" if v >= 60 else "#dc2626"


drows = []   # (district, days)
for d in PEERS:
    c = cash.get((d, FY)); e = exp.get((d, FY))
    if c is not None and e:
        drows.append((d, c / (e / 365.0)))
if IC_DAYS:
    drows.append((IC, IC_DAYS))   # Iowa City: district's own stated FY2025 days
drows.sort(key=lambda t: -t[1])

DSCALE = 160.0
DLAB = 230               # left label band width
DX0 = DLAB               # bars start here
DBW = W - DLAB - 60      # bar area width
dtop = 30
dH = dtop + len(drows) * ROWH + 30
def dX(v): return DX0 + (v / DSCALE) * DBW

ds = [f'<svg viewBox="0 0 {W} {dH}" class="chart" role="img" aria-label="Day\'s Net Cash Ratio (days) by district">']
# 90-120 recommended band
ds.append(f'<rect x="{dX(90):.1f}" y="{dtop-4}" width="{dX(120)-dX(90):.1f}" height="{len(drows)*ROWH}" fill="#16a34a" opacity="0.10"/>')
ds.append(f'<text x="{dX(105):.1f}" y="{dtop-8}" class="dbandlab" text-anchor="middle">recommended 90–120 days</text>')
for g in (60, 90, 120, 150):
    ds.append(f'<line x1="{dX(g):.1f}" y1="{dtop-4}" x2="{dX(g):.1f}" y2="{dtop+len(drows)*ROWH}" class="thr"/>')
    ds.append(f'<text x="{dX(g):.1f}" y="{dtop+len(drows)*ROWH+16}" class="thrlab">{g}</text>')
for i, (d, v) in enumerate(drows):
    y = dtop + i * ROWH
    me = d == IC
    if me:
        ds.append(f'<rect x="40" y="{y+1:.0f}" width="{W-80}" height="{ROWH-3}" class="merow"/>')
    ds.append(f'<text x="{DLAB-10:.0f}" y="{y+ROWH/2+4:.0f}" class="{"dname me" if me else "dname"}" text-anchor="end">{html.escape(d)}</text>')
    ds.append(f'<rect x="{DX0:.1f}" y="{y+5:.0f}" width="{dX(v)-DX0:.1f}" height="{ROWH-12}" fill="{dcolor(v)}" rx="2"/>')
    ds.append(f'<text x="{dX(v)+6:.1f}" y="{y+ROWH/2+4:.0f}" class="val" text-anchor="start">{v:.0f}</text>')
ds.append('</svg>')
dsvg = "".join(ds)
icd = next(v for d, v in drows if d == IC)
ic_days_rank = [d for d, v in drows].index(IC) + 1
peer_days_med = st.median([v for d, v in drows if d != IC])

ica = None   # Iowa City has no FY2025 audited reserves figure (audit not filed)
icn = next(nc for d, a, nc in rows if d == IC)
n = len(rows)
cash_rank = sorted(rows, key=lambda t: -t[2])
ic_cash_rank = [d for d, a, nc in cash_rank].index(IC) + 1
# reserves/gap stats over peers only (ICCSD has no reserves figure)
peer_res_med = st.median([a for d, a, nc in rows if a is not None])
peer_cash_med = st.median([nc for d, a, nc in rows if d != IC])
gaps = {d: nc - a for d, a, nc in rows if a is not None}
peer_gap_med = st.median(list(gaps.values()))

date = datetime.date(2026, 6, 19).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Three liquidity lenses (reserves, cash, days)</title>
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
.dbandlab{{fill:#16a34a;font-size:11px;opacity:.9}}
.dname{{font-size:12.5px;fill:#475569;font-weight:600}} .dname.me{{fill:#b91c1c;font-weight:800}}
.nodata{{fill:#b91c1c;font-size:10px;font-style:italic;font-weight:600}}
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

<h1>Three Liquidity Lenses, Side by Side</h1>
<p class="sub">Reserves, cash, and days — the same liquidity, three very different-looking numbers · FY2025 (peers audited; Iowa City internal) · {date}</p>

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
<p>We then add a <b>third lens the district uses on its own dashboard</b> — <b>Day's Net Cash Ratio</b>
(cash ÷ average daily spending = days of cash on hand). It measures almost the same thing as the cash ratio,
but expressed in <b>days</b> rather than a percent — which, as you'll see, makes the very same position
sound far less alarming.</p>
</div>

<div class="card">
<p style="margin:0 0 2px;font-size:13px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;font-weight:700">Lenses 1 &amp; 2 — Moody's ratios (% of revenue)</p>
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
<p style="margin:0 0 2px;font-size:13px;color:#64748b;text-transform:uppercase;letter-spacing:.04em;font-weight:700">Lens 3 — the district's own KPI (days of cash)</p>
<p style="margin:2px 0 0;font-size:14px;color:#475569"><b>Day's Net Cash Ratio</b> = Cash &amp; Investments ÷ (Total Expenditures ÷ 365). FY2025; the district's own target is 90+ days. Iowa City's FY2025 is its own internal figure (unaudited).</p>
{dsvg}
<div class="legend"><b>Days band:</b>
<span><i style="background:#16a34a"></i>≥ 90 (in range)</span>
<span><i style="background:#eab308"></i>60–90</span>
<span><i style="background:#dc2626"></i>&lt; 60</span>
</div>
</div>

<div class="card">
<h2 style="margin:0 0 4px;font-size:20px">How the story changes across the three lenses</h2>
<p class="take"><b>The most important lens is the one Iowa City can't show.</b> For FY2025 every peer posts an
audited <b>reserves</b> ratio (peer median ~<b>{peer_res_med:.0f}%</b>) — the single number a rating analyst
reaches for first. Iowa City has <b>no bar at all</b>: its FY2025 audit isn't filed, so the figure simply
doesn't exist. A blank where every peer has a measurable green bar is, by itself, the story.</p>
<p class="take"><b>On the measures it can report, it sits in the bottom group — and the unit flatters it.</b>
From its own internal books Iowa City reads as <b>{icn:.1f}% net cash</b> and <b>{icd:.0f} days of cash</b> —
"days" being the friendlier-sounding number ("33 days" lands softer than "9%"). Both land it <b>#{ic_cash_rank}
of {n}</b>, well below the peer medians (~<b>{peer_cash_med:.0f}% net cash</b>, ~<b>{peer_days_med:.0f} days</b>).
Two peers with their own troubles (College/Prairie, Waterloo) sit even lower — but Iowa City is firmly in the
weakest group <i>and</i>, unlike them, has no reserves figure to fall back on.</p>
<p class="take"><b>And even that cash figure is generous.</b> The net-cash bar is shown <i>before</i> Moody's
subtracts short-term borrowing. Iowa City is precisely the district leaning on it — a planned <b>$25M
tax-anticipation warrant</b> plus a <b>$10M interfund loan</b> in FY2026. Net that out, as Moody's does, and
the one lens Iowa City still has collapses further. Peers' cash mostly sits well above their reserves (median
gap <b>+{peer_gap_med:.0f} points</b>) because it's <i>real surplus</i>; Iowa City's is thin and partly borrowed.</p>
<p class="caution"><b>⚠ Iowa City's FY2025 bars are unaudited (dashed outline), and pre-TAN.</b> Peers use
audited FY2025 figures; Iowa City has no FY2025 audit, so its cash &amp; revenue come from the district's own
internal report (PFM Exhibit 1) and its reserves can't be computed at all. The net-cash bars (all districts)
are also gross of short-term borrowing — we don't yet have year-end tax-anticipation balances; subtracting
them would shorten the cash bars, most for the borrowers (chiefly Iowa City).</p>
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
Peer fund balance, revenue and cash from their <b>audited FY2025</b> statements
(<code>data/iowa-district-financials.csv</code>, <code>data/gf-operating-cash.csv</code>). <b>Iowa City has no
FY2025 audit</b>, so its reserves ratio can't be computed; its cash ($19.4M) and revenue ($211.8M) for the
net-cash and days lenses come from the district's own internal report (PFM Exhibit 1,
<code>data/iccsd-cash-supplemental.csv</code>) and are unaudited. Bands per Moody's Exhibit 2. Built by
<code>scripts/build_two_lenses.py</code>.
</footer>
</div></body></html>"""

open("liquidity-lenses.html", "w").write(DOC)
print(f"Wrote liquidity-lenses.html ({len(DOC)//1024} KB)")
print(f"FY{FY}: ICCSD reserves=N/A (no audit), cash {icn:.1f}% (#{ic_cash_rank} of {n}), days {icd:.0f}; "
      f"peer medians res {peer_res_med:.0f}% / cash {peer_cash_med:.0f}% / days {peer_days_med:.0f}")
