"""Generate a transparent synthetic dataset for construction project risk modeling.

This dataset is simulated for training and portfolio demonstration; it is not real project data.
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 73
N = 500
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "construction_risk_simulated.csv"


def main():
    rng = np.random.default_rng(SEED)
    project_type = rng.choice(
        ["Residential", "Commercial", "Infrastructure", "Industrial"],
        size=N,
        p=[0.32, 0.28, 0.24, 0.16],
    )
    project_scale = rng.choice(["Small", "Medium", "Large"], size=N, p=[0.27, 0.47, 0.26])
    scale_value = np.select([project_scale == "Small", project_scale == "Medium", project_scale == "Large"], [18, 65, 180])
    planned_duration = np.select([project_scale == "Small", project_scale == "Medium", project_scale == "Large"], [120, 260, 520])
    planned_duration = np.maximum(60, planned_duration + rng.normal(0, np.select([project_scale == "Small", project_scale == "Medium", project_scale == "Large"], [18, 34, 65]), N)).round().astype(int)
    contract_value = np.maximum(5, scale_value * rng.lognormal(mean=0.0, sigma=0.32, size=N)).round(2)
    complexity = rng.integers(1, 6, size=N)
    rainfall_days = np.clip(rng.poisson(lam=9, size=N) + (project_type == "Infrastructure") * rng.binomial(6, 0.35, N), 0, 30)
    supplier_delay_days = np.clip(rng.gamma(shape=2.0, scale=4.0, size=N).round().astype(int), 0, 28)
    labor_availability_pct = np.clip(rng.normal(78, 11, size=N), 42, 100).round(1)
    design_changes_count = np.clip(rng.poisson(lam=2.2, size=N) + (complexity >= 4) * rng.binomial(2, 0.35, N), 0, 10)
    ground_risk_score = rng.integers(1, 6, size=N)
    safety_training_score = np.clip(rng.normal(76, 12, size=N), 35, 100).round(1)
    schedule_buffer_pct = np.clip(rng.normal(8.5, 4.0, size=N), 0, 20).round(1)
    subcontractor_rating = np.clip(rng.normal(3.4, 0.8, size=N), 1.0, 5.0).round(1)
    inspection_rework_events = np.clip(rng.poisson(lam=1.4, size=N) + (safety_training_score < 60) * rng.binomial(3, 0.25, N), 0, 9)

    # Outcomes use explicit relationships plus noise to create a realistic teaching exercise.
    type_delay = pd.Series(project_type).map({"Residential": 0.0, "Commercial": 2.0, "Infrastructure": 5.5, "Industrial": 3.5}).to_numpy()
    delay_noise = rng.normal(0, 8.0, size=N)
    delay_days = (
        2.5
        + 0.78 * supplier_delay_days
        + 0.52 * rainfall_days
        + 3.0 * (complexity - 1)
        + 3.8 * design_changes_count
        + 0.30 * np.maximum(0, 80 - labor_availability_pct)
        + 2.25 * (ground_risk_score - 1)
        + 2.8 * inspection_rework_events
        - 0.48 * schedule_buffer_pct
        - 2.2 * (subcontractor_rating - 3)
        + type_delay
        + delay_noise
    )
    delay_days = np.clip(delay_days, 0, None).round(1)

    type_cost = pd.Series(project_type).map({"Residential": 0.0, "Commercial": 0.7, "Infrastructure": 1.5, "Industrial": 1.0}).to_numpy()
    cost_noise = rng.normal(0, 2.7, size=N)
    cost_overrun_pct = (
        1.1
        + 0.13 * supplier_delay_days
        + 0.085 * rainfall_days
        + 0.62 * (complexity - 1)
        + 0.62 * design_changes_count
        + 0.045 * np.maximum(0, 80 - labor_availability_pct)
        + 0.54 * (ground_risk_score - 1)
        + 0.52 * inspection_rework_events
        - 0.055 * schedule_buffer_pct
        - 0.62 * (subcontractor_rating - 3)
        + type_cost
        + cost_noise
    )
    cost_overrun_pct = np.clip(cost_overrun_pct, -3.0, 35.0).round(2)
    cost_overrun_flag = (cost_overrun_pct >= 10.0).astype(int)
    high_delay_flag = (delay_days >= 30.0).astype(int)

    # Simulated safety incidents are count data; included as a risk outcome for prioritisation.
    safety_rate = np.exp(
        -1.2
        + 0.23 * (complexity - 1)
        + 0.38 * (ground_risk_score - 1)
        + 0.55 * (safety_training_score < 60)
        + 0.15 * inspection_rework_events
        - 0.025 * (safety_training_score - 70)
    )
    safety_incidents = rng.poisson(np.clip(safety_rate, 0.03, 5.5))

    df = pd.DataFrame({
        "project_id": [f"CP-{i:04d}" for i in range(1, N + 1)],
        "project_type": project_type,
        "project_scale": project_scale,
        "contract_value_inr_mn": contract_value,
        "planned_duration_days": planned_duration,
        "complexity_score_1_5": complexity,
        "rainfall_days": rainfall_days,
        "supplier_delay_days": supplier_delay_days,
        "labor_availability_pct": labor_availability_pct,
        "design_changes_count": design_changes_count,
        "ground_risk_score_1_5": ground_risk_score,
        "safety_training_score": safety_training_score,
        "schedule_buffer_pct": schedule_buffer_pct,
        "subcontractor_rating_1_5": subcontractor_rating,
        "inspection_rework_events": inspection_rework_events,
        "actual_delay_days": delay_days,
        "cost_overrun_pct": cost_overrun_pct,
        "cost_overrun_flag_10pct": cost_overrun_flag,
        "high_delay_flag_30days": high_delay_flag,
        "safety_incidents_simulated": safety_incidents,
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {len(df)} simulated projects to {OUT}")
    print(f"High delay rate: {df.high_delay_flag_30days.mean():.3f}")
    print(f"Cost overrun >=10% rate: {df.cost_overrun_flag_10pct.mean():.3f}")
    print(f"Mean delay: {df.actual_delay_days.mean():.2f} days")
    print(f"Mean cost overrun: {df.cost_overrun_pct.mean():.2f}%")

if __name__ == "__main__":
    main()
