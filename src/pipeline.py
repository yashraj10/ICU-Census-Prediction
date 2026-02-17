"""
pipeline.py — End-to-end ICU census prediction pipeline.

Orchestrates data loading → feature engineering → model training →
census forecasting → evaluation. Run from the project root:

    python src/pipeline.py --data-dir data/

Or import individual steps:

    from src.data_loader import load_daily_care
    from src.models import train_arrival_model
"""

import argparse
from pathlib import Path

import pandas as pd

from data_loader import load_daily_care, load_teletracking
from feature_engineering import (
    build_arrival_features,
    build_icu_discharge_hazard,
    engineer_los_features,
)
from models import train_arrival_model, train_discharge_models, train_los_models
from census_simulator import expected_discharges_from_census, simulate_census_scenario
from visualizations import create_dashboard


def run_pipeline(data_dir: str, output_dir: str = "outputs") -> None:
    """
    Run the full ICU census prediction pipeline.

    Parameters
    ----------
    data_dir : str
        Directory containing the source Excel files.
    output_dir : str
        Directory for saving outputs (CSVs, plots).
    """
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 1 — Loading data")
    print("=" * 60)

    daily_care_file = next(Path(data_dir).glob("*inpatient*level*of*care*"), None)
    teletrack_file = next(Path(data_dir).glob("*Teletrack*"), None)

    if not daily_care_file or not teletrack_file:
        raise FileNotFoundError(
            f"Expected Excel files in {data_dir}. "
            "Need: Daily Inpatient Level of Care + TeleTracking files."
        )

    daily_care = load_daily_care(str(daily_care_file))
    teletrack = load_teletracking(str(teletrack_file))

    # ------------------------------------------------------------------
    # 2. Feature engineering
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 2 — Feature engineering")
    print("=" * 60)

    arrival_features = build_arrival_features(teletrack)
    arrival_features.to_csv(out / "arrival_features.csv")

    daily_care = engineer_los_features(daily_care)
    hazard_table = build_icu_discharge_hazard(daily_care)
    hazard_table.to_csv(out / "icu_discharge_hazard.csv", index=False)

    # ------------------------------------------------------------------
    # 3. Train models
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 3 — Model training & evaluation")
    print("=" * 60)

    arrival_results = train_arrival_model(arrival_features)
    arrival_results["predictions"].to_csv(out / "arrival_forecast_results.csv")

    los_results = train_los_models(daily_care)
    los_results["predictions"].to_csv(out / "los_predictions.csv", index=False)

    discharge_results = train_discharge_models(daily_care)
    discharge_results["predictions"].to_csv(out / "discharge_predictions.csv", index=False)

    # ------------------------------------------------------------------
    # 4. Census simulation
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 4 — Census simulation")
    print("=" * 60)

    holdout_preds = arrival_results["predictions"]["predicted_arrivals"]
    sim = simulate_census_scenario(
        initial_census_size=30,
        hazard_table=hazard_table,
        predicted_arrivals_series=holdout_preds,
    )
    sim.to_csv(out / "census_simulation.csv", index=False)
    print(f"✅ Simulated {len(sim)}-day census forecast")

    # ------------------------------------------------------------------
    # 5. Consolidated metrics
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 5 — Performance summary")
    print("=" * 60)

    summary = pd.DataFrame([
        {
            "Task": "Arrival Forecast (14d holdout)",
            "Model": "RandomForest",
            **arrival_results["metrics"],
        },
        {
            "Task": "LOS Regression (holdout)",
            "Model": "RandomForest",
            **los_results["metrics"].set_index("Model").loc["RandomForest"].to_dict(),
        },
        {
            "Task": "Discharge Classification",
            "Model": "LogisticRegression",
            **discharge_results["metrics"].set_index("Model").loc["LogisticRegression"].to_dict(),
        },
        {
            "Task": "Discharge Classification",
            "Model": "RandomForest",
            **discharge_results["metrics"].set_index("Model").loc["RandomForest"].to_dict(),
        },
    ])
    summary.to_csv(out / "model_performance_summary.csv", index=False)
    print(summary.to_string(index=False))

    # ------------------------------------------------------------------
    # 6. Dashboard
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 6 — Generating dashboard")
    print("=" * 60)

    create_dashboard(teletrack, daily_care, hazard_table, save_path=str(out / "dashboard.png"))

    print("\n" + "=" * 60)
    print("✅ Pipeline complete! Outputs saved to:", out.resolve())
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ICU Census Prediction Pipeline")
    parser.add_argument("--data-dir", default="data/", help="Path to raw data folder")
    parser.add_argument("--output-dir", default="outputs/", help="Path for outputs")
    args = parser.parse_args()

    run_pipeline(data_dir=args.data_dir, output_dir=args.output_dir)
