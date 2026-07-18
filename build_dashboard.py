"""Build a static readiness dashboard from data/log.csv.

Usage: python build_dashboard.py
Reads the normalized log schema (see PRD §6); ingestion adapters must write
that schema — scoring and rendering never change per source.
Stdlib only.
"""
import csv
import json
import statistics
from pathlib import Path

LOG = Path(__file__).parent / "data" / "log.csv"
OUT = Path(__file__).parent / "dashboard.html"

METRICS = ["sleep_hours", "sleep_quality", "hrv_ms", "resting_hr", "steps", "stress"]


def load_rows():
    with open(LOG, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for m in METRICS:
            v = r.get(m, "").strip()
            r[m] = float(v) if v else None
    rows.sort(key=lambda r: r["date"])
    return rows


def baseline(rows, idx, metric, window):
    vals = [r[metric] for r in rows[max(0, idx - window):idx] if r[metric] is not None]
    return statistics.mean(vals) if vals else None


def score_day(rows, idx):
    """Return (score, parts) where parts = [(metric, earned, weight, detail)]."""
    r = rows[idx]
    parts = []

    def add(metric, weight, frac, detail):
        frac = max(0.0, min(1.0, frac))
        parts.append({"metric": metric, "earned": frac * weight, "weight": weight, "detail": detail})

    if r["sleep_hours"] is not None:
        add("sleep_hours", 30, r["sleep_hours"] / 7.5,
            f"{r['sleep_hours']:.1f}h slept (target 7.5h)")
    hrv_base = baseline(rows, idx, "hrv_ms", 7)
    if r["hrv_ms"] is not None and hrv_base:
        add("hrv_ms", 25, r["hrv_ms"] / hrv_base,
            f"HRV {r['hrv_ms']:.0f}ms vs 7-day baseline {hrv_base:.0f}ms")
    rhr_base = baseline(rows, idx, "resting_hr", 7)
    if r["resting_hr"] is not None and rhr_base:
        # at/below baseline = full; each % above baseline costs 5% of the weight
        pct_above = (r["resting_hr"] - rhr_base) / rhr_base
        add("resting_hr", 20, 1 - max(0, pct_above) * 5,
            f"Resting HR {r['resting_hr']:.0f} vs 7-day baseline {rhr_base:.0f}")
    if r["stress"] is not None:
        add("stress", 15, 1 - r["stress"] / 100,
            f"Stress {r['stress']:.0f}/100")
    if r["sleep_quality"] is not None:
        add("sleep_quality", 10, r["sleep_quality"] / 100,
            f"Sleep quality {r['sleep_quality']:.0f}/100")

    total_weight = sum(p["weight"] for p in parts)
    if not total_weight:
        return None, []
    # redistribute missing metrics' weight proportionally
    score = round(sum(p["earned"] for p in parts) / total_weight * 100)
    return score, parts


ACTION_TEMPLATES = {
    "sleep_hours": "Sleep was short — aim for bed 30–60 min earlier tonight.",
    "sleep_quality": "Sleep quality was poor — cut screens/caffeine late, cool the room.",
    "hrv_ms": "HRV below your baseline — keep today easy (walk/mobility, no hard training).",
    "resting_hr": "Resting HR elevated vs baseline — hydrate, keep intensity low, watch for illness.",
    "stress": "Stress ran high — schedule a 10-min walk or breathing break today.",
    "steps": "Movement was low — get a walk in early.",
}

GREEN_ACTIONS = [
    "Recovery looks good — cleared to push in today's training.",
    "Bank the streak: keep bedtime consistent tonight.",
    "Good day for a harder or longer session if planned.",
]


def actions_for(score, parts):
    if score is None:
        return ["No data for today — check the pipeline."]
    if score >= 75:
        return GREEN_ACTIONS
    losses = sorted(parts, key=lambda p: p["weight"] - p["earned"], reverse=True)
    out = []
    for p in losses[:3]:
        if p["weight"] - p["earned"] < 1:
            continue
        out.append(f"{ACTION_TEMPLATES[p['metric']]} ({p['detail']})")
    return out or GREEN_ACTIONS


def color(score):
    if score is None:
        return "#999"
    return "#22a35a" if score >= 75 else "#e0a800" if score >= 50 else "#d9453d"


def build():
    rows = load_rows()
    idx = len(rows) - 1
    score, parts = score_day(rows, idx)
    today = rows[idx]
    acts = actions_for(score, parts)

    chart_data = {
        m: {
            "dates": [r["date"] for r in rows],
            "values": [r[m] for r in rows],
            "baseline": [baseline(rows, i, m, 7) for i in range(len(rows))],
        }
        for m in ["sleep_hours", "hrv_ms", "resting_hr", "steps"]
    }
    table = [[r["date"]] + [("" if r[m] is None else r[m]) for m in METRICS] + [r.get("notes", "")] for r in rows]

    payload = json.dumps({"charts": chart_data, "table": table})
    html = TEMPLATE
    html = html.replace("__DATE__", today["date"])
    html = html.replace("__SCORE__", "–" if score is None else str(score))
    html = html.replace("__COLOR__", color(score))
    html = html.replace("__ACTIONS__", "".join(f"<li>{a}</li>" for a in acts))
    html = html.replace("__DATA__", payload)
    OUT.write_text(html, encoding="utf-8")
    print(f"{today['date']}: readiness {score} -> {OUT.name}")


TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Readiness Dashboard</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#222}
.score{display:flex;align-items:center;gap:1.5rem}
.ring{width:120px;height:120px;border-radius:50%;border:10px solid __COLOR__;display:flex;align-items:center;justify-content:center;font-size:2.2rem;font-weight:700}
ul.actions li{margin:.4rem 0}
.chart{margin:1.5rem 0}
.chart h3{margin:0 0 .3rem}
svg{width:100%;height:140px;background:#fafafa;border:1px solid #eee}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{border:1px solid #ddd;padding:.3rem .5rem;text-align:right}
th{cursor:pointer;background:#f4f4f4}
td:first-child,th:first-child{text-align:left}
#tip{position:fixed;background:#222;color:#fff;padding:2px 8px;border-radius:4px;font-size:.8rem;pointer-events:none;display:none}
</style></head><body>
<div id="tip"></div>
<h1>Readiness — __DATE__</h1>
<div class="score"><div class="ring">__SCORE__</div>
<div><h2>Today's actions</h2><ul class="actions">__ACTIONS__</ul></div></div>
<h2>30-day trends</h2><div id="charts"></div>
<h2>Raw log</h2><table id="log"></table>
<script>
const DATA=__DATA__;
const tip=document.getElementById('tip');
const LABELS={sleep_hours:'Sleep (h)',hrv_ms:'HRV (ms)',resting_hr:'Resting HR',steps:'Steps'};
const W=880,H=140,P=8;
for(const [m,d] of Object.entries(DATA.charts)){
  const div=document.createElement('div');div.className='chart';
  div.innerHTML=`<h3>${LABELS[m]}</h3>`;
  const vals=d.values.filter(v=>v!==null).concat(d.baseline.filter(v=>v!==null));
  const min=Math.min(...vals),max=Math.max(...vals),span=(max-min)||1;
  const x=i=>P+i*(W-2*P)/(d.dates.length-1);
  const y=v=>H-P-(v-min)*(H-2*P)/span;
  const path=arr=>arr.map((v,i)=>v===null?null:`${x(i)},${y(v)}`).map((p,i,a)=>p===null?'':((i===0||a[i-1]==='')?'M':'L')+p).join(' ');
  let svg=`<svg viewBox="0 0 ${W} ${H}">`;
  svg+=`<path d="${path(d.baseline)}" fill="none" stroke="#bbb" stroke-dasharray="4 3"/>`;
  svg+=`<path d="${path(d.values)}" fill="none" stroke="#2a6fdb" stroke-width="2"/>`;
  d.values.forEach((v,i)=>{if(v!==null)svg+=`<circle cx="${x(i)}" cy="${y(v)}" r="3.5" fill="#2a6fdb" data-t="${d.dates[i]}: ${v}"/>`;});
  svg+='</svg>';
  div.innerHTML+=svg;
  document.getElementById('charts').appendChild(div);
}
document.addEventListener('mouseover',e=>{const t=e.target.getAttribute&&e.target.getAttribute('data-t');
  if(t){tip.textContent=t;tip.style.display='block';}});
document.addEventListener('mousemove',e=>{tip.style.left=e.clientX+12+'px';tip.style.top=e.clientY+12+'px';});
document.addEventListener('mouseout',()=>tip.style.display='none');
const HEAD=['date','sleep_hours','sleep_quality','hrv_ms','resting_hr','steps','stress','notes'];
let rows=DATA.table.slice(),asc=false,sortCol=0;
function renderTable(){
  const t=document.getElementById('log');
  t.innerHTML='<tr>'+HEAD.map((h,i)=>`<th onclick="sortBy(${i})">${h}</th>`).join('')+'</tr>'+
    rows.map(r=>'<tr>'+r.map(c=>`<td>${c}</td>`).join('')+'</tr>').join('');
}
function sortBy(i){
  asc=sortCol===i?!asc:true;sortCol=i;
  rows.sort((a,b)=>{const x=a[i],y=b[i];
    const n=parseFloat(x),m2=parseFloat(y);
    const c=(!isNaN(n)&&!isNaN(m2))?n-m2:String(x).localeCompare(String(y));
    return asc?c:-c;});
  renderTable();
}
renderTable();
</script></body></html>
"""

if __name__ == "__main__":
    build()
