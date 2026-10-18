"""Week 4 stakeholder synthesis for the construction analytics internship.

The Week 2 and Week 3 datasets are intentionally separate synthetic samples.
This script combines their findings at the narrative/indicator level only; it
never joins the independent rows as though they were the same projects.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
FIGURES = ROOT / "reports" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

W2_PATH = DATA / "raw" / "construction_projects_eda_simulated.csv"
W3_PATH = DATA / "raw" / "construction_risk_simulated.csv"
W3_REG_PATH = PROCESSED / "week3_delay_regression_metrics.csv"
W3_CLS_PATH = PROCESSED / "week3_cost_overrun_classification_metrics.csv"
W3_SCENARIO_PATH = PROCESSED / "week3_scenario_analysis.csv"
W3_REGISTER_PATH = PROCESSED / "week3_risk_mitigation_register.csv"


def savefig(fig, name: str) -> None:
    fig.savefig(FIGURES / name, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    for p in [W2_PATH, W3_PATH, W3_REG_PATH, W3_CLS_PATH, W3_SCENARIO_PATH, W3_REGISTER_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Required Week 2/3 project file not found: {p.relative_to(ROOT)}")

    w2 = pd.read_csv(W2_PATH)
    w3 = pd.read_csv(W3_PATH)
    reg = pd.read_csv(W3_REG_PATH)
    cls = pd.read_csv(W3_CLS_PATH)
    scenarios = pd.read_csv(W3_SCENARIO_PATH)
    register = pd.read_csv(W3_REGISTER_PATH)

    corr_proc = float(w2["procurement_delay_days"].corr(w2["schedule_delay_days"]))
    corr_material_cost = float(w2["material_cost_index"].corr(w2["cost_overrun_pct"]))
    w2_type = (
        w2.groupby("project_type", as_index=False)
        .agg(
            project_count=("project_id", "count"),
            mean_schedule_delay_days=("schedule_delay_days", "mean"),
            median_schedule_delay_days=("schedule_delay_days", "median"),
            mean_cost_overrun_pct=("cost_overrun_pct", "mean"),
            on_time_rate_pct=("on_time_delivery", lambda s: 100 * s.mean()),
        )
        .sort_values("mean_schedule_delay_days", ascending=False)
    )
    w2_type.to_csv(PROCESSED / "week4_project_type_summary.csv", index=False, float_format="%.3f")

    linear = reg.loc[reg["model"].str.lower().eq("linear regression")].iloc[0]
    forest_reg = reg.loc[reg["model"].str.lower().eq("random forest regressor")].iloc[0]
    logit = cls.loc[cls["model"].str.lower().eq("logistic regression")].iloc[0]
    forest_cls = cls.loc[cls["model"].str.lower().eq("random forest classifier")].iloc[0]

    # Portfolio/prioritization ratings are a structured expert-style starting point,
    # not model-predicted probabilities or frequencies from the synthetic data.
    risk_priority = pd.DataFrame([
        {"risk_area": "Schedule / adverse weather", "likelihood_1_to_5": 4, "impact_1_to_5": 5, "priority_score": 20, "priority_band": "Critical", "owner": "Project planner + site manager", "first_response": "Seasonal work plan, phase look-ahead, recovery actions and protected schedule buffer"},
        {"risk_area": "Supplier / procurement delays", "likelihood_1_to_5": 5, "impact_1_to_5": 4, "priority_score": 20, "priority_band": "Critical", "owner": "Procurement lead", "first_response": "Long-lead tracker, confirmed promise dates, escalation rules and alternate suppliers"},
        {"risk_area": "Design changes / rework", "likelihood_1_to_5": 4, "impact_1_to_5": 4, "priority_score": 16, "priority_band": "High", "owner": "Design manager + client representative", "first_response": "Design-freeze gates, RFI ageing review and multidisciplinary clash checks"},
        {"risk_area": "Cost overrun / commitment drift", "likelihood_1_to_5": 3, "impact_1_to_5": 5, "priority_score": 15, "priority_band": "High", "owner": "Cost controller / quantity surveyor", "first_response": "Monthly estimate-at-completion and reconciliation of commitments, actuals and changes"},
        {"risk_area": "Ground / site uncertainty", "likelihood_1_to_5": 3, "impact_1_to_5": 4, "priority_score": 12, "priority_band": "High", "owner": "Site engineer + geotechnical lead", "first_response": "Targeted surveys, explicit assumptions, contingency ownership and escalation"},
        {"risk_area": "Safety-critical activities", "likelihood_1_to_5": 2, "impact_1_to_5": 5, "priority_score": 10, "priority_band": "High - safety critical", "owner": "HSE officer + site leadership", "first_response": "Task risk assessments, permits, toolbox talks and verified close-out of safety actions"},
        {"risk_area": "Labor availability / productivity", "likelihood_1_to_5": 2, "impact_1_to_5": 3, "priority_score": 6, "priority_band": "Moderate-high", "owner": "Construction manager", "first_response": "Rolling trade-wise crew forecast, subcontractor confirmation and productivity review"},
    ])
    risk_priority.to_csv(PROCESSED / "week4_risk_priority_register.csv", index=False)

    recommendations = pd.DataFrame([
        {"horizon": "0-30 days", "action": "Establish a weekly control-room dashboard for schedule, procurement, cost, rework and safety indicators.", "owner": "Project controls lead", "measure_of_success": "Named owner and current status for every critical indicator; overdue actions visible"},
        {"horizon": "0-30 days", "action": "Create a long-lead procurement tracker with promise date, required-on-site date and escalation owner.", "owner": "Procurement lead", "measure_of_success": "All critical materials have verified dates, contingency options and escalation triggers"},
        {"horizon": "31-60 days", "action": "Pilot a delay-risk score using only information available at the forecast date; review it with planners.", "owner": "Data analyst + project planner", "measure_of_success": "Back-tested error, recall and false-alert rate documented on held-out real projects"},
        {"horizon": "31-60 days", "action": "Introduce design-freeze and RFI-ageing checkpoints for packages on the critical path.", "owner": "Design manager", "measure_of_success": "Open critical RFIs and unapproved changes are reviewed at each weekly meeting"},
        {"horizon": "61-90 days", "action": "Run a controlled pilot across multiple real projects and compare forecast quality by project type and phase.", "owner": "PMO / project controls", "measure_of_success": "Time-based or project-group validation completed; model limits and escalation rules approved"},
        {"horizon": "Ongoing", "action": "Keep safety checks independent from the schedule/cost model; investigate incidents and near misses using formal controls.", "owner": "HSE lead + site management", "measure_of_success": "Required safety actions closed on time; no model score used to relax a safety control"},
    ])
    recommendations.to_csv(PROCESSED / "week4_recommendation_tracker.csv", index=False)

    # Summary deliberately keeps results from each independent synthetic sample distinct.
    summary = {
        "report_title": "Data Visualization, Reporting, and Actionable Insights",
        "data_caveat": "Week 1, Week 2 and Week 3 used separate synthetic samples and distinct objectives. Summary themes are synthesized, but records are not row-merged and no metric is an observed industry benchmark.",
        "week1_data_acquisition_sample": {"rows": 51, "columns": 23, "exact_duplicate_rows": 1, "rows_with_duplicate_project_id": 2, "rows_flagged_for_manual_review": 7, "note": "Raw starter fixture with intentionally introduced data-quality issues."},
        "week2_eda_sample": {
            "rows": int(len(w2)), "columns": int(w2.shape[1]),
            "mean_schedule_delay_days": round(float(w2.schedule_delay_days.mean()), 2),
            "median_schedule_delay_days": round(float(w2.schedule_delay_days.median()), 2),
            "on_time_rate_pct": round(float(100 * w2.on_time_delivery.mean()), 2),
            "mean_cost_overrun_pct": round(float(w2.cost_overrun_pct.mean()), 2),
            "over_10pct_cost_overrun_rate_pct": round(float(100 * w2.cost_overrun_over_10pct.mean()), 2),
            "mean_procurement_delay_days": round(float(w2.procurement_delay_days.mean()), 2),
            "mean_weather_delay_days": round(float(w2.weather_delay_days.mean()), 2),
            "correlation_procurement_schedule": round(corr_proc, 3),
            "correlation_material_cost_overrun": round(corr_material_cost, 3),
            "highest_mean_delay_type": str(w2_type.iloc[0].project_type),
            "highest_mean_delay_days": round(float(w2_type.iloc[0].mean_schedule_delay_days), 2),
            "lowest_mean_delay_type": str(w2_type.iloc[-1].project_type),
            "lowest_mean_delay_days": round(float(w2_type.iloc[-1].mean_schedule_delay_days), 2),
        },
        "week3_risk_sample": {
            "rows": int(len(w3)), "columns": int(w3.shape[1]),
            "mean_delay_days": round(float(w3.actual_delay_days.mean()), 2),
            "median_delay_days": round(float(w3.actual_delay_days.median()), 2),
            "high_delay_rate_30days_pct": round(float(100 * w3.high_delay_flag_30days.mean()), 2),
            "mean_cost_overrun_pct": round(float(w3.cost_overrun_pct.mean()), 2),
            "cost_overrun_rate_10pct_pct": round(float(100 * w3.cost_overrun_flag_10pct.mean()), 2),
            "safety_incident_project_rate_pct": round(float(100 * (w3.safety_incidents_simulated > 0).mean()), 2),
            "delay_linear_regression": {"holdout_MAE_days": float(linear.test_MAE_days), "holdout_RMSE_days": float(linear.test_RMSE_days), "holdout_R2": float(linear.test_R2), "cv_R2_mean": float(linear.cv_R2_mean), "cv_R2_std": float(linear.cv_R2_std)},
            "delay_random_forest": {"holdout_MAE_days": float(forest_reg.test_MAE_days), "holdout_RMSE_days": float(forest_reg.test_RMSE_days), "holdout_R2": float(forest_reg.test_R2), "cv_R2_mean": float(forest_reg.cv_R2_mean), "cv_R2_std": float(forest_reg.cv_R2_std)},
            "cost_risk_logistic_regression": {"accuracy": float(logit.test_accuracy), "precision": float(logit.test_precision), "recall": float(logit.test_recall), "f1": float(logit.test_F1), "roc_auc": float(logit.test_ROC_AUC), "cv_roc_auc_mean": float(logit.cv_ROC_AUC_mean), "cv_roc_auc_std": float(logit.cv_ROC_AUC_std)},
            "cost_risk_random_forest": {"accuracy": float(forest_cls.test_accuracy), "precision": float(forest_cls.test_precision), "recall": float(forest_cls.test_recall), "f1": float(forest_cls.test_F1), "roc_auc": float(forest_cls.test_ROC_AUC), "cv_roc_auc_mean": float(forest_cls.cv_ROC_AUC_mean), "cv_roc_auc_std": float(forest_cls.cv_ROC_AUC_std)},
        },
        "scenario_analysis": scenarios.to_dict(orient="records"),
    }
    with open(PROCESSED / "week4_executive_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Palette chosen for consistent, high-contrast report figures.
    navy = "#17324D"
    blue = "#2E75B6"
    teal = "#2A9D8F"
    orange = "#E58B2A"
    red = "#C84C4C"
    grey = "#5B6573"

    # Figure 1: executive KPI dashboard from the Week 2 EDA sample.
    kpis = [
        ("Projects in EDA sample", f"{len(w2):,}", "Week 2 synthetic dataset"),
        ("Mean schedule delay", f"{w2.schedule_delay_days.mean():.1f} days", "Median: %.1f days" % w2.schedule_delay_days.median()),
        ("On-time completion rate", f"{100*w2.on_time_delivery.mean():.1f}%", "Operational improvement area"),
        ("Mean cost overrun", f"{w2.cost_overrun_pct.mean():.2f}%", "Mean across synthetic records"),
        ("Mean procurement delay", f"{w2.procurement_delay_days.mean():.1f} days", f"r with schedule delay = {corr_proc:.2f}"),
        (">10% cost overrun", f"{100*w2.cost_overrun_over_10pct.mean():.1f}%", "Threshold-based sample indicator"),
    ]
    fig, ax = plt.subplots(figsize=(11.5, 6.6))
    ax.set_xlim(0, 3); ax.set_ylim(0, 2); ax.axis("off")
    fig.suptitle("Construction Project Performance | Executive Snapshot", fontsize=18, fontweight="bold", color=navy, y=0.97)
    for i, (label, value, note) in enumerate(kpis):
        r, c = divmod(i, 3)
        x, y = c + 0.08, 1.08 - r * 0.92
        rect = plt.Rectangle((x, y), 0.84, 0.76, facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=1.2, joinstyle="round")
        ax.add_patch(rect)
        ax.text(x+0.42, y+0.56, label, ha="center", va="center", fontsize=9, color=grey, wrap=True)
        ax.text(x+0.42, y+0.35, value, ha="center", va="center", fontsize=17, color=blue if i not in (2,5) else teal, fontweight="bold")
        ax.text(x+0.42, y+0.13, note, ha="center", va="center", fontsize=7.5, color=grey, wrap=True)
    fig.text(0.5, 0.02, "Synthetic Week 2 sample only; indicators are illustrative, not real-world benchmarks.", ha="center", fontsize=9, color=grey)
    savefig(fig, "week4_01_executive_kpi_dashboard.png")

    # Figure 2: project-type comparison.
    plot = w2_type.sort_values("mean_schedule_delay_days", ascending=True)
    fig, ax = plt.subplots(figsize=(9.3, 5.6))
    bars = ax.barh(plot.project_type, plot.mean_schedule_delay_days, color=blue)
    ax.set_title("Average Schedule Delay by Project Type", loc="left", fontsize=15, fontweight="bold", color=navy, pad=14)
    ax.set_xlabel("Mean delay (days)")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    for b, val in zip(bars, plot.mean_schedule_delay_days):
        ax.text(b.get_width()+0.5, b.get_y()+b.get_height()/2, f"{val:.1f}", va="center", fontsize=9, color=grey)
    ax.set_xlim(0, max(plot.mean_schedule_delay_days)*1.18)
    ax.spines[["top", "right", "left"]].set_visible(False)
    savefig(fig, "week4_02_delay_by_project_type.png")

    # Figure 3: procurement delays versus schedule delay.
    x = w2.procurement_delay_days.to_numpy(dtype=float)
    y = w2.schedule_delay_days.to_numpy(dtype=float)
    coeff = np.polyfit(x, y, 1)
    xx = np.linspace(x.min(), x.max(), 120)
    fig, ax = plt.subplots(figsize=(8.8, 5.6))
    ax.scatter(x, y, alpha=0.62, s=34, color=teal, edgecolor="white", linewidth=0.3)
    ax.plot(xx, coeff[0]*xx+coeff[1], color=orange, linewidth=2.5, label="Least-squares trend")
    ax.set_title("Procurement Delay and Overall Schedule Delay", loc="left", fontsize=15, fontweight="bold", color=navy, pad=14)
    ax.set_xlabel("Procurement delay (days)"); ax.set_ylabel("Schedule delay (days)")
    ax.text(0.03, 0.96, f"Pearson correlation r = {corr_proc:.3f}\nAssociation, not proof of causation", transform=ax.transAxes, ha="left", va="top", fontsize=10, color=navy, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#CBD5E1", alpha=0.95))
    ax.legend(frameon=False, loc="lower right"); ax.grid(linestyle="--", alpha=0.25); ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, "week4_03_procurement_vs_schedule_delay.png")

    # Figure 4: planned budget vs final cost.
    budget = w2.planned_budget_inr_lakh.to_numpy(dtype=float)
    actual = w2.actual_final_cost_inr_lakh.to_numpy(dtype=float)
    low = min(budget.min(), actual.min()); high = max(budget.max(), actual.max())
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    over = w2.cost_overrun_pct.to_numpy(dtype=float) > 0
    ax.scatter(budget[~over], actual[~over], s=35, alpha=0.68, color=teal, label="At/below budget")
    ax.scatter(budget[over], actual[over], s=35, alpha=0.68, color=orange, label="Above budget")
    ax.plot([low, high], [low, high], linestyle="--", color=navy, linewidth=1.8, label="Budget parity line")
    ax.set_title("Planned Budget vs Actual Final Cost", loc="left", fontsize=15, fontweight="bold", color=navy, pad=14)
    ax.set_xlabel("Planned budget (INR lakh)"); ax.set_ylabel("Actual final cost (INR lakh)")
    ax.legend(frameon=False); ax.grid(linestyle="--", alpha=0.25); ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, "week4_04_budget_vs_actual_cost.png")

    # Figure 5: separate scales for regression error and fit; comparable 0-1 classifier scores.
    fig = plt.figure(figsize=(12.2, 6.3))
    grid = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.15], height_ratios=[1, 1], wspace=0.32, hspace=0.52)
    ax_mae = fig.add_subplot(grid[0, 0])
    ax_r2 = fig.add_subplot(grid[1, 0])
    ax_cls = fig.add_subplot(grid[:, 1])
    names = ["Linear\nRegression", "Random\nForest"]
    xx = np.arange(2)
    mae_vals = [float(linear.test_MAE_days), float(forest_reg.test_MAE_days)]
    r2_vals = [float(linear.test_R2), float(forest_reg.test_R2)]
    bm = ax_mae.bar(xx, mae_vals, color=[blue, orange], width=0.56)
    ax_mae.set_xticks(xx, names); ax_mae.set_ylabel("MAE (days)"); ax_mae.set_title("Delay forecast error\n(lower is better)", fontweight="bold", color=navy, fontsize=10)
    ax_mae.grid(axis="y", linestyle="--", alpha=0.25); ax_mae.set_axisbelow(True)
    for b in bm: ax_mae.text(b.get_x()+b.get_width()/2, b.get_height()+0.12, f"{b.get_height():.2f}", ha="center", fontsize=8)
    br = ax_r2.bar(xx, r2_vals, color=[blue, orange], width=0.56)
    ax_r2.set_xticks(xx, names); ax_r2.set_ylim(0, 0.7); ax_r2.set_ylabel("Holdout R²"); ax_r2.set_title("Delay forecast fit\n(higher is better)", fontweight="bold", color=navy, fontsize=10)
    ax_r2.grid(axis="y", linestyle="--", alpha=0.25); ax_r2.set_axisbelow(True)
    for b in br: ax_r2.text(b.get_x()+b.get_width()/2, b.get_height()+0.015, f"{b.get_height():.2f}", ha="center", fontsize=8)
    model_names = ["Logistic\nRegression", "Random Forest\nClassifier"]
    rec = [float(logit.test_recall), float(forest_cls.test_recall)]
    auc = [float(logit.test_ROC_AUC), float(forest_cls.test_ROC_AUC)]
    width = 0.34
    b1 = ax_cls.bar(xx-width/2, auc, width, color=teal, label="ROC-AUC")
    b2 = ax_cls.bar(xx+width/2, rec, width, color=red, label="Recall")
    ax_cls.set_xticks(xx, model_names); ax_cls.set_ylim(0, 1.05); ax_cls.set_title("Cost-overrun risk classification\n(higher is generally better; trade-offs remain)", fontweight="bold", color=navy, fontsize=10)
    ax_cls.set_ylabel("Score (0-1)"); ax_cls.grid(axis="y", alpha=0.25, linestyle="--"); ax_cls.set_axisbelow(True); ax_cls.legend(frameon=False, fontsize=8, loc="upper right")
    for b in list(b1)+list(b2): ax_cls.text(b.get_x()+b.get_width()/2, b.get_height()+0.025, f"{b.get_height():.2f}", ha="center", va="bottom", fontsize=8)
    fig.suptitle("Model Validation: Read Each Metric in Its Own Context", fontsize=15, fontweight="bold", color=navy, y=0.99)
    fig.text(0.5, 0.015, "Week 3 synthetic sample. MAE is in days; R², ROC-AUC and recall are unitless.", ha="center", fontsize=8.5, color=grey)
    savefig(fig, "week4_05_model_validation_tradeoffs.png")

    # Figure 6: model-based what-if scenario estimates from the high-risk synthetic project.
    scenario_order = ["Baseline high-risk project", "Workforce plan (+10 percentage points)", "Supplier coordination (-5 supplier-delay days)", "Design freeze (-2 design changes)", "Combined controls"]
    sc = scenarios.copy()
    sc["_order"] = sc.scenario.map({name: i for i, name in enumerate(scenario_order)})
    sc = sc.sort_values("_order")
    label_map = {
        "Baseline high-risk project": "Baseline",
        "Supplier coordination (-5 supplier-delay days)": "Supplier\ncoordination",
        "Design freeze (-2 design changes)": "Design freeze",
        "Workforce plan (+10 percentage points)": "Workforce\nplan",
        "Combined controls": "Combined\ncontrols",
    }
    labels = [label_map.get(s, s) for s in sc.scenario]
    base = float(sc.loc[sc.scenario.eq("Baseline high-risk project"), "predicted_delay_days"].iloc[0])
    fig, ax = plt.subplots(figsize=(10, 5.8))
    bars = ax.bar(labels, sc.predicted_delay_days, color=[teal if "Combined" in s else blue if "Baseline" not in s else red for s in [label_map.get(s, s) for s in sc.scenario]])
    ax.set_title("Illustrative Mitigation Scenarios for One High-Risk Project", loc="left", fontsize=15, fontweight="bold", color=navy, pad=14)
    ax.set_ylabel("Predicted schedule delay (days)"); ax.grid(axis="y", linestyle="--", alpha=0.25); ax.set_axisbelow(True)
    for b, val in zip(bars, sc.predicted_delay_days):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.8, f"{val:.1f}", ha="center", va="bottom", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.5, 0.01, "Model what-if outputs are illustrative, not causal estimates or guaranteed savings.", ha="center", fontsize=9, color=grey)
    savefig(fig, "week4_06_mitigation_scenario_comparison.png")

    # Figure 7: transparent qualitative priority matrix, not model output.
    fig, ax = plt.subplots(figsize=(8.3, 6.1))
    cmap = plt.get_cmap("YlOrRd")
    vals = np.outer(np.arange(1, 6), np.arange(1, 6))
    ax.imshow(vals, cmap=cmap, origin="lower", vmin=1, vmax=25, aspect="equal")
    ax.set_xticks(range(5), ["1\nLow", "2", "3", "4", "5\nVery high"])
    ax.set_yticks(range(5), ["1\nRare", "2", "3", "4", "5\nVery likely"])
    ax.set_xlabel("Impact if the risk occurs (1-5)"); ax.set_ylabel("Likelihood rating (1-5)")
    ax.set_title("Qualitative Risk Priority Matrix", loc="left", fontsize=15, fontweight="bold", color=navy, pad=14)
    for _, row in risk_priority.iterrows():
        xpt = int(row.impact_1_to_5)-1; ypt = int(row.likelihood_1_to_5)-1
        short = {
            "Schedule / adverse weather": "Schedule /\nweather",
            "Supplier / procurement delays": "Supplier /\nprocurement",
            "Design changes / rework": "Design /\nrework",
            "Cost overrun / commitment drift": "Cost",
            "Ground / site uncertainty": "Ground /\nsite",
            "Safety-critical activities": "Safety",
            "Labor availability / productivity": "Labor",
        }[row.risk_area]
        ax.scatter([xpt], [ypt], s=160, c=navy, edgecolors="white", linewidths=1.1)
        ax.annotate(short, (xpt, ypt), xytext=(5, 5), textcoords="offset points", fontsize=7.4, color=navy, fontweight="bold")
    ax.set_xticks(np.arange(-.5,5,1), minor=True); ax.set_yticks(np.arange(-.5,5,1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=2); ax.tick_params(which="minor", bottom=False, left=False)
    savefig(fig, "week4_07_qualitative_risk_priority_matrix.png")

    print(json.dumps({"summary_path": str((PROCESSED / 'week4_executive_summary.json').relative_to(ROOT)),
                      "figures": sorted(p.name for p in FIGURES.glob("week4_*.png")),
                      "rows_week2": len(w2), "rows_week3": len(w3),
                      "procurement_schedule_corr": round(corr_proc, 3),
                      "material_cost_corr": round(corr_material_cost, 3)}, indent=2))


if __name__ == "__main__":
    main()
