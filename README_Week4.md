# Week 4 — Data Visualization, Reporting, and Actionable Insights

This Week 4 addition synthesizes the Week 1 data acquisition and quality work, the Week 2 EDA work, and the Week 3 predictive risk-modeling work into a stakeholder-ready final report.

## Files added

- `reports/Week_4_Data_Visualization_Reporting_and_Actionable_Insights.docx` — editable final stakeholder report.
- `reports/figures/week4_*.png` — seven Python-generated visuals: executive KPI dashboard, delay by project type, procurement-delay relationship, budget versus actual cost, model validation trade-offs, mitigation scenarios, and a qualitative risk matrix.
- `data/processed/week4_executive_summary.json` — key indicators and model metrics, with separate entries for the Week 2 and Week 3 samples.
- `data/processed/week4_project_type_summary.csv` — project-type performance summary from Week 2 data.
- `data/processed/week4_risk_priority_register.csv` — qualitative likelihood/impact rating, owner, and first response for key risks.
- `data/processed/week4_recommendation_tracker.csv` — proposed actions, timelines, owners, and measures of progress.
- `submission/Week_4_Submission_Description.txt` — report description for the portal (200+ words).
- `src/week4_final_analysis.py` — reads the existing Week 2/3 repository artifacts and generates summary tables and visuals.
- `src/build_week4_report.py` — builds the editable Word report from the generated artifacts.
- `tests/test_week4_outputs.py` — checks core output integrity.

## Run from the repository root

The script expects the Week 2 and Week 3 data files already in the repository. Install the repository requirements first, then run:

```bash
python src/week4_final_analysis.py
python src/build_week4_report.py
python -m unittest discover -s tests -p "test_week4_outputs.py"
```

## Data and interpretation notes

All rows and outcomes in this internship portfolio are simulated. Week 1, Week 2, and Week 3 use separate datasets with different sample sizes and generation assumptions. The final report synthesizes themes and clearly labels metrics by source sample; it does not row-merge those samples. Correlation is not causal evidence, model-based what-if scenarios are not guaranteed intervention effects, and model metrics are not production validation. Before any real project use, data access, target definitions, feature timing, validation design, monitoring, human review, and safety governance would require formal approval.
