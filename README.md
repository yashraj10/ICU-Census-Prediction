# Predicting ICU Census with Arrivals, LOS & Discharge Modeling

**ICU 1 — Team 2**
Yashraj Jadhav · Jiaqi · Janell Wang · Shiv Paul Gupta · Kris He

---

## Overview

Hospital ICU census is volatile, causing staffing challenges, ED boarding, and patient diversion risk. This project builds a predictive pipeline that combines:

1. **Daily arrival forecasting** — predict hospital-wide and ICU-specific arrivals
2. **Length-of-stay modeling** — analyse LOS distributions and build short-stay classifiers
3. **Discharge hazard tables** — empirical survival-based daily discharge probabilities
4. **Census simulation** — next-day census = current census + arrivals − expected discharges
5. **Capacity dashboard** — flag units as SAFE / NEAR FULL / AT RISK

## Repository Structure

```
ICU-Census-Prediction/
├── src/
│   ├── __init__.py               # Package docstring
│   ├── data_loading.py           # Load & clean Excel data
│   ├── feature_engineering.py    # Lags, rolling stats, LOS features
│   ├── models.py                 # Arrival, classifier, & hazard models
│   ├── census_forecast.py        # Census simulation engine
│   └── visualization.py          # Dashboard plots
├── data/                         # Put your .xlsx files here (gitignored)
├── outputs/                      # Generated results (gitignored)
├── dashboard/
│   └── icu_dashboard.jsx         # Interactive React dashboard
├── run_pipeline.py               # One-command full pipeline runner
├── requirements.txt
├── .gitignore
└── README.md
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/<your-org>/ICU-Census-Prediction.git
cd ICU-Census-Prediction
pip install -r requirements.txt
```

### 2. Add data

Place your two data files in the `data/` folder:
- `Daily inpatient level of care.xlsx`
- `Teletracking02.24_01.25DEID.xlsx`

These are **not** committed to git (patient data).

### 3. Run the full pipeline

```bash
python run_pipeline.py \
    --care "data/Daily inpatient level of care.xlsx" \
    --tele "data/Teletracking02.24_01.25DEID.xlsx" \
    --output outputs/
```

This will:
- Load and clean both datasets
- Engineer 24+ time-series features
- Train arrival models (Random Forest, Gradient Boosting, Ensemble)
- Train short-stay classifiers for ICU, PCU, and Tele
- Build empirical discharge hazard tables
- Simulate 365-day ICU census
- Generate a 6-panel dashboard PNG
- Save all results as CSVs to `outputs/`

### 4. Use in Google Colab

```python
# Clone from GitHub
!git clone https://github.com/<your-org>/ICU-Census-Prediction.git
%cd ICU-Census-Prediction

# Install dependencies
!pip install -r requirements.txt

# Upload data to data/ folder, then run:
!python run_pipeline.py \
    --care "data/Daily inpatient level of care.xlsx" \
    --tele "data/Teletracking02.24_01.25DEID.xlsx"
```

Or import modules directly in a notebook:

```python
from src.data_loading import load_daily_care, load_teletracking, add_encounter_flags
from src.feature_engineering import build_daily_features, get_feature_columns
from src.models import train_arrival_models, build_hazard_table
from src.census_forecast import simulate_census, assign_status
```

## Data Sources

| Dataset | Records | Description |
|---------|---------|-------------|
| Daily Inpatient Level of Care | ~6,451 encounters | LOS per encounter across ICU, Med/Surg, PCU, Tele |
| TeleTracking ED Bed Request | ~20,431 requests | Bed requests with timestamps, origin, LOC, timing metrics |

Date range: Feb 2024 — Jan 2025 (365 days)

## Key Results

### Arrival Models (14-day holdout)

| Model | MAE | MAPE | R² |
|-------|-----|------|----|
| Random Forest | 5.99 | 11.0% | 0.073 |
| Gradient Boosting | 7.62 | 13.9% | -0.649 |
| Ensemble (avg) | 6.61 | 12.1% | -0.243 |

### Short-Stay Classifiers (≤2 days)

| Unit | Best Model | AUC | F1 |
|------|-----------|-----|-----|
| ICU | Gradient Boosting | **0.935** | 0.853 |
| PCU | Logistic Regression | 0.744 | 0.651 |
| Tele | Gradient Boosting | 0.756 | 0.704 |

### ICU Census Simulation

- Mean daily census: **27.6 patients** (capacity ~36)
- SAFE days: 193 (53%) · NEAR FULL: 140 (38%) · AT RISK: 32 (9%)
- Mean daily arrivals: 9.1 · Mean daily discharges: 9.0

## Module Docs

### `src/data_loading.py`
- `load_daily_care(path)` — auto-detects header, cleans LOS columns
- `load_teletracking(path)` — parses timestamps, maps LOC groups
- `add_encounter_flags(df)` — adds Has_ICU, Care_Levels_Count, etc.

### `src/feature_engineering.py`
- `build_daily_features(teletrack)` — lags, rolling stats, calendar features
- `build_los_features(daily_care, unit)` — LOS categories and log transform
- `los_summary(daily_care)` — summary table across all units

### `src/models.py`
- `train_arrival_models(daily, features)` — RF + GB + Ensemble
- `train_short_stay_classifier(daily_care, unit)` — LR + RF + GB
- `build_hazard_table(los_series)` — empirical hazard/survival table

### `src/census_forecast.py`
- `simulate_census(arrivals, hazard)` — stochastic or deterministic
- `assign_status(census_df, capacity)` — SAFE / NEAR FULL / AT RISK

### `src/visualization.py`
- `plot_dashboard(...)` — full 6-panel figure
- `plot_census_timeline(...)` — single census panel
- `plot_hazard_curves(...)` — multi-unit hazard overlay

## Limitations & Future Work

- **Single hospital**, limited time period (1 year)
- **Operational data only** — no clinical acuity, surgery schedules, or staffing
- Arrival model R² is low — consider ARIMA/Prophet or external features
- Census forecast is calibrated for ICU only; PCU/Tele extension is framework-ready
- Dashboard is a prototype; needs piloting with charge nurses and bed managers

## License

Academic project — not for clinical use without validation.
