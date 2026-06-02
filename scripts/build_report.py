#!/usr/bin/env python3
"""Generate iowa-district-financial-benchmark.html from /tmp/audit/cards.json (UAB-anchored v2)."""
import json, html, datetime

cards = json.load(open("/tmp/audit/cards.json"))

def color(v, lo=1, hi=5):
    if v is None: return "#cbd5e1"
    t = max(0, min(1, (v-lo)/(hi-lo)))
    r = int(220 - t*(220-22)); g = int(38 + t*(163-38)); b = int(38 + t*(74-38))
    return f"rgb({r},{g},{b})"

def badge(v):
    return (f'<span class="badge" style="background:{color(v)}">{v:.1f}</span>'
            if v is not None else '<span class="badge na">n/a</span>')

def spark(series, kind_zero=True):
    pts = [(i, v) for i, v in enumerate(series) if v is not None]
    if len(pts) < 2: return ""
    vals = [v for _, v in pts]
    lo, hi = min(vals + ([0] if kind_zero else [])), max(vals + ([0] if kind_zero else []))
    rng = (hi-lo) or 1
    W, H, pad = 150, 38, 3
    X = lambda i: pad + i*(W-2*pad)/(len(series)-1)
    Y = lambda v: H-pad - (v-lo)*(H-2*pad)/rng
    z = (f'<line x1="{pad}" y1="{Y(0):.1f}" x2="{W-pad}" y2="{Y(0):.1f}" stroke="#e2e8f0"/>'
         if (kind_zero and lo <= 0 <= hi) else "")
    path = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in pts)
    lx, lv = pts[-1]
    dot = f'<circle cx="{X(lx):.1f}" cy="{Y(lv):.1f}" r="2.6" fill="{"#16a34a" if lv>=0 else "#dc2626"}"/>'
    return f'<svg viewBox="0 0 {W} {H}" class="spark" preserveAspectRatio="xMidYMid meet">{z}<polyline points="{path}" fill="none" stroke="#475569" stroke-width="1.5"/>{dot}</svg>'

def quadrant():
    W, H, m = 560, 420, 48
    X = lambda v: m + (v-1)/4*(W-2*m)
    Y = lambda v: H-m - (v-1)/4*(H-2*m)
    p = [f'<svg viewBox="0 0 {W} {H}" class="quad">',
         f'<rect x="{m}" y="{m}" width="{W-2*m}" height="{H-2*m}" fill="#fafafa" stroke="#e2e8f0"/>',
         f'<line x1="{X(3)}" y1="{m}" x2="{X(3)}" y2="{H-m}" stroke="#e2e8f0" stroke-dasharray="4"/>',
         f'<line x1="{m}" y1="{Y(3)}" x2="{W-m}" y2="{Y(3)}" stroke="#e2e8f0" stroke-dasharray="4"/>']
    for v in (1,2,3,4,5):
        p.append(f'<text x="{X(v)}" y="{H-m+16}" class="ax">{v}</text>')
        p.append(f'<text x="{m-12}" y="{Y(v)+3}" class="ax" text-anchor="end">{v}</text>')
    p.append(f'<text x="{W/2}" y="{H-12}" class="axt">Financial Health (UAB-anchored) →</text>')
    p.append(f'<text x="16" y="{H/2}" class="axt" transform="rotate(-90 16 {H/2})">Operational Quality →</text>')
    p.append(f'<text x="{X(4.4)}" y="{Y(4.75)}" class="qn">strong + trustworthy</text>')
    p.append(f'<text x="{X(1.1)}" y="{Y(1.2)}" class="qn">distressed</text>')
    emax = max(c["enrollment"] or 4000 for c in cards)
    for c in cards:
        e = c["enrollment"] or 4000; r = 7 + (e/emax)*20
        cx, cy = X(c["health"]), Y(c["quality"]); fill = color(c["composite"])
        short = c["district"].replace(" CSD","").replace(" (Prairie)","").replace(" Independent","")
        p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" fill-opacity="0.55" stroke="{fill}" stroke-width="1.5"><title>{html.escape(c["district"])}: Health {c["health"]}, Quality {c["quality"]}, composite {c["composite"]}</title></circle>')
        p.append(f'<text x="{cx:.1f}" y="{cy-r-3:.1f}" class="lbl">{html.escape(short)}</text>')
    p.append('</svg>')
    return "".join(p)

