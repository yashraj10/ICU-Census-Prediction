"""
predict.py — Inference engine for ICU Census Prediction API.

Loads serialized model artifacts (joblib) and provides prediction methods.
This module is independent of the training pipeline — it only needs the
saved model files in models/.

Add this file to: src/predict.py
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class ICUCensusPredictor:
    """Loads all trained models and exposes prediction endpoints.

    Usage:
        predictor = ICUCensusPredictor("models/")
        result = predictor.forecast_census(current_census=30, ...)
    """

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self._load_artifacts()

    def _load_artifacts(self):
        with open(self.model_dir / "model_metadata.json") as f:
            self.metadata = json.load(f)

        self.arrival_model = joblib.load(
            self.model_dir / self.metadata["arrival_model"]["file"]
        )
        self.arrival_features = self.metadata["arrival_model"]["features"]

        self.los_model = joblib.load(
            self.model_dir / self.metadata["los_model"]["file"]
        )
        self.los_features = self.metadata["los_model"]["features"]
        self.los_log_transform = self.metadata["los_model"].get("log_transform", True)

        self.short_stay_model = joblib.load(
            self.model_dir / self.metadata["short_stay_classifier"]["file"]
        )
        self.short_stay_features = self.metadata["short_stay_classifier"]["features"]

        self.hazard_table = pd.read_csv(
            self.model_dir / self.metadata["hazard_table"]["file"]
        )
        self._hazard_lookup = dict(
            zip(
                self.hazard_table["Days_Completed"],
                self.hazard_table["P_Discharge_Next_Day"],
            )
        )
        log.info("Models loaded from %s", self.model_dir)

    # ----- Arrival forecasting -----

    def predict_arrivals(self, features: dict) -> dict:
        X = pd.DataFrame([features])[self.arrival_features]
        pred = float(self.arrival_model.predict(X)[0])
        return {"predicted_arrivals": round(pred, 1)}

    # ----- LOS prediction -----

    def predict_los(self, patient: dict) -> dict:
        X = pd.DataFrame([patient])[self.los_features].astype(float)
        pred = float(self.los_model.predict(X)[0])
        if self.los_log_transform:
            pred = float(np.expm1(pred))
        return {"predicted_los_days": round(max(pred, 0), 1)}

    # ----- Short-stay classification -----

    def predict_short_stay(self, patient: dict) -> dict:
        X = pd.DataFrame([patient])[self.short_stay_features].astype(float)
        proba = float(self.short_stay_model.predict_proba(X)[0, 1])
        return {
            "is_short_stay": proba >= 0.5,
            "short_stay_probability": round(proba, 3),
        }

    # ----- Discharge hazard -----

    def expected_discharges(self, icu_days_completed: list[int]) -> dict:
        max_day = self.hazard_table["Days_Completed"].max()
        probs = [
            self._hazard_lookup.get(min(int(d), max_day), 0.0)
            for d in icu_days_completed
        ]
        return {
            "current_census": len(icu_days_completed),
            "expected_discharges": round(sum(probs), 2),
            "per_patient_probabilities": [round(p, 4) for p in probs],
        }

    # ----- Census forecast (main endpoint) -----

    def forecast_census(
        self,
        current_census: int,
        icu_days_completed: list[int],
        predicted_arrivals: float = None,
        arrival_features: dict = None,
        icu_share: float = 0.15,
    ) -> dict:
        """Census_tomorrow = Census_today + ICU_arrivals − Expected_discharges"""

        if predicted_arrivals is not None:
            total_arrivals = predicted_arrivals
        elif arrival_features is not None:
            total_arrivals = self.predict_arrivals(arrival_features)["predicted_arrivals"]
        else:
            raise ValueError("Provide predicted_arrivals or arrival_features")

        icu_arrivals = total_arrivals * icu_share
        discharge_result = self.expected_discharges(icu_days_completed)
        exp_dis = discharge_result["expected_discharges"]
        forecast = current_census + icu_arrivals - exp_dis

        return {
            "current_census": current_census,
            "predicted_total_arrivals": round(total_arrivals, 1),
            "icu_share": icu_share,
            "predicted_icu_arrivals": round(icu_arrivals, 1),
            "expected_discharges": round(exp_dis, 2),
            "forecasted_census_tomorrow": round(max(forecast, 0), 1),
        }

    # ----- Batch -----

    def predict_batch_los(self, patients: list[dict]) -> list[dict]:
        return [self.predict_los(p) for p in patients]

    # ----- Info -----

    def get_model_info(self) -> dict:
        return {
            "arrival_model": self.metadata["arrival_model"]["metrics"],
            "los_model": self.metadata["los_model"]["metrics"],
            "short_stay_classifier": self.metadata["short_stay_classifier"]["metrics"],
            "hazard_table_rows": len(self.hazard_table),
        }
