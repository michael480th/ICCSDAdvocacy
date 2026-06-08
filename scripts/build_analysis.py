#!/usr/bin/env python3
"""
Build the Iowa district financial benchmark (v2 — UAB-anchored).

Merges the audited per-district extractions (data/iowa-district-financials.csv) with the
Iowa DOM state-data layer (data/dom/*.csv) and scores each district per
iowa-district-financial-analysis-framework.md.

Pillar A (Health) is rebuilt around UAB per the framework's stated #1 metric:
    Health = 0.50·UAB + 0.30·Solvency + 0.20·OperatingMarginTrend
Solvency is recomputed UNIFORMLY using the DOM AEA flow-through denominator.
Composite = 0.40·Health + 0.35·OperationalQuality + 0.25·CapitalSustainability.
Strategic posture is a LABEL, not scored.
"""
import csv, os, json
from collections import defaultdict

OUT_DATA = "data"; DOM = "data/dom"
ASBO = {"Dubuque CSD", "Linn-Mar CSD"}
YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

def f(x):
    if x is None: return None
    x = str(x).strip().replace(",", "").replace("$", "").replace("%", "")
    if x in ("", "N/A", "NA", "-"): return None
    try: return float(x)
    except ValueError: return None

def loadcsv(path, delim=","):
    with open(path) as fh: return list(csv.DictReader(fh, delimiter=delim))

# ---- audit master (per district-year) ----
audit = loadcsv(f"{OUT_DATA}/iowa-district-financials.csv")
A = defaultdict(dict)            # district -> fy -> row
for r in audit: A[r["district"]][int(r["fiscal_year"])] = r

# ---- DOM layers keyed (district, fy) ----
def keyed(name, field):
    d = {}
    for r in loadcsv(f"{DOM}/{name}"):
        d[(r["district"], int(r["fiscal_year"]))] = r.get(field)
    return d
UAB   = keyed("unspent-authorized-budget.csv", "uab_pct_of_max")
AEA   = keyed("aea-flowthrough.csv", "aea_flowthrough")
ENR   = keyed("certified-enrollment.csv", "certified_enrollment")
CRLp  = keyed("cash-reserve-levy.csv", "crl_pct_of_cap")
CRLmx = keyed("cash-reserve-levy.csv", "levying_maximum")
NETV  = keyed("levy-rates-and-valuation.csv", "net_valuation_with_ge")
DSR   = keyed("levy-rates-and-valuation.csv", "debt_service_rate")
VPPEL = keyed("levy-rates-and-valuation.csv", "voted_ppel_rate")
ISL   = keyed("levy-rates-and-valuation.csv", "isl_rate")
ASSESS = {r["district"]: f(r["assessed_actual_with_ge"]) for r in loadcsv(f"{DOM}/assessed-valuation-latest.csv")}
ATRISK = keyed("at-risk.csv", "atrisk_dollars_generated")

# ---- notes layer (balance sheet + forward capital commitments) ----
NOTES = {}
for r in loadcsv("data/iowa-district-notes.csv"):
    NOTES[(r["district"], int(str(r["fiscal_year"]).replace("FY", "").strip()))] = r
def notes_latest(d):
    ys = [y for (dd, y) in NOTES if dd == d]
    return NOTES.get((d, max(ys))) if ys else {}

DISTRICTS = sorted(A.keys())

def band(v, cuts, scores):
    for c, s in zip(cuts, scores):
        if v < c: return s
    return scores[-1]

def series(d, src):                       # ordered list of (fy, val) present
    return [(y, f(src.get((d, y)))) for y in YEARS if f(src.get((d, y))) is not None]

# ---- recompute solvency uniformly with DOM AEA ----
def solvency_series(d):
    out = []
    for y in sorted(A[d]):
        r = A[d][y]
        una, asg, rev = f(r["gf_unassigned"]), f(r["gf_assigned"]) or 0, f(r["gf_revenue"])
        aea = f(AEA.get((d, y))) or 0
        if una is not None and rev:
            out.append((y, round(100*(una+asg)/(rev-aea), 2)))
    return out

# ---- components ----
def uab_component(d):
    s = series(d, UAB)
    if not s: return 3.0, None, None, None, 3, 3
    last = s[-1][1]
    ref = s[-4][1] if len(s) >= 4 else s[0][1]
    lvl = band(last, [0, 5, 10, 20], [1, 2, 3, 4, 5])
    trend = last - ref
    tr = band(trend, [-6, -3, 0, 3], [1, 2, 3, 4, 5])
    return round(0.75*lvl + 0.25*tr, 2), last, round(trend, 1), min(v for _, v in s), lvl, tr

