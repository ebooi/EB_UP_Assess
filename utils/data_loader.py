"""
Data loader for the Faculty Enrolment dataset (v3).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "Faculty_Enrolment.xlsx"


@st.cache_data(show_spinner=False)
def load_enrolment_data() -> pd.DataFrame:
    """Load the workbook with derived helper columns."""
    df = pd.read_excel(DATA_PATH)

    # Enrolment domain
    df["VariancePct"] = df["ActualHeadcount"] / df["ApprovedPlanHeadcount"] - 1

    # Student Success domain
    df["RetentionRate"] = 1 - df["DropoutRate"]
    df["GraduationRate"] = df["Graduates"] / df["ActualHeadcount"]

    # Efficiency domain
    df["StudentStaffRatio"] = df["FTE"] / df["AcademicStaffFTE"]
    df["ResearchPerStaff"] = df["ResearchOutputUnits"] / df["AcademicStaffFTE"]
    df["CapacityUtilisation"] = df["ActualHeadcount"] / df["CapacitySeats"]

    # Financial domain
    df["DebtToTuition"] = df["StudentDebt_Rm"] / df["TuitionRevenue_Rm"]

    # Subsidy domain
    df["GraduateConversion"] = df["Graduates"] / df["ActualHeadcount"]
    df["OutputPerFTE"] = df["TOU_proxy"] / df["FTE"]

    # Replace infinities
    df = df.replace([np.inf, -np.inf], np.nan)

    return df


def aggregate(df: pd.DataFrame, by: list) -> pd.DataFrame:
    """Generic aggregator with derived ratios recomputed."""
    agg = df.groupby(by).agg(
        ApprovedPlanHeadcount=("ApprovedPlanHeadcount", "sum"),
        ActualHeadcount=("ActualHeadcount", "sum"),
        FTE=("FTE", "sum"),
        TIU_proxy=("TIU_proxy", "sum"),
        Graduates=("Graduates", "sum"),
        TOU_proxy=("TOU_proxy", "sum"),
        ResearchOutputUnits=("ResearchOutputUnits", "sum"),
        AcademicStaffFTE=("AcademicStaffFTE", "sum"),
        TuitionRevenue_Rm=("TuitionRevenue_Rm", "sum"),
        StudentDebt_Rm=("StudentDebt_Rm", "sum"),
        CapacitySeats=("CapacitySeats", "sum"),
        SuccessRate=("SuccessRate", "mean"),
        DropoutRate=("DropoutRate", "mean"),
    ).reset_index()

    agg["VariancePct"] = agg["ActualHeadcount"] / agg["ApprovedPlanHeadcount"] - 1
    agg["RetentionRate"] = 1 - agg["DropoutRate"]
    agg["GraduationRate"] = agg["Graduates"] / agg["ActualHeadcount"]
    agg["StudentStaffRatio"] = agg["FTE"] / agg["AcademicStaffFTE"]
    agg["ResearchPerStaff"] = agg["ResearchOutputUnits"] / agg["AcademicStaffFTE"]
    agg["DebtToTuition"] = agg["StudentDebt_Rm"] / agg["TuitionRevenue_Rm"]
    agg["GraduateConversion"] = agg["Graduates"] / agg["ActualHeadcount"]
    agg["OutputPerFTE"] = agg["TOU_proxy"] / agg["FTE"]
    agg["CapacityUtilisation"] = agg["ActualHeadcount"] / agg["CapacitySeats"]

    return agg


@st.cache_data(show_spinner=False)
def get_institutional_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Institution-year level."""
    return aggregate(df, ["Year"])


@st.cache_data(show_spinner=False)
def get_faculty_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Faculty-year level."""
    return aggregate(df, ["Year", "Faculty", "FacultyCode"])


def get_level_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Year-Level aggregation (UG vs PG)."""
    return aggregate(df, ["Year", "Level"])


def get_funding_group_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Year-FundingGroup aggregation."""
    return aggregate(df, ["Year", "FundingGroup"])


def get_mix_share(df: pd.DataFrame, by: str = "Level") -> pd.DataFrame:
    """Year-by-Year share by Level or FundingGroup."""
    yearly = df.groupby(["Year", by])["ActualHeadcount"].sum().reset_index()
    totals = df.groupby("Year")["ActualHeadcount"].sum().reset_index()
    totals = totals.rename(columns={"ActualHeadcount": "Total"})
    merged = yearly.merge(totals, on="Year")
    merged["Share"] = merged["ActualHeadcount"] / merged["Total"]
    return merged
