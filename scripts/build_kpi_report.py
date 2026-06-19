#!/usr/bin/env python3
"""
Render kpi-three-methodologies.html — the comprehensive, grouped, three-methodology KPI
benchmark for ICCSD vs. peer districts, FY2015-FY2025.

Self-contained (inline CSS + JS + embedded JSON), matching the repo's house style. Reads
data/kpi-three-methodologies.csv and scripts/kpi_catalog.py. The page has:
  * a methodology overview (Internal 10-point test / Moody's K-12 scorecard / S&P US Governments)
  * one section per logical KPI group; each KPI is a card with its methodology badge, formula,
    target band, an ICCSD FY15-25 trend, and an interactive district x fiscal-year heatmap
  * a "qualitative / external — not scored" panel naming the factors that can't come from audits
  * a methodology appendix and data-currency / gap notes

-> kpi-three-methodologies.html
"""
import csv, os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpi_catalog as K
from _nav import nav

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)

ICCSD = "Iowa City CSD"
ORDER = ["Iowa City CSD","Ankeny CSD","Cedar Rapids CSD","Davenport CSD","Des Moines Independent CSD",
 "Dubuque CSD","Johnston CSD","Linn-Mar CSD","Pleasant Valley CSD","Waterloo CSD","Waukee CSD",
 "West Des Moines CSD","College CSD (Prairie)","Muscatine CSD","Burlington CSD"]
SHORT = {d: d.replace(" CSD","").replace(" (Prairie)","") for d in ORDER}
YEARS = list(range(2015, 2026))

def load():
    rows = list(csv.DictReader(open(p("data/kpi-three-methodologies.csv"))))
    data = {}
    for r in rows:
        data[(r["district"], int(r["fiscal_year"]))] = r
    return rows, data

BADGE = {"Internal":"#7c3aed","Moody's":"#c2410c","S&P":"#0369a1","Shared":"#0f766e","Context":"#64748b"}

def fmt(val, unit):
    if val in (None, ""): return ""
    try: x = float(val)
    except ValueError: return str(val)
    if unit in ("pct","ratio_pct"): return f"{x:g}%"
    if unit == "days": return f"{x:g}"
    if unit == "usd_pp": return f"${x:,.0f}"
    if unit == "x": return f"{x:g}"
    if unit == "months": return f"{x:g}"
    if unit == "number": return f"{x:g}"
    return f"{x:g}"

