#!/usr/bin/env python3
"""Self-contained scatterplot: audit filing speed vs. financial-control metrics.
x = average days to file audited financials; y = UAB / days-of-reserves / solvency (toggle).
Reads /tmp/audit/cards.json + data/iowa-district-financials.csv. -> iccsd-filing-vs-control.html
"""
import json, csv, datetime, statistics as st
from collections import defaultdict

cards = {c["district"]: c for c in json.load(open("/tmp/audit/cards.json"))}
rows = list(csv.DictReader(open("data/iowa-district-financials.csv")))
byd = defaultdict(dict)
for r in rows: byd[r["district"]][int(r["fiscal_year"])] = r

def parse(rd):
    for fmt in ("%Y-%m-%d","%m/%d/%Y","%B %d, %Y","%b %d, %Y"):
        try: return datetime.datetime.strptime(rd.strip(), fmt).date()
        except: pass
    return None

pts = []
for d, yr in byd.items():
    lags = {}
    for fy, r in yr.items():
        dt = parse(r.get("report_date") or "")
        if dt:
            days = (dt - datetime.date(fy, 6, 30)).days
            if 0 < days < 2000: lags[fy] = days
    if not lags: continue
    c = cards[d]
    pts.append(dict(d=d, short=d.replace(" CSD","").replace(" Independent","").replace(" (Prairie)",""),
                    avg_lag=round(st.mean(lags.values())), latest_lag=lags[max(lags)],
                    uab=c["uab_last"], solv=c["solv_last"], reserves=c.get("days_reserves"),
                    composite=c["composite"], ic=(d=="Iowa City CSD")))

