"""
07_build_report.py  -- a single, self-contained HTML report for a general
audience (reporters / community members). Plain language + real terminology.
Charts are embedded as base64 so the file is fully portable and is NOT linked
into the public site.
Writes: output/liquidity-stress-report.html
"""
import base64
import html
import pandas as pd

import common as C

RECENT = C.COMMON_RECENT_FY
RISK_BG = {
    "Very high risk": "#f4cccc", "High risk": "#fce5cd",
    "Moderate risk": "#fff2cc", "Low risk": "#d9ead3",
    "Unscored (insufficient component data)": "#eeeeee",
}


def b64(path):
    return base64.b64encode(path.read_bytes()).decode()


def pct(x, d=1):
    return "n/a" if pd.isna(x) else f"{x*100:.{d}f}%"


def days(x):
    return "n/a" if pd.isna(x) else f"{x:.0f}"


def money(x):
    return "n/a" if pd.isna(x) else f"${x:,.0f}"


def short(n):
    return (n.replace(" CSD", "").replace(" Community", "").replace(" Independent", "")
            .replace(" (Prairie)", ""))


def fig(chart_file, caption):
    data = b64(C.CHARTS_DIR / chart_file)
    return (f'<figure><img class="chart" alt="{html.escape(caption)}" '
            f'src="data:image/png;base64,{data}">'
            f'<figcaption>{caption}</figcaption></figure>')


def risk_badge(cls):
    bg = RISK_BG.get(cls, "#eee")
    return f'<span class="badge" style="background:{bg}">{html.escape(cls)}</span>'


