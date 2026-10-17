# Week 2 — Exploratory Data Analysis and Statistical Modeling

This Week 2 extension builds on the Construction Project Data Science internship repository. It contains an end-to-end, reproducible EDA and regression example for construction performance indicators.

## Data transparency
`data/raw/construction_projects_eda_simulated.csv` contains 250 simulated project rows created with a fixed random seed. It is an educational dataset and is not a collection of real projects or a representation of actual industry outcomes. Do not present these values as observed construction data.

## Main deliverables
- `reports/Week_2_Exploratory_Data_Analysis_and_Statistical_Modeling.docx` — formatted report with methods, findings, visual interpretations, regression results, assumptions and recommendations.
- `submission/Week_2_Submission_Description.txt` — portal description (200+ words).
- `src/generate_week2_simulated_data.py` — deterministic synthetic data generator.
- `src/eda_statistical_modeling.py` — data audit, descriptive summaries, five charts, outlier screen, and two regression models.
- `reports/figures/` — five saved visualizations.
- `data/processed/week2_*` — generated summaries, audit, metrics, coefficients and predictions.

## Run from repository root
```bash
python -m pip install -r requirements.txt
python src/generate_week2_simulated_data.py
python src/eda_statistical_modeling.py
```

## Methods
- Completeness and duplicate checks; descriptive statistics; project-type summaries; IQR-based outlier flagging.
- Visual analysis of schedule delay, procurement relationship, project categories, correlations, and planned budget versus final cost.
- Multiple linear regression for schedule delay and cost-overrun percentage, using an 80/20 train/test split with `random_state=42`.
- Metrics: MAE, RMSE and R-squared.

## Limitations
The results, associations and metrics are specific to synthetic data. They are not causal estimates and must not be used for operational budgets or commitments. Real deployment would require representative, permissioned project data, documented KPI definitions, residual diagnostics, repeated or time-aware validation, and construction-domain review.
