"""
models.py — Train and evaluate arrival, LOS, and discharge models.

Extracted from notebook Steps 11–14.
Each function returns fitted models and evaluation metrics.
"""

import numpy as np
import pandas as pd
from math import sqrt
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    r2_score,
    roc_auc_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)


# ---------------------------------------------------------------------------
# Arrival forecasting (Steps 11–12)
# ---------------------------------------------------------------------------

def train_arrival_model(
    features: pd.DataFrame,
    target_col: str = "arrivals",
    holdout_days: int = 14,
    n_estimators: int = 400,
    random_state: int = 42,
) -> dict:
    """
    Train a Random Forest regressor on daily arrival features with a
    time-ordered holdout split.

    Parameters
    ----------
    features : pd.DataFrame
        Output of build_arrival_features() — DatetimeIndex, includes target.
    target_col : str
        Name of the arrival count column.
    holdout_days : int
        Number of trailing days reserved for evaluation.
    n_estimators : int
        Number of trees.
    random_state : int
        Reproducibility seed.

    Returns
    -------
    dict with keys: model, metrics, predictions, feature_importance
    """
    data = features.dropna().copy()
    feat_cols = [c for c in data.columns if c != target_col]

    train = data.iloc[:-holdout_days]
    test = data.iloc[-holdout_days:]

    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    rf.fit(train[feat_cols], train[target_col])
    pred = rf.predict(test[feat_cols])

    y_true = test[target_col].values
    metrics = _regression_metrics(y_true, pred, include_mape=True)

    predictions = test.copy()
    predictions["predicted_arrivals"] = pred

    importance = pd.DataFrame({
        "feature": feat_cols,
        "importance": rf.feature_importances_,
    }).sort_values("importance", ascending=False)

    print(f"📈 Arrival RF — {holdout_days}-day holdout")
    print(f"   MAE : {metrics['MAE']:.2f}")
    print(f"   RMSE: {metrics['RMSE']:.2f}")
    print(f"   MAPE: {metrics['MAPE']:.2f}%")
    print(f"   R²  : {metrics['R2']:.3f}")

    return {
        "model": rf,
        "metrics": metrics,
        "predictions": predictions,
        "feature_importance": importance,
    }


def refit_arrival_model_full(
    features: pd.DataFrame,
    target_col: str = "arrivals",
    n_estimators: int = 400,
    random_state: int = 42,
) -> RandomForestRegressor:
    """Refit arrival RF on the full dataset for production forecasting."""
    data = features.dropna().copy()
    feat_cols = [c for c in data.columns if c != target_col]

    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    rf.fit(data[feat_cols], data[target_col])
    print(f"✅ Arrival model refit on {len(data)} days (full data)")
    return rf


# ---------------------------------------------------------------------------
# LOS regression (Step 13)
# ---------------------------------------------------------------------------

def train_los_models(
    daily_care: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """
    Train baseline (naive median), Ridge, and Random Forest regressors
    for total LOS prediction.

    Parameters
    ----------
    daily_care : pd.DataFrame
        Must contain LOS_Total and Has_* / Care_Levels_Count columns.

    Returns
    -------
    dict with keys: ridge, rf, metrics (DataFrame), predictions
    """
    feature_cols = [
        "Has_ICU", "Has_Med_Surg", "Has_PCU", "Has_Tele",
        "Care_Levels_Count", "Has_Multiple_Units",
    ]

    df = daily_care[["LOS_Total"] + feature_cols].dropna().copy()
    df = df[df["LOS_Total"] > 0]

    X = df[feature_cols].astype(float)
    y = df["LOS_Total"].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Naive baseline: constant median
    yhat_naive = np.full_like(y_test, fill_value=y_train.median())

    # Ridge
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train, y_train)
    yhat_ridge = ridge.predict(X_test)

    # Random Forest
    rf = RandomForestRegressor(n_estimators=400, random_state=random_state)
    rf.fit(X_train, y_train)
    yhat_rf = rf.predict(X_test)

    m_naive = _regression_metrics(y_test, yhat_naive)
    m_ridge = _regression_metrics(y_test, yhat_ridge)
    m_rf = _regression_metrics(y_test, yhat_rf)

    metrics = pd.DataFrame([
        {"Model": "Naive (median)", **m_naive},
        {"Model": "Ridge", **m_ridge},
        {"Model": "RandomForest", **m_rf},
    ])

    print("🏥 LOS prediction — holdout metrics")
    for _, row in metrics.iterrows():
        print(f"   {row['Model']:<18s}  MAE={row['MAE']:.2f}  RMSE={row['RMSE']:.2f}  R²={row['R2']:.3f}")

    predictions = X_test.copy()
    predictions["y_true"] = y_test.values
    predictions["yhat_ridge"] = yhat_ridge
    predictions["yhat_rf"] = yhat_rf

    return {
        "ridge": ridge,
        "rf": rf,
        "metrics": metrics,
        "predictions": predictions,
    }


