import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "worldbank_gdp_per_capita_constant_2015_usd.json"
OUTPUT = ROOT / "worldbank_gdp_per_capita_constant_2015_usd.csv"
SUMMARY = ROOT / "worldbank_gdp_per_capita_constant_2015_usd_summary.json"


data = json.loads(INPUT.read_text(encoding="utf-8-sig"))
api_meta, records = data
rows = []
indicator = None
source = None

for record in records:
    if indicator is None:
        indicator = record.get("indicator", {})
        source = record.get("source", {})
    value = record.get("value")
    if value is None:
        continue
    rows.append(
        {
            "Country Name": record["country"]["value"],
            "Country Code": record.get("countryiso3code") or record["country"]["id"],
            "Year": int(record["date"]),
            "GDP per capita constant 2015 US$": float(value),
            "Indicator Code": indicator.get("id", "NY.GDP.PCAP.KD"),
            "Indicator Name": indicator.get("value", ""),
        }
    )

rows.sort(key=lambda row: (row["Country Code"], row["Year"]))

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

summary = {
    "api_meta": api_meta,
    "indicator": indicator,
    "source": source,
    "rows": len(rows),
    "countries": len({row["Country Code"] for row in rows}),
    "min_year": min(row["Year"] for row in rows),
    "max_year": max(row["Year"] for row in rows),
}
SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
