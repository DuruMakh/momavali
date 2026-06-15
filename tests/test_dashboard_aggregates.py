import json
import re
import unittest
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "outputs" / "government_spending_real_ppp_10k_dashboard.html"
OECD_REVENUE = ROOT / "oecd_all_countries_tax_revenue_gdp_1965_onward.csv"
MADDISON_GDP = ROOT / "maddison_gdp_per_capita.csv"
SPENDING_DOWNLOAD = ROOT / "outputs" / "government_spending_real_ppp_10k_dashboard_spending.csv"
REVENUE_DOWNLOAD = ROOT / "outputs" / "government_spending_real_ppp_10k_dashboard_revenue.csv"
OECD_DOWNLOAD = ROOT / "outputs" / "government_spending_real_ppp_10k_dashboard_oecd_revenue_1965.csv"


def extract_datasets():
    html = DASHBOARD.read_text(encoding="utf-8")
    match = re.search(r"const datasets = (.*?);\n", html, re.S)
    assert match, "Dashboard must embed datasets"
    return json.loads(match.group(1)), html


def median(values):
    sorted_values = sorted(values)
    mid = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[mid]
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2


def expected_oecd_1965_rows():
    revenue_rows = {}
    with OECD_REVENUE.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["year"] == "1965":
                revenue_rows[row["country_code"]] = row

    gdp_rows = {}
    with MADDISON_GDP.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Year"] == "1965":
                gdp_rows[row["Code"]] = row

    rows = []
    for code in sorted(set(revenue_rows) & set(gdp_rows)):
        revenue_row = revenue_rows[code]
        gdp_row = gdp_rows[code]
        rows.append(
            {
                "country": revenue_row["country"],
                "code": code,
                "year": 1965,
                "gdp": float(gdp_row["GDP per capita"]),
                "value": float(revenue_row["tax_revenue_pct_gdp"]),
            }
        )
    return rows


def read_csv_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stringify_rows(rows, value_key, include_code=False):
    output = []
    for row in rows:
        item = {
            "country": row["country"],
            "gdp_per_capita_2011_intl": str(row["gdp"]),
            value_key: str(row["value"]),
            "year": str(row["year"]),
        }
        if include_code:
            item["country_code"] = row["code"]
        output.append(item)
    return output


class DashboardAggregateTests(unittest.TestCase):
    def test_spending_kpis_exclude_countries_reaching_10k_before_1950(self):
        datasets, html = extract_datasets()
        spending = datasets["spending"]
        aggregate_rows = [row for row in spending if row["year"] >= 1950]

        self.assertTrue(any(row["year"] < 1950 for row in spending))
        self.assertIn(
            'const getAggregateData = () => activeMetric === "spending" ? getData().filter(d => d.year >= 1950) : getData();',
            html,
        )

        aggregate_values = [row["value"] for row in aggregate_rows]
        full_values = [row["value"] for row in spending]

        self.assertEqual(len(aggregate_values), 22)
        self.assertEqual(round(sum(aggregate_values) / len(aggregate_values), 1), 22.3)
        self.assertEqual(round(median(aggregate_values), 1), 20.8)
        self.assertNotEqual(round(sum(full_values) / len(full_values), 1), 22.3)
        self.assertNotEqual(round(median(full_values), 1), 20.8)

    def test_oecd_revenue_tab_uses_1965_tax_revenue_and_1965_gdp_per_capita(self):
        datasets, html = extract_datasets()
        self.assertIn("REVENUE OECD", html)
        self.assertIn('"oecdRevenue"', html)
        self.assertIn('const getScatterX = (d) => activeMetric === "oecdRevenue" ? d.gdp : d.year;', html)
        self.assertIn('const scatterUsesGdp = () => activeMetric === "oecdRevenue";', html)

        actual = sorted(datasets["oecdRevenue"], key=lambda row: row["country"])
        expected = sorted(expected_oecd_1965_rows(), key=lambda row: row["country"])

        self.assertEqual(len(actual), 18)
        self.assertEqual(actual, expected)
        self.assertTrue(all(row["year"] == 1965 for row in actual))
        self.assertEqual(actual[0]["country"], "Australia")
        self.assertEqual(actual[-1]["country"], "United Kingdom")

    def test_dashboard_exposes_downloads_for_all_three_tab_datasets(self):
        datasets, html = extract_datasets()

        self.assertIn('government_spending_real_ppp_10k_dashboard_spending.csv', html)
        self.assertIn('government_spending_real_ppp_10k_dashboard_revenue.csv', html)
        self.assertIn('government_spending_real_ppp_10k_dashboard_oecd_revenue_1965.csv', html)

        spending_rows = read_csv_rows(SPENDING_DOWNLOAD)
        revenue_rows = read_csv_rows(REVENUE_DOWNLOAD)
        oecd_rows = read_csv_rows(OECD_DOWNLOAD)

        self.assertEqual(
            spending_rows,
            stringify_rows(datasets["spending"], "government_spending_pct_gdp"),
        )
        self.assertEqual(
            revenue_rows,
            stringify_rows(datasets["revenue"], "government_revenue_pct_gdp"),
        )
        self.assertEqual(
            oecd_rows,
            stringify_rows(datasets["oecdRevenue"], "tax_revenue_pct_gdp", include_code=True),
        )
