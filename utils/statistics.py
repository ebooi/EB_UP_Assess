"""
Statistical analysis utilities for executive reporting.

Provides:
- Trend regression with significance test
- Year-on-year growth analysis with confidence intervals
- Distribution statistics (mean, std, IQR, outliers)
- Throughput correlation analysis
- Plan deviation analysis
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def trend_regression(series: pd.Series) -> dict:
    """Fit linear trend, return slope, intercept, R-squared, p-value."""
    series = series.dropna()
    if len(series) < 3:
        return {"slope": np.nan, "intercept": np.nan, "r_squared": np.nan,
                "p_value": np.nan, "std_err": np.nan, "significant": False}

    x = np.array(series.index, dtype=float)
    y = np.array(series.values, dtype=float)
    result = stats.linregress(x, y)
    return {
        "slope": result.slope,
        "intercept": result.intercept,
        "r_squared": result.rvalue ** 2,
        "p_value": result.pvalue,
        "std_err": result.stderr,
        "significant": result.pvalue < 0.05,
    }


def yoy_growth_stats(series: pd.Series) -> dict:
    """Year-on-year growth rate statistics."""
    series = series.dropna()
    if len(series) < 2:
        return {"mean_growth": np.nan, "std_growth": np.nan,
                "ci_lower": np.nan, "ci_upper": np.nan, "min": np.nan, "max": np.nan}

    growth = series.pct_change().dropna()
    if len(growth) == 0:
        return {"mean_growth": np.nan, "std_growth": np.nan,
                "ci_lower": np.nan, "ci_upper": np.nan, "min": np.nan, "max": np.nan}

    mean_g = growth.mean()
    std_g = growth.std()
    n = len(growth)
    # 95% CI for the mean
    if n > 1 and not np.isnan(std_g):
        se = std_g / np.sqrt(n)
        t_crit = stats.t.ppf(0.975, n - 1)
        ci_lower = mean_g - t_crit * se
        ci_upper = mean_g + t_crit * se
    else:
        ci_lower = ci_upper = np.nan

    return {
        "mean_growth": mean_g,
        "std_growth": std_g,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "min": growth.min(),
        "max": growth.max(),
    }


def distribution_stats(values: pd.Series) -> dict:
    """Mean, median, std, IQR, and outliers via IQR rule."""
    values = values.dropna()
    if len(values) < 3:
        return {"mean": np.nan, "median": np.nan, "std": np.nan,
                "q1": np.nan, "q3": np.nan, "iqr": np.nan,
                "lower_bound": np.nan, "upper_bound": np.nan, "outliers": 0}

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = ((values < lower_bound) | (values > upper_bound)).sum()

    return {
        "mean": values.mean(),
        "median": values.median(),
        "std": values.std(),
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "outliers": int(outliers),
    }


def correlation_analysis(series_a: pd.Series, series_b: pd.Series) -> dict:
    """Pearson correlation between two aligned series."""
    df_pair = pd.concat([series_a, series_b], axis=1).dropna()
    if len(df_pair) < 3:
        return {"correlation": np.nan, "p_value": np.nan, "significant": False}

    r, p = stats.pearsonr(df_pair.iloc[:, 0], df_pair.iloc[:, 1])
    return {"correlation": r, "p_value": p, "significant": p < 0.05}


def plan_deviation_history(df: pd.DataFrame, group_col: str = None) -> pd.DataFrame:
    """Historical plan vs actual deviation per year (and optionally group)."""
    if group_col:
        grouped = df.groupby(["Year", group_col]).agg(
            Plan=("ApprovedPlanHeadcount", "sum"),
            Actual=("ActualHeadcount", "sum"),
        ).reset_index()
    else:
        grouped = df.groupby("Year").agg(
            Plan=("ApprovedPlanHeadcount", "sum"),
            Actual=("ActualHeadcount", "sum"),
        ).reset_index()

    grouped["Deviation"] = grouped["Actual"] - grouped["Plan"]
    grouped["Deviation_pct"] = grouped["Deviation"] / grouped["Plan"]
    grouped["Abs_deviation_pct"] = grouped["Deviation_pct"].abs()
    return grouped


def forecast_accuracy_metric(df: pd.DataFrame) -> dict:
    """Mean absolute percentage error (MAPE) of actual against plan."""
    grouped = df.groupby("Year").agg(
        Plan=("ApprovedPlanHeadcount", "sum"),
        Actual=("ActualHeadcount", "sum"),
    ).reset_index()
    if len(grouped) == 0:
        return {"mape": np.nan, "mean_abs_dev_pct": np.nan, "max_abs_dev_pct": np.nan}

    grouped["abs_pct_error"] = (grouped["Actual"] - grouped["Plan"]).abs() / grouped["Plan"]
    return {
        "mape": grouped["abs_pct_error"].mean(),
        "mean_abs_dev_pct": grouped["abs_pct_error"].mean(),
        "max_abs_dev_pct": grouped["abs_pct_error"].max(),
    }
