"""
Forecasting module v3.

Key change: forecasts are based on the approved plan trajectory rather
than actuals, so the 2023 outlier in the dummy data does not inflate
projections. Applies the UP 2025 2% YoY institutional growth cap and
the 70/30 UG/PG mix target.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def linear_forecast(series: pd.Series, years_ahead: int = 5,
                    confidence: float = 0.95) -> pd.DataFrame:
    """Linear regression forecast with 95% confidence interval."""
    series = series.dropna()
    if len(series) < 3:
        return pd.DataFrame(columns=["Year", "Forecast", "Lower", "Upper"])

    years = np.array(series.index, dtype=float).reshape(-1, 1)
    y = np.array(series.values, dtype=float)

    model = LinearRegression().fit(years, y)
    fitted = model.predict(years)
    residuals = y - fitted
    std_err = float(np.std(residuals, ddof=2)) if len(residuals) > 2 else 0.0

    z = 1.96 if confidence == 0.95 else 1.645
    last = int(series.index.max())
    future = np.arange(last + 1, last + 1 + years_ahead).reshape(-1, 1)
    forecast = model.predict(future)

    return pd.DataFrame({
        "Year": future.flatten(),
        "Forecast": forecast,
        "Lower": forecast - z * std_err,
        "Upper": forecast + z * std_err,
    })


def holt_winters_forecast(series: pd.Series, years_ahead: int = 5) -> pd.DataFrame:
    """Holt-Winters exponential smoothing with additive trend."""
    series = series.dropna()
    if len(series) < 4:
        return pd.DataFrame(columns=["Year", "Forecast"])
    try:
        model = ExponentialSmoothing(
            series.values, trend="add", seasonal=None,
            initialization_method="estimated"
        ).fit(optimized=True)
        forecast = model.forecast(years_ahead)
        last = int(series.index.max())
        future = np.arange(last + 1, last + 1 + years_ahead)
        return pd.DataFrame({"Year": future, "Forecast": forecast})
    except Exception:
        return pd.DataFrame(columns=["Year", "Forecast"])


def apply_growth_cap(start_value: float, periods: int, cap_pct: float = 0.02) -> np.ndarray:
    """Compound growth from a start value at cap_pct per year for N periods."""
    result = []
    prev = start_value
    for _ in range(periods):
        next_val = prev * (1 + cap_pct)
        result.append(next_val)
        prev = next_val
    return np.array(result)


def constrained_institutional_forecast(
    plan_series: pd.Series,
    actual_series: pd.Series,
    years_ahead: int = 5,
    growth_cap: float = 0.02,
    use_plan_baseline: bool = True,
) -> pd.DataFrame:
    """Institutional headcount forecast with 2% YoY growth cap.

    If use_plan_baseline=True, the forecast starts from the approved plan
    trajectory rather than actuals. This avoids the 2023 outlier inflating
    the projection.
    """
    if use_plan_baseline:
        # Start from the latest plan value, apply growth cap forward
        base = float(plan_series.dropna().iloc[-1])
    else:
        base = float(actual_series.dropna().iloc[-1])

    capped = apply_growth_cap(base, years_ahead, growth_cap)
    last_year = int(actual_series.dropna().index.max())
    future = np.arange(last_year + 1, last_year + 1 + years_ahead)

    # Also run statistical forecast for comparison
    lr = linear_forecast(actual_series, years_ahead=years_ahead)

    result = pd.DataFrame({
        "Year": future,
        "Plan-anchored capped": capped,
        "Statistical (unconstrained)": lr["Forecast"].values if not lr.empty else [np.nan] * years_ahead,
        "Lower 95%": lr["Lower"].values if not lr.empty else [np.nan] * years_ahead,
        "Upper 95%": lr["Upper"].values if not lr.empty else [np.nan] * years_ahead,
    })
    return result


def ug_pg_mix_forecast(
    ug_series: pd.Series,
    pg_series: pd.Series,
    years_ahead: int = 5,
    growth_cap: float = 0.02,
    target_ug_share: float = 0.70,
    target_pg_share: float = 0.30,
    convergence_years: int = 5,
) -> pd.DataFrame:
    """Forecast UG and PG separately, converging to the target mix.

    Total grows at the institutional cap. The UG share converges linearly
    from its current value to the target over `convergence_years` years.
    """
    ug_series = ug_series.dropna()
    pg_series = pg_series.dropna()
    if len(ug_series) < 2 or len(pg_series) < 2:
        return pd.DataFrame()

    last_year = int(max(ug_series.index.max(), pg_series.index.max()))
    last_ug = float(ug_series.iloc[-1])
    last_pg = float(pg_series.iloc[-1])
    last_total = last_ug + last_pg
    current_ug_share = last_ug / last_total if last_total > 0 else 0.5

    rows = []
    prev_total = last_total
    for step in range(1, years_ahead + 1):
        year = last_year + step
        # Total grows at the cap
        new_total = prev_total * (1 + growth_cap)
        # UG share converges to target
        progress = min(step / convergence_years, 1.0)
        ug_share_year = current_ug_share + (target_ug_share - current_ug_share) * progress
        pg_share_year = 1 - ug_share_year
        ug_year = new_total * ug_share_year
        pg_year = new_total * pg_share_year
        rows.append({
            "Year": year,
            "Total": new_total,
            "UG": ug_year,
            "PG": pg_year,
            "UG_share": ug_share_year,
            "PG_share": pg_share_year,
        })
        prev_total = new_total
    return pd.DataFrame(rows)


def funding_group_forecast(
    set_series: pd.Series,
    general_series: pd.Series,
    years_ahead: int = 5,
    growth_cap: float = 0.02,
) -> pd.DataFrame:
    """Forecast SET and Business/General separately with the institutional cap."""
    set_series = set_series.dropna()
    general_series = general_series.dropna()
    if len(set_series) < 2 or len(general_series) < 2:
        return pd.DataFrame()

    last_year = int(max(set_series.index.max(), general_series.index.max()))
    last_set = float(set_series.iloc[-1])
    last_general = float(general_series.iloc[-1])

    rows = []
    prev_set = last_set
    prev_general = last_general
    for step in range(1, years_ahead + 1):
        year = last_year + step
        new_set = prev_set * (1 + growth_cap)
        new_general = prev_general * (1 + growth_cap)
        rows.append({"Year": year, "SET": new_set, "Business/General": new_general,
                     "Total": new_set + new_general})
        prev_set = new_set
        prev_general = new_general
    return pd.DataFrame(rows)


def shape_size_simulation(
    base_headcount: float, base_pg_share: float, base_set_share: float,
    new_pg_share: float, new_set_share: float,
    avg_general_tiu_weight: float = 1.5, avg_set_tiu_weight: float = 2.5,
    avg_ug_grad_rate: float = 0.20, avg_pg_grad_rate: float = 0.45,
    rand_per_tiu: float = 16_819,
) -> dict:
    """Simulate impact of a shape-and-size shift on TIU, subsidy, graduates."""
    def calc(headcount, pg_share, set_share):
        pg = headcount * pg_share
        ug = headcount - pg
        set_total = headcount * set_share
        general_total = headcount - set_total
        # Simplified weighted TIU
        tiu = (
            ug * (1 - set_share) * avg_general_tiu_weight
            + ug * set_share * avg_set_tiu_weight
            + pg * (1 - set_share) * avg_general_tiu_weight * 2.5
            + pg * set_share * avg_set_tiu_weight * 2.5
        ) * 0.8
        grads = ug * avg_ug_grad_rate + pg * avg_pg_grad_rate
        subsidy = tiu * rand_per_tiu
        return {"headcount": headcount, "pg": pg, "ug": ug,
                "set": set_total, "general": general_total,
                "tiu": tiu, "graduates": grads, "subsidy": subsidy}

    base = calc(base_headcount, base_pg_share, base_set_share)
    new = calc(base_headcount, new_pg_share, new_set_share)
    return {
        "base": base, "new": new,
        "delta_tiu": new["tiu"] - base["tiu"],
        "delta_graduates": new["graduates"] - base["graduates"],
        "delta_subsidy": new["subsidy"] - base["subsidy"],
    }
