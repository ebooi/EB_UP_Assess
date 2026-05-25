"""
Data quality dimensions: Completeness, Accuracy, Consistency, Reliability.

Each dimension produces a score (0-1) per faculty per year. The aggregate
gives an executive scorecard.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

KEY_FIELDS = [
    "ActualHeadcount", "FTE", "Graduates", "ResearchOutputUnits",
    "AcademicStaffFTE", "SuccessRate", "TuitionRevenue_Rm",
    "StudentDebt_Rm", "CapacitySeats",
]


# ---------------------------------------------------------------------------
# Dimension 1: Completeness
# ---------------------------------------------------------------------------
def completeness_by_faculty(df: pd.DataFrame) -> pd.DataFrame:
    """Share of non-missing cells in key fields, per faculty per year."""
    rows = []
    for (year, fac), group in df.groupby(["Year", "Faculty"]):
        total = len(group) * len(KEY_FIELDS)
        missing = group[KEY_FIELDS].isna().sum().sum()
        score = 1 - (missing / total) if total else 1.0
        rows.append({"Year": year, "Faculty": fac, "Score": score,
                     "MissingCells": int(missing), "TotalCells": int(total)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Dimension 2: Accuracy
# ---------------------------------------------------------------------------
def accuracy_by_faculty(df: pd.DataFrame) -> pd.DataFrame:
    """Share of records that pass range-validity checks."""
    rows = []
    for (year, fac), group in df.groupby(["Year", "Faculty"]):
        failures = 0
        records_checked = 0
        for _, row in group.iterrows():
            records_checked += 1
            # Rate fields must be in 0-1
            if pd.notna(row["SuccessRate"]) and (row["SuccessRate"] < 0 or row["SuccessRate"] > 1):
                failures += 1
                continue
            if pd.notna(row["DropoutRate"]) and (row["DropoutRate"] < 0 or row["DropoutRate"] > 1):
                failures += 1
                continue
            # Headcount and other counts must be non-negative
            for field in ["ActualHeadcount", "ApprovedPlanHeadcount", "FTE",
                          "Graduates", "ResearchOutputUnits", "AcademicStaffFTE",
                          "TuitionRevenue_Rm", "StudentDebt_Rm", "CapacitySeats"]:
                if pd.notna(row[field]) and row[field] < 0:
                    failures += 1
                    break
        score = 1 - (failures / records_checked) if records_checked else 1.0
        rows.append({"Year": year, "Faculty": fac, "Score": score,
                     "Failures": failures, "Records": records_checked})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Dimension 3: Consistency
# ---------------------------------------------------------------------------
def consistency_by_faculty(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-field validation: FTE <= Headcount, Graduates <= Headcount, etc."""
    rows = []
    for (year, fac), group in df.groupby(["Year", "Faculty"]):
        failures = 0
        records = 0
        for _, row in group.iterrows():
            records += 1
            hc = row["ActualHeadcount"]
            fte = row["FTE"]
            grads = row["Graduates"]

            # FTE should be 0.1 to 1.3 times headcount
            if pd.notna(hc) and pd.notna(fte) and hc > 0:
                ratio = fte / hc
                if ratio < 0.1 or ratio > 1.3:
                    failures += 1
                    continue
            # Annual graduates should be <= headcount
            if pd.notna(hc) and pd.notna(grads) and grads > hc:
                failures += 1
                continue
        score = 1 - (failures / records) if records else 1.0
        rows.append({"Year": year, "Faculty": fac, "Score": score,
                     "Failures": failures, "Records": records})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Dimension 4: Reliability
# ---------------------------------------------------------------------------
def reliability_by_faculty(df: pd.DataFrame) -> pd.DataFrame:
    """Year-on-year stability score. Excessive YoY swings reduce reliability."""
    rows = []
    sorted_df = df.sort_values(["Faculty", "ProgrammeCluster", "Year"]).copy()
    sorted_df["hc_change"] = (
        sorted_df.groupby(["Faculty", "ProgrammeCluster"])["ActualHeadcount"].pct_change()
    )

    for (year, fac), group in sorted_df.groupby(["Year", "Faculty"]):
        records = len(group)
        if records == 0:
            continue
        # Count records with extreme YoY change (>50%)
        extreme = (group["hc_change"].abs() > 0.5).sum()
        score = 1 - (extreme / records) if records else 1.0
        rows.append({"Year": year, "Faculty": fac, "Score": score,
                     "ExtremeChanges": int(extreme), "Records": records})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Aggregate scorecard
