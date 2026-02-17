"""
visualizations.py — Generate publication-quality plots for the ICU census project.

Extracted from notebook Step 10.
All functions return matplotlib figure objects for flexible saving/display.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_daily_arrivals(teletrack: pd.DataFrame, ax=None) -> plt.Axes:
    """Time-series of daily ED arrivals."""
    daily = (
        teletrack.groupby(teletrack["Bedrequest Timestamp"].dt.date)
        .size()
        .reset_index(name="Total_Arrivals")
    )
    daily.columns = ["Date", "Total_Arrivals"]
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily.sort_values("Date")

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily["Date"], daily["Total_Arrivals"], linewidth=0.9)
    ax.set_title("Daily ED Arrivals")
    ax.set_xlabel("Date")
    ax.set_ylabel("Arrivals")
    return ax


def plot_arrivals_by_dow(teletrack: pd.DataFrame, ax=None) -> plt.Axes:
    """Bar chart of arrivals by day of week."""
    dow = teletrack["Bedrequest Timestamp"].dt.dayofweek.value_counts().reindex(range(7), fill_value=0)
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, dow.values, color="#4C72B0")
    ax.set_title("Arrivals by Day of Week")
    ax.set_ylabel("Arrivals")
    return ax


def plot_los_distribution(daily_care: pd.DataFrame, max_los: int = 30, ax=None) -> plt.Axes:
    """Density plot of LOS by unit (capped)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))

    units = {"ICU": "LOS_ICU", "Med_Surg": "LOS_Med_Surg", "PCU": "LOS_PCU", "Tele": "LOS_Tele"}
    for label, col in units.items():
        if col in daily_care.columns:
            data = daily_care[daily_care[col] > 0][col].clip(upper=max_los)
            if len(data) > 0:
                data.plot.kde(ax=ax, label=label, bw_method=0.3)

    ax.set_title(f"LOS Distribution by Unit (Capped {max_los}d)")
    ax.set_xlabel("Length of Stay (days)")
    ax.set_ylabel("Density")
    ax.legend()
    ax.set_xlim(0, max_los)
    return ax


def plot_discharge_hazard(hazard_table: pd.DataFrame, ax=None) -> plt.Axes:
    """Bar chart of ICU discharge probability by day."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4))

    ax.bar(
        hazard_table["Days_Completed"],
        hazard_table["P_Discharge_Next_Day"],
        color="#4C72B0",
    )
    ax.set_title("ICU Discharge Probability by Day")
    ax.set_xlabel("ICU Day")
    ax.set_ylabel("P(Discharge)")
    return ax


def plot_arrival_forecast(predictions: pd.DataFrame, ax=None) -> plt.Axes:
    """Actual vs predicted arrivals on the holdout set."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))

    dates = predictions.index if isinstance(predictions.index, pd.DatetimeIndex) else range(len(predictions))
    ax.plot(dates, predictions["arrivals"], marker="o", label="Actual", linewidth=1.5)
    ax.plot(dates, predictions["predicted_arrivals"], marker="s", label="Predicted", linewidth=1.5)
    ax.set_title("Arrival Forecast — Holdout Period")
    ax.set_xlabel("Date")
    ax.set_ylabel("Arrivals")
    ax.legend()
    return ax


def plot_census_control_chart(
    daily_census: pd.Series,
    ax=None,
    sigma: float = 2.0,
) -> plt.Axes:
    """Census time series with control limits (mean ± σ bands)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))

    mean = daily_census.mean()
    std = daily_census.std()

    ax.plot(daily_census.index, daily_census.values, linewidth=0.9)
    ax.axhline(mean, color="green", linestyle="--", alpha=0.7, label=f"Mean ({mean:.1f})")
    ax.axhline(mean + sigma * std, color="red", linestyle="--", alpha=0.5, label=f"+{sigma}σ")
    ax.axhline(mean - sigma * std, color="red", linestyle="--", alpha=0.5, label=f"−{sigma}σ")
    ax.fill_between(
        daily_census.index,
        mean - sigma * std,
        mean + sigma * std,
        alpha=0.1,
        color="red",
    )
    ax.set_title("ICU Census — Control Chart")
    ax.set_xlabel("Date")
    ax.set_ylabel("Patient Count")
    ax.legend(loc="upper right")
    return ax


def create_dashboard(
    teletrack: pd.DataFrame,
    daily_care: pd.DataFrame,
    hazard_table: pd.DataFrame,
    save_path: str | None = None,
) -> plt.Figure:
    """Generate a 2×2 dashboard with key project visuals."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("ICU Census Prediction — Dashboard", fontsize=16, fontweight="bold")

    plot_daily_arrivals(teletrack, ax=axes[0, 0])
    plot_arrivals_by_dow(teletrack, ax=axes[0, 1])
    plot_los_distribution(daily_care, ax=axes[1, 0])
    plot_discharge_hazard(hazard_table, ax=axes[1, 1])

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    if save_path:
        fig.savefig(save_path, dpi=180, bbox_inches="tight")
        print(f"✅ Dashboard saved: {save_path}")

    return fig
