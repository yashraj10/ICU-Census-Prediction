"""
save_models.py — Train and serialize all models for the API.

Run from project root:
    python save_models.py

This creates the models/ directory with:
  - arrival_rf.joblib
  - los_ridge.joblib
  - short_stay_logit.joblib
  - icu_hazard_table.csv
  - model_metadata.json

The API (src/api.py) loads these files on startup.

Add this file to: save_models.py  (project root)
"""

import json
from math import sqrt
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    roc_auc_score, precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split


# ── Config ───────────────────────────────────────────────────────

TELETRACK_PATH = "Teletracking02.24_01.25DEID (3).xlsx"
DAILY_CARE_PATH = "Daily inpatient level of care.xlsx"
OUTPUT_DIR = "models"

CARE_UNITS = ["ICU", "Med_Surg", "PCU", "Tele"]
ARRIVAL_FEATURE_COLS = [
    "arrivals_lag1", "arrivals_lag3", "arrivals_lag7", "arrivals_lag14",
    "arrivals_ma7", "arrivals_ma14", "arrivals_std7",
    "day_of_week", "is_weekend", "month", "week_of_year",
]
LOS_FEATURE_COLS = [
    "Has_ICU", "Has_Med_Surg", "Has_PCU", "Has_Tele",
    "Care_Levels_Count", "Has_Multiple_Units",
]


def mape(y, yhat):
    y, yhat = np.array(y), np.array(yhat)
    mask = y != 0
    return float((np.abs((yhat[mask] - y[mask]) / y[mask])).mean() * 100)


# ── 1. Load data ─────────────────────────────────────────────────

def load_data():
    print("Loading TeleTracking data...")
    tt = pd.read_excel(TELETRACK_PATH)
    tt["Bedrequest Timestamp"] = pd.to_datetime(tt["Bedrequest Timestamp"])

    print("Loading Daily Inpatient data...")
    preview = pd.read_excel(DAILY_CARE_PATH, header=None, nrows=20)
    header_idx = preview[preview.iloc[:, 0] == "Proxy Enc ID"].index[0]
    dc = pd.read_excel(DAILY_CARE_PATH, skiprows=header_idx)
    dc = dc.rename(columns={"Proxy Enc ID": "Proxy_Enc_ID", "Med/Surg": "Med_Surg"})
    return tt, dc


# ── 2. Build arrival features ────────────────────────────────────

def build_arrival_features(tt):
    tt["Date"] = tt["Bedrequest Timestamp"].dt.date
    daily = tt.groupby("Date").size().reset_index(name="arrivals")
    daily["Date"] = pd.to_datetime(daily["Date"])

    idx = pd.date_range(daily["Date"].min(), daily["Date"].max(), freq="D")
    df = pd.DataFrame(index=idx)
    df["arrivals"] = daily.set_index("Date")["arrivals"].reindex(idx).fillna(0)

    for k in [1, 3, 7, 14]:
        df[f"arrivals_lag{k}"] = df["arrivals"].shift(k)
    lagged = df["arrivals"].shift(1)
    df["arrivals_ma7"] = lagged.rolling(7, min_periods=7).mean()
    df["arrivals_ma14"] = lagged.rolling(14, min_periods=14).mean()
    df["arrivals_std7"] = lagged.rolling(7, min_periods=7).std()
    df["day_of_week"] = df.index.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["month"] = df.index.month
    df["week_of_year"] = df.index.isocalendar().week.astype(int)

    return df.dropna().copy()


# ── 3. Build patient features ────────────────────────────────────

def build_patient_features(dc):
    df = dc.copy()
    for unit in CARE_UNITS:
        col = unit if unit in df.columns else f"LOS_{unit}"
        df[f"LOS_{unit}"] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)

    if "LOS_Total" not in df.columns:
        df["LOS_Total"] = pd.to_numeric(df.get("Total", 0), errors="coerce")
    df = df.dropna(subset=["LOS_Total"])
    df = df[df["LOS_Total"] > 0]

    for u in CARE_UNITS:
        df[f"Has_{u}"] = (df[f"LOS_{u}"] > 0).astype(int)
    df["Care_Levels_Count"] = df[[f"Has_{u}" for u in CARE_UNITS]].sum(axis=1)
    df["Has_Multiple_Units"] = (df["Care_Levels_Count"] > 1).astype(int)
    df["label_short"] = (df["LOS_Total"] <= 2).astype(int)
    return df


# ── 4. Build hazard table ────────────────────────────────────────

def build_hazard_table(patient_df, max_los=30):
    icu = patient_df[patient_df["LOS_ICU"] > 0].copy()
    icu["LOS_ICU_capped"] = icu["LOS_ICU"].clip(upper=max_los).astype(int)

    rows = []
    total = len(icu)
    discharged = 0
    for day in range(max_los + 1):
        at_risk = total - discharged
        if at_risk <= 0:
            break
        dis_today = (icu["LOS_ICU_capped"] == day).sum()
        hazard = dis_today / at_risk if at_risk > 0 else 0.0
        rows.append({
            "Days_Completed": day,
            "Patients_At_Risk": at_risk,
            "Discharges": dis_today,
            "P_Discharge_Next_Day": round(hazard, 4),
        })
        discharged += dis_today
    return pd.DataFrame(rows)


