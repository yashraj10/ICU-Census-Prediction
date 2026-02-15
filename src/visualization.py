"""
visualization.py
=================
Dashboard-style plots for ICU census prediction results.

All functions return matplotlib Figure objects so callers can
``fig.savefig(...)`` or display inline in Jupyter.

Usage:
    from src.visualization import plot_dashboard
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns


# Consistent palette
COLORS = {
    "ICU": "#2196F3",
    "Med_Surg": "#4CAF50",
    "PCU": "#FF9800",
    "Tele": "#9C27B0",
    "SAFE": "#4CAF50",
    "NEAR FULL": "#FF9800",
    "AT RISK": "#f44336",
}

sns.set_style("whitegrid")
plt.rcParams.update({"figure.dpi": 120, "font.size": 10})


# ──────────────────────────────────────────────────────────────
# 1. Full dashboard (6-panel figure)
# ──────────────────────────────────────────────────────────────
def plot_dashboard(
    census_df: pd.DataFrame,
    arrival_test: pd.DataFrame,
    daily_df: pd.DataFrame,
    daily_care: pd.DataFrame,
    hazard_df: pd.DataFrame,
    capacity: int = 36,
) -> plt.Figure:
    """
    Create a 3×2 dashboard figure.

    Panels:
        [0,0] ICU census over time
        [0,1] Arrival forecast (holdout)
        [1,0] LOS distribution by unit
        [1,1] ICU discharge hazard
        [2,0] Weekly arrivals by LOC
        [2,1] Capacity status distribution
    """
    fig, axes = plt.subplots(3, 2, figsize=(18, 16))
    fig.suptitle(
        "ICU Census Prediction Dashboard",
        fontsize=18, fontweight="bold", y=0.98,
    )

    # --- 1. Census over time ---
    ax = axes[0, 0]
    ax.plot(census_df["date"], census_df["census"],
            color=COLORS["ICU"], lw=1.2, alpha=0.8, label="Simulated Census")
    ax.axhline(capacity, color="red", ls="--", alpha=0.7, label=f"Capacity ({capacity})")
    ax.axhline(capacity * 0.8, color="orange", ls="--", alpha=0.5, label="80% threshold")
    ax.fill_between(census_df["date"], capacity * 0.95, census_df["census"].max() * 1.1,
                     alpha=0.08, color="red")
    ax.set_title("ICU Census Over Time", fontweight="bold")
    ax.set_ylabel("Patient Count")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)

    # --- 2. Arrival forecast ---
    ax = axes[0, 1]
    ax.plot(arrival_test["date"], arrival_test["actual"], "ko-", label="Actual", ms=5)
    ax.plot(arrival_test["date"], arrival_test["rf_pred"], "s--",
            color="#4CAF50", label="RF", ms=4)
    ax.plot(arrival_test["date"], arrival_test["gb_pred"], "^--",
            color="#FF9800", label="GB", ms=4)
    ax.plot(arrival_test["date"], arrival_test["ensemble_pred"], "D-",
            color="#9C27B0", label="Ensemble", ms=4)
    ax.set_title("Daily Arrival Forecast (Holdout)", fontweight="bold")
    ax.set_ylabel("Total Arrivals")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="x", rotation=45)

    # --- 3. LOS distribution ---
    ax = axes[1, 0]
    for unit, col in [("ICU", "ICU"), ("Med_Surg", "Med_Surg"),
                      ("PCU", "PCU"), ("Tele", "Tele")]:
        data = daily_care[daily_care[col] > 0][col].clip(upper=30)
        if len(data) > 0:
            ax.hist(data, bins=30, alpha=0.45, label=unit,
                    color=COLORS[unit], density=True)
    ax.set_title("LOS Distribution by Unit (Capped 30d)", fontweight="bold")
    ax.set_xlabel("Length of Stay (days)")
    ax.set_ylabel("Density")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # --- 4. Hazard ---
    ax = axes[1, 1]
    haz = hazard_df[hazard_df["day"] < 30]
    ax.bar(haz["day"], haz["hazard"], color=COLORS["ICU"], alpha=0.7, edgecolor="white")
    ax.set_title("ICU Discharge Probability by Day", fontweight="bold")
    ax.set_xlabel("ICU Day")
    ax.set_ylabel("P(Discharge)")
    ax.grid(True, alpha=0.3, axis="y")

    # --- 5. Arrivals by LOC ---
    ax = axes[2, 0]
    loc_cols = [c for c in daily_df.columns
                if c.startswith("arrivals_") and "lag" not in c and "ma" not in c]
    if loc_cols:
        weekly = daily_df.set_index("date").resample("W")[loc_cols].mean()
        for loc in ["ICU", "Med_Surg", "PCU", "Tele"]:
            col = f"arrivals_{loc}"
            if col in weekly.columns:
                ax.plot(weekly.index, weekly[col], label=loc,
                        color=COLORS[loc], lw=2)
    ax.set_title("Weekly Average Arrivals by LOC", fontweight="bold")
    ax.set_ylabel("Daily Arrivals (Weekly Avg)")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # --- 6. Status distribution ---
    ax = axes[2, 1]
    if "status" in census_df.columns:
        counts = census_df["status"].value_counts()
        bars = ax.bar(
            counts.index, counts.values,
            color=[COLORS.get(s, "gray") for s in counts.index],
            edgecolor="white", lw=2,
        )
        for bar, val in zip(bars, counts.values):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f"{val}\n({100 * val / len(census_df):.0f}%)",
                ha="center", fontsize=11, fontweight="bold",
            )
    ax.set_title("ICU Capacity Status Distribution", fontweight="bold")
    ax.set_ylabel("Number of Days")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


# ──────────────────────────────────────────────────────────────
# Individual plots (for flexibility)
# ──────────────────────────────────────────────────────────────
def plot_census_timeline(census_df: pd.DataFrame, capacity: int = 36) -> plt.Figure:
    """Single-panel census timeline with capacity zones."""
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(census_df["date"], 0, capacity * 0.8,
                     alpha=0.08, color="green", label="SAFE zone")
    ax.fill_between(census_df["date"], capacity * 0.8, capacity * 0.95,
                     alpha=0.08, color="orange", label="NEAR FULL zone")
    ax.fill_between(census_df["date"], capacity * 0.95, capacity * 1.2,
                     alpha=0.08, color="red", label="AT RISK zone")
    ax.plot(census_df["date"], census_df["census"],
            color=COLORS["ICU"], lw=1.5, label="Census")
    ax.axhline(capacity, color="red", ls="--", lw=1, alpha=0.7)
    ax.set_xlabel("Date")
    ax.set_ylabel("ICU Census")
    ax.set_title("ICU Census with Capacity Zones", fontweight="bold")
    ax.legend(fontsize=8)
    plt.tight_layout()
    return fig


def plot_hazard_curves(hazard_tables: dict[str, pd.DataFrame]) -> plt.Figure:
    """Overlay hazard curves for multiple units."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for unit, df in hazard_tables.items():
        haz = df[df["day"] < 30]
        ax.plot(haz["day"], haz["hazard"], "o-", label=unit,
                color=COLORS.get(unit, "gray"), ms=4, lw=1.5)
    ax.set_xlabel("Day in Unit")
    ax.set_ylabel("P(Discharge)")
    ax.set_title("Discharge Hazard by Unit", fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig
