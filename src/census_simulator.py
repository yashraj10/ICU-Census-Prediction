"""
census_simulator.py — Forecast ICU bed occupancy using the arrival + discharge pipeline.

Extracted from notebook Steps 6–7.
Combines arrival predictions with the LOS-based discharge hazard model
to project next-day ICU census via a simple balance equation.
"""

import numpy as np
import pandas as pd


def expected_discharges_from_census(
    census_df: pd.DataFrame,
    hazard_table: pd.DataFrame,
) -> tuple[pd.DataFrame, float]:
    """
    Given a current ICU census and a discharge hazard table, compute
    the expected number of discharges tomorrow.

    Parameters
    ----------
    census_df : pd.DataFrame
        One row per ICU patient; must contain a 'Days_Completed' column.
    hazard_table : pd.DataFrame
        Output of build_icu_discharge_hazard(); must contain
        'Days_Completed' and 'P_Discharge_Next_Day'.

    Returns
    -------
    merged : pd.DataFrame
        census_df joined with discharge probabilities.
    expected_total : float
        Sum of per-patient discharge probabilities (expected discharges).
    """
    merged = census_df.merge(
        hazard_table[["Days_Completed", "P_Discharge_Next_Day"]],
        on="Days_Completed",
        how="left",
    )
    merged["Expected_Discharge_Next_Day"] = merged["P_Discharge_Next_Day"].fillna(0.0)
    expected_total = merged["Expected_Discharge_Next_Day"].sum()
    return merged, expected_total


def forecast_icu_census_one_day(
    current_census_size: int,
    predicted_arrivals: float,
    expected_discharges: float,
) -> float:
    """
    Simple ICU census balance equation:
        Census_{t+1} = Census_t + Arrivals_{t+1} − Expected_Discharges_{t+1}

    Parameters
    ----------
    current_census_size : int
        Number of ICU patients today.
    predicted_arrivals : float
        Forecasted new ICU admissions for tomorrow.
    expected_discharges : float
        Expected ICU discharges for tomorrow (from hazard model).

    Returns
    -------
    float
        Forecasted ICU census for tomorrow.
    """
    return current_census_size + predicted_arrivals - expected_discharges


def simulate_census_scenario(
    initial_census_size: int,
    hazard_table: pd.DataFrame,
    predicted_arrivals_series: pd.Series,
    max_los: int = 30,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Run a multi-day ICU census simulation using the balance equation.

    Parameters
    ----------
    initial_census_size : int
        Starting ICU census.
    hazard_table : pd.DataFrame
        Discharge hazard table.
    predicted_arrivals_series : pd.Series
        Daily predicted arrival counts (indexed by date).
    max_los : int
        Maximum LOS for sampling initial census days-on-service.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Columns: date, census, arrivals, expected_discharges
    """
    np.random.seed(seed)

    # Bootstrap initial census days-on-service
    days_completed = np.random.choice(
        hazard_table["Days_Completed"].values,
        size=initial_census_size,
        replace=True,
    )

    records = []
    census_size = initial_census_size

    for date, arrivals in predicted_arrivals_series.items():
        census_df = pd.DataFrame({"Days_Completed": days_completed[:census_size]})
        _, exp_disch = expected_discharges_from_census(census_df, hazard_table)

        forecast = forecast_icu_census_one_day(census_size, arrivals, exp_disch)
        forecast = max(0, round(forecast))

        records.append({
            "date": date,
            "census": forecast,
            "arrivals": arrivals,
            "expected_discharges": round(exp_disch, 2),
        })
        census_size = forecast

        # Refresh days-on-service (simplified: sample from hazard support)
        days_completed = np.random.choice(
            hazard_table["Days_Completed"].values,
            size=max(census_size, 1),
            replace=True,
        )

    return pd.DataFrame(records)
