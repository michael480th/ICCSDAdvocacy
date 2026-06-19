#!/usr/bin/env python3
"""Generate two presentation artifacts from the benchmark:
   iccsd-findings-handout.html  — one-page printable leave-behind
   iccsd-findings-deck.html     — self-contained slide deck (one finding per slide)
Reads /tmp/audit/cards.json (run build_analysis.py first)."""
import json, statistics as st

cards = json.load(open("/tmp/audit/cards.json"))
IC = next(c for c in cards if c["district"] == "Iowa City CSD")
large = [c for c in cards if (c["enrollment"] or 0) >= 5000 and c["district"] != "Iowa City CSD"]
def avg(fn):
    v=[fn(c) for c in large if fn(c) is not None]; return round(st.mean(v),1) if v else None
rank = sorted(cards, key=lambda c:-c["composite"]).index(IC)+1
debt_pp = lambda c: round(c["debt_last"]*1e6/c["enrollment"]) if (c.get("debt_last") and c.get("enrollment")) else None

# (label, iowa-city value, peer avg, formatter, lower_is_better, scalemax)
BARS = [
 ("Overall financial score (of 5)", IC["composite"], avg(lambda c:c["composite"]), lambda v:f"{v:.1f}", False, 5),
 ("Spending authority left (UAB %)", IC["uab_last"], avg(lambda c:c["uab_last"]), lambda v:f"{v:.0f}%", False, 30),
 ("Days of operating reserves", IC["days_reserves"], avg(lambda c:c.get("days_reserves")), lambda v:f"{v:.0f}", False, 70),
 ("Cash-reserve property tax used (% of cap)", IC["crl_pct"], avg(lambda c:c["crl_pct"]), lambda v:f"{v:.0f}%", True, 60),
 ("Yrs of SAVE revenue already pledged", IC.get("save_years"), avg(lambda c:c.get("save_years")), lambda v:f"{v:.1f}", True, 11),
 ("Building debt per student", debt_pp(IC), avg(debt_pp), lambda v:f"${v/1000:.0f}K", True, 40000),
]
FACTS = [
 ("Last of 15", f"Iowa City ranks <b>{rank}th of the 15 large Iowa districts</b> studied on overall financial health & management — and it isn't close."),
 ("Audits chronically late", "Iowa City filed its <b>FY2024 audit about two years late</b> (June 2026, with <b>five material weaknesses</b>) and its <b>FY2025 audit is still unfiled</b> — the furthest behind of the 15 large districts."),
 ("Spent past the limit", "Its <b>spending authority went negative in 2023</b> — the only district in the group, and the level that by law triggers a <b>state-supervised recovery</b>."),
 ("Lost its rating", "<b>Lost its bond rating in 2024</b> and remains unrated — rare for a district this size, where most regain it within months."),
 ("~9 days of cushion", f"About <b>{IC['days_reserves']} days</b> of operating reserves on hand. The recommended cushion is <b>~60</b>."),
 ("Not enrollment", f"Enrollment is essentially flat (<b>{IC['enr_cagr']:+.1f}%/yr</b>) — this is <b>not</b> a shrinking-district problem. It's about how the money was managed."),
]
def color(v, peer, lower):
    if v is None or peer is None: return "n"
    if lower: return "r" if v>peer*1.5 else "a" if v>peer*1.1 else "g"
    return "r" if v<peer*0.5 else "a" if v<peer*0.85 else "g"

CSS = """*{box-sizing:border-box} body{font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:#0f172a;margin:0;background:#f1f5f9}
.r{color:#dc2626}.a{color:#b45309}.g{color:#16a34a}.n{color:#334155}
.bar{height:9px;background:#e2e8f0;border-radius:5px;overflow:hidden;margin-top:5px}
.fill{height:100%;border-radius:5px} .fill.r{background:#dc2626}.fill.a{background:#d97706}.fill.g{background:#16a34a}.fill.n{background:#64748b}
.peer{height:9px;width:2px;background:#0f172a;opacity:.55}"""

