"""
census_forecast.py
===================
Simulate ICU census over time using:
    Next-day census = Current census + Arrivals − Expected discharges

Supports both stochastic (random draws from hazard) and deterministic
(expected-value) simulation modes.

Usage:
    from src.census_forecast import simulate_census, assign_status
"""

import numpy as np
import pandas as pd
from typing import Literal


def simulate_census(
    arrivals_by_date: dict[pd.Timestamp, int],
    hazard: np.ndarray,
    start_date: pd.Timestamp | None = None,
    end_date: pd.Timestamp | None = None,
    mode: Literal["stochastic", "deterministic"] = "stochastic",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Simulate daily ICU census using arrival counts and a hazard table.

    Parameters
    ----------
    arrivals_by_date : dict
        Mapping from date → number of new ICU arrivals that day.
    hazard : np.ndarray
        hazard[d] = P(discharge on day d | in ICU on day d).
        Index 0 is unused; day 1 is the first ICU day.
    start_date, end_date : pd.Timestamp, optional
        Date range to simulate.  Defaults to the full range of
        *arrivals_by_date*.
    mode : str
        "stochastic"   — each patient is discharged with probability
                          hazard[los] via a Bernoulli draw.
        "deterministic" — remove round(sum of hazards) patients per day,
                          prioritising highest-probability patients.
    seed : int
        Random seed (only used in stochastic mode).

    Returns
    -------
    pd.DataFrame
        Columns: date, census, arrivals, discharges, expected_discharges.
    """
    if start_date is None:
        start_date = min(arrivals_by_date.keys())
    if end_date is None:
        end_date = max(arrivals_by_date.keys())

    max_day = len(hazard) - 1
    dates = pd.date_range(start_date, end_date)
    rng = np.random.default_rng(seed)

    patients: list[int] = []  # current LOS for each patient in unit
    history = []

    for dt in dates:
        # Age all patients by 1 day
        patients = [los + 1 for los in patients]

        # New arrivals (LOS = 1)
        new = arrivals_by_date.get(dt, 0)
        patients.extend([1] * new)

        # Expected discharges (always computed)
        expected_disch = sum(
            hazard[min(int(los), max_day)] for los in patients
        )

        # Actual discharges
        if mode == "stochastic":
            remaining = []
            discharged = 0
            for los in patients:
                p = hazard[min(int(los), max_day)]
                if rng.random() < p:
                    discharged += 1
                else:
                    remaining.append(los)
            patients = remaining
        else:
            # Deterministic: remove highest-probability patients
            to_remove = int(round(expected_disch))
            discharged = min(to_remove, len(patients))
            if discharged > 0:
                probs = [
                    (i, hazard[min(int(los), max_day)])
                    for i, los in enumerate(patients)
                ]
                probs.sort(key=lambda x: -x[1])
                remove_idx = {probs[i][0] for i in range(discharged)}
                patients = [
                    los for i, los in enumerate(patients) if i not in remove_idx
                ]

        history.append({
            "date": dt,
            "census": len(patients),
            "arrivals": new,
            "discharges": discharged,
            "expected_discharges": round(expected_disch, 2),
        })

    return pd.DataFrame(history)


# ──────────────────────────────────────────────────────────────
# Capacity status thresholds
# ──────────────────────────────────────────────────────────────
def assign_status(
    census_df: pd.DataFrame,
    capacity: int | None = None,
    safe_pct: float = 80,
    near_full_pct: float = 95,
) -> pd.DataFrame:
    """
    Assign SAFE / NEAR FULL / AT RISK status based on census vs capacity.

    Parameters
    ----------
    census_df : pd.DataFrame
        Must have a ``census`` column.
    capacity : int, optional
        Bed capacity.  If None, the 95th percentile of census is used.
    safe_pct : float
        Below this % of capacity → SAFE.
    near_full_pct : float
        Between safe_pct and this → NEAR FULL; above → AT RISK.

    Returns
    -------
    pd.DataFrame
        With added columns: capacity, pct_full, status.
    """
    df = census_df.copy()

    if capacity is None:
        capacity = int(df["census"].quantile(0.95))

    df["capacity"] = capacity
    df["pct_full"] = (df["census"] / capacity * 100).round(1)
    df["status"] = pd.cut(
        df["pct_full"],
        bins=[0, safe_pct, near_full_pct, float("inf")],
        labels=["SAFE", "NEAR FULL", "AT RISK"],
    )

    return df


def census_summary(census_df: pd.DataFrame) -> dict:
    """
    Return a dict of key census statistics.
    """
    return {
        "mean_census": round(census_df["census"].mean(), 1),
        "std_census": round(census_df["census"].std(), 1),
        "min_census": int(census_df["census"].min()),
        "max_census": int(census_df["census"].max()),
        "mean_arrivals": round(census_df["arrivals"].mean(), 1),
        "mean_discharges": round(census_df["discharges"].mean(), 1),
        "safe_days": int((census_df["status"] == "SAFE").sum()),
        "near_full_days": int((census_df["status"] == "NEAR FULL").sum()),
        "at_risk_days": int((census_df["status"] == "AT RISK").sum()),
        "total_days": len(census_df),
    }
