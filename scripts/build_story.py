#!/usr/bin/env python3
"""
Build the long-form narrative "How Iowa City ran out of room" -> how-it-happened.html.

A single scrollable feature for a general reader, written in the project owner's voice (calm, factual,
front-end bolded, lead with the so-what, no em dashes, numbered footnotes). Self-contained: inline SVG
charts, inline CSS, a little vanilla JS for scroll reveal. Charts not photos.

NOT linked from site nav. The page exists in the repo but is unpublished/unlisted until approved.

Resume: each section is its own function in SECTIONS. Status + checklist in research/story-build-status.md.
Judgment calls / things to refine: research/story-judgment-calls.md.

Run:  python3 scripts/build_story.py   ->  how-it-happened.html
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------------------------------------------- citation system (numbered footnotes)
SOURCES = {
    "kcrg-jan": "KCRG-TV9, 'Iowa City School Board questions oversight after $10M transfer to cover payroll,' Jan 30 2026.",
    "kcrg-feb": "KCRG-TV9, 'Iowa City Schools face budget crisis after $10 million transfer without board approval,' Feb 2026.",
    "gz-bond":  "The Gazette, 'Iowa City School District voters pass $191.5 million school bond Tuesday,' Sept 2017.",
    "gz-act":   "The Gazette, 'Iowa City schools purchases ACT's Tyler Building for $8.7 million,' 2022.",
    "di-act":   "The Daily Iowan, 'Iowa City Community School District to purchase Tyler Building on ACT campus,' June 19 2022.",
    "gz-contract": "The Gazette, 'Iowa City schools Superintendent Matt Degner gets new 3-year contract,' July 2025.",
    "gz-rating": "Moody's withdrawal of the district's bond rating, October 2024, as reported by The Gazette (2026).",
    "gz-emails": "The Gazette, 'Emails: Fundamental errors in Iowa City schools accounting flagged in 2024,' June 15 2026.",
    "gz-finger": "The Gazette, 'Former Iowa City school CFO questioned district's finances' (CFO Leslie Finger emails; $525,110 in federal late-filing penalties Sept 2023 to June 2025; federal tax lien filed and lifted Feb 2025), 2026.",
    "gz-cap":   "The Gazette, June 2026: corrective action plan submitted to a state financial oversight board, November 2023.",
    "gz-cline": "The Gazette, 'Iowa Board of Education questions Iowa City schools finances,' June 18 2026 (testimony of Kassandra Cline).",
    "gz-sped":  "The Gazette, 'Here's why Iowa City schools special education costs are rising,' May 28 2026.",
    "gz-banks": "KCRG-TV9, 'Iowa City facility projects may be stalled amidst financial crisis, banks reject loan bids,' April 28 2026.",
    "gz-sell":  "KCRG-TV9 / The Daily Iowan, April-May 2026: district sells former headquarters (1725 N Dodge St) to the City of Iowa City for $3.2 million.",
    "gz-forensic": "The Gazette, 'Iowa City school board accepts superintendent resignation,' June 2 2026 (forensic-audit plan; bond rating not restored until at least 2028; audit timeline).",
    "gz-statebd": "The Gazette, 'Iowa Board of Education questions Iowa City schools finances,' June 18 2026.",
    "di-cuts":  "The Daily Iowan, 'ICCSD approves $7.5 million in budget cuts amid financial uncertainty,' March 24 2026.",
    "npr":      "Iowa Public Radio / NPR, 'As school choice expands in Iowa, one district is in a crisis from losing students,' April 2026.",
    "pfm":      "PFM Financial Advisors, Exhibit 1, presented to the ICCSD board April 1 2026 (unaudited / projected).",
    "acfr":     "Iowa City CSD Annual Comprehensive Financial Reports (audited), FY2015-FY2024.",
    "dom":      "Iowa Department of Management, Unspent Authorized Budget Report (state-computed), FY2017-FY2025.",
    "fhr":      "Iowa City CSD, Annual Financial Health Report, prepared by CFO Leslie Finger, Nov 26 2019.",
    "fhr-series": "Iowa City CSD Annual Financial Health Reports, FY2015 through FY2025 (Ten Point Financial Condition Test, ratios scored green / yellow / red against board targets). The FY2015-FY2022 reports run 22-23 pages each; the FY2025 report is a single page.",
    "fy24":     "Iowa City CSD FY2024 audited Annual Comprehensive Financial Report (RSM US LLP, filed June 2026), incl. Note 15 (Restatement of beginning net position) and Schedule of Findings 2024-001 (payroll material weakness), 2024-007 and 2024-008.",
    "car25":    "Iowa City CSD FY2025 Certified Annual Report, Treasurer's Report by Fund (self-reported, unaudited).",
    "foc-videos": "Iowa City CSD Financial Oversight Committee meeting recordings, 2023-2024 (public video).",
    "foc-jan26": "Iowa City CSD Financial Oversight Committee meeting, January 2026 (public video); opening remarks by director Mitch Lingo.",
    "emails":   "Community correspondence addressed to the ICCSD Board of Directors during the crisis period (project files; authors withheld).",
}
CITES = []          # keys in first-cited order
def cite(key):
    if key not in CITES:
        CITES.append(key)
    n = CITES.index(key) + 1
    return f'<sup class="fn"><a href="#fn{n}" id="ref{n}">{n}</a></sup>'

def footnotes_html():
    rows = []
    for i, key in enumerate(CITES, 1):
        rows.append(f'<li id="fn{i}"><span class="fnn">{i}.</span> {SOURCES.get(key, key)} '
                    f'<a class="fnback" href="#ref{i}">&#8617;</a></li>')
    return '<ol class="fnlist">' + "".join(rows) + "</ol>"

# ----------------------------------------------------------------- data (verified series; provenance noted)
DAYS = {2015: 67, 2016: 84, 2017: 88, 2018: 79, 2019: 63, 2020: 53, 2021: 43,
        2022: 39, 2023: 33, 2024: 41, 2025: 33, 2026: 7}            # GF days cash; audited <=2024
DAYS_LAST_AUDITED = 2024
UAB = {2017: 6.6, 2018: 5.4, 2019: 2.2, 2020: 1.2, 2021: 1.7, 2022: 0.1, 2023: -1.2, 2024: 1.6, 2025: 2.3}
SOLV = {2015: 9.3, 2016: 11.5, 2017: 12.3, 2018: 11.0, 2019: 7.0, 2020: 4.2, 2021: 6.3,
        2022: 2.8, 2023: 2.5, 2024: 8.1}
# Debt outstanding by year ($M). GO bonds and sales-tax (SAVE) revenue bonds.
# FY2015-2019 from data/fy15-19-extractions/Iowa_City_CSD.csv (audited). FY2020-2024 from the FY2024 audit.
# Same basis throughout (GO bonds proper + SAVE revenue bonds; small GO capital loan notes excluded).
GO_DEBT = {2015: 9.3, 2016: 6.3, 2017: 3.2, 2018: 59.0, 2019: 115.1,
           2020: 176.9, 2021: 170.6, 2022: 164.0, 2023: 156.8, 2024: 149.4}
SAVE_DEBT = {2015: 0.0, 2016: 56.1, 2017: 74.0, 2018: 97.8, 2019: 90.3,
             2020: 82.5, 2021: 74.4, 2022: 66.2, 2023: 164.7, 2024: 155.9}
IFUND = {2020: 0.28, 2021: 0.15, 2022: 0.18, 2023: 0.16, 2024: 29.09}   # GF due-from-other-funds, $M
# FY2025 fund cash, begin -> end ($M), from the FY2025 CAR Treasurer's Report by Fund (unaudited)
FUNDS = [("SAVE sales-tax capital", 45.81, 9.21), ("General Fund", 19.37, 18.29),
         ("Internal Service (health)", 15.51, 13.38), ("PPEL capital", 15.30, 8.35),
         ("Enterprise", 6.52, 7.10), ("Debt Service", 2.23, 0.22),
         ("Management Levy", 1.87, 5.62), ("Other Capital Projects", 0.92, 0.0),
         ("Student Activity", 0.38, 0.0)]

# ----------------------------------------------------------------- chart helpers (inline SVG)
def _t(x, y, s, cls="", anchor="middle", size=None, fill=None):
    sz = f' font-size="{size}"' if size else ""
    fl = f' fill="{fill}"' if fill else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" class="{cls}"{sz}{fl}>{s}</text>'

def chart_days():
    W, H = 920, 360; L, R, T, B = 46, 130, 24, 36; iw, ih = W-L-R, H-T-B
    yrs = sorted(DAYS); ymax = 100
    def X(y): return L+iw*(y-yrs[0])/(yrs[-1]-yrs[0])
    def Y(v): return T+ih*(ymax-v)/ymax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="days of cash 2015 to 2026">']
    s.append(f'<rect x="{L}" y="{Y(ymax):.1f}" width="{iw}" height="{Y(90)-Y(ymax):.1f}" fill="#16a34a" opacity="0.10"/>')
    s.append(f'<line x1="{L}" y1="{Y(90):.1f}" x2="{L+iw}" y2="{Y(90):.1f}" stroke="#16a34a" stroke-dasharray="4 3" opacity="0.6"/>')
    s.append(_t(L+iw, Y(90)-5, "district target 90 days", "lbl", "end", fill="#16a34a"))
    s.append(f'<line x1="{L}" y1="{Y(60):.1f}" x2="{L+iw}" y2="{Y(60):.1f}" stroke="#d97706" stroke-dasharray="4 3" opacity="0.6"/>')
    s.append(_t(L+iw, Y(60)-5, "GFOA floor 60 days", "lbl", "end", fill="#d97706"))
    for g in (0, 50, 100): s.append(_t(L-8, Y(g)+4, str(g), "tick", "end"))
    for y in (2015, 2018, 2021, 2024, 2026): s.append(_t(X(y), T+ih+18, str(y), "tick"))
    aud = [(X(y), Y(DAYS[y])) for y in yrs if y <= DAYS_LAST_AUDITED]
    un = [(X(y), Y(DAYS[y])) for y in yrs if y >= DAYS_LAST_AUDITED]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in aud)}" fill="none" stroke="#b91c1c" stroke-width="3"/>')
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in un)}" fill="none" stroke="#b91c1c" stroke-width="2.4" stroke-dasharray="5 4"/>')
    for y in yrs:
        fill = "#fff" if y > DAYS_LAST_AUDITED else "#b91c1c"
        s.append(f'<circle cx="{X(y):.1f}" cy="{Y(DAYS[y]):.1f}" r="3.4" fill="{fill}" stroke="#b91c1c" stroke-width="1.8"/>')
    s.append(_t(X(2015)+4, Y(DAYS[2015])-9, "67 days", "val", "start"))
    s.append(_t(X(2026)+8, Y(DAYS[2026])+4, "about 7 (projected)", "val", "start", fill="#b91c1c"))
    s.append(_t(X(2024)+6, Y(DAYS[2024])-9, "last audited", "lbl", "start"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>Days of cash, falling for a decade.</b> General Fund cash '
            'divided by daily spending. Audited through 2024 (solid); 2025 unaudited and 2026 projected (open '
            'markers, before emergency borrowing).</figcaption>' + "".join(s) + '</figure>')

def _mini(series, title, units, ymin, ymax, band=None, zero=False):
    W, H = 300, 150; L, R, T, B = 34, 10, 22, 24; iw, ih = W-L-R, H-T-B
    yrs = sorted(series); xs0, xs1 = 2015, 2026
    def X(y): return L+iw*(y-xs0)/(xs1-xs0)
    def Y(v): return T+ih*(ymax-v)/(ymax-ymin)
    s = [f'<svg viewBox="0 0 {W} {H}" class="mini" role="img" aria-label="{title}">']
    s.append(f'<rect x="{X(2022):.1f}" y="{T}" width="{X(2026)-X(2022):.1f}" height="{ih}" fill="#fee2e2" opacity="0.5"/>')
    if band: s.append(f'<rect x="{L}" y="{Y(band[1]):.1f}" width="{iw}" height="{Y(band[0])-Y(band[1]):.1f}" fill="#16a34a" opacity="0.13"/>')
    if zero: s.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{L+iw}" y2="{Y(0):.1f}" stroke="#dc2626" stroke-dasharray="3 3" opacity="0.7"/>')
    for v in (ymin, ymax): s.append(_t(L-4, Y(v)+3, f"{v:g}", "tick", "end", 8.5))
    for y in (2016, 2020, 2024): s.append(_t(X(y), T+ih+11, str(y)[2:], "tick", "middle", 8.5))
    pts = [(X(y), Y(series[y])) for y in yrs]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" fill="none" stroke="#0f172a" stroke-width="2.2"/>')
    for x, y in pts: s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.1" fill="#0f172a"/>')
    last = yrs[-1]
    s.append(_t(X(last), Y(series[last])-6, f"{series[last]:g}{units}", "val", "middle", 9.5))
    s.append('</svg>')
    return f'<figure class="minicell"><div class="minit">{title}</div>{"".join(s)}</figure>'

def chart_cushions():
    a = _mini(UAB, "Spending authority", "%", -3, 14, band=(8, 14), zero=True)
    b = _mini(SOLV, "Cash reserves", "%", 0, 14, band=(5, 14))
    c = _mini({y: v for y, v in DAYS.items() if y <= 2024}, "Days of cash", "", 0, 100, band=(90, 100))
    return ('<figure class="figwrap"><figcaption><b>Three cushions, all draining.</b> Each is a different '
            'reserve in its own units. Green is the healthy range. The pink band marks 2022 to 2026.</figcaption>'
            f'<div class="minirow">{a}{b}{c}</div></figure>')

def chart_debt():
    W, H = 920, 320; L, R, T, B = 52, 30, 24, 36; iw, ih = W-L-R, H-T-B
    yrs = sorted(GO_DEBT); ymax = 340; bw = iw/len(yrs)*0.6
    def X(i): return L+iw*(i+0.5)/len(yrs)
    def Y(v): return T+ih*(ymax-v)/ymax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="debt outstanding by year">']
    for g in (0, 100, 200, 300):
        s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+iw}" y2="{Y(g):.1f}" stroke="#eef2f7"/>')
        s.append(_t(L-8, Y(g)+4, f"${g}M", "tick", "end"))
    for i, y in enumerate(yrs):
        go, sv = GO_DEBT[y], SAVE_DEBT[y]; x = X(i)-bw/2
        s.append(f'<rect x="{x:.1f}" y="{Y(go):.1f}" width="{bw:.1f}" height="{Y(0)-Y(go):.1f}" fill="#1d4ed8"/>')
        s.append(f'<rect x="{x:.1f}" y="{Y(go+sv):.1f}" width="{bw:.1f}" height="{Y(0)-Y(sv):.1f}" fill="#60a5fa"/>')
        s.append(_t(X(i), Y(go+sv)-6, f"${go+sv:.0f}M", "val", "middle", 10))
        s.append(_t(X(i), T+ih+18, str(y), "tick"))
    s.append(_t(L+4, T+12, "GO bonds", "lbl", "start", fill="#1d4ed8"))
    s.append(_t(L+4, T+26, "SAVE sales-tax bonds", "lbl", "start", fill="#60a5fa"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>The debt kept climbing, then jumped.</b> General obligation '
            'bonds plus sales-tax (SAVE) revenue bonds outstanding, 2015 to 2024. Modest before the 2017 '
            'referendum, then the bond issues of 2018 to 2020 and a new $71M SAVE issue in 2023 pushed it to a '
            '$322M peak. Source: FY2015 to FY2024 audits.</figcaption>' + "".join(s) + '</figure>')

def chart_dumbbell():
    W = 920; rowh = 27; H = 40 + rowh*len(FUNDS) + 30; L, R, T = 190, 80, 32; iw = W-L-R; xmax = 48
    def X(v): return L+iw*v/xmax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="fund cash drawdown FY2025">']
    s.append(_t(L, T-12, "open = start of FY2025", "lbl", "start", fill="#94a3b8"))
    s.append(_t(L+150, T-12, "filled = end of FY2025", "lbl", "start", fill="#b91c1c"))
    for gx in (0, 10, 20, 30, 40):
        s.append(f'<line x1="{X(gx):.1f}" y1="{T}" x2="{X(gx):.1f}" y2="{T+rowh*len(FUNDS):.1f}" stroke="#eef2f7"/>')
        s.append(_t(X(gx), T+rowh*len(FUNDS)+16, f"${gx}M", "tick"))
    for i, (name, b, e) in enumerate(FUNDS):
        y = T+rowh*i+rowh/2+4
        col = "#b91c1c" if e < b-0.3 else ("#16a34a" if e > b+0.3 else "#64748b")
        s.append(_t(L-10, y+3, name, "rowlab", "end"))
        s.append(f'<line x1="{X(b):.1f}" y1="{y:.1f}" x2="{X(e):.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="3" opacity="0.5"/>')
        s.append(f'<circle cx="{X(b):.1f}" cy="{y:.1f}" r="4.5" fill="#fff" stroke="#94a3b8"/>')
        s.append(f'<circle cx="{X(e):.1f}" cy="{y:.1f}" r="5" fill="{col}"/>')
        anc = "start" if e >= b else "end"; off = 9 if e >= b else -9
        s.append(_t(X(e)+off, y+3.5, f"${e:g}M", "val", anc, 10, fill=col))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>The whole pool emptied in one year.</b> Cash in each fund, '
            'start vs end of FY2025, from the district FY2025 Certified Annual Report (unaudited). These funds '
            'share one bank account.</figcaption>' + "".join(s) + '</figure>')

def chart_interfund():
    W, H = 920, 300; L, R, T, B = 52, 30, 26, 36; iw, ih = W-L-R, H-T-B
    yrs = sorted(IFUND); ymax = 32; bw = iw/len(yrs)*0.55
    def X(i): return L+iw*(i+0.5)/len(yrs)
    def Y(v): return T+ih*(ymax-v)/ymax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="general fund interfund borrowing by year">']
    for g in (0, 10, 20, 30):
        s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+iw}" y2="{Y(g):.1f}" stroke="#eef2f7"/>')
        s.append(_t(L-8, Y(g)+4, f"${g}M", "tick", "end"))
    for i, y in enumerate(yrs):
        v = IFUND[y]; x = X(i)-bw/2
        col = "#b91c1c" if y == 2024 else "#cbd5e1"
        s.append(f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{Y(0)-Y(v):.1f}" fill="{col}"/>')
        lab = f"${v:.0f}M" if v >= 1 else "under $1M"
        s.append(_t(X(i), Y(v)-6, lab, "val", "middle", 10))
        s.append(_t(X(i), T+ih+18, str(y), "tick"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>Then the General Fund started lending to other funds.</b> '
            'Money the General Fund was owed by other funds, by year. A rounding error until 2024, when it spiked '
            'to $29M. District-wide, the FY2024 audit flagged $38.2M of these interfund loans as unauthorized.'
            '</figcaption>' + "".join(s) + '</figure>')

# FY2024 spending authority (Unspent Authorized Budget, % of max) for all 15 large districts. From the
# project KPI dataset (data/kpi-three-methodologies.csv). Iowa City is the lowest of the 15.
PEER_UAB = {"Iowa City CSD": 1.6, "West Des Moines CSD": 9.4, "Dubuque CSD": 9.6, "Linn-Mar CSD": 9.6,
            "Ankeny CSD": 11.8, "Waterloo CSD": 12.7, "Cedar Rapids CSD": 13.5, "Davenport CSD": 14.9,
            "College CSD (Prairie)": 15.4, "Muscatine CSD": 20.7, "Des Moines Independent CSD": 21.0,
            "Johnston CSD": 21.6, "Pleasant Valley CSD": 21.9, "Burlington CSD": 29.3, "Waukee CSD": 31.0}

def chart_debt_cash():
    """Combo: debt outstanding (light bars, left axis) with days of operating cash (red line, right axis)."""
    W, H = 920, 380; L, R, T, B = 56, 56, 40, 38; iw, ih = W-L-R, H-T-B
    yrs = sorted(GO_DEBT); dmax, cmax = 340, 100; bw = iw/len(yrs)*0.6
    def X(i): return L+iw*(i+0.5)/len(yrs)
    def YD(v): return T+ih*(dmax-v)/dmax
    def YC(v): return T+ih*(cmax-v)/cmax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="debt and days of cash 2015 to 2024">']
    for g in (0, 100, 200, 300):
        s.append(f'<line x1="{L}" y1="{YD(g):.1f}" x2="{L+iw}" y2="{YD(g):.1f}" stroke="#eef2f7"/>')
        s.append(_t(L-8, YD(g)+4, f"${g}M", "tick", "end"))
    for g in (0, 50, 100):
        s.append(_t(L+iw+8, YC(g)+4, f"{g}", "tick", "start"))
    s.append(_t(L-8, T-16, "debt", "lbl", "end"))
    s.append(_t(L+iw+8, T-16, "days of cash", "lbl", "start", fill="#b91c1c"))
    for i, y in enumerate(yrs):
        go, sv = GO_DEBT[y], SAVE_DEBT[y]; x = X(i)-bw/2
        s.append(f'<rect x="{x:.1f}" y="{YD(go):.1f}" width="{bw:.1f}" height="{YD(0)-YD(go):.1f}" fill="#c7d8f5"/>')
        s.append(f'<rect x="{x:.1f}" y="{YD(go+sv):.1f}" width="{bw:.1f}" height="{YD(0)-YD(sv):.1f}" fill="#e2ebfb"/>')
        s.append(_t(X(i), T+ih+18, str(y), "tick"))
    pts = [(X(i), YC(DAYS[y])) for i, y in enumerate(yrs)]
    s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" fill="none" stroke="#b91c1c" stroke-width="3.2"/>')
    for x, yv in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{yv:.1f}" r="3.4" fill="#fff" stroke="#b91c1c" stroke-width="1.8"/>')
    s.append(_t(X(2), YC(DAYS[2017])-10, "88 days of cash", "val", "middle", fill="#b91c1c"))
    s.append(_t(X(8)+6, YC(DAYS[2023])+16, "33 days", "val", "middle", fill="#b91c1c"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>Debt up, cash down, on one clock.</b> Light bars are debt '
            'outstanding, GO plus SAVE (left axis). The red line is days of operating cash (right axis), which '
            'counts actual cash, not money owed between funds. By law these are separate pots. How they ended up '
            'moving together is the rest of this story.</figcaption>' + "".join(s) + '</figure>')

def chart_peer_strip():
    """All 15 large districts on FY2024 spending authority; Iowa City highlighted as the low outlier."""
    W, H = 920, 168; L, R, T = 32, 32, 54; iw = W-L-R; xmax = 34; band = 8
    def X(v): return L+iw*v/xmax
    yline = T+26
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="spending authority across 15 districts">']
    s.append(f'<rect x="{X(band):.1f}" y="{T}" width="{X(xmax)-X(band):.1f}" height="60" fill="#16a34a" opacity="0.08"/>')
    for g in (0, 10, 20, 30):
        s.append(f'<line x1="{X(g):.1f}" y1="{T}" x2="{X(g):.1f}" y2="{T+60}" stroke="#eef2f7"/>')
        s.append(_t(X(g), T+60+16, f"{g}%", "tick"))
    for name, v in PEER_UAB.items():
        me = name == "Iowa City CSD"
        s.append(f'<circle cx="{X(v):.1f}" cy="{yline:.1f}" r="{6 if me else 4.5}" '
                 f'fill="{"#b91c1c" if me else "#94a3b8"}" opacity="{1 if me else 0.7}"/>')
    s.append(_t(X(PEER_UAB["Iowa City CSD"]), yline-13, "Iowa City  1.6%", "val", "middle", fill="#b91c1c"))
    s.append(_t(X(20), yline-13, "the other 14 large districts", "lbl", "middle", fill="#64748b"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>Same state, same rules, very different results.</b> Each dot '
            'is one of the 15 largest Iowa districts on spending authority (unspent budget as a share of the '
            'limit), FY2024, the state\'s central health measure. Fourteen sit between 9% and 31%. Iowa City sits '
            'alone at 1.6%.</figcaption>' + "".join(s) + '</figure>')

# ----------------------------------------------------------------- sections
def sec_0():
    return f'''
<section class="sec reveal" id="s0">
<p class="lead"><b>In January 2026, Iowa City's school board learned it had borrowed $10M that no board member
had approved.</b> The money had come out of the district's health insurance fund the prior August, to cover
payroll.{cite("kcrg-jan")} It was left out of the quarterly report the board actually saw. The board got the
full story months later.</p>

<p><b>Six years earlier, the same district passed the largest school bond in Iowa history.</b> Voters approved
$191.5M in 2017 to rebuild and expand its schools.{cite("gz-bond")} By its own numbers at the time, the
district was in good shape.</p>

<p><b>The gap between those two facts is the story.</b> Two separate failures arrived at the same time, and they
drained the same bank account. One was a decade of building. The other was an operating budget that slowly
stopped balancing. Neither caused the other. They met in the district's checkbook, at the worst possible
moment.</p>

{chart_days()}

<p><b>Read the chart as the whole story in one line.</b> That is the district's cash, counted in days of
spending. It ran close to three months of cash in the mid 2010s. The audited line ends in 2024. The dotted
tail is the district's own unaudited figure for 2025 and a 2026 projection of about a week of cash, before any
emergency borrowing.{cite("pfm")}</p>
</section>'''

def sec_1():
    return f'''
<section class="sec reveal" id="s1">
<h2>It did not start in trouble</h2>

<p><b>In 2016 the district looked healthy on every measure that matters.</b> The General Fund held about $33M
in cash, close to 84 days of spending.{cite("acfr")} Its solvency ratio, reserves against a year of revenue,
sat above 11%, inside the range Iowa treats as healthy. Its spending authority, the number the state watches
most closely, still had room.</p>

<p><b>The district even graded its own books.</b> In 2019 its chief financial officer wrote a 22-page financial
health report, scoring ten financial ratios green, yellow, or red against targets.{cite("fhr")} That is a
finance office that knew exactly what to watch, and put it in writing for the board to read.</p>

<p><b>That same report sounded the first alarm.</b> It noted solvency had slipped from 11% to 7%, below the 10%
level it said bond rating agencies look for. It noted days of cash had fallen to 63, short of the 90-day target.
The warning was on the page in 2019, in the district's own hand.</p>

{chart_cushions()}

<p><b>So the capacity to see the problem existed.</b> The rest of this story is about what happened to the
people, the committee, and the habits that produced that 2019 report. Within a few years, all three were gone.</p>
</section>'''

def sec_2():
    return f'''
<section class="sec reveal" id="s2">
<h2>The biggest bet in the state</h2>

<p><b>In September 2017 voters approved $191.5M in bonds, the largest school bond in Iowa history.</b>{cite("gz-bond")}
It paid for the Facilities Master Plan, a decade of construction across the district. The district issued the
bonds in three pieces between 2017 and 2020.</p>

<p><b>One feature of Iowa school finance explains most of what follows.</b> Bond money is walled off. It goes
into a separate construction fund, restricted to the approved projects, and it is paid back by its own property
tax levy. It cannot pay a teacher, and the operating budget cannot touch it. So the building program and the
day-to-day budget were two different stories from the very start. A district can build a great deal and still
run its operations into the ground, because the two run on separate tracks.</p>

<p><b>The district did not stop at the bond.</b> It kept stacking capital debt, mostly through sales-tax (SAVE)
revenue bonds, including a $66M issue in 2022 and a $71M issue in 2023. Total debt peaked near $321M in
2023.{cite("fy24")} That left Iowa City with one of the largest sales-tax debt loads of any large district in
the state, most of its penny-sales-tax revenue pledged to bond payments for years out.</p>

{chart_debt()}

<p><b>It also spent capital cash closer to home.</b> In 2022 the district paid $8.7M for ACT's Tyler Building,
using its physical-plant levy, and moved its central offices there.{cite("gz-act")}{cite("di-act")} The price came in well
above the building's $5.4M assessed value, and the purchase drew public objection at the time. Some of the
residents who questioned it would spend the next three years warning the board, in writing, about nearly
everything else that went wrong.
<br><a class="more" href="act-building.html">The headquarters they bought, and the one they sold &rarr;</a></p>
</section>'''

def sec_3():
    return f'''
<section class="sec reveal" id="s3">
<h2>A short guide to how the money works</h2>

<p><b>Iowa runs its schools on two separate meters, and most people only watch one.</b> The first is cash, the
money in the bank. The second is spending authority, a state-set ceiling on how much a district may spend at
all, no matter how much cash it holds.{cite("dom")} A district can sit on cash and still run out of authority,
or keep authority while the cash drains. Iowa City managed to do both at once.</p>

<p><b>The funds are walled off from each other by law.</b> Operating money lives in the General Fund. Bond
proceeds live in a construction fund. Sales-tax money, the physical-plant levy, and debt service each have
their own fund. Money raised for one purpose generally cannot be spent on another. That is why building cannot
fund teaching, and teaching cannot raid the building money.</p>

<p><b>One detail breaks the tidy picture.</b> All those separate funds share a single bank account. The district
pools its cash and tracks each fund's claim on the pool as a bookkeeping entry.{cite("fy24")} So a fund can
spend more cash than it holds and quietly borrow from the others in the pool. Hold onto that. It is how two
unrelated problems ended up in the same hole.</p>

<div class="callout"><p><b>A fair question: aren't the funds separate?</b> They are, by law, and that separation
is real. It does not mean the building money and the operating money never met. Two things connect them. First,
the separate funds share one bank account, so spending in one draws down the cash available to all of them,
ledgers or no ledgers. Second, the funds were in fact mixed: the FY2024 audit found $38M of loans moving between
funds without the board votes Iowa law requires, and the following year $10M moved from the insurance fund to
cover payroll the same way.{cite("fy24")} The rule keeps the funds apart on paper. The cash sat in one
account.</p></div>
</section>'''

def sec_4():
    return f'''
<section class="sec reveal" id="s4">
<h2>The operating budget stops balancing</h2>

<p><b>While the district built, its day-to-day budget slowly came apart.</b> The cause was not exotic. Salaries
and benefits ran about 85% of the General Fund, year after year, while enrollment flattened and state aid stayed
thin.{cite("acfr")} Costs rose faster than the money allowed to cover them.</p>

<p><b>Every operating cushion drained on the same schedule, and each fell below the line the district had drawn
for itself.</b> The district's own 2019 financial health report set the target for days of cash at 90, and
treated solvency under 10% as a warning, the level it noted that bond rating agencies watch.{cite("fhr")} By
2022, spending authority had fallen from 6.6% of the limit to 0.1%, solvency from 12% to under 3%, and days of
cash from 88 to 39.{cite("dom")} Each number was not just lower year over year. It was below the floor the
district's own finance office had named. None of this had anything to do with construction. It was the
operating model not adding up.</p>

<p><b>This is the half of the story that gets missed.</b> The building program was loud and visible. The
operating decline was quiet and on a different page. Because the two run on separate tracks, almost no one
connected them until both hit bottom.</p>
</section>'''

def sec_5():
    return f'''
<section class="sec reveal" id="s5">
<h2>The alarms, and the committee built to answer them</h2>

<p><b>The warnings were not subtle, and they came early.</b> The district's own 2019 health report already
flagged solvency below the rating-agency line and cash below target.{cite("fhr")} By 2023, spending authority
had gone negative, the unlawful level that puts a district under state review.</p>

<p><b>The district responded the right way, on paper.</b> In November 2023, the same month it filed a
corrective-action plan with the state, the board formed a Financial Oversight Committee to watch the
finances.{cite("gz-cap")}{cite("foc-videos")} It met into early 2024.</p>

<p><b>Then it stopped.</b> The committee went dark for about two years. When it finally reconvened in January
2026, as the crisis broke, a director opened the meeting by noting the obvious, that the group had not met in a
couple of years.{cite("foc-jan26")} The two years it did not meet were the two years the rest of this story
happened.</p>

<p><b>The audits stopped landing, too.</b> The FY2023 audit, due in early 2024, did not arrive until August
2025, twenty-six months late, with a declared material weakness.{cite("fy24")} In October 2024, Moody's
withdrew the district's bond rating over the missing audits.{cite("gz-rating")}</p>
</section>'''

def sec_6():
    return f'''
<section class="sec reveal" id="s6">
<h2>Empty at the same time</h2>

<p><b>By 2025 there was no slack left anywhere.</b> The operating reserves were spent. The bond proceeds were
spent. The sales-tax fund, the district's big capital reservoir, drained from $45.8M to $9.2M in a single
year.{cite("car25")} Total pooled cash fell about 42% in 2025, from roughly $108M to $62M.</p>

{chart_dumbbell()}

<p><b>Look at how many funds emptied at once.</b> Debt service ran down to about $200K. The student-activity
fund went to zero. Two capital accounts went to zero. When every fund in the shared pool bottoms out together,
a normal summer cash dip has nowhere to turn.</p>
</section>'''

def sec_7():
    return f'''
<section class="sec reveal" id="s7">
<h2>Borrowing from itself</h2>

<p><b>With the pool dry, the funds began borrowing cash from each other to pay the bills.</b> The FY2024 audit
put a number on it. The district carried $38.2M of interfund loans at mid-2024, between funds, to cover what
the auditors called cash-flowing expenditures.{cite("fy24")}</p>

{chart_interfund()}

<p><b>The auditors flagged it as breaking the law, not just the budget.</b> Iowa rules require a formal board
vote before one fund lends to another, full repayment by October 1 of the next year, and interest on the loan.
The district did none of those.{cite("fy24")} The board had not approved the loans. The deadline passed. No
interest was paid.</p>

<p><b>The fund that pays for early retirement shows how the borrowing happened.</b> The district granted
early-retirement buyouts in waves: about $6M of new obligations in 2019 and $7.2M in 2023, against a normal year
of one to two million.{cite("acfr")} The 2023 wave was paid out in 2024, about $8.2M in cash, from a Management
Levy Fund whose own tax levy could not cover it. By mid-2024 that single fund owed the shared pool $11.4M, close
to a third of the district's $38.2M in unauthorized interfund loans.{cite("fy24")}
<br><a class="more" href="early-retirement.html">Follow the early-retirement money &rarr;</a></p>

<p><b>One fund went underwater and could not be rescued.</b> The student-activity fund overspent by about $1M
and ended 2024 nearly $1M in the red, owing the other funds $1.5M.{cite("fy24")} State law bars topping it up
with a transfer, so the hole just sat there.</p>

<p><b>The same audit had to correct the district's prior books in three separate places.</b> Its restatement
reset the 2023 starting balance for three unrelated errors: income surtax revenue recognized in the wrong year,
general-obligation bond premiums over-amortized, and an early-retirement benefit under-recorded by
$870,324.{cite("fy24")} Three independent corrections in a single restatement is a measure of how far the
records had drifted from the actual numbers.</p>
</section>'''

def sec_8():
    return f'''
<section class="sec reveal" id="s8">
<h2>Who was watching</h2>

<p><b>The CFO who wrote the district's 2019 financial health report retired in June 2023.</b>{cite("fhr")} His
successor, the state later testified, lacked the school-business-official credential and was not really the
district's financial leader.{cite("gz-cline")}</p>

<p><b>Bank reconciliations were not done for about three years.</b> One finance officer could set up vendors,
approve invoices, record the entries, and release the cash, with no second set of eyes. The auditors named the
payroll cycle itself a material weakness: the same person could carry a payroll run from start to finish without
an independent check.{cite("fy24")} A staffer who joined in 2024 warned leadership of fundamental errors that
October. The recorded reply was a two-word thank-you.{cite("gz-emails")}</p>

<p><b>The superintendent's contract carried no performance measures and was not tied to the district's
goals.</b> The board renewed it in July 2025, weeks before the crisis surfaced.{cite("gz-contract")} When the
failures came to light, the board moved the superintendent to a $180K role rather than removing
him.{cite("gz-forensic")}</p>
</section>'''

def sec_9():
    return f'''
<section class="sec reveal" id="s9">
<h2>Iowa City was watching</h2>

<p><b>Iowa City is not a place that misses this kind of thing.</b> It is a university town, thick with
accountants, lawyers, auditors, and finance professionals, and the school board hears from that community
constantly. On the money, people were paying close attention the whole way down.</p>

<p><b>They were watching when the district paid $8.7M for the ACT building, well above its $5.4M assessed
value.{cite("gz-act")}{cite("di-act")} They were watching when the audits stopped arriving on time, and when items left the
board agenda without explanation right before votes to authorize tens of millions in new spending.</b> The
questions residents raised, in public and in writing, named the board's fiduciary duty directly.{cite("emails")}</p>

<p><b>A year later, the State Board of Education would use the same word, fiduciary, to describe what had been
missing.</b>{cite("gz-statebd")} The community had said it first.</p>
</section>'''

def sec_10():
    return f'''
<section class="sec reveal" id="s10">
<h2>The reckoning</h2>

<p><b>The bill came due in 2026, all at once.</b> The hidden $10M loan surfaced in January.{cite("kcrg-jan")}
Payroll had run about $13.5M over budget, up 9% against a planned 2 to 3%, much of it a roughly $19M
special-education shortfall.{cite("kcrg-feb")}{cite("gz-sped")}</p>

<p><b>Every lever the district reached for was already compromised.</b> It approved $7.5M in cuts.{cite("di-cuts")}
It tried to borrow $25M, and every bank said no, because there were no current audits to underwrite
it.{cite("gz-banks")} It paused the $104M facilities plan and sold its old headquarters to the city for $3.2M to
raise cash.{cite("gz-sell")}</p>

<p><b>The people at the top left.</b> The superintendent, the deputy superintendent, and the CFO all departed.
The bond rating was gone until at least 2028.{cite("gz-forensic")} The state opened oversight proceedings, with
a takeover on the table.{cite("gz-statebd")} PFM projected the district would reach about a week of operating
cash by mid-2026, not enough to cover July payroll without an emergency warrant.{cite("pfm")}</p>
</section>'''

def sec_11():
    return f'''
<section class="sec reveal" id="s11">
<h2>Why it happened</h2>

<p><b>Strip away the noise and it is one mechanism.</b> A debt-financed building program drained the shared cash
pool from the capital side. A structural operating deficit drained the General Fund's claim from the other side.
They were never the same problem, but they ran through one bank account, and they emptied it together. With no
slack left, the funds cannibalized each other, and then the district reached into its insurance fund to make
payroll.</p>

<p><b>The district paid about $525,000 in federal penalties for filing its payroll and excise taxes late.</b> A
federal tax lien was filed against it and then lifted; the state found the late filings kept recurring because
no one was monitoring them.{cite("gz-finger")} The district lost its bond rating and its bank credit, which left
only costlier emergency borrowing. It owed interest on $38M of loans between its own funds and, by the auditors'
finding, never paid it.{cite("fy24")} In a single year its payroll ran about $13.5M over budget.{cite("kcrg-feb")}</p>

<p><b>The clearest proof is the other fourteen districts.</b> This project benchmarks Iowa City against the
fourteen other large districts in the state. They live under the same funding formula, the same enrollment
trends, and the same school-choice rules. On the state's central health measure, almost all of them sit in
comfortable territory. Iowa City sits alone at the bottom.</p>

{chart_peer_strip()}

<p><b>Fourteen districts lived under the same conditions and did not end up here.</b> A district can do well in
Iowa today, and most do. The difference was not the funding formula or the state's rules. It was everything that
sat inside the district's own control. <b>Whether that was error or something more is the question the board's
own forensic audit is meant to answer.</b>{cite("gz-forensic")}</p>
</section>'''

def sec_12():
    return f'''
<section class="sec reveal" id="s12">
<h2>What to watch next</h2>

<p><b>The full picture is still arriving.</b> The FY2024 audit landed in June 2026, two years late. The FY2025
audit is expected around November 2026, and FY2026 around March 2027.{cite("gz-forensic")} Until then, the most
recent years rest on unaudited figures.</p>

<p><b>Three things will tell you whether this is turning.</b> Whether the rebuilt Financial Oversight Committee
actually meets and bites. Whether the new CFO gets the audits and the monthly reporting current. And whether the
forensic audit finds error or intent.{cite("gz-statebd")}</p>

<p><b>The district used to grade its own books, and the grades trace the whole arc.</b> Every fall the finance
office published a financial health report, twenty-two pages scoring ten ratios green, yellow, or red against the
board's own targets.{cite("fhr-series")} Through 2017 the ratios that measure cash and reserves held. Solvency
graded green, days of cash and the unspent balance graded yellow, none of them red.</p>

<p><b>After the building program, those same ratios went red, and stayed red.</b> By FY2020 the solvency and
unspent-balance ratios had turned red. By FY2022 days of cash had joined them, every reserve measure below the
board's own target.{cite("fhr-series")} The marks never recovered.</p>

<p><b>By FY2025 the report itself had collapsed.</b> The twenty-two-page document was down to a single page, and
the district could not close its books in time to produce an audited balance sheet at all. The FY2024 audit did
not arrive until June 2026.{cite("fhr-series")}{cite("fy24")} A district that once graded its own cash and
reserves in green and yellow could not, by 2025, produce the audited balance sheet those grades are built on.
Everything in between is in the sources below.</p>
</section>'''

SECTIONS = [sec_0, sec_1, sec_2, sec_3, sec_4, sec_5, sec_6, sec_7, sec_8, sec_9, sec_10, sec_11, sec_12]

# ----------------------------------------------------------------- page assembly
CSS = """
*{box-sizing:border-box}
body{margin:0;background:#fbfbf9;color:#1a1a1a;font:19px/1.7 Georgia,'Iowan Old Style',Cambria,'Times New Roman',serif}
.bar{position:fixed;top:0;left:0;height:3px;background:#b91c1c;width:0;z-index:50}
.kicker{max-width:720px;margin:0 auto;padding:54px 22px 0;font:600 13px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#b91c1c}
h1{max-width:720px;margin:8px auto 6px;padding:0 22px;font:800 40px/1.12 Georgia,serif;letter-spacing:-.01em}
.dek{max-width:720px;margin:0 auto 10px;padding:0 22px;color:#555;font:400 21px/1.5 Georgia,serif}
.byline{max-width:720px;margin:0 auto 30px;padding:0 22px;color:#777;font:500 13.5px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.sec{max-width:720px;margin:0 auto;padding:6px 22px}
.sec h2{font:800 27px/1.2 Georgia,serif;margin:40px 0 10px;letter-spacing:-.01em}
.sec p{margin:0 0 18px}
.lead{font-size:21px}
b{font-weight:700}
.fn a{color:#b91c1c;text-decoration:none;font:600 11px/1 sans-serif;padding-left:1px}
.figwrap{margin:26px auto;max-width:960px}
figcaption{font:400 14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#555;margin:0 0 8px;max-width:760px}
figcaption b{color:#1a1a1a}
.fig{width:100%;height:auto;display:block;background:#fff;border:1px solid #ececec;border-radius:10px;padding:10px}
.minirow{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
@media(max-width:680px){.minirow{grid-template-columns:1fr}}
.minicell{margin:0;background:#fff;border:1px solid #ececec;border-radius:10px;padding:8px 8px 2px}
.minit{font:700 13px/1.3 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;padding:2px 4px}
.mini{width:100%;height:auto;display:block}
text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.tick{font-size:11px;fill:#94a3b8}
.lbl{font-size:11px;fill:#64748b}
.rowlab{font-size:12px;fill:#1a1a1a}
.val{font-size:11px;font-weight:700;fill:#1a1a1a}
.draft{max-width:720px;margin:30px auto 0;padding:10px 22px;font:600 12px/1.5 sans-serif;color:#b91c1c}
.reveal{opacity:0;transform:translateY(14px);transition:opacity .6s ease,transform .6s ease}
.reveal.in{opacity:1;transform:none}
.fnsec{max-width:720px;margin:40px auto 80px;padding:0 22px}
.fnsec h2{font:800 20px/1.2 Georgia,serif;border-top:1px solid #ddd;padding-top:20px}
.fnlist{font:400 13.5px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#444;padding-left:0;list-style:none}
.fnlist li{margin:0 0 9px;padding-left:26px;text-indent:-26px}
.fnn{font-weight:700;color:#b91c1c}
.fnback{color:#b91c1c;text-decoration:none;margin-left:4px}
.note{max-width:720px;margin:24px auto;padding:14px 18px;background:#fff;border:1px solid #ececec;border-left:4px solid #94a3b8;border-radius:8px;font:400 14.5px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#444}
.callout{margin:24px 0;padding:4px 20px;background:#fff7f6;border:1px solid #f3d4cf;border-left:4px solid #b91c1c;border-radius:8px}
.callout p{font-size:18px;margin:16px 0}
.more{display:inline-block;margin-top:2px;font:700 14px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#b91c1c;text-decoration:none;border-bottom:2px solid #f3d4cf}
.more:hover{border-bottom-color:#b91c1c}
.backlink{max-width:720px;margin:6px auto 0;padding:0 22px;font:700 14px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.backlink a{color:#b91c1c;text-decoration:none}
"""

JS = """
var b=document.querySelector('.bar');
function pr(){var h=document.documentElement;var sc=h.scrollTop||document.body.scrollTop;
var mx=(h.scrollHeight-h.clientHeight)||1;b.style.width=(100*sc/mx)+'%';}
document.addEventListener('scroll',pr,{passive:true});pr();
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)e.target.classList.add('in');});},{threshold:0.1});
document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
"""

def build():
    body = "".join(fn() for fn in SECTIONS)
    note = ('<div class="note"><b>About the figures.</b> Numbers through fiscal year 2024 are from audited '
            'reports. Fiscal year 2025 is from the district\'s own unaudited filings, and 2026 figures are '
            'projections or contemporaneous reporting. Each is labeled where it appears, and every claim is '
            'sourced in the notes at the end.</div>')
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>How Iowa City ran out of room</title>
<meta name="robots" content="noindex">
<style>{CSS}</style></head><body>
<div class="bar"></div>
<p class="draft">DRAFT &middot; not yet published &middot; under review</p>
<div class="kicker">Iowa City Community School District</div>
<h1>How Iowa City ran out of room</h1>
<p class="dek">A district built the biggest school project in state history, then went looking for cash to make
payroll. The two are connected, and they are not the same problem.</p>
<p class="byline">A data-driven account, built from audited reports, state filings, and contemporaneous coverage.</p>
{note}
{body}
<div class="fnsec"><h2>Sources</h2>{footnotes_html()}</div>
<script>{JS}</script>
</body></html>'''
    out = os.path.join(ROOT, "how-it-happened.html")
    open(out, "w").write(html)
    print(f"Wrote how-it-happened.html ({len(html)//1024} KB), {len(SECTIONS)} sections, {len(CITES)} sources")

# ===================================================================
# Companion deep-dive page: the early-retirement program and the Management Levy Fund.
# Self-contained citations so footnote numbers do not collide with the main page.
# ===================================================================

# New early-retirement obligations granted each year ($M), from Note 5 "Additions" lines,
# Iowa City CSD audited ACFRs FY2016-FY2024. Two buyout waves: 2019 and 2023.
GRANTS = {2016: 2.07, 2017: 1.43, 2018: 2.37, 2019: 5.96, 2020: 0.83,
          2021: 2.38, 2022: 1.21, 2023: 7.21, 2024: 3.43}

# Funds owing the shared cash pool at June 30, 2024 ($M), from the FY2024 interfund detail.
LEVY_SHARE = [("Management Levy Fund", 11.37, True), ("General Fund", 20.07, False),
              ("Nonmajor enterprise", 4.07, False), ("Nonmajor governmental", 1.55, False),
              ("Capital Projects", 1.10, False)]

def chart_grants():
    W, H = 920, 320; L, R, T, B = 50, 24, 28, 38; iw, ih = W-L-R, H-T-B
    yrs = sorted(GRANTS); ymax = 8; bw = iw/len(yrs)*0.6
    def X(i): return L+iw*(i+0.5)/len(yrs)
    def Y(v): return T+ih*(ymax-v)/ymax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="new early retirement obligations by year">']
    for g in (0, 2, 4, 6, 8):
        s.append(f'<line x1="{L}" y1="{Y(g):.1f}" x2="{L+iw}" y2="{Y(g):.1f}" stroke="#eef2f7"/>')
        s.append(_t(L-8, Y(g)+4, f"${g}M", "tick", "end"))
    for i, y in enumerate(yrs):
        v = GRANTS[y]; x = X(i)-bw/2
        spike = y in (2019, 2023)
        col = "#b91c1c" if spike else "#cbd5e1"
        s.append(f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{Y(0)-Y(v):.1f}" fill="{col}"/>')
        s.append(_t(X(i), Y(v)-6, f"${v:.1f}M", "val", "middle", 10,
                    fill="#b91c1c" if spike else "#64748b"))
        s.append(_t(X(i), T+ih+18, str(y), "tick"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>The district granted early retirement in waves.</b> '
            'New early-retirement obligations awarded each year. A normal year is one to two million dollars. '
            '2019 ran to about $6M, and 2023 to about $7.2M, the largest in the decade.'
            '</figcaption>' + "".join(s) + '</figure>')

def chart_levy_share():
    W, H = 920, 250; L, R, T, B = 170, 70, 16, 30; iw, ih = W-L-R, H-T-B
    xmax = 22; rows = LEVY_SHARE; rh = ih/len(rows)
    def X(v): return L+iw*v/xmax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="funds owing the shared cash pool 2024">']
    for g in (0, 5, 10, 15, 20):
        s.append(f'<line x1="{X(g):.1f}" y1="{T}" x2="{X(g):.1f}" y2="{T+ih}" stroke="#eef2f7"/>')
        s.append(_t(X(g), T+ih+20, f"${g}M", "tick"))
    for i, (name, v, hot) in enumerate(rows):
        y = T+rh*i+rh*0.5; bh = rh*0.5
        col = "#b91c1c" if hot else "#cbd5e1"
        s.append(f'<rect x="{L}" y="{y-bh/2:.1f}" width="{X(v)-L:.1f}" height="{bh:.1f}" fill="{col}" rx="2"/>')
        s.append(_t(L-10, y+4, name, "rowlab", "end"))
        s.append(_t(X(v)+6, y+4, f"${v:.1f}M", "val", "start", 11,
                    fill="#b91c1c" if hot else "#64748b"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>The early-retirement fund was one of the biggest borrowers.</b> '
            'Amounts each fund owed the shared cash pool at mid-2024. The Management Levy Fund, which pays early '
            'retirement, owed $11.4M of the district-wide $38.2M total.'
            '</figcaption>' + "".join(s) + '</figure>')

ER_SOURCES = {
    "er-note5":     "Iowa City CSD audited Annual Comprehensive Financial Reports, FY2016-FY2024, Note 5 (Long-Term Liabilities) changes schedules; the early-retirement 'Additions' line is the new obligations granted each year.",
    "er-fy24":      "Iowa City CSD FY2024 ACFR, Note 5 narrative: early-retirement benefits paid of $8,177,763 in FY2024; 54 new employee elections; 58 participants owed at year end; remaining liability $3,333,899; benefit terms (85-100% of final base salary into a Special Pay Deferral Plan, plus up to 20 sick days).",
    "er-interfund": "Iowa City CSD FY2024 ACFR, interfund-balances detail: Management Levy Fund due to other funds $11,373,033; district-wide interfund total $38,166,276; and Schedule of Findings 2024-008 (interfund balances not authorized by formal board resolution).",
    "er-restate":   "Iowa City CSD FY2024 ACFR, Note 15 (Restatement): the prior-year early-retirement liability was under-accrued by $870,324 because a 20-day sick-day benefit was excluded from the calculation.",
}

def build_early_retirement():
    cites = []
    def c(k):
        if k not in cites:
            cites.append(k)
        n = cites.index(k)+1
        return f'<sup class="fn"><a href="#fn{n}" id="ref{n}">{n}</a></sup>'
    def fns():
        rows = []
        for i, k in enumerate(cites, 1):
            rows.append(f'<li id="fn{i}"><span class="fnn">{i}.</span> {ER_SOURCES.get(k,k)} '
                        f'<a class="fnback" href="#ref{i}">&#8617;</a></li>')
        return '<ol class="fnlist">' + "".join(rows) + "</ol>"

    body = f'''
<section class="sec reveal">
<p class="lead"><b>The clearest way to see how Iowa City came to borrow from itself is to follow one cost the
board controlled directly: early retirement.</b> It is a discretionary buyout, set by board policy, paid from a
dedicated property-tax levy. Tracing it from 2016 to 2024 shows a program granted in waves, paid out of a fund
that could not cover it, and plugged with the same unauthorized interfund borrowing the audit later flagged.</p>
</section>

{chart_grants()}

<section class="sec reveal">
<h2>A program granted in waves</h2>
<p><b>Most years the district awarded one to two million dollars of new early-retirement benefits.</b> Twice it
did far more. In 2019 it granted about $6M, and in 2023 about $7.2M, the largest single year in the
decade.{c("er-note5")} These were not drift. An early-retirement buyout is a deliberate decision: the board sets
the terms and reserves the right to limit the number.</p>

<p><b>The 2023 wave is the one that mattered most.</b> It landed in the same year the district's books came apart
and its long-time chief financial officer retired. The benefit itself is generous: a district contribution worth
85% to 100% of the employee's final base salary, paid into a deferral plan, plus up to twenty sick days cashed
out.{c("er-fy24")}</p>
</section>

<section class="sec reveal">
<h2>Paid out just as the cash ran low</h2>
<p><b>The 2023 wave came due in 2024, and the bill was large.</b> The district paid $8.18M in early-retirement
benefits in fiscal 2024 alone, with 54 new employees electing in that single year.{c("er-fy24")} It was writing
some of its biggest retirement checks in the same months it was struggling to cover ordinary payroll.</p>
</section>

{chart_levy_share()}

<section class="sec reveal">
<h2>A levy that could not keep up</h2>
<p><b>Early retirement is paid from the Management Levy Fund, financed by its own property-tax levy.</b> In a
normal year the levy covers the payouts. An $8M payout year is not a normal year, and the levy could not keep
up.</p>

<p><b>So the fund borrowed the difference from the shared cash pool.</b> At mid-2024 the Management Levy Fund
owed other funds $11.4M, close to a third of the district-wide $38.2M of interfund loans the auditors flagged as
made without the board votes Iowa law requires.{c("er-interfund")} The cost the board controlled most directly
turned into one of the largest pieces of the borrowing nobody voted for.</p>

<p><b>The records understated it on the way in.</b> The 2024 audit also found the prior year's early-retirement
liability had been under-recorded by $870,324, because a twenty-day sick-day benefit was left out of the
calculation.{c("er-restate")}</p>
</section>

<section class="sec reveal">
<h2>What this shows, and what it does not</h2>
<p><b>This is not an accusation, and the audit does not name a policy violation.</b> No audit finding flags early
retirement, and there is no documented dollar figure for retirements granted beyond board policy. What the
audited records do show is a pattern worth the board's attention: a discretionary cost, granted in two large
waves, paid from a levy that could not fund it, and bridged with unauthorized interfund borrowing, while the
liability itself was understated until the cleanup.{c("er-note5")}{c("er-interfund")}</p>

<p><b>It is the whole story in miniature.</b> A controllable decision, made in good years and paid for in bad
ones, that ended up drawing on money the district did not have.</p>
</section>

<div class="backlink"><a href="how-it-happened.html">&larr; Back to the main story</a></div>
'''
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Follow the early-retirement money</title>
<meta name="robots" content="noindex">
<style>{CSS}</style></head><body>
<div class="bar"></div>
<p class="draft">DRAFT &middot; not yet published &middot; under review</p>
<div class="kicker">Iowa City Community School District &middot; a closer look</div>
<h1>Follow the early-retirement money</h1>
<p class="dek">How a cost the board controlled directly became one of the largest pieces of the borrowing nobody
voted for.</p>
<p class="byline">A companion to "How Iowa City ran out of room," built from the district's audited reports.</p>
{body}
<div class="fnsec"><h2>Sources</h2>{fns()}</div>
<script>{JS}</script>
</body></html>'''
    out = os.path.join(ROOT, "early-retirement.html")
    open(out, "w").write(html)
    print(f"Wrote early-retirement.html ({len(html)//1024} KB), {len(cites)} sources")

# ===================================================================
# Companion deep-dive page: the ACT building purchase and the headquarters trade.
# ===================================================================

# The headquarters trade, in dollars ($M). Confirmed facts.
ACT_BARS = [("Paid for ACT building, 2022", 8.7, True),
            ("Its county-assessed value", 5.4, False),
            ("Old headquarters sold, 2026", 3.2, False)]

def chart_act():
    W, H = 920, 220; L, R, T, B = 230, 70, 16, 28; iw, ih = W-L-R, H-T-B
    xmax = 10; rows = ACT_BARS; rh = ih/len(rows)
    def X(v): return L+iw*v/xmax
    s = [f'<svg viewBox="0 0 {W} {H}" class="fig" role="img" aria-label="the headquarters trade in dollars">']
    for g in (0, 2, 4, 6, 8, 10):
        s.append(f'<line x1="{X(g):.1f}" y1="{T}" x2="{X(g):.1f}" y2="{T+ih}" stroke="#eef2f7"/>')
        s.append(_t(X(g), T+ih+20, f"${g}M", "tick"))
    for i, (name, v, hot) in enumerate(rows):
        y = T+rh*i+rh*0.5; bh = rh*0.5
        col = "#b91c1c" if hot else "#cbd5e1"
        s.append(f'<rect x="{L}" y="{y-bh/2:.1f}" width="{X(v)-L:.1f}" height="{bh:.1f}" fill="{col}" rx="2"/>')
        s.append(_t(L-10, y+4, name, "rowlab", "end"))
        s.append(_t(X(v)+6, y+4, f"${v:.1f}M", "val", "start", 11,
                    fill="#b91c1c" if hot else "#64748b"))
    s.append('</svg>')
    return ('<figure class="figwrap"><figcaption><b>The headquarters trade.</b> The district paid $8.7M for an '
            'administrative building assessed at about $5.4M, then four years later sold its old headquarters for '
            '$3.2M to raise cash during the crisis.'
            '</figcaption>' + "".join(s) + '</figure>')

ACT_SOURCES = {
    "act-buy":   "The Gazette and The Daily Iowan, 2022: Iowa City CSD purchased ACT's Tyler Building for about $8.7M, funded from the Physical Plant and Equipment Levy (PPEL). The building, roughly 85,000 square feet on 7.9 acres at 301 ACT Drive, became the district's Center for Innovation and central administrative offices. (thegazette.com; dailyiowan.com, June 19 2022.)",
    "act-quest": "Contemporaneous coverage of the 2022 vote, which reported the board approved the purchase 'not without questions,' against a county-assessed value of about $5.4M.",
    "act-sell":  "KCRG-TV9 / The Daily Iowan, April-May 2026: the district sold its former headquarters at 1725 North Dodge Street to the City of Iowa City for $3.2M during the financial crisis.",
}

def build_act():
    cites = []
    def c(k):
        if k not in cites:
            cites.append(k)
        n = cites.index(k)+1
        return f'<sup class="fn"><a href="#fn{n}" id="ref{n}">{n}</a></sup>'
    def fns():
        rows = []
        for i, k in enumerate(cites, 1):
            rows.append(f'<li id="fn{i}"><span class="fnn">{i}.</span> {ACT_SOURCES.get(k,k)} '
                        f'<a class="fnback" href="#ref{i}">&#8617;</a></li>')
        return '<ol class="fnlist">' + "".join(rows) + "</ol>"

    body = f'''
<section class="sec reveal">
<p class="lead"><b>In 2022, with the building program already underway, the district bought itself a bigger
headquarters.</b> It paid about $8.7M for ACT's Tyler Building and moved its central offices in. Four years
later, short of cash, it sold its old headquarters for $3.2M. The two transactions, read together, are a small
study in how the district spent.</p>
</section>

{chart_act()}

<section class="sec reveal">
<h2>What it bought, and for how much</h2>
<p><b>The purchase was an $8.7M administrative building, paid from the physical-plant levy.</b> The Tyler
Building, about 85,000 square feet on roughly eight acres, became the district's Center for Innovation and the
home of its central administration.{c("act-buy")}</p>

<p><b>The price sat well above the building's assessed value.</b> The county assessed it at about $5.4M. The
board approved the purchase, in the words of contemporaneous coverage, "not without questions."{c("act-quest")}
The physical-plant levy that paid for it is restricted to buildings and equipment, so the money was legally
available for this even as the operating budget tightened. That is the point worth sitting with: the rules let
the district buy an $8.7M headquarters in the same window its General Fund cushion was thinning.</p>
</section>

<section class="sec reveal">
<h2>The timing</h2>
<p><b>The purchase came during the most expensive stretch in the district's history.</b> The 2017 bond was being
spent down, capital balances were already committed, and the operating reserves had been sliding since 2018.
Buying a larger administrative home in that window was a choice about priorities, made with restricted dollars
that could not have closed the operating gap, but that still signaled where attention was going.</p>
</section>

<section class="sec reveal">
<h2>The reversal</h2>
<p><b>By 2026 the district was selling property to raise cash.</b> It sold its former headquarters at 1725 North
Dodge Street to the City of Iowa City for $3.2M.{c("act-sell")} The sequence is hard to miss: $8.7M for a bigger
headquarters going into the squeeze, $3.2M for the old one coming out of it.</p>
</section>

<section class="sec reveal">
<h2>What this shows, and what it does not</h2>
<p><b>The purchase was legal and the levy was the right one to use.</b> This is not a finding of wrongdoing, and
nothing here turns on who sold the building. It is a capital-allocation decision, made in public, that residents
questioned at the time and that reads differently next to what came after.{c("act-buy")}{c("act-sell")} The
broader story is the same one the rest of the project tells: the district had room to spend in some places and
no room at all in others, and the walls between those pots of money meant a handsome headquarters and a payroll
scramble could be true at the same time.</p>
</section>

<div class="backlink"><a href="how-it-happened.html">&larr; Back to the main story</a></div>
'''
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The headquarters they bought, and the one they sold</title>
<meta name="robots" content="noindex">
<style>{CSS}</style></head><body>
<div class="bar"></div>
<p class="draft">DRAFT &middot; not yet published &middot; under review</p>
<div class="kicker">Iowa City Community School District &middot; a closer look</div>
<h1>The headquarters they bought, and the one they sold</h1>
<p class="dek">An $8.7M building bought going into the squeeze, and a $3.2M sale coming out of it.</p>
<p class="byline">A companion to "How Iowa City ran out of room," built from contemporaneous reporting.</p>
{body}
<div class="fnsec"><h2>Sources</h2>{fns()}</div>
<script>{JS}</script>
</body></html>'''
    out = os.path.join(ROOT, "act-building.html")
    open(out, "w").write(html)
    print(f"Wrote act-building.html ({len(html)//1024} KB), {len(cites)} sources")

if __name__ == "__main__":
    build()
    build_early_retirement()
    build_act()