def solvency_part(d):
    s = solvency_series(d)
    if not s: return 3.0, None, None, 3, 3
    last = s[-1][1]; ref = s[-4][1] if len(s) >= 4 else s[0][1]
    lvl = band(last, [0, 5, 10, 15, 25], [1, 2, 3, 4, 5, 4.5])
    tr = band(last-ref, [-8, -4, 0, 3], [1, 2, 3, 4, 5])
    return round(0.6*lvl + 0.4*tr, 2), last, round(last-ref, 1), lvl, tr

def forward_burden(d):
    """Forward capital load per pupil (total future debt service + construction commitments)
    -> 1-5 (higher = lighter load = more sustainable)."""
    nl = notes_latest(d)
    tfds = f(nl.get("total_future_debt_service")); cc = f(nl.get("construction_commitments")) or 0
    _, enr = enroll(d)
    if tfds is None or not enr: return 3.0, None
    load_pp = (tfds + cc) / enr
    return band(load_pp, [5000, 10000, 20000, 35000], [5, 4, 3, 2, 1]), round(load_pp)

def margin3(d):
    m = [f(A[d][y]["operating_margin_pct"]) for y in sorted(A[d]) if f(A[d][y]["operating_margin_pct"]) is not None]
    return round(sum(m[-3:])/len(m[-3:]), 1) if m else None

def quality(d):
    yrs = sorted(A[d]); rs = [A[d][y] for y in yrs]; last = rs[-1]
    last3, last2 = rs[-3:], rs[-2:]
    yn = lambda r, k: (r.get(k, "") or "").strip().upper().startswith("Y")
    opinion_ok = "unmod" in (last.get("opinion_type", "").lower())
    mw_recent = any(yn(r, "material_weakness") for r in last3)
    mw_ever = any(yn(r, "material_weakness") for r in rs)
    sd_recent = any(yn(r, "significant_deficiency") for r in last2)
    rep_recent = any(yn(r, "repeat_finding") for r in last2)
    cert = yn(last, "gfoa_cert") or d in ASBO
    stale = max(yrs) < 2025
    s = 5.0; items = [("Base", 5.0)]
    if not opinion_ok: s -= 2.0; items.append(("Opinion not unmodified", -2.0))
    if mw_recent: s -= 1.5; items.append(("Material weakness (last 3 yrs)", -1.5))
    elif mw_ever: s -= 0.5; items.append(("Material weakness (earlier)", -0.5))
    if sd_recent: s -= 0.75; items.append(("Significant deficiency (recent)", -0.75))
    if rep_recent: s -= 0.5; items.append(("Repeat finding (recent)", -0.5))
    if stale: s -= 2.5; items.append(("FY24/FY25 audit missing / stale", -2.5))
    if d == "Iowa City CSD": s -= 0.5; items.append(("$35M restatement + 26-mo-late filing", -0.5))
    if cert: s += 0.5; items.append(("GFOA/ASBO certificate", +0.5))
    total = max(1.0, min(5.0, round(s, 1)))
    if total != round(s, 1): items.append(("(floored to 1.0)" if s < 1 else "(capped at 5.0)", 0))
    return total, cert, mw_recent, sd_recent, stale, items

def enroll(d):
    s = series(d, ENR)
    if len(s) < 2: return None, (s[-1][1] if s else None)
    (y0, e0), (y1, e1) = s[0], s[-1]
    return round(((e1/e0)**(1/(y1-y0))-1)*100, 2), e1

def capex_intensity(d):
    rs = [A[d][y] for y in sorted(A[d])][-3:]
    r = [f(x["capital_additions"])/f(x["depreciation"]) for x in rs
         if f(x["capital_additions"]) is not None and f(x["depreciation"])]
    return round(sum(r)/len(r), 2) if r else None

def debt_headroom(d):                      # GO debt vs 5% of actual value (latest)
    yrs = sorted(A[d]); go = f(A[d][yrs[-1]]["go_debt_outstanding"]) or 0
    av = ASSESS.get(d)
    if not av: return None, None
    limit = 0.05*av
    return round(go/limit, 2), round((limit-go)/1e6)

