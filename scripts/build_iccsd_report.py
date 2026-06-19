#!/usr/bin/env python3
"""
Build a public-facing, self-contained report comparing Iowa City CSD to its SIZE-MATCHED peers,
one KPI per card. Reads /tmp/audit/cards.json (run build_analysis.py first).

Peer groups are size-matched (apples-to-apples), since Iowa City is one of the largest districts:
  - "Large districts"     = every district with 5,000+ students (excludes the smaller districts)
  - "Best-run large districts" = the 5 highest-scoring of those large districts
"""
import json, html, datetime, statistics as st, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

SIZE_MIN = 5000
cards = json.load(open("/tmp/audit/cards.json"))      # sorted desc by composite
IC = next(c for c in cards if c["district"] == "Iowa City CSD")
top10 = [c for c in cards if (c["enrollment"] or 0) >= SIZE_MIN and c["district"] != "Iowa City CSD"]
top5 = sorted(top10, key=lambda c: -c["composite"])[:5]   # best-run of the large districts

def avg(group, fn):
    vals = [fn(c) for c in group if fn(c) is not None]
    return round(st.mean(vals), 1) if vals else None

def last_year(c): return max(int(y) for y in c["years"])
def lastv(a):
    for v in reversed(a or []):
        if v is not None: return v
    return None

# ---- KPI definitions ----
# each: title, what (plain), why (plain), get(card)->value, fmt, color(value)->g/a/r,
#       scalemax, takeaway(ic,t10,t5)->str. context=True for neutral (no good/bad).
def band_color(v, good, ok):   # higher-better thresholds
    return "g" if v >= good else "a" if v >= ok else "r"
def low_color(v, good, ok):    # lower-better thresholds
    return "g" if v <= good else "a" if v <= ok else "r"

