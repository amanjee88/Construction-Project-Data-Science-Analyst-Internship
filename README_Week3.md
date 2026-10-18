# Week 3 — Predictive Analytics and Risk Modeling for Construction Projects

This addition demonstrates a reproducible Python workflow for estimating construction schedule delays and screening for high cost-overrun risk. **All project records and outcomes in the supplied dataset are simulated.** Model metrics are a training/portfolio demonstration and must not be treated as validated forecasts for real projects.

## Contents

- `data/raw/construction_risk_simulated.csv` — 500 simulated construction-project records.
- `data/processed/week3_delay_regression_metrics.csv` — holdout and five-fold CV metrics for delay regressors.
- `data/processed/week3_cost_overrun_classification_metrics.csv` — classification metrics for cost-overrun risk.
- `data/processed/week3_interpretable_model_coefficients.csv` — coefficients for linear and logistic baseline models.
- `data/processed/week3_holdout_predictions.csv` — holdout targets, predictions, and predicted cost-overrun probabilities.
- `data/processed/week3_scenario_analysis.csv` — illustrative intervention scenarios for one simulated high-risk project.
- `data/processed/week3_risk_model_summary.json` — compact summary of dataset, metrics, caveats, and scenarios.
- `data/processed/week3_data_quality_audit.json` — dataset integrity checks.
- `data/processed/week3_risk_mitigation_register.csv` — risk areas, response actions, owners, and indicators.
- `reports/Week_3_Predictive_Analytics_and_Risk_Modeling.docx` — report prepared for the internship task.
- `reports/figures/week3_*.png` — model diagnostics, classifier comparison, and scenario visualization.
- `submission/Week_3_Submission_Description.txt` — text for the YuvaIntern description field.
- `src/generate_week3_simulated_data.py` — deterministic data generator using seed 73.
- `src/risk_modeling.py` — train/test split, pipelines, five-fold CV, metrics, figures, predictions, and scenarios.
- `src/build_week3_report.py` — report builder from the generated artifacts.
- `tests/test_week3_outputs.py` — lightweight output integrity checks.

## Run from the repository root

Install dependencies from the repository's existing `requirements.txt`, then run:

```bash
python src/generate_week3_simulated_data.py
python src/risk_modeling.py
python src/build_week3_report.py
python -m unittest discover -s tests -p "test_week3_outputs.py"
```

The root requirements from the previous project weeks already cover pandas, NumPy, Matplotlib, scikit-learn, and python-docx. If maintaining a fresh environment, install the packages listed there before running the scripts.

## Method summary

- Delay models: Linear Regression and Random Forest Regressor.
- Cost-risk classification: Logistic Regression and Random Forest Classifier.
- Split: 80% training / 20% holdout; the cost label is stratified.
- Validation: five-fold KFold for regression and five-fold StratifiedKFold for classification, run inside the training sample.
- Metrics: MAE, RMSE, R-squared, ROC-AUC, precision, recall, F1, and accuracy.
- Preprocessing: imputers, numeric standardization where appropriate, categorical one-hot encoding, and scikit-learn pipelines.

## Important caveats

The synthetic relationships are predefined and cannot establish real-world predictive validity or intervention causality. A real deployment would need approved historical project data, dated features available as of each forecast, project/time-aware validation, stakeholder-defined thresholds, performance monitoring, and human review. Safety controls must never be relaxed based on model output.
