"""
feature_engineering.py
=======================
Build time-series and patient-level features for:
  - Daily arrival forecasting (lags, rolling stats, calendar features)
  - LOS analysis (category buckets, unit flags)

All rolling / lag features are computed from t-1 to prevent data leakage.

Usage:
    from src.feature_engineering import build_daily_features, build_los_features
"""

import pandas as pd
import numpy as np


# ──────────────────────────────────────────────────────────────
# Daily arrival features (for time-series forecasting)
# ──────────────────────────────────────────────────────────────
def build_daily_features(
    teletrack: pd.DataFrame,
    lags: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    """
    Aggregate TeleTracking bed requests into daily arrival counts
    and engineer time-series features.

    Parameters
    ----------
    teletrack : pd.DataFrame
        Output of ``load_teletracking()`` – must have ``date`` and
        ``LOC_Group`` columns.
    lags : list[int], optional
        Lag periods to create (default: [1, 2, 3, 7, 14]).
    rolling_windows : list[int], optional
        Rolling-stat windows (default: [3, 7, 14]).

    Returns
    -------
    pd.DataFrame
        One row per calendar day.  Columns include:
        ``date``, ``total_arrivals``, ``arrivals_<LOC>``, lag/rolling
        features, and calendar variables.

    Notes
    -----
    All rolling/lag features are shifted by 1 day so they use only
    past information (no leakage).
    """
    if lags is None:
        lags = [1, 2, 3, 7, 14]
    if rolling_windows is None:
        rolling_windows = [3, 7, 14]

    # --- aggregate ---
    daily_total = (
        teletrack.groupby("date").size().reset_index(name="total_arrivals")
    )
    daily_by_loc = (
        teletrack.groupby(["date", "LOC_Group"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    daily_by_loc.columns = ["date"] + [
        f"arrivals_{c}" for c in daily_by_loc.columns[1:]
    ]

    daily = daily_total.merge(daily_by_loc, on="date", how="left")
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)

    # --- calendar features ---
    daily["day_of_week"] = daily["date"].dt.dayofweek
    daily["is_weekend"] = (daily["day_of_week"] >= 5).astype(int)
    daily["month"] = daily["date"].dt.month
    daily["day_of_month"] = daily["date"].dt.day
    daily["iso_week"] = daily["date"].dt.isocalendar().week.astype(int)

    # --- lags (from t-1) ---
    target = "total_arrivals"
    for lag in lags:
        daily[f"lag_{lag}"] = daily[target].shift(lag)

    # --- rolling stats (from t-1 to avoid leakage) ---
    shifted = daily[target].shift(1)
    for w in rolling_windows:
        daily[f"ma_{w}"] = shifted.rolling(w).mean()
        daily[f"std_{w}"] = shifted.rolling(w).std()

    # --- LOC-specific lags ---
    for loc in ["ICU", "Med_Surg", "PCU", "Tele"]:
        col = f"arrivals_{loc}"
        if col in daily.columns:
            daily[f"{col}_lag1"] = daily[col].shift(1)
            daily[f"{col}_ma7"] = daily[col].shift(1).rolling(7).mean()

    return daily


def get_feature_columns(daily: pd.DataFrame) -> list[str]:
    """
    Return the list of model-ready feature column names
    (excludes date, target, and raw arrival counts).
    """
    exclude_prefixes = ("date", "total_arrivals")
    exclude_exact = {
        "arrivals_ICU", "arrivals_Med_Surg", "arrivals_PCU",
        "arrivals_Tele", "arrivals_Other",
    }
    return [
        c
        for c in daily.columns
        if c not in exclude_exact
        and not c.startswith(exclude_prefixes)
        and c != "date"
        and c != "total_arrivals"
    ]


# ──────────────────────────────────────────────────────────────
# LOS features (for encounter-level analysis)
# ──────────────────────────────────────────────────────────────
LOS_BINS = [0, 2, 7, 14, float("inf")]
LOS_LABELS = ["Short (1-2d)", "Medium (3-7d)", "Long (8-14d)", "Extended (>14d)"]


def build_los_features(
    daily_care: pd.DataFrame,
    unit_col: str = "ICU",
    cap: int = 30,
) -> pd.DataFrame:
    """
    For patients with time in *unit_col*, compute LOS category and
    a log-transformed LOS.

    Parameters
    ----------
    daily_care : pd.DataFrame
        Encounter-level frame with unit flags already added.
    unit_col : str
        Which unit column to analyse (ICU, Med_Surg, PCU, Tele).
    cap : int
        Cap LOS at this many days for modelling purposes.

    Returns
    -------
    pd.DataFrame
        Filtered to patients with ``unit_col > 0``, with new columns:
        ``LOS_capped``, ``LOS_log``, ``LOS_category``.
    """
    df = daily_care[daily_care[unit_col] > 0].copy()
    df["LOS_capped"] = df[unit_col].clip(upper=cap)
    df["LOS_log"] = np.log1p(df["LOS_capped"])
    df["LOS_category"] = pd.cut(
        df[unit_col], bins=LOS_BINS, labels=LOS_LABELS, right=True
    )
    return df


def los_summary(daily_care: pd.DataFrame) -> pd.DataFrame:
    """
    Return a summary table of LOS statistics for every unit.
    """
    records = []
    for unit, col in [("ICU", "ICU"), ("Med_Surg", "Med_Surg"),
                      ("PCU", "PCU"), ("Tele", "Tele")]:
        pts = daily_care[daily_care[col] > 0][col]
        if len(pts) == 0:
            continue
        records.append({
            "Unit": unit,
            "N_patients": len(pts),
            "Mean_LOS": round(pts.mean(), 2),
            "Median_LOS": pts.median(),
            "Std_LOS": round(pts.std(), 2),
            "Short_pct": round(100 * (pts <= 2).sum() / len(pts), 1),
            "Medium_pct": round(100 * ((pts > 2) & (pts <= 7)).sum() / len(pts), 1),
            "Long_pct": round(100 * ((pts > 7) & (pts <= 14)).sum() / len(pts), 1),
            "Extended_pct": round(100 * (pts > 14).sum() / len(pts), 1),
        })
    return pd.DataFrame(records)