KPIS = [
 dict(id="composite", title="Overall financial score", unit="/5", scalemax=5,
   what="A single 1–5 grade blending everything below: financial health, the quality of financial management, and whether building plans are affordable.",
   why="It's the one-glance answer to “how is this district doing financially?” — 5 is excellent, 1 is in serious trouble.",
   get=lambda c: c["composite"], fmt=lambda v: f"{v:.1f}", color=lambda v: band_color(v,4,3),
   takeaway=lambda ic,t10,t5: f"Iowa City scores <b>{ic:.1f} out of 5</b> — the lowest of the 15 large districts studied — while comparably large districts average <b>{t10:.1f}</b>, and the best-run large districts average <b>{t5:.1f}</b>."),

 dict(id="uab", title="Spending authority left (the #1 measure)", unit="%", scalemax=30,
   what="Iowa law caps how much a district may spend each year — separately from how much cash it has. This is the unused “room” left over, as a share of its budget.",
   why="It is the single most important measure of an Iowa district's financial health. Running it to zero (or negative) is unlawful and forces a state-supervised recovery plan.",
   get=lambda c: c["uab_last"], fmt=lambda v: f"{v:.1f}%", color=lambda v: band_color(v,10,5),
   takeaway=lambda ic,t10,t5: f"Iowa City has just <b>{ic:.1f}%</b> of room left — roughly a seventh of the <b>{t10:.0f}%</b> that comparably large districts carry — and it actually went <b>negative in 2023</b>, the level that triggers state review."),

 dict(id="solv", title="Rainy-day reserves", unit="%", scalemax=25, band=(5,15),
   what="The district's savings cushion (its general-fund reserves) measured against one year of revenue.",
   why="Reserves absorb surprises — a bad budget year, a late state payment, an emergency repair. In Iowa, 5–15% is considered healthy. This reserves-as-a-percent-of-revenue measure is the one the credit-rating agencies (Moody's, S&P) actually use to score a district.",
   get=lambda c: c["solv_last"], fmt=lambda v: f"{v:.1f}%", color=lambda v: band_color(v,5,2),
   takeaway=lambda ic,t10,t5: f"Iowa City's cushion is about <b>{ic:.1f}%</b> — well below the 5–15% healthy range — versus <b>{t10:.0f}%</b> for large districts and <b>{t5:.0f}%</b> for the best-run large districts."),

 dict(id="dayscash", title="Days of operating reserves on hand", unit=" days", scalemax=90,
   what="How many days the district could keep running on its rainy-day reserves — unassigned general-fund balance divided by average daily spending. (This excludes restricted money like bond proceeds, which is why it's lower than total 'cash on hand.')",
   why="A plain-English liquidity gauge: the GFOA guideline is to keep at least ~60 days (about two months) of cash. A thin cushion means little buffer for a bad month, a late state payment, or an emergency. (Days-of-cash is a GFOA/analyst convention; the rating agencies score reserves as a percent of revenue — the 'Rainy-day reserves' measure above.)",
   get=lambda c: c.get("days_reserves"), fmt=lambda v: f"{v:.0f} days", color=lambda v: band_color(v,60,30),
   takeaway=lambda ic,t10,t5: f"Iowa City could operate only about <b>{ic:.0f} days</b> on its reserves — versus ~<b>{t10:.0f} days</b> for large districts and ~<b>{t5:.0f}</b> for the best-run (GFOA recommends ~60). It is the thinnest cushion of any large district except Waterloo, whose reserves are negative."),

 dict(id="margin", title="Living within its means", unit="%", scalemax=4,
   what="Whether the district took in more than it spent, averaged over the last three years (its “operating margin”).",
   why="Consistently spending more than you bring in drains reserves and, eventually, spending authority. Above zero means it's living within its means.",
   get=lambda c: c["marg3"], fmt=lambda v: f"{v:+.1f}%", color=lambda v: band_color(v,1,0),
   takeaway=lambda ic,t10,t5: f"Here Iowa City is roughly break-even (<b>{ic:+.1f}%</b>), actually a touch better than the large-district average (<b>{t10:+.1f}%</b>) — its problem is depleted reserves and authority, not runaway recent spending."),

 dict(id="audit", title="Most recent completed audit", unit=" yrs behind", scalemax=2.5, lowerbetter=True,
   what="How many years behind the current cycle the district's most recent finished audit is. (The current year is 2025.)",
   why="Audited financial statements are how the public, lenders, and the state verify the numbers. Falling behind erodes trust — and cost Iowa City its bond rating.",
   get=lambda c: 2025 - last_year(c), fmt=lambda v: ("current" if v<=0 else f"{v:.0f} yr"+("s" if v>=2 else "")+" behind"),
   color=lambda v: low_color(v,0,1),
   takeaway=lambda ic,t10,t5: f"Iowa City's newest finished audit is for <b>2023 — two years behind</b> — and its 2024 and 2025 audits still aren't filed. The top districts are current."),

 dict(id="quality", title="Quality of financial management", unit="/5", scalemax=5,
   what="A 1–5 grade for how cleanly the books are kept: audit opinions, internal-control problems, repeat findings, on-time filing, and reporting-excellence awards.",
   why="Even with money in the bank, a district needs accurate, timely, well-controlled books to make sound decisions and keep the public's trust.",
   get=lambda c: c["quality"], fmt=lambda v: f"{v:.1f}", color=lambda v: band_color(v,4,3),
   takeaway=lambda ic,t10,t5: f"Iowa City scores <b>{ic:.1f} of 5</b> — the bottom of the group — against <b>{t10:.1f}</b> for large districts, reflecting late audits, unreconciled accounts, and repeat control findings."),

 dict(id="crl", title="Reliance on the cash-reserve property tax", unit="%", scalemax=60, lowerbetter=True,
   what="How much of its allowed “cash-reserve” property tax the district is using — a levy whose only purpose is to build up cash.",
   why="Leaning hard on this tax can mean a district is taxing residents heavily just to keep cash on hand. Lower is generally better for taxpayers.",
   get=lambda c: c["crl_pct"], fmt=lambda v: f"{v:.0f}%", color=lambda v: low_color(v,25,40),
   takeaway=lambda ic,t10,t5: f"Iowa City is using <b>{ic:.0f}%</b> of this tax's limit — about three times the large-district average (<b>{t10:.0f}%</b>) — i.e. taxing heavily to stay liquid, even as its spending authority is exhausted."),

 dict(id="taxrate", title="School property-tax rate", unit=" /$1,000", scalemax=18, lowerbetter=True,
   what="The school portion of the local property-tax rate, stated per $1,000 of taxable property value.",
   why="This is what local property owners actually pay to fund the schools — the most direct cost to the community. A higher rate is a heavier burden, worth weighing against how well the money is managed.",
   get=lambda c: lastv(c["deep"]["levy_rate"]), fmt=lambda v: f"${v:.2f}", color=lambda v: low_color(v,14.5,16.5),
   takeaway=lambda ic,t10,t5: f"Iowa City's school tax rate is about <b>${ic:.2f} per $1,000</b> of value — roughly <b>{(ic/t10-1)*100:.0f}% above</b> the large-district average of <b>${t10:.2f}</b> (among the higher rates, though a few growing districts are higher). Paired with its heavy use of the cash-reserve levy, local taxpayers are paying comparatively more."),

 dict(id="totaldebt", title="Total building debt per student", unit="$", scalemax=40000, lowerbetter=True,
   what="Everything the district has borrowed for buildings — both SAVE (sales-tax) bonds and voter-approved GO (property-tax) bonds — divided by the number of students.",
   why="Borrowed money is repaid for years out of restricted building funds and property taxes, so more debt per student means more of tomorrow's revenue is already committed. Some debt is healthy — especially in fast-growing districts building new schools — so it's best read alongside enrollment.",
   get=lambda c: round(c["debt_last"]*1e6/c["enrollment"]) if (c.get("debt_last") is not None and c.get("enrollment")) else None,
   fmt=lambda v: f"${v:,.0f}", color=lambda v: low_color(v,12000,20000),
   takeaway=lambda ic,t10,t5: f"Iowa City carries about <b>${ic:,.0f} per student</b> in building debt — roughly <b>{ic/t10:.1f}×</b> the large-district average of <b>${t10:,.0f}</b>, and the 3rd-highest of the 15. It's one of only a few districts carrying <b>both</b> SAVE and voter-approved GO debt, which is why its total load is so high despite its mid-pack size."),

 dict(id="annualds", title="Annual debt payments per student", unit="$", scalemax=3500, lowerbetter=True,
   what="How much the district pays each year to repay its building debt, per student.",
   why="This is money committed to past borrowing rather than to current students or new projects. It comes from restricted building funds and property taxes — not the classroom budget — but a higher figure means less room to maneuver.",
   get=lambda c: round(c["annual_ds"]/c["enrollment"]) if (c.get("annual_ds") and c.get("enrollment")) else None,
   fmt=lambda v: f"${v:,.0f}", color=lambda v: low_color(v,1500,2500),
   takeaway=lambda ic,t10,t5: f"Iowa City spends about <b>${ic:,.0f} per student each year</b> on building-debt payments — above the <b>${t10:,.0f}</b> large-district average (4th-highest of 15), though several fast-growing districts pay more. A moderate burden, on top of an already-stretched operating budget."),

 dict(id="save", title="Years of SAVE money already committed", unit=" yrs", scalemax=11, lowerbetter=True,
   what="SAVE is the statewide penny sales tax Iowa schools use to pay for buildings. This is how many years of that sales-tax revenue the district has already pledged to existing bond payments.",
   why="The more years committed, the less SAVE money is free for new projects. When it's fully committed, a district must lean on property-tax borrowing (PPEL or GO bonds) or wait years for room to open up.",
   get=lambda c: c.get("save_years"), fmt=lambda v: f"{v:.1f} yrs", color=lambda v: low_color(v,5,7),
   takeaway=lambda ic,t10,t5: f"Iowa City has pledged about <b>{ic:.1f} years</b> of its SAVE sales-tax revenue to existing bonds — the 2nd-most of any large district and well above the <b>{t10:.1f}-year</b> peer average — so SAVE can't fund new building until the mid-2030s, leaving PPEL and new borrowing to cover the gap."),

 dict(id="enroll", title="Enrollment trend", unit="%/yr", scalemax=4, context=True,
   what="The yearly change in the number of students, which drives most of a district's funding.",
   why="Declining enrollment is a common cause of school budget trouble. This shows whether Iowa City's problems stem from shrinking — they don't.",
   get=lambda c: c["enr_cagr"], fmt=lambda v: f"{v:+.1f}%", color=lambda v: "n",
   takeaway=lambda ic,t10,t5: f"Iowa City's enrollment is essentially flat (<b>{ic:+.1f}%/yr</b>), in line with peers — so its financial troubles are <b>not</b> caused by losing students. They are about how the money has been managed."),
]

