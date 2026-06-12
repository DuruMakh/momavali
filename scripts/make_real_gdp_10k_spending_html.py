import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "real_gdp_9000_11000_gov_spending_no_kuwait.csv"
HTML_OUTPUT = ROOT / "outputs" / "real_gdp_9000_11000_gov_spending_interactive.html"


rows = []
with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rows.append(
            {
                "country": row["Country Name"],
                "code": row["Country Code"],
                "year": int(row["Year"]),
                "gdp": float(row["GDP per capita constant 2015 US$"]),
                "spend": float(row["Gov expenditure pct GDP"]),
            }
        )

years = [row["year"] for row in rows]
max_spend = max(row["spend"] for row in rows)
y_max = 80 if max_spend <= 80 else int((max_spend + 9) // 10 * 10)

html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Government spending near $10k real GDP per capita</title>
  <style>
    :root {
      --text: #171717;
      --muted: #686868;
      --grid: #dfdfdf;
      --point: #1f9ac8;
      --panel: #f6f6f6;
      --border: #d8d8d8;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Arial, Helvetica, sans-serif; color: var(--text); background: #fff; }
    main { max-width: 1180px; margin: 0 auto; padding: 22px 20px 30px; }
    h1 { margin: 0 0 6px; font-size: clamp(24px, 3vw, 34px); line-height: 1.12; letter-spacing: 0; }
    .subtitle { margin: 0 0 18px; color: #303030; font-size: 17px; }
    .controls {
      display: grid;
      grid-template-columns: minmax(190px, 1fr) 140px 140px auto;
      gap: 10px;
      align-items: end;
      padding: 12px;
      border: 1px solid var(--border);
      background: var(--panel);
      margin-bottom: 14px;
    }
    label { display: grid; gap: 5px; color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }
    input, button { height: 36px; border: 1px solid #bfbfbf; border-radius: 4px; background: #fff; color: var(--text); font: inherit; padding: 0 10px; }
    button { cursor: pointer; font-weight: 700; }
    .stats { display: flex; flex-wrap: wrap; gap: 14px; color: #333; font-size: 14px; margin: 0 0 6px; }
    .chart-wrap { position: relative; overflow-x: auto; border-bottom: 1px solid #111; }
    svg { display: block; min-width: 920px; width: 100%; height: auto; }
    .grid { stroke: var(--grid); stroke-width: 1; }
    .axis { stroke: #111; stroke-width: 1.5; }
    .tick, .axis-label { fill: var(--muted); }
    .axis-label { font-weight: 700; }
    .point { fill: var(--point); opacity: .88; cursor: pointer; }
    .point.active { fill: #8fd2e8; stroke: #111; stroke-width: 2; opacity: 1; }
    .trend { stroke: #111; stroke-width: 1.5; fill: none; }
    .direct-label { font-size: 15px; fill: #1b1b1b; pointer-events: none; }
    .tooltip {
      position: absolute;
      min-width: 230px;
      pointer-events: none;
      background: #fff;
      border: 1px solid #aaa;
      box-shadow: 0 8px 22px rgba(0,0,0,.14);
      padding: 10px 11px;
      font-size: 13px;
      line-height: 1.45;
      display: none;
      z-index: 2;
    }
    .tooltip strong { display: block; font-size: 14px; margin-bottom: 2px; }
    .note { margin-top: 10px; color: var(--muted); font-size: 13px; }
    @media (max-width: 760px) {
      main { padding: 16px 12px 24px; }
      .controls { grid-template-columns: 1fr 1fr; }
      .controls label:first-child { grid-column: 1 / -1; }
    }
  </style>
</head>
<body>
  <main>
    <h1>Government spending when real GDP per capita was around $10k</h1>
    <p class="subtitle">World Bank `NY.GDP.PCAP.KD`: GDP per capita in constant 2015 US$; filter is $9k-$11k; Kuwait excluded if present.</p>

    <section class="controls" aria-label="Chart controls">
      <label>Search country or code
        <input id="search" type="search" placeholder="e.g. Brazil, BGR, Russia">
      </label>
      <label>From year
        <input id="fromYear" type="number" min="__MIN_YEAR__" max="__MAX_YEAR__" value="__MIN_YEAR__">
      </label>
      <label>To year
        <input id="toYear" type="number" min="__MIN_YEAR__" max="__MAX_YEAR__" value="__MAX_YEAR__">
      </label>
      <button id="reset" type="button">Reset</button>
    </section>

    <div class="stats" id="stats"></div>
    <div class="chart-wrap" id="chartWrap">
      <svg id="chart" viewBox="0 0 1120 660" role="img" aria-labelledby="chartTitle chartDesc">
        <title id="chartTitle">Government spending near ten thousand dollars real GDP per capita</title>
        <desc id="chartDesc">Scatter plot of country-year observations with year on the x axis and government spending as a share of GDP on the y axis.</desc>
      </svg>
      <div class="tooltip" id="tooltip"></div>
    </div>
    <p class="note">Dots are country-year observations where inflation-adjusted GDP per capita was between $9,000 and $11,000 in constant 2015 US dollars. Hover or tap a dot for exact values.</p>
  </main>
  <script>
    const data = __DATA__;
    const minYear = __MIN_YEAR__;
    const maxYear = __MAX_YEAR__;
    const maxSpend = __Y_MAX__;
    const svg = document.getElementById("chart");
    const tooltip = document.getElementById("tooltip");
    const chartWrap = document.getElementById("chartWrap");
    const search = document.getElementById("search");
    const fromYear = document.getElementById("fromYear");
    const toYear = document.getElementById("toYear");
    const stats = document.getElementById("stats");
    const reset = document.getElementById("reset");
    const width = 1120;
    const height = 660;
    const margin = { left: 76, right: 176, top: 34, bottom: 70 };
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    const labelCodes = new Set(["BRA", "VCT", "BGR", "RUS", "GRD", "MEX", "BEL", "HKG"]);
    const fmtPct = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
    const fmtUsd = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

    function xScale(year) {
      return margin.left + ((year - minYear) / (maxYear - minYear)) * plotW;
    }
    function yScale(value) {
      return margin.top + (1 - value / maxSpend) * plotH;
    }
    function el(name, attrs = {}) {
      const node = document.createElementNS("http://www.w3.org/2000/svg", name);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    }
    function regression(rows) {
      if (rows.length < 2) return null;
      const n = rows.length;
      const sx = rows.reduce((sum, d) => sum + d.year, 0);
      const sy = rows.reduce((sum, d) => sum + d.spend, 0);
      const sxx = rows.reduce((sum, d) => sum + d.year * d.year, 0);
      const sxy = rows.reduce((sum, d) => sum + d.year * d.spend, 0);
      const denom = n * sxx - sx * sx;
      if (!denom) return null;
      const slope = (n * sxy - sx * sy) / denom;
      return { slope, intercept: (sy - slope * sx) / n };
    }
    function median(values) {
      const sorted = [...values].sort((a, b) => a - b);
      const mid = Math.floor(sorted.length / 2);
      return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    }
    function filteredRows() {
      const query = search.value.trim().toLowerCase();
      const start = Number(fromYear.value);
      const end = Number(toYear.value);
      return data.filter((d) => {
        const matchText = !query || d.country.toLowerCase().includes(query) || d.code.toLowerCase().includes(query);
        return matchText && d.year >= start && d.year <= end;
      });
    }
    function showTooltip(event, d) {
      tooltip.innerHTML = `<strong>${d.country} (${d.code}), ${d.year}</strong>
        Real GDP per capita: $${fmtUsd.format(d.gdp)}<br>
        Gov spending: ${fmtPct.format(d.spend)}% of GDP`;
      const bounds = chartWrap.getBoundingClientRect();
      tooltip.style.display = "block";
      tooltip.style.left = `${event.clientX - bounds.left + chartWrap.scrollLeft + 14}px`;
      tooltip.style.top = `${event.clientY - bounds.top + 14}px`;
    }
    function hideTooltip() {
      tooltip.style.display = "none";
    }
    function render() {
      const visible = filteredRows();
      svg.replaceChildren();
      const yTicks = [0, 10, 20, 30, 40, 50, 60, 70, 80].filter((tick) => tick <= maxSpend);
      const xTicks = [1960, 1970, 1980, 1990, 2000, 2010, 2020, 2023].filter((tick) => tick >= minYear && tick <= maxYear);

      for (const gy of yTicks) {
        const y = yScale(gy);
        svg.append(el("line", { class: "grid", x1: margin.left, y1: y, x2: width - margin.right, y2: y }));
        svg.append(el("text", { class: "tick", x: margin.left - 12, y: y + 5, "text-anchor": "end" })).textContent = gy;
      }
      for (const gx of xTicks) {
        const x = xScale(gx);
        svg.append(el("line", { class: "grid", x1: x, y1: margin.top, x2: x, y2: height - margin.bottom }));
        svg.append(el("text", { class: "tick", x, y: height - margin.bottom + 32, "text-anchor": "middle" })).textContent = gx;
      }
      svg.append(el("line", { class: "axis", x1: margin.left, y1: height - margin.bottom, x2: width - margin.right, y2: height - margin.bottom }));
      svg.append(el("line", { class: "axis", x1: margin.left, y1: margin.top, x2: margin.left, y2: height - margin.bottom }));
      svg.append(el("text", { class: "axis-label", x: margin.left + 8, y: margin.top + 18 })).textContent = "Government spending (% of GDP)";
      svg.append(el("text", { class: "axis-label", x: width - margin.right, y: height - margin.bottom - 12, "text-anchor": "end" })).textContent = "Year country was near $10k real GDP per capita";

      const fit = regression(visible);
      if (fit) {
        svg.append(el("line", {
          class: "trend",
          x1: xScale(minYear),
          y1: yScale(fit.slope * minYear + fit.intercept),
          x2: xScale(maxYear),
          y2: yScale(fit.slope * maxYear + fit.intercept)
        }));
      }

      for (const d of visible) {
        const point = el("circle", { class: "point", cx: xScale(d.year), cy: yScale(d.spend), r: 4.5, tabindex: 0 });
        point.addEventListener("pointermove", (event) => showTooltip(event, d));
        point.addEventListener("pointerleave", hideTooltip);
        point.addEventListener("focus", (event) => showTooltip(event, d));
        point.addEventListener("blur", hideTooltip);
        svg.append(point);
      }

      const latest = new Map();
      for (const d of visible) {
        if (labelCodes.has(d.code) && (!latest.has(d.code) || d.year > latest.get(d.code).year)) latest.set(d.code, d);
      }
      for (const d of latest.values()) {
        const x = xScale(d.year);
        const y = yScale(d.spend);
        const label = d.code === "VCT" ? "St. Vincent" : d.code === "RUS" ? "Russia" : d.country;
        svg.append(el("circle", { class: "point active", cx: x, cy: y, r: 5 }));
        svg.append(el("text", {
          class: "direct-label",
          x: d.year >= 2020 ? x + 10 : x + 9,
          y: d.spend < 18 ? y + 20 : y - 8
        })).textContent = label;
      }

      const values = visible.map((d) => d.spend);
      const mean = values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1);
      stats.innerHTML = `
        <span><strong>${visible.length}</strong> observations</span>
        <span><strong>${new Set(visible.map((d) => d.code)).size}</strong> countries</span>
        <span><strong>${fmtPct.format(mean || 0)}%</strong> mean spending</span>
        <span><strong>${values.length ? fmtPct.format(median(values)) : "0"}%</strong> median spending</span>
      `;
    }
    search.addEventListener("input", render);
    fromYear.addEventListener("input", render);
    toYear.addEventListener("input", render);
    reset.addEventListener("click", () => {
      search.value = "";
      fromYear.value = minYear;
      toYear.value = maxYear;
      render();
    });
    render();
  </script>
</body>
</html>
"""

html = html.replace("__DATA__", json.dumps(rows, ensure_ascii=False))
html = html.replace("__MIN_YEAR__", str(min(years)))
html = html.replace("__MAX_YEAR__", str(max(years)))
html = html.replace("__Y_MAX__", str(y_max))
HTML_OUTPUT.write_text(html, encoding="utf-8")
print(HTML_OUTPUT)
