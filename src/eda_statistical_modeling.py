"""Reproducible EDA and introductory regression models for construction data.

The input is a synthetic educational dataset, not real-world construction records.
Run from repository root: python src/eda_statistical_modeling.py
"""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "construction_projects_eda_simulated.csv"
OUT = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook")

NUMERIC_FIELDS = [
    "planned_duration_days", "actual_duration_days", "schedule_delay_days",
    "planned_budget_inr_lakh", "actual_final_cost_inr_lakh", "cost_overrun_pct",
    "contractor_experience_years", "labor_count", "equipment_hours",
    "material_cost_index", "procurement_delay_days", "weather_delay_days", "safety_incidents"
]
NUMERIC_FEATURES = ["procurement_delay_days", "weather_delay_days", "contractor_experience_years",
                    "labor_count", "equipment_hours", "material_cost_index", "safety_incidents"]
CATEGORICAL_FEATURES = ["project_type", "region"]


def main():
    if not DATA.exists():
        raise FileNotFoundError(f"Input not found: {DATA}. Run python src/generate_week2_simulated_data.py first.")
    df = pd.read_csv(DATA)

    # Data audit and numerical summaries
    audit = {
        "synthetic_input": True,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_project_ids": int(df["project_id"].duplicated().sum()),
        "columns_with_missing_values": {str(k): int(v) for k, v in df.isna().sum().items() if int(v) > 0},
        "unique_project_types": int(df["project_type"].nunique()),
        "input_note": "Simulated data generated with a fixed seed for reproducibility; not actual project observations."
    }
    (OUT / "week2_data_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    df[NUMERIC_FIELDS].describe().T.round(2).to_csv(OUT / "week2_numeric_summary.csv")
    df.groupby("project_type", observed=True).agg(
        project_count=("project_id", "count"),
        mean_schedule_delay_days=("schedule_delay_days", "mean"),
        median_schedule_delay_days=("schedule_delay_days", "median"),
        mean_cost_overrun_pct=("cost_overrun_pct", "mean"),
        on_time_rate_pct=("on_time_delivery", lambda s: s.mean() * 100)
    ).round(2).to_csv(OUT / "week2_project_type_summary.csv")

    # Possible outliers from the IQR screen are flagged, not deleted automatically.
    outlier_rows = []
    for col in ["schedule_delay_days", "cost_overrun_pct", "procurement_delay_days", "material_cost_index"]:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((df[col] < low) | (df[col] > high)).sum())
        outlier_rows.append({"variable": col, "q1": round(float(q1), 2), "q3": round(float(q3), 2),
                             "iqr_lower_fence": round(float(low), 2), "iqr_upper_fence": round(float(high), 2),
                             "flagged_count": count, "action": "Flag for domain review; do not auto-delete"})
    pd.DataFrame(outlier_rows).to_csv(OUT / "week2_iqr_outlier_screen.csv", index=False)

    # Chart 1: outcome distribution
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    sns.histplot(data=df, x="schedule_delay_days", bins=24, kde=True, color="#287D8E", ax=ax)
    ax.axvline(0, color="#B64B4B", linestyle="--", linewidth=1.6, label="No schedule delay")
    ax.set(title="Distribution of Schedule Delay", xlabel="Schedule delay (days; negative = early)", ylabel="Project count")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "week2_01_schedule_delay_distribution.png", dpi=180); plt.close(fig)

    # Chart 2: procurement delay and schedule delay
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    sns.regplot(data=df, x="procurement_delay_days", y="schedule_delay_days", scatter_kws={"alpha":0.55, "s":28},
                line_kws={"color":"#B64B4B", "linewidth":2}, color="#287D8E", ax=ax)
    ax.set(title="Procurement Delay vs Schedule Delay", xlabel="Procurement delay (days)", ylabel="Schedule delay (days)")
    fig.tight_layout(); fig.savefig(FIG / "week2_02_procurement_vs_schedule_delay.png", dpi=180); plt.close(fig)

    # Chart 3: project type comparisons
    type_stats = df.groupby("project_type", observed=True)["schedule_delay_days"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    sns.barplot(x=type_stats.values, y=type_stats.index, color="#287D8E", ax=ax)
    ax.axvline(df["schedule_delay_days"].mean(), color="#B64B4B", linestyle="--", linewidth=1.5, label="Overall mean")
    ax.set(title="Mean Schedule Delay by Project Type", xlabel="Mean schedule delay (days)", ylabel="Project type")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / "week2_03_delay_by_project_type.png", dpi=180); plt.close(fig)

    # Chart 4: numeric correlations
    corr_cols = ["schedule_delay_days", "cost_overrun_pct", "procurement_delay_days", "weather_delay_days",
                 "contractor_experience_years", "material_cost_index", "safety_incidents", "labor_count"]
    corr = df[corr_cols].corr(numeric_only=True)
    corr.to_csv(OUT / "week2_correlation_matrix.csv")
    fig, ax = plt.subplots(figsize=(9.0, 6.4))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, square=True, linewidths=.35, ax=ax,
                cbar_kws={"shrink":0.8})
    ax.set_title("Correlation Matrix of Selected KPIs and Candidate Drivers", pad=14)
    fig.tight_layout(); fig.savefig(FIG / "week2_04_correlation_heatmap.png", dpi=180); plt.close(fig)

    # Chart 5: planned versus actual final cost
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    sns.scatterplot(data=df, x="planned_budget_inr_lakh", y="actual_final_cost_inr_lakh", hue="project_type",
                    alpha=.72, s=45, ax=ax, legend=False)
    lims = [min(df["planned_budget_inr_lakh"].min(), df["actual_final_cost_inr_lakh"].min()),
            max(df["planned_budget_inr_lakh"].max(), df["actual_final_cost_inr_lakh"].max())]
    ax.plot(lims, lims, linestyle="--", color="#B64B4B", linewidth=1.5, label="Budget = final cost")
    ax.set(title="Planned Budget vs Simulated Final Cost", xlabel="Planned budget (INR lakh)", ylabel="Actual final cost (INR lakh)")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "week2_05_budget_vs_actual_cost.png", dpi=180); plt.close(fig)

    # Train/test validation for two multiple linear regression models.
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    results = {}
    predictions = df[["project_id", "project_type", "schedule_delay_days", "cost_overrun_pct"]].copy()
    coefficient_records = []
    split_ids = None
    for target in ["schedule_delay_days", "cost_overrun_pct"]:
        y = df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
        transformer = ColumnTransformer(
            transformers=[
                ("numeric", "passthrough", NUMERIC_FEATURES),
                ("categorical", OneHotEncoder(handle_unknown="ignore", drop="first"), CATEGORICAL_FEATURES),
            ], remainder="drop"
        )
        model = Pipeline([("preprocessor", transformer), ("regression", LinearRegression())])
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
        results[target] = {
            "model": "Multiple Linear Regression",
            "test_rows": int(len(y_test)),
            "mae": round(float(mean_absolute_error(y_test, pred)), 3),
            "rmse": round(rmse, 3),
            "r2": round(float(r2_score(y_test, pred)), 3),
            "target_mean_test": round(float(y_test.mean()), 3),
            "target_note": "Validation metrics are demonstration results for synthetic data only."
        }
        predictions.loc[X_test.index, f"predicted_{target}"] = pred
        try:
            feature_names = model.named_steps["preprocessor"].get_feature_names_out()
            coefs = model.named_steps["regression"].coef_
            for name, coef in zip(feature_names, coefs):
                coefficient_records.append({"target": target, "feature": str(name), "coefficient": round(float(coef), 4)})
        except Exception as exc:
            warnings.warn(f"Could not extract model coefficients: {exc}")
    (OUT / "week2_model_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    pd.DataFrame(coefficient_records).to_csv(OUT / "week2_model_coefficients.csv", index=False)
    predictions.to_csv(OUT / "week2_model_predictions.csv", index=False)

    # Summary numbers used in the Word report
    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "mean_schedule_delay_days": round(float(df["schedule_delay_days"].mean()), 2),
        "median_schedule_delay_days": round(float(df["schedule_delay_days"].median()), 2),
        "on_time_rate_pct": round(float(df["on_time_delivery"].mean() * 100), 2),
        "mean_cost_overrun_pct": round(float(df["cost_overrun_pct"].mean()), 2),
        "median_cost_overrun_pct": round(float(df["cost_overrun_pct"].median()), 2),
        "over_10pct_cost_overrun_rate_pct": round(float(df["cost_overrun_over_10pct"].mean() * 100), 2),
        "mean_procurement_delay_days": round(float(df["procurement_delay_days"].mean()), 2),
        "mean_weather_delay_days": round(float(df["weather_delay_days"].mean()), 2),
        "correlation_procurement_schedule": round(float(df["procurement_delay_days"].corr(df["schedule_delay_days"])), 3),
        "correlation_material_cost_overrun": round(float(df["material_cost_index"].corr(df["cost_overrun_pct"])), 3),
        "highest_mean_delay_type": str(type_stats.index[0]),
        "highest_mean_delay_days": round(float(type_stats.iloc[0]), 2),
        "lowest_mean_delay_type": str(type_stats.index[-1]),
        "lowest_mean_delay_days": round(float(type_stats.iloc[-1]), 2),
        "audit": audit,
        "models": results,
    }
    (OUT / "week2_analysis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