# ── 5. Train & save ──────────────────────────────────────────────

def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    tt, dc = load_data()
    features = build_arrival_features(tt)
    patient_df = build_patient_features(dc)

    # ── Arrival model ──
    print("\n--- Arrival Model ---")
    train_df = features.iloc[:-14]
    test_df = features.iloc[-14:]

    rf = RandomForestRegressor(n_estimators=400, random_state=42, n_jobs=-1)
    rf.fit(train_df[ARRIVAL_FEATURE_COLS], train_df["arrivals"])
    preds = rf.predict(test_df[ARRIVAL_FEATURE_COLS])

    arr_metrics = {
        "mae": round(mean_absolute_error(test_df["arrivals"], preds), 3),
        "rmse": round(sqrt(mean_squared_error(test_df["arrivals"], preds)), 3),
        "mape": round(mape(test_df["arrivals"], preds), 3),
        "r2": round(r2_score(test_df["arrivals"], preds), 3),
        "holdout_days": 14,
    }
    print(f"  MAE={arr_metrics['mae']}  MAPE={arr_metrics['mape']}%")

    # Refit on all data
    rf_full = RandomForestRegressor(n_estimators=400, random_state=42, n_jobs=-1)
    rf_full.fit(features[ARRIVAL_FEATURE_COLS], features["arrivals"])
    joblib.dump(rf_full, out / "arrival_rf.joblib")

    # ── LOS model ──
    print("\n--- LOS Model ---")
    X = patient_df[LOS_FEATURE_COLS].astype(float)
    y = patient_df["LOS_Total"].astype(float)
    y_log = np.log1p(y)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    _, _, yl_tr, yl_te = train_test_split(X, y_log, test_size=0.2, random_state=42)

    ridge = Ridge(alpha=1.0)
    ridge.fit(X_tr, yl_tr)
    los_preds = np.expm1(ridge.predict(X_te))
    naive = np.full_like(y_te, fill_value=y_tr.median())

    los_metrics = {
        "ridge_mae": round(mean_absolute_error(y_te, los_preds), 3),
        "ridge_r2": round(r2_score(y_te, los_preds), 3),
        "naive_mae": round(mean_absolute_error(y_te, naive), 3),
    }
    print(f"  Ridge MAE={los_metrics['ridge_mae']}  Naive MAE={los_metrics['naive_mae']}")
    joblib.dump(ridge, out / "los_ridge.joblib")

    # ── Short-stay classifier ──
    print("\n--- Short-Stay Classifier ---")
    X_c = patient_df[LOS_FEATURE_COLS].astype(float)
    y_c = patient_df["label_short"]
    Xc_tr, Xc_te, yc_tr, yc_te = train_test_split(
        X_c, y_c, stratify=y_c, test_size=0.2, random_state=42
    )
    logit = LogisticRegression(max_iter=5000, class_weight="balanced")
    logit.fit(Xc_tr, yc_tr)
    proba = logit.predict_proba(Xc_te)[:, 1]
    pred_c = (proba >= 0.5).astype(int)
    auc = roc_auc_score(yc_te, proba)
    p, r, f1, _ = precision_recall_fscore_support(yc_te, pred_c, average="binary", zero_division=0)

    clf_metrics = {
        "auc": round(auc, 3),
        "precision": round(p, 3),
        "recall": round(r, 3),
        "f1": round(f1, 3),
        "short_stay_threshold_days": 2,
    }
    print(f"  AUC={clf_metrics['auc']}  F1={clf_metrics['f1']}")
    joblib.dump(logit, out / "short_stay_logit.joblib")

    # ── Hazard table ──
    print("\n--- Hazard Table ---")
    hazard = build_hazard_table(patient_df)
    hazard.to_csv(out / "icu_hazard_table.csv", index=False)
    print(f"  {len(hazard)} rows")

    # ── Metadata ──
    metadata = {
        "arrival_model": {
            "file": "arrival_rf.joblib",
            "features": ARRIVAL_FEATURE_COLS,
            "metrics": arr_metrics,
            "last_training_date": str(features.index.max().date()),
        },
        "los_model": {
            "file": "los_ridge.joblib",
            "features": LOS_FEATURE_COLS,
            "metrics": los_metrics,
            "log_transform": True,
        },
        "short_stay_classifier": {
            "file": "short_stay_logit.joblib",
            "features": LOS_FEATURE_COLS,
            "metrics": clf_metrics,
        },
        "hazard_table": {"file": "icu_hazard_table.csv"},
    }
    with open(out / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ All models saved to {OUTPUT_DIR}/")
    print("   Run the API with: uvicorn src.api:app --port 8080")


if __name__ == "__main__":
    main()
