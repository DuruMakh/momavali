import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "outputs" / "government_spending_real_ppp_10k_dashboard.html"


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
