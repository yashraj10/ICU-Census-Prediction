# ICU Census Prediction

> Forecasting real-time ICU bed occupancy using arrival modeling, length-of-stay prediction, and discharge hazard analysis on real de-identified hospital data.

## Why This Matters

ICU capacity planning is one of the highest-stakes operational challenges in healthcare. Underestimating demand leads to patient diversions and worse outcomes; overestimating wastes expensive staffed beds. This project builds an **end-to-end prediction pipeline** that combines three modeling components — arrival forecasting, LOS regression, and discharge probability estimation — into a unified ICU census forecast that hospital operations teams can act on daily.

## Approach

The pipeline follows a modular design with no target leakage:

| Component | Purpose | Method |
|-----------|---------|--------|
| **Arrival Forecasting** | Predict daily ICU admissions | Random Forest on lag/rolling/calendar features |
| **LOS Modeling** | Estimate total length of stay | Ridge + Random Forest regression |
| **Discharge Hazard** | P(discharge \| days in ICU) | Empirical hazard from LOS distribution |
| **Census Simulation** | Project bed occupancy | Balance equation: Census₊₁ = Census + Arrivals − Discharges |
| **Short-Stay Classification** | Segment ≤2-day stays | Logistic Regression + Random Forest (balanced) |

Data covers **Feb 2024 – Jan 2025** from two hospital sources: daily inpatient level-of-care records and TeleTracking bed-request timestamps.

🔗 **[Live Interactive Dashboard](https://yashraj10.github.io/ICU-Census-Prediction/)**
<!-- Replace with your actual dashboard screenshot -->

## Key Results

| Task | Model | Key Metric | Value |
|------|-------|------------|-------|
| Arrival Forecast (14d holdout) | Random Forest | MAE | [fill from notebook] |
| Arrival Forecast (14d holdout) | Random Forest | R² | [fill from notebook] |
| LOS Regression (holdout) | Random Forest | MAE | [fill from notebook] |
| LOS Regression (holdout) | Random Forest | R² | [fill from notebook] |
| Discharge Classification | Logistic Regression | AUC | [fill from notebook] |
| Discharge Classification | Random Forest | AUC | [fill from notebook] |

> Run `python src/pipeline.py` to regenerate the full metrics table in `outputs/model_performance_summary.csv`.

## Project Structure

```
ICU-Census-Prediction/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── pipeline.py              # End-to-end orchestrator
│   ├── data_loader.py           # Load & clean Excel sources
│   ├── feature_engineering.py   # Arrival features, LOS features, discharge hazard
│   ├── models.py                # Train & evaluate all models
│   ├── census_simulator.py      # Forecast ICU census via balance equation
│   └── visualizations.py        # Dashboard and plot generation
├── notebooks/
│   └── exploration.ipynb        # EDA and prototyping (imports from src/)
├── data/
│   └── README.md                # Data dictionary & sourcing instructions
└── docs/
    └── dashboard.png            # Key visualizations
```

## Setup & Reproduce

```bash
git clone https://github.com/yashraj10/ICU-Census-Prediction.git
cd ICU-Census-Prediction
pip install -r requirements.txt

# Place source Excel files in data/ (see data/README.md for details)

# Run the full pipeline
python src/pipeline.py --data-dir data/

# Or explore interactively
jupyter notebook notebooks/exploration.ipynb
```

## Tech Stack

**Language:** Python  
**ML:** scikit-learn (Random Forest, Ridge, Logistic Regression)  
**Data:** pandas, NumPy, openpyxl  
**Visualization:** matplotlib  

## What I'd Improve Next

- Add a **FastAPI inference endpoint** for real-time census predictions served to a hospital dashboard
- Incorporate **survival analysis** (Cox PH / Kaplan-Meier) as an alternative to the empirical hazard model
- Build a **Streamlit demo** for interactive scenario exploration (e.g., "what if arrivals spike 20%?")
- Add **unit tests** for data validation and model output sanity checks
- Integrate **transfer learning** across hospital units to generalize beyond a single ICU

## Author

**Yashraj Jadhav** — MS Business Analytics, USC Marshall  
[LinkedIn](https://www.linkedin.com/in/yashrajjadhav/) · [Email](mailto:yjadhav@marshall.usc.edu)
