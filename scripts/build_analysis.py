#!/usr/bin/env python3
"""
Build the Iowa district financial benchmark from the per-district extraction CSVs.

Inputs : /tmp/audit/out/*.csv  (one pipe-delimited file per district, produced by the
         per-district extraction agents; schema documented in
         iowa-district-financial-analysis-framework.md)
Outputs: data/iowa-district-financials.csv   (master, one row per district-year)
         data/iowa-district-scorecards.csv    (one row per district: derived metrics + scores)
         iowa-district-financial-benchmark.html (the report)

Scoring follows iowa-district-financial-analysis-framework.md:
  Pillar A (Health) 40% + Pillar C (Operational Quality) 35% + Capital-Sustainability 25%.
  Strategic posture is a LABEL reported alongside, not folded into the composite.
All 15 districts are treated as one peer set ("Iowa's large districts"); Iowa absolute
benchmark bands are the primary basis, with size/trajectory reported as context. Documented.
"""
import csv, glob, os, json

SRC = "/tmp/audit/out"
OUT_DATA = "data"
os.makedirs(OUT_DATA, exist_ok=True)

# ---- display-name normalization & recognition overrides (from audited intro sections) ----
NAME = {"College Community School District": "College CSD (Prairie)"}
ASBO = {"Dubuque CSD", "Linn-Mar CSD"}  # hold ASBO Cert of Excellence (not GFOA) per their ACFRs

def f(x):
    x = (x or "").strip().replace(",", "").replace("$", "").replace("%", "")
    if x in ("", "N/A", "NA", "-"): return None
    try: return float(x)
    except ValueError: return None

# ---- load ----
rows = []
for path in sorted(glob.glob(f"{SRC}/*.csv")):
    with open(path) as fh:
        for d in csv.DictReader(fh, delimiter="|"):
            d["district"] = NAME.get(d["district"].strip(), d["district"].strip())
            rows.append(d)

from collections import defaultdict
bydist = defaultdict(list)
for r in rows:
    bydist[r["district"]].append(r)
for d in bydist:
    bydist[d].sort(key=lambda r: r["fiscal_year"])