def barblock(label, v, peer, fmt, lower, smax):
    cls = color(v, peer, lower)
    vp = max(0,min(100, abs(v)/smax*100)) if (v is not None and smax) else 0
    pp = max(0,min(100, abs(peer)/smax*100)) if (peer is not None and smax) else 0
    pv = fmt(v) if v is not None else "—"; pe = fmt(peer) if peer is not None else "—"
    return f"""<div class="brow"><div class="blab">{label}</div>
      <div class="bnums"><b class="{cls}">{pv}</b> <span class="bpeer">vs peers ~{pe}</span></div>
      <div class="bar"><div class="fill {cls}" style="width:{vp:.0f}%"></div><div class="peer" style="margin-top:-9px;margin-left:{pp:.0f}%"></div></div></div>"""

# ---------------- HANDOUT (one page) ----------------
bars_html = "".join(barblock(*b) for b in BARS)
facts_html = "".join(f'<li><b>{t}.</b> {d}</li>' for t,d in FACTS)
handout = f"""<!doctype html><html><head><meta charset="utf-8"><title>Iowa City Schools — Benchmark findings</title>
<style>{CSS}
.page{{max-width:780px;margin:0 auto;background:#fff;padding:26px 30px;}}
@media print{{body{{background:#fff}}.page{{max-width:100%}}}}
h1{{font-size:22px;margin:0 0 2px}} .sub{{color:#64748b;font-size:13px;margin:0 0 14px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
@media(max-width:680px){{.cols{{grid-template-columns:1fr}}}}
h2{{font-size:14px;text-transform:uppercase;letter-spacing:.04em;color:#1d4ed8;margin:0 0 8px;border-bottom:1px solid #e2e8f0;padding-bottom:4px}}
.brow{{margin-bottom:11px}} .blab{{font-size:12.5px;color:#334155}} .bnums b{{font-size:17px}} .bpeer{{font-size:11px;color:#94a3b8}}
ul{{margin:0;padding-left:18px}} li{{font-size:13px;margin-bottom:8px}}
.foot{{margin-top:16px;border-top:1px solid #e2e8f0;padding-top:8px;color:#94a3b8;font-size:11px}}
</style></head><body><div class="page">
<h1>Iowa City Schools: the financial picture, in the data</h1>
<p class="sub">Iowa City CSD vs. Iowa's other large districts (5,000+ students), FY2020–FY2025 · audited financials + Iowa state filings</p>
<div class="cols">
 <div><h2>How it compares (Iowa City vs. peer average)</h2>{bars_html}
   <p style="font-size:10.5px;color:#94a3b8;margin-top:4px">Bar = Iowa City; tick = large-district average. Red = concern, amber = caution, green = healthy.</p></div>
 <div><h2>Six facts</h2><ul>{facts_html}</ul></div>
</div>
<div class="foot">Every figure traces to a district's audited financial report or an official Iowa Department of Management / Department of Education filing. Full interactive report, the underlying spreadsheet, and sources: the project repository.</div>
</div></body></html>"""
open("iccsd-findings-handout.html","w").write(handout)

