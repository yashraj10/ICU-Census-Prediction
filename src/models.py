"""
models.py
==========
Train and evaluate predictive models:
  1. Daily arrival forecast  (Random Forest, Gradient Boosting, Ensemble)
  2. Short-stay classifier   (Logistic Regression, RF, GB)
  3. Discharge hazard table  (empirical survival-based)

Usage:
    from src.models import (
        train_arrival_models,
        train_short_stay_classifier,
        build_hazard_table,
    )
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field

from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    RandomForestClassifier,
    GradientBoostingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
    f1_score,
    classification_report,
)
from sklearn.model_selection import train_test_split


# ──────────────────────────────────────────────────────────────
# Result containers
# ──────────────────────────────────────────────────────────────
@dataclass
class RegressionResult:
    name: str
    model: object
    y_true: np.ndarray
    y_pred: np.ndarray
    mae: float = 0.0
    rmse: float = 0.0
    r2: float = 0.0
    mape: float = 0.0

    def __post_init__(self):
        self.mae = mean_absolute_error(self.y_true, self.y_pred)
        self.rmse = np.sqrt(mean_squared_error(self.y_true, self.y_pred))
        self.r2 = r2_score(self.y_true, self.y_pred)
        self.mape = 100 * np.mean(
            np.abs((self.y_true - self.y_pred) / np.where(self.y_true == 0, 1, self.y_true))
        )

    def summary(self) -> dict:
        return {
            "Model": self.name,
            "MAE": round(self.mae, 2),
            "RMSE": round(self.rmse, 2),
            "R²": round(self.r2, 3),
            "MAPE (%)": round(self.mape, 2),
        }


@dataclass
class ClassificationResult:
    name: str
    model: object
    y_true: np.ndarray
    y_pred: np.ndarray
    y_proba: np.ndarray
    auc: float = 0.0
    f1: float = 0.0

    def __post_init__(self):
        self.auc = roc_auc_score(self.y_true, self.y_proba)
        self.f1 = f1_score(self.y_true, self.y_pred)

    def summary(self) -> dict:
        report = classification_report(self.y_true, self.y_pred, output_dict=True)
        return {
            "Model": self.name,
            "AUC": round(self.auc, 3),
            "F1": round(self.f1, 3),
            "Precision": round(report["1"]["precision"], 3),
            "Recall": round(report["1"]["recall"], 3),
        }


# ──────────────────────────────────────────────────────────────
# 1. Arrival models
# ──────────────────────────────────────────────────────────────
def train_arrival_models(
    daily: pd.DataFrame,
    feature_cols: list[str],
    target: str = "total_arrivals",
    holdout_days: int = 14,
    random_state: int = 42,
) -> tuple[list[RegressionResult], pd.DataFrame]:
    """
    Train Random Forest, Gradient Boosting, and an Ensemble for
    daily arrival prediction using a time-based holdout split.

    Parameters
    ----------
    daily : pd.DataFrame
        Must have ``date``, ``target``, and all ``feature_cols``.
    feature_cols : list[str]
        Column names to use as features.
    target : str
        Target column name.
    holdout_days : int
        Number of trailing days to use as the test set.
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    results : list[RegressionResult]
        One result object per model (RF, GB, Ensemble).
    test_df : pd.DataFrame
        Test-set dates with actual and predicted values.
    """
    df = daily.dropna(subset=feature_cols + [target]).copy()

    cutoff = df["date"].max() - pd.Timedelta(days=holdout_days)
    train = df[df["date"] <= cutoff]
    test = df[df["date"] > cutoff]

    X_train, y_train = train[feature_cols], train[target].values
    X_test, y_test = test[feature_cols], test[target].values

    # Random Forest
    rf = RandomForestRegressor(
        n_estimators=500, max_depth=10, min_samples_leaf=5,
        random_state=random_state,
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)

    # Gradient Boosting
    gb = GradientBoostingRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        random_state=random_state,
    )
    gb.fit(X_train, y_train)
    gb_pred = gb.predict(X_test)

    # Ensemble (simple average)
    ens_pred = (rf_pred + gb_pred) / 2

    results = [
        RegressionResult("RandomForest", rf, y_test, rf_pred),
        RegressionResult("GradientBoosting", gb, y_test, gb_pred),
        RegressionResult("Ensemble (RF+GB)", None, y_test, ens_pred),
    ]

    test_df = pd.DataFrame({
        "date": test["date"].values,
        "actual": y_test,
        "rf_pred": rf_pred,
        "gb_pred": gb_pred,
        "ensemble_pred": ens_pred,
    })

    return results, test_df


def feature_importance(model, feature_cols: list[str], top_n: int = 10) -> pd.Series:
    """Return sorted feature importances from a tree-based model."""
    return (
        pd.Series(model.feature_importances_, index=feature_cols)
        .sort_values(ascending=False)
        .head(top_n)
    )


# ──────────────────────────────────────────────────────────────
# 2. Short-stay classifier
# ──────────────────────────────────────────────────────────────
def train_short_stay_classifier(
    daily_care: pd.DataFrame,
    unit_col: str = "ICU",
    threshold: int = 2,
    test_size: float = 0.2,
    random_state: int = 42,
) -> list[ClassificationResult]:
    """
    Train classifiers to predict whether a patient's LOS in
    *unit_col* is ≤ *threshold* days ("short stay").

    Three models are trained: Logistic Regression, Random Forest,
    and Gradient Boosting (all with class_weight='balanced' where
    applicable).

    Parameters
    ----------
    daily_care : pd.DataFrame
        Must include encounter flags (Has_ICU, etc.) and unit LOS.
    unit_col : str
        Unit column to classify.
    threshold : int
        Days cutoff for short-stay label.
    test_size : float
        Fraction held out for testing.
    random_state : int

    Returns
    -------
    list[ClassificationResult]
    """
    pts = daily_care[daily_care[unit_col] > 0].copy()
    pts["short_stay"] = (pts[unit_col] <= threshold).astype(int)

    feature_cols = [
        "Has_ICU", "Has_Med_Surg", "Has_PCU", "Has_Tele",
        "Care_Levels_Count", "Has_Multiple_Units", "Total",
    ]

    X = pts[feature_cols]
    y = pts["short_stay"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state,
    )

    classifiers = [
        ("Logistic", LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=random_state
        )),
        ("RandomForest", RandomForestClassifier(
            n_estimators=200, class_weight="balanced", random_state=random_state
        )),
        ("GradientBoosting", GradientBoostingClassifier(
            n_estimators=200, max_depth=3, random_state=random_state
        )),
    ]

    results = []
    for name, clf in classifiers:
        clf.fit(X_train, y_train)
        proba = clf.predict_proba(X_test)[:, 1]
        pred = clf.predict(X_test)
        results.append(
            ClassificationResult(
                f"{name} ({unit_col})", clf, y_test.values, pred, proba
            )
        )

    return results


# ──────────────────────────────────────────────────────────────
# 3. Discharge hazard table
# ──────────────────────────────────────────────────────────────
def build_hazard_table(
    los_series: pd.Series,
    max_day: int = 30,
) -> pd.DataFrame:
    """
    Build an empirical hazard (discharge probability) table from
    a series of observed LOS values.

    hazard[d] = P(discharge on day d | still in unit on day d)

    Parameters
    ----------
    los_series : pd.Series
        Raw LOS values (one per patient).
    max_day : int
        Cap LOS at this value.

    Returns
    -------
    pd.DataFrame
        Columns: day, at_risk, discharged, hazard, survival.
    """
    capped = los_series.clip(upper=max_day)

    at_risk = np.zeros(max_day + 1)
    discharged = np.zeros(max_day + 1)

    for los in capped:
        for d in range(1, int(los) + 1):
            if d <= max_day:
                at_risk[d] += 1
        if int(los) <= max_day:
            discharged[int(los)] += 1

    hazard = np.zeros(max_day + 1)
    survival = np.ones(max_day + 1)
    for d in range(1, max_day + 1):
        hazard[d] = discharged[d] / at_risk[d] if at_risk[d] > 0 else 0
        survival[d] = survival[d - 1] * (1 - hazard[d])

    rows = []
    for d in range(1, max_day + 1):
        rows.append({
            "day": d,
            "at_risk": int(at_risk[d]),
            "discharged": int(discharged[d]),
            "hazard": round(hazard[d], 4),
            "survival": round(survival[d], 4),
        })

    return pd.DataFrame(rows)


def get_hazard_array(hazard_df: pd.DataFrame, max_day: int = 30) -> np.ndarray:
    """Convert hazard DataFrame back to a numpy array indexed by day."""
    arr = np.zeros(max_day + 1)
    for _, row in hazard_df.iterrows():
        arr[int(row["day"])] = row["hazard"]
    return arr