# ---------------------------------------------------------------------------
# Discharge classification (Steps 8 & 14)
# ---------------------------------------------------------------------------

def train_discharge_models(
    daily_care: pd.DataFrame,
    short_threshold: int = 2,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """
    Train Logistic Regression and Random Forest classifiers for
    short-stay (≤ threshold days) vs. longer-stay discharge prediction.

    Parameters
    ----------
    daily_care : pd.DataFrame
        Must contain LOS_Total and Has_* / Care_Levels_Count columns.
    short_threshold : int
        LOS days at or below which a stay is classified as "short".

    Returns
    -------
    dict with keys: logistic, rf, metrics (DataFrame), predictions
    """
    feature_cols = [
        "Has_ICU", "Has_Med_Surg", "Has_PCU", "Has_Tele",
        "Care_Levels_Count", "Has_Multiple_Units",
    ]

    df = daily_care[["LOS_Total"] + feature_cols].dropna().copy()
    df = df[df["LOS_Total"] > 0]
    df["label_short"] = (df["LOS_Total"] <= short_threshold).astype(int)

    X = df[feature_cols].astype(float)
    y = df["label_short"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, test_size=test_size, random_state=random_state
    )

    # Logistic Regression (balanced)
    logit = LogisticRegression(max_iter=5000, class_weight="balanced")
    logit.fit(X_train, y_train)
    proba_logit = logit.predict_proba(X_test)[:, 1]
    pred_logit = (proba_logit >= 0.5).astype(int)
    auc_logit = roc_auc_score(y_test, proba_logit)

    # Random Forest (balanced)
    rf = RandomForestClassifier(n_estimators=400, random_state=random_state, class_weight="balanced")
    rf.fit(X_train, y_train)
    proba_rf = rf.predict_proba(X_test)[:, 1]
    pred_rf = (proba_rf >= 0.5).astype(int)
    auc_rf = roc_auc_score(y_test, proba_rf)

    p_l, r_l, f1_l, _ = precision_recall_fscore_support(y_test, pred_logit, average="binary", zero_division=0)
    p_r, r_r, f1_r, _ = precision_recall_fscore_support(y_test, pred_rf, average="binary", zero_division=0)

    metrics = pd.DataFrame([
        {"Model": "LogisticRegression", "AUC": auc_logit, "Precision": p_l, "Recall": r_l, "F1": f1_l},
        {"Model": "RandomForest", "AUC": auc_rf, "Precision": p_r, "Recall": r_r, "F1": f1_r},
    ])

    print("🚪 Discharge (Short vs Other) — holdout metrics")
    for _, row in metrics.iterrows():
        print(f"   {row['Model']:<22s}  AUC={row['AUC']:.3f}  P={row['Precision']:.3f}  R={row['Recall']:.3f}  F1={row['F1']:.3f}")

    predictions = X_test.copy()
    predictions["y_true"] = y_test.values
    predictions["proba_logit"] = proba_logit
    predictions["proba_rf"] = proba_rf
    predictions["pred_logit"] = pred_logit
    predictions["pred_rf"] = pred_rf

    return {
        "logistic": logit,
        "rf": rf,
        "metrics": metrics,
        "predictions": predictions,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _regression_metrics(y_true, y_pred, include_mape: bool = False) -> dict:
    """Compute standard regression metrics."""
    result = {
        "MAE": mean_absolute_error(y_true, y_pred),
        "MedAE": median_absolute_error(y_true, y_pred),
        "RMSE": sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
    }
    if include_mape:
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        mask = y_true != 0
        result["MAPE"] = (np.abs((y_pred[mask] - y_true[mask]) / y_true[mask])).mean() * 100
    return result
