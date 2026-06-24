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
# published GitHub Pages site. Kept as the machine-readable companion served
# alongside the page (the data baked into the page itself comes from load_rows).
OUT_CSV_SITE = os.path.join(ROOT, "audit-findings-distribution.csv")
OUT_HTML = os.path.join(ROOT, "audit-findings-distribution.html")
# A fully self-contained, single-file copy with the data baked in and the site
# nav removed — meant to be downloaded/emailed and opened directly (no server,
# no CSV, no working links to the rest of the site). Regenerate it on each update.
OUT_STANDALONE = os.path.join(ROOT, "audit-findings-standalone.html")

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
.fedchart .bartrack{overflow:visible}
.ftag{position:absolute;right:.45rem;top:50%;transform:translateY(-50%);font-size:.62rem;font-weight:700;
letter-spacing:.03em;text-transform:uppercase;padding:.1rem .45rem;border-radius:999px;white-space:nowrap;line-height:1.4}
.ftag.fq{background:var(--red-soft);color:var(--red);border:1px solid var(--red-line)}
.ftag.fm{background:var(--gold-soft);color:var(--gold);border:1px solid var(--gold-line)}
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


def load_mw_counts():
    """Validated material-weakness counts per district-year (auditor-stated)."""
    path = os.path.join(ROOT, "data", "material-weakness-counts.csv")
    peak_fin, peak_tot = {}, {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            d = NAME_FIX.get(r["district"].strip(), r["district"].strip())
            fin = int(r["mw_financial"])
            tot = fin + int(r["mw_federal"])
            peak_fin[d] = max(peak_fin.get(d, 0), fin)
            peak_tot[d] = max(peak_tot.get(d, 0), tot)
    return peak_fin, peak_tot


def load_federal():
    """Per-district federal single-audit outcomes, FY2020-2025 (auditor-stated).

    Returns:
      fed_peak: worst-year federal material-weakness count per district
      fed_worst: worst federal outcome rank per district (0 clean .. 3 qualified)
      qualified: list of (district, fy) with a qualified/adverse federal opinion
    """
    path = os.path.join(ROOT, "data", "federal-findings.csv")
    fed_peak, fed_worst, qualified = {}, {}, []
    RANK = {"clean": 0, "finding": 1, "mw": 2, "qualified": 3}
    if not os.path.exists(path):
        return fed_peak, fed_worst, qualified
    for r in csv.DictReader(open(path)):
        d = NAME_FIX.get(r["district"].strip(), r["district"].strip())
        mw = int(r["fed_mw"] or 0)
        op = (r["fed_compliance_opinion"] or "").strip().lower()
        finding = (r["fed_finding"] or "").strip().upper() == "Y"
        fed_peak[d] = max(fed_peak.get(d, 0), mw)
        if op in ("qualified", "adverse", "disclaimer"):
            rank = RANK["qualified"]
            qualified.append((d, int(r["fiscal_year"])))
        elif mw > 0:
            rank = RANK["mw"]
        elif finding:
            rank = RANK["finding"]
        else:
            rank = RANK["clean"]
        fed_worst[d] = max(fed_worst.get(d, 0), rank)
    return fed_peak, fed_worst, qualified


def fed_chart_rows(summ, fed_peak, fed_worst, scale):
    """Bars = worst-year federal material weaknesses; a tag marks the rarer
    'qualified federal opinion' tier. Mirrors the financial MW chart."""
    LABEL = {3: "qualified opinion", 2: "material weakness", 1: "minor finding", 0: "clean"}
    out = []
    for s in sorted(summ, key=lambda x: (-fed_worst.get(x["district"], 0),
                                         -fed_peak.get(x["district"], 0), x["district"])):
        d = s["district"]
        v = fed_peak.get(d, 0)
        rank = fed_worst.get(d, 0)
        cls = " me" if s["is_iccsd"] else ""
        w = max(3, round(100 * v / scale)) if v else 0
        bar = f'<div class="bar" style="width:{w}%"></div>' if v else ""
        tag = ""
        if rank == 3:
            tag = '<span class="ftag fq">qualified opinion</span>'
        elif rank == 1:
            tag = '<span class="ftag fm">minor finding</span>'
        rightval = v if v else ("&mdash;" if rank == 0 else "0")
        out.append(
            f'<div class="row{cls}"><div class="nm">{d}</div>'
            f'<div class="bartrack">{bar}{tag}</div>'
            f'<div class="val">{rightval}</div></div>'
        )
    return "\n".join(out)


def load_prior_persistence():
    """Pooled 'still Not corrected a year later' from the prior-findings schedules."""
    path = os.path.join(ROOT, "data", "prior-findings-status.csv")
    peer_nc = peer_tot = 0
    ic_rows = []
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            if not (r.get("prior_total") or "").strip():
                continue
            t, nc = int(r["prior_total"]), int(r["prior_not_corrected"])
            if r["district"] == ICCSD:
                ic_rows.append((int(r["audit_fy"]), t, nc))
            else:
                peer_nc += nc; peer_tot += t
    peer_pct = round(100 * peer_nc / peer_tot) if peer_tot else 0
    # ICCSD's most recent audit (FY2024) specifically — the headline 6-of-7
    ic_rows.sort()
    ic_tot, ic_nc = (ic_rows[-1][1], ic_rows[-1][2]) if ic_rows else (0, 0)
    return peer_pct, ic_nc, ic_tot


def mw_chart_rows(summ, peak_fin, scale):
    out = []
    for s in sorted(summ, key=lambda x: (-peak_fin.get(x["district"], 0), x["district"])):
        v = peak_fin.get(s["district"], 0)
        cls = " me" if s["is_iccsd"] else ""
        w = max(3, round(100 * v / scale)) if v else 0
        bar = f'<div class="bar" style="width:{w}%"></div>' if v else ""
        out.append(
            f'<div class="row{cls}"><div class="nm">{s["district"]}</div>'
            f'<div class="bartrack">{bar}</div>'
            f'<div class="val">{v}</div></div>'
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

    # severity layer: validated material-weakness counts + finding persistence
    peak_fin, peak_tot = load_mw_counts()
    peer_pct, ic_nc, ic_tot = load_prior_persistence()
    mw_scale = max(peak_fin.values()) if peak_fin else 1
    ic_mw = peak_fin.get(ICCSD, 0)            # 5 financial-statement MWs (FY24)
    ic_mw_tot = peak_tot.get(ICCSD, 0)        # 8 incl. federal
    n_with_mw = sum(1 for s in summ if peak_fin.get(s["district"], 0) > 0)
    n_zero_mw = n_dist - n_with_mw
    # next-highest peer peak (financial MWs)
    peer_peaks = sorted((peak_fin.get(s["district"], 0) for s in summ if not s["is_iccsd"]),
                        reverse=True)
    next_mw = peer_peaks[0] if peer_peaks else 0

    # material-weakness incidence rows (district-years)
    mw_events = []
    for r in rows:
        if r["material_weakness"]:
            mw_events.append((r["district"], r["fiscal_year"], r["findings_count"]))
    mw_events.sort(key=lambda x: (x[0], x[1]))

    # per-year base rate: how ordinary is a clean (no material-weakness) year?
    n_dy = len(rows)
    n_mw_years = len(mw_events)
    n_clean_years = n_dy - n_mw_years
    pct_clean = round(100 * n_clean_years / n_dy) if n_dy else 0

    # federal single-audit outcomes
    fed_peak, fed_worst, qualified = load_federal()
    fed_scale = max(fed_peak.values()) if fed_peak else 1
    ic_fed_mw = fed_peak.get(ICCSD, 0)
    qual_names = sorted({d for d, _ in qualified})
    qual_other = [d for d in qual_names if d != ICCSD]
    n_qual = len(qual_names)
    mw_table = "\n".join(
        f'<tr class="{"me" if d==ICCSD else ""}"><td>{d}</td><td>FY{fy}</td>'
        f'<td>{c if c is not None else "&mdash;"}</td></tr>'
        for d, fy, c in mw_events
    )

    mw_names = ", ".join(s["district"] for s in sorted(mw_dist, key=lambda x: x["district"]))

    navbar = nav("more")
    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>How many audit findings is normal? | Iowa large districts</title>
<style>{CSS}</style>
</head><body>
{navbar}
<header class="hero"><div class="container">
  <div class="eyebrow">Iowa's 15 largest districts &middot; FY2020&ndash;FY2025</div>
  <h1>How many audit findings is normal?</h1>
  <p class="sub">Iowa City's recent audits drew an unusual number of findings &mdash; including several
  &ldquo;material weaknesses,&rdquo; an auditor's most serious red flag about how a district controls its
  money. This puts that in context: every large Iowa district, side by side, so you can see what's typical
  and where Iowa City actually stands.</p>
</div></header>

<main class="container">

  <div class="tldr">
    <div class="k">The short version</div>
    <ul>
      <li><span class="ic">&#9888;&#65039;</span><span><strong>A material weakness is serious &mdash; it's just
        not unique to Iowa City.</strong> Think of it like failing a class: not rare enough to be shocking, but
        never a good sign. In <strong>{pct_clean}% of the district-years here ({n_clean_years} of {n_dy}) the
        auditor found none</strong>, and only {len(mw_dist)} of the {n_dist} large districts drew even one
        material-weakness year in FY2020&ndash;2025 ({mw_names}). Iowa City is one of them &mdash; so a material
        weakness <em>by itself</em> wouldn't make it an outlier. What follows is why it is.</span></li>
      <li><span class="ic">&#128201;</span><span><strong>The severity is what stands out.</strong>
        Iowa City's FY2024 audit carried <strong>five financial-statement material weaknesses at once</strong>
        &mdash; the heaviest single-year load of any district in any year here. The most any peer ever showed in
        one year was two.</span></li>
      <li><span class="ic">&#127968;</span><span><strong>On the federal side, it is nearly alone.</strong>
        When an auditor reviews how federal money was spent, it issues an opinion on compliance. A
        <em>qualified</em> opinion &mdash; the auditor saying the district did <em>not</em> follow the rules in all
        material respects &mdash; is rare: across {n_dist} districts and six years, only
        <strong>{n_qual}</strong> ever received one ({", ".join(qual_names)}). Iowa City's FY2024 was qualified on
        <strong>two</strong> program clusters at once, with three federal material weaknesses on top.</span></li>
      <li><span class="ic">&#128681;</span><span><strong>And nothing else combines all of it.</strong>
        Most findings + five material weaknesses in one year + qualified federal opinions + repeat
        uncorrected items + an audit filed about two years late (which cost the district its bond rating).
        No peer district shows that combination.</span></li>
    </ul>
  </div>

  <h2>Material weaknesses by district &mdash; worst single year</h2>
  <div class="tldr" style="border-left-color:var(--gold)">
    <div class="k" style="color:var(--gold)">What's a &ldquo;material weakness&rdquo;?</div>
    <p style="margin:0">It's an auditor's most serious warning short of finding an actual wrong number.
    It means the checks a district relies on to catch a big mistake &mdash; or theft &mdash; in its own
    books are broken badly enough that one could slip through unnoticed. The books may still be right;
    the <em>safeguards</em> around them are not.</p>
  </div>
  <p class="section-sub">Below is how many material weaknesses an auditor found in each district's
  <strong>financial statements</strong> in its worst single year, FY2020&ndash;2025. {n_zero_mw} of the
  {n_dist} large districts never had a single one. Iowa City in red.</p>
  <div class="chart">
    {mw_chart_rows(summ, peak_fin, mw_scale)}
    <div class="legend">
      <span><span class="sw" style="background:var(--bar)"></span>material weaknesses (worst year)</span>
      <span><span class="sw" style="background:var(--red)"></span>Iowa City CSD</span>
    </div>
  </div>
  <p class="section-sub">Iowa City's FY2024 had <strong>{ic_mw} material weaknesses in its financial
  statements at once</strong> (and {ic_mw_tot} including its federal programs) &mdash; more than double the
  next-highest the group has ever shown ({next_mw}, Davenport in FY2020). This is the chart where Iowa City
  is genuinely an outlier: not that it has <em>a</em> material weakness, but <em>how many at once</em>.</p>

  <h2>What is a &ldquo;federal finding&rdquo;?</h2>
  <div class="tldr" style="border-left-color:var(--gold)">
    <div class="k" style="color:var(--gold)">The federal audit, in plain English</div>
    <p style="margin:0 0 .6em">Any district that spends enough federal money in a year (think Title I, special
    education/IDEA, school nutrition, and the COVID-era ESSER funds) gets a second, separate audit called a
    <strong>Single Audit</strong>, run under federal rules (the Uniform Guidance). It asks a different question
    than the regular audit: not &ldquo;are the books right?&rdquo; but <strong>&ldquo;did the district follow the
    rules that come attached to the federal dollars?&rdquo;</strong></p>
    <p style="margin:0">The auditor then issues an <strong>opinion on compliance</strong> for each major federal
    program. &ldquo;Unmodified&rdquo; is the clean result. A <strong>&ldquo;qualified&rdquo;</strong> opinion is
    the auditor formally stating the district did <em>not</em> comply, in some material way, with the federal
    requirements &mdash; and it can come with &ldquo;questioned costs,&rdquo; dollars the auditor flags as
    possibly spent improperly. A qualified opinion is the federal equivalent of the material-weakness warning above.</p>
  </div>
  <p class="section-sub">Below is each district's <strong>worst federal result</strong>, FY2020&ndash;2025. Most
  have a Single Audit every year and sail through clean. A handful drew a minor federal finding but kept a clean
  opinion. Only <strong>two</strong> districts ever drew a <strong>qualified opinion</strong> &mdash; and Iowa City
  is one. Bars show federal material weaknesses in the district's worst year; Iowa City in red.</p>
  <div class="chart fedchart">
    {fed_chart_rows(summ, fed_peak, fed_worst, fed_scale)}
    <div class="legend">
      <span><span class="sw" style="background:var(--bar)"></span>federal material weaknesses (worst year)</span>
      <span><span class="ftag fq" style="position:static">qualified opinion</span></span>
      <span><span class="ftag fm" style="position:static">minor finding</span></span>
      <span><span class="sw" style="background:var(--red)"></span>Iowa City CSD</span>
    </div>
  </div>
  <p class="section-sub">The two qualified opinions tell the whole story of how rare this is: {", ".join(qual_names)}.
  Both were on the COVID-era Education Stabilization (ESSER) funds. Iowa City's FY2024 went further than any peer
  year &mdash; qualified on two program clusters at once and carrying <strong>{ic_fed_mw} federal material
  weaknesses</strong> &mdash; and, unlike Davenport's, it has not yet been worked back to clean.</p>

  <h2>The significant issues, in plain English</h2>
  <p class="section-sub">The two charts above show <em>where</em> Iowa City stands out. This is <em>what</em> those
  findings actually were &mdash; translated out of audit language. All are from the district's FY2024 audit
  (findings 2024-001 through 2024-014).</p>
  <div class="tldr">
    <div class="k">What the auditor actually found</div>
    <ul>
      <li><span class="ic">&#127974;</span><span><strong>The bank accounts weren't being reconciled.</strong>
        Reconciling a bank account is critical because it is the one routine check that proves the district's own
        records match the money the bank actually holds &mdash; it's how missing, duplicated, or stolen funds get
        caught early. For FY2024 those reconciliations weren't done on time, so that check simply wasn't
        happening. In the auditor's words, errors or &ldquo;misappropriations of assets&rdquo; could occur and go
        undetected. (A repeat finding; the stated cause was turnover in key accounting staff.)</span></li>
      <li><span class="ic">&#128202;</span><span><strong>The year-end statements were materially wrong as first
        prepared.</strong> Receivables, payables, and capital assets weren't properly adjusted, so the financial
        statements were misstated and needed material corrections caught during the audit &mdash; not by the
        district's own process. (Also a repeat finding.)</span></li>
      <li><span class="ic">&#128100;</span><span><strong>One person could run an entire money cycle.</strong>
        The district lacked segregation of duties over payroll, cash disbursements, and school receipts &mdash;
        the basic separation that keeps a single error or theft from slipping through unnoticed.</span></li>
      <li><span class="ic">&#127970;</span><span><strong>Federal COVID money went to unallowable costs &mdash;
        and records were missing.</strong> The district charged the ESSER program for costs that weren't allowed,
        and for one program couldn't produce the expenditure records at all. These are the findings behind the
        qualified federal opinion above.</span></li>
      <li><span class="ic">&#9203;</span><span><strong>The audit was about two years late &mdash; and it cost the
        bond rating.</strong> The district didn't complete its FY2023 and FY2024 single audits within the required
        nine months. The delay left lenders and the public without current numbers, and the district's bond
        rating was withdrawn.</span></li>
      <li><span class="ic">&#128184;</span><span><strong>Smaller, but telling.</strong> A student activity fund
        ran a deficit, and money was moved between funds without the formal authorization the rules
        require.</span></li>
    </ul>
  </div>

  <h2>Case study: how Davenport climbed out</h2>
  <p class="section-sub">Davenport is the one large district that has been somewhere like where Iowa City is now
  &mdash; and worked its way back. It had material weaknesses <strong>three years running</strong> and a qualified
  federal opinion, then drove its findings to <strong>zero</strong>. The arc is worth studying because the
  weaknesses were strikingly similar to Iowa City's.</p>
  <table>
    <thead><tr><th>Fiscal year</th><th>Financial MWs</th><th>Federal MWs</th><th>Federal opinion</th><th>Total findings</th></tr></thead>
    <tbody>
      <tr><td>FY2020</td><td>2</td><td>1</td><td>Unmodified</td><td>6</td></tr>
      <tr><td>FY2021</td><td>1</td><td>1</td><td><strong>Qualified</strong> (ESSER)</td><td>8</td></tr>
      <tr><td>FY2022</td><td>1</td><td>0</td><td>Unmodified</td><td>7</td></tr>
      <tr><td>FY2023</td><td>0</td><td>0</td><td>Unmodified</td><td>3</td></tr>
      <tr><td>FY2024</td><td>0</td><td>0</td><td>Unmodified</td><td>2</td></tr>
      <tr><td>FY2025</td><td>0</td><td>0</td><td>Unmodified</td><td><strong>0</strong></td></tr>
    </tbody>
  </table>
  <div class="tldr">
    <div class="k">What the weaknesses were &mdash; and how they fixed them</div>
    <ul>
      <li><span class="ic">&#128269;</span><span><strong>Year-end close (2020-001).</strong> The audit turned up
        material corrections in capital assets, accrued liabilities, and accounts payable that Davenport's own
        controls would never have caught &mdash; &ldquo;inadequate reconciliation and internal review.&rdquo;
        <em>Fix:</em> they built reconciliation and review procedures over the balance-sheet accounts.</span></li>
      <li><span class="ic">&#127963;&#65039;</span><span><strong>Federal reporting (2020-002).</strong> Their
        Schedule of Expenditures of Federal Awards was misstated by <strong>$1.84 million</strong> &mdash; it
        didn't reconcile to the books, mostly mis-coded ESSER money. <em>Fix:</em> reconcile the schedule to the
        general ledger with a separate Finance review before anything is certified to the state.</span></li>
      <li><span class="ic">&#128176;</span><span><strong>Payroll charged to federal funds (2020-005, the federal
        material weakness).</strong> Timesheets weren't being approved before payroll ran, and the time-clock
        didn't talk to the general ledger. <em>Fix:</em> require supervisory approval of time and move toward
        integrated, batch-processed payroll.</span></li>
    </ul>
  </div>
  <p class="section-sub">Those are nearly the same failure points in Iowa City's FY2024 report: year-end close,
  federal-award reporting and allowable costs, and payroll controls. Davenport shows the climb is doable &mdash;
  findings dropped and downgraded every single year (material weakness &rarr; significant deficiency &rarr;
  resolved) on the back of assigned ownership and review-before-certify discipline, not a single dramatic move.</p>
  <div class="note" style="background:var(--red-soft);border-color:var(--red-line)">
    <strong>The pressure behind the turnaround.</strong> Davenport's recovery didn't happen by choice alone.
    From 2019 to 2022 the district was under <strong>conditional accreditation</strong> &mdash; the state's most
    serious sanction short of pulling accreditation &mdash; and in September 2020, after Davenport missed its
    corrective-action plan, the Iowa State Board of Education took the unprecedented step of <strong>temporarily
    replacing its superintendent and chief financial officer</strong>. That case was driven mostly by special
    education and equity, not the audit &mdash; but years of overspending the district's budget authority (a
    roughly $12&nbsp;million deficit) were part of it, and the financial cleanup visible in these audits tracks
    with that state-installed leadership. The lesson cuts both ways for Iowa City: unaddressed financial problems
    can escalate until the state steps in &mdash; and Davenport's fix came under heavy outside pressure, not
    purely on its own.
  </div>
  <div class="note">
    <strong>The honest caveat.</strong> Davenport is a fair role model, not a perfect mirror. Even its
    <em>worst</em> year (FY2020: three material weaknesses) was milder than Iowa City's FY2024 (eight, five of
    them financial). Iowa City is starting from a deeper hole &mdash; so Davenport's roughly four-year climb is a
    floor on the effort, not a ceiling.</p>
  </div>

  <h2>What actually makes Iowa City the outlier</h2>
  <p class="section-sub">Not any single finding, but four things together &mdash; each compared with the peer group:</p>
  <table>
    <thead><tr><th>Measure</th><th>Iowa City</th><th>The other 14 large districts</th></tr></thead>
    <tbody>
      <tr class="me"><td>Material weaknesses in one year</td><td>5 (FY2024)</td><td>At most 1&ndash;2 in any year</td></tr>
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

    # Standalone single file: same baked-in content, just no site nav (so there
    # are no dead links when it's opened on its own).
    standalone = html.replace(navbar, "<!-- standalone build: site nav removed -->")
    with open(OUT_STANDALONE, "w") as fh:
        fh.write(standalone)

    # console summary
    print(f"districts: {n_dist}  |  with >=1 material-weakness year: {len(mw_dist)} ({mw_names})")
    print(f"ICCSD peak findings: {iccsd['peak']}  avg: {iccsd['avg']:.1f}  MW years: {iccsd['mw_years']}")
    print(f"wrote {os.path.relpath(OUT_CSV, ROOT)}, {os.path.relpath(OUT_CSV_SITE, ROOT)}, "
          f"{os.path.relpath(OUT_HTML, ROOT)} and {os.path.relpath(OUT_STANDALONE, ROOT)}")


if __name__ == "__main__":
    build()