def strategic(d, cagr):
    ci = capex_intensity(d)
    yrs = sorted(A[d])
    go = [f(A[d][y]["go_debt_outstanding"]) or 0 for y in yrs]
    sv = [f(A[d][y]["save_rev_bonds"]) or 0 for y in yrs]
    d0, d1 = go[0]+sv[0], go[-1]+sv[-1]
    big = any((go[i]+sv[i]) - (go[i-1]+sv[i-1]) > 10_000_000 for i in range(max(1, len(yrs)-3), len(yrs)))
    building = (ci and ci > 1.2) or big or d1 > d0*1.05
    if cagr is not None and cagr > 1.0 and building: return "Building — growth-driven", ci
    if building and cagr is not None and cagr < -1.0: return "Building — renewal (declining enrollment)", ci
    if building: return "Building — renewal", ci
    if cagr is not None and cagr < -1.5: return "Contracting", ci
    return "Maintain", ci

# ---- wealth tertiles (taxable valuation per pupil, latest) ----
vpp = {}
for d in DISTRICTS:
    _, enr_last = enroll(d)
    nv = f(NETV.get((d, 2025)))
    vpp[d] = (nv/enr_last) if (nv and enr_last) else None
ranked = sorted([d for d in DISTRICTS if vpp[d] is not None], key=lambda d: vpp[d])
tert = {}
n = len(ranked)
for i, d in enumerate(ranked):
    tert[d] = "low" if i < n/3 else "mid" if i < 2*n/3 else "high"