# ---------------- DECK ----------------
slides = []
slides.append(("Iowa City Schools","The financial picture, in the data","A benchmark of Iowa's 15 largest districts · audited financials + state filings · FY2020–FY2025"))
slides.append((f"#{rank} of 15","Iowa City ranks last of the 15 large Iowa districts on overall financial health &amp; management.",f"Composite {IC['composite']:.1f} of 5 — vs. ~{avg(lambda c:c['composite']):.1f} for comparable districts."))
slides.append((f"{IC['uab_last']:.1f}%","Spending authority left — the #1 measure of an Iowa district's health.",f"Peers carry ~{avg(lambda c:c['uab_last']):.0f}%. Iowa City's went <b>negative in 2023</b> — the level that by law triggers a state review."))
slides.append((f"{IC['days_reserves']} days","of operating reserves on hand.","A healthy cushion is ~60 days (GFOA). Peers average ~"+f"{avg(lambda c:c.get('days_reserves')):.0f}."))
slides.append(("Furthest behind","Iowa City filed its FY2024 audit about two years late (June 2026) and still hasn't filed FY2025.","Its FY2024 audit was filed ~710 days after year-end, with five material weaknesses. Every other large district is current."))
slides.append(("Unrated","Lost its bond rating in 2024 — and is still unrated.","Most districts that lose a rating regain it within months. Staying unrated into a 2nd–3rd year is rare for a district this size."))
slides.append((f"{IC.get('save_years'):.1f} yrs","of SAVE sales-tax revenue already pledged to bonds — 2nd-most of any large district.",f"Peers ~{avg(lambda c:c.get('save_years')):.1f} yrs. SAVE can't fund new building until the mid-2030s under current debt."))
slides.append((f"${debt_pp(IC)/1000:.0f}K","in building debt per student (GO + SAVE) — ~1.8× the peer average.","One of the few districts carrying both sales-tax and voter-approved property-tax debt."))
slides.append(("Not enrollment",f"Enrollment is essentially flat ({IC['enr_cagr']:+.1f}%/yr) — in line with peers.","So this is <b>not</b> a shrinking-district problem. It's about how the money was managed."))
slides.append(("The basics","A monthly close. Reconciled accounts. Audited financials on time. A rating in good standing.","Districts running far less money than Iowa City manage all of it, every year. Sources: the project repository."))

def slide(i, big, head, sub):
    return f"""<section class="slide" data-i="{i}"><div class="s-in">
      <div class="big">{big}</div><div class="head">{head}</div><div class="sub">{sub}</div>
      <div class="snum">{i+1} / {len(slides)}</div></div></section>"""
slides_html = "".join(slide(i,*s) for i,s in enumerate(slides))
deck = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — findings deck</title><style>
*{{box-sizing:border-box}} html,body{{margin:0;height:100%;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:#0f172a;color:#fff}}
.slide{{display:none;height:100vh;width:100%;padding:7vh 9vw;flex-direction:column;justify-content:center}}
.slide.on{{display:flex}} .s-in{{max-width:900px;margin:auto;width:100%}}
.big{{font-size:min(13vw,120px);font-weight:800;line-height:1;color:#60a5fa;margin-bottom:18px}}
.head{{font-size:min(5vw,34px);font-weight:700;line-height:1.2;margin-bottom:14px}}
.sub{{font-size:min(3.4vw,20px);color:#cbd5e1;line-height:1.45}} .sub b,.head b{{color:#fff}}
.snum{{position:fixed;bottom:18px;right:24px;color:#475569;font-size:14px}}
.nav{{position:fixed;bottom:14px;left:0;right:0;text-align:center}}
.nav button{{background:#1e293b;color:#cbd5e1;border:1px solid #334155;border-radius:8px;padding:7px 14px;font-size:15px;cursor:pointer;margin:0 4px}}
.hint{{position:fixed;top:16px;right:20px;color:#475569;font-size:12px}}
@media print{{.slide{{display:flex;height:auto;page-break-after:always;color:#0f172a}}body{{background:#fff;color:#0f172a}}.big{{color:#1d4ed8}}.sub{{color:#334155}}.nav,.hint{{display:none}}}}
</style></head><body>
<div class="hint">&larr; &rarr; to navigate</div>
{slides_html}
<div class="nav"><button onclick="go(-1)">&lsaquo; Prev</button><button onclick="go(1)">Next &rsaquo;</button></div>
<script>
let i=0;const S=[...document.querySelectorAll('.slide')];
function show(){{S.forEach((s,k)=>s.classList.toggle('on',k===i))}}
function go(d){{i=Math.max(0,Math.min(S.length-1,i+d));show()}}
document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key===' ')go(1);if(e.key==='ArrowLeft')go(-1)}});
show();
</script></body></html>"""
open("iccsd-findings-deck.html","w").write(deck)
print(f"handout: {len(handout)//1024}KB | deck: {len(deck)//1024}KB, {len(slides)} slides")
