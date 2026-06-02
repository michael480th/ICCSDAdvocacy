#!/usr/bin/env python3
"""Generate iowa-district-financial-benchmark.html from /tmp/audit/cards.json."""
import json, html, datetime

cards = json.load(open("/tmp/audit/cards.json"))

def color(v, lo=1, hi=5):
    if v is None: return "#cbd5e1"
    t = max(0, min(1, (v - lo) / (hi - lo)))
    r = int(220 - t * (220 - 22)); g = int(38 + t * (163 - 38)); b = int(38 + t * (74 - 38))
    return f"rgb({r},{g},{b})"

def badge(v):
    return (f'<span class="badge" style="background:{color(v)}">{v:.1f}</span>'
            if v is not None else '<span class="badge na">n/a</span>')

def spark(series, years, kind="line", zero=True):
    pts = [(i, v) for i, v in enumerate(series) if v is not None]
    if len(pts) < 2: return ""
    vals = [v for _, v in pts]
    lo, hi = min(vals + ([0] if zero else [])), max(vals + ([0] if zero else []))
    rng = (hi - lo) or 1
    W, H, pad = 150, 38, 3
    def X(i): return pad + i * (W - 2*pad) / (len(series) - 1)
    def Y(v): return H - pad - (v - lo) * (H - 2*pad) / rng
    z = f'<line x1="{pad}" y1="{Y(0):.1f}" x2="{W-pad}" y2="{Y(0):.1f}" stroke="#e2e8f0" stroke-width="1"/>' if (zero and lo <= 0 <= hi) else ""
    path = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in pts)
    last = pts[-1]
    dot = f'<circle cx="{X(last[0]):.1f}" cy="{Y(last[1]):.1f}" r="2.6" fill="{ "#16a34a" if last[1] >= (0 if zero else lo) else "#dc2626"}"/>'
    return (f'<svg width="{W}" height="{H}" class="spark">{z}'
            f'<polyline points="{path}" fill="none" stroke="#475569" stroke-width="1.5"/>{dot}</svg>')

# ---- quadrant chart: Health (x) vs Quality (y), bubble = enrollment ----
def quadrant():
    W, H, m = 560, 420, 48
    def X(v): return m + (v - 1) / 4 * (W - 2*m)
    def Y(v): return H - m - (v - 1) / 4 * (H - 2*m)
    parts = [f'<svg viewBox="0 0 {W} {H}" class="quad">']
    parts.append(f'<rect x="{m}" y="{m}" width="{W-2*m}" height="{H-2*m}" fill="#fafafa" stroke="#e2e8f0"/>')
    parts.append(f'<line x1="{X(3)}" y1="{m}" x2="{X(3)}" y2="{H-m}" stroke="#e2e8f0" stroke-dasharray="4"/>')
    parts.append(f'<line x1="{m}" y1="{Y(3)}" x2="{W-m}" y2="{Y(3)}" stroke="#e2e8f0" stroke-dasharray="4"/>')
    for v in (1,2,3,4,5):
        parts.append(f'<text x="{X(v)}" y="{H-m+16}" class="ax">{v}</text>')
        parts.append(f'<text x="{m-12}" y="{Y(v)+3}" class="ax" text-anchor="end">{v}</text>')
    parts.append(f'<text x="{W/2}" y="{H-12}" class="axt">Financial Health →</text>')
    parts.append(f'<text x="16" y="{H/2}" class="axt" transform="rotate(-90 16 {H/2})">Operational Quality →</text>')
    parts.append(f'<text x="{X(4.3)}" y="{Y(4.7)}" class="qn">strong + trustworthy</text>')
    parts.append(f'<text x="{X(1.15)}" y="{Y(1.25)}" class="qn">distressed</text>')
    enrs = [c["enrollment"] or 4000 for c in cards]
    emax = max(enrs)
    for c in cards:
        e = c["enrollment"] or 4000
        r = 7 + (e / emax) * 20
        cx, cy = X(c["health"]), Y(c["quality"])
        fill = color(c["composite"]);
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="0.55" stroke="{fill}" stroke-width="1.5"><title>{html.escape(c["district"])}: H {c["health"]}, Q {c["quality"]}, composite {c["composite"]}</title></circle>')
        short = c["district"].replace(" CSD","").replace(" (Prairie)","").replace(" Independent","")
        parts.append(f'<text x="{cx:.1f}" y="{cy-r-3:.1f}" class="lbl">{html.escape(short)}</text>')
    parts.append('</svg>')
    return "".join(parts)