# ---- assemble ----
cards = []
for d in DISTRICTS:
    uc, uab_last, uab_trend, uab_min, uab_lvl, uab_tr = uab_component(d)
    sc, solv_last, solv_trend, solv_lvl, solv_tr = solvency_part(d)
    m3 = margin3(d) if margin3(d) is not None else 0.0
    mc = band(m3, [-6, -3, 0, 2], [1, 2, 3, 4, 5])
    H = round(0.50*uc + 0.30*sc + 0.20*mc, 2)
    Q, cert, mw_recent, sd_recent, stale, q_items = quality(d)
    cagr, enr_last = enroll(d)
    label, ci = strategic(d, cagr)
    enr_s = 5 if (cagr is not None and cagr > 1) else (3 if (cagr is None or cagr > -1) else 2)
    dh_ratio, dh_room = debt_headroom(d)
    dh_s = 5 if dh_ratio is None else band(dh_ratio, [0.3, 0.5, 0.7, 0.9], [5, 4, 3, 2, 1])
    fb_s, forward_load_pp = forward_burden(d)        # forward capital load per pupil -> 1-5
    CS = round(0.35*H + 0.20*enr_s + 0.15*mc + 0.20*fb_s + 0.10*dh_s, 2)
    composite = round(0.40*H + 0.35*Q + 0.25*CS, 2)

    nl = notes_latest(d)
    auth_unissued = f(nl.get("authorized_unissued_debt"))
    tfds = f(nl.get("total_future_debt_service")); constr = f(nl.get("construction_commitments"))
    crl_last = f(CRLp.get((d, 2025)))
    crl_max = (CRLmx.get((d, 2025)) or "").strip() == "Y"
    flags = []
    if uab_min is not None and uab_min < 0: flags.append("UAB went negative")
    if uab_last is not None and uab_last < 5: flags.append("Thin UAB (<5%)")
    if uab_trend is not None and uab_trend < -6: flags.append("UAB falling >6pp")
    if crl_last is not None and crl_last > 40: flags.append("Heavy cash-reserve-levy reliance")
    elif crl_max: flags.append("Cash-reserve-levy at cap")
    if solv_last is not None and solv_last < 0: flags.append("Negative solvency")
    if m3 < -2: flags.append("Multi-yr operating deficit")
    if forward_load_pp is not None and forward_load_pp > 30000: flags.append("Heavy forward capital load")
    if auth_unissued and auth_unissued > 50_000_000: flags.append("Large authorized-unissued GO bond")
    if mw_recent: flags.append("Recent material weakness")
    if sd_recent: flags.append("Recent significant deficiency")
    if stale: flags.append("FY24/FY25 audit missing (stale)")
    if dh_ratio is not None and dh_ratio > 0.8: flags.append("GO debt near 5% limit")
    last = A[d][max(A[d])]
    if (f(last["gf_unassigned"]) or 0) < 0: flags.append("Negative GF unassigned balance")

    # SAVE leverage: years of sales-tax revenue already pledged to bonds (latest non-null)
    sd = next((f(A[d][y]["save_rev_bonds"]) for y in sorted(A[d], reverse=True) if f(A[d][y].get("save_rev_bonds"))), None)
    sv = next((f(A[d][y]["save_revenue"]) for y in sorted(A[d], reverse=True) if f(A[d][y].get("save_revenue"))), None)
    save_years = round(sd/sv, 1) if (sd and sv) else None

    math = dict(
        health=dict(weights=[0.50, 0.30, 0.20],
            parts=[("UAB", uc, f"level {uab_lvl} (UAB {uab_last}%) + trend {uab_tr} ({uab_trend:+}pp)" if uab_last is not None else "n/a"),
                   ("Solvency", sc, f"level {solv_lvl} (solv {solv_last}%) + trend {solv_tr} ({solv_trend:+}pp)" if solv_last is not None else "n/a"),
                   ("Margin trend", mc, f"3-yr avg op margin {m3}%")], total=H),
        quality=dict(items=q_items, total=Q),
        capsust=dict(weights=[0.35, 0.20, 0.15, 0.20, 0.10],
            parts=[("Health", H, ""), ("Enrollment", enr_s, f"{cagr:+}%/yr" if cagr is not None else "n/a"),
                   ("Margin", mc, f"{m3}%"),
                   ("Forward capital burden", fb_s, f"${forward_load_pp:,}/pupil future debt svc + commitments" if forward_load_pp else "n/a"),
                   ("GO-debt headroom", dh_s, f"{dh_ratio} of 5% limit" if dh_ratio is not None else "no GO debt")], total=CS),
        composite=dict(weights=[0.40, 0.35, 0.25], parts=[("Health", H), ("Quality", Q), ("Capital sust.", CS)], total=composite),
    )

    cards.append(dict(
        auth_unissued=auth_unissued, total_future_ds=tfds, constr_commit=constr,
        forward_load_pp=forward_load_pp, save_years=save_years, math=math,
        district=d, size=("&gt;15k" if (enr_last or 0) > 15000 else "10–15k" if (enr_last or 0) > 10000
                          else "5–10k" if (enr_last or 0) > 5000 else "&lt;5k"),
        enrollment=round(enr_last) if enr_last else None, enr_cagr=cagr, wealth=tert.get(d, "?"),
        val_per_pupil=round(vpp[d]) if vpp[d] else None,
        uab_last=uab_last, uab_trend=uab_trend, uab_min=uab_min,
        solv_last=solv_last, marg3=m3, label=label, capex=ci,
        debt_headroom_ratio=dh_ratio, debt_room_m=dh_room,
        atrisk=f(ATRISK.get((d, 2025))),
        health=H, quality=Q, cap_sust=CS, composite=composite, cert=cert,
        flags=flags, opinion_last=last.get("opinion_type", ""),
        debt_last=round(((f(last["go_debt_outstanding"]) or 0)+(f(last["save_rev_bonds"]) or 0))/1e6, 1),
        years=[y for y in sorted(A[d])],
        uab_series=[f(UAB.get((d, y))) for y in YEARS],
        uab_years=YEARS,
        solv_series=[v for _, v in solvency_series(d)],
        marg_series=[f(A[d][y]["operating_margin_pct"]) for y in sorted(A[d])],
        crl_pct=crl_last,
    ))

cards.sort(key=lambda c: c["composite"], reverse=True)

with open(f"{OUT_DATA}/iowa-district-scorecards.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["rank","district","size","enrollment","enr_cagr_pct","wealth_tertile","val_per_pupil",
                "strategic_label","uab_last_pct","uab_trend_pp","uab_min_pct","solvency_last_pct",
                "op_margin_3yr_avg_pct","cash_reserve_levy_pct_cap","debt_vs_5pct_limit",
                "health_score","quality_score","capital_sustainability","composite","flags"])
    for i, c in enumerate(cards, 1):
        w.writerow([i, c["district"], c["size"].replace("&gt;",">").replace("&lt;","<"), c["enrollment"], c["enr_cagr"],
                    c["wealth"], c["val_per_pupil"], c["label"], c["uab_last"], c["uab_trend"], c["uab_min"],
                    c["solv_last"], c["marg3"], c["crl_pct"], c["debt_headroom_ratio"],
                    c["health"], c["quality"], c["cap_sust"], c["composite"], "; ".join(c["flags"])])

