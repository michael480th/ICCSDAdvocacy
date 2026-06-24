#!/usr/bin/env python3
"""Build the audit-findings distribution page for the 15 large Iowa districts.

Answers a single question: across Iowa's large school districts, how many audit
findings — and how many *material weaknesses* — is normal in a year, and where does
Iowa City sit in that distribution?

Reads the per-district audit extractions in ``data/district-extractions/*.csv``
(one row per district per fiscal year, FY2020-2025), writes a tidy machine-readable
companion ``data/audit-findings-distribution.csv``, and emits the static page
``audit-findings-distribution.html`` in the repo root.

Run from the repo root:  ``python scripts/build_audit_findings.py``
"""
from __future__ import annotations

import csv
import glob
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from _nav import nav  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACT_GLOB = os.path.join(ROOT, "data", "district-extractions", "*.csv")
OUT_CSV = os.path.join(ROOT, "data", "audit-findings-distribution.csv")
# A second copy at the repo root, because _config.yml excludes data/ from the
# published GitHub Pages site. The live page (audit-findings-live.html) fetches
# THIS copy so the auto-refresh works on the deployed site, not just in the repo.
OUT_CSV_SITE = os.path.join(ROOT, "audit-findings-distribution.csv")
OUT_HTML = os.path.join(ROOT, "audit-findings-distribution.html")

# Display names are slightly long in the raw extractions; tidy for the chart.
NAME_FIX = {
    "College Community School District (Prairie)": "College CSD (Prairie)",
    "College Community School District": "College CSD (Prairie)",
    "College CSD": "College CSD (Prairie)",
    "Des Moines Independent CSD": "Des Moines CSD",
}
ICCSD = "Iowa City CSD"


def _int(x):
    try:
        return int(str(x).strip())
    except (TypeError, ValueError):
        return None


def load_rows():
    rows = []
    for path in sorted(glob.glob(EXTRACT_GLOB)):
        with open(path, newline="") as fh:
            for r in csv.DictReader(fh, delimiter="|"):
                name = NAME_FIX.get(r["district"].strip(), r["district"].strip())
                rows.append(
                    {
                        "district": name,
                        "fiscal_year": r["fiscal_year"].strip(),
                        "report_date": (r.get("report_date") or "").strip(),
                        "opinion": (r.get("opinion_type") or "").strip(),
                        "findings_count": _int(r.get("findings_count")),
                        "material_weakness": (r.get("material_weakness") or "").strip().upper() == "Y",
                        "significant_deficiency": (r.get("significant_deficiency") or "").strip().upper() == "Y",
                        "repeat_finding": (r.get("repeat_finding") or "").strip().upper() == "Y",
                    }
                )
    return rows


def write_csv(rows):
    cols = [
        "district",
        "fiscal_year",
        "report_date",
        "opinion",
        "findings_count",
        "material_weakness",
        "significant_deficiency",
        "repeat_finding",
    ]
    ordered = sorted(rows, key=lambda x: (x["district"], x["fiscal_year"]))
    for path in (OUT_CSV, OUT_CSV_SITE):
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in ordered:
                w.writerow({c: ("Y" if r[c] is True else "N" if r[c] is False else r[c]) for c in cols})


def summarize(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["district"]].append(r)
    out = []
    for d, rs in by.items():
        filed = [r for r in rs if r["findings_count"] is not None]
        counts = [r["findings_count"] for r in filed]
        mw_years = sorted(r["fiscal_year"] for r in rs if r["material_weakness"])
        out.append(
            {
                "district": d,
                "years_filed": len(filed),
                "peak": max(counts) if counts else 0,
                "avg": (sum(counts) / len(counts)) if counts else 0.0,
                "mw_years": mw_years,
                "mw_count": len(mw_years),
                "is_iccsd": d == ICCSD,
            }
        )
    out.sort(key=lambda x: (-x["peak"], -x["avg"]))
    return out


# ---- HTML ------------------------------------------------------------------