rows_html = []
for i, c in enumerate(cards, 1):
    flags = "".join(f'<span class="flag">{html.escape(x)}</span>' for x in c["flags"]) or '<span class="ok">— none —</span>'
    cagr = f'{c["enr_cagr"]:+.1f}%/yr' if c["enr_cagr"] is not None else "n/a"
    rows_html.append(f"""<tr>
<td class="rk">{i}</td><td class="dist">{html.escape(c['district'])}</td>
<td>{c['size']}</td><td>{c['enrollment'] or '—'}</td><td class="{ 'pos' if (c['enr_cagr'] or 0)>0 else 'neg' if (c['enr_cagr'] or 0)<0 else ''}">{cagr}</td>
<td class="lab">{html.escape(c['label'])}</td>
<td>{c['solv_last']:.1f}%</td><td class="{ 'pos' if c['marg3']>=0 else 'neg'}">{c['marg3']:.1f}%</td>
<td>{badge(c['health'])}</td><td>{badge(c['quality'])}</td><td>{badge(c['cap_sust'])}</td>
<td>{badge(c['composite'])}</td>
<td class="flags">{flags}</td></tr>""")

cards_html = []
for c in cards:
    flags = "".join(f'<span class="flag">{html.escape(x)}</span>' for x in c["flags"]) or '<span class="ok">no auto-flags</span>'
    sb = f'{c["sbpct"]:.0f}% (est., MD&A)' if c["sbpct"] else 'not in audits'
    cards_html.append(f"""<div class="card">
  <div class="ch"><h3>{html.escape(c['district'])}</h3>
    <span class="comp" style="background:{color(c['composite'])}">{c['composite']:.2f}</span></div>
  <div class="meta">{c['size']} · enrollment {c['enrollment'] or '—'} · {c['fy_first']}–{c['fy_last']} · <b>{html.escape(c['label'])}</b></div>
  <div class="grid">
    <div><span class="k">Health</span>{badge(c['health'])}</div>
    <div><span class="k">Op. Quality</span>{badge(c['quality'])}</div>
    <div><span class="k">Capital sustain.</span>{badge(c['cap_sust'])}</div>
    <div><span class="k">Recognition</span>{'GFOA/ASBO' if c['cert'] else '—'}</div>
  </div>
  <div class="sparks">
    <div><span class="k">Solvency % (FY{c['years'][0]}–{c['years'][-1]})</span>{spark(c['solv_series'], c['years'])}<b>{c['solv_last']:.1f}%</b></div>
    <div><span class="k">Operating margin %</span>{spark(c['marg_series'], c['years'])}<b>{c['marg_series'][-1]:.1f}%</b></div>
  </div>
  <div class="kv"><span>Latest opinion:</span> {html.escape(c['opinion_last'] or '—')} &nbsp;·&nbsp;
     <span>Debt o/s:</span> ${c['debt_last']:.0f}M &nbsp;·&nbsp; <span>Personnel %GF:</span> {sb}</div>
  <div class="cardflags">{flags}</div>
</div>""")

building = sum(1 for c in cards if c["label"].startswith("Building"))
neg_margin = sum(1 for c in cards if c["marg3"] < 0)
date = datetime.date(2026, 6, 2).strftime("%B %Y")

DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa Large-District Financial Benchmark · FY2020–FY2025</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--bg:#f8fafc}}
*{{box-sizing:border-box}}
body{{font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:var(--bg)}}
.wrap{{max-width:1180px;margin:0 auto;padding:34px 22px 80px}}
h1{{font-size:30px;margin:0 0 4px}} h2{{font-size:21px;margin:42px 0 12px;border-bottom:2px solid var(--line);padding-bottom:6px}}
.sub{{color:var(--mut);margin:0 0 8px}} a{{color:#2563eb}}
.cards-summary{{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}}
.sumbox{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 18px;flex:1;min-width:150px}}
.sumbox b{{font-size:26px;display:block}}
.sumbox span{{color:var(--mut);font-size:13px}}
table{{width:100%;border-collapse:collapse;background:#fff;font-size:13.5px;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th,td{{padding:8px 9px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}}
th{{background:#f1f5f9;cursor:pointer;font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:#475569}}
th:hover{{background:#e2e8f0}}
td.dist{{font-weight:600;white-space:normal;min-width:150px}} td.rk{{color:var(--mut)}}
td.lab,.lab{{font-size:12px;color:#334155;white-space:normal;min-width:120px}}
.flags{{white-space:normal;min-width:200px}}
.badge{{color:#fff;border-radius:6px;padding:2px 8px;font-weight:700;font-size:12.5px}}
.badge.na{{background:#cbd5e1}}
.flag{{display:inline-block;background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;border-radius:5px;padding:1px 6px;margin:1px 2px;font-size:11px}}
.ok{{color:#16a34a;font-size:12px}} .pos{{color:#16a34a}} .neg{{color:#dc2626}}
.legend{{display:flex;gap:8px;align-items:center;margin:8px 0 2px;color:var(--mut);font-size:12px}}
.scale{{height:10px;width:160px;border-radius:5px;background:linear-gradient(90deg,rgb(220,38,38),rgb(234,179,8),rgb(22,163,74))}}
.layout{{display:grid;grid-template-columns:1.1fr .9fr;gap:24px;align-items:start}}
@media(max-width:900px){{.layout{{grid-template-columns:1fr}}}}
.quad{{width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:10px}}
.quad .ax{{font-size:10px;fill:#94a3b8;text-anchor:middle}} .quad .axt{{font-size:11px;fill:#475569;text-anchor:middle;font-weight:600}}
.quad .lbl{{font-size:9px;fill:#334155;text-anchor:middle}} .quad .qn{{font-size:10px;fill:#cbd5e1;text-anchor:middle;font-style:italic}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px;margin-top:14px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:15px 16px}}
.ch{{display:flex;justify-content:space-between;align-items:center}} .ch h3{{margin:0;font-size:16px}}
.comp{{color:#fff;font-weight:800;border-radius:8px;padding:3px 11px;font-size:15px}}
.meta{{color:var(--mut);font-size:12.5px;margin:5px 0 11px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;margin-bottom:11px}}
.grid .k,.sparks .k{{display:block;color:var(--mut);font-size:11px;margin-bottom:2px}}
.grid>div{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px dashed var(--line);padding-bottom:4px}}
.sparks{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px}}
.sparks>div{{display:flex;flex-direction:column}} .sparks b{{font-size:13px}} .spark{{margin:2px 0}}
.kv{{font-size:12px;color:#475569;border-top:1px solid var(--line);padding-top:8px}} .kv span{{color:var(--mut)}}
.cardflags{{margin-top:8px}}
.note{{background:#fff;border:1px solid var(--line);border-left:4px solid #2563eb;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:14px}}
.note h4{{margin:0 0 6px}} .note ul{{margin:6px 0 0 18px;padding:0}} .note li{{margin:3px 0}}
footer{{color:var(--mut);font-size:12px;margin-top:50px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body><div class="wrap">

<h1>Iowa Large-District Financial Benchmark</h1>
<p class="sub">15 of Iowa's largest school districts · audited ACFRs, FY2020–FY2025 · compiled {date}</p>

<div class="cards-summary">
  <div class="sumbox"><b>15</b><span>districts benchmarked</span></div>
  <div class="sumbox"><b>88</b><span>audited district-years extracted</span></div>
  <div class="sumbox"><b>{building}/15</b><span>in a capital "building" posture</span></div>
  <div class="sumbox"><b>{neg_margin}/15</b><span>running a multi-yr operating deficit</span></div>
</div>

<div class="note">
<h4>Executive summary</h4>
<p>Across the FY2020–FY2025 window, the dominant story is a <b>General Fund operating squeeze</b>:
the expiration of one-time federal ESSER aid colliding with declining enrollment and rising
personnel/plant costs. {neg_margin} of 15 districts now run a multi-year operating deficit, and several
have drawn reserves down sharply from their FY2022–FY2023 ESSER-era peaks. Yet
<b>{building} of 15 are simultaneously in a capital "building" posture</b> — funded through Iowa's
<b>restricted</b> SAVE (statewide-penny) and GO/PPEL streams, which are walled off from the
General Fund. The framework's central discipline — scoring operating <b>health</b> and reporting
<b>quality</b> separately from the <b>strategic/capital</b> posture — is what keeps these from being
conflated.</p>
<ul>
<li><b>Healthiest:</b> Pleasant Valley and Waukee — genuine enrollment growth, reserves rising even
through heavy construction, clean audits with continuous GFOA recognition.</li>
<li><b>Most distressed, two different ways:</b> <b>Waterloo</b> — operating collapse (FY2025 solvency
<b>−5.6%</b>, negative GF balance) while issuing $87M of new SAVE debt; and <b>Iowa City</b> — a
<b>reporting</b> collapse (FY2023 audit 26 months late with two material weaknesses, FY2024/FY2025
unfiled, Moody's rating withdrawn). One fails on Health, the other on Operational Quality.</li>
<li><b>The reserve cliff is broad:</b> Burlington, Johnston, College/Prairie, West Des Moines and Des
Moines all show steep post-ESSER reserve drawdowns despite clean audits.</li>
</ul>
</div>

<h2>Health × Quality map</h2>
<p class="sub">Horizontal = financial health · vertical = operational/reporting quality · bubble size = enrollment · color = composite score.</p>
<div class="layout">
  <div>{quadrant()}</div>
  <div class="note" style="border-left-color:#16a34a">
  <h4>How to read the map</h4>
  <p>Top-right is the goal: financially strong <i>and</i> trustworthy reporting. Bubbles low on the
  vertical axis (Iowa City) have a reporting/controls problem regardless of the balance-sheet numbers;
  bubbles far left (Waterloo) have an operating-solvency problem regardless of how clean the audit is.
  A district can be a confident "builder" from either position — which is why building posture is a
  <b>label</b>, reported beside the scores rather than baked into them.</p>
  </div>
</div>

<h2>Master benchmark table</h2>
<div class="legend">Score scale (1–5): <span>weak</span><div class="scale"></div><span>strong</span> &nbsp;·&nbsp; click any column header to sort.</div>
<table id="bt"><thead><tr>
<th>#</th><th>District</th><th>Size</th><th>Enroll.</th><th>Enr. trend</th><th>Strategic posture</th>
<th>Solvency (last)</th><th>Op. margin (3yr)</th>
<th>Health</th><th>Quality</th><th>Cap. sustain.</th><th>Composite</th><th>Flags</th>
</tr></thead><tbody>
{''.join(rows_html)}
</tbody></table>

<h2>District scorecards</h2>
<div class="cards">{''.join(cards_html)}</div>

<h2>Methodology &amp; confidence</h2>
<div class="note">
<h4>How the scores were built</h4>
<ul>
<li><b>Source:</b> each district's audited ACFRs (FY2020–FY2025) were text-extracted and parsed
field-by-field with a never-invent / blank-and-flag rule. Iowa City has only FY2020–FY2023 (FY2024/FY2025
were never filed); it is scored on available data and carries a stale-data / missing-recent-year penalty.</li>
<li><b>Pillars (1–5):</b> <b>Health</b> = solvency level + 3-yr operating margin + reserve trend;
<b>Operational Quality</b> = audit opinion, material weaknesses / significant deficiencies / repeat
findings, timeliness &amp; data currency, GFOA/ASBO recognition; <b>Capital-sustainability</b> = can the
building program be afforded (health × enrollment trajectory × margin). <b>Composite = 0.40·Health +
0.35·Quality + 0.25·Capital-sustainability.</b> Strategic posture is a label, not scored good/bad.</li>
<li><b>Benchmark bands</b> follow ISFIS/IASB Iowa norms (solvency 5–15% target). All 15 are treated as
one peer set ("Iowa's large districts"); size and enrollment trajectory are reported as context.</li>
</ul>
<h4>Known limitations</h4>
<ul>
<li><b>Personnel-cost ratio (framework metric A8) is largely unavailable</b> — no district breaks
salaries/benefits out by object in the General Fund statements; MD&amp;A narratives cite "~80%". Only a
few districts (Ankeny, Cedar Rapids, Dubuque est.) could be populated. Reliable cross-district staffing
ratios require the state CAR / DOM data, not the audits.</li>
<li><b>Unspent Authorized Budget (UAB) — Iowa's #1 health indicator — is not in the audits.</b> Spending
authority lives in the DOM Unspent Authorized Budget report and SBRC actions (e.g., Cedar Rapids' reported
~$18M at-risk reduction did not appear in its ACFRs). Solvency is used here as the audit-available proxy.</li>
<li>Solvency numerator = Unassigned + Assigned GF balance; "Committed" balances are excluded uniformly.
Net pension (IPERS) swings are actuarial, not cash, and are read in context.</li>
</ul>
</div>

<footer>
Generated from <code>scripts/build_analysis.py</code> + <code>scripts/build_report.py</code>.
Data: <code>data/iowa-district-financials.csv</code> (88 district-years),
<code>data/iowa-district-scorecards.csv</code>. Methodology:
<code>iowa-district-financial-analysis-framework.md</code>. Every figure traces to an audited ACFR;
unaudited substitutes (CAR/DOM) would be needed to fill the gaps noted above.
</footer>
</div>
<script>
document.querySelectorAll('#bt th').forEach((th,idx)=>{{
 th.addEventListener('click',()=>{{
  const tb=th.closest('table').querySelector('tbody');
  const rows=[...tb.rows];
  const asc=th._asc=!th._asc;
  const num=s=>{{const m=s.replace('%','').replace('+','').match(/-?\\d+\\.?\\d*/);return m?parseFloat(m[0]):NaN}};
  rows.sort((a,b)=>{{
   let x=a.cells[idx].innerText.trim(),y=b.cells[idx].innerText.trim();
   let nx=num(x),ny=num(y);
   if(!isNaN(nx)&&!isNaN(ny))return asc?nx-ny:ny-nx;
   return asc?x.localeCompare(y):y.localeCompare(x);
  }});
  rows.forEach(r=>tb.appendChild(r));
 }});
}});
</script>
</body></html>"""

open("iowa-district-financial-benchmark.html", "w").write(DOC)
print("Wrote iowa-district-financial-benchmark.html (%d KB)" % (len(DOC)//1024))
