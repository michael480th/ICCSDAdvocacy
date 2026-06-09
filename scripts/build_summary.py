#!/usr/bin/env python3
"""One-screen summary table: Iowa City vs. all large peers vs. best-run peers.
Reads /tmp/audit/cards.json. -> iccsd-summary.html"""
import json, statistics as st
cards = json.load(open("/tmp/audit/cards.json"))
IC = next(c for c in cards if c["district"] == "Iowa City CSD")
large = [c for c in cards if (c["enrollment"] or 0) >= 5000 and c["district"] != "Iowa City CSD"]
best = sorted(large, key=lambda c:-c["composite"])[:5]
def A(grp, fn):
    v=[fn(c) for c in grp if fn(c) is not None]; return st.mean(v) if v else None
debt_pp = lambda c: (c["debt_last"]*1e6/c["enrollment"]) if (c.get("debt_last") and c.get("enrollment")) else None
yrs_behind = lambda c: 2025 - max(int(y) for y in c["years"])
lastlevy = lambda c: next((v for v in reversed(c["deep"]["levy_rate"]) if v is not None), None)
annual_pp = lambda c: (c["annual_ds"]/c["enrollment"]) if (c.get("annual_ds") and c.get("enrollment")) else None

# (label, getter, fmt, dir: 'hi'|'lo'|'ctx', good, ok)   good/ok are absolute thresholds for the IC cell
ROWS = [
 ("Overall financial score (of 5)", lambda c:c["composite"], lambda v:f"{v:.1f}", "hi", 4, 3),
 ("Spending authority left — UAB (%)", lambda c:c["uab_last"], lambda v:f"{v:.0f}%", "hi", 10, 5),
 ("Rainy-day reserves / solvency (%)", lambda c:c["solv_last"], lambda v:f"{v:.0f}%", "hi", 10, 5),
 ("Days of operating reserves", lambda c:c.get("days_reserves"), lambda v:f"{v:.0f}", "hi", 60, 30),
 ("Operating margin, 3-yr avg (%)", lambda c:c["marg3"], lambda v:f"{v:+.1f}%", "hi", 0, -2),
 ("Most recent audit (yrs behind)", yrs_behind, lambda v:("current" if v<=0 else f"{v:.0f} yr"+("s" if v>=2 else "")), "lo", 0, 1),
 ("Financial-management quality (of 5)", lambda c:c["quality"], lambda v:f"{v:.1f}", "hi", 4, 3),
 ("Cash-reserve tax used (% of cap)", lambda c:c["crl_pct"], lambda v:f"{v:.0f}%", "lo", 25, 40),
 ("School property-tax rate ($/$1,000)", lastlevy, lambda v:f"${v:.2f}", "lo", 14.5, 16.5),
 ("Building debt per student", debt_pp, lambda v:f"${v/1000:.0f}K", "lo", 12000, 20000),
 ("Annual debt payments per student", annual_pp, lambda v:f"${v:,.0f}", "lo", 1500, 2500),
 ("Years of SAVE revenue pledged", lambda c:c.get("save_years"), lambda v:f"{v:.1f}", "lo", 5, 7),
 ("Enrollment trend (%/yr)", lambda c:c["enr_cagr"], lambda v:f"{v:+.1f}%", "ctx", 0, 0),
]
def cls(v, d, good, ok):
    if v is None or d=="ctx": return "n"
    if d=="hi": return "g" if v>=good else "a" if v>=ok else "r"
    return "g" if v<=good else "a" if v<=ok else "r"
def fmt(fn, v): return fn(v) if v is not None else "—"

rows_html=""
for label, get, f, d, good, ok in ROWS:
    icv, lv, bv = get(IC), A(large,get), A(best,get)
    arrow = "↑ better" if d=="hi" else "↓ better" if d=="lo" else "context"
    rows_html += f"""<tr><td class="m">{label}<span class="dir">{arrow}</span></td>
      <td class="ic {cls(icv,d,good,ok)}">{fmt(f,icv)}</td>
      <td>{fmt(f,lv)}</td><td>{fmt(f,bv)}</td></tr>"""

html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City vs. peers — summary</title><style>
*{{box-sizing:border-box}} body{{font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:#0f172a;margin:0;background:#f1f5f9}}
.wrap{{max-width:760px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:23px;margin:0 0 3px}} .sub{{color:#64748b;font-size:13.5px;margin:0 0 16px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;font-size:14.5px}}
th,td{{padding:10px 12px;text-align:center;border-bottom:1px solid #eef2f7}}
th{{background:#1f4e79;color:#fff;font-size:12px;text-transform:uppercase;letter-spacing:.03em}}
th:first-child,td.m{{text-align:left}} td.m{{font-weight:600;color:#334155}}
.dir{{display:block;font-size:10.5px;color:#94a3b8;font-weight:400;text-transform:none;letter-spacing:0}}
td.ic{{font-weight:800;font-size:16px}} th.ic{{background:#15396b}}
.g{{color:#16a34a}} .a{{color:#b45309}} .r{{color:#dc2626}} .n{{color:#334155}}
tr:last-child td{{border-bottom:none}}
.foot{{color:#94a3b8;font-size:11.5px;margin-top:12px}}
.key{{font-size:12px;color:#64748b;margin:10px 2px}} .key b.g{{color:#16a34a}} .key b.a{{color:#b45309}} .key b.r{{color:#dc2626}}
</style></head><body><div class="wrap">
<h1>Iowa City Schools vs. its peers — at a glance</h1>
<p class="sub">One row per measure. Compared only to similarly large Iowa districts (5,000+ students), FY2020–FY2025 · audited financials + Iowa state filings.</p>
<table>
<thead><tr><th>Measure</th><th class="ic">Iowa City</th><th>All large peers (avg)</th><th>Best-run peers (avg)</th></tr></thead>
<tbody>{rows_html}</tbody></table>
<p class="key">Iowa City's value is shaded <b class="g">green</b> (healthy) · <b class="a">amber</b> (caution) · <b class="r">red</b> (concern). "Best-run peers" = the 5 highest-scoring large districts.</p>
<p class="foot">Every figure traces to a district's audited financial report or an official Iowa state filing. Detailed report, charts, and sources: the project repository.</p>
</div></body></html>"""
open("iccsd-summary.html","w").write(html)
print(f"Wrote iccsd-summary.html ({len(html)//1024} KB), {len(ROWS)} rows")
