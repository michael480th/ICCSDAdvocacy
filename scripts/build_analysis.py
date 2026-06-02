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
    if not s: return 3.0, None, None, None
    last = s[-1][1]
    ref = s[-4][1] if len(s) >= 4 else s[0][1]
    lvl = band(last, [0, 5, 10, 20], [1, 2, 3, 4, 5])
    trend = last - ref
    tr = band(trend, [-6, -3, 0, 3], [1, 2, 3, 4, 5])
    return round(0.75*lvl + 0.25*tr, 2), last, round(trend, 1), min(v for _, v in s)

def solvency_part(d):
    s = solvency_series(d)
    if not s: return 3.0, None, None
    last = s[-1][1]; ref = s[-4][1] if len(s) >= 4 else s[0][1]
    lvl = band(last, [0, 5, 10, 15, 25], [1, 2, 3, 4, 5, 4.5])
    tr = band(last-ref, [-8, -4, 0, 3], [1, 2, 3, 4, 5])
    return round(0.6*lvl + 0.4*tr, 2), last, round(last-ref, 1)

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
    s = 5.0
    if not opinion_ok: s -= 2.0
    if mw_recent: s -= 1.5
    elif mw_ever: s -= 0.5
    if sd_recent: s -= 0.75
    if rep_recent: s -= 0.5
    if stale: s -= 2.5            # missing-recent-year + stale (Iowa City)
    if d == "Iowa City CSD": s -= 0.5
    if cert: s += 0.5
    return max(1.0, min(5.0, round(s, 1))), cert, mw_recent, sd_recent, stale

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
    uc, uab_last, uab_trend, uab_min = uab_component(d)
    sc, solv_last, solv_trend = solvency_part(d)
    m3 = margin3(d) if margin3(d) is not None else 0.0
    mc = band(m3, [-6, -3, 0, 2], [1, 2, 3, 4, 5])
    H = round(0.50*uc + 0.30*sc + 0.20*mc, 2)
    Q, cert, mw_recent, sd_recent, stale = quality(d)
    cagr, enr_last = enroll(d)
    label, ci = strategic(d, cagr)
    enr_s = 5 if (cagr is not None and cagr > 1) else (3 if (cagr is None or cagr > -1) else 2)
    dh_ratio, dh_room = debt_headroom(d)
    dh_s = 5 if dh_ratio is None else band(dh_ratio, [0.3, 0.5, 0.7, 0.9], [5, 4, 3, 2, 1])
    CS = round(0.40*H + 0.25*enr_s + 0.20*mc + 0.15*dh_s, 2)
    composite = round(0.40*H + 0.35*Q + 0.25*CS, 2)

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
    if mw_recent: flags.append("Recent material weakness")
    if sd_recent: flags.append("Recent significant deficiency")
    if stale: flags.append("FY24/FY25 audit missing (stale)")
    if dh_ratio is not None and dh_ratio > 0.8: flags.append("GO debt near 5% limit")
    last = A[d][max(A[d])]
    if (f(last["gf_unassigned"]) or 0) < 0: flags.append("Negative GF unassigned balance")

    cards.append(dict(
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

json.dump(cards, open("/tmp/audit/cards.json", "w"))
print(f"Scored {len(cards)} districts (UAB-anchored).\n")
print(f"{'#':>2} {'composite':>9} {'H':>4} {'Q':>4} {'CS':>4}  {'UAB%':>6} {'solv%':>6}  district / label")
for i, c in enumerate(cards, 1):
    print(f"{i:>2} {c['composite']:>9.2f} {c['health']:>4} {c['quality']:>4} {c['cap_sust']:>4}  "
          f"{(c['uab_last'] or 0):>6.1f} {(c['solv_last'] or 0):>6.1f}  {c['district']:24s} {c['label']}")
