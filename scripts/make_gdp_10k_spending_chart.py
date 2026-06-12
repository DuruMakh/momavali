import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "outputs" / "gdp_9000_11000_gov_spending_all_years.csv"
FILTERED_CSV = ROOT / "outputs" / "gdp_9000_11000_gov_spending_no_kuwait.csv"
SVG_OUTPUT = ROOT / "outputs" / "gdp_9000_11000_gov_spending_by_year.svg"
PNG_OUTPUT = ROOT / "outputs" / "gdp_9000_11000_gov_spending_by_year.png"
HTML_OUTPUT = ROOT / "outputs" / "gdp_9000_11000_gov_spending_interactive.html"
EXCLUDED_CODES = {"KWT"}


def svg_escape(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


rows = []
with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["Country Code"] in EXCLUDED_CODES:
            continue
        rows.append(
            {
                "country": row["Country Name"],
                "code": row["Country Code"],
                "year": int(row["Year"]),
                "gdp": float(row["GDP per capita current US$"]),
                "spend": float(row["Gov expenditure pct GDP"]),
            }
        )

with FILTERED_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["country", "code", "year", "gdp", "spend"])
    writer.writeheader()
    writer.writerows(rows)

years = np.array([r["year"] for r in rows], dtype=float)
spend = np.array([r["spend"] for r in rows], dtype=float)
slope, intercept = np.polyfit(years, spend, 1)

width, height = 1120, 680
left, right, top, bottom = 92, 180, 92, 82
plot_w = width - left - right
plot_h = height - top - bottom
x_min, x_max = min(r["year"] for r in rows), max(r["year"] for r in rows)
y_min, y_max = 0, 75


def x_scale(year):
    return left + ((year - x_min) / (x_max - x_min)) * plot_w


def y_scale(value):
    return top + (1 - ((value - y_min) / (y_max - y_min))) * plot_h


labels = {
    "DMA": "Dominica",
    "BRA": "Brazil",
    "VCT": "St. Vincent",
    "ALB": "Albania",
    "DOM": "Dominican Rep.",
    "BHS": "Bahamas",
    "HKG": "Hong Kong",
    "BEL": "Belgium",
}

latest_by_code = {}
for row in rows:
    existing = latest_by_code.get(row["code"])
    if existing is None or row["year"] > existing["year"]:
        latest_by_code[row["code"]] = row

label_rows = [latest_by_code[code] for code in labels if code in latest_by_code]
label_offsets = {
    "DMA": (10, -7),
    "BRA": (10, -6),
    "VCT": (10, 14),
    "ALB": (-62, 16),
    "DOM": (-104, 16),
    "BHS": (-82, 2),
    "HKG": (10, 24),
    "BEL": (10, -8),
}

grid_x = [1975, 1985, 1995, 2005, 2015, 2023]
grid_y = [0, 15, 30, 45, 60, 75]
trend_points = [
    (x_scale(x_min), y_scale(slope * x_min + intercept)),
    (x_scale(x_max), y_scale(slope * x_max + intercept)),
]

svg_parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    "<style>",
    "text{font-family:Arial, Helvetica, sans-serif;fill:#1b1b1b}",
    ".title{font-size:30px;font-weight:700}",
    ".subtitle{font-size:18px;fill:#333}",
    ".axis-label{font-size:15px;font-weight:700;fill:#6e6e6e}",
    ".tick{font-size:15px;fill:#6e6e6e}",
    ".grid{stroke:#dfdfdf;stroke-width:1}",
    ".axis{stroke:#111;stroke-width:1.5}",
    ".dot{fill:#1f9ac8;opacity:.9}",
    ".focus{fill:#8fd2e8;stroke:#111;stroke-width:2}",
    ".trend{stroke:#111;stroke-width:1.4;fill:none}",
    ".label{font-size:16px}",
    "</style>",
    '<rect width="100%" height="100%" fill="white"/>',
    '<text class="title" x="28" y="42">Government spending when GDP per capita was around $10k</text>',
    '<text class="subtitle" x="28" y="73">GDP per capita $9k-$11k, current USD; Kuwait excluded; spending as % of GDP</text>',
]

for gy in grid_y:
    y = y_scale(gy)
    svg_parts.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{left + plot_w}" y2="{y:.2f}"/>')
    svg_parts.append(f'<text class="tick" x="{left - 14}" y="{y + 5:.2f}" text-anchor="end">{gy}</text>')

for gx in grid_x:
    x = x_scale(gx)
    svg_parts.append(f'<line class="grid" x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_h}"/>')
    svg_parts.append(f'<text class="tick" x="{x:.2f}" y="{top + plot_h + 31}" text-anchor="middle">{gx}</text>')