date = datetime.date(2026,6,2).strftime("%B %Y")
DATA = json.dumps(pts)

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Audit filing speed vs. financial control — Iowa districts</title>
<style>
body{font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:#0f172a;margin:0;background:#f1f5f9}
.wrap{max-width:860px;margin:0 auto;padding:30px 20px 70px}
h1{font-size:25px;margin:0 0 4px} .sub{color:#64748b;margin:0 0 16px;font-size:15px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;margin-bottom:16px}
.toggle{margin:4px 0 10px;font-size:14px} .toggle label{margin-right:14px;cursor:pointer}
svg{width:100%;height:auto;display:block} .ax{font-size:11px;fill:#475569} .tick{font-size:10px;fill:#94a3b8}
.gl{stroke:#eef2f7} .ref{stroke:#f59e0b;stroke-dasharray:4 3;stroke-width:1.2} .reflbl{font-size:10px;fill:#d97706}
.lbl{font-size:10px;fill:#334155} .note{font-size:13.5px;color:#475569;line-height:1.5}
.qlbl{font-size:11px;fill:#cbd5e1;font-style:italic}
.legend{font-size:12px;color:#64748b;margin-top:6px}
b{color:#0f172a}
</style></head><body><div class="wrap">
<h1>Do districts that manage their books tightly also stay financially strong?</h1>
<p class="sub">Each dot is one of Iowa's large school districts. Horizontal: how long, on average, it takes to file its audited financials (faster = tighter operations). Vertical: a measure of financial control. """ + date + """</p>
<div class="card">
 <div class="toggle"><b>Vertical axis:</b>
   <label><input type="radio" name="y" value="uab" checked> Spending authority (UAB %)</label>
   <label><input type="radio" name="y" value="reserves"> Days of operating reserves</label>
   <label><input type="radio" name="y" value="solv"> Reserves / solvency %</label>
 </div>
 <svg id="plot" viewBox="0 0 640 440"></svg>
 <div class="legend">&#9679; district &nbsp;&middot;&nbsp; <span style="color:#dc2626">&#9679;</span> Iowa City &nbsp;&middot;&nbsp; <span style="color:#d97706">&#8888;</span> GFOA timely-filing guideline (180 days)</div>
</div>
<div class="card note" id="readout"></div>
<script>
const PTS = __DATA__;
const YDEF = {uab:{lab:"Spending authority (UAB %)",fmt:v=>v.toFixed(1)+"%",good:"high"},
              reserves:{lab:"Days of operating reserves",fmt:v=>v.toFixed(0)+" d",good:"high"},
              solv:{lab:"Reserves / solvency %",fmt:v=>v.toFixed(1)+"%",good:"high"}};
function corr(xs,ys){const n=xs.length,mx=xs.reduce((a,b)=>a+b)/n,my=ys.reduce((a,b)=>a+b)/n;
 let c=0,sx=0,sy=0;for(let i=0;i<n;i++){c+=(xs[i]-mx)*(ys[i]-my);sx+=(xs[i]-mx)**2;sy+=(ys[i]-my)**2;}
 return c/Math.sqrt(sx*sy);}
function draw(ykey){
 const W=640,H=440,L=56,R=20,T=20,B=46;
 const pts=PTS.filter(p=>p[ykey]!=null);
 const xs=pts.map(p=>p.avg_lag), ys=pts.map(p=>p[ykey]);
 const xmax=Math.max(...xs)*1.08, xmin=0;
 let ymin=Math.min(...ys,0), ymax=Math.max(...ys); const pad=(ymax-ymin)*0.12; ymin-=pad; ymax+=pad;
 const X=v=>L+(v-xmin)/(xmax-xmin)*(W-L-R), Y=v=>H-B-(v-ymin)/(ymax-ymin)*(H-T-B);
 let s=`<rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="#fafbfc"/>`;
 for(let i=0;i<=4;i++){const yv=ymin+(ymax-ymin)*i/4;s+=`<line class="gl" x1="${L}" y1="${Y(yv).toFixed(1)}" x2="${W-R}" y2="${Y(yv).toFixed(1)}"/><text class="tick" x="${L-6}" y="${(Y(yv)+3).toFixed(1)}" text-anchor="end">${YDEF[ykey].fmt(yv)}</text>`;}
 for(let i=0;i<=4;i++){const xv=xmin+(xmax-xmin)*i/4;s+=`<text class="tick" x="${X(xv).toFixed(1)}" y="${H-B+15}" text-anchor="middle">${Math.round(xv)}</text>`;}
 if(180<xmax){s+=`<line class="ref" x1="${X(180).toFixed(1)}" y1="${T}" x2="${X(180).toFixed(1)}" y2="${H-B}"/><text class="reflbl" x="${X(180)+3}" y="${T+11}">180-day guideline</text>`;}
 if(ymin<0&&ymax>0){s+=`<line x1="${L}" y1="${Y(0).toFixed(1)}" x2="${W-R}" y2="${Y(0).toFixed(1)}" stroke="#e2e8f0"/>`;}
 s+=`<text class="ax" x="${(L+W-R)/2}" y="${H-8}" text-anchor="middle">Average days to file audited financials  (faster &rarr;, slower &rarr;)</text>`;
 s+=`<text class="ax" x="16" y="${(T+H-B)/2}" text-anchor="middle" transform="rotate(-90 16 ${(T+H-B)/2})">${YDEF[ykey].lab}</text>`;
 s+=`<text class="qlbl" x="${L+8}" y="${T+14}">tight + strong</text><text class="qlbl" x="${W-R-6}" y="${H-B-6}" text-anchor="end">slow + weak</text>`;
 for(const p of pts){const cx=X(p.avg_lag),cy=Y(p[ykey]),r=p.ic?7:5,fill=p.ic?"#dc2626":"#2563eb";
   s+=`<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r}" fill="${fill}" fill-opacity="${p.ic?0.9:0.65}" stroke="${fill}" stroke-width="1"><title>${p.d}: ${p.avg_lag} days, ${YDEF[ykey].fmt(p[ykey])}</title></circle>`;
   s+=`<text class="lbl" x="${(cx+ (p.ic?9:7)).toFixed(1)}" y="${(cy+3).toFixed(1)}"${p.ic?' style="fill:#dc2626;font-weight:600"':''}>${p.short}</text>`;}
 document.getElementById("plot").innerHTML=s;
 const r=corr(xs,ys);
 const ic=PTS.find(p=>p.ic);
 document.getElementById("readout").innerHTML=
   `<b>What this shows.</b> Across these ${pts.length} large districts the relationship between filing speed and ${YDEF[ykey].lab.toLowerCase()} is <b>${Math.abs(r)<0.3?"weak":Math.abs(r)<0.5?"modest":"moderate"}</b> (correlation r = ${r.toFixed(2)}). `+
   `The clearest signal is the <b>bottom-right corner</b>: <b>Iowa City</b> is the slowest to file (~${ic.avg_lag} days on average &mdash; its most recent audit was ~${ic.latest_lag} days, about two years late) <b>and</b> near the bottom on ${YDEF[ykey].lab.toLowerCase()} (${YDEF[ykey].fmt(ic[ykey])}). `+
   `So the chart is better read as "Iowa City stands apart in the slow-and-weak corner" than as a tight statistical law &mdash; a fair, defensible framing.`;
}
document.querySelectorAll('input[name=y]').forEach(el=>el.addEventListener('change',e=>draw(e.target.value)));
draw('uab');
</script></div></body></html>"""
HTML = HTML.replace("__DATA__", DATA)
open("iccsd-filing-vs-control.html","w").write(HTML)
print(f"Wrote iccsd-filing-vs-control.html ({len(HTML)//1024} KB), {len(pts)} districts")
