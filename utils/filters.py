"""
Shared sidebar filter panel.

Every page calls apply_filters() at the top to display the unified sidebar
filters and get back a filtered DataFrame. The filters apply consistently
across pages and persist via session_state.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and return the filtered DataFrame."""
    st.sidebar.markdown("### Filters")
    st.sidebar.caption(
        "Filters apply across all pages. Reset by selecting 'All' on every filter."
    )

    # Faculty filter
    faculties = ["All"] + sorted(df["FacultyCode"].unique().tolist())
    selected_faculty = st.sidebar.selectbox(
        "Faculty", options=faculties, key="filter_faculty"
    )

    # Programme cluster filter (depends on faculty selection)
    if selected_faculty == "All":
        cluster_options = ["All"] + sorted(df["ProgrammeCluster"].unique().tolist())
    else:
        cluster_options = ["All"] + sorted(
            df[df["FacultyCode"] == selected_faculty]["ProgrammeCluster"].unique().tolist()
        )
    selected_cluster = st.sidebar.selectbox(
        "Programme cluster", options=cluster_options, key="filter_cluster"
    )

    # Level filter
    levels = ["All"] + sorted(df["Level"].unique().tolist())
    selected_level = st.sidebar.selectbox(
        "Level", options=levels, key="filter_level"
    )

    # Funding group filter
    funding_groups = ["All"] + sorted(df["FundingGroup"].unique().tolist())
    selected_funding = st.sidebar.selectbox(
        "Funding group", options=funding_groups, key="filter_funding"
    )

    # Mode filter
    modes = ["All"] + sorted(df["Mode"].unique().tolist())
    selected_mode = st.sidebar.selectbox(
        "Mode", options=modes, key="filter_mode"
    )

    # Year range
    year_min = int(df["Year"].min())
    year_max = int(df["Year"].max())
    selected_years = st.sidebar.slider(
        "Year range",
        min_value=year_min, max_value=year_max,
        value=(year_min, year_max), key="filter_years",
    )

    # Apply filters
    filtered = df.copy()
    if selected_faculty != "All":
        filtered = filtered[filtered["FacultyCode"] == selected_faculty]
    if selected_cluster != "All":
        filtered = filtered[filtered["ProgrammeCluster"] == selected_cluster]
    if selected_level != "All":
        filtered = filtered[filtered["Level"] == selected_level]
    if selected_funding != "All":
        filtered = filtered[filtered["FundingGroup"] == selected_funding]
    if selected_mode != "All":
        filtered = filtered[filtered["Mode"] == selected_mode]
    filtered = filtered[
        (filtered["Year"] >= selected_years[0]) & (filtered["Year"] <= selected_years[1])
    ]

    # Show summary of active filters
    active = []
    if selected_faculty != "All":
        active.append(f"Faculty: {selected_faculty}")
    if selected_cluster != "All":
        active.append(f"Cluster: {selected_cluster}")
    if selected_level != "All":
        active.append(f"Level: {selected_level}")
    if selected_funding != "All":
        active.append(f"Funding: {selected_funding}")
    if selected_mode != "All":
        active.append(f"Mode: {selected_mode}")

    if active:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Active filters**")
        for a in active:
            st.sidebar.markdown(f"- {a}")
        st.sidebar.caption(f"Showing {len(filtered)} of {len(df)} rows")

    return filtered
