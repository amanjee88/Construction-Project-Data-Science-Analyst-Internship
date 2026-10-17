"""Generate a deterministic synthetic construction-project dataset for Week 2.

This data is simulated for educational use. It is not an observed industry dataset.
Run from repository root: python src/generate_week2_simulated_data.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "construction_projects_eda_simulated.csv"


def generate_data(n: int = 250, seed: int = 20261017) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    types = np.array(["Residential", "Commercial", "Road", "Bridge", "Hospital", "School", "Industrial"])
    probs = np.array([0.23, 0.18, 0.17, 0.10, 0.10, 0.12, 0.10])
    project_type = rng.choice(types, size=n, p=probs)
    type_duration = {"Residential": 250, "Commercial": 340, "Road": 310, "Bridge": 420,
                     "Hospital": 390, "School": 285, "Industrial": 365}
    type_budget = {"Residential": 3200, "Commercial": 5400, "Road": 4100, "Bridge": 6700,
                   "Hospital": 7200, "School": 2900, "Industrial": 6100}
    duration_base = np.array([type_duration[t] for t in project_type])
    budget_base = np.array([type_budget[t] for t in project_type], dtype=float)

    planned_duration = np.clip(np.round(duration_base + rng.normal(0, 75, n)), 100, 850).astype(int)
    contractor_experience = rng.integers(1, 31, n)
    labor_count = np.clip(np.round(rng.normal(125, 48, n)), 25, 280).astype(int)
    equipment_hours = np.clip(np.round(planned_duration * labor_count * rng.uniform(0.18, 0.42, n)), 1000, 80000).astype(int)
    material_index = np.clip(rng.normal(113, 13, n), 82, 158).round(2)
    procurement_delay = np.clip(np.round(rng.gamma(2.0, 12.0, n)), 0, 90).astype(int)
    weather_delay = np.clip(np.round(rng.gamma(1.8, 6.5, n)), 0, 55).astype(int)
    safety_incidents = np.clip(rng.poisson(2.1, n), 0, 11).astype(int)

    type_delay = {"Residential": 1, "Commercial": 5, "Road": 7, "Bridge": 11,
                  "Hospital": 8, "School": 2, "Industrial": 6}
    delay_noise = rng.normal(0, 15, n)
    schedule_delay = (3 + 0.69 * procurement_delay + 0.57 * weather_delay
                      - 0.78 * (contractor_experience - 10)
                      + np.array([type_delay[t] for t in project_type])
                      + 0.65 * safety_incidents + delay_noise)
    schedule_delay = np.clip(np.round(schedule_delay), -35, 210).astype(int)
    actual_duration = np.maximum(60, planned_duration + schedule_delay).astype(int)

    budget = budget_base * (planned_duration / duration_base) * rng.uniform(0.78, 1.28, n)
    budget = np.round(budget, 2)
    cost_noise = rng.normal(0, 3.2, n)
    cost_overrun_pct = (-2.2 + 0.075 * procurement_delay + 0.14 * (material_index - 100)
                        + 0.62 * safety_incidents - 0.095 * (contractor_experience - 10)
                        + 0.025 * weather_delay + cost_noise)
    cost_overrun_pct = np.clip(cost_overrun_pct, -18, 48).round(2)
    actual_cost = np.round(budget * (1 + cost_overrun_pct / 100), 2)

    states = rng.choice(["Uttar Pradesh", "Maharashtra", "Karnataka", "Kerala", "Tamil Nadu", "Rajasthan", "Gujarat"], n)
    region = pd.Series(states).map({"Uttar Pradesh":"North", "Rajasthan":"North", "Maharashtra":"West", "Gujarat":"West", "Karnataka":"South", "Kerala":"South", "Tamil Nadu":"South"}).to_numpy()
    project_id = [f"EDA{j:04d}" for j in range(1, n + 1)]
    df = pd.DataFrame({
        "project_id": project_id,
        "project_type": project_type,
        "state": states,
        "region": region,
        "planned_duration_days": planned_duration,
        "actual_duration_days": actual_duration,
        "schedule_delay_days": schedule_delay,
        "planned_budget_inr_lakh": budget,
        "actual_final_cost_inr_lakh": actual_cost,
        "cost_overrun_pct": cost_overrun_pct,
        "contractor_experience_years": contractor_experience,
        "labor_count": labor_count,
        "equipment_hours": equipment_hours,
        "material_cost_index": material_index,
        "procurement_delay_days": procurement_delay,
        "weather_delay_days": weather_delay,
        "safety_incidents": safety_incidents,
        "on_time_delivery": (schedule_delay <= 0).astype(int),
        "cost_overrun_over_10pct": (cost_overrun_pct > 10).astype(int),
    })
    return df

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = generate_data()
    data.to_csv(OUT, index=False)
    print(f"Wrote {len(data)} synthetic project rows to {OUT.relative_to(ROOT)}")
