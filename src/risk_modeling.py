"""Train and evaluate baseline models for simulated construction project risk.

Uses synthetic teaching data only. Run from any directory:
    python src/risk_modeling.py
"""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, KFold, StratifiedKFold, cross_validate
from sklearn.impute import SimpleImputer
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                             roc_auc_score, precision_score, recall_score,
                             f1_score, accuracy_score, confusion_matrix,
                             ConfusionMatrixDisplay)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "construction_risk_simulated.csv"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"
SEED = 73

NUMERIC_FEATURES = [
    "contract_value_inr_mn", "planned_duration_days", "complexity_score_1_5",
    "rainfall_days", "supplier_delay_days", "labor_availability_pct",
    "design_changes_count", "ground_risk_score_1_5", "safety_training_score",
    "schedule_buffer_pct", "subcontractor_rating_1_5", "inspection_rework_events",
]
CATEGORICAL_FEATURES = ["project_type", "project_scale"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def preprocessor(scale_numeric=False):
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric = Pipeline(numeric_steps)
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric, NUMERIC_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def build_and_evaluate():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA)
    X = df[FEATURES]
    y_delay = df["actual_delay_days"]
    y_cost_flag = df["cost_overrun_flag_10pct"]

    # One holdout split kept separate from cross-validation folds.
    X_train, X_test, yd_train, yd_test, yc_train, yc_test = train_test_split(
        X, y_delay, y_cost_flag, test_size=0.20, random_state=SEED, stratify=y_cost_flag
    )

    models_reg = {
        "Linear Regression": Pipeline([("prep", preprocessor(scale_numeric=True)), ("model", LinearRegression())]),
        "Random Forest Regressor": Pipeline([("prep", preprocessor()), ("model", RandomForestRegressor(
            n_estimators=350, min_samples_leaf=3, max_features=0.85, random_state=SEED, n_jobs=-1
        ))]),
    }
    reg_rows = []
    trained_reg = {}
    for name, model in models_reg.items():
        model.fit(X_train, yd_train)
        pred = model.predict(X_test)
        cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
        scores = cross_validate(model, X_train, yd_train, cv=cv,
                                scoring={"r2": "r2", "mae": "neg_mean_absolute_error", "rmse": "neg_root_mean_squared_error"},
                                n_jobs=-1, return_train_score=False)
        reg_rows.append({
            "model": name,
            "test_MAE_days": round(float(mean_absolute_error(yd_test, pred)), 3),
            "test_RMSE_days": round(float(np.sqrt(mean_squared_error(yd_test, pred))), 3),
            "test_R2": round(float(r2_score(yd_test, pred)), 3),
            "cv_R2_mean": round(float(np.mean(scores["test_r2"])), 3),
            "cv_R2_std": round(float(np.std(scores["test_r2"])), 3),
            "cv_MAE_mean_days": round(float(-np.mean(scores["test_mae"])), 3),
            "cv_RMSE_mean_days": round(float(-np.mean(scores["test_rmse"])), 3),
        })
        trained_reg[name] = (model, pred)

    models_clf = {
        "Logistic Regression": Pipeline([("prep", preprocessor(scale_numeric=True)), ("model", LogisticRegression(max_iter=2500, class_weight="balanced", random_state=SEED))]),
        "Random Forest Classifier": Pipeline([("prep", preprocessor()), ("model", RandomForestClassifier(
            n_estimators=350, min_samples_leaf=3, max_features=0.85, class_weight="balanced_subsample", random_state=SEED, n_jobs=-1
        ))]),
    }
    clf_rows = []
    trained_clf = {}
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for name, model in models_clf.items():
        model.fit(X_train, yc_train)
        pred = model.predict(X_test)
        prob = model.predict_proba(X_test)[:, 1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cv = cross_validate(model, X_train, yc_train, cv=skf,
                                scoring={"roc_auc": "roc_auc", "f1": "f1", "recall": "recall", "precision": "precision", "accuracy": "accuracy"},
                                n_jobs=-1, return_train_score=False)
        clf_rows.append({
            "model": name,
            "test_accuracy": round(float(accuracy_score(yc_test, pred)), 3),
            "test_precision": round(float(precision_score(yc_test, pred, zero_division=0)), 3),
            "test_recall": round(float(recall_score(yc_test, pred, zero_division=0)), 3),
            "test_F1": round(float(f1_score(yc_test, pred, zero_division=0)), 3),
            "test_ROC_AUC": round(float(roc_auc_score(yc_test, prob)), 3),
            "cv_ROC_AUC_mean": round(float(np.mean(cv["test_roc_auc"])), 3),
            "cv_ROC_AUC_std": round(float(np.std(cv["test_roc_auc"])), 3),
            "cv_F1_mean": round(float(np.mean(cv["test_f1"])), 3),
            "cv_Recall_mean": round(float(np.mean(cv["test_recall"])), 3),
        })
        trained_clf[name] = (model, pred, prob)

    reg_df = pd.DataFrame(reg_rows).sort_values("test_R2", ascending=False)
    clf_df = pd.DataFrame(clf_rows).sort_values("test_ROC_AUC", ascending=False)
    reg_df.to_csv(PROCESSED / "week3_delay_regression_metrics.csv", index=False)
    clf_df.to_csv(PROCESSED / "week3_cost_overrun_classification_metrics.csv", index=False)

    # Use the best test-set R2 regressor and highest ROC-AUC classifier for the demonstration.
    best_reg_name = str(reg_df.iloc[0]["model"])
    best_clf_name = str(clf_df.iloc[0]["model"])
    best_reg, best_reg_pred = trained_reg[best_reg_name]
    best_clf, best_clf_pred, best_clf_prob = trained_clf[best_clf_name]

    pred_df = pd.DataFrame({
        "project_id": df.loc[X_test.index, "project_id"].to_numpy(),
        "actual_delay_days": yd_test.to_numpy(),
        "predicted_delay_days": np.maximum(0, best_reg_pred).round(2),
        "actual_cost_overrun_flag_10pct": yc_test.to_numpy(),
        "predicted_cost_overrun_flag_10pct": best_clf_pred,
        "predicted_cost_overrun_probability": best_clf_prob.round(4),
    })
    pred_df.to_csv(PROCESSED / "week3_holdout_predictions.csv", index=False)

    # Feature importance for the selected forest-based estimator where available.
    importance_df = None
    if best_reg_name == "Random Forest Regressor":
        names = best_reg.named_steps["prep"].get_feature_names_out()
        vals = best_reg.named_steps["model"].feature_importances_
        importance_df = pd.DataFrame({"feature": names, "importance": vals}).sort_values("importance", ascending=False)
    elif best_clf_name == "Random Forest Classifier":
        names = best_clf.named_steps["prep"].get_feature_names_out()
        vals = best_clf.named_steps["model"].feature_importances_
        importance_df = pd.DataFrame({"feature": names, "importance": vals}).sort_values("importance", ascending=False)
    if importance_df is not None:
        importance_df.to_csv(PROCESSED / "week3_feature_importance.csv", index=False)

    # Coefficients for interpretable baseline models, useful for an audit-friendly report.
    coefficient_rows = []
    for model_name, model_obj in [("Delay Linear Regression", models_reg["Linear Regression"]),
                                  ("Cost-overrun Logistic Regression", models_clf["Logistic Regression"])]:
        fitted_model = model_obj
        feature_names = fitted_model.named_steps["prep"].get_feature_names_out()
        coefs = fitted_model.named_steps["model"].coef_.ravel()
        for feature_name, coefficient in zip(feature_names, coefs):
            coefficient_rows.append({"model": model_name, "feature": feature_name,
                                     "coefficient": round(float(coefficient), 6),
                                     "absolute_coefficient": round(float(abs(coefficient)), 6)})
    pd.DataFrame(coefficient_rows).sort_values(["model", "absolute_coefficient"], ascending=[True, False]).to_csv(
        PROCESSED / "week3_interpretable_model_coefficients.csv", index=False
    )

    # Plot 1: actual vs predicted delay.
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    ax.scatter(yd_test, best_reg_pred, alpha=0.72, edgecolor="white", linewidth=0.4)
    lim = max(float(yd_test.max()), float(np.max(best_reg_pred))) + 5
    ax.plot([0, lim], [0, lim], linestyle="--", linewidth=1.6)
    ax.set(xlabel="Actual delay (days)", ylabel="Predicted delay (days)", title=f"Holdout performance: {best_reg_name}")
    ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(FIGURES / "week3_01_actual_vs_predicted_delay.png", dpi=180); plt.close(fig)

    # Plot 2: residual distribution.
    residuals = yd_test.to_numpy() - best_reg_pred
    fig, ax = plt.subplots(figsize=(7.4, 4.7))
    ax.hist(residuals, bins=18, edgecolor="white")
    ax.axvline(0, linestyle="--", linewidth=1.5)
    ax.set(xlabel="Actual minus predicted delay (days)", ylabel="Number of projects", title="Delay model residual distribution")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(FIGURES / "week3_02_delay_model_residuals.png", dpi=180); plt.close(fig)

    # Plot 3: model comparison for classification.
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    plot_df = clf_df.set_index("model")[["test_ROC_AUC", "test_F1", "test_recall"]]
    plot_df.plot(kind="bar", ax=ax, ylim=(0, 1), rot=0)
    ax.set(ylabel="Score (0-1)", title="Cost-overrun risk model comparison")
    ax.grid(axis="y", alpha=0.25); ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES / "week3_03_cost_overrun_model_comparison.png", dpi=180); plt.close(fig)

    # Plot 4: confusion matrix of selected classifier.
    cm = confusion_matrix(yc_test, best_clf_pred, labels=[0, 1])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Below 10%", "At least 10%"])
    fig, ax = plt.subplots(figsize=(6.5, 5.2))
    disp.plot(ax=ax, colorbar=False, values_format="d")
    ax.set_title(f"Holdout confusion matrix: {best_clf_name}")
    fig.tight_layout(); fig.savefig(FIGURES / "week3_04_cost_overrun_confusion_matrix.png", dpi=180); plt.close(fig)

    # Representative high-risk scenario: upper quartile by a transparent rule-based score.
    score = (
        df["supplier_delay_days"] / 28 * 2.0
        + df["rainfall_days"] / 30 * 1.0
        + (df["design_changes_count"] / 10) * 2.0
        + (df["complexity_score_1_5"] - 1) / 4 * 1.2
        + (80 - df["labor_availability_pct"]).clip(lower=0) / 40 * 1.0
        + (df["ground_risk_score_1_5"] - 1) / 4 * 1.0
    )
    high_risk_idx = score.quantile(0.75)
    candidates = df.loc[score >= high_risk_idx].copy()
    rep = candidates.sort_values("actual_delay_days", ascending=False).iloc[0]
    feat = rep[FEATURES].to_frame().T
    scenario_defs = {
        "Baseline high-risk project": {},
        "Supplier coordination (-5 supplier-delay days)": {"supplier_delay_days": -5},
        "Design freeze (-2 design changes)": {"design_changes_count": -2},
        "Workforce plan (+10 percentage points)": {"labor_availability_pct": 10},
        "Combined controls": {"supplier_delay_days": -5, "design_changes_count": -2, "labor_availability_pct": 10,
                             "schedule_buffer_pct": 3, "subcontractor_rating_1_5": 0.5},
    }
    scenario_rows = []
    for scenario_name, changes in scenario_defs.items():
        row = feat.copy()
        bounds = {
            "supplier_delay_days": (0, 28),
            "design_changes_count": (0, 10),
            "labor_availability_pct": (42, 100),
            "schedule_buffer_pct": (0, 20),
            "subcontractor_rating_1_5": (1, 5),
        }
        for col, delta in changes.items():
            low, high = bounds[col]
            row[col] = float(np.clip(float(row.iloc[0][col]) + delta, low, high))
        delay_hat = max(0.0, float(best_reg.predict(row)[0]))
        overrun_prob = float(best_clf.predict_proba(row)[0, 1])
        scenario_rows.append({
            "scenario": scenario_name,
            "predicted_delay_days": round(delay_hat, 2),
            "predicted_cost_overrun_probability": round(overrun_prob, 4),
            "changed_inputs": "; ".join(f"{k}: {v:+g}" for k, v in changes.items()) if changes else "None",
        })
    scen_df = pd.DataFrame(scenario_rows)
    scen_df.to_csv(PROCESSED / "week3_scenario_analysis.csv", index=False)

    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    bars = ax.bar(scen_df["scenario"], scen_df["predicted_delay_days"])
    ax.set(ylabel="Predicted delay (days)", title="Illustrative risk-control scenario analysis")
    ax.tick_params(axis="x", rotation=24, labelsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(FIGURES / "week3_05_scenario_delay_comparison.png", dpi=180); plt.close(fig)

    # Summary values for report and interpretation.
    summary = {
        "dataset_rows": int(len(df)),
        "dataset_columns": int(len(df.columns)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "mean_delay_days": round(float(df.actual_delay_days.mean()), 2),
        "median_delay_days": round(float(df.actual_delay_days.median()), 2),
        "high_delay_rate_30_days": round(float(df.high_delay_flag_30days.mean()), 3),
        "mean_cost_overrun_pct": round(float(df.cost_overrun_pct.mean()), 2),
        "cost_overrun_rate_10pct": round(float(df.cost_overrun_flag_10pct.mean()), 3),
        "projects_with_safety_incidents_rate": round(float((df.safety_incidents_simulated > 0).mean()), 3),
        "best_delay_model_by_holdout_r2": best_reg_name,
        "best_cost_overrun_model_by_holdout_roc_auc": best_clf_name,
        "delay_regression_metrics": reg_df.to_dict(orient="records"),
        "cost_overrun_classification_metrics": clf_df.to_dict(orient="records"),
        "scenario_analysis": scen_df.to_dict(orient="records"),
        "representative_project_id": str(rep["project_id"]),
        "target_definitions": {
            "actual_delay_days": "Simulated non-negative number of days beyond the planned schedule.",
            "cost_overrun_pct": "Simulated percentage difference above the planned budget; small negative values represent under-budget outcomes.",
            "cost_overrun_flag_10pct": "1 when simulated cost overrun is at least 10%; otherwise 0.",
            "high_delay_flag_30days": "1 when simulated delay is at least 30 days; otherwise 0.",
        },
        "data_caveat": "All rows and outcomes are synthetic. Holdout and cross-validation metrics demonstrate the workflow only and must not be interpreted as production performance.",
    }
    save_json(PROCESSED / "week3_risk_model_summary.json", summary)
    print(json.dumps({
        "best_delay_model": best_reg_name,
        "regression_metrics": reg_df.to_dict(orient="records"),
        "best_cost_model": best_clf_name,
        "classification_metrics": clf_df.to_dict(orient="records"),
        "scenarios": scen_df.to_dict(orient="records"),
    }, indent=2))

if __name__ == "__main__":
    build_and_evaluate()
