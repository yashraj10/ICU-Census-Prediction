"""
feature_engineering.py — Build arrival features, LOS features, and discharge hazard tables.

Extracted from notebook Steps 3–5.
All features are constructed with no target leakage (lag-only windows).
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Arrival features (Step 3)
# ---------------------------------------------------------------------------

def build_arrival_features(teletrack: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate TeleTracking bed requests into daily arrival counts and
    engineer lag / rolling / calendar features with **no leakage**.

    Parameters
    ----------
    teletrack : pd.DataFrame
        TeleTracking data with a parsed 'Bedrequest Timestamp' column.

    Returns
    -------
    pd.DataFrame
        DatetimeIndex dataframe with arrival features, NaN-free.
    """
    teletrack = teletrack.copy()
    teletrack["Bedrequest Timestamp"] = pd.to_datetime(teletrack["Bedrequest Timestamp"])
    teletrack["Date"] = teletrack["Bedrequest Timestamp"].dt.date

    daily = teletrack.groupby("Date").size().reset_index(name="arrivals")
    daily["Date"] = pd.to_datetime(daily["Date"])

    # Full date index (no gaps)
    idx = pd.date_range(daily["Date"].min(), daily["Date"].max(), freq="D")
    df = pd.DataFrame(index=idx)
    df["arrivals"] = daily.set_index("Date")["arrivals"].reindex(idx).fillna(0)

    # Lag features
    for k in [1, 3, 7, 14]:
        df[f"arrivals_lag{k}"] = df["arrivals"].shift(k)

    # Rolling stats on the *lagged* series (past-only → no leakage)
    lagged = df["arrivals"].shift(1)
    df["arrivals_ma7"] = lagged.rolling(7, min_periods=7).mean()
    df["arrivals_ma14"] = lagged.rolling(14, min_periods=14).mean()
    df["arrivals_std7"] = lagged.rolling(7, min_periods=7).std()

    # Calendar features
    df["day_of_week"] = df.index.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["month"] = df.index.month
    df["week_of_year"] = df.index.isocalendar().week.astype(int)

    features = df.dropna().copy()
    print(
        f"✅ Built arrival features: {features.shape[0]} days "
        f"({features.index.min().date()} → {features.index.max().date()})"
    )
    return features


# ---------------------------------------------------------------------------
# LOS features (Steps 4–5)
# ---------------------------------------------------------------------------

def engineer_los_features(daily_care: pd.DataFrame) -> pd.DataFrame:
    """
    Derive LOS-related features per encounter from the daily inpatient data.

    Adds columns: LOS_ICU, LOS_Med_Surg, LOS_PCU, LOS_Tele, LOS_Total,
    Has_* flags, Care_Levels_Count, LOS_Category, Patient_Type.

    Parameters
    ----------
    daily_care : pd.DataFrame
        Cleaned daily inpatient level-of-care data.

    Returns
    -------
    pd.DataFrame
        Enriched dataframe with LOS features.
    """
    df = daily_care.copy()

    # Map raw columns to standardized LOS columns
    for col in ["ICU", "Med_Surg", "PCU", "Tele", "Total"]:
        los_col = f"LOS_{col}"
        if los_col not in df.columns:
            df[los_col] = pd.to_numeric(df.get(col), errors="coerce")

    # Binary flags
    for unit in ["ICU", "Med_Surg", "PCU", "Tele"]:
        df[f"Has_{unit}"] = (df[f"LOS_{unit}"] > 0).astype(int)

    df["Care_Levels_Count"] = df[["Has_ICU", "Has_Med_Surg", "Has_PCU", "Has_Tele"]].sum(axis=1)
    df["Has_Multiple_Units"] = (df["Care_Levels_Count"] > 1).astype(int)

    # LOS category
    df["LOS_Category"] = df["LOS_Total"].apply(_categorize_los)

    # Patient type
    df["Patient_Type"] = df.apply(_classify_patient, axis=1)

    print(f"✅ Engineered LOS features for {len(df):,} encounters")
    return df


def _categorize_los(days: float) -> str:
    """Bin total LOS into clinically meaningful categories."""
    if days <= 2:
        return "1_Short (1-2 days)"
    elif days <= 7:
        return "2_Medium (3-7 days)"
    elif days <= 14:
        return "3_Long (8-14 days)"
    else:
        return "4_Extended (>14 days)"


def _classify_patient(row: pd.Series) -> str:
    """Assign a patient type label based on unit flags."""
    if row["Has_ICU"] == 1 and row["Care_Levels_Count"] == 1:
        return "ICU_only"
    if row["Has_ICU"] == 1:
        return "ICU_plus_others"
    if row["Has_Med_Surg"] == 1 and row["Care_Levels_Count"] == 1:
        return "Med_Surg_only"
    return "Other"


# ---------------------------------------------------------------------------
# ICU discharge hazard (Step 5)
# ---------------------------------------------------------------------------

def build_icu_discharge_hazard(
    daily_care: pd.DataFrame,
    max_los: int = 30,
) -> pd.DataFrame:
    """
    Compute an empirical ICU discharge hazard table:
    P(discharge on day d | still in ICU at start of day d).

    Parameters
    ----------
    daily_care : pd.DataFrame
        Must contain 'Has_ICU' and 'LOS_Total' columns (from engineer_los_features).
    max_los : int
        Cap LOS at this value to avoid thin tails (default 30).

    Returns
    -------
    pd.DataFrame
        Columns: Days_Completed, P_Discharge_Next_Day, Survival
    """
    icu = daily_care[daily_care["Has_ICU"] == 1].copy()
    icu = icu[icu["LOS_Total"].notna() & (icu["LOS_Total"] > 0)]
    icu["LOS_Capped"] = icu["LOS_Total"].clip(upper=max_los).round().astype(int)

    # Empirical PMF
    counts = icu["LOS_Capped"].value_counts().sort_index()
    all_days = pd.Index(range(1, max_los + 1), name="LOS_Day")
    counts = counts.reindex(all_days, fill_value=0)
    total = counts.sum()
    pmf = counts / total

    # Survival and hazard
    survival = 1.0 - pmf.cumsum()
    survival = pd.concat([pd.Series([1.0], index=[0]), survival])

    hazard_records = []
    for d in range(0, max_los):
        s = survival.iloc[d] if d < len(survival) else 0.0
        p = (pmf.iloc[d] / s) if s > 0 else 0.0
        hazard_records.append({
            "Days_Completed": d,
            "P_Discharge_Next_Day": round(p, 4),
            "Survival": round(s, 4),
        })

    hazard_df = pd.DataFrame(hazard_records)
    print(f"✅ Built ICU discharge hazard table ({len(hazard_df)} rows, {total:,.0f} ICU stays)")
    return hazard_df
