"""
test_api.py — Integration tests for the ICU Census Prediction API.
Run: pytest tests/test_api.py -v
"""
import os, pytest
from fastapi.testclient import TestClient
from src.api import app

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ARRIVAL = {
    "arrivals_lag1": 55, "arrivals_lag3": 48, "arrivals_lag7": 52,
    "arrivals_lag14": 60, "arrivals_ma7": 53.4, "arrivals_ma14": 54.2,
    "arrivals_std7": 6.1, "day_of_week": 2, "is_weekend": 0,
    "month": 1, "week_of_year": 4,
}
PATIENT = {
    "Has_ICU": 1, "Has_Med_Surg": 1, "Has_PCU": 0,
    "Has_Tele": 0, "Care_Levels_Count": 2, "Has_Multiple_Units": 1,
}

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

class TestHealth:
    def test_health(self, client):
        assert client.get("/health").status_code == 200
    def test_models_loaded(self, client):
        assert client.get("/health").json()["models_loaded"] is True

class TestModelInfo:
    def test_returns_metrics(self, client):
        r = client.get("/model-info")
        assert r.status_code == 200
        assert "mae" in r.json()["arrival_model"]

class TestArrivals:
    def test_predict(self, client):
        r = client.post("/predict/arrivals", json=ARRIVAL)
        assert r.status_code == 200
        assert r.json()["predicted_arrivals"] > 0
    def test_missing_field(self, client):
        bad = {k: v for k, v in ARRIVAL.items() if k != "month"}
        assert client.post("/predict/arrivals", json=bad).status_code == 422

class TestLOS:
    def test_single(self, client):
        r = client.post("/predict/los", json=PATIENT)
        assert r.status_code == 200
        assert r.json()["predicted_los_days"] >= 0
    def test_batch(self, client):
        r = client.post("/predict/los/batch", json={"patients": [PATIENT, PATIENT]})
        assert r.status_code == 200
        assert r.json()["count"] == 2
    def test_batch_empty(self, client):
        assert client.post("/predict/los/batch", json={"patients": []}).status_code == 422

class TestShortStay:
    def test_classify(self, client):
        r = client.post("/predict/short-stay", json=PATIENT)
        assert r.status_code == 200
        assert 0 <= r.json()["short_stay_probability"] <= 1

class TestCensus:
    def test_with_predicted_arrivals(self, client):
        r = client.post("/predict/census", json={
            "current_census": 28,
            "icu_days_completed": [0,1,2,3,5,7,10,1,2,0,3,4,5,6,8,1,2,3,4,5,0,1,6,7,12,15,2,3],
            "predicted_arrivals": 55.0, "icu_share": 0.15,
        })
        assert r.status_code == 200
        assert r.json()["forecasted_census_tomorrow"] >= 0
    def test_with_arrival_features(self, client):
        r = client.post("/predict/census", json={
            "current_census": 25,
            "icu_days_completed": [0,1,2,3,5,7,1,2,0,3,4,5,6,8,1,2,3,4,5,0,1,6,7,12,15],
            "arrival_features": ARRIVAL, "icu_share": 0.15,
        })
        assert r.status_code == 200
    def test_missing_both_fails(self, client):
        r = client.post("/predict/census", json={
            "current_census": 28, "icu_days_completed": [0, 1, 2],
        })
        assert r.status_code == 422
