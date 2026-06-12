import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GDP_INPUT = ROOT / "worldbank_gdp_per_capita_constant_2015_usd.csv"
SPENDING_INPUT = ROOT / "historical-gov-spending-gdp" / "historical-gov-spending-gdp.csv"
OUTPUT_DIR = ROOT / "outputs"
ALL_OUTPUT = OUTPUT_DIR / "real_gdp_9000_11000_gov_spending_all_years.csv"
NO_KUWAIT_OUTPUT = OUTPUT_DIR / "real_gdp_9000_11000_gov_spending_no_kuwait.csv"
LATEST_OUTPUT = OUTPUT_DIR / "real_gdp_9000_11000_gov_spending_2023.csv"


def read_gdp():
    rows = {}
    with GDP_INPUT.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[(row["Country Code"], int(row["Year"]))] = {
                "Country Name": row["Country Name"],
                "Country Code": row["Country Code"],
                "Year": int(row["Year"]),
                "GDP per capita constant 2015 US$": float(row["GDP per capita constant 2015 US$"]),
            }
    return rows


def read_spending():
    rows = {}
    with SPENDING_INPUT.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["Government expenditure (% of GDP)"]:
                continue
            rows[(row["Code"], int(row["Year"]))] = {
                "Spending Entity": row["Entity"],
                "Gov expenditure pct GDP": float(row["Government expenditure (% of GDP)"]),
            }
    return rows


OUTPUT_DIR.mkdir(exist_ok=True)
gdp = read_gdp()
spending = read_spending()

matched = []
for key, gdp_row in gdp.items():
    spending_row = spending.get(key)
    if not spending_row:
        continue
    value = gdp_row["GDP per capita constant 2015 US$"]
    if 9000 <= value <= 11000:
        matched.append({**gdp_row, **spending_row})

matched.sort(key=lambda row: (row["Year"], row["Country Name"]))
no_kuwait = [row for row in matched if row["Country Code"] != "KWT"]
latest = [row for row in no_kuwait if row["Year"] == 2023]
latest.sort(key=lambda row: row["Gov expenditure pct GDP"], reverse=True)

fieldnames = [
    "Country Name",
    "Country Code",
    "Year",
    "GDP per capita constant 2015 US$",
    "Gov expenditure pct GDP",
]

for path, rows in [
    (ALL_OUTPUT, matched),
    (NO_KUWAIT_OUTPUT, no_kuwait),
    (LATEST_OUTPUT, latest),
]:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{key: row[key] for key in fieldnames} for row in rows])

values = [row["Gov expenditure pct GDP"] for row in no_kuwait]
values_sorted = sorted(values)
mid = len(values_sorted) // 2
median = values_sorted[mid] if len(values_sorted) % 2 else (values_sorted[mid - 1] + values_sorted[mid]) / 2

print(f"matched_rows_including_kuwait={len(matched)}")
print(f"matched_rows_excluding_kuwait={len(no_kuwait)}")
print(f"countries_excluding_kuwait={len({row['Country Code'] for row in no_kuwait})}")
print(f"year_range={min(row['Year'] for row in no_kuwait)}-{max(row['Year'] for row in no_kuwait)}")
print(f"mean_spending_pct={sum(values) / len(values):.3f}")
print(f"median_spending_pct={median:.3f}")
print(f"latest_2023_rows={len(latest)}")
for row in latest:
    print(
        f"{row['Country Name']} ({row['Country Code']}), "
        f"{row['GDP per capita constant 2015 US$']:.2f}, "
        f"{row['Gov expenditure pct GDP']:.2f}%"
    )