CSS = """
:root{--ink:#0f172a;--ink-soft:#334155;--ink-mute:#64748b;--bg:#f7f9fc;--hero:#0b1426;
--accent:#2c5fa1;--red:#b03a2e;--red-soft:#fdecec;--red-line:#f5b7b1;--gold:#b58220;
--gold-soft:#fdf3df;--gold-line:#ecd49a;--green:#1e7a3a;--green-soft:#e7f5ec;--bar:#9db8de;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg);line-height:1.55;font-size:17px}
.container{max-width:820px;margin:0 auto;padding:0 1.5rem}
.hero{background:var(--hero);color:#fff;padding:2.6rem 0 2.2rem;margin-bottom:1.6rem}
.hero .eyebrow{color:#6ea8fe;font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;margin-bottom:.8rem}
.hero h1{font-size:2.25rem;line-height:1.1;margin:0 0 .8rem;font-weight:800;letter-spacing:-.02em}
.hero .sub{color:#c8d4e8;font-size:1.08rem;max-width:660px;margin:0}
h2{font-size:1.35rem;font-weight:800;margin:2.4rem 0 .5rem}
p{margin:0 0 1rem;color:var(--ink-soft)} p strong{color:var(--ink)}
a{color:var(--accent)}
.section-sub{color:var(--ink-mute);font-size:.97rem;margin:0 0 1rem}
.tldr{background:#fff;border:1px solid #e2e8f0;border-left:5px solid var(--accent);border-radius:10px;padding:1.1rem 1.3rem;margin:0 0 1rem}
.tldr .k{font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-mute);margin-bottom:.55rem}
.tldr ul{list-style:none;margin:0;padding:0}
.tldr li{display:flex;gap:.6rem;align-items:flex-start;margin-bottom:.55rem;font-size:1.0rem;color:var(--ink-soft)}
.tldr li:last-child{margin-bottom:0}.tldr .ic{flex:0 0 auto;font-size:1.05rem}
.tldr li strong{color:var(--ink)}
/* chart */
.chart{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:1.1rem 1.2rem;margin:0 0 .6rem}
.row{display:grid;grid-template-columns:135px 1fr 34px;align-items:center;gap:.5rem;margin:.28rem 0;font-size:.86rem}
.row .nm{color:var(--ink-soft);text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row.me .nm{color:var(--red);font-weight:800}
.bartrack{background:#eef2f7;border-radius:5px;height:18px;position:relative;overflow:hidden}
.bar{height:100%;background:var(--bar);border-radius:5px}
.row.me .bar{background:var(--red)}
.pk{position:absolute;top:-3px;height:24px;width:2px;background:#0f172a;opacity:.55}
.row .val{font-weight:700;color:var(--ink);text-align:left}
.row.me .val{color:var(--red)}
.legend{font-size:.8rem;color:var(--ink-mute);margin:.5rem 0 0;display:flex;gap:1.1rem;flex-wrap:wrap}
.legend span{display:inline-flex;align-items:center;gap:.35rem}
.sw{width:13px;height:13px;border-radius:3px;display:inline-block}
table{width:100%;border-collapse:collapse;font-size:.9rem;background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin:0 0 1rem}
th,td{padding:.55rem .7rem;text-align:left;border-bottom:1px solid #eef2f7}
th{background:#f8fafc;font-size:.74rem;text-transform:uppercase;letter-spacing:.04em;color:var(--ink-mute)}
tr:last-child td{border-bottom:none}
tr.me td{background:var(--red-soft);font-weight:700;color:var(--ink)}
.bottomline{background:#e8f0ff;border:1px solid #aac6f7;border-radius:10px;padding:1.1rem 1.4rem;margin:1.4rem 0}
.bottomline .k{font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#1a4f9b;margin-bottom:.35rem}
.bottomline p{margin:0;color:var(--ink);font-size:1.04rem}
.note{background:var(--gold-soft);border:1px solid var(--gold-line);border-radius:9px;padding:.9rem 1.1rem;margin:1rem 0;font-size:.94rem;color:var(--ink-soft)}
.sources{border-top:1px solid #e2e8f0;margin-top:2.4rem;padding-top:1.1rem;font-size:.84rem;color:var(--ink-mute)}
.footer{text-align:center;padding:1.4rem 0 3rem;color:var(--ink-mute);font-size:.82rem}
@media(max-width:600px){.hero h1{font-size:1.75rem}.row{grid-template-columns:96px 1fr 30px}}
"""