date = datetime.date(2026, 6, 2).strftime("%B %Y")

def bar(v, scalemax, cls, lowerbetter=False):
    pct = max(0, min(100, abs(v) / scalemax * 100)) if scalemax else 0
    return f'<div class="bar"><div class="fill {cls}" style="width:{pct:.0f}%"></div></div>'

def panel(label, v, kpi, highlight=False):
    if v is None: return f'<div class="pnl"><div class="pl">{label}</div><div class="pv">—</div></div>'
    cls = kpi["color"](v) if not kpi.get("context") else "n"
    val = kpi["fmt"](v)
    return (f'<div class="pnl{" me" if highlight else ""}"><div class="pl">{label}</div>'
            f'<div class="pv {cls}">{val}</div>{bar(v, kpi["scalemax"], cls, kpi.get("lowerbetter"))}</div>')

cards_html = []
for kpi in KPIS:
    icv, t10, t5 = kpi["get"](IC), avg(top10, kpi["get"]), avg(top5, kpi["get"])
    note = "" if not kpi.get("band") else f'<span class="bnote">healthy range: {kpi["band"][0]}–{kpi["band"][1]}%</span>'
    dirn = "lower is better" if kpi.get("lowerbetter") else ("context — not better or worse" if kpi.get("context") else "higher is better")
    cards_html.append(f"""<div class="kpi">
  <div class="khead"><h3>{html.escape(kpi['title'])}</h3><span class="dir">{dirn}{note}</span></div>
  <p class="what"><b>What it is:</b> {kpi['what']}</p>
  <p class="why"><b>Why it matters:</b> {kpi['why']}</p>
  <div class="pnls">
    {panel("Iowa City CSD", icv, kpi, highlight=True)}
    {panel("Large districts (5,000+ students) avg", t10, kpi)}
    {panel("Best-run large districts (avg)", t5, kpi)}
  </div>
  <p class="take">{kpi['takeaway'](icv, t10, t5)}</p>
</div>""")

DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — How They Compare</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:920px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:30px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 18px;font-size:16px}}
.intro{{background:#fff;border:1px solid var(--line);border-left:4px solid #2563eb;border-radius:10px;padding:16px 20px;margin-bottom:10px}}
.intro p{{margin:6px 0}} .intro b{{color:var(--ink)}}
.legend{{font-size:13px;color:var(--mut);margin:14px 2px 22px}}
.legend .sw{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:middle;margin:0 4px 0 12px}}
.kpi{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.khead{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:12px}}
.khead h3{{margin:0;font-size:21px}} .dir{{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}}
.bnote{{display:block;text-transform:none;letter-spacing:0;color:#16a34a;font-size:12px;margin-top:2px}}
.what,.why{{margin:6px 0;font-size:15px;color:#334155}} .what b,.why b{{color:#0f172a}}
.pnls{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:16px 0 12px}}
@media(max-width:620px){{.pnls{{grid-template-columns:1fr}}}}
.pnl{{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:#f8fafc}}
.pnl.me{{background:#eff6ff;border-color:#bfdbfe;border-width:2px}}
.pl{{font-size:12.5px;color:var(--mut);margin-bottom:6px;font-weight:600}}
.pnl.me .pl{{color:#1d4ed8}}
.pv{{font-size:30px;font-weight:800;line-height:1.1}}
.pv.g{{color:#16a34a}} .pv.a{{color:#b45309}} .pv.r{{color:#dc2626}} .pv.n{{color:#334155}}
.bar{{height:7px;background:#e2e8f0;border-radius:4px;margin-top:9px;overflow:hidden}}
.fill{{height:100%;border-radius:4px}} .fill.g{{background:#16a34a}} .fill.a{{background:#d97706}} .fill.r{{background:#dc2626}} .fill.n{{background:#64748b}}
.take{{margin:6px 0 0;font-size:15.5px;line-height:1.55;background:#fafafa;border-left:3px solid #94a3b8;border-radius:6px;padding:10px 14px;color:#1f2937}}
.take b{{color:#0f172a}}
footer{{color:var(--mut);font-size:12.5px;margin-top:34px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body>{nav("overview")}<div class="wrap">

<h1>Iowa City Schools: How They Compare</h1>
<p class="sub">Iowa City Community School District measured against the strongest large districts in the state — one measure at a time · {date}</p>

<div class="intro">
<p>Iowa City Community School District (ICCSD) is one of the largest districts in the state — about
14,400 students. To keep the comparison fair, it is measured here only against other <b>large
districts</b>, not small ones. For each financial measure it sits beside two size-matched peer groups:</p>
<p>• <b>Large districts</b> — every Iowa district in this study with <b>5,000+ students</b> (12 districts).<br>
• <b>Best-run large districts</b> — the 5 highest-scoring of those large districts.</p>
<p>Each card explains the measure in plain language, why it matters to your community, and what Iowa
City's number means next to its peers.</p>
</div>

<div class="legend">How to read the colors:
<span class="sw" style="background:#16a34a"></span>healthy / strong
<span class="sw" style="background:#d97706"></span>caution
<span class="sw" style="background:#dc2626"></span>concern
&nbsp;·&nbsp; bars are scaled within each card.
</div>

{''.join(cards_html)}

<footer>
Iowa City CSD compared with size-matched peers, using audited financial reports (FY2020–FY2025) and
Iowa state financial filings. To keep the comparison fair for a district of Iowa City's size,
“Large districts” includes only the 12 districts in this study with 5,000+ students; “Best-run large
districts” are the 5 highest-scoring of those by overall composite score. (Districts smaller than
5,000 students are excluded from the comparison entirely.) State spending-authority figures are
available even though Iowa City's 2024 and 2025 audits are not yet filed. Companion: the full
benchmark report covering all districts.
</footer>
</div></body></html>"""

# Write both the named page and the GitHub Pages landing page (index.html) so they
# never drift — index.html IS this page; no manual copy/rename step is ever needed.
for out in ("iccsd-vs-peers.html", "index.html"):
    open(out, "w").write(DOC)
print(f"Wrote iccsd-vs-peers.html + index.html ({len(DOC)//1024} KB), {len(KPIS)} KPI cards")