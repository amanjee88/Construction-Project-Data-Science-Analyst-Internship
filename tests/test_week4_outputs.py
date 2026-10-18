import json
import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

class TestWeek4Outputs(unittest.TestCase):
    def test_summary_clearly_separates_samples(self):
        p = ROOT / "data" / "processed" / "week4_executive_summary.json"
        summary = json.loads(p.read_text(encoding="utf-8"))
        self.assertIn("synthetic", summary["data_caveat"].lower())
        self.assertEqual(summary["week2_eda_sample"]["rows"], 250)
        self.assertEqual(summary["week3_risk_sample"]["rows"], 500)

    def test_week4_figures_exist(self):
        figs = list((ROOT / "reports" / "figures").glob("week4_*.png"))
        self.assertGreaterEqual(len(figs), 7)
        self.assertTrue(all(p.stat().st_size > 10000 for p in figs))

    def test_report_and_submission_description_exist(self):
        report = ROOT / "reports" / "Week_4_Data_Visualization_Reporting_and_Actionable_Insights.docx"
        desc = ROOT / "submission" / "Week_4_Submission_Description.txt"
        self.assertTrue(report.exists() and report.stat().st_size > 100000)
        words = desc.read_text(encoding="utf-8").split()
        self.assertGreaterEqual(len(words), 200)

    def test_risk_and_recommendation_tables_have_rows(self):
        risks = pd.read_csv(ROOT / "data" / "processed" / "week4_risk_priority_register.csv")
        recs = pd.read_csv(ROOT / "data" / "processed" / "week4_recommendation_tracker.csv")
        self.assertGreaterEqual(len(risks), 7)
        self.assertGreaterEqual(len(recs), 5)
        self.assertTrue((risks["priority_score"] > 0).all())

if __name__ == "__main__":
    unittest.main()