def chart_rows(summ, scale_max):
    out = []
    for s in summ:
        cls = " me" if s["is_iccsd"] else ""
        avg_w = max(2, round(100 * s["avg"] / scale_max))
        pk_l = min(99.0, 100 * s["peak"] / scale_max)
        out.append(
            f'<div class="row{cls}"><div class="nm">{s["district"]}</div>'
            f'<div class="bartrack"><div class="bar" style="width:{avg_w}%"></div>'
            f'<div class="pk" style="left:{pk_l:.1f}%" title="peak {s["peak"]}"></div></div>'
            f'<div class="val">{s["peak"]}</div></div>'
        )
    return "\n".join(out)


def build():
    rows = load_rows()
    write_csv(rows)
    summ = summarize(rows)

    n_dist = len(summ)
    mw_dist = [s for s in summ if s["mw_count"] > 0]
    iccsd = next(s for s in summ if s["is_iccsd"])
    scale_max = max(s["peak"] for s in summ)

    # material-weakness incidence rows (district-years)
    mw_events = []
    for r in rows:
        if r["material_weakness"]:
            mw_events.append((r["district"], r["fiscal_year"], r["findings_count"]))
    mw_events.sort(key=lambda x: (x[0], x[1]))
    mw_table = "\n".join(
        f'<tr class="{"me" if d==ICCSD else ""}"><td>{d}</td><td>FY{fy}</td>'
        f'<td>{c if c is not None else "&mdash;"}</td></tr>'
        for d, fy, c in mw_events
    )

    mw_names = ", ".join(s["district"] for s in sorted(mw_dist, key=lambda x: x["district"]))

    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>How many audit findings is normal? | Iowa large districts</title>
<style>{CSS}</style>
</head><body>
{nav("more")}
<header class="hero"><div class="container">
  <div class="eyebrow">Iowa's 15 largest districts &middot; FY2020&ndash;FY2025</div>
  <h1>How many audit findings is normal?</h1>
  <p class="sub">Iowa City's recent audits drew an unusual number of findings &mdash; including
  material weaknesses. This puts that count in context: every large Iowa district's audit findings,
  side by side, so you can see what's typical and where Iowa City actually stands.</p>
</div></header>