def main():
    m = pd.read_csv(C.MASTER_CSV)
    f = pd.read_csv(C.FOCUS_CSV)
    t1 = pd.read_csv(C.TABLES_DIR / "table1_recent_screen.csv")
    t3 = pd.read_csv(C.TABLES_DIR / "table3_numerator_sensitivity.csv")
    t5 = pd.read_csv(C.TABLES_DIR / "table5_fy2025_audited_peers.csv")
    iccash = pd.read_csv(C.OUTPUT_DIR / "iccsd_recent_cash.csv")
    supp = pd.read_csv(C.ICCSD_CASH_SUPP_CSV)

    ic24 = m[(m.district_code == 3141) & (m.fiscal_year == RECENT)].iloc[0]
    ic_aud = f[f.district_code == 3141].sort_values("fiscal_year")
    ic23 = ic_aud[ic_aud.fiscal_year == 2023].iloc[0]
    cur = m[(m.fiscal_year == RECENT) & m.practical_days_cushion.notna()]
    ic_pctile = (cur.practical_days_cushion < ic24.practical_days_cushion).mean()
    n_state = len(cur)
    t1s = t1.sort_values("Practical days cushion").reset_index(drop=True)
    ic_rank = int(t1s.index[t1s.District == "Iowa City CSD"][0]) + 1
    ic_t3 = t3[t3.District.str.startswith("Iowa City")]
    cr_t3 = t3[t3.District.str.startswith("Cedar Rapids")]
    q25 = cur.practical_days_cushion.quantile(0.25)

    # ---- Table 1 HTML ----
    t1_rows = ""
    for _, r in t1s.iterrows():
        nm = r["District"]
        hl = ' class="me"' if nm == "Iowa City CSD" else ""
        t1_rows += (
            f"<tr{hl}><td>{html.escape(short(nm))}</td>"
            f"<td>{pct(r['GF unassigned / GF exp.'])}</td>"
            f"<td>{pct(r['GF (assigned+unassigned) / GF exp.'])}</td>"
            f"<td><b>{days(r['Practical days cushion'])}</b></td>"
            f"<td>{days(r['GF cash days'])}</td>"
            f"<td>{pct(r['Cash reserve levy / GF exp.'])}</td>"
            f"<td>{pct(r['UAB / GF exp.'])}</td>"
            f"<td>{risk_badge(r['Risk class'])}</td></tr>")

    # ---- numerator sensitivity table ----
    sens_rows = ""
    for _, ri in ic_t3.iterrows():
        rc = cr_t3[cr_t3["Numerator case"] == ri["Numerator case"]].iloc[0]
        sens_rows += (f"<tr><td>{html.escape(ri['Numerator case'])}</td>"
                      f"<td><b>{ri['Approx. days cushion']:.0f} days</b></td>"
                      f"<td>{rc['Approx. days cushion']:.0f} days</td></tr>")

    # ---- ICCSD trend table ----
    tr_rows = ""
    for _, r in ic_aud.iterrows():
        tr_rows += (f"<tr><td>FY{int(r.fiscal_year)}</td><td>{money(r.gf_expenditure)}</td>"
                    f"<td>{money(r.gf_unassigned)}</td><td><b>{days(r.practical_days_cushion)}</b></td>"
                    f"<td>{pct(r.uab_cushion)}</td><td>{risk_badge(r.risk_class)}</td></tr>")
    tr_rows += (f'<tr class="me"><td>FY{RECENT} *</td><td>{money(ic24.gf_expenditures)}</td>'
                f"<td>{money(ic24.gf_unassigned)}</td><td><b>{days(ic24.practical_days_cushion)}</b></td>"
                f"<td>{pct(ic24.uab_cushion)}</td><td>{risk_badge(ic24.risk_class)}</td></tr>")

    supp_txt = "; ".join(
        f"FY{int(r.fiscal_year)} ≈ {money(r.gf_cash_investments)} ({html.escape(str(r.status))})"
        for _, r in supp.iterrows())

    # FY2025 audited-peer view
    t5s = t5.sort_values("Practical days cushion").reset_index(drop=True)
    fy25_rows = ""
    for _, r in t5s.iterrows():
        neg = r["Practical days cushion"] < 0
        style = ' style="color:#b91c1c;font-weight:700"' if neg else ""
        fy25_rows += (
            f"<tr><td>{html.escape(short(r['District']))}</td>"
            f"<td>{pct(r['GF unassigned / GF exp.'])}</td>"
            f"<td{style}><b>{days(r['Practical days cushion'])}</b></td>"
            f"<td>{days(r['GF cash days'])}</td>"
            f"<td>{pct(r['Operating result'])}</td>"
            f"<td>{pct(r['UAB / GF exp.'])}</td>"
            f"<td>{risk_badge(r['Risk class'])}</td></tr>")
    wtr = t5s.iloc[0]
    ic25 = iccash[iccash.fiscal_year == 2025].iloc[0]
    ic26 = iccash[iccash.fiscal_year == 2026].iloc[0]

    # ICCSD management/board disclosures (unaudited)
    borrow = pd.read_csv(C.INPUTS_DIR / "iccsd_short_term_borrowing.csv")
    mcash = pd.read_csv(C.INPUTS_DIR / "iccsd_management_cash_projection.csv")
    STATUS_BG = {"executed": "#f4cccc", "proposed": "#fce5cd", "projected": "#fff2cc"}
    borrow_rows = ""
    for _, r in borrow.iterrows():
        ctx = f" — {html.escape(str(r.gf_cash_context))}" if pd.notna(r.gf_cash_context) else ""
        bg = STATUS_BG.get(r.status, "#eee")
        borrow_rows += (
            f"<tr><td>{html.escape(str(r.period))}</td>"
            f"<td>{html.escape(str(r.instrument))}</td>"
            f'<td><span class="badge" style="background:{bg}">{html.escape(str(r.status))}</span></td>'
            f"<td>{money(r.amount_usd)}</td>"
            f"<td style='text-align:left'>{html.escape(str(r.purpose))}{ctx}</td></tr>")
    mcash_txt = " → ".join(f"{r.days_cash_on_hand:.1f} (FY{int(r.fiscal_year)})"
                           for _, r in mcash.iterrows())

    css = """
:root{--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--blue:#2563eb;--red:#dc2626}
*{box-sizing:border-box}
body{font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#f1f5f9}
.wrap{max-width:920px;margin:0 auto;padding:34px 20px 80px}
h1{font-size:32px;margin:0 0 8px;line-height:1.15}
.sub{color:var(--mut);margin:0 0 22px;font-size:16px}
h2{font-size:23px;margin:34px 0 6px}
.intro{background:#fff;border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:10px;padding:18px 22px;margin-bottom:20px}
.intro p{margin:8px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 24px;margin-bottom:20px;box-shadow:0 1px 2px rgba(0,0,0,.04);overflow-x:auto}
.plain{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:10px 0;font-size:15px;color:#334155}
.plain b{color:#0f172a}
.take{margin:14px 0 0;font-size:16px;background:#fef2f2;border-left:4px solid var(--red);border-radius:6px;padding:12px 16px;color:#1f2937}
.take b{color:#0f172a}
.caution{margin:14px 0 0;font-size:15px;background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;border-radius:8px;padding:12px 16px;color:#3f3f46}
.caution b{color:#92400e}
.good{background:#f0fdf4;border-left-color:#16a34a}.good b{color:#166534}
table{border-collapse:collapse;width:100%;font-size:14px;margin:10px 0}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}
thead th{background:#1f4e79;color:#fff;font-weight:600;position:sticky;top:0}
tr.me{background:#fff7ed;font-weight:600}
tr.me td{border-bottom:1px solid #fdba74}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;color:#1f2937}
.chart{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:10px}
figure{margin:12px 0}
figcaption{font-size:13px;color:var(--mut);margin-top:8px}
.kpis{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0}
.kpi{flex:1;min-width:150px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi .n{font-size:26px;font-weight:800;color:var(--red)}
.kpi .l{font-size:13px;color:var(--mut);margin-top:2px}
dl{margin:6px 0}dt{font-weight:700;margin-top:10px}dd{margin:2px 0 0;color:#334155;font-size:15px}
footer{color:var(--mut);font-size:13px;margin-top:34px;border-top:1px solid var(--line);padding-top:16px}
.tag{display:inline-block;background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;border-radius:999px;padding:3px 12px;font-size:12.5px;font-weight:700;margin-bottom:10px}
"""

    H = []
    A = H.append
    A(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Iowa City schools: how thin is the financial cushion?</title>
<style>{css}</style></head><body><div class="wrap">""")

    A('<span class="tag">Independent analysis · standalone report</span>')
    A("<h1>How thin is Iowa City schools' financial cushion — and how does it compare?</h1>")
    A(f'<p class="sub">A statewide screen of Iowa school districts’ operating liquidity, '
      f'built only from official state filings and audited reports · June 2026</p>')

    A('<div class="intro">')
    A("<p><b>The question in plain terms:</b> if money stopped coming in for a while, how long could "
      "a school district keep paying its bills — payroll, benefits, vendors — out of its flexible "
      "savings? Schools collect most of their money in big lumps (property taxes, state aid) at "
      "certain times of year but spend steadily every month, so a thin cushion can mean a cash "
      "squeeze between those inflows.</p>")
    A("<p><b>What we did:</b> we measured every Iowa district the same way, using the same state "
      f"data sources, for the most recent comparable year (FY{RECENT}), and went deeper on the 15 "
      "largest districts back to FY2020. <b>The short answer for Iowa City:</b> it keeps one of the "
      "thinnest operating cushions of any large Iowa district, and — separately — the "
      "least <i>spending room</i> under Iowa’s budget-authority rules of any of its big peers.</p>")
    A('<p style="font-size:14px;color:#64748b;margin-bottom:0"><b>Important:</b> this is an '
      "<i>early-warning screen</i> built from year-end numbers. It shows which districts look "
      "stretched on paper. For most districts it does <b>not</b> prove they actually ran short of "
      "cash during the year — confirming that needs month-by-month records. <b>Iowa City is the one "
      "case where that confirming evidence now exists</b>, from the district’s own management "
      "(section 6).</p>")
    A("</div>")

    # KPI strip
    A('<div class="kpis">')
    A(f'<div class="kpi"><div class="n">{days(ic24.practical_days_cushion)} days</div>'
      f'<div class="l">Iowa City’s practical operating cushion, FY{RECENT} '
      f'(#{ic_rank} thinnest of {len(t1s)} large peers)</div></div>')
    A(f'<div class="kpi"><div class="n">{pct(ic24.uab_cushion)}</div>'
      f'<div class="l">Iowa City’s leftover spending authority (UAB) — lowest of any large peer</div></div>')
    A(f'<div class="kpi"><div class="n">{days(ic23.practical_days_cushion)} days</div>'
      f'<div class="l">Cushion in FY2023, its tightest recent year (spending authority went negative)</div></div>')
    A(f'<div class="kpi"><div class="n">≈{ic25.gf_cash_days:.0f} days</div>'
      f'<div class="l">Cash on hand at the <i>start</i> of FY2026, by the district’s own board figures '
      "(the seasonal low point)</div></div>")
    A("</div>")

    # Glossary
    A('<div class="card"><h2>The terms, in plain language</h2>')
    A("<dl>")
    A("<dt>General Fund</dt><dd>The district’s main operating checkbook — salaries, "
      "benefits, and day-to-day costs. Most of this analysis is about this fund.</dd>")
    A("<dt>Fund balance (reserves)</dt><dd>Money left over at the end of the year — the "
      "district’s savings. It comes in layers: <b>unassigned</b> (truly flexible, "
      "rainy-day money), <b>assigned</b> (softly earmarked but still district-controlled), and "
      "restricted/nonspendable layers that aren’t freely usable.</dd>")
    A("<dt>Practical days cushion <span style='font-weight:400;color:#64748b'>(our main measure)</span></dt>"
      "<dd>The flexible savings (assigned + unassigned) divided by a year of spending, turned into "
      "days. “30 days” means the district could cover about a month of operations from "
      "that cushion. Rough rule of thumb used here: under 20 days is high stress, 45–75 days is "
      "comfortable, 75+ is very comfortable.</dd>")
    A("<dt>Spending authority / Unspent Authorized Budget (UAB)</dt><dd>An Iowa-specific legal "
      "ceiling on how much a district is <i>allowed</i> to spend — separate from how much cash "
      "it has. A district can have cash but run out of legal authority to spend it. If UAB goes "
      "<b>negative</b>, the state’s School Budget Review Committee (SBRC) gets involved.</dd>")
    A("<dt>Cash reserve levy</dt><dd>A property-tax tool districts use to refill the operating "
      "cushion. “Near capacity” means a district is already levying close to the most the "
      "state lets it — so it has little room left to tax its way back to a healthier cushion.</dd>")
    A("<dt>Cash days</dt><dd>Actual cash on hand divided by daily spending. Useful, but year-end "
      "cash is seasonally high (right after tax/aid inflows), so it can <i>overstate</i> the "
      "tightest point of the year.</dd>")
    A("</dl></div>")

    # Headline / peer bar
    A('<div class="card"><h2>1. The headline: Iowa City keeps one of the thinnest cushions</h2>')
    A('<p class="plain"><b>How to read this:</b> each bar is a large district. Longer is safer. '
      "The dashed lines mark the rough stress thresholds (10, 20, 45, 75 days).</p>")
    A(fig("2_bar_practical_days.png",
          f"Practical operating days cushion by district, FY{RECENT}. Iowa City is near the bottom."))
    A(f'<div class="take"><b>Takeaway:</b> In FY{RECENT}, Iowa City’s practical cushion was '
      f'about <b>{days(ic24.practical_days_cushion)} days</b> — the {ic_rank}rd-thinnest of the '
      f'{len(t1s)} large districts, behind only Waterloo and Linn-Mar, and roughly the '
      f'{int(round(ic_pctile*100))}th percentile among the ~{n_state} Iowa districts we could score '
      "statewide. Cedar Rapids, by contrast, sits around 60 days.</div>")
    A("</div>")

    # Two different problems / scatter
    A('<div class="card"><h2>2. Two different problems: thin savings <i>and</i> little spending room</h2>')
    A('<p class="plain">Liquidity has two faces. One is <b>cash/reserves</b> (do you have the '
      "money?). The other is <b>spending authority</b> (are you legally allowed to spend it?). "
      "Iowa City screens poorly on both at once — which is unusual.</p>")
    A(fig("1_scatter_cushion_vs_uab.png",
          "Every grey dot is an Iowa district (FY2024). Bigger bubbles are bigger districts. "
          "Iowa City sits in the bottom-left corner: low cushion (left) and almost no leftover "
          "spending authority (bottom)."))
    A(f'<div class="take"><b>Takeaway:</b> Iowa City’s leftover spending authority (UAB) was '
      f'about <b>{pct(ic24.uab_cushion)}</b> of its spending in FY{RECENT} — the <b>lowest of '
      "any large peer</b> (others run roughly 10–45%). In FY2023 it was actually "
      f'<b>negative ({pct(ic23.uab_cushion)})</b>, the level that triggers state review. So even when '
      "cash looks okay, Iowa City has had the least legal room to maneuver.</div>")
    A("</div>")

    # Full peer table
    A(f'<div class="card"><h2>3. The full large-district scorecard (FY{RECENT})</h2>')
    A('<p class="plain">Sorted thinnest cushion first. “Cash days” is year-end and tends '
      "to look generous; the cushion and spending-authority columns are the more telling ones.</p>")
    A("<table><thead><tr><th>District</th><th>Unassigned / spending</th>"
      "<th>Flexible savings / spending</th><th>Practical days cushion</th><th>Cash days</th>"
      "<th>Cash reserve levy / spending</th><th>Spending room (UAB)</th><th>Screen result</th>"
      f"</tr></thead><tbody>{t1_rows}</tbody></table>")
    A('<p style="font-size:13px;color:#64748b">“Screen result” combines the cushion band '
      "with additional warning flags (operating deficits, multi-year drawdowns, low/negative spending "
      "authority, cash-reserve-levy near its cap, enrollment decline). It is an apparent-risk label, "
      "not a verdict.</p>")
    A("</div>")

    # Trend
    A('<div class="card"><h2>4. How Iowa City got here (FY2020–FY2024)</h2>')
    A(fig("3_trend_practical_days.png",
          "Practical days cushion over time. Iowa City (bold) has run at or below the stress "
          "thresholds for most of the period; its FY2024 figure comes from the state CAR because "
          "its FY2024 audit has not been filed."))
    A("<table><thead><tr><th>Year</th><th>General Fund spending</th><th>Unassigned reserves</th>"
      "<th>Practical days cushion</th><th>Spending room (UAB)</th><th>Screen result</th>"
      f"</tr></thead><tbody>{tr_rows}</tbody></table>")
    A('<p style="font-size:13px;color:#64748b">* FY2024 from the state Certified Annual Report '
      "(CAR); Iowa City’s FY2024 and FY2025 independent audits had not been filed at the time "
      "of writing, which is itself a transparency concern.</p>")
    A('<div class="take"><b>Takeaway:</b> The cushion fell into the <b>high-stress range '
      "(about 9–11 days) in FY2022 and FY2023</b>, recovered toward ~27 days in FY2024, but "
      "remains thin by peer and rule-of-thumb standards — and the cash reserve levy is already "
      "near its cap, leaving little room to rebuild reserves through taxes.</div>")
    A("</div>")

    # FY2025 audited-peer view + ICCSD board cash
    A('<div class="card"><h2>5. The newest year on the books (FY2025) — audited peers</h2>')
    A('<p class="plain"><b>Why this is a separate table:</b> the statewide state files (CAR and the '
      "cash-reserve-levy data) only run through FY2024, so FY2025 can’t be a statewide screen yet. "
      "But the large districts’ <b>audited</b> FY2025 reports are in — so here is the latest "
      "apples-to-apples picture for the big districts. <b>Iowa City is absent because its FY2024 and "
      "FY2025 audits still aren’t filed.</b></p>")
    A("<table><thead><tr><th>District</th><th>Unassigned / spending</th>"
      "<th>Practical days cushion</th><th>Cash days</th><th>Operating result</th>"
      "<th>Spending room (UAB)</th><th>Screen result</th>"
      f"</tr></thead><tbody>{fy25_rows}</tbody></table>")
    A('<p style="font-size:13px;color:#64748b">Iowa City’s cushion and operating-result cells are '
      "blank because its FY2025 audit isn’t filed; its UAB is the state’s audit-independent figure "
      "and its cash-days is a <b>start-of-year</b> number (≈ the seasonal low), <i>not</i> directly "
      "comparable to the other districts’ June-30 year-end cash days. Cash days here are year-end and "
      "look generous for everyone — the cushion and UAB columns are the more telling ones.</p>")
    A(f'<div class="take"><b>New this year:</b> <b>{html.escape(short(wtr["District"]))}</b> ran its '
      "flexible reserves <b>negative</b> in FY2025 "
      f"({days(wtr['Practical days cushion'])} days — it spent more than it took in and drew the "
      "unassigned balance below zero), the clearest single-district deterioration in the set. "
      "Several others (College Community, Johnston, Burlington) tightened into the 20–30 day range. "
      "Cedar Rapids held around 47 days.</div>")
    A('<div class="caution"><b>What Iowa City’s own numbers add.</b> Even without a filed audit, the '
      "district’s board materials give cash and spending. Those imply about "
      f"<b>{ic25.gf_cash_days:.0f} days of cash at the start of FY2026</b> "
      f"({money(ic25.gf_cash_investments)} on ~{money(ic25.gf_expenditures)} of spending) and about "
      f"<b>{ic26.gf_cash_days:.0f} days</b> projected for FY2026 "
      f"({money(ic26.gf_cash_investments)} on ~{money(ic26.gf_expenditures)}). Crucially, a "
      "start-of-year figure lands near the <i>seasonal low point</i> of cash — so unlike a tidy "
      "June-30 audit number, ~33–35 days is close to the tightest the district gets. That "
      "<b>corroborates</b> the thin-cushion screen with the kind of intra-year evidence the annual "
      "data alone can’t provide. And the state’s own (audit-independent) FY2025 figure puts Iowa "
      f"City’s leftover spending authority at about <b>{pct(ic25.uab_cushion)}</b> — again the "
      "lowest of the 15. <i>(Board cash figures are unaudited/projected; a filed FY25 audit would "
      "still be needed to compute its FY25 reserve cushion here.)</i></div>")
    A("</div>")

    # ICCSD management disclosures -- the one place we move past "apparent"
    A('<div class="card"><h2>6. The strongest evidence: Iowa City’s own management</h2>')
    A('<p class="plain">Everything above is a <i>screen</i> built from year-end numbers. For Iowa '
      "City there is something more direct: its own administration has told the school board, in "
      "writing, that the district is borrowing short-term to make payroll and bond payments. This is "
      "the kind of evidence — short-term borrowing plus direct management disclosure — that lets us "
      "say liquidity stress is <b>actually happening</b>, not just <i>apparent</i> on paper.</p>")
    A(fig("7_iccsd_management_cash_projection.png",
          "Management’s own projection of days of cash on hand, from the COO’s FY26–FY28 Cash Flow "
          "Narrative (board packet B.01.01, April 2026). A district projection, not an audited figure."))
    A(f'<p class="plain"><b>Management’s projected cash trajectory:</b> {mcash_txt} days. '
      "Under ~30 days is tight; ~17 days (FY28) is alarming for a district this size.</p>")
    A("<table><thead><tr><th>When</th><th>Borrowing</th><th>Status</th><th>Amount</th>"
      f"<th>Purpose</th></tr></thead><tbody>{borrow_rows}</tbody></table>")
    A('<div class="take"><b>Takeaway:</b> Iowa City took a <b>$10M interfund loan</b> from its '
      "health-insurance fund in August 2025 — the month its General Fund cash fell <b>below $6M "
      "(~10 days)</b> — and a <b>$3M revenue anticipation warrant</b> to make the March 15, 2026 "
      "payroll, with a much larger warrant proposed for May 2026 (partly to lend the SAVE construction "
      "fund enough cash to make its own bond payment). For a district to borrow short-term to cover "
      "payroll and to prop up another fund’s bond payment is direct evidence of an intra-year cash "
      "squeeze.</div>")
    A('<div class="caution"><b>Sourcing &amp; status.</b> These figures come from the COO’s memo to '
      "the Board of Education (board packet item B.01.01, April 1, 2026) — <b>district projections and "
      "disclosures, not audited figures</b>. “Executed” items had already occurred when the memo was "
      "written; “proposed”/“projected” items had not. We rely on monthly/board data here only for "
      "Iowa City follow-up — exactly the targeted use the statewide screen reserves it for; it does "
      "not change any other district’s classification.</div>")
    A("</div>")

    # Numerator sensitivity vs Cedar Rapids
    A('<div class="card"><h2>7. “Is it just one strict measure?” — No.</h2>')
    A('<p class="plain">A fair question: maybe Iowa City only looks thin under the strictest '
      "definition of savings. So we recalculated the cushion under five progressively broader "
      "definitions, for Iowa City and Cedar Rapids (its most natural large peer), in the same year "
      "(FY2023, the last year both have audited detail).</p>")
    A("<table><thead><tr><th>Definition of “savings”</th><th>Iowa City</th>"
      f"<th>Cedar Rapids</th></tr></thead><tbody>{sens_rows}</tbody></table>")
    A(fig("4_waterfall_iccsd_numerators.png",
          "Iowa City’s cushion under each broader definition of savings (FY2023). Even the "
          "most generous definition stays under about 20 days."))
    A('<div class="take"><b>Takeaway:</b> The thinness is <b>not</b> an artifact of one strict '
      "metric. Under every definition — from the narrowest to the broadest — Iowa City "
      "lands at roughly 9–20 days, while Cedar Rapids is 60–90 days. Cedar Rapids is "
      "stronger across the board.</div>")
    A("</div>")

    # Statewide context + heatmap
    A('<div class="card"><h2>8. Statewide context (FY2024)</h2>')
    A(f'<p class="plain">We scored about {n_state} Iowa districts for FY{RECENT} on the same '
      "practical-cushion measure. The bottom quarter of districts had a cushion of roughly "
      f"<b>{q25:.0f} days or less</b>. Iowa City sits just inside that bottom group; many of the "
      "districts thinner than it are much smaller. Among the <i>large</i> districts, only Waterloo "
      "and Linn-Mar were thinner.</p>")
    A(fig("5_heatmap_metrics.png",
          "Heatmap of the focus districts across several liquidity measures (red = relatively worse "
          "within this peer set). Numbers are the actual values; days for the cushion, percentages "
          "for the rest."))
    A("</div>")

    # What it does/doesn't prove
    A('<div class="card"><h2>9. What this proves — and what it doesn’t</h2>')
    A('<div class="caution"><b>This is a screen, not a diagnosis.</b> Year-end balances cannot show '
      "the lowest point of cash <i>during</i> the year, which is when a squeeze would actually "
      "happen. So the honest conclusions are:</div>")
    A("<ul>")
    A("<li><b>Iowa City screens as liquidity-constrained and keeps thin operating reserves.</b> "
      "That part is well-supported by the data.</li>")
    A("<li><b>Its sharpest signal is spending authority (UAB), not year-end cash.</b> It has the "
      "least legal spending room of any large peer, and that room went negative in FY2023.</li>")
    A("<li><b>For most districts, intra-year cash stress stays unproven</b> by this annual data — "
      "confirming it needs monthly records or borrowing evidence. <b>Iowa City is the exception:</b> "
      "its own management has disclosed short-term borrowing to make payroll and bond payments "
      "(section 6), so for Iowa City the intra-year stress is <b>documented, not just apparent</b> "
      "(on unaudited, district-reported figures).</li>")
    A("<li><b>Cedar Rapids does not screen as constrained</b> under any definition we tested.</li>")
    A("</ul>")
    A('<p class="plain">To confirm actual intra-year stress for a flagged district, the next step is '
      "month-by-month data: cash balances by fund, revenue and spending by month, payroll and "
      "benefit runs, accounts payable, any short-term or interfund borrowing, and grant-receivable "
      "aging. <i>Iowa City’s own board materials gesture at this:</i> "
      f"{supp_txt} — internal/unaudited figures suitable only for targeted follow-up.</p>")
    A("</div>")

    # Methodology
    A('<div class="card"><h2>How this was built (sources &amp; method)</h2>')
    A("<p style='font-size:15px'>Every number traces to an official source. Nothing here relies on "
      "monthly board packets for the statewide comparison (those are used only for district-specific "
      "follow-up, like the Iowa City cash figures above).</p>")
    A("<dl style='font-size:14.5px'>")
    A("<dt>Certified Annual Report (CAR)</dt><dd>State-filed revenues, spending, and fund balances "
      "for every district (FY2017–FY2024). Source of the per-fund balances.</dd>")
    A("<dt>SBRC Final Cash Reserve Levy files</dt><dd>State-computed assigned+unassigned reserves, "
      "the 20% reference cap, the cash reserve levy, and remaining levy capacity — statewide, "
      "FY2020–FY2024. Source of the practical-cushion numerator across all districts.</dd>")
    A("<dt>Department of Education / Management UAB workbook</dt><dd>Spending authority (UAB) and "
      "certified enrollment, statewide. These are state-computed and exist even when a district’s "
      "audit is late.</dd>")
    A("<dt>Audited financial reports (ACFRs)</dt><dd>For the 15 largest districts (FY2020–FY2025): "
      "the unassigned/assigned split, cash &amp; investments, and audit findings.</dd>")
    A("</dl>")
    A('<p style="font-size:14px;color:#64748b">Capital balances (the SAVE/penny-tax fund, PPEL, '
      "construction and debt-service funds) are deliberately excluded from the operating-cushion "
      "measures — that money is legally tied up and can’t be used to make payroll. The full "
      "dataset, a field-by-field data dictionary, every table, and the code that produces all of it "
      "live alongside this report.</p>")
    A("</div>")

    A('<footer>Independent analysis. Built only from Iowa state filings (CAR, SBRC cash-reserve-levy '
      "files, DE/DOM UAB workbook) and audited district financial reports. This is an annual "
      "early-warning screen of <i>apparent</i> liquidity risk; it does not assert confirmed "
      "intra-year cash stress. Generated June 2026.</footer>")
    A("</div></body></html>")

    out = C.OUTPUT_DIR / "liquidity-stress-report.html"
    out.write_text("\n".join(H))
    print("wrote", out, f"({out.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
