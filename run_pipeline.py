#!/usr/bin/env python3
"""
run_pipeline.py
================
End-to-end pipeline runner.

    python run_pipeline.py --care "data/Daily inpatient level of care.xlsx" \
                           --tele "data/Teletracking02.24_01.25DEID.xlsx" \
                           --output outputs/

Steps:
    1. Load & clean data
    2. Engineer features
    3. Train arrival models
    4. Train short-stay classifiers (ICU, PCU, Tele)
    5. Build discharge hazard tables
    6. Simulate ICU census forecast
    7. Generate dashboard plots
    8. Save all results
"""

import argparse
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from src.data_loading import load_daily_care, load_teletracking, add_encounter_flags
from src.feature_engineering import (
    build_daily_features,
    get_feature_columns,
    build_los_features,
    los_summary,
)
from src.models import (
    train_arrival_models,
    train_short_stay_classifier,
    build_hazard_table,
    get_hazard_array,
    feature_importance,
)
from src.census_forecast import simulate_census, assign_status, census_summary
from src.visualization import plot_dashboard


def main(care_path: str, tele_path: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    # ──────────────────────────────────────────────────────────
    # 1. Load data
    # ──────────────────────────────────────────────────────────
    print("=" * 60)
    print("STEP 1: Loading data")
    print("=" * 60)

    daily_care = load_daily_care(care_path)
    daily_care = add_encounter_flags(daily_care)
    teletrack = load_teletracking(tele_path)

    print(f"  Daily Care:   {daily_care.shape[0]:,} encounters")
    print(f"  TeleTracking: {teletrack.shape[0]:,} bed requests")
    print(f"  Date range:   {teletrack['date'].min()} → {teletrack['date'].max()}")

    # ──────────────────────────────────────────────────────────
    # 2. Feature engineering
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Feature engineering")
    print("=" * 60)

    daily = build_daily_features(teletrack)
    feat_cols = get_feature_columns(daily)
    print(f"  Daily features: {len(feat_cols)} columns")

    los_table = los_summary(daily_care)
    print(f"\n  LOS Summary:\n{los_table.to_string(index=False)}")

    # ──────────────────────────────────────────────────────────
    # 3. Arrival models
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Arrival models")
    print("=" * 60)

    arrival_results, arrival_test = train_arrival_models(daily, feat_cols)
    for r in arrival_results:
        print(f"  {r.summary()}")

    # Feature importance from the best tree model
    best_tree = [r for r in arrival_results if r.model is not None][0]
    fi = feature_importance(best_tree.model, feat_cols)
    print(f"\n  Top features:\n{fi.to_string()}")

    # ──────────────────────────────────────────────────────────
    # 4. Short-stay classifiers
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Short-stay classifiers")
    print("=" * 60)

    clf_results = []
    for unit in ["ICU", "PCU", "Tele"]:
        results = train_short_stay_classifier(daily_care, unit_col=unit)
        clf_results.extend(results)
        for r in results:
            print(f"  {r.summary()}")

    # ──────────────────────────────────────────────────────────
    # 5. Hazard tables
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: Discharge hazard tables")
    print("=" * 60)

    hazard_tables = {}
    for unit, col in [("ICU", "ICU"), ("PCU", "PCU"), ("Tele", "Tele")]:
        los = daily_care[daily_care[col] > 0][col]
        ht = build_hazard_table(los)
        hazard_tables[unit] = ht
        print(f"\n  {unit} hazard (day 1/2/3/7/14):")
        for d in [1, 2, 3, 7, 14]:
            row = ht[ht["day"] == d]
            if not row.empty:
                print(f"    Day {d:2d}: {row.iloc[0]['hazard']:.3f}")

    # ──────────────────────────────────────────────────────────
    # 6. Census forecast
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: ICU Census forecast")
    print("=" * 60)

    icu_daily = (
        teletrack[teletrack["LOC_Group"] == "ICU"]
        .groupby("date")
        .size()
        .reset_index(name="icu_arrivals")
    )
    icu_daily["date"] = pd.to_datetime(icu_daily["date"])
    arrivals_dict = dict(zip(icu_daily["date"], icu_daily["icu_arrivals"]))

    hazard_arr = get_hazard_array(hazard_tables["ICU"])

    census_df = simulate_census(arrivals_dict, hazard_arr, mode="stochastic")
    census_df = assign_status(census_df)
    summary = census_summary(census_df)

    print(f"  {summary}")

    # ──────────────────────────────────────────────────────────
    # 7. Plots
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 7: Generating dashboard")
    print("=" * 60)

    fig = plot_dashboard(
        census_df=census_df,
        arrival_test=arrival_test,
        daily_df=daily,
        daily_care=daily_care,
        hazard_df=hazard_tables["ICU"],
    )
    fig.savefig(os.path.join(output_dir, "dashboard.png"), dpi=150, bbox_inches="tight")
    print(f"  Saved dashboard.png")

    # ──────────────────────────────────────────────────────────
    # 8. Save CSVs
    # ──────────────────────────────────────────────────────────
    census_df.to_csv(os.path.join(output_dir, "icu_census_forecast.csv"), index=False)
    arrival_test.to_csv(os.path.join(output_dir, "arrival_test_results.csv"), index=False)
    los_table.to_csv(os.path.join(output_dir, "los_summary.csv"), index=False)

    for unit, ht in hazard_tables.items():
        ht.to_csv(os.path.join(output_dir, f"hazard_{unit}.csv"), index=False)

    # Model performance summary
    perf = []
    for r in arrival_results:
        perf.append({"Type": "Regression", **r.summary()})
    for r in clf_results:
        perf.append({"Type": "Classification", **r.summary()})
    pd.DataFrame(perf).to_csv(os.path.join(output_dir, "model_performance.csv"), index=False)

    print(f"  All outputs saved to {output_dir}/")
    print("\n✅ Pipeline complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ICU Census Prediction Pipeline")
    parser.add_argument("--care", required=True, help="Path to Daily Inpatient Level of Care .xlsx")
    parser.add_argument("--tele", required=True, help="Path to TeleTracking .xlsx")
    parser.add_argument("--output", default="outputs", help="Output directory")
    args = parser.parse_args()

    main(args.care, args.tele, args.output)