def build():
    rows, data = load()
    # embed compact dataset: {kpi: {district: {year: value}}}
    kpi_keys = [k["key"] for k in K.KPIS]
    series = {k: {SHORT[d]: {} for d in ORDER} for k in kpi_keys}
    basis = {SHORT[d]: {} for d in ORDER}
    for (d, fy), r in data.items():
        if d not in SHORT: continue
        basis[SHORT[d]][fy] = r.get("data_basis","")
        for k in kpi_keys:
            v = r.get(k, "")
            if v not in (None, ""):
                try: series[k][SHORT[d]][fy] = float(v)
                except ValueError: series[k][SHORT[d]][fy] = v
    catalog = []
    for grp_key, grp_label, grp_desc in K.GROUPS:
        items = [k for k in K.KPIS if k["group"] == grp_key]
        catalog.append(dict(key=grp_key, label=grp_label, desc=grp_desc, kpis=[
            {kk: kpi.get(kk,"") for kk in ("key","label","source","unit","good","target","formula","note")}
            for kpi in items]))

    payload = dict(series=series, basis=basis, catalog=catalog,
                   districts=[SHORT[d] for d in ORDER], years=YEARS, iccsd=SHORT[ICCSD],
                   badge=BADGE)

    # ---- methodology overview cards ----
    meth_cards = """
<div class="mcards">
  <div class="mc"><div class="mt" style="color:#7c3aed">① ICCSD Internal</div>
    <div class="md">The district's own <b>Ten-Point Financial Condition Test</b> (Annual Financial Health
    Report). Iowa-specific ratios drawn mostly from the Certified Annual Report — solvency, day's cash,
    employee-cost, unspent-balance, and more. Benchmarks are the district's published targets.</div></div>
  <div class="mc"><div class="mt" style="color:#c2410c">② Moody's</div>
    <div class="md">Moody's <b>US K-12 Public School Districts</b> scorecard (Jul 2024): Economy 30%,
    Financial Performance 30%, Institutional Framework 10%, Leverage 30%. We compute the audit-derivable
    sub-factors (available fund balance, net cash, long-term liabilities, fixed costs, enrollment trend).</div></div>
  <div class="mc"><div class="mt" style="color:#0369a1">③ S&amp;P</div>
    <div class="md">S&amp;P <b>Methodology for Rating US Governments</b> (Sep 2024): five equally-weighted
    factors. We compute the financial ones — 3-yr operating result, available reserves, debt current-cost,
    and per-pupil debt/pension proxies.</div></div>
</div>"""

    # ---- per-group sections (ICCSD trend tables rendered server-side; heatmap via JS) ----
    sections = []
    for grp_key, grp_label, grp_desc in K.GROUPS:
        items = [k for k in K.KPIS if k["group"] == grp_key]
        cards = []
        for kpi in items:
            key = kpi["key"]; src = kpi["source"]
            iccsd_cells = "".join(
                f'<td>{fmt(series[key][SHORT[ICCSD]].get(y,""), kpi["unit"])}</td>' for y in YEARS)
            note = f'<div class="note">⚠ {kpi["note"]}</div>' if kpi.get("note") else ""
            cards.append(f"""
  <div class="kcard" id="kc-{key}">
    <div class="kch"><h4>{kpi['label']}</h4>
      <span class="badge" style="background:{BADGE[src]}">{src}</span>
      <span class="dir">{'↑ better' if kpi['good']=='up' else '↓ better' if kpi['good']=='down' else '◦ context'}</span>
    </div>
    <div class="frm"><b>Formula:</b> {kpi['formula']}</div>
    <div class="tgt"><b>Benchmark:</b> {kpi['target']}</div>{note}
    <div class="trend"><span class="tl">ICCSD FY15–25</span>
      <table class="mini"><tr class="yh"><th></th>{''.join(f'<th>{str(y)[2:]}</th>' for y in YEARS)}</tr>
      <tr><th>ICCSD</th>{iccsd_cells}</tr></table>
    </div>
    <button class="hbtn" data-kpi="{key}">Show all 15 districts ▸</button>
    <div class="heat" id="heat-{key}"></div>
  </div>""")
        sections.append(f"""
<section class="grp" id="grp-{grp_key}">
  <h2>{grp_label}</h2><p class="gd">{grp_desc}</p>
  {''.join(cards)}
</section>""")

    # ---- qualitative / external factors ----
    qrows = "".join(
        f'<tr><td><span class="badge" style="background:{BADGE.get(q["methodology"],"#64748b")}">{q["methodology"]}</span></td>'
        f'<td><b>{q["factor"]}</b></td><td>{q["weight"]}</td><td>{q["reason"]}</td></tr>'
        for q in K.QUALITATIVE)

    nav_html = nav("more")
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ICCSD — Three-Methodology KPI Benchmark (FY2015–FY2025)</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}}
body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:1040px;margin:0 auto;padding:30px 20px 70px}}
h1{{font-size:29px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px}}
.intro{{background:#fff;border:1px solid var(--line);border-left:4px solid #2563eb;border-radius:10px;padding:16px 20px;margin-bottom:16px}}
.intro p{{margin:7px 0}}
.mcards{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:14px 0 8px}}
@media(max-width:760px){{.mcards{{grid-template-columns:1fr}}}}
.mc{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.mt{{font-weight:800;font-size:15px;margin-bottom:5px}} .md{{font-size:13.5px;color:#334155}}
.toc{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 18px;margin:8px 0 22px;font-size:14px}}
.toc a{{color:#2563eb;text-decoration:none;margin-right:14px;white-space:nowrap;display:inline-block;padding:3px 0}}
.grp{{margin:30px 0}} .grp h2{{font-size:22px;margin:0 0 4px;border-bottom:2px solid #cbd5e1;padding-bottom:6px}}
.gd{{color:var(--mut);margin:4px 0 14px;font-size:14.5px}}
.kcard{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:14px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.kch{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:8px}}
.kch h4{{margin:0;font-size:18px;flex:0 1 auto}}
.badge{{color:#fff;font-size:11px;font-weight:700;padding:2px 9px;border-radius:999px;letter-spacing:.02em}}
.dir{{margin-left:auto;font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}}
.frm,.tgt{{font-size:13.5px;color:#334155;margin:3px 0}} .frm b,.tgt b{{color:#0f172a}}
.note{{font-size:12.5px;color:#b45309;background:#fffbeb;border:1px solid #fde68a;border-radius:7px;padding:5px 9px;margin:6px 0}}
.trend{{margin:10px 0 6px}} .tl{{font-size:12px;color:var(--mut);font-weight:600}}
table.mini{{border-collapse:collapse;width:100%;margin-top:4px;font-size:12.5px}}
table.mini th,table.mini td{{border:1px solid #eef2f7;padding:3px 5px;text-align:center}}
table.mini .yh th{{color:var(--mut);font-weight:600;background:#f8fafc}}
table.mini td{{font-variant-numeric:tabular-nums}}
.hbtn{{margin-top:8px;font:600 12.5px inherit;color:#2563eb;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:5px 11px;cursor:pointer}}
.hbtn:hover{{background:#dbeafe}}
.heat{{overflow-x:auto;margin-top:10px}}
table.hm{{border-collapse:collapse;font-size:12px;width:100%}}
table.hm th,table.hm td{{border:1px solid #e9eef5;padding:3px 6px;text-align:center;font-variant-numeric:tabular-nums;white-space:nowrap}}
table.hm th{{background:#f8fafc;color:#475569;font-weight:600}}
table.hm td.d{{text-align:left;font-weight:600;position:sticky;left:0;background:#fff}}
table.hm tr.me td{{background:#eff6ff}} table.hm tr.me td.d{{color:#1d4ed8;background:#eff6ff}}
table.hm td.proj{{font-style:italic;opacity:.85}}
.qual{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin:18px 0}}
.qual table{{border-collapse:collapse;width:100%;font-size:13.5px;margin-top:8px}}
.qual td{{border-top:1px solid var(--line);padding:7px 8px;vertical-align:top}}
.appx{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 20px;margin:18px 0;font-size:14px}}
.appx li{{margin:5px 0}}
footer{{color:var(--mut);font-size:12.5px;margin-top:34px;border-top:1px solid var(--line);padding-top:14px}}
.lg{{font-size:12.5px;color:var(--mut);margin:8px 0}}
.sw{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:middle;margin:0 3px 0 10px}}
</style></head><body>{nav_html}<div class="wrap">

<h1>ICCSD Financial KPIs — Three Methodologies, FY2015–FY2025</h1>
<p class="sub">Iowa City CSD and 14 benchmarked peer districts, scored under the district's own internal
ratios, Moody's, and S&amp;P — grouped by financial area · every figure from audited ACFRs or official
Iowa state filings (FY2024–25 ICCSD from management reporting)</p>

<div class="intro">
<p>This page calculates the district's financial KPIs three ways and lays them side by side: <b>(1)</b> ICCSD's
own internal definitions, <b>(2)</b> Moody's US K-12 school-district rating scorecard, and <b>(3)</b> S&amp;P's
US-government rating methodology. KPIs are grouped into seven financial areas. Where a rating-agency factor
relies on data that does not exist in audited financials (county income, population), it is named in the
<a href="#qual">qualitative panel</a> rather than guessed.</p>
</div>
{meth_cards}

<div class="toc"><b>Jump to:</b> """ + " ".join(
        f'<a href="#grp-{gk}">{gl}</a>' for gk, gl, _ in K.GROUPS) + """
<a href="#qual">Qualitative factors</a> <a href="#appx">Methodology &amp; notes</a></div>

<div class="lg">Heatmap colors rank each district <b>within a fiscal year</b> by the metric's good-direction:
<span class="sw" style="background:#86efac"></span>stronger
<span class="sw" style="background:#fde68a"></span>middle
<span class="sw" style="background:#fca5a5"></span>weaker &nbsp;·&nbsp; italic = management/unaudited (ICCSD FY24–25).</div>
""" + "".join(sections) + f"""
<section id="qual"><div class="qual">
<h2 style="font-size:20px;margin:0 0 4px">Qualitative / external factors — named, not scored</h2>
<p style="color:#64748b;font-size:14px;margin:4px 0">Per the agreed approach, rating-agency factors that
cannot be derived from audited financials are listed here rather than estimated. For all Iowa school
districts the institutional framework is the same: a <b>state-determined revenue framework</b> — the
foundation formula caps spending authority, with voter-approved local supplements (ISL, PPEL, SAVE).</p>
<table><tr><td><b>Methodology</b></td><td><b>Factor</b></td><td><b>Weight</b></td><td><b>Why it's external/qualitative</b></td></tr>
{qrows}</table></div></section>

<section id="appx"><div class="appx">
<h2 style="font-size:20px;margin:0 0 8px">Methodology &amp; notes</h2>
<ul>
<li><b>Sources.</b> Audited ACFRs (FY2015–FY2023 for ICCSD; FY2015–FY2025 for peers where filed),
Iowa DOM (UAB, certified enrollment, valuations, levies), the Certified Annual Report (function detail,
FY2017–2023), and ICCSD's published Annual Financial Health Report (FY2015–2019 internal ratios, used verbatim).
ICCSD has <b>not filed FY2024 or FY2025 audits</b>; those two years use management/unaudited actuals (PFM).</li>
<li><b>Operating revenue proxy.</b> Moody's/S&amp;P "operating revenue" is proxied by General Fund revenue
for cross-district comparability; Moody's would also fold in the debt-service fund.</li>
<li><b>Pension/OPEB.</b> The long-term-liabilities ratio uses <b>reported</b> GASB net pension/OPEB
liabilities, not Moody's discount-rate-adjusted ANPL/ANOPEB. Fixed-cost and current-cost ratios need
annual debt service and employer contributions, available chiefly for FY2015–2019 (extracted) — blank where not.</li>
<li><b>Per-capita vs per-pupil.</b> S&amp;P and Moody's score net direct debt, pension, and full value
<b>per capita</b> (population). Audits don't carry population, so those are shown <b>per pupil</b> as an
Iowa-appropriate proxy and are <b>not</b> mapped to the agencies' per-capita rating bands.</li>
<li><b>Implied debt service</b> uses Moody's 20-year level-dollar method at a ~4.0% implied municipal rate
(their FY-by-FY index averages near this over FY2015–25).</li>
<li><b>Reproduce:</b> <code>python3 scripts/build_kpi_dataset.py &amp;&amp; python3 scripts/build_kpi_report.py</code>.
Underlying data: <code>data/kpi-three-methodologies.csv</code>. Definitions: <code>scripts/kpi_catalog.py</code>.</li>
</ul></div></section>

<footer>Generated from <code>data/kpi-three-methodologies.csv</code>. Internal definitions: ICCSD Annual
Financial Health Report. Moody's: <i>US K-12 Public School Districts</i> (24 Jul 2024). S&amp;P:
<i>Methodology For Rating US Governments</i> (9 Sep 2024). Per the repo's discipline, blank cells are
honest gaps, not guesses.</footer>
</div>
<script>
const D = {json.dumps(payload)};
function colorFor(kpi, year, dist){{
  const good = kpi.good;
  if(good==='context') return '';
  const vals=[]; D.districts.forEach(dd=>{{const v=(D.series[kpi.key][dd]||{{}})[year]; if(typeof v==='number') vals.push(v);}});
  if(vals.length<3) return '';
  const v=(D.series[kpi.key][dist]||{{}})[year]; if(typeof v!=='number') return '';
  const s=[...vals].sort((a,b)=>a-b); const rank=s.filter(x=>x<v).length/(s.length-1);
  const t = good==='up'? rank : 1-rank;   // 1 = strong
  if(t>=0.6) return 'background:#86efac'; if(t>=0.33) return 'background:#fde68a'; return 'background:#fca5a5';
}}
function unitFmt(u,v){{ if(typeof v!=='number') return v||'';
  if(u==='usd_pp') return '$'+Math.round(v).toLocaleString();
  if(u==='pct'||u==='ratio_pct') return (Math.round(v*100)/100)+'%';
  return (Math.round(v*100)/100); }}
function findKpi(key){{ for(const g of D.catalog) for(const k of g.kpis) if(k.key===key) return k; }}
document.querySelectorAll('.hbtn').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    const key=btn.dataset.kpi, host=document.getElementById('heat-'+key), kpi=findKpi(key);
    if(host.dataset.open==='1'){{host.innerHTML='';host.dataset.open='0';btn.textContent='Show all 15 districts ▸';return;}}
    let h='<table class="hm"><tr><th class="d">District</th>'+D.years.map(y=>'<th>FY'+String(y).slice(2)+'</th>').join('')+'</tr>';
    D.districts.forEach(dd=>{{
      const me=dd===D.iccsd?' class="me"':'';
      h+='<tr'+me+'><td class="d">'+dd+'</td>';
      D.years.forEach(y=>{{
        const v=(D.series[key][dd]||{{}})[y];
        const bs=(D.basis[dd]||{{}})[y]||''; const proj=(bs&&bs!=='audited'&&v!==undefined)?' proj':'';
        const st=colorFor(kpi,y,dd);
        h+='<td class="'+(st?'':'')+proj.trim()+'" style="'+st+'">'+(v===undefined?'·':unitFmt(kpi.unit,v))+'</td>';
      }});
      h+='</tr>';
    }});
    h+='</table>';
    host.innerHTML=h; host.dataset.open='1'; btn.textContent='Hide ▾';
  }});
}});
</script>
</body></html>"""
    out = p("kpi-three-methodologies.html")
    open(out, "w").write(html)
    print(f"Wrote {out} ({len(html):,} bytes)")

if __name__ == "__main__":
    build()