# ---- enrich each card with full multi-year series + curated narrative (for the deep-dive) ----
UABd = keyed("unspent-authorized-budget.csv", "unspent_authorized_budget")
MAXB = keyed("unspent-authorized-budget.csv", "max_authorized_budget")
GTR  = keyed("levy-rates-and-valuation.csv", "grand_total_rate")
TAXV = keyed("levy-rates-and-valuation.csv", "taxable_valuation")
CRLd = keyed("cash-reserve-levy.csv", "cash_reserve_levy")

def aud(d, y, col):
    r = A[d].get(y); return f(r[col]) if r else None

NARR = {
"Pleasant Valley CSD":"The healthiest profile in the set. Genuine enrollment growth (+1.9%/yr) funded a $27M junior-high build while UAB rose to 22.8% and audited solvency to 22.7% — building from strength, not borrowing against it. Six straight clean audits and a GFOA certificate every year. The model of a growth district living within its means.",
"Waukee CSD":"Iowa's fastest grower (+4.1%/yr; enrollment up ~20% over six years), absorbing a $324M GO-bond multi-school program without strain: UAB near 30% (the highest in the set), positive operating margins, clean audits, and GFOA continuously since 2012. Its 58%-of-cap cash-reserve levy is funding expansion, not plugging holes.",
"Muscatine CSD":"Ranks third despite the sharpest enrollment decline in the group (−10% over six years) by restraining spending: UAB held at 20.5% and solvency at 15%, with six clean audits and GFOA since FY2023. Proof that a shrinking district can stay financially strong if it adjusts staffing and costs as enrollment falls.",
"Davenport CSD":"A turnaround story: from conditional accreditation and multiple material weaknesses (FY2020–21) to a fully clean FY2025 audit, with UAB climbing from 1% to 19% and solvency to 24%. The FY2025 operating margin turned negative as ESSER aid expired, and a $76M SAVE-funded build is underway — the next few years test whether the gains hold.",
"Cedar Rapids CSD":"A solid large urban district: UAB recovered to 13%, solvency 14%, clean RSM audits, and GFOA for 30+ years. FY2025 swung to a −4.5% margin (a ~$10M deficit) on the ESSER cliff. Actively building via SAVE (Trailside Elementary opened); the news-reported ~$18M SBRC at-risk reduction sits outside the audited statements, in the DOM/SBRC record.",
"Dubuque CSD":"Steady and well-run: UAB stable near 11%, solvency 15%, six clean audits, and ASBO recognition. SAVE-funded construction continues despite a −6% enrollment slide. The one nagging item is a certified-enrollment data variance that recurs every year and spiked to 17.0 in FY2025.",
"Ankeny CSD":"A growth district running a tight ship: UAB 14%, solvency recovered to 13.4%, GFOA for 12+ years, with a $130M GO bond on the November-2025 ballot. FY2025 brought its first significant deficiency (enterprise-fund reconciliation) and a rising findings count — internal controls lagging the district's rapid scale.",
"West Des Moines CSD":"Built big — ~$109M of construction placed in service in FY2024 — and is now digesting it: UAB 11%, solvency slid from 19% to 11% on back-to-back operating deficits. Six clean audits, GFOA 30+ years, and a high-wealth tax base provide cushion.",
"Linn-Mar CSD":"Middle of the pack: UAB ~10%, solvency dipped to 6.7% then recovered to 9.5% with a positive FY2025 margin. Building a Performing Arts Center; a multi-year segregation-of-duties deficiency (FY2020–22) was resolved but a new nutrition-fund item appeared in FY2025. Holds ASBO, not GFOA.",
"Burlington CSD":"The clearest 'cash is not authority' case: audited solvency collapsed to 8% on the ESSER cliff plus a $44M high-school renovation, but UAB is among the highest in the set at 28% — it spent down accumulated cash, not spending authority, and levies $0 cash reserve. Six clean audits. Far healthier than a reserve-only read suggests.",
"Johnston CSD":"A similar story to Burlington: solvency fell to 7.7% across three deficit years, but UAB is strong and rising at 21%. The real flag is on the audit side — a new auditor in FY2024 immediately identified three segregation-of-duties deficiencies that persisted into FY2025.",
"Des Moines Independent CSD":"Iowa's largest district has deep reserves (solvency 25%, UAB 18%) but a sharp FY2025 reversal — a −10% margin that drew down ~$40M — and a FY2025 material weakness (OPEB misallocated for ~7 years) pull its scores down. Voters authorized new GO bonds in November 2025, signaling a fresh capital cycle.",
"College CSD (Prairie)":"Building aggressively — GO debt rose from $112M to $149M for a new building, now ~59% of its 5%-of-value debt limit (the highest in the set) — while reserves erode: solvency to 6.6% across four straight deficits, though UAB (14%) is steadier. Clean opinions; the district is at its cash-reserve-levy cap.",
"Waterloo CSD":"Operating distress: audited solvency went negative (−5.6%), the GF balance flipped to −$7M, the FY2025 margin was −13.6%, and UAB halved to 7.5% and is falling — all while issuing $87M of new SAVE debt. Recurring material weaknesses (FY2021, FY2023). The worst operating position in the set.",
"Iowa City CSD":"The distress case on both authority and reporting. UAB went negative in FY2023 — the unlawful, SBRC-trigger condition — and sits near 2% today, while the district levies 57% of its cash-reserve cap just to stay liquid. The FY2023 audit arrived 26 months late with two material weaknesses and ~$1M+ in unreconciled bank accounts; FY2024 and FY2025 remain unfiled and Moody's withdrew the district's rating.",
}

