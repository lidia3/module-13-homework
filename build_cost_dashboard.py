import json
from decimal import Decimal
from html import escape
from pathlib import Path

data = json.loads(Path("evals/results.json").read_text())
rows = data["results"]
if not rows or any(row.get("error") for row in rows):
    raise SystemExit("Expected completed evaluation runs without errors.")

costs = [Decimal(str(row["cost_usd"])) for row in rows]
total = sum(costs)
average = total / len(costs)
maximum = max(costs) * Decimal("1.25")

bars = []
for i, (row, cost) in enumerate(zip(rows, costs)):
    y = 65 + i * 60
    width = float(cost / maximum) * 620
    bars.append(
        f'<text x="245" y="{y+20}" text-anchor="end">'
        f'{escape(row["case"])}</text>'
        f'<rect x="260" y="{y}" width="{width:.2f}" height="30" '
        f'fill="#2563eb" rx="4"/>'
        f'<text x="{270+width:.2f}" y="{y+20}">${cost:.8f}</text>'
    )

mean_x = 260 + float(average / maximum) * 620
chart = "".join(bars)
page = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Telco Retention — Average Cost per Run</title>
<style>
body {{font-family:Arial,sans-serif;background:#f1f5f9;color:#0f172a;
max-width:1100px;margin:40px auto;padding:20px}}
.card {{background:white;border-radius:12px;padding:24px;margin:20px 0}}
.metrics {{display:flex;gap:40px;flex-wrap:wrap}}
strong {{display:block;font-size:28px;margin-top:10px}}
svg {{width:100%;height:auto}}
text {{font-size:14px;fill:#334155}}
</style>
<h1>Telco Retention — Cost Dashboard</h1>
<p>Recorded local Golden Dataset evaluation · Source: evals/results.json</p>
<div class="card metrics">
<div>Average cost per run<strong>${average:.8f}/run</strong></div>
<div>Total token cost<strong>${total:.8f}</strong></div>
<div>Completed runs<strong>{len(rows)}</strong></div>
</div>
<div class="card">
<h2>Token cost by execution</h2>
<svg viewBox="0 0 1100 450" role="img"
aria-label="Cost of six runs with arithmetic mean">
{chart}
<line x1="{mean_x:.2f}" y1="50" x2="{mean_x:.2f}" y2="400"
stroke="#dc2626" stroke-width="3" stroke-dasharray="7 5"/>
<text x="{mean_x:.2f}" y="30" text-anchor="middle">
Average: ${average:.8f}/run</text>
<text x="260" y="435">Blue bars: individual run cost · Red line: arithmetic mean</text>
</svg>
</div>
<p>This supplementary dashboard summarizes six local runs.
LangSmith screenshots separately show cost percentiles,
span latency, and the complete trace tree.</p>
</html>"""
out = Path("reports/cost_dashboard.html")
out.write_text(page)
print(f"Created: {out}")
print(f"Average: ${average:.8f}/run")