rows = []
for i, c in enumerate(cards, 1):
    flags = "".join(f'<span class="flag">{html.escape(x)}</span>' for x in c["flags"]) or '<span class="ok">— none —</span>'
    cagr = f'{c["enr_cagr"]:+.1f}%/yr' if c["enr_cagr"] is not None else "n/a"
    uab = f'{c["uab_last"]:.1f}%' if c["uab_last"] is not None else "—"
    rows.append(f"""<tr>
<td class="rk">{i}</td><td class="dist">{html.escape(c['district'])}</td>
<td>{c['size']}</td><td class="w-{c['wealth']}">{c['wealth']}</td>
<td class="{ 'pos' if (c['enr_cagr'] or 0)>0 else 'neg' if (c['enr_cagr'] or 0)<0 else ''}">{cagr}</td>
<td class="lab">{html.escape(c['label'])}</td>
<td class="{ 'neg' if (c['uab_last'] or 0)<5 else '' }"><b>{uab}</b></td>
<td>{c['solv_last']:.1f}%</td>
<td>{badge(c['health'])}</td><td>{badge(c['quality'])}</td><td>{badge(c['cap_sust'])}</td>
<td>{badge(c['composite'])}</td><td class="flags">{flags}</td></tr>""")

cardhtml = []
for c in cards:
    flags = "".join(f'<span class="flag">{html.escape(x)}</span>' for x in c["flags"]) or '<span class="ok">no auto-flags</span>'
    crl = f'{c["crl_pct"]:.0f}% of cap' if c["crl_pct"] is not None else "—"
    room = f'${c["debt_room_m"]:,}M left' if c["debt_room_m"] is not None else "n/a"
    vpp = f'${c["val_per_pupil"]:,}/pupil' if c["val_per_pupil"] else "—"
    cardhtml.append(f"""<div class="card">
  <div class="ch"><h3>{html.escape(c['district'])}</h3><span class="comp" style="background:{color(c['composite'])}">{c['composite']:.2f}</span></div>
  <div class="meta">{c['size']} · {c['enrollment'] or '—'} students · <b>{html.escape(c['label'])}</b> · {c['wealth']} wealth ({vpp})</div>
  <div class="grid">
    <div><span class="k">Health</span>{badge(c['health'])}</div>
    <div><span class="k">Op. Quality</span>{badge(c['quality'])}</div>
    <div><span class="k">Capital sustain.</span>{badge(c['cap_sust'])}</div>
    <div><span class="k">Recognition</span>{'GFOA/ASBO' if c['cert'] else '—'}</div>
  </div>
  <div class="sparks">
    <div><span class="k">UAB % of max budget (FY20–25)</span>{spark(c['uab_series'])}<b class="{ 'neg' if (c['uab_last'] or 0)<5 else 'pos'}">{(c['uab_last'] or 0):.1f}%</b></div>
    <div><span class="k">Solvency % (audited)</span>{spark(c['solv_series'])}<b>{(c['solv_last'] or 0):.1f}%</b></div>
    <div><span class="k">Operating margin %</span>{spark(c['marg_series'])}<b class="{ 'pos' if c['marg3']>=0 else 'neg'}">{c['marg_series'][-1]:.1f}%</b></div>
  </div>
  <div class="kv"><span>Opinion:</span> {html.escape(c['opinion_last'] or '—')} · <span>Debt:</span> ${c['debt_last']:.0f}M
     · <span>GO-limit room:</span> {room} · <span>Cash-reserve levy:</span> {crl}</div>
  <div class="cardflags">{flags}</div>
</div>""")

building = sum(1 for c in cards if c["label"].startswith("Building"))
neg_margin = sum(1 for c in cards if c["marg3"] < 0)
thin_uab = sum(1 for c in cards if (c["uab_last"] or 0) < 5)
date = datetime.date(2026, 6, 2).strftime("%B %Y")

DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa Large-District Financial Benchmark · FY2020–FY2025</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--bg:#f8fafc}}
*{{box-sizing:border-box}} body{{font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:var(--bg)}}
.wrap{{max-width:1200px;margin:0 auto;padding:34px 22px 80px}}
h1{{font-size:30px;margin:0 0 4px}} h2{{font-size:21px;margin:42px 0 12px;border-bottom:2px solid var(--line);padding-bottom:6px}}
.sub{{color:var(--mut);margin:0 0 8px}} a{{color:#2563eb}}
.cards-summary{{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}}
.sumbox{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 18px;flex:1;min-width:140px}}
.sumbox b{{font-size:26px;display:block}} .sumbox span{{color:var(--mut);font-size:13px}}
table{{width:100%;border-collapse:collapse;background:#fff;font-size:13px;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th,td{{padding:8px 9px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}}
th{{background:#f1f5f9;cursor:pointer;font-size:11.5px;text-transform:uppercase;letter-spacing:.03em;color:#475569}}
th:hover{{background:#e2e8f0}}
td.dist{{font-weight:600;white-space:normal;min-width:140px}} td.rk{{color:var(--mut)}}
.lab{{font-size:12px;color:#334155;white-space:normal;min-width:118px}} .flags{{white-space:normal;min-width:210px}}
.badge{{color:#fff;border-radius:6px;padding:2px 8px;font-weight:700;font-size:12.5px}} .badge.na{{background:#cbd5e1}}
.flag{{display:inline-block;background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;border-radius:5px;padding:1px 6px;margin:1px 2px;font-size:11px}}
.ok{{color:#16a34a;font-size:12px}} .pos{{color:#16a34a}} .neg{{color:#dc2626}}
.w-high{{color:#15803d}} .w-mid{{color:#a16207}} .w-low{{color:#b45309}}
.legend{{display:flex;gap:8px;align-items:center;margin:8px 0 2px;color:var(--mut);font-size:12px}}
.scale{{height:10px;width:160px;border-radius:5px;background:linear-gradient(90deg,rgb(220,38,38),rgb(234,179,8),rgb(22,163,74))}}
.layout{{display:grid;grid-template-columns:1.1fr .9fr;gap:24px;align-items:start}} @media(max-width:900px){{.layout{{grid-template-columns:1fr}}}}
.quad{{width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:10px}}
.quad .ax{{font-size:10px;fill:#94a3b8;text-anchor:middle}} .quad .axt{{font-size:11px;fill:#475569;text-anchor:middle;font-weight:600}}
.quad .lbl{{font-size:9px;fill:#334155;text-anchor:middle}} .quad .qn{{font-size:10px;fill:#cbd5e1;text-anchor:middle;font-style:italic}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(335px,1fr));gap:16px;margin-top:14px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:15px 16px}}
.ch{{display:flex;justify-content:space-between;align-items:center}} .ch h3{{margin:0;font-size:16px}}
.comp{{color:#fff;font-weight:800;border-radius:8px;padding:3px 11px;font-size:15px}}
.meta{{color:var(--mut);font-size:12px;margin:5px 0 11px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;margin-bottom:11px}}
.grid .k,.sparks .k{{display:block;color:var(--mut);font-size:11px;margin-bottom:2px}}
.grid>div{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px dashed var(--line);padding-bottom:4px}}
.sparks{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:10px}}
.sparks>div{{display:flex;flex-direction:column;min-width:0}} .sparks b{{font-size:13px}}
.spark{{width:100%;height:auto;display:block;margin:2px 0}}
.kv{{font-size:11.5px;color:#475569;border-top:1px solid var(--line);padding-top:8px}} .kv span{{color:var(--mut)}}
.cardflags{{margin-top:8px}}
.note{{background:#fff;border:1px solid var(--line);border-left:4px solid #2563eb;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:14px}}
.note h4{{margin:0 0 6px}} .note ul{{margin:6px 0 0 18px;padding:0}} .note li{{margin:3px 0}}
footer{{color:var(--mut);font-size:12px;margin-top:50px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body><div class="wrap">

<h1>Iowa Large-District Financial Benchmark</h1>
<p class="sub">15 of Iowa's largest school districts · audited ACFRs + Iowa DOM state data · FY2020–FY2025 · {date}</p>

<div class="cards-summary">
  <div class="sumbox"><b>15</b><span>districts benchmarked</span></div>
  <div class="sumbox"><b>88+90</b><span>audited + state district-years</span></div>
  <div class="sumbox"><b>{building}/15</b><span>in a capital "building" posture</span></div>
  <div class="sumbox"><b>{neg_margin}/15</b><span>multi-yr operating deficit</span></div>
  <div class="sumbox"><b>{thin_uab}/15</b><span>thin spending authority (UAB&lt;5%)</span></div>
</div>

<div class="note">
<h4>Executive summary</h4>
<p>This edition is <b>anchored on Unspent Authorized Budget (UAB)</b> — Iowa's #1 financial-health
indicator and the binding legal constraint on a district's spending — sourced from the Iowa DOM
report and weighted <b>50%</b> of the Health pillar (audited solvency 30%, operating-margin trend
20%). Because UAB is state-computed, it exists even where audits do not (Iowa City FY24/FY25).</p>
<ul>
<li><b>Cash ≠ spending authority — and it re-ranks the field.</b> Districts that looked stressed on
audited <i>reserves</i> are fine on <i>authority</i>: <b>Burlington</b> (solvency 8% but UAB <b>28%</b>)
and <b>Johnston</b> (solvency 8% but UAB <b>21%</b>) drew down cash while keeping ample authority —
exactly what ISFIS says UAB is for. They rank mid-pack, not at the bottom.</li>
<li><b>The two genuinely distressed districts fail differently.</b> <b>Iowa City</b> — UAB went
<b>negative in FY2023</b> (the unlawful, SBRC-trigger condition), sits at ~2% today, is levying
<b>57% of its cash-reserve cap</b> to stay liquid, and has <b>not filed FY2024/FY2025 audits</b>
(Moody's rating withdrawn). <b>Waterloo</b> — an operating collapse: UAB halved to 7.5%, audited
solvency <b>−5.6%</b>, negative GF balance, while issuing $87M of new SAVE debt.</li>
<li><b>The post-ESSER operating squeeze is broad</b> — {neg_margin} of 15 run a multi-year deficit —
but <b>{building} of 15 keep building</b> through Iowa's restricted SAVE/GO streams. Operating health,
reporting quality, and capital posture are scored separately so these don't get conflated.</li>
<li><b>Healthiest:</b> Pleasant Valley and Waukee — growing enrollment, UAB above 22%/30%, clean
audits, continuous GFOA. Muscatine ranks high on a strong UAB (20%) despite the sharpest enrollment
decline, by restraining spending.</li>
</ul>
</div>

<h2>Health × Quality map</h2>
<p class="sub">Horizontal = UAB-anchored financial health · vertical = operational/reporting quality · bubble = enrollment · color = composite.</p>
<div class="layout"><div>{quadrant()}</div>
<div class="note" style="border-left-color:#16a34a"><h4>Reading the map</h4>
<p>Top-right = strong <i>and</i> trustworthy. Iowa City sits at the bottom (reporting collapse)
regardless of its balance sheet; Waterloo sits far left (operating/authority collapse) regardless of
its clean audit. A district can be a confident "builder" from either position — which is why building
posture is a <b>label</b>, reported beside the scores rather than baked into them.</p></div></div>

<h2>Master benchmark table</h2>
<div class="legend">Score scale (1–5): <span>weak</span><div class="scale"></div><span>strong</span> · click any header to sort · <b>UAB</b> = spending authority (Iowa's #1 metric).</div>
<table id="bt"><thead><tr>
<th>#</th><th>District</th><th>Size</th><th>Wealth</th><th>Enr. trend</th><th>Strategic posture</th>
<th>UAB %</th><th>Solvency %</th><th>Health</th><th>Quality</th><th>Cap. sust.</th><th>Composite</th><th>Flags</th>
</tr></thead><tbody>
{''.join(rows)}
</tbody></table>

<h2>District scorecards</h2>
<div class="cards">{''.join(cardhtml)}</div>

__DEEPDIVE__

<h2>Methodology &amp; confidence</h2>
<div class="note">
<h4>How the scores were built</h4>
<ul>
<li><b>Two data layers:</b> audited ACFRs (FY2020–FY2025, text-extracted field-by-field) +
the Iowa DOM state-data layer (UAB, AEA flow-through, certified enrollment, cash-reserve levy &amp;
20% cap, levy rates, valuation, at-risk). State data is <b>unaudited</b> but exists where audits do
not — so Iowa City carries FY24/FY25 UAB and a stale/missing-audit Quality penalty.</li>
<li><b>Pillar A — Health = 0.50·UAB + 0.30·Solvency + 0.20·Operating-margin trend.</b> UAB% (of max
authorized budget) is the primary input; <b>negative UAB</b> is a hard flag. Solvency is recomputed
uniformly using the DOM AEA flow-through denominator (the ISFIS formula). <b>Pillar C — Quality</b>:
opinion, material weaknesses / significant deficiencies / repeat findings, timeliness &amp; data
currency, GFOA/ASBO. <b>Capital-sustainability</b>: health × enrollment trajectory × margin × GO-debt
headroom (vs. the 5%-of-actual-value limit). <b>Composite = 0.40·Health + 0.35·Quality +
0.25·Capital-sustainability.</b> Strategic posture is a label, not scored.</li>
<li><b>Context layers:</b> property-wealth tertiles (taxable valuation/pupil), GO-debt headroom, and
cash-reserve-levy reliance (who taxes to stay liquid). All 15 are one peer set; Iowa benchmark bands
(ISFIS/IASB) anchor the scales.</li>
</ul>
<h4>Notes &amp; limits</h4>
<ul>
<li><b>Enrollment</b> uses the DOM funding/budget figure (uniform, complete; ~1–3% from audit
"certified enrollment" due to the one-year funding lag).</li>
<li><b>Personnel-cost ratio (A8)</b> remains audit-limited (most districts don't break salaries out by
object in the GF statements; MD&amp;A cites ~80%).</li>
<li>Solvency numerator = Unassigned + Assigned GF balance ("Committed" excluded uniformly). IPERS
pension swings are actuarial, not cash. Cash-reserve-levy "reliance" is context, not a demerit — for
a growth district (Waukee) it funds expansion; for Iowa City it signals taxing to stay liquid.</li>
</ul>
</div>

<footer>Generated from <code>scripts/extract_dom.py</code> → <code>scripts/build_analysis.py</code> →
<code>scripts/build_report.py</code>. Data: <code>data/iowa-district-financials.csv</code> (audited),
<code>data/dom/</code> (state), <code>data/iowa-district-scorecards.csv</code> (scores). Method:
<code>iowa-district-financial-analysis-framework.md</code>.</footer>
</div>
<script>
document.querySelectorAll('#bt th').forEach((th,idx)=>{{th.addEventListener('click',()=>{{
 const tb=th.closest('table').querySelector('tbody'); const rows=[...tb.rows]; const asc=th._asc=!th._asc;
 const num=s=>{{const m=s.replace('%','').replace('+','').match(/-?\\d+\\.?\\d*/);return m?parseFloat(m[0]):NaN}};
 rows.sort((a,b)=>{{let x=a.cells[idx].innerText.trim(),y=b.cells[idx].innerText.trim();let nx=num(x),ny=num(y);
  if(!isNaN(nx)&&!isNaN(ny))return asc?nx-ny:ny-nx; return asc?x.localeCompare(y):y.localeCompare(x);}});
 rows.forEach(r=>tb.appendChild(r));}});}});
</script></body></html>"""
# ---------- deep-dive section (dropdown -> per-district charts + narrative) ----------
order = [c["district"] for c in cards]
deep_data = {}
for i, c in enumerate(cards, 1):
    deep_data[c["district"]] = dict(
        rank=i, n=len(cards), composite=c["composite"], health=c["health"],
        quality=c["quality"], cap_sust=c["cap_sust"], uab_last=c["uab_last"],
        solv_last=c["solv_last"], marg3=c["marg3"], label=c["label"],
        size=c["size"].replace("&gt;", ">").replace("&lt;", "<"), wealth=c["wealth"],
        enrollment=c["enrollment"], vpp=c["val_per_pupil"], debt_last=c["debt_last"],
        debt_room=c["debt_room_m"], crl_pct=c["crl_pct"], atrisk=c["atrisk"],
        cert=c["cert"], flags=c["flags"], narrative=c["narrative"], series=c["deep"])
options = "".join(f'<option value="{html.escape(d)}">{html.escape(d)}</option>' for d in order)

DEEP_SECTION = r"""
<style>
.ddwrap{margin:6px 0 4px} #dd{font-size:15px;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;background:#fff;min-width:300px}
#deep{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px 22px;margin-top:12px}
.dhead{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.dhead h3{margin:0;font-size:21px} .dhead .rank{font-size:13px;color:#64748b;font-weight:500}
.dmeta{color:#64748b;font-size:13.5px;margin-top:4px}
.dcomp{color:#fff;font-weight:800;border-radius:10px;padding:6px 14px;font-size:20px}
.dscores{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
.dchip{background:#f8fafc;border:1px solid #e2e8f0;border-radius:9px;padding:8px 12px;display:flex;flex-direction:column;gap:4px;min-width:130px}
.dchip .cl{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.03em}
.dchip .badge{align-self:flex-start;color:#fff;border-radius:6px;padding:2px 9px;font-weight:700;font-size:14px}
.dchip .csub{font-size:11px;color:#475569}
.dctx{font-size:13px;color:#475569;margin:4px 0 10px} .dctx span{color:#94a3b8}
.dflags{margin:8px 0} .dnarr{font-size:14.5px;line-height:1.6;background:#f8fafc;border-left:3px solid #2563eb;border-radius:6px;padding:12px 15px;margin:10px 0 18px}
.dcharts{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.dcard{border:1px solid #e2e8f0;border-radius:9px;padding:6px 8px 2px}
.dchart{width:100%;height:auto;display:block}
.dchart .ct{font-size:11px;fill:#334155;font-weight:600} .dchart .yt{font-size:9px;fill:#94a3b8;text-anchor:end}
.dchart .xt{font-size:9px;fill:#94a3b8;text-anchor:middle} .dchart .zl{stroke:#cbd5e1;stroke-width:1}
.dchart .gl{stroke:#f1f5f9;stroke-width:1} .dchart .lg{font-size:9px}
.nochart{font-size:11px;color:#94a3b8;padding:20px 6px}
</style>

<h2>Analyze one district</h2>
<p class="sub">Pick a district — every chart, score, and the narrative below update to that district.</p>
<div class="ddwrap"><select id="dd">__OPTIONS__</select></div>
<div id="deep"></div>

<script>
const DEEP = __DEEP_JSON__;
const ORDER = __ORDER__;
const CHARTS = [
 {t:"UAB % of max budget",k:["uab_pct"],c:["#2563eb"],f:"pct",z:true},
 {t:"Spending authority $: UAB vs max",k:["uab_dollar","max_budget"],c:["#2563eb","#94a3b8"],lab:["UAB","Max"],f:"m"},
 {t:"Solvency % (audited)",k:["solvency"],c:["#0891b2"],f:"pct",z:true},
 {t:"Operating margin %",k:["op_margin"],c:["#7c3aed"],f:"pct",z:true},
 {t:"GF revenue vs expenditure",k:["gf_rev","gf_exp"],c:["#16a34a","#dc2626"],lab:["Rev","Exp"],f:"m"},
 {t:"GF fund balance: unassigned vs total",k:["gf_unassigned","gf_total_fb"],c:["#2563eb","#94a3b8"],lab:["Unassigned","Total"],f:"m",z:true},
 {t:"Certified enrollment",k:["enrollment"],c:["#0d9488"],f:"n"},
 {t:"Debt outstanding: GO vs SAVE",k:["go_debt","save_debt"],c:["#b45309","#0891b2"],lab:["GO","SAVE"],f:"m"},
 {t:"Capital additions vs depreciation",k:["capital_add","depreciation"],c:["#16a34a","#94a3b8"],lab:["Additions","Deprec."],f:"m"},
 {t:"Construction in progress",k:["cip"],c:["#a16207"],f:"m"},
 {t:"IPERS pension vs OPEB liability",k:["ipers","opeb"],c:["#7c3aed","#94a3b8"],lab:["IPERS","OPEB"],f:"m"},
 {t:"Unrestricted net position",k:["unrestricted_np"],c:["#0891b2"],f:"m",z:true},
 {t:"Cash & investments",k:["cash"],c:["#0d9488"],f:"m"},
 {t:"Cash-reserve levy $",k:["crl"],c:["#b45309"],f:"m"},
 {t:"Cash-reserve levy % of 20% cap",k:["crl_pct"],c:["#b45309"],f:"pct"},
 {t:"Taxable valuation",k:["taxable_val"],c:["#15803d"],f:"b"},
 {t:"Total levy rate ($/$1,000)",k:["levy_rate"],c:["#7c3aed"],f:"r"},
 {t:"At-risk dollars generated",k:["atrisk"],c:["#dc2626"],f:"k"},
];
function col(v){if(v==null)return"#cbd5e1";let t=Math.max(0,Math.min(1,(v-1)/4));
 let r=Math.round(220-t*198),g=Math.round(38+t*125),b=Math.round(38+t*36);return`rgb(${r},${g},${b})`;}
function fmt(v,f){if(v==null)return"—";
 if(f=="pct")return v.toFixed(1)+"%"; if(f=="m")return"$"+(v/1e6).toFixed(Math.abs(v)>=1e8?0:1)+"M";
 if(f=="b")return"$"+(v/1e9).toFixed(2)+"B"; if(f=="k")return"$"+(v/1e3).toFixed(0)+"K";
 if(f=="n")return Math.round(v).toLocaleString(); if(f=="r")return v.toFixed(2); return v;}
function chart(def,S){
 const years=S.years,W=360,H=200,L=46,R=12,T=24,B=22;
 let vals=[]; def.k.forEach(k=>(S[k]||[]).forEach(v=>{if(v!=null)vals.push(v)}));
 if(def.z)vals.push(0);
 if(!vals.length)return'<div class="nochart">'+def.t+': no data</div>';
 let lo=Math.min(...vals),hi=Math.max(...vals); if(lo===hi)hi=lo+Math.abs(lo||1)*0.1+1;
 let pad=(hi-lo)*0.10; lo-=pad; hi+=pad; if(def.z&&lo>0)lo=0; if(def.z&&hi<0)hi=0;
 const X=i=>L+i*(W-L-R)/(years.length-1), Y=v=>H-B-(v-lo)*(H-T-B)/(hi-lo);
 let s=`<svg viewBox="0 0 ${W} ${H}" class="dchart"><text x="${L}" y="13" class="ct">${def.t}</text>`;
 [lo,(lo+hi)/2,hi].forEach(t=>{s+=`<line x1="${L}" y1="${Y(t).toFixed(1)}" x2="${W-R}" y2="${Y(t).toFixed(1)}" class="gl"/><text x="${L-5}" y="${(Y(t)+3).toFixed(1)}" class="yt">${fmt(t,def.f)}</text>`;});
 if(def.z&&lo<=0&&hi>=0)s+=`<line x1="${L}" y1="${Y(0).toFixed(1)}" x2="${W-R}" y2="${Y(0).toFixed(1)}" class="zl"/>`;
 years.forEach((yr,i)=>s+=`<text x="${X(i).toFixed(1)}" y="${H-7}" class="xt">'${String(yr).slice(2)}</text>`);
 def.k.forEach((k,ki)=>{const a=S[k]||[],p=[];a.forEach((v,i)=>{if(v!=null)p.push([i,v])});if(!p.length)return;
  if(p.length>1)s+=`<polyline points="${p.map(q=>X(q[0]).toFixed(1)+','+Y(q[1]).toFixed(1)).join(' ')}" fill="none" stroke="${def.c[ki]}" stroke-width="2"/>`;
  const lp=p[p.length-1];s+=`<circle cx="${X(lp[0]).toFixed(1)}" cy="${Y(lp[1]).toFixed(1)}" r="3" fill="${def.c[ki]}"/>`;});
 if(def.lab){let lx=L+2;def.lab.forEach((nm,ki)=>{s+=`<rect x="${lx}" y="17" width="8" height="8" fill="${def.c[ki]}" rx="1"/><text x="${lx+11}" y="24" class="lg" fill="#475569">${nm}</text>`;lx+=12+nm.length*5.5+12;});}
 return s+'</svg>';}
function chip(label,v,sub){return`<div class="dchip"><span class="cl">${label}</span><span class="badge" style="background:${col(v)}">${v.toFixed(1)}</span>${sub?'<span class="csub">'+sub+'</span>':''}</div>`;}
function renderDeep(name){
 const d=DEEP[name];let h="";
 h+=`<div class="dhead"><div><h3>${name} <span class="rank">#${d.rank} of ${d.n}</span></h3>
   <div class="dmeta">${d.size} · ${d.enrollment?d.enrollment.toLocaleString():"—"} students · ${d.wealth} wealth${d.vpp?" ($"+d.vpp.toLocaleString()+"/pupil)":""} · <b>${d.label}</b></div></div>
   <span class="dcomp" style="background:${col(d.composite)}">${d.composite.toFixed(2)}</span></div>`;
 h+=`<div class="dscores">
   ${chip("Health",d.health,"UAB "+fmt(d.uab_last,"pct")+" · Solv "+fmt(d.solv_last,"pct")+" · Margin "+fmt(d.marg3,"pct"))}
   ${chip("Operational Quality",d.quality,d.cert?"GFOA/ASBO":"")}
   ${chip("Capital sustainability",d.cap_sust,"")}
   ${chip("Composite",d.composite,"")}</div>`;
 h+=`<div class="dctx"><span>Debt outstanding:</span> $${d.debt_last.toFixed(0)}M &nbsp;·&nbsp; <span>GO-limit room:</span> ${d.debt_room!=null?"$"+d.debt_room.toLocaleString()+"M":"n/a"} &nbsp;·&nbsp; <span>Cash-reserve levy:</span> ${d.crl_pct!=null?d.crl_pct.toFixed(0)+"% of cap":"—"} &nbsp;·&nbsp; <span>At-risk $:</span> ${d.atrisk!=null?"$"+(d.atrisk/1e3).toFixed(0)+"K":"—"}</div>`;
 h+=`<div class="dflags">${d.flags.map(x=>'<span class="flag">'+x+'</span>').join("")||'<span class="ok">no auto-flags</span>'}</div>`;
 h+=`<p class="dnarr">${d.narrative}</p>`;
 h+=`<div class="dcharts">${CHARTS.map(def=>'<div class="dcard">'+chart(def,d.series)+'</div>').join("")}</div>`;
 document.getElementById("deep").innerHTML=h;}
document.getElementById("dd").addEventListener("change",e=>renderDeep(e.target.value));
renderDeep(ORDER[0]);
</script>
"""
DEEP_SECTION = (DEEP_SECTION
                .replace("__DEEP_JSON__", json.dumps(deep_data))
                .replace("__ORDER__", json.dumps(order))
                .replace("__OPTIONS__", options))
DOC = DOC.replace("__DEEPDIVE__", DEEP_SECTION)

open("iowa-district-financial-benchmark.html", "w").write(DOC)
print("Wrote iowa-district-financial-benchmark.html (%d KB)" % (len(DOC)//1024))
