#!/usr/bin/env python3
"""
Build other-analyses.html — the catch-all index for the narrower and older analyses that
don't belong on the four main "doors." Two groups: the detailed deep-dives that sit behind a
main page, and the narrower / point-in-time topics. Self-contained.

Run:  python3 scripts/build_other_analyses.py   ->  other-analyses.html
"""
import datetime, html, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nav import nav

# (href, title, blurb)
DEEP = [
    ("iccsd-liquidity-trend.html", "Reserves over time — detailed",
     "The full reserves story: spending-authority cushion (2017–2025) and audited cash reserves "
     "(2020–2025), charted on their own. Summarized on the “Does it have a cushion?” page."),
    ("iccsd-operating-cash.html", "Operating cash — detailed",
     "Days-cash-on-hand through FY2026, with the shareable infographic and the full caution note on "
     "the unaudited recent years. Summarized on the “Does it have a cushion?” page."),
    ("car-vs-audited.html", "Self-reported vs. audited — full matrix",
     "The district-by-year grid comparing each district's self-reported (CAR) General Fund balance to "
     "its audited books, headlined on Iowa City's FY2023 gap. The detail behind the trust screen."),
]
NARROW = [
    ("activity-fund.html", "Student Activities fund",
     "Year-end balance of each district's student-activity fund — self-reported, audited, and per "
     "student. Iowa City carries the thinnest cushion of the 15."),
    ("FY24-UAB-cushion.html", "FY24 spending-authority cushion",
     "A point-in-time look at why Iowa City's FY24 unspent-budget-authority cushion is roughly $3.3M "
     "wide and what it means for spending authority."),
    ("FY24-audit-watchlist.html", "FY24 audit watchlist",
     "A plain-English guide to what to check first when Iowa City's overdue FY24 audit is finally "
     "released."),
    ("iccsd-filing-vs-control.html", "Filing timeliness vs. spending control",
     "An exploratory scatterplot: does how promptly a district files its audited financials relate to "
     "how much spending-authority cushion it keeps?"),
    ("solon-financial-health.html", "Solon CSD — financial health",
     "A companion look at a smaller neighboring district, outside the 15-district large-district "
     "benchmark."),
]


def cards(items):
    out = []
    for href, title, blurb in items:
        out.append(
            f'<a class="item" href="{href}"><div class="t">{html.escape(title)} '
            f'<span class="arr">&rarr;</span></div><div class="b">{html.escape(blurb)}</div></a>')
    return "\n".join(out)


date = datetime.date(2026, 6, 18).strftime("%B %Y")
DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City Schools — Other analyses</title>
<style>
:root{{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0}}
*{{box-sizing:border-box}} body{{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}}
.wrap{{max-width:960px;margin:0 auto;padding:32px 20px 70px}}
h1{{font-size:28px;margin:0 0 6px}} .sub{{color:var(--mut);margin:0 0 22px}}
h2{{font-size:18px;margin:26px 0 4px}} .gnote{{color:var(--mut);font-size:14px;margin:0 0 12px}}
.grid{{display:grid;gap:12px}}
.item{{display:block;background:#fff;border:1px solid var(--line);border-radius:12px;padding:15px 18px;text-decoration:none;color:inherit;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.item:hover{{border-color:#bfdbfe;background:#fbfdff}}
.item .t{{font-weight:700;font-size:16px;color:#0f172a}} .item .arr{{color:#2563eb}}
.item .b{{font-size:14px;color:#475569;margin-top:3px}}
.back{{display:inline-block;margin-top:24px;color:#2563eb;text-decoration:none;font-weight:600}}
</style></head><body>{nav("more")}<div class="wrap">

<h1>Other analyses</h1>
<p class="sub">The narrower and older pieces, kept here so the four main pages stay focused. The
detailed versions behind those main pages live here too · {date}</p>

<h2>Detailed versions</h2>
<p class="gnote">The full, single-topic pages that the main doors summarize.</p>
<div class="grid">
{cards(DEEP)}
</div>

<h2>Narrower &amp; point-in-time topics</h2>
<p class="gnote">Specific questions and snapshots that aren't part of the core story.</p>
<div class="grid">
{cards(NARROW)}
</div>

<a class="back" href="index.html">&larr; Back to the overview</a>
</div></body></html>"""

open("other-analyses.html", "w").write(DOC)
print(f"Wrote other-analyses.html ({len(DOC)//1024} KB), {len(DEEP)+len(NARROW)} links")