# ---- write master (cleaned + per-pupil) ----
master_cols = list(rows[0].keys())
extra = ["debt_per_pupil", "gf_rev_per_pupil"]
with open(f"{OUT_DATA}/iowa-district-financials.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(master_cols + extra)
    for r in rows:
        enr = f(r.get("certified_enrollment"))
        go = f(r.get("go_debt_outstanding")) or 0
        save = f(r.get("save_rev_bonds")) or 0
        rev = f(r.get("gf_revenue"))
        dpp = round((go + save) / enr) if enr else ""
        rpp = round(rev / enr) if (enr and rev) else ""
        w.writerow([r[c] for c in master_cols] + [dpp, rpp])

# ---- scoring helpers ----
def band(v, cuts, scores):
    for c, s in zip(cuts, scores):
        if v < c: return s
    return scores[-1]

def health_score(rs):
    solv = [f(r["solvency_ratio_pct"]) for r in rs if f(r["solvency_ratio_pct"]) is not None]
    marg = [f(r["operating_margin_pct"]) for r in rs if f(r["operating_margin_pct"]) is not None]
    solv_last = solv[-1]
    solv_ref = solv[-4] if len(solv) >= 4 else solv[0]          # ~3 yrs ago
    marg3 = sum(marg[-3:]) / len(marg[-3:])
    s_level = band(solv_last, [0, 5, 10, 15, 25], [1, 2, 3, 4, 5, 4.5])
    s_marg  = band(marg3,     [-6, -3, 0, 2],      [1, 2, 3, 4, 5])
    s_trend = band(solv_last - solv_ref, [-8, -4, 0, 3], [1, 2, 3, 4, 5])
    return round(0.40*s_level + 0.35*s_marg + 0.25*s_trend, 1), solv_last, solv_ref, round(marg3,1)

def quality_score(d, rs):
    latest = rs[-1]
    last3 = rs[-3:]
    last2 = rs[-2:]
    yn = lambda r, k: (r.get(k, "") or "").strip().upper().startswith("Y")
    opinion_ok = "unmod" in (latest.get("opinion_type", "").lower())
    mw_recent = any(yn(r, "material_weakness") for r in last3)
    mw_ever   = any(yn(r, "material_weakness") for r in rs)
    sd_recent = any(yn(r, "significant_deficiency") for r in last2)
    rep_recent = any(yn(r, "repeat_finding") for r in last2)
    cert = yn(latest, "gfoa_cert") or d in ASBO
    stale = int(latest["fiscal_year"]) < 2025           # only Iowa City
    missing_recent = stale                                # FY24/FY25 unfiled
    s = 5.0
    if not opinion_ok: s -= 2.0
    if mw_recent: s -= 1.5
    elif mw_ever: s -= 0.5
    if sd_recent: s -= 0.75
    if rep_recent: s -= 0.5
    if stale: s -= 1.5
    if missing_recent: s -= 1.0
    if d == "Iowa City CSD": s -= 0.5   # documented $35M restatement + 26-mo-late + bank recs
    if cert: s += 0.5
    return max(1.0, min(5.0, round(s, 1))), cert, mw_recent, sd_recent, stale

def enroll_traj(rs):
    e = [(int(r["fiscal_year"]), f(r["certified_enrollment"])) for r in rs if f(r["certified_enrollment"])]
    if len(e) < 2: return None, None
    (y0, e0), (y1, e1) = e[0], e[-1]
    if y1 == y0 or not e0: return None, e1
    cagr = (e1 / e0) ** (1 / (y1 - y0)) - 1
    return round(cagr * 100, 2), e1

def capex_intensity(rs):
    ratios = []
    for r in rs[-3:]:
        ca, dep = f(r["capital_additions"]), f(r["depreciation"])
        if ca is not None and dep: ratios.append(ca / dep)
    return round(sum(ratios) / len(ratios), 2) if ratios else None

def strategic(rs):
    cagr, enr = enroll_traj(rs)
    ci = capex_intensity(rs)
    go = [f(r["go_debt_outstanding"]) or 0 for r in rs]
    save = [f(r["save_rev_bonds"]) or 0 for r in rs]
    debt0, debt1 = go[0] + save[0], go[-1] + save[-1]
    big_recent_issue = any((f(rs[i]["save_rev_bonds"]) or 0) + (f(rs[i]["go_debt_outstanding"]) or 0)
                           - ((f(rs[i-1]["save_rev_bonds"]) or 0) + (f(rs[i-1]["go_debt_outstanding"]) or 0)) > 10_000_000
                           for i in range(max(1, len(rs)-3), len(rs)))
    building = (ci and ci > 1.2) or big_recent_issue or debt1 > debt0 * 1.05
    if cagr is not None and cagr > 1.0 and building:
        label = "Building — growth-driven"
    elif building and cagr is not None and cagr < -1.0:
        label = "Building — renewal (declining enrollment)"
    elif building:
        label = "Building — renewal"
    elif cagr is not None and cagr < -1.5:
        label = "Contracting"
    else:
        label = "Maintain"
    return label, cagr, enr, ci

def cap_sustainability(health, cagr, marg3):
    enr_s = 5 if (cagr is not None and cagr > 1) else (3 if (cagr is None or cagr > -1) else 2)
    marg_s = band(marg3, [-6, -3, 0, 2], [1, 2, 3, 4, 5])
    return round(0.5*health + 0.3*enr_s + 0.2*marg_s, 1)

SIZE = lambda e: (">15k" if e and e > 15000 else "10–15k" if e and e > 10000
                  else "5–10k" if e and e > 5000 else "<5k")

# ---- build scorecards ----
cards = []
for d, rs in bydist.items():
    H, solv_last, solv_ref, marg3 = health_score(rs)
    Q, cert, mw_recent, sd_recent, stale = quality_score(d, rs)
    label, cagr, enr, ci = strategic(rs)
    CS = cap_sustainability(H, cagr, marg3)
    composite = round(0.40*H + 0.35*Q + 0.25*CS, 2)

    flags = []
    if solv_last < 0: flags.append("Negative solvency")
    elif solv_last < 5: flags.append("Solvency <5%")
    if marg3 < -2: flags.append("Multi-yr operating deficit")
    if solv_last - solv_ref < -8: flags.append("Reserve drawdown >8pp")
    if mw_recent: flags.append("Recent material weakness")
    if sd_recent: flags.append("Recent significant deficiency")
    if stale: flags.append("FY24/FY25 audit missing (stale)")
    last = rs[-1]
    if (f(last["gf_unassigned"]) or 0) < 0: flags.append("Negative GF unassigned balance")

    cards.append({
        "district": d, "n_years": len(rs),
        "fy_first": rs[0]["fiscal_year"], "fy_last": rs[-1]["fiscal_year"],
        "enrollment": enr, "size": SIZE(enr), "enr_cagr": cagr,
        "solv_last": round(solv_last,1), "solv_ref": round(solv_ref,1), "marg3": marg3,
        "capex_intensity": ci, "label": label,
        "health": H, "quality": Q, "cap_sust": CS, "composite": composite,
        "cert": cert, "flags": flags,
        "opinion_last": rs[-1].get("opinion_type",""),
        "solv_series": [f(r["solvency_ratio_pct"]) for r in rs],
        "marg_series": [f(r["operating_margin_pct"]) for r in rs],
        "years": [r["fiscal_year"] for r in rs],
        "debt_last": round(((f(rs[-1]["go_debt_outstanding"]) or 0)+(f(rs[-1]["save_rev_bonds"]) or 0))/1e6,1),
        "sbpct": next((f(r["salary_benefit_pct_gf"]) for r in reversed(rs) if f(r["salary_benefit_pct_gf"])), None),
    })

cards.sort(key=lambda c: c["composite"], reverse=True)

with open(f"{OUT_DATA}/iowa-district-scorecards.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["rank","district","size","enrollment","enr_cagr_pct","strategic_label",
                "solvency_last_pct","solvency_3yr_ago_pct","op_margin_3yr_avg_pct","capex_intensity",
                "health_score","quality_score","capital_sustainability","composite","flags"])
    for i,c in enumerate(cards,1):
        w.writerow([i,c["district"],c["size"],c["enrollment"],c["enr_cagr"],c["label"],
                    c["solv_last"],c["solv_ref"],c["marg3"],c["capex_intensity"],
                    c["health"],c["quality"],c["cap_sust"],c["composite"],"; ".join(c["flags"])])

json.dump(cards, open("/tmp/audit/cards.json","w"))
print(f"Scored {len(cards)} districts. Wrote master + scorecards CSVs.")
for c in cards:
    print(f"  {c['composite']:.2f}  H{c['health']} Q{c['quality']} CS{c['cap_sust']}  "
          f"{c['district']:24s} {c['label']}")