# ---------------------------------------------------------------------------
def all_dimensions_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """Combine all dimensions into a single scorecard."""
    comp = completeness_by_faculty(df)[["Year", "Faculty", "Score"]].rename(columns={"Score": "Completeness"})
    acc = accuracy_by_faculty(df)[["Year", "Faculty", "Score"]].rename(columns={"Score": "Accuracy"})
    cons = consistency_by_faculty(df)[["Year", "Faculty", "Score"]].rename(columns={"Score": "Consistency"})
    rel = reliability_by_faculty(df)[["Year", "Faculty", "Score"]].rename(columns={"Score": "Reliability"})

    merged = comp.merge(acc, on=["Year", "Faculty"], how="outer") \
                 .merge(cons, on=["Year", "Faculty"], how="outer") \
                 .merge(rel, on=["Year", "Faculty"], how="outer")

    score_cols = ["Completeness", "Accuracy", "Consistency", "Reliability"]
    merged["Overall"] = merged[score_cols].mean(axis=1)
    return merged


def get_all_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Combined issue list across all checks."""
    issues = []
    # Negative values
    numeric = ["ApprovedPlanHeadcount", "ActualHeadcount", "FTE", "Graduates",
               "ResearchOutputUnits", "AcademicStaffFTE", "TuitionRevenue_Rm",
               "StudentDebt_Rm", "CapacitySeats"]
    for col in numeric:
        mask = df[col] < 0
        for _, r in df[mask].iterrows():
            issues.append({"Year": r["Year"], "Faculty": r["Faculty"],
                          "Programme": r["ProgrammeCluster"], "Field": col,
                          "Value": r[col], "Dimension": "Accuracy",
                          "Issue": "Negative value"})
    # Impossible rates
    for _, r in df.iterrows():
        if pd.notna(r["SuccessRate"]) and (r["SuccessRate"] < 0 or r["SuccessRate"] > 1):
            issues.append({"Year": r["Year"], "Faculty": r["Faculty"],
                          "Programme": r["ProgrammeCluster"], "Field": "SuccessRate",
                          "Value": r["SuccessRate"], "Dimension": "Accuracy",
                          "Issue": "Rate outside 0-1"})
    # FTE consistency
    for _, r in df.iterrows():
        if pd.notna(r["FTE"]) and pd.notna(r["ActualHeadcount"]) and r["ActualHeadcount"] > 0:
            ratio = r["FTE"] / r["ActualHeadcount"]
            if ratio < 0.1 or ratio > 1.3:
                issues.append({"Year": r["Year"], "Faculty": r["Faculty"],
                              "Programme": r["ProgrammeCluster"], "Field": "FTE",
                              "Value": r["FTE"], "Dimension": "Consistency",
                              "Issue": f"FTE/headcount = {ratio:.2f}"})
    # Reliability (YoY outliers)
    sorted_df = df.sort_values(["Faculty", "ProgrammeCluster", "Year"]).copy()
    sorted_df["change"] = sorted_df.groupby(["Faculty", "ProgrammeCluster"])["ActualHeadcount"].pct_change()
    for _, r in sorted_df.iterrows():
        if pd.notna(r["change"]) and abs(r["change"]) > 0.5:
            issues.append({"Year": r["Year"], "Faculty": r["Faculty"],
                          "Programme": r["ProgrammeCluster"], "Field": "ActualHeadcount",
                          "Value": r["ActualHeadcount"], "Dimension": "Reliability",
                          "Issue": f"YoY change = {r['change']:.0%}"})
    # Completeness (missing values)
    for col in KEY_FIELDS:
        mask = df[col].isna()
        for _, r in df[mask].iterrows():
            issues.append({"Year": r["Year"], "Faculty": r["Faculty"],
                          "Programme": r["ProgrammeCluster"], "Field": col,
                          "Value": None, "Dimension": "Completeness",
                          "Issue": "Missing value"})
    if not issues:
        return pd.DataFrame(columns=["Year", "Faculty", "Programme", "Field", "Value", "Dimension", "Issue"])
    return pd.DataFrame(issues).sort_values(["Year", "Faculty", "Programme"])