<main class="container">

  <div class="tldr">
    <div class="k">The short version</div>
    <ul>
      <li><span class="ic">&#9888;&#65039;</span><span><strong>A material weakness by itself is not unique.</strong>
        {len(mw_dist)} of the {n_dist} large districts had at least one material-weakness year in
        FY2020&ndash;2025 ({mw_names}). So &ldquo;had a material weakness&rdquo; alone would not make Iowa City an outlier.</span></li>
      <li><span class="ic">&#128201;</span><span><strong>The volume and severity are what stand out.</strong>
        Iowa City's FY2024 audit carried <strong>14 numbered findings, five of them financial-statement
        material weaknesses</strong> &mdash; the heaviest single-year load of any district in any year here.
        The next-worst peak at any peer was {summ[1]['peak']} findings.</span></li>
      <li><span class="ic">&#128681;</span><span><strong>And nothing else combines all of it.</strong>
        Most findings + five material weaknesses in one year + qualified federal opinions + repeat
        uncorrected items + an audit filed about two years late (which cost the district its bond rating).
        No peer district shows that combination.</span></li>
    </ul>
  </div>

  <h2>Findings per district &mdash; peak and typical</h2>
  <p class="section-sub">Each bar is a district's <strong>average</strong> findings per filed audit, FY2020&ndash;2025;
  the black tick marks its <strong>worst single year</strong> (the number at right). Iowa City is shown in red.
  Sorted by worst year.</p>
  <div class="chart">
    {chart_rows(summ, scale_max)}
    <div class="legend">
      <span><span class="sw" style="background:var(--bar)"></span>average findings / year</span>
      <span><span class="sw" style="background:#0f172a;width:3px;height:15px"></span>worst single year</span>
      <span><span class="sw" style="background:var(--red)"></span>Iowa City CSD</span>
    </div>
  </div>
  <p class="section-sub">Iowa City's FY2024 (14) and FY2023 (7) sit at the top; its earlier years (2&ndash;3
  findings) were unremarkable. The jump is recent, not chronic &mdash; which is its own kind of warning sign.</p>

  <h2>Who has had a material weakness</h2>
  <p class="section-sub">The most serious internal-control flag short of a wrong number. Across FY2020&ndash;2025,
  these are the district-years that drew one. {len(mw_dist)} of {n_dist} districts appear at least once;
  Davenport ran a three-year stretch, but only Iowa City's FY2024 stacked five in a single year.</p>
  <table>
    <thead><tr><th>District</th><th>Fiscal year</th><th>Total findings that year</th></tr></thead>
    <tbody>
    {mw_table}
    </tbody>
  </table>
  <p class="section-sub">The table counts material-weakness <em>years</em>. Iowa City's FY2024 is one row here,
  but it contained <strong>five</strong> financial-statement material weaknesses at once (plus three more on
  the federal side) &mdash; a concentration no other district-year in the group approaches.</p>

  <h2>What actually makes Iowa City the outlier</h2>
  <p class="section-sub">Not any single finding, but four things together &mdash; each compared with the peer group:</p>
  <table>
    <thead><tr><th>Measure</th><th>Iowa City</th><th>The other 14 large districts</th></tr></thead>
    <tbody>
      <tr class="me"><td>Most findings in one year</td><td>14 (FY2024)</td><td>Peak {summ[1]['peak']} (Davenport, FY2021); most are 0&ndash;4</td></tr>
      <tr><td>Material weaknesses in one year</td><td>5 (FY2024)</td><td>At most 1&ndash;2 in any year</td></tr>
      <tr><td>Federal program opinion</td><td>Qualified on two programs (FY2024)</td><td>Almost all clean / no single-audit findings</td></tr>
      <tr><td>Audit filed on time</td><td>~2 years late (FY2023 &amp; FY2024); FY2025 still unfiled</td><td>Effectively all on time</td></tr>
      <tr><td>Bond rating</td><td>Withdrawn for late information</td><td>Retained</td></tr>
    </tbody>
  </table>

  <div class="note">
    <strong>Reading this honestly.</strong> If the question is &ldquo;is Iowa City the only large
    district that ever had a material weakness?&rdquo; the answer is <em>no</em> &mdash; {len(mw_dist)} of
    {n_dist} did. The defensible claim is narrower and stronger: <strong>Iowa City's FY2024 is the most
    severe single-year audit result in the large-district group</strong>, and the surrounding pattern
    (late filing, lost rating, repeat findings, federal qualifications) is unmatched by any peer.
  </div>

  <div class="bottomline">
    <div class="k">Bottom line</div>
    <p>Yes &mdash; on the evidence, Iowa City is an outlier among Iowa's large districts, but in
    <em>magnitude and pattern</em>, not in merely having a finding. Five material weaknesses and 14 findings
    in one year, on top of a two-year-late audit and a withdrawn rating, is the worst combination in the group.
    The most credible way to say so is to show the distribution &mdash; which is this page.</p>
  </div>

  <div class="sources">
    Source: each district's audited Financial &amp; Compliance Report (Schedule of Findings and Questioned
    Costs), FY2020&ndash;FY2025, as compiled in <code>data/district-extractions/</code> and
    <code>data/audit-findings-distribution.csv</code>. &ldquo;Findings&rdquo; counts numbered GAGAS,
    federal, and statutory findings. Iowa City FY2024 figures are read directly from its audit report dated
    June 10, 2026 (findings 2024-001 through 2024-014). Iowa City has no FY2025 row; that audit is not yet filed.
    Des&nbsp;Moines Independent CSD is abbreviated &ldquo;Des Moines CSD&rdquo; and College Community as &ldquo;College CSD (Prairie).&rdquo;
  </div>
  <div class="footer">Unofficial community analysis of public audit documents. Not produced by ICCSD or any rating agency.</div>
</main>
</body></html>"""

    with open(OUT_HTML, "w") as fh:
        fh.write(html)

    # console summary
    print(f"districts: {n_dist}  |  with >=1 material-weakness year: {len(mw_dist)} ({mw_names})")
    print(f"ICCSD peak findings: {iccsd['peak']}  avg: {iccsd['avg']:.1f}  MW years: {iccsd['mw_years']}")
    print(f"wrote {os.path.relpath(OUT_CSV, ROOT)}, {os.path.relpath(OUT_CSV_SITE, ROOT)} "
          f"and {os.path.relpath(OUT_HTML, ROOT)}")


if __name__ == "__main__":
    build()
