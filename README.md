# Construction Project Data Science — Week 1

## Project purpose
This Week 1 package documents a data acquisition and preparation strategy for a fictional construction-project analytics scenario. It is intended as the foundation for later EDA, statistical modeling, risk forecasting and reporting tasks.

## Data transparency
`data/raw/construction_projects_simulated_raw.csv` is a synthetic training fixture generated specifically for this project. It is not sourced from actual construction sites and must not be presented as observed industry data. It intentionally contains a small number of missing, inconsistent and invalid values to demonstrate profiling and review workflows.

Public source candidates and their limitations are described in the Word report. In particular, MoSPI project-monitoring reports are context, CPWD Delhi Schedule of Rates is a dated rate reference, World Bank procurement notices are tender metadata, and OGD resources vary by publisher and granularity. None is presumed to supply every operational field required for project-level modeling.

## Repository layout
- `reports/Week_1_Data_Acquisition_Strategy_and_Preliminary_Insights.docx` — Word report.
- `submission/Week_1_Submission_Description.txt` — 200+ word portal description.
- `data/raw/` — synthetic raw starter dataset.
- `data/processed/` — profiling outputs and records flagged for manual review.
- `src/profile_raw_data.py` — data quality profiling and staging starter script.
- `assets/data_acquisition_workflow.png` — workflow diagram embedded in the report.

## Setup and run
Python 3.10+ is recommended.

```bash
python -m pip install -r requirements.txt
python src/profile_raw_data.py
```

The script reads the synthetic CSV and regenerates these outputs under `data/processed/`:
- `data_quality_profile.csv`
- `standardized_staging.csv`
- `records_for_manual_review.csv`
- `quality_summary.json`

## Important limitations
- A flagged value is not automatically wrong; it requires source or domain review.
- The staging file is standardized but not certified as model-ready.
- Example data and output counts relate only to synthetic training rows.
- Before using real data, obtain appropriate access permission and revise the schema, validation ranges, units and cleaning decisions with the project data owner.