svg_parts.append(f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>')
svg_parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>')
svg_parts.append(f'<text class="axis-label" x="{left + 8}" y="{top + 18}">Government spending (% of GDP)</text>')
svg_parts.append(f'<text class="axis-label" x="{left + plot_w}" y="{top + plot_h - 12}" text-anchor="end">Year country was near $10k GDP per capita</text>')

for row in rows:
    svg_parts.append(f'<circle class="dot" cx="{x_scale(row["year"]):.2f}" cy="{y_scale(row["spend"]):.2f}" r="4.2"/>')

svg_parts.append(
    f'<path class="trend" d="M {trend_points[0][0]:.2f} {trend_points[0][1]:.2f} L {trend_points[1][0]:.2f} {trend_points[1][1]:.2f}"/>'
)

for row in label_rows:
    x = x_scale(row["year"])
    y = y_scale(row["spend"])
    dx, dy = label_offsets[row["code"]]
    svg_parts.append(f'<circle class="focus" cx="{x:.2f}" cy="{y:.2f}" r="4.6"/>')
    svg_parts.append(f'<text class="label" x="{x + dx:.2f}" y="{y + dy:.2f}">{svg_escape(labels[row["code"]])}</text>')

svg_parts.append(
    f'<text class="subtitle" x="{left}" y="{height - 24}">n={len(rows)} country-year observations; mean={spend.mean():.1f}%, median={np.median(spend):.1f}%</text>'
)
svg_parts.append("</svg>")
SVG_OUTPUT.write_text("\n".join(svg_parts), encoding="utf-8")

image = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(image)
title_font = font(30, True)
subtitle_font = font(18)
tick_font = font(15)
axis_font = font(15, True)
label_font = font(16)

draw.text((28, 14), "Government spending when GDP per capita was around $10k", fill="#111111", font=title_font)
draw.text(
    (28, 54),
    "GDP per capita $9k-$11k, current USD; Kuwait excluded; spending as % of GDP",
    fill="#333333",
    font=subtitle_font,
)
for gy in grid_y:
    y = y_scale(gy)
    draw.line((left, y, left + plot_w, y), fill="#dfdfdf", width=1)
    draw.text((left - 14, y - 8), str(gy), fill="#6e6e6e", font=tick_font, anchor="ra")
for gx in grid_x:
    x = x_scale(gx)
    draw.line((x, top, x, top + plot_h), fill="#dfdfdf", width=1)
    draw.text((x, top + plot_h + 17), str(gx), fill="#6e6e6e", font=tick_font, anchor="ma")
draw.line((left, top + plot_h, left + plot_w, top + plot_h), fill="#111111", width=2)
draw.line((left, top, left, top + plot_h), fill="#111111", width=2)
draw.text((left + 8, top + 4), "Government spending (% of GDP)", fill="#6e6e6e", font=axis_font)
draw.text(
    (left + plot_w, top + plot_h - 28),
    "Year country was near $10k GDP per capita",
    fill="#6e6e6e",
    font=axis_font,
    anchor="ra",
)
for row in rows:
    x = x_scale(row["year"])
    y = y_scale(row["spend"])
    draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#1f9ac8")
draw.line((trend_points[0][0], trend_points[0][1], trend_points[1][0], trend_points[1][1]), fill="#111111", width=2)
for row in label_rows:
    x = x_scale(row["year"])
    y = y_scale(row["spend"])
    dx, dy = label_offsets[row["code"]]
    draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#8fd2e8", outline="#111111", width=2)
    draw.text((x + dx, y + dy - 12), labels[row["code"]], fill="#1b1b1b", font=label_font)
draw.text(
    (left, height - 42),
    f"n={len(rows)} country-year observations; mean={spend.mean():.1f}%, median={np.median(spend):.1f}%",
    fill="#333333",
    font=subtitle_font,
)
image.save(PNG_OUTPUT)

html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Government spending near $10k GDP per capita</title>
  <style>
    :root {
      --text: #171717;
      --muted: #6d6d6d;
      --grid: #dedede;
      --point: #1f9ac8;
      --point-dark: #0f5f79;
      --panel: #f6f6f6;
      --border: #d8d8d8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--text);
      background: #fff;
    }
    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 22px 20px 30px;
    }
    h1 {
      margin: 0 0 6px;
      font-size: clamp(24px, 3vw, 34px);
      line-height: 1.12;
      letter-spacing: 0;
    }
    .subtitle {
      margin: 0 0 18px;
      color: #303030;
      font-size: 17px;
    }
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
    label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }
    input, button {
      height: 36px;
      border: 1px solid #bfbfbf;
      border-radius: 4px;
      background: #fff;
      color: var(--text);
      font: inherit;
      padding: 0 10px;
    }
    button {
      cursor: pointer;
      font-weight: 700;
    }
    .stats {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      color: #333;
      font-size: 14px;
      margin: 0 0 6px;
    }
    .chart-wrap {
      position: relative;
      overflow-x: auto;
      border-bottom: 1px solid #111;
    }
    svg {
      display: block;
      min-width: 920px;
      width: 100%;
      height: auto;
    }
    .grid { stroke: var(--grid); stroke-width: 1; }
    .axis { stroke: #111; stroke-width: 1.5; }
    .tick, .axis-label { fill: var(--muted); }
    .axis-label { font-weight: 700; }
    .point { fill: var(--point); opacity: .88; cursor: pointer; }
    .point.dim { opacity: .18; }
    .point.active { fill: #8fd2e8; stroke: #111; stroke-width: 2; opacity: 1; }
    .trend { stroke: #111; stroke-width: 1.5; fill: none; }
    .direct-label { font-size: 15px; fill: #1b1b1b; pointer-events: none; }
    .tooltip {
      position: absolute;
      min-width: 210px;
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
    .note {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }
    @media (max-width: 760px) {
      main { padding: 16px 12px 24px; }
      .controls { grid-template-columns: 1fr 1fr; }
      .controls label:first-child { grid-column: 1 / -1; }
    }
  </style>
</head>
<body>
  <main>
    <h1>Government spending when GDP per capita was around $10k</h1>
    <p class="subtitle">GDP per capita $9k-$11k, current USD; matched by country and year; Kuwait excluded.</p>

    <section class="controls" aria-label="Chart controls">
      <label>Search country or code
        <input id="search" type="search" placeholder="e.g. Albania, BRA, Korea">
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
        <title id="chartTitle">Government spending near ten thousand dollars GDP per capita</title>
        <desc id="chartDesc">Scatter plot of country-year observations with year on the x axis and government spending as a share of GDP on the y axis.</desc>
      </svg>
      <div class="tooltip" id="tooltip"></div>
    </div>
    <p class="note">Dots are country-year observations where GDP per capita was between $9,000 and $11,000. Hover or tap a dot for exact values.</p>
  </main>
  <script>
    const data = __DATA__;
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
    const minYear = __MIN_YEAR__;
    const maxYear = __MAX_YEAR__;
    const maxSpend = 75;
    const labelCodes = new Set(["DMA", "BRA", "VCT", "ALB", "DOM", "BHS", "HKG", "BEL"]);

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
      const intercept = (sy - slope * sx) / n;
      return { slope, intercept };
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
    function setTooltip(event, d) {
      tooltip.innerHTML = `<strong>${d.country} (${d.code}), ${d.year}</strong>
        GDP per capita: $${fmtUsd.format(d.gdp)}<br>
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

      for (const gy of [0, 15, 30, 45, 60, 75]) {
        const y = yScale(gy);
        svg.append(el("line", { class: "grid", x1: margin.left, y1: y, x2: width - margin.right, y2: y }));
        svg.append(el("text", { class: "tick", x: margin.left - 12, y: y + 5, "text-anchor": "end" })).textContent = gy;
      }
      for (const gx of [1975, 1985, 1995, 2005, 2015, 2023]) {
        const x = xScale(gx);
        svg.append(el("line", { class: "grid", x1: x, y1: margin.top, x2: x, y2: height - margin.bottom }));
        svg.append(el("text", { class: "tick", x, y: height - margin.bottom + 32, "text-anchor": "middle" })).textContent = gx;
      }
      svg.append(el("line", { class: "axis", x1: margin.left, y1: height - margin.bottom, x2: width - margin.right, y2: height - margin.bottom }));
      svg.append(el("line", { class: "axis", x1: margin.left, y1: margin.top, x2: margin.left, y2: height - margin.bottom }));
      svg.append(el("text", { class: "axis-label", x: margin.left + 8, y: margin.top + 18 })).textContent = "Government spending (% of GDP)";
      svg.append(el("text", { class: "axis-label", x: width - margin.right, y: height - margin.bottom - 12, "text-anchor": "end" })).textContent = "Year country was near $10k GDP per capita";

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
        const point = el("circle", {
          class: "point",
          cx: xScale(d.year),
          cy: yScale(d.spend),
          r: 4.5,
          tabindex: 0
        });
        point.addEventListener("pointermove", (event) => setTooltip(event, d));
        point.addEventListener("pointerleave", hideTooltip);
        point.addEventListener("focus", (event) => setTooltip(event, d));
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
        const label = d.code === "DOM" ? "Dominican Rep." : d.code === "VCT" ? "St. Vincent" : d.country;
        svg.append(el("circle", { class: "point active", cx: x, cy: y, r: 5 }));
        svg.append(el("text", {
          class: "direct-label",
          x: d.year >= 2020 ? x + 10 : x + 9,
          y: d.spend < 15 ? y + 20 : y - 8
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
html = html.replace("__MIN_YEAR__", str(x_min))
html = html.replace("__MAX_YEAR__", str(x_max))
HTML_OUTPUT.write_text(html, encoding="utf-8")

print(SVG_OUTPUT)
print(PNG_OUTPUT)
print(HTML_OUTPUT)
print(FILTERED_CSV)
