"""
ICU Census Prediction Pipeline
================================
Predicting ICU Census with Arrivals, LOS, and Discharge Modeling.

Modules:
    - data_loading: Load and clean raw hospital data
    - feature_engineering: Build lag, rolling, and categorical features
    - models: Train arrival, LOS, and short-stay classifiers
    - census_forecast: Simulate ICU census using hazard-based discharges
    - visualization: Generate dashboard plots and summaries
"""
