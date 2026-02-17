"""
api.py — FastAPI REST API for ICU Census Prediction.

Endpoints:
  GET  /health              — Health check
  GET  /model-info          — Model metadata and metrics
  POST /predict/arrivals    — Predict daily arrivals
  POST /predict/los         — Predict length of stay (single)
  POST /predict/los/batch   — Predict LOS (batch, max 500)
  POST /predict/short-stay  — Classify short stay (≤2 days)
  POST /predict/census      — Forecast next-day ICU census

Interactive docs: http://localhost:8080/docs

Add this file to: src/api.py
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.predict import ICUCensusPredictor

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

predictor: Optional[ICUCensusPredictor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global predictor
    log.info("Loading model artifacts...")
    predictor = ICUCensusPredictor("models/")
    log.info("Models loaded — API ready.")
    yield


app = FastAPI(
    title="ICU Census Prediction API",
    description=(
        "Forecasting ICU census via arrival modeling, LOS estimation, "
        "and discharge hazard analysis. Built with real hospital data."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── Request Schemas ──────────────────────────────────────────────

class ArrivalFeatures(BaseModel):
    arrivals_lag1: float = Field(..., description="Arrivals 1 day ago")
    arrivals_lag3: float = Field(..., description="Arrivals 3 days ago")
    arrivals_lag7: float = Field(..., description="Arrivals 7 days ago")
    arrivals_lag14: float = Field(..., description="Arrivals 14 days ago")
    arrivals_ma7: float = Field(..., description="7-day moving average")
    arrivals_ma14: float = Field(..., description="14-day moving average")
    arrivals_std7: float = Field(..., description="7-day rolling std")
    day_of_week: int = Field(..., ge=0, le=6, description="0=Mon … 6=Sun")
    is_weekend: int = Field(..., ge=0, le=1)
    month: int = Field(..., ge=1, le=12)
    week_of_year: int = Field(..., ge=1, le=53)

    model_config = {"json_schema_extra": {"examples": [{
        "arrivals_lag1": 55, "arrivals_lag3": 48, "arrivals_lag7": 52,
        "arrivals_lag14": 60, "arrivals_ma7": 53.4, "arrivals_ma14": 54.2,
        "arrivals_std7": 6.1, "day_of_week": 2, "is_weekend": 0,
        "month": 1, "week_of_year": 4,
    }]}}


class PatientFeatures(BaseModel):
    Has_ICU: int = Field(..., ge=0, le=1)
    Has_Med_Surg: int = Field(..., ge=0, le=1)
    Has_PCU: int = Field(..., ge=0, le=1)
    Has_Tele: int = Field(..., ge=0, le=1)
    Care_Levels_Count: int = Field(..., ge=1, le=4)
    Has_Multiple_Units: int = Field(..., ge=0, le=1)

    model_config = {"json_schema_extra": {"examples": [{
        "Has_ICU": 1, "Has_Med_Surg": 1, "Has_PCU": 0,
        "Has_Tele": 0, "Care_Levels_Count": 2, "Has_Multiple_Units": 1,
    }]}}


class BatchPatientRequest(BaseModel):
    patients: list[PatientFeatures] = Field(..., min_length=1, max_length=500)


class CensusRequest(BaseModel):
    current_census: int = Field(..., ge=0)
    icu_days_completed: list[int] = Field(..., min_length=1)
    predicted_arrivals: Optional[float] = None
    arrival_features: Optional[ArrivalFeatures] = None
    icu_share: float = Field(0.15, ge=0.01, le=1.0)

    model_config = {"json_schema_extra": {"examples": [{
        "current_census": 28,
        "icu_days_completed": [0,1,1,2,3,3,4,5,6,7,8,10,12,15,
                               0,1,2,3,4,5,6,7,1,2,0,3,5,8],
        "predicted_arrivals": 55.0,
        "icu_share": 0.15,
    }]}}


# ── Endpoints ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "models_loaded": predictor is not None}


@app.get("/model-info")
async def model_info():
    return predictor.get_model_info()


@app.post("/predict/arrivals")
async def predict_arrivals(features: ArrivalFeatures):
    try:
        return predictor.predict_arrivals(features.model_dump())
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/predict/los")
async def predict_los(patient: PatientFeatures):
    try:
        return predictor.predict_los(patient.model_dump())
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/predict/los/batch")
async def predict_los_batch(req: BatchPatientRequest):
    try:
        results = predictor.predict_batch_los([p.model_dump() for p in req.patients])
        return {"predictions": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/predict/short-stay")
async def predict_short_stay(patient: PatientFeatures):
    try:
        return predictor.predict_short_stay(patient.model_dump())
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/predict/census")
async def forecast_census(req: CensusRequest):
    """Forecast next-day ICU census using the balance equation."""
    try:
        arrival_feats = req.arrival_features.model_dump() if req.arrival_features else None
        return predictor.forecast_census(
            current_census=req.current_census,
            icu_days_completed=req.icu_days_completed,
            predicted_arrivals=req.predicted_arrivals,
            arrival_features=arrival_feats,
            icu_share=req.icu_share,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))