for c in cards:
    d = c["district"]; ys = YEARS
    sv = dict(solvency_series(d))
    c["deep"] = {
        "years": ys,
        "uab_pct":[f(UAB.get((d,y))) for y in ys],
        "uab_dollar":[f(UABd.get((d,y))) for y in ys],
        "max_budget":[f(MAXB.get((d,y))) for y in ys],
        "solvency":[sv.get(y) for y in ys],
        "op_margin":[aud(d,y,"operating_margin_pct") for y in ys],
        "enrollment":[f(ENR.get((d,y))) for y in ys],
        "gf_rev":[aud(d,y,"gf_revenue") for y in ys],
        "gf_exp":[aud(d,y,"gf_expenditure") for y in ys],
        "gf_unassigned":[aud(d,y,"gf_unassigned") for y in ys],
        "gf_total_fb":[aud(d,y,"gf_total_fund_balance") for y in ys],
        "go_debt":[aud(d,y,"go_debt_outstanding") for y in ys],
        "save_debt":[aud(d,y,"save_rev_bonds") for y in ys],
        "capital_add":[aud(d,y,"capital_additions") for y in ys],
        "depreciation":[aud(d,y,"depreciation") for y in ys],
        "cip":[aud(d,y,"construction_in_progress") for y in ys],
        "ipers":[aud(d,y,"ipers_npl") for y in ys],
        "opeb":[aud(d,y,"opeb_liability") for y in ys],
        "unrestricted_np":[aud(d,y,"unrestricted_net_position") for y in ys],
        "cash":[aud(d,y,"cash_and_investments") for y in ys],
        "crl":[f(CRLd.get((d,y))) for y in ys],
        "crl_pct":[f(CRLp.get((d,y))) for y in ys],
        "taxable_val":[f(TAXV.get((d,y))) for y in ys],
        "levy_rate":[f(GTR.get((d,y))) for y in ys],
        "atrisk":[f(ATRISK.get((d,y))) for y in ys],
        # balance sheet + forward commitments (notes layer)
        "net_invest":[f(NOTES.get((d,y),{}).get("net_invest_capital_assets")) for y in ys],
        "restricted_np":[f(NOTES.get((d,y),{}).get("restricted_net_position")) for y in ys],
        "unrestricted_np2":[f(NOTES.get((d,y),{}).get("unrestricted_net_position")) for y in ys],
        "total_np":[f(NOTES.get((d,y),{}).get("total_net_position")) for y in ys],
        "total_assets":[f(NOTES.get((d,y),{}).get("total_assets")) for y in ys],
        "total_liabilities":[f(NOTES.get((d,y),{}).get("total_liabilities")) for y in ys],
        "constr_commit":[f(NOTES.get((d,y),{}).get("construction_commitments")) for y in ys],
    }
    c["narrative"] = NARR.get(d, "")

json.dump(cards, open("/tmp/audit/cards.json", "w"))
print(f"Scored {len(cards)} districts (UAB-anchored).\n")
print(f"{'#':>2} {'composite':>9} {'H':>4} {'Q':>4} {'CS':>4}  {'UAB%':>6} {'solv%':>6}  district / label")
for i, c in enumerate(cards, 1):
    print(f"{i:>2} {c['composite']:>9.2f} {c['health']:>4} {c['quality']:>4} {c['cap_sust']:>4}  "
          f"{(c['uab_last'] or 0):>6.1f} {(c['solv_last'] or 0):>6.1f}  {c['district']:24s} {c['label']}")
