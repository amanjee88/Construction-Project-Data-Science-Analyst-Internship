"""Lightweight integrity checks for Week 3 generated artifacts."""
from pathlib import Path
import json
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

class Week3OutputTests(unittest.TestCase):
    def test_synthetic_dataset_integrity(self):
        df = pd.read_csv(ROOT / "data/raw/construction_risk_simulated.csv")
        self.assertEqual(len(df), 500)
        self.assertTrue(df["project_id"].is_unique)
        self.assertEqual(int(df.isna().sum().sum()), 0)

    def test_model_outputs_exist(self):
        reg = pd.read_csv(ROOT / "data/processed/week3_delay_regression_metrics.csv")
        clf = pd.read_csv(ROOT / "data/processed/week3_cost_overrun_classification_metrics.csv")
        self.assertEqual(len(reg), 2)
        self.assertEqual(len(clf), 2)
        self.assertIn("test_R2", reg.columns)
        self.assertIn("test_ROC_AUC", clf.columns)

    def test_summary_has_synthetic_caveat(self):
        summary = json.loads((ROOT / "data/processed/week3_risk_model_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["dataset_rows"], 500)
        self.assertIn("synthetic", summary["data_caveat"].lower())

    def test_visuals_present(self):
        names = [
            "week3_01_actual_vs_predicted_delay.png",
            "week3_02_delay_model_residuals.png",
            "week3_03_cost_overrun_model_comparison.png",
            "week3_04_cost_overrun_confusion_matrix.png",
            "week3_05_scenario_delay_comparison.png",
        ]
        for name in names:
            self.assertTrue((ROOT / "reports/figures" / name).exists(), name)

if __name__ == "__main__":
    unittest.main()
