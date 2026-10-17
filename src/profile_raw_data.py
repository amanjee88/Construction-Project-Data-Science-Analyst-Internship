"""Profile a deliberately imperfect synthetic construction-project dataset.

The input is generated for training. It does NOT contain real project records.
Run from repository root: python src/profile_raw_data.py
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "construction_projects_simulated_raw.csv"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

NUMERIC_FIELDS = [
    "baseline_budget_inr_lakh", "actual_cost_to_date_inr_lakh",
    "planned_duration_days", "elapsed_duration_days", "physical_completion_pct",
    "contractor_experience_years", "labor_count", "equipment_hours_to_date",
    "material_cost_index", "procurement_delay_days", "weather_delay_days", "safety_incidents"
]
DATE_FIELDS = ["planned_start_date", "planned_end_date", "actual_start_date", "forecast_completion_date", "last_updated"]
CATEGORY_FIELDS = ["project_type", "state", "city", "project_status"]


def profile_and_stage(path=RAW):
    df = pd.read_csv(path, dtype="string")
    profile = pd.DataFrame({
        "column": df.columns,
        "raw_dtype": [str(df[c].dtype) for c in df.columns],
        "missing_count": [int(df[c].isna().sum() + df[c].astype("string").str.strip().eq("").sum()) for c in df.columns],
        "distinct_nonblank": [int(df[c].replace(r"^\s*$", pd.NA, regex=True).nunique(dropna=True)) for c in df.columns]
    })
    profile["missing_pct"] = (profile["missing_count"] / max(len(df), 1) * 100).round(2)
    profile.to_csv(OUT / "data_quality_profile.csv", index=False)

    staged = df.copy()
    for c in CATEGORY_FIELDS:
        staged[c] = staged[c].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    for c in ["project_type", "project_status"]:
        staged[c] = staged[c].str.title()
    staged["state"] = staged["state"].str.title()
    for c in NUMERIC_FIELDS:
        cleaned = staged[c].astype("string").str.replace(r"[₹,\s]", "", regex=True)
        staged[c] = pd.to_numeric(cleaned, errors="coerce")
    for c in DATE_FIELDS:
        # The synthetic fixture uses ISO dates; use a source-specific explicit format for non-ISO sources.
        staged[c] = pd.to_datetime(staged[c], errors="coerce", dayfirst=False)

    reasons = [[] for _ in range(len(staged))]
    def flag(mask, label):
        for idx in staged.index[mask.fillna(False)]:
            reasons[idx].append(label)
    flag(staged["project_id"].duplicated(keep=False), "duplicate_project_id_review")
    flag(staged["baseline_budget_inr_lakh"].isna(), "missing_or_invalid_baseline_budget")
    flag(staged["actual_cost_to_date_inr_lakh"].isna(), "missing_or_invalid_actual_cost_to_date")
    flag(staged["physical_completion_pct"].notna() & ~staged["physical_completion_pct"].between(0, 100), "completion_out_of_range")
    flag(staged["equipment_hours_to_date"].notna() & (staged["equipment_hours_to_date"] < 0), "negative_equipment_hours")
    flag(staged["planned_end_date"].isna(), "invalid_or_missing_planned_end_date")
    flag(staged["last_updated"].isna(), "missing_or_invalid_last_updated")
    staged["manual_review_reason"] = ["; ".join(x) for x in reasons]
    staged["record_quality_status"] = staged["manual_review_reason"].map(lambda x: "MANUAL_REVIEW" if x else "SCREENED_NOT_APPROVED")
    staged.to_csv(OUT / "standardized_staging.csv", index=False, date_format="%Y-%m-%d")
    staged.loc[staged["manual_review_reason"].ne("")].to_csv(OUT / "records_for_manual_review.csv", index=False, date_format="%Y-%m-%d")

    summary = {
        "synthetic_input": True,
        "input_path": str(path.relative_to(ROOT)),
        "rows_read": int(len(df)),
        "columns_read": int(len(df.columns)),
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "rows_with_duplicate_project_id": int(df["project_id"].duplicated(keep=False).sum()),
        "rows_flagged_for_manual_review": int(staged["manual_review_reason"].ne("").sum()),
        "rows_in_staging": int(len(staged)),
        "note": "Staging is standardized, not analyst-approved or model-ready. Missing values are not silently imputed."
    }
    (OUT / "quality_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary

if __name__ == "__main__":
    print(json.dumps(profile_and_stage(), indent=2))
