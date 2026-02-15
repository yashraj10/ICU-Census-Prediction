"""
data_loading.py
================
Load, clean, and validate the two raw hospital datasets:
  1. Daily Inpatient Level of Care  (encounter-level IP days by unit)
  2. TeleTracking ED Bed Requests   (bed requests with timestamps)

Usage:
    from src.data_loading import load_daily_care, load_teletracking

    daily_care = load_daily_care("path/to/Daily inpatient level of care.xlsx")
    teletrack  = load_teletracking("path/to/Teletracking02.24_01.25DEID.xlsx")
"""

import pandas as pd
import numpy as np


# ──────────────────────────────────────────────────────────────
# Daily Inpatient Level of Care
# ──────────────────────────────────────────────────────────────
def load_daily_care(filepath: str) -> pd.DataFrame:
    """
    Load the Daily Inpatient Level of Care Excel file.

    The raw file has metadata rows above the real header.
    This function auto-detects the header row ('Proxy Enc ID'),
    reloads with the correct offset, standardises column names,
    and drops the trailing summary row.

    Parameters
    ----------
    filepath : str
        Path to the .xlsx file.

    Returns
    -------
    pd.DataFrame
        Columns: Proxy_Enc_ID, ICU, Med_Surg, PCU, Tele, Total
        All LOS columns are int; NaN → 0.
    """
    # 1. Preview raw rows to find the header
    preview = pd.read_excel(filepath, header=None, nrows=20)
    header_mask = preview.iloc[:, 0] == "Proxy Enc ID"
    if not header_mask.any():
        raise ValueError(
            "Could not locate 'Proxy Enc ID' header row in the first 20 rows."
        )
    header_row_idx = header_mask.idxmax()

    # 2. Reload with proper header
    df = pd.read_excel(filepath, skiprows=header_row_idx)
    df = df.rename(columns={
        "Proxy Enc ID": "Proxy_Enc_ID",
        "Med/Surg": "Med_Surg",
    })

    # 3. Drop summary / total rows
    df = df[df["Proxy_Enc_ID"] != "Total"].copy()

    # 4. Cast LOS columns to int (NaN → 0)
    los_cols = ["ICU", "Med_Surg", "PCU", "Tele", "Total"]
    for col in los_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 5. Basic validation
    assert df.shape[0] > 0, "No encounter rows found after cleaning."
    assert (df["Total"] >= 0).all(), "Negative Total LOS detected."

    return df.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────
# TeleTracking ED Bed Requests
# ──────────────────────────────────────────────────────────────
# Mapping from raw "Requested Level Of Care" values to standard groups
LOC_MAP = {
    "ICU": "ICU",
    "Medical / Surgical": "Med_Surg",
    "Step Down/PCU": "PCU",
    "Telemetry": "Tele",
}


def load_teletracking(filepath: str) -> pd.DataFrame:
    """
    Load the TeleTracking ED Bed Request Excel file.

    Converts the bed-request timestamp to datetime, creates a
    plain `date` column, and maps *Requested Level Of Care* into
    four standard groups (ICU, Med_Surg, PCU, Tele) plus 'Other'.

    Parameters
    ----------
    filepath : str
        Path to the .xlsx file.

    Returns
    -------
    pd.DataFrame
        Original columns plus: date (datetime.date), LOC_Group (str).
    """
    df = pd.read_excel(filepath)

    # Normalise timestamp
    df["Bedrequest Timestamp"] = pd.to_datetime(
        df["Bedrequest Timestamp"], errors="coerce"
    )
    df["date"] = df["Bedrequest Timestamp"].dt.date

    # Standard level-of-care grouping
    df["LOC_Group"] = (
        df["Requested Level Of Care"].map(LOC_MAP).fillna("Other")
    )

    # Validation
    assert df["Bedrequest Timestamp"].notna().sum() > 0, "No valid timestamps."

    return df


# ──────────────────────────────────────────────────────────────
# Convenience: add derived flags to the daily care frame
# ──────────────────────────────────────────────────────────────
def add_encounter_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add binary flags and proportions to the encounter-level frame.

    New columns
    -----------
    Has_ICU, Has_Med_Surg, Has_PCU, Has_Tele  : 0/1
    Care_Levels_Count   : int (1–4)
    Has_Multiple_Units  : 0/1
    ICU_Proportion      : float (ICU days / Total days)
    """
    df = df.copy()
    for unit in ["ICU", "Med_Surg", "PCU", "Tele"]:
        df[f"Has_{unit}"] = (df[unit] > 0).astype(int)

    df["Care_Levels_Count"] = df[
        ["Has_ICU", "Has_Med_Surg", "Has_PCU", "Has_Tele"]
    ].sum(axis=1)

    df["Has_Multiple_Units"] = (df["Care_Levels_Count"] > 1).astype(int)
    df["ICU_Proportion"] = df["ICU"] / df["Total"].replace(0, np.nan)

    return df


# ──────────────────────────────────────────────────────────────
# Quick test
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    care_path = sys.argv[1] if len(sys.argv) > 1 else "data/Daily inpatient level of care.xlsx"
    tele_path = sys.argv[2] if len(sys.argv) > 2 else "data/Teletracking02.24_01.25DEID.xlsx"

    dc = load_daily_care(care_path)
    print(f"Daily Care:   {dc.shape[0]:,} encounters, {dc.shape[1]} cols")

    tt = load_teletracking(tele_path)
    print(f"TeleTracking: {tt.shape[0]:,} bed requests, {tt.shape[1]} cols")
    print(f"Date range:   {tt['date'].min()} → {tt['date'].max()}")
