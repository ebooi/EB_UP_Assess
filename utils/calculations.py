"""
Calculations for DHET funding exposure, compliance, and scenarios.
"""
from __future__ import annotations

import pandas as pd

from utils.constants import (
    DHET_OVER_THRESHOLD,
    DHET_UNDER_THRESHOLD,
    RAND_PER_TIU_2026_27,
    REMOVAL_RATE_2024,
    REMOVAL_RATE_2025,
    REMOVAL_RATE_2026,
    UP_2025_VARIANCE_THRESHOLD,
)


def up_2025_compliance(variance_pct: float) -> str:
    """Return Green / Amber / Red against the 2% UP 2025 threshold."""
    if variance_pct is None or pd.isna(variance_pct):
        return "Unknown"
    abs_v = abs(variance_pct)
    if abs_v <= UP_2025_VARIANCE_THRESHOLD:
        return "Green"
    if abs_v <= UP_2025_VARIANCE_THRESHOLD + 0.01:
        return "Amber"
    return "Red"


def dhet_compliance(variance_pct: float) -> str:
    """Return Green / Amber / Red against DHET thresholds (-2% / +3%)."""
    if variance_pct is None or pd.isna(variance_pct):
        return "Unknown"
    if DHET_UNDER_THRESHOLD <= variance_pct <= DHET_OVER_THRESHOLD:
        return "Green"
    if (DHET_UNDER_THRESHOLD - 0.01) <= variance_pct < DHET_UNDER_THRESHOLD:
        return "Amber"
    if DHET_OVER_THRESHOLD < variance_pct <= (DHET_OVER_THRESHOLD + 0.01):
        return "Amber"
    return "Red"


def calculate_subsidy_exposure(
    actual_tiu: float,
    approved_tiu: float,
    removal_rate: float = REMOVAL_RATE_2024,
    rand_per_tiu: float = RAND_PER_TIU_2026_27,
) -> dict:
    """Calculate rand-value exposure for over- or under-enrolment."""
    if approved_tiu == 0:
        return {
            "variance_pct": 0,
            "excess_units": 0,
            "units_removed": 0,
            "rand_exposure": 0,
            "removal_rate": removal_rate,
        }
    variance_pct = (actual_tiu / approved_tiu) - 1
    excess_units = 0.0

    if variance_pct > DHET_OVER_THRESHOLD:
        threshold_tiu = approved_tiu * (1 + DHET_OVER_THRESHOLD)
        excess_units = actual_tiu - threshold_tiu
    elif variance_pct < DHET_UNDER_THRESHOLD:
        threshold_tiu = approved_tiu * (1 + DHET_UNDER_THRESHOLD)
        excess_units = threshold_tiu - actual_tiu

    units_removed = excess_units * removal_rate
    rand_exposure = units_removed * rand_per_tiu

    return {
        "variance_pct": variance_pct,
        "excess_units": excess_units,
        "units_removed": units_removed,
        "rand_exposure": rand_exposure,
        "removal_rate": removal_rate,
    }


def project_exposure_across_years(
    actual_tiu: float, approved_tiu: float
) -> pd.DataFrame:
    """Project subsidy exposure across the three published removal-rate years."""
    rows = []
    for label, rate in [
        ("2026/27 (2024 data)", REMOVAL_RATE_2024),
        ("2027/28 (2025 data)", REMOVAL_RATE_2025),
        ("2028/29 (2026 data)", REMOVAL_RATE_2026),
    ]:
        result = calculate_subsidy_exposure(actual_tiu, approved_tiu, rate)
        rows.append(
            {
                "Financial year": label,
                "Removal rate": f"{rate:.0%}",
                "Units removed": round(result["units_removed"]),
                "Rand exposure (Rm)": round(result["rand_exposure"] / 1_000_000, 1),
            }
        )
    return pd.DataFrame(rows)


def cagr(start_value: float, end_value: float, periods: int) -> float:
    """Compound annual growth rate."""
    if start_value <= 0 or periods <= 0:
        return 0.0
    return (end_value / start_value) ** (1 / periods) - 1
