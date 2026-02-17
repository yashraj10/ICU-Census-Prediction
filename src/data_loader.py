"""
data_loader.py — Load and clean Daily Inpatient Level of Care and TeleTracking data.

Extracted from notebook Steps 1–2.
Handles header detection, column renaming, and timestamp parsing.
"""

import os
import pandas as pd
import numpy as np


def load_daily_care(filepath: str) -> pd.DataFrame:
    """
    Load the Daily Inpatient Level of Care Excel file.

    Automatically detects the header row by searching for 'Proxy Enc ID'
    in the first column, then re-reads the file using that row as the header.

    Parameters
    ----------
    filepath : str
        Path to the Daily Inpatient Level of Care .xlsx file.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with standardized column names.
    """
    # Preview raw file to find the real header row
    preview = pd.read_excel(filepath, header=None, nrows=20)
    header_row_idx = preview[preview.iloc[:, 0] == "Proxy Enc ID"].index[0]

    # Re-load using detected header
    df = pd.read_excel(filepath, skiprows=header_row_idx)

    # Standardize column names
    df = df.rename(columns={
        "Proxy Enc ID": "Proxy_Enc_ID",
        "Med/Surg": "Med_Surg",
    })

    print(f"✅ Loaded Daily Inpatient Data: {df.shape[0]:,} rows × {df.shape[1]} cols")
    return df


def load_teletracking(filepath: str) -> pd.DataFrame:
    """
    Load the TeleTracking Excel file and parse timestamps.

    Parameters
    ----------
    filepath : str
        Path to the TeleTracking .xlsx file.

    Returns
    -------
    pd.DataFrame
        TeleTracking data with parsed 'Bedrequest Timestamp' and derived 'Date' column.
    """
    df = pd.read_excel(filepath)
    df["Bedrequest Timestamp"] = pd.to_datetime(df["Bedrequest Timestamp"])
    df["Date"] = df["Bedrequest Timestamp"].dt.date

    print(f"✅ Loaded TeleTracking Data: {df.shape[0]:,} rows × {df.shape[1]} cols")
    return df


def list_healthcare_files(folder: str) -> list[str]:
    """List all .xlsx files in the healthcare data folder."""
    if not os.path.exists(folder):
        raise FileNotFoundError(f"Healthcare folder not found: {folder}")

    files = [f for f in os.listdir(folder) if f.lower().endswith(".xlsx")]
    for f in files:
        size_mb = os.path.getsize(os.path.join(folder, f)) / (1024 * 1024)
        print(f"  📊 {f} ({size_mb:.2f} MB)")
    return files
